"""Two independent Jobs, overlapping, through the arrangement this gate proposes.

ASSESSMENT-249338.md G2: "use a single deterministic two-Job witness through
the selected composition with provider simulation at its normal boundary.
Require an observed interval in which A and B are both actively executing,
distinct runtime/workspace/attempt attribution, both frozen independently
attributed review results, and positive stop/cleanup. Inspect concrete
identities/timestamps or a controlled overlap barrier, never infer overlap from
two submits or test counts."

THE FIXTURE IS THE ACCEPTED ONE. `TwoBoundJobsTraverseServingAndCorrection` is
W130224's own two-Job fixture, independently accepted by
review-2026-09-11T00-52-04Z.md, with two real sources, two real Works, two
producers, two reviewers and real owner/content operations. These cases
SUBCLASS it and replace exactly one thing: the deployment document, which now
comes from `two_jobs.arrangement`. So what is measured is whether THIS
arrangement serves two Jobs, over machinery whose acceptance is not in question.

WHAT IS SIMULATED, at its normal boundary: the container. The turn is the
fixture's own deterministic worker turn, the same one every accepted v12
lifecycle case uses. No engine, image, network or credential is reached, and
`CONTINUITY-247941.md` says which accepted evidence covers the boundary this
does not.
"""
import ast
import copy
import io
import json
import os
import pathlib
import sys
import unittest
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
CHECKOUT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(HERE)))))
if HERE not in sys.path:                                     # pragma: no cover
    sys.path.insert(0, HERE)

# THE PINNED SNAPSHOT, for the subprocess checks that ask a command what
# operands it accepts. They must ask the selected product, not the checkout.
SNAPSHOT = "/home/sl/baton-runs/independent-review-247947/manager-source"

from tests.tools.test_stage_execution import (                # noqa: E402
    SECOND_WORK, TwoBoundJobsTraverseServingAndCorrection)

import two_jobs                                               # noqa: E402


class ArrangedCase(TwoBoundJobsTraverseServingAndCorrection):
    """The accepted fixture, serving THIS arrangement's document."""

    def jobs_from(self, given):
        """The two Jobs' own facts, READ OUT OF the document being composed.

        Derived rather than typed, and derived from THIS document rather than
        from the fixture's raw two-Job helper: the traversal overrides Job B's
        base and source, and a recomposition that ignored those overrides
        would compose a Job whose line cannot materialize -- which is exactly
        what the first version did, and Git said so ("not our ref").
        """
        workers = {one["worker_id"]: one for one in given["workers"]}
        held = []
        for binding in given["job_bindings"]:
            producer = workers[binding["source_worker_id"]]
            reviewer = self.reviewer_for(binding, workers)
            held.append({
                "job_id": binding["job_id"],
                "work_id": binding["job_work_id"],
                "producer_worker_id": producer["worker_id"],
                "reviewer_worker_id": reviewer["worker_id"],
                "producer_participant": producer["deployment"]["participant"],
                "reviewer_participant": reviewer["deployment"]["participant"],
                "nominated_source": producer["deployment"]["nominated_source"],
                "declared_base": binding["line_declared_base"],
                "task_document": producer["deployment"]["task_document"],
                "canonical_target_id": binding["canonical_target_id"]})
        return held

    def jobs(self):
        return self.jobs_from(self.two_jobs())

    def reviewer_for(self, binding, workers):
        """The review worker bound to this Job's Work.

        `worker_of` in the product answers by ROLE, and with two reviewers
        that is whichever the document lists last -- the same trap the
        accepted fixture's own docstring names. This selects by the Work the
        worker is bound to, which is the fact that actually decides it.
        """
        held = [one for one in workers.values() if one["role"] == "review"
                and self.bound_work(one) == binding["review_work_id"]]
        self.assertEqual(len(held), 1,
                         f"{binding['job_id']} has {len(held)} review workers "
                         f"bound to {binding['review_work_id']}")
        return held[0]

    def bound_work(self, worker):
        """The Work a configured worker's own input manifest names.

        `bound_worker` in the accepted fixture moves the manifest and the task
        document together, and `single_worker._held` cross-checks them -- so
        the manifest's `work_ref` is the fact that says which Job a worker was
        configured for, rather than anything in the worker's name.
        """
        manifest = worker["deployment"].get("input_manifest") or {}
        return (manifest.get("work_ref") or {}).get("work_id")

    def composed_document(self, **members):
        """The inherited document, RECOMPOSED by `two_jobs.arrangement`.

        Everything this gate does not choose -- stores, profiles, policy,
        receipts, the worker documents themselves -- stays exactly what the
        accepted fixture supplies. What `arrangement` decides is the POOL and
        the BINDINGS, which is the whole of what this gate proposes.
        """
        given = super().composed_document(**members)
        if "job_bindings" not in given:
            return given                      # the one-Job admission fixture
        workers = {one["worker_id"]: one for one in given["workers"]}
        jobs = self.jobs_from(given)
        mine = {one[name] for one in jobs
                for name in ("producer_worker_id", "reviewer_worker_id")}
        extra = [one for one in given["workers"] if one["worker_id"] not in mine]
        self.arranged_extra = [one["role"] for one in extra]
        self.arranged_served = two_jobs.arrangement(
            instance=given, jobs=jobs, extra_workers=extra,
            worker_of=lambda role, *, worker_id, participant, job:
                workers[worker_id])
        return two_jobs.arrangement(
            instance=given, jobs=jobs, extra_workers=extra,
            worker_of=lambda role, *, worker_id, participant, job:
                workers[worker_id])


    def both_jobs(self):
        """The accepted submission, WITHOUT either Job's integration stage.

        Review 2026-09-23T17:12:02Z R3: the witness inherited a submission
        carrying an integration stage for both Jobs while the packet said this
        arrangement submits none. A limit the documents assert and the
        submission contradicts is not a limit, so this drops those two stages
        and changes nothing else about the accepted shape.
        """
        held = super().both_jobs()
        for one in held["jobs"]:
            one["stages"] = [stage for stage in one["stages"]
                             if stage["kind"] != "integration"]
        return held


class TheArrangementIsTheSupportedCompositionResolved(ArrangedCase):
    """G1: one manager, one pool, four workers, two bindings."""

    def arranged_document(self):
        """The `/2` document this arrangement composes.

        `composed_document()` with no members is the ONE-Job document -- the
        fixture only reaches the two-Job one through its own `two_jobs()`
        helper, which is what `serving_two` passes. Asking for it directly is
        how these cases look at the same document the traversal serves.
        """
        return self.composed_document(**self.two_jobs())

    def test_the_document_the_product_validator_accepts(self):
        given = self.arranged_document()
        from tools import stage_execution
        self.assertEqual(given["schema"],
                         stage_execution.MULTI_CONFIG_SCHEMA)
        self.assertEqual(len(given["job_bindings"]), 2)
        two_jobs.held(given)

    def test_each_binding_names_its_own_producer_and_one_work(self):
        [first, second] = self.arranged_document()["job_bindings"]
        self.assertEqual(first["source_worker_id"], "implementation-worker")
        self.assertEqual(second["source_worker_id"], "implementation-worker-b")
        for one in (first, second):
            with self.subTest(job=one["job_id"]):
                self.assertEqual(one["job_work_id"], one["review_work_id"])
        self.assertNotEqual(first["job_work_id"], second["job_work_id"])

    def test_the_per_job_facts_are_the_bindings_and_not_the_instance(self):
        """Where each Job's Work, base and target actually come from.

        A `/2` document still carries the instance-level `job_work_id`,
        `line_declared_base` and `canonical_target_id` -- `_MEMBERS` requires
        them and `held_configuration` refuses a document without them. What
        makes this arrangement two Jobs is that each BINDING carries its own,
        and Job B's differ from the instance's in the two ways that matter.
        """
        given = self.arranged_document()
        [first, second] = given["job_bindings"]
        self.assertEqual(first["job_work_id"], given["job_work_id"])
        self.assertNotEqual(second["job_work_id"], given["job_work_id"])
        self.assertNotEqual(second["line_declared_base"],
                            first["line_declared_base"])

    def test_the_document_declines_the_correction_round(self):
        """The boundary is composed, not asserted in prose.

        The first version claimed `correction_policy: "decline"` in the packet
        while composing a document that carried no such member -- which means
        `open`, today's behaviour. The claim was prose; this is the act.
        """
        from tools import stage_execution
        given = self.arranged_document()
        self.assertEqual(given["correction_policy"],
                         stage_execution.DECLINE_CORRECTION)
        two_jobs.held(given)

    def test_the_submission_carries_no_integration_stage(self):
        for one in self.both_jobs()["jobs"]:
            with self.subTest(job=one["job_id"]):
                self.assertEqual([stage["kind"] for stage in one["stages"]],
                                 ["implementation", "review"])

    def test_the_pool_this_gate_composes_is_four_stage_workers(self):
        """Two producers and two reviewers, and no third lane of its own.

        The fixture's document also configures an INTEGRATOR, which this
        arrangement carries through rather than deleting from somebody else's
        deployment. What keeps this gate's no-integration limit is the
        submission: no integration stage is submitted, so no integration
        capacity is ever allocated.
        """
        given = self.arranged_document()
        composed = two_jobs.workers(
            self.jobs(),
            worker_of=lambda role, *, worker_id, participant, job:
                {"worker_id": worker_id, "role": role})
        self.assertEqual(sorted(one["role"] for one in composed),
                         ["implementation", "implementation",
                          "review", "review"])
        self.assertEqual(sorted(two_jobs.LANES),
                         ["implementation", "review"])
        self.assertEqual(sorted(self.arranged_extra), ["integration"])
        self.assertEqual(len(given["workers"]), len(composed) + 1)


class TwoJobsThatAreSecretlyOneAreRefused(ArrangedCase):
    """Isolation is checked before composition, not asserted afterwards."""

    def arranged(self, **overrides):
        jobs = self.jobs()
        jobs[1].update(overrides)
        given = self.two_jobs()
        workers = {one["worker_id"]: one for one in given["workers"]}
        return two_jobs.arrangement(
            instance=given, jobs=jobs,
            worker_of=lambda role, *, worker_id, participant, job:
                workers[worker_id])

    def refusal(self, **overrides):
        with self.assertRaises(two_jobs.ArrangementRefusal) as caught:
            self.arranged(**overrides)
        return str(caught.exception)

    def test_one_task_for_both_jobs(self):
        """Two Jobs given one task document are one Job submitted twice."""
        self.assertIn("task_document",
                      self.refusal(task_document=self.jobs()[0]
                                   ["task_document"]))

    def test_one_work_for_both_jobs(self):
        """One Work is one line: their stages could not even be told apart."""
        self.assertIn("work_id",
                      self.refusal(work_id=self.jobs()[0]["work_id"]))

    def test_one_source_for_both_jobs_is_NOT_refused(self):
        """Two lines of one target at one base is the supported shape.

        The first version of this arrangement refused a shared source and a
        shared base, and the accepted two-Job traversal -- which is exactly
        that shape, because an Authority holds one canonical revision -- could
        not compose. Refusing the supported arrangement is not a stricter
        rule, it is a wrong one.
        """
        jobs = self.jobs()
        shared = self.arranged(nominated_source=jobs[0]["nominated_source"],
                               declared_base=jobs[0]["declared_base"])
        self.assertEqual(len(shared["job_bindings"]), 2)

    def test_one_reviewer_for_both_jobs(self):
        """Not refused by the product -- refused by THIS gate's limit.

        A reviewer serving both Jobs would compose and serve; it is this
        arrangement that will not propose a single identity seeing both
        subjects. It is the disjointness rule that catches this one, and the
        four-identity rule that catches a reviewer who is somebody's producer.
        """
        self.assertIn("reviewer_participant",
                      self.refusal(reviewer_participant=self.jobs()[0]
                                   ["reviewer_participant"]))

    def test_a_producer_reviewing_its_own_job(self):
        self.assertIn("independent identities",
                      self.refusal(
                          reviewer_participant=self.jobs()[1]
                          ["producer_participant"]))

    def test_a_third_job_is_a_different_selection(self):
        given = self.two_jobs()
        jobs = self.jobs()
        with self.assertRaises(two_jobs.ArrangementRefusal) as caught:
            two_jobs.arrangement(
                instance=given, jobs=jobs + [dict(jobs[0])],
                worker_of=lambda role, *, worker_id, participant, job: {})
        self.assertIn("exactly 2 Jobs", str(caught.exception))


class BothJobsAreActivelyExecutingAtOneObservedInstant(ArrangedCase):
    """G2's first requirement, and the reason this Work exists.

    THE OVERLAP IS OBSERVED, NOT INFERRED. The assertion is made at ONE
    instant, on the deployment's own projected status, with each Job's
    implementation stage `waiting` on its OWN allocated producer -- which is
    the state a stage is in while its runtime is executing. Two submissions,
    two completions, or a passing count would prove nothing about whether
    either Job was ever queued behind the other's capacity.
    """

    def test_the_document_that_actually_served_is_this_arrangements(self):
        """Otherwise these four cases would be re-running W130224's evidence.

        The fixture's own pool lists the integrator THIRD; this arrangement
        composes the four stage workers first and carries other roles after
        them. The order the served document actually had is the cheapest fact
        that tells the two apart.
        """
        self.coding()
        self.assertEqual([one["role"] for one in
                          self.arranged_served["workers"]],
                         ["implementation", "review", "implementation",
                          "review", "integration"])

    def test_both_implementations_are_waiting_at_the_same_instant(self):
        held = self.coding()
        first = self.states_for(held.job, held.composed, "job-a")
        second = self.states_for(held.job, held.composed, "job-b")
        self.assertEqual(first["implementation"], "waiting")
        self.assertEqual(second["implementation"], "waiting")

    def test_each_runs_on_its_own_allocated_producer(self):
        held = self.coding()
        self.assertEqual(self.allocated(held.job, "job-a/implementation"),
                         "implementation-worker")
        self.assertEqual(self.allocated(held.job, "job-b/implementation"),
                         "implementation-worker-b")
        self.assertNotEqual(held.first, held.second)

    def test_each_writes_its_own_line_from_its_own_source(self):
        held = self.coding()
        first = self.line_of(held.composed, "job-a")
        second = self.line_of(held.composed, "job-b")
        self.assertNotEqual(first["line_id"], second["line_id"])
        self.assertEqual(first["work_id"], self.work)
        self.assertEqual(second["work_id"], SECOND_WORK)

    def test_each_attempt_mounts_its_own_workspace(self):
        held = self.coding()
        self.assertNotEqual(self.mounted_at(held.composed, held.first),
                            self.mounted_at(held.composed, held.second))


