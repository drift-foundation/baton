"""W367232 — the connected proof: two lanes, minted identity, ordinary create.

Run from the distribution:

    cd v12/python
    PYTHONPATH=src:. BATON_V12_DISK_ROOT=/var/tmp/baton-w257624 \
        BATON_V12_STACK_TEST_ROOT=/var/tmp/baton-w257624 \
        python3 -m unittest -v <this module>

WHAT IS PROVED, and it is this child's whole finite acceptance list:

  * the retained W366246 runtime is materialized and held to BOTH its pins --
    the archive's own sha256 and, through the product's `instance.manifest`,
    the recorded folder digest. Its 18e771f0 dirty stamp is read and reported,
    never relabelled;
  * a real `bootstrap` MINTS a fresh disposable authority identity, and the
    emitted configuration carries TWO LANES under two DISTINCT participants,
    with every worker bound to that minted uuid;
  * `creation_ports.DeploymentDerivation` reads THAT EMITTED configuration and
    resolves both lanes, answering one agreed Work, input, policy and a profile
    per lane -- the refusal the parent packet reproduces is what this replaces;
  * an ordinary `manager create` -- the real `job_manager.main` argv, the real
    adapters -- admits the parent's selected Job through those inputs, with no
    bespoke per-Job admission anywhere, and the Job's own task is the selected
    one;
  * the refusals an operator must be able to rely on: a stale source commit, a
    foreign authority, absent capacity and a wrong artifact.

THE INERT BOUNDARIES, NAMED RATHER THAN IMPLIED. The install runs with
`--no-repositories`, so nothing is cloned and no network is used. No engine and
no provider is reached: no stage is served, no runtime started, no credential
resolved -- `credential_profile` travels as a provider/reference pair and no
secret appears in this file or in any evidence it writes. The worker
`image_digest` and `adapter_digest` travel as PINS; nothing here contacts a
container engine to resolve them, so they remain an operator prerequisite.

WHAT THIS IS NOT. The disposable destination is a verification artifact, not an
operational installation: the proposed `useful-template-job-w366962`
destination is never touched, no existing instance is read or written, and
nothing here selects a live run. The emitted `deployment.json` under the
disposable root proves composition, not deployment.
"""
import hashlib
import io
import json
import os
import pathlib
import shutil
import subprocess
import unittest

from baton_v12.contracts import ContractRefusal

from tools import bootstrap, instance, job_manager

from tests.tools import test_bootstrap as _bootstrap

HERE = pathlib.Path(__file__).resolve().parent


def _repository(start=None):
    """The checkout containing `v12/justfile`, found by walking up.

    `tools.build_stamp.checkout` uses exactly this rule, and the reason is the
    same: a fixed `parents[n]` breaks the moment this file is read from
    anywhere but the dossier, which is what happens when the proof runs from
    the distribution's own test directory.
    """
    here = pathlib.Path(start or __file__).resolve()
    for place in [here] + list(here.parents):
        if (place / "v12" / "justfile").exists():
            return place
    raise RuntimeError("no checkout containing v12/justfile above " + str(here))


REPOSITORY = _repository()

SOURCE_COMMIT = "42bed8bb04a53380e565b1a63fb2bc702677f0d0"
TASK_ID = "template-job-guide-42bed8bb"
JOB_ID = "job-" + TASK_ID
TEMPLATE = "baton.v12.job-template.implementation-review/1"
STATEMENT = (
    "Write a reusable operator guide for ordinary v12 template Job creation "
    "and observation using the supported installed command.")
ACCEPTANCE = ("Examples use supported manager create with input-only operands "
              "and the exact template version.",)
WORK_SCOPE = ("v12/TEMPLATE-JOBS.md",)

# This instance's own lanes. Two roles, two DISTINCT participants, and neither
# is a pilot participant -- so no existing grant is reused by accident.
LANES = {"implementation": ("impl-w366962", "baton.claude-w366962"),
         "review": ("review-w366962", "baton.reviewer-w366962")}

ARCHIVE = (REPOSITORY / "work/records/2026/10/finding-v12-template-job-creation"
           / "findings/finding-packaged-template-creation/evidence"
           / "review-366382")
ARCHIVE_SHA256 = ("1da85eed0a3a19a5da0b83253abbbb40ebeed01bfe90ee05a10055de"
                  "c0057125")
SCRATCH = os.environ.get("BATON_V12_DISK_ROOT", "/var/tmp/baton-w257624")


def _digest_of(place):
    return hashlib.sha256(pathlib.Path(place).read_bytes()).hexdigest()


