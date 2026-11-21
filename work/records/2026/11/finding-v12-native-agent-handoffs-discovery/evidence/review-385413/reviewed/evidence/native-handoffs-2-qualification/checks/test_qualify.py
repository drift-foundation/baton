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
TREE = CONFIG / "native-handoffs-2-tree.py"
SUMS = CONFIG / "native-handoffs-2-reviewed.sha256"
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
        # and the base's own tools (tools/source_identity, tools/build_stamp): the
        # helper runs the bound checkout's identity tool and the stamp check runs
        # the real stamp capture over this fixture
        shutil.copytree(BASE_ARCHIVE / "v12/python/tools", self.repo / "v12/python/tools")
        for manifest, packet in ((self.slice, SLICE), (self.composer, COMPOSER)):
            for one in manifest["paths"]:
                target = self.repo / one["path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(packet / "candidate" / one["path"], target)
        # the packet's own inputs at their repository-relative places
        (self.repo / PILOT / "config").mkdir(parents=True)
        for name in ("native-handoffs-2-bind.py", "native-handoffs-2-qualify.sh", "native-handoffs-2-tree.py",
                     "native-handoffs-2-reviewed.sha256",
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
                    QUALIFY_IMAGE_REF="baton-v12-worker:check",
                    # the fixture carries no declared consumed input of the test runner, so its
                    # source identity is the v12/ scope alone (the real run passes --declared)
                    QUALIFY_DECLARED="")
        if stubs is not None:
            held["PATH"] = str(stubs) + ":" + held["PATH"]
        held.update(env or {})
        return subprocess.run(["bash", str(self.cfg / "native-handoffs-2-qualify.sh"), step],
                              capture_output=True, text=True, env=held)

    REAL_STAMP = ("cd %(repo)s && mkdir -p v12/python/packaging && PYTHONPATH=v12/python python3 -c "
                  "\"import json; from tools import build_stamp; "
                  "build_stamp.write('v12/python/packaging/build-stamp.json', build_stamp.capture(source='%(repo)s')); "
                  "print(json.dumps(build_stamp.read('v12/python/packaging/build-stamp.json')))\" "
                  "&& echo 'Ran 24 tests' && echo OK")

    def real_stamp_just(self):
        """A `just` stand-in whose test-packaging writes the REAL build stamp of
        the fixture repository (tools/build_stamp.capture, whole-repository
        observation)."""
        return self.REAL_STAMP % {"repo": self.repo}

    def stand_in_bundle(self):
        bundle = self.repo / "v12/python/build/out/distro"; bundle.mkdir(parents=True, exist_ok=True)
        exe = bundle / "baton-v12-stack"
        exe.write_text("#!/usr/bin/env bash\ncase \"$*\" in *--version*) echo 'baton 12.0.0 (check)';; *identity*) echo '{}';; *compose-worker*) echo '--template VERSION';; esac\n")
        exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
        return exe

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

    # -- round 6 (review 2026-11-21T02-34-34Z G1-G3) ------------------------------

    def unrelated_records(self):
        """Dirty paths that are NOT inputs: review evidence, an older checkpoint's
        qualification records, a dossier note. None of them may gate a step."""
        review = self.repo / "work/records/2026/11/finding-v12-native-agent-handoffs-discovery/evidence/review-999999"
        review.mkdir(parents=True); (review / "probes.log").write_text("reviewer evidence\n")
        (self.cfg / "native-instance-2-deadbeef.json").write_text("{}\n")
        (self.cfg / "impl-a-2-deadbeef-compose.log").write_text("older\n")
        (self.repo / "work/notes.txt").write_text("a note\n")
        # (`--porcelain` collapses the wholly untracked `work/records/2026/11/` tree to its name)
        return ["work/records/2026/11/", "native-instance-2-deadbeef.json", "impl-a-2-deadbeef-compose.log", "work/notes.txt"]

    def test_a_stamp_naming_another_commit_fails_the_bundle_step_after_a_green_gate(self):
        self.assertEqual(self.helper("bind").returncode, 0)
        stubs = self.stubs(just="mkdir -p %s/v12/python/packaging; echo '{\"schema\": \"baton.v12.build-stamp/1\", \"commit\": \"%s\", \"dirty\": true, \"changed_entries\": 4, \"excused_build_output\": 0, \"detail\": null, \"source\": \"x\"}' > %s/v12/python/packaging/build-stamp.json; echo 'Ran 24 tests'; echo OK; exit 0"
                           % (self.repo, "f" * 40, self.repo))
        out = self.helper("bundle", stubs=stubs)
        self.assertEqual(out.returncode, 2, out.stdout + out.stderr)
        self.assertIn("recorded stamp names commit " + "f" * 40, out.stderr)
        self.assertFalse((self.repo / PILOT / "evidence" / f"checkpoint-{self.sha[:8]}-packaging" / "version.txt").exists())

    def test_a_stamp_with_no_observation_is_refused(self):
        self.assertEqual(self.helper("bind").returncode, 0)
        stubs = self.stubs(just="mkdir -p %s/v12/python/packaging; echo '{\"schema\": \"baton.v12.build-stamp/1\", \"commit\": \"%s\", \"dirty\": null, \"detail\": \"the repository tool could not report the tree state\", \"source\": \"x\"}' > %s/v12/python/packaging/build-stamp.json; echo 'Ran 24 tests'; echo OK; exit 0"
                           % (self.repo, self.sha, self.repo))
        out = self.helper("bundle", stubs=stubs)
        self.assertEqual(out.returncode, 2, out.stdout + out.stderr)
        self.assertIn("carries no observation of the tree", out.stderr)

    def test_the_real_stamp_is_kept_as_captured_and_the_finite_sequence_needs_no_checkpoint(self):
        """G1+G2: with unrelated records, this qualification's own records and
        the gate's own evidence all dirty, check -> bundle pass on the SAME
        commit; the real stamp is dirty, truthful, and recorded unchanged."""
        self.assertEqual(self.helper("bind").returncode, 0)
        unrelated = self.unrelated_records()
        out = self.helper("check")
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        for name in unrelated:
            self.assertIn(name, out.stdout)
        self.assertIn("[unrelated", out.stdout)
        self.assertTrue((self.cfg / f"native-inputs-2-{self.sha[:8]}.json").exists())   # the inputs record, first check
        self.stand_in_bundle()
        out = self.helper("bundle", stubs=self.stubs(just=self.real_stamp_just()))
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        held = self.repo / PILOT / "evidence" / f"checkpoint-{self.sha[:8]}-packaging"
        stamp = json.loads((held / "build-stamp.json").read_text())
        self.assertEqual(stamp["commit"], self.sha); self.assertTrue(stamp["dirty"]); self.assertEqual(stamp["excused_build_output"], 0)
        # the stamp counted the whole repository at capture time: 3 bind records + inputs record
        # + 4 unrelated entries + the evidence directory = 9, and is recorded exactly so
        self.assertEqual(stamp["changed_entries"], 9)
        after = json.loads((held / "tree-state.after.json").read_text())
        self.assertEqual(after["recorded_stamp"], stamp)
        self.assertEqual(after["inputs_stability"].split(" since")[0], "stable")
        self.assertEqual(after["inputs"]["content_digest"], json.loads((held / "tree-state.before.json").read_text())["inputs"]["content_digest"])
        self.assertIn("kept as captured", out.stdout)
        self.assertEqual(self.helper("check").returncode, 0)   # and a later check still passes with the evidence present
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), self.sha)   # no commit anywhere in the sequence

    def test_capture_excused_build_outputs_are_labelled_as_the_stamp_excuses_them(self):
        """The reviewer's counterexample, at the tool's own boundary: given the
        capture's observation lines, the three build outputs the real
        `build_stamp.capture` excuses are labelled so, never `product`, and the
        bind record is `generated`. (In the checkout those outputs are
        gitignored, `v12/.gitignore`, so neither the stamp nor `git status --
        v12` ever lists them; a checkout that un-ignored them would make the
        v12/ guard refuse first, which is the product-scope rule, not drift
        invented here.)"""
        import importlib.util
        spec = importlib.util.spec_from_file_location("treeguard", TREE); tree = importlib.util.module_from_spec(spec); spec.loader.exec_module(tree)
        lines = ["?? " + PILOT + "/config/native-bound-2.json", "?? v12/python/build/out/", "?? v12/python/build/work/",
                 "?? v12/python/packaging/build-stamp.json", "?? v12/python/tools/stray.py",
                 "?? work/records/2026/11/finding-v12-native-agent-handoffs-discovery/evidence/review-385406/"]
        held = {one["path"]: one["class"] for one in tree.classify(lines, "deadbeef", [])}
        self.assertEqual(held["v12/python/build/out/"], "build-output (excused by the stamp)")
        self.assertEqual(held["v12/python/build/work/"], "build-output (excused by the stamp)")
        self.assertEqual(held["v12/python/packaging/build-stamp.json"], "build-output (excused by the stamp)")
        self.assertEqual(held["v12/python/tools/stray.py"], "product")
        self.assertEqual(held[PILOT + "/config/native-bound-2.json"], "generated (this qualification, this checkpoint)")
        self.assertEqual(held["work/records/2026/11/finding-v12-native-agent-handoffs-discovery/evidence/review-385406/"], "unrelated (not an input)")
        # and the real capture over the same observation agrees on what it excuses
        import sys
        sys.path.insert(0, str(CHECKOUT / "v12/python"))
        try:
            from tools import build_stamp
        finally:
            sys.path.pop(0)
        stamp = build_stamp.capture(source=self.repo, runner=lambda argv, cwd: (self.sha + "\n") if "rev-parse" in argv else "\n".join(lines) + "\n")
        self.assertEqual((stamp["dirty"], stamp["changed_entries"], stamp["excused_build_output"]), (True, 3, 3))
        self.assertTrue((self.repo / "v12/.gitignore").read_text().startswith("/python/build/\n"))

    def test_a_dirty_product_input_refuses_every_consuming_step(self):
        self.assertEqual(self.helper("bind").returncode, 0)
        (self.repo / "v12/python/tools/stray.py").write_text("# an untracked product file\n")
        out = self.helper("check")
        self.assertEqual(out.returncode, 2)
        self.assertIn("changed or untracked", out.stderr)   # the v12/ guard fires first

    def test_a_changed_helper_byte_refuses_before_anything_else_runs(self):
        self.assertEqual(self.helper("bind").returncode, 0)
        tree = self.cfg / "native-handoffs-2-tree.py"
        tree.write_text(tree.read_text() + "\n# not the reviewed bytes\n")
        out = self.helper("check", stubs=self.stubs(just="exit 0"))
        self.assertEqual(out.returncode, 2)
        self.assertIn("not the reviewed ones", out.stderr)
        self.assertEqual(self.calls("just"), [])

    def test_a_declared_input_dirty_in_git_or_changed_in_content_refuses_as_input_drift(self):
        """Declared inputs are hashed by content (collapsed untracked directories
        expanded), so an untracked file inside one is drift, and an edited one
        changes the recorded content digest across the gate."""
        declared = self.repo / "work/records/declared/context"; declared.mkdir(parents=True)
        (declared / "agent.py").write_text("tracked input\n")
        self.git("add", "--all"); self.git("commit", "-q", "--message", "a declared input"); self.sha = self.git("rev-parse", "HEAD").strip()
        self.assertEqual(self.helper("bind").returncode, 0)
        env = {"QUALIFY_DECLARED": "--input work/records/declared/context"}
        self.assertEqual(self.helper("check", env=env).returncode, 0)
        (declared / "fresh.py").write_text("hidden inside a collapsed untracked directory? no: expanded\n")
        out = self.helper("check", env=env)
        self.assertEqual(out.returncode, 2)
        self.assertIn("declared consumed input(s) changed or untracked in git", out.stderr)
        self.assertIn("work/records/declared/context/fresh.py", out.stderr)
        (declared / "fresh.py").unlink()
        (declared / "agent.py").write_text("edited input\n")
        self.git("commit", "-q", "-a", "--message", "edit the input")   # committed, so git is clean but the content moved
        moved = self.git("rev-parse", "HEAD").strip()
        out = self.helper("check", env=env)
        self.assertEqual(out.returncode, 2)
        self.assertIn("is not the bound checkpoint", out.stderr)   # HEAD moved first; and with the bound sha forced:
        bound = json.loads(self.bound.read_text()); bound["sha"] = moved; self.bound.write_text(json.dumps(bound))
        inputs = self.cfg / f"native-inputs-2-{self.sha[:8]}.json"; inputs.rename(self.cfg / f"native-inputs-2-{moved[:8]}.json")
        out = self.helper("check", env=env)
        self.assertEqual(out.returncode, 2)
        self.assertTrue("drifted since" in out.stderr or "does not describe" in out.stderr, out.stderr)

    def test_install_verifies_the_qualified_bundle_before_bootstrap_has_any_effect(self):
        """G3: missing evidence, other bytes under the same stamp, and another
        stamp all refuse BEFORE bootstrap; the installed identity must be the
        verified artifact's."""
        self.assertEqual(self.helper("bind").returncode, 0)
        dest = self.root / "dest"; dest.mkdir(exist_ok=True)
        (dest / "authority-identity.json").write_text(json.dumps({"authority_uuid": "0000000a000000000000000000000000"}))
        bootstrap_stub = ("case \"$*\" in *bootstrap*) python3 -c \"import json,subprocess,sys; said=json.loads(subprocess.run(['%s/v12/python/build/out/distro/baton-v12-stack','identity'],capture_output=True,text=True).stdout); "
                          "json.dump({'authority_uuid': '0000000a000000000000000000000000', 'identity': said}, open('%s/instance.json', 'w'))\";; esac; exit 0" % (self.repo, dest))
        # (1) no bundle evidence yet
        out = self.helper("install", stubs=self.stubs(just=bootstrap_stub))
        self.assertEqual(out.returncode, 2); self.assertIn("no qualification evidence", out.stderr)
        self.assertFalse((dest / "instance.json").exists()); self.assertEqual([c for c in self.calls("just") if "bootstrap" in c], [])
        # the bundle step, with a stand-in bundle whose identity carries the real stamp
        exe = self.stand_in_bundle()
        exe.write_text("#!/usr/bin/env bash\ncase \"$*\" in *--version*) echo 'baton 12.0.0 (check)';; *identity*) python3 -c \"import json,hashlib; s=json.load(open('%s/v12/python/packaging/build-stamp.json')); print(json.dumps({'command': 'baton-v12-stack', 'frozen': True, 'build_stamp': s, 'sha256': hashlib.sha256(open('%s', 'rb').read()).hexdigest()}, sort_keys=True))\";; *compose-worker*) echo '--template VERSION';; esac\n" % (self.repo, exe))
        self.assertEqual(self.helper("bundle", stubs=self.stubs(just=self.real_stamp_just())).returncode, 0)
        held = self.repo / PILOT / "evidence" / f"checkpoint-{self.sha[:8]}-packaging"
        recorded = json.loads((held / "bundle-identity.json").read_text())
        self.assertEqual(recorded["sha256"], (held / "distro-sha256.txt").read_text().split()[0])
        # (2) other bytes under the SAME stamp: the bundle file changed after the gate
        original = exe.read_text()
        exe.write_text(original + "\n# rebuilt or replaced: same stamp, other bytes\n")
        out = self.helper("install", stubs=self.stubs(just=bootstrap_stub))
        self.assertEqual(out.returncode, 2, out.stdout + out.stderr); self.assertIn("same stamp is not the same artifact", out.stderr)
        self.assertFalse((dest / "instance.json").exists()); self.assertEqual([c for c in self.calls("just") if "bootstrap" in c], [])
        exe.write_text(original)
        # (3) another stamp: the bundle says a different stamp than recorded (bytes equal by construction of this stand-in cannot differ, so the recorded identity is edited)
        kept = (held / "bundle-identity.json").read_text()
        other = recorded.copy(); other["build_stamp"] = dict(recorded["build_stamp"], dirty=False, changed_entries=0)
        (held / "bundle-identity.json").write_text(json.dumps(other, sort_keys=True))
        out = self.helper("install", stubs=self.stubs(just=bootstrap_stub))
        self.assertEqual(out.returncode, 1, out.stdout + out.stderr); self.assertIn("does not carry the recorded stamp", out.stderr)
        self.assertFalse((dest / "instance.json").exists()); self.assertEqual([c for c in self.calls("just") if "bootstrap" in c], [])
        (held / "bundle-identity.json").write_text(kept)
        # (4) the verified bundle installs, and the installed identity is checked
        out = self.helper("install", stubs=self.stubs(just=bootstrap_stub))
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn("qualified bundle verified before install:", out.stdout)
        self.assertIn("instance 0000000a000000000000000000000000 bundle " + recorded["sha256"], out.stdout)
        self.assertEqual(len([c for c in self.calls("just") if "bootstrap" in c]), 1)
        # (5) an installed identity that is not the verified artifact's fails after the fact
        instance = json.loads((dest / "instance.json").read_text()); instance["identity"]["sha256"] = "0" * 64
        (dest / "instance.json").write_text(json.dumps(instance))
        out = self.helper("install", stubs=self.stubs(just="case \"$*\" in *bootstrap*) :;; esac; exit 0"))
        self.assertNotEqual(out.returncode, 0); self.assertIn("installed bundle sha256", out.stderr)

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

    def test_the_helper_opens_no_coordination_store(self):
        """Review 2026-11-21T01-49-15Z: dossier code never opens the Authority,
        Job or control store; the create readback is the command's own output."""
        text = HELPER.read_text()
        for token in ("open_readonly", "Authority.open", "sqlite3.connect", "from baton_v12.authority", "import baton_v12"):
            self.assertNotIn(token, text, token)
        bind = BIND.read_text()
        for token in ("sqlite3", "import baton_v12", "from baton_v12", "Authority"):
            self.assertNotIn(token, bind, token)

    def create_stand_ins(self, report_lines):
        """A stand-in bundle whose `manager create` answers on stdout and
        reports on stderr exactly as the real command does, plus `just`."""
        dest = self.root / "dest"; (dest / "distro").mkdir(parents=True, exist_ok=True)
        (dest / "authority-identity.json").write_text(json.dumps({"authority_uuid": "0000000a000000000000000000000000"}))
        answer = {"work_id": "0000000a-W1", "job_id": "w385331-handoffs-2",
                  "template": {"version": "baton.v12.job-template.implementation-review/3"},
                  "control": {"profile": "native-handoff/1"}}
        exe = dest / "distro" / "baton-v12-stack"
        exe.write_text("#!/usr/bin/env bash\n" + "".join("echo %s >&2\n" % json.dumps(line) for line in report_lines)
                       + "echo " + json.dumps(json.dumps(answer)) + "\n")
        exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
        statement = self.root / "statement.txt"; statement.write_text("Do one small useful thing.\n")
        return self.stubs(just="exit 0"), {"JOB": "w385331-handoffs-2", "STMT": str(statement)}

    REPORT = ("route impl           -> baton.claude-native",
              "route rview          -> baton.reviewer-native",
              "routing               reviewer baton.reviewer-native, decisions to baton.slaw",
              "work  0000000a-W1    already exists; left alone",
              "grant 0000000a-W1    approve/review/verify/integrate in its own scope",
              "answer               answer-handoff to baton.reviewer-native in its own scope; no review grant")

    def test_a_create_whose_report_names_routing_and_the_grant_passes(self):
        self.assertEqual(self.helper("bind").returncode, 0)
        stubs, env = self.create_stand_ins(self.REPORT)
        out = self.helper("create", env=env, stubs=stubs)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        held = self.repo / PILOT / "evidence" / "native-handoffs-2-qualification"
        self.assertEqual(json.loads((held / "create-w385331-handoffs-2.json").read_text())["work_id"], "0000000a-W1")
        self.assertEqual((held / "create-w385331-handoffs-2.report.log").read_text().splitlines(), list(self.REPORT))
        self.assertIn("reported by the command: routing", out.stdout)
        self.assertEqual(len(self.calls("just")), 1)   # the status before the command

    def test_a_create_whose_report_lacks_the_answering_grant_fails_after_the_command(self):
        self.assertEqual(self.helper("bind").returncode, 0)
        stubs, env = self.create_stand_ins(self.REPORT[:-1])
        out = self.helper("create", env=env, stubs=stubs)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("the create report lacks the line 'answer               answer-handoff to baton.reviewer-native", out.stderr)
        self.assertNotIn("reported by the command", out.stdout)

    def test_a_create_answering_another_template_fails_before_the_report_is_read(self):
        self.assertEqual(self.helper("bind").returncode, 0)
        stubs, env = self.create_stand_ins(self.REPORT)
        exe = self.root / "dest" / "distro" / "baton-v12-stack"
        exe.write_text(exe.read_text().replace("implementation-review/3", "implementation-review/1"))
        out = self.helper("create", env=env, stubs=stubs)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("implementation-review/1", out.stderr)
        self.assertNotIn("reported by the command", out.stdout)


if __name__ == "__main__":
    unittest.main()
