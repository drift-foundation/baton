"""K probes for W385694 candidate 775fcfe4 (review-only; deterministic)."""
import copy, os, pathlib, shutil, sys, tempfile, unittest
from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import role_contract
from baton_v12.worker_manager import sealing
from tests.manager import disk_roots
sys.path.insert(0, str(pathlib.Path("..", "worker").resolve()))
import baton_worker

REAL = "/home/sl/src/baton/work/records/2026/11/finding-v12-retained-recovery-admission/evidence/output-limit-recovery-20261122/proposal"


class K(unittest.TestCase):
    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix="k694-", dir=disk_roots.disk_backed_root()))
        self.addCleanup(disk_roots.remove_owned_root, str(self.root))
        self.src = self.root / "proposal"
        shutil.copytree(REAL, self.src)   # copy: never touch retained evidence

    def decl(self, template):
        return role_contract.contract_for(template)["outputs"][0]

    def test_P1_real_w385624_proposal_old_refuses_new_accepts(self):
        total = sum(p.stat().st_size for p in self.src.rglob("*") if p.is_file())
        print("P1-REAL-BYTES", total)
        old = self.decl(role_contract.HANDOFF_TEMPLATE)
        try:
            baton_worker.measured(str(self.src), old["constraints"]); print("P1-OLD-WORKER", "ACCEPTED?!")
        except baton_worker.WorkerFault as e:
            print("P1-OLD-WORKER", "refused:", str(e)[:120])
        try:
            sealing._staged(str(self.src), str(self.root / "c-old"), old, old["name"]); print("P1-OLD-MANAGER", "ACCEPTED?!")
        except ContractRefusal as e:
            print("P1-OLD-MANAGER", "refused:", e.code)
        new = self.decl(role_contract.PROPOSAL100M_TEMPLATE)
        m = baton_worker.measured(str(self.src), new["constraints"])
        h = sealing._staged(str(self.src), str(self.root / "c-new"), new, new["name"])
        print("P1-NEW", m["total_bytes"], m == h)
        self.assertEqual(m, h)

    def test_P2_cross_revision_exactness(self):
        d3 = role_contract.contract_for(role_contract.HANDOFF_TEMPLATE)
        d3["outputs"][0]["constraints"]["max_bytes"] = 104857600
        d4 = role_contract.contract_for(role_contract.PROPOSAL100M_TEMPLATE)
        d4["outputs"][0]["constraints"]["max_bytes"] = 1048576
        d4b = role_contract.contract_for(role_contract.PROPOSAL100M_TEMPLATE)
        d4b["outputs"][1]["constraints"]["max_bytes"] = 104857600
        for name, doc in (("3-with-100M", d3), ("4-with-1M", d4), ("4-other-output-100M", d4b)):
            try:
                role_contract.check_any_role_contract(doc); print("P2", name, "ACCEPTED?!")
            except ContractRefusal as e:
                print("P2", name, "refused", e.code)


if __name__ == "__main__":
    unittest.main(verbosity=2)
