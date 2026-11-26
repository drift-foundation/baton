"""The owner's record that an ordinary Job's accepted candidate was integrated. W385263.

Owner decisions 2026-11-26 (W385263 ruling, amended by M386422): an ordinary
implementation -> review delivery reads READY FOR INTEGRATION once every phase
finished and the exact current, retained and importable candidate has a
matching accepted verdict. After integrating it, the owner records the
EXISTING target commit against that specific Job and accepted candidate
through the shared API and the CLI. The receipt is persisted, an identical
retry returns it unchanged, a conflicting receipt or a mismatched candidate is
refused, and status, monitor and TUI show DONE from that receipt -- also with
every service stopped. MANUAL closure (`manual.close_job`) is unchanged.

ONE RECEIPT PER JOB. The operation identity is derived from the Job alone and
the signature from (Job, candidate head, target commit), so the journal
(`JobStore.transact`) replays an identical retry and refuses a second,
different receipt for the same Job as a collision. Nothing about the Job's
stages, attempts, lines, custody or verdict changes; the receipt sits beside
them and `receipt_of` reads it back for the status document.

WHAT IS CHECKED BEFORE ANYTHING IS WRITTEN (a refusal records nothing):
  * the Job is an ordinary report-and-hold Job (MANUAL closes on its own path);
  * every phase is `completed`;
  * the review verdict is the one bound to this Job's review attempt, it is
    `accepted`, and its checkpoint is the line's integration-eligible
    (retained, importable) candidate -- `review_verdicts.matching`;
  * the candidate the owner names is that verdict's head commit;
  * the target commit the owner names exists in the target repository and its
    tree is the accepted candidate's tree. This first form records exact-tree
    integrations (M386415: 340f8674 and 6540775d share tree 35686824); a
    target whose tree differs is refused rather than recorded as this candidate.
"""
import json
import os
import re
import subprocess

from ..contracts import ContractRefusal, digest
from ..worker_manager import boundaries
from . import job_control, projection, review_verdicts
from .store import job_signature

KIND = "job.integration-recorded"
_OBJECT = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")


def operation_of(job_id):
    """The one integration-receipt operation identity of this Job."""
    boundaries.identity(job_id, "a Job identity")
    return KIND + ":" + digest({"job_id": job_id}).split(":", 1)[1]


def _refuse(message):
    raise ContractRefusal("refused", "precondition", message)


def _git(repository, *argv):
    """One read-only Git read of LITERAL objects (M386429).

    Replacement refs (`refs/replace/*`) would let a repository report another
    commit's tree for an existing commit, so an immutable receipt is read with
    replacement disabled twice over: the `--no-replace-objects` option and
    `GIT_NO_REPLACE_OBJECTS`. Every inherited `GIT_*` variable is dropped first,
    so no ambient directory, index or object-store override reaches the read.
    """
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment.update(GIT_OPTIONAL_LOCKS="0", GIT_NO_REPLACE_OBJECTS="1")
    done = subprocess.run(["git", "--no-replace-objects", "-C", repository, *argv], env=environment,
                          capture_output=True, text=True, timeout=60)
    return done.stdout.strip() if done.returncode == 0 else None


def target_commit(repository, commit):
    """The full commit and tree of an EXISTING target commit, read-only, or a refusal."""
    if type(repository) is not str or not os.path.isabs(repository):
        _refuse("the target repository is an absolute path")
    if type(commit) is not str or not re.fullmatch(r"[0-9a-f]{7,64}", commit):
        _refuse("the target commit is a hexadecimal commit name")
    full = _git(repository, "rev-parse", "--verify", "--quiet", commit + "^{commit}")
    if not full or not _OBJECT.fullmatch(full):
        _refuse(f"commit {commit} does not exist in the target repository {repository}")
    tree = _git(repository, "rev-parse", "--verify", "--quiet", full + "^{tree}")
    if not tree or not _OBJECT.fullmatch(tree):
        _refuse(f"the tree of commit {full} cannot be read in {repository}")
    return {"commit": full, "tree": tree}