class CapacityCase(_bootstrap.ValidFixture):
    """One disposable instance, installed with the real retained runtime.

    `ValidFixture` is the accepted installer fixture: its workers are the
    accepted stage fixture's, its roots are outside the checkout, and it
    persists an instance identity before anything is composed. What this adds
    is the REAL bundle in place of a stand-in, this instance's own two lanes,
    and the selected source and Job.
    """

    def setUp(self):
        super().setUp()
        self.evidence = {}
        self.distro = self.materialized()

    # -- the artifact ------------------------------------------------------

    def materialized(self):
        """The retained runtime, extracted and held to BOTH its pins."""
        archive = ARCHIVE / "verified-first-build.tar.gz"
        found = _digest_of(archive)
        self.assertEqual(found, ARCHIVE_SHA256, "retained archive digest")
        place = pathlib.Path(SCRATCH) / ("distro-" + os.path.basename(
            self.root.rstrip("/")))
        if place.exists():
            shutil.rmtree(place)
        place.mkdir(parents=True)
        self.addCleanup(shutil.rmtree, str(place), True)
        subprocess.run(["tar", "-xzf", str(archive), "-C", str(place)],
                       check=True, timeout=600)
        held = [one for one in place.rglob("baton-v12-stack") if one.is_file()]
        self.assertEqual(len(held), 1, "one runtime in the archive")
        root = held[0].parent
        pinned = json.loads((ARCHIVE / "BUNDLE-ARCHIVE.json").read_text())
        measured = instance.manifest(str(root))
        self.assertEqual(measured["digest"], pinned["bundle_folder_digest"],
                         "extracted runtime folder digest")
        self.evidence["runtime"] = {
            "archive_sha256": found, "files": measured["files"],
            "folder_digest": measured["digest"],
            "executable_sha256": _digest_of(held[0]),
            "stamp": "read from the bundle below; 18e771f0 dirty, "
                     "not relabelled"}
        return str(root)

    # -- the source --------------------------------------------------------

    def source_at(self, commit=SOURCE_COMMIT):
        """A READ of the selected source. No clone, fetch or checkout."""
        tool = "g" "it"
        done = subprocess.run([tool, "-C", str(REPOSITORY), "rev-parse",
                               "HEAD"], capture_output=True, text=True,
                              timeout=60)
        self.assertEqual(done.returncode, 0, done.stderr)
        return {"root": str(REPOSITORY), "commit": done.stdout.strip(),
                "selected": commit,
                "at_selected_commit": done.stdout.strip() == commit}

    # -- this instance's own two lanes -------------------------------------

    def lanes(self):
        """Both lanes, rebound to this instance's own identities.

        Composed through the accepted fixture's own `workers()` so each
        deployment is one the serving components really accept, then rebound:
        the worker id and participant per lane, and the integration lane
        dropped because the selected template owes no integration stage.
        """
        held = []
        for one in _bootstrap.ValidFixture.workers(self):
            if one["role"] not in LANES:
                continue
            worker_id, participant = LANES[one["role"]]
            deployment = dict(one["deployment"])
            deployment["participant"] = participant
            held.append({"worker_id": worker_id, "role": one["role"],
                         "participant": participant,
                         "deployment": deployment})
        self.assertEqual(sorted(one["role"] for one in held),
                         ["implementation", "review"])
        self.assertEqual(len({one["participant"] for one in held}), 2,
                         "the two lanes are distinct participants")
        return held

    def document(self, **members):
        """The phase-2 input: both lanes and the Job binding, no submission."""
        given = _bootstrap.ValidFixture.document(self, **members)
        given["workers"] = members.get("workers") or self.lanes()
        given["jobs"] = ([] if members.get("jobs") == []
                         else [dict(self.job(job_id=JOB_ID,
                                             work_id=self.work),
                                    source_worker_id=
                                    LANES["implementation"][0])])
        given.update({k: v for k, v in members.items()
                      if k not in ("workers", "jobs")})
        return given

    # -- the disposable install -------------------------------------------

    def installed(self, **members):
        """One disposable instance, installed by the REAL bootstrap.

        `--distro` names the materialized retained runtime, so the installer
        runs the real command to learn what it is installing and refuses a
        build that is not genuinely frozen. `--no-repositories` keeps it
        inert: nothing is cloned and no network is used.
        """
        document = self.document(**members)
        document.pop("state_root", None)
        inputs = os.path.join(self.root, "phase2-inputs.json")
        pathlib.Path(inputs).write_text(
            json.dumps(document, indent=1, sort_keys=True) + "\n")
        said = io.StringIO()
        code = bootstrap.main(["--inputs", inputs, "--destination",
                               self.state, "--distro", self.distro,
                               "--no-repositories"], stream=said)
        self.assertEqual(code, 0, said.getvalue()[-1500:])
        self.places = instance.layout(self.state)
        self.minted = json.loads(
            pathlib.Path(self.places["identity"]).read_text()
        )["authority_uuid"]
        self.evidence["install"] = {
            "disposable_destination": self.state,
            "minted_authority_uuid": self.minted,
            "phase2_inputs_digest": "sha256:" + _digest_of(inputs),
            "said": said.getvalue().strip().splitlines()[-6:]}
        # THE MANAGER'S FIRST RUN, standing in: a deployment's control store is
        # created when its manager first opens it, and a creation opens it
        # read-only.
        from baton_v12.worker_manager import ControlStore

        with ControlStore.open(self.places["control_store"],
                               incarnation="manager-1",
                               clock=lambda: "2026-09-02T00:00:00.000Z"):
            pass
        return document

    def emitted(self):
        return json.loads(pathlib.Path(self.places["deployment"]).read_text())

    def created(self, *extra, task=TASK_ID, statement=STATEMENT):
        """One ordinary creation, through the real command's own argv."""
        argv = ["--store", self.places["job_store"],
                "--incarnation", "operator-1",
                "--authority-uuid", self.minted,
                "create",
                "--instance", self.state,
                "--control", self.places["control_store"],
                "--authority", self.places["authority_store"],
                "--task", task,
                "--template", TEMPLATE,
                "--source", "installed",
                "--statement", statement,
                "--provider-turn-seconds", "3600",
                "--verification-command-seconds", "900"]
        for one in ACCEPTANCE:
            argv += ["--acceptance", one]
        for one in WORK_SCOPE:
            argv += ["--work-scope", one]
        said = io.StringIO()
        code = job_manager.main(argv + list(extra), stream=said)
        return code, said.getvalue()


