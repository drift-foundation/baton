"""Checks of the qualification packet's commands, on DISPOSABLE fixtures.

W385331, review 2026-11-21T00-55-22Z C3. Nothing here builds, installs or
launches anything, and nothing touches the owner's checkout: every check runs
the real `native-handoffs-2-bind.py` and the real `native-handoffs-2-qualify.sh`
against a throw-away git repository that carries the accepted candidate bytes
(copied from the two accepted packets with the composer's precedence on the
overlap), and stands in `just`/`docker` with recording stubs on PATH.

Run from the repository root:
    python3 -m unittest evidence…/native-handoffs-2-qualification/checks/test_qualify.py
"""
import hashlib
import json
import os
import pathlib
import shutil
import stat
import subprocess
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve()
CHECKOUT = HERE.parents[8]          # …/evidence/native-handoffs-2-qualification/checks/test_qualify.py
PILOT = "work/records/2026/10/finding-v12-development-coordination-pilot"
CONFIG = CHECKOUT / PILOT / "config"
EVIDENCE = CHECKOUT / PILOT / "evidence"
BIND = CONFIG / "native-handoffs-2-bind.py"
HELPER = CONFIG / "native-handoffs-2-qualify.sh"
COMPOSER = EVIDENCE / "native-handoffs-composer"
SLICE = EVIDENCE / "native-handoffs-1-correction-2"
BASE_ARCHIVE = CHECKOUT / "work/scratch/w383217/composer/base"   # git archive 331dd737, read-only use
GIT_ENV = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": "/nonexistent",
           "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull,
           "GIT_AUTHOR_NAME": "Baton Check", "GIT_AUTHOR_EMAIL": "check@baton.invalid",
           "GIT_COMMITTER_NAME": "Baton Check", "GIT_COMMITTER_EMAIL": "check@baton.invalid",
           "GIT_OPTIONAL_LOCKS": "0"}


def sha256(place):
    return "sha256:" + hashlib.sha256(pathlib.Path(place).read_bytes()).hexdigest()


