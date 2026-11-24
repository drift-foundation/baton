import json, os, unittest
from pathlib import Path
from tests.tools.test_pool import PoolCase
from tools import bootstrap
class Drop(PoolCase):
    def test_drop(self):
        self.admitting()
        before = [o["worker_id"] for o in self.written()["workers"]]
        document = self.document(); document.pop("jobs", None)
        with open(os.devnull, "w") as quiet:
            bootstrap.prepare(document, stream=quiet)
        after = [o["worker_id"] for o in self.written()["workers"]]
        print("BEFORE", before, "AFTER", after)
if __name__ == "__main__":
    unittest.main()
