"""The Job store: one transaction boundary and one journal.

W71875. The mechanism is the Worker Manager control store's, applied to this
leaf's own database: `transact` is the atomic boundary and `replay` is what
makes a repeated request return the FIRST outcome instead of performing it
twice. Journalling outside the transaction that did the work would let a crash
leave a mutation with no operation record, and the next sweep would do it
again -- which for a scheduler means a second offer against Work that already
has one.

WHY THIS IS A SEPARATE CLASS RATHER THAN `ControlStore` OPENED TWICE. That
class validates the manager's store KIND and creates the manager's schema, and
both are correct: adopting a database because it is "a v12 store" is exactly
the ownership-not-presence failure the manager was corrected for. So this
store carries its own kind and its own schema and refuses the manager's
database as firmly as the manager refuses this one.

WHAT IS REUSED RATHER THAN COPIED. `seal_refusal` and `revive_refusal` are the
manager's public helpers for the closed refusal pair, and the outcome they
seal is this distribution's own `ContractRefusal` either way -- so a second
implementation here would be a second chance to get the durable/ordinary split
wrong. What is NOT reused is the manager's `manager_signature`: that is the
manager's fact about whether two requests are the same request, and this store
answers the same question about a scheduler's acts. One store's identity is
not another store's, however identical the serialization looks.
"""

import json
import re
import sqlite3

from ..contracts import (ContractRefusal, canonical_text,
                         check_no_durable_secret, own)
from ..contracts.errors import name_value, sample_of
from ..worker_manager import boundaries
from ..worker_manager.store import revive_refusal, seal_refusal
from . import schema
from .schema import (MIGRATIONS, SCHEMA, SCHEMA_VERSION, STORE_KIND,
                     check_authority)

__all__ = ["JobStore", "job_signature"]

_BUSY_TIMEOUT_MS = 5000
_SQLITE_BUSY = 5
_SQLITE_LOCKED = 6
_META_STORE_KIND = "store_kind"
_META_SCHEMA_VERSION = "schema_version"
# W83781: WHICH AUTHORITY THIS STORE BELONGS TO, persisted once and immutable.
#
# It is a BINDING and not a capability. The Authority, the Worker Manager
# control store and this one remain separate files with separate owners; what
# is recorded here is a stable public identity, and holding it grants no
# session, no store path and no mutation surface. `submit` and read-only
# `status` learn exactly this and nothing else, which is what lets them keep
# constructing no Authority at all.
_META_AUTHORITY_UUID = "authority_uuid"

_SIGNATURE_MEMBERS = ("kind", "operands")


def _is_contention(failure):
    """Whether SQLite says another connection owns the needed lock.

    The low byte is the primary result code; high bits carry an extended
    reason. Free-form exception prose does not choose storage policy, and a
    failure with no structured code keeps its original identity.
    """
    code = getattr(failure, "sqlite_errorcode", None)
    if type(code) is not int:
        return False
    return code & 0xff in (_SQLITE_BUSY, _SQLITE_LOCKED)


_PUNCTUATION = re.compile(r"([(),])")
# `--` to end of line. This schema's string literals are single-quoted and
# carry no `--`, so there is nothing for it to eat but a comment.
_COMMENT = re.compile(r"--[^\n]*")


def _definition(sql):
    """One SQL definition, compared by its content rather than its spelling.

    WHITESPACE AND IDENTIFIER QUOTING ONLY. A renamed table's stored header is
    `CREATE TABLE "stages"` where an install's is `CREATE TABLE stages`, and
    the two are the same table; everything else -- columns, CHECK expressions,
    partial-index predicates -- is content and must match.

    Punctuation is spaced out before the collapse, because `meta (key TEXT` and
    `meta ( key TEXT` are one table written by two hands -- an installed schema
    and a hand-written historical fixture -- and a comparison that called those
    different would refuse a store for its typography.

    Double quotes are SQLite's IDENTIFIER quoting; string literals in this
    schema use single quotes, which are left exactly as they are, so a CHECK's
    vocabulary is compared as itself.
    """
    # COMMENTS GO FIRST, and while the newlines are still there to end them.
    # SQLite stores the definition verbatim, so `SCHEMA`'s explanation of the
    # all-three-or-none ending CHECK is part of `episodes`' recorded text and
    # `MIGRATIONS[1]`'s copy of the same table has no comment at all.
    bare = _COMMENT.sub("", sql or "")
    spaced = _PUNCTUATION.sub(r" \1 ", bare.replace('"', ""))
    return " ".join(spaced.split())


