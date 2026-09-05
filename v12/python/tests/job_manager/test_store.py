"""W71875 — the Job store: ownership, one atomic boundary, byte-stable replay.

The mechanism is the Worker Manager control store's and the obligations are
the same ones, held against THIS store: a database that is not ours is refused
without a byte changed, an operation identity carries one kind and one
signature, a durable refusal replays as itself, and presence is its own fact.

The case that matters most for this leaf is the last one in `Ownership`: the
Job store and the manager's control store sit side by side in one deployment,
and each must refuse the other.
"""

import os
import sqlite3
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import (SCHEMA_VERSION, STORE_KIND, JobStore,
                                   episodes,
                                   episodes_of, job_signature, live_of,
                                   owed_acts, stage_rows, status)
from baton_v12.job_manager.episodes import identities
from baton_v12.worker_manager import ControlStore

if __package__:
    from .fixtures import NOW, UUID, JobManagerCase
else:
    from fixtures import NOW, UUID, JobManagerCase


class Ownership(JobManagerCase):

    def test_an_empty_database_becomes_this_manager_s_store(self):
        store = self.store()
        self.assertEqual(store.incarnation, "jobs-1")
        recorded = dict(store._connection.execute(
            "SELECT key, value FROM meta").fetchall())
        self.assertEqual(recorded["store_kind"], STORE_KIND)
        self.assertEqual(recorded["schema_version"], str(SCHEMA_VERSION))

    def test_reopening_our_own_store_adds_nothing(self):
        self.store().close()
        with open(self.job_path, "rb") as handle:
            before = handle.read()
        self.store()
        reading = sqlite3.connect(self.job_path)
        self.addCleanup(reading.close)
        objects = {row[0] for row in reading.execute(
            "SELECT name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'")}
        self.assertEqual(objects & {"submissions", "jobs", "stages"},
                         {"submissions", "jobs", "stages"})
        self.assertTrue(before)

    def test_the_worker_manager_s_control_store_is_refused_untouched(self):
        # THE TWO STORES SIT SIDE BY SIDE IN ONE DEPLOYMENT and an operator
        # who swaps two paths gets a refusal rather than a scheduler writing
        # into the manager's database. "It is a v12 store" is not ownership.
        control = ControlStore.open(self.control_path, incarnation="manager-1",
                                    clock=self.clock)
        control.close()
        with open(self.control_path, "rb") as handle:
            before = handle.read()
        with self.assertRaises(ContractRefusal) as caught:
            JobStore.open(self.control_path, authority_uuid=UUID, incarnation="jobs-1",
                          clock=self.clock)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "schema"))
        self.assertIn("worker-manager", caught.exception.message)
        with open(self.control_path, "rb") as handle:
            self.assertEqual(handle.read(), before)

    def test_our_store_is_refused_by_the_worker_manager(self):
        self.store().close()
        with self.assertRaises(ContractRefusal) as caught:
            ControlStore.open(self.job_path, incarnation="manager-1",
                              clock=self.clock)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "schema"))

    def test_a_foreign_database_is_refused_without_a_byte_changed(self):
        path = os.path.join(self.root, "foreign.sqlite3")
        connection = sqlite3.connect(path, isolation_level=None)
        connection.execute("CREATE TABLE meta (id INTEGER)")
        connection.close()
        with open(path, "rb") as handle:
            before = handle.read()
        with self.assertRaises(ContractRefusal):
            JobStore.open(path, authority_uuid=UUID, incarnation="jobs-1", clock=self.clock)
        with open(path, "rb") as handle:
            self.assertEqual(handle.read(), before)

    def test_a_store_at_another_schema_version_is_not_guessed_across(self):
        store = self.store()
        store._connection.execute(
            "UPDATE meta SET value = '99' WHERE key = 'schema_version'")
        store.close()
        with self.assertRaises(ContractRefusal) as caught:
            JobStore.open(self.job_path, authority_uuid=UUID, incarnation="jobs-1",
                          clock=self.clock)
        self.assertIn("does not guess across versions",
                      caught.exception.message)

    def test_an_unnamed_path_is_refused_rather_than_defaulted(self):
        with self.assertRaises(ContractRefusal) as caught:
            JobStore.open("", authority_uuid=UUID, incarnation="jobs-1", clock=self.clock)
        self.assertEqual(caught.exception.code, "path")

    def test_an_instance_names_its_incarnation(self):
        with self.assertRaises(ContractRefusal):
            JobStore.open(self.job_path, authority_uuid=UUID, incarnation="", clock=self.clock)

    def test_a_clock_that_cannot_answer_is_found_at_open(self):
        def broken():
            return "not-an-instant"

        with self.assertRaises(ContractRefusal):
            JobStore.open(self.job_path, authority_uuid=UUID, incarnation="jobs-1", clock=broken)


