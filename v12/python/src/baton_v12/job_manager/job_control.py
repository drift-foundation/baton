"""W383217 / DESIGN LIM-5: the persisted finite control of one Job.

WHAT THIS OWNS. One versioned CONTROL PROFILE per Job -- the admitted
correction-round allowance and the stage/Job wall deadlines -- journalled in
this store INSIDE the submission that admits the Job, so a Job and its
control are one durable fact or none. The deadlines are DERIVED from durable
origins this store already holds: the Job's own `submissions.recorded_at`
(durable accepted creation, queue time included) and, per stage, the Worker
Manager's OWN journalled instant of the stage's `admit` operation as this
store carries it in the admit receipt's `detail.settled_at`. That instant is
the execution admission before preparation; a delayed reply or a restart
adoption records the same owner instant, and the earliest over all episodes
of a stage is the origin, so a replacement or a correction never resets it.

THE TRUSTED CLOCK MODEL. Immutable origins are not enough: a clock that
reads origin+200 and then origin+100 is still "after the origin" and would
lose a hundred known seconds. So this store persists a monotonic WATERMARK
(`meta` key `control.watermark`): the latest instant any control evaluation
of this store observed. Known elapsed time is measured from the LATER of the
clock and the watermark; a clock earlier than the watermark is `uncertain`
-- a rollback, or a restart on another clock basis -- which HOLDS new
admission and is reported, while deadlines the watermark already reached stay
reached and every fence and its reconciliation continue untouched.

THE TRIGGER IS DETERMINISTIC. `deadline_at` is origin plus the profile's
seconds, derived from durable rows, so every observer -- this incarnation,
the next one, a concurrent sweep -- derives the same instant and the expiry
record is signed over it. The record's observation instant is evidence of
when a manager noticed, never a substitute for the trigger: the shutdown
bound runs from the deadline, and a manager that was not serving reports the
gap rather than continuous enforcement.

WHAT IT DOES NOT OWN. Cessation, outputs, verdicts and settlement. A reached
deadline is carried out through `cancellation`: the expiry record is one more
fence the existing owners read, and the serving sweep orders exact-generation
cessation through the owners that already prove whether anything ceased.
"""

import json
from datetime import datetime, timezone

from ..contracts import ContractRefusal
from ..contracts.errors import name_value
from ..worker_manager import boundaries
from .store import job_signature

__all__ = ["CONTINUATIONS", "CONTROL_KIND", "EXPIRY_KIND",
           "NATIVE_HANDOFF_PROFILE", "HEAVY_NATIVE_HANDOFF_PROFILE",
           "SUCCESSOR_RECOVERY_PROFILE", "PROFILES", "PROFILE_MEMBERS",
           "continuation_allowance", "continuations_used_in",
           "refuse_continuation",
           "TRIGGERS", "TIMING", "WATERMARK_KEY", "control_operation_id",
           "expiry_operation_id", "owned_control", "resolved", "agreeing",
           "record_within", "control_in", "control_of", "controls_of",
           "expiry_in", "expiry_of", "expiries_of", "watermark_in",
           "advance_watermark", "observe", "job_origin_in",
           "stage_origin_in",
           "evaluate", "closing", "closed_of", "refuse_closed",
           "refuse_uncertain", "require_ordinary_profile",
           "closed_message", "rounds_used_in",
           "refuse_round", "expire", "reported", "report"]

CONTROL_KIND = "job.control"
EXPIRY_KIND = "job.expire"
WATERMARK_KEY = "control.watermark"
TRIGGERS = ("stage-deadline", "job-deadline")
TIMING = ("trusted", "uncertain")
UNITS = "seconds"

# THE FROZEN PROFILES, in the shape `execution_limits.GENERATIONS` keeps and
# for the same reason: a profile a Job was admitted under is never edited; a
# changed policy is a new entry. The first documentation profile is owner
# E383183 / DESIGN LIM-5 exactly: one implementation and one independent
# review with zero correction rounds, 4800 s per stage from execution
# admission, 9960 s per Job from durable accepted creation, 3600 s per
# provider invocation and 900 s per verification command.
PROFILE_MEMBERS = ("correction_rounds", "stage_seconds", "job_seconds",
                   "provider_turn_seconds", "verification_command_seconds")

