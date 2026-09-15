"""W156162: a Job's configured ceilings, carried into a container and APPLIED.

WHAT THIS MODULE IS FOR. The Job owner's module proves what a Job may configure;
the manager's module proves the launch carrier states it and is adopted by its
exact bytes. Neither shows a command actually running under a configured number,
and until something does, the feature is configuration that changes nothing.

These cases close that gap at the two ends that matter: the container's own entry
reader accepts a `/3` delivery and refuses a malformed one, and the adapter hands
the CONFIGURED seconds to the provider turn and to the verification command --
with the defaults kept for a launch that carries no Job context at all.

NO PROVIDER RUNS HERE. The subprocess boundary is captured, which is what the
plan asks for: "Injected timeout verifies argument selection and failure
handling, not observed OS descendant termination."
"""

import json
import os
import shutil
import subprocess
import tempfile
import sys
import unittest
from types import SimpleNamespace

# THE IMAGE'S OWN MODULES, on the path the sibling suites already declare.
# `claude_agent` imports `source_profiles` as a top-level name because inside
# the container it is one, so the package directory goes on the path beside the
# worker directory -- exactly as `tests/tools/test_single_worker.py` does it.
_WORKER = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))), "worker")
_PACKAGE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))), "src", "baton_v12")
for _place in (_WORKER, _PACKAGE):
    if _place not in sys.path:
        sys.path.insert(0, _place)

import baton_worker                                             # noqa: E402
import claude_agent                                             # noqa: E402
import integration_contract                                     # noqa: E402

from baton_v12.job_manager import execution_limits as limits    # noqa: E402
from baton_v12.job_manager import submission                     # noqa: E402
from baton_v12.worker_manager import attempt_runtime_of         # noqa: E402
from tests.job_manager import fixtures as job_fixtures           # noqa: E402
from baton_v12.worker_manager import launch                     # noqa: E402


def configured(**requested):
    """One Job's effective configuration, resolved by its own owner."""
    return limits.resolved(requested, limits.CURRENT_GENERATION)


def delivery(**requested):
    """A `/3` launch document, authored by the manager's own owner."""
    held = configured(**requested)
    return launch.launch_document(
        session="session-one", contract="a contract", role="implementation",
        transport=None,
        job_execution={
            "job_id": "job-a", "attempt_id": "attempt-1",
            "job_input_digest": "sha256:" + "1" * 64,
            "job_policy_digest": "sha256:" + "2" * 64,
            "runtime_input_digest": "sha256:" + "3" * 64,
            "runtime_policy_digest": "sha256:" + "2" * 64,
            "execution_limits": held,
            "execution_limits_digest": launch._digest(held)})


class TheContainerEntryReadsTheThirdVersion(unittest.TestCase):
    """The worker is the untrusted side: it proves what it was handed rather
    than trusting a file it cannot check."""

    def launched(self, document):
        return baton_worker.launched(document, place="/run/baton/launch.json")

    def refused(self, document):
        with self.assertRaises(baton_worker.WorkerFault) as caught:
            self.launched(document)
        return str(caught.exception)

    def test_a_third_version_delivery_is_read(self):
        held = self.launched(delivery(provider_turn_seconds=60))
        self.assertEqual(held["schema"], "baton.worker-launch/3")
        self.assertEqual(
            held["job_execution"]["execution_limits"]["boundaries"]
            ["provider_turn"]["seconds"], 60)

    def test_the_earlier_versions_are_read_exactly_as_before(self):
        for document in (
                launch.launch_document(session="s", contract="c",
                                       role="implementation"),
                launch.launch_document(
                    session="s", contract="c", role="implementation",
                    transport="baton.worker-exchange/1")):
            with self.subTest(schema=document["schema"]):
                self.assertEqual(self.launched(document), document)

    def test_a_context_that_is_not_a_document_is_refused(self):
        held = delivery()
        held["job_execution"] = "60"
        self.assertIn("not a document", self.refused(held))

    def test_a_missing_context_member_is_refused(self):
        held = delivery()
        del held["job_execution"]["runtime_input_digest"]
        self.assertIn("missing runtime_input_digest", self.refused(held))

    def test_a_seal_that_does_not_cover_its_contents_is_refused(self):
        """The container cannot ask which Job resolved these numbers; what it
        can do is refuse a document whose seal does not cover them."""
        held = delivery(provider_turn_seconds=60)
        held["job_execution"]["execution_limits"]["boundaries"][
            "provider_turn"]["seconds"] = 9
        self.assertIn("do not match their own seal", self.refused(held))

    def test_a_boolean_bound_is_refused_before_it_becomes_one_second(self):
        held = delivery()
        held["job_execution"]["execution_limits"]["boundaries"][
            "provider_turn"]["seconds"] = True
        held["job_execution"]["execution_limits_digest"] = launch._digest(
            held["job_execution"]["execution_limits"])
        self.assertIn("whole number of seconds", self.refused(held))

    def test_a_bound_outside_the_supported_range_is_refused(self):
        for seconds in (0, baton_worker.MAX_LAUNCH_SECONDS + 1):
            with self.subTest(seconds=seconds):
                held = delivery()
                held["job_execution"]["execution_limits"]["boundaries"][
                    "ordinary_verification"]["seconds"] = seconds
                held["job_execution"]["execution_limits_digest"] = \
                    launch._digest(
                        held["job_execution"]["execution_limits"])
                self.assertIn("whole number of seconds",
                              self.refused(held))

    def test_an_unknown_transport_is_refused(self):
        """[P2]: `transport='unknown/channel'` was accepted, and `main` then
        treated it as a one-shot launch -- a container deciding for itself that
        it had been told nothing."""
        held = delivery()
        held["transport"] = "unknown/channel"
        self.assertIn("channel nothing is listening to", self.refused(held))

    def test_a_non_text_job_identity_is_refused(self):
        held = delivery()
        held["job_execution"]["job_id"] = False
        self.assertIn("not bounded non-empty text", self.refused(held))

    def test_foreign_units_are_refused(self):
        """A container that reads somebody else's units hands a command sixty
        times the bound the operator wrote."""
        held = delivery()
        held["job_execution"]["execution_limits"]["units"] = "minutes"
        held["job_execution"]["execution_limits_digest"] = launch._digest(
            held["job_execution"]["execution_limits"])
        self.assertIn("hands a command 'seconds'", self.refused(held))

    def test_a_missing_boundary_is_refused_rather_than_defaulted(self):
        held = delivery(provider_turn_seconds=60)
        held["job_execution"]["execution_limits"]["boundaries"].pop(
            "host_verification")
        held["job_execution"]["execution_limits_digest"] = launch._digest(
            held["job_execution"]["execution_limits"])
        self.assertIn("missing host_verification", self.refused(held))

    def resealed(self, change):
        """One mutation of the configuration, RESEALED, so the seal check is
        never what refuses it."""
        held = delivery(provider_turn_seconds=60)
        change(held["job_execution"]["execution_limits"])
        held["job_execution"]["execution_limits_digest"] = launch._digest(
            held["job_execution"]["execution_limits"])
        return self.refused(held)

    def test_a_boolean_requested_setting_is_refused(self):
        """Review 2026-09-13T02:51:29Z: a seal proves the bytes were not
        changed after somebody wrote them; it says nothing about whether what
        they wrote is a configuration this container can act on."""
        self.assertIn("whole number of seconds", self.resealed(
            lambda one: one["requested"].update(provider_turn_seconds=True)))

    def test_a_requested_setting_this_worker_does_not_name_is_refused(self):
        self.assertIn("nobody here honours", self.resealed(
            lambda one: one["requested"].update(cumulative_seconds=300)))

    def test_a_boundary_missing_its_origin_is_refused(self):
        self.assertIn("missing origin", self.resealed(
            lambda one: one["boundaries"]["provider_turn"].pop("origin")))

    def test_a_boundary_carrying_an_unknown_member_is_refused(self):
        self.assertIn("unexpected remaining_seconds", self.resealed(
            lambda one: one["boundaries"]["provider_turn"].update(
                remaining_seconds=10)))

    def test_an_origin_this_worker_cannot_name_is_refused(self):
        """A bound whose origin this program cannot name is one it cannot
        explain to whoever reads a failure it caused."""
        self.assertIn("worker names job, compatibility", self.resealed(
            lambda one: one["boundaries"]["provider_turn"].update(
                origin="somewhere")))

    def test_a_boundary_naming_a_foreign_setting_is_refused(self):
        self.assertIn("answers to 'provider_turn_seconds'", self.resealed(
            lambda one: one["boundaries"]["provider_turn"].update(
                setting="cumulative_seconds")))

    def test_a_boundary_naming_the_other_honoured_setting_is_refused(self):
        """Review 2026-09-13T02:59:22Z, and the sharper half of the case above:
        a foreign name was already refused, but `verification_command_seconds`
        is a setting this worker DOES honour, so a resealed provider_turn could
        claim the Job's verification ceiling had moved its provider turn. Which
        setting a boundary answers to is fixed HERE, not in the delivery."""
        self.assertIn("not something a delivery gets to say", self.resealed(
            lambda one: one["boundaries"]["provider_turn"].update(
                setting="verification_command_seconds")))

    def test_a_boundary_reporting_seconds_its_request_does_not_support(self):
        """Every member was well formed and the document still contradicted
        itself: 60 requested, 30 enforced, sealed over the pair."""
        self.assertIn("contradicts itself", self.resealed(
            lambda one: one["boundaries"]["provider_turn"].update(seconds=30)))

    def test_an_explicitly_requested_boundary_claiming_the_default_origin(self):
        """The Job asked for 60 and the boundary calls itself preserved. The
        seconds still say 60, so only the pair of them is wrong -- which is why
        origin is checked against the request rather than believed."""
        self.assertIn("contradicts itself", self.resealed(
            lambda one: one["boundaries"]["provider_turn"].update(
                origin="compatibility")))

    def test_an_unrequested_boundary_claiming_the_job_asked_for_it(self):
        """And the other direction: nothing in `requested` names this
        boundary's setting, so it cannot be the Job's."""
        self.assertIn("contradicts itself", self.resealed(
            lambda one: one["boundaries"]["ordinary_verification"].update(
                origin="job")))

    def test_an_unrequested_boundary_departing_from_its_own_default(self):
        """A preserved boundary that enforces something other than the default
        it carries. Nothing outside the document is consulted to catch it: the
        two members it already states disagree."""
        self.assertIn("contradicts itself", self.resealed(
            lambda one: one["boundaries"]["ordinary_verification"].update(
                seconds=45)))

    def test_the_consistent_configuration_this_work_produces_is_accepted(self):
        """The negatives above are only worth anything if the real document
        passes all of them, so the production composition is run through the
        same entry rather than a fixture shaped like it."""
        held = delivery(provider_turn_seconds=60)
        self.assertEqual(self.launched(held), held)
        for name, one in held["job_execution"]["execution_limits"][
                "boundaries"].items():
            with self.subTest(boundary=name):
                self.assertEqual(one["setting"],
                                 baton_worker.LAUNCH_BOUNDARY_SETTING[name])

    def test_an_unknown_version_is_still_refused(self):
        """The module's own rule is unchanged: an unknown schema is held to
        `/1`'s member set so the refusal names the VERSION rather than the
        members, which is why this case carries a `/1`-shaped document."""
        held = launch.launch_document(session="s", contract="c",
                                      role="implementation")
        held["schema"] = "baton.worker-launch/9"
        self.assertIn("another generation", self.refused(held))

    def test_a_third_version_document_missing_its_context_is_refused(self):
        """And a /3 that lost its Job context is refused as the version it
        claims to be rather than read as an earlier one."""
        held = delivery()
        del held["job_execution"]
        self.assertIn("missing job_execution", self.refused(held))


class TheAdapterHandsTheCommandWhatWasConfigured(unittest.TestCase):
    """The end of the chain, and the reason the Work exists: a configured
    60 seconds is what the provider turn and the verification command GET."""

    def agent(self, seen):
        held = claude_agent.ClaudeAgent.__new__(claude_agent.ClaudeAgent)
        held._seen = seen
        return held

    def test_a_configured_provider_turn_is_the_one_handed_over(self):
        held = self.agent(baton_worker.launched(
            delivery(provider_turn_seconds=60),
            place="/run/baton/launch.json"))
        self.assertEqual(
            held._bound(held._seen, "provider_turn",
                        claude_agent.PROVIDER_SECONDS), 60)

    def test_a_configured_verification_reaches_the_ordinary_command(self):
        held = self.agent(baton_worker.launched(
            delivery(verification_command_seconds=45),
            place="/run/baton/launch.json"))
        self.assertEqual(
            held._bound(held._seen, "ordinary_verification",
                        claude_agent.VERIFICATION_SECONDS), 45)
        # AND THE PROVIDER TURN IS UNTOUCHED BY IT.
        self.assertEqual(
            held._bound(held._seen, "provider_turn",
                        claude_agent.PROVIDER_SECONDS),
            claude_agent.PROVIDER_SECONDS)

    def test_a_job_that_configured_nothing_gets_its_runners_defaults(self):
        held = self.agent(baton_worker.launched(
            delivery(), place="/run/baton/launch.json"))
        self.assertEqual(
            held._bound(held._seen, "provider_turn",
                        claude_agent.PROVIDER_SECONDS), 3600)
        self.assertEqual(
            held._bound(held._seen, "ordinary_verification",
                        claude_agent.VERIFICATION_SECONDS), 900)

    def test_a_launch_with_no_job_behind_it_keeps_the_module_default(self):
        """The default is for a delivery carrying no Job context at all -- a
        `/1` or `/2` launch. A Job that configured nothing resolves to the same
        numbers at its own owner and delivers them explicitly."""
        for seen in (None, {}, launch.launch_document(
                session="s", contract="c", role="implementation")):
            with self.subTest(seen=type(seen).__name__):
                held = self.agent(seen)
                self.assertEqual(
                    held._bound(seen, "provider_turn",
                                claude_agent.PROVIDER_SECONDS),
                    claude_agent.PROVIDER_SECONDS)

    def production(self, seen):
        """A real adapter over an injected run seam, as `__init__` documents.

        Review 2026-09-13T02:41:57Z [P2]: the first form of the case below
        called a LOCAL runner directly after `_bound` and asserted that
        runner's own exception. It never injected anything into the adapter and
        never entered `_provider` or `_verify`, so it would have passed against
        the module constants and against broken timeout handling alike -- a test
        that exercised its own fixture. This drives the production methods.

        Only the provider's environment preparation is substituted, because it
        reads a credential home this case has no business composing.
        """
        captured = []

        def runner(argv, **options):
            captured.append(options["timeout"])
            if self.mode == "timeout":
                raise subprocess.TimeoutExpired(argv, options["timeout"])
            if self.mode == "start-error":
                raise FileNotFoundError("injected runner start failure")
            return SimpleNamespace(returncode=0)

        held = claude_agent.ClaudeAgent(run=runner)
        held._revalidated_environment = lambda scratch, env: env
        held._seen = seen
        return held, captured

    mode = "success"

    def test_the_configured_seconds_reach_the_real_provider_and_verifier(self):
        """The end of the chain, through the adapter's own methods."""
        task = {"verification": ["fake-verification"]}
        for requested, expected in (
                ({"provider_turn_seconds": 60,
                  "verification_command_seconds": 45}, (60, 45)),
                ({"provider_turn_seconds": 17,
                  "verification_command_seconds": 23}, (17, 23)),
                ({}, (3600, 900))):
            seen = baton_worker.launched(delivery(**requested),
                                         place="/run/baton/launch.json")
            for mode in ("success", "timeout", "start-error"):
                with self.subTest(requested=requested, mode=mode):
                    self.mode = mode
                    held, captured = self.production(seen)
                    held._provider(task, "/unused-candidate",
                                   "/unused-scratch", {},
                                   prompt="fixed fake prompt")
                    held._verify(task, "/unused-candidate", {}, ())
                    self.assertEqual(tuple(captured), expected)

    def test_a_successful_turn_answers_through_the_configured_bound(self):
        """The success path, asserted rather than assumed: the adapter returns
        its ordinary structured answers and the bound it used is the Job's."""
        self.mode = "success"
        held, captured = self.production(baton_worker.launched(
            delivery(provider_turn_seconds=60,
                     verification_command_seconds=45),
            place="/run/baton/launch.json"))
        task = {"verification": ["fake-verification"]}
        provider = held._provider(task, "/unused-candidate",
                                  "/unused-scratch", {},
                                  prompt="fixed fake prompt")
        self.assertTrue(provider["ok"])
        verification = held._verify(task, "/unused-candidate", {}, ())
        self.assertEqual(verification["status"], 0)
        self.assertEqual(tuple(captured), (60, 45))

    def test_a_start_failure_reports_itself_and_not_a_timeout(self):
        """The third path: a runner that cannot start is a start error, and the
        bound it would have been given is still the configured one."""
        self.mode = "start-error"
        held, captured = self.production(baton_worker.launched(
            delivery(provider_turn_seconds=60,
                     verification_command_seconds=45),
            place="/run/baton/launch.json"))
        task = {"verification": ["fake-verification"]}
        provider = held._provider(task, "/unused-candidate",
                                  "/unused-scratch", {},
                                  prompt="fixed fake prompt")
        self.assertFalse(provider["ok"])
        self.assertEqual(provider["failure_reason"],
                         claude_agent.PROVIDER_START_ERROR)
        verification = held._verify(task, "/unused-candidate", {}, ())
        self.assertIsNone(verification["status"])
        self.assertEqual(tuple(captured), (60, 45))

    def test_a_timed_out_turn_reports_the_configured_bound(self):
        """The failure text an operator reads names the number they wrote."""
        self.mode = "timeout"
        held, _captured = self.production(baton_worker.launched(
            delivery(provider_turn_seconds=60,
                     verification_command_seconds=45),
            place="/run/baton/launch.json"))
        provider = held._provider({"verification": ["fake-verification"]},
                                  "/unused-candidate", "/unused-scratch", {},
                                  prompt="fixed fake prompt")
        self.assertFalse(provider["ok"])
        self.assertEqual(provider["failure_reason"],
                         claude_agent.PROVIDER_TIMED_OUT)
        self.assertIn("60s", provider["why"])
        verification = held._verify({"verification": ["fake-verification"]},
                                    "/unused-candidate", {}, ())
        self.assertIsNone(verification["status"])
        self.assertIn("45s", verification["text"])

    def test_a_job_bound_delivery_never_falls_back_to_a_module_default(self):
        """[P1]: a resealed configuration missing a boundary was accepted and
        silently ran for an hour. The entry refuses it, and the adapter refuses
        it too rather than trusting that the entry did."""
        held = delivery(provider_turn_seconds=60)
        held["job_execution"]["execution_limits"]["boundaries"].pop(
            "provider_turn")
        held["job_execution"]["execution_limits_digest"] = launch._digest(
            held["job_execution"]["execution_limits"])
        with self.assertRaises(baton_worker.WorkerFault) as caught:
            baton_worker.launched(held, place="/run/baton/launch.json")
        self.assertIn("missing provider_turn", str(caught.exception))
        # AND THE ADAPTER, handed that document directly, refuses rather than
        # answering 3600 for a Job that asked for 60.
        agent, _captured = self.production(held)
        with self.assertRaises(claude_agent.TaskRefusal):
            agent._bound(held, "provider_turn",
                         claude_agent.PROVIDER_SECONDS)


class TheImportedVerificationUsesItsOwnBoundary(unittest.TestCase):
    """The integration workload's boundary is its own, with its own default,
    and the Git and engine timers are not it."""

    def setUp(self):
        import integration_workload

        self.workload = integration_workload

    def integration(self, **requested):
        """A `/3` delivery for the integration role, whose transport is null
        because this workload consumes no exchange channel."""
        held = configured(**requested)
        document = launch.launch_document(
            session="session-one", contract="a contract",
            role="integrator", transport=None,
            job_execution={
                "job_id": "job-a", "attempt_id": "attempt-1",
                "job_input_digest": "sha256:" + "1" * 64,
                "job_policy_digest": "sha256:" + "2" * 64,
                "runtime_input_digest": "sha256:" + "3" * 64,
                "runtime_policy_digest": "sha256:" + "2" * 64,
                "execution_limits": held,
                "execution_limits_digest": launch._digest(held)})
        return baton_worker.launched(document,
                                     place="/run/baton/launch.json")

    def test_a_configured_verification_reaches_the_imported_boundary(self):
        self.assertEqual(
            self.workload.launch_verification_seconds(
                self.integration(verification_command_seconds=120)), 120)

    def test_a_job_that_configured_nothing_keeps_the_imported_default(self):
        self.assertEqual(
            self.workload.launch_verification_seconds(self.integration()),
            self.workload.VERIFICATION_SECONDS)

    def test_a_launch_with_no_job_behind_it_keeps_the_module_default(self):
        self.assertIsNone(self.workload.launch_verification_seconds(
            launch.launch_document(session="s", contract="c",
                                   role="integrator")))

    def test_the_workload_reads_a_third_version_launch(self):
        self.assertEqual(
            self.workload.checked_launch(self.integration())["role"],
            "integrator")

    def test_a_third_version_selecting_a_transport_is_not_this_workloads(self):
        """This workload runs once from durable files; a delivery selecting an
        exchange channel is not its, which is exactly why `/3` states its
        transport rather than leaving it to be inferred."""
        held = dict(self.integration(), transport="baton.worker-exchange/1")
        with self.assertRaises(Exception) as caught:
            self.workload.checked_launch(held)
        self.assertIn("consumes no exchange transport",
                      str(caught.exception))

    def test_the_configured_bound_reaches_the_verification_runner(self):
        captured = []

        def runner(argv, **options):
            captured.append(options["timeout"])
            raise subprocess.TimeoutExpired(argv, options["timeout"])

        held = self.workload.run_verification(
            "/unused-target", ["fake-verification"], run=runner,
            seconds=self.workload.launch_verification_seconds(
                self.integration(verification_command_seconds=120)))
        self.assertEqual(captured, [120])
        self.assertNotEqual(held["status"], 0)

    def test_an_omitted_bound_keeps_the_runners_own_default(self):
        captured = []

        def runner(argv, **options):
            captured.append(options["timeout"])
            raise subprocess.TimeoutExpired(argv, options["timeout"])

        self.workload.run_verification("/unused-target",
                                       ["fake-verification"], run=runner)
        self.assertEqual(captured, [self.workload.VERIFICATION_SECONDS])


