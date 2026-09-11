"""W133117: the integration RESULT, proved against the real things it owns.

INTEGRATION-CONTRACT-v1 sections 1 to 5. A submission is the producer's
ORIGINAL proposal on its ORIGINAL base; a result is that submission reconciled
with one pinned target snapshot, and it earns its OWN content, evidence,
review, approval and derived Authority proposal.

WHAT IS REAL HERE AND WHY. The dossier requires readers, cutpoints and result
preparation proved with real repositories and a real Authority/session in at
least one focused path, so these cases run actual Git against actual
repositories, an actual `IntegrationStore` and an actual `Authority` -- with a
real producer proposal, its three real policy receipts, and an actually
claimed integration assignment. The causal observations in
`CausalEvidenceSurvivesComposition` are the exit statuses of one pinned
harness actually executed against three content states.

WHAT IS SUBSTITUTED, AND WHY IT IS THE HONEST BOUNDARY. The Worker Manager's
checkpoint/writer/frozen-output readers and the Job store's rows are patched
the way `test_admission` patches them: those owners are W71918's and W101491's
and have their own cases, and P's accepted scope does not include standing up
a manager fixture. Everything admission CROSS-BINDS between them still runs.
"""

import copy
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

from baton_v12.authority import Authority
from baton_v12.authority.errors import Refusal as AuthorityRefusal
from baton_v12.contracts import ContractRefusal, digest
from baton_v12.integration import (TARGET_SCHEMA, IntegrationStore,
                                   activate_target, admission, reconciliation)
from baton_v12.integration.git_profile import (GitIntegrationProfile,
                                               IntegrationProfileRefusal)
from baton_v12.source_profiles import GIT_PROFILE

NOW = "2026-09-10T05:00:00.000Z"
UUID = "0123456789abcdef0123456789abcdef"
WORK = "0123456f-W133117"
TARGET = "target:mainline"
REFERENCE = "refs/baton/integration/target"
PRODUCER = "baton.producer"
INTEGRATOR = "baton.integrator"
# The SUBMISSION's own three policy receipts, and the RESULT's own three
# independent owners. They are deliberately different participants: a result's
# evidence is about bytes that did not exist when the submission was judged.
SOURCE_OWNERS = {"verification": "baton.source-verify",
                 "review": "baton.source-review",
                 "approval": "baton.source-approve"}
RESULT_OWNERS = {"verification": "baton.result-verify",
                 "review": "baton.result-review",
                 "approval": "baton.result-approve"}
TEST_SCOPE = ["v12/python/tests/integration"]
SUBPROCESS_TIMEOUT = 120

# GIT WITH NO AMBIENT CONFIGURATION. The profile's whole claim is that it
# writes in two nominated places and nowhere else, so a case that let it read
# this machine's user configuration would be proving something about this
# machine. The instants are pinned too: a commit whose identity moved between
# two runs would make every derived result identity here unrepeatable.
ENV = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": "/nonexistent",
       "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull,
       "GIT_TERMINAL_PROMPT": "0",
       "GIT_AUTHOR_NAME": "Integration Case",
       "GIT_AUTHOR_EMAIL": "case@invalid",
       "GIT_COMMITTER_NAME": "Integration Case",
       "GIT_COMMITTER_EMAIL": "case@invalid",
       "GIT_AUTHOR_DATE": "2026-09-10T05:00:00+00:00",
       "GIT_COMMITTER_DATE": "2026-09-10T05:00:00+00:00"}

# THE DEFECT, ITS FIX, AND THE HARNESS THAT SEES BOTH.
#
# `total` drops the first value. Job B fixes it and brings the regression
# harness with it, so the harness is a file that does NOT exist on the old
# base -- which is exactly the situation section 4 rules on: pin the harness
# once and run that SAME harness against all three content states rather than
# pretending a test absent from the base ever ran there.
DEFECT = ("from scale import SCALE\n\n\n"
          "def total(values):\n"
          "    return sum(values[1:]) * SCALE\n")
FIXED = ("from scale import SCALE\n\n\n"
         "def total(values):\n"
         "    return sum(values) * SCALE\n")
HARNESS = ("from feature import total\n\n"
           "answered = total([1, 2, 3])\n"
           "assert answered == 6, f'total answered {answered}'\n"
           "print('the regression harness passed')\n")
HARNESS_IDENTITY = "regression/total-keeps-the-first-value"


def _run(argv, cwd=None):
    return subprocess.run(list(argv), capture_output=True, text=True, env=ENV,
                          cwd=cwd, timeout=SUBPROCESS_TIMEOUT)


def runner(argv):
    """The profile's ONLY way to reach a subprocess."""
    answered = _run(argv)
    return {"returncode": answered.returncode, "stdout": answered.stdout,
            "stderr": answered.stderr}


class Owner:
    """One configured, scoped evidence owner.

    IT IS ASKED AND IT ANSWERS. The record derives the question; this answers
    about exactly what it was asked, under its own participant. The variants
    below are what a MISCONFIGURED or dishonest owner does, and each of them
    is a case rather than a description.
    """

    def __init__(self, participant, kind, *, about=None, disposition=None,
                 actor=None):
        self.participant = participant
        self._kind = kind
        self._about = about or {}
        self._disposition = disposition
        self._actor = actor
        self.asked = []
        setattr(self, {"verification": "verify", "review": "review",
                       "approval": "approve"}[kind], self._answer)

    def _answer(self, basis):
        self.asked.append(copy.deepcopy(basis))
        given = dict(basis)
        given.update(self._about)
        return {"kind": self._kind,
                "identity": f"{self._kind}-of-{basis['result_id']}",
                "actor": self._actor or self.participant,
                "disposition": self._disposition or
                {"verification": "passed", "review": "accepted",
                 "approval": "approved"}[self._kind],
                "result_id": given["result_id"],
                "content_digest": given["content_digest"],
                "candidate": given["candidate"],
                "target": given["target"]}


