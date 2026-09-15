"""W161230 slice1, condition 4: the portable task, its report and its result.

WHAT THESE CASES ARE ABOUT. Three answers that a careless build collapses into
one: a status this manager MEASURED, a report that was collected and carries NO
status, and NO REPORT AT ALL. Every collapse has the same shape -- absence read
as success -- and each is driven here on its own.

Nothing is stubbed, because there is nothing to stub: this leaf composes and
adopts documents and performs no act. What the cases supply is values.
"""
import json
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.integration import managed_execution as managed
from baton_v12.job_manager import execution_limits

AUTHORITY = "0" * 31 + "a"
WORK = "00000000-W7"
ORCHESTRATION = "integration-capacity-1"
TARGET = "target:main"
PREPARE = "prepare-attempt-1"
APPLY = "apply-attempt-1"
COMMANDS = ["fetch", "compose", "verify"]


def assignment(**changed):
    held = {"work_ref": {"authority_uuid": AUTHORITY, "work_id": WORK},
            "participant": "baton.impl-a", "generation": 1}
    held.update(changed)
    return held


def limits(requested=None, generation=execution_limits.CURRENT_GENERATION):
    """THE JOB OWNER'S OWN ANSWER, not a shape written here.

    Review 2026-09-13T18:21:26Z [P1]: the fixture invented `effective` and
    `generation`, the task required exactly those, and the GENUINE output of
    `execution_limits.resolved` -- units, scope, compatibility generation,
    requested settings and per-boundary seconds/origin/setting/default -- was
    refused by the very contract that claimed to carry a Job's limits. Every
    case below now starts from the real owner.
    """
    return execution_limits.resolved(requested, generation)


class TheTaskSaysWhatWasAskedFor(unittest.TestCase):

    def task(self, **changed):
        held = {"phase": "prepare", "orchestration_id": ORCHESTRATION,
                "canonical_target_id": TARGET,
                "execution_attempt_id": PREPARE,
                "assignment": assignment(),
                "task_digest": "sha256:" + "a" * 64,
                "input_digest": "sha256:" + "b" * 64,
                "harness_digest": "sha256:" + "h" * 64,
                "execution_limits": limits(), "commands": COMMANDS}
        held.update(changed)
        return managed.managed_task(**held)

    def test_a_task_binds_identity_content_and_the_jobs_own_limits(self):
        composed = self.task()
        self.assertEqual(sorted(composed), sorted(managed.TASK_MEMBERS))
        self.assertEqual(composed["schema"], managed.TASK_SCHEMA)
        self.assertEqual(composed["execution_attempt_id"], PREPARE)
        self.assertEqual(composed["assignment"], assignment())
        self.assertEqual(
            composed["execution_limits"]["compatibility_generation"],
            execution_limits.CURRENT_GENERATION)
        self.assertIsNone(composed["parent"])

    def test_a_task_names_no_host_path_and_no_location(self):
        """It says WHAT was asked for, never WHERE it runs. A task carrying a
        path or an argv would be this boundary deciding a deployment's
        layout, which is exactly what relocatable execution must not fix."""
        composed = self.task()
        for member in ("workspace", "argv", "host", "mounts", "image",
                       "locator", "path"):
            self.assertNotIn(member, composed)

    def test_an_apply_names_the_real_preparation_it_follows(self):
        composed = self.task(
            phase="apply", execution_attempt_id=APPLY,
            parent={"execution_attempt_id": PREPARE,
                    "collected_digest": "sha256:" + "c" * 64})
        self.assertEqual(composed["parent"]["execution_attempt_id"], PREPARE)

    def test_an_apply_that_imports_nothing_is_refused(self):
        with self.assertRaises(ContractRefusal) as caught:
            self.task(phase="apply", execution_attempt_id=APPLY)
        self.assertIn("an apply's parent", str(caught.exception))

    def test_an_apply_naming_only_an_attempt_is_refused(self):
        """Both members, because an attempt alone lets an apply follow a
        preparation that collected something else and a digest alone lets it
        follow no execution at all."""
        with self.assertRaises(ContractRefusal) as caught:
            self.task(phase="apply", execution_attempt_id=APPLY,
                      parent={"execution_attempt_id": PREPARE})
        self.assertIn("an apply's parent", str(caught.exception))

    def test_an_apply_cannot_be_its_own_parent(self):
        with self.assertRaises(ContractRefusal) as caught:
            self.task(phase="apply", execution_attempt_id=APPLY,
                      parent={"execution_attempt_id": APPLY,
                              "collected_digest": "sha256:" + "c" * 64})
        self.assertIn("names itself as its own parent", str(caught.exception))

    def test_a_preparation_with_a_parent_is_refused(self):
        with self.assertRaises(ContractRefusal) as caught:
            self.task(parent={"execution_attempt_id": "earlier-1",
                              "collected_digest": "sha256:" + "c" * 64})
        self.assertIn("content it could import does not exist",
                      str(caught.exception))

    def test_a_task_that_runs_nothing_is_not_a_task(self):
        with self.assertRaises(ContractRefusal) as caught:
            self.task(commands=[])
        self.assertIn("has nothing to report", str(caught.exception))

    def test_a_task_naming_one_command_twice_is_refused(self):
        with self.assertRaises(ContractRefusal) as caught:
            self.task(commands=["verify", "verify"])
        self.assertIn("more than once", str(caught.exception))

    def test_limits_are_the_jobs_own_document_not_two_numbers(self):
        with self.assertRaises(ContractRefusal) as caught:
            self.task(execution_limits={"effective": {}})
        self.assertIn("a task's execution limits", str(caught.exception))


