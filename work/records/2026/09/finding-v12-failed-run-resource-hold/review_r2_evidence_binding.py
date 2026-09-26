"""Second independent R2 pass: settlement attribution and reader validation."""
import json
import os
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import custody
from baton_v12.worker_manager.store import manager_signature
from test_hold_clearance import OnlyExactSettlementClearsOneHold


class EvidenceBinding(OnlyExactSettlementClearsOneHold):
    def test_zero_exit_without_accountable_output_stays_held(self):
        control, composed, attempt_id = self.unresolved_custody("review-r2-zero")

        def illegible(one, argv, mount, verb):
            one.vectors.append(list(argv))
            return one.answer(status=0, stdout="not a custodian result")

        for engine in self.engines:
            engine.__class__.acting = illegible
        answer = composed.normalize_directory(control, assignment_id=attempt_id, which="result")
        self.assertFalse(answer.ok)
        [held] = custody.custody_holds(control, attempt_id, "result")
        self.assertFalse(held["cleared"], "the selected R2 contract excludes unaccountable answers")

    def test_unused_old_direct_answer_cannot_settle_a_new_submission(self):
        control, composed, attempt_id = self.unresolved_custody("review-r2-unused")
        document = {"custody": "normalize", "entries": 1, "not_ours": 0,
                    "running_as": [os.getuid(), os.getgid()]}

        def successful(one, argv, mount, verb):
            one.vectors.append(list(argv))
            return one.answer(status=0, stdout=json.dumps(document))

        for engine in self.engines:
            engine.__class__.acting = successful
        self.assertTrue(composed.normalize_directory(control, assignment_id=attempt_id, which="result").ok)
        [first] = custody.custody_holds(control, attempt_id, "result")
        self.assertTrue(first["cleared"])
        old_answer = self.answered(first["held"], document=document)

        def lost(one, argv, mount, verb):
            one.vectors.append(list(argv))
            raise RuntimeError("lost response to second submission")

        for engine in self.engines:
            engine.__class__.acting = lost
        self.assertFalse(composed.normalize_directory(control, assignment_id=attempt_id, which="result").ok)
        holds = custody.custody_holds(control, attempt_id, "result")
        self.assertEqual(len(holds), 2)
        self.assertFalse(holds[1]["cleared"])
        with self.assertRaises(ContractRefusal, msg="an unused old answer is still evidence for the old submission"):
            custody.clear_custody_hold(control, attempt_id=attempt_id, which="result", episode=1,
                                      observed="retained output from the first successful act",
                                      helper_identity=holds[1]["held"]["helper_identity"], settlement=old_answer)

    def test_reader_rejects_empty_settlement_with_matching_signature(self):
        control, _composed, attempt_id, held = self.held_episode("review-r2-empty")
        body = {"attempt_id": attempt_id, "root": "result", "episode": 0,
                "helper_identity": held["helper_identity"], "observed": "no evidence", "settlement": {}}
        # Malformed record in a disposable test store only.
        identity = custody._hold_identity(custody.CUSTODY_CLEARED_KIND, attempt_id, "result", 0)
        control.transact(identity, custody.CUSTODY_CLEARED_KIND,
                         manager_signature(custody.CUSTODY_CLEARED_KIND, body), lambda _c: dict(body))
        with self.assertRaises(ContractRefusal, msg="a dictionary alone is not a valid settlement"):
            custody.custody_holds(control, attempt_id, "result")


def load_tests(loader, standard, pattern):
    return unittest.TestSuite(EvidenceBinding(name) for name in sorted(EvidenceBinding.__dict__) if name.startswith("test_"))


if __name__ == "__main__":
    unittest.main()
