"""THE OWNER'S INSPECTION AND DECISION ON A RETAINED OUTPUT PUBLICATION
FAILURE, AND THE CLOSED ADMISSION BOUNDARY THAT DECISION REACHES.

W385695 internal checkpoint 1, under DESIGN REC-9 and the owner-selected
contract `work/records/2026/11/finding-v12-output-publication-recovery/
CONTRACT-PROPOSED-385720.md` (SHA-256 `8bd467f6668b38063dbdff53403cd2eb24cc
acc4e3cedf4753a3d922b34cd152`), selected by that dossier's FINDING.md
"Consolidated owner selection — 2026-11-22". The owning record is
`work/records/2026/11/finding-v12-output-publication-recovery/`.

WHAT THIS IS ABOUT, and it is a DIFFERENT ending from REC-8's. Stage 1's
retained recovery is about a producer whose required VERIFICATION failed: the
provider turn succeeded, the output was published, frozen and retained, and
what went wrong was a command's exit status. This is about a producer that
SUCCEEDED -- provider exit 0, its own required verifier exit 0 -- and then
failed at PUBLICATION, so nothing was frozen, nothing entered custody, and
every reader that resolves retained evidence through a frozen manifest
truthfully answers that there is nothing there. The bytes are still on the
host, in the attempt's own writable root, and REC-9 is the capability that
lets an owner look at them and decide.

THE THREE ACTS THIS CHECKPOINT OWNS, and the fourth it refuses to pretend to:

  1. `inspect` -- READ-ONLY. It resolves the failed Job/stage/episode to the
     attempt the host owns, proves there is no published result, reads the
     ORIGINAL host-held output through its owner under positive writer
     cessation and exclusion, measures it, qualifies the producer's own
     adapter-attributed verification against the read-only admitted task, and
     asks the SOURCE-AWARE owner whether the candidate, its base and its path
     set correspond to the bytes that are there. It reserves nothing, writes
     nothing and manufactures no trusted state from a copy.
  2. `decide` -- ONE attributable owner approval, hold or denial, authorized
     through the Authority in the Work's own scope, binding the EXACT
     selection digest, the exact failed execution and command, the exact
     candidate, the exact measured output bytes, the exact producer
     verification context, the selected stages and the approved profile and
     its digest.
  3. `admit_publication` -- THE ADMISSION. W385695 checkpoint 2 installed the
     four capabilities checkpoint 1 could only name as owed -- the `/4`
     submission vocabulary, the `baton.v12.worker-pool/2` publication lane,
     the schema-10 store and the enforced `output-publication-review/1`
     control profile -- so this is now a real admission: the prior assignment
     is ENDED through the Authority's own exact-expect transition, the
     recovery identity is RESERVED, the Work is REUSED, the deployment binds
     the Job, and ONE `/4` submission carrying one publication stage and one
     review stage gated on it is recorded. Every prerequisite is still read
     from the owners that hold it, and a MISSING one still produces the
     checkpoint-1 held record and no effect at all -- which is what an older
     deployment, or a store this build has not migrated, answers with.
  4. WHAT IT STILL WILL NOT DO. It will not publish anything itself: the
     deterministic adoption of the retained bytes, its read-only staging, its
     absolute deadline and its custody are `publication_execution`'s. It will
     not open the review gate: REC-9's "Review MUST remain non-runnable until
     attributable publication custody and the exact candidate handoff are
     validated" is kept by `publication_execution.execution_gate`, which is
     shut until that module's own handoff record commits -- an approval, a
     qualified producer result, a candidate digest or a submitted graph edge
     cannot open it. And it will not run or redispatch an implementation or
     repeat the producer's verifier under any path.

WHAT IT REFUSES, every one of them a ruling rather than a preference:

  * THE ORIGINAL IS THE TRUST ROOT. The output is resolved FROM THE ATTEMPT
    through the host owner, under a completed preparation, proved object
    identity and settled writers. A dossier copy, an agent-authored manifest
    or an operator-supplied path is not a trust root and cannot become one by
    being approved: `workspaces.retained_output_of` is the only door, and a
    missing, replaced or unreadable original HOLDS.
  * PRODUCER EVIDENCE IS NEVER ACCEPTANCE. The adapter's `result.json` is
    qualified -- its argv against the read-only admitted task, its exit status
    0, its candidate and base against the claim, its task identity and digest
    -- and the qualification is recorded as PRODUCER EVIDENCE. Reuse means the
    recovery pipeline does not repeat that producer verifier; it does not mean
    anything was accepted. The substantive reviewer still owes its own tests.
  * NO IMPLEMENTATION AND NO VERIFICATION STAGE. `owned_stages` refuses
    `implementation`, `verification` and `integration` by name, and the only
    admissible set is `("publication", "review")` in that order.
  * NEVER MAP PUBLICATION TO IMPLEMENTATION. `scheduler.lane_of` is now a
    TABLE whose publication entry is the publication lane and which refuses a
    kind it has no entry for; the fallthrough that used to answer
    `implementation` for every non-review stage is gone. A deployment whose
    installed pool reserves no publication capacity is still a MISSING
    PREREQUISITE and is never worked around by routing the stage elsewhere.
  * NO ORDINARY MISUSE, AND THE GUARD IS NAMED ACCURATELY. The guard is
    `job_control.require_ordinary_profile`, it belongs to the CONTROL owner
    rather than to this module, and what it refuses is exactly one thing: a
    Job admitted under a RECOVERY CONTROL PROFILE by an ordinary creation,
    submission or fresh attempt. Checkpoint 1's text claimed this module owned
    a guard over the profile, template, role descriptor AND stage set, which
    was wrong in both halves -- the function is `job_control`'s, and at the
    time it named only REC-8's profile, so it would not have refused this
    recovery's own. It now reads `job_control.RECOVERY_PROFILES`, which holds
    both. The other three identities are kept out of ordinary use by the
    owners that hold them and each is asserted separately: the `/4` generation
    is the only one `documents` lets a publication stage into, the template is
    not a bound role contract, and `owned_stages` is the only admissible set.
  * NO CLOCK IS RESET. The original Job, its admission, its terminal, its
    fences and its deadlines are read and never written.
"""

import json

from ..contracts import ContractRefusal, digest, digest_of_bytes
from ..contracts.errors import name_value, sample_of
from ..worker_manager import boundaries, frozen_output_of
from . import (cancellation, creation, documents, episodes, failure_analysis,
               fresh_attempt, job_control, role_contract, schema, scheduler,
               submission)
from .store import job_signature

__all__ = ["RECOVERY_SELECTION", "RECOVERY_DECISION", "RECOVERY_TEMPLATE",
           "RECOVERY_ROLE", "RECOVERY_SUBMISSION", "RECOVERY_POOL",
           "RECOVERY_STORE_GENERATION", "PUBLICATION_LANE",
           "PUBLICATION_PROFILE", "PUBLICATION_DEFINITION",
           "PUBLICATION_DEFINITION_BYTES", "PUBLICATION_PROFILE_DIGEST",
           "PUBLICATION_PROFILES", "CLOCK_ORIGINS", "PROVENANCE",
           "PROVENANCE_OUTPUT", "PROVENANCE_PATH", "PROVENANCE_TYPE",
           "PROPOSAL_BYTES", "ORIGINAL_PROPOSAL_BYTES",
           "resolved_profile", "admitted_bounds",
           "corrective_declaration",
           "PUBLICATION_STAGE", "REVIEW_STAGE", "FORBIDDEN_STAGES",
           "SELECTED_STAGES", "SELECTED_STAGE_SETS", "owned_stages",
           "OWNER_CAPABILITY", "OWNER_AUTHORIZATION", "OWNER_DECISION",
           "DISPOSITIONS", "APPROVED", "DENIED", "HELD",
           "HOST_OUTPUT", "SOURCE_CORRESPONDENCE", "ADMISSION_OWNERS",
           "SOURCE_REFUSALS",
           "READ_SCHEMA", "SELECTION_MEMBERS", "selection_digest",
           "PRODUCER_RESULT", "PRODUCER_VERIFICATION", "producer_entries",
           "COMPLETION_ENVELOPE",
           "inspect", "expected_facts",
           "EXPECTED_MEMBERS", "DECISION_KIND", "DECISION_MEMBERS",
           "decision_operation_id", "decision_of", "decisions_of",
           "decisions_for", "decide",
           "HELD_KIND", "HELD_MEMBERS", "held_operation_id",
           "held_admission_of", "held_admissions_of",
           "INTENT_KIND", "INTENT_MEMBERS", "intent_operation_id",
           "intent_of", "intents_of",
           "ENDING_KIND", "ENDING_MEMBERS", "ENDING_CAUSES",
           "ENDING_DISPOSITION", "ENDING_OUTCOMES", "ending_operation_id",
           "ending_of",
           "ADMITTED_KIND", "ADMITTED_MEMBERS", "admit_operation_id",
           "admission_of", "admissions_of", "admission_for", "prior_job_in",
           "PUBLICATION_BINDING", "PRIOR_ASSIGNMENT", "WORKER_MEMBERS",
           "RECOVERY_INPUT_SCHEMA", "RECOVERY_INPUT_MEMBERS",
           "recovery_input", "recovery_input_digest",
           "end_prior_assignment", "advance_endings",
           "PREREQUISITES", "prerequisites", "admit_publication",
           "recovery_job_id", "recovery_submission_id",
           "review_stage_id", "publication_stage_id",
           "GATE_UNAVAILABLE", "GATE_REASONS", "execution_gate",
           "admission_readiness"]


def _refuse(message, *, category="refused", code="precondition"):
    raise ContractRefusal(category, code, message)


def _denied(message):
    raise ContractRefusal("policy", "denied", message)


# -- 1. the owner-selected identities ----------------------------------------
#
# HELD AS NAMED CONSTANTS AND NOT SPELLED TWICE. Every string below is one the
# owner selected by name in the consolidated FINDING entry, and each is the
# single spelling this build compares against -- `failure_analysis`'s rule for
# its declaration schema, for its reason: two spellings of one approved
# identity are two chances for a selection to drift away from its approval.
RECOVERY_SELECTION = "baton.v12.output-publication-recovery/1"
RECOVERY_DECISION = "baton.v12.output-publication-decision/1"
RECOVERY_TEMPLATE = "baton.v12.job-template.output-publication-review/1"
RECOVERY_ROLE = "baton.v12.development-role-contract.output-publication-review/1"
RECOVERY_SUBMISSION = "baton.v12.job-submission/4"
RECOVERY_POOL = "baton.v12.worker-pool/2"
RECOVERY_STORE_GENERATION = 10
PUBLICATION_LANE = "publication"

# W385694'S EXACT DECLARATION, READ FROM ITS OWNER rather than restated. The
# owner's joint selection names `native-handoff.proposal100m/1` and
# `implementation-review/4` with a proposal-only 104857600-byte ceiling, and
# the contract is explicit that W385695 CONSUMES that declaration rather than
# owning it. A number written here would be the second account of one owner
# selection, and the first one to drift would be the one a recovery published
# under.
PROPOSAL_BYTES = role_contract.MAX_PROPOSAL_BYTES
ORIGINAL_PROPOSAL_BYTES = role_contract.MAX_OUTPUT_BYTES


def corrective_declaration():
    """The output declaration a recovery publication would publish under.

    THE SELECTED REVISION'S OWN, composed by the descriptor owner and detached
    on every call. Not a document this module assembles: the entries, the
    media types, the 100-entry ceiling and the forbidden-link policy are
    `role_contract`'s, and a copy here would be a declaration nobody approved
    wearing the name of one they did.
    """
    held = role_contract.contract_for(role_contract.PROPOSAL100M_TEMPLATE)
    named = [one for one in held["outputs"]
             if one["name"] == role_contract.CANDIDATE_OUTPUT]
    if len(named) != 1:                                   # pragma: no cover
        _refuse(f"the selected proposal revision declares {len(named)} "
                f"{name_value(role_contract.CANDIDATE_OUTPUT)} outputs",
                category="integrity", code="schema")
    return {"descriptor": held["schema"], "template": held["template"],
            "digest": role_contract.contract_digest(held),
            "output": dict(named[0])}


# -- 2. the owner-approved finite profile ------------------------------------
#
# HELD AS DATA AND PROVING ITS OWN DIGEST, exactly as `retained_recovery`
# holds `stage1-verification-review/1`. The DIFFERENCE from that one is worth
# naming: the owner published that profile as a definition RECORD whose bytes
# a case compares against, and selected THIS one as exact NUMBERS in the
# consolidated FINDING entry. So what is pinned at import is the numbers --
# each against a separately named constant carrying the selection it came from
# -- and the digest is this build's own canonical identity for them, which the
# decision binds and the admission compares.
PUBLICATION_PROFILE = "output-publication-review/1"

# THE SELECTED NUMBERS, one constant per owner sentence, so a changed value is
# a changed NAME in a diff rather than a digit inside a document.
SELECTED_JOB_SECONDS = 9960            # "Job 9960 seconds including queue"
SELECTED_STAGE_SECONDS = 4800          # "stage 4800"
SELECTED_PUBLICATION_SECONDS = 900     # "publication absolute sub-bound 900
#                                         from durable stage start"
SELECTED_REVIEW_INVOCATION_SECONDS = 3600   # "reviewer invocation 3600
#                                              including investigation/tests"
SELECTED_REVIEW_COMMAND_SECONDS = 900  # "each reviewer command 900"
SELECTED_ALLOWANCE = 0                 # "zero corrections, retries and
#                                         continuations"
SELECTED_PROVENANCE_BYTES = 16384      # "a separate output limited to 16384
#                                         bytes, one regular file, no links"
SELECTED_PROVENANCE_ENTRIES = 1

PUBLICATION_DEFINITION = {
    "automatic_continuations": SELECTED_ALLOWANCE,
    "automatic_corrections": SELECTED_ALLOWANCE,
    "automatic_retries": SELECTED_ALLOWANCE,
    "each_stage": {
        "origin": "stage_admission",
        "seconds": SELECTED_STAGE_SECONDS,
    },
    "identity": PUBLICATION_PROFILE,
    "overall_job": {
        "includes_queue": True,
        "origin": "accepted_admission",
        "seconds": SELECTED_JOB_SECONDS,
    },
    "publication_stage": {
        # AN ABSOLUTE SUB-BOUND AND NOT A WORKER-LOCAL TIMER, which the
        # contract states twice and in both directions: it runs from the
        # PERSISTED publication-stage execution admission, it is not restarted
        # by a worker restart, and the host enforces cessation when the worker
        # is lost. A number alone cannot say that, so the origin says it.
        "origin": "stage_admission",
        "restart_resets": False,
        "seconds": SELECTED_PUBLICATION_SECONDS,
    },
    "publication_authority": (
        "W385695; work/records/2026/11/finding-v12-output-publication-"
        "recovery/FINDING.md: Consolidated owner selection — 2026-11-22"),
    "review_provider_invocation": {
        "includes_investigation_and_tests": True,
        "origin": "invocation_start",
        "seconds": SELECTED_REVIEW_INVOCATION_SECONDS,
    },
    "verification_command": {
        # THE REVIEWER'S OWN COMMANDS, and the member says so. The owner's
        # 900 s is "each reviewer command"; it is not a prohibition on the
        # reviewer running tests, and the contract's G3 answer is explicit
        # that only the PRODUCER's verifier is not repeated.
        "applies_to": "each_reviewer_command",
        "origin": "command_start",
        "seconds": SELECTED_REVIEW_COMMAND_SECONDS,
    },
}

PUBLICATION_DEFINITION_BYTES = (
    json.dumps(PUBLICATION_DEFINITION, indent=2, sort_keys=True,
               ensure_ascii=False) + "\n").encode("utf-8")
PUBLICATION_PROFILE_DIGEST = digest_of_bytes(PUBLICATION_DEFINITION_BYTES)
PUBLICATION_PROFILES = {PUBLICATION_PROFILE: PUBLICATION_DEFINITION}

# THE RECOVERY PROVENANCE OUTPUT, as its own bounded descriptor. It is
# SEPARATE from the proposal on purpose, which is the contract's own sentence:
# "it never alters the original proposal tree digest". Publishing the
# provenance inside the adopted tree would change the bytes this whole
# capability exists to preserve.
PROVENANCE = {"name": "recovery-provenance",
              "max_bytes": SELECTED_PROVENANCE_BYTES,
              "max_entries": SELECTED_PROVENANCE_ENTRIES,
              "regular_files_only": True,
              "link_policy": role_contract.LINK_POLICY}
# AND THE DECLARED OUTPUT THE WORKER CONTRACT ADMITS, derived from exactly
# those four facts rather than restating them.
#
# TWO DOCUMENTS FOR ONE SELECTION, and the reason is a boundary rather than a
# preference. `PROVENANCE` above is what the OWNER DECISION binds -- it is a
# member of every committed decision record, so its bytes are immutable
# history and widening it would change the signature of decisions already
# taken. `sealing.declared_outputs` admits exactly `name`, `type`, `path`,
# `required` and `constraints` and refuses an unknown member, which is the
# right rule for an assignment's declaration and the wrong shape for a
# decision's. So this composes the second from the first, and the numbers
# have one source.
#
# `record-output` AND NOT `git-change-proposal`: this is one document about a
# recovery, not a change proposal, and the type travels into the frozen result
# where a consumer reads it. The PATH is its own, disjoint from the proposal's,
# which is what `declared_outputs` proves and what keeps the adopted proposal
# tree digest unchanged.
PROVENANCE_PATH = "recovery-provenance"
PROVENANCE_TYPE = "record-output"
PROVENANCE_OUTPUT = {
    "name": PROVENANCE["name"], "type": PROVENANCE_TYPE,
    "path": PROVENANCE_PATH, "required": True,
    "constraints": {"max_bytes": PROVENANCE["max_bytes"],
                    "max_entries": PROVENANCE["max_entries"],
                    "allowed_media_types": [role_contract.OCTET_STREAM,
                                            role_contract.PLAIN_TEXT],
                    "link_policy": PROVENANCE["link_policy"],
                    "validator_digest": None}}
