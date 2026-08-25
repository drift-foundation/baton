"""W6633 — the OCI reference worker image and its entry point.

The acceptance this file answers to:

  a reproducible recipe with an immutable base/image digest and explicit
  runtime user/entrypoint; a protected framed channel with bounded input and
  output and no ambient authority or engine access; scripted consent, decline,
  execution and fault fixtures; and the approved `baton.worker-entry/1`
  envelope — every frame bound to an exact posture-session identity with a
  one-use operation id, closed per operation, and answered in one correlated
  shape.

WHAT IS HERE AND WHAT IS NEXT DOOR. This suite establishes what the image WILL
be and what the entry point DOES, from the recipe and the program. The built
image, the real containers, and the manager's actual cancellation path are in
`test_worker_container.py`, which drives a daemon — and which FAILS rather than
skips when there is none, because a required gate that quietly passes for being
unable to run is the failure mode this distribution is built against.
"""

import ast
import io
import json
import pathlib
import sys
import unittest

WORKER = (pathlib.Path(__file__).resolve().parents[3] / "worker")
sys.path.insert(0, str(WORKER))

import baton_worker                                          # noqa: E402
from baton_worker import (ANSWER_MEMBERS, COMMON_MEMBERS, MAX_FRAME,  # noqa
                          MAX_IDENTITY, OPERATIONS, POSTURES, PROTOCOL,
                          REQUEST_MEMBERS, Uncorrelated, WorkerFault,
                          read_frame, serve, write_frame)
from scripted_agent import ScriptedAgent                     # noqa: E402

# THE TWO SESSIONS ARE DIFFERENT, and that is the topology rather than the
# fixture being tidy: an execution session is never a continuation or a
# promotion of a consent one, so the manager mints a separate identity for the
# separate container.
CONSENT_SESSION = "session-consent-1"
EXECUTION_SESSION = "session-execution-1"

CONSENT = {"BATON_WORKER_POSTURE": "consent",
           "BATON_WORKER_SESSION": CONSENT_SESSION,
           "BATON_WORKER_CONTRACT": "do the thing",
           "BATON_WORKER_ROLE": "implementer"}
EXECUTION = {**CONSENT, "BATON_WORKER_POSTURE": "execution",
             "BATON_WORKER_SESSION": EXECUTION_SESSION,
             "BATON_WORKER_ASSIGNMENT": "assignment-1",
             "BATON_WORKER_WORKSPACE": "/workspace",
             "BATON_WORKER_OUTPUT": "/workspace/out"}

_minted = iter(range(1, 10_000))


def ask(operation, session, **members):
    """One request in the approved envelope, with a fresh operation id.

    Fresh by default because an id is consumed once per session: a fixture
    that reused one would be driving the replay fence by accident and calling
    it something else.
    """
    return {"protocol": PROTOCOL, "session": session,
            "operation_id": f"op-{next(_minted)}", "operation": operation,
            **members}


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


def consent(operation="describe", **members):
    return ask(operation, CONSENT_SESSION, **members)


def execution(operation="describe", **members):
    return ask(operation, EXECUTION_SESSION, **members)


# -- the envelope ------------------------------------------------------------

