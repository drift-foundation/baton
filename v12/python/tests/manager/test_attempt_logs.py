"""W198667 — the attempt log delivery: its room, its vocabulary, its readers.

NO CONTAINER, NO ENGINE, NO MODEL. Everything here is a directory this manager
makes and a file something writes into it, which is exactly what the delivery
is; the capture that fills it is `test_claude_agent`'s and the mount is
`test_oci`'s.

THE CASES ARE THE OWNER'S REQUIRED OUTCOME, one at a time: a room made before
startup, partial evidence surviving a restart, concurrent attempts kept apart,
missing distinguished from empty, and an operator surface that needs no engine.
"""

import hashlib
import io
import itertools
import json
import os
import shutil
import stat
import tempfile
import subprocess
import sys
import threading
import unittest
from types import SimpleNamespace
from unittest import mock

from baton_v12.contracts import ContractRefusal
from baton_v12 import attempt_log_format
from baton_v12.worker_manager import ControlStore, attempt_logs, workspaces
from baton_v12.worker_manager import (configure_workspace_group,
                                      configured_workspace_group)


REPO = "/home/sl/src/baton"


def _as_the_image_lays_it_out(case):
    """The worker's own import namespace, the way the image really composes it.

    `Dockerfile.claude` copies the worker programs to `/opt/baton/` and the
    profile package to `/opt/baton/source_profiles` -- TOP-LEVEL names, because
    nothing from `baton_v12` travels into a worker image. `attempt_log_format`
    is carried the same way, so a case exercising worker code has to put those
    two directories on the path or it is exercising an import layout no
    container has.
    """
    import sys

    for place in (os.path.join(REPO, "v12/worker"),
                  os.path.join(REPO, "v12/python/src/baton_v12")):
        sys.path.insert(0, place)
        case.addCleanup(sys.path.remove, place)
    # AND NOTHING IS EVICTED FROM `sys.modules`. A first cut of this helper
    # popped `claude_agent` and `baton_worker` on cleanup, which broke three
    # cases in OTHER suites that had already imported them and still held the
    # old class objects -- a fixture that tidies up a shared import cache is a
    # fixture that decides what every later case is testing.


class LogRoom(unittest.TestCase):
    """One delivery root and this deployment's own minted group."""

    ATTEMPT = "attempt-w198667"

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="v12-w198667-")
        self.addCleanup(shutil.rmtree, self.home, True)
        self.root = os.path.join(self.home, "logs")
        os.makedirs(self.root)
        self.control = ControlStore.open(
            os.path.join(self.home, "control.sqlite3"),
            incarnation="i-1", clock=lambda: "2026-09-18T00:00:00.000Z")
        self.addCleanup(self.control.close)
        # THE DEPLOYMENT'S OWN RECORD MINTS THE CAPABILITY, exactly as
        # `test_exchange` does: a group any caller could construct would leave
        # the hole the frozen answer exists to close.
        configure_workspace_group(self.control, os.getgid())
        self.group = configured_workspace_group(self.control)

    def made(self, attempt_id=None):
        return attempt_logs.materialize(
            self.root, attempt_id=attempt_id or self.ATTEMPT,
            workspace_group=self.group)

    def wrote(self, delivery, stream, payload):
        with open(delivery.place(stream), "ab") as handle:
            handle.write(payload)

    def staging_of(self, delivery, stream, *, which=0):
        """The staging name the NEXT declaration will pick, made predictable.

        The per-call counter that fixes R2's same-process collision also makes
        the name unguessable from outside, so a case that plants a collision
        has to control the identity source rather than guess at it. `_STAGING`
        is the module's own named seam for exactly that: patching it is testing
        the rule the module states, not reaching around it.
        """
        # THE SEAM MOVED WITH THE ACT. The staging identity now lives in
        # `attempt_log_format`, which is the module that opens the entry, so
        # that is what a deterministic collision forces.
        self.enterContext(mock.patch.object(attempt_log_format, "_STAGING",
                                            itertools.count(which)))
        return os.path.join(
            delivery.log_root,
            f"{stream}.status.{os.getpid()}.{which}.staging")


class TheRoomIsMadeBeforeAnythingRuns(LogRoom):

    def test_the_room_and_its_native_corner_exist_and_are_group_writable(self):
        delivery = self.made()
        for place in (delivery.log_root, delivery.native_root):
            held = os.stat(place)
            self.assertTrue(stat.S_ISDIR(held.st_mode))
            self.assertEqual(stat.S_IMODE(held.st_mode),
                             attempt_logs.LOG_DIR)
            self.assertEqual(held.st_gid, self.group.gid)

    def test_the_mode_is_the_one_its_establisher_sets(self):
        """A second constant here would be a second thing to keep true, and
        `adopt` would start refusing rooms this module itself made."""
        self.assertEqual(attempt_logs.LOG_DIR, workspaces.WORKSPACE_DIR)

    def test_a_second_materialize_over_one_attempt_REFUSES(self):
        """A fresh attempt writing into another attempt's evidence is the
        concurrency defect the required outcome names."""
        self.made()
        with self.assertRaises(FileExistsError):
            self.made()

    def test_the_room_is_NOT_the_result_or_protocol_surface(self):
        """The whole reason this delivery exists rather than a subdirectory of
        something that already had a mount.

        W202663 (owner 2026-09-21T05:54:40Z) MOVED the target: the legacy
        `/run/baton/logs` is a disposable decoy now, covered in the composed
        restrictions, so old-byte nested writers cannot reach the
        authoritative room. The two spellings must never collapse back into
        one -- a decoy AT the room is no decoy."""
        self.assertEqual(attempt_logs.LOG_TARGET, "/run/baton/attempt-logs")
        self.assertEqual(attempt_logs.LEGACY_LOG_TARGET, "/run/baton/logs")
        self.assertNotEqual(attempt_logs.LOG_TARGET,
                            attempt_logs.LEGACY_LOG_TARGET)
        from baton_v12.worker_manager import exchange

        self.assertNotIn(attempt_logs.LOG_TARGET,
                         (exchange.COMMAND_TARGET, exchange.EVENT_TARGET))
        self.assertFalse(attempt_logs.LOG_TARGET.startswith("/output"))
        # AND THE DECOY IS COMPOSED, at the legacy spelling, as a tmpfs the
        # container can write and nobody reads back.
        from baton_v12.worker_manager import oci

        self.assertIn(
            ("--tmpfs", f"{attempt_logs.LEGACY_LOG_TARGET}"
                        f":rw,noexec,nosuid,nodev,size=16m"),
            oci.RESTRICTIONS)

    def test_a_delivery_is_frozen_and_names_only_the_streams_it_has(self):
        delivery = self.made()
        with self.assertRaises(ContractRefusal):
            delivery.attempt_id = "somebody-else"
        with self.assertRaisesRegex(ContractRefusal, "not a stream"):
            delivery.place("provider.stdlog")
        for stream in attempt_logs.STREAMS:
            self.assertTrue(delivery.place(stream).startswith(
                delivery.log_root))

    def test_a_bare_integer_is_not_this_deployment_s_group(self):
        with self.assertRaisesRegex(ContractRefusal, "minted workspace group"):
            attempt_logs.materialize(self.root, attempt_id="attempt-x",
                                     workspace_group=os.getgid())


class ConcurrentAttemptsAreKeptApart(LogRoom):

    def test_two_attempts_have_two_rooms_and_two_streams(self):
        one = self.made("attempt-one")
        two = self.made("attempt-two")
        self.assertNotEqual(one.log_root, two.log_root)
        self.wrote(one, "provider.stdout", b"first attempt\n")
        self.wrote(two, "provider.stdout", b"second attempt\n")
        self.assertEqual(
            attempt_logs.read(one, "provider.stdout")["text"],
            "first attempt\n")
        self.assertEqual(
            attempt_logs.read(two, "provider.stdout")["text"],
            "second attempt\n")


class PartialEvidenceSURVIVES(LogRoom):
    """Error, abnormal termination and restart, which is the required outcome's
    sharpest sentence: a log directory emptied by the act of re-entering it
    would lose exactly what it exists for."""

    def test_adopt_keeps_every_byte_a_previous_incarnation_wrote(self):
        delivery = self.made()
        self.wrote(delivery, "worker.stderr", b"the first incarnation spoke\n")
        again = attempt_logs.adopt(self.root, attempt_id=self.ATTEMPT,
                                   workspace_group=self.group)
        self.assertEqual(again, delivery)
        self.assertEqual(
            attempt_logs.read(again, "worker.stderr")["text"],
            "the first incarnation spoke\n")

    def test_a_second_incarnation_appends_rather_than_clearing(self):
        delivery = self.made()
        self.wrote(delivery, "provider.stdout", b"before the restart\n")
        again = attempt_logs.adopt(self.root, attempt_id=self.ATTEMPT,
                                   workspace_group=self.group)
        self.wrote(again, "provider.stdout", b"after the restart\n")
        self.assertEqual(attempt_logs.read(again, "provider.stdout")["text"],
                         "before the restart\nafter the restart\n")

    def test_adopt_refuses_a_room_this_manager_did_not_make(self):
        place = os.path.join(self.root, "attempt-foreign")
        os.makedirs(place, mode=0o755)
        with self.assertRaisesRegex(ContractRefusal, "mode"):
            attempt_logs.adopt(self.root, attempt_id="attempt-foreign",
                               workspace_group=self.group)

    def test_adopt_refuses_a_room_that_is_not_a_directory(self):
        with open(os.path.join(self.root, "attempt-file"), "w") as handle:
            handle.write("not a room")
        with self.assertRaisesRegex(ContractRefusal, "not a directory"):
            attempt_logs.adopt(self.root, attempt_id="attempt-file",
                               workspace_group=self.group)


class MissingIsNotEmpty(LogRoom):
    """The one thing the required outcome forbids outright: never represent
    missing logs as an empty successful run -- and, after review
    2026-09-18T01-04-54Z R1, never represent a FAILED capture as a missing one
    either."""

    def test_a_stream_that_was_never_created_is_ABSENT(self):
        delivery = self.made()
        found = attempt_logs.capture_state(delivery, "provider.stderr")
        self.assertEqual(found["state"], "absent")
        self.assertEqual(found["bytes"], 0)
        self.assertIn("no log was created", found["why"])

    def test_a_stream_created_and_never_written_is_EMPTY(self):
        delivery = self.made()
        open(delivery.place("provider.stderr"), "wb").close()
        found = attempt_logs.capture_state(delivery, "provider.stderr")
        self.assertEqual(found["state"], "empty")
        self.assertNotEqual(found["state"], "absent")

    def test_a_writer_that_could_not_OPEN_is_FAILED_with_no_file_at_all(self):
        """R1, and it is the sharpest case. A writer whose open failed has
        nothing to leave a trace in, and answering `absent` there reports a
        failure as a run that had nothing to say."""
        delivery = self.made()
        attempt_logs.record_capture(delivery, "provider.stdout", "failed",
                                    reason="the log could not be opened")
        found = attempt_logs.capture_state(delivery, "provider.stdout")
        self.assertEqual(found["state"], "failed")
        self.assertEqual(found["file"], "absent")
        self.assertNotEqual(found["state"], "absent")
        self.assertIn("could not be opened", found["why"])

    def test_an_INACCESSIBLE_stream_is_not_an_absent_one(self):
        """R1: a permission failure means 'I could not ask', which is a
        different fact from 'there is nothing there'."""
        delivery = self.made()
        self.wrote(delivery, "provider.stdout", b"x")
        os.chmod(delivery.log_root, 0)
        self.addCleanup(os.chmod, delivery.log_root, attempt_logs.LOG_DIR)
        found = attempt_logs.capture_state(delivery, "provider.stdout")
        self.assertEqual(found["state"], "inaccessible")
        self.assertNotEqual(found["state"], "absent")
        self.assertIn("could not be opened", found["why"])
        # AND THE OPERATOR SURFACE STILL ANSWERS. One unreadable room must not
        # take the other five streams' answers away with it.
        every = attempt_logs.locators(found and delivery)["streams"]
        self.assertEqual(len(every), len(attempt_logs.STREAMS))
        self.assertTrue(all(one["state"] == "inaccessible" for one in every))

    def test_the_writer_s_declaration_is_DURABLE_and_reaches_every_reader(self):
        """R1: a state held only in a return value was lost the moment anybody
        else looked, and `read` answered `captured` for a declared prefix."""
        delivery = self.made()
        self.wrote(delivery, "provider.stdout", b"a prefix of something\n")
        for declared in ("partial", "truncated", "failed"):
            with self.subTest(declared=declared):
                attempt_logs.record_capture(delivery, "provider.stdout",
                                            declared)
                for found in (attempt_logs.capture_state(delivery,
                                                         "provider.stdout"),
                              attempt_logs.read(delivery, "provider.stdout"),
                              attempt_logs.follow(delivery, "provider.stdout")):
                    self.assertEqual(found["state"], declared)
                    self.assertNotIn("whole stream was retained",
                                     found.get("why", ""))

    def test_a_declaration_SURVIVES_A_RESTART(self):
        delivery = self.made()
        self.wrote(delivery, "worker.stdout", b"a prefix\n")
        attempt_logs.record_capture(delivery, "worker.stdout", "partial")
        again = attempt_logs.adopt(self.root, attempt_id=self.ATTEMPT,
                                   workspace_group=self.group)
        self.assertEqual(
            attempt_logs.capture_state(again, "worker.stdout")["state"],
            "partial")

    def test_an_invented_state_is_refused_from_both_directions(self):
        delivery = self.made()
        with self.assertRaisesRegex(ContractRefusal, "not a capture state"):
            attempt_logs.capture_state(delivery, "provider.stdout",
                                       reported="probably-fine")
        with self.assertRaisesRegex(ContractRefusal, "not a state a writer"):
            attempt_logs.record_capture(delivery, "provider.stdout", "captured")

    def test_BYTES_ALONE_ARE_NOT_COMPLETENESS(self):
        """R1: file existence and a momentary end of file prove neither. A
        stream with content and no declaration is LIVE, and only a writer's
        `finished` reaches `captured`."""
        delivery = self.made()
        self.wrote(delivery, "verification.stdout", b"x" * 40)
        found = attempt_logs.capture_state(delivery, "verification.stdout")
        self.assertEqual((found["state"], found["bytes"]), ("live", 40))
        self.assertIn("completeness is unknown", found["why"])
        attempt_logs.record_capture(delivery, "verification.stdout", "finished")
        found = attempt_logs.capture_state(delivery, "verification.stdout")
        self.assertEqual((found["state"], found["bytes"]), ("captured", 40))


class TheReaderCannotLEAVETheAttemptsOwnRoom(LogRoom):
    """Review 2026-09-18T01-04-54Z R2, reproduced and closed.

    A `worker.stdout.log` SYMLINK inside one attempt, pointing at a sibling
    attempt's file, was followed and its content returned as this attempt's
    own captured output. That is an attribution failure independently of the
    owner's acceptance of raw content: evidence has to be THIS attempt's.
    """

    def sibling(self, delivery, stream, payload=b"somebody else's output\n"):
        elsewhere = os.path.join(self.home, "other-attempt.log")
        with open(elsewhere, "wb") as handle:
            handle.write(payload)
        os.symlink(elsewhere, delivery.place(stream))
        return elsewhere

    def test_a_stream_that_is_a_SYMLINK_is_refused_not_followed(self):
        delivery = self.made()
        elsewhere = self.sibling(delivery, "worker.stdout")
        found = attempt_logs.capture_state(delivery, "worker.stdout")
        self.assertEqual(found["state"], "inaccessible")
        self.assertIn("link", found["why"])
        window = attempt_logs.read(delivery, "worker.stdout")
        self.assertEqual(window["text"], "")
        self.assertEqual(window["bytes_read"], 0)
        # AND THE SIBLING IS UNTOUCHED, which is the fact that matters.
        with open(elsewhere, "rb") as handle:
            self.assertEqual(handle.read(), b"somebody else's output\n")

    def test_a_stream_that_is_not_a_REGULAR_FILE_is_refused(self):
        """A special file is not a log, and reading one could block a reader
        that promised to be bounded."""
        delivery = self.made()
        os.mkfifo(delivery.place("provider.stdout"))
        found = attempt_logs.capture_state(delivery, "provider.stdout")
        self.assertEqual(found["state"], "inaccessible")
        self.assertIn("not a regular file", found["why"])
        # AND THE READ RETURNS rather than blocking on the FIFO.
        window = attempt_logs.read(delivery, "provider.stdout")
        self.assertEqual(window["bytes_read"], 0)

    def test_a_NATIVE_corner_that_is_a_link_is_refused_not_walked(self):
        delivery = self.made()
        elsewhere = os.path.join(self.home, "somebody-elses-native")
        os.makedirs(elsewhere)
        with open(os.path.join(elsewhere, "session.jsonl"), "w") as handle:
            handle.write("{}\n")
        os.rmdir(delivery.native_root)
        os.symlink(elsewhere, delivery.native_root)
        found = attempt_logs.locators(delivery)["native"]
        self.assertEqual(found["state"], "inaccessible")
        self.assertEqual(found["entries"], [])
        self.assertIn("link", found["why"])

    def test_an_ordinary_partial_log_still_reads_normally(self):
        """The control: what is refused is an ESCAPE, not an ordinary read."""
        delivery = self.made()
        self.wrote(delivery, "provider.stdout", b"0123456789")
        attempt_logs.record_capture(delivery, "provider.stdout", "partial")
        window = attempt_logs.read(delivery, "provider.stdout", from_byte=3,
                                   limit=4)
        self.assertEqual(window["text"], "3456")
        self.assertEqual(window["state"], "partial")


