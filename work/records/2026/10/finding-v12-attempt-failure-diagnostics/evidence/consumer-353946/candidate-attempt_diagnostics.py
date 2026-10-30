"""W333486 -- one READ-ONLY diagnostic report over one status document.

A PURE PROJECTION, and the word is exact. It opens no store, asks for no
clock, calls no engine, speaks to no provider and spawns no subprocess. Its
only input is a status document read through `tools/job_viewer.read_snapshot`,
which is `tools/worker_visibility.py`'s accepted discipline and is reused here
rather than respelled.

WHAT IT IS NOT, and each of these is a line somebody has crossed before:

* IT IS NOT AN ACCEPTANCE. A diagnostic cause says which component ordered a
  runtime stopped. It does not accept a candidate, settle a stage, clear a
  gate or authorize a cleanup, and nothing in the projection branches on it.
* IT IS NOT A FRESHNESS VERDICT. No freshness policy has been selected for
  these facts, so this reports the instants it was given and declines to say
  whether they are recent. Inventing a staleness rule here would be this
  report selecting a policy nobody ruled on.
* IT RESOLVES NO LOCATOR. Device and inode identify a workspace OBJECT. They
  are not a path, and they resolve no retained output on their own. The
  supported read is the deployed `logs` subcommand over
  `worker_manager.attempt_logs`, and this report emits the exact invocation
  shape with the ONE operand the operator must supply named as such -- the
  delivery root. A report that resolved a deployment document would be a
  reader that can be pointed at a store, which is the thing this is not.
* IT CARRIES NO STREAM CONTENT, NO CREDENTIAL, NO ENVIRONMENT VALUE AND NO
  PRIVATE TEXT. The allowlist below is POSITIVE -- a member reaches the report
  because it is named here with a declared type, not because it was present in
  the document -- and nothing nested is forwarded wholesale. A new member
  appearing upstream is reported as unrecognised rather than passed through.

AND AN INCOMPLETE FINAL RESULT IS INCOMPLETE. A status document whose recorded
facts are partial the way a deadline-bounded publication failure leaves them
is reported as `incomplete`, which is neither a cessation nor an acceptance.
`SHUTDOWN.md` and `decisions/shutdown-review.md` state the rule three ways and
this report is held to it: a missing or partial final result is never success,
never acceptance and never proof of cessation.

AND THE REBUILT BUNDLE OBLIGATION IS EXPLICIT. `tools/stack_command.COMMANDS`
serves this subcommand in SOURCE, and a source-level case is not proof that an
installed bundle carries it. The deployed bundle must be rebuilt before an
operator can reach this command from a deployment; this Work rebuilds nothing
and says so here and in `report()`.
"""

import json
import sys


from tools import job_viewer

SCHEMA = "baton.v12.attempt-diagnostics/1"

# W333486 review340349 blocker 2: THE PRODUCER'S OWN VERSION, OWNED HERE BY
# VALUE. `baton_v12.worker_manager.failure_cause.DIAGNOSTIC_SCHEMA` is the one
# authority for this string; it is copied rather than imported for exactly the
# reason `tools/stack.py` copies the status schema -- this report is a pure
# projection and importing the manager package would give it a dependency on
# the thing it is a projection OVER. The copy cannot drift silently:
# `tests/tools/test_attempt_diagnostics.py` holds it equal to the original.
#
# AND IT IS OWNED IN BOTH DIRECTIONS. A diagnostic carrying a version this
# report does not own is reported as unavailable-as-evidence saying WHICH
# version it was, rather than being decoded member by member against a shape
# nobody promised.
SOURCE_DIAGNOSTIC_SCHEMA = "baton.v12.attempt-failure-cause/1"

# THE SUPPORTED RETAINED-OUTPUT READ, and the one operand it needs that this
# report cannot supply. `<launch-home>` is a DEPLOYMENT fact; resolving it
# would make this a reader that can be pointed at a store.
LOCATOR_COMMAND = ("baton-v12-stack logs --logs <launch-home>/logs "
                   "--attempt <attempt-id> locators")
LOCATOR_OPERAND = "<launch-home>"
LOCATOR_WHY = ("the delivery root is a deployment fact and this report "
               "resolves no deployment document; a report that did would be "
               "a reader that can be pointed at a store")

