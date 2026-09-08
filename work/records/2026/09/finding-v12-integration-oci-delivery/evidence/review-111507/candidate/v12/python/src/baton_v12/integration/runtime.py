"""THE GENERIC INTEGRATION RUNTIME BOUNDARY: what a fenced integration is
composed from, and what it may not be composed without.

W101490, `work/records/2026/09/finding-v12-standalone-multi-job-pipeline/
findings/finding-serialized-integration/findings/finding-generic-integration-
runtime/`. K owns this boundary: its documents, its schemas and its exports are
one contract, and the leaves that admit candidates, execute one fenced
integration and hold an interrupted one compose it rather than widen it.

THERE IS NO SECOND STATE MACHINE, AND NO SECOND TRANSPORT MECHANISM. The
revalidated tree already owns every mechanism this needs:
`worker_manager/exchange.py` is the durable command/event file exchange whose
lifetime outlives the manager process, `launch.py` delivers one versioned
read-only document, `workspaces.py` and `source_boundary.py` compose mounts,
and `attempts.py` owns the runtime axes. What was missing is the narrow thing
this module is: WHICH integration a runtime performs, WHAT it had to prove
before it could be composed at all, and WHAT its answer means.

THIS MODULE DOES MATERIALIZE ITS OWN TWO NAMESPACES, and the distinction is the
whole of it: every RULE below is `exchange.py`'s -- the same publication, modes,
descriptor proofs and untrusted-read discipline -- while the DELIVERY is a
separate one, for the reason that module gives about being a third. Its two
namespaces carry one attempt's operation sequence and an integration assignment
is not one of those operations; `inputs` is frozen and closed over W19784's
protocol pair; and anything under `workspace` is reachable through the
runtime's own writable mount. See `DELIVERY_DIRECTORY`.

NOTHING HERE NAMES A VERSION CONTROL SYSTEM. Under the owner clarifications of
2026-09-06 core Baton mechanically owns serialized admission, the live fenced
grant, exclusive target write access, quiescence and durable settlement, and it
neither parses nor validates commits, refs, branches, trees, ancestry or
merges. A model that needs Git reads its Work instructions and uses ordinary
Git tools inside the runtime; that traffic never becomes coordinator or
manager schema. `source_profiles/` is the shape this follows -- the generic
contract here, the version-control plan outside it -- and
`TheIntegrationBoundaryIsVCSNeutral` is the gate that keeps it true rather than
a paragraph promising it.

THE FOUR THINGS THIS MODULE DECIDES:

  the PROFILE      one deployment's trusted wiring for one target: which
                   participant integrates it, under which closed profile kind
                   and version, against which instructions digest and result
                   contract. It carries no location and no argv.
  the ASSIGNMENT   the document a composed runtime is launched with, binding
                   the exact target, entry, lease, fence and attempt. It is
                   composed ONLY from a live grant proved at the moment of
                   composition.
  the RESULT       what the runtime claims it did, adopted as untrusted input
                   in the coordinator's own settlement vocabulary -- and a
                   claim is not a settlement, so nothing here settles.
  the HOLD         the account an interruption or an ambiguity produces, whose
                   members are exactly what `block_target` takes. Under the
                   owner ruling of 2026-09-06 this leaf surfaces it and does
                   not act on it: no automatic retry, acceptance, receipt,
                   cleanup, release, discard or reassignment.

WRITABLE ACCESS IS DECIDED HERE AND IS NOT AN OPERAND. It requires the
coordinator's currently live grant AND a positive prior-runtime observation
from the manager's own execution-runtime vocabulary, in which `uncertain` may
never stand for absence. There is no quiet read-only fallback: a runtime that
cannot write the target cannot perform the integration it was launched for, and
launching it to fail would put a container in front of a target for no reason.
"""

import json
import os
import stat

from ..contracts import ContractRefusal, digest, digest_of_bytes
from ..contracts.errors import name_value
from ..worker_manager import attempts, boundaries, workspaces
from .queue import granted_context

__all__ = ["ACCESS_KINDS", "ASSIGNMENT_DIRECTORY", "ASSIGNMENT_DOCUMENT",
           "ASSIGNMENT_MEMBERS", "ASSIGNMENT_SCHEMA", "ASSIGNMENT_TARGET",
           "DELIVERY_DIRECTORY", "HOLD_MEMBERS", "HOLD_REASONS", "HOLD_SCHEMA",
           "IntegrationDelivery", "MAX_DELIVERY_BYTES", "MUTATING_STATES",
           "OBSERVATIONS", "OBSERVED_RUNTIME_MEMBERS", "PROFILE_MEMBERS",
           "PROFILE_SCHEMA", "QUIESCENT_STATES", "RESULT_CONTRACTS",
           "RESULT_DIRECTORY", "RESULT_DOCUMENT", "RESULT_MEMBERS",
           "RESULT_OUTCOMES", "RESULT_SCHEMA", "RESULT_TARGET",
           "adopt_delivery", "assignment_digest", "compose_assignment",
           "hold_account", "integration_profile", "materialize_delivery",
           "observed_delivery", "observed_result", "prior_runtime_witness",
           "publish_assignment", "published_assignment", "target_access"]

PROFILE_SCHEMA = "baton.v12.integration-profile/1"

# WHAT A PROFILE IS AND IS NOT. It is the deployment's trusted wiring for one
# target: who integrates it, under which closed kind and version, against which
# instructions and which result contract. It is NOT a plan, an argv, a mount
# table or a location -- the manager's own components own all four, and a
# profile that carried them would be this boundary deciding another one's
# contract while calling itself generic.
PROFILE_MEMBERS = ("schema", "profile_kind", "profile_version",
                   "integrator_participant", "instructions_digest",
                   "result_contract")

