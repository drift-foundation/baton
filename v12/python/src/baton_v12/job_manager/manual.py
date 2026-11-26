"""Owner-paced Jobs. Selection and settlement are the two clock boundaries."""
import json
import re
from datetime import datetime, timedelta

from ..contracts import ContractRefusal, canonical_text, check_relative_path, digest
from ..worker_manager import boundaries
from . import job_control
from .schema import check_authority
from .store import job_signature


def _refuse(reason):
    raise ContractRefusal("integrity", "schema", reason)


def _key(value, label):
    if type(value) is not str or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]{0,127}", value):
        _refuse(f"{label} requires a bounded stable name")
    return value


EXECUTION_PREFIX = "manual-phase-"


def execution_job_id(job_id, phase):
    return EXECUTION_PREFIX + digest([_key(job_id, "Job"), _key(phase, "phase")])[7:]


def generated_work_id(authority_uuid, execution):
    """Name a phase's one Work in its actual Authority across retries."""
    check_authority(authority_uuid, what="MANUAL phase Authority")
    if type(execution) is not str or not re.fullmatch(EXECUTION_PREFIX + "[0-9a-f]{64}", execution):
        _refuse("generated Work needs an exact MANUAL phase execution identity")
    namespace = digest(["manual.research-work", authority_uuid, execution])
    return f"{authority_uuid[:8]}-W{1 + int(namespace[7:39], 16)}"


def _scope(value):
    if type(value) is not list or not value or len(value) > 256:
        _refuse("research scope requires an explicit nonempty list of at most 256 paths")
    paths = [check_relative_path(path, "research scope") for path in value]
    if len(set(paths)) != len(paths):
        _refuse("research scope paths must be distinct")
    return paths


def _act(store, name, job_id, phase, facts, apply):
    kind = "manual." + name
    target = {"job_id": _key(job_id, "Job")}
    if phase is not None:
        target["phase"] = _key(phase, "phase")
    operation = kind + ":" + digest(target)[7:]

    def perform(connection):
        now = store._now()
        watermark = job_control.advance_watermark(connection, now)
        if watermark > now:
            _refuse("clock is earlier than the persisted Job Store watermark")
        apply(connection, now)
        result = dict(target, action=name, operation_id=operation, recorded_at=now)
        if phase is not None:
            result["execution_job_id"] = execution_job_id(job_id, phase)
        return result

    return store.transact(operation, kind, job_signature(kind, dict(target, **facts)), perform)


def _open(connection, job_id):
    row = connection.execute("SELECT * FROM manual_jobs WHERE job_id=?", (job_id,)).fetchone()
    if row is None:
        _refuse("unknown MANUAL Job")
    if row["closed_at"]:
        _refuse("the MANUAL Job has been closed")
    return row


def _phase(connection, job_id, phase):
    row = connection.execute("SELECT * FROM manual_phases WHERE job_id=? AND phase=?", (job_id, phase)).fetchone()
    if row is None:
        _refuse(f"unknown phase {phase} on the MANUAL Job")
    return row


def _phase_rows(connection, job_id):
    return list(connection.execute("SELECT * FROM manual_phases WHERE job_id=? ORDER BY selected_at,phase", (job_id,)))


def refuse_reserved(connection, job_id, submission_id):
    """Ordinary creation, fresh attempts and submission share the same names."""
    if connection.execute(
            "SELECT 1 FROM manual_jobs WHERE job_id=? UNION ALL "
            "SELECT 1 FROM manual_phases WHERE execution_job_id IN (?, ?) LIMIT 1",
            (job_id, job_id, submission_id)).fetchone():
        raise ContractRefusal("refused", "precondition", "identity belongs to an owner-paced Job or phase")


def _require_available(connection, job_id, submission_id=None):
    if connection.execute(
            "SELECT 1 FROM jobs WHERE job_id=? UNION ALL "
            "SELECT 1 FROM fresh_attempts WHERE job_id=? OR submission_id=? UNION ALL "
            "SELECT 1 FROM template_jobs WHERE job_id=? OR submission_id=? LIMIT 1",
            (job_id, job_id, submission_id, job_id, submission_id)).fetchone():
        _refuse("Job or submission identity is already in use")
    if submission_id is not None and connection.execute(
            "SELECT 1 FROM operations WHERE operation_id=?", ("submission.record:" + submission_id,)).fetchone():
        _refuse("research submission identity already has a recorded operation")


def create(store, job_id, document):
    doc = boundaries.document(document, "a MANUAL Job", required=("scope", "wall_seconds"), optional=("job_id",))
    if doc.pop("job_id", job_id) != job_id:
        _refuse("MANUAL Job identity differs from its creation request")
    if _key(job_id, "Job").startswith(EXECUTION_PREFIX):
        _refuse("MANUAL Job name occupies the reserved phase execution namespace")
    _scope(doc["scope"])

    def apply(connection, now):
        boundaries.deadline(now, doc["wall_seconds"], "the MANUAL wall budget")
        _require_available(connection, job_id)
        connection.execute("INSERT INTO manual_jobs(job_id, document, created_at) VALUES (?,?,?)",
                           (job_id, canonical_text(doc), now))

    return _act(store, "create", job_id, None, {"document": doc}, apply)


