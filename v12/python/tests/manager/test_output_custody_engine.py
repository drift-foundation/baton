"""W26283 — output custody, over a REAL worker's real output.

`work/records/2026/08/finding-v12-oci-output-custody/`.

The acceptance for this provider opens with *"A real OCI worker output is
copied into manager custody only after exact manifest validation"*, and no
suite established that. `test_sealing.py` drives the seal against trees a
fixture wrote and an envelope a fixture composed — which is the right way to
cover forty refusal paths, and it is not the same claim. A fixture agrees with
the manager by construction; the question here is whether the REFERENCE WORKER
and this manager agree about a document neither of them wrote for the other.

WHAT IS REAL AND WHAT IS NOT. The container, the image, the worker program, the
bytes it writes, the envelope it publishes and the engine that is asked whether
anything is still running are all real. The manager side is the actual
`OciAdapter.seal`. What this suite supplies is what a manager would: the two
`/input` documents, the declarations and the freeze request.

IT FAILS RATHER THAN SKIPS WITHOUT A DAEMON, inheriting `ContainerCase` — for
the reason W6633's gate gives, and because this Work's acceptance names a real
engine outright.
"""

from __future__ import annotations

import json
import os
import stat
import tempfile
import uuid

from baton_v12.contracts import ContractRefusal, held_secret
from baton_v12.worker_manager import workspaces
from baton_v12.worker_manager.oci import OciAdapter

from .test_worker_container import (ASSIGNMENT_REF, DECLARATION, LAUNCH,
                                    EXECUTION_SESSION, ContainerCase, ask,
                                    input_pair)

NOW = "2026-08-27T00:00:00.000Z"
DIGEST = "sha256:" + "a" * 64
IDENTITY = {"image_digest": "sha256:" + "b" * 64,
            "profile_digest": "sha256:" + "c" * 64,
            "policy_digest": "sha256:" + "d" * 64,
            "adapter_digest": "sha256:" + "e" * 64}