class TheEnvelopeBindsEveryFrame(unittest.TestCase):
    """Exclusive stdio is transport isolation, not message identity.

    Every case here drives a frame that is well-formed as a frame and wrong as
    a REQUEST, and requires the refusal to arrive correlated — so a sender can
    always match the answer to what it asked.
    """

    def refusing(self, code, request, environment=None):
        status, given = run(environment or CONSENT, request)
        self.assertEqual(len(given), 1, given)
        self.assertIs(given[0]["ok"], False)
        self.assertEqual(given[0]["code"], code, given[0]["message"])
        return given[0]

    def test_a_well_formed_request_is_answered_and_correlated(self):
        request = consent("describe")
        status, given = run(CONSENT, request)
        self.assertEqual(status, 0)
        self.assertEqual(sorted(given[0]),
                         ["answer", "ok", "operation_id", "protocol",
                          "session"])
        for member in ("protocol", "session", "operation_id"):
            self.assertEqual(given[0][member], request[member], member)

    def test_a_fault_carries_the_same_identity_and_nothing_else(self):
        answer = self.refusing("posture", consent("work", task="x"))
        self.assertEqual(sorted(answer),
                         ["code", "message", "ok", "operation_id", "protocol",
                          "session"])

    def test_a_frame_naming_another_session_is_refused(self):
        """A worker answers only the session the manager minted for it."""
        self.refusing("session", ask("describe", "session-somebody-else"))

    def test_a_consent_worker_refuses_the_execution_sessions_frames(self):
        """The cross-posture case, which is the one the topology is about: an
        execution session is never a continuation of a consent one, so a frame
        minted for the other container is refused even though the OPERATION
        would be legal here."""
        self.refusing("session", ask("describe", EXECUTION_SESSION))
        self.refusing("session", ask("describe", CONSENT_SESSION),
                      environment=EXECUTION)

    def test_a_frame_speaking_another_protocol_is_refused(self):
        self.refusing("protocol",
                      {**consent("describe"), "protocol": "baton.other/9"})

    def test_a_missing_identity_member_is_answered_by_no_frame_at_all(self):
        """The ruling forbids inventing an uncorrelated response shape, so a
        frame this program cannot read an identity out of gets no answer and a
        non-zero exit; the manager already owns the launched session and
        settles that from the engine."""
        for member in ("protocol", "session", "operation_id"):
            with self.subTest(missing=member):
                request = consent("describe")
                del request[member]
                status, given = run(CONSENT, request)
                self.assertEqual((status, given), (1, []))

    def test_an_identity_member_that_is_not_bounded_text_is_uncorrelatable(
            self):
        for what, value in [("null", None), ("a number", 7), ("empty", ""),
                            ("oversized", "x" * (MAX_IDENTITY + 1))]:
            with self.subTest(what=what):
                request = {**consent("describe"), "operation_id": value}
                status, given = run(CONSENT, request)
                self.assertEqual((status, given), (1, []))

    def test_an_operation_id_is_consumed_once_within_a_session(self):
        request = consent("describe")
        status, given = run(CONSENT, request, dict(request))
        self.assertIs(given[0]["ok"], True)
        self.assertIs(given[1]["ok"], False)
        self.assertEqual(given[1]["code"], "replay")
        self.assertEqual(given[1]["operation_id"], request["operation_id"])

    def test_an_id_that_reached_the_agent_is_spent_whatever_the_outcome(self):
        """"It failed, so you may send it again" is exactly the reasoning a
        replay fence exists to refuse: this program cannot know whether the
        first attempt's side effects happened."""
        class Angry:
            def work(self, seen, request):
                raise ZeroDivisionError("after doing half of it")

        request = execution("work", task="build")
        status, given = run(EXECUTION, request, dict(request), agent=Angry())
        self.assertEqual(given[0]["code"], "agent")
        self.assertEqual(given[1]["code"], "replay")

    def test_a_frame_refused_for_its_shape_never_spends_its_id(self):
        """The other side of the same rule, and the reason the fence sits
        where it does: a request that never reached the agent had no effect to
        be uncertain about, so a sender that corrects its frame may use the id
        it never spent."""
        broken = execution("work")
        status, given = run(EXECUTION, dict(broken),
                            {**broken, "task": "build"})
        self.assertEqual(given[0]["code"], "protocol")
        self.assertIs(given[1]["ok"], True)

    def test_a_missing_session_identity_produces_no_frame(self):
        """Without it nothing this program says could be matched to anything,
        which is the case the ruling hands to the Worker Manager."""
        without = {name: value for name, value in CONSENT.items()
                   if name != "BATON_WORKER_SESSION"}
        status, given = run(without, consent("describe"))
        self.assertEqual((status, given), (2, []))


# -- the closure is per operation --------------------------------------------

