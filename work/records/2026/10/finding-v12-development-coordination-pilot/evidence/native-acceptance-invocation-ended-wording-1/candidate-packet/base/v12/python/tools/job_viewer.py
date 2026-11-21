"""W167896 — the minimal read-only Job viewer.

WHAT IT IS. A terminal list/detail view over the status document the Job
Manager already publishes. It exists because V12 runs Jobs in parallel and an
operator cannot see them, and it is the SMALLEST thing that fixes that.

WHAT IT IS NOT, and each of these is a decision rather than an omission:

  IT HAS NO BACKEND. `job_manager/projection.py:status` is the read path and
  this file does not have a second one -- no SQL, no projection, no observer.
  A viewer with its own reader would be a second answer to "what is running",
  and the two would disagree on the day it mattered.

  IT PERFORMS NO ACT. There is no submit, claim, cancel, serve, reconcile or
  clean here, and no serving factory is constructed. Refresh reads; that is
  the whole verb list. An operator surface that could act is a control plane,
  and this one was asked not to be.

  IT INVENTS NO FACTS. Every value it shows comes from the snapshot or is
  spelled `unknown`. That sounds obvious and it is the entire difficulty: the
  tempting thing for a viewer is to compute a plausible number when a real one
  is missing -- elapsed time from the wall clock, activity from the fact that
  polling returned -- and each of those reports the VIEWER'S behaviour as if it
  were the JOB'S. W61599's trusted activity source now exists and this view
  reads it out of the snapshot; where the manager has observed nothing, activity
  is still `unknown`, an empty stream is not progress, and a known zero remains
  an observed empty count. The instant is the MANAGER'S RECEIPT TIME, so a relative
  age is shown only while the stage is live and a terminal stage shows the
  instant marked `last`.

  AND IT DOES NOT HIDE ITS OWN AGE. A snapshot is exactly as fresh as the
  moment it was observed. When it stops being refreshed, the view says so
  conspicuously rather than continuing to show numbers that were true once.
"""

import argparse
import datetime
import json
import os
import stat
import sys
import time

from baton_v12.job_manager import documents
from tools import job_observation
from tools.job_observation import _elapsed, _instant, _duration, _activity, _stage_line, _reason, _live_episode, _allocated, MAX_ACTIVITY_BYTES, MAX_INSTANT_TEXT, ALLOCATION_FIELDS

__all__ = ["MAX_SNAPSHOT_BYTES", "MAX_LOCATOR_BYTES", "POLL_SECONDS",
           "STALE_FLOOR_SECONDS", "stale_after", "UNKNOWN", "ViewerRefusal",
           "Snapshot", "JobViewer", "read_snapshot", "render_list",
           "render_detail", "select_artifact", "locator_path", "read_locator",
           "main"]

# THE DISPLAY BOUNDS. These bound WHAT THIS PROGRAM HOLDS AND SHOWS and are not
# protocol limits: the manager's own input rules are untouched by anything here.
MAX_SNAPSHOT_BYTES = 4 * 1024 * 1024
MAX_LOCATOR_BYTES = 64 * 1024

POLL_SECONDS = 1.0

# Owner M385273: UI poll frequency does not change source freshness.
STALE_FLOOR_SECONDS = job_observation.STALE_SECONDS


def stale_after(interval=POLL_SECONDS):
    return job_observation.STALE_SECONDS

UNKNOWN = "unknown"

# The one terminal-ish vocabulary this view borrows rather than restates.
TERMINAL_STATES = documents.TERMINAL_STAGE_STATES

# States where the operator is being WAITED ON, as opposed to states where the
# control plane owes the next act. Named here because "why is nothing moving"
# is the question a viewer exists to answer.
OPERATOR_ACTION_STATES = ("changes-requested",)
HELD_STATES = ("blocked", "queued")


class ViewerRefusal(Exception):
    """What this program answers with instead of showing something untrue."""


def _refuse(message):
    raise ViewerRefusal(message)


