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
from . import git_profile, reconciliation, runtime
from .admission import resolved_account, source_account
from .queue import (ELIGIBILITY_MEMBERS, _settlement, block_target,
                    grant_lease, live_grant, refuse_entry, release_lease,
                    settle_integrated)

__all__ = ["INTEGRATION_PORT", "OUTCOMES", "POST_IMPORT_MEMBERS",
           "finalize_direct_target",
           "POST_IMPORT_VERB", "authorized_result_eligibility",
           "complete_integrated", "complete_reconciled",
           "import_authorized_result", "integrate_next", "reconciled_result",
           "settle_observed"]

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


# WHAT THE REQUIRED POST-IMPORT TESTS ARE ASKED THROUGH, and what they must
# answer. Review 2026-09-10T14:20:24Z [R1]: this branch had no such owner at
# all and called a Git content readback `verification`.
#
# THE MEMBER SET IS W133117'S CAUSAL OBSERVATION SHAPE deliberately, minus the
# member that only a base run needs. An import's evidence and the combined
# observation it was approved on are then the same document to read, which is
# what lets an operator compare them.
POST_IMPORT_VERB = "verify_imported"
POST_IMPORT_MEMBERS = ("command", "test_identity", "input_commit",
                       "input_tree", "test_digest", "environment", "status",
                       "output", "execution")


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


def reconciled_result(store, entry):
    """WHICH result this entry is, or `None` if it is a direct import.

    THE COORDINATOR'S OWN CUSTODY RECORD DECIDES, not a caller and not a new
    column. W133117 gives this store `integration_results`, and a reconciled
    result publishes a DERIVED Authority proposal that nothing else has. So an
    entry whose admitted `proposal_id` is some row's `derived_proposal_id` is
    that row's import, and every other entry is the direct path exactly as it
    was. Adding an entry column to say the same thing would be a schema
    expansion Q was not granted, and a caller-supplied flag would be the
    "which branch am I" question answered by the least informed party.
    """
    admitted = entry["eligibility"]
    row = store._connection.execute(
        "SELECT result_id FROM integration_results "
        "WHERE derived_proposal_id = ?", (admitted["proposal_id"],)).fetchone()
    return None if row is None else row["result_id"]


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
    if reconciled_result(store, entry) is not None:
        # A RECONCILED RESULT REACHED THE MODEL PATH, which is a wiring
        # statement about this deployment rather than a statement about the
        # candidate. `import_authorized_result` is its owner: its bytes are
        # already composed, observed and independently approved, and there is
        # nothing for a model to compose. INTEGRITY, so `_stale` blocks the
        # target and keeps the lease for an explicit operator rather than
        # terminally refusing a candidate that is perfectly integrable.
        return (None, ContractRefusal(
            "integrity", "schema",
            f"entry {name_value(entry['entry_id'])} is a reconciled "
            f"integration result and is imported by its own owner, not by a "
            f"runtime asked to compose one"))
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


# THE SEVEN MEMBERS A RECONCILED RESULT ANSWERS FOR ITSELF, and the eight it
# keeps from the producer that made the submission. `preserve both source and
# derived identities` is this split, written once.
_DERIVED_MEMBERS = ("proposal_id", "candidate_digest", "result_id",
                    "result_digest", "expected_target_revision",
                    "path_set_digest", "profile_kind")
_SOURCE_MEMBERS = tuple(name for name in ELIGIBILITY_MEMBERS
                        if name not in _DERIVED_MEMBERS)


