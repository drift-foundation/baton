"""THE APPROVED VERIFIER RUN ON THE EXACT RETAINED CANDIDATE, AND THE SAME
CANDIDATE HANDED TO INDEPENDENT REVIEW.

W385625 Stage 1-C, under DESIGN REC-8 and the accepted Stage 1 contract
`work/records/2026/08/finding-v12-isolated-agent-workers/findings/
finding-v12-team-hierarchy-shared-approvers/STAGE-1-CONTRACT.md` (SHA-256
`52c2c640fdbb791e70ae61edf7ef7db7190bacd767d6d044f678517d2e09e1bc`), accepted
by `review-2026-11-22T05-18-37Z.md`. The owning record is
`work/records/2026/11/finding-v12-retained-recovery-verification/`.

IT FILLS THE ONE SEAM STAGE 1-B LEFT OPEN AND SAID SO. `retained_recovery`
admits one verification/review-only successor, reserves the isolated
verification's identity, publishes the binding -- and executes nothing: its
`successor_readiness` answers `blocked: retained candidate handoff
unavailable`, and its `execution_gate` keeps the admitted review stage out of
circulation so that a reserved Job cannot be mistaken for a performed
recovery. This module is the five acts that boundary names, each one durable
and each one replayable:

  1. MATERIALIZE. The exact retained candidate bytes are copied out of the
     custody that holds them into a NEW PRIVATE workspace, measured in the
     same no-follow pass that writes them, and held to the digest the owner's
     decision bound. The declared source profile and base are validated
     through `source_profiles.checkout`, which owns that pairing -- so a
     `git` candidate whose base is not an object name and a `generic`
     candidate that declares one are both refused here rather than discovered
     by a verifier. The original custody is never opened for writing and is
     never moved: the workspace is a COPY, and the candidate's identity stays
     the custody's.
  2. EXECUTE. Only the owner-approved corrected argv, only in the approved
     execution context -- working directory, environment, tool and runtime
     selection, bound by the digest the decision approved, because "a command
     string must not hide a changed execution context". The exit status, both
     streams and the real start and end instants are retained as this
     execution's own measured output tree, under the approved 900-second
     per-command ceiling, with zero automatic retry and zero correction.
  3. HAND OFF. A PASSED verification -- and nothing else -- binds the same
     candidate, the original failure, the owner decision and the verification
     evidence into one durable handoff, after which `execution_gate` opens and
     the deployment's own independent reviewer is admitted by the ordinary
     manager tick. No verdict is manufactured here and no review is performed
     here: what this slice owes is the exact same-candidate delivery, and the
     substance is the reviewer's.
  4. RENEW. A FAILED verification produces ONE new failure key, ONE analysis
     intent under the owner-approved `stage1-analysis/1` bounds and ONE owner
     item -- and never a further successor. "Each recovery round needs a new
     owner decision."
  5. HOLD. Expiry after the verification passed but before review completed,
     including during a busy-reviewer wait, preserves that evidence and holds
     an owner item carrying the three lineage operands a review-only decision
     must name back. It is neither a verification failure nor an acceptance:
     no analysis is triggered and nothing is retried.

WHAT IT REFUSES, and every one of these is a ruling rather than a preference:

  * NO VERIFIER OUTPUT BECOMES A CANDIDATE. REC-8 says it in four words and
    this module keeps it structurally: the candidate root is re-measured after
    the command and compared with the bound digest, the retained execution
    output lives under a SEPARATE root, and the handoff binds the CUSTODY's
    candidate identity. A workspace the verifier changed is reported and is
    not handed anywhere.
  * NO IMPLEMENTATION, EVER. There is no stage kind, no provider prompt, no
    correction round and no second attempt at the task reachable from here;
    the only command this module runs is the one argv an owner approved
    against a candidate that already exists.
  * NO GATE WITHOUT A HANDOFF. `execution_gate` opens on the committed
    handoff record and on nothing else -- not on a passed account alone, which
    is exactly what Stage 1-B's review found: "a passed account alone cannot
    open review".
  * NO EXECUTION BESIDE A FENCE. Cancellation and expiry are re-read at every
    act through their own owners; a cancelled successor is never revived, an
    expired one is held rather than driven, and an unknown prior execution
    holds instead of being replaced.
  * NO SECOND EFFECT. Every act is journalled under an identity DERIVED from
    the successor Job, so a lost reply, a restart and a concurrent tick all
    reach the same record; a changed operand under one identity collides.
  * NO RECURSION. A renewed failure is analysed once and delivered once; the
    analysis's own failure, expiry or cancellation goes straight to the owner
    and never triggers another analysis.

WHAT IS DELIBERATELY NOT HERE. No process is started by this module: running
argv is a host act and `baton_v12` never imports `subprocess`, so the runner
is an injected port and `tools.recovery_execution.CommandRunner` is the
deployment's own. No reviewer is launched, no verdict is recorded and no
checkpoint is frozen: those are the pool's, the review driver's and the
reviewer's, reached by the ordinary tick once the gate this module opens is
open.
"""

import fcntl
import json
import os

from ..contracts import ContractRefusal, digest, digest_of_bytes, own
from ..contracts.errors import name_value
from ..contracts.manifest import check_uri
from ..source_profiles import checkout
from ..worker_manager import boundaries, frozen_output_of
from ..worker_manager.workspaces import copied_manifest, directory_manifest
from . import (cancellation, documents, episodes, failure_analysis,
               retained_recovery)
from .store import job_signature

__all__ = ["CONTEXT_SCHEMA", "CONTEXT_MEMBERS", "TOOL_MEMBERS",
           "RUNTIME_MEMBERS", "MAX_ENVIRONMENT", "MAX_OUTPUT_BYTES",
           "owned_context", "context_digest",
           "CANDIDATE_ROOT", "SCRATCH_ROOT", "OUTPUT_ROOT", "WORKSPACE_ROOTS",
           "RETAINED_OUTPUT", "SOURCE_PROFILES", "candidate_source_profile",
           "MAX_ENVIRONMENT_NAME", "MAX_ENVIRONMENT_VALUE",
           "RUNNER_PORT", "RUN_MEMBERS", "VERIFICATION_SEAM",
           "check_verification_seam",
           "MATERIALIZATION_KIND", "MATERIALIZATION_MEMBERS",
           "INTENT_KIND", "INTENT_MEMBERS", "intent_operation_id",
           "execution_intent_of",
           "RESULT_KIND", "RESULT_MEMBERS",
           "HANDOFF_KIND", "HANDOFF_MEMBERS",
           "RENEWED_KIND", "RENEWED_MEMBERS",
           "RENEWED_ANALYSIS_KIND", "RENEWED_ANALYSIS_MEMBERS",
           "RENEWED_ITEM_KIND", "RENEWED_ITEM_MEMBERS",
           "RENEWED_ENDPOINT_KIND", "RENEWED_ENDPOINT_MEMBERS",
           "renewed_endpoint_operation_id", "renewed_endpoint_of",
           "HOLD_KIND", "HOLD_MEMBERS",
           "RENEWED_INPUT_SCHEMA", "renewed_input", "renewed_failure_key",
           "materialization_operation_id", "result_operation_id",
           "EXECUTION_LOCK",
           "handoff_operation_id", "renewed_operation_id",
           "renewed_analysis_operation_id", "renewed_item_operation_id",
           "hold_operation_id",
           "materialization_of", "execution_result_of", "handoff_of",
           "renewed_failure_of", "renewed_analysis_of", "renewed_item_of",
           "hold_of", "owner_items_of",
           "RENEWED_OUTCOME", "HOLD_OUTCOME", "ENDPOINT_OUTCOMES",
           "VERIFICATION_ACTS", "VERIFICATION_OUTCOMES",
           "EXECUTION_STATES", "execution_readiness", "successor_execution",
           "materialize", "execute", "hand_off", "renew", "hold",
           "deliver_renewed_endpoint", "advance_verification"]


def _refuse(message, *, category="refused", code="precondition"):
    raise ContractRefusal(category, code, message)


def _denied(message):
    raise ContractRefusal("policy", "denied", message)


# -- 1. the approved execution context ---------------------------------------
#
# WHY THERE IS A DOCUMENT HERE AT ALL. The owner's decision binds a
# `context_digest` beside the corrected argv, and Stage 1-B compares that
# digest exactly -- but a digest over nothing in particular is a digest nobody
# can check an execution against. The contract's section 2 names what the
# digest has to cover: "Arguments, working directory, environment and
# tool/runtime selection must be bound where they affect verification; a
# command string alone must not hide changes to its execution context." So
# this is that document, closed, and `context_digest` is the one spelling of
# its identity.
#
# THE WORKING DIRECTORY IS VIEW-RELATIVE AND NEVER A HOST PATH. The contract
# keeps paths as evidence locators rather than as authority, and a context
# naming `/var/lib/...` would be a declaration about somebody else's
# filesystem that this manager would then have to honour. What it names is one
# of this workspace's own roots.
CONTEXT_SCHEMA = "baton.v12.recovery-verification-context/1"
CONTEXT_MEMBERS = ("schema", "working_directory", "environment", "tool",
                   "runtime")
TOOL_MEMBERS = ("kind", "selector")
RUNTIME_MEMBERS = ("kind", "isolation")

# The declared environment is bounded, closed and sorted at its own boundary:
# an environment a reader cannot reproduce is not a bound context.
MAX_ENVIRONMENT = 32
MAX_ENVIRONMENT_NAME = 128
MAX_ENVIRONMENT_VALUE = 4096

# WHAT THE MANAGER'S PRIVATE VERIFICATION WORKSPACE CONSISTS OF, and the names
# are the contract's own split: "Original custody is immutable; scratch/
# generated test outputs are separate."
CANDIDATE_ROOT = "candidate"
SCRATCH_ROOT = "scratch"
OUTPUT_ROOT = "output"
WORKSPACE_ROOTS = (CANDIDATE_ROOT, SCRATCH_ROOT, OUTPUT_ROOT)

# The one retained output tree this execution writes, under `output`. It is
# the execution's own account and is never a candidate: nothing reads it as
# one, and `hand_off` binds the custody's candidate rather than this.
RETAINED_OUTPUT = "verification"

# Each stream is bounded and a truncation is RECORDED rather than silent: a
# retained account that quietly dropped the end of a failure's own output
# would be evidence about something smaller than what happened.
MAX_OUTPUT_BYTES = 1 << 20

