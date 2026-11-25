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


    def test_missing_initialized_credential_never_reseeds(self):
        from baton_v12.provider_policy import PolicyRefusal
        self.prepare()
        (self.home / "state/credential").unlink()
        before = self.seed.read_bytes()
        with mock.patch.object(os, "read", side_effect=AssertionError("must not read seed")):
            with self.assertRaisesRegex(PolicyRefusal, "credential recovery required"):
                self.prepare()
        self.assertFalse((self.home / "state/credential").exists())
        self.assertEqual(self.seed.read_bytes(), before)

    def test_interrupted_seed_requires_recovery_without_retry(self):
        from baton_v12.provider_policy import PolicyRefusal
        with mock.patch.object(os, "link", side_effect=OSError("simulated interrupted copy")):
            with self.assertRaises(OSError):
                self.prepare()
        self.assertFalse((self.home / "state/credential").exists())
        with self.assertRaisesRegex(PolicyRefusal, "credential recovery required"):
            self.prepare()

    def test_marker_loss_corruption_wrong_path_and_permissions_refuse(self):
        from baton_v12.provider_policy import PolicyRefusal
        from baton_v12.provider_policy.home import CREDENTIAL_STATE
        self.prepare()
        marker = self.home / CREDENTIAL_STATE
        original = marker.read_bytes()
        for raw in (b"{}", b"not-json", original.replace(b"state/credential", b"other")):
            marker.write_bytes(raw)
            with self.assertRaisesRegex(PolicyRefusal, "credential recovery required"):
                self.prepare()
        marker.write_bytes(original); marker.chmod(0o644)
        with self.assertRaisesRegex(PolicyRefusal, "credential recovery required"):
            self.prepare()
        marker.unlink()
        with self.assertRaisesRegex(PolicyRefusal, "credential recovery required"):
            self.prepare()
        self.assertEqual((self.home / "state/credential").read_bytes(), b"simulated-seed-only")

    def test_lifecycle_metadata_cannot_be_managed_or_credential(self):
        import hashlib
        from baton_v12.provider_policy import PolicyRefusal
        from baton_v12.provider_policy.home import CREDENTIAL_STATE
        raw = b"synthetic instructions"
        with self.assertRaises(PolicyRefusal):
            self.prepare(managed=[(CREDENTIAL_STATE, raw, "sha256:" + hashlib.sha256(raw).hexdigest())])
        with self.assertRaises(PolicyRefusal):
            self.prepare(credential_path=CREDENTIAL_STATE)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_external_receipt_preserves_refresh_without_source_callback(self):
        initialize = mock.Mock(side_effect=lambda: (self.prepare(), "first delivery")[1])
        self.assertEqual(homes.initialize_credential(str(self.home), str(self.root), "state/credential", initialize), "first delivery")
        target = self.home / "state/credential"
        target.write_bytes(b"simulated refresh")
        self.seed.unlink()
        self.assertIsNone(homes.initialize_credential(str(self.home), str(self.root), "state/credential", initialize))
        initialize.assert_called_once()
        self.assertEqual(target.read_bytes(), b"simulated refresh")
        receipt = (self.root / "credential.json").read_bytes()
        self.assertNotIn(b"simulated", receipt)
        self.assertNotIn(str(self.seed).encode(), receipt)

    def test_external_receipt_catches_loss_of_both_worker_marker_and_credential(self):
        from baton_v12.provider_policy.home import CREDENTIAL_STATE
        homes.initialize_credential(str(self.home), str(self.root), "state/credential", self.prepare)
        (self.home / CREDENTIAL_STATE).unlink()
        (self.home / "state/credential").unlink()
        initialize = mock.Mock(side_effect=AssertionError("must not reseed"))
        with self.assertRaisesRegex(homes.HomeRefusal, "credential recovery required"):
            homes.initialize_credential(str(self.home), str(self.root), "state/credential", initialize)
        initialize.assert_not_called()

    def test_external_pending_receipt_requires_recovery_after_crash(self):
        def interrupted():
            self.prepare()
            raise OSError("simulated crash after copy")
        with self.assertRaises(OSError):
            homes.initialize_credential(str(self.home), str(self.root), "state/credential", interrupted)
        with self.assertRaisesRegex(homes.HomeRefusal, "credential recovery required"):
            homes.initialize_credential(str(self.home), str(self.root), "state/credential", self.prepare)
        self.assertEqual((self.home / "state/credential").read_bytes(), b"simulated-seed-only")

    def test_external_missing_receipt_does_not_adopt_unattributed_copy(self):
        homes.initialize_credential(str(self.home), str(self.root), "state/credential", self.prepare)
        (self.root / "credential.json").unlink()
        with self.assertRaisesRegex(homes.HomeRefusal, "credential recovery required"):
            homes.initialize_credential(str(self.home), str(self.root), "state/credential", self.prepare)



