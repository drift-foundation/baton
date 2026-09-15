"""W161230 slice 1: one reservation, and the executions accounted inside it.

THE PROBLEM THIS OWNS. A managed integration runs more than one execution --
a preparation phase, then the apply -- and each needs its own real Work, offer
and claim. `stage_allocations` is keyed by the stage attempt and its live
worker/principal indexes admit one row per capacity, so a second allocation for
a child could not be written at all; and a child with NO allocation is invisible
to `scheduler.reserve`, which is hidden capacity. Neither is acceptable.

SO THE CAPACITY IS NAMED RATHER THAN DUPLICATED. A root binds the integration
stage's OWN allocation -- by foreign key, so a root for a reservation nobody
made does not exist -- and every execution that runs under it is a MEMBER of
that root. The scheduler's occupancy is untouched: other Jobs go on seeing one
occupied integrator, and no new lane, principal or pool worker is introduced.

WHAT THE RELATIONS ENFORCE, structurally rather than by convention:

  - one root per allocation, and only for an integration-kind episode;
  - one membership per (root, phase), so a plan cannot quietly grow;
  - at MOST ONE admitted or recovery-required member per root, through a
    partial unique index -- which is what makes the phases serial;
  - a planned membership carries no claimed assignment, and an admitted one
    must; an ended one carries its outcome, and a live one must not.

WHAT IT DELIBERATELY DOES NOT DO. It starts nothing, claims nothing and ends
nothing on anybody's behalf: every operation here records a decision about
capacity from evidence its caller already obtained through the real owners. A
membership is not a stage, an attempt id here is the one a Worker Manager claim
actually produced, and `outcome` says what the execution DID while the state
says whether it is excluded -- two facts that must never be read off each other.
"""
import json

from ..contracts import ContractRefusal
from ..contracts.errors import name_value
from ..worker_manager import boundaries
from ..worker_manager.attempts import (assignment_of, attempt_runtime_of,
                                       unstarted_cancellation_of)
from ..worker_manager.offers import claimed_offers_for
from ..worker_manager.intake import intake_receipt_of
from ..worker_manager.output import frozen_output_of
from ..integration import managed_execution
from .scheduler import allocation_of
from .store import job_signature

__all__ = ["INTENT_KIND", "PREPARATION_INTENT_MEMBERS",
           "record_preparation_intent", "preparation_intent_of",
           "LIFECYCLES", "MEMBER_STATES", "PHASES", "LIVE_MEMBER_STATES",
           "EXCLUSIONS", "register_integration_capacity",
           "admit_integration_execution", "end_integration_execution",
           "require_integration_recovery", "begin_integration_ending",
           "integration_capacity_of", "root_of_allocation"]

LIFECYCLES = ("open", "ending", "ended")
PHASES = ("prepare", "apply")
MEMBER_STATES = ("planned", "admitted", "recovery-required",
                 "ended", "cancelled")
# THE STATES THAT OCCUPY THE ROOT. `recovery-required` is live on purpose:
# uncertainty holds capacity rather than freeing it.
LIVE_MEMBER_STATES = ("admitted", "recovery-required")
OUTCOMES = ("succeeded", "failed")

_PLAN_MEMBERS = ("phase", "execution_attempt_id", "execution_work_id",
                 "execution_offer_id", "participant", "task_digest",
                 "input_digest", "profile_digest")
# THE APPLY IS THE PARENT'S OWN ATTEMPT. Accepted design v2 section A: "apply
# member names the parent's actual attempt", and "Parent apply is registered
# too; it cannot bypass the check because it already owns the original
# allocation". Review 2026-09-13T18:02:07Z reproduced the gap: the apply was a
# SEPARATELY CLAIMED execution on another Work, another offer and another
# attempt, and registration compared none of the three against the episode that
# holds the reservation -- so the member accounted for something that was not
# the parent apply at all.
_PARENT_IDENTITY = (("execution_attempt_id", "attempt_id"),
                    ("execution_offer_id", "offer_id"),
                    ("execution_work_id", "work_id"))

# WHAT A PREPARATION COLLECTED IS THE WORKER MANAGER'S FACT. A frozen output
# with this disposition is a COLLECTED report; the other three dispositions are
# a worker that answered something else, and absence is a third answer again --
# no report was collected at all. The three are never read as each other.
COLLECTED_DISPOSITION = "completed"

# AND THE CUSTODY THAT MAKES CONTENT IMPORTABLE. Slice2 scope, the observed
# gap: a FROZEN output is the manager's receipt over a tree the writer stopped
# changing. It is not a statement that anything was taken into custody, and
# custody is what a later phase actually reads from. `accepted` is the one
# answer that says the bytes are held; `quarantined` says they were collected
# and are deliberately not to be used, which is a different fact from absence
# and must never be read as either success or nothing.
ACCEPTED_CUSTODY = "accepted"

# WHAT AN APPLY'S AUTHORIZATION MUST ANSWER. Accepted design v2 section A:
# "apply requires collected successful preparation, its closed execution
# membership, and the actual authorized derived candidate/grant". The
# preparation and the membership were proved; these two were not, and an
# admission that proves two of three is an admission that lets the third
# through.
#
# THE CAPABILITY IS THE CALLER'S NODE, NOT A DOCUMENT IT WRITES. Whether a
# candidate was independently approved is somebody else's fact, and an operand
# describing it would be the caller composing its own authorization -- which
# is the substitution this gate exists to refuse.
AUTHORIZATION_MEMBERS = ("schema", "managed_result_id",
                         "canonical_target_id", "derived_proposal_id",
                         "derived_result_id", "derived_result_digest",
                         "content_digest", "approved")
AUTHORIZATION_SCHEMA = "baton.v12.managed-authorization/1"

# AND THE GRANT THE APPLY WILL RUN UNDER, named by its four parts. A lease id
# with a fence is a replayable value, so the grant is READ from the coordinator
# rather than presented by its holder.
GRANT_MEMBERS = ("canonical_target_id", "entry_id", "lease_id", "fence")


# HOW A MEMBER MAY BE PROVED EXCLUDED. Each name is resolved through the owner
# that can answer it; neither is a word a caller may simply assert.
EXCLUSIONS = ("fenced-before-start", "runtime-destroyed")

# THE ATTEMPT RECORD'S OWN CONTRACT, WRITTEN DOWN HERE. Review
# 2026-09-13T17:38:55Z [P2]: the first form loaded `signature["operands"]`,
# checked that it was a dict naming this attempt and read two values out of it
# -- so a record naming ANOTHER OPERATION KIND in its envelope, or carrying
# members this build does not know, was evidence. `ControlStore.operation_record`
# owns the persisted row's COLUMN shapes; the semantics of what an
# `attempt.record` operation contains are the reader's to own, and that is what
# these three tuples are. They are fixed text, never derived from the value
# being checked.
_RECORD_KIND = "attempt.record"
_SIGNATURE_ENVELOPE = ("kind", "operands")
_RECORD_OPERANDS = ("attempt_id", "adapter_name", "adapter_digest",
                    "profile_digest", "input_digest", "policy_digest",
                    "image_digest", "toolchain_digest")
_RECORD_RESULT = ("attempt_id", "adapter_name", "profile_digest")

# AND THE OFFER MEMBERS THIS READS. `claimed_offers_for` returns a row already
# owned against the Worker Manager's own column contract, so the SET of columns
# is that owner's fact and is not re-closed here. What is this reader's fact is
# WHICH members it requires to be present before it compares them -- a fixed
# tuple, not "whatever the answer happened to contain".
_OFFER_IDENTITY = ("offer_id", "work_id", "authority_uuid", "participant",
                   "runtime_attempt_id", "claim_generation", "input_digest",
                   "profile_digest", "policy_digest")


# W161230 slice2: THE INTENT THAT PRECEDES A CHILD WORK.
#
# WHY IT IS WRITTEN FIRST. Creating a Work is an act at ANOTHER store, and the
# window between deciding to create one and learning that it exists is exactly
# where a crash loses track of it. So the decision is journalled here BEFORE
# the Authority is asked, and it carries the operation identity that creation
# will be made under -- `Authority.create_work` takes an explicit
# `operation_id`, so an interrupted creation is replayable rather than
# repeatable, and a restart finds the Work its own intent named instead of
# minting a second one.
#
# A CREATED WORK WITH REGISTRATION UNFINISHED IS RECOVERABLE INTENT, not
# permission to issue an offer or start anything: the intent records what was
# decided, and the registration below is what makes capacity accountable.
INTENT_KIND = "integration-capacity.intent"

PREPARATION_INTENT_MEMBERS = ("orchestration_id", "root_assignment_id",
                              "authority_uuid", "request_digest",
                              "execution_work_id", "execution_route",
                              "work_operation_id", "parent", "plan")