class ResultCase(unittest.TestCase):
    """One base target, one producer line that never rebases, one first Job
    that integrates ahead of it, and the owners that answer for the second.

    THE SHAPE IS W131409'S OWN. Job B commits on the base, Job A integrates,
    the dedicated target's configured reference advances, and B's submission
    is now behind: unchanged, still accepted, and unable to import directly.
    """

    def setUp(self):
        self._root = tempfile.TemporaryDirectory(prefix="v12-reconciliation-")
        self.addCleanup(self._root.cleanup)
        self.root = self._root.name

        self.target = self.repository("target")
        self.write(self.target, "feature.py", DEFECT)
        self.write(self.target, "scale.py", "SCALE = 1\n")
        self.write(self.target, "other.py", "MESSAGE = 'the base'\n")
        self.record(self.target, "the base")
        self.base = self.git(self.target, "rev-parse", "HEAD")
        self.git(self.target, "update-ref", REFERENCE, self.base)

        # Job B's ORIGINAL submission, on the ORIGINAL base.
        self.line = os.path.join(self.root, "line-b")
        self.assertEqual(_run(["git", "clone", "-q", self.target,
                               self.line]).returncode, 0)
        self.git(self.line, "checkout", "-q", "--detach", self.base)
        self.write(self.line, "feature.py", FIXED)
        self.write(self.line, "harness.py", HARNESS)
        self.record(self.line, "job b fixes the defect")
        self.candidate = self.git(self.line, "rev-parse", "HEAD")

        # Job A integrates first, and the dedicated reference advances.
        self.advanced = self.advance("other.py",
                                     "MESSAGE = 'the first job answered'\n")

        self.workspace = self.repository("workspace", bare=True)
        self.fetch(self.candidate)

        self.authority = Authority.create(
            os.path.join(self.root, "authority.sqlite3"), authority_uuid=UUID)
        self.addCleanup(self.authority.dispose)
        self.authority.set_policy("canonical_target", self.base)
        self.authority.create_work(WORK, "impl", contract="v12-assignment-1",
                                   operation_id="create-work")
        self.authority.add_route_handler("impl", PRODUCER)
        self.authority.add_route_handler("integ", INTEGRATOR)
        producer = self.authority.session(PRODUCER)
        claimed = producer.claim({"work_id": WORK,
                                  "operation_id": "claim-producer"})
        self.producer_assignment = claimed["assignment"]
        self.original = producer.publish({
            "expect": claimed["assignment"],
            "operation_id": "publish-original",
            "proposal_id": "proposal-b1", "result_id": "result-b1",
            "result_digest": "sha256:" + "1" * 64,
            "candidate_digest": self.candidate,
            "input_digest": "sha256:" + "2" * 64,
            "policy_digest": "sha256:" + "3" * 64})
        self.issue_source_receipts()
        producer.pass_work({"expect": claimed["assignment"],
                            "operation_id": "pass-to-integ",
                            "to_route": "integ",
                            "comment": "ready for integration"})
        self.session = self.authority.session(INTEGRATOR)
        self.assignment = self.session.claim(
            {"work_id": WORK, "operation_id": "claim-integ"})["assignment"]

        self.store = IntegrationStore.open(
            os.path.join(self.root, "coordinator.sqlite3"),
            incarnation="coordinator-1", clock=lambda: NOW)
        self.addCleanup(self.store.close)
        activate_target(self.store, {"schema": TARGET_SCHEMA,
                                     "canonical_target_id": TARGET,
                                     "description": "the mainline target"})
        self.profile = GitIntegrationProfile(runner)
        self.owners = {kind: Owner(participant, kind)
                       for kind, participant in RESULT_OWNERS.items()}
        self.patch_producers()

    # -- the accepted producers admission re-reads ---------------------------

    def issue_source_receipts(self):
        """The SUBMISSION's own three receipts, written by real sessions.

        `admission` reads these through the Authority, so a proposal nobody
        published or a receipt nobody wrote is refused by the Authority itself
        rather than by a fixture that agreed to pretend.
        """
        generation = self.authority.policy_generation()
        for kind, participant in SOURCE_OWNERS.items():
            verb = {"verification": "verify", "review": "review",
                    "approval": "approve"}[kind]
            self.authority.grant_capability(participant, verb)
            session = self.authority.session(participant)
            operands = {"proposal_id": "proposal-b1",
                        "operation_id": f"source-{kind}"}
            if kind == "verification":
                operands.update(verification_id="source-verification-1",
                                observation="passed")
            elif kind == "review":
                operands.update(review_id="source-review-1",
                                disposition="accepted")
            else:
                operands.update(approval_id="source-approval-1",
                                disposition="approved",
                                policy_generation=generation)
            getattr(session, verb)(operands)

    def patch_producers(self):
        """The Worker Manager and Job rows, as `test_admission` supplies them.

        THE OBJECT NAMES ARE THE REAL ONES. The accepted checkpoint evidence
        carries this line's ACTUAL base and head, because the reconciliation
        under test resolves its Git operands from exactly here.
        """
        evidence = {"profile": GIT_PROFILE, "base": self.base,
                    "head": self.candidate,
                    "tree": self.git(self.line, "rev-parse",
                                     self.candidate + "^{tree}"),
                    "paths": ["feature.py", "harness.py"],
                    "path_set_digest": digest(["feature.py", "harness.py"]),
                    "reference": "checkpoint/line-b/1"}
        self.accepted = {"line_id": "line-b", "checkpoint_id": "checkpoint-b1",
                         "verdict_id": "verdict-b1",
                         "checkpoint_digest": digest(evidence),
                         "evidence": evidence}
        self.line_row = {"line_id": "line-b", "authority_uuid": UUID,
                         "work_id": WORK,
                         "current_checkpoint_id": "checkpoint-b1"}
        self.checkpoint = {"checkpoint_id": "checkpoint-b1",
                           "writer_id": "writer-b1", "line_id": "line-b",
                           "checkpoint_digest": digest(evidence),
                           "path_set_digest": evidence["path_set_digest"],
                           "evidence": copy.deepcopy(evidence)}
        self.writer = {"writer_id": "writer-b1", "line_id": "line-b",
                       "runtime_attempt_id": "attempt-b1",
                       "assignment_generation":
                           self.producer_assignment["generation"],
                       "participant": PRODUCER}
        self.writer_assignment = {
            "runtime_attempt_id": "attempt-b1", "authority_uuid": UUID,
            "work_id": WORK, "participant": PRODUCER,
            "generation": self.producer_assignment["generation"],
            "principal": "principal.producer",
            "effective_scope": "repository"}
        self.frozen = {"attempt_id": "attempt-b1", "result_id": "result-b1",
                       "disposition": "completed",
                       "manifest_digest": "sha256:" + "1" * 64,
                       "freeze_operation_id": "freeze-b1", "frozen_at": NOW,
                       "artifacts": []}
        self.job = {"job_id": "job-b", "submission_id": "submission-b",
                    "ordinal": 0, "input_digest": "sha256:" + "2" * 64,
                    "policy_digest": "sha256:" + "3" * 64,
                    "test_scope": json.dumps(TEST_SCOPE),
                    "terminal_policy": "report-and-hold"}
        self.stages = [{"stage_id": "job-b/implementation", "job_id": "job-b",
                        "ordinal": 0, "kind": "implementation",
                        "work_id": WORK, "profile_name": "implementation",
                        "profile_digest": "sha256:profile",
                        "depends_on": "[]"}]
        patches = {
            "integration_checkpoint": lambda store, line_id:
                copy.deepcopy(self.accepted),
            "line_of": lambda store, line_id: copy.deepcopy(self.line_row),
            "checkpoint_of": lambda store, checkpoint_id:
                copy.deepcopy(self.checkpoint),
            "writer_of": lambda store, writer_id: copy.deepcopy(self.writer),
            "assignment_of": lambda store, attempt_id:
                copy.deepcopy(self.writer_assignment),
            "frozen_output_of": lambda store, attempt_id:
                copy.deepcopy(self.frozen),
            "job_rows": lambda store: [copy.deepcopy(self.job)],
            "stages_of": lambda store, job_id: copy.deepcopy(self.stages),
        }
        patch = mock.patch.multiple(admission, **patches)
        patch.start()
        self.addCleanup(patch.stop)
        self.manager = SimpleNamespace(_connection=lambda: None)
        self.jobs = SimpleNamespace(_connection=lambda: None,
                                    authority_uuid=UUID)

    # -- the repositories ----------------------------------------------------

    def repository(self, name, bare=False):
        place = os.path.join(self.root, name)
        os.makedirs(place)
        self.git(place, "init", "-q", *(("--bare",) if bare else
                                        ("-b", "main")))
        return place

    def git(self, place, *argv):
        answered = _run(["git", "-C", place] + list(argv))
        self.assertEqual(answered.returncode, 0,
                         f"git {argv}: {answered.stderr}")
        return answered.stdout.strip()

    def record(self, place, message):
        """One disposable fixture repository's own history, in the temporary
        directory this case owns and nowhere near this checkout."""
        self.git(place, "add", "--all")
        self.git(place, "commit", "-q", "-m", message)

    def write(self, place, name, body):
        with open(os.path.join(place, name), "w") as handle:
            handle.write(body)

    def fetch(self, revision):
        self.assertEqual(_run(["git", "-C", self.workspace, "fetch",
                               "--no-tags", self.line,
                               revision]).returncode, 0)

    def advance(self, name, body):
        """One more Job integrates: the dedicated reference moves by CAS."""
        held = self.git(self.target, "rev-parse", REFERENCE)
        self.write(self.target, name, body)
        self.record(self.target, f"an integration of {name}")
        moved = self.git(self.target, "rev-parse", "HEAD")
        self.git(self.target, "update-ref", REFERENCE, moved, held)
        return moved

    def place(self, path):
        held = os.stat(path)
        return {"path": path, "device": held.st_dev, "inode": held.st_ino}

    def materialize(self, repository, revision):
        """One revision's content on disk, so a harness can actually run it."""
        where = tempfile.mkdtemp(dir=self.root)
        archive = os.path.join(where, "content.tar")
        self.git(repository, "archive", "--format=tar", "-o", archive,
                 revision)
        with tarfile.open(archive) as held:
            held.extractall(where, filter="data")
        os.remove(archive)
        return where

    def observe(self, repository, commit, *, adding=None, actor=None):
        """RUN the pinned harness against one content state and record it.

        Section 4's members, none of them a word from a model: the command,
        the harness identity and digest, the exact input commit and tree, the
        environment, the ACTUAL exit status, the output and the execution that
        produced it. `harness_added` keeps the base observation honest about a
        file the base never carried.
        """
        content = self.materialize(repository, commit)
        if adding is not None:
            self.write(content, "harness.py", adding)
        with open(os.path.join(content, "harness.py")) as handle:
            harness = handle.read()
        answered = _run([sys.executable, "harness.py"], cwd=content)
        tail = answered.stderr.strip().splitlines()[-1:]
        return {"command": [sys.executable, "harness.py"],
                "test_identity": HARNESS_IDENTITY,
                "input_commit": commit,
                "input_tree": self.git(repository, "rev-parse",
                                       commit + "^{tree}"),
                "test_digest": digest(harness),
                "environment": f"{sys.executable} / {GIT_PROFILE}",
                "status": answered.returncode,
                "output": answered.stdout.strip() or (tail[0] if tail else ""),
                "execution": actor or RESULT_OWNERS["verification"],
                "harness_added": adding is not None}

    def observations(self, held, *, actor=None):
        """The three causal observations of ONE pinned harness."""
        return {
            "base": self.observe(self.target, self.base, adding=HARNESS,
                                 actor=actor),
            "isolated": self.observe(self.line, self.candidate, actor=actor),
            "combined": self.observe(self.workspace,
                                     held["prepared"]["head"], actor=actor)}

    # -- the owners ----------------------------------------------------------

    def prepare(self, **over):
        operands = {"line_id": "line-b", "proposal_id": "proposal-b1",
                    "workspace": self.place(self.workspace),
                    "target_source": self.place(self.target),
                    "target_reference": REFERENCE,
                    "integration_attempt_id": "attempt-integration",
                    "integration_assignment": self.assignment,
                    "canonical_target_id": TARGET}
        operands.update(over)
        profile = operands.pop("profile", self.profile)
        return reconciliation.prepare_result(
            self.store, profile, self.manager, self.jobs, self.authority,
            **operands)

    def authorize(self, held, *, owners=None, observations=None):
        given = owners or self.owners
        return reconciliation.record_result_evidence(
            self.store, given["verification"], given["review"],
            given["approval"], result_id=held["result_id"],
            observations=observations if observations is not None
            else self.observations(held))

    def publish(self, held):
        return reconciliation.publish_result(
            self.store, self.session, result_id=held["result_id"],
            input_digest="sha256:" + "5" * 64,
            policy_digest="sha256:" + "6" * 64)

    def import_account(self, held):
        return reconciliation.resolve_import_account(
            self.store, self.profile, self.manager, self.jobs, self.authority,
            result_id=held["result_id"])

    def through_publication(self):
        held = self.prepare()
        self.assertEqual(held["state"], "prepared")
        return self.publish(self.authorize(held))

    # -- reaching BEHIND the owner, which is the only way to ask what a
    #    reader actually binds ------------------------------------------------

    def row(self, result_id, member):
        return self.store._connection.execute(
            f"SELECT {member} FROM integration_results WHERE result_id = ?",
            (result_id,)).fetchone()[0]

    def edit(self, result_id, member, value):
        self.store._connection.execute(
            f"UPDATE integration_results SET {member} = ? WHERE result_id = ?",
            (value, result_id))

    def reopen_intent(self, result_id):
        """Put a settled record back into the state a death mid-preparation
        leaves: a committed intent with no outcome."""
        self.store._connection.execute(
            "UPDATE integration_results SET state = 'preparing', "
            "prepared = NULL, content_digest = NULL, operation_id = ? "
            "WHERE result_id = ?",
            (reconciliation.INTENT_KIND + ":" + result_id, result_id))
        self.store._connection.execute(
            "DELETE FROM operations WHERE operation_id = ?",
            (reconciliation.OUTCOME_KIND + ":" + result_id,))


