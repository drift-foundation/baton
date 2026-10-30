"""W361910 — resolving the versioned implementation-to-independent-review
template, and proving the document it produces is the one the real consumer
takes.

WHY SO MANY CASES REACH `submit` AND `status` RATHER THAN COMPARING DICTS. The
FINDING's acceptance is explicit that "focused tests must exercise real
normalization and consumer boundaries, not only expected dictionaries", and the
reason is concrete: the whole claim of this module is that a resolved template
is SUBMITTABLE. A case that asserts the shape this module composed proves this
module agrees with itself. So the resolutions here go into a real Job store
through `submission.submit`, and the stages they produce are read back through
the real projection -- including the gate that has to hold the review blocked.

AND THE ONE DEFECT HAND-AUTHORING ACTUALLY HAS is driven directly:
`test_review_driver.one_work_submission` records that the package's own default
fixture names TWO Works across one Job's two stages, which parses and can never
attach. `TheResolvedStages` asserts the resolver cannot produce that document.
"""

import ast
import json
import pathlib
import unittest

from baton_v12.contracts import ContractRefusal, digest
from baton_v12.job_manager import (STAGE_KINDS, SUBMISSION_SCHEMA,
                                   TERMINAL_POLICIES, owned_submission,
                                   read_submission, stage_rows, status,
                                   stages_of, submission_signature, submit)
from baton_v12.job_manager import documents, execution_limits, scheduler
from baton_v12.job_manager import review_driver, templates
from baton_v12.job_manager.templates import (CANDIDATE_OUTPUT,
                                             CONFIGURATION_SCHEMA,
                                             DEFAULT_TEMPLATE,
                                             IMPLEMENTATION_REVIEW,
                                             REQUEST_SCHEMA,
                                             RESOLUTION_MEMBERS,
                                             RESOLUTION_SCHEMA, TEMPLATES,
                                             check_template,
                                             resolution_digest, resolve)

if __package__:
    from .fixtures import NOW, FakeOperations, JobManagerCase
else:
    from fixtures import NOW, FakeOperations, JobManagerCase

WORK = "0000000a-W1"
JOB = "w361910-a"
INPUT = "sha256:" + "1" * 64
POLICY = "sha256:" + "2" * 64
IMPLEMENTATION_PROFILE = "sha256:" + "a" * 64
REVIEW_PROFILE = "sha256:" + "b" * 64
STATEMENT = "Resolve the versioned implementation-review Job template."
CRITERION = "The normalized submission is accepted by its real consumer."
# TWO SCOPES THAT DELIBERATELY DO NOT OVERLAP. R3: the selected work scope is
# product source and the bounded test-change scope is a test path, so every
# case that reads one back can tell which one it got.
WORK_SCOPE = ("v12/python/src/baton_v12/job_manager/templates.py",)
TEST_SCOPE = ("v12/python/tests/job_manager/test_templates.py",)


def configuration(profiles=None, **named):
    """One deployment's half: which template, and which installed profiles.

    The profiles are the DEPLOYMENT's, which is why a case that changes one
    changes this document rather than the request -- `scheduler.reserve`
    matches a stage's profile against the installed pool, so a request that
    could state one would be configuring the pool from a Job.
    """
    held = {"schema": CONFIGURATION_SCHEMA,
            "profiles": {"implementation": {"profile_name": "reference",
                                            "profile_digest":
                                                IMPLEMENTATION_PROFILE},
                         "review": {"profile_name": "reviewer",
                                    "profile_digest": REVIEW_PROFILE}}
            if profiles is None else profiles}
    held.update(named)
    return held


def request(**named):
    held = {"schema": REQUEST_SCHEMA,
            "task": {"job_id": JOB, "work_id": WORK, "statement": STATEMENT},
            "source": {"input_digest": INPUT, "policy_digest": POLICY},
            "scope": {"work": list(WORK_SCOPE), "tests": list(TEST_SCOPE)},
            "acceptance": [CRITERION]}
    held.update(named)
    return held


class ResolverCase(unittest.TestCase):
    """The resolver alone: no store, no clock and nothing on disk."""

    def resolved(self, **named):
        return resolve(request(**named), configuration=configuration())

    def refused(self, caught):
        return caught.exception.message

    def stage(self, resolution, kind):
        for one in resolution["stages"]:
            if one["kind"] == kind:
                return one
        raise AssertionError(kind)


class TheSelection(ResolverCase):
    """An explicit version, a configured default, and nothing hidden."""

    def test_an_explicit_selection_is_recorded_as_the_requests_own(self):
        held = self.resolved(template=IMPLEMENTATION_REVIEW)
        self.assertEqual(held["template"]["version"], IMPLEMENTATION_REVIEW)
        self.assertEqual(held["template"]["origin"], "request")

    def test_an_omitted_selection_resolves_the_configured_default(self):
        """A DEFAULT SAVES TYPING AND HIDES NOTHING.

        SCH-1a: "A configured default may save typing but MUST NOT hide that
        selection." So the exact version is in the answer either way, and the
        ORIGIN is what distinguishes them -- a reader handed a version alone
        cannot tell whether this caller chose it or inherited it.
        """
        held = self.resolved()
        self.assertEqual(held["template"]["version"], IMPLEMENTATION_REVIEW)
        self.assertEqual(held["template"]["origin"], "configured-default")

    def test_a_deployment_may_configure_the_default_explicitly(self):
        held = resolve(request(), configuration=configuration(
            default_template=IMPLEMENTATION_REVIEW))
        self.assertEqual(held["template"]["version"], IMPLEMENTATION_REVIEW)
        self.assertEqual(held["template"]["origin"], "configured-default")

    def test_the_two_selections_of_one_version_resolve_identically(self):
        """WHICH IS WHAT MAKES A PINNED VERSION REPRODUCIBLE.

        The resolution records the exact version it selected, so the document
        can be re-derived by explicit selection whatever the configured
        default has become. The origin member is the one legitimate
        difference, and it is excluded here rather than ignored.
        """
        explicit = self.resolved(template=IMPLEMENTATION_REVIEW)
        defaulted = self.resolved()
        self.assertNotEqual(explicit["template"]["origin"],
                            defaulted["template"]["origin"])
        del explicit["template"]["origin"], defaulted["template"]["origin"]
        self.assertEqual(explicit, defaulted)
        self.assertEqual(digest(explicit), digest(defaulted))

    def test_an_unknown_explicit_version_refuses_and_names_what_exists(self):
        with self.assertRaises(ContractRefusal) as caught:
            self.resolved(template="baton.v12.job-template.whatever/9")
        self.assertIn("whatever/9", self.refused(caught))
        self.assertIn(IMPLEMENTATION_REVIEW, self.refused(caught))

    def test_a_version_that_is_not_text_refuses(self):
        with self.assertRaises(ContractRefusal):
            self.resolved(template=1)

    def test_a_deployment_whose_default_is_unknown_refuses_every_request(self):
        """AND IT REFUSES ONE THAT NAMED A VERSION, which is the point.

        A misconfigured default is the deployment's fault for every request,
        so proving it on a request that omitted the selection would leave the
        explicit case looking fine. The configuration is held to this build
        before the selection is read at all.
        """
        broken = configuration(default_template="baton.v12.job-template.x/1")
        for named in ({}, {"template": IMPLEMENTATION_REVIEW}):
            with self.assertRaises(ContractRefusal) as caught:
                resolve(request(**named), configuration=broken)
            self.assertIn("job-template.x/1", self.refused(caught))

    def test_the_request_schema_is_an_equality_test(self):
        with self.assertRaises(ContractRefusal) as caught:
            resolve(request(schema="baton.v12.job-template-request/9"),
                    configuration=configuration())
        self.assertIn(REQUEST_SCHEMA, self.refused(caught))

    def test_the_configuration_schema_is_an_equality_test(self):
        with self.assertRaises(ContractRefusal) as caught:
            resolve(request(), configuration=configuration(
                schema="baton.v12.job-template-configuration/9"))
        self.assertIn(CONFIGURATION_SCHEMA, self.refused(caught))


