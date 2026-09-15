"""W161230 slice1, condition 4: the portable managed result, in the store.

THREE THINGS ARE PROVED HERE and they are separate on purpose.

  THE EXPLICIT UPGRADE. A coordinator at schema 5 is not migrated by opening
  it. `open` refuses and names the act; `upgrade_store` performs it, once, in
  one transaction, after the SAME ownership decision an ordinary adoption
  makes -- so a store this build cannot describe entirely is left exactly as
  it was found. What the step preserves it preserves by not touching: it
  creates a relation and alters nothing, so records and live leases are where
  they were.

  READ-ONLY COMPATIBILITY. A status reader understands both shapes and writes
  neither. Asking a schema-5 coordinator for managed results is answered --
  it has none and never had any -- rather than raising `no such table` from
  inside a query.

  THE SHARED KEY. One submission has one result per target snapshot, in
  EITHER representation. SQLite enforces a UNIQUE per table; this key spans
  two, so both writers claim it inside the one target-global transaction, and
  each direction is driven below.
"""
import json
import os
import pathlib
import sqlite3
import sys
import unittest
from unittest import mock

from baton_v12.contracts import ContractRefusal
from baton_v12.integration import (activate_target, enqueue, entries_of,
                                   grant_lease, lease_of,
                                   managed_execution as managed, target_of)
from baton_v12.integration.reconciliation import (_claim_result_key,
                                                  attach_managed_phase,
                                                  managed_result_of,
                                                  record_managed_result,
                                                  result_identity, result_of)
from baton_v12.integration.store import (IntegrationStore, READABLE_VERSIONS,
                                         integration_signature, shape_for,
                                         upgrade_store)
from baton_v12.integration import schema
from baton_v12.job_manager import execution_limits

from . import fixtures
# THE RECONCILIATION FIXTURE, UNCHANGED. A genuine legacy result needs the
# real repositories, the real profile and the real submission owners, and
# `test_reconciliation.ResultCase` already composes exactly those -- a second
# fixture here would be a second account of what a legacy result IS.
from .test_reconciliation import REFERENCE, TARGET, ResultCase

ORCHESTRATION = "integration-capacity-1"
PREPARE = "prepare-attempt-1"
APPLY = "apply-attempt-1"
COMMANDS = ["fetch", "compose", "verify"]
PROPOSAL = "proposal-1"
REVISION = "b" * 40
COLLECTED = "sha256:" + "c" * 64


def assignment():
    return {"work_ref": {"authority_uuid": fixtures.UUID_A,
                         "work_id": fixtures.UUID_A[:8] + "-W7"},
            "participant": "baton.impl-a", "generation": 1}


def submission(**changed):
    """The submission identities a managed result is a result FOR.

    The same words the legacy relation names them by -- and NONE of the four
    location-bearing members, because a portable result does not carry a
    coordinator's workspace or target path.
    """
    held = {"authority_uuid": fixtures.UUID_A,
            "work_id": fixtures.UUID_A[:8] + "-W7", "job_id": "job-1",
            "line_id": "line-1", "source_checkpoint_id": "checkpoint-1",
            "source_verdict_id": "verdict-1", "source_proposal_id": PROPOSAL,
            "source_result_id": "result-1",
            "source_result_digest": "sha256:" + "1" * 64,
            "source_checkpoint_digest": "sha256:" + "2" * 64,
            "source_base": "a" * 40, "source_candidate": "c" * 40}
    held.update(changed)
    return held


class ManagedStorageCase(fixtures.CoordinatorCase):

    def coordinator(self):
        store = self.store()
        activate_target(store, fixtures.target())
        return store

    def task(self, **changed):
        held = {"phase": "prepare", "orchestration_id": ORCHESTRATION,
                "canonical_target_id": fixtures.TARGET,
                "execution_attempt_id": PREPARE,
                "assignment": assignment(),
                "task_digest": "sha256:" + "a" * 64,
                "input_digest": "sha256:" + "b" * 64,
                "harness_digest": "sha256:" + "h" * 64,
                "execution_limits": execution_limits.resolved({}, 1),
                "commands": COMMANDS}
        held.update(changed)
        return managed.managed_task(**held)

    def account(self, task=None, **changed):
        task = task or self.task()
        report = managed.collected_report(
            task, kind="measured",
            completed=[{"name": one, "status": 0} for one in COMMANDS],
            status=0)
        held = {"collected": {"result_id": "result-" + task[
            "execution_attempt_id"], "manifest_digest": COLLECTED,
            "disposition": "completed"}}
        held.update(changed)
        return {"task": task,
                "result": managed.managed_result(task, report, **held)}

    def applying(self, **changed):
        """The apply phase of the SAME result: a second account, not a second
        result. The first form made each phase a row carrying the shared
        (target, proposal, revision) key, so two phases of one result
        collided -- and the case that appeared to show both working had moved
        the second to another target revision."""
        held = {"phase": "apply", "execution_attempt_id": APPLY,
                "parent": {"execution_attempt_id": PREPARE,
                           "collected_digest": COLLECTED}}
        held.update(changed)
        return self.account(self.task(**held), collected=None)

    def phases(self, **changed):
        held = {"prepare": self.account(), "apply": self.applying()}
        held.update(changed)
        return held

    def record(self, store, *, phases=("prepare", "apply"), **changed):
        """Create the result, then attach each phase by its OWN act.

        Review 2026-09-13T19:07:44Z: creation used to take the whole phase set
        at once, so a preparation retained on its own could never be joined by
        an apply -- the later call changed the one immutable creation
        operation and collided. The accepted sequence is prepare, retain, then
        apply, and this drives exactly that.
        """
        held = {"orchestration_id": ORCHESTRATION,
                "canonical_target_id": fixtures.TARGET,
                "target_revision": REVISION}
        held.update(changed)
        answer = record_managed_result(store, submission(), **held)
        for phase in phases:
            account = self.account() if phase == "prepare" else self.applying()
            answer = attach_managed_phase(
                store, managed_result_id=held["orchestration_id"],
                task=account["task"], result=account["result"])
        return answer

    def populated(self, *, managed=True):
        """A coordinator with a live import in flight, through its own owners.

        Review 2026-09-13T18:51:48Z [P2]: the first preservation case compared
        TABLE DEFINITIONS and one target row. CREATE-only is useful reasoning
        about why nothing should be lost; it is not evidence that nothing was.
        So this enqueues a real entry and grants a real LIVE lease.

        `managed` IS A CHOICE BECAUSE A SCHEMA-5 STORE CANNOT HOLD ONE. Review
        2026-09-13T23:19:08Z: the preservation fixture recorded a managed
        result and then demoted the store by dropping the managed tables while
        LEAVING its `result.managed` acts in the journal -- a schema-5 store
        that carries acts schema 5 never had, which is not an old store at all.
        A case about carrying an old store forward populates the old side only.
        """
        store = self.coordinator()
        entry = enqueue(store, canonical_target_id=fixtures.TARGET,
                        entry_id="entry-1",
                        eligibility=fixtures.eligibility())
        lease = grant_lease(store, canonical_target_id=fixtures.TARGET,
                            entry_id="entry-1", lease_id="lease-1",
                            integrator_participant="baton.integrator",
                            attempt_id="attempt-1")
        if managed:
            self.record(store)
        return store, entry, lease

    def contents(self, tables):
        beside = sqlite3.connect(self.path, isolation_level=None)
        try:
            return {table: [tuple(row) for row in
                            beside.execute(f"SELECT * FROM {table}")]
                    for table in tables}
        finally:
            beside.close()

    def recorded_version(self):
        beside = sqlite3.connect(self.path, isolation_level=None)
        try:
            return beside.execute(
                "SELECT value FROM meta WHERE key = 'schema_version'"
            ).fetchone()[0]
        finally:
            beside.close()

    def legacy_operands(self, proposal, revision):
        held = dict(submission(source_proposal_id=proposal),
                    canonical_target_id=fixtures.TARGET,
                    integration_attempt_id="attempt-" + revision,
                    integration_assignment=assignment(),
                    workspace={"path": "/srv/candidate", "device": 66,
                               "inode": 101},
                    profile_name=fixtures.PROFILE_KIND, profile_version=1,
                    target_revision=revision,
                    target_source={"path": "/srv/target", "device": 66,
                                   "inode": 102},
                    target_reference="reference-1")
        return held

    def legacy(self, store, *, proposal=PROPOSAL, revision=REVISION):
        """One row in the OLD representation for the same target snapshot.

        ITS IDENTITY IS DERIVED, not made up: `result_of` re-derives the
        identity from the row's own operands, so a fixture that named its row
        arbitrarily would be refused by that rule before reaching the one
        these cases are about (measured, step 70).
        """
        operands = self.legacy_operands(proposal, revision)
        result_id = result_identity(operands)
        store._connection.execute(
            "INSERT INTO integration_results (result_id, operation_id, "
            "canonical_target_id, authority_uuid, work_id, job_id, line_id, "
            "source_checkpoint_id, source_verdict_id, source_proposal_id, "
            "source_result_id, source_result_digest, source_checkpoint_digest, "
            "source_base, source_candidate, integration_attempt_id, "
            "integration_assignment, workspace, profile_name, profile_version, "
            "target_revision, target_source, target_reference, state, "
            "recorded_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
            "?, ?, ?, ?, ?, ?, ?, ?, ?, 'preparing', ?)",
            (result_id, "result.prepare:" + result_id,
             fixtures.TARGET, operands["authority_uuid"],
             operands["work_id"], operands["job_id"], operands["line_id"],
             operands["source_checkpoint_id"], operands["source_verdict_id"],
             proposal, operands["source_result_id"],
             operands["source_result_digest"],
             operands["source_checkpoint_digest"], operands["source_base"],
             operands["source_candidate"],
             operands["integration_attempt_id"],
             json.dumps(operands["integration_assignment"]),
             json.dumps(operands["workspace"]),
             operands["profile_name"], operands["profile_version"], revision,
             json.dumps(operands["target_source"]),
             operands["target_reference"], fixtures.NOW))
        return result_id

    def demoted(self, store):
        """A coordinator impersonating schema 5, by DROPPING what 5 never had.

        The same shape the Job store's migration fixtures use: an older store
        is this one minus exactly the objects the later step creates, so the
        impersonation cannot drift from the migration it is testing.
        """
        store.close()
        beside = sqlite3.connect(self.path, isolation_level=None)
        try:
            beside.execute("DROP INDEX managed_results_by_orchestration")
            beside.execute("DROP TABLE managed_publications")
            beside.execute("DROP TABLE managed_integration_phases")
            beside.execute("DROP TABLE managed_integration_results")
            beside.execute("UPDATE meta SET value = '5' WHERE key = ?",
                           ("schema_version",))
        finally:
            beside.close()


