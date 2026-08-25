"""W6633 — the OCI reference worker image and its entry point.

The acceptance this file answers to:

  a reproducible recipe with an immutable base/image digest and explicit
  runtime user/entrypoint; a protected framed channel with bounded input and
  output and no ambient authority or engine access; scripted consent, decline,
  execution, cancellation and fault fixtures; inspection proving filesystem,
  user, capability and entrypoint posture with no secret or assignment
  material in a layer; and container-level negative tests proving CONSENT
  CANNOT REACH EXECUTION STATE.

The last two are answered here at the RECIPE and PROGRAM level -- what the
image will be and what the entry point does -- because those are facts this
suite can establish without a daemon. Driving a built image through a real
engine is the mutable half and is reported in the record as its own cut; the
gate this suite belongs to must not depend on somebody's daemon being up.
"""

import io
import json
import pathlib
import sys
import unittest

WORKER = (pathlib.Path(__file__).resolve().parents[3] / "worker")
sys.path.insert(0, str(WORKER))

import baton_worker                                          # noqa: E402
from baton_worker import (MAX_FRAME, OPERATIONS, POSTURES, PROTOCOL,  # noqa
                          WorkerFault, read_frame, serve, write_frame)
from scripted_agent import ScriptedAgent                     # noqa: E402

CONSENT = {"BATON_WORKER_POSTURE": "consent",
           "BATON_WORKER_CONTRACT": "do the thing",
           "BATON_WORKER_ROLE": "implementer"}
EXECUTION = {**CONSENT, "BATON_WORKER_POSTURE": "execution",
             "BATON_WORKER_ASSIGNMENT": "assignment-1",
             "BATON_WORKER_WORKSPACE": "/workspace",
             "BATON_WORKER_OUTPUT": "/workspace/out"}


def frames(*documents):
    payload = b""
    for document in documents:
        body = json.dumps(document).encode("utf-8")
        payload += str(len(body)).encode("ascii") + b"\n" + body
    return io.BytesIO(payload)


def answers(payload):
    stream = io.BytesIO(payload)
    found = []
    while True:
        one = read_frame(stream)
        if one is None:
            return found
        found.append(one)


def run(environment, *requests, agent=None):
    out = io.BytesIO()
    status = serve(frames(*requests), out, environment,
                   agent or ScriptedAgent())
    return status, answers(out.getvalue())


class TheChannelIsFramedAndBounded(unittest.TestCase):

    def test_a_frame_round_trips(self):
        out = io.BytesIO()
        write_frame(out, {"ok": True})
        self.assertEqual(answers(out.getvalue()), [{"ok": True}])

    def test_the_framing_is_length_prefixed_and_not_newline_delimited(self):
        """A newline is a byte an agent's output legitimately contains, and a
        protocol whose framing a payload can forge has no framing."""
        out = io.BytesIO()
        write_frame(out, {"recap": "line one\nline two"})
        self.assertEqual(answers(out.getvalue()),
                         [{"recap": "line one\nline two"}])

    def test_an_oversized_frame_is_refused_before_it_is_read(self):
        stream = io.BytesIO(str(MAX_FRAME + 1).encode("ascii") + b"\n")
        with self.assertRaises(WorkerFault) as caught:
            read_frame(stream)
        self.assertEqual(caught.exception.code, "protocol")
        self.assertEqual(stream.tell(), len(str(MAX_FRAME + 1)) + 1,
                         "the body was read despite the refusal")

    def test_a_header_that_never_ends_is_bounded_too(self):
        """A header is caller input, so the bound is on it as well as on the
        body -- otherwise a peer that sends no newline reads forever."""
        with self.assertRaises(WorkerFault):
            read_frame(io.BytesIO(b"9" * 4096))

    def test_malformed_frames_are_faults_rather_than_crashes(self):
        for what, payload in [("a header that is not a length", b"abc\n{}"),
                              ("a body that ends early", b"99\n{}"),
                              ("a body that is not JSON", b"2\nno"),
                              ("a body that is not an object", b"2\n[]")]:
            with self.subTest(what=what):
                with self.assertRaises(WorkerFault) as caught:
                    read_frame(io.BytesIO(payload))
                self.assertEqual(caught.exception.code, "protocol")

    def test_a_clean_end_of_input_is_an_answer(self):
        self.assertIsNone(read_frame(io.BytesIO(b"")))

    def test_our_own_answer_is_bounded_as_well(self):
        """An agent that produced an enormous recap must not make this program
        the thing that broke the channel."""
        class Loud:
            def consider(self, seen, request):
                return {"reason": "x" * (MAX_FRAME + 10)}

        status, given = run(CONSENT, {"operation": "consider"}, agent=Loud())
        self.assertEqual(given[0]["ok"], False)
        self.assertEqual(given[0]["code"], "bounds")