def authorized_result_eligibility(store, profile, manager, jobs, authority, *,
                                  result_id):
    """The queue account for one AUTHORIZED reconciled result.

    A RECONCILED RESULT IS AN ORDINARY QUEUE CANDIDATE, and this is the
    document that says so. The queue stores an already-proved eligibility
    account and never re-derives one, so what matters is that every member
    comes from an owner that proved it rather than from a caller.

    TWO PROVED READERS, NO THIRD SPELLING. `admission.source_account` answers
    the producer's own eight members -- the Authority, the Work, the assignment
    generation, the line, the checkpoint, the verdict, the checkpoint digest
    and the scope digest -- as ELIGIBILITY and nothing more, which is exactly
    what a submission whose target moved still is.
    `reconciliation.resolve_import_account` answers the RESULT's seven: its own
    derived proposal, its own frozen result identity and digest, the prepared
    combined commit as the candidate, the snapshot it was actually prepared
    onto as the expected target, and its content digest as the path set. Where
    the two overlap they are compared member for member, so an account that
    stopped agreeing with its own producer never reaches a rank.

    AND `checkpoint_id` STAYS THE PRODUCER'S, deliberately. The queue's
    `UNIQUE (canonical_target_id, authority_uuid, checkpoint_id)` is the
    one-candidate-one-place rule; keeping the source checkpoint there means a
    submission cannot hold two places on one target by being reconciled, which
    is the rule that index exists for rather than an accident of reuse.
    """
    account = reconciliation.resolve_import_account(
        store, profile, manager, jobs, authority, result_id=result_id)
    # The line is the record's own immutable operand; the account answers the
    # identities an import acts on and deliberately carries no selector.
    line_id = reconciliation.result_of(store, result_id)["line_id"]
    source = source_account(manager, jobs, authority, line_id=line_id,
                            proposal_id=account["source_proposal_id"])
    for member, expected in (("authority_uuid", account["authority_uuid"]),
                             ("work_id", account["work_id"]),
                             ("proposal_id", account["source_proposal_id"]),
                             ("checkpoint_id", account["source_checkpoint_id"])):
        if source[member] != expected:
            _refuse(f"this result was prepared from {member} "
                    f"{name_value(expected)} and its accepted producers now "
                    f"say {name_value(source[member])}",
                    category="refused", code="precondition")
    eligibility = {name: source[name] for name in _SOURCE_MEMBERS}
    eligibility.update({
        "proposal_id": account["derived_proposal_id"],
        "result_id": account["derived_result_id"],
        "result_digest": account["derived_result_digest"],
        "candidate_digest": account["candidate_digest"],
        "expected_target_revision": account["expected_target_revision"],
        "path_set_digest": account["content_digest"],
        "profile_kind": source["profile_kind"]})
    if set(eligibility) != set(ELIGIBILITY_MEMBERS):
        _refuse("a reconciled result's eligibility account is the queue's own "
                "closed member set")
    return account, eligibility


def _delivered(runner, argv, what):
    """One composed profile vector, run through the deployment's OWN runner.

    THE RUNNER IS THE CAPABILITY AND THE VECTOR IS THE COMPOSITION, which is
    `git_profile`'s own division: it composes argv and opens no process. The
    dedicated target must actually hold the prepared commit before a reference
    can name it, and `import_vector` is the exported composition for exactly
    that. Naming the runner here rather than adding a verb to `git_profile`
    keeps P's independently accepted profile bytes untouched.
    """
    boundaries.capability(runner, "the injected Git command runner")
    answer = runner(tuple(argv))
    if type(answer) is not dict or set(answer) != {"returncode", "stdout",
                                                   "stderr"}:
        _refuse(f"the Git runner's {what} answer has the closed "
                f"command-result shape")
    if type(answer["returncode"]) is not int \
            or type(answer["returncode"]) is bool:
        _refuse(f"the Git runner's {what} status is an integer")
    if answer["returncode"] != 0:
        _refuse(f"Git {what} failed: {answer['stderr'].strip()[:240]}",
                category="refused", code="precondition")
    return answer["stdout"]