class TheUpgradeIsAnActSomebodyChooses(ManagedStorageCase):

    def test_an_older_store_is_refused_by_open_and_left_alone(self):
        """Opening is not consent to change somebody's coordinator. A writing
        process that migrated silently would upgrade a live deployment at
        whatever moment a command happened to run."""
        self.demoted(self.coordinator())
        before = os.stat(self.path).st_size
        with self.assertRaises(ContractRefusal) as caught:
            IntegrationStore.open(self.path, incarnation="c-2",
                                  clock=self.clock)
        self.assertIn("only through an explicit `upgrade_store`",
                      str(caught.exception))
        self.assertIn("Nothing was changed", str(caught.exception))
        self.assertEqual(os.stat(self.path).st_size, before)
        self.assertEqual(self.recorded_version(), "5")

    def test_the_upgrade_carries_it_forward_once(self):
        self.demoted(self.coordinator())
        answer = upgrade_store(self.path, incarnation="c-2", clock=self.clock)
        self.assertEqual(answer["from_version"], 5)
        self.assertEqual(answer["to_version"], schema.SCHEMA_VERSION)
        self.assertIs(answer["upgraded"], True)
        self.assertEqual(self.recorded_version(), str(schema.SCHEMA_VERSION))
        store = self.store(incarnation="c-3")
        self.assertEqual(store.schema_version, schema.SCHEMA_VERSION)
        self.assertTrue(store.managed_results_available())

    def test_upgrading_a_current_store_is_an_ordinary_answer(self):
        """Two operators doing the same sensible thing is not an error."""
        self.coordinator().close()
        answer = upgrade_store(self.path, incarnation="c-2", clock=self.clock)
        self.assertIs(answer["upgraded"], False)
        self.assertEqual(answer["from_version"], schema.SCHEMA_VERSION)

    def owned_shape(self, names):
        beside = sqlite3.connect(self.path, isolation_level=None)
        try:
            return {row[0]: row[1] for row in beside.execute(
                "SELECT name, sql FROM sqlite_master WHERE name IN "
                "(" + ", ".join("?" for _ in names) + ")", names)}
        finally:
            beside.close()

    def test_the_step_preserves_the_records_and_leases_it_found(self):
        """WHAT IT PRESERVES IT PRESERVES BY NOT TOUCHING -- and this compares
        the ROWS, not the definitions. A live lease held across the upgrade is
        the same lease afterwards, the entry mid-import is where it was, and
        the journal that records how they got there is byte-identical."""
        store, entry, lease = self.populated(managed=False)
        kept = ("targets", "entries", "leases", "integration_results",
                "operations")
        before = self.contents(kept)
        definitions = self.owned_shape(kept)
        self.assertTrue(before["leases"])
        self.assertTrue(before["entries"])
        self.assertTrue(before["operations"])
        # AND NOTHING MANAGED IS IN IT, which is what makes this an old store
        # rather than a new one with its tables removed.
        self.assertEqual(
            [row[0] for row in store._connection.execute(
                "SELECT operation_id FROM operations WHERE kind = ?",
                ("result.managed",))], [])
        self.demoted(store)
        upgrade_store(self.path, incarnation="c-2", clock=self.clock)
        self.assertEqual(self.contents(kept), before)
        self.assertEqual(self.owned_shape(kept), definitions)
        # AND THE LIVE LEASE IS STILL LIVE TO ITS PUBLIC READER, not merely
        # still present as bytes.
        reopened = self.store(incarnation="c-3")
        held = lease_of(reopened, "lease-1")
        self.assertEqual(held["state"], "live")
        self.assertEqual(held["entry_id"], "entry-1")
        self.assertEqual(
            [one["entry_id"] for one in entries_of(reopened, fixtures.TARGET)],
            ["entry-1"])
        self.assertEqual(target_of(reopened, fixtures.TARGET)["state"], "open")
        self.assertIsNotNone(entry)
        self.assertIsNotNone(lease)

    def test_a_concurrent_shape_change_is_caught_under_the_lock(self):
        """[P2] Review 2026-09-13T18:51:48Z: the preflight ran BEFORE the lock
        and only the VERSION was re-read inside it.

        A second connection dropping an index after `_adopt` returned and
        before `BEGIN IMMEDIATE` passed unnoticed: the upgrade reported
        success, stamped schema 6, and the next ordinary open refused the
        store it had just created. The version had not changed, so a version
        check could not see it.

        The interleaving is injected deterministically by patching the
        transaction boundary -- it is not a claim that ordinary recording
        drops indexes.
        """
        store, _entry, _lease = self.populated()
        self.demoted(store)
        original = IntegrationStore._adopt
        dropped = []

        def interleave(connection, path, accept=(schema.SCHEMA_VERSION,)):
            answer = original(connection, path, accept)
            if not dropped:
                # RIGHT AFTER THE PREFLIGHT RETURNS AND BEFORE THE LOCK IS
                # TAKEN, on a connection of its own -- which is exactly the
                # window the finding named. Measured, step 75: `sqlite3`'s
                # connection type is immutable, so the interleave is injected
                # at this boundary rather than at `execute`.
                dropped.append(True)
                beside = sqlite3.connect(self.path, isolation_level=None)
                try:
                    beside.execute("DROP INDEX results_by_submission")
                finally:
                    beside.close()
            return answer

        with mock.patch.object(IntegrationStore, "_adopt",
                               staticmethod(interleave)):
            with self.assertRaises(ContractRefusal) as caught:
                upgrade_store(self.path, incarnation="c-2", clock=self.clock)
        self.assertTrue(dropped)
        self.assertIn("results_by_submission", str(caught.exception))
        # AND NOTHING WAS STAMPED. The version is still 5 and the relation the
        # DDL would have created is absent, so the store is exactly the one
        # the interleaving left rather than a half-upgraded one.
        self.assertEqual(self.recorded_version(), "5")
        self.assertNotIn("managed_integration_results",
                         self.owned_shape(("managed_integration_results",)))

    def test_a_malformed_older_store_is_refused_before_any_mutation(self):
        """The ownership decision runs FIRST and in full. A store missing one
        of the objects schema 5 does have is not a schema-5 store, and this
        build does not carry it forward on the strength of its version stamp.
        """
        store = self.coordinator()
        self.demoted(store)
        beside = sqlite3.connect(self.path, isolation_level=None)
        try:
            beside.execute("DROP INDEX results_by_submission")
        finally:
            beside.close()
        with self.assertRaises(ContractRefusal) as caught:
            upgrade_store(self.path, incarnation="c-2", clock=self.clock)
        self.assertIn("results_by_submission", str(caught.exception))
        self.assertIn("Nothing was changed", str(caught.exception))
        self.assertEqual(self.recorded_version(), "5")

    def test_an_unknown_version_is_refused_by_both_openers(self):
        store = self.coordinator()
        store.close()
        beside = sqlite3.connect(self.path, isolation_level=None)
        try:
            beside.execute("UPDATE meta SET value = '4' WHERE key = ?",
                           ("schema_version",))
        finally:
            beside.close()
        with self.assertRaises(ContractRefusal):
            IntegrationStore.open(self.path, incarnation="c-2",
                                  clock=self.clock)
        with self.assertRaises(ContractRefusal) as caught:
            IntegrationStore.open_readonly(self.path, incarnation="c-2",
                                           clock=self.clock)
        self.assertIn("this build reads", str(caught.exception))

    def test_the_older_shape_is_derived_not_restated(self):
        """`shape_for(5)` is this build's own script minus exactly what the
        5 -> 6 step creates. A hand-written second expectation would be a
        second owner of the shape and would drift the first time either
        changed."""
        current, older = shape_for(schema.SCHEMA_VERSION), shape_for(5)
        self.assertEqual(sorted(key for key in current if key not in older),
                         [("index", "managed_results_by_orchestration"),
                          ("table", "managed_integration_phases"),
                          ("table", "managed_integration_results"),
                          ("table", "managed_publications")])
        self.assertEqual(READABLE_VERSIONS, (5, schema.SCHEMA_VERSION))


class AReadOnlyOpenUnderstandsBothShapes(ManagedStorageCase):

    def test_a_schema_five_coordinator_reads_and_is_not_upgraded(self):
        self.demoted(self.coordinator())
        reader = IntegrationStore.open_readonly(self.path, incarnation="c-2",
                                                clock=self.clock)
        self.addCleanup(reader.close)
        self.assertEqual(reader.schema_version, 5)
        self.assertFalse(reader.managed_results_available())
        self.assertEqual(self.recorded_version(), "5")

    def test_asking_an_older_store_for_managed_results_is_answered(self):
        """Absence is an ANSWER. A reader that discovered it as `no such
        table` mid-query would be reporting a fault instead."""
        self.demoted(self.coordinator())
        reader = IntegrationStore.open_readonly(self.path, incarnation="c-2",
                                                clock=self.clock)
        self.addCleanup(reader.close)
        with self.assertRaises(ContractRefusal) as caught:
            managed_result_of(reader, ORCHESTRATION)
        self.assertIn("holds no managed results", str(caught.exception))

    def test_a_current_coordinator_reads_as_current(self):
        self.coordinator().close()
        reader = IntegrationStore.open_readonly(self.path, incarnation="c-2",
                                                clock=self.clock)
        self.addCleanup(reader.close)
        self.assertEqual(reader.schema_version, schema.SCHEMA_VERSION)
        self.assertTrue(reader.managed_results_available())

    def test_a_read_only_handle_records_nothing(self):
        store = self.coordinator()
        recorded = self.record(store)
        reader = IntegrationStore.open_readonly(self.path, incarnation="c-2",
                                                clock=self.clock)
        self.addCleanup(reader.close)
        self.assertEqual(managed_result_of(reader, ORCHESTRATION), recorded)
        with self.assertRaises(ContractRefusal) as caught:
            record_managed_result(
                reader, submission(), orchestration_id=ORCHESTRATION,
                canonical_target_id=fixtures.TARGET,
                target_revision=REVISION)
        self.assertIn("performs no act", str(caught.exception))


