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
import sqlite3

from ..contracts import (ContractRefusal, canonical_text,
                         check_no_durable_secret, own)
from ..contracts.errors import name_value, sample_of
from ..worker_manager import boundaries
from ..worker_manager.store import revive_refusal, seal_refusal
from . import schema
from .schema import SCHEMA, SCHEMA_VERSION, STORE_KIND

__all__ = ["JobStore", "job_signature"]

_BUSY_TIMEOUT_MS = 5000
_META_STORE_KIND = "store_kind"
_META_SCHEMA_VERSION = "schema_version"

_SIGNATURE_MEMBERS = ("kind", "operands")


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

    def __init__(self, connection, *, incarnation, clock):
        self._connection = connection
        self.incarnation = incarnation
        self._clock = clock

    # -- opening -------------------------------------------------------------

    @classmethod
    def open(cls, path, *, incarnation, clock):
        """Open a Job store this build owns, or refuse without changing it.

        Every failure closes the handle. A refused open that leaked one would
        hold a lock on a store this build has just said it must not touch.
        """
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
                cls._adopt(connection, path)
            else:
                cls._initialize(connection)
            store = cls(connection, incarnation=incarnation, clock=clock)
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
    def _adopt(cls, connection, path):
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
        cls._validate(recorded, path)
        connection.execute("PRAGMA foreign_keys = ON")

    @staticmethod
    def _path_of(connection):
        for row in connection.execute("PRAGMA database_list"):
            if row[1] == "main":
                return row[2]
        return ""

    @classmethod
    def _initialize(cls, connection):
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
                cls._adopt(connection, cls._path_of(connection))
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
            connection.execute("COMMIT")
        except BaseException:
            try:
                connection.execute("ROLLBACK")
            except BaseException:
                pass
            raise
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA foreign_keys = ON")

    @staticmethod
    def _validate(recorded, path):
        kind = recorded.get(_META_STORE_KIND)
        # KIND BEFORE VERSION: version 1 is true of several stores beside this
        # one, so telling a caller their store is the wrong VERSION when it is
        # the wrong PRODUCT sends them to fix the wrong thing.
        if kind != STORE_KIND:
            raise ContractRefusal(
                "integrity", "schema",
                f"the database at {name_value(path)} is {name_value(kind)}, "
                f"not a {STORE_KIND} store; this Job manager opens its own "
                f"stores and adopts nothing. Nothing was changed")
        version = recorded.get(_META_SCHEMA_VERSION)
        if version != str(SCHEMA_VERSION):
            raise ContractRefusal(
                "integrity", "schema",
                f"the Job store at {name_value(path)} is schema "
                f"{name_value(version)}; this build is {SCHEMA_VERSION} and "
                f"does not guess across versions. Nothing was changed")

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