# THE PARENT FACTS AN INTENT BINDS, read from the allocation's own stage and
# episode rather than accepted: an intent naming a parent nobody reserved is a
# decision about somebody else's capacity.
INTENT_PARENT_MEMBERS = ("stage_id", "episode", "job_id", "work_id",
                         "attempt_id", "offer_id", "participant",
                         "canonical_principal", "worker_id",
                         "pool_generation")


def _refuse(message, *, category="refused", code="precondition"):
    raise ContractRefusal(category, code, message)


def _row(connection, statement, operands):
    found = connection.execute(statement, operands).fetchone()
    return None if found is None else {key: found[key] for key in found.keys()}


def _rows(connection, statement, operands):
    return [{key: row[key] for key in row.keys()}
            for row in connection.execute(statement, operands)]


def _configured_attempt(configured, execution_attempt_id):
    """The attempt's OWN committed configuration, owned end to end.

    The envelope, the operands AND the result. The journal row is persisted
    evidence from a store this process did not write, and the three parts say
    different things: the envelope says which operation this is, the operands
    say what it was asked with, and the result says what it answered. A reader
    that owns one of the three has owned the easiest one.
    """
    if configured is None:
        _refuse(f"execution {name_value(execution_attempt_id)} has no "
                f"attempt record at "
                f"{name_value(_RECORD_KIND + ':' + execution_attempt_id)}; "
                f"its configured digests are not readable and are not assumed")
    if configured["state"] != "committed":
        _refuse(f"the attempt record for "
                f"{name_value(execution_attempt_id)} is "
                f"{name_value(configured['state'])}; an operation nobody "
                f"committed configured nothing")
    if configured["kind"] != _RECORD_KIND:
        _refuse(f"the operation at "
                f"{name_value(_RECORD_KIND + ':' + execution_attempt_id)} is "
                f"a {name_value(configured['kind'])}; a record of another "
                f"kind is not this attempt's configuration")
    try:
        envelope = json.loads(configured["signature"])
    except ValueError:
        envelope = None
    envelope = boundaries.document(envelope, "the attempt record's signature",
                                   required=_SIGNATURE_ENVELOPE)
    # THE ENVELOPE'S OWN KIND. The row's `kind` column and the signature's are
    # two accounts of one fact, and a reader that checks the column alone would
    # accept a row whose signed document is about something else entirely.
    if envelope["kind"] != _RECORD_KIND:
        _refuse(f"the attempt record for "
                f"{name_value(execution_attempt_id)} is signed as "
                f"{name_value(envelope['kind'])}; its row and its signature "
                f"are two accounts of one operation and they disagree")
    operands = boundaries.document(envelope["operands"],
                                   "the attempt record's operands",
                                   required=_RECORD_OPERANDS)
    if operands["attempt_id"] != execution_attempt_id:
        _refuse(f"the attempt record at "
                f"{name_value(_RECORD_KIND + ':' + execution_attempt_id)} was "
                f"signed over attempt "
                f"{name_value(operands['attempt_id'])}; a record about "
                f"another attempt is not this one's configuration")
    try:
        answered = json.loads(configured["result"])
    except (TypeError, ValueError):
        answered = None
    result = boundaries.document(answered, "the attempt record's result",
                                 required=_RECORD_RESULT)
    # AND THE ANSWER IS ABOUT THE SAME ATTEMPT THE OPERANDS NAME. The result is
    # what a replay hands back, so a row whose two halves describe different
    # attempts would configure one attempt and report another.
    for name in _RECORD_RESULT:
        if result[name] != operands[name]:
            _refuse(f"the attempt record for "
                    f"{name_value(execution_attempt_id)} answered {name} "
                    f"{name_value(result[name])} for operands naming "
                    f"{name_value(operands[name])}")
    return operands


def _settled_offer(offers, execution_attempt_id):
    """The ONE claimed offer this attempt's claim settled.

    `claimed_offers_for` answers a list because an attempt with two claimed
    offers is a state somebody could reach; a membership is admitted against
    exactly one, and "the first of some" is not that.
    """
    if len(offers) != 1:
        _refuse(f"execution {name_value(execution_attempt_id)} has "
                f"{len(offers)} claimed offers; a membership is admitted "
                f"against exactly one")
    offer = offers[0]
    missing = [name for name in _OFFER_IDENTITY if offer.get(name) is None]
    if missing:
        _refuse(f"the claimed offer for "
                f"{name_value(execution_attempt_id)} answers no "
                f"{name_value(missing[0])}; the complete identity is what is "
                f"compared, and an absent member compares equal to nothing")
    # NO `runtime_attempt_id` COMPARISON HERE, and its absence is deliberate.
    # Measured, step 42: `claimed_offers_for` SELECTS on that column, so an
    # offer naming another attempt is not returned at all and the exactly-one
    # rule above is what refuses. A comparison beside it could never fail, and
    # an assertion that cannot fail is not an assertion. Its PRESENCE is still
    # required, because absence compares equal to nothing.
    return offer


def _owned_plan(plan):
    """The closed two-phase plan, owned once and used by both owners.

    Slice2: the intent and the registration take the SAME plan, and two
    spellings of "what a plan is" is how they come to disagree about one
    orchestration.
    """
    if type(plan) is not list or not plan:
        _refuse("a capacity plan is a non-empty list of phase memberships")
    taken = []
    for one in plan:
        member = boundaries.document(one, "a planned membership",
                                     required=_PLAN_MEMBERS)
        if member["phase"] not in PHASES:
            _refuse(f"a membership phase is one of {', '.join(PHASES)}; this "
                    f"is {name_value(member['phase'])}")
        boundaries.identity(member["execution_attempt_id"],
                            "an execution attempt id")
        boundaries.identity(member["execution_work_id"],
                            "an execution Work id")
        boundaries.identity(member["execution_offer_id"],
                            "an execution offer id")
        for name in ("participant", "task_digest", "input_digest",
                     "profile_digest"):
            boundaries.text(member[name], f"a membership {name}")
        taken.append(member)
    if len({one["phase"] for one in taken}) != len(taken):
        _refuse("a capacity plan names one phase more than once")
    # AND THE PARENT APPLY IS AN EXPLICIT MEMBER. Finish condition 1: an
    # orchestration whose apply is not planned would execute its apply outside
    # the accounting -- the exact hidden capacity these relations exist to
    # remove. Both phases are named at registration or the root is not one.
    if {one["phase"] for one in taken} != set(PHASES):
        _refuse(f"a capacity plan names every phase -- "
                f"{', '.join(PHASES)} -- and this names "
                f"{name_value(sorted(one['phase'] for one in taken))}; the "
                f"parent apply is accounted under this reservation or it is "
                f"capacity nobody can see")
    if len({one["execution_attempt_id"] for one in taken}) != len(taken):
        _refuse("a capacity plan names one execution attempt more than once")
    return taken


def _parent_facts(connection, store, root_assignment_id):
    """The reservation this orchestration runs inside, read from its own rows.

    Every member comes from the allocation the scheduler wrote and the stage
    and episode it belongs to. A caller supplies the assignment id and nothing
    else, which is what makes the answer the store's rather than the caller's.
    """
    allocation = allocation_of(store, root_assignment_id)
    if allocation is None:
        _refuse(f"stage assignment {name_value(root_assignment_id)} has no "
                f"allocation; an orchestration is intended inside capacity "
                f"the scheduler actually reserved")
    if allocation["allocation_state"] != "reserved":
        _refuse(f"stage assignment {name_value(root_assignment_id)} is "
                f"{name_value(allocation['allocation_state'])}; an intent "
                f"accounts capacity that is actually held")
    stage = _row(connection, "SELECT * FROM stages WHERE stage_id = ?",
                 (allocation["stage_id"],))
    if stage is None:
        _refuse(f"stage {name_value(allocation['stage_id'])} has no row")
    if stage["kind"] != "integration":
        _refuse(f"stage {name_value(allocation['stage_id'])} is a "
                f"{name_value(stage['kind'])} stage; this intent accounts "
                f"integration capacity")
    episode = _row(connection,
                   "SELECT * FROM episodes WHERE stage_id = ? AND episode = ?",
                   (allocation["stage_id"], allocation["episode"]))
    if episode is None:
        _refuse(f"stage {name_value(allocation['stage_id'])} has no episode "
                f"{name_value(allocation['episode'])}")
    return {"stage_id": stage["stage_id"], "episode": allocation["episode"],
            "job_id": stage["job_id"], "work_id": stage["work_id"],
            "attempt_id": episode["attempt_id"],
            "offer_id": episode["offer_id"],
            "participant": allocation["participant"],
            "canonical_principal": allocation["canonical_principal"],
            "worker_id": allocation["worker_id"],
            "pool_generation": allocation["generation"]}


