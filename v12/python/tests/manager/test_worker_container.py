"""W6633 — the BUILT image, real containers, and the manager's stop path.

`work/records/2026/08/finding-v12-oci-reference-worker-image/`.

RECIPE TEXT CANNOT ESTABLISH A BUILT IMAGE. `test_worker_image.py` asserts what
the recipe SAYS; nothing there can tell you the resolved image identity, the
inherited layer contents, the config the engine actually applied, or that a
consent container running for real refuses to work. Those are facts about an
artefact, and the only way to have them is to build it.

IT FAILS RATHER THAN SKIPS WHEN THERE IS NO DAEMON. A required gate that
quietly passes because it could not run is the failure mode this distribution
is built against — and the acceptance names image inspection and
container-level negative tests, not "image inspection where available". A
missing daemon is an actionable failed prerequisite.

IT CLEANS UP EVERYTHING IT CREATES, ON EVERY PATH. Every resource is registered
for removal the instant it can exist, so a failure between creation and use
still removes it; the teardown is `--force` and ignores its own errors, because
a cleanup that fails loudly is a cleanup that leaves the NEXT resource behind.
A final case asserts the engine holds nothing this suite made.

THE CANCELLATION FIXTURE IS THE MANAGER'S REAL PATH, and the approved ruling is
why: cancellation is the runtime stop/termination path, never a worker-entry
operation and never a clean end of input. So a container is started, left
waiting on its channel, stopped through the engine, and its observable
settlement recorded. An empty stdin proves the manager closed a pipe; it proves
nothing about intent.
"""

import copy
import hashlib
import json
import os
import pathlib
import shutil
import tempfile
import subprocess
import time
import unittest
import uuid
from unittest.mock import patch

from baton_v12.worker_manager.oci import RESTRICTIONS
from tools.worker_image import (build_vector, build_worker_image,
                                staging_tag)

WORKER = (pathlib.Path(__file__).resolve().parents[3] / "worker")
ENGINE = os.environ.get("BATON_TEST_ENGINE", "docker")

# Everything this suite makes carries this prefix, so the final sweep can ask
# the engine a question rather than trust a bookkeeping list.
MARK = "baton-w6633-test"

PROTOCOL = "baton.worker-entry/1"


def engine(*arguments, stdin=None, timeout=180, check=True):
    finished = subprocess.run(
        [ENGINE, *arguments], input=stdin, capture_output=True,
        timeout=timeout)
    if check and finished.returncode != 0:
        raise AssertionError(
            f"{ENGINE} {' '.join(arguments)} failed ({finished.returncode}): "
            f"{finished.stderr.decode('utf-8', 'replace')[:2000]}")
    return finished


def restricted(*flags):
    """Every unconditional restriction the manager applies, DERIVED from
    `oci.RESTRICTIONS` rather than retyped.

    Fourth review [P1]: these launches carried `--network none` and nothing
    else, so twenty-three green cases ran containers that kept the default
    capability bounding set, a writable root, ordinary privilege behaviour and
    no CPU, PID or memory bound — and the acceptance's filesystem, user and
    capability half was never established by an ARTEFACT, only by argv this
    suite happened to choose.

    Derived, because a second copy of the table is a second thing to keep
    true: the adapter owns the posture and this gate consumes it, so a
    restriction added there tomorrow is applied here tomorrow.

    Module-level rather than a method, so it is reachable from a duck-typed
    harness that is standing in for a case class.
    """
    arguments = list(flags)
    for flag, value in RESTRICTIONS:
        arguments.append(flag)
        if value is not None:
            arguments.append(value)
    return arguments


def frame(document):
    body = json.dumps(document).encode("utf-8")
    return str(len(body)).encode("ascii") + b"\n" + body


def unframe(payload):
    found, at = [], 0
    while at < len(payload):
        end = payload.find(b"\n", at)
        if end < 0:
            break
        length = int(payload[at:end])
        body = payload[end + 1:end + 1 + length]
        found.append(json.loads(body.decode("utf-8")))
        at = end + 1 + length
    return found


class TheDaemonGateExercisesWhatTheManagerWillRun(unittest.TestCase):
    """Source-visible properties of the daemon gate, with no daemon needed.

    A green real-container result proves only the argv it actually launched.
    The acceptance requires the approved restricted runtime posture, and a
    second build proves reproducibility only when it does not reuse the first
    build's cached result.
    """

    def recording_engine(self, calls):
        def recorded(*arguments, **options):
            calls.append(arguments)
            return subprocess.CompletedProcess(arguments, 0, b"", b"")
        return recorded

    def test_the_channel_container_uses_every_unconditional_restriction(self):
        class Harness:
            image = "sha256:" + "0" * 64

            def container(self):
                return f"{MARK}-restriction-probe"

        calls = []
        with patch(f"{__name__}.engine", self.recording_engine(calls)):
            ContainerCase.talk(Harness(), CONSENT)
        arguments = calls[0]
        adjacent = set(zip(arguments, arguments[1:]))
        missing = []
        for flag, value in RESTRICTIONS:
            if value is None:
                if flag not in arguments:
                    missing.append(flag)
            elif (flag, value) not in adjacent:
                missing.append(f"{flag} {value}")
        self.assertEqual(missing, [],
                         "the real container gate omitted manager runtime "
                         "restrictions")

    def test_the_reproducibility_build_does_not_reuse_builder_cache(self):
        """Read from the build's own vector rather than by driving a build.

        It used to patch this module's `engine` helper and call
        `ContainerCase.build`. Once the build moved into `tools/
        worker_image.py` that patch reached nothing — and the case then ran a
        REAL build against the daemon and left its tag behind, which the
        residual sweep correctly caught. A golden vector is the right shape
        for a flag that is a decision: no daemon, and nothing created.
        """
        argv = build_vector(ENGINE, WORKER, WORKER / "Dockerfile",
                            f"{MARK}:cache-probe-unnormalized-probe",
                            "linux/amd64")
        self.assertIn("--no-cache", argv,
                      "the alleged independent rebuild can be a cache hit")
        self.assertEqual(argv[:2], [ENGINE, "build"])
        self.assertEqual(argv[argv.index("--platform") + 1], "linux/amd64")

    def test_the_normalized_tag_is_not_what_the_engine_built(self):
        """The staging reference is the tool's own and never the artefact.

        An image nobody normalized is not what the manager pins, so the two
        must not be able to collide — and a leftover stage has to be readable
        as one rather than mistaken for the result.

        Review [P1] made the stage an ALLOCATION rather than a derivation, so
        this asserts the two properties that still hold of every one: it
        names its destination and it is not its destination. Two calls
        answering two references is `test_concurrent_builds_for_one_
        destination_have_distinct_stages`, in the tool's own suite.
        """
        stage = staging_tag(f"{MARK}:probe")
        argv = build_vector(ENGINE, WORKER, WORKER / "Dockerfile", stage,
                            "linux/amd64")
        built = argv[argv.index("--tag") + 1]
        self.assertEqual(built, stage)
        self.assertTrue(built.startswith(f"{MARK}:probe-"), built)
        self.assertNotEqual(built, f"{MARK}:probe")