class TheDirectIntegrationCarriesItsJobsOwnCeiling(unittest.TestCase):
    """THE END OF THE CHAIN, over the real composition and the REAL OWNING JOB.

    Review 2026-09-13T03:27:43Z [P1] found the first form of this class proving
    the wrong thing. It submitted a SECOND Job with renamed Works, handed its id
    to `prepare`, and then admitted the WORLD'S ORIGINAL proposal -- so the
    launch said `ceiling-job-a` while the bundle's accepted authority scope said
    `job-a`, and both reached a real provider. That is the cross-Job refusal
    case passing as the positive.

    SO THE POSITIVES CONFIGURE THE REAL OWNING JOB. The world's own submission
    document is arranged, once, at the factory the lifecycle fixture calls --
    before anything is stored, so no immutable intent is edited and no existing
    assertion moves -- and the Job that owns the proposal is the Job whose
    ceiling is carried. The old mismatched setup is retained BELOW as a negative.

    AND THE INJECTION IS AT THE SUBPROCESS BOUNDARY. The PLAN bounds this to
    "injected timeout verifies argument selection and failure handling, not
    observed OS descendant termination", and the first form slept for real. The
    workload's own `subprocess.run` is replaced for the turn, which is the
    normal boundary: everything above it -- the port, the bundle, the entry, the
    contract, the import, the result document -- is the production path.
    """

    # BOTH SETTINGS, because both boundaries are under test here and neither
    # is the module default: 3600 and 1800 are what an unconfigured delivery
    # gets, so a case that asserted either of those would pass with the wiring
    # removed.
    CEILING = 120
    PROVIDER_CEILING = 60

    def setUp(self):
        from tests.tools import test_integration_worker as port_fixture
        from tools import integration_worker

        self.fixture_module = integration_worker
        self.fixture = self._arranged(port_fixture)
        self.attempt = port_fixture.ATTEMPT

    def _arranged(self, port_fixture):
        """The composed fixture, with the WORLD'S OWN Job configured.

        The lifecycle owner builds its store from one module-level document
        factory. Substituting that factory for the duration of this `setUp` --
        and restoring it immediately -- arranges the Job's SUBMITTED intent
        rather than editing a stored row, which is what keeps the ceiling a
        fact the Job owner admitted through its ordinary public path.
        """
        from baton_v12.job_manager import documents
        from tests.job_manager import test_review_driver as lifecycle

        original = lifecycle.one_work_submission

        def configured(submission_id="sub-1"):
            held = json.loads(json.dumps(original(submission_id)))
            held["schema"] = documents.SUBMISSION_SCHEMA
            held["jobs"][0]["execution_limits"] = {
                "verification_command_seconds": self.CEILING,
                "provider_turn_seconds": self.PROVIDER_CEILING}
            return held

        lifecycle.one_work_submission = configured
        try:
            case = port_fixture.TheWholeIntegrationRunsThroughThisPort(
                "test_the_start_composes_the_three_binds_and_answers_running")
            case.setUp()
        finally:
            lifecycle.one_work_submission = original
        self.addCleanup(case.doCleanups)
        return case

    def _port(self, **changed):
        from tools import single_worker

        return self.fixture.port(
            execution_context=single_worker.job_execution_reader(
                self.fixture.world.jobs), **changed)

    def _started(self, job_id="job-a"):
        self.held = self._port()
        self.held.prepare(self.fixture.stage(job_id=job_id), None)
        return self.held, self.fixture.admit(self.held)

    def _materialized(self):
        """The document the PORT wrote, adopted through the launch owner.

        `adopt` is a byte comparison against what the manager would have
        written, so reading it back this way proves the port wrote exactly the
        context its own reader answers.
        """
        return launch.adopt(
            self.fixture.place("launch-home"), attempt_id=self.attempt,
            session="integration-session",
            contract="baton.worker-control/1",
            role=self.fixture_module.LAUNCH_ROLE,
            job_execution=self.held._job_execution(self.attempt)).document

    # -- the owning Job, carried and compared --------------------------------

    def test_the_port_carries_the_job_that_owns_the_proposal(self):
        """The positive, and the thing the first form did not establish: the
        Job in the carrier is the Job the BUNDLE proved owns this work."""
        _, answer = self._started()
        self.assertEqual(answer["outcome"], "running")
        held = self._materialized()
        self.assertEqual(held["schema"], "baton.worker-launch/3")
        self.assertEqual(held["job_execution"]["job_id"], "job-a")
        self.assertEqual(held["job_execution"]["attempt_id"], self.attempt)
        boundary = held["job_execution"]["execution_limits"]["boundaries"][
            "integration_verification"]
        self.assertEqual((boundary["seconds"], boundary["origin"]),
                         (self.CEILING, "job"))
        # AND THE BUNDLE AGREES, which is the comparison that was missing.
        bundle = integration_contract.read_bundle(
            os.path.join(self.fixture.root, "bundles", self.attempt))
        self.assertEqual(
            bundle["evidence"]["authority.json"]["scope"]["job_id"], "job-a")

    def _foreign_job(self):
        """A second, REAL Job, admitted through the Job owner's public entry.

        Renamed throughout -- Jobs, submission and Works -- because admission
        resolves a proposal's Work to exactly one implementation stage and a
        second Job over the world's own Work would make the world's real
        admission ambiguous.
        """
        from baton_v12.job_manager import documents, submit
        from tests.job_manager import fixtures

        held = json.loads(json.dumps(fixtures.submission())
                          .replace("job-", "ceiling-job-")
                          .replace("sub-1", "ceiling-sub-1")
                          .replace("0000000a-W", "0000000c-W"))
        held["schema"] = documents.SUBMISSION_SCHEMA
        held["jobs"][0]["execution_limits"] = {
            "verification_command_seconds": 1}
        submit(self.fixture.world.jobs, held)
        return held["jobs"][0]["job_id"]

    def test_a_carrier_naming_another_job_never_starts(self):
        """THE RETAINED MISMATCH, now a negative. `prepare` is handed a real
        Job that is not the one this proposal belongs to; the bundle resolves
        the owner from admission's own account, and the two disagree.

        REFUSED BEFORE A RUNTIME EXISTS. The mount plan, the source boundary
        and the start are all still ahead of the comparison."""
        foreign = self._foreign_job()
        with self.assertRaises(Exception) as caught:
            self._started(job_id=foreign)
        held = str(caught.exception)
        self.assertIn(foreign, held)
        self.assertIn("job-a", held)
        self.assertEqual(
            attempt_runtime_of(self.fixture.world.manager,
                               self.attempt)["execution_runtime"],
            "not-started")

    def test_the_container_refuses_that_mismatch_for_itself(self):
        """And the untrusted side asks the same question independently. The
        host compares before it starts; this is the container holding a bundle
        it verified and a launch it verified, and refusing to act on the two
        together."""
        with self.assertRaises(Exception) as caught:
            self.workload.correlate_launch_job(
                {"schema": "baton.worker-launch/3",
                 "job_execution": {"job_id": "somebody-elses-job"}},
                {"job_id": "job-a"})
        self.assertIn("another Job's evidence", str(caught.exception))

    def test_a_launch_with_no_job_correlates_with_anything(self):
        """`/1` and `/2` claim no Job, so there is nothing to disagree with."""
        self.assertIsNone(self.workload.correlate_launch_job(
            {"schema": "baton.worker-launch/1"}, {"job_id": "job-a"}))

    def test_a_correlated_launch_answers_its_own_job(self):
        self.assertEqual(self.workload.correlate_launch_job(
            {"schema": "baton.worker-launch/3",
             "job_execution": {"job_id": "job-a"}}, {"job_id": "job-a"}),
            "job-a")

    @property
    def workload(self):
        import integration_workload

        return integration_workload

    def test_a_port_with_no_job_owner_composes_exactly_what_it_always_did(self):
        """The unchanged deployment: a port composed without the reader is not
        quietly given a context, and the container reads the `/1` it always
        read."""
        held = self.fixture.port()
        held.prepare(self.fixture.stage(job_id="job-a"), None)
        self.fixture.admit(held)
        self.assertEqual(
            launch.adopt(self.fixture.place("launch-home"),
                         attempt_id=self.attempt,
                         session="integration-session",
                         contract="baton.worker-control/1",
                         role=self.fixture_module.LAUNCH_ROLE)
            .document["schema"],
            "baton.worker-launch/1")

    def test_an_attempt_this_execution_never_prepared_is_refused(self):
        """A configured reader and an unbound attempt does NOT fall back to the
        defaults: a launch composed there would state ceilings under the name of
        a Job that chose others."""
        with self.assertRaises(Exception) as caught:
            self._port()._job_execution("attempt-nobody-prepared")
        self.assertIn("names no Job", str(caught.exception))

    # -- what the container does with the number, at the run seam ------------

    def _turn(self, document, *, run=None, behaviour="import", agent=None):
        """The fixture's own real worker turn, over the PORT'S document.

        `TheWholeIntegrationRunsThroughThisPort.worker_turn` authors a launch of
        its own, which is right for a case about the import and wrong for one
        about what the PORT wrote. Everything else is the fixture's: its
        provider child, its agent, its adopted delivery, its bundle and its
        expected revision.
        """
        import subprocess

        import claude_agent as agent_module
        import integration_entry

        from tests.manager import test_integration_worker as workload_fixture

        script = os.path.join(self.fixture.place("provider"), "provider.py")
        with open(script, "w", encoding="utf-8") as handle:
            handle.write(workload_fixture.PROVIDER_SOURCE)

        def runner(argv, **options):
            return subprocess.run(
                [sys.executable, script, behaviour, argv[-1]],
                capture_output=True, text=True, cwd=options.get("cwd"),
                timeout=300)

        place = os.path.join(self.fixture.place("worker"), "launch.json")
        if os.path.exists(place):
            # A REPLAYED TURN READS THE SAME DELIVERY. The container's own copy
            # is read-only, which is the contract; this rewrites the host file
            # between turns rather than pretending a second delivery exists.
            os.chmod(place, 0o644)
        with open(place, "w", encoding="utf-8") as handle:
            json.dump(document, handle)
        os.chmod(place, 0o444)
        delivery = self.fixture.delivery()
        bundle = os.path.join(self.fixture.root, "bundles", self.attempt)
        expected = integration_contract.read_bundle(
            bundle)["envelope"]["eligibility"]["expected_target_revision"]
        if run is not None:
            # THE NORMAL SUBPROCESS BOUNDARY, replaced for this turn only. The
            # workload calls `subprocess.run` to execute the accepted
            # verification; nothing above it changes.
            original = self.workload.subprocess.run
            self.workload.subprocess.run = run
            self.addCleanup(setattr, self.workload.subprocess, "run", original)
        return integration_entry.main(
            agent=agent if agent is not None else agent_module.ClaudeAgent(
                run=runner, home=self.fixture.place("agent-home")),
            launch_place=place,
            assignment_root=delivery.assignment_root,
            result_root=delivery.result_root,
            bundle_root=bundle,
            target_root=self.fixture.target_place,
            scratch=self.fixture.place("worker-scratch"),
            revision=lambda place: expected)

    def _result(self):
        with open(os.path.join(self.fixture.delivery().result_root,
                               "result.json"), encoding="utf-8") as handle:
            return json.load(handle)

    def _verification_seam(self):
        """Intercept the ACCEPTED VERIFICATION only, at the workload's own
        `subprocess.run`.

        The workload reaches that boundary for more than one thing -- the
        target's revision query goes through it too, under its own constant --
        so a blanket replacement captures the wrong number. Everything that is
        not the accepted command is handed straight to the real runner.
        """
        import subprocess

        accepted = list(self.fixture.world.required["argv"])
        captured = []
        real = self.workload.subprocess.run

        def run(argv, **options):
            if list(argv) != accepted:
                return real(argv, **options)
            captured.append(options.get("timeout"))
            raise subprocess.TimeoutExpired(argv, options.get("timeout"))

        return captured, run

    def test_the_configured_ceiling_is_what_the_verification_is_given(self):
        """THE WHOLE CHAIN, and the number is OBSERVED rather than inferred.

        The port composes and materializes the document; the container reads
        that exact file; and the seconds the accepted verification command is
        actually given are captured at the boundary the workload runs it
        through. The Job asked for 120 and the image default is 1800.
        """
        self._started()
        captured, run = self._verification_seam()
        self.assertEqual(self._turn(self._materialized(), run=run), 0)
        self.assertEqual(captured, [self.CEILING])
        answer = self._result()
        self.assertEqual(answer["outcome"], "held")
        self.assertEqual(answer["detail"]["reason"], "verification-failed")
        self.assertIn(f"did not finish within {self.CEILING}s",
                      answer["detail"]["detail"]["observed"])

    def test_the_same_turn_with_no_job_is_given_the_image_default(self):
        """THE CONTROL, and without it the case above proves only that a
        timeout can be injected. Same fixture, same injection, a port composed
        with no Job reader -- so the container reads the `/1` it always read and
        the command is handed the image's own 1800."""
        held = self.fixture.port()
        held.prepare(self.fixture.stage(job_id="job-a"), None)
        self.fixture.admit(held)
        captured, run = self._verification_seam()
        document = launch.adopt(
            self.fixture.place("launch-home"), attempt_id=self.attempt,
            session="integration-session",
            contract="baton.worker-control/1",
            role=self.fixture_module.LAUNCH_ROLE).document
        self.assertEqual(self._turn(document, run=run), 0)
        self.assertEqual(captured, [self.workload.VERIFICATION_SECONDS])
        self.assertNotEqual(self.workload.VERIFICATION_SECONDS, self.CEILING)

    def test_the_provider_turn_is_given_the_jobs_own_bound(self):
        """[P1] `_seen` is set by the ordinary `work()` and this entry never
        calls it, so a Job requesting a provider ceiling reached the production
        run seam with 3600. The delivery travels with the turn now, and the
        number is read at the adapter's own run seam."""
        self._started()
        captured = self._provider_seconds(self._materialized())
        self.assertEqual(captured, [self.PROVIDER_CEILING])
        self.assertNotEqual(self.PROVIDER_CEILING,
                            limits.boundary_default("provider_turn"))

    def test_the_same_turn_with_no_job_gives_the_provider_its_default(self):
        """The control for the case above: a `/1` delivery claims no Job and
        the adapter's own 3600 is what the child is given."""
        held = self.fixture.port()
        held.prepare(self.fixture.stage(job_id="job-a"), None)
        self.fixture.admit(held)
        document = launch.adopt(
            self.fixture.place("launch-home"), attempt_id=self.attempt,
            session="integration-session",
            contract="baton.worker-control/1",
            role=self.fixture_module.LAUNCH_ROLE).document
        self.assertEqual(self._provider_seconds(document),
                         [limits.boundary_default("provider_turn")])

    def test_a_configured_provider_turn_succeeds_and_imports(self):
        """The configured SUCCESS, over the real composition. A Job-bound
        delivery is not only about failing under a smaller number: the ordinary
        outcome has to keep working, and the import really lands."""
        self._started()
        self.assertEqual(self._turn(self._materialized()), 0)
        answer = self._result()
        self.assertEqual(answer["outcome"], "integrated")
        with open(os.path.join(self.fixture.target_place,
                               self.fixture.reviewed), "rb") as handle:
            self.assertEqual(handle.read(), self.fixture.CANDIDATE)

    def test_a_configured_provider_that_cannot_start_is_held_as_that(self):
        """And the start failure, under a configured context: the adapter's own
        closed vocabulary answers, not the provider's prose, and the container
        does not import anything."""
        self._started()
        document = self._materialized()

        def refusing(argv, **options):
            raise OSError("no such provider on this image")

        import claude_agent as agent_module

        held = agent_module.ClaudeAgent(
            run=refusing, home=self.fixture.place("agent-home"))
        answer = self._turn(document, agent=held)
        self.assertEqual(answer, 0)
        settled = self._result()
        self.assertEqual(settled["outcome"], "held")
        self.assertEqual(settled["detail"]["reason"], "provider-failed")
        # AND NOTHING WAS IMPORTED. The reviewed path does not exist in the
        # target until a turn puts it there, so its absence is the assertion.
        self.assertFalse(os.path.exists(os.path.join(
            self.fixture.target_place, self.fixture.reviewed)))

    def test_a_second_turn_under_the_same_delivery_duplicates_nothing(self):
        """REPLAY, with the configured context in it. The attempt already
        carries a terminal result, so the workload answers it again rather than
        taking a second provider turn or importing twice."""
        self._started()
        document = self._materialized()
        self.assertEqual(self._turn(document), 0)
        first = self._result()
        replayed_from = self._result_bytes()
        captured = self._provider_seconds(document)
        self.assertEqual(captured, [],
                         "a replayed turn takes no second provider turn")
        # THE EXACT BYTES, not two documents that happen to parse alike.
        # Review 2026-09-13T04:03:31Z: the first form compared parsed results
        # and the prose claimed byte identity. A replayed answer is the
        # retained one, so the file must be unchanged on disk.
        self.assertEqual(self._result_bytes(), replayed_from)
        self.assertEqual(self._result(), first)

    def _result_bytes(self):
        with open(os.path.join(self.fixture.delivery().result_root,
                               "result.json"), "rb") as handle:
            return handle.read()

    def _provider_seconds(self, document):
        """What the PROVIDER child is actually given, at the adapter's seam."""
        import claude_agent as agent_module

        captured = []
        original = agent_module.ClaudeAgent._ran_provider

        def watching(self, argv, *, cwd, seconds, env):
            captured.append(seconds)
            return original(self, argv, cwd=cwd, seconds=seconds, env=env)

        agent_module.ClaudeAgent._ran_provider = watching
        self.addCleanup(setattr, agent_module.ClaudeAgent, "_ran_provider",
                        original)
        self._turn(document)
        return captured


class TheDerivedJudgmentCarriesItsOwningResultsJob(unittest.TestCase):
    """The last execution in this deployment that received no Job context.

    A derived judgment runs a real container over a real candidate and it is
    NOT an ordinary stage: it has no stage row, no pool allocation and no
    carrier handed to it. Review 2026-09-13T03:50:23Z: bind the actual owning
    result Job and the retained intent, and do not infer either from an
    allocation that does not exist or from an incoming document.

    SO THE BINDING IS THE OWNER'S OWN SUBJECT. `Integration` composes the
    judged subject from the reconciled result account, and the Job in it is the
    Job that owns the result being judged. The runtime half is the judge's own
    configured manifest and policy -- what this execution actually mounts and
    runs under -- which is the retained intent it already carried.
    """

    def setUp(self):
        from tools import single_worker

        self.module = single_worker

    SUBJECT = {"job_id": "job-b", "candidate": "c" * 40,
               "derived_proposal_id": "proposal-derived"}

    def test_the_owning_job_is_read_from_the_judged_subject(self):
        self.assertEqual(self.module._judged_job(dict(self.SUBJECT)), "job-b")

    def test_a_subject_naming_no_job_is_refused(self):
        """Not defaulted, and not looked up somewhere else: a judgment whose
        own subject cannot say which result's Job it is about has not
        identified what it is judging."""
        for held in ({}, {"job_id": None}, {"job_id": ""}, {"job_id": 7}):
            with self.subTest(subject=held):
                with self.assertRaises(Exception) as caught:
                    self.module._judged_job(dict(held))
                self.assertIn("judged result", str(caught.exception))

    def test_an_execution_naming_no_job_does_not_take_the_defaults(self):
        """The serving and observing readers both refuse an execution with no
        Job when a Job reader is configured. Answering `None` would hand a
        Job-bound deployment the image defaults under an execution that has an
        owner -- the legacy-delivery fallback this Work refuses everywhere.

        BOTH READERS, because they exist to produce IDENTICAL BYTES: two
        compositions that disagreed about an unbound execution would disagree
        about the document, and the observation would report every Job-bound
        launch unreadable.
        """
        for name in ("_SingleWorker", "_Observation"):
            with self.subTest(reader=name):
                held = SimpleNamespace(
                    execution_context=lambda **named: named,
                    given={"input_manifest": {"manifest_digest": "sha256:1"},
                           "policy_digest": "sha256:2"})
                reader = getattr(self.module, name)._job_execution
                with self.assertRaises(Exception) as caught:
                    reader(held, {"attempt_id": "attempt-1"})
                self.assertIn("names no Job", str(caught.exception))

    def test_a_composition_with_no_job_owner_still_answers_none(self):
        """And the deployment that genuinely has none is untouched."""
        held = SimpleNamespace(execution_context=None, given={})
        self.assertIsNone(
            self.module._SingleWorker._job_execution(held, {"job_id": "job-a"}))
        self.assertIsNone(
            self.module._SingleWorker._job_execution(
                SimpleNamespace(execution_context=lambda **named: named,
                                given={}), None))

    def test_the_retained_intent_is_what_the_launch_states(self):
        """The runtime half is the judge's OWN configured identities, not the
        Job's submitted ones. Both are stated and neither is invented."""
        seen = {}

        def reader(**named):
            seen.update(named)
            return {"job_id": named["job_id"]}

        held = SimpleNamespace(
            execution_context=reader,
            given={"input_manifest": {"manifest_digest": "sha256:runtime"},
                   "policy_digest": "sha256:policy"})
        answer = self.module._SingleWorker._job_execution(
            held, {"job_id": "job-b", "attempt_id": "judgment-1"})
        self.assertEqual(answer, {"job_id": "job-b"})
        self.assertEqual(seen, {"job_id": "job-b",
                                "attempt_id": "judgment-1",
                                "runtime_input_digest": "sha256:runtime",
                                "runtime_policy_digest": "sha256:policy"})


