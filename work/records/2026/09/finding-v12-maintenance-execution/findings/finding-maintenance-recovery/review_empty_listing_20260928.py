"""Exercise current reconciliation with literal empty stdout; no engine/store."""
import unittest
from baton_v12.worker_manager import custody, oci

class EmptyListing(unittest.TestCase):
    def test_empty_listing_is_no_candidate(self):
        for stdout in ('', '\n', '  \n'):
            with self.subTest(stdout=repr(stdout)):
                seen=[]
                def engine(argv, *, seconds):
                    seen.append(list(argv))
                    return dict(status=0, stdout=stdout, stderr='')
                self.assertIsNone(custody._reconciled('docker', oci.EnginePort(engine), name='baton-custody-review', image_digest='sha256:'+'c'*64))
                self.assertEqual([v[1] for v in seen], ['ps'])

if __name__ == '__main__':
    unittest.main()