ASSIGNMENT_SCHEMA = "baton.v12.integration-assignment/1"

# EVERY OPERAND A COMPOSED RUNTIME IS LAUNCHED WITH. The grant's four parts are
# here because a runtime that could not name the exact lease and fence it runs
# under could not be refused when that grant ends; the profile's three are here
# because the runtime must be able to prove it is the one the deployment wired;
# and `target_access` is here because what a runtime was GIVEN is part of what
# it was asked to do.
ASSIGNMENT_MEMBERS = ("schema", "canonical_target_id", "entry_id", "lease_id",
                      "fence", "attempt_id", "integrator_participant",
                      "profile_kind", "profile_version", "instructions_digest",
                      "target_access")

# THE ONE ACCESS THIS BOUNDARY COMPOSES, and the tuple is one member because
# inventing the other two would be inventing work nobody asked for. An
# integration runtime that cannot write the target cannot perform the
# integration it was launched for, so there is no read-only fallback to compose
# and no "none" to hand a container: those are refusals, and a refusal says
# what it refused rather than being encoded as an access kind. A later leaf
# that genuinely needs a read-only inspection runtime adds its kind with the
# case that drives it.
ACCESS_KINDS = ("writable",)

RESULT_SCHEMA = "baton.v12.integration-result/1"
RESULT_CONTRACTS = (RESULT_SCHEMA,)

# THE RUNTIME'S CLAIM, IN THE COORDINATOR'S OWN WORDS. The three outcomes are
# `entries.state`'s three terminal ones, deliberately spelled the same: a later
# leaf carrying this claim to `settle_integrated`, `refuse_entry` or
# `block_target` should be choosing a verb, not translating a vocabulary. Two
# vocabularies for one outcome is how an operator stops being able to compare
# what a runtime said with what the queue recorded.
RESULT_OUTCOMES = ("integrated", "refused", "held")
RESULT_MEMBERS = ("schema", "attempt_id", "lease_id", "canonical_target_id",
                  "entry_id", "fence", "outcome", "detail")

HOLD_SCHEMA = "baton.v12.integration-hold/1"

# WHAT AN INTERRUPTION PRODUCES. The members are exactly `block_target`'s
# `reason` and `detail` plus the schema and the observation that produced it,
# so a hold this module composes is a document the coordinator already knows
# how to take. It is composed and returned; it is never applied here.
HOLD_MEMBERS = ("schema", "reason", "observed", "detail")

# The closed reasons this boundary can observe. Each names a state of the
# WORLD rather than a decision: what to do about any of them is an operator's
# under the ruling of 2026-09-06.
HOLD_REASONS = ("runtime-interrupted", "runtime-ambiguous",
                "result-unreadable", "result-foreign")

# WHAT ONE OBSERVATION OF A PRIOR RUNTIME IS, and it is exactly what
# `prior_runtime_witness` returns.
#
# Re-review [P1]: the caller-authored witness this replaced declared three
# members and the manager-derived answer returns two, and the obsolete tuple
# stayed exported -- a public contract advertising a closed document no
# function returns, with an `evidence` member belonging to the superseded
# caller claim. `evidence` was the caller's word for why it believed itself;
# the manager's row needs no such member, because the row IS the evidence.
#
# The vocabulary is the manager's. It owns the execution-runtime axis and its
# transitions, and this reads that table rather than restating it, for the
# reason `schema.check_authority` imports the Authority predicate instead of
# spelling a third "32 lowercase hex".
OBSERVED_RUNTIME_MEMBERS = ("attempt_id", "execution_runtime")

_EXECUTION = attempts.TRANSITIONS["execution_runtime"]

# THE ONLY POSITIVE ANSWERS. `quiescent` is a runtime observed to have stopped
# and `destroyed` is one observed to be gone; both are facts somebody looked at.
# `uncertain` is the state the manager's own table refuses to let become
# `destroyed`, because destruction is a fact about the world and inferring it
# from a failure to look reports a cleaned-up runtime that is still executing
# somebody's code. It is not a quiescence answer here either.
QUIESCENT_STATES = ("quiescent", "destroyed")
MUTATING_STATES = tuple(state for state in _EXECUTION
                        if state not in QUIESCENT_STATES)


def _refuse(message, *, category="integrity", code="schema"):
    raise ContractRefusal(category, code, message)


def _denied(message):
    raise ContractRefusal("policy", "denied", message)


def integration_profile(*, profile_kind, profile_version,
                        integrator_participant, instructions_digest,
                        result_contract=RESULT_SCHEMA):
    """One deployment's trusted wiring for one target, authored here.

    REBUILT OVER `PROFILE_MEMBERS` RATHER THAN COPIED FROM A MAPPING, which is
    `launch_document`'s rule and is here for its reason: a caller supplies
    values, never a document shape, so how a caller happened to build its dict
    cannot reach a document this manager then treats as its own.
    """
    document = {
        "schema": PROFILE_SCHEMA,
        "profile_kind": boundaries.text(profile_kind, "a profile kind"),
        "profile_version": _counted_from_one(profile_version,
                                             "a profile version"),
        "integrator_participant": boundaries.text(
            integrator_participant, "an integrator participant"),
        "instructions_digest": boundaries.text(
            instructions_digest, "a profile's instructions digest"),
        "result_contract": boundaries.text(result_contract,
                                           "a profile's result contract")}
    if document["result_contract"] not in RESULT_CONTRACTS:
        _refuse(f"a profile answers with {name_value(RESULT_SCHEMA)}; this "
                f"names {name_value(document['result_contract'])}")
    return document


