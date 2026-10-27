"""W361912 — creating an ordinary Job from a versioned template.

WHAT THESE CASES ARE ABOUT. `creation.create_template_job` composes four
owners over one real disposable Job store: it reserves an identity, authorizes
a Work, publishes a deployment binding, asks the selector whether the result
can be served, takes the submission through W361910's accepted consumption
contract and records it. So the cases drive the REAL store -- the reservation
rows, the journal, `submission.submit`, the projection -- and fake only the
three owners that live in other processes' files.

AND THE ONE THING A SUBMISSION CANNOT IDENTIFY. W361910's acceptance review:
"Task statement, acceptance and work scope can differ without changing the
legacy submission; a submission signature alone is therefore insufficient to
identify that complete selected intent." `ChangedIntent` below drives exactly
that: two requests whose normalized submissions are byte-identical and whose
resolutions are not, where `submission.submit` would replay and this operation
must refuse.
"""

import json
import threading
import unittest
from contextlib import contextmanager

from baton_v12.contracts import ContractRefusal, digest
from baton_v12.job_manager import (create_template_job, created_job_of,
                                   created_job_rows, stage_rows, stages_of,
                                   status, submit, templates)
from baton_v12.job_manager import creation, documents, execution_limits
from baton_v12.job_manager.creation import resolution_of
from baton_v12.job_manager.submission import (boundary_seconds,
                                              execution_limits_of,
                                              submission_of)

if __package__:
    from .fixtures import (NOW, UUID, WORK_A, FakeOperations, JobManagerCase,
                           job, stage, submission)
else:
    from fixtures import (NOW, UUID, WORK_A, FakeOperations, JobManagerCase,
                          job, stage, submission)

TASK = "w361912-a"
JOB = "job-w361912-a"
STATEMENT = "Create ordinary Jobs through manager-owned template admission."
CRITERION = "A created Job is recorded, bound and servable."
WORK_SCOPE = ("v12/python/src/baton_v12/job_manager/creation.py",)
TEST_SCOPE = ("v12/python/tests/job_manager/test_creation.py",)
INPUT = "sha256:" + "1" * 64
POLICY = "sha256:" + "2" * 64
IMPLEMENTATION_PROFILE = "sha256:" + "a" * 64
REVIEW_PROFILE = "sha256:" + "b" * 64
PRODUCER = "implementation-worker"
REVIEWER = "review-worker"

# The identity every stand-in answers for, rebound per case to that case's own
# disposable root -- `test_fresh_attempt`'s rule, and for its reason: a
# fixture declaring a fictional path would be declaring another deployment.
CURRENT = {}
STAND_IN = {"root": "/does/not/exist", "job_store": "/does/not/exist/jobs",
            "control_store": "/does/not/exist/control",
            "authority_store": "/does/not/exist/authority",
            "authority_uuid": UUID}


def request(**named):
    held = {"schema": templates.REQUEST_SCHEMA,
            "task": {"task_id": TASK, "statement": STATEMENT},
            "source_selection": creation.INSTALLED_SOURCE,
            "scope": {"work": list(WORK_SCOPE), "tests": list(TEST_SCOPE)},
            "acceptance": [CRITERION]}
    held.update(named)
    return held


class FakeDerivation:
    """What the deployment says about the workers it installed."""

    def __init__(self, work_id=WORK_A, input_digest=INPUT,
                 policy_digest=POLICY, profiles=None, identity=None,
                 refusal=None, task=None):
        self.answer = {
            "work_id": work_id, "input_digest": input_digest,
            "policy_digest": policy_digest,
            "profiles": {"implementation": {
                             "profile_name": "reference",
                             "profile_digest": IMPLEMENTATION_PROFILE},
                         "review": {"profile_name": "reviewer",
                                    "profile_digest": REVIEW_PROFILE}}
            if profiles is None else profiles}
        self.refusal = refusal
        self.calls = 0
        self.selections = []
        # W363066: WHETHER THIS DEPLOYMENT COMPOSES A PER-JOB TASK AT ALL.
        # `None` is the deployment that does not -- four answered members, and
        # its Jobs run the installed task exactly as every Job did before
        # that Work. A composer is a callable so a case can see the selection
        # it was handed.
        self.task = task
        self._identity = identity

    def instance(self):
        return self._identity or CURRENT.get("identity") or STAND_IN

    def derived(self, selection=None):
        self.calls += 1
        if selection is not None:
            self.selections.append(json.loads(json.dumps(selection)))
        if self.refusal is not None:
            raise self.refusal
        held = json.loads(json.dumps(self.answer))
        if selection is None or self.task is None:
            return held
        return dict(held, **self.task(selection))


class FakeAuthorization:
    """One Work, and a record of whether anything was created."""

    def __init__(self, state="open", known=True, identity=None):
        self.state = state
        self.known = known
        self.created = []
        self._identity = identity

    def instance(self):
        return self._identity or CURRENT.get("identity") or STAND_IN

    def work_of(self, work_id):
        if not self.known:
            return None
        return {"work_id": work_id, "state": self.state, "phase": "queued"}

    def create_work(self, work_id, *, operation_id):
        self.created.append((work_id, operation_id))
        self.known = True
        return {"work_id": work_id, "state": "open", "phase": "queued"}


class FakeBinding:
    """The deployment, with the new-Job bind recorded rather than performed."""

    def __init__(self, bound=(), serving=None, work_id=WORK_A,
                 identity=None, refusal=None):
        self.bound = {one: {"job_id": one, "job_work_id": work_id,
                            "source_worker_id": PRODUCER}
                      for one in bound}
        self._serving = ({"implementation": [PRODUCER],
                          "review": [REVIEWER]}
                         if serving is None else serving)
        self._work_id = work_id
        self.created = []
        self.asked = []
        self.refusal = refusal
        self._identity = identity

    def instance(self):
        return self._identity or CURRENT.get("identity") or STAND_IN

    def binding_of(self, job_id):
        return self.bound.get(job_id)

    def create_binding(self, job_id, *, work_id, template_version):
        if self.refusal is not None:
            raise self.refusal
        self.created.append((job_id, work_id, template_version))
        self.bound[job_id] = {"job_id": job_id, "job_work_id": work_id,
                              "source_worker_id": PRODUCER}
        return self.bound[job_id]

    def serving(self, job_id, *, stage, job):
        # THE FAKE RECORDS WHAT IT WAS ASKED, because the operands are the
        # point: a case asserts the DERIVED digests and each stage's OWN
        # profile reached this port rather than the implementation's twice.
        self.asked.append((job_id, dict(stage), dict(job)))
        return list(self._serving.get(stage["kind"], ()))


class FakeOwnership:
    """The instance guard, recorded rather than taken."""

    def __init__(self, holder="control.sqlite3", refusal=None, running=None,
                 lock=None, overlap=None, identity=None, between=None):
        self.holder = holder
        self.refusal = refusal
        self.held_count = 0
        self.released = 0
        self.running = set() if running is None else running
        self.lock = threading.Lock() if lock is None else lock
        self.overlap = overlap
        self.between = between
        self._identity = identity

    def instance(self):
        return self._identity or CURRENT.get("identity") or STAND_IN

    @contextmanager
    def held(self):
        if self.refusal is not None:
            raise self.refusal
        self.held_count += 1
        try:
            yield self
        finally:
            self.released += 1

    @contextmanager
    def invocation(self, job_id):
        with self.lock:
            if job_id in self.running:
                if self.overlap is not None:
                    self.overlap.set()
                raise ContractRefusal(
                    "refused", "precondition",
                    f"another creation of {job_id!r} is in flight")
            self.running.add(job_id)
        try:
            if self.between is not None:
                self.between()
            if self.overlap is not None:
                self.overlap.wait(timeout=20)
            yield
        finally:
            with self.lock:
                self.running.discard(job_id)


