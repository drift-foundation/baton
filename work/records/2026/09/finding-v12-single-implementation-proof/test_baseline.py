"""Deterministic verification of the single-implementation baseline (W239528).

WHAT IS REAL HERE. `baseline.supervise` itself, the owner acts in
`baseline.prepare`, the `AdmissionGate` the manager actually calls, the real
candidate qualification grant guard, the ordinary manager composition, the
worker launch, `claude_agent.ClaudeAgent` performing the turn over the mounted
namespaces, REAL version control on a real private line, custody, the ending
driver's seal/intake/retention/publication/freeze/cleanup, and the manager's own
committed cleanup records. The engine and the provider subprocess are the two
accepted deterministic seams `ComposedOneJobCase` already names; version control
is not simulated at all, which is what lets the attribution cases below mean
something.

WHAT IS NOT CLAIMED. No container, no image execution, no live provider, no
network and no credential. This establishes the BASELINE's lifetime, cap, stop,
cleanup accounting, proposal attribution and refusals -- not that the production
CLI behaves this way, which is the remaining question
`PROVIDER-QUESTION-239528.md` states and the owner's bounded command exists to
ask.

THE `sleep` SEAM IS WHERE THE WORKER TURN HAPPENS, and that is deliberate: the
composed deployment has no daemon to run a container, so the one boundary this
build cannot cross is driven from the loop's own injected wait. `supervise` is
otherwise entered exactly as the live command enters it.

THE TWO CASES THIS FILE EXISTS FOR are `TheProposalIsTheAdaptersOwnAccount`.
W236087's live run retained no proposal because its provider committed its own
work and `ClaudeAgent._unmoved` refused to adopt a history it did not write.
One case here proves the positive shape -- adapter-authored, one commit on the
declared base -- and the other REPRODUCES the live failure through the same
real code and asserts that this run reports it rather than settling.
"""
import json
import os
from pathlib import Path
import subprocess
import unittest
from unittest import mock

from baton_v12.contracts import ContractRefusal, job_input_identity
from baton_v12.job_manager import execution_limits
from baton_v12.worker_manager.workspaces import configure_workspace_storage
from tests.job_manager import fixtures
from tests.manager.test_claude_context import ManagedSessionResume
from tools import stage_execution

import baseline

HERE = Path(__file__).resolve().parent
# THE SELECTED CHANGE, and it is the final target because this Job has no
# correction in it. W236087 needed a first proposal a reviewer would send back;
# this one needs a first proposal that is simply right.
IMPLEMENTATION_EDITS = {"harness.py": "print('READY')\n"}
TURN_SECONDS = 180


