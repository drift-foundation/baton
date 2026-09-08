"""Narrow independent ending probes; no suite, engine, credential or Git mutation.

Use the accepted producer/entry/provider-process fixture, but a plain disposable
target and the fixture's explicit revision seam. These cases ask about the
ending, not Git revision identity. Synthetic canaries are not credentials.
"""
import json
import os
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[7]
sys.path[:0] = [str(REPO / "v12/python"), str(REPO / "v12/python/src")]
from tests.manager import test_integration_worker as fixture


def run_case(name, injected, linked_result=False):
    case = fixture.WorldCase("run")
    case.setUp()
    try:
        case.bundle(operation="add")
        target = case.target(repository=False)
        program = fixture.PROVIDER_SOURCE.replace(
            '    with open(facts["report"], "w", encoding="utf-8") as handle:',
            injected + '\n    with open(facts["report"], "w", encoding="utf-8") as handle:')
        Path(case.script).write_text(program)
        result_root = None
        if linked_result:
            old = {"schema": fixture.contract.RESULT_SCHEMA,
                   **{key: case.assignment[key] for key in
                      ("attempt_id", "lease_id", "canonical_target_id", "entry_id", "fence")},
                   "outcome": "held", "detail": {"reason": "prior-turn", "detail": {}}}
            fixture.workload.publish_result(case.delivery.result_root, old)
            result_root = str(Path(case.root) / "linked-result")
            os.symlink(case.delivery.result_root, result_root)
        status = case.entry(target=target, result_root=result_root)
        observed = case.observed()
        result = observed.get("result")
        return {"name": name, "entry_status": status,
                "provider_turns": len(case.commands),
                "target_imported": Path(target, case.reviewed()).read_bytes() == case.CANDIDATE,
                "observed": observed,
                "synthetic_canary_published": "REVIEW_CANARY_114048" in json.dumps(result)}
    finally:
        case.doCleanups()


cases = [
    ("verification_failed", '    report["verification"]["status"] = 1'),
    ("verification_unfinished", '    report["verification"]["status"] = None'),
    ("verification_missing", '    report["verification"] = None'),
    ("provider_argv_canary", '    report["verification"]["argv"] = ["check", "REVIEW_CANARY_114048"]'),
    ("outside_path_canary", '    report["paths"] = ["REVIEW_CANARY_114048"]'),
    ("phase_and_paths_incomplete", '    report["phase"] = "preflight"\n    report["paths"] = []'),
]
answers = [run_case(name, injected) for name, injected in cases]
answers.append(run_case("terminal_result_behind_link", "", linked_result=True))
output = {"boundary": "Real producer, entry, provider child and manager result reader; plain disposable target; injected revision; no Git process", "cases": answers}
Path(__file__).with_name("probe.json").write_text(json.dumps(output, indent=2) + "\n")
print(json.dumps(output, indent=2))
