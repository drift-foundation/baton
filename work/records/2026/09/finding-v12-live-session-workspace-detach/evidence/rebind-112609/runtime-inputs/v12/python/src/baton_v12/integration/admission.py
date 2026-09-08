"""Cross-bind accepted candidate evidence before it receives a queue rank.

W101491.  The coordinator deliberately stores an ALREADY-PROVED eligibility
account.  This is the leaf that proves one: it re-reads the immutable
checkpoint/review surface, the checkpoint writer's assignment and frozen
output, the Authority proposal and its three policy receipts, and the Job that
owns the implementation Work.  Only after those sources agree does it call
``queue.enqueue``.

No caller supplies a member of the eligibility account.  ``line_id`` and
``proposal_id`` are selectors, while ``canonical_target_id`` and ``entry_id``
belong to the coordinator operation itself.  Everything copied into the entry
is read from its accepted producer in this call.
"""

import json

from ..authority.errors import Refusal as AuthorityRefusal
from ..contracts import ContractRefusal, check_relative_path, digest
from ..contracts.errors import name_value
from ..job_manager import documents as job_documents
from ..job_manager.submission import job_rows, stages_of
from ..worker_manager import boundaries
from ..worker_manager.attempts import assignment_of
from ..worker_manager.output import frozen_output_of
from ..worker_manager.review_cycles import (checkpoint_of,
                                             integration_checkpoint, line_of,
                                             writer_of)
from .queue import enqueue

__all__ = ["admit_candidate", "resolved_account"]


_PROPOSAL_MEMBERS = (
    "proposal_id", "assignment_ref", "decision", "result_id",
    "result_digest", "candidate_digest", "input_digest", "policy_digest",
    "target", "published_at")
_RECEIPT_MEMBERS = (
    "receipt_id", "kind", "proposal_id", "actor", "disposition",
    "candidate_digest", "target", "policy_generation", "recorded_at",
    "decision")
_RECEIPT_DISPOSITIONS = {
    "verification": "passed", "review": "accepted", "approval": "approved"}


def _refuse(message, *, category="refused", code="precondition"):
    raise ContractRefusal(category, code, message)


def _same(what, *values):
    if any(value != values[0] for value in values[1:]):
        _refuse(f"accepted evidence disagrees about {what}; one queue entry "
                f"describes one candidate")
    return values[0]


def _authority_call(action, what, *operands):
    try:
        return action(*operands)
    except AuthorityRefusal as refused:
        _refuse(f"the Authority refused {what}: {refused}")


def _assignment_ref(value):
    taken = boundaries.document(
        value, "an Authority proposal's assignment",
        required=("work_ref", "participant", "generation"))
    work = boundaries.document(
        taken["work_ref"], "an Authority proposal's Work reference",
        required=("authority_uuid", "work_id"))
    from .schema import check_authority

    check_authority(work["authority_uuid"],
                    what="the proposal assignment's Authority")
    boundaries.identity(work["work_id"], "the proposal assignment's Work")
    boundaries.text(taken["participant"],
                    "the proposal assignment's participant")
    boundaries.generation(taken["generation"],
                          "the proposal assignment's generation")
    return taken


def _proposal(authority, proposal_id):
    answer = _authority_call(authority.proposal, "the proposal read",
                             proposal_id)
    taken = boundaries.document(answer, "an Authority proposal",
                                required=_PROPOSAL_MEMBERS)
    boundaries.identity(taken["proposal_id"], "the proposal id")
    taken["assignment_ref"] = _assignment_ref(taken["assignment_ref"])
    # The Authority owns the decision's full contract.  Admission still owns
    # the crossing as a document rather than accepting an arbitrary object.
    taken["decision"] = boundaries.document(
        taken["decision"], "the proposal's authorization decision")
    boundaries.identity(taken["result_id"], "the proposal's result id")
    for member in ("result_digest", "candidate_digest", "input_digest",
                   "policy_digest", "target"):
        boundaries.text(taken[member], f"the proposal's {member}")
    boundaries.instant(taken["published_at"], "the proposal's publication")
    if taken["proposal_id"] != proposal_id:
        _refuse(f"the Authority answered proposal "
                f"{name_value(taken['proposal_id'])} when admission selected "
                f"{name_value(proposal_id)}")
    return taken


