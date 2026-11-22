"""THE RETAINED VERIFICATION FAILURE, ANALYSED ONCE, AND DELIVERED TO THE OWNER.

W385623 Stage 1-A, under DESIGN REC-8 and the accepted Stage 1 contract
`work/records/2026/08/finding-v12-isolated-agent-workers/findings/
finding-v12-team-hierarchy-shared-approvers/STAGE-1-CONTRACT.md` (SHA-256
`52c2c640fdbb791e70ae61edf7ef7db7190bacd767d6d044f678517d2e09e1bc`), accepted
by `review-2026-11-22T05-18-37Z.md`. The owning record is
`work/records/2026/11/finding-v12-retained-failure-analysis/`.

WHAT THIS OWNS, and the list is the whole of 1-A:

  1. THE TRIGGER. A durably attributed terminal `verification-failed` ending
     with a successful provider turn and a VALIDATED retained candidate. Not a
     commit name: the retained bytes, the base and the content manifest are
     bound and compared, and a candidate that fails that is REPORTED rather
     than used (`classified_failure`).
  2. THE FAILURE KEY. Authority, Work, execution Job, stage, attempt and
     terminal-result identity, over which every record below is deduplicated.
     A successor's failure has its own key; one ending delivered twice is one
     analysis and one owner item.
  3. THE FIXED INPUT. One immutable document composed from facts their owners
     already hold, digested once, and compared again at report time -- so an
     analysis is about exactly the evidence its intent named.
  4. THE DECLARED ANALYSIS AUTHORITY. Participant, principal, profile and
     PERMITTED OUTPUTS, declared as configuration. The role is not a model and
     not a provider; an absent or unusable declaration is an actionable
     configuration refusal and never a coder standing in for one.
  5. THE DURABLE RECORDS. Failure item, analysis intent, dispatch intent,
     analysis report, owner item -- each one operation of this store's journal
     under a deterministic identity, so an exact retry replays and changed
     operands collide.
  6. THE FINITE ENDING. A failed, expired or cancelled analysis, and an
     analysis whose cessation is UNKNOWN, each retain whatever partial
     evidence exists and deliver ONE owner item. There is no retry here, no
     recursive analysis and no replacement.

WHAT IT REFUSES TO DO, and every one of these is a ruling rather than a
preference:

  * NO MUTATION OF THE CANDIDATE, THE VERIFIER OR THE EXECUTION. Nothing in
    this module writes to the Worker Manager's control store, to a candidate
    tree, to a verifier input or to a stage's execution state. The analysis
    agent's own result is read for its report and for nothing else, and a
    result that carries anything outside `PERMITTED_OUTPUTS` is refused as the
    mutation attempt it is.
  * NO RECOVERY AUTHORITY. An analysis report earns no successor, no
    correction round, no verdict and no receipt. W385624 owns the owner
    decision and the successor admission; W385625 owns the verification and
    review recovery. Neither is implemented here and neither graph is touched.
  * NO RECURSION. An analysis attempt's own ending is excluded from the
    trigger, by the declared analysis participant and by this store's own
    dispatch records -- two independent exclusions, because one of them is
    configuration and the other is history.
  * NO BLIND DISPATCH. The dispatch intent is committed BEFORE the launch it
    is about. A re-entry that finds an intent whose attempt the control store
    cannot positively account for answers `unknown` and HOLDS; it never
    launches a second analysis turn.
  * NO MANUFACTURED CESSATION. Whether the original runtime ceased is
    `worker_manager.failure_cause`'s answer, carried with its qualification.
    An `unknown` travels as an unknown and excludes replacement.
  * NO CLOCK RESET. The analysis admission has its own deadlines, derived from
    the owner-approved profile and persisted in the intent, so a restart
    resolves the admitted deadlines rather than fresh ones. The original Job's
    expired deadlines are not read, moved or extended.

NOTHING HERE IS A SECOND ACCOUNT OF A FACT SOMEBODY ELSE HOLDS. The frozen
result, the retained manifest, the measured candidate tree, the fixed
assignment and the cessation axis are read through their accepted owners in
`baton_v12.worker_manager`; the stage, the Job and the Work come from this
store's own rows. This module composes, deduplicates and journals.
"""

import json

from ..contracts import ContractRefusal, digest, digest_of_bytes, own
from ..contracts.errors import name_value
from ..worker_manager import (attempts, boundaries, frozen_output_of,
                              load_manifest)
from ..worker_manager import failure_cause
from ..worker_manager.schema import OUTPUT_TYPES
# The frozen-result disposition vocabulary, under this module's own name for
# it: `DISPOSITIONS` here is this package's RECOVERY disposition set, and two
# closed vocabularies under one word is how a mapping comes to answer for the
# wrong one.
from ..worker_manager.schema import DISPOSITIONS as RESULT_DISPOSITIONS
from . import cancellation, documents, ending, episodes, submission
from .store import job_signature

__all__ = ["ANALYSIS_DEFINITION", "ANALYSIS_DEFINITION_BYTES",
           "ANALYSIS_PROFILE", "ANALYSIS_PROFILE_DIGEST", "ANALYSIS_PROFILES",
           "CLOCK_ORIGINS", "resolved_profile", "admitted_deadlines",
           "ANALYSIS_ROLE", "DECLARATION_SCHEMA", "DECLARATION_MEMBERS",
           "ANALYSIS_OUTPUT", "PARTIAL_OUTPUT", "PERMITTED_OUTPUTS",
           "check_analysis_declaration", "declaration_digest",
           "FAILURE_SELECTORS", "failure_key",
           "TRIGGER_ENDING", "CANDIDATE_CLAIM", "ORDINARY_TESTS",
           "classified_failure", "INPUT_SCHEMA", "analysis_input",
           "input_digest",
           "REPORT_SCHEMA", "REPORT_MEMBERS", "OPTION_MEMBERS",
           "MAX_REPORT_BYTES", "check_analysis_report", "report_digest",
           "FAILURE_KIND", "INTENT_KIND", "DISPATCH_KIND", "REPORT_KIND",
           "OWNER_ITEM_KIND",
           "failure_operation_id", "intent_operation_id",
           "dispatch_operation_id", "report_operation_id",
           "owner_item_operation_id",
           "failure_of", "intent_of", "dispatch_of", "report_of",
           "owner_item_of", "failures_of",
           "record_failure", "record_analysis_intent", "record_dispatch",
           "record_analysis_report", "record_owner_item",
           "DISPOSITIONS", "OWNER_OUTCOMES", "ENDPOINT_OUTCOMES",
           "REPORTED_OUTCOME", "DISPATCH_STATES", "TRIGGER_DISPOSITION",
           "CANDIDATE_OUTPUT_TYPE", "PUBLISHED_PROFILE_DIGEST",
           "preserved_partials",
           "recovery_disposition", "reconciled_dispatch",
           "observe_terminal_failure", "admit_dispatch", "deliver_analysis",
           "deliver_endpoint", "expiry_reached",
           "ANALYSIS_SEAM", "WORKER_DECLARED", "TRIGGER_STAGE_KIND",
           "ANALYSIS_ENDINGS", "ANALYSIS_ACTS", "ANALYSIS_OUTCOMES",
           "RESULT_DISPOSITIONS",
           "declared_analysis_worker", "analysis_attempt_id",
           "triggered_ending", "check_analysis_seam",
           "settled_trigger_endings", "advance_recovery"]


def _refuse(message, *, category="refused", code="precondition"):
    raise ContractRefusal(category, code, message)


def _denied(message):
    raise ContractRefusal("policy", "denied", message)


# -- 1. the owner-approved finite profile ------------------------------------
#
# THE DEFINITION IS HELD AS DATA AND PROVES ITS OWN DIGEST. M385612 published
# `stage1-analysis/1` as one immutable definition record whose SHA-256 covers
# its exact UTF-8 bytes including the final newline; the contract's section 5
# names that digest and requires admission to check exact agreement with the
# profile the owner selected.
#
# SO THE NUMBERS ARE NOT RESTATED HERE. Every bound and every clock origin
# below is READ OUT of this document, and the document is held to the owner's
# digest by `ANALYSIS_PROFILE_DIGEST` at import. A table of four integers
# beside the record would be the second account of one ceiling that
# `job_control.PROFILES` exists to prevent -- and the integers are the half
# that silently drifts.
#
# AND IT IS DELIBERATELY NOT AN ENTRY IN `job_control.PROFILES`. That table is
# the control profile of an ADMITTED JOB and its closed `PROFILE_MEMBERS`
# projects a verification-command ceiling; the analysis execution runs no
# verification command, and writing one into its resolved document would state
# a bound the owner did not approve. The implementation Job that builds this
# feature keeps its own `native-handoff/1` control, which is a different fact
# about a different execution.
ANALYSIS_PROFILE = "stage1-analysis/1"
ANALYSIS_DEFINITION = {
    "automatic_corrections": 0,
    "automatic_retries": 0,
    "identity": ANALYSIS_PROFILE,
    "overall_job": {
        "includes_queue": True,
        "origin": "accepted_admission",
        "seconds": 4800,
    },
    "provider_invocation": {
        "origin": "invocation_start",
        "seconds": 3600,
    },
    "publication_authority": (
        "M385612; FINDING.md: Owner-approved Stage 1 finite profiles "
        "— 2026-11-22"),
    "stage": {
        "origin": "stage_admission",
        "seconds": 4800,
    },
}

# THE EXACT BYTES THE OWNER'S DEFINITION RECORD CARRIES, reproduced rather
# than read from the dossier: a product module that opened a Work record to
# resolve its own policy would make an evidence directory a runtime input.
# The acceptance module reads the record and compares, which is where that
# binding belongs.
ANALYSIS_DEFINITION_BYTES = (
    json.dumps(ANALYSIS_DEFINITION, indent=2, sort_keys=True) + "\n"
).encode("utf-8")
ANALYSIS_PROFILE_DIGEST = digest_of_bytes(ANALYSIS_DEFINITION_BYTES)

# The frozen table, in `job_control.PROFILES`' shape and under its rule: a
# profile an analysis was admitted under is never edited, and a changed policy
# is a new entry.
ANALYSIS_PROFILES = {ANALYSIS_PROFILE: ANALYSIS_DEFINITION}

# WHERE EACH CLOCK STARTS, as the closed vocabulary the definition names. A
# bare number cannot say what it is measured from, and the contract makes the
# origins normative: the Job clock runs from the ACCEPTED ANALYSIS ADMISSION
# with queue time included, the stage clock from the stage's own execution
# admission, and the provider clock from the invocation's REAL START. No
# activity or dispatch stamp substitutes for an invocation start.
CLOCK_ORIGINS = ("accepted_admission", "stage_admission", "invocation_start")

# THE DIGEST STAGE-1-CONTRACT.md SECTION 5 PINS, held against the definition
# above at import. A RAISE AND NOT AN `assert`: a build run under `-O` strips
# assertions, and a self-check that disappears under an optimisation flag is
# best-effort dressed as a guarantee -- which is the posture
# `failure_cause.ensure_cessation_intent` was corrected for. The acceptance
# module compares these bytes to the owner's published record besides.
PUBLISHED_PROFILE_DIGEST = (
    "sha256:a4be8b48e098efc47f770a8b7f941b80eadd22b23c48eebf67863d3a4dc824ab")
if ANALYSIS_PROFILE_DIGEST != PUBLISHED_PROFILE_DIGEST:   # pragma: no cover
    raise AssertionError(
        f"the held {ANALYSIS_PROFILE} definition digests to "
        f"{ANALYSIS_PROFILE_DIGEST} and the owner published "
        f"{PUBLISHED_PROFILE_DIGEST}; this build does not carry the approved "
        f"profile and will not admit an analysis under a guess")
if any(ANALYSIS_DEFINITION[one]["origin"] not in CLOCK_ORIGINS
       for one in ("overall_job", "stage", "provider_invocation")):
    raise AssertionError(                                 # pragma: no cover
        "the held analysis definition names a clock origin this build does "
        "not own")


def resolved_profile(profile=ANALYSIS_PROFILE):
    """The approved bounds of one analysis profile, with their units.

    A profile this build does not hold is a STALE SELECTION and is refused
    rather than guessed -- `job_control.owned_control`'s rule, for its reason:
    an execution admitted under a policy nobody selected is one nothing can
    enforce.
    """
    boundaries.text(profile, "an analysis profile identity")
    if profile not in ANALYSIS_PROFILES:
        _refuse(f"an analysis profile is one of "
                f"{', '.join(sorted(ANALYSIS_PROFILES))}; this is "
                f"{name_value(profile)}. A profile this build does not hold "
                f"is a finite control it cannot enforce",
                category="integrity", code="schema")
    held = ANALYSIS_PROFILES[profile]
    return {"profile": profile, "units": "seconds", "scope": "per-admission",
            "digest": digest_of_bytes(
                (json.dumps(held, indent=2, sort_keys=True)
                 + "\n").encode("utf-8")),
            "automatic_retries": held["automatic_retries"],
            "automatic_corrections": held["automatic_corrections"],
            "overall_job_seconds": held["overall_job"]["seconds"],
            "overall_job_includes_queue": held["overall_job"]["includes_queue"],
            "overall_job_origin": held["overall_job"]["origin"],
            "stage_seconds": held["stage"]["seconds"],
            "stage_origin": held["stage"]["origin"],
            "provider_invocation_seconds":
                held["provider_invocation"]["seconds"],
            "provider_invocation_origin":
                held["provider_invocation"]["origin"]}


