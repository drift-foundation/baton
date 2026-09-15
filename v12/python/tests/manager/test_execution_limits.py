"""W156162: the launch delivery that carries a Job's own execution ceilings.

WHAT THIS MODULE COVERS AND WHAT IT DOES NOT. `baton.worker-launch/3` is the
carrier: it states the Job and attempt a container is running, the identities the
Job was submitted with, the identities this runtime was actually given, and the
effective ceilings with their own seal. These cases hold the document, its
versioning and its exact adoption comparison.

They do NOT show a provider turn or a verification command running under a
configured ceiling. That is the propagation half -- the ordinary worker, the
integration entry and the derived judgment reading this document and passing the
number to a command -- and it is not in this slice. A carrier proves delivery is
possible; it is not evidence that anything was delivered.
"""

import os
import tempfile
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import execution_limits as limits
from baton_v12.worker_manager import launch


def job_execution(**changed):
    """The ordinary context, resolved through the current generation."""
    configuration = limits.resolved({"provider_turn_seconds": 60},
                                    limits.CURRENT_GENERATION)
    held = {"job_id": "job-a", "attempt_id": "attempt-1",
            "job_input_digest": "sha256:" + "1" * 64,
            "job_policy_digest": "sha256:" + "2" * 64,
            "runtime_input_digest": "sha256:" + "3" * 64,
            "runtime_policy_digest": "sha256:" + "2" * 64,
            "execution_limits": configuration,
            "execution_limits_digest": launch._digest(configuration)}
    held.update(changed)
    return held


class TheVersionMovesWithTheMember(unittest.TestCase):
    """`/1` and `/2` are untouched, which is what makes this additive."""

    def test_a_document_without_a_job_context_is_still_version_one(self):
        held = launch.launch_document(session="s", contract="c", role="r")
        self.assertEqual(held["schema"], "baton.worker-launch/1")
        self.assertNotIn("job_execution", held)
        self.assertNotIn("transport", held)

    def test_a_document_with_a_transport_alone_is_still_version_two(self):
        from baton_v12.worker_manager import exchange

        held = launch.launch_document(session="s", contract="c", role="r",
                                      transport=exchange.EXCHANGE_TRANSPORT)
        self.assertEqual(held["schema"], "baton.worker-launch/2")
        self.assertNotIn("job_execution", held)

    def test_a_job_context_selects_version_three(self):
        held = launch.launch_document(session="s", contract="c", role="r",
                                      job_execution=job_execution())
        self.assertEqual(held["schema"], "baton.worker-launch/3")
        self.assertEqual(sorted(held), sorted(launch.JOB_MEMBERS))
        # THE TRANSPORT IS STATED, and here it is stated as absent -- which a
        # one-shot integration launch needs to be able to say explicitly.
        self.assertIsNone(held["transport"])
        self.assertEqual(
            held["job_execution"]["execution_limits"]["boundaries"]
            ["provider_turn"]["seconds"], 60)

    def test_a_job_context_keeps_a_real_transport(self):
        from baton_v12.worker_manager import exchange

        held = launch.launch_document(session="s", contract="c", role="r",
                                      transport=exchange.EXCHANGE_TRANSPORT,
                                      job_execution=job_execution())
        self.assertEqual(held["schema"], "baton.worker-launch/3")
        self.assertEqual(held["transport"], exchange.EXCHANGE_TRANSPORT)

    def test_the_closed_member_set_follows_the_schema(self):
        for schema, members in (
                ("baton.worker-launch/1", launch.LAUNCH_MEMBERS),
                ("baton.worker-launch/2", launch.EXCHANGE_MEMBERS),
                ("baton.worker-launch/3", launch.JOB_MEMBERS)):
            with self.subTest(schema=schema):
                self.assertEqual(launch.members_for({"schema": schema}),
                                 members)


class TheJobContextIsOwnedBeforeItIsWritten(unittest.TestCase):
    """A worker handed a ceiling nobody sealed has been handed a number nobody
    agreed to, so the refusals are at the authoring boundary."""

    def refused(self, **changed):
        with self.assertRaises(ContractRefusal) as caught:
            launch.launch_document(session="s", contract="c", role="r",
                                   job_execution=job_execution(**changed))
        return caught.exception

    def test_every_member_is_required(self):
        for name in launch.JOB_EXECUTION_MEMBERS:
            with self.subTest(member=name):
                held = job_execution()
                del held[name]
                with self.assertRaises(ContractRefusal):
                    launch.launch_document(session="s", contract="c", role="r",
                                           job_execution=held)

    def test_an_unknown_member_is_refused(self):
        held = job_execution()
        held["cumulative_seconds"] = 300
        with self.assertRaises(ContractRefusal):
            launch.launch_document(session="s", contract="c", role="r",
                                   job_execution=held)

    def test_a_seal_that_does_not_match_its_configuration_is_refused(self):
        held = self.refused(execution_limits_digest="sha256:" + "0" * 64)
        self.assertIn("nobody agreed to", held.message)

    def test_a_changed_ceiling_under_the_old_seal_is_refused(self):
        """The seal is over the configuration, so moving a number without
        resealing is caught where it is written."""
        held = job_execution()
        held["execution_limits"]["boundaries"]["provider_turn"]["seconds"] = 9
        with self.assertRaises(ContractRefusal):
            launch.launch_document(session="s", contract="c", role="r",
                                   job_execution=held)

    def test_the_job_and_runtime_identities_are_both_stated(self):
        """They are DIFFERENT facts and are not compared: a review or a derived
        judgment legitimately consumes a frozen input that is not the Job's
        own, so requiring them equal would refuse the ordinary case."""
        held = launch.launch_document(
            session="s", contract="c", role="r",
            job_execution=job_execution())["job_execution"]
        self.assertNotEqual(held["job_input_digest"],
                            held["runtime_input_digest"])
        self.assertEqual(held["job_policy_digest"],
                         held["runtime_policy_digest"])


