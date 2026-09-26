"""Independent acquisition replay regressions; no engine/provider execution."""
import importlib.util
from pathlib import Path
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import tokens

spec = importlib.util.spec_from_file_location("author_token_tests", Path(__file__).with_name("test_token_lifecycle.py"))
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)


class ReplayReview(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture.TokenLifecycle()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def test_acquisition_replay_after_return_keeps_original_generation(self):
        f = self.fixture
        original = f.held()
        tokens.returned(f.store, original, cessation=f.launched(original))
        replay = f.held()
        self.assertEqual(replay, original, "a completed operation must not acquire fresh permission")
        self.assertEqual(tokens.outstanding(f.store, f.domain), [])

    def test_acquisition_replay_rejects_changed_attempt(self):
        f = self.fixture
        f.held()
        with self.assertRaises(ContractRefusal):
            f.held(attempt="a-different-attempt")

    def test_acquisition_replay_rejects_changed_lifetime(self):
        f = self.fixture
        f.held()
        with self.assertRaises(ContractRefusal):
            f.held(seconds=1800)


if __name__ == "__main__":
    unittest.main()
