"""Admitting a FRESH ATTEMPT at a Job whose execution failed. W358969.

DESIGN REC-7, owner 2026-10-23. A routine retry is a supported deterministic
manager operation reached through the CLI -- not a packet somebody writes for
each occurrence. The pilot's own failure is the case: `quickstart-c`'s
implementation stage died on an expired provider credential, nothing had been
spent, and the only way to try again was for an agent to author a bespoke
script that reserved identities, rewrote configuration and checked its own
preconditions. Script-side prechecks are not enforcement: they run outside the
store's lock, they go stale between the check and the effect, and every new
one is a second implementation of a rule the manager already owns.

WHAT A FRESH ATTEMPT IS, AND WHAT IT IS NOT. It is a NEW Job carrying the
PRIOR Job's own submitted specification -- the same input, policy, scope,
terminal policy, stages, dependencies and per-invocation limits -- admitted
with a new identity and linked back to the attempt it replaces. It is not a
restart: `episodes.restart_abandoned_correction` reaches a committed fence, a
restored line and an excluded writer, and an expired credential produces none
of those. It is not a resubmission either: `submission.submit` journals by
submission identity, so the same document replays rather than re-running, and
`_unclaimed` refuses a second submission reusing a live Job's identity. Both
of those are correct and neither is a retry, so this is the operation that was
missing rather than a way around them.

THREE OWNERS, NO CROSS-STORE TRANSACTION. The Jobs are this store's; the Work
authorization is the Authority's; the runtime and the resource are the Worker
Manager's; the Job/worker binding is the deployment configuration's. REC-7 is
explicit that composing them "does not imply a cross-store transaction", so
this operation does not pretend to one. It reserves the fresh identity HERE,
durably, before it touches anything else; it asks each other owner through
that owner's own API; and every cut between them is replayable, with an
explicit HELD outcome naming what is unfinished rather than a silent partial.

THE ORDER OF THE CUTS IS THE RECOVERY STORY.

  1. read the prior Job, its stages and its episodes -- this store alone
  2. require every prior stage SETTLED and at least one of them EXCEPTIONAL
  3. require the host to have CEASED every prior attempt's runtime and
     RETURNED its resource; unknown refuses
  4. CUT A: reserve the fresh identity and write the durable intent
  5. re-ask the host, because a check before a reservation is a check about
     the past; nothing conflicting may be done on a stale answer
  6. CUT B: the Work authorization, reused or created
  7. bind the fresh Job in the deployment configuration, through its owner.
     A binding with no Job is INERT -- nothing selects a worker for a Job the
     store does not hold -- so this is the safe half to publish first
  8. CUT C: record the submission, which is where the Job becomes real
  9. mark the intent admitted

NOTHING OUTSIDE THIS STORE IS TOUCHED BEFORE CUT A, and that ordering is a
correction. The first cut authorized the Work first, so a request that
differed from a recorded one minted a Work on the Authority and THEN refused
as a collision -- an effect performed for an operation that was never
admitted.

A crash anywhere resumes: the intent says which fresh Job was being admitted
and from what, the binding is idempotent, `submit` replays by its own identity
and the completion replays by its own. What cannot happen is two admissions of
one identity, because the reservation is a PRIMARY KEY taken inside this
store's write lock -- nor two successors of one failure, because
`fresh_attempts_one_successor` is a unique index on the prior Job and two
writers meet at it rather than at a read.

A REFUSAL PAST CUT A SAYS SO. The reservation, and whatever the Work
authorization and the binding already published, remain; the attempt is
INCOMPLETE rather than undone, and `_incomplete` names the identity and the
one way forward -- fix what was named and run the same request again.

THE PORTS ANSWER FACTS AND THIS MODULE DECIDES. `exclusion`, `authorization`
and `binding` each wrap one owner's public API; none of them is allowed to
hold a rule. That split is the whole point of REC-7's "script-side prechecks
cannot substitute for manager enforcement": an adapter that decided whether a
runtime had ceased would be the pilot's helper again, wearing this module's
name.
"""

import json
import os
import sqlite3

from ..contracts import ContractRefusal
from ..contracts.errors import name_value, sample_of
from ..worker_manager import boundaries
from . import documents, episodes, projection, submission
from .store import job_signature

__all__ = ["ACQUIRE_KIND", "INTENT_KIND", "ADMIT_KIND", "admit",
           "admit_fresh_attempt",
           "fresh_attempt_of", "fresh_attempt_rows", "successor_of",
           "successors_of"]

INTENT_KIND = "fresh_attempt.intend"
ADMIT_KIND = "fresh_attempt.admit"
ACQUIRE_KIND = "fresh_attempt.acquire"

# WHERE A PRIOR STAGE MAY HAVE STOPPED. `documents.TERMINAL_STAGE_STATES` is
# the manager's own answer to "does this control plane still owe this stage an
# act", which is exactly the question a fresh attempt has to ask first.
_TERMINAL = frozenset(documents.TERMINAL_STAGE_STATES)
# AND THE ONE NON-TERMINAL STATE THAT IS STILL OVER. The pilot's own failure
# is the case: the implementation stage went `exceptional` and the review
# stage it gated stayed `blocked` -- which is not terminal, because a blocked
# stage is ordinarily one whose turn has not come. Here its turn never will,
# because the only gate it names can no longer open. So a blocked stage is
# settled WHEN EVERY GATE IT NAMES IS ITSELF PAST OPENING, and a blocked
# stage waiting on something still running is not.
_NEVER_OPENS = frozenset(("exceptional", "changes-requested"))
# AND WHICH SETTLED STATE MAKES A RETRY MEANINGFUL. `completed` is a Job that
# worked and `changes-requested` is the same-line correction cycle, which has
# its own operation and its own line; neither is a failure to re-attempt.
_FAILED = "exceptional"