class TheHostSideVerificationCarriesTheSameCeiling(unittest.TestCase):
    """The third place candidate code runs, and the one with no container.

    `stage_execution`'s two reconciled owners materialize a revision and then
    execute the deployment's required test IN THIS PROCESS. That is the
    `host_verification` boundary, and until now it borrowed `GIT_SECONDS` -- so
    a Job that configured a verification ceiling was obeyed inside a container
    and ignored here.

    THE GIT CLOCK IS DELIBERATELY NOT THE SAME NUMBER. `_materialize` asks this
    deployment's own tooling for content; only what runs afterwards is the
    Job's, and these cases prove the two moved apart rather than together.
    """

    def setUp(self):
        from tools import stage_execution

        self.module = stage_execution

    def observer(self, **changed):
        held = {"participant": "baton.observer",
                "argv": ["python3", "harness.py"],
                "runner": lambda argv: {"returncode": 0, "stderr": ""},
                "root": "/unused"}
        held.update(changed)
        return self.module._ConfiguredExecution(
            held["participant"], held["argv"], held["runner"], held["root"],
            seconds=held.get("seconds"), retention=held.get("retention"),
            scope=held.get("scope"))

    def test_an_unconfigured_owner_runs_under_the_boundarys_own_default(self):
        """And that default is the number this line already used, so a
        deployment with no Job configuration sees no change at all."""
        self.assertEqual(self.observer()._seconds,
                         limits.boundary_default("host_verification"))
        self.assertEqual(self.observer()._seconds, self.module.GIT_SECONDS)

    def _prepared(self, **changed):
        """One observer over a real root, with the Git half replaced.

        This case is about the clock and the memo the COMMAND gets;
        materializing a real revision would put this module's Git tooling
        inside cases that are not about it.
        """
        import tempfile

        root = tempfile.mkdtemp(prefix="v12-w156162-host-")
        self.addCleanup(shutil.rmtree, root, True)
        held = self.observer(argv=["python3", "harness.py"], root=root,
                             **changed)
        where = os.path.join(root, "content")
        os.makedirs(where)
        with open(os.path.join(where, "harness.py"), "w") as handle:
            handle.write("pass\n")

        def archive(runner, repository, revision, into):
            for name in os.listdir(where):
                shutil.copy(os.path.join(where, name), into)
            return into

        original = self.module._materialize
        self.module._materialize = archive
        self.addCleanup(setattr, self.module, "_materialize", original)
        return held, root, []

    def _refusing(self, root):
        """Capture the command and refuse it, at the normal boundary."""
        import subprocess

        captured = []
        ran = subprocess.run

        def run(argv, **options):
            captured.append((list(argv), options.get("timeout")))
            raise subprocess.TimeoutExpired(argv, options.get("timeout"))

        subprocess.run = run
        self.addCleanup(setattr, subprocess, "run", ran)
        return captured

    def test_the_configured_seconds_are_what_the_command_is_given(self):
        """Through the production `_run`, at the NORMAL SUBPROCESS BOUNDARY.

        The PLAN bounds this to "injected timeout verifies argument selection
        and failure handling, not observed OS descendant termination", and the
        first form of this case slept for three real seconds. The seconds the
        command is actually handed are captured where `_run` hands them over,
        and the argv it was given is captured with them so the case cannot pass
        on some other call.
        """
        import subprocess
        import tempfile

        root = tempfile.mkdtemp(prefix="v12-w156162-host-")
        self.addCleanup(shutil.rmtree, root, True)
        held = self.observer(argv=["python3", "harness.py"], root=root,
                             seconds=1)
        where = os.path.join(root, "content")
        os.makedirs(where)
        with open(os.path.join(where, "harness.py"), "w") as handle:
            handle.write("pass\n")

        def archive(runner, repository, revision, into):
            for name in os.listdir(where):
                shutil.copy(os.path.join(where, name), into)
            return into

        # THE GIT HALF IS REPLACED, not the run: this case is about the clock
        # the COMMAND gets, and materializing a real revision would put this
        # module's Git tooling inside a case that is not about it.
        original = self.module._materialize
        self.module._materialize = archive
        self.addCleanup(setattr, self.module, "_materialize", original)

        captured = []
        ran = subprocess.run

        def run(argv, **options):
            captured.append((list(argv), options.get("timeout")))
            raise subprocess.TimeoutExpired(argv, options.get("timeout"))

        # `_run` imports `subprocess` inside itself, so the module object here
        # is the one it resolves -- this replaces the call it actually makes.
        # The window is one `_run` and `_materialize` is already replaced, so
        # nothing else in it reaches this boundary.
        subprocess.run = run
        self.addCleanup(setattr, subprocess, "run", ran)
        # AND THE TIMEOUT IS ANSWERED, NOT RAISED AND NOT FABRICATED. Owner
        # ruling M157653: the run returns the owner's own closed failure shape
        # carrying the bound, the closed reason and the command, with no exit
        # status anywhere -- which is what the observation owner retains.
        from baton_v12.integration import reconciliation

        answered = held._run("/unused-repository", "HEAD")
        self.assertEqual(captured, [(["python3", "harness.py"], 1)])
        self.assertTrue(reconciliation.is_failed_observation(answered))
        self.assertEqual(answered["reason"], "timeout")
        self.assertEqual(answered["seconds"], 1)
        self.assertEqual(answered["command"], ["python3", "harness.py"])
        self.assertNotIn("status", answered)
        self.assertIn("none is invented", answered["detail"])
        # A SECOND ATTEMPT RUNS NOTHING and repeats the retained diagnostic.
        with self.assertRaises(Exception) as again:
            held._run("/unused-repository", "HEAD")
        self.assertEqual(captured, [(["python3", "harness.py"], 1)])
        self.assertIn("none is invented", str(again.exception))
        # AND THE TEMPORARY TREE IS DISPOSED OF, which is step 5: the one real
        # attempt left none, and the memo hit materialized none.
        self.assertEqual([one for one in os.listdir(root)
                          if one != "content"], [])

    def test_a_different_harness_at_the_same_revision_is_its_own_work(self):
        """[P1], and the worst of the two. The causal owner runs the SAME
        command at the SAME revision with a DIFFERENT harness -- that is what
        `adding` is for, and `harness_added` exists to keep it honest. The
        first key was `(argv, revision, seconds)`, so one harness's retained
        failure refused another harness's run WITHOUT EVER ATTEMPTING IT."""
        import subprocess

        held, root, _trees = self._prepared(seconds=1)
        captured = self._refusing(root)
        # THE FIRST ATTEMPT ANSWERS the closed failure; the retained one after
        # it refuses. Both are "this work was already attempted".
        self.assertTrue(held._run("/unused-repository", "HEAD",
                                  adding="pass\n"))
        self.assertEqual(len(captured), 1)
        # THE SAME COMMAND, THE SAME REVISION, A DIFFERENT HARNESS: this is
        # other work and it is attempted.
        self.assertTrue(held._run("/unused-repository", "HEAD",
                                  adding="raise SystemExit\n"))
        self.assertEqual(len(captured), 2)
        # AND EACH ONE IS THEN ITS OWN RETAINED FAILURE.
        for harness in ("pass\n", "raise SystemExit\n"):
            with self.subTest(harness=harness):
                with self.assertRaises(Exception):
                    held._run("/unused-repository", "HEAD", adding=harness)
        self.assertEqual(len(captured), 2)

    def test_one_scope_never_speaks_for_another(self):
        """The retention is shared by a deployment, so a key that did not name
        the owning Job, result and phase would let one result's failure refuse
        another's run."""
        held, root, _trees = self._prepared(seconds=1,
                                            scope=("job-a", "result-1",
                                                   "causal"))
        captured = self._refusing(root)
        self.assertTrue(held._run("/unused-repository", "HEAD"))
        self.assertEqual(len(captured), 1)
        other = self.observer(argv=["python3", "harness.py"], root=root,
                              seconds=1, retention=held._retention,
                              scope=("job-b", "result-2", "causal"))
        self.assertTrue(other._run("/unused-repository", "HEAD"))
        self.assertEqual(len(captured), 2)

    def test_the_git_clock_is_untouched_by_a_jobs_ceiling(self):
        """The separation stated as a fact rather than as a comment: nothing a
        Job configures changes this module's own Git timeout."""
        self.assertEqual(self.module.GIT_SECONDS, 300)
        self.assertEqual(self.observer(seconds=1).__dict__["_seconds"], 1)
        self.assertEqual(self.module.GIT_SECONDS, 300)