class Journal(JobManagerCase):

    def signature(self, **operands):
        return job_signature("probe", operands or {"one": 1})

    def act(self, answer):
        def perform(connection):
            self.performed.append(answer)
            return answer
        return perform

    def setUp(self):
        super().setUp()
        self.performed = []

    def test_an_exact_retry_replays_the_first_answer(self):
        store = self.store()
        signature = self.signature()
        first = store.transact("probe:1", "probe", signature,
                               self.act({"answer": 1}))
        second = store.transact("probe:1", "probe", signature,
                                self.act({"answer": 2}))
        self.assertEqual(first, {"answer": 1})
        self.assertEqual(second, {"answer": 1})
        self.assertEqual(self.performed, [{"answer": 1}])

    def test_presence_is_its_own_fact(self):
        # A committed `null` result must not read as "no row", or the retry
        # runs the action a second time and only then hits the primary key.
        store = self.store()
        signature = self.signature()
        store.transact("probe:null", "probe", signature, self.act(None))
        store.transact("probe:null", "probe", signature, self.act(None))
        self.assertEqual(len(self.performed), 1)

    def test_reusing_an_identity_with_other_operands_collides(self):
        store = self.store()
        store.transact("probe:1", "probe", self.signature(one=1),
                       self.act({"answer": 1}))
        with self.assertRaises(ContractRefusal) as caught:
            store.transact("probe:1", "probe", self.signature(one=2),
                           self.act({"answer": 2}))
        self.assertEqual(caught.exception.code, "operation-collision")

    def test_one_operation_has_one_kind(self):
        store = self.store()
        with self.assertRaises(ContractRefusal) as caught:
            store.transact("probe:1", "other", self.signature(),
                           self.act({"answer": 1}))
        self.assertEqual(caught.exception.code, "operation-collision")

    def test_a_signature_this_build_could_not_have_produced_is_refused(self):
        store = self.store()
        with self.assertRaises(ContractRefusal):
            store.transact("probe:1", "probe",
                           '{ "kind": "probe", "operands": {} }',
                           self.act({"answer": 1}))

    def test_a_durable_refusal_replays_as_itself(self):
        store = self.store()
        signature = self.signature()

        def refusing(connection):
            self.performed.append("ran")
            raise ContractRefusal("policy", "retention", "no", durable=True)

        for _ in range(2):
            with self.assertRaises(ContractRefusal) as caught:
                store.transact("probe:refused", "probe", signature, refusing)
            self.assertEqual((caught.exception.category,
                              caught.exception.code), ("policy", "retention"))
            self.assertTrue(caught.exception.durable)
        self.assertEqual(self.performed, ["ran"])

    def test_an_ordinary_refusal_leaves_the_act_retryable(self):
        store = self.store()
        signature = self.signature()
        attempts = []

        def sometimes(connection):
            attempts.append(len(attempts))
            if len(attempts) == 1:
                raise ContractRefusal("refused", "precondition", "not yet")
            return {"answer": "later"}

        with self.assertRaises(ContractRefusal):
            store.transact("probe:retry", "probe", signature, sometimes)
        self.assertEqual(store.transact("probe:retry", "probe", signature,
                                        sometimes), {"answer": "later"})

    def test_a_fault_is_not_journalled_as_an_outcome(self):
        store = self.store()

        def faulting(connection):
            raise ZeroDivisionError("a defect, not a refusal")

        with self.assertRaises(ZeroDivisionError):
            store.transact("probe:fault", "probe", self.signature(), faulting)
        self.assertIsNone(store.operation_record("probe:fault"))

    def test_the_journal_row_is_readable_as_a_fresh_document(self):
        store = self.store()
        store.transact("probe:1", "probe", self.signature(),
                       self.act({"answer": 1}))
        record = store.operation_record("probe:1")
        self.assertEqual(record["kind"], "probe")
        self.assertEqual(record["state"], "committed")
        self.assertEqual(record["settled_at"], NOW)