def _intent_identity(operands):
    return INTENT_KIND + ":" + operands["orchestration_id"]


def record_preparation_intent(store, *, orchestration_id, root_assignment_id,
                              authority_uuid, request, execution_work_id,
                              execution_route, plan):
    """Decide a preparation BEFORE the Work it needs exists.

    WHAT THIS COMMITS IS A DECISION, NOT A CAPACITY. Nothing is admitted, no
    offer is issued and no runtime may start on the strength of it. What it
    buys is that the act at the Authority has a durable, exactly replayable
    identity on this side of the boundary: the `work_operation_id` below is
    what `Authority.create_work` is called with, so an interrupted creation is
    resumed rather than repeated.

    AND WHAT IT BINDS CANNOT DRIFT. The parent facts are read from the
    allocation's own stage and episode; the request is bound by digest; the
    plan is the same closed plan registration takes. A changed request, route,
    Work, plan or parent produces a different identity and collides rather
    than quietly replacing the decision this orchestration already made.
    """
    boundaries.identity(orchestration_id, "an orchestration id")
    boundaries.identity(root_assignment_id, "a stage assignment id")
    boundaries.text(authority_uuid, "an authority")
    boundaries.identity(execution_work_id, "the preparation's Work")
    boundaries.text(execution_route, "the preparation's route")
    bound = getattr(store, "authority_uuid", None)
    if bound != authority_uuid:
        _refuse(f"this Job store is bound to Authority {name_value(bound)} "
                f"and this intent names {name_value(authority_uuid)}")
    held = managed_execution.adopt_preparation_request(request)
    if held["orchestration_id"] != orchestration_id:
        _refuse(f"this request is for orchestration "
                f"{name_value(held['orchestration_id'])} and this intent is "
                f"{name_value(orchestration_id)}")
    taken = _owned_plan(plan)
    preparing = [one for one in taken if one["phase"] == "prepare"][0]
    if preparing["execution_work_id"] != execution_work_id:
        _refuse(f"the preparation is planned on Work "
                f"{name_value(preparing['execution_work_id'])} and this "
                f"intent creates {name_value(execution_work_id)}")
    # The request measures published source content; the membership binds the
    # ordinary worker input manifest. Admission checks that manifest against
    # the actual offer and attempt. Equating these distinct digests prevents
    # any ordinary launch. The profile remains the same configured identity.
    for mine, theirs in (("profile_digest", "profile_digest"),):
        if preparing[mine] != held[theirs]:
            _refuse(f"the preparation is planned with {mine} "
                    f"{name_value(preparing[mine])} and the request names "
                    f"{name_value(held[theirs])}")

    def intend(connection):
        parent = _parent_facts(connection, store, root_assignment_id)
        operands = {
            "orchestration_id": orchestration_id,
            "root_assignment_id": root_assignment_id,
            "authority_uuid": authority_uuid,
            "request_digest": managed_execution.request_digest(held),
            "execution_work_id": execution_work_id,
            "execution_route": execution_route,
            "work_operation_id": "integration-preparation.create-work:"
                                 + orchestration_id,
            "parent": parent,
            "plan": [dict(one) for one in taken]}
        return operands

    # THE OPERANDS ARE COMPOSED FROM THE STORE'S OWN ROWS FIRST, because the
    # identity is over them: a signature built from a caller's account of the
    # parent would make two different reservations one decision.
    operands = intend(store._connection)
    operation_id = _intent_identity(operands)
    signature = job_signature(INTENT_KIND, operands)

    def perform(connection):
        # RE-READ UNDER THE WRITE LOCK. The parent may have been released
        # between the composition above and this transaction, and an intent
        # about capacity that is gone is a decision nobody can act on.
        again = _parent_facts(connection, store, root_assignment_id)
        if again != operands["parent"]:
            _refuse(f"the reservation behind {name_value(orchestration_id)} "
                    f"changed while this intent was being composed")
        return dict(operands)

    return store.transact(operation_id, INTENT_KIND, signature, perform)


def preparation_intent_of(store, orchestration_id):
    """The decision this orchestration committed, or absence.

    ABSENCE IS AN ORDINARY ANSWER and the important one: an orchestration with
    no intent has decided nothing, whatever Work happens to exist elsewhere.
    """
    boundaries.identity(orchestration_id, "an orchestration id")
    found = store.operation_record(INTENT_KIND + ":" + orchestration_id)
    if found is None:
        return None
    if found["state"] != "committed" or found["kind"] != INTENT_KIND:
        _refuse(f"the intent of {name_value(orchestration_id)} is "
                f"{name_value(found['state'])} {name_value(found['kind'])}; "
                f"an act nobody committed decided nothing",
                category="integrity", code="schema")
    try:
        operands = json.loads(found["signature"])["operands"]
    except (TypeError, ValueError, KeyError):
        operands = None
    held = boundaries.document(operands, "a preparation intent",
                               required=PREPARATION_INTENT_MEMBERS)
    boundaries.document(held["parent"], "an intent's parent",
                        required=INTENT_PARENT_MEMBERS)
    # AND THE RECORDED ANSWER IS THE OPERANDS, so a row whose two halves
    # disagree is not this decision.
    try:
        answered = json.loads(found["result"])
    except (TypeError, ValueError):
        answered = None
    if answered != held:
        _refuse(f"the intent of {name_value(orchestration_id)} answered "
                f"something its own operands do not produce",
                category="integrity", code="schema")
    return held


def root_of_allocation(store, assignment_id):
    """The registered root binding this allocation, or absence.

    ABSENCE IS AN ORDINARY ANSWER: an allocation nobody registered is an
    ordinary one and keeps every ordinary behaviour, which is what lets this
    slice be additive rather than a change to how capacity already works.
    """
    boundaries.identity(assignment_id, "a stage assignment id")
    return _row(store._connection,
                "SELECT * FROM integration_capacity_roots "
                "WHERE root_assignment_id = ?", (assignment_id,))


def _members(connection, orchestration_id):
    return _rows(connection,
                 "SELECT * FROM integration_capacity_members "
                 "WHERE orchestration_id = ? ORDER BY phase",
                 (orchestration_id,))


def integration_capacity_of(store, orchestration_id):
    """The root AND every membership, so capacity is visible between phases.

    A reader that answered only about the live member would make the gap
    between preparation ending and apply beginning look like free capacity,
    which is exactly the moment an operator most needs to see it held.
    """
    boundaries.identity(orchestration_id, "an orchestration id")
    root = _row(store._connection,
                "SELECT * FROM integration_capacity_roots "
                "WHERE orchestration_id = ?", (orchestration_id,))
    if root is None:
        _refuse(f"no integration capacity root {name_value(orchestration_id)} "
                f"is registered")
    return {"root": root, "members": _members(store._connection,
                                              orchestration_id)}


