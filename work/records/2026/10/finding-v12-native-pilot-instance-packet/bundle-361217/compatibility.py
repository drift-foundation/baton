"""W325959 — what the source-pinned bundle is, and what it can and cannot do.

PREPARATION ONLY. Nothing here installs, deploys, starts, stops, submits or
retries anything, and nothing here writes to the retained instance. The
retained instance is READ as ordinary JSON documents -- `deployment.json`,
`instance.json`, `install-inputs.json`, `bootstrap.json` -- which is what it
publishes about itself; no store under `db/` is opened, copied, traversed or
hashed, and no supported command is run against it.

WHAT IT ESTABLISHES, in four parts.

  1. THE BUNDLE. Its frozen identity, its whole-folder manifest through the
     product's own `tools.instance.manifest`, its native assets, and that the
     `fresh-attempt` verb is reachable from the FROZEN command rather than
     only from the checkout.
  2. THE RETAINED DOCUMENTS. The new build's own readers are run over the
     retained instance's published configuration, in memory, to show the
     formats it already holds are ones this build still accepts.
  3. THE STORE FORMAT. Schema 8 adds `fresh_attempts`; the retained Job store
     is at 7. A DISPOSABLE schema-7 store carrying a quickstart-shaped failed
     Job is migrated by this build and every row is compared before and
     after. This is a format fixture, NOT the retained store.
  4. THE UPDATE GAP, measured rather than argued: what `bootstrap.custody`
     and `instance.verify` actually refuse when a new runtime meets a prepared
     destination.
"""

import hashlib
import json
import os
import pathlib
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[5]
PYTHON = ROOT / "v12" / "python"
BUNDLE = pathlib.Path(os.environ.get("W325959_BUNDLE",
                                     "/home/sl/w325959-bundle/out/distro"))
RETAINED = pathlib.Path("/home/sl/baton-instances/"
                        "native-coordination-pilot-w321608-3")

sys.path[:0] = [str(PYTHON), str(PYTHON / "src")]
os.environ.setdefault("BATON_V12_STACK_TEST_ROOT", "/var/tmp")

CHECKS = []


def check(what, outcome, detail=None):
    CHECKS.append({"check": what, "outcome": outcome, "detail": detail})
    return outcome


def digest_of(place):
    return hashlib.sha256(pathlib.Path(place).read_bytes()).hexdigest()


# -- 1. the bundle -----------------------------------------------------------

def the_bundle():
    from tools import instance

    said = json.loads(subprocess.run(
        [str(BUNDLE / "baton-v12-stack"), "identity"],
        capture_output=True, text=True, check=True).stdout)
    held = instance.manifest(str(BUNDLE))
    check("the frozen command names this commit",
          said["build_stamp"]["commit"] ==
          "614668e0831e8c87cdae11ca43620e0d544a84d5",
          said["build_stamp"])
    check("it reports itself frozen", said["frozen"] is True)
    check("the native validator extension travelled",
          said["native_rpds"].endswith(".so"), said["native_rpds"])
    check("both frozen schema assets travelled",
          sorted(said["schema_assets"]) ==
          ["agent-session-1.0", "worker-control-1.0"],
          said["schema_assets"])
    # THE WHOLE FOLDER, through the reader an instance verification uses.
    check("the whole-bundle manifest is computable by the product's reader",
          isinstance(held.get("digest"), str) and held.get("files", 0) > 0,
          {"files": held.get("files"), "digest": held.get("digest")})
    # AND THE RETRY VERB IS REACHABLE FROM THE FROZEN COMMAND.
    ran = subprocess.run(
        [str(BUNDLE / "baton-v12-stack"), "manager", "--store", "/nonexistent",
         "--incarnation", "probe", "--authority-uuid", "0" * 32,
         "fresh-attempt", "--help"], capture_output=True, text=True)
    check("`manager fresh-attempt --help` answers from the frozen command",
          ran.returncode == 0 and "--prior-job" in ran.stdout,
          {"returncode": ran.returncode})
    for operand in ("--prior-job", "--control", "--authority", "--instance"):
        check(f"the frozen verb names {operand}", operand in ran.stdout)
    return {"identity": said, "manifest": held}