# THE POSITIVE ALLOWLIST, with a declared type per member. A member is here
# because it was chosen, and anything else in the document is unrecognised.
# `None` in a type tuple means the member may honestly be absent.
#
# EVERY MEMBER BELOW IS READ AS A WRAPPER, which is the one owned shape
# review340349 blocker 2 required and the thing the rejected candidate got
# wrong: the producer wrapped its facts as `{"known": ..., "value": ...,
# "source": ...}` and this report's member lists wanted raw scalars, so a
# recorded KNOWN value arrived as UNKNOWN. The declared type is the type of
# the wrapper's `value`, and `_fact` is the single decoder.
STAGE_MEMBERS = (
    ("stage_id", (str,)),
    ("job_id", (str,)),
    ("kind", (str,)),
    ("state", (str,)),
    ("attempt_id", (str, type(None))),
    ("episode", (int, type(None))),
)
# THE CAUSAL MEMBERS: which component, under which operation, with what
# engine outcome, and whether cessation was established. `effects` is what
# the pass ACTUALLY ordered -- a list, because a replayed reclaim that
# observed an exact absence ordered nothing and a known empty is not an
# unknown.
CAUSE_MEMBERS = (
    ("component", (str,)),
    ("operation_id", (str,)),
    ("correlation_id", (str,)),
    ("outcome", (str,)),
    ("cessation", (str,)),
    ("runtime_id", (str,)),
    ("category", (str,)),
    ("code", (str,)),
    ("effects", (list, tuple)),
    ("superseded", (int,)),
    ("intent_recorded", (bool,)),
)
EXECUTION_MEMBERS = (
    ("execution_runtime", (str,)),
    ("cleanup", (str,)),
    ("observed_at", (str, int, float)),
    ("runtime_id", (str,)),
    ("token_bound_runtime_id", (str,)),
    ("activity_bytes", (int,)),
    ("activity_at", (str, int, float)),
)
# THE TOKEN AXIS, member by member and with no arithmetic anywhere. An expiry
# with `renewals=0` against a limit of four is legible by reading the two
# numbers beside each other, which is the pilot's exact shape.
TOKEN_MEMBERS = (
    ("owner", (str,)),
    ("container", (str,)),
    ("expires_at", (str, int, float)),
    ("acquired_expires_at", (str, int, float)),
    ("renewed_at", (str, int, float)),
    ("renewals", (int,)),
    ("renewals_remaining", (int,)),
    ("expired", (bool,)),
    ("expiry_judged_at", (str, int, float)),
    ("returned", (bool,)),
    ("activating", (bool,)),
    ("launch", (str, int, float, bool)),
)
# THE LIMITS, THE REVOCATION, THE COMPLETION AND THE TWO PRE-EXECUTION
# ENDINGS. All five were composed by the producer and named in NONE of the
# rejected candidate's member lists, so they were silently dropped.
AXIS_MEMBERS = (
    ("renewal_limit", (int,)),
    ("lifetime_seconds", (int, float)),
    ("domain", (str,)),
    ("generation", (int, str)),
    ("revocation", (bool,)),
    ("revoked_expired_at", (str, int, float)),
    ("revoked_container", (str,)),
    ("revoked_owner", (str,)),
    ("completion", (bool,)),
    ("start_failure_recorded", (bool,)),
    ("start_failure_runtime_id", (str,)),
    ("preparation_failure_recorded", (bool,)),
    ("preparation_failure_runtime_id", (str,)),
)
WORKSPACE_MEMBERS = (
    ("device", (int,)),
    ("inode", (int,)),
)

# THE JOB'S OWN EXECUTION LIMITS, and the snapshot's own observation time.
#
# W333486 review-2026-10-22T18-18-00Z.md: `rows_of` discarded the Job object
# when it built a row, so a report about a failed attempt could not say which
# provider or verification ceiling that attempt actually ran under, and
# `report` discarded `observed_at`, so it could not say how old the snapshot
# was. The token axis is NOT a substitute: a token lifetime and a renewal limit
# are a different mechanism from the per-invocation ceilings a command is given.
# An independent packaged reproduction proved both absent downstream while
# present upstream (`evidence/review-353910/report-omission.json`).
#
# THE VOCABULARY IS MIRRORED BY VALUE, the same way SOURCE_DIAGNOSTIC_SCHEMA is
# and for the same reason: this report is a projection OVER the Job manager and
# importing it would give the projection a dependency on its own subject.
# `test_owned_execution_limit_vocabulary_does_not_drift` holds every name here
# against `baton_v12.job_manager.execution_limits`.
SOURCE_LIMIT_BOUNDARIES = ("host_verification", "integration_verification",
                           "ordinary_verification", "provider_turn")
