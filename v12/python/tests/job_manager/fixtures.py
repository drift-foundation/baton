"""The two stores, the strict session, and one two-Job submission.

THE FAKE SESSION IS STRICT ON PURPOSE. A permissive one would let this control
plane call things the real authority session does not have and pass anyway,
which is the opposite of what composing an existing operation is for. It
answers exactly the members `AuthorityPort` names and records every call, so a
case can assert which canonical operation was reached.
"""

import os
import tempfile
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import JobStore, ManagerOperations, stage_intent
from baton_v12.worker_manager import (ControlStore, certify_profile,
                                      manager_signature)

NOW = "2026-09-02T00:00:00.000Z"
# Inside the manager's 120-second offer TTL, so a case about restart recovery
# is about recovery rather than about an offer the clock already ended.
SOON = "2026-09-02T00:01:00.000Z"
LATER = "2026-09-02T00:05:00.000Z"
WHO = "baton.claude"
UUID = "0" * 31 + "a"
SCOPE = "scope:deployment"
ROUTE = "baton.impl"
PRINCIPAL = "principal:org-a"
PROFILE = "sha256:" + "b" * 64
INPUT_DIGEST = "sha256:" + "1" * 64
POLICY_DIGEST = "sha256:" + "2" * 64
WORK_A = "0000000a-W1"
WORK_B = "0000000a-W2"
WORK_C = "0000000a-W3"


def decision(participant=WHO):
    return {"endpoint": participant, "principal": PRINCIPAL,
            "effective_scope": SCOPE, "role": ROUTE, "grant": "direct",
            "policy_generation": 1}


class FakeSession:
    """Exactly the seven members the port names, and a record of every call."""

    def __init__(self, participant=WHO):
        self.participant = participant
        self.calls = []
        self.work = {}
        self.claim_answer = {
            "assignment": {"work_ref": {"authority_uuid": UUID,
                                        "work_id": WORK_A},
                           "participant": participant, "generation": 1},
            "claim_event": 1, "decision": decision(participant)}
        self.settle_answer = {"kind": "live", "record": None}

    def open_work(self, work_id):
        self.work[work_id] = {"status": "open", "phase": "queued",
                              "handler": None, "gate": None,
                              "authority_uuid": UUID, "scope": SCOPE,
                              "route": ROUTE}

    def project_work(self, work_id):
        self.calls.append(("project_work", work_id))
        return self.work.get(work_id)

    def slot_holder(self, participant):
        self.calls.append(("slot_holder", participant))
        return None

    def assignment_of(self, work_id):
        self.calls.append(("assignment_of", work_id))
        return dict(self.claim_answer["assignment"])

    def cancel(self, operands):
        self.calls.append(("cancel", dict(operands)))
        return {"cause": "cancelled",
                "assignment": dict(self.claim_answer["assignment"]),
                "phase": "block", "gate": "runtime-quiescence:1",
                "fenced": True}

    def claim(self, operands):
        self.calls.append(("claim", dict(operands)))
        if isinstance(self.claim_answer, BaseException):
            raise self.claim_answer
        answer = dict(self.claim_answer)
        assignment = dict(answer["assignment"])
        assignment["work_ref"] = {"authority_uuid": UUID,
                                  "work_id": operands["work_id"]}
        answer["assignment"] = assignment
        return answer

    def settle_operation(self, operands):
        self.calls.append(("settle_operation", dict(operands)))
        return self.settle_answer

    def publish_answer(self, operands):
        self.calls.append(("publish_answer", dict(operands)))
        return "baton:M1"


def _unobserved():
    """A stage nothing canonical has happened to yet."""
    return {"claimed_by": None, "runtime": None, "activity": None,
            "output": None, "start_failure": None,
            "preparation_failure": None, "exchange": None}


# The kind the MANAGER journals each delegated act under. The fake below signs
# its journal rows the way `offers.py` does, so a case that reconciles against
# it is reconciling against the shape the real store holds rather than against
# a placeholder the binding proof would have to be lenient about.
FAKE_KINDS = {"admit": "offer.issue", "claim": "offer.settle"}


