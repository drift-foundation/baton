"""The durable authority store: creation, opening, and the write transaction.

Creation, opening and adoption refusal are cut 1.  Cut 3 adds the OPERATION
JOURNAL, and the two live in one module because they are one mechanism.

`transact` is the atomic boundary the contract keeps insisting on -- "ONE
transaction: fence the exact generation AND end the assignment" -- and `replay`
is what makes a repeated request return the first outcome instead of performing
it twice.  Neither is safe without the other: journalling outside the
transaction that did the work would let a crash leave a mutation with no
operation record, and the next retry would do it again.

THE SAVEPOINT IS NOT DECORATION.  §7 distinguishes two kinds of refusal and they
need opposite storage:

  * an ORDINARY refusal writes nothing and stays retryable.  Its partial writes,
    if any, must vanish.
  * a refusal that WROTE something durable -- the stale-target integration
    journals its attempt before refusing -- is itself a committed outcome, so
    those writes AND the refusal record must survive, and the retry replays the
    refusal rather than appending a second attempt.

So the action runs inside a savepoint: an ordinary refusal rolls back to it, a
durable refusal releases it and records the refusal, and both then COMMIT the
enclosing transaction.  A fault that is not a `Refusal` takes the whole
transaction down instead -- an operation whose failure we cannot describe is not
one we may record an outcome for.

WHICH KIND a refusal is comes from the refusal itself, set by the transition
that RAISED it.  The frozen host was corrected for having that as a flag on the
call site: one transition then marked every refusal durable, including the ones
that wrote nothing, permanently closing operation identities that should have
stayed retryable.

CREATION AND OPENING ARE DIFFERENT OPERATIONS, and that is the whole design.

The frozen Node host has one `open` that creates when absent, adopts when
present and writes the schema before it has established whose store it is.  For
a disposable single-host authority that was tolerable.  It is not tolerable
here, because this distribution now sits beside three other SQLite files that
all call their first schema version `1` -- the Node authority, the v11 authority
and the Worker Manager control store.  A create-or-adopt `open` against any of
them writes tables into somebody else's database before anyone has asked whose
it is, and the failure mode is silent success.

So:

  * `create` REQUIRES ABSENCE and wins it exclusively.  The path is reserved
    with `O_CREAT | O_EXCL` before SQLite is involved at all, so two racing
    creators produce one winner and one refusal rather than two half-built
    stores.
  * `open` REQUIRES A RECOGNIZED STORE.  It probes READ-ONLY first, so an
    unowned, empty, foreign, newer, older or UUID-mismatched database is refused
    with the file exactly as it was found.  Not "refused after we fixed the
    PRAGMAs"; refused without modification.
  * the compatibility facts are RECHECKED inside the first write transaction,
    because a read-only probe is a fact about the past and another process may
    own the file by the time we write.

NO DIRECTORY IS CREATED and no state root is inferred.  Placement supplies one
explicit file path.  A symlink or any non-regular target refuses: the authority
UUID is durable, and a store reachable through a link somebody else can repoint
is not durable in the sense that matters.
"""

import json
import os
import sqlite3

from .errors import Refusal, label_of, name_of
from .schema import (META_AUTHORITY_UUID, META_SCHEMA_VERSION, META_STORE_KIND,
                     SCHEMA, SCHEMA_VERSION, STORE_KIND)

__all__ = ["Store"]

_BUSY_TIMEOUT_MS = 5000


def _require_path(path, *, what="the authority store path"):
    # The LABEL is caller text at every exported helper, so it is
    # bound by the rule here, once, where it is accepted.
    what = label_of(what)
    if type(path) is not str or path == "":
        raise Refusal(f"{what} is {name_of(path)}; placement supplies one explicit file")
    return path


def _describe_target(path):
    """What is at `path`, without following a link.

    `lstat` rather than `stat`, because the question is what the path IS, not
    what it points at.  A symlink target can be repointed by whoever owns the
    link, and an authority UUID that can be swapped underneath a running host
    is not durable.
    """
    try:
        status = os.lstat(path)
    except FileNotFoundError:
        return None
    except OSError as failure:
        raise Refusal(
            f"the authority store path could not be inspected ({failure.errno}); "
            f"operands are proved before anything durable happens")
    return status