class ContainerCase(unittest.TestCase):
    """One built image for the whole class, and nothing left behind."""

    image = None

    @classmethod
    def setUpClass(cls):
        # THE PREREQUISITE IS CHECKED AND FAILED, not skipped.
        found = subprocess.run([ENGINE, "version", "--format", "{{.Server.Version}}"],
                               capture_output=True, timeout=60)
        if found.returncode != 0:
            raise AssertionError(
                f"W6633's image gate requires a reachable {ENGINE} daemon and "
                f"there is none: "
                f"{found.stderr.decode('utf-8', 'replace')[:500]}. This is a "
                f"failed prerequisite for a required gate, not a reason to "
                f"pass without running it.")
        cls.server = found.stdout.decode("utf-8").strip()
        # THE PLATFORM IS NAMED, NOT INHERITED. Re-review [P1]: the build
        # selected none, so nothing here could say which platform the recorded
        # identity belonged to -- and an image identity that does not name its
        # platform is not an identity a manager can pin. The value is the
        # engine's own, so this gate runs on an arm64 host without demanding
        # emulation, and it is passed EXPLICITLY so what was asked for and what
        # was applied are two facts that can disagree.
        told = subprocess.run(
            [ENGINE, "version", "--format", "{{.Server.Os}}/{{.Server.Arch}}"],
            capture_output=True, timeout=60)
        cls.platform = told.stdout.decode("utf-8").strip()
        assert "/" in cls.platform, cls.platform
        cls.image = f"{MARK}:{uuid.uuid4().hex[:12]}"
        cls.rebuilt = f"{MARK}:{uuid.uuid4().hex[:12]}"
        # BOTH TAGS REGISTERED BEFORE EITHER BUILD CAN CREATE ONE, so a build
        # that fails part way still has its tag removed -- and so the second
        # tag is registered even though the case that builds it may never run.
        for tag in (cls.image, cls.rebuilt):
            cls.addClassCleanup(
                lambda name=tag: subprocess.run(
                    [ENGINE, "image", "rm", "--force", name],
                    capture_output=True, timeout=120))
        cls.build(cls.image)

    @classmethod
    def rebuild(cls):
        """The second EXECUTION of the recipe, built once per class and
        inspected by whichever case asks first.

        Built on demand rather than in `setUpClass` so a class that never asks
        does not pay for it, and cached on the class so two cases that both
        ask compare the same second artefact rather than a third.
        """
        if not getattr(cls, "_rebuilt", False):
            cls.build(cls.rebuilt)
            cls._rebuilt = True
        found = engine("image", "inspect", cls.rebuilt)
        return json.loads(found.stdout.decode("utf-8"))[0]

    @classmethod
    def build(cls, tag):
        """One EXECUTION of the pinned recipe, through the recipe's own
        deterministic output step.

        Fifth review [P1]: the acceptance names an immutable IMAGE digest and
        `docker build` alone cannot produce one, so the previous correction
        redefined the artefact as equal layers plus a chosen subset of the
        config. That was the wrong move and the review said so. `tools/
        worker_image.py` is the right one: the engine builds with `--no-cache`
        and the volatile receipt metadata is normalized out of the result,
        which two independent executions then agree on exactly.

        The staging tag the tool builds under is its own and is removed on
        every path; what this gate inspects is the loaded, normalized image.
        """
        build_worker_image(ENGINE, WORKER, WORKER / "Dockerfile", tag,
                           cls.platform)

    def setUp(self):
        self.made = []

    def tearDown(self):
        for name in self.made:
            subprocess.run([ENGINE, "rm", "--force", name],
                           capture_output=True, timeout=120)

    def container(self):
        name = f"{MARK}-{uuid.uuid4().hex[:12]}"
        self.made.append(name)
        return name

    def inspected(self):
        found = engine("image", "inspect", self.image)
        return json.loads(found.stdout.decode("utf-8"))[0]

    def roots(self, given=None, assignment=None):
        """A host `/input/` carrying BOTH manager-authored documents, and a
        writable `/output/`, as mount triples for `talk`.

        W19784: the assignment identity is a DOCUMENT under a fixed read-only
        path, so this is what an execution container's delivery actually looks
        like. `assignment=None` leaves it out, which is the missing-delivery
        case.

        The output tree is world-writable because the image runs as an
        unprivileged uid the host does not have; the container's own posture is
        what makes that safe, and it is the manager's bind that decides the
        input side is read-only.
        """
        home = tempfile.mkdtemp(prefix="v12-worker-roots-")
        self.addCleanup(shutil.rmtree, home, True)
        inputs = os.path.join(home, "input")
        outputs = os.path.join(home, "output")
        os.makedirs(inputs)
        os.makedirs(outputs)
        os.chmod(outputs, 0o777)
        if given is None and assignment is None:
            given, assignment = input_pair()
        for name, document in (("input.json", given),
                               ("assignment.json", assignment)):
            if document is None:
                continue
            with open(os.path.join(inputs, name), "w",
                      encoding="utf-8") as handle:
                json.dump(document, handle)
        return outputs, ((inputs, "/input", False), (outputs, "/output", True))

    def talk(self, environment, *requests, timeout=120, mounts=()):
        """Run one container, speak the framed channel, read what it says.

        W19784: `mounts` exists because an EXECUTION container now has two
        filesystem roles and three protocol documents, and a suite that spoke
        only through the environment could not deliver any of them. A consent
        container passes none, which is the topology rather than the default:
        §7.0 says consent mounts nothing.
        """
        name = self.container()
        arguments = restricted("run", "--interactive", "--rm",
                               "--name", name)
        for source, target, writable in mounts:
            arguments += ["--mount", f"type=bind,source={source},"
                          f"target={target},readonly="
                          f"{'false' if writable else 'true'}"]
        for key, value in environment.items():
            arguments += ["--env", f"{key}={value}"]
        arguments.append(self.image)
        finished = engine(*arguments, stdin=b"".join(
            frame(request) for request in requests),
            timeout=timeout, check=False)
        return finished.returncode, unframe(finished.stdout)


