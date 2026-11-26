"""Shared, read-only interpretation of /9 execution and /10 MANUAL lifecycle facts."""
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
                        "changes-requested", "completed", "exceptional", "awaiting-answer", "answered")
_STATUS_ADAPTER_CODES = ("declaration-set-invalid", "declaration-name-unsupported",
                         "role-output-missing", "other-role-output-required")
_STATUS_FAULT_CODES = ("agent", "answer", "entitlement", "exchange", "input",
                       "launch", "output", "protocol", "replay", "session")


def _status_text(value):
    # Identifiers remain one line even in a damaged publication.
    return json.dumps(value if type(value) is str and value else "unknown",
                      ensure_ascii=True)[1:-1]


def lifecycle_problem(job):
    if "mode" not in job and "lifecycle" not in job:
        return None
    if job.get("mode") != "MANUAL" or job.get("lifecycle") not in ("open", "closed"):
        return "the published Job mode or owner lifecycle is unknown"
    if not isinstance(job.get("stages"), list):
        return "a MANUAL Job must publish its planned phases"
    return None


def _job_headline(job, phases):
    stages = _rows(job.get("stages"))
    states = [phase["state"] for phase in phases]
    manual_open = job.get("mode") == "MANUAL" and job.get("lifecycle") == "open"
    if job.get("mode") == "MANUAL" and job.get("lifecycle") == "closed":
        finished = states.count("completed")
        failed = states.count("exceptional")
        unselected = sum(not stage.get("selected_at") and state in HELD_STATES for stage, state in zip(stages, states))
        summary = f"{finished} finished · {failed} failed · {unselected} never selected"
        unknown = len(states) - finished - failed - unselected
        return "CLOSED", summary + (f" · {unknown} unknown" if unknown else "")
    if any(phase["state"] == "exceptional" and not (phase["live_attempt"] or {}).get("stop")
           for phase in phases):
        return "FAILED", ""
    for stage, phase in zip(stages, phases):
        hold = _owner_hold(stage)
        if hold and phase["live_attempt"] and phase["state"] not in ("completed", "changes-requested") and not _owner_decision(stage, job):
            return "DECISION NEEDED", phase["stage_id"] + ": " + hold + "; owner action needed"
    if type(job.get("cancellation")) is dict:
        return "CANCELLATION REQUESTED", ""
    if manual_open and _mapping(job.get("budget")).get("expired") is True:
        return "BUDGET EXHAUSTED", "The Job wall budget has expired; further phase starts are refused."
    if any(phase["execution_position"] == "in progress" for phase in phases):
        return "IN PROGRESS", ""
    if any(phase["execution_position"] == "admitted" for phase in phases):
        return "ADMITTED", ""
    # W386395: NOTHING IS RUNNING OR ABOUT TO, and a review froze without a
    # usable report. Failure, an owner decision, cancellation, an expired
    # budget and genuine activity elsewhere have all been answered above.
    held_reasons = []
    for stage, phase in zip(stages, phases):
        if phase["execution_position"] == "held":
            sentence = held_review(stage, phase["state"])
            if sentence and sentence not in held_reasons:
                held_reasons.append(sentence)
    if held_reasons:
        return "BLOCKED", "; ".join(held_reasons)
    if manual_open and all(state in ("completed", "blocked", "queued") for state in states):
        if _externally_blocked(stages):
            return "BLOCKED", ""
        if not any(stage.get("selected_at") and state != "completed" for stage, state in zip(stages, states)):
            reason = ""
            if states and all(state == "completed" for state in states):
                reason = "The planned phase finished." if len(states) == 1 else f"All {len(states)} planned phases finished."
            return "AWAITING ASSIGNMENT", reason
    if any(state == "queued" and (not manual_open or stage.get("selected_at")) for stage, state in zip(stages, states)):
        return "QUEUED", ""
    if states and all(state == "completed" for state in states):
        # job-status/9 publishes neither a final Job outcome nor an act of
        # Job finalization. A completed *stage* establishes neither.
        return "UNKNOWN", "The final Job outcome has not been recorded."
    if "changes-requested" in states:
        return "CHANGES REQUESTED", ""
    if "awaiting-answer" in states:
        return "WAITING FOR AN ANSWER", ""
    if "answered" in states:
        return "ANSWERED — HELD", ""
    if _externally_blocked(stages):
        return "BLOCKED", ""
    return "UNKNOWN", ""


