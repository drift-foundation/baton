"""The seam onto the v12 operations this control plane composes.

W71875. THE POINT OF THIS FILE IS THAT THERE IS NO SECOND STATE MACHINE. Every
act the scheduler performs is one already-public Worker Manager operation, and
every fact it projects is one already-public Worker Manager read. What this
leaf adds is *when* to call them and a durable receipt saying it did -- not a
parallel account of offers, claims, attempts, runtimes or outputs.

TWO ACTS, AND WHY ONLY TWO. `admit` issues the offer that authorizes one stage
and `claim` takes the claim the accepted offer froze. Both are control-plane
acts that need nothing this leaf was told not to own. Starting a runtime needs
a delivered workspace and a runtime adapter (W71917, W71877); freezing an
output, deciding a verdict and importing a proposal need review and
integration policy (W71918, W71878). Those operations exist and are not called
from here, because calling them would mean inventing the operands their owners
have not specified yet.

THE CANONICAL OPERATION IDENTITY IS HOW A RESTART DECIDES. `issue_offer` and
the claim recording journal themselves in the MANAGER's store under identities
derived from the offer id, and `ControlStore.operation_record` is the public
reader for them. So a next incarnation that finds no receipt of its own can
ask the manager whether the act already committed, adopt that answer, and
neither repeat a committed act nor skip an owed one. The two templates below
are this build's copy of a spelling the manager owns -- `test_delegation`
drives the real operations and asserts the manager journals exactly these
identities, so a change to that spelling fails here loudly instead of turning
every restart into a repeated offer.

AND A DERIVED IDENTITY IS NOT BY ITSELF A BINDING. Review [P1]: the identity
above is derived from the Job id and the stage kind alone, and the CLI takes
the Job store and the control store as two independent paths -- so a second Job
store over one control store could submit the same `job-a/implementation` with
another input digest, find the first store's committed offer under the derived
name, adopt it, and project its own digest beside a canonical offer whose
signature contains only the first one's. The same operation id had become two
accounts of intent, which is the shadow state this leaf exists not to have.
`check_binding` below closes that: an existing canonical operation is proved to
be the act for THIS persisted Job/stage intent before anything is adopted from
it or read beside it, and one that is not refuses instead.

AND PROVING THE OFFER IS NOT BY ITSELF A BOUND OBSERVATION. Re-review [P1,
2026-09-03]: `check_binding` proves the record under this stage's derived OFFER
id, while the canonical observation was read under its derived ATTEMPT id --
two identities, and only the first was proved. A distinct canonical offer
issued for another Work can name this stage's attempt, win the manager's unique
claimed-attempt slot, and be projected as this Job's claim; the check still
passed, because this Job's own offer really was its own. Nothing recorded it
and no act stayed owed, so the false projection was durable and did not
self-correct. `observation_of` below is the answer: the observation is acquired
and bound to the proved offer identity in ONE operation, and an attempt whose
claim belongs to somebody else refuses instead of being read.
"""

import json

from ..contracts import ContractRefusal
from ..contracts.errors import name_value
from ..eventing import EventQueue, pump
from ..worker_manager import (attempt_activity_of, attempt_runtime_of,
                              attempt_preparation_failure_of,
                              attempt_start_failure_of, boundaries,
                              claimed_offers_for, frozen_output_of,
                              issue_offer, recover_on_restart, submit_claim)
from ..worker_manager.events import publish_offer_states

__all__ = ["CANONICAL_OPERATIONS", "INTENT_OPERANDS", "OBSERVATION_MEMBERS",
           "OPERATIONS", "ManagerOperations", "Unobserved",
           "canonical_operation", "check_binding", "observation_of",
           "stage_intent", "unobserved"]

# act -> the identity the MANAGER journals that act under, keyed by offer id.
CANONICAL_OPERATIONS = {"admit": "offer.issue:{offer_id}",
                        "claim": "offer.settle:{offer_id}"}

