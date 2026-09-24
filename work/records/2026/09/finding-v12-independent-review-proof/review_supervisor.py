"""Drive ONE bounded managed review of a retained proposal, and stop.

W239533. THE LOCAL SPECIALIZATION review 2026-09-23T05:08:49Z proposed and
owner reroute 247154 selected, in preference to the two options this
implementer had framed: it neither copies W239528's accepted `baseline.py`
wholesale nor edits it.

WHAT IS IMPORTED UNCHANGED, and it is most of the machine. Every one of these
is already kind-agnostic -- none of them mentions `implementation` -- so a
review run uses the accepted bytes rather than a second copy of them:

    Termination              the signal handler held around the whole run
    AdmissionGate            caps are `{kind: count}`; `review` is a kind
    survey                   what the store held before any owner act
    _guarded                 one read, its failure named rather than raised
    _attempts_of, _refresh   the canonical attempt/state read
    _terminal                every configured stage reached its end
    _observation, _cleanups  the progress signal and the cleanup journal
    _cancel_active           fence, then order quiescence, through the port
    _origin                  did this run start that runtime, or find it
    _publish, _moment        the retained outcome and its instant
    _turn_ceiling            the Job's declared per-turn ceiling
    verify_imported_sources  the bound manager source, proved
    verify_worker_image      the bound image, proved
    _compose, _engine_inspect        the production composition and engine

WHAT IS LOCAL, and it is only what a review actually differs in:

    held_packet              this packet's schema, bounds and subject
    supervise                the orchestration body, `review`-shaped
    _verdict_evidence        the checkpoint-bound verdict, in place of the
                             proposal/attribution evidence

THE IMPORTED BYTES ARE BOUND. `BASELINE_SHA256` is the digest review
2026-09-23T05:08:49Z recorded for the accepted `baseline.py`, and
`held_packet` refuses before anything opens if the file this process imported
is not those bytes. Reuse that cannot say WHICH bytes it reused is not reuse,
it is a dependency.

NOTHING HERE MONKEYPATCHES `baseline`. No global of that module is assigned,
no attribute of it is replaced, and `test_review_supervisor` holds this
program to that by parsing it. Its `KINDS` constant stays exactly what it is:
a statement about W239528's run, not a switch.

NO CORRECTION ON CHANGES-REQUESTED IS THE SELECTED CONTRACT, and it is now
IMPLEMENTED rather than merely reported. Two earlier versions of this docstring
got it wrong in opposite directions: one claimed an opened round "belongs to
W236087", which review 2026-09-23T11:30:47Z R4 refused as a scope change
proposed by prose; the next held the run AFTER the round had been opened, which
review 2026-09-23T11:56:42Z R4 refused because "returning held does not undo
that store effect".

Owner selection 247421 added `correction_policy` to the stage-execution
deployment. `StageComposition.routed` honours it BEFORE calling
`review_driver.open_correction`, `review_bindings` composes `decline`, and
`held_packet` refuses a packet whose deployment does not carry it -- so the
boundary is a precondition of running rather than a promise. What is declined
is the ROUND, never the verdict.

A `changes-requested` verdict is a SUCCESSFUL review and
`test_review_lifecycle` drives one end to end: settled, one attributed verdict,
zero correction rounds and zero correction containers.

A `changes-requested` or `rejected` verdict is a SUCCESSFUL review. This
program has no preference between the three dispositions and records whichever
the reviewer actually returned; what it refuses to do is call a run successful
that produced no attributed verdict at all.
"""

import argparse
import hashlib
import json
import os
import sys

import baseline
from baseline import (AdmissionGate, STALLED_TICKS, SupervisorInterrupted,
                      SupervisorRefusal, Termination, _attempts_of, _cancel_active,
                      _cleanups, _compose, _digest_of_file, _document,
                      _engine_inspect, _guarded, _moment, _object_name,
                      _observation, _origin, _pin, _publish, _refresh,
                      _relative, _terminal, _turn_ceiling, _whole_number,
                      survey, verify_imported_sources, verify_worker_image)

__all__ = ["PACKET_SCHEMA", "OUTCOME_SCHEMA", "KINDS", "BASELINE_SHA256",
           "held_packet", "supervise", "main"]

PACKET_SCHEMA = "baton.independent-review-packet/1"
OUTCOME_SCHEMA = "baton.independent-review-outcome/1"

# THE ONE STAGE KIND THIS PACKET SERVES, closed. An `implementation` stage
# reaching the admission gate is not a smaller version of this run -- it is
# W239528's workload, already produced and frozen, or W236087's correction --
# so it is refused by name rather than admitted under whichever cap is spare.
KINDS = ("review",)

# THE ACCEPTED `baseline.py` THIS PROGRAM IMPORTS. Recorded by review
# 2026-09-23T05:08:49Z; `held_packet` proves it before anything opens.
BASELINE_SHA256 = \
    "f27f3cd766f9271c4b3eddb6c657bca4770d18c11a74f377e717bef23df18fd5"

# The verdicts `claude_agent._review_report` may write and the manager may
# read back. All three are valid review results; none of them is this run's
# preferred answer.
VERDICTS = ("accepted", "changes-requested", "rejected")

# THE POLICY A REVIEW-ONLY DEPLOYMENT MUST CARRY. Mirrored from
# `stage_execution` rather than imported, because `held_packet` runs BEFORE
# `verify_imported_sources` has proved which `tools` this process resolved --
# importing the value from an unproved tree to decide whether to trust that
# tree would be circular. The deterministic suite asserts the two agree.
DECLINE_CORRECTION = "decline"