SOURCE_LIMIT_SETTINGS = ("provider_turn_seconds",
                         "verification_command_seconds")
SOURCE_LIMIT_UNITS = "seconds"
SOURCE_LIMIT_SCOPE = "per-invocation"

# WHAT A JOB STATES ABOUT ITS LIMITS, beside the per-boundary resolution below.
# `requested` is what the Job ASKED FOR and is deliberately separate from the
# effective value: an empty `requested` beside an effective 3600 says the
# default applied, which is a different fact from a Job that asked for 3600.
LIMIT_ENVELOPE_MEMBERS = (
    ("units", (str,)),
    ("scope", (str,)),
    ("compatibility_generation", (int,)),
)
# PER BOUNDARY: what it IS, what it would have been, where that came from, and
# which Job setting moves it. `origin` is the provenance the review asked for.
BOUNDARY_MEMBERS = (
    ("seconds", (int,)),
    ("default_seconds", (int,)),
    ("origin", (str,)),
    ("setting", (str,)),
)
# THE SNAPSHOT'S OWN OBSERVATION TIME, which is NOT the runtime's observation
# time and NOT the cause's instant. All three appear in this report and they
# are three different facts: `source_observed_at` is when the document was
# composed, `execution.observed_at` is when the runtime was looked at, and the
# cause carries its own `at`. No freshness verdict is derived from any of them.
_LIMIT_SETTING_MEMBERS = tuple((one, (int,))
                               for one in SOURCE_LIMIT_SETTINGS)
SOURCE_TIME_MEMBERS = (
    ("observed_at", (str, int, float)),
)

NO_DIAGNOSTIC = ("this status document carries no attempt diagnostics for "
                 "this stage; nobody looked, which is not the same as "
                 "nothing having happened")


def _known(value, source):
    return {"known": True, "value": value, "source": source}


# THE ABSENT-RECORD NAMES THE PRODUCER ACTUALLY EMITS.
#
# W333486 claim353758. The previous revision allowlisted `attempt.start-failed`,
# `attempt.preparation-failed` and a bare `resource.revoked`. The producer emits
# `runtime.start-failed`, `runtime.preparation-failed` and
# `<REVOKED_KIND>:<domain>:<generation>...` -- so THREE OF THE FOUR KINDS were
# silently dropped, and silent dropping is exactly what
# `failure_cause._compose`'s own note warns about: "one that discarded it
# quietly would hide that the producer had moved". Measured from the packaged
# command over a product-composed document; `tests/tools/test_attempt_diagnostics.py`
# holds these against the producer's own composition so a rename fails a test
# instead of emptying a report.
#
# THE CESSATION FORM KEEPS ITS LITERAL `*`, which is the producer's spelling and
# not a wildcard this reader expands: one name covers a component's intent and
# its outcome together.
_CESSATION_ABSENT = tuple("attempt.cessation-*:" + one
                          for one in ("expiry-reclaim", "settlement",
                                      "cancellation"))
_EXACT_ABSENT = _CESSATION_ABSENT + ("runtime.start-failed",
                                     "runtime.preparation-failed")
# The revoked record is emitted BOTH WAYS by the producer -- bare when no
# domain and generation are in hand, and suffixed `:<domain>:<generation>...`
# when they are -- so it is recognised by its OWNED KIND and that kind followed
# by a separator, never by an exact string this reader cannot predict. Measured
# through the real seam: the bare form is what a composed expiry actually
# carried, and a prefix-only rule dropped it.
_REVOKED_ABSENT_KIND = "resource-token.revoked"


def _absent_record(name):
    """Whether `name` is an absent-record kind this report is written against.

    POSITIVE RECOGNITION, unchanged in principle: a name reaches the report
    because it is one of the producer's kinds, never because it was present.
    """
    return (name in _EXACT_ABSENT or name == _REVOKED_ABSENT_KIND
            or name.startswith(_REVOKED_ABSENT_KIND + ":"))