class TheClosureIsPerOperation(unittest.TestCase):
    """Closure one level coarser than the contract is closure over the wrong
    thing: an execution `describe` carrying `task` used to succeed, because
    some OTHER operation of that posture takes one."""

    def test_each_operation_names_exactly_its_own_members(self):
        self.assertEqual(REQUEST_MEMBERS["describe"], COMMON_MEMBERS)
        self.assertEqual(REQUEST_MEMBERS["consider"], COMMON_MEMBERS)
        self.assertEqual(REQUEST_MEMBERS["work"], COMMON_MEMBERS + ("task",))

    def test_describe_does_not_accept_another_operations_member(self):
        status, given = run(EXECUTION, execution("describe", task="build"))
        self.assertIs(given[0]["ok"], False)
        self.assertEqual(given[0]["code"], "protocol")
        self.assertIn("unexpected task", given[0]["message"])

    def test_an_unknown_member_is_refused_rather_than_ignored(self):
        status, given = run(CONSENT, consent("consider", assignment="a-1"))
        self.assertEqual(given[0]["code"], "protocol")
        self.assertIn("assignment", given[0]["message"])

    def test_a_missing_operation_member_is_named(self):
        request = execution("work")
        status, given = run(EXECUTION, request)
        self.assertEqual(given[0]["code"], "protocol")
        self.assertIn("missing task", given[0]["message"])

    def test_an_unknown_operation_is_refused_before_anything_else(self):
        status, given = run(CONSENT, consent("meditate"))
        self.assertEqual(given[0]["code"], "protocol")


# -- the answer is a boundary too --------------------------------------------

class TheAnswerIsValidatedBeforeItIsFramed(unittest.TestCase):
    """The agent is the least trusted thing inside this container, and an
    answer is what crosses out of it."""

    def answering(self, answer, operation="consider", environment=None):
        class Fixed:
            def consider(self, seen, request):
                return answer

            def work(self, seen, request):
                return answer

        request = ask(operation,
                      CONSENT_SESSION if operation == "consider"
                      else EXECUTION_SESSION,
                      **({"task": "build"} if operation == "work" else {}))
        status, given = run(environment or CONSENT, request, agent=Fixed())
        return given[0]

    def test_the_pinned_answer_sets_are_what_the_contract_names(self):
        self.assertEqual(ANSWER_MEMBERS["describe"],
                         ("protocol", "posture", "operations", "environment"))
        self.assertEqual(ANSWER_MEMBERS["consider"],
                         ("contract_digest", "decision", "reason"))
        self.assertEqual(ANSWER_MEMBERS["work"],
                         ("disposition", "workspace", "recap"))

    def test_an_answer_with_an_extra_member_never_becomes_a_frame(self):
        given = self.answering({"contract_digest": "sha256:x",
                                "decision": "accept", "reason": "fine",
                                "plan": "and also this"})
        self.assertEqual(given["code"], "answer")
        self.assertIn("unexpected plan", given["message"])

    def test_an_answer_missing_a_member_never_becomes_a_frame(self):
        given = self.answering({"decision": "accept", "reason": "fine"})
        self.assertEqual(given["code"], "answer")
        self.assertIn("missing contract_digest", given["message"])

    def test_an_answer_member_that_is_not_bounded_text_is_refused(self):
        given = self.answering({"contract_digest": "sha256:x",
                                "decision": {"nested": "object"},
                                "reason": "fine"})
        self.assertEqual(given["code"], "answer")

    def test_a_workspace_may_be_null_and_nothing_else_may(self):
        """Null is how a posture with no workspace SAYS so; absent and null are
        different documents and only one of them answers the question."""
        given = self.answering({"disposition": "completed", "workspace": None,
                                "recap": "done"}, operation="work",
                               environment=EXECUTION)
        self.assertIs(given["ok"], True)
        given = self.answering({"disposition": None, "workspace": None,
                                "recap": "done"}, operation="work",
                               environment=EXECUTION)
        self.assertEqual(given["code"], "answer")

    def test_the_scripted_work_answer_is_exactly_the_pinned_set(self):
        status, given = run(EXECUTION, execution("work", task="build"))
        self.assertEqual(sorted(given[0]["answer"]),
                         sorted(ANSWER_MEMBERS["work"]))


# -- a bootstrap fault is latched and correlated -----------------------------

