"""The integration coordinator's store: one transaction boundary, one journal.

W71878. The mechanism is the one `JobStore` and the Worker Manager's
`ControlStore` already use -- `transact` is the atomic boundary and `replay` is
what makes a repeated request return the FIRST outcome instead of performing it
twice -- applied to a database neither of them may own.

WHY A THIRD STORE RATHER THAN A THIRD TABLE IN THE SECOND ONE. `JobStore` is
bound immutably to one Authority UUID by W83781, and refuses an open under
another. That binding is right for a Job store and fatal for a target lock: two
Authorities addressing one canonical target hold two Job stores, so a unique
index there excludes nothing between them. The owner ruled on 2026-09-05 that
integration ordering and exclusion live in a store whose transaction domain is
independent of every Authority-bound one, and this is that store.

SO IT RECORDS NO AUTHORITY BINDING AT ALL, which is the one place this class
deliberately differs from `JobStore` rather than resembling it. Binding it
would put the defect back one layer down. What is Authority-specific travels
inside an immutable entry as evidence.

WHAT IS REUSED RATHER THAN COPIED. `seal_refusal` is the manager's public
helper for the closed refusal pair, and `boundaries` is the one owner of every
crossing. Its partner `revive_refusal` is NOT here: reviving a recorded refusal
is answering a caller with a recorded act, and after the eighth review of
2026-09-06 that belongs to the witness with every other outcome. What is also
not reused is either sibling's signature helper: one store's answer to "are
these the same request" is not another's, however identical the serialization
looks.

WHERE THIS STORE STOPS AND `queue` BEGINS. This module owns the transaction,
the operation identity, the durable ORDER of the acts and the adoption of an
operation row. It owns no queue semantics at all, so `replay` cannot decide
whether a recorded act is the act it claims to be -- and after the seventh
review of 2026-09-06 it is not allowed to guess. Every caller supplies the
`witness` that owns a recorded act semantically, and there is no default,
because a default is how the one path that skipped every proof got there.
`replay` therefore does not branch on a recorded act's outcome either -- the
eighth review found the refused branch answering before the witness ran.

AND IT OWNS THE SNAPSHOT THOSE PROOFS OBSERVE. `snapshot` is the read
transaction that makes a multi-statement proof one observation of one state.
"""

import json
import os
import re
import sqlite3

from ..contracts import (ContractRefusal, canonical_text,
                         check_no_durable_secret, own)
from ..contracts.errors import name_value
from ..worker_manager import boundaries
from ..worker_manager.store import seal_refusal
from .schema import (MIGRATIONS, OPERATION_COLUMNS, SCHEMA, SCHEMA_VERSION,
                     STORE_KIND)

__all__ = ["IntegrationStore", "integration_signature"]

_BUSY_TIMEOUT_MS = 5000
_META_STORE_KIND = "store_kind"
_META_SCHEMA_VERSION = "schema_version"


def integration_signature(kind, operands):
    """The stable text one coordinator act's operands are compared as."""
    boundaries.text(kind, "an operation kind")
    # §13 AT THE CONSTRUCTOR rather than at the eventual write, for the reason
    # `job_signature` gives: a caller holding a signature that contains a live
    # bearer already holds the leak before any journal walk could refuse it.
    check_no_durable_secret({"kind": kind, "operands": operands},
                            what="an integration operation signature")
    return canonical_text({"kind": kind, "operands": operands})


def _refuse(message, *, category="integrity", code="schema"):
    raise ContractRefusal(category, code, message)


# The SQLite header byte that says which journal mode a file was left in. Byte
# 18 is the write version; `2` is write-ahead logging.
_HEADER_BYTES = 20
_HEADER_WAL = 2