# The one profile W385331 adds, named once so no caller spells it twice.
NATIVE_HANDOFF_PROFILE = "native-handoff/1"
HEAVY_NATIVE_HANDOFF_PROFILE = "native-handoff-heavy/1"
# W385624 / DESIGN REC-8: the finite control of one RETAINED-RECOVERY
# verification/review successor. Owner M385612 approved the definition record
# `stage1-verification-review/1` (`a4be8b48`'s sibling,
# `5a6a420e416caab0942f9709939ae01f1f2d9dabbd13e09ff3b03ea08d2932fb`), and
# `retained_recovery` holds those exact bytes and proves at import that this
# entry states the same five bounds. A NEW immutable entry rather than a reuse
# of `documentation/1`, which happens to carry the same numbers: a Job's
# control profile is the policy it was ADMITTED under, and two different owner
# approvals sharing one name would make the admitted policy unattributable.
SUCCESSOR_RECOVERY_PROFILE = "stage1-verification-review/1"
def require_ordinary_profile(control):
    """Recovery policy is admitted only by the retained-successor owner."""
    if control and control.get("profile") == SUCCESSOR_RECOVERY_PROFILE:
        raise ContractRefusal("refused", "precondition", "stage1-verification-review/1 requires retained-recovery successor admission")


PROFILES = {
    "documentation/1": {"correction_rounds": 0, "stage_seconds": 4800,
                        "job_seconds": 9960, "provider_turn_seconds": 3600,
                        "verification_command_seconds": 900},
    # W385331: THE MINIMAL HANDOFF-CAPABLE PROFILE, and a NEW entry rather
    # than a widened `documentation/1` -- which is this table's standing rule
    # ("a profile a Job was admitted under is never edited") and the slice's
    # own instruction in the same words: add a new immutable profile revision,
    # do not widen documentation/1 in place.
    #
    # EVERY NUMBER HERE IS `documentation/1`'S, UNCHANGED. Zero code-correction
    # rounds, 4800 s per stage, 9960 s per Job, 3600 s per provider invocation
    # and 900 s per verification command. What this profile adds is ONE
    # RESOLVED CONTINUATION, and that allowance is deliberately NOT a member of
    # this document -- see `CONTINUATIONS` below.
    NATIVE_HANDOFF_PROFILE: {"correction_rounds": 0, "stage_seconds": 4800,
                             "job_seconds": 9960,
                             "provider_turn_seconds": 3600,
                             "verification_command_seconds": 900},
    # Owner M385638: a new immutable duration selection, not an extension
    # of any admitted Job. Clarification/correction policy stays unchanged.
    HEAVY_NATIVE_HANDOFF_PROFILE: {"correction_rounds": 0, "stage_seconds": 9000,
                                   "job_seconds": 21600,
                                   "provider_turn_seconds": 7200,
                                   "verification_command_seconds": 900},
    # Owner M385612, through STAGE-1-CONTRACT.md section 5: overall 9960 s
    # including queue from the accepted successor admission, 4800 s per stage
    # from each stage's own execution admission, 3600 s per review provider
    # invocation, 900 s per verification command (the approved corrected
    # verifier and the review's own required verification alike), and ZERO
    # automatic corrections and retries.
    SUCCESSOR_RECOVERY_PROFILE: {"correction_rounds": 0,
                                 "stage_seconds": 4800,
                                 "job_seconds": 9960,
                                 "provider_turn_seconds": 3600,
                                 "verification_command_seconds": 900},
}
CONTROL_MEMBERS = ("profile",)