# THE HOST STATES THAT MEAN THIS EXECUTION IS OVER. Read from the Worker
# Manager's own axis vocabulary rather than restated as a guess: `destroyed`
# and `quiescent` are cessation, `not-started` is an attempt that never ran,
# and everything else -- including `uncertain` -- is either still happening or
# unknown, which REC-4 says is an actionable state and not a synonym for safe.
_CEASED_RUNTIME = ("not-started", "quiescent", "destroyed")
# AND WHERE ITS RESOURCE ACCOUNTING HAS STOPPED MOVING. `retained` is a
# deliberate hold on evidence and is settled; `pending`, `blocked-on-intake`
# and `failed` are all cleanup this host still owes.
_SETTLED_CLEANUP = ("complete", "retained")

_SUFFIX = "-retry-"


def successor_of(prior_job_id):
    """The fresh Job identity derived from the one being replaced.

    DERIVED SO NOBODY HAS TO INVENT ONE. REC-7's whole complaint is that a
    retry required a model to prepare the run, and "pick a Job id" is the
    first thing such a model was asked to do. A chain reads
    `quickstart-c`, `quickstart-c-retry-2`, `quickstart-c-retry-3` -- the base
    stays legible and the ordinal says how many attempts this specification
    has had.

    IT IS NOT A FREE SLOT SEARCH, deliberately. An identity that skipped to
    the next unused name would make a repeated command admit a SECOND retry
    instead of being told the first one already exists, which is the duplicate
    admission this operation exists to prevent.
    """
    boundaries.identity(prior_job_id, "a Job id")
    base, ordinal = _chain(prior_job_id)
    return f"{base}{_SUFFIX}{ordinal + 1}"


def _chain(job_id):
    """`(base, ordinal)` for a Job id, whether or not it is already a retry."""
    head, found, tail = job_id.rpartition(_SUFFIX)
    if found and tail.isdigit() and not tail.startswith("0"):
        return head, int(tail)
    return job_id, 1


def intent_operation_id(job_id):
    return f"{INTENT_KIND}:{job_id}"


def admit_operation_id(job_id):
    return f"{ADMIT_KIND}:{job_id}"


def acquire_operation_id(job_id, holder):
    """One acquisition per holder, so a holder's own retry replays.

    DERIVED FROM BOTH, because the journal would otherwise make a SECOND
    holder's attempt replay the first one's success -- which is the opposite
    of what the compare-and-swap is for.
    """
    return f"{ACQUIRE_KIND}:{job_id}:{holder}"


def work_operation_id(job_id):
    """The identity the Authority creation is journalled under, if one is made.

    Derived from the FRESH JOB rather than from the Work, because the Work is
    what this operation may be creating and an identity derived from it would
    be the same for two different admissions that happened to choose it.
    """
    return f"{ADMIT_KIND}:work:{job_id}"


def admit(store, operations, *, prior_job_id, exclusion, authorization,
          binding, ownership, job_id=None, work_id=None,
          submission_id=None):
    """Admit one fresh attempt at `prior_job_id`, or replay having done so.

    Answers a `fresh-attempt.admitted` document. Every refusal here names the
    fact that stopped it and leaves this store, the Authority, the host and
    the deployment exactly as they were.
    """
    boundaries.identity(prior_job_id, "a Job id")
    job_id = (successor_of(prior_job_id) if job_id is None
              else boundaries.identity(job_id, "a Job id"))
    submission_id = (f"sub-{job_id}" if submission_id is None
                     else boundaries.identity(submission_id,
                                              "a submission id"))
    for port, what in ((exclusion, "the host exclusion port"),
                       (authorization, "the Work authorization port"),
                       (binding, "the deployment binding port"),
                       (ownership, "the instance ownership port")):
        if port is None:
            raise ContractRefusal(
                "integrity", "schema",
                f"a fresh attempt composes three owners and {what} is "
                f"absent; this operation does not decide an owner's fact for "
                f"it by assuming one")

    # ONE INSTANCE, AGREED BY EVERY OWNER, BEFORE ANYTHING IS READ OR DONE.
    #
    # Review R14: a caller composed these four ports over an unrelated EMPTY
    # control store and the admission read its absences as this instance's
    # own history, because the only check compared an operand with itself.
    # Each port now declares which instance it answers for, from ITS OWN
    # owner's facts, and this refuses before the first read unless they are
    # one instance -- including the Authority this store is bound to, which
    # is a fact the store itself holds rather than one a caller supplies.
    _one_instance(store, {"the host exclusion port": exclusion,
                          "the Work authorization port": authorization,
                          "the deployment binding port": binding,
                          "the instance ownership port": ownership})

    prior = _prior(store, prior_job_id)
    if work_id is None:
        work_id = prior["work_id"]
    else:
        boundaries.text(work_id, "a Work id")
    operands = {"prior_job_id": prior_job_id, "job_id": job_id,
                "work_id": work_id, "submission_id": submission_id}

    # A REPLAY ANSWERS BEFORE ANY OWNER IS ASKED ANYTHING. The whole operation
    # is already recorded, so re-deriving its preconditions would mean a
    # completed admission could start refusing later because the host moved
    # on -- which is precisely the stale-check defect this design removes.
    found, value = store.replay(admit_operation_id(job_id),
                                job_signature(ADMIT_KIND, operands),
                                kind=ADMIT_KIND)
    if found:
        return value

    document = _composed(store, prior, job_id=job_id, work_id=work_id,
                         submission_id=submission_id)

    # -- THE INSTANCE IS HELD FOR THE WHOLE OF THE REST. Review R7: a
    #    coherent read is not an exclusion, and a sentence telling an operator
    #    to stop the serving loop is not one either. `hold_manager_instance`
    #    is the product's own answer -- the guard a manager takes "before it
    #    dispatches work or mutates a managed resource" -- so a serving
    #    manager holding this instance refuses this admission outright, and
    #    two admissions in two processes cannot both act on one instance.
    # AND EXACTLY ONE ADMISSION OF THIS IDENTITY RUNS AT A TIME. Review R8:
    # the holder below is a stable NAME and answers who may resume; this is
    # the lock that answers who is acting right now, and two concurrent calls
    # under one manager incarnation are one of the cases it decides.
    with ownership.held() as owner, ownership.invocation(job_id):
        return _owned(store, operations, prior=prior, operands=operands,
                      document=document, exclusion=exclusion,
                      authorization=authorization, binding=binding,
                      owner=owner)