from ..worker_manager.schema import OUTPUT_TYPES as _OUTPUT_TYPES  # noqa: E402
if PROVENANCE_TYPE not in _OUTPUT_TYPES:                  # pragma: no cover
    raise AssertionError(
        f"the recovery provenance declares output type {PROVENANCE_TYPE!r}, "
        f"which the worker contract does not carry")
if PROVENANCE_PATH == role_contract.CANDIDATE_OUTPUT \
        or PROVENANCE["name"] == role_contract.CANDIDATE_OUTPUT:
    raise AssertionError(                                 # pragma: no cover
        "the recovery provenance shares the proposal's name or path; a "
        "SEPARATE output is what keeps the adopted proposal tree digest "
        "unchanged, and two declarations at one path are one tree")

CLOCK_ORIGINS = ("accepted_admission", "stage_admission", "command_start",
                 "invocation_start")
if any(PUBLICATION_DEFINITION[one]["origin"] not in CLOCK_ORIGINS
       for one in ("overall_job", "each_stage", "publication_stage",
                   "verification_command",
                   "review_provider_invocation")):   # pragma: no cover
    raise AssertionError(
        "the held publication definition names a clock origin this build "
        "does not own")
if PUBLICATION_DEFINITION["publication_stage"]["seconds"] \
        > PUBLICATION_DEFINITION["each_stage"]["seconds"] \
        or PUBLICATION_DEFINITION["each_stage"]["seconds"] \
        > PUBLICATION_DEFINITION["overall_job"]["seconds"]:  # pragma: no cover
    raise AssertionError(
        "the held publication definition states a sub-bound wider than the "
        "stage or a stage wider than the Job it is inside")
# A RAISE AND NOT AN `assert`, for `failure_analysis`'s reason: a build run
# under `-O` strips assertions, and a self-check that disappears under an
# optimisation flag is best-effort dressed as a guarantee.
#
# CHECKPOINT 1 ASSERTED THE OPPOSITE OF THIS, and deliberately: it required
# `job_control.PROFILES` to carry NO entry under this name, because it
# admitted no Job and "an entry nothing admits would be an enforced policy
# with no execution". Checkpoint 2 admits the Job, so the entry must exist AND
# must state the same numbers the owner selected -- which is a stronger
# property than its absence was, and is the one a reader needs: the policy a
# recovery Job is enforced under is the policy its decision bound.
if PUBLICATION_PROFILE not in job_control.PROFILES:       # pragma: no cover
    raise AssertionError(
        f"this build admits publication recovery Jobs and its control owner "
        f"holds no {PUBLICATION_PROFILE} profile; an admitted Job whose "
        f"finite control nothing enforces is a recovery with no deadline")
if PUBLICATION_PROFILE != job_control.PUBLICATION_RECOVERY_PROFILE \
        or PUBLICATION_PROFILE not in job_control.RECOVERY_PROFILES:
    raise AssertionError(                                 # pragma: no cover
        f"{PUBLICATION_PROFILE} is not the control owner's own recovery "
        f"profile identity, so an ordinary submission naming it would not be "
        f"refused by require_ordinary_profile")
_enforced = job_control.PROFILES[PUBLICATION_PROFILE]
if (_enforced["job_seconds"], _enforced["stage_seconds"],
        _enforced["provider_turn_seconds"],
        _enforced["verification_command_seconds"],
        _enforced["correction_rounds"],
        job_control.CONTINUATIONS[PUBLICATION_PROFILE],
        job_control.sub_bound_of(PUBLICATION_PROFILE,
                                 job_control.PUBLICATION_STAGE_KIND)) != (
        SELECTED_JOB_SECONDS, SELECTED_STAGE_SECONDS,
        SELECTED_REVIEW_INVOCATION_SECONDS, SELECTED_REVIEW_COMMAND_SECONDS,
        SELECTED_ALLOWANCE, SELECTED_ALLOWANCE,
        SELECTED_PUBLICATION_SECONDS):                    # pragma: no cover
    raise AssertionError(
        f"the enforced {PUBLICATION_PROFILE} control profile and the owner "
        f"numbers this module holds disagree; a recovery would be admitted "
        f"under one account of its limits and enforced under another")
del _enforced


def resolved_profile(profile=PUBLICATION_PROFILE):
    """The approved bounds of the publication profile, with their units.

    A profile this build does not hold is a STALE SELECTION and is refused
    rather than guessed -- `job_control.owned_control`'s rule, for its reason:
    an execution admitted under a policy nobody selected is one nothing can
    enforce.

    AND THE ENFORCEMENT IS REPORTED RATHER THAN IMPLIED. `enforced_by` says
    which control profile would carry these numbers into a serving manager,
    and today the answer is `None`: `job_control.PROFILES` has no entry,
    because checkpoint 1 admits no Job and an unenforceable entry would be the
    second account of a policy the first one could not apply. A reader is told
    that rather than left to infer it from a Job that never appears.
    """
    boundaries.text(profile, "a publication recovery profile identity")
    if profile not in PUBLICATION_PROFILES:
        _refuse(f"a publication-recovery profile is one of "
                f"{', '.join(sorted(PUBLICATION_PROFILES))}; this is "
                f"{name_value(profile)}. A profile this build does not hold "
                f"is a finite control it cannot enforce",
                category="integrity", code="schema")
    held = PUBLICATION_PROFILES[profile]
    return {
        "profile": profile, "units": "seconds", "scope": "per-admission",
        "digest": digest_of_bytes(
            (json.dumps(held, indent=2, sort_keys=True, ensure_ascii=False)
             + "\n").encode("utf-8")),
        "enforced_by": job_control.PROFILES.get(profile) and profile,
        "automatic_retries": held["automatic_retries"],
        "automatic_corrections": held["automatic_corrections"],
        "automatic_continuations": held["automatic_continuations"],
        "overall_job_seconds": held["overall_job"]["seconds"],
        "overall_job_includes_queue": held["overall_job"]["includes_queue"],
        "overall_job_origin": held["overall_job"]["origin"],
        "each_stage_seconds": held["each_stage"]["seconds"],
        "each_stage_origin": held["each_stage"]["origin"],
        "publication_stage_seconds": held["publication_stage"]["seconds"],
        "publication_stage_origin": held["publication_stage"]["origin"],
        "publication_stage_restart_resets":
            held["publication_stage"]["restart_resets"],
        "verification_command_seconds":
            held["verification_command"]["seconds"],
        "verification_command_origin": held["verification_command"]["origin"],
        "verification_command_applies_to":
            held["verification_command"]["applies_to"],
        "review_provider_invocation_seconds":
            held["review_provider_invocation"]["seconds"],
        "review_provider_invocation_origin":
            held["review_provider_invocation"]["origin"],
        "review_provider_invocation_covers_tests":
            held["review_provider_invocation"][
                "includes_investigation_and_tests"]}


def admitted_bounds(policy, *, admitted_at, stages):
    """WHICH APPROVED BOUNDS THIS ADMISSION SELECTED, and from when.

    DELIBERATELY NOT A SECOND SET OF DEADLINES, for `retained_recovery.
    admitted_bounds`' reason: LIM-5 derives and persists an admitted Job's
    enforced deadline from the durable submission instant, and a deadline
    computed here would be the second account of one instant -- the one that
    drifts when a restart re-derives the other. What this records is the
    SELECTION. In this checkpoint it is additionally true that no stage has a
    durable execution admission yet, so every per-stage and per-command
    ceiling below has no origin instant at all; the origins name where those
    clocks WILL start rather than claiming they have.
    """
    boundaries.instant(admitted_at, "a publication admission instant")
    selected = owned_stages(stages)
    return {"profile": policy["profile"], "digest": policy["digest"],
            "units": policy["units"], "admitted_at": admitted_at,
            "stages": list(selected),
            **{name: policy[name] for name in sorted(policy)
               if name not in ("profile", "digest", "units", "scope",
                               "enforced_by")}}


# -- 3. the selected stage set -----------------------------------------------
#
# WHAT A RECOVERY JOB MAY CONSIST OF. Exactly one publication stage followed
# by exactly one review stage, which is the `/4` submission shape the owner
# selected, compared as a SEQUENCE because the order is part of the selection:
# publication is the producer edge the review consumes, and the reverse would
# be a review of something nothing has published.
PUBLICATION_STAGE = "publication"
REVIEW_STAGE = "review"
# AND THE THREE WORDS THAT ARE NEVER IN A SELECTED SET, named so the refusal
# can say them. `implementation` is REC-9's "without redispatching
# implementation"; `verification` is the producer verifier this recovery
# explicitly does not repeat; `integration` is a disposition nobody selected.
FORBIDDEN_STAGES = ("implementation", "verification", "integration")
SELECTED_STAGES = (PUBLICATION_STAGE, REVIEW_STAGE)
SELECTED_STAGE_SETS = (SELECTED_STAGES,)
if REVIEW_STAGE not in documents.STAGE_KINDS:             # pragma: no cover
    raise AssertionError(
        "the Job stage vocabulary no longer names the review stage this "
        "recovery hands its candidate to")


def owned_stages(value):
    """The selected stage set, proved to be the one the owner may select."""
    if type(value) in (list, tuple):
        held = tuple(value)
    else:
        _refuse(f"a selected stage set is a list of stage words; this is "
                f"{name_value(value)}", category="integrity", code="schema")
    named = [one for one in FORBIDDEN_STAGES if one in held]
    if named:
        _denied(f"the selected stage set names {', '.join(named)}; an "
                f"output-publication recovery PUBLISHES an existing output "
                f"and hands it to review, and it never redispatches the work "
                f"that produced it or repeats the producer's own verifier")
    if held not in SELECTED_STAGE_SETS:
        _refuse(f"an output-publication recovery selects "
                f"{json.dumps(list(SELECTED_STAGES))}; this is "
                f"{json.dumps(list(held))}",
                category="integrity", code="schema")
    return held


# -- 4. the owner's authority ------------------------------------------------
#
# THE CAPABILITY THE DEPLOYMENT ALREADY GRANTS, and the port shape is
# `retained_recovery.OWNER_AUTHORIZATION`'s unchanged: the scope comes off the
# WORK's own row, the principal comes off the Authority's endpoint mapping,
# and neither is an operand anywhere on this surface. A new capability word
# would be a deployment configuration change nobody approved.
OWNER_CAPABILITY = "approve"
OWNER_AUTHORIZATION = ("participant", "work_of", "authorize")
OWNER_DECISION = ("endpoint", "principal", "effective_scope", "role", "grant",
                  "policy_generation")

APPROVED = "approved"
DENIED = "denied"
HELD = "held"
DISPOSITIONS = (APPROVED, DENIED, HELD)

# THE TWO PORTS THIS SLICE ADDS to the four a retained-recovery admission
# already composes. `host` is the owner of the ORIGINAL output -- the trust
# root -- and `source` is the Git-aware consumer that validates commit, base
# and path set, because REC-9's own boundary is that "the generic manager does
# not interpret Git or scan the nominated source checkout".
HOST_OUTPUT = ("instance", "output_of")
SOURCE_CORRESPONDENCE = ("instance", "correspondence_of")
ADMISSION_OWNERS = ("exclusion", "authorization", "binding", "ownership",
                    "host")


def _port(port, members, *, what):
    missing = [one for one in members if getattr(port, one, None) is None]
    if port is None or missing:
        _refuse(f"{what} supplies exactly {', '.join(members)}; "
                + ("this one is absent" if port is None else
                   f"this one carries no {', '.join(missing)}"),
                category="refused", code="capability")
    return port


def _owner(authorization, work_id, *, what):
    """Resolve WHO is deciding and in WHICH scope, through the Authority."""
    _port(authorization, OWNER_AUTHORIZATION, what=what)
    participant = boundaries.text(authorization.participant,
                                  f"{what}'s acting participant")
    work = authorization.work_of(work_id)
    if work is None:
        _refuse(f"this deployment's Authority holds no Work "
                f"{name_value(work_id)}; the scope one publication recovery "
                f"decision is authorized in is that Work's own, and there is "
                f"none to read")
    if type(work) is not dict \
            or any(one not in work for one in ("work_id", "scope", "status")):
        _refuse(f"{what}'s Work projection carries no work_id, scope and "
                f"status; the scope one recovery decision is authorized in "
                f"is read off the Work's own row",
                category="integrity", code="schema")
    held = {one: work[one] for one in ("work_id", "scope", "status")}
    boundaries.text(held["scope"], f"Work {work_id}'s effective scope")
    if held["status"] != "open":
        _refuse(f"Work {name_value(work_id)} is {name_value(held['status'])} "
                f"and a publication recovery reuses the ORIGINAL OPEN Work; "
                f"deciding on somebody else's terminal Work is not this "
                f"operation's to do")
    decided = authorization.authorize(participant, capability=OWNER_CAPABILITY,
                                      scope=held["scope"])
    if decided is None:
        _denied(f"{name_value(participant)} holds no "
                f"{name_value(OWNER_CAPABILITY)} capability in "
                f"{name_value(held['scope'])}, which is Work "
                f"{name_value(work_id)}'s own effective scope; a publication "
                f"recovery is authorized by the deployment's decision grant "
                f"and never by reading the inspection, by holding the output "
                f"or by a producer's own green result")
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


# -- 5. the trust root -------------------------------------------------------
#
# WHERE THE ORIGINAL LIVES AND WHAT IS IN IT. The producer this recovery is
# about is the native handoff worker, which writes its proposal tree under the
# declared output name and, beside it, the sealing contract's own completion
# envelope. The envelope is the COMPLETION SIGNAL -- `sealing.
# _completion_envelope`: "a worker that published none has not completed" --
# so its ABSENCE under a tree that carries a finished proposal is exactly the
# shape of this trigger: the producer measured its own output, refused it, and
# faulted before signalling anything.
COMPLETION_ENVELOPE = "output.json"
PRODUCER_RESULT = "result.json"
PRODUCER_VERIFICATION = "verification.txt"
# The two generations of the worker's typed result this build reads, by value
# from the owner that already owns the vocabulary rather than respelled.
from ..worker_manager.failure_cause import (                     # noqa: E402
    DECLARED_ENDINGS, RETAINED_RESULT_SCHEMAS)

# The declared ending a COMPLETED producer carries. `candidate` is the word
# `claude_agent` publishes when the turn produced a proposal and its own
# required verification passed; every other member of the vocabulary is a
# different ending and is not reclassified here.
COMPLETED_ENDING = "candidate"
if COMPLETED_ENDING not in DECLARED_ENDINGS:              # pragma: no cover
    raise AssertionError(
        "this trigger names an ending the worker vocabulary does not carry")

# THE REFUSALS THE SOURCE-AWARE OWNER SPEAKS IN, named by value so a hold can
# carry one without this module pretending it is a contract answer of its own.
# `IntegrationProfileRefusal` is deliberately not a `ContractRefusal`: it is
# the Git owner's answer about Git, and a generic manager that let it escape
# would turn "this bundle does not carry that commit" into a traceback.
from ..integration.git_profile import (                          # noqa: E402
    IntegrationProfileRefusal as _GitRefusal)
SOURCE_REFUSALS = (_GitRefusal,)

# THE COMMAND BOUNDS, read from the trigger reader that already resolved them
# so one spelling serves both recoveries, and the path-set bound from the
# declaration owner that already states the entry ceiling.
MAX_ARGV_WORDS = failure_analysis.MAX_ARGV_WORDS
MAX_ARGV_BYTES = failure_analysis.MAX_ARGV_BYTES
MAX_CHANGED_PATHS = role_contract.MAX_OUTPUT_ENTRIES


def _hold(holds, category, code, message):
    """One reported hold, and the read keeps going.

    THE WHOLE POINT OF A READ-ONLY INSPECTION is that an owner is shown every
    reason this recovery is not eligible, not merely the first one somebody's
    control flow reached. A refusal would answer one; a list answers all of
    them, and `decide` is what refuses to act while any is present.
    """
    holds.append({"category": category, "code": code, "message": message})
    return None


def _held(holds, refusal):
    return _hold(holds, refusal.category, refusal.code, refusal.message)


