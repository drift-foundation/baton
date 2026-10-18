"""W321528 — a failed turn's RETAINED candidate is reported, or honestly refused.

The defect this closes, in one sentence: the selected live run of this Work
timed out at 900s with a real three-file candidate retained on its private
line, and the report said the run retained nothing at all -- because the only
question anybody asked was "what did it PUBLISH", and a turn that did not
complete publishes nothing by contract.

So these drive `_candidates` at the boundary the review named, over the two
records of one artifact that actually exist: the worker's SEALED result manifest
and the manager's OWN INDEX of what it received. The four states are proved to
be four different answers -- `valid`, `absent`, `refused`, `unreadable` -- and
the last is proved NOT to be reported as absence, which is the conflation that
produced the original false report.

Nothing here runs a provider, an engine or a container. The manager boundary is
supplied by exact doubles so a single custody disagreement can be introduced on
purpose; what is NOT doubled is the collector, which is the code under test.
"""

import os
import sys
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import baseline                                              # noqa: E402

ATTEMPT = "attempt-" + "a" * 8
BASE = "3dcf6dc4bcee97e932d17c93ac13c5811b3af188"
HEAD = "2c89d3aa1c3ccf190a47417f3147593b694948dd"
DIGEST = "sha256:" + "c" * 64
LOCATOR = "file:/retained/proposal.bundle"


class ContractRefusal(Exception):
    """Stands in for the distribution's refusal at the doubled boundary."""


def reference(**changed):
    held = {"artifact_id": "artifact-" + "b" * 8,
            "media_type": "application/x-git-bundle", "bytes": 11067,
            "content_digest": DIGEST, "locator": LOCATOR}
    held.update(changed)
    return held


def indexed(**changed):
    held = dict(reference(), output_name=baseline.PROPOSAL_OUTPUT)
    held.update(changed)
    return held


def sealed_output(*, claim=True, status="present", artifact=True, **changed):
    held = {"name": baseline.PROPOSAL_OUTPUT, "type": "git-proposal",
            "status": status, "content_manifest": None,
            "artifact": reference(**changed) if artifact else None,
            "result_metadata": {}}
    if claim:
        held["result_metadata"] = {baseline.CLAIM_NAMESPACE: {
            "base": BASE, "head": HEAD, "transport": "bundle"}}
    return held


def manifest(outputs=None, *, tests=None):
    held = {"outputs": [sealed_output()] if outputs is None else outputs,
            "result_metadata": {}}
    if tests is not None:
        held["result_metadata"] = {baseline.ORDINARY_TESTS_NAMESPACE: tests}
    return held


class Collector(unittest.TestCase):
    """One attempt, one packet, and exact doubles at the manager boundary."""

    def setUp(self):
        # THE DECLARED BASE IS DOUBLED AT ITS OWN HELPER. `_declared_base`
        # opens the deployment's config file; what these cases are about is
        # what the collector does with the ANSWER, including when there is
        # none, so the answer is supplied and the file read is not re-tested
        # here -- `_proposals`' own cases already cover it.
        self.declared = BASE
        self.packet = {"deployment": {}}
        self.frozen = {"disposition": "unable",
                       "manifest_digest": "sha256:" + "d" * 64,
                       "artifacts": [indexed()]}
        self.manifest = manifest()
        self.assignment = {"generation": 1}
        self.shortfalls = []

    def collected(self):
        """`_candidates` over this case's doubles, and nothing else doubled.

        The collector imports its manager helpers INSIDE the function, so the
        seam is `sys.modules` and the code under test is reached unmodified.
        """
        manager = types.ModuleType("manager_double")

        def frozen_output_of(_control, _attempt):
            if isinstance(self.frozen, Exception):
                raise self.frozen
            return self.frozen

        def load_manifest(_control, _digest, definition):
            assert definition == "resultManifest", definition
            if isinstance(self.manifest, Exception):
                raise self.manifest
            return self.manifest

        outer = self

        class attempts:
            @staticmethod
            def assignment_of(_control, _attempt):
                if isinstance(outer.assignment, Exception):
                    raise outer.assignment
                return outer.assignment

        manager.frozen_output_of = frozen_output_of
        manager.load_manifest = load_manifest
        manager.attempts = attempts

        def declared_base(_packet):
            if self.declared is None:
                raise baseline.SupervisorRefusal(
                    "the deployment declares no canonical target")
            return self.declared

        held_base = baseline._declared_base
        baseline._declared_base = declared_base
        contracts = types.ModuleType("contracts_double")
        contracts.ContractRefusal = ContractRefusal
        held = dict(sys.modules)
        sys.modules["baton_v12.worker_manager"] = manager
        sys.modules["baton_v12.contracts"] = contracts
        try:
            return baseline._candidates(object(), [ATTEMPT], self.packet,
                                        self.shortfalls)
        finally:
            baseline._declared_base = held_base
            sys.modules.clear()
            sys.modules.update(held)

    def one(self):
        found = self.collected()
        self.assertEqual(len(found), 1, found)
        self.assertEqual(found[0]["attempt_id"], ATTEMPT)
        return found[0]


