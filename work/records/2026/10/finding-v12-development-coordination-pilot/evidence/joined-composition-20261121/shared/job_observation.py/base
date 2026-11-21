"""Pure shared interpretation of existing job-status/9 facts (W385263).

No stores, collectors, provider calls or new wire schema. Both operator views
use these functions; a future TUI can consume stage_view and job_outcome.
"""
import datetime
import json
import math

UNKNOWN = "unknown"
TERMINAL_STATES = ("changes-requested", "completed", "exceptional")
OPERATOR_ACTION_STATES = ("changes-requested",)
HELD_STATES = ("blocked", "queued")
STALE_SECONDS = 15.0


def stale_ages(*ages):
    """Absent/invalid required age is unknown, never fresh."""
    return any(age is None or not math.isfinite(age) or age >= STALE_SECONDS for age in ages)


def observation_age(observed_at, now):
    try:
        return now - _instant(observed_at)
    except (ValueError, TypeError, OverflowError):
        return None


_STATUS_STAGE_STATES = ("blocked", "queued", "offered", "claimed", "starting",
                        "waiting", "running", "reviewing", "integrating", "answering",
                        "changes-requested", "completed", "exceptional")
_STATUS_ADAPTER_CODES = ("declaration-set-invalid", "declaration-name-unsupported",
                         "role-output-missing", "other-role-output-required")
_STATUS_FAULT_CODES = ("agent", "answer", "entitlement", "exchange", "input",
                       "launch", "output", "protocol", "replay", "session")


def _status_text(value):
    # Identifiers remain one line even in a damaged publication.
    return json.dumps(value if type(value) is str and value else "unknown",
                      ensure_ascii=True)[1:-1]


def _job_outcome(job):
    states = [stage.get("state") for stage in (job.get("stages") or [])]
    if "exceptional" in states:
        return "FAILED"
    if type(job.get("cancellation")) is dict:
        return "CANCELLATION REQUESTED"
    if not states or any(state not in _STATUS_STAGE_STATES for state in states):
        return "UNKNOWN"
    if "changes-requested" in states:
        return "CHANGES REQUESTED"
    if all(state == "completed" for state in states):
        return "COMPLETED"
    if any(state in ("offered", "claimed", "starting", "waiting", "running",
                     "reviewing", "integrating", "answering") for state in states):
        return "IN PROGRESS"
    if "queued" in states:
        return "QUEUED"
    return "BLOCKED"


def _elapsed(started, ended, observed_at):
    """Elapsed time FROM KNOWN SOURCE TIMES ONLY.

    The wall clock is not a source time. A stage whose start nobody recorded
    has an unknown elapsed, and saying `unknown` is the correct answer -- the
    alternative is measuring how long THIS PROGRAM has been looking and
    printing it as how long the JOB has been running.
    """
    finish = ended or observed_at
    if not started or not finish:
        return None
    try:
        return max(0.0, _instant(finish) - _instant(started))
    except ValueError:
        return None


def _instant(value):
    """One recorded instant, parsed strictly."""
    if type(value) is not str:
        raise ValueError("not an instant")
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    instant = datetime.datetime.fromisoformat(text)
    if instant.tzinfo is None:
        instant = instant.replace(tzinfo=datetime.timezone.utc)
    return instant.timestamp()


