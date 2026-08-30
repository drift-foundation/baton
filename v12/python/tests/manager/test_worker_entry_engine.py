"""W39356 — the worker-entry transport, asked of a REAL daemon.

`test_worker_entry.py` proves what the manager COMPOSED and drives the image's
own program over a pipe pair in this process. That is a strong proof of the
FRAMING and it cannot prove the one thing this checkpoint's acceptance is
actually about: that Docker applies the vector. A pipe is a pipe whether or not
`docker exec` would have given us one.

THE ACCEPTANCE SENTENCE THIS ANSWERS: *one real container completes a
correlated worker-entry conversation through exec, returns its own status,
preserves stderr separation and writes through the inherited workspace group.*

Four separate facts live in that sentence and each one has failed differently
in this campaign before:

  THE CONVERSATION HAPPENS AT ALL. The accepted start is `--detach` with no
  stdin, so the worker reads EOF and exits before anything can speak to it.
  The interactive operand is what holds the channel open, and this is where
  that stops being an argv assertion.
  THE SESSION RETURNS ITS OWN STATUS. `docker exec` answers for the exec'd
  process, not for the container -- which is the whole reason the transport
  reads a status at all.
  STDERR STAYS APART FROM STDOUT. Answers are stdout and diagnostics are
  stderr; a tty would merge them and a merged stream lets a diagnostic be read
  as a frame. There is no `--tty`, and this asks the daemon rather than the
  argv.
  THE WORKER WRITES. W33936's supplementary group reaches an exec session by
  inheritance rather than by anything this transport composes, and that was
  measured on a probe before it was relied on. Here it is proved through the
  real arc: the agent writes a declared output and the host reads it back.

IT FAILS RATHER THAN SKIPS WITHOUT DOCKER, inheriting the lifecycle gate's
rule: a required integration that quietly passes because it could not run is
the failure mode this campaign is built against. Podman is additive and skips.
"""

import json
import os
import subprocess
import threading
import unittest
import uuid

from baton_v12.worker_manager import launch, workspaces
from baton_v12.worker_manager.oci import EnginePort, OciAdapter
from baton_v12.worker_manager.worker_entry import ChannelPort, converse

from . import input_roots
from .test_lifecycle_composition import Lifecycle

WORK_REF = {"authority_uuid": "43c55d4b" + "0" * 24,
            "work_id": "43c55d4b-W39356"}
WHO = "baton.claude"
PROFILE = "sha256:" + "b" * 64
POLICY = "sha256:" + "d" * 64
ADAPTER = "sha256:" + "c" * 64
PROGRAM = ["python3", "/opt/baton/baton_worker.py"]


