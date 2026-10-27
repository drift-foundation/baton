"""Creating an ORDINARY JOB from a versioned template. W361912.

DESIGN SCH-1a, owner 2026-10-24. "Ordinary creation MUST NOT require
operator-authored manifests or bespoke launch packets, nor duplicate
admission, uniqueness or recovery in a helper. The Job manager owns validation
and admission of the instantiated workflow through the existing owning APIs.
The CLI requests the operation and reports its result."

WHAT WAS MISSING, AND IT IS NOT THE RESOLVER. W361910 delivered
`templates.resolve`, `templates.owned_resolution` and
`templates.submission_for_admission`, and its acceptance review is explicit
that those are "not an atomic admission, cross-owner recovery protocol or full
workflow execution proof". What this module adds is the operation that spends
a resolution: one manager-owned act that reserves the identity, composes the
Work authorization and the deployment binding through their owners, records
the submission and journals the whole thing replayably.

AND THE OTHER HALF IS THAT NOBODY COULD SUPPLY THE RESOLVER'S OPERANDS.
`templates.resolve` needs a configuration naming each role's
`profile_name`/`profile_digest`, and a source naming the Job's `input_digest`
and `policy_digest`. Those four are not an operator's to know, and the rule
that proves it is `stage_execution._disagreements` -- the scheduler's own
comparison, which decides which configured worker may serve a stage by
checking, per stage, the serving worker's `launch_role` against the stage
kind, its manifest `work_ref.work_id` against the binding's Work, its
`profile_name` and `profile_digest` against the stage's,
`job_input_identity(manifest)` against the Job's `input_digest`, and its
`policy_digest` against the Job's. Every one of those is a fact the DEPLOYMENT
holds about the workers it installed. An operator typing them is configuring
the pool from a Job, and typing one wrong produces a configuration that
validates cleanly and whose stages no worker can ever be selected for -- which
is the failure the pilot actually recorded.

SO THE REQUEST IS INPUT ONLY and the derivation is a port. The caller supplies
the template selection, the task, the two scopes, the acceptance criteria and
the permitted overrides. `derivation` answers what this deployment installed;
this module holds it to the shape `templates.resolve` requires and then asks
the SELECTOR whether the result can actually be served, because a derivation
this module believed and the scheduler would reject is the same defect wearing
a different coat.

THE FULL RESOLUTION DIGEST IS THE IDENTITY OF THE SELECTED INTENT, and that is
W361910's acceptance review speaking: "Task statement, acceptance and work
scope can differ without changing the legacy submission; a submission
signature alone is therefore insufficient to identify that complete selected
intent." So the reservation records `resolution_digest`, a replay is the same
digest, and a second request whose statement, acceptance or work scope differs
refuses as the different creation it is -- even though `submission.submit`
would have replayed it happily.

THE ORDER OF THE CUTS IS THE RECOVERY STORY, and it is `fresh_attempt`'s
order, for `fresh_attempt`'s reasons.

  1. derive the deployment's facts and resolve -- no store is touched
  2. hold the instance, then re-derive and re-resolve inside the guard
  3. CUT A: reserve the identity, the submission name and the resolution
     digest, inside this store's write lock
  4. acquire the holder, so exactly one admission publishes this identity's
     external effects
  5. CUT B: the Work authorization, then the deployment binding. A binding
     with no Job is INERT, so it is the safe half to publish first
  6. ask the selector whether each resolved stage can be served, with the
     binding now published
  7. agree the compatibility generation and take the submission THROUGH
     `templates.submission_for_admission`, which is the accepted consumption
     contract
  8. CUT C: `submission.submit`
  9. mark the intent created and journal the answer

NOTHING OUTSIDE THIS STORE IS TOUCHED BEFORE CUT A. That ordering is
`fresh_attempt`'s own correction carried forward: its first cut authorized the
Work first, so a request differing from a recorded one minted a Work on the
Authority and THEN refused as a collision -- an effect performed for an
operation that was never admitted.

WHAT THIS MODULE DOES NOT OWN. It records no second account of a submission,
an offer, a runtime or a review; `submission.submit` still owns submission
identity and atomicity and `fresh_attempt.admit` still owns retry, both
untouched. It performs no Git operation, opens no container, reads no
credential and takes no review decision. It does not schedule: whether the
created Job then RUNS is the serving loop's, and this module stops at a
recorded, bound, servable Job.
"""

import json
import sqlite3

from ..contracts import ContractRefusal, digest
from ..contracts.errors import name_value, sample_of
from ..worker_manager import boundaries
from . import documents, execution_limits, submission, templates
from .store import job_signature

__all__ = ["ACQUIRE_KIND", "CREATE_KIND", "DERIVATION_MEMBERS",
           "INSTALLED_SOURCE", "INTENT_KIND", "PROFILE_MEMBERS",
           "create_operation_id", "create_template_job", "created_job_of",
           "created_job_rows", "intent_operation_id", "job_id_for",
           "job_task_of", "resolution_of", "submission_id_for"]

INTENT_KIND = "template_job.intend"
ACQUIRE_KIND = "template_job.acquire"
CREATE_KIND = "template_job.create"

# What the deployment's derivation port must answer. CLOSED, because a member
# this module does not resolve is a fact somebody believes is being used.
DERIVATION_MEMBERS = ("work_id", "input_digest", "policy_digest", "profiles")
# W363066: AND THE TWO A SELECTION-AWARE DERIVATION ADDS. A deployment that
# answers them delivers THIS Job's own task; one that does not is serving the
# installed task, which is the behaviour every Job had before this and is
# preserved rather than broken.
TASK_MEMBERS = ("task_document", "input_manifest")
PROFILE_MEMBERS = ("profile_name", "profile_digest")

# The one source a creation may select: the one this instance installed. An
# enum of one says the decision was made rather than skipped --
# `documents.TERMINAL_POLICIES` is the same shape for the same reason -- and a
# second member would be a source-profile decision nobody has made.
INSTALLED_SOURCE = "installed"


def _refuse(message, *, category="integrity", code="schema", durable=False):
    raise ContractRefusal(category, code, message, durable=durable)


