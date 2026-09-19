"""W197661 — the verifier's own predicates, driven by fixtures.

WHY THIS SUITE EXISTS. Review 2026-09-18T05-14-53Z found instance-200254's
verifier to be a BROKEN INSTRUMENT rather than a failing one: it judged an
unobserved projection whose own document said `canonical=false`, and three of
its final predicates named members no contract has. Nothing caught that,
because nothing ever drove the verifier over a shape it should accept and
shapes it must refuse.

So the predicates are pure functions over documents now, and these cases are
the positive and negative fixtures review 2026-09-18T06-19-15Z asks for:
"Contract-derived verifier and negative cases need not wait for successful live
fixture." A verifier that accepts a successful shape and refuses each broken
one is an instrument somebody has calibrated.

NO DEPLOYMENT, NO ENGINE, NO AUTHORITY. Every case here is a dictionary.
"""

import copy
import json
import os
import pathlib
import sys
import types
import unittest
from unittest import mock

REPO = "/home/sl/src/baton"
# THIS EPISODE'S VERIFIER. instance-200564's copy and its five retained
# verification-*.json are PRESERVED untouched; what this suite exercises is the
# one carrying review201732's corrections -- the terminal read through
# `StageObservation.observe_integration`, the owned base->result->target chain,
# and the `--observe` comparison.
INSTANCE = os.path.join(
    REPO, "work/records/2026/09/finding-v12-worker-launch-version-mismatch",
    "instance-201492")


def _verifier():
    if INSTANCE not in sys.path:
        sys.path.insert(0, INSTANCE)
    import verify_lifecycle

    return verify_lifecycle


class VerifierCase(unittest.TestCase):
    """One SUCCESSFUL shape, and every case bends exactly one thing in it."""

    def setUp(self):
        self.verify = _verifier()
        with open(os.path.join(INSTANCE, "CAPTURED-records.json")) as handle:
            self.captured = {name: held for name, held in
                             json.load(handle).items()
                             if not name.startswith("_")}
        # THE TERMINAL AND THE OWNED PROPOSAL, AS THEIR OWNERS ANSWERED THEM.
        # Review201732 [R1] named `StageObservation.observe_integration` as the
        # existing read-only owner; `CAPTURED-terminal.json` is what it and
        # `Authority.open_readonly` actually returned for the retained run, so
        # these member names are the contracts' own rather than mine.
        with open(os.path.join(INSTANCE, "CAPTURED-terminal.json")) as handle:
            self.owner_shaped = json.load(handle)
        self.implementation = "attempt-" + "1" * 64
        self.review = "attempt-" + "2" * 64
        self.integration = "attempt-" + "3" * 64
        self.offer = "offer-" + "3" * 64
        self.candidate = "4" * 40
        self.proposal_id = "integration-driver.proposal:" + "5" * 64
        self.receipt_id = "integration-driver.integration-receipt:" + "6" * 64
        self.result_id = "result-" + self.implementation
        self.sealed = {"image": "sha256:" + "a" * 64,
                       "image_inputs": {"worker/x.py": "sha256:" + "b" * 64},
                       "built_runtime": "sha256:" + "c" * 64,
                       "installed_runtime": "sha256:" + "c" * 64,
                       "configuration": "sha256:" + "d" * 64}
        self.observed = {
            "status": {
                "canonical": True,
                "jobs": [{
                    "job_id": self.verify.JOB,
                    "submission_id": self.verify.SUBMISSION,
                    "terminal_policy": "report-and-hold",
                    "stages": [
                        {"kind": "implementation", "state": "completed",
                         "attempt_id": self.implementation},
                        {"kind": "review", "state": "completed",
                         "attempt_id": self.review},
                        # THE STAGE'S OWN EPISODE, left as the projection
                        # answers it. `terminal()` does NOT overwrite the
                        # captured observation's episode, so the two operands
                        # judge compares reach the fixture by different routes
                        # -- review201853 [R1]: "Do not copy a constant into
                        # both observed operands to satisfy these checks."
                        {"kind": "integration", "state": "completed",
                         "episode": 1,
                         "attempt_id": self.integration,
                         "offer_id": self.offer}]}]},
            "expected": copy.deepcopy(self.sealed),
            "measured": copy.deepcopy(self.sealed),
            # THE TARGET HAS ADVANCED, because a completed import advances
            # it. Review201732 [R3]: base equality is wrong after completion.
            "authority": {"policy_generation": 23,
                          "canonical_target": self.candidate,
                          "work_present": True},
            "pin": {"configured_pin": 23, "authority_generation": 23,
                    "equal": True},
            "line": {"candidate": self.verify.CANDIDATE_BYTES,
                     "custody": self.implementation},
            "records": self.records(),
            "owned": self.owned(),
            "observation_gap": {"with_observe": "completed",
                                "without_observe": "starting",
                                "explains_the_gap": True},
            # THE PROVENANCE CLASSIFICATION. The image digest has an
            # independent build-time record; the inputs were measured at seal
            # time, which is the post-build seal limitation stated rather than
            # papered over.
            "provenance": {
                "seal": {"rewritten": False},
                "image_identity": {"corroborated": True,
                                   "build_record": self.sealed["image"],
                                   "sealed": self.sealed["image"]},
                "image_inputs": {"corroborated": False,
                                 "why_not": "measured at seal time"},
            },
        }

    def records(self):
        """The four records, SHAPED AS AN OWNER REALLY SHAPES THEM.

        Review 2026-09-18T06-41-32Z [R4]: hand-written dictionaries "cannot
        establish compatibility with actual owner APIs". `CAPTURED-records.json`
        holds what `read_records` actually read out of the retained episode
        through `review_cycles.integration_checkpoint`, `verdict_of`,
        `review_of`, `frozen_output_of` and `load_manifest` -- so the member
        names here are the owners' own, and a reader that drifts from them
        fails `test_the_CAPTURED_records_still_match_the_adapter`.

        The captured terminal is `unread`, because that record's owner is not
        a read-only path; the positive shape substitutes the held state so the
        successful case exists to be accepted.
        """
        import copy

        held = copy.deepcopy(self.captured)
        held["verdict"]["attempt_id"] = self.review
        held["result"]["attempt_id"] = self.implementation
        held["result"]["assignment_ref"] = {
            "work_ref": {"work_id": self.verify.WORK}}
        # THE SUCCESSFUL TERMINAL IS `completed`, from
        # stage_execution.managed_account's own vocabulary: `held` is a HELD
        # queue entry or an unanswered ending, and review 2026-09-18T07-01-24Z
        # caught me reading the Job's terminal POLICY name as an integration
        # state.
        held["result"]["result_id"] = self.result_id
        held["terminal"] = self.terminal()
        return held

    def terminal(self):
        """The integration observation, RESHAPED FROM THE REAL ONE.

        The captured document is the retained run's; its identities are that
        run's, so they are substituted for this fixture's. Every MEMBER NAME is
        the contract's, which is the point -- `judge` reads
        `baton.v12.integration-stage-observation/1` and a reader that invented
        its own spelling would pass a hand-written shape and fail here.
        """
        held = copy.deepcopy(self.owner_shaped["terminal"])
        held["stage_id"] = f"{self.verify.JOB}/integration"
        held["attempt_id"] = self.integration
        held["offer_id"] = self.offer
        held["assignment"]["work_ref"] = {
            "authority_uuid": self.verify.AUTHORITY,
            "work_id": self.verify.WORK}
        held["completion"]["proposal_id"] = self.proposal_id
        held["completion"]["source_proposal_id"] = self.proposal_id
        held["completion"]["integration_receipt_id"] = self.receipt_id
        # THE OPENER REPORT, as read_terminal attaches it.
        held["_opener"] = {
            "opener": "baton_v12.job_manager.JobStore.open_readonly",
            "opener_is_read_only": True,
            "read_only_opener_available": True,
            "refusals_are_the_owners": True,
            "what_it_refuses": ["an empty store, rather than initializing one"],
            "data_unchanged": True,
            "only_sqlite_sidecars": True,
            "sidecars_unchanged": True,
            "sidecars_created": []}
        return held

    def owned(self):
        """The proposal and receipt, from the same capture."""
        held = copy.deepcopy(self.owner_shaped["owned"])
        held["proposal_id"] = self.proposal_id
        held["proposal"]["proposal_id"] = self.proposal_id
        held["proposal"]["target"] = self.verify.TARGET_BASE
        held["proposal"]["candidate_digest"] = self.candidate
        held["proposal"]["result_id"] = self.result_id
        held["proposal"]["assignment_ref"] = {
            "work_ref": {"authority_uuid": self.verify.AUTHORITY,
                         "work_id": self.verify.WORK}}
        held["receipt"]["receipt_id"] = self.receipt_id
        held["receipt"]["proposal_id"] = self.proposal_id
        held["receipt"]["disposition"] = "integrated"
        held["receipt"]["candidate_digest"] = self.candidate
        held["receipt"]["target"] = self.verify.TARGET_BASE
        held["receipt"]["decision"] = {"policy_generation": 23}
        return held

    def judged(self, **changed):
        held = copy.deepcopy(self.observed)
        held.update(changed)
        return self.verify.judge(held)

    def refuses(self, path, value, expected):
        """Bend ONE member, and name the check that must fail for it."""
        checks = self.bent(path, value)
        self.assertIn(expected, checks.failed,
                      f"bending {path} to {value!r} did not fail "
                      f"{expected!r}; failures were {checks.failed}")

    def bent(self, path, value):
        """One member of the successful shape, changed, and nothing else."""
        held = copy.deepcopy(self.observed)
        where = held
        for step in path[:-1]:
            where = where[step]
        where[path[-1]] = value
        return self.verify.judge(held)


