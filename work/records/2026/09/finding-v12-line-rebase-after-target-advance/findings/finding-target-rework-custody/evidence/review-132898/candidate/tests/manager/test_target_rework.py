"""W131409 slice A -- target-rework custody, effective base and the seal.

THE PROFILE HALF IS REAL. A transplant that preserved both Jobs' changes is
the whole claim this slice makes, and a profile double asked to say so would
be this fixture asserting its own arithmetic. So the line, the target and the
objects are real repositories driven by the real `GitCheckpointProfile`, over
this case's own disposable directories.

THE AUTHORITY AND THE SESSION ARE DOUBLES, exactly as every other owner test in
this package composes them: what `prepare_rework` and `settle_unstarted` owe is
that they ASK those owners and hold their answers to a contract, and a double
that answers wrongly is how a case proves the holding. The real Authority path
belongs to the composed witness in a later slice.
"""

import json
import os
import subprocess
import tempfile
import unittest

from baton_v12.checkpoint_profiles import GitCheckpointProfile, checkpoint_ref
from baton_v12.contracts import ContractRefusal, digest
from baton_v12.source_profiles.checkout import ProfileRefusal
from baton_v12.worker_manager import (ControlStore, attach_review,
                                      create_line, freeze_checkpoint,
                                      grant_writer, integration_checkpoint,
                                      line_of, record_verdict, writer_of)
from baton_v12.worker_manager.source_boundary import nominate_source
from baton_v12.worker_manager.target_rework import (PASS_COMMENT, REWORK_KIND,
                                                    SEAL_KIND, effective_base,
                                                    prepare_rework, rework_of,
                                                    seal_unstarted, seal_of,
                                                    settle_unstarted,
                                                    settlement_of)
from baton_v12.worker_manager.workspaces import configure_workspace_storage
from . import input_roots
from .disk_roots import disk_backed_under

NOW = "2026-09-10T02:00:00.000Z"
AUTHORITY = "0123456789abcdef0123456789abcdef"
WORK = "01234567-W131409"
TARGET = "target-1"
PROPOSAL = "proposal-1"
RECEIPT = "receipt-1"


class Port:
    """The fence session the freeze reaches; it decides nothing here."""

    def __init__(self, participant):
        self.participant = participant

    def cancel(self, expect, operation_id, reason, work_id, authority_uuid):
        del reason, work_id, authority_uuid
        return {"operation_id": operation_id, "participant": self.participant,
                "generation": expect["generation"], "status": "fenced"}


class Session:
    """One Authority session's `pass_work`, and a record of every call."""

    def __init__(self, participant, *, route=None, fenced=False,
                 assignment=None, refusal=None):
        self.participant = participant
        self.calls = []
        self._route = route
        self._fenced = fenced
        self._assignment = assignment
        self._refusal = refusal

    def pass_work(self, request):
        self.calls.append(dict(request))
        if self._refusal is not None:
            raise self._refusal
        return {"assignment": self._assignment or request["expect"],
                "route": self._route or request["to_route"],
                "cause": "pass", "phase": "queued", "gate": None,
                "fenced": self._fenced}


class Authority:
    """The three reads preparation makes, and nothing else."""

    def __init__(self, target, *, proposal=PROPOSAL, receipt=RECEIPT,
                 candidate=None, disposition="integrated"):
        self._target = target
        self._proposal = proposal
        self._receipt = receipt
        self._candidate = candidate if candidate is not None else target
        self._disposition = disposition

    def canonical_target(self):
        return self._target

    def proposal(self, proposal_id):
        if proposal_id != self._proposal:
            return None
        return {"proposal_id": proposal_id, "candidate_digest": self._candidate}

    def receipt(self, proposal_id, kind):
        if proposal_id != self._proposal or kind != "integration":
            return None
        return {"receipt_id": self._receipt, "kind": kind,
                "disposition": self._disposition}


