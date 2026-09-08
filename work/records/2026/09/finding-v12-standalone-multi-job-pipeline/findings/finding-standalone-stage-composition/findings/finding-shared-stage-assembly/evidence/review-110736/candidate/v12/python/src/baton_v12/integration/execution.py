"""ONE FENCED INTEGRATION, END TO END: grant, compose, deliver, run, settle.

W101492, `work/records/2026/09/finding-v12-standalone-multi-job-pipeline/
findings/finding-serialized-integration/findings/finding-fenced-model-
integration/`. K owns this assembly, and it is an ASSEMBLY: every proof it
depends on already exists in the two leaves it composes, and what it adds is
the decision each of them deliberately refused to make.

WHAT THE PIECES ALREADY DO, so this module does not do it again. `admission`
proves every member of a candidate account from its accepted producer before
the entry has a rank. `queue.grant_lease` decides the race in the store, takes
the target's smallest queued rank and burns one fence.
`runtime.compose_assignment` reads the live grant, the accepted entry and the
grant it follows out of ONE relationship pass, and refuses an attempt or a
profile kind that is not the grant's, or a predecessor the manager has not
observed stopped. `runtime.observed_delivery` reads what the model wrote as
untrusted input.

WHAT IS THIS MODULE'S, AND IT IS ONE THING: WHICH COORDINATOR VERB A CLAIM
EARNS. The runtime boundary adopts a claim in the coordinator's own three
terminal words and settles nothing, because choosing between
`settle_integrated`, `refuse_entry` and `block_target` is a decision about the
world and belongs where the whole attempt is visible. That is here.

THE MODEL IS AN INJECTED CAPABILITY AND NEVER AN ARGV. A deployment supplies
the port; this composes a proved assignment, publishes it into the durable
delivery, asks the port to run, and reads the files back. It never learns what
the model ran. For Baton's repository the model uses ordinary Git tools under
its Work instructions, and no byte of that reaches this module -- there is no
VCS adapter here and v12 requires none.

THE ACCOUNT IS RE-RESOLVED BEFORE THE MODEL IS ASKED, and the review of
2026-09-06 is why. Admission is valid when an entry receives its rank and can
be STALE by the time that entry reaches the head of the queue: Authority may
advance the canonical target, or the accepted evidence may cease to agree. So
`resolved_account` -- admission's own resolution, not a second reading of the
same sources -- runs again under the live grant, and every member of its answer
must equal the member the entry was admitted with. Nothing is rebuilt from a
caller value: the selectors come out of the stored entry.

THE ATTEMPT MUST NOT HAVE STARTED YET, which is narrower than "not already
finished" and is the second review's correction. `not-started` is the ONE state
in which this assembly asks a port to run: every other state either has a
runtime that may already be writing (`start-requested`, `running`), one that is
being taken down (`cancel-requested`, `stopping`), one nobody can account for
(`uncertain`), or one already over (`quiescent`, `destroyed`). Refusing all
seven is what makes the interval between this check and the quiescent
observation afterwards the interval the writer actually ran in -- and it is why
the namespaces are materialized BEFORE that runtime starts, which is
`materialize_delivery`'s own contract.

TWO GRANT CUTPOINTS, AND THEY ANSWER DIFFERENT RACES. The grant is re-read
immediately before the port receives writable work, because producer
revalidation is a cross-store proof that takes time and a grant can end inside
it -- the second review reproduced exactly that, with the target mutated after
the lease had been abandoned. And it is re-read again before settling, because
a grant can also end while the model runs. Neither check substitutes for the
other.

WHAT THIS DOES NOT DO. It stages and commits nothing -- Slawomir keeps Git
index and history ownership. It makes no policy decision, repairs no candidate,
and RECOVERS NOTHING: under the owner ruling of 2026-09-06 an interruption or
an ambiguity is surfaced for an operator, so an unanswered attempt is reported
and left exactly where it was. W101493 owns what happens next.
"""

from ..contracts import ContractRefusal
from ..contracts.errors import name_value
from ..worker_manager import boundaries
from . import runtime
from .admission import resolved_account
from .queue import (_settlement, block_target, grant_lease, live_grant,
                    refuse_entry, release_lease, settle_integrated)

__all__ = ["INTEGRATION_PORT", "OUTCOMES", "complete_integrated",
           "integrate_next", "settle_observed"]