def ask(operation, session, **members):
    return {"protocol": PROTOCOL, "session": session,
            "operation_id": f"op-{uuid.uuid4().hex[:12]}",
            "operation": operation, **members}


CONSENT_SESSION = "session-consent-real"
EXECUTION_SESSION = "session-execution-real"

CONSENT = {"BATON_WORKER_POSTURE": "consent",
           "BATON_WORKER_SESSION": CONSENT_SESSION,
           "BATON_WORKER_CONTRACT": "do the thing",
           "BATON_WORKER_ROLE": "implementer"}
# W14251, closed, and this suite is where it was still unclosed. The two
# postures carry THE SAME FOUR MEMBERS: `BATON_WORKER_ASSIGNMENT`,
# `_WORKSPACE` and `_OUTPUT` are REMOVED rather than renamed, because with two
# fixed filesystem roots there is nothing left for them to say -- and the
# worker refuses a `BATON_WORKER_*` member outside the set, so a container
# built with one of them is a container built wrong.
#
# The posture difference did not go with them. It moved to where it belongs:
# an execution container HAS the two roots and a consent container does not.
EXECUTION = {"BATON_WORKER_POSTURE": "execution",
             "BATON_WORKER_SESSION": EXECUTION_SESSION,
             "BATON_WORKER_CONTRACT": "do the thing",
             "BATON_WORKER_ROLE": "implementer"}

# The WHOLE frozen `outputDescriptor`. W6633 eleventh review [P1]: the
# constraints were absent here as well as in the worker, so a declaration this
# suite handed a real container was one the contract would refuse.
UNBOUNDED = {"max_bytes": 1048576, "max_entries": 100,
             "allowed_media_types": ["text/plain"],
             "link_policy": "forbid", "validator_digest": None}
DECLARATION = {"name": "proposal", "type": "directory-result",
               "path": "out", "required": True,
               "constraints": dict(UNBOUNDED)}
WORK_REF = {"authority_uuid": "0123456789abcdef0123456789abcdef",
            "work_id": "01234567-W1"}
ASSIGNMENT_REF = {"work_ref": WORK_REF,
                  "participant": "baton.claude", "generation": 1}

VECTORS = (pathlib.Path(__file__).resolve().parents[4] / "work" / "records"
           / "2026" / "08" / "finding-v12-isolated-agent-workers" / "findings"
           / "finding-v12-worker-contract" / "findings"
           / "finding-worker-control-api-manifests" / "evidence"
           / "vectors.json")


def _resealed(document):
    """A document whose own digest describes its own (spoiled) bytes, so what
    refuses it is the closed-set rule rather than the digest rule."""
    document.pop("manifest_digest", None)
    document["manifest_digest"] = _digest(document)
    return document


def _digest(value):
    body = json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(body).hexdigest()


def input_pair(declarations=None, **spoiled):
    """The record's own input manifest and an assignment minted against it."""
    corpus = json.loads(VECTORS.read_text(encoding="utf-8"))
    given = next(one["document"] for one in corpus["valid"]
                 if one["name"] ==
                 "input-manifest-directory-and-declared-output")
    given = dict(given, work_ref=dict(WORK_REF),
                 outputs=[dict(DECLARATION)] if declarations is None
                 else declarations)
    given.pop("manifest_digest", None)
    given["manifest_digest"] = _digest(given)
    assignment = {"version": given["version"], "manifest_id": "assignment-1",
                  "created_at": given["created_at"], "extensions": {},
                  "schema": "baton.worker-manifest/assignment",
                  "assignment_ref": copy.deepcopy(ASSIGNMENT_REF),
                  "assignment_contract": given["assignment_contract"],
                  "offer_id": "offer-1", "runtime_attempt_id": "attempt-1",
                  "input_manifest_digest": given["manifest_digest"],
                  "policy_digest": given["policy_digest"],
                  "runtime_profile_digest": given["runtime_profile_digest"],
                  "claim_receipt_digest": "sha256:" + "c" * 64,
                  "claim_event_seq": 7,
                  "activated_at": given["created_at"]}
    assignment.update(spoiled)
    assignment.pop("manifest_digest", None)
    assignment["manifest_digest"] = _digest(assignment)
    return given, assignment