class TheThreeAnswersAreNeverEachOther(unittest.TestCase):

    def setUp(self):
        self.task = managed.managed_task(
            phase="prepare", orchestration_id=ORCHESTRATION,
            canonical_target_id=TARGET, execution_attempt_id=PREPARE,
            assignment=assignment(), task_digest="sha256:" + "a" * 64,
            input_digest="sha256:" + "b" * 64,
            harness_digest="sha256:" + "h" * 64,
            execution_limits=limits(), commands=COMMANDS)

    def ran(self, *names, status=0):
        return [{"name": one, "status": status} for one in names]

    # -- measured -----------------------------------------------------------

    def test_a_measured_report_carries_the_status_that_was_measured(self):
        report = managed.collected_report(
            self.task, kind="measured", completed=self.ran(*COMMANDS),
            status=0)
        self.assertEqual(sorted(report), sorted(managed.REPORT_MEMBERS))
        self.assertEqual(report["status"], 0)
        self.assertIsNone(report["tag"])
        self.assertEqual(report["not_run"], [])

    def test_a_measured_nonzero_status_is_an_answer_like_any_other(self):
        report = managed.collected_report(
            self.task, kind="measured",
            completed=self.ran("fetch", "compose") + [{"name": "verify",
                                                       "status": 2}],
            not_run=[], status=2)
        self.assertEqual(report["status"], 2)

    def test_a_status_that_is_not_an_integer_is_refused(self):
        with self.assertRaises(ContractRefusal) as caught:
            managed.collected_report(self.task, kind="measured",
                                     completed=self.ran(*COMMANDS),
                                     status="0")
        self.assertIn("the integer status this manager measured",
                      str(caught.exception))

    def test_a_boolean_status_is_refused(self):
        """`True` is an `int` in this language, so an `isinstance` check would
        read a flag as exit code 1 -- a failure invented out of a boolean."""
        with self.assertRaises(ContractRefusal):
            managed.collected_report(self.task, kind="measured",
                                     completed=self.ran(*COMMANDS),
                                     status=True)

    def test_a_measured_report_that_ran_nothing_is_refused(self):
        with self.assertRaises(ContractRefusal) as caught:
            managed.collected_report(self.task, kind="measured",
                                     not_run=COMMANDS, status=0)
        self.assertIn("comes from a command that ran", str(caught.exception))

    # -- collected, with no status ------------------------------------------

    def test_a_collected_report_without_a_status_is_tagged(self):
        report = managed.collected_report(
            self.task, kind="collected-without-status",
            completed=self.ran("fetch"), not_run=["compose", "verify"],
            tag="the runtime was destroyed before the harness reported")
        self.assertIsNone(report["status"])
        self.assertIn("destroyed", report["tag"])
        self.assertEqual(report["not_run"], ["compose", "verify"])

    def test_a_missing_status_is_never_zero(self):
        """THE COLLAPSE THIS VOCABULARY EXISTS TO PREVENT. There is no way to
        spell "no status" as a status, because every number already means
        something -- and 0 means the thing that passed."""
        with self.assertRaises(ContractRefusal) as caught:
            managed.collected_report(
                self.task, kind="collected-without-status",
                completed=self.ran(*COMMANDS), status=0, tag="cut short")
        self.assertIn("if a status was measured", str(caught.exception))

    def test_a_tagless_no_status_report_is_refused(self):
        with self.assertRaises(ContractRefusal) as caught:
            managed.collected_report(
                self.task, kind="collected-without-status",
                completed=self.ran("fetch"), not_run=["compose", "verify"])
        self.assertIn("why no status was measured", str(caught.exception))

    # -- not collected ------------------------------------------------------

    def test_nothing_collected_describes_no_run_at_all(self):
        report = managed.collected_report(self.task, kind="not-collected",
                                          not_run=COMMANDS)
        self.assertIsNone(report["status"])
        self.assertIsNone(report["tag"])
        self.assertEqual(report["completed"], [])
        self.assertEqual(report["not_run"], COMMANDS)

    def test_a_report_that_does_not_exist_cannot_say_what_ran(self):
        with self.assertRaises(ContractRefusal) as caught:
            managed.collected_report(self.task, kind="not-collected",
                                     completed=self.ran("fetch"),
                                     not_run=["compose", "verify"])
        self.assertIn("cannot say what ran", str(caught.exception))

    def test_a_report_that_does_not_exist_carries_no_tag(self):
        with self.assertRaises(ContractRefusal) as caught:
            managed.collected_report(self.task, kind="not-collected",
                                     not_run=COMMANDS, tag="probably fine")
        self.assertIn("absence is its own answer", str(caught.exception))

    def test_an_unknown_kind_is_refused(self):
        with self.assertRaises(ContractRefusal) as caught:
            managed.collected_report(self.task, kind="probably-passed",
                                     not_run=COMMANDS)
        self.assertIn("a collected report is one of", str(caught.exception))

    # -- the prefix and the suffix ------------------------------------------

    def test_the_completed_prefix_and_not_run_suffix_are_the_sequence(self):
        with self.assertRaises(ContractRefusal) as caught:
            managed.collected_report(self.task, kind="measured",
                                     completed=self.ran("fetch"), status=0)
        self.assertIn("in its order", str(caught.exception))

    def test_a_reordered_report_describes_a_different_phase(self):
        with self.assertRaises(ContractRefusal) as caught:
            managed.collected_report(
                self.task, kind="measured",
                completed=self.ran("compose", "fetch", "verify"), status=0)
        self.assertIn("in its order", str(caught.exception))

    def test_a_command_the_task_never_declared_is_refused(self):
        with self.assertRaises(ContractRefusal) as caught:
            managed.collected_report(
                self.task, kind="measured",
                completed=self.ran("fetch", "compose", "publish"), status=0)
        self.assertIn("the task declares", str(caught.exception))