class EachJobCollectsItsOwnAttributedVerdict(ArrangedCase):
    """G2's second and third requirements: attribution, and two verdicts."""

    def reviewed(self):
        held = self.coding()
        self.produced(held, "job-a", held.first, "print('a')\n")
        self.produced(held, "job-b", held.second, "print('b')\n",
                      edits={"feature_check.py": "print('b')\n"})
        return held

    def test_BOTH_jobs_reach_their_own_reviewers(self):
        """Two verdicts, not one -- R3: "only B review waiting, no pair"."""
        held = self.reviewed()
        for job_id, worker in (("job-a", "review-worker"),
                               ("job-b", "review-worker-b")):
            with self.subTest(job=job_id):
                self.drive_job(held.job, held.composed, job_id, "review",
                               "waiting")
                self.assertIsNotNone(
                    self.one_attempt_of(held.composed, worker))
        first = self.one_attempt_of(held.composed, "review-worker")
        second = self.one_attempt_of(held.composed, "review-worker-b")
        self.assertNotEqual(first, second)

    def test_the_second_job_reaches_its_own_reviewer(self):
        """Its own, not the first Job's -- which is what a shared pool could
        get wrong without anyone noticing until two subjects were judged by
        one identity."""
        held = self.reviewed()
        self.drive_job(held.job, held.composed, "job-b", "review", "waiting")
        attempt = self.one_attempt_of(held.composed, "review-worker-b")
        self.assertIsNotNone(attempt)
        self.assertNotEqual(
            attempt, self.attempts_of(held.composed, "review-worker"))