def register_integration_capacity(store, *, orchestration_id,
                                  root_assignment_id, authority_uuid, plan):
    """Bind a root to an ACTUAL live allocation, and plan its phases.

    EVERYTHING ABOUT THE CAPACITY IS READ, NOT ACCEPTED. The worker,
    participant, principal and pool generation come from the row the scheduler
    wrote, and the Job, Work, stage and episode come from that allocation's own
    stage row -- review 2026-09-13T17:06:59Z [P1]: the first form COPIED a
    caller's `job_id`, `work_id` and `authority_uuid` without comparing them to
    anything, so a root could describe capacity that was reserved for somebody
    else. A root that disagrees with its reservation is accounting fiction.

    AND THE STAGE KIND IS THE STAGE ROW'S, not a string suffix. The first form
    read `stage_id.endswith("/integration")`, which is a naming convention
    rather than a fact: the `stages` row carries the kind and that is what is
    asked.

    THE PLAN IS PLANNED, NOT ADMITTED. Every membership starts `planned` with
    no claimed assignment: the Work and offer are intended, the claim has not
    happened, and inventing its generation here is precisely what this refuses.
    """
    boundaries.identity(orchestration_id, "an orchestration id")
    boundaries.identity(root_assignment_id, "a stage assignment id")
    boundaries.text(authority_uuid, "an authority")
    # AND IT IS THIS STORE'S OWN. Review 2026-09-13T17:23:49Z: the first form
    # took the caller's word and INSERTED it unchanged, so a root could record
    # a foreign Authority against real local capacity -- and my own handoff
    # said this was derived when it was not. The Job store is bound to one
    # Authority at open; the operand is compared with that binding rather than
    # believed, and a mismatch refuses.
    bound = getattr(store, "authority_uuid", None)
    if bound != authority_uuid:
        _refuse(f"this Job store is bound to Authority {name_value(bound)} and "
                f"this root names {name_value(authority_uuid)}")
    taken = _owned_plan(plan)
    operation_id = "integration-capacity.register:" + orchestration_id
    signature = job_signature(
        "integration-capacity.register",
        {"orchestration_id": orchestration_id,
         "root_assignment_id": root_assignment_id,
         "authority_uuid": authority_uuid,
         "plan": [dict(one) for one in taken]})

    def perform(connection):
        # AND IT REGISTERS THE DECISION THIS ORCHESTRATION ALREADY MADE.
        # Slice2: the intent is committed before the child Work exists, so a
        # registration that described a different plan, root or Authority
        # would be accounting for an orchestration nobody decided on. An
        # orchestration with NO intent is the slice1 shape and stays legal --
        # registration did not require one before and refusing here would
        # break capacity that never had a preparation.
        decided = preparation_intent_of(store, orchestration_id)
        if decided is not None:
            for member, given in (("root_assignment_id", root_assignment_id),
                                  ("authority_uuid", authority_uuid)):
                if decided[member] != given:
                    _refuse(f"orchestration {name_value(orchestration_id)} "
                            f"committed its intent with {member} "
                            f"{name_value(decided[member])} and this "
                            f"registration names {name_value(given)}")
            if decided["plan"] != [dict(one) for one in taken]:
                _refuse(f"orchestration {name_value(orchestration_id)} "
                        f"committed a different plan than this registration "
                        f"describes; a decision is not revised by registering "
                        f"something else")
        allocation = allocation_of(store, root_assignment_id)
        if allocation is None:
            _refuse(f"stage assignment {name_value(root_assignment_id)} has "
                    f"no allocation; a root names capacity the scheduler "
                    f"actually reserved")
        if allocation["allocation_state"] == "released":
            _refuse(f"stage assignment {name_value(root_assignment_id)} was "
                    f"already released; released capacity cannot be "
                    f"registered")
        if allocation["allocation_state"] != "reserved":
            _refuse(f"stage assignment {name_value(root_assignment_id)} is "
                    f"{name_value(allocation['allocation_state'])}; a root "
                    f"accounts capacity that is actually held")
        stage_id = allocation["stage_id"]
        stage = _row(connection,
                     "SELECT * FROM stages WHERE stage_id = ?", (stage_id,))
        if stage is None:
            _refuse(f"stage {name_value(stage_id)} has no row; a root names "
                    f"a stage this store admitted")
        if stage["kind"] != "integration":
            _refuse(f"stage {name_value(stage_id)} is a "
                    f"{name_value(stage['kind'])} stage; this root accounts "
                    f"integration capacity")
        job_id, work_id = stage["job_id"], stage["work_id"]
        # THE CONFIGURED ACTOR IS THE ALLOCATION'S. Every phase executes under
        # the participant the scheduler reserved, and a plan naming another one
        # would be a second actor's capacity wearing this reservation's name.
        foreign = [one for one in taken
                   if one["participant"] != allocation["participant"]]
        if foreign:
            _refuse(f"phase {name_value(foreign[0]['phase'])} names "
                    f"{name_value(foreign[0]['participant'])} and this "
                    f"reservation is held by "
                    f"{name_value(allocation['participant'])}")
        # AND THE APPLY IS THE PARENT'S OWN EXECUTION. The episode holding
        # this reservation already names an attempt and an offer, and the
        # stage names the Work; the apply membership accounts THAT execution
        # or it accounts something else while calling itself the parent.
        episode = _row(connection,
                       "SELECT * FROM episodes WHERE stage_id = ? "
                       "AND episode = ?", (stage_id, allocation["episode"]))
        if episode is None:
            _refuse(f"stage {name_value(stage_id)} has no episode "
                    f"{name_value(allocation['episode'])}; a root accounts an "
                    f"episode this store opened")
        parent = {"attempt_id": episode["attempt_id"],
                  "offer_id": episode["offer_id"],
                  "work_id": stage["work_id"]}
        applying = [one for one in taken if one["phase"] == "apply"][0]
        for mine, theirs in _PARENT_IDENTITY:
            if applying[mine] != parent[theirs]:
                _refuse(f"the apply names {mine} "
                        f"{name_value(applying[mine])} and the episode this "
                        f"reservation is held for is "
                        f"{name_value(parent[theirs])}; the apply IS the "
                        f"parent's own execution, not a second one wearing "
                        f"its accounting")
        # AND THE PREPARATION IS A SEPARATE ONE. It runs under the same actor
        # and the same reservation, and it is its own Work, offer and attempt:
        # a preparation wearing the parent's identity would BE the apply.
        preparing = [one for one in taken if one["phase"] == "prepare"][0]
        for mine, theirs in _PARENT_IDENTITY:
            if preparing[mine] == parent[theirs]:
                _refuse(f"the preparation names {mine} "
                        f"{name_value(preparing[mine])}, which is the "
                        f"parent's own; a preparation is the actor's separate "
                        f"execution under this reservation")
        connection.execute(
            "INSERT INTO integration_capacity_roots (orchestration_id, "
            "root_assignment_id, stage_id, episode, job_id, authority_uuid, "
            "work_id, pool_generation, worker_id, participant, "
            "canonical_principal, lifecycle, registered_operation_id, "
            "registered_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', "
            "?, ?)",
            (orchestration_id, root_assignment_id, stage_id,
             allocation["episode"], job_id, authority_uuid, work_id,
             allocation["generation"], allocation["worker_id"],
             allocation["participant"], allocation["canonical_principal"],
             operation_id, store._now()))
        for member in taken:
            connection.execute(
                "INSERT INTO integration_capacity_members "
                "(execution_attempt_id, orchestration_id, phase, "
                "execution_work_id, execution_offer_id, participant, "
                "task_digest, input_digest, profile_digest, state, "
                "registered_operation_id) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'planned', ?)",
                (member["execution_attempt_id"], orchestration_id,
                 member["phase"], member["execution_work_id"],
                 member["execution_offer_id"], member["participant"],
                 member["task_digest"], member["input_digest"],
                 member["profile_digest"], operation_id))
        return integration_capacity_of(store, orchestration_id)

    return store.transact(operation_id, "integration-capacity.register",
                          signature, perform)


def _owned_grant(grant):
    """The four parts of a grant, owned BEFORE any identity is composed.

    Review 2026-09-14T00:55:37Z: a malformed grant reached the signature, so a
    request this build cannot describe still produced a durable identity.
    """
    held = boundaries.document(grant, "the apply's grant",
                               required=GRANT_MEMBERS)
    boundaries.identity(held["canonical_target_id"], "a canonical target id")
    boundaries.identity(held["entry_id"], "an entry id")
    boundaries.identity(held["lease_id"], "a lease id")
    if type(held["fence"]) is not int or type(held["fence"]) is bool \
            or held["fence"] < 1:
        _refuse(f"a grant fence is a whole number from one; this is "
                f"{name_value(held['fence'])}")
    return {name: held[name] for name in GRANT_MEMBERS}


def _prove_grant(coordinator, grant):
    """The grant, FROM THE COORDINATOR, at this moment and no earlier.

    Review 2026-09-14T00:55:37Z [P1]: this ran before the authorization owner
    was called, and asking that owner is a call that can change the world --
    the reviewer's probe released this very lease from inside one, and the
    admission committed anyway. Whatever is checked last is the only thing
    true when the row is written.
    """
    from ..integration.queue import live_grant

    live_grant(coordinator, lease_id=grant["lease_id"],
               canonical_target_id=grant["canonical_target_id"],
               entry_id=grant["entry_id"], fence=grant["fence"])


def _approved_candidate(authorization, grant, collected, orchestration_id):
    """The approved derived candidate, from the owner that holds the question.

    NOT A CALLER'S WORD, and not discarded once compared: what comes back is
    returned so the admission can bind it into its own identity and retain it.
    """
    answer = authorization.authorized(
        {"managed_result_id": orchestration_id,
         "canonical_target_id": grant["canonical_target_id"],
         "content_digest": collected})
    if answer is None:
        _refuse(f"no authorization owner answered for "
                f"{name_value(orchestration_id)}; an unavailable owner "
                f"refuses an admission rather than granting one",
                category="policy", code="denied")
    approved = boundaries.document(answer, "the candidate authorization",
                                   required=AUTHORIZATION_MEMBERS)
    if approved["schema"] != AUTHORIZATION_SCHEMA:
        _refuse(f"an authorization is {name_value(AUTHORIZATION_SCHEMA)}; "
                f"this is {name_value(approved['schema'])}",
                category="integrity", code="schema")
    if approved["approved"] is not True:
        _refuse(f"the derived candidate for {name_value(orchestration_id)} is "
                f"not approved; an apply runs content somebody independently "
                f"authorized", category="policy", code="denied")
    for member, expected in (
            ("managed_result_id", orchestration_id),
            ("canonical_target_id", grant["canonical_target_id"]),
            ("content_digest", collected)):
        if approved[member] != expected:
            _refuse(f"the authorization names {member} "
                    f"{name_value(approved[member])} and this apply is "
                    f"{name_value(expected)}", category="policy",
                    code="denied")
    for member in ("derived_proposal_id", "derived_result_id"):
        boundaries.identity(approved[member], f"the authorized {member}")
    boundaries.text(approved["derived_result_digest"],
                    "the authorized derived result digest")
    return approved