def _unknown(why):
    """A member nobody established, with a BOUNDED reason.

    A MISSING COUNT IS NEVER A ZERO. `activity_bytes` absent means nobody has
    observed the stream; `0` means somebody observed it and it was empty.
    """
    return {"known": False, "value": None, "why": why}


def _fact(held, name, kinds, source):
    """ONE ALLOWLISTED MEMBER, decoded from the owned wrapper shape.

    THE ONE SHAPE, AND THE ONLY PLACE IT IS DECODED. The producer, the
    ordinary status document and this report all carry every diagnostic leaf
    as `{"known": true, "value": ..., "source": ...}` or `{"known": false,
    "value": null, "why": ...}` -- review340349 blocker 2 is what two
    different answers cost. So a recorded KNOWN value is reported as known,
    and an UNKNOWN keeps the producer's own bounded reason rather than having
    one invented here.

    NO NESTED-OBJECT FORWARDING, which survives the wrapper unchanged. A
    wrapper's `value` must match a declared scalar type (or a list of them for
    `effects`); a mapping, or a list where one was not declared, is reported
    as unrecognised. Forwarding an object nobody owns is how private text
    reaches a report, and a wrapper around it would not make it owned.

    A KNOWN ZERO IS A KNOWN ZERO. `renewals: 0` and `activity_bytes: 0` are
    answers somebody established; this never re-reads them as absences.
    """
    if not isinstance(held, dict):
        return _unknown("the enclosing value is not an object, so " + name
                        + " could not be read")
    if name not in held:
        return _unknown("the source document does not carry " + name)
    wrapper = held[name]
    if not isinstance(wrapper, dict) or "known" not in wrapper:
        return _unknown(name + " is not carried in the owned known/value "
                        "shape this report reads, so it was not forwarded")
    if not isinstance(wrapper["known"], bool):
        return _unknown(name + " declares a non-boolean 'known', so this "
                        "report cannot tell whether it was established")
    if not wrapper["known"]:
        # THE PRODUCER'S OWN BOUNDED REASON, CARRIED RATHER THAN REPLACED.
        # The whole point of the unknown shape is that it names what is
        # absent; substituting a reason of this report's own would discard it.
        return _unknown(name + " was not established by the diagnostic producer")
    value = wrapper.get("value")
    if isinstance(value, bool) and bool not in kinds:
        return _unknown(name + " is a boolean and this report declares it "
                        + "/".join(sorted(one.__name__ for one in kinds)))
    if not isinstance(value, kinds):
        return _unknown(name + " is a " + type(value).__name__
                        + " and this report declares it "
                        + "/".join(sorted(one.__name__ for one in kinds)))
    if isinstance(value, (list, tuple)) and not all(
            isinstance(one, str) for one in value):
        return _unknown(name + " is a list carrying something other than "
                        "names, so it was not forwarded")
    # THE SOURCE THE PRODUCER NAMED, kept where it is a name and replaced by
    # this report's own only where the producer named none. Per-fact
    # provenance is the obligation; inventing it would defeat it.
    if isinstance(value, str) and (len(value) > 512 or any(ord(c) < 32 for c in value)):
        return _unknown(name + " is not a bounded diagnostic value")
    return _known(list(value) if isinstance(value, tuple) else value, source)


def _typed(held, name, kinds, source):
    """One allowlisted member of a document that carries RAW SCALARS.

    The status document's own stage members are the Job manager's shape and
    not this diagnostic's, so they are read as what they are. Everything
    inside the diagnostic goes through `_fact` above.
    """
    if not isinstance(held, dict):
        return _unknown("the enclosing value is not an object, so " + name
                        + " could not be read")
    if name not in held:
        return _unknown("the source document does not carry " + name)
    value = held[name]
    if isinstance(value, bool) and bool not in kinds:
        return _unknown(name + " is a boolean and this report declares it "
                        + "/".join(sorted(one.__name__ for one in kinds)))
    if not isinstance(value, kinds):
        return _unknown(name + " is a " + type(value).__name__
                        + " and this report declares it "
                        + "/".join(sorted(one.__name__ for one in kinds)))
    return _known(value, source)


