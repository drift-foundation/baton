"""W366246 — ORDINARY TEMPLATE CREATION, THROUGH THE ACTUAL FROZEN COMMAND.

`test_connected_creation` drives the real `bootstrap.main` and the real
`job_manager.main` IN THIS PROCESS, against an instance it really installs.
That proves the operation, the owners and the installer's custody, and it is
accepted. What it cannot prove is the thing this suite exists for: that the
BUNDLE an operator is given -- the one-folder build carrying its own
interpreter, its own libraries and its own packaged resources -- creates an
ordinary Job. Its install is handed a stand-in runtime and patches
`bootstrap._identity_of`, because a directory with a file in it cannot answer
`identity`; so every question about packaged resources, dynamic imports and
actual command wiring was answered by a stand-in.

WHAT IS REAL HERE, AND IT IS EVERYTHING THE COMMAND DOES. `just build`
produces the bundle (`packaging/stack.spec`, the build tool pinned by
`requirements.build.lock`), and every operation below is that executable run
as a SUBPROCESS with nothing of this checkout in its environment: no
PYTHONPATH, no `BATON_V12_*`, no virtual environment, `HOME` inside a
disposable root and the working directory `/`. `tests/tools/test_packaging.py`
established that convention and this suite borrows it rather than inventing a
second one.

  * the INSTALL is the bundle's own `bootstrap` subcommand with `--distro`
    naming the bundle itself, so `_identity_of` runs the REAL command and
    holds it to being frozen, to carrying both frozen schema assets, and to
    naming a native validator that is one of the files the instance binds.
    Nothing is patched.
  * the CREATION is the bundle's own `manager ... create`, with the operator's
    ordinary operands and no digest, manifest or launch packet anywhere in
    them -- which is DESIGN SCH-1a's "Ordinary creation MUST NOT require
    operator-authored manifests or bespoke launch packets" asked of the
    deployed surface.
  * the TEMPLATE comes out of the bundle's own packaged resources. The
    refusal case reads the inventory this build carries out of the command's
    own sentence, and the created Job's template version is in it.

WHAT THIS PROCESS STILL DOES, and it is one thing: it COMPOSES the operator's
input document for `bootstrap`, using `test_bootstrap`'s accepted worker
fixtures, and writes it to a file. That document is operator input -- the
installer reads JSON and nothing else from it -- so composing it here is the
same act as an operator writing one, and `v12/STACK.md` is where its members
are specified. Nothing of this checkout reaches the command any other way.

NO LIVE EXECUTION OF ANY KIND. `--no-repositories` is passed, no Job is
served, no runtime is started, no provider or credential is reached, and no
version-control operation is performed by anything here.
"""
import json
import os
from pathlib import Path
import subprocess
import unittest

from baton_v12.worker_manager import ControlStore
from tools.creation_ports import instance_identity
from tools import instance, stack_command

from tests.tools import test_connected_creation as connected
# THE BUNDLE SELECTION RULE IS ONE RULE. `test_packaging` owns where a built
# runtime is looked for, the variable that moves it, and the variable that
# says "this run is the gate, so a skip would be a false pass". Re-deciding
# any of that here would be a second answer to one question.
from tests.tools import test_packaging


