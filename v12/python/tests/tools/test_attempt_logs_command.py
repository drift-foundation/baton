"""W198667 — the operator command, over a real room and nothing else.

THE ACCEPTANCE: a deferred or failed attempt exposes its evidence "without
direct store or Docker inspection". Every case here builds a room with the
manager's own delivery, writes bytes into it the way a worker would, and then
asks the COMMAND -- no engine, no store beyond the one that mints the group,
no container.
"""

import io
import json
import os
import shutil
import tempfile
import unittest

from baton_v12 import attempt_log_format
from baton_v12.worker_manager import ControlStore, attempt_logs
from baton_v12.worker_manager import (configure_workspace_group,
                                      configured_workspace_group)
from tools import attempt_logs_command


class OperatorCase(unittest.TestCase):

    ATTEMPT = "attempt-w198667-operator"

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="v12-w198667-cli-")
        self.addCleanup(shutil.rmtree, self.home, True)
        self.root = os.path.join(self.home, "logs")
        os.makedirs(self.root)
        self.control = ControlStore.open(
            os.path.join(self.home, "control.sqlite3"),
            incarnation="i-1", clock=lambda: "2026-09-18T00:00:00.000Z")
        self.addCleanup(self.control.close)
        configure_workspace_group(self.control, os.getgid())
        self.group = configured_workspace_group(self.control)
        self.delivery = attempt_logs.materialize(
            self.root, attempt_id=self.ATTEMPT, workspace_group=self.group)

    def wrote(self, stream, payload):
        """What a worker writes, written the worker's way."""
        room = os.open(self.delivery.log_root,
                       os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY)
        try:
            handle = attempt_log_format.append_writer(room, stream)
            try:
                attempt_log_format.write_all(handle, payload)
            finally:
                os.close(handle)
        finally:
            os.close(room)

    def declared(self, stream, state):
        room = os.open(self.delivery.log_root,
                       os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY)
        try:
            attempt_log_format.write_declaration(room, stream, state)
        finally:
            os.close(room)

    def ran(self, *argv):
        out = io.StringIO()
        code = attempt_logs_command.main(
            ["--logs", self.root, "--attempt", self.ATTEMPT, *argv],
            stream=out)
        return code, out.getvalue()

    def driven(self, stream, waiting, bound=None):
        """The real `_follow`, over this case's room, with an injected wait."""
        import argparse
        from unittest import mock

        taken = argparse.Namespace(
            logs=self.root, attempt=self.ATTEMPT, stream=stream, from_byte=0,
            bound=attempt_logs.MAX_FOLLOW if bound is None else bound,
            interval=0.0, once=False)
        out, err = io.StringIO(), io.StringIO()
        with mock.patch("sys.stderr", err):
            code = attempt_logs_command._follow(taken, out, sleep=waiting)
        return code, out.getvalue(), err.getvalue()

    def answered(self, *argv):
        code, text = self.ran(*argv)
        self.assertEqual(code, 0, text)
        return json.loads(text)