def intent_operation_id(job_id):
    return f"{INTENT_KIND}:{job_id}"


def acquire_operation_id(job_id, holder):
    return f"{ACQUIRE_KIND}:{job_id}:{holder}"


def create_operation_id(job_id):
    return f"{CREATE_KIND}:{job_id}"


def job_id_for(task_id):
    """The Job identity a request that states none resolves to.

    DERIVED FROM WHAT THE CALLER DID NAME rather than invented, so an operator
    never has to make up a second name for one task. `fresh_attempt` derives
    its successor the same way and for the same reason.
    """
    return f"job-{boundaries.identity(task_id, 'a task id')}"


def submission_id_for(job_id):
    """`templates.submission_id_for`'s spelling, reached rather than copied."""
    return templates.submission_id_for(job_id)


def create_template_job(store, operations, *, request, derivation,
                        authorization, binding, ownership):
    """Create one ordinary Job from a versioned template, or replay doing so.

    Answers a `template-job.created` document. Every refusal names the fact
    that stopped it and says whether anything was published.

    `operations` is accepted and deliberately UNUSED for any decision: it is
    the manager's canonical-operations object, and a creation issues no offer,
    starts no runtime and takes no claim. It is in the signature because the
    reads this operation performs are the same reads the serving loop's object
    exposes, and a later slice that needs one will not change this surface.
    """
    for port, what in ((derivation, "the deployment derivation port"),
                       (authorization, "the Work authorization port"),
                       (binding, "the deployment binding port"),
                       (ownership, "the instance ownership port")):
        if port is None:
            _refuse(f"an ordinary creation composes four owners and {what} is "
                    f"absent; this operation does not decide an owner's fact "
                    f"for it by assuming one",
                    category="refused", code="precondition")
    _one_instance(store, {"the deployment derivation port": derivation,
                          "the Work authorization port": authorization,
                          "the deployment binding port": binding,
                          "the instance ownership port": ownership})

    # THE REQUEST IS OWNED, AND ITS IDENTITY IS THE CALLER'S INTENT ALONE.
    #
    # Review 2026-10-26T19-22-51Z R2: the first cut resolved against the
    # DERIVATION before it replayed, and keyed the journal signature on the
    # resulting resolution digest -- so an identical caller request repeated
    # after this deployment's own inputs moved was refused as a "different
    # creation" instead of replaying the creation it had already performed.
    # The reviewer's probe completed a creation, changed one derived digest
    # and repeated the same request, and got a refusal.
    #
    # THE TWO FACTS ARE DIFFERENT AND NOW THEY ARE SEPARATE. What the caller
    # asked for is immutable: the template selection, the task, the two
    # scopes, the acceptance criteria and the overrides. What this deployment
    # derives is a fact about the pool at the moment of admission. A replay is
    # keyed on the first; the second is RECORDED as the created Job's
    # provenance and is never compared on replay.
    asked = _asked(request)
    operands = {"job_id": asked["job_id"],
                "submission_id": asked["submission_id"],
                "request_digest": asked["request_digest"]}

    # AND A REPLAY ANSWERS BEFORE THE DEPLOYMENT IS ASKED ANYTHING AT ALL.
    # The earlier claim's own case comment promised this and the code did not
    # deliver it; the derivation is now reached only past this point, so a
    # recorded creation costs the deployment nothing and cannot start refusing
    # later because the pool moved on -- `fresh_attempt.admit`'s rule, and the
    # same stale-check defect it removes.
    try:
        found, value = store.replay(create_operation_id(operands["job_id"]),
                                    job_signature(CREATE_KIND, operands),
                                    kind=CREATE_KIND)
    except ContractRefusal as collision:
        if collision.code != "operation-collision":
            raise
        # AN OPERATION COLLISION HERE IS A CHANGED CALLER INTENT, and the
        # generic sentence does not say so. The operation identity is the Job
        # and the signature carries the digest of the REQUEST, so a second
        # request under this identity whose statement, acceptance contract,
        # selected work scope, template selection or overrides differ
        # collides -- which is exactly the case W361910's acceptance review
        # says a submission signature could not have caught, because the
        # normalized submission is byte-identical for three of those five.
        raise _changed(store, operands) from collision
    if found:
        return value

    with ownership.held() as owner, ownership.invocation(operands["job_id"]):
        # DERIVED AND RESOLVED EXACTLY ONCE, INSIDE THE GUARD. The derivation
        # reads this instance's own configuration, and the one writer that
        # could change it is a manager whose guard this now holds -- so there
        # is nothing composed outside the guard to go stale, and no comparison
        # between two readings for anybody to get wrong. The first cut read it
        # twice and compared them, which is how R2's replay came to depend on
        # a fact the caller never stated.
        derived, resolution = _resolved(asked, derivation)
        held = dict(operands,
                    work_id=resolution["task"]["work_id"],
                    template_version=resolution["template"]["version"],
                    resolution_digest=templates.resolution_digest(resolution))
        return _owned(store, resolution=resolution, operands=held,
                      derived=derived, authorization=authorization,
                      binding=binding, owner=owner)


def _changed(store, operands):
    """The refusal a second, different creation under one identity gets."""
    held = created_job_of(store, operands["job_id"])
    recorded = held["request_digest"] if held is not None else None
    return ContractRefusal(
        "refused", "precondition",
        f"Job {name_value(operands['job_id'])} is already the creation of a "
        f"DIFFERENT request: this store records the request "
        f"{name_value(recorded)} and this one is "
        f"{name_value(operands['request_digest'])}. A caller's intent is the "
        f"task statement, the acceptance criteria, the two scopes, the "
        f"template selection and the overrides -- and the normalized "
        f"submission carries none of the first three, so two requests that "
        f"would submit byte-identical documents are still two creations. "
        f"Create the changed intent under another Job identity; the recorded "
        f"one is untouched", durable=True)


