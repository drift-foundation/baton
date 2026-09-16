"""Focused checks for the v12 stack's prepared Python environment. W183883.

DETERMINISTIC AND OFFLINE. The one command that reaches an index is injected,
so nothing here downloads anything; what is proved is the LIFECYCLE -- what is
created, what is refused, what is never deleted, and what the four stack recipes
resolve -- not pip, which has its own.
"""
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

_DISTRIBUTION = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_DISTRIBUTION))
from tools import environment


class Fixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="v12-venv-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "env"
        self.environ = {"HOME": self.temp.name}
        self.ran = []

    def runner(self, returncode=0, stderr="", stdout=""):
        def running(argv, **named):
            self.ran.append(list(argv))
            return subprocess.CompletedProcess(argv, returncode, stdout=stdout,
                                               stderr=stderr)
        return running

    def prepared(self, *, python=None, lock=None, path=None):
        """A directory shaped like one this setup created."""
        (self.root / "bin").mkdir(parents=True, exist_ok=True)
        place = self.root / "bin" / "python"
        if not place.exists():
            place.symlink_to(python or sys.executable)
        environment.marker_path(self.root).write_text(json.dumps({
            "schema": environment.SCHEMA,
            "path": str(self.root.resolve()) if path is None else path,
            "python": "3.13.0", "installed": True,
            "lock_sha256": environment.lock_digest() if lock is None else lock}))
        return self.root

    def output(self, call):
        import io
        stream = io.StringIO()
        return call(stream), stream.getvalue()


class WhereItLives(Fixture):
    def test_the_environment_is_outside_the_checkout_by_default(self):
        chosen = environment.venv_path({"HOME": "/home/someone"})
        self.assertEqual(chosen, Path("/home/someone/.local/state/baton-v12-venv"))
        self.assertEqual(environment.venv_path({environment.VENV_ENV: "/srv/v12env"}),
                         Path("/srv/v12env"))

    def test_the_declared_minimum_is_read_rather_than_assumed(self):
        """The distribution says `requires-python`; nothing here restates it."""
        self.assertEqual(environment.required_python(), (3, 13))
        declared = (_DISTRIBUTION / "pyproject.toml").read_text()
        self.assertIn('requires-python = ">=3.13"', declared)

    def test_a_pyproject_with_no_minimum_is_refused_rather_than_guessed(self):
        empty = Path(self.temp.name) / "pyproject.toml"
        empty.write_text("[project]\nname = 'x'\n")
        with mock.patch.object(environment, "PROJECT", empty):
            with self.assertRaises(environment.SetupRefusal) as raised:
                environment.required_python()
        self.assertIn("will not guess", str(raised.exception))

    def test_the_lock_is_digested_from_its_own_bytes(self):
        import hashlib
        self.assertEqual(
            environment.lock_digest(),
            hashlib.sha256((_DISTRIBUTION / "requirements.lock").read_bytes()).hexdigest())


class WhatItSeesThere(Fixture):
    def test_an_absent_environment_is_absent(self):
        self.assertEqual(environment.observe(self.root, self.environ)["state"],
                         "absent")

    def test_a_directory_this_setup_did_not_create_is_foreign(self):
        self.root.mkdir(parents=True)
        (self.root / "something-elses").write_text("not ours")
        answer = environment.observe(self.root, self.environ)
        self.assertEqual(answer["state"], "foreign")
        self.assertIn("will NOT be deleted", answer["detail"])

    def test_a_marker_naming_another_path_is_foreign(self):
        """A copied or moved environment: its interpreter's shebangs and its
        `pyvenv.cfg` still name where it was built."""
        self.prepared(path="/somewhere/else")
        answer = environment.observe(self.root, self.environ)
        self.assertEqual(answer["state"], "foreign")
        self.assertIn("/somewhere/else", answer["detail"])

    def test_an_unreadable_marker_is_foreign_rather_than_absent(self):
        self.prepared()
        environment.marker_path(self.root).write_text("{ not json")
        self.assertEqual(environment.observe(self.root, self.environ)["state"],
                         "foreign")

    def test_an_interpreter_that_does_not_run_is_broken(self):
        self.prepared()
        environment.interpreter_path(self.root).unlink()
        environment.interpreter_path(self.root).write_text("not an interpreter")
        os.chmod(environment.interpreter_path(self.root), 0o700)
        self.assertEqual(environment.observe(self.root, self.environ)["state"],
                         "broken")

    def test_an_interpreter_below_the_declared_minimum_is_incompatible(self):
        self.prepared()
        with mock.patch.object(environment, "_version_of", lambda _p: (3, 9, 1)):
            answer = environment.observe(self.root, self.environ)
        self.assertEqual(answer["state"], "incompatible")
        self.assertIn("3.9.1", answer["detail"])
        self.assertIn("3.13", answer["detail"])

    def test_an_environment_installed_from_another_lock_is_stale(self):
        self.prepared(lock="0" * 64)
        self.assertEqual(environment.observe(self.root, self.environ)["state"],
                         "stale")

    def test_a_matching_environment_is_ready(self):
        self.prepared()
        answer = environment.observe(self.root, self.environ)
        self.assertEqual(answer["state"], "ready")
        self.assertEqual(answer["interpreter"],
                         str(self.root / "bin" / "python"))


class NamingTheInterpreter(Fixture):
    def test_a_ready_environment_answers_its_interpreters_path(self):
        self.prepared()
        code, text = self.output(
            lambda s: environment.interpreter(self.root, self.environ, stream=s))
        self.assertEqual(code, 0)
        self.assertEqual(text.strip(), str(self.root / "bin" / "python"))

    def test_an_unprepared_environment_refuses_and_names_the_command(self):
        with self.assertRaises(environment.SetupRefusal) as raised:
            environment.interpreter(self.root, self.environ)
        self.assertIn("just setup", str(raised.exception))
        self.assertIn("installs anything as a side effect", str(raised.exception))

    def test_the_refusal_never_reaches_the_stream_a_recipe_reads(self):
        """A recipe runs what STDOUT answers, so a refusal printed there would
        be executed as a path."""
        import io

        stream, errors = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "stderr", errors):
            code = environment.main(["--root", str(self.root), "interpreter"],
                                    stream=stream, environ=self.environ)
        self.assertEqual(code, 2)
        self.assertEqual(stream.getvalue(), "")
        self.assertIn("just setup", errors.getvalue())