# -- the continuation allowance, in its own table ----------------------------
#
# W385331. A SEPARATE FROZEN TABLE AND DELIBERATELY NOT A SIXTH
# `PROFILE_MEMBERS` ENTRY, for exactly the reason `role_contract` keeps its
# template binding out of `templates.TEMPLATE_MEMBERS`: that tuple is closed
# and it is what `resolved()` projects, so adding a member to it would have
# added one to `documentation/1`'s resolved document too -- and the resolved
# document of an already admitted profile is the policy a running Job is
# admitted under. Keeping documentation/1 immutable means keeping its BYTES
# immutable, not only its numbers.
#
# ZERO IS THE ANSWER FOR EVERY PROFILE THAT DOES NOT NAME ONE, and it is
# written out for `documentation/1` rather than defaulted, because "this
# profile permits no continuation" is a policy statement and a missing key is
# not one.
#
# WHAT A CONTINUATION IS NOT. It is not a correction round: it consumes no
# correction allowance, it resets no stage or Job clock, and
# `rounds_used_in` -- which counts `CORRECT_KIND` operations -- cannot see it.
# A profile with one continuation and zero correction rounds is therefore
# exactly what the slice selects: one more implementation invocation and its
# necessary response invocation, and still no code-correction round.
CONTINUATIONS = {"documentation/1": 0, NATIVE_HANDOFF_PROFILE: 1,
                 HEAVY_NATIVE_HANDOFF_PROFILE: 1,
                 # W385624: ZERO, written out rather than defaulted, because
                 # "this profile permits no continuation" is the owner's
                 # policy statement and a missing key is not one. The approved
                 # definition says zero automatic retries and zero automatic
                 # corrections; a recovery round is a new owner decision.
                 SUCCESSOR_RECOVERY_PROFILE: 0}


def _refuse(message, *, category="refused", code="precondition"):
    raise ContractRefusal(category, code, message)


def control_operation_id(job_id):
    return f"{CONTROL_KIND}:{job_id}"


def expiry_operation_id(job_id):
    """ONE expiry per Job: the first deadline reached closes it, and a later
    observer of the same durable deadline replays rather than collides."""
    return f"{EXPIRY_KIND}:{job_id}"


# -- the submitted member ----------------------------------------------------

def owned_control(value):
    """The one member a Job states: which frozen profile it is admitted under.

    A profile this build does not carry is a STALE SELECTION and is refused
    rather than guessed, exactly as an unknown compatibility generation is.
    """
    taken = boundaries.document(value, "a Job's control",
                                required=CONTROL_MEMBERS)
    profile = boundaries.text(taken["profile"], "a Job's control profile")
    if profile not in PROFILES:
        _refuse(f"a Job's control profile is one of "
                f"{', '.join(sorted(PROFILES))}; this is "
                f"{name_value(profile)}. A profile this build does not hold "
                f"is a control it cannot enforce, and guessing one would "
                f"admit the Job under a policy nobody selected",
                category="integrity", code="schema")
    return {"profile": profile}


def resolved(profile):
    """The frozen numbers of one profile, with their units, as a document."""
    held = PROFILES[owned_control({"profile": profile})["profile"]]
    return {"profile": profile, "units": UNITS,
            **{member: held[member] for member in PROFILE_MEMBERS}}


def agreeing(control, limits):
    """The profile pins the per-invocation ceilings; a Job whose resolved
    execution limits say otherwise is refused at submit rather than admitted
    under two accounts of one ceiling. The profile enlarges nothing: these
    are the existing runner defaults, restated by the owner's selection.
    """
    held = resolved(control["profile"])
    bounds = limits["boundaries"]
    pairs = (("provider_turn", "provider_turn_seconds"),
             ("ordinary_verification", "verification_command_seconds"))
    for boundary, member in pairs:
        if bounds[boundary]["seconds"] != held[member]:
            _refuse(f"control profile {name_value(held['profile'])} pins "
                    f"{member} at {held[member]} {UNITS} and this Job "
                    f"resolves {boundary} to {bounds[boundary]['seconds']}; "
                    f"a Job is admitted under one account of its ceilings",
                    category="integrity", code="schema")
    return held


# -- the persisted record, written inside the submission ----------------------