class TheResultIsAClaimAboutOnePhase(unittest.TestCase):

    def setUp(self):
        self.task = managed.managed_task(
            phase="prepare", orchestration_id=ORCHESTRATION,
            canonical_target_id=TARGET, execution_attempt_id=PREPARE,
            assignment=assignment(), task_digest="sha256:" + "a" * 64,
            input_digest="sha256:" + "b" * 64,
            harness_digest="sha256:" + "h" * 64,
            execution_limits=limits(), commands=COMMANDS)
        self.report = managed.collected_report(
            self.task, kind="measured",
            completed=[{"name": one, "status": 0} for one in COMMANDS],
            status=0)
        self.custody = {"result_id": "result-prepare-attempt-1",
                        "manifest_digest": "sha256:" + "c" * 64,
                        "disposition": "completed"}

    def test_a_result_carries_its_identity_report_and_content(self):
        composed = managed.managed_result(self.task, self.report,
                                          collected=self.custody)
        self.assertEqual(sorted(composed), sorted(managed.RESULT_MEMBERS))
        self.assertEqual(composed["orchestration_id"], ORCHESTRATION)
        self.assertEqual(composed["collected"], self.custody)
        self.assertEqual(composed["report"]["status"], 0)

    def test_a_measured_status_and_no_collected_content_is_legal(self):
        """They are separate facts: a phase can measure a status and collect
        nothing, and a document folding one into the other would make that
        indistinguishable from a phase that collected a failure."""
        composed = managed.managed_result(self.task, self.report)
        self.assertIsNone(composed["collected"])
        self.assertEqual(composed["report"]["status"], 0)

    def test_content_without_a_report_is_a_contradiction(self):
        absent = managed.collected_report(self.task, kind="not-collected",
                                          not_run=COMMANDS)
        with self.assertRaises(ContractRefusal) as caught:
            managed.managed_result(self.task, absent, collected=self.custody)
        self.assertIn("reports that nothing was collected",
                      str(caught.exception))

    def test_a_report_about_another_execution_is_refused(self):
        other = dict(self.report, execution_attempt_id=APPLY)
        with self.assertRaises(ContractRefusal) as caught:
            managed.managed_result(self.task, other)
        self.assertIn("reports the work it was asked to do",
                      str(caught.exception))

    def test_an_adopted_result_is_held_to_the_task_it_answers(self):
        composed = managed.managed_result(self.task, self.report,
                                          collected=self.custody)
        self.assertEqual(managed.adopt_managed_result(self.task, composed),
                         composed)

    def test_an_adopted_result_for_another_orchestration_is_denied(self):
        composed = managed.managed_result(self.task, self.report)
        foreign = dict(composed, orchestration_id="integration-capacity-2")
        with self.assertRaises(ContractRefusal) as caught:
            managed.adopt_managed_result(self.task, foreign)
        self.assertEqual(caught.exception.category, "policy")
        self.assertIn("answers the integration it was composed for",
                      str(caught.exception))

    def test_an_adopted_result_of_another_schema_is_refused(self):
        composed = managed.managed_result(self.task, self.report)
        with self.assertRaises(ContractRefusal) as caught:
            managed.adopt_managed_result(
                self.task, dict(composed, schema="baton.v12.something/1"))
        self.assertIn("a managed integration result is",
                      str(caught.exception))