class AFailedTurnWithARetainedCandidate(Collector):
    """THE CASE THE LIVE RUN GOT WRONG."""

    def test_a_FAILED_turn_still_reports_its_valid_retained_candidate(self):
        held = self.one()
        self.assertEqual(held["state"], baseline.CANDIDATE_VALID)
        self.assertEqual(held["disposition"], "unable")
        self.assertEqual(held["head"], HEAD)
        self.assertEqual(held["base"], BASE)
        self.assertEqual(held["locator"], LOCATOR)
        self.assertEqual(held["content_digest"], DIGEST)
        self.assertEqual(held["transport"], "bundle")
        self.assertIsNone(held["why"])

    def test_a_valid_retained_candidate_is_NOT_a_shortfall(self):
        """Reporting the useful fact as a deficiency would be the same mistake
        in the other direction."""
        self.one()
        self.assertEqual(self.shortfalls, [])

    def test_it_is_NOT_a_verification_and_NOT_an_acceptance(self):
        """A valid candidate is "these bytes are retained and their custody
        holds" and nothing about whether they are correct or wanted."""
        held = self.one()
        self.assertEqual(held["verification"],
                         baseline.VERIFICATION_UNREPORTED)
        self.assertEqual(held["acceptance"], baseline.ACCEPTANCE_NONE)

    def test_a_SUCCESSFUL_turn_is_collected_by_the_same_path(self):
        self.frozen["disposition"] = "completed"
        held = self.one()
        self.assertEqual(held["state"], baseline.CANDIDATE_VALID)
        self.assertEqual(held["disposition"], "completed")
        self.assertEqual(self.shortfalls, [])

    def test_the_turns_own_verification_outcome_is_reported_not_judged(self):
        for outcome, expected in (("passed", baseline.VERIFICATION_PASSED),
                                  ("failed", baseline.VERIFICATION_FAILED),
                                  (None, baseline.VERIFICATION_NOT_RUN),
                                  ("nonsense",
                                   baseline.VERIFICATION_UNREPORTED)):
            with self.subTest(outcome=outcome):
                self.manifest = manifest(tests={"outcome": outcome})
                self.assertEqual(self.one()["verification"], expected)


class AFailedTurnWithoutOne(Collector):

    def test_a_turn_that_FROZE_NOTHING_is_absent_and_says_so(self):
        """Absence is an ANSWER and the ordinary shape of a failure."""
        self.frozen = None
        held = self.one()
        self.assertEqual(held["state"], baseline.CANDIDATE_ABSENT)
        self.assertEqual(held["acceptance"], baseline.ACCEPTANCE_NO_CANDIDATE)
        self.assertEqual(held["verification"], baseline.VERIFICATION_NOT_RUN)
        self.assertIn("froze no result", held["why"])
        self.assertEqual(self.shortfalls, [])

    def test_a_turn_that_declared_no_candidate_is_absent(self):
        self.manifest = manifest(outputs=[])
        self.frozen["artifacts"] = []
        held = self.one()
        self.assertEqual(held["state"], baseline.CANDIDATE_ABSENT)
        self.assertEqual(held["acceptance"], baseline.ACCEPTANCE_NO_CANDIDATE)
        self.assertEqual(self.shortfalls, [])

    def test_a_MISSING_OPTIONAL_output_with_no_indexed_row_is_absent(self):
        self.manifest = manifest(
            outputs=[sealed_output(status="missing-optional", artifact=False)])
        self.frozen["artifacts"] = []
        self.assertEqual(self.one()["state"], baseline.CANDIDATE_ABSENT)


