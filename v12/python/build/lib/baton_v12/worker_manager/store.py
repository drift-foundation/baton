"""The manager control store: one transaction boundary and one journal.

W4 cut B (PLAN item 4bc). `transact` is the atomic boundary and `replay` is what
makes a repeated request return the FIRST outcome instead of performing it twice.
They are one mechanism: journalling outside the transaction that did the work
would let a crash leave a mutation with no operation record, and the next retry
would do it again.

TWO KINDS OF REFUSAL, AND THEY NEED OPPOSITE STORAGE. An ORDINARY refusal wrote
nothing and stays retryable, so its partial writes must vanish. A DURABLE refusal
is itself a committed outcome, so its writes and the refusal record must survive
and the retry must REPLAY the refusal rather than re-decide it. The action
therefore runs inside a savepoint.

OWNERSHIP, NOT PRESENCE. The frozen host was corrected for asking only whether
`meta` existed and treating its absence as proof the file was new: absence of
this manager's metadata is not evidence that a database belongs to it -- it is
equally the signature of somebody else's store. A pre-existing file holding
`foreign_state` was adopted and came back carrying both that table and every
manager table. So a GENUINELY EMPTY schema is initialized; anything else must
carry this manager's own marker or be refused WITHOUT A BYTE CHANGED.

WHY THIS IS NOT THE AUTHORITY'S CREATE/OPEN SPLIT, said rather than left for a
reviewer to wonder about. The authority separates `create` from `open` and
reserves its path with `O_CREAT|O_EXCL`, because it is the deployment's root of
identity and adopting anything at all would be wrong. The manager's reviewed
obligation is different and weaker on purpose: a manager may be started against
a path that does not exist yet, and the frozen host's correction is the
empty-or-ours rule above. Both refuse to adopt somebody else's database; they
differ in whether an absent path is an error. Carrying the manager's own
reviewed semantics is the port; substituting the authority's would be a redesign
this cut has no ruling for.
"""

import json
import sqlite3

from ..contracts import (ContractRefusal, canonical_text,
                         check_no_durable_secret, own)
from ..contracts.errors import name_value
from ..contracts.errors import sample_of
from . import boundaries, schema
from .schema import SCHEMA, SCHEMA_VERSION, STORE_KIND

__all__ = ["ControlStore", "manager_signature", "seal_refusal",
           "revive_refusal"]

_BUSY_TIMEOUT_MS = 5000

# Concurrent managers WAIT for the write lock rather than failing with
# SQLITE_BUSY. A rule that must be decided by a refusal INSIDE a transaction
# cannot be decided by not getting a transaction at all, and the two outcomes are
# not interchangeable.
_META_STORE_KIND = "store_kind"
_META_SCHEMA_VERSION = "schema_version"


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


def manager_signature(kind, operands):
    """The stable text an operation's operands are compared as.

    The manager's own signature, deliberately not the authority's
    `claim_signature`: that one is the authority's fact about whether two claims
    are the same claim, and this one is the manager's fact about whether two
    requests are the same request. Reusing the authority's would make the manager
    a second opinion on a question it does not own.

    The kind is proved HERE as well as at the store, because a helper that can
    build an identity the store must refuse is a helper that invites the caller
    to discover the rule by hitting it.
    """
    boundaries.text(kind, "an operation kind")
    # §13 AT THE CONSTRUCTOR, not at the eventual write. Review [P1]: this
    # returned protocol identity containing a live bearer verbatim, and the
    # journal walk refused the ROW afterwards -- by which point the caller
    # already held the leak. "Secret bytes stay outside protocol identity"
    # cannot be established by a guard that runs after the identity has been
    # handed out.
    #
    # THE OPERANDS RATHER THAN THE COMPOSED TEXT, because the walk's named
    # half is about MEMBERS: a `claim_token` operand is refused by its name
    # here and would be an ordinary substring once serialized. The value half
    # answers the same either way.
    check_no_durable_secret({"kind": kind, "operands": operands},
                            what="an operation signature")
    return canonical_text({"kind": kind, "operands": operands})


