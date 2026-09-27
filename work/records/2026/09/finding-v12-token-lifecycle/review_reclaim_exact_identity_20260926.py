"""Independent exact identity edge cases for reclaim cessation evidence."""
import json
import unittest
from tools.job_manager import _ReclaimAdapter

class ExactIdentity(unittest.TestCase):
    def test_empty_id_does_not_prove_requested_container_stopped(self):
        body = json.dumps({'Id': '', 'State': {'Running': False}})
        self.assertIsNone(_ReclaimAdapter._described('container-a', body))

    def test_different_full_identity_with_shared_prefix_is_not_accepted(self):
        body = json.dumps({'Id': 'container-a-other', 'State': {'Running': False}})
        self.assertIsNone(_ReclaimAdapter._described('container-a', body))

    def test_missing_another_named_container_is_not_absence(self):
        self.assertEqual(_ReclaimAdapter._missing('container-a', 'Error: No such container: container-a-other'), 'uncertain')

if __name__ == '__main__':
    unittest.main()
