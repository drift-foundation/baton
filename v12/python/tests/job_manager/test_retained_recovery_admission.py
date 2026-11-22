"""W385624 Stage 1-B — the owner's decision, and the one successor it admits.

WHAT THESE CASES ARE ABOUT. A retained verification failure that Stage 1-A has
already analysed and delivered to the owner: the supported command an owner
reads it with, the supported command they decide it with, and the ONE linked
verification/review-only successor an approval admits -- a durable Job on the
failed Job's own Work whose stage set carries no implementation.

WHAT IS REAL HERE, and the list is what makes this evidence rather than a
demonstration. The owner command is the installed one, reached through
`tools.job_manager.main` with an operator's own argv, so the parsing, the
operand checks, the store roles, the owner-port composition and the printed
answer are the deployment's. The AUTHORIZATION IS PRODUCTION: a real Authority
store, created by its own API, holding a real Work with its own effective
scope and a real `approve` grant made in that scope exactly as
`bootstrap._compose` makes it -- so a wrong actor and a wrong scope are
refused by the Authority's own seam and not by a stand-in. The Job store, its
submission, its stages, its cancellation fence, its LIM-5 control and its
operations journal are real and disposable. The control store, its retained
result manifests, its MEASURED candidate tree on disk-backed storage and its
composed typed failure cause are Stage 1-A's own real fixture, inherited from
`tests.job_manager.test_retained_failure_analysis` by module attribute.

WHAT IS FAKED, AND ONLY WHERE A DEPLOYMENT WOULD SUPPLY ONE: the three owner
ports a deployment composes over its own installation -- the HOST's record of
each prior attempt's runtime and workspace token, the deployment
configuration's additive binding and servability selector, and the instance
guard -- plus the execution of the approved verifier itself, which is
W385625's and is driven here through the supported `record_verification`
boundary. Each fake answers one fact at a time and RECORDS what it was asked,
which is what lets a case assert that the submitted digests and the stage's
own profile reached the selector rather than that an answer came back. There
is no provider, no model, no adapter, no image and no container in this file.

WHAT IS DELIBERATELY ABSENT. No verifier is executed, no retained candidate is
materialized into a workspace and no candidate is handed to review: those are
W385625's, and a case here that performed one would be implementing it. What
is asserted instead is that the admission SAYS SO -- `readiness` names the
acts still owed -- and that nothing in this file writes a candidate, a
verifier input or an execution state, which one case proves by comparing the
whole control store's bytes across the entire path.
"""

import concurrent.futures
import hashlib
import io
import json
import os
import pathlib
import threading
import unittest

from baton_v12.contracts import ContractRefusal, digest
from baton_v12.job_manager import (JobStore, cancellation, failure_analysis,
                                   job_control, retained_recovery,
                                   submission)

from tests.job_manager import test_retained_failure_analysis as stage_a
from tests.job_manager.fixtures import NOW, WORK_A

OWNER = stage_a.OWNER
OWNER_PRINCIPAL = "principal:slawomir"
INTRUDER = "baton.claude"
ROUTE = "baton.impl"
WORK_SCOPE = "scope:w385624-recovery"
LATER = stage_a.LATER
# Past the approved 9960-second Job bound measured from the accepted
# admission, queue time included, and one instant after that.
EXPIRED = "2026-09-02T02:46:00.000Z"
AFTER = "2026-09-02T03:00:00.000Z"

# The owner-approved definition record this Work implements, by its canonical
# repository path. READ IN A CASE AND NOT IN THE PRODUCT, exactly as Stage
# 1-A's is: the module holds the definition as data and proves its own digest,
# and this file is what binds that held copy to the bytes M385612 published.
# Declared in `tools/parallel_test.py` `CONSUMED_INPUTS`, which is what makes
# the run's source identity cover it.
APPROVED_PROFILE = (
    pathlib.Path(__file__).resolve().parents[4] / "work" / "records" / "2026"
    / "08" / "finding-v12-isolated-agent-workers" / "findings"
    / "finding-v12-team-hierarchy-shared-approvers" / "evidence"
    / "stage-1-contract-385615" / "stage1-verification-review-1.json")
APPROVED_PROFILE_DIGEST = (
    "5a6a420e416caab0942f9709939ae01f1f2d9dabbd13e09ff3b03ea08d2932fb")

# The exact correction the joined acceptance names: the accidental newline
# removed from the original argv, and nothing else about the command changed.
CORRECTED = ["bash", "-c", "exec python3 -m unittest -v x"]
CONTEXT = "sha256:" + "e" * 64

# WHICH DISPOSABLE INSTANCE THE STAND-IN PORTS ANSWER FOR, set by each case to
# its own temporary root and its own real store paths. Review R17/R18 of
# W359719 made the instance part of what every owner port declares, so a
# fixture naming a fictional deployment would be declaring another one --
# which is exactly what `one_instance` refuses.
CURRENT = {}


def ceased(runtime="destroyed", cleanup="retained", token=None):
    """One attempt the host accounts for as over, with its resource back."""
    return {"runtime": {"attempt_id": None, "runtime_id": "runtime-1",
                        "execution_runtime": runtime, "cleanup": cleanup,
                        "assignment": None},
            "token": token if token is not None else {"returned": True}}


class FakeExclusion:
    """The host's answer, one fact at a time, with every call recorded."""

    def __init__(self, answer=None, identity=None):
        self.answer = answer
        self.asked = []
        self._identity = identity

    def instance(self):
        return self._identity or CURRENT.get("identity")

    def evidence_of(self, attempt_ids):
        self.asked.append(tuple(attempt_ids))
        if callable(self.answer):
            held = self.answer(attempt_ids)
        elif self.answer is None:
            held = {one: ceased() for one in attempt_ids}
        else:
            held = {one: self.answer for one in attempt_ids}
        held = dict(held)
        held["host"] = CURRENT.get("identity", {}).get("control_store")
        return held


class FakeBinding:
    """The deployment, with the additive bind recorded rather than performed."""

    def __init__(self, bound=(), serving=("review-worker-1",),
                 work_id=WORK_A, identity=None, unservable=0):
        self.bound = {one: {"job_id": one, "job_work_id": work_id}
                      for one in bound}
        self._serving = serving
        self._work_id = work_id
        self.added = []
        self.asked = []
        self.tasks = []
        self._identity = identity
        # HOW MANY TIMES THIS DEPLOYMENT CANNOT SERVE THE STAGE YET, which is
        # the fault cut between the reservation and the submission: an
        # admission refused there has already reserved an identity and
        # published a binding, and the next attempt must RESUME rather than
        # start again.
        self.unservable = unservable

    def instance(self):
        return self._identity or CURRENT.get("identity")

    def binding_of(self, job_id):
        return self.bound.get(job_id)

    def bind(self, job_id, *, like, work_id):
        self.added.append((job_id, like, work_id))
        self.bound[job_id] = {"job_id": job_id, "job_work_id": work_id,
                              "source_worker_id": "impl-worker-1"}
        return self.bound[job_id]

    def serving(self, job_id, *, stage, job, task=None):
        # THE FAKE RECORDS WHAT IT WAS ASKED, because W359719's review R3 was
        # about the OPERANDS rather than the answer: a case asserts that the
        # SUBMITTED digests and the stage's own profile reached this port.
        self.asked.append((job_id, dict(stage), dict(job)))
        self.tasks.append(task)
        if self.unservable > 0:
            self.unservable -= 1
            return []
        return list(self._serving)


class FakeOwnership:
    """The instance guard and this admission's invocation lock, in memory.

    REAL ENOUGH TO DECIDE A RACE. `held` counts, and `invocation` is a genuine
    per-identity lock so a case about two concurrent admissions is about one
    rather than about which thread happened to finish first.
    """

    def __init__(self, holder="control.sqlite3", refusal=None, locks=None,
                 identity=None):
        self.holder = holder
        self.refusal = refusal
        self.held_count = 0
        self.released = 0
        self.locks = {} if locks is None else locks
        self._identity = identity

    def instance(self):
        return self._identity or CURRENT.get("identity")

    def held(self):
        import contextlib

        @contextlib.contextmanager
        def holding():
            if self.refusal is not None:
                raise self.refusal
            self.held_count += 1
            try:
                yield self
            finally:
                self.released += 1

        return holding()

    def invocation(self, job_id):
        import contextlib

        lock = self.locks.setdefault(job_id, threading.Lock())

        @contextlib.contextmanager
        def owning():
            if not lock.acquire(timeout=30):             # pragma: no cover
                raise ContractRefusal(
                    "refused", "precondition",
                    f"another admission of {job_id!r} is in flight")
            try:
                yield
            finally:
                lock.release()

        return owning()


class WorkPort:
    """The Authority's own answer about the Work this successor runs under.

    THE REAL AUTHORITY BEHIND IT. This is the production
    `fresh_attempt_ports.WorkAuthorization` reduced to the one read a recovery
    admission makes -- it never creates a Work -- so the handle it wraps is
    the case's real Authority and the answer is that store's own projection.
    """

    def __init__(self, authority, identity=None):
        self._authority = authority
        self._identity = identity

    def instance(self):
        return self._identity or CURRENT.get("identity")

    def work_of(self, work_id):
        from baton_v12.authority import Refusal

        try:
            return self._authority.project_work(work_id)
        except Refusal:
            if self._authority.work_creation(work_id) is None:
                return None
            raise