# The offer operands this leaf OWNS, and can therefore recognise its own act
# by. Every one is a member `issue_offer` puts in the signature it journals and
# every one comes from a persisted row here, so comparing them answers exactly
# "was this offer issued for the intent this store is holding".
#
# THE OTHER OPERANDS ARE DELIBERATELY NOT COMPARED. The participant, the
# authority, the Work's frozen scope and route and the offer's expiry are the
# manager's and the authority's facts about the same act; this leaf neither
# supplies nor persists them, so a build that recomputed them would be
# inventing a second opinion about somebody else's state in order to check it.
INTENT_OPERANDS = ("offer_id", "work_id", "runtime_attempt_id",
                   "input_digest", "policy_digest", "profile_digest")

# The closed surface a Job manager calls. A deployment may substitute its own
# object here, and a fake in a test may too -- so it is written down rather
# than discovered from whatever the caller happened to pass.
OPERATIONS = ("canonical", "canonical_operation", "receipt_of", "recover",
              "attach", "drain", "admit", "claim", "launch", "observe")

# W76207: `launch` is the THIRD act, and it is deliberately not a fourth
# receipt. `admit` and `claim` are the two acts this control plane journals in
# its own store; a runtime start is journalled by the Worker Manager under an
# identity it derives, so replaying it is that manager's question and not a
# second state machine here. What this leaf owns is WHEN to ask -- level-
# triggered, from canonical state, on every tick including the first one after
# a restart.
#
# IT IS NOT HIDDEN INSIDE `claim`, and that is the whole correction. A crash
# after the Authority commits the claim makes the next manager adopt the
# canonical `offer.settle` receipt WITHOUT calling `claim` again -- so a launch
# folded into that call would be skipped forever, exactly once, on the path
# nobody watches.

# What one stage's canonical observation carries. Every member is another
# package's public read; none of them is this leaf's opinion.
#
# `claimed_by` IS AN IDENTITY AND NOT A FLAG, and re-review [P1, 2026-09-03] is
# why it stopped being one. It used to be `claimed`, a boolean meaning "some
# offer holds this attempt's claim" -- and "somebody claimed it" and "this
# stage claimed it" are not the same fact. The attempt id is derived from the
# Job id and the stage kind, so another Job store can name it; a boolean threw
# away the only member that says whose claim was found, and `status` reported
# the other store's claim as this Job's. The reader answers WHICH offer holds
# it and this leaf decides whether that offer is the one it proved.
OBSERVATION_MEMBERS = ("claimed_by", "runtime", "activity", "output",
                       "start_failure", "preparation_failure")

# W76207: `start_failure` is the manager's OWN journalled record that this
# attempt's start failed, and it is a fifth member rather than something
# derived from `runtime` because it cannot be derived from it. The manager
# journals the failure as its own act and reconciliation may still ATTACH a
# runtime id afterwards, so an attached identity is not evidence that anything
# is running -- which is exactly how this projection used to report a stage as
# `running` after its start had durably failed.

# W76207 re-review [P1]: `preparation_failure` is a SIXTH member and not a
# spelling of the fifth. The manager keeps two records because they mean two
# things -- a start act that failed, which is also its authority to remove the
# container that start created, and a post-claim preparation that never
# reached a start and authorizes nothing. Filing one under the other's kind so
# this projection would not have to distinguish them was the defect; asking
# for both and treating either as an ending is what unifies them HERE, where
# unification is a stage state rather than a durable act.


def unobserved():
    """The observation of a stage nothing canonical is currently answering for.

    A FRESH DOCUMENT EACH TIME. It is handed to a projection that keeps it
    beside a stage, and one shared dict would make two stages' observations the
    same object -- which is fine until the day something writes to one.
    """
    return {"claimed_by": None, "runtime": None, "activity": None,
            "output": None, "start_failure": None,
            "preparation_failure": None}


def canonical_operation(act, offer_id):
    """The manager journal identity for one act on one offer."""
    if act not in CANONICAL_OPERATIONS:
        raise ContractRefusal(
            "integrity", "schema",
            f"this control plane delegates {', '.join(CANONICAL_OPERATIONS)}; "
            f"this is {name_value(act)}")
    return CANONICAL_OPERATIONS[act].format(offer_id=offer_id)