class OriginalSubmissionIsImmutable(ResultCase):
    """Section 1: nothing here rewrites the producer's original submission."""

    def before(self):
        return {"line_head": self.git(self.line, "rev-parse", "HEAD"),
                "candidate_tree": self.git(self.line, "rev-parse",
                                           self.candidate + "^{tree}"),
                "line_refs": self.git(self.line, "show-ref"),
                "line_status": self.git(self.line, "status", "--porcelain"),
                "proposal": self.authority.proposal("proposal-b1"),
                "receipts": self.authority.receipts("proposal-b1")}

    def test_preparing_publishing_and_admitting_touch_no_producer_byte(self):
        first = self.before()
        published = self.through_publication()
        account = self.import_account(published)
        self.assertEqual(self.before(), first)
        # The submission is named by the result and by the account as a
        # reference each of them reads and neither of them rewrites.
        self.assertEqual(published["source_candidate"], self.candidate)
        self.assertEqual(published["source_base"], self.base)
        self.assertEqual(account["source_proposal_id"], "proposal-b1")

    def test_the_old_base_is_the_point_and_is_not_relaxed_away(self):
        """An old submission base is ALLOWED at this boundary. What stays
        exact is the RESULT's own target."""
        self.assertNotEqual(self.base, self.advanced)
        published = self.through_publication()
        self.assertEqual(published["source_base"], self.base)
        self.assertEqual(published["target_revision"], self.advanced)

    def test_the_prepared_result_carries_both_jobs_changes(self):
        held = self.prepare()
        content = self.materialize(self.workspace, held["prepared"]["head"])
        with open(os.path.join(content, "other.py")) as handle:
            self.assertIn("the first job answered", handle.read())
        with open(os.path.join(content, "feature.py")) as handle:
            self.assertEqual(handle.read(), FIXED)
        self.assertEqual(sorted(held["prepared"]["content"]),
                         ["feature.py", "harness.py", "other.py", "scale.py"])

    def test_the_producers_line_is_never_an_operand_of_the_merge(self):
        """The profile writes in the nominated workspace and in the dedicated
        target's own reference namespace. The line is a source it fetched
        FROM, and the merge has no index, worktree or HEAD."""
        before = sorted(os.listdir(os.path.join(self.line, ".git")))
        self.through_publication()
        self.assertEqual(sorted(os.listdir(os.path.join(self.line, ".git"))),
                         before)
        self.assertEqual(self.git(self.line, "status", "--porcelain"), "")


