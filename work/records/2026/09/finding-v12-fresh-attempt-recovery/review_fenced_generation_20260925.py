"""Reviewer probe: author schedule with the cancelled assignment ended.

Run only FenceProbe.test_fenced_generation_is_no_longer_live. The underlying
author case is intentionally exercised inside an expected refusal here.
"""
import unittest
from unittest.mock import patch

import test_fresh_attempt_after_failure as m
from baton_v12.contracts import ContractRefusal


class FenceProbe(m.AFailedRunSettlesAndAFreshRunSucceeds):
    def test_fenced_generation_is_no_longer_live(self):
        original = m.worker_manager.abandon_attempt

        def abandon(*args, **kwargs):
            result = original(*args, **kwargs)
            self.session.live_assignment = None
            return result

        with patch.object(m.worker_manager, "abandon_attempt", abandon):
            with self.assertRaises(ContractRefusal) as caught:
                super().test_a_failed_run_settles_and_a_fresh_run_is_accepted()
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("stale-assignment", "ended"))
        self.assertIn("no live assignment", caught.exception.message)
        self.assertIsNone(m.frozen_output_of(self.store, m.FRESH))