def admitted_deadlines(policy, *, admitted_at):
    """The deadlines ONE analysis admission is bound by, derived once.

    PERSISTED WITH THE INTENT AND NEVER RE-DERIVED AT A LATER CLOCK, which is
    LIM-5's rule and the contract's: "Restart preserves admitted deadlines,
    not fresh clocks." The stage and provider clocks are NOT derived here --
    their origins are the stage's own execution admission and the invocation's
    real start, neither of which exists at admission -- so what this answers
    is the Job deadline and the two remaining ceilings a later origin applies.
    """
    boundaries.instant(admitted_at, "an accepted analysis admission instant")
    return {"admitted_at": admitted_at,
            "job_deadline_at": boundaries.deadline(
                admitted_at, policy["overall_job_seconds"],
                "an analysis Job deadline"),
            "job_seconds": policy["overall_job_seconds"],
            "includes_queue": policy["overall_job_includes_queue"],
            "stage_seconds": policy["stage_seconds"],
            "stage_origin": policy["stage_origin"],
            "provider_invocation_seconds":
                policy["provider_invocation_seconds"],
            "provider_invocation_origin":
                policy["provider_invocation_origin"]}


# -- 2. the declared analysis authority --------------------------------------
#
# A ROLE, NOT A MODEL. REC-8: "The analysis role uses declared worker/profile
# configuration, without binding the role to a provider or model". So the word
# below is a RESPONSIBILITY and the thing that carries it is a declaration a
# deployment supplies -- participant, principal, worker, profile and the
# outputs it is permitted to write. No adapter name, image, model or provider
# appears in this module, and a declaration naming one in place of a
# participant is refused by the member contract rather than by a denylist.
ANALYSIS_ROLE = "analysis"
DECLARATION_SCHEMA = "baton.v12.recovery-analysis-worker/1"

# THE TWO OUTPUTS AN ANALYSIS MAY WRITE, and the set is CLOSED because that is
# what makes "it may author its report only" enforceable. `analysis` is the
# report; `partial` is whatever an interrupted turn had written when it
# stopped, which the finite endings preserve. There is no candidate output, no
# proposal, no verifier input and no execution state here -- a frozen analysis
# result carrying any other output is refused as a mutation attempt.
ANALYSIS_OUTPUT = "analysis"
PARTIAL_OUTPUT = "partial"
PERMITTED_OUTPUTS = (ANALYSIS_OUTPUT, PARTIAL_OUTPUT)

DECLARATION_MEMBERS = ("schema", "role", "worker_id", "participant",
                       "principal", "profile", "profile_digest",
                       "permitted_outputs", "capability_digest")

MAX_DECLARATION_BYTES = 2048


def declaration_digest(document):
    """The canonical identity of one declaration, over the WHOLE object.

    `role_contract.contract_digest`'s rule: no embedded digest member, so the
    identity is a fact about the bytes rather than a field the document
    asserts about itself.
    """
    return digest(own(document, what="an analysis worker declaration"))


def check_analysis_declaration(document,
                               *, what="an analysis worker declaration"):
    """The closed validator for the declared analysis authority.

    PURE: no store, no filesystem, no environment, no engine and no provider
    import. What it proves is that a deployment has DECLARED, explicitly, who
    analyses, under whose principal, against which owner-approved profile, and
    what that execution is permitted to write.

    AN ABSENT OR UNUSABLE DECLARATION IS A CONFIGURATION REFUSAL. The contract
    is explicit that it is "an actionable configuration refusal/owner item,
    not substitution of a coder or silent success", which is why every failure
    below REFUSES and none of them resolves to a default.
    """
    taken = own(document, what=what)
    if type(taken) is not dict:
        _refuse(f"{what} is one closed object; this is {name_value(document)}",
                category="integrity", code="schema")
    missing = [one for one in DECLARATION_MEMBERS if one not in taken]
    extra = sorted(one for one in taken if one not in DECLARATION_MEMBERS)
    if missing or extra:
        _refuse(f"{what} is exactly {', '.join(DECLARATION_MEMBERS)}"
                + (f"; missing {', '.join(missing)}" if missing else "")
                + (f"; unexpected {', '.join(extra)}" if extra else ""),
                category="integrity", code="schema")
    if taken["schema"] != DECLARATION_SCHEMA:
        _denied(f"{what} says it is {name_value(taken['schema'])} and this "
                f"build reads exactly {name_value(DECLARATION_SCHEMA)}")
    if len(json.dumps(taken).encode("utf-8")) > MAX_DECLARATION_BYTES:
        _refuse(f"{what} is bounded configuration",
                category="integrity", code="schema")
    # THE ROLE IS THE DEDICATED ONE AND IS NOT A CODING LANE. Section 6 of the
    # contract: "do not disguise analysis as an authorized coding stage". A
    # declaration that named `implementation` here would be exactly that.
    if taken["role"] != ANALYSIS_ROLE:
        _denied(f"{what} declares role {name_value(taken['role'])}; the "
                f"dedicated analysis responsibility is {name_value(ANALYSIS_ROLE)} "
                f"and an implementation or review lane does not carry it")
    for member in ("worker_id", "participant", "principal",
                   "capability_digest"):
        boundaries.text(taken[member], f"a declared analysis {member}")
    # NO PROVIDER OR MODEL STANDS IN FOR A PARTICIPANT. The participant is a
    # coordination identity the Authority resolves; a declaration whose
    # participant is an adapter, an image reference or a model name is one
    # that bound the role to a provider, which REC-8 forbids by name.
    if taken["participant"] == taken["principal"]:
        _refuse(f"{what} names one value as both its participant and its "
                f"principal; who executes and under whose authority are two "
                f"facts, and a declaration carrying one of them twice cannot "
                f"attribute either", category="integrity", code="schema")
    if taken["profile"] not in ANALYSIS_PROFILES:
        _denied(f"{what} selects profile {name_value(taken['profile'])} and "
                f"the owner-approved analysis profiles are "
                f"{', '.join(sorted(ANALYSIS_PROFILES))}; a profile selection "
                f"is the owner's and is not inferred")
    expected = resolved_profile(taken["profile"])["digest"]
    if taken["profile_digest"] != expected:
        _refuse(f"{what} names profile digest "
                f"{name_value(taken['profile_digest'])} and "
                f"{name_value(taken['profile'])} is "
                f"{name_value(expected)}; admission checks exact agreement "
                f"with the definition the owner published",
                category="integrity", code="digest")
    permitted = taken["permitted_outputs"]
    if type(permitted) is not list or not permitted \
            or any(type(one) is not str for one in permitted) \
            or sorted(permitted) != sorted(PERMITTED_OUTPUTS):
        _denied(f"{what} permits {name_value(permitted)}; an analysis is "
                f"permitted exactly {', '.join(PERMITTED_OUTPUTS)} -- its "
                f"report and whatever a stopped turn had written -- and a "
                f"declaration that widened that would be granting the "
                f"analysis role an output it may not author")
    return taken


# -- 3. the failure key ------------------------------------------------------
#
# THE PROPOSED STABLE KEY, exactly as the contract names it: "authority + Work
# + execution Job + stage + attempt + terminal-result identity". Each selector
# narrows something a different owner holds, and together they identify ONE
# ending rather than one Job or one candidate -- which is what makes a
# successor's verification failure a DIFFERENT key and a duplicate
# notification of the same ending the SAME one.
FAILURE_SELECTORS = ("authority_uuid", "work_id", "job_id", "stage_id",
                     "attempt_id", "result_id")


def failure_key(**selectors):
    """The stable identity of ONE terminal verification failure.

    A DIGEST OVER THE CLOSED SELECTOR DOCUMENT rather than their concatenated
    text. Two reasons, and the second decides it: a journal identity is
    bounded text and six opaque identities concatenated are not, and a
    separator chosen here would be a separator some identity could contain --
    which is how two different endings acquire one key. The selectors
    themselves travel in the failure record, so the key stays resolvable.
    """
    missing = [one for one in FAILURE_SELECTORS if one not in selectors]
    extra = sorted(one for one in selectors if one not in FAILURE_SELECTORS)
    if missing or extra:
        _refuse(f"a failure key is derived from exactly "
                f"{', '.join(FAILURE_SELECTORS)}"
                + (f"; missing {', '.join(missing)}" if missing else "")
                + (f"; unexpected {', '.join(extra)}" if extra else ""),
                category="integrity", code="schema")
    for name in FAILURE_SELECTORS:
        boundaries.identity(selectors[name], f"a failure key's {name}")
    return digest({name: selectors[name] for name in FAILURE_SELECTORS})


# -- 4. the trigger ----------------------------------------------------------

# The worker's own typed ending this trigger is about, by value from the
# vocabulary its owner publishes rather than respelled here.
TRIGGER_ENDING = "verification-failed"
if TRIGGER_ENDING not in failure_cause.DECLARED_ENDINGS:  # pragma: no cover
    raise AssertionError(
        "this trigger names an ending the worker vocabulary does not carry")

# The two worker-owned claims a retained candidate carries, named by their
# owners' spellings. The first is what the turn produced; the second is what
# its own required command did. BOTH are read, and they are COMPARED: a claim
# and an observation that disagree about the candidate are two accounts of one
# tree, and the contract refuses to resolve that by picking a half.
CANDIDATE_CLAIM = "baton.git-proposal/1"
ORDINARY_TESTS = "baton.git-ordinary-tests/1"
CLAIM_MEMBERS = ("base", "head", "transport", "recap")
TESTS_MEMBERS = ("argv", "base", "head", "status", "task_digest", "task_id")

# The manager disposition a verification-failed turn freezes. `claude_agent`
# maps every ending but `candidate` and `yielded` to `unable`, so this is the
# word the control store holds for this trigger; `completed` is a candidate or
# a yield, and `cancelled`/`plan-rejected` are other endings entirely.
TRIGGER_DISPOSITION = "unable"

MAX_ARGV_WORDS = 64
MAX_ARGV_BYTES = 1 << 14
# THE OWNED CANDIDATE OUTPUT TYPE, taken from the schema that owns the
# vocabulary rather than respelled, and held to the one this trigger is about:
# a reordered `OUTPUT_TYPES` would otherwise silently make this reader look
# for a candidate in a directory result.
CANDIDATE_OUTPUT_TYPE = OUTPUT_TYPES[0]
if CANDIDATE_OUTPUT_TYPE != "git-change-proposal":        # pragma: no cover
    raise AssertionError(
        "the owned output vocabulary no longer names the candidate type this "
        "trigger validates")


def _retained(control, attempt_id):
    """The frozen result and retained manifest of one attempt, cross-bound.

    `native_handoffs._frozen_result`'s bindings, with this trigger's own
    disposition: a namespaced claim by itself says only that somebody wrote
    members into an output. What makes it evidence about THIS attempt is that
    the frozen summary and the retained manifest name one result, and that the
    manifest names this attempt's own fixed assignment at its own generation.
    """
    frozen = frozen_output_of(control, attempt_id)
    if frozen is None:
        _refuse(f"attempt {name_value(attempt_id)} froze no result; a "
                f"retained verification failure is read from immutable "
                f"output and never from a running one")
    if frozen["disposition"] != TRIGGER_DISPOSITION:
        _refuse(f"attempt {name_value(attempt_id)} froze a "
                f"{name_value(frozen['disposition'])} result and this "
                f"trigger is the {name_value(TRIGGER_DISPOSITION)} ending a "
                f"failed required verification freezes; another disposition "
                f"is another ending and is not reclassified here")
    result = load_manifest(control, frozen["manifest_digest"],
                           "resultManifest")
    if result is None:
        _refuse(f"this manager retains no result manifest at "
                f"{name_value(frozen['manifest_digest'])} for attempt "
                f"{name_value(attempt_id)}; absent retained evidence is "
                f"reported and is never treated as eligible recovery input")
    if result["result_id"] != frozen["result_id"]:
        _refuse("the frozen summary and its retained manifest name different "
                "results", category="integrity", code="schema")
    fixed = attempts.assignment_of(control, attempt_id)
    expected = {"work_ref": {"authority_uuid": fixed["authority_uuid"],
                             "work_id": fixed["work_id"]},
                "participant": fixed["participant"],
                "generation": fixed["generation"]}
    if result["assignment_ref"] != expected:
        _refuse("the frozen result and the attempt do not name one "
                "assignment", category="integrity", code="schema")
    return frozen, result, fixed