class TheSubmissionIsResolvedFromItsOwners(ResultCase):
    """Review 2026-09-10T05:14:36Z [P1]: provenance is READ, not accepted.

    The reviewer's counterexample supplied proposal `never-published` with a
    checkpoint and verdict nobody created and reached a real derived
    publication. There is no longer a door for it: `line_id` and `proposal_id`
    are selectors, and every member of the submission comes back from the
    accepted producers.
    """

    def test_a_proposal_the_authority_never_published_refuses(self):
        with self.assertRaises(ContractRefusal) as caught:
            self.prepare(proposal_id="never-published")
        self.assertIn("Authority refused", caught.exception.message)
        self.assertEqual(self.store._connection.execute(
            "SELECT COUNT(*) FROM integration_results").fetchone()[0], 0)

    def test_the_resolved_submission_is_the_producers_own_answer(self):
        held = self.prepare()
        evidence = self.accepted["evidence"]
        self.assertEqual(
            {name: held[name] for name in
             ("authority_uuid", "work_id", "job_id", "line_id",
              "source_checkpoint_id", "source_verdict_id",
              "source_proposal_id", "source_result_id", "source_base",
              "source_candidate")},
            {"authority_uuid": UUID, "work_id": WORK, "job_id": "job-b",
             "line_id": "line-b", "source_checkpoint_id": "checkpoint-b1",
             "source_verdict_id": "verdict-b1",
             "source_proposal_id": "proposal-b1",
             "source_result_id": "result-b1",
             "source_base": evidence["base"],
             "source_candidate": evidence["head"]})

    def test_a_producer_that_stops_agreeing_refuses(self):
        """Each of these is a cross-binding admission already owns; what is
        new is that a reconciliation cannot get past them."""
        for what, document, member, value in (
                ("frozen result", self.frozen, "result_id", "result-other"),
                ("checkpoint", self.checkpoint, "checkpoint_digest",
                 "sha256:different"),
                ("writer", self.writer, "participant", "baton.someone-else"),
                ("job", self.job, "input_digest", "sha256:different")):
            with self.subTest(what=what):
                prior = document[member]
                document[member] = value
                with self.assertRaises(ContractRefusal):
                    self.prepare()
                document[member] = prior
        self.assertEqual(self.prepare()["state"], "prepared")

    def test_an_unaccepted_checkpoint_refuses(self):
        with mock.patch.object(admission, "integration_checkpoint",
                               return_value=None):
            with self.assertRaises(ContractRefusal):
                self.prepare()
        self.assertEqual(self.store._connection.execute(
            "SELECT COUNT(*) FROM integration_results").fetchone()[0], 0)

    def test_the_import_account_rereads_the_producers(self):
        published = self.through_publication()
        self.assertEqual(self.import_account(published)["source_proposal_id"],
                         "proposal-b1")
        self.frozen["result_id"] = "result-other"
        with self.assertRaises(ContractRefusal):
            self.import_account(published)


