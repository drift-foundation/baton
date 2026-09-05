"""W71877 correction review: schema 3 accepts a changed index predicate."""

import os
import sqlite3
import tempfile
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import JobStore


AUTHORITY = "0" * 31 + "a"
NOW = "2026-09-05T11:56:00.000Z"


class CompletePriorSchema(unittest.TestCase):

    def test_changed_partial_index_predicate_refuses_without_migrating(self):
        with tempfile.TemporaryDirectory(prefix="w71877-review-") as root:
            path = os.path.join(root, "jobs.sqlite3")
            store = JobStore.open(path, authority_uuid=AUTHORITY,
                                  incarnation="initial", clock=lambda: NOW)
            store.close()
            connection = sqlite3.connect(path, isolation_level=None)
            try:
                for table in ("worker_affinity", "stage_allocations",
                              "pool_workers", "pool_generations"):
                    connection.execute(f"DROP TABLE {table}")
                connection.execute("DROP INDEX episodes_one_live_per_stage")
                # Same name, uniqueness and columns; opposite predicate. This
                # permits multiple live episodes, defeating the index's rule.
                connection.execute(
                    "CREATE UNIQUE INDEX episodes_one_live_per_stage "
                    "ON episodes(stage_id) WHERE ended_state IS NOT NULL")
                connection.execute(
                    "UPDATE meta SET value = '3' WHERE key = ?",
                    ("schema_version",))
            finally:
                connection.close()

            with self.assertRaises(ContractRefusal):
                JobStore.open(path, authority_uuid=AUTHORITY,
                              incarnation="migrating", clock=lambda: NOW)


if __name__ == "__main__":
    unittest.main(verbosity=2)