class CreationCase(JobManagerCase):
    """One real Job store, one strict operations fake, four stand-in owners."""

    def setUp(self):
        super().setUp()
        self.jobs = self.store()
        self.acts = FakeOperations()
        self.stand_in = dict(STAND_IN, root=self.root,
                             job_store=self.job_path,
                             control_store=self.control_path)
        held = CURRENT.get("identity")
        CURRENT["identity"] = self.stand_in
        self.addCleanup(CURRENT.__setitem__, "identity", held)
        self.derivation = FakeDerivation()
        self.authorization = FakeAuthorization()
        self.binding = FakeBinding()
        self.ownership = FakeOwnership()

    def created(self, **named):
        held = {"request": request(), "derivation": self.derivation,
                "authorization": self.authorization,
                "binding": self.binding, "ownership": self.ownership}
        held.update(named)
        return create_template_job(self.jobs, self.acts, **held)

    def refused(self, **named):
        with self.assertRaises(ContractRefusal) as caught:
            self.created(**named)
        return caught.exception

    def rows(self):
        return [dict(one) for one in created_job_rows(self.jobs)]


class TheCreation(CreationCase):
    """What one ordinary creation actually does."""

    def test_the_answer_names_the_job_its_work_and_its_stages(self):
        held = self.created()
        self.assertEqual(held["job_id"], JOB)
        self.assertEqual(held["work_id"], WORK_A)
        self.assertEqual(held["submission_id"], f"sub-{JOB}")
        self.assertEqual(held["stages"],
                         [f"{JOB}/implementation", f"{JOB}/review"])
        self.assertEqual(held["recorded_at"], NOW)

    def test_the_job_is_really_recorded_and_its_stages_gated(self):
        """THE STORE IS THE PROOF, not the answer document.

        A creation that composed a correct-looking answer and recorded
        nothing would pass every assertion about its own return value.
        """
        self.created()
        self.assertEqual([row["stage_id"] for row in stage_rows(self.jobs)],
                         [f"{JOB}/implementation", f"{JOB}/review"])
        document = status(self.jobs, self.acts, observed_at=NOW)
        states = {one["stage_id"]: one["state"]
                  for entry in document["jobs"] for one in entry["stages"]}
        self.assertEqual(states, {f"{JOB}/implementation": "queued",
                                  f"{JOB}/review": "blocked"})

    def test_both_stages_run_under_the_one_derived_work(self):
        self.created()
        rows = {one["kind"]: one for one in stages_of(self.jobs, JOB)}
        self.assertEqual(rows["implementation"]["work_id"], WORK_A)
        self.assertEqual(rows["review"]["work_id"], WORK_A)

    def test_every_digest_comes_from_the_deployment_and_none_from_the_request(
            self):
        """THE WHOLE POINT OF THE OPERATION, asserted as an absence.

        The request carries no input digest, no policy digest, no profile and
        no Work. Each one appears in the recorded Job because the derivation
        port answered it.
        """
        written = json.dumps(request())
        for member in ('"source"', '"input_digest"', '"policy_digest"',
                       '"profiles"', '"work_id"', '"profile_digest"',
                       '"profile_name"', '"stages"'):
            self.assertNotIn(member, written,
                             f"{member} must not be an operator's to supply")
        held = self.created()
        self.assertEqual(held["source"],
                         {"input_digest": INPUT, "policy_digest": POLICY})
        rows = {one["kind"]: one for one in stages_of(self.jobs, JOB)}
        self.assertEqual(rows["implementation"]["profile_digest"],
                         IMPLEMENTATION_PROFILE)
        self.assertEqual(rows["review"]["profile_digest"], REVIEW_PROFILE)
        self.assertEqual(rows["implementation"]["profile_name"], "reference")
        self.assertEqual(rows["review"]["profile_name"], "reviewer")

    def test_the_two_scopes_stay_separate_through_the_creation(self):
        """R3 OF THE RESOLVER, PRESERVED BY ITS CONSUMER.

        The selected work scope is product source here and the test scope is
        a test path, and only the second reaches `test_scope`.
        """
        held = self.created()
        self.assertEqual(held["scope"],
                         {"work": list(WORK_SCOPE),
                          "tests": list(TEST_SCOPE)})
        stored = json.loads(submission_of(self.jobs,
                                          f"sub-{JOB}")["document"])
        self.assertEqual(stored["jobs"][0]["test_scope"], list(TEST_SCOPE))
        for path in WORK_SCOPE:
            self.assertNotIn(path, stored["jobs"][0]["test_scope"])

    def test_the_statement_and_acceptance_survive_where_the_submission_cannot(
            self):
        held = self.created()
        self.assertEqual(held["task"]["statement"], STATEMENT)
        self.assertEqual(held["acceptance"], [CRITERION])
        stored = json.loads(submission_of(self.jobs,
                                          f"sub-{JOB}")["document"])
        self.assertNotIn(STATEMENT, json.dumps(stored))
        self.assertNotIn(CRITERION, json.dumps(stored))

    def test_the_answer_carries_the_full_resolution_and_its_digest(self):
        held = self.created()
        stored = resolution_of(self.jobs, JOB)
        self.assertEqual(held["resolution_digest"],
                         templates.resolution_digest(stored))
        self.assertEqual(stored["task"]["statement"], STATEMENT)
        self.assertEqual(stored["acceptance"], [CRITERION])
        self.assertIsNone(resolution_of(self.jobs, "job-nobody-created"))
        self.assertEqual(held["template"]["version"],
                         templates.IMPLEMENTATION_REVIEW)
        self.assertEqual(held["template"]["origin"], "configured-default")

    def test_an_explicit_template_selection_travels_and_is_shown(self):
        held = self.created(request=request(
            template=templates.IMPLEMENTATION_REVIEW))
        self.assertEqual(held["template"]["origin"], "request")
        self.assertEqual(held["template"]["version"],
                         templates.IMPLEMENTATION_REVIEW)

    def test_the_reservation_is_durable_and_records_the_digest(self):
        held = self.created()
        rows = self.rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["job_id"], JOB)
        self.assertEqual(rows[0]["state"], "created")
        self.assertEqual(rows[0]["resolution_digest"],
                         held["resolution_digest"])
        self.assertEqual(rows[0]["template_version"],
                         templates.IMPLEMENTATION_REVIEW)
        self.assertEqual(rows[0]["work_id"], WORK_A)
        self.assertIsNotNone(rows[0]["created_at"])
        self.assertEqual(created_job_of(self.jobs, JOB)["job_id"], JOB)
        self.assertIsNone(created_job_of(self.jobs, "job-nobody-created"))

    def test_the_work_is_reused_rather_than_created(self):
        held = self.created()
        self.assertEqual(held["work"]["state"], "reused")
        self.assertEqual(self.authorization.created, [])

    def test_a_work_that_does_not_exist_yet_is_created_replayably(self):
        self.authorization.known = False
        held = self.created(authorization=self.authorization)
        self.assertEqual(held["work"]["state"], "created")
        self.assertEqual(self.authorization.created,
                         [(WORK_A, f"{creation.CREATE_KIND}.work:{WORK_A}")])

    def test_the_binding_is_published_through_its_owner(self):
        held = self.created()
        self.assertEqual(self.binding.created,
                         [(JOB, WORK_A, templates.IMPLEMENTATION_REVIEW)])
        self.assertEqual(held["binding"]["job_id"], JOB)

    def test_a_binding_already_configured_is_used_rather_than_added(self):
        self.binding = FakeBinding(bound=(JOB,))
        held = self.created(binding=self.binding)
        self.assertEqual(self.binding.created, [])
        self.assertEqual(held["binding"]["job_id"], JOB)

    def test_the_selector_is_asked_for_every_stage_with_its_own_profile(self):
        """THE OPERANDS ARE THE SUBMITTED ONES, per stage.

        `_job_workers` was corrected for deriving compatibility from the
        implementation kind alone, which reserved a review worker on another
        Work. This asserts both kinds were asked, each with its own profile.
        """
        held = self.created()
        asked = {stage["kind"]: (stage, job)
                 for _job_id, stage, job in self.binding.asked}
        self.assertEqual(sorted(asked), ["implementation", "review"])
        self.assertEqual(asked["implementation"][0]["profile_digest"],
                         IMPLEMENTATION_PROFILE)
        self.assertEqual(asked["review"][0]["profile_digest"], REVIEW_PROFILE)
        for _kind, (_stage, entry) in asked.items():
            self.assertEqual(entry["input_digest"], INPUT)
            self.assertEqual(entry["policy_digest"], POLICY)
        self.assertEqual(held["servable"],
                         {"implementation": [PRODUCER], "review": [REVIEWER]})

    def test_the_instance_guard_is_held_for_the_whole_creation(self):
        self.created()
        self.assertEqual(self.ownership.held_count, 1)
        self.assertEqual(self.ownership.released, 1)

    def test_the_derivation_is_read_exactly_once_inside_the_guard(self):
        """CORRECTED. Review 2026-10-26T19-22-51Z R2.

        The first candidate read the derivation twice -- once to compose the
        operands and once inside the guard -- and compared the two. That
        comparison is how a replay came to depend on a fact the caller never
        stated. Nothing is composed outside the guard now, so there is one
        reading and nothing to compare it with.
        """
        self.created()
        self.assertEqual(self.derivation.calls, 1)
        self.assertEqual(self.ownership.held_count, 1)


