"""N4a host guards with patch-only synthetic paths, never a qualified Codex row."""
import copy
from pathlib import Path
import unittest
from baton_v12 import provider_policy as policy
from baton_v12.contracts import ContractRefusal
from tests.manager import codex_fixtures as fixture
from tests.tools import test_pool as existing
from tools import pool, single_worker


class CodexComposition(unittest.TestCase):
    def setUp(self):
        self.fixture = existing.ComposingCase(methodName="runTest")
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)

    def compose(self, **changes):
        values = dict(provider_selection=fixture.SELECTED, cli_build="0.169.0",
                      credentials=["codex=operator-file:synthetic-only"])
        values.update(changes)
        return self.fixture.composing(**values)["worker"]

    def test_no_production_realization_can_be_composed(self):
        with self.assertRaises(pool.PoolRefusal):
            self.compose()

    def test_composition_binds_codex_slot_entry_and_role(self):
        with fixture.simulated(policy):
            worker = self.compose()
            given = pool.admitted(self.fixture.held, worker, "fixture-principal")["deployment"]
            Path(given["nominated_source"]).mkdir(parents=True)
            checked = single_worker._held(given)
            self.assertEqual(checked["credential_slots"], ["codex"])
            self.assertEqual(set(checked["credential_profile"]), {"codex"})
            adapter = checked["provider_contract"]["adapter"]
            self.assertEqual(adapter["entrypoint"], policy.ENTRYPOINTS["codex"])
            self.assertEqual(adapter["context_label"]["roles"], ["implementation"])
            self.assertEqual(adapter["participation_sources"], [])

    def test_composer_refuses_wrong_roles_and_slot_names(self):
        with fixture.simulated(policy):
            for role in ("review", "integration", "publication"):
                with self.subTest(role=role), self.assertRaises(pool.PoolRefusal):
                    self.compose(role=role)
            for credentials in (["claude=operator-file:synthetic-only"],
                    ["codex=operator-file:synthetic-only", "extra=operator-file:other"]):
                with self.subTest(credentials=credentials), self.assertRaises(pool.PoolRefusal):
                    self.compose(credentials=credentials)

    def test_revalidation_refuses_changed_role_slot_and_context(self):
        with fixture.simulated(policy):
            worker = self.compose()
            original = pool.admitted(self.fixture.held, worker, "fixture-principal")["deployment"]
            for changes in ({"launch_role": "review"}, {"launch_role": "integration"},
                            {"credential_slots": ["claude"]},
                            {"credential_profile": {"claude": original["credential_profile"]["codex"]}},
                            {"provider_context": {}}):
                given = dict(copy.deepcopy(original), **changes)
                with self.subTest(changes=changes), self.assertRaises(ContractRefusal):
                    single_worker._held(given, roles=("implementation", "review", "integration"))
