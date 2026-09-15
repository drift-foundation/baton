"""Check the settlement-window hypothesis disproved by the first research run."""
import unittest
from unittest import mock
from tests.tools import test_managed_integration as supplied
from baton_v12.integration.reconciliation import publication_of
from baton_v12.integration.queue import entries_of
import integration_placement as placement
class SettlementRecovery(supplied.PlacementCase):
    def test_queue_settlement_before_marker_recovers_without_another_swap(self):
        self.custody(); self.stopped()
        real=placement.record_publication_effect
        def interrupted(store,publication_id,state):
            if state=='settled':raise RuntimeError('after queue settlement')
            return real(store,publication_id,state)
        with mock.patch.object(placement,'record_publication_effect',side_effect=interrupted):
            with self.assertRaises(RuntimeError):self.publish()
        self.assertEqual(entries_of(self.coordinator,supplied.coordinator_fixtures.TARGET)[0]['state'],'integrated')
        self.assertEqual(publication_of(self.coordinator,supplied.ORCHESTRATION,'apply')['state'],'swapped')
        with mock.patch.object(self.profile,'advance',side_effect=AssertionError('duplicate swap')):
            answer=self.publish()
        self.assertEqual(answer['outcome'],'resumed')
        self.assertEqual(publication_of(self.coordinator,supplied.ORCHESTRATION,'apply')['state'],'settled')
if __name__=='__main__':unittest.main()