class ReplayAndIdentity(CreationCase):
    """One identity, one creation, and what a second request is told."""

    def test_the_same_request_replays_its_recorded_answer(self):
        first = self.created()
        created = len(self.binding.created)
        second = self.created()
        self.assertEqual(second, first)
        self.assertEqual(len(self.binding.created), created,
                         "a replay publishes no second binding")
        self.assertEqual(len(self.rows()), 1)
        self.assertEqual([row["job_id"] for row in stage_rows(self.jobs)],
                         [JOB, JOB])

    def test_a_replay_asks_no_owner_anything(self):
        """A COMPLETED CREATION CANNOT START REFUSING LATER.

        `fresh_attempt.admit`'s rule: re-deriving a recorded operation's
        preconditions means the deployment moving on turns a finished act
        into a refusal. So a replay answers before the guard is taken.

        AND THE ASSERTIONS ARE REAL NOW. Review R2: the first version of this
        case reset `derivation.calls` and never asserted it, so its own
        comment promised more than the code delivered. Every counter it
        resets is checked.
        """
        first = self.created()
        self.derivation.calls = 0
        self.ownership.held_count = 0
        self.binding.asked.clear()
        self.authorization.known = False
        self.binding.refusal = ContractRefusal("refused", "precondition",
                                               "the deployment moved on")
        second = self.created()
        self.assertEqual(second, first)
        self.assertEqual(self.derivation.calls, 0)
        self.assertEqual(self.ownership.held_count, 0)
        self.assertEqual(self.authorization.created, [])
        self.assertEqual(self.binding.asked, [])

    def test_an_identity_an_ordinary_submission_holds_refuses(self):
        submit(self.jobs, submission(submission_id="sub-other",
                                     jobs=[job(JOB, stages=[
                                         stage("implementation", WORK_A)])]))
        caught = self.refused()
        self.assertIn(JOB, caught.message)
        self.assertIn("already recorded", caught.message)
        self.assertEqual(self.binding.created, [],
                         "nothing is published for a refused creation")
        self.assertEqual(self.authorization.created, [])

    def test_a_submission_identity_another_document_recorded_refuses(self):
        submit(self.jobs, submission(submission_id=f"sub-{JOB}",
                                     jobs=[job("job-elsewhere", stages=[
                                         stage("implementation", WORK_A)])]))
        caught = self.refused()
        self.assertIn(f"sub-{JOB}", caught.message)
        self.assertEqual(self.binding.created, [])

    def test_a_chosen_submission_identity_is_used_and_derived_otherwise(self):
        held = self.created(request=request(
            task={"task_id": TASK, "statement": STATEMENT,
                  "submission_id": "sub-chosen"}))
        self.assertEqual(held["submission_id"], "sub-chosen")
        self.assertEqual(self.rows()[0]["submission_id"], "sub-chosen")

    def test_a_chosen_job_identity_is_used_and_derived_otherwise(self):
        self.assertEqual(creation.job_id_for(TASK), JOB)
        held = self.created(request=request(
            task={"task_id": TASK, "statement": STATEMENT,
                  "job_id": "job-chosen"}))
        self.assertEqual(held["job_id"], "job-chosen")

    def test_two_creations_sharing_one_submission_identity_refuse(self):
        self.created(request=request(
            task={"task_id": TASK, "statement": STATEMENT,
                  "submission_id": "sub-shared"}))
        caught = self.refused(request=request(
            task={"task_id": "w361912-b", "statement": STATEMENT,
                  "submission_id": "sub-shared"}))
        # THE JOURNAL ANSWERS FIRST AND NAMES THE SUBMISSION OPERATION, which
        # is the more actionable of the two refusals: the remedy is another
        # submission identity, and an operation's outcome is immutable.
        self.assertIn("sub-shared", caught.message)
        self.assertIn("another submission identity", caught.message)
        self.assertEqual(len(self.rows()), 1)

    def test_an_identity_a_fresh_attempt_reserved_refuses(self):
        """THE TWO RESERVATION RELATIONS SEE EACH OTHER.

        A creation and a retry are different intents and keep separate
        relations, and an identity either one holds is not free for the
        other -- which `_reserved` checks inside the same lock rather than
        discovering at `submit`.
        """
        submit(self.jobs, submission(submission_id="sub-prior",
                                     jobs=[job("job-prior", stages=[
                                         stage("implementation", WORK_A)])]))
        self.jobs._connection.execute(
            "INSERT INTO fresh_attempts (job_id, prior_job_id, "
            "prior_attempt_ids, work_id, submission_id, state, request, "
            "submission_signature, intended_at, admitted_at, incarnation) "
            "VALUES (?, 'job-prior', '[]', ?, 'sub-retry', 'intended', "
            "'{}', 'x', ?, NULL, 'jobs-1')", (JOB, WORK_A, NOW))
        caught = self.refused()
        self.assertIn("fresh attempt", caught.message)
        self.assertEqual(self.binding.created, [])

    def test_a_concurrent_creation_of_one_identity_is_one_creation(self):
        overlap = threading.Event()
        shared = FakeOwnership(running=set(), lock=threading.Lock(),
                               overlap=overlap)
        answers = []
        refusals = []

        def run():
            # THE SECOND STORE HANDLE IS OPENED AND CLOSED IN ITS OWN THREAD.
            # SQLite connections belong to the thread that made them, and a
            # handle registered for cleanup on the main thread would be closed
            # from the wrong one -- which is a defect in the case rather than
            # in the product.
            from baton_v12.job_manager import JobStore

            beside_store = JobStore.open(self.job_path, authority_uuid=UUID,
                                         incarnation="jobs-2",
                                         clock=self.clock)
            try:
                answers.append(create_template_job(
                    beside_store, self.acts,
                    request=request(), derivation=FakeDerivation(),
                    authorization=self.authorization, binding=self.binding,
                    ownership=shared))
            except ContractRefusal as caught:
                refusals.append(caught)
            finally:
                beside_store.close()

        beside = threading.Thread(target=run)
        beside.start()
        try:
            self.created(ownership=shared)
        except ContractRefusal as caught:
            refusals.append(caught)
        else:
            answers.append("first")
        overlap.set()
        beside.join(timeout=30)
        self.assertEqual(len(answers) + len(refusals), 2)
        self.assertEqual(len(refusals), 1, refusals)
        self.assertEqual(len(self.rows()), 1)
        self.assertLessEqual(len(self.binding.created), 1)


