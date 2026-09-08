"""Independent bounded probes; run from v12/python with PYTHONPATH=src:. .

Uses the accepted local fixture Authority and fake engine/profile only.
No live coordination database, provider, OCI engine or Git subprocess is used.
"""
import json
import unittest.mock

from baton_v12.job_manager import reconcile, status, submit, scheduler
from baton_v12.worker_manager import configured_workspace_group
from tests.job_manager import fixtures
from tests.job_manager.test_review_driver import Profile
from tests.tools.test_single_worker import Engine
from tests.tools.test_stage_execution import ServingCase
from tools import stage_execution


class LocalProfile(Profile):
    name = "git"


def report(name, **values):
    print(json.dumps(dict(probe=name, **values), sort_keys=True), flush=True)


def run(name, action):
    case = ServingCase()
    try:
        case.setUp()
        action(case)
    except Exception as error:
        report(name, error_type=type(error).__name__, error=str(error))
    finally:
        case.doCleanups()


def configured(control):
    try:
        return configured_workspace_group(control).gid
    except Exception as error:
        return type(error).__name__


def preflight(case):
    jobs, control = case.stores("review-preflight")
    before = configured(control)
    given = case.composed_document()
    given["receipt_participants"]["approval"] = "baton.not-configured"
    try:
        composed = stage_execution.operations_from(
            given, jobs, control, engine_run=Engine(),
            credential_provider=lambda *_: case.secret,
            clock=lambda: fixtures.NOW, checkout=case.checkout)
        case.addCleanup(composed.close)
        report("missing-session", before=before, after=configured(control),
               constructed=True,
               actor=composed.sessions["approval"].participant,
               holds_approve=composed.authority.holds_capability(
                   composed.sessions["approval"].participant, "approve"))
    except Exception as error:
        report("missing-session", before=before, after=configured(control),
               error_type=type(error).__name__, error=str(error))


def malformed_session(case):
    jobs, control = case.stores("review-malformed-session")
    before = configured(control)
    given = case.composed_document()
    given["receipt_participants"]["approval"] = "not-an-address"
    try:
        composed = stage_execution.operations_from(
            given, jobs, control, engine_run=Engine(),
            credential_provider=lambda *_: case.secret,
            clock=lambda: fixtures.NOW, checkout=case.checkout)
        case.addCleanup(composed.close)
    except Exception as error:
        report("malformed-session", before=before, after=configured(control),
               error_type=type(error).__name__, error=str(error))


def generation(case):
    jobs, control = case.stores("review-generation")
    before = scheduler.active_generation(jobs)
    try:
        stage_execution.operations_from(
            case.composed_document(pool_generation=4), jobs, control,
            engine_run=Engine(), credential_provider=lambda *_: case.secret,
            clock=lambda: fixtures.NOW, checkout=case.checkout)
    except Exception as error:
        report("wrong-generation", before=before,
               after=scheduler.active_generation(jobs),
               error_type=type(error).__name__, error=str(error))


def launch(case):
    jobs, control = case.stores("review-launch")
    engine = Engine()
    composed = stage_execution.operations_from(
        case.composed_document(), jobs, control, engine_run=engine,
        credential_provider=lambda *_: case.secret,
        clock=lambda: fixtures.NOW, checkout=case.checkout,
        checkpoint_profile=LocalProfile())
    case.addCleanup(composed.close)
    submit(jobs, case.submission)
    for tick in range(6):
        try:
            result = reconcile(jobs, composed, now=fixtures.NOW)
            report("launch-tick", tick=tick, result=result)
        except Exception as error:
            report("launch-tick", tick=tick, error_type=type(error).__name__,
                   error=str(error))
            break
    report("launch-final", starts=len(engine.starts),
           status=status(jobs, composed, observed_at=fixtures.NOW))


run("missing-session", preflight)
run("malformed-session", malformed_session)
run("wrong-generation", generation)
run("launch", launch)
