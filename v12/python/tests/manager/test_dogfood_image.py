"""W39357 — the dogfood image, BUILT and probed, with no secret anywhere.

`work/records/2026/08/finding-v12-first-useful-dogfood-task/findings/
finding-real-claude-adapter-image/`.

THE ACCEPTANCE SENTENCE THIS ANSWERS: *a no-secret image gate proves the
CLI/entrypoint is present.* Review [P2] refused to let that be closed from
Dockerfile inspection alone, and it was right to: a recipe that names a package
and an image that contains it are two facts, and only the second one runs.

WHAT THIS DELIBERATELY DOES NOT DO. It makes no provider call, mounts no
credential and asks for no network at run time. The first live turn needs the
operator's exact credential grant and the approver's network posture and
belongs to W39364 — so every container here runs `--network none` with no
credential root, and the only questions asked are "is the runtime installed",
"is the worker's program the entrypoint" and "does the image carry a secret".

IT FAILS RATHER THAN SKIPS WITHOUT DOCKER, inheriting the rule every engine
gate in this campaign is under. THE BUILD ITSELF NEEDS NETWORK — npm and
Debian packages — which is why this is a serial gate and not part of the
offline suite; the acceptance names an image, and an image has to be built to
be one.
"""

import json
import os
import pathlib
import shutil
import subprocess
import unittest
import uuid

WORKER = (pathlib.Path(__file__).resolve().parents[3] / "worker")
MARK = "baton-w39357-dogfood"
ENGINE = "docker"

# W17110's pinned version, which the recipe names and this asks the artefact
# for. Two places agreeing because they were written from one decision.
CLAUDE_VERSION = "2.1.247"


def reachable(engine):
    if shutil.which(engine) is None:
        return False, f"{engine} is not on PATH"
    found = subprocess.run([engine, "version", "--format",
                            "{{.Server.Version}}"],
                           capture_output=True, timeout=120)
    if found.returncode != 0:
        return False, (f"{engine} is installed and its daemon is not "
                       f"reachable: "
                       f"{found.stderr.decode('utf-8', 'replace')[:200]}")
    return True, found.stdout.decode("utf-8").strip()


