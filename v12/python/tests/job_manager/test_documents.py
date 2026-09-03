"""W71875 — the submission document, owned member by member.

The submission is the ONE thing an operator hands this control plane, so
everything a later stage would have to guess at is decided here: the schema
and its version, a closed member set, closed vocabularies, dependencies that
resolve inside the submission, and a graph with no cycle. A defect admitted
here becomes durable rows and a pipeline nobody can explain.
"""

import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import (STAGE_KINDS, SUBMISSION_SCHEMA,
                                   owned_submission, read_submission,
                                   stage_id, submission_signature)

# THE SAME FIXTURES, FROM EITHER DISCOVERY ROOT. The distribution's gate runs
# `unittest discover -s tests -t .` from `v12/python`, where this file is
# `tests.job_manager.test_documents`; this Work's focused vector roots
# discovery at THIS directory, where it is a top-level module with no package
# at all. `__package__` answers which exactly, and catching `ImportError`
# instead would also swallow a genuine failure inside the fixtures.
if __package__:
    from .fixtures import WORK_A, WORK_B, job, stage, submission
else:
    from fixtures import WORK_A, WORK_B, job, stage, submission


class SubmissionShape(unittest.TestCase):

    def refusal(self, document):
        with self.assertRaises(ContractRefusal) as caught:
            owned_submission(document)
        return caught.exception

    def test_the_default_submission_is_owned_whole(self):
        owned = owned_submission(submission())
        self.assertEqual(owned["schema"], SUBMISSION_SCHEMA)
        self.assertEqual([one["job_id"] for one in owned["jobs"]],
                         ["job-a", "job-b"])
        self.assertEqual([one["kind"] for one in owned["jobs"][0]["stages"]],
                         ["implementation", "review"])

    def test_an_unrecognised_schema_is_refused_rather_than_read_as_ours(self):
        document = submission()
        document["schema"] = "baton.v12.job-submission/2"
        refusal = self.refusal(document)
        self.assertEqual((refusal.category, refusal.code),
                         ("integrity", "schema"))

    def test_a_member_this_build_does_not_name_is_refused_not_ignored(self):
        document = submission()
        document["priority"] = "high"
        self.refusal(document)

    def test_a_missing_member_is_named(self):
        document = submission()
        del document["jobs"]
        self.assertIn("jobs", self.refusal(document).message)

    def test_an_empty_submission_carries_no_pipeline(self):
        self.refusal(submission(jobs=[]))

    def test_a_stage_kind_outside_the_vocabulary_is_refused(self):
        self.refusal(submission(jobs=[job(stages=[stage(kind="tuning")])]))

    def test_a_terminal_policy_outside_the_vocabulary_is_refused(self):
        self.refusal(submission(jobs=[job(terminal_policy="auto-accept")]))

    def test_the_bounded_test_scope_travels_with_the_job(self):
        owned = owned_submission(submission(jobs=[
            job(test_scope=["v12/python/tests/job_manager",
                            "v12/python/tests/manager/test_offers.py"])]))
        self.assertEqual(owned["jobs"][0]["test_scope"],
                         ["v12/python/tests/job_manager",
                          "v12/python/tests/manager/test_offers.py"])

    def test_a_job_with_no_test_scope_is_ordinary(self):
        owned = owned_submission(submission(jobs=[job(test_scope=[])]))
        self.assertEqual(owned["jobs"][0]["test_scope"], [])

    def test_a_test_scope_entry_is_a_repository_path_not_prose(self):
        """Review [P1]: each entry was owned as text alone.

        The scope IS the bounded test-change authority a later reviewer and
        integrator check a proposal's changed paths against, so an entry that
        climbs out of the repository, names an absolute location or spells one
        place two ways is an authority nobody can evaluate. Every spelling
        below was ACCEPTED UNCHANGED by the reviewed candidate.
        """
        for spoiled in ("../outside.py", "/absolute.py", "v12//dup.py",
                        "v12/./same.py", "v12/../escape.py", "",
                        "v12\\windows.py", "v12/tests\0.py", "./here.py",
                        "..", "v12/tests/"):
            with self.subTest(path=spoiled):
                refusal = self.refusal(
                    submission(jobs=[job(test_scope=[spoiled])]))
                self.assertEqual((refusal.category, refusal.code),
                                 ("integrity", "path"),
                                 "the existing public repository-path "
                                 "contract is what refuses this, so its own "
                                 "code is what an operator sees")

    def test_a_test_scope_entry_that_is_not_text_is_refused(self):
        for spoiled in (None, 1, True, ["v12/tests"], {"path": "v12/tests"}):
            with self.subTest(path=spoiled):
                self.refusal(submission(jobs=[job(test_scope=[spoiled])]))

    def test_one_scope_set_has_one_spelling_of_each_path(self):
        refusal = self.refusal(submission(jobs=[job(test_scope=[
            "v12/python/tests/job_manager",
            "v12/python/tests/job_manager"])]))
        self.assertIn("test-scope path", refusal.message)
        self.assertIn("job-a", refusal.message)

    def test_a_scope_that_is_not_a_list_is_refused(self):
        self.refusal(submission(jobs=[job(test_scope="v12/python/tests")]))

    def test_two_jobs_may_not_share_one_identity(self):
        self.refusal(submission(jobs=[job("job-a"), job("job-a")]))

    def test_one_job_may_not_carry_two_stages_of_one_kind(self):
        self.refusal(submission(jobs=[job(stages=[
            stage("implementation", WORK_A),
            stage("implementation", WORK_B)])]))

    def test_every_stage_kind_is_admitted(self):
        owned = owned_submission(submission(jobs=[job(stages=[
            stage(kind) for kind in STAGE_KINDS])]))
        self.assertEqual([one["kind"] for one in owned["jobs"][0]["stages"]],
                         list(STAGE_KINDS))


