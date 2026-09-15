"""D1 regression through the current observer; synthetic owner inputs only."""
import json
from types import SimpleNamespace
from unittest.mock import patch

from tests.tools import scheduler_trace as trace
from tests.tools.test_scheduler_trace import TheComposedOwnersSupplyAuthorizedTransitions

observer = TheComposedOwnersSupplyAuthorizedTransitions()
observer.runtime_of = lambda held, attempt: None
stage_id = "job-a/implementation"
attempt = dict(attempt_id="attempt-a", episode=1)
allocation = dict(worker_id="worker-a", canonical_principal="principal-a", allocation_state="reserved")
answers = {}
for name, offer_at, claim_at in (
    ("invalid_claim_before_offer", "2026-09-12T00:00:02Z", "2026-09-12T00:00:01Z"),
    ("valid_offer_before_claim", "2026-09-12T00:00:01Z", "2026-09-12T00:00:02Z"),
):
    receipts = {
        "admit": dict(state="performed", operation_id="offer-a", detail=None, recorded_at=offer_at),
        "claim": dict(state="performed", operation_id="claim-a", detail=None, recorded_at=claim_at),
    }
    recorded = trace.Trace(trace.Scenario(name="synthetic-" + name, jobs=[], workers=[]))
    with patch("baton_v12.job_manager.stage_rows", return_value=[dict(stage_id=stage_id, ordinal=0)]), patch("baton_v12.job_manager.episodes_of", return_value=[attempt]), patch("baton_v12.job_manager.projection.receipts_of", return_value=receipts), patch("baton_v12.job_manager.projection.stage_states", return_value={}), patch("baton_v12.job_manager.allocation_of", return_value=allocation):
        observer.observed(SimpleNamespace(job=None, composed=None), recorded, 1, ("job-a",), set())
    answers[name] = dict(input_receipts=receipts, records=recorded.records, violations=trace.validate(recorded.artifact()))
print(json.dumps(answers, indent=2))