class CausalEvidenceSurvivesComposition(ResultCase):
    """Section 4: three distinct observations, actually produced, and kept in
    the record's own custody rather than beside it."""

    def test_it_fails_on_the_base_passes_isolated_and_passes_combined(self):
        held = self.prepare()
        observed = self.observations(held)
        self.assertEqual(held["state"], "prepared")
        self.assertNotEqual(observed["base"]["status"], 0)
        self.assertIn("total answered 5", observed["base"]["output"])
        self.assertEqual(observed["isolated"]["status"], 0)
        self.assertEqual(observed["combined"]["status"], 0)
        self.assertEqual(observed["combined"]["output"],
                         "the regression harness passed")
        # ONE harness, pinned once and run three times.
        self.assertEqual({one["test_digest"] for one in observed.values()},
                         {digest(HARNESS)})
        self.assertEqual([observed[where]["harness_added"] for where in
                          ("base", "isolated", "combined")],
                         [True, False, False])

    def test_the_observations_are_retained_in_the_record(self):
        held = self.prepare()
        observed = self.observations(held)
        authorized = self.authorize(held, observations=observed)
        self.assertEqual(authorized["causal_observations"], observed)
        # And they survive publication and reach the import account.
        published = self.publish(authorized)
        self.assertEqual(self.import_account(published)["causal_observations"],
                         observed)

    def test_a_combined_failure_blocks_and_erases_no_positive(self):
        """A clean textual merge establishes only prepared CONTENT.

        A third Job changes `scale.py`, which B never touched, so the merge is
        clean and the combined result is still wrong. It cannot be authorized,
        the isolated positive is exactly what it was, and the earlier result
        is untouched.
        """
        first = self.prepare()
        earlier = self.observations(first)
        self.advance("scale.py", "SCALE = 2\n")
        again = self.prepare()
        self.assertEqual(again["state"], "prepared")
        observed = self.observations(again)
        self.assertNotEqual(observed["combined"]["status"], 0)
        self.assertIn("total answered 12", observed["combined"]["output"])
        with self.assertRaises(ContractRefusal) as caught:
            self.authorize(again, observations=observed)
        self.assertIn("blocks integration", caught.exception.message)
        self.assertEqual(reconciliation.result_of(
            self.store, again["result_id"])["state"], "prepared")
        # The isolated fix is not invalidated by what composition did to it.
        self.assertEqual(observed["isolated"]["status"], 0)
        self.assertEqual(observed["isolated"]["test_digest"],
                         earlier["isolated"]["test_digest"])
        self.assertNotEqual(again["result_id"], first["result_id"])
        self.assertEqual(
            reconciliation.result_of(self.store, first["result_id"]), first)

    def test_observations_about_other_content_refuse(self):
        held = self.prepare()
        observed = self.observations(held)
        cases = {
            "base ran elsewhere": ("base", "input_commit", self.advanced),
            "isolated ran elsewhere": ("isolated", "input_commit", self.base),
            "combined ran elsewhere": ("combined", "input_commit",
                                       self.candidate),
        }
        for what, (where, member, value) in cases.items():
            with self.subTest(what=what):
                moved = copy.deepcopy(observed)
                moved[where][member] = value
                with self.assertRaises(ContractRefusal):
                    self.authorize(held, observations=moved)
        with self.subTest(what="three different harnesses"):
            moved = copy.deepcopy(observed)
            moved["base"]["test_digest"] = "sha256:" + "7" * 64
            with self.assertRaises(ContractRefusal) as caught:
                self.authorize(held, observations=moved)
            self.assertIn("different harnesses", caught.exception.message)
        with self.subTest(what="a base that passed"):
            moved = copy.deepcopy(observed)
            moved["base"]["status"] = 0
            with self.assertRaises(ContractRefusal) as caught:
                self.authorize(held, observations=moved)
            self.assertIn("PASSED on the original base",
                          caught.exception.message)
        self.assertEqual(self.authorize(held, observations=observed)["state"],
                         "authorized")

    def test_observations_produced_by_somebody_else_refuse(self):
        held = self.prepare()
        observed = self.observations(held, actor="baton.somebody-else")
        with self.assertRaises(ContractRefusal) as caught:
            self.authorize(held, observations=observed)
        self.assertIn("verification owner", caught.exception.message)

    def test_an_unrelated_setup_failure_is_not_the_defects_baseline(self):
        """Section 4 rules that these are not the same observation, so the
        record has to be able to tell them apart."""
        broken = self.materialize(self.target, self.base)
        os.remove(os.path.join(broken, "scale.py"))
        self.write(broken, "harness.py", HARNESS)
        setup = _run([sys.executable, "harness.py"], cwd=broken)
        self.assertNotEqual(setup.returncode, 0)
        self.assertIn("ModuleNotFoundError", setup.stderr)
        defect = self.observe(self.target, self.base, adding=HARNESS)
        self.assertIn("total answered 5", defect["output"])
        self.assertNotIn("ModuleNotFoundError", defect["output"])


