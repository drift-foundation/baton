"""THE OWNER'S DECISION ON A RETAINED VERIFICATION FAILURE, AND THE ONE
VERIFICATION/REVIEW-ONLY SUCCESSOR IT ADMITS.

W385624 Stage 1-B, under DESIGN REC-8 and the accepted Stage 1 contract
`work/records/2026/08/finding-v12-isolated-agent-workers/findings/
finding-v12-team-hierarchy-shared-approvers/STAGE-1-CONTRACT.md` (SHA-256
`52c2c640fdbb791e70ae61edf7ef7db7190bacd767d6d044f678517d2e09e1bc`), accepted
by `review-2026-11-22T05-18-37Z.md`. The owning record is
`work/records/2026/11/finding-v12-retained-recovery-admission/`.

IT CONSUMES W385623's RECORDS AND ADDS THE TWO ACTS THEY STOPPED SHORT OF.
Stage 1-A observes a terminal `verification-failed` ending, analyses it once
and delivers ONE owner item with a bounded diagnosis. It admits nothing, and
it says so: "an analysis report earns no successor, no correction round, no
verdict and no receipt". This module is where that stops being true, in two
separately attributable steps:

  1. THE OWNER DECISION. An authorized owner, resolved through the Authority's
     own principal/scope seam at the capability that deployment granted,
     records an APPROVED, DENIED or HELD disposition that binds the exact
     failure, the exact delivered report, the exact retained candidate bytes
     and base, the exact ORIGINAL verifier argv, the exact CORRECTED argv and
     its execution context, the owner-approved profile identity and digest,
     and the selected stage set. Nothing else authorizes a successor: not a
     generic "retry", not reading the item, not the analysis's own
     recommendation, and not a review approval of something else.
  2. THE SUCCESSOR ADMISSION. A NEW manager-owned admission -- not
     `fresh_attempt`, which carries the prior specification forward and would
     therefore repeat the implementation -- of one isolated Job whose stage
     set carries NO IMPLEMENTATION. The retained candidate, the original task
     and the original failure are untouched; the successor is LINKED to them.

WHAT IT REFUSES, and every one of these is a ruling rather than a preference:

  * NO IMPLEMENTATION REDISPATCH. The admitted successor's stages are the
    owner's selected verification/review set, and `owned_stages` refuses
    `implementation` by name. No provider coding prompt, no correction round
    and no second attempt at the task is reachable from here.
  * NO DECISION WITHOUT AUTHORITY. The scope comes off the WORK's own row and
    the principal comes off the Authority's endpoint mapping; neither is an
    operand. A participant that holds no decision capability in that scope is
    refused before anything is recorded.
  * NO DECISION ON STALE EVIDENCE. The failure's own fixed input is
    recomposed from the original attempt AS IT STANDS NOW and held to the
    digest the analysis was admitted on. Evidence that changed under the
    owner is refused, not decided about.
  * NO GENERIC RETRY. A "correction" whose argv is the argv that failed is
    refused as the retry it is -- the contract's own words, "a generic
    'retry' ... cannot authorize a successor".
  * DENIAL AND HOLD LAUNCH NOTHING. `admit_successor` reads the disposition
    out of the committed decision; a denied or held one admits nothing, and a
    later approval is a NEW decision identity and a new attributable act that
    never overwrites the first.
  * NO SECOND SUCCESSOR BY ACCIDENT. One failure key has at most one admitted
    verification/review successor, decided inside this store's write lock, so
    two concurrent owner decisions meet at a fence rather than at a read. A
    further round needs a new owner decision, and a renewed verification
    failure has its own failure key.
  * NO BLIND RE-VERIFICATION. A review-only admission is authorized only
    against still-valid exact evidence: the named prior successor, its
    journalled PASSED verification of this exact candidate under this exact
    approved command, and the candidate still validating now. Absent,
    mismatched or unknown evidence REFUSES and reports why; it never becomes
    permission to verify again.
  * NO MANUFACTURED CESSATION. Whether the prior runtimes ceased and returned
    their resources is the host's answer, read through its own owner, and
    `unknown` refuses. REC-7's rule, for REC-8's reason.
  * NO CROSS-STORE TRANSACTION. The Jobs are this store's, the authorization
    is the Authority's, the runtime and the resource are the Worker Manager's
    and the binding is the deployment configuration's. The successor identity
    is reserved HERE, durably, before any other owner is touched; every cut
    between them replays, and a refusal past the reservation says so.

WHAT IS DELIBERATELY NOT HERE. The verifier is not executed, the retained
candidate is not materialized, no workspace is prepared, no review handoff is
prepared and no verification result is produced: those are W385625's, which
owns the verifier execution adapter and the final loop. What this module owns
of that boundary is the CONTRACT of the verification record a review-only
admission validates (`record_verification`) -- the evidence shape, not the
execution that fills it -- and `successor_readiness` says out loud which act
is owed next rather than implying one was performed.
"""

import json
import os

from ..contracts import ContractRefusal, digest, digest_of_bytes, own
from ..contracts.errors import name_value, sample_of
from ..worker_manager import boundaries, frozen_output_of, load_manifest
from . import (cancellation, documents, failure_analysis, fresh_attempt,
               job_control, submission)
from .store import job_signature

__all__ = ["SUCCESSOR_PROFILE", "SUCCESSOR_DEFINITION",
           "SUCCESSOR_DEFINITION_BYTES", "SUCCESSOR_PROFILE_DIGEST",
           "SUCCESSOR_PROFILES", "PUBLISHED_PROFILE_DIGEST", "CLOCK_ORIGINS",
           "resolved_profile", "admitted_bounds",
           "VERIFICATION_STAGE", "REVIEW_STAGE", "FORBIDDEN_STAGE",
           "FULL_STAGES", "REVIEW_ONLY_STAGES", "SELECTED_STAGE_SETS",
           "owned_stages",
           "OWNER_CAPABILITY", "OWNER_AUTHORIZATION", "OWNER_DECISION",
           "DISPOSITIONS", "APPROVED", "DENIED", "HELD",
           "EXPECTED_MEMBERS", "CORRECTION_MEMBERS", "LINEAGE_MEMBERS",
           "DECISION_KIND", "DECISION_MEMBERS", "decision_operation_id",
           "decision_of", "decisions_of", "decisions_for",
           "VERIFICATION_KIND", "VERIFICATION_MEMBERS",
           "VERIFICATION_OUTCOMES", "verification_operation_id",
           "verification_of", "record_verification",
           "SUCCESSOR_INTENT_KIND", "SUCCESSOR_KIND", "SUCCESSOR_MEMBERS",
           "INTENT_MEMBERS", "intent_operation_id", "admit_operation_id",
           "successor_job_id", "successor_submission_id",
           "verification_attempt_id",
           "successor_intent_of", "successor_of", "successors_for",
           "SUCCESSOR_DISPOSITIONS", "successor_disposition",
           "READ_SCHEMA", "owner_item_read", "expected_facts",
           "review_stage_id", "successor_readiness",
           "decide", "admit_successor", "execution_gate"]


def _refuse(message, *, category="refused", code="precondition"):
    raise ContractRefusal(category, code, message)


def _denied(message):
    raise ContractRefusal("policy", "denied", message)


# -- 1. the owner-approved finite profile ------------------------------------
#
# HELD AS DATA AND PROVING ITS OWN DIGEST, exactly as `failure_analysis` holds
# `stage1-analysis/1` and for the same reason: M385612 published
# `stage1-verification-review/1` as one immutable definition record whose
# SHA-256 covers its exact UTF-8 bytes including the final newline, and the
# contract's section 5 requires admission to check EXACT agreement with the
# profile the owner named. A table of five integers beside the record would be
# the second account that silently drifts.
#
# AND THIS ONE IS ALSO A `job_control.PROFILES` ENTRY, which the analysis
# profile deliberately is not. The difference is a fact about the executions,
# not a change of policy: an analysis runs no verification command, so
# projecting one into its resolved control document would state a bound the
# owner did not approve. This successor runs TWO -- the approved corrected
# verifier and the review's own required verification -- so its five numbers
# are exactly `PROFILE_MEMBERS` and the Job it admits is admitted under the
# accepted LIM-5 control that enforces them. `_agreeing_control` below holds
# that entry to these bytes rather than trusting that they match.
SUCCESSOR_PROFILE = "stage1-verification-review/1"
SUCCESSOR_DEFINITION = {
    "automatic_corrections": 0,
    "automatic_retries": 0,
    "each_stage": {
        "origin": "stage_admission",
        "seconds": 4800,
    },
    "identity": SUCCESSOR_PROFILE,
    "overall_job": {
        "includes_queue": True,
        "origin": "accepted_admission",
        "seconds": 9960,
    },
    "publication_authority": (
        "M385612; FINDING.md: Owner-approved Stage 1 finite profiles "
        "— 2026-11-22"),
    "review_provider_invocation": {
        "origin": "invocation_start",
        "seconds": 3600,
    },
    "verification_command": {
        "includes_required_review_verification": True,
        "origin": "command_start",
        "seconds": 900,
    },
}

# THE EXACT BYTES THE OWNER'S DEFINITION RECORD CARRIES, reproduced rather
# than read from the dossier: a product module that opened a Work record to
# resolve its own policy would make an evidence directory a runtime input. The
# acceptance module reads the record and compares, which is where that binding
# belongs.
SUCCESSOR_DEFINITION_BYTES = (
    json.dumps(SUCCESSOR_DEFINITION, indent=2, sort_keys=True) + "\n"
).encode("utf-8")
SUCCESSOR_PROFILE_DIGEST = digest_of_bytes(SUCCESSOR_DEFINITION_BYTES)
SUCCESSOR_PROFILES = {SUCCESSOR_PROFILE: SUCCESSOR_DEFINITION}

# WHERE EACH CLOCK STARTS, as the closed vocabulary the definition names. A
# bare number cannot say what it is measured from: the Job clock runs from the
# ACCEPTED SUCCESSOR ADMISSION with queue time included, each stage clock from
# that stage's own execution admission, each command clock from the command's
# REAL START and the review provider clock from the invocation's real start.
# No activity or dispatch stamp substitutes for a command or invocation start.
CLOCK_ORIGINS = ("accepted_admission", "stage_admission", "command_start",
                 "invocation_start")

# THE DIGEST STAGE-1-CONTRACT.md SECTION 5 PINS, held against the definition
# above at import. A RAISE AND NOT AN `assert`, for `failure_analysis`'s
# reason: a build run under `-O` strips assertions, and a self-check that
# disappears under an optimisation flag is best-effort dressed as a guarantee.
PUBLISHED_PROFILE_DIGEST = (
    "sha256:5a6a420e416caab0942f9709939ae01f1f2d9dabbd13e09ff3b03ea08d2932fb")
if SUCCESSOR_PROFILE_DIGEST != PUBLISHED_PROFILE_DIGEST:  # pragma: no cover
    raise AssertionError(
        f"the held {SUCCESSOR_PROFILE} definition digests to "
        f"{SUCCESSOR_PROFILE_DIGEST} and the owner published "
        f"{PUBLISHED_PROFILE_DIGEST}; this build does not carry the approved "
        f"profile and will not admit a successor under a guess")
if any(SUCCESSOR_DEFINITION[one]["origin"] not in CLOCK_ORIGINS
       for one in ("overall_job", "each_stage", "verification_command",
                   "review_provider_invocation")):
    raise AssertionError(                                 # pragma: no cover
        "the held successor definition names a clock origin this build does "
        "not own")
# AND THE CONTROL PROFILE THE ADMITTED JOB IS ENFORCED UNDER IS THE SAME
# POLICY, member by member. `job_control.PROFILES` is what the serving manager
# enforces; this definition is what the owner approved. Two accounts of five
# ceilings agree here, at import, or this build admits nothing.
if SUCCESSOR_PROFILE not in job_control.PROFILES:         # pragma: no cover
    raise AssertionError(
        f"this build does not carry the control profile {SUCCESSOR_PROFILE} "
        f"the owner-approved successor definition names")