class TheOperatorCanSeeAnAttemptWithoutAStoreOrAnEngine(OperatorCase):

    def test_locators_names_every_stream_and_where_it_is(self):
        found = self.answered("locators")
        self.assertEqual(found["attempt_id"], self.ATTEMPT)
        self.assertEqual(found["target"], attempt_logs.LOG_TARGET)
        self.assertEqual([one["stream"] for one in found["streams"]],
                         list(attempt_logs.STREAMS))
        for one in found["streams"]:
            self.assertTrue(one["place"].startswith(self.delivery.log_root))

    def test_a_stream_nobody_wrote_is_ABSENT_and_not_empty(self):
        found = self.answered("locators")
        states = {one["stream"]: one for one in found["streams"]}
        self.assertEqual(states["provider.stdout"]["state"], "absent")
        self.assertEqual(states["provider.stdout"]["declaration"], "none")

    def test_the_wrappers_earliest_output_is_readable(self):
        self.wrote("worker.stderr", b"baton-worker: launch: refused\n")
        self.declared("worker.stderr", "finished")
        found = self.answered("read", "--stream", "worker.stderr")
        self.assertEqual(found["text"], "baton-worker: launch: refused\n")
        self.assertEqual(found["state"], "captured")
        self.assertEqual(found["declaration"], "declared")

    def test_a_FAILED_capture_says_so_rather_than_looking_empty(self):
        self.declared("provider.stderr", "failed")
        found = self.answered("read", "--stream", "provider.stderr")
        self.assertEqual(found["state"], "failed")
        self.assertIn("could not write this stream", found["why"])

    def test_a_PARTIAL_capture_is_not_reported_as_the_whole_stream(self):
        self.wrote("provider.stdout", b"a prefix of a record\n")
        self.declared("provider.stdout", "partial")
        found = self.answered("read", "--stream", "provider.stdout")
        self.assertEqual(found["state"], "partial")
        self.assertNotEqual(found["state"], "captured")

    def test_follow_ONCE_answers_where_to_ask_from_next(self):
        """The one-shot form a script wants: a slice and a position, without
        having to interrupt a loop to get them."""
        self.wrote("verification.stdout", b"one\ntwo\n")
        first = self.answered("follow", "--stream", "verification.stdout",
                              "--once", "--bound", "4")
        self.assertEqual(first["text"], "one\n")
        self.assertEqual(first["next_from_byte"], 4)
        self.assertTrue(first["more_may_arrive"])
        second = self.answered("follow", "--stream", "verification.stdout",
                               "--once", "--from-byte",
                               str(first["next_from_byte"]))
        self.assertEqual(second["text"], "two\n")

    def test_follow_LOOPS_until_the_writer_says_the_stream_ENDED(self):
        """The termination rule is the delivery's own, not one this command
        invents: `more_may_arrive` is false once a writer has declared."""
        self.wrote("provider.stdout", b"first\n")

        def ending(_seconds):
            self.wrote("provider.stdout", b"second\n")
            self.declared("provider.stdout", "finished")

        code, said, note = self.driven("provider.stdout", ending)
        self.assertEqual(code, 0)
        self.assertEqual(said, "first\nsecond\n")
        self.assertIn("[captured]", note)

    def test_an_INTERRUPTED_follow_says_where_to_resume(self):
        self.wrote("provider.stdout", b"a long tail\n")

        def interrupted(_seconds):
            raise KeyboardInterrupt

        code, said, note = self.driven("provider.stdout", interrupted)
        self.assertEqual(code, 0)
        self.assertEqual(said, "a long tail\n")
        self.assertIn("resume with --from-byte 12", note)

    def test_the_text_form_writes_bytes_to_stdout_and_state_to_stderr(self):
        from unittest import mock

        self.wrote("provider.stdout", b"raw bytes\n")
        self.declared("provider.stdout", "partial")
        out, err = io.StringIO(), io.StringIO()
        with mock.patch("sys.stdout", out), mock.patch("sys.stderr", err):
            code = attempt_logs_command.main(
                ["--logs", self.root, "--attempt", self.ATTEMPT, "read",
                 "--stream", "provider.stdout", "--text"], stream=out)
        self.assertEqual(code, 0)
        self.assertIn("raw bytes\n", out.getvalue())
        # THE STATE DOES NOT TRAVEL WITH THE PIPED BYTES, which is the point:
        # a prefix must not look whole because somebody redirected stdout.
        self.assertIn("[partial]", err.getvalue())