def _argv(value, what):
    """A command as the WORDS IT ACTUALLY IS, bounded.

    `failure_analysis._argv`'s rule and `integration.driver`'s before it: "a
    command this module would have to assemble from a string is a shell, and
    there is no shell here".
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


def _failed_publication(jobs, control, *, job_id, stage_id, episode):
    """THE EXACT FAILED EXECUTION, resolved from the Job's own rows.

    NOT FROM AN OPERAND, which is the first half of REC-9's trust rule: the
    attempt is the one THIS Job's THIS stage's THIS episode opened, so an
    operator naming another attempt is naming a different execution and is
    refused by the binding rather than believed. The assignment comes off the
    host's own attempt row and is cross-bound against the stage's Work, so
    evidence about another deployment's execution cannot arrive wearing this
    one's selectors.

    AND THE PUBLICATION FAILURE IS PROVED BY ABSENCE, through the owner that
    would hold its presence: `frozen_output_of` answers `None` for an attempt
    that froze no result, and a frozen result is what publication IS. An
    attempt that published is not this trigger and is not reclassified into
    it.
    """
    from ..worker_manager import attempts, failure_cause

    boundaries.identity(job_id, "a Job id")
    boundaries.identity(stage_id, "a stage id")
    if type(episode) is not int or type(episode) is bool or episode < 1:
        _refuse("an episode is a whole number from one",
                category="integrity", code="schema")
    held = submission.job_of(jobs, job_id)
    if held is None:
        _refuse(f"this store holds no Job {name_value(job_id)}")
    stages = {one["stage_id"]: one for one in submission.stages_of(jobs,
                                                                   job_id)}
    stage = stages.get(stage_id)
    if stage is None:
        _refuse(f"Job {name_value(job_id)} carries no stage "
                f"{name_value(stage_id)}; a publication recovery is about the "
                f"producer stage of the Job it names")
    if stage["kind"] != "implementation":
        _refuse(f"stage {name_value(stage_id)} is "
                f"{name_value(stage['kind'])} and an output-publication "
                f"recovery follows the IMPLEMENTATION that completed and then "
                f"failed to publish; another stage's ending is another ending")
    found = episodes.episode_of(jobs, stage_id, episode)
    if found is None:
        _refuse(f"stage {name_value(stage_id)} has no episode {episode}; the "
                f"failed execution is the one this stage actually opened")
    attempt_id = found["attempt_id"]
    assignment = attempts.assignment_of(control, attempt_id)
    if assignment["work_id"] != stage["work_id"]:
        _refuse(f"attempt {name_value(attempt_id)} ran under Work "
                f"{name_value(assignment['work_id'])} and stage "
                f"{name_value(stage_id)} names "
                f"{name_value(stage['work_id'])}; evidence about one "
                f"execution is not evidence about another",
                category="integrity", code="schema")
    frozen = frozen_output_of(control, attempt_id)
    if frozen is not None:
        _refuse(f"attempt {name_value(attempt_id)} FROZE result "
                f"{name_value(frozen['result_id'])}; its output was "
                f"published and this recovery is for an output that was not. "
                f"A published result is disposed of through the ordinary "
                f"collection and review path")
    composed = failure_cause.attempt_failure_cause_of(control, attempt_id)
    if composed is None:                                  # pragma: no cover
        _refuse(f"this manager holds no attempt {name_value(attempt_id)}; a "
                f"terminal ending is attributed through the owner that holds "
                f"the attempt")
    cessation = {"answer": failure_cause.answer_of(composed),
                 "absent_records": list(failure_cause.absent_of(composed)),
                 "declaration": failure_cause.declaration_of(composed)}
    return {"job_id": job_id, "stage_id": stage_id, "episode": episode,
            "attempt_id": attempt_id, "work_id": stage["work_id"],
            "authority_uuid": assignment["authority_uuid"],
            "participant": assignment["participant"],
            "principal": assignment["principal"],
            "generation": assignment["generation"],
            "effective_scope": assignment["effective_scope"],
            "ended_state": found["ended_state"],
            "ended_at": found["ended_at"],
            "input_digest": held["input_digest"],
            "policy_digest": held["policy_digest"],
            "submission_id": held["submission_id"],
            "terminal_policy": held["terminal_policy"],
            "cessation": cessation}


def producer_entries(declaration):
    """WHERE THE ADAPTER'S OWN RECORDS SIT INSIDE THE ORIGINAL.

    INSIDE THE DECLARED OUTPUT DIRECTORY, WHICH IS WHAT THE ORIGINAL IS
    (review 2026-11-23T20-28-00Z F1). The host owner is handed the declared
    output's own path and proves and measures THAT directory, so these names
    are relative to it. The first cut measured the attempt's whole writable
    root and prefixed these with the declared path -- which was the same two
    files only while a fixture's workspace held nothing but the proposal. A
    real producer's writable root is its candidate's working tree, and its
    development line is a whole checkout. The two names are constants of the
    producing adapter's contract, which is why they are not operands.
    """
    del declaration
    return (PRODUCER_RESULT, PRODUCER_VERIFICATION)


def _retained_output(host, failed, declaration, *, holds):
    """THE ORIGINAL HOST-HELD OUTPUT, through the host owner, or a hold.

    EVERY REFUSAL THIS PORT RAISES IS A HOLD AND NOT A CRASH, because each of
    them is one of REC-9's own: missing, unreadable, substituted or
    unverifiable. An owner reading the inspection is owed the sentence the
    owner of the bytes produced, in the vocabulary it produced it in.
    """
    _port(host, HOST_OUTPUT, what="the host output port")
    try:
        return host.output_of(failed["attempt_id"],
                              read=producer_entries(declaration),
                              output=declaration["output"]["path"])
    except ContractRefusal as refusal:
        return _held(holds, refusal)


def _shape(output, *, declaration, holds):
    """WHAT IS IN THE ORIGINAL, judged against the corrective declaration.

    THREE QUESTIONS AND THEY ARE THREE:

      IS THERE A COMPLETION ENVELOPE? If there is, this producer SIGNALLED
        completion and whatever went wrong afterwards is not the ending this
        slice classifies. The envelope's absence is the trigger.
      DID THE OUTPUT EXCEED THE DECLARATION IT WAS ADMITTED UNDER? REC-9's
        first slice is the producer whose publication failed on the declared
        ceiling, and an output that fits the ORIGINAL 1048576 bytes failed for
        some other reason this build does not classify. Reported rather than
        assumed, from the measurement rather than from a report.
      DOES IT FIT THE CORRECTIVE DECLARATION? W385694's exact selected
        104857600 bytes, 100 entries, forbidden links and allowed media. An
        original that overflows the SELECTED ceiling too is not publishable by
        this recovery either, and saying so now is the honest answer.
    """
    manifest = output["manifest"]
    constraints = declaration["output"]["constraints"]
    paths = {one["path"] for one in manifest["entries"]}
    # THE COMPLETION SIGNAL IS AT THE WRITABLE ROOT, beside the declared
    # output and never inside it, so it is the owner's own answer rather than
    # an entry of the measured proposal.
    if output.get("completion_envelope") is True \
            or COMPLETION_ENVELOPE in paths:
        _hold(holds, "refused", "precondition",
              f"the retained output carries {name_value(COMPLETION_ENVELOPE)}, "
              f"which is the worker's completion signal; this recovery is for "
              f"a producer that measured its own output, refused it and "
              f"published no envelope, and an ending that signalled completion "
              f"is not reclassified here")
    if manifest["total_bytes"] <= ORIGINAL_PROPOSAL_BYTES:
        _hold(holds, "refused", "precondition",
              f"the retained output measures {manifest['total_bytes']} bytes, "
              f"which is inside the {ORIGINAL_PROPOSAL_BYTES} its producer was "
              f"admitted under; this first slice recovers a publication that "
              f"failed on the declared byte ceiling, and another cause is "
              f"reported rather than classified into this one")
    if manifest["total_bytes"] > constraints["max_bytes"]:
        # `integrity/limit` AND NOT `refused/limit`. W385695 checkpoint 2:
        # the pairing is closed -- `contracts.errors._PAIRING` puts `limit`
        # under `integrity` and nowhere else -- and `decide` re-raises the
        # first hold under its own category and code. So a `refused/limit`
        # hold did not refuse an oversized original at all: it raised an
        # AssertionError out of the error constructor, which is a defect
        # report rather than the answer an owner is owed. Measured by driving
        # a real 101-entry original at it.
        _hold(holds, "integrity", "limit",
              f"the retained output measures {manifest['total_bytes']} bytes "
              f"and the selected {declaration['descriptor']} declares "
              f"{constraints['max_bytes']}; an original the corrective "
              f"declaration cannot carry is not published by widening it here")
    if manifest["entry_count"] > constraints["max_entries"]:
        _hold(holds, "integrity", "limit",
              f"the retained output carries {manifest['entry_count']} entries "
              f"and the selected declaration allows "
              f"{constraints['max_entries']}; the entry ceiling, the media "
              f"types and the link policy are unchanged by this recovery")
    return {"root_identity": output["identity"],
            "tree_digest": manifest["tree_digest"],
            "entry_count": manifest["entry_count"],
            "total_bytes": manifest["total_bytes"],
            "paths": sorted(paths),
            "completion_envelope": output.get("completion_envelope") is True
            or COMPLETION_ENVELOPE in paths,
            "exceeded": manifest["total_bytes"] > ORIGINAL_PROPOSAL_BYTES,
            "fits_corrective": (manifest["total_bytes"]
                                <= constraints["max_bytes"]
                                and manifest["entry_count"]
                                <= constraints["max_entries"])}


def _producer_evidence(output, failed, task, declaration, *, holds):
    """THE ADAPTER'S OWN ACCOUNT, QUALIFIED -- AND IT IS NOT ACCEPTANCE.

    REC-9 states the qualification clause by clause and every one of them is a
    comparison here:

      the record is the ADAPTER'S, measured in the original output at the path
        the adapter writes it to, read back against that measurement;
      it declares a generation this build reads and the COMPLETED ending;
      a verification was attempted and EXITED 0, from the adapter's observed
        wait result rather than from provider prose;
      its argv agrees with the READ-ONLY ADMITTED TASK, which is the Job
        owner's own document and not a copy;
      it binds the exact candidate, its base and its declared path set; and
      it names the task identity the Job was admitted under.

    WHAT THE ANSWER SAYS ABOUT ITSELF. `qualification` is the word
    `producer-evidence`, and `independent_acceptance` is `False` -- stated in
    the document rather than left to a reader's charity, because the one thing
    this evidence must never become is the reason a result was accepted. The
    reviewer's own required verification stays owed, under the selected
    command and invocation limits, and `reuse` says only which command the
    recovery pipeline does not repeat.
    """
    result_path, account_path = producer_entries(declaration)
    entries = output["entries"]
    raw = entries.get(result_path)
    if raw is None:                                       # pragma: no cover
        return _hold(holds, "refused", "precondition",
                     f"the retained output carries no measured "
                     f"{name_value(result_path)}")
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return _hold(holds, "integrity", "schema",
                     f"the retained {name_value(result_path)} is not a "
                     f"readable document; an unreadable attribution HOLDS and "
                     f"is never interpreted as a success")
    if type(document) is not dict \
            or document.get("schema") not in RETAINED_RESULT_SCHEMAS:
        return _hold(holds, "integrity", "schema",
                     f"the retained result declares generation "
                     f"{name_value((document or {}).get('schema'))}, which "
                     f"this build does not read; it is not decoded against a "
                     f"shape nobody promised")
    if document.get("disposition") != COMPLETED_ENDING:
        return _hold(holds, "refused", "precondition",
                     f"the retained result declares ending "
                     f"{name_value(document.get('disposition'))} and this "
                     f"recovery follows a producer that declared "
                     f"{name_value(COMPLETED_ENDING)}; a producer that did "
                     f"not complete has no output to publish")
    provider = document.get("provider")
    provider = provider if type(provider) is dict else {}
    if provider.get("failure_reason") is not None:
        return _hold(holds, "refused", "precondition",
                     f"the retained result names provider failure reason "
                     f"{name_value(provider.get('failure_reason'))}; a "
                     f"provider failure is a different ending")
    verification = document.get("verification")
    if type(verification) is not dict:
        return _hold(holds, "refused", "precondition",
                     f"the retained result carries no verification record, so "
                     f"whether the producer's own required command ran is "
                     f"UNKNOWN; unknown HOLDS and is not reverified blindly")
    if verification.get("status") != 0:
        return _hold(holds, "refused", "precondition",
                     f"the retained result declares verification status "
                     f"{name_value(verification.get('status'))}; producer "
                     f"evidence is reusable only when the adapter observed "
                     f"exit 0, and a non-zero status is REC-8's trigger rather "
                     f"than this one")
    try:
        argv = _argv(verification.get("argv"),
                     "the producer's own verification command")
    except ContractRefusal as refusal:
        return _held(holds, refusal)
    base = document.get("base")
    head = document.get("head")
    for name, value in (("base", base), ("head", head)):
        if type(value) is not str or not value:
            _hold(holds, "integrity", "schema",
                  f"the retained result names no {name} this build can own; a "
                  f"candidate bound to no revision is bound to nothing")
    paths = document.get("changed_paths")
    if type(paths) is not list or not paths \
            or not all(type(one) is str and one for one in paths) \
            or len(paths) > MAX_CHANGED_PATHS:
        _hold(holds, "integrity", "schema",
              f"the retained result declares no path set of at most "
              f"{MAX_CHANGED_PATHS} entries; a candidate whose own account of "
              f"what it changed is unreadable is not corresponded")
        paths = []
    # THE READ-ONLY ADMITTED TASK IS THE OTHER SIDE OF THE COMPARISON, and
    # where there is none this HOLDS rather than accepting the adapter's own
    # word for what it was asked to run. "The adapter's command from the
    # read-only task" is the contract's phrase, and a comparison with nothing
    # is not that comparison.
    if task is None:
        _hold(holds, "refused", "precondition",
              "this Job records no admitted task document, so the producer's "
              "argv cannot be held against the command it was admitted to "
              "run; an attribution nothing binds is not valid attribution")
    else:
        if document.get("task_id") != task.get("task_id"):
            _hold(holds, "integrity", "schema",
                  f"the retained result names task "
                  f"{name_value(document.get('task_id'))} and this Job's "
                  f"admitted task is {name_value(task.get('task_id'))}; a "
                  f"record about another task is not evidence about this "
                  f"execution")
        declared = task.get("verification")
        if type(declared) is not list or list(declared) != argv:
            _hold(holds, "integrity", "schema",
                  f"the producer ran {sample_of(argv)} and the read-only "
                  f"admitted task declares "
                  f"{sample_of(list(declared) if type(declared) is list else [])}"
                  f"; an adapter's argv is attributable only when it is the "
                  f"task's own")
        if task.get("declared_base") is not None \
                and task["declared_base"] != base:
            _hold(holds, "integrity", "digest",
                  f"the producer declares base {name_value(base)} and the "
                  f"admitted task was delivered against "
                  f"{name_value(task['declared_base'])}; a command string "
                  f"must not hide a changed input identity")
    context = {"schema": document["schema"], "task_id": document.get("task_id"),
               "base": base, "entry_head": document.get("entry_head"),
               "argv": argv, "status": 0,
               "seconds_bound": provider.get("seconds_bound"),
               "seconds_bound_source": provider.get("seconds_bound_source")}
    return {"schema": document["schema"],
            "attributed_to": "role-adapter",
            "source": f"{result_path} measured in the original output",
            "declared_ending": document["disposition"],
            "argv": argv, "status": 0,
            "task_id": document.get("task_id"),
            "base": base, "head": head, "entry_head": document.get("entry_head"),
            "changed_paths": sorted(paths),
            "verification_account": (account_path in entries
                                     and len(entries[account_path]) or 0),
            "context": context,
            "context_digest": digest(context),
            "result_digest": digest_of_bytes(raw),
            # THE TWO SENTENCES THAT KEEP THIS EVIDENCE WHAT IT IS.
            "qualification": "producer-evidence",
            "independent_acceptance": False,
            "reuse": ("the recovery pipeline does not repeat this producer "
                      "verifier; the substantive reviewer still owes its own "
                      "required verification and investigation, including "
                      "tests, under the selected command and invocation "
                      "limits")}


def _correspondence(source, output, producer, *, holds):
    """CANDIDATE, BASE AND PATH SET, through the SOURCE-AWARE owner.

    THE GENERIC MANAGER DOES NOT INTERPRET GIT, which is REC-9's own boundary
    and the reason this is a port rather than a function. What crosses is the
    proved original root, the measured entry set and the producer's own
    declared base, head and paths; what comes back is the Git-aware consumer's
    answer about whether this repository really holds that commit on that base
    and whether its content is that path set. A refusal from that owner is a
    HOLD here, in its own words.

    AND THE ANSWER IS COMPARED, not merely received. An owner that answered
    about another revision would otherwise be a correspondence proof for a
    candidate nobody asked about.
    """
    if producer is None:
        return _hold(holds, "refused", "precondition",
                     "the producer attribution did not qualify, so there is "
                     "no candidate to correspond; correspondence is not "
                     "asked about an unqualified claim")
    _port(source, SOURCE_CORRESPONDENCE, what="the source correspondence port")
    request = {"root": output["root"], "tree_digest":
               output["manifest"]["tree_digest"],
               "entries": [one["path"] for one in output["manifest"]["entries"]],
               "base": producer["base"], "candidate": producer["head"],
               "changed_paths": list(producer["changed_paths"])}
    # OWNER SELECTION M385913 (option A): WHERE THE BASE MAY BE READ FROM. The
    # host owner's answer names the line's own durably recorded source for a
    # line-layout original, with whether that object is still the recorded
    # one. It is passed through as it was answered -- this module chooses no
    # repository -- and is absent for an attempt-layout original, where the
    # correspondence stays bundle-only.
    if output.get("source") is not None:
        request["base_source"] = dict(output["source"])
    try:
        answer = source.correspondence_of(request)
    except ContractRefusal as refusal:
        return _held(holds, refusal)
    except Exception as refusal:
        # THE SOURCE OWNER REFUSES IN ITS OWN VOCABULARY, and that refusal is
        # a HOLD here rather than a crash. `integration.git_profile` raises
        # `IntegrationProfileRefusal`, which is deliberately not a
        # `ContractRefusal` -- it is the Git owner's answer about Git -- and a
        # generic manager that let it escape would turn "this bundle does not
        # carry that commit" into a traceback instead of a reason an owner
        # can read. The type is named in the hold so nothing is laundered
        # into a contract category it did not come from.
        if type(refusal) not in SOURCE_REFUSALS:
            raise
        return _hold(holds, "refused", "precondition",
                     f"the source-aware owner refused this correspondence "
                     f"({type(refusal).__name__}): {refusal}")
    try:
        held = boundaries.document(
            answer, "the source correspondence answer",
            required=("base", "candidate", "changed_paths", "vectors"),
            # THE TREE NAMES ARE OPTIONAL AND THEY TRAVEL. A Git-aware owner
            # that resolved the commits has resolved their trees too, and
            # carrying them lets a reader see WHICH content was corresponded
            # rather than only that something was; a port that answers without
            # them is still answering this question.
            optional=("base_tree", "candidate_tree", "owner"))
    except ContractRefusal as refusal:
        return _held(holds, refusal)
    if held["base"] != producer["base"] \
            or held["candidate"] != producer["head"]:
        return _hold(holds, "integrity", "digest",
                     f"the source owner corresponded candidate "
                     f"{name_value(held['candidate'])} on "
                     f"{name_value(held['base'])} and the retained output "
                     f"declares {name_value(producer['head'])} on "
                     f"{name_value(producer['base'])}; a correspondence about "
                     f"another revision proves nothing about this one")
    if sorted(held["changed_paths"]) != sorted(producer["changed_paths"]):
        return _hold(holds, "ambiguous", "collection",
                     f"the source owner read "
                     f"{len(held['changed_paths'])} changed paths out of the "
                     f"candidate and the retained result declares "
                     f"{len(producer['changed_paths'])}; two accounts of one "
                     f"candidate are not resolved by picking a half")
    return {"base": held["base"], "candidate": held["candidate"],
            "base_tree": held.get("base_tree"),
            "candidate_tree": held.get("candidate_tree"),
            "changed_paths": sorted(held["changed_paths"]),
            "vectors": [list(one) for one in held["vectors"]],
            "owner": "the deployment's source-aware consumer in confinement"}


def _exclusion(exclusion, attempt_ids, *, holds):
    """POSITIVE CESSATION, from the host, and `unknown` is a hold.

    `fresh_attempt.CEASED_RUNTIME` and `SETTLED_CLEANUP` are the Worker
    Manager's axis words, read from the module that already resolved them. The
    difference from `retained_recovery._excluded` is only what happens to the
    answer: there it raises, because an admission is about to perform effects;
    here it is reported, because an inspection performs none and an owner is
    owed the whole picture.
    """
    _port(exclusion, ("instance", "evidence_of"),
          what="the host exclusion port")
    held = exclusion.evidence_of(tuple(attempt_ids))
    boundaries.document(held if isinstance(held, dict) else {},
                        "the host's attempt evidence", required=("host",),
                        optional=tuple(attempt_ids))
    evidence = {}
    for attempt_id in attempt_ids:
        if attempt_id not in held:
            _hold(holds, "runtime-observation", "quiescence-unknown",
                  f"the host returned no evidence about attempt "
                  f"{name_value(attempt_id)}; an execution nobody can account "
                  f"for is unknown, and unknown is not permission to publish "
                  f"the bytes it may still be writing")
            continue
        found = held[attempt_id]
        if found is None:
            evidence[attempt_id] = {
                "runtime": None, "cleanup": None, "resource": None,
                "ceased": False,
                "basis": f"no attempt was ever recorded on this instance's "
                         f"own host, {held['host']}"}
            _hold(holds, "runtime-observation", "quiescence-unknown",
                  f"this host has no record of attempt "
                  f"{name_value(attempt_id)}; the original output is read "
                  f"under POSITIVE cessation and an absence is not one")
            continue
        runtime = (found.get("runtime") or {}).get("execution_runtime")
        cleanup = (found.get("runtime") or {}).get("cleanup")
        token = found.get("token")
        ceased = runtime in fresh_attempt.CEASED_RUNTIME
        settled = cleanup in fresh_attempt.SETTLED_CLEANUP
        returned = bool(token and token.get("returned"))
        evidence[attempt_id] = {"runtime": runtime, "cleanup": cleanup,
                                "resource": "returned" if returned else None,
                                "ceased": ceased and settled and returned,
                                "basis": "the host's own record"}
        if not ceased:
            _hold(holds, "runtime-observation", "quiescence-unknown",
                  f"attempt {name_value(attempt_id)}'s runtime is "
                  f"{name_value(runtime)} and cessation is "
                  f"{', '.join(fresh_attempt.CEASED_RUNTIME)}; a writer this "
                  f"host cannot say has stopped is a writer")
        elif not settled:
            _hold(holds, "runtime-observation", "quiescence-unknown",
                  f"attempt {name_value(attempt_id)}'s cleanup is "
                  f"{name_value(cleanup)} and this host still owes it; an "
                  f"accounting that has not finished may still reach these "
                  f"bytes")
        elif not returned:
            _hold(holds, "runtime-observation", "quiescence-unknown",
                  f"attempt {name_value(attempt_id)} has not returned its "
                  f"workspace resource; an outstanding token is uncertainty "
                  f"about a resource rather than evidence it was released")
    return evidence


# -- 6. the owner-facing read ------------------------------------------------

READ_SCHEMA = RECOVERY_SELECTION

# THE MEMBERS THE SELECTION DIGEST COVERS, closed and ordered. The digest is
# what a decision binds, so what it covers is the whole of what an owner was
# shown ABOUT THE RECOVERY -- and deliberately not the parts that are about
# the READING: `authorization` says who happened to ask, `decisions` and
# `admissions` say what has already happened since, and either one changing
# would make an owner's approval of unchanged evidence collide.
SELECTION_MEMBERS = ("schema", "selector", "job", "output", "producer",
                     "correspondence", "cessation", "exclusion",
                     "declaration", "profile", "stages", "provenance",
                     "reviewer", "holds", "eligible")


def selection_digest(selection):
    """The canonical identity of ONE inspection answer.

    ONE FUNCTION FOR BOTH SIDES, `expected_facts`' rule: the read reports this
    and `decide` recomputes it from the read it takes itself, so an owner
    approving exactly what they were shown cannot be refused for a
    transcription -- and an owner approving something else cannot be accepted.
    """
    missing = [one for one in SELECTION_MEMBERS if one not in selection]
    if missing:
        _refuse(f"a publication recovery selection carries "
                f"{', '.join(SELECTION_MEMBERS)}; this one has no "
                f"{', '.join(missing)}", category="integrity", code="schema")
    return digest({one: selection[one] for one in SELECTION_MEMBERS})


def _admitted_task(jobs, job_id, *, holds):
    """The Job owner's own task document, READ-ONLY, parsed once.

    `creation.job_task_of` walks the retry lineage to the creation that made
    this Job and answers the composed document as TEXT. `None` is an ordinary
    answer for a Job submitted by hand, and this reports it as the hold it is
    rather than inventing a command to compare against.
    """
    try:
        held = creation.job_task_of(jobs, job_id)
    except ContractRefusal as refusal:
        return _held(holds, refusal)
    if held is None:
        return None
    try:
        document = json.loads(held)
    except (UnicodeDecodeError, ValueError):              # pragma: no cover
        return _hold(holds, "integrity", "schema",
                     f"Job {name_value(job_id)}'s admitted task document is "
                     f"not readable as one document")
    return document if type(document) is dict else None


def inspect(jobs, control, *, job_id, stage_id, episode, host, exclusion,
            source, authorization=None, now=None):
    """WHAT THE OWNER IS LOOKING AT BEFORE THEY DECIDE. A READ, and it writes
    nothing.

    EVERY FACT COMES FROM THE OWNER THAT HOLDS IT. The Job, its stage and its
    episode are this store's; the attempt and its assignment are the Worker
    Manager's; the absence of a published result is the output owner's; the
    original bytes, their object identity and their measurement are the
    workspace owner's, under a completed preparation and settled writers; the
    runtime and resource cessation are the host's; the candidate/base/path
    correspondence is the source-aware consumer's; and the corrective
    declaration and the finite profile are the owner selections this build
    holds and proves.

    NOTHING IS RESERVED AND NOTHING IS TRUSTED FROM A COPY. There is no
    operand through which a caller could name a path, a manifest, a digest or
    an attempt: the selectors are a Job, a stage and an episode, and
    everything else is resolved from them.

    IT REPORTS ITS HOLDS RATHER THAN RAISING THE FIRST ONE. An owner deciding
    whether to approve needs every reason this is not yet eligible, which a
    refusal cannot carry. `eligible` is `False` while any hold stands, and
    `decide` is what refuses to approve one.
    """
    holds = []
    failed = _failed_publication(jobs, control, job_id=job_id,
                                 stage_id=stage_id, episode=episode)
    declaration = corrective_declaration()
    task = _admitted_task(jobs, job_id, holds=holds)
    evidence = _exclusion(exclusion, (failed["attempt_id"],), holds=holds)
    output = _retained_output(host, failed, declaration, holds=holds)
    shape = (None if output is None
             else _shape(output, declaration=declaration, holds=holds))
    producer = (None if output is None
                else _producer_evidence(output, failed, task, declaration,
                                        holds=holds))
    correspondence = (None if output is None else
                      _correspondence(source, output, producer, holds=holds))
    # THE COMMANDS ARE REPORTED BESIDE THE ANSWER AND ARE NOT DIGESTED.
    # An operator is owed the exact argv the source-aware owner composed --
    # it is how they can tell a real correspondence from a claimed one -- but
    # those words name a PRIVATE SCRATCH REPOSITORY this read created and
    # removed, so a different path on every read would make two inspections of
    # unchanged evidence collide and refuse the owner's own approval. The
    # facts are what the decision binds; the commands are what it was shown.
    commands = ([] if correspondence is None
                else correspondence.pop("vectors"))
    # THE COMPOSED CAUSE IS REPORTED AND IS NOT A GATE, and the distinction
    # is the one `failure_cause.answer_of` draws for itself. Its four answers
    # are about a cessation THIS MANAGER ORDERED, and nobody ordered one here:
    # a producer that measured its own output, refused it and exited is an
    # attempt with no stop to account for, which reads `unknown` and should.
    # What gates this recovery is POSITIVE cessation -- the host's own
    # runtime, cleanup and token answers above, and the completed preparation
    # and settled writers the workspace owner proves before it measures a
    # byte. Holding on this member instead would refuse every ordinary
    # instance of the ending the capability exists for.
    fence = cancellation.fence_of(jobs, job_id)
    if fence is not None and fence.get("trigger", "operator") == "operator":
        _hold(holds, "refused", "precondition",
              f"Job {name_value(job_id)} was cancelled at "
              f"{fence['requested_at']} ({fence['reason']}); a cancelled "
              f"execution is never revived and its retained output is not "
              f"published under a new identity")
    policy = resolved_profile()
    selection = {
        "schema": READ_SCHEMA,
        "selector": {one: failed[one] for one in
                     ("job_id", "stage_id", "episode", "attempt_id",
                      "work_id", "authority_uuid", "participant", "principal",
                      "generation", "effective_scope")},
        "job": {"submission_id": failed["submission_id"],
                "input_digest": failed["input_digest"],
                "policy_digest": failed["policy_digest"],
                "terminal_policy": failed["terminal_policy"],
                "ended_state": failed["ended_state"],
                "ended_at": failed["ended_at"],
                "published_result": None,
                "task_id": None if task is None else task.get("task_id"),
                "task_declared_base": (None if task is None
                                       else task.get("declared_base"))},
        "output": shape, "producer": producer,
        "correspondence": correspondence,
        "cessation": failed["cessation"], "exclusion": evidence,
        "declaration": declaration, "profile": policy,
        "stages": [list(one) for one in SELECTED_STAGE_SETS],
        "provenance": dict(PROVENANCE),
        # WHAT THE REVIEWER STILL OWES, stated in the selection the owner
        # approves rather than left to the review contract to be remembered.
        # REC-9: producer evidence "is producer evidence, NEVER independent
        # acceptance", and the reviewer "MUST still perform required
        # independent verification and investigation, including tests".
        "reviewer": {
            "independent_verification": "required",
            "investigation_and_tests": "required",
            "invocation_seconds": policy["review_provider_invocation_seconds"],
            "each_command_seconds": policy["verification_command_seconds"],
            "excluded_principals": "the original implementation principal and "
                                   "the publication principal",
            "producer_evidence": "qualified and reused, never acceptance"},
        "holds": holds,
        "eligible": not holds,
    }
    selection["selection_digest"] = selection_digest(selection)
    selection["source_commands"] = commands
    selection["fence"] = fence
    selection["decisions"] = [
        {"decision_id": one["decision_id"], "disposition": one["disposition"],
         "decided_at": one["decided_at"], "endpoint": one["owner"]["endpoint"],
         "selection_digest": one["expected"]["selection_digest"]}
        for one in decisions_for(jobs, job_id)]
    selection["admissions"] = [
        {"decision_id": one["decision_id"], "state": one["state"],
         "job_id": one["job_id"], "reserved": one["reserved"]}
        for one in held_admissions_of(jobs)
        if one["prior_job_id"] == job_id]
    if authorization is not None:
        try:
            selection["authorization"] = _owner(
                authorization, failed["work_id"],
                what="the owner authorization port")
            selection["authorization"]["holds"] = True
        except ContractRefusal as refusal:
            selection["authorization"] = {
                "participant": getattr(authorization, "participant", None),
                "holds": False,
                "why": {"category": refusal.category, "code": refusal.code,
                        "message": refusal.message}}
    if now is not None:
        selection["control"] = job_control.report(jobs, job_id, now=now)
    return selection


def expected_facts(selection):
    """THE EXACT OPERANDS A DECISION BINDS, in the spelling `decide` compares.

    Composed from one inspection answer, so the read reports what the decision
    will be held to and the decision recomputes it from its own fresh read. A
    selection carrying holds has no expected facts to offer: there is nothing
    to approve, and composing a document that looked approvable would be this
    function helping somebody past the refusal.
    """
    if selection.get("producer") is None or selection.get("output") is None:
        _refuse("this inspection qualified no producer evidence and no "
                "measured original, so there are no exact facts for a "
                "decision to bind; the holds it reports are what to answer")
    return {"attempt_id": selection["selector"]["attempt_id"],
            "producer_argv": list(selection["producer"]["argv"]),
            "producer_status": selection["producer"]["status"],
            "candidate_base": selection["producer"]["base"],
            "candidate_head": selection["producer"]["head"],
            "output_tree_digest": selection["output"]["tree_digest"],
            "output_total_bytes": selection["output"]["total_bytes"],
            "verification_context_digest":
                selection["producer"]["context_digest"],
            "selection_digest": selection["selection_digest"]}


EXPECTED_MEMBERS = ("attempt_id", "producer_argv", "producer_status",
                    "candidate_base", "candidate_head", "output_tree_digest",
                    "output_total_bytes", "verification_context_digest",
                    "selection_digest")


def _expected(value):
    taken = boundaries.document(value, "the facts this decision was taken on",
                                required=EXPECTED_MEMBERS)
    boundaries.identity(taken["attempt_id"], "the decided attempt id")
    for member in ("candidate_base", "candidate_head", "output_tree_digest",
                   "verification_context_digest", "selection_digest"):
        boundaries.text(taken[member], f"the decided {member}")
    if taken["producer_status"] != 0:
        _denied(f"this decision binds producer status "
                f"{name_value(taken['producer_status'])}; producer evidence "
                f"is reusable only at exit 0, and approving anything else "
                f"would be approving a producer that did not pass its own "
                f"required command")
    if type(taken["output_total_bytes"]) is not int \
            or type(taken["output_total_bytes"]) is bool \
            or taken["output_total_bytes"] <= 0:
        _refuse("the decided output byte count is a whole number above zero",
                category="integrity", code="schema")
    return {**{name: taken[name] for name in EXPECTED_MEMBERS},
            "producer_argv": _argv(taken["producer_argv"],
                                   "the producer verification command")}


# -- 7. the durable records --------------------------------------------------
#
# TWO KINDS, BOTH ORDINARY OPERATIONS OF THIS STORE'S EXISTING JOURNAL, for
# `retained_recovery`'s reasons: the journal already supplies exact replay,
# collision on changed operands and a committed result later incarnations read
# instead of re-deciding. No schema change and no new table -- which matters
# here for a second reason, because the schema generation this capability will
# eventually need is a ONE-WAY store upgrade nobody has selected for any live
# instance.
DECISION_KIND = "publication.owner-decision"
HELD_KIND = "publication.admission-held"
# W385695 checkpoint 2: THE THREE RECORDS A REAL ADMISSION IS MADE OF, each
# one durable BEFORE the external act it authorizes and each replayed exactly.
# `retained_recovery`'s split, for its reasons: the INTENT is the reservation
# of the recovery identity inside this store's write lock, the ENDING is the
# Authority transition that releases the prior assignment on the reused Work,
# and the ADMITTED record is the completion that closes the intent.
#
# THREE RECORDS AND NOT ONE, because each is a different cut. A crash between
# the reservation and the ending leaves an identity spoken for and an
# assignment still held, which is resumable and is reported as such; a crash
# between the ending and the submission leaves a released Work and a reserved
# identity, which the same request resumes; and a crash after the submission
# leaves a Job whose completion record the next incarnation writes from rows
# rather than from memory. One combined record could not say which of those
# happened.
INTENT_KIND = "publication.admission-intent"
ENDING_KIND = "publication.prior-assignment-ended"
ADMITTED_KIND = "publication.admitted"

DECISION_MEMBERS = ("job_id", "stage_id", "episode", "attempt_id",
                    "decision_id", "disposition", "owner", "work_id",
                    "expected", "declaration_digest", "profile",
                    "profile_digest", "stages", "provenance", "decided_at")
HELD_MEMBERS = ("decision_id", "prior_job_id", "job_id", "work_id",
                "submission_id", "stages", "state", "reserved",
                "prerequisites", "owners", "candidate", "output",
                "readiness", "gate", "recorded_at")
# THE RESERVATION'S OWN OPERANDS. `input_declaration` is the exact recovery
# input the publication stage is admitted against -- the document whose digest
# the Job carries -- so a later incarnation can compare the bytes a worker
# staged against the approved selection without re-deriving anything.
INTENT_MEMBERS = ("decision_id", "prior_job_id", "job_id", "work_id",
                  "submission_id", "stages", "state", "publication_stage_id",
                  "review_stage_id", "candidate",
                  "output", "input_declaration", "input_digest",
                  "recovery_input_digest", "worker", "bounds", "intended_at")
ENDING_MEMBERS = ("decision_id", "job_id", "work_id", "disposition",
                  "expect", "answer", "cessation", "ended_at")
ADMITTED_MEMBERS = ("decision_id", "prior_job_id", "job_id", "work_id",
                    "submission_id", "stages", "state", "stage_ids",
                    "publication_stage_id", "review_stage_id",
                    "candidate", "output",
                    "input_declaration", "input_digest",
                    "recovery_input_digest", "worker", "bounds",
                    "work", "binding", "ending", "exclusion", "control",
                    "readiness", "gate", "admitted_at")


def _operation_id(kind, name):
    boundaries.identity(name, "an operation operand")
    return f"{kind}:{name}"


def decision_operation_id(decision_id):
    return _operation_id(DECISION_KIND, decision_id)


def held_operation_id(decision_id):
    return _operation_id(HELD_KIND, decision_id)


def _committed(store, kind, operation_id, members, *, named=None, value=None):
    """One committed record of this store's journal, PROVED to be the one
    asked for. `retained_recovery._committed`'s rule: a signature is not
    ownership, so a well-made record of another decision copied to this
    identity does not read as this one's."""
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
    return _records_of(store, DECISION_KIND, DECISION_MEMBERS)


