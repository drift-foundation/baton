"""W383215 — the installed cancel commands over a serving composition.

One disposable installed instance (the same layout the settlement commands
recognise), one REAL composed stage deployment over the recording fake engine,
and the two commands driven against it while it serves. The command requests
and reports; the sweep carries the request out through `cancel_attempt` and
the pre-attach fence; the stores say what was ordered and what ceased.
"""
import copy
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
from unittest import mock

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import JobStore, cancellation, submit, sweep
from baton_v12.worker_manager import ControlStore, attempts, oci
from baton_v12.worker_manager.failure_cause import attempt_cessation_outcome_of
from tools import instance, job_manager, stack_command
from tools import job_cancellation as command
from tests.job_manager import fixtures
from tests.tools import test_stage_execution as composed_tests

REASON = "the operator ends this Job before its deadline"
SOON = "2026-09-02T00:00:30.000Z"
MUCH_LATER = "2026-09-02T00:02:01.000Z"


class InstalledCancellation(composed_tests.ComposedOneJobCase):

    def setUp(self):
        super().setUp()
        self.places = instance.layout(self.root)
        Path(self.places["stores"]).mkdir()
        os.rename(self.authority_path, self.places["authority_store"])
        self.authority_path = self.places["authority_store"]
        self.config["authority_store"] = self.authority_path
        self.job_path = self.places["job_store"]
        self.control_path = self.places["control_store"]
        distro = Path(self.places["distro"])
        distro.mkdir(parents=True)
        Path(self.places["command"]).write_text("deterministic packaged fixture")
        selector = instance.emit(self.root,
                                 authority_uuid=self.config["authority_uuid"],
                                 identity={"fixture": True},
                                 runtime=instance.manifest(distro), now=1)
        instance.publish(self.places["instance"], selector)
        self.deployment_document = self.composed_document(line_declared_base=self.base)
        Path(self.places["deployment"]).write_text(json.dumps(self.deployment_document))
        self.patch_checkout = mock.patch("tools.stage_execution._checkout",
                                         return_value=self.checkout)
        self.patch_checkout.start()
        self.addCleanup(self.patch_checkout.stop)
        self.jobs, self.control, self.composed = self.serving()
        submit(self.jobs, self.submission)
        self.stage_id = "job-a/implementation"

    # -- the two commands, and the serving ticks beside them -----------------

    def call(self, verb, reason=None, job_id="job-a", at=fixtures.NOW):
        return command.execute(verb, self.places["instance"], job_id=job_id,
                               reason=reason, clock=lambda: at)

    def cancel(self, reason=REASON, **named):
        return self.call("cancel-job", reason=reason, **named)

    def report(self, **named):
        return self.call("cancel-status", **named)["cancellation"]

    def tick(self):
        return sweep(self.jobs, self.composed, now=fixtures.NOW)

    def state(self):
        return self.states(self.jobs, self.composed)["implementation"]

    def attempting(self, store, stage_id):
        from baton_v12.job_manager import attempting, live_of, stage_rows
        row = {one["stage_id"]: one for one in stage_rows(store)}[stage_id]
        return attempting(row, live_of(store, stage_id))

    def attempt_id(self):
        return self.attempting(self.jobs, self.stage_id)["attempt_id"]

    def claimed(self):
        """Drive to a CLAIMED stage whose launch the deployment cannot yet
        perform: an ordinary launch refusal keeps the claim level-triggered
        and no runtime exists, which is the pre-attach case."""
        held = mock.patch.object(
            type(self.composed), "launch",
            side_effect=ContractRefusal("refused", "precondition",
                                        "the workspace is not ready yet"))
        held.start()
        self.addCleanup(held.stop)
        self.drive(self.jobs, self.composed, "implementation", "claimed")
        return held

    def axes(self):
        return attempts.attempt_runtime_of(self.control, self.attempt_id())

    def journalled(self, kind):
        return self.control._connection.execute(
            "SELECT count(*) FROM operations WHERE kind = ? AND state = "
            "'committed'", (kind,)).fetchone()[0]

    def stops(self):
        return [one for one in self.engine.vectors if one[1] == "stop"]

    def logical(self):
        return tuple(tuple(owner._connection.iterdump())
                     for owner in (self.jobs, self.control))