class TheConfigurationIsHeldToTheJobOwnersOwnRules(unittest.TestCase):
    """R5, review 2026-09-13T01:36:01Z: A MATCHING SEAL PROVES BYTE
    CORRESPONDENCE, NOT THAT ANYBODY AGREED TO THE CONTENT.

    The first carrier took any document at all and checked only its digest, so a
    correctly sealed empty object was accepted, and so was a sealed object
    stating minutes, cumulative scope, an unknown generation and a negative
    ceiling. Every case here reseals its mutation, so the stale-seal check
    cannot be what refuses it.
    """

    def sealed(self, configuration):
        held = job_execution()
        held["execution_limits"] = configuration
        held["execution_limits_digest"] = launch._digest(configuration)
        with self.assertRaises(ContractRefusal) as caught:
            launch.launch_document(session="s", contract="c", role="r",
                                   job_execution=held)
        return caught.exception

    def test_a_correctly_sealed_empty_configuration_is_refused(self):
        self.sealed({})

    def test_foreign_units_and_scope_are_refused(self):
        configuration = limits.resolved({}, limits.CURRENT_GENERATION)
        configuration["units"] = "minutes"
        configuration["scope"] = "cumulative"
        held = self.sealed(configuration)
        self.assertIn("nobody resolved", held.message)

    def test_a_generation_this_build_does_not_hold_is_refused(self):
        configuration = limits.resolved({}, limits.CURRENT_GENERATION)
        configuration["compatibility_generation"] = 999
        self.sealed(configuration)

    def test_a_ceiling_outside_the_supported_range_is_refused(self):
        """The Job owner's own range, reached rather than restated: a negative
        provider ceiling is refused here because it is refused there."""
        configuration = limits.resolved({}, limits.CURRENT_GENERATION)
        configuration["requested"] = {"provider_turn_seconds": -1}
        held = self.sealed(configuration)
        self.assertIn("not ones the Job owner accepts", held.message)

    def test_an_effective_value_that_no_resolution_produces_is_refused(self):
        """The seconds and the requested settings must agree: a document whose
        boundary says 9 while its own settings say 60 is a configuration nobody
        resolved."""
        configuration = limits.resolved({"provider_turn_seconds": 60},
                                        limits.CURRENT_GENERATION)
        configuration["boundaries"]["provider_turn"]["seconds"] = 9
        self.sealed(configuration)

    def test_a_forged_origin_is_refused(self):
        configuration = limits.resolved({}, limits.CURRENT_GENERATION)
        configuration["boundaries"]["provider_turn"]["origin"] = "job"
        self.sealed(configuration)

    def test_a_boolean_where_a_second_belongs_is_refused(self):
        """Review 2026-09-13T01:44:11Z: `True == 1` in Python, so replacing the
        effective provider seconds with `true` and RESEALING compared equal to
        the resolution of a Job requesting 1 second, and the carrier returned
        `seconds: true`. The owner rejects a bool because it is not a whole
        number of seconds; the comparison has to be able to tell them apart."""
        configuration = limits.resolved({"provider_turn_seconds": 1},
                                        limits.CURRENT_GENERATION)
        configuration["boundaries"]["provider_turn"]["seconds"] = True
        self.sealed(configuration)

    def test_a_boolean_requested_setting_is_refused(self):
        configuration = limits.resolved({"verification_command_seconds": 1},
                                        limits.CURRENT_GENERATION)
        configuration["requested"]["verification_command_seconds"] = True
        self.sealed(configuration)

    def test_a_boolean_generation_is_refused(self):
        configuration = limits.resolved({}, limits.CURRENT_GENERATION)
        configuration["compatibility_generation"] = True
        self.sealed(configuration)

    def test_the_lower_bound_stays_a_valid_second(self):
        """The companion, so the rule refuses a bool rather than the number 1."""
        for requested in ({"provider_turn_seconds": limits.MIN_SECONDS},
                          {"verification_command_seconds": limits.MIN_SECONDS}):
            with self.subTest(requested=requested):
                configuration = limits.resolved(requested,
                                                limits.CURRENT_GENERATION)
                held = launch.launch_document(
                    session="s", contract="c", role="r",
                    job_execution=job_execution(
                        execution_limits=configuration,
                        execution_limits_digest=launch._digest(configuration)))
                self.assertEqual(held["job_execution"]["execution_limits"],
                                 configuration)

    def test_the_configuration_the_owner_resolves_is_accepted(self):
        """The positive, so the rule is a comparison rather than a refusal."""
        for requested in ({}, {"provider_turn_seconds": 60},
                          {"verification_command_seconds": 45},
                          {"provider_turn_seconds": 60,
                           "verification_command_seconds": 45}):
            with self.subTest(requested=requested):
                configuration = limits.resolved(requested,
                                                limits.CURRENT_GENERATION)
                held = job_execution(
                    execution_limits=configuration,
                    execution_limits_digest=launch._digest(configuration))
                self.assertEqual(
                    launch.launch_document(
                        session="s", contract="c", role="r",
                        job_execution=held)["job_execution"]
                    ["execution_limits"], configuration)