def _counted_from_one(value, what):
    boundaries.generation(value, what)
    if value < 1:
        _refuse(f"{what} counts from one; this is {name_value(value)}")
    return value


def _owned_profile(value):
    """One profile, owned wherever it is READ rather than only where it is
    built. The same document with one lock and two doors is the shape
    `boundaries.sealed` records having been caught twice."""
    profile = boundaries.document(value, "an integration profile",
                                  required=PROFILE_MEMBERS)
    if profile["schema"] != PROFILE_SCHEMA:
        _refuse(f"an integration profile is {name_value(PROFILE_SCHEMA)}; "
                f"this is {name_value(profile['schema'])}")
    return integration_profile(
        profile_kind=profile["profile_kind"],
        profile_version=profile["profile_version"],
        integrator_participant=profile["integrator_participant"],
        instructions_digest=profile["instructions_digest"],
        result_contract=profile["result_contract"])


def prior_runtime_witness(manager, attempt_id):
    """The MANAGER'S DURABLE ANSWER about the runtime that held this target.

    W101490's review [P0]: this used to own the shape of a dictionary a CALLER
    handed in. The record was right that agent quiescence is not runtime
    quiescence, and the reviewer was right that moving the same unsupported
    claim into a dictionary does not make it a runtime observation -- a witness
    naming an unrelated attempt as `destroyed` authorized a writer, and omitting
    one authorized a writer unconditionally.

    So there is no witness operand any more. The attempt is the one the
    COORDINATOR says held the previous grant, and its runtime state is read
    from `attempts.attempt_runtime_of`, which is the manager's own durable row
    for exactly that runtime. Nothing a caller can compose reaches this answer.

    ABSENCE OF A RECORD IS NOT ABSENCE OF A RUNTIME. A predecessor the
    coordinator recorded granting, for which the manager holds no attempt at
    all, is a contradiction between two durable stores; it is refused rather
    than read as "nothing was running", which is the permissive branch the
    corrupted absence would otherwise choose.
    """
    boundaries.identity(attempt_id, "a prior attempt id")
    found = attempts.attempt_runtime_of(manager, attempt_id)
    if found is None:
        _denied(f"the coordinator recorded a grant to attempt "
                f"{name_value(attempt_id)} and this manager holds no such "
                f"attempt; absence of a record is not absence of a runtime, "
                f"and a writer does not start behind a runtime nobody can "
                f"account for")
    state = found["execution_runtime"]
    if state not in _EXECUTION:
        _refuse(f"the manager records execution runtime {name_value(state)} "
                f"for attempt {name_value(attempt_id)}, which is not one of "
                f"{', '.join(_EXECUTION)}")
    # AUTHORED OVER THE MEMBER TUPLE, so the exported contract and the answer
    # are one thing rather than two that agree today.
    return {"attempt_id": boundaries.identity(found["attempt_id"],
                                              "a recorded attempt id"),
            "execution_runtime": state}


def target_access(store, manager, *, profile, canonical_target_id, entry_id,
                  lease_id, fence):
    """What access a runtime for this grant may be composed with, RIGHT NOW.

    THREE PROOFS, NONE OF THEM A CALLER'S, and none substituting for another.

    The LIVE GRANT says this caller currently holds the target's one lease at
    exactly this fence over exactly this entry -- read from the coordinator
    rather than presented by its holder, because a lease id with a fence is a
    replayable value.

    The ACCEPTED ENTRY says which profile kind was admitted, and the runtime
    profile the deployment wired must be that one. Review [P0]: this checked
    only the integrator participant, so a lease admitted for one profile kind
    composed a runtime for another. It comes out of the SAME relationship as
    the grant, because a second unsynchronised read would give away the
    one-snapshot property that proof depends on.

    The PREDECESSOR says the runtime that held this target before can no longer
    mutate it, and both halves of that come from durable state: which attempt
    held the previous grant is the coordinator's answer, and what its runtime
    is doing is the manager's. A live grant with a still-running predecessor
    would put two writers in front of one working tree, which is the whole
    thing this campaign's lock exists to prevent.
    """
    taken = _owned_profile(profile)
    boundaries.capability(getattr(manager, "_connection", None),
                          "the worker manager's store")
    context = granted_context(store, lease_id=lease_id,
                              canonical_target_id=canonical_target_id,
                              entry_id=entry_id, fence=fence)
    held, entry = context["lease"], context["entry"]
    if entry["profile_kind"] != taken["profile_kind"]:
        _denied(f"entry {name_value(entry['entry_id'])} was admitted for "
                f"profile kind {name_value(entry['profile_kind'])} and this "
                f"deployment wires {name_value(taken['profile_kind'])}; a "
                f"runtime integrates the candidate that was accepted, under "
                f"the profile it was accepted for")
    if held["integrator_participant"] != taken["integrator_participant"]:
        _denied(f"lease {name_value(held['lease_id'])} was granted to "
                f"{name_value(held['integrator_participant'])} and this "
                f"profile wires {name_value(taken['integrator_participant'])}; "
                f"the participant that holds the grant is the one that runs "
                f"under it")
    prior = None
    if context["predecessor"] is not None:
        prior = prior_runtime_witness(manager,
                                      context["predecessor"]["attempt_id"])
        if prior["execution_runtime"] not in QUIESCENT_STATES:
            _denied(f"the runtime of attempt "
                    f"{name_value(prior['attempt_id'])} is "
                    f"{name_value(prior['execution_runtime'])} and a writer "
                    f"starts only behind one observed "
                    f"{' or '.join(QUIESCENT_STATES)}; an unobserved runtime "
                    f"is not an absent one")
    return {"access": "writable", "lease": held, "entry": entry,
            "prior": prior}