def owners(request):
    """The owner-port factory the command is pointed at by `--owners`.

    THE PRODUCTION SHAPE, with the three host/deployment/instance ports stood
    in for. `owner` is the real `tools.recovery_decision.OwnerAuthorization`
    over the case's real Authority store, so every authorization answer in
    this file is the Authority's own decision document; `authorization` is the
    same store's Work projection. What is faked is cessation, binding and the
    instance guard, which is where a deployment's own host would answer.
    """
    from baton_v12.authority import Authority
    from tools.recovery_decision import OwnerAuthorization

    authority = Authority.open_readonly(
        request["authority"],
        expected_authority_uuid=request["authority_uuid"])
    held = CURRENT.setdefault("ports", {})
    identity = CURRENT["identity"]
    return {"owner": OwnerAuthorization(authority,
                                        participant=request["participant"]),
            "authorization": WorkPort(authority, identity=identity),
            "exclusion": held.setdefault("exclusion",
                                         FakeExclusion(identity=identity)),
            "binding": held.setdefault("binding",
                                       FakeBinding(identity=identity)),
            "ownership": held.setdefault("ownership",
                                         FakeOwnership(identity=identity)),
            "release": authority.dispose}


class RecoveryCase(stage_a.AnalysisCase):
    """One delivered owner item, a real Authority, and the owner's command.

    Stage 1-A's whole fixture is inherited: the control store, its development
    line, its writer, the measured candidate tree in real custody, the typed
    failure cause and the scripted analysis. What this adds is the Authority
    the decision is authorized by, the stand-in owner ports, and the two
    helpers that drive the installed command.
    """

    def setUp(self):
        from baton_v12.authority import Authority

        super().setUp()
        self.authority_path = os.path.join(self.root, "authority.sqlite3")
        authority = Authority.create(self.authority_path,
                                     authority_uuid=self.AUTHORITY)
        self.addCleanup(authority.dispose)
        # THE WORK'S OWN EFFECTIVE SCOPE, deliberately NOT the deployment's.
        # W16821 item 2 makes the scope authority-owned and supplied at
        # creation, and a Work that happened to carry the deployment default
        # would make "the grant is in the WORK's scope" unfalsifiable -- a
        # grant made with no scope at all would satisfy it.
        authority.create_work(WORK_A, ROUTE, operation_id="bootstrap-job-a",
                              contract="v12-assignment-1",
                              scope=WORK_SCOPE)
        self.work_row = authority.project_work(WORK_A)
        # THE DEPLOYMENT'S OWN GRANTS, in the bound Work's own scope and
        # through the Authority's own API -- `bootstrap.OWNER_GRANTS` for the
        # selected human owner, and no `verify` or `review` grant, so a case
        # about the wrong capability is about a real absence.
        authority.bind_endpoint(OWNER, OWNER_PRINCIPAL)
        for capability in ("approve", "integrate", "close"):
            authority.grant_capability(OWNER, capability,
                                       scope=self.work_row["scope"])
        # AND THE IMPLEMENTER IS A REAL PARTICIPANT WITH REAL GRANTS THAT ARE
        # NOT THIS ONE. An intruder with no grant at all would be refused by
        # the first check it met; one that holds `review` in the same scope is
        # the case that matters, because it proves the capability is the thing
        # being asked about rather than membership.
        authority.add_route_handler(ROUTE, INTRUDER)
        authority.grant_capability(INTRUDER, "review",
                                   scope=self.work_row["scope"])
        self.authority = authority
        CURRENT.clear()
        CURRENT["identity"] = {
            "root": os.path.join(self.root, "instance"),
            "job_store": os.path.realpath(self.jobs.database),
            "control_store": os.path.realpath(self.control.database),
            "authority_store": os.path.realpath(self.authority_path),
            "authority_uuid": self.AUTHORITY}
        os.makedirs(CURRENT["identity"]["root"], exist_ok=True)
        self.addCleanup(CURRENT.clear)

    # -- the installed command ----------------------------------------------

    def argv(self, command, *extra):
        return [command,
                "--store", self.jobs.database,
                "--authority-uuid", self.AUTHORITY,
                "--incarnation", "recovery-1",
                "--control", self.control.database,
                "--authority", self.authority_path,
                "--instance", CURRENT["identity"]["root"],
                "--owners", "tests.job_manager."
                            "test_retained_recovery_admission:owners",
                *extra]

    def command(self, *argv, clock=None):
        """Run the installed owner command and return `(code, document)`."""
        from tools import job_manager

        said = io.StringIO()
        code = job_manager.main(list(argv), clock=clock or (lambda: NOW),
                                stream=said)
        text = said.getvalue()
        return code, (json.loads(text) if text.strip() else None)

    def read(self, key, *extra):
        code, document = self.command(*self.argv("recovery-item",
                                                 "--failure", key, *extra))
        self.assertEqual(code, 0)
        return document

    def decide_argv(self, key, read, *, decision_id="D1",
                    disposition="--approve", original=None, corrected=None,
                    stages=None, participant=OWNER, lineage=None, **changed):
        """The operands an owner copies out of what they were just shown.

        EVERY VALUE DEFAULTS TO THE READ'S OWN, which is what makes a negative
        case a one-operand change: `candidate_digest=...` is the only thing
        that differs between the positive path and the wrong-digest refusal,
        so the refusal cannot be passing for another reason.
        """
        expected = dict(read["expected"])
        held = {"decision-id": decision_id, "participant": participant,
                "expect-failure-digest": expected["failure_digest"],
                "expect-report-digest": expected["report_digest"],
                "expect-candidate-base": expected["candidate_base"],
                "expect-candidate-head": expected["candidate_head"],
                "expect-candidate-digest":
                    expected["candidate_content_digest"],
                "context-digest": CONTEXT,
                "profile": read["profile"]["profile"],
                "profile-digest": read["profile"]["digest"]}
        if lineage is not None:
            held.update({"prior-successor": lineage["successor_job_id"],
                         "prior-verification-attempt":
                             lineage["verification_attempt_id"],
                         "prior-verification-digest":
                             lineage["verification_result_digest"]})
        held.update({one.replace("_", "-"): value
                     for one, value in changed.items()})
        flat = [f"--{one}={value}" for one, value in held.items()
                if value is not None]
        for word in (expected["original_argv"] if original is None
                     else original):
            flat.append(f"--original-verification={word}")
        for word in (CORRECTED if corrected is None else corrected):
            flat.append(f"--corrected-verification={word}")
        for word in (list(retained_recovery.FULL_STAGES) if stages is None
                     else stages):
            flat.append(f"--stage={word}")
        return self.argv("recovery-decide", "--failure", key, disposition,
                         *flat)

    def decide(self, key, read, *, clock=None, **changed):
        return self.command(*self.decide_argv(key, read, **changed),
                            clock=clock)

    # -- the delivered Stage 1-A item ---------------------------------------

    def delivered(self, number=1):
        """Stage 1-A's whole path, through its own accepted operations."""
        return self.whole_path(number=number)

    def journal(self, kind, store=None):
        store = store if store is not None else self.jobs
        return [row["operation_id"] for row in store._connection.execute(
            "SELECT operation_id FROM operations WHERE kind = ? ORDER BY "
            "operation_id", (kind,))]

    def control_bytes(self):
        with open(self.control.database, "rb") as handle:
            return hashlib.sha256(handle.read()).hexdigest()

    def approved(self, read, *, decision_id, stages=None, lineage=None,
                 now=NOW):
        """One APPROVED decision and no admission, through the operation.

        USED ONLY WHERE THE ADMISSION ITSELF IS UNDER TEST. The command above
        performs both acts, which is what an owner does; a case about a
        refusal INSIDE the admission needs a committed approval it can then
        drive the admission against with one port replaced.
        """
        from tools.recovery_decision import OwnerAuthorization

        expected = dict(read["expected"])
        return retained_recovery.decide(
            self.jobs, self.control, key=read["failure_key"],
            decision_id=decision_id, disposition="approved",
            authorization=OwnerAuthorization(self.authority,
                                             participant=OWNER),
            expected=expected,
            correction={"argv": CORRECTED, "context_digest": CONTEXT},
            profile=read["profile"]["profile"],
            profile_digest=read["profile"]["digest"],
            stages=list(retained_recovery.FULL_STAGES) if stages is None
            else stages,
            lineage=lineage, now=now)

    def job_row(self, job_id):
        """The Job row this store holds under one identity, or `None`.

        READ DIRECTLY BECAUSE ABSENCE IS THE QUESTION. `submission.job_of`
        REFUSES an unknown Job on purpose -- a stage row naming a Job the
        store does not hold means the rows were changed underneath a process
        -- so it is the wrong reader for "was anything admitted at all".
        """
        return self.jobs._connection.execute(
            "SELECT job_id FROM jobs WHERE job_id = ?", (job_id,)).fetchone()

    def stand_ins(self):
        """The three stand-in owner ports this case's command composed."""
        return CURRENT.setdefault("ports", {})


# -- 1. the ordinary outcome -------------------------------------------------


