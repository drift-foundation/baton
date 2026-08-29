"""Show that the composition orphan case bypasses production recovery.

Run from ``v12/python`` with ``PYTHONPATH=src:.``.  No OCI daemon is needed:
the case under review never calls the adapter operation.
"""

from unittest.mock import patch

from baton_v12.worker_manager.oci import OciAdapter
from tests.manager.test_lifecycle_composition import DockerComposition


case = DockerComposition(
    "test_orphan_recovery_cannot_delete_a_siblings_delivery")
case.setUp()
try:
    with patch.object(
            OciAdapter, "recover_credentials",
            side_effect=AssertionError("the production recovery seam ran")):
        case.test_orphan_recovery_cannot_delete_a_siblings_delivery()
finally:
    case.doCleanups()

print("composition orphan case passed while recover_credentials was disabled")