class ConsentCannotReachExecution(unittest.TestCase):
    """THE NEGATIVE TESTS THE TOPOLOGY EXISTS FOR."""

    def test_a_consent_container_is_not_asked_to_work(self):
        """Not "unknown operation" — `work` is a real operation this container
        is not entitled to, and saying so is what makes this meaningful."""
        status, given = run(CONSENT, {"operation": "work", "task": "t"})
        self.assertEqual(given[0]["ok"], False)
        self.assertEqual(given[0]["code"], "posture")
        self.assertIn("not asked to 'work'", given[0]["message"])

    def test_there_is_no_message_that_promotes_a_consent_worker(self):
        """Promotion is what a fresh container after activation replaces."""
        for operation in ("promote", "activate", "execution", "work",
                          "escalate", "become"):
            with self.subTest(operation=operation):
                status, given = run(CONSENT, {"operation": operation})
                self.assertEqual(given[0]["ok"], False)
                self.assertEqual(given[0]["code"], "posture")

    def test_a_consent_container_carrying_assignment_material_refuses(self):
        """It means the manager built the wrong container, and continuing
        would hide that."""
        for name in ("BATON_WORKER_ASSIGNMENT", "BATON_WORKER_WORKSPACE",
                     "BATON_WORKER_OUTPUT"):
            with self.subTest(name=name):
                status, given = run({**CONSENT, name: "/somewhere"},
                                    {"operation": "describe"})
                self.assertEqual(given[0]["ok"], False)
                self.assertEqual(given[0]["code"], "posture")
                self.assertIn(name, given[0]["message"])

    def test_assignment_material_cannot_arrive_inside_a_consent_frame(self):
        """Environment filtering is not enough: the framed request is the
        other input boundary into the same consent process."""
        status, given = run(
            CONSENT,
            {"operation": "consider", "assignment": "assignment-1",
             "workspace": "/workspace", "output": "/workspace/out"})
        self.assertEqual(given[0]["ok"], False)
        self.assertIn(given[0]["code"], ("posture", "protocol"))

    def test_the_posture_is_checked_on_every_operation(self):
        """A check that ran once at start is a check a later message walks
        past."""
        status, given = run(CONSENT,
                            {"operation": "describe"},
                            {"operation": "consider"},
                            {"operation": "work", "task": "t"},
                            {"operation": "consider"})
        self.assertEqual([one["ok"] for one in given],
                         [True, True, False, True])

    def test_a_posture_the_image_does_not_define_never_runs(self):
        """An image that defaulted to a posture would run as `execution` when
        the manager forgot to say, and forgetting is when it matters."""
        for posture in (None, "", "admin", "EXECUTION", "consent "):
            with self.subTest(posture=repr(posture)):
                environment = dict(CONSENT)
                if posture is None:
                    del environment["BATON_WORKER_POSTURE"]
                else:
                    environment["BATON_WORKER_POSTURE"] = posture
                # MIGRATED: this asserted the fault was RAISED out of
                # `serve`. The reviewer's case requires it to arrive as a
                # frame like every other fault, and that is right -- a worker
                # that dies leaves the manager waiting for a runtime that is
                # gone. The refusal is unchanged; only its delivery is.
                out = io.BytesIO()
                status = serve(frames({"operation": "describe"}), out,
                               environment, ScriptedAgent())
                self.assertEqual(status, 1)
                self.assertEqual(answers(out.getvalue())[0]["code"], "posture")

    def test_an_execution_container_is_not_asked_to_consent(self):
        """The exclusion runs both ways: consent is decided once, in its own
        container, and an execution worker re-deciding it would be the
        promotion this topology forbids, arriving from the other end."""
        status, given = run(EXECUTION, {"operation": "consider"})
        self.assertEqual(given[0]["ok"], False)
        self.assertEqual(given[0]["code"], "posture")