class ChangedIntent(CreationCase):
    """The acceptance sentence this Work exists to honour.

    W361910's acceptance review: "Task statement, acceptance and work scope
    can differ without changing the legacy submission; a submission signature
    alone is therefore insufficient to identify that complete selected
    intent."
    """

    def moved(self, **named):
        """One request differing ONLY in a member the submission never sees."""
        held = request()
        held.update(named)
        return held

    def test_a_changed_statement_is_a_different_creation(self):
        first = self.created()
        changed = self.moved(task={"task_id": TASK,
                                   "statement": "something else entirely"})
        # THE SUBMISSIONS ARE BYTE-IDENTICAL, which is the whole difficulty.
        resolved = templates.resolve(
            {k: v for k, v in changed.items() if k != "source_selection"}
            | {"task": {"job_id": JOB, "work_id": WORK_A,
                        "statement": "something else entirely"},
               "source": {"input_digest": INPUT, "policy_digest": POLICY}},
            configuration={"schema": templates.CONFIGURATION_SCHEMA,
                           "profiles": self.derivation.answer["profiles"]})
        self.assertEqual(resolved["submission"],
                         resolution_of(self.jobs, JOB)["submission"])
        self.assertNotEqual(templates.resolution_digest(resolved),
                            first["resolution_digest"])
        caught = self.refused(request=changed)
        self.assertIn("DIFFERENT request", caught.message)
        self.assertEqual(self.rows()[0]["resolution_digest"],
                         first["resolution_digest"],
                         "the recorded creation is untouched")

    def test_a_changed_acceptance_contract_is_a_different_creation(self):
        first = self.created()
        caught = self.refused(request=self.moved(
            acceptance=["a completely different requirement"]))
        self.assertIn("DIFFERENT request", caught.message)
        self.assertEqual(self.rows()[0]["resolution_digest"],
                         first["resolution_digest"])

    def test_a_changed_work_scope_is_a_different_creation(self):
        self.created()
        caught = self.refused(request=self.moved(
            scope={"work": ["v12/python/tools/job_manager.py"],
                   "tests": list(TEST_SCOPE)}))
        self.assertIn("DIFFERENT request", caught.message)

    def test_submit_alone_would_have_replayed_every_one_of_those(self):
        """THE CONTROL CASE, so the refusals above are not a coincidence.

        The same three changed requests produce one normalized submission, and
        `submission.submit` replays it -- which is correct for `submit` and is
        exactly why the reservation records the resolution digest.
        """
        self.created()
        document = resolution_of(self.jobs, JOB)["submission"]
        first = submit(self.jobs, document)
        again = submit(self.jobs, json.loads(json.dumps(document)))
        self.assertEqual(first, again)

    def test_a_changed_override_is_a_different_creation(self):
        self.created()
        caught = self.refused(request=self.moved(
            overrides={"execution_limits": {"provider_turn_seconds": 5400}}))
        self.assertIn("DIFFERENT request", caught.message)

    def test_a_changed_derivation_is_the_SAME_creation_and_replays(self):
        """CORRECTED, AND THIS IS R2 ITSELF.

        The first candidate treated the deployment's derived facts as part of
        the caller's intent, so an identical request repeated after the pool
        moved was refused as a different creation. The reviewer's probe did
        exactly this. What the caller asked for and what the deployment
        derived are two facts: the first identifies the creation, the second
        is recorded as its provenance.
        """
        first = self.created()
        moved = FakeDerivation(policy_digest="sha256:" + "9" * 64)
        second = self.created(derivation=moved)
        self.assertEqual(second, first)
        self.assertEqual(moved.calls, 0,
                         "a replay asks the deployment nothing at all")
        self.assertEqual(len(self.rows()), 1)
        self.assertEqual(self.rows()[0]["resolution_digest"],
                         first["resolution_digest"],
                         "the recorded provenance is the first creation's")


