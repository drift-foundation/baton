"""W361912 — ORDINARY CREATION, THROUGH THE REAL COMMAND AND A REAL INSTALL.

Every earlier claim of this Work proved the operation and its ports against
documents and stand-in owners. This suite is the one the PLAN's current
milestone asks for: the supported CLI, against an instance this fixture
really INSTALLS, with the deployment's own stores, its own Authority, its own
install document and the real additive binding that publishes into it and
prepares again.

WHAT IS REAL. `tools.bootstrap.main` installs the destination; the deployment
configuration, the Authority, the identity, the selector and the install
document are its own. `tools.job_manager.main` is entered with the operator's
argv -- there is no helper here that composes the operation's operands. Behind
it `creation.create_template_job` runs under the Job store's lock and the
instance guard, and `creation_ports.NewJobBinding` publishes the Job entry
into `install-inputs.json` and calls `bootstrap.prepare` on it.

WHAT STANDS IN, NAMED. The one-folder RUNTIME is a directory carrying the
launcher's name and a file beside it -- `test_bootstrap`'s own stand-in, whose
docstring explains why: a frozen bundle cannot be built here and nothing in
this suite executes it. `_identity_of` is patched for the same reason, exactly
as that suite patches it. The CONTROL STORE is created by this fixture with
one `ControlStore.open`, which is what a deployment's manager does on its
first run; the creation opens it READ-ONLY and reads nothing from it but the
instance guard. No container engine, no provider, no serving loop and no
version control: `--no-repositories` is passed and the installed workers'
sources are directories.

WHAT DRIVING IT FOUND. Three defects, all of them invisible to a fixture that
composed the ports itself, all fixed in this candidate:

  * `install-inputs.json` was never written by anything. Its reader's
    docstring said `bootstrap.install` wrote it; nothing did, so on a real
    install EVERY additive binding -- an ordinary creation's and a fresh
    attempt's -- refused with "there is nothing here to add to".
  * the document `install` is handed is not the document `prepare` accepts:
    `main` adds the resolved `authority_uuid` for the selector and that
    member is SUPERSEDED as an input. Keeping it made the first binding
    refuse with "nothing reads authority_uuid".
  * the servability question was asked without the task the Job is being
    created with, so a Job whose submitted input identity is its own task's
    was compared against the INSTALLED one and refused as unservable by a
    pool that could serve it.
"""

import io
import json
import os
import unittest
from pathlib import Path
from unittest import mock

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import ControlStore

from tools import bootstrap, job_manager
from tools.creation_ports import instance_identity
from tools.fresh_attempt_ports import BindingRefusal

from tests.tools import test_bootstrap


