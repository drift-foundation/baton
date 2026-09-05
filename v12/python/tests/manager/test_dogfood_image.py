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
import tempfile
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
             # W71917: THE CONTEXT IS `v12`, because the recipe now
             # copies the distribution's profile package beside the
             # worker modules and a context cannot reach above itself.
             "-t", cls.image, str(WORKER.parent)],
            capture_output=True, timeout=2400)
        # W71917: BOTH STREAMS, because the legacy builder writes its steps
        # AND its failures to STDOUT. Showing only stderr reported a build
        # failure as the daemon's `DEPRECATED: The legacy builder...` banner
        # and nothing else, which named neither the step that failed nor why --
        # a diagnostic that turns a real failure into an unreadable one.
        assert built.returncode == 0, (
            f"the dogfood image did not build (exit {built.returncode})\n"
            f"stdout: {built.stdout.decode('utf-8', 'replace')[-3000:]}\n"
            f"stderr: {built.stderr.decode('utf-8', 'replace')[-2000:]}")

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

    def test_the_scripted_default_did_not_travel(self):
        """THE STOPGAP IS GONE, and this is what keeps it gone.

        For two rounds this image carried `scripted_agent.py` because
        `main(agent=...)` opened with an unconditional import of it, so the
        documented injection seam could not be used without shipping the
        default it overrode. W39770 is the real correction and is CLOSED
        SATISFYING, with a rationale that assigns this removal to W39357.

        So the case inverts. It asserts the ARTEFACT does not carry a scripted
        provider — a real provider image has no business shipping one — and
        then asserts the seam property that makes the absence safe, so a
        regression in `baton_worker.py` fails HERE with actionable prose
        rather than as a `ModuleNotFoundError` in some later live turn.
        """
        status, out, errors = self.ran("-c", "ls /opt/baton")
        self.assertEqual(status, 0, errors)
        self.assertNotIn("scripted_agent.py", out)
        worker = (WORKER / "baton_worker.py").read_text("utf-8")
        # THE IMPORT IS INSIDE THE LAZY DEFAULT, not ahead of the injection
        # check. That is the whole reason this image can omit the module.
        import ast
        tree = ast.parse(worker)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) \
                    and node.module == "scripted_agent":
                where = node
                break
        else:
            # NOT A FAILURE. A worker with no scripted default at all needs no
            # module shipped either, which is what this image already assumes.
            return
        lazy = [one for one in ast.walk(tree)
                if isinstance(one, ast.FunctionDef)
                and one.name == "_scripted_default"
                and any(child is where for child in ast.walk(one))]
        self.assertTrue(lazy,
                        "the scripted import left the lazy default, so "
                        "`main` needs a module this image no longer ships; "
                        "W39770's seam correction has regressed")

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

    def test_the_adapter_in_the_image_is_the_reviewed_file(self):
        """W85497 correction bytes must be in the artefact being certified.

        The previous gate bound `baton_worker.py` but only asserted that
        `claude_agent.py` existed. After a containment correction changed the
        adapter, that shape let the old image digest pass all fifteen cases.
        Byte identity is the discriminator between a rebuilt candidate and a
        stale cached artefact.
        """
        status, out, errors = self.ran(
            "-c", "sha256sum /opt/baton/claude_agent.py")
        self.assertEqual(status, 0, errors)
        import hashlib
        expected = hashlib.sha256(
            (WORKER / "claude_agent.py").read_bytes()).hexdigest()
        self.assertIn(expected, out)

    # -- W85497: the interpreter floor, asked of the artefact ----------------

    def test_the_interpreter_meets_the_distributions_declared_floor(self):
        """THE DEFECT W85497 EXISTS FOR, asked of the image rather than the
        recipe.

        `v12/python/pyproject.toml` declares `requires-python >= 3.13`. The
        first ordinary self-hosted W71917 retry ran this image with Debian
        BOOKWORM's unversioned `python3`, which is 3.11: the provider
        succeeded and `python3 -m compileall` reported an unterminated string
        at `worker_manager/custody.py:752` in source no candidate had touched.
        The image was rejecting syntax the distribution's floor makes legal.

        A HOST PYTHON THAT PASSES PROVES NOTHING HERE. The whole finding is
        that the two interpreters disagreed, so the question is put to the
        artefact that will actually run the workload.
        """
        status, out, errors = self.ran(
            "-c", "python3 -c 'import sys; print(sys.version_info[:3]); "
                  "raise SystemExit(0 if sys.version_info >= (3, 13) else 9)'")
        self.assertEqual(status, 0,
                         f"this image's python3 is below the v12 floor of "
                         f"3.13: {out.strip()} {errors}")

    def test_there_is_exactly_one_python3_in_the_artefact(self):
        """The suite was moved rather than a second interpreter installed.

        Two Pythons would make "which one ran" a question every future probe
        has to answer, so the recipe's choice is asserted on the artefact.
        """
        status, out, errors = self.ran(
            "-c", "ls /usr/bin/python3* /usr/local/bin/python3* 2>/dev/null "
                  "| xargs -r -n1 readlink -f | sort -u")
        self.assertEqual(status, 0, errors)
        self.assertEqual(len(out.split()), 1, out)

    def test_the_committed_v12_baseline_compiles_and_stays_byte_identical(
            self):
        """BOTH HALVES OF THE ACCEPTANCE, in one container.

        The unchanged committed baseline must pass the mandatory command in
        THIS image, and that command must not create a single cache entry in
        the tree it compiled -- which is what turned run6's ten-path proposal
        into a 10,779,527-byte patch.

        THE MOUNT IS WRITABLE ON PURPOSE. A read-only bind would make the
        cache-free result a property of the MOUNT rather than of the composed
        environment, and the environment is what `claude_agent` and
        `dogfood_operator` actually rely on.

        AND THE TREE IS THE COMMITTED ONE, which review 2026-09-04T13-56-04Z
        [P1] found this was not. It copied `src`, `tests` and `tools` out of
        the WORKING TREE -- which at packaging time carried several other
        Works\' dirty paths and this candidate\'s own edits -- so
        `baseline_unchanged` proved only that compiling did not change that
        dirty staging. It said nothing about the committed baseline every
        document here names. `committed()` extracts the exact commit and binds
        which one, so the sentence and the measurement are about one tree.
        """
        import hashlib

        staged, commit = self.committed()
        self.assertRegex(commit, r"\A[0-9a-f]{40}\Z")

        def snapshot():
            """Every ENTRY, typed -- directories included.

            An empty `__pycache__` is exactly the entry this gate must catch,
            and a files-only snapshot reads it as no change at all.
            """
            found = {}
            for one in sorted(staged.rglob("*")):
                name = str(one.relative_to(staged))
                found[name] = ("dir" if one.is_dir() else
                               "file:" + hashlib.sha256(
                                   one.read_bytes()).hexdigest())
            return found

        before = snapshot()
        name = f"{MARK}-compile-{uuid.uuid4().hex[:10]}"
        done = subprocess.run(
            [ENGINE, "run", "--rm", "--name", name, "--network", "none",
             "--read-only",
             "--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=256m",
             "--mount", f"type=bind,source={staged},target=/candidate,readonly=false",
             "--workdir", "/candidate",
             "--env", "PYTHONPYCACHEPREFIX=/tmp/pycache",
             "--entrypoint", "python3", self.image,
             "-m", "compileall", "-q", "src", "tests", "tools"],
            capture_output=True, timeout=1800)
        self.assertEqual(done.returncode, 0,
                         done.stdout.decode("utf-8", "replace")[-4000:]
                         + done.stderr.decode("utf-8", "replace")[-2000:])
        self.assertEqual(snapshot(), before,
                         "the mandatory compile command changed the tree it "
                         "was measuring")
        self.assertEqual(
            [str(one.relative_to(staged)) for one in staged.rglob("*")
             if one.name == "__pycache__" or one.suffix == ".pyc"],
            [], "a cache entry landed in the candidate")

    def test_an_invalid_file_still_fails_with_a_usable_diagnostic(self):
        """The negative control for the floor case above.

        A gate that only proved "the baseline compiles" would also pass an
        image whose `compileall` could not fail, and the operator-facing half
        of this finding is that a failure must still SAY which file and where.
        """
        staged = pathlib.Path(self.staging()) / "broken"
        staged.mkdir(parents=True)
        (staged / "broken.py").write_text("def broken(:\n    pass\n",
                                          encoding="utf-8")
        subprocess.run(["chmod", "-R", "a+rwX", str(staged)], timeout=300)
        name = f"{MARK}-invalid-{uuid.uuid4().hex[:10]}"
        done = subprocess.run(
            [ENGINE, "run", "--rm", "--name", name, "--network", "none",
             "--read-only", "--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=64m",
             "--mount", f"type=bind,source={staged},target=/candidate,readonly=false",
             "--workdir", "/candidate",
             "--env", "PYTHONPYCACHEPREFIX=/tmp/pycache",
             "--entrypoint", "python3", self.image,
             "-m", "compileall", "-q", "."],
            capture_output=True, timeout=600)
        self.assertNotEqual(done.returncode, 0)
        said = (done.stdout + done.stderr).decode("utf-8", "replace")
        self.assertIn("broken.py", said)
        self.assertIn("SyntaxError", said)

    def staging(self):
        """One host directory this case owns, removed with the case."""
        made = tempfile.mkdtemp(prefix="w85497-image-")
        self.addCleanup(shutil.rmtree, made, True)
        return made

    def committed(self):
        """The exact committed `src`, `tests` and `tools`, and its commit.

        AN ARCHIVE AND NOT A COPY OF THE CHECKOUT. This gate\'s whole claim is
        about the COMMITTED baseline, and a working tree carrying anybody\'s
        uncommitted edits is a different tree -- which is what the review
        found. READ-ONLY with respect to version control: nothing here writes
        an index, a ref, an object or a working file.

        THE COMMIT IS RETURNED so the case can bind it. A probe that staged
        "whatever HEAD was" without saying which commit would be as
        unfalsifiable as the copy it replaces.
        """
        # THE REPOSITORY ROOT, counted from this file: manager, tests, python,
        # v12, repository. `parents[3]` is `v12/`, whose own path names the
        # archive cannot resolve.
        root = pathlib.Path(__file__).resolve().parents[4]
        found = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                               capture_output=True, timeout=120)
        # A FAILED PREREQUISITE FOR A REQUIRED GATE, said as one -- the same
        # rule this module applies to a missing engine, and for the same
        # reason. This case exists to compile the COMMITTED baseline, so a
        # tree with no history cannot answer it; the previous version ran
        # anywhere precisely because it measured the wrong thing. A reviewer
        # reproducing the candidate outside a repository should run this one
        # from a checkout rather than read a raw version-control error.
        assert found.returncode == 0, (
            f"this gate compiles the COMMITTED v12 baseline, so it needs the "
            f"repository at {root} to be a version-controlled tree with "
            f"history. It is not: "
            f"{found.stderr.decode('utf-8', 'replace').strip()[:200]}. That "
            f"is a failed prerequisite for a required gate, not a reason to "
            f"pass without running it, and not a reason to fall back to "
            f"copying a working tree -- which is exactly the defect this "
            f"helper replaced.")
        commit = found.stdout.decode().strip()
        staged = pathlib.Path(self.staging()) / "candidate"
        staged.mkdir(parents=True)
        archive = staged.parent / "committed.tar"
        made = subprocess.run(
            ["git", "-C", str(root), "archive", "--format=tar",
             "-o", str(archive), commit,
             "v12/python/src", "v12/python/tests", "v12/python/tools"],
            capture_output=True, timeout=600)
        assert made.returncode == 0, made.stderr
        # THE ARCHIVE IS CHECKED FOR CONTENT. A silently empty one would make
        # every assertion below pass over nothing, which this campaign has
        # already been bitten by once.
        assert archive.stat().st_size > 0, "the archive is empty"
        opened = subprocess.run(
            ["tar", "-x", "-f", str(archive), "-C", str(staged),
             "--strip-components", "2"], capture_output=True, timeout=600)
        assert opened.returncode == 0, opened.stderr
        for name in ("src", "tests", "tools"):
            assert (staged / name).is_dir(), f"{name} did not extract"
        # A COMMITTED TREE CARRIES NO CACHE, asserted rather than cleaned up
        # after: an extract that produced one would mean the repository itself
        # carries bytecode, which is its own defect and not this gate\'s to
        # quietly repair.
        assert not list(staged.rglob("__pycache__")), \
            "the committed tree carries a bytecode cache"
        assert not list(staged.rglob("*.pyc")), \
            "the committed tree carries bytecode"
        subprocess.run(["chmod", "-R", "a+rwX", str(staged)], timeout=300)
        return staged, commit

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