def _admitted_for(store, held, entry_id):
    """The named entry IS this result's, proved BEFORE a fence is burned.

    REVIEW 2026-09-10T14:20:24Z [R2], the first half of its correction. This
    granted the requested entry and then resolved the result INDEPENDENTLY,
    comparing only the target -- so a live grant admitted for ANOTHER proposal
    on the same target authorized this result's fetch and reference advance,
    which the reviewer's probe drove all the way to a real target write. The
    terminal act catches it afterwards, and afterwards is too late for a write.

    THIS HALF COSTS NOTHING AND BURNS NOTHING. `result_of` is a pure read of
    this record's own custody, so the five members that identify a reconciled
    candidate can be compared with the entry's admitted account before
    `grant_lease` is called at all. A wrong entry never receives a grant.
    """
    row = store._connection.execute(
        "SELECT canonical_target_id, proposal_id, result_id, result_digest, "
        "candidate_digest, expected_target_revision FROM entries "
        "WHERE entry_id = ?", (entry_id,)).fetchone()
    if row is None:
        _refuse(f"this coordinator holds no entry {name_value(entry_id)}",
                category="refused", code="precondition")
    for member, expected in (
            ("canonical_target_id", held["canonical_target_id"]),
            ("proposal_id", held["derived_proposal_id"]),
            ("result_id", held["derived_result_id"]),
            ("result_digest", held["derived_result_digest"]),
            ("candidate_digest", held["prepared"]["head"]),
            ("expected_target_revision", held["target_revision"])):
        if row[member] != expected:
            _refuse(f"entry {name_value(entry_id)} was admitted with {member} "
                    f"{name_value(row[member])} and this result's is "
                    f"{name_value(expected)}; a grant for another candidate "
                    f"authorizes no byte of this one",
                    category="refused", code="precondition")
    return row


def _granted_for(granted, eligibility, integrator_participant, held):
    """AND THE GRANT THIS MODULE ACTUALLY HOLDS IS THIS RESULT'S.

    Review [R2], the second half. The pre-grant check above compares the entry
    as it stands; this compares the FULL freshly derived account -- all fifteen
    members -- against the account the entry the store actually leased was
    admitted with, and binds the configured integrating participant and the
    result's own live integration assignment to that lease. Both halves are
    needed: the first refuses before a fence is burned, and this one is the
    proof that the lease in hand is over the entry that was just re-proved.
    """
    entry = granted["entry"]
    admitted = entry["eligibility"]
    for name in sorted(ELIGIBILITY_MEMBERS):
        if admitted.get(name) != eligibility.get(name):
            _refuse(f"the granted entry {name_value(entry['entry_id'])} was "
                    f"admitted with {name} {name_value(admitted.get(name))} "
                    f"and this result's account now says "
                    f"{name_value(eligibility.get(name))}",
                    category="refused", code="precondition")
    lease = granted["lease"]
    if lease["entry_id"] != entry["entry_id"]:
        _refuse(f"lease {name_value(lease['lease_id'])} is over entry "
                f"{name_value(lease['entry_id'])}, not the entry this import "
                f"proved", category="refused", code="precondition")
    if lease["integrator_participant"] != integrator_participant:
        _refuse(f"the live grant is held by "
                f"{name_value(lease['integrator_participant'])} and this "
                f"import acts for {name_value(integrator_participant)}",
                category="policy", code="denied")
    assignment = held["integration_assignment"]
    if assignment["participant"] != integrator_participant:
        _refuse(f"this result's integration assignment names "
                f"{name_value(assignment['participant'])} and the configured "
                f"integrating participant is "
                f"{name_value(integrator_participant)}",
                category="policy", code="denied")
    return admitted