class Store:
    """One process's connection to one authority store."""

    def __init__(self, connection, path, authority_uuid):
        self._db = connection
        self._path = path
        self.authority_uuid = authority_uuid
        self._depth = 0
        self._reading = False
        self._savepoints = 0

    # -- creation and opening ------------------------------------------------

    @staticmethod
    def create(path, *, authority_uuid):
        """Create a NEW Python-authority store at an absent path.

        Exclusive by construction: `O_CREAT | O_EXCL` is the reservation, and it
        fails on an existing file, an existing directory and an existing symlink
        alike -- including a DANGLING one, which is exactly the case a
        "does it exist?" check answers wrongly.
        """
        from .identity import check_authority_uuid

        _require_path(path)
        check_authority_uuid(authority_uuid)
        try:
            handle = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            raise Refusal(
                f"an authority store already exists at {name_of(path)}; create "
                f"makes a "
                f"new authority and never adopts one, and open is the operation "
                f"for an existing store") from None
        except OSError as failure:
            raise Refusal(
                f"the authority store at {name_of(path)} could not be created "
                f"({failure.errno}); the authority creates no directory and "
                f"infers no state root") from None
        os.close(handle)
        connection = None
        try:
            connection = _connect(path)
            connection.execute("BEGIN IMMEDIATE")
            _apply_schema(connection)
            _write_meta(connection, META_STORE_KIND, STORE_KIND)
            _write_meta(connection, META_SCHEMA_VERSION, str(SCHEMA_VERSION))
            _write_meta(connection, META_AUTHORITY_UUID, authority_uuid)
            connection.execute("COMMIT")
        except BaseException:
            # The reservation was ours, so the half-built file is ours to
            # remove.  Leaving it would make the next `create` refuse on a store
            # that never existed and the next `open` refuse on one that is
            # empty -- two wrong answers where there should be none.
            if connection is not None:
                try:
                    connection.close()
                except sqlite3.Error:
                    pass
            try:
                os.unlink(path)
            except OSError:
                pass
            raise
        return Store(connection, path, authority_uuid)

    @staticmethod
    def open(path, *, expected_authority_uuid=None):
        """Open an EXISTING recognized Python-authority store.

        Every refusal below leaves the file byte-for-byte as it was found.
        """
        from .identity import check_authority_uuid

        _require_path(path)
        if expected_authority_uuid is not None:
            check_authority_uuid(expected_authority_uuid,
                                 what="expected_authority_uuid")
        status = _describe_target(path)
        if status is None:
            raise Refusal(
                f"there is no authority store at {name_of(path)}; open requires "
                f"an "
                f"existing store and create is the operation for a new one")
        if not os.path.stat.S_ISREG(status.st_mode):
            raise Refusal(
                f"the authority store path {name_of(path)} is not a regular "
                f"file; a "
                f"symlink or device is not a durable home for an authority UUID")
        if status.st_size == 0:
            raise Refusal(
                f"the file at {name_of(path)} is empty and is not an authority "
                f"store; an "
                f"interrupted creation leaves no store to open")

        # THE PROBE IS READ-ONLY, and that is the point.  A read-write open
        # would let SQLite write a journal, a WAL file or a PRAGMA into a
        # database we have not yet established is ours.
        recorded = _probe(path)
        _check_compatibility(path, recorded, expected_authority_uuid)

        # CONNECTED WITHOUT WRITING.  `busy_timeout` and `foreign_keys` are
        # per-connection settings that touch no byte of the file; the journal
        # mode is PERSISTENT and is therefore deliberately not set yet.  The
        # probe said this store is ours, but the probe is a fact about the past,
        # and setting a persistent mode before the recheck would modify a file
        # whose ownership this connection has not re-established.
        connection = _connect(path, persist_journal_mode=False)
        try:
            # RECHECKED UNDER THE WRITE LOCK.  Another process could have
            # replaced the file between the probe and this transaction, and the
            # first thing this connection does that matters is a write.
            connection.execute("BEGIN IMMEDIATE")
            committed = False
            try:
                live = _read_meta_all(connection)
                _check_compatibility(path, live, expected_authority_uuid)
                # Review [P1]: THE LIVE IDENTITY IS THE ONE THAT GOVERNS, and
                # the store used to be built from the PROBE's.  If the file was
                # replaced in the window by another valid Python-authority store
                # and no expected UUID was supplied, both checks passed and the
                # public `authority_uuid` named A while the connection governed
                # B -- an authority answering to two identities, which is the
                # one thing §4 says an `assignment_ref` must never be.
                #
                # A disagreement is REFUSED rather than silently resolved: the
                # caller made its decision to open against what the probe said,
                # and quietly handing back a different authority would answer a
                # question nobody asked.
                live_uuid = live[META_AUTHORITY_UUID]
                if live_uuid != recorded.get(META_AUTHORITY_UUID):
                    raise Refusal(
                        f"the store at {name_of(path)} was replaced while it "
                        f"was being "
                        f"opened; it is now a different authority, and this "
                        f"boundary hands back the one that was asked for or "
                        f"none")
                _apply_schema(connection)
                connection.execute("COMMIT")
                committed = True
            finally:
                # Review [P1]: this used to COMMIT in a `finally`, so a fault
                # partway through the schema COMMITTED the statements that had
                # already run.  A failed open left tables behind in somebody
                # else's database -- the exact outcome the whole non-adopting
                # design exists to prevent, reached through the error path
                # instead of the success one.
                if not committed:
                    connection.execute("ROLLBACK")
            # Now that the store has been re-established as ours under the write
            # lock, the persistent setting is ours to make.
            connection.execute("PRAGMA journal_mode = WAL")
        except BaseException:
            connection.close()
            raise
        return Store(connection, path, live_uuid)

    # -- connection ----------------------------------------------------------

    def close(self):
        self._db.close()

    @property
    def path(self):
        return self._path

    def get(self, sql, *args):
        row = self._db.execute(sql, args).fetchone()
        return None if row is None else dict(row)

    def all(self, sql, *args):
        return [dict(row) for row in self._db.execute(sql, args).fetchall()]

    def run(self, sql, *args):
        return self._db.execute(sql, args)

    # -- transactions --------------------------------------------------------

    # -- the operation journal ----------------------------------------------

    def operation_row(self, operation_id):
        return self.get("SELECT * FROM operation WHERE operation_id = ?",
                        operation_id)

    def operation_record(self, operation_id):
        """What the journal durably says about one identity.

        Audit-shaped: a retirement's whole job is to say WHICH operation died
        and why, so the record has to be readable even though `operation_result`
        answers only for a committed one.
        """
        row = self.operation_row(operation_id)
        if row is None:
            return None
        state = row["state"]
        if state == "committed":
            detail = None
        elif state == "retired":
            detail = json.loads(row["detail"])
        else:
            detail = row["detail"]
        return {
            "operation_id": operation_id,
            "state": state,
            "signature": row["signature"],
            "result": json.loads(row["result"]) if state == "committed" else None,
            "detail": detail,
        }

    def _record(self, operation_id, signature, state, result, detail, at):
        self.run(
            "INSERT INTO operation (operation_id, signature, state, result, "
            "detail, recorded_at) VALUES (?, ?, ?, ?, ?, ?)",
            operation_id, signature, state,
            json.dumps(result) if state == "committed" else None,
            detail, at)

    def record_retirement(self, operation_id, signature, record, at):
        self._record(operation_id, signature, "retired", None,
                     json.dumps(record), at)

    def _savepoint(self, body):
        """Run `body` inside a savepoint, and report which kind of failure it was.

        The savepoint is left OPEN on a refusal: only the caller knows whether
        that refusal wrote something it must keep.
        """
        name = f"sp_{self._savepoints}"
        self._savepoints += 1
        self._db.execute(f"SAVEPOINT {name}")
        try:
            value = body()
        except Refusal as refusal:
            return {"ok": False, "refusal": refusal, "name": name}
        except BaseException:
            self._db.execute(f"ROLLBACK TO {name}")
            self._db.execute(f"RELEASE {name}")
            raise
        self._db.execute(f"RELEASE {name}")
        return {"ok": True, "value": value}

    def replay(self, operation_id, signature, action, *, at):
        """Effectively-once over the FULL effective operands.

        Order matters and is the contract's, not convenience: RETIREMENT is
        answered before the signature, because §4 makes retirement a property of
        the operation IDENTITY rather than of one request's operands.  A stale
        submitter must learn the identity is dead, not that its operands
        disagree -- those are different facts and only one of them is true.
        """
        from .identity import check_opaque_id

        # An operation id is an opaque identity, and the frozen contract already
        # has a grammar for those -- `opaqueId`, 160 characters and a fixed
        # shape -- so this reuses it rather than inventing a limit.  Every id
        # this authority's own callers use, and every UUID, satisfies it.
        #
        # Review [P1]: this was the ONLY site that enforced it.  The shared
        # check now serves replay, settlement and both journal reads, so no two
        # paths can answer differently about the same string.
        check_opaque_id(operation_id,
                        "every mutating operation needs an operation id, and one")

        def body():
            prior = self.operation_row(operation_id)
            if prior is not None:
                if prior["state"] == "retired":
                    return {"ok": False, "refusal": Refusal(
                        json.loads(prior["detail"])["reason"])}
                if prior["signature"] != signature:
                    return {"ok": False, "refusal": Refusal(
                        "operation id was reused for different operands")}
                if prior["state"] == "refused":
                    return {"ok": False, "refusal": Refusal(prior["detail"])}
                return {"ok": True, "value": json.loads(prior["result"]),
                        "replayed": True}
            attempt = self._savepoint(action)
            if attempt["ok"]:
                value = attempt["value"]
                self._record(operation_id, signature, "committed", value, None, at)
                return {"ok": True, "value": value, "replayed": False}
            refusal = attempt["refusal"]
            if refusal.durable:
                # KEEP what the action wrote on its way to refusing, and bind
                # the refusal to this identity so the retry replays it rather
                # than appending a second attempt.  The RAISING transition
                # decides this, not the caller.
                self._db.execute(f"RELEASE {attempt['name']}")
                self._record(operation_id, signature, "refused", None,
                             refusal.message, at)
            else:
                self._db.execute(f"ROLLBACK TO {attempt['name']}")
                self._db.execute(f"RELEASE {attempt['name']}")
            return {"ok": False, "refusal": refusal}

        outcome = self.transact(body)
        if not outcome["ok"]:
            raise outcome["refusal"]
        return outcome["value"]

    def read_snapshot(self, body):
        """One READ transaction, so composed reads see ONE state of the world.

        Review [P0]: a projection read its Work row and its labels in separate
        autocommit statements, and a caller could close the Work and add a
        label between them -- so the projection returned an OPEN Work carrying
        a label that only existed after it closed. A state that never existed.
        The predicate reader had the same shape one table over: all label rows,
        then all Work rows, so a Work atomically created WITH an excluded label
        between the two came back as unlabelled.

        A COMMENT SAYING "ONE SNAPSHOT" IS NOT ONE, which the review said in as
        many words and which is the reason this exists as a seam rather than a
        promise. `BEGIN DEFERRED` takes the read lock at the first statement
        and holds that view until it ends, so every read inside the body is
        answered from the same state.

        It JOINS an open write transaction rather than opening a second, on
        `transact`'s rule and for its reason: a read composed inside a write
        already has the strongest view there is.
        """
        if self._depth > 0:
            # A READ JOINS A WRITE, which is the approved direction: a read
            # composed inside a write already has the strongest view there is.
            return body()
        self._db.execute("BEGIN DEFERRED")
        self._depth, self._reading = 1, True
        try:
            return body()
        finally:
            self._depth, self._reading = 0, False
            # A READ TRANSACTION ENDS BY ROLLBACK, because it wrote nothing and
            # `COMMIT` on a read-only view would be this build claiming an act
            # it did not perform.
            self._db.execute("ROLLBACK")

    def transact(self, body):
        """One write transaction.

        Nested calls JOIN the outer one rather than opening a second, so a
        transition that composes two helpers still commits exactly once.  The
        contract keeps insisting on atomicity across composed helpers -- "ONE
        transaction: fence the exact generation AND end the assignment" -- and a
        nested `BEGIN` that silently became a second transaction would break
        that without any statement looking wrong.
        """
        if self._depth > 0:
            # A WRITE MAY NOT JOIN A READ SNAPSHOT, and this refusal is the
            # correction review [P0] required. One `_depth` counter served both
            # modes, so a `transact` nested inside `read_snapshot` took this
            # join branch, performed its mutation, and returned a committed
            # answer -- which the snapshot's own `ROLLBACK` then threw away.
            # The caller was told an act was durable that was not.
            #
            # A write joining a write still joins, for the reason below.
            if getattr(self, "_reading", False):
                raise Refusal(
                    "a write cannot join a read snapshot: the snapshot ends in "
                    "ROLLBACK, so the mutation would be discarded after this "
                    "caller was told it committed. Take the write transaction "
                    "first and read inside it")
            self._depth += 1
            try:
                return body()
            finally:
                self._depth -= 1
        self._db.execute("BEGIN IMMEDIATE")
        self._depth = 1
        committed = False
        try:
            value = body()
            self._db.execute("COMMIT")
            committed = True
            return value
        finally:
            self._depth = 0
            if not committed:
                self._db.execute("ROLLBACK")