def add_phase(store, job_id, phase, document):
    doc = boundaries.document(document, "a research assignment",
                              required=("kind", "statement", "scope", "depends_on", "work_id", "profile_name", "profile_digest",
                                        "input_digest", "policy_digest"), optional=("source_commit", "work_origin"))
    if "work_origin" in doc and (doc["work_origin"] != "generated" or doc["work_id"] != generated_work_id(store.authority_uuid, execution_job_id(job_id, phase))):
        _refuse("generated research Work must have the identity of this Authority, Job and phase")
    if "source_commit" in doc and (type(doc["source_commit"]) is not str or not re.fullmatch(r"(?:[a-f0-9]{40}|[a-f0-9]{64})", doc["source_commit"])):
        _refuse("research source_commit must be a full Git object identity")
    if doc["kind"] != "research":
        _refuse("a MANUAL phase requires the research result contract")
    for key in ("statement", "work_id", "profile_name"):
        boundaries.text(doc[key], "research " + key)
    for key in ("input_digest", "policy_digest", "profile_digest"):
        if type(doc[key]) is not str or not re.fullmatch(r"sha256:[0-9a-f]{64}", doc[key]):
            _refuse(f"research {key} requires a SHA-256 digest")
    paths = _scope(doc["scope"])
    dependencies = doc["depends_on"]
    if type(dependencies) is not list:
        _refuse("phase dependencies must name a list of earlier phases")
    for dependency in dependencies:
        _key(dependency, "prerequisite")
    if len(set(dependencies)) != len(dependencies) or phase in dependencies:
        _refuse("phase prerequisites must be distinct earlier phases")

    def apply(connection, now):
        scope = json.loads(_open(connection, job_id)["document"])["scope"]
        if any(not any(path == root or path.startswith(root + "/") for root in scope) for path in paths):
            _refuse("research assignment exceeds the MANUAL Job scope")
        for dependency in dependencies:
            _phase(connection, job_id, dependency)
        execution = execution_job_id(job_id, phase)
        _require_available(connection, execution, execution)
        connection.execute("INSERT INTO manual_phases(job_id, phase, execution_job_id, document) VALUES (?,?,?,?)",
                           (job_id, phase, execution, canonical_text(doc)))

    return _act(store, "add-phase", job_id, phase, {"document": doc}, apply)


def _budget(limit, rows, now, watermark):
    """Rows are sorted by selection instant. Charge only previously uncovered time."""
    effective = datetime.fromisoformat(max(now, watermark or now))
    elapsed = timedelta()
    covered_until = None
    deadline = None
    allowance = timedelta(seconds=limit)
    for row in rows:
        if row["selected_at"] is None:
            continue
        start = datetime.fromisoformat(row["selected_at"])
        frozen = json.loads(row["frozen"]) if row["frozen"] else None
        stop = frozen["frozen_at"] if frozen else row["settled_at"]
        end = datetime.fromisoformat(stop) if stop else effective
        if covered_until is not None:
            start = max(start, covered_until)
        if end >= start:
            if deadline is None and (not stop or elapsed + end - start >= allowance):
                deadline = start + allowance - elapsed
            elapsed += end - start
            covered_until = end
    milliseconds = elapsed // timedelta(milliseconds=1)
    remaining = max(0, limit * 1000 - milliseconds)
    return {"limit_seconds": limit, "charged_milliseconds": milliseconds,
            "charged_seconds": milliseconds // 1000, "remaining_seconds": (remaining + 999) // 1000,
            "expired": elapsed >= allowance, "timing": "uncertain" if watermark and watermark > now else "trusted",
            "deadline_at": None if deadline is None else deadline.isoformat(timespec="milliseconds").replace("+00:00", "Z")}


def _state(row):
    return row["outcome"] or ("selected" if row["selected_at"] else "planned")


def execution_gate(connection, execution_job_id, now):
    row = connection.execute("SELECT p.*,j.document AS job_document FROM manual_phases p JOIN manual_jobs j USING(job_id) "
                             "WHERE p.execution_job_id=?", (execution_job_id,)).fetchone()
    if row is None:
        return None
    budget = _budget(json.loads(row["job_document"])["wall_seconds"], _phase_rows(connection, row["job_id"]),
                     now, job_control.watermark_in(connection))
    return dict(budget, frozen=json.loads(row["frozen"]) if row["frozen"] else None, state=_state(row), job_id=row["job_id"], phase=row["phase"])