def admit_integration_execution(store, control, *, orchestration_id, phase,
                                execution_attempt_id, assignment,
                                coordinator=None, authorization=None,
                                grant=None):
    """Admit ONE planned phase, with the claim that actually happened.

    AND SO ARE THE OFFER AND THE CONFIGURED DIGESTS. Review
    2026-09-13T17:33:59Z resolved a blocker I had reported wrongly: I said no
    public reader answered a claimed attempt's configured digests, and two do.
    `claimed_offers_for` answers the offer that claim actually settled, and the
    journal holds the attempt's own `attempt.record` operation with the
    operands it was configured under. So the plan, the offer and the recorded
    attempt must all agree, and anything unknown, malformed or contradictory
    refuses.

    THE CLAIM IS READ FROM THE WORKER MANAGER, not accepted from the caller.
    Review 2026-09-13T17:06:59Z [P1]: the first form checked the assignment
    document's three outer member names and the participant against the plan,
    which proves only that somebody built a well-formed dictionary. The
    Worker Manager owns that attempt, `assignment_of` is its public reader,
    and what it answers is the identity activation actually fixed -- so a
    membership is admitted against THAT, or not at all.

    ADMISSION IS THE GATE A RUNTIME START IS BEHIND. It is committed before
    anything is started, so a crash between the two leaves capacity held and
    an admitted member to reconcile -- never a runtime nobody accounted for.

    THE FIXED ASSIGNMENT IS TAKEN HERE AND ONCE. Its absence is legal only
    while a membership is planned.
    """
    boundaries.identity(orchestration_id, "an orchestration id")
    boundaries.identity(execution_attempt_id, "an execution attempt id")
    if phase not in PHASES:
        _refuse(f"a membership phase is one of {', '.join(PHASES)}; this is "
                f"{name_value(phase)}")
    held = boundaries.document(assignment, "the claimed assignment",
                               required=("work_ref", "participant",
                                         "generation"))
    boundaries.document(held["work_ref"], "the claimed assignment's Work",
                        required=("authority_uuid", "work_id"))
    boundaries.text(held["work_ref"]["authority_uuid"],
                    "the claimed assignment's authority")
    boundaries.identity(held["work_ref"]["work_id"],
                        "the claimed assignment's Work")
    boundaries.text(held["participant"], "the claimed assignment's participant")
    boundaries.generation(held["generation"],
                          "the claimed assignment's generation")
    # THE OWNER'S OWN ANSWER ABOUT THIS ATTEMPT. It refuses an attempt that
    # never activated, and what it returns is the four-part identity this
    # manager fixed -- which is the thing a membership may be admitted
    # against. A caller's dictionary is compared to it, never the reverse.
    # ONE SNAPSHOT, so the assignment, the offer and the journal cannot be
    # read from three different instants.
    with control.snapshot():
        claimed = assignment_of(control, execution_attempt_id)
        offers = claimed_offers_for(control, execution_attempt_id)
        configured = control.operation_record(
            "attempt.record:" + execution_attempt_id)
    fixed = {"work_ref": {"authority_uuid": claimed["authority_uuid"],
                          "work_id": claimed["work_id"]},
             "participant": claimed["participant"],
             "generation": claimed["generation"]}
    offer = _settled_offer(offers, execution_attempt_id)
    recorded = _configured_attempt(configured, execution_attempt_id)
    if held != fixed:
        parts = "; ".join(
            f"{member} {name_value(held.get(member))} where the claim says "
            f"{name_value(fixed[member])}"
            for member in ("work_ref", "participant", "generation")
            if held.get(member) != fixed[member])
        _refuse(f"this admission presents {parts} for execution "
                f"{name_value(execution_attempt_id)}; a membership is "
                f"admitted against the claim its own owner recorded")
    # AN APPLY BRINGS ITS GRANT AND ITS AUTHORIZATION, and a preparation
    # brings neither: a preparation writes no target, so a grant over one
    # would be capability it has no use for.
    if phase == "apply":
        if coordinator is None or authorization is None or grant is None:
            absent = sorted(
                name for name, given in (("coordinator", coordinator),
                                         ("authorization", authorization),
                                         ("grant", grant)) if given is None)
            _refuse(f"an apply is admitted with the coordinator, the "
                    f"authorization owner and the grant it will run under; "
                    f"this admission of {name_value(execution_attempt_id)} "
                    f"carries no {', '.join(absent)}")
        boundaries.capability(getattr(authorization, "authorized", None),
                              "the authorization owner")
        held_grant = _owned_grant(grant)
        # THE CONTENT THE CANDIDATE MUST BE APPROVED OVER, read before the
        # identity is composed because the identity carries what the owner
        # answers about it. This read is DIAGNOSTIC: the authoritative one is
        # inside the transaction below, and a preparation whose collected
        # content changed between them refuses there rather than here.
        preparing = _row(store._connection,
                         "SELECT * FROM integration_capacity_members "
                         "WHERE orchestration_id = ? AND phase = 'prepare'",
                         (orchestration_id,))
        # AND WHEN THERE IS NOTHING TO BE AUTHORIZED OVER, THE GATE BELOW
        # SAYS SO IN ITS OWN WORDS. Measured, step 154: refusing here with a
        # second sentence for the same rule pre-empted the apply gate and left
        # two spellings of "an apply follows a preparation that ended
        # successfully" in one owner. This one states the same rule.
        if preparing is None:
            _refuse(f"integration capacity {name_value(orchestration_id)} "
                    f"plans no preparation; an apply imports content a "
                    f"preparation produced")
        if preparing["state"] != "ended" \
                or preparing["outcome"] != "succeeded":
            _refuse(f"preparation "
                    f"{name_value(preparing['execution_attempt_id'])} is "
                    f"{name_value(preparing['state'])}"
                    f"/{name_value(preparing['outcome'])}; an apply follows a "
                    f"preparation that ended successfully")
        if preparing["collected_digest"] is None:
            _refuse(f"preparation "
                    f"{name_value(preparing['execution_attempt_id'])} "
                    f"collected no content; an apply imports what a "
                    f"preparation produced and there is none")
        approved = _approved_candidate(authorization, held_grant,
                                       preparing["collected_digest"],
                                       orchestration_id)
    elif coordinator is not None or authorization is not None \
            or grant is not None:
        _refuse(f"a preparation is admitted without a grant or an "
                f"authorization; it writes no target, and capability it has "
                f"no use for is capability nobody should hold")
    else:
        held_grant, approved = None, None
    operation_id = "integration-capacity.admit:" + execution_attempt_id
    signature = job_signature(
        "integration-capacity.admit",
        {"orchestration_id": orchestration_id, "phase": phase,
         "execution_attempt_id": execution_attempt_id,
         "assignment": dict(held),
         # THE GRANT *AND* THE AUTHORIZED CANDIDATE RIDE THE SIGNATURE.
         # Review 2026-09-14T00:55:37Z: I claimed both and signed only the
         # grant, so an exact retry naming another approved candidate replayed
         # the first answer WITHOUT ASKING THE OWNER at all -- and the journal
         # held no record of which candidate had been approved. An operation
         # identity that ignores an operand is not an identity, and this is
         # the second time in this Work that the operand it ignored was the
         # one a reviewer had just asked for.
         "grant": held_grant,
         # AND THE CONTENT THE CANDIDATE WAS APPROVED OVER. Review
         # 2026-09-14T01:03:32Z [P2]: the identity carried the candidate and
         # not the content, so a retry after the preparation's collected
         # digest changed asked the owner about the NEW content and then
         # replayed the ORIGINAL admission -- `transact` answers a committed
         # identity without running the action, so the in-transaction
         # comparison never ran. What an authorization is ABOUT is part of
         # what makes this act this act.
         "authorized": None if approved is None
         else {"derived_proposal_id": approved["derived_proposal_id"],
               "derived_result_id": approved["derived_result_id"],
               "derived_result_digest": approved["derived_result_digest"],
               "content_digest": preparing["collected_digest"]}})

    def perform(connection):
        root = _row(connection,
                    "SELECT * FROM integration_capacity_roots "
                    "WHERE orchestration_id = ?", (orchestration_id,))
        if root is None:
            _refuse(f"no integration capacity root "
                    f"{name_value(orchestration_id)} is registered")
        if root["lifecycle"] != "open":
            _refuse(f"integration capacity {name_value(orchestration_id)} is "
                    f"{name_value(root['lifecycle'])}; admission is closed")
        # THE RESERVATION IS STILL HELD. Review [P1]: serial occupancy alone
        # let a root whose allocation had been quarantined go on admitting
        # executions -- capacity that is `recovery-required` is exactly the
        # capacity nothing new may run under.
        allocation = allocation_of(store, root["root_assignment_id"])
        if allocation is None or allocation["allocation_state"] != "reserved":
            _refuse(f"the reservation behind "
                    f"{name_value(orchestration_id)} is "
                    f"{name_value((allocation or {}).get('allocation_state'))}"
                    f"; an execution is admitted only under held capacity")
        member = _row(connection,
                      "SELECT * FROM integration_capacity_members "
                      "WHERE execution_attempt_id = ?",
                      (execution_attempt_id,))
        if member is None or member["orchestration_id"] != orchestration_id:
            _refuse(f"execution {name_value(execution_attempt_id)} is not a "
                    f"planned member of {name_value(orchestration_id)}")
        if member["phase"] != phase:
            _refuse(f"execution {name_value(execution_attempt_id)} is planned "
                    f"as {name_value(member['phase'])} and this admission "
                    f"names {name_value(phase)}")
        if member["state"] != "planned":
            _refuse(f"execution {name_value(execution_attempt_id)} is "
                    f"{name_value(member['state'])}; only a planned "
                    f"membership is admitted")
        if held["participant"] != member["participant"]:
            _refuse(f"execution {name_value(execution_attempt_id)} is planned "
                    f"for {name_value(member['participant'])} and its claim "
                    f"names {name_value(held['participant'])}")
        # AND THE WORK THE CLAIM IS ON IS THE WORK THAT WAS PLANNED. A phase
        # planned against one execution Work and claimed on another is two
        # different pieces of work wearing one membership.
        if held["work_ref"]["work_id"] != member["execution_work_id"]:
            _refuse(f"execution {name_value(execution_attempt_id)} is planned "
                    f"on Work {name_value(member['execution_work_id'])} and "
                    f"its claim is on "
                    f"{name_value(held['work_ref']['work_id'])}")
        if held["work_ref"]["authority_uuid"] != root["authority_uuid"]:
            _refuse(f"execution {name_value(execution_attempt_id)} claimed "
                    f"under Authority "
                    f"{name_value(held['work_ref']['authority_uuid'])} and "
                    f"this root is "
                    f"{name_value(root['authority_uuid'])}")
        # THE OFFER THE CLAIM SETTLED IS THE OFFER THAT WAS PLANNED, and it is
        # on the same Work and generation the claim fixed. Review
        # 2026-09-13T17:33:59Z: a plan naming an offer nobody issued was
        # admitted, because nothing compared the plan's offer to the one the
        # claim actually settled.
        if offer["offer_id"] != member["execution_offer_id"]:
            _refuse(f"execution {name_value(execution_attempt_id)} is planned "
                    f"on offer {name_value(member['execution_offer_id'])} and "
                    f"its claim settled {name_value(offer['offer_id'])}")
        # AND THE COMPLETE IDENTITY, not two members of it. Review
        # 2026-09-13T17:38:55Z [P2]: Work and generation were compared and the
        # Authority and the participant were not -- and an offer settled for
        # another actor, or under another Authority, is another claim.
        settled = {"work_id": offer["work_id"],
                   "authority_uuid": offer["authority_uuid"],
                   "participant": offer["participant"],
                   "generation": offer["claim_generation"]}
        fixed_identity = {"work_id": held["work_ref"]["work_id"],
                          "authority_uuid": held["work_ref"]["authority_uuid"],
                          "participant": held["participant"],
                          "generation": held["generation"]}
        if settled != fixed_identity:
            parts = "; ".join(
                f"{member} {name_value(settled[member])} where the claim says "
                f"{name_value(fixed_identity[member])}"
                for member in sorted(fixed_identity)
                if settled[member] != fixed_identity[member])
            _refuse(f"the offer {name_value(offer['offer_id'])} settled "
                    f"{parts}; an offer and the claim it settled are one "
                    f"identity")
        # AND THE CONFIGURED DIGESTS AGREE ACROSS ALL THREE. The plan says what
        # this phase was meant to run; the offer says what was claimed; the
        # attempt record says what the manager configured. Two of three
        # agreeing is not agreement.
        for name in ("profile_digest", "input_digest"):
            planned, settled = member[name], offer[name]
            written = recorded.get(name)
            if not (planned == settled == written):
                _refuse(f"execution {name_value(execution_attempt_id)} is "
                        f"planned with {name} {name_value(planned)}, claimed "
                        f"an offer carrying {name_value(settled)} and was "
                        f"recorded with {name_value(written)}")
        # AND APPLY FOLLOWS A PREPARATION THAT SUCCEEDED. Review [P1]: the
        # first form let `apply` be the FIRST admission, and let it follow a
        # failed preparation -- neither of which has the prepared content an
        # apply exists to import. The preparation's own ending is the gate.
        by_phase = {one["phase"]: one for one in _members(connection,
                                                          orchestration_id)}
        if phase == "apply":
            preparation = by_phase.get("prepare")
            if preparation is None:
                _refuse(f"integration capacity {name_value(orchestration_id)} "
                        f"plans no preparation; an apply imports content a "
                        f"preparation produced")
            if preparation["state"] != "ended" \
                    or preparation["outcome"] != "succeeded":
                _refuse(f"preparation "
                        f"{name_value(preparation['execution_attempt_id'])} is "
                        f"{name_value(preparation['state'])}"
                        f"/{name_value(preparation['outcome'])}; an apply "
                        f"follows a preparation that ended successfully")
            # AND IT IMPORTS THE CONTENT THAT PREPARATION ACTUALLY COLLECTED.
            # Review 2026-09-13T17:38:55Z: "a preparation succeeded" is not
            # authorization to apply ANYTHING -- the apply names the content by
            # digest at planning time and the preparation's own ending records
            # what it collected, so the two are compared here. A preparation
            # that ended successfully having collected nothing authorizes no
            # apply at all.
            collected = preparation["collected_digest"]
            if collected is None:
                _refuse(f"preparation "
                        f"{name_value(preparation['execution_attempt_id'])} "
                        f"collected no content; an apply imports what a "
                        f"preparation produced and there is none")
            # THE CONTENT THE OWNER WAS ASKED ABOUT IS THE CONTENT THIS
            # TRANSACTION SEES. The read above was outside the lock; this one
            # is the authoritative one, and a preparation whose collected
            # content moved in between is a different apply.
            if collected != preparing["collected_digest"]:
                _refuse(f"the authorization was asked about "
                        f"{name_value(preparing['collected_digest'])} and "
                        f"this preparation now holds "
                        f"{name_value(collected)}")
        live = [one for one in by_phase.values()
                if one["state"] in LIVE_MEMBER_STATES]
        if live:
            _refuse(f"integration capacity {name_value(orchestration_id)} "
                    f"already holds {name_value(live[0]['phase'])} execution "
                    f"{name_value(live[0]['execution_attempt_id'])}; phases "
                    f"under one reservation are serial")
        # THE PARENT CONTENT IS WRITTEN HERE, FROM THE PREPARATION'S OWN
        # ENDING. Review 2026-09-13T18:02:07Z: the plan predeclared it, so the
        # only value a caller could supply before the preparation ran was one
        # it invented -- and comparing two strings a caller wrote at two times
        # proves the caller consistent, not the content collected. It is
        # derived at the one moment it exists.
        # AND THE GRANT, LAST, IMMEDIATELY BEFORE THE ROW IS WRITTEN. Asking
        # the authorization owner is a call that can change the world; what is
        # proved after it is the only thing true when this commits.
        if phase == "apply":
            _prove_grant(coordinator, held_grant)
        connection.execute(
            "UPDATE integration_capacity_members SET state = 'admitted', "
            "assignment = ?, parent_content_digest = ?, "
            "authorized_proposal_id = ?, authorized_result_id = ?, "
            "authorized_result_digest = ? "
            "WHERE execution_attempt_id = ?",
            (json.dumps(dict(held), sort_keys=True),
             by_phase["prepare"]["collected_digest"] if phase == "apply"
             else None,
             None if approved is None else approved["derived_proposal_id"],
             None if approved is None else approved["derived_result_id"],
             None if approved is None else approved["derived_result_digest"],
             execution_attempt_id))
        return integration_capacity_of(store, orchestration_id)

    return store.transact(operation_id, "integration-capacity.admit",
                          signature, perform)