def _post_import_execution(verifier, basis):
    """ASK THE CONFIGURED OWNER TO RUN THE REQUIRED TESTS, and keep what it did.

    REVIEW 2026-09-10T14:20:24Z [R1]. This branch read the imported tree back
    and LABELLED that readback `verification`, so a result reached an
    integrated Authority receipt, a settled entry and terminal custody without
    one test ever executing against the imported bytes. Object equality is a
    statement about which objects are present; INTEGRATION-CONTRACT-v1
    sections 4 and 6 require retained post-import TESTS, and
    DELIVERY-SCOPE-2026-09-10 keeps that check and its failed-test hold as
    essential minimums rather than parked hardening.

    IT IS AN OWNER'S ANSWER, NOT A CALLER'S ARGUMENT -- the same shape W133117
    settled on for the causal observations, and deliberately the same closed
    member set, so an operator can read an import's evidence beside the
    combined observation it was approved on. The question is derived here; what
    comes back must name the candidate and tree it was asked about.

    IT IS ASKED OUTSIDE THE HOLD, AND ITS ANSWER IS OWNED INSIDE ONE. Review
    2026-09-10T14:33:43Z [R3] found this the hard way: a single `try` around
    both turned ANY refusal the owner's own work provoked -- including the
    coordinator's own, when that work recovered this very grant -- into a
    second `block_target` for the same target and entry, which collided with
    the first and buried the real refusal. So the owner is asked here, and only
    the SHAPE of what it answers is adopted under the caller's hold. A
    configured owner that explodes is not answering, and its refusal is not
    this module's to relabel; W133117's observation owner is asked exactly this
    way.
    """
    boundaries.capability(getattr(verifier, POST_IMPORT_VERB, None),
                          f"the configured post-import verification owner's "
                          f"{POST_IMPORT_VERB} capability")
    actor = boundaries.text(getattr(verifier, "participant", None),
                            "the configured post-import owner's participant")
    return getattr(verifier, POST_IMPORT_VERB)(dict(basis)), actor


def _owned_post_import(answered, actor, basis):
    """The answer, owned. Unreadable material reaches the caller's hold."""
    answer = boundaries.document(answered, "the post-import verification",
                                 required=POST_IMPORT_MEMBERS)
    for member in ("input_commit", "input_tree"):
        if answer[member] != basis[member]:
            _refuse(f"the post-import verification was run against {member} "
                    f"{name_value(answer[member])} and the imported result is "
                    f"{name_value(basis[member])}; evidence about other bytes "
                    f"is not this import's",
                    category="integrity", code="digest")
    for member in ("command", "test_identity", "test_digest", "environment"):
        boundaries.text(answer[member],
                        f"a post-import verification's {member}")
    if type(answer["output"]) is not str:
        # EMPTY IS A REAL ANSWER for a test that printed nothing, so this is a
        # type check rather than `boundaries.text`, which requires a value.
        _refuse("a post-import verification's output is text",
                category="integrity", code="schema")
    if type(answer["status"]) is not int or type(answer["status"]) is bool:
        _refuse("a post-import verification answers an integer exit status",
                category="integrity", code="schema")
    if answer["execution"] != actor:
        _refuse(f"the post-import verification owner acts for "
                f"{name_value(actor)} and attested execution "
                f"{name_value(answer['execution'])}",
                category="policy", code="denied")
    return answer