def record_within(store, connection, *, job_id, control, limits):
    """Journal the control INSIDE the caller's admission transaction.

    The row is this store's operations journal, keyed per Job, so a store
    holding the Job without its control cannot exist and no schema changes.
    """
    from . import documents

    held = agreeing(control, limits)
    operation_id = control_operation_id(job_id)
    operands = {"job_id": job_id, "profile": held["profile"],
                "resolved": {member: held[member]
                             for member in PROFILE_MEMBERS}}
    record = documents.job_control_record(
        operation_id=operation_id, job_id=job_id, profile=held["profile"],
        resolved=held, admitted_at=store._now(),
        incarnation=store.incarnation)
    return store.journal_within(connection, operation_id, CONTROL_KIND,
                                job_signature(CONTROL_KIND, operands), record)


def _committed(connection, operation_id, kind):
    row = connection.execute(
        "SELECT state, result FROM operations WHERE operation_id = ? AND "
        "kind = ?", (operation_id, kind)).fetchone()
    if row is None or row["state"] != "committed" or row["result"] is None:
        return None
    return json.loads(row["result"])


def control_in(connection, job_id):
    return _committed(connection, control_operation_id(job_id), CONTROL_KIND)


def control_of(store, job_id):
    boundaries.identity(job_id, "a Job id")
    return control_in(store._connection, job_id)


def _by_job(store, kind):
    held = {}
    for row in store._connection.execute(
            "SELECT result FROM operations WHERE kind = ? AND state = "
            "'committed' AND result IS NOT NULL", (kind,)):
        record = json.loads(row["result"])
        held[record["job_id"]] = record
    return held


def controls_of(store):
    return _by_job(store, CONTROL_KIND)


def expiry_in(connection, job_id):
    return _committed(connection, expiry_operation_id(job_id), EXPIRY_KIND)


def expiry_of(store, job_id):
    boundaries.identity(job_id, "a Job id")
    return expiry_in(store._connection, job_id)


def expiries_of(store):
    return _by_job(store, EXPIRY_KIND)


# -- the trusted clock -------------------------------------------------------

def _instant(value):
    for grammar in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(value, grammar).replace(
                tzinfo=timezone.utc)
        except (TypeError, ValueError):
            continue
    return None


def watermark_in(connection):
    row = connection.execute("SELECT value FROM meta WHERE key = ?",
                             (WATERMARK_KEY,)).fetchone()
    return None if row is None else row["value"]


def advance_watermark(connection, now):
    """Record `now` as observed, never moving the watermark backwards.

    ONE STATEMENT, because two observers reach this concurrently. W385624
    found it: the first cut READ the row, inserted when it was absent and
    updated when `now` was later, so two concurrent admissions against one
    store both found no watermark and both inserted -- and the loser died on
    `UNIQUE constraint failed: meta.key` inside a caller's transaction, which
    is a FAULT rather than the refusal that caller was entitled to. A
    read-then-write check is not a check when somebody else may write between
    the two; the upsert below decides it in the database, which is where both
    writers actually meet.

    THE SEMANTICS ARE UNCHANGED and the comparison is the same one: the row
    moves only when the new instant is LATER, and what is answered is the
    EFFECTIVE watermark -- `now` when it advanced and the standing value when
    it did not. Instants compare lexicographically by the frozen grammar
    `boundaries.instant` holds `now` to, which is what makes SQLite's own text
    comparison the same answer Python's `>` was.
    """
    boundaries.instant(now, "a control evaluation instant")
    connection.execute(
        "INSERT INTO meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO "
        "UPDATE SET value = excluded.value WHERE excluded.value > meta.value",
        (WATERMARK_KEY, now))
    return watermark_in(connection)


def observe(store, now):
    """Advance the persisted watermark to `now` as this store's own write."""
    return advance_watermark(store._connection, now)


# -- the durable origins -----------------------------------------------------

def job_origin_in(connection, job_id):
    row = connection.execute(
        "SELECT recorded_at FROM submissions WHERE submission_id = "
        "(SELECT submission_id FROM jobs WHERE job_id = ?)",
        (job_id,)).fetchone()
    return None if row is None else row["recorded_at"]


