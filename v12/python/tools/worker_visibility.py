"""W324214 -- the minimum read-only worker visibility view.

WHAT IT IS. A bounded PROJECTION over one status document the Job Manager
already publishes (`baton.v12.job-status/7`): one row per current stage, with
the worker, allocation, runtime, exchange and activity facts that document
actually carries, each labelled with WHERE IT CAME FROM and -- when the source
records one -- WHEN IT WAS OBSERVED. It answers "which worker is this stage
on, and what has anybody actually seen of it".

WHAT IT IS NOT, and each of these is a decision rather than an omission:

  IT IS NOT TELEMETRY COLLECTION. There is no provider call, no engine call,
  no CPU or network sampling, no terminal scraping, no transcript and no
  context restoration here. The view reads a file an operator already has.
  A collector would be a second source of truth about liveness, and the one
  this deployment trusts is the manager's own observation.

  IT HAS NO STORE AND NO CLOCK. No database is opened, no serving factory is
  constructed, no command is spawned. It never asks what time it is, because
  every age it could compute would be a statement about how long THIS PROGRAM
  has been looking rather than about the worker. `--snapshot` names the one
  input, and `observed_at` in that input is the SNAPSHOT QUERY TIME -- when
  the manager looked at its own stores -- which is not when a worker was last
  heard from and is never reported as if it were.

  IT DECIDES NOTHING ABOUT FRESHNESS. No freshness threshold has been
  selected for this Work, so freshness is reported as `unknown` with the
  reason `no freshness policy selected`. That is deliberate: a view that
  invented a window would be publishing a policy nobody chose, and an old
  timestamp must not be able to acquire `fresh` or `healthy` merely because
  somebody read the same file again. This projection is a pure function of
  the document, so re-reading an unchanged source answers the same facts with
  the same instants, every time.

  IT INVENTS NO FACT AND NO INSTANT. Every member is either KNOWN, with its
  source JSON field path, or UNKNOWN with a bounded reason. A missing count is
  never a zero; an observed integer zero IS a known zero, because the producer
  can really record one and "nobody has observed anything" and "this manager
  observed zero bytes at 12:04" are different answers. A quiet runtime is
  neither healthy nor offline -- the producer's own axis word is forwarded and
  nothing here maps it onto a verdict.

  IT FORWARDS NO NESTED OBJECT. Every block below is an explicit allowlist of
  named members with a declared type. A view that forwarded whole nested
  documents would publish whatever a future producer adds to them --
  credentials, raw logs, a command argv, a private-context path -- and would
  do it silently. The worker-authored entry names an exchange reports as
  `foreign` are deliberately not among the members: they are bytes a container
  chose, and naming them here would make this view their publisher.

  AND IT ATTACHES NOTHING TO AN ATTEMPT THAT DID NOT EARN IT. Activity carries
  an attempt id and is compared against the stage's CURRENT attempt; an
  allocation carries an assignment id and episode and is compared against both.
  An observation belonging to a previous episode is reported as unknown with
  the reason, never silently re-attached and never filled in from history.
  The runtime block carries no attempt id at all in this contract -- so this
  view says the association is unverifiable here rather than claiming it.

HOW IT RELATES TO THE EXISTING SURFACES. `tools/job_viewer.py` is the
operator's terminal view of the same document and owns the reading of it:
`read_snapshot` validates the schema and the nested structure and bounds the
input, and this module calls it rather than growing a second reader. What is
new here is the JSON PROJECTION -- per-fact provenance, per-fact unknown
reasons and the explicit attempt-association checks -- published under its own
version, `baton.v12.worker-visibility/1`. `baton.v12.job-status/7` is
unchanged by this Work.

ONE DELIBERATE DISAGREEMENT WITH THE VIEWER, stated out loud: the terminal
view renders an observed `0` as `unknown`, which is a DISPLAY rule about a
count an operator reads as "running and idle". This surface is a FACT
projection for a consumer, so an observed zero is reported as a known zero
with its observation time and its explicit `bytes` unit. Neither surface
renders an absence as a count.
"""

import argparse
import datetime
import json
import sys

from baton_v12.job_manager import documents

from tools import job_viewer

__all__ = ["SCHEMA", "SOURCE_SCHEMA", "MAX_SNAPSHOT_BYTES", "MAX_TEXT",
           "MAX_INSTANT_TEXT", "MAX_ACTIVITY_BYTES", "VisibilityRefusal",
           "visibility", "rows_of", "read_status", "main"]

# WHAT THIS VIEW PUBLISHES, versioned on its own. A consumer that must not
# mistake this projection for the status document has to be able to tell which
# one it is holding.
SCHEMA = "baton.v12.worker-visibility/1"

# AND THE ONE IT READS, taken from the producer's own constant rather than
# spelled again here. A copy would be a second place to update.
SOURCE_SCHEMA = documents.STATUS_SCHEMA

# THE INPUT BOUNDS, which are the existing viewer's own. They bound what this
# program holds; the manager's input rules are untouched by anything here.
MAX_SNAPSHOT_BYTES = job_viewer.MAX_SNAPSHOT_BYTES
MAX_INSTANT_TEXT = job_viewer.MAX_INSTANT_TEXT
MAX_ACTIVITY_BYTES = job_viewer.MAX_ACTIVITY_BYTES

# How much of a source TEXT member may become a reported value. Identities,
# participants, lanes and digests are all far inside this; a longer one is a
# document this view does not recognise rather than a value to republish.
MAX_TEXT = 256