class BaselineCase(ManagedSessionResume):
    """One Job, ONE implementation stage, driven by the baseline supervisor."""

    RUN = "single-implementation-239528-deterministic"

    def setUp(self):
        super().setUp()
        # ONE STAGE. `_terminal` requires EVERY configured stage to complete,
        # so a review stage left in the submission would make this run's own
        # stop condition unreachable -- and a review container is W239533's
        # workload, not a smaller part of this one.
        #
        # AND `/2`, CARRYING THE PROVIDER-TURN CEILING: the Job is where that
        # number is a bound rather than a number in a manifest.
        self.submission = {
            "schema": "baton.v12.job-submission/2",
            "submission_id": "sub-1",
            "jobs": [dict(
                fixtures.job(
                    "job-a", input_digest=job_input_identity(self.manifest),
                    policy_digest=fixtures.POLICY_DIGEST,
                    stages=[fixtures.stage("implementation", self.work)]),
                execution_limits={"provider_turn_seconds": TURN_SECONDS})]}
        self.turned = set()
        self.packet_root = Path(self.root) / "packet"
        self.packet_root.mkdir()
        self.packet = self.written_packet()

    # -- the packet, over this composition's own real paths ------------------

    def written_packet(self, **overrides):
        configuration = self.composed_document(line_declared_base=self.base)
        places = {}
        for name, document in (("deployment.json", configuration),
                               ("submission.json", self.submission),
                               ("profile.json", self.context_profile)):
            place = self.packet_root / name
            place.write_text(json.dumps(document, sort_keys=True, indent=2),
                             encoding="utf-8")
            places[name] = str(place)
        packet = {
            "schema": baseline.PACKET_SCHEMA,
            "run_id": self.RUN, "work": "W239528", "claim": 239653,
            "note": "one deterministic managed implementation under this grant",
            "worker_image": {
                "reference": "baton-v12-claude-worker:deterministic",
                "config_digest": "sha256:" + "0" * 64,
                "worker_files": {"opt/baton/claude_agent.py": "0" * 64}},
            "manager_runtime": {
                "path": str(self.packet_root / "runtime"),
                "executable_sha256": self.written_runtime(),
                "build_commit": "c97fe766000000000000000000000000000000ab"},
            "manager_source": self.written_source(),
            "supervisor": {
                "path": str(HERE / "baseline.py"),
                "sha256": self.digest_of(str(HERE / "baseline.py"))},
            # THE TREE THE CODE LIVES IN, bound rather than inferred. This
            # fixture's stores are siblings of it, which is the ordinary
            # relocated-source shape.
            "code_boundary": str(self.packet_root / "manager-source"),
            "deployment": {
                "config_path": places["deployment.json"],
                "config_sha256": self.digest_of(places["deployment.json"]),
                "job_store": str(Path(self.root) / "jobs.sqlite3"),
                "control_store": str(Path(self.root) / "control.sqlite3"),
                "authority_store": str(self.authority_path),
                "authority_uuid": self.config["authority_uuid"],
                "state_root": str(self.root)},
            "context": {
                "storage_path": str(self.context_root),
                "excluded_roots": [str(self.source), str(self.storage)],
                "runtime_uid": os.getuid(),
                "profile_path": places["profile.json"],
                "profile_sha256": self.digest_of(places["profile.json"]),
                "profile_digest": self.context_digest,
                "job_id": self.submission["jobs"][0]["job_id"]},
            "submission": {
                "path": places["submission.json"],
                "sha256": self.digest_of(places["submission.json"]),
                "job_id": self.submission["jobs"][0]["job_id"]},
            "fixture": {
                "source_root": str(self.source),
                "files": {"harness.py": self.digest_of(
                    os.path.join(self.source, "harness.py"))}},
            "bounds": {"turn_seconds": TURN_SECONDS, "total_seconds": 900,
                       "cleanup_seconds": 60, "implementer_invocations": 1,
                       "retry": False},
            "outcome_path": str(self.packet_root / "outcome.json")}
        packet.update(overrides)
        place = self.packet_root / "PACKET.json"
        place.write_text(json.dumps(packet, sort_keys=True, indent=2),
                         encoding="utf-8")
        self.packet_path = str(place)
        return packet

    def written_runtime(self):
        """A stand-in for the installed runtime's own executable.

        The frozen executable is the INSTALLATION artifact and is never what
        supervises. The packet still binds it, and this case still proves that
        a moved byte refuses -- which one file proves exactly as well as a
        5 MiB one.
        """
        place = self.packet_root / "runtime"
        place.mkdir(exist_ok=True)
        (place / "baton-v12-stack").write_bytes(b"#!/bin/sh\nexit 0\n")
        return self.digest_of(str(place / "baton-v12-stack"))

    def written_source(self):
        """A REAL importable manager-source tree, bound file by file.

        The production packet binds `baton_v12` and `tools`; this binds a small
        package with the same property -- it is on `sys.path`, it is really
        imported, and every one of its files is hashed -- so the location and
        digest checks are exercised rather than described.
        """
        place = self.packet_root / "manager-source"
        (place / "boundpkg").mkdir(parents=True, exist_ok=True)
        (place / "boundpkg" / "__init__.py").write_text(
            "VERSION = 'bound'\n", encoding="utf-8")
        (place / "boundpkg" / "inner.py").write_text(
            "MARK = 'inner'\n", encoding="utf-8")
        files = {}
        for base, _dirs, names in os.walk(place):
            for name in sorted(names):
                whole = os.path.join(base, name)
                files[os.path.relpath(whole, place)] = self.digest_of(whole)
        return {"path": str(place), "packages": ["boundpkg"],
                "file_count": len(files), "files": files}

    @staticmethod
    def digest_of(path):
        import hashlib

        with open(path, "rb") as handle:
            return hashlib.sha256(handle.read()).hexdigest()

    # -- composition, with the supervisor performing the owner acts ----------

    def serving(self, *, packet=None, **members):
        """The accepted composition, with `baseline.prepare` in place of the
        owner acts the fixture otherwise performs by hand.

        This is the point of the case: the storage, the certified profile and
        the one qualification grant are the SUPERVISOR's, committed through the
        same public functions, and the admission boundary then either accepts
        them or does not.
        """
        self.engine = self.quiescing()
        job, control = self.stores("baseline-serving")
        configure_workspace_storage(control, self.storage)
        # THE GRANT IS MINTED FOR ONE JOB IDENTITY. `authorize_qualification_run`
        # binds `packet["context"]["job_id"]`, so preparing one packet and then
        # supervising another leaves the opening admission with no grant for
        # the Job it is admitting. The two must be the same document.
        baseline.prepare(control, self.packet if packet is None else packet)
        composed = stage_execution.operations_from(
            self.composed_document(line_declared_base=self.base, **members),
            job, control, engine_run=self.engine,
            credential_provider=lambda provider, reference: self.secret,
            clock=lambda: fixtures.NOW, checkout=self.checkout)
        self.addCleanup(composed.close)
        self._composed = composed
        return job, control, composed

    # -- the injected wait, which is where a container would have run --------

    def driver(self, job, control, composed, *, edits=None, expect=0):
        def wait(seconds):
            del seconds
            if self.states(job, composed).get("implementation") != "waiting":
                return None
            return self.run_implementation(control, composed, edits=edits,
                                           expect=expect)
        return wait

    def pending(self, composed, role):
        held = [one for one in
                sorted(self.worker_of(composed, role).stage._prepared)
                if one not in self.turned]
        return held[0] if held else None

    def run_implementation(self, control, composed, *, edits=None, expect=0):
        attempt = self.pending(composed, "implementation")
        if attempt is None:
            return None
        self.turned.add(attempt)
        status = self.turn(control, "implementation", attempt,
                           self.mounted(composed, "implementation", attempt),
                           edits=dict(edits or IMPLEMENTATION_EDITS))
        if expect is not None:
            self.assertEqual(status, expect)
        return status

    # -- one bounded supervised run ------------------------------------------

    def supervised(self, *, packet=None, **operands):
        job, control, composed = self.serving(packet=packet)
        ticks = iter(range(0, 100000))

        def monotonic():
            return float(next(ticks))

        self._job = job
        return composed, baseline.supervise(
            job, control, composed, packet or self.packet,
            clock=lambda: fixtures.NOW,
            sleep=self.driver(job, control, composed, **operands),
            monotonic=monotonic), job, control

    def vcs_at(self, place, *arguments):
        """The FIXTURE's own history at an arbitrary checkout, under the
        fixture's own identity.

        Deliberately NOT the adapter's identity: the whole point of the
        attribution cases is that the adapter's authorship is distinguishable
        from anybody else's, and lending it this name would erase that.
        """
        argv = ["git", "-C", place] + list(arguments)
        answer = subprocess.run(
            argv, capture_output=True, text=True, timeout=300,
            env=dict(self.environment(), GIT_AUTHOR_NAME="Baton Test",
                     GIT_AUTHOR_EMAIL="test@baton.invalid",
                     GIT_COMMITTER_NAME="Baton Test",
                     GIT_COMMITTER_EMAIL="test@baton.invalid"))
        self.assertEqual(answer.returncode, 0,
                         f"{argv} failed: {answer.stderr}")
        return answer.stdout


