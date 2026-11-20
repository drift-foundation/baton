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
from types import SimpleNamespace
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
                                  "input-manifest-template": 30,
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


class TheInstallerInputIsOwnedOrRefused(ConnectedCreationCase):
    """W361912 review 2026-10-26T23-51-22Z: custody over the document I added.

    The first version of that write used `_publish`, which renames a `.tmp`
    into place and asks nobody about either name. The reviewer's probe proved
    the three consequences, and these cases are those three plus the retry:

      a regular `install-inputs.json` carrying foreign bytes was OVERWRITTEN
        and the install still published a selector;
      a LINK at the temporary name was followed by the write and then
        promoted onto the real name by the rename;
      and a failure after the write LEFT the document behind, which the
        comment beside it claimed it did not.

    The correction uses the patterns this module already has for the justfile
    and the selector: `custody` refuses a foreign name before any effect, the
    write is exclusive and no-follow with no temporary at all, the identity is
    pinned from the moment the file exists, and the unwind removes it only
    while it is still the file this attempt made.
    """

    def inputs_place(self):
        return os.path.join(self.state, "install-inputs.json")

    def foreign(self, place, body="FOREIGN\n"):
        """Somebody else's bytes, at a name this install derives."""
        Path(os.path.dirname(place)).mkdir(parents=True, exist_ok=True)
        Path(place).write_text(body)
        return place

    def refused_install(self, **members):
        """One install this destination refuses, with its output."""
        document = self.document(**members)
        document.pop("state_root", None)
        inputs = os.path.join(self.root, "operator-inputs.json")
        Path(inputs).write_text(json.dumps(document))
        said = {"command": "baton-v12-stack", "frozen": True,
                "python": "3.13.7", "platform": "Linux", "machine": "x86_64",
                "schema_assets": {"agent-session-1.0": 10,
                                  "input-manifest-template": 30,
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
        return code, out.getvalue()

    def nothing_was_published(self):
        """No selector, no runtime, no justfile: the install had no effect."""
        for name in ("instance.json", "distro", "justfile"):
            self.assertFalse(
                os.path.lexists(os.path.join(self.state, name)), name)

    def no_selector_and_every_effect_retained(self, said):
        """The ending of an install that DID have effects before it refused.

        W376956: `nothing_was_published` is the right question for a refusal
        that comes before any effect, and the wrong one after it. Under the
        selected pre-deletion retention a failure past the copy leaves its own
        runtime and justfile in place, so what has to hold is that no SELECTOR
        was published, that every effect is named as retained, and that the
        report claims no removal.
        """
        self.assertFalse(
            os.path.lexists(os.path.join(self.state, "instance.json")),
            "a selector was published by a refused install")
        for name in ("distro", "justfile"):
            place = os.path.join(self.state, name)
            self.assertTrue(os.path.lexists(place), place)
            self.assertIn("retained " + place, said)
        self.assertIn("RETAINED", said)
        # NO REMOVAL IS CLAIMED ANYWHERE in the output -- not by the cleanup
        # lines and not by the refusal. ("Nothing was deleted." belongs to the
        # OSError refusal `main` prints; these cases end in a BootstrapRefusal
        # with its own sentence, so the property is asserted on the absence of
        # a removal claim rather than on that one pointer.)
        self.assertNotIn("unwound", said)
        self.assertNotIn("could not remove", said)

    def test_a_foreign_regular_input_document_is_refused_untouched(self):
        self.foreign(self.inputs_place())
        code, said = self.refused_install()
        self.assertEqual(code, 2, said)
        self.assertIn("install-inputs.json", said)
        self.assertEqual(Path(self.inputs_place()).read_text(), "FOREIGN\n")
        self.nothing_was_published()

    def test_a_link_at_the_input_name_is_refused_and_its_target_survives(self):
        target = self.foreign(os.path.join(self.root, "elsewhere.json"))
        Path(os.path.dirname(self.inputs_place())).mkdir(parents=True,
                                                         exist_ok=True)
        os.symlink(target, self.inputs_place())
        code, said = self.refused_install()
        self.assertEqual(code, 2, said)
        self.assertTrue(os.path.islink(self.inputs_place()))
        self.assertEqual(Path(target).read_text(), "FOREIGN\n")
        self.nothing_was_published()

    def test_a_dangling_link_at_the_input_name_is_refused(self):
        Path(self.state).mkdir(parents=True, exist_ok=True)
        os.symlink(os.path.join(self.root, "nothing-here.json"),
                   self.inputs_place())
        code, said = self.refused_install()
        self.assertEqual(code, 2, said)
        self.assertTrue(os.path.islink(self.inputs_place()))
        self.assertFalse(os.path.exists(
            os.path.join(self.root, "nothing-here.json")))
        self.nothing_was_published()

    def test_a_link_at_the_temporary_name_is_refused_and_not_followed(self):
        """The reviewer's second consequence, closed twice over.

        `custody` refuses this name, and the write that used to follow it does
        not exist any more -- the document is created exclusively at its own
        name with no rename. So the foreign target survives and nothing is
        promoted onto the real name.
        """
        target = self.foreign(os.path.join(self.root, "temporary-target.json"))
        Path(self.state).mkdir(parents=True, exist_ok=True)
        os.symlink(target, os.path.join(self.state,
                                        "install-inputs.json.partial"))
        code, said = self.refused_install()
        self.assertEqual(code, 2, said)
        self.assertEqual(Path(target).read_text(), "FOREIGN\n")
        self.assertFalse(os.path.lexists(self.inputs_place()))
        self.nothing_was_published()

    def test_a_selector_failure_RETAINS_what_this_attempt_made(self):
        """The third consequence: the cleanup now covers the input document.

        W376956: AND COVERING IT MEANS RETAINING AND NAMING IT. This case read
        `..._removes_only_what_this_attempt_made` and asserted
        `unwound <input document>`, the absent runtime and a SUCCEEDING retry.
        The owner selected pre-deletion fail-closed retention instead --
        `unlinkat` names an entry and never an inode, so the destructive call
        cannot be bound to the object the ownership proof was about -- and
        under it the input document is kept, named, and the destination stays
        occupied so the retry refuses. The name moved with the behaviour
        because a case whose title asserts a removal that no longer happens is
        worse than a red one.

        This is the FOURTH file of this outcome. The three pinned ones were
        converted in earlier claims; these two cases are the same conversion
        in the suite that drives `main` end to end, and they were red until
        now.
        """
        from tools import instance as instances

        def refusing(place, selector):
            raise instances.InstanceRefusal("the fixture refuses the selector")

        with mock.patch.object(instances, "create", refusing):
            code, said = self.refused_install()
        self.assertEqual(code, 2, said)
        # THE INPUT DOCUMENT IS THIS ATTEMPT'S, AND IT STAYS, named as ours.
        self.assertIn("retained " + self.inputs_place(), said)
        self.assertIn("this attempt made the installer input document", said)
        self.assertTrue(os.path.isfile(self.inputs_place()))
        # NO HALF INSTALL IS PUBLISHED: no selector, and the runtime and
        # justfile that were made are named rather than deleted.
        self.no_selector_and_every_effect_retained(said)
        # AND THE RETRY REFUSES THE OCCUPIED DESTINATION, naming what is
        # there. That is what retention means operationally: a failed attempt
        # does not clear the ground for the next one, and nothing repairs or
        # replaces the residue.
        code, again = self.refused_install()
        self.assertEqual(code, 2, again)
        self.assertIn("already", again)
        self.assertTrue(os.path.isfile(self.inputs_place()))

    def test_an_input_replaced_during_the_failure_is_left_alone(self):
        """A path is not an identity, and the unwind knows the difference.

        The document is REPLACED between its creation and the failure, so the
        file this attempt made is gone and somebody else's is at that name.
        Removing it would be this attempt deleting bytes it did not write.
        """
        from tools import instance as instances

        def refusing(place, selector):
            # RENAMED OVER, not rewritten in place: a file created and then
            # unlinked at the same path can be handed the same inode back,
            # and then "replaced" would be indistinguishable from "ours".
            # The replacement is allocated before the original is gone.
            beside = self.inputs_place() + ".somebody-else"
            Path(beside).write_text("SOMEBODY ELSE\n")
            os.replace(beside, self.inputs_place())
            raise instances.InstanceRefusal("the fixture refuses the selector")

        with mock.patch.object(instances, "create", refusing):
            code, said = self.refused_install()
        self.assertEqual(code, 2, said)
        self.assertEqual(Path(self.inputs_place()).read_text(),
                         "SOMEBODY ELSE\n")
        self.assertIn("no longer the installer input document", said)
        # W376956: THEIR BYTES SURVIVE EITHER WAY, and now by construction:
        # the cleanup makes no removal at all, so there is no window for a
        # replacement to be deleted in. The identity check that used to be the
        # protection still runs, and what it decides is which of the three
        # things the report SAYS about the path -- not whether it is deleted.
        self.assertIn("not this attempt's", said)
        self.no_selector_and_every_effect_retained(said)

    def test_a_stale_tmp_link_cannot_be_followed_because_none_is_used(self):
        """The reviewer's exact second setup, and why it is now inert.

        Their probe put a LINK at `install-inputs.json.tmp` -- the name
        `_publish` renames from -- and the write followed it. That name is not
        used by anything now: the document is created exclusively at its own
        name. So this install SUCCEEDS with the link untouched, which is a
        stronger answer than refusing it would be.
        """
        target = self.foreign(os.path.join(self.root, "tmp-target.json"))
        Path(self.state).mkdir(parents=True, exist_ok=True)
        os.symlink(target, self.inputs_place() + ".tmp")
        self.installed()
        self.assertEqual(Path(target).read_text(), "FOREIGN\n")
        self.assertTrue(os.path.isfile(self.inputs_place()))
        self.assertFalse(os.path.islink(self.inputs_place()))
        # AND THE CREATION OVER IT STILL WORKS.
        self.assertEqual(self.answered()["job_id"], "job-cli-first")

    def test_a_successful_install_owns_the_document_it_wrote(self):
        """And it is a regular file this install created, not a link."""
        self.installed()
        place = self.inputs_place()
        self.assertTrue(os.path.isfile(place))
        self.assertFalse(os.path.islink(place))
        # NO TEMPORARY IS LEFT, because none is used.
        self.assertFalse(os.path.lexists(place + ".partial"))
        self.assertFalse(os.path.lexists(place + ".tmp"))
        # AND A SECOND INSTALL INTO THE SAME DESTINATION IS REFUSED, naming
        # what it would have replaced rather than replacing it.
        code, said = self.refused_install()
        self.assertEqual(code, 2, said)
        self.assertTrue(os.path.isfile(place))


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

    def test_a_created_job_carries_the_verification_it_named(self):
        """W321608: through the real command and the real install, two
        defined Jobs on one installed task -- one naming its own verification,
        one not -- each receive their intended instructions and verification;
        nothing of the installation was written per Job."""
        self.installed()
        before = Path(self.owned["configuration"]).read_bytes() \
            if "configuration" in self.owned else None
        self.answered()
        argv = self.argv(task="cli-verified", statement="The verified task.")
        argv += ["--verification", "python3", "--verification=-c",
                 "--verification", "raise SystemExit(3)"]
        said = io.StringIO()
        self.assertEqual(job_manager.main(argv, stream=said), 0,
                         said.getvalue())
        answer = json.loads(said.getvalue())
        store, creation = self.rows()
        verified = json.loads(creation.job_task_of(store, "job-cli-verified"))
        plain = json.loads(creation.job_task_of(store, "job-cli-first"))
        self.assertEqual(verified["verification"],
                         ["python3", "-c", "raise SystemExit(3)"])
        self.assertEqual(plain["verification"],
                         ["python3", "-c", "raise SystemExit(0)"])
        self.assertIn("The verified task.", verified["instructions"])
        self.assertNotEqual(verified["instructions"], plain["instructions"])
        self.assertEqual(answer["job_id"], "job-cli-verified")
        self.assertEqual(sorted(self.bindings()),
                         ["job-a", "job-cli-first", "job-cli-verified"])
        # THE SAME COMMAND AGAIN CONVERGES; another verification is refused.
        said = io.StringIO()
        self.assertEqual(job_manager.main(argv, stream=said), 0)
        self.assertEqual(json.loads(said.getvalue())["job_id"],
                         "job-cli-verified")
        changed = argv[:-1] + ["raise SystemExit(4)"]
        with self.assertRaises(ContractRefusal):
            job_manager.main(changed, stream=io.StringIO())
        del before

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


class TheReusableInstanceServesDefinedJobs(ConnectedCreationCase):
    """W321608: the complete supported path from reusable product
    configuration to a reusable instance, then two ordinary Jobs.

    Instance-only install with its repositories prepared (no worker, no Job,
    the source commit named once) -> two workers composed by `pool
    compose-worker` from this build's own documents plus ordinary operator
    configuration -> the one-operand repeat bootstrap that configures them
    AND clones their sources from the instance's own target -> two `manager
    create` invocations with distinct instructions and verification. No
    dossier document, no hand-sealed manifest, no per-Job installation, and
    no fixture effect on the filesystem: the only stand-in is the `git`
    process boundary, whose every call is asserted. CREATION is what this
    proves; the Jobs are not run here.
    """

    BASE = "a" * 40
    SOURCE = "/srv/the-owners-source"

    def git(self, issued):
        def runner(argv, **named):
            issued.append(list(argv))
            if argv[1] == "clone":
                place = Path(argv[-1])
                (place / "objects" / "info").mkdir(parents=True, exist_ok=True)
                (place / "refs").mkdir(parents=True, exist_ok=True)
                (place / "HEAD").write_text("ref: refs/heads/main\n")
                return SimpleNamespace(returncode=0, stdout="", stderr="")
            if "rev-parse" in argv and "--verify" not in argv:
                return SimpleNamespace(returncode=0, stdout=argv[2],
                                       stderr="")
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return runner

    def installed_with_repositories(self, issued):
        # THE CHECKPOINT PROFILE IS THE DETERMINISTIC SEAM every connected
        # serving case uses (`test_connected_startup`, `test_job_task_delivery`):
        # the line is materialized without version control, so dispatch is
        # proved up to the engine boundary and no git process runs.
        from tests.job_manager.test_review_driver import Profile
        self.profile_seam = Profile()
        document = self.document(workers=[], jobs=[],
                                 line_declared_base=self.BASE,
                                 canonical_target_id=self.BASE,
                                 checkpoint_profile=self.profile_seam.name)
        document.pop("state_root", None)
        inputs = os.path.join(self.root, "operator-inputs.json")
        Path(inputs).write_text(json.dumps(document))
        said = {"command": "baton-v12-stack", "frozen": True,
                "python": "3.13.7", "platform": "Linux", "machine": "x86_64",
                "schema_assets": {"agent-session-1.0": 10,
                                  "input-manifest-template": 30,
                                  "worker-control-1.0": 20},
                "native_rpds": str(Path(self.stand_in_runtime())
                                   / "_internal" / "lib.so")}
        out = io.StringIO()
        with mock.patch.object(
                bootstrap, "_identity_of",
                lambda command, runtime=None, distro=None: said):
            code = bootstrap.main(
                ["--inputs", inputs, "--destination", self.state,
                 "--distro", self.stand_in_runtime(),
                 "--repository-source", self.SOURCE],
                stream=out, runner=self.git(issued))
        self.assertEqual(code, 0, out.getvalue())
        self.owned = instance_identity(self.state)
        with ControlStore.open(self.owned["control_store"],
                               incarnation="manager-1",
                               clock=lambda: "2026-09-02T00:00:00.000Z"):
            pass

    def test_two_defined_jobs_run_on_one_product_configured_instance(self):
        from tools import pool
        from baton_v12.worker_manager import source_boundary

        issued = []
        self.installed_with_repositories(issued)
        before = self.configuration()
        self.assertEqual(before["workers"], [])
        self.assertEqual([one[-1] for one in issued if one[1] == "clone"],
                         [os.path.join(self.state, "repo", "target.git"),
                          os.path.join(self.state, "repo", "workspace")])
        # THE INSTALLED TASK DOCUMENT is ordinary configuration: one file the
        # operator places inside the instance.
        task_place = os.path.join(self.state, "state", "task",
                                  "installed-task.json")
        os.makedirs(os.path.dirname(task_place), exist_ok=True)
        held = json.loads(Path(self.config["task_document"]).read_bytes())
        held["task_id"] = "installed-task"
        Path(task_place).write_bytes(json.dumps(held, sort_keys=True).encode())
        record_path = ("work/records/2026/08/finding-v12-work-tags/findings/"
                       "finding-v12-work-label-protocol-cli")
        record = Path(self.checkout, record_path)
        record.mkdir(parents=True, exist_ok=True)
        (record / "FINDING.md").write_text("# Finding\n")
        (record / "PLAN.md").write_text("# Plan\n")
        workers = []
        for worker_id, role, participant in (
                ("impl-a", "implementation", "baton.impl-a"),
                ("review-a", "review", "baton.reviewer")):
            answer = pool.composed(
                before, worker_id=worker_id, role=role,
                participant=participant,
                image_reference="baton-v12-worker:test",
                image_digest=self.config["image_digest"],
                cli_build="2.1.247", network=self.config["network"],
                credential_sources=os.path.join(self.root,
                                                "credential-sources.json"),
                credentials=["claude=operator-file:w202663-development"],
                workspace_group=self.config["workspace_group"],
                task_document=task_place, record_path=record_path,
                checkout=self.checkout,
                # M385234: the native path selects the image's marker; the
                # verb writes nothing without an explicit selection.
                verifier_layout=source_boundary.image_layout_marker())
            manifest = answer["worker"]["deployment"]["input_manifest"]
            # PROVENANCE IS THIS INSTANCE'S (review 2026-11-19T06-06-42Z).
            self.assertEqual(manifest["record_binding"]["path"], record_path)
            self.assertEqual(manifest["retention_policy_digest"],
                             before["retention_policy_digest"])
            from baton_v12.contracts import frozen
            from tools import next_run_bindings
            template = frozen.input_manifest_template()
            for name in next_run_bindings.BOUND_MEMBERS:
                self.assertNotEqual(manifest[name], template[name], name)
            workers.append(answer["worker"])
        for worker in workers:
            self.assertFalse(os.path.exists(
                worker["deployment"]["nominated_source"]))
        # THE ONE-OPERAND REPEAT: the instance document, its state_root, the
        # derived selections it already holds, and the two composed workers.
        # It clones each worker's source from the instance's own target.
        carried = {name: before[name]
                   for name in ("integration_target", "integration_workspace")
                   if before.get(name)}
        document = self.document(workers=workers, jobs=[],
                                 checkpoint_profile=self.profile_seam.name,
                                 line_declared_base=self.BASE,
                                 canonical_target_id=self.BASE, **carried)
        updated = os.path.join(self.root, "updated-inputs.json")
        Path(updated).write_text(json.dumps(document))
        mark = len(issued)
        said = io.StringIO()
        self.assertEqual(bootstrap.main(
            ["--inputs", updated, "--repository-source", self.SOURCE],
            stream=said, runner=self.git(issued)), 0, said.getvalue())
        target = os.path.join(self.state, "repo", "target.git")
        self.assertEqual(
            [one for one in issued[mark:] if one[1] == "clone"],
            [["git", "clone", "--no-local", target,
              os.path.join(self.state, "repo", "source-impl-a")],
             ["git", "clone", "--no-local", target,
              os.path.join(self.state, "repo", "source-review-a")]])
        self.assertIn(["git", "-C", target, "cat-file", "-e",
                       self.BASE + "^{commit}"], issued[mark:])
        for worker in workers:
            self.assertTrue(os.path.isdir(
                worker["deployment"]["nominated_source"]))
        after = self.configuration()
        self.assertEqual([one["worker_id"] for one in after["workers"]],
                         ["impl-a", "review-a"])
        self.assertEqual(after["workers"][0]["deployment"]["profile_name"],
                         "claude-fresh-implementation")
        # AND THE ROOTS A MANAGER STARTS IN EXIST (review 2026-11-19T05-23-45Z):
        # the manager's own workspace check accepts the configured store.
        from baton_v12.worker_manager import workspaces

        self.assertEqual(bootstrap.prerequisite_report(document), [])
        for worker in after["workers"]:
            for name in bootstrap.PREREQUISITE_ROOTS:
                self.assertTrue(os.path.isdir(worker["deployment"][name]),
                                name)
        workspaces.check_workspace_storage(
            after["workers"][0]["deployment"]["workspace_storage"],
            physical=False)
        # THE REAL MANAGER COMPOSITION STARTS IDLE OVER THIS INSTANCE (review
        # 2026-11-19T05-33-40Z): configured capacity, zero bound Jobs, no
        # receipt session minted, honest zeros from a real sweep and status,
        # and not one engine call.
        from baton_v12.job_manager import JobStore, reconcile, status, sweep
        from baton_v12.worker_manager import ControlStore
        from tests.job_manager import fixtures
        from tests.tools.test_single_worker import Engine
        from tools import stage_execution

        profile_seam = self.profile_seam

        def composed_now():
            engine = Engine()
            job_store = JobStore.open(self.owned["job_store"],
                                      authority_uuid=self.owned["authority_uuid"],
                                      incarnation="idle-proof",
                                      clock=lambda: fixtures.NOW)
            self.addCleanup(job_store.close)
            control = ControlStore.open(self.owned["control_store"],
                                        incarnation="idle-proof",
                                        clock=lambda: fixtures.NOW)
            self.addCleanup(control.close)
            composed = stage_execution.operations_from(
                self.configuration(), job_store, control, engine_run=engine,
                credential_provider=lambda provider, reference: "a-secret",
                clock=lambda: fixtures.NOW, checkout=self.checkout,
                checkpoint_profile=profile_seam)
            self.addCleanup(composed.close)
            return job_store, composed, engine

        job_store, idle, engine = composed_now()
        self.assertIsNone(idle.sessions)
        report = sweep(job_store, idle, now=fixtures.NOW)
        self.assertEqual(report.get("acts", []), [])
        self.assertEqual(status(job_store, idle,
                                observed_at=fixtures.NOW)["jobs"], [])
        self.assertEqual(engine.vectors, [])
        idle.close()
        job_store.close()
        # AN EXPLICIT ROUTE NO CONFIGURED IMPLEMENTATION WORKER HANDLES IS
        # REFUSED BEFORE ANY WORK OR JOB EXISTS (W321608, native-labels-3):
        # the first create on an idle instance makes the derived Work, and a
        # Work on an unhandled route could never be claimed.
        from baton_v12.authority.api import Authority

        def authority():
            opened = Authority.open_readonly(
                self.owned["authority_store"],
                expected_authority_uuid=self.owned["authority_uuid"])
            self.addCleanup(opened.dispose)
            return opened

        workers = {one["worker_id"]: one
                   for one in self.configuration()["workers"]}
        derived = (workers["impl-a"]["deployment"]["input_manifest"]
                   ["work_ref"]["work_id"])
        unserved = self.argv(task="labels-zero", statement="Never created.")
        unserved += ["--route", "baton.impl"]
        with self.assertRaises(ContractRefusal) as caught:
            job_manager.main(unserved, stream=io.StringIO())
        self.assertIn("baton.impl", caught.exception.message)
        self.assertIn("baton.impl-a", caught.exception.message)
        self.assertIsNone(authority().work_creation(derived))
        self.assertEqual(self.bindings(), {})
        self.assertEqual(self.install_document().get("jobs") or [], [])
        # TWO ORDINARY JOBS, input-only, each with its own instructions and
        # its own verification; the installation is not written per Job.
        configured = json.dumps(self.configuration()["workers"],
                                sort_keys=True)
        first = self.argv(task="labels-one", statement="The first slice.")
        first += ["--verification", "python3", "--verification=-c",
                  "--verification", "raise SystemExit(1)"]
        second = self.argv(task="labels-two", statement="The second slice.")
        second += ["--verification", "python3", "--verification=-c",
                   "--verification", "raise SystemExit(2)"]
        for argv in (first, second):
            said = io.StringIO()
            self.assertEqual(job_manager.main(argv, stream=said), 0,
                             said.getvalue())
        store, creation = self.rows()
        one = json.loads(creation.job_task_of(store, "job-labels-one"))
        two = json.loads(creation.job_task_of(store, "job-labels-two"))
        self.assertIn("The first slice.", one["instructions"])
        self.assertIn("The second slice.", two["instructions"])
        self.assertEqual(one["verification"],
                         ["python3", "-c", "raise SystemExit(1)"])
        self.assertEqual(two["verification"],
                         ["python3", "-c", "raise SystemExit(2)"])
        self.assertEqual(sorted(self.bindings()),
                         ["job-labels-one", "job-labels-two"])
        bound = self.bindings()["job-labels-one"]
        self.assertEqual(bound["line_declared_base"], self.BASE)
        self.assertEqual(bound["source_worker_id"], "impl-a")
        self.assertEqual(json.dumps(self.configuration()["workers"],
                                    sort_keys=True), configured)
        self.assertEqual(
            {one["job_id"] for one in self.install_document()["jobs"]},
            {"job-labels-one", "job-labels-two"})
        # THE DERIVED WORK WAS CREATED ON THE DEPLOYMENT'S OWN IMPLEMENTATION
        # ROUTE -- the one its bootstrap registered impl-a on -- and the
        # review handoff route the implementation worker carries resolves to
        # the configured reviewer, so stage two does not meet the same
        # mismatch. The old fixture spelling resolves to nobody here.
        held = authority()
        self.assertEqual(held.project_work(derived)["route"],
                         bootstrap.ROUTES["implementation"])  # "impl"
        self.assertTrue(held.handles_route(bootstrap.ROUTES["implementation"],
                                           "baton.impl-a"))
        self.assertEqual(workers["impl-a"]["deployment"]["review_route"],
                         bootstrap.ROUTES["review"])
        self.assertTrue(held.handles_route(
            workers["impl-a"]["deployment"]["review_route"], "baton.reviewer"))
        self.assertFalse(held.handles_route("baton.impl", "baton.impl-a"))
        # AND THE BOUND WORK IS AUTHORIZED BEFORE ANYTHING IS SERVED: the
        # same composition over the configuration that now binds the two Jobs
        # mints the receipt sessions in the bound Work's own scope (the
        # grants the creation made), and status shows the two queued Jobs.
        job_store, bound, engine = composed_now()
        self.assertIsNotNone(bound.sessions)
        for name in stage_execution.RECEIPT_SESSIONS:
            self.assertIn(name, bound.sessions, name)
        shown = status(job_store, bound, observed_at=fixtures.NOW)
        self.assertEqual(sorted(one["job_id"] for one in shown["jobs"]),
                         ["job-labels-one", "job-labels-two"])
        self.assertEqual(engine.vectors, [])
        # ONE REAL SWEEP CLAIMS THE FIRST JOB'S IMPLEMENTATION THROUGH THE
        # AUTHORITY -- the claim native-labels-3 refused -- and dispatches it
        # once through the deterministic engine; the next sweep over the same
        # state dispatches nothing again.
        from tests.tools.test_single_worker import launching

        def implementation_stages():
            return {one["job_id"]: stage
                    for one in status(job_store, bound,
                                      observed_at=fixtures.NOW)["jobs"]
                    for stage in one["stages"]
                    if stage["kind"] == "implementation"}

        # The scheduler reaches a launch over a few ticks (offer, claim,
        # allocation, writer, dispatch), as `test_connected_startup.driven`
        # drives it; this stops at the first launch and bounds the rounds.
        reports = []
        for _ in range(16):
            reconcile(job_store, bound, now=fixtures.NOW)
            reports.append(sweep(job_store, bound, now=fixtures.NOW))
            if any(launching(one) for one in engine.vectors):
                break
        launched = [one for one in engine.vectors if launching(one)]
        self.assertEqual(len(launched), 1,
                         (engine.vectors, implementation_stages(), reports))
        stages = implementation_stages()
        for job_id, stage in stages.items():
            self.assertNotIn("does not resolve",
                             json.dumps(stage.get("deferral") or []), job_id)
        # ONE JOB IS RUNNING ON THE ONE IMPLEMENTATION WORKER (`waiting`, the
        # state `test_connected_startup.driven` drives to) and the other is
        # honestly queued behind it, not refused and not dispatched.
        self.assertEqual({job_id: stage["state"]
                          for job_id, stage in stages.items()},
                         {"job-labels-one": "waiting",
                          "job-labels-two": "queued"}, stages)
        dispatched = ["job-labels-one"]
        for _ in range(4):
            reconcile(job_store, bound, now=fixtures.NOW)
            sweep(job_store, bound, now=fixtures.NOW)
        self.assertEqual(len([one for one in engine.vectors if launching(one)]),
                         1, engine.vectors)
        self.assertEqual(implementation_stages()[dispatched[0]]["state"],
                         stages[dispatched[0]]["state"])
        bound.close()
        job_store.close()
        # A BOUND WORK WHOSE RECEIPT ACTOR HOLDS NO GRANT REFUSES AT
        # COMPOSITION, before any dispatch or publication: the implementation
        # participant is a real participant and holds no verify capability.
        configured = self.configuration()
        configured["receipt_participants"]["verification"] = "baton.impl-a"
        job_store = JobStore.open(self.owned["job_store"],
                                  authority_uuid=self.owned["authority_uuid"],
                                  incarnation="grant-proof",
                                  clock=lambda: fixtures.NOW)
        self.addCleanup(job_store.close)
        control = ControlStore.open(self.owned["control_store"],
                                    incarnation="grant-proof",
                                    clock=lambda: fixtures.NOW)
        self.addCleanup(control.close)
        engine = Engine()
        with self.assertRaises(ContractRefusal) as caught:
            stage_execution.operations_from(
                configured, job_store, control, engine_run=engine,
                credential_provider=lambda provider, reference: "a-secret",
                clock=lambda: fixtures.NOW, checkout=self.checkout,
                checkpoint_profile=profile_seam)
        self.assertIn("verify", caught.exception.message)
        self.assertIn("baton.impl-a", caught.exception.message)
        self.assertEqual(engine.vectors, [])


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


class CreateTimeWorkLabelsThroughTheRealCommand(ConnectedCreationCase):
    """W29401: `manager create --label`, against a really installed instance.

    THE TWO DIRECTIONS THIS INSTALL MAKES REAL. The ordinary fixture's
    bootstrap already created this deployment's Work (for `job-a`), so an
    ordinary creation REUSES it -- which is the case that must refuse rather
    than relabel somebody else's Work. An install that names no Job has no
    Work yet, so the creation MAKES it, and that is where create-time labels
    are applied.

    AND THE TWO COMMANDS COMPOSE. The labels a reused Work is missing are
    added by `baton-v12-stack work label-work` against this instance's own
    Authority store -- the real command, the real deployment -- after which
    the same creation converges. That is the workflow the refusal's own
    sentence tells an operator to use.
    """

    def labelled(self, *labels, **named):
        """One creation that also states Work labels, as argv."""
        argv = self.argv(**named)
        for one in labels:
            argv += ["--label", one]
        return argv

    def made(self, argv):
        """One creation this command performs, as its parsed answer.

        ITS OWN ENTRY RATHER THAN THE BASE HELPER'S, because `created`
        composes the argument list from keywords and `--label` is repeatable:
        a keyword cannot carry two of them.
        """
        said = io.StringIO()
        code = job_manager.main(argv, stream=said)
        self.assertEqual(code, 0, said.getvalue())
        return json.loads(said.getvalue())

    def stopped(self, argv):
        """One creation this command refuses, as the typed refusal it is.

        A `ContractRefusal` reaches the caller rather than becoming an exit
        code, which is this CLI's shape for every command -- see `refused` on
        the base case.
        """
        with self.assertRaises(ContractRefusal) as caught:
            job_manager.main(argv, stream=io.StringIO())
        return caught.exception

    def authority(self, *, writable=False):
        """This instance's OWN Authority, read the way a verb reads it."""
        from baton_v12.authority import Authority

        opener = Authority.open if writable else Authority.open_readonly
        held = opener(self.owned["authority_store"],
                      expected_authority_uuid=self.owned["authority_uuid"])
        self.addCleanup(held.dispose)
        return held

    def work_verb(self, *operands):
        """The installed `work` subcommand, over this instance's own
        Authority: the real command against the real deployment."""
        from tools import work_command

        said = io.StringIO()
        with mock.patch("sys.stdout", said):
            code = work_command.main(
                list(operands) + ["--authority-store",
                                  self.owned["authority_store"],
                                  "--authority-uuid",
                                  self.owned["authority_uuid"]])
        return code, said.getvalue()

    def test_an_unlabelled_creation_is_exactly_what_it_was(self):
        """THE PRESERVED PATH, and the additive member in the answer."""
        self.installed()
        held = self.made(self.argv())
        self.assertEqual(held["work"]["state"], "reused")
        self.assertEqual(held["work"]["requested_labels"], [])
        self.assertEqual(self.authority().labels_of(self.work), [])
        self.assertEqual(self.authority().work_label_events(self.work), [])
        code, said = self.work_verb("labels", "--work", self.work)
        self.assertEqual(code, 0, said)
        self.assertEqual(json.loads(said)["labels"], [])

    def test_a_creation_that_makes_the_work_applies_its_labels(self):
        """An install that names no Job has no Work, so this creation makes
        it -- and it is created carrying the normalized labels, in the act
        that made it.

        THIS FIXTURE'S CREATION THEN STOPS AT ITS BINDING, because an install
        with no Job emits no `job_bindings` for `prepare` to publish into.
        That is a property of a Job-less install and not of this option: what
        it demonstrates is the thing `_incomplete` promises, since the Work
        and its labels are what the creation had already published.
        """
        self.installed(jobs=[], line_declared_base="a" * 40,
                       canonical_target_id="target-1")
        refusal = self.stopped(self.labelled("Release-Foo", "V12"))
        self.assertIn("is RESERVED", str(refusal))
        authority = self.authority()
        self.assertEqual(authority.labels_of(self.work),
                         ["release-foo", "v12"])
        # ONE INSTANT AND ONE ACT: every label event is the creation's own.
        self.assertEqual(
            [(one["label"], one["act"]) for one
             in authority.work_label_events(self.work)],
            [("release-foo", "work-create"), ("v12", "work-create")])
        self.assertEqual(authority.works_with_labels(all_of=["v12"]),
                         [self.work])
        # AND THE RECORD NAMES THIS CREATION (W385292): the Authority says
        # which creation minted the Work, which is what lets the same request
        # -- and only it -- reuse the Work with its labels.
        from baton_v12.job_manager import creation as creating
        self.assertEqual(
            authority.work_creation(self.work)["operation_id"],
            creating.work_operation_id("job-cli-first", self.work))
        # AND THE SAME REQUEST AGAIN REACHES THE SAME PLACE rather than
        # refusing about labels the Work already carries.
        again = self.stopped(self.labelled("Release-Foo", "V12"))
        self.assertIn("is RESERVED", str(again))
        self.assertNotIn("work label-work", str(again))
        self.assertEqual(authority.labels_of(self.work),
                         ["release-foo", "v12"])

    def test_a_creation_that_reuses_a_work_refuses_to_relabel_it(self):
        self.installed()
        refusal = self.stopped(self.labelled("v12"))
        self.assertIn("would reuse the existing Work", str(refusal))
        self.assertIn("was not made by this creation", str(refusal))
        # AND WHOSE IT IS: the bootstrap's own creation record, by name.
        self.assertIn("it was made by the operation `bootstrap-job-a`",
                      str(refusal))
        self.assertIn("work label-work", str(refusal))
        # AND NOTHING WAS RESERVED (W385292): the identity stays free for the
        # creation the guidance names.
        self.assertIn("Nothing was reserved by this request", str(refusal))
        self.assertNotIn("is RESERVED", str(refusal))
        # NOTHING WAS MUTATED ON THE SHARED WORK, and no Job was submitted.
        authority = self.authority()
        self.assertEqual(authority.labels_of(self.work), [])
        self.assertEqual(authority.work_label_events(self.work), [])
        self.assertNotIn("job-cli-first", self.bindings())
        self.assertEqual(self.submitted("job-cli-first"), [])

    def test_the_work_verb_is_how_a_reused_works_labels_are_added(self):
        """The refusal's own guidance, carried out through the real command."""
        self.installed()
        self.stopped(self.labelled("v12"))
        self.authority(writable=True).grant_capability(
            "baton.slaw", "manage-work-labels")
        code, said = self.work_verb(
            "label-work", "--participant", "baton.slaw",
            "--work", self.work, "--operation-id", "labels-1",
            "--label", "V12")
        self.assertEqual(code, 0, said)
        answer = json.loads(said)
        self.assertEqual(answer["changed"], ["v12"])
        self.assertEqual(answer["acts"][0]["decision"]["role"],
                         "manage-work-labels")
        # AND THE SAME LABELLED CREATION STILL REFUSES (W385292): the Work
        # now carries exactly what it asks for, and it is still not the Work
        # this creation made. Without --label it reuses the Work as always,
        # and the label the authorized act added is what `list` finds.
        again = self.stopped(self.labelled("v12"))
        self.assertIn("was not made by this creation", str(again))
        self.assertEqual(self.authority().labels_of(self.work), ["v12"])
        held = self.made(self.argv())
        self.assertEqual(held["work"]["state"], "reused")
        self.assertEqual(held["work"]["requested_labels"], [])
        self.assertIn("job-cli-first", self.bindings())
        code, said = self.work_verb("list", "--label", "v12")
        self.assertEqual(json.loads(said)["work"], [self.work])

    def minted_under(self, job_id, *labels):
        """A Job-less install and one creation under `job_id` that mints the
        Work and stops at its binding: the real command, the real Authority,
        and the Authority's own record of the minting act (W385292
        correction review R1). Each install is one instance, so each Job id
        under test is its own case."""
        from baton_v12.authority import identity as grammar
        from baton_v12.job_manager import creation as creating

        self.installed(jobs=[], line_declared_base="a" * 40,
                       canonical_target_id="target-1")
        refusal = self.stopped(self.labelled(*labels, job_id=job_id))
        self.assertIn("is RESERVED", str(refusal))
        self.assertIn("reported no binding", str(refusal))
        authority = self.authority()
        self.assertEqual(authority.labels_of(self.work), sorted(labels))
        record = authority.work_creation(self.work)
        self.assertEqual(record["operation_id"],
                         creating.work_operation_id(job_id, self.work))
        self.assertIsNone(grammar.opaque_id_fault(record["operation_id"]))
        store, module = self.rows()
        self.assertEqual([one["state"] for one
                          in module.created_job_rows(store)], ["intended"])
        # AND THE SAME REQUEST AGAIN REACHES THE SAME PLACE: the record names
        # this creation, however the Job is spelled.
        again = self.stopped(self.labelled(*labels, job_id=job_id))
        self.assertIn("reported no binding", str(again))
        self.assertNotIn("label-work", str(again))
        self.assertEqual(authority.labels_of(self.work), sorted(labels))
        return record

    def test_a_130_character_job_id_mints_the_work_with_labels(self):
        self.minted_under("j" * 130, "v12")

    def test_a_160_character_job_id_mints_the_work_without_labels(self):
        self.minted_under("j" * 160)

    def test_a_job_id_longer_than_the_opaque_limit_mints_the_work(self):
        self.minted_under("job-" + "x" * 300, "hot", "v12")

    def test_a_job_id_outside_the_opaque_grammar_mints_the_work(self):
        self.minted_under("job/segment", "v12")

    def test_a_job_id_with_a_space_mints_the_work_without_labels(self):
        self.minted_under("job with space")

    def test_distinct_job_ids_mint_under_distinct_identities(self):
        from baton_v12.job_manager import creation as creating

        record = self.minted_under("j" * 130, "v12")
        self.assertNotEqual(record["operation_id"],
                            creating.work_operation_id("j" * 131, self.work))
        self.assertNotEqual(record["operation_id"],
                            creating.work_operation_id("j" * 130,
                                                       "0000000a-W2"))

    def test_the_minting_creations_work_relabelled_since_is_restored_by_the_named_act(
            self):
        """R2 through the real command and the real Authority: the own
        minted Work relabelled by an authorized act, the honest refusal, the
        no-label retry colliding as it warns, and the named act bringing the
        same request back to where it was interrupted."""
        self.installed(jobs=[], line_declared_base="a" * 40,
                       canonical_target_id="target-1")
        self.stopped(self.labelled("v12"))
        self.authority(writable=True).grant_capability(
            "baton.slaw", "manage-work-labels")
        code, said = self.work_verb(
            "label-work", "--participant", "baton.slaw",
            "--work", self.work, "--operation-id", "labels-1",
            "--label", "hot")
        self.assertEqual(code, 0, said)
        again = self.stopped(self.labelled("v12"))
        self.assertIn("this creation minted the Work", str(again))
        self.assertIn("carrying exactly 'v12'", str(again))
        self.assertIn("it now carries 'hot', 'v12'", str(again))
        self.assertIn(f"`baton-v12-stack work unlabel-work --work "
                      f"{self.work} --label hot`", str(again))
        self.assertIn("is RESERVED", str(again))
        self.assertNotIn("was not made by this creation", str(again))
        self.assertNotIn("Nothing was reserved", str(again))
        self.assertNotIn("repeat this creation without --label", str(again))
        collided = self.stopped(self.argv())
        self.assertIn("already recorded with a different kind or signature",
                      str(collided))
        code, said = self.work_verb(
            "unlabel-work", "--participant", "baton.slaw",
            "--work", self.work, "--operation-id", "labels-2",
            "--label", "hot")
        self.assertEqual(code, 0, said)
        self.assertEqual(self.authority().labels_of(self.work), ["v12"])
        third = self.stopped(self.labelled("v12"))
        self.assertIn("reported no binding", str(third))
        self.assertNotIn("label-work", str(third))
        self.assertNotIn("minted the Work", str(third))
        self.assertEqual(self.submitted("job-cli-first"), [])

    def test_two_operands_that_are_one_key_refuse_before_any_effect(self):
        self.installed()
        refusal = self.stopped(self.labelled("v12", "V12"))
        self.assertIn("one label after normalization", str(refusal))
        self.assertEqual(self.authority().labels_of(self.work), [])
        self.assertNotIn("job-cli-first", self.bindings())
        self.assertEqual(
            [one["job_id"] for one in self.install_document()["jobs"]],
            ["job-a"])

    def test_a_malformed_label_refuses_before_any_effect(self):
        self.installed()
        for bad in ("team=core", "v12,hot", "has space", "a" * 65):
            with self.subTest(bad=bad):
                refusal = self.stopped(self.labelled(bad))
                self.assertIn("a Work label is 1 to 64 characters",
                              str(refusal))
        self.assertNotIn("job-cli-first", self.bindings())
        self.assertEqual(
            [one["job_id"] for one in self.install_document()["jobs"]],
            ["job-a"])


if __name__ == "__main__":
    unittest.main()