# THE SOURCE PROFILE VOCABULARY IS READ FROM ITS OWNER rather than respelled.
# `source_profiles.checkout` owns the three profile words and the base
# pairing, and this module asks that package -- a second copy of the pairing
# would be a second decision-maker about what a `git` candidate is.
SOURCE_PROFILES = (checkout.GENERIC_PROFILE, checkout.GIT_PROFILE)
if any(one not in checkout.PROFILES
       for one in SOURCE_PROFILES):                       # pragma: no cover
    raise AssertionError(
        "the source profile vocabulary no longer names the profiles a "
        "retained candidate can be materialized under")

# The transport suffix a retained `git-change-proposal` names its bundle by.
# Read as a CLASSIFIER and never as a path this module opens.
_BUNDLE_SUFFIX = ".bundle"


def _environment(value, what):
    taken = own(value, what=what)
    if type(taken) is not dict:
        _refuse(f"{what} is one closed object of name to value; this is "
                f"{name_value(value)}", category="integrity", code="schema")
    if len(taken) > MAX_ENVIRONMENT:
        _refuse(f"{what} carries at most {MAX_ENVIRONMENT} names; this one "
                f"carries {len(taken)}", category="integrity", code="limit")
    held = {}
    for name in sorted(taken):
        if type(name) is not str or not name or len(name) > \
                MAX_ENVIRONMENT_NAME or "=" in name or "\x00" in name:
            _refuse(f"{what} names {name_value(name)}, which is not one "
                    f"environment variable name",
                    category="integrity", code="schema")
        value_of = taken[name]
        if type(value_of) is not str or len(value_of) > \
                MAX_ENVIRONMENT_VALUE or "\x00" in value_of:
            _refuse(f"{what} binds {name_value(name)} to a value this "
                    f"boundary cannot carry",
                    category="integrity", code="schema")
        held[name] = value_of
    return held


def owned_context(document, *, what="an approved execution context"):
    """One closed `baton.v12.recovery-verification-context/1`, owned.

    EVERY MEMBER IS A BINDING THE VERIFICATION IS DECIDED BY, which is why the
    set is closed rather than permissive: a context carrying a member this
    build does not read would be a declaration whose effect nobody validated,
    and the digest the owner approved would be covering it.
    """
    taken = boundaries.document(document, what, required=CONTEXT_MEMBERS)
    if taken["schema"] != CONTEXT_SCHEMA:
        _refuse(f"{what} is {name_value(CONTEXT_SCHEMA)}; this one is "
                f"{name_value(taken['schema'])}. An unknown generation is "
                f"refused rather than part-read",
                category="refused", code="unsupported-version")
    place = taken["working_directory"]
    boundaries.text(place, f"{what}'s working directory")
    if place not in WORKSPACE_ROOTS:
        _refuse(f"{what} names working directory {name_value(place)} and a "
                f"private verification workspace holds "
                f"{', '.join(WORKSPACE_ROOTS)}; a context naming a host path "
                f"would be a declaration about another filesystem rather "
                f"than a binding of this execution",
                category="integrity", code="path")
    tool = boundaries.document(taken["tool"], f"{what}'s tool selection",
                               required=TOOL_MEMBERS)
    runtime = boundaries.document(taken["runtime"],
                                  f"{what}'s runtime selection",
                                  required=RUNTIME_MEMBERS)
    for held, members, label in ((tool, TOOL_MEMBERS, "tool"),
                                 (runtime, RUNTIME_MEMBERS, "runtime")):
        for member in members:
            boundaries.text(held[member], f"{what}'s {label} {member}")
    return {"schema": CONTEXT_SCHEMA, "working_directory": place,
            "environment": _environment(taken["environment"],
                                        f"{what}'s environment"),
            "tool": dict(tool), "runtime": dict(runtime)}


def context_digest(document):
    """The canonical identity of ONE approved execution context."""
    return digest(owned_context(document))


# -- 2. the candidate's declared source ---------------------------------------

def candidate_source_profile(candidate, *, what="a retained candidate"):
    """WHICH SOURCE PROFILE THESE RETAINED BYTES ARE MATERIALIZED UNDER, and
    the base pairing proved by the package that owns it.

    SOURCE-AWARE RATHER THAN SOURCE-GUESSING. The retained claim names a
    transport and a base/head pair; the profile follows from the transport,
    and `checkout.check_declared_base` is what decides whether the pair is
    admissible under it. A `git` candidate whose base is not an object name
    and a `generic` candidate that declares one are refused HERE, before a
    byte is copied -- "candidate/evidence validation failure is reported
    explicitly and never treated as eligible recovery input".
    """
    held = boundaries.document(candidate, what,
                               required=("base", "head", "transport"),
                               optional=("output", "artifact_id",
                                         "content_digest", "tree_digest",
                                         "entry_count", "locator"))
    transport = held["transport"]
    boundaries.text(transport, f"{what}'s transport")
    profile = (checkout.GIT_PROFILE if transport.endswith(_BUNDLE_SUFFIX)
               else checkout.GENERIC_PROFILE)
    if profile == checkout.GENERIC_PROFILE:
        # A GENERIC CANDIDATE DECLARES NO BASE, which is the pairing the
        # profile package itself enforces at the launch boundary: a transport
        # that is not a Git bundle cannot be resolved against a revision, and
        # a base beside one would be a declaration nothing could check.
        if held["base"] is not None or held["head"] is not None:
            _refuse(f"{what} names transport {name_value(transport)}, which "
                    f"is not a Git bundle, and still declares base "
                    f"{name_value(held['base'])} and head "
                    f"{name_value(held['head'])}; a generic candidate "
                    f"carrying a revision is a pairing the source profile "
                    f"package refuses",
                    category="integrity", code="schema")
        return {"source_profile": profile, "declared_base": None,
                "declared_head": None, "transport": transport}
    # THE BASE AND THE HEAD ARE HELD TO THE SAME GRAMMAR, through the package
    # that owns it. A candidate commit name alone is insufficient -- the
    # contract says so -- but a name that is not even a name cannot identify
    # the bytes this materialization is about.
    for member in ("base", "head"):
        try:
            checkout.check_declared_base(held[member])
        except checkout.ProfileRefusal as refusal:
            _refuse(f"{what} names {member} {name_value(held[member])} under "
                    f"{name_value(profile)} and the source profile package "
                    f"refuses it: {refusal}",
                    category="integrity", code="schema")
    return {"source_profile": profile, "declared_base": held["base"],
            "declared_head": held["head"], "transport": transport}


# -- 3. the deployment's seam --------------------------------------------------
#
# WRITTEN DOWN RATHER THAN DISCOVERED, exactly as `failure_analysis
# .ANALYSIS_SEAM` and `retained_recovery`'s owner set are: a member that
# cannot be called would otherwise fault between a committed materialization
# and the execution that materialization authorizes.
#
#   `control`      the Worker Manager control store the retained candidate and
#                  its custody live in. READ-ONLY to this module.
#   `context`      the deployment's declared execution context, whose digest
#                  the owner approved.
#   `workspaces`   the root this deployment allocates PRIVATE verification
#                  workspaces under. Never inside custody.
#   `runner`       the host port that runs one bounded command.
#   `declaration`  the declared analysis worker a RENEWED failure's one
#                  analysis is admitted under -- `failure_analysis`'s own
#                  `baton.v12.recovery-analysis-worker/1`.
#   `destination`  the owner address a renewed item or a post-verification
#                  hold is delivered to.
VERIFICATION_SEAM = ("control", "context", "workspaces", "runner",
                     "declaration", "destination")

# THE HOST PORT, AND IT IS TWO MEMBERS. `instance` is which deployment this
# runner answers for -- W359719 review R17/R18's rule, which every other owner
# port in this recovery path keeps -- and `run` is the one capability.
RUNNER_PORT = ("instance", "run")

# What one bounded command's account must carry back. `timed_out` is a fact
# about the ceiling rather than a status: a command the runner stopped at the
# approved 900 seconds did not pass, and saying so separately is what keeps
# "expired" from being read as "failed its assertions".
RUN_MEMBERS = ("exit_status", "signal", "stdout", "stderr", "started_at",
               "ended_at", "timed_out")


def check_verification_seam(seam, *, what="the retained verification seam"):
    """Prove the configured seam BEFORE this pass spends anything.

    `failure_analysis.check_analysis_seam`'s rule, for its reason: a
    capability that cannot be called would otherwise fault between a
    committed materialization and the execution that materialization
    authorizes -- the one window this module is built to keep empty.
    """
    def member(name):
        # AN OBJECT OR THE ALREADY-PROVED MAPPING, because this check is
        # IDEMPOTENT on purpose: `advance_verification` proves the seam once
        # before it spends anything and then hands it to each act, and each
        # act proves it again because each is also a supported entry point an
        # owner surface can call directly. A check that only read attributes
        # would make the second proof refuse the thing the first one
        # returned.
        if isinstance(seam, dict):
            return seam.get(name)
        return getattr(seam, name, None)

    missing = [one for one in VERIFICATION_SEAM if member(one) is None]
    if missing:
        _refuse(f"{what} supplies exactly "
                f"{', '.join(VERIFICATION_SEAM)}; this one carries no "
                f"{', '.join(missing)}",
                category="refused", code="capability")
    taken = {one: member(one) for one in VERIFICATION_SEAM}
    taken["context"] = owned_context(taken["context"])
    taken["declaration"] = failure_analysis.check_analysis_declaration(
        taken["declaration"])
    boundaries.identity(taken["destination"], f"{what}'s owner destination")
    place = taken["workspaces"]
    boundaries.text(place, f"{what}'s private workspace root")
    if not os.path.isabs(place):
        _refuse(f"{what} names private workspace root {name_value(place)}; "
                f"an allocation root is one absolute path",
                category="integrity", code="path")
    if os.path.islink(place) or not os.path.isdir(place):
        _refuse(f"{what}'s private workspace root {name_value(place)} is not "
                f"a directory this manager can allocate under",
                category="integrity", code="path")
    runner = taken["runner"]
    absent = [one for one in RUNNER_PORT
              if not callable(getattr(runner, one, None))]
    if absent:
        _refuse(f"{what}'s command runner answers no {', '.join(absent)}; a "
                f"host port that cannot say which instance it runs in is a "
                f"port this pass cannot attribute an execution to",
                category="refused", code="capability")
    return taken


def _agreeing_instance(seam, *, what):
    """One deployment's facts, not two. `retained_recovery._agreeing_control`'s
    rule for the one operand its ports do not supply, applied here to the two
    this seam does: the control store the candidate is read from and the root
    the workspace is allocated under both belong to the instance the runner
    declares.
    """
    declared = seam["runner"].instance()
    held = declared if isinstance(declared, dict) else {}
    expected = held.get("control_store")
    here = getattr(seam["control"], "database", None)
    if expected is not None and os.path.realpath(str(here or "")) \
            != os.path.realpath(str(expected)):
        _refuse(f"{what} reads the retained candidate from "
                f"{name_value(here)} and instance "
                f"{name_value(held.get('root'))} owns "
                f"{name_value(expected)}; evidence about a failed execution "
                f"read from another deployment's store is evidence about "
                f"another deployment")
    return held