def signature_of(act, intent=None):
    """One journal row's signature, in the real spelling.

    `intent` is the offer's own operands and is absent for a settlement, which
    is the truth about `offer.settle`: it signs the offer id, the state and the
    authorization context, and the Job facts belong to the offer it settles.
    """
    return manager_signature(FAKE_KINDS[act],
                             dict(intent) if intent is not None else {})


def fake_claim_signature(work_id, participant):
    """Stands in for the authority's own derivation.

    The manager consumes it and never recomputes it, so a fake proves the
    manager USES what it is given.
    """
    return f"claim-signature({work_id},{participant})"


def stage(kind="implementation", work_id=WORK_A, depends_on=None,
          profile_name="reference", profile_digest=PROFILE):
    return {"kind": kind, "work_id": work_id, "profile_name": profile_name,
            "profile_digest": profile_digest,
            "depends_on": depends_on if depends_on is not None else []}


def job(job_id="job-a", stages=None, test_scope=None,
        terminal_policy="report-and-hold", input_digest=INPUT_DIGEST,
        policy_digest=POLICY_DIGEST):
    return {"job_id": job_id, "input_digest": input_digest,
            "policy_digest": policy_digest,
            "test_scope": test_scope if test_scope is not None
            else ["v12/python/tests/job_manager"],
            "terminal_policy": terminal_policy,
            "stages": stages if stages is not None else [stage()]}


def submission(submission_id="sub-1", jobs=None):
    """The default document: two independent Jobs from one baseline.

    Job A carries an implementation stage and a review stage gated on it; Job
    B carries an implementation stage gated on nothing. That is the smallest
    document that exercises both halves of the acceptance -- concurrent
    independent Jobs, and a stage-scoped dependency that has to open before
    its successor is eligible.
    """
    return {"schema": "baton.v12.job-submission/1",
            "submission_id": submission_id,
            "jobs": jobs if jobs is not None else [
                job("job-a", stages=[
                    stage("implementation", WORK_A),
                    stage("review", WORK_B,
                          depends_on=[{"job_id": "job-a",
                                       "kind": "implementation"}])]),
                job("job-b", stages=[stage("implementation", WORK_C)])]}


class JobManagerCase(unittest.TestCase):
    """One temporary root holding both stores, and one pinned clock."""

    def setUp(self):
        self._root = tempfile.TemporaryDirectory(prefix="v12-job-manager-")
        self.addCleanup(self._root.cleanup)
        self.root = self._root.name
        self.job_path = os.path.join(self.root, "jobs.sqlite3")
        self.control_path = os.path.join(self.root, "control.sqlite3")
        self.instants = [NOW]
        self.session = FakeSession()
        for work_id in (WORK_A, WORK_B, WORK_C):
            self.session.open_work(work_id)
        self.minted = []
        self.delivered = []

    def clock(self):
        return self.instants[-1]

    def store(self, incarnation="jobs-1", authority_uuid=UUID):
        """This case's Job store, bound to this case's Authority.

        W83781 made the binding required: it is the namespace every episode
        identity is derived in. `UUID` is the same authority the fake session
        answers for, so a case that wants two independent authorities names
        the second one explicitly.
        """
        store = JobStore.open(self.job_path, authority_uuid=authority_uuid,
                              incarnation=incarnation, clock=self.clock)
        self.addCleanup(store.close)
        return store

    def control(self, incarnation="manager-1"):
        control = ControlStore.open(self.control_path,
                                    incarnation=incarnation, clock=self.clock)
        self.addCleanup(control.close)
        certify_profile(control, "runtime", "reference", PROFILE)
        return control

    def attempting(self, store, stage_id="job-a/implementation"):
        """One stage row merged with the episode currently answering for it.

        W73629 moved the offer and attempt identities off the stage and onto
        the episode, so a case that wants "this stage's offer" wants the live
        episode's. This is the same view the projection hands the seam.
        """
        from baton_v12.job_manager import attempting, live_of, stage_rows

        row = {one["stage_id"]: one for one in stage_rows(store)}[stage_id]
        return attempting(row, live_of(store, stage_id))

    def operations(self, control=None, port=None, **supplied):
        """The REAL operations object, with any optional capability supplied.

        `**supplied` reaches `ManagerOperations` unchanged, so a case about one
        optional capability names exactly that one and every other stays
        absent -- which is the posture the class documents.
        """
        from baton_v12.worker_manager import AuthorityPort

        control = control if control is not None else self.control()
        port = port if port is not None else AuthorityPort(
            self.session, fake_claim_signature)
        return ManagerOperations(control, port, mint_bearer=self.mint,
                                 deliver_bearer=self.deliver, **supplied)

    def mint(self):
        bearer = f"bearer-{len(self.minted) + 1}"
        self.minted.append(bearer)
        return bearer

    def deliver(self, issued):
        self.delivered.append(issued)