class TheOwnerReadsTheItemAndTheApprovalAdmitsOneSuccessor(RecoveryCase):
    """The first usable result of 1-B, through the installed command."""

    def test_the_read_presents_every_fact_a_decision_must_bind(self):
        held = self.delivered()
        read = self.read(held["key"])
        self.assertEqual(read["schema"], retained_recovery.READ_SCHEMA)
        self.assertEqual(read["failure_key"], held["key"])
        self.assertEqual(read["disposition"], "delivered")
        self.assertEqual(read["owner_item"]["outcome"], "reported")
        # THE ORIGINAL FAILED VERIFIER, as the words it actually was.
        self.assertEqual(read["original_verification"]["argv"],
                         ["bash", "-c", "exec python3 -m unittest -v x\n"])
        self.assertEqual(read["original_verification"]["status"], 1)
        # AND THE EXACT PROPOSED CORRECTION AND ITS CONTEXT, out of the
        # delivered report's own bytes.
        self.assertEqual(read["proposed_correction"],
                         {"argv": CORRECTED, "context_digest": CONTEXT})
        self.assertEqual(read["report"]["document"], held["report"])
        # THE FOUR DIGESTS AND THE CANDIDATE, bound to bytes and not a name.
        self.assertEqual(read["expected"]["failure_digest"],
                         held["observed"]["failure"]["input_digest"])
        self.assertEqual(read["expected"]["report_digest"],
                         failure_analysis.report_of(
                             self.jobs, held["key"])["report_digest"])
        self.assertEqual(read["expected"]["candidate_content_digest"],
                         held["failed"]["content"]["tree_digest"])
        self.assertEqual(read["expected"]["candidate_base"],
                         read["candidate"]["base"])
        self.assertTrue(read["evidence"]["valid"])
        # THE APPROVED PROFILE AND THE SELECTABLE SCOPE.
        self.assertEqual(read["profile"]["profile"],
                         retained_recovery.SUCCESSOR_PROFILE)
        self.assertEqual(read["profile"]["digest"],
                         "sha256:" + APPROVED_PROFILE_DIGEST)
        self.assertEqual(read["selectable_stages"],
                         [["verification", "review"], ["review"]])
        self.assertEqual(read["decisions"], [])
        self.assertEqual(read["successors"], [])

    def test_the_read_says_whether_the_asker_may_decide_at_all(self):
        held = self.delivered()
        mine = self.read(held["key"], "--participant", OWNER)
        self.assertTrue(mine["authorization"]["holds"])
        self.assertEqual(mine["authorization"]["principal"], OWNER_PRINCIPAL)
        self.assertEqual(mine["authorization"]["effective_scope"],
                         self.work_row["scope"])
        self.assertEqual(mine["authorization"]["role"], "approve")
        theirs = self.read(held["key"], "--participant", INTRUDER)
        self.assertFalse(theirs["authorization"]["holds"])
        self.assertEqual(theirs["authorization"]["why"]["code"], "denied")

    def test_one_approval_admits_one_durable_review_only_successor(self):
        held = self.delivered()
        read = self.read(held["key"])
        code, answer = self.decide(held["key"], read)
        self.assertEqual(code, 0, answer)
        decision, successor = answer["decision"], answer["successor"]
        self.assertTrue(answer["admitted"])
        self.assertEqual(decision["disposition"], "approved")
        self.assertEqual(decision["owner"]["principal"], OWNER_PRINCIPAL)
        self.assertEqual(decision["owner"]["effective_scope"],
                         self.work_row["scope"])
        self.assertEqual(decision["correction"],
                         {"argv": CORRECTED, "context_digest": CONTEXT})
        self.assertEqual(decision["stages"], ["verification", "review"])
        self.assertEqual(decision["profile"],
                         retained_recovery.SUCCESSOR_PROFILE)
        # ONE ACTUAL DURABLE SUCCESSOR, read back out of the store.
        job_id = successor["job_id"]
        self.assertEqual(job_id, "recovery-D1")
        self.assertIsNotNone(submission.job_of(self.jobs, job_id))
        self.assertEqual(successor["stage_ids"], [f"{job_id}/review"])
        self.assertEqual(
            [row["kind"] for row in submission.stages_of(self.jobs, job_id)],
            ["review"])
        self.assertEqual(successor["prior_job_id"], "job-a")
        self.assertEqual(successor["work_id"], WORK_A)
        self.assertEqual(successor["work"], {"work_id": WORK_A,
                                             "disposition": "reused",
                                             "status": "open"})
        # THE EXACT RETAINED CANDIDATE AND THE APPROVED CORRECTION.
        self.assertEqual(successor["candidate"]["tree_digest"],
                         held["failed"]["content"]["tree_digest"])
        self.assertEqual(successor["correction"]["argv"], CORRECTED)
        # THE OWNER-APPROVED FINITE BOUNDS, and the LIM-5 control the
        # submission journalled for the Job.
        self.assertEqual(successor["bounds"]["profile"],
                         retained_recovery.SUCCESSOR_PROFILE)
        self.assertEqual(successor["bounds"]["overall_job_seconds"], 9960)
        self.assertEqual(successor["bounds"]["each_stage_seconds"], 4800)
        self.assertEqual(
            successor["bounds"]["verification_command_seconds"], 900)
        self.assertEqual(
            successor["bounds"]["review_provider_invocation_seconds"], 3600)
        self.assertEqual(successor["bounds"]["automatic_retries"], 0)
        self.assertEqual(successor["control"]["profile"],
                         retained_recovery.SUCCESSOR_PROFILE)
        self.assertEqual(successor["control"]["resolved"]["job_seconds"],
                         9960)
        # AND IT SAYS WHAT IS STILL OWED rather than implying it happened.
        self.assertEqual(successor["readiness"]["verification"], "owed")
        self.assertEqual(successor["readiness"]["review"], "blocked")
        self.assertEqual(successor["verification_attempt_id"],
                         "verification-recovery-D1")

    def test_the_admission_asked_its_owners_the_submitted_specification(self):
        held = self.delivered()
        read = self.read(held["key"])
        self.decide(held["key"], read)
        binding = self.stand_ins()["binding"]
        self.assertEqual(binding.added, [("recovery-D1", "job-a", WORK_A)])
        job_id, stage, job = binding.asked[-1]
        self.assertEqual(job_id, "recovery-D1")
        self.assertEqual(stage["kind"], "review")
        # THE REVIEW STAGE'S OWN PROFILE, carried from the failed Job's own
        # review stage rather than built out of whatever worker answered.
        prior = json.loads(self.jobs._connection.execute(
            "SELECT document FROM submissions WHERE submission_id = 'sub-1'"
        ).fetchone()[0])["jobs"][0]
        wanted = [one for one in prior["stages"]
                  if one["kind"] == "review"][0]
        self.assertEqual(stage["profile_name"], wanted["profile_name"])
        self.assertEqual(stage["profile_digest"], wanted["profile_digest"])
        self.assertEqual(job["input_digest"], prior["input_digest"])
        # AND THE HOST WAS ASKED ABOUT THE FAILED ATTEMPT, twice: once before
        # the reservation and once after it.
        exclusion = self.stand_ins()["exclusion"]
        self.assertEqual(len(exclusion.asked), 2)
        for asked in exclusion.asked:
            self.assertIn(held["failed"]["attempt_id"], asked)
        # AND THE INSTANCE WAS HELD FOR THE WHOLE OF IT AND RELEASED. The
        # guard is what makes two admissions in two processes impossible and
        # what makes the host read above an EXCLUSION rather than a coherent
        # observation -- the one writer that could change those answers is the
        # manager whose guard this held.
        ownership = self.stand_ins()["ownership"]
        self.assertEqual(ownership.held_count, 1)
        self.assertEqual(ownership.released, 1)
        self.assertEqual(sorted(ownership.locks), ["recovery-D1"])

    def test_a_finite_analysis_ending_is_decidable_with_no_report(self):
        """THE FOUR ENDINGS STAGE 1-A DELIVERS DIRECTLY TO THE OWNER.

        An analysis that failed, expired, was cancelled or whose cessation is
        unknown preserved its partial evidence and delivered NO diagnosis --
        so there is no report digest to bind, and requiring one would make
        exactly the endings the contract routes straight to Slawomir
        undecidable. The owner's own correction then stands on its own, and
        the decision records WHICH ending it was taken on.
        """
        failed = self.failed_attempt(3)
        seen = self.observed(failed)
        key = seen["failure"]["failure_key"]
        failure_analysis.deliver_endpoint(
            self.jobs, self.control, key=key, outcome="analysis-failed",
            why="the dispatched analysis froze its result unable",
            destination=OWNER, now=LATER)
        read = self.read(key)
        self.assertEqual(read["owner_item"]["outcome"], "analysis-failed")
        self.assertIsNone(read["expected"]["report_digest"])
        self.assertIsNone(read["report"]["document"])
        self.assertIsNone(read["proposed_correction"])

        code, said = self.decide(key, read, decision_id="E1")
        self.assertEqual(code, 0, said)
        self.assertEqual(said["decision"]["item_outcome"], "analysis-failed")
        self.assertIsNone(said["decision"]["expected"]["report_digest"])
        self.assertIsNone(said["decision"]["proposed_digest"])
        self.assertEqual(said["successor"]["job_id"], "recovery-E1")
        self.assertEqual(said["successor"]["stage_ids"],
                         ["recovery-E1/review"])
        # AND NAMING A REPORT DIGEST FOR AN ENDING THAT DELIVERED NONE IS
        # REFUSED, which is what keeps the two cases apart.
        code, said = self.decide(key, read, decision_id="E2",
                                 expect_report_digest="sha256:" + "5" * 64)
        self.assertEqual(code, 1, said)
        self.assertIsNone(retained_recovery.decision_of(self.jobs, "E2"))

    def test_the_held_definition_is_the_bytes_the_owner_published(self):
        """THE PRODUCT'S COPY AND THE DOSSIER RECORD, compared."""
        published = APPROVED_PROFILE.read_bytes()
        self.assertEqual(
            retained_recovery.SUCCESSOR_DEFINITION_BYTES, published)
        self.assertEqual(hashlib.sha256(published).hexdigest(),
                         APPROVED_PROFILE_DIGEST)
        self.assertEqual(retained_recovery.SUCCESSOR_PROFILE_DIGEST,
                         "sha256:" + APPROVED_PROFILE_DIGEST)
        # AND THE CONTROL PROFILE THE ADMITTED JOB IS ENFORCED UNDER SAYS THE
        # SAME FIVE THINGS.
        enforced = job_control.resolved(
            retained_recovery.SUCCESSOR_PROFILE)
        self.assertEqual(enforced["job_seconds"], 9960)
        self.assertEqual(enforced["stage_seconds"], 4800)
        self.assertEqual(enforced["provider_turn_seconds"], 3600)
        self.assertEqual(enforced["verification_command_seconds"], 900)
        self.assertEqual(enforced["correction_rounds"], 0)


# -- 2. what a decision refuses ----------------------------------------------