# WHY A CORRECTION ROUND STILL HOLDS THIS RUN, now that it cannot ordinarily
# happen. The limitation this named is CLOSED: owner selection 247421 added
# `correction_policy`, `held_packet` refuses a packet whose deployment does not
# carry `decline`, and `StageComposition.routed` never reaches
# `open_correction` under it. The check below is therefore a belt-and-braces
# read of the Job store's own stage records rather than a report of something
# expected -- if a round appears anyway, the boundary did not hold and that is
# a fault worth holding on, not a state to accommodate.
CORRECTION_LIMITATION = (
    "a review-only deployment declines the correction round through "
    "`correction_policy: \"decline\"`, which `StageComposition.routed` honours "
    "before calling `review_driver.open_correction`, and this packet is "
    "refused without it. A round appearing anyway means that boundary did not "
    "hold, so this run reports it and refuses to call itself settled.")

_PACKET = ("schema", "run_id", "work", "claim", "note", "subject",
           "producer_run_root", "producer_control_store", "worker_image",
           "manager_runtime", "manager_source", "supervisor", "code_boundary",
           "deployment", "context", "submission", "criteria", "bounds",
           "outcome_path")
# NO `implementer_invocations` AND NO `corrections`. Carrying either as a zero
# would describe this run as an implementation that happens to make none.
_BOUNDS = ("turn_seconds", "total_seconds", "cleanup_seconds",
           "review_invocations", "retry")
_DEPLOYMENT = ("config_path", "config_sha256", "job_store", "control_store",
               "authority_store", "authority_uuid", "state_root")
_SUBMISSION = ("path", "sha256", "job_id")
_CRITERIA = ("path", "sha256", "content_digest")
# The members of the subject this program actually acts on. REQUIRED, not
# exact: `attachment.subject` composes the whole survey account -- the line's
# path, device and inode, its state and revision, the source it was
# materialized from, the checkpoint's reference name and path set -- and all
# of that belongs in the packet an operator reads. Holding the subject to an
# EXACT member list refused the real composition for carrying evidence, which
# is the wrong direction for a validator to fail in.
_SUBJECT = ("schema", "line_id", "checkpoint_id", "authority_uuid", "work_id",
            "declared_base", "base_object", "head_object", "tree_object",
            "checkpoint_digest", "producer")


def _refuse(message):
    raise SupervisorRefusal(message)


def held_packet(path):
    """Read the packet and PROVE every artifact it binds, before anything opens.

    Nothing durable is touched here and no store is opened: a packet whose
    criteria bytes, deployment configuration, submission, manager source or
    supervisor program have moved since it was reviewed is refused with the
    artifact named.

    AND THE IMPORTED BASELINE IS ONE OF THOSE ARTIFACTS. This program's
    orchestration is its own; its machine is W239528's, and a run that could
    not say which bytes of it were imported would be claiming reuse it cannot
    evidence.
    """
    with open(path, "rb") as handle:
        packet = json.loads(handle.read().decode("utf-8"))
    _document(packet, "the independent-review packet", _PACKET)
    if packet["schema"] != PACKET_SCHEMA:
        _refuse(f"this supervisor reads {PACKET_SCHEMA!r}; the packet names "
                f"{packet['schema']!r}")

    held = _digest_of_file(baseline.__file__)
    if held != BASELINE_SHA256:
        _refuse(f"this supervisor imports W239528's accepted `baseline.py` "
                f"for its termination, admission, discovery, cancellation, "
                f"cleanup and publication machinery, and the file it imported "
                f"hashes {held}. The accepted bytes are {BASELINE_SHA256}. "
                f"A specialization cannot vouch for machinery it cannot "
                f"identify.")

    bounds = _document(packet["bounds"], "the packet's bounds", _BOUNDS)
    _whole_number(bounds["turn_seconds"], "the per-turn bound")
    _whole_number(bounds["total_seconds"], "the overall bound")
    _whole_number(bounds["cleanup_seconds"], "the reserved cleanup bound")
    if bounds["retry"] is not False:
        _refuse("this supervisor never retries; the packet's bounds must say "
                "so with `retry: false`")
    # EXACTLY ONE. Two review turns on identical frozen bytes would be a second
    # opinion rather than a review, and zero answers nothing. Both are refused
    # before a store opens rather than discovered in the outcome.
    if bounds["review_invocations"] != 1:
        _refuse(f"this packet drives ONE review container; its bounds declare "
                f"{bounds['review_invocations']!r} review invocation(s).")
    if bounds["cleanup_seconds"] >= bounds["total_seconds"]:
        _refuse("the reserved cleanup bound is inside the overall bound, not "
                "beside it; reserve less than the whole run")

    subject = packet["subject"]
    if type(subject) is not dict:
        _refuse("the packet's subject is one document")
    absent = [one for one in _SUBJECT if one not in subject]
    if absent:
        _refuse(f"the packet's subject names no {', '.join(absent)}; the "
                f"subject is what says WHICH proposal this run reviews")
    for name in ("base_object", "head_object", "tree_object"):
        _object_name(subject[name], f"the subject's {name}")
    if subject["base_object"] != subject["declared_base"]:
        _refuse(f"the subject's declared base {subject['declared_base']!r} is "
                f"not the checkpoint's own base {subject['base_object']!r}; "
                f"a review judges the change the producer actually froze")
    if subject["head_object"] == subject["base_object"]:
        _refuse("the subject's head and base are the same object, so there is "
                "no change to review")

    deployment = _document(packet["deployment"], "the packet's deployment",
                           _DEPLOYMENT)
    _pin(deployment["config_path"], deployment["config_sha256"],
         "the deployment configuration")
    submission = _document(packet["submission"], "the packet's submission",
                           _SUBMISSION)
    _pin(submission["path"], submission["sha256"], "the submission")
    criteria = _document(packet["criteria"], "the packet's criteria",
                         _CRITERIA)
    _pin(criteria["path"], criteria["sha256"], "the review criteria")
    # THE CRITERIA THE WORKER READS ARE THE ONES THE MANIFEST SEALED. The
    # deployment's manifest carries a content digest over the exact bytes; a
    # pretty-printed copy of the same object is a different document at the
    # launch boundary, and the criteria are the whole of what makes this a
    # review rather than an unprompted turn.
    from baton_v12.contracts import digest_of_bytes

    with open(criteria["path"], "rb") as handle:
        body = handle.read()
    if digest_of_bytes(body) != criteria["content_digest"]:
        _refuse(f"the criteria at {criteria['path']!r} do not hash to the "
                f"content digest the packet seals; the reviewer would be "
                f"given a different document from the reviewed one")
    # THE NO-CORRECTION BOUNDARY IS A PRECONDITION OF RUNNING, not a promise.
    # Owner reroute 247421 selected the product change and requires the packet
    # to stay non-runnable until the boundary is in place; reading the
    # deployment document here is how "in place" becomes checkable before a
    # store opens.
    with open(deployment["config_path"], "rb") as handle:
        configured = json.loads(handle.read().decode("utf-8"))
    policy = configured.get("correction_policy")
    if policy != DECLINE_CORRECTION:
        _refuse(f"this deployment's correction policy is {policy!r} and a "
                f"review-only run requires {DECLINE_CORRECTION!r}. Without it "
                f"`StageComposition.routed` opens a correction round in this "
                f"Job store whenever the reviewer answers changes-requested, "
                f"which is a separately selected Job's work. The packet is "
                f"not runnable until the boundary is configured.")
    if deployment["control_store"] != packet["producer_control_store"]:
        _refuse(f"the deployment opens control store "
                f"{deployment['control_store']!r} and the subject was read "
                f"from {packet['producer_control_store']!r}. The line being "
                f"reviewed lives in one store; reviewing a checkpoint read "
                f"from another one is reviewing a line this run cannot reach.")
    return packet