def _receipt(authority, proposal, kind):
    answer = _authority_call(authority.receipt, f"the {kind} receipt read",
                             proposal["proposal_id"], kind)
    if answer is None:
        _refuse(f"proposal {name_value(proposal['proposal_id'])} has no "
                f"{kind} receipt")
    taken = boundaries.document(answer, f"an Authority {kind} receipt",
                                required=_RECEIPT_MEMBERS)
    for member in ("receipt_id", "proposal_id"):
        boundaries.identity(taken[member], f"the {kind} receipt's {member}")
    for member in ("kind", "actor", "disposition", "candidate_digest",
                   "target"):
        boundaries.text(taken[member], f"the {kind} receipt's {member}")
    boundaries.instant(taken["recorded_at"], f"the {kind} receipt's instant")
    taken["decision"] = boundaries.document(
        taken["decision"], f"the {kind} receipt's authorization decision")
    if kind == "approval":
        boundaries.generation(taken["policy_generation"],
                              "the approval's policy generation")
        if taken["policy_generation"] < 1:
            _refuse("the approval's policy generation counts from one",
                    category="integrity", code="schema")
    elif taken["policy_generation"] is not None:
        _refuse(f"the {kind} receipt carries an approval policy generation")
    expected = _RECEIPT_DISPOSITIONS[kind]
    if taken["kind"] != kind or taken["disposition"] != expected:
        _refuse(f"proposal {name_value(proposal['proposal_id'])} needs a "
                f"{kind} receipt with disposition {name_value(expected)}")
    _same("the proposal identity", proposal["proposal_id"],
          taken["proposal_id"])
    _same("the candidate digest", proposal["candidate_digest"],
          taken["candidate_digest"])
    _same("the expected target revision", proposal["target"], taken["target"])
    return taken


def _job_for(jobs, work_id):
    matches = []
    for job in job_rows(jobs):
        for stage in stages_of(jobs, job["job_id"]):
            if stage["kind"] == "implementation" and stage["work_id"] == work_id:
                matches.append(job)
    if len(matches) != 1:
        _refuse(f"Work {name_value(work_id)} belongs to {len(matches)} Job "
                f"implementation stages; admission needs exactly one accepted "
                f"Job to own its input, policy and test scope")
    job = matches[0]
    try:
        scope = json.loads(job["test_scope"])
    except (TypeError, ValueError):
        _refuse(f"Job {name_value(job['job_id'])} has no readable test scope",
                category="integrity", code="schema")
    if type(scope) is not list or len(scope) > job_documents.MAX_JOBS:
        _refuse(f"Job {name_value(job['job_id'])} has a malformed test scope",
                category="integrity", code="schema")
    owned = [check_relative_path(path, "an accepted Job test-scope path")
             for path in scope]
    if len(set(owned)) != len(owned):
        _refuse(f"Job {name_value(job['job_id'])} repeats a test-scope path",
                category="integrity", code="schema")
    return job, owned