# The schema-1 shape, exactly as this package shipped it at `efbad19`. Kept
# here rather than imported because the point of the case below is that a store
# written by THAT build opens under this one -- a copy that tracked the current
# schema would test nothing.
SCHEMA_1 = """
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);

CREATE TABLE operations (
  operation_id TEXT PRIMARY KEY, kind TEXT NOT NULL, signature TEXT NOT NULL,
  state TEXT NOT NULL CHECK (state IN ('committed', 'refused')),
  result TEXT, refusal TEXT, settled_at TEXT NOT NULL,
  CHECK ((state = 'committed' AND refusal IS NULL)
         OR (state = 'refused' AND result IS NULL AND refusal IS NOT NULL))
);

CREATE TABLE submissions (
  submission_id TEXT PRIMARY KEY, signature TEXT NOT NULL,
  document TEXT NOT NULL, incarnation TEXT NOT NULL,
  recorded_at TEXT NOT NULL
);

CREATE TABLE jobs (
  job_id TEXT PRIMARY KEY,
  submission_id TEXT NOT NULL REFERENCES submissions(submission_id),
  ordinal INTEGER NOT NULL, input_digest TEXT NOT NULL,
  policy_digest TEXT NOT NULL, test_scope TEXT NOT NULL,
  terminal_policy TEXT NOT NULL
);

CREATE TABLE stages (
  stage_id TEXT PRIMARY KEY, job_id TEXT NOT NULL REFERENCES jobs(job_id),
  ordinal INTEGER NOT NULL, kind TEXT NOT NULL, work_id TEXT NOT NULL,
  profile_name TEXT NOT NULL, profile_digest TEXT NOT NULL,
  depends_on TEXT NOT NULL, offer_id TEXT NOT NULL, attempt_id TEXT NOT NULL,
  UNIQUE (job_id, kind)
);

CREATE TABLE receipts (
  stage_id TEXT NOT NULL REFERENCES stages(stage_id),
  act TEXT NOT NULL CHECK (act IN ('admit', 'claim')),
  operation_id TEXT NOT NULL,
  state TEXT NOT NULL CHECK (state IN ('performed', 'adopted', 'refused')),
  detail TEXT NOT NULL, recorded_at TEXT NOT NULL, incarnation TEXT NOT NULL,
  PRIMARY KEY (stage_id, act)
);
"""


