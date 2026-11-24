"""Print what a LEGACY (no provider selection) composition produces, canonically. Run once in the base tree and once in the candidate tree; the two outputs must be byte-identical."""
import json, sys, os, inspect
from baton_v12.contracts import digest
from baton_v12.worker_manager import launch, oci, provider_context as context
from tools import next_run_bindings, single_worker, stage_execution
sys.path.insert(0, os.path.join(os.path.dirname(os.getcwd()), "worker")); sys.path.insert(0, os.path.join(os.getcwd(), "src", "baton_v12"))
out = {}
for contextual in (False, True):
    for build in ("2.1.247", "2.1.200"):
        kw = dict(image_reference="img:ref", image_digest="sha256:" + "b" * 64, cli_build=build, provider_network="bridge", runtime_uid=1000, turn_seconds=900, verification_seconds=300, implementer_invocations=1, contextual=contextual)
        out[f"identities contextual={contextual} build={build}"] = next_run_bindings.deployment_identities(**kw)
job = {"job_id": "job-a", "attempt_id": "att-1", "job_input_digest": "sha256:" + "c" * 64}
for name, fn in (("launch_schemas", lambda: [launch.SCHEMAS[:5], launch.PAYLOAD_SCHEMAS[:4]]),
                 ("config_schemas", lambda: [single_worker.CONFIG_SCHEMA, single_worker.CONTEXT_CONFIG_SCHEMA, single_worker.LAYOUT_CONFIG_SCHEMA]),
                 ("separation_constant", lambda: stage_execution.SEPARATION_CLASS),
                 ("context_policies", lambda: [dict(context.ARGV_POLICY), dict(context.ENVIRONMENT_POLICY)])):
    out[name] = fn()
import claude_agent, baton_worker
out["worker constants"] = [claude_agent.PROVIDER_PROGRAM, list(claude_agent.PROVIDER_ARGUMENTS), claude_agent.PROVIDER_HOME_STATE, claude_agent.PROVIDER_CREDENTIAL, list(baton_worker.SUPPORTED_LAUNCH_SCHEMAS[:4])]
sig = inspect.signature(launch.launch_document)
out["launch_document parameters (legacy prefix)"] = [n for n in sig.parameters if n != "provider_selection"]
print(json.dumps(out, sort_keys=True, indent=1, default=str))