class TheDeliveryNamesTheAttemptItIsFor(unittest.TestCase):
    """R5: a launch root named for one attempt whose document describes another
    is the delivery mix-up this component exists to prevent, arriving inside the
    document instead of across it."""

    def setUp(self):
        self._root = tempfile.TemporaryDirectory(prefix="v12-launch-attempt-")
        self.addCleanup(self._root.cleanup)
        self.storage = os.path.join(self._root.name, "launch")

    def test_materializing_a_foreign_attempt_context_is_refused(self):
        with self.assertRaises(ContractRefusal) as caught:
            launch.materialize(self.storage, attempt_id="attempt-1",
                               session="s", contract="c", role="r",
                               job_execution=job_execution(
                                   attempt_id="attempt-other"))
        self.assertIn("one delivery is one attempt's", caught.exception.message)
        # AND NOTHING WAS WRITTEN: the refusal is before materialization.
        self.assertFalse(os.path.exists(self.storage))

    def test_adopting_a_foreign_attempt_context_is_refused(self):
        launch.materialize(self.storage, attempt_id="attempt-1", session="s",
                           contract="c", role="r",
                           job_execution=job_execution())
        with self.assertRaises(ContractRefusal):
            launch.adopt(self.storage, attempt_id="attempt-1", session="s",
                         contract="c", role="r",
                         job_execution=job_execution(
                             attempt_id="attempt-other"))


class TheDeliveryIsAdoptedByItsExactBytes(unittest.TestCase):
    """Adoption re-authors what this component would have written and compares
    canonical bytes, so the Job context is covered by the same one comparison
    that already covered session, contract and role."""

    def setUp(self):
        self._root = tempfile.TemporaryDirectory(prefix="v12-launch-limits-")
        self.addCleanup(self._root.cleanup)
        self.storage = os.path.join(self._root.name, "launch")

    def materialize(self, **changed):
        return launch.materialize(self.storage, attempt_id="attempt-1",
                                  session="s", contract="c", role="r",
                                  job_execution=job_execution(**changed))

    def test_a_delivery_carrying_a_job_context_is_adopted(self):
        made = self.materialize()
        held = launch.adopt(self.storage, attempt_id="attempt-1", session="s",
                            contract="c", role="r",
                            job_execution=job_execution())
        self.assertEqual(held.document, made.document)
        self.assertEqual(held.document["schema"], "baton.worker-launch/3")

    def test_another_jobs_ceiling_is_not_this_delivery(self):
        self.materialize()
        other = limits.resolved({"provider_turn_seconds": 61},
                                limits.CURRENT_GENERATION)
        with self.assertRaises(ContractRefusal):
            launch.adopt(self.storage, attempt_id="attempt-1", session="s",
                         contract="c", role="r",
                         job_execution=job_execution(
                             execution_limits=other,
                             execution_limits_digest=launch._digest(other)))

    def test_another_attempt_is_not_this_delivery(self):
        self.materialize()
        with self.assertRaises(ContractRefusal):
            launch.adopt(self.storage, attempt_id="attempt-1", session="s",
                         contract="c", role="r",
                         job_execution=job_execution(attempt_id="attempt-9"))

    def test_a_job_delivery_is_not_adopted_as_a_legacy_one(self):
        """A Job that configured a ceiling cannot fall back silently to a
        launch that does not carry it."""
        self.materialize()
        with self.assertRaises(ContractRefusal):
            launch.adopt(self.storage, attempt_id="attempt-1", session="s",
                         contract="c", role="r")

    def test_a_legacy_delivery_is_not_adopted_as_a_job_one(self):
        launch.materialize(self.storage, attempt_id="attempt-2", session="s",
                           contract="c", role="r")
        with self.assertRaises(ContractRefusal):
            launch.adopt(self.storage, attempt_id="attempt-2", session="s",
                         contract="c", role="r",
                         job_execution=job_execution(attempt_id="attempt-2"))


if __name__ == "__main__":                 # pragma: no cover
    unittest.main()