_ENFORCED = job_control.PROFILES[SUCCESSOR_PROFILE]
if (_ENFORCED["job_seconds"] != SUCCESSOR_DEFINITION["overall_job"]["seconds"]
        or _ENFORCED["stage_seconds"]
        != SUCCESSOR_DEFINITION["each_stage"]["seconds"]
        or _ENFORCED["provider_turn_seconds"]
        != SUCCESSOR_DEFINITION["review_provider_invocation"]["seconds"]
        or _ENFORCED["verification_command_seconds"]
        != SUCCESSOR_DEFINITION["verification_command"]["seconds"]
        or _ENFORCED["correction_rounds"]
        != SUCCESSOR_DEFINITION["automatic_corrections"]
        or job_control.CONTINUATIONS.get(SUCCESSOR_PROFILE)
        != SUCCESSOR_DEFINITION["automatic_retries"]):    # pragma: no cover
    raise AssertionError(
        f"the control profile {SUCCESSOR_PROFILE} this build enforces and the "
        f"owner-approved definition it is named for state different bounds")


def resolved_profile(profile=SUCCESSOR_PROFILE):
    """The approved bounds of one successor profile, with their units.

    A profile this build does not hold is a STALE SELECTION and is refused
    rather than guessed -- `job_control.owned_control`'s rule, for its reason:
    an execution admitted under a policy nobody selected is one nothing can
    enforce.
    """
    boundaries.text(profile, "a successor profile identity")
    if profile not in SUCCESSOR_PROFILES:
        _refuse(f"a retained-recovery successor profile is one of "
                f"{', '.join(sorted(SUCCESSOR_PROFILES))}; this is "
                f"{name_value(profile)}. A profile this build does not hold "
                f"is a finite control it cannot enforce",
                category="integrity", code="schema")
    held = SUCCESSOR_PROFILES[profile]
    return {"profile": profile, "units": "seconds", "scope": "per-admission",
            "digest": digest_of_bytes(
                (json.dumps(held, indent=2, sort_keys=True)
                 + "\n").encode("utf-8")),
            "automatic_retries": held["automatic_retries"],
            "automatic_corrections": held["automatic_corrections"],
            "overall_job_seconds": held["overall_job"]["seconds"],
            "overall_job_includes_queue": held["overall_job"]["includes_queue"],
            "overall_job_origin": held["overall_job"]["origin"],
            "each_stage_seconds": held["each_stage"]["seconds"],
            "each_stage_origin": held["each_stage"]["origin"],
            "verification_command_seconds":
                held["verification_command"]["seconds"],
            "verification_command_origin":
                held["verification_command"]["origin"],
            "verification_command_covers_review":
                held["verification_command"][
                    "includes_required_review_verification"],
            "review_provider_invocation_seconds":
                held["review_provider_invocation"]["seconds"],
            "review_provider_invocation_origin":
                held["review_provider_invocation"]["origin"]}


def admitted_bounds(policy, *, admitted_at, stages):
    """WHICH APPROVED BOUNDS THIS ADMISSION SELECTED, and from when.

    DELIBERATELY NOT A SECOND SET OF DEADLINES. `job_control` derives the
    successor Job's enforced deadline from the durable `submissions.recorded_at`
    of the submission that admits it, and persists it inside that same
    transaction -- so a deadline computed here would be the second account of
    one instant that LIM-5 exists to prevent, and the one that drifts when a
    restart re-derives the other. What this records is the SELECTION: the
    admission instant the owner's bounds run from, the stage set they apply
    to, and the per-stage and per-command ceilings that have no durable origin
    yet because their executions have not been admitted.

    UNUSED STAGE TIME IS NOT TRANSFERRED, which the contract states and this
    shape keeps true by construction: there is one `each_stage_seconds` and no
    pool for a stage to draw another stage's remainder from.
    """
    boundaries.instant(admitted_at, "a successor admission instant")
    selected = owned_stages(stages)
    return {"profile": policy["profile"], "digest": policy["digest"],
            "units": policy["units"], "admitted_at": admitted_at,
            "stages": list(selected),
            "overall_job_seconds": policy["overall_job_seconds"],
            "overall_job_includes_queue":
                policy["overall_job_includes_queue"],
            "overall_job_origin": policy["overall_job_origin"],
            "each_stage_seconds": policy["each_stage_seconds"],
            "each_stage_origin": policy["each_stage_origin"],
            "verification_command_seconds":
                policy["verification_command_seconds"],
            "verification_command_origin":
                policy["verification_command_origin"],
            "review_provider_invocation_seconds":
                policy["review_provider_invocation_seconds"],
            "review_provider_invocation_origin":
                policy["review_provider_invocation_origin"],
            "automatic_retries": policy["automatic_retries"],
            "automatic_corrections": policy["automatic_corrections"]}


# -- 2. the selected stage set -----------------------------------------------
#
# WHAT A SUCCESSOR MAY CONSIST OF, as a closed vocabulary of exactly two
# admissible sets. The owner selects one and the admission checks exact
# agreement; a set this build does not hold is refused rather than reduced to
# whichever half looks allowed.
#
# `verification` IS THE MANAGER'S OWN EXECUTION and not a Job stage kind:
# `documents.STAGE_KINDS` names the three stages a Job HAS, and REC-8 has the
# manager materialize the retained candidate into a new private workspace and
# run the approved corrected command itself. So the admitted Job carries the
# `review` stage -- which is the independent substantive review the contract
# requires, with the accepted pool's reviewer independence and checkpoint
# attachment -- and the verification travels as the selected recovery stage it
# is, with its own identity and its own approved ceilings.
VERIFICATION_STAGE = "verification"
REVIEW_STAGE = "review"
# AND THE ONE WORD THAT IS NEVER IN A SELECTED SET, named so the refusal can
# say it. This is REC-8's "never redispatching implementation" as a value
# check rather than as a sentence in a docstring.
FORBIDDEN_STAGE = "implementation"
if REVIEW_STAGE not in documents.STAGE_KINDS \
        or FORBIDDEN_STAGE not in documents.STAGE_KINDS:  # pragma: no cover
    raise AssertionError(
        "the Job stage vocabulary no longer names the stages this admission "
        "composes and refuses")
FULL_STAGES = (VERIFICATION_STAGE, REVIEW_STAGE)
REVIEW_ONLY_STAGES = (REVIEW_STAGE,)
SELECTED_STAGE_SETS = (FULL_STAGES, REVIEW_ONLY_STAGES)


def owned_stages(value):
    """The selected stage set, proved to be one the owner may select.

    ORDER IS PART OF THE SELECTION. `("review", "verification")` would say
    the review runs first, which is the opposite of the contract's own
    ordering -- successful verification is what hands the candidate to review
    -- so the sets are compared as sequences rather than as sets.
    """
    if type(value) in (list, tuple):
        held = tuple(value)
    else:
        _refuse(f"a selected stage set is a list of stage words; this is "
                f"{name_value(value)}", category="integrity", code="schema")
    if FORBIDDEN_STAGE in held:
        _denied(f"the selected stage set names {name_value(FORBIDDEN_STAGE)}; "
                f"a retained-recovery successor verifies and reviews an "
                f"EXISTING candidate and never redispatches the work that "
                f"produced it")
    if held not in SELECTED_STAGE_SETS:
        _refuse(f"a retained-recovery successor selects "
                f"{' or '.join(json.dumps(list(one)) for one in SELECTED_STAGE_SETS)}"
                f"; this is {json.dumps(list(held))}",
                category="integrity", code="schema")
    return held


# -- 3. the owner's authority ------------------------------------------------
#
# THE CAPABILITY THE DEPLOYMENT ALREADY GRANTS. Stage 1 uses the delivered
# W16821 principal/scope seam and the EXISTING deployment decision capability
# -- `bootstrap.OWNER_GRANTS` grants the selected human owner `approve`,
# `integrate` and `close` in each bound Work's own scope -- and full
# organizational grant/mask resolution is Stage 3-A's and is not a
# prerequisite. So this names the existing word rather than adding one: a new
# capability would be a deployment configuration change nobody approved, and
# `authority.CAPABILITIES` is explicit that a deployment "grants what §7 names
# and not a word of its own".
OWNER_CAPABILITY = "approve"

# THE PORT, AND IT IS THREE MEMBERS. `participant` is WHO is acting, carried
# by the port because the port is minted for that address -- there is no actor
# operand on `decide`, and that absence is the point: a caller cannot name an
# identity this operation then treats as authorized. `work_of` answers the
# Work's own row, which is where the EFFECTIVE SCOPE comes from. `authorize`
# is W16821's one decision seam and answers with the decision rather than a
# boolean, so what is recorded beside the act says who acted, in which scope,
# by which grant and under which policy generation.
OWNER_AUTHORIZATION = ("participant", "work_of", "authorize")

# The decision document W16821 retains, member for member. Read back rather
# than recomposed: a decision this module assembled would be this module's
# account of somebody else's authorization.
OWNER_DECISION = ("endpoint", "principal", "effective_scope", "role",
                  "grant", "policy_generation")

APPROVED = "approved"
DENIED = "denied"
HELD = "held"
# WHAT AN OWNER MAY SAY, and all three are attributable acts. `held` is not
# "nothing happened": it is the owner explicitly parking a delivered item, and
# it is recorded so a later approval is visibly a SECOND act rather than a
# first one somebody finally got round to.
DISPOSITIONS = (APPROVED, DENIED, HELD)


def _owner(authorization, work_id, *, what):
    """Resolve WHO is deciding and in WHICH scope, through the Authority.

    THE SCOPE IS THE WORK'S AND THE PRINCIPAL IS THE AUTHORITY'S. Neither is
    an operand anywhere on this surface: `_label_transition`'s correction, for
    its reason -- "a default scope let a receipt resolve in the deployment's"
    -- and a decision authorized in a scope the caller chose would be a
    decision about nothing.
    """
    missing = [one for one in OWNER_AUTHORIZATION
               if getattr(authorization, one, None) is None]
    if missing:
        _refuse(f"{what} supplies exactly {', '.join(OWNER_AUTHORIZATION)}; "
                f"this one carries no {', '.join(missing)}",
                category="refused", code="capability")
    participant = boundaries.text(authorization.participant,
                                  f"{what}'s acting participant")
    work = authorization.work_of(work_id)
    if work is None:
        _refuse(f"this deployment's Authority holds no Work "
                f"{name_value(work_id)}; the scope one recovery decision is "
                f"authorized in is that Work's own, and there is none to read")
    # THE THREE MEMBERS THIS ACT NEEDS, named rather than the whole
    # projection: `project_work` answers a wide document that grows, and a
    # closed member contract over it would refuse the day it grows again.
    if type(work) is not dict \
            or any(one not in work for one in ("work_id", "scope", "status")):
        _refuse(f"{what}'s Work projection carries no work_id, scope and "
                f"status; the scope one recovery decision is authorized in is "
                f"read off the Work's own row",
                category="integrity", code="schema")
    held = {one: work[one] for one in ("work_id", "scope", "status")}
    boundaries.text(held["scope"], f"Work {work_id}'s effective scope")
    if held["status"] != "open":
        _refuse(f"Work {name_value(work_id)} is {name_value(held['status'])} "
                f"and a recovery decision is taken under an open "
                f"authorization; deciding on somebody else's terminal Work is "
                f"not this operation's to do")
    decided = authorization.authorize(participant,
                                      capability=OWNER_CAPABILITY,
                                      scope=held["scope"])
    if decided is None:
        _denied(f"{name_value(participant)} holds no "
                f"{name_value(OWNER_CAPABILITY)} capability in "
                f"{name_value(held['scope'])}, which is Work "
                f"{name_value(work_id)}'s own effective scope; a retained "
                f"recovery is authorized by the deployment's decision grant "
                f"and never by reading the owner item, by handling a route or "
                f"by an analysis recommendation")
    taken = boundaries.document(decided, f"{what}'s authorization decision",
                                required=OWNER_DECISION)
    if taken["endpoint"] != participant:
        _refuse(f"the authorization decision names endpoint "
                f"{name_value(taken['endpoint'])} and this act is "
                f"{name_value(participant)}'s; a decision retained beside an "
                f"act is that act's own",
                category="integrity", code="schema")
    if taken["effective_scope"] != held["scope"]:
        _refuse(f"the authorization decision resolved in "
                f"{name_value(taken['effective_scope'])} and Work "
                f"{name_value(work_id)}'s effective scope is "
                f"{name_value(held['scope'])}; one act is authorized in one "
                f"scope", category="integrity", code="schema")
    if taken["role"] != OWNER_CAPABILITY:
        _refuse(f"the authorization decision describes "
                f"{name_value(taken['role'])} and this act needs "
                f"{name_value(OWNER_CAPABILITY)}",
                category="integrity", code="schema")
    boundaries.generation(taken["policy_generation"],
                          "the decision's policy generation")
    return {"work_id": held["work_id"], "work_scope": held["scope"],
            **{name: taken[name] for name in OWNER_DECISION}}