def _candidate(frozen, result, attempt_id):
    """THE RETAINED CANDIDATE, bound to bytes rather than to a commit name.

    The contract is explicit that "a candidate commit name alone is
    insufficient: bind and validate retained bytes and base/content
    manifest". So every clause below is a binding:

      ONE present candidate output of the owned type, measured, with both its
      artifact and its content manifest -- a document that claims material it
      nobody measured is not evidence;
      THE ARTIFACT IDENTITY `sealing` COMPOSES for this exact attempt, so a
      tree staged for another attempt cannot arrive;
      THIS MANAGER'S OWN INDEXED ARTIFACT ROW agreeing with the retained
      manifest about identity, digest and locator, because two accounts that
      disagree are both unread;
      THE ARTIFACT DIGEST EQUAL TO THE MEASURED TREE DIGEST, which is what
      ties the named bytes to the measurement;
      and the worker's CLAIM and its own ordinary-test OBSERVATION agreeing
      about the base and the head.
    """
    named = [one for one in result["outputs"]
             if one.get("type") == CANDIDATE_OUTPUT_TYPE
             and one.get("status") == "present"]
    if len(named) != 1:
        _refuse(f"the frozen result of attempt {name_value(attempt_id)} "
                f"carries {len(named)} present "
                f"{name_value(CANDIDATE_OUTPUT_TYPE)} outputs; a retained "
                f"candidate is exactly one, and an ending with none is not "
                f"recovery input", category="integrity", code="schema")
    output = named[0]
    content = output.get("content_manifest")
    artifact = output.get("artifact")
    if type(content) is not dict or type(artifact) is not dict:
        _refuse(f"the frozen {name_value(output['name'])} output is not "
                f"present with both its artifact and its content manifest; a "
                f"candidate is not validated from an output nobody measured",
                category="integrity", code="schema")
    if artifact.get("artifact_id") != f"{attempt_id}:{output['name']}":
        _refuse(f"the frozen candidate artifact "
                f"{name_value(artifact.get('artifact_id'))} is not the one "
                f"this attempt's own seal composed; it is not evidence about "
                f"attempt {name_value(attempt_id)}",
                category="integrity", code="schema")
    rows = [one for one in frozen["artifacts"]
            if one["output_name"] == output["name"]]
    if len(rows) != 1 \
            or rows[0]["artifact_id"] != artifact.get("artifact_id") \
            or rows[0]["content_digest"] != artifact.get("content_digest") \
            or rows[0]["locator"] != artifact.get("locator"):
        _refuse("this manager's recorded artifact row and its retained "
                "result manifest disagree about the frozen candidate, so "
                "neither is read as validated recovery input",
                category="integrity", code="digest")
    if artifact.get("content_digest") != content.get("tree_digest"):
        _refuse(f"the frozen candidate names content digest "
                f"{name_value(artifact.get('content_digest'))} and the tree "
                f"this manager measured digests to "
                f"{name_value(content.get('tree_digest'))}; a candidate is "
                f"bound to the bytes that were sealed",
                category="integrity", code="digest")
    metadata = output.get("result_metadata")
    if type(metadata) is not dict or CANDIDATE_CLAIM not in metadata \
            or ORDINARY_TESTS not in metadata:
        _refuse(f"the frozen candidate carries no "
                f"{name_value(CANDIDATE_CLAIM)} claim beside its "
                f"{name_value(ORDINARY_TESTS)} observation; what a turn "
                f"produced and what its own command did are both the "
                f"producer's facts and this manager will not invent either",
                category="integrity", code="schema")
    claim = boundaries.document(metadata[CANDIDATE_CLAIM],
                                "a worker candidate claim",
                                required=CLAIM_MEMBERS)
    observed = boundaries.document(metadata[ORDINARY_TESTS],
                                   "a worker ordinary-test observation",
                                   required=TESTS_MEMBERS)
    for member in ("base", "head", "transport"):
        boundaries.text(claim[member], f"a claimed candidate {member}")
    boundaries.identity(observed["task_id"], "an observed task id")
    boundaries.text(observed["task_digest"], "an observed task digest")
    for member in ("base", "head"):
        if observed[member] != claim[member]:
            _refuse(f"the candidate claim names {member} "
                    f"{name_value(claim[member])} and its own ordinary-test "
                    f"observation names {name_value(observed[member])}; two "
                    f"accounts of one candidate are not resolved by picking "
                    f"a half", category="ambiguous", code="collection")
    return output, claim, observed


def _argv(observed):
    """The ORIGINAL verification command, as the words it actually was.

    A LIST OF WORDS AND NEVER A STRING. `integration.driver._observation_of`'s
    rule, for its reason: "a command this module would have to assemble from a
    string is a shell, and there is no shell here". The bound is on the words
    and on their bytes, because this travels into a durable record.
    """
    argv = observed["argv"]
    if type(argv) is not list or not argv \
            or not all(type(one) is str and one for one in argv):
        _refuse("an ordinary-test observation names its command as a "
                "non-empty list of words", category="integrity", code="schema")
    if len(argv) > MAX_ARGV_WORDS \
            or len(json.dumps(argv).encode("utf-8")) > MAX_ARGV_BYTES:
        _refuse(f"the observed verification command is bounded at "
                f"{MAX_ARGV_WORDS} words and {MAX_ARGV_BYTES} bytes",
                category="integrity", code="schema")
    return list(argv)


def _declared(control, attempt_id, observed):
    """The worker's own typed declaration about this ending, PROVED.

    READ THROUGH ITS OWNER. `worker_manager.failure_cause` composes it from
    this manager's own frozen row and the `result.json` the same seal
    MEASURED, member by member, each one known with its source or unknown
    with a bounded reason. Nothing here re-reads a file or re-derives a digest.

    THE THREE CLAUSES THAT MAKE THIS TRIGGER THIS TRIGGER:
      the declared ending is `verification-failed`;
      a verification was ATTEMPTED and reported a NON-ZERO status;
      and the PROVIDER SUCCEEDED -- which the declared ending itself
      establishes, because the worker's own `_disposition` reaches
      `provider-failed` before it can reach this word, and which is checked
      again here by requiring that it named no provider failure reason.
    """
    composed = failure_cause.attempt_failure_cause_of(control, attempt_id)
    if composed is None:
        _refuse(f"this manager holds no attempt {name_value(attempt_id)}; a "
                f"terminal ending is attributed through the owner that holds "
                f"the attempt")
    held = failure_cause.declaration_of(composed)
    if held is None:
        _refuse(f"this manager composed no worker declaration for attempt "
                f"{name_value(attempt_id)}; an ending with no typed "
                f"declaration is not classified by inference")

    def member(name):
        return failure_cause.decode(held[name])

    known, ending = member("declared_ending")
    if not known or ending != TRIGGER_ENDING:
        _refuse(f"attempt {name_value(attempt_id)} declared "
                f"{name_value(ending) if known else 'no owned ending'} and "
                f"this trigger is {name_value(TRIGGER_ENDING)}; general "
                f"exceptional-ending classification is a separately "
                f"delivered capability and is not widened here")
    known, attempted = member("verification_attempted")
    if not known or attempted is not True:
        _refuse(f"attempt {name_value(attempt_id)} does not declare that a "
                f"verification command ran; an unrun or unknown command is "
                f"the absence of evidence and is not a verification failure")
    known, status = member("verification_status")
    if not known:
        _refuse(f"attempt {name_value(attempt_id)} declares no verification "
                f"exit status this manager can own; an unknown status is not "
                f"read as a failure")
    if status == 0:
        _refuse(f"attempt {name_value(attempt_id)} declares verification "
                f"status 0; a passed command is not this trigger",
                category="integrity", code="schema")
    if status != observed["status"]:
        _refuse(f"the retained result declares verification status "
                f"{name_value(status)} and the candidate's own ordinary-test "
                f"observation names {name_value(observed['status'])}; one "
                f"ending has one account of its command",
                category="ambiguous", code="collection")
    reason_known, reason = member("failure_reason")
    if reason_known:
        _refuse(f"attempt {name_value(attempt_id)} names provider failure "
                f"reason {name_value(reason)}; this trigger requires a "
                f"SUCCESSFUL provider turn whose required verification "
                f"failed, and a provider failure is a different ending")
    return composed, held, status


def _cessation(composed):
    """The original runtime's cessation axis, carried WITH its qualification.

    REC-4 and the contract's section 4: "unknown is a hold, not proof of
    safety". An `unknown` therefore travels as an unknown and is recorded as
    one. It does NOT stop the analysis -- an analysis reads fixed evidence and
    starts no runtime, so an unresolved old writer cannot be displaced by it
    -- and it does not authorize any replacement either, which is W385624's
    and W385625's question rather than this module's.
    """
    answer = failure_cause.answer_of(composed)
    cause = composed.get("cause")
    held = {"answer": answer, "qualified": answer == "unknown",
            "absent_records": list(failure_cause.absent_of(composed))}
    if cause is None:
        held.update({"component": None, "operation_id": None,
                     "cessation": None, "effects": []})
        return held
    known_component, component = failure_cause.decode(cause["component"])
    known_operation, operation = failure_cause.decode(cause["operation_id"])
    known_cessation, ceased = failure_cause.decode(cause["cessation"])
    known_effects, effects = failure_cause.decode(cause["effects"])
    held.update({
        "component": component if known_component else None,
        "operation_id": operation if known_operation else None,
        "cessation": ceased if known_cessation else None,
        "effects": sorted(effects) if known_effects else []})
    if not known_cessation or ceased == "unknown":
        held["qualified"] = True
    return held