class FollowDRAINSBeforeItDecidesAnything(OperatorCase):
    """Review 2026-09-18T03-27-44Z [R2], reproduced through the actual command.

    A completed ten-byte stream read at `--bound 3` printed `abc` and returned
    SUCCESS. `more_may_arrive` says the WRITER may append; it says nothing
    about whether the slices already retained have been emitted, and
    terminating on it mid-file loses the rest in silence.
    """

    def test_a_COMPLETED_stream_is_emitted_WHOLE_across_small_slices(self):
        self.wrote("worker.stdout", b"abcdefghij")
        self.declared("worker.stdout", "finished")
        code, said, note = self.driven("worker.stdout", lambda _s: None,
                                       bound=3)
        self.assertEqual(code, 0)
        self.assertEqual(said, "abcdefghij")
        self.assertIn("[captured]", note)

    def test_an_ABSENT_stream_is_WAITED_for_rather_than_called_finished(self):
        """A follower started before its writer is in exactly this state, and
        reporting a run that never began as one that finished is the class of
        falsehood this Work removes."""
        arriving = []

        def then(_seconds):
            arriving.append(1)
            if len(arriving) == 2:
                self.wrote("worker.stderr", b"the writer arrived\n")
                self.declared("worker.stderr", "finished")

        code, said, note = self.driven("worker.stderr", then)
        self.assertEqual(code, 0)
        self.assertEqual(said, "the writer arrived\n")
        # IT REALLY WAITED rather than returning on the first look.
        self.assertGreaterEqual(len(arriving), 2)

    def test_an_INACCESSIBLE_stream_is_REPORTED_and_not_waited_on(self):
        """A room this manager cannot read is a condition to report rather
        than one to sit on. Absence, inaccessibility and completion are three
        different answers and the follower keeps them apart."""
        os.mkfifo(self.delivery.place("verification.stderr"))
        ticks = []
        code, said, note = self.driven("verification.stderr",
                                       lambda _s: ticks.append(1))
        self.assertEqual(code, 0)
        self.assertEqual(said, "")
        self.assertIn("[inaccessible]", note)
        self.assertEqual(ticks, [])

    def test_a_MULTIBYTE_stream_is_not_corrupted_by_the_slice_boundary(self):
        """A bounded read that ended mid-sequence used to decode with
        `replace`, so every character straddling a boundary was destroyed --
        and its caller could not tell, because the byte count was the count of
        bytes handed over rather than of bytes that decoded."""
        said = "→←↑↓ done\n"
        self.wrote("provider.stdout", said.encode("utf-8"))
        self.declared("provider.stdout", "finished")
        code, got, _ = self.driven("provider.stdout", lambda _s: None, bound=4)
        self.assertEqual(code, 0)
        self.assertEqual(got, said)
        self.assertNotIn("\ufffd", got)

    def test_creation_then_append_then_finish_through_the_DEPLOYED_route(self):
        """The whole lifecycle, and reached the way an operator reaches it."""
        from tools import stack_command

        arriving = []

        def then(_seconds):
            arriving.append(1)
            if len(arriving) == 1:
                self.wrote("provider.stderr", b"first\n")
            elif len(arriving) == 2:
                self.wrote("provider.stderr", b"second\n")
            else:
                self.declared("provider.stderr", "finished")

        self.assertIn("logs", stack_command.COMMANDS)
        code, got, note = self.driven("provider.stderr", then)
        self.assertEqual(code, 0)
        self.assertEqual(got, "first\nsecond\n")
        self.assertIn("[captured]", note)


