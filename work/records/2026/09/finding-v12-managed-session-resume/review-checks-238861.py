"""Independent fresh-entrypoint and workspace boundary checks."""
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path[:0] = [str(HERE), str(ROOT / 'v12/python/src'), str(ROOT / 'v12/python')]
from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import ControlStore, workspaces
from tests.job_manager import fixtures
import supervisor
import test_generated_packet


class Boundaries(test_generated_packet.TheGeneratedPacketRunsThroughMain):
    def test_existing_different_workspace_is_preserved_and_refused(self):
        packet = self.main_packet()
        other = Path(self.root) / 'preexisting-workspace'
        other.mkdir(mode=0o700)
        with ControlStore.open(packet['deployment']['control_store'],
                               incarnation='review-conflict', clock=lambda: fixtures.NOW) as control:
            workspaces.configure_workspace_storage(control, str(other))
            with self.assertRaises(ContractRefusal) as caught:
                supervisor.prepare(control, packet)
            self.assertIn('already configured', str(caught.exception))
            self.assertEqual(workspaces.configured_workspace_storage(control).place, str(other))

    def test_context_cannot_overlap_derived_workspace(self):
        packet = self.main_packet()
        nested = Path(self.storage) / 'private-context-overlap'
        nested.mkdir(mode=0o700)
        packet['context']['storage_path'] = str(nested)
        with ControlStore.open(packet['deployment']['control_store'],
                               incarnation='review-overlap', clock=lambda: fixtures.NOW) as control:
            with self.assertRaises(ContractRefusal) as caught:
                supervisor.prepare(control, packet)
            self.assertIn('overlaps', str(caught.exception))
            self.assertEqual(workspaces.configured_workspace_storage(control).place, self.storage)


if __name__ == '__main__':
    suite = unittest.TestSuite()
    for cls in (Boundaries, test_generated_packet.TheGeneratedPacketRunsThroughMain):
        for name in sorted(n for n in vars(cls) if n.startswith('test_')):
            suite.addTest(cls(name))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(not result.wasSuccessful())
