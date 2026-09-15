"""W167896 — the read-only Job viewer, driven over REAL status documents.

EVERY SNAPSHOT HERE COMES FROM `projection.status`. A viewer tested against a
handwritten dictionary proves only that it agrees with the fixture beside it;
the thing worth proving is that it reads what the Job Manager actually
publishes, so these cases submit real Jobs into a real store and view the
document that comes out.

AND THE OWNER IS TRAPPED. The viewer is given sources that raise on every act,
because "performs no act" is the acceptance -- not a property of the code as
currently written, which anybody could change tomorrow.
"""

import io
import json
import os
import sys
import time
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "job_manager"))

from baton_v12.job_manager import Unobserved, submit            # noqa: E402
from baton_v12.job_manager.projection import status             # noqa: E402
from baton_v12.job_manager.store import JobStore                # noqa: E402

from tools import job_viewer                                    # noqa: E402
from tools.job_viewer import (JobViewer, ViewerRefusal, read_locator,  # noqa: E402
                              read_snapshot, render_detail, render_list)

from fixtures import (FakeOperations, NOW, UUID,                 # noqa: E402
                      submission)

from tests.job_manager import fixtures                          # noqa: E402


def _epoch(stamp):
    import datetime

    return datetime.datetime.fromisoformat(
        stamp[:-1] + "+00:00" if stamp.endswith("Z") else stamp).timestamp()