class TheSHIPPEDTemplateComposesThroughTheACTUALCLI(ArrangedCase):
    """The roundtrip review 2026-09-23T17:17:50Z asked for, end to end.

    THE SHIPPED FILE, not a synthetic one. `SELECTIONS-247941.json` is read as
    it ships, every `<OWNER: ...>` is resolved with a DISPOSABLE value taken
    from the accepted fixture, and `two_jobs.py` runs as a subprocess exactly
    as ADOPTION-247941.md step 3 prints it. Then the two documents it wrote go
    to the product's own readers.

    W239533 learned this at an owner's expense: every case in that suite wrote
    its own selections, so a template defect reached a live operator. A
    composer is only as good as the document an operator actually holds.
    """

    SHIPPED = os.path.join(HERE, "SELECTIONS-247941.json")

    def packet_root(self):
        held = os.path.join(self.root, "packet")
        os.makedirs(held, exist_ok=True)
        return held

    def resolved(self):
        """The shipped template with disposable operands, and nothing else."""
        import copy
        with open(self.SHIPPED, encoding="utf-8") as handle:
            document = json.load(handle)
        given = document["arrangement"]
        inherited = self.two_jobs()
        workers = {one["worker_id"]: one for one in inherited["workers"]}
        producer = workers["implementation-worker"]["deployment"]
        reviewer = workers["review-worker"]["deployment"]
        instance = given["instance"]
        shape = self.composed_document()
        instance.update({
            "run_root": os.path.join(self.packet_root(), "declared"),
            "authority_store": producer["authority_store"],
            "authority_uuid": producer["authority_uuid"],
            "job_store": os.path.join(self.packet_root(), "jobs.sqlite3"),
            "integration_store": self.integration_store,
            "state_root": self.state_root,
            "workspace_storage": producer["workspace_storage"],
            "launch_home": producer["launch_home"],
            "credential_home": producer["credential_home"],
            "credential_sources": producer["credential_sources"],
            "credential_slots": producer["credential_slots"],
            "credential_profile": producer["credential_profile"],
            "provider_network": producer["network"],
            "retention_policy_digest": producer["retention_policy_digest"],
            "retention_disposition": producer["retention_disposition"],
            "policy_digest": producer["policy_digest"],
            "adapter_name": producer["adapter_name"],
            "adapter_digest": producer["adapter_digest"],
            "engine": producer["engine"],
            "image_digest": producer["image_digest"],
            "workspace_group": producer["workspace_group"],
            "workspace_capacity": producer["workspace_capacity"],
            "launch_contract": producer["launch_contract"],
            "review_route": producer["review_route"],
            "reviewed_route": reviewer["review_route"],
            "checkpoint_profile": shape["checkpoint_profile"],
            "policy_generation": self.fixture_policy,
            "integration_profile": copy.deepcopy(shape["integration_profile"]),
            "receipt_participants": copy.deepcopy(
                shape["receipt_participants"]),
            "job_work_id": self.work, "review_work_id": self.work,
            "line_declared_base": self.base,
            "canonical_target_id": inherited["job_bindings"][0][
                "canonical_target_id"],
            "submission_id": "two-job-packet",
        })
        for one, binding in zip(given["jobs"], inherited["job_bindings"]):
            source = workers[binding["source_worker_id"]]["deployment"]
            judge = self.reviewer_for(binding, workers)
            held = judge["deployment"]
            one.update({
                "job_id": binding["job_id"],
                "work_id": binding["job_work_id"],
                "producer_worker_id": binding["source_worker_id"],
                "reviewer_worker_id": judge["worker_id"],
                "producer_participant": source["participant"],
                "reviewer_participant": held["participant"],
                "implementation_principal": source["principal"],
                "review_principal": held["principal"],
                "nominated_source": source["nominated_source"],
                "declared_base": binding["line_declared_base"],
                "task_document": source["task_document"],
                "canonical_target_id": binding["canonical_target_id"],
                "input_digest": source["input_manifest"]["manifest_digest"],
                "test_scope": ["v12/python/tests/job_manager"],
                "profile_name": source["profile_name"],
                "profile_digest": source["profile_digest"],
                "review_profile_name": held["profile_name"],
                "review_profile_digest": held["profile_digest"],
                "implementation_input_manifest": source["input_manifest"],
                "review_input_manifest": held["input_manifest"],
            })
        place = os.path.join(self.packet_root(), "resolved-selections.json")
        with open(place, "w", encoding="utf-8") as handle:
            json.dump(document, handle, indent=2, sort_keys=True)
        return place, document

    def bound_environment(self):
        """The import path ADOPTION-247941.md step 3 prints, exactly.

        THE PINNED SOURCE ALONE, not the checkout. Review
        2026-09-23T17:25:40Z: the subprocess imported the checkout while the
        pin helper checked the snapshot, so a passing pin check said nothing
        about the bytes that actually composed. `two_jobs.imported_from` now
        refuses that, and this is the environment that satisfies it.
        """
        import verify_247941
        return dict(os.environ, PYTHONDONTWRITEBYTECODE="1",
                    PYTHONPATH=os.pathsep.join(
                        [str(verify_247941.SNAPSHOT), HERE]))

    def composing(self, selections, into):
        import subprocess
        return subprocess.run(
            [sys.executable, "-B", os.path.join(HERE, "two_jobs.py"),
             "--selections", selections, "--into", into],
            capture_output=True, text=True, timeout=300, cwd=os.sep,
            env=self.bound_environment())

    def composed_packet(self):
        place, _ = self.resolved()
        into = os.path.join(self.packet_root(), "run")
        return self.composing(place, into), into

    def test_the_shipped_template_still_asks_every_operand_by_name(self):
        """Otherwise this class would resolve fields nobody ships."""
        with open(self.SHIPPED, encoding="utf-8") as handle:
            given = json.load(handle)["arrangement"]
        for name in two_jobs.INSTANCE_OPERANDS:
            with self.subTest(operand=name):
                self.assertIn(name, given["instance"])
        for index, one in enumerate(given["jobs"]):
            for name in two_jobs.JOB_OPERANDS:
                with self.subTest(job=index, operand=name):
                    self.assertIn(name, one)

    def test_the_documented_command_writes_both_documents(self):
        answer, into = self.composed_packet()
        self.assertEqual(answer.returncode, 0,
                         f"stdout={answer.stdout}\nstderr={answer.stderr}")
        printed = json.loads(answer.stdout)
        # AND THE COMPOSITION CHECKED THE PINS FIRST, which is what binds the
        # packet's step 1 to its step 3 rather than trusting an operator to
        # have run both.
        self.assertTrue(printed.pop("_pins_agree"))
        self.assertEqual(sorted(printed),
                         ["deployment.json", "submission.json"])
        for name in printed:
            with self.subTest(document=name):
                self.assertTrue(os.path.exists(os.path.join(into, name)))

    def test_the_written_deployment_is_the_one_the_product_accepts(self):
        answer, into = self.composed_packet()
        self.assertEqual(answer.returncode, 0, answer.stderr)
        with open(os.path.join(into, "deployment.json"),
                  encoding="utf-8") as handle:
            deployment = json.load(handle)
        from tools import stage_execution
        self.assertEqual(deployment["schema"],
                         stage_execution.MULTI_CONFIG_SCHEMA)
        self.assertEqual(deployment["correction_policy"],
                         stage_execution.DECLINE_CORRECTION)
        self.assertEqual(len(deployment["workers"]), 4)
        stage_execution.held_configuration(deployment, checkout=self.checkout)

    def test_the_written_submission_is_one_the_public_reader_accepts(self):
        """R1's second half: the reader refused it for two missing members."""
        from baton_v12.job_manager import submit
        answer, into = self.composed_packet()
        self.assertEqual(answer.returncode, 0, answer.stderr)
        with open(os.path.join(into, "submission.json"),
                  encoding="utf-8") as handle:
            document = json.load(handle)
        job, _control = self.stores("packet-submission")
        submit(job, document)
        for one in document["jobs"]:
            with self.subTest(job=one["job_id"]):
                self.assertEqual([stage["kind"] for stage in one["stages"]],
                                 ["implementation", "review"])
                self.assertIn("test_scope", one)
                self.assertIn("terminal_policy", one)

    def test_a_composition_bound_to_the_CHECKOUT_is_refused(self):
        """The pin check and the composition must be about the same bytes."""
        place, _ = self.resolved()
        into = os.path.join(self.packet_root(), "unbound")
        import subprocess
        answer = subprocess.run(
            [sys.executable, "-B", os.path.join(HERE, "two_jobs.py"),
             "--selections", place, "--into", into],
            capture_output=True, text=True, timeout=300, cwd=os.sep,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1",
                     PYTHONPATH=os.pathsep.join(
                         [os.path.join(CHECKOUT, "v12/python/src"),
                          os.path.join(CHECKOUT, "v12/python"), HERE])))
        self.assertNotEqual(answer.returncode, 0)
        self.assertIn("bound to the pinned manager source",
                      answer.stderr + answer.stdout)
        self.assertFalse(os.path.exists(into))

    def test_an_invalid_terminal_policy_is_refused_at_composition(self):
        """Not at submission, where an operator would meet it instead."""
        place, document = self.resolved()
        for one in document["arrangement"]["jobs"]:
            one["terminal_policy"] = "carry-on-regardless"
        with open(place, "w", encoding="utf-8") as handle:
            json.dump(document, handle, indent=2, sort_keys=True)
        into = os.path.join(self.packet_root(), "invalid-policy")
        answer = self.composing(place, into)
        self.assertNotEqual(answer.returncode, 0)
        self.assertIn("public reader refuses", answer.stderr + answer.stdout)
        self.assertFalse(os.path.exists(into))

    def test_MAIN_refuses_BEFORE_it_can_owe_an_outcome(self):
        """The entrypoint, invoked -- not described. AND IT PUBLISHES NOTHING.

        Review 2026-09-23T19:22:24Z: "Main composition/submission failures
        still precede supervise and have no outcome path; either implement the
        existing requested failure guarantee or precisely distinguish
        pre-execution refusal in the operator contract, without claiming every
        path publishes." This case is that distinction, and its old name --
        `..._publishes_an_outcome` -- claimed the opposite of what it asserts.

        THE LINE IS WHERE `supervise` IS ENTERED. Before it, nothing has been
        admitted, no runtime exists and there is no account to render; the
        command refuses and writes no outcome. After it, every path publishes.
        A packet that promised an outcome for a refusal would be promising a
        document about a run that never began.

        Review 2026-09-23T17:56:23Z: `main` omitted the REQUIRED `clock` at
        both openers, so the one command this packet tells an operator to type
        could not open a store at all. Nothing short of calling it catches
        that, so this calls it.

        The documents are the ones the composer wrote for this fixture, the
        stores are fresh paths under the disposable root, and the bounds are
        small because the arithmetic is proved separately on a controlled
        clock.
        """
        import two_job_supervisor
        from baton_v12.contracts import ContractRefusal
        answer, into = self.composed_packet()
        self.assertEqual(answer.returncode, 0, answer.stderr)
        outcome = os.path.join(into, "outcome.json")
        argv = ["--deployment", os.path.join(into, "deployment.json"),
                "--submission", os.path.join(into, "submission.json"),
                "--job-store", os.path.join(into, "jobs.sqlite3"),
                "--control-store", os.path.join(into, "control.sqlite3"),
                "--incarnation", "two-job-entrypoint",
                "--outcome", outcome,
                "--total-seconds", "12", "--cleanup-seconds", "4"]
        # WHAT THIS PROVES, AND WHAT IT DOES NOT. `main` opens both stores and
        # reaches the real composition; the PRODUCTION credential provider
        # then refuses, because this fixture's deployment carries
        # `credential_sources: null` and the production path requires an
        # absolute private registry. That refusal is the product working.
        #
        # What it catches is the defect review 2026-09-23T17:56:23Z found: the
        # openers require a `clock` and `main` passed none, so it could not
        # open a store at all. A `TypeError` here would be that defect again.
        with self.assertRaises(ContractRefusal) as caught:
            two_job_supervisor.main(argv)
        self.assertIn("credential_sources", str(caught.exception))
        # AND BOTH STORES EXIST, which is what "it opened them" means.
        for name in ("jobs.sqlite3", "control.sqlite3"):
            with self.subTest(store=name):
                self.assertTrue(os.path.exists(os.path.join(into, name)))
        # AND NO OUTCOME WAS WRITTEN, which is the contract this case now
        # states: the refusal precedes `supervise`, so there is nothing for an
        # outcome to account for.
        self.assertFalse(os.path.exists(outcome))

    def entrypoint(self, **members):
        """`main`'s operands over the composer's own documents."""
        answer, into = self.composed_packet()
        self.assertEqual(answer.returncode, 0, answer.stderr)
        outcome = os.path.join(into, "outcome.json")
        argv = ["--deployment", os.path.join(into, "deployment.json"),
                "--submission", os.path.join(into, "submission.json"),
                "--job-store", os.path.join(into, "jobs.sqlite3"),
                "--control-store", os.path.join(into, "control.sqlite3"),
                "--incarnation", members.get("incarnation", "two-job-main"),
                "--outcome", outcome,
                "--total-seconds", str(members.get("total", 600)),
                "--cleanup-seconds", str(members.get("cleanup", 60))]
        return argv, outcome, into

    def disposable(self, into):
        """The provider, engine and turn a deterministic witness supplies.

        All three stand exactly where production's would: the registry the
        real provider refuses to do without, the engine that would start a
        container, and the turn the container would run. None of them is a
        loosening of `main` -- they are operands it takes and an operator
        never passes.
        """
        # THE MULTI-RUNTIME ENGINE, not the single-runtime fake. Review
        # 2026-09-23T18:56:28Z: `test_single_worker.Engine` answers
        # `runtime-single-1` for EVERY run and overwrites its one labels and
        # mounts record, so two concurrent launches through one instance
        # collide and one delivery goes missing. The accepted two-Job fixture
        # has an engine that models SEVERAL live containers, and this uses
        # THAT -- the runtime identity is not weakened anywhere.
        return {"credential_provider": lambda provider, reference: self.secret,
                "engine_run": self.quiescing(),
                "checkout": self.checkout}

    def test_MAIN_runs_the_whole_command_and_publishes_its_outcome(self):
        """The COMMAND, end to end -- and NOT yet a success through it.

        Review 2026-09-23T18:26:13Z: the supervisor success called
        `serving_two`/`submit`/`supervise` directly, so it proved the run and
        not the command. This drives the command: it opens both stores,
        composes with a disposable provider and engine, submits, serves
        bounded, stops and publishes.

        THIS ONE IS THE NEGATIVE, and it is deliberately still here now that
        the success is asserted beside it: a callback that answers nothing
        leaves both implementations unfinished, so the run collects no verdict
        and reports `held`. Success has to be what the run PRODUCED, and the
        way to show that is a run that produced nothing and says so.
        """
        import two_job_supervisor
        # SMALL BOUNDS, because `main` serves on the REAL wall clock -- there
        # is no injected monotonic through the documented entry point, and
        # there should not be. The 600/60 arithmetic is proved separately on a
        # controlled clock; this proves the COMMAND.
        argv, outcome, into = self.entrypoint(total=12, cleanup=4)
        held = {}

        def turns(gate, context):
            held.setdefault("gate", gate)

        status = two_job_supervisor.main(argv, turns=turns,
                                         **self.disposable(into))
        with open(outcome, encoding="utf-8") as handle:
            published = json.load(handle)
        self.assertEqual(published["schema"], "baton.v12.two-job-outcome/1")
        self.assertEqual(published["job_ids"], ["job-a", "job-b"])
        # HELD, NOT "either" -- a run whose workers never answered has not
        # done its work, and accepting `0` here would accept the defect the
        # shadowed callback produced.
        self.assertEqual(status, 1)
        self.assertEqual(published["state"], "held")
        self.assertEqual(published["verdicts"], {})
        self.assertTrue(any("no attributed verdict" in one
                            for one in published["held_because"]),
                        published["held_because"])
        self.assertTrue(held.get("gate"), "the turn was never invoked")

    def commanded(self, *, total=600, cleanup=60, wrap=None):
        """One whole run of the DOCUMENTED command, and what it read.

        THE CLOCK IS CONTROLLED. `main` serves on the real wall clock by
        default, and it should; a witness that had to wait out 540 real
        seconds would be a witness nobody runs. The monotonic seam steps five
        seconds a tick, so the serving bound is reached after a fixed number
        of ticks and this case is deterministic.

        THE STATUS READ IS TAKEN FROM INSIDE THE TURN, where `operations` is
        open. `projection.status` asks the composition whether the canonical
        store was read at all -- that is what its `canonical` member reports
        -- so a read taken after the command returns has nothing to ask and
        raises. Every earlier receipt printed that AttributeError instead of
        stage states.
        """
        import two_job_supervisor
        from baton_v12.job_manager.projection import status as projected
        from tests.job_manager import fixtures
        argv, outcome, into = self.entrypoint(total=total, cleanup=cleanup)
        inner = self.answering()
        captured = []

        def turns(gate, context):
            if wrap is not None:
                wrap(gate, context)
            inner(gate, context)
            captured.append({
                "canonical": projected(context["job"], context["operations"],
                                       observed_at=fixtures.NOW)["canonical"],
                "jobs": {one["job_id"]: {two["kind"]: two["state"]
                                         for two in one["stages"]}
                         for one in projected(
                             context["job"], context["operations"],
                             observed_at=fixtures.NOW)["jobs"]}})

        moments = iter(range(0, 10_000, 5))
        status = two_job_supervisor.main(
            argv, turns=turns, monotonic=lambda: float(next(moments)),
            sleep=lambda _seconds: None, **self.disposable(into))
        with open(outcome, encoding="utf-8") as handle:
            return status, json.load(handle), captured, into

    def test_the_DOCUMENTED_COMMAND_reaches_four_attempts_and_two_verdicts(
            self):
        """R4's success through the COMMAND, not through `supervise`.

        The command opens both stores, composes the deployment `two_jobs.py`
        wrote, submits, serves bounded, stops, cleans up and publishes. What
        this asserts is what it PRODUCED: four admissions, two verdicts each
        derived from its own frozen result, and no runtime left without a
        positive cleanup.

        This was observed once and not asserted, and then not reproduced --
        because `answering` had been shadowed by a second definition that
        never set the composed handle, so every turn raised and no
        implementation completed. An observation nothing asserts is how that
        survived.
        """
        status, published, captured, into = self.commanded()
        del into
        self.assertEqual(published["schema"], "baton.v12.two-job-outcome/1")
        self.assertEqual(published["job_ids"], ["job-a", "job-b"])
        self.assertEqual(published["admissions"],
                         {"implementation": 2, "review": 2})
        self.assertEqual(sorted(published["verdicts"]), ["job-a", "job-b"])
        for job_id, verdict in sorted(published["verdicts"].items()):
            with self.subTest(job=job_id):
                self.assertEqual(verdict["verdict"], "accepted")
        self.assertEqual(published["outstanding_cleanup"], [])
        self.assertEqual(published["uncertainty"], [])
        self.assertEqual(published["gate_refusals"], [])
        self.assertEqual(published["state"], "settled",
                         published["held_because"])
        self.assertEqual(published["held_because"], [])
        self.assertEqual(published["stopped"], "serving-bound-exceeded")
        # AND THE COMMAND'S OWN EXIT STATUS SAYS SO. An operator reads that
        # before reading any document.
        self.assertEqual(status, 0)
        self.assertTrue(captured, "no tick took a status read")

    def test_the_COMMAND_reports_a_SUPPORTED_status_with_a_live_composition(
            self):
        """The read an operator takes while the run is up.

        ADOPTION-247941.md step 7 tells an operator to ask what is running.
        Every diagnostic receipt before this one answered that question with
        `AttributeError: 'NoneType' object has no attribute 'canonical'`,
        because it asked after the command had closed the composition. This
        asks during, which is the supported way, and asserts both ends of the
        run: every stage offered before any turn answered, and every stage
        completed by the last tick.
        """
        _status, published, captured, _into = self.commanded()
        self.assertEqual(published["state"], "settled",
                         published["held_because"])
        for one in (captured[0], captured[-1]):
            with self.subTest(read=captured.index(one)):
                # THE CANONICAL STORE WAS READ, which is the difference
                # between "nothing is running" and "nobody looked".
                self.assertIs(one["canonical"], True)
                self.assertEqual(sorted(one["jobs"]), ["job-a", "job-b"])
                for job_id, stages in sorted(one["jobs"].items()):
                    self.assertEqual(sorted(stages),
                                     ["implementation", "review"], job_id)
        self.assertEqual(
            {job_id: stages["implementation"]
             for job_id, stages in captured[0]["jobs"].items()},
            {"job-a": "offered", "job-b": "offered"})
        self.assertEqual(
            captured[-1]["jobs"],
            {"job-a": {"implementation": "completed", "review": "completed"},
             "job-b": {"implementation": "completed", "review": "completed"}})

    def test_the_COMMAND_records_the_REAL_assignment_generations(self):
        """The ASSIGNMENT axis, through the command, from the store it wrote.

        `allocation.generation` is the POOL generation, and the two axes
        sharing the value 1 is the easiest false pass available here -- which
        is why this reads `attempts.assignment_of` back out of the control
        store the command left behind and compares it to what the run
        published, attempt by attempt.
        """
        from baton_v12.worker_manager import ControlStore
        from baton_v12.worker_manager import attempts as attempt_rows
        _status, published, _captured, into = self.commanded()
        self.assertEqual(published["state"], "settled",
                         published["held_because"])
        self.assertEqual(len(published["admitted_attempts"]), 4)
        control = ControlStore.open_readonly(
            os.path.join(into, "control.sqlite3"),
            incarnation="assignment-readback",
            clock=lambda: "1970-01-01T00:00:00.000Z")
        try:
            for attempt_id in published["admitted_attempts"]:
                with self.subTest(attempt=attempt_id):
                    recorded = published["generations"].get(attempt_id)
                    self.assertIsNotNone(recorded)
                    self.assertEqual(
                        attempt_rows.assignment_of(
                            control, attempt_id)["generation"], recorded)
        finally:
            control.close()

    def test_the_pool_and_assignment_axes_ACTUALLY_DIFFER_here(self):
        """The difference the reviewer asked for twice, already here.

        `scheduler.reserve` stamps each allocation with the CURRENT POOL
        generation; `attempts.assignment_of` reads the generation the
        Authority activated for that assignment. Review 2026-09-23T19:22:24Z
        asked twice for a case that forces or asserts a DIFFERENCE between
        them, and I had twice answered with a reader-agreement check.

        I came here to LABEL the distinction unproved and the run refused the
        label: the two axes already differ in this witness. The pool activates
        once and every allocation carries generation 1, while the review
        attempts activate a SECOND assignment generation on their own
        attempts. So a supervisor reading `allocation.generation` publishes 1
        where the assignment is 2 -- and `review_for_attempt` fences an
        attachment to the ACTIVATED generation, which is why reading the wrong
        axis is a verdict read that refuses rather than a cosmetic difference.

        The name says what it asserts. How it was found is in PROGRESS: the
        check I wrote to record a limitation is the one that disproved it.
        """
        from baton_v12.job_manager import JobStore, scheduler
        from baton_v12.worker_manager import ControlStore
        from baton_v12.worker_manager import attempts as attempt_rows
        _status, published, _captured, into = self.commanded()
        self.assertEqual(published["state"], "settled",
                         published["held_because"])
        jobs = JobStore.open_readonly(
            os.path.join(into, "jobs.sqlite3"),
            authority_uuid=self.config["authority_uuid"],
            incarnation="axis-readback",
            clock=lambda: "1970-01-01T00:00:00.000Z")
        control = ControlStore.open_readonly(
            os.path.join(into, "control.sqlite3"),
            incarnation="axis-readback",
            clock=lambda: "1970-01-01T00:00:00.000Z")
        try:
            pool = scheduler.active_generation(jobs)["generation"]
            assignments = {
                one: attempt_rows.assignment_of(control, one)["generation"]
                for one in published["admitted_attempts"]}
            allocations = {one["generation"]
                           for one in scheduler.allocation_rows(jobs)}
        finally:
            control.close()
            jobs.close()
        # THE POOL AXIS: one activated generation, and every allocation
        # stamped with it. `scheduler.reserve` writes the CURRENT POOL
        # generation into each allocation row, so this is what a reader of
        # `allocation.generation` would have answered for every attempt.
        self.assertEqual(pool, 1)
        self.assertEqual(allocations, {1})
        # THE ASSIGNMENT AXIS: NOT the same numbers. The review attempts
        # activate a second assignment generation on their own attempts while
        # the pool never moves, so at least one attempt's assignment
        # generation is 2 where its allocation says 1.
        self.assertEqual(set(assignments.values()), {1, 2})
        differing = sorted(one for one, generation in assignments.items()
                           if generation not in allocations)
        self.assertTrue(differing,
                        f"no attempt separates the axes: {assignments}")
        # AND THE SEPARATION IS THE POINT: a supervisor reading the pool axis
        # would have published 1 for these attempts, and
        # `review_for_attempt` fences an attachment to the ACTIVATED
        # generation -- so the wrong axis is not a cosmetic difference, it is
        # a verdict read that refuses.
        for attempt_id in differing:
            with self.subTest(attempt=attempt_id):
                self.assertEqual(published["generations"][attempt_id],
                                 assignments[attempt_id])
                self.assertNotIn(published["generations"][attempt_id],
                                 allocations)

    def test_an_INTERRUPTION_through_the_command_publishes_and_still_raises(
            self):
        """The whole lifecycle is protected, not just the serving loop.

        A SIGTERM arriving mid-run is owed an outcome: the operator who sent
        it has to be able to read what the run left behind. This raises from
        inside the turn, where a container would be, and asserts that the
        command still wrote the document and still let the interruption
        through rather than swallowing it into a tidy exit status.
        """
        def interrupting(_gate, _context):
            raise KeyboardInterrupt("the operator stopped this run")

        with self.assertRaises(baseline_interrupted()):
            self.commanded(wrap=interrupting)
        # THE DOCUMENT IS ON DISK EVEN THOUGH THE COMMAND RAISED.
        outcome = os.path.join(self.packet_root(), "run", "outcome.json")
        self.assertTrue(os.path.exists(outcome))
        with open(outcome, encoding="utf-8") as handle:
            published = json.load(handle)
        # `stopped` NAMES HOW SERVING ENDED, and serving ended at its bound.
        # `baseline._guarded` catches `BaseException` on purpose so that an
        # interruption arriving inside a turn is RECORDED rather than allowed
        # to abandon the shutdown -- cancellation, cleanup and publication
        # still run, and `supervise` re-raises once the document is on disk.
        # That is the protection being asserted here, so this asserts the
        # record rather than the loop's exit reason.
        self.assertEqual(published["state"], "held")
        self.assertTrue(any("KeyboardInterrupt" in one
                            for one in published["interruptions"]),
                        published["interruptions"])
        self.assertTrue(any("KeyboardInterrupt" in one
                            for one in published["held_because"]),
                        published["held_because"])
        # AND THE SHUTDOWN STILL RAN TO THE END rather than being abandoned.
        self.assertIs(published["admission_closed_before_cancellation"], True)
        self.assertIn("cleanup_sweeps", published)
        self.assertEqual(published["verdicts"], {})

    def answering(self):
        """The deterministic turn, driven from the RUNTIME CONTEXT.

        THE HANDLE IS SET HERE. `mounted_at` reads `self._composed`, which the
        fixture's own `serving` sets and `main`'s composition does not -- so
        through the command every turn raised `AttributeError`, `_guarded`
        recorded it as uncertainty, and no implementation ever completed.

        Review 2026-09-23T18:47:09Z also found that this helper was defined
        TWICE and my fix had landed in the OTHER one, `turning`. Two
        definitions of one name in a class is a silent shadowing: the second
        wins and the first is unreachable, so a correction applied to the
        wrong one looks applied. There is one now.
        """
        answered = set()

        def turns(gate, context):
            self._composed = context["operations"]
            for attempt_id, kind in sorted(gate.launched.items()):
                if attempt_id in answered:
                    continue
                mounted = self.mounted_at(context["operations"], attempt_id)
                if not mounted:
                    continue
                if kind == "implementation":
                    edits = {"harness.py": "print('answered')\n"}
                    if gate.job_of(attempt_id) == "job-b":
                        edits = {"feature.py": self.B_FEATURE,
                                 "feature_check.py": self.B_CHECK}
                else:
                    report = copy.deepcopy(self.REPORT)
                    report["verdict"] = "accepted"
                    edits = {"review-report.json": json.dumps(report)}
                self.turn(context["control"], kind, attempt_id, mounted,
                          edits=edits)
                answered.add(attempt_id)

        return turns

    def test_an_unresolved_template_is_refused_by_name(self):
        into = os.path.join(self.packet_root(), "refused")
        answer = self.composing(self.SHIPPED, into)
        self.assertNotEqual(answer.returncode, 0)
        self.assertIn("not resolved", answer.stderr + answer.stdout)
        self.assertFalse(os.path.exists(into))