def compose_assignment(store, manager, *, profile, canonical_target_id,
                       entry_id, lease_id, fence, attempt_id):
    """The document one integration runtime is launched with.

    COMPOSED FROM THE PROOF, NOT BESIDE IT. `target_access` runs first and its
    refusal is this function's refusal: there is no path here that reaches a
    document without the live grant having been read from the coordinator in
    the same call.

    THE GRANT'S OWN VALUES ARE USED, not the caller's. The lease the
    coordinator returned is what fills the target, entry, lease and fence
    members, so an assignment cannot name a grant that agrees with the caller
    and not with the store -- the two are the same values only when the proof
    passed, and using the store's is what makes that visible rather than
    assumed.
    """
    boundaries.identity(attempt_id, "an integrator attempt id")
    taken = _owned_profile(profile)
    granted = target_access(store, manager, profile=taken,
                            canonical_target_id=canonical_target_id,
                            entry_id=entry_id, lease_id=lease_id, fence=fence)
    held = granted["lease"]
    # THE ATTEMPT IS THE GRANT'S TOO. Review [P0]: this validated the caller's
    # attempt id and wrote it into the assignment without ever comparing it
    # with the one the lease was granted to, so a live grant for one attempt
    # composed an assignment and a delivery for any other. The acceptance
    # boundary names an exact target, entry, ATTEMPT and fence, and three out
    # of four is a different boundary.
    if held["attempt_id"] != attempt_id:
        _denied(f"lease {name_value(held['lease_id'])} was granted to attempt "
                f"{name_value(held['attempt_id'])} and this caller composes "
                f"{name_value(attempt_id)}; a runtime runs under the grant it "
                f"was given, not beside it")
    document = {
        "schema": ASSIGNMENT_SCHEMA,
        "canonical_target_id": held["canonical_target_id"],
        "entry_id": held["entry_id"],
        "lease_id": held["lease_id"],
        "fence": held["fence"],
        "attempt_id": held["attempt_id"],
        "integrator_participant": taken["integrator_participant"],
        "profile_kind": taken["profile_kind"],
        "profile_version": taken["profile_version"],
        "instructions_digest": taken["instructions_digest"],
        "target_access": granted["access"]}
    return document


def assignment_digest(document):
    """The identity of one composed assignment, for a caller that must bind it.

    The document is re-owned before it is digested, so a digest is never taken
    over something this build has not agreed is an assignment.
    """
    return digest(_owned_assignment(document))


def _owned_assignment(value):
    assignment = boundaries.document(value, "an integration assignment",
                                     required=ASSIGNMENT_MEMBERS)
    if assignment["schema"] != ASSIGNMENT_SCHEMA:
        _refuse(f"an integration assignment is "
                f"{name_value(ASSIGNMENT_SCHEMA)}; this is "
                f"{name_value(assignment['schema'])}")
    for name in ("canonical_target_id", "entry_id", "lease_id", "attempt_id"):
        boundaries.identity(assignment[name], f"an assignment's {name}")
    _counted_from_one(assignment["fence"], "an assignment's fence")
    _counted_from_one(assignment["profile_version"],
                      "an assignment's profile version")
    for name in ("integrator_participant", "profile_kind",
                 "instructions_digest"):
        boundaries.text(assignment[name], f"an assignment's {name}")
    if assignment["target_access"] not in ACCESS_KINDS:
        _refuse(f"an assignment's target access is one of "
                f"{', '.join(ACCESS_KINDS)}; this is "
                f"{name_value(assignment['target_access'])}")
    return assignment


def observed_result(assignment, value):
    """The runtime's claim about what it did, adopted as UNTRUSTED INPUT.

    A CLAIM IS NOT A SETTLEMENT, and this module settles nothing. The runtime
    runs under the same identity that can reach the target, so what it writes
    is bounded, closed-member checked and held to the exact assignment this
    manager composed -- and even then it is what the runtime SAYS. Which
    coordinator verb the claim earns is the fenced-integration leaf's decision,
    made against the live grant at that moment.

    THE OUTCOMES ARE THE COORDINATOR'S THREE, so that decision is a choice of
    verb rather than a translation.
    """
    composed = _owned_assignment(assignment)
    result = boundaries.document(value, "an integration result",
                                 required=RESULT_MEMBERS)
    if result["schema"] != RESULT_SCHEMA:
        _refuse(f"an integration result is {name_value(RESULT_SCHEMA)}; this "
                f"is {name_value(result['schema'])}")
    for name in ("attempt_id", "lease_id", "canonical_target_id", "entry_id"):
        boundaries.identity(result[name], f"a result's {name}")
    _counted_from_one(result["fence"], "a result's fence")
    if result["outcome"] not in RESULT_OUTCOMES:
        _refuse(f"a result's outcome is one of "
                f"{', '.join(RESULT_OUTCOMES)}; this is "
                f"{name_value(result['outcome'])}")
    boundaries.document(result["detail"], "a result's detail")
    for name in ("attempt_id", "lease_id", "canonical_target_id", "entry_id",
                 "fence"):
        if result[name] != composed[name]:
            _denied(f"this result accounts for {name} "
                    f"{name_value(result[name])} and the assignment it answers "
                    f"names {name_value(composed[name])}; a runtime answers "
                    f"the integration it was composed for")
    return result