class Session:
    """The real channel: one `docker exec` process, driven as a stream.

    THIS IS THE OBJECT THE PACKAGE DELIBERATELY DOES NOT CONTAIN. Every
    outward act in the Worker Manager crosses an injected capability, and the
    thing that actually spawns a process belongs to the deployment -- which
    here is this suite. What the module owns is the framing and the rules; what
    this owns is a pipe.

    STDERR IS DRAINED BY A THREAD from the moment the process starts. A
    container that writes more diagnostics than a pipe buffer holds would
    otherwise block in `write` while this waited for stdout, and the two would
    wait for each other -- which is a hang that looks exactly like a worker
    that stopped answering.
    """

    def __init__(self, argv, *, seconds):
        self._seconds = seconds
        self._process = subprocess.Popen(argv, stdin=subprocess.PIPE,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
        self._errors = []
        self._pump = threading.Thread(target=self._drain, daemon=True)
        self._pump.start()

    def _drain(self):
        for chunk in iter(lambda: self._process.stderr.read(4096), b""):
            self._errors.append(chunk)

    def send(self, payload):
        self._process.stdin.write(payload)
        self._process.stdin.flush()

    def receive(self, count):
        return self._process.stdout.read1(count)

    def close_input(self):
        if not self._process.stdin.closed:
            self._process.stdin.close()

    def finish(self):
        self.close_input()
        status = self._process.wait(timeout=self._seconds)
        self._pump.join(self._seconds)
        self._process.stdout.close()
        self._process.stderr.close()
        return {"status": status,
                "stderr": b"".join(self._errors).decode("utf-8", "replace")}


class OneRealContainerAnswersTheTransport(Lifecycle):

    def setUp(self):
        super().setUp()
        self.attempt = f"attempt-{uuid.uuid4().hex[:10]}"
        self.spoken = []

    def channel_port(self):
        def open_session(argv, *, seconds):
            self.spoken.append(list(argv))
            return Session(argv, seconds=seconds)

        return ChannelPort(open_session)

    def running(self):
        """One started, interactive, real container over the reference image.

        Composed through the ACCEPTED operations -- the allocation, the input
        root, the launch delivery and `OciAdapter.start` -- rather than by
        calling `docker run` here, because a transport proved against a
        container this suite started by hand would be proved against a
        container the manager does not compose.
        """
        given, assignment = input_roots.documents(
            work_ref=dict(WORK_REF), participant=WHO, generation=1,
            runtime_attempt_id=self.attempt, policy_digest=POLICY,
            profile_digest=PROFILE)
        roots = workspaces.assignment_workspace(self.group, self.storage,
                                                self.attempt)
        workspaces.compose_input_root(
            roots["inputs"], given, assignment,
            assignment=dict(assignment["assignment_ref"]),
            runtime_attempt_id=self.attempt)
        home = os.path.join(self.home, f"launch-{self.attempt}")
        os.makedirs(home, exist_ok=True)
        delivery = launch.materialize(
            home, attempt_id=self.attempt,
            session=f"session-{self.attempt}",
            contract="prove the worker-entry transport", role="implementer")
        self.addCleanup(launch.discard, delivery.root)
        adapter = OciAdapter(
            self.engine, EnginePort(self.spawn),
            identity={"image_digest": self.image_digest,
                      "profile_digest": PROFILE, "policy_digest": POLICY,
                      "adapter_digest": ADAPTER},
            assignment_roots=dict(roots), posture="execution",
            # THE WORKER'S OWN FIXED OUTPUT PATH. `baton_worker` writes
            # declared outputs under `/output`, so a workspace bound anywhere
            # else is a workspace the agent cannot reach -- which is the
            # mismatch W38956's revalidation recorded against the lifecycle
            # fixture's `/workspace` spelling.
            mounts=[{"source": roots["inputs"], "target": "/input",
                     "writable": False},
                    {"source": roots["workspace"], "target": "/output",
                     "writable": True}],
            workspace_group=self.group,
            launch_delivery=delivery,
            interactive=True)
        started = adapter.start({
            "labels": self.labels_for(), "operation_id": f"start:{self.attempt}",
            "input_root": roots["inputs"]})
        self.assertIsNotNone(started["runtime_id"], started)
        return started["runtime_id"], roots, given, delivery

    def labels_for(self):
        from .test_offers import PRINCIPAL, SCOPE
        return {"runtime_attempt_id": self.attempt,
                "authority_uuid": WORK_REF["authority_uuid"],
                "work_id": WORK_REF["work_id"], "participant": WHO,
                "generation": 1, "principal": PRINCIPAL,
                "effective_scope": SCOPE, "profile_digest": PROFILE,
                "policy_digest": POLICY, "adapter_digest": ADAPTER}

    def talk(self, runtime_id, session, operations, ids, seconds=120):
        return converse(self.channel_port(), engine=self.engine,
                        runtime_id=runtime_id, program=PROGRAM,
                        session=session, operations=operations,
                        operation_ids=ids, seconds=seconds)

    # -- the acceptance ------------------------------------------------------

    def test_a_real_container_answers_describe_and_work_through_exec(self):
        """THE WHOLE ACCEPTANCE SENTENCE, in one case.

        Two correlated operations in one exec session against a container this
        manager started detached and interactive, the session's own clean
        status, an untouched stderr, and a declared output the agent wrote
        through the inherited workspace group and the host can read back.
        """
        runtime_id, roots, given, delivery = self.running()
        answered = self.talk(runtime_id, delivery.document["session"],
                             ["describe", "work"],
                             [f"op-1-{self.attempt}", f"op-2-{self.attempt}"])
        self.assertEqual(answered["ending"], "answered", answered)
        # THE SESSION'S OWN STATUS, which is the exec'd process's rather than
        # the container's -- the container is still up at this point.
        self.assertEqual(answered["status"], 0, answered)
        self.assertEqual([one["operation"] for one in answered["answers"]],
                         ["describe", "work"])
        # THE ARGV THAT CROSSED, asserted where it actually crossed.
        self.assertEqual(
            self.spoken[-1],
            [self.engine, "exec", "--interactive", runtime_id] + PROGRAM)

        described = answered["answers"][0]["answer"]
        self.assertEqual(described["protocol"], "baton.worker-entry/1")
        self.assertEqual(described["launch"],
                         ["contract", "role", "schema", "session"])

        worked = answered["answers"][1]["answer"]
        self.assertEqual(worked["disposition"], "completed")
        declared = given["outputs"][0]
        self.assertEqual(worked["outputs"], [declared["name"]])

        # THE WORKER REALLY WROTE, AND THE HOST REALLY READS IT. This is the
        # inherited supplementary group proved through the arc rather than on
        # a probe: an exec session that did not carry it could not have
        # created anything under the `02770` manager-owned workspace.
        produced = os.path.join(roots["workspace"], declared["path"])
        self.assertTrue(os.path.isdir(produced), produced)
        envelope = os.path.join(roots["workspace"], "output.json")
        self.assertTrue(os.path.isfile(envelope), envelope)
        with open(envelope, encoding="utf-8") as handle:
            published = json.load(handle)
        self.assertEqual(published["schema"],
                         "baton.worker-manifest/completion")
        self.assertEqual(published["disposition"], "completed")
        # AND THE ENVELOPE NAMES THIS ASSIGNMENT, copied from the input root
        # rather than composed by the worker.
        self.assertEqual(published["assignment_ref"]["work_ref"],
                         dict(WORK_REF))
        # THE GROUP IS THE DEPLOYMENT'S CONFIGURED ONE, which is the half of
        # this that the mechanism actually provides and the half the
        # acceptance names: the setgid workspace put what the worker created
        # into the group the manager holds, so the manager can reach it.
        held = os.stat(produced)
        self.assertEqual(held.st_gid, self.group.gid)
        self.assertTrue(os.access(produced, os.R_OK | os.X_OK), produced)
        # THE HOST-SIDE UID IS DELIBERATELY NOT ASSERTED, and the measurement
        # is why rather than a hedge. Inside the container the worker is
        # exactly `65532:65532` -- `--user` fixes it and the image asserts it.
        # What the HOST sees for the same file depends on the daemon's uid
        # mapping: on this development host `docker info` reports no
        # `userns` security option and the host still sees uid 65534, the
        # kernel's overflow id, for a file a container uid 65532 created.
        #
        # So a case pinning 65532 here would be pinning a deployment's mapping
        # under the name of this transport's contract, and would fail on a
        # correctly working host for a reason that has nothing to do with the
        # channel. What this arc is entitled to require is that the write
        # HAPPENED and that the manager can read it, which is what the two
        # assertions above say. The fixed runtime identity is W6632's property
        # and `test_worker_container` is where it is held.
        self.assertNotEqual(held.st_uid, os.getuid(),
                            "the worker's material is not the manager's own; "
                            "if it were, nothing would have crossed a "
                            "container boundary")

    def test_stderr_stays_apart_from_the_answers(self):
        """Asked of the DAEMON, not of the absence of `--tty` in an argv.

        A tty would merge the two streams and let a diagnostic be read as a
        frame. The worker writes nothing to stderr on a clean run, so what this
        establishes is that the answers arrived on stdout and stderr came back
        separately and empty -- a merged stream would have put the frames in
        both or the diagnostics in the frames.
        """
        runtime_id, _roots, _given, delivery = self.running()
        answered = self.talk(runtime_id, delivery.document["session"],
                             ["describe"], [f"op-{self.attempt}"])
        self.assertEqual(answered["ending"], "answered", answered)
        self.assertEqual(answered["stderr"], "")
        self.assertNotIn("--tty", self.spoken[-1])

    def test_a_frame_for_another_session_is_refused_by_the_real_worker(self):
        """The binding holds at the far end of a real container too."""
        runtime_id, _roots, _given, delivery = self.running()
        answered = self.talk(runtime_id, "session-somebody-else",
                             ["describe"], [f"op-{self.attempt}"])
        self.assertEqual(answered["ending"], "faulted", answered)
        self.assertEqual(answered["answers"][0]["code"], "session")

    def test_an_exec_against_a_runtime_that_is_gone_is_lost(self):
        """Transport loss over a real daemon, and it is NOT runtime absence.

        The container is removed first, so the engine cannot open the session
        at all. `lost` is the whole of what may be concluded: whether the
        runtime is absent is `observe`'s question, answered by asking the
        engine rather than by failing to reach it.
        """
        runtime_id, _roots, _given, delivery = self.running()
        subprocess.run([self.engine, "rm", "--force", runtime_id],
                       capture_output=True, timeout=180)
        answered = self.talk(runtime_id, delivery.document["session"],
                             ["describe"], [f"op-{self.attempt}"], seconds=60)
        self.assertIn(answered["ending"], ("lost", "faulted"))
        self.assertEqual(answered["ending"], "lost", answered)
        self.assertEqual(answered["answers"], [])

    def test_the_interactive_start_is_what_makes_the_container_reachable(self):
        """The other half of the same fact, and the reason the operand exists.

        A container started WITHOUT the interactive channel reads EOF on a
        closed stdin and exits at once, so there is nothing to exec into. That
        is the accepted default and it is correct for a runtime nobody speaks
        to -- this is what it costs, measured rather than asserted.
        """
        given, assignment = input_roots.documents(
            work_ref=dict(WORK_REF), participant=WHO, generation=1,
            runtime_attempt_id=self.attempt, policy_digest=POLICY,
            profile_digest=PROFILE)
        roots = workspaces.assignment_workspace(self.group, self.storage,
                                                self.attempt)
        workspaces.compose_input_root(
            roots["inputs"], given, assignment,
            assignment=dict(assignment["assignment_ref"]),
            runtime_attempt_id=self.attempt)
        home = os.path.join(self.home, f"launch-quiet-{self.attempt}")
        os.makedirs(home, exist_ok=True)
        delivery = launch.materialize(
            home, attempt_id=self.attempt,
            session=f"session-{self.attempt}",
            contract="prove the non-interactive default", role="implementer")
        self.addCleanup(launch.discard, delivery.root)
        adapter = OciAdapter(
            self.engine, EnginePort(self.spawn),
            identity={"image_digest": self.image_digest,
                      "profile_digest": PROFILE, "policy_digest": POLICY,
                      "adapter_digest": ADAPTER},
            assignment_roots=dict(roots), posture="execution",
            mounts=[{"source": roots["inputs"], "target": "/input",
                     "writable": False},
                    {"source": roots["workspace"], "target": "/output",
                     "writable": True}],
            workspace_group=self.group, launch_delivery=delivery)
        started = adapter.start({
            "labels": self.labels_for(),
            "operation_id": f"quiet:{self.attempt}",
            "input_root": roots["inputs"]})
        runtime_id = started["runtime_id"]
        self.assertNotIn("--interactive",
                         next(argv for argv in self.engine_calls
                              if "run" in argv))
        self.settled(runtime_id)
        answered = self.talk(runtime_id, delivery.document["session"],
                             ["describe"], [f"op-{self.attempt}"], seconds=60)
        self.assertEqual(answered["ending"], "lost", answered)
        self.assertEqual(answered["answers"], [])


class DockerWorkerEntry(OneRealContainerAnswersTheTransport,
                        unittest.TestCase):
    engine = "docker"
    required = True


class PodmanWorkerEntry(OneRealContainerAnswersTheTransport,
                        unittest.TestCase):
    engine = "podman"
    required = False