def _connect_readonly(path):
    """One connection that CANNOT write, or a refusal naming why.

    W126887, and the same measured limit its Authority sibling reports.
    `mode=ro` is the whole guarantee: SQLite refuses every write on it.
    `immutable=1` is deliberately NOT used -- it asserts the file cannot
    change, which is false of a live coordinator two Authorities may be
    contending for, and would hand back stale or torn reads.

    THE SIDECARS ARE THE ONE REAL LIMIT AND IT IS NAMED. Reading a WAL
    database needs `-wal` and `-shm`, and SQLite CREATES them when they are
    absent -- from a `mode=ro` connection too, because they are not the
    database. Creating a journal artifact is what this opener may not do, so a
    store nobody is holding is refused here and its files are left exactly as
    they were. A readable main file is not proof the whole store is
    accessible.
    """
    try:
        with open(path, "rb") as handle:
            header = handle.read(_HEADER_BYTES)
    except OSError as failure:
        _refuse(f"the integration coordinator store at {name_value(path)} "
                f"could not be read: {type(failure).__name__}",
                category="refused", code="precondition")
    if len(header) >= _HEADER_BYTES and header[18] == _HEADER_WAL \
            and not any(os.path.lexists(path + one)
                        for one in ("-wal", "-shm")):
        _refuse(f"the integration coordinator store at {name_value(path)} is "
                f"a write-ahead-log store whose -wal and -shm sidecars are "
                f"absent, so no process is holding it; opening it at all "
                f"would make SQLite create both, and a read-only open creates "
                f"no journal artifact. Read it while its coordinator holds "
                f"it, or open it for writing deliberately",
                category="refused", code="precondition")
    try:
        connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True,
                                     isolation_level=None,
                                     timeout=_BUSY_TIMEOUT_MS / 1000)
    except sqlite3.Error as failure:
        _refuse(f"the integration coordinator store at {name_value(path)} "
                f"could not be opened for reading "
                f"({type(failure).__name__}); a read-only open refuses rather "
                f"than reopening a store it may not write",
                category="refused", code="precondition")
    try:
        connection.row_factory = sqlite3.Row
        connection.execute(f"PRAGMA busy_timeout = {_BUSY_TIMEOUT_MS}")
        connection.execute("PRAGMA foreign_keys = ON")
        # THE FIRST REAL READ IS WHERE AN UNREACHABLE SIDECAR ANNOUNCES
        # ITSELF, so it is made here and translated once.
        connection.execute("SELECT 1").fetchone()
    except sqlite3.Error as failure:
        connection.close()
        _refuse(f"the integration coordinator store at {name_value(path)} is "
                f"not readable through a non-writing connection "
                f"({type(failure).__name__}: {failure}); this refuses rather "
                f"than opening the store in a mode that would repair it",
                category="refused", code="precondition")
    return connection


def _statements(script):
    """Split where SQLITE says a statement ends, not at every semicolon.

    MEASURED, not anticipated: splitting on `;` cut one `CREATE TABLE` in half
    the moment a schema comment contained a semicolon, and the store then
    failed to build at all. `complete_statement` is SQLite's own answer to "is
    this a whole statement", so a semicolon inside a comment or a string
    literal stays inside the statement it belongs to. The commentary is kept in
    the executed text on purpose: it is what `.schema` shows an operator
    holding a database this build wrote.
    """
    statements, buffer = [], ""
    for line in script.splitlines(keepends=True):
        buffer += line
        if sqlite3.complete_statement(buffer):
            statements.append(buffer.strip())
            buffer = ""
    if buffer.strip():
        statements.append(buffer.strip())
    return statements


# THE THREE NORMALIZATIONS, and each one reconciles a spelling difference that
# was MEASURED rather than imagined. SQLite hands back the text of the CREATE
# statement it was given, so one shape can be spelled several ways: a rebuilt
# table carries no `--` commentary, a tool-written one quotes its identifiers,
# and hand-written punctuation spacing varies. None of the three changes what
# the definition MEANS.
#
# CASE IS NOT NORMALIZED, deliberately. Identifiers are case-insensitive in
# SQLite and string literals are not, so folding case would make
# `state IN ('open')` and `state IN ('OPEN')` compare equal -- two different
# constraints, silently reconciled.
_COMMENT = re.compile(r"--[^\n]*")
_PUNCTUATION = re.compile(r"([(),])")


def _definition(sql):
    bare = _COMMENT.sub("", sql or "")
    spaced = _PUNCTUATION.sub(r" \1 ", bare.replace('"', ""))
    return " ".join(spaced.split())