class WorkerInstructionDelivery(unittest.TestCase):
    """W385853. Pure policy proofs; no provider, image or vendor loader."""
    SELECTED = dict(provider="claude", requested_model="simulated-selector",
                    reported_identity="simulated-identity", cli_build="2.1.247")

    def adapter(self):
        from baton_v12 import provider_policy
        return provider_policy.adapter(self.SELECTED, network="bridge")

    def test_packaged_copy_is_byte_identical_to_the_canonical_document(self):
        import hashlib
        from baton_v12 import provider_policy
        canonical = (Path(__file__).resolve().parents[4] / "docs/V12-WORKER-INSTRUCTIONS.md").read_bytes()
        packaged = (Path(provider_policy.__file__).parent / provider_policy.INSTRUCTIONS_FILE).read_bytes()
        self.assertEqual(packaged, canonical)
        self.assertEqual(provider_policy.worker_instructions(), canonical)
        (entry,) = self.adapter()["managed_entries"]
        self.assertEqual(entry, {"path": ".claude/CLAUDE.md", "kind": "worker-instructions", "bytes": len(canonical),
                                 "sha256": "sha256:" + hashlib.sha256(canonical).hexdigest()})
        self.assertLessEqual(len(canonical), provider_policy.INSTRUCTIONS_BOUND)

    def test_packaged_copy_travels_as_package_data(self):
        text = (Path(__file__).resolve().parents[2] / "pyproject.toml").read_text()
        self.assertIn('"provider_policy/worker_instructions.md"', text)
        recipe = (Path(__file__).resolve().parents[3] / "worker/Dockerfile.claude").read_text()
        self.assertIn("COPY python/src/baton_v12/provider_policy /opt/baton/provider_policy", recipe)

    def test_changed_absent_empty_or_oversized_instructions_refuse(self):
        from baton_v12 import provider_policy
        adapter = self.adapter()
        with mock.patch.object(provider_policy, "worker_instructions", return_value=b"one byte differs"):
            with self.assertRaises(provider_policy.PolicyRefusal):
                provider_policy.managed_payloads(adapter)
            with self.assertRaises(provider_policy.PolicyRefusal):
                provider_policy.validate_adapter(adapter, self.SELECTED, adapter_digest=provider_policy.digest(adapter),
                                                 tool_policy_digest=provider_policy.digest(provider_policy.POLICY))
        with mock.patch.object(provider_policy, "INSTRUCTIONS_FILE", "absent.md"), self.assertRaises(provider_policy.PolicyRefusal):
            provider_policy.adapter(self.SELECTED, network="bridge")
        with mock.patch.object(provider_policy, "INSTRUCTIONS_BOUND", 100), self.assertRaises(provider_policy.PolicyRefusal):
            provider_policy.worker_instructions()
        with tempfile.TemporaryDirectory(dir=disk_backed_root()) as root:
            Path(root, "empty.md").write_bytes(b"")
            with mock.patch.object(provider_policy, "INSTRUCTIONS_FILE", os.path.join(root, "empty.md")), \
                    self.assertRaises(provider_policy.PolicyRefusal):
                provider_policy.worker_instructions()

    def test_managed_payloads_are_placed_replaced_and_leave_provider_state(self):
        from baton_v12 import provider_policy
        from baton_v12.provider_policy.home import prepare
        with tempfile.TemporaryDirectory(dir=disk_backed_root()) as root:
            home = Path(root, "home")
            home.mkdir(mode=0o700)
            seed = Path(root, "delivered")
            seed.write_bytes(b"simulated-seed-only")
            adapter = self.adapter()
            operands = dict(credential_path=adapter["credential"]["path"], delivered=str(seed), mode="delivered",
                            managed=provider_policy.managed_payloads(adapter))
            prepare(str(home), **operands)
            placed = home / ".claude/CLAUDE.md"
            self.assertEqual(placed.read_bytes(), provider_policy.worker_instructions())
            self.assertEqual(placed.stat().st_mode & 0o777, 0o600)
            placed.write_bytes(b"simulated provider rewrite")
            (home / ".claude/own").write_bytes(b"simulated provider state")
            prepare(str(home), **operands)
            self.assertEqual(placed.read_bytes(), provider_policy.worker_instructions())
            self.assertEqual((home / ".claude/own").read_bytes(), b"simulated provider state")
            self.assertTrue((home / ".claude/.credentials.json").is_symlink())
        for changed in ({"path": ".claude/.credentials.json"}, {"sha256": "sha256:" + "0" * 64}, {"bytes": 1}, {"kind": "other"}):
            with self.subTest(changed=changed), self.assertRaises(provider_policy.PolicyRefusal):
                provider_policy.managed_payloads(dict(adapter, managed_entries=[dict(adapter["managed_entries"][0], **changed)]))
        for entries in ([], adapter["managed_entries"] * 2, None):
            with self.subTest(entries=entries), self.assertRaises(provider_policy.PolicyRefusal):
                provider_policy.managed_payloads(dict(adapter, managed_entries=entries))

    def test_label_names_role_instructions_and_what_does_not_apply(self):
        import hashlib
        from baton_v12 import provider_policy
        adapter = self.adapter()
        self.assertEqual(adapter["context_label"], {"schema": "baton.native-worker-context/1", "placement": "prompt-prefix",
            "roles": ["implementation", "review"], "bound": 2048,
            "template_sha256": "sha256:" + hashlib.sha256(provider_policy.LABEL_TEMPLATE.encode()).hexdigest()})
        labels = {role: provider_policy.context_label(adapter, role) for role in ("implementation", "review")}
        self.assertNotEqual(labels["implementation"], labels["review"])
        for role, raw in labels.items():
            text = raw.decode("ascii")
            self.assertLessEqual(len(raw), 2048)
            self.assertTrue(text.startswith("[Baton execution context: baton.native-worker-context/1]\n"))
            self.assertTrue(text.endswith("removes no restriction.\n"))
            self.assertEqual(text.count("Assigned role: "), 1)
            for required in ("You are running as a Baton native v12 worker.", "Assigned role: " + role + ".",
                             "/run/baton/provider-home/.claude/CLAUDE.md", adapter["managed_entries"][0]["sha256"][7:],
                             "Does not apply to you:", "AGENTS.md", "docs/HOST-INTEGRATION.md", "v11 claims",
                             "Protected-main and task boundaries", "It grants no permission"):
                self.assertIn(required, text)
            for absent in ("resum", "conversation", "session", "attempt", "/output", "{", "}"):
                self.assertNotIn(absent, text)
            self.assertEqual(provider_policy.context_record(adapter, role), {"schema": "baton.native-worker-context/1", "role": role,
                "context_label_digest": "sha256:" + hashlib.sha256(raw).hexdigest(),
                "worker_instructions_digest": adapter["managed_entries"][0]["sha256"]})
            prompt = "task text\n-- with its own lines\n"
            self.assertEqual(provider_policy.labelled(adapter, role, prompt), text + "\n" + prompt)
        with self.assertRaises(provider_policy.PolicyRefusal):
            provider_policy.labelled(adapter, "review", b"bytes")

    def test_label_refuses_unknown_role_changed_template_and_oversize(self):
        from baton_v12 import provider_policy
        adapter = self.adapter()
        for role in ("integration", "publication", "reconciliation", "Implementation", "", None, ["review"]):
            with self.subTest(role=role), self.assertRaises(provider_policy.PolicyRefusal):
                provider_policy.context_label(adapter, role)
        for member, value in (("template_sha256", "sha256:" + "0" * 64), ("roles", ["implementation", "review", "integration"]),
                              ("bound", 4096), ("placement", "home-file"), ("schema", "baton.native-worker-context/2")):
            with self.subTest(member=member), self.assertRaises(provider_policy.PolicyRefusal):
                provider_policy.context_label(dict(adapter, context_label=dict(adapter["context_label"], **{member: value})), "review")
        for document in (dict(adapter, managed_entries=[]), {key: adapter[key] for key in adapter if key != "context_label"},
                         dict(adapter, provider="simulated-unknown"), None):
            with self.subTest(document=type(document).__name__), self.assertRaises(provider_policy.PolicyRefusal):
                provider_policy.context_label(document, "review")
        long = provider_policy.LABEL_TEMPLATE + "x" * 2048
        with mock.patch.object(provider_policy, "LABEL_TEMPLATE", long):
            grown = provider_policy.adapter(self.SELECTED, network="bridge")
            self.assertNotEqual(provider_policy.digest(grown), provider_policy.digest(adapter))
            with self.assertRaises(provider_policy.PolicyRefusal):
                provider_policy.context_label(grown, "review")

    def test_earlier_adapter_shape_and_undeclared_realization_refuse(self):
        import copy
        from baton_v12 import provider_policy
        adapter = self.adapter()
        # The 317351e7 shape: empty managed list, no label member.
        earlier = {key: value for key, value in adapter.items() if key != "context_label"}
        earlier["managed_entries"] = []
        earlier["realization"] = dict(earlier["realization"], user_configuration="private-home-empty-managed-entries")
        with self.assertRaises(provider_policy.PolicyRefusal):
            provider_policy.validate_adapter(earlier, self.SELECTED, adapter_digest=provider_policy.digest(earlier),
                                             tool_policy_digest=provider_policy.digest(provider_policy.POLICY))
        with self.assertRaises(provider_policy.PolicyRefusal):
            provider_policy.argv(earlier, self.SELECTED, "prompt")
        self.assertNotEqual(provider_policy.digest(earlier), provider_policy.digest(adapter))
        synthetic = copy.deepcopy(provider_policy.REALIZATIONS["claude"])
        with mock.patch.dict(provider_policy.REALIZATIONS, {"simulated-other": synthetic}), self.assertRaises(provider_policy.PolicyRefusal):
            provider_policy.adapter(dict(self.SELECTED, provider="simulated-other"), network="bridge")

    def test_only_one_instruction_selector_name_exists_in_the_tracked_tree(self):
        # Static: delivery adds no AGENTS/CLAUDE.md selector to the source tree.
        root = Path(__file__).resolve().parents[4]
        found = []
        for here, directories, files in os.walk(root):
            if here == str(root):
                directories[:] = [one for one in directories if one not in ("work", ".git")]
            found += [os.path.relpath(os.path.join(here, one), root) for one in files
                      if one in ("AGENTS.md", "AGENTS.override.md", "CLAUDE.md")]
        self.assertEqual(found, ["AGENTS.md"])
        # Inside the shared policy package the host file is named only by
        # the label text; nothing there reads it.
        from baton_v12 import provider_policy
        for source in Path(provider_policy.__file__).parent.glob("*.py"):
            self.assertNotIn("AGENTS.md", source.read_text().replace(provider_policy.LABEL_TEMPLATE, ""), str(source))


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