def _owned(store, *, resolution, operands, derived, authorization,
           binding, owner):
    """Everything that happens while this process owns the instance."""
    job_id = operands["job_id"]
    document = resolution["submission"]
    _task_agrees(resolution, derived)

    # -- CUT A: the reservation, before any other owner is mutated.
    _reserved(store, operands, resolution, document, derived)

    # -- AND EXACTLY ONE RUNNER OWNS THIS IDENTITY'S EFFECTS. The reservation
    #    says the identity is spoken for and says nothing about who may act on
    #    it; this compare-and-swap is what a second concurrent caller loses.
    _acquired(store, operands, owner=owner)

    # -- CUT B: the Work authorization, then the binding. Both idempotent, and
    #    the binding is inert until the Job exists.
    authorized = _authorized(authorization, operands)
    bound = _bound(binding, operands, resolution=resolution)

    # -- THE SELECTOR DECIDES SERVABILITY, not this module and not the
    #    derivation port. Asked AFTER the binding is published, because
    #    `servable_workers` compares against the binding -- and asked for
    #    EVERY resolved stage, because a review worker on another Work is the
    #    exact case `_job_workers` was corrected for.
    servable = _servable(binding, resolution, reserved=job_id,
                         task=derived.get("task_document"))

    # -- THE ACCEPTED CONSUMPTION CONTRACT, inside the operation. W361910's
    #    review: "W361912 owns those existing acceptance obligations and must
    #    preserve the generation agreement through its operation rather than
    #    treating a precheck as authority." So the document this submits is
    #    the one that verb answers, and a resolution this build would no
    #    longer produce refuses here with the binding already published and
    #    nothing recorded.
    try:
        taken = templates.submission_for_admission(
            resolution, generation=execution_limits.CURRENT_GENERATION)
    except ContractRefusal as refusal:
        raise _incomplete(f"the resolution this creation composed is no "
                          f"longer consumable: {refusal.message}",
                          reserved=job_id) from refusal

    # -- CUT C: the submission, and the completion that closes the intent.
    try:
        recorded = submission.submit(store, taken)
    except ContractRefusal as refusal:
        if refusal.code == "operation-collision":
            raise ContractRefusal(
                "refused", "precondition",
                f"the submission for this creation collided with an "
                f"operation this store had already settled: "
                f"{refusal.message}. The identity {name_value(job_id)} is "
                f"RESERVED and its binding may already be published; "
                f"repeating this request cannot change an immutable outcome, "
                f"so create the Job under another submission identity") \
                from refusal
        raise _incomplete(f"the submission for this creation was refused: "
                          f"{refusal.message}", reserved=job_id) from refusal
    # THE DERIVATION IN THE ANSWER IS THE ONE THIS CREATION USED, not a third
    # reading of the port. Asking again would record facts the Job was not
    # composed from if anything had moved -- which is the whole class of
    # defect the re-read inside the guard exists to catch.
    return _completed(store, operands, resolution=resolution,
                      derivation=derived, work=authorized,
                      bound=bound, servable=servable, recorded=recorded)


def _incomplete(why, *, reserved):
    """A refusal PAST the reservation, reported as the incomplete act it is.

    `fresh_attempt._incomplete`'s rule: the reservation and whatever the Work
    authorization and the binding already published REMAIN. The creation is
    incomplete rather than undone, and the one way forward is to fix what is
    named and run the same request again.
    """
    return ContractRefusal(
        "refused", "precondition",
        f"{why}. The Job identity {name_value(reserved)} is RESERVED and its "
        f"Work authorization and deployment binding may already be "
        f"published: this creation is INCOMPLETE rather than undone, no "
        f"submission was recorded, and running the same request again "
        f"finishes it once what is named above is repaired")


# -- the request, and what the deployment answers ----------------------------

def _asked(request):
    """The caller's request, owned by the resolver's own contract.

    NOT A SECOND SCHEMA. `templates.resolve` already owns a
    `baton.v12.job-template-request/1` member by member, including the two
    scopes, the acceptance list and the permitted overrides -- so this takes
    exactly that document and adds the one thing a creation needs and a pure
    resolution does not: the request may omit the identities this operation
    derives.

    WHAT IS OMITTED HERE AND SUPPLIED LATER. `work_id` is the DEPLOYMENT's --
    the configured workers hold a Work in their own input manifests and
    `_disagreements` compares against it, so a caller naming one would be
    choosing which installed workers can serve the Job it is creating. The
    `job_id` may be derived from the task id. Everything else is the caller's
    and travels verbatim into the resolution.
    """
    taken = boundaries.document(
        request, "an ordinary Job creation request",
        required=("schema", "task", "source_selection", "scope",
                  "acceptance"),
        optional=("template", "overrides"))
    if taken["schema"] != templates.REQUEST_SCHEMA:
        _refuse(f"an ordinary Job creation request is "
                f"{name_value(templates.REQUEST_SCHEMA)}, the resolver's own "
                f"request contract; this is "
                f"{name_value(taken['schema'])}")
    task = boundaries.document(taken["task"], "a creation request's task",
                               required=("task_id", "statement"),
                               optional=("job_id", "submission_id"))
    boundaries.identity(task["task_id"], "a task id")
    boundaries.text(task["statement"], "a task statement")
    # THE SOURCE SELECTION IS A CHOICE, NOT A DIGEST. A creation names WHICH
    # of this deployment's installed sources it runs against; the digests that
    # selection resolves to are the deployment's to state. An enum of one is
    # how this build says the decision was made rather than skipped --
    # `documents.TERMINAL_POLICIES` is the same shape for the same reason.
    if taken["source_selection"] != INSTALLED_SOURCE:
        _refuse(f"a creation's source selection is one of "
                f"{name_value(INSTALLED_SOURCE)}; this is "
                f"{name_value(taken['source_selection'])}. The input and "
                f"policy digests a Job carries are facts about the workers "
                f"this deployment installed, and a request that could state "
                f"them would be configuring the pool from a Job")
    # THE TWO SHAPES THIS OPERATION NEEDS BEFORE IT CAN COMPOSE A TASK.
    #
    # W363066: a creation composes this Job's own task document from the
    # acceptance criteria and the two scopes, and it has to do that BEFORE
    # `templates.resolve` runs -- the task decides the Job's input identity
    # and the input identity is an operand of the resolution. So this owns
    # their SHAPES here, and reaching into them unvalidated is the R4 defect
    # one Work over: `acceptance: null` left a TypeError and a `scope` missing
    # a member left a KeyError at a surface whose whole job is to refuse.
    #
    # THE RESOLVER STILL OWNS THE SEMANTICS. The path rule, the duplicate
    # refusal, the bounds and the non-empty work scope are
    # `templates._scope` and `templates._acceptance`, reached a few lines
    # later and not restated here. What this owns is only enough to compose.
    acceptance = taken["acceptance"]
    if type(acceptance) is not list or not acceptance \
            or not all(type(one) is str and one for one in acceptance):
        _refuse(f"a creation request's acceptance is a non-empty list of "
                f"criteria; this is {name_value(acceptance)}")
    scope = boundaries.document(taken["scope"],
                                "a creation request's scope",
                                required=("work", "tests"))
    for member in ("work", "tests"):
        if type(scope[member]) is not list \
                or not all(type(one) is str and one for one in scope[member]):
            _refuse(f"a creation request's {member} scope is a list of "
                    f"repository-relative paths; this is "
                    f"{name_value(scope[member])}")
    # THE IDENTITIES ARE DERIVED FROM THE REQUEST ALONE, here, before any
    # owner is asked anything -- which is what lets the replay above be keyed
    # on the caller's intent. `work_id` is NOT among them: it is the
    # deployment's, and a creation that needed it to find its own journal
    # entry would be R2 again.
    job_id = boundaries.identity(
        task["job_id"] if "job_id" in task else job_id_for(task["task_id"]),
        "a Job id")
    submission_id = boundaries.identity(
        task["submission_id"] if "submission_id" in task
        else submission_id_for(job_id), "a submission id")
    return {"request": taken, "task": task, "job_id": job_id,
            "submission_id": submission_id, "acceptance": acceptance,
            "scope": scope,
            # THE IMMUTABLE CALLER INTENT, as one digest over the OWNED
            # request. Owned rather than as-given, so two spellings of one
            # intent -- a different member order, a pretty-printed document --
            # are one creation, which is `documents.owned_submission`'s own
            # reason for returning a normalized document.
            "request_digest": digest(taken)}


