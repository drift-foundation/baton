"""W38956 — the worker-entry transport, driven against the REAL worker.

`work/records/2026/08/finding-v12-first-useful-dogfood-task/`.

THE POSITIVE CASES DO NOT USE A FAKE PEER, and that is the whole design of this
file. `baton_worker.serve` is imported and run in a thread over a real pipe
pair, so every green case here is the manager's transport and the image's
program actually meeting — two independent implementations of
`baton.worker-entry/1`, one of which cannot import the other. A hand-written
fake worker would agree with whatever the transport did, which is exactly the
failure W6636 recorded when two closed components turned out not to be able to
meet at all.

THE NEGATIVE CASES DO USE A COMPOSED PEER, and for the opposite reason: a
healthy worker cannot produce a truncated frame, a foreign session or a
duplicated answer, and those are the ones the transport exists to refuse. A
suite that could only drive the real worker could only prove the happy path.

WHAT IS NOT HERE. No daemon and no container: `exec_vector` is asserted as a
composed vector, and whether Docker applies it is `test_worker_container`'s
and `test_lifecycle_composition`'s question. This file owns the CHANNEL.
"""

import io
import json
import os
import pathlib
import shutil
import sys
import threading
import unittest

WORKER = (pathlib.Path(__file__).resolve().parents[3] / "worker")
sys.path.insert(0, str(WORKER))
# THE BYTECODE CACHE GOES BEFORE THE IMPORT, for the reason
# `test_worker_image` gives at the same line: the worker directory is COPIED
# into the image, and a `__pycache__` this suite created would travel with it.
shutil.rmtree(WORKER / "__pycache__", ignore_errors=True)

import baton_worker                                          # noqa: E402
from scripted_agent import ScriptedAgent                     # noqa: E402

from baton_v12.contracts import ContractRefusal              # noqa: E402
from baton_v12.contracts.secrets import held_secret          # noqa: E402
from baton_v12.worker_manager import worker_entry            # noqa: E402
from baton_v12.worker_manager.oci import exec_vector         # noqa: E402
from baton_v12.worker_manager.worker_entry import (          # noqa: E402
    ANSWER_MEMBERS, ChannelPort, MAX_FRAME, MAX_IDENTITY, OPERATIONS,
    PROTOCOL, converse)

from .test_worker_image import DECLARATION, staged           # noqa: E402

SESSION = "session-w38956"
RUNTIME = "8fce41c0d2b4"
PROGRAM = ["python3", "/opt/baton/baton_worker.py"]
SECONDS = 30


def launch_document(case, session=SESSION, schema="baton.worker-launch/1"):
    """One read-only launch document, as the adapter binds one.

    MODE 0444 IS PART OF THE FIXTURE rather than tidiness. `read_launch`
    proves the file is not writable from inside the container by ATTEMPTING a
    write-open, because mode bits describe a host file and say nothing about
    how it was mounted. In-process there is no mount, so the only way to give
    that proof something true to find is to take the write bit away.
    """
    import tempfile
    home = tempfile.mkdtemp(prefix="v12-w38956-launch-")
    case.addCleanup(shutil.rmtree, home, True)
    place = os.path.join(home, "launch.json")
    with open(place, "w", encoding="utf-8") as handle:
        json.dump({"schema": schema, "session": session,
                   "contract": "add the missing coverage", "role": "coder"},
                  handle)
    os.chmod(place, 0o444)
    return place