class TheManagedResultGoesThroughItsOwnOwner(ManagedStorageCase):

    def test_a_preparation_is_retained_and_an_apply_follows_it_later(self):
        """THE ACCEPTED SEQUENCE, in three journalled acts rather than one.

        The result is created, the preparation is retained on its own -- a
        complete, readable custody record with one phase -- and the apply
        attaches AFTERWARDS without rewriting either. The earlier form could
        not express this at all: adding the apply changed the single immutable
        creation operation and collided with itself.
        """
        store = self.coordinator()
        created = record_managed_result(
            store, submission(), orchestration_id=ORCHESTRATION,
            canonical_target_id=fixtures.TARGET, target_revision=REVISION)
        self.assertEqual(created["phases"], {})
        self.assertEqual(created["state"], "preparing")
        prepared = attach_managed_phase(
            store, managed_result_id=ORCHESTRATION,
            task=self.account()["task"], result=self.account()["result"])
        self.assertEqual(sorted(prepared["phases"]), ["prepare"])
        applied = attach_managed_phase(
            store, managed_result_id=ORCHESTRATION,
            task=self.applying()["task"], result=self.applying()["result"])
        self.assertEqual(sorted(applied["phases"]), ["apply", "prepare"])
        self.assertEqual(applied["target_revision"], REVISION)
        # AND EVERY ACT REPLAYS EXACTLY, including the creation whose phase
        # set has grown underneath it.
        self.assertEqual(
            record_managed_result(
                store, submission(), orchestration_id=ORCHESTRATION,
                canonical_target_id=fixtures.TARGET,
                target_revision=REVISION),
            applied)
        self.assertEqual(
            attach_managed_phase(store, managed_result_id=ORCHESTRATION,
                                 task=self.account()["task"],
                                 result=self.account()["result"]),
            applied)

    def test_an_apply_naming_a_foreign_preparation_is_refused(self):
        """[P1] Sharing a parent row is not parentage. An apply naming another
        preparation, or other collected content, was accepted beside this
        result's actual preparation."""
        store = self.coordinator()
        self.record(store, phases=("prepare",))
        foreign = self.applying(parent={
            "execution_attempt_id": "prepare-attempt-elsewhere",
            "collected_digest": COLLECTED})
        with self.assertRaises(ContractRefusal) as caught:
            attach_managed_phase(store, managed_result_id=ORCHESTRATION,
                                 task=foreign["task"],
                                 result=foreign["result"])
        self.assertIn("the preparation retained beside it",
                      str(caught.exception))

    def test_an_apply_importing_other_content_is_refused(self):
        store = self.coordinator()
        self.record(store, phases=("prepare",))
        other = self.applying(parent={"execution_attempt_id": PREPARE,
                                      "collected_digest": "sha256:" + "9" * 64})
        with self.assertRaises(ContractRefusal) as caught:
            attach_managed_phase(store, managed_result_id=ORCHESTRATION,
                                 task=other["task"], result=other["result"])
        self.assertIn("its preparation collected", str(caught.exception))

    def test_an_apply_with_no_preparation_retained_is_refused(self):
        store = self.coordinator()
        record_managed_result(
            store, submission(), orchestration_id=ORCHESTRATION,
            canonical_target_id=fixtures.TARGET, target_revision=REVISION)
        with self.assertRaises(ContractRefusal) as caught:
            attach_managed_phase(store, managed_result_id=ORCHESTRATION,
                                 task=self.applying()["task"],
                                 result=self.applying()["result"])
        self.assertIn("retains no preparation", str(caught.exception))

    def test_one_result_carries_both_phases_at_one_snapshot(self):
        """[P1] Review 2026-09-13T18:51:48Z: the granularity was wrong.

        The first form made each PHASE the row, and the row carried the shared
        (target, proposal, revision) key -- so two phases of ONE result
        collided on it, and the case that appeared to show both working had
        quietly moved the apply to another target revision. That proves two
        snapshots; it proves nothing about a two-phase result.

        Here both phases belong to ONE result at ONE admitted revision, and no
        revision is invented to make them fit.
        """
        store = self.coordinator()
        recorded = self.record(store)
        self.assertEqual(sorted(recorded["phases"]), ["apply", "prepare"])
        self.assertEqual(recorded["target_revision"], REVISION)
        self.assertEqual(recorded["state"], "preparing")
        self.assertEqual(
            recorded["phases"]["prepare"]["result"],
            self.account()["result"])
        self.assertEqual(
            recorded["phases"]["apply"]["task"]["parent"][
                "execution_attempt_id"], PREPARE)
        self.assertEqual(managed_result_of(store, ORCHESTRATION), recorded)

    def test_the_result_uses_the_existing_result_state_vocabulary(self):
        """A managed result is a distinct admitted REPRESENTATION of the same
        thing, so an operator reading one state machine reads both -- and the
        relation carries the same relationships between state and content,
        including blocked/rejected history and publication before
        authorization."""
        store = self.coordinator()
        self.record(store)
        definition = store._connection.execute(
            "SELECT sql FROM sqlite_master WHERE name = ?",
            ("managed_integration_results",)).fetchone()[0]
        for state in schema.RESULT_STATES:
            self.assertIn(f"'{state}'", definition)
        for required in ("reason IS NOT NULL", "causal_observations",
                         "derived_proposal_id IS NOT NULL",
                         "evidence IS NOT NULL AND policy_generation",
                         "state = 'imported' AND entry_id IS NOT NULL"):
            self.assertIn(required, definition)

    def test_a_portable_result_carries_no_coordinator_location(self):
        """Managed fields hold content-addressed artifacts; a workspace path,
        an inode or a container id is exactly what must not travel in a result
        another machine will apply."""
        store = self.coordinator()
        self.record(store)
        row = store._connection.execute(
            "SELECT * FROM managed_integration_results").fetchone()
        for absent in ("workspace", "target_source", "profile_name",
                       "profile_version", "target_reference"):
            self.assertNotIn(absent, row.keys())

    def test_a_changed_immutable_task_operand_collides(self):
        """[P1] The attachment identity must carry the task it stores, so a
        request naming another harness, task or input digest collides instead
        of replaying and returning somebody else's task."""
        for member in ("harness_digest", "task_digest", "input_digest"):
            with self.subTest(member=member):
                case = type(self)(self._testMethodName)
                case.setUp()
                store = case.coordinator()
                first = case.record(store, phases=("prepare",))
                changed = case.account(
                    case.task(**{member: "sha256:" + "f" * 64}))
                with self.assertRaises(ContractRefusal) as caught:
                    attach_managed_phase(
                        store, managed_result_id=ORCHESTRATION,
                        task=changed["task"], result=changed["result"])
                self.assertEqual(caught.exception.code, "operation-collision")
                self.assertEqual(managed_result_of(store, ORCHESTRATION),
                                 first)
                case.doCleanups()

    def test_an_exact_repeat_replays(self):
        store = self.coordinator()
        first = self.record(store)
        self.assertEqual(self.record(store), first)
        self.assertEqual(
            store._connection.execute(
                "SELECT count(*) FROM managed_integration_phases"
            ).fetchone()[0], 2)

    def test_a_result_that_does_not_answer_its_task_is_refused(self):
        store = self.coordinator()
        record_managed_result(
            store, submission(), orchestration_id=ORCHESTRATION,
            canonical_target_id=fixtures.TARGET, target_revision=REVISION)
        broken = self.account()
        with self.assertRaises(ContractRefusal) as caught:
            attach_managed_phase(
                store, managed_result_id=ORCHESTRATION,
                task=broken["task"],
                result=dict(broken["result"],
                            orchestration_id="somebody-elses"))
        self.assertIn("answers the integration it was composed for",
                      str(caught.exception))

    def test_a_task_for_another_orchestration_is_refused(self):
        store = self.coordinator()
        record_managed_result(
            store, submission(), orchestration_id=ORCHESTRATION,
            canonical_target_id=fixtures.TARGET, target_revision=REVISION)
        foreign = self.account(
            self.task(orchestration_id="integration-capacity-2"))
        with self.assertRaises(ContractRefusal) as caught:
            attach_managed_phase(store, managed_result_id=ORCHESTRATION,
                                 task=foreign["task"],
                                 result=foreign["result"])
        self.assertIn("and the result is", str(caught.exception))

    def test_a_stored_report_is_re_adopted_on_the_way_out(self):
        """A ROW IS NOT A DOCUMENT UNTIL IT HAS BEEN OWNED."""
        store = self.coordinator()
        self.record(store)
        held = json.loads(store._connection.execute(
            "SELECT report FROM managed_integration_phases "
            "WHERE phase = 'prepare'").fetchone()[0])
        held["status"] = True
        store._connection.execute(
            "UPDATE managed_integration_phases SET report = ? "
            "WHERE phase = 'prepare'", (json.dumps(held),))
        with self.assertRaises(ContractRefusal) as caught:
            managed_result_of(store, ORCHESTRATION)
        self.assertIn("the integer status this manager measured",
                      str(caught.exception))

    def test_a_tampered_stored_task_is_refused_on_the_way_out(self):
        store = self.coordinator()
        self.record(store)
        held = json.loads(store._connection.execute(
            "SELECT task FROM managed_integration_phases "
            "WHERE phase = 'prepare'").fetchone()[0])
        held["execution_limits"]["boundaries"]["provider_turn"][
            "seconds"] = 7200
        store._connection.execute(
            "UPDATE managed_integration_phases SET task = ? "
            "WHERE phase = 'prepare'", (json.dumps(held),))
        with self.assertRaises(ContractRefusal) as caught:
            managed_result_of(store, ORCHESTRATION)
        self.assertIn("this Job's own resolution says", str(caught.exception))