class ConnectedCreationCase(test_bootstrap.ValidFixture):
    """One really installed instance, and the real command against it.

    `ValidFixture` is `test_bootstrap`'s own: a bootstrap input document whose
    workers are the ACCEPTED stage fixture's, a state root outside the
    checkout, and this instance's Authority identity persisted before anything
    is composed -- which is the fresh-install order itself.
    """

    def stand_in_runtime(self):
        """A directory shaped like a one-folder bundle, and nothing more."""
        source = Path(self.root) / "stand-in-distro"
        (source / "_internal").mkdir(parents=True, exist_ok=True)
        (source / "baton-v12-stack").write_text("a stand-in for the launcher")
        (source / "_internal" / "lib.so").write_text("stand-in bytes")
        return str(source)

    def installed(self, **members):
        """One instance, installed by the real installer."""
        document = self.document(**members)
        document.pop("state_root", None)
        inputs = os.path.join(self.root, "operator-inputs.json")
        Path(inputs).write_text(json.dumps(document))
        said = {"command": "baton-v12-stack", "frozen": True,
                "python": "3.13.7", "platform": "Linux", "machine": "x86_64",
                "schema_assets": {"agent-session-1.0": 10,
                                  "worker-control-1.0": 20},
                "native_rpds": str(Path(self.stand_in_runtime())
                                   / "_internal" / "lib.so")}
        out = io.StringIO()
        with mock.patch.object(
                bootstrap, "_identity_of",
                lambda command, runtime=None, distro=None: said):
            code = bootstrap.main(
                ["--inputs", inputs, "--destination", self.state,
                 "--distro", self.stand_in_runtime(), "--no-repositories"],
                stream=out)
        self.assertEqual(code, 0, out.getvalue())
        self.owned = instance_identity(self.state)
        # THE MANAGER'S FIRST RUN, standing in: a deployment's control store
        # is created when its manager first opens it, and the creation opens
        # it read-only.
        with ControlStore.open(self.owned["control_store"],
                               incarnation="manager-1",
                               clock=lambda: "2026-09-02T00:00:00.000Z"):
            pass
        return self.state, out.getvalue()

    def argv(self, task="cli-first", statement="The first CLI task.",
             **named):
        held = ["--store", self.owned["job_store"], "--incarnation", "cli-1",
                "--authority-uuid", self.owned["authority_uuid"],
                "create", "--instance", self.state,
                "--control", self.owned["control_store"],
                "--authority", self.owned["authority_store"],
                "--task", task, "--statement", statement,
                "--acceptance", "The CLI creates a bound, servable Job.",
                "--work-scope", "v12/python/tools/job_manager.py"]
        for name, value in named.items():
            held += ["--" + name.replace("_", "-"), str(value)]
        return held

    def created(self, **named):
        """One ordinary creation, through `job_manager.main`."""
        said = io.StringIO()
        code = job_manager.main(self.argv(**named), stream=said)
        return code, said.getvalue()

    def refused(self, expected=ContractRefusal, **named):
        """One creation this command refuses.

        THE REFUSAL IS AN EXCEPTION, which is this CLI's shape for every
        command: `job_manager.main` parses, dispatches and catches nothing, so
        a typed refusal reaches the caller rather than becoming an exit code.
        That is not this Work's choice -- `submit`, `fresh-attempt` and
        `status` all behave this way -- and a case that expected exit 2 would
        be asserting a surface nothing here has.
        """
        said = io.StringIO()
        with self.assertRaises(expected) as caught:
            job_manager.main(self.argv(**named), stream=said)
        return caught.exception, said.getvalue()

    def submitted(self, job_id):
        """The stage rows a SUBMISSION writes, which a reservation does not."""
        from baton_v12.job_manager import submission as job_rows

        store, _creation = self.rows()
        return [dict(one) for one in job_rows.stage_rows(store)
                if one["job_id"] == job_id]

    def answered(self, **named):
        code, said = self.created(**named)
        self.assertEqual(code, 0, said)
        return json.loads(said)

    def configuration(self):
        return json.loads(
            Path(self.owned["configuration"]
                 if "configuration" in self.owned
                 else os.path.join(self.state, "deployment.json")).read_text())

    def install_document(self):
        return json.loads(
            Path(os.path.join(self.state, "install-inputs.json")).read_text())

    def bindings(self):
        return {one["job_id"]: one
                for one in self.configuration().get("job_bindings") or []}

    def rows(self):
        from baton_v12.job_manager import JobStore, creation

        store = JobStore.open(self.owned["job_store"],
                              authority_uuid=self.owned["authority_uuid"],
                              incarnation="reader-1",
                              clock=lambda: "2026-09-02T00:00:00.000Z")
        self.addCleanup(store.close)
        return store, creation


class TheInstallKeepsTheDocumentItConsumed(ConnectedCreationCase):
    """The first defect, and the smallest one to state.

    An additive binding prepares from this instance's own install document.
    Nothing wrote it, so there was nothing to add to.
    """

    def test_a_real_install_leaves_a_preparable_input_document(self):
        self.installed()
        place = os.path.join(self.state, "install-inputs.json")
        self.assertTrue(os.path.isfile(place))
        document = self.install_document()
        # IT IS AN INPUT DOCUMENT, not the emitted configuration.
        self.assertEqual(document["schema"], bootstrap.SCHEMA)
        self.assertIn("jobs", document)
        # AND IT IS THE ONE `prepare` ACCEPTS: the superseded member `main`
        # adds for the selector is not in it.
        self.assertNotIn("authority_uuid", document)
        bootstrap.prepare(document, stream=io.StringIO())

    def test_the_installer_says_where_it_put_it(self):
        _destination, said = self.installed()
        self.assertIn("install-inputs.json", said)