# WHAT A DEPLOYMENT'S RUNTIME PORT MUST CARRY, and it is one verb. `run` is
# handed the typed delivery and the proved assignment and answers when the
# model has been asked -- not when it has finished, which is what the durable
# files say. A second verb here would be this module deciding a lifecycle the
# Worker Manager already owns.
#
# ONE RATHER THAN FOUR, which is the difference from `AGENT_ADAPTER`: that
# contract needs `cancel`, `observe_session`, `probe` and `inquire` because the
# manager BRANCHES on those answers. This module branches on the delivery and
# on the manager's own runtime axis, so a port that could answer more would be
# a port whose answers nothing reads.
INTEGRATION_PORT = ("run",)

# WHAT ONE ATTEMPT CAN END AS, from this module's point of view. The first
# three are the coordinator's own settlements, reached because the model
# claimed them; `running` is an attempt that has not answered yet and is
# deliberately not one of the others.
OUTCOMES = ("integrated", "refused", "held", "running")


def _refuse(message, *, category="integrity", code="schema"):
    raise ContractRefusal(category, code, message)


def _denied(message):
    raise ContractRefusal("policy", "denied", message)


def _port(value):
    """The deployment's runtime port, typed before it is trusted."""
    for verb in INTEGRATION_PORT:
        boundaries.capability(getattr(value, verb, None),
                              f"the integration runtime port's {verb}")
    return value


def _settled(result):
    """The model's `detail`, owned as the settlement its outcome requires.

    THE ONE PLACE THE TWO VOCABULARIES MEET. `runtime.observed_result` adopts a
    closed result whose `detail` is a document and deliberately says no more --
    that boundary's own commentary records that what a verification must
    CONTAIN belongs to the leaf that performs the import, which is this one. So
    the mapping is here: an `integrated` detail is the coordinator's integrated
    settlement (`imported_paths` and `verification`), and a `refused` or `held`
    one is its refusal shape (`reason` and `detail`).

    `queue._settlement` IS THE OWNER, not a second spelling of it. A settlement
    validated here against a copy of the coordinator's rules would be the
    "member set is not a shape" defect this record has caught three times; the
    coordinator's own function is what admits it, so what this module proves is
    exactly what the store will accept.

    ANSWERS `None` RATHER THAN RAISING, because the caller turns that into a
    hold: a model whose answer this coordinator cannot record is runtime
    material outside its contract, and the least trusted program in the
    deployment must not be able to raise out of a sweep.
    """
    try:
        return _settlement(result["detail"], result["outcome"],
                           "an integration result's settlement")
    except ContractRefusal:
        return None


# THE ONE STATE A PORT IS ASKED IN. Second review [P0]: refusing only the two
# terminal states left five others through, and none of them says no runtime is
# writing -- `start-requested` and `running` have one, `cancel-requested` and
# `stopping` are taking one down, and `uncertain` is the state the manager's own
# table refuses to let become `destroyed` because nobody looked successfully.
UNSTARTED = "not-started"


def _unstarted(manager, attempt_id):
    """This attempt's runtime does not exist yet.

    THE INTERVAL IS WHAT IS BEING PROVED. A quiescent observation after the
    model ran means "the writer stopped" only if there was no writer before it
    started; otherwise it is a statement about somebody else's runtime wearing
    this attempt's identity. `not-started` is the only state that says so, and
    it is also what makes `materialize_delivery`'s contract hold -- the fixed
    namespaces are created before the runtime that will mount them.
    """
    observed = runtime.prior_runtime_witness(manager, attempt_id)
    if observed["execution_runtime"] != UNSTARTED:
        _denied(f"the runtime of attempt {name_value(attempt_id)} is "
                f"{name_value(observed['execution_runtime'])} and a port is "
                f"asked to run only for an attempt whose runtime is "
                f"{name_value(UNSTARTED)}; every other state either has a "
                f"writer, is taking one down, or cannot account for one")
    return observed