class TargetReworkCase(unittest.TestCase):
    """One accepted checkpoint on a real line, and a target that moved."""

    def setUp(self):
        self.root = disk_backed_under(self)
        self.temporary = tempfile.TemporaryDirectory()
        self.storage = os.path.join(self.root, "storage")
        os.makedirs(self.storage, exist_ok=True)
        self.target_place = os.path.join(self.root, "target")
        os.makedirs(self.target_place)
        self.profile = GitCheckpointProfile(self.runner)
        self.vcs(self.target_place, "init", "-q", "-b", "main")
        self.write(self.target_place, "harness.py", "print('base')\n")
        self.write(self.target_place, "other.py", "print('other base')\n")
        self.vcs(self.target_place, "add", "--all")
        self.vcs(self.target_place, "commit", "-q", "--message", "base")
        self.base = self.vcs(self.target_place, "rev-parse", "HEAD").strip()
        self.store = ControlStore.open(
            os.path.join(self.temporary.name, "control.sqlite3"),
            incarnation="manager-1", clock=lambda: NOW)
        self.group = input_roots.configured_group(self.store)
        configure_workspace_storage(self.store, self.storage)
        self.addCleanup(self.temporary.cleanup)
        self.addCleanup(self.store.close)

    # -- the bounded process boundary this profile is given ------------------

    def environment(self):
        return {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                "HOME": self.root, "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_CONFIG_SYSTEM": os.devnull, "GIT_TERMINAL_PROMPT": "0"}

    def runner(self, argv):
        answer = subprocess.run(
            list(argv), capture_output=True, text=True, timeout=120,
            env=dict(self.environment(), GIT_AUTHOR_NAME="Baton Test",
                     GIT_AUTHOR_EMAIL="test@baton.invalid",
                     GIT_COMMITTER_NAME="Baton Test",
                     GIT_COMMITTER_EMAIL="test@baton.invalid"))
        return {"returncode": answer.returncode, "stdout": answer.stdout,
                "stderr": answer.stderr}

    def vcs(self, place, *arguments):
        answer = self.runner(["git", "-C", place] + list(arguments))
        self.assertEqual(answer["returncode"], 0, answer["stderr"])
        return answer["stdout"]

    @staticmethod
    def write(place, name, body):
        with open(os.path.join(place, name), "w", encoding="utf-8") as handle:
            handle.write(body)

    # -- the durable rows an owner test composes itself ----------------------

    def attempt(self, attempt_id, generation, participant, principal):
        self.store._connection.execute(
            "INSERT INTO attempts (runtime_attempt_id, adapter_name, "
            "adapter_digest, profile_digest, created_at, work_id, "
            "authority_uuid, assignment_participant, assignment_generation, "
            "assignment_claim_event_seq, assignment_principal, "
            "assignment_scope, assignment_role, assignment_grant, "
            "assignment_policy_generation) VALUES (?, 'adapter', "
            "'adapter-digest', 'profile-digest', ?, ?, ?, ?, ?, ?, ?, "
            "'scope', 'role', 'grant', 1)",
            (attempt_id, NOW, WORK, AUTHORITY, participant, generation,
             generation, principal))
        return attempt_id

    def completed(self, attempt_id, *, review=False):
        self.store._connection.execute(
            "UPDATE attempts SET runtime_id = ?, execution_runtime = "
            "'quiescent', worker_disposition = 'completed' WHERE "
            "runtime_attempt_id = ?", ("runtime-" + attempt_id, attempt_id))
        if not review:
            return
        self.store._connection.execute(
            "UPDATE attempts SET output = 'frozen', verification = 'passed' "
            "WHERE runtime_attempt_id = ?", (attempt_id,))
        self.store._connection.execute(
            "INSERT INTO outputs (runtime_attempt_id, result_id, disposition, "
            "manifest_digest, freeze_operation_id, frozen_at) VALUES (?, ?, "
            "'completed', ?, ?, ?)",
            (attempt_id, "result-" + attempt_id, "sha256:" + "1" * 64,
             "freeze-" + attempt_id, NOW))
        for name, tail in (("findings", "2"), ("logs", "3")):
            self.store._connection.execute(
                "INSERT INTO output_artifacts (runtime_attempt_id, "
                "output_name, artifact_id, media_type, bytes, content_digest, "
                "locator) VALUES (?, ?, ?, 'text/plain', 1, ?, ?)",
                (attempt_id, name, f"artifact-{name}-{attempt_id}",
                 "sha256:" + tail * 64, f"custody/{attempt_id}/{name}"))

    def integration_attempt(self, attempt_id="integration-attempt",
                            *, generation=9, participant="baton.integrator",
                            offer_id="offer-integration"):
        """One activated, CLAIMED integration attempt that never started."""
        self.attempt(attempt_id, generation, participant, "integrator")
        self.store._connection.execute(
            "INSERT INTO offers (offer_id, work_id, authority_uuid, "
            "participant, runtime_attempt_id, incarnation, input_digest, "
            "policy_digest, profile_digest, verifier, verifier_spent, "
            "work_scope, work_route, issued_at, expires_at, state, "
            "intent_digest, accepted_at, settle_by, claim_operation_id, "
            "claim_signature, claim_generation, claim_event_seq, "
            "claim_principal, claim_scope, claim_role, claim_grant, "
            "claim_policy_generation, decided_at) VALUES (?, ?, ?, ?, ?, "
            "'manager-1', ?, ?, 'profile-digest', ?, 1, 'scope', 'integ', ?, "
            "?, 'claimed', ?, ?, ?, ?, ?, ?, ?, 'integrator', 'scope', "
            "'role', 'grant', 1, ?)",
            (offer_id, WORK, AUTHORITY, participant, attempt_id,
             "sha256:" + "4" * 64, "sha256:" + "5" * 64,
             "sha256:" + "8" * 64, NOW, NOW, "sha256:" + "6" * 64, NOW, NOW,
             "claim-" + offer_id, "sha256:" + "7" * 64, generation,
             generation, NOW))
        return attempt_id

    # -- the accepted line this rework is prepared from ----------------------

    def accepted_line(self, *, body="print('the second job answered')\n",
                      name="other.py"):
        line = create_line(self.store, source=nominate_source(
            self.target_place), declared_base=self.base, profile=self.profile,
            authority_uuid=AUTHORITY, work_id=WORK)
        line = line_of(self.store, line["line_id"])
        writer_attempt = self.attempt("writer-attempt-1", 1, "baton.impl",
                                      "writer")
        writer = grant_writer(self.store, line_id=line["line_id"],
                              attempt_id=writer_attempt, generation=1,
                              worker_id="impl-worker", profile=self.profile)
        self.write(line["line_path"], name, body)
        self.vcs(line["line_path"], "add", "--all")
        self.vcs(line["line_path"], "commit", "-q", "--message", "job b")
        self.completed(writer_attempt)
        checkpoint = freeze_checkpoint(
            self.store, writer_id=writer["writer_id"], generation=1,
            profile=self.profile, port=Port("baton.impl"))
        review_attempt = self.attempt("review-attempt-1", 1, "baton.review",
                                      "reviewer")
        review = attach_review(
            self.store, checkpoint_id=checkpoint["checkpoint_id"],
            attempt_id=review_attempt, generation=1,
            reviewer_worker_id="review-worker", profile=self.profile)
        self.completed(review_attempt, review=True)
        record_verdict(self.store, attachment_id=review["attachment_id"],
                       disposition="accepted", profile=self.profile,
                       port=Port("baton.review"))
        return line, checkpoint

    def advanced(self, body="print('the first job answered')\n",
                 name="harness.py"):
        """Job A integrates: the canonical target really moves."""
        self.write(self.target_place, name, body)
        self.vcs(self.target_place, "add", "--all")
        self.vcs(self.target_place, "commit", "-q", "--message", "job a")
        return self.vcs(self.target_place, "rev-parse", "HEAD").strip()

    def settled(self, attempt_id=None):
        """A sealed and settled stale integration attempt."""
        attempt_id = attempt_id or self.integration_attempt()
        seal = seal_unstarted(self.store, attempt_id=attempt_id)
        return settle_unstarted(self.store, Session("baton.integrator"),
                                seal_id=seal["seal_id"], to_route="impl")

    def prepared(self, **members):
        line, checkpoint = self.accepted_line()
        target = self.advanced()
        settlement = self.settled()
        held = prepare_rework(
            self.store, members.pop("authority", Authority(target)),
            line_id=line["line_id"],
            checkpoint_id=checkpoint["checkpoint_id"], target_id=TARGET,
            target_source=self.target_place, target_proposal_id=PROPOSAL,
            profile=self.profile, settlement_id=settlement["settlement_id"],
            **members)
        return line, checkpoint, target, held