def _resolved(asked, derivation, held=None):
    """The resolution, from the caller's request and the deployment's facts.

    THE DERIVATION IS HELD TO A CLOSED SHAPE before it is believed. It is a
    port over another owner's documents, and a port that answered a missing
    profile as `None` would resolve a Job whose stage requests a profile named
    `null` -- which `documents` admits as text and the selector can never
    match.
    """
    task = asked["task"]
    job_id = asked["job_id"]
    # THE SELECTION THE DEPLOYMENT NEEDS BEFORE IT CAN COMPOSE THIS JOB'S OWN
    # TASK. W363066: the task bytes decide the Job's input identity and the
    # input identity is an operand of `templates.resolve`, so a selection that
    # waited for a resolution could never be made. Every member of it is one
    # the request already owns, except the Work -- which is the deployment's
    # own answer, taken from a first derivation that composes no task.
    #
    # THE TEMPLATE VERSION IS RESOLVED THE SAME WAY `templates.resolve`
    # RESOLVES IT -- the request's selection or this build's default -- rather
    # than guessed. `_configuration_for` names no `default_template`, so the
    # resolver reads `templates.DEFAULT_TEMPLATE`, and `template_of` proves
    # the version here so an unknown one refuses before a task is composed.
    version = (asked["request"]["template"]
               if "template" in asked["request"]
               else templates.DEFAULT_TEMPLATE)
    templates.template_of(version)
    # THE WORK IS NOT IN THE SELECTION. It is the deployment's own answer, so
    # the port adds it -- which is what keeps this ONE reading of the
    # configuration rather than two.
    derived = _derived(derivation, selection={
        "job_id": job_id, "statement": task["statement"],
        "acceptance": list(asked["acceptance"]),
        "scope": {"work": list(asked["scope"]["work"]),
                  "tests": list(asked["scope"]["tests"])},
        "template_version": version}) if held is None else held
    request = dict(asked["request"])
    del request["source_selection"]
    request["task"] = {"job_id": boundaries.identity(job_id, "a Job id"),
                       "work_id": derived["work_id"],
                       "statement": task["statement"]}
    # ALWAYS STATED, because the identity was already derived from the request
    # and the resolver must not re-derive a second one.
    request["task"]["submission_id"] = asked["submission_id"]
    request["source"] = {"input_digest": derived["input_digest"],
                         "policy_digest": derived["policy_digest"]}
    return derived, templates.resolve(request, configuration={
        "schema": templates.CONFIGURATION_SCHEMA,
        "profiles": derived["profiles"]})


def _derived(derivation, selection=None):
    answered = (derivation.derived() if selection is None
                else derivation.derived(selection=selection))
    # THE TASK MEMBERS ARE OPTIONAL AND ARE OWNED WHEN PRESENT. A deployment
    # whose derivation does not compose a per-Job task answers four members
    # and its Jobs run the installed task exactly as they did before this
    # Work; one that does answers six, and then the task bytes and the
    # manifest that names them travel together or neither travels.
    taken = boundaries.document(answered,
                                "this deployment's derived Job facts",
                                required=DERIVATION_MEMBERS,
                                optional=TASK_MEMBERS)
    present = [one for one in TASK_MEMBERS if one in taken]
    if present and len(present) != len(TASK_MEMBERS):
        _refuse(f"this deployment derived {', '.join(present)} without "
                f"{', '.join(one for one in TASK_MEMBERS if one not in taken)}"
                f"; a Job's task bytes and the manifest that names them are "
                f"one fact and half of it is a delivery no validator would "
                f"accept",
                category="refused", code="precondition")
    for member in ("work_id", "input_digest", "policy_digest"):
        boundaries.text(taken[member], f"this deployment's derived {member}")
    profiles = boundaries.document(
        taken["profiles"], "this deployment's derived runtime profiles",
        optional=documents.STAGE_KINDS)
    if not profiles:
        _refuse(f"this deployment derived no runtime profile for any stage "
                f"kind; a creation requests the profile its installed "
                f"workers carry, and there is nothing here to request",
                category="refused", code="precondition")
    for kind in profiles:
        one = boundaries.document(profiles[kind],
                                  f"the derived {kind} runtime profile",
                                  required=PROFILE_MEMBERS)
        for member in PROFILE_MEMBERS:
            boundaries.text(one[member], f"a derived {member}")
    if present:
        boundaries.text(taken["task_document"], "a derived task document")
        boundaries.document(taken["input_manifest"],
                            "a derived per-Job input manifest")
    return taken