def classified_failure(control, attempt_id, *, declaration=None):
    """WHAT ONE TERMINAL ENDING WAS, and whether it is this trigger at all.

    Answers the validated facts or REFUSES. Read-only: it opens no
    transaction, writes nothing and decides nothing about recovery. Repeated
    reads answer identically.

    `declaration` IS OPTIONAL HERE AND REQUIRED BY THE DRIVER. When it is
    supplied, this refuses an ending produced BY the declared analysis
    participant -- the configuration half of the recursion exclusion, which
    the contract states by name: "Analysis-role failures are explicitly
    excluded from recursive triggering."
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    frozen, result, fixed = _retained(control, attempt_id)
    if declaration is not None:
        held = check_analysis_declaration(declaration)
        if fixed["participant"] == held["participant"]:
            _denied(f"attempt {name_value(attempt_id)} was executed by the "
                    f"declared analysis participant "
                    f"{name_value(held['participant'])}; an analysis-role "
                    f"ending never triggers another analysis")
    output, claim, observed = _candidate(frozen, result, attempt_id)
    composed, _held, status = _declared(control, attempt_id, observed)
    return {"attempt_id": attempt_id,
            "authority_uuid": fixed["authority_uuid"],
            "work_id": fixed["work_id"],
            "participant": fixed["participant"],
            "principal": fixed["principal"],
            "generation": fixed["generation"],
            "result_id": frozen["result_id"],
            "manifest_digest": frozen["manifest_digest"],
            "frozen_at": frozen["frozen_at"],
            "disposition": frozen["disposition"],
            "declared_ending": TRIGGER_ENDING,
            "input_manifest_digest": result["input_manifest_digest"],
            "candidate": {"output": output["name"],
                          "base": claim["base"], "head": claim["head"],
                          "transport": claim["transport"],
                          "artifact_id": output["artifact"]["artifact_id"],
                          "content_digest":
                              output["artifact"]["content_digest"],
                          "tree_digest":
                              output["content_manifest"]["tree_digest"],
                          "entry_count":
                              output["content_manifest"]["entry_count"],
                          "locator": output["artifact"]["locator"]},
            "verification": {"attempted": True, "status": status,
                             "argv": _argv(observed),
                             "task_id": observed["task_id"],
                             "task_digest": observed["task_digest"]},
            "cessation": _cessation(composed)}


# -- 5. the fixed analysis input ---------------------------------------------

INPUT_SCHEMA = "baton.v12.recovery-analysis-input/1"


def analysis_input(classified, *, failure_key, job_id, stage_id, episode):
    """THE IMMUTABLE DOCUMENT ONE ANALYSIS IS ABOUT.

    Composed once from the classified ending and this store's own stage
    selectors, digested, and compared AGAIN when the report arrives. Which is
    the whole point: an agent that received this input and answered about
    something else is refused, and an evidence set that changed under a
    running analysis invalidates the report rather than the evidence.

    PATHS TRAVEL AS LOCATORS AND NEVER AS AUTHORITY. The contract keeps that
    distinction: a custody locator identifies where this manager sealed a
    tree; it is not permission for a reader to open arbitrary host files, and
    nothing in this module follows one.
    """
    boundaries.identity(failure_key, "a failure key")
    boundaries.identity(job_id, "a Job id")
    boundaries.identity(stage_id, "a stage id")
    boundaries.generation(episode, "an episode number")
    return {
        "schema": INPUT_SCHEMA,
        "failure_key": failure_key,
        "selectors": {"authority_uuid": classified["authority_uuid"],
                      "work_id": classified["work_id"], "job_id": job_id,
                      "stage_id": stage_id, "episode": episode,
                      "attempt_id": classified["attempt_id"],
                      "result_id": classified["result_id"]},
        "task": {"task_id": classified["verification"]["task_id"],
                 "task_digest": classified["verification"]["task_digest"],
                 "input_manifest_digest": classified["input_manifest_digest"]},
        "execution": {"participant": classified["participant"],
                      "principal": classified["principal"],
                      "generation": classified["generation"],
                      "declared_ending": classified["declared_ending"],
                      "disposition": classified["disposition"],
                      "manifest_digest": classified["manifest_digest"],
                      "frozen_at": classified["frozen_at"]},
        "candidate": dict(classified["candidate"]),
        "verification": dict(classified["verification"]),
        "cessation": dict(classified["cessation"]),
    }


def input_digest(document):
    """The canonical identity of one fixed analysis input."""
    return digest(own(document, what="a fixed analysis input"))


# -- 6. the analysis report document -----------------------------------------

REPORT_SCHEMA = "baton.v12.recovery-analysis-report/1"
REPORT_MEMBERS = ("schema", "failure_key", "input_digest", "facts",
                  "hypotheses", "options", "recommendation",
                  "proposed_verification")
OPTION_MEMBERS = ("option", "tradeoff")
PROPOSED_MEMBERS = ("argv", "context_digest")

MAX_REPORT_BYTES = 1 << 16
MAX_REPORT_ENTRIES = 32
MAX_REPORT_TEXT = 2048


def report_digest(document):
    return digest(own(document, what="an analysis report"))


def _bounded_list(value, what, *, allow_empty=False):
    if type(value) is not list:
        _refuse(f"{what} is a list", category="integrity", code="schema")
    if not value and not allow_empty:
        _refuse(f"{what} is non-empty", category="integrity", code="schema")
    if len(value) > MAX_REPORT_ENTRIES:
        _refuse(f"{what} carries at most {MAX_REPORT_ENTRIES} entries",
                category="integrity", code="schema")
    return value


def _bounded_text(value, what):
    boundaries.text(value, what)
    if len(value.encode("utf-8")) > MAX_REPORT_TEXT:
        _refuse(f"{what} is bounded at {MAX_REPORT_TEXT} bytes",
                category="integrity", code="schema")
    return value


def check_analysis_report(document, *, what="an analysis report"):
    """The closed validator for what an analysis is permitted to author.

    FACTS AND HYPOTHESES ARE SEPARATE MEMBERS, which is the contract's own
    requirement -- "diagnosis separating facts from hypotheses" -- and it is a
    SHAPE rule rather than a quality judgement. This build does not grade a
    diagnosis; it requires the producer to say which of its sentences it is
    standing behind. A report that mixed them would be read by an owner as
    though every line were observed.

    A RECOMMENDATION IS NOT AN AUTHORIZATION. The member exists because the
    owner is owed one; nothing downstream of here consumes it as permission,
    and `proposed_verification` is explicitly a PROPOSAL -- the owner approves
    an exact correction under W385624, and this module admits nothing.
    """
    taken = own(document, what=what)
    if type(taken) is not dict:
        _refuse(f"{what} is one closed object; this is {name_value(document)}",
                category="integrity", code="schema")
    missing = [one for one in REPORT_MEMBERS if one not in taken]
    extra = sorted(one for one in taken if one not in REPORT_MEMBERS)
    if missing or extra:
        _refuse(f"{what} is exactly {', '.join(REPORT_MEMBERS)}"
                + (f"; missing {', '.join(missing)}" if missing else "")
                + (f"; unexpected {', '.join(extra)}" if extra else ""),
                category="integrity", code="schema")
    if taken["schema"] != REPORT_SCHEMA:
        _denied(f"{what} says it is {name_value(taken['schema'])} and this "
                f"build reads exactly {name_value(REPORT_SCHEMA)}")
    if len(json.dumps(taken).encode("utf-8")) > MAX_REPORT_BYTES:
        _refuse(f"{what} is a bounded report; a diagnosis larger than "
                f"{MAX_REPORT_BYTES} bytes is not made durable here",
                category="integrity", code="schema")
    boundaries.identity(taken["failure_key"], "an analysed failure key")
    boundaries.text(taken["input_digest"], "an analysed input digest")
    for member in ("facts", "hypotheses"):
        # HYPOTHESES MAY BE EMPTY AND FACTS MAY NOT. A diagnosis that observed
        # nothing is not one; a diagnosis that needed to guess nothing is.
        for one in _bounded_list(taken[member], f"{what}'s {member}",
                                 allow_empty=member == "hypotheses"):
            _bounded_text(one, f"one of {what}'s {member}")
    for one in _bounded_list(taken["options"], f"{what}'s options"):
        held = boundaries.document(one, f"one of {what}'s options",
                                   required=OPTION_MEMBERS)
        for member in OPTION_MEMBERS:
            _bounded_text(held[member], f"an option's {member}")
    _bounded_text(taken["recommendation"], f"{what}'s recommendation")
    proposed = taken["proposed_verification"]
    if proposed is not None:
        held = boundaries.document(proposed, f"{what}'s proposed verification",
                                   required=PROPOSED_MEMBERS)
        argv = held["argv"]
        if type(argv) is not list or not argv \
                or not all(type(one) is str and one for one in argv) \
                or len(argv) > MAX_ARGV_WORDS:
            _refuse(f"{what} proposes its corrected command as a bounded "
                    f"non-empty list of words; a command somebody would have "
                    f"to assemble from a string is a shell",
                    category="integrity", code="schema")
        boundaries.text(held["context_digest"],
                        "a proposed execution context digest")
    return taken


# -- 7. the durable records --------------------------------------------------
#
# FIVE KINDS, ALL ORDINARY OPERATIONS OF THIS STORE'S EXISTING JOURNAL, taken
# through `transact` under deterministic identities derived from the FAILURE
# KEY. No schema changes and no new table: the journal already supplies exact
# replay, collision on changed operands and a committed result that later
# incarnations read instead of re-deciding.
FAILURE_KIND = "recovery.failure"
INTENT_KIND = "recovery.analysis-intent"
DISPATCH_KIND = "recovery.analysis-dispatch"
REPORT_KIND = "recovery.analysis-report"
OWNER_ITEM_KIND = "recovery.owner-item"

FAILURE_MEMBERS = ("failure_key", "selectors", "job_id", "stage_id",
                   "episode", "candidate", "verification", "execution",
                   "cessation", "input_digest", "disposition")
INTENT_MEMBERS = ("failure_key", "job_id", "stage_id", "input_digest",
                  "declaration_digest", "role", "participant", "principal",
                  "worker_id", "profile", "profile_digest", "policy",
                  "deadlines")
DISPATCH_MEMBERS = ("failure_key", "job_id", "analysis_attempt_id",
                    "input_digest", "declaration_digest", "participant",
                    "intended_at")
REPORT_MEMBERS_RECORD = ("failure_key", "job_id", "analysis_attempt_id",
                         "input_digest", "report_digest", "result_id",
                         "manifest_digest", "outputs", "ending")
OWNER_ITEM_MEMBERS = ("failure_key", "job_id", "outcome", "destination",
                      "input_digest", "report_digest", "partials", "why",
                      "delivered_at")

# THE RECOVERY DISPOSITION VOCABULARY, closed and DERIVED. The failure record
# is written once and never updated -- this journal has no update -- so the
# CURRENT disposition is answered from which records exist rather than stored
# and moved. A stored-and-moved disposition is the second account of a state
# this package's own projection rule forbids.
DISPOSITIONS = ("analysis-owed", "analysis-intended", "analysis-dispatched",
                "analysis-reported", "delivered")

# WHAT ONE OWNER ITEM SAYS HAPPENED. `reported` is the ordinary ending; the
# other four are the finite endpoints, and they are FOUR rather than one
# because an owner looking at a held recovery needs to know which of them it
# is. `unknown-cessation` is not a failure: it is an analysis whose own
# runtime this manager cannot account for, which excludes replacement.
REPORTED_OUTCOME = "reported"
ENDPOINT_OUTCOMES = ("analysis-failed", "analysis-expired",
                     "analysis-cancelled", "analysis-unknown-cessation")
OWNER_OUTCOMES = (REPORTED_OUTCOME,) + ENDPOINT_OUTCOMES

MAX_PARTIAL_ENTRIES = 16
PARTIAL_MEMBERS = ("name", "content_digest", "bytes")


def _operation_id(kind, key):
    boundaries.identity(key, "a failure key")
    return f"{kind}:{key}"


def failure_operation_id(key):
    return _operation_id(FAILURE_KIND, key)


def intent_operation_id(key):
    """ONE analysis per failure key, and this identity is what enforces it.

    Derived from the KEY and from nothing about the observer: a second
    publication of the same ending, a concurrent sweep and a restarted
    incarnation all compute this name and all replay the first record.
    """
    return _operation_id(INTENT_KIND, key)


def dispatch_operation_id(key):
    return _operation_id(DISPATCH_KIND, key)


def report_operation_id(key):
    return _operation_id(REPORT_KIND, key)


def owner_item_operation_id(key):
    """ONE owner item per failure key. The ordinary report and every finite
    endpoint compete for this single identity, which is what makes "delivers
    one owner item" true of the whole path rather than of one branch."""
    return _operation_id(OWNER_ITEM_KIND, key)


def _committed(store, kind, operation_id, members, key):
    """One committed record of this store's journal, PROVED to be this
    failure's.

    A SIGNATURE IS NOT OWNERSHIP -- `ending._committed`'s correction and
    `native_handoffs._committed`'s restatement, which applies here for its
    reason: a well-made record of ANOTHER failure, copied through the public
    journal to this identity, would otherwise read as this one's. So the
    record's own key is compared back against the key it was selected by.
    """
    row = store._connection.execute(
        "SELECT state, result FROM operations WHERE operation_id = ? AND "
        "kind = ?", (operation_id, kind)).fetchone()
    if row is None or row["state"] != "committed" or row["result"] is None:
        return None
    record = json.loads(row["result"])
    if type(record) is not dict or any(one not in record for one in members):
        _refuse(f"the committed {kind} record at "
                f"{name_value(operation_id)} is not one this build can read",
                category="integrity", code="schema")
    if record["failure_key"] != key:
        _refuse(f"the committed {kind} record at {name_value(operation_id)} "
                f"names failure {name_value(record['failure_key'])} and it "
                f"was selected as {name_value(key)}; a record is proved to be "
                f"this failure's rather than merely well made",
                category="integrity", code="schema")
    return record


def failure_of(store, key):
    return _committed(store, FAILURE_KIND, failure_operation_id(key),
                      FAILURE_MEMBERS, key)


def intent_of(store, key):
    return _committed(store, INTENT_KIND, intent_operation_id(key),
                      INTENT_MEMBERS, key)


def dispatch_of(store, key):
    return _committed(store, DISPATCH_KIND, dispatch_operation_id(key),
                      DISPATCH_MEMBERS, key)


def report_of(store, key):
    return _committed(store, REPORT_KIND, report_operation_id(key),
                      REPORT_MEMBERS_RECORD, key)


def owner_item_of(store, key):
    return _committed(store, OWNER_ITEM_KIND, owner_item_operation_id(key),
                      OWNER_ITEM_MEMBERS, key)


def failures_of(store):
    """Every failure record this store holds, by key."""
    held = {}
    for row in store._connection.execute(
            "SELECT result FROM operations WHERE kind = ? AND state = "
            "'committed' AND result IS NOT NULL", (FAILURE_KIND,)):
        record = json.loads(row["result"])
        held[record["failure_key"]] = record
    return held


def recovery_disposition(store, key):
    """THE CURRENT recovery disposition of one failure, derived from records.

    Answers `None` for a key this store holds no failure for. Pure: it reads
    this database and writes nothing, so a status read and a guard inside
    another owner's transaction get the same answer.
    """
    if failure_of(store, key) is None:
        return None
    if owner_item_of(store, key) is not None:
        return "delivered"
    if report_of(store, key) is not None:
        return "analysis-reported"
    if dispatch_of(store, key) is not None:
        return "analysis-dispatched"
    if intent_of(store, key) is not None:
        return "analysis-intended"
    return "analysis-owed"


def _stage_row(store, stage_id):
    for row in submission.stage_rows(store):
        if row["stage_id"] == stage_id:
            return row
    _refuse(f"this store carries no stage {name_value(stage_id)}; a recovery "
            f"record belongs to a stage of this Job store")


def record_failure(store, *, classified, job_id, stage_id, episode):
    """Journal the failure/recovery item for ONE terminal ending.

    EVERY SELECTOR IS READ FROM THIS STORE rather than accepted: the Job and
    the Work come from the stage row, so a caller cannot file a failure
    against a stage it names incorrectly or attribute one Job's ending to
    another. The Authority is compared too -- this store is opened bound to
    one, and an attempt of a different Authority is not this store's failure.

    REPLAY IS THE JOURNAL'S. The same ending under the same key replays this
    record; changed operands collide, which is what stops one ending from
    being recorded as two different failures.
    """
    stage = _stage_row(store, stage_id)
    if stage["job_id"] != job_id:
        _refuse(f"stage {name_value(stage_id)} belongs to Job "
                f"{name_value(stage['job_id'])} and this failure is filed "
                f"against {name_value(job_id)}",
                category="integrity", code="schema")
    if stage["work_id"] != classified["work_id"]:
        _refuse(f"stage {name_value(stage_id)} names Work "
                f"{name_value(stage['work_id'])} and the failed attempt was "
                f"assigned {name_value(classified['work_id'])}; an ending is "
                f"attributed to the Work that was executing",
                category="integrity", code="schema")
    if store.authority_uuid != classified["authority_uuid"]:
        _refuse(f"this Job store is bound to Authority "
                f"{name_value(store.authority_uuid)} and the failed attempt "
                f"names {name_value(classified['authority_uuid'])}; one "
                f"store's records are one Authority's",
                category="integrity", code="schema")
    key = failure_key(authority_uuid=classified["authority_uuid"],
                      work_id=classified["work_id"], job_id=job_id,
                      stage_id=stage_id, attempt_id=classified["attempt_id"],
                      result_id=classified["result_id"])
    fixed = analysis_input(classified, failure_key=key, job_id=job_id,
                           stage_id=stage_id, episode=episode)
    record = {
        "failure_key": key,
        "selectors": dict(fixed["selectors"]),
        "job_id": job_id, "stage_id": stage_id, "episode": episode,
        "candidate": dict(classified["candidate"]),
        "verification": dict(classified["verification"]),
        "execution": dict(fixed["execution"]),
        "cessation": dict(classified["cessation"]),
        "input_digest": input_digest(fixed),
        # THE DISPOSITION THIS RECORD IS BORN WITH, and the only one it ever
        # carries. `recovery_disposition` answers the current one.
        "disposition": DISPOSITIONS[0]}
    operation_id = failure_operation_id(key)
    return store.transact(
        operation_id, FAILURE_KIND, job_signature(FAILURE_KIND, record),
        lambda connection: record)


def _not_ended(store, key, what):
    """A delivered owner item is TERMINAL for this failure's analysis.

    The contract's finite endpoint: analysis failure, expiry or cancellation
    "preserves available evidence and goes directly to Slawomir without retry
    or recursive analysis". So once an owner item exists, a second intent, a
    second dispatch and a second report are all refused -- which is what makes
    "no automatic retry" a property of the records rather than of a caller's
    restraint.
    """
    held = owner_item_of(store, key)
    if held is not None:
        _denied(f"failure {name_value(key)} already delivered owner item "
                f"{name_value(held['outcome'])}; {what} would be an automatic "
                f"retry of a finite analysis, and a later disposition is a "
                f"new attributable act of the owner's rather than this "
                f"manager's")
    return held