class LiveWorker:
    """The image's own program, over a real pipe pair, in this process.

    A THREAD AND NOT A SUBPROCESS. A subprocess would be a second interpreter
    with its own import path and would prove the same thing more slowly; what
    matters is that the bytes on the wire are produced by `baton_worker` and
    consumed by the transport, and a pipe is a pipe.

    THE WORKER'S READER IS BUFFERED AND THE MANAGER'S IS NOT, deliberately.
    `read_frame` reads a body with one `read(length)` and requires exactly that
    many bytes, which is what `sys.stdin.buffer` gives it in the image; the
    manager's `_Reader` is written to survive short reads, so it is handed the
    raw stream that actually produces them.
    """

    def __init__(self, agent, place, *, seconds=SECONDS):
        to_worker, self._write = os.pipe()
        self._read, from_worker = os.pipe()
        self._seconds = seconds
        self.status = None
        worker_in = io.BufferedReader(io.FileIO(to_worker, "rb"))
        worker_out = io.FileIO(from_worker, "wb")

        def serve():
            try:
                self.status = baton_worker.serve(worker_in, worker_out, agent,
                                                 place)
            finally:
                worker_out.close()
                worker_in.close()

        self._thread = threading.Thread(target=serve, daemon=True)
        self._thread.start()

    def send(self, payload):
        os.write(self._write, payload)

    def receive(self, count):
        return os.read(self._read, count)

    def finish(self):
        os.close(self._write)
        self._thread.join(self._seconds)
        if self._thread.is_alive():
            raise AssertionError("the worker did not end within the bound")
        os.close(self._read)
        return {"status": self.status, "stderr": ""}


class Composed:
    """A peer that says EXACTLY what a case tells it to.

    Answers are looked up by the frame index rather than replayed blindly, so
    a case can answer the second request wrongly and the first correctly --
    which is what tells "the transport refuses a bad answer" apart from "the
    transport refuses everything".
    """

    def __init__(self, payloads, *, status=0, stderr="", fail_send=False,
                 fail_finish=False, finish=None):
        self._payloads = list(payloads)
        self._held = b""
        self.sent = []
        self._status = status
        self._stderr = stderr
        self._fail_send = fail_send
        self._fail_finish = fail_finish
        self._finish = finish

    def send(self, payload):
        if self._fail_send:
            raise OSError("the exec session is gone")
        self.sent.append(payload)
        if self._payloads:
            self._held += self._payloads.pop(0)

    def receive(self, count):
        piece, self._held = self._held[:count], self._held[count:]
        return piece

    def finish(self):
        if self._fail_finish:
            raise OSError("the exec session cannot be waited on")
        if self._finish is not None:
            return self._finish
        return {"status": self._status, "stderr": self._stderr}


def framed(document):
    body = json.dumps(document).encode("utf-8")
    return str(len(body)).encode("ascii") + b"\n" + body


def reply(operation_id, answer, *, session=SESSION, protocol=PROTOCOL):
    return framed({"protocol": protocol, "session": session,
                   "operation_id": operation_id, "ok": True,
                   "answer": answer})


DESCRIBE_ANSWER = {"protocol": PROTOCOL, "operations": ["describe", "work"],
                   "launch": ["contract", "role", "schema", "session"]}


def spoken(case, channel, operations, ids, **overrides):
    """One conversation over an already-made channel."""
    return converse(ChannelPort(lambda argv, *, seconds: channel),
                    engine="docker", runtime_id=RUNTIME, program=PROGRAM,
                    session=overrides.pop("session", SESSION),
                    operations=operations, operation_ids=ids,
                    seconds=overrides.pop("seconds", SECONDS), **overrides)