def import_authorized_result(store, profile, runner, manager, jobs, authority,
                             verifier, *, canonical_target_id, entry_id,
                             lease_id, integrator_participant, attempt_id,
                             result_id):
    """Put ONE authorized reconciled result's bytes on the dedicated target.

    THIS IS THE TRANSITION W131409 HAS BEEN MISSING. P composes the second
    Job's submission with the target snapshot the first Job left, retains the
    causal observations, publishes an unapproved derived candidate and adopts
    three real independent Authority receipts. Nothing then MOVED the target.
    This does, through the ordinary coordinator: the queue's own smallest rank,
    one burned fence, the live grant re-read immediately before the write, and
    the settlement and release the queue already owns.

    THERE IS NO MODEL IN THIS BRANCH, and that is the point rather than an
    omission. `integrate_next` asks a runtime to COMPOSE an import because a
    direct candidate's bytes must still be reconciled with the target. These
    bytes were reconciled in P, observed by an independent owner, published and
    approved; asking a model to compose them again would be asking it to
    re-derive an object three participants have already signed. What a model
    path supplies and this one must supply too is the REQUIRED POST-IMPORT
    TESTS, and review [R1] is why that sentence is here: a deterministic branch
    earns its determinism by producing the same evidence, not by being excused
    from it.

    THE ORDER, and each step is somebody's proof:

      1. The named entry is proved to be THIS result's before a fence is burned
         (review [R2]), from the entry's own admitted account.
      2. `grant_lease` takes this target's smallest queued rank and burns one
         fence. Not the head, or another live lease, and this is a no-act.
      3. `resolve_import_account` RE-PROVES everything at the moment of asking:
         the accepted producers, the live integration assignment, the derived
         proposal, all three receipts and the current policy generation, the
         nominated storage and its isolation from the producer, and the
         dedicated target's CURRENT revision against the pinned snapshot. A
         target that moved again refuses HERE, with nothing written.
      4. The FULL freshly derived account is compared with the account the
         leased entry was admitted with, and the configured participant is
         bound to both the live grant and this result's own assignment.
      5. The live grant is re-read immediately before the first byte moves, and
         the prepared commit is delivered into the dedicated target.
      6. THE REQUIRED POST-IMPORT TESTS RUN, on the imported candidate, BEFORE
         the reference names it. A failing or unreadable execution holds the
         target with its retained evidence and reaches no reference advance, no
         Authority receipt, no settlement and no release.
      7. Only then is the reference advanced by COMPARE-AND-SWAP from the exact
         revision this result was reviewed against. A second writer that moved
         the target in between loses the swap; Git refuses it, not this module.
      8. The content is read back from the target itself and must be the
         authorized path, mode and object set. The readback is kept BESIDE the
         executed tests rather than instead of them.

    IT ANSWERS THE SETTLEMENT AND SETTLES NOTHING. The Authority integration
    receipt and the terminal custody act come next and belong to the driver, so
    what comes back is the value `complete_reconciled` will accept -- exactly
    as `settle_observed` answers for the model path.
    """
    boundaries.capability(getattr(store, "_connection", None),
                          "the integration coordinator store")
    boundaries.identity(canonical_target_id, "a canonical target id")
    boundaries.identity(entry_id, "an entry id")
    boundaries.identity(lease_id, "a lease id")
    boundaries.identity(attempt_id, "an integrator attempt id")
    boundaries.text(integrator_participant, "an integrator participant")

    # 1. THE ENTRY IS THIS RESULT'S, before anything is granted or burned.
    held = reconciliation.result_of(store, result_id)
    if held["canonical_target_id"] != canonical_target_id:
        _refuse(f"result {name_value(result_id)} is on target "
                f"{name_value(held['canonical_target_id'])} and this entry is "
                f"on {name_value(canonical_target_id)}",
                category="refused", code="precondition")
    _admitted_for(store, held, entry_id)

    granted = grant_lease(
        store, canonical_target_id=canonical_target_id, entry_id=entry_id,
        lease_id=lease_id, integrator_participant=integrator_participant,
        attempt_id=attempt_id)
    if granted is None:
        return {"outcome": None, "entry": None, "assignment": None,
                "observed": None}
    fence = granted["lease"]["fence"]

    # RE-PROVED UNDER THE GRANT AND BEFORE ANY WRITE. A result whose target,
    # producers, assignment, receipts, policy or storage moved while it waited
    # is settled with the verb the record ruled, with nothing imported.
    try:
        account, eligibility = authorized_result_eligibility(
            store, profile, manager, jobs, authority, result_id=result_id)
    except ContractRefusal as refused:
        outcome = _stale(store, entry_id, canonical_target_id, lease_id, fence,
                         refused)
        return {"outcome": outcome, "entry": entry_id, "assignment": None,
                "observed": {"state": "not-assigned", "result": None,
                             "hold": None, "refused": str(refused)},
                "result_id": result_id}
    held = reconciliation.result_of(store, result_id)
    _granted_for(granted, eligibility, integrator_participant, held)

    target_root = held["target_source"]["path"]
    reference = held["target_reference"]
    candidate = account["candidate_digest"]
    reviewed = account["expected_target_revision"]

    # THE PRE-MUTATION CUTPOINT, immediately before the first byte moves.
    live_grant(store, lease_id=lease_id,
               canonical_target_id=canonical_target_id, entry_id=entry_id,
               fence=fence)
    _delivered(runner,
               git_profile.import_vector(target_root,
                                         held["workspace"]["path"], candidate),
               "prepared result delivery")
    proved = profile.held(target_root, candidate, "the imported result")

    # THE REQUIRED POST-IMPORT TESTS, on the imported bytes, BEFORE the
    # reference names them.
    basis = {"result_id": result_id, "candidate": candidate,
             "input_commit": candidate, "input_tree": proved["tree"],
             "target_root": target_root, "reference": reference,
             "reviewed": reviewed}
    # THE OWNER IS ASKED OUTSIDE THE HOLD (review [R3]): a refusal its own work
    # provokes -- the coordinator's included -- is not this module's to relabel
    # as unreadable evidence, and relabelling it is what buried the real one.
    answered, actor = _post_import_execution(verifier, basis)
    try:
        executed = _owned_post_import(answered, actor, basis)
    except ContractRefusal as refused:
        # THE HOLD ACCOUNT IS COMPOSED HERE, not through
        # `runtime.hold_account`: that owner's four reasons are about a
        # RUNTIME's interruption and this branch has no runtime. `_stale`
        # already composes a block account the same way, from the coordinator's
        # own vocabulary rather than the runtime boundary's.
        held_account = {
            "reason": "post-import-verification-unreadable",
            "detail": {"result_id": result_id, "candidate": candidate,
                       "observed": str(refused)}}
        block_target(store, canonical_target_id=canonical_target_id,
                     entry_id=entry_id, lease_id=lease_id, fence=fence,
                     reason=held_account["reason"],
                     detail=held_account["detail"])
        return {"outcome": "held", "entry": entry_id, "assignment": None,
                "observed": {"state": "held", "result": None,
                             "hold": held_account, "refused": str(refused)},
                "result_id": result_id}
    if executed["status"] != 0:
        # THE FAILED-TEST HOLD. The reference was never advanced, so the target
        # still holds exactly what the first Job left -- and it is BLOCKED with
        # the execution that failed, because objects for a candidate whose
        # tests fail are now in that repository and no later entry may be
        # offered into it until somebody says so.
        held_account = {
            "reason": "post-import-tests-failed",
            "detail": {"result_id": result_id, "candidate": candidate,
                       "observed": f"the required post-import tests answered "
                                   f"status {executed['status']} on the "
                                   f"imported result",
                       "verification": executed}}
        block_target(store, canonical_target_id=canonical_target_id,
                     entry_id=entry_id, lease_id=lease_id, fence=fence,
                     reason=held_account["reason"],
                     detail=held_account["detail"])
        return {"outcome": "held", "entry": entry_id, "assignment": None,
                "observed": {"state": "held", "result": None,
                             "hold": held_account, "refused": None},
                "result_id": result_id, "verification": executed}

    # THE THIRD CUTPOINT, AND THE VERIFICATION IS WHY IT EXISTS. Review
    # 2026-09-10T14:33:43Z [R3]: the grant was proved live before the fetch and
    # then not again, so a holder recovered WHILE the configured tests ran --
    # through the ordinary public `block_target`/`abandon_lease` pair, which is
    # exactly how the direct path's own accepted control recovers one -- still
    # reached this compare-and-swap. The reviewer's probe advanced the real
    # reference and wrote a real integration receipt before anything refused.
    #
    # Running the required tests is the longest interval in this branch, so it
    # is the interval most likely to outlive its grant. `live_grant` re-reads
    # the exact target, entry, lease and fence from the store; a recovered
    # grant refuses HERE, with the reference untouched, no receipt, no
    # settlement and no release, and the recovering owner's held state is left
    # exactly as that owner made it.
    live_grant(store, lease_id=lease_id,
               canonical_target_id=canonical_target_id, entry_id=entry_id,
               fence=fence)
    imported = profile.advance(target_root, reference=reference,
                               imported=candidate, reviewed=reviewed)

    # AND THE READBACK, from the target's own bytes rather than from what was
    # asked for -- kept BESIDE the executed tests, never instead of them.
    settled = profile.revision(target_root, reference)
    observed = profile.content(target_root, settled)
    if settled != candidate or imported != candidate:
        _refuse(f"the dedicated target holds {name_value(settled)} after the "
                f"import and this result is {name_value(candidate)}",
                category="integrity", code="digest")
    if observed != account["content"]:
        _refuse("the dedicated target's content after the import is not the "
                "authorized path, mode and object set",
                category="integrity", code="digest")
    settlement = _settlement(
        {"imported_paths": sorted(observed),
         "verification": {"kind": "reconciled-result-import",
                          "result_id": result_id,
                          "derived_proposal_id": account["derived_proposal_id"],
                          "derived_result_id": account["derived_result_id"],
                          "candidate": candidate, "reviewed": reviewed,
                          "reference": reference, "settled": settled,
                          "content_digest": account["content_digest"],
                          "paths": len(observed),
                          "post_import_tests": executed}},
        "integrated", "a reconciled result's settlement")
    return {"outcome": "integrated", "entry": entry_id, "assignment": None,
            "observed": None, "settlement": settlement,
            "result_id": result_id, "account": account,
            "verification": executed, "lease": granted["lease"]}


