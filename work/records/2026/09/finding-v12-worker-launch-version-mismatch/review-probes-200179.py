import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import time
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[5]
DOSSIER = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / "v12/python"), str(ROOT / "v12/python/src")]
from tools import bootstrap
from baton_v12.authority.core import UNESTABLISHED_TARGET


class AuthorityDouble:
    def __init__(self):
        self.effects = []
        self.works = {}

    def add_route_handler(self, *args, **kwargs):
        self.effects.append(["route", args, kwargs])

    def project_work(self, work_id):
        return self.works.get(work_id)

    def create_work(self, work_id, *args, **kwargs):
        self.works[work_id] = {"scope": work_id}
        self.effects.append(["work", work_id])

    def grant_capability(self, *args, **kwargs):
        self.effects.append(["grant", args, kwargs])

    def canonical_target(self):
        return UNESTABLISHED_TARGET


def main():
    started = time.monotonic()
    evidence = json.loads((DOSSIER / "EVIDENCE-200000.json").read_text())
    hashes = {path: {"expected": digest, "actual": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()} for path, digest in evidence["candidate"].items()}
    document = {
        "workers": [{"role": "implementation", "participant": "review-probe.author"}],
        "jobs": [{"job_id": "first", "work_id": "first-work", "line_declared_base": "a" * 40}, {"job_id": "second", "work_id": "second-work", "line_declared_base": "b" * 40}],
        "receipt_participants": {name: "review-probe." + name for name in bootstrap.GRANTS},
        "integration_profile": {"integrator_participant": "review-probe.integrator"},
    }
    authority = AuthorityDouble()
    try:
        bootstrap._compose(authority, document, stream=io.StringIO())
    except bootstrap.BootstrapRefusal as failure:
        refused = str(failure)
    else:
        raise AssertionError("conflicting bases unexpectedly accepted")
    assert authority.effects and len(authority.works) == 2
    spec = importlib.util.spec_from_file_location("reviewed_proposing_agent", DOSSIER / "instance-200000/context/worker/proposing_agent.py")
    agent_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(agent_module)
    calls = []

    def observed(repository, *arguments, **kwargs):
        calls.append({"repository": repository, "arguments": arguments})
        return "a" * 40 + "\n"

    with mock.patch.object(agent_module, "_ran", side_effect=observed):
        agent_module.ProposingAgent().work({"role": "review"}, [])
    assert len(calls) == 3 and all(call["repository"] == "/output" for call in calls)
    tests = unittest.defaultTestLoader.loadTestsFromName("tests.manager.test_proposing_fixture.TheIMAGEActuallySELECTSThisAgent")
    transcript = io.StringIO()
    run_started = time.monotonic()
    result = unittest.TextTestRunner(stream=transcript, verbosity=2).run(tests)
    answer = {
        "claim": 200179,
        "participant": "baton.rvpc",
        "candidate_hashes": hashes,
        "hashes_match": all(entry["actual"] == entry["expected"] for entry in hashes.values()),
        "bootstrap_late_refusal": {"refusal": refused, "effects_before_refusal": authority.effects, "boundary": "real _compose and _canonical_target, in-memory Authority double; no store opened"},
        "review_root_probe": {"calls": calls, "boundary": "real agent review branch; subprocess observation seam mocked; no commands or output writes"},
        "tests": {"count": result.testsRun, "successful": result.wasSuccessful(), "seconds": time.monotonic() - run_started, "output": transcript.getvalue()},
        "seconds": time.monotonic() - started,
        "engine_observation": "read-only docker ps attempt lookup refused: permission denied connecting to unix:///var/run/docker.sock; no engine state claimed or changed",
    }
    print(json.dumps(answer, indent=2))
    return 0 if answer["hashes_match"] and result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
