"""W133117: the integration RESULT, proved against the real things it owns.

INTEGRATION-CONTRACT-v1 sections 1 to 5. A submission is the producer's
ORIGINAL proposal on its ORIGINAL base; a result is that submission reconciled
with one pinned target snapshot, and it earns its OWN content, evidence,
review, approval and derived Authority proposal.

WHAT IS REAL HERE AND WHY. The dossier requires readers, cutpoints and result
preparation proved with real repositories and a real Authority/session in at
least one focused path, so these cases run actual Git against actual
repositories, an actual `IntegrationStore` and an actual `Authority` with an
actual claimed assignment. Nothing below is a canned owner answer: the causal
observations in `CausalEvidenceSurvivesComposition` are the exit statuses of
one pinned harness actually executed against three content states.
"""

import os
import subprocess
import sys
import tarfile
import tempfile
import unittest

from baton_v12.authority import Authority
from baton_v12.authority.errors import Refusal as AuthorityRefusal
from baton_v12.contracts import ContractRefusal, digest
from baton_v12.integration import (TARGET_SCHEMA, IntegrationStore,
                                   activate_target, reconciliation)
from baton_v12.integration.git_profile import (GitIntegrationProfile,
                                               IntegrationProfileRefusal)

NOW = "2026-09-10T05:00:00.000Z"
UUID = "0123456789abcdef0123456789abcdef"
WORK = "0123456f-W133117"
TARGET = "target:mainline"
REFERENCE = "refs/baton/integration/target"
PRODUCER = "baton.producer"
INTEGRATOR = "baton.integrator"
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


def _run(argv, cwd=None):
    return subprocess.run(list(argv), capture_output=True, text=True, env=ENV,
                          cwd=cwd, timeout=SUBPROCESS_TIMEOUT)