def _shape(connection):
    """Every object this build owns, keyed by kind and name.

    `sqlite_%` names are SQLite's own -- the auto-indexes a UNIQUE constraint
    implies are already stated by the table definition that implies them, so
    comparing them would be comparing one fact twice.
    """
    return {(row["type"], row["name"]): _definition(row["sql"])
            for row in connection.execute(
                "SELECT type, name, sql FROM sqlite_master "
                "WHERE name NOT LIKE 'sqlite_%'")}


_EXPECTED = None


def expected_shape():
    """This build's own schema, measured by BUILDING it rather than restating.

    A hand-written expectation is a second owner of the shape and drifts from
    `SCHEMA` the first time either changes. This runs the real script into a
    throwaway database and reads back what SQLite stored, so the expectation
    cannot disagree with what `_initialize` writes.
    """
    global _EXPECTED
    if _EXPECTED is None:
        scratch = sqlite3.connect(":memory:")
        try:
            scratch.row_factory = sqlite3.Row
            for statement in _statements(SCHEMA):
                scratch.execute(statement)
            _EXPECTED = _shape(scratch)
        finally:
            scratch.close()
    return _EXPECTED


class _Snapshot:
    """The read transaction `IntegrationStore.snapshot` hands out."""

    __slots__ = ("_connection", "_owned")

    def __init__(self, connection):
        self._connection = connection
        self._owned = False

    def __enter__(self):
        if not self._connection.in_transaction:
            # DEFERRED rather than IMMEDIATE: this reads and never writes, so
            # taking the write lock would serialize two coordinators' reads
            # against each other for nothing. The snapshot begins at the first
            # statement inside it and holds until it ends.
            self._connection.execute("BEGIN DEFERRED")
            self._owned = True
        return self

    def __exit__(self, kind, value, traceback):
        if self._owned:
            # A read changes nothing, so ending it is a rollback rather than a
            # commit -- and it must happen on the failure path too, or one
            # refusal would leave the connection holding a snapshot forever.
            self._connection.execute("ROLLBACK")
            self._owned = False
        return False


