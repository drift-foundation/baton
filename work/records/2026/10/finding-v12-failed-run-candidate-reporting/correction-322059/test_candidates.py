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
TASK_ID = "failed-reporting-w321528-321530"


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


def ordinary_tests(**changed):
    """THE PRODUCER'S OWN SHAPE, from `claude_agent._ordinary_tests`.

    `task_id`, `task_digest`, `argv`, `status` -- an INTEGER OR `None` -- plus
    `base` and `head`. There is no `outcome` member anywhere in it, which is
    the schema the first reader invented and these cases now refuse to.
    """
    held = {"task_id": TASK_ID, "task_digest": "sha256:" + "9" * 64,
            "argv": ["python3", "harness.py"], "status": 0,
            "base": BASE, "head": HEAD}
    held.update(changed)
    return held


def sealed_output(*, claim=True, status="present", artifact=True, tests=None,
                  **changed):
    held = {"name": baseline.PROPOSAL_OUTPUT, "type": "git-proposal",
            "status": status, "content_manifest": None,
            "artifact": reference(**changed) if artifact else None,
            "result_metadata": {}}
    if claim:
        held["result_metadata"][baseline.CLAIM_NAMESPACE] = {
            "base": BASE, "head": HEAD, "transport": "bundle"}
    if tests is not None:
        # ON THE OUTPUT, beside the claim, because that is where the real
        # producer puts it -- not at manifest level, which is where the first
        # reader looked and found nothing.
        held["result_metadata"][baseline.ORDINARY_TESTS_NAMESPACE] = tests
    return held


def manifest(outputs=None):
    return {"outputs": [sealed_output()] if outputs is None else outputs,
            "result_metadata": {}}


class Collector(unittest.TestCase):
    """One attempt, one packet, and exact doubles at the manager boundary."""

    def setUp(self):
        # THE DECLARED BASE IS DOUBLED AT ITS OWN HELPER. `_declared_base`
        # opens the deployment's config file; what these cases are about is
        # what the collector does with the ANSWER, including when there is
        # none, so the answer is supplied and the file read is not re-tested
        # here -- `_proposals`' own cases already cover it.
        self.declared = BASE
        self.packet = {"deployment": {}, "run_id": TASK_ID}
        self.frozen = {"disposition": "unable",
                       "manifest_digest": "sha256:" + "d" * 64,
                       "artifacts": [indexed()]}
        self.manifest = manifest()
        self.assignment = {"authority_uuid": "0" * 32,
                           "work_id": "00000000-W1",
                           "participant": "baton.impl",
                           "principal": "principal:baton.impl",
                           "generation": 1,
                           "effective_scope": "scope:deployment"}
        # THE RETAINED LINE'S OWN ANSWER. Review 2026-10-18T08-39-00Z P1:
        # metadata agreement between the seal and the index is not custody, so
        # `_candidates` reads the commit object through `line_attribution`'s
        # supported boundary. This stands in for that read so a missing,
        # damaged or substituted retained candidate can be driven on purpose.
        self.custody = {
            "author": f"{baseline.COMMIT_NAME} <{baseline.COMMIT_EMAIL}>",
            "committer": f"{baseline.COMMIT_NAME} <{baseline.COMMIT_EMAIL}>",
            "parents": [BASE], "head": HEAD, "base": BASE}
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

        def inspect(_control, **named):
            """The retained line's own answer, so a missing, damaged or
            substituted candidate can be driven on purpose. `test_baseline`'s
            own cases exercise the real git reads behind it."""
            if isinstance(self.custody, Exception):
                raise self.custody
            return self.custody

        try:
            return baseline._candidates(object(), [ATTEMPT], self.packet,
                                        self.shortfalls, inspect=inspect)
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
        # REVIEW P2: `none` would claim a read nobody performed. This Job
        # admits no reviewer and this supervisor consults no exact-candidate
        # acceptance evidence, so the honest value is that nobody looked.
        self.assertEqual(held["acceptance"], baseline.ACCEPTANCE_UNOBSERVED)

    def test_a_SUCCESSFUL_turn_is_collected_by_the_same_path(self):
        self.frozen["disposition"] = "completed"
        held = self.one()
        self.assertEqual(held["state"], baseline.CANDIDATE_VALID)
        self.assertEqual(held["disposition"], "completed")
        self.assertEqual(self.shortfalls, [])

    def test_the_PRODUCERS_OWN_STATUS_is_interpreted_not_invented(self):
        """Review P2: the first reader looked at manifest-level metadata for an
        `outcome` key that exists nowhere in the producer. These drive the real
        shape -- the observation on the proposal OUTPUT, with an integer or
        `None` `status`."""
        for status, expected in (
                (0, baseline.VERIFICATION_PASSED),
                (1, baseline.VERIFICATION_FAILED),
                (137, baseline.VERIFICATION_FAILED),
                # NOT `not-run`: the producer emits None for a skipped
                # command, a timeout AND a failed start alike.
                (None, baseline.VERIFICATION_NO_STATUS)):
            with self.subTest(status=status):
                self.setUp()
                self.manifest = manifest(
                    outputs=[sealed_output(tests=ordinary_tests(
                        status=status))])
                self.assertEqual(self.one()["verification"], expected)

    def test_a_MISSING_or_MALFORMED_observation_is_unreported(self):
        for tests in (None, {}, {"status": "zero"}, {"outcome": "passed"}):
            with self.subTest(tests=tests):
                self.setUp()
                self.manifest = manifest(
                    outputs=[sealed_output(tests=tests)])
                self.assertEqual(self.one()["verification"],
                                 baseline.VERIFICATION_UNREPORTED)

    def test_an_observation_of_ANOTHER_CANDIDATE_is_not_this_ones(self):
        """An observation whose base/head are not this candidate's is an
        observation of something else."""
        for changed in ({"head": "f" * 40}, {"base": "e" * 40},
                        {"task_id": "some-other-task"}):
            with self.subTest(changed=changed):
                self.setUp()
                self.manifest = manifest(
                    outputs=[sealed_output(tests=ordinary_tests(**changed))])
                self.assertEqual(self.one()["verification"],
                                 baseline.VERIFICATION_UNREPORTED)


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