def stage_origin_in(connection, stage_id):
    """The OWNER'S instant of the stage's first admission, or None.

    Read from every admit receipt of the stage, performed or adopted alike:
    `detail.settled_at` is the Worker Manager's journal stamp of the
    `offer.issue` it committed, carried here verbatim. The local
    `recorded_at` of the receipt is deliberately not read -- it is when this
    store learned, which a delayed reply or a restart moves.
    """
    earliest = None
    for row in connection.execute(
            "SELECT detail FROM receipts WHERE stage_id = ? AND act = 'admit' "
            "AND state IN ('performed', 'adopted')", (stage_id,)):
        detail = json.loads(row["detail"])
        settled = detail.get("settled_at")
        if type(settled) is not str:
            # A receipt without the owner's instant is UNCERTAIN, not absent:
            # it says an admission happened and does not say when.
            return "uncertain"
        if earliest is None or settled < earliest:
            earliest = settled
    return earliest


def _seconds_between(later, earlier):
    one, two = _instant(later), _instant(earlier)
    if one is None or two is None:
        return None
    return int((one - two).total_seconds())


def _deadline(origin, seconds):
    try:
        return boundaries.deadline(origin, seconds, "a control deadline")
    except ContractRefusal:
        return None


def evaluate(connection, job_id, now, *, stages=None):
    """One Job's control evaluation at `now`, from durable rows only.

    PURE: reads this database and writes nothing, so a status read and a
    guard inside another owner's transaction get the same answer. `timing`
    is `uncertain` when `now` is earlier than the watermark OR THAN ANY
    DURABLE ORIGIN of this Job (review 2026-11-19T00-20-37Z P3: a first
    sweep or a restart behind the submission's own instant is a rollback
    this store can see without a watermark), when an origin cannot be
    ordered, or when a receipt holds no owner instant. The clock the
    deadlines and the elapsed times are decided against is the LATEST of
    `now`, the watermark and the origins -- the latest instant this store
    durably knows happened -- so a rollback never un-reaches a deadline and
    never reports less elapsed time than the rows already prove.
    """
    control = control_in(connection, job_id)
    if control is None:
        return None
    policy = control["resolved"]
    watermark = watermark_in(connection)
    job_origin = job_origin_in(connection, job_id)
    stage_rows = stages if stages is not None else [
        row["stage_id"] for row in connection.execute(
            "SELECT stage_id FROM stages WHERE job_id = ? ORDER BY ordinal",
            (job_id,))]
    origins = {stage_id: stage_origin_in(connection, stage_id)
               for stage_id in stage_rows}
    evidence = [one for one in (watermark, job_origin, *origins.values())
                if one is not None and one != "uncertain"
                and _instant(one) is not None]
    latest = max(evidence) if evidence else None
    timing = "trusted"
    if _instant(now) is None:
        timing = "uncertain"
        clock = latest
    elif latest is not None and now < latest:
        timing = "uncertain"
        clock = latest
    else:
        clock = now
    job_deadline = (_deadline(job_origin, policy["job_seconds"])
                    if job_origin is not None else None)
    if job_origin is None or job_deadline is None:
        timing = "uncertain"
    reached = []
    job_view = {"origin": job_origin, "deadline_at": job_deadline,
                "elapsed_seconds": (_seconds_between(clock, job_origin)
                                    if clock is not None
                                    and job_origin is not None else None),
                "reached": (clock is not None and job_deadline is not None
                            and clock >= job_deadline)}
    if job_view["reached"]:
        reached.append((job_deadline, 1, "", "job-deadline", None))
    stage_views = []
    for stage_id in stage_rows:
        origin = origins[stage_id]
        if origin == "uncertain":
            timing = "uncertain"
            origin = None
        deadline = (_deadline(origin, policy["stage_seconds"])
                    if origin is not None else None)
        if origin is not None and deadline is None:
            timing = "uncertain"
        view = {"stage_id": stage_id, "origin": origin,
                "deadline_at": deadline,
                "elapsed_seconds": (_seconds_between(clock, origin)
                                    if clock is not None and origin is not None
                                    else None),
                "reached": (clock is not None and deadline is not None
                            and clock >= deadline)}
        if view["reached"]:
            reached.append((deadline, 0, stage_id, "stage-deadline",
                            stage_id))
        stage_views.append(view)
    del reached
    held = {"profile": control["profile"], "resolved": policy,
            "timing": timing, "observed_at": now, "watermark": watermark,
            "job": job_view, "stages": stage_views,
            "corrections": {"allowance": policy["correction_rounds"],
                            "used": rounds_used_in(connection, job_id)},
            # W385331: AND THE CONTINUATION ACCOUNT, beside the correction one
            # and never merged with it. An operator reading a held Job has to
            # be able to see which of the two allowances is exhausted, and one
            # combined number cannot say.
            "continuations": {
                "allowance": CONTINUATIONS[control["profile"]],
                "used": continuations_used_in(connection, job_id)}}
    # THE RAW FIRST DEADLINE over every stage, finished or not: a reader's
    # convenience. Which deadline CLOSES the Job is `closing`'s question,
    # and it depends on which stages are already over.
    held["first"] = closing(held, any_stage=True)
    return held


