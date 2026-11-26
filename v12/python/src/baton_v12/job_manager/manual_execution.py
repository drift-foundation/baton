"""Bridge owner selections to the ordinary single-stage execution and its custody."""
from ..contracts import ContractRefusal
from . import cancellation, documents, job_control, manual, research, submission


def submitted(store, execution):
    return store._connection.execute("SELECT 1 FROM jobs WHERE job_id=?", (execution,)).fetchone() is not None


def collect_freezes(store, operations, now):
    read = getattr(operations, "research_freeze", None)
    if read is None or (job_control.watermark_in(store._connection) or now) > now:
        return
    # Before expiry on every sweep (including reconcile), and again after the
    # exchange. The worker control transaction can survive a crash between them.
    rows = store._connection.execute(
        "SELECT p.job_id,p.phase,p.frozen,p.held_cause,e.attempt_id "
        "FROM manual_phases p JOIN stages s ON s.job_id=p.execution_job_id JOIN episodes e USING(stage_id) "
        "WHERE p.selected_at IS NOT NULL AND (p.frozen IS NULL OR (p.settled_at IS NULL AND p.held_cause IS NULL))"
    ).fetchall()
    for row in rows:
        evidence = read(row["attempt_id"])
        if evidence is not None:
            frozen, cause = evidence
            if row["frozen"] is None or cause != row["held_cause"]:
                manual.record_freeze(store, row["job_id"], row["phase"], frozen, cause)


def prepare(store, operations, now):
    """Only selected phases get a submission. Its identity survives a manager crash."""
    collect_freezes(store, operations, now)
    owner_jobs = manual.snapshot(store, now)
    if any(phase["state"] == "selected" for job in owner_jobs for phase in job["phases"]):
        job_control.observe(store, now)
    for job in owner_jobs:
        for phase in job["phases"]:
            if phase["state"] != "selected":
                continue
            execution = phase["execution_job_id"]
            if job["budget"]["timing"] != "trusted":
                continue
            if phase["frozen"] and (not job["budget"]["expired"] or phase["frozen"]["frozen_at"] <= job["budget"]["deadline_at"]):
                continue
            existing = submitted(store, execution)
            if job["budget"]["expired"] and existing:
                if not cancellation.fence_of(store, execution):
                    job_control.expire(store, job_id=execution, trigger="job-deadline", stage_id=None,
                                       deadline_at=job["budget"]["deadline_at"], observed_at=now)
                continue
            if existing:
                continue
            if job["budget"]["expired"]:
                manual.settle_phase(store, job["job_id"], phase["phase"], "exceptional",
                                    {"reason": "manual-job-deadline", "deadline_at": job["budget"]["deadline_at"]})
                continue
            prepare_phase = getattr(operations, "prepare_research", None)
            try:
                if prepare_phase is None:
                    raise ContractRefusal("refused", "precondition", "deployment lacks a research worker capability")
                document = prepare_phase(execution, phase["document"])
                owned = documents.owned_submission(document)
                if owned != research.prepare_submission(execution, phase["document"]):
                    raise ContractRefusal("integrity", "schema", "research submission differs from the pinned phase contract")
                submission._submit_owned(store, owned, manual_execution=execution)
            except ContractRefusal as exc:
                # Concurrent materialization can already have succeeded.
                if not submitted(store, execution):
                    manual.settle_phase(store, job["job_id"], phase["phase"], "exceptional",
                                        {"reason": "research-admission-refused", "code": exc.code, "detail": exc.message})


def _finish_selected(store, phase, outcome, result):
    try:
        manual.settle_phase(store, phase["job_id"], phase["phase"], outcome, result)
    except ContractRefusal:
        # The authenticated owner can concurrently dispose of a held result.
        # Only the winner's durable terminal decision supersedes our stale read.
        if manual.phase_for_execution(store, phase["execution_job_id"])["state"] == "selected":
            raise


def finish(store, operations, held):
    for entry in held.values():
        phase = entry.get("manual_phase")
        if phase is None or phase["state"] != "selected" or phase["timing"] != "trusted":
            continue
        canonical = manual.phase_for_execution(store, entry["stage"]["job_id"])
        if canonical["held_cause"] is not None or canonical["state"] != "selected":
            continue
        attempt = entry["episode"]
        if entry["state"] == "completed":
            if attempt is None or not cancellation.over(entry):
                continue
            # The worker owner validates the retained agreement and custody.
            try:
                result = operations.research_result(attempt["attempt_id"])
            except ContractRefusal as exc:
                _finish_selected(store, canonical, "exceptional",
                                 {"reason": "research-custody-refused", "code": exc.code, "detail": exc.message,
                                  "attempt_id": attempt["attempt_id"]})
                continue
            if result is not None:
                _finish_selected(store, canonical, "completed", result)
            continue
        ending = entry["history"][-1] if entry["history"] else {}
        reason = None
        if attempt is None and ending.get("ended_at"):
            reason = ending["ended_state"]
        elif entry["state"] == "exceptional" and cancellation.over(entry):
            reason = "research-execution-failed"
        elif (entry["receipts"].get("admit") or {}).get("state") == "refused" or entry.get("allocation_refusal"):
            reason = "research-admission-refused"
        elif entry.get("cancellation"):
            target = cancellation.target_state(entry, entry["observed"], entry["cancellation_targets"],
                                               entry["cancellation"]["requested_at"])
            if target == "retired-before-admission":
                reason = "execution-fenced-before-admission"
            elif target in ("ceased", "fenced-unstarted", "ended-before-request"):
                reason = "execution-fenced"
        if reason:
            _finish_selected(store, canonical, "exceptional",
                             {"reason": reason, "attempt_id": ending.get("attempt_id")})


def closed(connection, execution_job_id, now):
    gate = manual.execution_gate(connection, execution_job_id, now)
    if gate is None:
        return None
    if gate["state"] != "selected":
        return {"cause": "manual-selection", "state": gate["state"]}
    if gate["expired"]:
        return {"cause": "deadline", "first": {"trigger": "job-deadline", "stage_id": None, "deadline_at": gate["deadline_at"]}}
    if gate["timing"] != "trusted":
        return {"cause": "uncertain", "watermark": job_control.watermark_in(connection)}
    return None
