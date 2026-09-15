"""Exercise the existing schema4 fixture with synthetic future objects only.

This is a fixture-construction probe, not a capacity schema implementation/test.
"""
import json
import sqlite3
from unittest import mock
from baton_v12.job_manager import schema
from tests.job_manager.test_execution_limits import TheMigrationLeavesOldJobsMeaningExactlyWhatTheyMeant

case = TheMigrationLeavesOldJobsMeaningExactlyWhatTheyMeant(
    "test_an_empty_schema_four_store_migrates")
case.setUp()
try:
    future = """
CREATE TABLE integration_capacity_roots (id TEXT PRIMARY KEY);
CREATE TABLE integration_capacity_members (id TEXT PRIMARY KEY, state TEXT);
CREATE UNIQUE INDEX capacity_one_active_member ON integration_capacity_members(state);
"""
    with mock.patch.object(schema, "SCHEMA", schema.SCHEMA + future):
        case.schema_four()
    with sqlite3.connect(case.job_path) as connection:
        version = connection.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()[0]
        names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master")}
    retained = sorted(names & {"integration_capacity_roots", "integration_capacity_members", "capacity_one_active_member"})
    assert version == "4" and len(retained) == 3
    print(json.dumps({"declared_version": version, "future_objects_retained": retained,
                      "meaning": "Current schema_four fixture does not remove later capacity objects; synthetic DDL, not candidate migration evidence."}))
finally:
    case.tearDown()
    case.doCleanups()