class TheComposedHostVerificationUsesTheJobsCeiling(unittest.TestCase):
    """The host boundary through its ACTUAL composed owners.

    Review 2026-09-13T04:03:31Z: `_ConfiguredExecution._run` raising
    `TimeoutExpired` is not sufficient. The causal observer and the imported
    verifier are the owners that run the required test on the host, and what
    has to be established is the configured timeout AT THE NORMAL SUBPROCESS
    BOUNDARY inside the real reconciled path, plus the owning result, the
    cleanup and the no-duplicate behaviour after it.

    THE JOB IS CONFIGURED AT ITS OWN SUBMISSION. `job-b` is the reconciled Job
    in this fixture, and its submitted document is arranged at the factory the
    composed case calls -- before anything is stored, so no immutable intent is
    edited and no existing assertion moves.
    """

    CEILING = 77

    def setUp(self):
        from tests.tools import test_stage_execution as composed

        self.case = composed.TwoBoundJobsTraverseServingAndCorrection(
            "test_two_accepted_jobs_share_one_integrator_one_at_a_time")
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)
        self._configured()
        self.seen = []

    def _configured(self):
        """Arrange `job-b`'s SUBMITTED ceiling, once, at the factory."""
        from baton_v12.job_manager import documents

        original = self.case.both_jobs

        def both():
            held = json.loads(json.dumps(original()))
            held["schema"] = documents.SUBMISSION_SCHEMA
            [job] = [one for one in held["jobs"] if one["job_id"] == "job-b"]
            job["execution_limits"] = {
                "verification_command_seconds": self.CEILING}
            return held

        self.case.both_jobs = both

    def _watching(self, *, failing=False, composed=None, error=None,
                  argv=None, home=None, argvs=None):
        """Capture the ACCEPTED COMMAND at the host's own subprocess boundary.

        `_ConfiguredExecution._run` imports `subprocess` inside itself, so this
        is the module object it resolves and the call it actually makes.
        Everything that is not the accepted command -- this deployment's Git
        tooling above all -- is handed to the real runner untouched.
        """
        import subprocess

        # THE MATERIALIZATION COUNTER, at the call the host owner makes. Review
        # 2026-09-13T10:27:22Z: a scratch directory count alone is not that
        # counter -- it would miss a materialization that cleaned up after
        # itself. It is installed with the command watch, so every case that
        # watches also counts.
        from tools import stage_execution

        self.materialized = 0
        materializing = stage_execution._materialize

        def counted(*arguments, **named):
            self.materialized += 1
            return materializing(*arguments, **named)

        stage_execution._materialize = counted
        self.addCleanup(setattr, stage_execution, "_materialize",
                        materializing)
        # THE COMMAND THIS DEPLOYMENT DERIVES, asked of the owner that derives
        # it rather than spelled here: `Integration.required_tests` reads the
        # configured implementation task and its bound manifest, which is what
        # the host owners actually run.
        # ONE COMMAND OR SEVERAL. Two Jobs with their own configured tasks run
        # two different required tests, and a watch that knew only one of them
        # would let the other through to the real runner -- which would look
        # like isolation and be nothing of the kind.
        accepted = [list(one) for one in argvs] if argvs is not None else [
            list(argv if argv is not None else self.required_argv(composed))]
        real = subprocess.run

        # AND ONLY THE HOST OWNER'S RUNS. The ordinary worker's own verification
        # is the SAME accepted command, so argv alone selects both and
        # intercepting the worker's would fail the traversal before the
        # reconciled path exists. The host owners materialize their content
        # under this deployment's integration root and run there; that
        # directory is the discriminator.
        home = os.path.realpath(home if home is not None
                                else self.case.deployment_of(
                                    composed if composed is not None
                                    else self.case._composed
                                ).integration_root)

        def run(argv, **options):
            where = options.get("cwd")
            if list(argv) not in accepted or not where \
                    or not os.path.realpath(where).startswith(home):
                return real(argv, **options)
            self.seen.append((list(argv), options.get("timeout")))
            if error is not None:
                # THE START FAILURE, which is the OTHER way a host command
                # produces no exit status: the child never ran at all.
                raise error
            if failing:
                raise subprocess.TimeoutExpired(argv, options.get("timeout"))
            return real(argv, **options)

        subprocess.run = run
        self.addCleanup(setattr, subprocess, "run", real)

    def required_argv(self, composed=None):
        """The accepted command, derived by the owner that derives it.

        FROM THE DEPLOYMENT THAT IS ALREADY SERVING, when there is one. Review
        2026-09-13T05:32:04Z: the first form always called `serving_two`, which
        composes a NEW deployment and RESETS the fixture's `_composed` and
        `engine` -- so arming the watch after the judgments threw away the
        deployment whose post-import branch was about to run, and no command
        was ever seen. Composing a deployment merely to read an argv is the
        mistake; reading it from the one in hand is not.
        """
        from tools import stage_execution

        held = (composed if composed is not None
                else self.case.serving_two(**self.case.traversing())[2])
        deployment = self.case.deployment_of(held)
        return stage_execution.Integration(deployment).required_tests(
            "job-b")["argv"]

    def test_the_composed_causal_owner_runs_under_the_jobs_ceiling(self):
        """The reconciled path drives the causal observer over three content
        states, and every one of those runs is given the JOB'S number."""
        self._watching()
        held, deployment, result_id, result = self.case.pending_judgments()
        self.assertTrue(self.seen, "the composed causal owner ran no command")
        for argv, seconds in self.seen:
            with self.subTest(argv=argv):
                self.assertEqual(seconds, self.CEILING)
        # THE OWNING RESULT, and it is job-b's: the ceiling that moved these
        # runs is the one the Job that owns this result submitted.
        self.assertEqual(result["state"], "published")
        self.assertEqual(self.owning_job(deployment, result_id), "job-b")
        # AND THE CAUSAL EVIDENCE IS REALLY THERE -- three observations, which
        # is what the reconciled owner requires before it publishes.
        self.assertEqual(sorted(result["causal_observations"]),
                         ["base", "combined", "isolated"])
        del held

    def owning_job(self, deployment, result_id):
        """Which Job owns this result, from the integration owner's own row."""
        from baton_v12.integration import reconciliation

        return reconciliation.result_of(deployment.integration,
                                        result_id)["job_id"]

    def test_a_causal_overrun_is_retained_and_blocks_the_result(self):
        """THE APPROVED CONTRACT at the causal boundary.

        Owner ruling M157653 (2026-09-13T09:19:44Z) approving
        HOST-FAILURE-PROPOSAL-2026-09-13.md. Before it, a host command that
        supplied no exit status had NO CUSTODY: the null status was refused
        before retention and every tick re-ran the command, and the later
        raising form kept the diagnostic but still stored nothing.

        NOW IT IS RETAINED AS ITSELF. The owner keeps a tagged, closed failure
        answer and settles the result BLOCKED, with a reason naming the phase,
        the closed cause and the bound this Job actually applied. The command
        runs ONCE across repeated ticks, and the result is never published.
        """
        from baton_v12.integration import reconciliation

        self._watching(failing=True)
        held = self.case.integrating(
            result_judgment_workers=self.case.judgment_workers())
        self.case.drive_job(held.job, held.composed, "job-a", "integration",
                            "completed", ticks=4)
        for _ in range(4):
            self.case.tick(held)
        self.assertEqual([seconds for _argv, seconds in self.seen],
                         [self.CEILING])
        deployment = self.case.deployment_of(held.composed)
        [row] = deployment.integration._connection.execute(
            "SELECT result_id FROM integration_results").fetchall()
        settled = reconciliation.result_of(deployment.integration,
                                           row["result_id"])
        self.assertEqual(settled["state"], "blocked")
        self.assertIn("NO EXIT STATUS", settled["reason"])
        self.assertIn(f"{self.CEILING}s", settled["reason"])
        # THE RETAINED ANSWER ITSELF, read back through the owner's own reader.
        failed = reconciliation.failed_host_verification(
            deployment.integration, row["result_id"])
        self.assertIsNotNone(failed)
        self.assertEqual(failed["reason"], "timeout")
        self.assertEqual(failed["seconds"], self.CEILING)
        self.assertIn(failed["phase"], reconciliation.CAUSAL_PHASES)
        # THE COMPLETED PREFIX AND THE REMAINDER, exactly the phases before and
        # after the one that failed -- and nothing invented for the remainder.
        order = list(reconciliation.CAUSAL_PHASES)
        where = order.index(failed["phase"])
        self.assertEqual(sorted(failed["completed"]), sorted(order[:where]))
        self.assertEqual(sorted(failed["not_run"]), sorted(order[where + 1:]))
        # AND NO JUDGE WAS COMPOSED: a blocked result is never published.
        self.assertEqual(deployment.judges, {})

    def test_resumed_serving_after_a_reopen_runs_no_command(self):
        """RESUMED SERVING, not a getter.

        Review 2026-09-13T10:14:06Z: reading the custody back through a
        read-only handle shows the record survives; it does not show that a
        DEPLOYMENT which resumes over that store declines to redo the work. So
        the serving composition is closed and a NEW ONE is composed over the
        same stores and ticked, with the host boundary still watched.

        WHAT IS COUNTED: host commands and materializations, both across the
        resumed ticks. The retained failure is what the resumed deployment
        meets, and it meets it without running anything.
        """
        from baton_v12.integration import reconciliation

        self._watching(failing=True)
        held = self.case.integrating(
            result_judgment_workers=self.case.judgment_workers())
        self.case.drive_job(held.job, held.composed, "job-a", "integration",
                            "completed", ticks=4)
        for _ in range(4):
            self.case.tick(held)
        ran, scratch = len(self.seen), self._scratch_count(held)
        self.assertEqual(ran, 1)
        deployment = self.case.deployment_of(held.composed)
        [row] = deployment.integration._connection.execute(
            "SELECT result_id FROM integration_results").fetchall()
        result_id = row["result_id"]
        settled = reconciliation.result_of(deployment.integration,
                                           result_id)["state"]
        self.assertEqual(settled, "blocked")

        # THE SERVING COMPOSITION IS TAKEN DOWN AND A NEW ONE COMES UP.
        engine = self.case.engine
        held.composed.close()
        held.job.close()
        held.control.close()
        from unittest.mock import patch
        from baton_v12.job_manager import sweep
        from tests.job_manager import fixtures

        with patch.object(type(self.case), "quiescing", return_value=engine):
            job, control, composed = self.case.serving_two(
                **self.case.traversing(
                    result_judgment_workers=self.case.judgment_workers()))
        self.addCleanup(composed.close)
        resumed = SimpleNamespace(job=job, control=control, composed=composed)
        for _ in range(6):
            sweep(job, composed, now=fixtures.NOW)

        # NOTHING RAN AND NOTHING WAS MATERIALIZED on the resumed deployment.
        self.assertEqual(len(self.seen), ran,
                         "the resumed deployment re-ran the host command")
        self.assertEqual(self._scratch_count(resumed), scratch,
                         "the resumed deployment materialized again")
        # AND THE MATERIALIZATION IS COUNTED AT ITS OWN CALL, asserted rather
        # than merely installed. Review 2026-09-13T10:38:32Z: I said the case
        # asserted this and it did not -- the counter was wired and never read.
        # A directory count cannot see a materialization that cleaned up after
        # itself; this one can.
        self.assertEqual(self.materialized, 1,
                         "the host owner materialized more than once")
        # AND THE RESULT IS STILL BLOCKED, under the same retained failure.
        again = self.case.deployment_of(composed)
        self.assertEqual(
            reconciliation.result_of(again.integration, result_id)["state"],
            "blocked")
        failed = reconciliation.failed_host_verification(again.integration,
                                                         result_id)
        self.assertIsNotNone(failed)
        self.assertEqual(failed["seconds"], self.CEILING)
        self.assertEqual(again.judges, {})

    def test_a_blocked_failure_can_never_be_published_or_authorized(self):
        """BLOCKED PUBLICATION, EVIDENCE AND IMPORT, asked of the PUBLIC OWNERS.

        Review 2026-09-13T10:27:22Z: the first form of this case called private
        shape helpers and claimed a public-owner result. It did not have one.
        These are the typed public entries a deployment would actually reach,
        called against a real blocked result, and each refuses in its own
        owner's words while the public readback stays exactly as it was.
        """
        from baton_v12.contracts import ContractRefusal
        from baton_v12.integration import reconciliation

        held, deployment, result_id = self._blocked_result()
        before = reconciliation.result_of(deployment.integration, result_id)
        self.assertEqual(before["state"], "blocked")
        publisher = deployment.sessions["integrator"]
        for what, call in (
                ("publish_result",
                 lambda: reconciliation.publish_result(
                     deployment.integration, publisher, result_id=result_id,
                     input_digest="sha256:" + "1" * 64,
                     policy_digest="sha256:" + "2" * 64)),
                ("record_result_evidence",
                 lambda: reconciliation.record_result_evidence(
                     deployment.integration, deployment.authority,
                     deployment.sessions["verification"],
                     deployment.sessions["review"],
                     deployment.sessions["approval"],
                     result_id=result_id)),
                # THE THIRD OWNER, which my previous case omitted: an import of
                # a blocked result refuses on its own precondition.
                ("record_imported",
                 lambda: reconciliation.record_imported(
                     deployment.integration, deployment.authority,
                     result_id=result_id, entry_id="entry-1"))):
            with self.subTest(owner=what):
                with self.assertRaises(ContractRefusal) as caught:
                    call()
                # EACH REFUSES IN ITS OWN OWNER'S WORDS. The two publication
                # owners say the result is BLOCKED and quote its retained
                # reason; `record_imported` refuses on its own PRECONDITION, so
                # what is asserted of it is that code rather than a shared
                # word it does not use.
                if what == "record_imported":
                    self.assertEqual(caught.exception.code, "precondition")
                else:
                    self.assertIn("is blocked", str(caught.exception))
                    self.assertIn("NO EXIT STATUS", str(caught.exception))
        # AND THE PUBLIC READBACK IS UNCHANGED by any of those attempts.
        after = reconciliation.result_of(deployment.integration, result_id)
        self.assertEqual(after["state"], "blocked")
        self.assertEqual(after["reason"], before["reason"])
        self.assertEqual(after["causal_observations"],
                         before["causal_observations"])
        self.assertEqual(deployment.judges, {})
        del held

    def _blocked_result(self):
        """One real result blocked by a host verification that had no status."""
        self._watching(failing=True)
        held = self.case.integrating(
            result_judgment_workers=self.case.judgment_workers())
        self.case.drive_job(held.job, held.composed, "job-a", "integration",
                            "completed", ticks=4)
        for _ in range(4):
            self.case.tick(held)
        deployment = self.case.deployment_of(held.composed)
        [row] = deployment.integration._connection.execute(
            "SELECT result_id FROM integration_results").fetchall()
        return held, deployment, row["result_id"]

    def test_a_post_import_restart_keeps_one_unchanged_queue_hold(self):
        """THE POST-IMPORT TWIN OF THE CAUSAL RESTART, and a different shape.

        A causal failure blocks the RESULT. A post-import failure leaves the
        result AUTHORIZED and holds the TARGET through the queue -- one entry,
        one hold -- and that distinction is the point of having both cases.

        Review 2026-09-13T10:38:32Z proved this restart independently and I
        said this case carried that proof. Review 2026-09-13T10:48:56Z checked
        and it did not: it asserted the result was NOT BLOCKED rather than
        authorized, and it never read the public target, the blocked account,
        the target's reference or the Authority's receipts at all. Raw entry
        tuples do not speak for those owners. Every one of them is read here
        now, through each owner's own public reader.
        """
        import copy
        import subprocess
        from unittest.mock import patch
        from baton_v12.integration import queue, reconciliation
        from baton_v12.job_manager import sweep
        from tests.job_manager import fixtures

        def revision(row):
            """What the target's OWN reference points at, asked of Git."""
            return subprocess.run(
                ["git", "-C", row["target_source"]["path"], "rev-parse",
                 row["target_reference"]],
                check=True, capture_output=True, text=True).stdout.strip()

        blocked = []
        # PATCHED WHERE IT IS CALLED FROM. `execution` imports `block_target`
        # by name, so patching the queue module's attribute intercepts nothing.
        from baton_v12.integration import execution as execution_owner

        blocking = execution_owner.block_target

        def counted(*arguments, **named):
            blocked.append(named.get("reason"))
            return blocking(*arguments, **named)

        with patch.object(execution_owner, "block_target",
                          side_effect=counted):
            held, deployment, result_id, before = self._post_import_failure(
                failing=True)
            ran, made = len(self.seen), self.materialized
            self.assertEqual((ran, made), (1, 1))
            self.assertEqual(len(blocked), 1, blocked)
            # THE RESULT IS AUTHORIZED -- positively, and not merely "not
            # blocked". This branch holds the TARGET instead, which is the
            # whole distinction from the causal twin.
            settled = reconciliation.result_of(deployment.integration,
                                               result_id)
            self.assertEqual(settled["state"], "authorized")
            # AND THE HOLD IS THE QUEUE OWNER'S OWN, read through its public
            # readers: the target's state, the reason it names, and the
            # account it retained -- which carries the failed verification
            # this deployment actually observed.
            target_id = settled["canonical_target_id"]
            target = copy.deepcopy(
                queue.target_of(deployment.integration, target_id))
            self.assertEqual(target["state"], "blocked")
            self.assertEqual(target["blocked_reason"],
                             "post-import-verification-no-status")
            account = target["blocked_account"]
            self.assertEqual(account["reason"], target["blocked_reason"])
            self.assertEqual(
                account["detail"]["verification"]["phase"], "post-import")
            self.assertEqual(account["detail"]["verification"]["seconds"],
                             self.CEILING)
            entries = copy.deepcopy(
                queue.entries_of(deployment.integration, target_id))
            first = [tuple(one) for one in
                     deployment.integration._connection.execute(
                         "SELECT * FROM entries").fetchall()]
            # THE TARGET'S REFERENCE, ASKED OF GIT. A hold that let the import
            # advance the branch anyway would leave every row above identical
            # and the repository changed.
            reference = revision(settled)
            # AND NOBODY HAS RECEIPTED THE DERIVED PROPOSAL.
            self.assertIsNone(deployment.authority.receipt(
                settled["derived_proposal_id"], "integration"))

            # THE SERVING COMPOSITION IS TAKEN DOWN AND BROUGHT BACK UP.
            engine = self.case.engine
            held.composed.close()
            held.job.close()
            held.control.close()
            with patch.object(type(self.case), "quiescing",
                              return_value=engine):
                job, control, composed = self.case.serving_two(
                    **self.case.traversing(
                        result_judgment_workers=self.case.judgment_workers()))
            self.addCleanup(composed.close)
            for _ in range(6):
                sweep(job, composed, now=fixtures.NOW)

        # NOTHING RAN, NOTHING WAS MATERIALIZED, AND NOTHING WAS BLOCKED AGAIN.
        self.assertEqual(len(self.seen), ran)
        self.assertEqual(self.materialized, made)
        self.assertEqual(len(blocked), 1,
                         "the restart held the target a second time")
        # AND EVERY OWNER SAYS WHAT IT SAID, through its own public reader.
        again = self.case.deployment_of(composed)
        after = reconciliation.result_of(again.integration, result_id)
        self.assertEqual(after, settled)
        self.assertEqual(queue.target_of(again.integration, target_id), target)
        self.assertEqual(queue.entries_of(again.integration, target_id),
                         entries)
        self.assertEqual(
            [tuple(one) for one in again.integration._connection.execute(
                "SELECT * FROM entries").fetchall()], first)
        # THE REFERENCE HAS NOT MOVED, and no receipt appeared behind the
        # restart either.
        self.assertEqual(revision(after), reference)
        self.assertIsNone(again.authority.receipt(
            after["derived_proposal_id"], "integration"))
        # AND THE SCRATCH COUNT THE HELPER TOOK BEFORE THE FAILURE is what
        # the REOPENED deployment holds: the failed run disposed of its own
        # scratch and the reopen materialized nothing, so nothing accumulated
        # across the restart.
        self.assertEqual(
            self._scratch_count(SimpleNamespace(composed=composed)), before)

    def test_an_exact_replay_reaches_the_journal_and_writes_nothing(self):
        """THE OBSERVATION OPERATION REPLAYED, at the store's own Journal.

        My own replay evidence was DICT-LEVEL: it compared what a helper
        returned. Review 2026-09-13T10:48:56Z supplied the actual proof and
        this carries it. The declared observation owner hands back a COPY of
        the custody this deployment really retained -- it runs no command and
        invents no success -- and the public call reaches
        `IntegrationStore.replay` for the operation that is already committed.

        WHAT IS COUNTED IS THE REAL CALL. `replay` and `transact` are watched
        on the store itself, so this asserts that the owner took the replay
        path ONCE and opened NO write transaction, rather than that two
        dictionaries happened to match.
        """
        import copy
        from unittest.mock import patch
        from baton_v12.contracts import ContractRefusal
        from baton_v12.integration import reconciliation

        _held, deployment, result_id = self._blocked_result()
        store = deployment.integration
        before = copy.deepcopy(reconciliation.result_of(store, result_id))
        counts = (len(self.seen), self.materialized)
        self.assertEqual(counts, (1, 1))
        observed = copy.deepcopy(before["causal_observations"])
        replayed, written, asked = [], [], []

        def observe(basis):
            asked.append(copy.deepcopy(basis))
            return dict(basis, execution=observed["execution"],
                        observations=copy.deepcopy(observed))

        observer = SimpleNamespace(participant=before["observed_by"],
                                   observe=observe)
        replay, transact = store.replay, store.transact

        def replaying(*arguments, **named):
            replayed.append(arguments[0])
            return replay(*arguments, **named)

        def writing(*arguments, **named):
            written.append(arguments[0])
            return transact(*arguments, **named)

        with patch.object(store, "replay", replaying), \
                patch.object(store, "transact", writing):
            identical = reconciliation.record_causal_observations(
                store, observer, result_id=result_id)
            self.assertEqual(identical, before)
            self.assertEqual(len(replayed), 1, replayed)
            self.assertEqual(written, [], "an exact replay opened a write")

            # AND A DIFFERENT ATTESTATION OF THE SAME OPERATION IS REFUSED.
            # Only the valid diagnostic changes -- nothing here fabricates a
            # success or edits retained custody -- so what the owner sees is
            # the same operation carrying different observations.
            observed["detail"] += " [different replay attestation]"
            with self.assertRaises(ContractRefusal) as caught:
                reconciliation.record_causal_observations(
                    store, observer, result_id=result_id)
            self.assertEqual(caught.exception.code, "operation-collision")

        # NOTHING MOVED: not the public result, not the write log, and not the
        # host counters -- no command ran and nothing was materialized again.
        self.assertEqual(reconciliation.result_of(store, result_id), before)
        self.assertEqual(written, [])
        self.assertEqual(len(replayed), 1)
        self.assertEqual((len(self.seen), self.materialized), counts)
        # THE OWNER WAS ASKED TWICE AND THE SUBPROCESS ONCE, which is the
        # distinction a call count alone would blur.
        self.assertEqual(len(asked), 2)

    # -- every causal phase, for each closed reason, through the real owners --
    #
    # Review 2026-09-13T10:48:56Z: four cases from repro-159705.py that I had
    # not carried. The retained-failure schema is exercised elsewhere against
    # a validator; these drive the COMPOSED reconciled path and fail the host
    # command at the phase's own call, so what is asserted is the owner's real
    # answer: which phases completed, which never ran, and what the result
    # became.
    CAUSAL_CALL = {"base": 2, "isolated": 3}

    def _phase_failure(self, phase, reason):
        """Fail the host command at THIS phase's call and read the custody."""
        import copy
        import subprocess
        from unittest.mock import patch
        from tools import stage_execution
        from baton_v12.integration import reconciliation

        argv = list(self.required_argv())
        home = os.path.realpath(
            self.case.deployment_of(self.case._composed).integration_root)
        real = subprocess.run
        observing = stage_execution._CausalObserver.observe
        calls, answers = [], []
        failing = self.CAUSAL_CALL[phase]

        def run(command, **options):
            where = options.get("cwd")
            if list(command) == argv and where \
                    and os.path.realpath(where).startswith(home):
                calls.append({"argv": list(command),
                              "seconds": options.get("timeout")})
                if len(calls) == failing:
                    if reason == "timeout":
                        raise subprocess.TimeoutExpired(command,
                                                        options["timeout"])
                    raise FileNotFoundError(
                        "injected host command start failure")
            return real(command, **options)

        def observe(owner, basis):
            answer = observing(owner, basis)
            answers.append(copy.deepcopy(answer))
            return answer

        with patch.object(subprocess, "run", run), \
                patch.object(stage_execution._CausalObserver, "observe",
                             observe):
            held = self.case.integrating(
                result_judgment_workers=self.case.judgment_workers())
            self.case.drive_job(held.job, held.composed, "job-a",
                                "integration", "completed", ticks=4)
            for _ in range(4):
                self.case.tick(held)
        self.assertEqual(len(answers), 1, answers)
        deployment = self.case.deployment_of(held.composed)
        row = reconciliation.result_of(deployment.integration,
                                       answers[0]["result_id"])
        return row, calls

    def _assert_phase_failure(self, phase, reason):
        """The one shape all four share, asserted once."""
        from baton_v12.integration import reconciliation

        row, calls = self._phase_failure(phase, reason)
        failure = row["causal_observations"]
        # THE RESULT IS BLOCKED, and by THIS phase for THIS reason.
        self.assertEqual(row["state"], "blocked")
        self.assertEqual(failure["phase"], phase)
        self.assertEqual(failure["reason"], reason)
        # EVERY CALL CARRIED THE JOB'S OWN NUMBER, and there were exactly as
        # many as this phase is reached by.
        self.assertEqual(len(calls), self.CAUSAL_CALL[phase], calls)
        self.assertEqual({one["seconds"] for one in calls}, {self.CEILING})
        # AND THE PREFIX AND THE REMAINDER ARE THE OWNER'S OWN ORDER: the
        # phases before this one completed, the ones after it never ran.
        order = list(reconciliation.CAUSAL_PHASES)
        self.assertEqual(sorted(failure["completed"]),
                         sorted(order[:order.index(phase)]))
        self.assertEqual(failure["not_run"], order[order.index(phase) + 1:])
        return failure

    def test_a_base_observation_that_never_finishes(self):
        self._assert_phase_failure("base", "timeout")

    def test_a_base_observation_that_never_starts(self):
        failure = self._assert_phase_failure("base", "start-failed")
        self.assertIn("could not be started", failure["detail"])

    def test_an_isolated_observation_that_never_finishes(self):
        self._assert_phase_failure("isolated", "timeout")

    def test_an_isolated_observation_that_never_starts(self):
        failure = self._assert_phase_failure("isolated", "start-failed")
        self.assertIn("could not be started", failure["detail"])

    def test_a_blocked_result_is_refused_by_the_composed_judgment_owners(self):
        """THE DIRECT JUDGMENT BOUNDARY, on the deployment's own methods.

        Review 2026-09-13T11:08:02Z proved it independently and this carries
        it. The publication owners were already refused a blocked result; these
        are the two the DEPLOYMENT exposes, and judgment requires a published
        derived candidate that a blocked result never has.

        WHAT IS COUNTED IS THAT NOTHING WAS STARTED. A refusal that had already
        built a judgment execution or asked the engine for a container would be
        a refusal after the fact; both counts are zero, the dispatch directory
        is the one it was, and the public result is unchanged.
        """
        import copy
        from unittest.mock import patch
        from baton_v12.contracts import ContractRefusal
        from baton_v12.integration import reconciliation
        from tools import single_worker

        _held, deployment, result_id = self._blocked_result()
        before = copy.deepcopy(
            reconciliation.result_of(deployment.integration, result_id))
        self.assertEqual(before["state"], "blocked")
        home = os.path.join(deployment.given["state_root"], "result-judgments")
        dispatched = sorted(os.listdir(home)) if os.path.isdir(home) else None
        counts = (len(self.seen), self.materialized)
        self.assertEqual(counts, (1, 1))

        with patch.object(single_worker, "JudgmentExecution",
                          wraps=single_worker.JudgmentExecution) as building, \
                patch.object(deployment, "_engine_run",
                             wraps=deployment._engine_run) as engine:
            for owner in ("judgment_subject", "judge_result"):
                with self.subTest(owner=owner):
                    with self.assertRaises(ContractRefusal) as caught:
                        getattr(deployment, owner)(result_id)
                    # EACH OWNER'S OWN SENTENCE, and it names the state.
                    self.assertIn("blocked", str(caught.exception))
            self.assertEqual(building.call_count, 0)
            self.assertEqual(engine.call_count, 0)

        self.assertEqual(
            reconciliation.result_of(deployment.integration, result_id),
            before)
        self.assertEqual((len(self.seen), self.materialized), counts)
        self.assertEqual(deployment.judges, {})
        self.assertEqual(
            sorted(os.listdir(home)) if os.path.isdir(home) else None,
            dispatched)

    def test_a_scratch_that_survives_disposal_is_the_deployments_to_release(
            self):
        """STEP 5 OF THE HOST-FAILURE PROPOSAL, through the real runtime.

        Review 2026-09-13T11:08:02Z: a no-op `rmtree` test plus fixture
        teardown does not discharge it. `_no_status` named the surviving tree
        in its diagnostic and nobody owned it -- a deployment released its
        workers, its integration store and its Authority and walked past the
        bytes.

        SO THE DEPLOYMENT OWNS IT NOW. The disposal is refused at the real
        boundary inside a COMPOSED causal failure; the tree survives, the
        diagnosis names it, and it is registered on the deployment. Then the
        operator closes the deployment the ordinary way and the tree is gone --
        with the diagnosis still saying what it said, because a later cleanup
        does not get to edit the failure that was reported.
        """
        import shutil
        from unittest.mock import patch
        from baton_v12.integration import reconciliation
        from tools import stage_execution

        # A DISPOSAL THAT REMOVES NOTHING, injected where `_no_status` makes
        # it, and lifted before anything else in this case runs.
        with patch.object(shutil, "rmtree", lambda *a, **named: None):
            held, deployment, result_id = self._blocked_result()
        self.assertEqual(
            reconciliation.result_of(deployment.integration,
                                     result_id)["state"], "blocked")

        surviving = stage_execution._host_scratch(deployment)
        self.assertEqual(len(surviving), 1, surviving)
        [where] = list(surviving)
        self.assertTrue(os.path.isdir(where),
                        "the injected disposal removed the tree after all")
        # THE DIAGNOSIS NAMES IT, in the registry and in the retention.
        self.assertIn("could not be disposed of and remains", surviving[where])
        self.assertIn(where, surviving[where])
        retained = dict(stage_execution._host_retention(deployment))
        self.assertTrue(any(where in one for one in retained.values()),
                        retained)

        # AND THE ORDINARY RELEASE IS WHAT CLEANS IT UP.
        held.composed.close()
        self.assertFalse(os.path.exists(where),
                         "the deployment released without disposing of the "
                         "scratch it retained")
        self.assertEqual(stage_execution._host_scratch(deployment), {})
        # THE FAILURE IS STILL REPORTED THE WAY IT WAS REPORTED.
        self.assertEqual(dict(stage_execution._host_retention(deployment)),
                         retained)

    def test_a_scratch_that_survives_the_release_too_is_reported(self):
        """AND IT IS NOT QUIETLY ABANDONED A SECOND TIME.

        The registry would be worthless if a release that could not remove the
        tree either dropped it. The disposal is refused for the whole case
        here, so the release meets a path it cannot remove: it refuses,
        NAMING the path, and the entry is still held afterwards rather than
        forgotten.
        """
        import shutil
        from unittest.mock import patch
        from baton_v12.contracts import ContractRefusal
        from tools import stage_execution

        with patch.object(shutil, "rmtree", lambda *a, **named: None):
            held, deployment, _result_id = self._blocked_result()
            surviving = stage_execution._host_scratch(deployment)
            self.assertEqual(len(surviving), 1, surviving)
            [where] = list(surviving)
            with self.assertRaises(ContractRefusal) as caught:
                held.composed.close()
            # THE MESSAGE NAMES THE PATH. `release` reports a failed closer
            # by its name, so the path is in that name -- a surviving tree an
            # operator cannot locate is the silence this Work refuses.
            self.assertIn(where, str(caught.exception))
            self.assertIn("did not release cleanly", str(caught.exception))
            # STILL HELD, because it is still there.
            self.assertEqual(list(stage_execution._host_scratch(deployment)),
                             [where])
            self.assertTrue(os.path.isdir(where))
        # AND THE RETRY IS THE SAME PUBLIC CLOSE. Review 2026-09-13T11:22:32Z
        # proved this branch and asked for it rather than my private call to
        # the disposer: once the fault is lifted the operator repeats the
        # ordinary operation and it succeeds, which is what an operator can
        # actually do.
        held.composed.close()
        self.assertFalse(os.path.exists(where))
        self.assertEqual(stage_execution._host_scratch(deployment), {})
        # AND NOTHING RAN OR WAS MATERIALIZED FOR ANY OF IT.
        self.assertEqual((len(self.seen), self.materialized), (1, 1))

    def _post_import_scratch(self, **failing):
        """A post-import host failure whose scratch will not dispose of itself.

        The disposal is refused ONLY for this deployment's own integration
        root, so the fixture's Git tooling and every other tree are untouched
        by the injection.
        """
        import os as _os
        import shutil
        from unittest.mock import patch

        held, deployment, result_id, _before = self._judged()
        self._watching(
            argv=json.loads(self.case.shared_task_bytes)["verification"],
            home=deployment.integration_root, **failing)
        removing = shutil.rmtree

        def refusing(where, *arguments, **named):
            if _os.path.dirname(_os.path.realpath(where)) == \
                    _os.path.realpath(deployment.integration_root):
                return None
            return removing(where, *arguments, **named)

        with patch.object(shutil, "rmtree", refusing):
            for _ in range(4):
                self.case.tick(held)
        return held, deployment, result_id

    def _assert_post_import_scratch(self, **failing):
        """One surviving post-import tree, released by the ordinary close.

        Review 2026-09-13T11:22:32Z proved both reasons independently. What
        this adds to the causal case is the OTHER owner: `_ImportedVerifier`
        runs against the imported commit in the dedicated target, and its
        surviving scratch has to reach the same registry -- which is the
        wiring, not a restatement.
        """
        import copy
        from baton_v12.integration import IntegrationStore, queue, reconciliation
        from tools import stage_execution

        held, deployment, result_id = self._post_import_scratch(**failing)
        registry = stage_execution._host_scratch(deployment)
        self.assertEqual(len(registry), 1, registry)
        [where] = list(registry)
        self.assertTrue(os.path.isdir(where))
        retained = copy.deepcopy(stage_execution._host_retention(deployment))
        row = copy.deepcopy(
            reconciliation.result_of(deployment.integration, result_id))
        target = copy.deepcopy(queue.target_of(deployment.integration,
                                               row["canonical_target_id"]))
        # THE RESULT IS AUTHORIZED AND THE TARGET IS HELD, and the surviving
        # path is named in the REAL blocked account rather than only in a
        # private dictionary.
        self.assertEqual(row["state"], "authorized")
        self.assertEqual(target["state"], "blocked")
        self.assertIn(
            where,
            target["blocked_account"]["detail"]["verification"]["detail"])

        store_path = deployment.given["integration_store"]
        incarnation = stage_execution._incarnation(held.control)
        held.composed.close()
        self.assertFalse(os.path.exists(where))
        self.assertEqual(stage_execution._host_scratch(deployment), {})
        # THE DIAGNOSIS IS NOT REWRITTEN BY THE CLEANUP.
        self.assertEqual(stage_execution._host_retention(deployment), retained)
        # AND THE DURABLE CUSTODY IS WHAT IT WAS, read by a FRESH READ-ONLY
        # reader rather than through the handles that were just released.
        with IntegrationStore.open_readonly(
                store_path, incarnation=incarnation,
                clock=lambda: job_fixtures.NOW) as reader:
            self.assertEqual(reconciliation.result_of(reader, result_id), row)
            self.assertEqual(
                queue.target_of(reader, row["canonical_target_id"]), target)
        self.assertEqual((len(self.seen), self.materialized), (1, 1))

    def test_a_post_import_scratch_is_released_by_the_same_close(self):
        self._assert_post_import_scratch(failing=True)

    def test_a_post_import_start_failures_scratch_is_released_too(self):
        self._assert_post_import_scratch(
            error=FileNotFoundError("no such required test"))

    # -- UNIT COVERAGE of the retention key, and NOT composed isolation ------
    #
    # WHAT THIS IS. Every owner below is the product's own `_ImportedVerifier`
    # and every attempt really materializes content and really reaches the
    # subprocess boundary, so the discriminator is an ATTEMPT COUNT rather than
    # a key I compared myself. That much is real and is worth keeping.
    #
    # WHAT IT IS NOT, and review 2026-09-13T11:36:15Z measured every line of
    # this. The owners are constructed here and `_run` is called directly, so
    # `verify_imported`, the causal phase assembly and the adoption of a
    # failure by a result owner are all bypassed. Read through the public
    # readers, the variants are NOT the coherent pairs their names suggest:
    #
    #   - "another Job" names `job-a` in the scope while the result reader says
    #     the result is job-b's, and the bound stays Job B's 77;
    #   - "another result" uses the DIRECT entry's result id, which is not an
    #     `IntegrationResult` at all -- `result_of` refuses it, as the seam case
    #     below asserts;
    #   - "another phase" is the coarse retention label `causal`, not one of
    #     the causal owner's own `combined`/`base`/`isolated` phases;
    #   - "another bound" runs Job B's own result at the boundary default while
    #     the Job it belongs to was admitted at 77;
    #   - "another harness" adds a different body under the same command and
    #     task without a new coherent result or task identity.
    #
    # Every raw answer here also carries `input_tree` equal to `input_commit`,
    # because `_run`'s intermediate answer has not been through the owner that
    # resolves the tree. These are deliberate unit inputs; a pair of
    # individually real identifiers is NOT an authorized pair, and no failure
    # in this matrix is durably adopted as a second result. The composed case
    # this cannot replace is the one the seam below is about.

    def _isolation_owner(self, deployment, *, scope, seconds):
        """One real post-import owner, composed the way the product does."""
        from tools import stage_execution

        return stage_execution._ImportedVerifier(
            deployment.observer_participant(),
            self._isolation_argv, stage_execution._git_run,
            deployment.integration_root,
            identity=json.loads(self.case.shared_task_bytes)["task_id"],
            seconds=seconds,
            retention=stage_execution._host_retention(deployment),
            surviving=stage_execution._host_scratch(deployment),
            scope=scope)

    def test_the_retention_key_distinguishes_its_operands_at_the_unit(self):
        """THE KEY'S OWN OPERANDS, at real attempts -- UNIT COVERAGE ONLY.

        Read the note above for what each variant is and is not. This asserts
        that the retention refuses a repeat of the same work without running
        anything, and that changing any single operand of the key reaches the
        command again. It does NOT establish composed Job, result, harness or
        phase isolation, and it is not offered as that.
        """
        from tools import stage_execution
        from baton_v12.contracts import ContractRefusal

        held, deployment, first_result, _result = self._judged()
        # TWO RESULT IDENTIFIERS THIS DEPLOYMENT HOLDS SOMEWHERE. One is the
        # reconciled result; the other is the identifier the first Job's own
        # accepted ENTRY names, and it is NOT an `IntegrationResult` -- which
        # is exactly why this is unit coverage of the key rather than a second
        # admitted result. The seam case below asserts that refusal.
        results = [one["result_id"] for one in
                   deployment.integration._connection.execute(
                       "SELECT result_id FROM integration_results "
                       "UNION SELECT result_id FROM entries").fetchall()]
        self.assertIn(first_result, results)
        second_result = next((one for one in results if one != first_result),
                             None)
        self.assertIsNotNone(second_result, results)
        # THE TWO BOUNDS ARE THE OWNER'S OWN ANSWERS: Job B carries this
        # Work's submitted ceiling, and a stage no Job binds gets the
        # boundary's own default.
        configured = stage_execution._host_seconds(deployment,
                                                   {"job_id": "job-b"})
        default = stage_execution._host_seconds(deployment, {})
        self.assertEqual(configured, self.CEILING)
        self.assertNotEqual(configured, default)
        # AND THE TWO HARNESSES ARE REAL CONTENT.
        with open(os.path.join(self.case.source, "harness.py")) as reading:
            other_harness = reading.read()
        self.assertNotEqual(other_harness, self.case.B_CHECK)

        self._isolation_argv = json.loads(
            self.case.shared_task_bytes)["verification"]
        self._watching(argv=self._isolation_argv,
                       home=deployment.integration_root, failing=True)
        repository, revision = self.case.source, self.case.base
        held_scope = ("job-b", first_result, "post-import")

        def attempt(*, scope=held_scope, seconds=configured,
                    adding=self.case.B_CHECK):
            before = len(self.seen)
            answer = self._isolation_owner(
                deployment, scope=scope, seconds=seconds)._run(
                    repository, revision, adding=adding)
            self.assertEqual(len(self.seen) - before, 1,
                             "this owner never reached its command")
            self.assertEqual(answer["reason"], "timeout")
            return answer

        # THE FIRST REAL FAILURE, RETAINED BY THE OWNER ITSELF.
        attempt()
        self.assertEqual(len(self.seen), 1)

        # AND THE SAME WORK IS REFUSED WITHOUT ATTEMPTING ANYTHING. This is
        # what the retention is FOR, and it is asserted first so that every
        # case below means something.
        with self.assertRaises(ContractRefusal) as caught:
            self._isolation_owner(
                deployment, scope=held_scope, seconds=configured)._run(
                    repository, revision, adding=self.case.B_CHECK)
        self.assertEqual(caught.exception.code, "precondition")
        self.assertEqual(len(self.seen), 1, "a memo hit ran the command")

        # AND CHANGING ANY SINGLE OPERAND OF THE KEY REACHES THE COMMAND
        # AGAIN. These are key operands, not coherent identities; see above.
        varied = {
            "another Job": {"scope": ("job-a", first_result, "post-import")},
            "another result": {"scope": ("job-b", second_result,
                                         "post-import")},
            "another phase": {"scope": ("job-b", first_result, "causal")},
            "another bound": {"seconds": default},
            "another harness": {"adding": other_harness}}
        for what, changed in varied.items():
            with self.subTest(differs_in=what):
                attempt(**changed)

        # SIX REAL ATTEMPTS AND ONE REFUSAL, and the refusal is the only run
        # that did not happen.
        self.assertEqual(len(self.seen), 1 + len(varied))
        self.assertEqual({seconds for _argv, seconds in self.seen},
                         {configured, default})
        # AND EACH OF THEM IS REMEMBERED UNDER ITS OWN KEY.
        self.assertEqual(
            len(stage_execution._host_retention(deployment)), 1 + len(varied))
        del held

    def _held_assignment(self, **failing):
        """A post-import hold, and EVERY ASSIGNMENT THE DEPLOYMENT COMPOSED.

        Not one this test builds. `execution.admit_authorized_result` composes
        it under the grant it just took, and that document is the operand the
        supported recovery verbs accept -- so it is captured where the product
        makes it, by watching the owner that makes it and returning its answer
        untouched.
        """
        from unittest.mock import patch
        from baton_v12.integration import runtime

        composed = []
        composing = runtime.compose_assignment

        def watching(*arguments, **named):
            answer = composing(*arguments, **named)
            composed.append(answer)
            return answer

        with patch.object(runtime, "compose_assignment", watching):
            held, deployment, result_id, _before = self._post_import_failure(
                **failing)
        # EVERY ONE OF THEM IS RETURNED. Which assignments this deployment
        # composed -- and which it did not -- is the fact the case below is
        # about, so the caller gets all of them rather than one this helper
        # picked. Over a held target they are in fact the same document: same
        # entry, same lease, same fence, same attempt.
        self.assertTrue(composed)
        self.assertEqual([one for one in composed if one != composed[-1]], [])
        return held, deployment, result_id, composed

    ACCOUNT_KEYS = ("attempt_id", "entry_id", "lease_id", "fence")

    def test_a_post_import_hold_is_not_reachable_by_the_supported_recovery(
            self):
        """THE SEAM, MEASURED, because an operator meets it and I did.

        `recovery.abandon_held_lease` is the supported explicit operation: it
        ends the held grant after positive quiescence and leaves the target
        blocked and the entry held. It is reached through an ASSIGNMENT, and
        `_owned_assignment` is checked against the account the target is
        actually blocked under.

        A POST-IMPORT HOLD HAS NO SUCH ASSIGNMENT. The reconciled branch
        starts no integration runtime, so nothing ever composed an assignment
        for the account `block_target` recorded -- asserted below against every
        assignment this deployment composed for the whole drive, not against a
        list spelled here. Both supported verbs therefore refuse, each with its
        own sentence, and a caller holding only the blocked account cannot
        compose a fresh assignment either: the grant is read from the
        coordinator in the same call and a blocked target is not open at its
        fence.

        NOTHING IS WORKED AROUND. No raw-store write, no invented retry, no
        reopening -- `activate_target` replays activation, which is a different
        thing. What this case does is establish the exact boundary; the bounded
        correction it implies is recorded in the dossier for its owner.
        """
        import copy
        from baton_v12.contracts import ContractRefusal
        from baton_v12.integration import queue, reconciliation, recovery
        from baton_v12.integration import runtime

        held, deployment, result_id, assignments = self._held_assignment(
            failing=True)
        row = copy.deepcopy(
            reconciliation.result_of(deployment.integration, result_id))
        target = copy.deepcopy(queue.target_of(deployment.integration,
                                               row["canonical_target_id"]))
        entries = copy.deepcopy(queue.entries_of(deployment.integration,
                                                 row["canonical_target_id"]))
        self.assertEqual(target["state"], "blocked")
        self.assertEqual(target["blocked_reason"],
                         "post-import-verification-no-status")
        account = target["blocked_account"]

        # NO ASSIGNMENT THIS DEPLOYMENT COMPOSED NAMES THIS ACCOUNT.
        self.assertTrue(assignments)
        self.assertEqual(
            [one for one in assignments
             if all(one.get(name) == account.get(name)
                    for name in self.ACCOUNT_KEYS)],
            [], "a composed assignment does name the blocked account")

        # SO BOTH SUPPORTED VERBS REFUSE OVER THE ONE IT DID COMPOSE.
        for verb in ("held_status", "abandon_held_lease"):
            with self.subTest(verb=verb):
                with self.assertRaises(ContractRefusal) as caught:
                    getattr(recovery, verb)(deployment.integration,
                                            held.control, None,
                                            assignments[-1])
                self.assertEqual(
                    (caught.exception.category, caught.exception.code),
                    ("policy", "denied"))
                self.assertIn("blocked for another integration account",
                              str(caught.exception))

        # AND THE ACCOUNT ITSELF CANNOT BE TURNED BACK INTO A GRANT.
        with self.assertRaises(ContractRefusal) as caught:
            runtime.compose_assignment(
                deployment.integration, held.control,
                profile=deployment.integration_profile,
                canonical_target_id=row["canonical_target_id"],
                entry_id=account["entry_id"], lease_id=account["lease_id"],
                fence=account["fence"], attempt_id=account["attempt_id"])
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("policy", "denied"))
        self.assertIn("is not open at fence", str(caught.exception))

        # THREE REFUSALS AND NOTHING MOVED: the hold, its entries, the result,
        # the result count, and the host counters.
        self.assertEqual(queue.target_of(deployment.integration,
                                         row["canonical_target_id"]), target)
        self.assertEqual(queue.entries_of(deployment.integration,
                                          row["canonical_target_id"]), entries)
        self.assertEqual(
            reconciliation.result_of(deployment.integration, result_id), row)
        self.assertEqual(
            [one["result_id"] for one in
             deployment.integration._connection.execute(
                 "SELECT result_id FROM integration_results").fetchall()],
            [result_id])
        self.assertEqual((len(self.seen), self.materialized), (1, 1))

    def test_this_deployment_can_admit_only_one_derived_result(self):
        """THE SETUP SEAM, measured rather than asserted.

        Review 2026-09-13T11:36:15Z asks for composed isolation over two
        coherently admitted results and says plainly: if the existing fixture
        cannot create a second derived result, identify its exact setup seam
        rather than substituting a direct-result id. This is that measurement.

        A DERIVED RESULT IS MADE BY THE RECONCILED BRANCH, which a Job takes
        when the canonical target has moved past the proposal it was built on.
        This deployment binds TWO Jobs: the first imports DIRECTLY -- moving
        the target -- and the second reconciles. So one full traversal admits
        exactly ONE `IntegrationResult`, which this drives to completion and
        then counts.

        AND THE FIRST JOB'S IMPORT IS NOT A SECOND ONE. Its accepted entry
        names a result identifier, and the result owner does not hold it: the
        public reader refuses. That is the identifier my own earlier matrix
        used as its "another result" variant, so this is the correction as
        well as the seam.

        WHAT A SECOND DERIVED RESULT TAKES is therefore a THIRD bound Job
        reaching integration after the target moved again -- its own Work in
        the Authority, its own producer and reviewer with the routes and
        capability for it, its own binding and its own submitted Job -- with
        the single configured integrator serializing all three.

        AND THAT IS BUILT, in `_three_jobs` below. When this case was written I
        added that the borrowed fixture having no helper made it a scenario
        change rather than a case; review 2026-09-13T11:49:41Z answered that
        the helpers belong in this Work's own test, and they are there. What
        this case still establishes is what the TWO-Job traversal admits, which
        is one derived result and one direct entry identifier the result owner
        does not hold.
        """
        from baton_v12.contracts import ContractRefusal
        from baton_v12.integration import queue, reconciliation

        held, deployment, result_id, _result = self._judged()
        # EXACTLY TWO JOBS ARE BOUND, which is the fact the rest follows from.
        self.assertEqual(
            sorted(one["job_id"] for one in deployment.given["job_bindings"]),
            ["job-a", "job-b"])
        # `_judged` has already taken the three judgment turns; taking them
        # again is not a second judgment, it is the same turn twice.
        self.case.drive_job(held.job, held.composed, "job-b", "integration",
                            "completed", ticks=14)
        settled = reconciliation.result_of(deployment.integration, result_id)
        self.assertEqual(settled["state"], "imported")
        # ONE DERIVED RESULT, AFTER BOTH JOBS HAVE INTEGRATED.
        self.assertEqual(
            [one["result_id"] for one in
             deployment.integration._connection.execute(
                 "SELECT result_id FROM integration_results").fetchall()],
            [result_id])
        for job_id in ("job-a", "job-b"):
            with self.subTest(job=job_id):
                self.assertEqual(
                    self.case.states_for(held.job, held.composed,
                                         job_id)["integration"], "completed")
        # AND THE DIRECT IMPORT'S IDENTIFIER IS NOT A RESULT THIS OWNER HOLDS.
        entries = queue.entries_of(deployment.integration,
                                   settled["canonical_target_id"])
        direct = [one["result_id"] for one in entries
                  if one["result_id"] != result_id]
        self.assertTrue(direct, entries)
        for one in direct:
            with self.subTest(result=one):
                with self.assertRaises(ContractRefusal) as caught:
                    reconciliation.result_of(deployment.integration, one)
                self.assertIn("result", str(caught.exception).lower())

    # -- a THIRD Job, so two results can fail independently -----------------
    #
    # Review 2026-09-13T11:49:41Z settled the question my last claim left open:
    # the absence of a helper in the borrowed fixture is not an authorization
    # gate, and the additional-Job scenario belongs HERE, in this Work's own
    # test, built out of the fixture primitives. That reviewer's own probe
    # showed two genuine derived results are reachable from the public setup.
    #
    # WHAT A THIRD JOB NEEDS, and every piece is an owner's own act: its Work
    # created in the Authority, the routes that say who may claim on it, the
    # reviewer's capability at the Work's own scope, a producer and a reviewer
    # bound to ITS task and manifest, its binding in the deployment document,
    # its submitted Job carrying the same input digest and its own ceiling, and
    # judges keyed to ITS result. The policy generation is re-read AFTER those
    # acts, because every one of them moves it.
    THIRD_WORK = "0000000a-W6"
    THIRD = {"producer": "other.third", "reviewer": "other.reviewer-3"}
    THIRD_CEILING = 61

    def _third_task(self):
        """Job C's own task, naming a required test the base does not have."""
        payload = json.dumps(
            {"schema": "baton.dogfood-task/2",
             "task_id": "w156162-third-job-regression",
             "instructions": "Add focused coverage for the third Job.",
             "source_root": "source", "source_profile": "git-line",
             "declared_base": self.case.base,
             "verification": ["python3", "check_third.py"]},
            sort_keys=True).encode("utf-8")
        document = os.path.join(self.case.root, "task-third-job.json")
        with open(document, "wb") as writing:
            writing.write(payload)
        return payload, document

    THIRD_FEATURE = "VALUE = 'the third job answered'\n"
    THIRD_CHECK = ("from feature_third import VALUE\n\n"
                   "assert VALUE == 'the third job answered', VALUE\n"
                   "print('the third job feature check passed')\n")

    def _third_edits(self):
        return {"feature_third.py": self.THIRD_FEATURE,
                "check_third.py": self.THIRD_CHECK}

    def _third_manifest(self):
        payload, _document = self._third_task()
        return self.case.manifest_over(self.THIRD_WORK, payload)

    def _bind_third(self, worker):
        payload, document = self._third_task()
        worker["deployment"]["input_manifest"] = self.case.manifest_over(
            self.THIRD_WORK, payload)
        worker["deployment"]["task_document"] = document
        return worker

    def _third_work(self):
        """The Authority's own acts, and the policy read after them."""
        from baton_v12.authority import Authority, V12

        from tests.job_manager import fixtures

        authority = Authority.open(
            self.case.authority_path,
            expected_authority_uuid=self.case.config["authority_uuid"])
        try:
            authority.create_work(self.THIRD_WORK, fixtures.ROUTE,
                                  contract=V12,
                                  operation_id="create-third-job-work")
            authority.add_route_handler(fixtures.ROUTE,
                                        self.THIRD["producer"])
            authority.add_route_handler("rview", self.THIRD["reviewer"])
            # ONLY THE REVIEWER TAKES A GRANT: a producer is authorized by the
            # route it may claim on, and what a capability governs is the
            # judgments a participant may record.
            authority.grant_capability(self.THIRD["reviewer"], "review",
                                       scope=self.case.scope)
            self.case.fixture_policy = authority.policy_generation()
        finally:
            authority.dispose()

    def _three_jobs(self):
        """The deployment document for three Jobs on one canonical target."""
        import copy

        judges = {}
        for job_id in ("job-b", "job-c"):
            judges.update(self.case.judgment_workers(job_id))
        given = self.case.traversing(result_judgment_workers=judges)
        held = {one["worker_id"]: one for one in given["workers"]}
        producer = copy.deepcopy(held["implementation-worker-b"])
        producer["worker_id"] = "implementation-worker-c"
        producer["deployment"]["participant"] = self.THIRD["producer"]
        producer["deployment"]["principal"] = \
            "principal:" + self.THIRD["producer"]
        self._bind_third(producer)
        reviewer = self._bind_third(self.case.role_worker(
            "review", self.THIRD_WORK, "review-worker-c",
            participant=self.THIRD["reviewer"],
            principal="principal:" + self.THIRD["reviewer"],
            review_route=self.case.INTEGRATION_ROUTE))
        given["workers"] = list(given["workers"]) + [producer, reviewer]
        binding = {one["job_id"]: one for one in given["job_bindings"]}
        given["job_bindings"] = given["job_bindings"] + [
            {"job_id": "job-c", "job_work_id": self.THIRD_WORK,
             "review_work_id": self.THIRD_WORK,
             "line_declared_base": self.case.base,
             "canonical_target_id": binding["job-a"]["canonical_target_id"],
             "source_worker_id": "implementation-worker-c"}]
        return given

    def _three_submission(self):
        """The two accepted Jobs and Job C, each with its own ceiling."""
        import copy

        from baton_v12.job_manager import documents
        from tests.job_manager import fixtures

        held = json.loads(json.dumps(self.case.both_jobs()))
        held["schema"] = documents.SUBMISSION_SCHEMA
        third = fixtures.job(
            "job-c",
            input_digest=self._third_manifest()["manifest_digest"],
            policy_digest=fixtures.POLICY_DIGEST,
            stages=[
                fixtures.stage("implementation", self.THIRD_WORK),
                fixtures.stage("review", self.THIRD_WORK,
                               depends_on=[{"job_id": "job-c",
                                            "kind": "implementation"}]),
                fixtures.stage("integration", self.THIRD_WORK,
                               depends_on=[{"job_id": "job-c",
                                            "kind": "review"}])])
        # ITS OWN CEILING, and a DIFFERENT one from Job B's, so the two
        # failures below cannot be confused for each other by their bound.
        third["execution_limits"] = {
            "verification_command_seconds": self.THIRD_CEILING}
        held["jobs"] = list(held["jobs"]) + [third]
        return copy.deepcopy(held)

    def _three_job_serving(self):
        """Three Jobs submitted, coded and accepted on one deployment."""
        from types import SimpleNamespace

        from baton_v12.job_manager import submit

        self._third_work()
        job, control, composed = self.case.serving_two(**self._three_jobs())
        self.addCleanup(composed.close)
        submit(job, self._three_submission())
        held = SimpleNamespace(job=job, control=control, composed=composed)
        self.case.drive_job(job, composed, "job-b", "implementation",
                            "waiting")
        held.first = self.case.one_attempt_of(composed,
                                              "implementation-worker")
        held.second = self.case.one_attempt_of(composed,
                                               "implementation-worker-b")
        held.third = self.case.one_attempt_of(composed,
                                              "implementation-worker-c")
        self.case.accepted(held, "job-a", "implementation-worker",
                           "review-worker", held.first,
                           "print('the first job answered')\n")
        self.case.accepted(held, "job-b", "implementation-worker-b",
                           "review-worker-b", held.second,
                           "print('the second job answered')\n",
                           edits={"feature.py": self.case.B_FEATURE,
                                  "feature_check.py": self.case.B_CHECK})
        self.case.accepted(held, "job-c", "implementation-worker-c",
                           "review-worker-c", held.third,
                           "print('the third job answered')\n",
                           edits=self._third_edits())
        return held

    def test_three_jobs_bind_three_ceilings_and_three_tasks(self):
        """THE SCENARIO ITSELF, before anything is asked to fail.

        A third Job is admitted with its OWN Work, producer, reviewer, task and
        ceiling, and the owners answer for it as themselves: the Job owner
        resolves its submitted bound, the deployment derives its required test
        from ITS configured task, and all three implementations are accepted.
        A scenario nobody can show is coherent is not a scenario to draw
        conclusions from, so this is asserted before the failures are injected.
        """
        from tools import stage_execution

        held = self._three_job_serving()
        deployment = self.case.deployment_of(held.composed)
        for job_id, seconds in (("job-b", self.CEILING),
                                ("job-c", self.THIRD_CEILING)):
            with self.subTest(job=job_id):
                self.assertEqual(
                    stage_execution._host_seconds(deployment,
                                                  {"job_id": job_id}), seconds)
        integration = stage_execution.Integration(deployment)
        self.assertEqual(integration.required_tests("job-b")["argv"],
                         json.loads(self.case.shared_task_bytes)
                         ["verification"])
        self.assertEqual(integration.required_tests("job-c")["argv"],
                         ["python3", "check_third.py"])
        self.assertNotEqual(integration.required_tests("job-b")["task_id"],
                            integration.required_tests("job-c")["task_id"])
        for job_id in ("job-a", "job-b", "job-c"):
            with self.subTest(job=job_id):
                self.assertEqual(
                    self.case.states_for(held.job, held.composed,
                                         job_id)["review"], "completed")

    def _two_failed_results(self):
        """Two Jobs' OWN derived results, each failing its own host command.

        Job A imports directly and moves the target, so Job B and then Job C
        each reach the RECONCILED branch and each runs ITS configured required
        test under ITS admitted ceiling. Both are refused at the host boundary.
        """
        from baton_v12.integration import reconciliation
        from tools import stage_execution

        held = self._three_job_serving()
        deployment = self.case.deployment_of(held.composed)
        integration = stage_execution.Integration(deployment)
        commands = [integration.required_tests(one)["argv"]
                    for one in ("job-b", "job-c")]
        self.assertNotEqual(commands[0], commands[1])
        self._watching(argvs=commands, home=deployment.integration_root,
                       failing=True)
        # JOB A'S DIRECT IMPORT, which is what moves the canonical target and
        # puts the other two on the reconciled branch.
        self.case.drive_job(held.job, held.composed, "job-a", "integration",
                            "integrating")
        attempt = self.case.attempted(held.job,
                                      "job-a/integration")["attempt_id"]
        self.assertEqual(self.case.integration_turn(held, attempt), 0)
        # THE QUIESCENCE IS FOR JOB A'S CONTAINER AND FOR NOTHING ELSE, so it
        # is set for that completion and lifted again. It is deployment-WIDE,
        # which is why it is not simply left on.
        #
        # AND IT IS NOT WHY JOB B ENDS UP `exceptional`. That was my first
        # reading of probe-160341-third-job.py, and the same probe disproves it:
        # with the flag lifted, job-b's integration is exceptional all the same,
        # because the reconciled branch answered `held` with no runtime and
        # nothing settles the stage. The case below asserts THAT, which is the
        # owners' own behaviour rather than this fixture's engine.
        self.case.engine.stopped = True
        self.case.drive_job(held.job, held.composed, "job-a", "integration",
                            "completed", ticks=6)
        self.case.engine.stopped = False
        blocked = {}
        for _ in range(24):
            self.case.tick(held)
            blocked = {
                row["job_id"]: row for row in
                (reconciliation.result_of(deployment.integration,
                                          one["result_id"])
                 for one in deployment.integration._connection.execute(
                     "SELECT result_id FROM integration_results").fetchall())
                if row["state"] == "blocked"}
            if len(blocked) == 2:
                break
        return held, deployment, blocked

    def test_a_blocked_result_holds_the_only_integrator_and_job_c_waits(self):
        """WHY THE SECOND FAILURE IS NOT REACHABLE HERE, measured.

        The scenario above is coherent: three admitted Jobs, three tasks, three
        ceilings. This drives it toward two independent host failures and finds
        a concrete owner behaviour that stops at one, which is what review
        2026-09-13T11:49:41Z asked me to name if I met it.

        JOB B'S FAILURE IS ADOPTED DURABLY -- its own result, blocked, carrying
        its own command, task identity and 77-second bound. And then its
        integration stage is **exceptional**: the reconciled branch that
        answered `held` started no runtime, and the stage does not leave that
        state by itself. This deployment configures ONE integrator, so from
        that tick on every admission of `job-c/integration` is DEFERRED with
        the capacity owner's own sentence -- "every effective worker/principal
        capacity is reserved or recovery-required" -- and job-c stays `queued`.

        THE PUBLIC RECOVERY VERB DOES NOT FREE IT: `recover` answers nothing
        abandoned and nothing recoverable. So job-c's configured command never
        runs at all, and the reason is CAPACITY rather than the retention --
        which is asserted below by the deferral itself, not inferred from the
        counter.

        WHAT A SECOND SIMULTANEOUS FAILURE WOULD TAKE is therefore integration
        capacity that a blocked result does not hold: another integrator
        participant with its own worker, or a second deployment. Both are
        scenario operands beyond the one this Work's fixture configures, and
        neither is invented here.
        """
        from baton_v12.integration import reconciliation
        from tests.job_manager import fixtures
        from tools import stage_execution

        held, deployment, blocked = self._two_failed_results()
        # ONE FAILURE, AND IT IS JOB B'S OWN.
        self.assertEqual(sorted(blocked), ["job-b"])
        answer = blocked["job-b"]["causal_observations"]
        self.assertEqual(answer["seconds"], self.CEILING)
        self.assertEqual(answer["command"],
                         json.loads(self.case.shared_task_bytes)
                         ["verification"])
        self.assertEqual(answer["reason"], "timeout")
        self.assertEqual(len(self.seen), 1, self.seen)
        # JOB C'S OWN COMMAND NEVER RAN: no call carried ITS bound.
        self.assertNotIn(self.THIRD_CEILING,
                         [seconds for _argv, seconds in self.seen])

        states = {one: self.case.states_for(held.job, held.composed, one)
                  for one in ("job-a", "job-b", "job-c")}
        self.assertEqual(states["job-a"]["integration"], "completed")
        self.assertEqual(states["job-b"]["integration"], "exceptional")
        self.assertEqual(states["job-c"]["integration"], "queued")

        # AND THE REASON JOB C WAITS IS THE CAPACITY OWNER'S OWN, read from the
        # sweep it refuses in rather than inferred from the counter.
        deferred = []
        for _ in range(4):
            report = self.case.tick(held)
            deferred += [one for one in report.get("acts", [])
                         if one.get("stage_id") == "job-c/integration"]
        self.assertTrue(deferred, "job-c/integration was never even asked")
        self.assertEqual({one["outcome"] for one in deferred}, {"deferred"})
        self.assertTrue(
            all("capacity is reserved or recovery-required"
                in (one.get("detail") or {}).get("message", "")
                for one in deferred), deferred)

        # THE PUBLIC RECOVERY VERB FINDS NOTHING TO RECOVER.
        recovered = held.composed.recover(now=fixtures.NOW)
        self.assertEqual(recovered, {"abandoned": [], "recoverable": []})

        # NOTHING RAN THROUGHOUT, and the retention holds exactly the one
        # failure this deployment actually made.
        self.assertEqual(len(self.seen), 1)
        retained = stage_execution._host_retention(deployment)
        self.assertEqual(len(retained), 1, retained)
        [(scope, argv, _revision, seconds, _harness)] = list(retained)
        self.assertEqual((scope[0], scope[2], seconds),
                         ("job-b", "causal", self.CEILING))
        self.assertEqual(list(argv), answer["command"])
        self.assertEqual(
            reconciliation.result_of(deployment.integration,
                                     blocked["job-b"]["result_id"]),
            blocked["job-b"])

    def test_the_retained_failure_is_keyed_by_the_work_it_is_about(self):
        """WHOSE WORK A RETAINED FAILURE IS, from the key the owner made.

        The name and docstring this case used to carry said a fresh process
        would attempt the command again -- which this case never drove, and
        which review 2026-09-13T11:49:41Z established is not the behaviour
        either: the causal failure settles the result BLOCKED in owner custody,
        and `test_resumed_serving_after_a_reopen_runs_no_command` drives
        exactly that reopen and counts no command. What is asserted here is
        what is actually read: the key's scope, command and bound.
        """
        from tools import stage_execution

        self._watching(failing=True)
        held = self.case.integrating(
            result_judgment_workers=self.case.judgment_workers())
        self.case.drive_job(held.job, held.composed, "job-a", "integration",
                            "completed", ticks=4)
        self.case.tick(held)
        deployment = self.case.deployment_of(held.composed)
        retained = stage_execution._host_retention(deployment)
        self.assertEqual(len(retained), 1, retained)
        [(scope, argv, _revision, seconds, _harness)] = list(retained)
        self.assertEqual(seconds, self.CEILING)
        self.assertEqual(list(argv), list(self.required_argv()))
        # AND THE KEY NAMES WHOSE WORK IT IS: Job, result and phase. A
        # retention shared by a deployment must not let one result's failure
        # speak for another's.
        self.assertEqual(scope[0], "job-b")
        self.assertEqual(scope[2], "causal")
        self.assertTrue(scope[1])
        # AND WHAT IS STILL MISSING IS NAMED IN THE SOURCE, not only here. It
        # is no longer "a durable outcome" -- the owners record that -- but the
        # attempt that never reached them and the terminal account it leaves.
        self.assertIn("before reaching its owner",
                      stage_execution.HOST_OBSERVATION_CONTRACT)

    def _judged(self):
        """The reconciled result carried to its three accepted verdicts.

        THE CAUSAL HALF RUNS NORMALLY, so the post-import command is the only
        one an injection armed afterwards can reach -- and the watch is armed
        with the deployment ALREADY IN HAND, because composing another to read
        an argv resets the fixture's own.
        """
        held, deployment, result_id, result = self.case.pending_judgments()
        for execution in deployment.judges.values():
            self.case.judgment_turn(held, execution)
        # NO TICK HERE. The post-import command runs on the next ordinary tick,
        # and taking one before the watch is armed spends the very call this is
        # here to observe.
        return held, deployment, result_id, result

    def _scratch_count(self, held):
        """Temporary trees under this deployment's own integration root."""
        home = self.case.deployment_of(held.composed).integration_root
        if not os.path.isdir(home):
            return 0
        return len([one for one in os.listdir(home)
                    if os.path.isdir(os.path.join(home, one))])

    def _post_import_failure(self, **failing):
        """Drive to the post-import command and refuse it there."""
        held, deployment, result_id, _result = self._judged()
        before = self._scratch_count(held)
        # THE ACCEPTED COMMAND FROM THE CONFIGURED TASK ITSELF. `required_tests`
        # would do, but reaching it needs a deployment, and the helper that
        # composes one resets the fixture's own -- so the argv comes from the
        # task document this deployment is configured with, which is what that
        # owner derives it from.
        self._watching(
            argv=json.loads(self.case.shared_task_bytes)["verification"],
            home=deployment.integration_root, **failing)
        for _ in range(4):
            self.case.tick(held)
        return held, deployment, result_id, before

    def test_the_post_import_verification_uses_the_jobs_ceiling(self):
        """THE SECOND HOST BOUNDARY, reachable at last.

        `_ImportedVerifier` runs the required test against the IMPORTED commit
        in the dedicated target. It is a different owner, a different basis and
        a different failure path from the causal observer, and no case of mine
        had driven it -- because the watch itself was recomposing the
        deployment out from under the branch.
        """
        held, _deployment, _result_id, _before = self._post_import_failure()
        self.assertTrue(self.seen, "the post-import verifier ran no command")
        self.assertEqual({seconds for _argv, seconds in self.seen},
                         {self.CEILING})
        del held

    def test_a_post_import_overrun_runs_once_and_defers(self):
        """The overrun at this boundary: ONE call across four ordinary ticks,
        at the Job's own number, and a deferral carrying the real reason."""
        held, deployment, _result_id, _before = self._post_import_failure(
            failing=True)
        self.assertEqual([seconds for _argv, seconds in self.seen],
                         [self.CEILING])
        self.assertEqual(
            {one[0][2] for one in self._retention(held)}, {"post-import"})
        del deployment

    def test_a_post_import_start_failure_is_the_same_shape(self):
        """The OTHER way a host command produces no exit status: the child
        never ran. It is retained and refused exactly as the overrun is, and
        the phase in its key is this branch's."""
        held, _deployment, _result_id, _before = self._post_import_failure(
            error=FileNotFoundError("no such required test"))
        self.assertEqual([seconds for _argv, seconds in self.seen],
                         [self.CEILING])
        retained = self._retention(held)
        self.assertEqual({one[0][2] for one in retained}, {"post-import"})
        self.assertTrue(any("could not be started" in message
                            for message in retained.values()), retained)

    def _retention(self, held):
        from tools import stage_execution

        return stage_execution._host_retention(
            self.case.deployment_of(held.composed))

    def test_the_failed_scratch_is_disposed_of(self):
        """STEP 5 OF THE APPROVED RULING: the temporary materialization goes.

        My previous claim asserted this tree SURVIVED and recorded that as a
        measured limitation, which it was. The owner approved the proposal that
        owns it, so the run disposes of the tree once its diagnostic is in the
        failure answer -- nothing needs those bytes afterwards, and a failed run
        owning a path with no lifecycle is what that step exists to end.

        REPEATED POLLS STILL ADD NONE, which was true before and stays true:
        the retained failure refuses before anything is materialized.
        """
        held, _deployment, _result_id, before = self._post_import_failure(
            failing=True)
        after = self._scratch_count(held)
        self.assertEqual(after, before,
                         "the failed attempt left its temporary tree behind")
        for _ in range(4):
            self.case.tick(held)
        self.assertEqual(self._scratch_count(held), before)

    def test_a_repeated_tick_after_that_runs_no_second_command(self):
        """NO DUPLICATE WORK after observation. The causal observations are
        retained by their owner, so a further ordinary tick over the same
        result does not run the accepted command again."""
        self._watching()
        held, _deployment, _result_id, _result = self.case.pending_judgments()
        before = len(self.seen)
        self.assertTrue(before)
        for _ in range(3):
            self.case.tick(held)
        self.assertEqual(len(self.seen), before,
                         "a repeated tick re-ran the accepted command")