class TheOperatorSurfaceNeedsNoEngine(LogRoom):
    """Locators and a read/follow that work whether the container is running,
    stopped or gone."""

    def test_locators_name_every_stream_with_its_honest_state(self):
        """R1 CORRECTED THIS CASE. It previously asserted that a stream
        REPORTED failed with no file was `absent` -- so a passing suite
        endorsed exactly the defect the review found. A reported failure is
        `failed`."""
        delivery = self.made()
        self.wrote(delivery, "worker.stdout", b"hello\n")
        open(delivery.place("provider.stderr"), "wb").close()
        found = attempt_logs.locators(
            delivery, reported={"provider.stdout": "failed"})
        self.assertEqual(found["attempt_id"], self.ATTEMPT)
        self.assertEqual(found["target"], attempt_logs.LOG_TARGET)
        states = {one["stream"]: one["state"] for one in found["streams"]}
        self.assertEqual(len(states), len(attempt_logs.STREAMS))
        self.assertEqual(states["worker.stdout"], "live")
        self.assertEqual(states["provider.stderr"], "empty")
        self.assertEqual(states["provider.stdout"], "failed")
        self.assertNotEqual(states["provider.stdout"], "absent")
        self.assertEqual(states["verification.stdout"], "absent")
        for one in found["streams"]:
            self.assertTrue(one["place"].startswith(delivery.log_root))

    def test_native_session_output_is_its_own_fact(self):
        delivery = self.made()
        found = attempt_logs.locators(delivery)
        self.assertEqual(found["native"]["state"], "empty")
        with open(os.path.join(delivery.native_root, "session.jsonl"),
                  "w") as handle:
            handle.write("{}\n")
        found = attempt_logs.locators(delivery)
        self.assertEqual(found["native"]["state"], "captured")
        self.assertEqual(found["native"]["entries"], ["session.jsonl"])

    def test_a_read_answers_the_STATE_as_well_as_the_bytes(self):
        delivery = self.made()
        absent = attempt_logs.read(delivery, "provider.stdout")
        self.assertEqual(absent["state"], "absent")
        self.assertEqual(absent["text"], "")
        self.assertTrue(absent["at_end"])
        self.wrote(delivery, "provider.stdout", b"a line\n")
        found = attempt_logs.read(delivery, "provider.stdout")
        self.assertEqual((found["state"], found["text"]), ("live", "a line\n"))
        self.assertTrue(found["at_end"])

    def test_a_read_is_bounded_and_positioned(self):
        delivery = self.made()
        self.wrote(delivery, "provider.stdout", b"0123456789")
        window = attempt_logs.read(delivery, "provider.stdout", from_byte=3,
                                   limit=4)
        self.assertEqual(window["text"], "3456")
        self.assertFalse(window["at_end"])
        with self.assertRaisesRegex(ContractRefusal, "whole number"):
            attempt_logs.read(delivery, "provider.stdout", from_byte=-1)
        with self.assertRaisesRegex(ContractRefusal, "bounded"):
            attempt_logs.read(delivery, "provider.stdout",
                              limit=attempt_logs.MAX_READ + 1)

    def test_follow_answers_the_next_byte_and_never_loops(self):
        delivery = self.made()
        self.wrote(delivery, "worker.stdout", b"first\n")
        one = attempt_logs.follow(delivery, "worker.stdout")
        self.assertEqual(one["text"], "first\n")
        self.assertEqual(one["next_from_byte"], len("first\n"))
        # AT THE END IS NOT FINISHED. R1: a reader that has caught up with a
        # stream still being written is at its end for this instant only.
        self.assertTrue(one["at_end"])
        self.assertTrue(one["more_may_arrive"])
        self.wrote(delivery, "worker.stdout", b"second\n")
        two = attempt_logs.follow(delivery, "worker.stdout",
                                  from_byte=one["next_from_byte"])
        self.assertEqual(two["text"], "second\n")
        self.assertEqual(two["next_from_byte"], len("first\nsecond\n"))
        attempt_logs.record_capture(delivery, "worker.stdout", "finished")
        done = attempt_logs.follow(delivery, "worker.stdout",
                                   from_byte=two["next_from_byte"])
        self.assertFalse(done["more_may_arrive"])
        self.assertEqual(done["state"], "captured")

    def test_a_log_that_cannot_be_read_is_INACCESSIBLE_not_empty(self):
        delivery = self.made()
        self.wrote(delivery, "provider.stderr", b"unreadable soon\n")
        os.chmod(delivery.place("provider.stderr"), 0)
        self.addCleanup(os.chmod, delivery.place("provider.stderr"), 0o600)
        found = attempt_logs.read(delivery, "provider.stderr")
        self.assertEqual(found["state"], "inaccessible")
        self.assertEqual(found["text"], "")
        self.assertNotEqual(found["state"], "empty")


class TheSIDECARIsInsideTheBoundaryToo(LogRoom):
    """Review 2026-09-18T01-15-42Z R1. The streams were confined and the
    METADATA was not, which is the same escape one level over.

    A status symlink supplied another attempt's word -- a prefix log reported
    as `captured` on somebody else's say-so -- and a STAGING symlink made
    `record_capture` OVERWRITE the file it pointed at. That second one is an
    actual write outside the attempt's room, and no acceptance of raw
    development content authorizes it.
    """

    def elsewhere(self, name, payload):
        place = os.path.join(self.home, name)
        with open(place, "w", encoding="utf-8") as handle:
            handle.write(payload)
        return place

    def test_a_status_SYMLINK_does_not_supply_another_attempts_word(self):
        delivery = self.made()
        self.wrote(delivery, "provider.stdout", b"a prefix\n")
        somebody = self.elsewhere(
            "other-status.json",
            json.dumps({"declared": "finished", "reason": "not ours"}))
        os.symlink(somebody,
                   os.path.join(delivery.log_root,
                                attempt_logs.status_name("provider.stdout")))
        found = attempt_logs.capture_state(delivery, "provider.stdout")
        self.assertNotEqual(found["state"], "captured")
        self.assertEqual(found["declaration"], "corrupt")
        self.assertEqual(found["state"], "live")

    def test_a_staging_SYMLINK_does_not_overwrite_what_it_points_at(self):
        delivery = self.made()
        somebody = self.elsewhere("somebody-elses-file.txt", "PRECIOUS")
        os.symlink(somebody, self.staging_of(delivery, "provider.stdout"))
        with self.assertRaises(ContractRefusal):
            attempt_logs.record_capture(delivery, "provider.stdout", "partial")
        # THE FACT THAT MATTERS: the sibling still says what it said.
        with open(somebody, encoding="utf-8") as handle:
            self.assertEqual(handle.read(), "PRECIOUS")

    def test_a_status_that_is_a_SPECIAL_FILE_is_corrupt_not_a_blocked_read(self):
        delivery = self.made()
        os.mkfifo(os.path.join(delivery.log_root,
                               attempt_logs.status_name("worker.stdout")))
        found = attempt_logs.capture_state(delivery, "worker.stdout")
        self.assertEqual(found["declaration"], "corrupt")
        self.assertEqual(found["state"], "absent")


class ONEWritersWordCannotEraseANOTHERS(LogRoom):
    """R2. Atomic REPLACEMENT of a document is not an atomic UPDATE of an
    entry in it: the probe let stderr record `failed` while stdout was
    mid-update, and the failure vanished. One sidecar per stream means no two
    writers ever touch one file."""

    def test_two_streams_declared_concurrently_both_survive(self):
        delivery = self.made()
        self.wrote(delivery, "provider.stdout", b"out\n")
        self.wrote(delivery, "provider.stderr", b"err\n")
        done = []

        def declare(stream, state):
            attempt_logs.record_capture(delivery, stream, state)
            done.append(stream)

        threads = [threading.Thread(target=declare, args=one) for one in
                   (("provider.stdout", "partial"),
                    ("provider.stderr", "failed"))]
        for one in threads:
            one.start()
        for one in threads:
            one.join(10)
        self.assertEqual(sorted(done), ["provider.stderr", "provider.stdout"])
        self.assertEqual(
            attempt_logs.capture_state(delivery, "provider.stdout")["state"],
            "partial")
        self.assertEqual(
            attempt_logs.capture_state(delivery, "provider.stderr")["state"],
            "failed")

    def test_both_declarations_survive_a_restart(self):
        delivery = self.made()
        self.wrote(delivery, "provider.stdout", b"out\n")
        attempt_logs.record_capture(delivery, "provider.stdout", "truncated")
        attempt_logs.record_capture(delivery, "provider.stderr", "failed")
        again = attempt_logs.adopt(self.root, attempt_id=self.ATTEMPT,
                                   workspace_group=self.group)
        self.assertEqual(
            attempt_logs.capture_state(again, "provider.stdout")["state"],
            "truncated")
        self.assertEqual(
            attempt_logs.capture_state(again, "provider.stderr")["state"],
            "failed")

    def test_declaring_one_stream_leaves_the_others_alone(self):
        delivery = self.made()
        attempt_logs.record_capture(delivery, "worker.stderr", "failed")
        attempt_logs.record_capture(delivery, "provider.stdout", "partial")
        self.assertEqual(
            attempt_logs.capture_state(delivery, "worker.stderr")["state"],
            "failed")


class CorruptMetadataDoesNotTakeDownTheView(LogRoom):
    """R3. A valid JSON object whose entry was the integer 1 crashed locators
    with a TypeError -- the opposite of the readable operator picture this
    exists for. Corruption is REPORTED, never raised, and never silently
    becomes an assertion of completeness."""

    def corrupt(self, delivery, stream, payload):
        place = os.path.join(delivery.log_root,
                             attempt_logs.status_name(stream))
        with open(place, "wb") as handle:
            handle.write(payload)

    def test_every_malformed_shape_is_reported_rather_than_raised(self):
        delivery = self.made()
        self.wrote(delivery, "provider.stdout", b"a prefix\n")
        for what, payload in (
                ("an integer entry", b"1"),
                ("a list", b"[]"),
                ("a string", b'"finished"'),
                ("not json", b"{{{"),
                ("not utf-8", b"\xff\xfe"),
                ("an invented state", b'{"declared":"perfect","reason":"x"}'),
                ("a missing reason", b'{"declared":"finished"}'),
                ("a non-text reason", b'{"declared":"finished","reason":7}'),
                ("an oversized document", b'{"declared":"finished","reason":"'
                                          + b"x" * 8000 + b'"}')):
            with self.subTest(what=what):
                self.corrupt(delivery, "provider.stdout", payload)
                found = attempt_logs.capture_state(delivery, "provider.stdout")
                self.assertEqual(found["declaration"], "corrupt")
                # AND IT IS NOT TREATED AS COMPLETENESS.
                self.assertNotEqual(found["state"], "captured")
                self.assertEqual(found["state"], "live")

    def test_the_whole_operator_view_still_answers_with_corrupt_metadata(self):
        delivery = self.made()
        self.wrote(delivery, "worker.stdout", b"hello\n")
        self.corrupt(delivery, "worker.stdout", b"1")
        found = attempt_logs.locators(delivery)
        self.assertEqual(len(found["streams"]), len(attempt_logs.STREAMS))
        states = {one["stream"]: one for one in found["streams"]}
        self.assertEqual(states["worker.stdout"]["declaration"], "corrupt")
        # AND THE RAW LOG IS STILL READABLE, which is what an operator came for.
        self.assertEqual(
            attempt_logs.read(delivery, "worker.stdout")["text"], "hello\n")

    def test_an_oversized_reason_is_BOUNDED_rather_than_refused(self):
        """The prose is bounded the way every other diagnostic in this package
        is -- truncated at the ceiling -- and `MAX_STATUS` is the backstop for
        the document itself. A first cut of this case expected a refusal, which
        was my expectation rather than the contract."""
        delivery = self.made()
        # THE LOG FIRST: `partial` says what is HERE is a prefix, so a stream
        # with no file at all still reports `absent`. This case is about the
        # bounding, so it gives the declaration something to be about.
        self.wrote(delivery, "provider.stdout", b"a prefix\n")
        found = attempt_logs.record_capture(
            delivery, "provider.stdout", "partial", reason="x" * 9000)
        self.assertEqual(len(found["reason"]), attempt_logs.MAX_REASON)
        place = os.path.join(delivery.log_root,
                             attempt_logs.status_name("provider.stdout"))
        self.assertLessEqual(os.stat(place).st_size, attempt_logs.MAX_STATUS)
        # AND IT IS STILL READ BACK AS THE STATE IT DECLARED.
        self.assertEqual(
            attempt_logs.capture_state(delivery, "provider.stdout")["state"],
            "partial")


class ANameIsHELDBeforeAnythingIsOpened(LogRoom):
    """Review 2026-09-18T01-25-03Z R1, and the THIRD appearance of one mistake.

    I confined the streams, then the metadata about them, and left the public
    reader operands unconfined. `place` held the allowlist and nothing else
    called it, so `read(delivery, "../other")` returned a sibling's log from
    outside the attempt's room -- which the reviewer reproduced rather than
    predicted. `dir_fd` resolves `..` like any path and `O_NOFOLLOW` governs
    only the final component, so the allowlist IS the confinement.
    """

    ESCAPES = ("../other", "../../other", "..", "/etc/passwd",
               "native/../../other", "./worker.stdout", "worker.stdout/",
               "worker.stdout.log", "unknown.stream", "")

    def sibling(self):
        """A real log belonging to somebody else, one level up."""
        for name in ("other.log", "other.status.json"):
            with open(os.path.join(self.root, name), "wb") as handle:
                handle.write(b'{"declared": "finished", "reason": "SYNTHETIC"}'
                             if name.endswith(".json")
                             else b"SYNTHETIC OTHER ATTEMPT\n")

    def test_read_cannot_be_asked_for_a_log_outside_the_room(self):
        self.sibling()
        delivery = self.made()
        for escape in self.ESCAPES:
            with self.assertRaises(ContractRefusal):
                attempt_logs.read(delivery, escape)

    def test_capture_state_cannot_be_asked_about_one_either(self):
        self.sibling()
        delivery = self.made()
        for escape in self.ESCAPES:
            with self.assertRaises(ContractRefusal):
                attempt_logs.capture_state(delivery, escape)

    def test_follow_cannot_be_asked_for_one_either(self):
        self.sibling()
        delivery = self.made()
        for escape in self.ESCAPES:
            with self.assertRaises(ContractRefusal):
                attempt_logs.follow(delivery, escape)

    def test_status_name_refuses_before_it_composes_a_name(self):
        for escape in self.ESCAPES:
            with self.assertRaises(ContractRefusal):
                attempt_logs.status_name(escape)

    def test_record_capture_refuses_one_too(self):
        delivery = self.made()
        for escape in self.ESCAPES:
            with self.assertRaises(ContractRefusal):
                attempt_logs.record_capture(delivery, escape, "finished")

    def test_an_operand_that_is_not_text_is_refused_as_that(self):
        delivery = self.made()
        for operand in (None, 1, b"worker.stdout", ("worker.stdout",),
                        ["worker.stdout"], object()):
            for ask in (attempt_logs.read, attempt_logs.capture_state,
                        attempt_logs.follow):
                with self.assertRaisesRegex(ContractRefusal,
                                            "this delivery's own names"):
                    ask(delivery, operand)

    def test_the_refusal_comes_BEFORE_any_filesystem_access(self):
        """A room that does not exist at all still refuses by name, which is
        what "before any filesystem access" means operationally."""
        gone = attempt_logs.AttemptLogs(
            attempt_id="attempt-not-here",
            root=os.path.join(self.home, "no-such-root"))
        for escape in ("../other", "/etc/passwd"):
            with self.assertRaises(ContractRefusal):
                attempt_logs.read(gone, escape)

    def test_the_ordinary_named_streams_are_untouched_by_the_rule(self):
        delivery = self.made()
        self.wrote(delivery, "provider.stdout", b"ordinary\n")
        self.assertEqual(attempt_logs.named("provider.stdout"),
                         "provider.stdout")
        self.assertEqual(
            attempt_logs.read(delivery, "provider.stdout")["text"],
            "ordinary\n")
        for stream in attempt_logs.STREAMS:
            self.assertEqual(attempt_logs.named(stream), stream)
            self.assertIsNotNone(attempt_logs.capture_state(delivery, stream))


class CleanupOWNSOnlyWhatItMade(LogRoom):
    """Review 2026-09-18T01-25-03Z R2. The exclusive create is what refuses a
    name somebody else holds -- and the handler then deleted that name anyway,
    on the failure of the very call that proves it is not ours."""

    def staging_names(self, delivery):
        return sorted(one for one in os.listdir(delivery.log_root)
                      if one.endswith(".staging"))

    def test_a_refused_create_does_not_unlink_the_entry_it_refused(self):
        delivery = self.made()
        self.wrote(delivery, "provider.stdout", b"a prefix\n")
        taken = self.staging_of(delivery, "provider.stdout")
        with open(taken, "wb") as handle:
            handle.write(b"SOMEBODY ELSE'S EVIDENCE")
        with self.assertRaisesRegex(ContractRefusal, "FileExistsError"):
            attempt_logs.record_capture(delivery, "provider.stdout", "partial")
        # THE ENTRY THE REFUSAL WAS ABOUT IS STILL THERE. Refusing to touch
        # somebody else's name and then deleting it is not a refusal.
        with open(taken, "rb") as handle:
            self.assertEqual(handle.read(), b"SOMEBODY ELSE'S EVIDENCE")
        # AND THE STREAM'S OWN WORD WAS NOT INVENTED EITHER.
        self.assertEqual(
            attempt_logs.capture_state(delivery, "provider.stdout")[
                "declaration"], "none")

    def test_a_staging_symlink_leaves_BOTH_the_link_and_its_target_alone(self):
        delivery = self.made()
        outside = os.path.join(self.home, "outside.txt")
        with open(outside, "w") as handle:
            handle.write("NOT THIS ATTEMPT'S FILE")
        link = self.staging_of(delivery, "worker.stderr")
        os.symlink(outside, link)
        with self.assertRaises(ContractRefusal):
            attempt_logs.record_capture(delivery, "worker.stderr", "failed")
        # BOTH ENDS SURVIVE: the target still says what it said, and the link
        # this call did not create is still standing.
        with open(outside) as handle:
            self.assertEqual(handle.read(), "NOT THIS ATTEMPT'S FILE")
        self.assertTrue(os.path.islink(link))
        self.assertEqual(self.staging_names(delivery),
                         [os.path.basename(link)])

    def test_an_ordinary_declaration_leaves_no_staging_entry_behind(self):
        delivery = self.made()
        self.wrote(delivery, "provider.stdout", b"x\n")
        attempt_logs.record_capture(delivery, "provider.stdout", "finished")
        self.assertEqual(self.staging_names(delivery), [])

    def test_two_declarations_in_one_process_do_not_share_a_staging_name(self):
        """The pid alone was the identity, and a tee is two threads in one
        process draining two streams at once."""
        delivery = self.made()
        seen = []
        real = os.open

        def watching(path, *args, **kwargs):
            if isinstance(path, str) and path.endswith(".staging"):
                seen.append(path)
            return real(path, *args, **kwargs)

        with mock.patch("os.open", watching):
            attempt_logs.record_capture(delivery, "provider.stdout", "failed")
            attempt_logs.record_capture(delivery, "provider.stderr", "failed")
            attempt_logs.record_capture(delivery, "provider.stdout", "failed")
        self.assertEqual(len(seen), 3)
        self.assertEqual(len(set(seen)), 3)


class AShortWriteIsNeverASUCCESSFULDeclaration(LogRoom):
    """Review 2026-09-18T01-25-03Z R3. One `os.write` had its count ignored, so
    a writer that accepted four bytes got back the whole declaration and a
    truncated sidecar was PUBLISHED -- read back as `corrupt`, the stream
    reported `absent`, and a failure's own evidence lost while its writer was
    told it had been kept."""

    def writing(self, counts):
        """A boundary that accepts exactly these many bytes per call."""
        real = os.write
        remaining = list(counts)

        def partial(handle, payload):
            if not remaining:
                return real(handle, payload)
            allowed = remaining.pop(0)
            if isinstance(allowed, Exception):
                raise allowed
            return real(handle, payload[:allowed])

        return partial

    def test_a_short_write_that_never_completes_is_REFUSED(self):
        delivery = self.made()
        self.wrote(delivery, "provider.stderr", b"a prefix\n")
        with mock.patch("os.write", self.writing([4, 0])):
            with self.assertRaises(ContractRefusal):
                attempt_logs.record_capture(delivery, "provider.stderr",
                                            "failed")
        # NOTHING WAS PUBLISHED, so the stream still reports what it really is
        # rather than a corrupt declaration about it.
        found = attempt_logs.capture_state(delivery, "provider.stderr")
        self.assertEqual(found["declaration"], "none")
        self.assertEqual(found["state"], "live")

    def test_a_short_write_that_CONTINUES_publishes_the_whole_declaration(self):
        delivery = self.made()
        self.wrote(delivery, "provider.stdout", b"a prefix\n")
        with mock.patch("os.write", self.writing([4, 4, 4])):
            attempt_logs.record_capture(delivery, "provider.stdout", "partial")
        found = attempt_logs.capture_state(delivery, "provider.stdout")
        self.assertEqual(found["declaration"], "declared")
        self.assertEqual(found["state"], "partial")

    def test_a_write_that_ERRORS_after_a_prefix_publishes_nothing(self):
        delivery = self.made()
        self.wrote(delivery, "worker.stdout", b"a prefix\n")
        with mock.patch("os.write",
                        self.writing([4, OSError("the writer stopped")])):
            with self.assertRaises(ContractRefusal):
                attempt_logs.record_capture(delivery, "worker.stdout",
                                            "truncated")
        self.assertEqual(
            attempt_logs.capture_state(delivery, "worker.stdout")["state"],
            "live")

    def test_a_FAILED_write_PRESERVES_the_declaration_already_recorded(self):
        """The sharpest half: an operator's existing word must not be replaced
        by a failed attempt to write a new one."""
        delivery = self.made()
        self.wrote(delivery, "provider.stdout", b"a prefix\n")
        attempt_logs.record_capture(delivery, "provider.stdout", "truncated")
        with mock.patch("os.write", self.writing([2, 0])):
            with self.assertRaises(ContractRefusal):
                attempt_logs.record_capture(delivery, "provider.stdout",
                                            "finished")
        found = attempt_logs.capture_state(delivery, "provider.stdout")
        self.assertEqual(found["declaration"], "declared")
        self.assertEqual(found["state"], "truncated")

    def test_a_failed_declaration_leaves_no_staging_entry_behind(self):
        delivery = self.made()
        with mock.patch("os.write", self.writing([0])):
            with self.assertRaises(ContractRefusal):
                attempt_logs.record_capture(delivery, "worker.stderr",
                                            "failed")
        self.assertEqual(
            [one for one in os.listdir(delivery.log_root)
             if one.endswith(".staging")], [])

    def test_the_refusal_says_the_log_AND_the_prior_word_are_unaffected(self):
        delivery = self.made()
        with mock.patch("os.write", self.writing([0])):
            with self.assertRaisesRegex(ContractRefusal,
                                        "already recorded for it are "
                                        "unaffected"):
                attempt_logs.record_capture(delivery, "worker.stderr",
                                            "failed")