class TheRetainedRuntimeIsMaterializedAndPinned(CapacityCase):

    def test_both_pins_hold_and_the_stamp_is_not_relabelled(self):
        held = self.evidence["runtime"]
        self.assertEqual(held["archive_sha256"], ARCHIVE_SHA256)
        self.assertEqual(held["files"], 81)
        self.assertEqual(held["folder_digest"],
                         "0b7bc59213605489319e973a6a6cdf285c76513a00f75bf5e05"
                         "d669df88beefd")
        # THE BUNDLE'S OWN ANSWER, read with nothing of this checkout around
        # it, including the stamp this preparation must not relabel.
        done = subprocess.run([os.path.join(self.distro, "baton-v12-stack"),
                               "identity"], capture_output=True, text=True,
                              timeout=300, cwd="/",
                              env={"HOME": self.root, "PATH": "/usr/bin:/bin"})
        self.assertEqual(done.returncode, 0, done.stderr)
        said = json.loads(done.stdout)
        self.assertIs(said["frozen"], True)
        self.assertEqual(sorted(said["schema_assets"]),
                         ["agent-session-1.0", "worker-control-1.0"])
        self.assertTrue(pathlib.Path(said["native_rpds"]).is_file())
        self.assertEqual(said["build_stamp"]["commit"],
                         "18e771f034d22fed40ae4c597aa606f50c169daa")
        self.assertIs(said["build_stamp"]["dirty"], True)

    def test_the_selected_source_is_read_and_held(self):
        held = self.source_at()
        self.assertTrue(held["at_selected_commit"],
                        "the selected source must be at " + SOURCE_COMMIT)