def record_analysis_intent(store, *, key, declaration, admitted_at):
    """Journal the analysis intent BEFORE any admission or dispatch.

    REC-3: durable intent before an external effect. This record is what makes
    a crash between "we decided to analyse" and "we launched something"
    recoverable -- a later incarnation reads it, finds the same identity, the
    same input digest and the same admitted deadlines, and continues rather
    than re-deciding.

    AND IT PINS THE DECLARED AUTHORITY AND THE PROFILE AT ADMISSION. Who
    analyses, under whose principal, and under which owner-approved finite
    bounds are facts about THIS admission; a configuration change afterwards
    does not reinterpret it, which is `execution_limits`' generation rule
    applied to a profile selection.
    """
    held = check_analysis_declaration(declaration)
    failure = failure_of(store, key)
    if failure is None:
        _refuse(f"this store holds no failure {name_value(key)}; an analysis "
                f"intent is recorded for an attributed ending and never for "
                f"an unrecorded one")
    _not_ended(store, key, "a second analysis intent")
    policy = resolved_profile(held["profile"])
    record = {
        "failure_key": key, "job_id": failure["job_id"],
        "stage_id": failure["stage_id"],
        "input_digest": failure["input_digest"],
        "declaration_digest": declaration_digest(held),
        "role": held["role"], "participant": held["participant"],
        "principal": held["principal"], "worker_id": held["worker_id"],
        "profile": held["profile"], "profile_digest": held["profile_digest"],
        "policy": policy,
        "deadlines": admitted_deadlines(policy, admitted_at=admitted_at)}
    # THE REPLAY IDENTITY IS THE DECISION AND NOT THE CLOCK THAT NOTICED IT.
    # `job_control.record_within`'s split, for its reason: the committed
    # record carries the admission instant and the deadlines derived from it,
    # and the SIGNATURE carries the facts that make this the same analysis --
    # the failure, its fixed input, the declared authority and the selected
    # profile. A signature that included the observer's clock would make a
    # second observation of one ending a COLLISION instead of a replay, which
    # is precisely the duplicate-delivery defect this record exists to
    # prevent; a changed declaration or a changed input still collides.
    operands = {name: record[name] for name in INTENT_MEMBERS
                if name != "deadlines"}
    operation_id = intent_operation_id(key)
    return store.transact(
        operation_id, INTENT_KIND, job_signature(INTENT_KIND, operands),
        lambda connection: record)


def record_dispatch(store, *, key, analysis_attempt_id, intended_at):
    """Journal the DISPATCH INTENT, before the launch it is about.

    THE FENCE AGAINST A SECOND PROVIDER TURN. The identity is the failure
    key's, so a lost launch reply, a restart and a concurrent observer all
    reach this one record; `reconciled_dispatch` then answers what actually
    happened, and a state it cannot establish HOLDS instead of launching
    again. Message deduplication alone is explicitly not claimed to make a
    provider execution exactly-once; what is claimed is that this manager
    never orders a second one.
    """
    boundaries.identity(analysis_attempt_id, "an analysis runtime attempt id")
    boundaries.instant(intended_at, "an analysis dispatch intent instant")
    intent = intent_of(store, key)
    if intent is None:
        _refuse(f"this store holds no analysis intent for failure "
                f"{name_value(key)}; a dispatch is never the first durable "
                f"record of an analysis")
    _not_ended(store, key, "a second analysis dispatch")
    record = {"failure_key": key, "job_id": intent["job_id"],
              "analysis_attempt_id": analysis_attempt_id,
              "input_digest": intent["input_digest"],
              "declaration_digest": intent["declaration_digest"],
              "participant": intent["participant"],
              "intended_at": intended_at}
    # The same split as the intent: the ATTEMPT IDENTITY is in the signature,
    # so a second execution for one failure collides, and the instant is not,
    # so a re-entry at a later clock replays the committed record.
    operands = {name: record[name] for name in DISPATCH_MEMBERS
                if name != "intended_at"}
    operation_id = dispatch_operation_id(key)
    return store.transact(
        operation_id, DISPATCH_KIND, job_signature(DISPATCH_KIND, operands),
        lambda connection: record)


def record_analysis_report(store, *, key, analysis_attempt_id, report,
                           result_id, manifest_digest, outputs, ending):
    """Journal the analysis execution and its report.

    WHAT IS JOURNALLED IS A BINDING, NOT A BODY. The report's own digest, the
    result it was read out of, the outputs the analysis actually wrote and the
    ending it reached -- so an owner reading this record can resolve the exact
    bytes, and this store never becomes a second copy of a diagnosis.
    """
    held = check_analysis_report(report)
    intent = intent_of(store, key)
    if intent is None:
        _refuse(f"this store holds no analysis intent for failure "
                f"{name_value(key)}")
    _not_ended(store, key, "a second analysis report")
    if held["failure_key"] != key:
        _refuse(f"the report names failure {name_value(held['failure_key'])} "
                f"and it is recorded against {name_value(key)}; an analysis "
                f"of another failure is not evidence about this one",
                category="integrity", code="schema")
    if held["input_digest"] != intent["input_digest"]:
        _refuse(f"the report names input {name_value(held['input_digest'])} "
                f"and this analysis was admitted on "
                f"{name_value(intent['input_digest'])}; a diagnosis is about "
                f"the fixed evidence its intent named",
                category="integrity", code="digest")
    record = {"failure_key": key, "job_id": intent["job_id"],
              "analysis_attempt_id": analysis_attempt_id,
              "input_digest": intent["input_digest"],
              "report_digest": report_digest(held),
              "result_id": result_id, "manifest_digest": manifest_digest,
              "outputs": sorted(outputs), "ending": ending}
    operation_id = report_operation_id(key)
    return store.transact(
        operation_id, REPORT_KIND, job_signature(REPORT_KIND, record),
        lambda connection: record)


def _partials(value):
    """The partial outputs a stopped analysis had written, bounded.

    PRESERVED RATHER THAN DISCARDED, which is the contract's requirement at
    every finite endpoint, and carried as IDENTITIES: a name, the digest this
    manager measured and the bytes it measured. A record that copied the
    material would be this store holding a second account of a custody tree.
    """
    if type(value) is not list:
        _refuse("the preserved partial outputs are a list",
                category="integrity", code="schema")
    if len(value) > MAX_PARTIAL_ENTRIES:
        _refuse(f"at most {MAX_PARTIAL_ENTRIES} partial outputs are preserved "
                f"as identities", category="integrity", code="schema")
    held = []
    for one in value:
        entry = boundaries.document(one, "a preserved partial output",
                                    required=PARTIAL_MEMBERS)
        if entry["name"] not in PERMITTED_OUTPUTS:
            _denied(f"a preserved partial output is named "
                    f"{name_value(entry['name'])}; an analysis may have "
                    f"written only {', '.join(PERMITTED_OUTPUTS)}, and "
                    f"preserving anything else would be retaining material "
                    f"the role was never permitted to author")
        boundaries.text(entry["content_digest"], "a partial output digest")
        if type(entry["bytes"]) is not int or type(entry["bytes"]) is bool \
                or entry["bytes"] < 0:
            _refuse("a preserved partial output's measured bytes is a "
                    "non-negative whole number",
                    category="integrity", code="schema")
        held.append({name: entry[name] for name in PARTIAL_MEMBERS})
    return sorted(held, key=lambda one: one["name"])


def record_owner_item(store, *, key, outcome, destination, delivered_at,
                      report=None, partials=(), why=None):
    """Journal THE ONE owner item this failure delivers.

    ONE IDENTITY FOR EVERY BRANCH. The ordinary report and all four finite
    endpoints commit under `owner_item_operation_id`, so the first to reach it
    wins and every later observer of the same durable facts REPLAYS it. That
    is what makes duplicate delivery impossible rather than unlikely: a second
    notification of the same ending recomputes this name and finds the answer
    already there.

    OWNER-FACING DELIVERY IS PART OF THIS PATH. The contract is explicit that
    there is "no coordinator arranging a review handoff" here: the record
    names the configured destination and the exact digests the owner needs,
    and nothing downstream is required to notice it for the delivery to have
    happened.
    """
    boundaries.text(destination, "an owner item destination")
    boundaries.instant(delivered_at, "an owner item delivery instant")
    failure = failure_of(store, key)
    if failure is None:
        _refuse(f"this store holds no failure {name_value(key)}; an owner "
                f"item is delivered for an attributed ending")
    if outcome not in OWNER_OUTCOMES:
        _refuse(f"an owner item's outcome is one of "
                f"{', '.join(OWNER_OUTCOMES)}; this is {name_value(outcome)}",
                category="integrity", code="schema")
    # THE SHAPE IS PROVED BEFORE THE HISTORY IS READ. An item whose members
    # contradict its own outcome is a build defect in the caller, and
    # reporting it as "no report is journalled" would send whoever wrote it
    # looking at the journal for a mistake that is in the call.
    if outcome != REPORTED_OUTCOME:
        if report is not None:
            _refuse(f"an owner item with outcome {name_value(outcome)} "
                    f"delivers no analysis report; a failed, expired, "
                    f"cancelled or unaccounted analysis preserves its "
                    f"partial evidence and says so",
                    category="integrity", code="schema")
        _bounded_text(why, "the reason a finite analysis ended")
    elif why is not None:
        _refuse("a reported owner item carries its diagnosis in the report "
                "and no separate reason", category="integrity", code="schema")
    recorded = report_of(store, key)
    if outcome == REPORTED_OUTCOME:
        if recorded is None:
            _refuse(f"failure {name_value(key)} has no recorded analysis "
                    f"report; a {name_value(REPORTED_OUTCOME)} owner item is "
                    f"delivered from a journalled report and never from a "
                    f"caller's claim about one")
        if report is None or report_digest(check_analysis_report(report)) \
                != recorded["report_digest"]:
            _refuse(f"the delivered report does not digest to "
                    f"{name_value(recorded['report_digest'])}, which is what "
                    f"this failure's journalled analysis recorded",
                    category="integrity", code="digest")
    record = {"failure_key": key, "job_id": failure["job_id"],
              "outcome": outcome, "destination": destination,
              "input_digest": failure["input_digest"],
              "report_digest": (None if recorded is None
                                or outcome != REPORTED_OUTCOME
                                else recorded["report_digest"]),
              "partials": _partials(list(partials)), "why": why,
              "delivered_at": delivered_at}
    operands = {name: record[name] for name in OWNER_ITEM_MEMBERS
                if name != "delivered_at"}
    operation_id = owner_item_operation_id(key)
    return store.transact(
        operation_id, OWNER_ITEM_KIND,
        job_signature(OWNER_ITEM_KIND, operands), lambda connection: record)


# -- 8. reconciliation, cancellation and expiry ------------------------------

DISPATCH_STATES = ("none", "launched", "unknown")


def reconciled_dispatch(store, control, key):
    """WHAT HAPPENED TO A POSSIBLE ANALYSIS LAUNCH, as one of three answers.

    `none`      no dispatch intent is committed, so nothing was ordered and a
                dispatch may proceed.
    `launched`  the control store POSITIVELY holds the attempt this intent
                named, so the launch took effect and is that owner's to
                settle.
    `unknown`   a dispatch intent exists and the control store accounts for no
                such attempt. That is exactly the cut the intent exists for --
                "after possible launch with lost reply" -- and the answer is
                an actionable unknown with the operation and attempt named. It
                HOLDS. It is never read as "nothing was launched", because
                reading it that way is how a second provider turn happens.
    """
    held = dispatch_of(store, key)
    if held is None:
        return {"state": "none", "analysis_attempt_id": None, "why": None}
    attempt_id = held["analysis_attempt_id"]
    found = attempts.assignment_of(control, attempt_id) \
        if _attempt_held(control, attempt_id) else None
    if found is not None:
        if found["participant"] != held["participant"]:
            _refuse(f"analysis attempt {name_value(attempt_id)} is assigned "
                    f"to {name_value(found['participant'])} and this "
                    f"dispatch named {name_value(held['participant'])}; a "
                    f"reconciliation does not adopt another participant's "
                    f"execution", category="integrity", code="schema")
        return {"state": "launched", "analysis_attempt_id": attempt_id,
                "why": None}
    return {"state": "unknown", "analysis_attempt_id": attempt_id,
            "why": (f"dispatch intent "
                    f"{dispatch_operation_id(key)} named analysis attempt "
                    f"{attempt_id} and this manager's control store accounts "
                    f"for no such attempt; whether a turn was launched is "
                    f"unknown and no second one is ordered")}


def _attempt_held(control, attempt_id):
    row = control._connection.execute(
        "SELECT 1 FROM attempts WHERE runtime_attempt_id = ?",
        (attempt_id,)).fetchone()
    return row is not None


def expiry_reached(intent, now):
    """Whether this ADMITTED analysis has passed its own Job deadline.

    AGAINST THE PERSISTED DEADLINE AND NOT A FRESH DERIVATION. The deadline
    was fixed at admission from the owner-approved bound and the accepted
    admission instant, queue time included, so a restart on a later clock
    reaches the same instant. Job time includes queue: an analysis can expire
    before it has used a full stage window, and that is the approved bound
    rather than a defect.
    """
    boundaries.instant(now, "an expiry evaluation instant")
    return now >= intent["deadlines"]["job_deadline_at"]


# -- 9. the automatic path ---------------------------------------------------