def decisions_for(store, job_id):
    boundaries.identity(job_id, "a Job id")
    return [one for one in decisions_of(store) if one["job_id"] == job_id]


def held_admission_of(store, decision_id):
    return _committed(store, HELD_KIND, held_operation_id(decision_id),
                      HELD_MEMBERS, named="decision_id", value=decision_id)


def held_admissions_of(store):
    return _records_of(store, HELD_KIND, HELD_MEMBERS)


def intent_operation_id(decision_id):
    return _operation_id(INTENT_KIND, decision_id)


def ending_operation_id(decision_id):
    return _operation_id(ENDING_KIND, decision_id)


def admit_operation_id(decision_id):
    return _operation_id(ADMITTED_KIND, decision_id)


def intent_of(store, decision_id):
    return _committed(store, INTENT_KIND, intent_operation_id(decision_id),
                      INTENT_MEMBERS, named="decision_id", value=decision_id)


def intents_of(store):
    return _records_of(store, INTENT_KIND, INTENT_MEMBERS)


def ending_of(store, decision_id):
    return _committed(store, ENDING_KIND, ending_operation_id(decision_id),
                      ENDING_MEMBERS, named="decision_id", value=decision_id)


def admission_of(store, decision_id):
    return _committed(store, ADMITTED_KIND, admit_operation_id(decision_id),
                      ADMITTED_MEMBERS, named="decision_id",
                      value=decision_id)