class TheBaselineDrivesOneBoundedImplementation(BaselineCase):

    def test_it_settles_after_one_turn_and_proves_the_cleanup(self):
        composed, outcome, job, control = self.supervised()
        self.assertEqual(outcome["state"], "settled", outcome["held_because"])
        self.assertEqual(outcome["stopped"], "completed")
        self.assertEqual(outcome["stage_states"],
                         {"implementation": "completed"})
        self.assertEqual(outcome["retry"], False)
        self.assertEqual(outcome["outstanding_cleanup"], [])
        self.assertEqual(outcome["unexpected_attempts"], [])
        # ONE RUNTIME, which is the selected workload exactly.
        self.assertEqual(len(outcome["admitted_attempts"]), 1)
        for attempt, held in sorted(outcome["cleanup"].items()):
            with self.subTest(attempt=attempt):
                self.assertIn(held["cleanup"], baseline.POSITIVE_CLEANUP)
                self.assertEqual(held["state"], "absent")
        del composed, job, control

    def test_quiescence_is_not_counted_as_cleanup(self):
        """The FINDING's own words: "do not count ... quiescence as cleanup".

        A stopped container is not a removed one. What makes this run settle is
        a POSITIVE committed `runtime.destroy` read back from the journal, so
        this asserts the committed record rather than the execution axis.
        """
        _composed, outcome, _job, _control = self.supervised()
        self.assertTrue(outcome["cleanup"])
        for attempt, held in sorted(outcome["cleanup"].items()):
            with self.subTest(attempt=attempt):
                # A COMMITTED ENDING, and one the manager's own axis calls
                # positive. This deployment retains, so the ending is
                # `retained`; what matters is that it is a RECORD rather than
                # an observation that the container stopped.
                self.assertIn(held["cleanup"], baseline.POSITIVE_CLEANUP)
                # AND THE ENGINE'S OWN ABSENCE SENTENCE, not an inference from
                # a container having stopped.
                self.assertEqual(held["state"], "absent")
                self.assertIn("does not exist", held["why"])

    def test_the_declared_per_turn_ceiling_is_the_jobs_own(self):
        _composed, outcome, _job, _control = self.supervised()
        self.assertEqual(outcome["provider_turn"]["seconds"], TURN_SECONDS)
        self.assertEqual(outcome["provider_turn"]["origin"],
                         execution_limits.JOB)
        self.assertEqual(outcome["provider_turn"]["setting"],
                         "provider_turn_seconds")

    def test_the_gate_counted_exactly_one_invocation(self):
        _composed, outcome, _job, _control = self.supervised()
        self.assertEqual(outcome["admissions"], {"implementation": 1})
        self.assertEqual(outcome["gate_refusals"], [])

    def test_one_context_was_opened_and_none_restored(self):
        """`restore` is the resume Job's mode; a baseline that resumed
        something did not establish a baseline."""
        _composed, outcome, _job, _control = self.supervised()
        workload = outcome["workload"]
        self.assertEqual(workload["shortfalls"], [])
        self.assertEqual(workload["modes"], ["open"])
        self.assertEqual(workload["generations"], [0])
        self.assertEqual(len(workload["conversations"]), 1)

    def test_the_provider_was_called_exactly_once(self):
        self.supervised()
        calls = [json.loads(line)
                 for line in self.calls.read_text().splitlines()]
        self.assertEqual([one["restored"] for one in calls], [False])

    def test_the_outcome_is_retained_where_the_packet_says(self):
        _composed, outcome, _job, _control = self.supervised()
        retained = json.loads(
            Path(self.packet["outcome_path"]).read_text(encoding="utf-8"))
        self.assertEqual(retained, outcome)
        self.assertEqual(retained["schema"], baseline.OUTCOME_SCHEMA)

    def test_the_outcome_carries_no_review_vocabulary(self):
        """A member this run does not carry is a decision, not an omission.

        `disposition` is deliberately NOT in this list. It is the MANAGER's
        closed vocabulary for how a worker turn ended -- `completed`,
        `unable`, `cancelled` -- and the outcome reports it precisely so a
        failed run says what happened where an operator can find it. What must
        not appear is a REVIEW's vocabulary: a verdict, a correction, or an
        acceptance this run has no reviewer to produce.
        """
        _composed, outcome, _job, _control = self.supervised()
        body = json.dumps(outcome)
        for word in ("verdict", "changes-requested", "accepted", "correction",
                     "plan-rejected"):
            with self.subTest(word=word):
                self.assertNotIn(word, body)
        # AND THE MANAGER'S OWN WORD IS PRESENT, reported rather than implied.
        self.assertEqual(
            [one["disposition"] for one in outcome["workload"]["dispositions"]],
            ["completed"])