class TheScriptedFixtures(unittest.TestCase):

    def test_consent_accepts_and_declines_deterministically(self):
        status, accepted = run(CONSENT, {"operation": "consider"})
        self.assertEqual(accepted[0]["answer"]["decision"], "accept")
        status, declined = run({**CONSENT,
                                "BATON_WORKER_CONTRACT": "please decline this"},
                               {"operation": "consider"})
        self.assertEqual(declined[0]["answer"]["decision"], "decline")

    def test_a_consent_answer_names_nothing_it_cannot_see(self):
        status, given = run(CONSENT, {"operation": "consider"})
        self.assertEqual(sorted(given[0]["answer"]),
                         ["contract_digest", "decision", "reason"])

    def test_execution_completes_and_recaps(self):
        status, given = run(EXECUTION, {"operation": "work", "task": "build"})
        answer = given[0]["answer"]
        self.assertEqual(answer["disposition"], "completed")
        self.assertEqual(answer["workspace"], "/workspace")
        self.assertIn("build", answer["recap"])

    def test_the_same_request_produces_the_same_bytes(self):
        """DETERMINISTIC is what makes a reproducibility case possible."""
        first = run(EXECUTION, {"operation": "work", "task": "build"})
        second = run(EXECUTION, {"operation": "work", "task": "build"})
        self.assertEqual(first, second)

    def test_an_agent_fault_is_a_frame_and_carries_no_traceback(self):
        """A traceback would carry paths from inside the image out through the
        channel, and a worker that died would leave the manager waiting for a
        runtime that is gone."""
        status, given = run(EXECUTION, {"operation": "work"})
        self.assertEqual(given[0]["ok"], False)
        self.assertEqual(given[0]["code"], "agent")
        self.assertEqual(given[0]["message"], "the agent failed: ValueError")

    def test_a_cancelled_channel_ends_cleanly(self):
        """Cancellation reaches this program as its input ending. It exits 0
        rather than faulting: the manager stopped it on purpose, and a fault
        would report its own cancellation as a problem."""
        status, given = run(EXECUTION)
        self.assertEqual((status, given), (0, []))

    def test_a_broken_frame_ends_the_session_after_reporting_it(self):
        out = io.BytesIO()
        status = serve(io.BytesIO(b"abc\n"), out, EXECUTION, ScriptedAgent())
        self.assertEqual(status, 1)
        self.assertEqual(answers(out.getvalue())[0]["code"], "protocol")

    def test_a_startup_posture_fault_is_a_frame_and_not_a_crash(self):
        out = io.BytesIO()
        status = serve(frames({"operation": "describe"}), out,
                       {**CONSENT, "BATON_WORKER_POSTURE": "admin"},
                       ScriptedAgent())
        self.assertEqual(status, 1)
        self.assertEqual(answers(out.getvalue())[0]["code"], "posture")