class ThePreparedReworkCarriesBothChanges(TargetReworkCase):
    """CONTRACT-v1 section 7's first provider requirement, driven for real."""

    def test_a_clean_transplant_preserves_both_jobs_changes(self):
        line, _checkpoint, target, held = self.prepared()
        self.assertEqual(held["state"], "ready")
        self.assertEqual(held["target_revision"], target)
        self.assertEqual(held["prepared"]["base"], target)
        # THE CONTENT ITSELF, read out of the object the rework retained.
        place = line["line_path"]
        head = held["prepared"]["head"]
        self.assertEqual(self.vcs(place, "show", head + ":other.py"),
                         "print('the second job answered')\n")
        self.assertEqual(self.vcs(place, "show", head + ":harness.py"),
                         "print('the first job answered')\n")

    def test_the_effective_base_moves_and_the_declared_base_does_not(self):
        line, _checkpoint, target, _held = self.prepared()
        current = line_of(self.store, line["line_id"])
        self.assertEqual(current["declared_base"], self.base)
        self.assertEqual(effective_base(self.store, line["line_id"]), target)
        self.assertEqual(current["state"], "rework-ready")

    def test_an_unreworked_line_answers_its_creation_operand(self):
        line, _checkpoint = self.accepted_line()
        self.assertEqual(effective_base(self.store, line["line_id"]),
                         self.base)

    def test_the_old_checkpoint_reference_and_verdict_survive(self):
        line, checkpoint, _target, _held = self.prepared()
        place = line["line_path"]
        self.assertEqual(
            self.vcs(place, "rev-parse",
                     checkpoint_ref(line["line_id"], 1)).strip(),
            checkpoint["evidence"]["head"])
        # AND THE ACCEPTED VERDICT IS STILL HISTORICAL FACT, while the CURRENT
        # eligibility it granted is retired -- which is what stops the stale
        # candidate being offered again.
        held = self.store._connection.execute(
            "SELECT count(*) FROM checkpoint_verdicts WHERE checkpoint_id = ?",
            (checkpoint["checkpoint_id"],)).fetchone()[0]
        self.assertEqual(held, 1)
        self.assertIsNone(integration_checkpoint(self.store, line["line_id"]))

    def test_the_original_creation_still_recovers_the_same_line(self):
        line, _checkpoint, _target, _held = self.prepared()
        again = create_line(self.store, source=nominate_source(
            self.target_place), declared_base=self.base, profile=self.profile,
            authority_uuid=AUTHORITY, work_id=WORK)
        self.assertEqual(again["line_id"], line["line_id"])
        self.assertEqual(line_of(self.store,
                                 again["line_id"])["declared_base"], self.base)

    def test_a_creation_naming_the_moved_base_still_refuses(self):
        _line, _checkpoint, target, _held = self.prepared()
        with self.assertRaises(ContractRefusal):
            create_line(self.store, source=nominate_source(self.target_place),
                        declared_base=target, profile=self.profile,
                        authority_uuid=AUTHORITY, work_id=WORK)

    def test_preparing_the_same_round_twice_transplants_once(self):
        line, checkpoint, target, held = self.prepared()
        place = line["line_path"]
        before = self.vcs(place, "rev-parse", held["prepared"]["reference"])
        again = prepare_rework(
            self.store, Authority(target), line_id=line["line_id"],
            checkpoint_id=checkpoint["checkpoint_id"], target_id=TARGET,
            target_source=self.target_place, target_proposal_id=PROPOSAL,
            profile=self.profile,
            settlement_id=held["integration_settlement"]["settlement_id"])
        self.assertEqual(again["operation_id"], held["operation_id"])
        self.assertEqual(again["prepared"], held["prepared"])
        self.assertEqual(self.vcs(place, "rev-parse",
                                  held["prepared"]["reference"]), before)