class TheTwoCopiesOfOneContractAgree(unittest.TestCase):
    """The manager's copy of the worker's closed sets, held against the
    worker's own literals.

    The image cannot import this package and this package cannot import the
    image, so the contract exists twice. `test_oci` already does exactly this
    for the launch document's members; two copies of one contract agree until
    they don't, and this is where they stop being allowed to.
    """

    def test_the_protocol_name_is_the_workers_own(self):
        self.assertEqual(PROTOCOL, baton_worker.PROTOCOL)

    def test_the_frame_and_identity_ceilings_are_the_workers_own(self):
        self.assertEqual(MAX_FRAME, baton_worker.MAX_FRAME)
        self.assertEqual(MAX_IDENTITY, baton_worker.MAX_IDENTITY)

    def test_the_answer_member_sets_are_the_workers_own(self):
        self.assertEqual(ANSWER_MEMBERS, baton_worker.ANSWER_MEMBERS)

    def test_the_operations_are_the_workers_whole_vocabulary(self):
        """INCLUDING `consider`, which this runtime is not entitled to.

        The worker keeps it as a real operation it refuses; a transport that
        could not send it could not prove that refusal, and the negative case
        below sends exactly it.
        """
        self.assertEqual(sorted(OPERATIONS),
                         sorted(baton_worker.REQUEST_MEMBERS))

    def test_the_request_envelope_is_the_workers_common_members(self):
        self.assertEqual(
            sorted(worker_entry._ENVELOPE + ("operation",)),
            sorted(baton_worker.COMMON_MEMBERS))


class TheVectorIsClosed(unittest.TestCase):

    def test_the_exec_vector_names_the_runtime_and_the_program(self):
        self.assertEqual(
            exec_vector("docker", runtime_id=RUNTIME, program=PROGRAM),
            ["docker", "exec", "--interactive", RUNTIME] + PROGRAM)

    def test_there_is_no_tty(self):
        """A tty merges the worker's stdout and stderr onto one stream, and a
        channel that cannot tell an answer from a diagnostic is not one."""
        argv = exec_vector("docker", runtime_id=RUNTIME, program=PROGRAM)
        self.assertNotIn("--tty", argv)
        self.assertNotIn("-t", argv)

    def test_an_exec_names_a_program_because_no_entrypoint_is_applied(self):
        with self.assertRaises(ContractRefusal) as refused:
            exec_vector("docker", runtime_id=RUNTIME, program=[])
        self.assertIn("applies no entrypoint", str(refused.exception))

    def test_an_engine_this_adapter_does_not_speak_is_refused(self):
        with self.assertRaises(ContractRefusal):
            exec_vector("kubectl", runtime_id=RUNTIME, program=PROGRAM)

    def test_a_live_secret_never_reaches_the_channel(self):
        """§13, at the port rather than at the vector.

        The runtime id is caller-supplied text that lands in an argv every
        process on this host can read, so the sweep has to be on INVOCATION.
        """
        with held_secret(RUNTIME):
            with self.assertRaises(ContractRefusal) as refused:
                spoken(self, Composed([]), ["describe"], ["op-1"])
        self.assertIn("secret", str(refused.exception).lower())