def _servable(binding, resolution, *, reserved, task=None):
    """Every resolved stage can be served by a worker this deployment holds.

    THE TASK THIS JOB WILL BE DELIVERED IS AN OPERAND, and it has to be.

    W361912, found by driving the real `create` command against a real
    install. A Job created against a deployment that composes a per-Job task
    submits THAT task's Job-scoped input identity -- `_task_agrees` refuses
    the creation if it does not -- and the selector derives a worker's
    compatibility from the document the worker would serve the Job under.
    That document is composed from the Job's task, which the selector reads
    through `job_task_reader` from the `template_jobs` row... which THIS
    operation has not written yet, because the servability question is asked
    before anything is submitted. So every configured worker was judged
    against the INSTALLED identity, disagreed with the submitted one, and the
    creation refused with "this deployment configures no worker that can
    serve the 'implementation', 'review' stage of the Job this request
    creates" -- for a pool that could serve it perfectly well once the row
    existed.

    THE DERIVATION ALREADY HAS THE DOCUMENT, so it is passed rather than
    re-read: the same bytes `_task_agrees` holds the submitted identity to,
    and the same bytes the row will carry. A deployment that composes no
    per-Job task passes `None` and the selector compares the installed
    document exactly as it did before.

    ASKED OF THE SELECTOR, which is `stage_execution.servable_workers` behind
    the port -- not re-derived here. A comparison written in this module would
    be a copy of the scheduler's rule, and the pilot measured what that copy
    costs: a configuration that validated cleanly and whose stages no worker
    could ever be selected for.

    AND ASKED FOR EVERY STAGE. `_job_workers` was corrected for exactly the
    narrower version of this: compatibility derived for the implementation
    kind alone reserved a review worker on another Work, leaving capacity held
    for a stage that could never be served.
    """
    entry = resolution["submission"]["jobs"][0]
    answered = {}
    empty = []
    for stage in entry["stages"]:
        held = binding.serving(entry["job_id"], stage=stage, job=entry,
                               task=task)
        answered[stage["kind"]] = sorted(held or ())
        if not held:
            empty.append(stage["kind"])
    if empty:
        raise _incomplete(
            f"this deployment configures no worker that can serve the "
            f"{sample_of(sorted(empty))} stage of the Job this request "
            f"creates, so nothing would ever run it", reserved=reserved)
    return answered


# -- the other owners --------------------------------------------------------

def _one_instance(store, ports):
    """Every owner answers for the SAME instance, or nothing is attempted.

    `fresh_attempt._one_instance`'s rule and its reason: a caller composed
    the real ports over an unrelated EMPTY control store and the admission
    read its absences as this instance's own history. A port that declares no
    instance is UNBOUND and accepted, which is what lets a unit case compose
    stand-ins that answer for no deployment.
    """
    declared = {}
    for what, port in ports.items():
        named = port.instance() if hasattr(port, "instance") else None
        if named is not None:
            declared[what] = named
    roots = {what: one.get("root") for what, one in declared.items()}
    distinct = sorted({one for one in roots.values() if one is not None})
    if len(distinct) > 1:
        _refuse(f"these owners answer for {len(distinct)} different "
                f"deployments -- {sample_of(distinct)} -- and an ordinary "
                f"creation is composed against one instance: "
                f"{json.dumps(roots, sort_keys=True)}",
                category="refused", code="precondition")
    for what, one in declared.items():
        named = one.get("authority_uuid")
        if named is not None and named != store.authority_uuid:
            _refuse(f"{what} answers for Authority {name_value(named)} and "
                    f"this Job store is bound to "
                    f"{name_value(store.authority_uuid)}; a Job created here "
                    f"derives its episode identities in this store's "
                    f"namespace and nobody else's",
                    category="refused", code="precondition")
    return declared


def _authorized(authorization, operands):
    """The Work this Job runs under, reused when it is open or created once.

    THE WORK IS THE DEPLOYMENT'S DERIVATION and this port's to confirm. The
    configured workers hold a Work in their own input manifests, so a created
    Job runs under that Work or no installed worker can serve it -- which the
    selector is asked about a few lines later. What this does is prove the
    Authority really holds it, through the Authority's own API.
    """
    work_id = operands["work_id"]
    held = authorization.work_of(work_id)
    if held is None:
        created = authorization.create_work(
            work_id, operation_id=f"{CREATE_KIND}.work:{work_id}")
        return {"work_id": work_id, "state": "created",
                "projection": created}
    state = held.get("state") if type(held) is dict else None
    if state is not None and state != "open":
        raise _incomplete(
            f"Work {name_value(work_id)} is {name_value(state)} and an "
            f"ordinary Job is created under an OPEN Work; a closed Work "
            f"cannot take a claim, so nothing would ever run this Job",
            reserved=operands["job_id"])
    return {"work_id": work_id, "state": "reused", "projection": held}