def _owned(store, operations, *, prior, operands, document, exclusion,
           authorization, binding, owner):
    """Everything that happens while this process owns the instance."""
    job_id = operands["job_id"]
    work_id = operands["work_id"]
    prior_job_id = operands["prior_job_id"]
    settled = _settled(store, operations, prior)
    # THE HOST IS READ WHILE THE INSTANCE IS HELD, which is the difference
    # between an observation and an exclusion: the one writer that could
    # change these answers is the manager whose guard this now holds.
    evidence = _excluded(exclusion, prior["attempt_ids"], when="before")

    # -- CUT A: THE RESERVATION COMES FIRST, BEFORE ANY OTHER OWNER IS
    #    MUTATED. Review R4: the first cut created the Work here and reserved
    #    afterwards, so a request that differed from a recorded one minted a
    #    Work on the Authority and THEN refused as a collision -- an effect
    #    performed on behalf of an operation that was never admitted. Nothing
    #    outside this store is touched until this returns, and what it
    #    returns is the operands this store agreed to.
    _reserved(store, operands, prior, document)

    # -- AND THE EFFECTS ARE OWNED BY EXACTLY ONE RUNNER. Review R5: the
    #    reservation says the identity is spoken for and says nothing about
    #    who may act on it, so a replaying second caller went on to publish a
    #    second binding. This compare-and-swap is what one of them loses.
    _acquired(store, operands, owner=owner)

    # -- re-ask, because cut A took time and a reservation is not a lock on
    #    somebody else's store.
    evidence = _excluded(exclusion, prior["attempt_ids"], when="after",
                         reserved=job_id)

    # -- CUT B: the Work authorization, then the binding, both AFTER the
    #    reservation and both idempotent. The binding is inert until the Job
    #    exists, so it is the safe half to publish first.
    authorized = _authorized(authorization, work_id, job_id,
                             reserved=job_id)
    # W364834: AND THE TASK THIS FRESH JOB WILL BE DELIVERED travels with the
    # servability question. The composed submission carries the prior Job's
    # input digest verbatim, which for a template-created Job is its own
    # task's Job-scoped identity -- so asking without the task compares every
    # configured worker against the INSTALLED document and refuses the retry
    # as unservable by the very pool that served the original. Read from the
    # store rather than remembered: `creation.job_task_of` is the Job owner's
    # own answer and it follows the retry lineage, so a retry of a retry is
    # the same read.
    from . import creation
    bound = _bound(binding, job_id=job_id, prior_job_id=prior_job_id,
                   work_id=work_id, document=document, reserved=job_id,
                   task=creation.job_task_of(store, prior_job_id))

    # -- CUT C: the submission, and the completion that closes the intent.
    #    A refusal HERE is a refusal with effects already published, so it is
    #    reported as the incomplete admission it is rather than as whatever
    #    the submission boundary said on its own.
    try:
        recorded = submission.submit(store, document)
    except ContractRefusal as refusal:
        if refusal.code == "operation-collision":
            # AN IMMUTABLE OUTCOME IS NOT A TRANSIENT ONE. `_incomplete`
            # tells a caller to run the same request again, which is right
            # for everything a correction can clear and wrong for this:
            # the journal's answer will be the same forever. The reservation
            # check above catches this before any effect; reaching it here
            # means the journal moved underneath this admission, so the
            # honest report is what is true rather than a loop.
            raise ContractRefusal(
                "refused", "precondition",
                f"the submission for this fresh attempt collided with an "
                f"operation this store had already settled: "
                f"{refusal.message}. The fresh identity "
                f"{name_value(job_id)} is RESERVED and its binding may "
                f"already be published; repeating this request cannot "
                f"change an immutable outcome, so admit the attempt under "
                f"another submission identity") from refusal
        raise _incomplete(f"the submission for this fresh attempt was "
                          f"refused: {refusal.message}",
                          reserved=job_id) from refusal
    return _completed(store, operands, prior=prior, settled=settled,
                      evidence=evidence, authorized=authorized, bound=bound,
                      recorded=recorded)


# -- what this store alone knows ---------------------------------------------