class PackagedCreationCase(connected.ConnectedCreationCase):
    """One really built bundle, installing and creating for itself.

    `ConnectedCreationCase` is borrowed for what it owns -- the accepted
    worker fixtures behind `document()`, a state root outside the checkout,
    and the readers for the configuration, the install document, the bindings
    and the Job store. Its own `installed`/`created`/`answered` helpers drive
    the SOURCE command and are deliberately not used; every method here that
    reaches the command is named `packaged_` so the two cannot be confused.
    """

    TASK = "pkg-first"
    JOB = "job-pkg-first"
    STATEMENT = "The task the packaged command was given."
    ACCEPTANCE = "The frozen command creates a bound, servable Job."
    SCOPE = "v12/python/tools/job_manager.py"

    def setUp(self):
        super().setUp()
        self.distro = test_packaging.built()
        if self.distro is None:
            missing = (
                "no built runtime to create with -- run `just build` from "
                "v12/ (or `just test-packaging`, which builds and then runs "
                "this), or name one with " + test_packaging.VARIABLE
                + ". A bundle is the one thing these cases cannot stand in "
                "for: creating a Job with the SOURCE command is what "
                "tests/tools/test_connected_creation.py already does.")
            if os.environ.get(test_packaging.REQUIRED):
                self.fail(missing + " -- and " + test_packaging.REQUIRED
                          + " is set, so this run is the gate and a skip "
                          "would be a false pass.")
            raise unittest.SkipTest(missing)
        self.command = self.distro / stack_command.COMMAND

    # -- the command, and nothing of this checkout around it ----------------

    def ran(self, *operands):
        """The bundle, run with NOTHING from this checkout in its environment.

        `test_packaging.Fixture.ran`'s rule, and the whole claim an installed
        deployment makes: no PYTHONPATH, no `BATON_V12_*`, no virtual
        environment, and not from the distribution directory.
        """
        return subprocess.run([str(self.command), *operands],
                              capture_output=True, text=True, timeout=600,
                              cwd="/", env={"HOME": str(self.root),
                                            "PATH": "/usr/bin:/bin"})

    def packaged_install(self, **members):
        """One disposable instance, installed BY THE BUNDLE ITSELF.

        `--distro` names the bundle under test, so the installer runs the real
        command to learn what it is installing. Nothing is patched: a build
        that was not frozen, or whose schema assets or native validator did
        not travel, is refused here by the product's own rule.
        """
        document = self.document(**members)
        # THE DESTINATION DECIDES THE LAYOUT. `bootstrap` replaces
        # `state_root` from `--destination`, and leaving one in the operator's
        # document would be two statements about one place.
        document.pop("state_root", None)
        inputs = os.path.join(self.root, "operator-inputs.json")
        Path(inputs).write_text(json.dumps(document, indent=1, sort_keys=True))
        done = self.ran("bootstrap", "--inputs", inputs,
                        "--destination", self.state,
                        "--distro", str(self.distro), "--no-repositories")
        self.assertEqual(done.returncode, 0, done.stderr or done.stdout)
        self.owned = instance_identity(self.state)
        # THE MANAGER'S FIRST RUN, standing in, exactly as the connected
        # creation fixture does it: a deployment's control store is created
        # when its manager first opens it, and a creation opens it read-only.
        with ControlStore.open(self.owned["control_store"],
                               incarnation="manager-1",
                               clock=lambda: "2026-09-02T00:00:00.000Z"):
            pass
        return done

    def packaged_argv(self, task=None, statement=None, *extra):
        """The operator's ordinary operands. NO DIGEST IS AMONG THEM."""
        return ["manager",
                "--store", self.owned["job_store"],
                "--incarnation", "cli-1",
                "--authority-uuid", self.owned["authority_uuid"],
                "create",
                "--instance", self.state,
                "--control", self.owned["control_store"],
                "--authority", self.owned["authority_store"],
                "--task", task or self.TASK,
                "--statement", statement or self.STATEMENT,
                "--acceptance", self.ACCEPTANCE,
                "--work-scope", self.SCOPE] + list(extra)

    def packaged_create(self, task=None, statement=None, *extra):
        return self.ran(*self.packaged_argv(task, statement, *extra))

    def packaged_answer(self, task=None, statement=None, *extra):
        """One creation the frozen command performed, as its own document."""
        done = self.packaged_create(task, statement, *extra)
        self.assertEqual(done.returncode, 0, done.stderr or done.stdout)
        return json.loads(done.stdout)

    def packaged_refusal(self, task=None, statement=None, *extra):
        """One creation the frozen command refused, with what it said.

        THE SHAPE IS THE CLI'S OWN AND IS NOT THIS WORK'S CHOICE.
        `job_manager.main` parses, dispatches and catches nothing, so a typed
        refusal reaches the caller rather than becoming an exit code --
        `test_connected_creation.refused` says so for the source command, and
        `submit`, `fresh-attempt` and `status` all behave this way. Frozen,
        that arrives as a non-zero exit with the refusal's own sentence on
        stderr, plus PyInstaller's own "Failed to execute script" line. What
        this asserts is what the FINDING requires: a TRUTHFUL refusal, naming
        the fact that stopped it, with nothing created.
        """
        done = self.packaged_create(task, statement, *extra)
        # EXIT 1 AND NOT MERELY NON-ZERO. A refusal that reaches the caller as
        # an exception exits 1; argparse exits 2. A draft of one case below
        # was green on an argparse message, so the two are told apart here
        # rather than in each case's own assertions.
        self.assertEqual(done.returncode, 1, done.stderr or done.stdout)
        self.assertEqual(done.stdout, "")
        self.assertIn("baton_v12.contracts.errors.ContractRefusal",
                      done.stderr)
        return done

    # -- what the instance holds afterwards ---------------------------------

    def job_task(self, job_id):
        from baton_v12.job_manager import creation

        store, _creation = self.rows()
        return creation.job_task_of(store, job_id)

    def created_rows(self):
        from baton_v12.job_manager import creation

        store, _creation = self.rows()
        return {one["job_id"]: one for one in creation.created_job_rows(store)}