def admissions_of(store):
    return _records_of(store, ADMITTED_KIND, ADMITTED_MEMBERS)


def admission_for(store, job_id):
    """The committed admission of ONE recovery Job, or None.

    BY THE JOB IT ADMITTED rather than by the decision that authorized it,
    because every consumer downstream of the admission -- the scheduler's
    independence exclusion, the execution pass, the review gate -- holds a
    stage and therefore a Job, and deriving a decision id back out of a Job
    name would be those consumers re-implementing an identity this record
    already carries.
    """
    boundaries.identity(job_id, "a Job id")
    found = [one for one in admissions_of(store) if one["job_id"] == job_id]
    return found[0] if len(found) == 1 else None


def prior_job_in(connection, job_id):
    """The FAILED Job whose output recovery Job `job_id` publishes, or None.

    A CONNECTION-LEVEL READ because its one caller is `scheduler._exclusions`,
    which runs inside another owner's write transaction and has no store
    handle. The answer comes from the committed admission or, before the
    submission commits, from the reservation -- both of which carry the
    lineage. An ordinary Job matches neither and answers None.
    """
    boundaries.identity(job_id, "a Job id")
    for kind in (ADMITTED_KIND, INTENT_KIND):
        for row in connection.execute(
                "SELECT result FROM operations WHERE kind = ? AND state = "
                "'committed' AND result IS NOT NULL ORDER BY operation_id",
                (kind,)):
            record = json.loads(row["result"])
            if type(record) is dict and record.get("job_id") == job_id:
                return record.get("prior_job_id")
    return None


def publication_input_of(store, job_id):
    """THE INPUT IDENTITY ONE RECOVERY'S PUBLICATION STAGE IS SERVED UNDER,
    or `None` for a Job that is not a publication recovery. A read.

    THE TYPED PUBLICATION PRODUCER EDGE (contract section 5: "the /4 binding
    adds exact recovery input and publication worker/profile"). A recovery Job
    has two stages served by two different kinds of worker:

      its REVIEW stage is served by the Work's ordinarily configured
        reviewer, under the ORIGINAL Job's own input identity -- the task,
        the Work and the declarations that reviewer already carries -- which
        is therefore what the recovery Job itself is submitted under; and
      its PUBLICATION stage is served by the installed deterministic
        publisher, under that publisher's declarations bound to this
        recovery's Work and original task. That identity is this record's.

    One Job row cannot carry both, and neither lane's comparison is relaxed
    to make it look as though it did: each stage is held, whole, to the
    identity that is its own. The answer is the reservation's or the
    committed admission's, fixed when the recovery identity was taken.
    """
    boundaries.identity(job_id, "a Job id")
    for record in list(admissions_of(store)) + list(intents_of(store)):
        if record["job_id"] == job_id:
            return record["input_digest"]
    return None


def stage_job(store, stage, job):
    """THE JOB AS ONE STAGE IS HELD TO IT: `job` itself for every stage but a
    recovery's publication stage, and for that one the same Job with the
    publication stage's own input identity.

    ONE RULE, ASKED BY EVERY READER THAT COMPARES A STAGE WITH ITS JOB'S
    INPUT -- the scheduler's offer binding, the deployment's selector and the
    publication capacity -- so the three cannot hold one stage to two
    identities. Nothing is relaxed: the comparison each of them then makes is
    the one it always made.
    """
    if job is None or stage.get("kind") != PUBLICATION_STAGE:
        return job
    expected = publication_input_of(store, stage["job_id"])
    return job if expected is None else dict(job, input_digest=expected)


def prior_job_of(store, job_id):
    """`prior_job_in`, for a caller that holds the store. A read.

    WHAT THE SERVING COMPOSITION ASKS (review 2026-11-23T18-55-03Z R3). A
    recovery Job has no task of its own: the task its stages are served under
    is the ORIGINAL Job's, and `single_worker.job_task_reader` reaches it
    through this lineage exactly as `creation.job_task_of` reaches a retried
    Job's through `fresh_attempts`. The record is the reservation or the
    committed admission, so the answer exists from the moment the recovery
    identity is spoken for and never moves afterwards.
    """
    return prior_job_in(store._connection, job_id)


# -- 8. the derived identities -----------------------------------------------

def recovery_job_id(decision_id):
    """The recovery Job identity, DERIVED from the owner's decision key.

    DERIVED RATHER THAN ALLOCATED, `retained_recovery.successor_job_id`'s rule
    and its reason: an admission that asked a counter for an identity would
    mint a second one after a crash. In THIS checkpoint it is derived and
    REPORTED and nothing is reserved under it -- the held admission says
    `reserved: False` in so many words -- so an operator reading a Job id here
    is reading the name a later admission will use rather than a Job that
    exists.
    """
    boundaries.identity(decision_id, "an owner decision id")
    return f"publication-{decision_id}"


def recovery_submission_id(decision_id):
    return f"sub-{recovery_job_id(decision_id)}"


# WHAT IS DELIBERATELY NOT DERIVED HERE: THE PUBLICATION ATTEMPT'S IDENTITY.
# Checkpoint 1 derived one and reported it, which was harmless while nothing
# executed and is a FABRICATED FACT now that something does. A stage episode's
# offer and attempt identities are derived by `episodes.identities` in the
# AUTHORITY's own namespace when the episode opens, so a name composed here
# would not be the attempt a claim produced -- and a durable admission record
# carrying it would bind the handoff to an execution that does not exist.
# `publication_execution` reads the live episode instead.


def review_stage_id(decision_id):
    return documents.stage_id(recovery_job_id(decision_id), REVIEW_STAGE)


def publication_stage_id(decision_id):
    return documents.stage_id(recovery_job_id(decision_id), PUBLICATION_STAGE)


# -- 8b. the approved recovery input, as a document --------------------------
#
# W385695 checkpoint 2. WHAT THE PUBLICATION STAGE IS ADMITTED AGAINST, and
# why it is a document rather than a path.
#
# The bytes a recovery publishes are staged into a recovery-owned input root
# AFTER the fresh claim and the host exclusion -- the contract fixes that
# order, because staging before a claim would be this manager copying an
# original for an execution nobody authorized. So at ADMISSION there is no
# staged tree to digest, and a Job's `input_digest` must still be an exact
# fact about what it will consume. This is that fact: the ORIGINAL root and
# attempt, the measured tree digest and byte count, the candidate, the owner
# decision and the exact selection it bound, and the two declarations the
# publication writes under. The staged payload is compared against THIS
# before anything launches, which is "content is compared with the approved
# selection before launch" in one document.
#
# IT CARRIES NO PATH, NO LOCATOR AND NO BYTES. A locator would make an
# operator-supplied directory an operand of the trust root, which is the one
# thing REC-9 refuses outright; the only door to the original is the host
# owner's own `output_of`, resolved from the attempt.
RECOVERY_INPUT_SCHEMA = "baton.v12.output-publication-input/1"
RECOVERY_INPUT_MEMBERS = ("schema", "decision_id", "attempt_id", "job_id",
                          "stage_id", "episode", "root_identity",
                          "tree_digest", "total_bytes", "entry_count",
                          "candidate", "producer", "selection_digest",
                          "declaration", "provenance", "delivery")


def recovery_input(decision, selection):
    """The exact recovery input one approved decision admits.

    COMPOSED FROM THE DECISION AND THE READ IT WAS TAKEN ON, both of which
    this manager holds, and from nothing a caller supplies. Deterministic: two
    incarnations composing it from the same committed decision and the same
    unchanged original derive the same document and therefore the same digest,
    which is what makes the submission replayable.
    """
    expected = decision["expected"]
    return {"schema": RECOVERY_INPUT_SCHEMA,
            "decision_id": decision["decision_id"],
            "attempt_id": decision["attempt_id"],
            "job_id": decision["job_id"], "stage_id": decision["stage_id"],
            "episode": decision["episode"],
            "root_identity": selection["output"]["root_identity"],
            "tree_digest": expected["output_tree_digest"],
            "total_bytes": expected["output_total_bytes"],
            "entry_count": selection["output"]["entry_count"],
            "candidate": {"base": expected["candidate_base"],
                          "head": expected["candidate_head"]},
            # THE PRODUCER'S OWN ACCOUNT TRAVELS, AND SAYS WHAT IT IS. The
            # publication stage does not run this command and the reviewer
            # still owes its own; what the input carries is the attribution,
            # so a reader of the staged manifest can see whose evidence it is.
            "producer": {"argv": list(expected["producer_argv"]),
                         "status": expected["producer_status"],
                         "context_digest":
                             expected["verification_context_digest"],
                         "qualification": "producer-evidence",
                         "independent_acceptance": False},
            "selection_digest": expected["selection_digest"],
            "declaration": decision["declaration_digest"],
            "provenance": dict(decision["provenance"]),
            # HOW IT IS DELIVERED, in the document the Job is admitted on, so
            # a worker cannot be handed a writable original by a deployment
            # that composed the root differently than the owner approved.
            "delivery": "read-only"}


def recovery_input_digest(document):
    missing = [one for one in RECOVERY_INPUT_MEMBERS if one not in document]
    if missing:                                           # pragma: no cover
        _refuse(f"a recovery input declaration carries "
                f"{', '.join(RECOVERY_INPUT_MEMBERS)}; this one has no "
                f"{', '.join(missing)}", category="integrity", code="schema")
    return digest({one: document[one] for one in RECOVERY_INPUT_MEMBERS})


# -- 9. the owner decision ---------------------------------------------------

def decide(jobs, control, *, job_id, stage_id, episode, decision_id,
           disposition, authorization, expected, profile, profile_digest,
           stages, declaration_digest, host, exclusion, source, now=None):
    """Record ONE owner disposition on one retained output publication
    failure.

    EVERY COMPARISON BEFORE THE WRITE, AND THE READ IS TAKEN AGAIN HERE. The
    owner is approving an inspection they read a moment ago; this operation
    performs the SAME inspection, from the same selectors, through the same
    owners, and holds the owner's operands against it. So evidence that moved
    under the owner -- the original replaced, a writer that came back, a
    candidate that stopped corresponding -- is refused rather than decided
    about, and an owner who approved exactly what they were shown cannot be
    refused for a transcription.

    A DISPOSITION IS NOT AN ADMISSION. This launches nothing, even for
    `approved`: `admit_publication` is a separate act with its own identity,
    its own owner ports and its own prerequisite evaluation, so a crash
    between them leaves a decision that can be carried out rather than an
    effect nobody decided.

    A HOLD AND A DENIAL ARE DECIDED ON THE SAME EVIDENCE AS AN APPROVAL, and
    that is deliberate. An owner parking or refusing a recovery is recording
    an attributable act about a specific state of the world, and a hold taken
    against evidence nobody checked would be a decision about nothing.
    """
    boundaries.identity(decision_id, "an owner decision id")
    if disposition not in DISPOSITIONS:
        _refuse(f"an owner disposition is one of {', '.join(DISPOSITIONS)}; "
                f"this is {name_value(disposition)}",
                category="integrity", code="schema")
    decided_at = boundaries.instant(now if now is not None else jobs._now(),
                                    "an owner decision instant")
    taken = _expected(expected)
    selected = owned_stages(stages)
    # WHO IS DECIDING, BEFORE ANY DIGEST IS COMPARED. Everything around it is
    # a pure read, so the order changes no effect -- what it changes is the
    # sentence an unauthorized caller is given.
    failed = _failed_publication(jobs, control, job_id=job_id,
                                 stage_id=stage_id, episode=episode)
    owner = _owner(authorization, failed["work_id"],
                   what="the owner authorization port")
    policy = resolved_profile(boundaries.text(profile,
                                              "the approved profile identity"))
    if boundaries.text(profile_digest,
                       "the approved profile digest") != policy["digest"]:
        _refuse(f"the decision names profile digest "
                f"{name_value(profile_digest)} and {name_value(profile)} "
                f"digests to {name_value(policy['digest'])}; the owner's "
                f"decision names the profile and admission checks exact "
                f"agreement", category="integrity", code="digest")
    held = corrective_declaration()
    if boundaries.text(declaration_digest,
                       "the approved output declaration digest") \
            != held["digest"]:
        _refuse(f"the decision names output declaration "
                f"{name_value(declaration_digest)} and the selected "
                f"{name_value(held['descriptor'])} digests to "
                f"{name_value(held['digest'])}; the corrective output "
                f"declaration is the exact revision W385694 published",
                category="integrity", code="digest")

    # -- the evidence AS IT STANDS NOW, through every owner that holds it.
    selection = inspect(jobs, control, job_id=job_id, stage_id=stage_id,
                        episode=episode, host=host, exclusion=exclusion,
                        source=source)
    if selection["holds"]:
        first = selection["holds"][0]
        _refuse(f"this publication recovery is held and is not decided about: "
                f"{first['category']}/{first['code']}: {first['message']}"
                + (f" (and {len(selection['holds']) - 1} further hold"
                   f"{'s' if len(selection['holds']) > 2 else ''})"
                   if len(selection["holds"]) > 1 else ""),
                category=first["category"], code=first["code"])
    wanted = expected_facts(selection)
    for member in EXPECTED_MEMBERS:
        if taken[member] != wanted[member]:
            _refuse(f"this decision expects {member} "
                    f"{name_value(json.dumps(taken[member]))} and the "
                    f"inspection of Job {name_value(job_id)} now reports "
                    f"{name_value(json.dumps(wanted[member]))}; an owner "
                    f"decides on the exact execution, output, candidate and "
                    f"producer attribution they actually read",
                    category="integrity", code="digest")

    if disposition == APPROVED:
        # A CANCELLED JOB IS NEVER REVIVED, and an approval of one would be a
        # decision nothing may carry out. An EXPIRY is deliberately not a
        # refusal: REC-9 keeps old clocks unchanged and gives the recovery its
        # own admission and its own limits.
        _refuse_cancelled(jobs._connection, job_id,
                          "an approved publication recovery decision")
        job_control.refuse_uncertain(jobs._connection, job_id,
                                     "a publication recovery decision about "
                                     "it", now=decided_at)

    record = {"job_id": job_id, "stage_id": stage_id, "episode": episode,
              "attempt_id": failed["attempt_id"], "decision_id": decision_id,
              "disposition": disposition, "owner": owner,
              "work_id": failed["work_id"], "expected": taken,
              "declaration_digest": held["digest"],
              "profile": policy["profile"], "profile_digest": policy["digest"],
              "stages": list(selected), "provenance": dict(PROVENANCE),
              "decided_at": decided_at}
    # THE REPLAY IDENTITY IS THE DECISION AND NOT THE CLOCK THAT TOOK IT.
    # `retained_recovery.decide`'s split, for its reason: the committed record
    # carries the instant and the resolved authorization, and the SIGNATURE
    # carries the facts that make this the same decision -- so an exact retry
    # replays the committed bytes rather than being re-authorized against
    # today's policy, which is what effectively-once means for an act that
    # already happened.
    operands = {name: record[name] for name in DECISION_MEMBERS
                if name not in ("decided_at", "owner")}
    operands["endpoint"] = owner["endpoint"]
    operands["principal"] = owner["principal"]
    operands["effective_scope"] = owner["effective_scope"]

    def act(connection):
        if disposition == APPROVED:
            # THE PER-EXECUTION FENCE, DECIDED UNDER THE SAME WRITE LOCK as
            # the record, so two concurrent owner decisions meet at a fence
            # rather than at a read.
            _fenced_decision(connection, jobs, failed["attempt_id"],
                             decision_id)
            _refuse_cancelled(connection, job_id,
                              "an approved publication recovery decision")
        return record

    return jobs.transact(decision_operation_id(decision_id), DECISION_KIND,
                         job_signature(DECISION_KIND, operands), act)


def _refuse_cancelled(connection, job_id, what):
    """An EXPLICIT cancellation refuses; a reached deadline does not.

    `retained_recovery._refuse_cancelled`'s rule, for its reason: a retained
    output is ordinarily decided about well after the Job that produced it
    reached its own wall, so refusing on expiry would make the capability
    unreachable in its commonest case -- while refusing on a cancellation is
    the ruling.
    """
    held = cancellation.fenced(connection, job_id)
    if held is not None and held.get("trigger", "operator") == "operator":
        _refuse(f"Job {name_value(job_id)} was cancelled at "
                f"{held['requested_at']} ({held['reason']}); {what} is not "
                f"recorded after an explicit cancellation, and a cancelled "
                f"execution is never revived")
    return held