def _one_instance(store, ports):
    """Every owner answers for the SAME instance, or nothing is attempted.

    A port that declares no instance is UNBOUND and is accepted: the unit
    cases compose stand-ins that answer for no deployment, and refusing them
    would be this rule deciding how a caller must build its ports rather
    than that they agree. What is refused is DISAGREEMENT -- two owners
    naming two deployments -- and an Authority that is not this store's.
    """
    named = {}
    for what, port in ports.items():
        declared = getattr(port, "instance", None)
        held = declared() if callable(declared) else None
        if held is None:
            # REVIEW R17: AN UNDECLARED PORT IS NOT AN EXEMPT ONE. The first
            # cut skipped ports that answered nothing, so a real host port
            # built with no identity was accepted beside three bound ones
            # and an admission read an unrelated empty control store as this
            # instance's own history. A stand-in declares a synthetic
            # instance exactly as a real port declares a real one; being a
            # fixture is not a reason to be trusted without saying what you
            # answer for.
            raise ContractRefusal(
                "refused", "precondition",
                f"{what} does not say which instance it answers for; a "
                f"fresh attempt trusts what its owners report about ONE "
                f"deployment, and a port that names none cannot be checked "
                f"against the others")
        named[what] = held
    roots = {held["root"] for held in named.values()}
    if len(roots) != 1:
        raise ContractRefusal(
            "refused", "precondition",
            f"these owners answer for different deployments: "
            f"{json.dumps({what: held['root'] for what, held in named.items()}, sort_keys=True)}"
            f". A fresh attempt is admitted against one instance, and ports "
            f"composed over two of them would read one deployment's history "
            f"as another's")
    identity = sorted(named.values(), key=lambda held: held["root"])[0]
    # AND THE STORE THIS OPERATION IS WRITING TO IS THAT INSTANCE'S.
    #
    # Review R18: the four declared roots and one Authority uuid agreed, and
    # the JobStore itself was never compared to any of them -- so two real
    # deployments that happen to share an Authority admitted one instance's
    # Job through the other's ports, published the binding in the wrong
    # deployment, and read its empty runtime history as the failed Job's own.
    # Sharing an Authority does not make two stores one instance.
    here = getattr(store, "database", None)
    owned = identity.get("job_store")
    if owned is not None and os.path.realpath(str(here or "")) \
            != os.path.realpath(str(owned)):
        raise ContractRefusal(
            "refused", "precondition",
            f"this Job store is {name_value(here)} and instance "
            f"{identity['root']!r} owns {name_value(owned)}; these owners "
            f"answer for a deployment whose Jobs are not the ones this "
            f"operation would record, and an Authority two instances share "
            f"does not make them one")
    if identity.get("authority_uuid") not in (None, store.authority_uuid):
        raise ContractRefusal(
            "refused", "precondition",
            f"instance {identity['root']!r} is configured for Authority "
            f"{name_value(identity.get('authority_uuid'))} and this Job "
            f"store is bound to {name_value(store.authority_uuid)}; the "
            f"episode identities this admission would read are derived in "
            f"an Authority's namespace, so two of them are two namespaces")
    return identity


def _prior(store, prior_job_id):
    """The Job being replaced, its stages, its episodes and its document.

    THE SUBMITTED DOCUMENT IS THE SPECIFICATION, not the rows. Rebuilding a
    Job entry out of `jobs` and `stages` would silently normalize it -- a /1
    Job would acquire a /2 identity, an absent `execution_limits` member would
    become an empty one -- and "preserve the selected Job specification" means
    the bytes the operator submitted, not an equivalent this build would have
    written.
    """
    held = submission.job_of(store, prior_job_id)
    stages = submission.stages_of(store, prior_job_id)
    if not stages:
        raise ContractRefusal(
            "refused", "precondition",
            f"Job {name_value(prior_job_id)} has no stages; a fresh attempt "
            f"repeats a specification and there is nothing here to repeat")
    recorded = submission.submission_of(store, held["submission_id"])
    if recorded is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"Job {name_value(prior_job_id)} names submission "
            f"{name_value(held['submission_id'])} and this store holds no "
            f"such submission; the specification to repeat is that "
            f"document's")
    # THE PERSISTED DOCUMENT COMES BACK AS THE TEXT IT WAS, because replay is
    # byte-stable and `_persisted_json` hands back exactly what was stored.
    # Decoding it here is this reader's own act rather than a surprise.
    document = json.loads(recorded["document"])
    entry = None
    for one in document["jobs"]:
        if one["job_id"] == prior_job_id:
            entry = one
    if entry is None:
        raise ContractRefusal(
            "integrity", "schema",
            f"submission {name_value(held['submission_id'])} records Job "
            f"{name_value(prior_job_id)} and its document does not carry it")
    works = {stage["work_id"] for stage in stages}
    if len(works) != 1:
        # EVERY STAGE OF ONE JOB SHARES ONE WORK in every configuration this
        # build serves -- `_job_workers` compares a single `job_work_id` from
        # the binding against each stage -- so a Job spread over two would
        # have no single Work for a fresh attempt to inherit. Refused rather
        # than guessed.
        raise ContractRefusal(
            "refused", "precondition",
            f"Job {name_value(prior_job_id)}'s stages name "
            f"{sample_of(sorted(works))}; a fresh attempt inherits one Work "
            f"and this build cannot choose between them")
    attempts = []
    for stage in stages:
        for episode in episodes.episodes_of(store, stage["stage_id"]):
            attempts.append(episode["attempt_id"])
    return {"job_id": prior_job_id, "job": held, "stages": stages,
            "entry": entry, "schema": document["schema"],
            "submission_id": held["submission_id"],
            "work_id": sorted(works)[0], "attempt_ids": sorted(attempts)}


def _incomplete(why, *, reserved):
    """A refusal AFTER the reservation, which says so.

    Review R4: every refusal in this operation used to end "and changes
    nothing", which stopped being true the moment the reservation existed.
    A reserved identity with no Job is a real, recorded, resumable state, and
    an operator told "nothing happened" would go looking for a row that is
    there. So the refusals raised past cut A name the reservation and the one
    way forward: fix what was named and run the SAME request again.
    """
    return ContractRefusal(
        "refused", "precondition",
        f"{why}. The fresh identity {name_value(reserved)} is already "
        f"RESERVED in this store and this attempt is incomplete rather than "
        f"undone: correct what is named above and run the same request "
        f"again, which resumes from the reservation. A different request "
        f"under this identity is refused as the collision it is")