def hold_account(*, reason, observed, detail):
    """The account an interruption or an ambiguity produces.

    COMPOSED AND RETURNED, NEVER APPLIED. The owner ruling of 2026-09-06 puts
    interrupted or inconsistent integration behind an explicit operator
    decision: restart may observe and classify, and it may not retry, accept,
    complete a receipt, clean up, release, discard output or reassign. So this
    module builds the document `block_target` takes and calls nothing.

    ITS MEMBERS ARE THAT VERB'S. `reason` and `detail` are exactly what a
    blocked target records, so an operator reading the coordinator sees the
    account this boundary composed rather than a summary of it.
    """
    if reason not in HOLD_REASONS:
        _refuse(f"an integration hold is one of {', '.join(HOLD_REASONS)}; "
                f"this is {name_value(reason)}")
    return {"schema": HOLD_SCHEMA, "reason": reason,
            "observed": boundaries.text(observed, "a hold's observation"),
            "detail": boundaries.document(detail, "a hold's detail")}


# -- THE DURABLE DELIVERY ---------------------------------------------------
#
# WHY THIS IS A FOURTH DELIVERY AND NOT A CORNER OF AN EXISTING ONE. It is the
# question `exchange.py` asks of ITSELF as the third -- after `inputs` and
# `workspace` -- and it answers it the same way. Its two namespaces carry ONE
# ATTEMPT'S OPERATION SEQUENCE -- `describe` then `work`
# -- and an integration assignment is not one of those operations; publishing
# it there would either widen another record's closed vocabulary or smuggle a
# document through a member that means something else. `inputs` is frozen
# before the runtime starts and is closed over its own protocol pair, so an
# assignment cannot be added to it without changing W19784's contract.
# Anything under `workspace` is reachable through the runtime's own writable
# mount, so an assignment placed there could be replaced by the very program it
# is addressed to.
#
# WHAT IS REUSED IS THE RULE, NOT THE ROOT. Every mechanism below is
# `exchange.py`'s, deliberately: the same five-step atomic publication, the
# same directory modes and the reasons for them, the same no-follow bounded
# regular-file read, and the same separation between an INTEGRITY refusal --
# this build and its own state disagree -- and an UNTRUSTED one, where the
# least trusted program in the deployment wrote something outside its
# contract.
DELIVERY_DIRECTORY = "integration"
ASSIGNMENT_DIRECTORY = "assignment"
RESULT_DIRECTORY = "result"
ASSIGNMENT_DOCUMENT = "assignment.json"
RESULT_DOCUMENT = "result.json"

# THE FIXED CONTAINER PATHS, constants of the contract at both ends. A path a
# caller could vary is a path a runtime can be pointed at wrongly, so there is
# no locator operand and no caller-selected target.
ASSIGNMENT_TARGET = "/run/baton/integration/assignment"
RESULT_TARGET = "/run/baton/integration/result"

MAX_DELIVERY_BYTES = 65536

# THE ASSIGNMENT DIRECTORY IS MANAGER-WRITABLE AND WORLD-READABLE, and mounted
# READ-ONLY. The container's fixed uid is not this manager's and a bind mount
# carries the host mode through, so `other` must be able to read and traverse
# or the runtime sees an empty directory forever; the read-only mount is what
# actually stops it writing here.
ASSIGNMENT_DIR = 0o755
ASSIGNMENT_FILE = 0o444

# THE DELIVERY ROOT IS THIS MANAGER'S AND NOBODY ELSE'S. Re-review [P1]:
# adoption proved the two leaf namespaces and never opened their parent, and
# `O_NOFOLLOW` binds only the FINAL component of a path -- so an `integration`
# symlink in the middle was followed, and an arbitrary correctly shaped tree
# behind it was reported as this manager's own delivery. The root is created at
# an exact mode, proved at that mode, and the children are opened relative to
# ITS descriptor rather than by absolute path.
DELIVERY_DIR = 0o700


def _untrusted(message):
    """A runtime-written document this manager will not adopt.

    A SEPARATE CATEGORY from an integrity refusal, for `exchange.py`'s reason:
    `integrity` means this build and its own durable state disagree, and this
    means the least trusted program in the deployment wrote something outside
    its contract. Neither is success and only one is a bug here.
    """
    raise ContractRefusal("refused", "precondition", message)


class IntegrationDelivery:
    """The TYPED capability a caller receives, and the only one.

    Paths are not operands anywhere in this contract: a caller holding two
    strings could point a runtime at a namespace this manager did not make,
    which is exactly what the fixed targets exist to take away.
    """

    __slots__ = ("attempt_id", "root")

    def __init__(self, *, attempt_id, root):
        self.attempt_id = boundaries.identity(attempt_id,
                                              "an integrator attempt id")
        self.root = os.path.join(boundaries.text(root, "a delivery root"),
                                 DELIVERY_DIRECTORY)

    @property
    def assignment_root(self):
        return os.path.join(self.root, ASSIGNMENT_DIRECTORY)

    @property
    def result_root(self):
        return os.path.join(self.root, RESULT_DIRECTORY)


def _group(workspace_group):
    """The configured group, taken only from this manager's own frozen answer.

    `workspaces.configured_workspace_group` is the one thing that mints a
    `WorkspaceGroup`, so a caller holding one means the deployment configured
    it. An integer here would be validating whatever the caller chose.
    """
    if type(workspace_group) is not workspaces.WorkspaceGroup:
        _denied(f"an integration result namespace is created in the "
                f"deployment's configured workspace group, obtained from this "
                f"manager's own record; this is "
                f"{name_value(workspace_group)}")
    return workspace_group.gid