# THE PRODUCER'S OWN FROZEN INSTANT GRAMMAR, and the shape of it.
#
# REVIEW 2026-10-18T17-37-19Z: this used `datetime.fromisoformat`, which
# accepts a great deal this deployment never writes -- a date with no time at
# all, a naive local time with no zone, a six-digit fraction, an offset other
# than `Z`. Every one of those was reported as a KNOWN source instant, which
# is this surface publishing a value whose meaning it had guessed. The
# contract is `worker_manager.boundaries.GRAMMAR`: exactly
# `0000-00-00T00:00:00.000Z`, and a real moment on the calendar.
#
# IT IS A COPY, DELIBERATELY, which is the opposite of what this module does
# for `SOURCE_SCHEMA` -- and the reason is the boundary rather than taste.
# Importing that grammar means importing the Worker Manager package, which is
# the owner of the control store this view must not be able to open. So the
# grammar is restated here and `tests/tools/test_worker_visibility.py` holds
# the copy against `boundaries.instant` vector for vector, so it cannot drift
# quietly.
#
# `0` MEANS ONE ASCII DIGIT and every other position is itself. `strptime`
# alone is not the grammar: it accepts a one-digit month and a four-digit
# fraction, and `2026-9-02T00:00:00.0000Z` is the same length as a durable
# instant without being one.
_INSTANT_SHAPE = "0000-00-00T00:00:00.000Z"
_INSTANT_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


class VisibilityRefusal(Exception):
    """What this program answers with instead of reporting something untrue.

    ITS MESSAGES CARRY NO INPUT. Every sentence below is a literal plus, at
    most, a Python type name -- never a member of the document. An error
    string assembled out of an untrusted document is a way for that document
    to choose what lands in a log, and this view refuses rather than echoing.
    """


def _refuse(message):
    raise VisibilityRefusal(message)


# -- the vocabulary of absence ----------------------------------------------
#
# ONE CLOSED SET OF REASONS, because "unknown" alone is the answer this Work
# exists to replace. A consumer branching on these needs them to be stable
# strings rather than prose assembled at the call site.

ABSENT = "the source document does not carry this member"
NULL = "the source document carries this member as null"
PARENT_NULL = ("the source document carries the observation this member would "
               "be part of as null")
MALFORMED = ("the source member is not the type this contract names, so it is "
             "unknown rather than evidence")
MALFORMED_BLOCK = ("the source document carries this observation as something "
                   "other than a document, so none of its members is evidence")
UNSUPPORTED = "unsupported by this status contract"
NO_FACT = "this fact is unknown, so there is no observation of it to time"
NO_OBSERVATION_TIME = ("this status contract records no observation time for "
                       "this fact, and this view does not invent one")
NO_RUNTIME = "this status document reports no runtime for this stage"
NO_EXCHANGE = ("this status document reports no exchange read for this stage, "
               "which is nobody looked rather than an idle worker")
NO_ACTIVITY = ("this status document reports no activity projection for this "
               "stage's attempt")
NOTHING_OBSERVED = ("this attempt is recorded and this manager has observed "
                    "none of its session stream yet")
NO_ALLOCATION = ("this stage's current attempt holds no worker reservation in "
                 "this document")
NO_EPISODE = "this stage has no current episode"
FOREIGN_ALLOCATION = ("the reported reservation does not belong to this "
                      "stage's current attempt and episode, so it is not "
                      "attached to it")
FOREIGN_ACTIVITY = ("the reported activity names another attempt, so it is "
                    "not attached to this one")
NO_EPISODE_RECORD = ("this stage's episode history carries no live record for "
                     "the current episode and attempt; an earlier episode's "
                     "record is not read in its place")

# WHY FRESHNESS IS NOT ANSWERED. Selected for this Work: no threshold.
NO_FRESHNESS_POLICY = "no freshness policy selected"
FRESHNESS_NOTE = ("an instant in this document is a historical observation; "
                  "re-reading the same source cannot make it fresh, and this "
                  "view reports no fresh, stale, healthy or offline verdict")

# WHAT THE SNAPSHOT'S OWN INSTANT IS, and what it is not.
QUERY_TIME_NOTE = ("the instant the manager queried its own stores to assemble "
                   "this status document; it is not a worker contact time and "
                   "not an activity observation time")

# WHY AN ASSOCIATION IS OR IS NOT PROVED HERE.
ACTIVITY_ASSOCIATED = ("the activity projection names an attempt id and it "
                       "equals this stage's current attempt")
ALLOCATION_ASSOCIATED = ("the reservation's assignment_id and episode equal "
                         "this stage's current attempt and episode")
RUNTIME_UNVERIFIABLE = ("this status contract carries no attempt id on the "
                        "runtime, so this view cannot verify which attempt it "
                        "belongs to and does not claim one")
EXCHANGE_UNVERIFIABLE = ("this status contract carries no attempt id on the "
                         "exchange, so this view cannot verify which attempt "
                         "it belongs to and does not claim one")

# -- the member types ------------------------------------------------------

_TEXT = "text"
_INTEGER = "integer"
_INSTANT = "instant"
_COUNT = "count"

# THE ALLOWLISTS. Each is (member, type), and nothing outside them is read or
# reported. See the module docstring for why a whole nested object is never
# forwarded.

