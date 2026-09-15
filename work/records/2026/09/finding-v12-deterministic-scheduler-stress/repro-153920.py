"""Independent correction review: synthetic invalid records/snapshots only."""
import json
from types import SimpleNamespace
from unittest.mock import patch

from tests.tools import scheduler_trace as trace
from tests.tools.test_scheduler_trace import TheComposedOwnersSupplyAuthorizedTransitions, TheValidatorRefusesSyntheticInvalidTraces

oracle = TheValidatorRefusesSyntheticInvalidTraces()
cases = {
    "old_missing_reserve_offer": oracle.legal(acts=("claim", "complete")),
    "old_alias_occupancy": oracle.legal(acts=("reserve",)) + oracle.legal(attempt="b", worker="w2", acts=("reserve",)),
    "completion_without_start": oracle.legal(acts=("reserve", "offer", "claim", "complete")),
    "integration_without_any_authorization": oracle.legal(acts=("integrate",)),
    "review_without_any_claim": oracle.legal(acts=("review",)),
}
answers = {name: {"records": records, "violations": trace.validate(oracle.artifact(records))} for name, records in cases.items()}

# Exercise the extractor with an explicitly synthetic owner snapshot containing
# a refused admission receipt. No actual Authority or store is modified.
extractor = TheComposedOwnersSupplyAuthorizedTransitions()
extractor.case = SimpleNamespace(deployment_of=lambda ignored: None)
attempt = dict(job_id="job-a", stage_id="job-a/implementation", episode=1,
               attempt_id="attempt-a", offer_id="offer-a")
entry = dict(attempt=attempt, state="exceptional",
             receipts={"admit": {"state": "refused", "receipt_json": "{}"}})
scenario = trace.Scenario(name="synthetic-refused-owner-snapshot", jobs=[], workers=[])
with patch("baton_v12.job_manager.projection.stage_states", return_value={attempt["stage_id"]: entry}), patch("baton_v12.job_manager.allocation_of", return_value={"worker_id": "w1", "canonical_principal": "p1"}):
    recorded = extractor.recorded(SimpleNamespace(job=None, composed=None), trace.Trace(scenario))
answers["refused_admit_snapshot_translation"] = {"input": entry, "records": recorded.records, "violations": trace.validate(recorded.artifact())}
print(json.dumps(answers, indent=2))