# -- 4. the journal ------------------------------------------------------------

MATERIALIZATION_KIND = "recovery.candidate-materialized"
INTENT_KIND = "recovery.verification-intent"
RESULT_KIND = "recovery.verification-executed"
HANDOFF_KIND = "recovery.candidate-handoff"
RENEWED_KIND = "recovery.renewed-failure"
RENEWED_ANALYSIS_KIND = "recovery.renewed-analysis-intent"
RENEWED_ITEM_KIND = "recovery.renewed-owner-item"
RENEWED_ENDPOINT_KIND = "recovery.renewed-analysis-endpoint"
HOLD_KIND = "recovery.post-verification-hold"

MATERIALIZATION_MEMBERS = ("failure_key", "decision_id", "job_id",
                           "verification_attempt_id", "stages", "candidate",
                           "source", "workspace", "measured",
                           "materialized_at")
INTENT_MEMBERS = ("failure_key", "decision_id", "job_id",
                  "verification_attempt_id", "argv", "context_digest",
                  "context", "candidate", "workspace", "intended_at")
RESULT_MEMBERS = ("failure_key", "decision_id", "job_id",
                  "verification_attempt_id", "outcome", "exit_status", "argv",
                  "context_digest", "context", "candidate", "workspace",
                  "retained", "timing", "concluded_at")
HANDOFF_MEMBERS = ("failure_key", "decision_id", "job_id", "review_stage_id",
                   "stages", "candidate", "producer", "verification",
                   "workspace", "evidence", "handed_at")
RENEWED_MEMBERS = ("failure_key", "original_failure_key", "decision_id",
                   "job_id", "stage_id", "selectors", "candidate",
                   "verification", "input_digest", "successor", "next",
                   "recorded_at")
RENEWED_ANALYSIS_MEMBERS = ("failure_key", "original_failure_key",
                            "decision_id", "job_id", "stage_id",
                            "input_digest", "declaration_digest", "role",
                            "participant", "principal", "worker_id",
                            "profile", "profile_digest", "policy",
                            "deadlines")
RENEWED_ITEM_MEMBERS = ("failure_key", "original_failure_key", "decision_id",
                        "job_id", "destination", "outcome", "reason",
                        "analysis", "automatic_successor", "delivered_at")
RENEWED_ENDPOINT_MEMBERS = ("failure_key", "original_failure_key",
                            "decision_id", "job_id", "destination",
                            "outcome", "reason", "analysis",
                            "automatic_retry", "recursive_analysis",
                            "recorded_at")
HOLD_MEMBERS = ("failure_key", "decision_id", "job_id", "destination",
                "outcome", "fence", "verification", "candidate", "lineage",
                "analysis", "retry", "delivered_at")

# The one owner outcome a renewed verification failure is delivered under, and
# the one a post-verification expiry is. Both are CLOSED words this manager
# owns: an owner item whose outcome was prose could not be acted on by a
# script and could not be compared across a restart.
RENEWED_OUTCOME = "verification-failed-again"
HOLD_OUTCOME = "verification-passed-review-incomplete"

# AND THE FINITE ENDINGS OF THE RENEWED FAILURE'S OWN ANALYSIS, read from
# their owner rather than respelled: `failure_analysis` already publishes the
# three words a finite analysis ending is delivered under.
ENDPOINT_OUTCOMES = failure_analysis.ENDPOINT_OUTCOMES

RENEWED_INPUT_SCHEMA = "baton.v12.renewed-verification-input/1"


def _operation_id(kind, name):
    return f"{kind}:{name}"


def materialization_operation_id(job_id):
    boundaries.identity(job_id, "a successor Job id")
    return _operation_id(MATERIALIZATION_KIND, job_id)


def intent_operation_id(job_id):
    boundaries.identity(job_id, "a successor Job id")
    return _operation_id(INTENT_KIND, job_id)


def result_operation_id(job_id):
    boundaries.identity(job_id, "a successor Job id")
    return _operation_id(RESULT_KIND, job_id)


def handoff_operation_id(job_id):
    boundaries.identity(job_id, "a successor Job id")
    return _operation_id(HANDOFF_KIND, job_id)


def renewed_operation_id(job_id):
    boundaries.identity(job_id, "a successor Job id")
    return _operation_id(RENEWED_KIND, job_id)


def renewed_analysis_operation_id(job_id):
    boundaries.identity(job_id, "a successor Job id")
    return _operation_id(RENEWED_ANALYSIS_KIND, job_id)


def renewed_item_operation_id(job_id):
    boundaries.identity(job_id, "a successor Job id")
    return _operation_id(RENEWED_ITEM_KIND, job_id)


def renewed_endpoint_operation_id(job_id):
    boundaries.identity(job_id, "a successor Job id")
    return _operation_id(RENEWED_ENDPOINT_KIND, job_id)


def hold_operation_id(job_id):
    boundaries.identity(job_id, "a successor Job id")
    return _operation_id(HOLD_KIND, job_id)