class NeitherReaderAnswersADoubleRepresentation(ManagedStorageCase):
    """[P1] Review 2026-09-13T18:51:48Z: the writers checked and the readers
    did not.

    A store carrying one submission in both representations answered it
    normally from whichever side was asked. Reader ownership is the acceptance
    boundary -- a writer's care is not a property of the bytes a later reader
    finds -- so both read paths prove it, and BOTH write orders are driven
    through the actual writers.
    """

    def test_the_managed_reader_refuses_it(self):
        store = self.coordinator()
        self.record(store)
        self.legacy(store)
        with self.assertRaises(ContractRefusal) as caught:
            managed_result_of(store, ORCHESTRATION)
        self.assertIn("cannot be read as either", str(caught.exception))
        self.assertEqual(caught.exception.category, "integrity")

    def test_the_legacy_reader_refuses_it(self):
        store = self.coordinator()
        self.record(store)
        legacy_id = self.legacy(store)
        with self.assertRaises(ContractRefusal) as caught:
            result_of(store, legacy_id)
        self.assertIn("cannot be read as either", str(caught.exception))

    def test_the_managed_writer_refuses_a_key_the_legacy_side_holds(self):
        """Write order one, through the actual writer."""
        store = self.coordinator()
        self.legacy(store)
        with self.assertRaises(ContractRefusal) as caught:
            self.record(store)
        self.assertEqual(caught.exception.code, "operation-collision")
        self.assertIn("integration_results", str(caught.exception))

    def test_a_second_connection_sees_the_same_refusal(self):
        store = self.coordinator()
        self.record(store)
        self.legacy(store)
        second = IntegrationStore.open(self.path, incarnation="c-2",
                                       clock=self.clock)
        self.addCleanup(second.close)
        with self.assertRaises(ContractRefusal) as caught:
            managed_result_of(second, ORCHESTRATION)
        self.assertIn("cannot be read as either", str(caught.exception))

    def test_the_same_act_from_another_connection_replays(self):
        """Losing a race and repeating an act are different things, and the
        journal tells them apart."""
        store = self.coordinator()
        second = IntegrationStore.open(self.path, incarnation="c-2",
                                       clock=self.clock)
        self.addCleanup(second.close)
        first = record_managed_result(
            store, submission(), orchestration_id=ORCHESTRATION,
            canonical_target_id=fixtures.TARGET, target_revision=REVISION)
        self.assertEqual(
            record_managed_result(
                second, submission(), orchestration_id=ORCHESTRATION,
                canonical_target_id=fixtures.TARGET,
                target_revision=REVISION),
            first)
        self.assertEqual(
            store._connection.execute(
                "SELECT count(*) FROM managed_integration_results"
            ).fetchone()[0], 1)

    def test_an_ordinary_single_representation_reads_normally(self):
        """The guard refuses a DOUBLE representation and nothing else: a store
        holding one of each for DIFFERENT snapshots is ordinary."""
        store = self.coordinator()
        recorded = self.record(store)
        self.legacy(store, proposal="proposal-2", revision="d" * 40)
        # THE MANAGED READER ANSWERS NORMALLY. The legacy row is a different
        # snapshot, so nothing is doubly represented and the guard says
        # nothing about it.
        self.assertEqual(managed_result_of(store, ORCHESTRATION), recorded)
        # AND THE LEGACY READER IS NOT ASSERTED ON HERE. Measured, step 71:
        # `result_of` re-derives the identity AND asks the journal for the
        # committed act its state claims, which a hand-inserted row does not
        # have -- that reader's own chain proof is its own module's subject,
        # and driving it with a fabricated row would be asserting against a
        # fixture rather than against the rule this case is about.


class OneResultPerTargetSnapshotInEitherTable(ManagedStorageCase):
    """The key SQLite cannot enforce, because it spans two relations."""

    def test_the_shared_key_is_the_one_the_old_table_already_carries(self):
        self.assertEqual(schema.RESULT_KEY,
                         ("canonical_target_id", "source_proposal_id",
                          "target_revision"))

    def test_a_second_managed_result_for_one_snapshot_is_refused(self):
        store = self.coordinator()
        self.record(store)
        with self.assertRaises(ContractRefusal) as caught:
            record_managed_result(
                store, submission(),
                orchestration_id="integration-capacity-2",
                canonical_target_id=fixtures.TARGET,
                target_revision=REVISION)
        self.assertEqual(caught.exception.code, "operation-collision")
        self.assertIn("managed_integration_results", str(caught.exception))

    def test_another_snapshot_of_the_same_submission_is_ordinary(self):
        """A later target advance needs a NEW result from the same submission;
        it never mutates this one and it is not a collision."""
        store = self.coordinator()
        self.record(store)
        recorded = record_managed_result(
            store, submission(), orchestration_id="integration-capacity-2",
            canonical_target_id=fixtures.TARGET, target_revision="e" * 40)
        self.assertEqual(recorded["target_revision"], "e" * 40)
        self.assertEqual(recorded["phases"], {})


class TheQueueReadsAManagedCustodyAct(ManagedStorageCase):
    """Owner M164369 approved exactly one vocabulary member, and this is what
    it buys.

    `queue._history` walks the WHOLE journal and `_act` refuses a kind this
    build does not own, so before the amendment a single managed act made
    every queue reader on that store refuse -- lease, entry and target alike.
    `result.managed` is a custody kind now: named and positioned by the queue,
    and re-owned by `reconciliation.managed_result_of`, which is the rule the
    other six custody kinds are under.

    THESE CASES REPLACE THE TWO THAT MEASURED THE GAP. Those asserted the
    refusal that used to happen; asserting it now would pin the defect.
    """

    def test_the_queue_reads_normally_with_managed_acts_journalled(self):
        store, _entry, _lease = self.populated()
        held = lease_of(store, "lease-1")
        self.assertEqual(held["state"], "live")
        self.assertEqual(held["entry_id"], "entry-1")
        self.assertEqual(
            [one["entry_id"] for one in entries_of(store, fixtures.TARGET)],
            ["entry-1"])
        self.assertEqual(target_of(store, fixtures.TARGET)["state"], "open")

    def test_every_managed_act_is_read_including_the_attachments(self):
        """Creation AND each phase attachment commit under this one kind, so
        all three are walked. A vocabulary that admitted only the creation
        would refuse the moment a phase attached."""
        store, _entry, _lease = self.populated()
        journalled = sorted(
            row[0] for row in store._connection.execute(
                "SELECT operation_id FROM operations WHERE kind = ?",
                ("result.managed",)))
        stem = f"result.managed:{len(ORCHESTRATION)}:{ORCHESTRATION}"
        self.assertEqual(journalled,
                         [stem, stem + "/apply", stem + "/prepare"])
        self.assertEqual(lease_of(store, "lease-1")["state"], "live")

    def test_a_kind_this_build_does_not_own_still_refuses(self):
        """The amendment added ONE member and widened nothing else: a
        journal carrying an unknown kind is still a store this build cannot
        reason about entirely."""
        store, _entry, _lease = self.populated()
        seq = store._connection.execute(
            "SELECT COALESCE(MAX(seq), 0) + 1 FROM operations").fetchone()[0]
        store._connection.execute(
            "INSERT INTO operations (operation_id, kind, signature, state, "
            "result, settled_at, seq) VALUES (?, ?, ?, 'committed', ?, ?, ?)",
            ("result.invented:x", "result.invented",
             json.dumps({"kind": "result.invented", "operands": {}},
                        sort_keys=True, separators=(",", ":")),
             json.dumps({}), fixtures.NOW, seq))
        with self.assertRaises(ContractRefusal) as caught:
            lease_of(store, "lease-1")
        self.assertIn("which this build does not own", str(caught.exception))

    def test_a_malformed_managed_act_refuses(self):
        """Named is not re-owned: the queue positions this act and
        `managed_result_of` proves it. An act of the right kind at an
        identity that is not its own is refused by the queue's own rule."""
        store, _entry, _lease = self.populated()
        seq = store._connection.execute(
            "SELECT COALESCE(MAX(seq), 0) + 1 FROM operations").fetchone()[0]
        store._connection.execute(
            "INSERT INTO operations (operation_id, kind, signature, state, "
            "result, settled_at, seq) VALUES (?, ?, ?, 'committed', ?, ?, ?)",
            ("not-this-acts-identity", "result.managed",
             json.dumps({"kind": "result.managed", "operands": {}},
                        sort_keys=True, separators=(",", ":")),
             json.dumps({}), fixtures.NOW, seq))
        with self.assertRaises(ContractRefusal) as caught:
            lease_of(store, "lease-1")
        self.assertIn("is not that act's own identity", str(caught.exception))