def _bound(binding, operands, *, resolution):
    """This Job's deployment binding, published through its owner.

    IDEMPOTENT AND INERT. `bootstrap.prepare` revalidates the whole deployment
    and refuses to move anything a repeated bootstrap must preserve, and a
    binding for a Job this store does not hold selects nothing -- so this is
    the safe half to publish before the submission.
    """
    job_id = operands["job_id"]
    existing = binding.binding_of(job_id)
    if existing is not None:
        if existing.get("job_work_id") not in (None, operands["work_id"]):
            raise _incomplete(
                f"this deployment already binds Job {name_value(job_id)} to "
                f"Work {name_value(existing.get('job_work_id'))} and this "
                f"creation runs under {name_value(operands['work_id'])}; a "
                f"Job's Work is a fact about the Job",
                reserved=job_id)
        return existing
    # NOTHING IS CAUGHT HERE, which is `fresh_attempt._bound`'s posture and
    # the rule W361910's R4 review stated: unexpected programmer faults stay
    # visible rather than being translated into "your deployment refused".
    # `fresh_attempt_ports.BindingRefusal` is already an operator-facing
    # sentence about this instance and the thing it says is what has to be
    # fixed, so it propagates as itself; what this module adds is the
    # INCOMPLETE account below for the refusals it does decide.
    published = binding.create_binding(
        job_id, work_id=operands["work_id"],
        template_version=operands["template_version"])
    if published is None:
        raise _incomplete(f"this deployment reported no binding for Job "
                          f"{name_value(job_id)} after publishing one",
                          reserved=job_id)
    return published


# -- the three durable cuts in this store ------------------------------------

def _reserved(store, operands, resolution, document, derived):
    """CUT A: the identity, the submission name and the DIGEST, in one lock.

    THE PRIMARY KEY makes two concurrent requests one creation. The recorded
    request plus the recorded resolution digest make a THIRD request carrying
    a different selected intent a refusal rather than a quiet resumption of
    somebody else's Job.

    AND THE DIGEST IS WHY THIS IS NOT JUST A SUBMISSION. W361910's acceptance
    review: the statement, the acceptance contract and the selected work scope
    can all differ while the normalized submission stays byte-identical, so a
    reservation comparing submissions alone would hand the second caller back
    the first one's Job and call it their creation.
    """
    signature = job_signature(INTENT_KIND, _intent_of(operands))
    intended = job_signature("submission.record", document)
    provenance = json.dumps(resolution, sort_keys=True, ensure_ascii=False)
    # THIS JOB'S OWN TASK, OR NULL FOR A DEPLOYMENT THAT COMPOSES NONE. The
    # bytes are stored because the path they were read from is never reopened:
    # a recorded Job runs the task it was created with, and a later
    # configuration change cannot move it. `job_task_of` is the reader the
    # serving composition asks.
    task_document = derived.get("task_document")

    def act(connection):
        # THE ORDINARY JOB TABLE, INSIDE THE SAME LOCK. An identity an
        # ordinary submission or a fresh attempt already holds is not free,
        # and finding that out at `submit` would be finding it out with a
        # Work and a binding already published for it.
        taken = connection.execute(
            "SELECT job_id FROM jobs WHERE job_id = ?",
            (operands["job_id"],)).fetchone()
        if taken is not None:
            _refuse(f"Job {name_value(operands['job_id'])} is already "
                    f"recorded in this store; a creation cannot take an "
                    f"identity that names another pipeline",
                    category="refused", code="precondition", durable=True)
        # THE OTHER RESERVATION RELATION, by BOTH names. R1 made this
        # symmetric; it was already half right here and the submission-name
        # half was a separate query below. One statement, both names.
        retried = connection.execute(
            "SELECT job_id, submission_id FROM fresh_attempts WHERE "
            "job_id = ? OR submission_id = ?",
            (operands["job_id"], operands["submission_id"])).fetchone()
        if retried is not None:
            _refuse(f"{name_value(retried[0])} is RESERVED by a fresh "
                    f"attempt recorded under submission "
                    f"{name_value(retried[1])}; that admission is in "
                    f"progress or incomplete and owns the identity, so a "
                    f"creation taking the name would strand whatever it has "
                    f"already published",
                    category="refused", code="precondition")
        # AND THE SUBMISSION IDENTITY'S OWN HISTORY, in this store's journal
        # as well as its rows. `fresh_attempt._reserved` review R15: an
        # identity can be permanently settled with no `submissions` row at
        # all, and an absent row is not a free name. None of these is durable
        # for THIS operation: the remedy is another submission identity for
        # the same Job, which is the same intent operation id, so sealing
        # them here would make the remedy impossible.
        journalled = connection.execute(
            "SELECT signature, state FROM operations WHERE operation_id = ?",
            (submission.operation_id(operands["submission_id"]),)).fetchone()
        if journalled is not None and journalled[0] != intended:
            named = submission.operation_id(operands["submission_id"])
            _refuse(f"the submission operation {name_value(named)} "
                    f"is already settled in this store's journal as "
                    f"{name_value(journalled[1])} for a DIFFERENT document, "
                    f"so that identity can never record this one. An "
                    f"operation's outcome is immutable and repeating this "
                    f"request will not change it: choose another submission "
                    f"identity. Nothing was reserved and no Work or binding "
                    f"was touched", category="refused", code="precondition")
        recorded = connection.execute(
            "SELECT signature FROM submissions WHERE submission_id = ?",
            (operands["submission_id"],)).fetchone()
        if recorded is not None and recorded[0] != intended:
            _refuse(f"submission {name_value(operands['submission_id'])} is "
                    f"already recorded in this store for a different "
                    f"document; a creation cannot take a submission identity "
                    f"that names another intent",
                    category="refused", code="precondition")
        held = connection.execute(
            "SELECT request, request_digest, state FROM template_jobs "
            "WHERE job_id = ?", (operands["job_id"],)).fetchone()
        if held is not None:
            if json.loads(held[0]) != _intent_of(operands):
                _refuse(f"Job {name_value(operands['job_id'])} is already "
                        f"reserved for a different creation; one identity "
                        f"names one Job and a second intent reusing it would "
                        f"take over the first one's",
                        category="refused", code="precondition", durable=True)
            return _intent(operands, state=held[2])
        try:
            connection.execute(
                "INSERT INTO template_jobs (job_id, work_id, submission_id, "
                "template_version, state, request, request_digest, "
                "resolution_digest, resolution, task_document, "
                "submission_signature, intended_at, created_at, "
                "incarnation) "
                "VALUES (?, ?, ?, ?, 'intended', ?, ?, ?, ?, ?, ?, ?, NULL, "
                "?)",
                (operands["job_id"], operands["work_id"],
                 operands["submission_id"], operands["template_version"],
                 json.dumps(_intent_of(operands), sort_keys=True,
                            ensure_ascii=False),
                 operands["request_digest"],
                 operands["resolution_digest"], provenance, task_document,
                 intended, store._now(), store.incarnation))
        except sqlite3.IntegrityError:
            # THE LOSER OF THE RACE READS WHO WON, inside its own still-open
            # transaction, so the identity it names is the one really there.
            won = connection.execute(
                "SELECT job_id FROM template_jobs WHERE submission_id = ?",
                (operands["submission_id"],)).fetchone()
            _refuse(f"submission "
                    f"{name_value(operands['submission_id'])} is already "
                    f"reserved by the creation of Job "
                    f"{name_value(won[0] if won is not None else None)}; one "
                    f"submission identity names one creation",
                    category="refused", code="precondition", durable=True)
        return _intent(operands, state="intended")

    return store.transact(intent_operation_id(operands["job_id"]),
                          INTENT_KIND, signature, act)