class ABootstrapFaultIsLatchedAndCorrelated(unittest.TestCase):
    """The approved startup-correlation ruling. The framing loop is still
    operable, so the failure is answered through the ORDINARY shape after
    exactly one identity envelope — and it never reaches the agent."""

    def latched(self, environment):
        class Never:
            def consider(self, seen, request):
                raise AssertionError("a latched fault reached the agent")

            def work(self, seen, request):
                raise AssertionError("a latched fault reached the agent")

        out = io.BytesIO()
        status = serve(frames(ask("consider", environment.get(
            "BATON_WORKER_SESSION", "session-consent-1"))),
            out, environment, Never())
        return status, answers(out.getvalue())

    def test_an_invalid_posture_is_one_correlated_fault_and_a_non_zero_exit(
            self):
        for posture in (None, "", "admin", "EXECUTION", "consent "):
            with self.subTest(posture=posture):
                environment = dict(CONSENT)
                if posture is None:
                    del environment["BATON_WORKER_POSTURE"]
                else:
                    environment["BATON_WORKER_POSTURE"] = posture
                status, given = self.latched(environment)
                self.assertEqual(status, 1)
                self.assertEqual(len(given), 1)
                self.assertEqual(given[0]["code"], "posture")
                self.assertEqual(given[0]["session"], CONSENT_SESSION)
                self.assertEqual(given[0]["protocol"], PROTOCOL)

    def test_a_container_built_with_the_wrong_material_latches_too(self):
        for name in ("BATON_WORKER_ASSIGNMENT", "BATON_WORKER_WORKSPACE",
                     "BATON_WORKER_OUTPUT"):
            with self.subTest(name=name):
                status, given = self.latched({**CONSENT, name: "leaked"})
                self.assertEqual(status, 1)
                self.assertEqual(given[0]["code"], "posture")
                self.assertIn(name, given[0]["message"])

    def test_a_latched_fault_does_not_answer_another_sessions_envelope(self):
        """Startup correlation does not relax the common session binding.

        A pending bootstrap failure may be returned only after the one
        envelope has established this posture-specific container's identity;
        a frame minted for another session is still refused as such.
        """
        request = ask("consider", "session-somebody-else")
        status, given = run(
            {**CONSENT, "BATON_WORKER_POSTURE": "admin"}, request)
        self.assertEqual(status, 1)
        self.assertEqual(len(given), 1)
        self.assertEqual(given[0]["code"], "session")
        self.assertEqual(given[0]["session"], request["session"])

    def test_a_latched_fault_refuses_a_foreign_protocol_the_same_way(self):
        """The binding is protocol AND session, and both precede the latched
        answer. A container that failed to start is still a container this
        channel's contract applies to."""
        request = consent("consider")
        request["protocol"] = "baton.worker-entry/2"
        status, given = run(
            {**CONSENT, "BATON_WORKER_POSTURE": "admin"}, request)
        self.assertEqual(status, 1)
        self.assertEqual(len(given), 1)
        self.assertEqual(given[0]["code"], "protocol")

    def test_a_refused_binding_on_a_latched_container_still_answers_once(self):
        """The three properties the correction had to KEEP. Which fault a
        latched container names changed; that it writes exactly one frame,
        exits non-zero, and reaches no agent did not."""
        class Never:
            def consider(self, seen, request):
                raise AssertionError("a latched fault reached the agent")

            def work(self, seen, request):
                raise AssertionError("a latched fault reached the agent")

        out = io.BytesIO()
        status = serve(
            frames(ask("consider", "session-somebody-else"),
                   consent("consider")),
            out, {**CONSENT, "BATON_WORKER_POSTURE": "admin"}, Never())
        self.assertEqual(status, 1)
        given = answers(out.getvalue())
        self.assertEqual(len(given), 1, "more than one envelope was read")
        self.assertEqual(given[0]["code"], "session")

    def test_a_healthy_container_keeps_answering_after_a_foreign_frame(self):
        """The other half of the same move: lifting the binding out of
        `handle` must not turn an ordinary wrong-session refusal into the end
        of the channel. Only a LATCHED container stops."""
        status, given = run(EXECUTION,
                            ask("describe", "session-somebody-else"),
                            execution("describe"))
        self.assertEqual(status, 0)
        self.assertEqual([one["code"] for one in given[:1]], ["session"])
        self.assertEqual(len(given), 2)
        self.assertTrue(given[1]["ok"])
        self.assertEqual(given[1]["answer"]["posture"], "execution")

    def test_exactly_one_envelope_is_read_and_the_task_is_never_dispatched(
            self):
        """Reading the envelope grants no task, workspace, output, tool or
        agent capability."""
        class Never:
            def consider(self, seen, request):
                raise AssertionError("a latched fault reached the agent")

            def work(self, seen, request):
                raise AssertionError("a latched fault reached the agent")

        out = io.BytesIO()
        status = serve(frames(consent("consider"), consent("consider")),
                       out, {**CONSENT, "BATON_WORKER_POSTURE": "admin"},
                       Never())
        self.assertEqual(status, 1)
        self.assertEqual(len(answers(out.getvalue())), 1,
                         "more than one envelope was read")

    def test_a_latched_fault_with_no_readable_envelope_says_nothing(self):
        out = io.BytesIO()
        status = serve(io.BytesIO(b""), out,
                       {**CONSENT, "BATON_WORKER_POSTURE": "admin"},
                       ScriptedAgent())
        self.assertEqual((status, answers(out.getvalue())), (1, []))