def _members(held, names, source):
    """The stage's own raw-scalar members."""
    return {name: _typed(held, name, kinds, source) for name, kinds in names}


def _facts(held, names, source):
    """The diagnostic's members, every one of them through the one decoder."""
    return {name: _fact(held, name, kinds, source) for name, kinds in names}


def _unrecognised(held, names):
    """What the document carried that this report does NOT forward.

    Reported by NAME ONLY and never by value: the point is to tell an operator
    that the upstream shape has moved, not to leak the thing that moved.
    """
    if not isinstance(held, dict):
        return ()
    declared = {name for name, _kinds in names}
    return ("undeclared members omitted",) if any(one not in declared for one in held) else ()


def _execution_limits(job):
    """THIS row's Job's own execution limits, positively projected.

    NEVER A SIBLING'S. The limits live on the Job and the rows are per stage,
    so the Job is threaded through `rows_of` rather than looked up again; a
    report that resolved them by job_id a second time could answer with the
    wrong Job's ceiling when two Jobs are in one document, which is exactly
    what the multi-Job case asserts against.

    RAW SCALARS, READ AS WHAT THEY ARE. The Job manager's own document carries
    these unwrapped, like the stage members, so they go through `_typed` and
    not through `_fact`. Nothing nested is forwarded: each boundary is rebuilt
    from the four members declared above, and a boundary name this build does
    not own is reported by NAME ONLY under `unrecognised`.

    ABSENT AND MALFORMED STAY HONEST. No limits at all, limits that are not an
    object, a boundary that is not an object, a seconds value that is not an
    integer -- each reads `unknown` with a bounded reason, and none of them is
    turned into a default this report invented.
    """
    held = job.get("execution_limits") if isinstance(job, dict) else None
    if not isinstance(held, dict):
        return {"envelope": _members(None, LIMIT_ENVELOPE_MEMBERS, "status"),
                "requested": {name: _unknown(
                    "this status document carries no execution limits for "
                    "this Job") for name, _kinds in _LIMIT_SETTING_MEMBERS},
                "boundaries": {name: _members(None, BOUNDARY_MEMBERS,
                                              "status")
                               for name in SOURCE_LIMIT_BOUNDARIES},
                "unrecognised": (),
                "why": ("this status document carries no execution limits for "
                        "this Job; nobody stated them here, which is not a "
                        "claim that none applied")}
    asked = held.get("requested")
    boundaries = held.get("boundaries")
    return {
        "envelope": _members(held, LIMIT_ENVELOPE_MEMBERS, "status"),
        # WHAT THE JOB ASKED FOR, separately from what took effect.
        "requested": {name: _typed(asked, name, kinds, "status.requested")
                      for name, kinds in _LIMIT_SETTING_MEMBERS},
        "boundaries": {
            name: _members(boundaries.get(name)
                           if isinstance(boundaries, dict) else None,
                           BOUNDARY_MEMBERS, "status.boundaries")
            for name in SOURCE_LIMIT_BOUNDARIES},
        "unrecognised": (_unrecognised(held, LIMIT_ENVELOPE_MEMBERS
                                       + (("requested", (dict,)),
                                          ("boundaries", (dict,))))
                         + _unrecognised_names(boundaries,
                                               SOURCE_LIMIT_BOUNDARIES)),
        "why": None}


def _unrecognised_names(held, owned):
    """Boundary names the document carried that this build does not own."""
    if not isinstance(held, dict):
        return ()
    return ("undeclared boundaries omitted",) \
        if any(one not in owned for one in held) else ()