def closing(evaluation, *, stage_id=None, any_stage=False, finished=()):
    """The first reached deadline that closes ONE question, or None.

    THE JOB DEADLINE ALWAYS COUNTS. A STAGE DEADLINE COUNTS FOR THE STAGE
    IT BOUNDS: reserving, claiming, launching or replacing that stage after
    it is refused, and the sweep fences the Job when it is reached while the
    stage is still unfinished. A stage that finished within its allowance
    never "reaches" it -- `finished` names those, from the projection that
    can see their outputs -- so a deadline that passes after useful work
    finished closes nothing and manufactures no cancellation of it. With
    neither `stage_id` nor `any_stage` only the Job deadline is asked, which
    is a correction round's question.

    Deterministic: by instant, then a stage before the Job at the same
    instant, then stage id, so every observer derives the same trigger.
    """
    if evaluation is None:
        return None
    reached = []
    job = evaluation["job"]
    if job["reached"]:
        reached.append((job["deadline_at"], 1, "", "job-deadline", None))
    for view in evaluation["stages"]:
        if not view["reached"] or view["stage_id"] in finished:
            continue
        if not any_stage and view["stage_id"] != stage_id:
            continue
        reached.append((view["deadline_at"], 0, view["stage_id"],
                        "stage-deadline", view["stage_id"]))
    if not reached:
        return None
    deadline, _, _, trigger, which = sorted(reached)[0]
    return {"trigger": trigger, "stage_id": which, "deadline_at": deadline}


def closed_of(store, job_id, now=None, *, stage_id=None, any_stage=False):
    """Why this Job admits nothing more for one question, or None. A read."""
    from . import cancellation

    now = store._now() if now is None else now
    fence = cancellation.fenced(store._connection, job_id)
    if fence is not None:
        return {"cause": "fenced", "fence": fence}
    held = evaluate(store._connection, job_id, now)
    if held is None:
        return None
    first = closing(held, stage_id=stage_id, any_stage=any_stage)
    if first is not None:
        return {"cause": "deadline", "first": first}
    if held["timing"] == "uncertain":
        return {"cause": "uncertain", "watermark": held["watermark"]}
    return None


def closed_message(closed, what):
    """One sentence saying why `what` is not admitted, from `closed_of`."""
    if closed["cause"] == "fenced":
        fence = closed["fence"]
        return (f"the Job was {'cancelled' if fence.get('trigger', 'operator') == 'operator' else 'expired'} at "
                f"{fence['requested_at']} ({fence['reason']}); {what} is not "
                f"admitted after the fence")
    if closed["cause"] == "deadline":
        first = closed["first"]
        return (f"the Job reached its {first['trigger']} at "
                f"{first['deadline_at']}; {what} is not admitted after the "
                f"deadline")
    return (f"the Job's timing is uncertain (watermark "
            f"{name_value(closed.get('watermark'))}); {what} is held")