# -- 4. what the owner must have been looking at -----------------------------

EXPECTED_MEMBERS = ("failure_digest", "report_digest", "candidate_base",
                    "candidate_head", "candidate_content_digest",
                    "original_argv")
CORRECTION_MEMBERS = ("argv", "context_digest")
LINEAGE_MEMBERS = ("successor_job_id", "verification_attempt_id",
                   "verification_result_digest")

MAX_ARGV_WORDS = failure_analysis.MAX_ARGV_WORDS
MAX_ARGV_BYTES = failure_analysis.MAX_ARGV_BYTES


def _argv(value, what):
    """A command as the WORDS IT ACTUALLY IS, bounded.

    `failure_analysis._argv`'s rule and `integration.driver`'s before it: "a
    command this module would have to assemble from a string is a shell, and
    there is no shell here". The bounds are the trigger reader's own, read
    from it rather than restated, because an approved correction and the
    original it corrects travel in the same records.
    """
    if type(value) not in (list, tuple) or not value \
            or not all(type(one) is str and one for one in value):
        _refuse(f"{what} is a non-empty list of command words",
                category="integrity", code="schema")
    held = list(value)
    if len(held) > MAX_ARGV_WORDS \
            or len(json.dumps(held).encode("utf-8")) > MAX_ARGV_BYTES:
        _refuse(f"{what} is bounded at {MAX_ARGV_WORDS} words and "
                f"{MAX_ARGV_BYTES} bytes",
                category="integrity", code="schema")
    return held


def _expected(value):
    taken = boundaries.document(value, "the facts this decision was taken on",
                                required=EXPECTED_MEMBERS)
    boundaries.text(taken["failure_digest"], "the decided failure digest")
    if taken["report_digest"] is not None:
        boundaries.text(taken["report_digest"], "the decided report digest")
    for member in ("candidate_base", "candidate_head",
                   "candidate_content_digest"):
        boundaries.text(taken[member], f"the decided {member}")
    return {**{name: taken[name] for name in EXPECTED_MEMBERS},
            "original_argv": _argv(taken["original_argv"],
                                   "the original verification command")}


def _correction(value, *, original):
    taken = boundaries.document(value, "the approved verifier correction",
                                required=CORRECTION_MEMBERS)
    argv = _argv(taken["argv"], "the approved corrected command")
    boundaries.text(taken["context_digest"],
                    "the approved execution context digest")
    if argv == list(original):
        # THE CONTRACT'S OWN SENTENCE, enforced on the operands: "A generic
        # 'retry' ... cannot authorize a successor." The failed command is
        # not a correction of itself, and admitting one would make this whole
        # surface a retry button with extra ceremony.
        _denied(f"the approved correction is the command that failed "
                f"({sample_of(argv)}); a retained-recovery decision approves "
                f"an EXACT verifier correction, and repeating the original "
                f"verification is the generic retry this contract refuses")
    return {"argv": argv, "context_digest": taken["context_digest"]}


def _lineage(value):
    if value is None:
        return None
    taken = boundaries.document(value, "the review-only recovery lineage",
                                required=LINEAGE_MEMBERS)
    boundaries.identity(taken["successor_job_id"], "a prior successor Job id")
    boundaries.identity(taken["verification_attempt_id"],
                        "a prior verification attempt id")
    boundaries.text(taken["verification_result_digest"],
                    "a passed verification result digest")
    return {name: taken[name] for name in LINEAGE_MEMBERS}


# -- 5. the durable records --------------------------------------------------
#
# THREE KINDS, ALL ORDINARY OPERATIONS OF THIS STORE'S EXISTING JOURNAL,
# exactly as Stage 1-A's five are and for the same reasons: the journal
# already supplies exact replay, collision on changed operands and a committed
# result later incarnations read instead of re-deciding. No schema change and
# no new table.
#
# THE DECISION IS KEYED BY THE OWNER'S OWN OPERATION KEY and not by the
# failure, because one failure may legitimately be decided about more than
# once -- a denial and then an approval, or an approval and then the
# review-only disposition section 3.7 supplies. The PER-FAILURE fence is a
# separate rule decided inside the write lock (`_fenced_decision`), which is
# what makes two concurrent owner decisions produce one successor instead of
# two.
DECISION_KIND = "recovery.owner-decision"
SUCCESSOR_INTENT_KIND = "recovery.successor-intent"
SUCCESSOR_KIND = "recovery.successor-admitted"
VERIFICATION_KIND = "recovery.successor-verification"

DECISION_MEMBERS = ("failure_key", "decision_id", "disposition", "owner",
                    "job_id", "stage_id", "expected", "proposed_digest",
                    "correction", "profile", "profile_digest", "stages",
                    "lineage", "item_outcome", "decided_at")
INTENT_MEMBERS = ("failure_key", "decision_id", "job_id", "prior_job_id",
                  "work_id", "submission_id", "stages", "lineage",
                  "verification_attempt_id", "review_stage_id",
                  "candidate", "correction", "bounds", "state")
SUCCESSOR_MEMBERS = ("failure_key", "decision_id", "job_id", "prior_job_id",
                     "work_id", "submission_id", "stages", "work", "binding",
                     "candidate", "correction", "bounds", "control",
                     "exclusion", "fence", "readiness", "stage_ids",
                     "verification_attempt_id", "recorded_at")
VERIFICATION_MEMBERS = ("failure_key", "decision_id", "job_id",
                        "verification_attempt_id", "outcome", "exit_status",
                        "argv", "context_digest", "candidate",
                        "result_digest", "concluded_at")
# WHAT A SUCCESSOR'S VERIFICATION ENDED AS. `passed` is the only one a
# review-only admission may be authorized against; the other two are facts
# this record keeps so an owner reading the lineage is not left inferring
# them from an absence.
VERIFICATION_OUTCOMES = ("passed", "failed", "unknown")


def _operation_id(kind, name):
    boundaries.identity(name, "an operation operand")
    return f"{kind}:{name}"


def decision_operation_id(decision_id):
    """ONE decision per owner operation key, which is what makes an exact
    replay return the committed decision and a changed one collide."""
    return _operation_id(DECISION_KIND, decision_id)


def intent_operation_id(decision_id):
    return _operation_id(SUCCESSOR_INTENT_KIND, decision_id)


def admit_operation_id(decision_id):
    return _operation_id(SUCCESSOR_KIND, decision_id)


def verification_operation_id(successor_job_id):
    """ONE verification account per successor Job: the execution W385625 owns
    runs once for one admission, and a second account of its exit status is
    the fact a review-only admission would then have to choose between."""
    return _operation_id(VERIFICATION_KIND, successor_job_id)


def _committed(store, kind, operation_id, members, *, named=None,
               value=None):
    """One committed record of this store's journal, PROVED to be the one
    asked for.

    A SIGNATURE IS NOT OWNERSHIP -- `failure_analysis._committed`'s
    restatement of `ending._committed`'s correction, which applies here for
    its reason: a well-made record of another decision, copied through the
    public journal to this identity, would otherwise read as this one's.
    """
    row = store._connection.execute(
        "SELECT state, result FROM operations WHERE operation_id = ? AND "
        "kind = ?", (operation_id, kind)).fetchone()
    if row is None or row["state"] != "committed" or row["result"] is None:
        return None
    record = json.loads(row["result"])
    if type(record) is not dict or any(one not in record for one in members):
        _refuse(f"the committed {kind} record at {name_value(operation_id)} "
                f"is not one this build can read",
                category="integrity", code="schema")
    if named is not None and record[named] != value:
        _refuse(f"the committed {kind} record at {name_value(operation_id)} "
                f"names {named} {name_value(record[named])} and it was "
                f"selected as {name_value(value)}; a record is proved to be "
                f"the one asked for rather than merely well made",
                category="integrity", code="schema")
    return record


def _records_of(store, kind, members):
    held = []
    for row in store._connection.execute(
            "SELECT result FROM operations WHERE kind = ? AND state = "
            "'committed' AND result IS NOT NULL ORDER BY operation_id",
            (kind,)):
        record = json.loads(row["result"])
        if type(record) is not dict or any(one not in record
                                           for one in members):
            _refuse(f"this store holds a committed {kind} record this build "
                    f"cannot read", category="integrity", code="schema")
        held.append(record)
    return held


def decision_of(store, decision_id):
    return _committed(store, DECISION_KIND,
                      decision_operation_id(decision_id), DECISION_MEMBERS,
                      named="decision_id", value=decision_id)


def decisions_of(store):
    """Every owner decision this store holds, oldest operation identity first."""
    return _records_of(store, DECISION_KIND, DECISION_MEMBERS)


def decisions_for(store, key):
    boundaries.identity(key, "a failure key")
    return [one for one in decisions_of(store) if one["failure_key"] == key]


def successor_intent_of(store, decision_id):
    return _committed(store, SUCCESSOR_INTENT_KIND,
                      intent_operation_id(decision_id), INTENT_MEMBERS,
                      named="decision_id", value=decision_id)


def successor_of(store, decision_id):
    return _committed(store, SUCCESSOR_KIND,
                      admit_operation_id(decision_id), SUCCESSOR_MEMBERS,
                      named="decision_id", value=decision_id)


def successors_for(store, key):
    """Every reserved successor of one failure, admitted or not.

    THE INTENTS AND NOT THE ADMISSIONS, because the fence is about identities
    that are SPOKEN FOR: a reservation whose admission was interrupted owns
    its Job id and whatever it already published, and a second decision that
    walked past it would strand exactly that.
    """
    boundaries.identity(key, "a failure key")
    return [one for one in _records_of(store, SUCCESSOR_INTENT_KIND,
                                       INTENT_MEMBERS)
            if one["failure_key"] == key]


SUCCESSOR_DISPOSITIONS = ("undecided", "decided", "reserved", "admitted",
                          "verified")


def successor_disposition(store, decision_id):
    """THE CURRENT state of one decision's successor, DERIVED from records.

    `failure_analysis.recovery_disposition`'s rule, for its reason: this
    journal has no update, so a stored-and-moved state would be the second
    account of a fact the records already carry -- and the one that goes
    stale. The intent's own `state` member is the word it is BORN with and
    never moves; this is what a reader asks.
    """
    boundaries.identity(decision_id, "an owner decision id")
    decision = decision_of(store, decision_id)
    if decision is None:
        return SUCCESSOR_DISPOSITIONS[0]
    held = successor_of(store, decision_id)
    if held is not None:
        return ("verified" if verification_of(store, held["job_id"])
                is not None else "admitted")
    if successor_intent_of(store, decision_id) is not None:
        return "reserved"
    return "decided"