def _connect(path, *, persist_journal_mode=True):
    """One connection, owned by ONE process.

    Autocommit (`isolation_level=None`) because this module issues its own
    `BEGIN IMMEDIATE`: Python's implicit transaction management would otherwise
    open transactions this code did not ask for and commit them at times it did
    not choose.  Foreign keys are on because the schema declares them and a
    constraint nobody enforces is a comment.  The busy timeout is set BEFORE any
    other statement, so several processes opening one store contend by WAITING
    rather than by failing -- a competing claim must lose by being refused
    inside a transaction, which is a decision, not by failing to get a
    transaction at all, which is an error.
    """
    connection = sqlite3.connect(path, isolation_level=None, timeout=_BUSY_TIMEOUT_MS / 1000)
    connection.row_factory = sqlite3.Row
    connection.execute(f"PRAGMA busy_timeout = {_BUSY_TIMEOUT_MS}")
    connection.execute("PRAGMA foreign_keys = ON")
    # The journal mode is the only PERSISTENT setting here, so it is the only
    # one a caller may need to withhold until it has proved whose file this is.
    if persist_journal_mode:
        connection.execute("PRAGMA journal_mode = WAL")
    return connection


def _apply_schema(connection):
    """Run the schema INSIDE the caller's transaction.

    Not `executescript`: Python's sqlite3 COMMITS any open transaction before
    running a script, so a schema applied that way silently ends the
    `BEGIN IMMEDIATE` above it -- and with it the compatibility recheck that
    transaction exists to hold.  The failure is not an error; it is the
    transaction quietly finishing early, which is exactly the shape of bug this
    module's whole design is built against.  It cost one smoke test to find,
    and it would have cost a review round to find later.

    Statements are separated by `sqlite3.complete_statement`, the standard
    library's own answer to "is this a whole statement yet", rather than by
    splitting on semicolons and hoping none ever appears inside a literal.
    """
    statement = ""
    for line in SCHEMA.splitlines(keepends=True):
        statement += line
        if statement.strip() and sqlite3.complete_statement(statement):
            connection.execute(statement)
            statement = ""
    # W16821: the configuration generation is NOT seeded here.  This function
    # runs at open, before any injected clock exists, and a row dated by
    # `datetime.now()` would be durable evidence timed by the process rather
    # than by the authority's clock -- the same rule that keeps `clock` a
    # bootstrap operand.  `Core` treats an absent row as generation 1 and
    # writes one only when a configuration act bumps it, under the clock it
    # was constructed with.
    if statement.strip():
        raise Refusal("the authority schema ends with an incomplete statement")