class AConflictHoldsAndTakesNothing(TargetReworkCase):
    """Automatic resolution is outside v1 by decision, so the hold is the
    result -- and what it owes is evidence somebody can decide on."""

    def test_a_real_conflict_holds_with_its_paths(self):
        line, checkpoint = self.accepted_line(
            body="print('the second job edited this line')\n",
            name="harness.py")
        target = self.advanced()
        settlement = self.settled()
        held = prepare_rework(
            self.store, Authority(target), line_id=line["line_id"],
            checkpoint_id=checkpoint["checkpoint_id"], target_id=TARGET,
            target_source=self.target_place, target_proposal_id=PROPOSAL,
            profile=self.profile,
            settlement_id=settlement["settlement_id"])
        self.assertEqual(held["state"], "held")
        self.assertIn("harness.py", held["reason"])
        self.assertIsNone(held["prepared"])
        self.assertEqual(line_of(self.store, line["line_id"])["state"],
                         "rework-held")

    def test_a_held_rework_leaves_the_old_candidate_alone(self):
        line, checkpoint = self.accepted_line(
            body="print('the second job edited this line')\n",
            name="harness.py")
        target = self.advanced()
        settlement = self.settled()
        prepare_rework(
            self.store, Authority(target), line_id=line["line_id"],
            checkpoint_id=checkpoint["checkpoint_id"], target_id=TARGET,
            target_source=self.target_place, target_proposal_id=PROPOSAL,
            profile=self.profile, settlement_id=settlement["settlement_id"])
        place = line["line_path"]
        self.assertEqual(
            self.vcs(place, "rev-parse",
                     checkpoint_ref(line["line_id"], 1)).strip(),
            checkpoint["evidence"]["head"])
        refs = self.vcs(place, "for-each-ref", "--format=%(refname)",
                        "refs/baton/").split()
        self.assertNotIn(f"refs/baton/reworks/{line['line_id']}/1", refs)
        # A HELD LINE AUTHORIZES NO WRITER AND NO NEW BASE.
        self.assertEqual(effective_base(self.store, line["line_id"]),
                         self.base)