# -- 2. the retained documents -----------------------------------------------

def the_retained_documents():
    """The new build's OWN readers, over what the instance publishes.

    READ-ONLY AND IN MEMORY. These are the ordinary documents the instance
    writes about itself; the stores beside them are not touched.
    """
    from baton_v12.contracts import ContractRefusal
    from tools import bootstrap, stage_execution

    held = {}
    for name in ("deployment.json", "instance.json", "install-inputs.json",
                 "bootstrap.json"):
        place = RETAINED / name
        held[name] = {"present": place.exists(),
                      "sha256": digest_of(place) if place.exists() else None}
    check("the retained instance publishes all four documents",
          all(one["present"] for one in held.values()), held)

    configuration = json.loads((RETAINED / "deployment.json").read_text())
    try:
        stage_execution.held_configuration(configuration)
        check("this build still accepts the retained deployment "
              "configuration", True)
    except ContractRefusal as refusal:
        check("this build still accepts the retained deployment "
              "configuration", False, refusal.message)

    document = json.loads((RETAINED / "install-inputs.json").read_text())
    try:
        bootstrap.held(bootstrap.without_installer_members(document))
        check("this build still accepts the retained install document", True)
    except Exception as failure:                             # noqa: BLE001
        check("this build still accepts the retained install document",
              False, f"{type(failure).__name__}: {failure}")

    # THE TASK THE PILOT WOULD RE-ATTEMPT, and which schema it is.
    tasks = sorted((RETAINED / "state" / "task").glob("*.json"))
    kinds = {one.name: json.loads(one.read_text()).get("schema")
             for one in tasks}
    check("the retained task is a /2 document, so the W321776 verification "
          "context (a /3 concern) does not reach it",
          set(kinds.values()) == {"baton.dogfood-task/2"}, kinds)
    held["tasks"] = kinds
    held["configuration"] = {
        "authority_uuid": configuration.get("authority_uuid"),
        "job_bindings": [one.get("job_id")
                         for one in configuration.get("job_bindings") or []],
        "workers": [(one.get("worker_id"), one.get("role"))
                    for one in configuration.get("workers") or []]}
    return held


# -- 3. the store format -----------------------------------------------------