class TheProposalIsTheAdaptersOwnAccount(BaselineCase):
    """The check W236087's live failure earned. See DIAGNOSIS-239528.md."""

    def test_the_retained_commit_is_authored_and_committed_by_the_adapter(self):
        _composed, outcome, _job, _control = self.supervised()
        self.assertEqual(outcome["workload"]["shortfalls"], [])
        held = outcome["workload"]["attribution"]
        self.assertEqual(len(held), 1)
        said = held[0]
        self.assertEqual(said["author"],
                         f"{baseline.COMMIT_NAME} <{baseline.COMMIT_EMAIL}>")
        self.assertEqual(said["committer"], said["author"])
        # EXACTLY ONE COMMIT ON THE DECLARED BASE. The adapter authors one per
        # turn, and a second parent or a longer history is a history it did not
        # write.
        self.assertEqual(said["parents"], [self.base])
        self.assertEqual(said["base"], self.base)
        self.assertNotEqual(said["head"], said["base"])

    def test_the_proposal_is_offered_against_the_deployments_own_target(self):
        _composed, outcome, _job, _control = self.supervised()
        proposals = outcome["workload"]["proposals"]
        self.assertEqual([one["base"] for one in proposals], [self.base])
        self.assertTrue(all(one["head"] != one["base"] for one in proposals))

    def test_the_adapters_commit_identity_is_the_one_this_program_checks(self):
        """Two copies of a constant that disagree would make the attribution
        check pass against a name nothing uses."""
        import claude_agent

        self.assertEqual(baseline.COMMIT_NAME, claude_agent.COMMIT_NAME)
        self.assertEqual(baseline.COMMIT_EMAIL, claude_agent.COMMIT_EMAIL)
        self.assertEqual(baseline.CLAIM_NAMESPACE,
                         claude_agent.CLAIM_NAMESPACE)

    def test_a_provider_that_commits_is_reported_and_never_settles(self):
        """W236087's live failure, reproduced through this same real code.

        The provider writes the edit AND commits it, exactly as the live one
        did. `ClaudeAgent._unmoved` refuses to adopt a history it did not
        write, the turn faults, nothing is published -- and this run reports
        that instead of settling on a proposal nobody could attribute.
        """
        original = self.provider

        def committing(**operands):
            inner = original(**operands)

            def run(argv, **options):
                answer = inner(argv, **options)
                if argv[0] == "claude" and "--model" in argv:
                    place = options["cwd"]
                    self.vcs_at(place, "add", "--all")
                    self.vcs_at(place, "commit", "-q", "--no-gpg-sign",
                                "--message", "the provider's own")
                return answer
            return run

        self.provider = committing
        _composed, outcome, _job, _control = self.supervised(expect=None)
        self.assertEqual(outcome["state"], "held")
        self.assertNotEqual(outcome["stopped"], "completed")
        self.assertEqual(outcome["workload"]["proposals"], [])
        self.assertEqual(outcome["workload"]["attribution"], [])
        # AND THE REPORT NAMES WHAT HAPPENED. A turn the adapter refused
        # froze no result at all, which is a different fact from a completed
        # turn whose proposal could not be read, and the outcome says which.
        self.assertTrue(
            any("froze no result at all" in one
                for one in outcome["workload"]["shortfalls"]),
            outcome["workload"]["shortfalls"])
        self.assertEqual(
            [one["disposition"]
             for one in outcome["workload"]["dispositions"]], [None])

    def test_an_attribution_naming_anybody_else_is_a_shortfall(self):
        """The check has to be able to FAIL on a real answer, not only on an
        unreadable one.

        `line_attribution` is the seam, so this substitutes an answer of the
        exact shape the real reader returns and carrying a foreign identity --
        which is precisely what the live run's reflog showed.
        """
        def foreign(control, *, attempt_id, generation, head, base):
            del control, generation
            return {"attempt_id": attempt_id, "line_id": "line-x",
                    "line_path": "/nowhere", "head": head, "base": base,
                    "author": "sl <sl@pushcoin.com>",
                    "committer": "sl <sl@pushcoin.com>", "parents": [base]}

        job, control, composed = self.serving()
        ticks = iter(range(0, 100000))
        _composed, outcome = composed, baseline.supervise(
            job, control, composed, self.packet,
            clock=lambda: fixtures.NOW,
            sleep=self.driver(job, control, composed),
            monotonic=lambda: float(next(ticks)), inspect=foreign)
        self.assertEqual(outcome["state"], "held")
        self.assertTrue(
            any("rather than to the worker adapter" in one
                for one in outcome["workload"]["shortfalls"]),
            outcome["workload"]["shortfalls"])

    def test_a_commit_with_a_foreign_parent_is_a_shortfall(self):
        def rebased(control, *, attempt_id, generation, head, base):
            del control, generation
            return {"attempt_id": attempt_id, "line_id": "line-x",
                    "line_path": "/nowhere", "head": head, "base": base,
                    "author": f"{baseline.COMMIT_NAME} "
                              f"<{baseline.COMMIT_EMAIL}>",
                    "committer": f"{baseline.COMMIT_NAME} "
                                 f"<{baseline.COMMIT_EMAIL}>",
                    "parents": [base, "b" * 40]}

        job, control, composed = self.serving()
        ticks = iter(range(0, 100000))
        outcome = baseline.supervise(
            job, control, composed, self.packet,
            clock=lambda: fixtures.NOW,
            sleep=self.driver(job, control, composed),
            monotonic=lambda: float(next(ticks)), inspect=rebased)
        self.assertEqual(outcome["state"], "held")
        self.assertTrue(
            any("authors one commit per turn" in one
                for one in outcome["workload"]["shortfalls"]),
            outcome["workload"]["shortfalls"])