class TheLimitsAreTheJobsOwnAnswer(unittest.TestCase):
    """[P1] Review 2026-09-13T18:21:26Z: a task invented a limits document.

    It required `effective`/`generation`, which no owner produces, and
    accepted an empty effective map under compatibility generation 999 --
    a generation this build cannot reproduce, so a resolution it cannot
    reproduce either. These cases drive the actual owner.
    """

    def task(self, **changed):
        held = {"phase": "prepare", "orchestration_id": ORCHESTRATION,
                "canonical_target_id": TARGET,
                "execution_attempt_id": PREPARE,
                "assignment": assignment(),
                "task_digest": "sha256:" + "a" * 64,
                "input_digest": "sha256:" + "b" * 64,
                "harness_digest": "sha256:" + "h" * 64,
                "execution_limits": limits(), "commands": COMMANDS}
        held.update(changed)
        return managed.managed_task(**held)

    def test_the_real_resolved_document_is_carried_whole(self):
        composed = self.task()
        held = composed["execution_limits"]
        self.assertEqual(sorted(held), sorted(managed.LIMITS_MEMBERS))
        self.assertEqual(held["units"], execution_limits.UNITS)
        self.assertEqual(held["scope"], execution_limits.SCOPE)
        self.assertEqual(sorted(held["boundaries"]),
                         sorted(execution_limits.BOUNDARIES))
        for name, boundary in held["boundaries"].items():
            with self.subTest(boundary=name):
                self.assertEqual(boundary["origin"],
                                 execution_limits.COMPATIBILITY)
                self.assertEqual(boundary["setting"],
                                 execution_limits.BOUNDARIES[name])

    def test_a_jobs_own_request_travels_beside_the_resolution(self):
        """What a Job ASKED FOR and what a boundary GETS are different facts;
        the owner refuses to conflate them and so does this."""
        asked = {"verification_command_seconds": 1200}
        composed = self.task(execution_limits=limits(asked))
        held = composed["execution_limits"]
        self.assertEqual(held["requested"], asked)
        ordinary = held["boundaries"]["ordinary_verification"]
        self.assertEqual(ordinary["seconds"], 1200)
        self.assertEqual(ordinary["origin"], execution_limits.JOB)
        self.assertEqual(held["boundaries"]["provider_turn"]["origin"],
                         execution_limits.COMPATIBILITY)

    def test_a_legacy_job_resolves_and_is_ordinary(self):
        """A Job admitted before per-Job limits existed runs under generation
        0, and its preserved defaults are exactly what it ran under. Refusing
        it would make a managed phase impossible for every older Job."""
        composed = self.task(execution_limits=limits(
            generation=execution_limits.LEGACY_GENERATION))
        self.assertEqual(
            composed["execution_limits"]["compatibility_generation"],
            execution_limits.LEGACY_GENERATION)

    def test_a_generation_this_build_cannot_reproduce_is_refused(self):
        """THE DEFECT ITSELF: 999 was accepted by a generic generation rule.
        The owner's own rule refuses it, because a resolution this build
        cannot reproduce is one it would have to guess at."""
        with self.assertRaises(ContractRefusal) as caught:
            self.task(execution_limits=dict(limits(),
                                            compatibility_generation=999))
        self.assertIn("compatibility generation", str(caught.exception))

    def test_an_empty_limits_document_is_refused(self):
        """The other half of the same defect: `{"effective": {}}` passed a
        bare dict check. There is no boundary map to be empty now -- the
        member set is the owner's."""
        with self.assertRaises(ContractRefusal) as caught:
            self.task(execution_limits={"effective": {}, "generation": 1})
        self.assertIn("a task's execution limits", str(caught.exception))

    def test_a_missing_boundary_is_refused(self):
        held = limits()
        held["boundaries"].pop("host_verification")
        with self.assertRaises(ContractRefusal) as caught:
            self.task(execution_limits=held)
        # The rebuild is what refuses it, and it names the boundary the Job's
        # own resolution has and this document does not.
        self.assertIn("the host_verification boundary", str(caught.exception))
        self.assertIn("this Job's own resolution has one",
                      str(caught.exception))

    def test_units_and_scope_are_the_owners_own(self):
        for member, wrong in (("units", "milliseconds"),
                              ("scope", "per-attempt")):
            with self.subTest(member=member):
                with self.assertRaises(ContractRefusal) as caught:
                    self.task(execution_limits=dict(limits(),
                                                    **{member: wrong}))
                self.assertIn("this Job's own resolution says",
                              str(caught.exception))

    def test_a_boundary_carrying_seconds_the_generation_does_not_pin(self):
        """[P1] Review 2026-09-13T18:34:36Z, and this is the case that was
        missing rather than the assertion.

        The first form checked units, scope, a known generation, seconds in the
        shared range, a matching setting and an agreeing origin -- and never
        asked the owner what the number IS. 7200 satisfied every one of those
        while generation 0 and generation 1 both pin `provider_turn` at 3600.
        A document can be internally consistent and still describe a resolution
        this build would never produce, so the check is now a comparison
        against the owner's own rebuild.
        """
        for generation in sorted(execution_limits.GENERATIONS):
            for mutated in ("seconds", "default_seconds", "both"):
                with self.subTest(generation=generation, member=mutated):
                    held = limits(generation=generation)
                    pinned = execution_limits.GENERATIONS[generation][
                        "provider_turn"]
                    self.assertNotEqual(pinned, 7200)
                    if mutated in ("seconds", "both"):
                        held["boundaries"]["provider_turn"]["seconds"] = 7200
                    if mutated in ("default_seconds", "both"):
                        held["boundaries"]["provider_turn"][
                            "default_seconds"] = 7200
                    with self.assertRaises(ContractRefusal) as caught:
                        self.task(execution_limits=held)
                    self.assertIn(f"the provider_turn boundary's {mutated}"
                                  if mutated != "both"
                                  else "the provider_turn boundary's seconds",
                                  str(caught.exception))
                    self.assertIn(str(pinned), str(caught.exception))

    def test_a_requested_setting_that_the_boundaries_do_not_reflect(self):
        """Tampering from the other side: the request says one thing and the
        resolved boundary another. The rebuild is computed FROM the request, so
        the two cannot be made to disagree."""
        held = limits({"verification_command_seconds": 1200})
        held["boundaries"]["ordinary_verification"]["seconds"] = 900
        with self.assertRaises(ContractRefusal) as caught:
            self.task(execution_limits=held)
        self.assertIn("the ordinary_verification boundary",
                      str(caught.exception))

    def test_a_boundary_claiming_the_job_chose_it_when_it_did_not(self):
        """`job` means the Job asked for this number. A boundary claiming it
        while the Job requested nothing reports a choice nobody made -- and the
        owner's resolution is what says which it was."""
        held = limits()
        held["boundaries"]["provider_turn"]["origin"] = execution_limits.JOB
        with self.assertRaises(ContractRefusal) as caught:
            self.task(execution_limits=held)
        self.assertIn("the provider_turn boundary", str(caught.exception))

    def test_a_boundary_hiding_a_request_the_job_did_make(self):
        held = limits({"verification_command_seconds": 1200})
        held["boundaries"]["ordinary_verification"]["origin"] = (
            execution_limits.COMPATIBILITY)
        with self.assertRaises(ContractRefusal) as caught:
            self.task(execution_limits=held)
        self.assertIn("the ordinary_verification boundary",
                      str(caught.exception))

    def test_a_boundary_naming_another_boundarys_setting(self):
        held = limits()
        held["boundaries"]["provider_turn"]["setting"] = (
            "verification_command_seconds")
        with self.assertRaises(ContractRefusal) as caught:
            self.task(execution_limits=held)
        self.assertIn("the provider_turn boundary", str(caught.exception))

    def test_a_request_the_owner_itself_refuses_is_refused_here(self):
        """The two INPUTS go through the owner's own rules before anything is
        rebuilt, so an unknown setting or out-of-range seconds is refused by
        the authority that owns what a Job may ask for."""
        for requested in ({"provider_turn_seconds": 0},
                          {"provider_turn_seconds": True},
                          {"unknown_seconds": 900}):
            with self.subTest(requested=sorted(requested)):
                held = limits()
                held["requested"] = requested
                with self.assertRaises(ContractRefusal):
                    self.task(execution_limits=held)