def refuse_closed(connection, job_id, what, *, now, stage_id=None,
                  any_stage=False):
    """Refuse `what` ORDINARILY inside the caller's own transaction when the
    Job is fenced, when the Job deadline -- or the named stage's -- is
    reached by the trusted clock, or when timing is uncertain. The watermark
    is advanced on the same connection, so an act that COMMITS carries the
    instant it was decided against; a refused act rolls back with its
    transaction and leaves the sweep's own watermark standing.
    """
    from . import cancellation

    cancellation.refuse_fenced(connection, job_id, what)
    held = evaluate(connection, job_id, now)
    if held is None:
        return None
    advance_watermark(connection, now)
    first = closing(held, stage_id=stage_id, any_stage=any_stage)
    if first is not None:
        _refuse(f"Job {name_value(job_id)} reached its {first['trigger']} "
                f"at {first['deadline_at']}"
                + (f" (stage {name_value(first['stage_id'])})"
                   if first["stage_id"] is not None else "")
                + f"; {what} is not admitted after the deadline")
    if held["timing"] == "uncertain":
        _refuse(f"Job {name_value(job_id)}'s timing is uncertain (clock "
                f"{name_value(now)}, watermark "
                f"{name_value(held['watermark'])}); {what} is held until the "
                f"clock is trusted again")
    return held


def refuse_uncertain(connection, job_id, what, *, now):
    """Hold `what` ORDINARILY while this Job's timing is uncertain; a reached
    deadline is NOT asked here. For the one boundary that admits a NEW Job
    (a fresh attempt), whose own control starts afresh."""
    held = evaluate(connection, job_id, now)
    if held is None:
        return None
    advance_watermark(connection, now)
    if held["timing"] == "uncertain":
        _refuse(f"Job {name_value(job_id)}'s timing is uncertain (clock "
                f"{name_value(now)}, watermark "
                f"{name_value(held['watermark'])}); {what} is held until the "
                f"clock is trusted again")
    return held


# -- the correction allowance ------------------------------------------------

def rounds_used_in(connection, job_id):
    """Rounds this Job already spent: committed correction OPERATIONS, one
    per round -- never the two episode-ending rows one round writes."""
    from .episodes import CORRECT_KIND

    used = 0
    for row in connection.execute(
            "SELECT result FROM operations WHERE kind = ? AND state = "
            "'committed' AND result IS NOT NULL", (CORRECT_KIND,)):
        if json.loads(row["result"]).get("job_id") == job_id:
            used += 1
    return used


def continuation_allowance(profile):
    """How many resolved continuations one profile permits.

    A PROFILE THIS BUILD DOES NOT CARRY IS A STALE SELECTION, answered by
    `owned_control` rather than by a second membership test here -- so the
    refusal a caller gets is the one `resolved` already gives.
    """
    held = owned_control({"profile": profile})["profile"]
    return CONTINUATIONS[held]


def continuations_used_in(connection, job_id):
    """Continuations this Job already spent: committed continuation
    OPERATIONS, one per resolved continuation.

    THE MIRROR OF `rounds_used_in` AND A DIFFERENT COUNT. It reads the
    continuation kind and nothing else, so a correction round is invisible here
    and a continuation is invisible there -- which is what makes "one
    continuation and zero correction rounds" two allowances rather than one
    shared pool.
    """
    from .native_handoffs import CONTINUE_KIND

    used = 0
    for row in connection.execute(
            "SELECT result FROM operations WHERE kind = ? AND state = "
            "'committed' AND result IS NOT NULL", (CONTINUE_KIND,)):
        if json.loads(row["result"]).get("job_id") == job_id:
            used += 1
    return used