class TheSUCCESSFULShapeIsACCEPTED(VerifierCase):
    """The positive fixture, and it is the one a verifier can silently lose:
    predicates that can never pass fail this, which is how review200453's three
    invented members would have been caught."""

    def test_a_complete_lifecycle_passes_EVERY_check(self):
        checks = self.judged()
        self.assertEqual(checks.failed, [])

    def test_it_asserts_a_MEANINGFUL_number_of_things(self):
        """A verifier that accepts everything by checking almost nothing is the
        other way to pass this suite."""
        self.assertGreaterEqual(len(self.judged().held), 20)


class EveryBROKENShapeIsREFUSED(VerifierCase):
    """One case per way the run can be wrong, and each bends ONE member."""

    # -- the defect this verifier exists to not repeat -----------------------

    def test_an_UNOBSERVED_projection_is_REFUSED(self):
        """review200453 R1: the old verifier judged exactly this document and
        never looked at the flag it carries."""
        self.refuses(["status", "canonical"], False,
                     "the status projection is CANONICAL")
        self.refuses(["status", "canonical"], None,
                     "the status projection is CANONICAL")

    def test_an_UNREACHED_stage_is_REFUSED_not_summarized(self):
        for state in ("claimed", "answering", "exceptional", "queued"):
            with self.subTest(state=state):
                held = copy.deepcopy(self.observed)
                held["status"]["jobs"][0]["stages"][2]["state"] = state
                self.assertIn("the integration stage COMPLETED",
                              self.verify.judge(held).failed)

    # -- the records, which replace three members no contract has ------------

    def test_a_verdict_that_is_not_ACCEPTED_is_refused(self):
        self.refuses(["records", "verdict"], {"disposition": "rejected"},
                     "a review verdict was ACCEPTED")

    def test_a_verdict_about_ANOTHER_ATTEMPT_is_refused(self):
        """An accepted verdict is not evidence unless it is about this
        episode's review attempt."""
        self.refuses(["records", "verdict"],
                     {"disposition": "accepted",
                      "attempt_id": "attempt-" + "9" * 64},
                     "the accepted verdict names this episode's review "
                     "attempt")

    def test_a_MISSING_checkpoint_is_refused(self):
        self.refuses(["records", "checkpoint"], {},
                     "an integration CHECKPOINT was accepted")

    def test_a_checkpoint_on_ANOTHER_BASE_is_refused(self):
        self.refuses(["records", "checkpoint"],
                     {"checkpoint_id": "checkpoint-1",
                      "evidence": {"base": "0" * 40}},
                     "the checkpoint records the declared base")

    def test_a_result_that_is_not_completed_is_refused(self):
        self.refuses(["records", "result"], {"disposition": "unable"},
                     "the producer's frozen RESULT is completed")

    def test_a_result_naming_ANOTHER_WORK_is_refused(self):
        self.refuses(["records", "result"],
                     {"disposition": "completed",
                      "assignment_ref": {"work_ref": {"work_id": "0000-W9"}}},
                     "the frozen result names this Work")

    def test_a_terminal_that_is_not_COMPLETED_is_refused(self):
        self.refuses(["records", "terminal"], {"state": "open"},
                     "the integration account reached its COMPLETED state")

    def test_a_HELD_account_is_NOT_a_successful_terminal(self):
        """Review 2026-09-18T07-01-24Z: `managed_account` writes `held` for a
        held queue entry or an ending that was not `answered`. I read that
        spelling as proof of report-and-hold, which is the opposite of what it
        says."""
        checks = self.bent(["records", "terminal"], {"state": "held"})
        self.assertIn("the integration account reached its COMPLETED state",
                      checks.failed)
        self.assertIn("and `held` is not mistaken for that", checks.failed)

    def test_an_ANSWERED_account_is_not_completed_either(self):
        """Imported and settled, but the integration receipt is what finishes
        it."""
        self.refuses(["records", "terminal"], {"state": "answered"},
                     "the integration account reached its COMPLETED state")

    def test_an_UNREAD_record_set_is_refused_rather_than_skipped(self):
        """What the shell could not read must FAIL. The live shell answers
        exactly this while the integrator is unimplemented."""
        checks = self.judged(records={"unread": "no accepted verdict yet"})
        for what in ("a review verdict was ACCEPTED",
                     "an integration CHECKPOINT was accepted",
                     "the producer's frozen RESULT is completed",
                     "the integration account reached its COMPLETED "
                     "state"):
            self.assertIn(what, checks.failed)

    # -- the candidate and its custody ---------------------------------------

    def test_the_WRONG_candidate_bytes_are_refused(self):
        self.refuses(["line", "candidate"], "something else\\n",
                     "the candidate file carries exactly the declared bytes")

    def test_custody_holding_ANOTHER_ATTEMPT_is_refused(self):
        """review200453 R3: the old verifier counted one attempt and never
        compared its identity, so ANY one attempt satisfied it."""
        self.refuses(["line", "custody"], "attempt-" + "8" * 64,
                     "custody holds THIS implementation attempt")

    def test_custody_holding_MORE_THAN_ONE_attempt_is_refused(self):
        self.refuses(["line", "custody"], None,
                     "custody holds THIS implementation attempt")

    # -- the pin, now answering READINESS rather than gating completion ------

    def refuses_readiness(self, path, value, expected):
        checks = self.bent(path, value)
        self.assertIn(expected, checks.readiness_failed,
                      f"bending {path} to {value!r} did not fail readiness "
                      f"{expected!r}; readiness failures were "
                      f"{checks.readiness_failed}")

    def test_a_WRONG_PREDICTION_of_the_policy_pin_is_REPORTED(self):
        """Review 2026-09-18T06-19-15Z asked for a wrong prediction to be
        covered "without weakening the actual approval pin", and it still is --
        the comparison runs and its failure is reported. Review202028 moved
        WHICH verdict it belongs to: a pin that no longer matches bears on
        FUTURE authorization, not on whether the retained run completed."""
        self.refuses_readiness(
            ["pin"],
            {"configured_pin": 23, "authority_generation": 30, "equal": False},
            "the deployment could authorize a NEW action")

    def test_a_pin_check_that_was_NOT_RUN_is_reported(self):
        """An unrun comparison is not a passing one."""
        self.refuses_readiness(["pin"], {},
                               "the deployment could authorize a NEW action")

    # -- provenance ----------------------------------------------------------

    def test_an_UNSEALED_expectation_is_refused(self):
        checks = self.judged(expected=None)
        self.assertIn("an immutable expected manifest is SEALED", checks.failed)

    def test_an_IMAGE_that_is_not_the_sealed_one_is_refused(self):
        held = copy.deepcopy(self.observed)
        held["measured"]["image"] = "sha256:" + "f" * 64
        self.assertIn("the image matches the sealed expectation",
                      self.verify.judge(held).failed)

    def test_a_COPY_INPUT_that_moved_after_the_seal_is_refused(self):
        held = copy.deepcopy(self.observed)
        held["measured"]["image_inputs"]["worker/x.py"] = "sha256:" + "e" * 64
        self.assertIn("the image_inputs matches the sealed expectation",
                      self.verify.judge(held).failed)

    def test_an_INSTALLED_runtime_that_is_not_the_built_one_is_refused(self):
        held = copy.deepcopy(self.observed)
        held["measured"]["installed_runtime"] = "sha256:" + "0" * 64
        self.assertIn("the installed_runtime matches the sealed expectation",
                      self.verify.judge(held).failed)

    def test_a_CONFIGURATION_that_changed_after_the_seal_is_refused(self):
        held = copy.deepcopy(self.observed)
        held["measured"]["configuration"] = "sha256:" + "9" * 64
        self.assertIn("the configuration matches the sealed expectation",
                      self.verify.judge(held).failed)

    # -- the Authority --------------------------------------------------------

    def test_a_canonical_target_THIS_PROPOSAL_DID_NOT_PRODUCE_is_refused(self):
        """Review201732 [R3] replaced the old base-equality negative, which
        asserted the wrong thing: a completed import ADVANCES the target, so a
        target that is not the declared base is the SUCCESSFUL case. What must
        be refused is a target no owned proposal produced."""
        self.refuses(["authority", "canonical_target"], "9" * 40,
                     "the canonical target IS the revision this proposal "
                     "produced")

    def test_a_MISSING_Work_is_refused(self):
        self.refuses(["authority", "work_present"], False,
                     "the Job's Work exists on this Authority")

    # -- the Job itself -------------------------------------------------------

    def test_ANOTHER_submission_is_refused(self):
        held = copy.deepcopy(self.observed)
        held["status"]["jobs"][0]["submission_id"] = "w197661-lifecycle-200254"
        self.assertIn("it is the submission this episode recorded",
                      self.verify.judge(held).failed)

    def test_a_DIFFERENT_terminal_policy_is_refused(self):
        held = copy.deepcopy(self.observed)
        held["status"]["jobs"][0]["terminal_policy"] = "close"
        self.assertIn("its terminal policy is report-and-hold",
                      self.verify.judge(held).failed)

    def test_an_ABSENT_Job_is_refused(self):
        held = copy.deepcopy(self.observed)
        held["status"]["jobs"] = []
        self.assertIn("the projection names this Job",
                      self.verify.judge(held).failed)

    def test_an_EMPTY_observation_fails_rather_than_passing_vacuously(self):
        """The shape a verifier must never accept: nothing read at all."""
        checks = self.verify.judge({})
        self.assertGreaterEqual(len(checks.failed), 15)