class TheRealWorkerAnswersTheRealTransport(unittest.TestCase):
    """The positive arc, over the image's own program."""

    def setUp(self):
        self.place = launch_document(self)

    def test_describe_crosses_and_comes_back_correlated(self):
        answered = spoken(self, LiveWorker(ScriptedAgent(), self.place),
                          ["describe"], ["op-describe-1"])
        self.assertEqual(answered["ending"], "answered", answered["why"])
        self.assertEqual(answered["status"], 0)
        self.assertEqual(len(answered["answers"]), 1)
        one = answered["answers"][0]
        self.assertEqual(one["operation"], "describe")
        self.assertEqual(one["operation_id"], "op-describe-1")
        self.assertTrue(one["ok"])
        # THE WORKER'S OWN ANSWER, not this suite's idea of one: the protocol
        # it speaks, the operations it is entitled to and the launch document
        # it was actually started with.
        self.assertEqual(one["answer"]["protocol"], PROTOCOL)
        self.assertEqual(one["answer"]["operations"],
                         list(baton_worker.OPERATIONS))
        self.assertEqual(one["answer"]["launch"],
                         sorted(baton_worker.LAUNCH_MEMBERS))

    def test_two_operations_in_one_session_stay_in_order(self):
        staged(self, [dict(DECLARATION)])
        answered = spoken(self, LiveWorker(ScriptedAgent(), self.place),
                          ["describe", "work"], ["op-1", "op-2"])
        self.assertEqual(answered["ending"], "answered", answered["why"])
        self.assertEqual([one["operation"] for one in answered["answers"]],
                         ["describe", "work"])
        self.assertEqual([one["operation_id"] for one in answered["answers"]],
                         ["op-1", "op-2"])

    def test_a_work_turn_reaches_the_agent_and_publishes_its_own_envelope(
            self):
        """THE WHOLE POINT OF THE TRANSPORT, said in one case.

        The manager asks; the agent writes under the declared path; the worker
        measures what was written and publishes `/output/output.json` LAST.
        Every one of those is somebody else's code, and until this transport
        existed nothing in the manager could cause any of it to happen.
        """
        _inputs, outputs = staged(self, [dict(DECLARATION)])
        answered = spoken(self, LiveWorker(ScriptedAgent(), self.place),
                          ["work"], ["op-work-1"])
        self.assertEqual(answered["ending"], "answered", answered["why"])
        answer = answered["answers"][0]["answer"]
        self.assertEqual(answer["disposition"], "completed")
        self.assertEqual(answer["outputs"], [DECLARATION["name"]])
        # AND THE DURABLE DOCUMENT IS WHAT THE RESULT IS READ FROM. The framed
        # answer carries bounded names; the envelope carries the record, and
        # its presence is the completion signal.
        with open(os.path.join(outputs, "output.json"), encoding="utf-8") as h:
            envelope = json.load(h)
        self.assertEqual(envelope["schema"],
                         "baton.worker-manifest/completion")
        self.assertEqual(envelope["disposition"], "completed")
        self.assertEqual([one["name"] for one in envelope["outputs"]],
                         [DECLARATION["name"]])

    def test_an_operation_this_runtime_is_not_entitled_to_faults(self):
        """`consider` is a REAL operation and this runtime may not be asked it.

        The ending is `faulted` rather than `lost`: the channel worked, the
        worker answered, and what it answered was a refusal — which is a fact
        about the request and not about the transport.
        """
        answered = spoken(self, LiveWorker(ScriptedAgent(), self.place),
                          ["consider"], ["op-consider-1"])
        self.assertEqual(answered["ending"], "faulted")
        self.assertEqual(answered["answers"][0]["code"], "entitlement")
        self.assertFalse(answered["answers"][0]["ok"])
        # AND THE WORKER IS STILL HEALTHY, which is why `faulted` says nothing
        # about the status. An entitlement refusal leaves an operable framing
        # loop that ends 0 at EOF; only a LATCHED launch fault exits non-zero,
        # and the case below is the one that proves that difference.
        self.assertEqual(answered["status"], 0)

    def test_a_frame_for_another_session_is_refused_by_the_worker(self):
        """The far end binds too, and this proves the binding is real rather
        than a property of the manager always sending the right value."""
        answered = spoken(self, LiveWorker(ScriptedAgent(), self.place),
                          ["describe"], ["op-1"], session="session-somebody")
        self.assertEqual(answered["ending"], "faulted")
        self.assertEqual(answered["answers"][0]["code"], "session")

    def test_a_container_whose_launch_document_is_unreadable_says_nothing(
            self):
        """The `Uncorrelated` ending, from the far side.

        A worker with no readable launch document has no session to answer
        under, so the ruling has it write NO frame and exit non-zero. To the
        transport that is a lost channel, and it must not become an answer.
        """
        answered = spoken(self,
                          LiveWorker(ScriptedAgent(), "/nonexistent/launch"),
                          ["describe"], ["op-1"])
        self.assertEqual(answered["ending"], "lost")
        self.assertEqual(answered["status"], 2)
        self.assertEqual(answered["answers"], [])
        # WHICH loss it is depends on a race this case does not control: the
        # worker exits before reading, so the write may fail on a broken pipe
        # or succeed into a closing one and then find no answer. Both are the
        # same ending and the same conclusion, which is why the ending is what
        # a caller acts on and `why` is what an operator reads.
        self.assertIn(answered["why"],
                      ["the request could not be written: BrokenPipeError",
                       "the worker ended the channel without answering "
                       "describe"])

    def test_a_latched_launch_fault_answers_once_and_is_not_an_answer(self):
        """A document that IS correlatable and is wrong some other way.

        The worker latches, answers one correlated fault and exits non-zero.
        `faulted` — the channel worked and the container said what was wrong
        with it, which is exactly what an operator needs to see.
        """
        place = launch_document(self, schema="baton.worker-launch/2")
        answered = spoken(self, LiveWorker(ScriptedAgent(), place),
                          ["describe"], ["op-1"])
        self.assertEqual(answered["ending"], "faulted")
        self.assertEqual(answered["answers"][0]["code"], "launch")
        self.assertEqual(answered["status"], 1)