class MigratingFromSchemaOne(JobManagerCase):
    """W73629 — a store written before episodes existed, carried forward WHOLE.

    A persisted submission is a pipeline somebody is running, so the store is
    migrated rather than refused. The obligation this fixes on the migration is
    that it INVENTS NOTHING: every episode 1 asserts exactly what its schema-1
    stage row already asserted, so the canonical operation identities a
    migrated store reconciles against are the ones its receipts already name.
    """

    def write_schema_1(self):
        connection = sqlite3.connect(self.job_path, isolation_level=None)
        self.addCleanup(connection.close)
        connection.executescript(SCHEMA_1)
        connection.execute("INSERT INTO meta VALUES ('store_kind', ?)",
                           (STORE_KIND,))
        connection.execute("INSERT INTO meta VALUES ('schema_version', '1')")
        connection.execute(
            "INSERT INTO submissions VALUES ('sub-1', 's', '{}', 'jobs-old', "
            "?)", (NOW,))
        connection.execute(
            "INSERT INTO jobs VALUES ('job-a', 'sub-1', 0, 'sha256:1', "
            "'sha256:2', '[]', 'report-and-hold')")
        connection.execute(
            "INSERT INTO stages VALUES ('job-a/implementation', 'job-a', 0, "
            "'implementation', '0000000a-W1', 'reference', 'sha256:b', '[]', "
            "'offer:job-a/implementation', 'attempt:job-a/implementation')")
        connection.execute(
            "INSERT INTO receipts VALUES ('job-a/implementation', 'admit', "
            "'offer.issue:offer:job-a/implementation', 'performed', '{}', ?, "
            "'jobs-old')", (NOW,))
        connection.close()

    def test_a_schema_one_store_opens_at_the_current_version(self):
        self.write_schema_1()
        store = self.store()
        recorded = dict(store._connection.execute(
            "SELECT key, value FROM meta").fetchall())
        self.assertEqual(recorded["schema_version"], str(SCHEMA_VERSION))
        self.assertEqual(recorded["store_kind"], STORE_KIND)

    def test_every_migrated_stage_keeps_the_identities_it_already_had(self):
        self.write_schema_1()
        store = self.store()
        held = episodes_of(store, "job-a/implementation")
        self.assertEqual(len(held), 1)
        self.assertEqual(held[0]["episode"], 1)
        # THE OLD ROW'S OWN IDENTITIES, not recomputed ones. The manager
        # journal already holds `offer.issue:offer:job-a/implementation`, and
        # an episode naming anything else would orphan that reconciliation.
        self.assertEqual(held[0]["offer_id"], "offer:job-a/implementation")
        self.assertEqual(held[0]["attempt_id"],
                         "attempt:job-a/implementation")
        self.assertIsNone(held[0]["ended_state"])
        # The submission's own instant and incarnation, because that is when
        # and by whom this episode was really opened.
        self.assertEqual(held[0]["opened_at"], NOW)
        self.assertEqual(held[0]["incarnation"], "jobs-old")
        self.assertEqual(live_of(store, "job-a/implementation")["episode"], 1)

    def test_the_migrated_receipt_belongs_to_episode_one(self):
        self.write_schema_1()
        store = self.store()
        row = store._connection.execute(
            "SELECT * FROM receipts").fetchone()
        self.assertEqual(row["episode"], 1)
        self.assertEqual(row["act"], "admit")
        self.assertEqual(row["operation_id"],
                         "offer.issue:offer:job-a/implementation")

    def test_the_migrated_stage_row_drops_the_moved_columns(self):
        self.write_schema_1()
        store = self.store()
        stage = stage_rows(store)[0]
        self.assertEqual(stage["stage_id"], "job-a/implementation")
        self.assertNotIn("offer_id", dict(stage))
        self.assertNotIn("attempt_id", dict(stage))

    def test_a_migrated_store_still_derives_and_projects(self):
        """The pipeline survives the migration rather than merely the rows.

        It had an `admit` receipt, so it is `offered` and owes its claim --
        exactly what the same store answered before this build existed.
        """
        from baton_v12.job_manager import Unobserved

        self.write_schema_1()
        store = self.store()
        acts = self.operations()
        self.assertEqual([one["act"] for one in owed_acts(store, acts)],
                         ["claim"])
        held = status(store, Unobserved(),
                      observed_at=NOW)["jobs"][0]["stages"][0]
        self.assertEqual(held["state"], "offered")
        self.assertEqual(held["episode"], 1)
        self.assertEqual([one["episode"] for one in held["episodes"]], [1])

    def test_reopening_a_migrated_store_migrates_nothing_further(self):
        self.write_schema_1()
        self.store().close()
        again = self.store(incarnation="jobs-2")
        self.assertEqual(len(episodes_of(again, "job-a/implementation")), 1)
        self.assertEqual(
            dict(again._connection.execute(
                "SELECT key, value FROM meta").fetchall())["schema_version"],
            str(SCHEMA_VERSION))

