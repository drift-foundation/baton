"""Exact-engine evidence must fail closed in the production reclaim adapter."""
import json
import unittest
from tools.job_manager import _ReclaimAdapter

class ReclaimObservation(unittest.TestCase):
    def test_missing_engine_socket_is_not_container_absence(self):
        adapter = _ReclaimAdapter('docker', lambda argv: {'status': 1, 'stdout': '', 'stderr': 'dial unix /run/docker.sock: connect: no such file or directory'})
        self.assertEqual(adapter.observe('container-a')['state'], 'uncertain')

    def test_another_container_is_not_exact_termination_evidence(self):
        adapter = _ReclaimAdapter('docker', lambda argv: {'status': 0, 'stdout': json.dumps([{'Id': 'container-b', 'State': {'Running': False}}]), 'stderr': ''})
        self.assertEqual(adapter.observe('container-a')['state'], 'uncertain')

    def test_nonboolean_running_is_not_quiescence(self):
        adapter = _ReclaimAdapter('docker', lambda argv: {'status': 0, 'stdout': json.dumps([{'Id': 'container-a', 'State': {'Running': None}}]), 'stderr': ''})
        self.assertEqual(adapter.observe('container-a')['state'], 'uncertain')

if __name__ == '__main__':
    unittest.main()