def materialize_delivery(root, *, attempt_id, workspace_group):
    """Create this integration's two namespaces under an existing root.

    BEFORE THE RUNTIME STARTS AND NEVER AFTER: the mounts are fixed when the
    container is created, so a namespace that did not exist then is one nothing
    will ever hold. What happens afterwards is PUBLICATION, which writes into a
    directory that already exists and is already mounted.
    """
    delivery = IntegrationDelivery(attempt_id=attempt_id, root=root)
    os.makedirs(delivery.root, mode=0o700, exist_ok=False)
    # ESTABLISHED RATHER THAN REQUESTED. `makedirs` asks for a mode and the
    # process umask decides what it gets, so the mode adoption later proves has
    # to be set rather than hoped for -- the same reason `_publish_once` sets a
    # file's mode on its descriptor.
    os.chmod(delivery.root, DELIVERY_DIR)
    os.makedirs(delivery.assignment_root, mode=0o700, exist_ok=False)
    os.chmod(delivery.assignment_root, ASSIGNMENT_DIR)
    os.makedirs(delivery.result_root, mode=0o700, exist_ok=False)
    workspaces.adopt_workspace_group(
        {"workspace": delivery.result_root},
        workspaces.check_workspace_group(_group(workspace_group)))
    return delivery


def _own_directory(place, mode, what, *, within=None):
    """One directory this manager established, proved on its own descriptor.

    W101490's first review [P1]: adoption used `os.path.isdir`, which follows
    links and proves neither type nor mode. The re-review found the other half:
    `O_NOFOLLOW` binds only the FINAL component of a path, so opening
    `<root>/integration/assignment` no-follow says nothing about `integration`
    -- a symlink there was followed and the tree behind it adopted.

    So `within` exists and is not optional in spirit: the parent is proved
    first, and every child is opened RELATIVE TO ITS DESCRIPTOR. That is the
    same rule as before applied to every component rather than to the last one,
    and it is why the descriptor rather than the path is what gets passed
    around: checking with `isdir`, mode-checking with `lstat` and then opening
    by name is three lookups of a path that can change between them.
    """
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY
    try:
        opened = (os.open(place, flags) if within is None
                  else os.open(place, flags, dir_fd=within))
    except OSError as failure:
        _denied(f"{what} is not a directory this manager made "
                f"({type(failure).__name__}); an entry of another type is "
                f"state this build cannot account for")
    held = os.stat(opened)
    if stat.S_IMODE(held.st_mode) != mode:
        os.close(opened)
        _denied(f"{what} is mode {oct(stat.S_IMODE(held.st_mode))} and this "
                f"manager established {oct(mode)}; a delivery whose modes have "
                f"moved is not the one it wrote")
    return opened


def adopt_delivery(root, *, attempt_id, workspace_group):
    """Recover the delivery this manager already made, or FAIL CLOSED.

    ABSENT ADOPTS NOTHING, and that is an ordinary answer for an integration
    whose delivery was never made. What is not ordinary is a root that exists
    and cannot be proved: this manager's own delivery root and the two
    namespaces INSIDE IT, each at its exact established mode, with the
    runtime-written one in the group the deployment configured.

    THE GROUP IS PROVED, and it needs the trusted input for the same reason
    `materialize_delivery` does: a namespace the runtime's container does not
    share is one it cannot answer in, and a gid a caller could choose is a
    group a caller chose.
    """
    delivery = IntegrationDelivery(attempt_id=attempt_id, root=root)
    if not os.path.lexists(delivery.root):
        return None
    # THE PARENT FIRST, and everything else through its descriptor.
    parent = _own_directory(delivery.root, DELIVERY_DIR,
                            f"attempt {name_value(delivery.attempt_id)}'s "
                            f"integration delivery root")
    try:
        os.close(_own_directory(
            ASSIGNMENT_DIRECTORY, ASSIGNMENT_DIR,
            f"attempt {name_value(delivery.attempt_id)}'s integration "
            f"assignment namespace", within=parent))
        opened = _own_directory(
            RESULT_DIRECTORY, workspaces.WORKSPACE_DIR,
            f"attempt {name_value(delivery.attempt_id)}'s integration result "
            f"namespace", within=parent)
        try:
            held = os.stat(opened)
            gid = workspaces.check_workspace_group(_group(workspace_group))
            if held.st_gid != gid:
                _denied(f"attempt {name_value(delivery.attempt_id)}'s "
                        f"integration result namespace is in group "
                        f"{held.st_gid} and this deployment configured {gid}; "
                        f"a namespace the runtime's container does not share "
                        f"is one it cannot answer in")
        finally:
            os.close(opened)
    finally:
        os.close(parent)
    return delivery