# The scheduler's reservation, in `stage_allocations`' own spelling.
ALLOCATION_MEMBERS = (("assignment_id", _TEXT), ("stage_id", _TEXT),
                      ("episode", _INTEGER), ("worker_id", _TEXT),
                      ("participant", _TEXT), ("lane", _TEXT),
                      ("generation", _INTEGER),
                      ("allocation_state", _TEXT),
                      ("selection_outcome", _TEXT),
                      ("preferred_worker_id", _TEXT),
                      ("reserved_at", _INSTANT),
                      ("recovery_required_at", _INSTANT),
                      ("released_at", _INSTANT),
                      # THE RESERVED WORKER'S CONFIGURED PROFILE IDENTITY,
                      # which is a fact about the pool rather than about
                      # anything observed of a running process.
                      ("worker_profile_name", _TEXT),
                      ("worker_profile_digest", _TEXT),
                      ("variant", _TEXT), ("separation_class", _TEXT))

# The runtime axis as the projection publishes it: four members, and the
# attempt id is NOT one of them.
RUNTIME_MEMBERS = (("runtime_id", _TEXT), ("execution_runtime", _TEXT))

# The fixed assignment that travels with the runtime.
ASSIGNMENT_MEMBERS = (("participant", _TEXT), ("generation", _INTEGER))
WORK_REF_MEMBERS = (("work_id", _TEXT), ("authority_uuid", _TEXT))

# The exchange, reported as the deployment answered it. `foreign` is
# deliberately absent -- see the module docstring.
EXCHANGE_MEMBERS = (("transport", _TEXT), ("sequence_id", _TEXT),
                    ("state", _TEXT))
EXCHANGE_COMMAND_MEMBERS = (("sequence_id", _TEXT),
                            ("command_digest", _TEXT))
EXCHANGE_TERMINAL_MEMBERS = (("ending", _TEXT), ("fault_code", _TEXT),
                             ("manifest_digest", _TEXT))
# A contained unreadability, as the producer reduced it: the KIND of
# disagreement and never the prose, which is composed from bytes a worker
# wrote.
EXCHANGE_UNREADABLE_MEMBERS = (("category", _TEXT), ("code", _TEXT))

# The stage's own identities, from the status document's stage document.
STAGE_MEMBERS = (("stage_id", _TEXT), ("job_id", _TEXT), ("kind", _TEXT),
                 ("state", _TEXT), ("work_id", _TEXT), ("episode", _INTEGER),
                 ("attempt_id", _TEXT), ("offer_id", _TEXT))

# The stage's CONFIGURED profile, which is what was asked for rather than
# anything observed of a worker.
PROFILE_MEMBERS = (("profile_name", _TEXT), ("profile_digest", _TEXT))

JOB_MEMBERS = (("job_id", _TEXT), ("submission_id", _TEXT))

# -- facts -----------------------------------------------------------------


def _instant_text(value):
    """One recorded instant in the PRODUCER'S grammar, or None.

    BOTH HALVES, because the producer's own boundary is both: the shape, so
    that two instants compare lexicographically the way every reader of this
    deployment's documents assumes, and the calendar, because
    `2026-99-99T99:99:99.999Z` has the shape and names no moment.

    PARSED TO VALIDATE AND NEVER TO COMPUTE. This view reports the producer's
    own text; parsing is how it refuses to republish something that is not an
    instant at all. No age is derived from it, here or anywhere below -- that
    would need a clock, and this program has none.

    AND A NEAR MISS IS NOT AN INSTANT. A value this deployment never writes is
    one whose meaning this view would be choosing -- which zone a naive time
    is in, which moment of a bare date -- so it is unknown with a bounded
    reason rather than a fact with an invented meaning.
    """
    if type(value) is not str or len(value) > MAX_INSTANT_TEXT:
        return None
    if len(value) != len(_INSTANT_SHAPE):
        return None
    for held, want in zip(value, _INSTANT_SHAPE):
        if want == "0":
            # ASCII DIGITS ONLY, and spelled rather than asked: `str.isdigit`
            # is true of digits in other scripts that no durable instant of
            # this deployment is written in.
            if not ("0" <= held <= "9"):
                return None
        elif held != want:
            return None
    try:
        datetime.datetime.strptime(value, _INSTANT_FORMAT)
    except ValueError:
        return None
    return value


def _checked(value, kind):
    """One source value held to its declared type, or None for malformed."""
    if kind is _TEXT:
        return value if type(value) is str and 0 < len(value) <= MAX_TEXT \
            else None
    if kind is _INTEGER:
        # `bool` is an `int` in this language and is not a count or an
        # episode number; a document carrying one is malformed rather than
        # carrying zero or one.
        return value if type(value) is int and type(value) is not bool \
            and abs(value) <= MAX_ACTIVITY_BYTES else None
    if kind is _COUNT:
        # ZERO IS INSIDE THE DOMAIN, because the producer can really observe
        # and record a zero total. Negative is not: the producer refuses one.
        return value if type(value) is int and type(value) is not bool \
            and 0 <= value <= MAX_ACTIVITY_BYTES else None
    if kind is _INSTANT:
        return _instant_text(value)
    raise AssertionError("unknown member type")        # pragma: no cover


def _no_time(reason=NO_OBSERVATION_TIME, source=None):
    return {"known": False, "value": None, "source": source,
            "unknown_reason": reason}


def _at(value, source):
    return {"known": True, "value": value, "source": source,
            "unknown_reason": None}


def _known(value, source, observed_at=None):
    return {"known": True, "value": value, "source": source,
            "unknown_reason": None,
            "observed_at": observed_at if observed_at is not None
            else _no_time()}


def _unknown(source, reason):
    return {"known": False, "value": None, "source": source,
            "unknown_reason": reason, "observed_at": _no_time(NO_FACT)}