def _fenced_decision(connection, store, attempt_id, decision_id):
    """At most one APPROVED publication recovery per failed execution.

    ONE RETAINED OUTPUT IS PUBLISHED ONCE. A second approval of one attempt
    would authorize a second adoption of one set of bytes under two
    identities, which is the duplicate effect REC-9's admission fence exists
    to prevent. A later disposition of the same failure is a NEW decision
    identity, and it is refused HERE rather than at the admission, because by
    then the first decision may already hold a prerequisite nothing can undo.
    """
    for one in decisions_of(store):
        if one["attempt_id"] != attempt_id \
                or one["decision_id"] == decision_id \
                or one["disposition"] != APPROVED:
            continue
        _denied(f"attempt {name_value(attempt_id)}'s retained output is "
                f"already approved for publication under decision "
                f"{name_value(one['decision_id'])}; one failed publication "
                f"has one approved recovery, and a further disposition is a "
                f"new owner decision on new evidence rather than a second "
                f"approval of this one")
    return None


# -- 10. the admission boundary ----------------------------------------------
#
# WHAT AN ACTUAL ADMISSION WOULD NEED, evaluated against this build and this
# deployment rather than asserted. Each entry names the capability, the owner
# that holds it and the exact fact that decides it, and `prerequisites` reads
# them all so the answer is a LIST of what is owed rather than whichever one
# the control flow reached first.
#
# FOUR OF THE FIVE ARE FACTS ABOUT THIS BUILD, and that is why no port can
# talk this boundary into opening. A deployment that answers "yes, I have a
# publication worker" is answering about a stage kind, a lane, a store
# generation and a control profile this build must ALSO hold; checkpoint 2
# installed all four, so the deployment's answer is now the one that decides,
# and a build that was rolled back answers `False` for its own four again
# without one line of this module changing.
PREREQUISITES = (
    {"name": "publication-stage-vocabulary",
     "owner": "the Job submission document owner",
     "needs": f"{RECOVERY_SUBMISSION} admitting a {PUBLICATION_STAGE} stage",
     "checkpoint": 2},
    {"name": "publication-lane",
     "owner": "the Job scheduler and its pool revision",
     "needs": f"{RECOVERY_POOL} mapping {PUBLICATION_STAGE} to its own lane",
     "checkpoint": 2},
    {"name": "job-store-generation",
     "owner": "the Job store schema",
     "needs": f"generation {RECOVERY_STORE_GENERATION}",
     "checkpoint": 2},
    {"name": "publication-worker",
     "owner": "the deployment binding",
     "needs": "an installed deterministic publication worker and profile",
     "checkpoint": 2},
    {"name": "publication-control-profile",
     "owner": "the Job control owner",
     "needs": f"an enforced {PUBLICATION_PROFILE} entry carrying the "
              f"publication sub-bound",
     "checkpoint": 2},
)


def prerequisites(store, *, worker=None):
    """WHICH CAPABILITIES AN ACTUAL ADMISSION IS STILL MISSING, from the
    owners that hold them.

    THE HONEST ANSWER IS A LIST AND NOT A BOOLEAN, and every entry is read
    from the module or the owner that carries the fact rather than from a
    flag. Checkpoint 2 installed this build's four -- the `/4` generation, the
    publication lane under `baton.v12.worker-pool/2`, store generation 10 and
    the enforced control profile -- so the day one of them is absent again
    (an un-migrated store, a build rolled back) the answer changes by itself.

    `worker` IS THE DEPLOYMENT'S OWN ANSWER, resolved by the caller through
    the binding port and passed in rather than fetched here, because this
    function is also a pure read a status command calls with no ports at all.
    `None` means nobody asked, and `None` is not availability: a prerequisite
    nobody asked about is reported as missing, with `not asked` in its own
    observation, which is the checkpoint-1 behaviour and the honest one.

    THE LANE CHECK IS STILL THE ONE WORTH READING TWICE. What makes it
    available is not the word `publication` appearing in a tuple: it is
    `scheduler.lane_of` answering the publication lane FOR a publication
    stage, which is the routing decision itself, asked here of the function
    that makes it.
    """
    lane = None
    try:
        lane = scheduler.lane_of(PUBLICATION_STAGE)
    except ContractRefusal:                               # pragma: no cover
        lane = None
    available = {
        "publication-stage-vocabulary": (
            PUBLICATION_STAGE in documents.STAGE_KINDS
            and RECOVERY_SUBMISSION in documents.SUBMISSION_SCHEMAS
            and documents.RECOVERY_STAGES == SELECTED_STAGES),
        "publication-lane": (lane == PUBLICATION_LANE
                             and PUBLICATION_LANE in scheduler.LANES
                             and scheduler.POOL_SCHEMA == RECOVERY_POOL),
        "job-store-generation": (schema.SCHEMA_VERSION
                                 >= RECOVERY_STORE_GENERATION
                                 and store.schema_version
                                 >= RECOVERY_STORE_GENERATION),
        # THE DEPLOYMENT'S OWN FACT, and the only one of the five that is.
        "publication-worker": worker is not None,
        "publication-control-profile": (
            PUBLICATION_PROFILE in job_control.PROFILES
            and job_control.sub_bound_of(
                PUBLICATION_PROFILE, PUBLICATION_STAGE)
            == SELECTED_PUBLICATION_SECONDS),
    }
    held = []
    for entry in PREREQUISITES:
        held.append({**entry, "available": bool(available[entry["name"]]),
                     "observed": _observed(entry["name"], store=store,
                                           lane=lane, worker=worker)})
    return held


def _observed(name, *, store=None, lane=None, worker=None):
    """The exact current fact behind one prerequisite, in its owner's words."""
    if name == "publication-stage-vocabulary":
        return (f"this build's stage vocabulary is "
                f"{', '.join(documents.STAGE_KINDS)} and its submission "
                f"generations are {', '.join(documents.SUBMISSION_SCHEMAS)}")
    if name == "publication-lane":
        return (f"this build's lanes are {', '.join(scheduler.LANES)} under "
                f"{scheduler.POOL_SCHEMA}, and its stage-to-lane map sends a "
                f"{PUBLICATION_STAGE} stage to {name_value(lane)}")
    if name == "job-store-generation":
        return (f"this build's Job schema generation is "
                f"{schema.SCHEMA_VERSION}"
                + (f" and this store is at {store.schema_version}"
                   if store is not None else ""))
    if name == "publication-worker":
        if worker is None:
            return ("not asked: no deployment binding port answered for an "
                    "installed publication worker")
        return (f"this deployment installs publication worker "
                f"{worker['worker_id']} as {worker['participant']} under "
                f"profile {worker['profile_name']}/{worker['profile_digest']}")
    return (f"this build's enforced control profiles are "
            f"{', '.join(sorted(job_control.PROFILES))} and "
            f"{PUBLICATION_PROFILE} bounds a {PUBLICATION_STAGE} stage at "
            f"{name_value(job_control.sub_bound_of(PUBLICATION_PROFILE, PUBLICATION_STAGE))}"
            f" seconds")


GATE_UNAVAILABLE = "publication-custody-handoff-unavailable"
GATE_REASONS = (GATE_UNAVAILABLE,)


def execution_gate(store, decision_id):
    """THE REVIEW GATE OF ONE APPROVED PUBLICATION RECOVERY, and it is CLOSED.

    REC-9: "Review MUST remain non-runnable until attributable publication
    custody and the exact candidate handoff are validated". In this checkpoint
    there is no publication execution, so there is no custody, no intake
    receipt and no candidate handoff -- and the gate says exactly that, with
    the decision and the candidate it is about, read off the durable held
    admission rather than off a live process's memory so every incarnation
    answers the same thing.

    THERE IS NO SWITCH HERE THAT OPENS IT. `open` is a constant `False` in
    this slice, which is the point: an approval, a qualified producer result,
    a candidate digest or an operator's journalled account cannot open a gate,
    and the only thing that will is checkpoint 2's validated handoff.
    """
    boundaries.identity(decision_id, "an owner decision id")
    held = held_admission_of(store, decision_id)
    if held is None:
        return None
    return documents.publication_gate(
        job_id=held["job_id"], open=False, reason=GATE_UNAVAILABLE,
        decision_id=decision_id, prior_job_id=held["prior_job_id"],
        candidate=held["candidate"], runnable=False,
        prerequisites=[one["name"] for one in held["prerequisites"]
                       if not one["available"]])

def admission_readiness(record):
    """WHICH ACT IS OWED NEXT, said out loud rather than implied.

    TWO SHAPES BECAUSE THERE ARE TWO OUTCOMES, and neither of them is
    "recovered". A HELD admission performed nothing: no Job, no binding, no
    reservation, no offer, and it says so in the words checkpoint 1 wrote. An
    ADMITTED one reserved an identity, ended the prior assignment, bound the
    Job and recorded one `/4` submission -- and it still published nothing,
    took no custody and opened no gate, because the deterministic adoption of
    the retained bytes is `publication_execution`'s and the review gate is
    shut until that module's handoff commits.

    AN ANSWER THAT MERELY REPORTED A JOB ID WOULD READ AS A RECOVERY THAT
    HAPPENED, which is the false success REC-9 exists to prevent -- so this
    names the owner of every act still owed, in both shapes.
    """
    if record.get("state") == "admitted":
        return {
            "admission": "admitted",
            "publication": "queued",
            "review": "blocked",
            "offers": 0,
            "owed_by": "the deterministic publication worker, through the "
                       "ordinary serving tick",
            "detail": "this admission reserved the recovery Job identity, "
                      "ended the prior assignment on the reused Work through "
                      "the Authority's own transition, bound the Job and "
                      "recorded one publication/review submission under the "
                      "approved finite profile. NOTHING HAS BEEN PUBLISHED: "
                      "no original byte has been staged, no publication "
                      "attempt has been claimed, no result is frozen, no "
                      "custody exists and the review gate is shut. The "
                      "original Job remains failed and its retained output is "
                      "unchanged"}
    return {
        "admission": "held",
        "publication": "unavailable",
        "review": "blocked",
        "offers": 0,
        "owed_by": "the capabilities this deployment or this store is "
                   "missing, named one by one in `prerequisites`",
        "detail": "this checkpoint inspected the original output through its "
                  "host owner, recorded the owner's exact decision and "
                  "composed the admission's owners; it reserved no Job "
                  "identity, bound no Work, submitted no document and issued "
                  "no offer, because a capability an admission needs is not "
                  "installed on this instance. The original Job remains "
                  "failed and its retained output is unchanged"}


# -- 11. the two ports a real admission adds ---------------------------------
#
# W385695 checkpoint 2. THE DEPLOYMENT BINDING grows one member and the
# ASSIGNMENT ENDING is new.
#
# `publication_worker` is the deployment's own answer about the installed
# deterministic publication worker -- its participant, its lane and the
# profile a publication stage must name to be selectable. It is a port member
# rather than a lookup in this module because WHICH worker serves a lane is
# deployment configuration: a manager that chose one would be configuring the
# instance it is supposed to be reading. A deployment that answers `None` has
# installed none, and that REFUSES the admission; it is never worked around by
# submitting the stage under some other lane's profile.
#
# `PRIOR_ASSIGNMENT` is the supported ending path, and it is deliberately
# narrow. The Authority's `end` is a COMPARE-AND-SWAP on an exact assignment,
# performed through a session bound to the participant that HOLDS it -- which
# is why this is a port the deployment composes from the session it already
# mints for that worker, and not a capability this module could hold. There is
# no new recovery-only takeover power here and none was selected: this module
# cannot end an assignment it cannot name exactly, cannot end one belonging to
# another handler, and cannot reach the Authority any other way.
PUBLICATION_BINDING = ("instance", "binding_of", "bind", "serving",
                       "publication_worker", "publication_input")
PRIOR_ASSIGNMENT = ("instance", "assignment_of", "end")
WORKER_MEMBERS = ("worker_id", "participant", "lane", "profile_name",
                  "profile_digest", "eligible_kinds", "input_digest")
# The two dispositions the Authority's own release transition carries, read
# from the owner that defines them rather than respelled. `recovered` is the
# one a manager uses when it is reconciling an assignment whose holder is
# gone; `release` is an ordinary hand-back.
ENDING_DISPOSITION = "recovered"
ENDING_CAUSES = ("release", "recovered")
# What this module records having done about the prior assignment. `none` is
# a real outcome and not a skipped step: a Work whose claim was already
# released has nothing to end, and saying so is different from saying an
# ending was performed.
ENDING_OUTCOMES = ("ended", "none")


def _installed_worker(binding):
    """The deployment's installed deterministic publication worker, or refuse.

    PROVED TO BE A PUBLICATION WORKER rather than merely present. Its lane is
    the publication lane, it is eligible for the publication stage kind and
    nothing else, and it carries a profile a stage can name. A deployment that
    answered with its implementation worker would otherwise install the
    provider-backed producer as the publisher -- which is the one thing the
    separately selected deterministic worker exists to prevent.
    """
    _port(binding, PUBLICATION_BINDING, what="the deployment binding port")
    held = binding.publication_worker()
    if held is None:
        _refuse(f"this deployment installs no deterministic "
                f"{PUBLICATION_STAGE} worker; a publication recovery is "
                f"served by the separately selected publication lane and is "
                f"never routed to the workers that run implementations. "
                f"Install the {RECOVERY_POOL} publication worker once, as "
                f"part of the deployment, and admit this decision again",
                category="refused", code="capability")
    taken = boundaries.document(held, "the installed publication worker",
                                required=WORKER_MEMBERS)
    boundaries.identity(taken["worker_id"], "a publication worker id")
    boundaries.text(taken["participant"], "a publication worker participant")
    boundaries.text(taken["profile_name"], "a publication worker profile name")
    boundaries.text(taken["profile_digest"],
                    "a publication worker profile digest")
    # THE INSTALLED WORKER'S OWN INPUT MANIFEST IDENTITY, which is what the
    # recovery Job must be SUBMITTED under. `delegation.stage_intent` carries
    # the Job's `input_digest` into the offer and `check_binding` refuses an
    # offer whose intent names another -- so a Job submitted under anything
    # else is a Job this deployment's own worker could never be offered.
    #
    # IT IS THE DEPLOYMENT'S FACT AND NOT THIS MODULE'S. The approved recovery
    # INPUT -- the original root, its measured digest and the owner decision --
    # is a separate document the admission binds and the staging compares; it
    # is not the worker-contract manifest an offer is made against, and
    # conflating the two is what made that refusal fire.
    boundaries.text(taken["input_digest"],
                    "a publication worker input manifest digest")
    if taken["lane"] != PUBLICATION_LANE:
        _refuse(f"this deployment's {name_value(taken['worker_id'])} is in "
                f"lane {name_value(taken['lane'])} and a publication stage is "
                f"allocated in {name_value(PUBLICATION_LANE)}; lanes are "
                f"immutable and a worker in another lane cannot serve this "
                f"stage", category="integrity", code="schema")
    kinds = taken["eligible_kinds"]
    if type(kinds) not in (list, tuple) \
            or tuple(sorted(kinds)) != (PUBLICATION_STAGE,):
        _denied(f"this deployment's {name_value(taken['worker_id'])} declares "
                f"eligible kinds {sample_of(sorted(kinds) if type(kinds) in (list, tuple) else [])} "
                f"and a deterministic publication worker serves exactly "
                f"{name_value(PUBLICATION_STAGE)}; a worker that could also "
                f"take an implementation stage is not the no-provider "
                f"capacity this recovery reserves")
    return {name: (list(taken[name]) if name == "eligible_kinds"
                   else taken[name]) for name in WORKER_MEMBERS}


def _prior(jobs, decision):
    """The failed Job's own specification, and the reviewer profile it reuses.

    THE SUBMITTED DOCUMENT IS THE SPECIFICATION, `retained_recovery._prior`'s
    rule: rebuilding an entry out of rows would silently normalize it. What a
    recovery carries forward is narrow on purpose -- the policy digest, the
    test scope, the terminal policy and the REVIEW stage's own profile --
    because those are what make the configured reviewer able to serve the
    recovery without per-recovery installation.

    AND THE INPUT IDENTITY IS CARRIED FORWARD FOR THE JOB, BUT NOT FOR ITS
    PUBLICATION STAGE (COMPLETION-PLAN-385909 outcome 4). The first cut
    carried none of it, on the ground that a publication consumes the approved
    retained output and not the producer's task -- which is true of the
    PUBLICATION stage and remains so: that stage is held to its own identity,
    `publication_input_of`. It is not true of the REVIEW stage, which judges
    the candidate against the task, the Work and the declarations the
    original Job was admitted under, and which the ordinarily configured
    reviewer can only serve under that Job's own identity. Submitting the
    recovery under anything else left a review stage no production reviewer
    could be selected for.
    """
    job_id = decision["job_id"]
    held = submission.job_of(jobs, job_id)
    if held is None:                                      # pragma: no cover
        _refuse(f"this store holds no Job {name_value(job_id)}")
    recorded = submission.submission_of(jobs, held["submission_id"])
    if recorded is None:
        _refuse(f"Job {name_value(job_id)} names submission "
                f"{name_value(held['submission_id'])} and this store holds no "
                f"such submission; the specification a recovery reuses is "
                f"that document's")
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
        _refuse(f"Job {name_value(job_id)} carries no "
                f"{name_value(REVIEW_STAGE)} stage; its recovery hands the "
                f"published candidate to the independent review this "
                f"deployment already configures for it, and there is no "
                f"configured profile here to reuse")
    works = {one["work_id"] for one in submission.stages_of(jobs, job_id)}
    if works != {decision["work_id"]}:
        _refuse(f"Job {name_value(job_id)}'s stages name "
                f"{sample_of(sorted(works))} and the owner decided in "
                f"{name_value(decision['work_id'])}; a recovery inherits one "
                f"Work and this build cannot choose between them",
                category="integrity", code="schema")
    return {"job_id": job_id, "entry": entry, "review": review,
            "submission_id": held["submission_id"],
            "work_id": decision["work_id"]}