def _resolved_exclusion(control, port, exclusion, member):
    """The owner's own proof that this member no longer uses the capacity.

    REVIEW 2026-09-13T17:38:55Z: the ending took a free TEXT `evidence`, so the
    sentence "host verification produced no status" excluded an execution from
    a reservation. A settlement is a claim about the WORLD, and the only
    honest source for it is the owner that watches the world -- so the caller
    NAMES which proof applies and this resolves it, member by member, against
    the assignment admission fixed. Neither name can be asserted.

    THE TWO ARE NOT INTERCHANGEABLE, which is exactly why they are separate
    names. `fenced-before-start` is about an execution that never ran and has
    no runtime to destroy; `runtime-destroyed` is about one that did and whose
    runtime was positively observed gone. Reading either as the other is the
    fabricated quiescence this Work forbids.
    """
    attempt_id = member["execution_attempt_id"]
    admitted = json.loads(member["assignment"])
    if exclusion == "fenced-before-start":
        if port is None:
            _refuse(f"a {name_value(exclusion)} ending is proved at the "
                    f"Authority and no session was given; capacity stays held")
        proof = unstarted_cancellation_of(control, port, attempt_id)
        if proof["attempt_id"] != attempt_id \
                or proof["assignment"] != admitted:
            _refuse(f"the fenced-before-start proof names attempt "
                    f"{name_value(proof['attempt_id'])} and assignment "
                    f"{name_value(proof['assignment'])}; this membership was "
                    f"admitted for {name_value(attempt_id)} and "
                    f"{name_value(admitted)}")
        return dict(proof)
    # `runtime-destroyed`, and DESTROYED is the only answer that ends it.
    # `quiescent` is a runtime that stopped executing and still exists, and
    # `uncertain` is the manager saying it does not know -- neither excludes
    # anything, and both are why `recovery-required` exists.
    with control.snapshot():
        runtime = attempt_runtime_of(control, attempt_id)
    if runtime is None:
        _refuse(f"the Worker Manager has no attempt "
                f"{name_value(attempt_id)}; there is no runtime fact to end "
                f"this membership with")
    if runtime["execution_runtime"] != "destroyed":
        _refuse(f"attempt {name_value(attempt_id)} execution is "
                f"{name_value(runtime['execution_runtime'])}; a membership is "
                f"excluded on a runtime positively observed destroyed, and "
                f"anything else holds the capacity")
    if runtime["assignment"] != admitted:
        _refuse(f"attempt {name_value(attempt_id)} is fixed to "
                f"{name_value(runtime['assignment'])} and this membership was "
                f"admitted for {name_value(admitted)}")
    return {"state": exclusion, "attempt_id": attempt_id,
            "assignment": runtime["assignment"],
            "execution_runtime": runtime["execution_runtime"],
            "runtime_id": runtime["runtime_id"],
            "cleanup": runtime["cleanup"]}