class TheBaselineRefusesTheOtherJobsWorkload(unittest.TestCase):
    """The split is enforced by the code, not only described in a record."""

    def gate(self, operations, **caps):
        return baseline.AdmissionGate(
            operations, caps=caps or {"implementation": 1})

    def test_a_review_stage_is_refused_by_name_at_the_admission_gate(self):
        gate = self.gate(mock.Mock())
        with self.assertRaises(ContractRefusal) as caught:
            gate.admit({"kind": "review", "stage_id": "s2"}, {})
        self.assertIn("'review' stage reached the admission gate",
                      caught.exception.message)

    def test_a_second_implementation_is_refused_before_the_inner_admit(self):
        inner = mock.Mock()
        gate = self.gate(inner)
        gate.admit({"kind": "implementation", "stage_id": "s1"}, {})
        with self.assertRaises(ContractRefusal):
            gate.admit({"kind": "implementation", "stage_id": "s1"}, {})
        self.assertEqual(inner.admit.call_count, 1)
        self.assertEqual(gate.admissions["implementation"], 1)

    def test_a_closed_gate_refuses_admit_claim_and_launch(self):
        inner = mock.Mock()
        gate = self.gate(inner)
        gate.stop()
        for act, arguments in (("admit", ({"kind": "implementation"}, {})),
                               ("claim", ({"kind": "implementation"},)),
                               ("launch", ({"attempt_id": "a"}, {}))):
            with self.subTest(act=act):
                with self.assertRaises(ContractRefusal) as caught:
                    getattr(gate, act)(*arguments)
                self.assertIn("admission is closed", caught.exception.message)
        inner.admit.assert_not_called()
        inner.claim.assert_not_called()
        inner.launch.assert_not_called()

    def test_a_closed_gate_still_forwards_the_settling_acts(self):
        """The cleanup window drives endings; it just cannot start anything."""
        inner = mock.Mock()
        inner.canonical = True
        gate = self.gate(inner)
        gate.stop()
        gate.conclude({"attempt_id": "a"}, {})
        gate.refresh_runtime({"attempt_id": "a"})
        self.assertTrue(gate.canonical)
        inner.conclude.assert_called_once()
        inner.refresh_runtime.assert_called_once()

    def test_a_launch_that_faults_is_still_a_runtime_this_run_started(self):
        inner = mock.Mock()
        inner.launch.side_effect = RuntimeError("engine fault")
        gate = self.gate(inner)
        with self.assertRaises(RuntimeError):
            gate.launch({"attempt_id": "attempt-1", "stage_id": "s1"}, {})
        self.assertIn("attempt-1", gate.launched)

    def test_a_workload_that_also_ran_a_review_is_a_shortfall(self):
        """The gate refuses a foreign kind at admission; this is the same
        statement read back from what actually ran, so a review container that
        reached this Job by some other path is reported rather than left as an
        unexamined extra row."""
        shortfalls = []
        packet = {"bounds": {"implementer_invocations": 1},
                  "deployment": {"config_path": os.devnull}}
        with mock.patch.object(baseline, "_context_evidence",
                               return_value={"modes": ["open"],
                                             "conversations": ["c"],
                                             "generations": [0]}), \
                mock.patch.object(baseline, "_proposals",
                                  return_value={"proposals": [],
                                                "dispositions": []}), \
                mock.patch.object(baseline, "_attributions", return_value=[]):
            evidence = baseline._workload_evidence(
                None, None, packet,
                {"attempt-1": "implementation", "attempt-2": "review"},
                {}, inspect=None)
        shortfalls = evidence["shortfalls"]
        self.assertTrue(any("review and correction are separate Jobs" in one
                            for one in shortfalls), shortfalls)