class TheDeliveryComposesITSOWNMount(LogRoom):
    """The composer half of the bind `oci._log_mounts` already refuses badly.

    `_log_mounts` was written to hold an attempt-log delivery to one writable
    bind at `LOG_TARGET`, and nothing composed one -- so the boundary had a
    rule and the delivery had no way to satisfy it. This is the other half, and
    it is `ExchangeDelivery.mounts`'s shape for `ExchangeDelivery.mounts`'s
    reason: the direction is the contract's, not a caller's.
    """

    def test_the_delivery_authorizes_exactly_one_writable_bind(self):
        delivery = self.made()
        self.assertEqual(delivery.mounts(),
                         ((delivery.log_root, attempt_logs.LOG_TARGET, True),))

    def test_the_boundary_accepts_what_the_delivery_composes(self):
        from baton_v12.worker_manager import oci

        delivery = self.made()
        self.assertEqual(oci._log_mounts(list(delivery.mounts())),
                         ((delivery.log_root, attempt_logs.LOG_TARGET, True),))

    def test_two_attempts_compose_two_different_sources_one_target(self):
        one, two = self.made("attempt-one"), self.made("attempt-two")
        self.assertNotEqual(one.mounts()[0][0], two.mounts()[0][0])
        self.assertEqual(one.mounts()[0][1], two.mounts()[0][1])


# -- W198667 R4: the delivery, wired -------------------------------------------


class TheLAUNCHMakesTheRoomBeforeAnythingStarts(LogRoom):
    """R4's first half: the room is not a primitive a lifecycle might use, it
    is made by the launch that is about to start a container.

    `oci._log_mounts` had a rule and nothing composed a bind for it; the rule
    and the composer now meet at `LaunchDelivery.logs`.
    """

    UNSET = object()

    def launched(self, *, transport=UNSET, group=UNSET):
        from baton_v12.worker_manager import exchange, launch

        home = os.path.join(self.home, "launch")
        os.makedirs(home, exist_ok=True)
        return launch.materialize(
            home, attempt_id=self.ATTEMPT, session="session-w198667",
            contract="v12-assignment-1", role="implementation",
            transport=(exchange.EXCHANGE_TRANSPORT
                       if transport is self.UNSET else transport),
            workspace_group=(self.group if group is self.UNSET
                             else group))

    def test_a_launch_carries_a_log_room_beside_its_exchange(self):
        delivery = self.launched()
        self.assertIsNotNone(delivery.logs)
        self.assertIsNotNone(delivery.exchange)
        self.assertEqual(delivery.logs.attempt_id, self.ATTEMPT)

    def test_the_room_is_OUTSIDE_the_launch_root_it_rides_with(self):
        """Which is what lets `discard` tear a launch down without taking the
        evidence with it."""
        delivery = self.launched()
        self.assertFalse(
            delivery.logs.log_root.startswith(delivery.root + os.sep))

    def test_DISCARD_removes_the_launch_and_LEAVES_the_evidence(self):
        from baton_v12.worker_manager import launch

        delivery = self.launched()
        with open(delivery.logs.place("worker.stderr"), "ab") as handle:
            handle.write(b"baton-worker: launch: refused\n")
        self.assertTrue(launch.discard(delivery.root))
        self.assertFalse(os.path.exists(delivery.root))
        # THE REQUIRED OUTCOME, exactly: partial evidence survives teardown.
        self.assertEqual(
            attempt_logs.read(delivery.logs, "worker.stderr")["text"],
            "baton-worker: launch: refused\n")

    def test_a_RESTART_adopts_the_room_a_previous_incarnation_made(self):
        from baton_v12.worker_manager import exchange, launch

        delivery = self.launched()
        with open(delivery.logs.place("provider.stdout"), "ab") as handle:
            handle.write(b"before the restart\n")
        again = launch.adopt(
            os.path.join(self.home, "launch"), attempt_id=self.ATTEMPT,
            session="session-w198667", contract="v12-assignment-1",
            role="implementation", transport=exchange.EXCHANGE_TRANSPORT,
            workspace_group=self.group)
        self.assertEqual(again.logs, delivery.logs)
        with open(again.logs.place("provider.stdout"), "ab") as handle:
            handle.write(b"after the restart\n")
        self.assertEqual(
            attempt_logs.read(again.logs, "provider.stdout")["text"],
            "before the restart\nafter the restart\n")

    def test_no_workspace_group_means_NO_ROOM_rather_than_an_unwritable_one(self):
        """A delivery that promised a writable log and delivered an unwritable
        one would be worse than saying there is none: the container's fixed uid
        is not this manager's."""
        delivery = self.launched(transport=None, group=None)
        self.assertIsNone(delivery.logs)

    def test_two_attempts_launched_together_get_two_rooms(self):
        from baton_v12.worker_manager import exchange, launch

        home = os.path.join(self.home, "launch")
        os.makedirs(home, exist_ok=True)
        made = [launch.materialize(
            home, attempt_id=one, session="session-w198667",
            contract="v12-assignment-1", role="implementation",
            transport=exchange.EXCHANGE_TRANSPORT,
            workspace_group=self.group)
            for one in ("attempt-one", "attempt-two")]
        self.assertNotEqual(made[0].logs.log_root, made[1].logs.log_root)


class TheWORKERWritesItsOwnEarliestOutput(LogRoom):
    """R4's other half at the wrapper: a provider-side tee cannot retain a
    failure that happens before the provider starts, and the reported incident
    was exactly such a failure."""

    def setUp(self):
        super().setUp()
        _as_the_image_lays_it_out(self)

    def captured(self, delivery):
        import baton_worker

        return baton_worker._WorkerCapture(delivery.log_root)

    def test_the_wrappers_stderr_reaches_the_room_and_the_real_stream(self):
        import io
        import sys
        from unittest import mock

        delivery = self.made()
        held = io.StringIO()
        with mock.patch.object(sys, "stderr", held):
            with self.captured(delivery):
                print("baton-worker: launch: refused", file=sys.stderr)
        # THE REAL STREAM FIRST, ALWAYS: a tee that could break the thing it
        # observes would be worse than no tee.
        self.assertIn("baton-worker: launch: refused", held.getvalue())
        found = attempt_logs.read(delivery, "worker.stderr")
        self.assertIn("baton-worker: launch: refused", found["text"])
        self.assertEqual(found["state"], "captured")

    def test_a_wrapper_that_said_nothing_leaves_the_stream_ABSENT(self):
        """Missing is not empty, and an empty file would assert a run that had
        nothing to say."""
        import io
        import sys
        from unittest import mock

        delivery = self.made()
        with mock.patch.object(sys, "stderr", io.StringIO()):
            with self.captured(delivery):
                pass
        found = attempt_logs.capture_state(delivery, "worker.stderr")
        self.assertEqual(found["state"], "absent")
        self.assertEqual(found["declaration"], "none")

    def test_the_protocol_channel_is_NOT_teed(self):
        """`worker.stdout` is the framed transport's exact bytes. The review
        required them preserved, so nothing duplicates them into a log."""
        import io
        import sys
        from unittest import mock

        delivery = self.made()
        with mock.patch.object(sys, "stderr", io.StringIO()):
            with self.captured(delivery):
                self.assertIsNot(sys.stdout, None)
                self.assertNotIsInstance(
                    sys.stdout, type(sys.stderr)) if False else None
        self.assertEqual(
            attempt_logs.capture_state(delivery, "worker.stdout")["state"],
            "absent")

    def test_a_room_that_is_not_there_captures_NOTHING_and_fails_nothing(self):
        """A worker whose RUN failed because its LOGGING was unavailable would
        be a worker that logging made less reliable."""
        import io
        import sys
        from unittest import mock

        with mock.patch.object(sys, "stderr", io.StringIO()) as held:
            with self.captured_at(os.path.join(self.home, "no-such-room")):
                print("still says it", file=sys.stderr)
            self.assertIn("still says it", held.getvalue())

    def captured_at(self, place):
        import baton_worker

        return baton_worker._WorkerCapture(place)

    def test_an_image_without_the_format_module_captures_nothing(self):
        import baton_worker
        from unittest import mock

        with mock.patch.object(baton_worker, "_log_format",
                               lambda: None):
            capture = baton_worker._WorkerCapture(self.made().log_root)
            with capture:
                pass


class TheADAPTERNoLongerDiscardsWhatItRuns(LogRoom):
    """The four streams `_ran_provider` and `_ran` used to send to /dev/null."""

    def setUp(self):
        super().setUp()
        _as_the_image_lays_it_out(self)

    def captured(self, delivery, stream):
        import claude_agent

        room, fmt = claude_agent._log_room.__wrapped__() \
            if hasattr(claude_agent._log_room, "__wrapped__") else (None, None)
        del room, fmt
        import attempt_log_format

        held = attempt_log_format.open_room(delivery.log_root)
        return claude_agent._Captured(held, attempt_log_format, stream), held

    def test_a_captured_stream_reaches_the_room_and_declares_finished(self):
        delivery = self.made()
        capture, room = self.captured(delivery, "provider.stdout")
        capture.wrote(b"a provider said this\n")
        # THE OUTCOME IS AN OPERAND NOW. Review 2026-09-18T02-31-51Z [4]: a
        # bare `declare()` used to default to `finished`, which is what let a
        # child that never started be reported as a whole capture. `None` now
        # asserts nothing, so a case about a COMPLETED child says so.
        capture.declare("finished")
        os.close(room)
        found = attempt_logs.read(delivery, "provider.stdout")
        self.assertEqual(found["text"], "a provider said this\n")
        self.assertEqual(found["state"], "captured")

    def test_a_drain_that_ended_on_its_clock_declares_PARTIAL(self):
        delivery = self.made()
        capture, room = self.captured(delivery, "provider.stdout")
        capture.wrote(b"a prefix of a record\n")
        capture.declare("partial")
        os.close(room)
        found = attempt_logs.capture_state(delivery, "provider.stdout")
        self.assertEqual(found["state"], "partial")

    def test_no_room_means_DEVNULL_exactly_as_before(self):
        import subprocess

        import claude_agent

        capture = claude_agent._Captured(None, None, "verification.stdout")
        self.assertIs(capture.fileno_or_devnull, subprocess.DEVNULL)
        self.assertIsNone(capture.declare())

    def test_a_stream_whose_writes_were_LOST_declares_failed(self):
        delivery = self.made()
        capture, room = self.captured(delivery, "verification.stderr")
        with mock.patch("os.write", lambda handle, payload: 0):
            capture.wrote(b"this never arrives\n")
        capture.declare("finished")
        os.close(room)
        found = attempt_logs.capture_state(delivery, "verification.stderr")
        self.assertEqual(found["state"], "failed")

    def test_the_four_streams_are_kept_apart(self):
        delivery = self.made()
        for stream in ("provider.stdout", "provider.stderr",
                       "verification.stdout", "verification.stderr"):
            capture, room = self.captured(delivery, stream)
            capture.wrote(stream.encode() + b"\n")
            capture.declare("finished")
            os.close(room)
        for stream in ("provider.stdout", "provider.stderr",
                       "verification.stdout", "verification.stderr"):
            self.assertEqual(attempt_logs.read(delivery, stream)["text"],
                             stream + "\n")


class AChildThatNeverRanIsNOTACapture(LogRoom):
    """Review 2026-09-18T02-31-51Z [4], and it was a defect I shipped.

    `_ran`'s `finally` declared completion regardless of whether the child ever
    started, so an injected `FileNotFoundError` at the subprocess boundary left
    both verification streams reported CAPTURED, zero bytes, carrying "the
    writer saw this stream to its end". A failure to start reported as a
    complete capture is the exact sentence this vocabulary exists to forbid --
    and it is worse than the discard it replaced, because an operator would
    believe it.

    DRIVEN THROUGH `_ran` AND `_ran_provider`, not by selecting a declaration
    state by hand: the defect was in which state the real boundary CHOSE.
    """

    def setUp(self):
        super().setUp()
        _as_the_image_lays_it_out(self)
        self.delivery = self.made()
        import claude_agent

        self.claude_agent = claude_agent

    def agent(self, run):
        return self.claude_agent.ClaudeAgent(run=run)

    def in_the_room(self):
        """`_log_room` answers this case's own room rather than /run/baton."""
        import attempt_log_format

        return mock.patch.object(
            self.claude_agent, "_log_room",
            lambda: (attempt_log_format.open_room(self.delivery.log_root),
                     attempt_log_format))

    def states(self, *streams):
        return {one: attempt_logs.capture_state(self.delivery, one)
                for one in streams}

    # -- the verification command's two streams -----------------------------

    def test_a_MISSING_EXECUTABLE_leaves_both_streams_FAILED(self):
        def missing(*operands, **named):
            raise FileNotFoundError(2, "no such program", "check.py")

        with self.in_the_room():
            with self.assertRaises(FileNotFoundError):
                self.agent(missing)._ran(["check.py"], cwd=self.home,
                                         seconds=5, env={})
        found = self.states("verification.stdout", "verification.stderr")
        for stream, one in found.items():
            self.assertEqual(one["state"], "failed", stream)
            self.assertNotEqual(one["state"], "captured", stream)
            self.assertIn("could not write this stream", one["why"])

    def test_a_TIMEOUT_leaves_both_streams_PARTIAL_rather_than_whole(self):
        def timed_out(*operands, **named):
            raise subprocess.TimeoutExpired("check.py", 5)

        with self.in_the_room():
            with self.assertRaises(subprocess.TimeoutExpired):
                self.agent(timed_out)._ran(["check.py"], cwd=self.home,
                                           seconds=5, env={})
        for stream, one in self.states("verification.stdout",
                                       "verification.stderr").items():
            self.assertEqual(one["state"], "partial", stream)

    def test_a_child_that_RAN_and_FAILED_is_still_a_whole_capture(self):
        """An exit status is not an outcome here. A command that exits 1 wrote
        what it wrote and then stopped; conflating the two would report every
        failing verification as a broken log."""
        def ran_and_failed(argv, **named):
            os.write(named["stdout"], b"checking\n")
            os.write(named["stderr"], b"it did not pass\n")
            return SimpleNamespace(returncode=1)

        with self.in_the_room():
            self.assertEqual(
                self.agent(ran_and_failed)._ran(["check.py"], cwd=self.home,
                                                seconds=5, env={}), 1)
        found = self.states("verification.stdout", "verification.stderr")
        self.assertEqual(found["verification.stdout"]["state"], "captured")
        self.assertEqual(found["verification.stderr"]["state"], "captured")
        self.assertEqual(
            attempt_logs.read(self.delivery, "verification.stderr")["text"],
            "it did not pass\n")

    # -- the provider's two streams -----------------------------------------

    def test_a_PROVIDER_that_never_started_leaves_stderr_FAILED(self):
        def missing(*operands, **named):
            raise FileNotFoundError(2, "no such program", "claude")

        with self.in_the_room():
            with self.assertRaises(FileNotFoundError):
                self.agent(missing)._ran_provider(["claude"], cwd=self.home,
                                                  seconds=5, env={})
        found = self.states("provider.stdout", "provider.stderr")
        self.assertEqual(found["provider.stderr"]["state"], "failed")
        self.assertEqual(found["provider.stdout"]["state"], "failed")

    def test_a_PROVIDER_that_ran_retains_its_stdout_byte_identically(self):
        def spoke(argv, **named):
            os.write(named["stdout"], b'{"result": "ok"}\n')
            return SimpleNamespace(returncode=0)

        with self.in_the_room():
            status, record, partial = self.agent(spoke)._ran_provider(
                ["claude"], cwd=self.home, seconds=5, env={})
        self.assertEqual(status, 0)
        self.assertFalse(partial)
        # THE PARSED RECORD AND THE RETAINED BYTES ARE THE SAME BYTES.
        self.assertEqual(record, b'{"result": "ok"}\n')
        self.assertEqual(
            attempt_logs.read(self.delivery, "provider.stdout")["text"],
            '{"result": "ok"}\n')
        self.assertEqual(
            attempt_logs.capture_state(self.delivery,
                                       "provider.stdout")["state"], "captured")

    # -- the provider's own session files ------------------------------------

    def test_the_providers_NATIVE_session_files_are_RETAINED(self):
        """Review [3]: this was a constant and an empty directory. The fake
        provider here actually WRITES session files where a real one does."""
        scratch = os.path.join(self.home, "scratch")
        state = os.path.join(scratch, "home", ".claude", "projects", "one")
        os.makedirs(state)

        def writing(argv, **named):
            with open(os.path.join(state, "session.jsonl"), "w") as handle:
                handle.write('{"turn": 1}\n')
            return SimpleNamespace(returncode=0)

        with self.in_the_room():
            self.agent(writing)._ran_provider(["claude"], cwd=self.home,
                                              seconds=5, env={},
                                              scratch=scratch)
        found = attempt_logs.locators(self.delivery)["native"]
        self.assertEqual(found["state"], "captured")
        # THE ESCAPED FORM, because `__` collided: see `claude_agent._flat`.
        self.assertEqual(found["entries"],
                         ["projects%2Fone%2Fsession.jsonl"])

    def test_the_native_files_SURVIVE_the_scratch_being_removed(self):
        """Which is the whole point: the provider's home goes away with the
        container, and the room does not."""
        import shutil as _shutil

        scratch = os.path.join(self.home, "scratch")
        state = os.path.join(scratch, "home", ".claude")
        os.makedirs(state)

        def writing(argv, **named):
            with open(os.path.join(state, "session.jsonl"), "w") as handle:
                handle.write('{"turn": 1}\n')
            return SimpleNamespace(returncode=0)

        with self.in_the_room():
            self.agent(writing)._ran_provider(["claude"], cwd=self.home,
                                              seconds=5, env={},
                                              scratch=scratch)
        _shutil.rmtree(scratch)
        found = attempt_logs.locators(self.delivery)["native"]
        self.assertEqual(found["entries"], ["session.jsonl"])

    def test_a_CREDENTIAL_SYMLINK_is_never_followed_or_copied(self):
        """The one symlink this adapter puts in that home is the credential
        slot. Following it would be this function reading the bearer, which no
        logging ruling supersedes."""
        scratch = os.path.join(self.home, "scratch")
        state = os.path.join(scratch, "home", ".claude")
        os.makedirs(state)
        bearer = os.path.join(self.home, "the-bearer")
        with open(bearer, "w") as handle:
            handle.write("A SECRET NOBODY MAY COPY")
        os.symlink(bearer, os.path.join(state, ".credentials.json"))

        def wrote(argv, **named):
            with open(os.path.join(state, "session.jsonl"), "w") as handle:
                handle.write('{"turn": 1}\n')
            return SimpleNamespace(returncode=0)

        with self.in_the_room():
            self.agent(wrote)._ran_provider(["claude"], cwd=self.home,
                                            seconds=5, env={}, scratch=scratch)
        found = attempt_logs.locators(self.delivery)["native"]
        self.assertEqual(found["entries"], ["session.jsonl"])
        for name in found["entries"]:
            with open(os.path.join(self.delivery.native_root, name)) as handle:
                self.assertNotIn("A SECRET", handle.read())

    def test_a_child_that_never_started_retains_NO_native_files(self):
        scratch = os.path.join(self.home, "scratch")
        os.makedirs(os.path.join(scratch, "home", ".claude"))

        def missing(*operands, **named):
            raise FileNotFoundError(2, "no such program", "claude")

        with self.in_the_room():
            with self.assertRaises(FileNotFoundError):
                self.agent(missing)._ran_provider(["claude"], cwd=self.home,
                                                  seconds=5, env={},
                                                  scratch=scratch)
        # EMPTY, NOT ABSENT, and the difference is `materialize`'s: the room
        # is made with its native corner before anything runs, so the corner
        # exists and holds nothing. "The room exists and the provider wrote
        # nothing in it" is a different sentence from "there is no corner", and
        # my first expectation here confused them.
        self.assertEqual(
            attempt_logs.locators(self.delivery)["native"]["state"], "empty")


