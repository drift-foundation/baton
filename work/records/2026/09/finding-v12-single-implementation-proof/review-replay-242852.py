"""Unable-result ending re-entry on disposable fixtures, never provider reuse."""
import json
from pathlib import Path
import time
from unittest import mock

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import review_driver
from test_failure_path import AnUnableTurnFailsPromptlyAndCleansUp

started = time.monotonic()
results = []
for refuse_once in (False, True):
    case = AnUnableTurnFailsPromptlyAndCleansUp(
        "test_execution_is_stopped_and_cleanup_is_positive")
    try:
        case.setUp()
        ending = review_driver.end_implementation
        cleanup = review_driver.authorize_cleanup
        clean_calls = []

        def clean(*args, **kwargs):
            clean_calls.append(kwargs["attempt_id"])
            if refuse_once and len(clean_calls) == 1:
                raise ContractRefusal("refused", "precondition",
                                      "reviewer fixture withholds one cleanup")
            return cleanup(*args, **kwargs)

        with mock.patch.object(review_driver, "end_implementation",
                               wraps=ending) as spy, mock.patch.object(
                review_driver, "authorize_cleanup", side_effect=clean):
            outcome, job, control, composed = case.supervised_failure()
            args, kwargs = spy.call_args
            # Historical ending replay after the positive destroy, with the
            # exact operands the real composed stage used. No new provider turn.
            replayed = ending(*args, **kwargs)
        assert outcome["stopped"] == "exceptional", outcome
        assert outcome["state"] == "held", outcome
        assert outcome["outstanding_cleanup"] == [], outcome
        assert outcome["workload"]["proposals"] == []
        assert replayed["disposition"] == "unable", replayed
        assert replayed["published"] is None, replayed
        calls = [json.loads(line) for line in case.calls.read_text().splitlines()]
        assert len(calls) == 1, calls
        if refuse_once:
            assert len(clean_calls) == 2, clean_calls
        results.append({"withheld_one_cleanup": refuse_once,
                        "cleanup_calls": len(clean_calls),
                        "ending_calls": spy.call_count,
                        "provider_calls": len(calls),
                        "stopped": outcome["stopped"],
                        "state": outcome["state"],
                        "served_ticks": outcome["served_seconds"],
                        "cleanup": outcome["cleanup"],
                        "replayed_disposition": replayed["disposition"],
                        "replayed_publication": replayed["published"]})
    finally:
        case.doCleanups()

evidence = {"claim": 242852, "results": results,
            "seconds": time.monotonic() - started,
            "scope": "Deterministic ending re-entry only; no provider session resume, live execution or deployed state."}
Path(__file__).with_suffix(".json").write_text(json.dumps(evidence, indent=2) + "\n")
print(json.dumps(evidence, indent=2))
