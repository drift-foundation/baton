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
            "output": None}


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

    def store(self, incarnation="jobs-1"):
        store = JobStore.open(self.job_path, incarnation=incarnation,
                              clock=self.clock)
        self.addCleanup(store.close)
        return store

    def control(self, incarnation="manager-1"):
        control = ControlStore.open(self.control_path,
                                    incarnation=incarnation, clock=self.clock)
        self.addCleanup(control.close)
        certify_profile(control, "runtime", "reference", PROFILE)
        return control

    def operations(self, control=None, port=None):
        from baton_v12.worker_manager import AuthorityPort

        control = control if control is not None else self.control()
        port = port if port is not None else AuthorityPort(
            self.session, fake_claim_signature)
        return ManagerOperations(control, port, mint_bearer=self.mint,
                                 deliver_bearer=self.deliver)

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
        self.journal = {}
        self.observations = {}
        self.refusals = {}
        self.calls = []

    def canonical_operation(self, act, offer_id):
        from baton_v12.job_manager import canonical_operation

        return canonical_operation(act, offer_id)

    def receipt_of(self, operation_id):
        return self.journal.get(operation_id)

    def recover(self, *, now):
        self.calls.append(("recover", now))
        return {"abandoned": [], "recoverable": []}

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

    def observe(self, stage):
        return self.observations.get(stage["stage_id"], _unobserved())

    # -- what a case sets ----------------------------------------------------

    def refuse(self, stage_id, act, refusal):
        self.refusals[(stage_id, act)] = refusal

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
            held["claimed_by"] = f"offer:{stage_id}"
        self.observations[stage_id] = held

    def frozen(self, stage_id, disposition, artifacts=None):
        self.observed(stage_id, claimed_by=True,
                      runtime={"attempt_id": f"attempt:{stage_id}",
                               "runtime_id": "runtime-1",
                               "execution_runtime": "ended",
                               "cleanup": None, "assignment": None},
                      output={"attempt_id": f"attempt:{stage_id}",
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