def _composed(prior, decision, *, job_id, submission_id, worker,
              input_digest):
    """THE RECOVERY JOB'S OWN `/4` SPECIFICATION, and look at what is in it.

    ONE PUBLICATION STAGE AND ONE REVIEW STAGE GATED ON IT, on the original
    open Work, under the owner-approved finite profile. No implementation to
    redispatch, no verification stage to repeat the producer's own command
    with, no integration. The publication stage names the INSTALLED
    deterministic worker's profile, which is what makes it selectable in the
    publication lane and unselectable by anything else; the review stage names
    the profile the failed Job's own review was configured with, which is what
    makes the configured reviewer able to serve it.

    THE EXECUTION LIMITS ARE OMITTED ON PURPOSE, `retained_recovery._composed`'s
    reason: the approved profile pins the provider invocation at 3600 s and
    each verification command at 900 s, and those are this build's runner
    defaults -- `job_control.agreeing` proves the agreement at submit either
    way, and stating them again would be a second account of two ceilings the
    profile already owns.
    """
    entry = {"job_id": job_id,
             "input_digest": input_digest,
             "policy_digest": prior["entry"]["policy_digest"],
             "test_scope": list(prior["entry"]["test_scope"]),
             "terminal_policy": prior["entry"]["terminal_policy"],
             "control": {"profile": PUBLICATION_PROFILE},
             "stages": [
                 {"kind": PUBLICATION_STAGE, "work_id": prior["work_id"],
                  "profile_name": worker["profile_name"],
                  "profile_digest": worker["profile_digest"],
                  "depends_on": []},
                 {"kind": REVIEW_STAGE, "work_id": prior["work_id"],
                  "profile_name": prior["review"]["profile_name"],
                  "profile_digest": prior["review"]["profile_digest"],
                  "depends_on": [{"job_id": job_id,
                                  "kind": PUBLICATION_STAGE}]}]}
    return documents.owned_submission(
        {"schema": documents.SUBMISSION_RECOVERY_SCHEMA,
         "submission_id": submission_id, "jobs": [entry]})


def _incomplete(why, *, reserved):
    """A refusal AFTER the reservation, which says so.

    `retained_recovery._incomplete`'s correction in this operation's words: a
    reserved identity with no Job is a real, recorded, resumable state, and an
    operator told "nothing happened" would go looking for a row that is there.
    """
    return ContractRefusal(
        "refused", "precondition",
        f"{why}. The recovery identity {name_value(reserved)} is already "
        f"RESERVED in this store and this admission is incomplete rather than "
        f"undone: correct what is named above and run the same request again, "
        f"which resumes from the reservation. A different request under this "
        f"decision is refused as the collision it is")


def _refusing(why, reserved):
    if reserved is None:
        return ContractRefusal("refused", "precondition", why)
    return _incomplete(why, reserved=reserved)


def _reserved(jobs, operands, record, *, document, prior_job_id):
    """CUT A: the recovery identity is spoken for, durably, inside the lock.

    NOTHING OUTSIDE THIS STORE HAS BEEN TOUCHED WHEN THIS COMMITS, which is
    `fresh_attempt`'s review R4: an admission that authorized the Work first
    performed an Authority effect and then refused as a collision -- an effect
    for an operation that was never admitted. So the identity is taken here,
    and every external act below is after it and resumable.

    THE THREE TABLES THAT CAN ALREADY OWN A JOB NAME are asked, and so is the
    submission's own journal identity: an operation already settled for a
    DIFFERENT document can never record this one, and finding that out after
    ending somebody's assignment would be finding it out too late.
    """
    job_id = operands["job_id"]
    intended = job_signature("submission.record", document)

    def act(connection):
        _refuse_cancelled(connection, prior_job_id,
                          "a publication recovery admission")
        job_control.refuse_uncertain(connection, prior_job_id,
                                     "a publication recovery admission for "
                                     "it", now=jobs._now())
        taken = connection.execute(
            "SELECT job_id FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        if taken is not None:
            raise ContractRefusal(
                "refused", "precondition",
                f"Job {name_value(job_id)} is already recorded in this store "
                f"by another submission; the identity this decision's "
                f"recovery would carry names another pipeline", durable=True)
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
                    f"operation owns the identity, so a recovery taking the "
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
                f"identity. Nothing was reserved and no Work, binding or "
                f"assignment was touched")
        return record

    operands_for_signature = {name: record[name] for name in INTENT_MEMBERS
                              if name not in ("state", "bounds",
                                              "intended_at")}
    return jobs.transact(intent_operation_id(operands["decision_id"]),
                         INTENT_KIND,
                         job_signature(INTENT_KIND, operands_for_signature),
                         act)


def _expected_assignment(failed):
    """The EXACT assignment the failed execution held, in the Authority's
    shape. Not an operand anywhere on this surface: it is read off the
    attempt's own row, which is what makes an ending a compare-and-swap on one
    generation rather than a request to release whatever is there."""
    return {"work_ref": {"authority_uuid": failed["authority_uuid"],
                         "work_id": failed["work_id"]},
            "participant": failed["participant"],
            "generation": failed["generation"]}


def _ended_prior(jobs, ending, *, decision, failed, evidence, reserved,
                 now=None):
    """CUT B1: THE PRIOR ASSIGNMENT IS ENDED THROUGH THE AUTHORITY, or this
    stops before any publication effect.

    THE RULE REC-9'S CONTRACT STATES AND THE ONE THING IT FORBIDS. "Fresh
    assignments on reused Work still require the previous assignment to be
    ended/fenced through the Authority's existing exact-expect transition and
    positive host cessation" -- and "a host-only stopped-settlement receipt
    does not release the Authority claim". So the host's own cessation
    evidence is necessary and is NOT sufficient: the claim is held at the
    Authority and only the Authority's own transition releases it.

    THREE ANSWERS AND ONLY ONE OF THEM ENDS ANYTHING:

      NOTHING IS HELD. The Work's claim was already released -- by an earlier
        incarnation of this operation, by the ordinary ending path, or because
        the producer's own settlement got that far. There is nothing to end,
        `none` is recorded, and this is NOT reported as an ending performed.
      THIS EXECUTION HOLDS IT. The live assignment is exactly the failed
        attempt's participant and generation, the host says that attempt has
        CEASED and returned its resource, and the ending is performed through
        a session bound to THAT participant -- the deployment's own, because
        this module holds no session and may not impersonate one.
      SOMEBODY ELSE HOLDS IT. Another participant, or another generation of
        this one, is the live handler. That is reported with the exact held
        assignment and this stops: ending it would be taking over a claim
        nobody authorized this recovery to take, and no new recovery-only
        takeover power was selected.

    THE EARLIER ASSIGNMENT EVENTS ARE PRESERVED. The Authority appends an
    assignment event; nothing here rewrites, deletes or re-attributes one, and
    the original attempt's own rows are untouched.
    """
    _port(ending, PRIOR_ASSIGNMENT, what="the prior-assignment ending port")
    # A COMMITTED ENDING REPLAYS BEFORE THE AUTHORITY IS ASKED ANYTHING.
    # W385695 checkpoint 2: without this, a re-entry after the ending had
    # committed -- a crash before the admission record, or the serving
    # manager's own ending followed by the owner's repeated admission -- read
    # a now-released Work, composed disposition `none`, and COLLIDED with the
    # `ended` record it was replaying. The record is this operation's own
    # answer about what it did, and it is read rather than re-decided.
    recorded = ending_of(jobs, decision["decision_id"])
    if recorded is not None:
        return recorded
    work_id = failed["work_id"]
    expect = _expected_assignment(failed)
    live = ending.assignment_of(work_id)
    ended_at = boundaries.instant(now if now is not None else jobs._now(),
                                  "a prior-assignment ending instant")
    cessation = evidence.get(failed["attempt_id"]) or {}
    if live is None:
        record = {"decision_id": decision["decision_id"],
                  "job_id": recovery_job_id(decision["decision_id"]),
                  "work_id": work_id, "disposition": "none",
                  "expect": expect, "answer": None,
                  "cessation": dict(cessation), "ended_at": ended_at}
    else:
        held = boundaries.document(live, "the Work's live assignment",
                                   required=("work_ref", "participant",
                                             "generation"))
        if {"work_ref": held["work_ref"], "participant": held["participant"],
                "generation": held["generation"]} != expect:
            raise _refusing(
                f"Work {name_value(work_id)}'s live assignment is "
                f"{name_value(held['participant'])} generation "
                f"{name_value(held['generation'])} and the failed execution "
                f"this recovery is about held "
                f"{name_value(expect['participant'])} generation "
                f"{name_value(expect['generation'])}; another handler owns "
                f"this Work, and a publication recovery ends the assignment "
                f"it is about or stops. No takeover power was selected and "
                f"none is used here", reserved)
        if not cessation.get("ceased"):
            raise _refusing(
                f"the host cannot say attempt "
                f"{name_value(failed['attempt_id'])} has ceased and returned "
                f"its resource (runtime {name_value(cessation.get('runtime'))}, "
                f"cleanup {name_value(cessation.get('cleanup'))}, resource "
                f"{name_value(cessation.get('resource'))}); an assignment is "
                f"ended after POSITIVE cessation and never on the strength of "
                f"a deadline having passed", reserved)
        answer = ending.end(expect,
                            operation_id=ending_operation_id(
                                decision["decision_id"]),
                            disposition=ENDING_DISPOSITION,
                            reason=f"publication recovery "
                                   f"{decision['decision_id']}")
        taken = boundaries.document(answer, "the Authority's ending answer",
                                    required=("cause", "assignment", "phase"),
                                    optional=("gate", "fenced", "route"))
        if taken["cause"] not in ENDING_CAUSES:
            raise _refusing(
                f"the Authority answered cause "
                f"{name_value(taken['cause'])} and an assignment ending is "
                f"one of {', '.join(ENDING_CAUSES)}; a transition that did "
                f"something else is not the one this admission asked for",
                reserved)
        if taken["assignment"] != expect:
            raise _refusing(
                f"the Authority ended "
                f"{name_value(json.dumps(taken['assignment']))} and this "
                f"admission named {name_value(json.dumps(expect))}; an "
                f"ending that settled another assignment proves nothing about "
                f"this one", reserved)
        if taken["phase"] != "queued":
            raise _refusing(
                f"the Work is {name_value(taken['phase'])} after the ending "
                f"and a fresh claim needs it queued; a publication recovery "
                f"does not route, gate or reopen somebody else's Work",
                reserved)
        record = {"decision_id": decision["decision_id"],
                  "job_id": recovery_job_id(decision["decision_id"]),
                  "work_id": work_id, "disposition": "ended",
                  "expect": expect,
                  "answer": {one: taken[one] for one in
                             ("cause", "assignment", "phase")},
                  "cessation": dict(cessation), "ended_at": ended_at}
    operands = {name: record[name] for name in ENDING_MEMBERS
                if name not in ("ended_at",)}
    return jobs.transact(ending_operation_id(decision["decision_id"]),
                         ENDING_KIND, job_signature(ENDING_KIND, operands),
                         lambda connection: record)


def end_prior_assignment(jobs, control, *, decision_id, ending, exclusion,
                         now=None):
    """CUT B1 AS ITS OWN ENTRY, for the owner that actually holds the session.

    W385695 checkpoint 2. `admit_publication` performs this cut itself when
    the deployment it runs in can end the failed execution's assignment. The
    owner command's process cannot: it holds a READ-ONLY Authority and no
    participant session, and must never mint one, so its admission stops at
    this cut with the exact held assignment named. The session that CAN end
    that assignment is the producer participant's own, and the process that
    already holds it is the SERVING manager.

    So this is the same cut, entered by that manager: the same recorded
    decision, the same failed execution read through the same owners, the
    same positive host cessation, the same exact-expect transition under the
    same operation identity, and the same journalled record. Nothing is
    decided here that the admission does not decide; the admission then
    REPLAYS this record instead of asking the Authority again.

    WHAT MUST ALREADY EXIST, and each is somebody's durable act:

      an APPROVED owner decision -- an ending is never performed for a
        recovery nobody approved;
      the admission's own RESERVATION -- so an ending is performed only for a
        recovery whose admission really began and stopped here, never for a
        decision nobody has tried to admit;
      and no committed admission -- an admitted recovery ended its prior
        assignment already.

    It is not a takeover: `_ended_prior` ends exactly the failed execution's
    assignment or stops, and the port can only ask the deployment for the
    session of the participant the Authority reports as the live handler.
    """
    boundaries.identity(decision_id, "a publication decision id")
    recorded = ending_of(jobs, decision_id)
    if recorded is not None:
        return recorded
    decision = decision_of(jobs, decision_id)
    if decision is None or decision["disposition"] != APPROVED:
        _refuse(f"decision {name_value(decision_id)} is not a recorded "
                f"approval; a prior assignment is ended for an approved "
                f"publication recovery and for nothing else")
    job_id = recovery_job_id(decision_id)
    if intent_of(jobs, decision_id) is None:
        _refuse(f"recovery {name_value(job_id)} has no admission "
                f"reservation; the prior assignment is ended as part of an "
                f"admission that began, never ahead of one")
    failed = _failed_publication(jobs, control, job_id=decision["job_id"],
                                 stage_id=decision["stage_id"],
                                 episode=decision["episode"])
    evidence = _required_cessation(exclusion, failed, reserved=job_id)
    return _ended_prior(jobs, ending, decision=decision, failed=failed,
                        evidence=evidence, reserved=job_id, now=now)


def advance_endings(jobs, control, *, ending, exclusion, now=None):
    """ONE TICK of the serving manager's prior-assignment endings.

    LEVEL-TRIGGERED, like every pass beside it: every reserved, approved,
    not-yet-admitted recovery with no ending record is offered its ending
    once per tick, derived from durable rows. A contained refusal -- another
    handler owns the Work, the host cannot say the failed execution ceased,
    this deployment holds no session for the holder -- is reported with its
    typed category and code and does not stop the pass or the tick.

    IT ADMITS NOTHING. The admission is the owner command's; what this makes
    true is the one precondition that command could not establish.
    """
    acts = []
    for reserved in intents_of(jobs):
        decision_id = reserved["decision_id"]
        if ending_of(jobs, decision_id) is not None \
                or admission_of(jobs, decision_id) is not None:
            continue
        try:
            record = end_prior_assignment(
                jobs, control, decision_id=decision_id, ending=ending,
                exclusion=exclusion, now=now)
        except ContractRefusal as refusal:
            acts.append({"decision_id": decision_id,
                         "job_id": recovery_job_id(decision_id),
                         "act": "end-prior-assignment", "outcome": "refused",
                         "detail": {"category": refusal.category,
                                    "code": refusal.code}})
            continue
        acts.append({"decision_id": decision_id,
                     "job_id": record["job_id"],
                     "act": "end-prior-assignment", "outcome": "performed",
                     "detail": {"disposition": record["disposition"]}})
    return acts


def _bound(binding, jobs, *, job_id, prior_job_id, work_id, document, worker,
           reserved):
    """CUT B2: the deployment binds the recovery Job, and a worker can serve
    EVERY stage of it.

    THE SERVABILITY QUESTION IS ASKED WITH THE SUBMITTED OPERANDS, which is
    `fresh_attempt`'s review R3 and this contract's own sentence: "servability
    must compare actual submitted input/policy/profile/task/Work rather than
    self-confirm a worker's own fields". So what travels is this recovery's
    own composed input digest, its policy digest and each stage's own profile,
    and the answer is required to be non-empty for BOTH stages -- a publication
    nothing can serve is a Job that would sit queued forever, and a review
    nothing can serve is a candidate nobody will judge.
    """
    entry = document["jobs"][0]
    job = {"input_digest": entry["input_digest"],
           "policy_digest": entry["policy_digest"]}
    # EACH STAGE IS HELD TO ITS OWN IDENTITY: the publication stage to the
    # reservation's publication input, the review stage to the Job's.
    publication = dict(job, input_digest=publication_input_of(jobs, job_id))
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
            f"{name_value(held.get('job_work_id'))} and this recovery runs "
            f"under {name_value(work_id)}; a Job's Work is a fact about the "
            f"Job and this operation will not quietly move it", reserved)
    serving = {}
    for stage in entry["stages"]:
        workers = binding.serving(
            job_id, stage=dict(stage),
            job=dict(publication if stage["kind"] == PUBLICATION_STAGE
                     else job),
            task=creation.job_task_of(jobs, prior_job_id))
        if not workers:
            raise _refusing(
                f"no configured worker can serve Job {name_value(job_id)}'s "
                f"{name_value(stage['kind'])} stage under its own submitted "
                f"input, policy and profile "
                f"({stage['profile_name']}/{stage['profile_digest']}); a "
                f"stage that cannot be selected is a Job that would sit "
                f"queued forever", reserved)
        serving[stage["kind"]] = sorted(workers)
    # BY WORKER IDENTITY, which is what the selector answers (review
    # 2026-11-23T18-55-03Z R1). `DeploymentBinding.serving` returns the
    # configured `worker_id`s `stage_execution.servable_workers` found
    # compatible; this compared the installed worker's PARTICIPANT against
    # them, so the shipped binding could never satisfy it and only a stand-in
    # port that answered participants did. The pool tells its workers apart
    # by `worker_id`, and that is the identity compared here.
    if worker["worker_id"] not in serving[PUBLICATION_STAGE]:
        raise _refusing(
            f"this deployment's installed publication worker "
            f"{name_value(worker['worker_id'])} is not among the workers "
            f"that can serve the publication stage "
            f"({sample_of(serving[PUBLICATION_STAGE])}); the stage was "
            f"composed under that worker's own profile, so a deployment that "
            f"answers otherwise is describing two different installations",
            reserved)
    return {"job_id": job_id, "disposition": disposition,
            "job_work_id": work_id, "serving": serving,
            "publication_worker": dict(worker)}