class ADecisionIsRefusedBeforeItRecordsAnything(RecoveryCase):
    """Every operand compared, and nothing written when one disagrees.

    ONE OPERAND DIFFERS PER CASE. The positive path above and each case here
    share every other value, so a refusal cannot be passing because the whole
    request was malformed.
    """

    def nothing_happened(self, key, *, decision_id):
        self.assertIsNone(retained_recovery.decision_of(self.jobs,
                                                        decision_id))
        self.assertIsNone(retained_recovery.successor_intent_of(self.jobs,
                                                                decision_id))
        self.assertIsNone(self.job_row(f"recovery-{decision_id}"))
        self.assertEqual(retained_recovery.successors_for(self.jobs, key), [])
        self.assertEqual(self.stand_ins().get("binding", FakeBinding()).added,
                         [])

    def refused(self, key, read, **changed):
        """One decision attempt, under ITS OWN operation key.

        A FRESH KEY PER ATTEMPT, so a subTest cannot be passing because an
        earlier one already settled the identity -- which would turn a
        missing comparison into an operation collision and read as a refusal.
        """
        self.attempts += 1
        held = dict(changed)
        held.setdefault("decision_id", f"D-refused-{self.attempts}")
        code, said = self.decide(key, read, **held)
        self.assertEqual(code, 1, said)
        self.nothing_happened(key, decision_id=held["decision_id"])

    def setUp(self):
        super().setUp()
        self.attempts = 0
        self.held = self.delivered()
        self.item = self.read(self.held["key"])
        self.key = self.held["key"]

    def test_a_participant_without_the_decision_capability_is_refused(self):
        """THE AUTHORITY'S OWN SEAM, and `review` in the same scope is not
        the decision grant."""
        self.refused(self.key, self.item, participant=INTRUDER)
        self.assertTrue(self.authority.holds_capability(
            INTRUDER, "review", scope=self.work_row["scope"]))

    def test_a_grant_in_another_scope_does_not_authorize_this_act(self):
        self.authority.revoke_capability(OWNER, "approve",
                                         scope=self.work_row["scope"])
        self.authority.grant_capability(OWNER, "approve")
        self.assertTrue(self.authority.holds_capability(OWNER, "approve"))
        self.refused(self.key, self.item)

    def test_a_wrong_failure_report_or_candidate_digest_is_refused(self):
        for operand in ("expect_failure_digest", "expect_report_digest",
                        "expect_candidate_digest"):
            with self.subTest(operand=operand):
                self.refused(self.key, self.item,
                             **{operand: "sha256:" + "0" * 64})

    def test_a_wrong_candidate_base_or_head_is_refused(self):
        for operand in ("expect_candidate_base", "expect_candidate_head"):
            with self.subTest(operand=operand):
                self.refused(self.key, self.item,
                             **{operand: "b" * 40})

    def test_a_wrong_account_of_the_original_verifier_is_refused(self):
        """AN OWNER DECIDES ON THE COMMAND THAT ACTUALLY FAILED."""
        self.refused(self.key, self.item,
                     original=["bash", "-c", "exec python3 -m unittest -v x"])

    def test_approving_the_command_that_failed_is_the_generic_retry(self):
        self.refused(self.key, self.item,
                     corrected=list(self.item["expected"]["original_argv"]))

    def test_a_correction_with_no_execution_context_is_refused(self):
        """A COMMAND STRING MUST NOT HIDE ITS EXECUTION CONTEXT."""
        self.refused(self.key, self.item, context_digest="")

    def test_a_profile_this_build_does_not_hold_is_refused(self):
        self.refused(self.key, self.item, profile="documentation/1")

    def test_a_profile_digest_that_is_not_the_approved_one_is_refused(self):
        self.refused(self.key, self.item,
                     profile_digest="sha256:" + "b" * 64)

    def test_an_implementation_stage_is_refused_by_name(self):
        for stages in (["implementation"],
                       ["implementation", "verification", "review"],
                       ["verification", "implementation"]):
            with self.subTest(stages=stages):
                self.refused(self.key, self.item, stages=stages)

    def test_a_stage_set_this_contract_does_not_offer_is_refused(self):
        for stages in (["review", "verification"], ["verification"],
                       ["integration"], ["review", "review"]):
            with self.subTest(stages=stages):
                self.refused(self.key, self.item, stages=stages)

    def test_review_only_without_a_lineage_is_refused(self):
        self.refused(self.key, self.item, stages=["review"])

    def test_a_full_successor_naming_a_lineage_is_refused(self):
        self.refused(self.key, self.item,
                     lineage={"successor_job_id": "recovery-D0",
                              "verification_attempt_id": "verification-x",
                              "verification_result_digest":
                                  "sha256:" + "1" * 64})

    def test_evidence_that_changed_under_the_owner_is_refused(self):
        """THE ONE CHECK THE OWNER CANNOT MAKE FOR THEMSELVES."""
        self.repointed(self.held["failed"], recap="a different recap")
        self.refused(self.key, self.item)

    def test_a_candidate_that_no_longer_validates_is_reported(self):
        """REC-8: an invalid candidate is reported and is not recovery input."""
        self.control._connection.execute(
            "UPDATE output_artifacts SET content_digest = ? WHERE "
            "runtime_attempt_id = ?",
            ("sha256:" + "9" * 64, self.held["failed"]["attempt_id"]))
        read = self.read(self.key)
        self.assertFalse(read["evidence"]["valid"])
        self.assertEqual(read["evidence"]["why"]["category"], "integrity")
        self.refused(self.key, self.item)

    def test_an_undelivered_failure_cannot_be_decided(self):
        """STAGE 1-A DELIVERS THE ITEM AND THIS DECIDES IT, in that order."""
        failed = self.failed_attempt(2)
        seen = self.observed(failed)
        key = seen["failure"]["failure_key"]
        self.assertIsNone(failure_analysis.owner_item_of(self.jobs, key))
        code, said = self.command(*self.argv("recovery-item", "--failure",
                                             key))
        self.assertEqual(code, 0)
        self.refused(key, self.read(key))

    def test_a_denial_and_a_hold_launch_nothing(self):
        for disposition, word in (("--deny", "denied"), ("--hold", "held")):
            with self.subTest(disposition=disposition):
                key = self.key
                code, said = self.decide(
                    key, self.item, disposition=disposition,
                    decision_id="D-" + word)
                self.assertEqual(code, 0, said)
                self.assertEqual(said["decision"]["disposition"], word)
                self.assertFalse(said["admitted"])
                self.assertIsNone(said["successor"])
                self.assertIsNone(retained_recovery.successor_intent_of(
                    self.jobs, "D-" + word))
                self.assertIsNone(
                    self.job_row(f"recovery-D-{word}"))
        # AND THE DENIAL IS PRESERVED when a later explicit approval is made:
        # a new key is a new attributable act and never a rewrite of the old.
        denied = retained_recovery.decision_of(self.jobs, "D-denied")
        code, said = self.decide(self.key, self.item, decision_id="D3")
        self.assertEqual(code, 0, said)
        self.assertTrue(said["admitted"])
        self.assertEqual(retained_recovery.decision_of(self.jobs, "D-denied"),
                         denied)

    def test_an_admission_without_an_approved_decision_is_denied(self):
        self.decide(self.key, self.item, disposition="--hold",
                    decision_id="D-hold")
        with self.assertRaises(ContractRefusal) as caught:
            retained_recovery.admit_successor(
                self.jobs, self.control, decision_id="D-hold",
                exclusion=FakeExclusion(), authorization=WorkPort(
                    self.authority),
                binding=FakeBinding(), ownership=FakeOwnership())
        self.assertEqual(caught.exception.code, "denied")
        self.assertIsNone(self.job_row("recovery-D-hold"))


# -- 3. replay, collision and two concurrent decisions -----------------------