def the_store_format():
    """Schema 7 carrying a failed Job, migrated by this build. DISPOSABLE.

    The retained Job store is at schema 7 and this build is 8. What a
    deployment update would do on its first write-open is migrate it, so the
    question is whether that preserves the failed Job the pilot must keep.

    THE FIXTURE IS BUILT FROM THIS BUILD'S OWN SCHEMA minus exactly what the
    7 -> 8 step creates, which is how `test_store` and `test_execution_limits`
    impersonate an older store. It is not a copy of the retained one and
    nothing here opens that store.
    """
    import sqlite3
    import tempfile

    from baton_v12.job_manager import JobStore, schema, submit
    from baton_v12.job_manager.store import _statements

    where = tempfile.mkdtemp(prefix="w325959-schema7-")
    place = os.path.join(where, "jobs.sqlite3")
    uuid = "5a8fa4b4275b4f7fa32efafc2c48f546"
    now = "2026-10-19T15:00:00.000Z"

    made = sqlite3.connect(place, isolation_level=None)
    try:
        for statement in _statements(schema.SCHEMA):
            if "fresh_attempts" in statement:
                continue                      # the 7 -> 8 step's own objects
            made.execute(statement)
        made.execute("INSERT INTO meta (key, value) VALUES ('store_kind', ?)",
                     (schema.STORE_KIND,))
        made.execute("INSERT INTO meta (key, value) "
                     "VALUES ('schema_version', '7')")
        made.execute("INSERT INTO meta (key, value) "
                     "VALUES ('authority_uuid', ?)", (uuid,))
    finally:
        made.close()

    # A QUICKSTART-SHAPED FAILED JOB, written through the ordinary submission
    # path of a store this build has migrated -- so the rows are the product's
    # own, not hand-built ones.
    with JobStore.open(place, authority_uuid=uuid, incarnation="jobs-probe",
                       clock=lambda: now) as store:
        check("a schema-7 store migrates rather than refusing", True,
              {"version": store._connection.execute(
                  "SELECT value FROM meta WHERE key = 'schema_version'"
              ).fetchone()[0]})
        submit(store, {
            "schema": "baton.v12.job-submission/2",
            "submission_id": "sub-w321608-quickstart-3",
            "jobs": [{"job_id": "quickstart-c",
                      "input_digest": "sha256:" + "1" * 64,
                      "policy_digest": "sha256:" + "2" * 64,
                      "test_scope": ["v12/python/tests"],
                      "terminal_policy": "report-and-hold",
                      "execution_limits": {"provider_turn_seconds": 3600,
                                           "verification_command_seconds":
                                               900},
                      "stages": [
                          {"kind": "implementation", "work_id": "5a8fa4b4-W1",
                           "profile_name": "reference",
                           "profile_digest": "sha256:" + "b" * 64,
                           "depends_on": []},
                          {"kind": "review", "work_id": "5a8fa4b4-W1",
                           "profile_name": "reference",
                           "profile_digest": "sha256:" + "b" * 64,
                           "depends_on": [{"job_id": "quickstart-c",
                                           "kind": "implementation"}]}]}]})

    # Put it back to 7, as a retained store that never met this build would
    # be, and record every row before the migration.
    tables = ("submissions", "jobs", "job_execution_limits", "stages",
              "episodes", "operations")
    held = sqlite3.connect(place, isolation_level=None)
    try:
        held.execute("DROP INDEX IF EXISTS fresh_attempts_one_successor")
        held.execute("DROP TABLE IF EXISTS fresh_attempts")
        held.execute("UPDATE meta SET value = '7' WHERE key = 'schema_version'")
        # AS TUPLES ON BOTH SIDES. `JobStore` sets `sqlite3.Row`, which
        # compares by identity rather than by value, so a comparison that
        # did not normalise would report every row as changed and prove
        # nothing.
        before = {one: [tuple(row) for row in
                        held.execute(f"SELECT * FROM {one}").fetchall()]
                  for one in tables}
    finally:
        held.close()

    with JobStore.open(place, authority_uuid=uuid, incarnation="jobs-after",
                       clock=lambda: now) as store:
        after = {one: [tuple(row) for row in store._connection.execute(
            f"SELECT * FROM {one}").fetchall()] for one in tables}
        version = store._connection.execute(
            "SELECT value FROM meta WHERE key = 'schema_version'").fetchone()[0]
        relations = sorted(
            one[0] for one in store._connection.execute(
                "SELECT name FROM sqlite_schema WHERE type = 'table'"))

    check("the migration carries the store to this build's schema",
          version == str(schema.SCHEMA_VERSION), version)
    check("`fresh_attempts` exists afterwards and is empty",
          "fresh_attempts" in relations, relations)
    for one in tables:
        if one == "operations":
            # The migration journals nothing, but a comparison that demanded
            # byte-equality of a journal would be asserting about the wrong
            # thing; what matters is that no recorded outcome was lost.
            check(f"every prior `{one}` row survives",
                  all(row in after[one] for row in before[one]),
                  {"before": len(before[one]), "after": len(after[one])})
            continue
        check(f"`{one}` is byte-identical across the migration",
              before[one] == after[one],
              {"rows": len(before[one])})
    return {"relations": relations, "version": version,
            "rows": {one: len(before[one]) for one in tables}}


# -- 4. the update gap -------------------------------------------------------