def _verdict_evidence(control, packet, admitted, kinds):
    """Did this run collect ONE attributed verdict about THIS checkpoint?

    In place of W239528's `_workload_evidence`, which asks the implementation
    question: one turn, one context, one retained proposal, attributed to the
    adapter. This asks the review question:

      * ONE review attempt and no other kind;
      * an attachment for that attempt, to the checkpoint the packet names;
      * a verdict derived from the reviewer's OWN frozen output, through
        `review_driver.review_verdict_from_result`, which cross-binds the
        claim against the attempt, the manifest, the assignment and the
        checkpoint's own base, head and tree;
      * a disposition that is one of the three the contract allows.

    NOTHING HERE MANUFACTURES A VERDICT AND NOTHING HERE PREFERS ONE.
    `changes-requested` and `rejected` are results, not shortfalls; the
    shortfall is a run that produced no attributed verdict at all. That
    distinction is the whole reason this function reads the FROZEN OUTPUT
    rather than a process exit status.
    """
    from baton_v12.job_manager import review_driver
    from baton_v12.worker_manager import review_for_attempt

    shortfalls = []
    subject = packet["subject"]

    def named(kind):
        return [one for one in admitted
                if (admitted[one] or kinds.get(one)) == kind]

    review = named("review")
    evidence = {"review_attempts": review, "attachments": [], "verdicts": [],
                "dispositions": [], "corrections_opened": [],
                "shortfalls": []}

    want = packet["bounds"]["review_invocations"]
    if len(review) != want:
        shortfalls.append(f"the packet declares {want} review invocation(s) "
                          f"and this run has {len(review)}")
    # NO STAGE KIND BUT THIS ONE, read back from what actually ran. The gate
    # refuses a foreign kind at admission; this is the same statement taken
    # from the other end, so a container that reached this Job by some other
    # path is a shortfall rather than an unexamined extra row.
    foreign = sorted({(admitted[one] or kinds.get(one)) for one in admitted}
                     - {"review"} - {None})
    if foreign:
        shortfalls.append(f"this Job serves the review stage alone and this "
                          f"run also ran {', '.join(foreign)}; implementation "
                          f"and correction are separate Jobs")

    for attempt in review:
        held = _guarded(
            lambda one=attempt: review_for_attempt(
                control, attempt_id=one,
                generation=_generation_of(control, one)),
            None, what=f"the review attachment for {attempt}",
            uncertainty=shortfalls, interrupted=[])
        if held is None:
            shortfalls.append(f"attempt {attempt} has no readable review "
                              f"attachment, so nothing binds its turn to a "
                              f"checkpoint")
            continue
        attachment = held.get("attachment_id")
        # `assignment_generation`, WHICH IS WHAT THE ROW IS CALLED. Reading a
        # `generation` member that the public reader does not return recorded
        # null in every outcome -- review 2026-09-23T11:30:47Z R2. The reader's
        # own contract is the contract.
        generation = held.get("assignment_generation")
        evidence["attachments"].append(
            {"attempt_id": attempt, "attachment_id": attachment,
             "generation": generation,
             "runtime_attempt_id": held.get("runtime_attempt_id"),
             "checkpoint_id": held.get("checkpoint_id")})
        # THE ATTACHMENT IS THE PACKET'S OWN CHECKPOINT, or this run reviewed
        # something else. A stale or foreign checkpoint is exactly what
        # `attachment.py` refuses BEFORE launch; this is the same question
        # asked AFTER, because a preflight is a moment and this is the record.
        if held.get("checkpoint_id") != subject["checkpoint_id"]:
            shortfalls.append(
                f"attempt {attempt} reviewed checkpoint "
                f"{held.get('checkpoint_id')!r} and this packet names "
                f"{subject['checkpoint_id']!r}")
        answered = _guarded(
            lambda one=attachment: review_driver.review_verdict_from_result(
                control, attachment_id=one),
            None, what=f"the verdict recorded by {attempt}",
            uncertainty=shortfalls, interrupted=[])
        if answered is None:
            shortfalls.append(
                f"attempt {attempt} recorded no readable verdict. A review "
                f"that produced no attributed report is not a review result; "
                f"it is a review that did not happen.")
            continue
        # `verdict`, `result_id` AND `result_digest` -- the members
        # `review_verdict_from_result` ACTUALLY RETURNS. This read
        # `disposition` and `verdict_id`, which that reader does not answer,
        # so a valid `accepted` became `None` and every successful review was
        # reported as a shortfall. Review 2026-09-23T11:30:47Z R2, and it is
        # the worst kind of defect: it could only ever have been found by a
        # test that exercised the SUCCESS path, and there was none.
        disposition = answered.get("verdict")
        evidence["verdicts"].append(
            {"attempt_id": attempt, "attachment_id": attachment,
             "verdict": disposition,
             "result_id": answered.get("result_id"),
             "result_digest": answered.get("result_digest"),
             "checkpoint_id": answered.get("checkpoint_id"),
             "base": answered.get("base"), "head": answered.get("head"),
             "tree": answered.get("tree")})
        evidence["dispositions"].append(
            {"attempt_id": attempt, "verdict": disposition})
        if disposition not in VERDICTS:
            shortfalls.append(
                f"attempt {attempt} answered {disposition!r}, which is not "
                f"one of {', '.join(VERDICTS)}")
        # AND THE REVIEWER LOOKED AT THE BYTES THE CHECKPOINT RECORDS.
        # `review_verdict_from_result` cross-binds these itself and refuses
        # rather than answering when they disagree; naming them again here is
        # what puts them in the retained outcome where an operator can read
        # them beside the subject.
        for name, mine in (("base", subject["base_object"]),
                           ("head", subject["head_object"]),
                           ("tree", subject["tree_object"])):
            theirs = answered.get(name)
            if theirs is not None and theirs != mine:
                shortfalls.append(
                    f"attempt {attempt} reports {name} {theirs!r} and the "
                    f"reviewed checkpoint records {mine!r}")

    evidence["shortfalls"] = shortfalls
    return evidence