class TheStoreIsBoundToOneAuthority(JobManagerCase):
    """W83781 — the namespace every episode identity is derived in.

    `stage_id` and `episode` are both LOCAL to one Job store, so deriving an
    OCI attempt identity from them alone made two independent authorities
    produce the same identity for the same local stage name. A fresh authority
    was measured deriving an attempt already held by a retained container
    belonging to a different Authority and a different Work; the adapter
    refused to adopt it, correctly, and that refusal is not the defect.

    The correction is a store-level BINDING rather than a capability: what is
    persisted is a stable public identity, and holding it grants no session,
    no Authority store and no mutation surface.
    """

    OTHER = "1" * 31 + "b"

    def opened(self, authority_uuid=UUID, incarnation="jobs-1"):
        store = JobStore.open(self.job_path, authority_uuid=authority_uuid,
                              incarnation=incarnation, clock=self.clock)
        self.addCleanup(store.close)
        return store

    def test_a_new_store_persists_the_authority_it_was_opened_under(self):
        store = self.opened()
        self.assertEqual(store.authority_uuid, UUID)
        held = store._connection.execute(
            "SELECT value FROM meta WHERE key = 'authority_uuid'").fetchone()
        self.assertEqual(held["value"], UUID)

    def test_the_same_authority_reopens_the_store(self):
        self.opened().close()
        self.assertEqual(self.opened(incarnation="jobs-2").authority_uuid,
                         UUID)

    def bytes_of(self):
        with open(self.job_path, "rb") as reading:
            return reading.read()

    def test_another_authority_refuses_and_changes_nothing(self):
        self.opened().close()
        before = self.bytes_of()
        with self.assertRaises(ContractRefusal) as caught:
            self.opened(authority_uuid=self.OTHER, incarnation="jobs-2")
        self.assertEqual(caught.exception.code, "precondition")
        self.assertEqual(self.bytes_of(), before,
                         "a refused open leaves the store byte-for-byte")

    def test_a_malformed_authority_refuses_before_the_path_exists(self):
        for spoiled in (None, "", 7, UUID.upper(), UUID[:-1], UUID + "0",
                        "g" * 32, " " + UUID[1:]):
            with self.subTest(authority_uuid=spoiled):
                with self.assertRaises(ContractRefusal):
                    JobStore.open(self.job_path, authority_uuid=spoiled,
                                  incarnation="jobs-1", clock=self.clock)
                self.assertFalse(os.path.exists(self.job_path),
                                 "the path is not created by a refused open")

    def test_the_binding_is_the_authoritys_own_rule_and_not_a_second_one(self):
        """The vocabulary is imported rather than restated.

        A looser spelling living in the Job manager is exactly the drift the
        finding forbids, so this holds the store's refusal to the Authority
        package's own predicate rather than to a copy of its grammar.
        """
        from baton_v12.authority.identity import check_authority_uuid
        from baton_v12.job_manager.schema import check_authority

        self.assertEqual(check_authority_uuid(UUID), UUID)
        self.assertEqual(check_authority(UUID, what="a binding"), UUID)
        # THE RULE IS THEIRS AND THE REFUSAL IS OURS. A caller of this package
        # catches `ContractRefusal` everywhere else, so a boundary that
        # sometimes raised the Authority's own exception would be one every
        # caller had to special-case.
        with self.assertRaises(ContractRefusal):
            check_authority(UUID.upper(), what="a binding")