class TheAccountingDistinguishesAbsenceFromAnUnreadableState(
        unittest.TestCase):
    """Only an ANSWERED absence may retire a runtime obligation."""

    def origins(self, answer, *, launched=()):
        uncertainty = []
        with mock.patch.object(baseline, "_runtime_facts",
                               return_value=answer):
            found = baseline._origin(None, "attempt-1", set(launched),
                                     uncertainty)
        return found[0], uncertainty

    def test_an_answered_absence_is_unallocated(self):
        origin, uncertainty = self.origins((None, baseline.ABSENT, "none"))
        self.assertEqual(origin, baseline.UNALLOCATED)
        self.assertEqual(uncertainty, [])

    def test_an_unreadable_state_stays_accountable(self):
        origin, uncertainty = self.origins(
            (None, baseline.UNREADABLE, "the read did not complete"))
        self.assertEqual(origin, baseline.FOREIGN)
        self.assertTrue(any("absence was not established" in one
                            for one in uncertainty), uncertainty)

    def test_a_locally_launched_attempt_is_started_without_a_read(self):
        uncertainty = []
        with mock.patch.object(baseline, "_runtime_facts") as reading:
            origin, _why = baseline._origin(None, "attempt-1", {"attempt-1"},
                                            uncertainty)
        self.assertEqual(origin, baseline.STARTED)
        reading.assert_not_called()

    def test_a_discovered_runtime_is_foreign(self):
        origin, _uncertainty = self.origins(
            ({"runtime_id": "runtime-1", "execution_runtime": "running"},
             None, None))
        self.assertEqual(origin, baseline.FOREIGN)

    def cleanups(self, record):
        from baton_v12.worker_manager import intake

        with mock.patch.object(baseline, "_retention_of",
                               return_value="sha256:" + "a" * 64), \
                mock.patch.object(intake, "cleanup_of", return_value=record):
            return baseline._cleanups(None, {}, {"attempt-1": None})

    def test_a_failed_destroy_is_a_committed_record_and_still_outstanding(self):
        """`failed` is committed too, and it is deliberately not positive: a
        destroy that settled `failed` is a runtime this manager could not prove
        gone."""
        self.assertNotIn("failed", baseline.POSITIVE_CLEANUP)
        found = self.cleanups({"cleanup": "failed", "state": "uncertain",
                               "why": "the engine refused"})
        self.assertEqual(found["outstanding"], ["attempt-1"])

    def test_no_committed_cleanup_is_outstanding_rather_than_clean(self):
        found = self.cleanups(None)
        self.assertEqual(found["outstanding"], ["attempt-1"])
        self.assertEqual(found["cleanup"]["attempt-1"]["why"],
                         "no committed cleanup")

    def test_both_positive_endings_settle(self):
        for ending in baseline.POSITIVE_CLEANUP:
            with self.subTest(ending=ending):
                found = self.cleanups({"cleanup": ending, "state": "absent",
                                       "why": None})
                self.assertEqual(found["outstanding"], [])