def _serving_origin(control, attempt_id, launched, uncertainty):
    """This attempt's origin during serving, failing closed on ERROR only.

    The same `_origin` the shutdown accounting uses, asked per tick so the two
    phases classify one identity one way. An ordinary failure answers
    `FOREIGN`, which is NOT excluded: an identity this run cannot classify
    keeps its cleanup obligation rather than quietly leaving the set the
    no-progress rule reads.

    ONLY `Exception`, NEVER `BaseException` -- and the first version of this
    got it wrong in a way this project has been corrected for before. It used
    `_guarded(..., interrupted=[])`, and `_guarded` catches `BaseException`
    and appends the interruption to the list it is given; a DISPOSABLE list
    discards it. So a `KeyboardInterrupt` raised while classifying an origin
    was swallowed and `should_continue` could keep serving after an operator
    had asked the run to stop. W239528's review 2026-09-23T00:50:59Z R1 found
    exactly that shape in the progress read, and review 2026-09-23T13:52:06Z
    found me reintroducing it here.

    An interruption now travels out of the predicate, out of `serve`, and into
    the shutdown handler that closes admission, cancels, accounts and
    publishes -- which is the path that already exists.
    """
    try:
        return _origin(control, attempt_id, launched, uncertainty)[0]
    except Exception as failure:                             # noqa: BLE001
        uncertainty.append(
            f"the serving origin of {attempt_id} did not complete: "
            f"{type(failure).__name__}: {failure}. An identity this run "
            f"cannot classify keeps its cleanup obligation.")
        return baseline.FOREIGN


def _correction_rounds(job, job_id):
    """The implementation stages this Job's own records hold, if any.

    READ FROM `stage_rows`, which is what `survey` reads and is a pure read.
    An opened round is a STAGE; deriving it from attempt kinds -- as this did
    -- reported nothing at all for a round that was opened and never allocated
    an attempt, which is exactly the shape a `changes-requested` ending leaves
    behind before anything runs.
    """
    from baton_v12.job_manager import stage_rows

    return sorted(one.get("stage_id") or repr(one)
                  for one in stage_rows(job)
                  if one.get("job_id") == job_id
                  and one.get("kind") != "review")


def _generation_of(control, attempt_id):
    """The assignment generation an attempt runs at, from its own record."""
    from baton_v12.worker_manager import assignment_of

    return assignment_of(control, attempt_id)["generation"]


