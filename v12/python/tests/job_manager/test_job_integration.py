"""W385263 / M386422: the owner's integration receipt for an ordinary Job.

The receipt is journalled in the real Job store and read back by the real
status projection with NO control store (`Unobserved`), which is exactly the
services-stopped read. The accepted-candidate precondition is the product's
own (`review_verdicts.matching` over a real review line, covered in
`test_review_verdicts`); here it is stood in by name so every refusal,
the idempotent retry and the collision can be driven directly. The target
commit is read from a real disposable Git repository.
"""
import os
import subprocess
import tempfile
import unittest
from unittest import mock

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import job_integration, status, submit
from baton_v12.job_manager.delegation import Unobserved
from tools import job_observation

if __package__:
    from .fixtures import NOW, JobManagerCase, submission
else:
    from fixtures import NOW, JobManagerCase, submission

# M386415, the field case: accepted candidate 340f8674 integrated on main as 6540775d, one tree.
HEAD = "340f867479024e6dcffec92345a2dfc5d0263189"
TREE = "35686824a2f560f9c20e80d6905873dd0c89c41e"
ACTOR = {"participant": "baton.slaw", "principal": "principal:baton.slaw"}


def verdict(**changed):
    held = {"disposition": "accepted", "verdict_id": "verdict-a", "attachment_id": "review-a",
            "attempt_id": "attempt-review", "checkpoint_id": "checkpoint-a", "line_id": "line-a",
            "base_object": "6ac23589f24aa94fe8cfd9cb7d79eb57d78d061c", "head_object": HEAD,
            "tree_object": TREE, "importable": True}
    held.update(changed)
    return held


PHASES = [{"stage_id": "job-a/implementation", "state": "completed", "attempt_id": "attempt-impl"},
          {"stage_id": "job-a/review", "state": "completed", "attempt_id": "attempt-review"}]


class TheOwnerRecordsTheIntegrationOfItsAcceptedCandidate(JobManagerCase):
    def setUp(self):
        super().setUp()
        self.jobs = self.store()
        self.addCleanup(self.jobs.close)
        submit(self.jobs, submission())

    def record(self, candidate=HEAD, commit="6540775d5f29bea86f71756486c092be9d0a3ccd", tree=TREE, accepted=None):
        with mock.patch.object(job_integration, "accepted_candidate",
                               return_value=(PHASES, accepted if accepted is not None else verdict())):
            return job_integration.record(self.jobs, "job-a", candidate=candidate, target={"commit": commit, "tree": tree},
                                          actor=ACTOR, operations=Unobserved(), control=None)

    def journal(self):
        return self.jobs._connection.execute("SELECT count(*) FROM operations WHERE kind=?",
                                             (job_integration.KIND,)).fetchone()[0]

    def test_unfinished_phases_are_refused_by_the_real_precondition_and_record_nothing(self):
        with self.assertRaises(ContractRefusal) as refused:
            job_integration.record(self.jobs, "job-a", candidate=HEAD, target={"commit": "6540775d5f29bea86f71756486c092be9d0a3ccd", "tree": TREE},
                                   actor=ACTOR, operations=Unobserved(), control=None)
        self.assertIn("have not finished", str(refused.exception))
        with self.assertRaises(ContractRefusal) as unknown:
            job_integration.record(self.jobs, "job-z", candidate=HEAD, target={"commit": "6540775d5f29bea86f71756486c092be9d0a3ccd", "tree": TREE},
                                   actor=ACTOR, operations=Unobserved(), control=None)
        self.assertIn("no ordinary Job job-z", str(unknown.exception))
        self.assertEqual(self.journal(), 0)
        self.assertIsNone(job_integration.receipt_of(self.jobs, "job-a"))

    def test_the_receipt_persists_and_an_IDENTICAL_retry_returns_it_unchanged(self):
        first = self.record()
        self.assertEqual(first["candidate"]["head_object"], HEAD)
        self.assertEqual(first["target"], {"commit": "6540775d5f29bea86f71756486c092be9d0a3ccd", "tree": TREE})
        self.assertEqual(first["recorded_by"], ACTOR)
        self.assertEqual(first["phases"], PHASES)
        self.instants.append("2026-11-26T19:00:00.000Z")
        self.assertEqual(self.record(), first)
        self.assertEqual(self.journal(), 1)
        self.assertEqual(job_integration.receipt_of(self.jobs, "job-a"), first)

    def test_a_CONFLICTING_receipt_and_a_MISMATCHED_candidate_are_refused(self):
        first = self.record()
        for label, call in (("another commit", lambda: self.record(commit="1" * 40)),
                            ("another candidate", lambda: self.record(candidate="2" * 40))):
            with self.subTest(label), self.assertRaises(ContractRefusal) as refused:
                call()
            self.assertIn("already has an integration receipt", str(refused.exception))
        self.assertEqual(job_integration.receipt_of(self.jobs, "job-a"), first)
        self.assertEqual(self.journal(), 1)

    def test_a_candidate_that_is_not_the_accepted_one_or_a_foreign_tree_records_nothing(self):
        cases = (("not the accepted head", dict(candidate="3" * 40), "is not Job job-a's accepted candidate"),
                 ("another tree", dict(tree="4" * 40), "exact-tree integrations only"))
        for label, changed, words in cases:
            with self.subTest(label), self.assertRaises(ContractRefusal) as refused:
                self.record(**changed)
            self.assertIn(words, str(refused.exception))
        self.assertEqual(self.journal(), 0)

    def test_DONE_is_read_from_the_receipt_with_every_service_stopped(self):
        before = status(self.jobs, Unobserved(), observed_at=NOW)
        self.assertNotIn("integration", before["jobs"][0])
        receipt = self.record()
        document = status(self.jobs, Unobserved(), observed_at=NOW)
        job = next(one for one in document["jobs"] if one["job_id"] == "job-a")
        self.assertEqual(job["integration"], receipt)
        self.assertNotIn("integration", next(one for one in document["jobs"] if one["job_id"] == "job-b"))
        view = job_observation.job_view(document, job)
        self.assertEqual(view["headline"], "DONE")
        self.assertIn("Integrated as 6540775d5f29bea86f71756486c092be9d0a3ccd from accepted candidate " + HEAD, view["headline_reason"])
        self.assertEqual(view["integration"], receipt)