def _duration(seconds):
    if seconds is None:
        return UNKNOWN
    seconds = int(seconds)
    if seconds < 60:
        return str(seconds) + "s"
    if seconds < 3600:
        return str(seconds // 60) + "m" + str(seconds % 60).zfill(2) + "s"
    return str(seconds // 3600) + "h" + str((seconds % 3600) // 60).zfill(2) + "m"


# HOW A BYTE COUNT IS SPELLED. Whole units only: an operator reading this is
# asking "is it moving", and a third decimal place answers a question nobody
# asked while making two figures harder to compare at a glance.
_ACTIVITY_UNITS = (("GiB", 1 << 30), ("MiB", 1 << 20), ("KiB", 1 << 10))


# THE DOMAIN AN ACTIVITY COUNT MAY BE IN, and it is the producer's own.
#
# REVIEW 2026-09-15T14-42-20Z [R2]: this had no ceiling, and a status document
# carrying `bytes_observed: 10**400` -- valid JSON, far inside the 4 MiB input
# bound -- reached a float division and raised `OverflowError`. That escaped
# `refresh`'s last-good-snapshot handler and `main`, which catches only
# `ViewerRefusal`, so the ordinary command could die on a document the previous
# constant-`unknown` rendering displayed without complaint.
#
# THE BOUND IS CHECKED BEFORE ANY CONVERSION, because the conversion is what
# fails. A count outside it is `unknown` -- this view refuses to render a number
# it cannot hold, exactly as it refuses every other value it cannot account for.
# The trusted producer's own parser already excludes such a value, so this is
# about malformed CONSUMER input rather than an emission anybody has seen.
MAX_ACTIVITY_BYTES = 2 ** 53 - 1

# How much of a recorded instant may reach a line. The document is the
# manager's, but a malformed one must not decide this program's line width.
MAX_INSTANT_TEXT = 32


def _bytes_seen(count):
    for unit, size in _ACTIVITY_UNITS:
        if count >= size:
            return "{:.2f} {}".format(count / size, unit)
    return str(count) + " B"


def _activity(stage, state, observed_at):
    """W61599's count, rendered with the ONE distinction that matters.

    THE INSTANT IS THE MANAGER'S RECEIPT TIME, NOT THE PROVIDER'S. Owner ruling
    M174788 is explicit that an update admitted while the operation was live may
    ARRIVE AFTER COMPLETION, so the instant says when this manager recorded an
    observation and never that the provider is still working.

    SO A RELATIVE AGE IS ONLY HONEST WHILE THE STAGE IS LIVE. "4s ago" beside
    `completed` invites an operator to read a finished attempt as a running one,
    and it gets WORSE with time: the apparent freshness improves as the clock
    moves while nothing is running. A terminal stage therefore shows the
    absolute instant and the word `last`, which cannot be misread as now.

    Known zero is an observed empty count, not an absent observation.
    The activity must name the stage current attempt; foreign bytes are unknown.

    NOTHING BRANCHES ON THIS. It is a diagnostic under approver ruling M61707:
    a count is not proof of useful work, a quiet model call leaves it unchanged,
    and no refresh, refusal, ordering or selection in this program reads it.
    """
    runtime = stage.get("runtime") if type(stage.get("runtime")) is dict else {}
    held = runtime.get("activity") if type(runtime.get("activity")) is dict \
        else {}
    if not stage.get("attempt_id") or held.get("attempt_id") != stage.get("attempt_id"):
        return UNKNOWN, None
    count = held.get("bytes_observed")
    if type(count) is not int or type(count) is bool \
            or not 0 <= count <= MAX_ACTIVITY_BYTES:
        return UNKNOWN, None
    seen = _bytes_seen(count)
    instant = held.get("observed_at")
    if state in TERMINAL_STATES:
        # HISTORICAL, AND SAID SO. No age, because there is nothing for an age
        # to be measured against that an operator should read as liveness.
        return seen, "last at " + (instant[:MAX_INSTANT_TEXT]
                                   if type(instant) is str else UNKNOWN)
    age = _elapsed(instant, None, observed_at)
    return seen, ("observed " + _duration(age) + " ago" if age is not None
                  else "observed at " + UNKNOWN)


def _live_episode(stage):
    """The CURRENT episode, or None. A stage between an ending and its
    replacement genuinely has none, and naming the ended one would report a
    finished attempt as the live one."""
    live = stage.get("episode")
    if live is None:
        return None
    for one in stage.get("episodes") or []:
        if one.get("episode") == live:
            return one
    return None


def _stage_line(stage, observed_at):
    episode = _live_episode(stage)
    started = (episode or {}).get("opened_at")
    ended = (episode or {}).get("ended_at")
    state = stage.get("state")
    state = state if state in _STATUS_STAGE_STATES else UNKNOWN
    held = {
        "stage_id": stage.get("stage_id") or UNKNOWN,
        "kind": stage.get("kind") or UNKNOWN,
        "state": state,
        # THE EXACT IDENTITIES WHEN THEY ARE KNOWN, and `unknown` when they are
        # not. An operator chasing a stuck Job needs the attempt id to give to
        # anybody else, and a blank space is not an answer.
        "work_id": stage.get("work_id") or UNKNOWN,
        "attempt_id": stage.get("attempt_id") or UNKNOWN,
        "offer_id": stage.get("offer_id") or UNKNOWN,
        "episode": stage.get("episode") if stage.get("episode") is not None
                   else UNKNOWN,
        "elapsed": _duration(_elapsed(started, ended, observed_at)),
        "started_at": started or UNKNOWN,
        # ACTIVITY COMES FROM THE SNAPSHOT AND FROM NOWHERE ELSE. W61599's
        # producer puts it on the attempt, `delegation` observes it and
        # `projection` publishes it at `runtime.activity`; this reads that and
        # never infers liveness from an empty stream or from the fact that
        # polling returned. See `_activity`.
        "activity": _activity(stage, state, observed_at)[0],
        # R1, review 2026-09-15T14-42-20Z: THE TIMING IS ITS OWN LINE.
        #
        # The count and the instant together are wider than the ordinary
        # 100-column list, and the whole-line cut took the end of the timestamp
        # AND the entire stage id with it -- on ordinary valid counts, in the
        # renderer the plain CLI uses, which offers no width operand. An
        # operator chasing a stuck Job needs that identity to give to somebody
        # else, so the fixed-width columns keep it and the variable-width fact
        # moves to a continuation line, exactly as `reason` already does.
        "activity_when": _activity(stage, state, observed_at)[1],
        "reason": _reason(stage, state),
        "operation": reported_operation(stage),
        "corrections": stage.get("corrections", 0),
    }
    # REVIEW claim168071 [P2]: `projection.status` supplies these and the view
    # ignored them, so a document carrying a known worker and assignment
    # rendered neither. An operator asking "which worker is this on" was being
    # shown an absence the document did not report.
    runtime = stage.get("runtime") if type(stage.get("runtime")) is dict else {}
    assignment = (runtime.get("assignment")
                  if type(runtime.get("assignment")) is dict else {})
    held.update({
        "runtime_id": runtime.get("runtime_id") or UNKNOWN,
        "execution_runtime": runtime.get("execution_runtime") or UNKNOWN,
        "assignment_work": assignment.get("work_ref") or UNKNOWN,
        "assignment_participant": assignment.get("participant") or UNKNOWN,
        "assignment_generation": (assignment.get("generation")
                                  if assignment.get("generation") is not None
                                  else UNKNOWN),
    })
    held.update(_allocated(stage.get("allocation")))
    return held


# THE SCHEDULER'S OWN COLUMNS. Review claim168169 [P2]: `_allocation` looked
# for `allocation_id`/`name`/`root`/`capacity_id`, none of which the scheduler
# publishes -- so a really reserved worker displayed `unknown`, and my fixture
# invented an `allocation_id` and therefore passed while missing the actual
# shape. These names are `stage_allocations`' own.
#
# AND THE WORKER IS NOT THE ASSIGNMENT. A stage can be reserved on a worker
# before any runtime exists, so the scheduler's reservation and the runtime's
# fixed assignment are different facts at different times and are shown
# separately rather than folded into one line.
ALLOCATION_FIELDS = (("allocation_assignment", "assignment_id"),
                     ("allocation_worker", "worker_id"),
                     ("allocation_participant", "participant"),
                     ("allocation_lane", "lane"),
                     ("allocation_generation", "generation"),
                     ("allocation_state", "allocation_state"),
                     ("allocation_selection", "selection_outcome"))


def _allocated(held):
    taken = {}
    for label, member in ALLOCATION_FIELDS:
        value = held.get(member) if type(held) is dict else None
        taken[label] = UNKNOWN if value is None or value == "" else str(value)
    return taken


def _reason(stage, state):
    if state == "exceptional":
        exchange = stage.get("exchange")
        terminal = exchange.get("terminal") if type(exchange) is dict else None
        fault = terminal.get("fault_code") if type(terminal) is dict and terminal.get("ending") == "faulted" else None
        detail = fault + " fault; cause unknown" if fault in _STATUS_FAULT_CODES else "cause unknown"
        adapter = terminal.get("adapter_failure") if type(terminal) is dict else None
        if fault == "agent" and type(adapter) is dict and adapter.get("component") == "role-adapter" and adapter.get("code") in _STATUS_ADAPTER_CODES:
            detail = "agent fault; " + adapter["code"]
        return "failed: stage ended exceptionally; " + detail
    if state in OPERATOR_ACTION_STATES:
        return "operator action: changes requested"
    gates = stage.get("gates")
    closed = [one for one in gates if isinstance(one, dict) and one.get("open") is False] if type(gates) is list else []
    if closed:
        named = ", ".join(_status_text(one.get("stage_id")) + " (" + _status_text(one.get("state")) + ")" for one in closed[:3])
        more = "" if len(closed) <= 3 else " and " + str(len(closed) - 3) + " more"
        return "held: waiting on " + named + more
    if state == "blocked":
        return "held: blocker unknown"
    if state in HELD_STATES:
        return "held: no attempt in progress"
    return ""


def reported_operation(stage):
    exchange = stage.get("exchange")
    states = exchange.get("states") if type(exchange) is dict else None
    if type(states) is not list:
        return UNKNOWN
    reported = [one for one in states if type(one) is dict and one.get("operation") in ("describe", "work") and one.get("state") in ("dispatched", "answered", "faulted")]
    if not reported:
        return UNKNOWN
    # Report the ordered operation facts, not a guessed current provider tool.
    return ", ".join(one["operation"] + " " + one["state"] for one in reported) + " (reported; attempt association unverified)"


stage_view = _stage_line
job_outcome = _job_outcome