class RetainedCUSTODYIsReadNotInferred(Collector):
    """Review 2026-10-18T08-39-00Z P1, which is the finding that matters most.

    The first correction compared the sealed reference with the manager's
    indexed row and called agreement `valid`. Its own fixture named a locator
    that did not exist and got `valid` with no shortfall: two stored
    descriptions agreeing establishes that nobody disagrees, NOT that the bytes
    are there. So custody is now READ at the supported boundary, and these
    drive what happens when that read fails or disagrees.
    """

    def test_a_candidate_whose_LINE_DOES_NOT_ANSWER_is_not_valid(self):
        """Missing retained bytes. The metadata still agrees perfectly."""
        self.custody = ContractRefusal(
            "this manager holds no line writer for that attempt")
        held = self.one()
        self.assertEqual(held["state"], baseline.CANDIDATE_UNREADABLE)
        self.assertNotEqual(held["state"], baseline.CANDIDATE_VALID)
        self.assertIn("own line did not answer", held["why"])
        self.assertIn("UNREADABLE retained candidate", self.shortfalls[0])

    def test_an_OS_ERROR_reading_the_line_is_unreadable(self):
        self.custody = OSError("the retained workspace is gone")
        self.assertEqual(self.one()["state"], baseline.CANDIDATE_UNREADABLE)

    def test_USEFUL_EVIDENCE_SURVIVES_a_failed_custody_read(self):
        """An operator looking for the bytes needs the locator most when
        something is wrong, so it stays in the record."""
        self.custody = OSError("gone")
        held = self.one()
        self.assertEqual(held["locator"], LOCATOR)
        self.assertEqual(held["head"], HEAD)
        self.assertEqual(held["base"], BASE)
        self.assertEqual(held["content_digest"], DIGEST)
        self.assertIsNotNone(held["assignment"])

    def test_a_SUBSTITUTED_head_is_refused(self):
        """The line answers a different commit than the seal claims."""
        self.custody = dict(self.custody, head="f" * 40)
        held = self.one()
        self.assertEqual(held["state"], baseline.CANDIDATE_REFUSED)
        self.assertIn("answers head", held["why"])

    def test_a_DAMAGED_history_is_refused(self):
        """Parents that are not exactly the declared base: the adapter authors
        one commit per turn, so anything else is a history it did not write."""
        self.custody = dict(self.custody, parents=[BASE, "e" * 40])
        self.assertIn("parents", self.refused_why())

    def test_a_candidate_the_ADAPTER_DID_NOT_AUTHOR_is_refused(self):
        """W236087's live failure: the provider committed its own work."""
        self.custody = dict(self.custody,
                            author="Somebody Else <nobody@example.invalid>",
                            committer="Somebody Else <nobody@example.invalid>")
        self.assertIn("attributed to", self.refused_why())

    def test_a_split_AUTHOR_and_COMMITTER_is_refused(self):
        self.custody = dict(self.custody,
                            committer="Other <other@example.invalid>")
        self.assertIn("committed by", self.refused_why())

    def refused_why(self):
        held = self.one()
        self.assertEqual(held["state"], baseline.CANDIDATE_REFUSED, held)
        self.assertTrue(self.shortfalls)
        return held["why"]

    def test_a_valid_candidate_carries_its_WHOLE_attribution(self):
        """Review P1: the record named only the generation, so it could not say
        which authority, Work or participant the bytes belong to."""
        held = self.one()
        self.assertEqual(held["state"], baseline.CANDIDATE_VALID)
        self.assertEqual(held["assignment"]["authority_uuid"], "0" * 32)
        self.assertEqual(held["assignment"]["work_id"], "00000000-W1")
        self.assertEqual(held["assignment"]["participant"], "baton.impl")
        self.assertEqual(held["assignment"]["generation"], 1)
        self.assertEqual(held["attribution"]["head"], HEAD)


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
                         baseline.ACCEPTANCE_UNOBSERVED)


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