class TheBuiltImageIsWhatTheRecipeSaid(ContainerCase):

    def test_the_base_the_engine_resolved_is_the_pinned_one(self):
        """The recipe names a digest; this is the engine agreeing that it
        built from it."""
        recipe = (WORKER / "Dockerfile").read_text(encoding="utf-8")
        pinned = [line.split("@")[1].strip() for line in recipe.splitlines()
                  if line.startswith("FROM ")][0]
        found = engine("image", "inspect", "--format",
                       "{{json .RepoDigests}}", f"python@{pinned}")
        self.assertIn(pinned, found.stdout.decode("utf-8"))

    def test_the_image_identity_is_a_digest_and_names_its_platform(self):
        """An identity with no platform is not one a manager can pin: the same
        recipe on two architectures is two artefacts, and a digest that did not
        say which would make the record ambiguous rather than exact."""
        config = self.inspected()
        self.assertRegex(config["Id"], r"^sha256:[0-9a-f]{64}$")
        self.assertEqual(f"{config['Os']}/{config['Architecture']}",
                         self.platform,
                         "the engine applied a platform this gate did not ask "
                         "for")

    def test_the_same_context_builds_to_the_same_artefact(self):
        """REPRODUCIBLE, and now the whole artefact rather than a subset.

        This case used to carry a long argument for comparing layers and five
        config members INSTEAD of the image identity, on the reading that two
        independent builds have two ids by construction. Fifth review [P1]
        refused that as a weaker, contradictory contract, and it was right:
        the acceptance names an immutable image digest and a manager pins that
        digest, so reproducibility has to reach it.

        It does now. `tools/worker_image.py` normalizes the build's receipt
        metadata — the wall clock, the intermediate container ids, the parent
        chain id, and the build-time mtimes on the directories the `COPY`
        created — and two executions of the recipe reach one identity, which
        `test_two_independent_builds_have_one_pinnable_image_identity` states
        directly.

        What is left here is the FILESYSTEM and the applied configuration,
        which are worth their own case: an identity that matched while the
        layers differed would be a normalizer that had erased a real
        difference rather than a receipt.
        """
        again = self.rebuild()
        first = self.inspected()
        self.assertEqual(again["RootFS"], first["RootFS"],
                         "two executions of the recipe made two filesystems")
        self.assertGreater(len(again["RootFS"]["Layers"]), 1)
        for key in ("User", "Entrypoint", "Cmd", "Env", "WorkingDir"):
            with self.subTest(config=key):
                self.assertEqual(again["Config"].get(key),
                                 first["Config"].get(key))
        self.assertEqual(f"{again['Os']}/{again['Architecture']}",
                         self.platform)

    def test_two_independent_builds_have_one_pinnable_image_identity(self):
        """The acceptance names an immutable IMAGE digest, not only layers.

        `RootFS` equality proves equal filesystem bytes. It does not make two
        OCI images one artefact when their config objects — and therefore
        their content-addressed image identities — differ. A downstream
        manager pins and launches the image digest, so reproducibility has to
        reach that same identity rather than a reviewer-selected subset of its
        inputs.
        """
        again = self.rebuild()
        first = self.inspected()
        self.assertEqual(again["Id"], first["Id"],
                         "independent builds have no single image digest to "
                         "pin")

    def test_a_bare_engine_build_is_why_the_output_step_exists(self):
        """The measurement that motivates the normalizer, kept as a case.

        This replaces `test_the_image_id_is_a_receipt_and_not_the_artefact`,
        which required the two identities to REMAIN different and was the
        weakening fifth review [P1] refused. The fact it was built on is still
        true and still worth holding: a bare `docker build` on this engine
        cannot produce one identity. What was wrong was concluding that the
        acceptance had to give way.

        It also corrects that measurement. The record said the LAYERS were
        identical and only the config timestamp moved. They are not: the two
        `COPY` layers carry the directory entries the copy created, and their
        mtime is the build clock. Two builds a second apart differ in their
        layers too — which is why the previous reading found them equal, and
        why the same-artefact case above used to pass or fail depending on
        whether two builds landed inside one wall-clock second.
        """
        raw = []
        for _ in range(2):
            tag = f"{MARK}:{uuid.uuid4().hex[:12]}"
            self.addCleanup(lambda name=tag: subprocess.run(
                [ENGINE, "image", "rm", "--force", name],
                capture_output=True, timeout=120))
            engine("build", "--no-cache", "--platform", self.platform,
                   "--tag", tag, "--file", str(WORKER / "Dockerfile"),
                   str(WORKER), timeout=900)
            raw.append(json.loads(
                engine("image", "inspect", tag).stdout.decode("utf-8"))[0])
            # A SECOND APART ON PURPOSE. The directory mtime has one-second
            # resolution, so two builds inside one second agree by accident —
            # and an accident is exactly what the earlier measurement caught.
            time.sleep(1.1)
        self.assertNotEqual(raw[0]["Id"], raw[1]["Id"],
                            "a bare build is reproducible on this engine and "
                            "the normalizing output step is unnecessary")
        self.assertNotEqual(raw[0]["RootFS"]["Layers"],
                            raw[1]["RootFS"]["Layers"],
                            "only the config moved; the recorded reading that "
                            "the layers are stable would then be right")
        # AND THE OUTPUT STEP TURNS EXACTLY THAT INTO ONE IDENTITY.
        self.assertEqual(self.rebuild()["Id"], self.inspected()["Id"])

    def observed_inside(self, probe):
        """Run one Python expression INSIDE a restricted container and read
        its JSON answer.

        Fourth review [P1]: argv says what was ASKED FOR. These properties are
        what the kernel and the engine actually applied, read from inside the
        thing they were applied to.
        """
        name = self.container()
        found = engine(*restricted("run", "--name", name,
                                   "--entrypoint", "python3"),
                       self.image, "-c", probe)
        return json.loads(found.stdout.decode("utf-8"))

    def test_the_running_container_holds_no_effective_capability(self):
        """`--cap-drop ALL` and `--security-opt no-new-privileges`, as the
        process sees them. A bounding set that still carried a capability
        would make the flag a comment."""
        seen = self.observed_inside(
            "import json;"
            "status=dict(l.split(':',1) for l in "
            "open('/proc/self/status') if ':' in l);"
            "print(json.dumps({k: status[k].strip() "
            "for k in ('CapEff','CapPrm','CapBnd','NoNewPrivs')}))")
        for name in ("CapEff", "CapPrm", "CapBnd"):
            with self.subTest(capability_set=name):
                self.assertEqual(int(seen[name], 16), 0,
                                 f"{name} is {seen[name]}, not empty")
        self.assertEqual(seen["NoNewPrivs"], "1",
                         "privilege escalation was not denied")

    def test_the_running_container_has_a_read_only_root(self):
        """`--read-only`, proved by trying. The one writable place is the
        tmpfs the table names, and it is non-executable."""
        seen = self.observed_inside(
            "import json,os;"
            "w=lambda p: (lambda: (open(p,'w').close(), True)[1]);"
            "attempt=lambda p: (w(p)() if True else None);"
            "out={};"
            "\nfor path in ('/probe','/opt/baton/probe','/tmp/probe'):\n"
            "    try:\n"
            "        open(path,'w').close(); os.unlink(path); out[path]=True\n"
            "    except OSError:\n"
            "        out[path]=False\n"
            "print(json.dumps(out))")
        self.assertIs(seen["/probe"], False, "the root filesystem is writable")
        self.assertIs(seen["/opt/baton/probe"], False,
                      "the program directory is writable")
        self.assertIs(seen["/tmp/probe"], True,
                      "the named writable tmpfs is not writable")

    def test_the_running_container_carries_the_bounded_tmpfs_posture(self):
        """The two tmpfs mounts the table names, with the options it names.
        Read from `/proc/self/mounts`, which is the kernel's own account."""
        seen = self.observed_inside(
            "import json;"
            "print(json.dumps([l.split()[1:4] for l in "
            "open('/proc/self/mounts') if l.split()[1] in "
            "('/tmp','/dev/shm')]))")
        found = {where: options for where, kind, options in seen}
        for where in ("/tmp", "/dev/shm"):
            with self.subTest(mount=where):
                self.assertIn(where, found, seen)
                self.assertIn("noexec", found[where])
                self.assertIn("nosuid", found[where])
                self.assertIn("nodev", found[where])

    def test_the_engine_applied_the_non_root_user(self):
        self.assertEqual(self.inspected()["Config"]["User"], "65532:65532")

    def test_the_engine_applied_the_exec_form_entrypoint(self):
        config = self.inspected()["Config"]
        self.assertEqual(config["Entrypoint"],
                         ["python3", "/opt/baton/baton_worker.py"])
        self.assertIn(config.get("Cmd"), (None, []))

    def test_the_built_image_carries_no_posture_and_no_session(self):
        """Read from the CONFIG the engine applied, not from the recipe text:
        an image that defaulted either would make every container built from
        it share an identity, or run as execution when the manager forgot to
        say."""
        for entry in self.inspected()["Config"]["Env"]:
            self.assertFalse(entry.startswith("BATON_WORKER_"), entry)

    def test_the_built_image_announces_no_network_or_health_surface(self):
        config = self.inspected()["Config"]
        self.assertIn(config.get("ExposedPorts"), (None, {}))
        self.assertIn(config.get("Volumes"), (None, {}))
        self.assertIn(config.get("Healthcheck"), (None, {}))

    def test_the_filesystem_carries_the_program_and_nothing_of_the_manager(
            self):
        """The layer contents, not the COPY lines. A worker that could import
        the manager is a worker one bug away from holding its capabilities,
        and this is the artefact saying so."""
        name = self.container()
        found = engine(*restricted("run", "--name", name,
                                   "--entrypoint", "python3"),
                       self.image, "-c",
                       "import json,os,sys;"
                       "print(json.dumps({"
                       "'opt': sorted(os.listdir('/opt/baton')),"
                       "'manager': any(os.path.exists(os.path.join(p,'baton_v12'))"
                       " for p in sys.path if p and os.path.isdir(p)),"
                       "'uid': os.getuid(), 'gid': os.getgid()}))")
        seen = json.loads(found.stdout.decode("utf-8"))
        # W19784 review [P0], 2026-08-27: three entries now. The worker derives
        # the closed member sets of the manager's two `/input/` documents from
        # the frozen contract, so the contract travels with the image. Still
        # EXHAUSTIVE, and the case below proves the third is the same bytes as
        # the repository's -- an image validating against a drifted contract
        # would drift silently, because it validates against what it was
        # shipped.
        self.assertEqual(seen["opt"],
                         ["baton_worker.py", "scripted_agent.py",
                          "worker-control-1.0.schema.json"])
        self.assertIs(seen["manager"], False,
                      "the manager package is importable inside the worker")
        self.assertEqual((seen["uid"], seen["gid"]), (65532, 65532))

    def test_the_image_carries_the_frozen_contract_byte_for_byte(self):
        """Asked of the ARTEFACT. `test_frozen` proves the repository's five
        copies agree; this proves the one that actually reached the image is
        that same document, which is the only copy the running worker reads."""
        name = self.container()
        found = engine(*restricted("run", "--name", name,
                                   "--entrypoint", "python3"),
                       self.image, "-c",
                       "import hashlib,sys;"
                       "sys.stdout.write(hashlib.sha256(open("
                       "'/opt/baton/worker-control-1.0.schema.json','rb')"
                       ".read()).hexdigest())")
        here = (WORKER / "worker-control-1.0.schema.json").read_bytes()
        self.assertEqual(found.stdout.decode("utf-8").strip(),
                         hashlib.sha256(here).hexdigest())

    def test_no_assignment_or_secret_material_is_in_any_layer(self):
        """Asked of the image's own history rather than of the recipe: a
        build argument or an inherited layer could carry one without a COPY
        line saying so."""
        found = engine("image", "history", "--no-trunc", "--format",
                       "{{.CreatedBy}}", self.image)
        history = found.stdout.decode("utf-8")
        for marker in ("BATON_WORKER_ASSIGNMENT", "BATON_WORKER_WORKSPACE",
                       "BATON_WORKER_OUTPUT", "BATON_WORKER_SESSION",
                       "bearer", "claim_token"):
            self.assertNotIn(marker, history, marker)