class Dependencies(unittest.TestCase):

    def refusal(self, document):
        with self.assertRaises(ContractRefusal) as caught:
            owned_submission(document)
        return caught.exception

    def test_a_dependency_on_a_stage_outside_the_submission_is_refused(self):
        refusal = self.refusal(submission(jobs=[job("job-a", stages=[
            stage("review", WORK_A,
                  depends_on=[{"job_id": "job-z",
                               "kind": "implementation"}])])]))
        self.assertIn("job-z/implementation", refusal.message)

    def test_a_stage_may_not_gate_on_itself(self):
        refusal = self.refusal(submission(jobs=[job("job-a", stages=[
            stage("implementation", WORK_A,
                  depends_on=[{"job_id": "job-a",
                               "kind": "implementation"}])])]))
        self.assertIn("itself", refusal.message)

    def test_a_cycle_is_refused_at_submission_rather_than_at_a_dead_sweep(self):
        # Nothing in a cycle is ever eligible, and submission is the one
        # moment an operator can be told WHICH stages are involved rather than
        # watching a manager report nothing to do forever.
        refusal = self.refusal(submission(jobs=[job("job-a", stages=[
            stage("implementation", WORK_A,
                  depends_on=[{"job_id": "job-a", "kind": "review"}]),
            stage("review", WORK_B,
                  depends_on=[{"job_id": "job-a",
                               "kind": "implementation"}])])]))
        self.assertIn("cycle", refusal.message)

    def test_a_cross_job_dependency_resolves(self):
        owned = owned_submission(submission(jobs=[
            job("job-a", stages=[stage("implementation", WORK_A)]),
            job("job-b", stages=[
                stage("implementation", WORK_B,
                      depends_on=[{"job_id": "job-a",
                                   "kind": "implementation"}])])]))
        self.assertEqual(owned["jobs"][1]["stages"][0]["depends_on"],
                         [{"job_id": "job-a", "kind": "implementation"}])

    def test_one_stage_may_not_name_a_dependency_twice(self):
        self.refusal(submission(jobs=[job("job-a", stages=[
            stage("implementation", WORK_A),
            stage("review", WORK_B, depends_on=[
                {"job_id": "job-a", "kind": "implementation"},
                {"job_id": "job-a", "kind": "implementation"}])])]))


class Identity(unittest.TestCase):

    def test_a_stage_is_named_by_its_job_and_its_kind(self):
        self.assertEqual(stage_id("job-a", "review"), "job-a/review")

    def test_two_spellings_of_one_intent_have_one_signature(self):
        # THE NORMALIZATION IS WHAT MAKES RESUBMISSION IDEMPOTENT. An operator
        # that re-orders members or reformats its JSON is resubmitting the
        # same intent, and a byte-keyed identity that disagreed would refuse
        # it as a conflict.
        first = submission()
        second = {"jobs": first["jobs"], "submission_id": "sub-1",
                  "schema": first["schema"]}
        self.assertEqual(submission_signature(owned_submission(first)),
                         submission_signature(owned_submission(second)))

    def test_a_changed_operand_is_a_different_signature(self):
        other = submission()
        other["jobs"][0]["input_digest"] = "sha256:" + "9" * 64
        self.assertNotEqual(
            submission_signature(owned_submission(submission())),
            submission_signature(owned_submission(other)))

    def test_submission_text_is_owned_where_it_is_decoded(self):
        import json

        owned = read_submission(json.dumps(submission()))
        self.assertEqual(owned["submission_id"], "sub-1")

    def test_text_that_does_not_decode_refuses_rather_than_faults(self):
        with self.assertRaises(ContractRefusal):
            read_submission("{not json")