class FakeOperations:
    """The closed surface, with the canonical journal and observations set.

    THE COMPOSITION ITSELF IS PROVED AGAINST THE REAL OPERATIONS in
    `test_delegation`; what this stands in for is the rest of the pipeline.
    Freezing an output needs a delivered workspace, a runtime adapter and a
    review verdict -- three leaves this one does not own -- so a case about
    what a COMPLETED stage unblocks sets the manager's own answer directly
    rather than building three other leaves to obtain it.

    It is strict: exactly the members `delegation.OPERATIONS` names, and every
    act is recorded.
    """

    canonical = True

    def __init__(self):
        from baton_v12.eventing import EventQueue

        self.journal = {}
        self.observations = {}
        self.refusals = {}
        self.states = {}
        self.launches = {}
        self.recorded_failures = {}
        self.commands = {}
        self.endings = {}
        self.refreshes = {}
        self.refreshed_calls = []
        self.attaching = set()
        self.events = EventQueue()
        self.calls = []

    def canonical_operation(self, act, offer_id):
        from baton_v12.job_manager import canonical_operation

        return canonical_operation(act, offer_id)

    def receipt_of(self, operation_id):
        return self.journal.get(operation_id)

    def recover(self, *, now):
        self.calls.append(("recover", now))
        return {"abandoned": [], "recoverable": []}

    def attach(self, offer_ids):
        """Republish whatever this fake has been told the canonical state is.

        A case sets `states` for the offers it cares about; attaching turns
        those into the same `offer.state` documents the real publisher builds,
        so a case drives the consumer through its real handler rather than
        calling it directly. Silence for an offer nobody set is the real
        publisher's answer too.
        """
        from baton_v12.worker_manager.events import offer_state

        self.calls.append(("attach", tuple(offer_ids)))
        published = []
        for offer_id in offer_ids:
            held = self.states.get(offer_id)
            if held is None:
                continue
            self.events.publish(offer_state(held))
            published.append(offer_id)
        return published

    def drain(self, handlers, *, quiescent=()):
        from baton_v12.eventing import pump

        return pump(self.events, handlers, quiescent=tuple(quiescent))

    def starts(self, stage_id, answer=None, attaches=False):
        """Configure what this deployment's runtime start answers, or raises.

        `attaches` makes the successful start ALSO record the canonical runtime
        observation, which is what the real Worker Manager does inside
        `request_runtime_start`. A case about the post-start acts wants it; a
        case about the launch pass itself deliberately does not, because
        leaving the observation empty is how it drives the pass again.
        """
        self.launches[stage_id] = ({"runtime_id": f"runtime-{stage_id}"}
                                   if answer is None else answer)
        if attaches:
            self.attaching.add(stage_id)

    def fails(self, stage_id, error, *, records=True):
        """Fail this stage's launch, with or without a canonical record.

        `records=True` is the production shape: `request_runtime_start`
        journals the failed start and THEN lets the fault out, so the Job
        manager can prove the ending exists. `records=False` is the deployment
        that refused durably and journalled nothing, which the manager must
        not quietly retry forever.
        """
        self.launches[stage_id] = error
        if records:
            from baton_v12.job_manager.episodes import identities

            _offer_id, attempt_id = identities(UUID, stage_id, 1)
            self.recorded_failures[stage_id] = {
                "attempt_id": attempt_id, "expect": None,
                "start_operation_id": f"runtime.start:{stage_id}",
                "runtime_id": None, "execution_runtime": "absent",
                "failure": {"kind": "fault", "fault": type(error).__name__,
                            "message": str(error)}}
        else:
            self.recorded_failures.pop(stage_id, None)

    def canonical_state(self, offer_id, attempt_id, state):
        """Pretend the manager's offers table holds this row's state."""
        self.states[offer_id] = {"offer_id": offer_id,
                                 "runtime_attempt_id": attempt_id,
                                 "state": state}

    def admit(self, stage, job):
        # THE SIGNATURE IS THE REAL ONE'S SHAPE, because the binding proof
        # reads it. `issue_offer` journals the offer's operands under
        # `offer.issue`, so a fake that signed `{}` would let every adoption
        # case pass without the intent ever being compared -- which is exactly
        # the fail-open this fixture is now helping to cover.
        return self._act("admit", stage, {"offer_id": stage["offer_id"],
                                          "work_id": stage["work_id"]},
                         intent=stage_intent(stage, job))

    def claim(self, stage):
        # NO INTENT, LIKE THE REAL `offer.settle`: its signature carries the
        # offer id, the state and the authorization context, and the Job facts
        # are the offer's. The binding is proved through the offer.
        return self._act("claim", stage, {"offer_id": stage["offer_id"],
                                          "state": "claimed"})

    def launch(self, stage, job):
        """The deployment's runtime start, as a case configures it.

        DEFAULT IS A REFUSAL, and it is the honest one: a deployment that was
        given no runtime start cannot begin work, which is exactly what
        `ManagerOperations` answers with no `start_runtime`. A case that wants
        a live worker says so with `starts`.
        """
        stage_id = stage["stage_id"]
        self.calls.append(("launch", stage_id))
        held = self.launches.get(stage_id)
        if held is None:
            raise ContractRefusal(
                "refused", "capability",
                f"this fake deployment was given no runtime start for "
                f"{stage_id}")
        if isinstance(held, BaseException):
            # THE RECORD IS WRITTEN BEFORE THE RAISE, exactly as the real
            # `request_runtime_start` does it: the failed start is journalled
            # and only then does the adapter's fault come back out. A case that
            # wants the unrecorded variant says so with `records=False`.
            if stage_id in self.recorded_failures:
                self.observed(stage_id, claimed_by=True,
                              start_failure=self.recorded_failures[stage_id])
            raise held
        # W81857: A SUCCESSFUL START MAY ATTACH THE RUNTIME TO THE CANONICAL
        # OBSERVATION, because the real one does -- `request_runtime_start`
        # journals the attachment, so the very next canonical read sees it.
        #
        # IT IS OPT-IN AND THE DEFAULT DID NOT MOVE. Cases written before this
        # existed drive the launch pass by leaving the observation empty and
        # asking again, and quietly attaching for all of them would have
        # rewritten what those cases measure. `attaches` is how a case says it
        # is about what happens AFTER a container is up.
        if stage_id in self.attaching:
            self.observed(stage_id, claimed_by=True,
                          runtime={"attempt_id": stage["attempt_id"],
                                   "runtime_id": held.get("runtime_id"),
                                   "execution_runtime": "running",
                                   "cleanup": None, "assignment": None})
        return held

    def dispatch(self, stage, job):
        """The deployment's exchange publication, as a case configures it.

        DEFAULT IS A REFUSAL, and it is the honest one: a deployment given no
        dispatch cannot command a container, which is exactly what
        `ManagerOperations` answers with no `dispatch_exchange`. A case that
        wants a commanded worker says so with `commands`.

        A PERFORMED PUBLICATION MOVES THE OBSERVATION, because the real one
        does: the command is a durable file, so the very next scan of the
        exchange reports `waiting`. A fake that published and answered
        `not-requested` would make every level-triggered pass look like it
        publishes twice.
        """
        stage_id = stage["stage_id"]
        self.calls.append(("dispatch", stage_id))
        answer = self._exchange_act("dispatch", stage_id, self.commands)
        if not self._exchange_of(stage_id):
            self.commanded(stage_id, answer=answer)
        return answer

    def _exchange_of(self, stage_id):
        held = self.observations.get(stage_id)
        return None if held is None else held.get("exchange")

    def conclude(self, stage, job):
        stage_id = stage["stage_id"]
        self.calls.append(("conclude", stage_id))
        return self._exchange_act("conclude", stage_id, self.endings)

    def _exchange_act(self, act, stage_id, configured):
        held = configured.get(stage_id)
        if held is None:
            raise ContractRefusal(
                "refused", "capability",
                f"this fake deployment was given no {act} for {stage_id}")
        if isinstance(held, BaseException):
            raise held
        return held

    def observe(self, stage):
        return self.observations.get(stage["stage_id"], _unobserved())

    def refresh_runtime(self, stage):
        """The deployment's engine refresh, as a case configures it.

        DEFAULT IS `None` AND NOT A REFUSAL, because that is what
        `ManagerOperations` answers with no `refresh_runtime`: a control plane
        with no engine is a real deployment, and silence about a runtime is not
        a claim that one is gone. A case that wants a refreshed -- or a
        refusing -- runtime says so with `refreshed`.

        A PERFORMED REFRESH MOVES THE OBSERVATION, because the real one does:
        the reconciliation WRITES what it saw, so the very next canonical read
        reports it. A fake that answered `quiescent` and left the observation
        saying `running` would let a case pass that the production composition
        could not.

        RECORDED BESIDE `calls`, NOT IN IT, and that is a boundary rather than
        tidiness. `calls` is this fake's record of the ACTS a pass performed,
        and cases in several modules -- including ones this Work has no
        authority to edit -- assert it exactly to prove that a given pass
        performed nothing. A per-tick observation every live stage receives
        would change what all of those assertions mean.
        """
        stage_id = stage["stage_id"]
        self.refreshed_calls.append(stage_id)
        held = self.refreshes.get(stage_id)
        if held is None:
            return None
        if isinstance(held, BaseException):
            raise held
        # THE REAL SEAM'S OWN RULE, applied here rather than reimplemented.
        # W85500 review 2026-09-04T14-27-54Z [P1] is about what the manager
        # accepts from a deployment; a fake that was MORE permissive than
        # `ManagerOperations` would let a case pass that production could not,
        # which is the one thing a stand-in must never do.
        from baton_v12.job_manager.delegation import _refreshed

        held = _refreshed(held, stage)
        seen = self.observations.get(stage_id)
        if held is not None and seen is not None \
                and seen.get("runtime") is not None:
            runtime = dict(seen["runtime"])
            runtime["execution_runtime"] = held["execution_runtime"]
            self.observations[stage_id] = dict(seen, runtime=runtime)
        return held

    # -- what a case sets ----------------------------------------------------

    def refreshed(self, stage_id, execution_runtime="quiescent"):
        """What this stage's engine refresh answers on the next sweep."""
        self.refreshes[stage_id] = {"execution_runtime": execution_runtime}

    def refuse(self, stage_id, act, refusal):
        self.refusals[(stage_id, act)] = refusal

    def commanded(self, stage_id, answer=None, state="waiting", **members):
        """This stage's exchange, in the REAL reader's shape.

        The default is the state a published command with no worker receipt
        projects, because that is the interesting one: it is the first moment
        this control plane has done everything it owes and the container has
        not answered.
        """
        if not isinstance(answer, BaseException):
            self.commands[stage_id] = {"published": True} if answer is None \
                else answer
        held = dict(self.observations.get(stage_id) or _unobserved())
        held["exchange"] = {"transport": "baton.worker-exchange/1",
                            "sequence_id": f"sequence-{stage_id}",
                            "state": state, **members}
        self.observations[stage_id] = held

    def observed(self, stage_id, **members):
        """One stage's canonical observation, in the REAL reader's shape.

        `claimed_by=True` is the case saying "this stage's OWN offer holds the
        attempt's claim", and the fixture spells the identity so no case has to
        carry the derivation. A case about another store's offer says so by
        naming that offer id, which is the whole distinction the observation
        exists to carry.
        """
        held = _unobserved()
        held.update(members)
        if held["claimed_by"] is True:
            from baton_v12.job_manager.episodes import identities

            held["claimed_by"] = identities(UUID, stage_id, 1)[0]
        self.observations[stage_id] = held

    def frozen(self, stage_id, disposition, artifacts=None,
               execution_runtime="ended", cleanup="complete"):
        """One frozen result, with the two axes a case may need to steer.

        W81857 review [P1] made `cleanup` a fact this projection reads: the
        ending is owed until the manager's own cleanup axis is terminal, so a
        fixture that always answered `None` there could only ever model a
        HALF-FINISHED ending.

        IT DEFAULTS TO `complete`, which is what every case written before the
        ending existed meant by "this stage is frozen": a finished stage. A
        case about the window between the freeze and the last step says so by
        naming an unsettled value, and re-review 2026-09-04T07-00-54Z is why
        that is now the explicit half -- an unsettled default would have made
        every pre-existing terminal expectation mean something its author
        never wrote.

        AND THE EXCHANGE SURVIVES. `observed` rebuilds the observation from
        the unobserved shape, so freezing used to erase whatever exchange a
        case had set -- which made a frozen stage look like one this control
        plane holds no exchange read for, and hid exactly the window the
        review reproduced.
        """
        from baton_v12.job_manager.episodes import identities

        _offer_id, attempt_id = identities(UUID, stage_id, 1)
        held = self.observations.get(stage_id) or {}
        self.observed(stage_id, claimed_by=True,
                      exchange=held.get("exchange"),
                      runtime={"attempt_id": attempt_id,
                               "runtime_id": "runtime-1",
                               "execution_runtime": execution_runtime,
                               "cleanup": cleanup, "assignment": None},
                      output={"attempt_id": attempt_id,
                              "result_id": f"result-{stage_id}",
                              "disposition": disposition,
                              "manifest_digest": "sha256:" + "c" * 64,
                              "freeze_operation_id": "freeze:1",
                              "frozen_at": NOW,
                              "artifacts": artifacts if artifacts is not None
                              else []})

    def committed(self, act, offer_id, result=None, intent=None):
        """Pretend the manager already committed one act, as a restart would
        find it."""
        import json

        from baton_v12.job_manager import canonical_operation

        operation_id = canonical_operation(act, offer_id)
        self.journal[operation_id] = {
            "operation_id": operation_id, "kind": f"offer.{act}",
            "signature": signature_of(act, intent), "state": "committed",
            "result": json.dumps(result if result is not None
                                 else {"offer_id": offer_id}),
            "refusal": None, "settled_at": NOW}
        return operation_id

    def _act(self, act, stage, result, intent=None):
        import json

        self.calls.append((act, stage["stage_id"]))
        held = self.refusals.pop((stage["stage_id"], act), None)
        if held is not None:
            if getattr(held, "durable", False):
                operation_id = self.canonical_operation(act,
                                                        stage["offer_id"])
                self.journal[operation_id] = {
                    "operation_id": operation_id, "kind": f"offer.{act}",
                    # A DURABLE REFUSAL IS JOURNALLED UNDER THE REQUEST'S OWN
                    # SIGNATURE, so a refused offer is still recognisable as
                    # this stage's act rather than unreadable to the proof.
                    "signature": signature_of(act, intent), "state": "refused",
                    "result": None,
                    "refusal": json.dumps({"category": held.category,
                                           "code": held.code,
                                           "message": held.message,
                                           "durable": True}),
                    "settled_at": NOW}
            raise held
        self.committed(act, stage["offer_id"], result, intent=intent)
        return None