class IntegrationStore:
    """One coordinator database, keyed by its targets and by nothing else."""

    def __init__(self, connection, *, incarnation, clock, readonly=False):
        self._connection = connection
        self.incarnation = incarnation
        self._clock = clock
        # W126887: WHETHER THIS HANDLE MAY WRITE, decided at the open and never
        # afterwards. The connection behind a read-only handle cannot write
        # either -- SQLite refuses it -- but a `sqlite3` error arriving from
        # inside a transition is not this coordinator's refusal, and by the
        # time one appears the transition has already decided things.
        self._readonly = readonly
        # THE ONE ACT CURRENTLY BETWEEN ITS WRITE AND ITS RECORD.
        #
        # A materialized transition and its journal row commit together, so no
        # EXTERNAL reader can ever observe one without the other. Inside
        # `transact` there is exactly one instant where they differ: the action
        # has written and `_record` has not run. The queue's history proof is
        # told which act that is, by identity, so the window it allows is that
        # act and nothing else -- never a general "this row has no record yet"
        # allowance, which would readmit every fabricated row.
        self._pending = None

    @classmethod
    def open(cls, path, *, incarnation, clock):
        boundaries.text(path, "an integration coordinator store path")
        boundaries.text(incarnation, "a coordinator incarnation")
        boundaries.capability(clock, "the coordinator's instant source")
        connection = sqlite3.connect(path, isolation_level=None,
                                     timeout=_BUSY_TIMEOUT_MS / 1000)
        try:
            connection.execute(f"PRAGMA busy_timeout = {_BUSY_TIMEOUT_MS}")
            connection.row_factory = sqlite3.Row
            if cls._objects(connection):
                cls._adopt(connection, path)
            else:
                cls._initialize(connection)
            # CONCURRENT SNAPSHOTS, AND ONLY ONCE THE STORE IS OURS. Eighth
            # review of 2026-09-06 [P1]: a semantic proof must observe one
            # snapshot, and `snapshot` below is the read transaction that gives
            # it one. Under a rollback journal that transaction also blocks
            # every writer for its duration, which would turn one coordinator's
            # ordinary read into the other's timeout -- in a store whose entire
            # premise is two Authorities contending for one target. In WAL a
            # reader holds its snapshot while writers commit, which is the
            # shape this store's own contract asks for.
            #
            # AFTER the ownership decision, never before: a database this build
            # refuses must be left exactly as it was found, and setting a
            # journal mode is a change.
            cls._concurrent(connection, path)
            store = cls(connection, incarnation=incarnation, clock=clock)
            # Proved after the store exists and inside this handler, so a clock
            # that cannot stamp a row is found at open rather than at the first
            # journalled act -- and the connection is still closed.
            store._now()
        except BaseException:
            try:
                connection.close()
            except BaseException:
                pass
            raise
        connection.execute("PRAGMA foreign_keys = ON")
        return store

    @classmethod
    def open_readonly(cls, path, *, incarnation, clock):
        """Open an EXISTING recognized coordinator through a non-writing
        connection.

        W126887, `work/records/2026/09/finding-v12-composed-ending-consumer/
        findings/finding-readonly-coordinator-open/`.

        WHY `open` IS NOT THIS. It creates an absent store, initializes an
        empty one under `BEGIN IMMEDIATE`, and asks for a persistent journal
        mode -- right for a coordinator that is about to act, and the reason a
        separate status process had no way to read committed entry, lease and
        history evidence at all.

        THE OWNERSHIP DECISION IS THE SAME ONE, on the connection that is
        handed back and inside this store's own `snapshot`. `_adopt` refuses a
        foreign store, a store carrying metadata this build does not own, and
        one at another schema version, leaving each exactly as found; an EMPTY
        database is refused here rather than initialized, which is the one
        place this opener's answer differs from `open`'s and the reason it
        differs.

        IT CREATES NOTHING AND CHANGES NOTHING: no schema, no migration, no
        write lock, no checkpoint, no persistent PRAGMA, no permissions
        change. The store stays target-keyed and acquires no Authority
        identity.
        """
        boundaries.text(path, "an integration coordinator store path")
        boundaries.text(incarnation, "a coordinator incarnation")
        boundaries.capability(clock, "the coordinator's instant source")
        if not os.path.lexists(path):
            _refuse(f"there is no integration coordinator store at "
                    f"{name_value(path)}; a read-only open requires an "
                    f"existing store and creates none",
                    category="refused", code="precondition")
        connection = _connect_readonly(path)
        try:
            store = cls(connection, incarnation=incarnation, clock=clock,
                        readonly=True)
            with store.snapshot():
                if not cls._objects(connection):
                    _refuse(f"the database at {name_value(path)} holds no "
                            f"objects; a read-only open reads an initialized "
                            f"coordinator and initializes nothing",
                            category="refused", code="precondition")
                cls._adopt(connection, path)
            # Proved after the store exists and inside this handler, exactly as
            # `open` does it, so a clock that cannot stamp is found here rather
            # than at the first read that wants one.
            store._now()
        except BaseException:
            try:
                connection.close()
            except BaseException:
                pass
            raise
        return store

    @staticmethod
    def _concurrent(connection, path):
        """Ask for WAL, and record what the filesystem actually gave.

        NOT A REFUSAL, AND THE TRY BELOW IS WHAT MAKES THAT TRUE. Coherence is
        the read transaction's, and that holds in either journal mode; WAL only
        decides whether a reader's snapshot blocks a concurrent writer or runs
        beside it. A filesystem that cannot do WAL, or an instant at which
        another opener holds the file, therefore gets a correct store with a
        narrower concurrency story -- a deployment fact worth reading off the
        connection rather than a reason to refuse to open.
        """
        try:
            connection.execute("PRAGMA journal_mode = WAL")
        except sqlite3.OperationalError:
            # BUSY, OR A FILESYSTEM THAT CANNOT, AND NEITHER IS A REASON TO
            # REFUSE AN OPEN. Switching the journal mode needs the file to
            # itself, and `PRAGMA journal_mode` is one of the statements that
            # can answer BUSY without the busy handler retrying it -- so two
            # coordinators opening one store at the same instant can leave one
            # of them holding a raw `sqlite3.OperationalError` out of a public
            # constructor. MEASURED rather than anticipated: the sibling
            # `ControlStore` does this inside `_initialize` and a parallel
            # suite raced it exactly there.
            #
            # The store that results is CORRECT either way -- coherence belongs
            # to the read transaction in `snapshot`, not to the journal mode --
            # so what is lost is the non-blocking reader, which is a
            # concurrency story rather than a safety one. The mode is read back
            # and returned so a caller that cares can see which one it got.
            pass
        answered = connection.execute("PRAGMA journal_mode").fetchone()
        return None if answered is None else answered[0]

    @staticmethod
    def _objects(connection):
        return [row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'")]

    @classmethod
    def _initialize(cls, connection):
        """One transaction, so a crash mid-DDL leaves no half-built store."""
        connection.execute("BEGIN IMMEDIATE")
        try:
            if cls._objects(connection):
                # Somebody else won the race to create it. Roll back and decide
                # the store they made by exactly the rule any other existing
                # store is decided by.
                connection.execute("ROLLBACK")
                cls._adopt(connection, "(concurrently created)")
                return
            for statement in _statements(SCHEMA):
                connection.execute(statement)
            connection.execute("INSERT INTO meta (key, value) VALUES (?, ?)",
                               (_META_STORE_KIND, STORE_KIND))
            connection.execute("INSERT INTO meta (key, value) VALUES (?, ?)",
                               (_META_SCHEMA_VERSION, str(SCHEMA_VERSION)))
            connection.execute("COMMIT")
        except BaseException:
            try:
                connection.execute("ROLLBACK")
            except BaseException:
                pass
            raise

    @classmethod
    def _adopt(cls, connection, path):
        """Decide a non-empty database: ours, or refused untouched.

        The NAME `meta` is not permission to read `key, value` out of it: a
        foreign database reusing a generic table name is still foreign, so the
        probe runs inside the taxonomy rather than in front of it.
        """
        if "meta" not in cls._objects(connection):
            _refuse(f"the database at {name_value(path)} holds objects and "
                    f"none is this coordinator's metadata, so it is not a "
                    f"store this build owns. Nothing was changed")
        try:
            recorded = {row["key"]: row["value"] for row in
                        connection.execute("SELECT key, value FROM meta")}
        except sqlite3.Error as failure:
            _refuse(f"the database at {name_value(path)} carries a meta table "
                    f"this coordinator cannot read "
                    f"({type(failure).__name__}), so it is not a store this "
                    f"build owns. Nothing was changed")
        if recorded.get(_META_STORE_KIND) != STORE_KIND:
            _refuse(f"the database at {name_value(path)} is "
                    f"{name_value(recorded.get(_META_STORE_KIND))} and this "
                    f"build owns {name_value(STORE_KIND)}; a store is adopted "
                    f"by ownership rather than by resemblance. Nothing was "
                    f"changed")
        unexpected = sorted(set(recorded) - {_META_STORE_KIND,
                                            _META_SCHEMA_VERSION})
        if unexpected:
            _refuse(f"the integration coordinator store at {name_value(path)} "
                    f"carries metadata this build does not own "
                    f"({', '.join(unexpected)}); a store is adopted by "
                    f"ownership rather than by resemblance. Nothing was "
                    f"changed")
        version = recorded.get(_META_SCHEMA_VERSION)
        if version != str(SCHEMA_VERSION):
            # NO MIGRATION IS INVENTED. `MIGRATIONS` is empty and there is no
            # earlier shape; a store at another version is refused rather than
            # guessed across, which is the rule every store here is under.
            _refuse(f"the integration coordinator store at {name_value(path)} "
                    f"is schema {name_value(version)}; this build is "
                    f"{SCHEMA_VERSION}, carries no migration from that "
                    f"version, and does not guess across versions. Nothing "
                    f"was changed")
        # THE WHOLE OWNED SHAPE, NOT A LIST OF TABLE NAMES. Review of
        # 2026-09-06 [P1]: this checked that four names existed, so a database
        # with `leases_one_live_per_target` DROPPED reopened without complaint
        # -- and that partial index is not an optimization, it IS the
        # one-live-lease-per-target exclusion this store exists to enforce. A
        # missing constraint is not a missing convenience; it is a store whose
        # central safety property silently is not there.
        expected = expected_shape()
        found = _shape(connection)
        missing = sorted(f"{kind} {name}" for kind, name in expected
                         if (kind, name) not in found)
        if missing:
            _refuse(f"the integration coordinator store at {name_value(path)} "
                    f"says it is schema {SCHEMA_VERSION} and is missing "
                    f"{', '.join(missing)}. Nothing was changed")
        extra = sorted(f"{kind} {name}" for kind, name in found
                       if (kind, name) not in expected)
        if extra:
            _refuse(f"the integration coordinator store at {name_value(path)} "
                    f"carries {', '.join(extra)}, which this build does not "
                    f"own; a store this process cannot reason about entirely "
                    f"is not one it adopts. Nothing was changed")
        altered = sorted(f"{kind} {name}" for kind, name in expected
                         if found[(kind, name)] != expected[(kind, name)])
        if altered:
            _refuse(f"the integration coordinator store at {name_value(path)} "
                    f"defines {', '.join(altered)} differently from this "
                    f"build, so its constraints are not the ones this build "
                    f"relies on. Nothing was changed")

    def _now(self):
        return boundaries.instant(self._clock(), "the coordinator's instant")

    # -- the journalled boundary ---------------------------------------------

    def transact(self, operation_id, kind, signature, action, *, witness):
        """One atomic coordinator act, journalled by its operation identity.

        The collision check is made INSIDE the transaction, because two
        coordinators can reach it concurrently and a read-then-write check
        outside would let both through.

        `witness` is the semantic owner of a recorded act, and it is required
        rather than defaulted for the reason the seventh review of 2026-09-06
        gives: a replay that trusts the raw journal is a door into this store
        that every proof above it misses.
        """
        # W126887: A READ-ONLY HANDLE PERFORMS NO ACT, and it says so here --
        # before the operands are owned, before the transaction, and before
        # anything external. A `sqlite3` error out of the middle of a
        # coordinator act is not a refusal a caller handling ContractRefusal
        # would handle, and by then the act has already begun.
        if self._readonly:
            _refuse("this integration coordinator store was opened for "
                    "reading and performs no act; a read-only handle answers "
                    "the committed record and journals nothing",
                    category="refused", code="capability")
        boundaries.identity(operation_id, "an operation identity")
        boundaries.capability(action, "the journalled action")
        boundaries.text(kind, "an operation kind")
        found, value = self.replay(operation_id, signature, kind=kind,
                                   witness=witness)
        if found:
            return value
        connection = self._connection
        connection.execute("BEGIN IMMEDIATE")
        try:
            # RE-READ INSIDE THE LOCK. The peek above answers the sequential
            # case without taking a write lock; this is the one that decides.
            found, value = self.replay(operation_id, signature, kind=kind,
                                       witness=witness)
            if found:
                connection.execute("ROLLBACK")
                return value
            connection.execute("SAVEPOINT act")
            self._pending = {"operation_id": operation_id, "kind": kind,
                             "signature": signature}
            try:
                result = action(connection)
            except ContractRefusal as refusal:
                if refusal.durable:
                    # A durable refusal is itself a committed outcome, so its
                    # record must survive and the retry must REPLAY it rather
                    # than re-decide it.
                    sealed = seal_refusal(refusal)
                    connection.execute("RELEASE act")
                    self._record(operation_id, kind, signature, "refused",
                                 None, sealed)
                    connection.execute("COMMIT")
                    raise
                connection.execute("ROLLBACK TO act")
                connection.execute("ROLLBACK")
                raise
            except BaseException:
                connection.execute("ROLLBACK TO act")
                connection.execute("ROLLBACK")
                raise
            finally:
                self._pending = None
            connection.execute("RELEASE act")
            committed = own(result, what="an operation result")
            self._record(operation_id, kind, signature, "committed",
                         canonical_text(committed), None)
            connection.execute("COMMIT")
            return committed
        except BaseException:
            try:
                connection.execute("ROLLBACK")
            except BaseException:
                pass
            raise

    def _record(self, operation_id, kind, signature, state, result, refusal):
        """Append one act, at the next position in this store's durable order.

        THE POSITION IS ALLOCATED HERE, inside the act's own transaction, by
        exactly the rule `enqueue` allocates a rank by. Two coordinators
        reaching this concurrently are serialized by the write lock they are
        already holding, so `MAX(seq) + 1` cannot hand two acts one position --
        and `UNIQUE` says so in the schema rather than in this comment.
        """
        seq = self._connection.execute(
            "SELECT COALESCE(MAX(seq), 0) + 1 FROM operations").fetchone()[0]
        self._connection.execute(
            "INSERT INTO operations (seq, operation_id, kind, signature, "
            "state, result, refusal, settled_at) VALUES (?, ?, ?, ?, ?, ?, ?, "
            "?)",
            (seq, operation_id, kind, signature, state, result,
             None if refusal is None else canonical_text(refusal),
             self._now()))

    def replay(self, operation_id, signature, *, kind=None, witness):
        """`(found, value)` for one operation identity, PROVED before it is
        returned.

        PRESENCE IS ITS OWN FACT: `None` also means "the committed result was
        JSON null", and effectively-once cannot be built on a value that also
        means absence.

        AND PRESENCE IS NOT PROOF. Seventh review of 2026-09-06 [P0]: this read
        the row, compared the caller's raw signature text and handed back
        `json.loads(result)`. Every semantic owner above it -- the operand
        contract, the derived identity, the result variant, the whole
        materialized relationship -- was reached by ordinary reads and by first
        executions and by NOTHING ELSE, so the retry path that exists to make a
        transition effectively once was the one path that believed the journal
        without reading it. A rewritten result replayed as the caller's answer,
        and a fabricated committed settlement replayed as a successful
        post-import cutpoint over an entry still `leased`.
        """
        boundaries.identity(operation_id, "an operation identity")
        boundaries.capability(witness, "a recorded act's semantic owner")
        # ONE SNAPSHOT FOR THE WHOLE PROOF. Eighth review [P1]: the witness was
        # semantically complete and transactionally incoherent -- it read the
        # row here and its target, entries, leases and journal in separate
        # autocommit statements, so an ordinary concurrent grant landing
        # between two of them made a SOUND retry assemble one proof from two
        # committed states and report corruption instead of its first outcome.
        with self.snapshot():
            found = self._connection.execute(
                "SELECT * FROM operations WHERE operation_id = ?",
                (operation_id,)).fetchone()
            if found is None:
                return (False, None)
            # THE ROW IS PERSISTED INPUT, adopted here as it is adopted
            # wherever the durable history is read. The collision check runs on
            # the adopted text, so an id reused under other operands is still
            # told what it is rather than being diagnosed as corruption.
            row = boundaries.row(found, "a persisted operation record",
                                 OPERATION_COLUMNS)
            if row["signature"] != signature or (kind is not None
                                                 and row["kind"] != kind):
                raise ContractRefusal(
                    "refused", "operation-collision",
                    f"operation {name_value(operation_id)} is already recorded "
                    f"with a different kind or signature; reusing an id with "
                    f"different operands changes nothing")
            # BOTH OUTCOMES GO TO THE WITNESS, and the eighth review's second
            # [P1] is why there is no branch here at all. This module owns no
            # queue semantics, so it cannot own the difference between a
            # committed act and a refused one either: it read `state`, revived
            # the sealed refusal and returned before the witness ran, and a
            # refused retry therefore skipped the kind, operand, identity and
            # dense-order proofs that a committed one reached.
            return (True, witness(self, row))

    def snapshot(self):
        """One coherent read snapshot, or the caller's transaction if it holds
        one.

        A PROOF ASSEMBLED FROM INDEPENDENTLY COMMITTED READS IS NOT A PROOF.
        Eighth review [P1]: the relationship pass reads a target row, then its
        entries, then its leases, then the whole journal. Every one of those
        was its own autocommit statement, so a perfectly ordinary grant
        committing between two of them produced a composite that never existed
        -- a target at fence 0 beside a journal at fence 1 -- and the reader
        reported that as corruption.

        RE-ENTRANT ON PURPOSE. Inside `transact` the caller already holds the
        write transaction, and that IS the snapshot; opening a second one would
        be an error rather than a stronger guarantee. So this yields to the
        transaction in progress and owns only the case where there is none.
        """
        return _Snapshot(self._connection)

    def close(self):
        self._connection.close()

    def __enter__(self):
        return self

    def __exit__(self, kind, value, traceback):
        self.close()
        return False