class TheDogfoodImageIsBuiltAndProbed(unittest.TestCase):
    """One build, then every question asked of the ARTEFACT."""

    @classmethod
    def setUpClass(cls):
        usable, why = reachable(ENGINE)
        if not usable:
            raise AssertionError(
                f"W39357's acceptance requires a built dogfood image and "
                f"{why}. That is a failed prerequisite for a required gate, "
                f"not a reason to pass without running it.")
        cls.image = f"{MARK}:{uuid.uuid4().hex[:12]}"
        cls.addClassCleanup(
            lambda: subprocess.run(
                [ENGINE, "image", "rm", "--force", cls.image],
                capture_output=True, timeout=300))
        built = subprocess.run(
            [ENGINE, "build", "-f", str(WORKER / "Dockerfile.claude"),
             "-t", cls.image, str(WORKER)],
            capture_output=True, timeout=2400)
        assert built.returncode == 0, (
            f"the dogfood image did not build: "
            f"{built.stderr.decode('utf-8', 'replace')[-2000:]}")

    def ran(self, *argv, entrypoint="/bin/sh"):
        """One throwaway container, `--network none` and no credential root.

        Nothing here needs egress, and a gate that asked for it would be
        asking for the grant the live turn is waiting on.
        """
        name = f"{MARK}-probe-{uuid.uuid4().hex[:10]}"
        done = subprocess.run(
            [ENGINE, "run", "--rm", "--name", name, "--network", "none",
             "--read-only", "--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=16m",
             "--entrypoint", entrypoint, self.image, *argv],
            capture_output=True, timeout=300)
        return (done.returncode,
                done.stdout.decode("utf-8", "replace"),
                done.stderr.decode("utf-8", "replace"))

    # -- the runtime is really installed -------------------------------------

    def test_the_provider_cli_is_installed_at_the_pinned_version(self):
        """THE FACT A RECIPE CANNOT ESTABLISH. `npm install -g` naming a
        version and an image containing that version are two things."""
        status, out, errors = self.ran("-c", "claude --version")
        self.assertEqual(status, 0, errors)
        self.assertIn(CLAUDE_VERSION, out)

    def test_the_system_trust_store_is_present(self):
        """W17110 paid two review rounds for its absence: a native runtime
        uses the system store, so every TLS handshake failed and surfaced as
        a connection error that read exactly like a network fault."""
        status, _out, errors = self.ran(
            "-c", "test -s /etc/ssl/certs/ca-certificates.crt")
        self.assertEqual(status, 0, errors)

    def test_python_and_the_worker_program_travelled(self):
        status, out, errors = self.ran(
            "-c", "python3 -c 'print(1)' && ls /opt/baton")
        self.assertEqual(status, 0, errors)
        for name in ("baton_worker.py", "claude_agent.py",
                     "dogfood_entry.py", "worker-control-1.0.schema.json"):
            self.assertIn(name, out)

    def test_the_scripted_default_is_present_only_as_the_seam_stopgap(self):
        """A STATED STOPGAP, held so it cannot quietly become the answer.

        THE SEAM IS FIXED AND THE STOPGAP IS STILL HERE, which is the state
        this case now describes. W39770 moved the scripted default behind
        `_scripted_default()`, so `main` no longer requires the module an
        injecting image does not ship — the code reason for the COPY is gone.
        What keeps it is that W39770 is signed off and NOT YET ACCEPTED by the
        approver, and W39357 does not get to pre-empt that acceptance by
        shipping an image that depends on it.

        W39357 review 2026-08-29T22:51:53Z: the previous form of this case
        asserted that `baton_worker.py` still CONTAINED the import string,
        meaning to fail once the seam was fixed. It did not fail, because the
        fix moved the import rather than deleting it — so the guard said the
        stopgap was still needed after it no longer was. It now asserts the
        real condition instead, and the removal it guards is the one owed to
        the approver's acceptance.
        """
        status, out, errors = self.ran("-c", "ls /opt/baton")
        self.assertEqual(status, 0, errors)
        self.assertIn("scripted_agent.py", out)
        worker = (WORKER / "baton_worker.py").read_text("utf-8")
        # THE IMPORT IS INSIDE THE DEFAULT, not ahead of the injection check.
        # This is what makes the COPY removable, and asserting it here is what
        # makes the removal a deliberate act with a test to update.
        import ast
        tree = ast.parse(worker)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) \
                    and node.module == "scripted_agent":
                where = node
                break
        else:
            self.fail("the scripted default is gone entirely; remove the "
                      "COPY and this case together")
        lazy = [one for one in ast.walk(tree)
                if isinstance(one, ast.FunctionDef)
                and one.name == "_scripted_default"
                and any(child is where for child in ast.walk(one))]
        self.assertTrue(lazy,
                        "the scripted import is no longer inside the lazy "
                        "default; the seam's shape changed and this guard "
                        "and the recipe's COPY both need revisiting")

    # -- and the entrypoint is the reviewed worker ---------------------------

    def test_the_entrypoint_starts_the_worker_with_the_adapter_injected(self):
        """THE WHOLE INJECTION, asked of the artefact.

        A container with no launch document has no session to answer under, so
        the ruling has it write NO frame and exit 2 — which is exactly what a
        started-and-correct worker does here, and what a broken import or a
        missing agent could not do.
        """
        name = f"{MARK}-entry-{uuid.uuid4().hex[:10]}"
        done = subprocess.run(
            [ENGINE, "run", "--rm", "--name", name, "--network", "none",
             "--read-only", "--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=16m",
             self.image],
            capture_output=True, timeout=300)
        self.assertEqual(done.returncode, 2, done.stderr.decode(
            "utf-8", "replace")[-2000:])
        # AND IT SAID NOTHING, which is the ruling: an uncorrelatable start
        # writes no frame and the manager settles it from the engine.
        self.assertEqual(done.stdout, b"")

    def test_the_injected_agent_is_the_real_adapter(self):
        status, out, errors = self.ran(
            "-c", "python3 -c \"import sys; sys.path.insert(0, '/opt/baton');"
                  " import dogfood_entry, claude_agent;"
                  " print(claude_agent.ClaudeAgent().__class__.__name__)\"")
        self.assertEqual(status, 0, errors)
        self.assertIn("ClaudeAgent", out)

    def test_the_worker_in_the_image_is_the_reviewed_file(self):
        """Byte-for-byte, so an image built from a forked worker fails here
        rather than at some later protocol surprise."""
        status, out, errors = self.ran(
            "-c", "sha256sum /opt/baton/baton_worker.py")
        self.assertEqual(status, 0, errors)
        import hashlib
        expected = hashlib.sha256(
            (WORKER / "baton_worker.py").read_bytes()).hexdigest()
        self.assertIn(expected, out)

    # -- and it carries no secret --------------------------------------------

    def test_the_image_carries_no_provider_credential(self):
        """THE NO-SECRET HALF, asked of the artefact rather than the recipe."""
        status, out, _errors = self.ran(
            "-c", "ls -a /home/nonroot/.claude 2>/dev/null; "
                  "ls /run/baton/credentials 2>/dev/null; true")
        self.assertEqual(status, 0)
        self.assertNotIn(".credentials.json", out)

    def test_the_image_sets_no_provider_environment_variable(self):
        """An `ANTHROPIC_API_KEY` baked here would silently outrank the
        mounted slot and decide which account every container ran as."""
        found = subprocess.run(
            [ENGINE, "image", "inspect", self.image, "--format",
             "{{json .Config.Env}}"], capture_output=True, timeout=120)
        self.assertEqual(found.returncode, 0, found.stderr)
        for value in json.loads(found.stdout.decode("utf-8")):
            self.assertFalse(value.startswith("ANTHROPIC"), value)
            self.assertFalse(value.startswith("BATON_WORKER_"), value)

    def test_the_runtime_identity_is_the_fixed_non_root_pair(self):
        status, out, errors = self.ran("-c", "id -u; id -g")
        self.assertEqual(status, 0, errors)
        self.assertEqual(out.split(), ["65532", "65532"])

    def test_nothing_from_the_manager_travelled(self):
        """The image's whole isolation rule, asked of the artefact: a worker
        that could import the manager is one bug away from its capabilities."""
        status, out, _errors = self.ran(
            "-c", "python3 -c \"import baton_v12\" 2>&1; true")
        self.assertEqual(status, 0)
        self.assertIn("ModuleNotFoundError", out)


if __name__ == "__main__":
    unittest.main()