class OneRunAccountsForOneJobAndSaysSo(BaselineCase):
    """Review 2026-09-22T15:32:51Z R2, both halves.

    A fresh `run_id` is not a fresh Job identity, and an old Job's runtime is
    not part of this run's accounting. Both were prose before; both are checks
    now.
    """

    def foreign(self, job_id="job-somebody-else"):
        """A second Job recorded in THIS run's store, through the public API.

        Composed from this case's own manifest so it is servable by the same
        workers -- a Job nothing could serve would never reach the admission
        gate, and reaching it is the whole point.
        """
        from baton_v12.job_manager import submit

        return dict(self.submission, submission_id="sub-foreign", jobs=[dict(
            fixtures.job(job_id, input_digest=job_input_identity(self.manifest),
                         policy_digest=fixtures.POLICY_DIGEST,
                         stages=[fixtures.stage("implementation", self.work)]),
            execution_limits={"provider_turn_seconds": TURN_SECONDS})]), submit

    # -- the survey, which runs before any owner act ------------------------

    def test_a_job_identity_this_store_already_records_is_refused(self):
        job, _control, _composed = self.serving()
        document, submit = self.foreign(self.packet["submission"]["job_id"])
        submit(job, document)
        with self.assertRaises(baseline.SupervisorRefusal) as caught:
            baseline.survey(job, self.packet)
        said = str(caught.exception)
        self.assertIn("already records", said)
        self.assertIn("a run identity is not a Job identity", said)
        self.assertIn("no qualification grant was spent", said)

    def test_the_survey_names_every_other_job_and_disclaims_them(self):
        job, _control, _composed = self.serving()
        document, submit = self.foreign()
        submit(job, document)
        found = baseline.survey(job, self.packet)
        self.assertEqual(found["preexisting_jobs"], ["job-somebody-else"])
        self.assertEqual(found["preexisting_stages"],
                         {"job-somebody-else": ["implementation"]})
        self.assertIn("is NOT covered by this outcome",
                      found["accounting_scope"])

    def test_an_empty_store_surveys_clean(self):
        job, _control, _composed = self.serving()
        found = baseline.survey(job, self.packet)
        self.assertEqual(found["preexisting_jobs"], [])
        self.assertEqual(found["preexisting_stages"], {})

    # -- and the run itself, with a stranger in the store -------------------

    def test_another_jobs_stage_never_spends_this_runs_invocation(self):
        """The defect this closes: `serve` sweeps the STORE. Without the Job
        scope the stranger's implementation stage is admitted first, spends the
        single cap, and starts a container against work nobody selected here.
        """
        job, control, composed = self.serving()
        document, submit = self.foreign()
        submit(job, document)
        ticks = iter(range(0, 100000))
        outcome = baseline.supervise(
            job, control, composed, self.packet, clock=lambda: fixtures.NOW,
            sleep=self.driver(job, control, composed),
            monotonic=lambda: float(next(ticks)))
        self.assertEqual(outcome["state"], "settled", outcome["held_because"])
        self.assertEqual(outcome["admissions"], {"implementation": 1})
        # THE STRANGER REACHED THE GATE AND WAS TURNED AWAY. Recorded as
        # foreign, NOT as a refusal: a refusal ends this run, and an unrelated
        # Job in the store must not be able to do that.
        self.assertTrue(outcome["foreign_admissions"],
                        "the stranger never reached the gate, so this case "
                        "proves nothing about the scope")
        self.assertEqual(outcome["gate_refusals"], [])
        for one in outcome["foreign_admissions"]:
            self.assertIn("job-somebody-else", one["why"])
        # AND ITS ATTEMPT IS NOT THIS RUN'S TO ACCOUNT FOR.
        self.assertEqual(len(outcome["admitted_attempts"]), 1)
        self.assertEqual(outcome["preexisting_jobs"], ["job-somebody-else"])
        self.assertIn("is NOT covered by this outcome",
                      outcome["accounting_scope"])

    def test_the_outcome_names_the_job_it_accounts_for(self):
        _composed, outcome, _job, _control = self.supervised()
        self.assertEqual(outcome["job_id"],
                         self.packet["submission"]["job_id"])
        self.assertIn(outcome["job_id"], outcome["accounting_scope"])


class TheGateRefusesAnotherJobsWork(unittest.TestCase):
    """The scope, at the boundary itself."""

    def gate(self, operations, job_id="job-ours"):
        return baseline.AdmissionGate(operations, caps={"implementation": 1},
                                      job_id=job_id)

    def test_admit_and_claim_refuse_a_stage_of_another_job(self):
        inner = mock.Mock()
        gate = self.gate(inner)
        for act, stage in (("admit", {"kind": "implementation",
                                      "job_id": "job-theirs",
                                      "stage_id": "s9"}),
                           ("claim", {"kind": "implementation",
                                      "job_id": "job-theirs",
                                      "stage_id": "s9"})):
            with self.subTest(act=act):
                with self.assertRaises(ContractRefusal) as caught:
                    if act == "admit":
                        gate.admit(stage, {})
                    else:
                        gate.claim(stage)
                self.assertIn("this run serves Job 'job-ours'",
                              caught.exception.message)
        inner.admit.assert_not_called()
        inner.claim.assert_not_called()
        # NOT COUNTED AS A CAP REFUSAL. `should_continue` ends the run on
        # `refusals`, and a stranger in the store may not end a correct run.
        self.assertEqual(gate.refusals, [])
        self.assertEqual(len(gate.foreign), 2)

    def test_launch_refuses_an_attempt_on_a_stage_it_never_admitted(self):
        inner = mock.Mock()
        gate = self.gate(inner)
        with self.assertRaises(ContractRefusal) as caught:
            gate.launch({"attempt_id": "attempt-x", "stage_id": "s9"}, {})
        self.assertIn("never admitted", caught.exception.message)
        inner.launch.assert_not_called()
        # AND IT IS NOT RECORDED AS THIS RUN'S RUNTIME, which is the point:
        # recording it would put another Job's container into this run's
        # cleanup obligation.
        self.assertEqual(gate.launched, {})

    def test_our_own_stage_passes_through_untouched(self):
        inner = mock.Mock()
        gate = self.gate(inner)
        stage = {"kind": "implementation", "job_id": "job-ours",
                 "stage_id": "s1"}
        gate.admit(stage, {})
        gate.claim(stage)
        gate.launch({"attempt_id": "attempt-1", "stage_id": "s1"}, {})
        self.assertEqual(gate.foreign, [])
        self.assertEqual(gate.launched, {"attempt-1": "implementation"})
        inner.admit.assert_called_once()
        inner.launch.assert_called_once()

    def test_an_unscoped_gate_is_the_previous_behaviour(self):
        """`job_id=None` is the seam a caller may still drive without a Job."""
        gate = baseline.AdmissionGate(mock.Mock(),
                                      caps={"implementation": 1})
        gate.admit({"kind": "implementation", "job_id": "anything",
                    "stage_id": "s1"}, {})
        self.assertEqual(gate.foreign, [])