class TheFrozenCommandInstallsTheBundleItIsGiven(PackagedCreationCase):
    """Before any Job: the install is the real one, holding the real command."""

    def test_the_instance_binds_this_bundle_and_verifies_against_it(self):
        self.packaged_install()
        selector = instance.read(instance.layout(self.state)["instance"])
        # THE RUNTIME THE INSTANCE RECORDED IS THE ONE IT COPIED, re-digested
        # by the product's own manifest rather than compared by path.
        held = instance.verify(selector)
        self.assertEqual(held["digest"], selector["runtime"]["digest"])
        self.assertGreater(held["files"], 10)
        self.assertEqual(
            instance.manifest(instance.layout(self.state)["distro"])["digest"],
            instance.manifest(str(self.distro))["digest"])

    def test_the_identity_the_install_recorded_is_the_commands_own(self):
        """`_identity_of` RAN THE COMMAND, and this is what it got back.

        The stand-in install this suite exists beside supplies this document
        itself; here it is the bundle's own answer, so `frozen`, the two
        packaged schema assets and the native extension are facts about the
        thing installed rather than about a fixture.
        """
        self.packaged_install()
        selector = instance.read(instance.layout(self.state)["instance"])
        said = selector["identity"]
        self.assertIs(said["frozen"], True)
        self.assertEqual(said["command"], stack_command.COMMAND)
        self.assertEqual(sorted(said["schema_assets"]),
                         ["agent-session-1.0", "worker-control-1.0"])
        self.assertTrue(all(one > 0 for one in
                            said["schema_assets"].values()), said)
        # THE EXTENSION IS ON DISK INSIDE WHAT THIS INSTANCE BINDS, which is
        # the defect a real build found and a stand-in cannot have.
        native = Path(said["native_rpds"])
        self.assertTrue(native.is_file(), said["native_rpds"])
        self.assertTrue(native.name.endswith(".so")
                        or ".so." in native.name, native.name)
        # AND THE BUILD SAYS WHICH SOURCE IT WAS MADE FROM.
        stamp = said["build_stamp"]
        self.assertEqual(stamp["schema"], "baton.v12.build-stamp/1")
        self.assertIn(stamp.get("dirty"), (True, False, None))