def runner(argv):
    """The profile's ONLY way to reach a subprocess."""
    answered = _run(argv)
    return {"returncode": answered.returncode, "stdout": answered.stdout,
            "stderr": answered.stderr}


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
        self.original = producer.publish({
            "expect": claimed["assignment"],
            "operation_id": "publish-original",
            "proposal_id": "proposal-b1", "result_id": "result-b1",
            "result_digest": "sha256:" + "1" * 64,
            "candidate_digest": self.candidate,
            "input_digest": "sha256:" + "2" * 64,
            "policy_digest": "sha256:" + "3" * 64})
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
        self.submission = {
            "authority_uuid": UUID, "work_id": WORK, "job_id": "job-b",
            "line_id": "line-b", "source_checkpoint_id": "checkpoint-b1",
            "source_verdict_id": "verdict-b1",
            "source_proposal_id": "proposal-b1",
            "source_result_id": "result-b1",
            "source_result_digest": "sha256:" + "1" * 64,
            "source_checkpoint_digest": "sha256:" + "2" * 64,
            "source_base": self.base, "source_candidate": self.candidate}

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

    def observe(self, content, *, adding=None):
        """RUN the pinned harness against one content state and record it.

        The observation names the command, the harness's own digest, what was
        ADDED to make the run possible at all, the actual exit status and the
        actual output. None of those is a word from a model, and `harness_added`
        is what keeps the base observation honest about a file the base never
        carried.
        """
        if adding is not None:
            self.write(content, "harness.py", adding)
        with open(os.path.join(content, "harness.py")) as handle:
            harness = handle.read()
        answered = _run([sys.executable, "harness.py"], cwd=content)
        return {"command": [sys.executable, "harness.py"],
                "harness_digest": digest(harness),
                "harness_added": adding is not None,
                "returncode": answered.returncode,
                "stdout": answered.stdout.strip(),
                "stderr": answered.stderr.strip().splitlines()[-1:]}

    # -- the owners ----------------------------------------------------------

    def prepare(self, **over):
        operands = {"submission": self.submission,
                    "workspace": self.place(self.workspace),
                    "target_source": self.place(self.target),
                    "target_reference": REFERENCE,
                    "integration_attempt_id": "attempt-integration",
                    "integration_assignment": self.assignment,
                    "canonical_target_id": TARGET}
        operands.update(over)
        return reconciliation.prepare_result(self.store, self.profile,
                                             **operands)

    def evidence(self, kind, actor, content_digest=None, held=None):
        return {"kind": kind, "identity": f"{kind}-of-the-result",
                "actor": actor,
                "disposition": {"verification": "passed", "review": "accepted",
                                "approval": "approved"}[kind],
                "content_digest": content_digest or held["content_digest"]}

    def authorize(self, held):
        return reconciliation.record_result_evidence(
            self.store, result_id=held["result_id"],
            verification=self.evidence("verification", "baton.verifier",
                                       held=held),
            review=self.evidence("review", "baton.reviewer", held=held),
            approval=self.evidence("approval", "baton.approver", held=held))

    def publish(self, held):
        return reconciliation.publish_result(
            self.store, self.session, result_id=held["result_id"],
            input_digest="sha256:" + "5" * 64,
            policy_digest="sha256:" + "6" * 64)

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
                "proposal": self.authority.proposal("proposal-b1")}

    def test_preparing_publishing_and_admitting_touch_no_producer_byte(self):
        first = self.before()
        published = self.through_publication()
        account = reconciliation.resolve_import_account(
            self.store, self.profile, result_id=published["result_id"])
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
        FROM, and `merge-tree --write-tree` has no index, worktree or HEAD."""
        before = sorted(os.listdir(os.path.join(self.line, ".git")))
        self.through_publication()
        self.assertEqual(sorted(os.listdir(os.path.join(self.line, ".git"))),
                         before)
        self.assertEqual(self.git(self.line, "status", "--porcelain"), "")


class CausalEvidenceSurvivesComposition(ResultCase):
    """Section 4: three distinct observations, actually produced."""

    def three(self):
        base = self.materialize(self.target, self.base)
        isolated = self.materialize(self.line, self.candidate)
        held = self.prepare()
        combined = self.materialize(self.workspace, held["prepared"]["head"])
        return held, {
            # The harness does not exist on the old base. It is ADDED there,
            # once, from the same bytes, and the observation says so rather
            # than implying the base ever ran it.
            "base": self.observe(base, adding=HARNESS),
            "isolated": self.observe(isolated),
            "combined": self.observe(combined)}

    def test_it_fails_on_the_base_passes_isolated_and_passes_combined(self):
        held, observed = self.three()
        self.assertEqual(held["state"], "prepared")
        self.assertNotEqual(observed["base"]["returncode"], 0)
        self.assertIn("total answered 5", observed["base"]["stderr"][0])
        self.assertEqual(observed["isolated"]["returncode"], 0)
        self.assertEqual(observed["combined"]["returncode"], 0)
        self.assertEqual(observed["combined"]["stdout"],
                         "the regression harness passed")
        # ONE harness, pinned once and run three times.
        self.assertEqual({one["harness_digest"] for one in observed.values()},
                         {digest(HARNESS)})
        self.assertEqual([observed[where]["harness_added"] for where in
                          ("base", "isolated", "combined")],
                         [True, False, False])

    def test_a_combined_failure_stays_visible_and_erases_no_positive(self):
        """A clean textual merge establishes only prepared CONTENT.

        A third Job changes `scale.py`, which B never touched, so the merge is
        clean and the combined result is still wrong. The isolated positive is
        exactly what it was, and the earlier result is untouched.
        """
        first, observed = self.three()
        self.advance("scale.py", "SCALE = 2\n")
        again = self.prepare()
        self.assertEqual(again["state"], "prepared")
        combined = self.observe(self.materialize(self.workspace,
                                                 again["prepared"]["head"]))
        self.assertNotEqual(combined["returncode"], 0)
        self.assertIn("total answered 12", combined["stderr"][0])
        # The isolated fix is not invalidated by what composition did to it.
        self.assertEqual(observed["isolated"]["returncode"], 0)
        self.assertEqual(observed["isolated"]["harness_digest"],
                         combined["harness_digest"])
        # And it is a DIFFERENT result, so nothing about the first one moved.
        self.assertNotEqual(again["result_id"], first["result_id"])
        self.assertEqual(
            reconciliation.result_of(self.store, first["result_id"]), first)

    def test_a_failed_composition_is_not_authorized_by_clean_git(self):
        """No pass word from a model and no clean Git exit replaces test
        custody: the combined bytes still need evidence ABOUT them."""
        self.advance("scale.py", "SCALE = 2\n")
        held = self.prepare()
        self.assertEqual(held["state"], "prepared")
        with self.assertRaises(ContractRefusal):
            self.publish(held)

    def test_an_unrelated_setup_failure_is_not_the_defects_baseline(self):
        """Section 4 rules that these are not the same observation, so the
        record has to be able to tell them apart."""
        broken = self.materialize(self.target, self.base)
        os.remove(os.path.join(broken, "scale.py"))
        setup = self.observe(broken, adding=HARNESS)
        self.assertNotEqual(setup["returncode"], 0)
        self.assertIn("ModuleNotFoundError", setup["stderr"][0])
        defect = self.observe(self.materialize(self.target, self.base),
                              adding=HARNESS)
        self.assertIn("AssertionError", defect["stderr"][0])
        self.assertNotEqual(setup["stderr"], defect["stderr"])


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

    THE EDITED MEMBER IS DELIBERATELY ONE THE PREPARED EVIDENCE DOES NOT
    CARRY. `target_revision` is checked against prepared evidence before the
    identity is re-derived, so editing it would prove the earlier check rather
    than the binding. A source verdict, proposal, checkpoint or Job identity
    is in the FIXED operand set and in nothing else, so only re-derivation
    catches it.
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
        self.assertIn("does not match the operands", caught.exception.message)

    def test_a_state_its_own_operation_did_not_reach_is_caught(self):
        published = self.through_publication()
        self.edit(published["result_id"], "state", "prepared")
        with self.assertRaises(ContractRefusal) as caught:
            reconciliation.result_of(self.store, published["result_id"])
        self.assertIn("journal does not hold", caught.exception.message)

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
        self.assertIn("journal does not hold", caught.exception.message)

    def test_evidence_edited_under_an_authorized_result_is_caught(self):
        held = self.authorize(self.prepare())
        self.edit(held["result_id"], "evidence",
                  '{"verification": {}, "review": {}, "approval": {}}')
        with self.assertRaises(ContractRefusal):
            reconciliation.result_of(self.store, held["result_id"])


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

    def test_evidence_is_about_THESE_bytes_and_is_independent(self):
        held = self.prepare()
        with self.subTest(case="other bytes"):
            with self.assertRaises(ContractRefusal):
                reconciliation.record_result_evidence(
                    self.store, result_id=held["result_id"],
                    verification=self.evidence("verification",
                                               "baton.verifier",
                                               "sha256:" + "9" * 64),
                    review=self.evidence("review", "baton.reviewer",
                                         held=held),
                    approval=self.evidence("approval", "baton.approver",
                                           held=held))
        with self.subTest(case="one actor, two judgements"):
            with self.assertRaises(ContractRefusal):
                reconciliation.record_result_evidence(
                    self.store, result_id=held["result_id"],
                    verification=self.evidence("verification", "baton.same",
                                               held=held),
                    review=self.evidence("review", "baton.same", held=held),
                    approval=self.evidence("approval", "baton.approver",
                                           held=held))
        self.assertEqual(self.authorize(held)["state"], "authorized")

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
        account = reconciliation.resolve_import_account(
            self.store, self.profile, result_id=published["result_id"])
        self.assertEqual(account["source_proposal_id"], "proposal-b1")
        self.assertEqual(account["derived_proposal_id"],
                         published["derived_proposal_id"])
        self.assertEqual(account["expected_target_revision"], self.advanced)
        self.assertEqual(account["candidate_digest"],
                         published["prepared"]["head"])
        self.advance("other.py", "MESSAGE = 'a third job'\n")
        with self.assertRaises(ContractRefusal) as caught:
            reconciliation.resolve_import_account(
                self.store, self.profile, result_id=published["result_id"])
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
        return dict(self.submission, source_candidate=candidate)

    def test_a_real_conflict_holds_with_its_reason_and_retains_no_result(self):
        held = self.prepare(submission=self.conflicting())
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
        held = self.prepare(submission=self.conflicting())
        with self.assertRaises(ContractRefusal):
            self.authorize(held)
        with self.assertRaises(ContractRefusal):
            self.publish(held)
        self.assertEqual(
            reconciliation.result_of(self.store, held["result_id"]), held)

    def test_a_held_result_replays_as_the_same_hold(self):
        submission = self.conflicting()
        held = self.prepare(submission=submission)
        self.assertEqual(self.prepare(submission=submission), held)

    def test_a_submission_already_based_on_the_target_refuses(self):
        with self.assertRaises(ContractRefusal) as caught:
            self.prepare(submission=dict(self.submission,
                                         source_base=self.advanced))
        self.assertIn("nothing here to re-express", caught.exception.message)

    def test_a_foreign_object_this_workspace_cannot_reach_refuses(self):
        with self.assertRaises(IntegrationProfileRefusal):
            self.prepare(submission=dict(self.submission,
                                         source_candidate="f" * 40))

    def test_an_assignment_naming_another_Work_refuses(self):
        other = dict(self.assignment,
                     work_ref={"authority_uuid": UUID, "work_id": "0123456f-W9"})
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
            reconciliation.prepare_result(
                self.store, Other(), submission=self.submission,
                workspace=self.place(self.workspace),
                target_source=self.place(self.target),
                target_reference=REFERENCE,
                integration_attempt_id="attempt-integration",
                integration_assignment=self.assignment,
                canonical_target_id=TARGET, target_revision=self.advanced)
        self.assertEqual(caught.exception.code, "profile-uncertified")
        self.assertEqual(self.store._connection.execute(
            "SELECT COUNT(*) FROM integration_results").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