def stage_intent(stage, job):
    """The offer operands one persisted stage's submitted intent asks for.

    Assembled from the two rows and nothing else, so it is the store's account
    of the act rather than a re-derivation of what the manager probably did.
    """
    return {"offer_id": stage["offer_id"], "work_id": stage["work_id"],
            "runtime_attempt_id": stage["attempt_id"],
            "input_digest": job["input_digest"],
            "policy_digest": job["policy_digest"],
            "profile_digest": stage["profile_digest"]}


def check_binding(operations, stage, job):
    """Prove the canonical offer under this stage's derived id is THIS stage's.

    THE OFFER IS THE BINDING, WHICH IS WHY ONE CHECK COVERS EVERY ACT. Both
    identities this leaf derives are keyed by the offer id, the settlement can
    only be journalled by settling that one offer row, and the observation the
    projection reads is keyed by the attempt id the offer froze. So proving the
    `offer.issue` record carries this stage's intent proves the claim and the
    observation are this stage's too, and there is one place to get it right.

    Answers the record when there is one, and `None` when the offer has not
    been issued yet -- absence is not evidence of a foreign act, it is the
    ordinary state of a stage nothing has admitted.

    A caller holding NO control store is answered `None` without a read. Its
    journal is not open, `Unobserved` refuses the question, and a read-only
    status surface that could not be assembled without one would be a surface
    that only exists when the thing it exists without is present.
    """
    if not operations.canonical:
        return None
    operation_id = operations.canonical_operation("admit", stage["offer_id"])
    record = operations.receipt_of(operation_id)
    if record is None:
        return None
    wanted = stage_intent(stage, job)
    held = _operands(record, operation_id)
    differing = ["{0} {1} rather than {2}".format(
        name, name_value(held.get(name)), name_value(wanted[name]))
        for name in INTENT_OPERANDS if held.get(name) != wanted[name]]
    if differing:
        raise ContractRefusal(
            "refused", "operation-collision",
            f"the Worker Manager journalled {name_value(operation_id)} for "
            f"another intent -- it names {'; '.join(differing)} -- and stage "
            f"{name_value(stage['stage_id'])} of this store cannot adopt it. "
            f"One derived operation id naming two intents is a shadow account "
            f"of an act rather than a restart to reconcile, and adopting it "
            f"would project this store's Job beside somebody else's offer")
    return record


def _operands(record, operation_id):
    """The signed operands of one journalled operation, owned on the way in.

    The signature is durable text this process did not write, so it is decoded
    across a trust boundary like any other received document: a row whose
    signature is not an operation signature at all cannot answer whether the
    act was ours, and answering "it matches" for one would be the fail-open
    this check exists to close.
    """
    signature = record["signature"]
    try:
        held = json.loads(signature) if type(signature) is str else None
    except ValueError:
        held = None
    if type(held) is not dict or type(held.get("operands")) is not dict:
        raise ContractRefusal(
            "integrity", "schema",
            f"the Worker Manager's record of {name_value(operation_id)} "
            f"carries no operation signature this build can read, so nothing "
            f"can say whether it is this store's act")
    return held["operands"]


def observation_of(operations, stage, job):
    """This stage's canonical observation, ACQUIRED AND BOUND IN ONE OPERATION.

    Re-review [P1, 2026-09-03], and the approved correction: proving this Job's
    offer and then looking the attempt up by id alone is two operations, and
    the second one is unqualified. `check_binding` proves the record under this
    stage's derived OFFER id; the observation is read under its derived ATTEMPT
    id, which nothing had shown belonged to that offer. The measured defect is
    a distinct canonical offer for another Work naming this attempt, taking the
    manager's unique claimed-attempt slot, and being projected as this Job's
    claim while this Job store holds only its `admit` receipt. A claimed stage
    owes nothing, so the next sweep asked for nothing and the false projection
    stood.

    So the two are one act here. What the reader returns is compared against
    the offer identity just proved, at the instant it is returned, and a
    foreign holder refuses `refused/operation-collision` rather than being
    projected, recorded, or allowed to answer an act this Job still owes.

    THE ORDER IS SAFE IN BOTH DIRECTIONS, which is what makes one pass enough.
    A canonical operation row is immutable once written, so a foreign row
    arriving under this stage's OFFER id after the proof is what `_proved`'s
    own read refuses at the next read rather than something this pass can
    miss; and a foreign CLAIM arriving after the proof is compared below at the
    moment it is read, never trusted from an earlier look.
    """
    check_binding(operations, stage, job)
    return _bound(operations.observe(stage), stage)