class InvalidCustodyIsRefusedAndNeverCounted(Collector):
    """Evidence that EXISTS and did not survive a check is a much louder fact
    than absence, and must not be quietly dropped either way."""

    def refused(self):
        held = self.one()
        self.assertEqual(held["state"], baseline.CANDIDATE_REFUSED, held)
        self.assertTrue(self.shortfalls)
        self.assertIn("REFUSED retained candidate", self.shortfalls[0])
        return held

    def test_a_DIGEST_disagreement_between_the_two_records_is_refused(self):
        """The worker's seal and the manager's index are two records of one
        artifact; disagreeing means nobody knows which bytes it is."""
        self.frozen["artifacts"] = [
            indexed(content_digest="sha256:" + "e" * 64)]
        self.assertIn("content_digest", self.refused()["why"])

    def test_a_SIZE_disagreement_is_refused(self):
        self.frozen["artifacts"] = [indexed(bytes=99)]
        self.assertIn("bytes", self.refused()["why"])

    def test_an_ARTIFACT_ID_disagreement_is_refused(self):
        self.frozen["artifacts"] = [indexed(artifact_id="artifact-" + "f" * 8)]
        self.assertIn("artifact_id", self.refused()["why"])

    def test_a_LOCATOR_disagreement_is_refused(self):
        self.frozen["artifacts"] = [indexed(locator="file:/elsewhere.bundle")]
        self.assertIn("locator", self.refused()["why"])

    def test_a_SEALED_candidate_the_manager_never_indexed_is_refused(self):
        """Not absence: the worker's account declares bytes that are not in
        the manager's custody."""
        self.frozen["artifacts"] = []
        self.assertIn("not in its custody", self.refused()["why"])

    def test_an_INDEXED_artifact_the_seal_omits_is_refused(self):
        """And the other direction, which is louder still."""
        self.manifest = manifest(outputs=[])
        self.assertIn("disagree about whether a candidate exists",
                      self.refused()["why"])

    def test_a_candidate_on_ANOTHER_BASE_is_refused(self):
        self.manifest["outputs"][0]["result_metadata"][
            baseline.CLAIM_NAMESPACE]["base"] = "0" * 40
        self.assertIn("canonical target", self.refused()["why"])

    def test_a_candidate_whose_HEAD_IS_ITS_BASE_is_refused(self):
        self.manifest["outputs"][0]["result_metadata"][
            baseline.CLAIM_NAMESPACE]["head"] = BASE
        self.assertIn("holds no change", self.refused()["why"])

    def test_an_UNSTATED_claim_is_refused_rather_than_guessed(self):
        for claim in (None, {}, {"base": BASE}, {"base": BASE, "head": HEAD},
                      {"base": BASE, "head": HEAD, "transport": ""}):
            with self.subTest(claim=claim):
                self.setUp()
                held = sealed_output(claim=False)
                if claim is not None:
                    held["result_metadata"] = {
                        baseline.CLAIM_NAMESPACE: claim}
                self.manifest = manifest(outputs=[held])
                self.assertIn("no readable", self.refused()["why"])

    def test_an_UNREADABLE_declared_base_refuses_rather_than_passing(self):
        self.declared = None
        self.assertIn("declared base is unreadable", self.refused()["why"])


class AnUnreadableReadIsNeverReportedAsAbsence(Collector):
    """The conflation that produced the original false report."""

    def unreadable(self):
        held = self.one()
        self.assertEqual(held["state"], baseline.CANDIDATE_UNREADABLE, held)
        self.assertNotEqual(held["state"], baseline.CANDIDATE_ABSENT)
        self.assertTrue(self.shortfalls)
        self.assertIn("UNREADABLE retained candidate", self.shortfalls[0])
        return held

    def test_a_frozen_result_that_does_not_read_is_unreadable(self):
        self.frozen = ContractRefusal("the output table did not answer")
        said = self.unreadable()
        self.assertIn("did not read", said["why"])
        self.assertIn("not evidence", self.shortfalls[0])

    def test_a_manifest_that_does_not_read_is_unreadable(self):
        self.manifest = ContractRefusal(
            "the manifest digest did not recompute")
        self.assertIn("did not read", self.unreadable()["why"])

    def test_a_manifest_this_store_DOES_NOT_HOLD_is_unreadable(self):
        self.manifest = None
        self.assertIn("does not hold", self.unreadable()["why"])

    def test_an_unreadable_ASSIGNMENT_is_unreadable_not_valid(self):
        """The candidate cannot be bound to the attempt that produced it."""
        self.assignment = KeyError("generation")
        self.assertIn("assignment did not read", self.unreadable()["why"])

    def test_an_unreadable_candidate_carries_no_acceptance_claim(self):
        self.frozen = TypeError("row shape")
        self.assertEqual(self.unreadable()["acceptance"],
                         baseline.ACCEPTANCE_UNREADABLE)


class TheAbsenceMessagesNoLongerContradictTheRecord(unittest.TestCase):
    """The two sentences the review found false, corrected in place."""

    def test_the_noncompleted_message_points_at_the_candidate_question(self):
        import inspect

        said = inspect.getsource(baseline._proposals)
        self.assertIn("`candidates` answers it", said)

    def test_the_no_proposal_message_no_longer_claims_nothing_was_retained(
            self):
        import inspect

        said = inspect.getsource(baseline._proposals)
        self.assertNotIn("retained no proposal at all", said)
        self.assertIn("published no proposal at all", said)
        # Split across two source lines; both halves are asserted so the
        # sentence cannot lose the distinction it exists to draw.
        self.assertIn("a retained candidate is not a", said)
        self.assertIn("published proposal, a verification or an acceptance",
                      said)


if __name__ == "__main__":
    unittest.main()