class TheMANIFESTBindsWhatTheOldOneSKIPPED(unittest.TestCase):
    """review200453 R3: `tree_digest` skipped every symlink and every path
    containing `__pycache__`, so a link repointed or a cached module replaced
    left the digest unchanged."""

    def setUp(self):
        import shutil
        import tempfile

        self.verify = _verifier()
        self.root = tempfile.mkdtemp(prefix="w197661-manifest-")
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_a_SYMLINK_is_bound_by_its_TARGET(self):
        os.symlink("/somewhere", os.path.join(self.root, "pointer"))
        held = self.verify.tree_manifest(self.root)
        self.assertEqual(held["pointer"], "link:/somewhere")

    def test_REPOINTING_a_link_changes_the_manifest(self):
        os.symlink("/somewhere", os.path.join(self.root, "pointer"))
        before = self.verify.manifest_digest(
            self.verify.tree_manifest(self.root))
        os.unlink(os.path.join(self.root, "pointer"))
        os.symlink("/elsewhere", os.path.join(self.root, "pointer"))
        self.assertNotEqual(
            before,
            self.verify.manifest_digest(self.verify.tree_manifest(self.root)))

    def test_a_CACHED_module_is_bound_too(self):
        cache = os.path.join(self.root, "__pycache__")
        os.makedirs(cache)
        with open(os.path.join(cache, "x.cpython-313.pyc"), "wb") as handle:
            handle.write(b"the old one skipped this entirely")
        held = self.verify.tree_manifest(self.root)
        self.assertIn("__pycache__/x.cpython-313.pyc", held)


class MISSINGRequiredEvidenceCanNeverPASS(VerifierCase):
    """Review 2026-09-18T06-41-32Z [R1], and it was the worst kind of defect:
    the verifier ACCEPTED the absence of the evidence it exists to check.

    Replacing `expected` with an unrelated document and `measured` with an
    empty one made all five provenance comparisons `None == None`; removing
    every stage `attempt_id`, the verdict's attempt and the line's custody
    made those compare equal too. Both returned zero failed checks. A check
    that passes when its subject is missing is not a check.
    """

    def test_SIMULTANEOUS_ABSENCE_of_both_sides_is_REFUSED(self):
        """The reviewer's first probe, exactly."""
        checks = self.judged(expected={"unrelated": True}, measured={})
        for name in ("image", "image_inputs", "built_runtime",
                     "installed_runtime", "configuration"):
            self.assertIn(f"the {name} matches the sealed expectation",
                          checks.failed)

    def test_EVERY_IDENTITY_REMOVED_is_REFUSED(self):
        """The reviewer's second probe: no stage attempt, no verdict attempt,
        no custody -- all previously comparing equal because all were None."""
        held = copy.deepcopy(self.observed)
        for stage in held["status"]["jobs"][0]["stages"]:
            stage.pop("attempt_id", None)
        held["records"]["verdict"].pop("attempt_id", None)
        held["line"]["custody"] = None
        checks = self.verify.judge(held)
        for what in ("the implementation stage names an attempt",
                     "the review stage names an attempt",
                     "the integration stage names an attempt",
                     "the accepted verdict names this episode's review attempt",
                     "custody holds THIS implementation attempt"):
            self.assertIn(what, checks.failed)

    def test_an_EMPTY_STRING_is_absent_too(self):
        """The shape a stripped fixture and an unfilled record both produce."""
        for empty in ("", {}, [], None):
            with self.subTest(empty=empty):
                held = copy.deepcopy(self.observed)
                held["measured"]["image"] = empty
                held["expected"]["image"] = empty
                self.assertIn("the image matches the sealed expectation",
                              self.verify.judge(held).failed)

    def test_the_POSITIVE_shape_still_passes_with_the_stricter_rule(self):
        """A rule that also refused the real shape would be useless."""
        self.assertEqual(self.judged().failed, [])


class AnUNREADRecordIsNotAMISSINGOne(VerifierCase):
    """Review [R4]: "distinguish missing records from unread/unimplemented
    ones" and "do not conflate the unimplemented reader with a lifecycle
    refusal". An operator looks in different places for the two."""

    def test_an_UNREAD_record_fails_its_own_check(self):
        held = copy.deepcopy(self.observed)
        held["records"]["verdict"] = {"unread": "the store was not opened"}
        checks = self.verify.judge(held)
        self.assertIn("the verdict record was READ", checks.failed)

    def test_a_MISSING_record_fails_the_content_check_and_not_the_read_one(self):
        """Read, and genuinely absent: a different failure with a different
        remedy."""
        held = copy.deepcopy(self.observed)
        held["records"]["verdict"] = {"missing": "this line has no verdict"}
        checks = self.verify.judge(held)
        self.assertNotIn("the verdict record was READ", checks.failed)
        self.assertIn("a review verdict was ACCEPTED", checks.failed)

    def test_the_CAPTURED_records_still_match_the_adapter(self):
        """The calibration, and what catches a reader that drifts from its
        owner: these member names came out of the real contracts."""
        self.assertEqual(sorted(self.captured["verdict"]),
                         ["attempt_id", "checkpoint_id", "disposition",
                          "verdict_id", "work_id"])
        self.assertEqual(sorted(self.captured["checkpoint"]),
                         ["checkpoint_id", "evidence"])
        self.assertEqual(sorted(self.captured["result"]),
                         ["assignment_ref", "attempt_id", "disposition",
                          "manifest_digest", "result_id"])
        self.assertEqual(self.captured["verdict"]["disposition"], "accepted")
        self.assertEqual(self.captured["checkpoint"]["evidence"]["paths"],
                         [self.verify.CANDIDATE_FILE])
        self.assertEqual(self.captured["result"]["disposition"], "completed")

    def test_the_captured_TERMINAL_is_honestly_unread(self):
        """`read_records` no longer OWNS the terminal, and says so instead of
        answering an empty document. Review201732 [R1] corrected the claim this
        case used to carry: the terminal DOES have a read-only owner --
        `StageObservation.observe_integration` -- and `read_terminal` is what
        calls it. This case now pins the honest placeholder; the real read is
        pinned by `test_the_TERMINAL_is_READ_through_its_existing_owner`."""
        self.assertIn("unread", self.captured["terminal"])
        self.assertIn("read_terminal", self.captured["terminal"]["unread"])


class TheEVIDENCEOfAPreviousRunIsNeverOverwritten(unittest.TestCase):
    """Review [R3]: `main` wrote with `write_text` under a reusable default
    claim, so a second run REPLACED the first's evidence and returned zero."""

    def setUp(self):
        import shutil
        import tempfile

        self.verify = _verifier()
        self.home = tempfile.mkdtemp(prefix="w197661-evidence-")
        self.addCleanup(shutil.rmtree, self.home, True)

    def test_a_COLLIDING_run_is_REFUSED_and_the_bytes_survive(self):
        place = os.path.join(self.home, "verification-collide.json")
        with open(place, "w") as handle:
            handle.write("THE PREVIOUS RUN'S EVIDENCE\n")
        # SELF-CONTAINED, which it was not. Review 2026-09-18T07-01-24Z [R2]:
        # this patched the readers and left `check_policy_pin`, whose default
        # reads the emitted `deployment.json` and the INSTALLED Authority --
        # so a unit case about a file collision made one real deployment call,
        # and the reviewer's AssertionError boundary proved it by failing
        # before the collision was ever checked. Every boundary `main` reaches
        # is replaced here.
        import compose_lifecycle

        with mock.patch.object(self.verify, "HERE", pathlib.Path(self.home)), \
                mock.patch.object(self.verify, "measure", lambda: {}), \
                mock.patch.object(self.verify, "read_status",
                                  lambda run=None, observe=True: {}), \
                mock.patch.object(self.verify, "read_terminal",
                                  lambda run=None: {}), \
                mock.patch.object(self.verify, "read_owned_proposal",
                                  dict), \
                mock.patch.object(self.verify, "measure_observation_gap",
                                  lambda run=None: {}), \
                mock.patch.object(self.verify, "read_authority", dict), \
                mock.patch.object(self.verify, "read_line", dict), \
                mock.patch.object(self.verify, "read_records", dict), \
                mock.patch.object(compose_lifecycle, "check_policy_pin",
                                  lambda **named: {"equal": False}):
            answered = self.verify.main(["--claim", "collide"])
        self.assertEqual(answered, 2)
        with open(place) as handle:
            self.assertEqual(handle.read(), "THE PREVIOUS RUN'S EVIDENCE\n")

    def test_the_claim_NAME_is_required_and_has_no_reusable_default(self):
        """A reusable name plus an overwriting write is how the previous run's
        evidence disappeared."""
        with self.assertRaises(SystemExit):
            self.verify.main([])


class PRESENCEIsNotVALIDATION(VerifierCase):
    """Review 2026-09-18T07-01-24Z [R1], and this completes the earlier
    required-value finding rather than adding scope.

    `_present` accepted every non-container scalar, so setting all five
    provenance members to `False` on BOTH sides passed every check: a
    comparison of two well-typed-looking nothings is the same defect wearing a
    scalar. And `Checks.named` treated `wanted=None` as "no binding requested",
    so REMOVING the verdict's `checkpoint_id` -- the identity the check exists
    to bind -- turned the check off and reported a pass.
    """

    def test_a_BOOLEAN_on_both_sides_is_REFUSED(self):
        """The reviewer's probe exactly."""
        held = copy.deepcopy(self.observed)
        for name in ("image", "image_inputs", "built_runtime",
                     "installed_runtime", "configuration"):
            held["measured"][name] = False
            held["expected"][name] = False
        checks = self.verify.judge(held)
        for name in ("image", "image_inputs", "built_runtime",
                     "installed_runtime", "configuration"):
            self.assertIn(f"the {name} matches the sealed expectation",
                          checks.failed)

    def test_MALFORMED_scalars_are_refused_per_kind(self):
        """A digest that is not one, an identity with a space, a manifest whose
        values are not digests: each fails its own kind."""
        for name, bad in (("built_runtime", "not-a-digest"),
                          ("built_runtime", "sha256:" + "z" * 64),
                          ("configuration", 0),
                          ("image", "an identity with spaces"),
                          ("image_inputs", {"worker/x.py": True}),
                          ("image_inputs", {"": "sha256:" + "b" * 64})):
            with self.subTest(name=name, bad=bad):
                held = copy.deepcopy(self.observed)
                held["measured"][name] = bad
                held["expected"][name] = bad
                self.assertIn(f"the {name} matches the sealed expectation",
                              self.verify.judge(held).failed)

    def test_a_ONE_SIDED_missing_reference_is_REFUSED(self):
        """The reviewer's second probe: only `records.verdict.checkpoint_id`
        removed, everything else intact."""
        held = copy.deepcopy(self.observed)
        held["records"]["verdict"].pop("checkpoint_id", None)
        checks = self.verify.judge(held)
        self.assertIn("the accepted checkpoint is the one the verdict names",
                      checks.failed)

    def test_EVERY_required_binding_fails_when_EITHER_side_goes(self):
        """A required reference has two sides by definition."""
        for path, what in (
                (["records", "verdict", "attempt_id"],
                 "the accepted verdict names this episode's review attempt"),
                (["records", "verdict", "checkpoint_id"],
                 "the accepted checkpoint is the one the verdict names"),
                (["records", "result", "attempt_id"],
                 "the frozen result is THIS implementation attempt's"),
                (["line", "custody"],
                 "custody holds THIS implementation attempt")):
            with self.subTest(what=what):
                held = copy.deepcopy(self.observed)
                where = held
                for step in path[:-1]:
                    where = where[step]
                where.pop(path[-1], None)
                self.assertIn(what, self.verify.judge(held).failed)

    def test_the_POSITIVE_shape_still_passes_under_the_typed_rule(self):
        self.assertEqual(self.judged().failed, [])