class TheRowsAreBoundToTheJournalThatMadeThem(ManagedStorageCase):
    """[P1] Review 2026-09-13T19:07:44Z: the reader adopted current documents
    and returned current state, and nothing compared either with what was
    committed.

    Each of the three mutations below is individually well formed -- a valid
    digest, an absent row, a legal state with its required reason -- which is
    exactly why shape checking could not see them. What sees them is rebuilding
    the exact signed request from the rows as they stand and asking the journal
    whether that is what it recorded. An earlier valid write is not a current
    typed read.

    The rows are corrupted deliberately in a temporary store. No owner emits
    any of this; that is the point, because a coordinator this process did not
    write is the case a durable store exists to survive.
    """

    def prepared(self):
        store = self.coordinator()
        self.record(store, phases=("prepare",))
        return store

    def test_a_substituted_harness_digest_refuses_on_read_and_replay(self):
        store = self.prepared()
        held = json.loads(store._connection.execute(
            "SELECT task FROM managed_integration_phases "
            "WHERE phase = 'prepare'").fetchone()[0])
        held["harness_digest"] = "sha256:" + "f" * 64
        store._connection.execute(
            "UPDATE managed_integration_phases SET task = ? "
            "WHERE phase = 'prepare'", (json.dumps(held),))
        with self.assertRaises(ContractRefusal) as caught:
            managed_result_of(store, ORCHESTRATION)
        self.assertIn("these rows do not produce", str(caught.exception))
        # AND THE REPLAY TOO, because the witness reads through the same owner
        # rather than re-deriving a weaker rule beside it.
        account = self.account()
        with self.assertRaises(ContractRefusal) as replaying:
            attach_managed_phase(store, managed_result_id=ORCHESTRATION,
                                 task=account["task"],
                                 result=account["result"])
        self.assertIn("these rows do not produce", str(replaying.exception))

    def test_deleted_phase_rows_refuse_rather_than_answer_empty(self):
        store = self.prepared()
        store._connection.execute("DELETE FROM managed_integration_phases")
        with self.assertRaises(ContractRefusal) as caught:
            managed_result_of(store, ORCHESTRATION)
        self.assertIn("an act with nothing materialized",
                      str(caught.exception))
        self.assertIn(
            f"result.managed:{len(ORCHESTRATION)}:{ORCHESTRATION}/prepare",
            str(caught.exception))

    def test_an_unjournalled_state_transition_refuses(self):
        store = self.prepared()
        store._connection.execute(
            "UPDATE managed_integration_results SET state = 'held', "
            "reason = ? WHERE managed_result_id = ?",
            ("the target moved", ORCHESTRATION))
        with self.assertRaises(ContractRefusal) as caught:
            managed_result_of(store, ORCHESTRATION)
        self.assertIn("no committed act for", str(caught.exception))
        self.assertIn("transition chain", str(caught.exception))

    def test_a_changed_result_identity_refuses(self):
        """The creation act signs the submission identities too, so a row
        whose source proposal was edited no longer produces its own act."""
        store = self.prepared()
        store._connection.execute(
            "UPDATE managed_integration_results SET source_verdict_id = ? "
            "WHERE managed_result_id = ?", ("verdict-elsewhere",
                                            ORCHESTRATION))
        with self.assertRaises(ContractRefusal) as caught:
            managed_result_of(store, ORCHESTRATION)
        self.assertIn("these rows do not produce", str(caught.exception))

    def test_a_result_whose_own_act_is_gone_refuses(self):
        store = self.prepared()
        store._connection.execute(
            "DELETE FROM operations WHERE operation_id = ?",
            (f"result.managed:{len(ORCHESTRATION)}:{ORCHESTRATION}",))
        with self.assertRaises(ContractRefusal) as caught:
            managed_result_of(store, ORCHESTRATION)
        self.assertIn("nobody is recorded as having written",
                      str(caught.exception))

    def test_the_state_fields_are_carried_not_dropped(self):
        """A reader returning selected members could not report a held reason,
        a blocked record's retained observations or an authorization at all --
        so the whole result-history surface is answered."""
        store = self.prepared()
        held = managed_result_of(store, ORCHESTRATION)
        for member in ("reason", "prepared", "content_digest", "evidence",
                       "causal_observations", "observed_by",
                       "policy_generation", "derived_proposal_id",
                       "derived_result_id", "derived_result_digest",
                       "entry_id"):
            with self.subTest(member=member):
                self.assertIn(member, held)
                self.assertIsNone(held[member])
        self.assertEqual(held["state"], "preparing")


class TheUpgradeCarriesAGenuineLegacyResult(ResultCase):
    """[P2] Review 2026-09-13T19:07:44Z: the preservation fixture was not one.

    It recorded a MANAGED result and then demoted the store by dropping the
    managed tables while leaving that result's `result.managed` acts in an
    alleged schema-5 journal -- a store no version ever produced --  and
    `integration_results` was empty throughout. So the case compared an entry,
    a lease and table definitions, and proved nothing about carrying a real
    legacy result and its history across the step.

    THIS ONE DRIVES THE ACTUAL WRITER. `ResultCase` is `test_reconciliation`'s
    own fixture: real repositories, the real profile, the real submission
    owners. `prepare_result` produces a genuine `integration_results` row with
    its committed intent and outcome, and the case reads it back THROUGH
    `result_of` -- the public reader whose chain proof asks the journal for
    every act the row's state passed through -- on both sides of the upgrade.
    """

    @property
    def path(self):
        return os.path.join(self.root, "coordinator.sqlite3")

    def demoted(self):
        beside = sqlite3.connect(self.path, isolation_level=None)
        try:
            beside.execute("DROP INDEX managed_results_by_orchestration")
            beside.execute("DROP TABLE managed_publications")
            beside.execute("DROP TABLE managed_integration_phases")
            beside.execute("DROP TABLE managed_integration_results")
            beside.execute("UPDATE meta SET value = '5' WHERE key = ?",
                           ("schema_version",))
        finally:
            beside.close()

    def contents(self, tables):
        beside = sqlite3.connect(self.path, isolation_level=None)
        try:
            return {table: [tuple(row) for row in
                            beside.execute(f"SELECT * FROM {table}")]
                    for table in tables}
        finally:
            beside.close()

    def test_a_real_result_and_its_history_survive_the_upgrade(self):
        held = self.prepare()
        self.assertEqual(held["state"], "prepared")
        before = result_of(self.store, held["result_id"])
        kept = ("targets", "entries", "leases", "integration_results",
                "operations")
        rows = self.contents(kept)
        self.assertTrue(rows["integration_results"])
        self.assertTrue(rows["operations"])
        self.store.close()
        self.demoted()
        answer = upgrade_store(self.path, incarnation="c-2",
                               clock=lambda: fixtures.NOW)
        self.assertEqual(answer["from_version"], 5)
        self.assertIs(answer["upgraded"], True)
        # EVERY BYTE OF THE OLD SIDE, and the public reader's own verdict.
        self.assertEqual(self.contents(kept), rows)
        reopened = IntegrationStore.open(self.path, incarnation="c-3",
                                         clock=lambda: fixtures.NOW)
        self.addCleanup(reopened.close)
        self.assertEqual(result_of(reopened, held["result_id"]), before)
        self.assertEqual(reopened.schema_version, schema.SCHEMA_VERSION)
        self.assertTrue(reopened.managed_results_available())

    def test_the_legacy_writer_refuses_a_key_the_managed_side_holds(self):
        """THE REVERSE WRITE ORDER, through `prepare_result` itself rather
        than through its private claim. The managed side takes the snapshot
        first and the REAL legacy writer meets it.

        Both name the same submission the Authority actually holds; only the
        target revision is chosen, and it is a real object name from this
        fixture's own repository rather than an invented one.
        """
        # THE REVISION THE REAL WRITER WOULD DERIVE, asked of the same profile
        # it asks. Measured, step 91: naming the submission's own base instead
        # is refused earlier and for a different reason -- a reconciliation
        # answers a target that MOVED -- so this takes the target's actual
        # current revision rather than a convenient object name.
        revision = self.profile.revision(self.target, REFERENCE)
        record_managed_result(
            self.store, submission(source_proposal_id="proposal-b1"),
            orchestration_id=ORCHESTRATION, canonical_target_id=TARGET,
            target_revision=revision)
        with self.assertRaises(ContractRefusal) as caught:
            self.prepare()
        self.assertIn("managed_integration_results", str(caught.exception))
        self.assertIn("one submission has one result per target snapshot",
                      str(caught.exception))
        # MEASURED, step 86: `prepare_result`'s own intent act is where the
        # claim runs, and that boundary reports a refused precondition rather
        # than an operation collision. The CODE is the legacy writer's to
        # decide; what this case owns is that the claim is reached through the
        # real writer and names the other representation.
        self.assertEqual(caught.exception.category, "refused")


class AnIdentityIsNotAGrammar(ManagedStorageCase):
    """[P2] Review 2026-09-13T23:19:08Z: two composed-identity grammars, both
    silently narrowing what a result may be called.

    `_managed_witness` split the operation id on its first slash, so a result
    legitimately named `root/child` replayed as `root`. The reverse journal
    scan asked SQL for identities LIKE `<kind>:<id>/%`, and LIKE reads `_` as
    a wildcard and compares ASCII case-insensitively -- so `root_` claimed
    `rootA`'s attachments and `root` claimed `ROOT`'s, and two independent
    results refused each other.

    Both are gone: every act is signed over the result it belongs to, and that
    is what is read. These cases drive the public API only.
    """

    def named(self, store, orchestration, *, revision):
        record_managed_result(
            store, submission(source_proposal_id="proposal-" + revision),
            orchestration_id=orchestration,
            canonical_target_id=fixtures.TARGET, target_revision=revision)
        account = self.account(self.task(orchestration_id=orchestration,
                                         execution_attempt_id="prepare-"
                                         + orchestration))
        return attach_managed_phase(store, managed_result_id=orchestration,
                                    task=account["task"],
                                    result=account["result"])

    def test_a_result_whose_name_carries_a_slash_replays_exactly(self):
        store = self.coordinator()
        held = self.named(store, "root/child", revision="a" * 40)
        self.assertEqual(held["managed_result_id"], "root/child")
        self.assertEqual(sorted(held["phases"]), ["prepare"])
        # THE EXACT RETRY OF BOTH ACTS, each answering about THIS result.
        self.assertEqual(
            record_managed_result(
                store, submission(source_proposal_id="proposal-" + "a" * 40),
                orchestration_id="root/child",
                canonical_target_id=fixtures.TARGET,
                target_revision="a" * 40),
            held)
        account = self.account(self.task(
            orchestration_id="root/child",
            execution_attempt_id="prepare-root/child"))
        self.assertEqual(
            attach_managed_phase(store, managed_result_id="root/child",
                                 task=account["task"],
                                 result=account["result"]),
            held)
        self.assertEqual(managed_result_of(store, "root/child"), held)

    def test_neighbouring_names_do_not_claim_each_others_attachments(self):
        """`_` is a LIKE wildcard and LIKE is case-insensitive, so these four
        names are the ones a pattern conflates. Each answers about itself."""
        store = self.coordinator()
        held = {}
        for index, name in enumerate(("root", "root_", "rootA", "ROOT")):
            held[name] = self.named(store, name,
                                    revision=str(index) * 40)
        for name, answer in held.items():
            with self.subTest(orchestration=name):
                self.assertEqual(managed_result_of(store, name), answer)
                self.assertEqual(sorted(answer["phases"]), ["prepare"])
                self.assertEqual(
                    answer["phases"]["prepare"]["task"][
                        "execution_attempt_id"], "prepare-" + name)

    def test_deletion_is_still_detected_for_the_right_result(self):
        """The narrowed grammar is gone and what it was there FOR is not: a
        committed attachment with nothing materialized is still caught, and
        for the result that actually owns it."""
        store = self.coordinator()
        self.named(store, "root", revision="0" * 40)
        self.named(store, "root_", revision="1" * 40)
        store._connection.execute(
            "DELETE FROM managed_integration_phases "
            "WHERE managed_result_id = ?", ("root_",))
        with self.assertRaises(ContractRefusal) as caught:
            managed_result_of(store, "root_")
        self.assertIn("an act with nothing materialized",
                      str(caught.exception))
        # AND THE NEIGHBOUR IS UNAFFECTED, which the pattern could not have
        # promised either way.
        self.assertEqual(sorted(managed_result_of(store, "root")["phases"]),
                         ["prepare"])


