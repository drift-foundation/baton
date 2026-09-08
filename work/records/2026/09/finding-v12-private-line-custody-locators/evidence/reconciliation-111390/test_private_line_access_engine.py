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
        # EVERY container this case starts, so a composed proof that launches
        # three of them removes three. `self.container` stays the most recent,
        # which is what the failure diagnostic reads.
        self.containers = []
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

    def why_it_ended(self, ended):
        """What the container actually said, gathered while it still exists.

        BOUNDED AND READ-ONLY. Three reads of this run's own container -- its
        exit state, the streams it produced, and the mount table it was given
        -- and nothing else: no engine mutation, no second run, no repair, and
        no permissions conclusion drawn here. Whether a denial explains the
        ending is a reader's judgement over this evidence, and manufacturing
        that judgement is exactly what an unproven diagnosis would be.

        IT NEVER RAISES. A diagnostic that can fail replaces the failure it was
        meant to explain, so every read is guarded and its own error becomes
        part of the account instead of the verdict.
        """
        lines = [f"the runtime ended {ended!r} rather than '0'"]
        for what, argv in (
                ("state", ["docker", "inspect", "--format",
                           "{{json .State}}", self.container]),
                ("logs", ["docker", "logs", self.container]),
                ("mounts", ["docker", "inspect", "--format",
                            "{{json .Mounts}}", self.container])):
            try:
                seen = subprocess.run(argv, stdin=subprocess.DEVNULL,
                                      capture_output=True, text=True,
                                      timeout=60)
                lines.append(f"{what}: rc={seen.returncode} "
                             f"out={seen.stdout.strip()[:2000]!r} "
                             f"err={seen.stderr.strip()[:2000]!r}")
            except Exception as failure:                # noqa: BLE001
                lines.append(f"{what}: unreadable ({type(failure).__name__})")
        return "\n".join(lines)

    def cleanup_runtime(self):
        for container in (self.containers
                          or ([self.container] if self.container else [])):
            found = json.loads(self.command(["docker", "inspect", container]))[0]
            self.assertEqual(found["Id"], container)
            self.assertEqual(found["Image"], self.image)
            self.assertEqual(found["Config"]["Labels"].get("baton.initial-access"), self.run_nonce)
            self.command(["docker", "rm", "--force", container])

    def launched(self, *, attempt_id, roots, boundary, program):
        """Start ONE more fixed-identity runtime over already-composed roots.

        The initial writer turn composes its own launch inline and is left
        exactly as it was proved; this is the same composition for the reviewer
        and the correction, whose roots and boundary their own accepted
        lifecycle operations produced. Nothing here chooses a mount: `/input`
        and `/output` are the roots it was handed, and the read-only source
        comes from the boundary.
        """
        from baton_v12.worker_manager.attempts import assignment_of

        fixture = self.fixture
        labels = {**assignment_of(fixture.store, attempt_id),
                  "profile_digest": "sha256:" + "b" * 64,
                  "policy_digest": "sha256:" + "d" * 64,
                  "adapter_digest": "sha256:" + "c" * 64}
        identity = {name: labels[name] for name in
                    ("profile_digest", "policy_digest", "adapter_digest")}
        identity["image_digest"] = self.image
        home = Path(fixture.temporary.name, "launch-" + attempt_id)
        home.mkdir()
        delivery = launch.materialize(str(home), attempt_id=attempt_id,
                                      session="initial-access",
                                      contract="fixture", role="implementer")

        def engine(argv):
            if "run" in argv:
                self.assertEqual(argv[-1], self.image)
                argv = [*argv[:-1], "--pull=never", "--label",
                        "baton.initial-access=" + self.run_nonce,
                        "--entrypoint=python3", self.image, "-c", program]
            result = subprocess.run(argv, stdin=subprocess.DEVNULL,
                                    capture_output=True, text=True, timeout=300)
            if "run" in argv and result.returncode == 0:
                candidate = result.stdout.strip()
                self.assertRegex(candidate, r"^[0-9a-f]{64}$")
                self.container = candidate
                self.containers.append(candidate)
            return {"status": result.returncode, "stdout": result.stdout,
                    "stderr": result.stderr}

        adapter = oci.OciAdapter(
            "docker", engine, identity=identity, assignment_roots=roots,
            posture="execution", workspace_group=fixture.group,
            launch_delivery=delivery, source_delivery=boundary,
            mounts=[{"source": roots["inputs"], "target": "/input",
                     "writable": False},
                    {"source": roots["workspace"], "target": "/output",
                     "writable": True}])
        adapter.start({"labels": labels,
                       "operation_id": "initial-access-" + attempt_id,
                       "input_root": roots["inputs"]})
        container = self.container
        self.assertIsNotNone(container)
        ended = self.command(["docker", "wait", container])
        self.assertEqual(ended, "0", self.why_it_ended(ended))
        stopped = json.loads(self.command(["docker", "inspect", container]))[0]
        self.assertFalse(stopped["State"]["Running"])
        self.assertEqual(stopped["State"]["Pid"], 0)
        facts = json.loads(self.command(["docker", "logs", container]))
        self.assertEqual((facts["uid"], facts["gid"]), (65532, 65532))
        return adapter, facts

    def composed_writer(self):
        """One real writer turn, up to and including its confirmed stop.

        Shared so the composed proof below continues the SAME live line
        rather than describing a second one. Every assertion the initial
        case made still runs here, in the same order.
        """
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
                self.containers.append(candidate)
            return {"status": result.returncode, "stdout": result.stdout, "stderr": result.stderr}

        roots = delivered["roots"]
        adapter = oci.OciAdapter(
            "docker", engine, identity=identity, assignment_roots=roots, posture="execution",
            workspace_group=fixture.group, launch_delivery=delivery, source_delivery=delivered["boundary"],
            mounts=[{"source": roots["inputs"], "target": "/input", "writable": False},
                    {"source": roots["workspace"], "target": "/output", "writable": True}])
        adapter.start({"labels": labels, "operation_id": "initial-access-start", "input_root": roots["inputs"]})
        self.assertIsNotNone(self.container)
        ended = self.command(["docker", "wait", self.container])
        # THE DIAGNOSTIC COMES BEFORE THE ASSERTION, and that ordering is the
        # whole of this addition. The first live run ended `1`, and the exit
        # code was asserted before anything read the container and before
        # cleanup removed it -- so the run produced a verdict and destroyed its
        # own explanation, and a read-only sweep afterwards found nothing left
        # to inspect. Nothing below changes what is required; it only makes a
        # failure say why, once, in the same turn that observes it.
        self.assertEqual(ended, "0", self.why_it_ended(ended))
        stopped = json.loads(self.command(["docker", "inspect", self.container]))[0]
        self.assertFalse(stopped["State"]["Running"])
        self.assertEqual(stopped["State"]["Pid"], 0)
        facts = json.loads(self.command(["docker", "logs", self.container]))
        self.assertEqual((facts["uid"], facts["gid"]), (65532, 65532))
        self.assertIn(fixture.group.gid, facts["groups"])
        return {"fixture": fixture, "source": source, "base": base,
                "line": line, "writer": writer, "adapter": adapter,
                "before": before, "facts": facts}

    def test_initial_populated_line_is_writable_by_the_fixed_runtime(self):
        held = self.composed_writer()
        fixture, line, source = held["fixture"], held["line"], held["source"]
        base, before = held["base"], held["before"]
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

    def head_of(self, place, revision="HEAD"):
        """One revision resolved in the private line, read-only."""
        return self.command(["git", "-C", place, "rev-parse", revision])

    def test_the_composed_ending_consumes_reviews_and_corrects_one_line(self):
        """W105706's remaining proof, over the tree a real runtime just wrote.

        The initial case proves the runtime could WRITE the line. This proves
        the manager can then finish with it: read back what a foreign uid left
        behind, freeze an immutable checkpoint over that exact commit, hand a
        reviewer a read-only view without touching the line, and admit a
        correction writer to the SAME line rather than to a second checkout.

        Each step is one a host fixture cannot establish. The worker wrote as
        uid 65532 under its own creation mask; whether this manager can then
        traverse and open the result is a question only a genuinely
        foreign-owned tree can answer, and it is exactly the question
        W105982's consumption gate exists to ask.
        """
        held = self.composed_writer()
        fixture, line, writer = held["fixture"], held["line"], held["writer"]
        adapter, before = held["adapter"], held["before"]
        runtime_head = self.head_of(line["path"])
        self.assertNotEqual(Path(line["path"], "nested/new").stat().st_uid,
                            os.geteuid())

        # CONFIRMED STOP FIRST. `composed_writer` already proved the container
        # is not running and its pid is 0; this records the disposition the
        # ending observes before it reads anything.
        fixture.complete("writer-attempt-1")

        # THE CONSUMPTION GATE, over foreign-owned bytes rather than a
        # fixture's own.
        subject = adapter.prove_line_consumable(
            fixture.store, assignment_id="writer-attempt-1", generation=1)
        self.assertEqual(subject["line_path"], line["path"])
        self.assertEqual(subject["line_id"], line["line_id"])
        self.assertEqual(subject["pinned"], (before.st_dev, before.st_ino))
        # THE RETAINED SIBLING IS OUTSIDE THE WRITER'S OWN MOUNT: bytes the
        # worker can still reach are not retained.
        self.assertFalse(subject["custody_path"].startswith(
            line["path"].rstrip("/") + "/"))
        self.assertEqual(
            subject["custody_path"],
            os.path.join(os.path.dirname(line["path"]), "custody",
                         "writer-attempt-1"))
        # AND IT REPAIRED NOTHING while proving it could read.
        self.assertEqual(
            Path(line["path"], "nested/new").stat().st_mode & 0o7777, 0o664)
        self.assertEqual(os.stat(line["path"]).st_mode & 0o7777, 0o2775)

        # THE CHECKPOINT IS FROZEN OVER THE RUNTIME'S OWN COMMIT.
        checkpoint = fixture.freeze(writer, 1)
        evidence = checkpoint["evidence"]
        self.assertEqual(evidence["head"], runtime_head)
        self.assertEqual(evidence["base"], held["base"])
        self.assertIn("nested/new", evidence["paths"])
        self.assertEqual(self.head_of(line["path"], evidence["reference"]),
                         runtime_head)

        # THE REVIEWER GETS ORDINARY ROOTS, NOT THE LINE. Its output is its own
        # attempt workspace; the checkpoint stays the evidence it examines.
        from baton_v12.worker_manager import review_boundary, workspaces
        review = fixture.review(checkpoint["checkpoint_id"], 1)
        workspaces.assignment_workspace(fixture.group, fixture.storage,
                                        "review-attempt-1")
        readonly = review_boundary(fixture.store,
                                   attachment_id=review["attachment_id"],
                                   profile=fixture.profile)
        self.assertFalse(readonly["roots"]._line)
        self.assertNotEqual(os.path.realpath(readonly["roots"]["workspace"]),
                            line["path"])
        self.assertEqual(os.stat(line["path"]).st_mode & 0o7777, 0o2775)

        # THE CORRECTION CONTINUES ONE PRIVATE HISTORY. No second checkout, no
        # reclone, and the runtime's own bytes are still there for it.
        fixture.verdict(review, 1, "changes-requested")
        fixture.writer(line["line_id"], 2, checkpoint["checkpoint_id"])
        workspaces.assignment_workspace(fixture.group, fixture.storage,
                                        "writer-attempt-2")
        again = os.stat(line["path"])
        self.assertEqual((again.st_dev, again.st_ino),
                         (before.st_dev, before.st_ino))
        self.assertEqual(again.st_mode & 0o7777, 0o2775)
        self.assertEqual(Path(line["path"], "tracked").read_text(),
                         "initial\nruntime\n")
        self.assertEqual(self.head_of(line["path"]), runtime_head)
        # AND REVISION ONE STAYS RESOLVABLE after the line is handed on.
        self.assertEqual(self.head_of(line["path"], evidence["reference"]),
                         runtime_head)

    # -- the two remaining runtime stages ------------------------------------

    REVIEWER_PROGRAM = r"""
import errno,json,os,pathlib
os.umask(0o002)
line=pathlib.Path('/input/source')
denied={}
for name in ('tracked','.git/HEAD'):
    try:
        with (line/name).open('a') as f: f.write('reviewer\n')
    except OSError as e:
        denied[name]=e.errno
    else:
        raise AssertionError('the reviewer wrote %s' % name)
try:
    (line/'reviewer-new').write_text('reviewer\n')
except OSError as e:
    denied['reviewer-new']=e.errno
else:
    raise AssertionError('the reviewer created a new path in the checkpoint')
out=pathlib.Path('/output')
(out/'findings').write_text('reviewed\n')
print(json.dumps({'uid':os.getuid(),'gid':os.getgid(),'groups':os.getgroups(),
                  'denied':denied,'read':(line/'tracked').read_text()}))
"""

    CORRECTION_PROGRAM = r"""
import json,os,pathlib,subprocess
os.umask(0o002)
p=pathlib.Path('/output')
with (p/'tracked').open('a') as f: f.write('correction\n')
git=['git','-c','safe.directory=/output','-C','/output']
subprocess.run(git+['add','tracked'],check=True,stdout=subprocess.DEVNULL)
subprocess.run(git+['-c','user.name=fixture','-c','user.email=fixture@example.invalid',
                    'commit','-m','correction'],check=True,stdout=subprocess.DEVNULL)
head=subprocess.run(git+['rev-parse','HEAD'],check=True,capture_output=True,text=True)
print(json.dumps({'uid':os.getuid(),'gid':os.getgid(),'groups':os.getgroups(),
                  'head':head.stdout.strip()}))
"""

    def test_a_reviewer_runtime_cannot_write_the_checkpoint_it_reads(self):
        """The read-only half, proved by a real runtime rather than a mode bit.

        A reviewer is handed the line as its SOURCE and its own attempt
        workspace as its output. What must be true is that the same fixed
        identity that could write this tree as the writer cannot write it as
        the reviewer — including the private metadata, which is where a
        reviewer could otherwise rewrite the very history it is judging.
        """
        held = self.composed_writer()
        fixture, line, writer = held["fixture"], held["line"], held["writer"]
        runtime_head = self.head_of(line["path"])
        fixture.complete("writer-attempt-1")
        checkpoint = fixture.freeze(writer, 1)

        from baton_v12.worker_manager import review_boundary, workspaces
        review = fixture.review(checkpoint["checkpoint_id"], 1)
        workspaces.assignment_workspace(fixture.group, fixture.storage,
                                        "review-attempt-1")
        readonly = review_boundary(fixture.store,
                                   attachment_id=review["attachment_id"],
                                   profile=fixture.profile)
        _adapter, facts = self.launched(
            attempt_id="review-attempt-1", roots=readonly["roots"],
            boundary=readonly["boundary"], program=self.REVIEWER_PROGRAM)

        # EVERY WRITE REFUSED, and by the filesystem rather than by politeness.
        self.assertIn(fixture.group.gid, facts["groups"])
        self.assertEqual(sorted(facts["denied"]),
                         [".git/HEAD", "reviewer-new", "tracked"])
        for name, errno_seen in facts["denied"].items():
            self.assertEqual(errno_seen, 30, name)     # EROFS
        # AND IT COULD READ what it was given, and write its OWN output.
        self.assertEqual(facts["read"], "initial\nruntime\n")
        self.assertEqual(
            Path(readonly["roots"]["workspace"], "findings").read_text(),
            "reviewed\n")

        # THE LINE IS UNTOUCHED: same object, same mode, same history.
        self.assertEqual(Path(line["path"], "tracked").read_text(),
                         "initial\nruntime\n")
        self.assertFalse(Path(line["path"], "reviewer-new").exists())
        self.assertEqual(os.stat(line["path"]).st_mode & 0o7777, 0o2775)
        self.assertEqual(self.head_of(line["path"]), runtime_head)

    def test_a_correction_runtime_advances_the_same_line(self):
        """The correction half: one private history, not a second checkout.

        The second writer is a fresh container with the same fixed identity,
        and what it must find is the FIRST runtime's bytes — because the line
        was never recloned. What must survive its commit is the frozen
        checkpoint the reviewer examined.
        """
        held = self.composed_writer()
        fixture, line, writer = held["fixture"], held["line"], held["writer"]
        before = held["before"]
        first_head = self.head_of(line["path"])
        fixture.complete("writer-attempt-1")
        checkpoint = fixture.freeze(writer, 1)
        reference = checkpoint["evidence"]["reference"]

        from baton_v12.worker_manager import (review_boundary, workspaces,
                                              writer_boundary)
        review = fixture.review(checkpoint["checkpoint_id"], 1)
        workspaces.assignment_workspace(fixture.group, fixture.storage,
                                        "review-attempt-1")
        review_boundary(fixture.store, attachment_id=review["attachment_id"],
                        profile=fixture.profile)
        fixture.verdict(review, 1, "changes-requested")
        second = fixture.writer(line["line_id"], 2,
                                checkpoint["checkpoint_id"])
        workspaces.assignment_workspace(fixture.group, fixture.storage,
                                        "writer-attempt-2")
        delivered = writer_boundary(fixture.store,
                                    writer_id=second["writer_id"],
                                    generation=2)
        # THE CORRECTION IS MOUNTED AT THE SAME OBJECT, not at a new clone.
        again = os.stat(delivered["roots"]["workspace"])
        self.assertEqual((again.st_dev, again.st_ino),
                         (before.st_dev, before.st_ino))

        adapter, facts = self.launched(
            attempt_id="writer-attempt-2", roots=delivered["roots"],
            boundary=delivered["boundary"], program=self.CORRECTION_PROGRAM)
        self.assertIn(fixture.group.gid, facts["groups"])

        # IT FOUND THE FIRST RUNTIME'S WORK and continued it.
        self.assertEqual(Path(line["path"], "tracked").read_text(),
                         "initial\nruntime\ncorrection\n")
        self.assertEqual(facts["head"], self.head_of(line["path"]))
        self.assertNotEqual(facts["head"], first_head)
        self.assertEqual(self.head_of(line["path"], "HEAD~1"), first_head)

        # AND THE MANAGER FINISHES THE ROUND, which is what makes this a
        # correction rather than a container that happened to write. A second
        # turn that stopped at file and revision checks would prove the runtime
        # and leave the lifecycle half of the round untested.
        fixture.complete("writer-attempt-2")
        again_subject = adapter.prove_line_consumable(
            fixture.store, assignment_id="writer-attempt-2", generation=2)
        self.assertEqual(again_subject["line_path"], line["path"])
        self.assertEqual(again_subject["line_id"], line["line_id"])
        self.assertEqual(again_subject["pinned"],
                         (before.st_dev, before.st_ino))
        self.assertEqual(
            again_subject["custody_path"],
            os.path.join(os.path.dirname(line["path"]), "custody",
                         "writer-attempt-2"))

        # THE SECOND CHECKPOINT IS FROZEN OVER THE SECOND RUNTIME'S COMMIT.
        corrected = fixture.freeze(second, 2)
        evidence = corrected["evidence"]
        self.assertEqual(evidence["head"], facts["head"])
        self.assertEqual(evidence["base"], held["base"])
        self.assertIn("tracked", evidence["paths"])
        self.assertNotEqual(evidence["reference"], reference)
        self.assertEqual(self.head_of(line["path"], evidence["reference"]),
                         facts["head"])

        # AND THE REVIEWED CHECKPOINT IS STILL AUDIT EVIDENCE, asked through
        # the API that owns that question rather than by resolving a ref.
        from baton_v12.worker_manager import audit_checkpoint
        audited = audit_checkpoint(fixture.store,
                                   checkpoint["checkpoint_id"],
                                   fixture.profile)
        self.assertEqual(audited["head"], first_head)
        self.assertEqual(audited["reference"], reference)
        self.assertEqual(self.head_of(line["path"], reference), first_head)
        self.assertEqual((os.stat(line["path"]).st_dev,
                          os.stat(line["path"]).st_ino),
                         (before.st_dev, before.st_ino))
        self.assertEqual(os.stat(line["path"]).st_mode & 0o7777, 0o2775)