def refuse_continuation(connection, job_id):
    """Refuse a continuation this Job's admitted profile does not permit.

    EXHAUSTION HOLDS AND REPORTS HONESTLY; it does not fall back to a
    correction round, to a fresh attempt or to success. And REPLAY DOES NOT
    SPEND TWICE: the count is over committed continuation operations, so an
    exact retry of a continuation that already committed replays its own
    operation before ever reaching this guard.
    """
    control = control_in(connection, job_id)
    if control is None:
        return None
    allowance = CONTINUATIONS[control["profile"]]
    used = continuations_used_in(connection, job_id)
    if used >= allowance:
        _refuse(f"Job {name_value(job_id)} is admitted under control profile "
                f"{name_value(control['profile'])}, which permits "
                f"{allowance} resolved continuation(s) and {used} were used; "
                f"the answer stands recorded and the execution stays held")
    return {"allowance": allowance, "used": used}


def refuse_round(connection, job_id):
    control = control_in(connection, job_id)
    if control is None:
        return None
    allowance = control["resolved"]["correction_rounds"]
    used = rounds_used_in(connection, job_id)
    if used >= allowance:
        _refuse(f"Job {name_value(job_id)} is admitted under control "
                f"profile {name_value(control['profile'])}, which permits "
                f"{allowance} correction round(s) and {used} were used; the "
                f"changes-requested verdict stands and no round is opened")
    return {"allowance": allowance, "used": used}


# -- the expiry record -------------------------------------------------------

def expire(store, *, job_id, trigger, stage_id, deadline_at, observed_at):
    """Journal that this Job's FIRST deadline was reached: the fence.

    Signed over the durable trigger, never over the observation, so a
    restart or a concurrent sweep that derives the same deadline replays
    this record. `requested_at` is the deadline instant -- LIM-5's trigger
    the shutdown bound runs from -- and `observed_at` is when a manager
    noticed, reported beside it.
    """
    from . import documents

    if trigger not in TRIGGERS:
        _refuse(f"an expiry trigger is one of {TRIGGERS}; this is "
                f"{name_value(trigger)}", category="integrity", code="schema")
    boundaries.instant(deadline_at, "a control deadline")
    boundaries.instant(observed_at, "an expiry observation instant")
    operands = {"job_id": job_id, "trigger": trigger, "stage_id": stage_id,
                "deadline_at": deadline_at}
    operation_id = expiry_operation_id(job_id)
    signature = job_signature(EXPIRY_KIND, operands)
    reason = (f"{trigger} reached at {deadline_at}"
              + (f" (stage {stage_id})" if stage_id is not None else ""))

    def act(connection):
        if control_in(connection, job_id) is None:
            _refuse(f"Job {name_value(job_id)} holds no control; a deadline "
                    f"is reached under a profile", category="integrity",
                    code="schema")
        advance_watermark(connection, observed_at)
        return documents.job_expiry(
            operation_id=operation_id, job_id=job_id, trigger=trigger,
            stage_id=stage_id, reason=reason, requested_at=deadline_at,
            deadline_at=deadline_at, observed_at=observed_at,
            incarnation=store.incarnation)

    return store.transact(operation_id, EXPIRY_KIND, signature, act)


# -- the report --------------------------------------------------------------

def reported(evaluation, fence):
    from . import documents

    if evaluation is None:
        return None
    return documents.job_control_report(
        profile=evaluation["profile"], resolved=evaluation["resolved"],
        timing=evaluation["timing"], observed_at=evaluation["observed_at"],
        watermark=evaluation["watermark"], job=evaluation["job"],
        stages=evaluation["stages"], corrections=evaluation["corrections"],
        continuations=evaluation["continuations"],
        fence=(None if fence is None else {
            "trigger": fence.get("trigger", "operator"),
            "requested_at": fence["requested_at"],
            "operation_id": fence["operation_id"]}))


def report(store, job_id, *, now):
    """One Job's control report from a store handle; a read."""
    from . import cancellation

    boundaries.identity(job_id, "a Job id")
    with store.read_snapshot():
        evaluation = evaluate(store._connection, job_id, now)
        fence = cancellation.fenced(store._connection, job_id)
    return reported(evaluation, fence)
