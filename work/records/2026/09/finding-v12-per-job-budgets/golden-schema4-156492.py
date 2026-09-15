"""Produce a GENUINE populated schema-4 Job store with the OLD owner.

Run inside the materialized pre-W156162 tree. It submits the ordinary /1 document
through the committed owner, so the store, its schema version, its rows and its
signed submission operation are all that build's own work -- not this Work's code
writing what it wishes the old build had written.
"""
import hashlib
import json
import os
import shutil
import sys

OUT = sys.argv[1]

from baton_v12.job_manager import JobStore, submit, schema
from tests.job_manager.fixtures import UUID, submission

NOW = "2026-09-02T00:00:00.000Z"
place = "/tmp/w156162_golden/jobs.sqlite3"
shutil.rmtree("/tmp/w156162_golden", ignore_errors=True)
os.makedirs("/tmp/w156162_golden", exist_ok=True)
store = JobStore.open(place, authority_uuid=UUID, incarnation="jobs-old",
                      clock=lambda: NOW)
try:
    recorded = submit(store, submission())
    version = store._connection.execute(
        "SELECT value FROM meta WHERE key = 'schema_version'").fetchone()[0]
    tables = sorted(row[0] for row in store._connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' "
        "AND name NOT LIKE 'sqlite_%'"))
    jobs = [row[0] for row in store._connection.execute(
        "SELECT job_id FROM jobs ORDER BY job_id")]
finally:
    store.close()
shutil.copyfile(place, OUT)
with open(OUT, "rb") as reading:
    digest = hashlib.sha256(reading.read()).hexdigest()
print(json.dumps({"schema_version": version, "build_version": schema.SCHEMA_VERSION,
                  "tables": tables, "jobs": jobs, "recorded": recorded,
                  "golden_sha256": digest}, sort_keys=True, indent=1))