class TheResolvedStages(ResolverCase):
    """What selecting a template actually decides."""

    def test_both_stages_name_the_one_work_the_task_named(self):
        """THE DEFECT A GENERIC PARSER CANNOT REFUSE.

        `test_review_driver.one_work_submission`: the package's default
        fixture names two Works across one Job's implementation and review
        stages, "which the generic parser admits and the line provider can
        never attach, because a line is one `(authority_uuid, work_id)` pair
        and its reviewer is an assignment of that same Work". A request names
        ONE Work and there is no member that could introduce a second.
        """
        held = self.resolved()
        self.assertEqual({one["work_id"] for one in held["stages"]}, {WORK})
        self.assertEqual({one["work_id"]
                          for one in held["submission"]["jobs"][0]["stages"]},
                         {WORK})

    def test_the_stages_are_implementation_then_independent_review(self):
        held = self.resolved()
        self.assertEqual([one["role"] for one in held["stages"]],
                         ["implementation", "review"])
        self.assertEqual([one["kind"] for one in held["stages"]],
                         ["implementation", "review"])
        self.assertEqual([one["stage_id"] for one in held["stages"]],
                         [f"{JOB}/implementation", f"{JOB}/review"])

    def test_the_review_gates_on_the_implementation_of_its_own_job(self):
        held = self.resolved()
        self.assertEqual(self.stage(held, "implementation")["depends_on"], [])
        self.assertEqual(self.stage(held, "review")["depends_on"],
                         [{"job_id": JOB, "kind": "implementation"}])

    def test_each_stage_declares_what_it_consumes_and_produces(self):
        held = self.resolved()
        self.assertEqual(self.stage(held, "implementation")["consumes"], [])
        self.assertEqual(self.stage(held, "implementation")["produces"],
                         [CANDIDATE_OUTPUT])
        self.assertEqual(self.stage(held, "review")["consumes"],
                         [CANDIDATE_OUTPUT])
        self.assertEqual(self.stage(held, "review")["produces"],
                         [review_driver.FINDINGS_OUTPUT,
                          review_driver.LOGS_OUTPUT])

    def test_each_stage_requests_the_profile_its_deployment_installed(self):
        held = self.resolved()
        self.assertEqual(
            (self.stage(held, "implementation")["profile_name"],
             self.stage(held, "implementation")["profile_digest"]),
            ("reference", IMPLEMENTATION_PROFILE))
        self.assertEqual((self.stage(held, "review")["profile_name"],
                          self.stage(held, "review")["profile_digest"]),
                         ("reviewer", REVIEW_PROFILE))

    def test_a_deployment_that_installed_no_reviewer_refuses(self):
        """REFUSED HERE RATHER THAN AT RESERVATION.

        An invented profile digest is admitted by `documents` and only fails
        at `scheduler.reserve` as "no eligible review worker", long after the
        operator could tell why. So the absence is named at the one moment
        somebody is looking at this request.
        """
        with self.assertRaises(ContractRefusal) as caught:
            resolve(request(), configuration=configuration(profiles={
                "implementation": {"profile_name": "reference",
                                   "profile_digest": IMPLEMENTATION_PROFILE}}))
        self.assertIn("review", self.refused(caught))

    def test_a_profile_key_that_is_not_a_stage_kind_refuses(self):
        with self.assertRaises(ContractRefusal) as caught:
            resolve(request(), configuration=configuration(profiles={
                "implementor": {"profile_name": "reference",
                                "profile_digest": IMPLEMENTATION_PROFILE}}))
        self.assertIn("implementor", self.refused(caught))

    def test_a_configured_kind_this_template_does_not_carry_is_admitted(self):
        """A DEPLOYMENT CONFIGURES ITS POOL ONCE.

        `integration` is a real stage kind this template does not carry. A
        deployment that installed integration workers is configured, not
        wrong, and this resolution simply does not use that entry.
        """
        profiles = dict(configuration()["profiles"],
                        integration={"profile_name": "integrator",
                                     "profile_digest": "sha256:" + "c" * 64})
        held = resolve(request(), configuration=configuration(
            profiles=profiles))
        self.assertEqual([one["kind"] for one in held["stages"]],
                         ["implementation", "review"])


class TheAnswerIsSelfDescribing(ResolverCase):
    """What a reader of one resolution is owed."""

    def test_the_resolution_names_its_own_schema_and_closed_members(self):
        held = self.resolved()
        self.assertEqual(held["schema"], RESOLUTION_SCHEMA)
        self.assertEqual(sorted(held), sorted(RESOLUTION_MEMBERS))

    def test_the_request_four_are_preserved_exactly(self):
        """TASK, SOURCE, SCOPE AND ACCEPTANCE SURVIVE THE RESOLUTION.

        The submission has nowhere to carry a statement or a criterion, so
        the resolution is where what the Work was asked for and what it will
        be judged against stay legible. REV-2 gives an independent reviewer
        "a frozen candidate, selected requirement and test contract"; this is
        the selected requirement.
        """
        held = self.resolved()
        self.assertEqual(held["task"],
                         {"job_id": JOB, "work_id": WORK,
                          "submission_id": f"sub-{JOB}",
                          "statement": STATEMENT})
        self.assertEqual(held["source"], {"input_digest": INPUT,
                                          "policy_digest": POLICY})
        self.assertEqual(held["scope"], {"work": list(WORK_SCOPE),
                                         "tests": list(TEST_SCOPE)})
        self.assertEqual(held["acceptance"], [CRITERION])

    def test_an_explicit_submission_id_is_kept_and_an_absent_one_derived(self):
        self.assertEqual(self.resolved()["task"]["submission_id"],
                         f"sub-{JOB}")
        named = self.resolved(task={"job_id": JOB, "work_id": WORK,
                                    "statement": STATEMENT,
                                    "submission_id": "sub-chosen"})
        self.assertEqual(named["task"]["submission_id"], "sub-chosen")
        self.assertEqual(named["submission"]["submission_id"], "sub-chosen")

    def test_the_rules_report_the_vocabularies_their_owners_decide(self):
        """EACH MEMBER IS A WORD AN OWNING MODULE ALREADY DECIDED.

        A template that invented its own words for completion, correction and
        failure would be a second account of three lifecycles it does not own.
        These assertions hold the table to the owners rather than to literals.
        """
        rules = self.resolved()["rules"]
        self.assertEqual(rules["completion"]["outcome"],
                         review_driver.VERDICT_OUTCOMES[0])
        self.assertEqual(rules["completion"]["deciding_role"], "review")
        self.assertEqual(rules["completion"]["verdict_output"],
                         review_driver.FINDINGS_OUTPUT)
        self.assertEqual(rules["completion"]["delivers"], CANDIDATE_OUTPUT)
        self.assertEqual(rules["correction"]["outcome"],
                         review_driver.VERDICT_OUTCOMES[1])
        self.assertEqual(rules["correction"]["episode_ending"],
                         documents.CORRECTION_ENDINGS[0])
        self.assertEqual(rules["correction"]["repeats"],
                         ["implementation", "review"])
        self.assertEqual(rules["failure"]["outcome"],
                         review_driver.VERDICT_OUTCOMES[2])
        self.assertEqual(rules["failure"]["terminal_policy"],
                         TERMINAL_POLICIES[0])
        self.assertEqual(rules["failure"]["stage_state"], "exceptional")
        self.assertIn(rules["failure"]["stage_state"], documents.STAGE_STATES)
        self.assertEqual(rules["failure"]["recovery_operation"],
                         "fresh_attempt.admit")

    def test_the_resolution_carries_a_canonical_digest(self):
        """WHICH PROVES IT IS WITHIN THE FROZEN STRUCTURAL BOUNDS.

        `canonical_text` refuses a document nesting deeper than 8, and this
        answer carries a whole submission one level down -- whose own
        dependency entries are its deepest members. A digest that can be
        taken is the proof that a later admission can bind the exact
        resolution it consumed.
        """
        held = self.resolved()
        self.assertEqual(resolution_digest(held), digest(held))
        self.assertTrue(resolution_digest(held).startswith("sha256:"))
        self.assertNotEqual(resolution_digest(held),
                            submission_signature(held["submission"]))

    def test_the_answer_is_detached_from_the_frozen_table(self):
        """A CALLER CANNOT REACH THE TABLE THROUGH AN ANSWER.

        The answer's sequences are fresh lists, so appending to one does not
        grow the stage set every later Job resolves against. This was true of
        the first candidate too and was NOT the property that mattered — the
        other public door is `template_of`, driven in
        `TheRegisteredTemplateCannotBeWrittenTo` below.
        """
        held = self.resolved()
        held["template"]["permitted_overrides"].append("terminal_policy")
        held["stages"][1]["consumes"].append("whatever")
        again = self.resolved()
        self.assertEqual(again["template"]["permitted_overrides"],
                         ["execution_limits"])
        self.assertEqual(self.stage(again, "review")["consumes"],
                         [CANDIDATE_OUTPUT])
        self.assertEqual(TEMPLATES[IMPLEMENTATION_REVIEW]["roles"][1]
                         ["consumes"], (CANDIDATE_OUTPUT,))


