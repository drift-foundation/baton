"""Independent mutation checks on retained owner artifacts; never owner-state edits."""
import copy
import json
from pathlib import Path
from tests.tools import scheduler_trace as oracle
from tests.tools.test_scheduler_trace import TheComposedOwnersSupplyAuthorizedTransitions as Cases
from tests.tools.test_scheduler_trace import TheValidatorRefusesSyntheticInvalidTraces as Negatives


def main():
    artifacts = {s["name"]: s["artifact"] for s in json.loads(Path(__file__).with_name("trace-156124-composed.json").read_text())["schedules"]}
    original = artifacts["composed-both-jobs-imported"]
    assert oracle.validate(original) == []
    def show(name, artifact):
        print(json.dumps({name: oracle.validate(artifact)}, sort_keys=True), flush=True)
    swapped = copy.deepcopy(original)
    for r in swapped["records"]:
        if r["act"] in oracle.SUBJECT_AUTHORIZATION:
            r["job_id"] = {"job-a": "job-b", "job-b": "job-a"}[r["job_id"]]
            r["stage_id"] = r["job_id"] + "/integration"
    show("receipt_chains_swapped_between_completed_jobs", swapped)
    unclaimed = copy.deepcopy(original)
    unclaimed["records"] = [r for r in unclaimed["records"] if r.get("stage_id") != "job-b/integration" or r["act"] == "complete" or r["act"] in oracle.SUBJECT_AUTHORIZATION]
    next(r for r in unclaimed["records"] if r.get("stage_id") == "job-b/integration" and r["act"] == "complete")["attempt_id"] = "never-admitted-or-claimed"
    show("reconciled_completion_without_any_admission_chain", unclaimed)
    no_start = copy.deepcopy(original)
    no_start["records"] = [r for r in no_start["records"] if not (r.get("stage_id") == "job-a/integration" and r["act"] == "start")]
    show("direct_runtime_import_with_start_deleted", no_start)

    n = Negatives()
    first = n.legal(acts=("reserve",), tick=1)
    second = n.legal(attempt="attempt-2", acts=("reserve",), tick=2)
    release = n.record(act="release", attempt_id="attempt-1", tick=2, worker_id="foreign-worker", principal="principal:foreign", operation_id="attempt-1:release")
    assert "overlapping-occupancy" in n.codes(first + second + [release])
    release.update(worker_id="impl-one", principal="principal:one", recorded_at="2026-09-02T00:00:02.000Z")
    second[0]["recorded_at"] = "2026-09-02T00:00:01.000Z"
    assert "overlapping-occupancy" in n.codes(first + second + [release])
    print(json.dumps({"prior_occupancy_mutations_rejected": True}), flush=True)

    case = Cases("test_the_composed_deployment_reopens_and_continues")
    case.setUp()
    try:
        reopen = case.reopened
        def duplicate_start(held):
            result = reopen(held)
            vectors = [v for v in case.case.engine.starts if held.second in " ".join(v)]
            assert len(vectors) == 1
            case.case.engine(vectors[0])
            return result
        case.reopened = duplicate_start
        try:
            case.test_the_composed_deployment_reopens_and_continues()
        except AssertionError:
            print(json.dumps({"prior_duplicate_start_mutation_rejected": True}), flush=True)
        else:
            raise AssertionError("duplicate start passed candidate assertions")
    finally:
        case.doCleanups()


if __name__ == "__main__":
    main()