def _bound(observed, stage):
    """One acquired observation, owned, and bound to this stage's own offer.

    THE CLAIM IS THE ONLY THING THAT BINDS AN ATTEMPT TO AN OFFER. The manager
    persists the attempt id on the offer and holds at most one claimed offer
    per attempt; the runtime, the activity and the frozen result carry the
    attempt id and no offer at all, and it is the manager's own activation that
    refuses to run an attempt for anything but that attempt's committed claim.
    So an unclaimed attempt has nothing to say about this stage, and reporting
    its facts would be projecting attempt-keyed observations that nothing has
    bound to this Job.
    """
    held = boundaries.document(observed, "a canonical observation",
                               required=OBSERVATION_MEMBERS)
    holder = held["claimed_by"]
    if holder is None:
        return unobserved()
    boundaries.identity(holder, "the offer holding an attempt's claim")
    if holder != stage["offer_id"]:
        raise ContractRefusal(
            "refused", "operation-collision",
            f"the Worker Manager's claim on attempt "
            f"{name_value(stage['attempt_id'])} is held by "
            f"{name_value(holder)}, and stage "
            f"{name_value(stage['stage_id'])} of this store was issued "
            f"{name_value(stage['offer_id'])}. An attempt id derived from the "
            f"Job id and the stage kind is a name another Job store can also "
            f"reach, so projecting that claim as this Job's would report a "
            f"runtime this store never obtained and leave this stage's own "
            f"claim owed to nobody")
    return held


def _one_claim(control, attempt_id):
    """WHICH offer holds this attempt's claim, or absence.

    EXACTLY ONE, ASKED FOR RATHER THAN ASSUMED -- the manager reads the same
    question the same way. A unique partial index makes two impossible going
    forward, and a store written before it must fail closed here, because
    "whose claim is this stage looking at" has no answer row order may invent.
    """
    held = claimed_offers_for(control, attempt_id)
    if len(held) > 1:
        raise ContractRefusal(
            "integrity", "schema",
            f"the Worker Manager holds {len(held)} claimed offers for attempt "
            f"{name_value(attempt_id)}; one attempt belongs to one offer, and "
            f"choosing between them by row order would be inventing the "
            f"answer to whose claim this is")
    return held[0]["offer_id"] if held else None