class TheOverrides(ResolverCase):
    """The one permitted override, and everything that is not one."""

    def test_an_omitted_override_preserves_every_runner_default(self):
        held = self.resolved()
        self.assertEqual(held["overrides"], {})
        boundaries = held["execution_limits"]["boundaries"]
        self.assertEqual(boundaries["provider_turn"]["seconds"], 3600)
        self.assertEqual(boundaries["ordinary_verification"]["seconds"], 900)
        for one in boundaries.values():
            self.assertEqual(one["origin"], execution_limits.COMPATIBILITY)
        self.assertEqual(held["submission"]["jobs"][0].get("execution_limits"),
                         None)
        self.assertNotIn("execution_limits", held["submission"]["jobs"][0])

    def test_an_explicit_ceiling_moves_its_boundary_and_says_so(self):
        """AND THE ORIGIN IS WHERE THE OVERRIDE'S PROVENANCE LIVES.

        `execution_limits.resolved` already reports `job` or `compatibility`
        per boundary, so the resolution does not keep a second account of it.
        One explicit verification setting reaches all three verification
        boundaries, which is the owner's "Job-wide overrides initially".
        """
        held = self.resolved(overrides={"execution_limits": {
            "provider_turn_seconds": 5400,
            "verification_command_seconds": 1200}})
        self.assertEqual(held["overrides"], {"execution_limits": {
            "provider_turn_seconds": 5400,
            "verification_command_seconds": 1200}})
        boundaries = held["execution_limits"]["boundaries"]
        self.assertEqual(boundaries["provider_turn"]["seconds"], 5400)
        for name in ("ordinary_verification", "integration_verification",
                     "host_verification"):
            self.assertEqual(boundaries[name]["seconds"], 1200)
        for one in boundaries.values():
            self.assertEqual(one["origin"], execution_limits.JOB)

    def test_a_partial_override_leaves_the_other_boundary_alone(self):
        held = self.resolved(overrides={"execution_limits": {
            "provider_turn_seconds": 7200}})
        boundaries = held["execution_limits"]["boundaries"]
        self.assertEqual(boundaries["provider_turn"]["origin"],
                         execution_limits.JOB)
        self.assertEqual(boundaries["ordinary_verification"]["seconds"], 900)
        self.assertEqual(boundaries["ordinary_verification"]["origin"],
                         execution_limits.COMPATIBILITY)

    def test_the_answer_reports_which_generation_produced_these_numbers(self):
        """AND REPORTING IT IS ALL THIS MEMBER DOES.

        The earlier version of this case claimed "a later default change
        cannot move these numbers", which was wrong in the way review
        2026-10-26T17-46-15Z R1 measured: it cannot move the numbers in a
        SAVED DOCUMENT, and the Job the store admits moves anyway. What makes
        the pin load-bearing is `submission_for_admission`, driven in
        `TheConsumptionContract` below.
        """
        held = self.resolved()
        self.assertEqual(held["execution_limits"]["compatibility_generation"],
                         execution_limits.CURRENT_GENERATION)
        self.assertEqual(held["execution_limits"]["units"], "seconds")
        self.assertEqual(held["execution_limits"]["scope"], "per-invocation")

    def test_a_forbidden_override_refuses_rather_than_being_dropped(self):
        """DROPPING IT WOULD ANSWER A CHOICE THE CALLER DID NOT GET.

        The stage set, the dependency, the terminal policy and the output
        contracts are the template's. A request that could move them would be
        the operator-authored per-Job manifest SCH-1a forbids.
        """
        for forbidden in ({"terminal_policy": "report-and-hold"},
                          {"stages": []},
                          {"test_scope": ["v12"]},
                          {"template": IMPLEMENTATION_REVIEW}):
            with self.assertRaises(ContractRefusal) as caught:
                self.resolved(overrides=forbidden)
            self.assertIn(sorted(forbidden)[0], self.refused(caught))
            self.assertIn("execution_limits", self.refused(caught))

    def test_an_empty_override_object_resolves_the_preserved_defaults(self):
        held = self.resolved(overrides={})
        self.assertEqual(held["overrides"], {})
        self.assertEqual(held["submission"]["schema"],
                         documents.SUBMISSION_SCHEMAS[0])

    def test_a_present_null_override_is_not_an_omitted_one(self):
        """THE CORRECTION `documents._job` ALREADY CARRIES, one level up.

        The contract is omit the member or provide an object; admitting
        `execution_limits: null` would preserve that null as a selection.
        """
        with self.assertRaises(ContractRefusal) as caught:
            self.resolved(overrides={"execution_limits": None})
        self.assertIn("neither", self.refused(caught))

    def test_a_present_null_overrides_member_is_not_an_absent_one(self):
        """AN ABSENT MEMBER AND A PRESENT NULL ARE DIFFERENT INTENTS.

        The same distinction one level down, and the same reason: a request
        that wrote `overrides: null` stated something, and reading it as
        silence would answer a resolution it did not ask for.
        """
        with self.assertRaises(ContractRefusal) as caught:
            self.resolved(overrides=None)
        self.assertIn("overrides", self.refused(caught))

    def test_a_ceiling_outside_the_supported_range_refuses(self):
        for seconds in (0, -1, execution_limits.MAX_SECONDS + 1):
            with self.assertRaises(ContractRefusal) as caught:
                self.resolved(overrides={"execution_limits": {
                    "provider_turn_seconds": seconds}})
            self.assertIn(str(execution_limits.MAX_SECONDS),
                          self.refused(caught))

    def test_a_ceiling_that_is_not_a_whole_number_refuses(self):
        for value in (900.5, True, "900"):
            with self.assertRaises(ContractRefusal):
                self.resolved(overrides={"execution_limits": {
                    "verification_command_seconds": value}})

    def test_an_unknown_limit_setting_refuses_rather_than_being_ignored(self):
        with self.assertRaises(ContractRefusal) as caught:
            self.resolved(overrides={"execution_limits": {
                "total_seconds": 900}})
        self.assertIn("total_seconds", self.refused(caught))


class TheRequestIsOwned(ResolverCase):
    """Caller input, owned member by member, exactly as a submission is."""

    def test_a_missing_required_member_is_named(self):
        for member in ("task", "source", "scope", "acceptance"):
            held = request()
            del held[member]
            with self.assertRaises(ContractRefusal) as caught:
                resolve(held, configuration=configuration())
            self.assertIn(member, self.refused(caught))

    def test_an_unrecognised_request_member_refuses(self):
        with self.assertRaises(ContractRefusal) as caught:
            self.resolved(profiles={})
        self.assertIn("profiles", self.refused(caught))

    def test_a_missing_task_member_is_named(self):
        for member in ("job_id", "work_id", "statement"):
            task = {"job_id": JOB, "work_id": WORK, "statement": STATEMENT}
            del task[member]
            with self.assertRaises(ContractRefusal) as caught:
                self.resolved(task=task)
            self.assertIn(member, self.refused(caught))

    def test_a_missing_source_digest_is_named(self):
        for member in ("input_digest", "policy_digest"):
            source = {"input_digest": INPUT, "policy_digest": POLICY}
            del source[member]
            with self.assertRaises(ContractRefusal) as caught:
                self.resolved(source=source)
            self.assertIn(member, self.refused(caught))

    def test_a_scope_path_that_climbs_out_of_the_repository_refuses(self):
        """BOTH SCOPES ARE HELD TO `check_relative_path`.

        It is the rule `documents._paths` already reaches for, and proving it
        on one member would leave the other accepting `../outside.py`.
        """
        for path in ("../outside.py", "/absolute.py", "v12/../../up.py", ""):
            for member in ("work", "tests"):
                with self.assertRaises(ContractRefusal):
                    self.resolved(scope=dict(
                        {"work": list(WORK_SCOPE), "tests": list(TEST_SCOPE)},
                        **{member: [path]}))

    def test_either_scope_naming_one_place_twice_refuses(self):
        for member in ("work", "tests"):
            with self.assertRaises(ContractRefusal) as caught:
                self.resolved(scope=dict(
                    {"work": list(WORK_SCOPE), "tests": list(TEST_SCOPE)},
                    **{member: ["v12/python/tests", "v12/python/tests"]}))
            self.assertIn("more than once", self.refused(caught))

    def test_a_missing_scope_member_is_named(self):
        for member in ("work", "tests"):
            held = {"work": list(WORK_SCOPE), "tests": list(TEST_SCOPE)}
            del held[member]
            with self.assertRaises(ContractRefusal) as caught:
                self.resolved(scope=held)
            self.assertIn(member, self.refused(caught))

    def test_a_scope_that_is_not_two_lists_refuses(self):
        for value in ([], list(TEST_SCOPE), None, "v12",
                      {"work": list(WORK_SCOPE), "tests": list(TEST_SCOPE),
                       "docs": []}):
            with self.assertRaises(ContractRefusal):
                self.resolved(scope=value)

    def test_an_absent_acceptance_criterion_refuses(self):
        """A JOB WITH NOTHING TO BE JUDGED AGAINST CANNOT BE REVIEWED.

        Which is what this template's second stage is, so an empty list is
        refused rather than resolved into a review with no requirement.
        """
        for value in ([], "a criterion", None):
            with self.assertRaises(ContractRefusal) as caught:
                self.resolved(acceptance=value)
            self.assertIn("acceptance", self.refused(caught))

    def test_a_duplicated_acceptance_criterion_refuses(self):
        with self.assertRaises(ContractRefusal) as caught:
            self.resolved(acceptance=[CRITERION, CRITERION])
        self.assertIn("more than once", self.refused(caught))

    def test_the_prose_members_are_bounded(self):
        with self.assertRaises(ContractRefusal) as caught:
            self.resolved(task={"job_id": JOB, "work_id": WORK,
                                "statement":
                                    "x" * (templates.MAX_STATEMENT + 1)})
        self.assertIn(str(templates.MAX_STATEMENT), self.refused(caught))
        with self.assertRaises(ContractRefusal) as caught:
            self.resolved(acceptance=["x" * (templates.ACCEPTANCE_LIMIT + 1)])
        self.assertIn(str(templates.ACCEPTANCE_LIMIT), self.refused(caught))
        with self.assertRaises(ContractRefusal):
            self.resolved(acceptance=[CRITERION] * (
                templates.MAX_ACCEPTANCE + 1))

    def test_a_request_carrying_a_secret_is_refused_as_one(self):
        """THE SECRET CHECK RUNS BEFORE THE STRUCTURAL ONES.

        `check_no_durable_secret`'s own rule for wherever both apply: a
        document carrying a secret is refused AS that rather than as whatever
        structural fault is also in it, because the two answers send a caller
        to different places. Here both are present -- `password` is also an
        unrecognised member -- and the secret answer is the one returned.
        """
        with self.assertRaises(ContractRefusal) as caught:
            self.resolved(password="hunter2")
        self.assertEqual(caught.exception.code, "secret-leak")

    def test_a_request_that_is_not_a_document_refuses(self):
        for value in (None, [], "a request", 1):
            with self.assertRaises(ContractRefusal):
                resolve(value, configuration=configuration())

    def test_a_configuration_that_is_not_a_document_refuses(self):
        for value in ([], "a configuration", 1):
            with self.assertRaises(ContractRefusal):
                resolve(request(), configuration=value)

    def test_no_configuration_at_all_resolves_nothing_and_says_why(self):
        """AN ABSENT CONFIGURATION IS NOT AN EMPTY ONE WITH DEFAULTS.

        The template is this build's, so it resolves; the PROFILES are the
        deployment's, so with none configured the first role has nowhere to
        get one and the refusal names the stage rather than inventing a
        digest.
        """
        with self.assertRaises(ContractRefusal) as caught:
            resolve(request())
        self.assertIn("implementation", self.refused(caught))