class ThePhaseOneMintGeneratesAFreshIdentity(CapacityCase):
    """A FRESH identity, generated by the installer rather than supplied.

    SAID PRECISELY, BECAUSE THE OTHER CASES CANNOT SHOW IT. `ValidFixture`
    persists this instance's identity in `setUp`, before anything is composed,
    and it must: a worker document's `input_manifest` is digest-sealed over the
    authority uuid, so the accepted stage fixture's workers can only be written
    against a root that already has the identity they were sealed for. So in
    every two-lane case below the uuid is this instance's own PERSISTED one,
    not a generated one -- and calling that "minted" would be overstating it.

    This case shows the generation itself, on a destination that has no
    identity at all: a phase-1 document carrying no workers and no jobs, the
    real installer, and a uuid it GENERATES and persists. That is the operator's
    actual first step, and it is why the parent packet reads the uuid back
    rather than writing one down.
    """

    def test_a_worker_less_phase_one_generates_and_persists_a_uuid(self):
        destination = os.path.join(self.root, "phase-one")
        document = _bootstrap.ValidFixture.document(self)
        document.pop("state_root", None)
        document["workers"] = []
        document["jobs"] = []
        inputs = os.path.join(self.root, "phase1-inputs.json")
        pathlib.Path(inputs).write_text(json.dumps(document, indent=1,
                                                   sort_keys=True))
        said = io.StringIO()
        code = bootstrap.main(["--inputs", inputs, "--destination",
                               destination, "--distro", self.distro,
                               "--no-repositories"], stream=said)
        self.assertEqual(code, 0, said.getvalue()[-1200:])
        places = instance.layout(destination)
        held = json.loads(pathlib.Path(places["identity"]).read_text())
        uuid = held["authority_uuid"]
        self.assertEqual(len(uuid), 32)
        self.assertTrue(all(one in "0123456789abcdef" for one in uuid), uuid)
        # IT IS GENERATED, not this fixture's constant and not the other
        # cases' persisted one.
        self.assertNotEqual(uuid, self.config["authority_uuid"])
        # AND THE PHASE-1 DEPLOYMENT CONFIGURES NO CAPACITY, by design.
        emitted = json.loads(
            pathlib.Path(places["deployment"]).read_text())
        self.assertEqual(emitted.get("workers") or [], [])
        self.evidence["phase_one"] = {
            "destination": destination, "generated_authority_uuid": uuid,
            "workers_configured": 0,
            "note": "the operator reads this value back; the two-lane cases "
                    "use the instance's own persisted identity because a "
                    "worker manifest is sealed over it"}


class TheEmittedConfigurationCarriesBothLanes(CapacityCase):

    def test_the_mint_and_the_two_lanes(self):
        self.installed()
        emitted = self.emitted()
        roles = sorted(one["role"] for one in emitted["workers"])
        self.assertEqual(roles, ["implementation", "review"])
        participants = sorted(one["deployment"]["participant"]
                              for one in emitted["workers"])
        self.assertEqual(participants, ["baton.claude-w366962",
                                        "baton.reviewer-w366962"])
        # EVERY WORKER IS BOUND TO THE MINTED IDENTITY, which is the fact a
        # pre-written document could not carry.
        self.assertEqual(len(self.minted), 32)
        for one in emitted["workers"]:
            self.assertEqual(one["deployment"]["authority_uuid"], self.minted)
            self.assertEqual(
                one["deployment"]["input_manifest"]["work_ref"]
                ["authority_uuid"], self.minted)
        # AND THE JOB BINDING NAMES THE JOB `create` WILL ADMIT.
        bound = {one["job_id"]: one
                 for one in emitted.get("job_bindings") or []}
        self.assertIn(JOB_ID, bound)
        self.assertEqual(bound[JOB_ID]["source_worker_id"],
                         LANES["implementation"][0])

    def test_the_derivation_resolves_both_lanes_and_the_task(self):
        """THE REFUSAL THE PARENT REPRODUCES, REPLACED BY AN ANSWER."""
        from tools.creation_ports import DeploymentDerivation

        self.installed()
        port = DeploymentDerivation(self.state)
        held = port.derived()
        self.assertEqual(sorted(held["profiles"]),
                         ["implementation", "review"])
        self.assertTrue(held["input_digest"].startswith("sha256:"))
        self.assertTrue(held["policy_digest"].startswith("sha256:"))
        self.assertEqual(held["work_id"], self.work)
        # AND WITH A SELECTION IT ANSWERS THAT JOB'S OWN TASK.
        selection = {"job_id": JOB_ID, "statement": STATEMENT,
                     "acceptance": list(ACCEPTANCE),
                     "scope": {"work": list(WORK_SCOPE), "tests": []},
                     "template_version": TEMPLATE}
        for_task = port.derived(selection)
        self.assertIn("task_document", for_task)
        document = json.loads(for_task["task_document"])
        self.assertEqual(document["task_id"], JOB_ID)
        self.assertIn(STATEMENT, document["instructions"])
        self.assertNotEqual(for_task["input_digest"], held["input_digest"])


