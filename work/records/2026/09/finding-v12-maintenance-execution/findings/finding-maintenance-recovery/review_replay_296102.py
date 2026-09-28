"""Reviewer deterministic proof over real disposable capacity/worker stores."""
import copy
import unittest
from tests.job_manager.test_managed_integration_capacity import CapacityCase, capacity
from baton_v12.contracts import ContractRefusal, digest
from baton_v12.contracts.manifest import job_input_identity

class Replay(CapacityCase):
    def test_manifest_replay(self):
        store, stage, allocation, answer = self.registered()
        control = self.claimed('prepare-attempt-1', 'prepare-offer-1')
        manifest = self.configured_manifest()
        def admit(value):
            return capacity.admit_integration_execution(store, control,
                orchestration_id=self.ORCHESTRATION, phase='prepare',
                execution_attempt_id='prepare-attempt-1',
                assignment=self.claim_of('prepare-attempt-1'), input_manifest=value)
        first = admit(manifest)
        self.assertEqual(first, admit(manifest))
        other = copy.deepcopy(manifest)
        other['worker_image_digest'] = 'sha256:' + 'f' * 64
        other.pop('manifest_digest')
        other['manifest_digest'] = digest(other)
        self.assertEqual(job_input_identity(manifest), job_input_identity(other))
        self.assertNotEqual(manifest['manifest_digest'], other['manifest_digest'])
        with self.assertRaises(ContractRefusal) as caught:
            admit(other)
        self.assertIn('signature', str(caught.exception))
        forged = copy.deepcopy(manifest)
        forged['manifest_digest'] = 'sha256:' + '0' * 64
        with self.assertRaises(ContractRefusal): admit(forged)
        with self.assertRaises(ContractRefusal): admit(None)
        self.assertEqual(first, admit(manifest))

if __name__ == '__main__': unittest.main()