class TheFrozenTable(unittest.TestCase):
    """The rule every registered template is held to, and its two faults."""

    def definition(self, **named):
        held = {"version": "baton.v12.job-template.probe/1",
                "terminal_policy": TERMINAL_POLICIES[0],
                "permitted_overrides": ("execution_limits",),
                "roles": ({"role": "implementation",
                           "kind": "implementation", "depends_on": (),
                           "consumes": (), "produces": ("proposal",)},
                          {"role": "review", "kind": "review",
                           "depends_on": ("implementation",),
                           "consumes": ("proposal",),
                           "produces": ("findings", "logs")}),
                "completion": {}, "correction": {}, "failure": {}}
        held.update(named)
        return held

    def refused(self, caught):
        return caught.exception.message

    def test_every_registered_template_satisfies_the_rule(self):
        """CHECKED AT IMPORT TOO, and asserted again here.

        The import-time loop is what makes a bad table entry fail where it is
        written; this case is what makes that loop's absence visible if
        somebody removes it.
        """
        self.assertEqual(sorted(TEMPLATES), [IMPLEMENTATION_REVIEW])
        for version, definition in TEMPLATES.items():
            self.assertEqual(version, definition["version"])
            check_template(definition)
        self.assertIn(DEFAULT_TEMPLATE, TEMPLATES)

    def test_a_probe_definition_is_accepted_so_the_faults_are_the_faults(self):
        check_template(self.definition())

    def test_a_role_gating_on_a_role_the_template_does_not_carry_refuses(self):
        """THE FIRST OF THE TWO MISMATCHES: a gate nothing can open.

        `documents._resolvable` refuses the same thing one level up, for a
        dependency outside the submission. Refusing it in the table means a
        template that could never produce an eligible stage fails where it is
        written.
        """
        roles = ({"role": "implementation", "kind": "implementation",
                  "depends_on": (), "consumes": (), "produces": ()},
                 {"role": "review", "kind": "review",
                  "depends_on": ("planning",), "consumes": (),
                  "produces": ()})
        with self.assertRaises(ContractRefusal) as caught:
            check_template(self.definition(roles=roles))
        self.assertIn("planning", self.refused(caught))
        self.assertIn("never eligible", self.refused(caught))

    def test_a_role_consuming_a_result_nobody_upstream_produces_refuses(self):
        """THE SECOND, AND THE WORSE ONE.

        The dependency graph is satisfiable and the stage still cannot do its
        work: an independent review that is eligible and has no candidate to
        read. A satisfiable graph does not say a stage can run.
        """
        roles = ({"role": "implementation", "kind": "implementation",
                  "depends_on": (), "consumes": (), "produces": ("logs",)},
                 {"role": "review", "kind": "review",
                  "depends_on": ("implementation",),
                  "consumes": ("proposal",), "produces": ()})
        with self.assertRaises(ContractRefusal) as caught:
            check_template(self.definition(roles=roles))
        self.assertIn("proposal", self.refused(caught))
        self.assertIn("no role it depends on produces", self.refused(caught))

    def test_a_role_consuming_from_a_role_it_does_not_depend_on_refuses(self):
        """A PRODUCER THAT EXISTS IS NOT A GATE.

        SCH-4: "Containment, filesystem ancestry or a role name cannot supply
        a dependency." A review that reads the implementation's candidate
        without gating on it would be eligible before the candidate existed.
        """
        roles = ({"role": "implementation", "kind": "implementation",
                  "depends_on": (), "consumes": (),
                  "produces": ("proposal",)},
                 {"role": "review", "kind": "review", "depends_on": (),
                  "consumes": ("proposal",), "produces": ()})
        with self.assertRaises(ContractRefusal) as caught:
            check_template(self.definition(roles=roles))
        self.assertIn("no role it depends on produces", self.refused(caught))

    def test_a_role_gating_on_itself_refuses(self):
        roles = ({"role": "implementation", "kind": "implementation",
                  "depends_on": ("implementation",), "consumes": (),
                  "produces": ()},)
        with self.assertRaises(ContractRefusal) as caught:
            check_template(self.definition(roles=roles))
        self.assertIn("gates on itself", self.refused(caught))

    def test_two_roles_of_one_stage_kind_refuse(self):
        """BECAUSE THAT IS WHAT A STAGE IDENTITY IS.

        `documents.stage_id` derives it from the Job and the kind, so two
        roles on one kind resolve to one stage this build cannot tell apart --
        and `documents._job` would refuse the submission rather than the
        template, which is the wrong place to discover it.
        """
        roles = ({"role": "first", "kind": "implementation",
                  "depends_on": (), "consumes": (), "produces": ()},
                 {"role": "second", "kind": "implementation",
                  "depends_on": (), "consumes": (), "produces": ()})
        with self.assertRaises(ContractRefusal) as caught:
            check_template(self.definition(roles=roles))
        self.assertIn("one stage identity", self.refused(caught))

    def test_a_repeated_role_name_refuses(self):
        roles = ({"role": "same", "kind": "implementation",
                  "depends_on": (), "consumes": (), "produces": ()},
                 {"role": "same", "kind": "review", "depends_on": (),
                  "consumes": (), "produces": ()})
        with self.assertRaises(ContractRefusal) as caught:
            check_template(self.definition(roles=roles))
        self.assertIn("twice", self.refused(caught))

    def test_a_stage_kind_outside_the_submission_vocabulary_refuses(self):
        roles = ({"role": "planning", "kind": "planning", "depends_on": (),
                  "consumes": (), "produces": ()},)
        with self.assertRaises(ContractRefusal) as caught:
            check_template(self.definition(roles=roles))
        self.assertIn("planning", self.refused(caught))
        for kind in STAGE_KINDS:
            self.assertIn(kind, self.refused(caught))

    def test_more_roles_than_a_job_has_stages_refuses(self):
        roles = tuple({"role": f"role-{n}", "kind": "implementation",
                       "depends_on": (), "consumes": (), "produces": ()}
                      for n in range(documents.MAX_STAGES + 1))
        with self.assertRaises(ContractRefusal) as caught:
            check_template(self.definition(roles=roles))
        self.assertIn(str(documents.MAX_STAGES), self.refused(caught))

    def test_a_template_with_no_role_refuses(self):
        with self.assertRaises(ContractRefusal) as caught:
            check_template(self.definition(roles=()))
        self.assertIn("no role", self.refused(caught))

    def test_a_terminal_policy_outside_the_vocabulary_refuses(self):
        with self.assertRaises(ContractRefusal) as caught:
            check_template(self.definition(terminal_policy="discard"))
        self.assertIn("discard", self.refused(caught))

    def test_permitting_an_override_nothing_applies_refuses(self):
        """AN OVERRIDE NOBODY RESOLVES IS A CHOICE A REQUEST WOULD BE TOLD IT
        MADE."""
        with self.assertRaises(ContractRefusal) as caught:
            check_template(self.definition(
                permitted_overrides=("execution_limits", "terminal_policy")))
        self.assertIn("terminal_policy", self.refused(caught))

    def test_a_missing_or_extra_declaration_member_refuses(self):
        held = self.definition()
        del held["failure"]
        with self.assertRaises(ContractRefusal) as caught:
            check_template(held)
        self.assertIn("failure", self.refused(caught))
        with self.assertRaises(ContractRefusal) as caught:
            check_template(self.definition(retries=3))
        self.assertIn("retries", self.refused(caught))

    def test_a_declaration_that_is_not_a_sequence_refuses(self):
        for named in ({"roles": {"implementation": {}}},
                      {"permitted_overrides": "execution_limits"}):
            with self.assertRaises(ContractRefusal):
                check_template(self.definition(**named))

    def test_a_role_declaration_missing_a_member_refuses(self):
        roles = ({"role": "implementation", "kind": "implementation",
                  "depends_on": (), "consumes": ()},)
        with self.assertRaises(ContractRefusal) as caught:
            check_template(self.definition(roles=roles))
        self.assertIn("produces", self.refused(caught))