def accepted_candidate(store, job_id, operations, control):
    """This Job's phases and its retained, importable accepted candidate, or a refusal."""
    snapshot = projection.materialized(store)
    job = next((row for row in snapshot["jobs"] if row["job_id"] == job_id), None)
    if job is None:
        manual = store._connection.execute("SELECT 1 FROM manual_jobs WHERE job_id=?", (job_id,)).fetchone()
        _refuse(f"Job {job_id} is MANUAL and closes through close-job"
                if manual else f"no ordinary Job {job_id} is recorded in this store")
    if job["terminal_policy"] != "report-and-hold":
        _refuse(f"Job {job_id} is not a report-and-hold Job")
    held = projection.stage_states(store, operations, snapshot=snapshot)
    rows = snapshot["stages_by_job"][job_id]
    phases, review = [], []
    for row in rows:
        entry = held[row["stage_id"]]
        live = entry.get("episode") or {}
        assignment = ((entry.get("observed") or {}).get("runtime") or {}).get("assignment") or {}
        phases.append({"stage_id": row["stage_id"], "state": entry["state"], "attempt_id": live.get("attempt_id")})
        if row["kind"] == "review":
            review.append((live.get("attempt_id"), assignment.get("generation")))
    unfinished = [phase["stage_id"] + " (" + str(phase["state"]) + ")" for phase in phases if phase["state"] != "completed"]
    if not phases or unfinished:
        _refuse(f"Job {job_id} has phases that have not finished: {', '.join(unfinished) or 'none planned'}")
    if len(review) != 1:
        _refuse(f"Job {job_id} has {len(review)} review phases; one accepted review decides its candidate")
    verdict = review_verdicts.matching(control, attempt_id=review[0][0], generation=review[0][1])
    if verdict is None or verdict["disposition"] != "accepted" or verdict["importable"] is not True:
        _refuse(f"Job {job_id} has no accepted verdict on its retained, importable candidate")
    return phases, verdict


def record(store, job_id, *, candidate, target, actor, operations, control):
    """Record the EXISTING target commit for this Job's accepted candidate; the receipt.

    `candidate` is the accepted head commit the owner integrated; `target` is
    `target_commit(...)`'s answer; `actor` is the verified owner binding;
    `operations` and `control` are the read-only surfaces the phases and the
    verdict are read through.
    """
    operation = operation_of(job_id)
    if type(candidate) is not str or not _OBJECT.fullmatch(candidate):
        _refuse("the candidate is the accepted head commit, in full")
    if type(target) is not dict or not _OBJECT.fullmatch(str(target.get("commit"))) or not _OBJECT.fullmatch(str(target.get("tree"))):
        _refuse("the target is an existing commit and its tree")
    signature = job_signature(KIND, {"job_id": job_id, "candidate": candidate, "commit": target["commit"]})
    existing = store.operation_record(operation)
    if existing is not None and existing["signature"] != signature:
        recorded = receipt_of(store, job_id) or {}
        _refuse(f"Job {job_id} already has an integration receipt (candidate "
                f"{(recorded.get('candidate') or {}).get('head_object')}, commit "
                f"{(recorded.get('target') or {}).get('commit')}); a different one is refused")
    found, value = store.replay(operation, signature, kind=KIND)
    if found:
        return value
    if type(actor) is not dict or not actor.get("participant") or not actor.get("principal"):
        _refuse("recording an integration requires the verified owner binding")
    phases, verdict = accepted_candidate(store, job_id, operations, control)
    if candidate != verdict["head_object"]:
        _refuse(f"candidate {candidate} is not Job {job_id}'s accepted candidate {verdict['head_object']}")
    if target["tree"] != verdict["tree_object"]:
        _refuse(f"commit {target['commit']} has tree {target['tree']}, not the accepted candidate's tree "
                f"{verdict['tree_object']}; this form records exact-tree integrations only")

    def perform(connection):
        now = store._now()
        if job_control.advance_watermark(connection, now) > now:
            _refuse("the clock is earlier than the persisted Job Store watermark")
        return {"job_id": job_id, "action": "record-integration", "operation_id": operation, "recorded_at": now,
                "recorded_by": {"participant": actor["participant"], "principal": actor["principal"]},
                "candidate": {name: verdict[name] for name in ("checkpoint_id", "line_id", "verdict_id", "base_object", "head_object", "tree_object")},
                "target": {"commit": target["commit"], "tree": target["tree"]},
                "phases": phases}

    return store.transact(operation, KIND, signature, perform)


def receipt_of(store, job_id):
    """The committed integration receipt of this Job, or None."""
    record_ = store.operation_record(operation_of(job_id))
    if record_ is None or record_["kind"] != KIND or record_["state"] != "committed":
        return None
    result = record_["result"]
    if isinstance(result, str):
        result = json.loads(result)
    return result if type(result) is dict and result.get("job_id") == job_id else None
