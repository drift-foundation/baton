"""Direct construction-boundary diagnostics, not full deployment proof."""
import json
from types import SimpleNamespace
from unittest.mock import patch
from tools import stage_execution as s, integration_worker as w
from baton_v12.contracts import ContractRefusal

class Ordinary:
    def __init__(self): self.closed = False
    def close(self): self.closed = True

answers = []
for selection, missing, fail in [("false", False, False), (True, True, False), (True, False, True)]:
    ordinary = Ordinary()
    built = []
    given = {"job_bindings": [{"job_id": "job-a"}], "integration_preparation": selection}
    worker = {"deployment": {"participant": "baton.impl-a"}}
    deployment = SimpleNamespace(jobs=object())
    integrator = None if missing else SimpleNamespace(required_tests=lambda _: {})
    def port(*args):
        if fail: raise ContractRefusal("refused", "precondition", "diagnostic port refusal")
        return object()
    def managed(**kwargs): built.append(kwargs); return object()
    with patch.object(s, "_served_deployment", return_value={}), patch.object(s.single_worker, "worker_operations", return_value=ordinary), patch.object(w, "ManagedPreparation", side_effect=managed), patch.object(w, "authority_port", side_effect=port):
        try:
            s._integration_operations(given, worker, object(), object(), object(), engine_run=None, clock=None, checkpoint=None, job_store=object(), integrator=integrator, deployment=deployment)
        except ContractRefusal:
            assert fail
        else:
            assert not fail
    answers.append({"selection": selection, "integrator_missing": missing, "port_refuses": fail, "managed_constructed": bool(built), "ordinary_closed_after_call": ordinary.closed})
    ordinary.close()  # Dispose the diagnostic's own inert stand-in.
assert answers[0]["managed_constructed"]
assert not answers[1]["managed_constructed"]
assert not answers[2]["ordinary_closed_after_call"]
print(json.dumps({"observations": answers, "limits": "Normal composition function, mocked resource constructors. Confirms truthy-string activation, missing-owner fallback, and missing cleanup call on port failure; not an observed real resource leak."}, indent=2))