class RealContainersHoldTheTopology(ContainerCase):

    def test_a_consent_container_answers_describe_and_consider(self):
        status, given = self.talk(CONSENT, ask("describe", CONSENT_SESSION),
                                  ask("consider", CONSENT_SESSION))
        self.assertEqual(status, 0)
        self.assertEqual([answer["ok"] for answer in given], [True, True])
        self.assertEqual(given[0]["answer"]["posture"], "consent")
        self.assertEqual(given[1]["answer"]["decision"], "accept")

    def test_a_real_consent_container_is_not_asked_to_work(self):
        """The container-level negative the acceptance names: not the
        function refusing, the ARTEFACT refusing."""
        status, given = self.talk(CONSENT,
                                  ask("work", CONSENT_SESSION, task="build"))
        self.assertIs(given[0]["ok"], False)
        self.assertEqual(given[0]["code"], "posture")

    def test_an_execution_container_completes_and_recaps(self):
        """W19784, migrating what W14251 left behind here. This asked for a
        `task` and read a `workspace` back -- an operand and an answer member
        the artifact-neutral ruling removed -- and it delivered no `/input/`
        at all, so the built image had never once been asked to do the work it
        is for. It now runs against the real two-root delivery."""
        outputs, mounts = self.roots()
        status, given = self.talk(EXECUTION, ask("work", EXECUTION_SESSION),
                                  mounts=mounts)
        self.assertEqual(status, 0)
        answer = given[0]["answer"]
        self.assertEqual(sorted(answer), ["disposition", "outputs", "recap"])
        self.assertEqual(answer["disposition"], "completed")
        with open(os.path.join(outputs, "output.json"),
                  encoding="utf-8") as one:
            published = json.load(one)
        self.assertEqual(published["schema"],
                         "baton.worker-manifest/completion")
        # THE WHOLE POINT, observed in a real container: the identity the
        # envelope carries is the one the second input document delivered,
        # generation included.
        self.assertEqual(published["assignment_ref"], ASSIGNMENT_REF)

    def test_a_real_container_refuses_a_delivery_it_cannot_be_sure_of(self):
        """The negatives, at the ARTEFACT rather than the function. Each runs
        the built image against a real `/input/` and each must refuse before
        anything is published."""
        given, _ = input_pair()
        other = "sha256:" + "9" * 64
        for what, spoiled in (
                ("no assignment document", None),
                ("another Work",
                 {"assignment_ref": {
                     "work_ref": {"authority_uuid": "f" * 32,
                                  "work_id": "ffffffff-W9"},
                     "participant": "baton.claude", "generation": 1}}),
                ("another input manifest", {"input_manifest_digest": other}),
                ("another policy", {"policy_digest": other})):
            with self.subTest(what=what):
                assignment = (None if spoiled is None
                              else input_pair(**spoiled)[1])
                outputs, mounts = self.roots(given=given,
                                             assignment=assignment)
                status, seen = self.talk(
                    EXECUTION, ask("work", EXECUTION_SESSION), mounts=mounts)
                self.assertIs(seen[0]["ok"], False)
                self.assertEqual(seen[0]["code"], "input")
                self.assertEqual(os.listdir(outputs), [])

    def test_a_real_container_refuses_a_document_that_is_not_the_managers(self):
        """W19784 review [P0], through the BUILT IMAGE. The direct suite proves
        the worker refuses a false self-digest and an extra top-level member;
        this proves the artefact does, because the validation is derived from a
        contract that has to have reached the image for it to work at all.

        A recipe that forgot the third COPY would fail exactly here, and the
        refusal would be the worker saying it has no contract to hold anything
        to rather than an agent running on an unvalidated document.
        """
        given, assignment = input_pair()
        for what, spoil in (
                ("a false self-digest on the input side",
                 lambda g, a: (dict(g, manifest_digest="sha256:" + "0" * 64),
                               a)),
                ("a false self-digest on the assignment side",
                 lambda g, a: (g, dict(a, manifest_digest="sha256:" + "0" * 64))),
                ("a second identity alias on the input side",
                 lambda g, a: (_resealed(dict(
                     g, compatibility_assignment=copy.deepcopy(
                         ASSIGNMENT_REF))), a)),
                ("a second identity alias on the assignment side",
                 lambda g, a: (g, _resealed(dict(
                     a, compatibility_assignment=copy.deepcopy(
                         ASSIGNMENT_REF)))))):
            with self.subTest(what=what):
                spoiled_input, spoiled_assignment = spoil(
                    copy.deepcopy(given), copy.deepcopy(assignment))
                outputs, mounts = self.roots(given=spoiled_input,
                                             assignment=spoiled_assignment)
                status, seen = self.talk(
                    EXECUTION, ask("work", EXECUTION_SESSION), mounts=mounts)
                self.assertIs(seen[0]["ok"], False)
                self.assertEqual(seen[0]["code"], "input")
                self.assertEqual(os.listdir(outputs), [])

    def test_the_authorized_root_is_what_the_engine_was_actually_told(self):
        """W19784 second review [P0], at the ARTEFACT. The unit cases prove the
        adapter refuses a plan that does not name the proved root; this proves
        that what a real engine received was that root, read-only, at the
        worker's fixed path -- and that a real worker read its two documents
        out of it."""
        outputs, mounts = self.roots()
        inputs = mounts[0][0]
        status, given = self.talk(EXECUTION, ask("work", EXECUTION_SESSION),
                                  mounts=mounts)
        self.assertEqual(status, 0)
        self.assertIs(given[0]["ok"], True)
        # The argv this suite handed the engine, read back rather than
        # described: the source is the composed root and the bind is read-only
        # at the one fixed target.
        self.assertEqual(mounts[0][1], "/input")
        self.assertIs(mounts[0][2], False)
        self.assertTrue(os.path.isfile(os.path.join(inputs, "assignment.json")))
        with open(os.path.join(outputs, "output.json"),
                  encoding="utf-8") as one:
            self.assertEqual(json.load(one)["assignment_ref"], ASSIGNMENT_REF)

    def test_a_container_cannot_write_the_input_root_it_was_given(self):
        """The read-only half, asked of the artefact. The input is the evidence
        the result is measured against, so a runtime that could edit it could
        edit what it is judged by."""
        _outputs, mounts = self.roots()
        name = self.container()
        found = engine(*restricted("run", "--name", name,
                                   "--mount", f"type=bind,source={mounts[0][0]},"
                                              f"target=/input,readonly=true",
                                   "--entrypoint", "python3"),
                       self.image, "-c",
                       "import json;"
                       "\ntry:\n open('/input/assignment.json','a')"
                       "\n print(json.dumps({'wrote': True}))"
                       "\nexcept OSError as e:\n"
                       " print(json.dumps({'wrote': False}))",
                       check=False)
        self.assertEqual(json.loads(found.stdout.decode("utf-8"))["wrote"],
                         False)

    def test_a_real_container_answers_with_names_and_publishes_records(self):
        """W6633 eleventh review [P1], at the ARTEFACT. Two surfaces carrying
        different things: the framed answer names what was produced, and the
        published envelope holds the whole record for each output."""
        outputs, mounts = self.roots()
        status, given = self.talk(EXECUTION, ask("work", EXECUTION_SESSION),
                                  mounts=mounts)
        self.assertEqual(status, 0)
        self.assertEqual(given[0]["answer"]["outputs"], ["proposal"])
        with open(os.path.join(outputs, "output.json"),
                  encoding="utf-8") as one:
            published = json.load(one)
        record = published["outputs"][0]
        self.assertEqual(sorted(record),
                         ["content_manifest", "name", "path",
                          "result_metadata", "status", "type"])
        self.assertEqual(record["content_manifest"]["entry_count"], 1)

    def test_a_real_container_refuses_an_oversized_declared_output(self):
        """A one-byte ceiling against the scripted worker's 34-byte result.
        No success frame, and NO COMPLETION SIGNAL -- the manager reconciles a
        runtime that published nothing, not one that published a lie."""
        bounded = {**DECLARATION, "constraints": {**UNBOUNDED, "max_bytes": 1}}
        given, assignment = input_pair(declarations=[bounded])
        outputs, mounts = self.roots(given=given, assignment=assignment)
        status, seen = self.talk(EXECUTION, ask("work", EXECUTION_SESSION),
                                 mounts=mounts)
        self.assertIs(seen[0]["ok"], False)
        # THE MATERIAL IS THERE AND THE SIGNAL IS NOT, and that distinction is
        # the point rather than a weaker assertion. This declaration is valid,
        # so the agent runs and writes; the ceiling is crossed at measurement.
        # What must not exist is `output.json` -- its presence under its final
        # name is the completion signal, and the manager reconciles a runtime
        # that published nothing rather than one that published a lie.
        self.assertIn("out", os.listdir(outputs))
        self.assertNotIn("output.json", os.listdir(outputs))

    def test_a_real_container_cannot_be_declared_out_of_its_output_root(self):
        """THE CASE THE READ-ONLY INPUT MOUNT DOES NOT COVER. `../tmp/escaped`
        targets the writable private ephemeral space, so nothing about the
        input root's mode contains it -- only the worker's own containment
        rule does, and it runs before the agent."""
        escaped = {**DECLARATION, "path": "../tmp/escaped"}
        given, assignment = input_pair(declarations=[escaped])
        outputs, mounts = self.roots(given=given, assignment=assignment)
        status, seen = self.talk(EXECUTION, ask("work", EXECUTION_SESSION),
                                 mounts=mounts)
        self.assertIs(seen[0]["ok"], False)
        self.assertEqual(seen[0]["code"], "input")
        self.assertEqual(os.listdir(outputs), [])

    def test_a_real_container_refuses_the_reserved_output_manifest_name(self):
        """A declared output at `output.json` would have the agent writing the
        completion signal itself."""
        reserved = {**DECLARATION, "path": "output.json"}
        given, assignment = input_pair(declarations=[reserved])
        outputs, mounts = self.roots(given=given, assignment=assignment)
        status, seen = self.talk(EXECUTION, ask("work", EXECUTION_SESSION),
                                 mounts=mounts)
        self.assertIs(seen[0]["ok"], False)
        self.assertEqual(os.listdir(outputs), [])

    def test_a_real_container_refuses_a_descriptor_value_it_consumes(self):
        """W6633 twelfth review [P1], at the ARTEFACT. A numeric `name` is
        contract-invalid and is a value the worker uses for lookup and for
        authoring the completion envelope -- so it must never reach the
        agent."""
        for what, spoiled in (
                ("a numeric name", {**DECLARATION, "name": 7}),
                ("a link policy outside the frozen const",
                 {**DECLARATION, "constraints": {**UNBOUNDED,
                                                 "link_policy": "allow"}}),
                ("an entry ceiling above the frozen maximum",
                 {**DECLARATION, "constraints": {**UNBOUNDED,
                                                 "max_entries": 100001}})):
            with self.subTest(what=what):
                given, assignment = input_pair(declarations=[spoiled])
                outputs, mounts = self.roots(given=given,
                                             assignment=assignment)
                status, seen = self.talk(
                    EXECUTION, ask("work", EXECUTION_SESSION), mounts=mounts)
                self.assertIs(seen[0]["ok"], False)
                self.assertEqual(seen[0]["code"], "input")
                self.assertEqual(os.listdir(outputs), [])

    def test_a_real_container_publishes_nothing_for_a_directory_link(self):
        """The link the traversal used to walk straight past. Proved against
        the built image because `os.walk`'s directory/file split is a property
        of the runtime the artefact actually has, not of the recipe.

        The scripted agent cannot make a link, so this drives the entrypoint
        with a one-line agent supplied through the image's own module path.
        """
        outputs, mounts = self.roots()
        name = self.container()
        found = engine(
            *restricted("run", "--interactive", "--name", name),
            *[arg for source, target, writable in mounts
              for arg in ("--mount", f"type=bind,source={source},"
                                     f"target={target},readonly="
                                     f"{'false' if writable else 'true'}")],
            *[arg for key, value in EXECUTION.items()
              for arg in ("--env", f"{key}={value}")],
            "--entrypoint", "python3", self.image, "-c",
            "import os, sys;"
            "sys.path.insert(0, '/opt/baton');"
            "import baton_worker as w;"
            "\nclass Linking:\n"
            " def work(self, seen, declared):\n"
            "  place = os.path.join(w.OUTPUT_ROOT, declared[0]['path'])\n"
            "  os.makedirs(place)\n"
            "  os.symlink(w.OUTPUT_ROOT, os.path.join(place, 'linked'))\n"
            "  return {'disposition': 'completed', 'recap': 'linked',"
            " 'outputs': [{'name': declared[0]['name'], 'status': 'present',"
            " 'result_metadata': {}}]}\n"
            "\nsys.exit(w.main(agent=Linking()))",
            stdin=frame(ask("work", EXECUTION_SESSION)), check=False)
        answered = unframe(found.stdout)
        self.assertIs(answered[0]["ok"], False)
        self.assertNotIn("output.json", os.listdir(outputs))

    def test_a_real_consent_container_mounts_neither_input_document(self):
        """§7.0: consent mounts nothing. The posture boundary is the
        filesystem rather than a rule about a string, and this asks the
        ARTEFACT."""
        status, given = self.talk(CONSENT, ask("consider", CONSENT_SESSION))
        self.assertIs(given[0]["ok"], True)
        found = engine(*restricted("run", "--rm", "--name", self.container()),
                       *[arg for key, value in CONSENT.items()
                         for arg in ("--env", f"{key}={value}")],
                       "--entrypoint", "/bin/sh", self.image,
                       "-c", "ls /input /output 2>&1 || true", check=False)
        told = found.stdout.decode("utf-8", "replace")
        self.assertNotIn("input.json", told)
        self.assertNotIn("assignment.json", told)

    def test_a_real_container_refuses_the_other_postures_session(self):
        status, given = self.talk(CONSENT,
                                  ask("describe", EXECUTION_SESSION))
        self.assertIs(given[0]["ok"], False)
        self.assertEqual(given[0]["code"], "session")

    def test_a_real_container_consumes_an_operation_id_once(self):
        request = ask("describe", CONSENT_SESSION)
        status, given = self.talk(CONSENT, request, dict(request))
        self.assertEqual([answer["ok"] for answer in given], [True, False])
        self.assertEqual(given[1]["code"], "replay")

    def test_a_container_built_with_the_wrong_posture_latches_and_exits(self):
        status, given = self.talk(
            {**CONSENT, "BATON_WORKER_POSTURE": "admin"},
            ask("consider", CONSENT_SESSION))
        self.assertNotEqual(status, 0)
        self.assertEqual(len(given), 1)
        self.assertEqual(given[0]["code"], "posture")
        self.assertEqual(given[0]["session"], CONSENT_SESSION)

    def test_a_consent_container_carrying_assignment_material_latches(self):
        status, given = self.talk(
            {**CONSENT, "BATON_WORKER_ASSIGNMENT": "assignment-1"},
            ask("consider", CONSENT_SESSION))
        self.assertNotEqual(status, 0)
        self.assertEqual(given[0]["code"], "posture")

    def test_a_container_started_without_a_session_says_nothing(self):
        without = {name: value for name, value in CONSENT.items()
                   if name != "BATON_WORKER_SESSION"}
        status, given = self.talk(without, ask("describe", CONSENT_SESSION))
        self.assertEqual((status, given), (2, []))


