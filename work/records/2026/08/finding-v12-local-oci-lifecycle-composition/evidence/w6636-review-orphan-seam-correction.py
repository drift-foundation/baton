"""Verify the corrected orphan case crosses and measures adapter recovery.

Run from ``v12/python`` with ``PYTHONPATH=src:.``. The image identity is only
constructor metadata on this recovery path, so no OCI daemon is needed.
"""

from unittest.mock import patch

from baton_v12.worker_manager.oci import OciAdapter
from tests.manager.test_lifecycle_composition import DockerComposition


def prepared_case():
    case = DockerComposition(
        "test_orphan_recovery_cannot_delete_a_siblings_delivery")
    case.setUp()
    case.image_digest = "sha256:" + "a" * 64
    return case


case = prepared_case()
try:
    case.test_orphan_recovery_cannot_delete_a_siblings_delivery()
finally:
    case.doCleanups()

case = prepared_case()
try:
    with patch.object(
            OciAdapter, "recover_credentials",
            return_value={"lifecycle_state": "absent", "orphans": {}}) as recovery:
        with case.assertRaises(AssertionError):
            case.test_orphan_recovery_cannot_delete_a_siblings_delivery()
        recovery.assert_called_once()
finally:
    case.doCleanups()

print("orphan case crossed recover_credentials and rejected a no-op answer")
