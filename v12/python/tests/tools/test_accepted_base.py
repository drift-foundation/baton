"""The human accepted-base transition, proved at every pinned boundary.

W202663 OWNER-HANDOFF-PR-JOBS item 4, review220421's amendment: one
operation identity bound to the full acceptance document, durable intent
before effects, exclusion enforced rather than assumed, expected-old
inside the committed Authority body, resume matching only its own intent,
receipt finalization without a duplicate policy bump, and no receipt
synthesized from coincidentally agreeing values.
"""
import fcntl
import json
import os
import subprocess
import tempfile
import unittest
import uuid as uuid_module
from pathlib import Path

from baton_v12.authority import Authority

from tools import accepted_base


def _ran(*argv, cwd=None):
    answer = subprocess.run(list(argv), capture_output=True, text=True,
                            cwd=cwd, timeout=60)
    assert answer.returncode == 0, (argv, answer.stderr)
    return answer.stdout.strip()


class AcceptedBaseCase(unittest.TestCase):

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="w202663-accepted-"))
        self.addCleanup(lambda: subprocess.run(
            ["rm", "-rf", str(self.root)], check=False))
        # The OWNER's official line: R0, then the accepted R1 above it.
        self.official = self.root / "official"
        self.official.mkdir()
        _ran("git", "init", "-q", ".", cwd=self.official)
        _ran("git", "-c", "user.name=o", "-c", "user.email=o@x", "commit",
             "-q", "--allow-empty", "-m", "R0", cwd=self.official)
        self.r0 = _ran("git", "rev-parse", "HEAD", cwd=self.official)
        _ran("git", "-c", "user.name=o", "-c", "user.email=o@x", "commit",
             "-q", "--allow-empty", "-m", "R1: accepted", cwd=self.official)
        self.r1 = _ran("git", "rev-parse", "HEAD", cwd=self.official)
        # An instance-shaped root: identity, authority at R0, target at R0.
        self.instance = self.root / "instance"
        (self.instance / "db").mkdir(parents=True)
        (self.instance / "state").mkdir()
        self.uuid = uuid_module.uuid4().hex
        (self.instance / "authority-identity.json").write_text(
            json.dumps({"authority_uuid": self.uuid}))
        authority = Authority.create(str(self.instance / "db"
                                         / "authority.sqlite3"),
                                     authority_uuid=self.uuid)
        authority.set_policy("canonical_target", self.r0)
        self.generation_after_seed = authority.policy_generation()
        authority.dispose()
        target = self.instance / "repo" / "target.git"
        target.parent.mkdir()
        _ran("git", "init", "-q", "--bare", str(target))
        _ran("git", "--git-dir", str(target), "fetch", "-q",
             str(self.official), f"{self.r0}:refs/heads/main")

    def acceptance(self, **changed):
        held = {"schema": "baton.w202663.accepted-base/1",
                "repository": str(self.official),
                "accepted_commit": self.r1,
                "expected_old": self.r0,
                "included_candidates": ["candidate-1"],
                "acceptance_evidence": "merge of candidate-1, tests green",
                "accepted_by": "Slawomir",
                "recorded_at": "2026-09-20T12:00:00.000Z"}
        held.update(changed)
        place = self.root / "acceptance.json"
        place.write_text(json.dumps(held, sort_keys=True))
        return place, held

    def run_tool(self, place):
        return accepted_base.main(["--instance", str(self.instance),
                                   "--acceptance", str(place)])

    def refusal(self, place):
        with self.assertRaises(SystemExit) as caught:
            self.run_tool(place)
        return str(caught.exception)

    def target_ref(self):
        return _ran("git", "--git-dir",
                    str(self.instance / "repo" / "target.git"),
                    "rev-parse", "refs/heads/main")

    def authority_state(self):
        authority = Authority.open_readonly(
            str(self.instance / "db" / "authority.sqlite3"),
            expected_authority_uuid=self.uuid)
        try:
            return (authority.canonical_target(),
                    authority.policy_generation())
        finally:
            authority.dispose()

    def receipt_place(self, held):
        import hashlib
        identity = hashlib.sha256(json.dumps(
            held, ensure_ascii=False, sort_keys=True,
            separators=(",", ":")).encode()).hexdigest()
        return self.instance / "accepted-bases" / f"{identity}.json"

    # -- the pinned boundaries, one each ------------------------------------

    def test_an_acceptance_advances_target_reference_and_receipt_once(self):
        place, held = self.acceptance()
        self.assertEqual(self.run_tool(place), 0)
        self.assertEqual(self.target_ref(), self.r1)
        target, generation = self.authority_state()
        self.assertEqual(target, self.r1)
        self.assertEqual(generation, self.generation_after_seed + 1,
                         "exactly one policy bump")
        receipt = json.loads(self.receipt_place(held).read_text())
        self.assertEqual(receipt["acceptance"], held)
        self.assertEqual(receipt["authority"]["accepted_commit"], self.r1)
        self.assertFalse((self.instance / "accepted-bases" / "intents")
                         .joinpath(self.receipt_place(held).name).exists(),
                         "the intent is finalized away with the receipt")

    def test_replaying_the_same_acceptance_bumps_nothing(self):
        place, held = self.acceptance()
        self.run_tool(place)
        before = self.authority_state()
        receipt_bytes = self.receipt_place(held).read_bytes()
        self.assertEqual(self.run_tool(place), 0)
        self.assertEqual(self.authority_state(), before,
                         "no second policy bump on replay")
        self.assertEqual(self.receipt_place(held).read_bytes(),
                         receipt_bytes, "the receipt is untouched")

    def test_a_changed_document_under_one_intent_identity_refuses(self):
        place, held = self.acceptance()
        intents = self.instance / "accepted-bases" / "intents"
        intents.mkdir(parents=True)
        import hashlib
        identity = hashlib.sha256(json.dumps(
            held, ensure_ascii=False, sort_keys=True,
            separators=(",", ":")).encode()).hexdigest()
        (intents / f"{identity}.json").write_text(
            json.dumps(dict(held, accepted_by="somebody-else")))
        self.assertIn("differs", self.refusal(place))
        self.assertEqual(self.target_ref(), self.r0)
        self.assertEqual(self.authority_state()[0], self.r0)

    def test_a_moved_canonical_target_refuses_touching_nothing_durable(self):
        authority = Authority.open(str(self.instance / "db"
                                       / "authority.sqlite3"),
                                   expected_authority_uuid=self.uuid)
        authority.set_policy("canonical_target", "f" * 40)
        authority.dispose()
        place, held = self.acceptance()
        self.assertIn("moved", self.refusal(place))
        target, _generation = self.authority_state()
        self.assertEqual(target, "f" * 40, "the foreign target stands")
        # review221684 [R2]'s probe: the reference used to advance R0->R1
        # BEFORE the stale refusal. The policy precheck now runs before any
        # repository effect, and this is the assertion that was omitted.
        self.assertEqual(self.target_ref(), self.r0,
                         "the reference never moved on a stale refusal")
        self.assertFalse(self.receipt_place(held).exists())

    def test_a_foreign_reference_refuses_before_any_write(self):
        # A THIRD commit nobody's acceptance names, sitting at main: neither
        # the acceptance's expected_old nor its accepted commit, so the swap
        # refuses by name and nothing -- reference, policy, receipt -- moves.
        _ran("git", "-c", "user.name=o", "-c", "user.email=o@x", "commit",
             "-q", "--allow-empty", "-m", "R2: foreign", cwd=self.official)
        foreign = _ran("git", "rev-parse", "HEAD", cwd=self.official)
        target = self.instance / "repo" / "target.git"
        _ran("git", "--git-dir", str(target), "fetch", "-q",
             str(self.official), foreign)
        _ran("git", "--git-dir", str(target), "update-ref",
             "refs/heads/main", foreign)
        place, held = self.acceptance()
        self.assertIn("neither", self.refusal(place))
        self.assertEqual(self.target_ref(), foreign,
                         "the foreign reference stands untouched")
        self.assertEqual(self.authority_state()[0], self.r0)
        self.assertFalse(self.receipt_place(held).exists())

    def test_interruption_after_reference_resumes_and_completes(self):
        # The crash window: reference advanced, Authority not, intent held.
        place, held = self.acceptance()
        target = self.instance / "repo" / "target.git"
        _ran("git", "--git-dir", str(target), "fetch", "-q",
             str(self.official), self.r1)
        _ran("git", "--git-dir", str(target), "update-ref",
             "refs/heads/main", self.r1, self.r0)
        intents = self.instance / "accepted-bases" / "intents"
        intents.mkdir(parents=True)
        import hashlib
        payload = json.dumps(held, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":")).encode()
        (intents / (hashlib.sha256(payload).hexdigest() + ".json")
         ).write_bytes(payload)
        self.assertEqual(self.run_tool(place), 0)
        self.assertEqual(self.authority_state()[0], self.r1)
        self.assertTrue(self.receipt_place(held).exists())

    def test_interruption_after_authority_finalizes_receipt_without_bump(
            self):
        place, held = self.acceptance()
        self.run_tool(place)
        before = self.authority_state()
        self.receipt_place(held).unlink()
        self.assertEqual(self.run_tool(place), 0)
        self.assertEqual(self.authority_state(), before,
                         "receipt finalization replays; no second bump")
        self.assertTrue(self.receipt_place(held).exists())

    def test_a_coincidentally_agreeing_target_synthesizes_no_receipt(self):
        authority = Authority.open(str(self.instance / "db"
                                       / "authority.sqlite3"),
                                   expected_authority_uuid=self.uuid)
        authority.set_policy("canonical_target", self.r1)
        authority.dispose()
        target = self.instance / "repo" / "target.git"
        _ran("git", "--git-dir", str(target), "fetch", "-q",
             str(self.official), self.r1)
        _ran("git", "--git-dir", str(target), "update-ref",
             "refs/heads/main", self.r1, self.r0)
        place, held = self.acceptance()
        self.assertIn("another operation", self.refusal(place))
        self.assertFalse(self.receipt_place(held).exists())

    def test_a_held_lifecycle_lock_refuses_the_whole_invocation(self):
        lock = os.open(self.instance / "state" / "lifecycle.lock",
                       os.O_RDWR | os.O_CREAT, 0o644)
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            place, held = self.acceptance()
            self.assertIn("lifecycle operation holds", self.refusal(place))
            self.assertEqual(self.target_ref(), self.r0)
            self.assertFalse(self.receipt_place(held).exists())
        finally:
            os.close(lock)

    # -- review221684 [R1]: the lock is not the stopped proof ---------------

    def test_a_live_recorded_manager_refuses_even_with_the_lock_free(self):
        """The probe's exact gap: `start` RELEASES the admission when it
        returns and the children never inherit it, so a free lock means
        nothing about a running stack. The stack's own ownership records
        are the proof -- a record naming a LIVE process (this test's own,
        whose pid and start time agree) refuses by name."""
        from tools import stack

        stack.write_record(str(self.instance / "state"), "manager",
                           {"schema": stack.SCHEMA, "pid": os.getpid(),
                            "started_at": stack.started_at(os.getpid())})
        place, held = self.acceptance()
        self.assertIn("live", self.refusal(place))
        self.assertEqual(self.target_ref(), self.r0)
        self.assertEqual(self.authority_state()[0], self.r0)
        self.assertFalse(self.receipt_place(held).exists())

    def test_a_gone_recorded_manager_is_a_stopped_instance(self):
        """A record whose pid was reused or exited is positively NOT
        running (`stack.ownership` answers gone), and the acceptance
        proceeds."""
        from tools import stack

        stack.write_record(str(self.instance / "state"), "manager",
                           {"schema": stack.SCHEMA, "pid": os.getpid(),
                            "started_at": 1})
        place, held = self.acceptance()
        self.assertEqual(self.run_tool(place), 0)
        self.assertEqual(self.authority_state()[0], self.r1)

    # -- review221684 [R2]: refusals precede every repository effect --------

    def test_a_malformed_document_reaches_no_effect_at_all(self):
        place, held = self.acceptance()
        broken = json.loads(place.read_text())
        del broken["acceptance_evidence"]
        place.write_text(json.dumps(broken))
        self.assertIn("carries", self.refusal(place))
        self.assertEqual(self.target_ref(), self.r0)
        self.assertEqual(self.authority_state()[0], self.r0)
        self.assertFalse((self.instance / "accepted-bases").exists(),
                         "no intent, no custody directory, nothing")

    # -- review221684 [R3]: a receipt file alone is not authority -----------

    def test_a_fabricated_receipt_is_refused_not_replayed(self):
        """The probe's exact shape: only {"acceptance": document} at the
        expected receipt name, no committed operation, no advanced state.
        The old tool answered replayed:true; this refuses."""
        place, held = self.acceptance()
        receipt = self.receipt_place(held)
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text(json.dumps({"acceptance": held}))
        self.assertIn("not a file that ends the check", self.refusal(place))
        self.assertEqual(self.target_ref(), self.r0)
        self.assertEqual(self.authority_state()[0], self.r0)

    def test_a_well_shaped_receipt_without_its_committed_operation_refuses(
            self):
        import hashlib
        place, held = self.acceptance()
        payload = json.dumps(held, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":")).encode()
        identity = hashlib.sha256(payload).hexdigest()
        receipt = self.receipt_place(held)
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text(json.dumps(
            {"schema": "baton.w202663.accepted-base-receipt/1",
             "acceptance": held, "authority": {"kind": "accepted-base",
                                               "accepted_commit": self.r1},
             "operation_id": f"accepted-base:{identity}",
             "performed_at": "2026-09-20T12:00:00.000Z"}))
        self.assertIn("never committed", self.refusal(place))
        self.assertEqual(self.authority_state()[0], self.r0)

    def test_a_historical_receipt_stays_valid_after_a_later_acceptance(self):
        """The explicit historical-receipt contract: the committed operation
        is the evidence; replaying an OLD acceptance after a newer base is
        recorded answers success and rewinds nothing."""
        place, held = self.acceptance()
        self.run_tool(place)
        _ran("git", "-c", "user.name=o", "-c", "user.email=o@x", "commit",
             "-q", "--allow-empty", "-m", "R2", cwd=self.official)
        r2 = _ran("git", "rev-parse", "HEAD", cwd=self.official)
        second, _held2 = self.acceptance(accepted_commit=r2,
                                         expected_old=self.r1)
        self.assertEqual(self.run_tool(second), 0)
        self.assertEqual(self.authority_state()[0], r2)
        self.assertEqual(self.run_tool(place), 0,
                         "the first acceptance replays from its receipt")
        self.assertEqual(self.authority_state()[0], r2,
                         "and rewinds nothing")

    def test_a_reference_coincidentally_at_accepted_is_not_a_resume(self):
        """No prior intent, no committed operation, and main already at the
        accepted commit: somebody else put it there, and calling that this
        invocation's resume would adopt their act."""
        target = self.instance / "repo" / "target.git"
        _ran("git", "--git-dir", str(target), "fetch", "-q",
             str(self.official), self.r1)
        _ran("git", "--git-dir", str(target), "update-ref",
             "refs/heads/main", self.r1, self.r0)
        place, held = self.acceptance()
        self.assertIn("coincidence is not a resume", self.refusal(place))
        self.assertEqual(self.authority_state()[0], self.r0)
        self.assertFalse(self.receipt_place(held).exists())

    def test_a_refused_call_publishes_no_intent_and_repeating_it_refuses(
            self):
        """review221748's probe: the refused coincidence call used to WRITE
        the intent first, and the identical second call trusted that
        refused intent as resume authority and advanced the Authority. The
        initial state is now judged before any intent is published, so
        both calls refuse and neither leaves an intent behind."""
        import hashlib
        target = self.instance / "repo" / "target.git"
        _ran("git", "--git-dir", str(target), "fetch", "-q",
             str(self.official), self.r1)
        _ran("git", "--git-dir", str(target), "update-ref",
             "refs/heads/main", self.r1, self.r0)
        place, held = self.acceptance()
        payload = json.dumps(held, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":")).encode()
        intent = (self.instance / "accepted-bases" / "intents"
                  / (hashlib.sha256(payload).hexdigest() + ".json"))
        self.assertIn("coincidence is not a resume", self.refusal(place))
        self.assertFalse(intent.exists(),
                         "a refused call publishes no resumable intent")
        self.assertIn("coincidence is not a resume", self.refusal(place),
                      "the identical second call refuses identically")
        self.assertEqual(self.authority_state()[0], self.r0,
                         "repetition never grants resume authority")
        self.assertFalse(self.receipt_place(held).exists())

    def test_a_genuine_interruption_after_the_reference_swap_resumes(self):
        """The REAL crash window, driven through the tool itself: the
        acting Authority open raises after the intent is published and the
        reference swapped, and the identical second call completes through
        its own intent without a second swap."""
        from unittest import mock

        from baton_v12.authority import Authority

        place, held = self.acceptance()
        real_open = Authority.open

        def wounded(*operands, **named):
            raise RuntimeError("injected crash after the reference swap")

        with mock.patch.object(Authority, "open", staticmethod(wounded)):
            with self.assertRaises(RuntimeError):
                self.run_tool(place)
        self.assertEqual(self.target_ref(), self.r1,
                         "the swap happened before the crash")
        self.assertEqual(self.authority_state()[0], self.r0,
                         "the Authority never moved")
        self.assertEqual(Authority.open, real_open)
        self.assertEqual(self.run_tool(place), 0,
                         "the identical call resumes through its own intent")
        self.assertEqual(self.authority_state()[0], self.r1)
        self.assertTrue(self.receipt_place(held).exists())


if __name__ == "__main__":
    unittest.main()