def start_phase(store, job_id, phase):
    def apply(connection, now):
        _open(connection, job_id)
        row = _phase(connection, job_id, phase)
        for dependency in json.loads(row["document"])["depends_on"]:
            if _phase(connection, job_id, dependency)["outcome"] != "completed":
                _refuse(f"phase {phase} waits on {dependency}")
        budget = execution_gate(connection, row["execution_job_id"], now)
        if budget["expired"]:
            _refuse("the MANUAL Job wall budget is exhausted")
        boundaries.deadline(now, budget["remaining_seconds"], "the remaining MANUAL wall budget")
        connection.execute("UPDATE manual_phases SET selected_at=? WHERE job_id=? AND phase=?", (now, job_id, phase))

    return _act(store, "start-phase", job_id, phase, {}, apply)


def record_freeze(store, job_id, phase, frozen, held_cause):
    """Bind the worker-side freeze to the phase's journalled research episode."""
    def apply(connection, now):
        row = _phase(connection, job_id, phase)
        owner = connection.execute(
            "SELECT s.work_id FROM stages s JOIN episodes e USING(stage_id) "
            "WHERE s.job_id=? AND s.kind='research' AND e.attempt_id=?",
            (row["execution_job_id"], frozen["attempt_id"])).fetchone()
        if (owner is None or frozen["authority_uuid"] != store.authority_uuid or owner["work_id"] != frozen["work_id"]
                or json.loads(row["document"])["work_id"] != frozen["work_id"]
                or not row["selected_at"] or not row["selected_at"] <= frozen["frozen_at"] <= (row["settled_at"] or now)):
            _refuse("research freeze disagrees with the selected attempt, Work, or time interval")
        encoded = canonical_text(frozen)
        if row["frozen"] is not None and row["frozen"] != encoded:
            _refuse("recorded research freeze changed")
        connection.execute("UPDATE manual_phases SET frozen=?,held_cause=COALESCE(held_cause,?) WHERE job_id=? AND phase=?",
                           (encoded, held_cause, job_id, phase))

    action = "observe-freeze" if held_cause is None else "observe-held-freeze"
    return _act(store, action, job_id, phase, {"frozen": frozen, "held_cause": held_cause}, apply)


def settle_phase(store, job_id, phase, outcome, result):
    if outcome not in ("completed", "exceptional") or type(result) is not dict or not result:
        _refuse("settlement requires a terminal phase outcome and its evidence")

    def apply(connection, now):
        row = _phase(connection, job_id, phase)
        if not row["selected_at"]:
            _refuse("a phase must be selected before settlement")
        if row["outcome"] is not None or row["held_cause"] is not None:
            _refuse("a held or settled MANUAL phase cannot be automatically settled")
        connection.execute("UPDATE manual_phases SET settled_at=?,outcome=?,result=? WHERE job_id=? AND phase=?",
                           (now, outcome, canonical_text(result), job_id, phase))

    return _act(store, "settle-phase", job_id, phase, {"outcome": outcome, "result": result}, apply)


def close_job(store, job_id):
    def apply(connection, now):
        _open(connection, job_id)
        if connection.execute("SELECT 1 FROM manual_phases WHERE job_id=? AND selected_at IS NOT NULL AND settled_at IS NULL LIMIT 1", (job_id,)).fetchone():
            _refuse("MANUAL Job has selected unsettled phases")
        connection.execute("UPDATE manual_jobs SET closed_at=? WHERE job_id=?", (now, job_id))

    return _act(store, "close-job", job_id, None, {}, apply)


def _phase_snapshot(row):
    return dict(job_id=row["job_id"], phase=row["phase"], execution_job_id=row["execution_job_id"],
                document=json.loads(row["document"]), state=_state(row), selected_at=row["selected_at"],
                frozen=json.loads(row["frozen"]) if row["frozen"] else None, held_cause=row["held_cause"],
                settled_at=row["settled_at"], result=json.loads(row["result"]) if row["result"] else None)


def phase_for_execution(store, execution_job_id):
    row = store._connection.execute("SELECT * FROM manual_phases WHERE execution_job_id=?", (execution_job_id,)).fetchone()
    return None if row is None else _phase_snapshot(row)


def snapshot_in(connection, now):
    watermark = job_control.watermark_in(connection)
    result = []
    for job in connection.execute("SELECT * FROM manual_jobs ORDER BY job_id"):
        document = json.loads(job["document"])
        rows = _phase_rows(connection, job["job_id"])
        phases = [_phase_snapshot(row) for row in rows]
        result.append(dict(job_id=job["job_id"], mode="manual", lifecycle="closed" if job["closed_at"] else "open",
                           created_at=job["created_at"], closed_at=job["closed_at"], document=document, phases=phases,
                           budget=_budget(document["wall_seconds"], rows, now, watermark)))
    return result


def snapshot(store, now=None):
    with store.read_snapshot():
        return snapshot_in(store._connection, now or store._now())
