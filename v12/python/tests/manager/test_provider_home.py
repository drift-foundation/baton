"""Simulated manager lifecycle proofs for Job/worker provider homes."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from baton_v12.worker_manager import provider_home as homes
from tests.manager.disk_roots import disk_backed_root


class RetainedProviderHome(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=disk_backed_root())
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "job-work"
        self.selection = dict(authority_uuid="fixture-authority", job_id="fixture-job",
                              worker_id="fixture-worker", attempt_id="a1")

    def acquire(self, **changes):
        return homes.acquire(str(self.root), **dict(self.selection, **changes))

    def test_31_same_job_worker_restart_and_distinct_worker(self):
        one = self.acquire()
        self.assertEqual(one, self.acquire())
        self.assertNotEqual(one["home"], self.acquire(worker_id="review-worker")["home"])
        with self.assertRaises(homes.HomeRefusal):
            self.acquire(job_id=None)

    def test_31a_hostile_ids_only_enter_bounded_digest_components(self):
        for value in ("a/b", ".", "..", "-option", "white space", "\n\0", "é", "x" * 10000):
            with self.subTest(value=value[:30]):
                one = self.acquire(job_id=value, worker_id=value)
                parts = Path(one["home"]).relative_to(self.root).parts
                self.assertEqual(parts[-1], "home")
                for part in parts[:-1]:
                    self.assertRegex(part, "^[0-9a-f]{64}$")

    def test_31b_structured_identity_has_no_join_collisions(self):
        pairs = (("a", "bc"), ("ab", "c"), ("A", "bc"), ("a/b", "c"), ("a", "b/c"))
        paths = {self.acquire(job_id=job, worker_id=worker)["home"] for job, worker in pairs}
        self.assertEqual(len(paths), len(pairs))

    def test_31c_wrong_missing_record_and_symlink_refuse_without_repair(self):
        one = self.acquire()
        record = Path(one["home"]).parent / "record.json"
        original = record.read_bytes()
        value = json.loads(original)
        value["identity"]["job_id"] = "other"
        record.write_text(json.dumps(value))
        wrong = record.read_bytes()
        with self.assertRaises(homes.HomeRefusal):
            self.acquire()
        self.assertEqual(record.read_bytes(), wrong)
        record.unlink()
        with self.assertRaises(homes.HomeRefusal):
            self.acquire()
        self.assertFalse(record.exists())
        record.write_bytes(original)
        record.chmod(0o600)
        home = Path(one["home"])
        home.rmdir()
        home.symlink_to(Path(self.temp.name), target_is_directory=True)
        with self.assertRaises((homes.HomeRefusal, OSError)):
            self.acquire()
        self.assertTrue(home.is_symlink())

    def test_31d_plain_identity_and_holder_live_outside_mounted_home(self):
        one = self.acquire()
        record = json.loads((Path(one["home"]).parent / "record.json").read_text())
        self.assertEqual(record["identity"], {k: v for k, v in self.selection.items() if k != "attempt_id"})
        self.assertEqual(record["holder"], "a1")
        self.assertEqual(list(Path(one["home"]).iterdir()), [])

    def test_32_retention_and_32a_new_job_starts_empty(self):
        one = self.acquire()
        marker = Path(one["home"]) / "provider-owned"
        marker.write_text("simulated private state")
        evidence = dict(attempt_id="a1", runtime="destroyed", cleanup="retained",
                        observed_at="2026-11-24T01:00:00Z", last_activity_at="2026-11-24T00:00:00Z")
        two = self.acquire(attempt_id="a2", previous_runtime=lambda attempt: evidence)
        self.assertEqual(one["home"], two["home"])
        self.assertEqual(marker.read_text(), "simulated private state")
        other = self.acquire(job_id="unrelated")
        self.assertEqual(list(Path(other["home"]).iterdir()), [])
        self.assertTrue(marker.exists())

    def test_34_protected_storage_overlap_in_both_directions(self):
        for excluded in (str(self.root), str(self.root / "nested"), str(self.root.parent)):
            with self.subTest(excluded=excluded), self.assertRaises(homes.HomeRefusal):
                self.acquire(excluded=(excluded,))
        self.assertFalse(self.root.exists())

    def test_38_unknown_stale_uncertain_and_wrong_attempt_hold_then_retry(self):
        one = self.acquire()
        good = dict(attempt_id="a1", runtime="absent", cleanup="complete",
                    observed_at="2026-11-24T01:00:00Z", last_activity_at="2026-11-24T00:00:00Z")
        wrongs = [None, {}, dict(good, attempt_id="other"), dict(good, runtime="uncertain"),
                  dict(good, runtime="stop-ordered"), dict(good, cleanup="pending"),
                  dict(good, observed_at="2026-11-23T23:00:00Z"), dict(good, last_activity_at=None)]
        record = Path(one["home"]).parent / "record.json"
        before = record.read_bytes()
        for bad in wrongs:
            with self.subTest(bad=bad), self.assertRaises(homes.HomePending):
                self.acquire(attempt_id="a2", previous_runtime=lambda attempt: bad)
            self.assertEqual(record.read_bytes(), before)
        self.assertEqual(self.acquire(attempt_id="a2", previous_runtime=lambda attempt: good)["home"], one["home"])

    def test_39_crash_after_record_before_home_creation_replays_same_holder(self):
        original = os.mkdir
        expected_parent = homes.location(str(self.root), homes.identity(**{k: v for k, v in self.selection.items() if k != "attempt_id"}))
        def interrupted(path, *args, **kwargs):
            if path == "home" and kwargs.get("dir_fd") is not None and os.readlink("/proc/self/fd/" + str(kwargs["dir_fd"])) == str(expected_parent):
                raise OSError("simulated crash")
            return original(path, *args, **kwargs)
        with mock.patch.object(os, "mkdir", side_effect=interrupted):
            with self.assertRaises(OSError):
                self.acquire()
        record_path = expected_parent / "record.json"
        before = record_path.read_bytes()
        self.assertEqual(json.loads(before)["state"], "preparing")
        for evidence in (None, {}, {"attempt_id": "a1", "runtime": "start-requested"},
                {"attempt_id": "a1", "runtime": "not-started", "ended_before_start": False},
                {"attempt_id": "other", "runtime": "not-started", "ended_before_start": True}):
            with self.subTest(evidence=evidence), self.assertRaises(homes.HomePending):
                self.acquire(attempt_id="a2", previous_runtime=lambda holder: evidence)
            self.assertEqual(record_path.read_bytes(), before)
            self.assertFalse((expected_parent / "home").exists())
        one = self.acquire()
        self.assertTrue(Path(one["home"]).is_dir())
        self.assertEqual(one, self.acquire())

    def test_ready_home_loss_refuses_instead_of_silently_starting_fresh(self):
        one = self.acquire()
        Path(one["home"]).rmdir()
        with self.assertRaises(homes.HomeRefusal):
            self.acquire()

    def test_32_failed_holder_release_and_return_from_another_job_preserve_bytes(self):
        one = self.acquire()
        marker = Path(one["home"]) / "failed-turn-private-state"
        marker.write_bytes(b"simulated-failed-turn-state")
        # A failed terminal alone is NOT release evidence. This is the normal
        # runtime owner's positive gone/cleanup account, supplied at its seam.
        with self.assertRaises(homes.HomePending):
            self.acquire(attempt_id="after-failure", previous_runtime=lambda attempt: {"attempt_id": attempt, "terminal": "failed"})
        settled = dict(attempt_id="a1", runtime="destroyed", cleanup="complete",
            observed_at="2026-11-24T01:00:00Z", last_activity_at="2026-11-24T00:00:00Z")
        second = self.acquire(attempt_id="after-failure", previous_runtime=lambda attempt: settled)
        other = self.acquire(job_id="unrelated-job")
        other_mount = homes.HomeMount(str(self.root), **dict(self.selection, job_id="unrelated-job"))
        self.assertEqual(other_mount.boundary()[0], other["home"])
        self.assertNotEqual(other["home"], second["home"])
        self.assertEqual(list(Path(other["home"]).iterdir()), [])
        self.assertEqual(self.acquire(attempt_id="after-failure")["home"], one["home"])
        self.assertEqual(marker.read_bytes(), b"simulated-failed-turn-state")


class WorkerHomePreparation(unittest.TestCase):
    """All credential bytes here are explicit synthetic fixture markers."""
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=disk_backed_root())
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / "home"
        self.home.mkdir(mode=0o700)
        self.seed = self.root / "delivered"
        self.seed.write_bytes(b"simulated-seed-only")
        self.seed.chmod(0o600)

    def prepare(self, **changes):
        from baton_v12.provider_policy.home import prepare
        return prepare(str(self.home), **dict(dict(credential_path="state/credential",
                       delivered=str(self.seed), mode="seeded-retained"), **changes))

    def test_40_delivered_reference_never_reads_credential_bytes(self):
        real_open = os.open
        def no_seed_open(path, *args, **kwargs):
            self.assertNotEqual(path, str(self.seed))
            return real_open(path, *args, **kwargs)
        with mock.patch.object(os, "open", side_effect=no_seed_open):
            self.prepare(mode="delivered")
        self.assertTrue((self.home / "state/credential").is_symlink())
        self.assertEqual(os.readlink(self.home / "state/credential"), str(self.seed))

    def test_41_seed_once_and_42_keep_provider_refresh_despite_changed_or_missing_delivery(self):
        self.prepare()
        target = self.home / "state/credential"
        self.assertEqual(target.read_bytes(), b"simulated-seed-only")
        self.assertEqual(target.stat().st_mode & 0o777, 0o600)
        target.write_bytes(b"simulated-provider-refresh")
        self.seed.write_bytes(b"simulated-different-seed")
        self.prepare()
        self.assertEqual(target.read_bytes(), b"simulated-provider-refresh")
        self.seed.unlink()
        self.prepare()
        self.assertEqual(target.read_bytes(), b"simulated-provider-refresh")

    def test_45_same_seed_may_initialize_distinct_empty_homes(self):
        self.prepare()
        old = self.home
        self.home = self.root / "other-home"
        self.home.mkdir(mode=0o700)
        self.prepare()
        self.assertNotEqual((old / "state/credential").stat().st_ino,
                            (self.home / "state/credential").stat().st_ino)
        self.assertEqual(self.seed.read_bytes(), b"simulated-seed-only")

    def test_46_exact_managed_entries_replace_without_touching_provider_state(self):
        import hashlib
        self.prepare()
        session = self.home / "state/session"
        session.write_bytes(b"simulated-private-session")
        def managed(content):
            return [("instructions", content, "sha256:" + hashlib.sha256(content).hexdigest())]
        self.prepare(managed=managed(b"version-one"), provider_paths=("state/session",))
        self.prepare(managed=managed(b"version-two"), provider_paths=("state/session",))
        self.assertEqual((self.home / "instructions").read_bytes(), b"version-two")
        self.assertEqual(session.read_bytes(), b"simulated-private-session")
        before = {p.relative_to(self.home): p.read_bytes() for p in self.home.rglob("*") if p.is_file()}
        self.prepare(managed=())
        self.assertEqual(before, {p.relative_to(self.home): p.read_bytes() for p in self.home.rglob("*") if p.is_file()})

    def test_46_credential_session_and_digest_collisions_refuse_before_writes(self):
        import hashlib
        from baton_v12.provider_policy import PolicyRefusal
        raw = b"instruction"
        hashed = "sha256:" + hashlib.sha256(raw).hexdigest()
        for name, expected in (("state/credential", hashed), ("state/session", hashed), ("instructions", "sha256:" + "0" * 64)):
            with self.subTest(name=name), self.assertRaises(PolicyRefusal):
                self.prepare(managed=[(name, raw, expected)], provider_paths=("state/session",))
            self.assertEqual(list(self.home.iterdir()), [])

    def test_retained_credential_symlink_is_not_read_or_replaced(self):
        from baton_v12.provider_policy import PolicyRefusal
        state = self.home / "state"
        state.mkdir(mode=0o700)
        target = state / "credential"
        target.symlink_to(self.seed)
        with self.assertRaises(PolicyRefusal):
            self.prepare()
        self.assertTrue(target.is_symlink())
        self.assertEqual(self.seed.read_bytes(), b"simulated-seed-only")

    def test_41_second_job_uses_delivery_not_first_jobs_refreshed_seed(self):
        self.prepare()
        first = self.home
        (first / "state/credential").write_bytes(b"simulated-first-job-refresh")
        self.seed.write_bytes(b"simulated-new-delivery")
        self.home = self.root / "second-job-home"
        self.home.mkdir(mode=0o700)
        self.prepare()
        self.assertEqual((self.home / "state/credential").read_bytes(), b"simulated-new-delivery")
        self.assertEqual((first / "state/credential").read_bytes(), b"simulated-first-job-refresh")


class ProviderHomeMount(unittest.TestCase):
    def test_inode_replacement_invalidates_mount(self):
        with tempfile.TemporaryDirectory(dir=disk_backed_root()) as root:
            bound = dict(authority_uuid="fixture", job_id="job", worker_id="worker", attempt_id="a1")
            home_root = str(Path(root) / "job-work")
            one = homes.acquire(home_root, **bound)
            mount = homes.HomeMount(home_root, **bound)
            self.assertEqual(mount.boundary(), (one["home"], homes.TARGET, True))
            path = Path(one["home"])
            path.rename(path.parent / "preserved")
            path.mkdir(mode=0o700)
            with self.assertRaises(homes.HomeRefusal):
                mount.boundary()


class SharedProviderPackageBoundary(unittest.TestCase):
    def test_package_has_only_standard_library_and_package_local_imports(self):
        import ast
        import sys
        from baton_v12 import provider_policy
        for path in Path(provider_policy.__file__).parent.glob("*.py"):
            for node in ast.walk(ast.parse(path.read_text())):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertIn(alias.name.split(".")[0], sys.stdlib_module_names)
                elif isinstance(node, ast.ImportFrom):
                    if node.level:
                        self.assertEqual(node.level, 1)
                    else:
                        self.assertIn(node.module.split(".")[0], sys.stdlib_module_names)

    def test_provider_launch_round_trip_and_cross_attempt_refusal(self):
        import sys
        from baton_v12 import provider_policy
        from baton_v12.contracts import ContractRefusal, digest
        from baton_v12.job_manager import execution_limits
        from baton_v12.worker_manager import launch
        package = Path(provider_policy.__file__).parent.parent
        worker = Path(__file__).resolve().parents[3] / "worker"
        with mock.patch.object(sys, "path", [str(package), str(worker), *sys.path]):
            import baton_worker
            selection = dict(provider="claude", requested_model="simulated-selector",
                             reported_identity="simulated-identity", cli_build="2.1.247")
            profile = dict(schema="baton.single-implementation-runtime-profile/2", provider="claude", model="simulated-selector",
                           reported_identity="simulated-identity", cli_build="2.1.247")
            adapter = provider_policy.adapter(selection, network="fixture-network")
            binding = dict(selection=selection, adapter=adapter, runtime_profile=profile)
            delivered = provider_policy.delivery(binding, adapter_digest=digest(adapter),
                profile_digest=digest(profile), tool_policy_digest=digest(provider_policy.POLICY),
                authority_uuid="fixture-authority", job_id="fixture-job", worker_id="fixture-worker", attempt_id="fixture-attempt")
            limits = execution_limits.resolved(None)
            job = dict(job_id="fixture-job", attempt_id="fixture-attempt",
                       job_input_digest="sha256:" + "1" * 64, job_policy_digest="sha256:" + "2" * 64,
                       runtime_input_digest="sha256:" + "3" * 64, runtime_policy_digest="sha256:" + "4" * 64,
                       execution_limits=limits, execution_limits_digest=digest(limits))
            document = launch.launch_document(session="fixture-session", contract="v12-assignment-1",
                role="implementation", transport=baton_worker.EXCHANGE_TRANSPORT,
                job_execution=job, provider_selection=delivered)
            self.assertEqual(baton_worker.launched(document), launch.payload_of(document))
            import copy
            malformed = copy.deepcopy(document)
            payload = launch.payload_of(malformed)
            payload["provider_selection"]["contract"]["selection"]["requested_model"] = None
            with self.assertRaises(baton_worker.WorkerFault):
                baton_worker.launched(payload)

            delivered["attempt_id"] = "another-attempt"
            with self.assertRaises(ContractRefusal) as caught:
                launch.launch_document(session="fixture-session", contract="v12-assignment-1",
                    role="implementation", transport=baton_worker.EXCHANGE_TRANSPORT,
                    job_execution=job, provider_selection=delivered)
            self.assertIn("another Job or attempt", str(caught.exception))
