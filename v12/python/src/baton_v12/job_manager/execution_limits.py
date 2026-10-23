"""W156162: the per-Job execution ceilings, and what they are NOT.

Owner decision 2026-09-13T00:49:46Z, pinned in
`work/records/2026/09/finding-v12-per-job-budgets/FINDING.md`: a Job may
override the PROVIDER TURN and the VERIFICATION COMMAND ceilings, Job-wide,
preserving each runner's existing default when the Job says nothing. Cumulative
accounting and separate role/stage pools are deferred, and there is no universal
five-minute default.

WHAT THESE NUMBERS MEAN, because the requirement exists precisely because that
was unclear. Each one is a PER-INVOCATION ceiling handed to one command: the
seconds one provider turn may take, and the seconds one verification command may
take. None of them is a cumulative allowance, a remaining balance, a budget the
Job spends down, or a limit on how long an agent may work in total. W103525's
five-minute figures are cumulative TEST SUBPROCESS wall time recorded by hand
for one Work; they are not a worker timeout and they are not a default here.

WHY THE DEFAULTS ARE FOUR NUMBERS AND NOT ONE. The deployed runners already
carry different ceilings for different boundaries, each chosen for its own
reason, and inventing one number to replace all four would be this Work
changing behaviour nobody asked it to change. So an omitted setting resolves to
the boundary's OWN existing default, and only an explicit Job setting moves it.

ONE EXPLICIT VERIFICATION SETTING REACHES ALL THREE VERIFICATION BOUNDARIES,
which is the owner's "Job-wide overrides initially". A Job that wants the
ordinary and the imported verification to differ is asking for the role/stage
pools that were deferred, and it is refused the ability to express that here
rather than given half of it.
"""

from ..contracts import ContractRefusal
from ..contracts.errors import name_value
from ..worker_manager import boundaries

__all__ = ["BOUNDARIES", "CHECKOUT_SECONDS", "CHECKOUT_STEPS",
           "CLEANUP_RESERVE_SECONDS", "task_token_seconds",
           "COMPATIBILITY", "CURRENT_GENERATION",
           "GENERATIONS", "LEGACY_GENERATION", "LIMIT_MEMBERS", "MAX_SECONDS",
           "MIN_SECONDS", "SCOPE", "UNITS", "boundary_default", "effective",
           "owned_execution_limits", "owned_generation", "requested_from_row",
           "resolved"]

# The two settings a Job may state. CLOSED, so a document that grows a third
# is refused rather than half-read -- the same rule the submission itself
# follows, for the same reason.
LIMIT_MEMBERS = ("provider_turn_seconds", "verification_command_seconds")

# Every ceiling this build hands to a command, and the runner default each one
# keeps when the Job says nothing. These four are the CURRENT deployed values,
# read from their owners rather than chosen here:
#
#   `v12/worker/claude_agent.py`        one provider invocation   3600
#   `v12/worker/claude_agent.py`        one ordinary verification  900
#   `v12/worker/integration_workload.py` imported verification    1800
#   `v12/python/tools/stage_execution.py` host composition test    300
#
# The host figure is `GIT_SECONDS`, which ALSO bounds unrelated Git commands.
# A Job's verification setting moves the verification boundary and leaves those
# Git commands where they are; the owner decision says so in as many words.
BOUNDARIES = {
    "provider_turn": "provider_turn_seconds",
    "ordinary_verification": "verification_command_seconds",
    "integration_verification": "verification_command_seconds",
    "host_verification": "verification_command_seconds",
}

# AND THE DEFAULTS AS VERSIONED, FROZEN GENERATIONS -- which is review
# 2026-09-13T01:13:49Z R1, and a correction of a rule I had backwards.
#
# The first form resolved against these constants at READ TIME, and my reasoning
# for it was that a pinned resolution would go stale. That reverses the rule PLAN
# item 1 actually states: an admitted Job's configuration is deliberately STABLE,
# and changing a default must not reinterpret it. The reviewer's probe made the
# consequence concrete -- a Job submitted with the provider default preserved
# reported 3600, and the same unchanged Job reported 7200 the moment a newer
# default existed, while its identical submission still replayed.
#
# So a Job PINS THE GENERATION it was admitted under, and every read resolves
# through that generation's frozen table. A new default is a NEW GENERATION:
# new Jobs get it, existing Jobs keep what they were admitted with, and nobody
# has to rewrite a signed operand to say so.
#
# GENERATION 0 IS WHAT CAME BEFORE THIS BUILD. Jobs already in a store when this
# feature arrived configured nothing and ran under exactly these four numbers;
# recording that as its own immutable generation is how a migrated Job keeps
# meaning what it meant, rather than inheriting whatever the constants say later.
GENERATIONS = {
    0: {"provider_turn": 3600, "ordinary_verification": 900,
        "integration_verification": 1800, "host_verification": 300},
    1: {"provider_turn": 3600, "ordinary_verification": 900,
        "integration_verification": 1800, "host_verification": 300},
}