class PreparationRefusesWhatItCannotProve(TargetReworkCase):
    """Identity, tamper and foreign inputs refuse BEFORE any publication."""

    def prepare(self, **members):
        line, checkpoint = self.accepted_line()
        target = self.advanced()
        settlement = self.settled()
        operands = {"line_id": line["line_id"],
                    "checkpoint_id": checkpoint["checkpoint_id"],
                    "target_id": TARGET, "target_source": self.target_place,
                    "target_proposal_id": PROPOSAL, "profile": self.profile,
                    "settlement_id": settlement["settlement_id"]}
        authority = members.pop("authority", Authority(target))
        operands.update(members)
        with self.assertRaises(ContractRefusal) as caught:
            prepare_rework(self.store, authority, **operands)
        self.assertIsNone(line_of(self.store,
                                  line["line_id"])["current_rework_id"])
        return caught.exception

    def test_a_proposal_that_is_not_the_current_target_refuses(self):
        held = self.prepare(authority=Authority(
            "b" * 40, candidate="c" * 40))
        self.assertIn("canonical target names", held.message)

    def test_a_proposal_with_no_integrated_receipt_refuses(self):
        target = self.advanced.__wrapped__ if False else None
        del target
        line, checkpoint = self.accepted_line()
        moved = self.advanced()
        settlement = self.settled()
        with self.assertRaises(ContractRefusal) as caught:
            prepare_rework(
                self.store, Authority(moved, disposition="held"),
                line_id=line["line_id"],
                checkpoint_id=checkpoint["checkpoint_id"], target_id=TARGET,
                target_source=self.target_place, target_proposal_id=PROPOSAL,
                profile=self.profile,
                settlement_id=settlement["settlement_id"])
        self.assertIn("no integrated receipt", caught.exception.message)

    def test_a_foreign_checkpoint_refuses(self):
        """Before the target is even resolved: a checkpoint identity this
        store does not hold is refused as that."""
        held = self.prepare(checkpoint_id="checkpoint-somebody-else")
        self.assertIn("no line checkpoint", held.message)

    def test_an_unknown_settlement_refuses(self):
        held = self.prepare(settlement_id="rework-settlement-nobody")
        self.assertIn("no rework settlement", held.message)

    def test_a_target_source_that_is_not_a_directory_refuses(self):
        held = self.prepare(target_source=os.path.join(self.root, "absent"))
        self.assertIn("real directory of its own", held.message)

    def test_a_target_the_source_does_not_contain_refuses(self):
        """A digest this manager was told about is not content.

        THE PROFILE REFUSES IT, and the refusal is the profile's own -- the
        same way `create_line` lets a materialization refusal stand. The intent
        is already committed by then, which is the designed re-enterable crash
        window rather than a leak: the record stays `preparing` and a retry
        resumes it.
        """
        line, checkpoint = self.accepted_line()
        self.advanced()
        settlement = self.settled()
        with self.assertRaises(ProfileRefusal):
            prepare_rework(
                self.store, Authority("d" * 40), line_id=line["line_id"],
                checkpoint_id=checkpoint["checkpoint_id"], target_id=TARGET,
                target_source=self.target_place, target_proposal_id=PROPOSAL,
                profile=self.profile,
                settlement_id=settlement["settlement_id"])

    def test_a_target_that_has_not_moved_refuses(self):
        line, checkpoint = self.accepted_line()
        settlement = self.settled()
        with self.assertRaises(ContractRefusal) as caught:
            prepare_rework(
                self.store, Authority(self.base), line_id=line["line_id"],
                checkpoint_id=checkpoint["checkpoint_id"], target_id=TARGET,
                target_source=self.target_place, target_proposal_id=PROPOSAL,
                profile=self.profile,
                settlement_id=settlement["settlement_id"])
        self.assertIn("already based on", caught.exception.message)

    def test_a_tampered_custody_row_is_not_read_as_fact(self):
        _line, _checkpoint, _target, held = self.prepared()
        self.store._connection.execute(
            "UPDATE target_reworks SET target_revision = ? "
            "WHERE operation_id = ?", ("e" * 40, held["operation_id"]))
        self.store._connection.commit()
        # The row still reads, and its OPERATION still binds it -- what a
        # consumer must not do is trust the tampered member. The signature the
        # journal holds is what a later replay compares against, so a second
        # preparation under the same identity refuses rather than adopting it.
        again = rework_of(self.store, held["operation_id"])
        self.assertEqual(again["target_revision"], "e" * 40)
        self.store._connection.execute(
            "DELETE FROM operations WHERE operation_id = ?",
            (held["operation_id"],))
        self.store._connection.commit()
        with self.assertRaises(ContractRefusal) as caught:
            rework_of(self.store, held["operation_id"])
        self.assertIn("does not hold as a committed", caught.exception.message)