def observe_terminal_failure(store, control, *, stage_id, episode, attempt_id,
                             declaration, now=None):
    """THE ONE AUTOMATIC ENTRY POINT: observe an ending, owe one analysis.

    Called where `native_handoffs.classified_handoff` is called -- on the
    ending, from durable state, before anything downstream consumes the
    attempt. It performs exactly two journal acts and no external effect: the
    failure/recovery item, and the analysis intent. Dispatch is a separate
    operation under a separate fence, because the intent must be durable
    before the effect it authorizes.

    IDEMPOTENT BY CONSTRUCTION. A second observation of the same ending
    computes the same key, replays both records and returns them. A delivered
    owner item makes it answer that item instead, which is the contract's
    "repeated publication/notification of the same ending does not create
    another analysis or owner item".
    """
    held = check_analysis_declaration(declaration)
    stage = _stage_row(store, stage_id)
    classified = classified_failure(control, attempt_id, declaration=held)
    _refuse_recursive(store, attempt_id)
    failure = record_failure(store, classified=classified,
                             job_id=stage["job_id"], stage_id=stage_id,
                             episode=episode)
    key = failure["failure_key"]
    delivered = owner_item_of(store, key)
    if delivered is not None:
        return {"failure": failure, "intent": intent_of(store, key),
                "owner_item": delivered,
                "disposition": recovery_disposition(store, key)}
    # CANCELLATION IS CHECKED AT ADMISSION AND AGAIN AT DISPATCH. A cancelled
    # Job earns no new admission: the fence is this store's own, read through
    # its owner, and a cancelled execution is never revived.
    cancellation.refuse_fenced(store._connection, stage["job_id"],
                               "admitting an analysis of its retained "
                               "verification failure")
    intent = record_analysis_intent(
        store, key=key, declaration=held,
        admitted_at=now if now is not None else store._now())
    return {"failure": failure, "intent": intent, "owner_item": None,
            "disposition": recovery_disposition(store, key)}


def _refuse_recursive(store, attempt_id):
    """The HISTORY half of the recursion exclusion.

    The configuration half is in `classified_failure`: an ending produced by
    the declared analysis participant is refused. This one is independent of
    configuration -- a deployment that renamed its analysis participant would
    lose the first check and keep this one -- because an attempt this store
    DISPATCHED as an analysis is an analysis whatever the current declaration
    says.
    """
    for row in store._connection.execute(
            "SELECT result FROM operations WHERE kind = ? AND state = "
            "'committed' AND result IS NOT NULL", (DISPATCH_KIND,)):
        record = json.loads(row["result"])
        if record.get("analysis_attempt_id") == attempt_id:
            _denied(f"attempt {name_value(attempt_id)} is the analysis this "
                    f"store dispatched for failure "
                    f"{name_value(record['failure_key'])}; an analysis-role "
                    f"ending never triggers another analysis")


def admit_dispatch(store, control, *, key, analysis_attempt_id, now):
    """Reserve and journal ONE analysis dispatch, or HOLD.

    The order is the ruling's: reconcile first, then recheck cancellation and
    expiry, then commit the intent, and only then may a caller launch. Every
    refusal below happens BEFORE the record, so a held dispatch has spent
    nothing.
    """
    intent = intent_of(store, key)
    if intent is None:
        _refuse(f"this store holds no analysis intent for failure "
                f"{name_value(key)}")
    _not_ended(store, key, "a second analysis dispatch")
    reconciled = reconciled_dispatch(store, control, key)
    if reconciled["state"] == "unknown":
        _refuse(reconciled["why"], category="ambiguous", code="operation")
    if reconciled["state"] == "launched":
        # AN EXACT REPLAY RETURNS THE COMMITTED RECORD. A caller presenting
        # another attempt identity for the same failure COLLIDES at the
        # journal, which is the point: one analysis has one execution.
        return record_dispatch(store, key=key,
                               analysis_attempt_id=analysis_attempt_id,
                               intended_at=dispatch_of(store,
                                                       key)["intended_at"])
    cancellation.refuse_fenced(store._connection, intent["job_id"],
                               "dispatching its analysis")
    # THE EXECUTION THIS DISPATCH IS ABOUT MUST BE THE DECLARED ANALYST'S,
    # checked BEFORE the record rather than after. An attempt the control
    # store already holds under another participant is somebody else's
    # execution, and binding a failure's analysis to it would attribute one
    # participant's work to another -- the exact attribution defect the whole
    # key exists to prevent. An attempt the control store does not hold yet is
    # the ordinary case: the reservation precedes the launch.
    if _attempt_held(control, analysis_attempt_id):
        found = attempts.assignment_of(control, analysis_attempt_id)
        if found["participant"] != intent["participant"]:
            _refuse(f"analysis attempt {name_value(analysis_attempt_id)} is "
                    f"assigned to {name_value(found['participant'])} and this "
                    f"analysis was admitted for "
                    f"{name_value(intent['participant'])}; a reconciliation "
                    f"does not adopt another participant's execution",
                    category="integrity", code="schema")
    if expiry_reached(intent, now):
        _refuse(f"the analysis of failure {name_value(key)} reached its "
                f"admitted deadline {name_value(intent['deadlines']['job_deadline_at'])} "
                f"at {name_value(now)}; an expired admission is not "
                f"dispatched and its owner item is delivered instead")
    return record_dispatch(store, key=key,
                           analysis_attempt_id=analysis_attempt_id,
                           intended_at=now)


def _analysis_result(control, *, attempt_id, participant):
    """The frozen analysis result, cross-bound, and PERMITTED OUTPUTS ONLY.

    THIS IS WHERE "ANALYSIS CANNOT MUTATE THE CANDIDATE" IS ENFORCED, and it
    is enforced on the EVIDENCE rather than on a promise: a frozen analysis
    result carrying any output outside `PERMITTED_OUTPUTS` -- a candidate, a
    proposal, a verifier input, a findings verdict -- is refused, and nothing
    downstream reads a report out of it. An analysis that produced a candidate
    did something it was not permitted to do, and the correct answer is a
    refusal rather than a selective read of the parts that look allowed.
    """
    frozen = frozen_output_of(control, attempt_id)
    if frozen is None:
        _refuse(f"analysis attempt {name_value(attempt_id)} froze no result; "
                f"a report is read from immutable output")
    result = load_manifest(control, frozen["manifest_digest"],
                           "resultManifest")
    if result is None:
        _refuse(f"this manager retains no result manifest at "
                f"{name_value(frozen['manifest_digest'])} for analysis "
                f"attempt {name_value(attempt_id)}")
    if result["result_id"] != frozen["result_id"]:
        _refuse("the frozen summary and its retained manifest name different "
                "results", category="integrity", code="schema")
    fixed = attempts.assignment_of(control, attempt_id)
    if fixed["participant"] != participant:
        _refuse(f"analysis attempt {name_value(attempt_id)} is assigned to "
                f"{name_value(fixed['participant'])} and this analysis was "
                f"admitted for {name_value(participant)}",
                category="integrity", code="schema")
    expected = {"work_ref": {"authority_uuid": fixed["authority_uuid"],
                             "work_id": fixed["work_id"]},
                "participant": fixed["participant"],
                "generation": fixed["generation"]}
    if result["assignment_ref"] != expected:
        _refuse("the frozen analysis result and the attempt do not name one "
                "assignment", category="integrity", code="schema")
    unpermitted = sorted(one["name"] for one in result["outputs"]
                         if one["name"] not in PERMITTED_OUTPUTS)
    if unpermitted:
        _denied(f"the frozen analysis result carries "
                f"{', '.join(name_value(one) for one in unpermitted)}; the "
                f"analysis role is permitted exactly "
                f"{', '.join(PERMITTED_OUTPUTS)} and may not author a "
                f"candidate, a verifier input or an execution decision")
    return frozen, result


def _report_output(result):
    """The one present, measured, artifact-backed report output.

    `native_handoffs._sole_output`'s rule: a document that says it is missing
    while carrying material contradicts itself, and a claim is not read from
    an output nobody measured.
    """
    matches = [one for one in result["outputs"]
               if one["name"] == ANALYSIS_OUTPUT]
    if len(matches) != 1:
        _refuse(f"the frozen analysis result carries {len(matches)} outputs "
                f"named {name_value(ANALYSIS_OUTPUT)}; a report is read from "
                f"exactly one", category="integrity", code="schema")
    output = matches[0]
    if output["status"] != "present" or output["artifact"] is None \
            or output["content_manifest"] is None:
        _refuse(f"the frozen {name_value(ANALYSIS_OUTPUT)} output is not "
                f"present with both its artifact and content manifest; a "
                f"report is not read from an output nobody measured")
    metadata = output.get("result_metadata")
    if type(metadata) is not dict or REPORT_SCHEMA not in metadata:
        _refuse(f"the frozen {name_value(ANALYSIS_OUTPUT)} output carries no "
                f"{name_value(REPORT_SCHEMA)} report; what an analysis "
                f"concluded is its own declaration and this manager will not "
                f"invent one")
    return output, metadata[REPORT_SCHEMA]


def preserved_partials(result):
    """The partial material a frozen analysis result actually carries.

    Read from the manifest the manager measured, so a preserved partial is a
    measurement rather than a worker's assertion. A `missing-optional` output
    contributes nothing: there is no material to preserve and inventing an
    entry for it would report evidence that does not exist.
    """
    held = []
    for one in result["outputs"]:
        if one["name"] not in PERMITTED_OUTPUTS \
                or one["status"] != "present" \
                or type(one.get("artifact")) is not dict:
            continue
        held.append({"name": one["name"],
                     "content_digest": one["artifact"]["content_digest"],
                     "bytes": one["artifact"]["bytes"]})
    return sorted(held, key=lambda one: one["name"])


def deliver_analysis(store, control, *, key, destination, now=None):
    """Read the completed analysis, journal its report, deliver the owner item.

    AUTOMATIC AND IN ONE PATH. The owner item is not a later tick's optional
    follow-up: a report that was recorded and never delivered would be the
    "analysis report alone" the contract explicitly refuses to call a usable
    result.

    THE ORIGINAL EVIDENCE IS REVALIDATED FIRST. The failure's own input digest
    is recomposed from the ORIGINAL attempt as it stands now and compared: an
    analysis of evidence that has since changed under it is refused rather
    than delivered, and the original candidate, task, command and failure are
    unchanged by everything here.
    """
    intent = intent_of(store, key)
    failure = failure_of(store, key)
    if intent is None or failure is None:
        _refuse(f"this store holds no admitted analysis for failure "
                f"{name_value(key)}")
    delivered = owner_item_of(store, key)
    if delivered is not None:
        return {"report": report_of(store, key), "owner_item": delivered,
                "disposition": recovery_disposition(store, key)}
    reconciled = reconciled_dispatch(store, control, key)
    if reconciled["state"] != "launched":
        _refuse(f"failure {name_value(key)} has no reconciled analysis "
                f"execution to read a report from; its dispatch is "
                f"{name_value(reconciled['state'])}",
                category="ambiguous", code="operation")
    current = classified_failure(control, failure["selectors"]["attempt_id"])
    fixed = analysis_input(current, failure_key=key,
                           job_id=failure["job_id"],
                           stage_id=failure["stage_id"],
                           episode=failure["episode"])
    if input_digest(fixed) != failure["input_digest"]:
        _refuse(f"the original evidence of failure {name_value(key)} now "
                f"digests to {name_value(input_digest(fixed))} and this "
                f"analysis was admitted on "
                f"{name_value(failure['input_digest'])}; a diagnosis of "
                f"evidence that changed under it is not delivered",
                category="integrity", code="digest")
    attempt_id = reconciled["analysis_attempt_id"]
    frozen, result = _analysis_result(control, attempt_id=attempt_id,
                                     participant=intent["participant"])
    output, report = _report_output(result)
    record = record_analysis_report(
        store, key=key, analysis_attempt_id=attempt_id, report=report,
        result_id=frozen["result_id"],
        manifest_digest=frozen["manifest_digest"],
        outputs=[one["name"] for one in result["outputs"]
                 if one["status"] == "present"],
        ending=frozen["disposition"])
    item = record_owner_item(
        store, key=key, outcome=REPORTED_OUTCOME, destination=destination,
        delivered_at=now if now is not None else store._now(),
        report=report, partials=preserved_partials(result))
    return {"report": record, "owner_item": item,
            "report_document": report, "report_output": output["name"],
            "disposition": recovery_disposition(store, key)}


def deliver_endpoint(store, control, *, key, outcome, why, destination,
                     now=None, partials=None):
    """THE FINITE ENDPOINT: preserve what exists, notify the owner, stop.

    One owner item, no retry, no recursive analysis and no replacement. The
    original failure and this analysis failure stay DISTINCT facts: the
    failure record is untouched and the item names which of the four endings
    this was.

    PARTIALS ARE MEASURED WHERE THERE IS A RESULT AND EMPTY WHERE THERE IS
    NOT. An analysis that expired before it was dispatched wrote nothing, and
    reporting a partial for it would be reporting evidence that does not
    exist; one that stopped mid-turn has whatever the manager sealed, read out
    of that manifest.
    """
    if outcome not in ENDPOINT_OUTCOMES:
        _refuse(f"a finite analysis endpoint is one of "
                f"{', '.join(ENDPOINT_OUTCOMES)}; this is "
                f"{name_value(outcome)}", category="integrity", code="schema")
    intent = intent_of(store, key)
    if intent is None:
        _refuse(f"this store holds no admitted analysis for failure "
                f"{name_value(key)}")
    delivered = owner_item_of(store, key)
    if delivered is not None:
        return {"owner_item": delivered,
                "disposition": recovery_disposition(store, key)}
    held = list(partials) if partials is not None else []
    if partials is None:
        reconciled = reconciled_dispatch(store, control, key)
        if reconciled["state"] == "launched":
            frozen = frozen_output_of(control,
                                      reconciled["analysis_attempt_id"])
            result = (load_manifest(control, frozen["manifest_digest"],
                                    "resultManifest")
                      if frozen is not None else None)
            if result is not None:
                held = preserved_partials(result)
    item = record_owner_item(
        store, key=key, outcome=outcome, destination=destination,
        delivered_at=now if now is not None else store._now(),
        partials=held, why=why)
    return {"owner_item": item,
            "disposition": recovery_disposition(store, key)}