def _member(held, name, kind, path, *, observed_at=None):
    """One allowlisted member of one source document, with its field path.

    ABSENT, NULL AND MALFORMED ARE THREE ANSWERS and they stay three. A
    consumer asking "why do I not know this" gets a different sentence for a
    member the producer never wrote, a member it wrote as null, and a member it
    wrote as something this contract does not name.
    """
    source = (path + "." + name) if path else name
    if held is None:
        # THE PARENT IS ABSENT, NOT THIS MEMBER. `exchange.command: null` is
        # "no command has been published", and reporting that as a malformed
        # document would be this view calling an ordinary state a defect.
        return _unknown(source, PARENT_NULL)
    if type(held) is not dict:
        return _unknown(source, MALFORMED_BLOCK)
    if name not in held:
        return _unknown(source, ABSENT)
    value = held[name]
    if value is None:
        return _unknown(source, NULL)
    checked = _checked(value, kind)
    if checked is None:
        return _unknown(source, MALFORMED)
    return _known(checked, source, observed_at=observed_at)


def _members(held, names, path, *, observed_at=None):
    return {name: _member(held, name, kind, path, observed_at=observed_at)
            for name, kind in names}


def _absent_members(names, path, reason):
    """Every allowlisted member, unknown for ONE stated reason.

    THE SHAPE DOES NOT CHANGE WITH THE ANSWER. A consumer that had to handle
    a missing key as well as an unknown fact has two ways to read an absence,
    and one of them is `0`.
    """
    return {name: _unknown((path + "." + name) if path else name, reason)
            for name, _kind in names}


def _association(verified, basis):
    """Whether THIS observation was proved to belong to THIS attempt."""
    return {"verified": verified, "basis": basis}


# -- the envelope ----------------------------------------------------------