class Fixture(unittest.TestCase):
    """One disposable repository carrying the JOINED accepted bytes."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="qualify-check-")
        self.addCleanup(self.temporary.cleanup)
        self.root = pathlib.Path(self.temporary.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.composer = json.loads((COMPOSER / "manifest.json").read_text())
        self.slice = json.loads((SLICE / "manifest.json").read_text())
        # the product package at the base (so the compose step can import the
        # role contract out of the fixture checkout), then the joined bytes:
        # composer precedence on the overlap
        shutil.copytree(BASE_ARCHIVE / "v12/python/src/baton_v12", self.repo / "v12/python/src/baton_v12")
        for manifest, packet in ((self.slice, SLICE), (self.composer, COMPOSER)):
            for one in manifest["paths"]:
                target = self.repo / one["path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(packet / "candidate" / one["path"], target)
        # the packet's own inputs at their repository-relative places
        (self.repo / PILOT / "config").mkdir(parents=True)
        for name in ("native-handoffs-2-bind.py", "native-handoffs-2-qualify.sh",
                     "native-instance-handoffs-2.unbound.json",
                     "native-installed-task-handoffs-2.unbound.json"):
            shutil.copyfile(CONFIG / name, self.repo / PILOT / "config" / name)
        for packet in (COMPOSER, SLICE):
            place = self.repo / PILOT / "evidence" / packet.name
            place.mkdir(parents=True)
            shutil.copyfile(packet / "manifest.json", place / "manifest.json")
        # the checkout's own ignore rules for build output (v12/.gitignore), so a
        # stand-in bundle and stamp do not dirty the fixture tree
        (self.repo / "v12/.gitignore").write_text("/python/build/\n/python/packaging/build-stamp.json\n__pycache__/\n")
        self.git("init", "-q", "-b", "main")
        self.git("add", "--all")
        self.git("commit", "-q", "--message", "the accepted checkpoint, joined")
        self.sha = self.git("rev-parse", "HEAD").strip()
        self.cfg = self.repo / PILOT / "config"
        self.manifests = [str(self.repo / PILOT / "evidence" / "native-handoffs-composer" / "manifest.json"),
                          str(self.repo / PILOT / "evidence" / "native-handoffs-1-correction-2" / "manifest.json")]
        self.bound = self.cfg / "native-bound-2.json"

    def git(self, *arguments):
        out = subprocess.run(["git", "-C", str(self.repo), *arguments], capture_output=True, text=True, env=GIT_ENV)
        self.assertEqual(out.returncode, 0, out.stderr)
        return out.stdout

    def bind(self, *extra, sha=None, tree=None):
        argv = ["python3", "-I", str(BIND), "--repo", str(self.repo), "--sha", sha or self.sha,
                "--manifests", *self.manifests, *extra]
        if tree is not None:
            argv += ["--tree", str(tree)]
        return subprocess.run(argv, capture_output=True, text=True)

    def helper(self, step, *, env=None, stubs=None):
        """The real helper, one step, against the fixture repository."""
        held = dict(GIT_ENV, QUALIFY_REPO=str(self.repo), QUALIFY_DEST=str(self.root / "dest"),
                    QUALIFY_PACKAGING_ROOT=str(self.root / "packaging"), QUALIFY_TMP=str(self.root / "tmp"),
                    QUALIFY_PYTHON="python3", QUALIFY_CREDENTIALS=str(self.root / "credentials.json"),
                    QUALIFY_IMAGE_REF="baton-v12-worker:check")
        if stubs is not None:
            held["PATH"] = str(stubs) + ":" + held["PATH"]
        held.update(env or {})
        return subprocess.run(["bash", str(self.cfg / "native-handoffs-2-qualify.sh"), step],
                              capture_output=True, text=True, env=held)

    def stubs(self, **programs):
        """Recording stand-ins for the engine and the recipe runner on PATH.
        Each records its argv to `<name>.calls` and runs the given body."""
        place = self.root / "stubs"
        place.mkdir(exist_ok=True)
        for name, body in programs.items():
            script = place / name
            script.write_text("#!/usr/bin/env bash\nprintf '%s\\n' \"$*\" >> '" + str(place / (name + ".calls")) + "'\n" + body + "\n")
            script.chmod(script.stat().st_mode | stat.S_IEXEC)
        return place

    def calls(self, name):
        place = self.root / "stubs" / (name + ".calls")
        return place.read_text().splitlines() if place.exists() else []


class TheBindingHoldsOneCheckpointToTheAcceptedBytes(Fixture):

    def test_the_joined_candidate_binds_and_names_both_manifests(self):
        out = self.bind("--out", str(self.bound))
        self.assertEqual(out.returncode, 0, out.stderr)
        bound = json.loads(self.bound.read_text())
        self.assertEqual(bound["sha"], self.sha)
        self.assertEqual(bound["manifests"], {
            "native-handoffs-composer": "fa01b73d811ffabee510d333f18a97153ab197a21bf16ea32f92736be8ce1e77",
            "native-handoffs-1-correction-2": "4925897d2bdf6e343d6eac229544b7c2c308f31fbf59ce01ec8b70b9c2aafd24"})
        self.assertEqual(len(bound["paths"]), 43)
        self.assertEqual(len(bound["overlap"]), 5)
        # THE OVERLAP IS BOUND AT THE COMPOSER'S BYTES, the slice-only paths at the slice's.
        composer = {one["path"]: one["candidate"] for one in self.composer["paths"]}
        for path in bound["overlap"]:
            self.assertEqual(bound["paths"][path], {"digest": composer[path], "owner": "native-handoffs-composer"})
        slice_only = {one["path"]: one["candidate"] for one in self.slice["paths"] if one["path"] not in composer}
        self.assertEqual(len(slice_only), 31)
        for path, digest in slice_only.items():
            self.assertEqual(bound["paths"][path], {"digest": digest, "owner": "native-handoffs-1-correction-2"})
        # and the re-check of the written binding passes
        again = self.bind("--check", str(self.bound))
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertIn("verified: 43 paths", again.stdout)

    def test_the_checkpoint_before_the_correction_refuses_naming_every_composer_path(self):
        """Base-only / missing-correction: a tree at 331dd737 carries the
        slice but none of the composer bytes."""
        tree = self.root / "base-only"
        for path in {one["path"] for one in self.composer["paths"]} | {one["path"] for one in self.slice["paths"]}:
            source = BASE_ARCHIVE / path
            target = tree / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        out = self.bind("--out", str(self.bound), tree=tree)
        self.assertEqual(out.returncode, 2)
        self.assertIn("does not carry the accepted bytes of 12 path(s)", out.stderr)
        for one in self.composer["paths"]:
            self.assertIn(one["path"], out.stderr)
        self.assertFalse(self.bound.exists())

    def test_one_drifted_slice_path_refuses_and_writes_nothing(self):
        drifted = self.repo / "v12/python/src/baton_v12/authority/messages.py"
        drifted.write_bytes(drifted.read_bytes() + b"\n# drift\n")
        self.git("commit", "-q", "-a", "--message", "drift")
        out = self.bind("--out", str(self.bound), sha=self.git("rev-parse", "HEAD").strip())
        self.assertEqual(out.returncode, 2)
        self.assertIn("1 path(s)", out.stderr)
        self.assertIn("authority/messages.py", out.stderr)
        self.assertFalse(self.bound.exists())

    def test_a_manifest_that_is_not_the_pinned_one_is_refused_before_anything(self):
        place = pathlib.Path(self.manifests[0])
        document = json.loads(place.read_text())
        document["paths"][0]["candidate"] = "sha256:" + "0" * 64
        place.write_text(json.dumps(document, indent=1, sort_keys=True) + "\n")
        out = self.bind("--out", str(self.bound))
        self.assertEqual(out.returncode, 2)
        self.assertIn("is not the reviewed manifest", out.stderr)
        self.assertFalse(self.bound.exists())

    def test_a_stale_binding_is_refused_by_the_check(self):
        self.assertEqual(self.bind("--out", str(self.bound)).returncode, 0)
        (self.repo / "v12/STACK.md").write_text("changed\n")
        self.git("commit", "-q", "-a", "--message", "moved on")
        moved = self.git("rev-parse", "HEAD").strip()
        out = self.bind("--check", str(self.bound), sha=moved)
        self.assertEqual(out.returncode, 2)
        self.assertFalse((self.cfg / "nothing").exists())


class TheHelperStopsAtTheFirstFailure(Fixture):
    """Review C3.3: a failed guard, pipeline or command ends the step with its
    own status and nothing after it runs."""

    def test_bind_then_check_pass_and_write_the_bound_documents(self):
        out = self.helper("bind")
        self.assertEqual(out.returncode, 0, out.stderr + out.stdout)
        self.assertTrue(self.bound.exists())
        self.assertTrue((self.cfg / f"native-instance-2-{self.sha[:8]}.json").exists())
        self.assertTrue((self.cfg / f"native-installed-task-2-{self.sha[:8]}.json").exists())
        instance = json.loads((self.cfg / f"native-instance-2-{self.sha[:8]}.json").read_text())
        self.assertEqual(instance["line_declared_base"], self.sha)
        self.assertEqual(instance["native_handoff_routing"]["reviewer"], "baton.reviewer-native")
        out = self.helper("check")
        self.assertEqual(out.returncode, 0, out.stderr + out.stdout)
        self.assertIn("binding verified", out.stdout)

    def test_a_dirty_tree_refuses_before_binding(self):
        (self.repo / "v12/STACK.md").write_text("dirty\n")
        out = self.helper("bind")
        self.assertEqual(out.returncode, 2)
        self.assertIn("changed or untracked", out.stderr)
        self.assertFalse(self.bound.exists())

    def test_a_moved_head_refuses_every_consuming_step_before_any_action(self):
        self.assertEqual(self.helper("bind").returncode, 0)
        (self.repo / "v12/STACK.md").write_text("moved\n")
        self.git("commit", "-q", "-a", "--message", "moved on")
        stubs = self.stubs(just="exit 0", docker="exit 0")
        for step in ("check", "bundle", "image", "install", "compose", "repeat", "start"):
            out = self.helper(step, stubs=stubs)
            self.assertEqual(out.returncode, 2, step)
            self.assertIn("is not the bound checkpoint", out.stderr, step)
        self.assertEqual(self.calls("just"), [])
        self.assertEqual(self.calls("docker"), [])

    def test_a_failed_gate_pipeline_ends_the_bundle_step_with_its_status(self):
        self.assertEqual(self.helper("bind").returncode, 0)
        stubs = self.stubs(just="echo 'Ran 24 tests'; echo 'FAILED (failures=1)'; exit 7")
        out = self.helper("bundle", stubs=stubs)
        self.assertEqual(out.returncode, 7, out.stdout + out.stderr)
        self.assertEqual(len(self.calls("just")), 1)
        log = self.repo / PILOT / "evidence" / f"checkpoint-{self.sha[:8]}-packaging" / "build-and-gate.log"
        self.assertIn("FAILED (failures=1)", log.read_text())
        self.assertFalse((log.parent / "build-stamp.json").exists())   # nothing after the failed gate ran

    def test_a_dirty_or_foreign_stamp_fails_the_bundle_step_after_a_green_gate(self):
        self.assertEqual(self.helper("bind").returncode, 0)
        stamp = self.repo / "v12/python/packaging"
        stamp.mkdir(parents=True)
        stamp.joinpath("build-stamp.json").write_text(json.dumps({"commit": self.sha, "dirty": True}))
        stubs = self.stubs(just="echo 'Ran 24 tests'; echo OK; exit 0")
        out = self.helper("bundle", stubs=stubs)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("AssertionError", out.stderr)
        self.assertFalse((self.repo / PILOT / "evidence" / f"checkpoint-{self.sha[:8]}-packaging" / "version.txt").exists())

    def test_a_green_gate_with_a_clean_stamp_and_bundle_passes(self):
        self.assertEqual(self.helper("bind").returncode, 0)
        stamp = self.repo / "v12/python/packaging"; stamp.mkdir(parents=True)
        stamp.joinpath("build-stamp.json").write_text(json.dumps({"commit": self.sha, "dirty": False}))
        bundle = self.repo / "v12/python/build/out/distro"; bundle.mkdir(parents=True)
        exe = bundle / "baton-v12-stack"
        exe.write_text("#!/usr/bin/env bash\ncase \"$*\" in *--version*) echo 'baton 12.0.0 (check)';; *identity*) echo '{}';; *compose-worker*) echo '--template VERSION';; esac\n")
        exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
        stubs = self.stubs(just="echo 'Ran 24 tests'; echo OK; exit 0")
        out = self.helper("bundle", stubs=stubs)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        held = self.repo / PILOT / "evidence" / f"checkpoint-{self.sha[:8]}-packaging"
        for name in ("build-and-gate.log", "build-stamp.json", "version.txt", "bundle-identity.json", "distro-sha256.txt"):
            self.assertTrue((held / name).exists(), name)

    def test_a_failed_image_build_ends_the_image_step_before_inspection(self):
        self.assertEqual(self.helper("bind").returncode, 0)
        stubs = self.stubs(docker="case \"$1\" in build) echo 'build failed' >&2; exit 3;; *) exit 0;; esac")
        out = self.helper("image", stubs=stubs)
        self.assertEqual(out.returncode, 3, out.stdout + out.stderr)
        self.assertEqual([one.split()[0] for one in self.calls("docker")], ["build"])
        self.assertIn("build failed", (self.repo / PILOT / "evidence" / f"worker-image-{self.sha[:8]}" / "build.log").read_text())

    def test_a_pending_selection_refuses_the_create_step_before_the_command(self):
        self.assertEqual(self.helper("bind").returncode, 0)
        stubs = self.stubs(just="exit 0")
        for env in ({}, {"JOB": "PENDING-SELECTION", "STMT": str(self.root / "statement.txt")},
                    {"JOB": "w385331-handoffs-2", "STMT": str(self.root / "absent.txt")}):
            out = self.helper("create", env=env, stubs=stubs)
            self.assertEqual(out.returncode, 2, env)
            self.assertIn("pending selection", out.stderr)
        self.assertEqual(self.calls("just"), [])

    def test_a_composition_declaring_another_order_fails_the_compose_step(self):
        """Review C3.2: the expected declaration order is read from the bound
        checkout's role contract, and a worker document declaring anything
        else fails before the workers document is written."""
        self.assertEqual(self.helper("bind").returncode, 0)
        dest = self.root / "dest"; (dest / "distro").mkdir(parents=True)
        image_dir = self.repo / PILOT / "evidence" / f"worker-image-{self.sha[:8]}"; image_dir.mkdir()
        (image_dir / "image.id").write_text("sha256:" + "ab" * 32 + "\n")
        (dest / "deployment.json").write_text(json.dumps({"integration_target": {"t": 1}, "integration_workspace": {"w": 1}}))
        (dest / "authority-identity.json").write_text(json.dumps({"authority_uuid": "11111111-2222-3333-4444-555555555555"}))
        (self.root / "credentials.json").write_text("{}")
        order = json.dumps(["proposal", "handoff", "findings", "logs", "response"])   # the stale order the review caught
        exe = dest / "distro" / "baton-v12-stack"
        exe.write_text("#!/usr/bin/env bash\nwhile [ $# -gt 0 ]; do case \"$1\" in --into) INTO=$2;; esac; shift; done\n"
                       "python3 -c 'import json,sys; names=json.loads(sys.argv[2]); json.dump({\"deployment\": {\"schema\": \"baton.v12.single-worker-deployment/6\", \"image_digest\": \"sha256:\" + \"ab\"*32, \"input_manifest\": {\"outputs\": [{\"name\": n, \"required\": False} for n in names], \"work_ref\": {\"authority_uuid\": \"11111111-2222-3333-4444-555555555555\"}}}}, open(sys.argv[1], \"w\"))' \"$INTO\" '" + order + "'\n"
                       "echo 'template  baton.v12.job-template.implementation-review/3 declaring '" + json.dumps(", ".join(json.loads(order))) + "\n")
        exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
        env = {"PYTHONPATH": str(CHECKOUT / "v12/python/src")}
        out = self.helper("compose", env=env)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("AssertionError", out.stderr)
        self.assertIn("['proposal', 'findings', 'logs', 'handoff', 'response']", out.stderr)   # the contract's order, read from the product
        self.assertFalse((self.cfg / f"native-workers-2-{self.sha[:8]}.json").exists())
        # and the contract's own order composes through to the workers document
        exe.write_text(exe.read_text().replace(order, json.dumps(["proposal", "findings", "logs", "handoff", "response"]))
                       .replace(json.dumps(", ".join(json.loads(order))), json.dumps("proposal, findings, logs, handoff, response")))
        out = self.helper("compose", env=env)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        workers = json.loads((self.cfg / f"native-workers-2-{self.sha[:8]}.json").read_text())
        self.assertEqual([w["deployment"]["input_manifest"]["outputs"][3]["name"] for w in workers["workers"]], ["handoff", "handoff"])
        self.assertIn("native_handoff_routing", workers)


if __name__ == "__main__":
    unittest.main()