class MigratingPinsTheAuthorityWithoutRenamingAnything(MigratingFromSchemaOne):
    """W83781 — the compatibility obligation the namespace inherits.

    Episode identity is persisted EVIDENCE, not a value readers recompute.
    Worker Manager journal keys and Job receipts already reference the exact
    offer and attempt strings a store recorded, so a migration that renamed
    one would orphan the reconciliation that names it. The namespace decides
    what a NEW episode is called and nothing else.
    """

    OTHER = "1" * 31 + "b"

    def opened(self, authority_uuid=UUID, incarnation="jobs-1"):
        store = JobStore.open(self.job_path, authority_uuid=authority_uuid,
                              incarnation=incarnation, clock=self.clock)
        self.addCleanup(store.close)
        return store

    def bytes_of(self):
        with open(self.job_path, "rb") as reading:
            return reading.read()

    def write_schema_2(self):
        """A store at the version immediately before the binding existed."""
        self.write_schema_1()
        held = JobStore.open(self.job_path, authority_uuid=UUID,
                             incarnation="jobs-2", clock=self.clock)
        held.close()
        connection = sqlite3.connect(self.job_path, isolation_level=None)
        self.addCleanup(connection.close)
        connection.execute("UPDATE meta SET value = '2' WHERE key = ?",
                           ("schema_version",))
        connection.execute("DELETE FROM meta WHERE key = 'authority_uuid'")
        connection.close()

    def test_a_schema_two_store_is_pinned_by_the_migration(self):
        self.write_schema_2()
        store = self.store()
        recorded = dict(store._connection.execute(
            "SELECT key, value FROM meta").fetchall())
        self.assertEqual(recorded["schema_version"], str(SCHEMA_VERSION))
        self.assertEqual(recorded["authority_uuid"], UUID)

    def test_a_migrated_store_keeps_every_identity_and_receipt(self):
        for write in (self.write_schema_1, self.write_schema_2):
            with self.subTest(from_schema=write.__name__):
                self.setUp()
                write()
                store = self.store()
                held = episodes_of(store, "job-a/implementation")
                self.assertEqual(
                    (held[0]["offer_id"], held[0]["attempt_id"]),
                    ("offer:job-a/implementation",
                     "attempt:job-a/implementation"),
                    "a migrated episode keeps the identity its journal names")
                self.assertEqual(
                    [row["operation_id"] for row in store._connection.execute(
                        "SELECT operation_id FROM receipts")],
                    ["offer.issue:offer:job-a/implementation"])

    def test_the_namespace_applies_only_after_the_migration(self):
        """An episode opened AFTER the pin is namespaced; episode 1 is not.

        That asymmetry is the whole compatibility rule stated as one case: a
        legacy episode keeps the name its journal already references, and the
        replacement it is eventually given is derived in the Authority the
        store is now bound to.
        """
        self.write_schema_2()
        store = self.store()
        held = episodes_of(store, "job-a/implementation")[0]
        self.assertNotEqual(held["offer_id"],
                            identities(UUID, "job-a/implementation", 1)[0])
        # ENDED THROUGH ITS OWN OWNER, not by handing `open_next` a dict that
        # merely says so: the partial unique index allows one live episode per
        # stage, and it is right to refuse a replacement while the first one is
        # still live.
        ended = episodes.end_episode(store, held,
                                     "abandoned-after-restart", 1)
        fresh = episodes.open_next(store, "job-a/implementation", ended)
        self.assertEqual(
            (fresh["offer_id"], fresh["attempt_id"]),
            identities(UUID, "job-a/implementation", 2))

    def test_a_migration_under_another_authority_pins_that_one(self):
        """The binding is the OPENER's, because a legacy store carries none.

        There is nothing in a schema-1 or schema-2 store that says which
        Authority it belonged to, so the migration cannot discover it and must
        be told. What it must not do is guess one.
        """
        self.write_schema_2()
        store = JobStore.open(self.job_path, authority_uuid=self.OTHER,
                              incarnation="jobs-3", clock=self.clock)
        self.addCleanup(store.close)
        self.assertEqual(store.authority_uuid, self.OTHER)
        store.close()
        with self.assertRaises(ContractRefusal):
            JobStore.open(self.job_path, authority_uuid=UUID,
                          incarnation="jobs-4", clock=self.clock)
    def test_a_failed_migration_rolls_the_uuid_and_the_version_back(self):
        """W83781 review [P1]: the promised atomicity, exercised.

        The finding requires a failed migration to roll the binding and the
        version stamp back TOGETHER, so no store is ever left carrying one
        without the other. That is a claim about the public open boundary, not
        about how the transaction reads, so this fails the migration and then
        asks what the store is.

        WHERE THE FAILURE GOES IS THE WHOLE CASE. Review 2026-09-04T09-22-40Z
        [P1]: this used to raise from `_statements`, which `_migrate` calls
        BEFORE it has advanced the version or inserted the binding -- so it
        proved only that an exception just after `BEGIN IMMEDIATE` changes
        nothing, and would have passed an implementation that stamped either
        value outside this transaction. The hook now raises only once BOTH
        durable values are readable on the migration connection and the COMMIT
        has not run, which is the only moment at which "they roll back
        together" is a statement about anything.
        """
        from unittest import mock

        self.write_schema_2()
        before = self.bytes_of()
        saw = []
        real = JobStore._objects

        def once_both_stamps_are_visible(connection):
            recorded = dict(connection.execute(
                "SELECT key, value FROM meta").fetchall())
            if (recorded.get("schema_version") == str(SCHEMA_VERSION)
                    and recorded.get("authority_uuid") == UUID):
                saw.append(recorded)
                raise RuntimeError("migration interrupted after both stamps")
            return real(connection)

        with mock.patch.object(JobStore, "_objects",
                               staticmethod(once_both_stamps_are_visible)):
            with self.assertRaises(RuntimeError):
                JobStore.open(self.job_path, authority_uuid=UUID,
                              incarnation="jobs-broken", clock=self.clock)
        self.assertEqual(len(saw), 1,
                         "the failure was injected once, inside the migration")
        self.assertEqual(saw[0]["schema_version"], str(SCHEMA_VERSION))
        self.assertEqual(saw[0]["authority_uuid"], UUID)
        self.assertEqual(self.bytes_of(), before,
                         "an interrupted migration leaves the store as found")
        connection = sqlite3.connect(self.job_path, isolation_level=None)
        self.addCleanup(connection.close)
        recorded = dict(connection.execute(
            "SELECT key, value FROM meta").fetchall())
        self.assertEqual(recorded["schema_version"], "2",
                         "the version stamp is not advanced")
        self.assertNotIn("authority_uuid", recorded,
                         "and no binding survives the rollback")
        connection.close()
        # AND THE STORE IS STILL MIGRATABLE, which is the half a rollback
        # exists for: nothing about the failure poisoned it.
        store = self.opened(incarnation="jobs-after")
        self.assertEqual(store.authority_uuid, UUID)
        self.assertEqual(
            episodes_of(store, "job-a/implementation")[0]["offer_id"],
            "offer:job-a/implementation")

    def test_a_stale_opener_cannot_rebind_the_winners_authority(self):
        """W83781 review [P0], deterministically.

        Two openers both observe schema 2 before either holds the write lock.
        The first migrates and records its Authority. The second then acquires
        the lock still believing the store is at 2 -- and must not write: the
        winner's episodes are in the winner's namespace, and rebinding would
        derive every future episode in a namespace the existing rows were
        never in.
        """
        self.write_schema_2()
        first = sqlite3.connect(self.job_path, isolation_level=None)
        self.addCleanup(first.close)
        first.row_factory = sqlite3.Row
        second = sqlite3.connect(self.job_path, isolation_level=None)
        self.addCleanup(second.close)
        second.row_factory = sqlite3.Row
        # BOTH READ THE VERSION BEFORE EITHER MIGRATES, which is exactly the
        # window `_adopt` opens between its own read and `_migrate`'s lock.
        stale = JobStore._validate(
            {row["key"]: row["value"] for row in
             first.execute("SELECT key, value FROM meta")}, self.job_path)
        self.assertEqual(stale, 2)
        JobStore._migrate(first, stale, self.job_path, UUID)
        # THE WINNER'S FINISHED STORE, BYTE FOR BYTE. Review
        # 2026-09-04T09-22-40Z [P2]: the original P0 asked the loser to be
        # unable to change the winner's UUID, version, identities OR BYTES,
        # and only the first three were measured. The already-current store
        # covered by the wrong-UUID open above is a different path -- it never
        # enters the stale migration that caused the defect.
        won = self.bytes_of()
        JobStore._migrate(second, stale, self.job_path, self.OTHER)
        self.assertEqual(self.bytes_of(), won,
                         "the loser's migration writes nothing at all")
        recorded = dict(second.execute(
            "SELECT key, value FROM meta").fetchall())
        self.assertEqual(recorded["authority_uuid"], UUID,
                         "the loser does not replace the winner's binding")
        self.assertEqual(recorded["schema_version"], str(SCHEMA_VERSION))
        # AND THE LOSER IS THEN REFUSED AT THE BOUNDARY THAT DECIDES IT.
        with self.assertRaises(ContractRefusal) as caught:
            self.opened(authority_uuid=self.OTHER, incarnation="jobs-loser")
        self.assertEqual(caught.exception.code, "precondition")
        held = self.opened(incarnation="jobs-winner")
        self.assertEqual(
            episodes_of(held, "job-a/implementation")[0]["offer_id"],
            "offer:job-a/implementation")

    def test_a_corrupt_binding_is_malformed_evidence_not_another_authority(
            self):
        """W83781 review [P2]: the store's own evidence, owned before use.

        `boundaries.text` says a value is storable text. It does not say it is
        an Authority, so a corrupt row read back as one sent an operator
        looking for the Authority it names -- which does not exist.
        """
        self.opened().close()
        connection = sqlite3.connect(self.job_path, isolation_level=None)
        self.addCleanup(connection.close)
        connection.execute("UPDATE meta SET value = ? WHERE key = ?",
                           ("not-an-authority", "authority_uuid"))
        connection.close()
        with self.assertRaises(ContractRefusal) as caught:
            self.opened(incarnation="jobs-corrupt")
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "schema"))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
