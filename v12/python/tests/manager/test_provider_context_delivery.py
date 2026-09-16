"""Private custody checks using real temporary directories and owner admission."""
import os
import pathlib
from unittest import mock

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import context_delivery as delivery
from baton_v12.worker_manager import provider_context as context
from tests.manager.test_provider_context import ContextCase, profile


class Delivery(ContextCase):
    def test_fresh_home_and_exact_reopen_keep_the_original_pins(self):
        first = self.delivered()
        self.assertEqual(first, delivery.adopt_context_use(self.control, self.custody, attempt_id=self.attempt_id))
        self.assertEqual(list(pathlib.Path(first.home).iterdir()), [])
        self.assertFalse(pathlib.Path(first.invocation).exists())

    def test_replaced_home_is_not_adopted(self):
        first = self.delivered()
        home = pathlib.Path(first.home)
        home.rename(home.with_name("old-home"))
        home.mkdir(mode=0o700)
        with self.assertRaises(ContractRefusal):
            delivery.adopt_context_use(self.control, self.custody, attempt_id=self.attempt_id)

    def test_replaced_storage_ancestor_is_not_followed(self):
        self.private.rename(self.private.with_name("old-contexts"))
        self.private.symlink_to(self.private.with_name("old-contexts"), target_is_directory=True)
        with self.assertRaises(ContractRefusal):
            delivery.configured_context_storage(self.control)

    def test_excluded_source_cannot_be_used_as_context_storage(self):
        with self.assertRaises(ContractRefusal):
            delivery.configure_context_storage(self.control, str(self.source), excluded_roots=[str(self.source)], runtime_uid=os.getuid())

    def test_unsupported_runtime_uid_refuses_before_delivery(self):
        with self.assertRaises(ContractRefusal):
            delivery.configure_context_storage(self.control, str(self.private), excluded_roots=[str(self.source)], runtime_uid=os.getuid() + 1)

    def measured(self, first):
        fd, pins = delivery._open_absolute(first.home)
        try:
            return delivery._state(fd, profile())
        finally:
            os.close(fd)

    def test_exact_volatile_credential_link_is_never_opened_or_retained(self):
        first, state = self.state()
        credential = pathlib.Path(first.home) / delivery.CREDENTIAL_PATH
        credential.symlink_to(delivery.CREDENTIAL_TARGET)
        original = os.open
        def guarded(path, *args, **kwargs):
            if str(path) in (".credentials.json", delivery.CREDENTIAL_TARGET):
                self.fail("credential target opened")
            return original(path, *args, **kwargs)
        with mock.patch.object(os, "open", side_effect=guarded):
            entries = self.measured(first)
        self.assertEqual(entries, [(profile()["state_paths"][0], state.read_bytes())])

    def test_regular_credential_file_is_refused_without_reading_it(self):
        first, state = self.state()
        credential = pathlib.Path(first.home) / delivery.CREDENTIAL_PATH
        credential.write_bytes(b"synthetic secret")
        with self.assertRaises(ContractRefusal):
            self.measured(first)

    def test_other_link_hardlink_and_fifo_are_refused(self):
        first, state = self.state()
        bad = pathlib.Path(first.home) / "bad"
        for make in (lambda: bad.symlink_to(state), lambda: os.link(state, bad), lambda: os.mkfifo(bad)):
            with self.subTest(make=make):
                make()
                try:
                    with self.assertRaises(ContractRefusal):
                        self.measured(first)
                finally:
                    bad.unlink()

    def test_unknown_regular_file_bytes_are_not_read(self):
        first, state = self.state()
        bad = pathlib.Path(first.home) / "unknown"
        bad.write_bytes(b"not provider state")
        bad.chmod(0o000)
        self.assertEqual(self.measured(first), [(profile()["state_paths"][0], state.read_bytes())])

    def test_missing_state_size_and_entry_bounds_refuse(self):
        first, state = self.state()
        state.write_bytes(b"x" * 4097)
        with self.assertRaises(ContractRefusal):
            self.measured(first)
        state.unlink()
        with self.assertRaises(ContractRefusal):
            self.measured(first)
        for n in range(65):
            (pathlib.Path(first.home) / str(n)).touch(mode=0o600)
        with self.assertRaises(ContractRefusal):
            self.measured(first)

    def test_sealing_cannot_be_authorized_with_a_caller_absence_receipt(self):
        self.state()
        with self.assertRaises(ContractRefusal):
            delivery.seal_generation(self.control, self.custody, attempt_id=self.attempt_id, exclusion={"state": "absent", "cleanup": "complete"})

    def test_read_protection_is_not_repaired_after_delivery(self):
        first = self.delivered()
        home = pathlib.Path(first.home)
        home.chmod(0o000)
        try:
            with self.assertRaises(ContractRefusal):
                delivery.adopt_context_use(self.control, self.custody, attempt_id=self.attempt_id)
            self.assertEqual(home.stat().st_mode & 0o777, 0)
        finally:
            home.chmod(0o700)