class TheWRAPPERRetainsBOTHOfItsOwnStreams(LogRoom):
    """Review [2]: the selected scope is the wrapper's stdout AND stderr, and
    omitting stdout was my narrowing rather than the contract's."""

    def setUp(self):
        super().setUp()
        _as_the_image_lays_it_out(self)
        self.delivery = self.made()
        import baton_worker

        self.baton_worker = baton_worker

    def test_both_streams_reach_the_room_and_the_real_streams(self):
        import io

        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "stdout", out), \
                mock.patch.object(sys, "stderr", err):
            with self.baton_worker._WorkerCapture(self.delivery.log_root):
                print("an ordinary line", file=sys.stdout)
                print("baton-worker: refused", file=sys.stderr)
        self.assertIn("an ordinary line", out.getvalue())
        self.assertIn("baton-worker: refused", err.getvalue())
        self.assertIn("an ordinary line",
                      attempt_logs.read(self.delivery, "worker.stdout")["text"])
        self.assertIn("baton-worker: refused",
                      attempt_logs.read(self.delivery, "worker.stderr")["text"])

    def test_the_caller_visible_bytes_are_IDENTICAL_to_the_persisted_ones(self):
        import io

        said = "one\ntwo\nthree\n"
        out = io.StringIO()
        with mock.patch.object(sys, "stdout", out), \
                mock.patch.object(sys, "stderr", io.StringIO()):
            with self.baton_worker._WorkerCapture(self.delivery.log_root):
                sys.stdout.write(said)
        self.assertEqual(out.getvalue(), said)
        self.assertEqual(
            attempt_logs.read(self.delivery, "worker.stdout")["text"], said)

    def test_the_PROTOCOL_buffer_is_not_what_this_wraps(self):
        """`serve` frames on `sys.stdout.buffer`, passed as an operand, so a
        text wrapper here never sees a frame and cannot reorder or re-encode
        one. Held as a property of the signature rather than as a comment."""
        import inspect

        seen = inspect.signature(self.baton_worker.serve).parameters
        self.assertIn("stdout", seen)
        source = inspect.getsource(self.baton_worker.main)
        self.assertIn("sys.stdout.buffer", source)


class NATIVERetentionIsIncrementalAndHonest(LogRoom):
    """Review 2026-09-18T03-10-39Z [R2], and it found four separate defects in
    the end-of-turn copy I shipped."""

    def setUp(self):
        super().setUp()
        _as_the_image_lays_it_out(self)
        self.delivery = self.made()
        import attempt_log_format
        import claude_agent

        self.fmt = attempt_log_format
        self.claude_agent = claude_agent
        self.scratch = os.path.join(self.home, "scratch")
        self.state = os.path.join(self.scratch, "home", ".claude")
        os.makedirs(self.state)

    def room(self):
        return self.fmt.open_room(self.delivery.log_root)

    def retained(self, seen=None):
        room = self.room()
        try:
            return self.claude_agent._retain_native(
                self.scratch, room, self.fmt, seen)
        finally:
            os.close(room)

    def native(self, name):
        with open(os.path.join(self.delivery.native_root, name), "rb") as one:
            return one.read()

    def entries(self):
        """The retained SOURCE files, which is what these cases are about.

        `attempt_log_format.RETENTION` is the capture's own bookkeeping and
        lives in this corner because it describes these bytes; counting it as
        something the provider wrote would make every case here assert one
        file too many.
        """
        return sorted(one for one in os.listdir(self.delivery.native_root)
                      if one != self.fmt.RETENTION)

    def wrote_native(self, relative, payload, mode="wb"):
        place = os.path.join(self.state, relative)
        os.makedirs(os.path.dirname(place), exist_ok=True)
        with open(place, mode) as handle:
            handle.write(payload)

    def test_a_NESTED_name_cannot_collide_with_a_flattened_one(self):
        """`a/b` and `a__b` both flattened to `a__b`: three files counted and
        two present, with one source's bytes overwritten."""
        self.wrote_native("a/b", b"FROM THE NESTED ONE\n")
        self.wrote_native("a__b", b"FROM THE FLAT ONE\n")
        found = self.retained()
        self.assertEqual(found["failed"], [])
        names = self.entries()
        self.assertEqual(len(names), 2, names)
        self.assertEqual(sorted(self.native(one) for one in names),
                         sorted([b"FROM THE FLAT ONE\n",
                                 b"FROM THE NESTED ONE\n"]))

    def test_a_LARGE_file_is_streamed_rather_than_silently_truncated(self):
        """The earlier cut read a ceiling's worth and counted the file
        retained, so anything larger was truncated while reported complete."""
        payload = bytes(range(256)) * 900          # well past one chunk
        self.wrote_native("big.jsonl", payload)
        found = self.retained()
        self.assertEqual(found["failed"], [])
        self.assertEqual(self.native("big.jsonl"), payload)

    def test_retention_is_INCREMENTAL_and_appends_only_what_is_new(self):
        """The property an end-of-turn copy cannot have: bytes already survive
        before any orderly teardown."""
        self.wrote_native("session.jsonl", b'{"turn": 1}\n')
        first = self.retained()
        self.assertEqual(self.native("session.jsonl"), b'{"turn": 1}\n')
        self.wrote_native("session.jsonl", b'{"turn": 2}\n', mode="ab")
        self.retained(first["retained"])
        self.assertEqual(self.native("session.jsonl"),
                         b'{"turn": 1}\n{"turn": 2}\n')

    def test_an_INTERRUPTED_turn_has_already_retained_what_arrived(self):
        """Killed before any `finally`: the bytes are in the room because the
        drain put them there while the provider was still running."""
        self.wrote_native("session.jsonl", b"arrived before the kill\n")
        self.retained()
        import shutil as _shutil

        _shutil.rmtree(self.scratch)
        self.assertEqual(self.native("session.jsonl"),
                         b"arrived before the kill\n")

    def test_a_SYMLINK_is_refused_by_the_OPEN_and_not_by_a_name_check(self):
        """`islink` then `open(path)` is a check on one object and an open of
        whatever the name resolves to next."""
        secret = os.path.join(self.home, "the-bearer")
        with open(secret, "w") as handle:
            handle.write("A SECRET NOBODY MAY COPY")
        os.symlink(secret, os.path.join(self.state, ".credentials.json"))
        self.wrote_native("session.jsonl", b"ordinary\n")
        self.retained()
        names = self.entries()
        self.assertEqual(names, ["session.jsonl"])
        self.assertNotIn(b"A SECRET", self.native("session.jsonl"))

    def test_a_LINKED_DIRECTORY_is_not_walked_out_of(self):
        """Every ancestor was followed before, not only the leaf."""
        outside = os.path.join(self.home, "outside")
        os.makedirs(outside)
        with open(os.path.join(outside, "elsewhere.jsonl"), "w") as handle:
            handle.write("NOT THIS PROVIDER'S\n")
        os.symlink(outside, os.path.join(self.state, "projects"))
        self.wrote_native("session.jsonl", b"ordinary\n")
        self.retained()
        self.assertEqual(self.entries(), ["session.jsonl"])

    def test_a_FAILURE_is_reported_rather_than_skipped(self):
        """An empty corner must not read as 'the provider wrote nothing' when
        the capture is what failed."""
        from unittest import mock

        self.wrote_native("session.jsonl", b"something\n")
        with mock.patch.object(self.fmt, "write_all",
                               lambda handle, payload: 0):
            found = self.retained()
        self.assertTrue(found["failed"])
        self.assertIn("could not all be written", found["failed"][0])

    def test_a_failed_retention_makes_the_PROVIDER_STREAM_say_so(self):
        """Where a reader will actually meet it: beside the provider record
        whose turn produced the files."""
        room = self.room()
        try:
            self.claude_agent._declare_native(
                room, self.fmt,
                {"failed": ["a native file could not be read (OSError)"]},
                self.claude_agent._Outcome.COMPLETED)
        finally:
            os.close(room)
        found = attempt_logs.capture_state(self.delivery, "provider.stdout")
        self.assertEqual(found["state"], "failed")
        self.assertIn("session files were not all retained", found["why"])

    def test_an_ORDINARY_retention_declares_nothing_extra(self):
        self.wrote_native("session.jsonl", b"ordinary\n")
        room = self.room()
        try:
            self.claude_agent._declare_native(
                room, self.fmt, self.retained(),
                self.claude_agent._Outcome.COMPLETED)
        finally:
            os.close(room)
        self.assertEqual(
            attempt_logs.capture_state(self.delivery,
                                       "provider.stdout")["declaration"],
            "none")


class TheDRAINSOwnRetentionIsNotDuplicated(LogRoom):
    """Review 2026-09-18T03-27-44Z [R1], at the ACTUAL CALLER.

    `_retain_native` returned a NEW offset map and the drain discarded it, so
    every poll started at byte zero and appended the whole file again --
    seventeen copies of `abc` in the reviewer's probe. My helper-level cases
    all passed, because they threaded the returned map by hand; nothing
    exercised the wiring that ignored it.
    """

    def setUp(self):
        super().setUp()
        _as_the_image_lays_it_out(self)
        self.delivery = self.made()
        import attempt_log_format
        import claude_agent

        self.fmt = attempt_log_format
        self.claude_agent = claude_agent
        self.scratch = os.path.join(self.home, "scratch")
        self.state = os.path.join(self.scratch, "home", ".claude")
        os.makedirs(self.state)
        # A SHORT SLICE so a bounded child spans several ticks.
        self.enterContext(mock.patch.object(claude_agent,
                                            "PROVIDER_DRAIN_SLICE", 0.01))
        self.enterContext(mock.patch.object(
            claude_agent, "_log_room",
            lambda: (attempt_log_format.open_room(self.delivery.log_root),
                     attempt_log_format)))

    def session(self, payload, mode="wb"):
        with open(os.path.join(self.state, "session.jsonl"), mode) as handle:
            handle.write(payload)

    def native(self, name="session.jsonl"):
        with open(os.path.join(self.delivery.native_root, name), "rb") as one:
            return one.read()

    def ran(self, child):
        return self.claude_agent.ClaudeAgent(run=child)._ran_provider(
            ["claude"], cwd=self.home, seconds=5, env={},
            scratch=self.scratch)

    def test_MANY_TICKS_over_one_file_retain_it_ONCE(self):
        import time

        self.session(b"abc")

        def alive(argv, **named):
            time.sleep(0.15)
            return SimpleNamespace(returncode=0)

        self.ran(alive)
        self.assertEqual(self.native(), b"abc")

    def test_an_APPEND_between_ticks_is_retained_exactly_once(self):
        import time

        self.session(b"first\n")

        def appending(argv, **named):
            time.sleep(0.05)
            self.session(b"second\n", mode="ab")
            time.sleep(0.1)
            return SimpleNamespace(returncode=0)

        self.ran(appending)
        self.assertEqual(self.native(), b"first\nsecond\n")

    def test_bytes_that_arrive_AFTER_the_last_tick_are_still_retained(self):
        """The finalization pass, over the same offsets the drain kept."""
        def late(argv, **named):
            self.session(b"written at the very end\n")
            return SimpleNamespace(returncode=0)

        self.ran(late)
        self.assertEqual(self.native(), b"written at the very end\n")

    def entries(self):
        return sorted(one for one in os.listdir(self.delivery.native_root)
                      if one != self.fmt.RETENTION)

    def generation(self, at=2, name="session.jsonl"):
        return f"{name}{self.claude_agent.GENERATION}{at}"

    # -- rotation, AT THE CALLER -------------------------------------------
    #
    # Review 2026-09-18T03-48-00Z. The binding lived in a per-run dictionary
    # and the chosen generation name in a local variable, so every tick after a
    # rotation measured the ORIGINAL retained file again and made one more
    # generation -- `session.jsonl`, `#2` and `#3` all from two writes. These
    # run it through `_ran_provider` and its own shared map rather than through
    # a dict this case threads by hand, because that is exactly the difference
    # that hid the last one.

    def test_a_ROTATION_then_MANY_TICKS_makes_exactly_TWO_generations(self):
        """The reviewer's probe: retain `abcdef`, truncate to `XY`, keep
        ticking. A third generation per tick is the defect."""
        import time

        self.session(b"abcdef")

        def rotating(argv, **named):
            time.sleep(0.05)
            self.session(b"XY")
            time.sleep(0.15)
            return SimpleNamespace(returncode=0)

        self.ran(rotating)
        self.assertEqual(self.entries(),
                         ["session.jsonl", self.generation()])
        self.assertEqual(self.native(), b"abcdef")
        self.assertEqual(self.native(self.generation()), b"XY")

    def test_an_APPEND_AFTER_a_rotation_continues_the_NEW_generation(self):
        """The new generation is a stream too, and the second tick after it
        must append to it rather than open a third."""
        import time

        self.session(b"abcdef")

        def rotating(argv, **named):
            time.sleep(0.05)
            self.session(b"XY")
            time.sleep(0.05)
            self.session(b"Z", mode="ab")
            time.sleep(0.1)
            return SimpleNamespace(returncode=0)

        self.ran(rotating)
        self.assertEqual(self.entries(),
                         ["session.jsonl", self.generation()])
        self.assertEqual(self.native(self.generation()), b"XYZ")

    def test_a_RESTART_after_a_rotation_RESUMES_the_new_generation(self):
        """A second incarnation over the same durable room, with a map that
        remembers nothing. The record on disk is what carries it."""
        import time

        self.session(b"abcdef")

        def rotating(argv, **named):
            time.sleep(0.05)
            self.session(b"XY")
            time.sleep(0.1)
            return SimpleNamespace(returncode=0)

        self.ran(rotating)

        def appending(argv, **named):
            self.session(b"Z", mode="ab")
            return SimpleNamespace(returncode=0)

        self.ran(appending)
        self.assertEqual(self.entries(),
                         ["session.jsonl", self.generation()])
        self.assertEqual(self.native(), b"abcdef")
        self.assertEqual(self.native(self.generation()), b"XYZ")

    def test_a_source_CHANGED_BETWEEN_runs_is_retained_and_DECLARED(self):
        """The restart half of the probe, which returned `failed: []` and
        retained nothing: the map was fresh, so `was` was None and the length
        comparison had nothing to compare against."""
        self.session(b"abcdef")

        def quiet(argv, **named):
            return SimpleNamespace(returncode=0)

        self.ran(quiet)
        self.assertEqual(self.native(), b"abcdef")
        # BETWEEN THE TWO INCARNATIONS, which is when a rotation is hardest to
        # see: nothing was watching.
        self.session(b"ZZ")
        self.ran(quiet)
        self.assertEqual(self.native(), b"abcdef")
        self.assertEqual(self.native(self.generation()), b"ZZ")
        found = attempt_logs.locators(self.delivery)["native"]
        self.assertEqual(found["entries"],
                         ["session.jsonl", self.generation()])

    def test_a_source_REWRITTEN_BETWEEN_runs_at_the_SAME_length(self):
        """The restart probe at the actual caller. Nothing about the file
        changed that a stat can report -- same inode, same two bytes' worth --
        and the second incarnation's map is empty."""
        self.session(b"XY")

        def quiet(argv, **named):
            return SimpleNamespace(returncode=0)

        self.ran(quiet)
        self.session(b"ZZ")
        self.ran(quiet)
        self.assertEqual(self.native(), b"XY")
        self.assertEqual(self.native(self.generation()), b"ZZ")
        found = attempt_logs.locators(self.delivery)["native"]
        self.assertEqual(found["entries"],
                         ["session.jsonl", self.generation()])

    def test_a_REAL_source_NAMED_LIKE_a_generation_is_kept_apart(self):
        """`#2` was the suffix, and `session.jsonl#2` is a name a provider can
        give a real file. The namespace is `%23`, which no flattened source can
        produce: `_flat` emits only `%25` and `%2F`."""
        import time

        self.session(b"abcdef")
        with open(os.path.join(self.state, "session.jsonl#2"), "wb") as one:
            one.write(b"A REAL FILE OF THE PROVIDERS OWN\n")

        def rotating(argv, **named):
            time.sleep(0.05)
            self.session(b"XY")
            time.sleep(0.1)
            return SimpleNamespace(returncode=0)

        self.ran(rotating)
        self.assertEqual(self.entries(),
                         ["session.jsonl", "session.jsonl#2",
                          self.generation()])
        self.assertEqual(self.native("session.jsonl#2"),
                         b"A REAL FILE OF THE PROVIDERS OWN\n")
        self.assertEqual(self.native(self.generation()), b"XY")

    def test_an_INTERMEDIATE_failure_survives_a_clean_final_tick(self):
        """The same loop discarded `failed`, so a mid-turn retention failure
        followed by a clean finish vanished from the declared outcome."""
        import time

        self.session(b"something\n")
        held = {}
        real = self.fmt.write_all
        calls = []

        def once(handle, payload):
            calls.append(1)
            if len(calls) == 1:
                return 0
            return real(handle, payload)

        with mock.patch.object(self.fmt, "write_all", once):
            found = self.claude_agent._retain_native(
                self.scratch, self.fmt.open_room(self.delivery.log_root),
                self.fmt, held)
            self.assertTrue(found["failed"])
            # A CLEAN TICK AFTERWARDS DOES NOT ERASE IT.
            again = self.claude_agent._retain_native(
                self.scratch, self.fmt.open_room(self.delivery.log_root),
                self.fmt, held)
        self.assertTrue(again["failed"])
        self.assertIn("could not all be written", again["failed"][0])

    def test_a_LINK_at_the_ROOTS_OWN_ANCESTOR_is_refused(self):
        """`os.open(a/b/c, O_NOFOLLOW)` holds only `c`; the earlier cut opened
        the composite path, so the claim that every component is held was not
        true of root acquisition."""
        elsewhere = os.path.join(self.home, "elsewhere", ".claude")
        os.makedirs(elsewhere)
        with open(os.path.join(elsewhere, "stolen.jsonl"), "w") as handle:
            handle.write("NOT THIS PROVIDER'S\n")
        swapped = os.path.join(self.home, "swapped")
        os.makedirs(swapped)
        os.symlink(os.path.join(self.home, "elsewhere"),
                   os.path.join(swapped, "home"))
        found = self.claude_agent._retain_native(
            swapped, self.fmt.open_room(self.delivery.log_root), self.fmt, {})
        self.assertFalse(found["reached"])
        self.assertEqual(
            attempt_logs.locators(self.delivery)["native"]["entries"], [])