class TheTwoReadersResolveOneJobIdentically(unittest.TestCase):
    """The narrow fact the composed acceptance rests on, kept as its own case.

    `_Observation` adopts the delivery the SERVING composition materialized and
    `adopt` compares canonical bytes, so the two readers must resolve a Job's
    configuration identically or every Job-bound launch is reported unreadable
    on every status pass.

    THIS IS A HELPER-LEVEL CASE AND SAYS SO. It calls the two readers directly
    over one real Job owner. What it does NOT establish -- `observation_from`,
    a read-only open, the adopted launch bytes, absent-artifact behaviour or the
    absence of other writes -- is established by
    `TheComposedObservationAdoptsTwoJobsConfiguredLaunches`, which drives the
    real serving and observation factories.
    """

    def setUp(self):
        from tests.job_manager import fixtures as job_fixtures
        from baton_v12.job_manager import JobStore, documents, submit

        self.root = tempfile.mkdtemp(prefix="v12-w156162-observe-")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.store = JobStore.open(
            os.path.join(self.root, "jobs.sqlite3"),
            authority_uuid=job_fixtures.UUID, incarnation="jobs-1",
            clock=lambda: job_fixtures.NOW)
        self.addCleanup(self.store.close)
        held = json.loads(json.dumps(job_fixtures.submission()))
        held["schema"] = documents.SUBMISSION_SCHEMA
        held["jobs"][0]["execution_limits"] = {
            "provider_turn_seconds": 90, "verification_command_seconds": 45}
        submit(self.store, held)

    def readers(self):
        from tools import single_worker

        given = {"input_manifest": {"manifest_digest": "sha256:runtime"},
                 "policy_digest": "sha256:policy"}
        reader = single_worker.job_execution_reader(self.store)
        return [SimpleNamespace(execution_context=reader, given=given),
                SimpleNamespace(execution_context=reader, given=given)]

    def test_both_compositions_resolve_the_same_bytes(self):
        from tools import single_worker

        serving, observing = self.readers()
        stage = {"job_id": "job-a", "attempt_id": "attempt-1"}
        first = single_worker._SingleWorker._job_execution(serving, stage)
        second = single_worker._Observation._job_execution(observing, stage)
        self.assertEqual(
            json.dumps(first, sort_keys=True, separators=(",", ":")),
            json.dumps(second, sort_keys=True, separators=(",", ":")))
        boundaries = first["execution_limits"]["boundaries"]
        self.assertEqual(boundaries["provider_turn"]["seconds"], 90)
        self.assertEqual(boundaries["ordinary_verification"]["seconds"], 45)

    def test_a_foreign_job_is_refused_on_the_read_only_path_too(self):
        from tools import single_worker

        _serving, observing = self.readers()
        with self.assertRaises(Exception) as caught:
            single_worker._Observation._job_execution(
                observing, {"job_id": "job-never-admitted",
                            "attempt_id": "attempt-1"})
        self.assertIn("no such Job", str(caught.exception))

    def test_a_missing_context_is_refused_on_the_read_only_path_too(self):
        from tools import single_worker

        _serving, observing = self.readers()
        with self.assertRaises(Exception) as caught:
            single_worker._Observation._job_execution(
                observing, {"attempt_id": "attempt-1"})
        self.assertIn("names no Job", str(caught.exception))