class TheConsumerBoundary(JobManagerCase):
    """The resolved document, taken by the owner that really takes it."""

    def setUp(self):
        super().setUp()
        self.jobs = self.store()
        self.acts = FakeOperations()

    def resolved(self, **named):
        return resolve(request(**named), configuration=configuration())

    def test_the_submission_is_already_normalized_by_its_real_owner(self):
        """`resolve` RUNS IT THROUGH `owned_submission` BEFORE ANSWERING.

        Which is what makes "this resolution is submittable" a fact rather
        than an intention: re-owning the answer is a fixed point, so there is
        no member order, no spelling and no bound left for a later consumer to
        disagree with.
        """
        held = self.resolved()["submission"]
        self.assertEqual(owned_submission(held), held)
        self.assertEqual(list(held), ["schema", "submission_id", "jobs"])
        self.assertEqual(list(held["jobs"][0]), list(documents.JOB_MEMBERS))

    def test_the_submission_survives_a_round_trip_through_text(self):
        """BECAUSE THAT IS HOW THE CLI ACTUALLY DELIVERS ONE.

        `tools/job_manager._submit` reads a file or stdin and calls
        `read_submission`, which decodes and owns. A resolution whose document
        only worked in memory would be one nobody could submit.
        """
        import json

        held = self.resolved()["submission"]
        self.assertEqual(read_submission(json.dumps(held)), held)

    def test_the_resolution_records_into_a_real_job_store(self):
        held = self.resolved()
        recorded = submit(self.jobs, held["submission"])
        self.assertEqual(recorded["jobs"], [JOB])
        self.assertEqual(recorded["stages"],
                         [f"{JOB}/implementation", f"{JOB}/review"])
        self.assertEqual(recorded["recorded_at"], NOW)
        self.assertEqual([row["stage_id"] for row in stage_rows(self.jobs)],
                         [f"{JOB}/implementation", f"{JOB}/review"])

    def test_the_recorded_stages_carry_the_resolved_intent(self):
        import json

        submit(self.jobs, self.resolved()["submission"])
        rows = {one["kind"]: one for one in stages_of(self.jobs, JOB)}
        self.assertEqual(rows["implementation"]["work_id"], WORK)
        self.assertEqual(rows["review"]["work_id"], WORK)
        self.assertEqual(rows["implementation"]["profile_digest"],
                         IMPLEMENTATION_PROFILE)
        self.assertEqual(rows["review"]["profile_digest"], REVIEW_PROFILE)
        self.assertEqual(json.loads(rows["review"]["depends_on"]),
                         [{"job_id": JOB, "kind": "implementation"}])

    def test_the_projection_holds_the_review_behind_its_implementation(self):
        """THE GATE IS THE WHOLE POINT OF THE DEPENDENCY.

        A resolved Job that projected both stages `queued` would offer an
        independent review of a candidate that does not exist yet.
        """
        submit(self.jobs, self.resolved()["submission"])
        document = status(self.jobs, self.acts, observed_at=NOW)
        states = {one["stage_id"]: one["state"]
                  for entry in document["jobs"] for one in entry["stages"]}
        self.assertEqual(states, {f"{JOB}/implementation": "queued",
                                  f"{JOB}/review": "blocked"})
        review = [one for entry in document["jobs"]
                  for one in entry["stages"]
                  if one["stage_id"] == f"{JOB}/review"][0]
        self.assertEqual(review["gates"],
                         [{"stage_id": f"{JOB}/implementation",
                           "state": "queued", "open": False}])

    def test_a_resolution_with_a_ceiling_records_its_limits(self):
        """AND THE STORE'S OWN READER REPORTS WHAT THE REQUEST OVERRODE.

        `execution_limits_of` is the public immutable reader of a Job's
        admitted configuration and `boundary_seconds` is what a launch
        actually asks. Both are reached, because a resolution whose override
        stopped at the document would configure nothing.
        """
        from baton_v12.job_manager.submission import (boundary_seconds,
                                                      execution_limits_of)

        held = self.resolved(overrides={"execution_limits": {
            "provider_turn_seconds": 5400}})
        self.assertEqual(held["submission"]["schema"], SUBMISSION_SCHEMA)
        submit(self.jobs, held["submission"])
        self.assertEqual(
            execution_limits_of(self.jobs, JOB),
            {"requested": {"provider_turn_seconds": 5400},
             "compatibility_generation":
                 execution_limits.CURRENT_GENERATION})
        self.assertEqual(boundary_seconds(self.jobs, JOB, "provider_turn"),
                         5400)
        self.assertEqual(
            boundary_seconds(self.jobs, JOB, "ordinary_verification"), 900)

    def test_a_resolution_without_a_ceiling_submits_as_a_legacy_document(self):
        """A `/1` DOCUMENT IS STILL A `/1` DOCUMENT.

        A request that overrides nothing resolves to the exact schema and the
        exact member set this pipeline already admits -- the member is absent
        rather than present and empty, which is the distinction
        `documents._job` keeps. The store still pins the generation it
        admitted the Job under, because "the preserved DEFAULTS are as much a
        part of a Job's admitted configuration as an override is".
        """
        from baton_v12.job_manager.submission import (boundary_seconds,
                                                      execution_limits_of)

        held = self.resolved()
        self.assertEqual(held["submission"]["schema"],
                         documents.SUBMISSION_SCHEMAS[0])
        self.assertNotIn(documents.JOB_LIMIT_MEMBER,
                         held["submission"]["jobs"][0])
        submit(self.jobs, held["submission"])
        self.assertEqual(execution_limits_of(self.jobs, JOB),
                         {"requested": {},
                          "compatibility_generation":
                              execution_limits.CURRENT_GENERATION})
        self.assertEqual(boundary_seconds(self.jobs, JOB, "provider_turn"),
                         3600)

    def test_an_exact_resubmission_of_one_resolution_replays(self):
        """IDEMPOTENCE IS THE SUBMISSION'S AND IS NOT RE-EARNED HERE.

        What this case proves is that two resolutions of one request produce
        one durable identity -- so a caller that resolved twice and submitted
        twice has one Job rather than a collision.
        """
        first = submit(self.jobs, self.resolved()["submission"])
        second = submit(self.jobs, self.resolved()["submission"])
        self.assertEqual(first, second)
        self.assertEqual([row["job_id"] for row in stage_rows(self.jobs)],
                         [JOB, JOB])

    def test_a_changed_deployment_cannot_reinterpret_a_submitted_job(self):
        """THE ACCEPTANCE SENTENCE, DRIVEN AT THE STORE.

        "Changing a template/default cannot reinterpret a previously
        resolved/submitted Job." A deployment that reinstalls its pool
        resolves a DIFFERENT document -- visibly, with a different profile
        digest and a different signature -- and the Job already recorded is
        untouched: `submission._unclaimed` refuses the second intent on the
        identity the first one holds.
        """
        import json

        before = self.resolved()
        submit(self.jobs, before["submission"])
        moved = configuration(profiles={
            "implementation": {"profile_name": "reference",
                               "profile_digest": "sha256:" + "9" * 64},
            "review": {"profile_name": "reviewer",
                       "profile_digest": REVIEW_PROFILE}})
        after = resolve(request(), configuration=moved)
        self.assertNotEqual(submission_signature(after["submission"]),
                            submission_signature(before["submission"]))
        self.assertNotEqual(resolution_digest(after),
                            resolution_digest(before))
        with self.assertRaises(ContractRefusal) as caught:
            submit(self.jobs, after["submission"])
        self.assertIn(JOB, caught.exception.message)
        rows = {one["kind"]: one for one in stages_of(self.jobs, JOB)}
        self.assertEqual(rows["implementation"]["profile_digest"],
                         IMPLEMENTATION_PROFILE)
        self.assertEqual(
            json.loads(self.jobs_document())["jobs"][0]["stages"][0]
            ["profile_digest"], IMPLEMENTATION_PROFILE)

    def jobs_document(self):
        from baton_v12.job_manager.submission import submission_of

        return submission_of(self.jobs, f"sub-{JOB}")["document"]

    def test_the_legacy_submission_contract_is_untouched(self):
        """PRESERVE OLD SUBMISSION CONTRACTS, proved by submitting one.

        A hand-authored `/1` document naming two Works across one Job's
        stages is still admitted exactly as it was: this module refuses to
        PRODUCE one, and it changes nothing about what `documents` accepts.
        """
        if __package__:
            from .fixtures import submission
        else:
            from fixtures import submission

        recorded = submit(self.jobs, submission())
        self.assertEqual(recorded["jobs"], ["job-a", "job-b"])
        self.assertEqual(recorded["stages"],
                         ["job-a/implementation", "job-a/review",
                          "job-b/implementation"])