def _completed(jobs, operands, *, record, recorded, work, bound, ending,
               evidence, now):
    """CUT C: the reservation becomes an admission, and the answer is
    journalled.

    THE RESULT IS RECORDED RATHER THAN RECOMPOSED, `retained_recovery.
    _completed`'s rule: a caller repeating the command is told exactly what
    the first one was told -- which evidence the admission rested on, which
    assignment was ended, which workers can serve it and which act is still
    owed -- instead of a second rendering derived from a store that has moved
    on.
    """
    job_id = operands["job_id"]
    answer = {**{name: record[name] for name in INTENT_MEMBERS
                 if name not in ("state", "intended_at")},
              "state": "admitted",
              "stage_ids": list(recorded["stages"]),
              "work": work, "binding": bound,
              "ending": {one: ending[one] for one in
                         ("disposition", "expect", "answer", "ended_at")},
              "exclusion": evidence,
              "control": job_control.control_of(jobs, job_id),
              "readiness": admission_readiness({"state": "admitted"}),
              # THE GATE AS IT STANDS AT ADMISSION, which is SHUT. It is read
              # from the execution owner rather than asserted here, so an
              # admission cannot report a gate state the gate's own owner
              # disagrees with.
              "gate": {"open": False, "reason": GATE_UNAVAILABLE,
                       "runnable": False},
              "admitted_at": boundaries.instant(now, "an admission instant")}
    missing = [one for one in ADMITTED_MEMBERS if one not in answer]
    if missing:                                           # pragma: no cover
        _refuse(f"a publication admission record carries "
                f"{', '.join(ADMITTED_MEMBERS)}; this one has no "
                f"{', '.join(missing)}", category="integrity", code="schema")

    def act(connection):
        row = connection.execute(
            "SELECT result FROM operations WHERE operation_id = ? AND "
            "kind = ? AND state = 'committed'",
            (intent_operation_id(operands["decision_id"]),
             INTENT_KIND)).fetchone()
        if row is None:                                   # pragma: no cover
            raise ContractRefusal(
                "integrity", "schema",
                f"the reservation for {name_value(job_id)} is gone between "
                f"this operation's own two cuts")
        return answer

    return jobs.transact(admit_operation_id(operands["decision_id"]),
                         ADMITTED_KIND, job_signature(ADMITTED_KIND, operands),
                         act)


def admit_publication(jobs, control, *, decision_id, exclusion, authorization,
                      binding, ownership, host, source, ending=None,
                      now=None):
    """Admit THE one linked publication/review recovery Job of one approved
    owner decision, or replay having admitted it.

    THE ORDER IS THE RECOVERY STORY, and it is `fresh_attempt`'s order for
    `fresh_attempt`'s reasons:

      1. every owner port is present and they all answer for ONE instance
      2. read the committed decision; a denial or a hold admits nothing
      3. a REPLAY answers before any owner is asked anything
      4. recheck the fences: cancellation of the original, uncertain timing
      5. re-establish the TRUST ROOT -- the original bytes, through the host
         owner, under positive cessation -- and hold it to what the decision
         bound. A decision carried out against bytes that moved is not that
         decision
      6. the PREREQUISITES, from the owners that hold them. One missing is a
         HELD PREREQUISITE: journalled once, replayed exactly, carrying no
         reservation, no binding, no submission and no offer
      7. the Work, REUSED: open, the original's own, never minted
      8. CUT A: reserve the recovery identity, inside this store's write lock
      9. CUT B: end the prior assignment through the Authority, then bind the
         Job and prove every stage servable
     10. CUT C: the `/4` submission, and the completion that closes the intent

    WHAT IS STILL NOT DONE HERE. No byte is staged, no publication attempt is
    claimed, no result is frozen, no custody exists and the review gate stays
    shut -- `publication_execution` owns all of it, and `admission_readiness`
    says so in the record this returns rather than leaving a Job id to read as
    progress.
    """
    boundaries.identity(decision_id, "an owner decision id")
    for port, members, what in (
            (exclusion, ("instance", "evidence_of"),
             "the host exclusion port"),
            (authorization, ("instance", "work_of"),
             "the Work authorization port"),
            (binding, ("instance", "binding_of"),
             "the deployment binding port"),
            (ownership, ("instance", "held"), "the instance ownership port"),
            (host, HOST_OUTPUT, "the host output port"),
            (source, SOURCE_CORRESPONDENCE,
             "the source correspondence port")):
        _port(port, members, what=what)
    # ONE INSTANCE, AGREED BY EVERY OWNER, BEFORE ANYTHING IS READ OR DONE.
    # The rule, its refusals and its reasons are `fresh_attempt`'s, read from
    # that module rather than restated: composing owner ports over somebody
    # else's deployment is what reviews R14, R17 and R18 are about, and a
    # second implementation here would be a second chance to get them wrong.
    ports = {"the host exclusion port": exclusion,
             "the Work authorization port": authorization,
             "the deployment binding port": binding,
             "the instance ownership port": ownership,
             "the host output port": host,
             "the source correspondence port": source}
    if ending is not None:
        ports["the prior-assignment ending port"] = ending
    fresh_attempt.one_instance(jobs, ports)

    decision = decision_of(jobs, decision_id)
    if decision is None:
        _refuse(f"this store holds no owner decision "
                f"{name_value(decision_id)}; a publication recovery is "
                f"admitted on a committed decision and never on a caller's "
                f"claim about one")
    if decision["disposition"] != APPROVED:
        _denied(f"owner decision {name_value(decision_id)} is "
                f"{name_value(decision['disposition'])}; a denial or a hold "
                f"launches nothing, and a later approval is a NEW decision "
                f"identity rather than a second reading of this one")
    job_id = recovery_job_id(decision_id)
    operands = {"decision_id": decision_id,
                "prior_job_id": decision["job_id"], "job_id": job_id,
                "work_id": decision["work_id"],
                "submission_id": recovery_submission_id(decision_id),
                "stages": list(decision["stages"])}

    # A REPLAY ANSWERS BEFORE ANY OWNER IS ASKED ANYTHING. The whole operation
    # is already recorded, so re-deriving its preconditions would mean a
    # completed answer could start refusing later because the host moved on --
    # the stale-check defect REC-7 removed. Both outcomes replay: an admission
    # and a held prerequisite are each immutable facts about one request.
    found, value = jobs.replay(admit_operation_id(decision_id),
                               job_signature(ADMITTED_KIND, operands),
                               kind=ADMITTED_KIND)
    if found:
        return value
    found, value = jobs.replay(held_operation_id(decision_id),
                               job_signature(HELD_KIND, operands),
                               kind=HELD_KIND)
    if found:
        return value

    recorded_at = boundaries.instant(now if now is not None else jobs._now(),
                                     "a publication admission instant")
    _refuse_cancelled(jobs._connection, decision["job_id"],
                      "a publication recovery admission")
    job_control.refuse_uncertain(jobs._connection, decision["job_id"],
                                 "a publication recovery admission for it",
                                 now=recorded_at)

    # -- THE TRUST ROOT, AGAIN, and held to what the decision bound.
    selection = inspect(jobs, control, job_id=decision["job_id"],
                        stage_id=decision["stage_id"],
                        episode=decision["episode"], host=host,
                        exclusion=exclusion, source=source)
    if selection["holds"]:
        first = selection["holds"][0]
        _refuse(f"this publication recovery is held and is not admitted: "
                f"{first['category']}/{first['code']}: {first['message']}",
                category=first["category"], code=first["code"])
    wanted = expected_facts(selection)
    for member in EXPECTED_MEMBERS:
        if decision["expected"][member] != wanted[member]:
            _refuse(f"owner decision {name_value(decision_id)} bound "
                    f"{member} "
                    f"{name_value(json.dumps(decision['expected'][member]))} "
                    f"and the original now reports "
                    f"{name_value(json.dumps(wanted[member]))}; an admission "
                    f"carries out the decision that was taken, on the bytes "
                    f"it was taken about",
                    category="integrity", code="digest")

    # -- THE PREREQUISITES, before any effect. A deployment that installs no
    #    publication worker is asked ONCE and its refusal is a HELD record
    #    rather than an exception, because "this instance cannot serve a
    #    publication stage" is an operational fact an owner reads, not a
    #    malformed request.
    worker = None
    try:
        worker = _installed_worker(binding)
    except ContractRefusal:
        worker = None
    owed = prerequisites(jobs, worker=worker)
    missing = [one for one in owed if not one["available"]]

    # -- THE WORK, REUSED. Open, the original's own, never minted.
    work = authorization.work_of(decision["work_id"])
    if work is None:
        _refuse(f"this deployment's Authority holds no Work "
                f"{name_value(decision['work_id'])}; a publication recovery "
                f"runs under the authorization the failed execution held and "
                f"never under one it mints for itself")
    if work.get("status") != "open":
        _refuse(f"Work {name_value(decision['work_id'])} is "
                f"{name_value(work.get('status'))} and a recovery reuses an "
                f"OPEN authorization; reopening somebody else's Work is not "
                f"this operation's to do")
    reused = {"work_id": decision["work_id"], "disposition": "reused",
              "status": work.get("status")}

    if missing:
        return _held_admission(jobs, operands, decision=decision,
                               selection=selection, owed=owed, work=reused,
                               ownership=ownership, recorded_at=recorded_at)

    # -- EVERYTHING BELOW IS THE REAL ADMISSION.
    if ending is None:
        _refuse("a publication recovery admission composes the prior-"
                "assignment ending port; a fresh assignment on the reused "
                "Work requires the previous one to be ended through the "
                "Authority's own exact-expect transition, and this operation "
                "does not decide that owner's fact for it by assuming one",
                category="refused", code="capability")
    _port(ending, PRIOR_ASSIGNMENT, what="the prior-assignment ending port")
    failed = _failed_publication(jobs, control, job_id=decision["job_id"],
                                 stage_id=decision["stage_id"],
                                 episode=decision["episode"])
    prior = _prior(jobs, decision)
    declaration = recovery_input(decision, selection)
    # THE JOB'S INPUT IDENTITY IS THIS RECOVERY'S OWN (review
    # 2026-11-23T18-55-03Z R3), derived by the deployment from its installed
    # publication worker's declarations bound to THIS recovery's Work and the
    # ORIGINAL Job's task -- the document that worker will actually be
    # delivered for this Job. The first cut submitted every recovery under
    # the installed worker's own identity, which names the one Work that
    # worker was installed against: a recovery on any other Work was a Job
    # the selector refused, so the reusable capacity served exactly one Work.
    #
    # THE DERIVATION IS THE DEPLOYMENT'S AND IS ASKED, NOT REPEATED. The same
    # rule answers `serving` below and composes the delivery when the stage
    # is served, so the three cannot disagree; this module compares nothing
    # about a manifest and holds the answer only as the identity it submits.
    submitted = boundaries.text(
        binding.publication_input(
            job_id, work_id=decision["work_id"],
            task=creation.job_task_of(jobs, decision["job_id"])),
        "a publication recovery's input identity")
    # THE JOB ITSELF IS SUBMITTED UNDER THE ORIGINAL JOB'S INPUT IDENTITY
    # (COMPLETION-PLAN-385909 outcome 4). That is what the Work's ordinarily
    # configured reviewer is servable under, so no reviewer is reconfigured,
    # no declaration is copied into the review lane and no cross-lane check is
    # weakened. The publication stage's own identity is `submitted`, recorded
    # on the reservation and read back through `publication_input_of` by the
    # selector and by the publication capacity.
    document = _composed(prior, decision, job_id=job_id,
                         submission_id=operands["submission_id"],
                         worker=worker,
                         input_digest=prior["entry"]["input_digest"])
    bounds = admitted_bounds(resolved_profile(decision["profile"]),
                             admitted_at=recorded_at,
                             stages=decision["stages"])
    record = {
        **operands, "state": "intended",
        "publication_stage_id": publication_stage_id(decision_id),
        "review_stage_id": review_stage_id(decision_id),
        "candidate": {"base": selection["producer"]["base"],
                      "head": selection["producer"]["head"],
                      "changed_paths": selection["producer"]["changed_paths"],
                      "attempt_id": selection["selector"]["attempt_id"],
                      # THE ORIGINAL PRODUCER'S OWN ATTRIBUTION, carried on
                      # the reservation. REC-9 keeps "original producer and
                      # recovery provenance" both, and the publisher's
                      # provenance cannot name the producer it preserves from
                      # an attempt id alone. It is also what the reviewer's
                      # independence is enforced against.
                      "participant": selection["selector"]["participant"],
                      "principal": selection["selector"]["principal"]},
        "output": dict(selection["output"]),
        "input_declaration": declaration,
        "input_digest": submitted,
        "recovery_input_digest": recovery_input_digest(declaration),
        "worker": dict(worker), "bounds": bounds,
        "intended_at": recorded_at}

    with ownership.held(), ownership.invocation(job_id):
        # -- CUT A.
        reservation = _reserved(jobs, operands, record, document=document,
                                prior_job_id=decision["job_id"])
        if reservation["recovery_input_digest"] \
                != record["recovery_input_digest"]:
            _refuse(f"this store's reservation for {name_value(job_id)} was "
                    f"taken against recovery input "
                    f"{name_value(reservation['recovery_input_digest'])} and "
                    f"this request composes "
                    f"{name_value(record['recovery_input_digest'])}; a "
                    f"publication is admitted against the input its "
                    f"reservation named", category="integrity", code="digest")
        # -- re-ask the host, because cut A took time and a reservation is not
        #    a lock on somebody else's store.
        evidence = _required_cessation(exclusion, failed, reserved=job_id)
        # -- CUT B.
        released = _ended_prior(jobs, ending, decision=decision,
                                failed=failed, evidence=evidence,
                                reserved=job_id, now=recorded_at)
        bound = _bound(binding, jobs, job_id=job_id,
                       prior_job_id=decision["job_id"],
                       work_id=decision["work_id"], document=document,
                       worker=worker, reserved=job_id)
        # -- CUT C.
        try:
            recorded = submission._submit_owned(jobs, document)
        except ContractRefusal as refusal:
            if refusal.code == "operation-collision":
                _refuse(f"the submission for this recovery collided with an "
                        f"operation this store had already settled: "
                        f"{refusal.message}. The recovery identity "
                        f"{name_value(job_id)} is RESERVED and its binding "
                        f"may already be published; repeating this request "
                        f"cannot change an immutable outcome, so this "
                        f"recovery needs a new owner decision identity")
            raise _incomplete(f"the submission for this recovery was refused: "
                              f"{refusal.message}",
                              reserved=job_id) from refusal
        return _completed(jobs, operands, record=reservation,
                          recorded=recorded, work=reused, bound=bound,
                          ending=released, evidence=evidence,
                          now=recorded_at)


def _required_cessation(exclusion, failed, *, reserved):
    """POSITIVE CESSATION OF THE FAILED EXECUTION, re-asked, and `unknown`
    REFUSES.

    THE DIFFERENCE FROM `_exclusion` ABOVE IS WHAT HAPPENS TO THE ANSWER.
    There it is reported, because an inspection performs no effect and an
    owner is owed the whole picture; here it RAISES, because the next act
    ends an Authority assignment and stages bytes for a new execution --
    `retained_recovery._excluded`'s split, in this operation's words.
    """
    holds = []
    evidence = _exclusion(exclusion, (failed["attempt_id"],), holds=holds)
    if holds:
        first = holds[0]
        raise _refusing(
            f"the host cannot account for attempt "
            f"{name_value(failed['attempt_id'])} now: "
            f"{first['category']}/{first['code']}: {first['message']}",
            reserved)
    return evidence


def _held_admission(jobs, operands, *, decision, selection, owed, work,
                    ownership, recorded_at):
    """THE CHECKPOINT-1 ANSWER, kept exactly, for a deployment that cannot
    serve a publication stage.

    IT IS NOT A FALLBACK THAT ADMITS SOMETHING LESSER. No identity is
    reserved, no assignment is ended, no binding is published and no document
    is submitted: the record says `reserved: False` in so many words and names
    every capability that is owed. A build rolled back, a store nobody has
    migrated to generation 10 and a deployment that installs no publication
    worker all land here, and each is told exactly which of those it is.
    """
    job_id = operands["job_id"]
    record = {
        **operands, "state": "held", "reserved": False,
        "prerequisites": owed,
        "owners": {"instance": (ownership.instance() or {}).get("root"),
                   "work": dict(work),
                   "host_output": selection["output"]["root_identity"],
                   "exclusion": selection["exclusion"],
                   "source": selection["correspondence"]["owner"]},
        "candidate": {"base": selection["producer"]["base"],
                      "head": selection["producer"]["head"],
                      "changed_paths": selection["producer"]["changed_paths"],
                      "attempt_id": selection["selector"]["attempt_id"]},
        "output": dict(selection["output"]),
        "readiness": admission_readiness(operands),
        "gate": {"open": False, "reason": GATE_UNAVAILABLE,
                 "runnable": False},
        "recorded_at": recorded_at}

    def act(connection):
        # THE FENCES ARE RE-ASKED INSIDE THE WRITE LOCK, so a cancellation
        # that committed while this operation was reading the host meets this
        # record rather than slipping past it.
        _refuse_cancelled(connection, decision["job_id"],
                          "a publication recovery admission")
        job_control.refuse_uncertain(connection, decision["job_id"],
                                     "a publication recovery admission for "
                                     "it", now=jobs._now())
        # AND NOTHING MAY HAVE TAKEN THE DERIVED IDENTITY, even though this
        # answer does not reserve it. An identity another pipeline already
        # owns is one a later admission could not use, and finding that out
        # then would be finding it out with an owner decision already
        # committed against it.
        taken = connection.execute(
            "SELECT job_id FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        if taken is not None:
            raise ContractRefusal(
                "refused", "precondition",
                f"Job {name_value(job_id)} is already recorded in this store "
                f"by another submission; the identity this decision's "
                f"recovery would carry names another pipeline")
        return record

    with ownership.held(), ownership.invocation(job_id):
        return jobs.transact(held_operation_id(operands["decision_id"]),
                             HELD_KIND,
                             job_signature(HELD_KIND, operands), act)