class TheRecipeIsInspectableWithoutADaemon(unittest.TestCase):
    """What the image WILL be, asserted from the recipe.

    A built image proves this too, and more slowly, on a host with a daemon.
    These are the properties the gate can hold every time.
    """

    def setUp(self):
        self.recipe = (WORKER / "Dockerfile").read_text(encoding="utf-8")
        self.lines = [line.strip() for line in self.recipe.splitlines()
                      if line.strip() and not line.strip().startswith("#")]

    def test_the_base_is_pinned_by_digest_and_never_by_tag(self):
        base = [line for line in self.lines if line.startswith("FROM ")]
        self.assertEqual(len(base), 1, "one base, so one thing to pin")
        self.assertRegex(base[0], r"^FROM \S+@sha256:[0-9a-f]{64}$")
        self.assertNotIn(":latest", self.recipe)

    def test_the_runtime_user_is_a_fixed_non_root_numeric_id(self):
        self.assertIn("USER 65532:65532", self.lines)

    def test_the_entrypoint_is_exec_form_with_no_shell(self):
        """No shell in the process tree, so nothing interprets a signal or a
        metacharacter on the worker's behalf."""
        entry = [line for line in self.lines if line.startswith("ENTRYPOINT")]
        self.assertEqual(entry,
                         ['ENTRYPOINT ["python3", "/opt/baton/baton_worker.py"]'])

    def test_the_image_defaults_to_no_posture(self):
        self.assertNotIn("BATON_WORKER_POSTURE=", self.recipe.replace(
            "There is deliberately no `ENV BATON_WORKER_POSTURE`.", ""))

    def test_the_image_announces_no_network_or_health_surface(self):
        for directive in ("EXPOSE", "VOLUME", "HEALTHCHECK"):
            with self.subTest(directive=directive):
                self.assertEqual(
                    [line for line in self.lines
                     if line.startswith(directive)], [])

    def test_no_secret_or_assignment_material_enters_a_layer(self):
        """Only the two program files are copied in, so a layer cannot carry
        an assignment, a bearer or a workspace."""
        copied = [line for line in self.lines if line.startswith("COPY")]
        self.assertEqual(
            copied,
            ["COPY baton_worker.py /opt/baton/baton_worker.py",
             "COPY scripted_agent.py /opt/baton/scripted_agent.py"])
        for line in self.lines:
            if line.startswith("ENV"):
                self.assertNotIn("BATON_WORKER_", line)

    def test_the_user_agrees_with_the_adapters_own_restriction(self):
        """Two places agreeing because they were written from one decision."""
        from baton_v12.worker_manager.oci import RESTRICTIONS

        user = dict((flag, value) for flag, value in RESTRICTIONS)["--user"]
        self.assertIn(f"USER {user}", self.lines)


class TheWorkerHoldsNoneOfTheManagersCapabilities(unittest.TestCase):

    def test_the_entry_point_imports_nothing_from_the_distribution(self):
        """A worker that could import the manager is a worker one bug away
        from holding the manager's capabilities.

        Checked structurally rather than trusted: "we did not import it" is a
        property somebody will break by accident.
        """
        import ast

        for name in ("baton_worker.py", "scripted_agent.py"):
            with self.subTest(name=name):
                tree = ast.parse((WORKER / name).read_text(encoding="utf-8"))
                imported = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        imported.update(alias.name.split(".")[0]
                                        for alias in node.names)
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        imported.add(node.module.split(".")[0])
                self.assertNotIn("baton_v12", imported)
                self.assertFalse(
                    imported & {"socket", "subprocess", "urllib", "http",
                                "sqlite3", "ssl", "ftplib", "telnetlib"},
                    "the worker reaches for a network, a database or a "
                    "process; it has none of those")

    def test_the_protocol_name_is_the_only_thing_it_announces(self):
        status, given = run(CONSENT, {"operation": "describe"})
        self.assertEqual(given[0]["answer"]["protocol"], PROTOCOL)
        self.assertEqual(given[0]["answer"]["posture"], "consent")
        self.assertEqual(given[0]["answer"]["operations"],
                         list(OPERATIONS["consent"]))

    def test_the_two_postures_are_the_whole_set(self):
        self.assertEqual(POSTURES, ("consent", "execution"))
        self.assertEqual(sorted(OPERATIONS), ["consent", "execution"])


if __name__ == "__main__":
    unittest.main()
