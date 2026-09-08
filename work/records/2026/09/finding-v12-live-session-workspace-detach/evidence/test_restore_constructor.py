"""Actual fresh/replacement construction; no privileged or external operation."""
from contextlib import ExitStack
from pathlib import Path
import stat
import tempfile
import time
import unittest
from unittest import mock
import uuid

import live_controller_restore_constructor as candidate
import test_restored_only as restoration


class ConstructorTests(unittest.TestCase):
    def boundaries(self, stack):
        ownership = stack.enter_context(mock.patch.object(candidate.os, "chown"))
        forbidden = []
        for module, name in ((candidate, "docker"), (candidate.base, "docker"),
                             (candidate.subprocess, "run"), (candidate.subprocess, "Popen"),
                             (candidate, "runtime_apis")):
            forbidden.append(stack.enter_context(mock.patch.object(module, name, side_effect=AssertionError("external operation forbidden"))))
        credentials = mock.Mock()
        credentials.materialize.side_effect = AssertionError("credential operation forbidden")
        return ownership, forbidden, credentials

    def test_actual_fresh_and_replacement_preserve_arm_and_private_state(self):
        with tempfile.TemporaryDirectory(prefix="baton-w106673-constructor-") as directory, ExitStack() as stack:
            ownership, forbidden, credentials = self.boundaries(stack)
            root = Path(directory)
            deadline = time.monotonic() + 420
            first = candidate.Fixture(root, "restored-first", "unused-network", credentials, deadline)
            self.assertEqual(first.arm, "restored-first")
            self.assertEqual(first.directory, root / "restored-first")
            self.assertEqual(first.workspace, first.directory / "workspace")
            self.assertEqual(first.workspace_pin, candidate.base.pin(first.workspace))
            self.assertEqual(stat.S_IMODE(first.workspace.stat().st_mode), 0o2775)
            self.assertEqual(first.session_home, first.directory / "session-private")
            self.assertEqual({p.name for p in first.session_home.iterdir()}, {"work", "home", "cache"})
            for path in (first.session_home, *(first.session_home / name for name in ("work", "home", "cache"))):
                self.assertTrue(path.is_dir())
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o700)
            self.assertEqual(str(uuid.UUID(first.session)), first.session)
            self.assertFalse(first.resume)
            ownership.assert_has_calls([mock.call(first.workspace, 0, candidate.GID),
                                       mock.call(first.session_home, candidate.GID, candidate.GID),
                                       *(mock.call(first.session_home / name, candidate.GID, candidate.GID) for name in ("work", "home", "cache"))])
            self.assertEqual(ownership.call_count, 5)
            private_file = first.session_home / "home" / "retained-fixture-data"
            private_file.write_bytes(b"existing private session fixture")
            session_pin = candidate.base.pin(first.session_home)
            second = candidate.Fixture(root, "restored-second", "unused-network", credentials, deadline,
                                       workspace=first.workspace, session_home=first.session_home,
                                       session=first.session, resume=True)
            self.assertEqual(second.arm, "restored-second")
            self.assertEqual(second.directory, root / "restored-second")
            self.assertEqual(second.workspace, first.workspace)
            self.assertEqual(second.workspace_pin, first.workspace_pin)
            self.assertEqual(second.session_home, first.session_home)
            self.assertEqual(candidate.base.pin(second.session_home), session_pin)
            self.assertEqual(second.session, first.session)
            self.assertTrue(second.resume)
            self.assertEqual(private_file.read_bytes(), b"existing private session fixture")
            self.assertFalse((second.directory / "session-private").exists())
            self.assertFalse((second.directory / "workspace").exists())
            self.assertEqual(ownership.call_count, 5)
            for fixture in (first, second):
                self.assertIsNone(fixture.container)
                self.assertIsNone(fixture.delivery)
                self.assertEqual(fixture.active_turn, 0)
                self.assertEqual(fixture.live_stage, "created")
                self.assertIs(fixture.credentials, credentials)
                self.assertEqual(fixture.deadline, deadline)
            for boundary in forbidden:
                boundary.assert_not_called()
            self.assertEqual(credentials.mock_calls, [])

    def test_actual_constructor_refuses_unsupported_arms(self):
        for arm in ("retained-first", "cache", "unsupported"):
            with self.subTest(arm=arm), tempfile.TemporaryDirectory(prefix="baton-w106673-invalid-arm-") as directory, ExitStack() as stack:
                _, forbidden, credentials = self.boundaries(stack)
                with self.assertRaisesRegex(candidate.wire.Refusal, "^diagnostic-arm-invalid$"):
                    candidate.Fixture(Path(directory), arm, "unused-network", credentials, time.monotonic() + 420)
                for boundary in forbidden:
                    boundary.assert_not_called()
                self.assertEqual(credentials.mock_calls, [])


if __name__ == "__main__":
    restoration.candidate = candidate
    restoration.prior.host = candidate
    restoration.prior.worker = candidate.wire
    suite = unittest.TestSuite((unittest.defaultTestLoader.loadTestsFromModule(restoration.prior),
                               unittest.defaultTestLoader.loadTestsFromTestCase(restoration.RestorationTests),
                               unittest.defaultTestLoader.loadTestsFromTestCase(ConstructorTests)))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