class TheComposedObservationAdoptsTwoJobsConfiguredLaunches(unittest.TestCase):
    """A/B THROUGH THE ACTUAL SERVING AND OBSERVATION FACTORIES.

    My earlier read-only cases called `_job_execution` on `SimpleNamespace`
    objects over a writable store and compared one table's rows. That proved
    consistent context READING and nothing about observation: not
    `observation_from`, not a read-only open, not the adopted launch bytes, not
    the absence of other writes or acts.

    THE SEAMS HERE ARE THE ONES THE REVIEWER'S OWN BASELINE ESTABLISHED, adopted
    rather than reinvented: two Jobs configured with DISTINCT settings through
    their own submission, the real serving run driven and then CLOSED, the
    ControlStore publicly reopened READ-ONLY, `observation_from` composing the
    reader, and six alternating A/B/A `launch.adopt` calls whose documents must
    carry each Job's own numbers and equal what serving exchanged.

    ONE CLARIFICATION IS THE REVIEWER'S AND IT CORRECTS MY EARLIER SHORTHAND:
    `JobStore` has NO public read-only opener, and this does not invent a
    requirement for one. The already-open current-schema Job handle is retained
    and a SQLite authorizer rejects every write through it for the duration of
    the read window, which is what makes "the observation writes nothing" a
    measured fact rather than a claim.
    """

    A = {"provider_turn_seconds": 31, "verification_command_seconds": 29}
    B = {"provider_turn_seconds": 67, "verification_command_seconds": 43}

    def setUp(self):
        from tests.tools import test_stage_execution as composed
        from baton_v12.job_manager import documents

        self.case = composed.TwoBoundJobsTraverseServingAndCorrection(
            "test_two_accepted_jobs_share_one_integrator_one_at_a_time")
        original = self.case.both_jobs

        def both():
            held = json.loads(json.dumps(original()))
            held["schema"] = documents.SUBMISSION_SCHEMA
            for job in held["jobs"]:
                job["execution_limits"] = dict(
                    self.A if job["job_id"] == "job-a" else self.B)
            return held

        self.case.both_jobs = both
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)
        self.fixtures = composed

    def _served(self):
        """One real serving run, and the stages and exchanges it produced."""
        from baton_v12.job_manager import episodes_of, stages_of

        held = self.case.coding()
        stages = {}
        for job_id in ("job-a", "job-b"):
            row = next(one for one in stages_of(held.job, job_id)
                       if one["kind"] == "implementation")
            episode = episodes_of(held.job, row["stage_id"])[-1]
            stages[job_id] = dict(row, **{key: value
                                          for key, value in episode.items()
                                          if key not in row})
        exchanges = {job_id: held.composed.observe(one)["exchange"]
                     for job_id, one in stages.items()}
        for job_id, one in exchanges.items():
            self.assertIsNotNone(one, job_id)
            self.assertNotEqual(one.get("state"), "unreadable", job_id)
        return held, stages, exchanges

    def _guarded(self, held, stack, captured, *, present=True):
        """Refuse every act an observation must not perform, and watch adopt."""
        from unittest.mock import patch
        from baton_v12.authority import Authority
        from baton_v12.integration import IntegrationStore
        from baton_v12.worker_manager import launch as launch_owner
        from tools import stage_execution

        for owner, name in ((Authority, "open"), (Authority, "session"),
                            (IntegrationStore, "open"),
                            (stage_execution, "operations_from"),
                            (stage_execution.scheduler, "activate_pool"),
                            (stage_execution.review_cycles, "create_line"),
                            (stage_execution.single_worker,
                             "worker_preflight")):
            stack.enter_context(patch.object(
                owner, name,
                side_effect=AssertionError("observation acted: " + name)))
        adopting = launch_owner.adopt

        def watched(*arguments, **named):
            answered = adopting(*arguments, **named)
            if not present:
                # ABSENCE IS THE ORDINARY ANSWER and the launch owner says so:
                # `None` is what lets a caller tell "no delivery was ever made"
                # apart from "a delivery this build failed to prove".
                self.assertIsNone(answered)
                return answered
            self.assertIsNotNone(answered)
            context = answered.document["job_execution"]
            # THE DOCUMENT IS THE ONE THIS READER EXPECTED, byte for byte --
            # `adopt` compares canonical bytes and this is what it compared.
            self.assertEqual(context, named["job_execution"])
            captured.append(context)
            return answered

        stack.enter_context(patch.object(launch_owner, "adopt",
                                         side_effect=watched))

    def _writes_rejected(self, held):
        """Reject every write through the retained Job handle."""
        import sqlite3

        denied = {sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE,
                  sqlite3.SQLITE_DELETE, sqlite3.SQLITE_CREATE_TABLE,
                  sqlite3.SQLITE_DROP_TABLE, sqlite3.SQLITE_ALTER_TABLE,
                  sqlite3.SQLITE_CREATE_INDEX, sqlite3.SQLITE_DROP_INDEX}
        held.job._connection.set_authorizer(
            lambda action, *rest: (sqlite3.SQLITE_DENY if action in denied
                                   else sqlite3.SQLITE_OK))
        self.addCleanup(held.job._connection.set_authorizer, None)

    def _store_bytes(self):
        import hashlib
        import pathlib

        places = (self.case.job_path, self.case.control_path,
                  self.case.authority_path, self.case.integration_store)
        return {one: hashlib.sha256(pathlib.Path(one).read_bytes()).hexdigest()
                for one in places if os.path.exists(one)}

    def test_two_configured_jobs_are_adopted_by_a_read_only_observation(self):
        """THE WHOLE SEAM: distinct settings, real serving, a closed serving
        composition, a publicly reopened read-only ControlStore, and six
        alternating adoptions that each carry their own Job's numbers."""
        import contextlib
        from baton_v12.worker_manager import ControlStore
        from tools import stage_execution

        held, stages, exchanges = self._served()
        document = self.case.composed_document(
            line_declared_base=self.case.base, **self.case.traversing())
        held.composed.close()
        held.control.close()
        before = self._store_bytes()
        changes = held.job._connection.total_changes
        self._writes_rejected(held)
        captured = []
        with ControlStore.open_readonly(
                self.case.control_path, incarnation="w156162-readonly",
                clock=lambda: self.fixtures.NOW) as control, \
                contextlib.ExitStack() as stack:
            self._guarded(held, stack, captured)
            for _ in range(2):
                reader = stage_execution.observation_from(
                    document, held.job, control, checkout=self.case.checkout)
                for job_id in ("job-a", "job-b", "job-a"):
                    with self.subTest(job=job_id):
                        self.assertEqual(
                            reader.observe_exchange(stages[job_id]),
                            exchanges[job_id])
        # SIX ADOPTIONS, EACH CARRYING ITS OWN JOB'S NUMBERS.
        self.assertEqual(len(captured), 6)
        self.assertEqual([one["job_id"] for one in captured],
                         ["job-a", "job-b", "job-a"] * 2)
        for one in captured:
            with self.subTest(job=one["job_id"]):
                wanted = self.A if one["job_id"] == "job-a" else self.B
                boundaries = one["execution_limits"]["boundaries"]
                self.assertEqual(boundaries["provider_turn"]["seconds"],
                                 wanted["provider_turn_seconds"])
                self.assertEqual(
                    boundaries["ordinary_verification"]["seconds"],
                    wanted["verification_command_seconds"])
        # AND THE OBSERVATION WROTE NOTHING AND ACTED ON NOTHING.
        self.assertEqual(held.job._connection.total_changes, changes)
        self.assertEqual(self._store_bytes(), before)

    def test_a_second_reader_repeats_the_adoption_without_repairing(self):
        """NO DUPLICATE WORK AND NO REPAIR: the second reader in the run above
        adopts the same deliveries and changes nothing, which is why the
        alternation is driven twice rather than once."""
        import contextlib
        from baton_v12.worker_manager import ControlStore
        from tools import stage_execution

        held, stages, exchanges = self._served()
        document = self.case.composed_document(
            line_declared_base=self.case.base, **self.case.traversing())
        held.composed.close()
        held.control.close()
        self._writes_rejected(held)
        captured = []
        with ControlStore.open_readonly(
                self.case.control_path, incarnation="w156162-readonly",
                clock=lambda: self.fixtures.NOW) as control, \
                contextlib.ExitStack() as stack:
            self._guarded(held, stack, captured)
            first = stage_execution.observation_from(
                document, held.job, control, checkout=self.case.checkout)
            second = stage_execution.observation_from(
                document, held.job, control, checkout=self.case.checkout)
            for reader in (first, second):
                self.assertEqual(reader.observe_exchange(stages["job-a"]),
                                 exchanges["job-a"])
        self.assertEqual(len(captured), 2)
        self.assertEqual(captured[0], captured[1])

    def test_an_absent_delivery_is_answered_and_never_repaired(self):
        """ABSENT ARTIFACT: an attempt whose launch root does not exist is
        answered as absent. An observation does not materialize a replacement --
        authoring one under a container that may hold the mount is the
        correction the launch owner already records, and it applies with more
        force to a read-only path."""
        import contextlib
        from baton_v12.worker_manager import ControlStore
        from tools import stage_execution

        held, stages, _exchanges = self._served()
        document = self.case.composed_document(
            line_declared_base=self.case.base, **self.case.traversing())
        held.composed.close()
        held.control.close()
        home = self.case.config["launch_home"]
        root = os.path.join(os.path.realpath(home),
                            stages["job-a"]["attempt_id"])
        self.assertTrue(os.path.isdir(root))
        # REMOVED THROUGH THE LAUNCH OWNER'S OWN `discard`, which is what a
        # manager uses: the root is the manager's and its document is
        # read-only, so a fixture walking it by hand would be inventing a
        # removal path this build does not have.
        self.assertTrue(launch.discard(root))
        before = self._store_bytes()
        self._writes_rejected(held)
        with ControlStore.open_readonly(
                self.case.control_path, incarnation="w156162-readonly",
                clock=lambda: self.fixtures.NOW) as control, \
                contextlib.ExitStack() as stack:
            self._guarded(held, stack, [], present=False)
            reader = stage_execution.observation_from(
                document, held.job, control, checkout=self.case.checkout)
            answered = reader.observe_exchange(stages["job-a"])
        # ABSENCE IS THE ANSWER, and it is asserted rather than discarded.
        # Review 2026-09-13T04:59:02Z: the independent probe captured exactly
        # `None` here, and a regression that threw the answer away could not
        # tell absence from a delivery it failed to prove.
        self.assertIsNone(answered)
        self.assertFalse(os.path.exists(root),
                         "the observation recreated a delivery it only reads")
        self.assertEqual(self._store_bytes(), before)


FRESH_PROCESS = r'''
"""W156162: a FRESH PROCESS adopts two Jobs' configured launches.

A second observation object in the serving process is not a fresh process, and
review 2026-09-13T04:59:02Z said so. This is a real child: it opens the stores
itself, composes the observation factory, and adopts each attempt's delivery --
which `adopt` proves by canonical bytes -- with every serving act guarded.
"""
import contextlib
import json
import sys
from unittest.mock import patch

from baton_v12.authority import Authority
from baton_v12.integration import IntegrationStore
from baton_v12.job_manager import JobStore
from baton_v12.worker_manager import ControlStore
from baton_v12.worker_manager import launch as launch_owner
from tools import stage_execution

spec = json.load(open(sys.argv[1]))
clock = lambda: spec["now"]
captured = []
with JobStore.open(spec["job"], authority_uuid=spec["uuid"],
                   incarnation="w156162-fresh", clock=clock) as job,         ControlStore.open_readonly(spec["control"],
                                   incarnation="w156162-fresh",
                                   clock=clock) as control,         contextlib.ExitStack() as guards:
    for owner, name in ((Authority, "open"), (Authority, "session"),
                        (IntegrationStore, "open"),
                        (stage_execution, "operations_from"),
                        (stage_execution.scheduler, "activate_pool"),
                        (stage_execution.review_cycles, "create_line"),
                        (stage_execution.single_worker, "worker_preflight")):
        guards.enter_context(patch.object(
            owner, name, side_effect=AssertionError("read reached " + name)))
    reader = stage_execution.observation_from(
        json.load(open(spec["config"])), job, control,
        checkout=spec["checkout"])
    # THE ADOPTION ITSELF IS THE SEAM, as it is in the in-process case: what
    # `adopt` was handed is what it compared canonical bytes against, so the
    # context is read there rather than through a private attribute.
    adopting = launch_owner.adopt

    def watched(*arguments, **named):
        answered = adopting(*arguments, **named)
        assert answered is not None
        context = answered.document["job_execution"]
        assert context == named["job_execution"], context
        bounds = context["execution_limits"]["boundaries"]
        captured.append({"job_id": context["job_id"],
                         "attempt_id": context["attempt_id"],
                         "provider_turn": bounds["provider_turn"]["seconds"],
                         "ordinary_verification":
                             bounds["ordinary_verification"]["seconds"]})
        return answered

    guards.enter_context(patch.object(launch_owner, "adopt",
                                      side_effect=watched))
    for job_id in spec["order"]:
        stage = spec["stages"][job_id]
        answered = reader.observe_exchange(stage)
        assert answered == spec["exchanges"][job_id], (job_id, answered)
print(json.dumps(captured))
'''