def _payload(document):
    payload = json.dumps(document, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
    if len(payload) > MAX_DELIVERY_BYTES:
        _denied(f"this integration assignment is {len(payload)} bytes and the "
                f"runtime reads at most {MAX_DELIVERY_BYTES}; a document the "
                f"runtime would refuse is not one this manager writes")
    return payload


def publish_assignment(delivery, assignment):
    """Publish the one assignment ATOMICALLY, or replay the identical one.

    PUBLICATION IS `_publish_once`, and its steps are `publish_command`'s
    current ones rather than a paraphrase: a UNIQUE no-follow staging name so a
    process that died mid-publication wedges nothing; the complete bounded
    canonical write, every byte of it; the mode established on the DESCRIPTOR
    rather than requested through a umask; `fsync` on the file; NO-CLOBBER
    `link` into the fixed name, which fails closed on a racing winner instead
    of replacing it; `fsync` on the directory; and removal of the staging name
    whichever way it ended. A runtime that read this namespace mid-publication
    sees a staging name, which is not the fixed name and is therefore not an
    assignment.

    A DIFFERENT DOCUMENT UNDER THE SAME NAME REFUSES. One attempt integrates
    one thing; two byte strings claiming that means this build and whatever
    wrote the other one disagree about what was assigned, and replacing it
    would move an identity a running runtime may already have copied.
    """
    if type(delivery) is not IntegrationDelivery:
        _denied(f"an assignment is published through this component's own "
                f"typed delivery; this is {name_value(delivery)}")
    document = _owned_assignment(assignment)
    if document["attempt_id"] != delivery.attempt_id:
        _denied(f"this assignment names attempt "
                f"{name_value(document['attempt_id'])} and the delivery "
                f"belongs to {name_value(delivery.attempt_id)}; one delivery "
                f"carries one integration")
    payload = _payload(document)
    place = os.path.join(delivery.assignment_root, ASSIGNMENT_DOCUMENT)
    existing = _read_bounded(delivery.assignment_root, ASSIGNMENT_DOCUMENT,
                             what="the published assignment")
    if existing is not None:
        if existing != payload:
            _denied(f"attempt {name_value(delivery.attempt_id)} already "
                    f"carries a different assignment; one integration is "
                    f"assigned once, and replacing it would move an identity "
                    f"a running runtime may already have copied")
        return {"published": False, "place": place,
                "assignment_digest": digest_of_bytes(payload)}
    published = _publish_once(delivery.assignment_root, ASSIGNMENT_DOCUMENT,
                              payload)
    if not published:
        # LOST THE RACE TO THE FINAL NAME, which is an ordinary outcome rather
        # than a failure: the linking publication never clobbers, so the
        # winner's document is still there to be compared. An identical one is
        # adopted; a different one refuses exactly as one found before staging
        # does.
        existing = _read_bounded(delivery.assignment_root,
                                 ASSIGNMENT_DOCUMENT,
                                 what="the published assignment")
        if existing != payload:
            _denied(f"attempt {name_value(delivery.attempt_id)} already "
                    f"carries a different assignment; one integration is "
                    f"assigned once, and replacing it would move an identity "
                    f"a running runtime may already have copied")
    return {"published": published, "place": place,
            "assignment_digest": digest_of_bytes(payload)}


def _publish_once(root, name, payload):
    """Stage, sync, and LINK into the final name. Answers whether we made it.

    W101490's review [P1]: the first draft of this copied a SUPERSEDED
    publication shape -- one fixed staging name, one unchecked `os.write`,
    umask-dependent creation and `os.rename` -- and the record claimed it was
    `exchange.py`'s current mechanism. It was that module's OLD one, and every
    invariant W81857's own review added to fix it was missing. Reproduced: a
    stale staging file wedged publication forever, a short write published a
    truncated document as successful, a restrictive umask produced a mode-000
    file under a declared 0444 contract, and `rename` could replace a
    concurrent winner.

    So all of them are here, for their reasons rather than by imitation:

    THE STAGING NAME IS UNIQUE per attempt at publishing. A fixed name plus
    `O_EXCL` means a process that died between creation and publication leaves
    a file that fails every later incarnation forever -- a permanent wedge
    created by a crash, on the one path a durable transport exists to survive.

    EVERY BYTE IS WRITTEN. `os.write` may write fewer and does not report that
    as an error, and a truncated assignment is one the runtime refuses while
    this manager believes it delivered a whole one.

    THE MODE IS SET ON THE DESCRIPTOR. Creation mode is masked by whatever
    umask the process happens to hold, so the declared contract has to be
    established rather than requested.

    THE FINAL NAME IS TAKEN WITH `link`, NOT `rename`. `rename` silently
    replaces whatever is at the destination; `link` is equally atomic and fails
    closed on an existing name, which turns a race into a comparison.

    THE STAGING FILE ALWAYS GOES, whichever way this ends, and removing it
    removes a NAME rather than the document: `link` made a second name for the
    same inode.
    """
    staged = os.path.join(root, f".{name}.{os.getpid()}."
                                f"{os.urandom(8).hex()}.publishing")
    handle = os.open(staged,
                     os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                     0o000)
    try:
        try:
            _write_whole(handle, payload)
            os.fchmod(handle, ASSIGNMENT_FILE)
            os.fsync(handle)
        finally:
            os.close(handle)
        try:
            os.link(staged, os.path.join(root, name))
        except FileExistsError:
            return False
        opened = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(opened)
        finally:
            os.close(opened)
        return True
    finally:
        try:
            os.unlink(staged)
        except OSError:
            pass


def _write_whole(handle, payload):
    """Every byte, or a refusal. `os.write` is allowed to write fewer."""
    written = 0
    while written < len(payload):
        step = os.write(handle, payload[written:])
        if type(step) is not int or step <= 0:
            _refuse(f"writing the integration assignment made no progress "
                    f"after {written} of {len(payload)} bytes; a partly "
                    f"written assignment is one the runtime refuses and this "
                    f"manager believes it delivered")
        written += step
    return written


def _read_bounded(place, name, *, what):
    """One named regular file's whole bytes, or absence -- NO-FOLLOW, BOUNDED.

    The four properties are `exchange._read_exact`'s and each one is a way a
    container can hand this manager something other than a document: NO-FOLLOW
    so a link at a fixed name is refused rather than resolved, NON-BLOCKING so
    a FIFO cannot stop this manager inside `open`, REGULAR proved on the
    DESCRIPTOR rather than on the path, and BOUNDED at one byte past the
    ceiling.
    """
    try:
        opened = os.open(place, os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY)
    except OSError:
        return None
    try:
        try:
            handle = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                             dir_fd=opened)
        except FileNotFoundError:
            return None
        except OSError as failure:
            _untrusted(f"{what} at {name_value(name)} could not be opened as "
                       f"an ordinary file ({type(failure).__name__}); a link "
                       f"or a device at a name this contract fixes is not a "
                       f"document")
    finally:
        os.close(opened)
    try:
        found = os.fstat(handle)
        if not stat.S_ISREG(found.st_mode):
            _untrusted(f"{what} at {name_value(name)} is not a regular file")
        raw = os.read(handle, MAX_DELIVERY_BYTES + 1)
    finally:
        os.close(handle)
    if len(raw) > MAX_DELIVERY_BYTES:
        _untrusted(f"{what} at {name_value(name)} is wider than "
                   f"{MAX_DELIVERY_BYTES} bytes; a reader with no bound is "
                   f"bounded by whoever writes the file")
    return raw