# -- the channel -------------------------------------------------------------

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
        with self.assertRaises(Uncorrelated):
            read_frame(stream)
        self.assertEqual(stream.tell(), len(str(MAX_FRAME + 1)) + 1,
                         "the body was read despite the refusal")

    def test_a_header_that_never_ends_is_bounded_too(self):
        """A header is caller input, so the bound is on it as well as on the
        body -- otherwise a peer that sends no newline reads forever."""
        with self.assertRaises(Uncorrelated):
            read_frame(io.BytesIO(b"9" * 4096))

    def test_a_malformed_frame_has_no_identity_so_it_gets_no_answer(self):
        for what, payload in [("a header that is not a length", b"abc\n{}"),
                              ("a body that ends early", b"99\n{}"),
                              ("a body that is not JSON", b"2\nno"),
                              ("a body that is not an object", b"2\n[]")]:
            with self.subTest(what=what):
                with self.assertRaises(Uncorrelated):
                    read_frame(io.BytesIO(payload))
                out = io.BytesIO()
                status = serve(io.BytesIO(payload), out, EXECUTION,
                               ScriptedAgent())
                self.assertEqual((status, answers(out.getvalue())), (1, []))

    def test_a_clean_end_of_input_is_an_answer(self):
        self.assertIsNone(read_frame(io.BytesIO(b"")))

    def test_our_own_answer_is_bounded_and_keeps_its_identity(self):
        """An agent that produced an enormous recap must not make this program
        the thing that broke the channel — and a bounds fault that dropped the
        correlation would be the uncorrelated shape arriving by the back
        door."""
        class Loud:
            def consider(self, seen, request):
                return {"contract_digest": "sha256:x", "decision": "accept",
                        "reason": "x" * (MAX_FRAME - 100)}

        request = consent("consider")
        status, given = run(CONSENT, request, agent=Loud())
        self.assertIs(given[0]["ok"], False)
        self.assertEqual(given[0]["code"], "bounds")
        self.assertEqual(given[0]["operation_id"], request["operation_id"])


# -- consent cannot reach execution ------------------------------------------

class ConsentCannotReachExecution(unittest.TestCase):

    def test_a_consent_container_is_not_asked_to_work(self):
        status, given = run(CONSENT, consent("work", task="build"))
        self.assertIs(given[0]["ok"], False)
        self.assertEqual(given[0]["code"], "posture")
        self.assertIn("not asked to", given[0]["message"])

    def test_an_execution_container_is_not_asked_to_consent(self):
        status, given = run(EXECUTION, execution("consider"))
        self.assertEqual(given[0]["code"], "posture")

    def test_the_posture_is_checked_on_every_operation(self):
        """A check that ran once at start is a check a later message walks
        past."""
        status, given = run(CONSENT, consent("describe"),
                            consent("consider"), consent("work", task="x"),
                            consent("consider"))
        self.assertEqual([answer["ok"] for answer in given],
                         [True, True, False, True])

    def test_there_is_no_message_that_promotes_a_consent_worker(self):
        for operation in ("promote", "activate", "execution", "work",
                          "escalate", "become"):
            with self.subTest(operation=operation):
                status, given = run(CONSENT, consent(operation))
                self.assertIs(given[0]["ok"], False)

    def test_assignment_material_cannot_arrive_inside_a_consent_frame(self):
        for name in ("assignment", "workspace", "output", "task"):
            with self.subTest(member=name):
                status, given = run(CONSENT,
                                    consent("consider", **{name: "/leak"}))
                self.assertIs(given[0]["ok"], False)
                self.assertEqual(given[0]["code"], "protocol")


# -- the scripted fixtures ---------------------------------------------------