def supervise(job, control, operations, packet, *, clock=None, sleep=None,
              monotonic=None, surveyed=None):
    """One bounded review, with the termination handler held throughout.

    THE HANDLER IS INSTALLED HERE AND RESTORED HERE, around everything, for
    W239528's reason: the shutdown is the part of a run that most needs it, so
    it is the part that keeps it. `Termination` is imported unchanged.
    """
    termination = Termination().install()
    try:
        return _supervise(job, control, operations, packet, clock=clock,
                          sleep=sleep, monotonic=monotonic,
                          termination=termination, surveyed=surveyed)
    finally:
        termination.restore()


def _supervise(job, control, operations, packet, *, clock, sleep, monotonic,
               termination=None, surveyed=None):
    """One Job, one review, bounded -- then a real stop, then accounting.

    THE PHASES ARE SEPARATE ON PURPOSE, and they are W239528's phases because
    they are not implementation-specific: submission is not serving; serving is
    not stopping; stopping is not cleanup; cleanup is not the outcome; and the
    outcome is decided by what the run PRODUCED rather than by how the loop
    ended. What differs from that run is the cap's kind, the evidence in step
    7, and the correction round step 7b reports rather than starts.
    """
    import time

    clock = _moment if clock is None else clock
    sleep = time.sleep if sleep is None else sleep
    monotonic = time.monotonic if monotonic is None else monotonic
    from baton_v12.job_manager import read_submission, serve, submit, sweep

    bounds = packet["bounds"]
    job_id = packet["submission"]["job_id"]
    # THE ONLY CAP, AND ITS KIND IS `review`. `AdmissionGate` is imported
    # unchanged: it refuses by reading the caps it was constructed with, so an
    # `implementation` stage reaching it is denied for the same reason a
    # `review` stage was denied over there -- "this packet serves review and
    # an 'implementation' stage reached the admission gate".
    gate = AdmissionGate(operations, caps={"review": bounds["review_invocations"]},
                         job_id=job_id)
    started = monotonic()
    # THE CLEANUP RESERVE IS INSIDE THE TOTAL, and `held_packet` refuses a
    # packet that says otherwise -- so the loop has to honour it. It did not:
    # serving ran for the whole `total_seconds` and THEN a further
    # `cleanup_seconds` window opened, so a packet declaring 300 with 60
    # reserved could spend 360. Review 2026-09-23T11:30:47Z R3. Serving now
    # stops at `total - cleanup`, and the cleanup window below is additionally
    # bounded by what is left of `total`, so neither can overrun it alone or
    # together.
    serving_bound = bounds["total_seconds"] - bounds["cleanup_seconds"]
    measured = {"submitted_at": clock(), "job_id": job_id,
                "serving_bound_seconds": serving_bound,
                "subject": dict(packet["subject"])}
    uncertainty = []
    caught = []
    termination = Termination() if termination is None else termination

    if surveyed is None:
        surveyed = _guarded(lambda: survey(job, packet), None,
                            what="the pre-submission Job survey",
                            uncertainty=uncertainty, interrupted=caught)
    measured["preexisting_jobs"] = (
        [] if surveyed is None else surveyed["preexisting_jobs"])
    measured["preexisting_stages"] = (
        {} if surveyed is None else surveyed["preexisting_stages"])
    measured["accounting_scope"] = (
        surveyed["accounting_scope"] if surveyed is not None else
        f"this run accounts for Job {job_id!r} and for nothing else; the "
        f"store could not be surveyed, so what else it holds is unknown.")

    # -- 1. ONE SUBMISSION, AND A REPEAT REPLAYS IT ------------------------
    # INSIDE THE PUBLISHING REGION. These two steps sat outside the serving
    # `try`, so a submission that refused -- a colliding Job identity, an
    # unreadable submission document -- escaped this function with NOTHING
    # published, and a caller learned only what the traceback said. Review
    # 2026-09-23T11:30:47Z R3. They are owner acts and they can fail; a run
    # that took them and then vanished is the failure mode the retained
    # outcome exists for. `submission_failure` is a hold reason and the
    # serving loop is skipped, because there is nothing to serve.
    submission_failure = None
    held = {"stop": None, "states": {}, "kinds": {}}
    try:
        with open(packet["submission"]["path"], "r",
                  encoding="utf-8") as handle:
            recorded = submit(job, read_submission(handle.read()))
        measured["submission_id"] = recorded["submission_id"]

        # -- 2. THE DECLARED PER-TURN CEILING IS THE JOB'S, BEFORE SERVING -
        _seen, _states, limits = _attempts_of(job, gate, job_id)
        measured["provider_turn"] = _turn_ceiling(limits, packet)
    except BaseException as failure:                          # noqa: BLE001
        # `BaseException`, NOT `Exception`. Review 2026-09-23T11:56:42Z R3a:
        # the installed handler raises `KeyboardInterrupt`, which is not an
        # `Exception`, so an interrupt arriving during `submit` or the
        # turn-ceiling read escaped through `supervise`'s `finally` -- which
        # only restores handlers -- and left a COMMITTED stage with no outcome
        # on disk. The reviewer reproduced it by wrapping the real public
        # `submit`, letting it commit, then injecting the interrupt.
        #
        # An owner act is exactly where this matters most: it is the first
        # moment the run has changed anything. The interrupt is recorded here
        # and re-raised at the end, AFTER the accounting and the publication,
        # by the same path every other interruption takes.
        submission_failure = f"{type(failure).__name__}: {failure}"
        measured.setdefault("submission_id", None)
        measured.setdefault("provider_turn", None)
        held["stop"] = "submission-failed"
        if not isinstance(failure, Exception):
            caught.append(submission_failure)
            held["stop"] = "interrupted"
    measured["submission_failure"] = submission_failure

    # -- 3. BOUNDED SERVING, WITH ADMISSION BOUNDED AT THE GATE ------------

    def should_continue():
        seen, states, _limits = _attempts_of(job, gate, job_id)
        held["kinds"].update(seen)
        held["states"] = states
        reached = _terminal(states)
        if reached is not None:
            held["stop"] = reached
            return False
        accountable = {one: kind for one, kind in gate.launched.items()}
        accountable.update({one: kind for one, kind in seen.items()})
        # SERVING AND SHUTDOWN MUST MEAN THE SAME THING BY "accountable".
        #
        # They did not. The shutdown's `classify()` drops an identity whose
        # origin is `UNALLOCATED` -- "an identity the manager answers no row
        # for, that this run never launched, is not a runtime" -- and this
        # read did not, so a blocked stage's projection identity was counted
        # OUTSTANDING here every tick while being excluded there. Review
        # 2026-09-23T13:46:58Z traced it over 42 real cleanup reads: the
        # review attempt was already `retained`/`absent` DURING serving, and
        # the extra identity alone kept the outstanding set non-empty, which
        # suppresses the no-progress rule permanently. Two accounts of the
        # same set is the defect; one is the fix.
        #
        # IT FAILS CLOSED. `_serving_origin` answers `FOREIGN` when the read
        # does not complete, and only `UNALLOCATED` is dropped -- so an
        # identity this run cannot classify stays accountable and keeps its
        # cleanup obligation. Dropping on uncertainty would be inventing the
        # quiet the detector then reports.
        accountable = {
            one: kind for one, kind in accountable.items()
            if _serving_origin(control, one, set(gate.launched),
                               uncertainty) != baseline.UNALLOCATED}
        # ONLY `Exception`, NEVER `BaseException`. W239528's review
        # 2026-09-23T00:50:59Z R1: `_guarded` catches `BaseException`, so a
        # `KeyboardInterrupt` raised by the installed handler was swallowed
        # here and ordinary serving resumed. An operator who asks a run to
        # stop is owed it stopping, so the interrupt travels out of the
        # predicate into the shutdown path below.
        try:
            settled = _cleanups(control, packet, accountable)
        except Exception as failure:                         # noqa: BLE001
            uncertainty.append(
                f"the progress read did not complete: "
                f"{type(failure).__name__}: {failure}. A failed read is not "
                f"evidence that nothing is happening, so this tick counts as "
                f"progress.")
            settled = None
        now = (None if settled is None
               else _observation(states, accountable, settled["cleanup"]))
        if now is not None and accountable and not settled["outstanding"] \
                and now == held.get("observation"):
            held["stalled"] = held.get("stalled", 0) + 1
            if held["stalled"] >= STALLED_TICKS:
                held["stop"] = "no-progress"
                return False
        else:
            held["stalled"] = 0
        held["observation"] = now
        if gate.refusals:
            held["stop"] = "invocation-cap-refused"
            return False
        if monotonic() - started >= serving_bound:
            held["stop"] = "overall-bound-exceeded"
            return False
        return True

    serving_failure = None
    interrupted = None
    try:
        if submission_failure is None:
            serve(job, gate, clock=clock, sleep=sleep,
                  should_continue=should_continue, interval=1)
    except Exception as failure:                             # noqa: BLE001
        serving_failure = f"{type(failure).__name__}: {failure}"
        held["stop"] = held["stop"] or "serving-failed"
    except BaseException as failure:                         # noqa: BLE001
        interrupted = f"{type(failure).__name__}: {failure}"
        held["stop"] = held["stop"] or "interrupted"

    # -- 4. ADMISSION IS CLOSED, AND THE CANONICAL HISTORY IS RE-READ ------
    gate.stop()
    termination.defer()
    measured["stopped"] = held["stop"] or "stopped-without-a-reason"
    measured["serving_failure"] = serving_failure
    measured["admissions"] = dict(gate.admissions)
    measured["gate_refusals"] = list(gate.refusals)
    measured["foreign_admissions"] = list(gate.foreign)
    measured["served_seconds"] = monotonic() - started
    admitted = dict(gate.launched)
    refreshed, states, _limits, _read = _guarded(
        lambda: _refresh(job, gate, job_id, uncertainty,
                         "after the serving loop"),
        ({}, {}, None, False), what="the post-stop canonical read",
        uncertainty=uncertainty, interrupted=caught)
    held["states"] = states or held["states"]
    held["kinds"].update(refreshed)
    for attempt, kind in refreshed.items():
        admitted.setdefault(attempt, kind)

    # -- 4b. ASK THE COMPOSITION TO STOP WHAT IS STILL EXECUTING -----------
    measured["cancellation"] = _guarded(
        lambda: _cancel_active(operations, control, packet, admitted,
                               held["states"], uncertainty,
                               reason=measured["stopped"],
                               launched=set(gate.launched),
                               interrupted=caught),
        {}, what="the cancellation of what was still executing",
        uncertainty=uncertainty, interrupted=caught)

    # -- 4c. CLASSIFY, ONCE, BEFORE ANYTHING IS CHARGED --------------------
    origins = {}

    def classify():
        for attempt in sorted(admitted):
            if attempt in origins:
                continue
            origins[attempt] = _guarded(
                lambda one=attempt: _origin(control, one, set(gate.launched),
                                            uncertainty)[0],
                baseline.FOREIGN, what=f"the origin of {attempt}",
                uncertainty=uncertainty, interrupted=caught)
        return {one: kind for one, kind in admitted.items()
                if origins.get(one) != baseline.UNALLOCATED}

    accountable = classify()

    # -- 5. THE CLEANUP WINDOW, WHICH CANNOT ADMIT ANYTHING ----------------
    cleanup_started = monotonic()
    intruders, sweeps = [], 0
    while monotonic() - cleanup_started < bounds["cleanup_seconds"] \
            and monotonic() - started < bounds["total_seconds"]:
        # GUARDED. An accounting error here used to escape the whole function
        # with the outcome unpublished, which is the one thing a run that has
        # started runtimes must never do. A read that does not answer ends the
        # window and is a reason to hold, not a way out of the accounting.
        outstanding = _guarded(
            lambda: _cleanups(control, packet, accountable)["outstanding"],
            None, what="a cleanup-window progress read",
            uncertainty=uncertainty, interrupted=caught)
        if outstanding is None or not outstanding:
            break
        try:
            sweep(job, gate, now=clock())
            sweeps += 1
        except BaseException as failure:                     # noqa: BLE001
            if not isinstance(failure, Exception):
                interrupted = interrupted or \
                    f"{type(failure).__name__}: {failure}"
            serving_failure = serving_failure or \
                f"cleanup sweep: {type(failure).__name__}: {failure}"
            break
        finally:
            fresh, states, _limits, _read = _guarded(
                lambda: _refresh(job, gate, job_id, uncertainty,
                                 "during the cleanup window"),
                ({}, {}, None, False), what="a cleanup-window canonical read",
                uncertainty=uncertainty, interrupted=caught)
            held["states"] = states or held["states"]
            held["kinds"].update(fresh)
            for attempt, kind in list(gate.launched.items()) + list(
                    fresh.items()):
                if attempt not in admitted:
                    intruders.append(attempt)
                    admitted[attempt] = kind
            accountable = classify()
        try:
            sleep(1)
        except BaseException as failure:                     # noqa: BLE001
            if not isinstance(failure, Exception):
                interrupted = interrupted or \
                    f"{type(failure).__name__}: {failure}"
            uncertainty.append(
                f"the cleanup window ended early: "
                f"{type(failure).__name__}: {failure}")
            break
    measured["cleanup_sweeps"] = sweeps
    measured["stalled_ticks"] = held.get("stalled", 0)
    measured["stalled_after"] = STALLED_TICKS

    # -- 6. POSITIVE, MANAGER-OWNED CLEANUP FOR EVERY STARTED RUNTIME ------
    final, states, _limits, final_read = _guarded(
        lambda: _refresh(job, gate, job_id, uncertainty,
                         "for the final accounting"),
        ({}, {}, None, False), what="the final canonical read",
        uncertainty=uncertainty, interrupted=caught)
    held["states"] = states or held["states"]
    held["kinds"].update(final)
    for attempt, kind in final.items():
        if attempt not in admitted:
            intruders.append(attempt)
            admitted[attempt] = kind
    measured["final_canonical_read"] = final_read
    measured["stage_states"] = dict(held["states"])
    measured["admitted_attempts"] = sorted(accountable)
    measured["observed_attempts"] = sorted(admitted)
    measured["started_order"] = [one for one in admitted
                                 if one in accountable]
    measured["unexpected_attempts"] = sorted(set(intruders))
    accountable = classify()
    measured["attempt_origins"] = origins
    measured["unallocated_attempts"] = sorted(
        one for one, origin in origins.items()
        if origin == baseline.UNALLOCATED)
    accounting = _guarded(
        lambda: _cleanups(control, packet, accountable),
        {"cleanup": {}, "outstanding": sorted(accountable)},
        what="the cleanup accounting", uncertainty=uncertainty,
        interrupted=caught)
    measured["cleanup"] = accounting["cleanup"]
    measured["outstanding_cleanup"] = accounting["outstanding"]

    # -- 7. THE VERDICT THIS RUN ACTUALLY COLLECTED ------------------------
    workload = _guarded(
        lambda: _verdict_evidence(control, packet, accountable,
                                  held["kinds"]),
        {"shortfalls": ["the verdict evidence could not be read"]},
        what="the verdict evidence", uncertainty=uncertainty,
        interrupted=caught)
    measured["workload"] = workload

    # -- 7b. A CORRECTION ROUND HOLDS THIS RUN -----------------------------
    # READ FROM THE JOB STORE'S OWN STAGE RECORDS, not from attempt kinds. The
    # previous version derived this from `held["kinds"]`, which is keyed by
    # ATTEMPT -- so a round that was opened and never allocated an attempt had
    # no entry at all and went unreported. Review 2026-09-23T11:30:47Z R4.
    measured["correction_rounds_opened"] = _guarded(
        lambda: _correction_rounds(job, job_id), None,
        what="the Job's own stage records", uncertainty=uncertainty,
        interrupted=caught)
    measured["correction_containers_started"] = sorted(
        one for one, kind in gate.launched.items() if kind != "review")
    measured["correction_limitation"] = CORRECTION_LIMITATION

    # -- 8. THE OUTCOME, AND IT FAILS CLOSED -------------------------------
    for one in termination.received:
        if one not in caught:
            caught.append(one)
    if interrupted is None and caught:
        interrupted = caught[0]
    measured["interrupted"] = interrupted
    measured["interruptions"] = list(caught)
    reasons = []
    reasons.extend(uncertainty)
    if not final_read:
        reasons.append("the final canonical accounting could not be read, so "
                       "this run cannot say what it left behind")
    if interrupted is not None:
        reasons.append(f"the run was interrupted: {interrupted}")
    for attempt, said in sorted(measured["cancellation"].items()):
        if not said.get("requested"):
            reasons.append(f"execution on {attempt} was not stopped: "
                           + said.get("why", "no reason recorded"))
    if submission_failure is not None:
        reasons.append(f"the submission did not complete: "
                       f"{submission_failure}")
    if serving_failure is not None:
        reasons.append("the serving loop did not end cleanly")
    if intruders:
        reasons.append("a runtime was admitted after admission closed: "
                       + ", ".join(sorted(set(intruders))))
    if gate.refusals:
        reasons.append("the admission gate refused: "
                       + "; ".join(one["why"] for one in gate.refusals))
    if accounting["outstanding"]:
        reasons.append("this manager cannot prove positive cleanup for "
                       + ", ".join(accounting["outstanding"]))
    if not accountable:
        reasons.append("no runtime was ever admitted, so this run answered "
                       "nothing about the reviewer")
    if measured["correction_containers_started"]:
        reasons.append(
            "a correction container started in this run: "
            + ", ".join(measured["correction_containers_started"])
            + ". Correction is W236087's separately selected Job.")
    if measured["correction_rounds_opened"]:
        reasons.append(
            "a correction round was opened in this Job store: "
            + ", ".join(measured["correction_rounds_opened"]) + ". "
            + CORRECTION_LIMITATION)
    if held["stop"] == "no-progress":
        reasons.append(
            f"the run stopped because nothing changed for {STALLED_TICKS} "
            f"consecutive ticks while its stages were not terminal and every "
            f"runtime it started was already positively excluded. The stage "
            f"states were {dict(held['states'])}.")
    if held["stop"] != "completed":
        reasons.append(f"the run stopped {measured['stopped']!r} rather than "
                       f"completing its stages")
    reasons.extend(workload["shortfalls"])

    outcome = {"schema": OUTCOME_SCHEMA, "run_id": packet["run_id"],
               "work": packet["work"], "claim": packet["claim"],
               "job_id": job_id,
               "state": "settled" if not reasons else "held",
               "held_because": reasons,
               "retry": False, "finished_at": clock(),
               "uncertainty": uncertainty, **measured}
    _publish(packet["outcome_path"], outcome)
    if interrupted is not None:
        raise SupervisorInterrupted(interrupted, outcome)
    return outcome