class EachJobCollectsItsOwnFROZENAttributedVerdict(ArrangedCase):
    """R3 in full: two verdicts, each DERIVED from its own frozen result.

    Reaching two reviewers is not collecting two verdicts, and the previous
    claim said so rather than implying otherwise. This drives both review
    turns to completion and then reads each verdict back the way the manager
    itself does -- `review_driver.review_verdict_from_result`, which refuses
    unless the frozen result belongs to this attachment's attempt, its
    retained manifest names the same result and the same assignment at the
    same generation, and the base, head and tree the reviewer reports are the
    ones the checkpoint's own evidence records.
    """

    def verdict_for(self, held, job_id):
        """One Job's attachment and the verdict derived from its own result.

        `review_for_attempt(store, *, attempt_id, generation)` -- the
        generation is not optional, because an attempt may be offered more
        than once and an attachment belongs to ONE of those assignments.
        """
        from baton_v12.job_manager import review_driver
        from baton_v12.worker_manager import review_cycles
        attempt = self.reviewed_attempt(held, job_id)
        attachment = review_cycles.review_for_attempt(
            held.control, attempt_id=attempt,
            generation=self.generation_of(held, attempt))
        self.assertIsNotNone(attachment,
                             f"{job_id} has no review attachment")
        return attachment, review_driver.review_verdict_from_result(
            held.control, attachment_id=attachment["attachment_id"])

    def generation_of(self, held, attempt_id):
        """The assignment generation this attempt was prepared at.

        Taken from the PREPARATION RECORD the worker that prepared this
        attempt holds -- the same fact `preparing` uses to answer which worker
        that was -- rather than from a store reader this build does not
        export. `review_for_attempt` fences an attachment to one activated
        generation, so this is the operand it needs.
        """
        _worker, prepared = self.preparing(held.composed, attempt_id)
        return prepared["generation"]

    def reviewed_attempt(self, held, job_id):
        return (held.first_review if job_id == "job-a"
                else held.second_review)

    def both(self):
        return self.both_accepted()

    def test_both_verdicts_are_derived_from_their_own_frozen_results(self):
        held = self.both()
        held_verdicts = {}
        for job_id in ("job-a", "job-b"):
            with self.subTest(job=job_id):
                attachment, verdict = self.verdict_for(held, job_id)
                self.assertEqual(verdict["verdict"], "accepted")
                self.assertEqual(verdict["attempt_id"],
                                 attachment["runtime_attempt_id"])
                held_verdicts[job_id] = verdict
        # TWO VERDICTS, NOT ONE COUNTED TWICE.
        self.assertNotEqual(held_verdicts["job-a"]["attachment_id"],
                            held_verdicts["job-b"]["attachment_id"])
        self.assertNotEqual(held_verdicts["job-a"]["result_id"],
                            held_verdicts["job-b"]["result_id"])

    def test_each_verdict_is_bound_to_its_own_checkpoint_and_objects(self):
        """The cross-binding, which is what makes a claim a verdict."""
        from baton_v12.worker_manager import checkpoint_of
        held = self.both()
        for job_id in ("job-a", "job-b"):
            with self.subTest(job=job_id):
                attachment, verdict = self.verdict_for(held, job_id)
                self.assertEqual(verdict["checkpoint_id"],
                                 attachment["checkpoint_id"])
                held_checkpoint = checkpoint_of(held.control,
                                                verdict["checkpoint_id"])
                evidence = held_checkpoint.get("evidence") or {}
                for name in ("base", "head", "tree"):
                    if evidence.get(name) is not None:
                        self.assertEqual(verdict[name], evidence[name])

    def test_each_reviewer_is_the_one_configured_for_that_job(self):
        """Independence, read from the retained attachment rows."""
        held = self.both()
        identities = {}
        for job_id, worker in (("job-a", "review-worker"),
                               ("job-b", "review-worker-b")):
            attachment, _verdict = self.verdict_for(held, job_id)
            identities[job_id] = attachment["reviewer_worker_id"]
            with self.subTest(job=job_id):
                self.assertEqual(attachment["reviewer_worker_id"], worker)
        self.assertNotEqual(identities["job-a"], identities["job-b"])

    def test_no_correction_round_opened_for_either_job(self):
        """`correction_policy: "decline"` is composed; this is it holding.

        `line_of` rather than `line_status`: the latter answers an operator's
        whole report and needs a storage-usage operand this witness has no
        business supplying. The line's own recorded state is the fact.
        """
        from baton_v12.worker_manager import line_of
        held = self.both()
        for job_id in ("job-a", "job-b"):
            with self.subTest(job=job_id):
                states = self.states_for(held.job, held.composed, job_id)
                self.assertEqual(states["review"], "completed")
                line = self.line_of(held.composed, job_id)["line_id"]
                self.assertEqual(line_of(held.control, line)["state"],
                                 "accepted")


class TheGateAdmitsFourAndNoMore(ArrangedCase):
    """R4's admission boundary, over the real two-Job traversal.

    The bounded run this gate belongs to is NOT finished, and PLAN.md says so.
    What is finished is the part that decides what may be admitted at all,
    and it is driven here rather than described: the gate wraps the composed
    operations for a whole traversal, both Jobs code, both are reviewed, and
    the counts are read off the gate itself.
    """

    def gated(self, **members):
        """The gate, wrapping a RECORDER rather than the composed operations.

        The gate is a proxy over the three admitting acts, so what these
        cases measure is its decisions. Handing it the real composed
        operations and synthetic stage documents would reach the deployment
        and fail on the operands a real stage carries -- which says nothing
        about the rule under test. The real traversal is measured separately,
        by the cases above, through the composed operations themselves.
        """
        import two_job_supervisor
        two_job_supervisor.held_baseline()

        class Recorder:
            def __init__(self):
                self.admitted = []

            def admit(self, stage, job):
                self.admitted.append((stage.get("job_id"), stage.get("kind")))
                return {"stage_id": stage.get("stage_id")}

            def claim(self, stage):
                return stage

            def launch(self, attempt, job):
                return attempt

        self.recorder = Recorder()
        self.gate = two_job_supervisor.TwoJobGate(
            self.recorder, job_ids=("job-a", "job-b"))
        return self.recorder

    def test_the_gate_binds_the_accepted_machinery_by_digest(self):
        import two_job_supervisor
        self.assertEqual(two_job_supervisor.held_baseline(),
                         two_job_supervisor.BASELINE_SHA256)
        self.assertEqual(two_job_supervisor.CAPS,
                         {"implementation": 2, "review": 2})
        self.assertEqual(two_job_supervisor.CAPS,
                         two_jobs.LIMITS["admissions"])

    def test_a_third_job_is_refused_before_anything_is_served(self):
        import two_job_supervisor
        with self.assertRaises(two_job_supervisor.SupervisorRefusal):
            two_job_supervisor.TwoJobGate(
                object(), job_ids=("job-a", "job-b", "job-c"))
        with self.assertRaises(two_job_supervisor.SupervisorRefusal):
            two_job_supervisor.TwoJobGate(object(),
                                          job_ids=("job-a", "job-a"))

    def test_four_admissions_are_spent_and_a_fifth_is_refused(self):
        """Two implementations and two reviews, taken ON THE GATE.

        The first version of this case ran the fixture traversal -- which
        goes through the COMPOSED operations, not through this gate -- and
        then SET `gate.admissions` by hand before asserting the fifth was
        refused. That would have been asserting an assignment. The four
        admitting acts are taken on the gate here, so the counts are its own.
        """
        from baton_v12.contracts import ContractRefusal
        held = self.gated()
        job = None
        for kind in ("implementation", "review"):
            for job_id in ("job-a", "job-b"):
                with self.subTest(kind=kind, job=job_id):
                    self.gate.admit({"kind": kind, "job_id": job_id,
                                     "stage_id": f"{job_id}/{kind}"}, job)
        self.assertEqual(self.gate.admissions,
                         {"implementation": 2, "review": 2})
        self.assertEqual(self.gate.refusals, [])
        self.assertEqual(sorted(held.admitted),
                         [("job-a", "implementation"), ("job-a", "review"),
                          ("job-b", "implementation"), ("job-b", "review")])
        # AND THE FIFTH OF EITHER KIND IS REFUSED, whichever Job asks.
        for kind in ("implementation", "review"):
            with self.subTest(kind=kind), self.assertRaises(ContractRefusal):
                self.gate.admit({"kind": kind, "job_id": "job-a",
                                 "stage_id": f"job-a/{kind}-again"}, job)
        self.assertEqual(len(self.gate.refusals), 2)
        self.assertEqual(self.gate.admissions,
                         {"implementation": 2, "review": 2})

    def test_a_stopped_gate_admits_nothing_further(self):
        """What a bounded stop rests on, asserted rather than assumed."""
        from baton_v12.contracts import ContractRefusal
        held = self.gated()
        job = None
        self.gate.admit({"kind": "implementation", "job_id": "job-a",
                         "stage_id": "job-a/implementation"}, job)
        self.gate.stopped = True
        with self.assertRaises(ContractRefusal):
            self.gate.admit({"kind": "review", "job_id": "job-b",
                             "stage_id": "job-b/review"}, job)
        self.assertEqual(self.gate.admissions,
                         {"implementation": 1, "review": 0})

    def test_the_gate_records_the_provenance_a_verdict_read_needs(self):
        """Review 2026-09-23T18:06:35Z: nothing ever wrote these two.

        `generations` and `stage_of` were read through `getattr` defaults and
        no code populated them, so the public attachment reader was handed
        `generation=None` and refused, and `job_of` answered None. A reader
        with a default for a fact nobody records answers "unknown" quietly.
        """
        held = self.gated()
        job = None
        self.gate.admit({"kind": "review", "job_id": "job-b",
                         "stage_id": "job-b/review"}, job)
        self.gate.launch({"attempt_id": "attempt-b", "stage_id": "job-b/review",
                          "assignment_generation": 7}, job)
        # WHAT THIS CASE PROVES IS THE STAGE AND JOB MAPPING. It used to
        # assert a generation too, from a synthetic `assignment_generation=7`
        # I supplied -- which proved only that a dict I wrote had the key I
        # put in it. Review 2026-09-23T18:10:37Z: the projection attempt the
        # manager really passes carries NO generation, and the real value
        # comes from the allocation. `TheBoundedTwoJobRunStops...` asserts
        # that one, on a driven run.
        self.assertEqual(self.gate.stage_of["attempt-b"], "job-b/review")
        self.assertEqual(self.gate.job_of("attempt-b"), "job-b")
        self.assertEqual(self.gate.launched["attempt-b"], "review")
        del held

    def test_a_stage_of_neither_job_is_foreign_rather_than_a_cap_refusal(self):
        import two_job_supervisor
        from baton_v12.contracts import ContractRefusal
        held = self.gated()
        job = None
        with self.assertRaises(ContractRefusal):
            self.gate.admit({"kind": "implementation", "job_id": "job-c",
                             "stage_id": "job-c/implementation"}, job)
        self.assertEqual(len(self.gate.foreign), 1)
        self.assertEqual(held.admitted, [])
        self.assertEqual(self.gate.refusals, [])
        self.assertEqual(self.gate.admissions,
                         {"implementation": 0, "review": 0})
        del two_job_supervisor