class TheADAPTERSAreExercisedAndNotJustRecorded(unittest.TestCase):
    """Review 2026-09-18T07-01-24Z [R2]: the captured-record case only checked
    the keys of a saved JSON file, so an adapter regression would not fail it.

    These drive `read_records` itself over faithful owner doubles -- the shapes
    the real modules return, including the two members I originally guessed
    wrong: `runtime_attempt_id` on the review attachment and `assignment_ref`
    in the retained RESULT MANIFEST rather than on the frozen row.
    """

    LINE = "line-" + "a" * 64
    ATTEMPT = "attempt-" + "b" * 64
    REVIEW_ATTEMPT = "attempt-" + "c" * 64

    def setUp(self):
        self.verify = _verifier()

    def owners(self, **changed):
        """Doubles shaped exactly as the real readers answer."""
        accepted = {"checkpoint_id": "checkpoint-1", "verdict_id": "verdict-1",
                    "evidence": {"base": self.verify.TARGET_BASE,
                                 "paths": [self.verify.CANDIDATE_FILE]}}
        verdict = {"verdict_id": "verdict-1", "disposition": "accepted",
                   "checkpoint_id": "checkpoint-1",
                   "work_id": self.verify.WORK, "attachment_id": "review-1"}
        # THE ATTACHMENT ANSWERS `runtime_attempt_id`, which is the member my
        # first reader did not ask for and therefore answered None.
        attachment = {"attachment_id": "review-1",
                      "runtime_attempt_id": self.REVIEW_ATTEMPT}
        # THE FROZEN ROW ANSWERS assignment_ref None; the identity lives in
        # the retained manifest.
        frozen = {"attempt_id": self.ATTEMPT, "disposition": "completed",
                  "result_id": "result-1", "manifest_digest": "sha256:" + "d" * 64,
                  "assignment_ref": None}
        manifest = {"assignment_ref": {"work_ref": {"work_id": self.verify.WORK}}}
        held = {"accepted": accepted, "verdict": verdict,
                "attachment": attachment, "frozen": frozen,
                "manifest": manifest}
        held.update(changed)
        return held

    def read(self, owners):
        cycles = mock.Mock()
        cycles.integration_checkpoint.return_value = owners["accepted"]
        cycles.verdict_of.return_value = owners["verdict"]
        cycles.review_of.return_value = owners["attachment"]
        output = mock.Mock()
        output.frozen_output_of.return_value = owners["frozen"]
        manifests = mock.Mock()
        manifests.load_manifest.return_value = owners["manifest"]
        modules = {"baton_v12.worker_manager.review_cycles": cycles,
                   "baton_v12.worker_manager.output": output,
                   "baton_v12.worker_manager.manifests": manifests}
        real = __import__

        def imported(name, *rest, **named):
            if name == "baton_v12.worker_manager":
                held = mock.Mock()
                held.ControlStore = mock.Mock()
                held.review_cycles = cycles
                held.output = output
                return held
            if name in modules:
                return modules[name]
            return real(name, *rest, **named)

        with mock.patch("builtins.__import__", imported), \
                mock.patch.object(self.verify, "_custody_attempt",
                                  lambda line: self.ATTEMPT):
            return self.verify.read_records(control=mock.Mock(),
                                            line_id=self.LINE)

    def test_the_VERDICT_attempt_comes_from_the_ATTACHMENT(self):
        """`runtime_attempt_id`, not `attempt_id`: the member my first reader
        guessed, which made this predicate fail over the reader rather than
        over the lifecycle."""
        found = self.read(self.owners())
        self.assertEqual(found["verdict"]["attempt_id"], self.REVIEW_ATTEMPT)
        self.assertEqual(found["verdict"]["disposition"], "accepted")

    def test_an_attachment_WITHOUT_that_member_answers_None(self):
        """So `judge` fails the binding rather than inventing an identity."""
        owners = self.owners()
        owners["attachment"] = {"attachment_id": "review-1"}
        self.assertIsNone(self.read(owners)["verdict"]["attempt_id"])

    def test_the_RESULT_assignment_comes_from_the_RETAINED_MANIFEST(self):
        """The frozen row answers `assignment_ref: null`; reading it there was
        the second guess this case exists to catch."""
        found = self.read(self.owners())
        self.assertEqual(
            found["result"]["assignment_ref"]["work_ref"]["work_id"],
            self.verify.WORK)

    def test_a_MISSING_checkpoint_is_reported_as_MISSING(self):
        owners = self.owners()
        owners["accepted"] = None
        found = self.read(owners)
        self.assertIn("missing", found["checkpoint"])
        self.assertIn("missing", found["verdict"])

    def test_a_MISSING_frozen_result_is_reported_as_MISSING(self):
        owners = self.owners()
        owners["frozen"] = None
        self.assertIn("missing", self.read(owners)["result"])

    def test_the_TERMINAL_is_reported_UNREAD_with_its_reason(self):
        found = self.read(self.owners())
        self.assertIn("unread", found["terminal"])
        # REVIEW201732 [R1] CORRECTED THIS, and the case follows the
        # correction rather than the old claim: `managed_account` is NOT this
        # episode's reader, so `read_records` no longer names it. What it now
        # says is that nobody called the reader -- `read_terminal` is a
        # separate owner-backed function and `main` sets its answer in. The
        # adapter case for the real read is
        # `test_the_TERMINAL_is_READ_through_its_existing_owner`.
        self.assertIn("read_terminal", found["terminal"]["unread"])

    def test_what_the_adapter_reads_JUDGES_as_the_captured_record_does(self):
        """The calibration the saved file alone could not provide: the adapter
        output and `CAPTURED-records.json` agree on every member name."""
        with open(os.path.join(INSTANCE, "CAPTURED-records.json")) as handle:
            captured = json.load(handle)
        found = self.read(self.owners())
        for name in ("verdict", "checkpoint", "result"):
            self.assertEqual(sorted(found[name]), sorted(captured[name]),
                             f"the adapter and the captured record disagree "
                             f"about {name}")
class TheREADONLYDefaultIsExercisedOnItsOwn(unittest.TestCase):
    """Review 2026-09-18T07-01-24Z [R2]: "exercise the read-only default
    separately under mocked Authority APIs" -- so the boundary the collision
    case now replaces is still covered rather than merely hidden."""

    def setUp(self):
        if INSTANCE not in sys.path:
            sys.path.insert(0, INSTANCE)
        import compose_lifecycle

        self.compose = compose_lifecycle

    def opened(self, generation=23):
        """An Authority double that records which opener was used."""
        calls = []

        class Held:
            @staticmethod
            def policy_generation():
                return generation

            @staticmethod
            def dispose():
                calls.append("dispose")

        def opener(path, **named):
            calls.append(("opened", path, named))
            return Held()

        return opener, calls

    def test_the_DEFAULT_opener_is_the_READ_ONLY_one(self):
        """The defect was that `read_authority` was corrected and this second
        path still defaulted to the writable `Authority.open`."""
        from baton_v12.authority import Authority

        opener, calls = self.opened()
        with mock.patch.object(Authority, "open_readonly", opener), \
                mock.patch.object(
                    Authority, "open",
                    mock.Mock(side_effect=AssertionError(
                        "a verifier must not open the Authority for "
                        "writing"))):
            found = self.compose.check_policy_pin(pin=23)
        self.assertTrue(found["equal"])
        self.assertEqual(found["authority_generation"], 23)
        self.assertEqual(calls[0][0], "opened")

    def test_a_WRONG_PREDICTION_answers_not_equal(self):
        from baton_v12.authority import Authority

        opener, _calls = self.opened(generation=30)
        with mock.patch.object(Authority, "open_readonly", opener):
            found = self.compose.check_policy_pin(pin=23)
        self.assertFalse(found["equal"])
        self.assertEqual(found["authority_generation"], 30)

    def test_the_Authority_is_always_DISPOSED(self):
        from baton_v12.authority import Authority

        opener, calls = self.opened()
        with mock.patch.object(Authority, "open_readonly", opener):
            self.compose.check_policy_pin(pin=23)
        self.assertIn("dispose", calls)


if __name__ == "__main__":
    unittest.main()