class OneDecisionProducesOneEffectHoweverOftenItIsAsked(RecoveryCase):
    """Exact operands replay; changed ones collide; two decisions fence."""

    def setUp(self):
        super().setUp()
        self.held = self.delivered()
        self.item = self.read(self.held["key"])
        self.key = self.held["key"]

    def test_the_exact_same_request_replays_both_durable_acts(self):
        first = self.decide(self.key, self.item)[1]
        second = self.decide(self.key, self.item)[1]
        self.assertEqual(second, first)
        for kind in (retained_recovery.DECISION_KIND,
                     retained_recovery.SUCCESSOR_INTENT_KIND,
                     retained_recovery.SUCCESSOR_KIND):
            self.assertEqual(len(self.journal(kind)), 1, kind)
        # AND NOTHING WAS PUBLISHED TWICE.
        self.assertEqual(len(self.stand_ins()["binding"].added), 1)
        self.assertEqual(len(self.jobs._connection.execute(
            "SELECT job_id FROM jobs WHERE job_id = 'recovery-D1'"
        ).fetchall()), 1)

    def test_the_same_key_with_changed_operands_collides(self):
        self.decide(self.key, self.item)
        held = retained_recovery.decision_of(self.jobs, "D1")
        for changed in ({"corrected": ["bash", "-c", "true"]},
                        {"stages": ["review"]},
                        {"context_digest": "sha256:" + "d" * 64}):
            with self.subTest(changed=sorted(changed)):
                code, said = self.decide(self.key, self.item, **changed)
                self.assertEqual(code, 1, said)
                self.assertEqual(
                    retained_recovery.decision_of(self.jobs, "D1"), held)
        self.assertEqual(len(self.journal(
            retained_recovery.SUCCESSOR_KIND)), 1)

    def test_a_second_full_approval_of_one_failure_is_fenced(self):
        """ONE RETAINED FAILURE HAS ONE VERIFICATION/REVIEW SUCCESSOR."""
        self.assertEqual(self.decide(self.key, self.item)[0], 0)
        code, said = self.decide(self.key, self.item, decision_id="D2")
        self.assertEqual(code, 1, said)
        self.assertIsNone(retained_recovery.decision_of(self.jobs, "D2"))
        self.assertIsNone(self.job_row("recovery-D2"))
        self.assertEqual(
            [one["job_id"] for one in
             retained_recovery.successors_for(self.jobs, self.key)],
            ["recovery-D1"])

    def test_two_concurrent_decisions_admit_exactly_one_successor(self):
        """THE RACE, SYNCHRONIZED PAST THE POINT A READ WOULD HAVE DECIDED.

        Both commands get past the host read before either reserves, so the
        fence they meet is the one inside this store's write lock rather than
        the ordering of two threads.
        """
        gate = threading.Barrier(2, timeout=30)
        exclusion = self.stand_ins().setdefault(
            "exclusion", FakeExclusion(identity=CURRENT["identity"]))

        def answer(attempt_ids):
            held = {one: ceased() for one in attempt_ids}
            try:
                gate.wait()
            except threading.BrokenBarrierError:        # pragma: no cover
                pass
            return held

        exclusion.answer = answer

        def deciding(decision_id):
            try:
                return self.decide(self.key, self.item,
                                   decision_id=decision_id)[0]
            finally:
                gate.abort()

        with concurrent.futures.ThreadPoolExecutor(2) as pool:
            codes = sorted(one.result() for one in [
                pool.submit(deciding, "C1"), pool.submit(deciding, "C2")])
        self.assertEqual(codes, [0, 1])
        reserved = retained_recovery.successors_for(self.jobs, self.key)
        self.assertEqual(len(reserved), 1, reserved)
        admitted = [one for one in ("recovery-C1", "recovery-C2")
                    if self.job_row(one) is not None]
        self.assertEqual(len(admitted), 1, admitted)
        self.assertEqual(len(self.stand_ins()["binding"].added), 1)

    def test_a_restarted_incarnation_reads_the_same_admission(self):
        answer = self.decide(self.key, self.item)[1]["successor"]
        reopened = JobStore.open(
            self.jobs.database, authority_uuid=self.AUTHORITY,
            incarnation="recovery-2", clock=self.clock)
        self.addCleanup(reopened.close)
        self.assertEqual(retained_recovery.successor_of(reopened, "D1"),
                         answer)
        self.assertEqual(
            retained_recovery.decision_of(reopened, "D1")["disposition"],
            "approved")
        # THE ADMITTED DEADLINES ARE THE ADMITTED ONES, not fresh ones.
        self.assertEqual(
            job_control.control_of(reopened, "recovery-D1")["admitted_at"],
            NOW)


# -- 4. the fault cuts -------------------------------------------------------


class EveryCutBetweenTheOwnersResumes(RecoveryCase):
    """A crash or a refusal past the reservation is incomplete, not undone."""

    def setUp(self):
        super().setUp()
        self.held = self.delivered()
        self.item = self.read(self.held["key"])
        self.key = self.held["key"]

    def test_a_refusal_past_the_reservation_names_it_and_then_resumes(self):
        self.stand_ins()["binding"] = FakeBinding(
            identity=CURRENT["identity"], unservable=1)
        code, said = self.decide(self.key, self.item)
        self.assertEqual(code, 1)
        # THE DECISION STANDS and the identity is RESERVED; the Job is not.
        self.assertEqual(
            retained_recovery.decision_of(self.jobs, "D1")["disposition"],
            "approved")
        intent = retained_recovery.successor_intent_of(self.jobs, "D1")
        self.assertEqual(intent["state"], "intended")
        self.assertEqual(intent["job_id"], "recovery-D1")
        self.assertIsNone(retained_recovery.successor_of(self.jobs, "D1"))
        self.assertIsNone(self.job_row("recovery-D1"))
        # THE SAME REQUEST AGAIN FINISHES IT, and nothing is done twice.
        code, said = self.decide(self.key, self.item)
        self.assertEqual(code, 0, said)
        self.assertEqual(said["successor"]["job_id"], "recovery-D1")
        self.assertEqual(said["successor"]["binding"]["disposition"],
                         "already configured")
        self.assertEqual(len(self.stand_ins()["binding"].added), 1)
        self.assertEqual(len(self.journal(
            retained_recovery.SUCCESSOR_INTENT_KIND)), 1)

    def test_a_lost_completion_reply_resumes_without_redoing_anything(self):
        """THE CUT AFTER THE SUBMISSION AND BEFORE THE COMPLETION."""
        self.decide(self.key, self.item)
        self.jobs._connection.execute(
            "DELETE FROM operations WHERE operation_id = ?",
            (retained_recovery.admit_operation_id("D1"),))
        self.assertIsNone(retained_recovery.successor_of(self.jobs, "D1"))
        self.assertIsNotNone(self.job_row("recovery-D1"))

        code, said = self.decide(self.key, self.item)
        self.assertEqual(code, 0, said)
        self.assertEqual(said["successor"]["job_id"], "recovery-D1")
        self.assertEqual(len(self.stand_ins()["binding"].added), 1)
        self.assertEqual(len(self.jobs._connection.execute(
            "SELECT job_id FROM jobs WHERE job_id = 'recovery-D1'"
        ).fetchall()), 1)
        self.assertEqual(
            [row["kind"] for row in
             submission.stages_of(self.jobs, "recovery-D1")], ["review"])

    def test_a_crash_before_the_decision_leaves_nothing_to_carry_out(self):
        """THE FIRST CUT: no decision, so no admission is reachable."""
        with self.assertRaises(ContractRefusal) as caught:
            retained_recovery.admit_successor(
                self.jobs, self.control, decision_id="never-decided",
                exclusion=FakeExclusion(identity=CURRENT["identity"]),
                authorization=WorkPort(self.authority,
                                       identity=CURRENT["identity"]),
                binding=FakeBinding(identity=CURRENT["identity"]),
                ownership=FakeOwnership(identity=CURRENT["identity"]))
        self.assertIn("holds no owner decision", caught.exception.message)
        self.assertIsNone(self.job_row("recovery-never-decided"))

    def test_owner_ports_answering_for_two_deployments_refuse(self):
        """THE MANAGER'S OWN INSTANCE CHECK, independent of the composition."""
        self.approved(self.item, decision_id="H1")
        elsewhere = dict(CURRENT["identity"], root="/disposable/other")
        with self.assertRaises(ContractRefusal) as caught:
            retained_recovery.admit_successor(
                self.jobs, self.control, decision_id="H1",
                exclusion=FakeExclusion(identity=elsewhere),
                authorization=WorkPort(self.authority,
                                       identity=CURRENT["identity"]),
                binding=FakeBinding(identity=CURRENT["identity"]),
                ownership=FakeOwnership(identity=CURRENT["identity"]))
        self.assertIn("answer for different deployments",
                      caught.exception.message)

    def test_a_control_store_the_host_port_does_not_own_refuses(self):
        self.approved(self.item, decision_id="H2")
        elsewhere = dict(CURRENT["identity"],
                         control_store="/disposable/other/control.sqlite3")
        with self.assertRaises(ContractRefusal) as caught:
            retained_recovery.admit_successor(
                self.jobs, self.control, decision_id="H2",
                exclusion=FakeExclusion(identity=elsewhere),
                authorization=WorkPort(self.authority, identity=elsewhere),
                binding=FakeBinding(identity=elsewhere),
                ownership=FakeOwnership(identity=elsewhere))
        self.assertIn("evidence about another deployment",
                      caught.exception.message)
        self.assertIsNone(self.job_row("recovery-H2"))


# -- 5. cancellation, cessation and the fences -------------------------------


class UnknownIsAHoldAndACancelledExecutionIsNeverRevived(RecoveryCase):
    """What refuses, what holds, and what an expired original does NOT do."""

    def setUp(self):
        super().setUp()
        self.held = self.delivered()
        self.item = self.read(self.held["key"])
        self.key = self.held["key"]

    def test_an_explicitly_cancelled_job_is_not_recovered(self):
        self.cancel()
        code, said = self.decide(self.key, self.item)
        self.assertEqual(code, 1, said)
        self.assertIsNone(retained_recovery.decision_of(self.jobs, "D1"))
        self.assertIsNone(self.job_row("recovery-D1"))
        self.assertEqual(self.stand_ins()["binding"].added, [])

    def test_an_expired_original_is_admissible_and_the_fence_is_reported(self):
        """EXPIRED ORIGINAL DEADLINES REMAIN EXPIRED AND UNCHANGED.

        A retained verification failure is ordinarily decided about after the
        Job that produced it reached its own wall. Refusing on that would make
        this whole recovery unreachable in its commonest case; the successor
        gets its own admission and its own clocks, and the original's own
        expiry record is not touched.
        """
        expiry = job_control.expire(
            self.jobs, job_id="job-a", trigger="job-deadline", stage_id=None,
            deadline_at=EXPIRED, observed_at=EXPIRED)
        code, said = self.decide(self.key, self.item, clock=lambda: AFTER)
        self.assertEqual(code, 0, said)
        self.assertEqual(said["successor"]["fence"]["trigger"],
                         "job-deadline")
        self.assertEqual(said["successor"]["fence"]["requested_at"], EXPIRED)
        # THE SUCCESSOR'S OWN CLOCKS, and the original's untouched.
        self.assertEqual(said["successor"]["bounds"]["admitted_at"], AFTER)
        self.assertEqual(said["successor"]["control"]["admitted_at"], AFTER)
        self.assertEqual(job_control.expiry_of(self.jobs, "job-a"), expiry)

    def test_a_runtime_the_host_cannot_account_for_holds(self):
        for answer, why in (({}, "no evidence about attempt"),
                            (ceased(runtime="uncertain"), "cessation is"),
                            (ceased(cleanup="pending"), "still owes it"),
                            (ceased(token={"returned": False}),
                             "still holds its workspace resource")):
            with self.subTest(why=why):
                CURRENT["ports"] = {}
                held = FakeExclusion(identity=CURRENT["identity"])
                if answer == {}:
                    held.answer = lambda ids: {}
                else:
                    held.answer = answer
                CURRENT["ports"]["exclusion"] = held
                code, said = self.decide(self.key, self.item,
                                         decision_id="U-" + why[:6])
                self.assertEqual(code, 1, said)
                # THE DECISION IS RECORDED AND THE SUCCESSOR IS NOT: they are
                # two acts, the owner's one happened, and the ANSWER SAYS SO
                # -- an operator must be able to tell "nothing was recorded"
                # from "your decision stands and the admission is owed".
                self.assertEqual(said["decision"]["disposition"], "approved")
                self.assertIsNone(said["successor"])
                self.assertFalse(said["admitted"])
                self.assertIn(why, said["refusal"]["message"])
                self.assertEqual(
                    retained_recovery.decision_of(
                        self.jobs, "U-" + why[:6])["disposition"], "approved")
                self.assertIsNone(retained_recovery.successor_intent_of(
                    self.jobs, "U-" + why[:6]))
                self.assertIsNone(self.job_row("recovery-U-" + why[:6]))

    def test_a_terminal_work_cannot_carry_a_recovery(self):
        from baton_v12.authority import Authority

        self.authority.dispose()
        with Authority.open(self.authority_path,
                            expected_authority_uuid=self.AUTHORITY) as held:
            session = held.session(OWNER)
            held.set_policy("canonical_target", "b" * 40)
            held._core._store.run(
                "UPDATE work SET status = 'closed', phase = NULL WHERE "
                "work_id = ?", WORK_A)
            del session
        code, said = self.decide(self.key, self.item)
        self.assertEqual(code, 1, said)
        self.assertIsNone(retained_recovery.decision_of(self.jobs, "D1"))