class WhatItRefusesBeforeAnyEffect(CreationCase):
    """Nothing is published for a request that cannot be honoured."""

    def test_a_request_this_operation_owns_refuses_before_any_derivation(self):
        """THE MEMBERS `_asked` OWNS COST THE DEPLOYMENT NOTHING.

        The schema, the task and the source selection are this operation's
        own contract, so a request malformed in one of them is refused before
        the deployment is asked to read its configuration at all.
        """
        for named in ({"schema": "baton.v12.job-template-request/9"},
                      {"task": {}}, {"task": {"task_id": TASK}},
                      {"task": {"statement": STATEMENT}},
                      {"task": {"task_id": "", "statement": STATEMENT}},
                      {"source_selection": "somewhere-else"},
                      {"whatever": 1}):
            with self.subTest(named=sorted(named)):
                caught = self.refused(request=self.request_with(named))
                self.assertIsInstance(caught, ContractRefusal)
        self.assertEqual(self.derivation.calls, 0,
                         "a request this operation owns costs nothing")
        self.assertEqual(self.binding.created, [])
        self.assertEqual(self.rows(), [])

    def test_a_request_the_resolver_owns_refuses_before_any_effect(self):
        """AND THE RESOLVER'S OWN MEMBERS REFUSE WITH NOTHING PUBLISHED.

        The two scopes, the acceptance list and the overrides are the
        accepted resolver's contract, reached rather than restated here --
        so these are refused one call later, after the derivation has been
        read and before any owner is mutated.
        """
        for named in ({"acceptance": []}, {"acceptance": None},
                      {"scope": {"work": [], "tests": []}},
                      {"scope": {"work": list(WORK_SCOPE)}},
                      {"scope": ["v12"]},
                      {"overrides": {"terminal_policy": "discard"}},
                      {"overrides": {"execution_limits": {
                          "provider_turn_seconds": 0}}},
                      {"template": "baton.v12.job-template.nope/1"}):
            with self.subTest(named=sorted(named)):
                caught = self.refused(request=self.request_with(named))
                self.assertIsInstance(caught, ContractRefusal)
        self.assertEqual(self.binding.created, [])
        self.assertEqual(self.authorization.created, [])
        self.assertEqual(self.rows(), [])
        self.assertEqual([row["job_id"] for row in stage_rows(self.jobs)], [])

    def request_with(self, named):
        held = request()
        held.update(named)
        return held

    def test_a_request_that_is_not_a_document_refuses(self):
        for value in (None, [], "a request", 1):
            with self.subTest(value=value):
                self.refused(request=value)

    def test_an_absent_owner_port_refuses_naming_it(self):
        for member in ("derivation", "authorization", "binding", "ownership"):
            caught = self.refused(**{member: None})
            self.assertIn(member.replace("_", " "), caught.message.lower())

    def test_a_derivation_missing_a_member_refuses(self):
        for member in creation.DERIVATION_MEMBERS:
            held = FakeDerivation()
            del held.answer[member]
            with self.subTest(member=member):
                caught = self.refused(derivation=held)
                self.assertIn(member, caught.message)
        self.assertEqual(self.rows(), [])

    def test_a_derivation_answering_a_malformed_profile_refuses(self):
        for profiles in ({}, {"implementation": None},
                         {"implementation": {"profile_name": "reference"}},
                         {"implementation": {"profile_name": None,
                                             "profile_digest": "x"}},
                         {"implementor": {"profile_name": "reference",
                                          "profile_digest": "x"}}):
            with self.subTest(profiles=sorted(profiles)):
                self.refused(derivation=FakeDerivation(profiles=profiles))
        self.assertEqual(self.rows(), [])

    def test_a_derivation_missing_the_review_profile_refuses(self):
        """AND IT REFUSES AT THE RESOLVER, naming the role.

        An invented profile is admitted by `documents` and only fails at
        `scheduler.reserve` as "no eligible review worker", long after the
        operator could tell why.
        """
        caught = self.refused(derivation=FakeDerivation(profiles={
            "implementation": {"profile_name": "reference",
                               "profile_digest": IMPLEMENTATION_PROFILE}}))
        self.assertIn("review", caught.message)
        self.assertEqual(self.rows(), [])

    def test_a_deployment_that_can_serve_no_stage_refuses(self):
        for serving in ({"implementation": [], "review": [REVIEWER]},
                        {"implementation": [PRODUCER], "review": []},
                        {}):
            self.setUp()
            with self.subTest(serving=sorted(serving)):
                caught = self.refused(
                    binding=FakeBinding(serving=serving))
                self.assertIn("ever run it", caught.message)
                # PAST THE RESERVATION, so it says so.
                self.assertIn("INCOMPLETE", caught.message)
                self.assertEqual(self.rows()[0]["state"], "intended")
                self.assertEqual(
                    [row["job_id"] for row in stage_rows(self.jobs)], [],
                    "no submission is recorded for an unservable Job")

    def test_a_closed_work_refuses_and_nothing_is_submitted(self):
        caught = self.refused(
            authorization=FakeAuthorization(state="closed"))
        self.assertIn("OPEN Work", caught.message)
        self.assertEqual([row["job_id"] for row in stage_rows(self.jobs)], [])

    def test_a_deployment_binding_another_work_refuses(self):
        self.binding = FakeBinding(bound=(JOB,), work_id="0000000a-W9")
        caught = self.refused(binding=self.binding)
        self.assertIn("0000000a-W9", caught.message)
        self.assertEqual([row["job_id"] for row in stage_rows(self.jobs)], [])

    def test_a_binding_owner_refusal_propagates_as_itself(self):
        """NOTHING IS CAUGHT AND TRANSLATED.

        `fresh_attempt._bound` catches nothing either, and W361910's R4
        review stated the rule: unexpected faults stay visible rather than
        being rewritten as "your deployment refused". A `BindingRefusal` is
        already an operator-facing sentence about the instance, so the thing
        it says reaches the operator unaltered -- and the reservation it
        leaves behind is what the next run continues from.
        """
        class _Owner(Exception):
            pass

        with self.assertRaises(_Owner) as caught:
            self.created(binding=FakeBinding(
                refusal=_Owner("install-inputs.json does not exist")))
        self.assertIn("install-inputs.json", str(caught.exception))
        self.assertEqual(self.rows()[0]["state"], "intended")
        self.assertEqual([row["job_id"] for row in stage_rows(self.jobs)], [])

    def test_no_broad_except_stands_between_a_fault_and_its_caller(self):
        """ASSERTED FROM THE SOURCE, not remembered.

        The one `except` this module may hold is the submission boundary's,
        which re-reports a `ContractRefusal` as the incomplete act it is.
        A catch-all anywhere on this path would turn this module's own
        defects into "your request is invalid".
        """
        import ast
        import pathlib as _pathlib

        source = _pathlib.Path(creation.__file__).read_text(encoding="utf-8")
        for node in ast.parse(source).body:
            if type(node) is not ast.FunctionDef:
                continue
            for piece in ast.walk(node):
                if type(piece) is not ast.ExceptHandler:
                    continue
                self.assertIsNotNone(piece.type,
                                      f"{node.name} holds a bare except")
                named = (piece.type.attr if type(piece.type) is ast.Attribute
                         else getattr(piece.type, "id", None))
                self.assertIn(named, ("ContractRefusal", "IntegrityError"),
                              f"{node.name} catches {named}")

    def test_owners_answering_for_two_instances_refuse(self):
        caught = self.refused(binding=FakeBinding(
            identity=dict(STAND_IN, root="/another/instance")))
        self.assertIn("different deployments", caught.message)
        self.assertEqual(self.derivation.calls, 0)

    def test_an_owner_answering_for_another_authority_refuses(self):
        caught = self.refused(authorization=FakeAuthorization(
            identity=dict(self.stand_in, authority_uuid="f" * 32)))
        self.assertIn("Authority", caught.message)

    def test_a_guard_this_process_cannot_take_refuses_before_reserving(self):
        caught = self.refused(ownership=FakeOwnership(
            refusal=ContractRefusal("refused", "precondition",
                                    "a serving manager holds this instance")))
        self.assertIn("serving manager", caught.message)
        self.assertEqual(self.rows(), [])
        self.assertEqual(self.binding.created, [])


class TheGenerationAgreement(CreationCase):
    """R1 of the resolver, preserved THROUGH the operation.

    W361910's acceptance review: "W361912 owns those existing acceptance
    obligations and must preserve the generation agreement through its
    operation rather than treating a precheck as authority."
    """

    def newer_generation(self, provider=7200):
        from unittest import mock

        newer = dict(execution_limits.GENERATIONS[
            execution_limits.CURRENT_GENERATION])
        newer["provider_turn"] = provider
        moved = max(execution_limits.GENERATIONS) + 1
        return (mock.patch.dict(execution_limits.GENERATIONS,
                                {moved: newer}),
                mock.patch.object(execution_limits, "CURRENT_GENERATION",
                                  moved), moved)

    def test_the_created_job_reports_the_ceilings_the_store_gives_it(self):
        held = self.created()
        reported = (held["execution_limits"]["boundaries"]
                    ["provider_turn"]["seconds"])
        self.assertEqual(reported, 3600)
        self.assertEqual(boundary_seconds(self.jobs, JOB, "provider_turn"),
                         reported)
        self.assertEqual(
            execution_limits_of(self.jobs, JOB)["compatibility_generation"],
            held["execution_limits"]
            ["compatibility_generation"])

    def test_an_override_reaches_the_store_through_the_creation(self):
        held = self.created(request=request(overrides={
            "execution_limits": {"provider_turn_seconds": 5400}}))
        self.assertEqual(resolution_of(self.jobs, JOB)["submission"]["schema"],
                         documents.SUBMISSION_SCHEMA)
        self.assertEqual(boundary_seconds(self.jobs, JOB, "provider_turn"),
                         5400)
        self.assertEqual(
            execution_limits_of(self.jobs, JOB)["requested"],
            {"provider_turn_seconds": 5400})

    def test_a_creation_under_a_moved_default_is_honest_about_it(self):
        """THE RESOLUTION IS COMPOSED AND CONSUMED INSIDE ONE OPERATION.

        So the generation the answer reports and the generation the store
        stamps are the same one by construction, which is what the resolver
        could only refuse about from outside.
        """
        generations, current, moved = self.newer_generation()
        with generations, current:
            held = self.created()
            self.assertEqual(
                held["execution_limits"]
                ["compatibility_generation"], moved)
            self.assertEqual(
                held["execution_limits"]["boundaries"]
                ["provider_turn"]["seconds"], 7200)
            self.assertEqual(
                boundary_seconds(self.jobs, JOB, "provider_turn"), 7200)
            self.assertEqual(
                execution_limits_of(self.jobs, JOB)[
                    "compatibility_generation"], moved)

    def test_the_consumption_contract_is_reached_rather_than_bypassed(self):
        """A STALE RESOLUTION CANNOT BE SUBMITTED BY THIS OPERATION.

        The generation is read at `submission_for_admission` time, so a
        default that moves between composing and consuming refuses with the
        reservation and the binding already published and NOTHING recorded.
        """
        from unittest import mock

        generations, current, moved = self.newer_generation()
        real = templates.submission_for_admission

        def moving(resolution, *, generation=None):
            with generations, current:
                return real(resolution, generation=generation)

        with mock.patch.object(templates, "submission_for_admission", moving):
            caught = self.refused()
        self.assertIn("no longer consumable", caught.message)
        self.assertIn(str(moved), caught.message)
        self.assertIn("INCOMPLETE", caught.message)
        self.assertEqual([row["job_id"] for row in stage_rows(self.jobs)], [])
        self.assertEqual(self.rows()[0]["state"], "intended")