class PreparingIt(Fixture):
    def test_a_first_setup_creates_installs_and_records(self):
        def running(argv, **named):
            self.ran.append(list(argv))
            if argv[1:3] == ["-m", "venv"]:
                (Path(argv[3]) / "bin").mkdir(parents=True, exist_ok=True)
                (Path(argv[3]) / "bin" / "python").symlink_to(sys.executable)
            return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

        code, text = self.output(lambda s: environment.setup(
            self.root, self.environ, stream=s, runner=running, now=1.0))
        self.assertEqual(code, 0)
        self.assertIn("prepared: " + str(self.root), text)
        self.assertEqual(environment.observe(self.root, self.environ)["state"],
                         "ready")
        marker = json.loads(environment.marker_path(self.root).read_bytes())
        self.assertEqual(marker["lock_sha256"], environment.lock_digest())
        self.assertEqual(marker["path"], str(self.root.resolve()))

    def test_the_dependencies_are_installed_with_their_hashes_enforced(self):
        self.prepared(lock="0" * 64)                      # stale: reinstall
        environment.setup(self.root, self.environ, runner=self.runner(),
                          stream=open(os.devnull, "w"), now=1.0)
        installed = [argv for argv in self.ran if "install" in argv]
        self.assertEqual(len(installed), 1, self.ran)
        for operand in ("--require-hashes", "--ignore-installed",
                        "--no-cache-dir", str(_DISTRIBUTION / "requirements.lock")):
            self.assertIn(operand, installed[0], operand)
        # THE PREPARED ENVIRONMENT'S OWN pip, never the ambient one.
        self.assertEqual(installed[0][0], str(self.root / "bin" / "pip"))

    def test_a_stale_environment_is_reinstalled_and_not_recreated(self):
        self.prepared(lock="0" * 64)
        environment.setup(self.root, self.environ, runner=self.runner(),
                          stream=open(os.devnull, "w"), now=1.0)
        self.assertEqual([argv for argv in self.ran if "venv" in argv], [])
        self.assertEqual(environment.observe(self.root, self.environ)["state"],
                         "ready")

    def test_a_repeated_setup_installs_nothing_at_all(self):
        self.prepared()
        code, text = self.output(lambda s: environment.setup(
            self.root, self.environ, stream=s, runner=self.runner()))
        self.assertEqual(code, 0)
        self.assertIn("already prepared", text)
        self.assertEqual(self.ran, [])

    def test_a_foreign_directory_is_refused_and_never_deleted(self):
        self.root.mkdir(parents=True)
        kept = self.root / "somebody-elses-work"
        kept.write_text("important")
        with self.assertRaises(environment.SetupRefusal) as raised:
            environment.setup(self.root, self.environ, runner=self.runner())
        self.assertIn("will not delete a directory it did not create",
                      str(raised.exception))
        self.assertTrue(kept.exists())
        self.assertEqual(self.ran, [])

    def test_an_incompatible_environment_is_refused_and_never_deleted(self):
        self.prepared()
        with mock.patch.object(environment, "_version_of", lambda _p: (3, 9, 1)):
            with self.assertRaises(environment.SetupRefusal) as raised:
                environment.setup(self.root, self.environ, runner=self.runner())
        self.assertIn("3.9.1", str(raised.exception))
        self.assertTrue(environment.interpreter_path(self.root).exists())
        self.assertEqual(self.ran, [])

    def test_an_interpreter_below_the_minimum_builds_nothing(self):
        with mock.patch.object(environment, "_version_of", lambda _p: (3, 12, 9)):
            with self.assertRaises(environment.SetupRefusal) as raised:
                environment.setup(self.root, self.environ, runner=self.runner(),
                                  chosen="/usr/bin/python3.12")
        self.assertIn("3.12.9", str(raised.exception))
        self.assertIn("just setup /path/to/python3", str(raised.exception))
        self.assertFalse(self.root.exists())

    def test_an_interpreter_that_is_not_there_is_named(self):
        with self.assertRaises(environment.SetupRefusal) as raised:
            environment.setup(self.root, self.environ, runner=self.runner(),
                              chosen="/no/such/python3")
        self.assertIn("/no/such/python3", str(raised.exception))

    def test_a_refused_install_supplies_the_exact_command_and_deletes_nothing(self):
        """The owner's rule for anything this authority cannot do itself: the
        exact command comes back, rather than an escalation."""
        self.prepared(lock="0" * 64)
        with self.assertRaises(environment.SetupRefusal) as raised:
            environment.setup(self.root, self.environ,
                              runner=self.runner(returncode=1, stderr="no index"))
        said = str(raised.exception)
        self.assertIn("--require-hashes", said)
        self.assertIn(str(_DISTRIBUTION / "requirements.lock"), said)
        self.assertIn(str(self.root / "bin" / "pip"), said)
        self.assertIn("no index", said)
        self.assertIn("Nothing was deleted", said)
        self.assertTrue(environment.interpreter_path(self.root).exists())
        # AND THE MARKER STILL SAYS WHAT IT WAS INSTALLED FROM, so the next
        # setup still knows this environment is stale rather than ready.
        self.assertEqual(environment.observe(self.root, self.environ)["state"],
                         "stale")

    def test_setup_never_touches_the_stacks_own_runtime_state(self):
        """Repeat setup preserves persistent stack state, which it does by
        never knowing where it is."""
        import io
        import tokenize

        source = Path(environment.__file__).read_text()
        code = " ".join(
            text for kind, text, _, _, _ in
            tokenize.generate_tokens(io.StringIO(source).readline)
            if kind not in (tokenize.COMMENT, tokenize.STRING))
        for absent in ("BATON_V12_STACK_ROOT", "rmtree", "unlink", "rmdir"):
            self.assertNotIn(absent, code, absent)