class TheTERMINALIsREADThroughItsEXISTINGOwner(VerifierCase):
    """Review201732 [R1]. claim201492 claimed no read-only reader existed and
    pointed at `managed_account`; the reviewer named the real one and it checks
    out against this tree. These cases pin the correction so it cannot silently
    regress into another missing-reader claim."""

    def test_the_verifier_uses_observation_from_and_NOT_the_serving_factory(self):
        """`operations_from`/`factory` compose a SERVING surface. The named
        owner opens both stores `open_readonly` and holds them only for the
        read."""
        import ast

        with open(self.verify.__file__) as handle:
            tree = ast.parse(handle.read())
        called = set()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            named = node.func
            called.add(named.attr if isinstance(named, ast.Attribute)
                       else getattr(named, "id", None))
        # CALLS, NOT PROSE. The first form of this read the file as text and
        # failed on the verifier's own comment SAYING it never calls them --
        # a check that cannot distinguish a citation from an invocation.
        self.assertIn("observation_from", called)
        self.assertIn("observe_integration", called)
        for forbidden in ("operations_from", "factory", "managed_account"):
            self.assertNotIn(forbidden, called,
                             f"the verifier CALLS {forbidden}, which is a "
                             f"serving composition")

    def test_the_named_owner_really_is_READ_ONLY_in_this_tree(self):
        """The correction is revalidated against the current source rather than
        taken on the reviewer's word, which is this repository's standing rule
        for a pinned decision."""
        import inspect

        sys.path.insert(0, os.path.join(REPO, "v12/python"))
        sys.path.insert(0, os.path.join(REPO, "v12/python/src"))
        from tools import stage_execution

        body = inspect.getsource(stage_execution.StageObservation
                                 .observe_integration)
        self.assertIn("Authority.open_readonly", body)
        self.assertIn("IntegrationStore.open_readonly", body)
        self.assertTrue(callable(stage_execution.observation_from))

    def test_the_observation_CONTRACT_is_required_and_not_just_a_state(self):
        self.refuses(["records", "terminal", "schema"], "something.else/1",
                     "the observation is the integration-stage-observation "
                     "contract")

    def test_a_BARE_completed_with_NO_completion_references_is_refused(self):
        """"A bare completed string or provider result is not an equivalent
        proof" -- review201732 [R1]."""
        checks = self.bent(["records", "terminal"],
                           {"schema": "baton.v12.integration-stage-observation/1",
                            "state": "completed"})
        for needed in ("proposal_id", "integration_receipt_id", "entry_id",
                       "lease_id", "handoff_operation_id", "runtime_id"):
            self.assertIn(f"the completion names its {needed}", checks.failed)

    def test_ANOTHER_Works_observation_is_refused(self):
        self.refuses(["records", "terminal", "assignment", "work_ref"],
                     {"authority_uuid": self.verify.AUTHORITY,
                      "work_id": "somebody-else-W9"},
                     "the observed assignment names this Work")

    def test_ANOTHER_Authoritys_observation_is_refused(self):
        self.refuses(["records", "terminal", "assignment", "work_ref"],
                     {"authority_uuid": "f" * 32, "work_id": self.verify.WORK},
                     "the observed assignment names this Authority")

    def test_ANOTHER_attempts_observation_is_refused(self):
        self.refuses(["records", "terminal", "attempt_id"],
                     "attempt-" + "9" * 64,
                     "the observed attempt is the stage's attempt")

    def test_ANOTHER_stages_observation_is_refused(self):
        self.refuses(["records", "terminal", "stage_id"], "other-job/integration",
                     "the observation names THIS stage")

    def test_a_HELD_terminal_is_refused(self):
        self.refuses(["records", "terminal", "state"], "held",
                     "and `held` is not mistaken for that")

    def test_an_UNREAD_terminal_can_never_pass(self):
        """A refusal inside the reader is reported, never swallowed."""
        checks = self.bent(["records", "terminal"],
                           {"unread": "ContractRefusal: no"})
        self.assertIn("the terminal record was READ", checks.failed)


class TheOWNEDChainBindsBASEToRESULTToTARGET(VerifierCase):
    """Review201732 [R3]: "Bind initial base, owned settlement/result revision,
    final target and imported candidate/test evidence through the accepted
    completion contract; test wrong Work/attempt/result/target and unrelated
    descendant negatives.\""""

    def test_an_UNRELATED_LATER_DESCENDANT_is_REFUSED(self):
        """THE NEGATIVE ANCESTRY CANNOT REJECT, and the reason the check is a
        chain rather than a comparison. This revision is a perfectly good
        descendant of the declared base -- it is simply not what this episode's
        proposal produced, and nothing about ancestry can tell the difference."""
        self.refuses(["authority", "canonical_target"], "d" * 40,
                     "the canonical target IS the revision this proposal "
                     "produced")

    def test_BASE_EQUALITY_is_NOT_what_is_asserted(self):
        """The old check demanded the target still equal the declared base,
        which fails every successful import. The successful fixture's target is
        the advanced one, so this passing IS the correction."""
        self.assertEqual(self.judged().failed, [])
        self.assertNotEqual(self.observed["authority"]["canonical_target"],
                            self.verify.TARGET_BASE)

    def test_a_proposal_made_from_ANOTHER_BASE_is_refused(self):
        self.refuses(["owned", "proposal", "target"], "a" * 40,
                     "the owned proposal was made FROM the declared base")

    def test_a_proposal_owned_by_ANOTHER_WORK_is_refused(self):
        self.refuses(["owned", "proposal", "assignment_ref"],
                     {"work_ref": {"work_id": "somebody-else-W9"}},
                     "the owned proposal names this Work")

    def test_a_proposal_from_ANOTHER_RESULT_is_refused(self):
        self.refuses(["owned", "proposal", "result_id"], "result-" + "9" * 64,
                     "the owned proposal is THIS episode's frozen result")

    def test_a_proposal_the_COMPLETION_DOES_NOT_NAME_is_refused(self):
        self.refuses(["owned", "proposal", "proposal_id"],
                     "integration-driver.proposal:" + "9" * 64,
                     "the owned proposal is the one the completion names")

    def test_a_TARGET_THAT_NEVER_ADVANCED_is_refused(self):
        """A candidate identical to the base means nothing was imported, and
        the chain would otherwise still close on itself."""
        held = copy.deepcopy(self.observed)
        held["owned"]["proposal"]["candidate_digest"] = self.verify.TARGET_BASE
        held["owned"]["receipt"]["candidate_digest"] = self.verify.TARGET_BASE
        held["authority"]["canonical_target"] = self.verify.TARGET_BASE
        self.assertIn("and the target actually ADVANCED from the base",
                      self.verify.judge(held).failed)

    def test_a_receipt_that_settled_ANOTHER_CANDIDATE_is_refused(self):
        self.refuses(["owned", "receipt", "candidate_digest"], "e" * 40,
                     "the receipt settled the same candidate")

    def test_a_receipt_the_COMPLETION_DOES_NOT_NAME_is_refused(self):
        self.refuses(["owned", "receipt", "receipt_id"],
                     "integration-driver.integration-receipt:" + "9" * 64,
                     "the integration receipt is the completion's")

    def test_a_REFUSED_disposition_is_refused(self):
        self.refuses(["owned", "receipt", "disposition"], "declined",
                     "the receipt's disposition is INTEGRATED")

    def test_an_UNREAD_owned_proposal_can_never_pass(self):
        checks = self.bent(["owned"], {"unread": "OSError: no"})
        self.assertIn("the owned proposal was READ", checks.failed)


class HISTORICALCompletionIsSEPARATEFromFUTUREReadiness(VerifierCase):
    """Review202028, and the correction is to what the check MEANS.

    The pin comparison was a REQUIRED gate on historical completion. That is
    backwards: `authority/core.py integrate` decides, then
    `set_policy(canonical_target)` bumps the generation unconditionally, so a
    SUCCESSFUL integration always ends one past its own receipt. A gate every
    success fails is not a gate.
    `tests/authority/test_integration_generation.py` proves the mechanism
    deterministically against this tree (7 -> 8, receipt decision 7).

    IT IS NOT REMOVED. It runs, its values are recorded, its failure is
    reported -- under `readiness`, which is the question it actually answers.
    """

    def mismatched(self):
        """The retained run4 SHAPE: the pin the receipt was accepted under,
        and an Authority one step past it.

        THE CONFIGURED PIN STAYS THE FIXTURE'S, deliberately. Moving it alone
        would ALSO break the acceptance-time binding -- correctly, since a
        receipt accepted under some other generation was never this
        deployment's -- and the case would then pass for the wrong reason.
        """
        held = copy.deepcopy(self.observed)
        held["pin"] = {"configured_pin": 23, "authority_generation": 24,
                       "equal": False}
        return self.verify.judge(held)

    def test_a_MISMATCHED_pin_does_NOT_fail_the_completed_run(self):
        """The retained run4 shape exactly: pin 9, Authority 10, receipt 9."""
        held = copy.deepcopy(self.observed)
        held["pin"] = {"configured_pin": 23, "authority_generation": 24,
                       "equal": False}
        self.assertEqual(self.verify.judge(held).failed, [])

    def test_but_it_IS_reported_as_a_readiness_failure(self):
        """Visible, not swallowed. This is what "do not silently remove"
        means once the check has been moved to its right question."""
        self.assertIn("the deployment could authorize a NEW action",
                      self.mismatched().readiness_failed)

    def test_the_two_verdicts_are_answered_SEPARATELY(self):
        checks = self.mismatched()
        self.assertEqual(checks.failed, [])
        self.assertNotEqual(checks.readiness_failed, [])

    def test_the_readiness_detail_says_WHAT_IT_BEARS_ON(self):
        detail = [one["detail"] for one in self.mismatched().held
                  if one["check"] == "the deployment could authorize a NEW "
                                     "action"][0]
        self.assertIn("FUTURE authorization only", detail["bears_on"])
        self.assertIn("set_policy", detail["the_mechanism"])

    def test_a_readiness_check_is_NEVER_a_required_one(self):
        for one in self.judged().held:
            if one["check"].startswith("the deployment could authorize"):
                self.assertFalse(one["required"])

    # -- what the completed run IS proved by, and still fails without --------

    def test_ACCEPTANCE_TIME_generation_is_still_REQUIRED(self):
        """A later advance cannot un-accept a receipt; a receipt accepted under
        the WRONG generation was never this deployment's."""
        self.refuses(["owned", "receipt", "decision"],
                     {"policy_generation": 4},
                     "the integration receipt was accepted under the "
                     "configured pin")

    def test_an_UNOWNED_receipt_still_fails_even_with_a_matching_pin(self):
        """The pin moving out of the verdict must not take the owned bindings
        with it."""
        held = copy.deepcopy(self.observed)
        held["owned"]["receipt"]["proposal_id"] = ("integration-driver."
                                                   "proposal:" + "9" * 64)
        self.assertIn("the receipt settles the owned proposal",
                      self.verify.judge(held).failed)

    def test_an_UNOWNED_terminal_still_fails_even_with_a_matching_pin(self):
        held = copy.deepcopy(self.observed)
        held["records"]["terminal"]["assignment"]["work_ref"]["work_id"] = "W9"
        self.assertIn("the observed assignment names this Work",
                      self.verify.judge(held).failed)

    # -- and the advance itself proves nothing -------------------------------

    def test_a_ONE_STEP_advance_is_NOT_treated_as_acceptance(self):
        """Review202028: "Do not ... infer acceptance from merely current ==
        configured+1." The shape is recorded; the owned evidence is what
        decides, and it fails independently."""
        held = copy.deepcopy(self.observed)
        held["pin"] = {"configured_pin": 23, "authority_generation": 24,
                       "equal": False}
        held["owned"]["proposal"]["target"] = "a" * 40
        self.assertIn("the owned proposal was made FROM the declared base",
                      self.verify.judge(held).failed)

    def test_the_one_step_shape_is_RECORDED_in_NEITHER_verdict(self):
        """It was a readiness requirement, which is what made `ready`
        unsatisfiable beside pin equality. It is now a diagnostic: measured,
        reported, and entering neither conjunction."""
        held = copy.deepcopy(self.observed)
        held["pin"] = {"configured_pin": 23, "authority_generation": 99,
                       "equal": False}
        checks = self.verify.judge(held)
        self.assertEqual(checks.failed, [])
        self.assertNotIn("the advance is the ONE STEP a single integration "
                         "makes", checks.readiness_failed)
        self.assertIn("the advance is the ONE STEP a single integration makes",
                      [one["observation"] for one in checks.diagnostics])

    def test_GENERATION_ZERO_is_a_legitimate_value(self):
        """`count` rather than truthiness: the type vocabulary had already
        failed two checks whose `found` and `wanted` were the same number."""
        self.assertTrue(self.verify._well_formed(0, "count"))
        self.assertFalse(self.verify._well_formed(True, "count"))
        self.assertFalse(self.verify._well_formed("1", "count"))
        self.assertFalse(self.verify._well_formed(-1, "count"))