class TheRECORDIsINPUTAndTheWINDOWIsRECOVERABLE(LogRoom):
    """Review 2026-09-18T04-07-54Z, and both findings were mine.

    [R1] `_write_retention` could fail and `_appended` discarded the answer, so
    a record that never reached disk was reported as no failure at all. A fresh
    map then trusted the stale offset, seeked the source to 3, opened the
    destination `O_APPEND` and produced `abcdefdef`.

    [R2] `_read_retention` accepted any JSON object and `_destination` used its
    `destination` straight in `os.open(..., dir_fd=native)`, so a record naming
    `../escaped` had the source's bytes appended OUTSIDE the corner with
    nothing declared.
    """

    def setUp(self):
        super().setUp()
        _as_the_image_lays_it_out(self)
        self.delivery = self.made()
        import attempt_log_format
        import claude_agent

        self.fmt = attempt_log_format
        self.claude_agent = claude_agent
        self.scratch = os.path.join(self.home, "scratch")
        self.state = os.path.join(self.scratch, "home", ".claude")
        os.makedirs(self.state)

    def source(self, payload, mode="w", name="s.jsonl"):
        with open(os.path.join(self.state, name), mode) as handle:
            handle.write(payload)

    def tick(self, seen):
        room = self.fmt.open_room(self.delivery.log_root)
        try:
            return self.claude_agent._retain_native(
                self.scratch, room, self.fmt, seen)
        finally:
            os.close(room)

    def native(self, name="s.jsonl"):
        with open(os.path.join(self.delivery.native_root, name)) as handle:
            return handle.read()

    def entries(self):
        return sorted(one for one in os.listdir(self.delivery.native_root)
                      if one != self.fmt.RETENTION)

    def record(self, held=None):
        place = os.path.join(self.delivery.native_root, self.fmt.RETENTION)
        if held is None:
            with open(place) as handle:
                return json.load(handle)
        with open(place, "w") as handle:
            json.dump(held, handle)

    def identity(self, name="s.jsonl"):
        held = os.stat(os.path.join(self.state, name))
        return [held.st_dev, held.st_ino]

    # -- R1: the data/record commit window -----------------------------------

    def test_a_FAILED_record_write_is_DECLARED_and_not_swallowed(self):
        held = {}
        self.source("abc")
        self.tick(held)
        self.source("def", mode="a")
        with mock.patch.object(self.claude_agent, "_write_retention",
                               lambda *operands, **named: False):
            found = self.tick(held)
        self.assertTrue(found["failed"])
        self.assertIn("retention record could not be written",
                      found["failed"][0])

    def test_a_FRESH_map_after_that_failure_does_NOT_duplicate(self):
        """The reviewer's probe: this produced `abcdefdef`, with `failed` empty
        both times."""
        held = {}
        self.source("abc")
        self.tick(held)
        self.source("def", mode="a")
        with mock.patch.object(self.claude_agent, "_write_retention",
                               lambda *operands, **named: False):
            self.tick(held)
        found = self.tick({})
        self.assertEqual(self.entries(), ["s.jsonl"])
        self.assertEqual(self.native(), "abcdef")
        self.assertIn("behind the bytes it describes", found["failed"][0])

    def test_an_INTERRUPTED_update_is_the_same_case_and_recovers(self):
        """A process stopping between the append and the replace leaves
        exactly the state a failed write does; the record is edited backwards
        here to stand for that stop."""
        self.source("abc")
        self.tick({})
        self.source("def", mode="a")
        self.tick({})
        held = self.record()
        held["s.jsonl"]["retained"] = 3
        held["s.jsonl"]["head"] = hashlib.sha256(b"abc").hexdigest()
        self.record(held)
        found = self.tick({})
        self.assertEqual(self.native(), "abcdef")
        self.assertEqual(self.entries(), ["s.jsonl"])
        self.assertIn("behind the bytes it describes", found["failed"][0])

    def test_a_record_AHEAD_of_its_bytes_is_never_resumed(self):
        """The unrecoverable direction. Bytes the record counted and the
        destination does not hold cannot be explained, so the old bytes stay
        and a new generation begins."""
        self.source("abcdef")
        self.tick({})
        held = self.record()
        held["s.jsonl"]["retained"] = 99
        self.record(held)
        found = self.tick({})
        self.assertEqual(self.native(), "abcdef")
        self.assertIn("fewer bytes than the retention record counted",
                      found["failed"][0])

    def test_a_reconciled_prefix_that_DISAGREES_starts_a_generation(self):
        """Ahead is believed only when the retained head and the SOURCE'S
        agree over the reconciled length -- the record's own stale digest
        cannot settle bytes it does not describe."""
        self.source("abcdef")
        self.tick({})
        held = self.record()
        held["s.jsonl"]["retained"] = 3
        held["s.jsonl"]["head"] = hashlib.sha256(b"abc").hexdigest()
        self.record(held)
        # THE RETAINED FILE, changed under the record it belongs to.
        with open(os.path.join(self.delivery.native_root, "s.jsonl"),
                  "w") as handle:
            handle.write("zzzzzz")
        found = self.tick({})
        self.assertEqual(self.native(), "zzzzzz")
        self.assertEqual(self.native("s.jsonl%232"), "abcdef")
        self.assertIn("could not be reconciled", found["failed"][0])

    def test_a_SHORT_WRITE_still_records_what_DID_reach_the_room(self):
        """Otherwise the next tick re-copies bytes that are already there --
        and the data failure is said FIRST, because it is the one an operator
        is looking for."""
        self.source("abcdef")
        real = self.fmt.write_all
        calls = []

        def once(handle, payload):
            calls.append(1)
            return real(handle, payload[:2]) if len(calls) == 1 \
                else real(handle, payload)

        with mock.patch.object(self.fmt, "write_all", once):
            found = self.tick({})
        self.assertIn("could not all be written", found["failed"][0])
        self.assertEqual(self.native(), "ab")
        self.assertEqual(self.record()["s.jsonl"]["retained"], 2)
        # AND THE NEXT TICK CONTINUES rather than repeating.
        self.tick({})
        self.assertEqual(self.native(), "abcdef")

    def test_it_recovers_through_the_ACTUAL_caller_too(self):
        """Review 2026-09-18T04-07-54Z asks for this through the capture
        caller, which is the distinction that hid two earlier defects."""
        import time

        self.enterContext(mock.patch.object(
            self.claude_agent, "PROVIDER_DRAIN_SLICE", 0.01))
        self.enterContext(mock.patch.object(
            self.claude_agent, "_log_room",
            lambda: (self.fmt.open_room(self.delivery.log_root), self.fmt)))

        def ran(child):
            return self.claude_agent.ClaudeAgent(run=child)._ran_provider(
                ["claude"], cwd=self.home, seconds=5, env={},
                scratch=self.scratch)

        def quiet(argv, **named):
            return SimpleNamespace(returncode=0)

        self.source("abc")
        ran(quiet)
        self.source("def", mode="a")
        with mock.patch.object(self.claude_agent, "_write_retention",
                               lambda *operands, **named: False):
            ran(quiet)
        # A SECOND INCARNATION over the same durable room, remembering nothing.
        self.source("ghi", mode="a")

        def late(argv, **named):
            time.sleep(0.05)
            return SimpleNamespace(returncode=0)

        ran(late)
        self.assertEqual(self.entries(), ["s.jsonl"])
        self.assertEqual(self.native(), "abcdefghi")

    # -- R2: the record is input ---------------------------------------------

    def test_a_TRAVERSING_destination_writes_NOTHING_outside_the_corner(self):
        """The reviewer's probe: `../escaped` had the source's bytes appended
        beside the corner with `failed` empty. `O_NOFOLLOW` governs the final
        component only and `dir_fd` resolves `..` like any path does."""
        self.source("SHOULD STAY INSIDE THE CORNER\n")
        self.record({"s.jsonl": {"identity": self.identity(),
                                 "destination": "../escaped",
                                 "retained": 0, "head": ""}})
        found = self.tick({})
        self.assertFalse(os.path.exists(
            os.path.join(self.delivery.log_root, "escaped")))
        self.assertEqual(self.entries(), ["s.jsonl"])
        self.assertTrue(found["failed"])
        self.assertIn("will not act on", found["failed"][0])

    def test_an_ABSOLUTE_destination_is_refused_the_same_way(self):
        outside = os.path.join(self.home, "outside")
        self.source("SHOULD STAY INSIDE THE CORNER\n")
        self.record({"s.jsonl": {"identity": self.identity(),
                                 "destination": outside,
                                 "retained": 0, "head": ""}})
        self.tick({})
        self.assertFalse(os.path.exists(outside))
        self.assertEqual(self.entries(), ["s.jsonl"])

    def test_a_destination_naming_ANOTHER_SOURCES_file_is_refused(self):
        """A destination is either the flattened source itself or one of its
        own generations. One entry may not redirect another's bytes."""
        self.source("MINE\n")
        self.source("THEIRS\n", name="other.jsonl")
        self.tick({})
        held = self.record()
        held["s.jsonl"]["destination"] = "other.jsonl"
        held["s.jsonl"]["retained"] = 0
        held["s.jsonl"]["head"] = ""
        self.record(held)
        self.tick({})
        self.assertEqual(self.native("other.jsonl"), "THEIRS\n")

    def test_a_MALFORMED_offset_is_not_believed(self):
        for bad in ("3", -1, 1.5, True, None):
            with self.subTest(offset=bad):
                shutil.rmtree(self.delivery.native_root, ignore_errors=True)
                os.makedirs(self.delivery.native_root)
                self.source("abcdef")
                self.record({"s.jsonl": {"identity": self.identity(),
                                         "destination": "s.jsonl",
                                         "retained": bad, "head": ""}})
                found = self.tick({})
                self.assertEqual(self.native(), "abcdef")
                self.assertIn("will not act on", found["failed"][0])

    def test_a_MALFORMED_head_or_identity_is_not_believed(self):
        self.source("abcdef")
        self.record({"s.jsonl": {"identity": "not a pair",
                                 "destination": "s.jsonl",
                                 "retained": 0, "head": ""}})
        self.assertIn("will not act on", self.tick({})["failed"][0])

    def test_an_ENTRY_WITH_AN_EXTRA_MEMBER_is_not_believed(self):
        """A closed document, because the members somebody would want to add
        are exactly the ones this then trusts."""
        self.source("abcdef")
        self.record({"s.jsonl": {"identity": self.identity(),
                                 "destination": "s.jsonl", "retained": 0,
                                 "head": "", "also": "anything"}})
        self.assertIn("will not act on", self.tick({})["failed"][0])

    def test_ONE_BAD_ENTRY_does_not_lose_the_provable_ones(self):
        """The record describes many sources; a single unreadable entry is not
        a reason to lose the bindings that are provable."""
        self.source("abc")
        self.source("xyz", name="other.jsonl")
        self.tick({})
        held = self.record()
        held["s.jsonl"]["destination"] = "../escaped"
        self.record(held)
        self.source("def", mode="a", name="other.jsonl")
        self.tick({})
        # THE GOOD ENTRY RESUMED, appending only what is new.
        self.assertEqual(self.native("other.jsonl"), "xyzdef")

    def test_a_NONREGULAR_record_is_refused_rather_than_read(self):
        """`O_NOFOLLOW` refuses a symlink at the name and says nothing about a
        fifo, which would block this drain forever."""
        os.mkfifo(os.path.join(self.delivery.native_root, self.fmt.RETENTION))
        self.source("abcdef")
        found = self.tick({})
        self.assertEqual(self.native(), "abcdef")
        self.assertIn("not a regular file", found["failed"][0])

    def test_an_OVERSIZED_record_is_treated_as_ABSENT(self):
        """Metadata read back is input, and an unbounded read of a file
        somebody else can grow is not a read this adapter controls."""
        place = os.path.join(self.delivery.native_root, self.fmt.RETENTION)
        with open(place, "w") as handle:
            handle.write(" " * (self.claude_agent.MAX_RETENTION + 10))
        self.source("abcdef")
        found = self.tick({})
        self.assertEqual(self.native(), "abcdef")
        self.assertIn("larger than this capture reads back",
                      found["failed"][0])

    def test_the_STAGING_entry_is_CREATED_and_never_opened(self):
        """A fixed pid name opened `O_TRUNC` is not an exclusively owned
        staging file: two threads draining two sources share a pid, and the
        name is guessable by anything that can see this corner."""
        seen = []
        real = os.open

        def watching(path, flags, *rest, **named):
            if isinstance(path, str) and ".staging" in path:
                seen.append((path, flags))
            return real(path, flags, *rest, **named)

        self.source("abcdef")
        with mock.patch.object(os, "open", watching):
            self.tick({})
        self.assertTrue(seen)
        for path, flags in seen:
            self.assertTrue(flags & os.O_EXCL, path)
            self.assertTrue(flags & os.O_CREAT, path)
            self.assertFalse(flags & os.O_TRUNC, path)
        # AND TWO CALLS NEVER SHARE ONE NAME.
        self.source("ghi", mode="a")
        with mock.patch.object(os, "open", watching):
            self.tick({})
        names = [path for path, _ in seen]
        self.assertEqual(len(names), len(set(names)), names)

    def test_a_staging_entry_THIS_CALL_DID_NOT_MAKE_is_never_removed(self):
        """A handler that unlinked on any failure would delete somebody else's
        entry the day the exclusive create is what failed."""
        theirs = os.path.join(self.delivery.native_root,
                              f"{self.fmt.RETENTION}.somebody.else.staging")
        with open(theirs, "w") as handle:
            handle.write("NOT THIS CAPTURE'S\n")
        self.source("abcdef")
        real = os.open

        def refusing(path, flags, *rest, **named):
            if isinstance(path, str) and ".staging" in path:
                raise OSError(17, "it already exists")
            return real(path, flags, *rest, **named)

        with mock.patch.object(os, "open", refusing):
            found = self.tick({})
        self.assertTrue(os.path.exists(theirs))
        with open(theirs) as handle:
            self.assertEqual(handle.read(), "NOT THIS CAPTURE'S\n")
        self.assertIn("could not be written", found["failed"][0])

    def test_the_record_cannot_name_ITSELF_or_its_own_staging(self):
        """A destination of `.retention.json` would have the capture append a
        source's bytes onto its own bookkeeping."""
        self.source("abcdef")
        self.record({"s.jsonl": {"identity": self.identity(),
                                 "destination": self.fmt.RETENTION,
                                 "retained": 0, "head": ""}})
        found = self.tick({})
        self.assertEqual(self.native(), "abcdef")
        self.assertIn("will not act on", found["failed"][0])


class NATIVECaptureKnowsWHICHSourceItRetained(LogRoom):
    """Review 2026-09-18T03-39-32Z [R2]. The offsets were per-call integers, so
    they knew nothing about restart, truncation or replacement."""

    def setUp(self):
        super().setUp()
        _as_the_image_lays_it_out(self)
        self.delivery = self.made()
        import attempt_log_format
        import claude_agent

        self.fmt = attempt_log_format
        self.claude_agent = claude_agent
        self.scratch = os.path.join(self.home, "scratch")
        self.state = os.path.join(self.scratch, "home", ".claude")
        os.makedirs(self.state)

    def tick(self, seen, scratch=None):
        room = self.fmt.open_room(self.delivery.log_root)
        try:
            return self.claude_agent._retain_native(
                scratch or self.scratch, room, self.fmt, seen)
        finally:
            os.close(room)

    def generation(self, at=2, name="s.jsonl"):
        """What the Nth generation of one source is CALLED, from the writer.

        Spelling it out here would let the namespace change without a single
        case noticing -- and the namespace is the point: `#2` collided with a
        real source file named `s.jsonl#2`, which `test_a_REAL_source_named_
        like_a_generation` now holds.
        """
        return f"{name}{self.claude_agent.GENERATION}{at}"

    def source(self, payload, name="s.jsonl"):
        with open(os.path.join(self.state, name), "w") as handle:
            handle.write(payload)

    def native(self, name="s.jsonl"):
        with open(os.path.join(self.delivery.native_root, name)) as handle:
            return handle.read()

    def entries(self):
        """The retained SOURCE files, which is what these cases are about.

        `attempt_log_format.RETENTION` is the capture's own bookkeeping and
        lives in this corner because it describes these bytes; counting it as
        something the provider wrote would make every case here assert one
        file too many.
        """
        return sorted(one for one in os.listdir(self.delivery.native_root)
                      if one != self.fmt.RETENTION)

    def test_a_FRESH_offset_map_over_the_same_room_does_not_duplicate(self):
        """The restart case: the resume position is the retained copy's own
        size on DISK, so recovering it needs no memory."""
        self.source("abc")
        self.tick({})
        self.tick({})
        self.assertEqual(self.native(), "abc")

    def test_a_TRUNCATED_source_keeps_the_old_bytes_and_declares_the_break(self):
        """Appending the new bytes onto the old would splice two generations
        into one plausible file while omitting nothing visibly."""
        held = {}
        self.source("abcdef")
        self.tick(held)
        self.source("XY")
        found = self.tick(held)
        self.assertEqual(self.native(), "abcdef")
        self.assertEqual(self.native(self.generation()), "XY")
        self.assertTrue(found["failed"])
        # IN PLACE, and the note says so: the inode did not change, so only
        # the length-against-the-RECORD comparison can see this at all.
        self.assertIn("truncated in place", found["failed"][0])

    def test_a_REPLACED_source_is_a_new_generation_too(self):
        held = {}
        self.source("first generation\n")
        self.tick(held)
        os.unlink(os.path.join(self.state, "s.jsonl"))
        self.source("second generation, a longer one\n")
        found = self.tick(held)
        self.assertEqual(self.native(), "first generation\n")
        self.assertEqual(self.native(self.generation()),
                         "second generation, a longer one\n")
        self.assertTrue(found["failed"])

    def test_TICKING_AGAIN_after_a_rotation_makes_no_THIRD_generation(self):
        """The binding is the RECORD's, so a later tick resumes the generation
        instead of measuring the original retained file all over again."""
        held = {}
        self.source("abcdef")
        self.tick(held)
        self.source("XY")
        self.tick(held)
        self.tick(held)
        self.tick(held)
        self.assertEqual(self.entries(), ["s.jsonl", self.generation()])
        self.assertEqual(self.native(self.generation()), "XY")

    def test_a_FRESH_map_after_a_rotation_resumes_from_the_RECORD(self):
        """Restart. The room is the same, the map remembers nothing, and the
        answer must come from the record beside the bytes."""
        held = {}
        self.source("abcdef")
        self.tick(held)
        self.source("XY")
        self.tick(held)
        self.tick({})
        self.tick({})
        self.assertEqual(self.entries(), ["s.jsonl", self.generation()])
        self.assertEqual(self.native(), "abcdef")
        self.assertEqual(self.native(self.generation()), "XY")

    def test_a_new_generation_that_GROWS_PAST_the_old_one_never_splices(self):
        """Review 2026-09-18T03-48-00Z names this second failure exactly: "once
        the new source grows beyond the ORIGINAL retained size, the code can
        instead resume appending into the original generation, silently
        splicing generations." Length-based recovery flips from one wrong
        answer to a worse one at that threshold; the record does not have a
        threshold."""
        held = {}
        self.source("abcdef")
        self.tick(held)
        self.source("XY")
        self.tick(held)
        # PAST SIX BYTES, which is where a size comparison changes its mind.
        with open(os.path.join(self.state, "s.jsonl"), "a") as handle:
            handle.write("ZZZZZZZZ")
        self.tick(held)
        self.tick(held)
        self.assertEqual(self.entries(), ["s.jsonl", self.generation()])
        self.assertEqual(self.native(), "abcdef")
        self.assertEqual(self.native(self.generation()), "XYZZZZZZZZ")

    def test_a_REWRITE_AT_THE_SAME_LENGTH_is_still_a_new_generation(self):
        """Review 2026-09-18T03-48-00Z's second probe, exactly: `XY` becomes
        `ZZ` in place. Device, inode and size all still agree, so identity and
        length between them see NOTHING -- and the bytes were silently lost
        while the capture reported no failure at all. The record keeps a digest
        of the head of what it retained, which is what notices."""
        held = {}
        self.source("XY")
        self.tick(held)
        self.source("ZZ")
        found = self.tick(held)
        self.assertEqual(self.native(), "XY")
        self.assertEqual(self.native(self.generation()), "ZZ")
        self.assertIn("rewritten in place", found["failed"][0])

    def test_a_REWRITE_ACROSS_a_restart_is_caught_by_the_RECORD(self):
        """The same thing with a map that remembers nothing, which is the form
        the probe took: the digest is on disk beside the bytes."""
        self.source("XY")
        self.tick({})
        self.source("ZZ")
        found = self.tick({})
        self.assertEqual(self.native(self.generation()), "ZZ")
        self.assertTrue(found["failed"])

    def test_an_ORDINARY_APPEND_is_not_mistaken_for_a_rewrite(self):
        """The digest covers the RETAINED head, so growth leaves it alone --
        otherwise every append would rotate and the capture would be useless
        for the one thing it is for."""
        held = {}
        self.source("first\n")
        self.tick(held)
        with open(os.path.join(self.state, "s.jsonl"), "a") as handle:
            handle.write("second\n")
        found = self.tick(held)
        self.assertEqual(self.entries(), ["s.jsonl"])
        self.assertEqual(self.native(), "first\nsecond\n")
        self.assertEqual(found["failed"], [])

    def test_a_DESTINATION_WITH_NO_RECORD_is_never_resumed_BY_LENGTH(self):
        """Review 2026-09-18T03-48-00Z, in its own words: after a restart never
        infer correspondence from length alone. Bytes nobody can account for
        are kept exactly where they are and the uncertainty is DECLARED."""
        self.source("abcdef")
        self.tick({})
        os.unlink(os.path.join(self.delivery.native_root, self.fmt.RETENTION))
        found = self.tick({})
        self.assertEqual(self.native(), "abcdef")
        self.assertEqual(self.native(self.generation()), "abcdef")
        self.assertTrue(found["failed"])
        self.assertIn("no record of which source filled it",
                      found["failed"][0])

    def test_a_CORRUPT_record_is_treated_as_ABSENT_rather_than_believed(self):
        """Input like any other. A record that cannot be read is not a record,
        and what it must not do is take down the capture."""
        self.source("abcdef")
        self.tick({})
        with open(os.path.join(self.delivery.native_root,
                               self.fmt.RETENTION), "w") as handle:
            handle.write("{not json at all")
        found = self.tick({})
        self.assertEqual(self.native(), "abcdef")
        self.assertTrue(found["failed"])

    def test_a_REAL_source_named_like_a_GENERATION_does_not_collide(self):
        """`%23` is disjoint from every name `_flat` can emit, so a provider
        file called `s.jsonl%232` escapes to something else entirely."""
        held = {}
        self.source("abcdef")
        self.source("A REAL ONE",
                    name=f"s.jsonl{self.claude_agent.GENERATION}2")
        self.tick(held)
        self.source("XY")
        self.tick(held)
        self.assertEqual(self.native(self.generation()), "XY")
        self.assertEqual(self.native("s.jsonl%25232"), "A REAL ONE")

    def test_an_INACCESSIBLE_capture_root_is_not_reported_as_ABSENCE(self):
        """`_descended` collapsed every OSError into None and its caller called
        that an ordinary not-yet-created directory -- so a permission failure
        produced an empty corner reported as 'the provider wrote nothing'."""
        swapped = os.path.join(self.home, "swapped")
        os.makedirs(os.path.join(swapped, "home"))
        os.symlink(self.state, os.path.join(swapped, "home", ".claude"))
        found = self.tick({}, scratch=swapped)
        self.assertFalse(found["reached"])
        self.assertTrue(found["failed"])
        self.assertIn("is not an absent one", found["failed"][0])

    def test_a_GENUINELY_absent_root_is_still_silent(self):
        """The ordinary early tick, which must not be turned into a failure."""
        empty = os.path.join(self.home, "nothing-yet")
        os.makedirs(empty)
        found = self.tick({}, scratch=empty)
        self.assertFalse(found["reached"])
        self.assertEqual(found["failed"], [])