def _completeness(cause, diagnostic, refused):
    """`complete`, `incomplete`, `absent` or `unavailable` -- FOUR facts.

    A STATUS DOCUMENT WHOSE FACTS ARE PARTIAL IS INCOMPLETE. That is what a
    deadline-bounded publication failure leaves behind, and it is neither a
    cessation nor an acceptance. The report says `incomplete` and names which
    members are missing; it does not guess why they are missing, because an
    unavailable final result NAMES NO CAUSE.

    AND `absent` IS NOT `unavailable`. Nobody having looked, and a diagnostic
    that is there and cannot be read, are different facts about different
    things -- the same distinction `SHUTDOWN.md` draws between an absent final
    report and an inaccessible one, and collapsing them would be the mistake
    this report exists partly to avoid.
    """
    if refused is not None:
        return {"state": "unavailable", "missing": (), "why": refused,
                "is_acceptance": False, "proves_cessation": False}
    if diagnostic is None:
        return {"state": "absent", "missing": (), "why": NO_DIAGNOSTIC,
                "is_acceptance": False, "proves_cessation": False}
    if cause is None:
        # THE DIAGNOSTIC IS THERE AND NO COMPONENT RECORDED ORDERING A
        # CESSATION. That is the composition's explicit `unknown`, which is an
        # answer and not a partial reading.
        return {"state": "incomplete", "missing": ("cause",),
                "why": "this diagnostic records no component having ordered "
                       "a cessation for this attempt; which component ended "
                       "it, if any did, is unknown, and an absent record is "
                       "not proof that nothing happened",
                "is_acceptance": False, "proves_cessation": False}
    missing = tuple(sorted(name for name, member in cause.items()
                           if isinstance(member, dict)
                           and not member.get("known")))
    if missing:
        return {"state": "incomplete", "missing": missing,
                "why": "this diagnostic is partial; an incomplete final "
                       "result is not an acceptance and is not proof of "
                       "cessation, and why it is partial is unknown",
                "is_acceptance": False, "proves_cessation": False}
    return {"state": "complete", "missing": (),
            "why": "every allowlisted diagnostic member was read",
            # EVEN A COMPLETE DIAGNOSTIC IS NOT AN ACCEPTANCE. The two
            # verdicts are constants here because no input may move them.
            "is_acceptance": False,
            # ...and whether cessation was established is the CAUSE's own
            # `cessation` member, which this report forwards and does not
            # re-decide.
            "proves_cessation": False}


def _locators(stage, diagnostic):
    """SAFE LOCATORS ONLY, plus the supported invocation shape.

    The attempt identity and whatever locator the MANAGER ITSELF recorded --
    the frozen result's `artifacts` -- under the allowlist. Device and inode
    travel labelled as an object identity and explicitly not a path.
    """
    workspace = (diagnostic or {}).get("workspace_object")
    artifacts = stage.get("artifacts") if isinstance(stage, dict) else None
    named = ()
    if isinstance(artifacts, list):
        # NAMES ONLY, and from the artifact's own `name`/`path` member. The
        # whole entry is never forwarded: an artifact document is somebody
        # else's shape and copying it wholesale is how unowned text travels.
        named = tuple(one.get("name") or one.get("path")
                      for one in artifacts if isinstance(one, dict)
                      and isinstance(one.get("name") or one.get("path"), str))
    return {
        "attempt_id": _typed(stage, "attempt_id", (str, type(None)), "status"),
        # THE MANAGER'S OWN RECORDED LOCATORS, names only.
        "recorded_artifacts": (_known(named, "status.artifacts")
                               if isinstance(artifacts, list) else
                               _unknown("this stage records no artifacts")),
        "workspace_object": dict(
            _facts(workspace or {}, WORKSPACE_MEMBERS, "diagnostics"),
            is_a_path=False,
            is_a_locator=False,
            why="a device and inode identify a workspace object; they are "
                "not a path and resolve no retained output on their own"),
        "supported_read": {
            "command": LOCATOR_COMMAND,
            "operator_must_supply": LOCATOR_OPERAND,
            "why": LOCATOR_WHY,
        },
    }