class InterruptionAndRecovery(CreationCase):
    """What a crash between the cuts leaves, and how the next run finishes."""

    def test_a_creation_interrupted_after_the_binding_is_finished_by_a_rerun(
            self):
        """CUT B PUBLISHED, CUT C NOT. The intent row says so.

        The binding is inert while no Job exists, so what the operator sees
        is a reserved identity and a configured Job nothing selects -- and
        running the same request again records the submission and completes.
        """
        class _Interrupted(Exception):
            pass

        class _BindThenDie(FakeBinding):
            def serving(self, job_id, *, stage, job):
                raise _Interrupted("the process died after binding")

        dying = _BindThenDie()
        with self.assertRaises(_Interrupted):
            self.created(binding=dying)
        rows = self.rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["state"], "intended")
        self.assertIsNone(rows[0]["created_at"])
        self.assertEqual(rows[0]["incarnation"], "jobs-1")
        self.assertEqual(dying.created, [(JOB, WORK_A,
                                          templates.IMPLEMENTATION_REVIEW)])
        self.assertEqual([row["job_id"] for row in stage_rows(self.jobs)], [])
        # THE SAME REQUEST AGAIN, with the binding already published.
        held = self.created(binding=FakeBinding(bound=(JOB,)))
        self.assertEqual(held["job_id"], JOB)
        self.assertEqual(self.rows()[0]["state"], "created")
        self.assertEqual([row["stage_id"] for row in stage_rows(self.jobs)],
                         [f"{JOB}/implementation", f"{JOB}/review"])

    def test_a_reservation_held_by_another_incarnation_refuses_naming_it(self):
        """DECIDING AN UNSEEN MANAGER HAS STOPPED IS NOT THIS OPERATION'S.

        `fresh_attempt._acquired`'s rule: a holder continues its own
        interrupted work and a different incarnation is refused naming the
        holder rather than taking the work over.
        """
        class _Interrupted(Exception):
            pass

        class _Dying(FakeBinding):
            def create_binding(self, job_id, *, work_id, template_version):
                raise _Interrupted("died holding the reservation")

        with self.assertRaises(_Interrupted):
            self.created(binding=_Dying())
        self.assertEqual(self.rows()[0]["holder"], "jobs-1@control.sqlite3")
        other = self.store(incarnation="jobs-other")
        with self.assertRaises(ContractRefusal) as caught:
            create_template_job(
                other, self.acts, request=request(),
                derivation=FakeDerivation(),
                authorization=self.authorization, binding=FakeBinding(),
                ownership=self.ownership)
        self.assertIn("jobs-1@control.sqlite3", caught.exception.message)
        self.assertIn("same manager incarnation",
                      caught.exception.message)

    def test_the_same_incarnation_continues_its_own_interrupted_work(self):
        class _Interrupted(Exception):
            pass

        class _Dying(FakeBinding):
            def create_binding(self, job_id, *, work_id, template_version):
                raise _Interrupted("died holding the reservation")

        with self.assertRaises(_Interrupted):
            self.created(binding=_Dying())
        held = self.created()
        self.assertEqual(held["job_id"], JOB)
        self.assertEqual(self.rows()[0]["state"], "created")

    def test_a_reopened_store_replays_the_recorded_creation(self):
        """REPLAY SURVIVES A REOPEN, which is what makes it durable.

        The journal is in the store, not in this process, so a new store
        handle under a new incarnation answers the recorded creation.
        """
        first = self.created()
        self.jobs.close()
        again = self.store(incarnation="jobs-reopened")
        second = create_template_job(
            again, self.acts, request=request(),
            derivation=FakeDerivation(), authorization=self.authorization,
            binding=self.binding, ownership=self.ownership)
        self.assertEqual(second, first)
        self.assertEqual(len(created_job_rows(again)), 1)


class TheRetryContractIsPreserved(CreationCase):
    """A created Job is an ordinary Job, including for recovery."""

    def test_a_created_job_can_be_retried_by_the_existing_operation(self):
        """FRESH-ATTEMPT SEMANTICS ARE UNTOUCHED.

        `fresh_attempt._composed` copies the stored submission entry and
        renames it, so a Job this operation created carries forward exactly
        as a hand-submitted one does -- and this candidate adds no submission
        member for it to carry.
        """
        from baton_v12.job_manager.fresh_attempt import successor_of

        self.created()
        self.acts.frozen(f"{JOB}/implementation", "unable")
        self.assertEqual(successor_of(JOB), f"{JOB}-retry-2")
        stored = json.loads(submission_of(self.jobs,
                                          f"sub-{JOB}")["document"])
        self.assertEqual(sorted(stored["jobs"][0]),
                         sorted(documents.JOB_MEMBERS))

    def test_the_legacy_hand_authored_submission_still_records(self):
        recorded = submit(self.jobs, submission())
        self.assertEqual(recorded["jobs"], ["job-a", "job-b"])
        self.created()
        self.assertEqual(len(self.rows()), 1)
        self.assertEqual(
            sorted(one["job_id"] for one in created_job_rows(self.jobs)),
            [JOB])