class TheRequestWhileServing(InstalledCancellation):

    def test_an_active_runtime_is_ordered_through_the_composition(self):
        self.drive(self.jobs, self.composed, "implementation", "waiting")
        starts = len(self.engine.starts)
        answer = self.cancel()
        self.assertEqual(answer["schema"], command.SCHEMA)
        self.assertEqual(answer["request"]["job_id"], "job-a")
        self.assertEqual(answer["request"]["requested_at"], fixtures.NOW)
        # REQUESTED, NOT YET ACTED: the command placed no order itself.
        self.assertEqual(answer["cancellation"]["targets"][0]["state"],
                         "pending")
        self.assertEqual(self.stops(), [])
        self.assertEqual(self.journalled("attempt.cancel"), 0)
        report = self.tick()
        self.assertEqual([(one["effect"], one["outcome"])
                          for one in report["cancelled"]],
                         [("order-cessation", "ordered")])
        self.assertEqual(self.journalled("attempt.cancel"), 1)
        self.assertEqual(len(self.stops()), 1)
        self.assertIn(self.axes()["execution_runtime"],
                      ("cancel-requested", "stopping", "quiescent",
                       "uncertain"))
        status = self.report(at=SOON)
        self.assertEqual(status["targets"][0]["state"], "ordered")
        self.assertEqual(status["shutdown"], "within-bound")
        self.assertEqual(status["targets"][0]["orders"][0]["effect"],
                         "order-cessation")
        # THE OWNER FENCED ONCE; later ticks replay rather than re-fence,
        # and nothing was started again.
        self.tick()
        self.tick()
        self.assertEqual(self.journalled("attempt.cancel"), 1)
        self.assertEqual(len(self.engine.starts), starts)
        self.assertEqual(len(cancellation.targets_of(self.jobs, "job-a")), 1)
        # AND ORDERED IS NOT CEASED: the bound keeps running from the
        # request until an owner proves cessation.
        self.assertEqual(self.report(at=MUCH_LATER)["shutdown"], "unresolved")
        self.assertEqual(self.report(at=MUCH_LATER)["requested_at"],
                         fixtures.NOW)

    def test_a_claimed_stage_is_fenced_and_never_started(self):
        unready = self.claimed()
        self.cancel()
        report = self.tick()
        self.assertEqual([one["outcome"] for one in report["started"]],
                         ["deferred"])
        self.assertEqual([(one["effect"], one["outcome"])
                          for one in report["cancelled"]],
                         [("fence-unstarted", "ordered")])
        self.assertEqual(self.engine.starts, [])
        axes = self.axes()
        self.assertIsNone(axes["runtime_id"])
        # The owner's own axis: fenced with nothing attached to stop.
        self.assertIn(axes["execution_runtime"],
                      ("not-started", "cancel-requested"))
        self.assertIsNotNone(axes["assignment"])
        self.assertEqual(self.journalled("attempt.abandon"), 1)
        status = self.report()
        self.assertEqual(status["targets"][0]["state"], "fenced-unstarted")
        self.assertEqual(status["shutdown"], "complete")
        # A LATE LAUNCH CANNOT REOPEN IT: the assignment is fenced at the
        # Authority, so the composition's own start refuses and the engine
        # is never asked to run anything.
        unready.stop()
        attempt = self.attempting(self.jobs, self.stage_id)
        from baton_v12.job_manager import job_of
        with self.assertRaises(ContractRefusal):
            self.composed.launch(attempt, job_of(self.jobs, "job-a"))
        self.assertEqual(self.engine.starts, [])
        for _ in range(2):
            self.tick()
        self.assertEqual(self.journalled("attempt.abandon"), 1)
        self.assertEqual(self.engine.starts, [])

    def test_a_queued_job_is_retired_and_the_pool_reserves_nothing(self):
        self.cancel()
        for _ in range(3):
            self.tick()
        self.assertEqual(self.state(), "queued")
        self.assertEqual(self.engine.starts, [])
        from baton_v12.job_manager import scheduler
        self.assertEqual(scheduler.allocation_rows(self.jobs), [])
        status = self.report()
        self.assertEqual(status["targets"][0]["state"],
                         "retired-before-admission")
        self.assertEqual(status["shutdown"], "complete")

    def test_a_direct_owner_call_and_the_pass_converge_on_one_fence(self):
        self.drive(self.jobs, self.composed, "implementation", "waiting")
        self.cancel()
        self.composed.cancel_attempt(attempt_id=self.attempt_id(),
                                     reason=REASON)
        self.assertEqual(self.journalled("attempt.cancel"), 1)
        self.tick()
        # The pass finds the owner's axis already ordered and places no
        # second order of its own; the report reads the axis, not a record.
        self.assertEqual(self.journalled("attempt.cancel"), 1)
        self.assertEqual(cancellation.targets_of(self.jobs, "job-a"), [])
        self.assertEqual(self.report()["targets"][0]["state"], "ordered")
        self.assertEqual(len(self.stops()), 1)

    def test_a_request_with_no_serving_manager_stays_pending_until_one_serves(self):
        self.drive(self.jobs, self.composed, "implementation", "waiting")
        self.cancel()
        # Nothing ticks: the honest report is a pending target under the
        # bound, never cessation.
        self.assertEqual(self.report(at=SOON)["targets"][0]["state"],
                         "pending")
        self.assertEqual(self.report(at=MUCH_LATER)["shutdown"], "unresolved")
        self.assertEqual(self.stops(), [])
        # A later serving process picks the committed request up.
        self.tick()
        self.assertEqual(self.report()["targets"][0]["state"], "ordered")

    def refusing_stop(self, count=1):
        """The reviewer's counterexample: the adapter's stop refuses `count`
        times at the real boundary, then behaves."""
        original = oci.OciAdapter.stop
        remaining = [count]

        def stop(adapter, request):
            if remaining[0] > 0:
                remaining[0] -= 1
                raise ContractRefusal("refused", "precondition",
                                      "injected transient stop refusal")
            return original(adapter, request)

        held = mock.patch.object(oci.OciAdapter, "stop", stop)
        held.start()
        self.addCleanup(held.stop)

    def test_a_transient_stop_refusal_is_retried_until_the_owner_records_the_order(self):
        """Review 2026-11-18T19-56-12Z P1, reproduced and closed."""
        self.drive(self.jobs, self.composed, "implementation", "waiting")
        self.cancel()
        self.refusing_stop(1)
        first = self.tick()
        self.assertEqual([(one["effect"], one["outcome"])
                          for one in first["cancelled"]],
                         [("order-cessation", "deferred")])
        self.assertEqual(self.stops(), [])
        # THE OWNER'S OWN ACCOUNT: the fence crossed, the stop did not.
        recorded = attempt_cessation_outcome_of(self.control, self.attempt_id(),
                                                "cancellation")
        self.assertEqual(recorded["outcome"], "stop-failed")
        self.assertEqual(self.axes()["execution_runtime"], "cancel-requested")
        status = self.report()
        self.assertEqual(status["targets"][0]["state"], "order-failed")
        self.assertEqual(status["targets"][0]["orders"], [])
        self.assertEqual(status["targets"][0]["cessation"]["outcome"],
                         "stop-failed")
        self.assertNotEqual(status["shutdown"], "complete")
        second = self.tick()
        self.assertEqual([(one["effect"], one["outcome"])
                          for one in second["cancelled"]],
                         [("order-cessation", "ordered")])
        self.assertEqual(len(self.stops()), 1)
        self.assertEqual(self.journalled("attempt.cancel"), 1)
        recorded = attempt_cessation_outcome_of(self.control, self.attempt_id(),
                                                "cancellation")
        self.assertEqual(recorded["outcome"], "ordered")
        status = self.report()
        self.assertEqual(status["targets"][0]["state"], "ordered")
        self.assertEqual(len(status["targets"][0]["orders"]), 1)
        for _ in range(3):
            self.assertNotIn("cancelled", self.tick())
        self.assertEqual(len(self.stops()), 1)

    def interrupted_start(self):
        """Review 2026-11-18T20-12-59Z: the adapter's start completes and
        its reply is lost before the attempt owner attaches the identity.
        Durable state: `start-requested`, no runtime attached, the
        token-bound fake container exists."""
        class Interrupted(BaseException):
            pass

        original = oci.OciAdapter.start

        def lost_reply(adapter, request, **named):
            original(adapter, request, **named)
            raise Interrupted()

        with mock.patch.object(oci.OciAdapter, "start", lost_reply):
            with self.assertRaises(Interrupted):
                self.drive(self.jobs, self.composed, "implementation",
                           "waiting")
        axes = self.axes()
        self.assertIsNone(axes["runtime_id"])
        self.assertEqual(axes["execution_runtime"], "start-requested")
        self.assertEqual(len(self.engine.starts), 1)
        return axes

    def test_an_interrupted_start_reply_is_cancelled_through_the_stop_owner(self):
        """Review 2026-11-18T20-12-59Z P1, reproduced and closed: an in-flight
        start is not `never started`; the exact-generation owner resolves the
        token-bound runtime and stops it."""
        self.interrupted_start()
        self.cancel()
        self.assertEqual(self.report()["targets"][0]["state"], "pending")
        report = self.tick()
        self.assertEqual([(one["effect"], one["outcome"])
                          for one in report["cancelled"]],
                         [("order-cessation", "ordered")])
        self.assertEqual(len(self.stops()), 1)
        self.assertEqual(self.journalled("attempt.cancel"), 1)
        self.assertEqual(self.journalled("attempt.abandon"), 0)
        recorded = attempt_cessation_outcome_of(self.control, self.attempt_id(),
                                                "cancellation")
        self.assertEqual(recorded["outcome"], "ordered")
        self.assertEqual(recorded["runtime_id"], self.stops()[0][-1])
        status = self.report()
        self.assertEqual(status["targets"][0]["state"], "ordered")
        self.assertEqual(len(status["targets"][0]["orders"]), 1)
        self.assertNotEqual(status["shutdown"], "complete")
        # THE HOLD IS RETAINED: the token is not returned by an order.
        [record] = [one for one in attempts.runtime_recovery_inventory(self.control)
                    if one["attempt_id"] == self.attempt_id()]
        self.assertFalse(record["token"]["returned"])
        for _ in range(3):
            self.assertNotIn("cancelled", self.tick())
        self.assertEqual(len(self.stops()), 1)

    def test_an_interrupted_start_is_still_cancelled_after_a_restart_and_late_attachment(self):
        self.interrupted_start()
        self.cancel()
        self.composed.close()
        self.jobs, self.control, self.composed = self.serving()
        report = self.tick()
        self.assertEqual([(one["effect"], one["outcome"])
                          for one in report.get("cancelled", [])],
                         [("order-cessation", "ordered")])
        self.assertEqual(len(self.stops()), 1)
        self.assertEqual(self.journalled("attempt.cancel"), 1)
        ordered = self.stops()[0][-1]
        # A LATE ATTACHMENT OF THE SAME IDENTITY changes nothing: the owner's
        # record names it, so later ticks replay rather than re-fence.
        axes = self.axes()
        self.assertIn(axes["runtime_id"], (None, ordered))
        for _ in range(2):
            self.assertNotIn("cancelled", self.tick())
        self.assertEqual(self.journalled("attempt.cancel"), 1)
        self.assertEqual(len(self.stops()), 1)
        status = self.report()
        self.assertIn(status["targets"][0]["state"],
                      ("ordered", "held-unknown"))
        self.assertNotEqual(status["shutdown"], "complete")
        self.assertEqual(status["requested_at"], fixtures.NOW)

    def test_the_failed_stop_state_survives_a_restart_and_is_retried(self):
        self.drive(self.jobs, self.composed, "implementation", "waiting")
        self.cancel()
        self.refusing_stop(1)
        self.tick()
        self.assertEqual(self.stops(), [])
        self.assertEqual(self.report()["targets"][0]["state"], "order-failed")
        self.composed.close()
        self.jobs, self.control, self.composed = self.serving()
        report = self.tick()
        self.assertEqual([(one["effect"], one["outcome"])
                          for one in report.get("cancelled", [])],
                         [("order-cessation", "ordered")])
        self.assertEqual(len(self.stops()), 1)
        self.assertEqual(self.journalled("attempt.cancel"), 1)
        self.assertEqual(self.report()["targets"][0]["state"], "ordered")
        self.assertEqual(self.report()["requested_at"], fixtures.NOW)

    def test_a_restarted_composition_replays_the_order_rather_than_re_fencing(self):
        self.drive(self.jobs, self.composed, "implementation", "waiting")
        self.cancel()
        self.tick()
        self.assertEqual(self.journalled("attempt.cancel"), 1)
        self.composed.close()
        self.jobs, self.control, self.composed = self.serving()
        self.tick()
        self.tick()
        self.assertEqual(self.journalled("attempt.cancel"), 1)
        self.assertEqual(len(cancellation.targets_of(self.jobs, "job-a")), 1)
        # The restarted composition re-observes the runtime it did not start;
        # an uncertain observation is an honest hold, never cessation.
        status = self.report()
        self.assertIn(status["targets"][0]["state"],
                      ("ordered", "held-unknown"))
        self.assertNotEqual(status["shutdown"], "complete")
        self.assertEqual(status["requested_at"], fixtures.NOW)