class TheConnectedCreation(ConnectedCreationCase):
    """The milestone: the real command, the real install, one Job."""

    def test_the_command_creates_binds_and_submits_one_job(self):
        self.installed()
        held = self.answered()
        self.assertEqual(held["job_id"], "job-cli-first")
        self.assertEqual(held["work_id"], self.work)
        self.assertEqual(held["template"]["origin"], "configured-default")
        # EVERY DIGEST IS DERIVED: the operator named none.
        self.assertEqual(held["source"]["policy_digest"],
                         self.config["policy_digest"])
        self.assertTrue(held["source"]["input_digest"].startswith("sha256:"))
        # THE BINDING IS PUBLISHED INTO THE CONFIGURATION.
        bound = self.bindings()
        self.assertIn("job-cli-first", bound)
        self.assertEqual(bound["job-cli-first"]["job_work_id"], self.work)
        self.assertEqual(bound["job-cli-first"]["source_worker_id"], "impl-a")
        # AND INTO THE INSTALL DOCUMENT, additively: the Job the install
        # already named is still there.
        named = [one["job_id"] for one in self.install_document()["jobs"]]
        self.assertEqual(named, ["job-a", "job-cli-first"])
        # THE SUBMISSION IS ADMITTED and the Job carries its own task.
        store, creation = self.rows()
        self.assertEqual(held["submission_id"], "sub-job-cli-first")
        task = creation.job_task_of(store, "job-cli-first")
        self.assertIsNotNone(task)
        document = json.loads(task)
        self.assertEqual(document["task_id"], "job-cli-first")
        self.assertIn("The first CLI task.", document["instructions"])
        # AND EVERY RESOLVED STAGE HAS A WORKER THAT CAN SERVE IT.
        self.assertEqual(held["servable"],
                         {"implementation": ["impl-a"], "review": ["review-a"]})

    def test_two_ordinary_creations_bind_two_jobs(self):
        self.installed()
        self.answered()
        self.answered(task="cli-second", statement="The second CLI task.")
        named = [one["job_id"] for one in self.install_document()["jobs"]]
        self.assertEqual(named, ["job-a", "job-cli-first", "job-cli-second"])
        self.assertEqual(sorted(self.bindings()),
                         ["job-a", "job-cli-first", "job-cli-second"])
        store, creation = self.rows()
        first = json.loads(creation.job_task_of(store, "job-cli-first"))
        second = json.loads(creation.job_task_of(store, "job-cli-second"))
        self.assertNotEqual(first["instructions"], second["instructions"])