class TheInterpreterOverrideIsExecutable(unittest.TestCase):
    """E1. The documented remedy has to BE one.

    `just setup PY=/usr/bin/python3.13` was recommended in the recipe comment,
    in STACK.md and in two refusals. `PY` is a recipe ARGUMENT here, not a named
    option, so real `just` expansion forwards the whole `PY=...` string as the
    interpreter path and setup refuses it -- handing a broken remedy to exactly
    the operator whose default Python is too old.

    SO THIS RUNS `just`. Searching the recipe's prose is what let the wrong
    spelling survive; only expansion establishes what an operand becomes.
    """

    def expand(self, *operands, recipe="setup"):
        found = shutil.which("just")
        if found is None:
            raise AssertionError(
                "`just` is not on PATH, and this case exists because reading "
                "the recipe cannot answer what `just` does with an operand. "
                "Install it, or run this suite where the repository's own "
                "justfiles can be run.")
        done = subprocess.run([found, "--justfile", str(_DISTRIBUTION.parent / "justfile"),
                               "--dry-run", recipe, *operands],
                              capture_output=True, text=True, timeout=120,
                              cwd=str(_DISTRIBUTION.parent))
        self.assertEqual(done.returncode, 0, done.stderr)
        return done.stderr + done.stdout

    def test_a_positional_interpreter_reaches_the_helper_as_a_path(self):
        self.assertIn('--python "/usr/bin/python3.13"',
                      self.expand("/usr/bin/python3.13"))

    def test_the_default_is_the_ambient_python3(self):
        self.assertIn('--python "python3"', self.expand())

    def test_the_recipe_asks_the_helper_for_the_root_rather_than_assigning_one(self):
        """[I1]: the recipe assigned its own default over an exported
        selection, and a `just` default cannot read the environment -- so the
        order is resolved by the helper the recipes already ask for the
        interpreter, and the expansion shows exactly that."""
        expanded = self.expand(recipe="test-bootstrap")
        self.assertIn('tools.environment test-root --chosen ""', expanded)
        self.assertIn('BATON_V12_STACK_TEST_ROOT="$SELECTED"', expanded)

    def test_a_named_bootstrap_test_root_reaches_the_helper(self):
        self.assertIn('test-root --chosen "/srv/scratch"',
                      self.expand("/srv/scratch", recipe="test-bootstrap"))

    def test_a_lifecycle_recipe_given_a_DESTINATION_dispatches_to_its_justfile(self):
        """OWNER-STANDALONE-INTERFACE-20260916.md: "once deployed, we shouldn't
        have to require more than the destination for stop/start/status", and a
        source-side wrapper "require[s] at most DESTINATION and dispatch[es] to
        that deployed interface"."""
        for recipe in ("start", "stop", "status"):
            expanded = self.expand("/srv/d", recipe=recipe)
            self.assertIn('exec just --justfile "$(realpath -m "/srv/d")'
                          '/justfile" ' + recipe, expanded, recipe)
            # AND NOTHING FROM THIS CHECKOUT reaches the deployment: no helper,
            # no interpreter, no JSON operand.
            self.assertNotIn("tools.instance command", expanded, recipe)
            self.assertNotIn("--instance", expanded, recipe)

    def test_the_monitor_takes_the_destination_and_the_interval(self):
        expanded = self.expand("/srv/d", "3", recipe="monitor")
        self.assertIn('exec just --justfile "$(realpath -m "/srv/d")/justfile" '
                      'monitor "3"', expanded)
        self.assertNotIn("status.json", expanded)

    def test_without_a_destination_the_checkout_form_is_unchanged(self):
        for recipe in ("start", "stop", "status", "monitor"):
            expanded = self.expand(recipe=recipe)
            self.assertIn("tools.environment interpreter", expanded, recipe)
            self.assertIn("PYTHONPATH=src:.", expanded, recipe)

    def test_bootstrap_forwards_a_destination_and_a_built_runtime(self):
        expanded = self.expand("inputs.json", "/srv/deployment", "build/out/x",
                               recipe="bootstrap")
        self.assertIn('if [[ -n "/srv/deployment" ]]; then', expanded)
        self.assertIn('--destination "/srv/deployment"', expanded)
        # RESOLVED WHERE IT WAS TYPED. The body runs from `python/`, so a
        # relative operand resolved after that `cd` would have quietly meant
        # `v12/python/build/out/x` -- which is where the first live install
        # refused, saying there was no runtime there.
        self.assertIn('DISTRO_HERE="$(realpath -m "build/out/x")"', expanded)
        self.assertIn('--distro "$DISTRO_HERE"', expanded)
        self.assertIn('INPUTS_HERE="$(realpath -m "inputs.json")"', expanded)

    def test_bootstrap_without_a_destination_installs_nothing(self):
        """The operand is what decides, so the expansion is read as the GUARD
        it is: `just` prints the whole body, taken branch or not, and asserting
        on the word alone would answer about text that never runs."""
        expanded = self.expand("inputs.json", recipe="bootstrap")
        self.assertIn('if [[ -n "" ]]; then\n\tINSTALLING+=(--destination "" '
                      '--distro "$DISTRO_HERE")', expanded)
        self.assertIn('INPUTS_HERE="$(realpath -m "inputs.json")"', expanded)

    def test_a_lifecycle_recipe_without_a_destination_does_not_take_that_branch(self):
        for recipe in ("start", "stop", "status", "monitor"):
            expanded = self.expand(recipe=recipe)
            self.assertIn('if [[ -n "" ]]; then', expanded, recipe)
            self.assertIn('--justfile "$(realpath -m "")/justfile"', expanded,
                          recipe)

    def test_bootstrap_builds_its_own_distribution_from_two_operands(self):
        """The owner-selected public interface is two operands. Naming a third
        stays a development convenience."""
        expanded = self.expand("inputs.json", "/srv/deployment",
                               recipe="bootstrap")
        self.assertIn('if [[ -n "/srv/deployment" && -z "" ]]; then', expanded)
        self.assertIn("just --justfile", expanded)
        self.assertIn("build", expanded)
        self.assertIn('DISTRO_HERE="$(dirname "', expanded)

    def test_a_named_distribution_is_not_rebuilt(self):
        expanded = self.expand("inputs.json", "/srv/deployment", "build/out/x",
                               recipe="bootstrap")
        self.assertIn('if [[ -n "/srv/deployment" && -z "build/out/x" ]]; then',
                      expanded)

    def test_the_named_option_spelling_would_have_been_forwarded_whole(self):
        """The defect itself, kept as a case so the documentation cannot drift
        back to it: `PY=` is not an override, it is the path."""
        self.assertIn('--python "PY=/usr/bin/python3.13"',
                      self.expand("PY=/usr/bin/python3.13"))

    def test_nothing_recommends_the_spelling_that_does_not_work(self):
        for place in (_DISTRIBUTION.parent / "justfile",
                      _DISTRIBUTION / "tools" / "environment.py"):
            self.assertNotIn("just setup PY=", place.read_text(), str(place))

    def test_the_runbook_says_the_wrong_spelling_is_wrong(self):
        """The one place it may still appear is a warning, so an operator who
        already learned the broken form is told rather than left guessing."""
        runbook = (_DISTRIBUTION.parent / "STACK.md").read_text()
        self.assertIn("just setup PY=", runbook)
        # The warning is a sentence, not a line, so the paragraph is what is
        # read -- a line-by-line check would be asserting about line wrapping.
        for paragraph in runbook.split("\n\n"):
            if "just setup PY=" in paragraph:
                self.assertIn("does not work", paragraph)


