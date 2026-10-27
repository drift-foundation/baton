import json, unittest
from tests.tools import test_retry_task_lineage as lineage


class Probe(lineage.TheRetriedJobReachesItsOwnRuntimes):
    def runTest(self):
        held = self.admitted_retry()
        first = self.stage_of(held["jobs"], held["composed"], self.job_id)
        print(json.dumps(first, indent=2, default=str))


unittest.TextTestRunner(verbosity=0).run(unittest.TestSuite([Probe()]))