class TheTwoScopes(ResolverCase):
    """R3: the selected work scope and the bounded test-change scope.

    review-2026-10-26T17-46-15Z: `scope` was one list, documented as
    test-change paths and copied wholesale into `test_scope`, so a request
    selecting the PRODUCT paths its task covers was answered with a Job
    granting test-change authority over those product paths — and the selected
    work scope was nowhere in the resolution.
    """

    def test_the_two_scopes_differ_and_are_both_retained(self):
        held = self.resolved()
        self.assertEqual(held["scope"]["work"], list(WORK_SCOPE))
        self.assertEqual(held["scope"]["tests"], list(TEST_SCOPE))
        self.assertNotEqual(held["scope"]["work"], held["scope"]["tests"])

    def test_only_the_test_scope_reaches_the_submission(self):
        """THE EXACT COUNTEREXAMPLE FROM THE REVIEWER'S PROBE.

        A product path in the selected work scope must not appear as
        `test_scope`, because `test_scope` IS the test-change authority a
        reviewer and an integrator check a proposal against.
        """
        held = self.resolved()
        self.assertEqual(held["submission"]["jobs"][0]["test_scope"],
                         list(TEST_SCOPE))
        for path in WORK_SCOPE:
            self.assertNotIn(path,
                             held["submission"]["jobs"][0]["test_scope"])

    def test_a_work_scope_of_product_paths_grants_no_test_scope(self):
        held = self.resolved(scope={
            "work": ["v12/python/src/baton_v12/job_manager/submission.py"],
            "tests": []})
        self.assertEqual(
            held["scope"]["work"],
            ["v12/python/src/baton_v12/job_manager/submission.py"])
        self.assertEqual(held["scope"]["tests"], [])
        self.assertEqual(held["submission"]["jobs"][0]["test_scope"], [])

    def test_an_empty_test_scope_is_a_work_that_changes_no_test(self):
        held = self.resolved(scope={"work": list(WORK_SCOPE), "tests": []})
        self.assertEqual(held["scope"]["tests"], [])
        self.assertEqual(held["submission"]["jobs"][0]["test_scope"], [])

    def test_an_empty_work_scope_refuses(self):
        """A TASK THAT COVERS NOTHING HAS NO SELECTED SCOPE.

        And the refusal says which member may be empty, so a caller who
        confused the two is told rather than left guessing.
        """
        with self.assertRaises(ContractRefusal) as caught:
            self.resolved(scope={"work": [], "tests": list(TEST_SCOPE)})
        self.assertIn("non-empty", self.refused(caught))
        self.assertIn("TEST scope", self.refused(caught))

    def test_changing_either_scope_changes_the_resolved_intent(self):
        """SCOPE CHANGES ALTER RESOLVED INTENT, which is R3's last clause.

        The work scope moves the resolution and NOT the submission, because it
        reaches no submission member; the test scope moves both. Asserting
        only one of those would leave the other free to be ignored.
        """
        held = self.resolved()
        moved_work = self.resolved(scope={
            "work": ["v12/python/src/baton_v12/job_manager/submission.py"],
            "tests": list(TEST_SCOPE)})
        self.assertNotEqual(resolution_digest(moved_work),
                            resolution_digest(held))
        self.assertEqual(submission_signature(moved_work["submission"]),
                         submission_signature(held["submission"]))
        moved_tests = self.resolved(scope={
            "work": list(WORK_SCOPE),
            "tests": ["v12/python/tests/job_manager/test_submission.py"]})
        self.assertNotEqual(resolution_digest(moved_tests),
                            resolution_digest(held))
        self.assertNotEqual(submission_signature(moved_tests["submission"]),
                            submission_signature(held["submission"]))

    def test_the_closed_member_rules_still_hold_on_both(self):
        """RETAIN STRICT SUPPORTED-VERSION/MEMBER REFUSAL, as R3 requires."""
        self.assertEqual(templates.SCOPE_MEMBERS, ("work", "tests"))
        with self.assertRaises(ContractRefusal) as caught:
            self.resolved(scope={"work": list(WORK_SCOPE),
                                 "tests": list(TEST_SCOPE),
                                 "test_scope": []})
        self.assertIn("test_scope", self.refused(caught))


class TheRegisteredTemplateCannotBeWrittenTo(ResolverCase):
    """R2: the other public door, which the first candidate left open.

    review-2026-10-26T17-46-15Z: `template_of` answered with
    `TEMPLATES[version]` itself, so
    `template_of(v)["completion"]["delivers"] = "not-the-reviewed-proposal"`
    changed what the next resolution of that same version delivered, with no
    refusal. Tuple role sequences froze the sequences and none of the
    dictionaries in them.
    """

    def test_the_reviewers_exact_probe_now_raises_instead_of_succeeding(self):
        definition = templates.template_of(IMPLEMENTATION_REVIEW)
        with self.assertRaises(TypeError):
            definition["completion"]["delivers"] = "not-the-reviewed-proposal"
        self.assertEqual(self.resolved()["rules"]["completion"]["delivers"],
                         CANDIDATE_OUTPUT)

    def test_no_member_of_a_registered_template_can_be_assigned(self):
        """EVERY DEPTH, not the one the probe happened to reach."""
        definition = templates.template_of(IMPLEMENTATION_REVIEW)
        for target, member, value in (
                (definition, "version", "baton.v12.job-template.mine/1"),
                (definition, "terminal_policy", "discard"),
                (definition["completion"], "outcome", "accepted-by-me"),
                (definition["correction"], "episode_ending", "declined"),
                (definition["failure"], "stage_state", "completed"),
                (definition["roles"][0], "kind", "review"),
                (definition["roles"][1], "depends_on", ())):
            with self.assertRaises(TypeError):
                target[member] = value

    def test_a_registered_template_cannot_be_added_to_or_removed(self):
        with self.assertRaises(TypeError):
            TEMPLATES["baton.v12.job-template.mine/1"] = {}
        with self.assertRaises(TypeError):
            del TEMPLATES[IMPLEMENTATION_REVIEW]
        definition = templates.template_of(IMPLEMENTATION_REVIEW)
        with self.assertRaises(TypeError):
            del definition["failure"]
        self.assertEqual(sorted(TEMPLATES), [IMPLEMENTATION_REVIEW])

    def test_a_declared_sequence_cannot_be_appended_to(self):
        definition = templates.template_of(IMPLEMENTATION_REVIEW)
        for sequence in (definition["roles"],
                         definition["permitted_overrides"],
                         definition["roles"][1]["produces"],
                         definition["correction"]["repeats"]):
            self.assertIs(type(sequence), tuple)
            with self.assertRaises(AttributeError):
                sequence.append("whatever")

    def test_the_detached_view_is_json_data_and_fully_mutable(self):
        """INSPECTION STAYS USEFUL, which immutability alone does not give.

        A `MappingProxyType` is what makes `template_of`'s answer unwritable,
        and it is also something `json.dumps` and `copy.deepcopy` both refuse
        — so an inspection surface that answered only proxies would be safe
        and unusable. `template_document` answers the same declaration as
        exact built-in data.
        """
        import copy

        mine = templates.template_document(IMPLEMENTATION_REVIEW)
        self.assertIs(type(mine), dict)
        self.assertIs(type(mine["roles"]), list)
        self.assertIs(type(mine["roles"][0]), dict)
        self.assertIs(type(mine["roles"][1]["produces"]), list)
        json.dumps(mine)
        copy.deepcopy(mine)
        self.assertEqual(mine["version"], IMPLEMENTATION_REVIEW)
        self.assertEqual(mine["completion"]["delivers"], CANDIDATE_OUTPUT)

    def test_mutating_the_detached_view_changes_no_later_resolution(self):
        mine = templates.template_document(IMPLEMENTATION_REVIEW)
        mine["completion"]["delivers"] = "not-the-reviewed-proposal"
        mine["roles"].append({"role": "mine", "kind": "integration",
                              "depends_on": [], "consumes": [],
                              "produces": []})
        mine["permitted_overrides"].append("terminal_policy")
        held = self.resolved()
        self.assertEqual(held["rules"]["completion"]["delivers"],
                         CANDIDATE_OUTPUT)
        self.assertEqual([one["kind"] for one in held["stages"]],
                         ["implementation", "review"])
        self.assertEqual(held["template"]["permitted_overrides"],
                         ["execution_limits"])
        self.assertEqual(
            templates.template_document(IMPLEMENTATION_REVIEW)
            ["completion"]["delivers"], CANDIDATE_OUTPUT)

    def test_the_frozen_declaration_is_not_json_and_says_so_by_raising(self):
        """STATED AS A CASE rather than left for somebody to discover.

        `template_of` is the identity-stable immutable declaration and
        `template_document` is the serializable one; a caller reaching for the
        wrong one gets a TypeError at the first attempt rather than a document
        that quietly works until it does not.
        """
        definition = templates.template_of(IMPLEMENTATION_REVIEW)
        with self.assertRaises(TypeError):
            json.dumps(definition)
        self.assertEqual(json.loads(json.dumps(
            templates.template_document(IMPLEMENTATION_REVIEW)))["version"],
            IMPLEMENTATION_REVIEW)

    def test_the_declaration_rule_still_refuses_what_it_refused(self):
        """A FROZEN TABLE IS STILL A CHECKED ONE.

        `check_template` reads the registered declaration through a
        `MappingProxyType` now, so the case that matters is that it still
        accepts every registered entry and still refuses a bad relationship
        when one is handed to it as a proxy rather than as a dict.
        """
        from types import MappingProxyType

        for definition in TEMPLATES.values():
            check_template(definition)
        broken = MappingProxyType({
            "version": "baton.v12.job-template.probe/1",
            "terminal_policy": TERMINAL_POLICIES[0],
            "permitted_overrides": ("execution_limits",),
            "roles": (MappingProxyType(
                {"role": "review", "kind": "review",
                 "depends_on": (), "consumes": ("proposal",),
                 "produces": ()}),),
            "completion": MappingProxyType({}),
            "correction": MappingProxyType({}),
            "failure": MappingProxyType({})})
        with self.assertRaises(ContractRefusal) as caught:
            check_template(broken)
        self.assertIn("no role it depends on produces", self.refused(caught))