class OneIdentityHasOneOwnerAcrossEveryEntryPoint(CreationCase):
    """R1: the exclusion is symmetric or it is not an exclusion.

    review-2026-10-26T19-22-51Z: `creation._reserved` wrote `template_jobs`
    and `submission._unclaimed` consulted only `fresh_attempts`. The
    reviewer's probe interrupted a creation immediately after its binding was
    published, called the real `submit` with the reserved Job identity and a
    DIFFERENT document, and it SUCCEEDED -- after which the creation refused
    at its own submit with its Work authorization and binding stranded, while
    telling the operator that repeating the request would finish it.

    There are three entry points into one Job identity space: ordinary
    submission, fresh-attempt retry and template creation. Every pair is
    driven here, in both arrival orders.
    """

    def interrupted(self):
        """A creation stopped immediately after its binding was published."""
        class _Stop(Exception):
            pass

        class _BindThenDie(FakeBinding):
            def serving(self, job_id, *, stage, job):
                raise _Stop("the process died after binding")

        dying = _BindThenDie()
        with self.assertRaises(_Stop):
            self.created(binding=dying)
        self.assertEqual(self.rows()[0]["state"], "intended")
        return dying

    def foreign(self, submission_id="foreign-submission", job_id=None):
        return submission(submission_id=submission_id,
                          jobs=[job(job_id or JOB, stages=[
                              stage("implementation", WORK_A)])])

    def test_the_reviewers_counterexample_now_refuses(self):
        """THE EXACT PROBE, AND NOTHING IS STRANDED.

        The foreign submission is refused, the creation's own reservation is
        intact, and running the same request again FINISHES it -- which is
        what the incomplete report says will happen and what the first
        candidate could no longer honour.
        """
        self.interrupted()
        with self.assertRaises(ContractRefusal) as caught:
            submit(self.jobs, self.foreign())
        self.assertIn(JOB, caught.exception.message)
        self.assertIn("RESERVED by a template creation",
                      caught.exception.message)
        self.assertIn("strand", caught.exception.message)
        self.assertEqual([row["job_id"] for row in stage_rows(self.jobs)], [])
        # AND THE PROMISE IN THE INCOMPLETE REPORT IS TRUE.
        held = self.created(binding=FakeBinding(bound=(JOB,)))
        self.assertEqual(held["job_id"], JOB)
        self.assertEqual(self.rows()[0]["state"], "created")
        self.assertEqual([row["stage_id"] for row in stage_rows(self.jobs)],
                         [f"{JOB}/implementation", f"{JOB}/review"])

    def test_a_foreign_submission_reusing_the_reserved_submission_id_refuses(
            self):
        """BY SUBMISSION NAME AS WELL AS BY JOB NAME.

        A reservation owns both names -- `submission._unclaimed`'s own W358969
        R12 correction -- and the creation's operation identity is derived
        from the submission id, so a second writer taking that name for
        another Job would collide with it after the binding was published.
        """
        self.interrupted()
        with self.assertRaises(ContractRefusal) as caught:
            submit(self.jobs, self.foreign(submission_id=f"sub-{JOB}",
                                           job_id="job-elsewhere"))
        self.assertIn(f"sub-{JOB}", caught.exception.message)
        self.assertIn("template creation", caught.exception.message)

    def test_a_refused_intruder_does_not_poison_the_holders_journal(self):
        """THE REFUSAL IS ORDINARY, NOT DURABLE.

        `submission._unclaimed` says why in as many words: this operation
        identity is derived from the submission id, which belongs to the
        RESERVATION HOLDER, so sealing a refusal under it would let an
        intruder's rejected document permanently block the one submission the
        reservation exists to admit.
        """
        self.interrupted()
        for _attempt in range(2):
            with self.assertRaises(ContractRefusal):
                submit(self.jobs, self.foreign(submission_id=f"sub-{JOB}",
                                               job_id="job-elsewhere"))
        held = self.created(binding=FakeBinding(bound=(JOB,)))
        self.assertEqual(held["submission_id"], f"sub-{JOB}")
        self.assertEqual(self.rows()[0]["state"], "created")

    def test_the_exact_reserved_submission_still_consumes_the_reservation(
            self):
        """ONLY THE EXACT DOCUMENT PASSES, which is the other half.

        A conflict check that refused everything would also refuse the
        creation's own submit, which is the submission the reservation exists
        to admit.
        """
        dying = self.interrupted()
        del dying
        from baton_v12.job_manager.creation import resolution_of

        document = resolution_of(self.jobs, JOB)["submission"]
        recorded = submit(self.jobs, document)
        self.assertEqual(recorded["jobs"], [JOB])

    def test_a_fresh_attempt_cannot_take_a_reserved_creation_identity(self):
        """THE SECOND PAIR, and the symmetry R1 asked for.

        A retry reserves `fresh_attempts`; a creation reserves
        `template_jobs`. Neither may take the other's name — and this drives
        the REAL `fresh_attempt.admit` through its own suite's owner fakes
        rather than reproducing its insert here, because a case that
        reimplemented the rule would assert against its own copy of it.
        """
        self.interrupted()
        if __package__:
            from . import test_fresh_attempt as retry
        else:
            import test_fresh_attempt as retry
        from baton_v12.job_manager import admit_fresh_attempt

        # A FAILED PRIOR JOB FOR THE RETRY TO REPEAT, built by that suite's
        # own helper shape: an implementation stage whose freeze was `unable`,
        # which the projection reads as `exceptional`.
        submit(self.jobs, submission(
            submission_id="sub-prior",
            jobs=[job("job-prior", stages=[stage("implementation", WORK_A)])]))
        self.acts.frozen("job-prior/implementation", "unable")
        held = retry.CURRENT.get("identity")
        retry.CURRENT["identity"] = self.stand_in
        self.addCleanup(retry.CURRENT.__setitem__, "identity", held)
        with self.assertRaises(ContractRefusal) as caught:
            admit_fresh_attempt(
                self.jobs, self.acts, prior_job_id="job-prior",
                exclusion=retry.FakeExclusion(),
                authorization=retry.FakeAuthorization(),
                binding=retry.FakeBinding(), ownership=retry.FakeOwnership(),
                job_id=JOB)
        self.assertIn("RESERVED by a template creation",
                      caught.exception.message)
        self.assertIn("strand", caught.exception.message)
        # AND THE CREATION'S OWN RESERVATION IS UNTOUCHED.
        self.assertEqual(self.rows()[0]["state"], "intended")

    def test_a_creation_cannot_take_a_reserved_retry_identity(self):
        """AND THE SAME PAIR FROM THE OTHER SIDE."""
        submit(self.jobs, submission(submission_id="sub-prior",
                                     jobs=[job("job-prior", stages=[
                                         stage("implementation", WORK_A)])]))
        self.jobs._connection.execute(
            "INSERT INTO fresh_attempts (job_id, prior_job_id, "
            "prior_attempt_ids, work_id, submission_id, state, request, "
            "submission_signature, intended_at, admitted_at, incarnation) "
            "VALUES (?, 'job-prior', '[]', ?, ?, 'intended', '{}', 'x', ?, "
            "NULL, 'jobs-1')", (JOB, WORK_A, f"sub-{JOB}", NOW))
        caught = self.refused()
        self.assertIn("RESERVED by a fresh attempt", caught.message)
        self.assertEqual(self.binding.created, [])
        self.assertEqual(self.rows(), [])

    def test_a_recorded_ordinary_job_blocks_a_creation_of_that_identity(self):
        """THE THIRD PAIR. A recorded Job is not a reservation but it is
        certainly not free, and finding that out at `submit` would be finding
        it out with a Work and a binding already published."""
        submit(self.jobs, submission(submission_id="sub-other",
                                     jobs=[job(JOB, stages=[
                                         stage("implementation", WORK_A)])]))
        caught = self.refused()
        self.assertIn("already recorded", caught.message)
        self.assertEqual(self.binding.created, [])
        self.assertEqual(self.authorization.created, [])

    def test_a_creation_then_an_ordinary_submission_of_another_job_is_fine(
            self):
        """THE EXCLUSION IS ABOUT IDENTITY, NOT ABOUT ENTRY POINTS.

        An unrelated ordinary submission alongside a created Job is the
        ordinary case and must not be refused by any of this.
        """
        self.created()
        recorded = submit(self.jobs, submission())
        self.assertEqual(recorded["jobs"], ["job-a", "job-b"])


