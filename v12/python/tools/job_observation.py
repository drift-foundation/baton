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
    return any(age is None or not math.isfinite(age) or age < 0 or age >= STALE_SECONDS for age in ages)


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
        seconds = _instant(finish) - _instant(started)
        return seconds if math.isfinite(seconds) and seconds >= 0 else None
    except (ValueError, TypeError, OverflowError):
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


def job_age(job, observed_at):
    control = job.get("control") if type(job.get("control")) is dict else {}
    held = control.get("job") if type(control.get("job")) is dict else {}
    origin = job.get("created_at") or held.get("origin")
    return _duration(_elapsed(origin, None, observed_at))


def stage_timing(stage, job, observed_at):
    """Interpret only attributed process facts and original admitted deadlines."""
    state = stage.get("state")
    never = (state in HELD_STATES and not stage.get("runtime") and not stage.get("exchange")
             and not stage.get("receipts")
             and not any(one.get("ended_at") for one in stage.get("episodes") or [])
             and (not stage.get("attempt_id") or state == "blocked"))
    result = {"running": "not started" if never else UNKNOWN, "running_seconds": None,
              "started_at": None, "ended_at": None, "scope": "provider-process",
              "job_age": job_age(job or {}, observed_at), "deadlines": [],
              "limiting": [], "remaining_seconds": None, "complete": False,
              "timeout": "timeout unknown", "observed_at": observed_at}
    try:
        clock = _instant(observed_at)
    except (ValueError, TypeError, OverflowError):
        return result
    exchange = stage.get("exchange") if type(stage.get("exchange")) is dict else {}
    invocation = exchange.get("invocation")
    command = exchange.get("command") if type(exchange.get("command")) is dict else {}
    provider = None
    if type(invocation) is dict and stage.get("attempt_id") and invocation.get("attempt_id") == stage["attempt_id"] and invocation.get("scope") == "provider-process" and invocation.get("operation") == "work" and invocation.get("command_digest") and invocation.get("command_digest") == command.get("command_digest") and invocation.get("sequence_id") == command.get("sequence_id"):
        try:
            start = _instant(invocation.get("started_at"))
            deadline = _instant(invocation.get("deadline_at"))
            end = None if invocation.get("ended_at") is None else _instant(invocation["ended_at"])
            if start > clock or deadline < start or (end is not None and not start <= end <= clock):
                raise ValueError("invalid invocation chronology")
            if end is not None or state not in TERMINAL_STATES:
                seconds = (clock if end is None else end) - start
                result.update(running=_duration(seconds), running_seconds=seconds,
                              started_at=invocation["started_at"], ended_at=invocation.get("ended_at"))
            # Once this process ended, its deadline no longer limits the stage.
            provider = {"origin": invocation["started_at"], "deadline_at": invocation["deadline_at"]} if end is None else {}
        except (ValueError, TypeError, OverflowError):
            pass
    if state in TERMINAL_STATES:
        result["timeout"] = "timeout not applicable (stage ended)"
        return result
    control = (job or {}).get("control")
    trusted = False
    if type(control) is dict and control.get("timing") == "trusted":
        try:
            age = clock - _instant(control.get("observed_at"))
            trusted = 0 <= age < STALE_SECONDS
        except (ValueError, TypeError, OverflowError):
            pass
    control = control if trusted else {}
    stages = control.get("stages") if type(control.get("stages")) is list else []
    stage_control = next((one for one in stages if type(one) is dict and one.get("stage_id") == stage.get("stage_id")), {})
    missing = []
    limits = [("Job", control.get("job"))]
    if not never:
        limits.append(("stage", stage_control))
        if provider != {}:
            limits.append(("provider", provider))
    for name, held in limits:
        try:
            origin = _instant(held.get("origin"))
            deadline = _instant(held.get("deadline_at"))
            if origin > clock or deadline < origin:
                raise ValueError("invalid deadline chronology")
        except (AttributeError, ValueError, TypeError, OverflowError):
            missing.append(name)
            continue
        result["deadlines"].append({"cause": name, "deadline_at": held["deadline_at"],
                                    "remaining_seconds": max(0.0, deadline - clock),
                                    "reached": deadline <= clock})
    if result["deadlines"]:
        first = min(_instant(one["deadline_at"]) for one in result["deadlines"])
        names = [one["cause"] for one in result["deadlines"] if _instant(one["deadline_at"]) == first]
        remaining = max(0.0, first - clock)
        result.update(limiting=names, remaining_seconds=remaining, complete=not missing)
        label = "/".join(names)
        result["timeout"] = (label + " deadline reached; cessation unconfirmed" if first <= clock
                             else label + " timeout in " + _duration(remaining))
        if missing:
            result["timeout"] += "; " + "/".join(missing) + " timing unknown (earliest known only)"
    return result


