"""Separate setup correction regressions; no Docker, real source or privilege."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

sys.dont_write_bytecode = True
import live_controller_setup as candidate
import live_controller as original
import test_live_package as prior


class SetupTests(unittest.TestCase):
    def test_corrected_snapshot_imports_in_fresh_system_python(self):
        manifest = json.loads(original.MANIFEST.read_text())
        assets = candidate.REPO / "v12/python/src/baton_v12/contracts/schema"
        for name in ("worker-control-1.0.schema.json", "agent-session-1.0.schema.json"):
            path = assets / name
            manifest["files"][str(path.relative_to(candidate.REPO))] = hashlib.sha256(path.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            runtime = candidate.snapshot_runtime(Path(directory), manifest)
            program = """import json,sys
sys.path.insert(0,sys.argv[1])
import live_controller_setup as c
from pathlib import Path
setup=c.Setup(Path(sys.argv[3]))
setup.enter('credential-imports')
try:
 apis=c.runtime_apis(Path(sys.argv[2]),setup)
except BaseException as error:
 print(json.dumps(dict(outcome='refused',diagnostic=c.safe_exception(error,setup.value['stage']))))
else:
 print(json.dumps(dict(outcome='imports-passed',api_count=len(apis),source_reader_constructed=False)))
"""
            result = subprocess.run(["/usr/bin/python3", "-B", "-s", "-c", program, str(candidate.HERE), str(runtime), directory],
                cwd=directory, env={"PATH": "/usr/bin:/bin"}, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stderr, "")
            self.assertEqual(json.loads(result.stdout), dict(outcome="imports-passed", api_count=4, source_reader_constructed=False))

    def test_exception_projection_omits_text_paths_and_custom_type_names(self):
        class PrivateCanaryException(Exception): pass
        for error, kind in ((FileNotFoundError(2, "SECRET-CANARY", "/private/SECRET-CANARY"), "file-not-found"),
                            (ModuleNotFoundError("SECRET-CANARY"), "module-not-found"),
                            (PrivateCanaryException("SECRET-CANARY"), "other"),
                            (candidate.wire.Refusal("SECRET-CANARY"), "fixture-refusal")):
            result = candidate.safe_exception(error, "credential-imports")
            self.assertEqual(result["exception_kind"], kind)
            self.assertNotIn("CANARY", json.dumps(result))
            self.assertNotIn("private", json.dumps(result))
            self.assertEqual(set(result), {"stage", "exception_kind", "errno"})

    def test_partial_constructor_intent_is_durable_and_never_claims_settled(self):
        stages = (("credential-home-create", "credential_home"), ("source-registry-create", "source_registry"),
                  ("fixture-store-open", "fixture_store"))
        for stage, resource in stages:
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                setup = candidate.Setup(root)
                owner = candidate.Credentials()
                setup.enter(stage, resource)
                self.assertEqual(json.loads((root / "setup.json").read_text())["resources"][resource], "attempted")
                self.assertFalse(candidate.settle_setup(owner, setup))
                self.assertTrue(setup.value["partial_setup_unresolved"])

    def test_early_import_failure_is_proved_before_resource_attempt(self):
        with tempfile.TemporaryDirectory() as directory:
            setup = candidate.Setup(Path(directory))
            owner = candidate.Credentials()
            with mock.patch.object(candidate, "runtime_apis", side_effect=FileNotFoundError(2, "private")):
                with self.assertRaises(FileNotFoundError):
                    owner.prepare(Path(directory), Path(directory), setup)
            self.assertEqual(setup.value["stage"], "credential-imports")
            self.assertTrue(candidate.settle_setup(owner, setup))
            self.assertFalse(setup.value["partial_setup_unresolved"])

    def test_received_store_closes_after_partial_constructor_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            setup = candidate.Setup(Path(directory))
            owner = candidate.Credentials()
            owner.store = mock.Mock()
            setup.enter("fixture-store-open", "fixture_store")
            setup.created("fixture_store", Path(directory) / "fixture.sqlite3")
            setup.enter("fixture-group-configure")
            self.assertFalse(candidate.settle_setup(owner, setup))
            owner.store.close.assert_called_once_with()
            self.assertEqual(setup.value["store_close"], "confirmed")
            self.assertTrue(setup.value["partial_setup_unresolved"])

    def test_actual_prepare_retains_allocations_when_store_open_raises(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            setup = candidate.Setup(root)
            owner = candidate.Credentials()
            reader = mock.Mock()
            credential_api = SimpleNamespace(MAX_BEARER=4096, CredentialHome=mock.Mock())
            source_api = SimpleNamespace(SCHEMA="fixture-registry", UserCredentialSources=mock.Mock(return_value=reader))
            store_api = SimpleNamespace(open=mock.Mock(side_effect=OSError(5, "PRIVATE-CANARY")))
            def allocate(**kwargs):
                place = root / ("credential-home" if "credentials-" in kwargs["prefix"] else "source-registry")
                place.mkdir()
                return str(place)
            with mock.patch.object(candidate, "runtime_apis", return_value=(credential_api, mock.Mock(), store_api, source_api)), \
                    mock.patch.object(candidate.base, "mounts", return_value=[dict(target="/dev/shm", filesystem="tmpfs")]), \
                    mock.patch.object(candidate.tempfile, "mkdtemp", side_effect=allocate), \
                    mock.patch.object(candidate, "USER", os.getuid()):
                with self.assertRaises(OSError):
                    owner.prepare(root, root, setup)
            self.assertEqual(setup.value["stage"], "fixture-store-open")
            self.assertEqual(setup.value["resources"], dict(credential_home="created", source_registry="created", fixture_store="attempted"))
            self.assertIsNone(owner.store)
            self.assertFalse(candidate.settle_setup(owner, setup))
            self.assertTrue((root / "credential-home").is_dir())
            self.assertTrue((root / "source-registry/sources.json").is_file())
            reader.assert_not_called()
            credential_api.CredentialHome.return_value.materialize.assert_not_called()

    def test_store_close_failure_cannot_replace_original_diagnostic_or_claim_success(self):
        with tempfile.TemporaryDirectory() as directory:
            setup = candidate.Setup(Path(directory))
            owner = candidate.Credentials()
            owner.store = mock.Mock()
            owner.store.close.side_effect = OSError(5, "PRIVATE-CANARY")
            setup.enter("fixture-store-open", "fixture_store")
            setup.created("fixture_store", Path(directory) / "fixture.sqlite3")
            setup.complete()
            self.assertFalse(candidate.settle_setup(owner, setup))
            self.assertEqual(setup.value["ending_diagnostic"], dict(stage="fixture-store-close", exception_kind="os-error", errno=5))
            self.assertNotIn("CANARY", (Path(directory) / "setup.json").read_text())

    def test_full_run_reports_partial_setup_even_with_no_fixture(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            owners = []
            class FailedOwner(candidate.Credentials):
                def __init__(self):
                    super().__init__()
                    owners.append(self)
                def prepare(self, root, runtime, setup):
                    setup.enter("source-registry-create", "source_registry")
                    raise PermissionError(13, "PRIVATE-CANARY", "/PRIVATE-CANARY")
            image = dict(Id=candidate.IMAGE, Config={"Volumes": {}})
            network = dict(Name="bridge", Driver="bridge", Scope="local", Internal=False,
                           Id="b" * 64, Options={"com.docker.network.bridge.default_bridge": "true"})
            with mock.patch.object(candidate, "audit", return_value={"limitations": []}), \
                    mock.patch.object(candidate, "digest", return_value="manifest"), \
                    mock.patch.object(candidate, "docker", side_effect=[json.dumps([image]), json.dumps([network])]), \
                    mock.patch.object(candidate, "snapshot_runtime", return_value=root), \
                    mock.patch.object(candidate, "Credentials", FailedOwner), \
                    mock.patch.object(candidate, "execute_pair") as pair, \
                    mock.patch.object(candidate, "export_evidence", return_value=root / "export"), \
                    mock.patch.object(candidate.tempfile, "mkdtemp", return_value=str(root)), \
                    mock.patch.object(candidate.os, "geteuid", return_value=0), \
                    mock.patch.object(candidate.os, "setgroups"), mock.patch.object(candidate.os, "umask"), \
                    mock.patch.object(candidate.signal, "signal"), mock.patch.object(candidate.signal, "setitimer"), \
                    mock.patch.object(candidate.base, "libc_calls"), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(candidate.run(), 1)
            pair.assert_not_called()
            result = json.loads((root / "result.json").read_text())
            self.assertEqual(result["cleanup"], [])
            self.assertFalse(result["cleanup_confirmed"])
            self.assertEqual(result["diagnostic"], dict(stage="source-registry-create", exception_kind="permission-denied", errno=13))
            self.assertNotIn("CANARY", json.dumps(result))
            self.assertEqual(len(owners), 1)

    def test_export_includes_safe_setup_but_never_private_setup_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "root"
            root.mkdir()
            export = Path(directory) / "export"
            export.mkdir()
            setup = candidate.Setup(root)
            setup.enter("credential-home-create", "credential_home")
            setup.created("credential_home", Path("/PRIVATE-CANARY"))
            with mock.patch.object(candidate.tempfile, "mkdtemp", return_value=str(export)), mock.patch.object(candidate, "USER", os.getuid()):
                candidate.export_evidence(root)
            self.assertEqual({p.name for p in export.iterdir()}, {"setup.json", "PROVENANCE.json"})
            self.assertNotIn("CANARY", "".join(p.read_text() for p in export.iterdir()))


if __name__ == "__main__":
    # Reuse every existing assertion unchanged against the separate candidate.
    prior.controller = candidate
    suite = unittest.TestSuite((unittest.defaultTestLoader.loadTestsFromModule(prior),
                               unittest.defaultTestLoader.loadTestsFromTestCase(SetupTests)))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(not result.wasSuccessful())
