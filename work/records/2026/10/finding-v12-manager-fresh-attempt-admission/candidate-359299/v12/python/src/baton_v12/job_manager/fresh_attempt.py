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
import sqlite3

from ..contracts import ContractRefusal
from ..contracts.errors import name_value, sample_of
from ..worker_manager import boundaries
from . import documents, episodes, projection, submission
from .store import job_signature

__all__ = ["INTENT_KIND", "ADMIT_KIND", "admit", "admit_fresh_attempt",
           "fresh_attempt_of", "fresh_attempt_rows", "successor_of",
           "successors_of"]

INTENT_KIND = "fresh_attempt.intend"
ADMIT_KIND = "fresh_attempt.admit"

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


def work_operation_id(job_id):
    """The identity the Authority creation is journalled under, if one is made.

    Derived from the FRESH JOB rather than from the Work, because the Work is
    what this operation may be creating and an identity derived from it would
    be the same for two different admissions that happened to choose it.
    """
    return f"{ADMIT_KIND}:work:{job_id}"


def admit(store, operations, *, prior_job_id, exclusion, authorization,
          binding, job_id=None, work_id=None, submission_id=None):
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
                       (binding, "the deployment binding port")):
        if port is None:
            raise ContractRefusal(
                "integrity", "schema",
                f"a fresh attempt composes three owners and {what} is "
                f"absent; this operation does not decide an owner's fact for "
                f"it by assuming one")

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

    settled = _settled(store, operations, prior)
    evidence = _excluded(exclusion, prior["attempt_ids"], when="before")
    document = _composed(store, prior, job_id=job_id, work_id=work_id,
                         submission_id=submission_id)

    # -- CUT A: THE RESERVATION COMES FIRST, BEFORE ANY OTHER OWNER IS
    #    MUTATED. Review R4: the first cut created the Work here and reserved
    #    afterwards, so a request that differed from a recorded one minted a
    #    Work on the Authority and THEN refused as a collision -- an effect
    #    performed on behalf of an operation that was never admitted. Nothing
    #    outside this store is touched until this returns, and what it
    #    returns is the operands this store agreed to.
    _reserved(store, operands, prior, document)

    # -- re-ask, because cut A took time and a reservation is not a lock on
    #    somebody else's store.
    evidence = _excluded(exclusion, prior["attempt_ids"], when="after",
                         reserved=job_id)

    # -- CUT B: the Work authorization, then the binding, both AFTER the
    #    reservation and both idempotent. The binding is inert until the Job
    #    exists, so it is the safe half to publish first.
    authorized = _authorized(authorization, work_id, job_id,
                             reserved=job_id)
    bound = _bound(binding, job_id=job_id, prior_job_id=prior_job_id,
                   work_id=work_id, document=document, reserved=job_id)

    # -- CUT C: the submission, and the completion that closes the intent.
    recorded = submission.submit(store, document)
    return _completed(store, operands, prior=prior, settled=settled,
                      evidence=evidence, authorized=authorized, bound=bound,
                      recorded=recorded)


# -- what this store alone knows ---------------------------------------------

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
                        "the host's attempt evidence", required=(),
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
            evidence[attempt_id] = {"runtime": None, "cleanup": None,
                                    "resource": None, "basis": "no attempt "
                                    "was ever recorded on this host"}
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
        if token is not None and not token.get("returned"):
            raise _refusing(
                f"attempt {name_value(attempt_id)} still holds its workspace "
                f"resource: the token is outstanding. A returned resource is "
                f"what makes the workspace free for another execution",
                reserved)
        evidence[attempt_id] = {
            "runtime": runtime, "cleanup": cleanup,
            "resource": "returned" if token is not None else None,
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
           reserved=None):
    """The deployment binds the fresh Job, and a worker can serve every stage.

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
        workers = binding.serving(job_id, stage=dict(stage), job=dict(job))
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

    def act(connection):
        # THE ORDINARY JOB TABLE IS CHECKED HERE TOO, inside the same lock.
        # A fresh identity an ordinary submission already holds is not free,
        # and finding that out at `submit` would be finding it out after the
        # Work and the binding had been performed for it.
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
                "intended_at, admitted_at, incarnation) "
                "VALUES (?, ?, ?, ?, ?, 'intended', ?, ?, NULL, ?)",
                (operands["job_id"], operands["prior_job_id"],
                 json.dumps(prior["attempt_ids"], ensure_ascii=False),
                 operands["work_id"], operands["submission_id"],
                 json.dumps(operands, sort_keys=True, ensure_ascii=False),
                 store._now(), store.incarnation))
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