def verification_of(store, successor_job_id):
    return _committed(store, VERIFICATION_KIND,
                      verification_operation_id(successor_job_id),
                      VERIFICATION_MEMBERS, named="job_id",
                      value=successor_job_id)


# -- 6. the derived identities -----------------------------------------------

def successor_job_id(decision_id):
    """The successor Job identity, DERIVED from the owner's decision key.

    DERIVED RATHER THAN ALLOCATED, which is the contract's section 4 in one
    line: "Exact operation retry returns the committed decision/admission/
    effect". An admission that asked a counter for an identity would mint a
    second one after a crash and admit a second successor for one decision.
    Derived, every incarnation reaches the same name, so the reservation's
    primary key and the journal's replay are about the same Job.
    """
    boundaries.identity(decision_id, "an owner decision id")
    return f"recovery-{decision_id}"


def successor_submission_id(decision_id):
    return f"sub-{successor_job_id(decision_id)}"


def verification_attempt_id(decision_id):
    """The identity the manager's own isolated verification runs under.

    DERIVED HERE AND COMMITTED IN THE INTENT, before any execution exists, so
    W385625's adapter composes the execution this admission named rather than
    minting a second one -- `failure_analysis.analysis_attempt_id`'s rule for
    `AnalysisExecution`, applied to the execution this admission authorizes.
    """
    return f"verification-{successor_job_id(decision_id)}"


def review_stage_id(decision_id):
    return documents.stage_id(successor_job_id(decision_id), REVIEW_STAGE)


# -- 7. the owner-facing read ------------------------------------------------

READ_SCHEMA = "baton.v12.recovery-owner-item/1"


def _report_document(control, record):
    """The delivered diagnosis itself, resolved through the custody that holds
    it and HELD TO THE DIGEST this store journalled.

    READ RATHER THAN COPIED. Stage 1-A deliberately journals a BINDING -- the
    report's digest, the result it was read out of and the outputs the
    analysis wrote -- so this store never becomes a second copy of a
    diagnosis. The bytes live in the Worker Manager's retained manifest, and
    this reaches them through that owner and then proves they are the ones the
    owner item names.
    """
    frozen = frozen_output_of(control, record["analysis_attempt_id"])
    if frozen is None or frozen["manifest_digest"] != record["manifest_digest"]:
        _refuse(f"the analysis result {name_value(record['result_id'])} this "
                f"owner item names is not the one this host now holds for "
                f"attempt {name_value(record['analysis_attempt_id'])}; a "
                f"decision is taken on the diagnosis that was delivered",
                category="integrity", code="digest")
    result = load_manifest(control, record["manifest_digest"],
                           "resultManifest")
    if result is None:
        _refuse(f"this manager retains no result manifest at "
                f"{name_value(record['manifest_digest'])}; the delivered "
                f"diagnosis cannot be read back and a decision is not taken "
                f"on a report nobody can resolve")
    named = [one for one in result["outputs"]
             if one["name"] == failure_analysis.ANALYSIS_OUTPUT
             and one["status"] == "present"
             and type(one.get("result_metadata")) is dict
             and failure_analysis.REPORT_SCHEMA in one["result_metadata"]]
    if len(named) != 1:
        _refuse(f"the retained analysis result carries {len(named)} readable "
                f"{name_value(failure_analysis.ANALYSIS_OUTPUT)} reports; the "
                f"delivered diagnosis is exactly one",
                category="integrity", code="schema")
    held = failure_analysis.check_analysis_report(
        named[0]["result_metadata"][failure_analysis.REPORT_SCHEMA],
        what="the delivered analysis report")
    if failure_analysis.report_digest(held) != record["report_digest"]:
        _refuse(f"the retained report digests to "
                f"{name_value(failure_analysis.report_digest(held))} and this "
                f"failure's journalled analysis recorded "
                f"{name_value(record['report_digest'])}",
                category="integrity", code="digest")
    return held


def expected_facts(store, key):
    """THE FOUR DIGESTS AND THE ORIGINAL COMMAND a decision must bind.

    ONE FUNCTION FOR BOTH SIDES. The read surface reports these and `decide`
    compares them; computing them twice would be two spellings of one
    contract, and the first one to drift would refuse an owner for approving
    exactly what they were shown.

    `report_digest` IS `None` FOR A FINITE ENDING. An analysis that failed,
    expired, was cancelled or whose cessation is unknown delivered partial
    evidence and no diagnosis -- so there is no report digest to bind, and
    requiring one would make the four endings the contract delivers directly
    to the owner undecidable.
    """
    boundaries.identity(key, "a failure key")
    failure = failure_analysis.failure_of(store, key)
    if failure is None:
        _refuse(f"this store holds no retained failure {name_value(key)}")
    item = failure_analysis.owner_item_of(store, key)
    report = failure_analysis.report_of(store, key)
    reported = (item is not None
                and item["outcome"] == failure_analysis.REPORTED_OUTCOME)
    return {"failure_digest": failure["input_digest"],
            "report_digest": (report["report_digest"]
                              if reported and report is not None else None),
            "candidate_base": failure["candidate"]["base"],
            "candidate_head": failure["candidate"]["head"],
            "candidate_content_digest":
                failure["candidate"]["content_digest"],
            "original_argv": list(failure["verification"]["argv"])}


def owner_item_read(store, control, key, *, authorization=None, now=None):
    """WHAT THE OWNER IS LOOKING AT BEFORE THEY DECIDE. A READ, and it writes
    nothing.

    THE CONTRACT'S SECTION 2 AS ONE DOCUMENT: "The supported decision surface
    presents original verifier, exact correction, candidate and proposed
    verification/review scope before recording approval." Every member below
    is one of those facts, read through the owner that holds it, and the four
    digests a decision must bind are reported in the EXACT spelling `decide`
    compares, so an owner approving what they were shown cannot be refused for
    a transcription.

    IT ALSO SAYS WHAT IS ALREADY DECIDED. An owner item that already carries
    an approved decision and an admitted successor is not a second decision
    waiting to be taken, and a surface that went quiet about that would send
    the owner to perform an act the fence will refuse.
    """
    boundaries.identity(key, "a failure key")
    failure = failure_analysis.failure_of(store, key)
    if failure is None:
        _refuse(f"this store holds no retained failure {name_value(key)}; an "
                f"owner decides on an attributed ending and never on a key")
    item = failure_analysis.owner_item_of(store, key)
    report = failure_analysis.report_of(store, key)
    document = (None if report is None or item is None
                or item["outcome"] != failure_analysis.REPORTED_OUTCOME
                else _report_document(control, report))
    # THE EVIDENCE AS IT STANDS NOW, recomposed from the original attempt
    # through its owners and compared with what the analysis was admitted on.
    # Reported as a FACT rather than raised: an owner reading a held item is
    # owed the knowledge that its evidence moved, and `decide` is what
    # refuses to act on it.
    current, why = _evidence_now(store, control, key, failure)
    held = {
        "schema": READ_SCHEMA, "failure_key": key,
        "job_id": failure["job_id"], "stage_id": failure["stage_id"],
        "selectors": dict(failure["selectors"]),
        "disposition": failure_analysis.recovery_disposition(store, key),
        "owner_item": item,
        "report": {"record": report, "document": document},
        "candidate": dict(failure["candidate"]),
        "original_verification": dict(failure["verification"]),
        "declared_execution": dict(failure["execution"]),
        "cessation": dict(failure["cessation"]),
        "evidence": {"input_digest": failure["input_digest"],
                     "current_digest": current, "valid": current == failure[
                         "input_digest"], "why": why},
        # THE EXACT OPERANDS A DECISION BINDS, in the spelling `decide`
        # compares them in, from the one function that owns them.
        "expected": expected_facts(store, key),
        "proposed_correction": (None if document is None
                                else document["proposed_verification"]),
        "profile": resolved_profile(),
        "selectable_stages": [list(one) for one in SELECTED_STAGE_SETS],
        "decisions": [{"decision_id": one["decision_id"],
                       "disposition": one["disposition"],
                       "stages": one["stages"],
                       "decided_at": one["decided_at"],
                       "endpoint": one["owner"]["endpoint"]}
                      for one in decisions_for(store, key)],
        # EVERY SUCCESSOR THIS FAILURE RESERVED, with the three facts a
        # review-only decision has to name back. Reported rather than left to
        # be derived: the lineage operands are the expired successor, its
        # verification attempt and the DIGEST of its journalled passed
        # account, and an owner who had to compute that digest themselves
        # would be computing the thing the admission compares.
        "successors": [_successor_read(store, one)
                       for one in successors_for(store, key)],
        "fence": cancellation.fence_of(store, failure["job_id"]),
    }
    if authorization is not None:
        # WHETHER THE ASKER MAY ACTUALLY DO IT, in the Work's own scope.
        # `disposition_command._pending`'s rule: an operator told an act is
        # due and not told they hold no grant for it learns that from a
        # refusal later, and holding a capability is not using it.
        try:
            held["authorization"] = _owner(authorization,
                                           failure["selectors"]["work_id"],
                                           what="the owner authorization port")
            held["authorization"]["holds"] = True
        except ContractRefusal as refusal:
            held["authorization"] = {
                "participant": getattr(authorization, "participant", None),
                "holds": False,
                "why": {"category": refusal.category, "code": refusal.code,
                        "message": refusal.message}}
    if now is not None:
        held["control"] = job_control.report(store, failure["job_id"],
                                             now=now)
    return held


def _successor_read(store, intent):
    held = verification_of(store, intent["job_id"])
    return {"decision_id": intent["decision_id"], "job_id": intent["job_id"],
            "state": intent["state"], "stages": intent["stages"],
            "disposition": successor_disposition(store,
                                                 intent["decision_id"]),
            "admitted": successor_of(store, intent["decision_id"])
            is not None,
            "verification_attempt_id": intent["verification_attempt_id"],
            "review_stage_id": intent["review_stage_id"],
            "fence": cancellation.fence_of(store, intent["job_id"]),
            "verification": held,
            "verification_result_digest": (None if held is None
                                           else digest(held))}


def _evidence_now(store, control, key, failure):
    """`(digest, why)` for the failure's own fixed input AS IT STANDS NOW.

    Recomposed through `classified_failure`, which is the trigger's own
    validated reader: the retained bytes, the artifact bindings, the measured
    tree, the agreement between the worker's claim and its own observation and
    the successful provider turn. A candidate that no longer validates answers
    `(None, <typed reason>)` -- REC-8: "A candidate failing identity or digest
    validation MUST be reported and is not recovery input."
    """
    try:
        current = failure_analysis.classified_failure(
            control, failure["selectors"]["attempt_id"])
        fixed = failure_analysis.analysis_input(
            current, failure_key=key, job_id=failure["job_id"],
            stage_id=failure["stage_id"], episode=failure["episode"])
    except ContractRefusal as refusal:
        return None, {"category": refusal.category, "code": refusal.code,
                      "message": refusal.message}
    return failure_analysis.input_digest(fixed), None


# -- 8. the owner decision ---------------------------------------------------