class TheSealDecidesAgainstTheLaunch(TargetReworkCase):
    """CONTRACT-v1 section 4's bounded prelaunch settlement."""

    def test_a_claimed_unstarted_attempt_seals(self):
        attempt_id = self.integration_attempt()
        held = seal_unstarted(self.store, attempt_id=attempt_id)
        self.assertEqual(held["runtime_attempt_id"], attempt_id)
        self.assertEqual(seal_of(self.store, attempt_id)["seal_id"],
                         held["seal_id"])

    def test_sealing_twice_settles_once(self):
        attempt_id = self.integration_attempt()
        first = seal_unstarted(self.store, attempt_id=attempt_id)
        again = seal_unstarted(self.store, attempt_id=attempt_id)
        self.assertEqual(again, first)
        self.assertEqual(self.store._connection.execute(
            "SELECT count(*) FROM attempt_launch_seals").fetchone()[0], 1)

    def test_an_attempt_that_started_holds(self):
        attempt_id = self.integration_attempt()
        self.store._connection.execute(
            "UPDATE attempts SET execution_runtime = 'running' "
            "WHERE runtime_attempt_id = ?", (attempt_id,))
        with self.assertRaises(ContractRefusal) as caught:
            seal_unstarted(self.store, attempt_id=attempt_id)
        self.assertIn("has not crossed the launch-intent boundary",
                      caught.exception.message)

    def test_an_uncertain_runtime_holds(self):
        attempt_id = self.integration_attempt()
        self.store._connection.execute(
            "UPDATE attempts SET execution_runtime = 'uncertain' "
            "WHERE runtime_attempt_id = ?", (attempt_id,))
        with self.assertRaises(ContractRefusal):
            seal_unstarted(self.store, attempt_id=attempt_id)

    def test_an_unclaimed_attempt_holds(self):
        attempt_id = self.attempt("lonely-attempt", 3, "baton.integrator",
                                  "integrator")
        with self.assertRaises(ContractRefusal) as caught:
            seal_unstarted(self.store, attempt_id=attempt_id)
        self.assertIn("committed claimed offers", caught.exception.message)

    def test_an_attempt_with_no_assignment_holds(self):
        self.store._connection.execute(
            "INSERT INTO attempts (runtime_attempt_id, adapter_name, "
            "adapter_digest, profile_digest, created_at) VALUES "
            "('bare-attempt', 'adapter', 'a', 'p', ?)", (NOW,))
        with self.assertRaises(ContractRefusal) as caught:
            seal_unstarted(self.store, attempt_id="bare-attempt")
        self.assertIn("holds no fixed assignment", caught.exception.message)


