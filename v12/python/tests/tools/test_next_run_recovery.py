"""Real runtime/token owners, simulated engine only; no deployed effects."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tests.manager import test_authoring_enforcement as fixture
from tools import next_run_recovery as recovery, next_run_managed as managed


class OwnerCessation(fixture.LaneFixture):
    def test_returned_token_and_exact_absence_permit_fenced_continuation(self):
        lane = self.lane()
        self.clock.advance(900)
        lane.tick()
        result = recovery.prove(self.store, fixture.packet(), lane.adapter)
        self.assertEqual(result['state'], 'ceased')
        self.assertEqual(len(result['attempts']), 1)
        self.assertTrue(result['attempts'][0]['token']['returned'])
        self.assertEqual(result['attempts'][0]['observation']['state'], 'absent')
        self.assertIsNotNone(self.store.operation_record(fixture.enforcement.HALT_KIND + ':enforcement-case'))
        self.assertEqual(recovery.prove(self.store, fixture.packet(), lane.adapter), result)

    def test_running_unsettled_and_unknown_effects_refuse(self):
        lane = self.lane()
        with self.assertRaises(managed.nr.Refusal): recovery.prove(self.store, fixture.packet(), lane.adapter)
        self.clock.advance(900)
        lane.tick()
        for state in ('running', 'quiescent'):
            self.engine.state = state
            with self.assertRaises(managed.nr.Refusal): recovery.prove(self.store, fixture.packet(), lane.adapter)
        self.engine.unavailable = True
        with self.assertRaises(managed.nr.Refusal): recovery.prove(self.store, fixture.packet(), lane.adapter)

    def test_unlinked_effect_is_not_inferred_absent_from_job_selection(self):
        lane = self.lane()
        with patch.object(fixture.enforcement, 'selected_attempts', return_value=[]):
            with self.assertRaises(managed.nr.Refusal): recovery.prove(self.store, fixture.packet(), lane.adapter)


class ProcessEvidence(unittest.TestCase):
    def test_real_current_uid_is_not_mistaken_for_cessation(self):
        with self.assertRaises(managed.nr.Refusal):
            managed.Host().processes_stopped({'uid': os.getuid()})

    def test_unreadable_process_identity_refuses(self):
        with patch.object(Path, 'read_text', side_effect=PermissionError('unknown')):
            with self.assertRaises(PermissionError): managed.Host().processes_stopped({'uid': 999999})