class TheTwoActFamiliesCannotMeet(ManagedStorageCase):
    """[P2] Review 2026-09-13T23:28:58Z: two different acts, one identity.

    Creating a result named `root/prepare` and attaching the preparation of a
    result named `root` both composed `result.managed:root/prepare`. Two acts
    about two different results shared one journal identity, so each collided
    with the other in whichever order they arrived -- at different target
    snapshots, with nothing else in common.

    Forbidding a slash in an orchestration id would be the narrowed grammar the
    previous round already rejected. Both identities carry the decimal length
    of the result id instead, which makes the two families disjoint: for a
    creation to equal an attachment the digits before the first colon must
    match, and then the ids they describe differ in length by the phase.
    """

    def create(self, store, orchestration, revision):
        return record_managed_result(
            store, submission(source_proposal_id="proposal-" + revision),
            orchestration_id=orchestration,
            canonical_target_id=fixtures.TARGET, target_revision=revision)

    def attach(self, store, orchestration, phase="prepare"):
        account = self.account(self.task(
            orchestration_id=orchestration,
            execution_attempt_id="prepare-" + orchestration))
        return attach_managed_phase(store, managed_result_id=orchestration,
                                    task=account["task"],
                                    result=account["result"])

    def test_a_creation_and_an_attachment_that_used_to_collide(self):
        """Both orders, both surviving, at different snapshots."""
        store = self.coordinator()
        self.create(store, "root", "0" * 40)
        attached = self.attach(store, "root")
        created = self.create(store, "root/prepare", "1" * 40)
        self.assertEqual(sorted(attached["phases"]), ["prepare"])
        self.assertEqual(created["managed_result_id"], "root/prepare")
        self.assertEqual(created["phases"], {})
        # AND EACH STILL ANSWERS ABOUT ITSELF afterwards.
        self.assertEqual(managed_result_of(store, "root"), attached)
        self.assertEqual(managed_result_of(store, "root/prepare"), created)

    def test_the_other_order_survives_too(self):
        store = self.coordinator()
        self.create(store, "root/prepare", "1" * 40)
        self.create(store, "root", "0" * 40)
        attached = self.attach(store, "root")
        self.assertEqual(sorted(attached["phases"]), ["prepare"])
        self.assertEqual(managed_result_of(store, "root/prepare")["phases"],
                         {})

    def test_the_identities_are_disjoint_by_construction(self):
        store = self.coordinator()
        self.create(store, "root", "0" * 40)
        self.attach(store, "root")
        self.create(store, "root/prepare", "1" * 40)
        journalled = sorted(
            row[0] for row in store._connection.execute(
                "SELECT operation_id FROM operations WHERE kind = ?",
                ("result.managed",)))
        self.assertEqual(journalled,
                         ["result.managed:12:root/prepare",
                          "result.managed:4:root",
                          "result.managed:4:root/prepare"])
        self.assertEqual(len(set(journalled)), 3)

    def test_a_renamed_act_and_pointer_do_not_pass_together(self):
        """[P2] The reader followed whatever identity the row pointed at, so
        renaming the operation row and the pointer together left the original
        signature valid and the read passed. A row does not get to say which
        act made it."""
        store = self.coordinator()
        self.create(store, "root", "0" * 40)
        store._connection.execute(
            "UPDATE operations SET operation_id = ? WHERE operation_id = ?",
            ("result.managed:renamed", "result.managed:4:root"))
        store._connection.execute(
            "UPDATE managed_integration_results SET operation_id = ? "
            "WHERE managed_result_id = ?", ("result.managed:renamed", "root"))
        with self.assertRaises(ContractRefusal) as caught:
            managed_result_of(store, "root")
        self.assertIn("its own creation identity", str(caught.exception))

    def test_a_renamed_phase_act_and_pointer_do_not_pass_together(self):
        store = self.coordinator()
        self.create(store, "root", "0" * 40)
        self.attach(store, "root")
        store._connection.execute(
            "UPDATE operations SET operation_id = ? WHERE operation_id = ?",
            ("result.managed:4:root/renamed", "result.managed:4:root/prepare"))
        store._connection.execute(
            "UPDATE managed_integration_phases SET operation_id = ? "
            "WHERE managed_result_id = ?",
            ("result.managed:4:root/renamed", "root"))
        with self.assertRaises(ContractRefusal) as caught:
            managed_result_of(store, "root")
        self.assertIn("its own attachment identity", str(caught.exception))


class ThePublicWritersOverlapAtTheTransactionBoundary(ResultCase):
    """Both real writers, one holding its transaction while the other reaches
    `BEGIN IMMEDIATE`.

    Review 2026-09-13T23:37:46Z: my previous version described its holder as
    "the legacy writer's own claim" and it was not `prepare_result` -- it was
    that function's private claim plus an INSERT I wrote. The reviewer
    supplied a working proof rather than another reconstruction cycle, and
    this is it, adapted: `prepare_result` and `record_managed_result`, each on
    its own connection, in both orders.

    WHAT IS OBSERVED IS THE TRANSACTION BOUNDARY, not elapsed time. The holder
    pauses inside its own write transaction -- `_now` runs while `_pending` is
    set and the connection is in a transaction -- and the other side's
    `BEGIN IMMEDIATE` is seen through a trace callback. The recorded order is
    asserted: holder inside its write, THEN the other reaching its begin. That
    is an ordering claim about two real writers, and it deliberately does not
    claim to have measured how long SQLite blocked.
    """

    def overlap(self, first):
        import threading
        from baton_v12.integration import IntegrationStore as Store
        path = os.path.join(self.root, "coordinator.sqlite3")
        revision = self.profile.revision(self.target, REFERENCE)
        paused, attempted = threading.Event(), threading.Event()
        answers, trace = {}, []

        def instrument(handle, side):
            if side == first:
                original, once = handle._now, []

                def hold():
                    if not once and handle._pending is not None:
                        once.append(True)
                        self.assertTrue(handle._connection.in_transaction)
                        trace.append(side + ":inside-write")
                        paused.set()
                        self.assertTrue(
                            attempted.wait(5),
                            "the other public writer never reached BEGIN")
                    return original()

                handle._now = hold
            else:
                def observe(statement):
                    if statement.strip().upper() == "BEGIN IMMEDIATE":
                        trace.append(side + ":begin-write")
                        attempted.set()

                handle._connection.set_trace_callback(observe)

        def managed_side():
            handle = None
            try:
                handle = Store.open(path, incarnation="independent-managed",
                                    clock=lambda: fixtures.NOW)
                instrument(handle, "managed")
                if first != "managed":
                    self.assertTrue(paused.wait(5),
                                    "legacy never entered its transaction")

                def create():
                    return record_managed_result(
                        handle, submission(source_proposal_id="proposal-b1"),
                        orchestration_id="independent-root",
                        canonical_target_id=TARGET,
                        target_revision=revision)

                answers["managed"] = create()
                # THE WINNER'S OWN REPLAY AND READ, from its own connection.
                self.assertEqual(create(), answers["managed"])
                self.assertEqual(
                    managed_result_of(handle, "independent-root"),
                    answers["managed"])
            except BaseException as raised:
                answers["managed"] = raised
            finally:
                if handle is not None:
                    handle.close()

        instrument(self.store, "legacy")
        thread = threading.Thread(target=managed_side)
        thread.start()
        try:
            if first == "managed":
                self.assertTrue(paused.wait(5),
                                "managed never entered its transaction")
            try:
                answers["legacy"] = self.prepare()
            except ContractRefusal as refused:
                answers["legacy"] = refused
        finally:
            attempted.set()
            thread.join(20)
        self.assertFalse(thread.is_alive())
        other = "legacy" if first == "managed" else "managed"
        self.assertEqual(trace[:2],
                         [first + ":inside-write", other + ":begin-write"])
        self.assertIsInstance(answers[first], dict, str(answers[first]))
        self.assertIsInstance(answers[other], ContractRefusal,
                              str(answers[other]))
        self.assertIn("one submission has one result per target snapshot",
                      str(answers[other]))
        if first == "legacy":
            self.assertEqual(self.prepare(), answers["legacy"])
            self.assertEqual(
                result_of(self.store, answers["legacy"]["result_id"]),
                answers["legacy"])
        # AND EXACTLY ONE RESULT EXISTS, on the winner's side only.
        self.assertEqual(
            [self.store._connection.execute(
                "SELECT count(*) FROM " + table).fetchone()[0]
             for table in ("integration_results",
                           "managed_integration_results")],
            [1, 0] if first == "legacy" else [0, 1])

    def test_legacy_holds_before_the_managed_write_attempt(self):
        self.overlap("legacy")

    def test_managed_holds_before_the_legacy_write_attempt(self):
        self.overlap("managed")


if __name__ == "__main__":                                  # pragma: no cover
    unittest.main()


# -- W161230 slice2 A.4: adopting what a preparation actually collected -------