def _stage_line(stage, observed_at, job=None):
    episode = _live_episode(stage)
    started = (episode or {}).get("opened_at")
    ended = (episode or {}).get("ended_at")
    state = stage.get("state")
    state = state if state in _STATUS_STAGE_STATES else UNKNOWN
    timing = stage_timing(stage, job, observed_at)
    held = {
        "timing": timing,
        "running": timing["running"],
        "timeout": timing["timeout"],
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
        "elapsed": timing["running"],
        "started_at": timing["started_at"] or UNKNOWN,
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


# W385424: THE WORKER'S OWN DECLARED ENDING, as the diagnostic producer
# publishes it. Every name and value below is mirrored BY VALUE from
# `baton_v12.worker_manager.failure_cause`, for the reason this whole module
# imports nothing: it is the shared interpretation of a document, and a
# dependency on the producer would make it a reader of its own subject.
# `tests/tools/test_job_observation.py` holds the mirror against the owner.
#
# A DECLARATION IS NOT A CESSATION, AND THIS RENDERING SAYS SO IN WORDS. It
# reports what the worker DECLARED and what this manager SEALED of it; it
# never says a container died, a candidate is good, verification passed or
# anybody reviewed anything. The exchange fault and the manager's own
# cancellation facts keep their place ahead of it and are not replaced.
_DECLARATION_MEMBER = "worker_declaration"
# ONLY `unable` SPEAKS HERE. `cancelled` is the manager's own act and its
# facts are reported by the cancellation axis; `completed` and `plan-rejected`
# are not failures and have no business explaining one.
_DECLARED_UNABLE = "unable"
_DECLARED_ENDINGS = {
    "provider-failed": "the provider did not finish",
    "verification-failed": "its own verification command failed",
    "no-candidate": "it produced no candidate",
    "candidate": "it produced a candidate",
    "yielded": "it yielded a checkpoint",
}
_DECLARED_FAILURE_REASONS = {
    "timeout": "provider timed out",
    "start-error": "provider would not start",
    "api-error": "provider reported an api error",
    "unclassified": "provider failure unclassified",
}
_DECLARED_BOUND_SOURCES = ("job-default", "job-selected", "unstated",
                           "worker-default")
# The widest a declared provider bound or exit status may be before this view
# declines to render it. The producer already bounds both; this is what a
# CONSUMER must survive, exactly as MAX_ACTIVITY_BYTES is.
MAX_DECLARED_SECONDS = 7 * 24 * 60 * 60
DECLARED_STATUS_RANGE = (-256, 65535)


def _declared_fact(held, name):
    """One wrapped producer leaf as its value, or `None`.

    THE ONE SHAPE, READ THE WAY ITS OWNER WRITES IT: `{"known": true,
    "value": ...}` or `{"known": false, ...}`. A bare scalar, a missing
    member or a non-boolean `known` is not an established fact and answers
    `None` -- this view never reads an unknown as a known.
    """
    if type(held) is not dict:
        return None
    wrapper = held.get(name)
    if type(wrapper) is not dict or wrapper.get("known") is not True:
        return None
    return wrapper.get("value")


def _declared_word(held, name, owned):
    value = _declared_fact(held, name)
    return value if type(value) is str and value in owned else None


def _declared_number(held, name, low, high):
    value = _declared_fact(held, name)
    if type(value) is not int or type(value) is bool or not low <= value <= high:
        return None
    return value


def _declared_ending(stage):
    """What the worker said about its own ending, in bounded words, or `None`.

    `None` keeps `cause unknown` exactly as it was: no frozen result, a
    disposition this view does not speak for, evidence that did not bind, or
    a producer that carries no declaration at all are all "nobody established
    this", and inventing a sentence for them is the thing this model refuses
    everywhere else.
    """
    diagnostic = stage.get("attempt_diagnostics")
    if type(diagnostic) is not dict:
        return None
    held = diagnostic.get(_DECLARATION_MEMBER)
    if _declared_fact(held, "disposition") != _DECLARED_UNABLE:
        return None
    said = "worker declared unable"
    ending = _declared_word(held, "declared_ending", _DECLARED_ENDINGS)
    if ending is None:
        return said + "; its declared ending is unknown"
    said = said + ": " + _DECLARED_ENDINGS[ending]
    reason = _declared_word(held, "failure_reason", _DECLARED_FAILURE_REASONS)
    if reason is not None:
        said = said + " (" + _DECLARED_FAILURE_REASONS[reason] + ")"
    bound = _declared_number(held, "seconds_bound", 1, MAX_DECLARED_SECONDS)
    if bound is not None:
        source = _declared_word(held, "seconds_bound_source",
                                _DECLARED_BOUND_SOURCES)
        said = (said + " at a " + _duration(bound) + " provider bound"
                + ("" if source is None else " (" + source + ")"))
    attempted = _declared_fact(held, "verification_attempted")
    if attempted is False:
        return said + "; verification not attempted"
    if attempted is True:
        status = _declared_number(held, "verification_status",
                                  DECLARED_STATUS_RANGE[0],
                                  DECLARED_STATUS_RANGE[1])
        return (said + "; verification "
                + ("status unknown" if status is None
                   else "ended " + str(status)))
    return said + "; whether verification ran is unknown"


def _reason(stage, state):
    if state == "exceptional":
        exchange = stage.get("exchange")
        terminal = exchange.get("terminal") if type(exchange) is dict else None
        fault = terminal.get("fault_code") if type(terminal) is dict and terminal.get("ending") == "faulted" else None
        # W385424: THE WORKER'S DECLARATION REPLACES `cause unknown` AND
        # NOTHING ELSE. A recorded fault code and a role-adapter failure are
        # facts other owners established about this ending; they keep their
        # place and the declaration is reported after them.
        declared = _declared_ending(stage)
        detail = fault + " fault; " if fault in _STATUS_FAULT_CODES else ""
        detail = detail + (declared if declared is not None else "cause unknown")
        adapter = terminal.get("adapter_failure") if type(terminal) is dict else None
        if fault == "agent" and type(adapter) is dict and adapter.get("component") == "role-adapter" and adapter.get("code") in _STATUS_ADAPTER_CODES:
            detail = "agent fault; " + adapter["code"] + ("" if declared is None else "; " + declared)
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