class ManagerOperations:
    """The default binding: exactly the public v12 operations, and nothing else.

    Constructed from capabilities trusted deployment supplies -- the manager's
    control store, the authority-bound port, the bearer mint and the bearer
    delivery. This class opens no store, mints no session and reaches for no
    private attribute of either package.
    """

    __slots__ = ("control", "port", "events", "_mint_bearer",
                 "_deliver_bearer", "_start_runtime")

    # THE CANONICAL STORE IS OPEN. A status document says so, because a
    # projection assembled without the manager can only report what was
    # submitted and what this store received receipts for -- and "nothing is
    # running" and "nobody looked" are not the same answer.
    canonical = True

    def __init__(self, control, port, *, mint_bearer, deliver_bearer,
                 events=None, start_runtime=None):
        self.control = control
        self.port = port
        # THE TRANSPORT IS OURS BY DEFAULT AND SUPPLIABLE ON PURPOSE. One
        # process holding both products needs exactly one queue between them;
        # a deployment that later puts a socket or a broker in the middle
        # supplies its own object here and changes nothing else, because what
        # travels is a regenerable assertion rather than an authority.
        self.events = EventQueue() if events is None else events
        # Typed before anything is spent. A capability that cannot be called
        # would otherwise fault in the middle of a delegated authority act.
        self._mint_bearer = boundaries.capability(mint_bearer,
                                                  "the bearer mint")
        self._deliver_bearer = boundaries.capability(
            deliver_bearer, "the deployment's bearer delivery")
        # THE RUNTIME COMPOSITION IS THE DEPLOYMENT'S, and it is optional here
        # because a control plane with no way to start a worker is a real and
        # useful deployment: it still admits, claims, observes and reports. A
        # deployment that supplies none says so by omission and `launch`
        # refuses rather than pretending it started something.
        self._start_runtime = (None if start_runtime is None
                               else boundaries.capability(
                                   start_runtime,
                                   "the deployment's runtime start"))

    def canonical_operation(self, act, offer_id):
        return canonical_operation(act, offer_id)

    def receipt_of(self, operation_id):
        """The manager's own journal row for one operation, or absence.

        THIS IS THE RECONCILIATION READ. It is the manager's public projection
        of its journal, so what a restart adopts is the operation's committed
        record rather than a re-derivation of what it probably did.
        """
        return self.control.operation_record(operation_id)

    def recover(self, *, now):
        """The manager's own restart rules, run before anything is derived.

        An offer this manager issued and never delivered a bearer for is
        abandoned by `recover_on_restart`; an accepted one stays recoverable.
        Deciding that here would be a second opinion about the manager's
        durable state.

        NOTHING IS PUBLISHED FROM IN HERE, and that is deliberate rather than
        an omission. `recover_on_restart` commits as it settles, so a publish
        placed inside it would emit under its own write; and an assertion that
        exists only because somebody was on this code path is exactly the
        one-shot notice the level-triggered design rejects. The caller attaches
        after this returns, which republishes the same facts from the rows
        recovery has just committed.
        """
        return recover_on_restart(self.control, now=now)

    def attach(self, offer_ids):
        """Ask the manager to republish the current state of these offers.

        WHAT A CONSUMER DOES INSTEAD OF READING SOMEBODY ELSE'S TABLES. The
        consumer names the offers it is holding episodes for; the manager
        answers about its own rows, into the transport. Called after every
        recovery and on every resume, so a lost delivery costs latency rather
        than a wedged stage.
        """
        return publish_offer_states(self.control, self.events, offer_ids)

    def drain(self, handlers, *, quiescent=()):
        """Dispatch what is queued, at the top level, one handler at a time.

        The manager's own connection is probed alongside whatever the caller
        supplies, because both stores must be out of transaction before any
        handler runs: a consumer writing its store inside this manager's write
        would be one transaction with two owners.
        """
        return pump(self.events, handlers,
                    quiescent=tuple(quiescent)
                    + (lambda: self.control._connection.in_transaction,))

    def admit(self, stage, job):
        """Issue the offer that authorizes one stage.

        The offer's operands are the SUBMITTED intent: the Work the stage
        names, the Job's immutable input and policy identities, and the
        runtime profile the stage requested. Nothing is chosen here -- picking
        a worker out of a pool is W71877's, and a scheduler that quietly
        substituted a profile would be making that choice invisibly.
        """
        issued = issue_offer(
            self.control, self.port,
            offer_id=stage["offer_id"], work_id=stage["work_id"],
            runtime_attempt_id=stage["attempt_id"],
            input_digest=job["input_digest"],
            policy_digest=job["policy_digest"],
            profile_digest=stage["profile_digest"],
            profile_name=stage["profile_name"],
            mint_bearer=self._mint_bearer)
        # ONE CALL, AND THEN IT IS GONE. The issued document carries the
        # bearer; the delivery capability is the only thing that sees it, and
        # what this method answers is the manager's own journalled record read
        # back through `receipt_of` rather than anything derived from here.
        self._deliver_bearer(issued)
        return None

    def claim(self, stage):
        """Take the claim the accepted offer froze.

        An offer that has not been accepted yet refuses with an ORDINARY
        precondition, which is the honest answer: the worker has not decided.
        The sweep leaves the act owed and asks again, rather than recording a
        receipt for something that did not happen.
        """
        submit_claim(self.control, self.port, offer_id=stage["offer_id"])
        return None

    def launch(self, stage, job):
        """Drive ONE claimed stage into a live worker, through the deployment.

        WHAT THIS METHOD IS NOT. It is not a composition. The attempt record,
        the activation, the workspace and input delivery, the retained
        manifest, the credential materialization, the launch delivery, the
        adapter and `request_runtime_start` are all the Worker Manager's own
        public operations, ordered by the deployment that holds the homes and
        capabilities they need. This leaf holds none of those and is not going
        to grow them: what it contributes is the canonical operands and the
        decision that NOW is when to ask.

        IDEMPOTENCE IS THE MANAGER'S, NOT A RECEIPT HERE. Every act in that
        composition is journalled by its owner under an identity that owner
        derives, so a second call after a crash replays rather than repeats.
        Writing a Job-store receipt for the launch would be a second account
        of a fact somebody else already owns -- and the one this leaf could
        not keep true, because the crash window it exists for is between the
        act and the receipt.

        A deployment that supplied no runtime start refuses here rather than
        answering: a control plane cannot report that a worker is coming up
        when nothing in it can start one.
        """
        if self._start_runtime is None:
            raise ContractRefusal(
                "refused", "capability",
                f"this Job manager was given no runtime start, so it cannot "
                f"launch stage {name_value(stage['stage_id'])}; a deployment "
                f"that admits and claims without one is a control plane that "
                f"reports work it can never begin")
        return self._start_runtime(stage, job)

    def observe(self, stage):
        """Every canonical fact the projection needs, from public readers.

        FIVE READS AND NO OPINION. WHICH offer holds this attempt's claim,
        whether the attempt has a runtime, how much of that runtime this
        manager has observed, what result was frozen, and whether this
        manager recorded that the start FAILED. `observation_of` binds them to
        the stage; this method decides nothing and is not the place a caller
        should reach for one.

        THE FIFTH IS NOT REDUNDANT WITH THE SECOND. A failed start is its own
        journalled act and reconciliation may attach a runtime id after it, so
        reading only the runtime would report a stage as running on the
        strength of an identity its start never earned.

        WHOSE CLAIM IT IS, BECAUSE THE MANAGER KNOWS. This answered a boolean
        until re-review [P1, 2026-09-03], and the offer id it discarded was the
        only fact distinguishing this stage's claim from another Job store's
        claim on the same derived attempt id. A reader that throws away the
        answer leaves nobody able to check it.

        Custody, retention and cleanup receipts are deliberately absent. They
        are the manager's own endings and they belong to whoever ends the
        attempt, so reporting them as a stage state here would be this leaf
        answering a question it does not own.
        """
        attempt_id = stage["attempt_id"]
        return {"claimed_by": _one_claim(self.control, attempt_id),
                "runtime": attempt_runtime_of(self.control, attempt_id),
                "activity": attempt_activity_of(self.control, attempt_id),
                "output": frozen_output_of(self.control, attempt_id),
                "start_failure": attempt_start_failure_of(self.control,
                                                          attempt_id),
                "preparation_failure": attempt_preparation_failure_of(
                    self.control, attempt_id)}