class TheCommandBoundary(InstalledCancellation):

    def test_exact_replay_changed_reason_and_unknown_job(self):
        self.drive(self.jobs, self.composed, "implementation", "waiting")
        first = self.cancel()
        self.assertEqual(self.cancel(at=MUCH_LATER)["request"],
                         first["request"])
        with self.assertRaises(ContractRefusal) as caught:
            self.cancel(reason="a different account")
        self.assertEqual(caught.exception.code, "operation-collision")
        with self.assertRaises(ContractRefusal):
            self.cancel(job_id="job-nobody")
        with self.assertRaises(ContractRefusal):
            self.call("cancel-status", job_id="job-nobody")
        self.assertEqual(cancellation.fence_of(self.jobs, "job-a"),
                         first["request"])

    def test_a_blank_reason_and_a_foreign_instance_refuse_before_writes(self):
        before = self.logical()
        with self.assertRaises(ContractRefusal):
            self.cancel(reason="   ")
        changed = copy.deepcopy(self.deployment_document)
        changed["authority_uuid"] = "f" * 32
        Path(self.places["deployment"]).write_text(json.dumps(changed))
        with self.assertRaises(ContractRefusal):
            self.cancel()
        Path(self.places["deployment"]).write_text(json.dumps(self.deployment_document))
        Path(self.places["command"]).write_text("replaced package")
        with self.assertRaises(instance.InstanceRefusal):
            self.cancel()
        self.assertEqual(self.logical(), before)
        self.assertIsNone(cancellation.fence_of(self.jobs, "job-a"))

    def test_cancel_status_opens_nothing_writable_and_changes_nothing(self):
        self.drive(self.jobs, self.composed, "implementation", "waiting")
        self.assertIsNone(self.report())
        self.cancel()
        before = self.logical()
        with mock.patch.object(JobStore, "open",
                               side_effect=AssertionError("writable Jobs")), \
                mock.patch.object(ControlStore, "open",
                                  side_effect=AssertionError("writable control")):
            answer = self.call("cancel-status")
        self.assertEqual(answer["request"]["reason"], REASON)
        self.assertEqual(answer["cancellation"]["targets"][0]["state"],
                         "pending")
        self.assertEqual(self.logical(), before)

    def test_the_packaged_manager_dispatch_reaches_both_verbs(self):
        output = io.StringIO()
        with mock.patch.object(job_manager, "_utc_clock",
                               return_value=lambda: fixtures.NOW), \
                mock.patch("sys.stdout", output):
            self.assertEqual(stack_command.main(
                ["manager", "cancel-status", "--instance",
                 self.places["instance"], "--job", "job-a"]), 0)
            self.assertIsNone(json.loads(output.getvalue())["cancellation"])
            output.seek(0)
            output.truncate()
            self.assertEqual(stack_command.main(
                ["manager", "cancel-job", "--instance",
                 self.places["instance"], "--job", "job-a", "--reason",
                 REASON]), 0)
        answer = json.loads(output.getvalue())
        self.assertEqual(answer["request"]["reason"], REASON)
        self.assertEqual(answer["cancellation"]["targets"][0]["state"],
                         "retired-before-admission")
        with self.assertRaises(SystemExit):
            stack_command.main(["manager", "cancel-job", "--instance",
                                self.places["instance"], "--job", "job-a"])