def _collected_content(control, member, outcome):
    """What this execution actually collected, ASKED OF ITS OWNER.

    REVIEW 2026-09-13T18:02:07Z [P1]: the caller passed a `collected_digest`,
    it was checked for being nonempty text, and it became the successful
    preparation's content -- with nothing frozen, nothing collected and
    `frozen_output_of` answering None both before and after. A digest a caller
    wrote is not a report; the apply that later imported it was importing a
    string.

    THE THREE ANSWERS ARE KEPT APART, which is condition 4's own distinction:

      a COLLECTED report -- a frozen output at the collected disposition,
        whose manifest digest IS the content an apply may import;
      a report that was collected and says something else -- any other
        disposition, which is an execution that answered `unable`,
        `plan-rejected` or `cancelled` and produced no importable content;
      NO REPORT AT ALL -- absence, which is its own answer and is never read
        as either of the other two.

    EXCLUSION AND OUTPUT SUCCESS REMAIN SEPARATE FACTS. A destroyed runtime
    says the capacity is free and says nothing whatever about what was
    collected, which is why this is resolved from a different owner than the
    exclusion is.
    """
    attempt_id = member["execution_attempt_id"]
    frozen = frozen_output_of(control, attempt_id)
    if outcome != "succeeded":
        # A FAILED EXECUTION CONTRIBUTES NO CONTENT, whatever it froze. What it
        # froze is retained by its own owner and is not this membership's
        # account of importable content.
        return None
    if member["phase"] != "prepare":
        return None
    if frozen is None:
        _refuse(f"preparation {name_value(attempt_id)} ended successfully and "
                f"its manager has no frozen output; no report was collected, "
                f"and absence is not content an apply may import")
    if frozen["disposition"] != COLLECTED_DISPOSITION:
        _refuse(f"preparation {name_value(attempt_id)} collected a report at "
                f"disposition {name_value(frozen['disposition'])}; only "
                f"{name_value(COLLECTED_DISPOSITION)} is a collected result, "
                f"and an execution that answered otherwise produced no "
                f"importable content")
    if frozen["attempt_id"] != attempt_id:
        _refuse(f"the frozen output read for {name_value(attempt_id)} names "
                f"{name_value(frozen['attempt_id'])}")
    # AND THE INTAKE THAT ACTUALLY TOOK IT INTO CUSTODY. Slice2: a freeze says
    # the writer stopped; it says nothing about whether the bytes were
    # collected, and an apply reads from custody rather than from a tree that
    # once existed. FROZEN-BUT-UNCOLLECTED IS NOT IMPORTABLE CONTENT.
    receipt = intake_receipt_of(control, attempt_id)
    if receipt is None:
        _refuse(f"preparation {name_value(attempt_id)} froze its output and "
                f"this manager holds no intake for it; a freeze is a receipt "
                f"over a tree that stopped changing, not a statement that "
                f"anything was taken into custody")
    if receipt["custody"] != ACCEPTED_CUSTODY:
        _refuse(f"preparation {name_value(attempt_id)} was taken into custody "
                f"{name_value(receipt['custody'])}; content collected and "
                f"deliberately held aside is not content an apply may import, "
                f"and it is not absence either")
    # THE TWO OWNERS MUST BE TALKING ABOUT ONE EXECUTION AND ONE RESULT. A
    # receipt naming another attempt, another result or another manifest is a
    # receipt about something else however accepted it is.
    for name in ("attempt_id", "result_id", "manifest_digest"):
        if receipt[name] != frozen[name]:
            _refuse(f"the intake receipt for {name_value(attempt_id)} names "
                    f"{name} {name_value(receipt[name])} and its frozen "
                    f"output names {name_value(frozen[name])}")
    # AND THE CUSTODY IS THE ONE THIS MEMBERSHIP'S ASSIGNMENT FIXED.
    admitted = json.loads(member["assignment"])
    if receipt["assignment"] != admitted:
        _refuse(f"the intake receipt for {name_value(attempt_id)} is fixed to "
                f"{name_value(receipt['assignment'])} and this membership was "
                f"admitted for {name_value(admitted)}")
    # THE DECLARED ARTIFACTS ARE RETAINED WITH THEIR MEASURED IDENTITY, so a
    # later phase names content by digest and length rather than by a path.
    held = [{"artifact_id": one["artifact_id"],
             "content_digest": one["content_digest"], "bytes": one["bytes"]}
            for one in receipt["artifacts"]]
    if not held:
        _refuse(f"preparation {name_value(attempt_id)} was accepted into "
                f"custody with no artifact at all; an apply imports measured "
                f"content and there is none to name")
    return {"attempt_id": frozen["attempt_id"],
            "result_id": frozen["result_id"],
            "disposition": frozen["disposition"],
            "manifest_digest": frozen["manifest_digest"],
            "freeze_operation_id": frozen["freeze_operation_id"],
            "custody": receipt["custody"],
            # THE INTAKE ACT ITSELF, so a later reader can ask the journal
            # which act took this content into custody rather than trusting
            # the word. The receipt document carries `operation`; there is no
            # `receipt_digest` member, and inventing one here would have been
            # a second spelling of somebody else's contract.
            "intake_operation": receipt["operation"],
            "artifacts": sorted(held, key=lambda one: one["artifact_id"])}


