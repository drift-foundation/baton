import unittest
from unittest.mock import patch
from tests.manager.test_maintenance import TheSURVIVINGHelpersAreEstablishedAndNotAssumed
from baton_v12.worker_manager import custody
from baton_v12.contracts import ContractRefusal

class MissingImage(TheSURVIVINGHelpersAreEstablishedAndNotAssumed):
    def test_omitting_current_image_does_not_prove_old_helper_absence(self):
        name = custody._custody_identity(custody._recorded_store(self.store), "attempt-1", "result", "normalize")
        before, _ = self.asked(answering=(name,))
        self.assertEqual(before[0]["runtime_id"], "runtime-helper")
        original = custody.surviving_helpers
        def missing(*args, **kwargs):
            kwargs["image_digest"] = None
            return original(*args, **kwargs)
        try:
            with patch.object(custody, "surviving_helpers", side_effect=missing):
                after, seen = self.asked(answering=(name,))
        except ContractRefusal:
            return
        self.assertTrue(after, "unchanged engine/store now reports no writer solely because image is omitted")

if __name__ == "__main__":
    unittest.main(defaultTest="MissingImage.test_omitting_current_image_does_not_prove_old_helper_absence")