def _stamp(epoch):
    import datetime

    return datetime.datetime.fromtimestamp(
        epoch, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


class ViewerCase(unittest.TestCase):
    """One real store, one real status document."""

    def setUp(self):
        self.root = tempfile.TemporaryDirectory(prefix="v12-job-viewer-")
        self.addCleanup(self.root.cleanup)
        self.now = 1000.0
        self.store = JobStore.open(os.path.join(self.root.name, "jobs.sqlite"),
                                   authority_uuid=UUID, incarnation="v",
                                   clock=lambda: NOW)
        self.addCleanup(self.store.close)
        submit(self.store, submission())

    def document(self):
        return status(self.store, Unobserved(), observed_at=NOW)

    def snapshot(self, document=None, received_at=None):
        return read_snapshot(document if document is not None
                             else self.document(),
                             received_at=self.now if received_at is None
                             else received_at)

    def listed(self, snapshot=None, now=None):
        return "\n".join(render_list(snapshot or self.snapshot(),
                                      now=self.now if now is None else now))


class TheViewShowsTheJobsThatAreThere(ViewerCase):

    def test_two_independent_jobs_are_both_visible_and_distinct(self):
        """The whole reason this Work exists: V12 runs Jobs in parallel and an
        operator could not see them."""
        shown = self.listed()
        self.assertIn("JOB job-a", shown)
        self.assertIn("JOB job-b", shown)
        # AND THEIR STAGES DO NOT BLEED TOGETHER. job-a has implementation and
        # review; job-b has implementation alone.
        first = shown.index("JOB job-a")
        second = shown.index("JOB job-b")
        self.assertLess(first, second)
        self.assertIn("job-a/review", shown[first:second])
        # AND A BLOCKED STAGE SAYS WHAT IT IS WAITING ON, in identities rather
        # than in the document's own internals.
        self.assertIn("held: waiting on job-a/implementation (queued)", shown)
        self.assertNotIn("'open':", shown)
        self.assertNotIn("job-a/", shown[second:])

    def test_the_exact_identities_are_shown_not_summarised(self):
        """An operator chasing a stuck Job has to be able to hand somebody
        else the identity, so the detail view carries the real ones."""
        detail = "\n".join(render_detail(self.snapshot(), "job-a",
                                          now=self.now))
        stage = self.document()["jobs"][0]["stages"][0]
        self.assertIn(stage["stage_id"], detail)
        self.assertIn(stage["work_id"], detail)
        self.assertIn(stage["attempt_id"], detail)
        self.assertIn(stage["offer_id"], detail)

    def test_a_foreign_identity_refuses_instead_of_rendering_empty(self):
        """An empty detail view for a Job that is not here reads exactly like
        a Job that is here and idle."""
        with self.assertRaises(ViewerRefusal) as caught:
            render_detail(self.snapshot(), "job-zzz", now=self.now)
        self.assertIn("holds no Job", str(caught.exception))


class NothingIsInvented(ViewerCase):

    def test_activity_is_unknown_until_a_trusted_source_exists(self):
        """W61599 owns the activity source. Until it exists this says
        `unknown` -- and an empty stream is not progress, so nothing here
        derives liveness from the fact that a read returned."""
        self.assertIn("activity unknown", self.listed())
        detail = "\n".join(render_detail(self.snapshot(), "job-a",
                                          now=self.now))
        self.assertRegex(detail, r"activity\s+unknown")

    def test_elapsed_comes_from_source_times_and_not_the_wall_clock(self):
        """A stage whose start nobody recorded has an UNKNOWN elapsed. The
        alternative is measuring how long this program has been looking and
        printing it as how long the Job has been running."""
        document = self.document()
        for stage in document["jobs"][0]["stages"]:
            for episode in stage.get("episodes") or []:
                episode["opened_at"] = None
        shown = self.listed(self.snapshot(document))
        self.assertIn("elapsed unknown", shown)

    def test_a_known_start_produces_a_real_elapsed(self):
        """And the reversal of the case above: when the source time IS there,
        it is used -- so `unknown` means missing rather than unimplemented."""
        document = self.document()
        document["observed_at"] = "2026-09-02T00:05:00.000Z"
        shown = self.listed(self.snapshot(document))
        self.assertIn("elapsed 5m00s", shown)
        self.assertNotIn("elapsed unknown", shown)

    def test_an_unread_manager_says_nobody_looked(self):
        """`canonical: false` is the difference between "nothing is running"
        and "nobody looked", and the view must not quietly render the first."""
        self.assertFalse(self.document()["canonical"])
        self.assertIn("NOT read", self.listed())


class TheViewNeverHidesItsOwnAge(ViewerCase):

    def test_a_fresh_reading_shows_when_it_was_observed(self):
        shown = self.listed()
        self.assertIn("observed at 2026-09-02T00:00:00.000Z", shown)
        self.assertNotIn("STALE", shown)

    def test_an_unrefreshed_view_becomes_conspicuously_stale(self):
        snapshot = self.snapshot()
        shown = self.listed(snapshot, now=self.now + 60)
        self.assertIn("!! STALE", shown)
        self.assertIn("1m00s ago", shown)

    def test_a_failed_read_disconnects_and_keeps_saying_so(self):
        """The last good reading is kept because it was true once -- as long
        as the view says when."""
        taken = [self.document()]

        def source():
            if not taken:
                raise OSError("the status document went away")
            return taken.pop()

        viewer = JobViewer(source, clock=lambda: self.now, sleeper=lambda _: None)
        viewer.refresh()
        self.assertTrue(viewer.snapshot.connected)
        viewer.refresh()
        self.assertFalse(viewer.snapshot.connected)
        shown = "\n".join(render_list(viewer.snapshot, now=self.now))
        self.assertIn("!! DISCONNECTED", shown)
        self.assertIn("OSError", shown)
        # THE JOBS ARE STILL THERE, under the warning rather than instead of it.
        self.assertIn("JOB job-a", shown)

    def test_a_reconnect_clears_the_warning(self):
        held = [self.document(), None, self.document()]

        def source():
            taken = held.pop()
            if taken is None:
                raise OSError("briefly gone")
            return taken

        viewer = JobViewer(source, clock=lambda: self.now, sleeper=lambda _: None)
        viewer.refresh()
        viewer.refresh()
        self.assertFalse(viewer.snapshot.connected)
        viewer.refresh()
        self.assertTrue(viewer.snapshot.connected)
        self.assertNotIn("DISCONNECTED",
                         "\n".join(render_list(viewer.snapshot, now=self.now)))
        self.assertEqual((viewer.reads, viewer.failures), (3, 1))


class StaleBytesAreNeverReportedFresh(ViewerCase):
    """REVIEW claim168071 [P1] -- the defect this whole viewer exists to
    prevent, which the first form had.

    `age_seconds` used only the LOCAL read time and every refresh reset it, so
    re-reading one unchanged status file forever reported "read 0s ago" with no
    warning. An old document looked fresh indefinitely under the documented
    polling loop.
    """

    def test_rereading_an_unchanged_document_goes_stale(self):
        """The source is not advancing. Reading it again is not news."""
        document = self.document()
        wall = [_epoch(document["observed_at"])]
        viewer = JobViewer(lambda: document, clock=lambda: self.now,
                           wall=lambda: wall[0], sleeper=lambda _: None)
        viewer.refresh()
        fresh = "\n".join(render_list(viewer.snapshot, now=self.now,
                                       wall_now=wall[0]))
        self.assertNotIn("STALE", fresh)
        # SIXTY LOGICAL SECONDS LATER, same bytes, same successful read.
        wall[0] += 60
        viewer.refresh()
        shown = "\n".join(render_list(viewer.snapshot, now=self.now,
                                       wall_now=wall[0]))
        self.assertIn("!! STALE", shown)
        self.assertIn("observed 1m00s ago", shown)

    def test_an_observation_that_was_already_old_is_stale_on_first_read(self):
        """A view that only watched its own reads would call a two-hour-old
        document fresh the instant it opened it."""
        document = self.document()
        wall = _epoch(document["observed_at"]) + 7200
        snapshot = read_snapshot(document, received_at=self.now)
        self.assertTrue(snapshot.stale(self.now, wall_now=wall))
        self.assertIn("!! STALE", "\n".join(
            render_list(snapshot, now=self.now, wall_now=wall)))

    def test_an_advancing_observation_stays_fresh(self):
        """And the reversal: when the manager IS advancing, the view does not
        cry stale -- so the warning means something when it appears."""
        wall = [_epoch(self.document()["observed_at"])]

        def source():
            held = self.document()
            held["observed_at"] = _stamp(wall[0])
            return held

        viewer = JobViewer(source, clock=lambda: self.now,
                           wall=lambda: wall[0], sleeper=lambda _: None)
        for _ in range(4):
            wall[0] += 1
            viewer.refresh()
            self.assertNotIn("STALE", "\n".join(
                render_list(viewer.snapshot, now=self.now, wall_now=wall[0])))

    def test_an_unreadable_observation_time_is_treated_as_stale(self):
        """A view that cannot tell how old its facts are must not present them
        as current."""
        document = dict(self.document(), observed_at="not an instant")
        snapshot = read_snapshot(document, received_at=self.now)
        self.assertTrue(snapshot.stale(self.now, wall_now=self.now))

    def test_the_configured_threshold_reaches_the_rendering(self):
        """REVIEW claim168169 [P2]. The viewer computed a threshold from the
        interval and then rendered with the 1 s default, so at `--interval 5`
        a three-second-old observation was called STALE against a documented
        ten-second window. A threshold that never reaches the renderer is a
        threshold nobody applies -- and calling stale_after(5) directly, as my
        previous case did, cannot catch a missing connection."""
        document = self.document()
        wall = [_epoch(document["observed_at"]) + 3]
        stream = io.StringIO()
        viewer = JobViewer(lambda: document, clock=lambda: self.now,
                           wall=lambda: wall[0], interval=5.0,
                           sleeper=lambda _: None)
        viewer.run(ticks=1, stream=stream)
        self.assertNotIn("STALE", stream.getvalue())
        # AND THE SAME OBSERVATION AT THE 1 s DEFAULT *IS* STALE, so the
        # interval is doing the work rather than the age alone.
        other = io.StringIO()
        JobViewer(lambda: document, clock=lambda: self.now,
                  wall=lambda: wall[0], interval=1.0,
                  sleeper=lambda _: None).run(ticks=1, stream=other)
        self.assertIn("!! STALE", other.getvalue())

    def test_the_default_two_second_boundary_is_inclusive(self):
        """The selected behaviour is a changed or outdated observation visible
        WITHIN 2 s. A strict `>` first flagged an exact integer-tick
        observation one whole tick late, at 3 s."""
        document = self.document()
        started = _epoch(document["observed_at"])
        snapshot = read_snapshot(document, received_at=self.now)
        self.assertFalse(snapshot.stale(self.now, wall_now=started + 1.9))
        self.assertTrue(snapshot.stale(self.now, wall_now=started + 2.0))

    def test_the_threshold_follows_the_configured_interval(self):
        """The fixed 3 s constant ignored `--interval` entirely, so the
        selected 2 s behaviour was not what the loop actually did."""
        self.assertEqual(job_viewer.stale_after(1.0), 2.0)
        self.assertEqual(job_viewer.stale_after(5.0), 10.0)
        self.assertEqual(job_viewer.stale_after(0.1),
                         job_viewer.STALE_FLOOR_SECONDS)


class AMalformedRefreshDoesNotEndTheView(ViewerCase):
    """REVIEW claim168071 [P2]. The read was inside the handler and the PARSE
    was outside it, so a truncated document -- which the documented shell
    redirection produces while the file is being replaced -- escaped and exited
    the command. A viewer that dies because it caught its source mid-write is
    worse than one that says so and looks again."""

    def viewer(self, held):
        return JobViewer(lambda: held.pop(0), clock=lambda: self.now,
                         sleeper=lambda _: None)

    def test_a_truncated_document_disconnects_and_keeps_the_last_view(self):
        viewer = self.viewer([self.document(), b"{"])
        viewer.refresh()
        viewer.refresh()
        self.assertFalse(viewer.snapshot.connected)
        shown = "\n".join(render_list(viewer.snapshot, now=self.now))
        self.assertIn("!! DISCONNECTED", shown)
        self.assertIn("refused:", shown)
        self.assertIn("JOB job-a", shown)

    def test_a_json_list_is_refused_rather_than_crashing(self):
        """`held.get` on a list raises AttributeError, which escapes as a
        crash rather than as the refusal this is."""
        with self.assertRaises(ViewerRefusal) as caught:
            read_snapshot(b"[1, 2, 3]", received_at=self.now)
        self.assertIn("one document", str(caught.exception))

    def test_the_loop_retries_after_a_bad_document(self):
        viewer = self.viewer([self.document(), b"{", self.document()])
        viewer.refresh()
        viewer.refresh()
        viewer.refresh()
        self.assertTrue(viewer.snapshot.connected)
        self.assertEqual((viewer.reads, viewer.failures), (3, 1))

    def test_a_nested_malformed_document_never_replaces_the_good_one(self):
        """REVIEW claim168169 [P2]. `{"schema": ..., "jobs": [null]}` carried
        the right schema, passed, REPLACED the last good snapshot, and then
        raised `AttributeError` from the renderer -- outside refresh's handler,
        so the command died holding a view it had already thrown away.
        Validating the top level alone is not validating the document."""
        for broken in ({"jobs": [None]},
                       {"jobs": "not a list"},
                       {"jobs": [{"job_id": "job-a", "stages": [None]}]},
                       {"jobs": [{"job_id": "job-a", "stages": "no"}]},
                       {"jobs": [{"job_id": "job-a", "stages": [
                           {"stage_id": "s", "episodes": [None]}]}]},
                       {"jobs": [{"job_id": "job-a", "stages": [
                           {"stage_id": "s", "artifacts": "no"}]}]}):
            with self.subTest(broken=str(broken)[:40]):
                good = self.document()
                viewer = self.viewer([good, dict(good, **broken)])
                viewer.refresh()
                viewer.refresh()
                self.assertFalse(viewer.snapshot.connected)
                # THE GOOD DOCUMENT IS STILL THERE, and rendering it does not
                # raise.
                shown = "\n".join(render_list(viewer.snapshot, now=self.now))
                self.assertIn("!! DISCONNECTED", shown)
                self.assertIn("JOB job-a", shown)

    def test_detail_on_a_first_unreadable_snapshot_does_not_exit(self):
        """"I have not managed to look" and "I looked and it is not there"
        are different answers, and only the second is about the Job."""
        viewer = self.viewer([b"{", self.document()])
        viewer.refresh()
        self.assertFalse(viewer.snapshot.connected)
        shown = "\n".join(render_detail(viewer.snapshot, "job-a",
                                         now=self.now))
        self.assertIn("no readable observation yet", shown)
        # AND THE NEXT READ RECOVERS, which is the point of not exiting.
        viewer.refresh()
        self.assertIn("STAGE job-a/implementation",
                      "\n".join(render_detail(viewer.snapshot, "job-a",
                                               now=self.now)))

    def test_a_connected_snapshot_without_the_job_still_refuses(self):
        """A view that answered "not read yet" for a Job that genuinely is not
        in a readable snapshot would hide a real absence."""
        viewer = self.viewer([self.document()])
        viewer.refresh()
        with self.assertRaises(ViewerRefusal):
            render_detail(viewer.snapshot, "job-zzz", now=self.now)

    def test_an_oversize_document_disconnects_rather_than_exiting(self):
        viewer = self.viewer([self.document(),
                              b"x" * (job_viewer.MAX_SNAPSHOT_BYTES + 1)])
        viewer.refresh()
        viewer.refresh()
        self.assertFalse(viewer.snapshot.connected)
        self.assertIn("JOB job-a", "\n".join(
            render_list(viewer.snapshot, now=self.now)))


class TheIntervalIsFiniteAndPositive(ViewerCase):
    """Zero is convenient in a test that does not want to sleep and is not a
    reason to admit it in the user command."""

    def test_a_spinning_or_nonfinite_interval_refuses(self):
        for wrong in (0, -1, float("nan"), float("inf"), "x", None):
            with self.subTest(interval=repr(wrong)):
                with self.assertRaises(ViewerRefusal):
                    job_viewer.checked_interval(wrong)

    def test_the_command_refuses_one_too(self):
        import io

        stream = io.StringIO()
        code = job_viewer.main(["--status", "/dev/null", "--interval", "0"],
                               stream=stream)
        self.assertEqual(code, 2)
        self.assertIn("spin", stream.getvalue())


class TheBoundsAreHonest(ViewerCase):

    def test_an_oversize_snapshot_refuses_rather_than_omitting_jobs(self):
        """A view that dropped the tail would silently omit Jobs -- and a Job
        an operator cannot see is the failure this Work exists to fix."""
        with self.assertRaises(ViewerRefusal) as caught:
            read_snapshot(b"x" * (job_viewer.MAX_SNAPSHOT_BYTES + 1),
                          received_at=self.now)
        self.assertIn("refusing rather than showing", str(caught.exception))

    def test_a_foreign_schema_refuses(self):
        with self.assertRaises(ViewerRefusal):
            read_snapshot({"schema": "baton.v12.job-status/1"},
                          received_at=self.now)

    def test_a_locator_read_is_bounded_and_visibly_truncated(self):
        place = os.path.join(self.root.name, "result.log")
        with open(place, "wb") as handle:
            handle.write(b"L" * (job_viewer.MAX_LOCATOR_BYTES + 4096))
        shown = read_locator({"locator": place})
        self.assertLess(len(shown), job_viewer.MAX_LOCATOR_BYTES + 400)
        self.assertIn("truncated at", shown)

    def test_an_artifact_without_a_locator_is_unavailable_not_guessed(self):
        with self.assertRaises(ViewerRefusal) as caught:
            read_locator({"output_name": "result", "locator": None})
        self.assertIn("nothing this view is permitted to read",
                      str(caught.exception))

    def test_a_stage_with_no_frozen_output_says_unavailable(self):
        detail = "\n".join(render_detail(self.snapshot(), "job-a",
                                          now=self.now))
        self.assertIn("unavailable (no frozen output", detail)

    def test_read_locator_takes_no_path_operand(self):
        """A HELPER-SHAPE CHECK, and nothing more. Review claim168257: this is
        not evidence of manager permission -- that comes from
        `select_artifact` walking snapshot identities, which
        `test_the_artifact_is_selected_out_of_the_snapshot_by_identity` and the
        owner-produced case hold. Kept because a path operand appearing here
        later would be worth noticing."""
        import inspect

        taken = inspect.signature(read_locator).parameters
        self.assertEqual([one for one in taken], ["artifact", "opener"])


class TheDrillDownIsWiredAndUsesLocatorSemantics(ViewerCase):
    """REVIEW claim168071 [P2]. `main`/`render_detail` never called
    `read_locator`, and the standalone helper opened a locator STRING as a host
    pathname -- so an ordinary `file:///...` retained-result locator failed.
    Taking a dict from the caller was never evidence of manager permission
    either; selection now starts from the snapshot and walks identities.
    """

    def published(self, **changed):
        """A SYNTHETIC artifact in the manager's own artifact SHAPE.

        Labelled accurately after review claim168257: this writes a local file
        and injects an artifact document with a made-up digest. It is useful
        for the locator rules -- `file:///`, relative refusal, non-regular
        refusal, truncation -- because those are about the LOCATOR and not
        about provenance. It is NOT an owner-produced frozen output, and the
        earlier docstring calling it one overstated the fixture.
        `TheOwnerProducedArtifactReachesTheView` is where a real one is
        carried through.
        """
        place = os.path.join(self.root.name, "result.log")
        with open(place, "wb") as handle:
            handle.write(b"the retained result\n")
        held = {"output_name": "result", "artifact_id": "artifact-1",
                "media_type": "text/plain", "bytes": 20,
                "content_digest": "sha256:" + "c" * 64,
                "locator": "file://" + place}
        held.update(changed)
        document = self.document()
        document["jobs"][0]["stages"][0]["artifacts"] = [held]
        return document, held, place

    def test_a_file_uri_locator_is_read_as_a_locator(self):
        """`integration_bundle` already treats `file:///...` as a locator; the
        viewer was opening the whole URI as a filename."""
        _, artifact, place = self.published()
        self.assertTrue(artifact["locator"].startswith("file:///"))
        self.assertEqual(job_viewer.locator_path(artifact["locator"]), place)
        self.assertEqual(read_locator(artifact), "the retained result\n")

    def test_an_absolute_path_locator_also_reads(self):
        _, artifact, place = self.published(locator=None)
        artifact["locator"] = place
        self.assertEqual(read_locator(artifact), "the retained result\n")

    def test_a_relative_reference_is_never_resolved_against_the_cwd(self):
        """Where this program happens to be running is not part of the
        manager's meaning."""
        for wrong in ("result.log", "./result.log", "s3://bucket/key",
                      "file://relative"):
            with self.subTest(locator=wrong):
                with self.assertRaises(ViewerRefusal) as caught:
                    job_viewer.locator_path(wrong)
                self.assertIn("absolute local locators",
                              str(caught.exception))

    def test_the_artifact_is_selected_out_of_the_snapshot_by_identity(self):
        document, artifact, _ = self.published()
        snapshot = read_snapshot(document, received_at=self.now)
        stage = document["jobs"][0]["stages"][0]["stage_id"]
        self.assertEqual(
            job_viewer.select_artifact(snapshot, "job-a", stage, "result"),
            artifact)

    def test_an_unpublished_artifact_or_stage_refuses(self):
        document, _, _ = self.published()
        snapshot = read_snapshot(document, received_at=self.now)
        stage = document["jobs"][0]["stages"][0]["stage_id"]
        for job_id, stage_id, name in (("job-a", stage, "not-published"),
                                       ("job-a", "job-a/nope", "result"),
                                       ("job-zzz", stage, "result")):
            with self.subTest(name=name):
                with self.assertRaises(ViewerRefusal):
                    job_viewer.select_artifact(snapshot, job_id, stage_id,
                                               name)

    def test_a_locator_that_is_not_a_regular_file_refuses(self):
        """A fifo would block this program forever and a symlink would let the
        manager's locator name bytes outside what it published."""
        place = os.path.join(self.root.name, "pipe")
        os.mkfifo(place)
        with self.assertRaises(ViewerRefusal) as caught:
            read_locator({"locator": place})
        self.assertIn("regular file", str(caught.exception))
        linked = os.path.join(self.root.name, "linked.log")
        os.symlink("/etc/hostname", linked)
        with self.assertRaises(ViewerRefusal):
            read_locator({"locator": linked})

    def test_the_drill_down_banner_uses_the_configured_threshold(self):
        """REVIEW claim168257 [P2]. `_drilled` called `_banner` without the
        configured threshold, so a 3 s-old observation was fresh in the Job
        view and STALE in its artifact view at `--interval 5`. One document
        cannot be two ages."""
        document, _, _ = self.published()
        document["observed_at"] = _stamp(time.time() - 3)
        place = os.path.join(self.root.name, "status.json")
        with open(place, "w", encoding="utf-8") as handle:
            json.dump(document, handle)
        stage = document["jobs"][0]["stages"][0]["stage_id"]
        argv = ["--status", place, "--job", "job-a", "--stage", stage,
                "--artifact", "result"]
        wide = io.StringIO()
        self.assertEqual(job_viewer.main(argv + ["--interval", "5"],
                                         stream=wide), 0)
        self.assertNotIn("STALE", wide.getvalue())
        # AND AT THE 1 s DEFAULT THE SAME OBSERVATION *IS* STALE, so the
        # interval is doing the work rather than the age alone.
        narrow = io.StringIO()
        self.assertEqual(job_viewer.main(argv + ["--interval", "1"],
                                         stream=narrow), 0)
        self.assertIn("!! STALE", narrow.getvalue())

    def test_the_command_drills_down_through_identities(self):
        import io

        document, _, _ = self.published()
        place = os.path.join(self.root.name, "status.json")
        with open(place, "w", encoding="utf-8") as handle:
            json.dump(document, handle)
        stage = document["jobs"][0]["stages"][0]["stage_id"]
        stream = io.StringIO()
        code = job_viewer.main(["--status", place, "--job", "job-a",
                                "--stage", stage, "--artifact", "result"],
                               stream=stream)
        self.assertEqual(code, 0)
        shown = stream.getvalue()
        self.assertIn("ARTIFACT result", shown)
        self.assertIn("the retained result", shown)

    def test_drilling_down_without_identities_refuses(self):
        import io

        document, _, _ = self.published()
        place = os.path.join(self.root.name, "status.json")
        with open(place, "w", encoding="utf-8") as handle:
            json.dump(document, handle)
        stream = io.StringIO()
        code = job_viewer.main(["--status", place, "--artifact", "result"],
                               stream=stream)
        self.assertEqual(code, 2)
        self.assertIn("selected by identity", stream.getvalue())


class TheKnownIdentitiesAreShown(ViewerCase):
    """REVIEW claim168071 [P2]. `projection.status` supplies stage.runtime
    including the assignment, and allocation information; the view ignored
    them, so a document carrying a known worker and assignment rendered
    neither."""

    def reserved(self):
        """A REAL scheduler reservation, not an invented allocation document.

        Review claim168169 [P2]: my previous fixture wrote an `allocation_id`
        the scheduler does not publish, so it passed while the viewer missed
        the actual shape -- `assignment_id`, `worker_id`, `participant`,
        `lane`, `generation`, `allocation_state`. A fixture that invents the
        field it is checking proves only that the reader agrees with the
        fixture.
        """
        from tests.job_manager.test_scheduling import pool, principals

        from baton_v12.job_manager import episodes, scheduler
        from baton_v12.job_manager.submission import stage_rows

        document = pool()
        scheduler.activate_pool(self.store, document, principals(document))
        [row] = [one for one in stage_rows(self.store)
                 if one["stage_id"] == "job-a/implementation"]
        live = episodes.live_of(self.store, row["stage_id"])
        allocation = scheduler.reserve(
            self.store, episodes.attempting(dict(row), live))
        return dict(allocation)

    def running(self, allocation=None):
        document = self.document()
        stage = document["jobs"][0]["stages"][0]
        stage["state"] = "running"
        stage["runtime"] = {
            "runtime_id": "runtime-7f3a", "execution_runtime": "oci",
            "assignment": {"work_ref": "0000000a-W1",
                           "participant": "baton.worker", "generation": 3},
            "activity": None}
        if allocation is not None:
            stage["allocation"] = allocation
        return document

    def test_the_real_scheduler_reservation_is_displayed(self):
        """The reservation exists BEFORE any runtime does, so its worker and
        assignment are facts of their own rather than runtime members."""
        allocation = self.reserved()
        snapshot = read_snapshot(self.running(allocation), received_at=self.now)
        detail = "\n".join(render_detail(snapshot, "job-a", now=self.now))
        for member in ("assignment_id", "worker_id", "participant", "lane",
                       "allocation_state"):
            self.assertIn(str(allocation[member]), detail,
                          member + " is not shown")
        self.assertRegex(detail, r"reserved worker\s+" +
                         str(allocation["worker_id"]))
        self.assertRegex(detail, r"reservation state\s+" +
                         str(allocation["allocation_state"]))

    def test_a_reservation_without_a_runtime_still_shows_its_worker(self):
        """An assignment before a runtime exists is exactly the case an
        operator asks about: reserved, not yet started."""
        allocation = self.reserved()
        document = self.document()
        document["jobs"][0]["stages"][0]["allocation"] = allocation
        snapshot = read_snapshot(document, received_at=self.now)
        detail = "\n".join(render_detail(snapshot, "job-a", now=self.now))
        self.assertIn(str(allocation["worker_id"]), detail)
        self.assertIn(str(allocation["assignment_id"]), detail)
        # AND THE RUNTIME FIELDS STILL SAY UNKNOWN, because there is none.
        self.assertRegex(detail, r"runtime\s+unknown")

    def test_the_runtime_fixed_assignment_fields_are_rendered(self):
        """These are the runtime's OWN assignment, retained beside the
        scheduler's reservation rather than instead of it."""
        snapshot = read_snapshot(self.running(), received_at=self.now)
        detail = "\n".join(render_detail(snapshot, "job-a", now=self.now))
        for expected in ("runtime-7f3a", "oci", "baton.worker",
                         "0000000a-W1"):
            self.assertIn(expected, detail)
        self.assertRegex(detail, r"assigned gen\s+3")

    def test_an_absent_runtime_and_reservation_say_unknown(self):
        snapshot = self.snapshot()
        detail = "\n".join(render_detail(snapshot, "job-a", now=self.now))
        self.assertRegex(detail, r"runtime\s+unknown")
        self.assertRegex(detail, r"assigned to\s+unknown")
        self.assertRegex(detail, r"reserved worker\s+unknown")
        self.assertRegex(detail, r"reservation\s+unknown")

    def test_an_exact_identifier_is_never_clipped_in_detail(self):
        """A 100-column clamp cut identifiers in half -- precisely the view an
        operator opened the detail for."""
        document = self.running()
        stage = document["jobs"][0]["stages"][0]
        snapshot = read_snapshot(document, received_at=self.now)
        detail = "\n".join(render_detail(snapshot, "job-a", now=self.now))
        self.assertIn(stage["attempt_id"], detail)
        self.assertIn(stage["offer_id"], detail)
        self.assertGreater(max(len(one) for one in detail.splitlines()), 100)


class TheViewerPerformsNoAct(ViewerCase):

    class Trap:
        """Every act the operator surface must not have."""

        def __init__(self, document):
            self._document = document
            self.reads = 0

        def __call__(self):
            self.reads += 1
            return self._document

        def _refuse(self, *_a, **_k):
            raise AssertionError("the viewer performed an act")

        submit = claim = cancel = serve = reconcile = clean = _refuse
        advance = apply = freeze = settle = _refuse

    def test_refreshing_only_reads(self):
        trap = self.Trap(self.document())
        viewer = JobViewer(trap, clock=lambda: self.now, sleeper=lambda _: None)
        viewer.run(ticks=3, stream=open(os.devnull, "w"))
        self.assertEqual(trap.reads, 3)

    def test_the_store_is_unchanged_by_being_viewed(self):
        """The disposable owner state is established before and compared
        after, rather than assumed."""
        before = json.dumps(self.document(), sort_keys=True)
        viewer = JobViewer(lambda: self.document(), clock=lambda: self.now,
                           sleeper=lambda _: None)
        viewer.run(ticks=3, stream=open(os.devnull, "w"))
        render_detail(viewer.snapshot, "job-a", now=self.now)
        self.assertEqual(json.dumps(self.document(), sort_keys=True), before)

    def test_the_module_constructs_no_serving_factory(self):
        """Read the imports rather than the paragraph promising the absence."""
        import ast
        import pathlib

        source = (pathlib.Path(job_viewer.__file__)).read_text(encoding="utf-8")
        names = set()
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Import):
                names.update(one.name for one in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module)
        self.assertEqual(names, {"argparse", "datetime", "json", "os", "stat",
                                 "sys", "time", "baton_v12.job_manager"})
        # THE IDENTIFIERS, NOT THE PROSE. A text search here is satisfied --
        # or defeated -- by the very paragraph that promises the absence: the
        # module docstring says "no submit, claim, cancel, serve", so grepping
        # for "serve" finds the promise rather than an act. So this walks what
        # the module actually NAMES.
        used = set()
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Name):
                used.add(node.id)
            elif isinstance(node, ast.Attribute):
                used.add(node.attr)
        for absent in ("serve", "submit", "claim", "cancel", "reconcile",
                       "ControlStore", "JobStore", "Deployment", "connect",
                       "execute", "executemany", "commit", "cursor"):
            self.assertNotIn(absent, used)

    def test_a_changed_observation_is_visible_on_the_next_tick(self):
        """THE REFRESH LATENCY, TESTED LOGICALLY RATHER THAN BY WAITING.

        The selected target is a visible update within 2s at 1s polling. What
        makes that true is that a change costs AT MOST ONE INTERVAL -- the
        view never holds a reading for two ticks and never needs a second
        pass to notice. Measuring that with a stopwatch would prove only how
        busy this machine was; measuring the tick count proves the property.
        """
        first = self.document()
        second = self.document()
        second["observed_at"] = "2026-09-02T00:00:05.000Z"
        second["jobs"][0]["stages"][0]["state"] = "running"
        held = [second, first]
        viewer = JobViewer(lambda: held.pop(), clock=lambda: self.now,
                           interval=1.0, sleeper=lambda _: None)
        viewer.refresh()
        self.assertNotIn("running",
                         "\n".join(render_list(viewer.snapshot, now=self.now)))
        viewer.refresh()
        shown = "\n".join(render_list(viewer.snapshot, now=self.now))
        self.assertIn("running", shown)
        self.assertIn("2026-09-02T00:00:05.000Z", shown)
        # ONE tick, not two: at a 1s interval that is a 1s worst case.
        self.assertEqual(viewer.reads, 2)

    def test_the_loop_sleeps_between_reads_and_does_not_spin(self):
        slept = []
        viewer = JobViewer(lambda: self.document(), clock=lambda: self.now,
                           interval=1.0, sleeper=slept.append)
        viewer.run(ticks=4, stream=open(os.devnull, "w"))
        # THREE, not four: the sleep paces the NEXT read and after the last
        # one there is no next read.
        self.assertEqual(slept, [1.0, 1.0, 1.0])