class TheConsumptionContract(JobManagerCase):
    """R1: a resolution is spendable only while this build still produces it.

    review-2026-10-26T17-46-15Z, reproducing the reviewer's own probe: the
    answer's `compatibility_generation` is descriptive and the real consumer
    never receives it. `submission._job` stamps a Job's generation from
    `execution_limits.CURRENT_GENERATION` at SUBMIT time, so a default change
    between resolving and admitting left a saved resolution reporting 3600 for
    a Job the store answered 7200 for — through byte-identical submissions.

    The cases below move the default the way the probe does, in-process only,
    and touch no installed default and no live instance.
    """

    def setUp(self):
        super().setUp()
        self.jobs = self.store()

    def resolved(self, **named):
        return resolve(request(**named), configuration=configuration())

    def refused(self, caught):
        return caught.exception.message

    def newer_generation(self, provider=7200):
        """A hypothetical supported generation, process-local.

        Exactly the probe's construction: generation 1's table with one
        boundary moved, registered as 2, and `CURRENT_GENERATION` moved onto
        it. Nothing is written and `GENERATIONS` is restored by `patch.dict`.
        """
        from unittest import mock

        newer = dict(execution_limits.GENERATIONS[
            execution_limits.CURRENT_GENERATION])
        newer["provider_turn"] = provider
        moved = max(execution_limits.GENERATIONS) + 1
        return mock.patch.dict(
            execution_limits.GENERATIONS, {moved: newer}), mock.patch.object(
            execution_limits, "CURRENT_GENERATION", moved), moved

    def test_a_current_resolution_is_consumable_and_answers_its_submission(
            self):
        held = self.resolved()
        taken = templates.submission_for_admission(held)
        self.assertEqual(taken, held["submission"])
        self.assertEqual(owned_submission(taken), taken)
        recorded = submit(self.jobs, taken)
        self.assertEqual(recorded["jobs"], [JOB])

    def test_the_saved_resolution_refuses_after_the_default_moved(self):
        """THE DEFECT, DRIVEN AS A REFUSAL.

        The probe's `saved_resolution_submitted_provider_seconds` was 7200 for
        a resolution reporting 3600. The resolution is now unspendable and the
        refusal names both generations; the store is untouched.
        """
        before = self.resolved(template=IMPLEMENTATION_REVIEW)
        self.assertEqual(
            before["execution_limits"]["boundaries"]["provider_turn"]
            ["seconds"], 3600)
        generations, current, moved = self.newer_generation()
        with generations, current:
            with self.assertRaises(ContractRefusal) as caught:
                templates.submission_for_admission(before)
            self.assertIn(str(moved), self.refused(caught))
            self.assertIn(
                str(before["execution_limits"]["compatibility_generation"]),
                self.refused(caught))
            self.assertIn("Nothing has been submitted", self.refused(caught))
        self.assertEqual([row["job_id"] for row in stage_rows(self.jobs)], [])

    def test_re_resolving_the_same_request_is_consumable_and_honest(self):
        """AND ITS SUBMISSION IS THE IDENTICAL BYTES.

        Which is the half that made the defect invisible: the document does
        not change, so only the resolution could have told anybody, and it was
        the thing that was wrong. After re-resolving, the reported ceilings and
        the Job the store admits agree.
        """
        from baton_v12.job_manager.submission import (boundary_seconds,
                                                      execution_limits_of)

        before = self.resolved(template=IMPLEMENTATION_REVIEW)
        generations, current, moved = self.newer_generation()
        with generations, current:
            after = self.resolved(template=IMPLEMENTATION_REVIEW)
            self.assertEqual(after["submission"], before["submission"])
            self.assertEqual(after["template"], before["template"])
            self.assertEqual(
                after["execution_limits"]["compatibility_generation"], moved)
            self.assertEqual(
                after["execution_limits"]["boundaries"]["provider_turn"]
                ["seconds"], 7200)
            taken = templates.submission_for_admission(after)
            submit(self.jobs, taken)
            self.assertEqual(
                execution_limits_of(self.jobs, JOB)[
                    "compatibility_generation"], moved)
            self.assertEqual(
                boundary_seconds(self.jobs, JOB, "provider_turn"), 7200)
            self.assertEqual(
                after["execution_limits"]["boundaries"]["provider_turn"]
                ["seconds"],
                boundary_seconds(self.jobs, JOB, "provider_turn"))

    def test_a_consumer_may_declare_the_generation_it_will_admit_under(self):
        """THE OPERAND IS THE CONSUMER'S OWN FACT.

        A consumer that reads the admitting generation from its owner is held
        to that rather than to a module constant — agreeing is consumable and
        disagreeing refuses, in both directions.
        """
        held = self.resolved()
        pinned = held["execution_limits"]["compatibility_generation"]
        self.assertEqual(
            templates.submission_for_admission(held, generation=pinned),
            held["submission"])
        with self.assertRaises(ContractRefusal) as caught:
            templates.submission_for_admission(
                held, generation=execution_limits.LEGACY_GENERATION)
        self.assertIn(str(execution_limits.LEGACY_GENERATION),
                      self.refused(caught))
        with self.assertRaises(ContractRefusal):
            templates.submission_for_admission(held, generation=99)

    def test_a_partial_override_refuses_on_the_pin_not_on_the_numbers(self):
        """PARTIAL OVERRIDES, which R1 names explicitly.

        An overridden boundary is `job` origin and no default can move it; a
        preserved one is `compatibility` and a default can. Both still travel
        under one pinned generation, so the refusal is about the generation the
        resolution CLAIMS the Job was admitted under — which is itself a fact
        `execution_limits_of` reports and would have disagreed with.
        """
        held = self.resolved(overrides={"execution_limits": {
            "provider_turn_seconds": 5400}})
        boundaries = held["execution_limits"]["boundaries"]
        self.assertEqual(boundaries["provider_turn"]["origin"],
                         execution_limits.JOB)
        self.assertEqual(boundaries["ordinary_verification"]["origin"],
                         execution_limits.COMPATIBILITY)
        generations, current, moved = self.newer_generation()
        with generations, current:
            with self.assertRaises(ContractRefusal) as caught:
                templates.submission_for_admission(held)
            self.assertIn(str(moved), self.refused(caught))
            again = self.resolved(overrides={"execution_limits": {
                "provider_turn_seconds": 5400}})
            self.assertEqual(
                again["execution_limits"]["boundaries"]["provider_turn"]
                ["seconds"], 5400)
            templates.submission_for_admission(again)

    def test_a_fully_overriding_resolution_refuses_on_the_pin_too(self):
        """EVEN WHEN NO NUMBER WOULD HAVE MOVED.

        Every boundary is `job` origin here, so the default change reaches
        none of them — and the resolution still says the Job is admitted under
        a generation the store would not stamp, which `execution_limits_of`
        reports as part of its admitted configuration. Refusing uniformly is
        what keeps the resolution's account of the Job true.
        """
        held = self.resolved(overrides={"execution_limits": {
            "provider_turn_seconds": 5400,
            "verification_command_seconds": 1200}})
        for one in held["execution_limits"]["boundaries"].values():
            self.assertEqual(one["origin"], execution_limits.JOB)
        generations, current, _ = self.newer_generation()
        with generations, current:
            with self.assertRaises(ContractRefusal):
                templates.submission_for_admission(held)

    def test_a_changed_template_declaration_refuses_a_saved_resolution(self):
        """THE SAME CONTRACT COVERS R2'S CLASS OF DRIFT.

        The registry cannot be written to any more, so this drives the check
        by handing it a resolution whose own preserved request this build no
        longer resolves the same way — which is what a template revision would
        look like to a resolution saved before it.
        """
        held = self.resolved()
        held["rules"]["completion"]["delivers"] = "not-the-reviewed-proposal"
        with self.assertRaises(ContractRefusal) as caught:
            templates.submission_for_admission(held)
        self.assertIn("rules", self.refused(caught))
        self.assertIn("Nothing has been submitted", self.refused(caught))

    def test_an_edited_derived_member_refuses_and_names_it(self):
        """THE MEMBERS THE RE-DERIVATION CAN DISAGREE ABOUT."""
        for member, value in (
                ("source", {"input_digest": "sha256:" + "f" * 64,
                            "policy_digest": POLICY}),
                ("task", {"job_id": "another-job", "work_id": WORK,
                          "statement": STATEMENT,
                          "submission_id": f"sub-{JOB}"}),
                ("scope", {"work": list(WORK_SCOPE),
                           "tests": ["v12/python/tests/job_manager"]}),
                ("execution_limits", dict(
                    self.resolved()["execution_limits"],
                    compatibility_generation=execution_limits
                    .CURRENT_GENERATION))):
            held = self.resolved()
            held[member] = value
            if member == "execution_limits":
                held[member]["boundaries"]["provider_turn"]["seconds"] = 1
            with self.assertRaises(ContractRefusal) as caught:
                templates.submission_for_admission(held)
            self.assertIn("Nothing has been submitted", self.refused(caught))

    def test_a_resolution_whose_stages_were_emptied_refuses(self):
        """AND THE INNER REFUSAL IS SURFACED RATHER THAN SWALLOWED.

        `_configuration_of` reads the profiles off the stages, so a resolution
        with none describes a deployment that installed nothing — which
        `_stages` already refuses by role. Either refusal is correct; what
        would not be is answering a submission.
        """
        for value in ([], [self.resolved()["stages"][0]]):
            held = self.resolved()
            held["stages"] = value
            with self.assertRaises(ContractRefusal):
                templates.submission_for_admission(held)
        self.assertEqual([row["job_id"] for row in stage_rows(self.jobs)], [])

    def test_a_purely_preserved_member_is_a_different_request_not_a_stale_one(
            self):
        """THE CONTRACT'S BOUNDARY, STATED AS A CASE.

        The acceptance criteria, the task statement and the selected work
        scope reach nothing derived, so a resolution carrying different ones
        is a resolution of a DIFFERENT REQUEST that this build produces
        perfectly well — and consuming it is correct. This verb answers
        "would this build still produce this", not "has anybody edited this".
        What binds one consumer to one exact set of bytes is
        `resolution_digest`, and the digest does move.
        """
        held = self.resolved()
        before = resolution_digest(held)
        held["acceptance"] = ["something else entirely"]
        held["task"]["statement"] = "a different statement"
        held["scope"]["work"] = ["v12/python/tools/job_manager.py"]
        self.assertEqual(templates.submission_for_admission(held),
                         held["submission"])
        self.assertNotEqual(resolution_digest(held), before)

    def test_an_edited_submission_member_refuses(self):
        """BECAUSE THE DOCUMENT IS WHAT WOULD BE RECORDED.

        A resolution whose submission no longer matches its own resolved
        intent is the one case where consuming it would durably write
        something nobody resolved.
        """
        held = self.resolved()
        held["submission"]["jobs"][0]["test_scope"] = list(WORK_SCOPE)
        with self.assertRaises(ContractRefusal) as caught:
            templates.submission_for_admission(held)
        self.assertIn("submission", self.refused(caught))

    def test_a_resolution_that_is_not_one_refuses(self):
        for value in (None, [], "a resolution", {},
                      {"schema": "baton.v12.job-template-resolution/9"}):
            with self.assertRaises(ContractRefusal):
                templates.submission_for_admission(value)
        held = self.resolved()
        del held["rules"]
        with self.assertRaises(ContractRefusal) as caught:
            templates.submission_for_admission(held)
        self.assertIn("rules", self.refused(caught))

    def test_a_resolution_resolved_from_the_default_is_consumable(self):
        """THE SELECTION ORIGIN IS THE ONE PERMITTED DIFFERENCE.

        Consuming re-derives with the version named EXPLICITLY, so its origin
        is `request` where this resolution's was `configured-default`. That
        member is excluded from the comparison and nothing else is.
        """
        held = self.resolved()
        self.assertEqual(held["template"]["origin"], "configured-default")
        self.assertEqual(templates.submission_for_admission(held),
                         held["submission"])
        held["template"]["origin"] = "request"
        self.assertEqual(templates.submission_for_admission(held),
                         held["submission"])
        held["template"]["origin"] = "inherited"
        with self.assertRaises(ContractRefusal) as caught:
            templates.submission_for_admission(held)
        self.assertIn("inherited", self.refused(caught))

    def test_the_legacy_submission_and_retry_contracts_are_preserved(self):
        """NOTHING HERE CHANGES WHAT `documents` ACCEPTS OR WHAT RETRY DOES.

        A hand-authored `/1` document naming two Works across one Job's stages
        still records exactly as it did, and a fresh attempt at a resolved
        Job's own submission still carries that submission's bytes forward —
        `fresh_attempt._composed` copies the stored entry and renames it, and
        this candidate adds no member for it to carry.
        """
        if __package__:
            from .fixtures import submission
        else:
            from fixtures import submission
        from baton_v12.job_manager.fresh_attempt import successor_of
        from baton_v12.job_manager.submission import submission_of

        recorded = submit(self.jobs, submission())
        self.assertEqual(recorded["jobs"], ["job-a", "job-b"])
        held = self.resolved()
        submit(self.jobs, templates.submission_for_admission(held))
        stored = json.loads(submission_of(self.jobs,
                                          f"sub-{JOB}")["document"])
        self.assertEqual(stored, held["submission"])
        self.assertEqual(successor_of(JOB), f"{JOB}-retry-2")