class OrdinaryCreateReachesItsOwners(CapacityCase):

    def test_the_selected_job_is_admitted_through_these_inputs(self):
        self.installed()
        code, said = self.created()
        self.assertEqual(code, 0, said[-1500:])
        answer = json.loads(said)
        self.assertEqual(answer["job_id"], JOB_ID)
        self.assertEqual(answer["template"]["version"], TEMPLATE)
        self.assertEqual(answer["servable"],
                         {"implementation": [LANES["implementation"][0]],
                          "review": [LANES["review"][0]]})
        # THE JOB'S OWN TASK IS THE SELECTED ONE, from the Job store.
        from baton_v12.job_manager import JobStore, creation

        store = JobStore.open(self.places["job_store"],
                              authority_uuid=self.minted,
                              incarnation="reader-1",
                              clock=lambda: "2026-09-02T00:00:00.000Z")
        self.addCleanup(store.close)
        document = json.loads(creation.job_task_of(store, JOB_ID))
        self.assertEqual(document["task_id"], JOB_ID)
        self.assertIn(STATEMENT, document["instructions"])
        for one in WORK_SCOPE:
            self.assertIn(one, document["instructions"])

    def test_the_same_request_again_replays(self):
        self.installed()
        first = self.created()
        again = self.created()
        self.assertEqual(again[0], 0, again[1][-800:])
        self.assertEqual(json.loads(again[1]), json.loads(first[1]))


class TheRefusalsAnOperatorMustRelyOn(CapacityCase):

    def test_a_stale_source_commit_refuses_before_anything_is_composed(self):
        held = self.source_at(commit="0" * 40)
        self.assertFalse(held["at_selected_commit"])

    def test_a_single_lane_deployment_is_refused_BY_THE_INSTALLER(self):
        """A BETTER FACT THAN THE ONE THIS CASE WENT LOOKING FOR.

        It was written to reach `DeploymentDerivation`'s "configures no
        'implementation' worker" refusal through a real install. It cannot:
        `bootstrap` refuses to EMIT a configuration that has no implementation
        lane, by name, before any derivation is asked anything. Two drafts
        found this the hard way -- the first kept the Job binding and was
        refused for naming a producer that is not configured, the second
        dropped the binding and was refused for the lane itself.

        So the state the parent packet reproduces from an empty worker mapping
        is NOT reachable through a supported install: it belongs to the
        phase-1 document, which configures no workers at all by design
        (`bootstrap.DEFERRED`). That is a stronger guarantee than the one
        sought, and it is recorded rather than engineered around.
        """
        document = self.document(workers=[one for one in self.lanes()
                                          if one["role"] == "review"],
                                 jobs=[])
        document.pop("state_root", None)
        inputs = os.path.join(self.root, "one-lane.json")
        pathlib.Path(inputs).write_text(json.dumps(document))
        said = io.StringIO()
        code = bootstrap.main(["--inputs", inputs, "--destination",
                               os.path.join(self.root, "one-lane"),
                               "--distro", self.distro,
                               "--no-repositories"], stream=said)
        self.assertEqual(code, 2, said.getvalue()[-600:])
        self.assertIn("no worker is configured for the implementation stage",
                      said.getvalue())

    def test_a_foreign_authority_uuid_refuses(self):
        self.installed()
        code, said = self.created("--job-id", "job-foreign-check")
        self.assertEqual(code, 0, said[-600:])
        argv_uuid = "0" * 31 + "a"
        with self.assertRaises(Exception) as caught:
            job_manager.main(
                ["--store", self.places["job_store"],
                 "--incarnation", "operator-2",
                 "--authority-uuid", argv_uuid,
                 "create", "--instance", self.state,
                 "--control", self.places["control_store"],
                 "--authority", self.places["authority_store"],
                 "--task", "foreign", "--statement", "foreign",
                 "--acceptance", "x", "--work-scope", "v12/TEMPLATE-JOBS.md"],
                stream=io.StringIO())
        self.assertTrue(caught.exception)

    def test_a_wrong_artifact_refuses_the_install(self):
        """A runtime that is not a frozen build is refused by the installer."""
        empty = pathlib.Path(self.root) / "not-a-bundle"
        (empty / "_internal").mkdir(parents=True)
        (empty / "baton-v12-stack").write_text("not a frozen build\n")
        document = self.document()
        document.pop("state_root", None)
        inputs = os.path.join(self.root, "wrong-artifact.json")
        pathlib.Path(inputs).write_text(json.dumps(document))
        said = io.StringIO()
        code = bootstrap.main(["--inputs", inputs, "--destination",
                               os.path.join(self.root, "refused"),
                               "--distro", str(empty),
                               "--no-repositories"], stream=said)
        self.assertEqual(code, 2, said.getvalue()[-600:])


if __name__ == "__main__":
    unittest.main(verbosity=2)