def _committed(store, kind, operation_id, members, *, named=None, value=None):
    """One committed record of this journal, PROVED to be the one asked for.

    `retained_recovery._committed`'s restatement of `ending._committed`'s
    correction, which applies here for its reason: a well-made record of
    another execution, copied through the public journal to this identity,
    would otherwise read as this one's.
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


def materialization_of(store, job_id):
    return _committed(store, MATERIALIZATION_KIND,
                      materialization_operation_id(job_id),
                      MATERIALIZATION_MEMBERS, named="job_id", value=job_id)


def execution_intent_of(store, job_id):
    """The DURABLE INTENT one approved command was about to be run under.

    REC-3: intent before the external effect. This record is what makes the
    one uncertain window in this whole slice -- a process that started the
    approved command and died before journalling its account -- an ACTIONABLE
    state rather than an invitation to run it again.
    """
    return _committed(store, INTENT_KIND, intent_operation_id(job_id),
                      INTENT_MEMBERS, named="job_id", value=job_id)


def execution_result_of(store, job_id):
    return _committed(store, RESULT_KIND, result_operation_id(job_id),
                      RESULT_MEMBERS, named="job_id", value=job_id)


def handoff_of(store, job_id):
    """The ONE validated custody/execution handoff of one successor, or None.

    THIS IS WHAT OPENS THE GATE. `retained_recovery.execution_gate` asks this
    and nothing else -- not the verification account, which says a command
    exited 0, and not the readiness, which is derived. A gate that opened on a
    passed account alone would release a review with no proved delivery of the
    candidate it is about, which is the defect Stage 1-B's own review named.
    """
    return _committed(store, HANDOFF_KIND, handoff_operation_id(job_id),
                      HANDOFF_MEMBERS, named="job_id", value=job_id)


def renewed_failure_of(store, job_id):
    return _committed(store, RENEWED_KIND, renewed_operation_id(job_id),
                      RENEWED_MEMBERS, named="job_id", value=job_id)


def renewed_analysis_of(store, job_id):
    return _committed(store, RENEWED_ANALYSIS_KIND,
                      renewed_analysis_operation_id(job_id),
                      RENEWED_ANALYSIS_MEMBERS, named="job_id", value=job_id)


def renewed_item_of(store, job_id):
    return _committed(store, RENEWED_ITEM_KIND,
                      renewed_item_operation_id(job_id),
                      RENEWED_ITEM_MEMBERS, named="job_id", value=job_id)


def renewed_endpoint_of(store, job_id):
    return _committed(store, RENEWED_ENDPOINT_KIND,
                      renewed_endpoint_operation_id(job_id),
                      RENEWED_ENDPOINT_MEMBERS, named="job_id", value=job_id)


def hold_of(store, job_id):
    return _committed(store, HOLD_KIND, hold_operation_id(job_id),
                      HOLD_MEMBERS, named="job_id", value=job_id)


def owner_items_of(store):
    """Every Stage 1-C owner item this store holds, oldest identity first.

    TWO SHAPES AND THEY ARE NOT ONE. A renewed verification failure and a
    post-verification hold are different things for the owner to do next --
    the first needs a diagnosis and a new decision, the second needs a
    review-only decision against evidence that is still valid -- and an answer
    that merged them would make the owner read the body to find out which.
    """
    return {"renewed": _records_of(store, RENEWED_ITEM_KIND,
                                   RENEWED_ITEM_MEMBERS),
            "endpoints": _records_of(store, RENEWED_ENDPOINT_KIND,
                                     RENEWED_ENDPOINT_MEMBERS),
            "held": _records_of(store, HOLD_KIND, HOLD_MEMBERS)}


# -- 5. what is owed next ------------------------------------------------------

VERIFICATION_ACTS = ("materialize", "execute", "hand-off", "renew", "hold")
# WHICH ACT EACH OWED WORD IS. `execution_readiness` answers in the words an
# operator reads -- including "the post-verification hold" and the two that
# name an OWNER's next act rather than this pass's -- so the mapping to this
# pass's closed act vocabulary lives here rather than being inferred from a
# prefix.
_ACT_OF = {"materialize": "materialize", "execute": "execute",
           "hand-off": "hand-off", "renew": "renew",
           "the post-verification hold": "hold"}
VERIFICATION_OUTCOMES = ("materialized", "executed", "handed-off", "renewed",
                         "held", "refused")

EXECUTION_STATES = ("unmaterialized", "materialized", "unknown", "verified",
                    "failed", "handed-off", "renewed", "held", "cancelled",
                    "expired")


def _fence(store, job_id):
    return cancellation.fence_of(store, job_id)


def _expired(fence):
    """Is this fence an EXPIRY rather than the operator's cancellation?

    `retained_recovery._review_only_evidence`'s reading, by the same member:
    a record from before `trigger` existed is read as the operator's, which is
    the conservative half -- an operator cancellation is never revived, and
    reading one as an expiry would be the revival.
    """
    return fence is not None and fence.get("trigger", "operator") != "operator"


def _cancelled(fence):
    return fence is not None and fence.get("trigger", "operator") == "operator"


def _review_completed(store, held):
    """Has the successor's review stage reached a terminal state of its own?

    ASKED OF THE EPISODE HISTORY, which is the Job store's own record of what
    each attempt at that stage ended as. A review that COMPLETED is not owed
    a post-verification hold -- the recovery reached its outcome -- and a
    review that is queued, offered, claimed, running or abandoned is exactly
    the "before review completes" the disposition is for.
    """
    stage_id = documents.stage_id(held["job_id"],
                                  retained_recovery.REVIEW_STAGE)
    for one in episodes.episodes_of(store, stage_id):
        if one["ended_state"] in documents.TERMINAL_STAGE_STATES:
            return True
    return False


def execution_readiness(store, held):
    """WHICH ACT IS OWED NEXT for one admitted successor, said out loud.

    `retained_recovery.successor_readiness`'s own truthfulness requirement,
    carried forward: an answer that merely reported a record would read as
    though the recovery had happened. This one names the state, the act that
    is owed and whether the review stage may be released.
    """
    job_id = held["job_id"]
    stages = tuple(held["stages"])
    review_only = stages == retained_recovery.REVIEW_ONLY_STAGES
    fence = _fence(store, job_id)
    handoff = handoff_of(store, job_id)
    verification = retained_recovery.verification_of(store, job_id)
    material = materialization_of(store, job_id)
    if _cancelled(fence):
        return {"state": "cancelled", "owed": None, "review": "blocked",
                "verification": ("omitted" if review_only else "abandoned"),
                "detail": "this successor was cancelled; a cancelled "
                          "execution is never revived and nothing further is "
                          "admitted under its identity"}
    if renewed_item_of(store, job_id) is not None:
        return {"state": "renewed", "owed": "a new owner decision",
                "review": "blocked", "verification": "failed",
                "detail": "the renewed verification failure has its own "
                          "failure key, one analysis and one owner item; "
                          "another successor requires a new owner decision "
                          "and is never admitted automatically"}
    if hold_of(store, job_id) is not None:
        return {"state": "held", "owed": "a review-only owner decision",
                "review": "blocked", "verification": "passed",
                "detail": "the successful verification is preserved and the "
                          "owner holds an item; time expiry alone does not "
                          "invalidate it, and no analysis or retry follows"}
    if _expired(fence):
        # EXPIRY IS ASKED BEFORE THE HANDOFF, which is section 3.7 exactly:
        # the disposition is for a successor that expired "before review
        # completes, INCLUDING A BUSY-REVIEWER WAIT" -- so the candidate
        # having already been handed to a review that nobody finished is the
        # ordinary shape of this ending rather than a reason to skip it.
        passed = (review_only or (verification is not None
                                  and verification["outcome"] == "passed"))
        return {"state": "expired",
                "owed": ("the post-verification hold"
                         if passed and not _review_completed(store, held)
                         else None),
                "review": "blocked",
                "verification": ("omitted" if review_only else
                                 "unknown" if verification is None
                                 else verification["outcome"]),
                "detail": "this successor's admitted deadline passed; the "
                          "old deadline is unchanged, a passed verification "
                          "is preserved rather than invalidated, and no "
                          "further admission happens without a new owner "
                          "decision"}
    if handoff is not None:
        return {"state": "handed-off", "owed": None, "review": "releasable",
                "verification": ("omitted" if review_only else "passed"),
                "detail": "the exact retained candidate and this execution's "
                          "own evidence are bound to the review stage; the "
                          "configured independent reviewer is admitted by the "
                          "ordinary manager tick and this manager "
                          "manufactures no verdict"}
    if material is None:
        return {"state": "unmaterialized", "owed": "materialize",
                "review": "blocked",
                "verification": ("omitted" if review_only else "owed"),
                "detail": "the exact retained candidate has not been "
                          "materialized into a private verification "
                          "workspace yet; the retained custody is unchanged"}
    if review_only:
        return {"state": "materialized", "owed": "hand-off",
                "review": "blocked", "verification": "omitted",
                "detail": "the approved profile's verification stage is "
                          "omitted under this decision; the passed "
                          "verification named in the lineage stands, is not "
                          "repeated, and the same candidate is owed to review"}
    if verification is None:
        if execution_intent_of(store, job_id) is not None:
            # THE ONE UNCERTAIN STATE, REPORTED AS ONE. A journalled intent
            # with no account means a process said it was about to run the
            # approved command and never said what happened. REC-4: unknown
            # is an actionable state with exact references, not a synonym for
            # "safe to retry" -- so nothing is owed here, the pass goes quiet
            # and the owner is the one who disposes of it.
            return {"state": "unknown", "owed": None, "review": "blocked",
                    "verification": "unknown",
                    "detail": "this successor journalled the intent to run "
                              "its approved verification and journalled no "
                              "account of it; whether that command ran is "
                              "UNKNOWN, this manager never starts a second "
                              "one, and the retained output is reconciled "
                              "through its owner or disposed of by a new "
                              "owner decision"}
        return {"state": "materialized", "owed": "execute",
                "review": "blocked", "verification": "owed",
                "detail": "the owner-approved corrected command has not run "
                          "yet; only that argv, in the approved context, is "
                          "reachable from here"}
    if verification["outcome"] != "passed":
        return {"state": "failed", "owed": "renew", "review": "blocked",
                "verification": verification["outcome"],
                "detail": "this verification did not pass; it earns one new "
                          "failure key, one analysis and one owner item, and "
                          "never an automatic further successor"}
    return {"state": "verified", "owed": "hand-off", "review": "blocked",
            "verification": "passed",
            "detail": "the verification passed and the same candidate is "
                      "owed to independent substantive review; the review "
                      "stage stays blocked until that handoff is validated"}


def successor_execution(store, job_id):
    """Every Stage 1-C record of one successor, for the owner's own read.

    REPORTED BESIDE THE ADMISSION RATHER THAN MERGED INTO IT. The owner item
    surface is `retained_recovery.owner_item_read`'s, and what this adds is
    the execution half: what was materialized, what ran, what was handed to
    review, and which of the two finite endings the successor reached.
    """
    boundaries.identity(job_id, "a successor Job id")
    return {"materialization": materialization_of(store, job_id),
            "result": execution_result_of(store, job_id),
            "handoff": handoff_of(store, job_id),
            "renewed_failure": renewed_failure_of(store, job_id),
            "renewed_analysis": renewed_analysis_of(store, job_id),
            "renewed_item": renewed_item_of(store, job_id),
            "renewed_endpoint": renewed_endpoint_of(store, job_id),
            "hold": hold_of(store, job_id)}


# -- 6. the admitted successor this module acts for ----------------------------

def _successor(store, decision_id):
    held = retained_recovery.successor_of(store, decision_id)
    if held is None:
        _refuse(f"this store holds no admitted successor for decision "
                f"{name_value(decision_id)}; a verification execution belongs "
                f"to an admitted recovery and never to one nobody admitted")
    return held


def _unfenced(store, job_id, what):
    """Cancellation and expiry re-read through their owner, at every act.

    THE CONTRACT'S SECTION 4: "Recheck cancellation/ownership at admission and
    dispatch." An act that read the fence once and then performed three
    effects would be acting on a fact that was true earlier.
    """
    fence = _fence(store, job_id)
    if _cancelled(fence):
        _refuse(f"successor {name_value(job_id)} was cancelled at "
                f"{fence['requested_at']} ({fence['reason']}); {what} is not "
                f"performed for a cancelled execution, and a cancelled "
                f"execution is never revived")
    if _expired(fence):
        _refuse(f"successor {name_value(job_id)}'s admitted deadline passed "
                f"at {fence['requested_at']} ({fence['reason']}); {what} is "
                f"not performed under an expired admission, and this old "
                f"deadline is not reset or extended")
    return fence


def _candidate(store, control, held):
    """The retained candidate AS IT STANDS NOW, through its owning reader."""
    return retained_recovery.candidate_now(store, control,
                                           held["failure_key"],
                                           expected=held["candidate"])


# -- 7. act one: materialize ---------------------------------------------------

def _custody_place(control, candidate, *, attempt_id):
    """WHERE THE RETAINED CANDIDATE'S BYTES ARE, read through their owner.

    THE LOCATOR IS THE CONTROL STORE'S OWN ARTIFACT ROW and not an operand:
    `frozen_output_of` is the Worker Manager's indexed answer about what one
    attempt froze, and the row's `locator` is where that owner sealed the
    tree. So this module follows a path the custody owner published for the
    exact artifact the admission bound, and nothing else -- the contract's
    "preserve paths as evidence locators, not authority to read arbitrary host
    files", kept by having no other path to follow.
    """
    frozen = frozen_output_of(control, attempt_id)
    if frozen is None:
        _refuse(f"the control store holds no frozen result for attempt "
                f"{name_value(attempt_id)}; the retained candidate's custody "
                f"is absent and absent evidence is not recovery input")
    artifacts = [one for one in frozen["artifacts"]
                 if one["artifact_id"] == candidate["artifact_id"]]
    if len(artifacts) != 1:
        _refuse(f"the frozen result of attempt {name_value(attempt_id)} "
                f"names {len(artifacts)} artifacts "
                f"{name_value(candidate['artifact_id'])}; one retained "
                f"candidate is one artifact row",
                category="integrity", code="schema")
    artifact = artifacts[0]
    if artifact["content_digest"] != candidate["content_digest"]:
        _refuse(f"the custody row for {name_value(artifact['artifact_id'])} "
                f"now measures {name_value(artifact['content_digest'])} and "
                f"this recovery is bound to "
                f"{name_value(candidate['content_digest'])}",
                category="integrity", code="digest")
    locator = artifact["locator"]
    if locator is None:
        _refuse(f"the custody row for {name_value(artifact['artifact_id'])} "
                f"publishes no locator; where the retained bytes are is "
                f"UNKNOWN, and unknown holds rather than being searched for")
    check_uri(locator, "a retained candidate custody locator")
    if not locator.startswith("file:///"):
        _refuse(f"this manager materializes a retained candidate from custody "
                f"it holds locally and {name_value(locator)} names another "
                f"scheme; an unsupported custody transport is reported rather "
                f"than guessed at",
                category="refused", code="capability")
    place = locator[len("file://"):]
    if not os.path.isdir(place) or os.path.islink(place):
        _refuse(f"the retained candidate custody at {name_value(locator)} is "
                f"not a directory this manager can read; the bytes a recovery "
                f"verifies must still be there",
                category="integrity", code="path")
    return place, locator


def _private_workspace(seam, held):
    """A NEW private workspace, named by the reserved verification identity.

    DERIVED RATHER THAN ALLOCATED, which is this whole path's replay rule: the
    admission reserved the verification's identity before any execution
    existed, so a re-entry after a crash composes the same workspace instead
    of leaving an orphan beside a second one.
    """
    root = os.path.join(seam["workspaces"], held["verification_attempt_id"])
    if os.path.islink(root):
        _refuse(f"the private verification workspace {name_value(root)} is a "
                f"symbolic link; a workspace this manager did not create is "
                f"not one it materializes a candidate into",
                category="integrity", code="path")
    os.makedirs(root, mode=0o700, exist_ok=True)
    os.chmod(root, 0o700)
    for one in WORKSPACE_ROOTS:
        os.makedirs(os.path.join(root, one), mode=0o700, exist_ok=True)
    return root


def materialize(store, seam, *, decision_id, now=None):
    """ACT ONE: the exact retained candidate, in a NEW private workspace.

    THE BYTES WRITTEN ARE THE BYTES MEASURED. `workspaces.copied_manifest` is
    the one no-follow pass that does both, which is why it is used rather than
    a measure-then-copy pair: a candidate whose tree changed between the two
    would be verified as one thing and recorded as another.

    AND THE ORIGINAL CUSTODY IS NEVER TOUCHED. This reads it, copies out of
    it, and compares the copy's measured tree digest with the digest the
    owner's decision bound. A mismatch refuses: the candidate before and
    after a recovery is one candidate.
    """
    taken = check_verification_seam(seam)
    _agreeing_instance(taken, what="this materialization")
    boundaries.identity(decision_id, "an owner decision id")
    held = _successor(store, decision_id)
    job_id = held["job_id"]
    recorded = materialization_of(store, job_id)
    if recorded is not None:
        return recorded
    _unfenced(store, job_id, "materializing the retained candidate")
    candidate = _candidate(store, taken["control"], held)
    source = candidate_source_profile(candidate)
    place, locator = _custody_place(
        taken["control"], candidate,
        attempt_id=_producer(store, held)["attempt_id"])
    root = _private_workspace(taken, held)
    into = os.path.join(root, CANDIDATE_ROOT)
    measured = copied_manifest(place, into)
    if measured["tree_digest"] != candidate["content_digest"]:
        _refuse(f"the retained candidate at {name_value(locator)} measures "
                f"{name_value(measured['tree_digest'])} in this private "
                f"workspace and this recovery is bound to "
                f"{name_value(candidate['content_digest'])}; a candidate that "
                f"does not materialize to the bytes it was approved as is "
                f"reported and is not recovery input",
                category="integrity", code="digest")
    record = {
        "failure_key": held["failure_key"], "decision_id": decision_id,
        "job_id": job_id,
        "verification_attempt_id": held["verification_attempt_id"],
        "stages": list(held["stages"]),
        "candidate": dict(candidate),
        "source": dict(source),
        "workspace": {"locator": "file://" + root,
                      "roots": list(WORKSPACE_ROOTS),
                      "candidate_root": CANDIDATE_ROOT,
                      "scratch_root": SCRATCH_ROOT,
                      "output_root": OUTPUT_ROOT,
                      "custody_locator": locator},
        "measured": {"tree_digest": measured["tree_digest"],
                     "entry_count": measured["entry_count"],
                     "total_bytes": measured["total_bytes"]},
        "materialized_at": boundaries.instant(
            now if now is not None else store._now(),
            "a materialization instant")}
    operands = {name: record[name] for name in MATERIALIZATION_MEMBERS
                if name != "materialized_at"}
    return store.transact(materialization_operation_id(job_id),
                          MATERIALIZATION_KIND,
                          job_signature(MATERIALIZATION_KIND, operands),
                          lambda connection: record)


# -- 8. act two: execute -------------------------------------------------------

def _bounded(stream, what):
    if type(stream) is str:
        stream = stream.encode("utf-8")
    if type(stream) is not bytes:
        _refuse(f"{what} is the exact bytes the command wrote; this is "
                f"{name_value(stream)}", category="integrity", code="schema")
    if len(stream) > MAX_OUTPUT_BYTES:
        return stream[:MAX_OUTPUT_BYTES], len(stream), True
    return stream, len(stream), False


def _ran(answer, *, what):
    """One bounded command's account, member by member.

    NOT THROUGH `boundaries.document`, and the reason is the one member that
    matters most: `stdout` and `stderr` are the EXACT BYTES a command wrote,
    and `contracts.own` refuses bytes because a durable document carries JSON
    data. The streams never become part of a journalled record -- what is
    journalled is their measured digest and their length -- so they are
    checked here, where they are still bytes, and the account is composed
    from the members this build reads.
    """
    if type(answer) is not dict:
        _refuse(f"{what} is one closed answer; this is "
                f"{name_value(answer)}", category="integrity", code="schema")
    missing = [one for one in RUN_MEMBERS if one not in answer]
    extra = sorted(one for one in answer if one not in RUN_MEMBERS)
    if missing or extra:
        _refuse(f"{what} carries exactly {', '.join(RUN_MEMBERS)}"
                + (f"; missing {', '.join(missing)}" if missing else "")
                + (f"; unexpected {', '.join(extra)}" if extra else ""),
                category="integrity", code="schema")
    held = dict(answer)
    status = held["exit_status"]
    if type(status) is not int or type(status) is bool or status < 0:
        _refuse(f"{what}'s exit status is a NON-NEGATIVE whole number; this "
                f"is {name_value(status)}. A durable record may not carry a "
                f"negative integer, so a child a signal terminated travels "
                f"as the shell's own `128 + signal` with the signal beside it",
                category="integrity", code="schema")
    signalled = held["signal"]
    if signalled is not None and (type(signalled) is not int
                                  or type(signalled) is bool
                                  or signalled <= 0):
        _refuse(f"{what}'s signal is a positive whole number or nothing at "
                f"all; this is {name_value(signalled)}",
                category="integrity", code="schema")
    if type(held["timed_out"]) is not bool:
        _refuse(f"{what} says whether the approved ceiling stopped the "
                f"command, as a boolean", category="integrity", code="schema")
    if held["timed_out"] and status == 0:
        _refuse(f"{what} says the approved per-command ceiling stopped this "
                f"command and that it exited 0; a command the ceiling stopped "
                f"did not pass its required verification",
                category="integrity", code="schema")
    for member in ("started_at", "ended_at"):
        boundaries.instant(held[member], f"{what}'s {member}")
    if held["ended_at"] < held["started_at"]:
        _refuse(f"{what} ended before it started; a retained timing that "
                f"cannot be ordered is not evidence about a duration",
                category="integrity", code="schema")
    return held


def _retained_output(root, *, status, streams, timing):
    """THIS EXECUTION'S OWN ACCOUNT, measured, under its own root.

    SEPARATE FROM THE CANDIDATE BY CONSTRUCTION. The contract's section 3.5:
    "scratch/generated test outputs are separate" and "do not publish
    verifier-mutated source as a new candidate". So the exit status, the two
    streams and the real timing are written under `output/verification`, which
    nothing reads as a candidate, and the digest below is the identity of that
    account rather than of any source tree.
    """
    place = os.path.join(root, OUTPUT_ROOT, RETAINED_OUTPUT)
    os.makedirs(place, mode=0o700, exist_ok=True)
    with open(os.path.join(place, "exit"), "wb") as writing:
        writing.write(f"{status}\n".encode("utf-8"))
    for name in ("stdout", "stderr"):
        with open(os.path.join(place, name), "wb") as writing:
            writing.write(streams[name])
    with open(os.path.join(place, "timing.json"), "wb") as writing:
        writing.write((json.dumps(timing, indent=2, sort_keys=True)
                       + "\n").encode("utf-8"))
    return place, directory_manifest(place)


EXECUTION_LOCK = ".verification.lock"


def _exclusive(root, *, what):
    """ONE RUNNER OF ONE SUCCESSOR'S APPROVED COMMAND, in this host.

    THE LOCK IS IN THE MANAGER'S OWN PRIVATE WORKSPACE, which is the one
    place this operation already owns exclusively, and it is `flock` for
    `fresh_attempt_ports.DeploymentBinding._publishing`'s reason: two opens in
    one process contend for it exactly as two processes do, and the kernel
    releases it if the holder dies. A journal identity alone cannot close this
    window -- two callers that both read "no result yet" would both start a
    child process before either committed -- and the contract is explicit that
    "exactly once" must not be claimed from deduplication alone.
    """
    import contextlib

    place = os.path.join(root, EXECUTION_LOCK)

    @contextlib.contextmanager
    def holding():
        descriptor = os.open(place,
                             os.O_RDWR | os.O_CREAT | os.O_CLOEXEC, 0o600)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            yield
        finally:
            os.close(descriptor)

    return holding()


def execute(store, seam, *, decision_id, now=None):
    """ACT TWO: the owner-approved corrected command, and nothing else.

    THE CONTEXT IS CHECKED BEFORE THE COMMAND RUNS, by digest, against what
    the owner approved. A deployment whose declared working directory,
    environment or tool selection has moved since the decision does not get to
    run the approved argv in a context nobody approved -- "a command string
    must not hide a changed execution context", and the digest is where that
    is enforceable.

    ZERO AUTOMATIC RETRY AND ZERO CORRECTION. The approved profile says so and
    this operation keeps it by being journalled once: a second call replays
    the first account rather than running the command again, which is also
    what makes `no repeated verifier effects` a property of the records.
    """
    taken = check_verification_seam(seam)
    _agreeing_instance(taken, what="this verification execution")
    boundaries.identity(decision_id, "an owner decision id")
    held = _successor(store, decision_id)
    job_id = held["job_id"]
    recorded = execution_result_of(store, job_id)
    if recorded is not None:
        return recorded
    if tuple(held["stages"]) == retained_recovery.REVIEW_ONLY_STAGES:
        _denied(f"successor {name_value(job_id)} was admitted for "
                f"{json.dumps(held['stages'])}: the approved profile's "
                f"verification stage is OMITTED under that decision and the "
                f"passed verification it names is reused rather than "
                f"repeated. Re-verifying here would be the blind "
                f"re-verification this contract refuses")
    _unfenced(store, job_id, "executing the approved corrected verification")
    material = materialization_of(store, job_id)
    if material is None:
        _refuse(f"successor {name_value(job_id)} has materialized no "
                f"candidate; the approved command runs against the exact "
                f"retained bytes in a private workspace and never against "
                f"whatever a working directory happens to hold")
    context = taken["context"]
    approved = held["correction"]["context_digest"]
    if context_digest(context) != approved:
        _refuse(f"this deployment's declared execution context digests to "
                f"{name_value(context_digest(context))} and the owner "
                f"approved {name_value(approved)} for successor "
                f"{name_value(job_id)}; changed inputs after approval require "
                f"a new decision",
                category="integrity", code="digest")
    candidate = _candidate(store, taken["control"], held)
    root = material["workspace"]["locator"][len("file://"):]
    argv = list(held["correction"]["argv"])
    bounds = retained_recovery.resolved_profile(held["bounds"]["profile"])
    ceiling = bounds["verification_command_seconds"]
    with _exclusive(root, what=f"successor {job_id}'s approved verification"):
        # RE-ASKED INSIDE THE WINDOW, because everything above was decided
        # before this process held it: a caller that waited here is a caller
        # whose answer was settled by whoever held it first.
        recorded = execution_result_of(store, job_id)
        if recorded is not None:
            return recorded
        intended = execution_intent_of(store, job_id)
        if intended is not None:
            # THE ONE UNCERTAIN WINDOW IN THIS SLICE, AND IT HOLDS. An intent
            # with no account means a process journalled that it was about to
            # run the approved command and never said what happened --
            # REC-4's "unknown is an actionable state with exact operation
            # references, not a synonym for safe to retry", and REC-5's
            # "lost transport does not authorize a second provider turn".
            _refuse(f"successor {name_value(job_id)} journalled the intent to "
                    f"run its approved verification at "
                    f"{intended['intended_at']} and journalled no account of "
                    f"it; whether that command ran is UNKNOWN, and this "
                    f"manager never starts a second one. Reconcile the "
                    f"retained output at "
                    f"{name_value(intended['workspace']['locator'])} through "
                    f"its owner, or take a new owner decision",
                    category="ambiguous", code="operation")
        before = directory_manifest(os.path.join(root, CANDIDATE_ROOT))
        if before["tree_digest"] != candidate["content_digest"]:
            _refuse(f"the materialized candidate in {name_value(root)} now "
                    f"measures {name_value(before['tree_digest'])} and this "
                    f"recovery is bound to "
                    f"{name_value(candidate['content_digest'])}; the command "
                    f"is not run against a workspace that changed under it",
                    category="integrity", code="digest")
        intent = {
            "failure_key": held["failure_key"], "decision_id": decision_id,
            "job_id": job_id,
            "verification_attempt_id": held["verification_attempt_id"],
            "argv": argv, "context_digest": approved,
            "context": {"working_directory": context["working_directory"],
                        "tool": dict(context["tool"]),
                        "runtime": dict(context["runtime"]),
                        "environment_names": sorted(context["environment"])},
            "candidate": dict(candidate),
            "workspace": {"locator": "file://" + root,
                          "candidate_root": CANDIDATE_ROOT,
                          "candidate_tree_digest": before["tree_digest"],
                          "ceiling_seconds": ceiling},
            "intended_at": boundaries.instant(
                now if now is not None else store._now(),
                "a verification intent instant")}
        operands = {name: intent[name] for name in INTENT_MEMBERS
                    if name != "intended_at"}
        store.transact(intent_operation_id(job_id), INTENT_KIND,
                       job_signature(INTENT_KIND, operands),
                       lambda connection: intent)
        answer = _ran(taken["runner"].run(
            argv, cwd=os.path.join(root, context["working_directory"]),
            environment=dict(context["environment"]),
            timeout_seconds=ceiling),
            what="the retained verification's own run")
        return _accounted(store, taken, held=held, decision_id=decision_id,
                          candidate=candidate, root=root, context=context,
                          argv=argv, approved=approved, bounds=bounds,
                          ceiling=ceiling, answer=answer, before=before,
                          now=now)


def _accounted(store, taken, *, held, decision_id, candidate, root, context,
               argv, approved, bounds, ceiling, answer, before, now):
    """Retain what the command did, journal it, and record the account.

    SPLIT OUT SO THE EFFECT AND ITS ACCOUNT READ IN ORDER. Everything here
    happens AFTER a child process has already run, which is the half a reader
    has to be able to find: the retained output tree, the second measurement
    of the candidate, this slice's own journalled result, and only then the
    supported durable account Stage 1-B owns.
    """
    job_id = held["job_id"]
    streams = {}
    sizes = {}
    for name in ("stdout", "stderr"):
        kept, size, truncated = _bounded(answer[name],
                                         f"the command's {name}")
        streams[name] = kept
        sizes[name] = {"bytes": size, "retained_bytes": len(kept),
                       "truncated": truncated,
                       "content_digest": digest_of_bytes(kept)}
    timing = {"started_at": answer["started_at"],
              "ended_at": answer["ended_at"],
              "ceiling_seconds": ceiling,
              "ceiling_origin": bounds["verification_command_origin"],
              "timed_out": answer["timed_out"],
              "signal": answer["signal"]}
    place, retained = _retained_output(root, status=answer["exit_status"],
                                       streams=streams, timing=timing)
    # AND THE CANDIDATE AFTER, which is the same question asked again. A
    # verifier that wrote into the tree it was verifying is REPORTED here and
    # the handoff refuses it; what is never done is publishing that tree.
    after = directory_manifest(os.path.join(root, CANDIDATE_ROOT))
    outcome = "passed" if answer["exit_status"] == 0 else "failed"
    record = {
        "failure_key": held["failure_key"], "decision_id": decision_id,
        "job_id": job_id,
        "verification_attempt_id": held["verification_attempt_id"],
        "outcome": outcome, "exit_status": answer["exit_status"],
        "argv": argv, "context_digest": approved,
        "context": {"working_directory": context["working_directory"],
                    "tool": dict(context["tool"]),
                    "runtime": dict(context["runtime"]),
                    "environment_names": sorted(context["environment"])},
        "candidate": dict(candidate),
        "workspace": {"locator": "file://" + root,
                      "candidate_tree_digest_before": before["tree_digest"],
                      "candidate_tree_digest_after": after["tree_digest"],
                      "candidate_unchanged":
                          after["tree_digest"] == before["tree_digest"]},
        "retained": {"locator": "file://" + place,
                     "result_digest": retained["tree_digest"],
                     "entry_count": retained["entry_count"],
                     "total_bytes": retained["total_bytes"],
                     "streams": sizes},
        "timing": timing,
        "concluded_at": boundaries.instant(
            now if now is not None else store._now(),
            "a verification conclusion instant")}
    operands = {name: record[name] for name in RESULT_MEMBERS
                if name != "concluded_at"}
    journalled = store.transact(result_operation_id(job_id), RESULT_KIND,
                                job_signature(RESULT_KIND, operands),
                                lambda connection: record)
    # THE ATTRIBUTABLE DURABLE ACCOUNT THE ADMISSION OWNS, written through the
    # supported boundary Stage 1-B published for exactly this adapter. Second,
    # because that record is what a later review-only admission trusts and it
    # must never exist for an execution whose own account did not commit.
    retained_recovery.record_verification(
        store, taken["control"], decision_id=decision_id, outcome=outcome,
        exit_status=answer["exit_status"], argv=argv,
        context_digest=approved,
        result_digest=journalled["retained"]["result_digest"],
        now=journalled["concluded_at"])
    return journalled


# -- 9. act three: hand the SAME candidate to independent review ---------------

def _reused_verification(store, held):
    """The PASSED verification a handoff rests on, for either stage set.

    FULL: this successor's own journalled account. REVIEW-ONLY: the account
    the owner's decision named in its lineage, which Stage 1-B already
    validated at admission against the expired successor, its exact command
    and its exact candidate -- re-validated here by identity and digest,
    because a late result of another execution cannot satisfy this one by
    identity substitution.
    """
    job_id = held["job_id"]
    if tuple(held["stages"]) != retained_recovery.REVIEW_ONLY_STAGES:
        verification = retained_recovery.verification_of(store, job_id)
        if verification is None:
            _refuse(f"successor {name_value(job_id)} journalled no "
                    f"verification account; whether its verification passed "
                    f"is UNKNOWN, unknown holds, and a review is not released "
                    f"against it")
        if verification["outcome"] != "passed":
            _denied(f"successor {name_value(job_id)}'s verification is "
                    f"{name_value(verification['outcome'])} (exit "
                    f"{verification['exit_status']}); only a PASSED "
                    f"verification hands a candidate to review, and a failed "
                    f"one earns one new analysis and owner item instead")
        return verification, "this successor's own passed verification"
    decision = retained_recovery.decision_of(store, held["decision_id"])
    lineage = (decision or {}).get("lineage")
    if not lineage:
        _refuse(f"successor {name_value(job_id)} was admitted review-only and "
                f"its decision names no retained verification lineage; the "
                f"evidence a review-only handoff reuses is exact")
    prior = retained_recovery.verification_of(store,
                                              lineage["successor_job_id"])
    if prior is None:
        _refuse(f"the review-only lineage of {name_value(job_id)} names "
                f"successor {name_value(lineage['successor_job_id'])}, which "
                f"journalled no verification account; absent evidence refuses "
                f"and is never permission to verify again")
    if prior["verification_attempt_id"] != lineage["verification_attempt_id"]:
        _refuse(f"the review-only lineage names verification attempt "
                f"{name_value(lineage['verification_attempt_id'])} and the "
                f"journalled account is "
                f"{name_value(prior['verification_attempt_id'])}; a late "
                f"result of another execution cannot satisfy this one by "
                f"identity substitution",
                category="integrity", code="schema")
    if digest(prior) != lineage["verification_result_digest"]:
        _refuse(f"the review-only lineage names verification result "
                f"{name_value(lineage['verification_result_digest'])} and the "
                f"journalled account digests to {name_value(digest(prior))}",
                category="integrity", code="digest")
    if prior["outcome"] != "passed":
        _denied(f"the review-only lineage of {name_value(job_id)} names a "
                f"{name_value(prior['outcome'])} verification; a review-only "
                f"admission reuses a PASSED one")
    return prior, (f"the passed verification of expired successor "
                   f"{lineage['successor_job_id']}, reused and not repeated")


def _producer(store, held):
    """WHO PRODUCED THE CANDIDATE, from the original failure's own record.

    Reported so the review's evidence names the producer it is independent OF
    rather than leaving that to be inferred. It is the original attempt's
    attribution, unchanged: this recovery never publishes as the stopped
    producer.
    """
    failure = failure_analysis.failure_of(store, held["failure_key"])
    if failure is None:                                    # pragma: no cover
        _refuse(f"this store holds no retained failure "
                f"{name_value(held['failure_key'])}")
    return {"job_id": failure["job_id"], "stage_id": failure["stage_id"],
            "attempt_id": failure["selectors"]["attempt_id"],
            "result_id": failure["selectors"]["result_id"],
            "participant": failure["execution"]["participant"],
            "principal": failure["execution"]["principal"],
            "generation": failure["execution"]["generation"],
            "declared_ending": failure["execution"]["declared_ending"],
            "input_digest": failure["input_digest"]}


def hand_off(store, seam, *, decision_id, now=None):
    """ACT THREE: bind the SAME candidate and this evidence to the review.

    WHAT THIS RELEASES AND WHAT IT DOES NOT. After this record commits,
    `retained_recovery.execution_gate` reports the review stage's gate OPEN
    and the ordinary manager tick admits the deployment's configured
    independent reviewer -- automatically, which is REC-8's "Successful
    verification MUST hand the same candidate and attributable evidence to
    independent substantive review automatically". What it does not do is
    judge: no verdict is written here, no structural check is treated as
    acceptance, and the reviewer's own required verification and investigation
    remain the reviewer's.

    THE CANDIDATE IS RE-MEASURED ONE LAST TIME. A workspace the verifier
    changed is refused rather than handed on, and the identity that travels is
    the CUSTODY's -- so what review consumes is the bound candidate and never
    an unverified changed workspace.
    """
    taken = check_verification_seam(seam)
    _agreeing_instance(taken, what="this review handoff")
    boundaries.identity(decision_id, "an owner decision id")
    held = _successor(store, decision_id)
    job_id = held["job_id"]
    recorded = handoff_of(store, job_id)
    if recorded is not None:
        return recorded
    _unfenced(store, job_id, "handing the retained candidate to review")
    material = materialization_of(store, job_id)
    if material is None:
        _refuse(f"successor {name_value(job_id)} has materialized no "
                f"candidate; a review handoff delivers bytes this manager "
                f"proved rather than a name it was given")
    verification, why = _reused_verification(store, held)
    candidate = _candidate(store, taken["control"], held)
    for member in ("base", "head", "content_digest"):
        if verification["candidate"][member] != candidate[member]:
            _refuse(f"the reused verification names candidate {member} "
                    f"{name_value(verification['candidate'][member])} and the "
                    f"retained candidate is {name_value(candidate[member])}; "
                    f"the candidate before and after a recovery is one "
                    f"candidate",
                    category="integrity", code="digest")
    root = material["workspace"]["locator"][len("file://"):]
    measured = directory_manifest(os.path.join(root, CANDIDATE_ROOT))
    if measured["tree_digest"] != candidate["content_digest"]:
        _refuse(f"the materialized candidate in {name_value(root)} now "
                f"measures {name_value(measured['tree_digest'])} and this "
                f"recovery is bound to "
                f"{name_value(candidate['content_digest'])}; verifier output "
                f"never becomes a new candidate and a changed workspace is "
                f"not handed to review",
                category="integrity", code="digest")
    result = execution_result_of(store, job_id)
    record = {
        "failure_key": held["failure_key"], "decision_id": decision_id,
        "job_id": job_id,
        "review_stage_id": retained_recovery.review_stage_id(decision_id),
        "stages": list(held["stages"]),
        "candidate": dict(candidate),
        "producer": _producer(store, held),
        "verification": {
            "why": why,
            "attempt_id": verification["verification_attempt_id"],
            "outcome": verification["outcome"],
            "exit_status": verification["exit_status"],
            "argv": list(verification["argv"]),
            "context_digest": verification["context_digest"],
            "result_digest": verification["result_digest"],
            "account_digest": digest(verification),
            "retained_locator": (None if result is None
                                 else result["retained"]["locator"])},
        "workspace": {"locator": material["workspace"]["locator"],
                      "candidate_root": CANDIDATE_ROOT,
                      "tree_digest": measured["tree_digest"],
                      "entry_count": measured["entry_count"],
                      "delivered": "read-only"},
        "evidence": {"decision_digest": digest(
                         retained_recovery.decision_of(store, decision_id)),
                     "successor_digest": digest(held),
                     "materialization_digest": digest(material),
                     "custody_locator":
                         material["workspace"]["custody_locator"]},
        "handed_at": boundaries.instant(
            now if now is not None else store._now(),
            "a review handoff instant")}
    operands = {name: record[name] for name in HANDOFF_MEMBERS
                if name != "handed_at"}
    return store.transact(handoff_operation_id(job_id), HANDOFF_KIND,
                          job_signature(HANDOFF_KIND, operands),
                          lambda connection: record)


# -- 10. act four: ONE renewed failure, ONE analysis, ONE owner item -----------

def renewed_failure_key(store, held):
    """The stable identity of ONE RENEWED verification failure.

    ITS OWN KEY, DERIVED THROUGH THE SAME OWNER. The contract: "A successor's
    verification failure has its own key", over the same six selectors
    `failure_analysis.failure_key` is composed from -- so a renewed failure can
    never collide with the original it followed, and the two remain visibly
    distinct records of two different endings.
    """
    return failure_analysis.failure_key(
        authority_uuid=store.authority_uuid, work_id=held["work_id"],
        job_id=held["job_id"],
        stage_id=documents.stage_id(held["job_id"],
                                   retained_recovery.VERIFICATION_STAGE),
        attempt_id=held["verification_attempt_id"],
        result_id=f"verification-result-{held['job_id']}")


def renewed_input(store, held, *, key, result):
    """THE IMMUTABLE DOCUMENT ONE RENEWED ANALYSIS IS ABOUT.

    Composed once and digested, exactly as `failure_analysis.analysis_input`
    is and for its reason: an agent that received this input and answered
    about something else is refused, and an evidence set that changed under a
    running analysis invalidates the report rather than the evidence.
    """
    return {
        "schema": RENEWED_INPUT_SCHEMA,
        "failure_key": key,
        "original_failure_key": held["failure_key"],
        "selectors": {"authority_uuid": store.authority_uuid,
                      "work_id": held["work_id"], "job_id": held["job_id"],
                      "stage_id": documents.stage_id(
                          held["job_id"],
                          retained_recovery.VERIFICATION_STAGE),
                      "attempt_id": held["verification_attempt_id"],
                      "result_id": f"verification-result-{held['job_id']}"},
        "decision_id": held["decision_id"],
        "candidate": dict(result["candidate"]),
        "verification": {"outcome": result["outcome"],
                         "exit_status": result["exit_status"],
                         "argv": list(result["argv"]),
                         "context_digest": result["context_digest"],
                         "context": dict(result["context"]),
                         "retained": dict(result["retained"]),
                         "timing": dict(result["timing"]),
                         "workspace": dict(result["workspace"])},
    }


def renew(store, seam, *, decision_id, now=None):
    """ACT FOUR: the renewed failure, its one analysis, its one owner item.

    THREE RECORDS AND NOT ONE EFFECT MORE. REC-8: "Renewed verification
    failure produces one new analysis and owner item; another successor
    requires a new owner decision, never an automatic recovery loop." So this
    journals the new failure key, the one analysis intent it earns under the
    owner-approved `stage1-analysis/1` bounds, and the one owner item -- and
    admits nothing, dispatches no successor and proposes no correction.

    A SECOND CALL REPLAYS. Each of the three has its own derived identity, so
    a restart between any two of them finishes rather than repeating, and a
    second observation of the same failed verification writes nothing.
    """
    taken = check_verification_seam(seam)
    boundaries.identity(decision_id, "an owner decision id")
    held = _successor(store, decision_id)
    job_id = held["job_id"]
    delivered = renewed_item_of(store, job_id)
    if delivered is not None:
        return {"failure": renewed_failure_of(store, job_id),
                "analysis": renewed_analysis_of(store, job_id),
                "item": delivered}
    result = execution_result_of(store, job_id)
    if result is None:
        _refuse(f"successor {name_value(job_id)} journalled no verification "
                f"execution; a renewed failure is attributed to an execution "
                f"this manager performed and never to one nobody ran")
    if result["outcome"] != "failed":
        _denied(f"successor {name_value(job_id)}'s verification is "
                f"{name_value(result['outcome'])}; a renewed failure follows "
                f"a FAILED required verification and a passed one is handed "
                f"to review instead")
    key = renewed_failure_key(store, held)
    if key == held["failure_key"]:                         # pragma: no cover
        _refuse("a renewed verification failure must not share the original "
                "failure's key", category="integrity", code="schema")
    fixed = renewed_input(store, held, key=key, result=result)
    input_digest = digest(own(fixed, what="a renewed verification input"))
    instant = boundaries.instant(now if now is not None else store._now(),
                                 "a renewed failure instant")
    failure = {
        "failure_key": key, "original_failure_key": held["failure_key"],
        "decision_id": decision_id, "job_id": job_id,
        "stage_id": fixed["selectors"]["stage_id"],
        "selectors": dict(fixed["selectors"]),
        "candidate": dict(result["candidate"]),
        "verification": dict(fixed["verification"]),
        "input_digest": input_digest,
        # THE TWO FACTS AN OWNER READS FIRST, and both are refusals of an
        # automatic loop rather than descriptions of one.
        "successor": None, "next": "a new explicit owner decision",
        "recorded_at": instant}
    operands = {name: failure[name] for name in RENEWED_MEMBERS
                if name != "recorded_at"}
    journalled = store.transact(renewed_operation_id(job_id), RENEWED_KIND,
                                job_signature(RENEWED_KIND, operands),
                                lambda connection: failure)
    declaration = taken["declaration"]
    policy = failure_analysis.resolved_profile(declaration["profile"])
    analysis = {
        "failure_key": key, "original_failure_key": held["failure_key"],
        "decision_id": decision_id, "job_id": job_id,
        "stage_id": journalled["stage_id"],
        "input_digest": input_digest,
        "declaration_digest":
            failure_analysis.declaration_digest(declaration),
        "role": declaration["role"],
        "participant": declaration["participant"],
        "principal": declaration["principal"],
        "worker_id": declaration["worker_id"],
        "profile": declaration["profile"],
        "profile_digest": declaration["profile_digest"],
        "policy": policy,
        "deadlines": failure_analysis.admitted_deadlines(policy,
                                                         admitted_at=instant)}
    intent = {name: analysis[name] for name in RENEWED_ANALYSIS_MEMBERS
              if name != "deadlines"}
    admitted = store.transact(renewed_analysis_operation_id(job_id),
                              RENEWED_ANALYSIS_KIND,
                              job_signature(RENEWED_ANALYSIS_KIND, intent),
                              lambda connection: analysis)
    item = {
        "failure_key": key, "original_failure_key": held["failure_key"],
        "decision_id": decision_id, "job_id": job_id,
        "destination": taken["destination"],
        "outcome": RENEWED_OUTCOME,
        "reason": (f"the owner-approved corrected verification of this "
                   f"retained candidate exited "
                   f"{result['exit_status']}"
                   + (" at its approved per-command ceiling"
                      if result["timing"]["timed_out"] else "")),
        "analysis": {"failure_key": key,
                     "declaration_digest": admitted["declaration_digest"],
                     "profile": admitted["profile"],
                     "profile_digest": admitted["profile_digest"],
                     "deadlines": dict(admitted["deadlines"])},
        "automatic_successor": False,
        "delivered_at": instant}
    operands = {name: item[name] for name in RENEWED_ITEM_MEMBERS
                if name != "delivered_at"}
    return {"failure": journalled, "analysis": admitted,
            "item": store.transact(renewed_item_operation_id(job_id),
                                   RENEWED_ITEM_KIND,
                                   job_signature(RENEWED_ITEM_KIND, operands),
                                   lambda connection: item)}


def deliver_renewed_endpoint(store, seam, *, decision_id, outcome, reason,
                             now=None):
    """The RENEWED analysis's own finite ending, straight to the owner.

    NO RECURSION, WHICH IS THE WHOLE OF THIS FUNCTION. "Failed analysis again
    goes directly to owner without recursion": an analysis of a renewed
    failure that failed, expired or was cancelled records its ending and
    stops. It records no new failure key, admits no replacement, triggers no
    second analysis and -- deliberately -- creates no second owner ITEM: the
    renewed failure's one item already exists and already names the analysis
    this is the ending of, so a second one would be a second item for one
    failure. This is journalled BESIDE it, once.
    """
    taken = check_verification_seam(seam)
    boundaries.identity(decision_id, "an owner decision id")
    if outcome not in ENDPOINT_OUTCOMES:
        _refuse(f"a renewed analysis endpoint is one of "
                f"{', '.join(ENDPOINT_OUTCOMES)}; this is "
                f"{name_value(outcome)}", category="integrity", code="schema")
    held = _successor(store, decision_id)
    job_id = held["job_id"]
    recorded = renewed_endpoint_of(store, job_id)
    if recorded is not None:
        return recorded
    failure = renewed_failure_of(store, job_id)
    if failure is None:
        _refuse(f"successor {name_value(job_id)} recorded no renewed failure; "
                f"an analysis endpoint belongs to an attributed ending")
    admitted = renewed_analysis_of(store, job_id)
    record = {
        "failure_key": failure["failure_key"],
        "original_failure_key": held["failure_key"],
        "decision_id": decision_id, "job_id": job_id,
        "destination": taken["destination"], "outcome": outcome,
        "reason": boundaries.text(reason,
                                  "a renewed analysis endpoint reason"),
        "analysis": (None if admitted is None else
                     {"failure_key": failure["failure_key"],
                      "declaration_digest": admitted["declaration_digest"],
                      "profile": admitted["profile"],
                      "profile_digest": admitted["profile_digest"],
                      "deadlines": dict(admitted["deadlines"])}),
        # THE TWO THINGS THIS ENDING IS NOT, said rather than left to be
        # inferred from an absence.
        "automatic_retry": None, "recursive_analysis": None,
        "recorded_at": boundaries.instant(
            now if now is not None else store._now(),
            "a renewed analysis endpoint instant")}
    operands = {name: record[name] for name in RENEWED_ENDPOINT_MEMBERS
                if name != "recorded_at"}
    return store.transact(renewed_endpoint_operation_id(job_id),
                          RENEWED_ENDPOINT_KIND,
                          job_signature(RENEWED_ENDPOINT_KIND, operands),
                          lambda connection: record)


# -- 11. act five: the post-verification hold (M385611) ------------------------

def hold(store, seam, *, decision_id, now=None):
    """ACT FIVE: expiry after a PASSED verification preserves it and holds.

    M385611, AND IT IS NEITHER OF THE TWO THINGS IT LOOKS LIKE. A successor
    that expired after its verification passed but before review completed --
    including while waiting for a busy reviewer -- is not a verification
    failure and is not an acceptance. So this triggers no analysis and no
    retry: it preserves the successful verification and delivers ONE held
    owner item carrying the three lineage operands a review-only decision must
    name back, which is the gap Stage 1-B's review N1 left to this slice.

    "TIME EXPIRY ALONE DOES NOT INVALIDATE SUCCESSFUL VERIFICATION", so the
    evidence is reported with its own digest rather than re-derived; the old
    deadline stays exactly where it was, and nothing further is admitted
    without a new explicit owner decision.
    """
    taken = check_verification_seam(seam)
    boundaries.identity(decision_id, "an owner decision id")
    held = _successor(store, decision_id)
    job_id = held["job_id"]
    recorded = hold_of(store, job_id)
    if recorded is not None:
        return recorded
    fence = _fence(store, job_id)
    if not _expired(fence):
        _refuse(f"successor {name_value(job_id)} is "
                + ("cancelled" if _cancelled(fence) else "neither expired nor "
                                                         "cancelled")
                + f"; a post-verification hold is the disposition of an "
                  f"EXPIRED successor whose verification passed, and "
                  f"admitting one beside a live successor would hold an item "
                  f"about an execution still running")
    verification, why = _reused_verification(store, held)
    item = {
        "failure_key": held["failure_key"], "decision_id": decision_id,
        "job_id": job_id, "destination": taken["destination"],
        "outcome": HOLD_OUTCOME,
        "fence": {"trigger": fence.get("trigger", "operator"),
                  "requested_at": fence["requested_at"],
                  "reason": fence["reason"],
                  "operation_id": fence["operation_id"]},
        "verification": {
            "why": why,
            "attempt_id": verification["verification_attempt_id"],
            "outcome": verification["outcome"],
            "exit_status": verification["exit_status"],
            "argv": list(verification["argv"]),
            "context_digest": verification["context_digest"],
            "result_digest": verification["result_digest"],
            "account_digest": digest(verification)},
        "candidate": dict(held["candidate"]),
        # THE THREE OPERANDS A REVIEW-ONLY DECISION NAMES BACK, reported
        # rather than left to be computed: an owner who had to digest the
        # account themselves would be computing the thing the admission
        # compares.
        "lineage": {"successor_job_id": job_id,
                    "verification_attempt_id":
                        verification["verification_attempt_id"],
                    "verification_result_digest": digest(verification)},
        "analysis": None, "retry": None,
        "delivered_at": boundaries.instant(
            now if now is not None else store._now(),
            "a post-verification hold instant")}
    operands = {name: item[name] for name in HOLD_MEMBERS
                if name != "delivered_at"}
    return store.transact(hold_operation_id(job_id), HOLD_KIND,
                          job_signature(HOLD_KIND, operands),
                          lambda connection: item)


# -- 12. the level-triggered pass ----------------------------------------------

def _act(key, job_id, act, outcome, detail=None):
    """One tick-report entry, over this pass's own CLOSED vocabularies.

    `failure_analysis._analysis_record`'s rule: a tick report is a document
    rather than prose, so a word outside the two closed sets is refused here
    instead of reaching a reader as one.
    """
    if act not in VERIFICATION_ACTS:                       # pragma: no cover
        _refuse(f"a retained-verification act is one of "
                f"{', '.join(VERIFICATION_ACTS)}; this is {name_value(act)}",
                category="integrity", code="schema")
    if outcome not in VERIFICATION_OUTCOMES:               # pragma: no cover
        _refuse(f"a retained-verification outcome is one of "
                f"{', '.join(VERIFICATION_OUTCOMES)}; this is "
                f"{name_value(outcome)}", category="integrity", code="schema")
    return documents.recovery_verification(
        failure_key=key, job_id=job_id, act=act, outcome=outcome,
        **({} if detail is None else {"detail": detail}))


def _advancing(store, seam, held, now):
    """The ONE act this successor owes right now, performed or reported."""
    job_id = held["job_id"]
    key = held["failure_key"]
    readiness = execution_readiness(store, held)
    owed = readiness["owed"]
    if owed is None:
        return []
    if readiness["state"] == "expired":
        hold(store, seam, decision_id=held["decision_id"], now=now)
        return [_act(key, job_id, "hold", "held",
                     {"state": readiness["state"], "outcome": HOLD_OUTCOME})]
    if owed == "materialize":
        material = materialize(store, seam,
                               decision_id=held["decision_id"], now=now)
        return [_act(key, job_id, "materialize", "materialized",
                     {"tree_digest": material["measured"]["tree_digest"],
                      "source_profile": material["source"]["source_profile"]})]
    if owed == "execute":
        result = execute(store, seam, decision_id=held["decision_id"],
                         now=now)
        return [_act(key, job_id, "execute", "executed",
                     {"outcome": result["outcome"],
                      "exit_status": result["exit_status"]})]
    if owed == "renew":
        renewed = renew(store, seam, decision_id=held["decision_id"], now=now)
        return [_act(key, job_id, "renew", "renewed",
                     {"failure_key": renewed["failure"]["failure_key"],
                      "outcome": RENEWED_OUTCOME})]
    if owed == "hand-off":
        handoff = hand_off(store, seam, decision_id=held["decision_id"],
                           now=now)
        return [_act(key, job_id, "hand-off", "handed-off",
                     {"review_stage_id": handoff["review_stage_id"],
                      "candidate_digest":
                          handoff["candidate"]["content_digest"]})]
    return []                                              # pragma: no cover


def advance_verification(store, seam, *, now):
    """ONE LEVEL-TRIGGERED PASS: materialize, execute, hand off, renew, hold.

    THE PRODUCTION ENTRY POINT OF THIS MODULE, called from `manager.sweep` on
    every tick of every deployment that configures a verification seam, and
    from `manager.reconcile` on every resume. Nothing here is edge-triggered
    on a decision a live process happened to see: every act is derived from
    the records, so an ordinary tick and the first tick after a restart ask
    the same question and get the same answer.

    ONE ACT PER SUCCESSOR PER TICK, deliberately. Materializing and then
    running the command in the same tick would collapse the fault cut between
    them -- the cut the contract names and acceptance injects failures at --
    and the next tick performs the next act from the record the last one left.

    A CONTAINED REFUSAL IS A CONDITION AND NOT A FAULT, exactly as the
    cancellation, control, exchange and analysis passes treat theirs. One
    successor's unreadable candidate must not stop another's review handoff,
    and it must not stop the tick.
    """
    boundaries.instant(now, "a retained verification pass instant")
    taken = check_verification_seam(seam)
    acts = []
    for intent in _reserved_successors(store):
        try:
            acts.extend(_advancing(store, taken, intent, now))
        except ContractRefusal as refusal:
            # THE ACT IT WAS PERFORMING, named from the records rather than
            # from the exception: a refusal reported under the wrong act
            # would tell an operator to look at the wrong boundary. A
            # readiness this pass cannot derive at all is reported under the
            # act that derives nothing, which is `hold`.
            try:
                owed = execution_readiness(store, intent)["owed"]
            except ContractRefusal:                        # pragma: no cover
                owed = None
            acts.append(_act(intent["failure_key"], intent["job_id"],
                             _ACT_OF.get(owed, "hold"), "refused",
                             {"category": refusal.category,
                              "code": refusal.code}))
    return acts


def _reserved_successors(store):
    """Every ADMITTED successor this store holds, oldest identity first.

    THE ADMITTED ONES AND NOT THE RESERVED ONES. A reservation with no Job is
    an incomplete admission that `retained_recovery` resumes; acting on it
    here would be this pass finishing somebody else's operation.
    """
    return _records_of(store, retained_recovery.SUCCESSOR_KIND,
                       retained_recovery.SUCCESSOR_MEMBERS)