def _current(store, manager, jobs, authority, entry):
    """The entry's account, RE-RESOLVED now, and equal to what was admitted.

    THE SELECTORS ARE THE ENTRY'S. `line_id` and `proposal_id` come out of the
    stored account rather than from a caller, so this cannot be pointed at a
    different candidate; and what comes back is compared member for member
    against the account the coordinator holds.

    A DIFFERENCE IS STALENESS, NOT CORRUPTION, AND STALENESS HAS A VERB.
    Admission proved this account when the entry was enqueued; Authority may
    have advanced its canonical target since, or an accepted producer may no
    longer agree. The targeted review of 2026-09-05 already ruled what that
    is: an ordinary policy, scope or target failure found BEFORE any mutation
    terminally refuses THAT immutable entry and the queue moves on. Second
    review [P1]: raising here instead left the entry `leased` behind a live
    lease, turning an ordinary stale candidate into manual recovery and
    stopping rank two -- fail-closed, and contradicting the recorded
    disposition.

    So this ANSWERS rather than raises, and the caller applies the verb. An
    integrity refusal is the other branch and keeps its statement about the
    target.
    """
    admitted = entry["eligibility"]
    try:
        now = resolved_account(manager, jobs, authority,
                               line_id=admitted["line_id"],
                               proposal_id=admitted["proposal_id"])
    except ContractRefusal as refused:
        return (None, refused)
    for name in sorted(admitted):
        if now.get(name) != admitted[name]:
            return (None, ContractRefusal(
                "refused", "precondition",
                f"entry {name_value(entry['entry_id'])} was admitted with "
                f"{name} {name_value(admitted[name])} and its accepted "
                f"producers now say {name_value(now.get(name))}; a candidate "
                f"whose evidence moved while it waited is not integrated on "
                f"the strength of what was true then"))
    return (now, None)


def _stale(store, entry_id, canonical_target_id, lease_id, fence, refused):
    """Give an execution-time preflight failure the verb the record ruled.

    THE CATEGORY IS THE SPLIT, and it is the coordinator's own. A `refused` or
    `policy` account says this CANDIDATE is not integrable now -- ordinary, so
    the entry is refused and its lease released in the one transaction that
    does both, and the queue moves on. An `integrity` account says something
    about the persisted evidence nobody can reconcile, which is a statement
    about the TARGET: it blocks and keeps the lease for the explicit recovery.
    """
    account = {"reason": refused.code,
               "detail": {"category": refused.category,
                          "observed": refused.message}}
    if refused.category == "integrity":
        block_target(store, canonical_target_id=canonical_target_id,
                     entry_id=entry_id, lease_id=lease_id, fence=fence,
                     reason=account["reason"], detail=account["detail"])
        return "held"
    refuse_entry(store, canonical_target_id=canonical_target_id,
                 entry_id=entry_id, settlement=account, lease_id=lease_id,
                 fence=fence)
    return "refused"


def _quiescent(manager, attempt_id):
    """The model that wrote this claim can no longer write the target.

    NOT THE MODEL'S WORD FOR IT. A terminal document in the delivery is the
    runtime's claim that it finished; whether the runtime is GONE is the
    manager's durable row, and settling behind a runtime that is still up would
    record a result about a tree that is still moving. This is the same reader
    `runtime.target_access` uses for a predecessor, for the same reason:
    `uncertain` may never stand for absence.
    """
    observed = runtime.prior_runtime_witness(manager, attempt_id)
    if observed["execution_runtime"] not in runtime.QUIESCENT_STATES:
        _denied(f"the runtime of attempt {name_value(attempt_id)} is "
                f"{name_value(observed['execution_runtime'])} and a settlement "
                f"is recorded only behind one observed "
                f"{' or '.join(runtime.QUIESCENT_STATES)}; a model that can "
                f"still write the target has not finished writing it")
    return observed