def _externally_blocked(stages):
    """Follow closed gates backwards from external blockers to their dependents."""
    owned = {stage["stage_id"] for stage in stages if isinstance(stage.get("stage_id"), str) and stage["stage_id"]}
    if len(owned) != len(stages):
        return False
    dependents = {}
    pending = []
    unfinished = set()
    for stage in stages:
        if stage.get("state") == "completed":
            continue
        if stage.get("state") != "blocked":
            return False
        identity = stage["stage_id"]
        unfinished.add(identity)
        for gate in _rows(stage.get("gates")):
            dependency = gate.get("stage_id")
            if gate.get("open") is False and isinstance(dependency, str) and dependency:
                if dependency in owned:
                    dependents.setdefault(dependency, []).append(identity)
                else:
                    pending.append(identity)
    reached = set()
    while pending:
        identity = pending.pop()
        if identity not in reached:
            reached.add(identity)
            pending.extend(dependents.get(identity, ()))
    return bool(unfinished) and reached == unfinished


def _job_outcome(job):
    return job_view({}, job)["headline"]


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
    if type(stage.get("attempt_id")) is not str or not stage["attempt_id"] or held.get("attempt_id") != stage["attempt_id"]:
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
    for one in _rows(stage.get("episodes")):
        if one.get("episode") == live:
            return one
    return None


def job_age(job, observed_at):
    control = job.get("control") if type(job.get("control")) is dict else {}
    held = control.get("job") if type(control.get("job")) is dict else {}
    origin = job.get("created_at") or held.get("origin")
    return _duration(_elapsed(origin, None, observed_at))


# W385431: HOW A DURATION IS LABELLED, and the single distinction the label
# carries.
#
# THE DEFECT, measured on every shared surface: a provider invocation that had
# RECORDED ITS OWN END still printed `running 15s`. The worker runs its own
# verification command AFTER the provider process exits, so that figure is
# frozen while the stage is genuinely still open -- and the word beside it said
# two untrue things at once: that a provider turn was in progress, and that the
# number was current. It got worse with time, exactly as a relative activity
# age beside a terminal stage does.
#
# SO THE LABEL FOLLOWS THE INVOCATION AND NOTHING ELSE. `running` is said only
# while no ending is recorded; a recorded ending reads `provider ran`, past
# tense, naming the PROVIDER rather than the stage. Neither phrase says the
# stage or the Job ended, completed, succeeded or was accepted -- those are
# other owners' facts, and the state, timeout, reason and activity axes beside
# this one report them.
_INVOCATION_LABELS = {"active": "running ", "ended": "provider ran "}