# -- 10. the configured production path --------------------------------------
#
# WHAT SECTION 9 LEFT UNCONNECTED, and the correction is this section. Every
# operation above is an act a caller performs; nothing above decides WHEN to
# perform one, and a library nobody calls delivers no owner item. So this
# section is the AUTOMATIC half: a configured seam a deployment supplies, and
# one level-triggered pass the Job manager's own tick runs.
#
# LEVEL-TRIGGERED AND NOT EDGE-TRIGGERED, for `manager._launch`'s reason and
# with more force here. An edge hook on the ending would observe exactly the
# endings a live process saw, and the fault cuts this contract enumerates --
# "ending notification -> analysis intent -> possible analysis launch ->
# report publication" -- are precisely the moments a process is not there. The
# pass therefore derives what is OWED from durable state on every tick: the
# settled endings this store journalled, and the recovery records this store
# holds. A restarted incarnation with no cache and no live exchange reaches
# the same answer.
#
# AND IT ADDS NO SECOND ACCOUNT OF ANYTHING. The pass reads the Job store's
# own ending journal, the recovery records above, the cancellation fence
# through its owner and the control store through `worker_manager`; it decides
# an order and calls the operations in section 9.

# THE CLOSED SURFACE A DEPLOYMENT SUPPLIES. Written down rather than
# discovered from whatever object a caller passed, exactly as
# `delegation.OPERATIONS` is and for its reason.
#
#   `control`      the Worker Manager control store the original ending and
#                  the analysis execution are retained in.
#   `declaration`  the produced `baton.v12.recovery-analysis-worker/1`
#                  document. Configuration, which is why it is a document on
#                  the seam and not an operand of the pass: who analyses is a
#                  deployment fact and not a per-tick decision.
#   `destination`  where one owner item is delivered.
#   `launch`       ORDER OR RE-ENTER this analysis attempt's own turn over
#                  this fixed input. Level-triggered and idempotent, exactly
#                  as `manager._launch` drives a stage's runtime start: ONE
#                  attempt identity for the life of one failure, re-entered on
#                  every tick until its result is frozen, and never a second
#                  identity. The provider lives behind it; nothing in this
#                  package names an adapter, an image or a model.
ANALYSIS_SEAM = ("control", "declaration", "destination", "launch")

# THE OPERATOR'S HALF OF THE DECLARATION, and it is deliberately four members.
# A deployment declares WHO analyses -- the worker identity, the coordination
# participant, the principal it runs under and the qualification its
# capability was accepted by. It does NOT restate the schema, the role, the
# profile, the profile digest or the permitted outputs: each of those is the
# OWNER's fact, held above and digested at import, and asking an operator to
# copy `a4be8b48...` into a configuration file is asking for the one
# transcription that silently drifts.
WORKER_DECLARED = ("worker_id", "participant", "principal",
                   "capability_digest")

# WHICH STAGE KIND PRODUCES THIS TRIGGER. The ending this contract is about is
# a PRODUCER's: a retained candidate, a successful provider turn and that
# turn's own required verification. A review or integration ending has no
# `git-change-proposal` output for `classified_failure` to validate, so the
# kind is a cheap pre-filter in front of that reader rather than a second
# opinion about what it accepts. General exceptional-ending classification is
# the later Stage 2 outcome and is not widened here.
TRIGGER_STAGE_KIND = "implementation"

# WHAT A DISPATCHED ANALYSIS'S OWN FROZEN DISPOSITION MEANS FOR THE OWNER
# ITEM, over the control store's closed `DISPOSITIONS` vocabulary. `completed`
# is the only one with a report to read; the rest are the finite endings, and
# a word outside the mapping refuses rather than being read as one of them.
ANALYSIS_ENDINGS = {"completed": None,
                    "unable": "analysis-failed",
                    "plan-rejected": "analysis-failed",
                    "cancelled": "analysis-cancelled"}
if sorted(ANALYSIS_ENDINGS) != sorted(RESULT_DISPOSITIONS):  # pragma: no cover
    raise AssertionError(
        "the frozen-result disposition vocabulary changed and this mapping "
        "no longer answers for all of it")

# The acts this pass performs and the outcomes it reports, both closed so a
# tick report is a document rather than prose.
ANALYSIS_ACTS = ("observe", "dispatch", "deliver")
ANALYSIS_OUTCOMES = ("observed", "dispatched", "delivered", "held", "refused")


def declared_analysis_worker(configured,
                             *, what="a configured analysis worker"):
    """PRODUCE one `baton.v12.recovery-analysis-worker/1` declaration.

    THE PRODUCER THE DEPLOYMENT CALLS. `check_analysis_declaration` is the
    VALIDATOR and this is the maker: a deployment states the four facts that
    are its own and this composes the document, filling the schema, the role,
    the owner-approved profile, that profile's digest and the permitted output
    set from the definition this module holds and proved at import.

    SO AN OPERATOR CANNOT SELECT AN UNAPPROVED PROFILE BY TYPING ONE. The
    profile is not a configurable member here: M385612 approved exactly
    `stage1-analysis/1`, a later change is a new owner approval, and a
    configuration file is not where that selection is made. What the operator
    DOES choose -- who executes, under whose principal, with which worker and
    against which accepted qualification -- is what the four members are.

    AND THE PRODUCT OF THIS FUNCTION IS VALIDATED BEFORE IT IS RETURNED, by
    the same validator a hand-written declaration goes through. A producer
    that trusted its own output would be the one path into the records with no
    declaration check on it.
    """
    taken = own(configured, what=what)
    if type(taken) is not dict:
        _refuse(f"{what} is one closed object; this is "
                f"{name_value(configured)}", category="integrity",
                code="schema")
    missing = [one for one in WORKER_DECLARED if one not in taken]
    extra = sorted(one for one in taken if one not in WORKER_DECLARED)
    if missing or extra:
        _refuse(f"{what} is exactly {', '.join(WORKER_DECLARED)}"
                + (f"; missing {', '.join(missing)}" if missing else "")
                + (f"; unexpected {', '.join(extra)}" if extra else "")
                + ". The schema, the role, the owner-approved profile and its "
                  "digest and the permitted outputs are this build's and are "
                  "not configured",
                category="integrity", code="schema")
    return check_analysis_declaration(
        {"schema": DECLARATION_SCHEMA, "role": ANALYSIS_ROLE,
         "worker_id": taken["worker_id"],
         "participant": taken["participant"],
         "principal": taken["principal"],
         "profile": ANALYSIS_PROFILE,
         "profile_digest": ANALYSIS_PROFILE_DIGEST,
         "permitted_outputs": list(PERMITTED_OUTPUTS),
         "capability_digest": taken["capability_digest"]},
        what=what)


def analysis_attempt_id(key):
    """The ONE runtime attempt identity this failure's analysis is dispatched
    under, DERIVED from the failure key.

    DERIVED RATHER THAN ALLOCATED, which is the contract's section 4 in one
    line: "Exact operation retry returns the committed decision/admission/
    effect". A pass that asked a counter for an identity would mint a second
    one after a crash, present it to `admit_dispatch`, and collide with its
    own first dispatch -- or worse, be handed a fresh identity by a seam and
    order a second provider turn. Derived, every incarnation reaches the same
    name, so the journal's replay and the control store's reconciliation are
    asking about the same execution.
    """
    boundaries.identity(key, "a failure key")
    if not key.startswith("sha256:"):
        _refuse(f"a failure key is a sha256 digest; this is "
                f"{name_value(key)}", category="integrity", code="digest")
    return "analysis-" + key[len("sha256:"):]