def _settled(store, operations, prior):
    """Every prior stage has stopped, and at least one of them failed.

    THIS IS THE MANAGER'S OWN PROJECTION, not a second opinion about it.
    `stage_states` is what `status` and the serving loop derive from, so a
    fresh attempt cannot disagree with what an operator was just shown.
    """
    held = projection.stage_states(store, operations, prior["stages"])
    states = {stage_id: entry["state"] for stage_id, entry in held.items()}
    live = sorted(stage_id for stage_id, entry in held.items()
                  if not _over(entry, states[stage_id], held))
    if live:
        raise ContractRefusal(
            "refused", "precondition",
            f"{sample_of(live)} of Job {name_value(prior['job_id'])} has not "
            f"settled ({sample_of(sorted(set(states[one] for one in live)))}); "
            f"a fresh attempt replaces an execution that is over, and "
            f"admitting one beside a stage still owed an act would put two "
            f"attempts on one specification")
    if _FAILED not in states.values():
        raise ContractRefusal(
            "refused", "precondition",
            f"no stage of Job {name_value(prior['job_id'])} is {_FAILED}: "
            f"{json.dumps(states, sort_keys=True)}. A fresh attempt repeats a "
            f"FAILED execution; a completed Job is finished and a "
            f"changes-requested one is the correction cycle's, which has its "
            f"own line and its own operation")
    return states


# -- what the other owners know ----------------------------------------------

def _over(entry, state, held):
    """Is this stage past the point where anything more will happen to it?"""
    if state in _TERMINAL:
        return True
    if state != "blocked":
        return False
    gates = projection.gates_of(entry["stage"], held)
    return bool(gates) and all(gate["state"] in _NEVER_OPENS
                               for gate in gates)