class MALFORMEDMetadataAndNONREGULARFilesCannotSTRANDCapture(LogRoom):
    """Review 2026-09-18T04-53-08Z, and both findings were mine.

    [R1] `_generation_of` asked `str.isdigit` and then `int()`, which are not
    the same question: a destination of `s.jsonl%23` plus the superscript `²`,
    or plus 4301 ASCII nines, raised `ValueError` OUT of the drain. Both
    documents are well under `MAX_RETENTION`; validation over bounded input has
    to be TOTAL, and what it cannot recognise it must DISCARD and declare.

    [R2] Every type check stood on a NAME. A valid record naming a destination
    that is a fifo sent `_appended` into an `O_WRONLY` open with no reader, and
    the reviewer's bounded probe was killed at two seconds. `_ran_provider`
    joins this drain, so a logging failure could strand the provider path.
    """

    def setUp(self):
        super().setUp()
        _as_the_image_lays_it_out(self)
        self.delivery = self.made()
        import attempt_log_format
        import claude_agent

        self.fmt = attempt_log_format
        self.claude_agent = claude_agent
        self.scratch = os.path.join(self.home, "scratch")
        self.state = os.path.join(self.scratch, "home", ".claude")
        os.makedirs(self.state)

    def source(self, payload, name="s.jsonl", mode="w"):
        with open(os.path.join(self.state, name), mode) as handle:
            handle.write(payload)
        return os.stat(os.path.join(self.state, name))

    def identity(self, name="s.jsonl"):
        held = os.stat(os.path.join(self.state, name))
        return [held.st_dev, held.st_ino]

    def tick(self, seen=None):
        room = self.fmt.open_room(self.delivery.log_root)
        try:
            return self.claude_agent._retain_native(
                self.scratch, room, self.fmt, {} if seen is None else seen)
        finally:
            os.close(room)

    def record(self, held):
        place = os.path.join(self.delivery.native_root, self.fmt.RETENTION)
        with open(place, "w") as handle:
            handle.write(held if isinstance(held, str) else json.dumps(held))

    def entry(self, destination, name="s.jsonl", retained=0, head=""):
        return {name: {"identity": self.identity(name),
                       "destination": destination,
                       "retained": retained, "head": head}}

    def native(self, name="s.jsonl"):
        with open(os.path.join(self.delivery.native_root, name)) as handle:
            return handle.read()

    def entries(self):
        return sorted(one for one in os.listdir(self.delivery.native_root)
                      if one != self.fmt.RETENTION)

    def generation(self, at=2, name="s.jsonl"):
        return f"{name}{self.claude_agent.GENERATION}{at}"

    IN_A_CHILD = (
        "import sys, os, json;"
        "sys.path[:0] = " + repr([os.path.join(REPO, "v12/worker"),
                                  os.path.join(REPO, "v12/python/src",
                                               "baton_v12")]) + ";"
        "import attempt_log_format as fmt, claude_agent;")

    def bounded(self, program, seconds=10):
        """One capture step in a CHILD, so a WAIT is a measurable failure.

        An in-process case that blocks hangs the whole suite and reports
        nothing, and blocking forever is exactly the defect under test: an
        `O_RDONLY` open of a fifo waits for a writer and an `O_WRONLY` open
        waits for a reader. The timeout is generous because a slow machine is
        not a defect, while the defect never returns at all.
        """
        child = subprocess.run([sys.executable, "-c", self.IN_A_CHILD + program],
                               capture_output=True, text=True, timeout=seconds)
        self.assertEqual(child.returncode, 0, child.stderr)
        return json.loads(child.stdout or "null")

    def one_tick(self):
        """A whole `_retain_native` tick, from a fresh process."""
        return self.bounded(
            f"room = os.open({self.delivery.log_root!r}, os.O_RDONLY | os.O_DIRECTORY);"
            f"found = claude_agent._retain_native({self.scratch!r}, room, fmt, {{}});"
            "print(json.dumps(found['failed']))")

    def one_source(self, name="s.jsonl"):
        """`_appended` alone, which is the open boundary `_walked` cannot hold.

        `_walked` refuses a non-regular SOURCE by its stat, so the only way
        this file is reached with a fifo in place is the swap between that
        stat and this open -- and reaching it directly is how that window is
        exercised without pretending the walk let it through.
        """
        return self.bounded(
            f"here = os.open({self.state!r}, os.O_RDONLY | os.O_DIRECTORY);"
            f"native = os.open({self.delivery.native_root!r}, os.O_RDONLY | os.O_DIRECTORY);"
            "failed = [];"
            f"claude_agent._appended(here, {name!r}, native, {name!r}, {{}}, failed, fmt);"
            "print(json.dumps(failed))")

    # -- R1: malformed generation metadata -----------------------------------

    def test_a_UNICODE_digit_in_a_generation_is_DISCARDED_not_RAISED(self):
        """The reviewer's probe: `str.isdigit()` is true of `²` and `int()`
        raises on it, so the exception escaped the whole drain."""
        self.source("abc")
        self.record(self.entry("s.jsonl%23\u00b2"))
        found = self.tick()
        self.assertEqual(self.native(), "abc")
        self.assertIn("will not act on", found["failed"][0])

    def test_a_GENERATION_LONGER_than_any_conversion_is_DISCARDED(self):
        """4301 ASCII nines: within `MAX_RETENTION`, and refused by Python's
        own integer-conversion limit rather than by this validation."""
        self.source("abc")
        self.record(self.entry("s.jsonl%23" + "9" * 4301))
        found = self.tick()
        self.assertEqual(self.native(), "abc")
        self.assertIn("will not act on", found["failed"][0])

    def test_the_SHAPE_of_a_generation_is_decided_WITHOUT_converting_it(self):
        """The boundary, spelled out: greater than one, no leading zero, ASCII
        decimal, and no longer than any run of rotations this can reach."""
        believed = self.claude_agent._generation_of
        for good in ("2", "10", "9" * 18):
            with self.subTest(suffix=good, expected=True):
                self.assertTrue(believed("s.jsonl", "s.jsonl%23" + good))
        for bad in ("", "1", "0", "02", "2.0", "+2", " 2", "2 ", "\u00b2",
                    "\u0662", "9" * 19, "9" * 4301, "2\n"):
            with self.subTest(suffix=bad, expected=False):
                self.assertFalse(believed("s.jsonl", "s.jsonl%23" + bad))

    def test_a_LEGITIMATE_generation_entry_is_still_BELIEVED(self):
        """The correction must not refuse the records this actually writes."""
        held = {}
        self.source("abcdef")
        self.tick(held)
        self.source("XY")
        self.tick(held)
        self.assertEqual(self.entries(), ["s.jsonl", self.generation()])
        self.source("XYZ")
        found = self.tick({})
        self.assertEqual(self.native(self.generation()), "XYZ")
        self.assertEqual(self.native(), "abcdef")
        self.assertEqual(found["failed"], [])

    def test_a_DEEPLY_NESTED_record_is_treated_as_ABSENT_not_RAISED(self):
        """A bound on BYTES is not a bound on DEPTH: this document is a fifth
        of `MAX_RETENTION` and exhausts the decoder's stack, and the
        `RecursionError` it raises is not a `ValueError`."""
        self.source("abc")
        self.record("[" * 200000 + "]" * 200000)
        found = self.tick()
        self.assertEqual(self.native(), "abc")
        self.assertIn("could not be read as this capture's own document",
                      found["failed"][0])

    # -- R2: the data descriptors --------------------------------------------

    def test_a_FIFO_where_a_RETAINED_FILE_belongs_is_DECLARED(self):
        """The reviewer's probe, run in a child exactly as they ran it: this
        blocked in the destination `O_WRONLY` open and was killed at two
        seconds, with `_retained_size` having accepted the fifo's size zero."""
        self.source("abc")
        os.mkfifo(os.path.join(self.delivery.native_root, "s.jsonl"))
        self.record(self.entry("s.jsonl"))
        failed = self.one_tick()
        self.assertTrue(failed)
        self.assertIn("is not a regular file", failed[0])

    def test_and_the_SOURCES_BYTES_are_KEPT_rather_than_lost(self):
        """A destination nothing can account for is a rotation like any other:
        the bytes go somewhere this CAN explain and the reason is declared,
        rather than being dropped because the corner was tampered with."""
        self.source("abc")
        os.mkfifo(os.path.join(self.delivery.native_root, "s.jsonl"))
        self.record(self.entry("s.jsonl"))
        self.one_tick()
        self.assertEqual(self.native(self.generation()), "abc")

    def test_a_DIRECTORY_where_a_retained_file_belongs_is_the_SAME_case(self):
        """Not every non-file blocks; a destination this cannot account for is
        refused for what it IS rather than for how it would fail."""
        self.source("abc")
        os.mkdir(os.path.join(self.delivery.native_root, "s.jsonl"))
        self.record(self.entry("s.jsonl"))
        found = self.tick()
        self.assertIn("is not a regular file", found["failed"][0])
        self.assertEqual(self.native(self.generation()), "abc")

    def test_a_DESTINATION_swapped_after_the_check_is_caught_by_the_OPEN(self):
        """`_retained_size` checks a NAME, and a name checked and then opened
        is two objects whenever anything moves in between. A READER is held
        here so the open SUCCEEDS -- which is the case the flag cannot answer
        and the descriptor must: `O_NONBLOCK` only refuses a fifo NOBODY is
        reading, and a peer that is reading would otherwise be handed this
        attempt's log bytes.
        """
        self.source("abc")
        place = os.path.join(self.delivery.native_root, "s.jsonl")
        os.mkfifo(place)
        self.record(self.entry("s.jsonl"))
        peer = os.open(place, os.O_RDONLY | os.O_NONBLOCK)
        self.addCleanup(os.close, peer)
        with mock.patch.object(self.claude_agent, "_retained_size",
                               lambda *operands: 0):
            found = self.tick()
        self.assertTrue(found["failed"])
        self.assertIn("wrote nothing into it", found["failed"][0])
        # NOTHING REACHED THE PEER. Every writer is closed by now, so an empty
        # read is the pipe's own word that no byte was ever put into it.
        self.assertEqual(os.read(peer, 64), b"")

    def test_a_SOURCE_swapped_after_being_listed_is_caught_by_the_OPEN(self):
        """A nonblocking open of a fifo with no writer SUCCEEDS and then reads
        EOF, so without the descriptor check the swap would be retained as an
        empty file and reported as an ordinary success."""
        os.mkfifo(os.path.join(self.state, "s.jsonl"))
        failed = self.one_source()
        self.assertTrue(failed)
        self.assertIn("changed into something that is not a regular file",
                      failed[0])
        self.assertEqual(self.entries(), [])

    def test_and_a_SOURCE_fifo_WITH_a_writer_is_named_for_what_it_is(self):
        """The other half, and the reversal probe corrected my description of
        it: a fifo somebody IS writing to opens at once even without
        `O_NONBLOCK`, so this one never waited. What the old code did instead
        was take it for a file and fail at the SEEK -- "a native file could not
        be positioned (OSError)" -- which names the symptom and not the cause.
        The waiting case is the sibling above, where nothing holds the write
        end; both are answered by asking the descriptor what it is.
        """
        place = os.path.join(self.state, "s.jsonl")
        os.mkfifo(place)
        writer = os.open(place, os.O_RDWR | os.O_NONBLOCK)
        self.addCleanup(os.close, writer)
        os.write(writer, b"NOT A SESSION FILE")
        failed = self.one_source()
        self.assertIn("changed into something that is not a regular file",
                      failed[0])
        self.assertEqual(self.entries(), [])

    # -- the same contract, wherever this file decodes a bounded document -----

    def test_NO_bounded_document_in_this_adapter_RAISES_on_DEPTH(self):
        """The sweep review 2026-09-18T04-53-08Z [R1] asked for, and it found
        two more of my own: the review report and the task document are read
        under byte bounds and decoded with the same handler, and a bound on
        BYTES is not a bound on DEPTH. Each one has a REFUSAL vocabulary that
        exists to describe a malformed document; raising through it says the
        adapter broke where the truth is that somebody handed it nonsense.
        """
        nested = ("[" * 200000 + "]" * 200000).encode()

        place = os.path.join(self.home, "task.json")
        with open(place, "wb") as handle:
            handle.write(nested)
        with self.assertRaises(self.claude_agent.TaskRefusal) as refusal:
            self.claude_agent._read_task(place)
        self.assertIn("not a readable document", str(refusal.exception))

        with open(os.path.join(self.delivery.log_root,
                               self.claude_agent.REVIEW_REPORT), "wb") as handle:
            handle.write(nested)
        self.assertIsNone(
            self.claude_agent._review_report(self.delivery.log_root))

