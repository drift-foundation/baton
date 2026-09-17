"""Independent W183883 review: real empty composition and unexpected state.

Only disposable v12 fixture stores through public APIs. No raw SQL, real Git,
provider, engine, installed build, or production/v11 store access.
"""
import hashlib
import io
import json
from pathlib import Path
import tempfile
import time

from tools import bootstrap, stage_execution
from tests.tools.test_bootstrap import guide_example
from tests.job_manager.test_scheduling import pool, principals
from tests.manager.test_offers import FakeSession, fake_claim_signature, PROFILE, NOW
from baton_v12.job_manager import JobStore, scheduler, manager
from baton_v12.worker_manager import (ControlStore, AuthorityPort, certify_profile,
                                     issue_offer, accept_offer, recover_on_restart)


started = time.monotonic()
root = Path(tempfile.mkdtemp(prefix="w183883-review190015-"))
evidence = {"scratch": str(root), "cases": {}}

def scenario(name, seed_before):
    document = dict(guide_example(), state_root=str(root / name))
    prepared = bootstrap.prepare(document, stream=io.StringIO())
    places = prepared["places"]
    uuid = prepared["authority_uuid"]
    jobs = JobStore.open(places["job_store"], authority_uuid=uuid,
                         incarnation="review-jobs", clock=lambda: NOW)
    control = ControlStore.open(places["control_store"], incarnation="review-control",
                                clock=lambda: NOW)
    composed = None
    work_id = uuid[:8] + "-W1"
    session = FakeSession()
    session._work["authority_uuid"] = uuid
    port = AuthorityPort(session, fake_claim_signature)
    def seed():
        certify_profile(control, "runtime", "reference", PROFILE)
        issue_offer(control, port, offer_id="review-offer", work_id=work_id,
                    runtime_attempt_id="review-attempt", input_digest="sha256:" + "1"*64,
                    policy_digest="sha256:" + "2"*64, profile_digest=PROFILE,
                    profile_name="reference", mint_bearer=lambda: "review-only-bearer")
        accept_offer(control, port, offer_id="review-offer", decision="accept",
                     bearer="review-only-bearer", now=NOW, runtime_attempt_id="review-attempt",
                     work_ref={"authority_uuid":uuid,"work_id":work_id})
    try:
        if seed_before:
            seed()
        composed = stage_execution.operations_from(prepared["configuration"], jobs, control)
        if not seed_before:
            seed()
        reported = manager.reconcile(jobs, composed, now=NOW)
        actual = recover_on_restart(control, now=NOW)
        evidence["cases"][name] = {"composition_succeeded": True,
                                   "manager_report": reported,
                                   "control_public_recovery": actual,
                                   "seed_boundary": "real control offer APIs with strict fake Authority session"}
    finally:
        if composed is not None:
            composed.release()
        control.close()
        jobs.close()

scenario("existing-control-offer", True)
scenario("arriving-control-offer", False)

with JobStore.open(str(root / "pool-jobs"), authority_uuid="a"*32,
                   incarnation="review", clock=lambda: NOW) as jobs:
    operations = scheduler.PooledManagerOperations(jobs, {}, resolved_principals={})
    document = pool()
    activation = scheduler.activate_pool(jobs, document, principals(document))
    evidence["cases"]["pool-arrives-after-attachment"] = {
        "activation": activation, "sweep": manager.reconcile(jobs, operations, now=NOW),
        "active": scheduler.active_generation(jobs)}

record = Path(__file__).parent
repository = record.parents[4]
author = json.loads((record / "EVIDENCE-189914.json").read_text())
evidence["candidate_hashes"] = {
    name: {"expected": wanted,
           "actual": hashlib.sha256((repository / name).read_bytes()).hexdigest()}
    for name, wanted in author["changed_this_claim"].items()}
evidence["seconds"] = time.monotonic() - started
(record / "REVIEW-EVIDENCE-190015.json").write_text(json.dumps(evidence, indent=2) + "\n")
print(json.dumps(evidence, indent=2))