class TheCanonicalReaderIsExercised(ViewerCase):
    """The REAL `projection.status` through a CANONICAL operations surface.

    WHAT THIS IS EVIDENCE OF, stated exactly (review claim168169 [P1]): the
    projection and the formatter, driven with a SIMULATED operations answer.
    `FakeOperations.frozen` is the fixture saying "the manager's answer is
    completed"; it is not the `observation_from` + `_Observing` observation of
    a durable model-free completion account, and the no-act check below is
    against this same fake's recorded calls rather than the real reader's
    owner boundaries.

    `TheRealObservationReaderReachesTheView` is where that reader is actually
    exercised. These cases are kept because the projection and formatter are
    worth covering cheaply -- not because they establish the observation.
    """

    def canonical(self, prepare=None):
        operations = FakeOperations()
        if prepare is not None:
            prepare(operations)
        held = status(self.store, operations, observed_at=NOW)
        self.assertTrue(held["canonical"])
        return operations, held

    def test_a_canonical_read_does_not_carry_the_nobody_looked_warning(self):
        _, held = self.canonical()
        shown = "\n".join(render_list(read_snapshot(held,
                                                     received_at=self.now),
                                       now=self.now))
        self.assertNotIn("NOT read", shown)
        self.assertIn("JOB job-a", shown)

    def test_two_jobs_stay_isolated_through_the_canonical_reader(self):
        _, held = self.canonical()
        self.assertEqual(sorted(one["job_id"] for one in held["jobs"]),
                         ["job-a", "job-b"])
        shown = "\n".join(render_list(read_snapshot(held,
                                                     received_at=self.now),
                                       now=self.now))
        first, second = shown.index("JOB job-a"), shown.index("JOB job-b")
        self.assertNotIn("job-b/", shown[first:second])
        self.assertNotIn("job-a/", shown[second:])

    def test_a_model_free_completed_stage_renders_through_the_real_reader(self):
        """The completion path this viewer has to be able to show, taken from
        the canonical reader rather than from a document written here."""
        def prepare(operations):
            operations.frozen("job-a/implementation", "completed")

        _, held = self.canonical(prepare)
        states = {one["stage_id"]: one["state"]
                  for job in held["jobs"] for one in job["stages"]}
        self.assertEqual(states["job-a/implementation"], "completed")
        snapshot = read_snapshot(held, received_at=self.now)
        shown = "\n".join(render_list(snapshot, now=self.now))
        self.assertIn("completed", shown)
        # AND THE DEPENDENT STAGE IS NO LONGER HELD BEHIND IT.
        self.assertNotEqual(states["job-a/review"], "blocked")

    def test_a_held_stage_says_what_it_is_waiting_on(self):
        _, held = self.canonical()
        shown = "\n".join(render_list(read_snapshot(held,
                                                     received_at=self.now),
                                       now=self.now))
        self.assertIn("held: waiting on job-a/implementation", shown)

    def test_the_canonical_read_performs_no_act(self):
        """The operations surface records every act it is asked for, so an
        empty record is evidence rather than an assurance."""
        operations, held = self.canonical()
        before = list(operations.calls)
        snapshot = read_snapshot(held, received_at=self.now)
        render_list(snapshot, now=self.now)
        render_detail(snapshot, "job-a", now=self.now)
        self.assertEqual(operations.calls, before)
        self.assertEqual([one for one in operations.calls
                          if one[0] not in ("recover",)], [])