def decide(store, control, *, key, decision_id, disposition, authorization,
           expected, correction, profile, profile_digest, stages,
           lineage=None, now=None):
    """Record ONE owner disposition on one retained verification failure.

    EVERY COMPARISON BEFORE THE WRITE, and the write is one journal act. What
    is compared is the whole of the contract's section 3 step 3 -- the owner's
    identity and scope, the exact referenced inputs, the correction, the
    verification/review-only scope and the approved profile -- plus the thing
    an owner cannot check for themselves: whether the evidence still is what
    the analysis was admitted on.

    A DISPOSITION IS NOT AN ADMISSION. This operation launches nothing, even
    for `approved`: `admit_successor` is a separate act with its own identity,
    its own owner ports and its own fences, so a crash between them leaves a
    decision that can be carried out rather than an effect nobody decided.
    """
    boundaries.identity(key, "a failure key")
    boundaries.identity(decision_id, "an owner decision id")
    if disposition not in DISPOSITIONS:
        _refuse(f"an owner disposition is one of {', '.join(DISPOSITIONS)}; "
                f"this is {name_value(disposition)}",
                category="integrity", code="schema")
    decided_at = boundaries.instant(now if now is not None else store._now(),
                                    "an owner decision instant")
    failure = failure_analysis.failure_of(store, key)
    if failure is None:
        _refuse(f"this store holds no retained failure {name_value(key)}; an "
                f"owner decision is recorded for an attributed ending")
    item = failure_analysis.owner_item_of(store, key)
    if item is None:
        _refuse(f"failure {name_value(key)} has delivered no owner item; the "
                f"decision surface presents a DELIVERED diagnosis or finite "
                f"ending, and deciding before Stage 1-A has delivered one "
                f"would be deciding about evidence nobody was shown")
    # WHO IS DECIDING, FIRST. Everything below is a pure read, so the order
    # changes no effect -- what it changes is the sentence an unauthorized
    # caller is given: "you hold no decision capability in this Work's scope"
    # rather than a digest comparison they were never entitled to make.
    owner = _owner(authorization, failure["selectors"]["work_id"],
                   what="the owner authorization port")
    taken = _expected(expected)
    selected = owned_stages(stages)
    held = _lineage(lineage)
    corrected = _correction(correction, original=taken["original_argv"])

    # -- the approved profile, by exact agreement.
    policy = resolved_profile(boundaries.text(profile,
                                              "the approved profile identity"))
    if boundaries.text(profile_digest,
                       "the approved profile digest") != policy["digest"]:
        _refuse(f"the decision names profile digest "
                f"{name_value(profile_digest)} and {name_value(profile)} "
                f"digests to {name_value(policy['digest'])}; the owner's "
                f"decision names the profile and admission checks exact "
                f"agreement", category="integrity", code="digest")

    # -- the facts the owner says they were looking at.
    report = failure_analysis.report_of(store, key)
    reported = item["outcome"] == failure_analysis.REPORTED_OUTCOME
    wanted = expected_facts(store, key)
    for member in EXPECTED_MEMBERS:
        if taken[member] != wanted[member]:
            _refuse(f"this decision expects {member} "
                    f"{name_value(json.dumps(taken[member]))} and failure "
                    f"{name_value(key)} records "
                    f"{name_value(json.dumps(wanted[member]))}; an owner "
                    f"decides on the exact failure, report, candidate and "
                    f"verifier they actually read",
                    category="integrity", code="digest")

    # -- and the evidence as it stands NOW, which the owner cannot check.
    current, why = _evidence_now(store, control, key, failure)
    if current is None:
        _refuse(f"the retained candidate of failure {name_value(key)} no "
                f"longer validates ({why['category']}/{why['code']}: "
                f"{why['message']}); an invalid candidate is reported and is "
                f"not recovery input",
                category=why["category"], code=why["code"])
    if current != failure["input_digest"]:
        _refuse(f"the original evidence of failure {name_value(key)} now "
                f"digests to {name_value(current)} and its delivered analysis "
                f"was admitted on {name_value(failure['input_digest'])}; a "
                f"decision is not recorded against evidence that changed "
                f"under it", category="integrity", code="digest")

    proposed = None
    if reported:
        document = _report_document(control, report)
        proposed = (None if document["proposed_verification"] is None
                    else digest(document["proposed_verification"]))

    # -- review-only is authorized against still-valid exact evidence.
    if selected == REVIEW_ONLY_STAGES:
        if held is None:
            _refuse(f"a {json.dumps(list(REVIEW_ONLY_STAGES))} successor is "
                    f"the post-verification disposition and names the expired "
                    f"successor, its verification attempt and the passed "
                    f"result it reuses; this decision names no lineage")
        _review_only_evidence(store, control, key, held,
                              candidate=failure["candidate"],
                              correction=corrected)
    elif held is not None:
        _refuse(f"a {json.dumps(list(FULL_STAGES))} successor verifies the "
                f"candidate itself and reuses no prior verification; this "
                f"decision names a review-only lineage")

    if disposition == APPROVED:
        # A CANCELLED JOB IS NEVER REVIVED, and an approval of one would be a
        # decision nothing may carry out. Read through the fence's owner, and
        # an EXPIRY is deliberately not a refusal: the contract keeps expired
        # original deadlines expired and unchanged and gives the successor its
        # own admission and its own clocks.
        _refuse_cancelled(store._connection, failure["job_id"],
                          "an approved recovery decision")
        job_control.refuse_uncertain(store._connection, failure["job_id"],
                                     "a recovery decision about it",
                                     now=decided_at)

    record = {"failure_key": key, "decision_id": decision_id,
              "disposition": disposition, "owner": owner,
              "job_id": failure["job_id"], "stage_id": failure["stage_id"],
              "expected": taken, "proposed_digest": proposed,
              "correction": corrected, "profile": policy["profile"],
              "profile_digest": policy["digest"], "stages": list(selected),
              "lineage": held, "item_outcome": item["outcome"],
              "decided_at": decided_at}
    # THE REPLAY IDENTITY IS THE DECISION AND NOT THE CLOCK THAT TOOK IT, nor
    # the policy generation that happened to be in force when a retry arrived.
    # `failure_analysis.record_analysis_intent`'s split, for its reason: the
    # committed record carries the instant and the resolved authorization, and
    # the SIGNATURE carries the facts that make this the same decision. An
    # exact retry therefore replays the committed bytes rather than being
    # re-authorized against today's policy, which is what effectively-once
    # means for an act that already happened.
    operands = {name: record[name] for name in DECISION_MEMBERS
                if name not in ("decided_at", "owner")}
    operands["endpoint"] = owner["endpoint"]
    operands["principal"] = owner["principal"]
    operands["effective_scope"] = owner["effective_scope"]

    def act(connection):
        if disposition == APPROVED:
            # THE PER-FAILURE FENCE, DECIDED UNDER THE SAME WRITE LOCK as the
            # record. Two concurrent owner decisions meet here rather than at
            # a read, which is the whole of "a unique per-failure recovery
            # admission fence prevents concurrent decisions producing
            # conflicting successors".
            _fenced_decision(connection, store, key, decision_id,
                             stages=selected, lineage=held)
            _refuse_cancelled(connection, failure["job_id"],
                              "an approved recovery decision")
        return record

    return store.transact(decision_operation_id(decision_id), DECISION_KIND,
                          job_signature(DECISION_KIND, operands), act)


def _refuse_cancelled(connection, job_id, what):
    """An EXPLICIT cancellation refuses; a reached deadline does not.

    THE TWO TRIGGERS ARE TWO FACTS and the contract treats them differently.
    Section 4: "Cancellation of the target or successor blocks new admission;
    a cancelled execution is never revived." Section 5 and 3.7: "Expired
    original deadlines remain unchanged" and the successor "has its own
    explicitly selected admission/limits". A retained verification failure is
    ordinarily decided about well after the Job that produced it reached its
    own wall -- refusing on that would make the whole recovery unreachable in
    its own commonest case, while refusing on a cancellation is the ruling.
    """
    held = cancellation.fenced(connection, job_id)
    if held is not None and held.get("trigger", "operator") == "operator":
        _refuse(f"Job {name_value(job_id)} was cancelled at "
                f"{held['requested_at']} ({held['reason']}); {what} is not "
                f"admitted after an explicit cancellation, and a cancelled "
                f"execution is never revived")
    return held


def _fenced_decision(connection, store, key, decision_id, *, stages,
                     lineage):
    """At most one LIVE successor per failure, and one review-only successor
    per expired one.

    WHAT THIS REFUSES AND WHY IT IS NOT A RETRY GATE. A second FULL approval
    of one failure would admit a second verification of one candidate under
    one owner item -- the duplicate the contract's admission fence exists to
    prevent. A renewed verification failure is a DIFFERENT failure key with
    its own analysis and its own owner item, and the review-only disposition
    of section 3.7 is admitted here by naming the successor it follows. So
    "another successor requires a new owner decision" stays true without this
    becoming a way to loop.
    """
    for one in _records_of(store, SUCCESSOR_INTENT_KIND, INTENT_MEMBERS):
        if one["failure_key"] != key or one["decision_id"] == decision_id:
            continue
        if tuple(stages) == FULL_STAGES:
            _denied(f"failure {name_value(key)} already reserved the "
                    f"verification/review successor "
                    f"{name_value(one['job_id'])} under decision "
                    f"{name_value(one['decision_id'])}; one retained failure "
                    f"has one such successor, and a further round is a new "
                    f"owner decision on new evidence rather than a second "
                    f"admission of this one")
        if lineage is not None \
                and tuple(one["stages"]) == REVIEW_ONLY_STAGES \
                and (one.get("lineage") or {}).get("successor_job_id") \
                == lineage["successor_job_id"]:
            _denied(f"the expired successor "
                    f"{name_value(lineage['successor_job_id'])} already has "
                    f"the review-only successor {name_value(one['job_id'])} "
                    f"under decision {name_value(one['decision_id'])}; a "
                    f"second one would review one candidate twice on one "
                    f"owner decision")
    return None


# -- 9. the successor's own verification account ------------------------------

def record_verification(store, control, *, decision_id, outcome, exit_status,
                        argv, context_digest, result_digest=None, now=None):
    """Journal WHAT ONE SUCCESSOR'S VERIFICATION DID, effectively once.

    THE CONTRACT OF THE RECORD IS THIS SLICE'S AND THE EXECUTION IS W385625's.
    A review-only admission is authorized only against "exact candidate/
    verifier/result evidence", so the shape of that evidence, its identity and
    its validation belong with the admission that consumes it. Running the
    approved corrected command against a materialized retained candidate,
    reading its exit status and retaining its output belong with the verifier
    execution adapter, which is the next slice. This operation is what that
    adapter calls; nothing here starts, materializes or observes anything.

    THE CANDIDATE IS REVALIDATED THROUGH ITS OWNERS BEFORE THE RECORD EXISTS.
    An account of a verification that names a candidate this host no longer
    holds in the bytes the admission bound is not evidence about that
    candidate, and it must not become the thing a later review-only admission
    trusts.
    """
    boundaries.identity(decision_id, "an owner decision id")
    if outcome not in VERIFICATION_OUTCOMES:
        _refuse(f"a successor verification outcome is one of "
                f"{', '.join(VERIFICATION_OUTCOMES)}; this is "
                f"{name_value(outcome)}", category="integrity", code="schema")
    if type(exit_status) is not int or type(exit_status) is bool:
        _refuse("a successor verification exit status is a whole number",
                category="integrity", code="schema")
    if (outcome == "passed") != (exit_status == 0):
        _refuse(f"this account says the verification {name_value(outcome)} "
                f"and exited {exit_status}; a passed required verification "
                f"exits 0 and nothing else does",
                category="integrity", code="schema")
    held = successor_of(store, decision_id)
    if held is None:
        _refuse(f"this store holds no admitted successor for decision "
                f"{name_value(decision_id)}; a verification account belongs "
                f"to an admitted execution and never to one nobody admitted")
    if _argv(argv, "the executed verification command") \
            != held["correction"]["argv"]:
        _refuse(f"this account names a command the owner did not approve for "
                f"successor {name_value(held['job_id'])}; the approved "
                f"correction is {sample_of(held['correction']['argv'])}",
                category="integrity", code="schema")
    if boundaries.text(context_digest, "the executed context digest") \
            != held["correction"]["context_digest"]:
        _refuse(f"this account names execution context "
                f"{name_value(context_digest)} and the owner approved "
                f"{name_value(held['correction']['context_digest'])}; a "
                f"command string must not hide a changed execution context",
                category="integrity", code="digest")
    candidate = _candidate_now(store, control, held["failure_key"],
                               expected=held["candidate"])
    record = {"failure_key": held["failure_key"], "decision_id": decision_id,
              "job_id": held["job_id"],
              "verification_attempt_id": held["verification_attempt_id"],
              "outcome": outcome, "exit_status": exit_status,
              "argv": list(held["correction"]["argv"]),
              "context_digest": held["correction"]["context_digest"],
              "candidate": candidate,
              "result_digest": (None if result_digest is None
                                else boundaries.text(
                                    result_digest,
                                    "a retained verification result digest")),
              "concluded_at": boundaries.instant(
                  now if now is not None else store._now(),
                  "a verification conclusion instant")}
    operands = {name: record[name] for name in VERIFICATION_MEMBERS
                if name != "concluded_at"}
    return store.transact(verification_operation_id(held["job_id"]),
                          VERIFICATION_KIND,
                          job_signature(VERIFICATION_KIND, operands),
                          lambda connection: record)