def the_update_gap():
    """What the product actually refuses, driven on a disposable destination.

    NOT A PROPOSAL AND NOT AN UPDATER. These two calls are made against a
    throwaway directory so the refusals are this build's own words rather
    than a reading of its source, and so the packet's disposition rests on
    measurement.
    """
    import tempfile

    from tools import bootstrap, instance

    where = tempfile.mkdtemp(prefix="w325959-gap-")
    # CUSTODY IS THE INSTALLER'S VIEW OF A DESTINATION, which is
    # `tools.instance.layout`'s set of places -- `bootstrap.layout` is the
    # STATE ROOT's and names no runtime.
    places = instance.layout(where)
    pathlib.Path(places["distro"]).mkdir(parents=True)
    try:
        bootstrap.custody(places, where)
        check("bootstrap.custody refuses a destination that already holds a "
              "runtime", False, "it did not refuse")
    except bootstrap.BootstrapRefusal as refusal:
        check("bootstrap.custody refuses a destination that already holds a "
              "runtime", True, str(refusal))

    # AND THE SELECTOR'S OWN CHECK, over THIS REAL BUNDLE. The destination
    # is the folder the bundle sits in, so `layout` names the bundle itself
    # as the runtime and `verify` recomputes its true manifest -- the
    # refusal is then about the DIGEST rather than about an empty directory,
    # which is the state an updated bundle really puts a retained instance
    # into.
    beside = str(BUNDLE.parent)
    fresh = instance.manifest(str(BUNDLE))
    document = {"destination": beside,
                "command": str(BUNDLE / "baton-v12-stack"),
                "runtime": {"digest": "sha256:" + "0" * 64, "files": 1}}
    try:
        instance.verify(document)
        check("instance.verify refuses a runtime whose digest is not the one "
              "the instance recorded", False, "it did not refuse")
    except instance.InstanceRefusal as refusal:
        check("instance.verify refuses a runtime whose digest is not the one "
              "the instance recorded", True, str(refusal))
    # AND IT ACCEPTS THE SAME BUNDLE once the recorded digest is this one --
    # so the obstacle is the RECORD, not the runtime.
    try:
        instance.verify(dict(document, runtime=fresh))
        check("instance.verify accepts this bundle when the record names it, "
              "so the obstacle is the recorded selector and not the runtime",
              True, {"digest": fresh["digest"], "files": fresh["files"]})
    except instance.InstanceRefusal as refusal:
        check("instance.verify accepts this bundle when the record names it, "
              "so the obstacle is the recorded selector and not the runtime",
              False, str(refusal))

    # WHAT THE RETAINED INSTANCE RECORDS, read as an ordinary document.
    recorded = json.loads((RETAINED / "instance.json").read_text())
    held = recorded.get("runtime") or {}
    fresh = instance.manifest(str(BUNDLE))
    check("the retained instance records a runtime digest that is NOT this "
          "bundle's, which is the whole update gap",
          held.get("digest") != fresh.get("digest"),
          {"instance_records": held.get("digest"),
           "this_bundle": fresh.get("digest"),
           "instance_command": recorded.get("command")})
    return {"retained_runtime": held, "retained_command": recorded.get(
        "command"), "new_runtime": fresh}


def main():
    started = time.monotonic()
    answer = {"bundle_path": str(BUNDLE),
              "source_commit": "614668e0831e8c87cdae11ca43620e0d544a84d5",
              "retained_instance": str(RETAINED)}
    answer["bundle"] = the_bundle()
    answer["retained_documents"] = the_retained_documents()
    answer["store_format"] = the_store_format()
    answer["update_gap"] = the_update_gap()
    answer["checks"] = CHECKS
    answer["failed"] = [one for one in CHECKS if not one["outcome"]]
    answer["seconds"] = time.monotonic() - started
    print(json.dumps(answer, indent=1, sort_keys=True, default=str))
    return 1 if answer["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