def _recorded(value):
    """The exact text to journal for a committed result.

    Sorted keys, no insignificant whitespace: the row is compared and replayed,
    so two spellings of one document would be two answers. The value has already
    been through `own`, so this serializes exact built-ins and runs nothing.
    """
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      allow_nan=False)


def seal_refusal(refusal):
    """The WHOLE outcome, so a retry reproduces the first answer.

    The frozen host kept only the message, so replay fabricated
    `refused.precondition` for every durable refusal -- and a `policy.retention`
    and a `refused.precondition` are different answers with different retry
    policies. The closed pair IS the portable meaning.
    """
    # THE OPERAND ITSELF, BEFORE ANY MEMBER IS READ. Review [P1]: removing the
    # unreachable message sub-boundary did not establish the ENCLOSING input --
    # this reached straight for `.category`, `.code`, `.message` and `.durable`,
    # so an object with a hostile `__getattribute__` ran caller behaviour and
    # escaped as a raw AssertionError before the manager could refuse anything.
    # `type(...) is` rather than `isinstance`, for the reason the POD rules
    # give: a subclass can override attribute access, and this boundary is
    # exactly about not running what it is handed.
    if type(refusal) is not ContractRefusal:
        raise ContractRefusal(
            "integrity", "schema",
            f"a sealed outcome is this build's own refusal; this is "
            f"{name_value(refusal)}")
    # THE MESSAGE HAD ITS OWN OWNER HERE AND NO LONGER NEEDS ONE. W7079 made
    # `ContractRefusal` own its message AT CONSTRUCTION -- an unencodable one
    # cannot be built at all -- so this owner became unreachable: no refusal
    # that exists can fail it. This campaign removes a boundary it can no
    # longer reach rather than documenting one, and the ninth is this.
    #
    # The COMPOSED seal is still owned below, because that text is this
    # build's own value on its way into SQLite and the categories, codes and
    # separators around the message are not the message.
    # §13 AT THE SEALING SURFACE. Review [P1]: an interpolated live bearer
    # left this boundary in `message` and was refused only when a later
    # journal write happened -- so a direct caller received the portable leak.
    # Sealing is the point a diagnostic BECOMES a portable document, which is
    # exactly the bounded-diagnostic surface §13 names.
    #
    # The whole document, before it is composed into text, for the same reason
    # the signature walks its operands.
    sealed = {"category": refusal.category, "code": refusal.code,
              "message": refusal.message, "durable": True}
    check_no_durable_secret(sealed, what="a sealed refusal")
    return boundaries.text(
        json.dumps(sealed, sort_keys=True, ensure_ascii=False),
        "a sealed refusal")


def revive_refusal(sealed):
    """PUBLIC: rebuild a sealed outcome from text this build has NOT owned.

    Review [P1]: a persisted refusal of `{}` escaped as a raw `KeyError`. The
    seal is adopted persistent data and the whole closed pair is what makes a
    replay a replay, so the document is owned with exactly the members it needs
    before anything reads one.
    """
    # THE SAME SEMANTIC OWNER the adopted half uses. Review [P1]: this checked
    # the four member NAMES and handed their contents straight on, so a list
    # category escaped as TypeError, a cross-category pair as AssertionError, an
    # integer message was accepted into a refusal, and a `false` durable marker
    # was silently rewritten to true. The public door and the replay door lead
    # to one document; fitting a lock to one of them is not locking it.
    record = boundaries.sealed(
        boundaries.adopted(sealed, "a sealed refusal"), "a sealed refusal")
    # §13 AT THE PUBLIC DOOR, in the other direction. Re-review [P1]: the
    # inventory called this prose-only on the reasoning that the bytes were
    # walked on the way in -- true of the internal replay path, whose input is
    # a journal row this build wrote, and NOT of this function, whose input is
    # whatever text a caller holds. A caller supplying an interpolated live
    # bearer in `message` received the diagnostic object back, which is the
    # same portable surface `seal_refusal` guards travelling the other way.
    #
    # The SEALED DOCUMENT rather than the composed refusal, for the reason
    # `manager_signature` walks operands: the named half of the walk is about
    # MEMBERS, and a member named for a secret is an ordinary substring once
    # it has been folded into a message.
    check_no_durable_secret(record, what="a revived refusal")
    return _revived(record)