class TheSettlementIsAHandoffAndNotACompletion(TargetReworkCase):
    def test_the_sealed_attempt_is_passed_on_its_own_assignment(self):
        attempt_id = self.integration_attempt()
        seal = seal_unstarted(self.store, attempt_id=attempt_id)
        session = Session("baton.integrator")
        held = settle_unstarted(self.store, session, seal_id=seal["seal_id"],
                                to_route="impl")
        self.assertEqual(held["to_route"], "impl")
        self.assertEqual(held["account"]["cause"], "pass")
        self.assertEqual(len(session.calls), 1)
        self.assertEqual(session.calls[0]["comment"], PASS_COMMENT)
        self.assertEqual(session.calls[0]["expect"], seal["assignment"])
        self.assertEqual(settlement_of(self.store,
                                       held["settlement_id"])["seal_id"],
                         seal["seal_id"])

    def test_settling_twice_passes_once(self):
        attempt_id = self.integration_attempt()
        seal = seal_unstarted(self.store, attempt_id=attempt_id)
        session = Session("baton.integrator")
        first = settle_unstarted(self.store, session, seal_id=seal["seal_id"],
                                 to_route="impl")
        again = settle_unstarted(self.store, session, seal_id=seal["seal_id"],
                                 to_route="impl")
        self.assertEqual(again, first)
        self.assertEqual(len(session.calls), 1)

    def test_a_session_acting_for_another_participant_refuses(self):
        attempt_id = self.integration_attempt()
        seal = seal_unstarted(self.store, attempt_id=attempt_id)
        with self.assertRaises(ContractRefusal) as caught:
            settle_unstarted(self.store, Session("baton.somebody-else"),
                             seal_id=seal["seal_id"], to_route="impl")
        self.assertIn("sealed assignment names", caught.exception.message)

    def test_a_handoff_that_moved_another_route_refuses(self):
        attempt_id = self.integration_attempt()
        seal = seal_unstarted(self.store, attempt_id=attempt_id)
        with self.assertRaises(ContractRefusal) as caught:
            settle_unstarted(self.store,
                             Session("baton.integrator", route="elsewhere"),
                             seal_id=seal["seal_id"], to_route="impl")
        self.assertIn("moved the Work to", caught.exception.message)

    def test_a_handoff_that_fenced_the_assignment_refuses(self):
        attempt_id = self.integration_attempt()
        seal = seal_unstarted(self.store, attempt_id=attempt_id)
        with self.assertRaises(ContractRefusal) as caught:
            settle_unstarted(self.store,
                             Session("baton.integrator", fenced=True),
                             seal_id=seal["seal_id"], to_route="impl")
        self.assertIn("clears no gate", caught.exception.message)

    def test_a_handoff_that_ended_another_assignment_refuses(self):
        attempt_id = self.integration_attempt()
        seal = seal_unstarted(self.store, attempt_id=attempt_id)
        other = dict(seal["assignment"], generation=99)
        with self.assertRaises(ContractRefusal) as caught:
            settle_unstarted(self.store,
                             Session("baton.integrator", assignment=other),
                             seal_id=seal["seal_id"], to_route="impl")
        self.assertIn("ended another assignment", caught.exception.message)


