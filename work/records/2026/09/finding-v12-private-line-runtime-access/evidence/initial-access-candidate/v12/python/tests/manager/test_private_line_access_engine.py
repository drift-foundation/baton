"""W106896 initial-access engine checkpoint; full custody proof stays W105706.

Opt-in requires operator-approved exact local image and dedicated workspace gid.
No builds, pulls, providers or implicit group fallback. This module initially
proves only materialization/launch/first-writer access; W105982 owns the later
custody composition before this module gains manager/reviewer/correction cases.
"""
import json
import os
from pathlib import Path
import subprocess
import unittest
import uuid

from baton_v12.checkpoint_profiles import GitCheckpointProfile
from baton_v12.worker_manager import create_line, launch, oci
from baton_v12.worker_manager.source_boundary import nominate_source
from . import test_review_cycles


class InitialPrivateLineEngine(unittest.TestCase):
    def setUp(self):
        if os.environ.get("BATON_V12_INITIAL_ACCESS_ENGINE") != "1":
            self.skipTest("initial-access runtime setup is not explicitly enabled")
        self.image = os.environ.get("BATON_V12_PRIVATE_LINE_IMAGE", "")
        self.assertRegex(self.image, r"^sha256:[0-9a-f]{64}$",
                         "an operator-approved installed image ID is required")
        self.assertTrue(os.environ.get("BATON_V12_WORKSPACE_GROUP"),
                        "an explicit dedicated workspace group is required")
        self.fixture = test_review_cycles.StableLineLifecycle()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.addCleanup(self.fixture.tearDown)
        self.container = None
        self.run_nonce = uuid.uuid4().hex
        self.addCleanup(self.cleanup_runtime)
        image = json.loads(self.command(["docker", "image", "inspect", self.image]))[0]
        self.assertEqual(image["Id"], self.image)
        self.assertFalse(image["Config"].get("Volumes"),
                         "the fixture image may not add writable volume aliases")

    def command(self, argv):
        result = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True,
                                text=True, timeout=300, umask=0o002)
        self.assertEqual(result.returncode, 0, result.stderr[:1000])
        return result.stdout.strip()

    def cleanup_runtime(self):
        if self.container is None:
            return
        found = json.loads(self.command(["docker", "inspect", self.container]))[0]
        self.assertEqual(found["Id"], self.container)
        self.assertEqual(found["Image"], self.image)
        self.assertEqual(found["Config"]["Labels"].get("baton.initial-access"), self.run_nonce)
        self.command(["docker", "rm", "--force", self.container])

    def test_initial_populated_line_is_writable_by_the_fixed_runtime(self):
        fixture = self.fixture
        source = fixture.source
        self.command(["git", "init", source])
        Path(source, "tracked").write_text("initial\n")
        Path(source, "execute").write_text("#!/bin/sh\nexit 0\n")
        os.chmod(Path(source, "execute"), 0o755)
        self.command(["git", "-C", source, "add", "tracked", "execute"])
        self.command(["git", "-C", source, "-c", "user.name=fixture",
                      "-c", "user.email=fixture@example.invalid", "commit", "-m", "base"])
        base = self.command(["git", "-C", source, "rev-parse", "HEAD"])

        def manager_runner(argv):
            # Per-child creation mask; never mutate the manager-global mask.
            result = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True,
                                    text=True, timeout=300, umask=0o002)
            return {"returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}

        profile = GitCheckpointProfile(manager_runner)
        line = create_line(fixture.store, source=nominate_source(source), declared_base=base,
                           profile=profile, authority_uuid=test_review_cycles.AUTHORITY,
                           work_id=test_review_cycles.WORK)
        fixture.profile = profile
        writer = fixture.writer(line["line_id"], 1)
        from baton_v12.worker_manager import workspaces, writer_boundary
        workspaces.assignment_workspace(fixture.group, fixture.storage, "writer-attempt-1")
        delivered = writer_boundary(fixture.store, writer_id=writer["writer_id"], generation=1)
        before = os.stat(line["path"])
        self.assertEqual(before.st_mode & 0o7777, 0o2775)
        self.assertEqual(Path(line["path"], "tracked").read_text(), "initial\n")
        labels = {**fixture.labels(), "profile_digest": "sha256:" + "b" * 64,
                  "policy_digest": "sha256:" + "d" * 64, "adapter_digest": "sha256:" + "c" * 64}
        identity = {name: labels[name] for name in ("profile_digest", "policy_digest", "adapter_digest")}
        identity["image_digest"] = self.image
        home = Path(fixture.temporary.name, "launch")
        home.mkdir()
        delivery = launch.materialize(str(home), attempt_id="writer-attempt-1",
                                      session="initial-access", contract="fixture", role="implementer")
        program = r"""
import errno,json,os,pathlib,subprocess
os.umask(0o002)
p=pathlib.Path('/output')
with (p/'tracked').open('a') as f: f.write('runtime\n')
(p/'nested').mkdir()
(p/'nested'/'new').write_text('runtime-created\n')
subprocess.run([str(p/'execute')],check=True)
git=['git','-c','safe.directory=/output','-C','/output']
subprocess.run(git+['add','tracked','nested/new'],check=True,stdout=subprocess.DEVNULL)
subprocess.run(git+['-c','user.name=fixture','-c','user.email=fixture@example.invalid',
                    'commit','-m','runtime'],check=True,stdout=subprocess.DEVNULL)
try:
    pathlib.Path('/input/source/tracked').write_text('forbidden')
except OSError as e:
    assert e.errno==errno.EROFS
else:
    raise AssertionError('source is writable')
print(json.dumps({'uid':os.getuid(),'gid':os.getgid(),'groups':os.getgroups()}))
"""

        def engine(argv):
            if "run" in argv:
                # Change only this fixture's payload; retain composed restrictions,
                # identity labels and source/line/launch mounts.
                self.assertEqual(argv[-1], self.image)
                argv = [*argv[:-1], "--pull=never", "--label", "baton.initial-access=" + self.run_nonce,
                        "--entrypoint=python3", self.image, "-c", program]
            result = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True,
                                    text=True, timeout=300)
            if "run" in argv and result.returncode == 0:
                candidate = result.stdout.strip()
                self.assertRegex(candidate, r"^[0-9a-f]{64}$")
                self.container = candidate
            return {"status": result.returncode, "stdout": result.stdout, "stderr": result.stderr}

        roots = delivered["roots"]
        adapter = oci.OciAdapter(
            "docker", engine, identity=identity, assignment_roots=roots, posture="execution",
            workspace_group=fixture.group, launch_delivery=delivery, source_delivery=delivered["boundary"],
            mounts=[{"source": roots["inputs"], "target": "/input", "writable": False},
                    {"source": roots["workspace"], "target": "/output", "writable": True}])
        adapter.start({"labels": labels, "operation_id": "initial-access-start", "input_root": roots["inputs"]})
        self.assertIsNotNone(self.container)
        self.assertEqual(self.command(["docker", "wait", self.container]), "0")
        stopped = json.loads(self.command(["docker", "inspect", self.container]))[0]
        self.assertFalse(stopped["State"]["Running"])
        self.assertEqual(stopped["State"]["Pid"], 0)
        facts = json.loads(self.command(["docker", "logs", self.container]))
        self.assertEqual((facts["uid"], facts["gid"]), (65532, 65532))
        self.assertIn(fixture.group.gid, facts["groups"])
        created = Path(line["path"], "nested/new").stat()
        self.assertNotEqual(created.st_uid, os.geteuid(), "same-owner writes are not the runtime proof")
        self.assertEqual(created.st_gid, fixture.group.gid)
        self.assertEqual(created.st_mode & 0o7777, 0o664)
        self.assertEqual(Path(line["path"], "nested").stat().st_mode & 0o7777, 0o2775)
        self.assertEqual(Path(line["path"], "tracked").read_text(), "initial\nruntime\n")
        self.assertEqual(Path(source, "tracked").read_text(), "initial\n")
        self.assertEqual((os.stat(line["path"]).st_dev, os.stat(line["path"]).st_ino),
                         (before.st_dev, before.st_ino))
        self.assertNotEqual(self.command(["git", "-C", line["path"], "rev-parse", "HEAD"]), base)