class TheRealObservationReaderReachesTheView(
        __import__("tests.tools.test_stage_execution", fromlist=["x"])
        .TwoBoundJobsTraverseServingAndCorrection):
    """REVIEW claim168169 [P1] -- the selected acceptance, over the ACTUAL
    reader.

    `TheCanonicalReaderIsExercised` drives the real projection with a
    SIMULATED operations answer (`FakeOperations.frozen`). That is useful
    evidence about the formatter and the projection and it is labelled as such
    there -- but it is not the current `observation_from` + `_Observing`
    observation of a durable model-free completion account, and the no-act
    check on a fake's own calls cannot establish the real reader's owner and
    factory boundaries.

    So this reuses the existing real fixture the review named and renders what
    that reader actually produces. It builds no provider, runs no engine or
    model, and adds no projection.
    """

    def test_the_view_renders_the_real_model_free_completion(self):
        from contextlib import ExitStack
        from unittest import mock

        from baton_v12.authority import Authority
        from baton_v12.integration import IntegrationStore
        from baton_v12.job_manager import episodes_of, status
        from tools import job_manager, stage_execution

        judges = self.judgment_workers()
        with mock.patch.object(self, "judgment_workers", return_value=judges):
            held, deployment, result_id, result = self.pending_judgments()
        stage = {"job_id": "job-b", "kind": "integration",
                 "stage_id": "job-b/integration",
                 **episodes_of(held.job, "job-b/integration")[-1]}
        document = self.composed_document(
            line_declared_base=self.base, result_judgment_workers=judges,
            **self.traversing())
        for execution in deployment.judges.values():
            self.judgment_turn(held, execution)
        self.tick(held)
        self.drive_job(held.job, held.composed, "job-b", "integration",
                       "completed", ticks=14)

        with ExitStack() as guards:
            # THE SAME NO-ACT TRAPS THE REAL FIXTURE USES, so "read-only" is
            # the owners' own refusal rather than this case's assurance.
            for owner, method in (
                    (Authority, "open"), (Authority, "session"),
                    (IntegrationStore, "open"),
                    (stage_execution, "operations_from"),
                    (stage_execution.Integration, "run"),
                    (stage_execution.Integration, "finish"),
                    (stage_execution.scheduler, "activate_pool"),
                    (stage_execution.review_cycles, "create_line")):
                guards.enter_context(mock.patch.object(
                    owner, method,
                    side_effect=AssertionError("the view acted: " + method)))
            observed = stage_execution.observation_from(
                document, held.job, held.control, checkout=self.checkout)
            projected = status(held.job,
                               job_manager._Observing(held.control, observed),
                               observed_at=NOW)
            # THE VIEWER, over what the real reader produced.
            snapshot = read_snapshot(projected, received_at=1000.0)
            shown = "\n".join(render_list(snapshot, now=1000.0))
            detail = "\n".join(render_detail(snapshot, "job-b", now=1000.0))

        self.assertTrue(snapshot.canonical)
        self.assertNotIn("NOT read", shown)
        # BOTH JOBS, BOUND AND SEPARATE, through the real observation.
        self.assertIn("JOB job-a", shown)
        self.assertIn("JOB job-b", shown)
        first, second = shown.index("JOB job-a"), shown.index("JOB job-b")
        self.assertNotIn("job-b/", shown[first:second])
        self.assertNotIn("job-a/", shown[second:])
        # THE MODEL-FREE COMPLETION: completed with no runtime at all.
        states = {one["stage_id"]: one["state"]
                  for job in projected["jobs"] for one in job["stages"]}
        self.assertEqual(states["job-b/integration"], "completed")
        self.assertIn("completed", detail)
        # ACTIVITY STAYS UNKNOWN even here: W61599 owns the trusted source.
        self.assertRegex(detail, r"activity\s+unknown")

    def test_a_foreign_job_still_refuses_against_the_real_reader(self):
        from unittest import mock

        from baton_v12.job_manager import status
        from tools import job_manager, stage_execution

        judges = self.judgment_workers()
        with mock.patch.object(self, "judgment_workers", return_value=judges):
            held, deployment, result_id, result = self.pending_judgments()
        document = self.composed_document(
            line_declared_base=self.base, result_judgment_workers=judges,
            **self.traversing())
        observed = stage_execution.observation_from(
            document, held.job, held.control, checkout=self.checkout)
        projected = status(held.job,
                           job_manager._Observing(held.control, observed),
                           observed_at=NOW)
        snapshot = read_snapshot(projected, received_at=1000.0)
        with self.assertRaises(ViewerRefusal):
            render_detail(snapshot, "job-zzz", now=1000.0)