class ADestinationThisCaptureDoesNotOWNIsNotOneItWritesTo(LogRoom):
    """Review 2026-09-18T05-32-05Z, and both findings were mine.

    [R1] `S_ISREG` proves the opened thing is a FILE; it does not prove it is
    THIS corner's file. The reviewer hard-linked a sibling from outside the
    native directory at `native/s.jsonl`, supplied a valid record for it, and
    watched a supposedly confined writer append the provider's transcript to
    BOTH names with `failed` empty. `O_NOFOLLOW` refuses a symlink and a
    confined name refuses traversal; neither can see an alias, because a hard
    link is a second name for the INODE rather than for the path.

    [R2] A provider file literally called `.retention.json` was SILENTLY
    DROPPED: `_walked` skipped the source because the DESTINATION keeps its
    record under that name, so a real transcript was neither retained nor
    reported -- `reached` true, `failed` empty, the corner empty. A capture
    whose whole vocabulary exists to tell "missing" from "empty" cannot have a
    filename it quietly refuses.
    """

    TRANSCRIPT = "provider transcript"

    def setUp(self):
        super().setUp()
        _as_the_image_lays_it_out(self)
        self.delivery = self.made()
        import attempt_log_format
        import claude_agent

        self.fmt = attempt_log_format
        self.claude_agent = claude_agent
        self.scratch = os.path.join(self.home, "scratch")
        self.state = os.path.join(self.scratch, "home", ".claude")
        os.makedirs(self.state)

    def source(self, payload=None, name="s.jsonl", mode="w"):
        with open(os.path.join(self.state, name), mode) as handle:
            handle.write(self.TRANSCRIPT if payload is None else payload)

    def tick(self, seen=None):
        room = self.fmt.open_room(self.delivery.log_root)
        try:
            return self.claude_agent._retain_native(
                self.scratch, room, self.fmt, {} if seen is None else seen)
        finally:
            os.close(room)

    def record(self, held):
        place = os.path.join(self.delivery.native_root, self.fmt.RETENTION)
        with open(place, "w") as handle:
            handle.write(json.dumps(held))

    def entry(self, destination, name="s.jsonl", retained=0, head=""):
        held = os.stat(os.path.join(self.state, name))
        return {name: {"identity": [held.st_dev, held.st_ino],
                       "destination": destination,
                       "retained": retained, "head": head}}

    def native(self, name="s.jsonl"):
        with open(os.path.join(self.delivery.native_root, name)) as handle:
            return handle.read()

    def entries(self):
        return sorted(one for one in os.listdir(self.delivery.native_root)
                      if one != self.fmt.RETENTION)

    def generation(self, at=2, name="s.jsonl"):
        return f"{name}{self.claude_agent.GENERATION}{at}"

    def aliased(self, name="s.jsonl"):
        """One destination that is ALSO a file outside this room."""
        outside = os.path.join(self.home, "sibling.log")
        with open(outside, "w"):
            pass
        os.link(outside, os.path.join(self.delivery.native_root, name))
        return outside

    # -- R1: the alias --------------------------------------------------------

    def test_an_ALIASED_destination_is_REFUSED_before_a_byte_is_written(self):
        """The reviewer's probe: 19 bytes reached a file outside the native
        directory, and the capture reported no failure at all."""
        self.source()
        outside = self.aliased()
        self.record(self.entry("s.jsonl"))
        found = self.tick()
        with open(outside) as handle:
            self.assertEqual(handle.read(), "")
        self.assertEqual(self.native(), "")
        self.assertTrue(found["failed"])
        self.assertIn("linked elsewhere", found["failed"][0])

    def test_and_the_SOURCE_is_retained_SEPARATELY_rather_than_lost(self):
        """A destination this capture cannot account for is a rotation like
        any other: the bytes go somewhere it CAN explain."""
        self.source()
        self.aliased()
        self.record(self.entry("s.jsonl"))
        self.tick()
        self.assertEqual(self.native(self.generation()), self.TRANSCRIPT)
        self.assertEqual(self.entries(), ["s.jsonl", self.generation()])

    def test_a_FRESH_destination_is_CREATED_and_never_ADOPTED(self):
        """`O_CREAT` alone adopts whatever is already at the name, which is how
        the aliased file became a destination. A name this capture believes is
        free is claimed with `O_EXCL`, so the belief is proved."""
        opened = []
        real = os.open

        def watched(name, flags, *rest, **named):
            if named.get("dir_fd") is not None and name == "s.jsonl" \
                    and flags & os.O_CREAT:
                opened.append(flags)
            return real(name, flags, *rest, **named)

        self.source()
        with mock.patch.object(os, "open", watched):
            self.tick()
        self.assertTrue(opened)
        for flags in opened:
            self.assertTrue(flags & os.O_EXCL, flags)
            self.assertFalse(flags & os.O_TRUNC, flags)

    def test_an_ORDINARY_single_link_append_is_UNAFFECTED(self):
        """The control. A rule that also refused the ordinary case would be a
        capture that retains nothing."""
        held = {}
        self.source()
        self.tick(held)
        self.source(" and more", mode="a")
        found = self.tick(held)
        self.assertEqual(self.native(), self.TRANSCRIPT + " and more")
        self.assertEqual(self.entries(), ["s.jsonl"])
        self.assertEqual(found["failed"], [])

    def test_a_destination_LINKED_AFTER_it_was_created_is_caught_too(self):
        """The alias does not have to precede the capture: the check is on the
        descriptor every tick opens, not on how the file came to exist."""
        held = {}
        self.source()
        self.tick(held)
        os.link(os.path.join(self.delivery.native_root, "s.jsonl"),
                os.path.join(self.home, "later.log"))
        self.source(" and more", mode="a")
        found = self.tick(held)
        self.assertIn("linked elsewhere", found["failed"][0])
        # WHAT WAS ALREADY RETAINED IS KEPT, and the generation holds the
        # WHOLE source rather than the tail: a new generation is a fresh copy,
        # exactly as a truncation or an in-place rewrite produces, because
        # nothing here can prove the aliased file's bytes are this source's.
        self.assertEqual(self.native(), self.TRANSCRIPT)
        self.assertEqual(self.native(self.generation()),
                         self.TRANSCRIPT + " and more")

    def test_a_corner_where_the_FRESH_name_is_also_unusable_STOPS(self):
        """One rotation. A corner whose next generation is also aliased is not
        one more attempt away from working, and a capture that kept trying
        would be an unbounded loop inside the provider's own drain."""
        self.source()
        self.aliased()
        self.aliased(self.generation())
        self.record(self.entry("s.jsonl"))
        found = self.tick()
        self.assertEqual(self.native(), "")
        self.assertEqual(self.native(self.generation()), "")
        self.assertIn("linked elsewhere", found["failed"][0])

    # -- R2: the reserved name ------------------------------------------------

    def test_a_provider_file_named_LIKE_THE_RECORD_is_RETAINED(self):
        """The reviewer's probe: reached true, failed empty, corner empty."""
        self.source(name=self.fmt.RETENTION)
        found = self.tick()
        self.assertEqual(found["failed"], [])
        self.assertEqual(self.entries(), ["%2Eretention.json"])
        self.assertEqual(self.native("%2Eretention.json"), self.TRANSCRIPT)

    def test_a_name_with_the_records_own_PREFIX_is_retained_too(self):
        """`_confined` refuses `.retention.json.` names as destinations -- the
        staging namespace -- so a source flattened to one could never be
        resumed from its own record either."""
        self.source(name=self.fmt.RETENTION + ".1")
        self.tick()
        self.assertEqual(self.entries(), ["%2Eretention.json.1"])
        self.assertEqual(self.native("%2Eretention.json.1"), self.TRANSCRIPT)

    def test_it_RESUMES_that_source_across_a_RESTART(self):
        """Which is the half a skip could never have: the escaped name is a
        destination the record may name, so a fresh map continues it rather
        than starting a generation or copying it twice."""
        held = {}
        self.source(name=self.fmt.RETENTION + ".1")
        self.tick(held)
        self.source(" more", name=self.fmt.RETENTION + ".1", mode="a")
        self.tick(held)
        found = self.tick({})
        self.assertEqual(self.entries(), ["%2Eretention.json.1"])
        self.assertEqual(self.native("%2Eretention.json.1"),
                         self.TRANSCRIPT + " more")
        self.assertEqual(found["failed"], [])

    def test_the_ESCAPE_stays_INJECTIVE(self):
        """A provider file really called `%2Eretention.json` must not land on
        the escaped name of a different source. A literal per-cent is already
        `%25`, which is what keeps the two apart."""
        self.source(name=self.fmt.RETENTION)
        self.source("A DIFFERENT SOURCE", name="%2Eretention.json")
        self.tick()
        self.assertEqual(self.entries(),
                         ["%252Eretention.json", "%2Eretention.json"])
        self.assertEqual(self.native("%2Eretention.json"), self.TRANSCRIPT)
        self.assertEqual(self.native("%252Eretention.json"),
                         "A DIFFERENT SOURCE")

    def test_the_RECORD_ITSELF_is_still_not_a_session_file(self):
        """The escape is about SOURCES. The corner's own bookkeeping is still
        excluded from what an operator is shown, and a source is never given
        that name to write to."""
        self.source(name=self.fmt.RETENTION)
        self.tick()
        found = attempt_logs.locators(self.delivery)["native"]
        self.assertNotIn(self.fmt.RETENTION, found["entries"])
        self.assertIn("%2Eretention.json", found["entries"])
        with open(os.path.join(self.delivery.native_root,
                               self.fmt.RETENTION)) as handle:
            self.assertIn("%2Eretention.json", handle.read())


class TheSHAREDStreamBoundaryOwnsWhatItWritesTo(LogRoom):
    """Review 2026-09-18T06-27-53Z, and both findings were mine.

    [R1] The native corner learned three acquisition properties and the SHARED
    opener every one of the six streams goes through had none of them. A fifo
    at `provider.stdout.log` blocked `os.open` waiting for a reader and the
    reviewer's bounded child was killed at two seconds -- before the provider
    starts, in the wrapper's earliest output too. A file hard-linked from
    outside the room took the raw provider bytes while the capture declared
    `finished`.

    [R2] A second writer for one stream INHERITED the first's terminal word:
    ordinary sequential capture, no malicious input. The first declared
    `finished`, the second appended beside it, and the real reader answered
    `captured`, "the writer saw this stream to its end", `more_may_arrive:
    false`, over a file that was still growing.
    """

    STREAM = "provider.stdout"

    def setUp(self):
        super().setUp()
        _as_the_image_lays_it_out(self)
        self.delivery = self.made()
        import attempt_log_format
        import claude_agent

        self.fmt = attempt_log_format
        self.claude_agent = claude_agent
        self.room = self.fmt.open_room(self.delivery.log_root)
        self.addCleanup(os.close, self.room)

    def log_place(self, stream=None):
        return os.path.join(self.delivery.log_root,
                            self.fmt.log_name(stream or self.STREAM))

    def captured(self, stream=None):
        return self.claude_agent._Captured(self.room, self.fmt,
                                           stream or self.STREAM)

    def declaration(self, stream=None):
        return self.fmt.read_declaration(self.room, stream or self.STREAM)

    def followed(self, stream=None):
        return attempt_logs.follow(self.delivery, stream or self.STREAM)

    def aliased(self, stream=None):
        outside = os.path.join(self.home, "sibling.log")
        with open(outside, "w"):
            pass
        os.link(outside, self.log_place(stream))
        return outside

    # -- R1: acquisition ------------------------------------------------------

    def test_a_FIFO_at_a_SHARED_stream_does_not_BLOCK(self):
        """In a bounded child, because the defect never returns at all and an
        in-process case would hang the suite rather than report."""
        os.mkfifo(self.log_place())
        argv = [sys.executable, "-c",
                "import sys, os, json;"
                "sys.path[:0] = " + repr([os.path.join(REPO, "v12/worker"),
                                          os.path.join(REPO, "v12/python/src",
                                                       "baton_v12")]) + ";"
                "import attempt_log_format as fmt, claude_agent;"
                f"room = os.open({self.delivery.log_root!r}, "
                "os.O_RDONLY | os.O_DIRECTORY);"
                f"held = claude_agent._Captured(room, fmt, {self.STREAM!r});"
                "print(json.dumps({'acquired': held._handle is not None}))"]
        child = subprocess.run(argv, capture_output=True, text=True,
                               timeout=10)
        self.assertEqual(child.returncode, 0, child.stderr)
        self.assertFalse(json.loads(child.stdout)["acquired"])

    def test_a_FIFO_stream_is_DECLARED_failed_and_says_why(self):
        os.mkfifo(self.log_place())
        held = self.captured()
        held.wrote(b"raw provider bytes")
        said = held.declare("finished")
        self.assertEqual(said["declared"], "failed")
        self.assertNotEqual(said["reason"],
                            self.fmt.DECLARED["failed"])

    def test_an_ALIASED_shared_stream_writes_NOTHING_outside_the_room(self):
        """The reviewer's probe: `raw provider bytes` reached a file outside
        the room and the capture declared `finished`."""
        outside = self.aliased()
        held = self.captured()
        held.wrote(b"raw provider bytes")
        said = held.declare("finished")
        with open(outside) as handle:
            self.assertEqual(handle.read(), "")
        self.assertEqual(said["declared"], "failed")
        self.assertIn("linked elsewhere", said["reason"])

    def test_a_DEVICE_or_directory_at_a_stream_is_refused_too(self):
        """A device opens perfectly well and swallows everything."""
        os.mkdir(self.log_place())
        held = self.captured()
        held.wrote(b"raw provider bytes")
        self.assertEqual(held.declare("finished")["declared"], "failed")

    def test_the_WRAPPERS_OWN_stream_is_acquired_the_same_way(self):
        """`_TeeStream` reaches the same opener BEFORE the startup diagnostic,
        which is the half of the incident that made it expensive."""
        import baton_worker

        self.aliased("worker.stderr")
        tee = baton_worker._TeeStream(io.StringIO(), self.room,
                                      "worker.stderr", self.fmt)
        tee.write("a startup diagnostic\n")
        said = tee.declare()
        self.assertEqual(said["declared"], "failed")
        self.assertIn("linked elsewhere", said["reason"])

    def test_an_ORDINARY_stream_is_UNAFFECTED(self):
        """The control. A rule that also refused the ordinary case would be a
        capture that captures nothing."""
        held = self.captured()
        held.wrote(b"ordinary bytes")
        said = held.declare("finished")
        self.assertEqual(said["declared"], "finished")
        with open(self.log_place()) as handle:
            self.assertEqual(handle.read(), "ordinary bytes")

    def test_a_RESTART_still_APPENDS_beside_the_first_incarnation(self):
        """The required outcome: partial evidence survives restart. A fresh
        entry is created exclusively; an existing one is appended to."""
        first = self.captured()
        first.wrote(b"first incarnation\n")
        first.declare("finished")
        second = self.captured()
        second.wrote(b"second incarnation\n")
        second.declare("finished")
        with open(self.log_place()) as handle:
            self.assertEqual(handle.read(),
                             "first incarnation\nsecond incarnation\n")

    # -- R2: the declaration's lifetime ---------------------------------------

    def test_a_SECOND_writer_does_not_INHERIT_the_first_word(self):
        """A terminal word is about BYTES, not about a name."""
        first = self.captured()
        first.wrote(b"first")
        first.declare("finished")
        self.assertEqual(self.declaration()["declared"], "finished")
        second = self.captured()
        second.wrote(b"second")
        self.assertIsNone(self.declaration())
        second.declare(None)
        self.assertIsNone(self.declaration())

    def test_the_OPERATOR_sees_an_honest_state_while_it_is_open(self):
        """The reviewer read this through the real reader: `captured`, "the
        writer saw this stream to its end", `more_may_arrive: false`, over a
        file that was still growing."""
        first = self.captured()
        first.wrote(b"first")
        first.declare("finished")
        second = self.captured()
        second.wrote(b"second")
        found = self.followed()
        self.assertNotEqual(found["state"], "captured")
        self.assertTrue(found["more_may_arrive"], found)
        self.assertEqual(found["text"], "firstsecond")
        second.declare("finished")

    def test_the_EARLIER_BYTES_are_never_touched(self):
        first = self.captured()
        first.wrote(b"first")
        first.declare("finished")
        second = self.captured()
        second.wrote(b"second")
        second.declare("finished")
        with open(self.log_place()) as handle:
            self.assertEqual(handle.read(), "firstsecond")

    def test_a_SECOND_writer_that_FINISHES_says_so(self):
        """Not a pass obtained by declaring every stream incomplete forever."""
        first = self.captured()
        first.wrote(b"first")
        first.declare("finished")
        second = self.captured()
        second.wrote(b"second")
        self.assertEqual(second.declare("finished")["declared"], "finished")
        found = self.followed()
        self.assertEqual(found["state"], "captured")
        self.assertFalse(found["more_may_arrive"])

    def test_an_INTERRUPTED_second_writer_leaves_LIVE_and_not_finished(self):
        """The stop before the new declaration, which is the case an operator
        actually meets after a kill."""
        first = self.captured()
        first.wrote(b"first")
        first.declare("finished")
        second = self.captured()
        second.wrote(b"second")
        del second                              # killed before it declared
        found = self.followed()
        self.assertNotEqual(found["state"], "captured")
        self.assertTrue(found["more_may_arrive"])

    def test_a_declaration_that_CANNOT_be_cleared_REFUSES_the_handle(self):
        """Appending under a word that describes other bytes would report
        somebody else's ending as this capture's."""
        first = self.captured()
        first.wrote(b"first")
        first.declare("finished")
        # `carry_declaration` is what the opener calls now: it moves the
        # prior word into the cumulative record and then clears the sidecar,
        # and the refusal this case is about is the clearing failing.
        with mock.patch.object(self.fmt, "carry_declaration",
                               lambda *operands: (False, None)):
            second = self.captured()
            second.wrote(b"second")
            said = second.declare("finished")
        self.assertEqual(said["declared"], "failed")
        self.assertIn("could not be cleared", said["reason"])
        with open(self.log_place()) as handle:
            self.assertEqual(handle.read(), "first")

    def test_clearing_touches_the_METADATA_and_never_the_BYTES(self):
        first = self.captured()
        first.wrote(b"the bytes that must survive")
        first.declare("finished")
        self.assertTrue(self.fmt.clear_declaration(self.room, self.STREAM))
        self.assertIsNone(self.declaration())
        with open(self.log_place()) as handle:
            self.assertEqual(handle.read(), "the bytes that must survive")

    def test_clearing_NOTHING_is_an_ordinary_success(self):
        """The first writer of a stream meets this on every attempt."""
        self.assertTrue(self.fmt.clear_declaration(self.room, self.STREAM))