class ThePacketIsProvedBeforeAnythingOpens(BaselineCase):

    def read_packet(self, **overrides):
        return baseline.held_packet(
            self.rewritten(**overrides) if overrides else self.packet_path)

    def rewritten(self, **overrides):
        packet = dict(self.packet)
        packet.update(overrides)
        place = self.packet_root / "OTHER.json"
        place.write_text(json.dumps(packet, sort_keys=True, indent=2),
                         encoding="utf-8")
        return str(place)

    def test_the_reviewed_packet_is_held_whole(self):
        held = baseline.held_packet(self.packet_path)
        self.assertEqual(held["schema"], baseline.PACKET_SCHEMA)
        self.assertEqual(held["bounds"]["implementer_invocations"], 1)

    def test_a_second_implementer_invocation_is_refused_by_name(self):
        with self.assertRaises(baseline.SupervisorRefusal) as caught:
            self.read_packet(bounds=dict(self.packet["bounds"],
                                         implementer_invocations=2))
        self.assertIn("A correction round belongs to the resume Job",
                      str(caught.exception))

    def test_bounds_carrying_the_other_jobs_members_are_refused(self):
        """`_BOUNDS` is exact: a zeroed review count is still that Job's
        vocabulary arriving in this packet."""
        with self.assertRaises(baseline.SupervisorRefusal) as caught:
            self.read_packet(bounds=dict(self.packet["bounds"],
                                         review_invocations=0,
                                         corrections=0))
        self.assertIn("unexpected corrections, review_invocations",
                      str(caught.exception))

    def test_a_moved_fixture_byte_refuses_before_a_store_opens(self):
        place = os.path.join(self.source, "harness.py")
        with open(place, "a", encoding="utf-8") as handle:
            handle.write("# moved\n")
        with self.assertRaises(baseline.SupervisorRefusal) as caught:
            baseline.held_packet(self.packet_path)
        self.assertIn("harness.py", str(caught.exception))

    def test_a_retry_the_packet_did_not_forbid_is_refused(self):
        with self.assertRaises(baseline.SupervisorRefusal) as caught:
            self.read_packet(bounds=dict(self.packet["bounds"], retry=True))
        self.assertIn("never retries", str(caught.exception))

    def test_mutable_state_inside_the_code_boundary_is_refused(self):
        with self.assertRaises(baseline.SupervisorRefusal) as caught:
            self.read_packet(code_boundary=str(Path(self.root).resolve()))
        self.assertIn("inside the code boundary", str(caught.exception))

    def test_the_imported_packages_must_resolve_inside_the_bound_source(self):
        held = baseline.held_packet(self.packet_path)
        with self.assertRaises(baseline.SupervisorRefusal) as caught:
            baseline.verify_imported_sources(
                held, modules=["json"],
                program=str(HERE / "baseline.py"))
        self.assertIn("outside the bound manager source",
                      str(caught.exception))

    def test_an_image_the_engine_does_not_hold_is_refused(self):
        held = baseline.held_packet(self.packet_path)
        with self.assertRaises(baseline.SupervisorRefusal) as caught:
            baseline.verify_worker_image(held, image_inspect=lambda one: None)
        self.assertIn("answered no document", str(caught.exception))


class TheGitReaderRunsOnlyReadingVerbs(unittest.TestCase):
    """AGENTS.md permits reviewing history and nothing else."""

    def test_a_writing_verb_refuses_before_a_child_is_started(self):
        with mock.patch("subprocess.run") as running:
            for verb in ("commit", "checkout", "update-ref", "push",
                         "gc", "reset"):
                with self.subTest(verb=verb):
                    with self.assertRaises(baseline.SupervisorRefusal):
                        baseline._git_read("/nowhere", verb, "HEAD")
        running.assert_not_called()

    def test_the_reading_verbs_are_the_only_ones_declared(self):
        self.assertEqual(sorted(baseline.GIT_READS),
                         ["cat-file", "rev-list", "rev-parse"])


def load_tests(loader, tests, pattern):
    """THIS FILE'S OWN CHECKS, and not the ones it inherits.

    `BaselineCase` extends `ManagedSessionResume` to reuse its accepted
    composition, which also inherits every test method that class defines.
    Running those again here would re-attribute the context implementation's
    own measured evidence to this baseline's verification and inflate what this
    file claims to have established. They stay where they were run.
    """
    del tests, pattern, loader
    suite = unittest.TestSuite()
    for case in (TheBaselineDrivesOneBoundedImplementation,
                 TheProposalIsTheAdaptersOwnAccount,
                 TheBaselineRefusesTheOtherJobsWorkload,
                 OneRunAccountsForOneJobAndSaysSo,
                 TheGateRefusesAnotherJobsWork,
                 TheAccountingDistinguishesAbsenceFromAnUnreadableState,
                 ThePacketIsProvedBeforeAnythingOpens,
                 TheGitReaderRunsOnlyReadingVerbs):
        for name in sorted(one for one in vars(case)
                           if one.startswith("test")):
            suite.addTest(case(name))
    return suite