_WORKER = pathlib.Path(__file__).resolve().parents[3] / "worker"
if str(_WORKER) not in sys.path:
    sys.path.insert(0, str(_WORKER))

import reconciliation_task as worker_task                  # noqa: E402

from baton_v12.contracts import digest as document_digest  # noqa: E402
from baton_v12.contracts import digest_of_bytes            # noqa: E402
from baton_v12.integration import managed_execution as managed_owner  # noqa: E402
from baton_v12.integration import reconciliation as adoption  # noqa: E402
from baton_v12.job_manager import integration_capacity as capacity_owner  # noqa: E402

from ..job_manager.test_managed_integration_capacity import CapacityCase  # noqa: E402
from ..job_manager import fixtures as job_fixtures        # noqa: E402
from ..manager.test_output import OutputCase              # noqa: E402
from ..manager.test_output import sealed as sealed_manifest  # noqa: E402


def _declared_output(name, path):
    """One declared output, with the shared constraints the fixture uses."""
    return {"name": name, "type": "directory-result", "path": path,
            "required": True,
            "constraints": {"max_bytes": 1048576, "max_entries": 100,
                            "allowed_media_types": ["application/json",
                                                    "application/octet-stream",
                                                    "text/plain"],
                            "link_policy": "forbid",
                            "validator_digest": None}}


def _answered_output(name, body, artifact_id, *, path="report.json",
                     artifact=None):
    """A `present` output whose artifact IS the bytes it carries.

    The shared `OutputCase.present` fixture digests a constant, which is fine
    for cases about freezing and useless for one about adopting content: the
    whole question here is whether the bytes a later reader is handed are the
    ones this manager measured, and a constant answers it in advance.
    """
    entries = [{"path": path, "bytes": len(body),
                "content_digest": digest_of_bytes(body)}]
    return {"name": name, "type": "directory-result", "status": "present",
            "result_metadata": {},
            "content_manifest": {"entries": entries, "entry_count": 1,
                                 "total_bytes": len(body),
                                 "tree_digest": document_digest(entries)},
            "artifact": artifact or {
                "artifact_id": artifact_id, "media_type": "application/json",
                "bytes": len(body), "content_digest": digest_of_bytes(body),
                "locator": "file:///var/lib/baton/" + artifact_id}}