class Unobserved:
    """The read-only surface for a caller holding no manager control store.

    A status command run without one is a legitimate and useful thing -- it
    answers what was submitted, what this control plane delegated, and what it
    recorded -- and it must not pretend to have looked at the manager. So the
    observation is EMPTY rather than absent, `canonical` is false, and every
    ACT is refused: an object that could derive an act it cannot perform would
    be a scheduler with no scheduler.
    """

    canonical = False

    def canonical_operation(self, act, offer_id):
        return canonical_operation(act, offer_id)

    def receipt_of(self, operation_id):
        return self._refuse("read the manager's journal")

    def recover(self, *, now):
        return self._refuse("run the manager's restart recovery")

    def attach(self, offer_ids):
        # NOT A REFUSAL, because attaching is how a reader says what it holds
        # and a reader with no manager holds no conversation with one. It
        # asserts nothing, which is the honest answer, and `canonical: false`
        # is what tells the operator why.
        return []

    def drain(self, handlers, *, quiescent=()):
        return 0

    def admit(self, stage, job):
        return self._refuse("issue an offer")

    def claim(self, stage):
        return self._refuse("submit a claim")

    def launch(self, stage, job):
        return self._refuse("start a worker runtime")

    def observe(self, stage):
        return unobserved()

    @staticmethod
    def _refuse(what):
        raise ContractRefusal(
            "refused", "capability",
            f"this Job manager was given no Worker Manager control store, so "
            f"it cannot {what}; a read-only status surface reports what was "
            f"submitted and what this control plane recorded, and it does not "
            f"guess at the rest")