def _candidate_now(store, control, key, *, expected):
    """The retained candidate AS IT STANDS NOW, held to the bytes bound.

    THROUGH THE OWNING READER. `classified_failure` is the trigger's own
    validated candidate reader -- artifact identity, this manager's own
    artifact row, the measured tree digest and the agreement between the
    worker's claim and its own ordinary-test observation -- so nothing here
    re-opens custody, re-measures a tree or re-derives a digest. What this
    adds is the comparison with what an admission or a decision BOUND.
    """
    failure = failure_analysis.failure_of(store, key)
    if failure is None:
        _refuse(f"this store holds no retained failure {name_value(key)}")
    current = failure_analysis.classified_failure(
        control, failure["selectors"]["attempt_id"])["candidate"]
    for member in ("base", "head", "content_digest", "tree_digest",
                   "artifact_id"):
        if current[member] != expected[member]:
            _refuse(f"the retained candidate now names {member} "
                    f"{name_value(current[member])} and this operation is "
                    f"bound to {name_value(expected[member])}; the candidate "
                    f"before and after a recovery is one candidate",
                    category="integrity", code="digest")
    return dict(current)


def _review_only_evidence(store, control, key, lineage, *, candidate,
                          correction):
    """IS THE PASSED VERIFICATION STILL EXACTLY VALID? Refuse, or answer it.

    THE CONTRACT'S SECTION 3.7, clause by clause. A review-only admission is
    authorized when, and only when:

      the named prior successor is one THIS failure reserved -- not any Job
        that happens to carry the name;
      it is ENDED, by its own expiry or cancellation, read through the fence's
        owner. A successor still running is not expired, and admitting a
        review of it would put two executions on one candidate;
      its journalled verification PASSED, exited 0, and names the exact
        approved command, execution context and candidate;
      the result the lineage names is the result that was journalled; and
      the retained candidate STILL validates now, in the bytes the passed
        verification was about.

    ABSENT, MISMATCHED, INVALIDATED OR UNKNOWN REFUSES and says which. "Time
    expiry alone does not invalidate successful verification", and an invalid
    result never authorizes blind re-verification: a required new verification
    is a new owner-approved correction through this same contract.
    """
    reserved = None
    for one in successors_for(store, key):
        if one["job_id"] == lineage["successor_job_id"]:
            reserved = one
    if reserved is None:
        _refuse(f"failure {name_value(key)} reserved no successor "
                f"{name_value(lineage['successor_job_id'])}; a review-only "
                f"admission follows THIS failure's own expired successor")
    if tuple(reserved["stages"]) != FULL_STAGES:
        _refuse(f"successor {name_value(reserved['job_id'])} was admitted for "
                f"{json.dumps(reserved['stages'])} and a review-only "
                f"admission follows the one that carried the verification")
    fence = cancellation.fence_of(store, reserved["job_id"])
    if fence is None:
        _refuse(f"successor {name_value(reserved['job_id'])} is neither "
                f"expired nor cancelled; a review-only admission is the "
                f"disposition for a successor whose verification PASSED and "
                f"whose review did not complete before it expired, and "
                f"admitting one beside a live successor would review one "
                f"candidate twice")
    if fence.get("trigger", "operator") == "operator":
        _refuse(f"successor {name_value(reserved['job_id'])} was cancelled at "
                f"{fence['requested_at']} ({fence['reason']}); a cancelled "
                f"execution is never revived and its review is not admitted "
                f"under a new identity")
    verification = verification_of(store, reserved["job_id"])
    if verification is None:
        _refuse(f"successor {name_value(reserved['job_id'])} journalled no "
                f"verification account; whether its verification passed is "
                f"UNKNOWN, unknown refuses, and this is not permission to "
                f"verify the candidate again")
    if verification["outcome"] != "passed":
        _refuse(f"successor {name_value(reserved['job_id'])}'s verification "
                f"is {name_value(verification['outcome'])} (exit "
                f"{verification['exit_status']}); a review-only admission "
                f"reuses a PASSED verification, and a failed or unaccounted "
                f"one is disposed of explicitly rather than reviewed")
    if verification["verification_attempt_id"] \
            != lineage["verification_attempt_id"]:
        _refuse(f"this decision names verification attempt "
                f"{name_value(lineage['verification_attempt_id'])} and "
                f"successor {name_value(reserved['job_id'])} journalled "
                f"{name_value(verification['verification_attempt_id'])}; a "
                f"late result of another execution cannot satisfy this one by "
                f"identity substitution",
                category="integrity", code="schema")
    if lineage["verification_result_digest"] != digest(verification):
        _refuse(f"this decision names verification result "
                f"{name_value(lineage['verification_result_digest'])} and the "
                f"journalled account digests to "
                f"{name_value(digest(verification))}; the evidence a "
                f"review-only admission reuses is exact",
                category="integrity", code="digest")
    if verification["argv"] != list(correction["argv"]) \
            or verification["context_digest"] != correction["context_digest"]:
        _refuse(f"the passed verification of successor "
                f"{name_value(reserved['job_id'])} ran "
                f"{sample_of(verification['argv'])} and this decision "
                f"approves {sample_of(correction['argv'])}; omitting a "
                f"verification stage preserves the verification that actually "
                f"ran rather than claiming a different one",
                category="integrity", code="schema")
    for member in ("base", "head", "content_digest"):
        if verification["candidate"][member] != candidate[member]:
            _refuse(f"the passed verification names candidate {member} "
                    f"{name_value(verification['candidate'][member])} and "
                    f"this failure's retained candidate is "
                    f"{name_value(candidate[member])}",
                    category="integrity", code="digest")
    # AND THE BYTES, NOW. Everything above is a comparison of records; this
    # is the one clause that asks the host whether the candidate those
    # records are about still exists in the form they describe.
    _candidate_now(store, control, key,
                   expected=verification["candidate"])
    return {"prior_job_id": reserved["job_id"],
            "fence": {"trigger": fence.get("trigger", "operator"),
                      "requested_at": fence["requested_at"],
                      "operation_id": fence["operation_id"]},
            "verification": verification}


# -- 10. the successor admission ---------------------------------------------

def admit_successor(store, control, *, decision_id, exclusion,
                    authorization, binding, ownership, now=None):
    """Admit THE one linked verification/review-only successor of one approved
    owner decision, or replay having done so.

    THE ORDER OF THE CUTS IS THE RECOVERY STORY, and it is `fresh_attempt`'s
    order for `fresh_attempt`'s reasons -- REC-7 settled them and REC-8
    composes the same owners:

      1. read the committed decision and the failure it is about; a denied or
         held disposition admits nothing
      2. recheck the fences: cancellation of the target, uncertain timing
      3. require the host to have CEASED every prior runtime and RETURNED its
         resource; unknown refuses
      4. CUT A: reserve the successor identity and write the durable intent,
         under the per-failure fence, inside this store's write lock
      5. re-ask the host, because a check before a reservation is a check
         about the past
      6. CUT B: the Work authorization (REUSED; the failed Job's Work is this
         deployment's and its configured workers already serve it), then the
         deployment binding, then servability for every selected Job stage
      7. CUT C: the submission, which is where the successor becomes real and
         where LIM-5 journals its own admitted control, then the completion

    NOTHING OUTSIDE THIS STORE IS TOUCHED BEFORE CUT A, and a refusal past it
    says so rather than claiming it changed nothing.
    """
    boundaries.identity(decision_id, "an owner decision id")
    for port, what in ((exclusion, "the host exclusion port"),
                       (authorization, "the Work authorization port"),
                       (binding, "the deployment binding port"),
                       (ownership, "the instance ownership port")):
        if port is None:
            _refuse(f"a retained-recovery admission composes four owners "
                    f"and {what} is absent; this operation does not decide "
                    f"an owner's fact for it by assuming one",
                    category="integrity", code="schema")
    # ONE INSTANCE, AGREED BY EVERY OWNER, BEFORE ANYTHING IS READ OR DONE.
    # The rule, its refusals and its reasons are `fresh_attempt`'s, read from
    # that module rather than restated: review R14, R17 and R18 are about
    # composing owner ports over somebody else's deployment, and a second
    # implementation here would be a second chance to get them wrong.
    fresh_attempt.one_instance(
        store, {"the host exclusion port": exclusion,
                "the Work authorization port": authorization,
                "the deployment binding port": binding,
                "the instance ownership port": ownership})

    decision = decision_of(store, decision_id)
    if decision is None:
        _refuse(f"this store holds no owner decision "
                f"{name_value(decision_id)}; a successor is admitted on a "
                f"committed decision and never on a caller's claim about one")
    if decision["disposition"] != APPROVED:
        _denied(f"owner decision {name_value(decision_id)} is "
                f"{name_value(decision['disposition'])}; a denial or a hold "
                f"launches nothing, and a later approval is a NEW decision "
                f"identity rather than a second reading of this one")
    key = decision["failure_key"]
    failure = failure_analysis.failure_of(store, key)
    if failure is None:                                   # pragma: no cover
        _refuse(f"this store holds no retained failure {name_value(key)} the "
                f"committed decision {name_value(decision_id)} is about",
                category="integrity", code="schema")
    _agreeing_control(control, exclusion)
    prior = _prior(store, failure["job_id"],
                   attempt_id=failure["selectors"]["attempt_id"],
                   lineage=decision["lineage"])
    job_id = successor_job_id(decision_id)
    operands = {"failure_key": key, "decision_id": decision_id,
                "job_id": job_id, "prior_job_id": prior["job_id"],
                "work_id": prior["work_id"],
                "submission_id": successor_submission_id(decision_id),
                "stages": list(decision["stages"])}

    # A REPLAY ANSWERS BEFORE ANY OWNER IS ASKED ANYTHING. The whole operation
    # is already recorded, so re-deriving its preconditions would mean a
    # completed admission could start refusing later because the host moved on
    # -- the stale-check defect REC-7 removed.
    found, value = store.replay(admit_operation_id(decision_id),
                                job_signature(SUCCESSOR_KIND, operands),
                                kind=SUCCESSOR_KIND)
    if found:
        return value

    admitted_at = boundaries.instant(now if now is not None else store._now(),
                                     "a successor admission instant")
    fence = _refuse_cancelled(store._connection, prior["job_id"],
                              "a retained-recovery successor")
    job_control.refuse_uncertain(store._connection, prior["job_id"],
                                 "a retained-recovery successor of it",
                                 now=admitted_at)
    # THE CANDIDATE BYTES, THROUGH THEIR OWNERS, before anything is reserved.
    candidate = _candidate_now(store, control, key,
                               expected=failure["candidate"])
    if tuple(decision["stages"]) == REVIEW_ONLY_STAGES:
        _review_only_evidence(store, control, key, decision["lineage"],
                              candidate=candidate,
                              correction=decision["correction"])
    document = _composed(prior, decision, job_id=job_id,
                         submission_id=operands["submission_id"])

    with ownership.held() as owner, ownership.invocation(job_id):
        return _owned(store, prior=prior, decision=decision,
                      operands=operands, document=document,
                      candidate=candidate, admitted_at=admitted_at,
                      fence=fence, exclusion=exclusion,
                      authorization=authorization, binding=binding,
                      owner=owner)