class ThePackagedResourcesResolve(ConnectedCreationCase):
    """What the command reads that an operator did not supply.

    An ordinary creation resolves a TEMPLATE out of this build and validates
    documents against SCHEMAS the installer verified. Neither is an operand,
    which is the point of SCH-1a: the only packaged resource an operator can
    name is the template VERSION, and omitting even that resolves the
    configured default.

    WHAT THIS CASE DOES NOT CLAIM. The frozen one-folder bundle's own
    resources are `tests/tools/test_packaging.py`'s question, asked of the
    real bundle; the runtime here is `test_bootstrap`'s stand-in directory and
    nothing in this suite executes it. That suite carries one failure on this
    base -- `attempt-diagnostics` is not among the deployed command's
    subcommands -- which is pre-existing and unrelated to this Work.
    """

    def test_the_template_the_answer_names_is_the_one_this_build_carries(self):
        from baton_v12.job_manager import templates

        self.installed()
        held = self.answered()
        version = held["template"]["version"]
        self.assertEqual(version, templates.DEFAULT_TEMPLATE)
        carried = templates.template_document(version)
        self.assertEqual(carried["version"], version)
        # THE RESOLUTION IS OVER THAT DOCUMENT: the stages the Job was
        # submitted with are the template's roles, in its order.
        self.assertEqual([one["kind"] for one in carried["roles"].values()]
                         if isinstance(carried.get("roles"), dict)
                         else [one["kind"] for one in carried["roles"]],
                         ["implementation", "review"])
        self.assertEqual(sorted(held["servable"]),
                         ["implementation", "review"])

    def test_the_install_verified_the_runtime_it_recorded(self):
        """The selector the install emitted, read back off the instance.

        The installer digests the runtime it copied and refuses one that
        changed; the selector carries that identity and the schema assets the
        admission reported. This reads them back rather than trusting the
        install's own output.
        """
        self.installed()
        selector = json.loads(
            Path(os.path.join(self.state, "instance.json")).read_text())
        self.assertEqual(selector["authority_uuid"],
                         self.owned["authority_uuid"])
        self.assertIn("worker-control-1.0",
                      json.dumps(selector["identity"]["schema_assets"]))
        self.assertEqual(len(selector["runtime"]["digest"]), 64)
        # AND THE COMMAND THE SELECTOR NAMES IS THE COPIED ONE, under this
        # destination rather than anywhere this fixture ran from.
        self.assertTrue(selector["command"].startswith(self.state))


class TheSameIntentConverges(ConnectedCreationCase):
    """Replay, and it is the operator running the same command twice."""

    def test_the_same_request_again_answers_the_same_job_once(self):
        self.installed()
        first = self.answered()
        before = json.dumps(self.configuration(), sort_keys=True)
        second = self.answered()
        self.assertEqual(first["job_id"], second["job_id"])
        self.assertEqual(first["resolution_digest"],
                         second["resolution_digest"])
        # NOTHING WAS PUBLISHED TWICE.
        self.assertEqual(json.dumps(self.configuration(), sort_keys=True),
                         before)
        named = [one["job_id"] for one in self.install_document()["jobs"]]
        self.assertEqual(named, ["job-a", "job-cli-first"])
        store, creation = self.rows()
        self.assertEqual(
            [one["job_id"] for one in creation.created_job_rows(store)],
            ["job-cli-first"])

    def test_a_changed_intent_under_the_same_job_refuses(self):
        self.installed()
        self.answered()
        refusal, _said = self.refused(statement="A DIFFERENT statement.")
        self.assertIn("job-cli-first", str(refusal))
        # AND THE FIRST CREATION IS UNTOUCHED.
        store, creation = self.rows()
        document = json.loads(creation.job_task_of(store, "job-cli-first"))
        self.assertIn("The first CLI task.", document["instructions"])
        named = [one["job_id"] for one in self.install_document()["jobs"]]
        self.assertEqual(named, ["job-a", "job-cli-first"])