class CancellationIsTheManagersRuntimeStopPath(ContainerCase):
    """The approved ruling, exercised against a real container.

    Clean EOF is the manager closing a pipe. Cancellation is the manager
    STOPPING the runtime, and the difference is the whole reason this fixture
    was rejected in its first form.
    """

    def waiting(self, name):
        """A detached container holding its channel open, under every
        restriction the manager applies."""
        engine(*restricted("run", "--detach", "--interactive",
                           "--name", name),
               *[arg for key, value in EXECUTION.items()
                 for arg in ("--env", f"{key}={value}")],
               self.image)

    def test_a_waiting_container_is_stopped_and_settles_observably(self):
        name = self.container()
        # Started DETACHED and holding its channel open, so it is genuinely
        # waiting on stdin when the stop arrives -- a container that had
        # already exited would make this a fixture about scheduling.
        self.waiting(name)
        running = json.loads(engine(
            "container", "inspect", "--format", "{{json .State}}",
            name).stdout.decode("utf-8"))
        self.assertIs(running["Running"], True,
                      "the container was not waiting when the stop arrived")

        engine("stop", "--timeout", "10", name, timeout=120)

        settled = json.loads(engine(
            "container", "inspect", "--format", "{{json .State}}",
            name).stdout.decode("utf-8"))
        self.assertIs(settled["Running"], False)
        self.assertEqual(settled["Status"], "exited")
        # THE OBSERVABLE SETTLEMENT, recorded rather than described. PID 1 is
        # Python with no shell in front of it, so the engine's signal reaches
        # the program itself and the exit status is the one the manager reads
        # back through the adapter.
        self.assertIsInstance(settled["ExitCode"], int)
        self.settlement = settled

    def test_a_stopped_container_is_removable_and_leaves_nothing(self):
        name = self.container()
        self.waiting(name)
        engine("stop", "--timeout", "10", name, timeout=120)
        engine("rm", name)
        found = engine("container", "inspect", name, check=False)
        self.assertNotEqual(found.returncode, 0,
                            "the container survived its removal")

    def test_an_ended_channel_is_not_cancellation(self):
        """The distinction, asserted rather than asserted-about: closing the
        channel is an ORDINARY end and exits zero, which is exactly why it
        cannot stand in for a stop."""
        _outputs, mounts = self.roots()
        status, given = self.talk(EXECUTION, mounts=mounts)
        self.assertEqual((status, given), (0, []))


