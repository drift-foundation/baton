"""Deterministic verification of the bounded owner supervisor (W236087).

WHAT IS REAL HERE. `supervisor.supervise` itself, the owner acts in
`supervisor.prepare`, the `AdmissionGate` the manager actually calls, the real
candidate qualification grant guard, the ordinary manager composition, worker
launches, custody, review cycles, endings, recorded verdicts and the manager's
own committed cleanup records. The engine and the provider subprocess are the
two accepted deterministic seams `ManagedSessionResume` already names.

WHAT IS NOT CLAIMED. No container, no image execution, no live provider, no
network and no credential. This establishes the SUPERVISOR's lifetime, caps,
stop, cleanup accounting, workload validation and refusals -- not that the
production CLI restores a conversation, which is the remaining question the
packet exists to ask.

THE `sleep` SEAM IS WHERE THE WORKER TURNS HAPPEN, and that is deliberate: the
composed deployment has no daemon to run a container, so the one boundary this
build cannot cross is driven from the loop's own injected wait. `supervise` is
otherwise entered exactly as the live command enters it.

REVIEW 2026-09-22T06:36:24Z. `review-repro-236474.py` reproduced four defects:
a packet declaring one invocation of each ran two and settled; an accepted first
review settled with no correction; a cleanup sweep admitted a runtime and then
left it out of the accounting; and a fault after an admission lost that runtime
entirely. Each has a case below asserting the CORRECTED behaviour, named after
the defect rather than after the fix.
"""
import io
import json
import os
from pathlib import Path
import unittest
from unittest import mock

from baton_v12.contracts import (ContractRefusal, digest, digest_of_bytes,
                                 job_input_identity)
from baton_v12 import job_manager
from baton_v12.job_manager import execution_limits
from baton_v12.worker_manager import (frozen_output_of, load_manifest,
                                      provider_context as context)
from baton_v12.worker_manager.workspaces import configure_workspace_storage
from tests.job_manager import fixtures
from tests.manager.test_claude_context import ManagedSessionResume
from tools import stage_execution

import supervisor

HERE = Path(__file__).resolve().parent
IMPLEMENTATION_EDITS = {"harness.py": "print('ready')\n"}
CORRECTION_EDITS = {"harness.py": "print('READY')\n"}
FEEDBACK = ("Change the output to READY and preserve the trailing newline. "
            "Change only harness.py and rerun python3 harness.py.")
TURN_SECONDS = 180


