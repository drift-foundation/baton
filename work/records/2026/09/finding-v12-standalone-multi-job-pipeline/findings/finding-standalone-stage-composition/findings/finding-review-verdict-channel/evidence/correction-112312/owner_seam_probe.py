"""Show the existing historical read's adapter requirement on actual custody."""
import json
from pathlib import Path
from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import custody
from tests.job_manager.test_review_driver import TheWorkerCompletionTraversesPublicCustody as Case
f = Case()
try:
    f.setUp()
    held = f.produced()
    ended = f.end(held)
    f.assert_historical_replay(held, ended)
    evidence = {}
    with f.no_more_external_acts(held):
        for which in ("result", "workspace"):
            positive = custody.adopted_directory_custody(f.control, held["adapter"], held["attempt_id"], which)
            assert positive is not None
            try:
                custody.adopted_directory_custody(f.control, None, held["attempt_id"], which)
            except ContractRefusal as exc:
                evidence[which] = {"positive_with_adapter": positive, "adapter_free_refusal": str(exc)}
            else:
                raise AssertionError("read unexpectedly worked without adapter identity")
    Path(__file__).with_suffix(".json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))
finally:
    f.doCleanups()