class TheFrozenCommandCreatesAnOrdinaryJob(PackagedCreationCase):
    """The outcome: ordinary operands in, one bound servable Job out."""

    def test_the_bundle_creates_binds_and_submits_one_template_job(self):
        self.packaged_install()
        held = self.packaged_answer()
        self.assertEqual(held["job_id"], self.JOB)
        self.assertEqual(held["work_id"], self.work)
        self.assertEqual(held["submission_id"], "sub-" + self.JOB)
        # THE SELECTED INTENT, carried back as the operator wrote it.
        self.assertEqual(held["task"]["statement"], self.STATEMENT)
        self.assertEqual(held["acceptance"], [self.ACCEPTANCE])
        self.assertEqual(held["scope"], {"work": [self.SCOPE], "tests": []})
        # EVERY DIGEST IS DERIVED BY THE DEPLOYMENT: the operator named none,
        # and there is no operand in `packaged_argv` that could have.
        self.assertTrue(held["source"]["input_digest"].startswith("sha256:"))
        self.assertTrue(held["source"]["policy_digest"].startswith("sha256:"))
        self.assertEqual(held["derivation"]["work_id"], self.work)
        # AND EVERY RESOLVED STAGE HAS A CONFIGURED WORKER THAT CAN SERVE IT.
        self.assertEqual(held["servable"], {"implementation": ["impl-a"],
                                            "review": ["review-a"]})

    def test_the_template_resolved_is_one_THIS_BUILD_carries(self):
        """THE PACKAGED RESOURCE, and the build's own inventory of it.

        The bundle read its template out of `sys._MEIPASS`, not out of a
        checkout it cannot see. The inventory is not asserted from this
        process's own packages: it is read out of the refusal the COMMAND
        writes when asked for a version it does not hold, which is the one
        place the build enumerates what it carries.
        """
        self.packaged_install()
        held = self.packaged_answer()
        self.assertEqual(held["template"]["origin"], "configured-default")
        version = held["template"]["version"]
        self.assertTrue(version.startswith("baton.v12.job-template."), version)
        self.assertEqual(held["template"]["permitted_overrides"],
                         ["execution_limits"])
        done = self.packaged_refusal("pkg-inventory", "Asking what it holds.",
                                     "--template", "baton.v12.job-template.a/9")
        self.assertIn("this build carries the job templates", done.stderr)
        self.assertIn(repr(version), done.stderr)

    def test_the_created_job_carries_its_own_task_and_its_binding(self):
        """WHAT IS DURABLE AFTERWARDS, read from the instance's own files."""
        self.packaged_install()
        held = self.packaged_answer()
        # THE TASK IS THE JOB'S OWN, in the Job store the command wrote.
        document = json.loads(self.job_task(self.JOB))
        self.assertEqual(document["task_id"], self.JOB)
        self.assertIn(self.STATEMENT, document["instructions"])
        self.assertIn(self.ACCEPTANCE, document["instructions"])
        self.assertIn(self.SCOPE, document["instructions"])
        self.assertIn(held["template"]["version"], document["instructions"])
        # THE BINDING IS PUBLISHED INTO THE INSTANCE'S OWN CONFIGURATION, and
        # additively into the install document a later binding derives from.
        bound = self.bindings()
        self.assertIn(self.JOB, bound)
        self.assertEqual(bound[self.JOB]["job_work_id"], self.work)
        self.assertEqual(bound[self.JOB]["source_worker_id"], "impl-a")
        self.assertEqual([one["job_id"]
                          for one in self.install_document()["jobs"]],
                         ["job-a", self.JOB])
        # AND THE JOB IS SUBMITTED: two stages, which the template selected.
        self.assertEqual(sorted(one["kind"] for one in
                                self.submitted(self.JOB)),
                         ["implementation", "review"])

    def test_two_ordinary_creations_bind_two_jobs(self):
        self.packaged_install()
        self.packaged_answer()
        self.packaged_answer("pkg-second", "A second packaged task.")
        self.assertEqual(sorted(self.bindings()),
                         ["job-a", self.JOB, "job-pkg-second"])
        first = json.loads(self.job_task(self.JOB))
        second = json.loads(self.job_task("job-pkg-second"))
        self.assertNotEqual(first["instructions"], second["instructions"])


class TheSameIntentReplaysThroughTheBundle(PackagedCreationCase):
    """Two identical operator requests are ONE creation, and say so."""

    def test_the_same_request_again_answers_the_same_job_once(self):
        self.packaged_install()
        first = self.packaged_answer()
        again = self.packaged_answer()
        self.assertEqual(again, first)
        # ONE RESERVATION, ONE BINDING, ONE SUBMISSION -- not two of anything.
        rows = self.created_rows()
        self.assertEqual(sorted(rows), [self.JOB])
        self.assertEqual(rows[self.JOB]["state"], "created")
        self.assertEqual([one["job_id"]
                          for one in self.install_document()["jobs"]],
                         ["job-a", self.JOB])
        self.assertEqual(len(self.submitted(self.JOB)), 2)

    def test_a_changed_intent_under_the_same_task_is_refused(self):
        """A DIFFERENT SELECTION IS A DIFFERENT CREATION, not a replay.

        The statement is part of the selected intent and the submission has
        nowhere to carry it, which is why the reservation keys on the whole
        request rather than on the submission's signature.
        """
        self.packaged_install()
        self.packaged_answer()
        done = self.packaged_refusal(self.TASK, "A different statement.")
        self.assertIn("is already the creation of a DIFFERENT request",
                      done.stderr)
        self.assertIn(self.JOB, done.stderr)
        # AND IT SAYS WHY A BYTE-IDENTICAL SUBMISSION IS STILL TWO CREATIONS.
        self.assertIn("the normalized submission carries none of the first "
                      "three", done.stderr)
        # AND THE FIRST CREATION IS UNTOUCHED.
        rows = self.created_rows()
        self.assertEqual(sorted(rows), [self.JOB])
        self.assertIn(self.STATEMENT,
                      json.loads(self.job_task(self.JOB))["instructions"])