class TheBoundedTwoJobRunStopsAndAccountsForItself(ArrangedCase):
    """R4's whole path: serve, stop, close, cancel, clean up, publish.

    DRIVEN OVER THE REAL COMPOSED DEPLOYMENT -- this arrangement's own `/2`
    document, the accepted fixture's stores and its deterministic turn -- so
    what is measured is the supervisor's behaviour rather than a recorder's.
    The clock is injected, which is how a 600-second bound is proved in
    milliseconds without pretending the arithmetic is different.
    """

    def supervised(self, *, bounds=None, ticks=None, fail=False,
                   interrupt=False, submitted=False):
        import two_job_supervisor
        from baton_v12.job_manager import submit
        job, control, composed = self.serving_two(**self.traversing())
        if submitted:
            submit(job, self.both_jobs())
        moments = iter(ticks or range(0, 10_000, 5))

        def monotonic():
            try:
                return float(next(moments))
            except StopIteration:                            # pragma: no cover
                return 1e9

        held = composed
        if fail or interrupt:
            failing = RuntimeError("the serving loop faulted")
            stopping = KeyboardInterrupt("an operator asked it to stop")

            class Faulting:
                def __init__(self, inner):
                    self._inner = inner
                    self._ticks = 0

                def admit(self, stage, job):
                    self._ticks += 1
                    if self._ticks > 1:
                        raise stopping if interrupt else failing
                    return self._inner.admit(stage, job)

                def __getattr__(self, name):
                    return getattr(self._inner, name)

            held = Faulting(composed)
        outcome = os.path.join(self.packet_root(), "outcome.json")
        return two_job_supervisor, job, control, held, outcome, bounds or {
            "total_seconds": 600, "cleanup_seconds": 60}

    def packet_root(self):
        held = os.path.join(self.root, "supervised")
        os.makedirs(held, exist_ok=True)
        return held

    def deployment_path(self):
        """A document carrying this run's retention policy, for the journal."""
        place = os.path.join(self.packet_root(), "deployment.json")
        with open(place, "w", encoding="utf-8") as handle:
            json.dump(self.composed_document(**self.two_jobs()), handle,
                      indent=2, sort_keys=True)
        return place

    def driven(self, **members):
        module, job, control, composed, outcome, bounds = self.supervised(
            submitted=True, **members)
        self.supervised_control = control
        return module, module.supervise(
            job, control, composed, job_ids=("job-a", "job-b"),
            bounds=bounds, outcome_path=outcome,
            deployment_path=self.deployment_path(),
            clock=lambda: "1970-01-01T00:00:00.000Z",
            sleep=lambda _seconds: None,
            monotonic=self.monotonic_for(members)), outcome

    def monotonic_for(self, members):
        held = iter(members.get("ticks") or range(0, 10_000, 5))

        def monotonic():
            try:
                return float(next(held))
            except StopIteration:                            # pragma: no cover
                return 1e9

        return monotonic

    def published(self, outcome):
        with open(outcome, encoding="utf-8") as handle:
            return json.load(handle)

    def test_the_run_stops_at_total_minus_cleanup_and_publishes(self):
        _module, measured, outcome = self.driven()
        self.assertEqual(measured["serving_bound_seconds"], 540)
        self.assertEqual(measured["stopped"], "serving-bound-exceeded")
        self.assertEqual(self.published(outcome)["schema"],
                         "baton.v12.two-job-outcome/1")
        self.assertEqual(measured["caps"], {"implementation": 2, "review": 2})

    def test_admission_is_closed_before_anything_is_cancelled(self):
        _module, measured, _outcome = self.driven()
        self.assertTrue(measured["admission_closed_before_cancellation"])
        self.assertLessEqual(sum(measured["admissions"].values()), 4)

    def test_the_cleanup_window_is_inside_the_total(self):
        _module, measured, _outcome = self.driven()
        self.assertGreaterEqual(measured["cleanup_window_seconds"], 0)
        self.assertLessEqual(measured["cleanup_window_seconds"],
                             measured["bounds"]["cleanup_seconds"])

    def test_the_run_records_the_REAL_assignment_generations(self):
        """From each stage's own allocation, not from the launch document.

        `baton.v12.job-status/4` reports the allocation with its generation,
        worker, participant and principal -- the owner's record of the
        assignment an attempt was prepared under, and the generation
        `review_for_attempt` fences an attachment to.
        """
        _module, measured, _outcome = self.driven()
        # FROM THE ASSIGNMENT, NOT THE POOL. Review 2026-09-23T18:16:47Z:
        # `allocation.generation` is the POOL generation -- the projection
        # joins `pool_generations` for it -- and the two axes happening to
        # share the value 1 is the easiest possible false pass. This asserts
        # the value the SUPPORTED reader gives, and that it is the one
        # `assignment_of` would answer for each attempt.
        from baton_v12.worker_manager import attempts as attempt_rows
        self.assertTrue(measured["generations"],
                        "no assignment generation was captured")
        for attempt_id, generation in measured["generations"].items():
            with self.subTest(attempt=attempt_id):
                self.assertEqual(
                    attempt_rows.assignment_of(
                        self.supervised_control, attempt_id)["generation"],
                    generation)
        for attempt_id in measured["admitted_attempts"]:
            with self.subTest(attempt=attempt_id):
                self.assertIsNotNone(measured["generations"].get(attempt_id))
        self.assertEqual(measured["uncertainty"], [])

    def turning(self, held):
        """The deterministic worker turn, where the container would be.

        One callback, invoked each serving tick with the gate. For every
        attempt the gate has launched and not yet answered, it runs the
        fixture's own turn -- the same one every accepted v12 lifecycle case
        uses -- writing an implementation body or a review report by kind.
        """
        answered = set()

        def turns(gate, context):
            # `mounted_at` reads `self._composed`, which the fixture's own
            # `serving` sets and `main`'s composition does not -- so through
            # the command every turn raised AttributeError, was recorded as
            # uncertainty, and the implementations never completed. That is
            # the whole of the 2/0 that looked like a product question.
            self._composed = context["operations"]
            for attempt_id, kind in sorted(gate.launched.items()):
                if attempt_id in answered:
                    continue
                mounted = self.mounted_at(context["operations"],
                                          attempt_id)
                if not mounted:
                    continue
                if kind == "implementation":
                    edits = {"harness.py": "print('answered')\n"}
                    if gate.job_of(attempt_id) == "job-b":
                        edits = {"feature.py": self.B_FEATURE,
                                 "feature_check.py": self.B_CHECK}
                else:
                    report = copy.deepcopy(self.REPORT)
                    report["verdict"] = "accepted"
                    edits = {"review-report.json": json.dumps(report)}
                self.turn(held["control"], kind, attempt_id, mounted,
                          edits=edits)
                answered.add(attempt_id)

        return turns

    def test_the_SUPERVISED_run_reaches_four_attempts_and_two_verdicts(self):
        """R4's success: the whole bounded run, over the composed deployment.

        The supervisor serves, the deterministic turn answers where a
        container would, both Jobs reach their own reviewers, both verdicts
        are DERIVED from their own frozen results, and every runtime this run
        launched has a positive cleanup.
        """
        import two_job_supervisor
        from baton_v12.job_manager import submit
        job, control, composed = self.serving_two(**self.traversing())
        submit(job, self.both_jobs())
        held = {"job": job, "control": control, "composed": composed}
        outcome = os.path.join(self.packet_root(), "supervised-outcome.json")
        measured = two_job_supervisor.supervise(
            job, control, composed, job_ids=("job-a", "job-b"),
            bounds={"total_seconds": 600, "cleanup_seconds": 60},
            outcome_path=outcome, deployment_path=self.deployment_path(),
            clock=lambda: "1970-01-01T00:00:00.000Z",
            sleep=lambda _seconds: None,
            monotonic=self.monotonic_for({}),
            turns=self.turning(held))
        self.assertEqual(sum(measured["admissions"].values()), 4,
                         measured["admissions"])
        self.assertEqual(sorted(measured["verdicts"]), ["job-a", "job-b"])
        for job_id, verdict in measured["verdicts"].items():
            with self.subTest(job=job_id):
                self.assertEqual(verdict["verdict"], "accepted")
        self.assertEqual(measured["outstanding_cleanup"], [])
        self.assertEqual(measured["state"], "settled", measured["held_because"])
        with open(outcome, encoding="utf-8") as handle:
            self.assertEqual(json.load(handle)["state"], "settled")

    def test_a_serving_failure_still_publishes_an_outcome(self):
        _module, measured, outcome = self.driven(fail=True)
        self.assertEqual(measured["stopped"], "serving-failed")
        self.assertIsNotNone(measured["serving_failure"])
        self.assertEqual(measured["state"], "held")
        self.assertTrue(self.published(outcome)["held_because"])

    def test_an_interruption_publishes_the_outcome_and_still_raises(self):
        import two_job_supervisor
        with self.assertRaises(baseline_interrupted()) as caught:
            self.driven(interrupt=True)
        del caught, two_job_supervisor
        # THE OUTCOME IS ON DISK EVEN THOUGH THE CALL RAISED.
        outcome = os.path.join(self.packet_root(), "outcome.json")
        self.assertTrue(os.path.exists(outcome))
        self.assertEqual(self.published(outcome)["stopped"], "interrupted")

    def test_a_run_that_admitted_nothing_is_HELD_rather_than_settled(self):
        """The defect this rule closes, asserted rather than trusted.

        Review 2026-09-23T17:44:56Z drove an EMPTY serve and got `settled`
        with zero admissions and no verdicts, because "settled" had meant
        "nothing to complain about". Success is what the run produced.
        """
        import two_job_supervisor
        from baton_v12.job_manager import JobStore
        del JobStore
        module, job, control, composed, outcome, bounds = self.supervised()
        measured = module.supervise(
            job, control, composed, job_ids=("job-a", "job-b"),
            bounds=bounds, outcome_path=outcome,
            deployment_path=self.deployment_path(),
            clock=lambda: "1970-01-01T00:00:00.000Z",
            sleep=lambda _seconds: None,
            monotonic=self.monotonic_for({}))
        # NOTHING WAS SUBMITTED BY THIS PATH, so nothing could be admitted.
        self.assertEqual(measured["state"], "held")
        # THE REASON IS NOW ABOUT RESULTS, not admission counts: review
        # 2026-09-23T18:00:25Z asked for a result-based predicate, and a run
        # that produced no verdict is held whatever its counters say.
        self.assertTrue(any("no attributed verdict" in one
                            for one in measured["held_because"]),
                        measured["held_because"])
        self.assertEqual(measured["verdicts"], {})
        self.assertEqual(self.published(outcome)["state"], "held")
        del two_job_supervisor

    def recording_termination(self):
        """A Termination that records rather than touching a handler.

        The reviewer used exactly this shape, and it is the right one: what is
        under test is whether `supervise` restores what it installed, not
        whether `signal.signal` works.
        """
        class Recording:
            def __init__(self):
                self.received = []
                self.installed = self.deferred = self.restored = False

            def install(self):
                self.installed = True
                return self

            def defer(self):
                self.deferred = True

            def restore(self):
                self.restored = True

        return Recording()

    def faulting_run(self, *, at, failure):
        """One bounded run with a fault injected AFTER serving.

        `at` names a module attribute of the supervisor that the run calls
        during finalization; the wrapper raises instead. Injecting through a
        real step rather than a sentinel keeps the region under test the one
        an operator's run actually executes.
        """
        import two_job_supervisor
        from baton_v12.job_manager import submit
        module, job, control, composed, outcome, bounds = self.supervised()
        submit(job, self.both_jobs())
        held = {"job": job, "control": control, "composed": composed}
        termination = self.recording_termination()
        original = getattr(two_job_supervisor, at)

        def faulting(*arguments, **members):
            del arguments, members
            raise failure

        setattr(two_job_supervisor, at, faulting)
        try:
            caught = None
            try:
                module.supervise(
                    job, control, composed, job_ids=("job-a", "job-b"),
                    bounds=bounds, outcome_path=outcome,
                    deployment_path=self.deployment_path(),
                    clock=lambda: "1970-01-01T00:00:00.000Z",
                    sleep=lambda _seconds: None,
                    monotonic=self.monotonic_for({}),
                    termination=termination,
                    turns=self.turning(held))
            except BaseException as raised:                   # noqa: BLE001
                caught = raised
        finally:
            setattr(two_job_supervisor, at, original)
        return termination, outcome, caught

    def test_a_fault_AFTER_serving_still_restores_and_still_publishes(self):
        """The region my `finally` did not cover, entered deliberately.

        Review 2026-09-23T19:22:24Z injected a fault after serving and cleanup
        and measured `installed=True, restored=False, outcome_exists=False`.
        My `finally` surrounded `_publish` alone while the comment above it
        said it surrounded everything. This asserts all three of the values
        that reading produced, with the signs they should have.
        """
        failure = RuntimeError("the verdict read faulted")
        termination, outcome, caught = self.faulting_run(
            at="verdicts_of", failure=failure)
        self.assertTrue(termination.installed)
        # THE THREE VALUES THE REVIEWER MEASURED.
        self.assertTrue(termination.restored)
        self.assertTrue(os.path.exists(outcome))
        self.assertIs(caught, failure)
        published = self.published(outcome)
        # AND THE DOCUMENT SAYS WHAT HAPPENED rather than reading like a run
        # that finished with nothing to report.
        self.assertIn("the verdict read faulted",
                      published["finalization_failure"])
        self.assertEqual(published["state"], "held")
        self.assertTrue(any("faulted after serving" in one
                            for one in published["held_because"]),
                        published["held_because"])

    def test_the_FINAL_CLOCK_faulting_no_longer_costs_the_outcome(self):
        """The reviewer's exact injection, and what it should cost now.

        A finalizer that re-raises on the same call it exists to recover from
        protects nothing, so `_moment_of` answers None and the document says
        the instant was never taken. The run is otherwise unharmed: it still
        collected both verdicts, so it is still settled.
        """
        import two_job_supervisor
        from baton_v12.job_manager import submit
        module, job, control, composed, outcome, bounds = self.supervised()
        submit(job, self.both_jobs())
        held = {"job": job, "control": control, "composed": composed}
        termination = self.recording_termination()
        # THE CLOCK FAULTS ONLY ONCE FINALIZATION IS REACHED, signalled by the
        # real step that runs immediately before the final instant is taken.
        state = {"final": False}
        original = two_job_supervisor.verdicts_of

        def reached(*arguments, **members):
            answer = original(*arguments, **members)
            state["final"] = True
            return answer

        def clock():
            if state["final"]:
                raise RuntimeError("the clock faulted")
            return "1970-01-01T00:00:00.000Z"

        two_job_supervisor.verdicts_of = reached
        try:
            measured = module.supervise(
                job, control, composed, job_ids=("job-a", "job-b"),
                bounds=bounds, outcome_path=outcome,
                deployment_path=self.deployment_path(),
                clock=clock, sleep=lambda _seconds: None,
                monotonic=self.monotonic_for({}), termination=termination,
                turns=self.turning(held))
        finally:
            two_job_supervisor.verdicts_of = original
        self.assertTrue(termination.restored)
        self.assertTrue(os.path.exists(outcome))
        published = self.published(outcome)
        self.assertIsNone(published["finished_at"])
        self.assertIsNone(published["finalization_failure"])
        self.assertEqual(published["state"], "settled",
                         published["held_because"])
        self.assertEqual(sorted(measured["verdicts"]), ["job-a", "job-b"])

    def test_a_PUBLICATION_that_faults_still_restores_the_handler(self):
        """The worst ending this run has, and the one it must not hide.

        Nothing reaches disk, so an operator cannot read what happened. The
        failure therefore has to reach the caller -- a tidy return here would
        be a run reporting success for an outcome nobody can find -- and the
        handler still has to come off this process.
        """
        from baton_v12.job_manager import submit
        module, job, control, composed, outcome, bounds = self.supervised()
        submit(job, self.both_jobs())
        held = {"job": job, "control": control, "composed": composed}
        termination = self.recording_termination()
        failure = OSError("the outcome could not be written")

        def publishing(*arguments, **members):
            del arguments, members
            raise failure

        original = module.baseline._publish                   # noqa: SLF001
        module.baseline._publish = publishing                 # noqa: SLF001
        try:
            with self.assertRaises(OSError) as caught:
                module.supervise(
                    job, control, composed, job_ids=("job-a", "job-b"),
                    bounds=bounds, outcome_path=outcome,
                    deployment_path=self.deployment_path(),
                    clock=lambda: "1970-01-01T00:00:00.000Z",
                    sleep=lambda _seconds: None,
                    monotonic=self.monotonic_for({}),
                    termination=termination, turns=self.turning(held))
        finally:
            module.baseline._publish = original               # noqa: SLF001
        self.assertIs(caught.exception, failure)
        self.assertTrue(termination.restored)
        self.assertFalse(os.path.exists(outcome))

    def test_a_reserve_outside_the_total_is_refused(self):
        import two_job_supervisor
        module, job, control, composed, outcome, _bounds = self.supervised()
        with self.assertRaises(two_job_supervisor.SupervisorRefusal):
            module.supervise(job, control, composed,
                             job_ids=("job-a", "job-b"),
                             bounds={"total_seconds": 60,
                                     "cleanup_seconds": 60},
                             outcome_path=outcome,
                             deployment_path=self.deployment_path())