class AFreshProcessAdoptsBothJobsConfiguredLaunches(unittest.TestCase):
    """FRESH-PROCESS OWNERSHIP, which a second observation object is not.

    Review 2026-09-13T04:59:02Z named the existing
    `test_fresh_process_observes_owned_completion_after_serving_closes` and its
    `READONLY_PROCESS` as the source examples to revalidate and reuse. This
    follows that shape without editing that file: the serving composition and
    both stores are CLOSED, the configuration and the observed exchanges are
    written out, and a real child opens the stores itself, composes
    `observation_from`, and adopts each attempt's delivery alternately.

    WHAT THE CHILD ESTABLISHES that the in-process case cannot: the Job handle
    is a NEW one, so a context remembered anywhere in the serving process
    cannot be what answers. Both Jobs' own numbers come back, and the parent's
    four store files are byte-identical afterwards.
    """

    A = {"provider_turn_seconds": 31, "verification_command_seconds": 29}
    B = {"provider_turn_seconds": 67, "verification_command_seconds": 43}
    ORDER = ("job-a", "job-b", "job-a")

    def setUp(self):
        from tests.tools import test_stage_execution as composed
        from baton_v12.job_manager import documents

        self.case = composed.TwoBoundJobsTraverseServingAndCorrection(
            "test_two_accepted_jobs_share_one_integrator_one_at_a_time")
        original = self.case.both_jobs

        def both():
            held = json.loads(json.dumps(original()))
            held["schema"] = documents.SUBMISSION_SCHEMA
            for job in held["jobs"]:
                job["execution_limits"] = dict(
                    self.A if job["job_id"] == "job-a" else self.B)
            return held

        self.case.both_jobs = both
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)
        self.fixtures = composed

    def test_the_child_answers_each_jobs_own_numbers(self):
        import hashlib
        import pathlib
        import subprocess

        from baton_v12.job_manager import episodes_of, stages_of

        held = self.case.coding()
        stages, exchanges = {}, {}
        for job_id in ("job-a", "job-b"):
            row = next(one for one in stages_of(held.job, job_id)
                       if one["kind"] == "implementation")
            episode = episodes_of(held.job, row["stage_id"])[-1]
            stages[job_id] = dict(row, **{key: value
                                          for key, value in episode.items()
                                          if key not in row})
            exchanges[job_id] = held.composed.observe(
                stages[job_id])["exchange"]
            self.assertIsNotNone(exchanges[job_id], job_id)
        document = self.case.composed_document(
            line_declared_base=self.case.base, **self.case.traversing())
        configuration = os.path.join(self.case.root, "w156162-config.json")
        self.case.write(configuration, json.dumps(document))
        # EVERYTHING THE SERVING PROCESS HELD IS CLOSED BEFORE THE CHILD RUNS.
        held.composed.close()
        held.job.close()
        held.control.close()
        protected = (self.case.job_path, self.case.control_path,
                     self.case.authority_path, self.case.integration_store)
        before = {one: hashlib.sha256(pathlib.Path(one).read_bytes()).digest()
                  for one in protected if os.path.exists(one)}
        script = os.path.join(self.case.root, "w156162-fresh.py")
        self.case.write(script, FRESH_PROCESS)
        specification = os.path.join(self.case.root, "w156162-spec.json")
        self.case.write(specification, json.dumps({
            "job": self.case.job_path, "control": self.case.control_path,
            "uuid": self.case.config["authority_uuid"],
            "checkout": self.case.checkout, "config": configuration,
            "now": job_fixtures.NOW, "order": list(self.ORDER),
            "stages": stages, "exchanges": exchanges}))
        answered = subprocess.run(
            [sys.executable, script, specification],
            cwd=self.fixtures.REPOSITORY / "v12/python",
            env={**self.case.environment(), "PYTHONPATH": "src:.",
                 self.fixtures.stage_execution.CONFIG_ENV: configuration},
            capture_output=True, text=True, timeout=60)
        self.assertEqual(answered.returncode, 0, answered.stderr)
        captured = json.loads(answered.stdout)
        self.assertEqual([one["job_id"] for one in captured],
                         list(self.ORDER))
        for one in captured:
            with self.subTest(job=one["job_id"]):
                wanted = self.A if one["job_id"] == "job-a" else self.B
                self.assertEqual(one["provider_turn"],
                                 wanted["provider_turn_seconds"])
                self.assertEqual(one["ordinary_verification"],
                                 wanted["verification_command_seconds"])
        # AND THE CHILD CHANGED NOTHING, across the four named store files.
        self.assertEqual(
            {one: hashlib.sha256(pathlib.Path(one).read_bytes()).digest()
             for one in protected if os.path.exists(one)}, before)


class AReopenedServingKeepsBothJobsLaunchesUntouched(unittest.TestCase):
    """CONTINUED CONFIGURED A/B SERVING ACROSS AN OWNERSHIP REOPEN.

    A fresh process OBSERVING a delivery is a different fact from a serving
    composition being taken down and brought back up over the same stores, and
    review 2026-09-13T05:05:13Z was explicit that the first does not discharge
    the second. This is the second.

    THE FIRST FORM OF THIS CASE PASSED ON A LOST RUNTIME, and review
    2026-09-13T05:13:48Z is why it is rewritten. `serving_two` composes a NEW
    `_ConcurrentEngine`, so the reopened deployment saw no containers at all:
    the first sweep reported both attempts DESTROYED and the next reported them
    not-asked. An empty start list proves no restart only in a scenario where
    there was nothing left to restart -- which is not continued serving, and is
    not what I claimed it was.

    SO THE DAEMON SURVIVES THE CLIENT. The engine models an external process
    boundary, and a composition being rebuilt does not stop containers; the same
    engine object is handed to the reopened composition, which is what a real
    reopen meets. The sweeps' own answers are then asserted -- both attempts
    still running, nothing destroyed -- and the counts are taken per attempt on
    that one engine, before and after.
    """

    A = {"provider_turn_seconds": 31, "verification_command_seconds": 29}
    B = {"provider_turn_seconds": 67, "verification_command_seconds": 43}

    def setUp(self):
        from tests.tools import test_stage_execution as composed
        from baton_v12.job_manager import documents

        self.case = composed.TwoBoundJobsTraverseServingAndCorrection(
            "test_two_accepted_jobs_share_one_integrator_one_at_a_time")
        original = self.case.both_jobs

        def both():
            held = json.loads(json.dumps(original()))
            held["schema"] = documents.SUBMISSION_SCHEMA
            for job in held["jobs"]:
                job["execution_limits"] = dict(
                    self.A if job["job_id"] == "job-a" else self.B)
            return held

        self.case.both_jobs = both
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)

    def starts_naming(self, attempt_id):
        """Every engine `run` whose OWN OPERANDS name this attempt.

        The launch labels carry the attempt; the runtime id does not exist
        until the engine answers, so counting by an input identity is what lets
        a second container for one attempt be seen at all.
        """
        held = [list(one) for one in self.case.engine.starts
                if any(attempt_id in str(operand) for operand in one)]
        # AND A CUSTODY HELPER IS NOT A WORKLOAD. Review 2026-09-13T05:21:14Z:
        # each attempt's turn also runs two `--entrypoint` containers that take
        # custody of the workspace; counting those as duplicate workloads would
        # report three starts for one container that ran once.
        return [one for one in held if "--entrypoint" not in one]

    def test_a_reopened_serving_adopts_the_same_two_deliveries(self):
        from unittest.mock import patch
        from baton_v12.job_manager import episodes_of, stages_of, sweep
        from tests.job_manager import fixtures

        held = self.case.coding()
        stages, expected, delivered = {}, {}, {}
        for job_id in ("job-a", "job-b"):
            row = next(one for one in stages_of(held.job, job_id)
                       if one["kind"] == "implementation")
            episode = episodes_of(held.job, row["stage_id"])[-1]
            stages[job_id] = dict(row, **{key: value
                                          for key, value in episode.items()
                                          if key not in row})
            expected[job_id] = held.composed.observe(
                stages[job_id])["exchange"]
            # THE LITERAL DELIVERY ON DISK, path and bytes. The rest of this
            # case compares semantic context and exchanges; review
            # 2026-09-13T05:13:48Z asked for the bytes themselves as well,
            # because that is what a container actually reads.
            delivered[job_id] = self._launch_bytes(stages[job_id])
        # THE ORIGINAL CONTAINERS' MOUNTS, SAVED WHILE THEIR COMPOSITION IS
        # STILL OPEN. The reopened one has no `_prepared` map for attempts it
        # did not prepare.
        roots = {job_id: self.case.mounted_at(held.composed,
                                              one["attempt_id"])
                 for job_id, one in stages.items()}
        before = {job_id: len(self.starts_naming(one["attempt_id"]))
                  for job_id, one in stages.items()}
        for job_id, count in before.items():
            self.assertEqual(count, 1, (job_id, count))
        # BOTH CONTAINERS ARE LIVE BEFORE THE REOPEN.
        for job_id in stages:
            self.assertEqual(
                self.case.states_for(held.job, held.composed, job_id)
                ["implementation"], "waiting", job_id)
        document = self.case.traversing()
        engine = self.case.engine

        # THE SERVING COMPOSITION IS TAKEN DOWN, AND THE DAEMON IS NOT. An
        # engine is an external process boundary; rebuilding a client does not
        # stop containers, so the same engine meets the reopened composition.
        held.composed.close()
        held.job.close()
        held.control.close()
        with patch.object(type(self.case), "quiescing", return_value=engine):
            job, control, composed = self.case.serving_two(**document)
        self.assertIs(self.case.engine, engine)
        self.addCleanup(composed.close)
        reports = [sweep(job, composed, now=fixtures.NOW) for _ in range(3)]

        # THE SWEEPS' OWN ANSWERS, and they are asserted POSITIVELY rather than
        # as an absence: every reopened sweep reports both implementation
        # attempts `running`. "Not destroyed" was the first form's assertion and
        # it is satisfiable by a sweep that reports nothing at all -- which is
        # exactly what the lost-runtime version did.
        wanted = {one["attempt_id"] for one in stages.values()}
        for index, report in enumerate(reports):
            seen = {one["attempt_id"]: one["state"]
                    for one in report["refreshed"]
                    if one["attempt_id"] in wanted}
            with self.subTest(sweep=index):
                self.assertEqual(sorted(seen), sorted(wanted))
                self.assertEqual(set(seen.values()), {"running"}, seen)
        for job_id in stages:
            self.assertEqual(
                self.case.states_for(job, composed, job_id)["implementation"],
                "waiting", job_id)

        captured = self._adoptions(composed, stages)
        for job_id, context in captured.items():
            with self.subTest(job=job_id):
                wanted = self.A if job_id == "job-a" else self.B
                boundaries = context["execution_limits"]["boundaries"]
                self.assertEqual(context["job_id"], job_id)
                self.assertEqual(boundaries["provider_turn"]["seconds"],
                                 wanted["provider_turn_seconds"])
                self.assertEqual(
                    boundaries["ordinary_verification"]["seconds"],
                    wanted["verification_command_seconds"])
                self.assertEqual(composed.observe(stages[job_id])["exchange"],
                                 expected[job_id])
                # THE DELIVERY ON DISK IS UNCHANGED, path and bytes.
                self.assertEqual(self._launch_bytes(stages[job_id]),
                                 delivered[job_id])
        # AND NO SECOND CONTAINER FOR EITHER ATTEMPT, counted on the ONE engine
        # that has held them throughout.
        for job_id, one in stages.items():
            with self.subTest(job=job_id):
                self.assertEqual(len(self.starts_naming(one["attempt_id"])),
                                 before[job_id])
        self._continues(job, control, composed, stages, roots, captured)

    # THE TWO JOBS' OWN PRODUCER OUTPUT. Job B's task names `feature_check.py`
    # and asserts `feature.py`'s value, so its turn writes both; Job A's task is
    # the base fixture's harness. Using one Job's output for the other would be
    # a turn that could not pass its own configured verification.
    def _edits(self, job_id):
        if job_id == "job-b":
            return {"feature.py": self.case.B_FEATURE,
                    "feature_check.py": self.case.B_CHECK}
        return {"harness.py": "print('the reopened producer answered')\n"}

    def _continues(self, job, control, composed, stages, roots, captured):
        """THE REOPENED DEPLOYMENT FINISHES THE WORK IT INHERITED.

        Adoption and an unchanged start count say a reopen broke nothing; they
        do not say it can still DRIVE. Both original attempts take their real
        worker turns here -- through the containers the FIRST composition
        mounted -- and each one's provider is invoked exactly once, under its
        own Job's number.

        THE MOUNTS ARE THE ORIGINAL ONES, SAVED BEFORE THE CLOSE. The reopened
        composition has no `_prepared` map for attempts it did not prepare, so
        a fixture asking it for them would be asking about work it never did.
        """
        from unittest.mock import patch
        from baton_v12.job_manager import sweep
        from tests.job_manager import fixtures
        import claude_agent

        # THE JOB CONTEXT THE TURN ADOPTS AGAINST IS THE ONE THE DEPLOYMENT
        # ITSELF COMPOSED. The fixture's own resolver finds it through the
        # worker that PREPARED the attempt, and the reopened composition
        # prepared neither -- so what is supplied here is the context captured
        # from the REAL adoption above, not one this fixture invented.
        contexts = {one["attempt_id"]: one for one in captured.values()}

        def resolved(role, attempt_id):
            del role
            return contexts[attempt_id]

        seen = []
        original = claude_agent.ClaudeAgent._provider

        def watching(agent, task, candidate, scratch, environment,
                     prompt=None):
            # THE WHOLE TUPLE, not just the number. Review
            # 2026-09-13T05:25:38Z: a sorted list of bounds cannot detect a
            # SWAPPED association -- A running under B's ceiling and B under
            # A's would sort identically. What is recorded is which Job and
            # which attempt the turn was for, beside the bound it got, read
            # from the delivery the turn is actually holding.
            context = (agent._seen or {}).get("job_execution") or {}
            seen.append((context.get("job_id"), context.get("attempt_id"),
                         agent._bound(agent._seen, "provider_turn",
                                      claude_agent.PROVIDER_SECONDS)))
            return original(agent, task, candidate, scratch, environment,
                            prompt=prompt)

        watch = patch.object(claude_agent.ClaudeAgent, "_provider", watching)
        watch.start()
        self.addCleanup(watch.stop)
        with patch.object(type(self.case), "job_execution_for",
                          side_effect=resolved):
            for job_id, one in stages.items():
                self.assertEqual(
                    self.case.turn(control, "implementation",
                                   one["attempt_id"], roots[job_id],
                                   edits=self._edits(job_id)), 0,
                    job_id)
        # ONE PROVIDER TURN PER ATTEMPT, EACH UNDER ITS OWN JOB'S NUMBER, and
        # bound to the attempt it was for.
        wanted = {(job_id, one["attempt_id"],
                   (self.A if job_id == "job-a" else self.B)
                   ["provider_turn_seconds"])
                  for job_id, one in stages.items()}
        self.assertEqual(set(seen), wanted)
        self.assertEqual(len(seen), len(wanted))
        # AND THE SWEEPS TAKE NO FURTHER TURN, which is why the watch stays on
        # across them rather than stopping at the two calls above.
        for _ in range(6):
            sweep(job, composed, now=fixtures.NOW)
        self.assertEqual(set(seen), wanted)
        self.assertEqual(len(seen), len(wanted))
        for job_id in stages:
            self.assertEqual(
                self.case.states_for(job, composed, job_id)["implementation"],
                "completed", job_id)
        # AND STILL ONE WORKLOAD CONTAINER EACH: the turns ran in the containers
        # the first composition started, and the replay sweeps started none.
        for job_id, one in stages.items():
            with self.subTest(job=job_id):
                self.assertEqual(len(self.starts_naming(one["attempt_id"])), 1)

    def _launch_bytes(self, stage):
        """This attempt's delivery as it is ON DISK: its path and its bytes."""
        home = os.path.realpath(self.case.config["launch_home"])
        place = os.path.join(home, stage["attempt_id"], "launch.json")
        with open(place, "rb") as handle:
            return place, handle.read()

    def _adoptions(self, composed, stages):
        """What `adopt` was handed for each attempt after the reopen."""
        from unittest.mock import patch
        from baton_v12.worker_manager import launch as launch_owner

        captured = {}
        adopting = launch_owner.adopt

        def watched(*arguments, **named):
            answered = adopting(*arguments, **named)
            if answered is not None and named.get("job_execution"):
                context = answered.document["job_execution"]
                self.assertEqual(context, named["job_execution"])
                captured[context["job_id"]] = context
            return answered

        with patch.object(launch_owner, "adopt", side_effect=watched):
            for job_id in ("job-a", "job-b", "job-a"):
                composed.observe(stages[job_id])
        self.assertEqual(sorted(captured), ["job-a", "job-b"])
        return captured


class TwoJobsCeilingsDoNotLeakIntoEachOther(unittest.TestCase):
    """A/B SELECTION AT THE ADAPTER, and what these FOUR cases do and do not
    establish.

    `_seen` is what a turn's ceilings come from, and `invoke_provider` holds the
    delivery for its own turn only. These cases run turns in one process under
    alternating synthetic deliveries and assert each turn is bound by its own
    number.

    THEY ARE A HELPER-LEVEL PROOF. Review 2026-09-13T04:18:41Z: a NEW ADAPTER is
    constructed for each turn -- `_scratch` creates its private child root
    exclusively, so one home cannot serve two turns -- and `_provider` is
    replaced to read the bound. So what is established is that the delivery
    selects the number and that nothing leaks between turns in this process. It
    is NOT cross-Job propagation through a composed serving and observation,
    which is named as still owed in PROGRESS and remains so.
    """

    def setUp(self):
        self.agent = claude_agent.ClaudeAgent
        self.seen = []
        # THE CREDENTIAL BOUNDARY IS REAL AND THIS SUPPLIES IT SYNTHETICALLY.
        # `invoke_provider` composes the child environment before it runs
        # anything, and this adapter has no ambient fallback by design. The
        # bytes are never read by these cases and no live bearer exists.
        root = tempfile.mkdtemp(prefix="v12-w156162-credential-")
        self.addCleanup(shutil.rmtree, root, True)
        with open(os.path.join(root, "claude"), "w", encoding="utf-8") as one:
            one.write("not-a-credential\n")
        original = claude_agent.CREDENTIAL_ROOT
        claude_agent.CREDENTIAL_ROOT = root
        self.addCleanup(setattr, claude_agent, "CREDENTIAL_ROOT", original)

    def delivery(self, job_id, **requested):
        held = limits.resolved(requested, limits.CURRENT_GENERATION)
        return launch.launch_document(
            session="session-" + job_id, contract="a contract",
            role="implementation", transport=None,
            job_execution={
                "job_id": job_id, "attempt_id": "attempt-" + job_id,
                "job_input_digest": "sha256:" + "1" * 64,
                "job_policy_digest": "sha256:" + "2" * 64,
                "runtime_input_digest": "sha256:" + "3" * 64,
                "runtime_policy_digest": "sha256:" + "2" * 64,
                "execution_limits": held,
                "execution_limits_digest": launch._digest(held)})

    def interleave(self, *deliveries):
        """One adapter, many turns, each under its own delivery."""
        captured = []
        original = self.agent._provider

        def watching(agent, task, candidate, scratch, environment,
                     prompt=None):
            captured.append(agent._bound(agent._seen, "provider_turn",
                                         claude_agent.PROVIDER_SECONDS))
            return {"ok": True, "status": 0}

        self.agent._provider = watching
        self.addCleanup(setattr, self.agent, "_provider", original)
        # ONE ADAPTER PER TURN, which is the adapter's own contract rather than
        # a convenience: `_scratch` creates its private child root EXCLUSIVELY
        # and never repairs one, so a second turn on one home refuses. The
        # interleaving under test is therefore between turns that share this
        # process and this class -- `_seen` is where a leak would live -- and
        # not between two turns of one container.
        room = os.path.realpath(tempfile.mkdtemp(prefix="v12-w156162-ab-"))
        self.addCleanup(shutil.rmtree, room, True)
        held = None
        for index, one in enumerate(deliveries):
            home = os.path.join(room, f"turn-{index}")
            os.makedirs(home)
            held = self.agent(run=lambda argv, **options: None, home=home)
            held.invoke_provider(prompt="a prompt", room=room, seen=one)
        return captured, held

    def test_each_turn_is_bound_by_its_own_delivery(self):
        captured, _held = self.interleave(
            self.delivery("job-a", provider_turn_seconds=60),
            self.delivery("job-b", provider_turn_seconds=1200),
            self.delivery("job-a", provider_turn_seconds=60))
        self.assertEqual(captured, [60, 1200, 60])

    def test_a_turn_with_no_delivery_between_two_bound_ones(self):
        """The legacy delivery keeps the image default and does not inherit the
        previous Job's number -- and the Job after it is not affected either."""
        captured, _held = self.interleave(
            self.delivery("job-a", provider_turn_seconds=60),
            None,
            self.delivery("job-b", provider_turn_seconds=1200))
        self.assertEqual(captured,
                         [60, claude_agent.PROVIDER_SECONDS, 1200])

    def test_the_adapter_holds_nothing_after_the_last_turn(self):
        """And it keeps nothing afterwards: a turn's delivery is restored, so a
        later `work()` on the same object reads its own launch."""
        _captured, held = self.interleave(
            self.delivery("job-a", provider_turn_seconds=60))
        self.assertIsNone(held._seen)

    def test_a_delivery_that_is_not_a_document_is_refused(self):
        room = os.path.realpath(tempfile.mkdtemp(prefix="v12-w156162-ab-"))
        self.addCleanup(shutil.rmtree, room, True)
        held = self.agent(run=lambda argv, **options: None, home=room)
        with self.assertRaises(Exception) as caught:
            held.invoke_provider(prompt="a prompt", room=room,
                                 seen="not a document")
        self.assertIn("the document its caller proved",
                      str(caught.exception))


