"""W385694: versioned proposal bounds at both real filesystem boundaries."""
import copy
import pathlib
import sys
import tempfile
import unittest

from baton_v12.contracts import ContractRefusal, digest
from baton_v12.job_manager import role_contract, templates
from baton_v12.worker_manager import sealing
from tests.manager import disk_roots

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "worker"))
import baton_worker


class ProposalRevision(unittest.TestCase):
    def test_only_proposal_bytes_and_explicit_identities_change(self):
        old = role_contract.handoff_document()
        new = role_contract.contract_for(role_contract.PROPOSAL100M_TEMPLATE)
        expected = copy.deepcopy(old)
        expected.update(schema=role_contract.PROPOSAL100M_CONTRACT_SCHEMA,
                        template=role_contract.PROPOSAL100M_TEMPLATE)
        expected["outputs"][0]["constraints"]["max_bytes"] = 104857600
        self.assertEqual(new, expected)
        self.assertEqual(role_contract.check_any_role_contract(new), new)
        self.assertNotEqual(role_contract.contract_digest(old), role_contract.contract_digest(new))
        self.assertTrue(role_contract.is_handoff_capable(new["template"]))
        self.assertEqual(templates.DEFAULT_TEMPLATE, templates.IMPLEMENTATION_REVIEW)
        self.assertEqual(role_contract.handoff_document(), old)

    def test_old_registered_bytes_and_new_descriptor_identity_are_pinned(self):
        expected = (
            (templates.IMPLEMENTATION_REVIEW, "83a737b83b7615981e1437895ceb0ddb5ba8a13fd47097366e817135a308c1eb"),
            (templates.IMPLEMENTATION_REVIEW_2, "2388d55d0a469efec272bb0f67bfa3ec2b5c3d6c8c8afbd3d5f244117ae4e2fe"),
            (templates.IMPLEMENTATION_REVIEW_3, "0589d8544907d5753688a234addfb879760691c41c687805c243a98b0cc3240b"))
        for version, checksum in expected:
            self.assertEqual(digest(templates.template_document(version)), "sha256:" + checksum)
        self.assertEqual(role_contract.contract_digest(role_contract.handoff_document()),
                         "sha256:66f2c37d501fdc66558aabec35430d1945e2671e76e341991fa263dab05fa38c")
        self.assertEqual(role_contract.contract_digest(role_contract.contract_for(role_contract.PROPOSAL100M_TEMPLATE)),
                         "sha256:cf29ab07e507089520ba0c165b0661df0054f17fe35b986b4cf63c9ac713792e")

    def test_wrong_revision_or_limit_is_refused(self):
        for field in ("schema", "template"):
            doc = role_contract.contract_for(role_contract.PROPOSAL100M_TEMPLATE)
            doc[field] += "-unsupported"
            with self.subTest(field=field), self.assertRaises(ContractRefusal):
                role_contract.check_any_role_contract(doc)
        for template in (role_contract.HANDOFF_TEMPLATE, role_contract.PROPOSAL100M_TEMPLATE):
            for index in range(5):
                doc = role_contract.contract_for(template)
                doc["outputs"][index]["constraints"]["max_bytes"] += 1
                with self.subTest(template=template, index=index), self.assertRaises(ContractRefusal):
                    role_contract.check_any_role_contract(doc)


class WorkerAndManagerMeasurement(unittest.TestCase):
    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix="proposal100m-", dir=disk_roots.disk_backed_root()))
        self.addCleanup(disk_roots.remove_owned_root, str(self.root))
        self.source = self.root / "source"
        self.source.mkdir()

    def declaration(self, version, index=0):
        return role_contract.contract_for(version)["outputs"][index]

    def content(self, size):
        with (self.source / "payload").open("wb") as f:
            f.truncate(size)

    def both(self, declaration, size):
        self.content(size)
        measured = baton_worker.measured(str(self.source), declaration["constraints"])
        held = sealing._staged(str(self.source), str(self.root / "custody"), declaration, declaration["name"])
        self.assertEqual(measured["total_bytes"], size)
        return measured, held

    def test_new_proposal_accepts_above_legacy_and_exact_ceiling(self):
        declaration = self.declaration(role_contract.PROPOSAL100M_TEMPLATE)
        for size in (1048577, 104857600):
            with self.subTest(size=size):
                measured, held = self.both(declaration, size)
                self.assertEqual(measured, held)

    def test_old_ceiling_and_new_overflow_are_enforced_by_both(self):
        for version, size in ((role_contract.HANDOFF_TEMPLATE,1048577),
                              (role_contract.PROPOSAL100M_TEMPLATE,104857601)):
            declaration = self.declaration(version)
            self.content(size)
            with self.subTest(version=version):
                with self.assertRaises(baton_worker.WorkerFault):
                    baton_worker.measured(str(self.source), declaration["constraints"])
                with self.assertRaises(ContractRefusal):
                    sealing._staged(str(self.source), str(self.root / "custody"), declaration, declaration["name"])

    def test_old_proposal_exact_ceiling_remains_valid(self):
        measured, held = self.both(self.declaration(role_contract.HANDOFF_TEMPLATE), 1048576)
        self.assertEqual(measured, held)

    def test_entry_and_link_limits_still_refuse_at_both_boundaries(self):
        declaration = self.declaration(role_contract.PROPOSAL100M_TEMPLATE)
        for index in range(101):
            (self.source / str(index)).write_bytes(b"x")
        with self.assertRaises(baton_worker.WorkerFault):
            baton_worker.measured(str(self.source), declaration["constraints"])
        with self.assertRaises(ContractRefusal):
            sealing._staged(str(self.source), str(self.root / "custody"), declaration, declaration["name"])
        for path in self.source.iterdir():
            path.unlink()
        (self.source / "link").symlink_to(self.root)
        with self.assertRaises(baton_worker.WorkerFault):
            baton_worker.measured(str(self.source), declaration["constraints"])
        with self.assertRaises(ContractRefusal):
            sealing._staged(str(self.source), str(self.root / "custody"), declaration, declaration["name"])

    def test_other_outputs_remain_at_one_mib(self):
        for index in range(1,5):
            declaration = self.declaration(role_contract.PROPOSAL100M_TEMPLATE,index)
            self.content(1048577)
            with self.subTest(output=declaration["name"]):
                with self.assertRaises(baton_worker.WorkerFault):
                    baton_worker.measured(str(self.source), declaration["constraints"])
                with self.assertRaises(ContractRefusal):
                    sealing._staged(str(self.source), str(self.root / "custody"), declaration, declaration["name"])