class ThePreparationIsAdoptedFromWhatItCollected(CapacityCase):
    """W161230 CHECKPOINT A.4 -- the collected preparation, taken up.

    EVERY OWNER IN THIS PATH IS THE REAL ONE. The Job store admits and ends a
    real capacity membership; the Worker Manager really freezes a sealed
    result against a retained declaration and really takes it into custody
    through `request_intake`; the coordinator is a real `IntegrationStore`
    with an activated target; and THE REPORT IS COMPOSED BY THE WORKER'S OWN
    `reconciliation_task.compose_report` over real measured trees, so what
    adoption consumes is what the workload actually emits rather than a
    document this file wrote to match.

    WHAT IT DOES NOT DO, deliberately: no byte is applied, no entry is
    settled, no receipt is dispatched and no verdict is composed. Those are
    slice3's.
    """

    TARGET = fixtures.TARGET
    REPORT_PATH = "report.json"

    # -- the declaration a preparation actually answers ---------------------

    def published_declaration(self):
        return sealed_manifest(dict(
            OutputCase.published(),
            outputs=[_declared_output(adoption.PREPARATION_REPORT_OUTPUT,
                                      "workspace/report"),
                     _declared_output(adoption.PREPARED_CANDIDATE_OUTPUT,
                                      "workspace/candidate")]))

    # -- the request this orchestration committed ---------------------------

    HARNESS = "sha256:" + "7" * 64

    def request(self, **changed):
        self.owners()
        # THE LINE AND PROPOSAL THE COORDINATOR'S OWN ENTRY RETAINS. The
        # shared capacity fixture's request named a line nobody had an
        # accepted candidate on, which was harmless only while the submission
        # was a caller operand; now that adoption RESOLVES the submission from
        # the entry, a request naming another line is exactly what refuses.
        held = {"canonical_target_id": self.TARGET,
                "line_id": "line-1", "source_proposal_id": "proposal-1",
                "harness_digest": self.HARNESS}
        held.update(changed)
        return super().request(**held)

    def plan(self, stage, **changed):
        held = super().plan(stage, **changed)
        for one in held:
            one["task_digest"] = "sha256:" + "a" * 64
        return held

    # -- what the worker really produced ------------------------------------

    def trees(self):
        """Three real measured states, so the report's content is measured
        rather than asserted."""
        held = {}
        for index, name in enumerate(("combined", "base", "isolated")):
            place = os.path.join(self.root, "state-" + name)
            os.makedirs(place, exist_ok=True)
            with open(os.path.join(place, "harness.py"), "wb") as writing:
                writing.write(b"# " + name.encode() + b"\n")
            held[name] = {"revision": chr(ord("a") + index) * 40,
                          "path": place}
        return held

    def report_body(self, **changed):
        """THE WORKLOAD'S OWN REPORT, composed by the workload's own composer."""
        request = dict(self.request())
        request["harness_digest"] = self.HARNESS
        held = worker_task.compose_report(
            request, self.trees(),
            [{"name": one, "status": 0, "harness_added": one == "base",
              "output": ""} for one in request["commands"]],
            [], None, harness_measured=self.HARNESS)
        held.update(changed)
        return json.dumps(held, sort_keys=True).encode("utf-8")

    def outputs(self, body=None, **changed):
        body = self.report_body() if body is None else body
        held = {"report": _answered_output(
                    adoption.PREPARATION_REPORT_OUTPUT, body,
                    "artifact-report", path=self.REPORT_PATH),
                "candidate": _answered_output(
                    adoption.PREPARED_CANDIDATE_OUTPUT, b'{"candidate": 1}',
                    "artifact-candidate", path="candidate.json")}
        held.update(changed)
        return [held["report"], held["candidate"]]

    # -- the task the phase ran under ---------------------------------------

    def task(self, store, **changed):
        request = self.request()
        held = {"phase": "prepare", "orchestration_id": self.ORCHESTRATION,
                "canonical_target_id": self.TARGET,
                "execution_attempt_id": "prepare-attempt-1",
                "assignment": self.claim_of("prepare-attempt-1"),
                "task_digest": "sha256:" + "a" * 64,
                "input_digest": request["input_digest"],
                "harness_digest": request["harness_digest"],
                "execution_limits": request["execution_limits"],
                "commands": request["commands"]}
        held.update(changed)
        return managed_owner.managed_task(**held)

    # -- the whole ended preparation ----------------------------------------

    def ended(self, *, body=None, outputs=None, outcome="succeeded",
              request=None):
        request = self.request() if request is None else request
        store, stage, allocation, answer = self.registered()
        # THE INTENT THE ADOPTION IS PROVED AGAINST, committed by its own
        # owner before anything ran -- the request digest an adopted result
        # must match is the one THIS decided.
        capacity_owner.record_preparation_intent(
            store, orchestration_id=self.ORCHESTRATION,
            root_assignment_id=allocation["assignment_id"],
            authority_uuid=job_fixtures.UUID, request=request,
            execution_work_id=self.EXECUTION_WORK,
            execution_route="integration-preparation",
            plan=self.plan(stage))
        self.admit("prepare", "prepare-attempt-1", "prepare-offer-1", store)
        self.collected("prepare-attempt-1",
                       outputs=self.outputs(body) if outputs is None
                       else outputs)
        self.destroyed("prepare-attempt-1")
        capacity_owner.end_integration_execution(
            store, self._control, execution_attempt_id="prepare-attempt-1",
            outcome=outcome, exclusion="runtime-destroyed")
        return store

    def adopt(self, store, *, body=None, **changed):
        held = {"orchestration_id": self.ORCHESTRATION,
                "request": self.request(), "task": self.task(store),
                "report_body": self.report_body() if body is None else body}
        held.update(changed)
        return adoption.adopt_prepared_candidate(
            self.coordinated(), store, self._control, **held)

    # -- what adoption must establish ---------------------------------------

    def test_the_collected_preparation_is_adopted_end_to_end(self):
        store = self.ended()
        held = self.adopt(store)
        self.assertEqual(sorted(held),
                         sorted(adoption.PREPARED_CANDIDATE_MEMBERS))
        self.assertEqual(held["schema"], adoption.PREPARED_CANDIDATE_SCHEMA)
        self.assertEqual(held["execution_attempt_id"], "prepare-attempt-1")
        self.assertEqual(held["assignment"],
                         self.claim_of("prepare-attempt-1"))
        self.assertEqual(held["harness_digest"], self.HARNESS)
        self.assertEqual(held["source"], self.request()["source"])
        # THE MANAGER'S OWN THREE ANSWERS, composed through the owner that
        # decides what a report may carry rather than copied out of the JSON.
        self.assertEqual(held["report"]["kind"], "measured")
        self.assertEqual(held["report"]["status"], 0)
        self.assertEqual([one["name"] for one in held["report"]["completed"]],
                         self.request()["commands"])
        self.assertEqual(held["report"]["not_run"], [])
        # AND THE CANDIDATE IS NAMED BY MEASUREMENT, not by a path.
        self.assertEqual(held["candidate"]["artifact_id"],
                         "artifact-candidate")
        self.assertEqual(held["candidate"]["content_digest"],
                         digest_of_bytes(b'{"candidate": 1}'))
        self.assertEqual(held["candidate"]["bytes"], len(b'{"candidate": 1}'))
        self.assertEqual(held["collected"]["custody"], "accepted")

    def test_the_phase_is_retained_through_its_own_owner(self):
        """The adoption does not write rows: it drives `record_managed_result`
        and `attach_managed_phase`, so the retained account is the one that
        owner's reader answers with."""
        store = self.ended()
        held = self.adopt(store)
        retained = managed_result_of(self.coordinated(),
                                     held["managed_result_id"])
        self.assertEqual(retained["orchestration_id"], self.ORCHESTRATION)
        self.assertEqual(retained["canonical_target_id"], self.TARGET)
        self.assertEqual(sorted(retained["phases"]), ["prepare"])
        phase = retained["phases"]["prepare"]
        self.assertEqual(phase["task"]["execution_attempt_id"],
                         "prepare-attempt-1")
        self.assertEqual(phase["result"]["report"], held["report"])
        self.assertEqual(phase["result"]["collected"]["manifest_digest"],
                         held["collected"]["manifest_digest"])
        # AN EXACT REPEAT REPLAYS rather than colliding or doubling the phase.
        self.assertEqual(self.adopt(store), held)
        self.assertEqual(len(managed_result_of(
            self.coordinated(), held["managed_result_id"])["phases"]), 1)

    def test_a_foreign_task_digest_refuses_and_writes_nothing(self):
        """Review [P2]: the task's own identity was not compared to the
        membership admitted for it, so a substituted digest was journalled
        into the preparation phase beside a correct account of everything
        else. The capacity owner already retained it; this is the comparison.

        AND THE REFUSAL COSTS NOTHING. It happens before either coordinator
        write, so no result row exists afterwards, no phase is attached, and
        the one-per-target-snapshot slot is unconsumed -- which is proved by
        the correct adoption still succeeding right after.
        """
        store = self.ended()
        foreign = self.task(store, task_digest="sha256:" + "f" * 64)
        with self.assertRaises(ContractRefusal) as caught:
            self.adopt(store, task=foreign)
        self.assertIn("the membership admitted for it registered",
                      str(caught.exception))
        self.assertNoManagedResult()
        # AND THE SLOT IS STILL FREE: the honest adoption still lands.
        held = self.adopt(store)
        self.assertEqual(
            managed_result_of(self.coordinated(),
                              held["managed_result_id"])["phases"]["prepare"]
            ["task"]["task_digest"], self.task(store)["task_digest"])

    def test_the_submission_is_resolved_from_owners_not_supplied(self):
        """Review [P1]: the submission was a caller operand handed straight to
        `record_managed_result`, which validates its shape and journals it --
        so changing `source_candidate` alone produced a durable account naming
        a candidate this preparation never prepared.

        THE CORRECTION IS STRUCTURAL: there is no submission operand, so there
        is nothing left to substitute. This asserts where each member actually
        came from -- the committed request for the two Git objects and the
        shared Job/line/proposal identities, the coordinator's own accepted
        entry for the checkpoint, verdict and result facts.
        """
        import inspect

        self.assertNotIn(
            "submission",
            inspect.signature(adoption.adopt_prepared_candidate).parameters)
        store = self.ended()
        held = self.adopt(store)
        recorded = managed_result_of(self.coordinated(),
                                     held["managed_result_id"])
        request = self.request()
        [entry] = [one for one in entries_of(self.coordinated(), self.TARGET)
                   if one["proposal_id"] == request["source_proposal_id"]]
        # FROM THE REQUEST: the Git objects, which the entry carries only as
        # CONTENT digests -- a different language for the same candidate.
        self.assertEqual(recorded["source_base"], request["source"]["base"])
        self.assertEqual(recorded["source_candidate"],
                         request["source"]["candidate"])
        self.assertNotEqual(recorded["source_candidate"],
                            entry["candidate_digest"])
        # FROM THE COORDINATOR'S OWN ENTRY: everything no request carries.
        self.assertEqual(recorded["source_checkpoint_id"],
                         entry["checkpoint_id"])
        self.assertEqual(recorded["source_verdict_id"], entry["verdict_id"])
        self.assertEqual(recorded["source_result_id"], entry["result_id"])
        self.assertEqual(recorded["source_result_digest"],
                         entry["result_digest"])
        self.assertEqual(recorded["source_checkpoint_digest"],
                         entry["checkpoint_digest"])
        # AND THE SOURCE WORK IS NOT THIS PREPARATION'S CHILD WORK.
        self.assertEqual(recorded["work_id"], entry["work_id"])
        self.assertNotEqual(recorded["work_id"], self.EXECUTION_WORK)

    def test_a_request_naming_another_candidates_line_refuses(self):
        """The substitution the caller operand used to allow now has to go
        through the REQUEST -- and the request is pinned to the digest the
        intent committed before the child Work existed, so it refuses at the
        intent before it ever reaches the entry."""
        store = self.ended()
        with self.assertRaises(ContractRefusal) as caught:
            self.adopt(store, request=self.request(line_id="line-other"))
        self.assertIn("the committed intent decided", str(caught.exception))
        self.assertNoManagedResult()

    def test_a_proposal_this_coordinator_never_accepted_refuses(self):
        """And when the intent itself was decided for a proposal the
        coordinator holds no accepted entry for, adoption refuses rather than
        attributing the preparation to nothing."""
        store = self.ended(request=self.request(
            source_proposal_id="proposal-nobody-accepted"))
        with self.assertRaises(ContractRefusal) as caught:
            self.adopt(store, request=self.request(
                source_proposal_id="proposal-nobody-accepted"))
        self.assertIn("entries for proposal", str(caught.exception))
        self.assertNoManagedResult()

    def assertNoManagedResult(self):
        """No result row, no phase row, and no consumed uniqueness slot."""
        held = self.coordinated()
        for table in ("managed_integration_results",
                      "managed_integration_phases"):
            self.assertEqual(
                held._connection.execute(
                    f"SELECT COUNT(*) FROM {table}").fetchone()[0], 0, table)

    def test_the_report_bytes_are_weighed_against_custody(self):
        """A JSON report is not trusted custody. What makes this document the
        preparation's report is that its bytes digest to the artifact this
        manager froze and took in, at the length it recorded."""
        store = self.ended()
        tampered = self.report_body(tag=None, status=0)
        tampered = json.dumps(dict(json.loads(tampered), status=0,
                                   note="added after measurement"),
                              sort_keys=True).encode("utf-8")
        with self.assertRaises(ContractRefusal) as caught:
            self.adopt(store, body=tampered)
        self.assertIn("bytes and this manager measured", str(caught.exception))
        # AND A DOCUMENT OF THE RIGHT LENGTH BUT OTHER CONTENT is refused on
        # the digest rather than accepted for weighing the same.
        original = self.report_body()
        swapped = bytearray(original)
        swapped[-2] = ord(" ") if swapped[-2] != ord(" ") else ord("\t")
        with self.assertRaises(ContractRefusal) as digested:
            self.adopt(store, body=bytes(swapped))
        self.assertIn("took", str(digested.exception))

    def test_a_preparation_that_ran_another_harness_refuses(self):
        """The workload reports the harness it was ASKED for and the harness
        it actually pinned and ran, and deliberately does not compare them.
        Comparing them is this owner's act: a different harness measures a
        different test, and the accepted evidence authorized one of them."""
        other = "sha256:" + "8" * 64
        body = self.report_body(harness_measured_digest=other)
        store = self.ended(body=body)
        with self.assertRaises(ContractRefusal) as caught:
            self.adopt(store, body=body)
        self.assertIn("measures a different test", str(caught.exception))

    def test_a_report_about_another_snapshot_refuses(self):
        source = dict(self.request()["source"], candidate="e" * 40)
        body = self.report_body(source=source)
        store = self.ended(body=body)
        with self.assertRaises(ContractRefusal) as caught:
            self.adopt(store, body=body)
        self.assertIn("preparation is about the snapshot",
                      str(caught.exception))

    def test_a_request_the_intent_did_not_decide_refuses(self):
        store = self.ended()
        with self.assertRaises(ContractRefusal) as caught:
            self.adopt(store, request=self.request(
                harness_digest="sha256:" + "6" * 64))
        self.assertIn("the committed intent decided", str(caught.exception))

    def test_a_preparation_still_running_is_not_adopted(self):
        """A preparation is adopted after it ENDED. An execution that may
        still be writing has produced nothing final to take up."""
        store, stage, allocation, answer = self.registered()
        capacity_owner.record_preparation_intent(
            store, orchestration_id=self.ORCHESTRATION,
            root_assignment_id=allocation["assignment_id"],
            authority_uuid=job_fixtures.UUID, request=self.request(),
            execution_work_id=self.EXECUTION_WORK,
            execution_route="integration-preparation",
            plan=self.plan(stage))
        self.admit("prepare", "prepare-attempt-1", "prepare-offer-1", store)
        with self.assertRaises(ContractRefusal) as caught:
            self.adopt(store)
        self.assertIn("adopted after it ended", str(caught.exception))

    def test_a_failed_preparation_contributes_no_candidate(self):
        store = self.ended(outcome="failed")
        with self.assertRaises(ContractRefusal) as caught:
            self.adopt(store)
        self.assertIn("no importable candidate", str(caught.exception))

    def test_the_root_is_still_held_and_the_apply_still_planned(self):
        """Slice2 finishes with the preparation ended, the apply NOT run and
        the ONE root still held -- so adoption asserts that state rather than
        assuming it, and refuses when the root has begun ending."""
        store = self.ended()
        self.adopt(store)
        held = capacity_owner.integration_capacity_of(store,
                                                      self.ORCHESTRATION)
        self.assertEqual(held["root"]["lifecycle"], "open")
        [applying] = [one for one in held["members"]
                      if one["phase"] == "apply"]
        self.assertEqual(applying["state"], "planned")
        capacity_owner.begin_integration_ending(
            store, orchestration_id=self.ORCHESTRATION,
            reason="operator drain")
        with self.assertRaises(ContractRefusal) as caught:
            self.adopt(store)
        self.assertIn("still held", str(caught.exception))

    def test_an_output_the_preparation_did_not_produce_refuses(self):
        """The two declared outputs are the preparation's contract. A result
        that froze only its report has collected no candidate for an apply to
        import, and a missing artifact is not an empty one."""
        body = self.report_body()
        outputs = [_answered_output(adoption.PREPARATION_REPORT_OUTPUT, body,
                                    "artifact-report", path=self.REPORT_PATH),
                   {"name": adoption.PREPARED_CANDIDATE_OUTPUT,
                    "type": "directory-result", "status": "missing-optional",
                    "content_manifest": None, "artifact": None,
                    "result_metadata": {}}]
        with self.assertRaises(ContractRefusal):
            self.ended(outputs=outputs)