class ManualOperatorCommands(InstalledCancellation):
    def test_finish_phase_authenticates_installed_owner_before_writable_open(self):
        from baton_v12.authority import Authority
        from baton_v12.job_manager import manual_decision

        inputs = Path(self.places["install_inputs"])
        inputs.write_text(json.dumps({"owner_participant": "baton.slaw"}))
        with Authority.open(self.authority_path, expected_authority_uuid=self.config["authority_uuid"]) as authority:
            authority.bind_endpoint("baton.slaw", "principal:installed-owner")
        argv = ["manager", "finish-phase", "--instance", self.places["instance"],
                "--job", "study", "--phase", "routing", "--outcome", "failure"]
        with mock.patch.object(manual_decision, "finish", return_value={"outcome": "failure"}) as finish:
            with redirect_stdout(io.StringIO()):
                self.assertEqual(stack_command.main(argv), 0)
            self.assertEqual(finish.call_args.args[1:], ("study", "routing", "failure"))
            self.assertEqual(finish.call_args.kwargs["actor"], {
                "authority_uuid": self.config["authority_uuid"], "participant": "baton.slaw",
                "principal": "principal:installed-owner", "uid": os.getuid()})
        with mock.patch.object(JobStore, "open") as opened:
            with mock.patch("tools.manual_job.os.getuid", return_value=os.getuid() + 1):
                with self.assertRaisesRegex(ContractRefusal, "owner"):
                    stack_command.main(argv)
            inputs.write_text("{}")
            with self.assertRaisesRegex(ContractRefusal, "no configured owner"):
                stack_command.main(argv)
            foreign = Path(self.root) / "other-inputs"
            inputs.rename(foreign)
            inputs.symlink_to(foreign)
            with self.assertRaisesRegex(ContractRefusal, "owner-controlled"):
                stack_command.main(argv)
            opened.assert_not_called()

    def test_create_append_select_and_close_over_installed_command(self):

        def run(command, *operands):
            output = io.StringIO()
            with redirect_stdout(output), mock.patch.object(job_manager, "_utc_clock", return_value=lambda: fixtures.NOW):
                code = stack_command.main(["manager", command, "--instance", self.places["instance"], *operands])
            self.assertEqual(code, 0, output.getvalue())
            return json.loads(output.getvalue())

        job_id = "manual-research"
        document = Path(self.root) / "request.json"
        document.write_text(json.dumps({"job_id": job_id, "scope": ["src"], "wall_seconds": 60}))
        created = run("create", "--mode", "manual", "--document", str(document))
        self.assertEqual(created["job_id"], job_id)
        from baton_v12 import provider_policy
        from baton_v12.authority import Authority
        from baton_v12.contracts import digest
        from baton_v12.job_manager import research
        from tests.manager import provider_fixtures
        from tools import bootstrap, research_authorization, single_worker

        worker = self.worker("research", participant="baton.research")
        chosen, identities = provider_fixtures.identities()
        profile = dict(identities["runtime_profile"], image_digest=self.config["image_digest"], network=self.config["network"])
        adapter = provider_policy.adapter(chosen, network=self.config["network"], research=True)
        manifest = worker["deployment"]["input_manifest"]
        manifest.update(outputs=research.outputs(), runtime_profile_digest=digest(profile), tool_policy_digest=digest(provider_policy.POLICY))
        manifest.pop("manifest_digest")
        manifest["manifest_digest"] = digest(manifest)
        auth = Authority.open(self.authority_path, expected_authority_uuid=self.config["authority_uuid"])
        self.addCleanup(auth.dispose)
        worker["deployment"].update(schema=single_worker.PROVIDER_CONFIG_SCHEMA, provider_context=None, verifier_layout=None,
                                    profile_name=profile["name"], profile_digest=digest(profile),
                                    principal=auth.principal_of("baton.research"),
                                    adapter_name="report-only-claude", adapter_digest=digest(adapter),
                                    credential_slots=["claude"], credential_profile={"claude": {"provider": "fixture", "reference": "test-key"}},
                                    provider_home_root=str(Path(self.root)/"job-work"),
                                    provider_contract={"selection": chosen, "runtime_profile": profile, "adapter": adapter})
        self.deployment_document["workers"].append(worker)
        Path(self.places["deployment"]).write_text(json.dumps(self.deployment_document))
        phase = {"kind": "research", "scope": ["src"], "statement": "Inspect the routing code.", "depends_on": []}
        document.write_text(json.dumps(phase))
        identity = ("--job", job_id, "--phase", "routing")
        added = run("add-phase", *identity, "--document", str(document))
        self.assertEqual(added["phase"], "routing")
        deployment_path = Path(self.places["deployment"])
        deployed = deployment_path.read_bytes()
        deployment_path.write_text("{}")
        self.assertEqual(run("add-phase", *identity, "--document", str(document)), added)
        deployment_path.write_bytes(deployed)
        from baton_v12.job_manager import manual
        def phase_pins(name):
            return manual.phase_for_execution(self.jobs, manual.execution_job_id(job_id, name))["document"]
        pinned = phase_pins("routing")
        self.assertEqual(pinned["source_commit"], self.base)
        self.assertEqual(pinned["profile_digest"], worker["deployment"]["profile_digest"])
        self.assertEqual(pinned["policy_digest"], worker["deployment"]["policy_digest"])
        for member in ("profile_digest", "input_digest"):
            with self.subTest(member=member):
                document.write_text(json.dumps(dict(phase, **{member: "sha256:" + "f" * 64})))
                with self.assertRaisesRegex(ContractRefusal, "no configured research worker"):
                    run("add-phase", "--job", job_id, "--phase", "foreign", "--document", str(document))
        document.write_text(json.dumps(dict(phase, statement="Inspect the storage code.", scope=["src/storage"])))
        run("add-phase", "--job", job_id, "--phase", "storage", "--document", str(document))
        self.assertNotEqual(phase_pins("storage")["input_digest"], pinned["input_digest"])
        selected = run("start-phase", *identity)
        self.assertEqual(run("start-phase", *identity), selected)
        published = io.StringIO()
        job_manager.main(["--store", self.job_path, "--incarnation", "manual-observer",
                          "--authority-uuid", self.config["authority_uuid"], "status"],
                         stream=published, clock=lambda: fixtures.NOW)
        projection = json.loads(published.getvalue())
        self.assertEqual(projection["schema"], "baton.v12.job-status/10")
        manual_job = next(job for job in projection["jobs"] if job["job_id"] == job_id)
        self.assertEqual((manual_job["mode"], manual_job["lifecycle"]), ("MANUAL", "open"))
        by_id = {one["stage_id"]: one for one in manual_job["stages"]}
        self.assertEqual(by_id[job_id + "/routing"]["selected_at"], selected["recorded_at"])
        self.assertIsNone(by_id[job_id + "/storage"]["selected_at"])
        execution = manual.execution_job_id(job_id, "routing")
        self.assertEqual(pinned["work_origin"], "generated")
        self.assertIsNone(auth.work_creation(pinned["work_id"]))
        with self.assertRaisesRegex(ContractRefusal, "handles the configured research route"):
            research_authorization.ensure_phase_work(auth, execution, pinned, [worker])
        self.assertIsNone(auth.work_creation(pinned["work_id"]))
        auth.add_route_handler(bootstrap.ROUTES["research"], worker["deployment"]["participant"])
        grants = auth.grants_of(worker["deployment"]["participant"])
        granted = research_authorization.ensure_phase_work(auth, execution, pinned, [worker])
        receipt = auth.work_creation(pinned["work_id"])
        self.assertEqual(granted["scope"], "scope:" + execution)
        self.assertEqual(granted["route"], bootstrap.ROUTES["research"])
        self.assertEqual(research_authorization.ensure_phase_work(auth, execution, pinned, [worker]), granted)
        self.assertEqual(auth.work_creation(pinned["work_id"]), receipt)
        self.assertEqual(auth.grants_of(worker["deployment"]["participant"]), grants)
        self.assertNotEqual(pinned["work_id"], phase_pins("storage")["work_id"])
        storage = phase_pins("storage")
        auth.create_work(storage["work_id"], bootstrap.ROUTES["research"], contract="v12-assignment-1",
                         operation_id="belongs-to-another-operation")
        with self.assertRaises(ContractRefusal):
            research_authorization.ensure_phase_work(auth, manual.execution_job_id(job_id, "storage"), storage, [worker])
        self.assertEqual(auth.work_creation(storage["work_id"])["operation_id"], "belongs-to-another-operation")
        with self.assertRaisesRegex(ContractRefusal, "unsettled"):
            run("close-job", "--job", job_id)
        self.assertEqual(self.engine.starts, [])
        # The same CLI closes an empty open Job. The manager/worker acceptance
        # exercises closure after a real retained result.
        document.write_text(json.dumps({"job_id": "empty-research", "scope": ["src"], "wall_seconds": 60}))
        run("create", "--mode", "manual", "--document", str(document))
        self.assertEqual(run("close-job", "--job", "empty-research")["action"], "close-job")