class SmallBoundsAlwaysMakePROGRESS(OperatorCase):
    """Review 2026-09-18T03-39-32Z [R1]. Withholding a split character can
    withhold EVERYTHING when the bound is smaller than one character."""

    def test_a_completed_MULTIBYTE_log_at_bound_ONE_is_emitted_whole(self):
        self.wrote("worker.stdout", "\u20acx".encode("utf-8"))
        self.declared("worker.stdout", "finished")
        code, said, note = self.driven("worker.stdout", lambda _s: None,
                                       bound=1)
        self.assertEqual(code, 0)
        self.assertEqual(said, "\u20acx")
        self.assertIn("[captured]", note)

    def test_bytes_APPENDED_across_polls_complete_their_character(self):
        """A live writer may put the rest of a sequence down between polls, so
        an incomplete tail is held rather than replaced."""
        whole = "\u20ac done\n".encode("utf-8")
        self.wrote("provider.stdout", whole[:1])
        arriving = []

        def then(_seconds):
            arriving.append(1)
            if len(arriving) == 1:
                self.wrote("provider.stdout", whole[1:])
            else:
                self.declared("provider.stdout", "finished")

        code, said, _ = self.driven("provider.stdout", then, bound=2)
        self.assertEqual(code, 0)
        self.assertEqual(said, "\u20ac done\n")
        self.assertNotIn("\ufffd", said)

    def test_TERMINAL_malformed_bytes_are_reported_rather_than_waited_on(self):
        """A truncated sequence at the true end of a FINISHED stream is the
        writer's. A reader that waited for it would never finish, which is the
        hang this Work exists to remove."""
        self.wrote("verification.stderr", b"ok\n\xe2\x82")
        self.declared("verification.stderr", "failed")
        code, said, note = self.driven("verification.stderr",
                                       lambda _s: None, bound=4)
        self.assertEqual(code, 0)
        self.assertTrue(said.startswith("ok\n"))
        self.assertIn("[failed]", note)

    def test_the_RESUME_position_is_the_bytes_that_really_decoded(self):
        whole = "\u20ac\u20ac".encode("utf-8")
        self.wrote("provider.stdout", whole)
        first = self.answered("follow", "--stream", "provider.stdout",
                              "--once", "--bound", "1")
        self.assertEqual(first["text"], "\u20ac")
        self.assertEqual(first["next_from_byte"], 3)


class TheCommandReachesNothingItShouldNot(OperatorCase):

    def test_a_stream_outside_the_room_is_REFUSED(self):
        with open(os.path.join(self.root, "other.log"), "w") as handle:
            handle.write("SOMEBODY ELSE'S ATTEMPT\n")
        from unittest import mock

        err = io.StringIO()
        with mock.patch("sys.stderr", err):
            code, _ = self.ran("read", "--stream", "../other")
        self.assertEqual(code, 2)
        self.assertIn("is not a stream this delivery names", err.getvalue())

    def test_an_unknown_stream_is_REFUSED_as_prose_not_a_traceback(self):
        from unittest import mock

        err = io.StringIO()
        with mock.patch("sys.stderr", err):
            code, _ = self.ran("follow", "--stream", "provider.stdlog")
        self.assertEqual(code, 2)
        self.assertTrue(err.getvalue().startswith("refused: "))

    def test_reading_an_attempt_that_has_no_room_CREATES_nothing(self):
        """A room made by a reader would be an empty one reported where an
        absent one belongs."""
        out = io.StringIO()
        code = attempt_logs_command.main(
            ["--logs", self.root, "--attempt", "attempt-never-ran",
             "locators"], stream=out)
        self.assertEqual(code, 0)
        found = json.loads(out.getvalue())
        self.assertTrue(all(one["state"] in ("absent", "inaccessible")
                            for one in found["streams"]))
        self.assertFalse(os.path.exists(
            os.path.join(self.root, "attempt-never-ran")))

    def test_this_command_opens_no_store_and_no_engine(self):
        """Held as a property of what it IMPORTS rather than as a comment.

        A first cut of this case searched the source TEXT and failed on the
        module's own docstring, which says the command opens no Authority --
        prose about a boundary is not a crossing of it. What decides is the
        import graph.
        """
        import ast
        import inspect

        tree = ast.parse(inspect.getsource(attempt_logs_command))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(one.name for one in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.add(node.module or "")
                imported.update(f"{node.module}.{one.name}"
                                for one in node.names)
        for forbidden in ("sqlite3", "subprocess", "baton_v12.authority",
                          "baton_v12.job_manager",
                          "baton_v12.worker_manager.store"):
            self.assertNotIn(forbidden, imported)
        self.assertEqual(
            sorted(one for one in imported if one.startswith("baton_v12")),
            ["baton_v12.contracts", "baton_v12.contracts.ContractRefusal",
             "baton_v12.worker_manager",
             "baton_v12.worker_manager.attempt_logs"])


if __name__ == "__main__":
    unittest.main()