def integrate_next(store, manager, jobs, authority, port, *,
                   canonical_target_id, entry_id, profile, lease_id, attempt_id,
                   launch_root, workspace_group):
    """Take this target's next entry through one fenced integration.

    THE ORDER IS THE CONTRACT and every step of it is somebody's proof:

      1. `grant_lease` takes the target's SMALLEST QUEUED RANK and burns one
         fence, deciding any race inside the store. An empty queue answers
         `None` and this returns without composing anything.
      2. `compose_assignment` proves the grant live, the entry's accepted
         profile kind equal to the deployment's, and the previous runtime
         observed stopped. Its refusal is this function's refusal, and nothing
         has been delivered or started at that point.
      3. The delivery is materialized and the assignment published atomically.
      4. The port is asked to run. What the model then does is its Work
         instructions', and this module neither supplies nor reads them.
      5. The durable files are read back as untrusted input.
      6. A claim is settled only behind the live grant re-read AND the runtime
         observed quiescent.

    IT ANSWERS, IT DOES NOT WAIT. An attempt with no result yet is `running`,
    reported with its grant intact. Under the owner ruling of 2026-09-06 this
    leaf recovers nothing: no retry, no acceptance, no cleanup, no release.
    """
    boundaries.capability(getattr(store, "_connection", None),
                          "the integration coordinator store")
    boundaries.capability(getattr(manager, "_connection", None),
                          "the Worker Manager store")
    boundaries.capability(getattr(jobs, "_connection", None),
                          "the Job store")
    _port(port)
    boundaries.identity(canonical_target_id, "a canonical target id")
    boundaries.identity(entry_id, "an entry id")
    boundaries.identity(lease_id, "a lease id")
    boundaries.identity(attempt_id, "an integrator attempt id")
    taken = runtime._owned_profile(profile)

    granted = grant_lease(
        store, canonical_target_id=canonical_target_id, entry_id=entry_id,
        lease_id=lease_id,
        integrator_participant=taken["integrator_participant"],
        attempt_id=attempt_id)
    if granted is None:
        # THE TYPED EMPTY GRANT. Nothing was queued, so nothing was leased and
        # no fence was burned; there is no attempt to report on.
        return {"outcome": None, "entry": None, "assignment": None,
                "observed": None}

    fence = granted["lease"]["fence"]
    assignment = runtime.compose_assignment(
        store, manager, profile=taken,
        canonical_target_id=canonical_target_id, entry_id=entry_id,
        lease_id=lease_id, fence=fence, attempt_id=attempt_id)

    # RE-RESOLVED UNDER THE GRANT, BEFORE ANYTHING IS DELIVERED OR ASKED. A
    # candidate whose accepted evidence moved while it waited is settled with
    # the verb the record ruled -- ordinarily refused so the queue moves on --
    # with no delivery made, no model invoked and no target byte reachable.
    account, refused = _current(store, manager, jobs, authority,
                                granted["entry"])
    if refused is not None:
        outcome = _stale(store, entry_id, canonical_target_id, lease_id, fence,
                         refused)
        return {"outcome": outcome, "entry": entry_id, "assignment": None,
                "observed": {"state": "not-assigned", "result": None,
                             "hold": None, "refused": str(refused)}}
    _unstarted(manager, attempt_id)

    # THE NAMESPACES EXIST BEFORE THE RUNTIME DOES, which is
    # `materialize_delivery`'s own contract: a mount that did not exist when
    # the container was created is one nothing will ever hold.
    delivery = runtime.materialize_delivery(
        launch_root, attempt_id=attempt_id, workspace_group=workspace_group)
    runtime.publish_assignment(delivery, assignment)

    # THE PRE-MUTATION CUTPOINT. Producer revalidation is a cross-store proof
    # and a grant can end inside it, so the grant is proved live again HERE,
    # immediately before the port receives writable work. The post-run check
    # answers a different race and neither replaces the other.
    live_grant(store, lease_id=lease_id,
               canonical_target_id=canonical_target_id, entry_id=entry_id,
               fence=fence)
    port.run(delivery, assignment)
    return settle_observed(store, manager, delivery, assignment)