def stage_timing(stage, job, observed_at):
    """Interpret only attributed process facts and original admitted deadlines.

    `running`/`running_seconds` are the MEASURE and `duration` is what a
    surface prints: an active invocation is `running 30s` and a recorded ended
    one is `provider ran 15s`, which is the same measure with an honest label.
    `duration_note` is the one sentence an ended invocation under a stage that
    has NOT ended owes an operator, and `None` everywhere else.
    """
    state = stage.get("state")
    # Preserve the existing control-limit selection. This predicate is not
    # evidence of non-admission or of execution never having started.
    held_without_timing = (state in HELD_STATES and not stage.get("runtime") and not stage.get("exchange")
                           and not stage.get("receipts")
                           and not any(one.get("ended_at") for one in _rows(stage.get("episodes")))
                           and (not stage.get("attempt_id") or state == "blocked"))
    result = {"running": UNKNOWN, "running_seconds": None,
              "started_at": None, "ended_at": None, "scope": "provider-process",
              "job_age": job_age(job or {}, observed_at), "deadlines": [],
              "limiting": [], "remaining_seconds": None, "complete": False,
              "timeout": "timeout unknown", "observed_at": observed_at,
              # No invocation is attributed until one is, and an unattributed,
              # malformed, foreign-attempt or future invocation keeps the
              # qualification it already had rather than gaining a label that
              # would read as a measurement.
              "invocation": None, "invocation_valid": False, "duration_note": None,
              "duration": "duration unknown"}
    try:
        clock = _instant(observed_at)
    except (ValueError, TypeError, OverflowError):
        return result
    exchange = stage.get("exchange") if type(stage.get("exchange")) is dict else {}
    invocation = exchange.get("invocation")
    command = exchange.get("command") if type(exchange.get("command")) is dict else {}
    provider = None
    if type(invocation) is dict and type(stage.get("attempt_id")) is str and stage.get("attempt_id") and invocation.get("attempt_id") == stage["attempt_id"] and invocation.get("scope") == "provider-process" and invocation.get("operation") == "work" and type(invocation.get("command_digest")) is str and invocation.get("command_digest") and invocation.get("command_digest") == command.get("command_digest") and type(invocation.get("sequence_id")) is str and invocation.get("sequence_id") and invocation.get("sequence_id") == command.get("sequence_id"):
        try:
            start = _instant(invocation.get("started_at"))
            deadline = _instant(invocation.get("deadline_at"))
            end = None if invocation.get("ended_at") is None else _instant(invocation["ended_at"])
            if start > clock or deadline < start or (end is not None and not start <= end <= clock):
                raise ValueError("invalid invocation chronology")
            result.update(invocation_valid=True, started_at=invocation["started_at"])
            if end is not None or state not in TERMINAL_STATES:
                seconds = (clock if end is None else end) - start
                recorded = "active" if end is None else "ended"
                result.update(running=_duration(seconds), running_seconds=seconds,
                              started_at=invocation["started_at"], ended_at=invocation.get("ended_at"),
                              invocation=recorded,
                              duration=_INVOCATION_LABELS[recorded] + _duration(seconds))
                if recorded == "ended" and state not in TERMINAL_STATES:
                    # THE ONE CASE AN OPERATOR CANNOT READ OFF THE OTHER
                    # COLUMNS: the process ended and the stage did not, so the
                    # figure is frozen and the stage is still open. Said in
                    # words, because a non-terminal state beside a past-tense
                    # label is exactly the pair that invites "so which is it".
                    result["duration_note"] = ("provider invocation ended after "
                                               + _duration(seconds)
                                               + "; this stage has not ended")
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
    if not held_without_timing:
        limits.append(("stage", stage_control))
        if provider != {} and invocation is not None:
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
    stage = _mapping(stage)
    interpreted = _attempts(stage, job)
    state = stage.get("state")
    state = state if state in _STATUS_STAGE_STATES else UNKNOWN
    timing_stage = stage
    if interpreted["admission"] != "admitted":
        timing_stage = dict(stage, exchange=dict(_mapping(stage.get("exchange")), invocation=None))
    timing = stage_timing(timing_stage, job, observed_at)
    held = {
        "timing": timing,
        # THE MEASURE AND THE LABELLED LINE ARE TWO KEYS. `running` is the
        # bare figure for a caller that compares durations; `duration` is what
        # every shared surface PRINTS, and it is the only one of the two that
        # says whether the invocation is still in a turn. See
        # `_INVOCATION_LABELS`.
        "running": timing["running"],
        "duration": timing["duration"],
        "duration_note": timing["duration_note"],
        "invocation": timing["invocation"],
        "timeout": timing["timeout"],
        "stage_id": _status_text(stage.get("stage_id")),
        "kind": _status_text(stage.get("kind")),
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
        "reason": _reason(stage, state).removeprefix("failed: stage ended exceptionally; "),
        "operation": reported_operation(stage),
        "model_attribution": ((stage.get("runtime") or {}).get("model_attribution", "Requested: not selected (account default)")
                              if type(stage.get("runtime")) is dict else None),
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
    held.update(_allocated(interpreted["live_allocation"]))
    held.update(interpreted)
    held["dependencies"] = [_gate_text(gate) for gate in _rows(stage.get("gates"))]
    held["role"] = held["kind"]
    position = _position(stage, held)
    held["position"] = position + "; admission " + held["admission"]
    held["row_position"] = _row_position(position, stage, held, job)
    held["facts"] = _facts(stage, held, observed_at)
    if job and job.get("mode") == "MANUAL":
        if job.get("lifecycle") == "closed" and not stage.get("selected_at"):
            held["position"] = held["row_position"] = "never selected; Job closed"
        elif state == "queued":
            if _mapping(job.get("budget")).get("expired") is True:
                held["position"] = held["row_position"] = "admission fenced; Job wall budget exhausted"
            else:
                held["facts"].append("Selection recorded; waiting for admission" if stage.get("selected_at") else "Ready for explicit start")
        phase_cancellation = _mapping(stage.get("execution_cancellation"))
        if phase_cancellation:
            held["facts"].append("Phase cancellation: " + _status_text(phase_cancellation.get("trigger")))

        if state == "completed":
            held["facts"].append("Phase COMPLETED")
        if isinstance(stage.get("result"), dict):
            result = stage["result"]
            decision = _owner_decision(stage, job)
            if decision:
                actor = _mapping(decision.get("actor"))
                frozen = _mapping(decision.get("frozen"))
                held["reason"] = "Worker hold at freeze: " + _status_text(decision.get("held_cause"))
                held["facts"].extend([
                    "Owner decision: " + _status_text(decision.get("outcome")) + " by " + _status_text(actor.get("participant"))
                    + " (" + _status_text(actor.get("principal")) + ") at " + _status_text(decision.get("recorded_at")),
                    "Frozen result: " + _status_text(frozen.get("result_id")) + " at " + _status_text(frozen.get("frozen_at")),
                    "Frozen manifest: " + _status_text(frozen.get("manifest_digest"))])
            if result.get("reason"):
                held["facts"].append("Settlement reason: " + _status_text(result["reason"]))
            if result.get("attempt_id"):
                held["facts"].append("Retained result for attempt " + _status_text(result["attempt_id"]))
            if result.get("locator"):
                held["facts"].append("Retained findings: " + _status_text(result["locator"]))
    if held["execution_position"] == "admitted":
        held["facts"].append("reported phase state: " + state)
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
    diagnostic = _diagnostic(stage, stage.get("attempt_id"))
    if not diagnostic:
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


def _gate_text(gate):
    """One closed gate, named by the fact that actually decides it.

    W385625 (review note M1): the gate list carries TWO document shapes and
    this reader only knew one. A `stage.dependency-gate` is decided by another
    stage's state, so it is named by that stage and that state. A
    `stage.recovery-gate` has no predecessor stage and no state -- what it
    waits on is a validated retained-candidate execution handoff -- so
    reading it through the dependency members rendered `unknown (unknown)`,
    which told an operator nothing while the status document beside it carried
    the truthful reason all along. A recovery gate is named by its Job and its
    own closed reason.
    """
    if gate.get("reason") is not None and gate.get("stage_id") is None:
        return (_status_text(gate.get("job_id")) + " (" +
                _status_text(gate.get("reason")) + ")")
    return (_status_text(gate.get("stage_id")) + " (" +
            _status_text(gate.get("state")) + ")")


def _owner_decision(stage, job):
    if job.get("mode") == "MANUAL" and stage.get("state") in ("completed", "exceptional"):
        return _mapping(_mapping(stage.get("result")).get("owner_decision"))
    return {}


def _owner_hold(stage):
    hold = _mapping(stage.get("runtime")).get("model_attribution_hold")
    if hold in ("model-attribution-missing", "model-attribution-conflicting", "model-attribution-invalid",
                "model-attribution-faulted", "model-attribution-incomplete", "model-attribution-rerouted",
                "model-attribution-unqualified-build", "context-label-missing", "context-label-mismatch",
                "launched-image-refused", "launched-image-missing", "launched-image-invalid", "launched-image-mismatch"):
        return hold
    return None


def review_report_sentence(observation):
    """Unknown evidence never supplies a sentence; historical evidence is classified upstream."""
    if not isinstance(observation, dict) or observation.get("known") is not True:
        return ""
    state = observation.get("value")
    if state in ("missing", "empty", "malformed"):
        return "Review held: review report " + state
    if state == "unclassified":
        return "Review held: no usable report"
    return ""


def held_review(stage, state):
    """The sentence for a review whose current attempt froze without a usable
    report, or `""`. W386395.

    A review stage reads `answering` both while its worker is still working --
    verification may run after the provider turn -- and after the attempt has
    frozen its result. Only the second is a hold, and only the attempt-bound
    evidence says which: the worker's declaration for THIS attempt must carry a
    known frozen result (`frozen_at`) and a known report state the sentence
    owner classifies. Unknown, unbound or `not-read` evidence never makes a
    phase held.
    """
    if stage.get("kind") != "review" or state != "answering":
        return ""
    declared = _mapping(_diagnostic(stage, stage.get("attempt_id")).get(_DECLARATION_MEMBER))
    if not declared or _declared_fact(declared, "frozen_at") is None:
        return ""
    return review_report_sentence(declared.get("review_report"))


def _reason(stage, state):
    diagnostic = _diagnostic(stage, stage.get("attempt_id"))
    report = (review_report_sentence(_mapping(diagnostic.get("worker_declaration")).get("review_report"))
              if stage.get("kind") == "review" and state == "answering" else "")
    hold = _owner_hold(stage)
    if hold:
        return "held: " + hold + "; owner action needed" + ("; " + report if report else "")
    if report:
        return report
    if stage.get("kind") == "review" and state == "answering" and _declared_fact(
            _mapping(diagnostic.get("worker_declaration")), "review_report") == "not-read":
        return _declared_ending(stage) or ""
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
        named = ", ".join(_gate_text(one) for one in closed[:3])
        more = "" if len(closed) <= 3 else " and " + str(len(closed) - 3) + " more"
        return "held: waiting on " + named + more
    if state == "blocked":
        return "held: blocker unknown"
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


# A1: evidence belongs to an episode/attempt pair, never to a phase by proximity.
def _mapping(value):
    return value if type(value) is dict else {}


def _rows(value):
    return [row for row in value if type(row) is dict] if type(value) is list else []


def _diagnostic(stage, attempt):
    diagnostic = _mapping(stage.get("attempt_diagnostics"))
    if type(attempt) is not str or not attempt or diagnostic.get("attempt_id") != attempt or diagnostic.get("schema") != "baton.v12.attempt-failure-cause/1":
        return {}
    return diagnostic


def _stop_word(target, diagnostic):
    state = target.get("state")
    if state == "ceased":
        return "stopped"
    if state == "fenced-unstarted":
        return "cancelled before start"
    cause = _mapping(diagnostic.get("cause"))
    if _declared_fact(cause, "outcome") in ("ceased-absent", "ceased-quiescent", "held-attachment-unresolved"):
        return "stopped"
    if state in ("pending", "awaiting-offer-lapse", "ordered", "order-failed", "ending-in-progress", "held-unknown"):
        return "stopping (" + state + ")"
    return ""


def _attempts(stage, job):
    attempts = []
    live = None
    allocations = _rows(stage.get("allocations")) + [_mapping(stage.get("allocation"))]
    target_stage = stage.get("stage_id")
    cancellation = _mapping(job).get("cancellation")
    if _mapping(job).get("mode") == "MANUAL":
        execution = stage.get("execution_job_id")
        target_stage = execution + "/research" if type(execution) is str and execution and stage.get("kind") == "research" else None
        cancellation = stage.get("execution_cancellation")
    targets = _rows(_mapping(cancellation).get("targets")) if target_stage else []
    for row in _rows(stage.get("episodes")):
        number, identity = row.get("episode"), row.get("attempt_id")
        valid = type(number) is int and number > 0 and type(identity) is str and bool(identity)
        current = valid and type(stage.get("episode")) is int and number == stage.get("episode") and identity == stage.get("attempt_id")
        allocation = next((one for one in allocations if valid and type(one.get("episode")) is int and one.get("episode") == number and one.get("assignment_id") == identity), {})
        target = next((one for one in targets if valid and one.get("stage_id") == target_stage and type(one.get("episode")) is int and one.get("episode") == number and one.get("attempt_id") == identity), {})
        receipts = [one for one in _rows(stage.get("receipts")) if current and type(one.get("episode")) is int and one.get("episode") == number]
        offered = any(one.get("act") == "admit" and one.get("state") in ("performed", "adopted") and _mapping(one.get("detail")).get("canonical_state") == "committed" for one in receipts)
        claimed = any(one.get("act") == "claim" and _mapping(_mapping(one.get("detail")).get("result")).get("state") == "claimed" for one in receipts)
        admission = "admitted" if allocation or offered or claimed else UNKNOWN
        if target.get("state") == "retired-before-admission":
            admission = "not admitted"
        attempt = {"episode": number, "attempt_id": identity, "admission": admission,
                   "live": current, "allocation": allocation, "receipts": receipts,
                   "offered": offered, "ending": row.get("ended_state"), "ended_at": row.get("ended_at"),
                   "stop": _stop_word(target, _diagnostic(stage, identity) if current else {})}
        attempts.append(attempt)
        if current:
            live = attempt
    return {"attempts": attempts, "live_attempt": live,
            "admission": live["admission"] if live else UNKNOWN,
            "live_allocation": live["allocation"] if live else {},
            "attempt_count": sum(one["admission"] == "admitted" for one in attempts)}


_POSITIONS = {"offered": "admitted", "claimed": "admitted", "starting": "admitted", "waiting": "admitted",
              "running": "in progress", "reviewing": "in progress", "integrating": "in progress", "answering": "in progress",
              "awaiting-answer": "waiting for an answer", "answered": "answered — held",
              "changes-requested": "changes requested", "completed": "done", "exceptional": "failed"}


def _position(stage, held):
    state = stage.get("state")
    if state == "blocked":
        closed = [_gate_text(one) for one in _rows(stage.get("gates")) if one.get("open") is False]
        position = "planned — waiting on " + (", ".join(closed) or UNKNOWN)
    elif state == "queued":
        position = "ready"
    elif type(state) is str and state in _POSITIONS:
        position = _POSITIONS[state] if held["admission"] == "admitted" else "unknown (reported state: " + state + ")"
    else:
        position = UNKNOWN
    held["plan_position"] = position if state in HELD_STATES else UNKNOWN
    if held["live_attempt"] and state not in TERMINAL_STATES + HELD_STATES and _owner_hold(stage):
        position = _status_text(state) + " — held for owner"
    elif held["admission"] == "admitted" and held_review(stage, state):
        # W386395: a frozen review without a usable report is not progress.
        position = "held"
    stop = (held["live_attempt"] or {}).get("stop")
    if held["admission"] == "admitted" and stop and type(state) is str and state in _POSITIONS:
        position = position + " — " + stop if stop.startswith("stopping") and state != "exceptional" else stop
    held["execution_position"] = position if state not in HELD_STATES else UNKNOWN
    return position


def _row_position(position, stage, held, job):
    if held["admission"] == "not admitted":
        return position + " · not admitted"
    if position == "in progress" and stage.get("state") == "running":
        return "running"
    if position == "admitted" and stage.get("state") in ("offered", "claimed"):
        return "admitted · waiting for worker to start"
    if stage.get("state") == "blocked" and position == held["plan_position"]:
        gates = [gate for gate in _rows(stage.get("gates")) if gate.get("open") is False]
        if gates:
            prefix = str(_mapping(job).get("job_id")) + "/"
            names = [gate["stage_id"].removeprefix(prefix) if isinstance(gate.get("stage_id"), str) and gate["stage_id"] else _gate_text(gate)
                     for gate in gates]
            return "waiting for " + ", ".join(names)
    if position == UNKNOWN or position.startswith("unknown (reported state:"):
        return position + (" · admitted" if held["admission"] == "admitted" else " · admission unknown")
    return position


# Ending vocabulary of the published offer settlement result.
_CLAIM_ENDINGS = ("declined", "expired", "abandoned-after-restart", "claim-refused", "settlement-expired")


def _facts(stage, held, observed_at):
    facts = ["result recorded: " + _status_text(artifact.get("output_name")) for artifact in _rows(stage.get("artifacts"))]
    live = held["live_attempt"]
    if live:
        if live["offered"]:
            facts.append("offered")
        for receipt in live["receipts"]:
            if receipt.get("act") == "admit" and receipt.get("state") == "refused":
                facts.append("offer refused")
            if receipt.get("act") == "claim":
                result = _mapping(_mapping(receipt.get("detail")).get("result")).get("state")
                facts.append("claimed" if result == "claimed" else "claim not obtained: " + (_status_text(result) if result in _CLAIM_ENDINGS else UNKNOWN))
    if held["admission"] != "admitted":
        return facts
    if held["live_allocation"]:
        facts.append("reserved on " + held["allocation_worker"])
    runtime = _mapping(stage.get("runtime"))
    for key in ("runtime_id", "execution_runtime"):
        if key in runtime and runtime[key] is not None:
            facts.append("runtime recorded: " + _status_text(runtime[key]) if type(runtime[key]) is str and runtime[key] else "runtime unknown")
    diagnostic = _diagnostic(stage, stage.get("attempt_id"))
    if _declared_fact(diagnostic, "start_failure_recorded") is True:
        facts.append("runtime start failed")
    exchange = _mapping(stage.get("exchange"))
    receipt = _mapping(exchange.get("receipt"))
    if "accepted_at" in receipt:
        try:
            _instant(receipt["accepted_at"])
            facts.append("command accepted (reported) at " + _status_text(receipt["accepted_at"]))
        except (ValueError, TypeError, OverflowError):
            facts.append("command acceptance unknown")
    if held["timing"]["invocation_valid"]:
        facts.extend(("execution started", "provider started at " + _status_text(held["started_at"])))
    elif exchange.get("invocation") is not None:
        facts.append("execution start unknown; invocation evidence unknown")
    return facts


def attempt_lines(held, *, detail=False):
    """Shared words; renderers choose indentation, not evidence or positions."""
    lines = []
    for attempt in held["attempts"]:
        if attempt["admission"] != "admitted":
            if detail and attempt["admission"] == UNKNOWN:
                lines.append("reserved identity — admission unknown")
            continue
        line = "attempt " + str(attempt["episode"]) + " " + _status_text(attempt["attempt_id"])
        if attempt["stop"]:
            line += " — " + attempt["stop"]
        lines.append(line)
        if not attempt["live"]:
            allocation = attempt["allocation"]
            lines.append("  worker " + _status_text(allocation.get("worker_id")) + "; participant " + _status_text(allocation.get("participant"))
                         + "; allocation " + _status_text(allocation.get("allocation_state")) + "; release reason " + _status_text(allocation.get("release_reason")))
            lines.append("  " + ("ending " + _status_text(attempt["ending"]) + " at " + _status_text(attempt["ended_at"]) if attempt["ending"] else "no ending recorded"))
            lines.append("  other facts unknown")
    return lines


def job_view(document, job):
    """Interpret one Job from a published document, without I/O or mutation."""
    phases = [stage_view(stage, _mapping(document).get("observed_at"), job)
              for stage in _rows(_mapping(job).get("stages"))]
    count = sum(phase["attempt_count"] for phase in phases if phase["state"] in _STATUS_STAGE_STATES and phase["state"] not in TERMINAL_STATES)
    headline, reason = _job_headline(job, phases)
    label = ""
    summary = str(count) + " admitted attempt(s) in nonterminal phases"
    if job.get("mode") == "MANUAL":
        budget = _mapping(job.get("budget"))
        charged, limit = budget.get("charged_seconds"), budget.get("limit_seconds")
        if type(charged) is int and type(limit) is int:
            summary += f"; Job wall budget {charged}/{limit}s charged"
        if job.get("closed_at"):
            summary += "; closed at " + _status_text(job["closed_at"])
        label = "MANUAL OPEN   " if job.get("lifecycle") == "open" else "MANUAL · "
    return {"headline": headline, "labelled_headline": label + headline, "headline_reason": reason, "phases": phases, "open_admitted": count,
            "recorded_runtimes": sum(stage.get("runtime") is not None for stage in _rows(_mapping(job).get("stages"))),
            "summary": summary}