def _created_name(statement):
    """The object one `CREATE` statement makes, or `None`.

    The 3 -> 4 step only creates, which is what lets the schema-3 expectation
    be a subtraction. A step that ALTERED an existing table would make that
    subtraction wrong, so an unrecognised leading verb is refused here rather
    than silently contributing nothing.
    """
    words = statement.split()
    if not words:
        return None
    if words[0].upper() != "CREATE":
        raise ContractRefusal(
            "integrity", "schema",
            f"the 3 -> 4 migration performs {name_value(words[0])}; this "
            f"build derives schema 3 by subtracting what that step CREATES, "
            f"and a step that changes an existing object cannot be subtracted")
    rest = [word for word in words[1:]
            if word.upper() not in ("TABLE", "INDEX", "UNIQUE", "VIEW",
                                    "TRIGGER", "IF", "NOT", "EXISTS")]
    return rest[0].split("(")[0] if rest else None


def _statements(script):
    """Split a DDL script into complete statements, using SQLite's own parser.

    Splitting on semicolons would be a second SQL parser in this file, and a
    worse one.
    """
    statements = []
    pending = ""
    for line in script.split("\n"):
        pending += line + "\n"
        if sqlite3.complete_statement(pending):
            statements.append(pending.strip())
            pending = ""
    if pending.strip():
        statements.append(pending.strip())
    return statements


def job_signature(kind, operands):
    """The stable text one scheduler act's operands are compared as.

    The kind is proved here as well as at the store, because a helper that can
    build an identity the store must refuse is a helper that invites the
    caller to discover the rule by hitting it.
    """
    boundaries.text(kind, "an operation kind")
    # §13 AT THE CONSTRUCTOR rather than at the eventual write: a signature is
    # protocol identity, and a caller that received one containing a live
    # bearer already holds the leak by the time a journal walk could refuse
    # the row.
    check_no_durable_secret({"kind": kind, "operands": operands},
                            what="a job operation signature")
    return canonical_text({"kind": kind, "operands": operands})


def _recorded(value):
    """The exact text to journal for a committed result.

    Sorted keys and no insignificant whitespace: the row is compared and
    replayed, so two spellings of one document would be two answers.
    """
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      allow_nan=False)