# -- 6. the post-verification expiry disposition -----------------------------


class ReviewOnlyRecoveryNeedsExactlyValidEvidence(RecoveryCase):
    """Section 3.7: a passed verification is reused, never repeated.

    THE VERIFICATION ITSELF IS W385625's. What is driven here is the
    supported record its adapter writes, through `record_verification`, with
    deterministic values -- which is exactly the boundary this slice owns and
    the next slice fills.
    """

    def setUp(self):
        super().setUp()
        self.held = self.delivered()
        self.item = self.read(self.held["key"])
        self.key = self.held["key"]
        self.assertEqual(self.decide(self.key, self.item)[0], 0)

    def verified(self, *, outcome="passed", exit_status=0, argv=None,
                 context=None, decision_id="D1"):
        return retained_recovery.record_verification(
            self.jobs, self.control, decision_id=decision_id,
            outcome=outcome, exit_status=exit_status,
            argv=CORRECTED if argv is None else argv,
            context_digest=CONTEXT if context is None else context,
            result_digest="sha256:" + "4" * 64, now=LATER)

    def expired(self, job_id="recovery-D1"):
        return job_control.expire(
            self.jobs, job_id=job_id, trigger="job-deadline", stage_id=None,
            deadline_at=EXPIRED, observed_at=EXPIRED)

    def lineage(self, read, job_id="recovery-D1"):
        held = [one for one in read["successors"]
                if one["job_id"] == job_id][0]
        return {"successor_job_id": held["job_id"],
                "verification_attempt_id": held["verification_attempt_id"],
                "verification_result_digest":
                    held["verification_result_digest"]}

    def review_only(self, **changed):
        read = self.read(self.key)
        held = {"decision_id": "D2", "stages": ["review"],
                "lineage": self.lineage(read), "clock": lambda: AFTER}
        held.update(changed)
        return self.decide(self.key, read, **held), read

    def test_a_passed_verification_is_reviewed_without_being_repeated(self):
        verification = self.verified()
        self.expired()
        (code, said), read = self.review_only()
        self.assertEqual(code, 0, said)
        successor = said["successor"]
        self.assertEqual(successor["job_id"], "recovery-D2")
        self.assertEqual(successor["stages"], ["review"])
        self.assertEqual(successor["readiness"]["verification"], "omitted")
        self.assertEqual(successor["readiness"]["review"], "blocked")
        # THE SAME APPROVED PROFILE AND DIGEST, with the verification stage
        # omitted rather than a third profile invented.
        self.assertEqual(successor["bounds"]["profile"],
                         retained_recovery.SUCCESSOR_PROFILE)
        self.assertEqual(successor["bounds"]["digest"],
                         "sha256:" + APPROVED_PROFILE_DIGEST)
        self.assertEqual(successor["bounds"]["overall_job_seconds"], 9960)
        self.assertEqual(successor["bounds"]["each_stage_seconds"], 4800)
        self.assertEqual(successor["control"]["profile"],
                         retained_recovery.SUCCESSOR_PROFILE)
        # ITS OWN NEW CLOCKS, and the expired successor's deadline unchanged.
        self.assertEqual(successor["bounds"]["admitted_at"], AFTER)
        self.assertEqual(
            job_control.expiry_of(self.jobs, "recovery-D1")["requested_at"],
            EXPIRED)
        # ONE REVIEW STAGE AND NO VERIFICATION OF ITS OWN.
        self.assertEqual(
            [row["kind"] for row in
             submission.stages_of(self.jobs, "recovery-D2")], ["review"])
        self.assertIsNone(retained_recovery.verification_of(self.jobs,
                                                            "recovery-D2"))
        # AND THE EVIDENCE IT REUSED IS THE JOURNALLED ACCOUNT, by digest.
        self.assertEqual(said["decision"]["lineage"][
            "verification_result_digest"], digest(verification))
        self.assertEqual(verification["outcome"], "passed")

    def test_an_unexpired_successor_is_not_reviewed_under_a_new_identity(self):
        self.verified()
        (code, said), read = self.review_only()
        self.assertEqual(code, 1, said)
        self.assertIsNone(retained_recovery.decision_of(self.jobs, "D2"))
        self.assertIsNone(self.job_row("recovery-D2"))

    def test_an_unaccounted_verification_refuses_and_never_reverifies(self):
        self.expired()
        (code, said), read = self.review_only()
        self.assertEqual(code, 1, said)
        self.assertIsNone(self.job_row("recovery-D2"))
        # AND THE REFUSAL IS NOT PERMISSION TO VERIFY AGAIN: no second
        # verification/review successor was reserved either.
        self.assertEqual(
            [one["job_id"] for one in
             retained_recovery.successors_for(self.jobs, self.key)],
            ["recovery-D1"])

    def test_a_failed_verification_is_disposed_of_and_not_reviewed(self):
        self.verified(outcome="failed", exit_status=1)
        self.expired()
        (code, said), read = self.review_only()
        self.assertEqual(code, 1, said)
        self.assertIsNone(self.job_row("recovery-D2"))

    def test_a_cancelled_successor_is_never_revived(self):
        self.verified()
        cancellation.request(self.jobs, job_id="recovery-D1",
                             reason="the owner stopped the successor")
        (code, said), read = self.review_only()
        self.assertEqual(code, 1, said)
        self.assertIsNone(self.job_row("recovery-D2"))

    def test_a_lineage_naming_other_evidence_is_refused(self):
        self.verified()
        self.expired()
        read = self.read(self.key)
        exact = self.lineage(read)
        for member, value in (
                ("verification_result_digest", "sha256:" + "7" * 64),
                ("verification_attempt_id", "verification-somebody-else"),
                ("successor_job_id", "recovery-D9")):
            with self.subTest(member=member):
                code, said = self.decide(
                    self.key, read, decision_id="D-" + member[:6],
                    stages=["review"], lineage=dict(exact, **{member: value}),
                    clock=lambda: AFTER)
                self.assertEqual(code, 1, said)
                self.assertIsNone(self.job_row("recovery-D-" + member[:6]))

    def test_a_correction_the_verification_did_not_run_is_refused(self):
        """OMITTING A STAGE PRESERVES THE VERIFICATION THAT ACTUALLY RAN."""
        self.verified()
        self.expired()
        read = self.read(self.key)
        for changed in ({"corrected": ["bash", "-c", "exec true"]},
                        {"context_digest": "sha256:" + "9" * 64}):
            with self.subTest(changed=sorted(changed)):
                code, said = self.decide(
                    self.key, read, decision_id="D-" + sorted(changed)[0][:6],
                    stages=["review"], lineage=self.lineage(read),
                    clock=lambda: AFTER, **changed)
                self.assertEqual(code, 1, said)

    def test_a_candidate_that_changed_under_the_evidence_is_refused(self):
        self.verified()
        self.expired()
        read = self.read(self.key)
        self.repointed(self.held["failed"], recap="a different recap")
        code, said = self.decide(self.key, read, decision_id="D2",
                                 stages=["review"],
                                 lineage=self.lineage(read),
                                 clock=lambda: AFTER)
        self.assertEqual(code, 1, said)
        self.assertIsNone(self.job_row("recovery-D2"))

    def test_one_expired_successor_earns_one_review_only_successor(self):
        self.verified()
        self.expired()
        self.assertEqual(self.review_only()[0][0], 0)
        (code, said), read = self.review_only(decision_id="D3")
        self.assertEqual(code, 1, said)
        self.assertIsNone(self.job_row("recovery-D3"))

    def test_the_verification_account_is_held_to_what_was_approved(self):
        for changed, why in (
                ({"argv": ["bash", "-c", "exec true"]}, "not approve"),
                ({"context": "sha256:" + "1" * 64}, "execution context"),
                ({"outcome": "passed", "exit_status": 3}, "exits 0"),
                ({"decision_id": "nobody"}, "no admitted successor")):
            with self.subTest(why=why):
                with self.assertRaises(ContractRefusal) as caught:
                    self.verified(**changed)
                self.assertIn(why, caught.exception.message)
                self.assertIsNone(retained_recovery.verification_of(
                    self.jobs, "recovery-D1"))

    def test_a_verification_account_replays_and_collides(self):
        first = self.verified()
        self.assertEqual(self.verified(), first)
        with self.assertRaises(ContractRefusal):
            retained_recovery.record_verification(
                self.jobs, self.control, decision_id="D1", outcome="failed",
                exit_status=1, argv=CORRECTED, context_digest=CONTEXT,
                now=LATER)
        self.assertEqual(
            retained_recovery.verification_of(self.jobs, "recovery-D1"),
            first)