class TheEvidenceIsItsOwnersAndBindsTheseBytes(ResultCase):
    """Review [P1]: the two halves of the reproduced authorization defect."""

    def test_evidence_for_one_result_cannot_authorize_another(self):
        """THE REPRODUCED COUNTEREXAMPLE. Two combined trees over the same
        four paths used to share one content digest, so the first result's
        passing judgements authorized the second, failing one. The content
        digest names the objects now, so the two no longer collide."""
        first = self.prepare()
        self.authorize(first)
        self.advance("scale.py", "SCALE = 2\n")
        second = self.prepare()
        self.assertNotEqual(first["prepared"]["tree"],
                            second["prepared"]["tree"])
        self.assertNotEqual(first["content_digest"], second["content_digest"])
        # And an owner that answers about the FIRST result's bytes is refused
        # for the second.
        stale = {kind: Owner(RESULT_OWNERS[kind], kind,
                             about={"content_digest": first["content_digest"],
                                    "candidate": first["prepared"]["head"]})
                 for kind in RESULT_OWNERS}
        with self.assertRaises(ContractRefusal) as caught:
            self.authorize(second, owners=stale,
                           observations=self.observations(second))
        self.assertIn("not this result's", caught.exception.message)

    def test_each_owner_is_asked_about_this_result_and_nothing_else(self):
        held = self.prepare()
        self.authorize(held)
        for kind, owner in self.owners.items():
            with self.subTest(kind=kind):
                self.assertEqual(owner.asked, [{
                    "kind": kind, "result_id": held["result_id"],
                    "content_digest": held["content_digest"],
                    "candidate": held["prepared"]["head"],
                    "tree": held["prepared"]["tree"],
                    "target": held["target_revision"]}])

    def test_the_recorded_actor_is_the_owners_own_participant(self):
        held = self.prepare()
        liar = dict(self.owners)
        liar["review"] = Owner(RESULT_OWNERS["review"], "review",
                               actor="baton.somebody-important")
        with self.assertRaises(ContractRefusal) as caught:
            self.authorize(held, owners=liar)
        self.assertIn("answered for", caught.exception.message)

    def test_the_preparer_cannot_review_its_own_composition(self):
        held = self.prepare()
        itself = dict(self.owners)
        itself["review"] = Owner(INTEGRATOR, "review")
        with self.assertRaises(ContractRefusal) as caught:
            self.authorize(held, owners=itself)
        self.assertIn("does not review its own composition",
                      caught.exception.message)

    def test_an_absent_or_unconfigured_owner_refuses(self):
        held = self.prepare()
        for what, owner in (("no capability",
                             SimpleNamespace(participant="baton.x")),
                            ("no participant",
                             SimpleNamespace(verify=lambda basis: None))):
            with self.subTest(what=what):
                broken = dict(self.owners)
                broken["verification"] = owner
                with self.assertRaises(ContractRefusal):
                    self.authorize(held, owners=broken)

    def test_one_actor_may_not_give_two_judgements(self):
        held = self.prepare()
        same = dict(self.owners)
        same["review"] = Owner(RESULT_OWNERS["verification"], "review")
        with self.assertRaises(ContractRefusal) as caught:
            self.authorize(held, owners=same)
        self.assertIn("independence is what they are for",
                      caught.exception.message)

    def test_a_refusing_owner_does_not_authorize(self):
        held = self.prepare()
        refused = dict(self.owners)
        refused["review"] = Owner(RESULT_OWNERS["review"], "review",
                                  disposition="changes-requested")
        with self.assertRaises(ContractRefusal):
            self.authorize(held, owners=refused)
        self.assertEqual(reconciliation.result_of(
            self.store, held["result_id"])["state"], "prepared")


class PreparedResultReplaysItsIntent(ResultCase):
    """Section 3: a preparing record is not a completed operation."""

    def watched(self):
        """Ask the profile through a witness, so what it was asked WITH is
        evidence rather than inference."""
        asked = []
        original = self.profile.prepare

        def watching(*argv, **named):
            asked.append(named["target"])
            return original(*argv, **named)

        self.profile.prepare = watching
        return asked

    def test_an_exact_retry_is_the_same_record_and_merges_once(self):
        first = self.prepare()
        commits = self.git(self.workspace, "rev-list", "--all")
        asked = self.watched()
        self.assertEqual(self.prepare(), first)
        # Only a settled OUTCOME replays, and replaying it asks the profile
        # nothing at all.
        self.assertEqual(asked, [])
        self.assertEqual(self.git(self.workspace, "rev-list", "--all"),
                         commits)

    def test_exact_retries_replay_AFTER_the_record_has_moved_on(self):
        """Review [P2]: both of these used to refuse an identical call once
        the record had been authorized, because the signature they compared
        against was derived from the state it had reached SINCE."""
        held = self.prepare()
        authorized = self.authorize(held)
        self.assertEqual(authorized["state"], "authorized")
        asked = self.watched()
        self.assertEqual(self.prepare(), authorized)
        self.assertEqual(asked, [])
        self.assertEqual(self.authorize(authorized), authorized)
        # And it still replays after publication.
        published = self.publish(authorized)
        self.assertEqual(self.prepare(), published)
        self.assertEqual(self.authorize(published), published)

    def test_a_changed_operand_still_refuses_rather_than_replaying(self):
        held = self.authorize(self.prepare())
        different = dict(self.owners)
        different["review"] = Owner("baton.another-reviewer", "review")
        with self.assertRaises(ContractRefusal):
            self.authorize(held, owners=different)

    def test_a_committed_intent_with_no_outcome_RESUMES_on_its_own_target(self):
        """The superseded slice answered "already done" and asked the profile
        nothing, leaving a record that could never finish.

        AND THE RESUME CANNOT SELECT A LATER TARGET. The target moves under
        the reopened intent here, and the profile is still asked with the
        revision the record itself carries.
        """
        held = self.prepare()
        self.reopen_intent(held["result_id"])
        moved = self.advance("other.py", "MESSAGE = 'a third job'\n")
        asked = self.watched()
        resumed = self.prepare(target_revision=self.advanced)
        self.assertEqual(asked, [self.advanced])
        self.assertNotEqual(moved, self.advanced)
        self.assertEqual(resumed, held)
        # The profile validated and reused what it had retained rather than
        # reconciling a second time.
        self.assertEqual(resumed["prepared"]["head"], held["prepared"]["head"])

    def test_a_moved_target_is_a_NEW_result_and_the_old_one_is_untouched(self):
        first = self.prepare()
        moved = self.advance("other.py", "MESSAGE = 'a third job'\n")
        second = self.prepare()
        self.assertNotEqual(second["result_id"], first["result_id"])
        self.assertEqual(second["target_revision"], moved)
        self.assertEqual(first["target_revision"], self.advanced)
        self.assertEqual(
            reconciliation.result_of(self.store, first["result_id"]), first)

    def test_the_identity_is_derived_from_the_operands_and_only_from_those(self):
        held = self.prepare()
        operands = {name: held[name] for name in reconciliation._FIXED}
        self.assertEqual(reconciliation.result_identity(operands),
                         held["result_id"])
        for member in ("target_revision", "source_candidate",
                       "integration_attempt_id"):
            with self.subTest(member=member):
                moved = dict(operands)
                moved[member] = ("f" * 40 if member != "integration_attempt_id"
                                 else "attempt-other")
                self.assertNotEqual(reconciliation.result_identity(moved),
                                    held["result_id"])


