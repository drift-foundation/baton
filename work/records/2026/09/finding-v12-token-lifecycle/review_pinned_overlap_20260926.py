"""Pins-only governance is not nested-resource exclusion; seam-level probe."""
import os,tempfile,unittest
from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import ControlStore,tokens
class PinnedOverlap(unittest.TestCase):
    def test_pinned_only_governance_does_not_exclude_nested_roots(self):
        with tempfile.TemporaryDirectory(prefix="v12-review-pinned-overlap-") as root:
            outer=root+"/outer"; inner=outer+"/inner"
            os.makedirs(inner)
            with ControlStore.open(root+"/control.sqlite3",incarnation="review",clock=lambda:"2026-09-26T00:00:00.000Z") as store:
                def row(path,name):
                    stat=os.stat(path)
                    return dict(runtime_attempt_id=name,workspace_device=stat.st_dev,workspace_inode=stat.st_ino)
                governance=tokens.workspace_governance()
                governance.reserve(store,row(outer,"outer-attempt"),operation="outer-start")
                with self.assertRaises(ContractRefusal):
                    governance.reserve(store,row(inner,"inner-attempt"),operation="inner-start")
if __name__=="__main__": unittest.main()
