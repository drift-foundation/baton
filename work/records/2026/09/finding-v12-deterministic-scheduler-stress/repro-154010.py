"""Review probes: synthetic extractor inputs and real fixture observation points.

No product or coordination-store modification; synthetic inputs are labelled.
"""
import json
from types import SimpleNamespace
from unittest.mock import patch

from tests.tools import scheduler_trace as trace
from tests.tools.test_scheduler_trace import TheComposedOwnersSupplyAuthorizedTransitions, TheValidatorRefusesSyntheticInvalidTraces

oracle = TheValidatorRefusesSyntheticInvalidTraces()
answers = {"synthetic_validator_probes": {}}
for name, acts in {"missing_start": ("reserve", "offer", "claim", "complete"),
                   "unsupported_review": ("review",), "unsupported_integration": ("integrate",)}.items():
    answers["synthetic_validator_probes"][name] = trace.validate(oracle.artifact(oracle.legal(acts=acts)))

extractor = TheComposedOwnersSupplyAuthorizedTransitions()
extractor.runtime_of = lambda held, attempt_id: None
stage_id = "job-a/implementation"
attempt = dict(attempt_id="attempt-a", episode=1)
allocation = dict(worker_id="worker-a", canonical_principal="principal-a", allocation_state="reserved")
def extracted(receipts):
    scenario = trace.Scenario(name="synthetic-owner-snapshots", jobs=[], workers=[])
    with patch("baton_v12.job_manager.stage_rows", return_value=[dict(stage_id=stage_id, ordinal=0)]), patch("baton_v12.job_manager.episodes_of", return_value=[attempt]), patch("baton_v12.job_manager.projection.receipts_of", return_value=receipts), patch("baton_v12.job_manager.projection.stage_states", return_value={}), patch("baton_v12.job_manager.allocation_of", return_value=allocation):
        held = extractor.recorded(SimpleNamespace(job=None, composed=None), trace.Trace(scenario))
    return dict(input_receipts=receipts, records=held.records, violations=trace.validate(held.artifact()))

answers["synthetic_refusal_extractor"] = extracted({"admit": dict(state="refused", operation_id="offer-a", detail="synthetic explicit refusal", recorded_at="2026-09-12T00:00:00Z")})
answers["synthetic_claim_precedes_offer_but_extractor_reorders"] = extracted({
    "admit": dict(state="performed", operation_id="offer-a", detail=None, recorded_at="2026-09-12T00:00:02Z"),
    "claim": dict(state="performed", operation_id="claim-a", detail=None, recorded_at="2026-09-12T00:00:01Z"),
})

# Actual ordinary composed fixture, with read-only observations at existing
# driver boundaries. Capture before correction rather than infer after it.
case = TheComposedOwnersSupplyAuthorizedTransitions()
case.setUp()
try:
    fixture = case.case
    held = fixture.coding()
    fixture.produced(held, "job-a", held.first, "print('the first job answered')\n")
    before = fixture.states_for(held.job, held.composed, "job-a")
    fixture.drive_job(held.job, held.composed, "job-a", "review", "waiting")
    reviewed = fixture.one_attempt_of(held.composed, "review-worker")
    fixture.review_turn(held, "job-a", reviewed, "changes-requested")
    fixture.drive_job(held.job, held.composed, "job-a", "implementation", "waiting")
    after = fixture.states_for(held.job, held.composed, "job-a")
    answers["real_owner_observation_boundaries"] = dict(before_correction=before, after_correction=after,
        implementation_completion_visible_before_supersession=before["implementation"] == "completed")
finally:
    case.doCleanups()

print(json.dumps(answers, indent=2))