def _acquired(store, operands, *, owner):
    """Take exclusive ownership of THIS creation's external effects.

    `fresh_attempt._acquired`'s compare-and-swap, for its reason: a
    reservation plus a replayable submission does not make the WORK BETWEEN
    them happen once, and two identical concurrent requests both published a
    binding. A holder continues its OWN interrupted work and nobody else's.
    """
    holder = _holder(store, owner)
    signature = job_signature(ACQUIRE_KIND,
                              dict(_intent_of(operands), holder=holder))

    def act(connection):
        changed = connection.execute(
            "UPDATE template_jobs SET holder = ? WHERE job_id = ? AND "
            "(holder IS NULL OR holder = ?)",
            (holder, operands["job_id"], holder)).rowcount
        if changed == 0:
            held = connection.execute(
                "SELECT holder, state FROM template_jobs WHERE job_id = ?",
                (operands["job_id"],)).fetchone()
            _refuse(f"the creation of {name_value(operands['job_id'])} is "
                    f"held by {name_value(held[0] if held else None)} and is "
                    f"{name_value(held[1] if held else None)}; one creation "
                    f"performs this identity's Work authorization, binding "
                    f"and submission, and a second acting beside it would "
                    f"publish them twice. Let that one finish, or re-run "
                    f"under the same manager incarnation to continue its "
                    f"interrupted work",
                    category="refused", code="precondition")
        return {"job_id": operands["job_id"], "holder": holder}

    return store.transact(
        acquire_operation_id(operands["job_id"], holder), ACQUIRE_KIND,
        signature, act)


def _holder(store, owner):
    """`fresh_attempt._holder`'s identity: the guard and the incarnation."""
    named = getattr(owner, "holder", None)
    return f"{store.incarnation}@{named if named else 'no-instance'}"


def _intent_of(operands):
    """The three members that identify one caller's creation.

    THE DERIVED MEMBERS ARE DELIBERATELY ABSENT. `work_id`,
    `template_version` and `resolution_digest` are facts about the pool and
    the build at the moment of admission; including any of them in the
    identity is R2 -- an identical request refused because the deployment
    moved underneath a creation it had already performed.
    """
    return {"job_id": operands["job_id"],
            "submission_id": operands["submission_id"],
            "request_digest": operands["request_digest"]}


def _intent(operands, *, state):
    return {"job_id": operands["job_id"], "work_id": operands["work_id"],
            "submission_id": operands["submission_id"],
            "template_version": operands["template_version"],
            "resolution_digest": operands["resolution_digest"],
            "state": state}


def _completed(store, operands, *, resolution, derivation, work, bound,
               servable, recorded):
    """CUT C: the intent becomes a creation, and the answer is journalled.

    THE WHOLE RESOLUTION TRAVELS IN THE ANSWER, and so does its digest. A
    caller repeating the command is told the same thing the first one was
    told, including which selected intent was created and which deployment
    facts it was derived from -- so "what is this Job" is a question the store
    answers rather than one an operator reconstructs from a submission that
    carries none of it.
    """
    # THE JOURNAL SIGNATURE IS THE CALLER'S INTENT, not the derived facts.
    # `_intent_of` is exactly what the replay compares, so the two have to be
    # the same three members or a completed creation could never replay.
    signature = job_signature(CREATE_KIND, _intent_of(operands))
    # THE RESOLUTION'S MEMBERS TRAVEL FLATTENED, not nested, and that is a
    # structural fact rather than a preference. `contracts.canonical` bounds a
    # document at depth 8; a resolution carrying a normalized submission is
    # already at that bound, so an answer with `resolution` as a member is one
    # `store.transact` refuses to journal. The whole document is kept in the
    # reservation row instead -- `resolution_of` reads it back -- and what is
    # here is every member of it except the submission, whose own identity is
    # `submission_id` and whose bytes `submission_of` holds.
    answer = documents.template_job_created(
        job_id=operands["job_id"], work_id=operands["work_id"],
        submission_id=operands["submission_id"],
        resolution_digest=operands["resolution_digest"],
        template=dict(resolution["template"]),
        task=dict(resolution["task"]), source=dict(resolution["source"]),
        scope={"work": list(resolution["scope"]["work"]),
               "tests": list(resolution["scope"]["tests"])},
        acceptance=list(resolution["acceptance"]),
        overrides={name: dict(value) for name, value
                   in resolution["overrides"].items()},
        rules={name: dict(value)
               for name, value in resolution["rules"].items()},
        execution_limits=resolution["execution_limits"],
        derivation=derivation, work=work, binding=bound,
        stages=list(recorded["stages"]), servable=servable,
        recorded_at=recorded["recorded_at"])

    def act(connection):
        changed = connection.execute(
            "UPDATE template_jobs SET state = 'created', created_at = ? "
            "WHERE job_id = ? AND state = 'intended'",
            (store._now(), operands["job_id"])).rowcount
        if changed == 0:
            held = connection.execute(
                "SELECT state FROM template_jobs WHERE job_id = ?",
                (operands["job_id"],)).fetchone()
            if held is None:
                _refuse(f"the reservation for "
                        f"{name_value(operands['job_id'])} is gone between "
                        f"this operation's own two cuts")
        return answer

    return store.transact(create_operation_id(operands["job_id"]),
                          CREATE_KIND, signature, act)