def _complete(store, settlement, *, canonical_target_id, entry_id, lease_id,
              fence):
    """ONE ENDING, ONE OWNER, whichever branch reached it.

    The model path and the reconciled-result path differ in who composed the
    bytes and in whether a runtime was ever asked; they do not differ in what
    an integrated ending IS. Both prove the grant live one last time, settle
    the entry and drain the exact lease, in that order.
    """
    account = _settlement(settlement, "integrated",
                          "an Authority-completed integration settlement")
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
    return {"outcome": "integrated", "entry": entry_id}


def finalize_direct_target(store, profile, runner, *, canonical_target_id,
                           entry_id, lease_id, fence, source, candidate,
                           accepted_old, target_root, reference):
    """Put an ordinary DIRECT integration's accepted bytes on the dedicated
    target, and advance its configured reference from the accepted old one.

    OWNER return137905, AMENDMENT-direct-target-finalization-v1. W133129's
    witness measured the gap: after an ordinary direct integration completed,
    the Authority's canonical target was the accepted candidate while the
    dedicated target repository still held the ORIGINAL base and did not
    contain the candidate object at all. The worker imports approved path bytes
    and deliberately changes no repository metadata; nothing else finalized the
    Git target. So the second Job had no revision to reconcile onto and no
    reference for its own import to advance -- W133117 pins its snapshot by
    READING this reference and W133120 advances it by compare-and-swap.

    WHAT THIS DOES AND DOES NOT DO. It delivers the EXISTING accepted candidate
    commit out of the producer custody that was already proved, validates that
    the dedicated target really holds it, and advances the configured reference
    from the exact revision this integration was accepted against. It creates
    no commit, stages no index, rebases nobody, edits no candidate content and
    touches no working tree: the reference and the objects behind it are the
    dedicated target's content contract, and a checkout is a separate view this
    module does not claim to update.

    IT IS FENCED. The live grant is re-read immediately before the first byte
    moves, so a recovered holder finalizes nothing, and the compare-and-swap
    refuses if a second writer moved the reference in between -- Git's own
    refusal rather than this module's. An interrupted finalization holds
    conservatively; no restart guarantee is added here.
    """
    boundaries.identity(canonical_target_id, "a canonical target id")
    boundaries.identity(entry_id, "an entry id")
    boundaries.identity(lease_id, "a lease id")
    boundaries.generation(fence, "a lease fence")
    boundaries.text(target_root, "the configured dedicated target")
    boundaries.text(reference, "the configured target reference")
    boundaries.text(source, "the accepted candidate's source repository")

    boundaries.text(accepted_old, "the accepted old target revision")

    # THE ACCEPTED OLD TARGET IS THE ADMITTED ACCOUNT'S, NOT WHAT THE
    # REFERENCE HAPPENS TO SAY NOW. Review 2026-09-10T17:35:23Z [R1]: this
    # read the reference and used that reading as its own compare-and-swap
    # expected-old operand, which makes the swap unconditional -- whatever
    # drift a second writer had already left would simply become the baseline
    # and be overwritten. The revision this integration was ACCEPTED against
    # is `basis["target"]`, the proposal's own, and comparing it before any
    # effect is what makes drift a refusal instead of a starting point.
    held = profile.revision(target_root, reference)
    if held == candidate:
        # ALREADY AT THE CANDIDATE. Review [R2]: this returned success without
        # proving anything, so a reference somebody else had moved to these
        # bytes was adopted as this integration's own work. The grant and the
        # content are proved before it is adopted, and the accepted-old
        # comparison below still has to hold.
        live_grant(store, lease_id=lease_id,
                   canonical_target_id=canonical_target_id, entry_id=entry_id,
                   fence=fence)
        proved = profile.held(target_root, candidate, "the accepted candidate")
        return {"reference": reference, "revision": held, "advanced": False,
                "tree": proved["tree"], "reviewed": accepted_old}
    if held != accepted_old:
        _refuse(f"this integration was accepted against target "
                f"{name_value(accepted_old)} and the configured reference "
                f"{name_value(reference)} now holds {name_value(held)}; a "
                f"target that moved is reconciled again rather than "
                f"overwritten",
                category="stale-assignment", code="target")

    # THE PRE-MUTATION CUTPOINT, immediately before the first byte moves.
    live_grant(store, lease_id=lease_id,
               canonical_target_id=canonical_target_id, entry_id=entry_id,
               fence=fence)
    _delivered(runner, git_profile.import_vector(target_root, source,
                                                 candidate),
               "accepted candidate delivery")
    proved = profile.held(target_root, candidate, "the accepted candidate")

    # AND THE GRANT IS PROVED AGAIN AFTER DELIVERY, IMMEDIATELY BEFORE THE
    # SWAP. Review [R2]: delivery and readback are the longest interval here,
    # and a grant that ended inside it still reached the compare-and-swap. The
    # objects are already in the target by then, which is harmless -- they are
    # unreferenced -- but the reference write is not.
    live_grant(store, lease_id=lease_id,
               canonical_target_id=canonical_target_id, entry_id=entry_id,
               fence=fence)
    advanced = profile.advance(target_root, reference=reference,
                               imported=candidate, reviewed=accepted_old)
    settled = profile.revision(target_root, reference)
    if advanced != candidate or settled != candidate:
        _refuse(f"the dedicated target holds {name_value(settled)} after "
                f"finalization and this integration accepted "
                f"{name_value(candidate)}",
                category="integrity", code="digest")
    return {"reference": reference, "revision": settled, "advanced": True,
            "tree": proved["tree"], "reviewed": accepted_old}


def complete_integrated(store, assignment, settlement):
    """Settle and release only after the caller proved Authority completion."""
    composed = runtime._owned_assignment(assignment)
    return dict(_complete(store, settlement,
                          canonical_target_id=composed["canonical_target_id"],
                          entry_id=composed["entry_id"],
                          lease_id=composed["lease_id"],
                          fence=composed["fence"]),
                assignment=composed)


def complete_reconciled(store, answer):
    """The same ending for an import no runtime was ever asked to compose.

    It takes `import_authorized_result`'s own answer rather than a caller's
    reassembly of it, so the lease, entry, target and fence that are settled
    are the ones the grant actually returned.
    """
    lease = answer["lease"]
    return dict(_complete(store, answer["settlement"],
                          canonical_target_id=lease["canonical_target_id"],
                          entry_id=lease["entry_id"],
                          lease_id=lease["lease_id"], fence=lease["fence"]),
                assignment=None, result_id=answer["result_id"])