class JobStore:
    """One Job manager's handle on one Job store."""

    def __init__(self, connection, *, authority_uuid, incarnation, clock):
        self._connection = connection
        self.authority_uuid = authority_uuid
        self.incarnation = incarnation
        self._clock = clock

    # -- opening -------------------------------------------------------------

    @classmethod
    def open(cls, path, *, authority_uuid, incarnation, clock):
        """Open a Job store this build owns, or refuse without changing it.

        Every failure closes the handle. A refused open that leaked one would
        hold a lock on a store this build has just said it must not touch.

        W83781: THE AUTHORITY UUID IS REQUIRED AND IS PROVED FIRST, before the
        path is opened at all. It is the namespace every new episode identity
        is derived from, so a store opened without one would derive identities
        that are unique only within itself -- which is the collision this Work
        exists to remove, arriving one layer earlier.

        THE RULE IS THE AUTHORITY PACKAGE'S OWN, imported rather than restated.
        `check_authority_uuid` is a PREDICATE and not a capability: it opens
        nothing, reads nothing and grants nothing, and a second looser spelling
        of "32 lowercase hex" living here is exactly the drift the finding
        forbids. What this leaf still does not have is any Authority session,
        store or mutation surface, which is the separation that matters.
        """
        check_authority(authority_uuid,
                        what="the Job store's Authority binding")
        if type(path) is not str or path == "":
            raise ContractRefusal(
                "integrity", "path",
                f"the Job store needs an explicit path; there is no ambient "
                f"default, and one pointing into the checkout is exactly what "
                f"the external state root exists to prevent. This is "
                f"{name_value(path)}")
        if type(incarnation) is not str or incarnation == "":
            raise ContractRefusal(
                "integrity", "schema",
                f"a Job manager instance names its incarnation; this is "
                f"{name_value(incarnation)}")
        boundaries.capability(clock, "the Job manager's instant source")
        connection = sqlite3.connect(path, isolation_level=None,
                                     timeout=_BUSY_TIMEOUT_MS / 1000)
        try:
            connection.execute(f"PRAGMA busy_timeout = {_BUSY_TIMEOUT_MS}")
            connection.row_factory = sqlite3.Row
            if cls._objects(connection):
                cls._adopt(connection, path, authority_uuid)
            else:
                cls._initialize(connection, authority_uuid)
            cls._request_wal(connection)
            store = cls(connection, authority_uuid=authority_uuid,
                        incarnation=incarnation, clock=clock)
            # Proved after the store exists and INSIDE this handler, so a
            # clock that cannot stamp a row is found at open rather than at
            # the first journalled act -- and the connection is still closed.
            store._now()
        except BaseException:
            try:
                connection.close()
            except BaseException:
                pass
            raise
        return store

    @staticmethod
    def _objects(connection):
        return [row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'")]

    @classmethod
    def _adopt(cls, connection, path, authority_uuid):
        """Decide a NON-EMPTY database: ours, or refused untouched.

        The mere NAME `meta` is not permission to read `key, value` out of it:
        a foreign database that happens to reuse a generic table name is still
        a foreign database, so the probe runs inside the taxonomy rather than
        in front of it.
        """
        if "meta" not in cls._objects(connection):
            raise ContractRefusal(
                "integrity", "schema",
                f"the database at {name_value(path)} holds objects and none is "
                f"this Job manager's metadata, so it is not a Job store this "
                f"build owns. Nothing was changed")
        try:
            recorded = {boundaries.text(row["key"], "a persisted meta key"):
                        boundaries.text(row["value"], "a persisted meta value")
                        for row in connection.execute(
                            "SELECT key, value FROM meta")}
        except sqlite3.Error as failure:
            raise ContractRefusal(
                "integrity", "schema",
                f"the database at {name_value(path)} carries a meta table this "
                f"Job manager cannot read "
                f"({name_value(type(failure).__name__)}), so it is not a Job "
                f"store this build owns. Nothing was changed") from None
        version = cls._validate(recorded, path)
        # Schema 3 introduced the immutable Authority binding.  A schema-3
        # store that has lost or changed it is malformed evidence and must be
        # refused before the scheduler's 3 -> 4 migration changes anything.
        if version >= 3:
            cls._bound(connection, path, authority_uuid)
        cls._migrate(connection, version, path, authority_uuid)
        cls._bound(connection, path, authority_uuid)
        connection.execute("PRAGMA foreign_keys = ON")

    @classmethod
    def _exactly_schema_three(cls, connection, path):
        """Refuse a store whose objects are not the whole of schema 3.

        DERIVED, NOT LISTED. The expected shape is this build's own v4 schema
        minus exactly what the 3 -> 4 step creates, both read from
        `schema.py`. A second hand-written list of schema-3 objects would be a
        copy to drift from, and drift is the whole class of defect this check
        exists for.

        COMPARED BY THE WHOLE DEFINITION, which is a correction. The first
        version of this check compared columns, foreign keys and index column
        lists through pragmas, and W71877's second correction review showed
        what that misses: an index recreated with the same name, uniqueness
        and columns but the OPPOSITE partial predicate --
        `WHERE ended_state IS NOT NULL` in place of `IS NULL` -- migrated
        cleanly, and that predicate is the whole of what
        `episodes_one_live_per_stage` enforces. Table `CHECK` constraints were
        outside it for the same reason. Neither is expressible in a pragma, and
        both are in `sqlite_schema.sql`, so the definition is what is compared.

        TWO SPELLINGS OF ONE SCHEMA ARE STILL BOTH LEGITIMATE, and that is
        what `_definition` exists for rather than a weaker comparison.
        `MIGRATIONS[1]` builds `stages` and `receipts` as `stages_2` and
        `receipts_2` and renames them, and SQLite rewrites the stored header as
        `CREATE TABLE "stages"` -- quoted, where an install writes it bare.
        The bodies are identical. So identifier quoting and whitespace are
        normalised away and everything else -- every column, every constraint,
        every predicate -- must match exactly.
        """
        expected = cls._schema_three_shape()
        found = cls._schema_shape(connection)
        missing = sorted(set(expected) - set(found))
        added = sorted(set(found) - set(expected))
        changed = sorted(name for name in set(expected) & set(found)
                         if expected[name] != found[name])
        if missing or added or changed:
            raise ContractRefusal(
                "integrity", "schema",
                f"the Job store at {name_value(path)} says it is schema 3 and "
                f"its objects are not schema 3's"
                + (f"; missing {', '.join(missing)}" if missing else "")
                + (f"; unexpected {', '.join(added)}" if added else "")
                + (f"; changed {', '.join(changed)}" if changed else "")
                + ". Nothing was changed")

    @classmethod
    def _schema_three_shape(cls):
        """This build's v4 shape, less the objects 3 -> 4 creates.

        Built in a THROWAWAY IN-MEMORY DATABASE rather than parsed out of the
        DDL text: what a store must match is what SQLite makes of these
        statements, and the only reader that agrees with SQLite is SQLite.
        """
        beside = sqlite3.connect(":memory:")
        try:
            beside.row_factory = sqlite3.Row
            for statement in _statements(SCHEMA):
                beside.execute(statement)
            whole = cls._schema_shape(beside)
        finally:
            beside.close()
        added = set()
        for statement in _statements(MIGRATIONS[3]):
            name = _created_name(statement)
            if name is not None:
                added.add(name)
        return {name: shape for name, shape in whole.items()
                if name not in added}

    @staticmethod
    def _schema_shape(connection):
        """One database's objects, each as its whole normalised definition.

        The type travels with it so a table replaced by a view of the same
        name is a difference rather than a coincidence.
        """
        return {row["name"]: (row["type"], _definition(row["sql"]))
                for row in connection.execute(
                    "SELECT name, type, sql FROM sqlite_master "
                    "WHERE name NOT LIKE 'sqlite_%'")}

    @staticmethod
    def _bound(connection, path, authority_uuid):
        """Prove the store's recorded Authority is the one this open names.

        W83781. A Job store belongs to ONE Authority for its whole life: its
        episode identities are derived in that Authority's namespace, and the
        containers those identities name carry it as an immutable label. So an
        open under a different UUID is not a store this caller may use -- it is
        somebody else's pipeline, and adopting it would derive future episodes
        in a namespace the existing rows were never in.

        THE REFUSAL CHANGES NOTHING. The migration above has already committed
        or rolled back on its own, so a wrong UUID leaves the database exactly
        as it was found -- which is what makes "refused untouched" a fact a
        reader can rely on rather than a hope.
        """
        row = connection.execute("SELECT value FROM meta WHERE key = ?",
                                 (_META_AUTHORITY_UUID,)).fetchone()
        recorded = None if row is None else boundaries.text(
            row["value"], "a persisted Authority binding")
        # W83781 review [P1]: THE PERSISTED VALUE IS OWNED AS AN AUTHORITY
        # BEFORE IT IS COMPARED AS ONE. `boundaries.text` says it is storable
        # text; it does not say it is an Authority. Without this a corrupt
        # schema-3 row reads as a valid store belonging to somebody else --
        # `refused/precondition`, which sends an operator to look for the
        # other Authority -- when what it actually is, is this store's own
        # evidence being malformed.
        if recorded is not None:
            check_authority(
                recorded,
                what=f"the Authority binding recorded at {name_value(path)}")
        if recorded is None:
            raise ContractRefusal(
                "integrity", "schema",
                f"the Job store at {name_value(path)} records no Authority "
                f"binding; this build stamps one when it creates or migrates a "
                f"store, so a store without one is state this build cannot "
                f"account for. Nothing was changed")
        if recorded != authority_uuid:
            raise ContractRefusal(
                "refused", "precondition",
                f"the Job store at {name_value(path)} belongs to Authority "
                f"{name_value(recorded)} and this open names "
                f"{name_value(authority_uuid)}; a store's episode identities "
                f"are derived in its Authority's namespace, so opening it "
                f"under another one would derive future episodes in a "
                f"namespace its existing rows were never in. Nothing was "
                f"changed")

    @classmethod
    def _recorded_version(cls, connection, path):
        """The schema version this store is at RIGHT NOW, owned on the way in.

        W83781 review [P0]. The version `_adopt` read is a fact about a moment
        before any lock was held; this is the one a migration may act on.
        """
        row = connection.execute("SELECT value FROM meta WHERE key = ?",
                                 (_META_SCHEMA_VERSION,)).fetchone()
        recorded = None if row is None else boundaries.text(
            row["value"], "a persisted meta value")
        if recorded == str(SCHEMA_VERSION):
            return SCHEMA_VERSION
        for known in sorted(MIGRATIONS):
            if recorded == str(known):
                return known
        raise ContractRefusal(
            "integrity", "schema",
            f"the Job store at {name_value(path)} is schema "
            f"{name_value(recorded)} under the migration lock; this build is "
            f"{SCHEMA_VERSION} and carries no migration from that version. "
            f"Nothing was changed")

    @staticmethod
    def _path_of(connection):
        for row in connection.execute("PRAGMA database_list"):
            if row[1] == "main":
                return row[2]
        return ""

    @staticmethod
    def _request_wal(connection):
        """Ask an owned and Authority-bound store for WAL.

        WAL is a concurrency optimization rather than schema or identity.
        SQLite may answer BUSY or LOCKED immediately when another connection
        holds access needed to change journal mode; the valid store then opens
        in its retained mode, and every later open asks again. Other storage
        failures keep their exact exception identity.
        """
        try:
            connection.execute("PRAGMA journal_mode = WAL")
        except sqlite3.Error as failure:
            if not _is_contention(failure):
                raise

    @classmethod
    def _initialize(cls, connection, authority_uuid):
        """Create the schema, or ADOPT the store another opener just created.

        Emptiness observed before the write lock answers the common case; the
        re-read inside the lock is what decides. Several manager processes may
        legitimately start against one fresh path, and resuming into the same
        `CREATE TABLE` is what that race looks like without this.
        """
        connection.execute("BEGIN IMMEDIATE")
        try:
            if cls._objects(connection):
                connection.execute("ROLLBACK")
                cls._adopt(connection, cls._path_of(connection),
                           authority_uuid)
                return
            # NOT `executescript`: it issues a COMMIT before it runs, which
            # would end the transaction this DDL has to be atomic inside.
            for statement in _statements(SCHEMA):
                connection.execute(statement)
            connection.execute(
                "INSERT INTO meta (key, value) VALUES (?, ?)",
                (_META_STORE_KIND, STORE_KIND))
            connection.execute(
                "INSERT INTO meta (key, value) VALUES (?, ?)",
                (_META_SCHEMA_VERSION, str(SCHEMA_VERSION)))
            # W83781: THE BINDING IS WRITTEN IN THE SAME TRANSACTION as the
            # kind and the version. A store that existed for even one instant
            # without knowing its Authority is a store something could open
            # and derive an identity from first.
            connection.execute(
                "INSERT INTO meta (key, value) VALUES (?, ?)",
                (_META_AUTHORITY_UUID, authority_uuid))
            connection.execute("COMMIT")
        except BaseException:
            try:
                connection.execute("ROLLBACK")
            except BaseException:
                pass
            raise
        connection.execute("PRAGMA foreign_keys = ON")

    @staticmethod
    def _validate(recorded, path):
        """Prove the store is this product's, and answer the version it is at.

        KIND BEFORE VERSION: version 1 is true of several stores beside this
        one, so telling a caller their store is the wrong VERSION when it is
        the wrong PRODUCT sends them to fix the wrong thing.
        """
        kind = recorded.get(_META_STORE_KIND)
        if kind != STORE_KIND:
            raise ContractRefusal(
                "integrity", "schema",
                f"the database at {name_value(path)} is {name_value(kind)}, "
                f"not a {STORE_KIND} store; this Job manager opens its own "
                f"stores and adopts nothing. Nothing was changed")
        version = recorded.get(_META_SCHEMA_VERSION)
        # A VERSION THIS BUILD HAS NO PATH FROM is still refused untouched.
        # Migrating forward is not the same as guessing across versions: the
        # step from each older shape to the next is written down in
        # `MIGRATIONS`, and a version with no entry -- an unknown spelling, or
        # a store written by a LATER build -- has no such statement and is not
        # improvised one.
        if version == str(SCHEMA_VERSION):
            return SCHEMA_VERSION
        for known in sorted(MIGRATIONS):
            if version == str(known):
                return known
        raise ContractRefusal(
            "integrity", "schema",
            f"the Job store at {name_value(path)} is schema "
            f"{name_value(version)}; this build is {SCHEMA_VERSION}, carries "
            f"no migration from that version, and does not guess across "
            f"versions. Nothing was changed")

    @classmethod
    def _migrate(cls, connection, version, path, authority_uuid):
        """Carry an older store forward, WHOLE, in one transaction.

        A persisted submission is a pipeline somebody is running. Refusing it
        because the next slice added a relation would be this build deciding
        an operator's durable work is disposable, so each recorded step runs
        in order and the version is stamped in the SAME transaction that
        performed it. A step that fails rolls the whole thing back and leaves
        a store at exactly the version it was opened at -- there is no half-
        migrated shape for the next open to have to recognise.

        `foreign_keys` stays OFF for the duration and is turned on by the
        caller afterwards. The steps rebuild tables that others reference, and
        SQLite would otherwise decide a mid-migration moment is a violation of
        a constraint the finished shape satisfies.
        """
        if version == SCHEMA_VERSION:
            return
        connection.execute("BEGIN IMMEDIATE")
        try:
            # W83781 review 2026-09-04T09-07-42Z [P0]: THE VERSION IS RE-READ
            # UNDER THE LOCK, because the one this was called with is a
            # pre-lock observation.
            #
            # `_adopt` reads the version before this function asks for a write
            # lock, so two openers can both see schema 2. The first migrates
            # and records its Authority; the second then acquires the lock
            # still believing the store is at 2, runs the step again, and
            # rebinds. The winner's episodes stay in the winner's namespace
            # while every future episode is derived in the loser's -- the
            # cross-authority split this binding exists to prevent, produced
            # by the binding's own migration.
            #
            # WHAT THE LOCK IS FOR is deciding from state nobody else can be
            # changing. Everything below now derives from this read.
            at = cls._recorded_version(connection, path)
            if at == SCHEMA_VERSION:
                # SOMEBODY ELSE FINISHED IT. There is nothing to migrate and
                # nothing to write: the binding is already whatever the winner
                # recorded, and `_bound` is what decides whether this opener
                # may use it. A waiter that wrote here would be replacing an
                # immutable value it did not establish.
                connection.execute("COMMIT")
                return
            while at != SCHEMA_VERSION:
                if at == 3:
                    # W71877 review [P1]: THE WHOLE PRIOR SHAPE IS PROVED
                    # BEFORE THE STEP THAT DEPENDS ON IT, under this same lock.
                    #
                    # The finished-shape check below asks only that the v4
                    # TABLE NAMES exist afterwards. That says nothing about the
                    # store this migration started from -- the reviewer stamped
                    # a store as schema 3 with `episodes_one_live_per_stage`
                    # removed and it opened as schema 4 with the missing index
                    # still missing. A version stamp is a claim; the objects
                    # are the evidence.
                    cls._exactly_schema_three(connection, path)
                for statement in _statements(MIGRATIONS[at]):
                    connection.execute(statement)
                at += 1
                connection.execute(
                    "UPDATE meta SET value = ? WHERE key = ?",
                    (str(at), _META_SCHEMA_VERSION))
                if at == 3:
                    # W83781: THE BINDING IS STAMPED WITH THE VERSION THAT
                    # REQUIRES IT, inside this same transaction. A failure
                    # anywhere below rolls the UUID and the version stamp back
                    # together, so there is no half-migrated store carrying one
                    # without the other for the next open to have to recognise.
                    #
                    # AND NO EXISTING EPISODE IS TOUCHED. The namespace changes
                    # what a NEW episode is called; every offer and attempt
                    # already recorded stays exactly as it is, because Worker
                    # Manager journal keys and Job receipts already reference
                    # those strings and renaming one would orphan them.
                    #
                    # A PLAIN `INSERT`, NOT `INSERT OR REPLACE`. Review [P0]:
                    # replacement semantics are wrong for a value that is
                    # immutable once written -- the whole point of the binding
                    # is that nothing rebinds it. If a row is somehow already
                    # there the primary key refuses and this transaction rolls
                    # back, which is the correct answer to "somebody else got
                    # here first" and is the answer the re-read above already
                    # gives on every ordinary path.
                    connection.execute(
                        "INSERT INTO meta (key, value) VALUES (?, ?)",
                        (_META_AUTHORITY_UUID, authority_uuid))
            # THE FINISHED SHAPE IS PROVED BEFORE THE COMMIT, not assumed from
            # having run the statements. A migration that produced a store
            # this build cannot own is a migration whose next act would be
            # refused anyway, and refusing it here leaves the old store intact.
            objects = set(cls._objects(connection))
            missing = [table for table in schema.TABLES
                       if table not in objects]
            if missing:
                raise ContractRefusal(
                    "integrity", "schema",
                    f"migrating the Job store at {name_value(path)} to schema "
                    f"{SCHEMA_VERSION} left it without "
                    f"{', '.join(missing)}; nothing was changed")
            connection.execute("COMMIT")
        except BaseException:
            try:
                connection.execute("ROLLBACK")
            except BaseException:
                pass
            raise

    def close(self):
        self._connection.close()

    def __enter__(self):
        return self

    def __exit__(self, kind, value, traceback):
        self.close()
        return False

    # -- the injected instant ------------------------------------------------

    def _now(self):
        """This manager's clock, proved rather than trusted.

        Exposed through the store so an act built on it stamps its rows from
        the SAME instant source the journal does.
        """
        return boundaries.instant(self._clock(),
                                  "the configured clock's answer")

    # -- the atomic boundary -------------------------------------------------

    def transact(self, operation_id, kind, signature, action):
        """One atomic scheduler act, journalled by its operation identity.

        The collision check is made inside the transaction, because two
        managers can reach it concurrently and a read-then-write check outside
        would let both through.
        """
        boundaries.identity(operation_id, "an operation identity")
        boundaries.capability(action, "the journalled action")
        self._agreeing(kind, signature)
        found, value = self.replay(operation_id, signature, kind=kind)
        if found:
            return value
        connection = self._connection
        connection.execute("BEGIN IMMEDIATE")
        try:
            # RE-READ INSIDE THE LOCK. The peek above answers the sequential
            # case without taking a write lock; this is the one that decides.
            found, value = self.replay(operation_id, signature, kind=kind)
            if found:
                connection.execute("ROLLBACK")
                return value
            connection.execute("SAVEPOINT act")
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
                # Anything that is not a refusal is a FAULT: an operation
                # whose failure we cannot describe is not one we may record an
                # outcome for.
                connection.execute("ROLLBACK TO act")
                connection.execute("ROLLBACK")
                raise
            connection.execute("RELEASE act")
            committed = own(result, what="an operation result")
            self._record(operation_id, kind, signature, "committed",
                         _recorded(committed), None)
            connection.execute("COMMIT")
            # The COMMITTED answer, not the action's object: an exact retry
            # replays these same bytes, so the first caller and every later
            # one are told the same thing.
            return committed
        except BaseException:
            try:
                connection.execute("ROLLBACK")
            except BaseException:
                pass
            raise

    @classmethod
    def _agreeing(cls, kind, signature):
        """The signature must be one THIS BUILD COULD HAVE PRODUCED.

        The journal stores the kind and `job_signature` puts the kind inside
        the signature: two caller-controlled accounts of one fact, so they are
        compared. And agreeing is not the same as BEING one -- an indented
        spelling or an extra member is a durable identity this build cannot
        produce, which would let equivalent acts acquire different identities
        and let data outside the operand set enter replay identity.
        """
        boundaries.text(kind, "an operation kind")
        boundaries.text(signature, "an operation signature")
        try:
            parsed = json.loads(signature)
        except ValueError:
            raise ContractRefusal(
                "integrity", "schema",
                "an operation signature is the canonical text this Job "
                "manager builds from a kind and its operands") from None
        document = own(parsed, what="an operation signature")
        if type(document) is not dict \
                or tuple(sorted(document)) != _SIGNATURE_MEMBERS:
            raise ContractRefusal(
                "integrity", "schema",
                f"an operation signature carries exactly "
                f"{', '.join(_SIGNATURE_MEMBERS)}; this carries "
                f"{sample_of(sorted(document)) if type(document) is dict else name_value(parsed)}")
        if document["kind"] != kind:
            raise ContractRefusal(
                "refused", "operation-collision",
                f"the operation is submitted as {name_value(kind)} and its "
                f"signature names {name_value(document['kind'])}; one "
                f"operation has one kind, and a row recording two accounts of "
                f"it could be replayed as either")
        if signature != job_signature(document["kind"], document["operands"]):
            raise ContractRefusal(
                "integrity", "schema",
                "an operation signature is the exact canonical text this Job "
                "manager produces; a different spelling of the same document "
                "is a different durable identity")

    def replay(self, operation_id, signature, *, kind=None):
        """`(found, value)` for one operation identity.

        PRESENCE IS ITS OWN FACT: `None` also means "the committed result was
        JSON null", and effectively-once cannot be built on a value that also
        means absence.
        """
        boundaries.identity(operation_id, "an operation identity")
        row = self._operation_row(operation_id)
        if row is None:
            return (False, None)
        if row["signature"] != signature or (kind is not None
                                             and row["kind"] != kind):
            raise ContractRefusal(
                "refused", "operation-collision",
                f"operation {name_value(operation_id)} is already recorded "
                f"with a different kind or signature; reusing an id with "
                f"different operands changes nothing")
        if row["state"] == "refused":
            # The FIRST answer, reproduced. Rebuilding it as
            # `refused.precondition` would give the retry a different portable
            # meaning and a different retry policy.
            #
            # THE PUBLIC HELPER, and the second adoption it performs is
            # deliberate rather than overlooked. The manager splits this path
            # because ITS replay can carry a refusal that legitimately quotes
            # a since-forgotten bearer, and re-walking those bytes would make
            # an exact durable replay fail on the retry. No act journalled by
            # THIS store holds a secret live -- the bearer is minted, handed
            # to the deployment's delivery capability and dropped inside one
            # delegated call -- so the second walk here has nothing it could
            # wrongly refuse, and one shared implementation beats a private
            # copy that only differs in what it is allowed to see.
            raise revive_refusal(row["refusal"])
        if row["result"] is None:
            return (True, None)
        return (True, json.loads(row["result"]))

    def _record(self, operation_id, kind, signature, state, result, refusal):
        # §13: the journal is a durable surface and it is the one every
        # mutating act passes through. The WHOLE row, because the identity and
        # the kind are written by this build and the operands are not.
        check_no_durable_secret(
            {"operation_id": operation_id, "kind": kind,
             "signature": signature, "state": state, "result": result,
             "refusal": refusal},
            what="a journalled job operation")
        self._connection.execute(
            "INSERT INTO operations (operation_id, kind, signature, state, "
            "result, refusal, settled_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (operation_id, kind, signature, state, result, refusal,
             self._now()))

    def operation_record(self, operation_id):
        """The journal row as a FRESH document, or absence."""
        boundaries.identity(operation_id, "an operation identity")
        return self._operation_row(operation_id)

    def _operation_row(self, operation_id):
        """THE ONE CROSSING out of the journal table."""
        record = self._connection.execute(
            "SELECT * FROM operations WHERE operation_id = ?",
            (operation_id,)).fetchone()
        if record is None:
            return None
        return boundaries.row(record, "a persisted job operation",
                              schema.OPERATION_COLUMNS)