def settle_observed(store, manager, delivery, assignment):
    """Read what the attempt left behind and give it the verb it earned.

    SEPARATE FROM THE START, because a restart has to be able to reach it
    without starting anything: the delivery is on disk, the grant is in the
    coordinator, and neither needs the process that made them. `adopt_delivery`
    is how a later incarnation gets the typed delivery back.
    """
    composed = runtime._owned_assignment(assignment)
    seen = runtime.observed_delivery(delivery, composed)
    entry_id = composed["entry_id"]
    canonical_target_id = composed["canonical_target_id"]
    lease_id, fence = composed["lease_id"], composed["fence"]

    if seen["state"] in ("not-assigned", "waiting"):
        # NOT AN ENDING. The attempt may still be running, and only positive
        # evidence about the runtime could say otherwise -- which is the
        # operator's business under the manual-recovery ruling, not this
        # module's.
        return {"outcome": "running", "entry": entry_id,
                "assignment": composed, "observed": seen}

    if seen["state"] == "held":
        # UNREADABLE OR FOREIGN RUNTIME MATERIAL. The target may hold base
        # bytes, candidate bytes or a mixture, and offering the next entry into
        # that is the hidden correction this record forbids -- so the target is
        # blocked with the account the runtime boundary composed, and the entry
        # keeps its lease for the explicit recovery.
        held = seen["hold"]
        block_target(store, canonical_target_id=canonical_target_id,
                     entry_id=entry_id, lease_id=lease_id, fence=fence,
                     reason=held["reason"], detail=held["detail"])
        return {"outcome": "held", "entry": entry_id, "assignment": composed,
                "observed": seen}

    result = seen["result"]
    settlement = _settled(result)
    if settlement is None:
        # THE MODEL ANSWERED IN A SHAPE THE COORDINATOR CANNOT SETTLE. That is
        # runtime material outside its contract, so it reaches the same place
        # unreadable material does rather than an exception, and the target is
        # held for an operator.
        held = runtime.hold_account(
            reason="result-foreign",
            observed=f"the {result['outcome']} result's detail is not a "
                     f"settlement this coordinator can record",
            detail={"attempt_id": composed["attempt_id"],
                    "outcome": result["outcome"]})
        block_target(store, canonical_target_id=canonical_target_id,
                     entry_id=entry_id, lease_id=lease_id, fence=fence,
                     reason=held["reason"], detail=held["detail"])
        return {"outcome": "held", "entry": entry_id, "assignment": composed,
                "observed": dict(seen, hold=held)}

    if result["outcome"] == "held":
        # THE MODEL'S OWN STATEMENT ABOUT THE TARGET, which is the other way to
        # reach a block: it reports an account nobody can reconcile.
        block_target(store, canonical_target_id=canonical_target_id,
                     entry_id=entry_id, lease_id=lease_id, fence=fence,
                     reason=settlement["reason"],
                     detail=settlement["detail"])
        return {"outcome": "held", "entry": entry_id, "assignment": composed,
                "observed": seen}

    # BOTH REMAINING OUTCOMES SETTLE, so both are behind the two proofs.
    live_grant(store, lease_id=lease_id,
               canonical_target_id=canonical_target_id, entry_id=entry_id,
               fence=fence)
    _quiescent(manager, composed["attempt_id"])

    if result["outcome"] == "refused":
        # ORDINARY PRE-MUTATION REFUSAL. The candidate is not integrable, the
        # target is untouched, and `refuse_entry` ends the grant in the same
        # transaction that refuses the entry so the queue may move on.
        refuse_entry(store, canonical_target_id=canonical_target_id,
                     entry_id=entry_id, settlement=settlement,
                     lease_id=lease_id, fence=fence)
        return {"outcome": "refused", "entry": entry_id,
                "assignment": composed, "observed": seen}

    # A MODEL'S INTEGRATED RESULT IS NOT COORDINATOR COMPLETION. The driver
    # must first write and re-read the exact Authority receipt while this live
    # lease still excludes every later writer. Returning the owned settlement
    # gives that orchestrator the only value `complete_integrated` will accept.
    return {"outcome": "integrated", "entry": entry_id,
            "assignment": composed, "observed": seen,
            "settlement": settlement}


def complete_integrated(store, assignment, settlement):
    """Settle and release only after the caller proved Authority completion."""
    composed = runtime._owned_assignment(assignment)
    account = _settlement(settlement, "integrated",
                          "an Authority-completed integration settlement")
    lease_id = composed["lease_id"]
    canonical_target_id = composed["canonical_target_id"]
    entry_id, fence = composed["entry_id"], composed["fence"]
    # The completion-side cutpoint is repeated here immediately before the
    # first coordinator transition. A second writer remains excluded until
    # release_lease ends this exact grant.
    live_grant(store, lease_id=lease_id,
               canonical_target_id=canonical_target_id, entry_id=entry_id,
               fence=fence)
    settle_integrated(store, lease_id=lease_id,
                      canonical_target_id=canonical_target_id, fence=fence,
                      entry_id=entry_id, settlement=account)
    release_lease(store, lease_id=lease_id,
                  canonical_target_id=canonical_target_id, entry_id=entry_id,
                  fence=fence, ending={"outcome": "integrated"})
    return {"outcome": "integrated", "entry": entry_id,
            "assignment": composed}