class TheFrozenCommandRefusesTruthfully(PackagedCreationCase):
    """An invalid selection is named, and nothing is created for it."""

    def nothing_was_created(self, job_id):
        self.assertNotIn(job_id, self.created_rows())
        self.assertNotIn(job_id, self.bindings())
        self.assertEqual([one["job_id"]
                          for one in self.install_document()["jobs"]],
                         ["job-a"])

    def test_a_template_this_build_does_not_carry_is_refused_by_name(self):
        self.packaged_install()
        done = self.packaged_refusal(
            "pkg-unknown", "A task under a template nobody ships.",
            "--template", "baton.v12.job-template.not-shipped/9")
        self.assertIn("baton.v12.job-template.not-shipped/9", done.stderr)
        self.assertIn("is not one of them", done.stderr)
        self.nothing_was_created("job-pkg-unknown")

    def test_an_unsupported_source_selection_is_refused_by_name(self):
        self.packaged_install()
        done = self.packaged_refusal(
            "pkg-source", "A task from a source nobody serves.",
            "--source", "somewhere-else")
        self.assertIn("a creation's source selection is one of 'installed'",
                      done.stderr)
        self.assertIn("somewhere-else", done.stderr)
        self.nothing_was_created("job-pkg-source")

    def test_an_operand_this_command_does_not_serve_is_refused(self):
        """AN UNPERMITTED OVERRIDE HAS NO OPERAND, which IS the enforcement.

        A draft of this case passed `--override terminal_policy=...` and
        asserted that `terminal_policy` appeared in the refusal. It did --
        inside argparse's "unrecognized arguments" line -- so the case was
        green without the template's permitted-override rule being consulted
        at all. The deployed surface offers exactly the two operands the
        template permits (`--provider-turn-seconds`,
        `--verification-command-seconds`) and no way to ask for anything
        else, which is SCH-1a's "permitted explicit overrides" expressed as
        an argument list. What is true and worth asserting is that an operand
        this command does not serve is refused by the parser, by name, with
        exit 2 and nothing created.
        """
        self.packaged_install()
        done = self.packaged_create(
            "pkg-override", "A task overriding what it may not.",
            "--override", "terminal_policy=report-and-hold")
        self.assertEqual(done.returncode, 2, done.stderr)
        self.assertIn("unrecognized arguments: --override", done.stderr)
        # AND THE SUBCOMMANDS IN THAT USAGE ARE THIS BUILD'S OWN.
        self.assertIn("{submit,fresh-attempt,create,status,serve}",
                      done.stderr)
        self.nothing_was_created("job-pkg-override")

    def test_the_permitted_override_reaches_the_resolved_limits(self):
        """AND THE ONE THAT IS PERMITTED IS HONOURED, end to end.

        The other half of the same rule: the template permits
        `execution_limits`, the command serves it, and the frozen resolver
        carries it into the Job's own boundary rather than leaving the
        compatibility default in place.
        """
        self.packaged_install()
        held = self.packaged_answer("pkg-limits", "A bounded packaged task.",
                                    "--provider-turn-seconds", "120")
        self.assertEqual(held["overrides"],
                         {"execution_limits": {"provider_turn_seconds": 120}})
        limits = held["execution_limits"]
        self.assertEqual(limits["requested"], {"provider_turn_seconds": 120})
        turn = limits["boundaries"]["provider_turn"]
        self.assertEqual(turn["seconds"], 120)
        self.assertEqual(turn["origin"], "job")
        self.assertEqual(turn["default_seconds"], 3600)
        # EVERY OTHER BOUNDARY IS STILL THE DEPLOYMENT'S OWN.
        for name in ("host_verification", "integration_verification",
                     "ordinary_verification"):
            self.assertEqual(limits["boundaries"][name]["origin"],
                             "compatibility", name)

    def test_an_unknown_subcommand_is_refused_rather_than_guessed(self):
        """Nothing is installed for this one: the command refuses first."""
        done = self.ran("nonsense")
        self.assertEqual(done.returncode, 2)
        self.assertIn("no subcommand named 'nonsense'", done.stderr)
        self.assertIn("manager", done.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