def resolved_account(manager, jobs, authority, *, line_id, proposal_id):
    """The fifteen-member account, RE-RESOLVED from its accepted producers.

    THE PROOF WITHOUT THE ENQUEUE, and W101492's review is why it is separate.
    Admission is valid when an entry receives its rank and can be stale by the
    time that entry reaches the head of the queue: Authority may advance the
    canonical target, or the accepted evidence may cease to agree. So the same
    resolution has to run a second time, under the live grant and before any
    model is asked to write -- and it has to be the SAME resolution rather than
    a second reading of the same sources, or the two would drift exactly where
    it matters.

    `admit_candidate` is now this plus `enqueue`, which is what it always was;
    nothing about what it proves has changed.
    """
    boundaries.capability(getattr(manager, "_connection", None),
                          "the Worker Manager store")
    boundaries.capability(getattr(jobs, "_connection", None),
                          "the Job store")
    from .schema import check_authority

    job_authority = check_authority(
        getattr(jobs, "authority_uuid", None),
        what="the Job store's Authority binding")
    for name in ("proposal", "receipt", "canonical_target"):
        boundaries.capability(getattr(authority, name, None),
                              f"the Authority's {name} read")
    boundaries.identity(line_id, "a development line id")
    boundaries.identity(proposal_id, "an Authority proposal id")

    accepted = integration_checkpoint(manager, line_id)
    if accepted is None:
        _refuse(f"development line {name_value(line_id)} has no accepted "
                f"integration checkpoint")
    line = line_of(manager, line_id)
    checkpoint = checkpoint_of(manager, accepted["checkpoint_id"])
    writer = writer_of(manager, checkpoint["writer_id"])
    assignment = assignment_of(manager, writer["runtime_attempt_id"])
    frozen = frozen_output_of(manager, writer["runtime_attempt_id"])
    if frozen is None:
        _refuse(f"checkpoint writer {name_value(writer['runtime_attempt_id'])} "
                f"has no frozen result")
    proposal = _proposal(authority, proposal_id)
    for kind in _RECEIPT_DISPOSITIONS:
        _receipt(authority, proposal, kind)
    current_target = _authority_call(authority.canonical_target,
                                     "the canonical target read")
    boundaries.text(current_target, "the Authority's canonical target")

    proposal_assignment = proposal["assignment_ref"]
    proposal_work = proposal_assignment["work_ref"]
    _same("the Authority", line["authority_uuid"],
          assignment["authority_uuid"], proposal_work["authority_uuid"],
          job_authority)
    _same("the Work", line["work_id"], assignment["work_id"],
          proposal_work["work_id"])
    _same("the assignment participant", writer["participant"],
          assignment["participant"], proposal_assignment["participant"])
    generation = _same("the assignment generation",
                       writer["assignment_generation"],
                       assignment["generation"],
                       proposal_assignment["generation"])
    _same("the line", line_id, line["line_id"], accepted["line_id"],
          checkpoint["line_id"], writer["line_id"])
    _same("the checkpoint", accepted["checkpoint_id"],
          checkpoint["checkpoint_id"], line["current_checkpoint_id"])
    _same("the checkpoint digest", accepted["checkpoint_digest"],
          checkpoint["checkpoint_digest"], digest(accepted["evidence"]))
    _same("the checkpoint evidence", accepted["evidence"],
          checkpoint["evidence"])
    _same("the path-set digest", accepted["evidence"]["path_set_digest"],
          checkpoint["path_set_digest"],
          digest(accepted["evidence"]["paths"]))
    _same("the frozen result identity", proposal["result_id"],
          frozen["result_id"])
    _same("the frozen result digest", proposal["result_digest"],
          frozen["manifest_digest"])
    if frozen["disposition"] != "completed":
        _refuse(f"checkpoint writer result is "
                f"{name_value(frozen['disposition'])}; only completed output "
                f"is an integration candidate")
    _same("the expected target revision", proposal["target"], current_target)

    job, scope = _job_for(jobs, proposal_work["work_id"])
    _same("the input digest", proposal["input_digest"], job["input_digest"])
    _same("the policy digest", proposal["policy_digest"],
          job["policy_digest"])
    account = {
        "authority_uuid": assignment["authority_uuid"],
        "work_id": assignment["work_id"],
        "assignment_generation": generation,
        "line_id": accepted["line_id"],
        "checkpoint_id": accepted["checkpoint_id"],
        "verdict_id": accepted["verdict_id"],
        "checkpoint_digest": accepted["checkpoint_digest"],
        "proposal_id": proposal["proposal_id"],
        "candidate_digest": proposal["candidate_digest"],
        "result_id": proposal["result_id"],
        "result_digest": proposal["result_digest"],
        "profile_kind": accepted["evidence"]["profile"],
        "expected_target_revision": proposal["target"],
        "path_set_digest": accepted["evidence"]["path_set_digest"],
        "scope_digest": digest(scope),
    }
    return account


def admit_candidate(store, manager, jobs, authority, *, canonical_target_id,
                    entry_id, line_id, proposal_id):
    """Prove and enqueue one accepted candidate account.

    Every read occurs before ``enqueue``.  Consequently any missing, stale or
    cross-wired source refuses without allocating a rank or writing a refused
    coordinator operation.  Exact retries reach the coordinator only with the
    same producer-derived account and replay its first entry and rank.
    """
    boundaries.capability(getattr(store, "_connection", None),
                          "the integration coordinator store")
    boundaries.identity(canonical_target_id, "a canonical target id")
    boundaries.identity(entry_id, "an integration entry id")
    account = resolved_account(manager, jobs, authority, line_id=line_id,
                               proposal_id=proposal_id)
    return enqueue(store, canonical_target_id=canonical_target_id,
                   entry_id=entry_id, eligibility=account)