class AStoredResultIsHeldToTheSameRules(unittest.TestCase):
    """[P1] Review 2026-09-13T18:21:26Z: adoption bypassed report semantics.

    `managed_result` checked a received report's outer member set, its schema
    and its phase/attempt and carried it through, so every rule the report
    contract advertises applied to ONE CONSTRUCTOR and not to the boundary
    that reads stored and collected results. The reviewer's probe adopted an
    unknown kind, a boolean status, an undeclared command with a dropped
    suffix, and a `not-collected` report carrying status 0 and completed
    commands -- all unchanged.

    THESE CASES MUTATE A SERIALIZED RESULT rather than calling the composer
    with bad arguments, because that is the crossing the defect lived at: the
    document goes out through JSON and comes back as somebody else's bytes.
    """

    def setUp(self):
        self.task = managed.managed_task(
            phase="prepare", orchestration_id=ORCHESTRATION,
            canonical_target_id=TARGET, execution_attempt_id=PREPARE,
            assignment=assignment(), task_digest="sha256:" + "a" * 64,
            input_digest="sha256:" + "b" * 64,
            harness_digest="sha256:" + "h" * 64,
            execution_limits=limits(), commands=COMMANDS)
        self.result = managed.managed_result(
            self.task,
            managed.collected_report(
                self.task, kind="measured",
                completed=[{"name": one, "status": 0} for one in COMMANDS],
                status=0))

    def stored(self, **report):
        """The result as it comes back off a wire or out of a store."""
        held = json.loads(json.dumps(self.result))
        held["report"].update(report)
        return held

    def test_a_valid_stored_result_round_trips(self):
        self.assertEqual(
            managed.adopt_managed_result(self.task, self.stored()),
            self.result)

    def test_every_valid_answer_survives_the_round_trip(self):
        """The three answers are preserved, not merely refused in their
        malformed shapes -- a boundary that rejected everything would pass the
        cases below and be useless."""
        for kind, extra in (
                ("collected-without-status",
                 {"completed": [], "not_run": COMMANDS, "status": None,
                  "tag": "the runtime was destroyed before it reported"}),
                ("not-collected",
                 {"completed": [], "not_run": COMMANDS, "status": None,
                  "tag": None})):
            with self.subTest(kind=kind):
                report = managed.collected_report(
                    self.task, kind=kind, completed=extra["completed"],
                    not_run=extra["not_run"], status=extra["status"],
                    tag=extra["tag"])
                composed = managed.managed_result(self.task, report)
                self.assertEqual(
                    managed.adopt_managed_result(
                        self.task, json.loads(json.dumps(composed))),
                    composed)

    def test_an_unknown_kind_is_refused_on_adoption(self):
        with self.assertRaises(ContractRefusal) as caught:
            managed.adopt_managed_result(self.task,
                                         self.stored(kind="probably-passed"))
        self.assertIn("a collected report is one of", str(caught.exception))

    def test_a_boolean_status_is_refused_on_adoption(self):
        with self.assertRaises(ContractRefusal) as caught:
            managed.adopt_managed_result(self.task, self.stored(status=True))
        self.assertIn("the integer status this manager measured",
                      str(caught.exception))

    def test_an_undeclared_command_and_dropped_suffix_are_refused(self):
        with self.assertRaises(ContractRefusal) as caught:
            managed.adopt_managed_result(self.task, self.stored(
                completed=[{"name": "publish", "status": True}], not_run=[]))
        self.assertIn("the integer status this manager measured",
                      str(caught.exception))
        with self.assertRaises(ContractRefusal) as caught:
            managed.adopt_managed_result(self.task, self.stored(
                completed=[{"name": "fetch", "status": 0}], not_run=[]))
        self.assertIn("in its order", str(caught.exception))

    def test_not_collected_carrying_a_status_is_refused_on_adoption(self):
        """THE WORST OF THE FOUR: a report that says nothing was collected
        while carrying status 0 and a list of commands that ran. Adopted
        unchanged, that is 'we did not look, so it passed' written down."""
        with self.assertRaises(ContractRefusal) as caught:
            managed.adopt_managed_result(self.task, self.stored(
                kind="not-collected", status=0,
                completed=[{"name": one, "status": 0} for one in COMMANDS],
                not_run=[]))
        self.assertIn("absence is its own answer", str(caught.exception))

    def test_a_report_about_another_execution_is_refused_on_adoption(self):
        with self.assertRaises(ContractRefusal) as caught:
            managed.adopt_managed_result(
                self.task, self.stored(execution_attempt_id=APPLY))
        self.assertIn("reports the work it was asked to do",
                      str(caught.exception))

    def test_a_report_of_another_schema_is_refused_on_adoption(self):
        with self.assertRaises(ContractRefusal) as caught:
            managed.adopt_managed_result(
                self.task, self.stored(schema="baton.v12.something/1"))
        self.assertIn("a collected report is", str(caught.exception))

    def test_the_composer_and_the_adopter_are_one_owner(self):
        """The rules are not spelled twice. Whatever the composer refuses,
        the adoption boundary refuses with the SAME sentence -- which is what
        stops the two crossings from drifting apart again."""
        for changed, expected in (
                ({"kind": "probably-passed"}, "a collected report is one of"),
                ({"status": True}, "the integer status this manager measured"),
                ({"completed": [{"name": "fetch", "status": 0}],
                  "not_run": []}, "in its order")):
            with self.subTest(changed=sorted(changed)):
                with self.assertRaises(ContractRefusal) as adopting:
                    managed.adopt_managed_result(self.task,
                                                 self.stored(**changed))
                held = dict({"kind": "measured", "status": 0,
                             "completed": [{"name": one, "status": 0}
                                           for one in COMMANDS],
                             "not_run": [], "tag": None}, **changed)
                with self.assertRaises(ContractRefusal) as composing:
                    managed.collected_report(
                        self.task, kind=held["kind"],
                        completed=held["completed"], not_run=held["not_run"],
                        status=held["status"], tag=held["tag"])
                self.assertIn(expected, str(adopting.exception))
                self.assertEqual(str(adopting.exception),
                                 str(composing.exception))