def end_integration_execution(store, control, *, execution_attempt_id,
                              outcome, exclusion, port=None):
    """End ONE member on its owner's resolved evidence, and say what it did.

    THE OUTCOME AND THE EXCLUSION ARE DIFFERENT FACTS. `failed` is an ending
    like `succeeded` is; neither says anything about a target, a receipt or a
    Work, and a capacity settlement is never a statement that something
    succeeded. The exclusion says the capacity is free; the outcome says what
    the execution did with it. Neither is read off the other.

    AND WHAT WAS COLLECTED IS A THIRD FACT, resolved from a THIRD owner. It is
    not an operand: a successful preparation's content is whatever its frozen
    output actually carries, and `_collected_content` asks the Worker
    Manager's own reader rather than taking a caller's word for it.

    UNCERTAINTY DOES NOT REACH HERE AT ALL. It is `require_integration_recovery`,
    which keeps the member live and the capacity held; this operation is how
    that uncertainty is RECONCILED, by the same owner proof an ordinary ending
    needs.
    """
    boundaries.identity(execution_attempt_id, "an execution attempt id")
    if outcome not in OUTCOMES:
        _refuse(f"an execution outcome is one of {', '.join(OUTCOMES)}; this "
                f"is {name_value(outcome)}")
    if exclusion not in EXCLUSIONS:
        _refuse(f"an exclusion proof is one of {', '.join(EXCLUSIONS)}; this "
                f"is {name_value(exclusion)}")
    # AN EXECUTION THAT NEVER STARTED DID NOT SUCCEED. The two facts are
    # separate and they are not independent: this pair is a contradiction, and
    # accepting it would let a fence stand in for a result.
    if exclusion == "fenced-before-start" and outcome == "succeeded":
        _refuse(f"execution {name_value(execution_attempt_id)} is ended as "
                f"{name_value(outcome)} on a proof that it never started; a "
                f"fence is not a result")
    operation_id = "integration-capacity.end:" + execution_attempt_id
    signature = job_signature(
        "integration-capacity.end",
        {"execution_attempt_id": execution_attempt_id, "outcome": outcome,
         "exclusion": exclusion})

    def perform(connection):
        member = _row(connection,
                      "SELECT * FROM integration_capacity_members "
                      "WHERE execution_attempt_id = ?",
                      (execution_attempt_id,))
        if member is None:
            _refuse(f"execution {name_value(execution_attempt_id)} is not a "
                    f"registered membership")
        if member["state"] == "planned":
            _refuse(f"execution {name_value(execution_attempt_id)} was never "
                    f"admitted; a plan that did not run is cancelled with its "
                    f"root rather than ended as an execution")
        # AND A CANCELLED PLAN IS NOT SETTLED EITHER. Review
        # 2026-09-13T17:38:55Z: `cancelled` fell through both guards and was
        # UPDATED to `ended` carrying an outcome -- which would have turned
        # "this never happened" into "this failed" at exactly the moment the
        # two are hardest to tell apart.
        if member["state"] == "cancelled":
            _refuse(f"execution {name_value(execution_attempt_id)} was "
                    f"cancelled before it was ever admitted; a plan that "
                    f"never ran has no outcome to record")
        if member["state"] == "ended":
            _refuse(f"execution {name_value(execution_attempt_id)} already "
                    f"ended {name_value(member['outcome'])}")
        collected = _collected_content(control, member, outcome)
        proof = _resolved_exclusion(control, port, exclusion, member)
        connection.execute(
            "UPDATE integration_capacity_members SET state = 'ended', "
            "outcome = ?, exclusion = ?, collected_digest = ?, "
            "collected_report = ?, ending_evidence = ?, "
            "ended_operation_id = ? WHERE execution_attempt_id = ?",
            (outcome, exclusion,
             None if collected is None else collected["manifest_digest"],
             None if collected is None else json.dumps(collected,
                                                       sort_keys=True),
             json.dumps(proof, sort_keys=True), operation_id,
             execution_attempt_id))
        return integration_capacity_of(store, member["orchestration_id"])

    return store.transact(operation_id, "integration-capacity.end",
                          signature, perform)


def require_integration_recovery(store, *, execution_attempt_id, reason):
    """Move an admitted member to `recovery-required`: uncertainty HOLDS.

    THIS IS NOT AN ENDING AND IT CARRIES NO OUTCOME. The member stays live, the
    root stays occupied and the reservation stays unreleasable -- because the
    honest answer to "is anything still running under this capacity" is "I do
    not know", and the conservative reading of that is that something is.

    IT IS LEFT ONLY THROUGH `end_integration_execution`, whose proof is
    resolved from the owner. A reason recorded here is why the doubt was
    entered; it is never the evidence that resolves it.
    """
    boundaries.identity(execution_attempt_id, "an execution attempt id")
    boundaries.text(reason, "a recovery reason")
    operation_id = "integration-capacity.recovery:" + execution_attempt_id
    signature = job_signature(
        "integration-capacity.recovery",
        {"execution_attempt_id": execution_attempt_id, "reason": reason})

    def perform(connection):
        member = _row(connection,
                      "SELECT * FROM integration_capacity_members "
                      "WHERE execution_attempt_id = ?",
                      (execution_attempt_id,))
        if member is None:
            _refuse(f"execution {name_value(execution_attempt_id)} is not a "
                    f"registered membership")
        if member["state"] != "admitted":
            _refuse(f"execution {name_value(execution_attempt_id)} is "
                    f"{name_value(member['state'])}; only an admitted "
                    f"execution can become uncertain")
        connection.execute(
            "UPDATE integration_capacity_members SET "
            "state = 'recovery-required', recovery_reason = ? "
            "WHERE execution_attempt_id = ?",
            (reason, execution_attempt_id))
        return integration_capacity_of(store, member["orchestration_id"])

    return store.transact(operation_id, "integration-capacity.recovery",
                          signature, perform)


def begin_integration_ending(store, *, orchestration_id, reason):
    """Close admission, and cancel the phases that never ran.

    ONE ACT, so a phase cannot be admitted into a root that is ending. It
    cancels PLANNED memberships only: an admitted one is ended by its own
    evidence, and closing admission is not a claim that anything stopped.
    """
    boundaries.identity(orchestration_id, "an orchestration id")
    boundaries.text(reason, "an ending reason")
    operation_id = "integration-capacity.ending:" + orchestration_id
    signature = job_signature(
        "integration-capacity.ending",
        {"orchestration_id": orchestration_id, "reason": reason})

    def perform(connection):
        root = _row(connection,
                    "SELECT * FROM integration_capacity_roots "
                    "WHERE orchestration_id = ?", (orchestration_id,))
        if root is None:
            _refuse(f"no integration capacity root "
                    f"{name_value(orchestration_id)} is registered")
        if root["lifecycle"] == "ended":
            _refuse(f"integration capacity {name_value(orchestration_id)} has "
                    f"already ended")
        connection.execute(
            "UPDATE integration_capacity_members SET state = 'cancelled', "
            "ending_evidence = ?, ended_operation_id = ? "
            "WHERE orchestration_id = ? AND state = 'planned'",
            (f"cancelled before admission: {reason}", operation_id,
             orchestration_id))
        connection.execute(
            "UPDATE integration_capacity_roots SET lifecycle = 'ending', "
            "ending_operation_id = ? WHERE orchestration_id = ?",
            (operation_id, orchestration_id))
        return integration_capacity_of(store, orchestration_id)

    return store.transact(operation_id, "integration-capacity.ending",
                          signature, perform)


def releasable(connection, assignment_id):
    """Why this registered root may not release its capacity yet, or None.

    THE SCHEDULER'S OWN QUESTION, answered inside its release transaction. A
    root that is still open, or that holds a membership which has not ended,
    is capacity somebody may still be executing under -- and a completion
    observed for the parent stage says nothing about that.
    """
    root = _row(connection,
                "SELECT * FROM integration_capacity_roots "
                "WHERE root_assignment_id = ?", (assignment_id,))
    if root is None:
        return None
    if root["lifecycle"] == "open":
        return (f"integration capacity "
                f"{name_value(root['orchestration_id'])} is still open; "
                f"admission is closed before its capacity is released")
    unfinished = [one for one in _members(connection,
                                          root["orchestration_id"])
                  if one["state"] not in ("ended", "cancelled")]
    if unfinished:
        return (f"integration capacity "
                f"{name_value(root['orchestration_id'])} holds "
                f"{name_value(unfinished[0]['phase'])} execution "
                f"{name_value(unfinished[0]['execution_attempt_id'])} in "
                f"{name_value(unfinished[0]['state'])}; every execution using "
                f"a reservation is proved excluded before it is released")
    return None


def mark_root_ended(connection, assignment_id):
    """Record that a releasable root's capacity has now been released.

    Called from inside the scheduler's own release transaction, so the root's
    lifecycle and the allocation's state move together or not at all.
    """
    connection.execute(
        "UPDATE integration_capacity_roots SET lifecycle = 'ended' "
        "WHERE root_assignment_id = ? AND lifecycle = 'ending'",
        (assignment_id,))