class TheGateLeavesTheEngineAsItFoundIt(ContainerCase):

    def test_no_container_of_this_suite_survives_it(self):
        """Asked of the ENGINE rather than of a bookkeeping list, because a
        list is a record of what somebody remembered creating."""
        found = engine("ps", "--all", "--filter", f"name={MARK}",
                       "--format", "{{.Names}}")
        # EVERY MATCH, and the correction is the whole case. Re-review [P1]:
        # this dropped every name starting with `baton-w6633-test-`, which is
        # the prefix every container this suite makes carries -- so the list
        # was empty whatever survived, and "the engine proves no residue" was
        # a sentence with nothing behind it.
        left = [line.strip()
                for line in found.stdout.decode("utf-8").splitlines()
                if line.strip()]
        self.assertEqual(left, [], "containers of this suite survived it")

    def test_the_residual_check_can_actually_fail(self):
        """A guard with nothing to catch changes no verdict -- measured. The
        way to test one is to hand it something: a real container is created,
        the same question is asked, and it has to come back naming it."""
        name = self.container()
        engine("create", "--name", name, self.image)
        found = engine("ps", "--all", "--filter", f"name={MARK}",
                       "--format", "{{.Names}}")
        left = [line.strip()
                for line in found.stdout.decode("utf-8").splitlines()
                if line.strip()]
        self.assertIn(name, left,
                      "the sweep cannot see a container this suite made")

    def test_only_this_run_s_image_tag_exists(self):
        found = engine("images", "--filter", f"reference={MARK}",
                       "--format", "{{.Repository}}:{{.Tag}}")
        tags = {line.strip()
                for line in found.stdout.decode("utf-8").splitlines()
                if line.strip()}
        # THIS RUN'S OWN TAGS AND NOTHING ELSE. Both are allowed because both
        # are registered for removal before either can exist; the reproducible
        # -identity case builds the second one, and whether it has run yet is
        # not what this case is about.
        self.assertIn(self.image, tags)
        self.assertEqual(tags - {self.image, self.rebuilt}, set(),
                         "an earlier run's image survived it")


if __name__ == "__main__":
    unittest.main()