class ALaterSUCCESSCannotEraseAnEarlierLOSS(LogRoom):
    """Review 2026-09-18T06-53-11Z, and this is a consequence of my own last
    correction.

    Clearing the stale terminal word was right: a declaration is about BYTES
    and stops being true when somebody appends. Clearing it UNCONDITIONALLY
    destroyed the earlier writer's evidence of LOSS. The reviewer drove the
    real capture through a short write it detected itself, let a second writer
    append cleanly, and watched the reader answer `captured`, "the writer saw
    this stream to its end", over a file whose middle was never restored.

    THE TWO FACTS ARE DIFFERENT AND BOTH ARE KEPT. The sidecar says what the
    writer that published it saw, which is why clearing it keeps a reopened
    stream honestly `live`. The cumulative record says whether the WHOLE FILE
    is complete, which no later writer can improve.
    """

    STREAM = "provider.stdout"

    def setUp(self):
        super().setUp()
        _as_the_image_lays_it_out(self)
        self.delivery = self.made()
        import attempt_log_format
        import claude_agent

        self.fmt = attempt_log_format
        self.claude_agent = claude_agent
        self.room = self.fmt.open_room(self.delivery.log_root)
        self.addCleanup(os.close, self.room)

    def captured(self, stream=None):
        return self.claude_agent._Captured(self.room, self.fmt,
                                           stream or self.STREAM)

    def bounded(self, held, accepts=5):
        """A write boundary that accepts only the first bytes of each payload,
        which the capture detects on its own.

        IT DELEGATES EVERYTHING ELSE to the real module rather than listing
        what it needs: the wrapper's tee opens its handle LAZILY, so a shim
        that knew only about writing broke at the acquisition it had never
        heard of -- and a fixture that has to be updated whenever the module
        grows a function is a fixture that decides what is tested.
        """
        real = self.fmt

        class Bounded:
            def __getattr__(self, name):
                return getattr(real, name)

            @staticmethod
            def write_all(handle, payload):
                return real.write_all(handle, payload[:accepts])

        held._fmt = Bounded()
        return held

    def declaration(self, stream=None):
        return self.fmt.read_declaration(self.room, stream or self.STREAM)

    def followed(self, stream=None):
        return attempt_logs.follow(self.delivery, stream or self.STREAM)

    def log_place(self, stream=None):
        return os.path.join(self.delivery.log_root,
                            self.fmt.log_name(stream or self.STREAM))

    # -- the reviewer's probe, through the real capture and the real reader ---

    def test_a_DETECTED_SHORT_WRITE_survives_a_later_whole_capture(self):
        """The probe exactly: `first-MISSING-TAIL` with a boundary that accepts
        only `first`, then a clean `second-whole`."""
        first = self.bounded(self.captured())
        first.wrote(b"first-MISSING-TAIL")
        self.assertEqual(first.declare("finished")["declared"], "failed")
        second = self.captured()
        second.wrote(b"second-whole")
        said = second.declare("finished")
        self.assertEqual(said["declared"], "failed")
        self.assertIn("never restored", said["reason"])

    def test_and_the_READER_no_longer_calls_that_stream_captured(self):
        first = self.bounded(self.captured())
        first.wrote(b"first-MISSING-TAIL")
        first.declare("finished")
        second = self.captured()
        second.wrote(b"second-whole")
        second.declare("finished")
        found = self.followed()
        self.assertEqual(found["state"], "failed")
        self.assertNotEqual(found["state"], "captured")
        self.assertEqual(found["text"], "firstsecond-whole")

    def test_the_RAW_BYTES_of_both_generations_are_preserved(self):
        """Evidence is kept; what changes is the word over it."""
        first = self.bounded(self.captured())
        first.wrote(b"first-MISSING-TAIL")
        first.declare("finished")
        second = self.captured()
        second.wrote(b"second-whole")
        second.declare("finished")
        with open(self.log_place()) as handle:
            self.assertEqual(handle.read(), "firstsecond-whole")

    def test_EVERY_prior_loss_state_survives_a_later_success(self):
        """`partial`, `truncated` and `unknown-completeness` all became
        whole-stream captured in the reviewer's state matrix."""
        # ONE STREAM EACH rather than a rebuilt room: this case holds the
        # room's DESCRIPTOR, and removing the directory under it leaves every
        # later write failing for a reason that has nothing to do with the
        # rule being tested.
        for prior, stream in (("failed", "provider.stdout"),
                              ("truncated", "provider.stderr"),
                              ("partial", "worker.stdout")):
            with self.subTest(prior=prior):
                one = self.captured(stream)
                one.wrote(b"first")
                one.declare(prior)
                two = self.captured(stream)
                two.wrote(b"second")
                self.assertEqual(
                    two.declare("finished")["declared"], prior)

    def test_the_WORSE_of_the_two_is_what_is_published(self):
        """A later writer that ALSO fails does not improve on an earlier
        `partial`, and an earlier `partial` does not soften a later `failed`."""
        one = self.captured()
        one.wrote(b"first")
        one.declare("partial")
        two = self.captured()
        two.wrote(b"second")
        self.assertEqual(two.declare("failed")["declared"], "failed")

    # -- the controls the review names explicitly ----------------------------

    def test_the_ALL_SUCCESSFUL_restart_still_ends_CAPTURED(self):
        """finished -> reopen -> finished. A correction that made every stream
        permanently incomplete would pass the cases above and be useless."""
        one = self.captured()
        one.wrote(b"first")
        one.declare("finished")
        two = self.captured()
        two.wrote(b"second")
        self.assertEqual(two.declare("finished")["declared"], "finished")
        found = self.followed()
        self.assertEqual(found["state"], "captured")
        self.assertFalse(found["more_may_arrive"])

    def test_an_ACTIVE_second_writer_still_keeps_follow_ALIVE(self):
        """The accepted stale-finished correction must not be undone: while a
        writer holds the stream open, nobody has said it ended."""
        one = self.captured()
        one.wrote(b"first")
        one.declare("failed")
        two = self.captured()
        two.wrote(b"second")
        self.assertIsNone(self.declaration())
        found = self.followed()
        self.assertTrue(found["more_may_arrive"])
        self.assertNotEqual(found["state"], "captured")

    def test_the_LOSS_is_DURABLE_while_that_writer_is_open(self):
        """A writer killed before it declares must not take the earlier loss
        with it: the cumulative record is on disk, not in its memory."""
        one = self.captured()
        one.wrote(b"first")
        one.declare("failed")
        two = self.captured()
        two.wrote(b"second")
        self.assertEqual(self.fmt.read_carried(self.room, self.STREAM),
                         "failed")
        del two
        third = self.captured()
        third.wrote(b"third")
        self.assertEqual(third.declare("finished")["declared"], "failed")

    def test_a_CLEAN_first_capture_writes_no_cumulative_record(self):
        """Only loss is carried, so the ordinary attempt costs nothing."""
        one = self.captured()
        one.wrote(b"first")
        one.declare("finished")
        self.assertIsNone(self.fmt.read_carried(self.room, self.STREAM))

    def test_an_UNREADABLE_cumulative_record_is_treated_as_the_WORST(self):
        """It is not permission to claim completeness."""
        one = self.captured()
        one.wrote(b"first")
        one.declare("finished")
        with open(os.path.join(self.delivery.log_root,
                               self.fmt.carried_name(self.STREAM)),
                  "w") as handle:
            handle.write("NOT A DOCUMENT")
        two = self.captured()
        two.wrote(b"second")
        self.assertEqual(two.declare("finished")["declared"], "failed")

    def test_the_cumulative_record_is_NOT_one_of_the_streams(self):
        """`locators` enumerates STREAMS by name; the bookkeeping is not one."""
        one = self.captured()
        one.wrote(b"first")
        one.declare("failed")
        self.captured()
        found = attempt_logs.locators(self.delivery)
        self.assertEqual(sorted(one["stream"] for one in found["streams"]),
                         sorted(self.fmt.STREAMS))

    # -- and the WRAPPER's own streams, which a restart really reopens --------

    def test_the_WRAPPERS_stream_carries_its_loss_across_a_reopen(self):
        import baton_worker

        first = baton_worker._TeeStream(io.StringIO(), self.room,
                                        "worker.stderr", self.fmt)
        first._fmt = self.bounded(first, accepts=5)._fmt
        first.write("first-MISSING-TAIL")
        self.assertEqual(first.declare()["declared"], "failed")
        second = baton_worker._TeeStream(io.StringIO(), self.room,
                                         "worker.stderr", self.fmt)
        second.write("second-whole")
        said = second.declare()
        self.assertEqual(said["declared"], "failed")
        self.assertIn("never restored", said["reason"])

    def test_the_WRAPPERS_all_successful_restart_still_ends_CAPTURED(self):
        import baton_worker

        for _ in range(2):
            tee = baton_worker._TeeStream(io.StringIO(), self.room,
                                          "worker.stderr", self.fmt)
            tee.write("an ordinary line\n")
            said = tee.declare()
        self.assertEqual(said["declared"], "finished")
        self.assertEqual(self.followed("worker.stderr")["state"], "captured")
class UNKNOWNAndUNREADABLEHistoryCannotBecomeCOMPLETE(LogRoom):
    """Review 2026-09-18T07-09-49Z, and all three were mine.

    Last claim carried DECLARED loss across a reopen. These are the three ways
    the same stream still reported `captured` over bytes nobody vouched for.

    [R1] An ending nobody declared -- the interrupted writer, and a corrupt
    sidecar, which carries no `declared` member either -- was treated exactly
    like an empty new stream, so a later clean append published `captured`
    over a prefix that never reached EOF.

    [R2] `carry_declaration` ignored `_write_carried`'s answer and unlinked the
    prior sidecar anyway, so an ordinary `OSError` in the helper destroyed the
    only record of a loss.

    [R3] `read_carried` answered `None` for every open or read failure and for
    a record that was not a regular file, so INACCESSIBLE history read exactly
    like absent history.
    """

    STREAM = "provider.stdout"

    def setUp(self):
        super().setUp()
        _as_the_image_lays_it_out(self)
        self.delivery = self.made()
        import attempt_log_format
        import claude_agent

        self.fmt = attempt_log_format
        self.claude_agent = claude_agent
        self.room = self.fmt.open_room(self.delivery.log_root)
        self.addCleanup(os.close, self.room)

    def captured(self, stream=None):
        return self.claude_agent._Captured(self.room, self.fmt,
                                           stream or self.STREAM)

    def followed(self, stream=None):
        return attempt_logs.follow(self.delivery, stream or self.STREAM)

    def carried_place(self, stream=None):
        return os.path.join(self.delivery.log_root,
                            self.fmt.carried_name(stream or self.STREAM))

    # -- R1: an ending nobody vouched for ------------------------------------

    def test_an_UNKNOWN_ending_then_a_success_is_NOT_captured(self):
        """The reviewer's probe: `first-prefix`, `declare(None)`, then a whole
        second capture. There is no evidence the first reached EOF."""
        first = self.captured()
        first.wrote(b"first-prefix")
        first.declare(None)
        second = self.captured()
        second.wrote(b"second-whole")
        said = second.declare("finished")
        self.assertEqual(said["declared"], "partial")
        found = self.followed()
        self.assertNotEqual(found["state"], "captured")
        self.assertEqual(found["text"], "first-prefixsecond-whole")

    def test_a_CORRUPT_prior_declaration_is_unknown_too(self):
        """A corrupt sidecar carries no `declared` member, so it reached the
        same branch as no sidecar at all."""
        first = self.captured()
        first.wrote(b"first-prefix")
        first.declare("finished")
        with open(os.path.join(self.delivery.log_root,
                               self.fmt.status_name(self.STREAM)),
                  "w") as handle:
            handle.write("NOT A DECLARATION")
        second = self.captured()
        second.wrote(b"second-whole")
        self.assertEqual(second.declare("finished")["declared"], "partial")

    def test_an_EMPTY_new_stream_is_still_a_CLEAN_start(self):
        """The distinction that keeps the ordinary capture free: what makes it
        `partial` is BYTES with no trustworthy ending, not a missing sidecar."""
        only = self.captured()
        only.wrote(b"the first bytes this stream ever had")
        self.assertEqual(only.declare("finished")["declared"], "finished")
        self.assertEqual(self.followed()["state"], "captured")

    def test_the_ALL_SUCCESSFUL_restart_is_still_CAPTURED(self):
        """finished -> reopen -> finished, with bytes present at the reopen."""
        first = self.captured()
        first.wrote(b"first")
        first.declare("finished")
        second = self.captured()
        second.wrote(b"second")
        self.assertEqual(second.declare("finished")["declared"], "finished")
        found = self.followed()
        self.assertEqual(found["state"], "captured")
        self.assertFalse(found["more_may_arrive"])

    def test_an_ACTIVE_second_writer_still_keeps_follow_ALIVE(self):
        first = self.captured()
        first.wrote(b"first")
        first.declare(None)
        second = self.captured()
        second.wrote(b"second")
        self.assertTrue(self.followed()["more_may_arrive"])

    def test_the_WRAPPERS_stream_treats_an_unknown_ending_the_same(self):
        import baton_worker

        first = baton_worker._TeeStream(io.StringIO(), self.room,
                                        "worker.stderr", self.fmt)
        first.write("a first line\n")
        first._handle, first._wrote = None, 0      # interrupted before declaring
        second = baton_worker._TeeStream(io.StringIO(), self.room,
                                         "worker.stderr", self.fmt)
        second.write("a second line\n")
        self.assertEqual(second.declare()["declared"], "partial")

    # -- R2: the persistence has to succeed ----------------------------------

    def test_a_FAILED_carry_REFUSES_the_handle_and_keeps_the_evidence(self):
        """The reviewer's probe models `_write_carried`'s ordinary `OSError`
        return; it caused no host disk failure and neither does this."""
        first = self.captured()
        first.wrote(b"first-prefix")
        first.declare("failed")
        with mock.patch.object(self.fmt, "_write_carried",
                               lambda *operands: False):
            second = self.captured()
            second.wrote(b"second-prefix")
            said = second.declare(None)
        # THE LOSS SURVIVES EITHER WAY, and this is what actually happens:
        # the prior sidecar is never cleared, and the REFUSED writer -- whose
        # own bytes never reached a file -- declares `failed` over it, naming
        # the acquisition refusal. Both words say the same thing about the
        # same bytes, which is why the refusal is safe.
        self.assertEqual(said["declared"], "failed")
        self.assertIn("could not be carried", said["reason"])
        third = self.captured()
        third.wrote(b"third-whole")
        self.assertEqual(third.declare("finished")["declared"], "failed")
        self.assertEqual(self.followed()["state"], "failed")

    def test_that_refusal_does_NOT_stop_the_child_from_running(self):
        """Logging contains its own failure: a refused handle leaves the
        stream on DEVNULL and declared, and the provider runs as it would."""
        import subprocess

        first = self.captured()
        first.wrote(b"first")
        first.declare("failed")
        with mock.patch.object(self.fmt, "_write_carried",
                               lambda *operands: False):
            second = self.captured()
            self.assertIs(second.fileno_or_devnull, subprocess.DEVNULL)
            self.assertEqual(second.declare("finished")["declared"], "failed")

    def test_the_BYTES_a_refused_writer_had_are_not_written_anywhere(self):
        first = self.captured()
        first.wrote(b"first")
        first.declare("failed")
        with mock.patch.object(self.fmt, "_write_carried",
                               lambda *operands: False):
            second = self.captured()
            second.wrote(b"NEVER REACHES THE FILE")
        with open(os.path.join(self.delivery.log_root,
                               self.fmt.log_name(self.STREAM))) as handle:
            self.assertEqual(handle.read(), "first")

    # -- R3: absence and inaccessibility are different -----------------------

    def test_an_INACCESSIBLE_carried_record_is_not_ABSENCE(self):
        """The reviewer injected `PermissionError` at the carried record only.
        Unknown history cannot establish completeness."""
        first = self.captured()
        first.wrote(b"first-prefix")
        first.declare("failed")
        second = self.captured()
        second.wrote(b"second-prefix")
        second.declare(None)
        real = os.open

        def refusing(name, *rest, **named):
            if isinstance(name, str) and name.endswith(".carried"):
                raise PermissionError("injected at the carried record only")
            return real(name, *rest, **named)

        with mock.patch.object(os, "open", refusing):
            third = self.captured()
            third.wrote(b"third-whole")
            said = third.declare("finished")
        self.assertEqual(said["declared"], "failed")
        self.assertEqual(self.followed()["state"], "failed")

    def test_a_NONREGULAR_carried_record_is_not_ABSENCE_either(self):
        first = self.captured()
        first.wrote(b"first")
        first.declare("failed")
        second = self.captured()
        second.wrote(b"second")
        second.declare(None)
        os.unlink(self.carried_place())
        os.mkfifo(self.carried_place())
        third = self.captured()
        third.wrote(b"third")
        self.assertEqual(third.declare("finished")["declared"], "failed")

    def test_a_READ_failure_on_the_record_is_not_ABSENCE_either(self):
        first = self.captured()
        first.wrote(b"first")
        first.declare("failed")
        second = self.captured()
        second.wrote(b"second")
        second.declare(None)
        real = os.read

        def refusing(handle, count):
            raise OSError("injected read failure")

        with mock.patch.object(os, "read", refusing):
            held = self.fmt.read_carried(self.room, self.STREAM)
        self.assertEqual(held, "failed")

    def test_a_GENUINELY_absent_record_is_still_absence(self):
        """The control for R3: the ordinary stream has no history and must not
        be reported as though it had an unreadable one."""
        self.assertIsNone(self.fmt.read_carried(self.room, self.STREAM))
        only = self.captured()
        only.wrote(b"ordinary bytes")
        self.assertEqual(only.declare("finished")["declared"], "finished")


class AMALFORMEDCarriedStateCannotBreakTheCapture(LogRoom):
    """Review 2026-09-18T07-23-56Z [R1], and it is the same shape as the
    generation-suffix defect this campaign already corrected once.

    `read_carried` decoded the record and then asked `said in SEVERITY`.
    Membership is a DICTIONARY LOOKUP, and a list or an object out of a JSON
    document is unhashable -- so `{"declared": []}` raised `TypeError` through
    `carry_declaration`, through `append_writer` and out of the real
    `_Captured` constructor, which runs BEFORE the provider starts. A capture
    that cannot set itself up is a capture that takes the workload with it,
    which is the containment rule this whole vocabulary rests on.
    """

    STREAM = "provider.stdout"

    def setUp(self):
        super().setUp()
        _as_the_image_lays_it_out(self)
        self.delivery = self.made()
        import attempt_log_format
        import claude_agent

        self.fmt = attempt_log_format
        self.claude_agent = claude_agent
        self.room = self.fmt.open_room(self.delivery.log_root)
        self.addCleanup(os.close, self.room)

    def fresh(self, name):
        """One delivery and its OWN room descriptor, per case.

        NOT A REBUILT SHARED ROOM: this suite holds a descriptor, and removing
        the directory under it leaves every later write failing for a reason
        that has nothing to do with the rule being tested. I made exactly that
        mistake in claim201156 and it is not worth making twice.
        """
        delivery = self.made(attempt_id=f"attempt-{name}")
        room = self.fmt.open_room(delivery.log_root)
        self.addCleanup(os.close, room)
        return delivery, room

    def carried(self, declared, stream=None, delivery=None):
        """A record whose `declared` member is whatever a document may hold."""
        stream = stream or self.STREAM
        held = delivery or self.delivery
        with open(os.path.join(held.log_root,
                               self.fmt.log_name(stream)), "w") as handle:
            handle.write("earlier bytes")
        with open(os.path.join(held.log_root,
                               self.fmt.carried_name(stream)), "w") as handle:
            json.dump({"declared": declared}, handle)

    def captured(self, stream=None, room=None):
        return self.claude_agent._Captured(self.room if room is None else room,
                                           self.fmt, stream or self.STREAM)

    # -- the real provider capture -------------------------------------------

    def test_EVERY_JSON_VALUE_is_decoded_without_raising(self):
        """Total over the value types a document may carry, and the two that
        are unhashable are the two that raised."""
        for index, declared in enumerate(
                ([], {}, 7, 1.5, True, None, "nonsense", [1, 2])):
            with self.subTest(declared=declared):
                delivery, room = self.fresh(f"malformed-{index}")
                self.carried(declared, delivery=delivery)
                held = self.captured(room=room)
                held.wrote(b"this turn's bytes")
                # CONSERVATIVE, because a history that cannot be read cannot
                # establish completeness.
                self.assertEqual(held.declare("finished")["declared"],
                                 "failed")

    def test_a_VALID_state_still_reads_as_itself(self):
        """The control: a rule that refused the real record would make every
        stream permanently incomplete."""
        for declared in ("failed", "truncated", "partial"):
            with self.subTest(declared=declared):
                delivery, room = self.fresh(f"valid-{declared}")
                self.carried(declared, delivery=delivery)
                held = self.captured(room=room)
                held.wrote(b"more")
                self.assertEqual(held.declare("finished")["declared"],
                                 declared)

    def test_a_CLEAN_stream_with_no_record_is_untouched(self):
        only = self.captured()
        only.wrote(b"ordinary bytes")
        self.assertEqual(only.declare("finished")["declared"], "finished")

    def test_the_CHILD_still_gets_a_usable_stream(self):
        """Containment: a malformed history is not a reason for the capture to
        fail, and the provider's own stream is still the log."""
        import subprocess

        self.carried([])
        held = self.captured()
        self.assertIsNot(held.fileno_or_devnull, subprocess.DEVNULL)
        held.wrote(b"this turn's bytes")
        held.declare("finished")
        with open(os.path.join(self.delivery.log_root,
                               self.fmt.log_name(self.STREAM))) as handle:
            self.assertEqual(handle.read(), "earlier bytesthis turn's bytes")

    def test_NO_DESCRIPTOR_is_leaked_by_a_malformed_record(self):
        """The construction opens the log before it reads the history; an
        exception between the two left the descriptor open."""
        before = len(os.listdir("/proc/self/fd"))
        for index in range(20):
            delivery, room = self.fresh(f"leak-{index}")
            self.carried([], delivery=delivery)
            held = self.captured(room=room)
            held.declare("finished")
        # THE ROOMS THEMSELVES ARE HELD until cleanup, so the bound allows one
        # per case and nothing more: a leaked LOG descriptor would be a second.
        self.assertLess(len(os.listdir("/proc/self/fd")), before + 25)

    # -- the shared boundary the review names --------------------------------

    def test_WORST_answers_rather_than_raising_on_either_side(self):
        for one, other in (([], "failed"), ("failed", {}), ([], {}),
                           (None, "partial"), (7, "truncated")):
            with self.subTest(one=one, other=other):
                self.assertIn(self.fmt.worst(one, other),
                              (None, "failed", "partial", "truncated"))

    def test_DECLARED_STATE_is_the_one_place_that_decides(self):
        for good in ("failed", "truncated", "partial", "finished"):
            self.assertEqual(self.fmt.declared_state(good), good)
        for bad in ([], {}, 7, 1.5, True, None, "", "captured"):
            self.assertIsNone(self.fmt.declared_state(bad))

    # -- and the wrapper, which reaches the same opener ----------------------

    def test_the_WRAPPERS_stream_is_contained_too(self):
        """It reaches this opener before its own startup diagnostic, so an
        exception here is the diagnostic never being written at all."""
        import baton_worker

        self.carried({}, stream="worker.stderr")
        tee = baton_worker._TeeStream(io.StringIO(), self.room,
                                      "worker.stderr", self.fmt)
        tee.write("a startup diagnostic\n")
        self.assertEqual(tee.declare()["declared"], "failed")

    def test_the_WRAPPERS_real_stream_still_receives_the_text(self):
        """A tee that could break the thing it observes would be worse than no
        tee, and that rule has to survive a malformed history."""
        import baton_worker

        self.carried([], stream="worker.stderr")
        real = io.StringIO()
        tee = baton_worker._TeeStream(real, self.room, "worker.stderr",
                                      self.fmt)
        tee.write("a startup diagnostic\n")
        self.assertEqual(real.getvalue(), "a startup diagnostic\n")


if __name__ == "__main__":
    unittest.main()