def _revived(record):
    """The constructor, over a sealed document somebody has ALREADY owned.

    Review [P1]: replay took its refusal from a journal row whose column
    contract had already proved the text, the decode AND the member set -- and
    then called the public `revive_refusal`, which adopted the same bytes again.
    One crossing, two adoptions, and the second was reachable: patching it made
    an exact durable replay fail.

    PLAN 4bz says a value is owned as it enters the receiving domain and not
    revalidated afterwards, so the two paths are split rather than one of the
    checks removed. A caller holding raw sealed text still gets the public
    boundary above; the replay path, which is holding an owned document, gets
    this.

    NO §13 WALK HERE EITHER, and for the same reason the adoption is absent:
    replay's bytes came out of a journal row `_record` walked before it wrote
    them. Walking them again would be the blanket revalidation 4bz forbids,
    and it would make an exact durable replay of a refusal that legitimately
    quotes a since-forgotten secret fail on the second attempt.
    """
    return ContractRefusal(record["category"], record["code"],
                           record["message"], durable=True)


class ControlStore:
    """One manager's handle on one control store."""

    def __init__(self, connection, *, incarnation, clock):
        self._connection = connection
        self.incarnation = incarnation
        self._clock = clock

    # -- opening -------------------------------------------------------------

    @classmethod
    def open(cls, path, *, incarnation, clock):
        """Open a control store this build owns, or refuse without changing it.

        Every failure closes the handle. A refused open that leaked one would
        hold a lock on a store this build has just said it must not touch.
        """
        if type(path) is not str or path == "":
            raise ContractRefusal(
                "integrity", "path",
                f"the control store needs an explicit path; there is no ambient "
                f"default, and one pointing into the checkout is exactly what "
                f"the external state root exists to prevent. This is "
                f"{name_value(path)}")
        if type(incarnation) is not str or incarnation == "":
            raise ContractRefusal(
                "integrity", "schema",
                f"a manager instance names its incarnation; this is "
                f"{name_value(incarnation)}")
        # The instant source is INJECTED, so a fixture that pins one pins the
        # journal too -- and a manager whose clock cannot be called cannot stamp
        # a row at all.
        boundaries.capability(clock, "the manager's instant source")
        connection = sqlite3.connect(path, isolation_level=None,
                                     timeout=_BUSY_TIMEOUT_MS / 1000)
        try:
            # The busy policy goes in force BEFORE any lock is taken, because
            # the initializing transaction is itself a lock-taker.
            connection.execute(f"PRAGMA busy_timeout = {_BUSY_TIMEOUT_MS}")
            connection.row_factory = sqlite3.Row
            if cls._objects(connection):
                # The common case: an existing store, decided without taking a
                # write lock.
                cls._adopt(connection, path)
            else:
                cls._initialize(connection)
        except BaseException:
            try:
                connection.close()
            except BaseException:
                pass
            raise
        store = cls(connection, incarnation=incarnation, clock=clock)
        # Proved AFTER the store exists, because the clock is the store's and a
        # clock that cannot stamp a row is a fault worth finding at open rather
        # than at the first journalled act.
        store._now()
        return store

    @staticmethod
    def _objects(connection):
        # NOTHING TO OWN, and saying so beats owning it. SQLite's catalogue
        # names objects with identifiers it accepted at CREATE time, so a name
        # here is storable text by construction -- and these names are read for
        # ONE membership comparison, never stored, compared to an instant or
        # decoded. I wrote a `boundaries.text` here first and could not drive
        # it: a boundary no caller can reach is the shape my own last round was
        # corrected for, so it is absent rather than decorative.
        return [row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'")]

    @classmethod
    def _adopt(cls, connection, path):
        """Decide a NON-EMPTY database: ours, or refused untouched.

        Review [P1]: the mere NAME `meta` was treated as permission to run
        `SELECT key, value FROM meta`, so a foreign database carrying
        `meta(id INTEGER)` escaped as a raw `sqlite3.OperationalError: no such
        column: key`. The empty-or-ours rule covers EVERY foreign schema,
        including one that happens to reuse a generic table name -- so the probe
        runs inside the taxonomy rather than in front of it.
        """
        if "meta" not in cls._objects(connection):
            raise ContractRefusal(
                "integrity", "schema",
                f"the database at {name_value(path)} holds objects and none is "
                f"this manager's metadata, so it is not a control store this "
                f"build owns. Nothing was changed")
        try:
            # OWNED AS IT IS READ, both halves. `_validate` compares these
            # against the store kind and schema version, and a metadata pair
            # this build cannot read is exactly the case that decides whether
            # the database is adopted or refused untouched.
            recorded = {boundaries.text(row["key"], "a persisted meta key"):
                        boundaries.text(row["value"], "a persisted meta value")
                        for row in connection.execute(
                            "SELECT key, value FROM meta")}
        except sqlite3.Error as failure:
            # A `meta` this manager cannot read is somebody else's `meta`. The
            # SQLite error is the EVIDENCE, not the outcome: a caller reading
            # our refusals must not have to know SQLite's error vocabulary to
            # find out their database is not ours.
            raise ContractRefusal(
                "integrity", "schema",
                f"the database at {name_value(path)} carries a meta table this "
                f"manager cannot read ({name_value(type(failure).__name__)}), "
                f"so it is not a control store this build owns. Nothing was "
                f"changed") from None
        cls._validate(recorded, path)
        connection.execute("PRAGMA foreign_keys = ON")

    @staticmethod
    def _path_of(connection):
        """The file SQLite actually has open.

        Asked of the connection rather than carried from the caller, so
        `_initialize` needs only the connection -- and so a refusal names the
        database that was really inspected rather than the string somebody
        passed in.
        """
        for row in connection.execute("PRAGMA database_list"):
            if row[1] == "main":
                return row[2]
        return ""

    @classmethod
    def _initialize(cls, connection):
        """Create the schema, or ADOPT the store another opener just created.

        Review [P1]: emptiness was decided before the write lock and never
        re-read inside it, so when several managers observed one fresh database
        as empty the first created the schema and every waiter resumed into the
        same `CREATE TABLE`, escaping as `table meta already exists`. The
        reviewed contract explicitly permits a manager to start at an absent
        path, and multi-process managers coordinate through this shared store --
        so concurrent first opens are the ordinary case and not an abuse.

        The lock is what decides, exactly as it is for a journalled act: the
        check outside answers the common case, and the re-read inside decides.
        """
        # ONE transaction: a crash mid-DDL leaves no half-built store for the
        # next process to mistake for a compatible one.
        connection.execute("BEGIN IMMEDIATE")
        try:
            if cls._objects(connection):
                # Somebody else won. Roll back this transaction and decide the
                # store they made by exactly the rule any other existing store
                # is decided by -- adopt it if it is ours, refuse it untouched
                # if it is not.
                connection.execute("ROLLBACK")
                cls._adopt(connection, cls._path_of(connection))
                return
            # NOT `executescript`. It issues a COMMIT before it runs, which
            # would end the transaction this DDL is supposed to be atomic
            # inside -- so a crash mid-schema could leave exactly the
            # half-built store the single transaction exists to prevent. The
            # authority slice was corrected for the same thing; the mechanism
            # is Python's, not either boundary's, so each applies it where it
            # opens a store.
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
        # WAL is a database-level property and cannot be set inside a
        # transaction. It is applied only to a store this build now OWNS, so a
        # refused open leaves even the journal mode as it was found.
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA foreign_keys = ON")

    @staticmethod
    def _validate(recorded, path):
        kind = recorded.get(_META_STORE_KIND)
        # KIND BEFORE VERSION. Version 1 is true of several stores beside this
        # one, so telling a caller their store is the wrong VERSION when it is
        # the wrong PRODUCT sends them to fix the wrong thing.
        if kind != STORE_KIND:
            raise ContractRefusal(
                "integrity", "schema",
                f"the database at {name_value(path)} is {name_value(kind)}, not "
                f"a {STORE_KIND} store; this manager opens its own stores and "
                f"adopts nothing. Nothing was changed")
        version = recorded.get(_META_SCHEMA_VERSION)
        if version != str(SCHEMA_VERSION):
            raise ContractRefusal(
                "integrity", "schema",
                f"the control store at {name_value(path)} is schema "
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
        """The manager's clock, proved rather than trusted.

        Exposed through the store so an act built ON it stamps its rows from the
        SAME instant source the journal does. A module reaching for wall time of
        its own would put two clocks in one manager, and a fixture that pinned
        one would silently not pin the other.
        """
        # THE BOUNDARY'S OWN REFUSAL, unwrapped. It was wrapped in a message of
        # mine, which read better and DESTROYED THE LABEL -- and the label is how
        # a probe proves it reached this boundary rather than some other. A
        # rewritten refusal is a refusal whose origin nobody can check.
        return boundaries.instant(self._clock(),
                                  "the configured clock's answer")

    # -- the atomic boundary -------------------------------------------------

    def transact(self, operation_id, kind, signature, action):
        """One atomic manager act, journalled by its operation identity.

        The collision check is made HERE, inside the transaction, because two
        managers can reach it concurrently and a read-then-write check outside
        would let both through.
        """
        # THE SAME RULE, AT EVERY VALUE THAT REACHES A TEXT COLUMN. The review
        # named the kind; a sweep found the identity, the settled instant, the
        # sealed refusal and both READ paths leaking `UnicodeEncodeError` the
        # same way. A rule applied at one of six sites is not applied -- sixth
        # time in this campaign -- so it is applied at all six.
        boundaries.identity(operation_id, "an operation identity")
        # THE ACTION IS A CAPABILITY, typed before a lock is taken. One that
        # cannot be called would fault INSIDE the transaction, which is the one
        # place a fault costs more than a refusal.
        boundaries.capability(action, "the journalled action")
        self._agreeing(kind, signature)
        found, value = self.replay(operation_id, signature, kind=kind)
        if found:
            return value
        connection = self._connection
        connection.execute("BEGIN IMMEDIATE")
        try:
            # RE-READ INSIDE THE LOCK. The optimistic peek above answers the
            # common case without taking a write lock; this is the one that
            # decides.
            found, value = self.replay(operation_id, signature, kind=kind)
            if found:
                connection.execute("ROLLBACK")
                return value
            connection.execute("SAVEPOINT act")
            try:
                result = action(connection)
            except ContractRefusal as refusal:
                if refusal.durable:
                    # Sealed first, then released -- and MEASURED AS EQUIVALENT
                    # for the outcome, so the claim here is the smaller true
                    # one. What protects the writes is the ROLLBACK in the outer
                    # handler: an unsealable refusal raises before the COMMIT
                    # either way, and the whole transaction goes back. Sealing
                    # first means the failure happens before this branch starts
                    # committing rather than in the middle of it, which is worth
                    # having and is not what makes the property hold.
                    #
                    # The property itself: a durable refusal that cannot be
                    # recorded must not keep its writes, or the retry would find
                    # no journal row and do the work again.
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
                # Anything that is not a refusal is a FAULT: the transaction
                # goes back rather than being journalled, because an operation
                # whose failure we cannot describe is not one we may record an
                # outcome for.
                connection.execute("ROLLBACK TO act")
                connection.execute("ROLLBACK")
                raise
            connection.execute("RELEASE act")
            # Inside the transaction, so a refusal here takes the action's
            # writes with it. A committed mutation whose journal row was
            # rejected would be the effectively-once mechanism's worst state:
            # done, unrecorded, and repeatable.
            committed = own(result, what="an operation result")
            # RECORDED INSIDE THE TRANSACTION, and the bytes recorded are the
            # bytes replayed. My first draft committed the action's writes and
            # never wrote this row at all -- so the retry ran the action a
            # SECOND TIME and returned a different answer under one operation
            # identity. Found by the first thing I ran against it, which is the
            # argument for exercising a mechanism rather than reading it.
            self._record(operation_id, kind, signature, "committed",
                         _recorded(committed), None)
            connection.execute("COMMIT")
            # The COMMITTED answer, not the action's object. An exact retry
            # replays these same bytes, so the first caller and every later one
            # are told the same thing -- and it is nobody's alias.
            return committed
        except BaseException:
            try:
                connection.execute("ROLLBACK")
            except BaseException:
                pass
            raise

    # The two members a manager signature has, and the only two.
    _SIGNATURE_MEMBERS = ("kind", "operands")

    @classmethod
    def _agreeing(cls, kind, signature):
        """The signature must be one THIS MANAGER COULD HAVE PRODUCED.

        Review [P1], twice over. The first round: the journal stored `kind` and
        `manager_signature` puts the kind INSIDE the signature, and `transact`
        took both from the caller and compared neither -- so a retry with the
        same signature and a different kind replayed the first success. Two
        caller-controlled accounts of one fact with nothing proving they agree.

        The second round: checking that they agree is not the same as checking
        the signature IS one. Parseable JSON with a matching `kind` was accepted,
        so an indented spelling, a document with no `operands`, and one carrying
        an extra member were all journalled -- DURABLE IDENTITIES
        `manager_signature` CANNOT PRODUCE. Equivalent operations could then
        acquire different byte identities, and data outside the defined operand
        set could enter collision and replay identity.

        So the test is not "does this parse and agree" but "is this exactly what
        we would have written": own it as exact POD, require exactly the two
        members, and compare the SUPPLIED BYTES against the canonical
        serialization of the owned document. Anything else is not this manager's
        identity for anything, whatever it parses as.

        All of it runs BEFORE the journal transaction, so a refusal leaves no
        operation row.
        """
        # THE KIND FIRST, and before any comparison. A hostile operand reached
        # `!=` and ran the caller's `__eq__` from inside a boundary that had
        # already decided to refuse -- so it is proved to be text before anything
        # touches it, and `type(x) is str` runs nothing.
        boundaries.text(kind, "an operation kind")
        # THROUGH THE LAYER, not beside it. This was a hand-written copy of the
        # text rule whose message happened to say "an operation signature" -- so
        # a probe aimed at that label was refused by a rule the inventory could
        # not see. The derived inventory caught it, which is what it is for.
        boundaries.text(signature, "an operation signature")
        try:
            parsed = json.loads(signature)
        except ValueError:
            raise ContractRefusal(
                "integrity", "schema",
                "an operation signature is the canonical text this manager "
                "builds from a kind and its operands") from None
        # `own` before anything reads the document: a signature is caller text
        # and its parse is caller data, so the same exact-POD rule applies to it
        # as to any other operand.
        document = own(parsed, what="an operation signature")
        if type(document) is not dict \
                or tuple(sorted(document)) != cls._SIGNATURE_MEMBERS:
            raise ContractRefusal(
                "integrity", "schema",
                f"an operation signature carries exactly "
                f"{', '.join(cls._SIGNATURE_MEMBERS)}; this carries "
                f"{sample_of(sorted(document)) if type(document) is dict else name_value(parsed)}")
        if document["kind"] != kind:
            raise ContractRefusal(
                "refused", "operation-collision",
                f"the operation is submitted as {name_value(kind)} and its "
                f"signature names {name_value(document['kind'])}; one operation "
                f"has one kind, and a row recording two accounts of it could be "
                f"replayed as either")
        if signature != manager_signature(document["kind"], document["operands"]):
            # The BYTES, not the meaning. Two spellings of one document are two
            # durable identities, and a journal keyed on identity cannot tell
            # them apart afterwards.
            raise ContractRefusal(
                "integrity", "schema",
                "an operation signature is the exact canonical text this "
                "manager produces; a different spelling of the same document is "
                "a different durable identity")

    def replay(self, operation_id, signature, *, kind=None):
        """`(found, value)` for one operation identity.

        `kind` is compared when it is supplied. Both accounts are compared --
        the recorded kind and the recorded signature -- because either alone
        lets a reused identity replay an outcome that was decided about
        something else.

        PRESENCE IS ITS OWN FACT. The frozen host answered `null` for both "no
        row" and "the committed result was JSON null", so an exact retry of a
        null-returning operation looked new, ran the action a second time, and
        only then hit the primary key. Effectively-once cannot be built on a
        value that also means absence.

        BYTE-STABLE: the stored JSON is returned as it was recorded, not
        recomputed.
        """
        # THE READS TOO. Found by my own case for the sweep above: an identity
        # that cannot be durable text cannot name a row either, so a lookup for
        # one is a lookup for something that cannot exist -- and it was faulting
        # in the driver rather than refusing. Four write sites and two read
        # sites is what the rule actually covers.
        boundaries.identity(operation_id, "an operation identity")
        row = self._operation_row(operation_id)
        if row is None:
            return (False, None)
        if row["signature"] != signature or (kind is not None
                                             and row["kind"] != kind):
            raise ContractRefusal(
                "refused", "operation-collision",
                f"operation {name_value(operation_id)} is already recorded with "
                f"a different kind or signature; reusing an id with different "
                f"operands changes nothing (§4.2)")
        if row["state"] == "refused":
            # The FIRST answer, reproduced. Rebuilding it as
            # `refused.precondition` would give the retry a different portable
            # meaning and a different retry policy, which is not a replay of the
            # same refusal however faithfully the message was kept.
            # ALREADY OWNED, at the read: the journal's column contract
            # proves this text decodes to the closed pair. Adopting it again
            # here was the duplicate crossing the ruling forbids.
            raise _revived(json.loads(row["refusal"]))
        # ALREADY OWNED, at the read. PLAN 4bz: a value crosses into the
        # receiving domain once, and `_operation_row` is where these bytes cross
        # -- the column contract proves they decode before anything here sees
        # them. Decoding again through the boundary layer would be the blanket
        # revalidation the same ruling forbids, so the decode below is an
        # ordinary parse of a value this store has already proved.
        #
        # A failure here would therefore be a DEFECT in that ownership rather
        # than a refusal, and it is left to fault as one -- the same rule
        # `deadline` follows with its already-owned instant.
        if row["result"] is None:
            return (True, None)
        return (True, json.loads(row["result"]))

    def _record(self, operation_id, kind, signature, state, result, refusal):
        # §13 (W6630): THE JOURNAL IS A DURABLE SURFACE, and it is the one
        # every mutating manager act passes through. The row carries an
        # operation's identity, the full effective signature of its operands,
        # its byte-stable result and its sealed refusal -- and a refusal that
        # interpolated an operand carries whatever that operand was, which is
        # exactly the containment case the walk exists for.
        #
        # THE WHOLE ROW, not the payload alone. The identity and the kind are
        # written by this build and the operands are not, and a rule applied
        # to some columns of a row is a rule applied to a row nobody can point
        # at.
        check_no_durable_secret(
            {"operation_id": operation_id, "kind": kind,
             "signature": signature, "state": state, "result": result,
             "refusal": refusal},
            what="a journalled operation")
        self._connection.execute(
            "INSERT INTO operations (operation_id, kind, signature, state, "
            "result, refusal, settled_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (operation_id, kind, signature, state, result, refusal,
             self._now()))

    def operation_record(self, operation_id):
        """The journal row as a FRESH document, or absence.

        A live row handed back would be a projection a caller could hold while
        the store moved on, which is the same "validate one view, execute
        another" shape the contracts cut exists to make impossible.
        """
        boundaries.identity(operation_id, "an operation identity")
        return self._operation_row(operation_id)

    def _operation_row(self, operation_id):
        """THE ONE CROSSING out of the journal table.

        Review [P1]: the journal was read from two places -- replay and the
        record projection -- and neither owned what came back. `state` is
        branched on, `signature` and `kind` are COMPARED to decide an operation
        collision, and a row whose signature is not durable text would have
        decided that comparison without ever being refused.

        Both sites read the whole row now, so there is one column contract per
        table rather than one per query.
        """
        record = self._connection.execute(
            "SELECT * FROM operations WHERE operation_id = ?",
            (operation_id,)).fetchone()
        if record is None:
            return None
        return boundaries.row(record, "a persisted operation",
                              schema.OPERATION_COLUMNS)