class NoCallbackInThisDossierIsSilentlyShadowed(unittest.TestCase):
    """The defect that came back twice, made into a failing check.

    Review 2026-09-23T18:47:09Z found `answering` defined twice and my fix
    landed in the unreachable copy. I removed it. Review 2026-09-23T19:04:38Z
    found it AGAIN, at 724 and 763, with the later one missing the composed
    handle -- and the suite was green through both, because a second
    definition of a method is legal Python and nothing here ever looked.

    Two definitions of one name in one class is never intentional in this
    dossier: the second silently wins, so a correction applied to the first
    looks applied and does nothing. These two checks are what makes that a
    red suite instead of a reading.
    """

    def modules(self):
        """Every module this dossier owns, by path."""
        found = sorted(pathlib.Path(__file__).resolve().parent.glob("*.py"))
        self.assertIn("test_two_jobs.py", [one.name for one in found])
        return found

    def test_no_class_defines_one_method_twice(self):
        """STRUCTURAL, over the source rather than over the imported class.

        Importing cannot see this at all -- by the time a class object exists
        the shadowed definition has already been discarded. So this reads the
        text, which is the only place both definitions are still visible.
        """
        for place in self.modules():
            with self.subTest(module=place.name):
                parsed = ast.parse(place.read_text(encoding="utf-8"))
                for node in ast.walk(parsed):
                    if not isinstance(node, ast.ClassDef):
                        continue
                    seen = {}
                    for one in node.body:
                        if isinstance(one, (ast.FunctionDef,
                                            ast.AsyncFunctionDef)):
                            seen.setdefault(one.name, []).append(one.lineno)
                    repeated = {name: lines
                                for name, lines in seen.items()
                                if len(lines) > 1}
                    self.assertEqual(
                        repeated, {},
                        f"{place.name}:{node.name} defines a method more than "
                        f"once; the later definition silently wins")

    def test_the_bound_callback_sets_the_composed_handle(self):
        """BEHAVIOURAL, on the callback the class actually binds.

        `mounted_at` reads `self._composed`, which the fixture's own `serving`
        sets and `main`'s composition does not. A turn that does not set it
        raises `AttributeError` on every tick, `_guarded` records that as one
        line of uncertainty, no implementation ever completes, and the run
        reports two admissions and no verdict. That is exactly what
        `{implementation: 2, review: 0}` was.

        No fixture is started here: a gate with nothing launched makes the
        loop body unreachable, so this asserts the handle and nothing else.
        """
        held = SimpleNamespace()
        turns = TheSHIPPEDTemplateComposesThroughTheACTUALCLI.answering(held)
        operations = object()
        turns(SimpleNamespace(launched={}),
              {"operations": operations, "control": None})
        self.assertIs(getattr(held, "_composed", None), operations,
                      "the bound callback did not set the composed handle")


class TheOPERATORRecipePrintsOperandsThatAGREE(unittest.TestCase):
    """The page an operator types from, read as an operator would.

    Review 2026-09-23T19:22:24Z found step 6 inspecting `<run root>/db/...`
    while step 4 opened `<run root>/...`. Nothing here could catch it: every
    other check reaches the live objects, and the objects were right. What was
    wrong was the text, so this reads the text.
    """

    PAGE = os.path.join(HERE, "ADOPTION-247941.md")

    def page(self):
        with open(self.PAGE, encoding="utf-8") as handle:
            return handle.read()

    def operands(self, page, flag):
        """Every value the page gives to one long flag."""
        import re
        return re.findall(rf'{re.escape(flag)}\s+"([^"]+)"', page)

    def test_the_inspect_step_names_the_stores_the_run_step_OPENS(self):
        """One store per axis across the whole page, or this fails."""
        page = self.page()
        jobs = set(self.operands(page, "--job-store")
                   + self.operands(page, "--store"))
        control = set(self.operands(page, "--control-store")
                      + self.operands(page, "--control"))
        # THE BOOTSTRAP'S OWN LAYOUT. `tools.bootstrap.layout` puts the four
        # stores under `db/`; review 2026-09-23T20:34:15Z found the page
        # naming three layouts, and my previous reconciliation moved the
        # inspect step onto the run step's ROOT-level paths -- the wrong side.
        self.assertEqual(jobs, {"$ROOT/db/jobs.sqlite3"})
        self.assertEqual(control, {"$ROOT/db/control.sqlite3"})
        # AND NO PLACEHOLDER SURVIVES IN A COMMAND, because `<run root>` read
        # as either directory could not make document and store paths agree.
        for line in page.splitlines():
            if line.strip().startswith(("--", "BATON_V12_", "ROOT=")):
                with self.subTest(line=line.strip()[:48]):
                    self.assertNotIn("<run root>", line)

    def test_the_page_does_not_promise_a_document_it_may_not_write(self):
        """The failure contract, on the page rather than in a docstring.

        Review 2026-09-23T19:48:52Z: "Handoff 250536 and current PLAN say
        ADOPTION explains pre-execution refusal versus an owed outcome. The
        current ADOPTION-247941.md does not." I had written the distinction
        into a test docstring and then reported that the page carried it.

        Two of this dossier's own cases contradict the prose that was there:
        the renamed pre-execution case asserts NO outcome file exists when the
        composition refuses, and the publication-failure case deliberately
        leaves nothing on disk. A page that says "on every path" is telling an
        operator something the tests say is false.
        """
        page = self.page()
        self.assertNotIn("**on every path**", page)
        for promised in (
                "When there is a document, and when there is not",
                "leaves no `outcome.json`",
                "is not an answer about the run",
                "neither is positive cleanup"):
            with self.subTest(says=promised):
                self.assertIn(promised, page)

    def test_the_check_count_the_page_states_is_the_ACTUAL_count(self):
        """Two stale `53 checks` survived a claim that added seven.

        A number in prose has no way of noticing that it is wrong, so this
        asks the loader how many cases there are and holds every count the
        page states against it.
        """
        import re
        page = self.page()
        stated = {int(one) for one
                  in re.findall(r"(\d+) checks", page)}
        self.assertTrue(stated, "the page states no check count")
        loaded = load_tests(unittest.TestLoader(), None, None)
        self.assertEqual(stated, {loaded.countTestCases()})

    def test_every_flag_the_run_step_prints_is_one_the_COMMAND_accepts(self):
        """Against the command's own `--help`, not against a list here.

        A second list of flags kept in a test is a second thing to drift.
        This asks the program.
        """
        import re
        import subprocess
        answer = subprocess.run(
            [sys.executable, "-B",
             os.path.join(HERE, "two_job_supervisor.py"), "--help"],
            capture_output=True, text=True, timeout=120, cwd=os.sep,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1",
                     PYTHONPATH=os.pathsep.join([SNAPSHOT, HERE])))
        self.assertEqual(answer.returncode, 0, answer.stderr)
        page = self.page()
        start = page.index("## Step 4 — serve the bounded run")
        block = page[start:page.index("```", page.index("```sh", start) + 5)]
        printed = sorted(set(re.findall(r"(--[a-z][a-z-]+)", block)))
        self.assertIn("--job-store", printed)
        for flag in printed:
            with self.subTest(flag=flag):
                self.assertIn(flag, answer.stdout)

    def test_every_flag_the_inspect_step_prints_is_one_the_TOOL_accepts(self):
        """The same question of `tools.job_manager status`.

        This is the step whose operands were wrong, and asking the tool is how
        the next wrong one gets caught.
        """
        import re
        import subprocess
        answer = subprocess.run(
            [sys.executable, "-B", "-m", "tools.job_manager", "--store", "x",
             "--incarnation", "x", "--authority-uuid", "0" * 32,
             "status", "--help"],
            capture_output=True, text=True, timeout=120, cwd=os.sep,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1",
                     PYTHONPATH=SNAPSHOT))
        self.assertEqual(answer.returncode, 0, answer.stderr)
        page = self.page()
        start = page.index("## Step 6 — watch, read-only")
        block = page[start:page.index("```", page.index("```sh", start) + 5)]
        printed = sorted(set(re.findall(r"(--[a-z][a-z-]+)", block)))
        self.assertIn("--control", printed)
        # `--store`, `--incarnation` and `--authority-uuid` are the TOOL's
        # operands rather than the subcommand's, so they are held against the
        # tool's own help instead.
        outer = subprocess.run(
            [sys.executable, "-B", "-m", "tools.job_manager", "--help"],
            capture_output=True, text=True, timeout=120, cwd=os.sep,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1",
                     PYTHONPATH=SNAPSHOT))
        self.assertEqual(outer.returncode, 0, outer.stderr)
        for flag in printed:
            with self.subTest(flag=flag):
                self.assertTrue(flag in answer.stdout or flag in outer.stdout,
                                f"{flag} is in neither help text")


