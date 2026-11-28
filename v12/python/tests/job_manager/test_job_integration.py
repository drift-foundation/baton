"""W385263 / M386422: the owner's integration receipt for an ordinary Job; W386746: the owner's decline.

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
from baton_v12.job_manager import JobStore, job_integration, status, submit
from baton_v12.job_manager.delegation import Unobserved
from tools import job_observation

if __package__:
    from .fixtures import NOW, UUID, JobManagerCase, submission
else:
    from fixtures import NOW, UUID, JobManagerCase, submission

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


REASON = "W386632 field-test probe; not imported (field-run-m386714/RESULT.md)"
COMMIT = "6540775d5f29bea86f71756486c092be9d0a3ccd"


class TheOwnerDeclinesTheIntegrationOfItsAcceptedCandidate(JobManagerCase):
    """W386746 (owner ruling 2026-11-28): decline-integration is FINAL for the Job and bound to the Job, its
    accepted candidate and the owner's reason; one disposition per Job, also when the two acts race."""

    def setUp(self):
        super().setUp()
        self.jobs = self.store()
        self.addCleanup(self.jobs.close)
        submit(self.jobs, submission())

    def decline(self, store=None, candidate=HEAD, reason=REASON):
        with mock.patch.object(job_integration, "accepted_candidate", return_value=(PHASES, verdict())):
            return job_integration.decline(store or self.jobs, "job-a", candidate=candidate, reason=reason, actor=ACTOR,
                                           operations=Unobserved(), control=None)

    def record(self, store=None, commit=COMMIT):
        with mock.patch.object(job_integration, "accepted_candidate", return_value=(PHASES, verdict())):
            return job_integration.record(store or self.jobs, "job-a", candidate=HEAD, target={"commit": commit, "tree": TREE},
                                          actor=ACTOR, operations=Unobserved(), control=None)

    def journal(self, store=None):
        return (store or self.jobs)._connection.execute(
            "SELECT kind, state FROM operations WHERE kind IN (?, ?)", (job_integration.KIND, job_integration.DECLINE_KIND)).fetchall()

    def test_the_receipt_binds_the_job_its_accepted_candidate_and_the_reason(self):
        receipt = self.decline()
        self.assertEqual(receipt["action"], "decline-integration")
        self.assertEqual(receipt["job_id"], "job-a")
        self.assertEqual(receipt["reason"], REASON)
        self.assertEqual(receipt["recorded_by"], ACTOR)
        self.assertEqual(receipt["candidate"], {"checkpoint_id": "checkpoint-a", "line_id": "line-a", "verdict_id": "verdict-a",
                                                "base_object": verdict()["base_object"], "head_object": HEAD, "tree_object": TREE,
                                                "review_attempt_id": "attempt-review"})
        self.assertEqual(receipt["phases"], PHASES)
        self.assertEqual(receipt["operation_id"], job_integration.operation_of("job-a"))
        self.assertEqual(job_integration.declined_of(self.jobs, "job-a"), receipt)
        self.assertIsNone(job_integration.receipt_of(self.jobs, "job-a"))

    def test_an_IDENTICAL_retry_returns_the_original_receipt_also_after_a_restart(self):
        first = self.decline()
        self.instants.append("2026-11-28T05:00:00.000Z")
        self.assertEqual(self.decline(), first)
        self.jobs.close()
        reopened = self.store(incarnation="jobs-2")
        self.addCleanup(reopened.close)
        self.jobs = reopened
        self.assertEqual(self.decline(), first)
        self.assertEqual(job_integration.declined_of(reopened, "job-a"), first)
        self.assertEqual([tuple(row) for row in self.journal()], [(job_integration.DECLINE_KIND, "committed")])

    def test_a_CONFLICTING_decision_is_refused_and_names_the_existing_disposition(self):
        first = self.decline()
        for label, call in (("another reason", lambda: self.decline(reason="changed my mind")),
                            ("another candidate", lambda: self.decline(candidate="2" * 40)),
                            ("record-integration", lambda: self.record())):
            with self.subTest(label), self.assertRaises(ContractRefusal) as refused:
                call()
            said = str(refused.exception)
            self.assertIn("integration was already declined by baton.slaw", said)
            self.assertIn("candidate " + HEAD, said)
            self.assertIn(REASON, said)
        self.assertEqual(job_integration.declined_of(self.jobs, "job-a"), first)
        self.assertIsNone(job_integration.receipt_of(self.jobs, "job-a"))
        self.assertEqual(len(self.journal()), 1)

    def test_a_decline_after_an_integration_is_refused_and_names_the_integration(self):
        integrated = self.record()
        with self.assertRaises(ContractRefusal) as refused:
            self.decline()
        self.assertIn("already has an integration receipt (candidate " + HEAD + ", commit " + COMMIT + ")", str(refused.exception))
        self.assertEqual(job_integration.receipt_of(self.jobs, "job-a"), integrated)
        self.assertIsNone(job_integration.declined_of(self.jobs, "job-a"))

    def test_when_the_two_RACE_exactly_one_succeeds_and_the_other_names_it(self):
        import threading
        for first, second in (("record", "decline"), ("decline", "record"), ("decline", "decline-other")):
            with self.subTest(race=(first, second)):
                self.jobs.close()
                self.setUp()
                both_checked = threading.Barrier(2, timeout=20)
                answers = {}

                def accepted(*_args, **_kwargs):
                    both_checked.wait()          # both callers are past every precondition before either commits
                    return PHASES, verdict()

                def act(name, incarnation):
                    # Opened AND closed in this thread: a SQLite connection belongs to its thread.
                    store = JobStore.open(self.job_path, authority_uuid=UUID, incarnation=incarnation, clock=self.clock)
                    try:
                        if name == "record":
                            answers[name] = job_integration.record(store, "job-a", candidate=HEAD, target={"commit": COMMIT, "tree": TREE},
                                                                   actor=ACTOR, operations=Unobserved(), control=None)
                        else:
                            answers[name] = job_integration.decline(store, "job-a", candidate=HEAD,
                                                                    reason=REASON if name == "decline" else "another reason",
                                                                    actor=ACTOR, operations=Unobserved(), control=None)
                    except ContractRefusal as refusal:
                        answers[name] = refusal
                    finally:
                        store.close()

                with mock.patch.object(job_integration, "accepted_candidate", side_effect=accepted):
                    threads = [threading.Thread(target=act, args=(name, "racer-" + name)) for name in (first, second)]
                    for one in threads:
                        one.start()
                    for one in threads:
                        one.join(30)
                won = [name for name, answer in answers.items() if not isinstance(answer, ContractRefusal)]
                lost = [name for name, answer in answers.items() if isinstance(answer, ContractRefusal)]
                self.assertEqual(len(won), 1, answers)
                self.assertEqual(len(lost), 1, answers)
                said = str(answers[lost[0]])
                if won[0] == "record":
                    self.assertIn("already has an integration receipt", said)
                else:
                    self.assertIn("integration was already declined", said)
                self.assertEqual(len(self.journal()), 1)
                self.assertEqual(self.journal()[0]["state"], "committed")

    def test_a_missing_or_padded_reason_or_a_bad_candidate_records_nothing(self):
        for label, changed in (("empty", dict(reason="")), ("padded", dict(reason=" " + REASON)),
                               ("too long", dict(reason="x" * 1001)), ("not a reason", dict(reason=7)),
                               ("short candidate", dict(candidate=HEAD[:8])), ("not the accepted head", dict(candidate="3" * 40))):
            with self.subTest(label), self.assertRaises(ContractRefusal):
                self.decline(**changed)
        self.assertEqual(self.journal(), [])

    def test_NOT_INTEGRATED_is_read_from_the_receipt_with_every_service_stopped(self):
        before = status(self.jobs, Unobserved(), observed_at=NOW)
        self.assertNotIn("integration_declined", before["jobs"][0])
        receipt = self.decline()
        self.jobs.close()
        self.jobs = self.store(incarnation="after-restart")
        self.addCleanup(self.jobs.close)
        document = status(self.jobs, Unobserved(), observed_at=NOW)
        job = next(one for one in document["jobs"] if one["job_id"] == "job-a")
        self.assertEqual(job["integration_declined"], receipt)
        self.assertNotIn("integration", job)
        self.assertNotIn("integration_declined", next(one for one in document["jobs"] if one["job_id"] == "job-b"))
        view = job_observation.job_view(document, job)
        self.assertEqual(view["headline"], "NOT INTEGRATED")
        self.assertEqual(view["headline_reason"],
                         "Owner declined to integrate accepted candidate " + HEAD + "; reason: \"" + REASON
                         + "\"; checkpoint checkpoint-a; recorded by baton.slaw at " + receipt["recorded_at"] + ".")
        self.assertEqual(view["integration_declined"], receipt)
        self.assertIsNone(view["integration"])