class TheRecipesRefuseAChangedRuntime(unittest.TestCase):
    """THE ACTUAL RECIPE BRANCH, not its dry-run text.

    Review 2026-09-16T13-36-58Z [K2]: the helper answered from the selector
    alone, so `just status <instance>` EXECUTED a changed launcher and returned
    zero. Expansion checks could never have caught that -- the expansion was
    right and what it ran was wrong -- so these run `just` for real against a
    harmless printing stand-in for a bundle.

    THE FIXTURE IS A PRINTING SCRIPT, NOT A BUNDLE. It establishes that the
    recipe reaches, or does not reach, the command an instance names. It is not
    a packaged-build acceptance (`tests/tools/test_packaging.py` owns that when
    it exists), and no security claim beyond selected corrupt/mismatch
    preservation follows from it.
    """

    MARKER = "instance-runtime-ran"

    def setUp(self):
        self.just = shutil.which("just")
        if self.just is None:
            raise AssertionError(
                "`just` is not on PATH, and these cases exist because the "
                "recipe's TEXT cannot answer what it runs.")
        self.temp = tempfile.TemporaryDirectory(prefix="v12-recipe-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        sys.path.insert(0, str(_DISTRIBUTION))
        from tools import instance

        self.instance = instance
        self.destination = str(self.root / "deployment")
        self.places = instance.layout(self.destination)
        distro = Path(self.places["distro"])
        (distro / "_internal").mkdir(parents=True)
        self.launcher = distro / "baton-v12-stack"
        self.launcher.write_text("#!/bin/sh\necho " + self.MARKER + " \"$@\"\n")
        self.launcher.chmod(0o755)
        self.library = distro / "_internal" / "lib.so"
        self.library.write_text("bytes of a library")
        for name in ("stores", "repository", "logs", "state"):
            Path(self.places[name]).mkdir(parents=True, exist_ok=True)
        from tools import bootstrap

        Path(self.places["justfile"]).write_text(
            bootstrap.deployed_justfile(self.places))
        self.publish()

    def publish(self):
        held = self.instance.manifest(self.places["distro"])
        document = self.instance.emit(
            self.destination, authority_uuid="0" * 31 + "a",
            identity={"frozen": True}, runtime=held, now=1.0)
        self.instance.publish(self.places["instance"], document)

    def recipe(self, name, *operands):
        """Run the real SOURCE recipe, in a runtime directory this test owns.

        `just` writes a script for a shebang recipe under XDG_RUNTIME_DIR, and
        a host whose runtime directory is read-only would otherwise fail before
        the recipe was ever launched -- which is a fact about the host, not
        about the recipe.
        """
        runtime = self.root / "runtime"
        runtime.mkdir(exist_ok=True)
        return subprocess.run(
            [self.just, "--justfile", str(_DISTRIBUTION.parent / "justfile"),
             name, *operands],
            cwd=str(_DISTRIBUTION.parent), capture_output=True, text=True,
            timeout=120,
            env=dict(os.environ, XDG_RUNTIME_DIR=str(runtime)))

    def deployed(self, name, *operands):
        """Run the DESTINATION's own justfile, from an unrelated directory."""
        runtime = self.root / "runtime"
        runtime.mkdir(exist_ok=True)
        return subprocess.run(
            [self.just, "--justfile", self.places["justfile"], name, *operands],
            cwd="/", capture_output=True, text=True, timeout=120,
            env={"HOME": str(self.root), "PATH": os.environ["PATH"],
                 "XDG_RUNTIME_DIR": str(runtime)})

    def test_an_unchanged_runtime_is_reached(self):
        """The positive control. Every refusal below is worth nothing if the
        ordinary path never ran the deployment's own command."""
        for name in ("start", "stop", "status", "monitor"):
            done = self.recipe(name, self.destination)
            self.assertEqual(done.returncode, 0, name + ": " + done.stderr)
            self.assertIn(self.MARKER, done.stdout, name)
            # AND IT IS THAT DEPLOYMENT'S OWN COMMAND, with the instance named.
            self.assertIn(self.places["instance"], done.stdout, name)

    def test_the_DEPLOYED_justfile_reaches_it_from_anywhere(self):
        """The interface the owner selected: no operand, from `/`."""
        for name in ("start", "stop", "status", "repository"):
            done = self.deployed(name)
            self.assertEqual(done.returncode, 0, name + ": " + done.stderr)
            self.assertIn(self.MARKER, done.stdout, name)
            self.assertIn(self.places["instance"], done.stdout, name)

    def test_the_runtime_CHECK_moved_into_the_command_and_this_says_so(self):
        """WHAT THE OWNER-SELECTED INTERFACE CHANGED, stated rather than
        quietly lost.

        Until OWNER-STANDALONE-INTERFACE-20260916.md the source recipe asked
        `tools.instance command`, which VERIFIED the runtime and only then
        printed a path for the recipe to exec -- so a changed launcher never
        ran. The deployed interface has no checkout to ask: the destination's
        own justfile runs `<HERE>/distro/baton-v12-stack`, and the command
        verifies its own instance (`stack.instance_settings` ->
        `instance.verify`) before deriving a single path.

        THE LIMIT IS REAL AND IT IS NOT HIDDEN. A self-contained deployment
        cannot prove its own launcher's bytes before that launcher runs;
        nothing inside it is outside it. What the command's verification does
        catch -- a changed library, a changed frozen asset, an unbound extra
        file, another instance's selector -- is checked against a REAL bundle
        by `tests/tools/test_packaging.py` and by the retained live evidence in
        LIFECYCLE-187142.json, where `status` and `start` both refuse a changed
        runtime. A printing stand-in cannot verify itself, so these cases no
        longer pretend to ask it to.
        """
        from tools import instance as instances
        from tools import stack

        out = io.StringIO()
        with mock.patch.object(instances, "verify",
                               side_effect=instances.InstanceRefusal(
                                   "the runtime is not the one this instance "
                                   "was prepared with")):
            code = stack.main(["--instance", self.places["instance"], "status"],
                              stream=out, environ={})
        self.assertEqual(code, 2)
        self.assertIn("refused:", out.getvalue())
        self.assertIn("not the one this instance was prepared with",
                      out.getvalue())

    def test_the_command_is_reached_with_no_operand_at_all(self):
        """And the interface itself: `just status` in the destination, with
        the instance still named beneath it."""
        done = self.deployed("status")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn(self.MARKER, done.stdout)
        self.assertIn("--instance", done.stdout)
        self.assertIn(self.places["instance"], done.stdout)


class TheBootstrapRecipeReachesTheHelper(unittest.TestCase):
    """THE ACTUAL RECIPE, both forms. Review 2026-09-16T14-06-35Z [R1]: the
    body resolved the OPTIONAL distro unconditionally, and `realpath -m ""` is
    an error -- so `just bootstrap inputs.json`, the form that installs
    nothing, died in the shell before Python ran at all. An expansion check
    could not see that: the expansion was right and the shell rejected it.

    A path that does not exist is used on purpose. What is under test is that
    the HELPER is reached and refuses by name; composing a real deployment is
    `test_bootstrap`'s, and it must not happen as a side effect of checking a
    recipe.
    """

    def setUp(self):
        self.just = shutil.which("just")
        if self.just is None:
            raise AssertionError("`just` is not on PATH, and this case exists "
                                 "because the recipe's text cannot answer what "
                                 "the shell does with it.")
        self.temp = tempfile.TemporaryDirectory(prefix="v12-recipe-bootstrap-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def recipe(self, *operands):
        runtime = self.root / "runtime"
        runtime.mkdir(exist_ok=True)
        return subprocess.run(
            [self.just, "--justfile", str(_DISTRIBUTION.parent / "justfile"),
             "bootstrap", *operands],
            cwd=str(_DISTRIBUTION.parent), capture_output=True, text=True,
            timeout=300, env=dict(os.environ, XDG_RUNTIME_DIR=str(runtime)))

    def test_the_form_that_installs_NOTHING_reaches_the_helper(self):
        done = self.recipe(str(self.root / "absent-inputs.json"))
        self.assertIn("refused: there is no input document at", done.stdout)
        self.assertIn(str(self.root / "absent-inputs.json"), done.stdout)
        # NOT the shell's own error, which is what it was.
        self.assertNotIn("realpath", done.stderr)

    def test_a_named_distribution_that_is_absent_is_refused_BY_NAME(self):
        """With two operands the recipe BUILDS, so the missing-runtime refusal
        is reached by naming one that is not there. It stays the helper's."""
        inputs = self.root / "inputs.json"
        inputs.write_text("{}")
        done = self.recipe(str(inputs), str(self.root / "destination"),
                           str(self.root / "no-such-distro"))
        self.assertIn("no built runtime at", done.stdout)
        self.assertFalse((self.root / "destination").exists())

    def test_an_OPTION_in_a_positional_slot_is_refused_by_the_recipe(self):
        """[V3]: `just bootstrap inputs dest --no-repositories` bound that
        option as DISTRO, so the recipe looked for a runtime called
        `--no-repositories` and the option never reached the helper. `just` has
        no option forwarding; the operand order IS the interface, so a mistake
        in it is said out loud rather than acted on."""
        done = self.recipe("inputs.json", "/srv/d", "--no-repositories")
        self.assertEqual(done.returncode, 2, done.stdout + done.stderr)
        said = done.stdout + done.stderr
        self.assertIn("is an option in a positional slot", said)
        # AND IT SHOWS THE FORM THAT WORKS, with the operand it was given.
        self.assertIn('"" "--no-repositories"', said)
        # Nothing ran: no build, no helper, no destination.
        self.assertNotIn("no input document", said)

    def test_the_documented_form_reaches_the_HELPER(self):
        """The counterpart: the fourth operand is forwarded verbatim, so the
        helper -- not the recipe -- is what answers.

        A DISTRO IS NAMED HERE ON PURPOSE. Review 2026-09-16T21-31-10Z [B1]:
        this case used the empty-DISTRO form, and that branch runs `just build`
        -- pip and PyInstaller -- BEFORE Python ever reads the absent input
        document, so a check written to be offline built the distribution every
        time it ran. Naming an existing directory takes the branch that does
        not build; the two-operand form is checked below against a recorded
        stand-in, which is the only way to see its argv without paying for it.
        """
        distro = self.root / "named-runtime"
        distro.mkdir()
        done = self.recipe(str(self.root / "absent.json"), str(self.root / "d"),
                           str(distro), "--no-repositories")
        said = done.stdout + done.stderr
        self.assertIn("there is no input document at", said)
        self.assertNotIn("is an option in a positional slot", said)
        self.assertFalse((self.root / "d").exists())

    def shadowed(self):
        """A PATH whose `just`, `python3` and prepared interpreter RECORD what
        they were asked for instead of doing it, and whose build tools REFUSE.

        The recipe body carries its own `#!/usr/bin/env bash`, so `just` runs
        it as a script and its PATH is exactly what is handed in -- the outer
        `just` is reached by absolute path and is the real one, while every
        program the BODY resolves by name is one of these. What is under test
        is the recipe's own argument forwarding, which is text no expansion
        check can answer; what is deliberately not under test is pip,
        PyInstaller or a clone.
        """
        binaries = self.root / "shadow"
        binaries.mkdir(exist_ok=True)
        asked = self.root / "asked.log"
        refused = self.root / "refused.log"
        prepared = binaries / "prepared-interpreter"

        def script(place, body):
            place.write_text("#!/usr/bin/env bash\n" + body)
            place.chmod(0o755)

        record = ('printf "%s\\n" "$(basename "$0")|$*" >> "' + str(asked) + '"\n')
        script(binaries / "just", record + "exit 0\n")
        script(binaries / "python3", record
               + 'if [[ "$*" == *tools.environment* ]]; then\n'
               + '  echo "' + str(prepared) + '"\nfi\nexit 0\n')
        script(prepared, record + "exit 0\n")
        # AND THE THINGS A BUILD WOULD REACH SAY SO RATHER THAN RUNNING.
        for name in ("pip", "pip3", "pyinstaller", "npm", "g" + "it"):
            script(binaries / name,
                   'printf "%s\\n" "$(basename "$0")|$*" >> "'
                   + str(refused) + '"\nexit 97\n')
        return binaries, asked, refused, prepared

    def test_the_TWO_OPERAND_form_forwards_the_built_path_without_building(self):
        """[B1] The documented normal form, with the build recorded rather than
        run. What it must forward is the destination and the path `just build`
        produces -- resolved from `v12/`, which is the defect one operand below
        this once was -- plus anything in EXTRA, verbatim."""
        binaries, asked, refused, prepared = self.shadowed()
        output = _DISTRIBUTION / "build" / "out"
        before = output.stat().st_mtime_ns if output.exists() else None

        done = subprocess.run(
            [self.just, "--justfile", str(_DISTRIBUTION.parent / "justfile"),
             "bootstrap", str(self.root / "absent.json"),
             str(self.root / "d"), "", "--no-repositories"],
            cwd=str(_DISTRIBUTION.parent), capture_output=True, text=True,
            timeout=120, env=dict(os.environ,
                                  PATH=str(binaries) + ":" + os.environ["PATH"],
                                  XDG_RUNTIME_DIR=str(self.root)))
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)

        lines = asked.read_text().splitlines()
        # THE BRANCH WAS TAKEN: the recipe asked for a build, and got a
        # recording instead of pip and PyInstaller.
        self.assertIn("just|--justfile " + str(_DISTRIBUTION.parent / "justfile")
                      + " build", lines)
        # AND THE HELPER WAS REACHED WITH THE BUILT PATH.
        helper = [one for one in lines if one.startswith("prepared-interpreter|")]
        self.assertEqual(len(helper), 1, lines)
        operands = helper[0].split("|", 1)[1].split()
        self.assertEqual(operands[:2], ["-m", "tools.bootstrap"])
        self.assertEqual(operands[operands.index("--destination") + 1],
                         str(self.root / "d"))
        self.assertEqual(
            os.path.realpath(operands[operands.index("--distro") + 1]),
            os.path.realpath(_DISTRIBUTION / "build" / "out" / "distro"))
        self.assertEqual(operands[-1], "--no-repositories")
        # NOTHING REAL HAPPENED. No build tool was reached, the destination was
        # never composed, and the bundle on disk is byte-for-byte untouched.
        self.assertFalse(refused.exists(), refused.read_text()
                         if refused.exists() else "")
        self.assertFalse((self.root / "d").exists())
        if before is not None:
            self.assertEqual(output.stat().st_mtime_ns, before)

    def test_the_stand_in_would_SEE_a_real_build_tool_being_reached(self):
        """The control for the case above: a recording that proves nothing is
        worse than no recording. Reaching one of the refusing programs writes
        the file whose absence is the assertion."""
        binaries, _asked, refused, _prepared = self.shadowed()
        done = subprocess.run([str(binaries / "pip"), "install", "-r", "x.txt"],
                              capture_output=True, text=True, timeout=30)
        self.assertEqual(done.returncode, 97)
        self.assertIn("pip|install -r x.txt", refused.read_text())

    def test_the_guide_shows_that_form_and_not_the_broken_one(self):
        runbook = (_DISTRIBUTION.parent / "STACK.md").read_text()
        self.assertIn('just bootstrap /path/to/inputs.json /srv/baton-v12 "" '
                      '"--no-repositories"', runbook)
        # The form that binds as DISTRO must not be recommended anywhere.
        for line in runbook.splitlines():
            if line.strip().startswith("just bootstrap "):
                operands = line.split()[2:]
                for index, one in enumerate(operands):
                    if one.startswith("--") and index < 2:
                        self.fail("the guide shows an option in a positional "
                                  "slot: " + line)

    def test_the_guides_DIRECT_helper_example_resolves_from_where_it_stands(self):
        """[B2]: the example said `cd v12/python` and then
        `--distro python/build/out/distro`, which after that cd names
        `v12/python/python/build/out/distro` -- a path that does not exist. The
        recipe's operand is right because the recipe resolves it from `v12/`;
        a command typed in `v12/python` needs the path from THERE.

        Every relative operand in a `cd v12/python` example is resolved against
        that directory and required to exist in this checkout, so the two forms
        cannot drift into each other again.
        """
        runbook = (_DISTRIBUTION.parent / "STACK.md").read_text()
        lines = runbook.splitlines()
        examples, standing = 0, None
        for index, line in enumerate(lines):
            if "cd v12/python" in line:
                standing = _DISTRIBUTION
            if standing is None or "--distro" not in line:
                continue
            operand = line.split("--distro", 1)[1].split()[0]
            if operand.startswith("/") or operand.startswith("<"):
                continue
            examples += 1
            # WHERE THE BUILD ACTUALLY LANDS, taken from the recipe rather than
            # restated: `just build` puts it at
            # `$(dirname justfile)/python/build/out/distro`. Compared as a
            # PATH, so a checkout that has never been built still answers.
            recipe = (_DISTRIBUTION.parent / "justfile").read_text()
            self.assertIn('/python/build/out/distro', recipe)
            self.assertEqual(
                os.path.normpath(standing / operand),
                os.path.normpath(_DISTRIBUTION / "build" / "out" / "distro"),
                "STACK.md line " + str(index + 1) + ": `" + operand
                + "` does not name the built runtime from " + str(standing))
            # AND THE INTERPRETER IS THE PREPARED ONE, as everywhere else.
            block = "\n".join(lines[max(0, index - 6):index + 1])
            self.assertIn("tools.environment interpreter", block)
        self.assertGreaterEqual(examples, 1, "the direct-helper example is gone")

    def test_a_relative_runtime_is_resolved_where_it_was_typed(self):  # noqa: D401
        inputs = self.root / "inputs.json"
        inputs.write_text("{}")
        done = self.recipe(str(inputs), str(self.root / "destination"),
                           "python/build/out/distro")
        # Either it found the built bundle (this checkout has one) or it says
        # where it looked -- and where it looked is v12/, not v12/python/.
        self.assertNotIn("v12/python/python/build", done.stdout + done.stderr)


class TheGateCannotSkip(unittest.TestCase):
    """[R2]: `just test-packaging` inherited BATON_V12_STACK_DISTRO while
    building the DEFAULT output, so an operator whose environment named
    something else -- or nothing -- got exit 0 with nine skipped checks from
    the one gate that cannot be stood in for."""

    def body(self):
        bodies, name = {}, None
        for line in (_DISTRIBUTION.parent / "justfile").read_text().splitlines():
            if not line.strip():
                continue
            if line[:1] in ("\t", " "):
                if name is not None:
                    bodies[name].append(line)
                continue
            if line.startswith("#") or ":=" in line or ":" not in line:
                name = None
                continue
            name = line.split(":")[0].split()[0]
            bodies[name] = []
        return "\n".join(bodies["test-packaging"])

    def test_the_recipe_binds_the_bundle_it_just_built(self):
        body = self.body()
        self.assertIn('BATON_V12_STACK_DISTRO="$PWD/build/out/distro"', body)
        self.assertIn("build", body)

    def test_the_recipe_says_this_run_is_the_gate(self):
        self.assertIn("BATON_V12_STACK_PACKAGING_REQUIRED=1", self.body())

    def test_the_module_FAILS_rather_than_skipping_when_it_is_the_gate(self):
        from tests.tools import test_packaging

        case = test_packaging.WhatTheBundleSaysItIs("test_the_frozen_schema_assets_travelled")
        with mock.patch.dict(os.environ,
                             {test_packaging.VARIABLE: "/nowhere-at-all",
                              test_packaging.REQUIRED: "1"}):
            answer = case.run()
        self.assertEqual(len(answer.failures), 1)
        self.assertIn("a skip would be a false pass", answer.failures[0][1])
        self.assertEqual(answer.skipped, [])

    def test_and_SKIPS_when_it_is_not(self):
        """Registered in the parallel suite, where a machine may legitimately
        have no bundle. The gate is the recipe."""
        from tests.tools import test_packaging

        case = test_packaging.WhatTheBundleSaysItIs("test_the_frozen_schema_assets_travelled")
        environ = dict(os.environ)
        environ.pop(test_packaging.REQUIRED, None)
        environ[test_packaging.VARIABLE] = "/nowhere-at-all"
        with mock.patch.dict(os.environ, environ, clear=True):
            answer = case.run()
        self.assertEqual(answer.failures, [])
        self.assertEqual(len(answer.skipped), 1)
        self.assertIn("/nowhere-at-all", answer.skipped[0][1])


class TheBootstrapTestRootFollowsTheOperator(unittest.TestCase):
    """I1. Explicit operand, then the exported selection, then /var/tmp.

    The recipe used to assign its own default unconditionally, so an operator
    who had exported `BATON_V12_STACK_TEST_ROOT` ran the checks on a different
    storage root from the one they selected -- and was never told.
    """

    def resolved(self, chosen=None, exported=None):
        import io

        stream = io.StringIO()
        environ = {} if exported is None else {environment.TEST_ROOT_ENV: exported}
        environment.test_root(chosen, environ, stream=stream)
        return stream.getvalue().strip()

    def test_nothing_selected_is_the_documented_default(self):
        self.assertEqual(self.resolved(), environment.DEFAULT_TEST_ROOT)
        self.assertEqual(environment.DEFAULT_TEST_ROOT, "/var/tmp")

    def test_an_exported_selection_beats_the_default(self):
        self.assertEqual(self.resolved(exported="/srv/exported"), "/srv/exported")

    def test_an_explicit_operand_beats_the_default(self):
        self.assertEqual(self.resolved("/srv/explicit"), "/srv/explicit")

    def test_an_explicit_operand_beats_an_exported_selection(self):
        """Both at once: saying it here and now is the most specific thing an
        operator can do."""
        self.assertEqual(self.resolved("/srv/explicit", "/srv/exported"),
                         "/srv/explicit")

    def test_an_empty_or_blank_operand_is_not_a_selection(self):
        """`just` passes an empty string when the operand is omitted, so an
        empty one must fall through rather than become the root."""
        for blank in ("", "   ", None):
            self.assertEqual(self.resolved(blank, "/srv/exported"), "/srv/exported",
                             repr(blank))
            self.assertEqual(self.resolved(blank), environment.DEFAULT_TEST_ROOT,
                             repr(blank))

    def test_a_blank_exported_selection_is_not_a_selection_either(self):
        self.assertEqual(self.resolved(None, "   "), environment.DEFAULT_TEST_ROOT)

    def test_the_command_answers_on_stdout_for_the_recipe_to_consume(self):
        import io

        stream = io.StringIO()
        code = environment.main(["test-root", "--chosen", "/srv/explicit"],
                                stream=stream, environ={})
        self.assertEqual(code, 0)
        self.assertEqual(stream.getvalue().strip(), "/srv/explicit")


class AnInterruptedSetupResumes(Fixture):
    """E2. A directory this setup created is ours before it is finished.

    Ownership used to be published only after a successful install, so a first
    install that failed left a directory this tool had made and could no longer
    recognise: the next setup called its own partial environment FOREIGN and
    told the operator to remove it, and running the printed pip command by hand
    could not write the missing marker either -- so the four stack commands went
    on refusing an environment that was in fact complete.
    """

    def creating(self, failures):
        """A runner that creates a real-enough environment, then fails N times."""
        def running(argv, **named):
            self.ran.append(list(argv))
            if argv[1:3] == ["-m", "venv"]:
                (Path(argv[3]) / "bin").mkdir(parents=True, exist_ok=True)
                (Path(argv[3]) / "bin" / "python").symlink_to(sys.executable)
                return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")
            if failures:
                failures.pop()
                return subprocess.CompletedProcess(argv, 1, stdout="",
                                                   stderr="simulated index failure")
            return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")
        return running

    def test_a_failed_first_install_leaves_a_resumable_environment(self):
        with self.assertRaises(environment.SetupRefusal) as raised:
            environment.setup(self.root, self.environ, runner=self.creating([1]),
                              stream=open(os.devnull, "w"), now=1.0)
        self.assertIn("simulated index failure", str(raised.exception))
        # OURS, AND SAID SO: not foreign, not ready.
        answer = environment.observe(self.root, self.environ)
        self.assertEqual(answer["state"], "incomplete")
        self.assertIn("resumes it", answer["detail"])
        self.assertTrue(environment.marker_path(self.root).exists())

    def test_an_incomplete_environment_is_not_admitted_as_ready(self):
        with self.assertRaises(environment.SetupRefusal):
            environment.setup(self.root, self.environ, runner=self.creating([1]),
                              stream=open(os.devnull, "w"), now=1.0)
        with self.assertRaises(environment.SetupRefusal) as raised:
            environment.interpreter(self.root, self.environ)
        self.assertIn("incomplete", str(raised.exception))

    def test_the_retry_resumes_without_recreating_the_environment(self):
        with self.assertRaises(environment.SetupRefusal):
            environment.setup(self.root, self.environ, runner=self.creating([1]),
                              stream=open(os.devnull, "w"), now=1.0)
        self.ran.clear()
        code, text = self.output(lambda s: environment.setup(
            self.root, self.environ, stream=s, runner=self.creating([]), now=2.0))
        self.assertEqual(code, 0)
        self.assertIn("resuming an interrupted setup", text)
        # NO SECOND `venv`: the environment that is there is reused.
        self.assertEqual([argv for argv in self.ran if "venv" in argv], [])
        self.assertEqual(environment.observe(self.root, self.environ)["state"],
                         "ready")

    def test_ready_is_published_only_after_the_install_succeeds(self):
        import json as _json

        with self.assertRaises(environment.SetupRefusal):
            environment.setup(self.root, self.environ, runner=self.creating([1]),
                              stream=open(os.devnull, "w"), now=1.0)
        self.assertFalse(_json.loads(
            environment.marker_path(self.root).read_bytes())["installed"])
        environment.setup(self.root, self.environ, runner=self.creating([]),
                          stream=open(os.devnull, "w"), now=2.0)
        self.assertTrue(_json.loads(
            environment.marker_path(self.root).read_bytes())["installed"])

    def test_a_genuinely_foreign_directory_is_still_refused(self):
        """Resumability must not become acceptance: the distinction is the
        marker THIS setup wrote, not the directory's existence."""
        self.root.mkdir(parents=True)
        (self.root / "bin").mkdir()
        (self.root / "bin" / "python").symlink_to(sys.executable)
        kept = self.root / "somebody-elses-work"
        kept.write_text("important")
        self.assertEqual(environment.observe(self.root, self.environ)["state"],
                         "foreign")
        with self.assertRaises(environment.SetupRefusal):
            environment.setup(self.root, self.environ, runner=self.runner())
        self.assertTrue(kept.exists())
        self.assertEqual(self.ran, [])


class TheRecipesUseIt(unittest.TestCase):
    """The four stack commands resolve the prepared interpreter, and install
    nothing. `just install` stays the Node proof's."""

    def bodies(self):
        """Each recipe's own INDENTED body, keyed by the recipe's name.

        A column-0 line that is not a header ends the body: `just` recipe
        bodies are the indented block, and a parser that let file-level
        comments fall into the preceding recipe would answer prose when asked
        what a recipe runs -- which is how this check first passed while a
        comment three recipes away supplied the word it was looking for.
        """
        bodies, name = {}, None
        for line in (_DISTRIBUTION.parent / "justfile").read_text().splitlines():
            if not line.strip():
                continue
            if line[:1] in ("\t", " "):
                if name is not None:
                    bodies[name].append(line)
                continue
            if line.startswith("#") or ":=" in line or ":" not in line:
                name = None
                continue
            name = line.split(":")[0].split()[0]
            bodies[name] = []
        return {name: "\n".join(lines) for name, lines in bodies.items()}

    def test_every_stack_recipe_resolves_the_prepared_interpreter(self):
        bodies = self.bodies()
        for name in ("start", "stop", "status", "monitor", "test-bootstrap"):
            self.assertIn("tools.environment interpreter", bodies[name], name)

    def test_no_stack_recipe_installs_anything(self):
        bodies = self.bodies()
        for name in ("start", "stop", "status", "monitor", "test-bootstrap"):
            for banned in ("tools.environment --python", "environment setup",
                           "pip install", "venv"):
                self.assertNotIn(banned, bodies[name], name + "/" + banned)

    def test_setup_is_its_own_recipe_and_the_node_install_is_untouched(self):
        bodies = self.bodies()
        self.assertIn("tools.environment", bodies["setup"])
        self.assertIn("setup", bodies["setup"])
        # The Node proof's recipe is a different one and stays as it was.
        self.assertIn("npm ci", bodies["install"])
        self.assertNotIn("venv", bodies["install"])

    def test_the_bootstrap_test_recipe_carries_the_reviewed_bounds(self):
        """The command the review specified, made memorable rather than
        reconstructed from a dossier each time."""
        body = self.bodies()["test-bootstrap"]
        self.assertIn("timeout --kill-after=10s 180s", body)
        self.assertIn("BATON_V12_STACK_TEST_ROOT", body)
        self.assertIn("PYTHONPATH=src:.", body)
        self.assertIn("tests.tools.test_bootstrap", body)

    def test_the_bootstrap_test_recipe_cannot_swallow_a_failure(self):
        """A command whose exit status did not mean anything would be worse
        than not having one."""
        body = self.bodies()["test-bootstrap"]
        self.assertIn("set -euo pipefail", body)
        self.assertIn("exec env", body)
        for swallowing in ("|| true", "|| :", "; true", "set +e"):
            self.assertNotIn(swallowing, body, swallowing)

    def test_no_recipe_asks_an_operator_to_activate_anything(self):
        """Over the recipe BODIES, not the file: asserting over the whole text
        would ban the comments from using the word `source`, which is prose and
        reaches nothing. The same over-broad reading was corrected once already
        in this Work's boundary check."""
        for name, body in self.bodies().items():
            self.assertNotIn("activate", body, name)
            for line in body.splitlines():
                bare = line.strip()
                self.assertFalse(bare.startswith("source ") or bare.startswith(". "),
                                 name + ": " + bare)


if __name__ == "__main__":
    unittest.main(verbosity=2)