class TheTargetCommitMustExist(unittest.TestCase):
    def setUp(self):
        room = tempfile.TemporaryDirectory(prefix="v12-w385263-target-")
        self.addCleanup(room.cleanup)
        self.repository = os.path.join(room.name, "target")
        environment = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": room.name, "GIT_CONFIG_NOSYSTEM": "1",
                       "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
                       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid"}
        def git(*argv):
            return subprocess.run(["git", "-C", self.repository, *argv], env=environment, check=True,
                                  capture_output=True, text=True).stdout.strip()
        self.git = git
        os.mkdir(self.repository)
        git("init", "-q")
        with open(os.path.join(self.repository, "file"), "w") as handle:
            handle.write("candidate\n")
        git("add", "file")
        git("commit", "-q", "-m", "integrated")
        self.commit, self.tree = git("rev-parse", "HEAD"), git("rev-parse", "HEAD^{tree}")

    def test_an_existing_commit_answers_its_full_name_and_tree(self):
        self.assertEqual(job_integration.target_commit(self.repository, self.commit[:8]),
                         {"commit": self.commit, "tree": self.tree})

    def test_a_REPLACEMENT_REF_cannot_change_the_tree_a_receipt_reads(self):
        """M386429: `refs/replace/<commit>` makes ordinary Git report another
        commit's tree for the target. The receipt reads the literal objects."""
        with open(os.path.join(self.repository, "file"), "w") as handle:
            handle.write("something else\n")
        self.git("commit", "-q", "-am", "decoy")
        decoy, decoy_tree = self.git("rev-parse", "HEAD"), self.git("rev-parse", "HEAD^{tree}")
        self.assertNotEqual(decoy_tree, self.tree)
        self.git("replace", self.commit, decoy)
        self.assertEqual(self.git("rev-parse", self.commit + "^{tree}"), decoy_tree,
                         "the fixture's replacement really changes what ordinary Git reports")
        self.assertEqual(job_integration.target_commit(self.repository, self.commit),
                         {"commit": self.commit, "tree": self.tree})
        with mock.patch.dict(os.environ, {"GIT_NO_REPLACE_OBJECTS": "", "GIT_DIR": "/nonexistent"}):
            self.assertEqual(job_integration.target_commit(self.repository, self.commit),
                             {"commit": self.commit, "tree": self.tree})

    def test_an_absent_commit_a_relative_repository_or_a_bad_name_is_refused(self):
        for repository, commit in ((self.repository, "f" * 40), ("relative/path", self.commit), (self.repository, "HEAD~1"),
                                   (self.repository, "--all")):
            with self.subTest(repository=repository, commit=commit), self.assertRaises(ContractRefusal):
                job_integration.target_commit(repository, commit)


if __name__ == "__main__":
    unittest.main()