class Snapshot:
    """One reading, and everything known about HOW it was read.

    THERE ARE TWO CLOCKS HERE AND THEY ANSWER DIFFERENT QUESTIONS.
    `received_at` is this program's own monotonic clock -- when the bytes
    arrived. `observed_at` is the MANAGER'S wall clock -- when the store was
    actually looked at. A snapshot that arrived a moment ago can describe a
    store nobody has advanced in an hour, and conflating the two is exactly how
    stale bytes get reported as fresh.
    """

    def __init__(self, document, *, received_at, connected=True, failure=None, published_at=None):
        self.document = document
        self.received_at = received_at
        self.connected = connected
        self.failure = failure
        self.published_at = published_at

    @property
    def observed_at(self):
        return (self.document or {}).get("observed_at")

    @property
    def canonical(self):
        """Whether the manager was read at all. `false` is the difference
        between "nothing is running" and "nobody looked"."""
        return bool((self.document or {}).get("canonical"))

    def age_seconds(self, now):
        """How long since THIS PROGRAM read the bytes."""
        if self.received_at is None:
            return None
        return max(0.0, now - self.received_at)

    def observation_age(self, wall_now):
        """How long since THE MANAGER looked. Unknown when unparseable --
        and unknown is treated as stale, because a view that cannot tell how
        old its facts are must not present them as current."""
        age = job_observation.observation_age(self.observed_at, wall_now)
        return None if age is None else max(0.0, age)

    def stale(self, now, after=None, wall_now=None):
        # `after` is retained for callers, but the owner-selected policy is fixed.
        if not self.connected or job_observation.stale_ages(self.age_seconds(now)):
            return True
        if wall_now is None:
            return False
        ages = [job_observation.observation_age(self.observed_at, wall_now)]
        if self.published_at is not None:
            ages.append(wall_now - self.published_at)
        return job_observation.stale_ages(*ages)

    def jobs(self):
        return list((self.document or {}).get("jobs") or [])