class TheOutputNamesAgreeWithTheirOwners(unittest.TestCase):
    """The names this table spells, held to the modules that own them."""

    def test_the_candidate_output_is_the_host_sides_own_spelling(self):
        from tools.authoring_baseline import PROPOSAL_OUTPUT

        self.assertEqual(CANDIDATE_OUTPUT, PROPOSAL_OUTPUT)

    def test_the_candidate_output_is_the_worker_adapters_own_spelling(self):
        """READ FROM THE ADAPTER'S SOURCE RATHER THAN IMPORTED.

        `v12/worker/claude_agent.py` is the module that declares which outputs
        each role produces, and nothing from `baton_v12` travels into that
        image -- it imports `source_profiles` as a top-level package the way
        the container lays it out, so importing it here would mean
        reproducing that layout on `sys.path` for the whole suite. The
        literal is read instead, which is the same drift this would catch
        with none of that.
        """
        source = (pathlib.Path(__file__).resolve().parents[3] / "worker"
                  / "claude_agent.py")
        declared = {}
        for node in ast.parse(source.read_text(encoding="utf-8")).body:
            if type(node) is not ast.Assign:
                continue
            for target in node.targets:
                if type(target) is ast.Name and target.id in (
                        "IMPLEMENTATION_OUTPUTS", "REVIEW_OUTPUTS"):
                    declared[target.id] = ast.literal_eval(node.value)
        self.assertEqual(declared["IMPLEMENTATION_OUTPUTS"],
                         (CANDIDATE_OUTPUT,))
        self.assertEqual(
            declared["REVIEW_OUTPUTS"],
            tuple(TEMPLATES[IMPLEMENTATION_REVIEW]["roles"][1]["produces"]))

    def test_the_review_output_names_come_from_the_review_driver(self):
        produces = TEMPLATES[IMPLEMENTATION_REVIEW]["roles"][1]["produces"]
        self.assertEqual(produces, (review_driver.FINDINGS_OUTPUT,
                                    review_driver.LOGS_OUTPUT))

    def test_the_two_resolved_kinds_are_the_pools_two_lanes(self):
        """A STAGE IS ALLOCATED BY ITS LANE, and this template's two kinds are
        exactly the two lanes `scheduler` installs workers for."""
        kinds = tuple(role["kind"]
                      for role in TEMPLATES[IMPLEMENTATION_REVIEW]["roles"])
        self.assertEqual(kinds, scheduler.LANES)
        for kind in kinds:
            self.assertIn(kind, STAGE_KINDS)


if __name__ == "__main__":
    unittest.main()
