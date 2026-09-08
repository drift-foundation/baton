"""W103083 claim 110456. Run from v12/python with PYTHONPATH=src.
Offline probe: no Authority, provider, OCI runtime or coordination store.
"""
import json
from types import SimpleNamespace
from unittest.mock import Mock, patch
from tools import stage_execution as se, single_worker as sw, job_manager as jm
from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager.scheduler import PooledManagerOperations
out = {}
w = object.__new__(sw._SingleWorker)
w.given = {"input_manifest": {"work_ref": {"work_id": "work-review"}, "manifest_digest": "input"}, "profile_name": "profile", "profile_digest": "digest", "policy_digest": "policy"}
job = {"input_digest": "input", "policy_digest": "policy"}
for kind in ("review", "integration"):
    stage = {"stage_id": "stage-" + kind, "kind": kind, "work_id": "work-review", "profile_name": "profile", "profile_digest": "digest"}
    try:
        w.start(stage, job)
    except ContractRefusal as failure:
        out[kind + "_launch"] = str(failure)
        assert "accepts only 'implementation'" in str(failure)
    else:
        raise AssertionError("non-implementation stage unexpectedly launched")
pool = object.__new__(PooledManagerOperations)
ending = Mock(return_value="bootstrap-ending")
pool._worker = Mock(return_value=SimpleNamespace(conclude=ending))
publication = Mock()
composed = se.StageExecution(pool, authority=None, integration=None, workers=[], given={}, publication=publication)
assert composed.conclude({"stage_id": "s"}, job) == "bootstrap-ending"
ending.assert_called_once_with({"stage_id": "s"}, job)
assert publication.mock_calls == []
out["conclude"] = "StageExecution -> real PooledManagerOperations -> worker conclude; publication unused"
try:
    jm._exchange_read(composed)
except SystemExit as failure:
    out["status_factory"] = str(failure)
else:
    raise AssertionError("serving object unexpectedly provides observe_exchange")
with patch.dict(se.os.environ, {se.CONFIG_ENV: "/unused/config.json"}), patch.object(se, "_read", return_value={"document": "sentinel"}), patch.object(se, "operations_from", return_value="operations") as make:
    assert se.factory("job-store", "control-store") == "operations"
    make.assert_called_once_with({"document": "sentinel"}, "job-store", "control-store")
    out["factory_supplies_sessions"] = False
print(json.dumps(out, indent=2, sort_keys=True))