class TheScriptedFixtures(unittest.TestCase):

    def test_consent_accepts_and_declines_deterministically(self):
        status, accepted = run(CONSENT, consent("consider"))
        self.assertEqual(accepted[0]["answer"]["decision"], "accept")
        status, declined = run(
            {**CONSENT, "BATON_WORKER_CONTRACT": "please decline this"},
            consent("consider"))
        self.assertEqual(declined[0]["answer"]["decision"], "decline")

    def test_a_consent_answer_names_nothing_it_cannot_see(self):
        status, given = run(CONSENT, consent("consider"))
        self.assertEqual(sorted(given[0]["answer"]),
                         ["contract_digest", "decision", "reason"])

    def test_execution_completes_and_recaps(self):
        status, given = run(EXECUTION, execution("work", task="build"))
        answer = given[0]["answer"]
        self.assertEqual(answer["disposition"], "completed")
        self.assertEqual(answer["workspace"], "/workspace")
        self.assertIn("build", answer["recap"])

    def test_the_same_request_produces_the_same_bytes(self):
        """DETERMINISTIC is what makes a reproducibility case possible."""
        request = execution("work", task="build")
        first = run(EXECUTION, dict(request))
        second = run(EXECUTION, dict(request))
        self.assertEqual(first, second)

    def test_an_agent_fault_is_a_frame_and_carries_no_traceback(self):
        """A traceback would carry paths from inside the image out through the
        channel, and a worker that died would leave the manager waiting for a
        runtime that is gone."""
        class Angry:
            def work(self, seen, request):
                raise ZeroDivisionError("inside the image")

        status, given = run(EXECUTION, execution("work", task="build"),
                            agent=Angry())
        self.assertIs(given[0]["ok"], False)
        self.assertEqual(given[0]["code"], "agent")
        self.assertEqual(given[0]["message"],
                         "the agent failed: ZeroDivisionError")

    def test_a_closed_channel_is_the_manager_closing_it_and_not_cancellation(
            self):
        """SUPERSEDED FIXTURE, and the ruling is why. An input stream empty
        from its first byte used to be called cancellation; the approved
        contract says cancellation is the manager's runtime stop path and is
        never a worker-entry message or a clean EOF.

        What a clean end of input actually means is that the manager closed
        the channel, and this program exits 0 without inventing a fault about
        it. The real cancellation path is exercised against a real container
        in `test_worker_container.py`.
        """
        status, given = run(EXECUTION)
        self.assertEqual((status, given), (0, []))


# -- the recipe --------------------------------------------------------------

class TheRecipeIsInspectableWithoutADaemon(unittest.TestCase):
    """What the image WILL be, asserted from the recipe.

    The built image proves the same properties and more, next door. These are
    the ones this suite can hold without a daemon; they are not a substitute
    for that gate and the record says so.
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
        self.assertEqual(
            entry, ['ENTRYPOINT ["python3", "/opt/baton/baton_worker.py"]'])

    def test_the_image_defaults_to_no_posture_and_no_session(self):
        for line in self.lines:
            if line.startswith("ENV"):
                self.assertNotIn("BATON_WORKER_", line)

    def test_the_image_announces_no_network_or_health_surface(self):
        for directive in ("EXPOSE", "VOLUME", "HEALTHCHECK"):
            with self.subTest(directive=directive):
                self.assertEqual([line for line in self.lines
                                  if line.startswith(directive)], [])

    def test_no_secret_or_assignment_material_enters_a_layer(self):
        """Only the two program files are copied in, so a layer cannot carry
        an assignment, a bearer or a workspace."""
        copied = [line for line in self.lines if line.startswith("COPY")]
        self.assertEqual(
            copied,
            ["COPY baton_worker.py /opt/baton/baton_worker.py",
             "COPY scripted_agent.py /opt/baton/scripted_agent.py"])

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
        status, given = run(CONSENT, consent("describe"))
        answer = given[0]["answer"]
        self.assertEqual(answer["protocol"], PROTOCOL)
        self.assertEqual(answer["posture"], "consent")
        self.assertEqual(answer["operations"], list(OPERATIONS["consent"]))
        self.assertNotIn("BATON_WORKER_ASSIGNMENT", answer["environment"])

    def test_the_two_postures_are_the_whole_set(self):
        self.assertEqual(POSTURES, ("consent", "execution"))
        self.assertEqual(sorted(OPERATIONS), ["consent", "execution"])


if __name__ == "__main__":
    unittest.main()