# -- 7. what this slice must not have changed --------------------------------


class NothingHereRedispatchesImplementationOrTouchesTheOriginal(RecoveryCase):
    """The original failure, its candidate and Stage 1-A's records, intact."""

    def setUp(self):
        super().setUp()
        self.held = self.delivered()
        self.item = self.read(self.held["key"])
        self.key = self.held["key"]

    def stage_a_records(self):
        key = self.key
        return {
            "failure": failure_analysis.failure_of(self.jobs, key),
            "intent": failure_analysis.intent_of(self.jobs, key),
            "dispatch": failure_analysis.dispatch_of(self.jobs, key),
            "report": failure_analysis.report_of(self.jobs, key),
            "owner_item": failure_analysis.owner_item_of(self.jobs, key),
            "disposition": failure_analysis.recovery_disposition(self.jobs,
                                                                 key)}

    def test_the_whole_path_writes_nothing_to_the_control_store(self):
        """NO CANDIDATE, NO VERIFIER INPUT, NO EXECUTION STATE.

        Proved on the BYTES of the whole store rather than on a list of
        tables this case thought to check.
        """
        before = self.control_bytes()
        self.read(self.key, "--participant", OWNER)
        self.assertEqual(self.decide(self.key, self.item)[0], 0)
        self.read(self.key)
        self.assertEqual(self.control_bytes(), before)

    def test_stage_1_a_s_five_records_are_exactly_as_they_were(self):
        before = self.stage_a_records()
        self.assertEqual(self.decide(self.key, self.item)[0], 0)
        self.assertEqual(self.stage_a_records(), before)
        self.assertEqual(before["disposition"], "delivered")
        # AND NO SECOND ANALYSIS, DISPATCH OR OWNER ITEM WAS CREATED.
        for kind in (failure_analysis.FAILURE_KIND,
                     failure_analysis.INTENT_KIND,
                     failure_analysis.DISPATCH_KIND,
                     failure_analysis.REPORT_KIND,
                     failure_analysis.OWNER_ITEM_KIND):
            self.assertEqual(len(self.journal(kind)), 1, kind)

    def test_the_failed_job_its_stages_and_its_submission_are_untouched(self):
        def original():
            return {
                "job": dict(self.jobs._connection.execute(
                    "SELECT * FROM jobs WHERE job_id = 'job-a'").fetchone()),
                "stages": [dict(row) for row in self.jobs._connection.execute(
                    "SELECT * FROM stages WHERE job_id = 'job-a' ORDER BY "
                    "ordinal")],
                "submission": self.jobs._connection.execute(
                    "SELECT document FROM submissions WHERE submission_id = "
                    "'sub-1'").fetchone()[0],
                "control": job_control.control_of(self.jobs, "job-a")}

        before = original()
        self.assertEqual(self.decide(self.key, self.item)[0], 0)
        self.assertEqual(original(), before)

    def test_no_successor_carries_an_implementation_stage_or_an_effect(self):
        self.assertEqual(self.decide(self.key, self.item)[0], 0)
        # EVERY stage of EVERY recovery successor in the whole store.
        rows = [row for row in submission.stage_rows(self.jobs)
                if row["job_id"].startswith("recovery-")]
        self.assertEqual(sorted(row["kind"] for row in rows), ["review"])
        self.assertEqual([row["job_id"] for row in rows], ["recovery-D1"])
        # AND NO EXECUTION EFFECT WAS PERFORMED FOR IT. A submitted stage
        # gets its first EPISODE from `submit` -- that is the stage's own
        # bookkeeping and is what makes it schedulable at all -- so what is
        # counted here is the acts: a receipt is an offer, a claim, a start or
        # an ending, and an allocation is a reserved worker. This admission
        # performs none of them, which is the whole of "no implementation
        # stage or effect" plus "the verifier was not executed here".
        for table in ("receipts", "stage_allocations"):
            self.assertEqual(self.jobs._connection.execute(
                f"SELECT count(*) FROM {table} WHERE stage_id LIKE "
                f"'recovery-%'").fetchone()[0], 0, table)

    def test_the_read_reports_what_has_already_been_decided(self):
        self.assertEqual(self.decide(self.key, self.item)[0], 0)
        read = self.read(self.key, "--participant", OWNER)
        self.assertEqual([one["decision_id"] for one in read["decisions"]],
                         ["D1"])
        self.assertEqual(read["decisions"][0]["disposition"], "approved")
        self.assertEqual(read["decisions"][0]["endpoint"], OWNER)
        self.assertEqual(len(read["successors"]), 1)
        held = read["successors"][0]
        self.assertEqual(held["job_id"], "recovery-D1")
        self.assertTrue(held["admitted"])
        self.assertEqual(held["disposition"], "admitted")
        self.assertEqual(held["stages"], ["verification", "review"])
        self.assertIsNone(held["verification"])
        self.assertIsNone(held["verification_result_digest"])
        self.assertIsNone(held["fence"])
        self.assertEqual(held["review_stage_id"], "recovery-D1/review")

    def test_the_successors_state_is_derived_and_never_stored_twice(self):
        """THIS JOURNAL HAS NO UPDATE, so the current state is derived.

        The reservation record's own `state` is the word it is BORN with and
        never moves; what a reader asks is `successor_disposition`, exactly
        as Stage 1-A's `recovery_disposition` is derived from which records
        exist rather than stored and advanced.
        """
        self.assertEqual(
            retained_recovery.successor_disposition(self.jobs, "D1"),
            "undecided")
        self.approved(self.item, decision_id="D1")
        self.assertEqual(
            retained_recovery.successor_disposition(self.jobs, "D1"),
            "decided")
        retained_recovery.admit_successor(
            self.jobs, self.control, decision_id="D1",
            exclusion=FakeExclusion(identity=CURRENT["identity"]),
            authorization=WorkPort(self.authority,
                                   identity=CURRENT["identity"]),
            binding=FakeBinding(identity=CURRENT["identity"]),
            ownership=FakeOwnership(identity=CURRENT["identity"]))
        self.assertEqual(
            retained_recovery.successor_disposition(self.jobs, "D1"),
            "admitted")
        self.assertEqual(
            retained_recovery.successor_intent_of(self.jobs, "D1")["state"],
            "intended")
        retained_recovery.record_verification(
            self.jobs, self.control, decision_id="D1", outcome="passed",
            exit_status=0, argv=CORRECTED, context_digest=CONTEXT,
            now=LATER)
        self.assertEqual(
            retained_recovery.successor_disposition(self.jobs, "D1"),
            "verified")

    def test_the_control_report_is_available_and_optional(self):
        plain = self.read(self.key)
        self.assertNotIn("control", plain)
        held = self.read(self.key, "--control-report")
        self.assertEqual(held["control"]["profile"],
                         job_control.NATIVE_HANDOFF_PROFILE)
        self.assertIsNone(held["control"]["fence"])

    def test_the_command_holds_no_rule_and_delegates_both_acts(self):
        """REC-7: THE CLI REQUESTS THE OPERATION AND REPORTS ITS OUTCOME.

        Asserted from the source, as `test_creation`'s own delegation case is:
        a branch here deciding authorization, digests, stage sets, profiles,
        fences or replay would be the script-side precheck REC-7 forbids,
        wearing the product's name.
        """
        import ast

        from tools import recovery_decision

        source = pathlib.Path(recovery_decision.__file__).read_text(
            encoding="utf-8")
        tree = ast.parse(source)
        named = {one.name: one for one in tree.body
                 if type(one) is ast.FunctionDef}
        called = {}
        for name in ("_item", "_decide"):
            called[name] = {piece.func.attr
                            if type(piece.func) is ast.Attribute
                            else getattr(piece.func, "id", None)
                            for piece in ast.walk(named[name])
                            if type(piece) is ast.Call}
        self.assertIn("owner_item_read", called["_item"])
        self.assertIn("decide", called["_decide"])
        self.assertIn("admit_successor", called["_decide"])
        # AND THE READ VERB PERFORMS NEITHER DURABLE ACT.
        self.assertNotIn("decide", called["_item"])
        self.assertNotIn("admit_successor", called["_item"])
        # THERE IS NO `--actor` AND NO `--scope` ANYWHERE ON THE SURFACE.
        for forbidden in ("--actor", "--scope", "--principal",
                          "--work-scope"):
            self.assertNotIn(f'"{forbidden}"', source, forbidden)

    def test_the_verbs_are_served_by_the_installed_manager_command(self):
        """REACHABLE FROM THE DEPLOYED BUNDLE, not only from a checkout.

        `stack_command.COMMANDS["manager"]` is `tools.job_manager.main`, which
        is what `baton-v12-stack manager ...` runs frozen and from source
        alike -- so dispatching these two verbs there is what makes the
        owner's surface reachable by somebody holding the installation. An
        owner surface reachable only out of band is reachable only by an
        agent.
        """
        from tools import job_manager, recovery_decision, stack_command

        self.assertIs(stack_command.COMMANDS["manager"].__wrapped__
                      if hasattr(stack_command.COMMANDS["manager"],
                                 "__wrapped__")
                      else stack_command.COMMANDS["manager"],
                      stack_command._manager)
        self.assertEqual(recovery_decision.COMMANDS,
                         ("recovery-item", "recovery-decide"))
        source = pathlib.Path(job_manager.__file__).read_text(
            encoding="utf-8")
        self.assertIn("recovery_decision.COMMANDS", source)
        for verb in recovery_decision.COMMANDS:
            with self.subTest(verb=verb):
                said = io.StringIO()
                with self.assertRaises(SystemExit) as caught:
                    job_manager.main([verb, "--help"], clock=lambda: NOW,
                                     stream=said)
                self.assertEqual(caught.exception.code, 0)


