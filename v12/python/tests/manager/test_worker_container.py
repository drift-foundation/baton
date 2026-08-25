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

import json
import os
import pathlib
import subprocess
import unittest
import uuid
from unittest.mock import patch

from baton_v12.worker_manager.oci import RESTRICTIONS

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
        calls = []
        with patch(f"{__name__}.engine", self.recording_engine(calls)):
            original = getattr(ContainerCase, "platform", None)
            ContainerCase.platform = "linux/amd64"
            try:
                ContainerCase.build("baton-w6633-test:cache-probe")
            finally:
                if original is None:
                    del ContainerCase.platform
                else:
                    ContainerCase.platform = original
        self.assertIn("--no-cache", calls[0],
                      "the alleged independent rebuild can be a cache hit")


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
        """One EXECUTION of the pinned recipe for the named platform.

        Fourth review [P1]: the "independent" rebuild reused the builder
        cache, so equal image ids proved cache reuse rather than two
        executions arriving at one artefact. `--no-cache` is unconditional
        rather than a keyword a caller may relax — the same reasoning the
        adapter's restriction table gives for its own flags, and it means
        every image this gate inspects was built rather than attached to
        somebody's earlier result. The recipe is a pinned base plus two
        `COPY`s, so an uncached build costs seconds.
        """
        engine("build", "--no-cache", "--platform", cls.platform,
               "--tag", tag, "--file", str(WORKER / "Dockerfile"),
               str(WORKER), timeout=900)

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

    def talk(self, environment, *requests, timeout=120):
        """Run one container, speak the framed channel, read what it says."""
        name = self.container()
        arguments = restricted("run", "--interactive", "--rm",
                               "--name", name)
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
EXECUTION = {"BATON_WORKER_POSTURE": "execution",
             "BATON_WORKER_SESSION": EXECUTION_SESSION,
             "BATON_WORKER_CONTRACT": "do the thing",
             "BATON_WORKER_ROLE": "implementer",
             "BATON_WORKER_ASSIGNMENT": "assignment-1",
             "BATON_WORKER_WORKSPACE": "/workspace",
             "BATON_WORKER_OUTPUT": "/workspace/out"}


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
        """REPRODUCIBLE, and what is compared is measured rather than assumed.

        Re-review [P1] asked for a rebuild; fourth review [P1] observed that
        the rebuild reused the builder cache, so equal ids proved cache reuse.
        `--no-cache` fixes that and CHANGES WHAT CAN BE COMPARED, which is
        worth stating plainly rather than working around:

          the image ID is the digest of the image CONFIG, and the config
          carries a `Created` timestamp the classic builder stamps from the
          wall clock. Two genuinely independent builds therefore have two ids
          BY CONSTRUCTION. Measured on docker 29.1.3: with `--no-cache` the
          ids differ and every `RootFS` layer is identical, and neither
          `SOURCE_DATE_EPOCH` nor a build-arg changes that on this engine,
          which has no buildx.

        So this compares the artefact rather than the receipt: every layer
        digest -- content-addressed, and the actual bytes a worker runs -- and
        the applied configuration. That is the property the acceptance needs
        (two executions of the recipe produce one worker) and it is one this
        engine can actually establish. `test_the_reproducibility_build_does_
        not_reuse_builder_cache` holds the cache isolation itself.

        The claim stays available because the recipe is a pinned base plus two
        `COPY`s and metadata, with deliberately no package manager and no
        network client. A recipe that installed anything could not make it,
        and this is where that would show up.
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

    def test_the_image_id_is_a_receipt_and_not_the_artefact(self):
        """The measurement the case above rests on, kept as its own case so a
        reader does not have to take the docstring's word for it.

        If a later engine DOES make ids reproducible, this fails and the
        comparison above can be strengthened -- which is the right way round
        for a claim that is currently limited by the tooling.
        """
        again = self.rebuild()
        first = self.inspected()
        self.assertNotEqual(again["Id"], first["Id"])
        self.assertNotEqual(again["Created"], first["Created"])
        self.assertEqual(again["RootFS"]["Layers"],
                         first["RootFS"]["Layers"],
                         "the ids differ for a reason other than the clock")

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
        self.assertEqual(seen["opt"],
                         ["baton_worker.py", "scripted_agent.py"])
        self.assertIs(seen["manager"], False,
                      "the manager package is importable inside the worker")
        self.assertEqual((seen["uid"], seen["gid"]), (65532, 65532))

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
        status, given = self.talk(EXECUTION,
                                  ask("work", EXECUTION_SESSION, task="build"))
        self.assertEqual(status, 0)
        answer = given[0]["answer"]
        self.assertEqual(sorted(answer),
                         ["disposition", "recap", "workspace"])
        self.assertEqual(answer["disposition"], "completed")

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
        status, given = self.talk(EXECUTION)
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
