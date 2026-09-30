"""The four endings, ASSERTED over the connected packet.

W236087 item 3's milestone, from reviews 2026-09-29T22-15-01Z through
2026-09-29T23-04-18Z: "one connected deterministic packet proof from generated
documents... real disposable stores, actual attachments/verdicts, bounded
supervision and positive cleanup", covering accepted-without-correction,
changes-requested then restored correction, rejection, and failure/interrupt.

WHAT DECIDES EVERY ASSERTION HERE IS CANONICAL. The verdicts come from
`review_cycles`' own attachment and verdict readers through the supervisor's
`review_disposition`; the restore is read from the manager's context journal by
`context_continuity`; the cleanup comes from the manager's own cleanup journal;
and the outcome is the one THIS PACKET'S supervisor published. Nothing is
asserted from a value this file supplied.

WHAT IS SIMULATED IS LABELLED IN `connected_packet_trace`: the OCI engine is the
accepted fixture's in-process one, the provider is a real child running a
scripted script, and the reviewer's dispositions are scripted -- committed
through the real owner API, never forged. The preparation and installation
boundaries are recorded there too.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:                                     # pragma: no cover
    sys.path.insert(0, HERE)

import connected_packet_trace as trace                       # noqa: E402
import correction_supervisor as supervisor                    # noqa: E402


class ConnectedEnding(unittest.TestCase):
    """One disposable world per ending. `doCleanups` runs it down either way."""

    def world_for(self):
        """A world whose cleanups are registered BEFORE `setUp` runs.

        A `setUp` that raises leaves its own patches started, and registering the
        unwind afterwards let one failure poison every later case in the process
        -- observed: a leaked provider-script patch made the next `setUp`'s
        substitution anchor stop matching.
        """
        world = trace.ConnectedPacket()
        self.addCleanup(world.doCleanups)
        world.setUp()
        self.world = world
        return world

    def run_packet(self, **operands):
        return self.world_for().run_packet(**operands)

    def assert_positive_cleanup(self, outcome, *, kinds):
        """Every runtime this run STARTED is positively excluded.

        A review attempt that never launched carries no runtime and is NOT
        counted as a positive cleanup: the manager holds nothing for it, and
        pretending otherwise is the distinction review 2026-09-29T22-36-24Z
        asked to be preserved.
        """
        started = [one for one in outcome["implementation_attempts"]
                   if outcome["cleanup"].get(one, {}).get("cleanup")]
        self.assertEqual(len(started), kinds["implementation"])
        for attempt in started:
            self.assertIn(outcome["cleanup"][attempt]["cleanup"],
                          ("complete", "retained"))


class AcceptedWithoutCorrection(ConnectedEnding):

    def test_the_first_review_accepts_and_the_run_makes_no_restore_claim(self):
        _held, outcome = self.run_packet(dispositions=["accepted"])
        self.assertEqual(outcome["outcome"],
                         supervisor.ACCEPTED_NO_CORRECTION)
        self.assertEqual(outcome["state"], "settled")
        self.assertEqual(outcome["stopped"], "completed")
        # THE VERDICT IS THE CANONICAL ONE, read through review_cycles.
        self.assertEqual(outcome["review_disposition"], supervisor.ACCEPTED)
        self.assertEqual(len(outcome["implementation_attempts"]), 1)
        self.assertEqual(len(outcome["review_attempts"]), 1)
        # AND IT CLAIMS NO RESTORE, because none happened.
        self.assertIs(outcome["context_continuity"]["continued"], False)
        self.assertEqual(outcome["held_because"], [])
        self.assert_positive_cleanup(outcome, kinds={"implementation": 1})


class CorrectedAndAccepted(ConnectedEnding):
    """The only ending that answers the provider question -- and the only one
    that has to prove a restore."""

    def test_changes_requested_then_a_restored_correction_is_accepted(self):
        _held, outcome = self.run_packet(
            dispositions=["changes-requested", "accepted"])
        self.assertEqual(outcome["outcome"], supervisor.CORRECTED_AND_ACCEPTED)
        self.assertEqual(outcome["stopped"], "completed")
        self.assertEqual(outcome["review_disposition"], supervisor.ACCEPTED)
        # TWO implementer invocations and TWO independent reviews, which is
        # exactly what the packet's bounds permit and no more.
        self.assertEqual(len(outcome["implementation_attempts"]), 2)
        self.assertEqual(len(outcome["review_attempts"]), 2)
        self.assertEqual(outcome["admissions"],
                         {"implementation": 2, "review": 2})
        # THE RESTORE, READ FROM THE MANAGER'S OWN CONTEXT JOURNAL: one context
        # across both uses and a later generation on the restored one.
        continuity = outcome["context_continuity"]
        self.assertIs(continuity["continued"], True)
        self.assertEqual(continuity["opening"]["context_id"],
                         continuity["restored"]["context_id"])
        self.assertGreater(continuity["restored"]["generation"],
                           continuity["opening"]["generation"])
        self.assertIn(continuity["opening"]["status"], ("ready", "retired"))
        # AND THE OPENING AND RESTORED ATTEMPTS ARE THE RECORDED ONES, in
        # episode order rather than in identity order.
        self.assertEqual(outcome["implementation_attempts"],
                         outcome["episode_chronology"]["implementation"])
        self.assertEqual(continuity["opening"]["attempt_id"],
                         outcome["implementation_attempts"][0])
        self.assertEqual(continuity["restored"]["attempt_id"],
                         outcome["implementation_attempts"][-1])
        self.assert_positive_cleanup(outcome, kinds={"implementation": 2})


class Rejected(ConnectedEnding):
    """A valid result. Nothing is manufactured from it and nothing reruns."""

    def test_a_canonical_rejection_is_reported_as_a_rejection(self):
        _held, outcome = self.run_packet(dispositions=["rejected"])
        self.assertEqual(outcome["outcome"], supervisor.REVIEW_REJECTED)
        self.assertEqual(outcome["review_disposition"], supervisor.REJECTED)
        # ONE implementer invocation: no correction is manufactured from a
        # rejection, and the cap is not spent on one.
        self.assertEqual(len(outcome["implementation_attempts"]), 1)
        self.assertEqual(outcome["admissions"]["implementation"], 1)
        self.assertIs(outcome["retry"], False)
        self.assertIs(outcome["context_continuity"]["continued"], False)
        self.assert_positive_cleanup(outcome, kinds={"implementation": 1})

    def test_how_a_rejected_run_STOPPED_is_recorded_without_erasing_it(self):
        """A rejected Job has nothing left to advance, so the loop stops
        `no-progress` -- a FACT about a decided run rather than a failure. An
        earlier version of the classifier turned that into
        `failed-or-unknown` and erased a valid canonical verdict.
        """
        _held, outcome = self.run_packet(dispositions=["rejected"])
        self.assertEqual(outcome["outcome"], supervisor.REVIEW_REJECTED)
        self.assertNotEqual(outcome["stopped"], "completed")
        self.assertTrue(any("stopped" in one
                            for one in outcome["held_because"]),
                        outcome["held_because"])


class FailureAndInterrupt(ConnectedEnding):

    def test_an_interruption_retains_the_outcome_and_is_not_swallowed(self):
        with self.assertRaises(supervisor.baseline.SupervisorInterrupted) \
                as raised:
            self.run_packet(dispositions=["accepted"], interrupt_at=1)
        outcome = raised.exception.outcome
        self.assertEqual(outcome["outcome"], supervisor.FAILED)
        self.assertEqual(outcome["state"], "held")
        self.assertIn("scripted interruption", outcome["interrupted"])
        self.assertIs(outcome["retry"], False)
        # THE OUTCOME IS ON DISK, which is the half an operator needs.
        import json

        with open(self.world.packet["outcome_path"], encoding="utf-8") as handle:
            self.assertEqual(json.load(handle)["outcome"], supervisor.FAILED)

    def test_a_PROVIDER_FAILURE_is_held_and_never_an_acceptance(self):
        """The provider's own non-zero turn, at the normal boundary: the
        workload publishes `provider-failed`, the stage cannot complete, and no
        verdict exists -- so the run is HELD rather than rounded up.
        """
        world = self.world_for()
        world.failing_script()
        _held, outcome = world.run_packet(dispositions=["accepted"])
        self.assertEqual(outcome["outcome"], supervisor.FAILED)
        self.assertEqual(outcome["state"], "held")
        self.assertIsNone(outcome["review_disposition"])
        self.assertIs(outcome["context_continuity"]["continued"], False)


class TheSupportedENTRYIsDriven(ConnectedEnding):
    """Review 2026-09-29T23-17-24Z's closure: from the supported preparation
    outputs through bind/check and the ACTUAL supervisor preparation entry."""

    def test_the_SUPPORTED_WORK_PREPARATION_performed_the_Authority_acts(self):
        """`prepare_work`'s real acts against the disposable Authority: the Work
        under the assignment contract, the three route handlers the stages need,
        the four receipt capabilities in the Work's own scope, and the canonical
        target. No Job is submitted here -- `baseline.survey` refuses a Job
        identity the store already records.
        """
        world = self.world_for()
        prepared = world.prepared_work
        # THIS PREPARATION'S OWN WORK, absent from the Authority until it created
        # it -- not the World's `W1`, which an earlier version adopted and then
        # called an exact replay.
        self.assertEqual(prepared["work_id"],
                         world.config["authority_uuid"][:8] + "-W236087")
        self.assertNotEqual(prepared["work_id"], world.work)
        self.assertIs(prepared["created"], True)
        self.assertEqual(sorted(prepared["route_handlers"]),
                         ["impl", "integration", "rview"])
        self.assertEqual(
            sorted(one["capability"] for one in prepared["granted"]),
            ["approve", "integrate", "review", "verify"])
        self.assertEqual(prepared["canonical_target"], world.base)
        self.assertTrue(prepared["scope"])
        # AND THE ACT IS BOUND TO ITS OPERANDS, which is what makes a changed
        # rerun a different act rather than a replay.
        self.assertEqual(
            prepared["operation_id"],
            trace.packets.preparation_identity(
                trace.packets.held_selections(
                    os.path.join(world.root, "selections.json")),
                prepared["work_id"]))

    def test_the_QUALIFIED_WORK_ID_comes_from_the_preparation_not_a_binding(self):
        """A FRESH installation binds no Job: the emitted configuration carries
        `job_bindings: []`, which is what `tools.bootstrap` really produces, and
        the identity comes from the supported preparation record.
        """
        import json

        world = self.world_for()
        installed = trace.packets.installed_layout(world.packet_root)
        with open(installed["configuration"], encoding="utf-8") as handle:
            self.assertEqual(json.load(handle)["job_bindings"], [])
        # And every stage the packet submitted names the prepared Work.
        with open(world.packet["submission"]["path"], encoding="utf-8") as handle:
            submitted = json.load(handle)
        for stage in submitted["jobs"][0]["stages"]:
            self.assertEqual(stage["work_id"], world.prepared_work["work_id"])

    def test_the_ACTUAL_SUPERVISOR_PREPARATION_ENTRY_composed_the_owner_acts(self):
        """`baseline.prepare` is the function `correction_supervisor.main`
        calls. Driving the four owner acts individually proved each works and NOT
        that this composition does, so the fixture drives the entry itself.
        """
        world = self.world_for()
        world.serving()
        held = world.prepared_owner_acts
        self.assertEqual(held["profile_digest"],
                         world.packet["context"]["profile_digest"])
        self.assertEqual(held["qualification_run"], world.packet["run_id"])
        self.assertEqual(held["storage_path"],
                         world.packet["context"]["storage_path"])
        self.assertEqual(held["workspace_storage"], world.storage)

    def test_CHECK_reproves_the_packet_after_the_preparation(self):
        """Step 4 of the emitted commands, run here: the real product validators
        over the packet the preparation produced.
        """
        world = self.world_for()
        reproved = trace.packets.held_packet(world.prepared["packet"])
        self.assertEqual(reproved["submission"]["work_id"],
                         world.prepared_work["work_id"])
        self.assertEqual(reproved["bounds"],
                         dict(trace.packets.BOUNDS))


class TheConnectedPathIsThePACKETS(ConnectedEnding):
    """What makes these four the PACKET's endings rather than the fixture's."""

    def test_the_consumed_documents_are_the_generated_ones(self):
        held, outcome = self.run_packet(dispositions=["accepted"])
        packet = self.world.packet
        # The submission the manager recorded is the packet's own.
        self.assertEqual(outcome["job_id"], packet["submission"]["job_id"])
        # The composition is the packet's, with both generated workers.
        self.assertEqual(
            sorted(one["worker_id"]
                   for one in self.world.configuration["workers"]),
            ["implementation-worker", "review-worker"])
        # And the run was bounded by the packet's own numbers.
        self.assertEqual(outcome["serving_seconds"]
                         + outcome["reserved_seconds"],
                         packet["bounds"]["total_seconds"])
        self.assertEqual(outcome["reserved_seconds"],
                         packet["bounds"]["cleanup_seconds"])
        del held


if __name__ == "__main__":                                   # pragma: no cover
    unittest.main()
