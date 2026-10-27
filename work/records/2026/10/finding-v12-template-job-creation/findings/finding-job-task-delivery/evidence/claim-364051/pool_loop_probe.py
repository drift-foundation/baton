"""Probe: create a Job through the real creation operation, then let the real
pool serving loop serve it, with the injected checkpoint profile and no VCS."""
import json
import os
import subprocess

from tests.tools.test_stage_execution import ServingCase
from tests.tools.test_single_worker import Engine
from tests.job_manager.test_review_driver import Profile
from tests.job_manager.test_creation import (FakeAuthorization, FakeBinding,
                                             FakeDerivation, FakeOwnership)
from tests.job_manager.fixtures import FakeOperations
from tests.job_manager import fixtures
from baton_v12.contracts.manifest import job_input_identity
from baton_v12.job_manager import (creation, reconcile,
                                   status as projected, sweep)
from baton_v12.job_manager import templates
from tools import job_task, single_worker, stage_execution

held_run, held_popen = subprocess.run, subprocess.Popen


def refuse(argv):
    if argv and str(argv[0]).split("/")[-1] == "git":
        raise AssertionError("VCS: " + " ".join(str(one) for one in argv))


subprocess.run = lambda argv, *a, **k: (refuse(argv), held_run(argv, *a, **k))[1]
subprocess.Popen = lambda argv, *a, **k: (refuse(argv), held_popen(argv, *a, **k))[1]

case = ServingCase()
case.setUp()
try:
    jobs, control = case.stores("pool-created")
    installed = single_worker._held(case.worker("implementation")["deployment"])
    manifest = installed["input_manifest"]

    def task(selection):
        held = job_task.per_job_delivery(
            installed["task_bytes"], manifest,
            dict(selection, work_id=case.work))
        return dict(held,
                    input_digest=job_input_identity(held["input_manifest"]))

    identity = {"root": case.root, "job_store": case.job_path,
                "control_store": case.control_path,
                "authority_store": case.authority_path,
                "authority_uuid": case.config["authority_uuid"]}
    derivation = FakeDerivation(
        identity=identity,
        work_id=case.work, input_digest=job_input_identity(manifest),
        policy_digest=manifest["policy_digest"],
        profiles={"implementation": {"profile_name": "reference",
                                     "profile_digest": fixtures.PROFILE},
                  "review": {"profile_name": "reference",
                             "profile_digest": fixtures.PROFILE}},
        task=task)
    request = {"schema": templates.REQUEST_SCHEMA,
               "task": {"task_id": "pool-a",
                        "statement": "A requested pool task."},
               "source_selection": creation.INSTALLED_SOURCE,
               "scope": {"work": ["v12/python/tools/single_worker.py"],
                         "tests": ["v12/python/tests/tools/"
                                   "test_job_task_delivery.py"]},
               "acceptance": ["The requested task reaches the runtime."]}
    answered = creation.create_template_job(
        jobs, FakeOperations(), request=request, derivation=derivation,
        authorization=FakeAuthorization(identity=identity),
        binding=FakeBinding(identity=identity, work_id=case.work),
        ownership=FakeOwnership(identity=identity))
    print("created:", json.dumps({k: str(v)[:40] for k, v in answered.items()}))
    job_id = answered["job_id"]
    held = creation.job_task_of(jobs, job_id)
    print("store answers a task:", held is not None)

    document = case.composed_document(checkpoint_profile="reference")
    operations = stage_execution.operations_from(
        document, jobs, control, engine_run=Engine(),
        credential_provider=lambda *_: case.secret,
        clock=lambda: fixtures.NOW, checkout=case.checkout,
        checkpoint_profile=Profile())
    try:
        for tick in range(14):
            try:
                report = reconcile(jobs, operations, now=fixtures.NOW)
                if tick == 0:
                    print("reconcile report:", json.dumps(report, default=str)[:1200])
                report = sweep(jobs, operations, now=fixtures.NOW)
                if tick == 0:
                    print("sweep report:", json.dumps(report, default=str)[:1200])
            except BaseException as error:
                print("TICK RAISED", type(error).__name__, str(error)[:500])
                break
            found = [one for one in projected(
                jobs, operations, observed_at=fixtures.NOW)["jobs"]
                if one["job_id"] == job_id]
            states = {one["kind"]: one["state"] for one in found[0]["stages"]}
            print(tick, states)
            if states.get("implementation") == "waiting":
                break
        stage = found[0]["stages"][0]
        from baton_v12.worker_manager import attempts
        print("attempt", stage.get("attempt_id"))
        if stage.get("attempt_id"):
            print("recorded", str(attempts.recorded_input_of(
                control, stage["attempt_id"]))[:30])
            place = os.path.join(case.config["workspace_storage"],
                                 stage["attempt_id"], "inputs", "task.json")
            print("root exists:", os.path.exists(place))
            if os.path.exists(place):
                with open(place, "rb") as reading:
                    document_bytes = reading.read()
                print("published task_id:",
                      json.loads(document_bytes.decode())["task_id"])
    finally:
        operations.close()
finally:
    case.doCleanups()
    subprocess.run, subprocess.Popen = held_run, held_popen
