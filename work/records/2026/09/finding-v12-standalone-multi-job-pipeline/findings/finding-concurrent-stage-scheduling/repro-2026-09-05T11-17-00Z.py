"""Independent-review reproductions for W71877 proposal c6524663....

Run from the reconstructed proposal's v12/python directory with:

    PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1 \
      python3 -B <this-file>

Each passing case demonstrates behavior the accepted contract requires to
refuse or handle differently. The script mutates only its test-owned temporary
Job stores.
"""

import sqlite3
from types import SimpleNamespace
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import (JobStore, PooledManagerOperations,
                                   active_generation, allocation_of,
                                   pool_workers, reserve)
from baton_v12.job_manager import scheduler
from tests.job_manager.fixtures import UUID, job, stage
from tests.job_manager.test_scheduling import PoolCase, pool, worker


class Routed:
    def __init__(self, participant):
        self.port = SimpleNamespace(participant=participant)
        self.calls = []

    def launch(self, stage, job_document):
        self.calls.append(("launch", stage["attempt_id"]))
        return {"runtime_id": "runtime:wrongly-routed"}

    def canonical_operation(self, act, offer_id):
        return f"offer.{act}:{offer_id}"

    def receipt_of(self, operation_id):
        return None


class DurableAdmissionRefusal(Routed):
    def admit(self, stage, job_document):
        # ManagerOperations can reach this shape after issue_offer commits and
        # the injected bearer-delivery capability refuses.
        raise ContractRefusal("refused", "capability", "delivery refused",
                              durable=True)


class SchedulerReviewReproductions(PoolCase):
    def test_reactivating_an_older_variant_does_not_make_it_active(self):
        primary = pool()
        self.activate(primary)
        self.activate(pool("fallback"))
        returned = self.activate(primary)
        self.assertEqual(returned["generation"], 1)
        self.assertEqual(active_generation(self.jobs)["generation"], 2)

    def test_an_unallocated_stage_is_silently_routed_to_the_first_worker(self):
        document = pool(workers=[worker(
            "impl", "implementation", "baton.impl", ["implementation"])])
        self.activate(document, {"baton.impl": "principal:impl"})
        attempt = self.attempts([
            job("one", stages=[stage("implementation", "work:one")])])[0]
        routed = Routed("baton.impl")
        pooled = PooledManagerOperations(self.jobs, {(1, "impl"): routed})
        answer = pooled.launch(attempt, {})
        self.assertEqual(answer["runtime_id"], "runtime:wrongly-routed")
        self.assertIsNone(allocation_of(self.jobs, attempt["attempt_id"]))

    def test_release_with_changed_reason_bypasses_operation_collision(self):
        self.activate()
        attempt = self.attempts([
            job("one", stages=[stage("implementation", "work:one")])])[0]
        reserve(self.jobs, attempt)
        scheduler.release(self.jobs, attempt["attempt_id"], "first-reason")
        replayed = scheduler.release(
            self.jobs, attempt["attempt_id"], "different-reason")
        self.assertEqual(replayed["release_reason"], "first-reason")

    def test_any_durable_admission_refusal_releases_without_ending_evidence(self):
        document = pool(workers=[worker(
            "impl", "implementation", "baton.impl", ["implementation"])])
        self.activate(document, {"baton.impl": "principal:impl"})
        attempt = self.attempts([
            job("one", stages=[stage("implementation", "work:one")])])[0]
        pooled = PooledManagerOperations(
            self.jobs, {(1, "impl"): DurableAdmissionRefusal("baton.impl")})
        with self.assertRaises(ContractRefusal):
            pooled.admit(attempt, {})
        self.assertEqual(allocation_of(
            self.jobs, attempt["attempt_id"])["allocation_state"], "released")
        self.assertIsNone(self.jobs._connection.execute(
            "SELECT ended_state FROM episodes WHERE stage_id = ?",
            (attempt["stage_id"],)).fetchone()[0])

    def test_schema_three_missing_its_live_episode_index_is_migrated(self):
        self.jobs.close()
        connection = sqlite3.connect(self.job_path, isolation_level=None)
        for table in ("worker_affinity", "stage_allocations", "pool_workers",
                      "pool_generations"):
            connection.execute(f"DROP TABLE {table}")
        connection.execute("DROP INDEX episodes_one_live_per_stage")
        connection.execute("UPDATE meta SET value = '3' WHERE key = ?",
                           ("schema_version",))
        connection.close()
        migrated = JobStore.open(self.job_path, authority_uuid=UUID,
                                 incarnation="review", clock=self.clock)
        self.addCleanup(migrated.close)
        self.assertEqual(pool_workers(migrated), [])
        objects = {row[0] for row in migrated._connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index'")}
        self.assertNotIn("episodes_one_live_per_stage", objects)


if __name__ == "__main__":
    unittest.main(verbosity=2)