class TheCommandRefusesAnIncompleteRequestBeforeItOpensAnything(RecoveryCase):
    """The operand gates, which are about COMPLETENESS and nothing else.

    Everything a decision MEANS is the operation's; what the command owns is
    that a request missing an operand is refused as the incomplete request it
    is rather than handed on as a weaker one.
    """

    def setUp(self):
        super().setUp()
        self.held = self.delivered()
        self.item = self.read(self.held["key"])
        self.key = self.held["key"]

    def exits(self, *argv):
        from tools import job_manager

        said = io.StringIO()
        with self.assertRaises(SystemExit) as caught:
            job_manager.main(list(argv), clock=lambda: NOW, stream=said)
        return caught.exception.code

    def test_a_decision_without_an_explicit_disposition_is_refused(self):
        argv = [one for one in
                self.decide_argv(self.key, self.item) if one != "--approve"]
        self.assertEqual(self.exits(*argv), 2)
        self.assertIsNone(retained_recovery.decision_of(self.jobs, "D1"))

    def test_a_decision_naming_no_participant_is_refused(self):
        argv = [one for one in self.decide_argv(self.key, self.item)
                if not one.startswith("--participant=")]
        self.assertEqual(self.exits(*argv), 2)
        self.assertIsNone(retained_recovery.decision_of(self.jobs, "D1"))

    def test_every_bound_operand_is_required(self):
        for operand in ("--decision-id", "--expect-failure-digest",
                        "--expect-candidate-base", "--expect-candidate-head",
                        "--expect-candidate-digest", "--context-digest",
                        "--profile", "--profile-digest"):
            with self.subTest(operand=operand):
                argv = [one for one in self.decide_argv(self.key, self.item)
                        if not one.startswith(operand + "=")]
                self.assertEqual(self.exits(*argv), 2)
        for operand in ("--original-verification", "--corrected-verification",
                        "--stage"):
            with self.subTest(operand=operand):
                argv = [one for one in self.decide_argv(self.key, self.item)
                        if not one.startswith(operand + "=")]
                self.assertEqual(self.exits(*argv), 2)
        self.assertEqual(retained_recovery.decisions_of(self.jobs), [])

    def test_half_a_review_only_lineage_is_refused_as_incomplete(self):
        code, said = self.decide(
            self.key, self.item, stages=["review"],
            prior_successor="recovery-D0")
        self.assertEqual(code, 1, said)
        self.assertIsNone(retained_recovery.decision_of(self.jobs, "D1"))

    def test_the_read_needs_no_participant_and_still_answers(self):
        held = self.read(self.key)
        self.assertNotIn("authorization", held)
        self.assertEqual(held["failure_key"], self.key)


if __name__ == "__main__":                                # pragma: no cover
    unittest.main()


class RecoveryAdmissionIsNotRunnable(RecoveryCase):
    """Real manager ticks honor the unsupported Stage1-C boundary."""
    verified = ReviewOnlyRecoveryNeedsExactlyValidEvidence.verified
    expired = ReviewOnlyRecoveryNeedsExactlyValidEvidence.expired
    lineage = ReviewOnlyRecoveryNeedsExactlyValidEvidence.lineage
    review_only = ReviewOnlyRecoveryNeedsExactlyValidEvidence.review_only

    def setUp(self):
        super().setUp()
        self.key = self.delivered()["key"]
        self.item = self.read(self.key)
        self.assertEqual(self.decide(self.key, self.item)[0], 0)

    def assert_no_offer(self, job_id="recovery-D1", now=NOW):
        from baton_v12.job_manager import projection, sweep
        from tests.job_manager.fixtures import FakeOperations
        operations = FakeOperations(authority_uuid=self.AUTHORITY)
        report = sweep(self.jobs, operations, now=now)
        self.assertFalse([act for act in report["acts"] if job_id in json.dumps(act)])
        state = projection.stage_states(self.jobs, operations)[job_id + "/review"]
        self.assertNotIn(state["state"], ("queued", "offered"))
        gate = projection.gates_of(state["stage"], {job_id + "/review": state})[0]
        self.assertFalse(gate["open"])
        self.assertEqual(gate["reason"], "retained-candidate-execution-handoff-unavailable")
        intent = retained_recovery.successor_intent_of(self.jobs, gate["decision_id"])
        self.assertEqual(gate["candidate"], intent["candidate"])
        self.assertEqual(gate["lineage"], intent["lineage"])
        self.assertFalse([call for call in operations.calls if job_id in json.dumps(call)])

    def test_unknown_verification_and_restart_never_offer_review(self):
        self.assert_no_offer()
        with JobStore.open(self.jobs.database, authority_uuid=self.AUTHORITY, incarnation="restarted", clock=lambda: NOW) as restarted:
            original, self.jobs = self.jobs, restarted
            try:
                self.assert_no_offer()
            finally:
                self.jobs = original

    def test_failed_verification_never_offers_review(self):
        self.verified(outcome="failed", exit_status=1)
        self.assert_no_offer()

    def test_passed_account_without_candidate_handoff_stays_blocked(self):
        self.verified()
        self.assert_no_offer()

    def test_review_only_keeps_exact_lineage_but_cannot_bypass_missing_handoff(self):
        self.verified()
        self.expired()
        (code, answer), _ = self.review_only()
        self.assertEqual(code, 0, answer)
        self.assert_no_offer("recovery-D2", now=AFTER)

    def test_cancelled_successor_never_offers_review(self):
        cancellation.request(self.jobs, job_id="recovery-D1", reason="owner stopped")
        self.assert_no_offer()

    def test_expired_successor_never_offers_review(self):
        self.expired()
        self.assert_no_offer(now=AFTER)

    def test_ordinary_submit_cannot_replay_even_exact_recovery_document(self):
        row = submission.submission_of(self.jobs, submission.job_of(self.jobs, "recovery-D1")["submission_id"])
        with self.assertRaisesRegex(ContractRefusal, "requires retained-recovery"):
            submission.submit(self.jobs, json.loads(row["document"]))

    def test_public_submit_command_refuses_the_recovery_profile(self):
        from tools import job_manager
        row = submission.submission_of(self.jobs, submission.job_of(self.jobs, "recovery-D1")["submission_id"])
        document = pathlib.Path(self.root) / "ordinary-submit.json"
        document.write_text(row["document"])
        with self.assertRaisesRegex(ContractRefusal, "requires retained-recovery"):
            job_manager.main(["--store", self.jobs.database, "--authority-uuid", self.AUTHORITY, "--incarnation", "ordinary-cli", "submit", "--document", str(document)], clock=lambda: NOW, stream=io.StringIO())

    def test_generic_fresh_attempt_refuses_before_owner_effects(self):
        from baton_v12.job_manager import fresh_attempt
        ports = self.stand_ins()
        with self.assertRaisesRegex(ContractRefusal, "requires retained-recovery"):
            fresh_attempt.admit(self.jobs, None, prior_job_id="recovery-D1", exclusion=ports["exclusion"], authorization=WorkPort(self.authority), binding=ports["binding"], ownership=ports["ownership"])

    def test_ordinary_create_refuses_the_recovery_only_profile(self):
        from tests.job_manager import test_creation
        case = test_creation.CreationCase("setUp")
        case.setUp()
        try:
            with self.assertRaisesRegex(ContractRefusal, "requires retained-recovery"):
                case.created(request=test_creation.request(control={"profile": retained_recovery.SUCCESSOR_PROFILE}))
        finally:
            case.doCleanups()


from tests.tools.test_bootstrap import ValidFixture as _InstalledFixture


class ShippedOwnersComposeOverAnInstalledInstance(_InstalledFixture):
    def test_default_factory_reaches_owner_item_and_rejects_foreign_stores(self):
        from contextlib import redirect_stderr
        from baton_v12.worker_manager import ControlStore
        from tools import bootstrap, job_manager
        prepared = self.prepared()
        places = bootstrap.layout(self.state)
        uuid = prepared["configuration"]["authority_uuid"]
        with JobStore.open(places["job_store"], authority_uuid=uuid, incarnation="fixture", clock=lambda: NOW):
            pass
        with ControlStore.open(places["control_store"], incarnation="fixture", clock=lambda: NOW):
            pass
        argv = ["recovery-item", "--instance", self.state, "--store", places["job_store"], "--control", places["control_store"], "--authority", places["authority_store"], "--authority-uuid", uuid, "--incarnation", "read-default-owners", "--participant", "baton.approver", "--failure", "not-yet-recorded"]
        said = io.StringIO()
        with redirect_stderr(said):
            code = job_manager.main(argv, clock=lambda: NOW, stream=io.StringIO())
        self.assertEqual(code, 1)
        self.assertIn("holds no retained failure", said.getvalue())
        for flag in ("--store", "--control", "--authority"):
            with self.subTest(flag=flag):
                other = os.path.join(self.root, "other-" + flag[2:] + ".sqlite3")
                if flag == "--store":
                    with JobStore.open(other, authority_uuid=uuid, incarnation="other", clock=lambda: NOW):
                        pass
                elif flag == "--control":
                    with ControlStore.open(other, incarnation="other", clock=lambda: NOW):
                        pass
                changed = list(argv)
                changed[changed.index(flag) + 1] = other
                said = io.StringIO()
                with redirect_stderr(said):
                    code = job_manager.main(changed, clock=lambda: NOW, stream=io.StringIO())
                self.assertEqual(code, 1)
                self.assertIn("owns", said.getvalue())
                self.assertNotIn("holds no retained failure", said.getvalue())