class ResultReadersRejectTampering(ResultCase):
    """Section 3: row existence is not a binding, and neither is agreement
    between two documents a caller controls.

    THE EDITED MEMBER IS DELIBERATELY ONE THE LATEST ACT DID NOT SIGN. Review
    2026-09-10T05:14:36Z [P1] found that only the newest operation's signature
    was ever compared, so everything an EARLIER act settled was unguarded the
    moment the record moved on. Each case below edits something an earlier act
    owns and reads the record in a later state.
    """

    def test_a_source_identity_the_prepared_evidence_never_saw_is_caught(self):
        held = self.prepare()
        for member in ("source_verdict_id", "source_proposal_id",
                       "source_checkpoint_id", "job_id", "line_id"):
            with self.subTest(member=member):
                prior = self.row(held["result_id"], member)
                self.edit(held["result_id"], member, "forged-" + member)
                with self.assertRaises(ContractRefusal) as caught:
                    reconciliation.result_of(self.store, held["result_id"])
                self.assertIn("does not derive its own identity",
                              caught.exception.message)
                self.edit(held["result_id"], member, prior)
        # And with nothing edited it reads, so the matrix is not passing
        # because everything refuses.
        self.assertEqual(
            reconciliation.result_of(self.store, held["result_id"]), held)

    def test_prepared_content_edited_UNDER_an_authorized_result_is_caught(self):
        """The reviewer's exact counterexample: replacing the prepared head
        and tree with syntactically valid object names nothing holds, in a row
        whose newest act is the evidence act."""
        held = self.authorize(self.prepare())
        raw = self.row(held["result_id"], "prepared")
        edited = json.loads(raw)
        edited["head"] = "f" * 40
        edited["tree"] = "e" * 40
        self.edit(held["result_id"], "prepared", json.dumps(edited))
        with self.assertRaises(ContractRefusal) as caught:
            reconciliation.result_of(self.store, held["result_id"])
        self.assertIn(reconciliation.OUTCOME_KIND, caught.exception.message)
        self.edit(held["result_id"], "prepared", raw)
        self.assertEqual(
            reconciliation.result_of(self.store, held["result_id"]), held)

    def test_evidence_emptied_UNDER_a_published_result_is_caught(self):
        """The reviewer's second counterexample: a published row whose
        evidence is replaced with `{}` used to resolve an import account,
        real profile validation and all."""
        published = self.through_publication()
        self.edit(published["result_id"], "evidence", "{}")
        with self.assertRaises(ContractRefusal) as caught:
            reconciliation.result_of(self.store, published["result_id"])
        self.assertIn(reconciliation.EVIDENCE_KIND, caught.exception.message)
        with self.assertRaises(ContractRefusal):
            self.import_account(published)

    def test_causal_observations_edited_after_the_fact_are_caught(self):
        published = self.through_publication()
        moved = json.loads(self.row(published["result_id"],
                                    "causal_observations"))
        moved["combined"]["status"] = 0
        moved["base"]["status"] = 0
        self.edit(published["result_id"], "causal_observations",
                  json.dumps(moved))
        with self.assertRaises(ContractRefusal):
            reconciliation.result_of(self.store, published["result_id"])

    def test_an_invented_imported_state_with_no_entry_is_caught(self):
        """The reviewer's third counterexample. It is refused twice now: the
        schema will not hold the row, and the reader would not read it."""
        published = self.through_publication()
        with self.assertRaises(Exception):
            self.edit(published["result_id"], "state", "imported")
        self.assertEqual(self.row(published["result_id"], "state"),
                         "published")

    def test_a_row_pointed_at_another_committed_act_is_caught(self):
        held = self.prepare()
        moved = self.advance("other.py", "MESSAGE = 'a third job'\n")
        other = self.prepare()
        self.assertNotEqual(other["result_id"], held["result_id"])
        self.assertEqual(other["target_revision"], moved)
        self.edit(held["result_id"], "operation_id",
                  self.row(other["result_id"], "operation_id"))
        with self.assertRaises(ContractRefusal) as caught:
            reconciliation.result_of(self.store, held["result_id"])
        self.assertIn("not the act that reaches that state",
                      caught.exception.message)

    def test_a_published_row_cannot_be_quietly_demoted(self):
        """The state and the evidence that earned it commit together, so a
        row cannot shed one and keep the other."""
        published = self.through_publication()
        with self.assertRaises(Exception):
            self.edit(published["result_id"], "state", "prepared")
        self.assertEqual(self.row(published["result_id"], "state"),
                         "published")
        self.assertEqual(
            reconciliation.result_of(self.store, published["result_id"]),
            published)

    def test_prepared_content_that_no_longer_digests_to_its_set_is_caught(self):
        held = self.prepare()
        self.edit(held["result_id"], "content_digest", "sha256:" + "0" * 64)
        with self.assertRaises(ContractRefusal) as caught:
            reconciliation.result_of(self.store, held["result_id"])
        self.assertIn("content digest", caught.exception.message)

    def test_a_row_whose_act_is_not_in_the_journal_at_all_is_caught(self):
        held = self.prepare()
        self.store._connection.execute(
            "DELETE FROM operations WHERE operation_id = ?",
            (self.row(held["result_id"], "operation_id"),))
        with self.assertRaises(ContractRefusal) as caught:
            reconciliation.result_of(self.store, held["result_id"])
        self.assertIn("does not hold as a committed",
                      caught.exception.message)