def _diagnostic_of(stage):
    """This stage's composed diagnostic, or why there is nothing to read.

    W333486 review340349 blocker 1: this now reads a member that ORDINARY
    VERSIONED STATUS ACTUALLY CARRIES. `job_manager/delegation.py`
    `ManagerOperations.observe` composes it from the control store it already
    holds and `job_manager/projection.py:_stage_status` emits it, so the bytes
    this report consumes are the producer's own rather than a fixture.

    Answers `(diagnostic, refusal)`: exactly one of the two is not `None`.
    """
    held = stage.get("attempt_diagnostics") if isinstance(stage, dict) else None
    if held is None:
        return None, None
    if not isinstance(held, dict):
        # AN OBSERVATION ABOUT THIS STAGE'S DIAGNOSTIC, not an exception that
        # abandons the rest of the report. A diagnostic whose top level is a
        # list is one unreadable member; the other stages were perfectly
        # readable and losing them would be the larger error.
        return None, ("this stage's attempt diagnostics is a "
                      + type(held).__name__ + " where this report reads an "
                      "object; it is unavailable as evidence and why it has "
                      "that shape is unknown")
    version = held.get("schema")
    if version != SOURCE_DIAGNOSTIC_SCHEMA:
        # OWNED IN BOTH DIRECTIONS, and it says WHICH version it was. An
        # older document reads as unavailable rather than being decoded
        # against a shape nobody promised, and a newer one is not silently
        # accepted.
        return None, ("this stage's attempt diagnostics declares schema "
                      + "an unsupported version"
                      + " and this report reads "
                      + SOURCE_DIAGNOSTIC_SCHEMA
                      + "; it is unavailable as evidence")
    if held.get("unavailable") is True:
        return None, "diagnostic evidence was unreadable; no cause inferred"
    if held.get("attempt_id") != stage.get("attempt_id"):
        return None, "diagnostic attempt does not match the current stage episode"
    execution = held.get("execution")
    runtime = stage.get("runtime")
    if isinstance(execution, dict) and isinstance(runtime, dict):
        attached = execution.get("runtime_id")
        if isinstance(attached, dict) and attached.get("known") is True and attached.get("value") != runtime.get("runtime_id"):
            return None, "diagnostic runtime does not match the stage observation"
    return held, None


def rows_of(document):
    """One report row per current stage, in the document's own order.

    THE IMPORTABLE HALF. A consumer that wants the projection rather than the
    command calls this; it opens nothing, spawns nothing and asks nothing what
    time it is.
    """
    snapshot = job_viewer.read_snapshot(document, received_at=None)
    # THE SNAPSHOT CARRIES HOW IT WAS READ as well as what was read, and this
    # report wants only the document. It takes the viewer's own reading rather
    # than parsing the bytes a second time: two parsers are two answers.
    held = getattr(snapshot, "document", snapshot)
    rows = []
    for job in (held.get("jobs") or []):
        for stage in (job.get("stages") or []):
            # THE JOB TRAVELS WITH ITS STAGE. See _execution_limits.
            rows.append(_row(stage, job))
    return rows


def _read(document):
    """The document, read ONCE, for callers that need more than the rows."""
    snapshot = job_viewer.read_snapshot(document, received_at=None)
    return getattr(snapshot, "document", snapshot)


def _source_time(held):
    """WHEN THE DOCUMENT WAS COMPOSED -- not when a runtime was observed.

    W333486 review-2026-10-22T18-18-00Z.md required this: a report about a
    missing or unknown historical cause particularly needs its snapshot's age,
    and it cannot derive one from a token expiry or from a wall clock it is
    forbidden to ask. It is reported as the instant the document states and
    NOTHING is concluded from it -- `freshness_verdict` stays null, and an old
    snapshot reads exactly as it was written rather than being judged stale.
    """
    return _members(held, SOURCE_TIME_MEMBERS, "status")