class TheReworkRoundIsAdmittedAndFrozenOnItsOwnBase(TargetReworkCase):
    """The writer/freeze binding CONTRACT-v1 section 5 ends with."""

    def rework_round(self):
        line, checkpoint, target, held = self.prepared()
        attempt = self.attempt("writer-attempt-2", 2, "baton.impl", "writer")
        writer = grant_writer(
            self.store, line_id=line["line_id"], attempt_id=attempt,
            generation=2, worker_id="impl-worker", profile=self.profile,
            based_checkpoint_id=checkpoint["checkpoint_id"])
        return line, checkpoint, target, held, writer

    def test_the_writer_records_the_base_it_was_admitted_under(self):
        _line, _checkpoint, target, held, writer = self.rework_round()
        row = writer_of(self.store, writer["writer_id"])
        self.assertEqual(row["effective_base"], target)
        self.assertEqual(row["rework_id"], held["operation_id"])

    def test_a_rework_writer_naming_another_checkpoint_refuses(self):
        line, _checkpoint, _target, _held = self.prepared()
        attempt = self.attempt("writer-attempt-2", 2, "baton.impl", "writer")
        with self.assertRaises(ContractRefusal) as caught:
            grant_writer(self.store, line_id=line["line_id"],
                         attempt_id=attempt, generation=2,
                         worker_id="impl-worker", profile=self.profile,
                         based_checkpoint_id="checkpoint-somebody-else")
        self.assertIn("must name the checkpoint its rework was prepared from",
                      caught.exception.message)

    def test_the_frozen_round_uses_the_effective_base(self):
        line, _checkpoint, target, _held, writer = self.rework_round()
        place = line["line_path"]
        # The round's own work, on top of the prepared result.
        self.vcs(place, "reset", "--hard", _held_head(self.store, line), "--")
        self.write(place, "third.py", "print('the rework round')\n")
        self.vcs(place, "add", "--all")
        self.vcs(place, "commit", "-q", "--message", "rework round")
        self.completed("writer-attempt-2")
        frozen = freeze_checkpoint(
            self.store, writer_id=writer["writer_id"], generation=2,
            profile=self.profile, port=Port("baton.impl"))
        self.assertEqual(frozen["evidence"]["base"], target)
        self.assertIn("third.py", frozen["evidence"]["paths"])


def _held_head(store, line):
    """The prepared rework head this round is written on top of."""
    current = line_of(store, line["line_id"])
    return rework_of(store, current["current_rework_id"])["prepared"]["head"]


if __name__ == "__main__":
    unittest.main()