class ThePREPARATIONDerivesWhatItUsedToAskAnOwnerFor(ArrangedCase):
    """Owner reroute 250730, driven rather than described.

    "Complete operator preparation: derive technical operands from accepted
    configuration and supported APIs instead of leaving them as owner
    questions." `prepare_two_jobs.py` is that step. These cases drive its
    derivation, its refusals and its Authority acts against a DISPOSABLE
    Authority this fixture owns -- no deployed store is opened, no container,
    credential, provider or network is reached, and no Git operation runs.
    """

    def derived(self, *, run_root=None, run_id="two-jobs-witness",
                work_ids=None):
        import prepare_two_jobs
        held = run_root or os.path.join(self.root, run_id)
        os.makedirs(os.path.join(held, "tasks"), exist_ok=True)
        tasks = {}
        for job_id in sorted(prepare_two_jobs.TASKS):
            document = prepare_two_jobs.task_document(
                job_id, run_id=run_id, base=self.base)
            raw = json.dumps(document, sort_keys=True).encode("utf-8")
            place = os.path.join(held, "tasks", f"{job_id}.json")
            with open(place, "wb") as handle:
                handle.write(raw)
            tasks[job_id] = {"path": place, "raw": raw}
        return prepare_two_jobs, prepare_two_jobs.resolved(
            run_root=held, run_id=run_id,
            source=self.config["nominated_source"], base=self.base,
            authority_uuid=self.config["authority_uuid"],
            work_ids=work_ids or {"job-a": self.work,
                                  "job-b": SECOND_WORK},
            tasks=tasks), tasks

    def bootstrapped(self, name="two-jobs-witness"):
        """A fresh instance shaped the way the bootstrap leaves one.

        A DISPOSABLE Authority under this fixture's own root -- which is
        outside both checkout boundaries, so the validator admits it -- with
        the record `receipt_of` reads. No deployed store is opened.

        THIS IS A STAND-IN, and the case below runs the REAL tool instead.
        Review 2026-09-23T20:52:13Z was right that a synthetic receipt is not
        evidence the printed bootstrap step leads into preparation; it is
        still the right fixture for the refusal cases, which are about this
        step's own rules and pay nothing for installing an 81-file runtime
        each time.
        """
        from baton_v12.authority import Authority
        root = os.path.join(self.root, name)
        os.makedirs(os.path.join(root, "db"), exist_ok=True)
        uuid = "5e1a2b3c4d5e6f708192a3b4c5d6e7f0"
        store = os.path.join(root, "db", "authority.sqlite3")
        if not os.path.exists(store):
            Authority.create(store, authority_uuid=uuid).dispose()
        with open(os.path.join(root, "bootstrap.json"), "w",
                  encoding="utf-8") as handle:
            json.dump({"schema": "baton.v12.stack-bootstrap-record/1",
                       "authority_uuid": uuid, "bindings": {}}, handle)
        return root, uuid

    def commanded(self, root, *, base=None, source=None):
        """The documented preparation command, invoked."""
        import io
        import prepare_two_jobs
        held = io.StringIO()
        status = prepare_two_jobs.main(
            ["--run-root", root,
             "--source", source or self.config["nominated_source"],
             "--base", base or self.base], stream=held)
        text = held.getvalue()
        start = text.index('{\n  "authority_uuid"')
        return status, json.loads(text[start:]), text

    def test_the_REAL_BOOTSTRAP_leads_into_this_preparation(self):
        """The printed step 2, run, and then step 3 on what it left.

        Review 2026-09-23T20:52:13Z: "Supply a concrete derived bootstrap
        input document/generator and exact command. Exercise the supported
        bootstrap preparation boundary on a disposable instance, then feed its
        actual receipt/Authority into preparation and validate the emitted
        packet."

        THE SEAM IS THE RUNTIME INSTALL. `tools.bootstrap` refuses without a
        built distribution -- "installing into ... needs a built runtime; name
        it with --distro" -- so this names the pinned one and the tool copies
        it. That copy is real work this case performs; nothing else about the
        runtime is exercised, and no scheduler is started.
        """
        import subprocess
        import prepare_two_jobs
        root = os.path.join(self.root, "two-jobs-bootstrapped")
        # STEP 2a: the inputs document, DERIVED rather than asked for.
        emitted = io.StringIO()
        self.assertEqual(
            prepare_two_jobs.main(["--run-root", root, "--source", os.sep,
                                   "--base", "a" * 40,
                                   "--emit-bootstrap-inputs"],
                                  stream=emitted), 0)
        inputs = json.loads(emitted.getvalue())
        self.assertEqual(inputs["schema"], "baton.v12.stack-bootstrap/1")
        # A FRESH INSTALL CONFIGURES NO CAPACITY, which is what makes this
        # step's own two Works unambiguous rather than in competition.
        self.assertNotIn("workers", inputs)
        self.assertNotIn("jobs", inputs)
        os.makedirs(root, exist_ok=True)
        place = os.path.join(root, "bootstrap-inputs.json")
        with open(place, "w", encoding="utf-8") as handle:
            json.dump(inputs, handle, indent=2, sort_keys=True)

        # STEP 2b: the tool itself.
        answer = subprocess.run(
            [sys.executable, "-B", "-m", "tools.bootstrap",
             "--inputs", place, "--destination", root, "--no-repositories",
             "--distro", prepare_two_jobs.ACCEPTED["runtime_path"]],
            capture_output=True, text=True, timeout=900, cwd=os.sep,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1",
                     PYTHONPATH=SNAPSHOT))
        self.assertEqual(answer.returncode, 0, answer.stdout + answer.stderr)
        # THE TOOL'S OWN WORDS about what it created, which is the
        # reconciliation the review asked for rather than an inference.
        self.assertIn("no Work, grant or placeholder was created",
                      answer.stdout)
        places = prepare_two_jobs.layout(os.path.realpath(root))
        with open(places["record"], encoding="utf-8") as handle:
            record = json.load(handle)
        self.assertTrue(os.path.isfile(places["authority_store"]))

        # STEP 3, on the receipt the tool actually wrote.
        status, receipt, _text = self.commanded(root)
        self.assertEqual(status, 0)
        self.assertEqual(receipt["authority_uuid"], record["authority_uuid"])
        for name in ("deployment", "submission", "selections"):
            with self.subTest(emitted=name):
                self.assertTrue(os.path.isfile(places[name]), places[name])
        made = [one["work_id"] for one in receipt["prepared"]["jobs"]]
        self.assertEqual(
            made, [f"{record['authority_uuid'][:8]}-W1",
                   f"{record['authority_uuid'][:8]}-W2"])

    def test_the_CHECK_mode_validates_and_writes_NOTHING(self):
        """The preflight the preparation runs, driven directly.

        Review 2026-09-23T21:06:44Z: validating in the preparation's own
        process meant `composed -> held -> from tools import stage_execution`
        resolved `tools` wherever that process found it, and I had explicitly
        tolerated the checkout's. `--check` performs the digest pins, the
        import provenance and the whole composition, and writes nothing.
        """
        import subprocess
        import prepare_two_jobs
        root, _uuid = self.bootstrapped("two-jobs-checked")
        places = prepare_two_jobs.layout(os.path.realpath(root))
        _module, document, tasks = self.derived(run_root=root)
        os.makedirs(places["tasks"], exist_ok=True)
        for one in tasks.values():
            with open(one["path"], "wb") as handle:
                handle.write(one["raw"])
        staged = os.path.join(self.root, "staged-selections.json")
        with open(staged, "w", encoding="utf-8") as handle:
            json.dump(document, handle, indent=2, sort_keys=True)
        answer = subprocess.run(
            [sys.executable, "-B", os.path.join(HERE, "two_jobs.py"),
             "--selections", staged, "--check"],
            capture_output=True, text=True, timeout=600, cwd=os.sep,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1",
                     PYTHONPATH=os.pathsep.join([SNAPSHOT, HERE])))
        self.assertEqual(answer.returncode, 0, answer.stderr)
        reported = json.loads(answer.stdout)
        self.assertEqual(reported["_written"], [])
        self.assertIs(reported["_pins_agree"], True)
        self.assertEqual(sorted(reported["_checked"]),
                         ["deployment.json", "submission.json"])
        self.assertFalse(os.path.exists(places["run"]))

    def test_the_preflight_REFUSES_when_the_digest_pins_disagree(self):
        """The pin gate, driven where the preflight actually runs.

        A first version of this case drove `two_jobs.main` IN PROCESS and
        never reached the pin gate at all: the provenance gate fired first,
        because under this runner `tools` is the checkout's. That is review
        2026-09-23T21:06:44Z's finding arriving a second time, from the other
        side -- so this drives `--check` as the subprocess the preparation
        uses, against a COPY of this dossier whose pinned digest has been
        changed. No pinned artifact is touched, and the copy is removed.
        """
        import shutil
        import subprocess
        import tempfile
        _module, document, _tasks = self.derived()
        staged = os.path.join(self.root, "pin-negative.json")
        with open(staged, "w", encoding="utf-8") as handle:
            json.dump(document, handle, indent=2, sort_keys=True)
        shadow = tempfile.mkdtemp(prefix="pin-negative-", dir=self.root)
        try:
            for one in sorted(os.listdir(HERE)):
                if one.endswith(".py"):
                    shutil.copy(os.path.join(HERE, one),
                                os.path.join(shadow, one))
            place = os.path.join(shadow, "verify_247941.py")
            with open(place, encoding="utf-8") as handle:
                body = handle.read()
            drifted = body.replace(
                '"6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771'
                'ab5801"', '"' + "0" * 64 + '"', 1)
            self.assertNotEqual(drifted, body, "the pinned digest moved")
            # THE COPY IS NOT AT THE DOSSIER'S DEPTH, so its own derived
            # checkout would resolve to `/`. Pinning it keeps this case about
            # the digest rather than about where the copy happens to live.
            held = drifted.replace("CHECKOUT = HERE.parents[4]",
                                   f"CHECKOUT = pathlib.Path({CHECKOUT!r})", 1)
            self.assertNotEqual(held, drifted, "the checkout line moved")
            drifted = held
            with open(place, "w", encoding="utf-8") as handle:
                handle.write(drifted)
            answer = subprocess.run(
                [sys.executable, "-B", os.path.join(shadow, "two_jobs.py"),
                 "--selections", staged, "--check"],
                capture_output=True, text=True, timeout=600, cwd=os.sep,
                env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1",
                         PYTHONPATH=os.pathsep.join([SNAPSHOT, shadow])))
        finally:
            shutil.rmtree(shadow, ignore_errors=True)
        self.assertNotEqual(answer.returncode, 0)
        self.assertIn("no longer match what",
                      answer.stderr + answer.stdout)
        # AND THE UNCHANGED PINS PASS, so the refusal was the pin rather than
        # the document.
        answer = subprocess.run(
            [sys.executable, "-B", os.path.join(HERE, "two_jobs.py"),
             "--selections", staged, "--check"],
            capture_output=True, text=True, timeout=600, cwd=os.sep,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1",
                     PYTHONPATH=os.pathsep.join([SNAPSHOT, HERE])))
        self.assertEqual(answer.returncode, 0, answer.stderr)

    def test_a_REFUSED_PREFLIGHT_leaves_no_selections_and_no_Authority_act(
            self):
        """What a failing preflight must not have done.

        The two task documents exist -- the validator opens them, so they are
        written first and the refusal says so. Nothing else may: no resolved
        selections, no composed target, and no Work in the Authority.
        """
        import prepare_two_jobs
        from baton_v12.authority import Authority
        root, uuid = self.bootstrapped("two-jobs-refused-preflight")
        places = prepare_two_jobs.layout(os.path.realpath(root))
        original = prepare_two_jobs._composer                 # noqa: SLF001

        class Refused:
            returncode = 2
            stdout = ""
            stderr = "refused: the pinned product will not have this packet"

        prepare_two_jobs._composer = (                        # noqa: SLF001
            lambda arguments: Refused() if "--check" in arguments
            else original(arguments))
        try:
            with self.assertRaises(
                    prepare_two_jobs.PreparationRefusal) as caught:
                self.commanded(root)
        finally:
            prepare_two_jobs._composer = original             # noqa: SLF001
        self.assertIn("will not have this packet", str(caught.exception))
        self.assertIn(places["tasks"], str(caught.exception))
        # THE TASK DOCUMENTS, and nothing else.
        self.assertEqual(sorted(os.listdir(places["tasks"])),
                         ["job-a.json", "job-b.json"])
        self.assertFalse(os.path.exists(places["selections"]))
        self.assertFalse(os.path.exists(places["run"]))
        authority = Authority.open(places["authority_store"],
                                   expected_authority_uuid=uuid)
        try:
            for number in (1, 2):
                with self.subTest(work=number):
                    with self.assertRaises(Exception):
                        authority.project_work(f"{uuid[:8]}-W{number}")
        finally:
            authority.dispose()

    def test_an_ABSENT_workspace_store_is_what_refused_the_live_startup(self):
        """The boundary the owner met on 2026-09-23, made deterministic.

        "the live supervisor refused in `worker_preflight` because its
        configured `run/workspaces` directory did not exist. Preparation
        declares that path but does not provision it."
        `workspaces.check_workspace_storage` asks with `lstat`, so an absent
        name is a refusal -- and the packet named four owned roots and created
        none of them.

        This drives the product's own check over the composed path before and
        after provisioning, which is the same judgment `worker_preflight`
        makes, without opening a store or starting anything.
        """
        import prepare_two_jobs
        from baton_v12.contracts import ContractRefusal
        from baton_v12.worker_manager import workspaces
        root, _uuid = self.bootstrapped("two-jobs-provisioned")
        places = prepare_two_jobs.layout(os.path.realpath(root))
        # BEFORE: the path the composed deployment names is not there.
        self.assertFalse(os.path.lexists(places["workspace_storage"]))
        with self.assertRaises(ContractRefusal) as caught:
            workspaces.check_workspace_storage(places["workspace_storage"])
        self.assertIn("not a directory this manager can see",
                      str(caught.exception))
        # AND AFTER the preparation ran, every owned root exists and the
        # product holds the one it refuses most sharply.
        _status, receipt, _text = self.commanded(root)
        for name in prepare_two_jobs.PROVISIONED:
            with self.subTest(root=name):
                self.assertTrue(os.path.isdir(places[name]), places[name])
                self.assertIn(name, receipt["provisioned"])
        self.assertEqual(
            workspaces.check_workspace_storage(places["workspace_storage"]),
            places["workspace_storage"])
        # AND THE DEPLOYMENT NAMES THE ONES THAT WERE PROVISIONED, so this is
        # not a directory tree beside the one the manager will look at.
        with open(places["deployment"], encoding="utf-8") as handle:
            composed = json.load(handle)
        for worker in composed["workers"]:
            with self.subTest(worker=worker["worker_id"]):
                self.assertEqual(worker["deployment"]["workspace_storage"],
                                 places["workspace_storage"])

    def test_an_EXISTING_TARGET_is_refused_before_any_effect(self):
        """Even an empty one, because the composer is create-only about it.

        Review 2026-09-23T20:52:13Z: the preflight looked for
        `deployment.json` or `submission.json`, so an empty directory passed
        it and the composer refused afterwards -- after the task documents,
        the selections and the Authority acts.
        """
        import prepare_two_jobs
        root, _uuid = self.bootstrapped("two-jobs-occupied")
        places = prepare_two_jobs.layout(os.path.realpath(root))
        os.makedirs(places["run"], exist_ok=True)
        with self.assertRaises(prepare_two_jobs.PreparationRefusal) as caught:
            self.commanded(root)
        self.assertIn("create-only about the target path",
                      str(caught.exception))
        # AND NOTHING WAS WRITTEN OR ACTED ON.
        self.assertEqual(sorted(os.listdir(places["run"])), [])
        self.assertFalse(os.path.exists(places["tasks"]))
        self.assertFalse(os.path.exists(places["selections"]))

    def test_the_PREPARATION_COMMAND_runs_end_to_end(self):
        """`main` itself, through the real composer, not its helpers.

        Review 2026-09-23T20:34:15Z: "The nine new tests call
        resolved/prepare helpers, not preparation main through its composer
        and the printed setup." They did, and that is how a recipe that could
        not compose reached a handoff. This drives the command.
        """
        import prepare_two_jobs
        root, uuid = self.bootstrapped()
        status, receipt, _text = self.commanded(root)
        self.assertEqual(status, 0)
        self.assertEqual(receipt["authority_uuid"], uuid)
        places = prepare_two_jobs.layout(os.path.realpath(root))
        # THE DOCUMENTS EXIST WHERE THE RECEIPT SAYS THEY DO.
        for name in ("deployment", "submission", "selections"):
            with self.subTest(emitted=name):
                self.assertTrue(os.path.isfile(places[name]), places[name])
        for job_id in ("job-a", "job-b"):
            with self.subTest(task=job_id):
                self.assertTrue(os.path.isfile(
                    os.path.join(places["tasks"], f"{job_id}.json")))
        self.assertEqual(receipt["tasks_touch"],
                         {"job-a": ["greet_a.py"], "job-b": ["greet_b.py"]})
        made = [one["job_id"] for one in receipt["prepared"]["jobs"]]
        self.assertEqual(made, ["job-a", "job-b"])

    def test_the_printed_OPERANDS_name_the_files_this_run_emitted(self):
        """The reconciliation review 2026-09-23T20:34:15Z asked for.

        Three documents named three different layouts, and no reading of
        `<run root>` could make them agree. The receipt now prints the exact
        operands the next two steps take, from the places this run used.
        """
        import prepare_two_jobs
        root, uuid = self.bootstrapped()
        _status, receipt, _text = self.commanded(root)
        places = prepare_two_jobs.layout(os.path.realpath(root))
        serve = dict(zip(receipt["serve_command"][::2],
                         receipt["serve_command"][1::2]))
        self.assertEqual(serve["--deployment"], places["deployment"])
        self.assertEqual(serve["--submission"], places["submission"])
        self.assertEqual(serve["--job-store"], places["job_store"])
        self.assertEqual(serve["--control-store"], places["control_store"])
        for flag in ("--deployment", "--submission"):
            with self.subTest(exists=flag):
                self.assertTrue(os.path.isfile(serve[flag]))
        # AND THE COMPOSED DOCUMENTS NAME THE SAME INSTANCE the serve command
        # opens -- the disagreement that made the old recipe unusable. The
        # deployment carries the integration store and the state root; both
        # must sit under the run root this command was given.
        with open(places["deployment"], encoding="utf-8") as handle:
            composed = json.load(handle)
        root = os.path.realpath(root) + os.sep
        for name in ("integration_store", "state_root", "authority_store"):
            with self.subTest(member=name):
                self.assertTrue(composed[name].startswith(root),
                                f"{name} is {composed[name]!r}")
        self.assertEqual(composed["integration_store"],
                         places["integration_store"])
        self.assertEqual(composed["authority_store"],
                         places["authority_store"])
        self.assertTrue(serve["--job-store"].startswith(root))
        status = dict(zip(receipt["status_command"][::2],
                          receipt["status_command"][1::2]))
        self.assertEqual(status["--store"], places["job_store"])
        self.assertEqual(status["--authority-uuid"], uuid)
        self.assertEqual(receipt["status_command"][-2:],
                         ["--control", places["control_store"]])

    def test_an_exact_repeat_REPLAYS_and_changes_nothing(self):
        """Same operands, twice. The composer is create-only, so the second
        run must refuse BEFORE it has touched anything rather than after."""
        import prepare_two_jobs
        root, _uuid = self.bootstrapped()
        _status, _receipt, _text = self.commanded(root)
        places = prepare_two_jobs.layout(os.path.realpath(root))
        before = {name: open(places[name], "rb").read()
                  for name in ("selections", "deployment", "submission")}
        with self.assertRaises(prepare_two_jobs.PreparationRefusal) as caught:
            self.commanded(root)
        self.assertIn("create-only", str(caught.exception))
        for name, raw in sorted(before.items()):
            with self.subTest(unchanged=name):
                self.assertEqual(open(places[name], "rb").read(), raw)

    def test_a_CHANGED_operand_is_refused_with_the_old_bytes_intact(self):
        """A different base is a different packet, not an update."""
        import prepare_two_jobs
        root, _uuid = self.bootstrapped()
        self.commanded(root)
        places = prepare_two_jobs.layout(os.path.realpath(root))
        before = {name: open(places[name], "rb").read()
                  for name in ("selections", "deployment", "submission")}
        with self.assertRaises(prepare_two_jobs.PreparationRefusal) as caught:
            self.commanded(root, base="b" * 40)
        self.assertIn("would change them", str(caught.exception))
        for name, raw in sorted(before.items()):
            with self.subTest(unchanged=name):
                self.assertEqual(open(places[name], "rb").read(), raw)

    def test_a_root_INSIDE_the_checkout_boundary_is_refused_first(self):
        """The refusal review 2026-09-23T20:34:15Z reproduced, moved forward.

        The validator refused this shape at composition, after task files and
        Authority acts. It is refused here, before anything.
        """
        import prepare_two_jobs
        for boundary in prepare_two_jobs.BOUNDARIES:
            with self.subTest(boundary=boundary):
                with self.assertRaises(
                        prepare_two_jobs.PreparationRefusal) as caught:
                    prepare_two_jobs.fresh(
                        os.path.join(boundary, "two-jobs-probe"),
                        "two-jobs-probe")
                self.assertIn("belongs outside the working tree",
                              str(caught.exception))

    def test_a_SYMLINK_into_a_consumed_root_is_refused(self):
        """One `ln -s` walked around every lexical refusal."""
        import prepare_two_jobs
        held = os.path.join(self.root, "single-implementation-244216")
        os.makedirs(held, exist_ok=True)
        alias = os.path.join(self.root, "two-jobs-fresh-alias")
        if not os.path.islink(alias):
            os.symlink(held, alias)
        with self.assertRaises(prepare_two_jobs.PreparationRefusal) as caught:
            prepare_two_jobs.fresh(alias, "two-jobs-fresh-alias")
        self.assertIn("single-implementation-244216", str(caught.exception))

    def test_the_shared_task_speaks_to_BOTH_roles(self):
        """One input identity, and the reviewer is not told to write code.

        `two_jobs.worker_document` deliberately gives both roles the same task
        and the same input identity -- that is the supported shape and it is
        not weakened here. What was wrong was the TEXT: it told its consumer
        to create the file and that judging was somebody else's stage, which
        is implementation-only instructions delivered to a reviewer.
        """
        _module, document, _tasks = self.derived()
        for job in document["arrangement"]["jobs"]:
            with self.subTest(job=job["job_id"]):
                with open(job["task_document"], encoding="utf-8") as handle:
                    said = json.load(handle)["instructions"]
                self.assertIn("IF YOUR STAGE IS THE IMPLEMENTATION", said)
                self.assertIn("IF YOUR STAGE IS THE REVIEW", said)
                self.assertIn("READ-ONLY", said)
                self.assertIn("All three are valid results", said)
                # AND THE INPUT IDENTITY IS STILL SHARED, which is the
                # supported shape rather than a thing to route around.
                self.assertEqual(job["implementation_input_manifest"],
                                 job["review_input_manifest"])

    def test_every_operand_the_COMPOSER_asks_for_is_derived(self):
        """No `<OWNER>` survives, and no operand is missing.

        The template asked twelve questions. This asserts the derived document
        answers all of them in the composer's own vocabulary rather than in a
        shape that merely looks complete.
        """
        _module, document, _tasks = self.derived()
        arrangement = document["arrangement"]
        self.assertEqual(
            sorted(two_jobs.INSTANCE_OPERANDS),
            sorted(one for one in arrangement["instance"]
                   if one in two_jobs.INSTANCE_OPERANDS))
        for name in sorted(two_jobs.INSTANCE_OPERANDS):
            with self.subTest(instance=name):
                self.assertIn(name, arrangement["instance"])
        for job in arrangement["jobs"]:
            for name in sorted(two_jobs.JOB_OPERANDS):
                with self.subTest(job=job["job_id"], operand=name):
                    self.assertIn(name, job)
        held = json.dumps(document)
        self.assertNotIn("<OWNER", held)

    def test_the_submission_ASKS_FOR_the_ceilings_this_packet_declares(self):
        """The live boundary of 2026-09-24T00:53Z, made deterministic.

        Owner 2026-09-24T00:58Z: the run reported `provider_turn` limits of
        3600 seconds from compatibility defaults rather than the selected 180.
        The launch document says why in one member -- `requested: {}` -- so
        this packet declared 180 in `LIMITS`, printed it in ADOPTION's table,
        and asked the manager for nothing.

        This asserts the operand, and then asks the PRODUCT what a Job
        submitted with it resolves to, because a member present and a ceiling
        effective are different facts.
        """
        from baton_v12.job_manager import documents, submit
        from baton_v12.job_manager import execution_limits, submission
        # THIS PACKET'S OWN SUBMISSION, not the fixture's accepted one. A first
        # version of this case asserted against `both_jobs()`, which is
        # W130224's document and carries no ceiling of ours -- it was checking
        # somebody else's submission for this packet's operand.
        # THE RESOLVED OPERANDS, which is what `submission` consumes -- the
        # arranged document's Jobs carry the composed shape, not the input
        # manifests `job_input_identity` needs.
        import prepare_two_jobs
        _module, resolved, _tasks = self.derived()
        jobs = resolved["arrangement"]["jobs"]
        del prepare_two_jobs
        document = two_jobs.held_submission(two_jobs.submission(
            jobs, submission_id="limits-witness",
            policy_digest=resolved["arrangement"]["instance"][
                "policy_digest"]))
        self.assertEqual(document["schema"], "baton.v12.job-submission/2")
        for job in document["jobs"]:
            with self.subTest(job=job["job_id"]):
                self.assertEqual(
                    job[documents.JOB_LIMIT_MEMBER],
                    {"provider_turn_seconds": 180,
                     "verification_command_seconds": 180})
        # AND THE EFFECTIVE CEILING, read through the product after a submit
        # of THIS document -- a member present and a ceiling effective are
        # different facts, and the live run had the second without the first.
        job_store, _control, _composed = self.serving_two(**self.traversing())
        submit(job_store, document)
        for one in document["jobs"]:
            with self.subTest(resolved=one["job_id"]):
                asked = submission.execution_limits_of(job_store,
                                                       one["job_id"])
                effective = execution_limits.resolved(
                    asked["requested"], asked["compatibility_generation"])
                self.assertEqual(
                    effective["boundaries"]["provider_turn"]["seconds"], 180)
                self.assertEqual(
                    effective["boundaries"]["provider_turn"]["origin"], "job")

    def test_each_input_digest_is_the_products_own_identity(self):
        """Derived from the manifest rather than copied beside it.

        A digest filled in by hand is a digest that disagrees with the
        manifest the next time either changes; W247941 already met that once,
        when a MANIFEST digest stood where `job_input_identity` belongs and no
        configured worker could serve any stage.
        """
        from baton_v12.contracts import job_input_identity
        _module, document, _tasks = self.derived()
        for job in document["arrangement"]["jobs"]:
            with self.subTest(job=job["job_id"]):
                self.assertEqual(
                    job["input_digest"],
                    job_input_identity(job["implementation_input_manifest"]))

    def test_the_task_bytes_are_the_manifests_own_human_contract(self):
        """`single_worker._held` compares them, so they are derived
        together."""
        module, document, tasks = self.derived()
        for job in document["arrangement"]["jobs"]:
            with self.subTest(job=job["job_id"]):
                contract = job["implementation_input_manifest"][
                    "human_contract"]
                raw = tasks[job["job_id"]]["raw"]
                self.assertEqual(contract["bytes"], len(raw))
                self.assertEqual(contract["content_digest"],
                                 module.digest_of_bytes(raw))
                with open(job["task_document"], "rb") as handle:
                    self.assertEqual(handle.read(), raw)

    def test_the_two_tasks_touch_DISJOINT_paths(self):
        """This gate's own limit, checked rather than trusted."""
        module, _document, tasks = self.derived()
        touched = module.disjoint(tasks)
        self.assertEqual(touched, {"job-a": ["greet_a.py"],
                                   "job-b": ["greet_b.py"]})
        # AND THE CHECK REFUSES when they are not, which is what makes the
        # assertion above worth making.
        module.TASKS["job-b"]["path"] = module.TASKS["job-a"]["path"]
        try:
            with self.assertRaises(module.PreparationRefusal) as caught:
                module.disjoint(tasks)
        finally:
            module.TASKS["job-b"]["path"] = "greet_b.py"
        self.assertIn("one contended change", str(caught.exception))

    def test_a_CONSUMED_instance_is_refused_before_anything_is_written(self):
        """Every root this campaign spent holds other work and is evidence."""
        module, _document, _tasks = self.derived()
        for older in module.CONSUMED:
            with self.subTest(consumed=older):
                with self.assertRaises(module.PreparationRefusal):
                    module.fresh(f"/home/sl/baton-runs/{older}", older)
                with self.assertRaises(module.PreparationRefusal):
                    module.fresh(f"/home/sl/baton-runs/{older}/successor",
                                 "successor")

    def test_a_root_that_does_not_name_its_own_run_is_refused(self):
        """And a root that does name it, OUTSIDE the boundaries, is accepted.

        The accepted path moved: `/home/sl/baton-runs/...` is now refused for
        the boundary before this check is even reached, which is the right
        order and is asserted separately.
        """
        module, _document, _tasks = self.derived()
        with self.assertRaises(module.PreparationRefusal):
            module.fresh(os.path.join(self.root, "somewhere-else"),
                         "two-jobs-1")
        held = os.path.join(self.root, "two-jobs-1")
        os.makedirs(held, exist_ok=True)
        self.assertEqual(module.fresh(held, "two-jobs-1"),
                         os.path.realpath(held))

    def test_the_AUTHORITY_acts_register_four_identities_and_both_routes(self):
        """Through the supported API, on this fixture's disposable Authority.

        Two Works, both implementers on `impl`, both reviewers on `rview`, the
        integrator on `integration` -- the review worker passes its answered
        assignment there -- the four scoped grants per Work, and the canonical
        target.
        """
        from baton_v12.authority import Authority
        # WORKS THIS FIXTURE HAS NOT MINTED. `create_work` refuses a Work that
        # already exists under somebody else's act -- measured, not assumed:
        # pointing this at the fixture's own `-W1` answered "Work
        # '0000000a-W1' already exists". Replay is same-identity replay, not
        # adoption of whatever is there, and the case below drives it twice to
        # show which.
        prefix = self.config["authority_uuid"][:8]
        module, document, _tasks = self.derived(
            work_ids={"job-a": f"{prefix}-W41", "job-b": f"{prefix}-W42"})
        authority = Authority.open(
            self.authority_path,
            expected_authority_uuid=self.config["authority_uuid"])
        try:
            prepared = module.prepare(authority, document, base=self.base,
                                      operation_prefix="w247941-witness")
            # AND AGAIN, under the same act identity: the same two Works and
            # the same scopes, rather than a refusal or a second pair.
            again = module.prepare(authority, document, base=self.base,
                                   operation_prefix="w247941-witness")
        finally:
            authority.dispose()
        self.assertEqual(again["jobs"], prepared["jobs"])
        self.assertEqual([one["job_id"] for one in prepared["jobs"]],
                         ["job-a", "job-b"])
        self.assertEqual(prepared["canonical_target"], self.base)
        self.assertEqual(prepared["route_handlers"]["integration"],
                         "baton.merge")
        for one in prepared["jobs"]:
            with self.subTest(job=one["job_id"]):
                self.assertTrue(one["scope"])
                self.assertEqual(
                    sorted(two["capability"] for two in one["granted"]),
                    ["approve", "integrate", "review", "verify"])
                self.assertEqual(sorted(one["route_handlers"]),
                                 ["impl", "rview"])

    def test_the_four_participants_are_four_DISTINCT_identities(self):
        """Two Jobs sharing a producer or a reviewer are not two Jobs."""
        module, document, _tasks = self.derived()
        del module
        named = []
        for job in document["arrangement"]["jobs"]:
            named += [job["producer_participant"], job["reviewer_participant"]]
        self.assertEqual(len(set(named)), 4, named)

    def test_the_derivation_carries_no_credential_BYTES(self):
        """A reference and a registry path, and nothing that is a secret."""
        _module, document, _tasks = self.derived()
        instance = document["arrangement"]["instance"]
        self.assertEqual(sorted(instance["credential_profile"]), ["claude"])
        self.assertEqual(instance["credential_profile"]["claude"],
                         {"provider": "operator-file",
                          "reference": "w202663-development"})
        self.assertEqual(instance["credential_slots"], ["claude"])
        for forbidden in ("token", "secret", "api_key", "apiKey", "password"):
            with self.subTest(absent=forbidden):
                self.assertNotIn(forbidden, json.dumps(document))


def baseline_interrupted():
    import two_job_supervisor
    return two_job_supervisor.baseline.SupervisorInterrupted


def load_tests(loader, standard, pattern):                   # noqa: ARG001
    """Only this module's own cases.

    The fixture is a real accepted test class, so loading it normally would
    re-run W130224's whole suite under this dossier's name and present another
    Job's accepted evidence as this one's.
    """
    suite = unittest.TestSuite()
    for name, value in sorted(globals().items()):
        if isinstance(value, type) and issubclass(value, unittest.TestCase) \
                and value.__module__ == __name__ \
                and name not in ("ArrangedCase",):
            for one in loader.getTestCaseNames(value):
                if one in value.__dict__ or any(
                        one in base.__dict__ for base in value.__mro__
                        if base.__module__ == __name__):
                    suite.addTest(value(one))
    return suite


if __name__ == "__main__":                                   # pragma: no cover
    unittest.main()