class TheOBSERVEOperandIsTheCONTROLLEDComparison(VerifierCase):
    """Review201732 [R2]: "Do not label new incarnation the cause without a
    controlled comparison." This is the comparison, and it is what refuted my
    own F1."""

    def test_read_status_passes_observe_AND_the_configuration_it_needs(self):
        seen = {}

        def runner(argv, env=None):
            seen["argv"], seen["env"] = argv, env
            return types.SimpleNamespace(returncode=0, stdout="{}")

        self.verify.read_status(run=runner, observe=True)
        self.assertIn("--observe", seen["argv"])
        self.assertIn(self.verify.OBSERVING_FACTORY, seen["argv"])
        self.assertEqual(seen["env"]["BATON_V12_STAGE_EXECUTION_CONFIG"],
                         str(self.verify.DEPLOYMENT))

    def test_the_UNOBSERVED_form_passes_NEITHER(self):
        seen = {}

        def runner(argv, env=None):
            seen["argv"], seen["env"] = argv, env
            return types.SimpleNamespace(returncode=0, stdout="{}")

        self.verify.read_status(run=runner, observe=False)
        self.assertNotIn("--observe", seen["argv"])
        self.assertNotIn("BATON_V12_STAGE_EXECUTION_CONFIG", seen["env"])

    def test_the_two_argv_differ_in_NOTHING_BUT_the_operand(self):
        """A comparison whose two sides differ in the store, the incarnation or
        the authority proves nothing about the operand."""
        seen = []

        def runner(argv, env=None):
            seen.append(list(argv))
            return types.SimpleNamespace(returncode=0, stdout="{}")

        self.verify.read_status(run=runner, observe=True)
        self.verify.read_status(run=runner, observe=False)
        observed, plain = seen
        self.assertEqual(observed[:len(plain)], plain)
        self.assertEqual(observed[len(plain):],
                         ["--observe", self.verify.OBSERVING_FACTORY])

    def test_the_gap_is_MEASURED_rather_than_asserted(self):
        answers = iter([
            {"jobs": [{"job_id": self.verify.JOB, "stages": [
                {"kind": "integration", "state": "completed"}]}]},
            {"jobs": [{"job_id": self.verify.JOB, "stages": [
                {"kind": "integration", "state": "starting"}]}]}])

        def runner(argv, env=None):
            return types.SimpleNamespace(returncode=0,
                                         stdout=json.dumps(next(answers)))

        found = self.verify.measure_observation_gap(run=runner)
        self.assertEqual(found["with_observe"], "completed")
        self.assertEqual(found["without_observe"], "starting")
        self.assertTrue(found["explains_the_gap"])

    def test_it_does_NOT_claim_a_gap_when_BOTH_answer_the_same(self):
        """If the operand were not the cause, this must say so."""
        def runner(argv, env=None):
            return types.SimpleNamespace(returncode=0, stdout=json.dumps(
                {"jobs": [{"job_id": self.verify.JOB, "stages": [
                    {"kind": "integration", "state": "completed"}]}]}))

        found = self.verify.measure_observation_gap(run=runner)
        self.assertFalse(found["explains_the_gap"])

    def test_the_RETAINED_comparison_from_the_real_run_is_preserved(self):
        """The captured measurement, so the refutation of F1 survives as
        evidence rather than as a sentence in a dossier."""
        gap = self.owner_shaped["observation_gap"]
        self.assertEqual(gap["without_observe"], "starting")
        self.assertEqual(gap["with_observe"], "completed")
        self.assertTrue(gap["explains_the_gap"])


class TheHOLESReview201853ProbedAreCLOSED(VerifierCase):
    """Three pure-document probes that ACCEPTED a broken run against exactly
    this fixture. Each is a case now, and each was reproduced before it was
    fixed: they all passed against the previous verifier."""

    # -- the episode, which nothing bound ------------------------------------

    def test_a_WRONG_episode_is_refused(self):
        """`terminal.episode = 999` was accepted."""
        self.refuses(["records", "terminal", "episode"], 999,
                     "the observed episode IS the stage's selected episode")

    def test_a_MISSING_episode_is_refused(self):
        """Removing it was accepted, which is the worse half: a check that
        vanishes with its operand protects nothing."""
        held = copy.deepcopy(self.observed)
        del held["records"]["terminal"]["episode"]
        failed = self.verify.judge(held).failed
        self.assertIn("the observed episode is a typed episode number", failed)
        self.assertIn("the observed episode IS the stage's selected episode",
                      failed)

    def test_a_BOOLEAN_episode_is_refused(self):
        """`True == 1` in Python, so an untyped comparison accepts it."""
        self.refuses(["records", "terminal", "episode"], True,
                     "the observed episode is a typed episode number")

    def test_a_STRING_episode_is_refused(self):
        self.refuses(["records", "terminal", "episode"], "1",
                     "the observed episode is a typed episode number")

    def test_a_SECOND_episode_is_refused_as_not_this_proof(self):
        """This proof is of a single-episode integration. A retried one may be
        perfectly correct -- it is simply not what this run demonstrated, and
        claiming it would be claiming something unmeasured."""
        held = copy.deepcopy(self.observed)
        held["records"]["terminal"]["episode"] = 2
        held["status"]["jobs"][0]["stages"][2]["episode"] = 2
        failed = self.verify.judge(held).failed
        self.assertIn("this proof's integration ran ONE episode", failed)
        self.assertIn("and the projection agrees it ran one", failed)

    def test_the_two_episode_operands_must_AGREE_with_each_other(self):
        """Not merely each with the declared constant: a projection and an
        observation that disagree about which episode ran is exactly the mixed
        captured input review201853 said the verifier must reject."""
        held = copy.deepcopy(self.observed)
        held["status"]["jobs"][0]["stages"][2]["episode"] = 7
        failed = self.verify.judge(held).failed
        self.assertIn("the observed episode IS the stage's selected episode",
                      failed)

    # -- the owned proposal's Authority, which nothing bound -----------------

    def test_a_proposal_from_ANOTHER_AUTHORITY_is_refused(self):
        """32 `f` characters was accepted. A proposal from another Authority
        can carry this Work's local id, so the Work binding did not cover it."""
        self.refuses(["owned", "proposal", "assignment_ref"],
                     {"work_ref": {"authority_uuid": "f" * 32,
                                   "work_id": self.verify.WORK}},
                     "the owned proposal names this Authority")

    def test_a_proposal_with_NO_Authority_is_refused(self):
        self.refuses(["owned", "proposal", "assignment_ref"],
                     {"work_ref": {"work_id": self.verify.WORK}},
                     "the owned proposal names this Authority")

    def test_a_proposal_and_OBSERVATION_that_disagree_are_refused(self):
        """Both name a well-formed Authority; they are not the same one. Only
        binding each to the constant would accept this."""
        held = copy.deepcopy(self.observed)
        held["records"]["terminal"]["assignment"]["work_ref"] = {
            "authority_uuid": "a" * 32, "work_id": self.verify.WORK}
        failed = self.verify.judge(held).failed
        self.assertIn("its Authority is the one the OBSERVATION names", failed)