class SupervisedCase(ManagedSessionResume):
    """One Job, implementation and review only, driven by the supervisor."""

    RUN = "managed-correction-236087-deterministic"

    def setUp(self):
        super().setUp()
        # THE PROPOSED WORKLOAD'S OWN SHAPE: two stages, because the proposal
        # submits implementation and review and stops. An integration stage
        # would be a fourth turn nobody selected, and `_terminal` requires
        # EVERY configured stage to complete -- so leaving one in would have
        # made the supervisor's own stop condition unreachable rather than
        # proving anything about it.
        #
        # AND `/2`, CARRYING THE PROVIDER-TURN CEILING. R1: `turn_seconds` was
        # validated and dropped, so a packet declaring 180 seconds ran under
        # the build's 3600-second default. The Job is where that number lives.
        self.submission = {
            "schema": "baton.v12.job-submission/2",
            "submission_id": "sub-1",
            "jobs": [dict(
                fixtures.job(
                    "job-a", input_digest=job_input_identity(self.manifest),
                    policy_digest=fixtures.POLICY_DIGEST,
                    stages=[fixtures.stage("implementation", self.work),
                            fixtures.stage(
                                "review", self.work,
                                depends_on=[{"job_id": "job-a",
                                             "kind": "implementation"}])]),
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
            "schema": supervisor.PACKET_SCHEMA,
            "run_id": self.RUN, "work": "W236087", "claim": 236529,
            "note": "one deterministic managed correction under this grant",
            "worker_image": {
                "reference": "baton-v12-claude-worker:deterministic",
                "config_digest": "sha256:" + "0" * 64,
                "worker_files": {"opt/baton/claude_agent.py": "0" * 64}},
            "manager_runtime": {
                "path": str(self.packet_root / "runtime"),
                "executable_sha256": self.written_runtime(),
                "build_commit": "1e576ff2186db69e8b44da9d38874ff7e99ebbe3"},
            "manager_source": self.written_source(),
            "supervisor": {
                "path": str(HERE / "supervisor.py"),
                "sha256": self.digest_of(str(HERE / "supervisor.py"))},
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
                "job_id": "job-a"},
            "submission": {
                "path": places["submission.json"],
                "sha256": self.digest_of(places["submission.json"]),
                "job_id": "job-a"},
            "fixture": {
                "source_root": str(self.source),
                "files": {"harness.py": self.digest_of(
                    os.path.join(self.source, "harness.py"))}},
            "bounds": {"turn_seconds": TURN_SECONDS, "total_seconds": 900,
                       "cleanup_seconds": 60, "implementer_invocations": 2,
                       "review_invocations": 2, "corrections": 1,
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

        R3 is the reason this is no longer the whole story: the frozen
        executable is the INSTALLATION artifact and is never what supervises.
        The packet still binds it, and this case still proves that a moved byte
        refuses -- which one file proves exactly as well as a 5 MiB one.
        """
        place = self.packet_root / "runtime"
        place.mkdir(exist_ok=True)
        (place / "baton-v12-stack").write_bytes(b"#!/bin/sh\nexit 0\n")
        return self.digest_of(str(place / "baton-v12-stack"))

    def written_source(self):
        """A REAL importable manager-source tree, bound file by file.

        R3 asks for the code that actually runs to be the code that was
        reviewed. The production packet binds `baton_v12` and `tools`; this
        binds a small package with the same property -- it is on `sys.path`, it
        is really imported, and every one of its files is hashed -- so the
        location and digest checks are exercised rather than described.
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

    def serving(self, **members):
        """`ServingContextCase.serving`, with `supervisor.prepare` in place of
        the three owner acts it performs by hand.

        This is the point of the case: the storage, the certified profile and
        the one qualification grant are the SUPERVISOR's, committed through the
        same public functions, and the admission boundary then either accepts
        them or does not.
        """
        self.engine = self.quiescing()
        job, control = self.stores("supervised-serving")
        configure_workspace_storage(control, self.storage)
        supervisor.prepare(control, self.packet)
        composed = stage_execution.operations_from(
            self.composed_document(line_declared_base=self.base, **members),
            job, control, engine_run=self.engine,
            credential_provider=lambda provider, reference: self.secret,
            clock=lambda: fixtures.NOW, checkout=self.checkout)
        self.addCleanup(composed.close)
        self._composed = composed
        return job, control, composed

    # -- the injected wait, which is where a container would have run --------

    def driver(self, job, control, composed, *, verdicts=None):
        def wait(seconds):
            del seconds
            states = self.states(job, composed)
            if states.get("implementation") == "waiting":
                return self.run_implementation(control, composed)
            if states.get("review") == "waiting":
                return self.run_review(job, control, composed,
                                       verdicts=verdicts)
            return None
        return wait

    def pending(self, composed, role):
        held = [one for one in
                sorted(self.worker_of(composed, role).stage._prepared)
                if one not in self.turned]
        return held[0] if held else None

    def run_implementation(self, control, composed):
        attempt = self.pending(composed, "implementation")
        if attempt is None:
            return None
        self.turned.add(attempt)
        prepared = self.worker_of(composed, "implementation").stage._prepared
        edits = IMPLEMENTATION_EDITS if len(prepared) == 1 \
            else {"harness.py": "print('READY')\n" if len(prepared) == 2
                  else f"print('round {len(prepared)}')\n"}
        return self.assertEqual(
            self.turn(control, "implementation", attempt,
                      self.mounted(composed, "implementation", attempt),
                      edits=dict(edits)), 0)

    def run_review(self, job, control, composed, *, verdicts=None):
        attempt = self.pending(composed, "review")
        if attempt is None:
            return None
        self.turned.add(attempt)
        reviewed = sorted(self.worker_of(composed, "review").stage._prepared)
        index = len(reviewed) - 1
        sequence = verdicts or ["changes-requested", "accepted"]
        want = sequence[index] if index < len(sequence) else sequence[-1]
        if want == "accepted":
            body = self.acceptance(control)
        else:
            body = json.dumps({"schema": "baton.review-report/1",
                               "verdict": want, "findings": FEEDBACK})
        del job
        return self.turn(control, "review", attempt,
                         self.mounted(composed, "review", attempt),
                         edits={"review-report.json": body})

    def acceptance(self, control):
        """The independent review's own accepted report.

        Built from what actually happened -- the admissions, their receipt and
        generation digests and the exact retained provider bytes -- rather than
        from a fixture that asserts its own conclusion.
        """
        owner = context.context_use_of(
            control, sorted(self.turned)[0])["context_id"]
        chain = context._history(control, owner)
        admits = [one for one in chain if one["action"] == "admit"]
        finalized = [one for one in chain if one["action"] == "finalize"]
        results = []
        for index, admission in enumerate(admits):
            attempt = admission["payload"]["attempt_id"]
            place = (Path(self.config["launch_home"]) / "logs" / attempt
                     / "provider.stdout.log")
            body = self.provider_records[index]
            place.parent.mkdir(parents=True, exist_ok=True)
            place.write_bytes(body)
            results.append({"path": str(place), "bytes": len(body),
                            "digest": digest_of_bytes(body)})
        report = {"schema": "baton.context-qualification-review/1",
                  "run_id": self.RUN, "context_id": owner,
                  "attempts": [one["payload"]["attempt_id"] for one in admits],
                  "receipt_digests": [one["payload"]["receipt_digest"]
                                      for one in finalized],
                  "generation_digests": [one["payload"]["manifest_digest"]
                                         for one in finalized],
                  "provider_results": results}
        return json.dumps({"schema": "baton.review-report/1",
                           "verdict": "accepted",
                           "findings": json.dumps(report)})

    # -- one bounded supervised run ------------------------------------------

    def supervised(self, *, packet=None, **operands):
        job, control, composed = self.serving()
        ticks = iter(range(0, 100000))

        def monotonic():
            return float(next(ticks))

        return composed, supervisor.supervise(
            job, control, composed, packet or self.packet,
            clock=lambda: fixtures.NOW,
            sleep=self.driver(job, control, composed, **operands),
            monotonic=monotonic), job, control


class TheSupervisorDrivesOneBoundedCorrection(SupervisedCase):

    def test_it_settles_after_one_correction_and_proves_every_cleanup(self):
        composed, outcome, job, control = self.supervised()
        self.assertEqual(outcome["state"], "settled", outcome["held_because"])
        self.assertEqual(outcome["stopped"], "completed")
        self.assertEqual(outcome["stage_states"],
                         {"implementation": "completed", "review": "completed"})
        self.assertEqual(outcome["retry"], False)
        self.assertEqual(outcome["outstanding_cleanup"], [])
        self.assertEqual(outcome["unexpected_attempts"], [])
        # FOUR RUNTIMES, which is the proposed workload exactly: two
        # implementer invocations and two independent review invocations.
        self.assertEqual(len(outcome["admitted_attempts"]), 4)
        for attempt, held in sorted(outcome["cleanup"].items()):
            with self.subTest(attempt=attempt):
                self.assertIn(held["cleanup"], supervisor.POSITIVE_CLEANUP)
                self.assertEqual(held["state"], "absent")
        del composed, job, control

    def test_the_declared_per_turn_ceiling_is_the_jobs_own(self):
        """R1: the number the packet declares is the number the Job carries."""
        _composed, outcome, _job, _control = self.supervised()
        self.assertEqual(outcome["provider_turn"]["seconds"], TURN_SECONDS)
        self.assertEqual(outcome["provider_turn"]["origin"],
                         execution_limits.JOB)
        self.assertEqual(outcome["provider_turn"]["setting"],
                         "provider_turn_seconds")

    def test_the_gate_counted_exactly_the_declared_invocations(self):
        _composed, outcome, _job, _control = self.supervised()
        self.assertEqual(outcome["admissions"],
                         {"implementation": 2, "review": 2})
        self.assertEqual(outcome["gate_refusals"], [])

    def test_the_workload_evidence_is_the_selected_sequence(self):
        """R1: settled now means the correction really happened."""
        _composed, outcome, _job, _control = self.supervised()
        workload = outcome["workload"]
        self.assertEqual(workload["shortfalls"], [])
        self.assertEqual(workload["modes"], ["open", "restore"])
        self.assertEqual(len(workload["conversations"]), 1)
        self.assertEqual(workload["generations"], [0, 1])
        self.assertEqual(len(set(workload["proposal_heads"])), 2)
        self.assertEqual(workload["dispositions"],
                         ["changes-requested", "accepted"])

    def test_the_correction_reached_the_provider_as_a_restore(self):
        """The supervised run really drove the resume path, not two opens."""
        self.supervised()
        calls = [json.loads(line)
                 for line in self.calls.read_text().splitlines()]
        self.assertEqual([one["restored"] for one in calls], [False, True])
        self.assertIn("THE REVIEW'S FINDINGS:\n" + FEEDBACK,
                      calls[1]["argv"][-1])

    def test_one_grant_carried_both_generations(self):
        _composed, _outcome, _job, control = self.supervised()
        owner = context.context_use_of(
            control, sorted(self.turned)[0])["context_id"]
        admits = [one for one in context._history(control, owner)
                  if one["action"] == "admit"]
        self.assertEqual([one["payload"]["qualification_run"]
                          for one in admits], [self.RUN, self.RUN])

    def test_the_outcome_is_retained_where_the_packet_says(self):
        _composed, outcome, _job, _control = self.supervised()
        retained = json.loads(
            Path(self.packet["outcome_path"]).read_text(encoding="utf-8"))
        self.assertEqual(retained, outcome)
        self.assertEqual(retained["schema"], supervisor.OUTCOME_SCHEMA)

    def test_the_mirrored_claim_namespace_matches_the_worker(self):
        """`single_worker`'s rule: mirrored names are kept honest by a test."""
        import claude_agent

        self.assertEqual(supervisor.CLAIM_NAMESPACE,
                         claude_agent.CLAIM_NAMESPACE)


class TheSupervisorEnforcesTheSelectedWorkload(SupervisedCase):
    """R1. Each case is one way a run can look finished and not be."""

    def test_one_declared_invocation_refuses_the_second_admission(self):
        """The reviewer's first counterexample, now refused at the gate.

        A packet declaring one implementer and one review invocation used to
        run two of each and report settled. The second admission is now
        refused BEFORE an offer is issued, and the run is held naming the cap.
        """
        packet = self.written_packet(bounds=dict(
            self.packet["bounds"], implementer_invocations=1,
            review_invocations=1, corrections=0))
        supervisor.held_packet(self.packet_path)
        _composed, outcome, _job, _control = self.supervised(packet=packet)
        self.assertEqual(outcome["state"], "held")
        self.assertEqual(outcome["admissions"],
                         {"implementation": 1, "review": 1})
        self.assertTrue(any("all of them are spent" in one["why"]
                            for one in outcome["gate_refusals"]),
                        outcome["gate_refusals"])
        self.assertEqual(outcome["stopped"], "invocation-cap-refused")
        # AND THE PROVIDER WAS NOT INVOKED A SECOND TIME.
        self.assertEqual(self.calls_count(), 1)

    def test_an_accepted_first_review_is_held_rather_than_settled(self):
        """The reviewer's second counterexample, now held.

        Both stages complete and every cleanup is positive, and that is exactly
        the state the old success condition called settled -- with no
        correction, no restore and no revised proposal.
        """
        _composed, outcome, _job, _control = self.supervised(
            verdicts=["accepted"])
        self.assertEqual(outcome["state"], "held")
        self.assertEqual(outcome["stopped"], "completed")
        self.assertEqual(outcome["outstanding_cleanup"], [])
        self.assertEqual(self.calls_count(), 1)
        workload = outcome["workload"]
        self.assertEqual(workload["modes"], ["open"])
        self.assertEqual(workload["dispositions"], ["accepted"])
        said = " ".join(outcome["held_because"])
        self.assertIn("the selected sequence is ['open', 'restore']", said)
        self.assertIn("implementer invocation(s) and this run has 1", said)

    def test_a_second_changes_requested_exhausts_the_cap_and_holds(self):
        """No third implementer invocation, and no fabricated acceptance."""
        _composed, outcome, _job, _control = self.supervised(
            verdicts=["changes-requested", "changes-requested"])
        self.assertEqual(outcome["state"], "held")
        self.assertEqual(outcome["admissions"]["implementation"], 2)
        self.assertEqual(outcome["stopped"], "invocation-cap-refused")
        self.assertTrue(any("all of them are spent" in one["why"]
                            for one in outcome["gate_refusals"]))

    def test_a_packet_whose_corrections_and_invocations_disagree_refuses(self):
        self.written_packet(bounds=dict(
            self.packet["bounds"], implementer_invocations=1,
            review_invocations=1, corrections=1))
        with self.assertRaisesRegex(supervisor.SupervisorRefusal,
                                    r"1 correction\(s\) is 2 implementer"):
            supervisor.held_packet(self.packet_path)

    def test_a_job_without_the_declared_ceiling_refuses_before_serving(self):
        """A bound this run did not request is not a bound it has."""
        self.submission = dict(
            self.submission, schema="baton.v12.job-submission/1",
            jobs=[{name: value
                   for name, value in self.submission["jobs"][0].items()
                   if name != "execution_limits"}])
        packet = self.written_packet()
        with self.assertRaisesRegex(supervisor.SupervisorRefusal,
                                    "effective ceiling is 3600s"):
            self.supervised(packet=packet)


class TheSupervisorStopsAdmissionAndAccountsForEveryRuntime(unittest.TestCase):
    """R2. The gate, and the two boundary faults the reviewer reproduced."""

    def gate(self, operations, **caps):
        return supervisor.AdmissionGate(
            operations, caps=caps or {"implementation": 1, "review": 1})

    def test_a_closed_gate_refuses_admit_claim_and_launch(self):
        inner = mock.Mock()
        gate = self.gate(inner)
        gate.stop()
        for act, arguments in (("admit", ({"kind": "implementation"}, {})),
                               ("claim", ({"kind": "review"},)),
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
        gate.receipt_of("op-1")
        self.assertTrue(gate.canonical)
        inner.conclude.assert_called_once()
        inner.refresh_runtime.assert_called_once()
        inner.receipt_of.assert_called_once_with("op-1")

    def test_the_cap_refuses_before_the_inner_admit_is_reached(self):
        inner = mock.Mock()
        gate = self.gate(inner, implementation=1, review=1)
        gate.admit({"kind": "implementation", "stage_id": "s1"}, {})
        with self.assertRaises(ContractRefusal):
            gate.admit({"kind": "implementation", "stage_id": "s1"}, {})
        self.assertEqual(inner.admit.call_count, 1)
        self.assertEqual(gate.admissions["implementation"], 1)

    def test_an_unknown_stage_kind_is_refused_by_name(self):
        gate = self.gate(mock.Mock())
        with self.assertRaises(ContractRefusal) as caught:
            gate.admit({"kind": "integration", "stage_id": "s3"}, {})
        self.assertIn("'integration' stage reached the admission gate",
                      caught.exception.message)

    def test_a_launch_that_faults_is_still_a_runtime_this_run_started(self):
        """R2: the identity is taken at the call, before delegating."""
        inner = mock.Mock()
        inner.launch.side_effect = RuntimeError("engine fault")
        gate = self.gate(inner)
        with self.assertRaises(RuntimeError):
            gate.launch({"attempt_id": "attempt-1", "stage_id": "s1"}, {})
        self.assertIn("attempt-1", gate.launched)

    # -- the two reproduced boundary faults, now corrected ------------------

    def run_case(self, *, late_failure=False):
        import tempfile

        with tempfile.TemporaryDirectory(prefix="w236087-fault-") as root:
            place = Path(root)
            (place / "submission").write_text("{}", encoding="utf-8")
            packet = {
                "bounds": {"total_seconds": 2, "cleanup_seconds": 3,
                           "turn_seconds": 180, "implementer_invocations": 1,
                           "review_invocations": 1, "corrections": 0,
                           "retry": False},
                "submission": {"path": str(place / "submission"),
                               "job_id": "job-a"},
                "outcome_path": str(place / "outcome"),
                "run_id": "fault-synthetic", "work": "W236087",
                "claim": 236529}
            seen, queries, counts = {}, [], {"sweeps": 0}
            limits = {"boundaries": {"provider_turn": {
                "seconds": 180, "origin": execution_limits.JOB,
                "setting": "provider_turn_seconds", "default_seconds": 3600}}}

            def attempts(job, operations, job_id):
                del job, job_id
                # THE GATE IS WHAT THE MANAGER WAS GIVEN, so a launch it
                # recorded is visible to the accounting even here.
                del operations
                return dict(seen), {"implementation": "waiting"}, limits

            def serve(store, operations, *, should_continue, **rest):
                del store, rest
                if not late_failure:
                    operations.launch({"attempt_id": "a", "stage_id": "s1"},
                                      {})
                    seen["a"] = "implementation"
                should_continue()
                if late_failure:
                    operations.launch({"attempt_id": "late",
                                       "stage_id": "s1"}, {})
                    raise RuntimeError("fault after a launch, before the "
                                       "next predicate")

            def clean(control, given, admitted):
                del control, given
                queries.append(sorted(admitted))
                return {"cleanup": {one: {"cleanup": None} for one in admitted},
                        "outstanding": list(admitted)}

            def sweep(store, operations, **rest):
                del store, rest
                counts["sweeps"] += 1
                # A REAL SWEEP WOULD HAVE TO GO THROUGH THE GATE TO START
                # ANYTHING, and the gate is closed by now. This models a
                # deployment that started one anyway.
                operations.launched["new-after-stop"] = "review"
                seen["new-after-stop"] = "review"

            ticks = iter(range(1000))
            inner = mock.Mock()
            inner.launch.return_value = {}
            with mock.patch.object(job_manager, "submit",
                                   return_value={"submission_id": "s"}), \
                mock.patch.object(job_manager, "read_submission",
                                  return_value={}), \
                mock.patch.object(job_manager, "serve", side_effect=serve), \
                mock.patch.object(job_manager, "sweep", side_effect=sweep), \
                mock.patch.object(supervisor, "_attempts_of",
                                  side_effect=attempts), \
                mock.patch.object(supervisor, "_cleanups", side_effect=clean), \
                mock.patch.object(supervisor, "_workload_evidence",
                                  return_value={"shortfalls": []}):
                outcome = supervisor.supervise(
                    None, None, inner, packet,
                    clock=lambda: "2026-09-22T00:00:00Z",
                    sleep=lambda seconds: None,
                    monotonic=lambda: float(next(ticks)))
            return outcome, queries, counts

    def test_a_runtime_started_during_cleanup_is_accounted_not_just_noted(self):
        """The reviewer's third counterexample.

        It used to appear in `unexpected_attempts` and NOWHERE else: no cleanup
        query named it and the final cleanup map left it out.
        """
        outcome, queries, counts = self.run_case()
        self.assertEqual(outcome["unexpected_attempts"], ["new-after-stop"])
        self.assertIn("new-after-stop", outcome["cleanup"])
        self.assertIn("new-after-stop", outcome["admitted_attempts"])
        self.assertTrue(any("new-after-stop" in one for one in queries),
                        queries)
        self.assertEqual(outcome["state"], "held")
        self.assertIn("a runtime was admitted after admission closed: "
                      "new-after-stop", outcome["held_because"])
        self.assertGreaterEqual(counts["sweeps"], 1)

    def test_a_fault_after_a_launch_still_accounts_for_that_runtime(self):
        """The reviewer's fourth counterexample.

        A fault between a launch and the next predicate used to yield
        `admitted_attempts: []` and `cleanup: {}` -- the runtime vanished from
        the report. The launch record is taken at the call, so it cannot.
        """
        outcome, queries, _counts = self.run_case(late_failure=True)
        self.assertIn("late", outcome["admitted_attempts"])
        self.assertIn("late", outcome["cleanup"])
        self.assertTrue(any("late" in one for one in queries), queries)
        self.assertEqual(outcome["state"], "held")
        self.assertIn("the serving loop did not end cleanly",
                      outcome["held_because"])


class TheSupervisorShutsDownWhatItStarted(SupervisedCase):
    """R2a and R2b, review 2026-09-22T07:03:13Z.

    Closing the gate stops the NEXT runtime. These are about the one already
    executing, and about a canonical read that did not answer.
    """

    @staticmethod
    def executing(outcome):
        """The admitted attempts this manager knew had a live runtime.

        PER ATTEMPT, not per stage kind: review 2026-09-22T11:53:11Z showed
        that reading the stage projection passed over a launched attempt whose
        kind was unknown and could cancel a completed older generation because
        its stage had a newer waiting one.
        """
        return sorted(
            one for one, held in outcome["cancellation"].items()
            if held.get("runtime_id") is not None
            and held.get("execution_runtime") not in supervisor.GONE)

    def timed_out(self, operations=None, seconds=8):
        job, control, composed = self.serving()
        ticks = iter(range(10000))
        packet = dict(self.packet, bounds=dict(
            self.packet["bounds"], total_seconds=seconds, cleanup_seconds=3))
        given = composed if operations is None else operations(composed)
        return composed, supervisor.supervise(
            job, control, given, packet, clock=lambda: fixtures.NOW,
            sleep=lambda seconds: None,
            monotonic=lambda: float(next(ticks)))

    def test_a_timeout_with_a_waiting_runtime_orders_the_stop(self):
        """The reviewer's counterexample, with a composition that can stop.

        `attempts.request_cancellation` fences at the Authority and then orders
        the agent and the runtime; its port, cooperative agent and adapter are
        per-attempt objects the composed deployment builds at launch, so the
        supervisor asks the composition for them by name.
        """
        ordered = []

        class Cancelling:
            def __init__(self, inner):
                self._inner = inner

            def __getattr__(self, name):
                return getattr(self._inner, name)

            @property
            def canonical(self):
                return self._inner.canonical

            def cancel_attempt(self, *, attempt_id, reason):
                ordered.append((attempt_id, reason))
                return {"fenced": True, "ordered": True}

        _composed, outcome = self.timed_out(operations=Cancelling)
        self.assertEqual(outcome["stopped"], "overall-bound-exceeded")
        self.assertTrue(outcome["admitted_attempts"])
        active = self.executing(outcome)
        self.assertTrue(active, outcome["cancellation"])
        # EVERY ATTEMPT WITH A LIVE RUNTIME WAS ORDERED STOPPED, and so was
        # every one this manager could not describe -- unknown is not absence.
        asked = sorted(one for one, _why in ordered)
        self.assertTrue(set(active).issubset(asked), (active, asked))
        self.assertTrue(set(asked).issubset(outcome["admitted_attempts"]))
        self.assertEqual([why for _one, why in ordered],
                         ["overall-bound-exceeded"] * len(ordered))
        for attempt in outcome["admitted_attempts"]:
            self.assertTrue(outcome["cancellation"][attempt]["requested"])
        self.assertNotIn("was not stopped",
                         " ".join(outcome["held_because"]))

    def test_the_real_composition_orders_the_engine_stop(self):
        """R2a's acceptance: the ORDINARY composition, and a real engine stop.

        No wrapper and no synthetic fenced/ordered facts. The supervisor asks
        the composed deployment, `stage_execution` routes the attempt to the
        worker its recorded allocation names, `single_worker` fences the exact
        participant and generation at the Authority through the accepted
        `attempts.request_cancellation`, and only then is the engine ordered to
        stop the exact runtime it started.
        """
        composed, outcome = self.timed_out()
        active = self.executing(outcome)
        self.assertTrue(active, outcome["cancellation"])
        for attempt in active:
            held = outcome["cancellation"][attempt]
            self.assertTrue(held["requested"], held)
            self.assertEqual(held["execution_runtime"], "running")
        # THE ENGINE REALLY RECEIVED THE STOP, for the exact runtime.
        stops = [argv for argv in self.engine.vectors if argv[1] == "stop"]
        self.assertTrue(stops, self.engine.vectors)
        started = {outcome["cancellation"][one]["runtime_id"]
                   for one in active}
        self.assertTrue(started.issubset({argv[-1] for argv in stops}),
                        (started, stops))
        # AND THE AUTHORITY WAS FENCED FIRST. `request_cancellation` journals
        # its intent and obtains the fence before any quiescence is ordered.
        for attempt in active:
            self.assertIn("fenced", outcome["cancellation"][attempt]["answer"])
        del composed

    def test_the_stop_is_ordered_and_is_not_proof_of_absence(self):
        """A stop that was ORDERED is not a runtime this manager saw gone."""
        _composed, outcome = self.timed_out()
        self.assertEqual(outcome["state"], "held")
        # Cleanup is still outstanding: ordering a stop settles no ending, and
        # the run refuses to call itself finished on the strength of the order.
        self.assertTrue(outcome["outstanding_cleanup"])
        self.assertIn("cannot prove positive cleanup",
                      " ".join(outcome["held_because"]))

    def test_a_composition_without_the_capability_is_held_and_says_so(self):
        """Honest reporting when a deployment composes no stop at all."""

        class Incapable:
            def __init__(self, inner):
                self._inner = inner

            def __getattr__(self, name):
                if name == "cancel_attempt":
                    raise AttributeError(name)
                return getattr(self._inner, name)

            @property
            def canonical(self):
                return self._inner.canonical

        _composed, outcome = self.timed_out(operations=Incapable)
        self.assertEqual(outcome["state"], "held")
        said = " ".join(outcome["held_because"])
        active = self.executing(outcome)
        self.assertTrue(active, outcome["cancellation"])
        for attempt in active:
            self.assertIn(f"execution on {attempt} was not stopped", said)
            self.assertFalse(outcome["cancellation"][attempt]["requested"])
        self.assertIn("no 'cancel_attempt'", said)

    def test_an_attempt_this_manager_cannot_describe_is_still_ordered(self):
        """R2a: unknown state is not absence.

        A launched attempt whose runtime facts cannot be read used to be passed
        over and reported as though nothing were executing. It is now named as
        unreadable AND the stop is still ordered for it -- a runtime this
        manager cannot describe is the one it must not leave running on a
        guess.
        """
        ordered, uncertainty = [], []

        class Cancelling:
            @staticmethod
            def cancel_attempt(*, attempt_id, reason):
                ordered.append((attempt_id, reason))
                return {"fenced": True}

        said = supervisor._cancel_active(
            Cancelling, mock.Mock(), {}, {"known-attempt": None}, {},
            uncertainty, reason="serving-failed",
            launched={"known-attempt"})
        self.assertEqual([one for one, _why in ordered], ["known-attempt"])
        self.assertTrue(said["known-attempt"]["requested"])
        self.assertIn("unreadable", said["known-attempt"])
        self.assertIn("could not describe the runtime of known-attempt",
                      " ".join(uncertainty))
        self.assertIn("not evidence that nothing is executing",
                      " ".join(uncertainty))

    def test_an_attempt_no_runtime_was_allocated_for_is_not_ordered(self):
        """The first live run's noise, removed without claiming quiescence.

        A review episode that never started anything carried an attempt
        identity in the projection. Ordering a cancellation for it refused for
        want of an allocation, and three held-reasons about a runtime that was
        never started buried the one real failure.
        """
        ordered, uncertainty = [], []

        class Cancelling:
            @staticmethod
            def cancel_attempt(*, attempt_id, reason):
                ordered.append((attempt_id, reason))
                return {"fenced": True}

        # AN ANSWERED ABSENCE, not a read that failed to answer. The
        # distinction is the whole of review 2026-09-22T14:38:24Z R1.
        with mock.patch.object(
                supervisor, "_runtime_facts",
                return_value=(None, supervisor.ABSENT, "no row")):
            said = supervisor._cancel_active(
                Cancelling, mock.Mock(), {}, {"never-started": "review"}, {},
                uncertainty, reason="exceptional", launched=set())
        self.assertEqual(ordered, [])
        held = said["never-started"]
        self.assertTrue(held["requested"])
        self.assertIsNone(held["runtime_id"])
        self.assertIn("holds no attempt row for this identity", held["why"])
        # AND IT SAYS WHAT IT IS NOT.
        self.assertIn("not a claim that nothing is running anywhere",
                      held["why"])

    def test_an_unreadable_state_is_accounted_for_not_excluded(self):
        """R1: absence is an ANSWER; a failed read is not one.

        A discovered attempt whose runtime read raised used to be written up as
        "never allocated", skipped for cancellation and dropped from the
        cleanup accounting -- absence inferred from a question nobody answered.
        """
        ordered, uncertainty = [], []

        class Cancelling:
            @staticmethod
            def cancel_attempt(*, attempt_id, reason):
                ordered.append((attempt_id, reason))
                return {"fenced": True}

        with mock.patch.object(
                supervisor, "_runtime_facts",
                return_value=(None, supervisor.UNREADABLE,
                              "RuntimeError: the store did not answer")):
            said = supervisor._cancel_active(
                Cancelling, mock.Mock(), {}, {"discovered": "review"}, {},
                uncertainty, reason="serving-failed", launched=set())
        # THE STOP IS STILL ORDERED.
        self.assertEqual([one for one, _why in ordered], ["discovered"])
        self.assertTrue(said["discovered"]["requested"])
        self.assertIn("unreadable", said["discovered"])

    def test_an_unreadable_discovered_attempt_stays_accountable(self):
        """And it is classified FOREIGN, so cleanup is still demanded."""
        uncertainty = []
        with mock.patch.object(
                supervisor, "_runtime_facts",
                return_value=(None, supervisor.UNREADABLE, "did not answer")):
            origin, _why = supervisor._origin(
                mock.Mock(), "discovered", set(), uncertainty)
        self.assertEqual(origin, supervisor.FOREIGN)
        self.assertIn("absence was not established", " ".join(uncertainty))

    def test_an_answered_absence_is_the_only_exclusion(self):
        uncertainty = []
        with mock.patch.object(
                supervisor, "_runtime_facts",
                return_value=(None, supervisor.ABSENT, "no row")):
            self.assertEqual(
                supervisor._origin(mock.Mock(), "never", set(), uncertainty)[0],
                supervisor.UNALLOCATED)
        # And an identity this run launched is never excluded, however it reads.
        with mock.patch.object(
                supervisor, "_runtime_facts",
                return_value=(None, supervisor.ABSENT, "no row")):
            self.assertEqual(
                supervisor._origin(mock.Mock(), "mine", {"mine"},
                                   uncertainty)[0],
                supervisor.STARTED)

    def test_an_interrupt_at_a_runtime_read_still_stops_and_retains(self):
        """The reviewer's strengthened counterexample. R2a.

        An interruption arriving at the per-attempt runtime READ used to escape
        `supervise` with no engine stop ordered and no outcome on disk. The
        read is now bounded, an unreadable fact is a reason to ORDER the stop,
        and the interruption is answered after the outcome is retained.
        """
        original = supervisor._runtime_facts
        raised = []

        def interrupt(control, attempt_id, uncertainty):
            if not raised:
                raised.append(attempt_id)
                raise KeyboardInterrupt("SIGTERM during runtime read")
            return original(control, attempt_id, uncertainty)

        with mock.patch.object(supervisor, "_runtime_facts",
                               side_effect=interrupt):
            with self.assertRaises(supervisor.SupervisorInterrupted) as caught:
                self.timed_out()
        self.assertTrue(raised)
        outcome = caught.exception.outcome
        self.assertEqual(outcome["state"], "held")
        self.assertIn("KeyboardInterrupt: SIGTERM during runtime read",
                      " ".join(outcome["interruptions"]))
        # THE OUTCOME IS ON DISK.
        retained = json.loads(
            Path(self.packet["outcome_path"]).read_text(encoding="utf-8"))
        self.assertEqual(retained["state"], "held")
        # AND THE ENGINE WAS STILL ORDERED TO STOP what was running.
        stops = [argv for argv in self.engine.vectors if argv[1] == "stop"]
        self.assertTrue(stops, self.engine.vectors)
        # Cleanup covers every attempt this run must account for; an
        # identity no runtime was allocated for is named separately.
        self.assertEqual(
            sorted(retained["cleanup"]),
            sorted(set(retained["admitted_attempts"])
                   - set(retained["unallocated_attempts"])))

    def test_a_deferred_signal_during_shutdown_is_recorded_not_raised(self):
        """The mode, asserted directly: raise while serving, defer after."""
        termination = supervisor.Termination()
        with self.assertRaises(KeyboardInterrupt):
            termination._handle(15, None)
        termination.defer()
        self.assertIsNone(termination._handle(15, None))
        self.assertEqual(len(termination.received), 2)
        self.assertIn("signal 15", termination.why)

    def test_an_interrupt_during_cancellation_still_retains_the_outcome(self):
        """R2a: the shutdown boundary holds across cancellation too.

        `KeyboardInterrupt` raised by the cancellation used to escape before
        anything was retained -- the one state this program exists to prevent.
        """
        job, control, composed = self.serving()
        ticks = iter(range(10000))

        class Interrupting:
            def __init__(self, inner):
                self._inner = inner

            def __getattr__(self, name):
                return getattr(self._inner, name)

            @property
            def canonical(self):
                return self._inner.canonical

            def cancel_attempt(self, *, attempt_id, reason):
                del attempt_id, reason
                raise KeyboardInterrupt("during cancellation")

        packet = dict(self.packet, bounds=dict(
            self.packet["bounds"], total_seconds=8, cleanup_seconds=3))
        with self.assertRaises(supervisor.SupervisorInterrupted) as caught:
            supervisor.supervise(
                job, control, Interrupting(composed), packet,
                clock=lambda: fixtures.NOW, sleep=lambda seconds: None,
                monotonic=lambda: float(next(ticks)))
        outcome = caught.exception.outcome
        self.assertEqual(outcome["state"], "held")
        self.assertIn("KeyboardInterrupt: during cancellation",
                      outcome["interrupted"])
        retained = json.loads(
            Path(packet["outcome_path"]).read_text(encoding="utf-8"))
        self.assertEqual(retained["state"], "held")
        # AND EVERY RUNTIME IS STILL ACCOUNTED FOR.
        # Cleanup covers every attempt this run must account for; an
        # identity no runtime was allocated for is named separately.
        self.assertEqual(
            sorted(retained["cleanup"]),
            sorted(set(retained["admitted_attempts"])
                   - set(retained["unallocated_attempts"])))

    def test_a_refused_cancellation_is_held_rather_than_absorbed(self):
        class Refusing:
            def __init__(self, inner):
                self._inner = inner

            def __getattr__(self, name):
                return getattr(self._inner, name)

            @property
            def canonical(self):
                return self._inner.canonical

            def cancel_attempt(self, *, attempt_id, reason):
                del attempt_id, reason
                raise ContractRefusal("refused", "precondition",
                                      "the authority would not fence")

        _composed, outcome = self.timed_out(operations=Refusing)
        self.assertEqual(outcome["state"], "held")
        self.assertIn("the cancellation of", " ".join(outcome["uncertainty"]))
        self.assertIn("the authority would not fence",
                      " ".join(outcome["held_because"]))

    def test_an_unreadable_history_after_the_stop_is_never_settled(self):
        """The reviewer's R2b counterexample.

        An otherwise completed correction used to report settled with no
        reasons at all when the canonical refresh raised after the stop. A
        failed read is not evidence of absence.
        """
        original = supervisor._attempts_of
        faults = []

        def fail_after_stop(job, operations, job_id):
            if isinstance(operations, supervisor.AdmissionGate) \
                    and operations.stopped:
                faults.append(True)
                raise RuntimeError("canonical history unavailable after stop")
            return original(job, operations, job_id)

        with mock.patch.object(supervisor, "_attempts_of",
                               side_effect=fail_after_stop):
            _composed, outcome, _job, _control = self.supervised()
        self.assertTrue(faults)
        self.assertEqual(outcome["state"], "held")
        self.assertFalse(outcome["final_canonical_read"])
        said = " ".join(outcome["held_because"])
        self.assertIn("canonical attempt history could not be read", said)
        self.assertIn("not evidence that no further runtime exists", said)
        self.assertIn("the final canonical accounting could not be read", said)
        # AND THE RUNTIMES IT DOES KNOW ARE STILL ACCOUNTED FOR.
        self.assertEqual(
            sorted(outcome["cleanup"]),
            sorted(set(outcome["admitted_attempts"])
                   - set(outcome["unallocated_attempts"])))

    def test_an_interrupt_retains_the_outcome_and_is_not_swallowed(self):
        """Ctrl-C and SIGTERM are shutdowns, not escapes."""
        job, control, composed = self.serving()
        ticks = iter(range(10000))

        def interrupt(seconds):
            del seconds
            raise KeyboardInterrupt("operator")

        with self.assertRaises(supervisor.SupervisorInterrupted) as caught:
            supervisor.supervise(
                job, control, composed, self.packet,
                clock=lambda: fixtures.NOW, sleep=interrupt,
                monotonic=lambda: float(next(ticks)))
        outcome = caught.exception.outcome
        self.assertEqual(outcome["stopped"], "interrupted")
        self.assertEqual(outcome["state"], "held")
        self.assertIn("KeyboardInterrupt: operator", outcome["interrupted"])
        self.assertIn("the run was interrupted",
                      " ".join(outcome["held_because"]))
        retained = json.loads(
            Path(self.packet["outcome_path"]).read_text(encoding="utf-8"))
        self.assertEqual(retained["state"], "held")
        self.assertIn("final_canonical_read", retained)


class ThePacketIsProvedBeforeAnythingOpens(SupervisedCase):

    def test_the_reviewed_packet_is_accepted_whole(self):
        held = supervisor.held_packet(self.packet_path)
        self.assertEqual(held["run_id"], self.RUN)

    def test_a_moved_fixture_byte_refuses_by_name(self):
        place = Path(self.source) / "harness.py"
        place.write_text("print('something else')\n", encoding="utf-8")
        with self.assertRaisesRegex(supervisor.SupervisorRefusal,
                                    r"the fixture file 'harness\.py'"):
            supervisor.held_packet(self.packet_path)

    def test_a_moved_deployment_configuration_refuses_by_name(self):
        place = Path(self.packet["deployment"]["config_path"])
        place.write_text(place.read_text(encoding="utf-8") + "\n",
                         encoding="utf-8")
        with self.assertRaisesRegex(supervisor.SupervisorRefusal,
                                    "the deployment configuration"):
            supervisor.held_packet(self.packet_path)

    def test_a_moved_manager_runtime_refuses_by_name(self):
        place = Path(self.packet["manager_runtime"]["path"]) / "baton-v12-stack"
        place.write_bytes(b"#!/bin/sh\nexit 1\n")
        with self.assertRaisesRegex(supervisor.SupervisorRefusal,
                                    "the installed manager runtime"):
            supervisor.held_packet(self.packet_path)

    def test_a_changed_imported_manager_source_refuses(self):
        """R3's entrypoint check: change the code that RUNS, not a stub."""
        place = (Path(self.packet["manager_source"]["path"]) / "boundpkg"
                 / "inner.py")
        place.write_text("MARK = 'tampered'\n", encoding="utf-8")
        with self.assertRaisesRegex(
                supervisor.SupervisorRefusal,
                r"the manager source file 'boundpkg/inner\.py'"):
            supervisor.held_packet(self.packet_path)

    def test_a_manager_source_whose_count_disagrees_refuses(self):
        source = dict(self.packet["manager_source"])
        source["file_count"] = 99
        self.written_packet(manager_source=source)
        with self.assertRaisesRegex(supervisor.SupervisorRefusal,
                                    "declares 99 files and binds 2"):
            supervisor.held_packet(self.packet_path)

    def test_a_moved_supervisor_program_refuses_by_name(self):
        held = dict(self.packet["supervisor"], sha256="0" * 64)
        self.written_packet(supervisor=held)
        with self.assertRaisesRegex(supervisor.SupervisorRefusal,
                                    "the supervisor program"):
            supervisor.held_packet(self.packet_path)

    def test_the_bound_source_is_where_the_imported_package_resolves(self):
        """R3: accepted only because the module really comes from there."""
        import sys

        sys.path.insert(0, self.packet["manager_source"]["path"])
        self.addCleanup(sys.path.remove,
                        self.packet["manager_source"]["path"])
        self.addCleanup(sys.modules.pop, "boundpkg", None)
        resolved = supervisor.verify_imported_sources(
            self.packet, program=str(HERE / "supervisor.py"))
        self.assertIn("boundpkg", resolved)
        for place in resolved["boundpkg"]:
            self.assertTrue(place.startswith(
                os.path.realpath(self.packet["manager_source"]["path"])))

    def test_a_package_resolved_outside_the_bound_source_refuses(self):
        """The defect R3 names: pinned bytes, different code executing."""
        with self.assertRaisesRegex(supervisor.SupervisorRefusal,
                                    "outside the bound manager source"):
            supervisor.verify_imported_sources(
                self.packet, modules=["baton_v12"],
                program=str(HERE / "supervisor.py"))

    def test_a_supervisor_running_from_elsewhere_refuses(self):
        with self.assertRaisesRegex(supervisor.SupervisorRefusal,
                                    "this process is running"):
            supervisor.verify_imported_sources(
                self.packet, modules=[], program=str(HERE / "PACKET.json"))

    def test_a_boundary_holding_this_runs_own_stores_refuses(self):
        """The owner's refused launch, caught before a store is opened.

        The inferred boundary answered the run root's PARENT, so this run's own
        Job store, control store, state root and context storage were all
        inside the tree the code lives in -- and composition refused after the
        owner acts had already committed.
        """
        for member, place in (
                ("job store", self.packet["deployment"]["job_store"]),
                ("control store", self.packet["deployment"]["control_store"]),
                ("state root", self.packet["deployment"]["state_root"]),
                ("context storage", self.packet["context"]["storage_path"])):
            with self.subTest(member=member):
                self.written_packet(
                    code_boundary=os.path.dirname(os.path.realpath(place)))
                with self.assertRaisesRegex(
                        supervisor.SupervisorRefusal,
                        "inside the code boundary"):
                    supervisor.held_packet(self.packet_path)

    def test_a_code_boundary_that_is_not_a_directory_refuses(self):
        self.written_packet(code_boundary=str(HERE / "supervisor.py"))
        with self.assertRaisesRegex(supervisor.SupervisorRefusal,
                                    "is not a directory"):
            supervisor.held_packet(self.packet_path)
        self.written_packet(code_boundary="relative/path")
        with self.assertRaisesRegex(supervisor.SupervisorRefusal,
                                    "one absolute canonical directory"):
            supervisor.held_packet(self.packet_path)

    def test_the_production_composition_passes_the_bound_boundary(self):
        """`_compose` never lets `operations_from` infer one again."""
        composed = []

        def operations_from(configuration, job, control, **named):
            composed.append((configuration, named))
            return "composed"

        with mock.patch.object(stage_execution, "operations_from",
                               operations_from):
            answered = supervisor._compose(self.packet, "job", "control",
                                           io.StringIO())
        self.assertEqual(answered, "composed")
        self.assertEqual(len(composed), 1)
        _configuration, named = composed[0]
        self.assertEqual(named, {"checkout": self.packet["code_boundary"]})

    def test_a_packet_that_permits_a_retry_refuses(self):
        self.written_packet(bounds=dict(self.packet["bounds"], retry=True))
        with self.assertRaisesRegex(supervisor.SupervisorRefusal,
                                    "never retries"):
            supervisor.held_packet(self.packet_path)

    def test_a_grant_and_a_submission_naming_two_Jobs_refuse(self):
        self.written_packet(
            context=dict(self.packet["context"], job_id="job-b"))
        with self.assertRaisesRegex(supervisor.SupervisorRefusal,
                                    "one grant serves exactly one Job"):
            supervisor.held_packet(self.packet_path)

    def test_a_cleanup_reserve_inside_the_overall_bound_refuses(self):
        self.written_packet(
            bounds=dict(self.packet["bounds"], cleanup_seconds=900))
        with self.assertRaisesRegex(supervisor.SupervisorRefusal,
                                    "beside it"):
            supervisor.held_packet(self.packet_path)

    def test_an_unknown_member_refuses_rather_than_being_dropped(self):
        held = dict(self.packet, enabled=True)
        Path(self.packet_path).write_text(json.dumps(held, sort_keys=True),
                                          encoding="utf-8")
        with self.assertRaisesRegex(supervisor.SupervisorRefusal,
                                    "unexpected enabled"):
            supervisor.held_packet(self.packet_path)

    def test_an_absent_image_refuses_before_a_store_is_opened(self):
        with self.assertRaisesRegex(supervisor.SupervisorRefusal,
                                    "answered no document for image"):
            supervisor.verify_worker_image(self.packet,
                                           image_inspect=lambda one: None)

    def test_a_moved_image_configuration_digest_refuses(self):
        with self.assertRaisesRegex(supervisor.SupervisorRefusal,
                                    "is bound to"):
            supervisor.verify_worker_image(
                self.packet,
                image_inspect=lambda one: {"Id": "sha256:" + "1" * 64})

    def test_a_production_profile_is_refused_rather_than_certified(self):
        """This program drives ONE candidate run and certifies nothing."""
        production = dict(self.context_profile, qualification="production")
        place = Path(self.packet["context"]["profile_path"])
        place.write_text(json.dumps(production, sort_keys=True),
                         encoding="utf-8")
        held = json.loads(Path(self.packet_path).read_text(encoding="utf-8"))
        held["context"]["profile_sha256"] = self.digest_of(str(place))
        held["context"]["profile_digest"] = digest(production)
        Path(self.packet_path).write_text(json.dumps(held, sort_keys=True),
                                          encoding="utf-8")
        _job, control = self.stores("refusing")
        configure_workspace_storage(control, self.storage)
        with self.assertRaises(ContractRefusal) as caught:
            supervisor.prepare(control, supervisor.held_packet(
                self.packet_path))
        self.assertIn("production profile lacks recorded certification",
                      caught.exception.message)


def load_tests(loader, tests, pattern):
    """THIS FILE'S OWN CHECKS, and not the ones it inherits.

    `SupervisedCase` extends `ManagedSessionResume` to reuse its accepted
    composition, which also inherits every test method that class defines.
    Running those again here would re-attribute the implementation review's
    own measured evidence to this supervisor's verification and inflate what
    this file claims to have established. They stay where they were run.
    """
    del tests, pattern
    suite = unittest.TestSuite()
    for case in (TheSupervisorDrivesOneBoundedCorrection,
                 TheSupervisorEnforcesTheSelectedWorkload,
                 TheSupervisorStopsAdmissionAndAccountsForEveryRuntime,
                 TheSupervisorShutsDownWhatItStarted,
                 ThePacketIsProvedBeforeAnythingOpens):
        for name in sorted(one for one in vars(case)
                           if one.startswith("test")):
            suite.addTest(case(name))
    return suite


del frozen_output_of, load_manifest