def _agreeing_control(control, exclusion):
    """The control store the candidate is read from is the HOST PORT's own.

    Review R14's rule in `fresh_attempt`, applied to the one operand this
    operation takes that the ports do not supply: a handle the exclusion port
    would have refused must not reach this admission through a second door.
    The port already declares which instance it answers for, so the
    comparison is against that declaration rather than against another
    operand.
    """
    declared = getattr(exclusion, "instance", None)
    held = declared() if callable(declared) else None
    expected = (held or {}).get("control_store")
    here = getattr(control, "database", None)
    if expected is not None \
            and os.path.realpath(str(here or "")) \
            != os.path.realpath(str(expected)):
        _refuse(f"this admission reads the retained candidate from "
                f"{name_value(here)} and instance "
                f"{name_value((held or {}).get('root'))} owns "
                f"{name_value(expected)}; evidence about a failed execution "
                f"read from another deployment's store is evidence about "
                f"another deployment")
    return control


def _prior(store, job_id, *, attempt_id, lineage=None):
    """The failed Job, its stages and the review profile its successor reuses.

    THE SUBMITTED DOCUMENT IS THE SPECIFICATION, exactly as it is for a fresh
    attempt -- rebuilding an entry out of rows would silently normalize it.
    What this successor carries forward is deliberately NARROWER than a fresh
    attempt's: the input and policy digests and the review stage's own
    profile, because those are what make the configured pool able to serve it
    without per-recovery installation. The stage SET is the owner's, the
    control profile is the owner's, and the implementation stage is gone.
    """
    held = submission.job_of(store, job_id)
    if held is None:
        _refuse(f"this store holds no Job {name_value(job_id)}")
    stages = submission.stages_of(store, job_id)
    recorded = submission.submission_of(store, held["submission_id"])
    if recorded is None:
        _refuse(f"Job {name_value(job_id)} names submission "
                f"{name_value(held['submission_id'])} and this store holds no "
                f"such submission; the specification its successor is derived "
                f"from is that document's")
    entry = None
    for one in json.loads(recorded["document"])["jobs"]:
        if one["job_id"] == job_id:
            entry = one
    if entry is None:                                     # pragma: no cover
        _refuse(f"submission {name_value(held['submission_id'])} records Job "
                f"{name_value(job_id)} and its document does not carry it",
                category="integrity", code="schema")
    review = None
    for one in entry["stages"]:
        if one["kind"] == REVIEW_STAGE:
            review = one
    if review is None:
        _refuse(f"Job {name_value(job_id)} carries no {name_value(REVIEW_STAGE)} "
                f"stage; its successor hands the retained candidate to the "
                f"independent review this deployment already configures for "
                f"it, and there is no configured profile here to reuse")
    works = {stage["work_id"] for stage in stages}
    if len(works) != 1:
        _refuse(f"Job {name_value(job_id)}'s stages name "
                f"{sample_of(sorted(works))}; a retained-recovery successor "
                f"inherits one Work and this build cannot choose between them")
    # EVERY EXECUTION WHOSE RUNTIME MUST BE OVER, and the failed attempt is
    # in the set BY NAME rather than only through the episodes. The failure
    # record's own selectors name the attempt that produced the retained
    # candidate; an exclusion asked only about the episodes this store happens
    # to carry would skip exactly the execution the recovery is about when a
    # correction round or a restart left its episode elsewhere.
    #
    # AND A REVIEW-ONLY ADMISSION ADDS THE EXPIRED SUCCESSOR'S OWN. Its
    # review attempts and the isolated verification the manager ran for it are
    # executions against the same candidate and the same workspace resource;
    # "unknown is a hold" applies to them exactly as it applies to the
    # original.
    from . import episodes

    attempts = {attempt_id}
    named = [job_id]
    if lineage is not None:
        named.append(lineage["successor_job_id"])
        attempts.add(lineage["verification_attempt_id"])
    for one in named:
        for stage in submission.stages_of(store, one):
            for episode in episodes.episodes_of(store, stage["stage_id"]):
                attempts.add(episode["attempt_id"])
    return {"job_id": job_id, "entry": entry, "review": review,
            "schema": documents.SUBMISSION_CONTROL_SCHEMA,
            "submission_id": held["submission_id"],
            "work_id": sorted(works)[0], "attempt_ids": sorted(attempts)}


def _composed(prior, decision, *, job_id, submission_id):
    """THE SUCCESSOR'S OWN SPECIFICATION, and look at what is not in it.

    NO IMPLEMENTATION STAGE, no dependency on the failed Job, no correction
    allowance and no second attempt at the task. One `review` stage on the
    failed Job's own Work, carrying the review profile this deployment already
    configured, under the OWNER-APPROVED control profile rather than the one
    the failed Job was admitted under -- which is the difference between this
    and REC-7's specification-preserving fresh attempt, stated as a document.

    THE EXECUTION LIMITS ARE OMITTED ON PURPOSE. The approved profile pins the
    provider turn at 3600 s and each verification command at 900 s, and those
    are this build's own runner defaults -- `job_control.agreeing` proves the
    agreement at submit either way, and stating them again here would be a
    second account of two ceilings the profile already owns.
    """
    entry = {"job_id": job_id,
             "input_digest": prior["entry"]["input_digest"],
             "policy_digest": prior["entry"]["policy_digest"],
             "test_scope": list(prior["entry"]["test_scope"]),
             "terminal_policy": prior["entry"]["terminal_policy"],
             "stages": [{"kind": REVIEW_STAGE, "work_id": prior["work_id"],
                         "profile_name": prior["review"]["profile_name"],
                         "profile_digest": prior["review"]["profile_digest"],
                         "depends_on": []}],
             "control": {"profile": decision["profile"]}}
    return documents.owned_submission(
        {"schema": prior["schema"], "submission_id": submission_id,
         "jobs": [entry]})


def _owned(store, *, prior, decision, operands, document,
           candidate, admitted_at, fence, exclusion, authorization, binding,
           owner):
    """Everything that happens while this process owns the instance."""
    job_id = operands["job_id"]
    key = operands["failure_key"]
    evidence = _excluded(exclusion, prior["attempt_ids"], when="before")

    # -- CUT A: THE RESERVATION COMES FIRST, BEFORE ANY OTHER OWNER IS
    #    MUTATED. `fresh_attempt`'s review R4: an admission that authorized
    #    the Work first minted one on the Authority and THEN refused as a
    #    collision -- an effect performed for an operation never admitted.
    bounds = admitted_bounds(resolved_profile(decision["profile"]),
                             admitted_at=admitted_at,
                             stages=decision["stages"])
    _reserved(store, operands, decision, candidate=candidate,
              bounds=bounds, document=document)

    # -- re-ask, because cut A took time and a reservation is not a lock on
    #    somebody else's store.
    evidence = _excluded(exclusion, prior["attempt_ids"], when="after",
                         reserved=job_id)

    # -- CUT B: the Work authorization, then the binding, both AFTER the
    #    reservation and both idempotent.
    authorized = _authorized(authorization, operands["work_id"],
                             reserved=job_id)
    bound = _bound(binding, store, job_id=job_id,
                   prior_job_id=prior["job_id"],
                   work_id=operands["work_id"], document=document,
                   reserved=job_id)

    # -- CUT C: the submission, and the completion that closes the intent.
    try:
        intent = successor_intent_of(store, decision["decision_id"])
        if intent is None or intent["job_id"] != job_id or intent["candidate"] != candidate:
            _refuse("successor submission requires its exact retained reservation")
        expected = _composed(prior, decision, job_id=job_id, submission_id=operands["submission_id"])
        if document != expected:
            _refuse("successor submission differs from its approved decision")
        recorded = submission._submit_owned(store, document)
    except ContractRefusal as refusal:
        if refusal.code == "operation-collision":
            _refuse(f"the submission for this successor collided with an "
                    f"operation this store had already settled: "
                    f"{refusal.message}. The successor identity "
                    f"{name_value(job_id)} is RESERVED and its binding may "
                    f"already be published; repeating this request cannot "
                    f"change an immutable outcome, so this recovery needs a "
                    f"new owner decision identity")
        raise _incomplete(f"the submission for this successor was refused: "
                          f"{refusal.message}", reserved=job_id) from refusal
    return _completed(store, operands, decision=decision, candidate=candidate,
                      bounds=bounds, evidence=evidence, fence=fence,
                      authorized=authorized, bound=bound, recorded=recorded)


def _incomplete(why, *, reserved):
    """A refusal AFTER the reservation, which says so.

    `fresh_attempt._incomplete`'s correction, in this operation's own words: a
    reserved identity with no Job is a real, recorded, resumable state, and an
    operator told "nothing happened" would go looking for a row that is there.
    """
    return ContractRefusal(
        "refused", "precondition",
        f"{why}. The successor identity {name_value(reserved)} is already "
        f"RESERVED in this store and this admission is incomplete rather than "
        f"undone: correct what is named above and run the same request again, "
        f"which resumes from the reservation. A different request under this "
        f"decision is refused as the collision it is")


def _refusing(why, reserved):
    if reserved is None:
        return ContractRefusal("refused", "precondition", why)
    return _incomplete(why, reserved=reserved)


def _excluded(exclusion, attempt_ids, *, when, reserved=None):
    """The host has ceased every prior runtime and released every resource.

    FAIL CLOSED, which is REC-7's "unknown prior execution must not permit
    conflicting effects" and REC-8's "Cancellation and unknown prior cessation
    cannot authorize conflicting execution". There are three answers and only
    one of them is permission: ceased, still going, and NOBODY KNOWS.

    THE VOCABULARIES ARE READ FROM THEIR OWNER. `fresh_attempt.CEASED_RUNTIME`
    and `SETTLED_CLEANUP` are the Worker Manager's axis words as that module
    already resolved them; restating them here would be a second guess at
    which states mean "over".
    """
    evidence = {}
    held = exclusion.evidence_of(tuple(attempt_ids))
    boundaries.document(held if isinstance(held, dict) else {},
                        "the host's attempt evidence", required=("host",),
                        optional=tuple(attempt_ids))
    for attempt_id in attempt_ids:
        if attempt_id not in held:
            raise _refusing(
                f"the host returned no evidence about attempt "
                f"{name_value(attempt_id)}; an execution nobody can account "
                f"for is unknown, and unknown is not permission to verify the "
                f"same candidate against the same resources", reserved)
        found = held[attempt_id]
        if found is None:
            evidence[attempt_id] = {
                "runtime": None, "cleanup": None, "resource": None,
                "basis": f"no attempt was ever recorded on this instance's "
                         f"own host, {held['host']}"}
            continue
        runtime = (found.get("runtime") or {}).get("execution_runtime")
        cleanup = (found.get("runtime") or {}).get("cleanup")
        token = found.get("token")
        if runtime not in fresh_attempt.CEASED_RUNTIME:
            raise _refusing(
                f"attempt {name_value(attempt_id)}'s runtime is "
                f"{name_value(runtime)} and cessation is "
                f"{', '.join(fresh_attempt.CEASED_RUNTIME)}; stop it and let "
                f"the host record the outcome before a successor is admitted",
                reserved)
        if cleanup not in fresh_attempt.SETTLED_CLEANUP:
            raise _refusing(
                f"attempt {name_value(attempt_id)}'s cleanup is "
                f"{name_value(cleanup)} and this host still owes it; a "
                f"successor admitted now would compete with an accounting "
                f"that has not finished", reserved)
        if token is None:
            launched = (found.get("runtime") or {}).get("runtime_id")
            if runtime != "not-started" or launched is not None:
                raise _refusing(
                    f"attempt {name_value(attempt_id)} has no workspace token "
                    f"in this host's record and its runtime is "
                    f"{name_value(runtime)}"
                    + (f" on {name_value(launched)}" if launched else "")
                    + "; an absent token is uncertainty about a resource "
                      "rather than evidence it was returned, and uncertainty "
                      "is not permission to start another execution against "
                      "it", reserved)
            resource = "never acquired: this attempt was never launched"
        elif not token.get("returned"):
            raise _refusing(
                f"attempt {name_value(attempt_id)} still holds its workspace "
                f"resource: the token is outstanding. A returned resource is "
                f"what makes the workspace free for another execution",
                reserved)
        else:
            resource = "returned"
        evidence[attempt_id] = {
            "runtime": runtime, "cleanup": cleanup, "resource": resource,
            "basis": f"the host's own record, read {when} the reservation"}
    return evidence