def _row(stage, job=None):
    diagnostic, refused = _diagnostic_of(stage)
    cause = None
    unknown = None
    absent = None
    if diagnostic is not None:
        got = diagnostic.get("cause")
        if isinstance(got, dict):
            cause = _facts(got, CAUSE_MEMBERS, "diagnostics.cause")
        # THE EXPLICIT UNKNOWN, FORWARDED WITH THE RECORDS IT NAMES. A
        # historical attempt that predates these records reaches exactly this
        # branch, and that is the correct answer rather than a shortfall: the
        # absence of a record is not proof that nothing happened, and the
        # names are what let an operator see which records were looked for.
        held = diagnostic.get("unknown")
        if isinstance(held, dict):
            unknown = "no durable cause was established for this attempt"
        named = diagnostic.get("absent_records")
        if isinstance(named, (list, tuple)):
            absent = tuple(one for one in named
                           if isinstance(one, str) and _absent_record(one))
    return {
        "stage": _members(stage, STAGE_MEMBERS, "status"),
        "cause": cause,
        "diagnostic_degradation": (
            _known(True, "ManagerOperations carrier observation; process-local")
            if isinstance(stage.get("diagnostic_degradation"), dict)
            and stage["diagnostic_degradation"].get("known") is True
            and stage["diagnostic_degradation"].get("value") is True else
            _unknown("no recording-failure carrier is available in this snapshot; absence does not prove recording succeeded")),
        "unknown_why": unknown,
        "absent_records": absent,
        "diagnostics_unavailable": refused,
        "execution": _facts(diagnostic.get("execution"), EXECUTION_MEMBERS,
                            "diagnostics.execution")
        if diagnostic is not None
        and isinstance(diagnostic.get("execution"), dict) else None,
        "token": _facts(diagnostic.get("token"), TOKEN_MEMBERS,
                        "diagnostics.token")
        if diagnostic is not None
        and isinstance(diagnostic.get("token"), dict) else None,
        # THE LIMITS, THE REVOCATION, THE COMPLETION AND THE TWO
        # PRE-EXECUTION ENDINGS, read off the diagnostic's top level.
        "axes": _facts(diagnostic, AXIS_MEMBERS, "diagnostics")
        if diagnostic is not None else None,
        "completeness": _completeness(cause, diagnostic, refused),
        # THIS ROW'S OWN JOB'S CEILINGS, requested beside effective, with the
        # units, the scope and the origin of each. See _execution_limits: the
        # Job is threaded in so a row can never answer with a sibling Job's.
        "execution_limits": _execution_limits(job),
        "unrecognised": _unrecognised(
            (diagnostic or {}).get("cause"), CAUSE_MEMBERS),
        "locators": _locators(stage if isinstance(stage, dict) else {},
                              diagnostic),
    }


def report(document):
    """The whole report: one envelope and one row per current stage."""
    return {"schema": SCHEMA,
            # THE DEPLOYMENT OBLIGATION, stated in the artifact itself.
            # `tools/stack_command.COMMANDS` serves this subcommand in SOURCE.
            # A source-level case is NOT proof that an already-installed
            # bundle carries it: the installed bundle is built separately and
            # this task rebuilds nothing. An operator reading this from a
            # bundle that predates the command will not find the subcommand,
            # and that is a deployment step rather than a defect here.
            "deployment_obligation":
                "tools/stack_command.COMMANDS serves 'attempt-diagnostics' in "
                "source; an installed bundle must be rebuilt before the "
                "deployed command carries it, and this report rebuilds "
                "nothing",
            "reads": "one status document, through tools/job_viewer.read_snapshot",
            # WHICH DIAGNOSTIC VERSION THIS REPORT OWNS, stated so a consumer
            # holding a row marked `unavailable` can see what it was read
            # against rather than guessing.
            "reads_diagnostics": SOURCE_DIAGNOSTIC_SCHEMA,
            "opens_no_store": True,
            "is_acceptance": False,
            "freshness_verdict": None,
            "freshness_why": "no freshness policy has been selected for these "
                             "facts, so this report states instants and "
                             "declines to judge them",
            # THE SNAPSHOT'S OWN TIME, distinguished from the other two
            # instants this report carries. See _source_time.
            "source_observed_at": _source_time(_read(document)),
            "source_time_why": ("`source_observed_at` is when the status "
                                "document was composed; a row's "
                                "`execution.observed_at` is when its runtime "
                                "was looked at and a cause's `at` is when the "
                                "cessation was ordered. Three different facts, "
                                "and no freshness verdict is derived from any "
                                "of them"),
            "rows": rows_of(document)}


def main(argv=None, *, stream=sys.stdout):
    """`baton-v12-stack attempt-diagnostics <status.json>` -- and nothing else.

    One positional operand, read as a file. No store path, no instance name
    and no engine operand, because accepting one would make this a reader that
    can be pointed at something other than a document.
    """
    operands = list(sys.argv[1:] if argv is None else argv)
    if len(operands) != 1:
        print("usage: attempt-diagnostics <status-document.json>; this report "
              "is a pure projection over one status document and takes no "
              "store, instance or engine operand", file=sys.stderr)
        return 2
    try:
        with open(operands[0], "rb") as handle:
            source = handle.read()
        result = report(source)
    except (OSError, ValueError, TypeError, KeyError, job_viewer.ViewerRefusal):
        print("attempt diagnostics unavailable: input is unreadable or not a supported status document", file=sys.stderr)
        return 2
    json.dump(result, stream, indent=2, sort_keys=True, default=list)
    stream.write("\n")
    return 0
