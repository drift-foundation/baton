"""R2 review: direct answers must satisfy the same selected settlement bar."""
import json
import os
import unittest

from baton_v12.worker_manager import custody
from test_hold_clearance import OnlyExactSettlementClearsOneHold


class DirectClearance(OnlyExactSettlementClearsOneHold):
    def test_nonzero_accountable_answer_stays_held(self):
        control, composed, attempt_id = self.unresolved_custody("review-r2-accountable-fail")

        def failed(one, argv, mount, verb):
            one.vectors.append(list(argv))
            return one.answer(status=1, stdout=json.dumps({"custody": "normalize", "entries": 1,
                              "not_ours": 0, "running_as": [os.getuid(), os.getgid()]}))

        for engine in self.engines:
            engine.__class__.acting = failed
        answer = composed.normalize_directory(control, assignment_id=attempt_id, which="result")
        self.assertEqual(answer.status, 1)
        self.assertFalse(answer.ok)
        self.assertIsNone(answer.unaccounted)
        [held] = custody.custody_holds(control, attempt_id, "result")
        self.assertFalse(held["cleared"], "nonzero answers must remain held under the selected R2 contract")


def load_tests(loader, standard, pattern):
    return unittest.TestSuite([DirectClearance("test_nonzero_accountable_answer_stays_held")])


if __name__ == "__main__":
    unittest.main()