# -- the owned reads ---------------------------------------------------------

def created_job_rows(store):
    from . import schema

    return [boundaries.row(record, "a persisted template Job",
                           schema.TEMPLATE_JOB_COLUMNS)
            for record in store._connection.execute(
                "SELECT * FROM template_jobs ORDER BY intended_at, job_id"
            ).fetchall()]


def created_job_of(store, job_id):
    """One creation's reservation, or `None` for a Job nobody created here."""
    boundaries.identity(job_id, "a Job id")
    for row in created_job_rows(store):
        if row["job_id"] == job_id:
            return row
    return None


def _task_agrees(resolution, derived):
    """This Job's submitted input identity IS the task it will be delivered.

    W363066. The whole finding is that these two can disagree: a Job whose
    `input_digest` named the installed task while its delivery named the
    requested one, or the reverse, is a Job the selector refuses for every
    stage -- so the agreement is checked HERE, inside the operation, before
    anything is reserved, rather than discovered at reservation time.

    A DEPLOYMENT THAT COMPOSES NO PER-JOB TASK IS NOT A DISAGREEMENT. Its
    Jobs run the installed task, which is what every Job did before this Work
    and is explicitly preserved.
    """
    if "input_manifest" not in derived:
        return
    from ..contracts.manifest import job_input_identity

    named = job_input_identity(derived["input_manifest"],
                               what="a created Job's own input")
    submitted = resolution["submission"]["jobs"][0]["input_digest"]
    if named != submitted:
        _refuse(f"this Job's submitted input identity is "
                f"{name_value(submitted)} and the manifest naming its own "
                f"task identifies as {name_value(named)}; a Job whose "
                f"delivered task and submitted input disagree is one no "
                f"configured worker can serve, and nothing has been reserved")


def job_task_of(store, job_id):
    """THIS Job's own task document, or `None` for one that has no own task.

    The narrow read the serving composition asks, and the reason it is a read
    rather than a remembered value is `job_execution_reader`'s: "a value
    remembered from admission would be a second account of a fact the Job
    owner holds."

    `None` IS AN ORDINARY ANSWER. A Job created before this Work, submitted
    by hand, or created against a deployment that composes no per-Job task has
    no own task, and its delivery is the installed one exactly as before.

    AND IT FOLLOWS THE RETRY LINEAGE, which is W364834.

    A fresh attempt carries the prior Job's specification VERBATIM --
    `_composed`'s own rule: "the input digest, the policy digest, the test
    scope, the terminal policy, the stage kinds, their profiles and their
    execution limits are the operator's selections and are carried
    verbatim". For a template-created Job that submitted input digest IS its
    own task's Job-scoped identity, so a retry that answered `None` here
    would be a Job whose declared identity is its task's and whose delivery
    is the installed one -- which `single_worker._matches` refuses as
    "another bootstrap input", and which the selector refuses one step
    earlier as a Job no configured worker can serve. Measured end to end
    before this existed; see `tests/tools/test_retry_task_lineage.py`.

    THE LINEAGE IS THE PRODUCT'S OWN DURABLE RECORD, not a copy and not an
    inference. `fresh_attempts.prior_job_id` is the retry relation's
    NOT NULL column and the schema's own reason for keeping two relations
    rather than widening one; this read walks it. So a retried Job's task is
    owned by the creation that made it, immutable where that creation wrote
    it, and reachable from every successor -- rather than duplicated into
    each retry's row, which would be a second account of one fact, or
    recovered from the deployment's installed bytes, which a configuration
    change moves.

    BOUNDED AND CYCLE-SAFE. The chain is walked with the identities already
    seen; a store whose rows point in a circle is a refusal rather than a
    loop, because answering a delivery question from a corrupt lineage is
    worse than saying so.
    """
    boundaries.identity(job_id, "a Job id")
    seen = []
    held = job_id
    while True:
        if held in seen:
            _refuse(f"the retry lineage of Job {name_value(job_id)} returns "
                    f"to {name_value(held)}; a Job's task is read from the "
                    f"creation that made it and a circular lineage names no "
                    f"creation", category="integrity", code="schema")
        seen.append(held)
        created = created_job_of(store, held)
        if created is not None:
            return created["task_document"]
        prior = _retried_from(store, held)
        if prior is None:
            return None
        held = prior


def _retried_from(store, job_id):
    """Which Job this one is a fresh attempt at, or `None`.

    READ FROM THE RETRY RELATION ITSELF rather than derived from the
    identity. `fresh_attempt.successor_of` composes a legible name --
    `job-a-retry-2` -- and parsing it back would be this module inventing a
    lineage out of a string an operator may have overridden with
    `--job-id`. The row is the fact.
    """
    held = store._connection.execute(
        "SELECT prior_job_id FROM fresh_attempts WHERE job_id = ?",
        (job_id,)).fetchone()
    return None if held is None else held[0]


def resolution_of(store, job_id):
    """The FULL resolution one created Job was created from.

    OWNED ON THE WAY OUT, through the resolver's own owner, because a row is
    this build's own write and is still receiver input the moment it is read
    back -- a store somebody edited by hand is exactly where an unchecked
    read would hand a consumer a resolution nobody resolved.

    THIS IS THE PROVENANCE HALF. `created_job_of` gives the digest, which
    says WHICH selected intent; this gives the document, which says what that
    intent was -- the statement, the acceptance contract and the selected
    work scope, none of which the submission has anywhere to carry.
    """
    held = created_job_of(store, job_id)
    if held is None:
        return None
    resolution = templates.owned_resolution(json.loads(held["resolution"]))
    found = digest(resolution)
    if found != held["resolution_digest"]:
        _refuse(f"the resolution stored for Job {name_value(job_id)} digests "
                f"to {name_value(found)} and its reservation records "
                f"{name_value(held['resolution_digest'])}; a row and the "
                f"identity it is filed under cannot disagree")
    return resolution