# Which generation Jobs admitted before this feature belong to, and which one
# this build admits new Jobs under. A default change adds a generation and moves
# CURRENT; it never edits an existing entry, because an edited entry is exactly
# the reinterpretation this structure exists to prevent.
LEGACY_GENERATION = 0
CURRENT_GENERATION = 1

# Where an effective value came from, as a closed vocabulary of two. A reader
# that cannot tell a Job's own choice from a preserved default cannot tell
# whether anybody decided anything.
COMPATIBILITY = "compatibility"
JOB = "job"

# AND WHAT THE NUMBERS ARE, said rather than assumed. The owner asked for exact
# units, scope and effective values, and a bare integer says none of the three.
UNITS = "seconds"
SCOPE = "per-invocation"

# ONE SUPPORTED RANGE, SHARED BY EVERY READER, AND NO SILENT CLAMP. The plan
# requires one range both the configuring owner and the consuming runner agree
# on: a value outside it is REFUSED where it is written, so no runner has to
# decide what to do with a number it cannot honour. One second is the smallest
# ceiling that can still admit a command; one day is far above every deployed
# default and far below the point where a caller is plainly saying "no limit",
# which this build does not offer.
MIN_SECONDS = 1
MAX_SECONDS = 86400


def _refuse(message):
    raise ContractRefusal("integrity", "schema", message)


def _seconds(value, member):
    """One positive whole number of seconds, in the one supported range.

    `bool` IS an `int` in Python and is refused first, because `True` would
    otherwise pass every numeric test below and persist as one second. A float
    is refused rather than rounded: a ceiling somebody wrote as 900.5 is a
    ceiling they have not agreed with this build about.
    """
    if type(value) is not int:
        _refuse(f"a Job's {member} is a whole number of {UNITS}; this is "
                f"{name_value(value)}")
    if value < MIN_SECONDS or value > MAX_SECONDS:
        _refuse(f"a Job's {member} is between {MIN_SECONDS} and "
                f"{MAX_SECONDS} {UNITS}; this is {name_value(value)}. The "
                f"range is refused here rather than clamped, because a runner "
                f"silently given a different ceiling than the operator wrote "
                f"is the confusion this Work exists to remove")
    return value


def owned_execution_limits(value):
    """One Job's requested settings, proved and returned in this build's order.

    Returns `None` for a Job that states none -- which is a DIFFERENT document
    from one stating an empty object, and both resolve to the same effective
    values. An empty object is a Job that opened the member and decided
    nothing, and it is admitted as exactly that rather than refused.
    """
    if value is None:
        return None
    taken = boundaries.document(value, "a Job's execution limits",
                                optional=LIMIT_MEMBERS)
    held = {}
    for member in LIMIT_MEMBERS:
        if member in taken:
            held[member] = _seconds(taken[member], member)
    return held


def owned_generation(value):
    """One compatibility generation this build knows, proved."""
    if type(value) is not int or type(value) is bool \
            or value not in GENERATIONS:
        _refuse(f"a Job's compatibility generation is one of "
                f"{', '.join(str(one) for one in sorted(GENERATIONS))}; this "
                f"is {name_value(value)}. A generation this build does not "
                f"hold is a resolution it cannot reproduce, and guessing one "
                f"would reinterpret the Job")
    return value