def main(argv=None, *, stream=None, compose=None, image_inspect=None):
    stream = sys.stderr if stream is None else stream
    parser = argparse.ArgumentParser(
        prog="review_supervisor",
        description="Drive ONE bounded managed review and stop.")
    parser.add_argument("--packet", required=True,
                        help="the reviewed packet manifest")
    parser.add_argument("--incarnation", required=True,
                        help="this supervising process's control incarnation")
    taken = parser.parse_args(argv)

    try:
        packet = held_packet(taken.packet)
        # `program=` IS NOT OPTIONAL HERE, and omitting it made this program
        # refuse every correct packet. `verify_imported_sources` lives in
        # `baseline.py` and defaults the running program to ITS OWN
        # `__file__`, so a packet that correctly binds `review_supervisor.py`
        # failed with "this process is running .../baseline.py and the packet
        # binds .../review_supervisor.py" -- exit 2, before the engine or any
        # store. Review 2026-09-23T11:30:47Z R1 reproduced it through `main`.
        # A default that is right for the module a function is DEFINED in is
        # wrong for every module that imports it.
        verify_imported_sources(packet,
                                program=os.path.abspath(__file__))
        verify_worker_image(
            packet,
            image_inspect=_engine_inspect if image_inspect is None
            else image_inspect)
    except SupervisorRefusal as refusal:
        print(f"refused before anything opened: {refusal}", file=stream)
        return 2

    from baton_v12.job_manager import JobStore
    from baton_v12.worker_manager import ControlStore

    deployment = packet["deployment"]
    with JobStore.open(deployment["job_store"],
                       authority_uuid=deployment["authority_uuid"],
                       incarnation=taken.incarnation, clock=_moment) as job:
        try:
            surveyed = survey(job, packet)
        except SupervisorRefusal as refusal:
            print(f"refused before any owner act: {refusal}", file=stream)
            return 2
        with ControlStore.open(deployment["control_store"],
                               incarnation=taken.incarnation,
                               clock=_moment) as control:
            composed = (_compose(packet, job, control, stream)
                        if compose is None else
                        compose(packet, job, control, stream))
            try:
                outcome = supervise(job, control, composed, packet,
                                    surveyed=surveyed)
            except SupervisorInterrupted as stopped:
                print(f"interrupted: {stopped.args[0]}; the outcome is "
                      f"retained at {packet['outcome_path']}", file=stream)
                return 130
            finally:
                release = getattr(composed, "release", None) or getattr(
                    composed, "close", None)
                if release is not None:
                    release()
    print(json.dumps({one: outcome[one] for one in
                      ("state", "stopped", "held_because", "served_seconds")},
                     indent=2), file=stream)
    return 0 if outcome["state"] == "settled" else 1


if __name__ == "__main__":                                   # pragma: no cover
    sys.exit(main())