# ONLY THE TWO CASES BELOW, not the parent's whole suite. Subclassing reuses
# the real fixture -- which is the point -- but `unittest` would otherwise
# discover and re-run every inherited case here, doubling a heavy suite for no
# extra evidence. The loader skips a non-callable attribute, so the inherited
# tests are unbound rather than re-run; the fixture methods they share stay.
_MINE = ("test_the_view_renders_the_real_model_free_completion",
         "test_a_foreign_job_still_refuses_against_the_real_reader")
for _name in [one for one in dir(TheRealObservationReaderReachesTheView)
              if one.startswith("test_") and one not in _MINE]:
    setattr(TheRealObservationReaderReachesTheView, _name, None)


class TheOwnerProducedArtifactReachesTheView(
        __import__("tests.job_manager.test_managed_integration_capacity",
                   fromlist=["x"]).ADecisionIsJournalledBeforeTheWorkExists):
    """REVIEW claim168257 -- an ACTUAL frozen artifact, carried through.

    `TheDrillDownIsWiredAndUsesLocatorSemantics` injects an artifact document
    with a made-up digest; it is honest about the locator RULES and says so,
    but it is not an owner-produced output. This one freezes a real result
    through `request_freeze`, reads the artifacts back through the manager's
    own `frozen_output_of` -- not the freeze call's answer -- carries them
    through the real projection, and then selects and reads by identity.

    The locator is the worker's own, named in the sealed result, so the file
    the view reads is the one the owner recorded rather than one this case
    pointed it at afterwards.
    """

    def frozen_artifacts(self):
        from baton_v12.worker_manager.output import frozen_output_of

        from tests.manager.test_output import OutputCase

        store, stage, allocation, answer = self.registered()
        place = os.path.join(self.root, "retained-result.txt")
        with open(place, "wb") as handle:
            handle.write(b"the owner's own retained result\n")
        outputs = OutputCase.present()
        outputs[0]["artifact"] = dict(outputs[0]["artifact"],
                                      locator="file://" + place)
        self.collected("prepare-attempt-1", outputs=outputs)
        held = frozen_output_of(self._control, "prepare-attempt-1")
        return store, stage, held, place

    def projected(self, store, artifacts):
        """The REAL projection, carrying the owner's own artifacts."""
        from baton_v12.job_manager.projection import status

        operations = fixtures.FakeOperations()
        operations.frozen("job-a/integration", "completed",
                          artifacts=artifacts)
        return status(store, operations, observed_at=fixtures.NOW)

    def test_an_owner_produced_artifact_is_selected_and_read(self):
        store, stage, frozen, place = self.frozen_artifacts()
        [owned] = frozen["artifacts"]
        document = self.projected(store, frozen["artifacts"])
        snapshot = read_snapshot(document, received_at=1000.0)
        # SELECTED BY IDENTITY out of what the projection published.
        chosen = job_viewer.select_artifact(snapshot, "job-a",
                                            "job-a/integration",
                                            owned["output_name"])
        self.assertEqual(chosen["content_digest"], owned["content_digest"])
        self.assertEqual(chosen["locator"], owned["locator"])
        # AND READ, BOUNDED, from the locator the OWNER recorded.
        self.assertEqual(read_locator(chosen),
                         "the owner's own retained result\n")

    def test_the_owners_artifact_is_shown_in_the_detail_view(self):
        store, stage, frozen, place = self.frozen_artifacts()
        [owned] = frozen["artifacts"]
        snapshot = read_snapshot(self.projected(store, frozen["artifacts"]),
                                 received_at=1000.0)
        detail = "\n".join(render_detail(snapshot, "job-a", now=1000.0))
        self.assertIn(owned["output_name"], detail)
        self.assertIn(owned["locator"], detail)
        self.assertNotIn("unavailable (no frozen output",
                         detail.split("STAGE job-a/integration")[-1])

    def test_an_owner_locator_whose_file_is_gone_is_unavailable_not_invented(self):
        """The owner recorded where it put the artifact; if that is no longer
        there, the view says so rather than producing content."""
        store, stage, frozen, place = self.frozen_artifacts()
        [owned] = frozen["artifacts"]
        os.remove(place)
        with self.assertRaises(ViewerRefusal) as caught:
            read_locator(owned)
        self.assertIn("could not be opened", str(caught.exception))


