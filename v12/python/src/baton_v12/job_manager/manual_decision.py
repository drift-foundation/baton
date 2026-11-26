"""Final owner decisions on held MANUAL phases. Worker assessments remain immutable."""
from ..contracts import ContractRefusal, canonical_text, digest
from ..worker_manager import boundaries
from . import job_control, manual
from .store import job_signature


def finish(store, job_id, phase, outcome, *, actor):
    """Record one decision. The installed operator boundary authenticates the actor."""
    job_id = manual._key(job_id, "Job")
    phase = manual._key(phase, "phase")
    if outcome not in ("success", "failure"):
        raise ContractRefusal("refused", "precondition", "choose success or failure for the held phase")
    actor = boundaries.document(actor, "authenticated owner identity",
                                required=("authority_uuid", "participant", "principal", "uid"))
    if actor["authority_uuid"] != store.authority_uuid or type(actor["uid"]) is not int or actor["uid"] < 0:
        raise ContractRefusal("refused", "precondition", "owner identity differs from the installed authority or has no local uid")
    for key in ("participant", "principal"):
        boundaries.identity(actor[key], "authenticated owner " + key)
    target = {"job_id": job_id, "phase": phase}
    kind = "manual.finish-phase"
    operation = kind + ":" + digest(target)[7:]
    signature = job_signature(kind, dict(target, outcome=outcome, actor=actor))

    def decide(connection):
        manual._open(connection, job_id)
        current = manual._phase_snapshot(manual._phase(connection, job_id, phase))
        frozen = current["frozen"]
        if current["state"] != "selected" or not frozen or not current["held_cause"]:
            raise ContractRefusal("refused", "precondition", "phase requires a selected, frozen result held for the owner")
        now = store._now()
        if job_control.advance_watermark(connection, now) > now or now < frozen["frozen_at"]:
            raise ContractRefusal("refused", "precondition", "owner decision predates the observed evidence")
        receipt = dict(target, action="finish-phase", operation_id=operation, recorded_at=now, outcome=outcome,
                       actor=actor, execution_job_id=current["execution_job_id"], held_cause=current["held_cause"],
                       frozen=frozen)
        result = {"reason": "owner-decision", "attempt_id": frozen["attempt_id"], "owner_decision": receipt}
        connection.execute("UPDATE manual_phases SET settled_at=?,outcome=?,result=? WHERE job_id=? AND phase=?",
                           (now, "completed" if outcome == "success" else "exceptional", canonical_text(result), job_id, phase))
        return receipt

    return store.transact(operation, kind, signature, decide)