class TheOUTEROpenerIsExercisedAgainstALocalStore(unittest.TestCase):
    """Review201853 [R2]: "Add a meaningful local temporary-store adapter case
    for missing/stale inputs and release/refusal paths."

    NO DESTINATION, NO DEPLOYMENT, NO ENGINE. Every case here is a temporary
    directory, so the retained run4 is never opened by this suite.

    WHAT THESE ARE FOR. The AST cases establish WHICH owner the verifier calls.
    They say nothing about the adapter that gets it a Job store. That adapter
    was `JobStore.open` -- writable, initializing, migrating, WAL-requesting --
    and is now `JobStore.open_readonly`. The owner's own refusals are covered
    by `tests/job_manager/test_store_readonly.py`; these cases are about the
    ADAPTER: that the verifier reaches them, carries their text through as
    `unread`, and never lets one read as an answer.
    """

    def setUp(self):
        import shutil
        import tempfile

        self.verify = _verifier()
        self.home = pathlib.Path(tempfile.mkdtemp(prefix="v12-w197661-opener-"))
        self.addCleanup(shutil.rmtree, self.home, True)
        self.db = self.home / "db"
        self.db.mkdir()
        self.patch = mock.patch.object(self.verify, "DEST", self.home)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.deployment = mock.patch.object(self.verify, "DEPLOYMENT",
                                            self.home / "deployment.json")
        self.deployment.start()
        self.addCleanup(self.deployment.stop)

    def deployed(self):
        (self.home / "deployment.json").write_text(json.dumps({"workers": []}))

    def files(self):
        return sorted(one.name for one in self.db.iterdir())

    # -- missing inputs ------------------------------------------------------

    def test_a_MISSING_deployment_document_is_UNREAD_and_named(self):
        found = self.verify.read_terminal()
        self.assertIn("unread", found)
        self.assertIn("deployment.json", found["unread"])

    def test_a_MISSING_store_is_REFUSED_BY_THE_OWNER(self):
        """The refusal is `JobStore.open_readonly`'s now, not this file's
        header guess, and the adapter carries its text through."""
        self.deployed()
        found = self.verify.read_terminal()
        self.assertIn("unread", found)
        self.assertIn("existing regular store", found["unread"])
        self.assertIn("does not create what it was asked to read",
                      found["unread"])

    def test_and_the_missing_store_is_STILL_NOT_THERE_afterwards(self):
        """The assertion that makes the one above mean something."""
        self.deployed()
        self.verify.read_terminal()
        self.assertEqual(self.files(), [],
                         "the verifier created something at a path it refused")

    def test_a_store_that_is_a_DIRECTORY_is_refused(self):
        self.deployed()
        (self.db / "jobs.sqlite3").mkdir()
        found = self.verify.read_terminal()
        self.assertIn("unread", found)
        self.assertIn("existing regular store", found["unread"])

    # -- stale and unreadable inputs ----------------------------------------

    def test_a_STALE_non_database_store_is_reported_UNREAD_not_ACCEPTED(self):
        """A refusal inside the adapter must surface as `unread` -- which
        `judge` fails -- rather than as an empty document that reads like a
        lifecycle answer."""
        self.deployed()
        (self.db / "jobs.sqlite3").write_bytes(b"NOT A DATABASE AT ALL\n")
        found = self.verify.read_terminal()
        self.assertIn("unread", found)
        self.assertNotIn("completion", found)

    def test_a_stale_store_CANNOT_be_mistaken_for_a_completed_run(self):
        self.deployed()
        (self.db / "jobs.sqlite3").write_bytes(b"NOT A DATABASE AT ALL\n")
        checks = self.verify.judge({"records": {
            "terminal": self.verify.read_terminal()}})
        self.assertIn("the terminal record was READ", checks.failed)

    def test_an_EMPTY_store_file_does_not_become_an_INITIALIZED_one(self):
        """THE CASE THAT FOUND THE REAL DEFECT. Written at claim201869 against
        the interim guard, it caught `JobStore.open` taking its `_initialize`
        branch and writing a complete 716KB database into a path the verifier
        was only reading. It is kept unchanged against the real opener, which
        refuses an empty store rather than initializing one."""
        self.deployed()
        place = self.db / "jobs.sqlite3"
        place.write_bytes(b"")
        found = self.verify.read_terminal()
        self.assertIn("unread", found)
        self.assertIn("empty", found["unread"])
        self.assertEqual(place.read_bytes(), b"",
                         "the verifier initialized an empty store it was only "
                         "meant to read")

    # -- release -------------------------------------------------------------

    def test_a_REFUSAL_releases_every_handle_and_leaves_no_sidecar(self):
        """A leaked handle holds a lock on a store the verifier has just said
        it must not touch -- `JobStore.open`'s own words for why it closes on
        every failure path."""
        self.deployed()
        (self.db / "jobs.sqlite3").write_bytes(b"NOT A DATABASE AT ALL\n")
        self.verify.read_terminal()
        self.assertEqual(self.files(), ["jobs.sqlite3"],
                         f"a refusal left {self.files()} behind")

    def test_the_REFUSAL_TEXT_is_kept_because_that_text_is_the_finding(self):
        self.deployed()
        (self.db / "jobs.sqlite3").write_bytes(b"NOT A DATABASE AT ALL\n")
        found = self.verify.read_terminal()
        self.assertTrue(found["unread"].strip(),
                        "an empty refusal is a refusal nobody can act on")