_OWNER_MINE = ("test_an_owner_produced_artifact_is_selected_and_read",
               "test_the_owners_artifact_is_shown_in_the_detail_view",
               "test_an_owner_locator_whose_file_is_gone_is_unavailable_not_invented")
for _name in [one for one in dir(TheOwnerProducedArtifactReachesTheView)
              if one.startswith("test_") and one not in _OWNER_MINE]:
    setattr(TheOwnerProducedArtifactReachesTheView, _name, None)


class TheCommandIsOrdinary(ViewerCase):

    def written(self):
        place = os.path.join(self.root.name, "status.json")
        with open(place, "w", encoding="utf-8") as handle:
            json.dump(self.document(), handle)
        return place

    def test_it_reads_a_status_document_an_operator_already_has(self):
        import io

        stream = io.StringIO()
        code = job_viewer.main(["--status", self.written(), "--ticks", "1",
                                "--interval", "1"], stream=stream)
        self.assertEqual(code, 0)
        self.assertIn("JOB job-a", stream.getvalue())
        self.assertIn("JOB job-b", stream.getvalue())

    def test_a_detail_request_for_an_absent_job_refuses_with_status_two(self):
        import io

        stream = io.StringIO()
        code = job_viewer.main(["--status", self.written(), "--job", "job-zzz",
                                "--ticks", "1", "--interval", "1"],
                               stream=stream)
        self.assertEqual(code, 2)
        self.assertIn("refused:", stream.getvalue())


if __name__ == "__main__":                                  # pragma: no cover
    unittest.main()