def triggered_ending(control, attempt_id):
    """Is this ending THIS TRIGGER'S KIND at all? A read, and never a raise.

    THE SELECTOR AND NOT THE VALIDATION, and the split is deliberate. What
    this answers is the one question the pass must be able to ask about every
    settled ending without consequence: did the worker declare the ending word
    this trigger is about. An ending that declared something else -- a
    candidate, a provider failure, a yield, or nothing this build can read --
    is simply not this trigger, and reporting a refusal for each of them every
    tick would bury the ones that matter.

    WHAT IT DELIBERATELY DOES NOT DO is accept an ending. The retained
    candidate, its artifact bindings, its measured tree, the agreement between
    the worker's claim and its own observation and the successful provider
    turn are `classified_failure`'s, and a failure there is REPORTED -- REC-8:
    "A candidate failing identity or digest validation MUST be reported and is
    not recovery input." This function never makes that call quiet.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    composed = failure_cause.attempt_failure_cause_of(control, attempt_id)
    if composed is None:
        return False
    held = failure_cause.declaration_of(composed)
    if held is None:
        return False
    known, ending_word = failure_cause.decode(held["declared_ending"])
    return bool(known) and ending_word == TRIGGER_ENDING


def check_analysis_seam(seam, *, what="a configured analysis seam"):
    """The four members a deployment supplies, owned before anything is spent.

    `ManagerOperations.__init__`'s rule, for its reason: "A capability that
    cannot be called would otherwise fault in the middle of a delegated
    authority act." Here it would fault between a committed dispatch intent
    and the launch that intent authorizes, which is the one window this whole
    module is built to keep empty.
    """
    missing = [one for one in ANALYSIS_SEAM
               if getattr(seam, one, None) is None]
    if missing:
        _refuse(f"{what} supplies exactly {', '.join(ANALYSIS_SEAM)}; this "
                f"one carries no {', '.join(missing)}", category="refused",
                code="capability")
    return {"control": seam.control,
            "declaration": check_analysis_declaration(
                seam.declaration, what=f"{what}'s declared analysis worker"),
            "destination": boundaries.text(
                seam.destination, f"{what}'s owner destination"),
            "launch": boundaries.capability(
                seam.launch, f"{what}'s analysis launch")}


def _analysis_record(*, act, stage_id, failure_key, outcome, detail=None):
    if act not in ANALYSIS_ACTS:                          # pragma: no cover
        _refuse(f"a recovery act is one of {', '.join(ANALYSIS_ACTS)}",
                category="integrity", code="schema")
    if outcome not in ANALYSIS_OUTCOMES:                  # pragma: no cover
        _refuse(f"a recovery outcome is one of "
                f"{', '.join(ANALYSIS_OUTCOMES)}", category="integrity",
                code="schema")
    return documents.recovery_analysis(
        failure_key=failure_key, stage_id=stage_id, act=act, outcome=outcome,
        **({"detail": detail} if detail is not None else {}))


def _fenced(store, job_id, when):
    """The Job's own fence as a finite ANALYSIS endpoint, or `None`.

    THE TWO TRIGGERS ARE TWO ANSWERS, read from the fence rather than
    collapsed. `cancellation.refuse_fenced` already distinguishes them for its
    message, and the distinction matters more here: an owner looking at a held
    recovery needs to know whether somebody cancelled the Job or whether its
    own deadline passed, and reporting a Job expiry as a cancellation would
    name an act nobody performed.
    """
    held = cancellation.fenced(store._connection, job_id)
    if held is None:
        return None
    operator = held.get("trigger", "operator") == "operator"
    return {"outcome": "analysis-cancelled" if operator
            else "analysis-expired",
            "why": (f"Job {job_id} "
                    + ("was cancelled" if operator else "expired")
                    + f" at {held['requested_at']} ({held['reason']}) "
                    + when)}


def _condition(refusal):
    """A contained refusal as its TYPED pair and nothing else.

    `documents`' rule for `stage.refresh`: "Never a refusal's prose and never
    an engine's message -- both are composed from bytes a worker or a daemon
    wrote, and a sweep report is read by whoever watches the service." The
    prose still exists; it is simply not put in a published document by this
    pass.
    """
    return {"category": refusal.category, "code": refusal.code}


def settled_trigger_endings(store):
    """Every settled producer ending this store holds that COULD be the
    trigger, oldest stage first.

    FROM THE OWNED IDENTITIES, exactly as `ending.pending_endings` enumerates
    its own: the stages and their episodes are rows this store owns and each
    record is read at an identity this build derives, so no raw journal SQL is
    read here and another deployment's operations are invisible.

    SETTLED RATHER THAN PENDING, and that is the whole selection. A registered
    ending that has not settled is an obligation somebody still owes --
    `manager._recover_endings` owns asking again -- and observing a failure
    from it would attribute a terminal ending before its own owner finished
    recording one. The contract requires a "durably attributed terminal
    ending", and a settlement is what durably attributed means here.

    PRIOR EPISODES ARE INCLUDED for `pending_endings`' reason: a correction
    round opens a successor episode, and a pass that looked only at live
    episodes would walk past the episode that actually failed.
    """
    rows = {one["stage_id"]: one for one in submission.stage_rows(store)}
    held = []
    for stage_id in sorted(rows):
        for episode in episodes.episodes_of(store, stage_id):
            found = ending.ending_of(store, stage_id, episode["episode"])
            if found is None or found["settlement"] is None:
                continue
            intent = found["intent"]
            if intent["kind"] != TRIGGER_STAGE_KIND \
                    or intent["disposition"] != TRIGGER_DISPOSITION:
                continue
            held.append(intent)
    return held


def _attributed(store, control, intent):
    """This settled ending's own failure key, if this store already holds one.

    DERIVED BEFORE ANYTHING IS OBSERVED, from the ending's own selectors plus
    the terminal result identity its frozen row names -- which is exactly the
    six selectors `failure_key` is over. So an ending this store has already
    attributed is recognised by its IDENTITY, the way `manager._adopt`
    recognises a performed act, rather than by performing the observation
    again and reading what came back.

    Answers `(key, record)`, with `record` `None` for an ending this store has
    not attributed yet, or `(None, None)` when the terminal result identity
    cannot be read -- in which case the observation below is what refuses, and
    it refuses with the trigger's own account of why.
    """
    frozen = frozen_output_of(control, intent["attempt_id"])
    if frozen is None:
        return None, None
    key = failure_key(
        authority_uuid=intent["assignment"]["work_ref"]["authority_uuid"],
        work_id=intent["work_id"], job_id=intent["job_id"],
        stage_id=intent["stage_id"], attempt_id=intent["attempt_id"],
        result_id=frozen["result_id"])
    return key, failure_of(store, key)


def _observing(store, control, declaration, intent, now):
    """One settled ending, observed if it is this trigger. At most two journal
    acts and no external effect."""
    stage_id = intent["stage_id"]
    attempt_id = intent["attempt_id"]
    try:
        if not triggered_ending(control, attempt_id):
            return []
        key, attributed = _attributed(store, control, intent)
        if attributed is not None:
            # ALREADY ATTRIBUTED. The records are this ending's durable
            # account of itself and the advancing half below works from them,
            # so re-observing would journal nothing and reporting it would
            # name an act this tick did not perform.
            #
            # ONE EXCEPTION, AND IT IS A FACT AN OPERATOR MUST KEEP SEEING: a
            # failure whose analysis was never ADMITTED -- the Job was already
            # cancelled when its ending was attributed -- can never be
            # advanced, because a cancelled Job earns no admission and a
            # cancelled execution is never revived. It is reported as the hold
            # it is rather than disappearing from every later tick.
            if intent_of(store, key) is None:
                return [_analysis_record(
                    act="observe", stage_id=stage_id, failure_key=key,
                    outcome="held",
                    detail={"disposition": recovery_disposition(store, key)})]
            return []
        seen = observe_terminal_failure(
            store, control, stage_id=stage_id, episode=intent["episode"],
            attempt_id=attempt_id, declaration=declaration, now=now)
    except ContractRefusal as refusal:
        # REPORTED AND NOT SWALLOWED, and nothing was written. An invalid
        # candidate, an unreadable declaration, a recursion exclusion and a
        # cancelled Job all arrive here; each is named by its typed pair on
        # every tick until its cause is disposed of, which is the honest
        # behaviour for a fact this manager cannot settle on its own.
        return [_analysis_record(act="observe", stage_id=stage_id,
                                 failure_key=None, outcome="refused",
                                 detail=_condition(refusal))]
    return [_analysis_record(
        act="observe", stage_id=stage_id,
        failure_key=seen["failure"]["failure_key"], outcome="observed",
        detail={"disposition": seen["disposition"]})]


def _fixed_input(store, control, key):
    """The failure's own fixed input, RECOMPOSED and held to its digest.

    The same revalidation `deliver_analysis` performs, performed before the
    launch as well as before the delivery: an analysis is dispatched about the
    evidence its intent named, and evidence that changed under it is refused
    rather than sent to an agent.
    """
    failure = failure_of(store, key)
    current = classified_failure(control, failure["selectors"]["attempt_id"])
    fixed = analysis_input(current, failure_key=key,
                           job_id=failure["job_id"],
                           stage_id=failure["stage_id"],
                           episode=failure["episode"])
    if input_digest(fixed) != failure["input_digest"]:
        _refuse(f"the original evidence of failure {name_value(key)} now "
                f"digests to {name_value(input_digest(fixed))} and this "
                f"analysis was admitted on "
                f"{name_value(failure['input_digest'])}; an analysis is not "
                f"dispatched about evidence that changed under its intent",
                category="integrity", code="digest")
    return failure, fixed


def _dispatching(store, seam, key, intent, now):
    """Reserve, journal and ORDER one analysis turn -- in that order.

    THE JOURNAL ACT IS BEFORE THE LAUNCH, which is the whole of REC-3 here.
    `admit_dispatch` rechecks cancellation and expiry and commits the dispatch
    intent; only then is the seam asked to order anything. A death in between
    leaves a committed intent whose attempt the control store cannot account
    for, and the next tick HOLDS on it rather than ordering a second turn.
    """
    control = seam["control"]
    fenced = _fenced(store, intent["job_id"],
                     "before its analysis was dispatched")
    if fenced is not None:
        return _delivering_endpoint(store, seam, key, now=now, **fenced)
    if expiry_reached(intent, now):
        return _delivering_endpoint(
            store, seam, key, outcome="analysis-expired", now=now,
            why=(f"the analysis admitted at "
                 f"{intent['deadlines']['admitted_at']} reached its "
                 f"{intent['deadlines']['job_seconds']}-second Job deadline "
                 f"{intent['deadlines']['job_deadline_at']} before it was "
                 f"dispatched; queue time is included in that bound"))
    _failure, fixed = _fixed_input(store, control, key)
    attempt_id = analysis_attempt_id(key)
    admit_dispatch(store, control, key=key, analysis_attempt_id=attempt_id,
                   now=now)
    # THE EXTERNAL EFFECT, LAST. The seam owns the worker, the provider and
    # the container; what this pass owns is that an intent naming this exact
    # attempt identity and this exact input is durable first.
    seam["launch"](attempt_id=attempt_id, document=fixed, intent=intent)
    return [_analysis_record(act="dispatch", stage_id=intent["stage_id"],
                             failure_key=key, outcome="dispatched",
                             detail={"disposition":
                                     recovery_disposition(store, key)})]


def _delivering_endpoint(store, seam, key, *, outcome, why, now):
    held = deliver_endpoint(store, seam["control"], key=key, outcome=outcome,
                            why=why, destination=seam["destination"], now=now)
    return [_analysis_record(
        act="deliver", stage_id=failure_of(store, key)["stage_id"],
        failure_key=key, outcome="delivered",
        detail={"owner_item": held["owner_item"]["outcome"]})]


def _delivering(store, seam, key, intent, now, disposition=None):
    """Read what the dispatched analysis ended as, and deliver ONE owner item.

    THE PRECEDENCE IS THE RULING'S, and each clause is here for a named
    reason:

      1. A FROZEN RESULT IS READ FIRST. An analysis that finished produced
         evidence, and a deadline that passed afterwards does not unmake it --
         REC-8's own post-verification rule, that "time expiry alone does not
         invalidate successful verification", applied to the analysis this
         section dispatches. A `completed` result is delivered as the report;
         the other three dispositions are the finite endings they are.
      2. AN UNACCOUNTED LAUNCH HOLDS UNTIL THE ADMITTED DEADLINE, and then
         becomes `analysis-unknown-cessation`. It is never read as "nothing
         was launched" and never relaunched; what makes the hold finite is
         the owner-approved bound, not a retry.
      3. THE JOB'S OWN FENCE, then the analysis's admitted deadline. Both are
         owner-facing endings that preserve whatever the manager sealed, and
         the fence's own trigger decides which of the two words it is -- a
         cancellation and a Job expiry are different acts.
      4. OTHERWISE THE ANALYSIS IS IN FLIGHT and this tick RE-ENTERS ITS OWN
         EXECUTION rather than waiting inside the tick. The identity is the
         one the committed dispatch named, so this is `manager._launch`'s
         level-triggered re-entry and not a second order: a worker lifecycle
         advances through admission, claim, start, command and ending, and
         nothing would advance it if the pass only ever read. An execution the
         control store cannot account for is excluded by clause 2 BEFORE this
         clause can be reached, which is what keeps "no blind dispatch" true.
    """
    control = seam["control"]
    reconciled = reconciled_dispatch(store, control, key)
    if reconciled["state"] == "none":
        # UNREACHABLE AND GUARDED ANYWAY. The caller only arrives here for a
        # failure whose disposition says a dispatch is committed, so `none`
        # would mean this store's own records disagree with each other -- and
        # the branch below would otherwise order a turn under a null identity.
        _refuse(f"failure {name_value(key)} is {name_value(disposition)} and "
                f"this store holds no dispatch intent for it",
                category="integrity", code="schema")
    frozen = (frozen_output_of(control, reconciled["analysis_attempt_id"])
              if reconciled["state"] == "launched" else None)
    if frozen is not None:
        if frozen["disposition"] not in ANALYSIS_ENDINGS:  # pragma: no cover
            _refuse(f"analysis attempt "
                    f"{name_value(reconciled['analysis_attempt_id'])} froze "
                    f"disposition {name_value(frozen['disposition'])}, which "
                    f"this build does not answer for",
                    category="integrity", code="schema")
        endpoint = ANALYSIS_ENDINGS[frozen["disposition"]]
        if endpoint is None:
            held = deliver_analysis(store, control, key=key,
                                    destination=seam["destination"], now=now)
            return [_analysis_record(
                act="deliver", stage_id=intent["stage_id"], failure_key=key,
                outcome="delivered",
                detail={"owner_item": held["owner_item"]["outcome"]})]
        return _delivering_endpoint(
            store, seam, key, outcome=endpoint, now=now,
            why=(f"the dispatched analysis froze its result "
                 f"{name_value(frozen['disposition'])}; its partial evidence "
                 f"is preserved and no replacement is ordered"))
    if reconciled["state"] == "unknown":
        if not expiry_reached(intent, now):
            return [_analysis_record(
                act="deliver", stage_id=intent["stage_id"], failure_key=key,
                outcome="held", detail={"state": reconciled["state"]})]
        return _delivering_endpoint(
            store, seam, key, outcome="analysis-unknown-cessation", now=now,
            why=reconciled["why"])
    fenced = _fenced(store, intent["job_id"],
                     "while its analysis was running")
    if fenced is not None:
        return _delivering_endpoint(store, seam, key, now=now, **fenced)
    if expiry_reached(intent, now):
        return _delivering_endpoint(
            store, seam, key, outcome="analysis-expired", now=now,
            why=(f"the analysis admitted at "
                 f"{intent['deadlines']['admitted_at']} reached its "
                 f"{intent['deadlines']['job_seconds']}-second Job deadline "
                 f"{intent['deadlines']['job_deadline_at']} mid-turn"))
    _failure, fixed = _fixed_input(store, control, key)
    seam["launch"](attempt_id=reconciled["analysis_attempt_id"],
                   document=fixed, intent=intent)
    # THE RECORD IS THE ACT THIS TICK WAS TRYING TO PERFORM, which is the
    # DELIVERY: the analysis is dispatched and what the pass wants is its
    # report. `held` says nothing durable changed in this store, and the
    # `state` says which of the two holds it is -- `launched`, where the
    # execution was re-entered under its own identity, or `unknown` above,
    # where nothing was ordered at all.
    return [_analysis_record(act="deliver", stage_id=intent["stage_id"],
                             failure_key=key, outcome="held",
                             detail={"state": reconciled["state"]})]


def _advancing(store, seam, key, now):
    """One failure, advanced by at most one act this tick."""
    disposition = recovery_disposition(store, key)
    if disposition == "delivered":
        return []
    intent = intent_of(store, key)
    if intent is None:
        # A failure whose intent was refused at observation -- a cancelled Job
        # is the ordinary case. The observing half re-reports it each tick and
        # this half has no admitted analysis to advance.
        return []
    try:
        if disposition == "analysis-intended":
            return _dispatching(store, seam, key, intent, now)
        return _delivering(store, seam, key, intent, now,
                           disposition=disposition)
    except ContractRefusal as refusal:
        return [_analysis_record(
            act="dispatch" if disposition == "analysis-intended"
            else "deliver", stage_id=intent["stage_id"], failure_key=key,
            outcome="refused", detail=_condition(refusal))]


def advance_recovery(store, seam, *, now):
    """ONE LEVEL-TRIGGERED RECOVERY PASS: observe, dispatch, deliver.

    THE PRODUCTION ENTRY POINT OF THIS MODULE, called from `manager.sweep` on
    every tick of every deployment that configures an analysis seam, and from
    `manager.reconcile` on every resume. Nothing here is edge-triggered on an
    ending a live process happened to see.

    WHAT IT RETURNS is a list of bounded `recovery.analysis` documents -- one
    per act this tick performed, held or reported -- so a sweep report names
    what the recovery path did rather than leaving it invisible. Returning an
    empty list is the ordinary answer for a store with no retained failures.

    THE TWO HALVES RUN IN ONE TICK AND THE ADVANCE IS ONE ACT. Observing
    first and advancing from the records afterwards is `manager._converse`'s
    reacquisition rule: a failure this tick observed is a failure that now
    owes a dispatch, and deriving that from state read before the observation
    would make every retained failure wait a whole tick for an act this tick
    could already perform. What is NEVER chained is dispatch and delivery --
    the analysis has not run yet when its turn is ordered, so reading a report
    in the tick that ordered it would be reading one nobody wrote.

    A CONTAINED REFUSAL IS A CONDITION AND NOT A FAULT, exactly as the
    cancellation, control and exchange passes treat theirs. One Job's
    unreadable candidate must not stop another Job's analysis from being
    delivered, and it must not stop the tick.
    """
    boundaries.instant(now, "a recovery pass instant")
    held = check_analysis_seam(seam)
    acts = []
    for intent in settled_trigger_endings(store):
        acts.extend(_observing(store, held["control"], held["declaration"],
                               intent, now))
    for key in sorted(failures_of(store)):
        acts.extend(_advancing(store, held, key, now))
    return acts