# W325959: THE NATIVE TASK-TOKEN LIFETIME, composed from this owner's own
# boundaries and nothing invented.
#
# WHY A TOKEN LIFETIME BELONGS HERE AT ALL. The native stop owner is the
# serving loop's reclaim pass: `tokens.Governance.overdue` answers only for an
# EXPIRED token and `tools/job_manager._reclaiming` acts on what it answers.
# So on the native path the token's lifetime IS the execution bound, and it has
# to cover the authorized work the attempt performs inside the workspace or it
# revokes a worker that is still doing what it was told to do. That is the
# recorded pilot failure: the task token took the 900-second default while its
# Job allowed a 3600-second provider turn.
#
# WHAT IT COVERS, enumerated rather than estimated -- every bounded operation
# the worker performs between acquisition and cessation:
#
#   * the SOURCE CHECKOUT. `v12/worker/claude_agent.py` gives each step of the
#     composed plan `CHECKOUT_SECONDS`, and the version-control profile's plan
#     is three steps (clone, detach, verify). `CHECKOUT_STEPS` is that count.
#   * ONE PROVIDER TURN, at this Job's resolved `provider_turn`. One, and the
#     product enforces it: `baton_worker.serve_exchange` publishes its receipt
#     before dispatch as the replay fence, so a restart or a crash re-entry
#     "all find it and none of them starts a second provider turn".
#   * ONE ORDINARY VERIFICATION, at this Job's resolved boundary.
#
# WHAT IT DOES NOT COVER, deliberately: offer settlement and host preparation
# happen BEFORE acquisition, and custody discard, container removal and the
# stop grace happen at or AFTER cessation. Expiry is not release, so the
# cleanup reserve below is additional rather than carved out of the work.
#
# THIS IS A LIM-2 TOKEN BOUND, not a LIM-3 cumulative one. It is derived per
# attempt from that attempt's own operations and each attempt acquires its own
# token, so nothing accumulates across a Job's stages and no whole-Job ceiling
# is implied.
CHECKOUT_SECONDS = 900
CHECKOUT_STEPS = 3
CLEANUP_RESERVE_SECONDS = 120


def task_token_seconds(resolved, *, checkout_steps=CHECKOUT_STEPS,
                       cleanup_reserve=CLEANUP_RESERVE_SECONDS):
    """How long a native task token must live for THIS Job's resolution.

    `resolved` is an `execution_limits.resolved` document -- this owner's own
    output -- so the two invocation ceilings come from the Job's admitted
    configuration and are never re-derived here. The per-invocation ceilings
    themselves are UNCHANGED by this: a longer token does not lengthen a
    provider turn or a verification, it only stops the permission expiring
    while one of them is legitimately running.
    """
    boundaries = resolved["boundaries"]
    provider = boundaries["provider_turn"]["seconds"]
    verification = boundaries["ordinary_verification"]["seconds"]
    if checkout_steps < 0 or cleanup_reserve < 0:
        _refuse("a token lifetime is composed from non-negative allowances")
    return (checkout_steps * CHECKOUT_SECONDS + provider + verification
            + cleanup_reserve)


def boundary_default(boundary, generation=CURRENT_GENERATION):
    """The runner default one boundary keeps under one frozen generation."""
    if boundary not in BOUNDARIES:
        _refuse(f"{name_value(boundary)} is not one of this build's execution "
                f"boundaries {', '.join(sorted(BOUNDARIES))}")
    return GENERATIONS[owned_generation(generation)][boundary]


def effective(requested, boundary, generation=CURRENT_GENERATION):
    """The seconds one boundary actually gets, and where that came from."""
    member = BOUNDARIES[boundary]
    if requested and member in requested:
        return requested[member], JOB
    return boundary_default(boundary, generation), COMPATIBILITY


def resolved(requested, generation=CURRENT_GENERATION):
    """The whole effective configuration, as a reader is owed it.

    UNITS AND SCOPE TRAVEL WITH THE NUMBERS. The owner asked for exact units,
    scope and effective values; a document carrying seconds alone would leave
    the next reader to guess, which is how the five-minute figure came to be
    read as a worker timeout in the first place.

    AND THE REQUESTED SETTINGS TRAVEL BESIDE THE EFFECTIVE ONES. They are
    different facts: what a Job asked for is immutable, and what a boundary
    gets is a resolution this build performed. A document carrying only the
    second could not answer whether a later default change moved it.
    """
    held = dict(requested or {})
    generation = owned_generation(generation)
    answer = {"units": UNITS, "scope": SCOPE,
              # THE GENERATION THIS JOB WAS ADMITTED UNDER, carried so a reader
              # can see WHICH frozen defaults produced these numbers -- and so
              # two Jobs reporting different preserved defaults are legible
              # rather than contradictory.
              "compatibility_generation": generation,
              "requested": {member: held[member] for member in LIMIT_MEMBERS
                            if member in held},
              "boundaries": {}}
    for boundary in sorted(BOUNDARIES):
        seconds, origin = effective(held, boundary, generation)
        answer["boundaries"][boundary] = {
            "seconds": seconds, "origin": origin,
            "setting": BOUNDARIES[boundary],
            "default_seconds": boundary_default(boundary, generation)}
    return answer


def requested_from_row(text):
    """The requested settings a stored row holds, proved on the way out.

    A row is this build's own write, and it is still owned on the way back:
    a store somebody edited by hand is exactly where an unchecked read would
    hand a runner a ceiling nobody agreed to.
    """
    import json

    if text is None:
        return None
    try:
        held = json.loads(text)
    except ValueError:
        _refuse("a stored Job execution limit row is not readable as one")
    return owned_execution_limits(held)