class TransportLossIsNeverCompletion(unittest.TestCase):
    """Every way the channel can end without telling us what the agent did."""

    def test_a_channel_that_cannot_be_opened_is_lost_and_not_absent(self):
        def refuses(argv, *, seconds):
            raise OSError("no such container")

        answered = converse(ChannelPort(refuses), engine="docker",
                            runtime_id=RUNTIME, program=PROGRAM,
                            session=SESSION, operations=["describe"],
                            operation_ids=["op-1"], seconds=SECONDS)
        self.assertEqual(answered["ending"], "lost")
        self.assertEqual(answered["answers"], [])
        self.assertIsNone(answered["status"])
        self.assertIn("could not be opened", answered["why"])

    def test_a_request_that_cannot_be_written_is_lost(self):
        answered = spoken(self, Composed([], fail_send=True), ["describe"],
                          ["op-1"])
        self.assertEqual(answered["ending"], "lost")
        self.assertIn("could not be written", answered["why"])

    def test_a_stream_that_ends_inside_a_body_is_lost(self):
        whole = reply("op-1", DESCRIBE_ANSWER)
        answered = spoken(self, Composed([whole[:-4]]), ["describe"],
                          ["op-1"])
        self.assertEqual(answered["ending"], "lost")
        self.assertIn("inside a frame body", answered["why"])

    def test_a_header_that_is_not_a_length_is_lost(self):
        answered = spoken(self, Composed([b"not-a-length\n{}"]), ["describe"],
                          ["op-1"])
        self.assertEqual(answered["ending"], "lost")
        self.assertIn("not a length", answered["why"])

    def test_a_header_with_no_newline_cannot_read_forever(self):
        answered = spoken(self, Composed([b"9" * 64]), ["describe"], ["op-1"])
        self.assertEqual(answered["ending"], "lost")
        self.assertIn("not a length", answered["why"])

    def test_a_frame_wider_than_the_channel_is_refused_before_it_is_read(self):
        answered = spoken(self, Composed([f"{MAX_FRAME + 1}\n".encode()]),
                          ["describe"], ["op-1"])
        self.assertEqual(answered["ending"], "lost")
        self.assertIn(f"a frame of {MAX_FRAME + 1} bytes", answered["why"])

    def test_a_frame_that_is_not_json_is_lost(self):
        answered = spoken(self, Composed([b"7\nnotjson"]), ["describe"],
                          ["op-1"])
        self.assertEqual(answered["ending"], "lost")
        self.assertIn("not UTF-8 JSON", answered["why"])

    def test_an_answer_for_another_session_is_lost(self):
        answered = spoken(
            self,
            Composed([reply("op-1", DESCRIBE_ANSWER, session="somebody")]),
            ["describe"], ["op-1"])
        self.assertEqual(answered["ending"], "lost")
        self.assertIn("another container session", answered["why"])

    def test_an_answer_for_another_operation_is_lost(self):
        answered = spoken(self,
                          Composed([reply("op-2", DESCRIBE_ANSWER)]),
                          ["describe"], ["op-1"])
        self.assertEqual(answered["ending"], "lost")
        self.assertIn("correlates to another operation", answered["why"])

    def test_an_answer_in_another_protocol_is_lost(self):
        answered = spoken(
            self,
            Composed([reply("op-1", DESCRIBE_ANSWER,
                            protocol="baton.worker-entry/2")]),
            ["describe"], ["op-1"])
        self.assertEqual(answered["ending"], "lost")

    def test_an_answer_with_an_extra_member_is_lost(self):
        answered = spoken(
            self,
            Composed([reply("op-1", dict(DESCRIBE_ANSWER, extra="alias"))]),
            ["describe"], ["op-1"])
        self.assertEqual(answered["ending"], "lost")
        self.assertIn("unexpected extra", answered["why"])

    def test_an_answer_missing_a_member_is_lost(self):
        short = {name: value for name, value in DESCRIBE_ANSWER.items()
                 if name != "launch"}
        answered = spoken(self, Composed([reply("op-1", short)]),
                          ["describe"], ["op-1"])
        self.assertEqual(answered["ending"], "lost")
        self.assertIn("missing launch", answered["why"])

    def test_a_frame_that_says_neither_ok_nor_not_ok_is_lost(self):
        answered = spoken(
            self,
            Composed([framed({"protocol": PROTOCOL, "session": SESSION,
                              "operation_id": "op-1",
                              "answer": DESCRIBE_ANSWER})]),
            ["describe"], ["op-1"])
        self.assertEqual(answered["ending"], "lost")
        self.assertIn("neither ok nor not-ok", answered["why"])

    def test_bytes_this_conversation_never_asked_for_are_lost(self):
        """A worker that said MORE than it was asked has said something
        nobody can match to a request, and truncating at the last frame that
        happened to correlate would be reading past the contract."""
        answered = spoken(
            self,
            Composed([reply("op-1", DESCRIBE_ANSWER)
                      + reply("op-9", DESCRIBE_ANSWER)]),
            ["describe"], ["op-1"])
        self.assertEqual(answered["ending"], "lost")
        self.assertIn("did not ask for", answered["why"])

    def test_complete_answers_with_an_unclean_ending_are_lost(self):
        """`serve` returns 0 only on a clean end of input with nothing
        latched. Answers followed by a non-zero ending is a worker that did
        something this conversation did not see — which is neither a refusal
        nor a completion."""
        answered = spoken(self,
                          Composed([reply("op-1", DESCRIBE_ANSWER)], status=3),
                          ["describe"], ["op-1"])
        self.assertEqual(answered["ending"], "lost")
        self.assertEqual(answered["status"], 3)
        self.assertIn("ends 0", answered["why"])
        # AND THE ANSWER IS STILL CARRIED, because what the worker said is
        # evidence even when the ending is not one to act on.
        self.assertEqual(len(answered["answers"]), 1)

    def test_an_unreadable_ending_is_lost_rather_than_a_zero_status(self):
        answered = spoken(self,
                          Composed([reply("op-1", DESCRIBE_ANSWER)],
                                   fail_finish=True),
                          ["describe"], ["op-1"])
        self.assertEqual(answered["ending"], "lost")
        self.assertIsNone(answered["status"])

    def test_an_ending_that_is_not_the_closed_answer_is_lost(self):
        for finish in ({"status": None, "stderr": ""},
                       {"status": True, "stderr": ""},
                       {"status": 0, "stderr": None},
                       {"status": 0},
                       {"status": 0, "stderr": "", "extra": 1}):
            with self.subTest(finish=finish):
                answered = spoken(
                    self,
                    Composed([reply("op-1", DESCRIBE_ANSWER)], finish=finish),
                    ["describe"], ["op-1"])
                self.assertEqual(answered["ending"], "lost")

    def test_a_fault_stops_the_conversation_rather_than_asking_again(self):
        """The worker consumes an operation id whatever the outcome and exits
        after a latched fault, so a second request would be asking a peer that
        has already finished."""
        faulted = framed({"protocol": PROTOCOL, "session": SESSION,
                          "operation_id": "op-1", "ok": False,
                          "code": "input", "message": "no readable /input"})
        channel = Composed([faulted, reply("op-2", DESCRIBE_ANSWER)])
        answered = spoken(self, channel, ["work", "describe"],
                          ["op-1", "op-2"])
        self.assertEqual(answered["ending"], "faulted")
        self.assertEqual(len(answered["answers"]), 1)
        self.assertEqual(len(channel.sent), 1)

    def test_the_worker_stderr_is_carried_bounded(self):
        answered = spoken(
            self,
            Composed([reply("op-1", DESCRIBE_ANSWER)],
                     stderr="d" * (worker_entry.MAX_STDERR * 3)),
            ["describe"], ["op-1"])
        self.assertEqual(len(answered["stderr"]), worker_entry.MAX_STDERR)