def _excluded(exclusion, attempt_ids, *, when, reserved=None):
    """The host has ceased every prior runtime and released every resource.

    FAIL CLOSED, which is the whole of REC-7's "unknown prior execution must
    not permit conflicting effects". There are three answers and only one of
    them is permission: ceased, still going, and NOBODY KNOWS. The pilot's
    helper treated a stale status timestamp and a dead supervisor PID as the
    third being the first; this refuses instead, and names the attempt.
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
                f"for is unknown, and unknown is not permission to start "
                f"another one against the same resources", reserved)
        found = held[attempt_id]
        if found is None:
            # NO ATTEMPT ROW AT ALL. The manager derived this identity when it
            # opened the episode and the host never recorded anything under
            # it, so nothing was ever launched for it. That is a real answer
            # and it is the common one for a stage that failed before it ran.
            evidence[attempt_id] = {
                "runtime": None, "cleanup": None, "resource": None,
                "basis": f"no attempt was ever recorded on this instance's "
                         f"own host, {held['host']}"}
            continue
        runtime = (found.get("runtime") or {}).get("execution_runtime")
        cleanup = (found.get("runtime") or {}).get("cleanup")
        token = found.get("token")
        if runtime not in _CEASED_RUNTIME:
            raise _refusing(
                f"attempt {name_value(attempt_id)}'s runtime is "
                f"{name_value(runtime)} and cessation is "
                f"{', '.join(_CEASED_RUNTIME)}; stop it and let the host "
                f"record the outcome before a fresh attempt is admitted",
                reserved)
        if cleanup not in _SETTLED_CLEANUP:
            raise _refusing(
                f"attempt {name_value(attempt_id)}'s cleanup is "
                f"{name_value(cleanup)} and this host still owes it; a fresh "
                f"attempt admitted now would compete with an accounting that "
                f"has not finished", reserved)
        if token is None:
            # REVIEW R11: AN ABSENT TOKEN IS UNCERTAINTY, and the owning
            # reader says so in its own words -- "never a synthetic
            # non-launch proof". The one reading that is not a guess is an
            # attempt the host recorded and never launched: no runtime
            # identity was ever minted for it, so there was no resource to
            # hold. Anything else is refused.
            launched = (found.get("runtime") or {}).get("runtime_id")
            if runtime != "not-started" or launched is not None:
                raise _refusing(
                    f"attempt {name_value(attempt_id)} has no workspace "
                    f"token in this host's record and its runtime is "
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


def _refusing(why, reserved):
    """One refusal, told differently once a reservation exists."""
    if reserved is None:
        return ContractRefusal("refused", "precondition", why)
    return _incomplete(why, reserved=reserved)


def _authorized(authorization, work_id, job_id, *, reserved=None):
    """The Work this fresh attempt will run under, reused or created.

    REUSED BY DEFAULT, and that is a configuration decision as much as an
    authorization one. `stage_execution._disagreements` compares a worker's
    manifest Work against the Job's binding, so a fresh Work needs workers
    carrying it -- which is new configuration for every retry, the exact
    "per-retry installation" REC-7 says is not required. The prior Work is
    already authorized, already bound and already served by the configured
    workers, and the failed Job that held it is over.
    """
    found = authorization.work_of(work_id)
    if found is None:
        created = authorization.create_work(work_id,
                                            operation_id=work_operation_id(
                                                job_id))
        return {"work_id": work_id, "disposition": "created",
                "status": (created or {}).get("status")}
    status = found.get("status")
    if status != "open":
        raise _refusing(
            f"Work {name_value(work_id)} is {name_value(status)} and a fresh "
            f"attempt runs under an open authorization; reopening somebody "
            f"else's Work is not this operation's to do", reserved)
    return {"work_id": work_id, "disposition": "reused", "status": status}


def _bound(binding, *, job_id, prior_job_id, work_id, document,
           reserved=None, task=None):
    """The deployment binds the fresh Job, and a worker can serve every stage.

    `task` IS THE TASK THIS FRESH JOB WILL BE DELIVERED, and W364834 is that
    it has to travel. The composed submission carries the prior Job's input
    digest verbatim, which for a template-created Job is its own task's
    Job-scoped identity -- so a servability question asked without the task
    compares every configured worker against the INSTALLED document and
    refuses the retry as unservable by the pool that served the original.
    `None` is every Job that has no own task, and the selector then compares
    the installed document exactly as it did before.

    THE SECOND HALF IS THE ONE THAT MATTERS, AND IT IS ASKED WITH THE
    SUBMITTED OPERANDS. Review R3: the first cut passed only a Job id and a
    stage kind, so the adapter built the digests and profiles it compared OUT
    OF the worker it was comparing them against -- a configuration consistent
    with itself, which proves nothing about the specification being
    re-attempted, and which judged a review stage by the implementation
    worker's profile. What travels now is the composed submission's own input
    digest, policy digest and per-stage profile, so `servable_workers`
    compares the real thing and the Work, the input, the policy, the profile
    and the producer affinity all have to agree.
    """
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
            f"{name_value(held.get('job_work_id'))} and this fresh attempt "
            f"runs under {name_value(work_id)}; a Job's Work is a fact about "
            f"the Job and this operation will not quietly move it", reserved)
    serving = {}
    for stage in entry["stages"]:
        workers = binding.serving(job_id, stage=dict(stage), job=dict(job),
                                  task=task)
        if not workers:
            raise _refusing(
                f"no configured worker can serve Job {name_value(job_id)}'s "
                f"{name_value(stage['kind'])} stage under its own submitted "
                f"input, policy and profile; a fresh attempt that cannot be "
                f"selected is a Job that would sit queued forever", reserved)
        serving[stage["kind"]] = sorted(workers)
    return {"job_id": job_id, "disposition": disposition,
            "job_work_id": work_id, "serving": serving}


# -- the specification, carried forward --------------------------------------

def _composed(store, prior, *, job_id, work_id, submission_id):
    """The fresh submission: the prior Job's own entry, renamed.

    EXACTLY THREE THINGS CHANGE -- the Job's identity, its stages' Work if the
    caller selected another one, and the dependency references that named the
    old identity. The input digest, the policy digest, the test scope, the
    terminal policy, the stage kinds, their profiles and their execution
    limits are the operator's selections and are carried verbatim.
    """
    entry = json.loads(json.dumps(prior["entry"]))
    entry["job_id"] = job_id
    for stage in entry["stages"]:
        stage["work_id"] = work_id
        # A DEPENDENCY ON THE OLD JOB WOULD GATE THE FRESH ONE ON A FAILURE.
        # Its stages depend on each other, not on the execution being
        # replaced, and `_resolvable` would refuse an unresolvable reference
        # anyway -- so the self-references move and a reference to any OTHER
        # Job is left exactly as the operator wrote it.
        for gate in stage.get("depends_on") or []:
            if gate["job_id"] == prior["job_id"]:
                gate["job_id"] = job_id
    document = {"schema": prior["schema"], "submission_id": submission_id,
                "jobs": [entry]}
    # OWNED HERE AS WELL AS IN `submit`, because a document this build
    # composed and cannot own is a defect to surface before a reservation is
    # taken rather than after.
    return documents.owned_submission(document)


# -- the two durable cuts in this store --------------------------------------

def _reserved(store, operands, prior, document):
    """CUT A: the fresh identity is spoken for, durably, inside the lock.

    The PRIMARY KEY is what makes two concurrent requests one admission, and
    the recorded request is what makes a THIRD request carrying different
    operands a refusal rather than a quiet resumption of somebody else's.
    """
    signature = job_signature(INTENT_KIND, operands)
    # THE EXACT DOCUMENT THIS RESERVATION IS FOR, in the submission store's
    # own spelling, so `_unclaimed` compares intents rather than names.
    intended = job_signature("submission.record", document)

    def act(connection):
        # THE ORDINARY JOB TABLE IS CHECKED HERE TOO, inside the same lock.
        # A fresh identity an ordinary submission already holds is not free,
        # and finding that out at `submit` would be finding it out after the
        # Work and the binding had been performed for it.
        # AND THE SUBMISSION IDENTITY ITSELF, before any effect. Review R9:
        # a submission id already recorded for a different document is a
        # collision this admission would only have met at its own `submit`,
        # with the Work and the binding already published.
        # AND ANOTHER RESERVATION HOLDING THAT SUBMISSION IDENTITY. Two
        # fresh attempts may legitimately choose their own names; two that
        # chose ONE name for two documents cannot both own the operation
        # identity derived from it, and finding that out at `submit` would
        # be finding it out with a binding already published.
        sharing = connection.execute(
            "SELECT job_id, submission_signature FROM fresh_attempts WHERE "
            "submission_id = ? AND job_id != ?",
            (operands["submission_id"], operands["job_id"])).fetchone()
        if sharing is not None and sharing[1] != intended:
            raise ContractRefusal(
                "refused", "precondition",
                f"submission {name_value(operands['submission_id'])} is "
                f"already reserved by the fresh attempt for Job "
                f"{name_value(sharing[0])} and carries a different "
                f"document; one submission identity names one intent")
        # NONE OF THE THREE SUBMISSION-IDENTITY REFUSALS BELOW IS DURABLE,
        # and it is the same rule that made the intruder rejection ordinary
        # one slice ago, applied where my own advice would otherwise have
        # been unfollowable. A durable refusal is a committed outcome for
        # THIS operation identity, and this intent's identity is derived
        # from the fresh JOB id. The remedy for all three is to choose
        # another SUBMISSION id for the same Job -- which is the same intent
        # operation id -- so sealing the refusal here would make the remedy
        # impossible and leave the caller in a loop. My own case for that
        # recovery is what caught it. What these report is another
        # identity's history, which is not this operation's outcome to seal.
        #
        # AND THE JOURNAL, WHICH IS WHERE A SUBMISSION IDENTITY REALLY LIVES.
        #
        # Review R15. `submissions` holds the rows a RECORDED submission
        # wrote, and `store.transact` additionally journals a DURABLE REFUSAL
        # as that operation's committed outcome -- so an identity can be
        # permanently settled with no submissions row at all, and an absent
        # row is not a free name. The first cut read only the rows, reserved,
        # published a binding, and then met the journal's immutable signature
        # at `submit`, where nothing could be done about it.
        #
        # AND THE ADVICE IS DIFFERENT FOR THIS ONE. Every other refusal past
        # the reservation is repaired by running the same request again; an
        # operation identity that is already settled for another intent never
        # will be, so this says to choose another submission identity instead
        # of sending the caller round a loop that cannot terminate. Nothing
        # here erases or renames the earlier outcome: history is what makes
        # the refusal true.
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
                f"change it: choose another submission identity. Nothing was "
                f"reserved and no Work or binding was touched")
        recorded = connection.execute(
            "SELECT signature FROM submissions WHERE submission_id = ?",
            (operands["submission_id"],)).fetchone()
        if recorded is not None and recorded[0] != intended:
            raise ContractRefusal(
                "refused", "precondition",
                f"submission {name_value(operands['submission_id'])} is "
                f"already recorded in this store for a different document; "
                f"a fresh attempt cannot take a submission identity that "
                f"names another intent")
        taken = connection.execute(
            "SELECT job_id FROM jobs WHERE job_id = ?",
            (operands["job_id"],)).fetchone()
        if taken is not None:
            raise ContractRefusal(
                "refused", "precondition",
                f"Job {name_value(operands['job_id'])} is already recorded "
                f"in this store by an ordinary submission; a fresh attempt "
                f"cannot take an identity that names another pipeline",
                durable=True)
        # W361912 review 2026-10-26T19-22-51Z R1: AND AN IDENTITY A TEMPLATE
        # CREATION HAS RESERVED. The exclusion has to be symmetric or it is
        # not an exclusion: a creation reserves `template_jobs` before it
        # publishes a Work authorization and a deployment binding, and a
        # retry that took that name would strand them exactly as the
        # reviewer's probe stranded a creation's.
        creating = connection.execute(
            "SELECT job_id, submission_id FROM template_jobs WHERE "
            "job_id = ? OR submission_id = ?",
            (operands["job_id"], operands["submission_id"])).fetchone()
        if creating is not None:
            raise ContractRefusal(
                "refused", "precondition",
                f"{name_value(creating[0])} is RESERVED by a template "
                f"creation recorded under submission "
                f"{name_value(creating[1])}; that creation is in progress or "
                f"incomplete and owns the identity, so a fresh attempt "
                f"taking the name would strand whatever it has already "
                f"published")
        held = connection.execute(
            "SELECT request, state FROM fresh_attempts WHERE job_id = ?",
            (operands["job_id"],)).fetchone()
        if held is not None:
            if json.loads(held[0]) != operands:
                raise ContractRefusal(
                    "refused", "precondition",
                    f"a fresh attempt is already reserved under "
                    f"{name_value(operands['job_id'])} for a different "
                    f"request; one identity names one admission and a second "
                    f"intent reusing it would take over the first one's Job",
                    durable=True)
            return _intent(operands, prior, state=held[1])
        # ONE FAILED JOB HAS ONE SUCCESSOR, AND THE DATABASE DECIDES IT.
        # Review R2: this was a SELECT taken before the transaction, and a
        # two-connection probe drove two requests past it with different
        # fresh identities -- both were admitted and one failure acquired
        # two successors. The unique index on `prior_job_id` is what two
        # writers actually meet at; the read below only turns the loser's
        # integrity error into the sentence it deserves.
        other = connection.execute(
            "SELECT job_id FROM fresh_attempts WHERE prior_job_id = ?",
            (operands["prior_job_id"],)).fetchone()
        if other is not None:
            raise _forked(operands["prior_job_id"], other[0])
        try:
            connection.execute(
                "INSERT INTO fresh_attempts (job_id, prior_job_id, "
                "prior_attempt_ids, work_id, submission_id, state, request, "
                "submission_signature, intended_at, admitted_at, "
                "incarnation) "
                "VALUES (?, ?, ?, ?, ?, 'intended', ?, ?, ?, NULL, ?)",
                (operands["job_id"], operands["prior_job_id"],
                 json.dumps(prior["attempt_ids"], ensure_ascii=False),
                 operands["work_id"], operands["submission_id"],
                 json.dumps(operands, sort_keys=True, ensure_ascii=False),
                 intended, store._now(), store.incarnation))
        except sqlite3.IntegrityError:
            # THE LOSER OF THE RACE READS WHO WON, inside its own still-open
            # transaction, so the identity it names is the one that is
            # actually there rather than one it remembered.
            won = connection.execute(
                "SELECT job_id FROM fresh_attempts WHERE prior_job_id = ?",
                (operands["prior_job_id"],)).fetchone()
            raise _forked(operands["prior_job_id"],
                          won[0] if won is not None else None) from None
        return _intent(operands, prior, state="intended")

    return store.transact(intent_operation_id(operands["job_id"]),
                          INTENT_KIND, signature, act)


def _forked(prior_job_id, successor):
    """A FORK IS TWO JOBS ON ONE WORK, and this is the one refusal for it."""
    return ContractRefusal(
        "refused", "precondition",
        f"Job {name_value(prior_job_id)} already has the fresh attempt "
        f"{name_value(successor)}; one failed execution has one successor, "
        f"and a second would put two Jobs on one Work. Ask for a fresh "
        f"attempt at {name_value(successor)} if that one has failed too",
        durable=True)


def _acquired(store, operands, *, owner):
    """Take exclusive ownership of THIS admission's external effects.

    Review R5. The reservation is about the IDENTITY and says nothing about
    who may act on it, so two identical concurrent requests -- one inserting
    the intent, one replaying it -- both went on to publish a binding. This
    is the compare-and-swap one of them loses.

    A HOLDER CONTINUES ITS OWN INTERRUPTED WORK and nobody else's. Re-running
    under the same manager incarnation re-acquires the row it already holds,
    which is how a crash between the binding and the submission is finished.
    A different incarnation is refused NAMING the holder rather than taking
    the work over, because deciding that an unseen manager has stopped is the
    inferred cessation this operation refuses everywhere else.
    """
    holder = _holder(store, owner)
    kind = ACQUIRE_KIND
    signature = job_signature(kind, dict(operands, holder=holder))

    def act(connection):
        changed = connection.execute(
            "UPDATE fresh_attempts SET holder = ? WHERE job_id = ? AND "
            "(holder IS NULL OR holder = ?)",
            (holder, operands["job_id"], holder)).rowcount
        if changed == 0:
            held = connection.execute(
                "SELECT holder, state FROM fresh_attempts WHERE job_id = ?",
                (operands["job_id"],)).fetchone()
            raise ContractRefusal(
                "refused", "precondition",
                f"the fresh attempt {name_value(operands['job_id'])} is held "
                f"by {name_value(held[0] if held else None)} and is "
                f"{name_value(held[1] if held else None)}; one admission "
                f"performs this identity's Work authorization, binding and "
                f"submission, and a second acting beside it would publish "
                f"them twice. Let that one finish, or re-run under the same "
                f"manager incarnation to continue its interrupted work")
        return {"job_id": operands["job_id"], "holder": holder}

    return store.transact(acquire_operation_id(operands["job_id"], holder),
                          kind, signature, act)


def _holder(store, owner):
    """Who this admission is, for the purpose of owning its own effects.

    THE INSTANCE GUARD AND THE MANAGER INCARNATION, TOGETHER. The guard names
    the control store this process holds the instance for, which is what
    makes two deployments' admissions distinguishable; the incarnation is the
    manager identity an operator re-runs under to continue its own work.
    """
    named = getattr(owner, "holder", None)
    return f"{store.incarnation}@{named if named else 'no-instance'}"


def _intent(operands, prior, *, state):
    return {"job_id": operands["job_id"],
            "prior_job_id": operands["prior_job_id"],
            "prior_attempt_ids": list(prior["attempt_ids"]),
            "work_id": operands["work_id"],
            "submission_id": operands["submission_id"], "state": state}


def _completed(store, operands, *, prior, settled, evidence, authorized,
               bound, recorded):
    """CUT C: the intent becomes an admission, and the answer is journalled.

    THE RESULT IS RECORDED RATHER THAN RECOMPOSED. A caller repeating the
    command is told the same thing the first one was told, including which
    evidence the decision rested on -- so "what did this retry inherit" is a
    question the store answers rather than one an operator reconstructs.
    """
    signature = job_signature(ADMIT_KIND, operands)
    answer = documents.fresh_attempt_admitted(
        job_id=operands["job_id"], prior_job_id=operands["prior_job_id"],
        prior_submission_id=prior["submission_id"],
        prior_attempt_ids=list(prior["attempt_ids"]),
        prior_states=settled, work=authorized, binding=bound,
        submission_id=operands["submission_id"],
        stages=list(recorded["stages"]), exclusion=evidence,
        recorded_at=recorded["recorded_at"])

    def act(connection):
        changed = connection.execute(
            "UPDATE fresh_attempts SET state = 'admitted', admitted_at = ? "
            "WHERE job_id = ? AND state = 'intended'",
            (store._now(), operands["job_id"])).rowcount
        if changed == 0:
            held = connection.execute(
                "SELECT state FROM fresh_attempts WHERE job_id = ?",
                (operands["job_id"],)).fetchone()
            if held is None:
                raise ContractRefusal(
                    "integrity", "schema",
                    f"the reservation for {name_value(operands['job_id'])} "
                    f"is gone between this operation's own two cuts")
        return answer

    return store.transact(admit_operation_id(operands["job_id"]), ADMIT_KIND,
                          signature, act)


# -- the owned reads ---------------------------------------------------------

def fresh_attempt_rows(store):
    from . import schema

    return [boundaries.row(record, "a persisted fresh attempt",
                           schema.FRESH_ATTEMPT_COLUMNS)
            for record in store._connection.execute(
                "SELECT * FROM fresh_attempts ORDER BY intended_at, job_id"
            ).fetchall()]


def fresh_attempt_of(store, job_id):
    from . import schema

    boundaries.identity(job_id, "a Job id")
    found = store._connection.execute(
        "SELECT * FROM fresh_attempts WHERE job_id = ?", (job_id,)).fetchone()
    if found is None:
        return None
    return boundaries.row(found, "a persisted fresh attempt",
                          schema.FRESH_ATTEMPT_COLUMNS)


def successors_of(store, prior_job_id):
    """Every fresh attempt recorded against one prior Job."""
    from . import schema

    boundaries.identity(prior_job_id, "a Job id")
    return [boundaries.row(record, "a persisted fresh attempt",
                           schema.FRESH_ATTEMPT_COLUMNS)
            for record in store._connection.execute(
                "SELECT * FROM fresh_attempts WHERE prior_job_id = ? "
                "ORDER BY intended_at, job_id", (prior_job_id,)).fetchall()]


# THE NAME THE PACKAGE EXPORTS. Inside this module the operation is `admit`,
# because the module says what is being admitted; `baton_v12.job_manager`
# already exports `submit`, `reserve` and `release`, and a bare `admit` beside
# them would not.
admit_fresh_attempt = admit