class ThePreparationRequestComesBeforeAnythingExists(unittest.TestCase):
    """W161230 slice2: what a preparation is asked to produce.

    A SEPARATE ARTIFACT RATHER THAN A WIDER TASK. The accepted task describes
    ONE EXECUTION -- its attempt, its assignment, its limits -- and none of
    that exists when a preparation is requested: there is no claim, no offer
    and no runtime input manifest. Relaxing the task to carry a few extra
    members before those facts exist would make one document mean two things
    at two times, which is exactly what the slice text forbids.
    """

    def request(self, **changed):
        held = {"orchestration_id": ORCHESTRATION,
                "canonical_target_id": TARGET, "job_id": "job-a",
                "line_id": "line-b", "source_proposal_id": "proposal-1",
                "source": {"base": "a" * 40, "candidate": "c" * 40,
                           "target_revision": "d" * 40},
                "authority": {"path_set_digest": "sha256:" + "1" * 64,
                              "test_scope_digest": "sha256:" + "2" * 64},
                "harness_digest": "sha256:" + "h" * 64,
                "profile_digest": "sha256:" + "p" * 64,
                "input_digest": "sha256:" + "i" * 64,
                "execution_limits": limits(), "commands": COMMANDS}
        held.update(changed)
        return managed.preparation_request(**held)

    def test_a_request_binds_its_objects_and_its_accepted_evidence(self):
        held = self.request()
        self.assertEqual(sorted(held), sorted(managed.REQUEST_MEMBERS))
        self.assertEqual(held["schema"], managed.REQUEST_SCHEMA)
        self.assertEqual(sorted(held["source"]),
                         sorted(managed.SOURCE_MEMBERS))
        self.assertEqual(sorted(held["authority"]),
                         sorted(managed.AUTHORITY_MEMBERS))

    def test_a_request_contains_no_future_and_no_location(self):
        """No claim generation, no attempt, no manifest digest of itself --
        and no path, workspace or machine, because a request travels to a node
        that has none of those."""
        held = self.request()
        for absent in ("generation", "execution_attempt_id", "assignment",
                       "workspace", "path", "locator", "host", "repository",
                       "request_digest"):
            self.assertNotIn(absent, held)

    def test_its_digest_is_over_its_material_not_over_itself(self):
        first = managed.request_digest(self.request())
        self.assertEqual(first, managed.request_digest(self.request()))
        self.assertNotEqual(
            first,
            managed.request_digest(self.request(line_id="line-other")))

    def test_a_revision_expression_never_travels(self):
        """`HEAD~1` and a branch name both resolve to something different
        tomorrow; a preparation is about an immutable snapshot."""
        for member in managed.SOURCE_MEMBERS:
            for wrong in ("HEAD~1", "main", "a" * 39, "A" * 40):
                with self.subTest(member=member, value=wrong):
                    with self.assertRaises(ContractRefusal) as caught:
                        self.request(source=dict(
                            {"base": "a" * 40, "candidate": "c" * 40,
                             "target_revision": "d" * 40}, **{member: wrong}))
                    self.assertIn("one full lowercase object name",
                                  str(caught.exception))

    def test_the_jobs_own_limits_are_the_owners_here_too(self):
        with self.assertRaises(ContractRefusal):
            self.request(execution_limits={"effective": {}, "generation": 1})
        held = self.request(execution_limits=limits(
            {"verification_command_seconds": 1200}))
        self.assertEqual(
            held["execution_limits"]["boundaries"]["ordinary_verification"]
            ["seconds"], 1200)

    def test_a_request_that_runs_nothing_is_refused(self):
        with self.assertRaises(ContractRefusal):
            self.request(commands=[])

    def test_an_adopted_request_is_rebuilt_through_its_composer(self):
        held = self.request()
        self.assertEqual(managed.adopt_preparation_request(
            json.loads(json.dumps(held))), held)

    def test_an_adopted_request_of_another_schema_is_refused(self):
        with self.assertRaises(ContractRefusal) as caught:
            managed.adopt_preparation_request(
                dict(self.request(), schema="baton.v12.something/1"))
        self.assertIn("a preparation request is", str(caught.exception))

    def test_an_edited_request_does_not_survive_the_rebuild(self):
        held = dict(self.request())
        held["source"] = dict(held["source"], base="b" * 40)
        # The rebuild produces exactly this document, so the mutation has to
        # be one the composer would NOT produce to be caught -- an unknown
        # member is.
        with self.assertRaises(ContractRefusal):
            managed.adopt_preparation_request(dict(held, extra="member"))


if __name__ == "__main__":                                  # pragma: no cover
    unittest.main()