class AnInterruptedPublicationIsRecoverable(ConnectedCreationCase):
    """The binding is two writes and a prepare, and a process can stop.

    `_create` publishes the install document FIRST and prepares it second,
    which is the direction its own comment calls harmless: an input naming a
    Job the configuration does not bind yet is finished by preparing the
    document it already describes. These cases stop the process at each of
    those points and then run the same command again.
    """

    def test_an_interruption_before_the_prepare_is_finished_by_a_rerun(self):
        self.installed()
        held = bootstrap.prepare

        def stopping(document, **named):
            raise RuntimeError("the fixture stopped the process")

        with mock.patch.object(bootstrap, "prepare", stopping):
            with self.assertRaisesRegex(RuntimeError, "stopped the process"):
                job_manager.main(self.argv(), stream=io.StringIO())
        # THE INSTALL DOCUMENT NAMES THE JOB AND THE CONFIGURATION DOES NOT:
        # the harmless direction, truthfully recorded.
        named = [one["job_id"] for one in self.install_document()["jobs"]]
        self.assertEqual(named, ["job-a", "job-cli-first"])
        self.assertNotIn("job-cli-first", self.bindings())
        # AND NOTHING WAS SUBMITTED: no Job runs because of a half-published
        # binding. The Job's own task document IS already written -- the
        # reservation cut writes it, which is what makes the operation
        # replayable -- so what absence means here is the SUBMISSION's: no
        # stage row, nothing a scheduler could offer.
        store, creation = self.rows()
        self.assertIsNotNone(creation.job_task_of(store, "job-cli-first"))
        self.assertEqual(self.submitted("job-cli-first"), [])
        # THE SAME COMMAND AGAIN FINISHES IT, without a second entry.
        self.assertIs(bootstrap.prepare, held)
        answered = self.answered()
        self.assertEqual(answered["job_id"], "job-cli-first")
        self.assertEqual(
            [one["job_id"] for one in self.install_document()["jobs"]],
            ["job-a", "job-cli-first"])
        self.assertIn("job-cli-first", self.bindings())

    def test_an_interruption_after_the_binding_is_finished_by_a_rerun(self):
        self.installed()
        from baton_v12.job_manager import creation as operation

        held = operation.submission.submit

        def stopping(*arguments, **named):
            raise RuntimeError("the fixture stopped the process")

        with mock.patch.object(operation.submission, "submit", stopping):
            with self.assertRaisesRegex(RuntimeError, "stopped the process"):
                job_manager.main(self.argv(), stream=io.StringIO())
        # THE BINDING IS PUBLISHED AND NO SUBMISSION IS RECORDED.
        self.assertIn("job-cli-first", self.bindings())
        store, creation = self.rows()
        self.assertEqual(self.submitted("job-cli-first"), [])
        operation.submission.submit = held
        # AND THE SAME COMMAND FINISHES IT, over the published binding.
        answered = self.answered()
        self.assertEqual(answered["job_id"], "job-cli-first")
        self.assertEqual(sorted(self.bindings()), ["job-a", "job-cli-first"])
        self.assertEqual(
            [one["kind"] for one in self.submitted("job-cli-first")],
            ["implementation", "review"])


class TheRefusalsAreTruthful(ConnectedCreationCase):
    """What a creation refuses, and that it leaves nothing behind."""

    def test_an_unsupported_source_selection_refuses(self):
        self.installed()
        refusal, _said = self.refused(source="somewhere-else")
        self.assertIn("source selection is one of 'installed'", str(refusal))
        self.assertNotIn("job-cli-first", self.bindings())
        self.assertEqual(
            [one["job_id"] for one in self.install_document()["jobs"]],
            ["job-a"])

    def test_a_template_this_build_does_not_carry_refuses(self):
        self.installed()
        refusal, _said = self.refused(
            template="baton.v12.job-template.nothing/9")
        self.assertIn("baton.v12.job-template.nothing/9", str(refusal))
        self.assertNotIn("job-cli-first", self.bindings())
        self.assertEqual(
            [one["job_id"] for one in self.install_document()["jobs"]],
            ["job-a"])

    def test_an_override_this_template_does_not_permit_refuses(self):
        """The permitted set is the template's, and it is named in the answer.

        `--provider-turn-seconds` IS permitted, so the refusal this reaches
        for is the value's: a ceiling nothing can mean.
        """
        self.installed()
        refusal, _said = self.refused(provider_turn_seconds=0)
        self.assertNotIn("job-cli-first", self.bindings())
        self.assertEqual(
            [one["job_id"] for one in self.install_document()["jobs"]],
            ["job-a"])
        del refusal

    def test_a_store_that_belongs_to_another_deployment_refuses(self):
        self.installed()
        elsewhere = os.path.join(self.root, "another-jobs.sqlite3")
        argv = self.argv()
        argv[argv.index("--store") + 1] = elsewhere
        said = io.StringIO()
        with self.assertRaises(ContractRefusal) as caught:
            job_manager.main(argv, stream=said)
        self.assertIn("another deployment", str(caught.exception))
        # AND THE STORE IT NAMED WAS NEVER CREATED: the agreement is asked
        # before anything is opened.
        self.assertFalse(os.path.exists(elsewhere))


if __name__ == "__main__":
    unittest.main()