class TheReplayIsTheCallersIntent(CreationCase):
    """R2: immutable caller intent, and what still refuses.

    review-2026-10-26T19-22-51Z required both halves and named the hazard:
    "Do not weaken changed-intent checks merely to pass the replay case."
    """

    def moved(self, **named):
        held = request()
        held.update(named)
        return held

    def test_an_identical_request_replays_after_a_reopen(self):
        """THE JOURNAL IS IN THE STORE, not in this process."""
        first = self.created()
        self.jobs.close()
        again = self.store(incarnation="jobs-reopened")
        moved = FakeDerivation(input_digest="sha256:" + "7" * 64)
        second = create_template_job(
            again, self.acts, request=request(), derivation=moved,
            authorization=self.authorization, binding=self.binding,
            ownership=self.ownership)
        self.assertEqual(second, first)
        self.assertEqual(moved.calls, 0)

    def test_an_identical_request_replays_when_the_derivation_is_unavailable(
            self):
        """A RECORDED CREATION DOES NOT DEPEND ON THE POOL STILL ANSWERING.

        The deployment's configuration can be gone entirely and the creation
        this store performed is still the creation it performed.
        """
        first = self.created()
        broken = FakeDerivation(refusal=ContractRefusal(
            "refused", "precondition", "deployment.json does not exist"))
        self.assertEqual(self.created(derivation=broken), first)
        self.assertEqual(broken.calls, 0)

    def test_an_identical_request_replays_when_the_default_generation_moved(
            self):
        from unittest import mock

        first = self.created()
        newer = dict(execution_limits.GENERATIONS[
            execution_limits.CURRENT_GENERATION])
        newer["provider_turn"] = 7200
        at = max(execution_limits.GENERATIONS) + 1
        with mock.patch.dict(execution_limits.GENERATIONS, {at: newer}), \
                mock.patch.object(execution_limits, "CURRENT_GENERATION", at):
            self.assertEqual(self.created(), first)

    def test_every_caller_stated_member_still_refuses_when_it_changes(self):
        """THE CHANGED-INTENT CHECK IS NOT WEAKENED, member by member."""
        first = self.created()
        for named in (
                {"task": {"task_id": TASK,
                          "statement": "something else entirely"}},
                {"acceptance": ["a completely different requirement"]},
                {"scope": {"work": ["v12/python/tools/job_manager.py"],
                           "tests": list(TEST_SCOPE)}},
                {"scope": {"work": list(WORK_SCOPE), "tests": []}},
                {"template": templates.IMPLEMENTATION_REVIEW},
                {"overrides": {"execution_limits": {
                    "provider_turn_seconds": 5400}}}):
            with self.subTest(named=sorted(named)):
                caught = self.refused(request=self.moved(**named))
                self.assertIn("DIFFERENT request", caught.message)
                self.assertEqual(self.rows()[0]["request_digest"],
                                 first["resolution"]["request_digest"]
                                 if "resolution" in first
                                 else self.rows()[0]["request_digest"])
        self.assertEqual(len(self.rows()), 1)
        self.assertEqual([row["stage_id"] for row in stage_rows(self.jobs)],
                         [f"{JOB}/implementation", f"{JOB}/review"])

    def test_one_intent_spelled_two_ways_is_one_creation(self):
        """THE DIGEST IS OVER THE OWNED REQUEST, not the caller's bytes.

        A different member order is the same intent, which is
        `documents.owned_submission`'s own reason for normalizing.
        """
        first = self.created()
        reordered = {}
        for name in reversed(list(request())):
            reordered[name] = request()[name]
        self.assertEqual(list(reordered), list(reversed(list(request()))))
        self.assertEqual(self.created(request=reordered), first)

    def test_the_recorded_provenance_is_the_first_creations_derivation(self):
        """REPLAY DOES NOT REWRITE WHAT WAS CREATED.

        The answer and the row still describe the pool the Job was actually
        admitted against, which is the honest thing for them to say.
        """
        first = self.created()
        self.created(derivation=FakeDerivation(
            policy_digest="sha256:" + "5" * 64))
        self.assertEqual(self.rows()[0]["resolution_digest"],
                         first["resolution_digest"])
        self.assertEqual(resolution_of(self.jobs, JOB)["source"],
                         {"input_digest": INPUT, "policy_digest": POLICY})


class TheCommandRequestsTheOperation(unittest.TestCase):
    """The CLI verb, and what it is NOT allowed to carry.

    SCH-1a: "The CLI requests the operation and reports its result." So the
    assertions here are about delegation and about an ARGUMENT LIST: a verb
    that offered `--input-digest` or `--profile-digest` would be asking an
    operator to configure the pool from a Job, which is the operator-authored
    manifest this milestone exists to remove.
    """

    def argv(self, *extra):
        return ["--store", "/i/jobs", "--incarnation", "jobs-1",
                "--authority-uuid", "0" * 31 + "a", "create",
                "--instance", "/i", "--control", "/i/control",
                "--authority", "/i/authority", "--task", TASK,
                "--statement", STATEMENT, "--acceptance", CRITERION,
                "--work-scope", WORK_SCOPE[0], *extra]

    def taken(self, *extra):
        """The parsed operands, without running anything."""
        import io
        from unittest import mock

        from tools import job_manager

        seen = {}

        def record(taken, clock, stream):
            seen["taken"] = taken
            seen["request"] = job_manager._creation_request(taken)
            return 0

        with mock.patch.object(job_manager, "_create", record):
            job_manager.main(self.argv(*extra), stream=io.StringIO())
        return seen

    def test_the_verb_offers_no_operand_for_a_derived_fact(self):
        import io
        from unittest import mock

        from tools import job_manager

        for forbidden in ("--input-digest", "--policy-digest", "--profile",
                          "--profile-name", "--profile-digest", "--work-id",
                          "--document", "--manifest", "--packet"):
            with self.subTest(forbidden=forbidden):
                with mock.patch.object(job_manager, "_create",
                                       lambda *a, **k: 0):
                    with self.assertRaises(SystemExit):
                        job_manager.main(self.argv(forbidden, "x"),
                                         stream=io.StringIO())

    def test_the_operator_words_become_the_resolvers_own_request(self):
        seen = self.taken("--test-scope", TEST_SCOPE[0])
        self.assertEqual(seen["request"], {
            "schema": templates.REQUEST_SCHEMA,
            "task": {"task_id": TASK, "statement": STATEMENT},
            "source_selection": creation.INSTALLED_SOURCE,
            "scope": {"work": list(WORK_SCOPE), "tests": list(TEST_SCOPE)},
            "acceptance": [CRITERION]})

    def test_an_absent_override_is_absent_rather_than_empty(self):
        """WHICH IS WHAT KEEPS AN UNCONFIGURED JOB A `/1` DOCUMENT."""
        self.assertNotIn("overrides", self.taken()["request"])
        held = self.taken("--provider-turn-seconds", "5400")["request"]
        self.assertEqual(held["overrides"],
                         {"execution_limits": {"provider_turn_seconds":
                                               5400}})
        both = self.taken("--provider-turn-seconds", "5400",
                          "--verification-command-seconds", "1200")
        self.assertEqual(both["request"]["overrides"]["execution_limits"],
                         {"provider_turn_seconds": 5400,
                          "verification_command_seconds": 1200})

    def test_repeating_an_operand_accumulates_a_list(self):
        held = self.taken("--acceptance", "a second criterion",
                          "--work-scope", "v12/python/tools/job_manager.py",
                          "--test-scope", TEST_SCOPE[0])["request"]
        self.assertEqual(held["acceptance"],
                         [CRITERION, "a second criterion"])
        self.assertEqual(held["scope"]["work"],
                         [WORK_SCOPE[0], "v12/python/tools/job_manager.py"])

    def test_an_explicit_template_and_identities_travel(self):
        held = self.taken("--template", templates.IMPLEMENTATION_REVIEW,
                          "--job-id", "job-chosen",
                          "--submission-id", "sub-chosen")["request"]
        self.assertEqual(held["template"], templates.IMPLEMENTATION_REVIEW)
        self.assertEqual(held["task"]["job_id"], "job-chosen")
        self.assertEqual(held["task"]["submission_id"], "sub-chosen")

    def test_the_verb_delegates_every_decision_to_the_manager(self):
        """IT HOLDS NO RULE, asserted from the source.

        `_create` composes four ports, opens the control store read-only and
        calls one operation. A branch here deciding identity, uniqueness,
        servability or generation agreement would be the script-side precheck
        REC-7 forbids.
        """
        import ast
        import pathlib as _pathlib

        from tools import job_manager

        source = _pathlib.Path(job_manager.__file__).read_text(
            encoding="utf-8")
        node = next(one for one in ast.parse(source).body
                    if type(one) is ast.FunctionDef
                    and one.name == "_create")
        called = {piece.func.attr if type(piece.func) is ast.Attribute
                  else getattr(piece.func, "id", None)
                  for piece in ast.walk(node) if type(piece) is ast.Call}
        self.assertIn("create_template_job", called)
        self.assertIn("open_readonly", called,
                      "the control store is opened read-only")
        self.assertNotIn("submit", called)
        self.assertNotIn("resolve", called,
                         "the CLI does not resolve; the manager does")
        for piece in ast.walk(node):
            self.assertNotIsInstance(
                piece, ast.Try, "_create holds no exception policy")


if __name__ == "__main__":
    unittest.main()