def read_snapshot(source, *, received_at):
    """One status document, from bytes, text or an already-parsed mapping.

    OVERSIZE REFUSES RATHER THAN TRUNCATES. A view that quietly dropped the
    tail of a status document would silently omit Jobs -- and a Job an operator
    cannot see is exactly the failure this Work exists to fix. So the honest
    answer to "too big" is to say so.
    """
    if isinstance(source, (bytes, bytearray)):
        if len(source) > MAX_SNAPSHOT_BYTES:
            _refuse("this status document is " + str(len(source)) + " bytes "
                    "and this view holds " + str(MAX_SNAPSHOT_BYTES) + "; "
                    "refusing rather than showing an unknown subset of the "
                    "Jobs")
        try:
            held = json.loads(bytes(source).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            _refuse("this status document is not readable as one document")
    elif isinstance(source, str):
        return read_snapshot(source.encode("utf-8"), received_at=received_at)
    elif isinstance(source, dict):
        held = source
    else:
        _refuse("a status snapshot is a document, not "
                + type(source).__name__)
    if not isinstance(held, dict):
        # A LIST IS VALID JSON AND IS NOT A STATUS DOCUMENT. `held.get` on one
        # raises AttributeError, which escapes as a crash rather than as the
        # refusal this is.
        _refuse("a status snapshot is one document, not "
                + type(held).__name__)
    schema = held.get("schema")
    if schema != documents.STATUS_SCHEMA:
        # A VERSION THIS VIEW DOES NOT KNOW IS NOT A DOCUMENT TO READ THE
        # PARTS IT RECOGNISES OUT OF.
        _refuse("this view reads " + documents.STATUS_SCHEMA + " and this is "
                + repr(schema))
    _shaped(held)
    return Snapshot(held, received_at=received_at, published_at=getattr(source, "published_at", None))


def _shaped(held):
    """THE NESTED SHAPE, CHECKED BEFORE THIS DOCUMENT REPLACES A GOOD ONE.

    REVIEW claim168169 [P2]: `{"schema": ..., "jobs": [null]}` carried the
    right schema, passed, REPLACED the last good snapshot, and then raised
    `AttributeError` from the renderer -- outside `refresh`'s handler, so the
    command died holding a view it had already thrown away. Validating the
    top level alone is not validating the document.

    This checks the shape the renderer walks and nothing more: it is not a
    second projection and it does not re-derive a single value.
    """
    jobs = held.get("jobs")
    if jobs is None:
        return held
    if not isinstance(jobs, list):
        _refuse("this document's jobs are a list; this is "
                + type(jobs).__name__)
    for job in jobs:
        if not isinstance(job, dict):
            _refuse("every Job in this document is a document; one is "
                    + type(job).__name__)
        stages = job.get("stages")
        if stages is None:
            continue
        if not isinstance(stages, list):
            _refuse("a Job's stages are a list; " + repr(job.get("job_id"))
                    + " carries " + type(stages).__name__)
        for stage in stages:
            if not isinstance(stage, dict):
                _refuse("every stage is a document; " + repr(job.get("job_id"))
                        + " carries " + type(stage).__name__)
            for member in ("episodes", "artifacts", "gates"):
                value = stage.get(member)
                if value is not None and not isinstance(value, list):
                    _refuse("a stage's " + member + " are a list; "
                            + repr(stage.get("stage_id")) + " carries "
                            + type(value).__name__)
                for one in (value or []):
                    if not isinstance(one, dict):
                        _refuse("every entry in a stage's " + member
                                + " is a document; "
                                + repr(stage.get("stage_id")) + " carries "
                                + type(one).__name__)
    return held


def render_list(snapshot, *, now, width=100, wall_now=None,
                stale_seconds=None):
    """The list view: every Job, and how old this reading is."""
    lines = [_banner(snapshot, now, wall_now=wall_now,
                     stale_seconds=stale_seconds)]
    jobs = snapshot.jobs()
    if not jobs:
        lines.append("  (this snapshot reports no Jobs"
                     + ("" if snapshot.canonical
                        else "; the manager was not read, so this is "
                             "'nobody looked' rather than 'nothing is "
                             "running'")
                     + ")")
        return lines
    observed_at = snapshot.observed_at
    for job in jobs:
        stages = job.get("stages") or []
        lines.append("")
        lines.append("JOB " + str(job.get("job_id") or UNKNOWN)
                     + "   submission " + str(job.get("submission_id")
                                              or UNKNOWN) + "   " + job_observation.job_outcome(job))
        lines.append("  Job age " + job_observation.job_age(job, observed_at))
        for stage in stages:
            one = _stage_line(stage, observed_at, job)
            lines.append(
                "  {kind:<16} {state:<16} running {running:<8} "
                "activity {activity:<8} {stage_id}".format(**one)[:width])
            # BOUNDED, AND NOT CUT BY THE LINE WIDTH. Both of its parts are
            # already bounded at their source -- the count by its domain, the
            # instant by `MAX_INSTANT_TEXT` -- so this cannot be the line that
            # grows, and truncating it would lose exactly the fact it exists to
            # carry.
            if one["activity_when"]:
                lines.append("      activity " + one["activity_when"])
            lines.append("      " + one["timeout"])
            lines.append("      attempt " + str(one["attempt_id"]))
            lines.append("      operation " + one["operation"])
            if one["reason"]:
                lines.append("      " + one["reason"])
    return lines


def _banner(snapshot, now, wall_now=None, stale_seconds=None):
    """The shared fifteen-second policy applies to every rendering."""
    if not snapshot.connected:
        return ("!! DISCONNECTED -- this view has not been refreshed"
                + (" (" + str(snapshot.failure) + ")" if snapshot.failure
                   else "")
                + "; everything below was true at "
                + str(snapshot.observed_at or UNKNOWN))
    age = snapshot.age_seconds(now)
    observed = snapshot.observation_age(wall_now)
    if snapshot.stale(now, after=stale_seconds, wall_now=wall_now):
        return ("!! STALE -- observed "
                + (_duration(observed) + " ago" if observed is not None
                   else "at an unreadable time")
                + "; this view last read it " + _duration(age) + " ago; "
                + "observed at " + str(snapshot.observed_at or UNKNOWN))
    banner = ("observed at " + str(snapshot.observed_at or UNKNOWN)
              + "   (" + (_duration(observed) + " old" if observed is not None
                          else "age unknown")
              + ", read " + _duration(age) + " ago)")
    if not snapshot.canonical:
        banner += "   [the manager was NOT read: absences here mean nobody looked]"
    return banner


def render_detail(snapshot, job_id, *, now, wall_now=None,
                  stale_seconds=None):
    """One Job, with its exact identities and its permitted locators."""
    banner = _banner(snapshot, now, wall_now=wall_now,
                     stale_seconds=stale_seconds)
    if snapshot.document is None:
        # NO OBSERVATION YET IS NOT A MISSING JOB, and this is checked BEFORE
        # the search rather than after it. Review claim168169 [P2]: detail mode
        # refused the requested Job as absent on its first unreadable snapshot
        # and exited before a second read that would have recovered. "I have
        # not managed to look" and "I looked and it is not there" are different
        # answers, and only the second is about the Job.
        return [banner, "",
                "  (no readable observation yet; this view has nothing to say "
                "about " + str(job_id) + " until it reads one)"]
    for job in snapshot.jobs():
        if job.get("job_id") == job_id:
            break
    else:
        # A CONNECTED SNAPSHOT THAT GENUINELY LACKS THE JOB STILL REFUSES. An
        # empty detail view for a Job that is not here reads exactly like a Job
        # that is here and idle.
        _refuse("this snapshot holds no Job named " + repr(job_id)
                + "; it holds "
                + (", ".join(repr(one.get("job_id"))
                             for one in snapshot.jobs()) or "nothing"))
    lines = ["",
             "JOB " + str(job.get("job_id")) + "   " + job_observation.job_outcome(job),
             "  submission   " + str(job.get("submission_id") or UNKNOWN),
             "  input        " + str(job.get("input_digest") or UNKNOWN),
             "  policy       " + str(job.get("policy_digest") or UNKNOWN),
             "  terminal     " + str(job.get("terminal_policy") or UNKNOWN)]
    observed_at = snapshot.observed_at
    lines.append("  Job age " + job_observation.job_age(job, observed_at))
    for stage in job.get("stages") or []:
        one = _stage_line(stage, observed_at, job)
        lines.append("")
        lines.append("  STAGE " + one["stage_id"] + "  [" + one["state"] + "]")
        for label, value in (("work", one["work_id"]),
                             ("episode", one["episode"]),
                             ("offer", one["offer_id"]),
                             ("attempt", one["attempt_id"]),
                             ("operation", one["operation"]),
                             ("runtime", one["runtime_id"]),
                             ("engine", one["execution_runtime"]),
                             ("assigned to", one["assignment_participant"]),
                             ("assigned work", one["assignment_work"]),
                             ("assigned gen", one["assignment_generation"]),
                             ("reserved worker", one["allocation_worker"]),
                             ("reserved as", one["allocation_participant"]),
                             ("reservation", one["allocation_assignment"]),
                             ("reservation state", one["allocation_state"]),
                             ("lane", one["allocation_lane"]),
                             ("pool generation", one["allocation_generation"]),
                             ("selection", one["allocation_selection"]),
                             ("started", one["started_at"]),
                             ("running", one["running"]),
                             ("limit", one["timeout"]),
                             ("activity", one["activity"]
                              + ("" if not one["activity_when"]
                                 else " " + one["activity_when"])),
                             ("corrections", one["corrections"])):
            lines.append("    {:<12} {}".format(label, value))
        if one["reason"]:
            lines.append("    {:<12} {}".format("reason", one["reason"]))
        lines.extend(_artifact_lines(stage))
    # NOTHING IN THE DETAIL VIEW IS TRUNCATED. Review claim168071 [P2]: a
    # 100-column clamp cut exact identifiers and locators in half, which is
    # precisely the view an operator opened the detail for. The banner was
    # already exempt because clipping a warning cuts the warning off the front
    # of the warning; the same argument applies to an attempt id somebody has
    # to paste somewhere else.
    return [banner] + lines


def _artifact_lines(stage):
    """The manager-permitted locators, or an honest unavailable."""
    artifacts = stage.get("artifacts")
    if not artifacts:
        return ["    {:<12} {}".format(
            "results", "unavailable (no frozen output in this snapshot)")]
    lines = ["    results"]
    for one in artifacts:
        lines.append("      {:<20} {:>10}  {}".format(
            str(one.get("output_name") or UNKNOWN),
            str(one.get("bytes") if one.get("bytes") is not None else UNKNOWN),
            str(one.get("locator") or "unavailable (no locator)")))
    return lines


def select_artifact(snapshot, job_id, stage_id, output_name):
    """The ONE artifact the snapshot itself permits, chosen by identity.

    REVIEW claim168071 [P2]: the previous helper took any dict containing any
    `locator` and opened it. That is not manager permission -- it is whatever
    the caller handed over, and inspecting the function signature proved
    nothing about where the path came from. Selection now starts from the
    SNAPSHOT and walks explicit identities, so the only references reachable
    are ones the manager put in the document it published.
    """
    for job in snapshot.jobs():
        if job.get("job_id") != job_id:
            continue
        for stage in job.get("stages") or []:
            if stage.get("stage_id") != stage_id:
                continue
            for one in stage.get("artifacts") or []:
                if type(one) is dict and one.get("output_name") == output_name:
                    return one
            _refuse("stage " + repr(stage_id) + " publishes no artifact named "
                    + repr(output_name) + "; it has "
                    + (", ".join(repr(one.get("output_name"))
                                 for one in (stage.get("artifacts") or []))
                       or "none"))
        _refuse("Job " + repr(job_id) + " has no stage " + repr(stage_id))
    _refuse("this snapshot holds no Job named " + repr(job_id))


def locator_path(locator):
    """A supported LOCAL locator, resolved by the existing rules.

    `integration_bundle` already treats `file:///...` as a locator rather than
    as a pathname, and the viewer was opening the whole URI as a filename --
    so a perfectly ordinary retained-result locator failed. The supported form
    is the absolute local one; anything else is refused BY NAME rather than
    guessed at, because a locator this program does not understand is not one
    it should try to open.

    A RELATIVE REFERENCE IS NEVER RESOLVED AGAINST THE VIEWER'S CWD. Where
    this program happens to be running is not part of the manager's meaning,
    and resolving against it would make the same locator name different bytes
    depending on who ran the command.
    """
    if type(locator) is not str or not locator:
        _refuse("this artifact carries no locator, so there is nothing this "
                "view is permitted to read")
    if locator.startswith("file:///"):
        place = locator[len("file://"):]
    elif locator.startswith("/"):
        place = locator
    else:
        _refuse("this view reads absolute local locators (`file:///...` or an "
                "absolute path) and this is " + repr(locator[:80])
                + "; it does not resolve a reference against wherever the "
                "viewer happens to be running")
    if os.path.normpath(place) != place:
        _refuse("this locator is not canonically spelled: " + repr(place[:80]))
    return place


def read_locator(artifact, *, opener=None):
    """A bounded read of ONE locator THE MANAGER SUPPLIED.

    BOUNDED AND VISIBLY TRUNCATED. At most one screenful of evidence, and when
    there is more the output SAYS there is more: silent truncation is how a
    reader concludes a log ended where it merely stopped being shown.

    A REGULAR FILE AND NOTHING ELSE, opened without following a link. A fifo
    would block this program forever and a symlink would let the manager's
    locator name bytes outside what it published.
    """
    if type(artifact) is not dict:
        _refuse("an artifact is a document from the snapshot")
    place = locator_path(artifact.get("locator"))
    if opener is not None:
        with opener(place, "rb") as handle:
            body = handle.read(MAX_LOCATOR_BYTES + 1)
        return _shown(body)
    try:
        held = os.open(place, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError as failure:
        _refuse("this locator could not be opened (" + type(failure).__name__
                + "); the view does not go looking elsewhere for it")
    try:
        if not stat.S_ISREG(os.fstat(held).st_mode):
            _refuse("this locator does not name a regular file, so there is "
                    "no bounded content for this view to show")
        body = os.read(held, MAX_LOCATOR_BYTES + 1)
    finally:
        os.close(held)
    return _shown(body)


def _shown(body):
    truncated = len(body) > MAX_LOCATOR_BYTES
    text = body[:MAX_LOCATOR_BYTES].decode("utf-8", "replace")
    if truncated:
        text += ("\n-- truncated at " + str(MAX_LOCATOR_BYTES)
                 + " bytes; this view shows a bounded read and this file "
                 "continues --")
    return text


def _named(failure):
    """What went wrong, said in a way an operator can act on."""
    if isinstance(failure, ViewerRefusal):
        return "refused: " + str(failure)[:200]
    return type(failure).__name__


def checked_interval(interval):
    """A FINITE POSITIVE interval, or a refusal.

    Zero is convenient in a test that does not want to sleep and is not a
    reason to admit it in the user command: a zero or negative interval turns
    the documented loop into a spin, and a NaN turns every comparison against
    it false, which is worse than either.
    """
    try:
        held = float(interval)
    except (TypeError, ValueError):
        _refuse("a refresh interval is a number of seconds")
    if held != held or held in (float("inf"), float("-inf")):
        _refuse("a refresh interval is finite; " + repr(interval)
                + " is not a length of time")
    if held <= 0:
        _refuse("a refresh interval is greater than zero; " + repr(interval)
                + " would make this loop spin")
    return held


class JobViewer:
    """The bounded refresh loop.

    IT SLEEPS BETWEEN READS AND NEVER SPINS. The interval is configured, the
    loop waits for it, and a read that fails does not become a hot retry --
    the view goes DISCONNECTED and the next attempt happens on the ordinary
    tick. A viewer that burned a core asking the same question would be worse
    than no viewer.
    """

    def __init__(self, source, *, clock=time.monotonic, interval=POLL_SECONDS,
                 sleeper=time.sleep, wall=time.time):
        self._source = source
        self._clock = clock
        self._wall = wall
        self._interval = checked_interval(interval)
        self._sleep = sleeper
        self.snapshot = Snapshot(None, received_at=None, connected=False,
                                 failure="not read yet")
        self.reads = 0
        self.failures = 0

    def refresh(self):
        """One read. Never an act, and never a partial view on failure.

        REVIEW claim168071 [P2]: the read was inside the handler and the PARSE
        was outside it, so a valid snapshot followed by a truncated one -- which
        the documented shell redirection produces while the file is being
        replaced -- escaped as a refusal and exited the command. A viewer that
        dies because it caught its source mid-write is worse than one that says
        so and looks again on the ordinary tick.
        """
        self.reads += 1
        try:
            taken = read_snapshot(self._source(), received_at=self._clock())
        except Exception as failure:            # noqa: BLE001 -- reported
            # THE LAST GOOD READING IS KEPT AND MARKED, rather than replaced
            # by nothing. What it showed was true once, and saying when is more
            # useful than an empty screen -- as long as the view says so.
            self.failures += 1
            self.snapshot = Snapshot(self.snapshot.document,
                                     received_at=self.snapshot.received_at,
                                     connected=False,
                                     failure=_named(failure),
                                     published_at=self.snapshot.published_at)
            return self.snapshot
        self.snapshot = taken
        return self.snapshot

    def run(self, *, ticks, render=None, stream=sys.stdout):
        """Bounded by a tick count so a test drives it and a person can stop
        it."""
        render = render or render_list
        for tick in range(ticks):
            self.refresh()
            for line in render(self.snapshot, now=self._clock(),
                               wall_now=self._wall(),
                               stale_seconds=stale_after(self._interval)):
                print(line, file=stream)
            # NO SLEEP AFTER THE LAST TICK. Waiting an interval to then exit
            # is time an operator spends for nothing; the sleep exists to pace
            # the NEXT read, and after the last one there is no next read.
            if tick + 1 < ticks:
                self._sleep(self._interval)
        return self.snapshot


def _source_from(place):
    """Snapshots from a file the operator names, re-read each tick.

    A FILE IS THE WHOLE ADAPTER. `tools/job_manager.py ... status` already emits
    this document; pointing the viewer at what it wrote keeps this program's
    verb list at `read` and means no store handle, no factory and no second
    reader exists here at all.
    """
    class PublishedBytes(bytes):
        pass

    def read():
        with open(place, "rb") as handle:
            source = PublishedBytes(handle.read(MAX_SNAPSHOT_BYTES + 1))
            source.published_at = os.fstat(handle.fileno()).st_mtime
            return source
    return read


def main(argv=None, *, stream=sys.stdout):
    parser = argparse.ArgumentParser(
        prog="job_viewer",
        description="Read-only view of submitted Jobs. Performs no act.")
    parser.add_argument("--status", required=True,
                        help="path to a status document written by "
                             "`job_manager ... status`")
    parser.add_argument("--job", default=None,
                        help="show one Job in detail")
    parser.add_argument("--interval", type=float, default=POLL_SECONDS,
                        help="seconds between bounded refreshes; finite and "
                             "greater than zero")
    parser.add_argument("--stage", default=None,
                        help="with --job and --artifact, the stage whose "
                             "published artifact to read")
    parser.add_argument("--artifact", default=None,
                        help="the output_name of an artifact THIS SNAPSHOT "
                             "publishes; the locator comes from the document, "
                             "never from this operand")
    parser.add_argument("--ticks", type=int, default=1,
                        help="number of bounded refreshes; the default reads "
                             "once and exits")
    taken = parser.parse_args(argv)
    try:
        viewer = JobViewer(_source_from(taken.status),
                           interval=checked_interval(taken.interval))
        if taken.artifact is not None:
            return _drilled(viewer, taken, stream)
        render = (render_list if taken.job is None
                  else (lambda snapshot, *, now, wall_now=None,
                               stale_seconds=None:
                        render_detail(snapshot, taken.job, now=now,
                                      wall_now=wall_now,
                                      stale_seconds=stale_seconds)))
        viewer.run(ticks=max(1, taken.ticks), render=render, stream=stream)
    except ViewerRefusal as refusal:
        print("refused: " + str(refusal), file=stream)
        return 2
    return 0


def _drilled(viewer, taken, stream):
    """ONE bounded read of one artifact this snapshot publishes.

    It is a one-shot, not a tail: the view reads the document once, selects by
    explicit identity, and shows a bounded amount. There is no idle log
    following here and no second refresh.
    """
    if taken.job is None or taken.stage is None:
        print("refused: --artifact needs --job and --stage, because an "
              "artifact is selected by identity out of the snapshot rather "
              "than by a path", file=stream)
        return 2
    viewer.refresh()
    if not viewer.snapshot.connected:
        print("refused: this snapshot could not be read ("
              + str(viewer.snapshot.failure) + ")", file=stream)
        return 2
    artifact = select_artifact(viewer.snapshot, taken.job, taken.stage,
                               taken.artifact)
    # THE SAME CONFIGURED THRESHOLD THE LIST AND DETAIL VIEWS USE. Review
    # claim168257 [P2]: this called `_banner` without it, so a 3 s-old
    # observation was fresh in the Job view and STALE in its artifact view at
    # `--interval 5`. One document cannot be two ages.
    print(_banner(viewer.snapshot, viewer._clock(),
                  wall_now=viewer._wall(),
                  stale_seconds=stale_after(viewer._interval)), file=stream)
    print("ARTIFACT " + str(artifact.get("output_name")) + "   "
          + str(artifact.get("bytes") if artifact.get("bytes") is not None
                else UNKNOWN) + " bytes   "
          + str(artifact.get("content_digest") or UNKNOWN), file=stream)
    print(read_locator(artifact), file=stream)
    return 0


if __name__ == "__main__":                                  # pragma: no cover
    sys.exit(main())
