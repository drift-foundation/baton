"""Probe: fail the created Job's attempt, then retry it through the CLI."""
import io
import json
import os

from tests.tools.test_connected_creation import ConnectedCreationCase
from tests.tools.test_single_worker import Engine
from tests.job_manager import fixtures
from baton_v12.job_manager import JobStore, creation, reconcile, sweep
from baton_v12.job_manager import status as projected
from tools import job_manager, stage_execution


class Case(ConnectedCreationCase):
    def runTest(self):
        pass


def refusing_engine():
    """An engine that will not launch, so the attempt fails for real."""
    original = Engine.__call__

    def call(engine, argv, *, seconds=None):
        if len(argv) > 1 and argv[1] in ("run", "create"):
            engine.vectors.append(list(argv))
            return Engine.answer(status=1, stderr="the fixture refuses to run")
        return original(engine, argv, seconds=seconds)

    held = Engine()
    Engine.__call__ = call
    return held, original


case = Case()
case.setUp()
engine, original = refusing_engine()
try:
    case.installed()
    held = case.answered()
    job_id = held["job_id"]
    jobs = JobStore.open(case.owned["job_store"],
                         authority_uuid=case.owned["authority_uuid"],
                         incarnation="loop-1",
                         clock=lambda: fixtures.NOW)
    from baton_v12.worker_manager import ControlStore
    control = ControlStore.open(case.owned["control_store"],
                                incarnation="loop-1",
                                clock=lambda: fixtures.NOW)
    composed = stage_execution.operations_from(
        json.loads(open(os.path.join(case.state, "deployment.json")).read()),
        jobs, control, engine_run=engine,
        credential_provider=lambda provider, reference: case.secret,
        clock=lambda: fixtures.NOW, checkout=case.checkout)
    try:
        for tick in range(10):
            reconcile(jobs, composed, now=fixtures.NOW)
            sweep(jobs, composed, now=fixtures.NOW)
            states = {one["kind"]: one["state"] for one in
                      [stage for job in projected(
                          jobs, composed, observed_at=fixtures.NOW)["jobs"]
                       if job["job_id"] == job_id
                       for stage in job["stages"]]}
            print(tick, states)
            if states.get("implementation") in ("exceptional", "failed"):
                break
    finally:
        composed.close()
        control.close()
        jobs.close()

    said = io.StringIO()
    argv = ["--store", case.owned["job_store"], "--incarnation", "cli-2",
            "--authority-uuid", case.owned["authority_uuid"],
            "fresh-attempt", "--prior-job", job_id,
            "--instance", case.state,
            "--control", case.owned["control_store"],
            "--authority", case.owned["authority_store"]]
    try:
        code = job_manager.main(argv, stream=said)
        print("retry exit:", code)
        print("retry said:", said.getvalue()[:1000])
    except BaseException as error:
        print("RETRY RAISED:", type(error).__name__, str(error)[:600])

    store = JobStore.open(case.owned["job_store"],
                          authority_uuid=case.owned["authority_uuid"],
                          incarnation="reader-1", clock=lambda: fixtures.NOW)
    try:
        rows = store._connection.execute(
            "SELECT job_id, prior_job_id, state FROM fresh_attempts").fetchall()
        for one in rows:
            print("fresh row:", tuple(one), "task ->",
                  (creation.job_task_of(store, one[0]) or "NONE")[:70])
    finally:
        store.close()
finally:
    Engine.__call__ = original
    case.doCleanups()