class TheOperandsAreOwnedBeforeAnythingIsSent(unittest.TestCase):
    """Every refusal here happens with the channel unopened, which is what
    makes them refusals rather than endings."""

    def refuses(self, **overrides):
        operands = {"engine": "docker", "runtime_id": RUNTIME,
                    "program": PROGRAM, "session": SESSION,
                    "operations": ["describe"], "operation_ids": ["op-1"],
                    "seconds": SECONDS}
        operands.update(overrides)
        opened = []

        def open_channel(argv, *, seconds):
            opened.append(argv)
            return Composed([])

        with self.assertRaises(ContractRefusal) as refused:
            converse(ChannelPort(open_channel), **operands)
        self.assertEqual(opened, [], "the channel was opened anyway")
        return refused.exception

    def test_an_unknown_operation_is_refused(self):
        self.assertIn("is not an operation this channel speaks",
                      str(self.refuses(operations=["negotiate"])))

    def test_a_conversation_asks_for_at_least_one_operation(self):
        self.assertIn("at least one operation",
                      str(self.refuses(operations=[], operation_ids=[])))

    def test_one_identity_per_operation(self):
        self.assertIn("one operation identity per operation",
                      str(self.refuses(operations=["describe", "work"],
                                       operation_ids=["op-1"])))

    def test_an_identity_is_consumed_once_per_session(self):
        """Composing a conversation the worker's replay fence must refuse is
        composing a request that cannot succeed."""
        self.assertIn("consumed once per worker session",
                      str(self.refuses(operations=["describe", "work"],
                                       operation_ids=["op-1", "op-1"])))

    def test_an_over_long_session_identity_is_refused(self):
        self.assertIn("at most",
                      str(self.refuses(session="s" * (MAX_IDENTITY + 1))))

    def test_a_session_that_is_not_an_identity_is_refused(self):
        for session in (None, "", 7, {"session": "x"}):
            with self.subTest(session=session):
                self.refuses(session=session)

    def test_a_bound_that_is_not_whole_seconds_is_refused(self):
        for seconds in (0, -1, True, 1.5, "30", None):
            with self.subTest(seconds=seconds):
                self.assertIn("whole number of seconds",
                              str(self.refuses(seconds=seconds)))

    def test_a_channel_that_is_not_the_framed_session_is_refused(self):
        class Partial:
            def send(self, payload):
                pass

        with self.assertRaises(ContractRefusal) as refused:
            converse(ChannelPort(lambda argv, *, seconds: Partial()),
                     engine="docker", runtime_id=RUNTIME, program=PROGRAM,
                     session=SESSION, operations=["describe"],
                     operation_ids=["op-1"], seconds=SECONDS)
        self.assertIn("is not the framed session", str(refused.exception))

    def test_an_open_operation_that_is_not_a_capability_is_refused(self):
        with self.assertRaises(ContractRefusal):
            ChannelPort("not a capability")


if __name__ == "__main__":
    unittest.main()