def _document(source):
    """One status document, validated, from a mapping, text or bytes.

    THE READING IS THE EXISTING VIEWER'S. `job_viewer.read_snapshot` owns the
    schema check, the nested structural check and the input bound; a second
    reader here would be a second answer to "is this document readable", and
    the two would disagree on the day it mattered.

    ITS REFUSALS ARE RESTATED RATHER THAN FORWARDED, and that is this Work's
    own rule rather than a complaint about that reader: the viewer's sentences
    name the offending value so an operator at a terminal can see it, and this
    surface is a JSON answer that may be logged by something that is not a
    person. So what crosses this boundary is a fixed sentence plus, at most, a
    Python type name.
    """
    held = source
    if isinstance(held, (bytes, bytearray, str)):
        if isinstance(held, str):
            held = held.encode("utf-8")
        if len(held) > MAX_SNAPSHOT_BYTES:
            _refuse("this status document is larger than the "
                    + str(MAX_SNAPSHOT_BYTES) + " bytes this view holds; "
                    "refusing rather than reporting an unknown subset of the "
                    "stages")
        try:
            held = json.loads(bytes(held).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            _refuse("this status document is not readable as one JSON "
                    "document")
    if type(held) is not dict:
        _refuse("a status snapshot is one JSON document, not "
                + type(held).__name__)
    if held.get("schema") != SOURCE_SCHEMA:
        # AN UNSUPPORTED VERSION IS NOT A DOCUMENT TO READ THE RECOGNISED
        # PARTS OUT OF, and the rejected value is not echoed back.
        _refuse("this view reads " + SOURCE_SCHEMA + " and this document "
                "declares another schema (" + type(held.get("schema")).__name__
                + "); an unsupported version is refused rather than partly "
                "read")
    _envelope(held)
    try:
        job_viewer.read_snapshot(held, received_at=None)
    except job_viewer.ViewerRefusal:
        _refuse("this document's nested structure is not the one "
                + SOURCE_SCHEMA + " describes; the view refuses rather than "
                "reporting an unknown subset of the stages")
    _enumerable(held)
    return held


def _enumerable(held):
    """EVERY STAGE THIS DOCUMENT HAS CAN BE FOUND, or no row is published.

    DELIBERATELY STRICTER THAN THE VIEWER, and the asymmetry is this Work's
    own decision rather than a complaint about that reader. `_shaped` treats a
    Job whose `stages` member is null as a Job with nothing to draw, which is
    right for a terminal list: it renders what it can read and an operator can
    see for themselves that a Job's row is empty.

    THIS SURFACE'S WHOLE OUTPUT IS ONE ROW PER CURRENT STAGE. Under the same
    tolerance, `{"stages": null}` answered `stages: []` -- a confident,
    well-formed, machine-readable "no stage is in any state", published to a
    consumer with nothing to notice. That is the same defect as rendering a
    missing count as zero, one level up: an absence dressed as an
    observation.

    REVIEW 2026-10-18T17-37-19Z found exactly that. `stages` is a REQUIRED
    member of `job.status`, so absent and null are both malformed, and a row
    set this view cannot enumerate is a refusal rather than a shorter answer.
    """
    for job in held["jobs"]:
        stages = job.get("stages")
        if type(stages) is not list:
            _refuse("a Job in this document carries its stages as "
                    + type(stages).__name__ + " where " + SOURCE_SCHEMA
                    + " names a list; refusing rather than publishing a row "
                    "set this document does not support")


def _envelope(held):
    """The five envelope members this contract names, by type.

    A MALFORMED ENVELOPE IS REFUSED RATHER THAN PARTLY REPORTED. `observed_at`
    in particular: it is the only instant the document has about ITSELF, the
    whole reason it can be read without a clock, and a document whose own
    query time is not an instant is not one to publish rows out of.
    """
    if _instant_text(held.get("observed_at")) is None:
        _refuse("this document's observed_at is not a bounded instant; the "
                "snapshot query time is the one instant this view needs from "
                "the envelope and it is not readable")
    if type(held.get("canonical")) is not bool:
        _refuse("this document's canonical member is not a boolean, so "
                "whether the manager was read at all is not readable")
    if held.get("incarnation") is not None \
            and _checked(held.get("incarnation"), _TEXT) is None:
        _refuse("this document's incarnation is neither absent nor a bounded "
                "identity")
    # `jobs` IS REQUIRED AND IS A LIST. The `status` contract names it among
    # its required members, so a document without one is not a status document
    # that happens to be quiet -- and answering `stages: []` for it would be
    # this view reporting "nothing is running" about a document that said
    # nothing at all.
    if type(held.get("jobs")) is not list:
        _refuse("this document carries no jobs list of the kind "
                + SOURCE_SCHEMA + " requires; refusing rather than reporting "
                "an unknown subset of the stages")


# -- the blocks ------------------------------------------------------------


def _allocation(stage, path, attempt, episode):
    """The scheduler's reservation for THIS stage's current attempt.

    THREE ANSWERS, AND `unallocated` IS NOT ONE OF THE OTHER TWO. A stage with
    no reservation is a real and ordinary state -- queued, or claimed before
    the scheduler acted -- and it is a different answer from a document whose
    allocation member is unreadable, which is a different answer again from a
    reservation that belongs to another attempt. Folding any of those into
    "unknown" alone is what makes an operator guess.

    AND THE WORKER IS NOT THE RUNTIME. A stage can be reserved on a worker
    before any runtime exists, so this block is reported beside the runtime
    rather than folded into it.
    """
    source = path + ".allocation"
    held = stage.get("allocation")
    if held is None:
        return {"presence": "unallocated", "reason": NO_ALLOCATION,
                "source": source,
                "attempt_association": _association(False, NO_ALLOCATION),
                "facts": _absent_members(ALLOCATION_MEMBERS, source,
                                         NO_ALLOCATION)}
    if type(held) is not dict:
        return {"presence": "unknown", "reason": MALFORMED_BLOCK,
                "source": source,
                "attempt_association": _association(False, MALFORMED_BLOCK),
                "facts": _absent_members(ALLOCATION_MEMBERS, source,
                                         MALFORMED_BLOCK)}
    # THE ASSOCIATION IS PROVED BEFORE ANY MEMBER IS REPORTED. A reservation
    # made for the episode that ended is not this episode's worker, and
    # reporting its worker id here is exactly the "old attempt's allocation on
    # a new one" this Work must not do.
    if not attempt["known"] or not episode["known"] \
            or _checked(held.get("assignment_id"), _TEXT) != attempt["value"] \
            or _checked(held.get("episode"), _INTEGER) != episode["value"]:
        return {"presence": "unknown", "reason": FOREIGN_ALLOCATION,
                "source": source,
                "attempt_association": _association(False, FOREIGN_ALLOCATION),
                "facts": _absent_members(ALLOCATION_MEMBERS, source,
                                         FOREIGN_ALLOCATION)}
    return {"presence": "allocated", "reason": None, "source": source,
            "attempt_association": _association(True, ALLOCATION_ASSOCIATED),
            # THE RESERVATION'S OWN INSTANTS ARE REPORTED AS FACTS and are not
            # bound to the state as its observation time. `reserved_at`,
            # `recovery_required_at` and `released_at` are the moments this
            # store recorded transitions; which of them explains the current
            # state is the reader's inference and not a time this view
            # attaches to a value the contract gave no time to.
            "facts": _members(held, ALLOCATION_MEMBERS, source)}


def _runtime(stage, path):
    """The runtime identity and the producer's own execution axis word.

    THE AXIS WORD IS FORWARDED AND NEVER MAPPED. `quiescent` is not "offline",
    `running` is not "healthy", and `uncertain` is not "failed": those are the
    manager's axis values and turning them into a verdict here would be this
    view deciding something it cannot observe. A consumer that wants a verdict
    has to say whose policy it is applying.

    AND ABSENCE IS NOT A VERDICT EITHER. No runtime means no runtime has been
    reported for this stage -- not that the worker is down.
    """
    source = path + ".runtime"
    held = stage.get("runtime")
    if held is None:
        return {"presence": "not-reported", "reason": NO_RUNTIME,
                "source": source,
                "attempt_association": _association(False, NO_RUNTIME),
                "facts": _absent_members(RUNTIME_MEMBERS, source, NO_RUNTIME),
                "assignment": {
                    "presence": "not-reported", "reason": NO_RUNTIME,
                    "source": source + ".assignment",
                    "facts": {
                        **_absent_members(ASSIGNMENT_MEMBERS,
                                          source + ".assignment", NO_RUNTIME),
                        **_absent_members(WORK_REF_MEMBERS,
                                          source + ".assignment.work_ref",
                                          NO_RUNTIME)}}}
    if type(held) is not dict:
        return {"presence": "unknown", "reason": MALFORMED_BLOCK,
                "source": source,
                "attempt_association": _association(False, MALFORMED_BLOCK),
                "facts": _absent_members(RUNTIME_MEMBERS, source,
                                         MALFORMED_BLOCK),
                "assignment": {
                    "presence": "unknown", "reason": MALFORMED_BLOCK,
                    "source": source + ".assignment",
                    "facts": {
                        **_absent_members(ASSIGNMENT_MEMBERS,
                                          source + ".assignment",
                                          MALFORMED_BLOCK),
                        **_absent_members(WORK_REF_MEMBERS,
                                          source + ".assignment.work_ref",
                                          MALFORMED_BLOCK)}}}
    return {"presence": "reported", "reason": None, "source": source,
            # THE PRODUCER SHAPE, REVALIDATED: `projection._stage_status`
            # publishes exactly runtime_id, execution_runtime, assignment and
            # activity. The attempt id the Worker Manager's reader carries is
            # NOT among them, so there is nothing here to compare against this
            # stage's attempt and this view says so instead of assuming.
            "attempt_association": _association(False, RUNTIME_UNVERIFIABLE),
            "facts": _members(held, RUNTIME_MEMBERS, source),
            "assignment": _assignment(held, source + ".assignment")}


def _assignment(runtime, source):
    """The four-part identity activation fixed, as the runtime carries it."""
    held = runtime.get("assignment")
    if held is None or type(held) is not dict:
        reason = NULL if held is None else MALFORMED_BLOCK
        return {"presence": "not-reported" if held is None else "unknown",
                "reason": reason, "source": source,
                "facts": {
                    **_absent_members(ASSIGNMENT_MEMBERS, source, reason),
                    **_absent_members(WORK_REF_MEMBERS,
                                      source + ".work_ref", reason)}}
    return {"presence": "reported", "reason": None, "source": source,
            "facts": {**_members(held, ASSIGNMENT_MEMBERS, source),
                      **_members(held.get("work_ref"), WORK_REF_MEMBERS,
                                 source + ".work_ref")}}


def _exchange(stage, path):
    """Whether a turn is happening inside the container, as answered.

    `null` IS "NOBODY LOOKED" AND IS NOT "IDLE". The producer is explicit that
    a control plane holding no exchange read is a different answer from an
    exchange that has been read and carries no command yet, and this view
    keeps them apart.

    THE RECEIPT'S INSTANT IS THE WORKER'S OWN `accepted_at` and is reported as
    that fact's time -- not as the time of the exchange STATE, which this
    contract gives no instant at all.
    """
    source = path + ".exchange"
    held = stage.get("exchange")
    if held is None or type(held) is not dict:
        reason = NO_EXCHANGE if held is None else MALFORMED_BLOCK
        return {"presence": "not-read" if held is None else "unknown",
                "reason": reason, "source": source,
                "attempt_association": _association(False, reason),
                "facts": _absent_members(EXCHANGE_MEMBERS, source, reason),
                "command": _absent_members(EXCHANGE_COMMAND_MEMBERS,
                                           source + ".command", reason),
                "receipt": {"accepted_at": _unknown(
                    source + ".receipt.accepted_at", reason)},
                "terminal": _absent_members(EXCHANGE_TERMINAL_MEMBERS,
                                            source + ".terminal", reason),
                "unreadable": _absent_members(EXCHANGE_UNREADABLE_MEMBERS,
                                              source + ".unreadable", reason)}
    accepted = _member(held.get("receipt"), "accepted_at", _INSTANT,
                       source + ".receipt")
    return {"presence": "reported", "reason": None, "source": source,
            "attempt_association": _association(False, EXCHANGE_UNVERIFIABLE),
            "facts": _members(held, EXCHANGE_MEMBERS, source),
            "command": _members(held.get("command"),
                                EXCHANGE_COMMAND_MEMBERS,
                                source + ".command"),
            # THE RECEIPT IS ITS OWN FACT WITH ITS OWN TIME, and that time is
            # the instant it carries rather than a time this view chose.
            "receipt": {"accepted_at": accepted},
            "terminal": _members(held.get("terminal"),
                                 EXCHANGE_TERMINAL_MEMBERS,
                                 source + ".terminal"),
            "unreadable": _members(held.get("unreadable"),
                                   EXCHANGE_UNREADABLE_MEMBERS,
                                   source + ".unreadable")}


def _activity(stage, path, attempt):
    """How much of the worker's session stream this manager has OBSERVED.

    IT IS BYTES. Not tokens, not a percentage of anything, not model progress:
    the producer's ruling is explicit that repeated noise grows the count, a
    long quiet model call leaves it unchanged, and a provider may expose no
    measurable stream at all. The unit is published beside the number so a
    consumer cannot read it as the other thing.

    A ZERO IS A ZERO AND AN ABSENCE IS NOT. The producer accepts an observed
    total of zero, stamps it, and answers `{bytes_observed: null,
    observed_at: null}` for a recorded attempt nobody has observed yet. Those
    are two different facts and this block reports them as two.

    AND THE ATTEMPT IS CHECKED, because the activity projection is the one
    observation in this contract that names its own attempt. A count belonging
    to the episode that ended is not this episode's progress.
    """
    runtime = stage.get("runtime")
    source = path + ".runtime.activity"
    if type(runtime) is not dict:
        reason = NO_RUNTIME if runtime is None else MALFORMED_BLOCK
        return _quiet_activity(source, "unknown", reason)
    held = runtime.get("activity")
    if held is None:
        return _quiet_activity(source, "not-observed", NO_ACTIVITY)
    if type(held) is not dict:
        return _quiet_activity(source, "unknown", MALFORMED_BLOCK)
    named = _checked(held.get("attempt_id"), _TEXT)
    if not attempt["known"] or named is None or named != attempt["value"]:
        return _quiet_activity(source, "unknown", FOREIGN_ACTIVITY)
    # THE COUNT'S OBSERVATION TIME IS THE PRODUCER'S OWN INSTANT, carried ON
    # the count rather than beside it, so a consumer cannot report the number
    # without the moment -- and when the producer recorded no instant, the
    # count's time is unknown WITH THE REASON rather than filled in from the
    # snapshot's query time.
    when = _member(held, "observed_at", _INSTANT, source)
    count = _member(held, "bytes_observed", _COUNT, source,
                    observed_at=(_at(when["value"], when["source"])
                                 if when["known"]
                                 else _no_time(when["unknown_reason"],
                                               when["source"])))
    if count["known"]:
        presence, reason = "observed", None
    elif count["unknown_reason"] in (NULL, ABSENT):
        # A RECORDED ATTEMPT NOBODY HAS OBSERVED YET. The producer answers
        # exactly this shape for one, and it is not a zero.
        presence, reason = "not-observed", NOTHING_OBSERVED
    else:
        presence, reason = "unknown", count["unknown_reason"]
    return {"presence": presence, "reason": reason, "source": source,
            "unit": "bytes",
            "what": ("bytes of the worker's native session stream this "
                     "manager has observed; not tokens, not model progress, "
                     "and not proof that useful work happened"),
            "attempt_association": _association(True, ACTIVITY_ASSOCIATED),
            "facts": {"bytes_observed": count, "observed_at": when},
            "freshness": {"state": "unknown", "reason": NO_FRESHNESS_POLICY,
                          "note": FRESHNESS_NOTE}}


def _quiet_activity(source, presence, reason):
    """An activity block with nothing in it, and the reason it is empty.

    NEVER A ZERO HERE. A missing count rendered as `0` is the exact failure
    this surface exists to prevent: it reads as "observed, and empty".
    """
    return {"presence": presence, "reason": reason, "source": source,
            "unit": "bytes",
            "what": ("bytes of the worker's native session stream this "
                     "manager has observed; not tokens, not model progress, "
                     "and not proof that useful work happened"),
            "attempt_association": _association(False, reason),
            "facts": {"bytes_observed": _unknown(source + ".bytes_observed",
                                                 reason),
                      "observed_at": _unknown(source + ".observed_at",
                                              reason)},
            "freshness": {"state": "unknown", "reason": NO_FRESHNESS_POLICY,
                          "note": FRESHNESS_NOTE}}


def _contact():
    """WHEN THE WORKER WAS LAST HEARD FROM, which this contract does not say.

    AND THE SNAPSHOT'S OWN INSTANT IS NOT IT. `observed_at` says when the
    manager queried its stores; presenting that as a contact time would report
    the READER'S behaviour as the WORKER'S, which is the whole family of defect
    this Work is bounded against. So this is unknown, with the reason, always.
    """
    return {"presence": "unsupported", "reason": UNSUPPORTED,
            "note": ("this status contract carries no worker contact instant; "
                     "the snapshot query time is not one"),
            "facts": {"last_contact": {
                "known": False, "value": None, "source": None,
                "unknown_reason": UNSUPPORTED,
                "observed_at": _no_time(UNSUPPORTED)}},
            "freshness": {"state": "unknown", "reason": NO_FRESHNESS_POLICY,
                          "note": FRESHNESS_NOTE}}


def _context():
    """CONTEXT ACCOUNTING, which this contract does not carry either.

    No part of this view reads a transcript, a private context path or a
    provider session, so there is nothing here to report and nothing to
    estimate. Unknown, with the reason.
    """
    return {"presence": "unsupported", "reason": UNSUPPORTED,
            "note": ("this status contract carries no context accounting, and "
                     "this view reads no transcript, provider session or "
                     "private context path to obtain one"),
            "facts": {name: {"known": False, "value": None, "source": None,
                             "unknown_reason": UNSUPPORTED,
                             "observed_at": _no_time(UNSUPPORTED)}
                      for name in ("context_used", "context_limit")}}


def _episode_opened(stage, path, episode, attempt):
    """The CURRENT episode's own opening instant, from its own record.

    MATCHED ON BOTH IDENTITIES AND ONLY WHILE LIVE. The episode history is
    append-only and an abandoned episode keeps its record, so matching on the
    episode number alone would hand a restarted stage the instant of the
    attempt that ended. There is no fallback to the latest record: a stage
    whose current episode has no live record answers unknown.
    """
    source = path + ".episodes"
    if not episode["known"] or not attempt["known"]:
        return _unknown(source, NO_EPISODE)
    for index, one in enumerate(stage.get("episodes") or []):
        if type(one) is not dict:
            continue
        if _checked(one.get("episode"), _INTEGER) != episode["value"] \
                or _checked(one.get("attempt_id"), _TEXT) != attempt["value"]:
            continue
        if one.get("ended_state") is not None or one.get("ended_at") is not None:
            # THE DOCUMENT CONTRADICTS ITSELF: this stage names an episode its
            # own history reports as ended. That is unknown with a bounded
            # reason rather than an instant to publish.
            continue
        return _member(one, "opened_at", _INSTANT,
                       source + "[" + str(index) + "]")
    return _unknown(source, NO_EPISODE_RECORD)


# -- the rows --------------------------------------------------------------


def _row(job, stage, path):
    """One current stage, including one nobody has assigned to a worker.

    EVERY STAGE GETS A ROW. A queued stage with no reservation, no runtime and
    no activity is precisely the row an operator asking "why is nothing
    moving" needs to see; omitting it would answer that question with silence.
    """
    identities = _members(stage, STAGE_MEMBERS, path)
    attempt = identities["attempt_id"]
    episode = identities["episode"]
    return {
        "source": path,
        "job": _members(job, JOB_MEMBERS, _parent(path)),
        "stage": {**identities,
                  "episode_opened_at": _episode_opened(stage, path, episode,
                                                       attempt)},
        # CONFIGURED, AND KEPT APART FROM EVERYTHING OBSERVED. This is the
        # profile the submission asked for; it is not evidence that any worker
        # ever ran under it.
        "configured_profile": {
            "presence": "configured",
            "note": ("the profile identity this stage was submitted with; a "
                     "configured identity is not an observation of a runtime"),
            "facts": _members(stage, PROFILE_MEMBERS, path)},
        "allocation": _allocation(stage, path, attempt, episode),
        "runtime": _runtime(stage, path),
        "exchange": _exchange(stage, path),
        "activity": _activity(stage, path, attempt),
        "contact": _contact(),
        "context": _context(),
        "freshness": {"state": "unknown", "reason": NO_FRESHNESS_POLICY,
                      "note": FRESHNESS_NOTE},
    }


def _parent(path):
    return path.split(".stages[")[0]


def rows_of(document):
    """Every current stage's row, in the document's own order.

    THE IMPORTABLE HALF, and the one a consumer that only wants the rows
    should call. A test or a consumer that wants the projection rather than
    the command calls this or `visibility`; neither opens anything, spawns
    anything or asks what time it is.
    """
    return _rows(_document(document))


def _rows(held):
    """The rows of an ALREADY VALIDATED document, validated once.

    Separate from `rows_of` so `visibility` does not read the same document
    through the structural check twice -- the check is the same answer both
    times, and running it twice would invite a reader to think the second one
    meant something.
    """
    rows = []
    for index, job in enumerate(held.get("jobs") or []):
        prefix = "jobs[" + str(index) + "]"
        for ordinal, stage in enumerate(job.get("stages") or []):
            rows.append(_row(job, stage,
                             prefix + ".stages[" + str(ordinal) + "]"))
    return rows


def visibility(document, *, read_at=None):
    """The whole view: one envelope, and one row per current stage.

    `read_at` IS THE CALLER'S OWN READ TIME AND CHANGES NOTHING. It is
    reported under its own name, beside -- never instead of -- the snapshot's
    query time, and no fact below is derived from it. Passing a different one
    answers the same rows, which is the property that keeps an old observation
    from becoming fresh by being read again.
    """
    held = _document(document)
    return {
        "schema": SCHEMA,
        "source_schema": SOURCE_SCHEMA,
        "snapshot": {
            # THE SNAPSHOT'S OWN INSTANT, NAMED FOR WHAT IT IS.
            "query_time": _at(held["observed_at"], "observed_at"),
            "query_time_note": QUERY_TIME_NOTE,
            # WHETHER THE MANAGER WAS READ AT ALL: `false` is the difference
            # between "nothing is running" and "nobody looked", and a consumer
            # must not read an empty view as a quiet deployment.
            "canonical": _at(held["canonical"], "canonical"),
            "incarnation": _member(held, "incarnation", _TEXT, ""),
        },
        # THE LOCAL READ TIME, SEPARATELY NAMED OR HONESTLY ABSENT.
        "read": ({"local_read_time": _at(_read_time(read_at), None),
                  "note": ("the caller's own read time; it is not a source "
                           "fact and no fact in this view is derived from it")}
                 if read_at is not None else
                 {"local_read_time": _no_time(
                     "the caller supplied no local read time"),
                  "note": ("the caller's own read time; it is not a source "
                           "fact and no fact in this view is derived from it")}),
        "freshness": {"state": "unknown", "reason": NO_FRESHNESS_POLICY,
                      "note": FRESHNESS_NOTE},
        "stages": _rows(held),
    }


def _read_time(read_at):
    """The caller's own instant, held to the same rule a source instant is.

    IT IS REFUSED RATHER THAN REPUBLISHED UNCHECKED. This operand is the only
    value in the whole view that does not come from the document, so it is the
    one place something arbitrary could reach the output; bounding it here
    keeps "no invented or unbounded value is published" true of every member.
    """
    held = _checked(read_at, _INSTANT)
    if held is None:
        _refuse("a local read time is a bounded instant, and it is reported "
                "beside the snapshot query time rather than instead of it")
    return held


# -- the command -----------------------------------------------------------


def read_status(place):
    """A bounded read of ONE status file the operator names.

    THE BOUND IS THE VIEWER'S, and the read is one `open` of the path the
    operand gives. No locator inside the document is followed or opened: a
    status document carries the manager's own artifact locators, and a
    visibility view that went looking at them would be reading whatever those
    name rather than reporting what this document says.
    """
    with open(place, "rb") as handle:
        return handle.read(MAX_SNAPSHOT_BYTES + 1)


def main(argv=None, *, stream=sys.stdout):
    parser = argparse.ArgumentParser(
        prog="worker_visibility",
        description="Read-only JSON view of worker visibility facts in one "
                    "status document. Performs no act.")
    parser.add_argument("--snapshot", required=True,
                        help="path to a status document written by "
                             "`job_manager ... status`")
    taken = parser.parse_args(argv)
    try:
        held = visibility(read_status(taken.snapshot))
    except VisibilityRefusal as refusal:
        # THE REFUSAL IS JSON TOO, so a consumer does not have to parse prose
        # to find out it got nothing. The message is this module's own
        # sentence; see `VisibilityRefusal`.
        json.dump({"schema": SCHEMA, "refused": str(refusal)}, stream,
                  indent=2, sort_keys=True)
        print("", file=stream)
        return 2
    except OSError as failure:
        json.dump({"schema": SCHEMA,
                   "refused": "this status document could not be read ("
                              + type(failure).__name__ + "); the view does "
                              "not go looking elsewhere for it"},
                  stream, indent=2, sort_keys=True)
        print("", file=stream)
        return 2
    json.dump(held, stream, indent=2, sort_keys=True)
    print("", file=stream)
    return 0


if __name__ == "__main__":                                  # pragma: no cover
    sys.exit(main())