class DerivedPublicationUsesItsOwnAssignment(ResultCase):
    """Section 5: an ordinary proposal under the INTEGRATION role's own live
    assignment, carrying a frozen result identity this record owns."""

    def test_the_derived_proposal_names_this_role_this_snapshot_these_bytes(self):
        published = self.through_publication()
        proposal = self.authority.proposal(published["derived_proposal_id"])
        self.assertEqual(proposal["assignment_ref"], self.assignment)
        self.assertEqual(proposal["assignment_ref"]["participant"], INTEGRATOR)
        self.assertEqual(proposal["target"], self.advanced)
        self.assertEqual(proposal["candidate_digest"],
                         published["prepared"]["head"])
        self.assertEqual(proposal["result_id"], published["derived_result_id"])
        self.assertNotEqual(proposal["result_id"], "result-b1")
        # The producer's own proposal is still exactly what it published.
        held = self.authority.proposal("proposal-b1")
        for member in ("proposal_id", "result_id", "result_digest",
                       "candidate_digest", "target"):
            with self.subTest(member=member):
                self.assertEqual(held[member], self.original[member])

    def test_an_unauthorized_result_does_not_publish(self):
        held = self.prepare()
        with self.assertRaises(ContractRefusal) as caught:
            self.publish(held)
        self.assertIn("never before them", caught.exception.message)
        self.assertIsNone(self.row(held["result_id"], "derived_proposal_id"))

    def test_the_publish_retry_replays_and_borrowing_the_producer_refuses(self):
        published = self.through_publication()
        self.assertEqual(self.publish(published), published)
        # And this is WHY the derived result identity must be new: the
        # Authority refuses the producer's under another assignment itself.
        with self.assertRaises(AuthorityRefusal):
            self.session.publish({
                "expect": self.assignment,
                "operation_id": "publish-borrowed",
                "proposal_id": "proposal-borrowed", "result_id": "result-b1",
                "result_digest": "sha256:" + "1" * 64,
                "candidate_digest": published["prepared"]["head"],
                "input_digest": "sha256:" + "5" * 64,
                "policy_digest": "sha256:" + "6" * 64,
                "target": self.advanced})

    def test_a_session_that_is_not_this_results_assignment_refuses(self):
        held = self.authorize(self.prepare())
        other = self.authority.session(PRODUCER)
        with self.assertRaises(ContractRefusal) as caught:
            reconciliation.publish_result(
                self.store, other, result_id=held["result_id"],
                input_digest="sha256:" + "5" * 64,
                policy_digest="sha256:" + "6" * 64)
        self.assertIn("assignment names", caught.exception.message)

    def test_the_import_account_keeps_both_identities_and_refuses_a_stale_one(self):
        published = self.through_publication()
        account = self.import_account(published)
        self.assertEqual(account["source_proposal_id"], "proposal-b1")
        self.assertEqual(account["derived_proposal_id"],
                         published["derived_proposal_id"])
        self.assertEqual(account["expected_target_revision"], self.advanced)
        self.assertEqual(account["candidate_digest"],
                         published["prepared"]["head"])
        self.advance("other.py", "MESSAGE = 'a third job'\n")
        with self.assertRaises(ContractRefusal) as caught:
            self.import_account(published)
        self.assertIn("reconciled again rather than imported",
                      caught.exception.message)


class ConflictsAndForeignSourcesHold(ResultCase):
    """Section 2: an ambiguous composition is a held question, not an answer."""

    def conflicting(self):
        """Job B's submission edits the SAME line Job A integrated."""
        self.git(self.line, "checkout", "-q", "--detach", self.base)
        self.write(self.line, "other.py", "MESSAGE = 'the second job'\n")
        self.record(self.line, "job b also touches other.py")
        candidate = self.git(self.line, "rev-parse", "HEAD")
        self.fetch(candidate)
        self.accepted["evidence"]["head"] = candidate
        self.accepted["evidence"]["tree"] = self.git(
            self.line, "rev-parse", candidate + "^{tree}")
        self.accepted["checkpoint_digest"] = digest(self.accepted["evidence"])
        self.checkpoint["evidence"] = copy.deepcopy(self.accepted["evidence"])
        self.checkpoint["checkpoint_digest"] = \
            self.accepted["checkpoint_digest"]
        return candidate

    def test_a_real_conflict_holds_with_its_reason_and_retains_no_result(self):
        self.conflicting()
        held = self.prepare()
        self.assertEqual(held["state"], "held")
        self.assertIn("does not reconcile cleanly", held["reason"])
        self.assertIn("other.py", held["reason"])
        self.assertIsNone(held["prepared"])
        self.assertIsNone(held["content_digest"])
        self.assertEqual(self.store._connection.execute(
            "SELECT COUNT(*) FROM integration_results WHERE prepared IS NOT "
            "NULL").fetchone()[0], 0)
        # The two sources are exactly as they were: neither was ever written.
        self.assertEqual(self.git(self.target, "rev-parse", REFERENCE),
                         self.advanced)
        self.assertEqual(self.git(self.line, "status", "--porcelain"), "")

    def test_a_held_result_neither_authorizes_nor_publishes(self):
        self.conflicting()
        held = self.prepare()
        with self.assertRaises(ContractRefusal):
            self.authorize(held, observations={})
        with self.assertRaises(ContractRefusal):
            self.publish(held)
        self.assertEqual(
            reconciliation.result_of(self.store, held["result_id"]), held)

    def test_a_held_result_replays_as_the_same_hold(self):
        self.conflicting()
        held = self.prepare()
        self.assertEqual(self.prepare(), held)

    def test_a_submission_already_based_on_the_target_refuses(self):
        """The producer's checkpoint says it was written on the revision the
        target already holds; there is nothing to re-express."""
        self.accepted["evidence"]["base"] = self.advanced
        self.accepted["checkpoint_digest"] = digest(self.accepted["evidence"])
        self.checkpoint["evidence"] = copy.deepcopy(self.accepted["evidence"])
        self.checkpoint["checkpoint_digest"] = \
            self.accepted["checkpoint_digest"]
        with self.assertRaises(ContractRefusal) as caught:
            self.prepare()
        self.assertIn("nothing here to re-express", caught.exception.message)

    def test_a_foreign_object_this_workspace_cannot_reach_refuses(self):
        self.accepted["evidence"]["head"] = "f" * 40
        self.accepted["checkpoint_digest"] = digest(self.accepted["evidence"])
        self.checkpoint["evidence"] = copy.deepcopy(self.accepted["evidence"])
        self.checkpoint["checkpoint_digest"] = \
            self.accepted["checkpoint_digest"]
        with self.assertRaises(IntegrationProfileRefusal):
            self.prepare()

    def test_an_assignment_naming_another_Work_refuses(self):
        other = dict(self.assignment,
                     work_ref={"authority_uuid": UUID,
                               "work_id": "0123456f-W9"})
        with self.assertRaises(ContractRefusal) as caught:
            self.prepare(integration_assignment=other)
        self.assertEqual(caught.exception.code, "operation-collision")

    def test_an_uncertified_profile_composes_nothing(self):
        class Other:
            name = "some-other-profile"
            version = 99

            def prepare(self, *argv, **named):
                raise AssertionError("an uncertified profile is never asked")

            validate = content = revision = prepare

        with self.assertRaises(ContractRefusal) as caught:
            self.prepare(profile=Other(), target_revision=self.advanced)
        self.assertEqual(caught.exception.code, "profile-uncertified")
        self.assertEqual(self.store._connection.execute(
            "SELECT COUNT(*) FROM integration_results").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
