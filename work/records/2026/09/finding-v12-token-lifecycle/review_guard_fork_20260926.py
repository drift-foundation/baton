"""Independent HOST-8 fork descriptor and cache probe; no engine/provider."""
import os
import tempfile
import unittest
from baton_v12.worker_manager import ControlStore, workspaces

class ForkOwnership(unittest.TestCase):
    def test_child_does_not_retain_manager_descriptor_or_cache(self):
        with tempfile.TemporaryDirectory(prefix="v12-review-guard-fork-") as root:
            place = root + "/storage"
            os.mkdir(place)
            store = ControlStore.open(root + "/control.sqlite3", incarnation="review-parent", clock=lambda: "2026-09-26T00:00:00.000Z")
            guard = workspaces.hold_manager_instance(store, place)
            read_fd, write_fd = os.pipe()
            child = os.fork()
            if child == 0:
                os.close(read_fd)
                try:
                    try:
                        os.fstat(guard._descriptor)
                        inherited = True
                    except (OSError, TypeError):
                        inherited = False
                    cached = place in workspaces._HELD_GUARDS
                    os.write(write_fd, repr((inherited, cached)).encode())
                finally:
                    os._exit(0)
            os.close(write_fd)
            try:
                result = os.read(read_fd, 100).decode()
                _, status = os.waitpid(child, 0)
                self.assertEqual(status, 0)
                self.assertEqual(result, "(False, False)", "fork child retains parent manager descriptor/cache")
            finally:
                os.close(read_fd)
                guard.release()
                store.close()

if __name__ == "__main__":
    unittest.main()