class TheOPENERIsTheREADONLYOwner(VerifierCase):
    """The requirement, INVERTED from what claim201869 had.

    That turn's check positively required `opener_is_read_only: False`, which
    was an honest description of an interim and, as review201931 said, must
    never be the acceptance contract -- it would refuse the very fix F5 asked
    for. `JobStore.open_readonly` exists now, so the verifier requires it.
    """

    def test_the_verifier_opens_the_Job_store_READ_ONLY(self):
        import ast

        with open(self.verify.__file__) as handle:
            tree = ast.parse(handle.read())
        # THE RECEIVER MATTERS. `open` alone is Python's builtin and this file
        # legitimately reads text with it; what must not appear is a call to
        # the WRITE-CAPABLE opener on one of these owners.
        owners = ("JobStore", "ControlStore", "Authority", "IntegrationStore")
        opened = set()
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)):
                continue
            receiver = getattr(node.func.value, "id", None)
            if receiver in owners:
                opened.add(f"{receiver}.{node.func.attr}")
        self.assertIn("JobStore.open_readonly", opened)
        for owner in owners:
            self.assertNotIn(f"{owner}.open", opened,
                             f"the verifier reaches {owner}'s write-capable "
                             f"opener")

    def test_the_named_READ_ONLY_owner_really_exists_in_this_tree(self):
        """A pinned decision revalidated against the code rather than trusted:
        claim201869 reported this API as ABSENT, and it is this turn's work
        that added it."""
        sys.path.insert(0, os.path.join(REPO, "v12/python/src"))
        from baton_v12.job_manager import JobStore

        self.assertTrue(hasattr(JobStore, "open_readonly"))

    def test_an_opener_that_is_NOT_read_only_is_refused(self):
        self.refuses(["records", "terminal", "_opener"],
                     {"opener": "baton_v12.job_manager.JobStore.open",
                      "opener_is_read_only": False,
                      "refusals_are_the_owners": False,
                      "data_unchanged": True, "only_sqlite_sidecars": True},
                     "and it is a READ-ONLY owner")

    def test_an_UNREPORTED_opener_is_refused(self):
        held = copy.deepcopy(self.observed)
        del held["records"]["terminal"]["_opener"]
        self.assertIn("the opener this read went through is REPORTED",
                      self.verify.judge(held).failed)

    def test_refusals_made_by_THE_VERIFIER_rather_than_the_OWNER_are_refused(self):
        """The interim guessed at SQLite's file header in this file. The point
        of the opener is that the refusal belongs to the owner."""
        held = copy.deepcopy(self.observed)
        held["records"]["terminal"]["_opener"]["refusals_are_the_owners"] = False
        self.assertIn("the owner itself refuses what must not be read",
                      self.verify.judge(held).failed)

    def test_the_OBSOLETE_interim_guard_is_GONE(self):
        """A dead guard left beside the real owner is a second place for the
        decision to live and drift."""
        self.assertFalse(hasattr(self.verify, "_store_refusal"))
        with open(self.verify.__file__) as handle:
            self.assertNotIn("_SQLITE_MAGIC", handle.read())

    def test_it_no_longer_claims_the_API_is_UNAVAILABLE(self):
        found = self.verify._opener_report(
            pathlib.Path("/nonexistent/jobs.sqlite3"),
            {"main": None, "-wal": None, "-shm": None})
        self.assertTrue(found["read_only_opener_available"])
        self.assertNotIn("bounded_resolution", found)

    def test_the_verifier_uses_NO_RAW_SQL(self):
        import ast

        with open(self.verify.__file__) as handle:
            tree = ast.parse(handle.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                said = node.value.strip().upper()
                self.assertFalse(
                    said.startswith(("SELECT ", "PRAGMA ", "ATTACH ",
                                     "INSERT ", "UPDATE ", "DELETE ")),
                    f"the verifier issues raw SQL: {node.value[:60]!r}")

    def test_the_DATA_and_SIDECAR_questions_are_answered_SEPARATELY(self):
        """One says the retained run is intact; the other says whether anything
        but SQLite's own WAL machinery appeared. Merging them loses both."""
        names = [one["check"] for one in self.judged().held]
        self.assertIn("this read moved no byte of the store's DATA", names)
        self.assertIn("the read created NOTHING BUT SQLite's own WAL machinery",
                      names)

    def test_a_read_that_CHANGED_THE_DATA_is_refused(self):
        held = copy.deepcopy(self.observed)
        held["records"]["terminal"]["_opener"]["data_unchanged"] = False
        self.assertIn("this read moved no byte of the store's DATA",
                      self.verify.judge(held).failed)

    def test_a_read_that_left_something_OTHER_than_a_sidecar_is_refused(self):
        """SQLite's `-wal` and `-shm` are exempt because a mode=ro connection
        cannot remove them; a new journal or a created store is not."""
        held = copy.deepcopy(self.observed)
        held["records"]["terminal"]["_opener"]["only_sqlite_sidecars"] = False
        self.assertIn("the read created NOTHING BUT SQLite's own WAL machinery",
                      self.verify.judge(held).failed)

    def test_SQLITE_sidecars_alone_do_NOT_fail_the_run(self):
        """The check must be satisfiable by a CORRECT read-only opener: on a
        WAL-mode store it necessarily creates them."""
        held = copy.deepcopy(self.observed)
        held["records"]["terminal"]["_opener"].update(
            {"sidecars_created": ["-wal", "-shm"],
             "sidecars_unchanged": False, "only_sqlite_sidecars": True})
        self.assertEqual(self.verify.judge(held).failed, [])


class TheSEALIsCLASSIFIEDRatherThanRewritten(VerifierCase):
    """Review202028: state the post-build seal limitation and classify whether
    the existing immutable image/build records corroborate inputs, "without
    rewriting the seal.\""""

    def test_the_IMAGE_being_corroborated_is_REQUIRED(self):
        self.refuses(["provenance", "image_identity"],
                     {"corroborated": False},
                     "the sealed image is corroborated by the BUILD's own "
                     "record")

    def test_a_MISSING_provenance_classification_is_refused(self):
        held = copy.deepcopy(self.observed)
        del held["provenance"]
        self.assertIn("the sealed image is corroborated by the BUILD's own "
                      "record", self.verify.judge(held).failed)

    def test_UNATTESTED_INPUTS_do_not_fail_the_completed_run(self):
        """The run happened; this is how well it is attested. Folding the two
        together would make an evidence limitation look like a lifecycle
        failure."""
        self.assertEqual(self.judged().failed, [])

    def test_but_the_INPUT_limitation_stays_VISIBLE(self):
        """As a DIAGNOSTIC, which is where review202123 placed it: "Input
        attestation is separately documented evidence quality." It was briefly
        a readiness precondition, which conflated an unattested build with an
        inability to act."""
        checks = self.judged()
        self.assertIn("the sealed image INPUTS are independently attested",
                      [one["observation"] for one in checks.diagnostics])
        self.assertNotIn("the sealed image INPUTS are independently attested",
                         checks.readiness_failed)

    def test_the_classification_reads_the_BUILD_S_OWN_record(self):
        """Not the seal read back to itself -- that is the current-to-current
        defect an earlier review already rejected."""
        found = self.verify.classify_provenance()
        self.assertIn("fixture.iid", found["image_identity"]["by"])
        self.assertTrue(found["image_identity"]["record_predates_the_seal"])

    def test_it_states_the_POST_BUILD_limitation_plainly(self):
        found = self.verify.classify_provenance()
        self.assertFalse(found["seal"]["rewritten"])
        self.assertIn("after the build", found["seal"]["what_it_does_not_prove"])
        self.assertFalse(found["image_inputs"]["corroborated"])

    def test_the_recipe_digests_are_NOT_called_attestation(self):
        """They record what the author intended to carry."""
        found = self.verify.classify_provenance()
        self.assertFalse(found["recipe_attribution"]["is_attestation"])

    def test_the_real_classification_matches_the_real_seal(self):
        """Run against this episode's actual files, so a drift in either is a
        failing case rather than a stale sentence in a dossier."""
        found = self.verify.classify_provenance()
        self.assertTrue(found["image_identity"]["corroborated"])
        self.assertEqual(found["image_identity"]["build_record"],
                         found["image_identity"]["sealed"])


class READYIsSATISFIABLEAndTurnsOnlyOnPRECONDITIONS(VerifierCase):
    """Review202123 [R1]: `ready` could never be true.

    THE DEFECT, IN MY OWN INSTRUMENT. `judge` recorded BOTH
    `current == configured` and `current == configured + 1` as readiness
    requirements and `ready` was `not readiness_failed`. Those are mutually
    exclusive for any consistent pair of readings, so no destination could ever
    report ready -- the reviewer's probes showed configured 23 / current 23
    failing the advance and configured 23 / current 24 failing equality, with
    every historical required check passing in both.

    A REPORTER THAT CAN ONLY EVER SAY NO IS NOT REPORTING. These cases exist so
    that cannot come back: one proves ready is reachable, one proves it still
    turns off for the real mismatch, and one proves the historical diagnostic
    cannot move it in either direction.
    """

    def consistent(self):
        """Matching generations and complete evidence -- a destination that
        genuinely could authorize another action."""
        held = copy.deepcopy(self.observed)
        held["pin"] = {"configured_pin": 23, "authority_generation": 23,
                       "equal": True}
        held["provenance"]["image_inputs"] = {"corroborated": True}
        return held

    def test_a_CONSISTENT_destination_reports_READY(self):
        checks = self.verify.judge(self.consistent())
        self.assertEqual(checks.readiness_failed, [],
                         "ready is unreachable; the two generation checks are "
                         "mutually exclusive again")

    def test_and_it_is_ACCEPTED_too(self):
        self.assertEqual(self.verify.judge(self.consistent()).failed, [])

    def test_the_REVIEWERS_FIRST_PROBE_now_reports_ready(self):
        """configured 23 / current 23, image inputs corroborated: their probe
        reported no required failures but readiness failing the one-step
        advance."""
        checks = self.verify.judge(self.consistent())
        self.assertEqual(checks.failed, [])
        self.assertEqual(checks.readiness_failed, [])

    def test_the_REVIEWERS_SECOND_PROBE_fails_ONLY_readiness(self):
        """configured 23 / current 24: their probe reported no required
        failures but readiness failing pin equality. Equality failing is
        correct; what was wrong was that the other probe failed too."""
        held = self.consistent()
        held["pin"] = {"configured_pin": 23, "authority_generation": 24,
                       "equal": False}
        checks = self.verify.judge(held)
        self.assertEqual(checks.failed, [])
        self.assertEqual(checks.readiness_failed,
                         ["the deployment could authorize a NEW action"])

    def test_a_MISMATCHED_pin_still_turns_readiness_OFF(self):
        """The negative: making ready reachable must not make it meaningless."""
        held = self.consistent()
        held["pin"] = {"configured_pin": 9, "authority_generation": 10,
                       "equal": False}
        held["owned"]["receipt"]["decision"] = {"policy_generation": 9}
        checks = self.verify.judge(held)
        self.assertIn("the deployment could authorize a NEW action",
                      checks.readiness_failed)
        self.assertEqual(checks.failed, [])

    def test_the_two_generation_checks_are_NOT_both_preconditions(self):
        """The structural assertion, so this cannot regress by someone moving
        one line: at most ONE generation comparison may be a readiness check."""
        checks = self.verify.judge(self.consistent())
        preconditions = [one["check"] for one in checks.held
                         if one.get("kind") == "readiness"]
        self.assertNotIn("the advance is the ONE STEP a single integration "
                         "makes", preconditions)

    # -- the diagnostic enters NEITHER verdict -------------------------------

    def test_the_ONE_STEP_observation_is_a_DIAGNOSTIC(self):
        kinds = {one["check"]: one.get("kind")
                 for one in self.judged().held}
        self.assertEqual(kinds["the advance is the ONE STEP a single "
                               "integration makes"], "diagnostic")

    def test_changing_ONLY_the_diagnostic_cannot_flip_READINESS(self):
        """Review202123: "ensure changing only the historical one-step
        diagnostic cannot flip readiness"."""
        ready = self.consistent()                     # advance does NOT hold
        broken = copy.deepcopy(ready)
        broken["pin"] = {"configured_pin": 23, "authority_generation": 24,
                         "equal": True}               # advance DOES hold
        self.assertEqual(self.verify.judge(ready).readiness_failed,
                         self.verify.judge(broken).readiness_failed)

    def test_changing_ONLY_the_diagnostic_cannot_flip_ACCEPTANCE(self):
        ready = self.consistent()
        broken = copy.deepcopy(ready)
        broken["pin"] = {"configured_pin": 23, "authority_generation": 24,
                         "equal": True}
        self.assertEqual(self.verify.judge(ready).failed,
                         self.verify.judge(broken).failed)

    def test_the_diagnostic_is_still_MEASURED_and_REPORTED(self):
        """Outside both verdicts is not the same as discarded."""
        checks = self.verify.judge(self.consistent())
        observed = {one["observation"]: one["held"]
                    for one in checks.diagnostics}
        self.assertIn("the advance is the ONE STEP a single integration makes",
                      observed)
        self.assertFalse(observed["the advance is the ONE STEP a single "
                                  "integration makes"])

    def test_INPUT_ATTESTATION_is_evidence_quality_and_not_readiness(self):
        """Review202123: "Input attestation is separately documented evidence
        quality." A stale pin and an unattested build are unrelated facts."""
        held = self.consistent()
        held["provenance"]["image_inputs"] = {"corroborated": False}
        checks = self.verify.judge(held)
        self.assertEqual(checks.readiness_failed, [])
        self.assertIn("the sealed image INPUTS are independently attested",
                      [one["observation"] for one in checks.diagnostics])

    # -- the language ---------------------------------------------------------

    def test_readiness_does_NOT_claim_every_future_action_fails(self):
        held = self.consistent()
        held["pin"] = {"configured_pin": 23, "authority_generation": 24,
                       "equal": False}
        detail = [one["detail"] for one in self.verify.judge(held).held
                  if one["check"] == "the deployment could authorize a NEW "
                                     "action"][0]
        self.assertIn("ONE checked precondition",
                      detail["what_a_false_here_means"])
        self.assertIn("not all traced", detail["what_a_false_here_means"])

    def test_the_provenance_diagnostic_keeps_the_STANDING_limitation(self):
        detail = [one["detail"] for one in self.judged().held
                  if one["check"] == "the sealed image INPUTS are "
                                     "independently attested"][0]
        self.assertIn("NOT approval to deploy", detail["the_standing_limitation"])