class TheOwnerCommandsTakeTheirOwnOperands(unittest.TestCase):
    """W386746: `manager decline-integration` takes --reason and no target; `record-integration` the reverse."""

    def refused(self, argv):
        import contextlib, io
        from tools import job_integration_command
        with contextlib.redirect_stderr(io.StringIO()) as said, self.assertRaises(SystemExit) as stopped:
            job_integration_command.main(argv)
        self.assertEqual(stopped.exception.code, 2)
        return said.getvalue()

    def test_each_verb_refuses_the_other_verbs_operands_before_opening_anything(self):
        common = ["--instance", "/nonexistent/instance.json", "--job", "job-a", "--candidate", HEAD]
        self.assertIn("decline-integration takes --reason", self.refused(["decline-integration", *common]))
        self.assertIn("decline-integration takes --reason", self.refused(["decline-integration", *common, "--reason", REASON, "--commit", COMMIT]))
        self.assertIn("record-integration takes --commit and --repository", self.refused(["record-integration", *common, "--commit", COMMIT]))
        self.assertIn("record-integration takes --commit and --repository",
                      self.refused(["record-integration", *common, "--commit", COMMIT, "--repository", "/r", "--reason", REASON]))

    def test_the_manager_routes_decline_integration_to_the_owner_command(self):
        from tools import job_integration_command, job_manager
        with mock.patch.object(job_integration_command, "main", return_value=0) as called:
            self.assertEqual(job_manager.main(["decline-integration", "--instance", "/x", "--job", "job-a"]), 0)
        self.assertEqual(called.call_args.args[0][0], "decline-integration")


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