def published_assignment(delivery):
    """The assignment a delivery CURRENTLY CARRIES, or `None` if none is there.

    W110934. `observed_delivery` compares the published bytes against an
    assignment the caller already holds and answers a STATE; nothing answered
    the document. A consumer that must bind a mount plan to the exact assignment
    the runtime will read needs the document itself, and deriving it from a
    private helper would be reaching around this module's own boundary.

    OWNED BEFORE IT IS ANSWERED. What is on disk is bytes the manager wrote,
    but this reader is the one a restarted incarnation uses, so the document
    goes through `_owned_assignment` exactly as a freshly composed one does --
    a reader that answered whatever decoded would let a corrupted or
    hand-edited file become a mount plan's idea of the assignment.

    IT PROVES NOTHING ABOUT A GRANT. An assignment stays readable after the
    lease that authorized it has ended, which is precisely why `target_access`
    is a separate call and why this one cannot stand in for it. What this
    answers is identity, not authority.
    """
    if type(delivery) is not IntegrationDelivery:
        _denied(f"a published assignment is read through this component's own "
                f"typed delivery; this is {name_value(delivery)}")
    raw = _read_bounded(delivery.assignment_root, ASSIGNMENT_DOCUMENT,
                        what="the published assignment")
    if raw is None:
        return None
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as failure:
        _untrusted(f"the published assignment does not decode "
                   f"({type(failure).__name__}); a document this manager "
                   f"cannot read is not one it will bind a mount plan to")
    return _owned_assignment(document)


# What this boundary can say about a delivery it has read. `waiting` is a real
# answer and is deliberately not rounded to a hold: an integration with no
# result yet may still be running, and only positive evidence about the runtime
# turns that into anything else -- which is the prior-runtime witness's job and
# not this reader's.
OBSERVATIONS = ("not-assigned", "waiting", "answered", "held")


def observed_delivery(delivery, assignment):
    """This integration's whole state, from the durable files and nothing else.

    THE FULL READ IS AUTHORITATIVE AND THERE IS NO CURSOR. A follower may
    reduce latency and losing one costs latency and nothing else, because this
    reconstructs the same answer from the same files every time.

    A REFUSAL FROM RUNTIME MATERIAL IS AN OBSERVATION, NOT AN EXCEPTION, and it
    arrives as a HOLD. `exchange.observation` reports unreadable worker
    material rather than raising, because a manager that raised would let the
    least trusted program in the deployment stop the sweep for every other
    stage; here the same material also means an integration nobody may settle,
    so the observation IS the account `block_target` takes. Composing it is all
    this does -- under the owner ruling of 2026-09-06 what happens next is an
    operator's.
    """
    if type(delivery) is not IntegrationDelivery:
        _denied(f"an integration is observed through this component's own "
                f"typed delivery; this is {name_value(delivery)}")
    composed = _owned_assignment(assignment)
    published = _read_bounded(delivery.assignment_root, ASSIGNMENT_DOCUMENT,
                              what="the published assignment")
    if published is None:
        return {"state": "not-assigned", "result": None, "hold": None}
    if published != _payload(composed):
        return {"state": "held", "result": None,
                "hold": hold_account(
                    reason="result-foreign",
                    observed="the published assignment is not the one this "
                             "observation was made against",
                    detail={"attempt_id": delivery.attempt_id})}
    try:
        raw = _read_bounded(delivery.result_root, RESULT_DOCUMENT,
                            what="the integration result")
    except ContractRefusal as refusal:
        return {"state": "held", "result": None,
                "hold": hold_account(
                    reason="result-unreadable", observed=refusal.message,
                    detail={"attempt_id": delivery.attempt_id})}
    if raw is None:
        return {"state": "waiting", "result": None, "hold": None}
    try:
        result = observed_result(composed, json.loads(raw.decode("utf-8")))
    except (UnicodeDecodeError, ValueError) as failure:
        return {"state": "held", "result": None,
                "hold": hold_account(
                    reason="result-unreadable",
                    observed=f"the integration result does not decode "
                             f"({type(failure).__name__})",
                    detail={"attempt_id": delivery.attempt_id})}
    except ContractRefusal as refusal:
        return {"state": "held", "result": None,
                "hold": hold_account(
                    reason="result-foreign", observed=refusal.message,
                    detail={"attempt_id": delivery.attempt_id})}
    return {"state": "answered", "result": result, "hold": None}