def _authorized(authorization, work_id, *, reserved):
    """The Work this successor runs under, REUSED and never created.

    AND THAT IS NOT A CONVENIENCE. `stage_execution._disagreements` compares a
    worker's manifest Work against the Job's binding, so a fresh Work would
    need workers carrying it -- new configuration for every recovery, which
    REC-7 is explicit is not required. The failed Job's Work is already
    authorized, already bound and already served by the configured reviewer;
    the execution that held it is over. A successor that MINTED a Work would
    also be performing an Authority effect for an owner decision about a Work
    that already exists.
    """
    found = authorization.work_of(work_id)
    if found is None:
        raise _refusing(
            f"this deployment's Authority holds no Work "
            f"{name_value(work_id)}; a retained-recovery successor runs under "
            f"the authorization the failed execution held and never under one "
            f"it mints for itself", reserved)
    status = found.get("status")
    if status != "open":
        raise _refusing(
            f"Work {name_value(work_id)} is {name_value(status)} and a "
            f"successor runs under an open authorization; reopening somebody "
            f"else's Work is not this operation's to do", reserved)
    return {"work_id": work_id, "disposition": "reused", "status": status}


def _bound(binding, store, *, job_id, prior_job_id, work_id, document,
           reserved):
    """The deployment binds the successor, and a worker can serve every stage.

    THE SERVABILITY QUESTION IS ASKED WITH THE SUBMITTED OPERANDS, which is
    `fresh_attempt`'s review R3: an adapter handed only a Job id and a stage
    kind built the digests it compared out of the worker it was comparing them
    against. What travels is this successor's own composed input digest,
    policy digest and the review stage's own profile, so the selector compares
    the real specification.
    """
    from . import creation

    entry = document["jobs"][0]
    job = {"input_digest": entry["input_digest"],
           "policy_digest": entry["policy_digest"]}
    held = binding.binding_of(job_id)
    if held is None:
        held = binding.bind(job_id, like=prior_job_id, work_id=work_id)
        disposition = "added"
    else:
        disposition = "already configured"
    if held is None:
        raise _refusing(
            f"the deployment reports no binding for Job {name_value(job_id)} "
            f"after being asked to add one; nothing further was attempted",
            reserved)
    if held.get("job_work_id") not in (None, work_id):
        raise _refusing(
            f"the deployment binds Job {name_value(job_id)} to Work "
            f"{name_value(held.get('job_work_id'))} and this successor runs "
            f"under {name_value(work_id)}; a Job's Work is a fact about the "
            f"Job and this operation will not quietly move it", reserved)
    serving = {}
    for stage in entry["stages"]:
        workers = binding.serving(job_id, stage=dict(stage), job=dict(job),
                                  task=creation.job_task_of(store,
                                                            prior_job_id))
        if not workers:
            raise _refusing(
                f"no configured worker can serve Job {name_value(job_id)}'s "
                f"{name_value(stage['kind'])} stage under its own submitted "
                f"input, policy and profile; a successor that cannot be "
                f"selected is a Job that would sit queued forever", reserved)
        serving[stage["kind"]] = sorted(workers)
    return {"job_id": job_id, "disposition": disposition,
            "job_work_id": work_id, "serving": serving}


def _reserved(store, operands, decision, *, candidate, bounds, document):
    """CUT A: the successor identity is spoken for, durably, inside the lock.

    THE OPERATION IDENTITY IS WHAT MAKES TWO CONCURRENT REQUESTS ONE
    ADMISSION, and the recorded operands are what make a THIRD request
    carrying different ones a collision rather than a quiet resumption of
    somebody else's. The per-failure fence is decided here too, so a second
    owner decision racing this one cannot reserve a second successor of one
    failure.
    """
    job_id = operands["job_id"]
    record = {**operands, "state": "intended",
              # WHICH EXPIRED SUCCESSOR THIS ONE FOLLOWS, carried on the
              # reservation rather than only on the decision. `prior_job_id`
              # is the FAILED Job -- every successor of one failure shares it
              # -- so the per-failure fence could not tell a review-only
              # successor of one expired execution from a review-only
              # successor of another without this.
              "lineage": (None if decision["lineage"] is None
                          else dict(decision["lineage"])),
              "verification_attempt_id":
                  verification_attempt_id(operands["decision_id"]),
              "review_stage_id": review_stage_id(operands["decision_id"]),
              "candidate": dict(candidate),
              "correction": dict(decision["correction"]),
              "bounds": bounds}
    operands_for_signature = {name: record[name] for name in INTENT_MEMBERS
                              if name not in ("state", "bounds")}
    # THE EXACT DOCUMENT THIS RESERVATION IS FOR, in the submission store's
    # own spelling, so the journal check below compares INTENTS rather than
    # names.
    intended = job_signature("submission.record", document)

    def act(connection):
        _refuse_cancelled(connection, operands["prior_job_id"],
                          "a retained-recovery successor")
        job_control.refuse_uncertain(connection, operands["prior_job_id"],
                                     "a retained-recovery successor of it",
                                     now=store._now())
        _fenced_decision(connection, store, operands["failure_key"],
                         operands["decision_id"],
                         stages=tuple(operands["stages"]),
                         lineage=decision["lineage"])
        # AN IDENTITY ANOTHER OWNER HAS RESERVED IS NOT FREE, and finding that
        # out at `submit` would be finding it out with a Work authorization
        # and a deployment binding already published for it. The three tables
        # asked are the three that reserve a Job identity in this store:
        # ordinary submissions, fresh attempts and template creations.
        taken = connection.execute(
            "SELECT job_id FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        if taken is not None:
            raise ContractRefusal(
                "refused", "precondition",
                f"Job {name_value(job_id)} is already recorded in this store "
                f"by another submission; a retained-recovery successor cannot "
                f"take an identity that names another pipeline", durable=True)
        for table, what in (("fresh_attempts", "a fresh attempt"),
                            ("template_jobs", "a template creation")):
            other = connection.execute(
                f"SELECT job_id FROM {table} WHERE job_id = ? OR "
                f"submission_id = ?",
                (job_id, operands["submission_id"])).fetchone()
            if other is not None:
                raise ContractRefusal(
                    "refused", "precondition",
                    f"{name_value(other[0])} is RESERVED by {what}; that "
                    f"operation owns the identity, so a successor taking the "
                    f"name would strand whatever it has already published")
        journalled = connection.execute(
            "SELECT signature, state FROM operations WHERE operation_id = ?",
            (submission.operation_id(operands["submission_id"]),)).fetchone()
        if journalled is not None and journalled[0] != intended:
            raise ContractRefusal(
                "refused", "precondition",
                f"the submission operation "
                f"{name_value(submission.operation_id(operands['submission_id']))} "
                f"is already settled in this store's journal as "
                f"{name_value(journalled[1])} for a DIFFERENT document, so "
                f"that identity can never record this one. An operation's "
                f"outcome is immutable and repeating this request will not "
                f"change it: this recovery needs a new owner decision "
                f"identity. Nothing was reserved and no Work or binding was "
                f"touched")
        return record

    return store.transact(intent_operation_id(operands["decision_id"]),
                          SUCCESSOR_INTENT_KIND,
                          job_signature(SUCCESSOR_INTENT_KIND,
                                        operands_for_signature), act)


def successor_readiness(record):
    """WHICH ACT IS OWED NEXT, said out loud rather than implied.

    THE ADMISSION BOUNDARY'S OWN TRUTHFULNESS REQUIREMENT. This slice admits a
    successor and executes nothing: the approved corrected verifier has not
    run, no workspace has been materialized and no candidate has been handed
    to review. An answer that merely reported a Job id would read as though
    the recovery had happened, which is exactly the false-success this
    contract exists to prevent. W385625 owns the acts named here.
    """
    stages = tuple(record["stages"])
    if stages == REVIEW_ONLY_STAGES:
        return {"verification": "omitted",
                "review": "blocked",
                "owed_by": "the verifier execution and review handoff slice",
            "execution": "blocked: retained candidate handoff unavailable",
                "detail": "the approved profile's verification stage is "
                          "omitted under this decision; the passed "
                          "verification named in the lineage stands and is "
                          "not repeated"}
    return {"verification": "owed", "review": "blocked",
            "owed_by": "the verifier execution and review handoff slice",
            "execution": "blocked: retained candidate handoff unavailable",
            "detail": "this admission reserved the isolated verification's "
                      "identity and executed nothing; the retained candidate "
                      "is unchanged and the review stage consumes the same "
                      "candidate only after passed verification AND the "
                      "supported execution handoff; this build keeps it blocked"}


def _completed(store, operands, *, decision, candidate, bounds, evidence,
               fence, authorized, bound, recorded):
    """CUT C: the intent becomes an admission, and the answer is journalled.

    THE RESULT IS RECORDED RATHER THAN RECOMPOSED, so a caller repeating the
    command is told the same thing the first one was told -- including which
    evidence the admission rested on and which act is still owed.
    """
    job_id = operands["job_id"]
    answer = documents.recovery_successor(
        failure_key=operands["failure_key"],
        decision_id=operands["decision_id"], job_id=job_id,
        prior_job_id=operands["prior_job_id"],
        work_id=operands["work_id"],
        submission_id=operands["submission_id"],
        stages=list(operands["stages"]), work=authorized, binding=bound,
        candidate=dict(candidate), correction=dict(decision["correction"]),
        bounds=bounds,
        control=job_control.control_of(store, job_id),
        exclusion=evidence,
        fence=(None if fence is None else {
            "trigger": fence.get("trigger", "operator"),
            "requested_at": fence["requested_at"],
            "operation_id": fence["operation_id"]}),
        readiness=successor_readiness({"stages": operands["stages"]}),
        stage_ids=list(recorded["stages"]),
        verification_attempt_id=verification_attempt_id(
            operands["decision_id"]),
        recorded_at=recorded["recorded_at"])

    def act(connection):
        row = connection.execute(
            "SELECT result FROM operations WHERE operation_id = ? AND "
            "kind = ? AND state = 'committed'",
            (intent_operation_id(operands["decision_id"]),
             SUCCESSOR_INTENT_KIND)).fetchone()
        if row is None:                                   # pragma: no cover
            raise ContractRefusal(
                "integrity", "schema",
                f"the reservation for {name_value(job_id)} is gone between "
                f"this operation's own two cuts")
        return answer

    return store.transact(admit_operation_id(operands["decision_id"]),
                          SUCCESSOR_KIND,
                          job_signature(SUCCESSOR_KIND, operands), act)


def execution_gate(store, job_id):
    """Keep recovery blocked until Stage1-C supplies a validated handoff.

    A passed account alone cannot open review. The exact reservation remains
    visible across restart, including review-only recovery. Stage1-C must
    replace this hold with validated custody and execution binding; this
    slice exposes no switch that bypasses the missing execution contract.
    """
    control = job_control.control_of(store, job_id)
    if control is None or control["profile"] != SUCCESSOR_PROFILE:
        return None
    intents = [one for one in _records_of(store, SUCCESSOR_INTENT_KIND, INTENT_MEMBERS) if one["job_id"] == job_id]
    held = intents[0] if len(intents) == 1 else None
    return documents.recovery_gate(
        job_id=job_id, open=False, reason="retained-candidate-execution-handoff-unavailable",
        decision_id=None if held is None else held["decision_id"],
        candidate=None if held is None else held["candidate"],
        lineage=None if held is None else held["lineage"])