class AFailureAnswerIsBoundToTheResultItIsAbout(unittest.TestCase):
    """SINGLE-MEMBER NEGATIVES for the closed failure answer.

    Review 2026-09-13T09:34:47Z [P1]: the first form of `_failure` DISCARDED
    the result it was given, so a composed probe durably accepted a foreign
    causal commit, tree, command, task, digest, environment and 999999 seconds
    into blocked custody. A failure this owner keeps is evidence about THIS
    result or it is not evidence.

    EACH CASE CHANGES EXACTLY ONE MEMBER of an answer the owner accepts, so
    every refusal below names the member it is about and nothing else can be
    what refused it.
    """

    def setUp(self):
        from baton_v12.integration import reconciliation

        self.owner = reconciliation

    # FULL LOWERCASE OBJECT NAMES, which is what the owner requires: these are
    # hex characters, and a letter outside that set is refused by a different
    # check for a different reason.
    HELD = {"prepared": {"head": "c" * 40, "tree": "d" * 40},
            "source_base": "b" * 40, "source_candidate": "e" * 40}

    def answer(self, **changed):
        held = self.owner.failed_observation(
            phase="combined", reason="timeout",
            detail="the required test did not finish", seconds=77,
            command=["python3", "harness.py"],
            test_identity="task-1", test_digest="sha256:" + "9" * 64,
            environment=self.owner.EXECUTION_ENVIRONMENT,
            execution="baton.observer", input_commit=self.HELD["prepared"]["head"],
            input_tree=self.HELD["prepared"]["tree"], completed={},
            not_run=["base", "isolated"])
        held.update(changed)
        return held

    def accepted(self, **changed):
        return self.owner._failure(
            self.answer(**changed), dict(self.HELD), "baton.observer",
            phases=self.owner.CAUSAL_PHASES, what="the failure")

    def refused(self, **changed):
        with self.assertRaises(Exception) as caught:
            self.accepted(**changed)
        return str(caught.exception)

    def test_the_unaltered_answer_is_accepted(self):
        """Every negative below is only worth something if this passes."""
        self.assertEqual(self.accepted()["phase"], "combined")

    def test_a_foreign_commit_is_refused(self):
        self.assertIn("this result's combined content is",
                      self.refused(input_commit="f" * 40))

    def test_a_foreign_tree_is_refused(self):
        self.assertIn("this result prepared",
                      self.refused(input_tree="f" * 40))

    def test_a_foreign_environment_is_refused(self):
        self.assertIn("names environment",
                      self.refused(environment="somebody-elses-harness"))

    def test_a_foreign_execution_is_refused(self):
        self.assertIn("was produced by",
                      self.refused(execution="baton.somebody-else"))

    def test_a_phase_this_owner_does_not_run_is_refused(self):
        self.assertIn("this owner runs", self.refused(phase="post-import"))

    def test_a_reason_outside_the_closed_two_is_refused(self):
        self.assertIn("ran past its bound or never started",
                      self.refused(reason="crashed"))

    def test_a_bound_that_is_not_a_positive_whole_number(self):
        for seconds in (0, -1, True, "77", None):
            with self.subTest(seconds=seconds):
                self.assertIn("whole number of seconds",
                              self.refused(seconds=seconds))
        # A FLOAT IS REFUSED EARLIER, by the boundary that admits only exact
        # JSON data -- a different owner and a different sentence, and this
        # names that one rather than pretending one check catches both.
        self.assertIn("not JSON data", self.refused(seconds=1.5))

    def test_an_exit_status_is_never_carried(self):
        """The whole point of the branch: a child that supplied none does not
        get one, and a document that smuggles one in is not this shape."""
        self.assertIn("also carries", self.refused(status=0))

    def test_a_prefix_that_does_not_match_the_phase_is_refused(self):
        self.assertIn("completed prefix",
                      self.refused(completed={"base": {}}))

    def test_a_remainder_that_does_not_match_the_phase_is_refused(self):
        self.assertIn("did not run", self.refused(not_run=["isolated"]))

    def test_a_prefix_running_another_command_is_refused(self):
        """The base phase really has a prefix, so this is where a completed
        observation that ran something else can be caught."""
        completed = {"combined": {
            "command": ["python3", "somebody-elses.py"],
            "test_identity": "task-1", "input_commit": self.HELD["prepared"]["head"],
            "input_tree": self.HELD["prepared"]["tree"],
            "test_digest": "sha256:" + "9" * 64,
            "environment": self.owner.EXECUTION_ENVIRONMENT,
            "status": 0, "output": "the combined harness passed",
            "execution": "baton.observer", "harness_added": False}}
        self.assertIn(
            "one configured command is run against every state",
            self.refused(phase="base", input_commit=self.HELD["source_base"],
                         input_tree="a" * 40, completed=completed,
                         not_run=["isolated"]))

    def test_a_prefix_naming_another_task_is_refused(self):
        completed = {"combined": {
            "command": ["python3", "harness.py"],
            "test_identity": "some-other-task",
            "input_commit": self.HELD["prepared"]["head"],
            "input_tree": self.HELD["prepared"]["tree"],
            "test_digest": "sha256:" + "9" * 64,
            "environment": self.owner.EXECUTION_ENVIRONMENT,
            "status": 0, "output": "the combined harness passed",
            "execution": "baton.observer", "harness_added": False}}
        self.assertIn(
            "names task", self.refused(
                phase="base", input_commit=self.HELD["source_base"],
                input_tree="a" * 40, completed=completed,
                not_run=["isolated"]))

    CONFIGURED = {"command": ["python3", "harness.py"],
                  "test_identity": "task-1", "seconds": 77}

    def trusted(self, **changed):
        """Validate against what the DEPLOYMENT configured, not the answer."""
        return self.owner._failure(
            self.answer(**changed), dict(self.HELD), "baton.observer",
            phases=self.owner.CAUSAL_PHASES, what="the failure",
            expected=dict(self.CONFIGURED))

    def refused_against_configuration(self, **changed):
        with self.assertRaises(Exception) as caught:
            self.trusted(**changed)
        return str(caught.exception)

    def test_the_configured_answer_is_accepted(self):
        self.assertEqual(self.trusted()["seconds"], 77)

    def test_a_bound_this_deployment_did_not_apply_is_refused(self):
        """THE REVIEWER'S OWN PROBE, as a case. Changing ONLY the seconds --
        from the 77 this deployment applied to 999999 -- was accepted by both
        host custodies, because every check was about the answer's
        self-consistency. A positive-integer rule and a maximum cannot catch
        it; only the configured value can."""
        for seconds in (999999, 78, 1):
            with self.subTest(seconds=seconds):
                self.assertIn(
                    "this deployment configured",
                    self.refused_against_configuration(seconds=seconds))

    def test_a_command_this_deployment_did_not_configure_is_refused(self):
        self.assertIn("this deployment configured",
                      self.refused_against_configuration(
                          command=["python3", "somebody-elses.py"]))

    def test_a_task_this_deployment_did_not_configure_is_refused(self):
        self.assertIn("this deployment configured",
                      self.refused_against_configuration(
                          test_identity="some-other-task"))

    def test_a_completed_phase_may_not_carry_foreign_content(self):
        """[P1] prefix: a base failure accepted a foreign completed-combined
        commit, tree or environment INDEPENDENTLY of the failed phase's own
        bindings. Each completed phase is bound to this result's content."""
        def base_failure(**combined):
            one = {"command": ["python3", "harness.py"],
                   "test_identity": "task-1",
                   "input_commit": self.HELD["prepared"]["head"],
                   "input_tree": self.HELD["prepared"]["tree"],
                   "test_digest": "sha256:" + "9" * 64,
                   "environment": self.owner.EXECUTION_ENVIRONMENT,
                   "status": 0, "output": "the combined harness passed",
                   "execution": "baton.observer", "harness_added": False}
            one.update(combined)
            return self.refused_against_configuration(
                phase="base", input_commit=self.HELD["source_base"],
                input_tree="a" * 40, completed={"combined": one},
                not_run=["isolated"])

        self.assertIn("this result's combined content is",
                      base_failure(input_commit="f" * 40))
        self.assertIn("this result prepared",
                      base_failure(input_tree="f" * 40))
        self.assertIn("names environment",
                      base_failure(environment="somebody-elses-harness"))

    def test_a_disposal_that_fails_is_named_and_not_raised(self):
        """CLEANUP FAILURE. `rmtree(ignore_errors=True)` would report a clean
        disposal for a tree that is still there. What remains is named in the
        retained diagnostic instead -- and it is NOT raised, because the FAILURE
        is the fact being reported and losing it to a cleanup problem would be
        worse."""
        import os as _os
        import shutil
        import subprocess
        import tempfile

        from tools import stage_execution

        root = tempfile.mkdtemp(prefix="v12-w156162-dispose-")
        self.addCleanup(shutil.rmtree, root, True)
        held = stage_execution._ConfiguredExecution(
            "baton.observer", ["python3", "harness.py"],
            lambda argv: {"returncode": 0, "stderr": ""}, root, seconds=1)
        where = _os.path.join(root, "content")
        _os.makedirs(where)
        with open(_os.path.join(where, "harness.py"), "w") as handle:
            handle.write("pass\n")

        def archive(runner, repository, revision, into):
            shutil.copy(_os.path.join(where, "harness.py"), into)
            return into

        original = stage_execution._materialize
        stage_execution._materialize = archive
        self.addCleanup(setattr, stage_execution, "_materialize", original)
        ran = subprocess.run

        def run(argv, **options):
            raise subprocess.TimeoutExpired(argv, options.get("timeout"))

        subprocess.run = run
        self.addCleanup(setattr, subprocess, "run", ran)
        # A DISPOSAL THAT REMOVES NOTHING, injected at the normal boundary.
        removing = shutil.rmtree
        shutil.rmtree = lambda *arguments, **named: None
        self.addCleanup(setattr, shutil, "rmtree", removing)
        answered = held._run("/unused-repository", "HEAD")
        shutil.rmtree = removing
        self.assertIn("could not be disposed of and remains",
                      held._retention[
                          held._failure_key("HEAD", None)])
        # THE ANSWER IS STILL THE FAILURE, with its own reason intact.
        self.assertEqual(answered["reason"], "timeout")

    def test_a_harness_this_run_did_not_read_is_refused(self):
        """[P1], and the last of the trusted bindings. A probe changed ONLY
        `test_digest` after a real 77-second timeout, and the causal recording
        retained the foreign harness durably while the post-import adoption
        took it too.

        I had argued this owner could not publish a digest because it does not
        know one until it reads the content. That is true of a CONFIGURATION
        digest and it does not waive the per-result binding: the harness for
        this phase is in hand at the content-read boundary, and that is where
        it is pinned.
        """
        wanted = dict(self.CONFIGURED, test_digest="sha256:" + "9" * 64)
        self.assertEqual(
            self.owner._failure(self.answer(), dict(self.HELD),
                                "baton.observer",
                                phases=self.owner.CAUSAL_PHASES,
                                what="the failure",
                                expected=wanted)["test_digest"],
            "sha256:" + "9" * 64)
        with self.assertRaises(Exception) as caught:
            self.owner._failure(
                self.answer(test_digest="sha256:" + "4" * 64),
                dict(self.HELD), "baton.observer",
                phases=self.owner.CAUSAL_PHASES, what="the failure",
                expected=wanted)
        self.assertIn("this deployment configured", str(caught.exception))

    def test_the_owner_pins_the_harness_it_actually_read(self):
        """And the pinned value is the CONTENT's, not a configured constant:
        it appears only after a run has read a harness, and it is the digest of
        the bytes that run read."""
        import hashlib
        import os as _os
        import shutil
        import tempfile

        from tools import stage_execution

        root = tempfile.mkdtemp(prefix="v12-w156162-pin-")
        self.addCleanup(shutil.rmtree, root, True)
        held = stage_execution._ConfiguredExecution(
            "baton.observer", ["python3", "harness.py"],
            lambda argv: {"returncode": 0, "stderr": ""}, root, seconds=1)
        # NOTHING READ YET, so nothing is published.
        self.assertNotIn("test_digest", held.expectations)
        body = "print('the pinned harness')\n"
        where = _os.path.join(root, "content")
        _os.makedirs(where)
        with open(_os.path.join(where, "harness.py"), "w") as handle:
            handle.write(body)

        def archive(runner, repository, revision, into):
            shutil.copy(_os.path.join(where, "harness.py"), into)
            return into

        original = stage_execution._materialize
        stage_execution._materialize = archive
        self.addCleanup(setattr, stage_execution, "_materialize", original)
        import subprocess

        ran = subprocess.run

        def run(argv, **options):
            raise subprocess.TimeoutExpired(argv, options.get("timeout"))

        subprocess.run = run
        self.addCleanup(setattr, subprocess, "run", ran)
        answered = held._run("/unused-repository", "HEAD")
        wanted = "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest()
        self.assertEqual(held.expectations["test_digest"], wanted)
        self.assertEqual(answered["test_digest"], wanted)

    def test_the_configured_owner_publishes_what_it_was_given(self):
        """And the expectations really are the deployment's own operands, read
        off the owner object before anything ran."""
        from tools import stage_execution

        held = stage_execution._ConfiguredExecution(
            "baton.observer", ["python3", "harness.py"],
            lambda argv: {"returncode": 0, "stderr": ""}, "/unused",
            seconds=77)
        self.assertEqual(held.expectations["command"],
                         ["python3", "harness.py"])
        self.assertEqual(held.expectations["seconds"], 77)

    def test_the_post_import_adoption_binds_its_imported_content(self):
        """The same closed semantics at the other boundary, and the same
        refusal when the content is not the import's."""
        basis = {"input_commit": "d" * 40, "input_tree": "e" * 40}
        held = self.answer(phase="post-import", not_run=[],
                           input_commit=basis["input_commit"],
                           input_tree=basis["input_tree"])
        self.assertEqual(
            self.owner.adopt_failed_post_import(
                held, "baton.observer", basis)["phase"], "post-import")
        for member in ("input_commit", "input_tree"):
            with self.subTest(member=member):
                with self.assertRaises(Exception) as caught:
                    self.owner.adopt_failed_post_import(
                        dict(held, **{member: "f" * 40}), "baton.observer",
                        basis)
                self.assertIn("is not this import's", str(caught.exception))


class TheAdmittedFailureMatrix(unittest.TestCase):
    """THE MATRIX THE APPROVED PROPOSAL ADMITS, case by case.

    Owner ruling M157653 lists what acceptance of the host-failure branch
    requires. The corrections up to now fixed defects the reviewer found; this
    is the coverage the proposal itself asked for, and it is written here in one
    place so what is and is not covered can be read at a glance.
    """

    def setUp(self):
        from baton_v12.integration import reconciliation

        self.owner = reconciliation

    HELD = {"prepared": {"head": "c" * 40, "tree": "d" * 40},
            "source_base": "b" * 40, "source_candidate": "e" * 40}
    CONTENT = {"combined": ("c" * 40, "d" * 40),
               "base": ("b" * 40, "a" * 40),
               "isolated": ("e" * 40, "a" * 40)}
    CONFIGURED = {"command": ["python3", "harness.py"],
                  "test_identity": "task-1", "seconds": 77,
                  "test_digest": "sha256:" + "9" * 64}

    def observation(self, phase, **changed):
        commit, tree = self.CONTENT[phase]
        held = {"command": list(self.CONFIGURED["command"]),
                "test_identity": self.CONFIGURED["test_identity"],
                "input_commit": commit, "input_tree": tree,
                "test_digest": self.CONFIGURED["test_digest"],
                "environment": self.owner.EXECUTION_ENVIRONMENT,
                "status": 0, "output": "it ran",
                "execution": "baton.observer",
                "harness_added": phase == "base"}
        held.update(changed)
        return held

    def failure(self, phase, reason="timeout", **changed):
        order = list(self.owner.CAUSAL_PHASES)
        where = order.index(phase)
        commit, tree = self.CONTENT[phase]
        held = self.owner.failed_observation(
            phase=phase, reason=reason,
            detail="the required test supplied no exit status",
            seconds=self.CONFIGURED["seconds"],
            command=list(self.CONFIGURED["command"]),
            test_identity=self.CONFIGURED["test_identity"],
            test_digest=self.CONFIGURED["test_digest"],
            environment=self.owner.EXECUTION_ENVIRONMENT,
            execution="baton.observer", input_commit=commit, input_tree=tree,
            completed={one: self.observation(one) for one in order[:where]},
            not_run=list(order[where + 1:]))
        held.update(changed)
        return held

    def adopted(self, phase, reason="timeout", **changed):
        return self.owner._failure(
            self.failure(phase, reason, **changed), dict(self.HELD),
            "baton.observer", phases=self.owner.CAUSAL_PHASES,
            what="the failure", expected=dict(self.CONFIGURED))

    # -- every phase, and every reason ---------------------------------------

    def test_each_causal_phase_fails_for_each_closed_reason(self):
        """ALL-PHASE AND ALL-REASON. The owner runs three phases and a command
        can supply no status in two ways; all six combinations are admitted and
        each keeps its own phase, prefix and remainder."""
        order = list(self.owner.CAUSAL_PHASES)
        for phase in order:
            for reason in self.owner.FAILURE_REASONS:
                with self.subTest(phase=phase, reason=reason):
                    held = self.adopted(phase, reason)
                    where = order.index(phase)
                    self.assertEqual(held["phase"], phase)
                    self.assertEqual(held["reason"], reason)
                    self.assertEqual(sorted(held["completed"]),
                                     sorted(order[:where]))
                    self.assertEqual(sorted(held["not_run"]),
                                     sorted(order[where + 1:]))

    # -- malformed ------------------------------------------------------------

    def test_a_malformed_answer_is_refused_member_by_member(self):
        """MALFORMED. A member missing, an unknown member, and a member of the
        wrong type each refuse, and each refusal names what is wrong."""
        for change, expected in (
                ({"phase": None}, "names phase"),
                ({"reason": None}, "names reason"),
                ({"detail": None}, "detail"),
                ({"command": []}, "command words"),
                ({"command": "python3 harness.py"}, "command words"),
                ({"completed": []}, "phases that completed"),
                ({"not_run": {}}, "phases that did not run"),
                ({"execution": None}, "execution")):
            with self.subTest(change=sorted(change)):
                held = self.failure("combined")
                held.update(change)
                with self.assertRaises(Exception) as caught:
                    self.owner._failure(
                        held, dict(self.HELD), "baton.observer",
                        phases=self.owner.CAUSAL_PHASES, what="the failure",
                        expected=dict(self.CONFIGURED))
                self.assertIn(expected, str(caught.exception))

    def test_a_member_this_build_does_not_name_is_refused(self):
        self.assertIn("also carries",
                      self._refused("combined", remaining_seconds=10))

    def _refused(self, phase, **changed):
        with self.assertRaises(Exception) as caught:
            self.adopted(phase, **changed)
        return str(caught.exception)

    def test_a_missing_member_is_refused_as_missing(self):
        held = self.failure("combined")
        del held["seconds"]
        with self.assertRaises(Exception) as caught:
            self.owner._failure(held, dict(self.HELD), "baton.observer",
                                phases=self.owner.CAUSAL_PHASES,
                                what="the failure",
                                expected=dict(self.CONFIGURED))
        self.assertIn("seconds", str(caught.exception))

    # -- isolation ------------------------------------------------------------

    def test_one_phases_failure_never_stands_for_another(self):
        """PHASE ISOLATION. A `base` failure carrying `combined`'s content, or
        the reverse, is refused: the phase decides which content it is about."""
        self.assertIn("this result's base content is",
                      self._refused("base",
                                    input_commit=self.CONTENT["combined"][0]))
        self.assertIn("this result's combined content is",
                      self._refused("combined",
                                    input_commit=self.CONTENT["base"][0]))

    def test_a_post_import_answer_is_not_a_causal_one(self):
        """RESULT AND PHASE ISOLATION across the two host boundaries."""
        held = self.failure("combined")
        held["phase"] = "post-import"
        with self.assertRaises(Exception) as caught:
            self.owner._failure(held, dict(self.HELD), "baton.observer",
                                phases=self.owner.CAUSAL_PHASES,
                                what="the failure",
                                expected=dict(self.CONFIGURED))
        self.assertIn("this owner runs", str(caught.exception))
        held = self.failure("combined")
        held.update({"phase": "post-import", "not_run": [], "completed": {}})
        with self.assertRaises(Exception) as caught:
            self.owner.adopt_failed_post_import(
                held, "baton.observer",
                {"input_commit": "f" * 40, "input_tree": "f" * 40},
                expected=dict(self.CONFIGURED))
        self.assertIn("is not this import's", str(caught.exception))

    # -- the successful branch, unchanged ------------------------------------

    def test_the_integer_observations_are_untouched(self):
        """LEGACY SUCCESS. The three-observation shape is what it always was:
        the failure branch is a separate answer, and a document carrying the
        three integer observations is not read as one."""
        held = {one: self.observation(one)
                for one in self.owner.CAUSAL_PHASES}
        held["base"]["status"] = 1
        self.assertFalse(self.owner.is_failed_observation(held))
        taken = self.owner._causal(held, dict(self.HELD, **{
            "prepared": self.HELD["prepared"]}), "baton.observer")
        self.assertEqual(taken["combined"]["status"], 0)
        self.assertEqual(taken["base"]["status"], 1)
        self.assertTrue(taken["base"]["harness_added"])

    def test_a_retained_failure_reads_back_under_its_own_signature(self):
        """SIGNATURE AND READBACK. `_observation_signature` re-derives what the
        observation act was recorded under, from the row rather than from the
        state it has reached since -- and a retained FAILURE has no combined
        status to read. It derives from the row's own members instead, so a
        blocked failure replays rather than colliding."""
        row = {"result_id": "result-1", "content_digest": "sha256:" + "1" * 64,
               "state": "blocked", "reason": "it supplied no exit status",
               "causal_observations": self.failure("combined"),
               "observed_by": "baton.observer"}
        first = self.owner._observation_signature(dict(row))
        self.assertEqual(first, self.owner._observation_signature(dict(row)))
        # AND A DIFFERENT RETAINED FAILURE HAS A DIFFERENT SIGNATURE, so a
        # replay cannot be satisfied by some other failure of the same result.
        other = dict(row, causal_observations=self.failure("base"))
        self.assertNotEqual(first, self.owner._observation_signature(other))
        # THE SUCCESSFUL SHAPE STILL DERIVES AS IT ALWAYS DID.
        passing = dict(row, state="awaiting-evidence", reason=None,
                       causal_observations={
                           one: self.observation(one)
                           for one in self.owner.CAUSAL_PHASES})
        self.assertNotEqual(first,
                            self.owner._observation_signature(passing))

    def test_a_failure_answer_is_not_read_as_the_success_shape(self):
        self.assertTrue(
            self.owner.is_failed_observation(self.failure("combined")))
        with self.assertRaises(Exception):
            self.owner._causal(self.failure("combined"), dict(self.HELD),
                               "baton.observer")


class TheJobOwnerAnswersOneBoundaryWithoutADelivery(
        job_fixtures.JobManagerCase):
    """`boundary_seconds`, which is what the host-side owners ask.

    A caller with no container has no attempt id and no runtime digests, and
    `job_execution_context` would make it invent both. This asks the same owner
    the same question about one boundary and nothing else.
    """

    def setUp(self):
        from baton_v12.job_manager import submit

        super().setUp()
        self.held = self.store()
        held = json.loads(json.dumps(job_fixtures.submission()))
        held["schema"] = "baton.v12.job-submission/2"
        held["jobs"][0]["execution_limits"] = {
            "verification_command_seconds": 120}
        submit(self.held, held)

    def test_a_configured_job_answers_its_own_number(self):
        self.assertEqual(
            submission.boundary_seconds(self.held, "job-a",
                                        "host_verification"), 120)

    def test_an_unconfigured_job_answers_the_preserved_default(self):
        self.assertEqual(
            submission.boundary_seconds(self.held, "job-b",
                                        "host_verification"),
            limits.boundary_default("host_verification"))

    def test_a_job_this_store_never_admitted_is_refused(self):
        """[P2], review 2026-09-13T03:27:43Z. `execution_limits_of`'s
        missing-row answer is a COMPATIBILITY answer for a Job admitted before
        this table existed, and it could not tell that apart from a Job nobody
        submitted -- so a misspelled or foreign id came back with the preserved
        defaults and a host path ran under ceilings belonging to nothing."""
        with self.assertRaises(Exception) as caught:
            submission.boundary_seconds(self.held, "job-never-admitted",
                                        "host_verification")
        self.assertIn("no such Job", str(caught.exception))

    def test_a_migrated_job_with_no_limits_row_still_answers(self):
        """And the compatibility this must NOT break: a Job the store really
        holds, with no row in the table this Work added, resolves through
        generation 0 exactly as it did before."""
        from baton_v12.job_manager import schema

        self.held._connection.execute(
            "DELETE FROM job_execution_limits WHERE job_id = ?", ("job-a",))
        self.assertEqual(
            submission.boundary_seconds(self.held, "job-a",
                                        "host_verification"),
            limits.GENERATIONS[limits.LEGACY_GENERATION][
                "host_verification"])
        self.assertEqual(schema.SCHEMA_VERSION, 5)

    def test_a_boundary_this_build_does_not_own_is_refused(self):
        with self.assertRaises(Exception) as caught:
            submission.boundary_seconds(self.held, "job-a", "git_archive")
        self.assertIn("not an execution boundary", str(caught.exception))

    def test_every_owned_boundary_can_be_asked_for(self):
        """The refusal above is only safe if the owner's own boundary names all
        answer, so each one is asked rather than assumed."""
        for boundary in limits.BOUNDARIES:
            with self.subTest(boundary=boundary):
                self.assertIsInstance(
                    submission.boundary_seconds(self.held, "job-a", boundary),
                    int)


if __name__ == "__main__":                 # pragma: no cover
    unittest.main()