def _write_meta(connection, key, value):
    connection.execute(
        "INSERT INTO meta (key, value) VALUES (?, ?) "
        "ON CONFLICT (key) DO NOTHING", (key, value))


def _read_meta_all(connection):
    try:
        rows = connection.execute("SELECT key, value FROM meta").fetchall()
    except sqlite3.DatabaseError:
        return None
    return {row[0]: row[1] for row in rows}


def _probe(path):
    """Read the store's own account of itself, without writing anything."""
    connection = None
    try:
        connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True,
                                     isolation_level=None)
        return _read_meta_all(connection)
    except sqlite3.DatabaseError:
        # Not a database at all, or not one this build can read.  Either way it
        # is not ours, and saying so is the whole answer.
        return None
    finally:
        if connection is not None:
            try:
                connection.close()
            except sqlite3.Error:
                pass


def _check_compatibility(path, recorded, expected_authority_uuid):
    """Whose store is this, how old is it, is its identity well formed, and is
    it the one we asked for."""
    """Whose store is this, how old is it, and is it the one we asked for.

    IN THAT ORDER, deliberately.  Kind before version, because "version 1"
    is true of the Node authority, the v11 authority and the manager's control
    store as well, and telling a caller their store is the wrong VERSION when it
    is actually the wrong PRODUCT sends them to fix the wrong thing.  Version
    before UUID, because a store this build cannot read is one whose recorded
    UUID it also cannot trust.
    """
    from .identity import check_authority_uuid

    if recorded is None or META_STORE_KIND not in recorded:
        raise Refusal(
            f"the file at {name_of(path)} is not a {STORE_KIND} store; this "
            f"authority "
            f"opens its own stores and adopts nothing -- not the Node v12 "
            f"authority, not v11, not a worker-manager control store, not an "
            f"arbitrary SQLite file")
    kind = recorded[META_STORE_KIND]
    if kind != STORE_KIND:
        raise Refusal(
            f"the store at {name_of(path)} is {name_of(kind)}, not "
            f"{STORE_KIND}; a "
            f"shared schema version number is not shared ownership")
    version = recorded.get(META_SCHEMA_VERSION)
    if version != str(SCHEMA_VERSION):
        # W16821, approver ruling M33752.  A store of OUR kind at a version
        # this build does not speak is refused READ-ONLY and the operator is
        # told what to do about it.
        #
        # THE REFUSAL IS THE WHOLE HANDLING.  Nothing here opens the file for
        # writing, reads a row out of it, deletes it, renames it, upgrades it,
        # or applies any part of the new schema to it: the caller reached this
        # function with a `recorded` dictionary from a read-only probe, and it
        # leaves with an exception.  A build that "helpfully" migrated would be
        # inventing the principal, effective scope and grant provenance schema
        # 2 requires and schema 1 never recorded -- the exact inference the
        # correction boundary forbids -- and it would do it to a file it has
        # not been authorized to change.
        #
        # DELETION IS THE OPERATOR'S ACT, not this build's.  v12 stores are
        # disposable proof state and the ruling says no migration is required
        # for them; it does not say a program may delete somebody's database
        # because it decided the contents were expendable.
        raise Refusal(
            f"the authority at {name_of(path)} is schema {name_of(version)} "
            f"and this build speaks schema {SCHEMA_VERSION}; this authority "
            f"does not migrate, in either direction, and has not read, "
            f"changed or removed one byte of that file. If it is a disposable "
            f"proof store, remove it and initialize a fresh one; if its state "
            f"must survive, a migration is separate product Work and this "
            f"build is not it")
    uuid = recorded.get(META_AUTHORITY_UUID)
    if uuid is None:
        raise Refusal(
            f"the authority at {name_of(path)} records no authority UUID; "
            f"every "
            f"assignment identity in a store names one, and a store that "
            f"cannot say which is not openable")
    # Review [P1]: the recorded UUID was checked for EXISTENCE and, only when a
    # caller happened to supply an expected one, for equality.  So a
    # marker-only file recording `not-a-uuid` was a recognized authority, and
    # opening it grew the full schema inside it.  Presence is not validity, and
    # the grammar is the same one every assignment identity is held to -- the
    # durable value has to satisfy it or nothing built from it can.
    #
    # This runs on BOTH the probe and the live recheck, because it is
    # `_check_compatibility` and both calls go through here.
    check_authority_uuid(
        uuid, what=f"the authority UUID recorded at {name_of(path)}")
    if expected_authority_uuid is not None and uuid != expected_authority_uuid:
        raise Refusal(
            f"the authority at {name_of(path)} is {name_of(uuid)}, not "
            f"{name_of(expected_authority_uuid)}; "
            f"an authority UUID is durable and is never reassigned")