class CustodyIsTakenOfWhatARealWorkerWrote(ContainerCase):

    def produced(self, declarations=None):
        """Run the reference worker for real and answer what it left behind.

        The worker is handed the two `/input` documents and a writable
        `/output`, and it writes its material and publishes its envelope
        exactly as it would under the manager. Nothing here writes into the
        output root — that is the whole point.
        """
        declarations = [dict(DECLARATION)] if declarations is None \
            else declarations
        given, assignment = input_pair(declarations)
        # THE HOME IS THE MANAGER'S, and custody is a SIBLING of the roots
        # rather than one of them: `_home` is the parent of `workspace`, and
        # the adapter puts custody under it precisely so the container cannot
        # reach its own evidence after the freeze.
        home = tempfile.mkdtemp(prefix="v12-w26283-engine-")
        self.addCleanup(self.release, home)
        inputs = os.path.join(home, "input")
        outputs = os.path.join(home, "output")
        for place in (inputs, outputs):
            os.makedirs(place)
        os.chmod(outputs, 0o777)
        # THE DECLARED ROOTS ARE PRE-CREATED AND HOST-OWNED, which is both
        # what a manager does and what makes this suite able to clean up
        # after itself. The container runs as a fixed non-root uid, so a
        # directory IT creates is one the host cannot later remove files
        # from -- `test_worker_container` lives with that by passing
        # `ignore_errors=True` and leaving the tree in /tmp. Creating the
        # directory here leaves the worker owning only the FILES it writes,
        # and a file inside a host-writable directory can be unlinked.
        for one in declarations:
            place = os.path.join(outputs, one["path"])
            os.makedirs(place, exist_ok=True)
            os.chmod(place, 0o777)
        for name, document in (("input.json", given),
                               ("assignment.json", assignment)):
            with open(os.path.join(inputs, name), "w",
                      encoding="utf-8") as handle:
                json.dump(document, handle)
        mounts = ((inputs, "/input", False), (outputs, "/output", True))
        status, answered = self.talk(LAUNCH, ask("work", EXECUTION_SESSION),
                                     mounts=mounts)
        self.assertEqual(status, 0, answered)
        # The worker really did the work, or the seal below proves nothing.
        self.assertTrue(os.path.isfile(os.path.join(outputs, "output.json")),
                        sorted(os.listdir(outputs)))
        return {"home": home, "inputs": inputs, "outputs": outputs,
                "given": given, "declarations": declarations}

    def release(self, home):
        """Sealing freezes custody read-only ON PURPOSE, so cleanup undoes it.

        NOT `ignore_errors`. A cleanup that cannot fail is a cleanup whose
        success is an assumption, and this suite creates the container-facing
        directories itself precisely so removal is possible rather than
        hopeful. A tree left behind fails here instead of accumulating in
        `/tmp`.

        The chmod is attempted and not required: files the container wrote are
        owned by another uid and cannot be chmodded by this process, but they
        CAN be unlinked, because that depends on the directory holding them --
        which this suite owns.
        """
        for base, directories, files in os.walk(home, topdown=False):
            for one in directories:
                try:
                    os.chmod(os.path.join(base, one), 0o700)
                except PermissionError:
                    pass
            for one in files:
                full = os.path.join(base, one)
                if os.path.islink(full):
                    continue
                try:
                    os.chmod(full, 0o600)
                except PermissionError:
                    pass
        os.chmod(home, 0o700)
        workspaces.discard_tree(home)
        self.assertFalse(os.path.exists(home), home)

    def adapter(self, rig, **overrides):
        """The real adapter, over the real roots the container just wrote."""
        built = OciAdapter(
            "docker", _Engine(), identity=dict(IDENTITY),
            assignment_roots={"inputs": rig["inputs"],
                              "workspace": rig["outputs"]},
            posture="execution", outputs=rig["declarations"],
            input_manifest_digest=rig["given"]["manifest_digest"],
            **overrides)
        return built

    def request(self, **overrides):
        body = {"attempt_id": "attempt-1",
                "assignment": json.loads(json.dumps(ASSIGNMENT_REF)),
                # W16823: the seal proves quiescence by SELECTING this
                # attempt's runtimes, and the selector is the whole label set
                # -- which now names the principal and the effective scope.
                "context": {"principal": "principal:org-a",
                            "effective_scope": "scope:deployment"},
                "disposition": "completed", "now": NOW,
                "operation": {"operation_id": "output.freeze:1",
                              "signature_digest": DIGEST}}
        body.update(overrides)
        return body

    # -- the acceptance's opening sentence ------------------------------------

    def test_a_real_workers_output_is_taken_into_custody(self):
        """End to end: a real container's bytes, in manager custody.

        The assertions are about CUSTODY rather than about the workspace,
        because the whole provider exists to stop the result describing a tree
        the worker still owns.
        """
        rig = self.produced()
        sealed = self.adapter(rig).seal(self.request())

        self.assertEqual(sealed["schema"], "baton.worker-manifest/result")
        self.assertEqual(sealed["disposition"], "completed")
        answered = sealed["outputs"][0]
        self.assertEqual(answered["name"], "proposal")
        self.assertEqual(answered["status"], "present")

        held = answered["artifact"]["locator"][len("file://"):]
        # CUSTODY IS NOT THE WORKSPACE. A locator naming the tree the container
        # wrote would be a result describing material somebody else can edit.
        self.assertNotEqual(os.path.realpath(held),
                            os.path.realpath(os.path.join(rig["outputs"],
                                                          "out")))
        self.assertFalse(held.startswith(rig["outputs"]))
        with open(os.path.join(held, "result.txt"), "rb") as reading:
            self.assertEqual(reading.read(),
                             b"scripted worker produced proposal\n")

        # THE MANIFEST DESCRIBES CUSTODY, measured again from disk rather than
        # taken from the document that claims it.
        manifest = answered["content_manifest"]
        self.assertEqual(manifest, workspaces.directory_manifest(held))
        self.assertEqual(answered["artifact"]["content_digest"],
                         manifest["tree_digest"])
        self.assertEqual(answered["artifact"]["bytes"],
                         manifest["total_bytes"])

    def test_the_completion_digest_describes_the_workers_own_envelope(self):
        """The receipt binds a digest of the bytes this manager opened.

        Recomputed here from the file the container published, so a manager
        that copied a claim instead of deriving one fails — which is the exact
        correction W6634's sixth review made and the reason the member exists.
        """
        rig = self.produced()
        sealed = self.adapter(rig).seal(self.request())
        with open(os.path.join(rig["outputs"], "output.json"), "rb") as reading:
            published = json.loads(reading.read().decode("utf-8"))
        body = {name: value for name, value in published.items()
                if name != "manifest_digest"}
        from baton_v12.contracts import digest as contract_digest
        self.assertEqual(sealed["completion_manifest_digest"],
                         contract_digest(body))

    def test_custody_is_read_only_and_the_container_cannot_reach_it(self):
        """Frozen, and OUTSIDE the roots a container may mount.

        `ROOT_NAMES` is the contract for what a container sees; custody is
        deliberately a sibling, because handing a worker its own frozen
        evidence back is the one place this material must not be.
        """
        rig = self.produced()
        sealed = self.adapter(rig).seal(self.request())
        held = sealed["outputs"][0]["artifact"]["locator"][len("file://"):]
        mode = stat.S_IMODE(os.stat(os.path.join(held, "result.txt")).st_mode)
        self.assertEqual(mode, workspaces.READ_ONLY_FILE)
        self.assertFalse(os.access(os.path.join(held, "result.txt"), os.W_OK))
        for root in (rig["inputs"], rig["outputs"]):
            self.assertFalse(os.path.realpath(held).startswith(
                os.path.realpath(root) + os.sep))

    def test_an_exact_replay_returns_the_first_answer(self):
        """Idempotent over a real freeze, including its instant.

        A second call must not re-derive: `created_at` would move, and a caller
        holding the first answer would be holding a different document for one
        operation.
        """
        rig = self.produced()
        built = self.adapter(rig)
        first = built.seal(self.request())
        again = built.seal(self.request())
        self.assertEqual(first, again)

    def test_a_replay_does_not_re_read_the_workers_output(self):
        """The receipt settles it, so transient worker storage may be gone.

        This is the ordering W6634 was corrected on three times: replay sits
        above every state read. Driven by REMOVING the worker's tree entirely
        between the two calls, which is what cleanup legitimately does.
        """
        rig = self.produced()
        built = self.adapter(rig)
        first = built.seal(self.request())
        os.chmod(rig["outputs"], 0o700)
        workspaces.discard_tree(os.path.join(rig["outputs"], "out"))
        os.unlink(os.path.join(rig["outputs"], "output.json"))
        self.assertEqual(built.seal(self.request()), first)

    def test_a_live_secret_a_real_worker_wrote_never_reaches_custody(self):
        """The acceptance's `live-secret bytes fail closed`, over real bytes.

        The container writes a deterministic body derived from its
        declaration, so the value the registry is armed with is the one the
        worker actually produced rather than one this case planted afterwards.
        """
        rig = self.produced()
        with open(os.path.join(rig["outputs"], "out", "result.txt"),
                  "rb") as reading:
            produced = reading.read().decode("utf-8").strip()
        built = self.adapter(rig)
        with held_secret(produced):
            with self.assertRaises(ContractRefusal) as caught:
                built.seal(self.request())
        self.assertEqual(caught.exception.code, "secret-leak")

    def test_a_link_a_worker_leaves_in_its_output_is_refused(self):
        """A real container's writable root, tampered with as a worker could.

        The container runs as a non-root uid and owns `/output`, so a symbolic
        link there is something a worker can genuinely create — this case
        plants it host-side because the scripted agent has no operation for
        it, and the path being exercised is the manager's.
        """
        rig = self.produced()
        os.symlink("/etc/hostname",
                   os.path.join(rig["outputs"], "out", "escape.txt"))
        with self.assertRaises(ContractRefusal) as caught:
            self.adapter(rig).seal(self.request())
        self.assertIn("symbolic link", str(caught.exception))

    def test_nothing_this_module_made_survives_it(self):
        """Asked of the engine, by this suite's own container mark."""
        import subprocess
        from .test_worker_container import ENGINE, MARK
        found = subprocess.run(
            [ENGINE, "ps", "--all", "--filter", f"name={MARK}",
             "--format", "{{.Names}}"], capture_output=True, timeout=120)
        self.assertEqual(found.returncode, 0,
                         found.stderr.decode("utf-8", "replace"))
        self.assertEqual(found.stdout.decode("utf-8").split(), [])


class _Engine:
    """The engine port `seal` reaches for, over a real `docker ps`.

    `seal` proves quiescence by ASKING the engine whether anything carrying
    this attempt's labels is still alive. The containers this suite runs are
    `--rm`, so the honest answer is an empty listing and the quiescence gate is
    genuinely satisfied rather than stubbed.
    """

    def __call__(self, argv):
        import subprocess
        finished = subprocess.run(argv, capture_output=True, timeout=180)
        return {"status": finished.returncode,
                "stdout": finished.stdout.decode("utf-8", "replace"),
                "stderr": finished.stderr.decode("utf-8", "replace")}
