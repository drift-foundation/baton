"""W198667 — the attempt's RAW OUTPUT, kept, and kept apart from everything else.

The owner's words, 2026-09-17: *"I'm not concerned about logged credentials --
this is dev use -- and credentials aren't printed out anyway. We need to capture
evidence so we don't chase tails."* For these private development deployments
that ruling supersedes the September-1 W61599 prohibition on durable raw output
and the W39357/W43972 credential-free-log restrictions **to the extent they
require discarding these streams**. It is not a claim that arbitrary process
output cannot contain a credential, and nothing here reads a credential in
order to log it.

THREE NAMESPACES, AND THIS IS THE THIRD. An attempt already has a RESULT
surface (`/output`, whose declared entries are validated and frozen) and a
PROTOCOL surface (`/run/baton/exchange`, whose documents are receipts, states
and terminals). Raw output belongs to neither: a log written under the result
surface would be validated as an output nobody declared, and one written under
the protocol surface would be a document the manager tries to read as an event.
So this is its own delivery, its own mount and its own target, and the
separation is the reason the module exists rather than a preference.

CREATED BEFORE THE RUNTIME STARTS, exactly as `exchange.materialize` is and for
the same reason: the mounts are fixed when the container is created, so a
namespace that did not exist then is one nothing will ever hold.

AND RE-ENTERED WITHOUT DESTROYING ANYTHING. `adopt` is what a restart uses. The
required outcome is that partial evidence survives error, abnormal termination
and restart, so a second incarnation appends beside the first rather than
clearing the room -- a log directory emptied by the act of looking at it again
would lose exactly the evidence this exists for.

MISSING IS NOT EMPTY, and the vocabulary keeps them apart. A stream that was
never opened, one that was opened and could not be written, one truncated at a
ceiling and one that ended on a drain's clock rather than at EOF are four
different facts, and `capture_state` says which. An empty successful run is a
fifth, and it is the one thing none of the others may be reported as.

LOGS ARE EVIDENCE AND NEVER INSTRUCTIONS. Nothing in this manager reads a log
to decide anything: not a receipt, not a completion, not a workflow step. The
readers below exist for an operator.
"""

import os
import stat

from .. import attempt_log_format
from ..attempt_log_format import FormatRefusal
from ..contracts import ContractRefusal
from ..contracts.errors import name_value
from . import boundaries, workspaces

__all__ = ["AttemptLogs", "CAPTURE_STATES", "LOG_DIR", "LOG_TARGET",
           "MAX_FOLLOW", "MAX_READ", "MAX_REASON", "MAX_STATUS", "STREAMS",
           "adopt", "capture_state", "locators", "materialize", "read",
           "named", "record_capture", "status_name", "follow"]

# WHERE THE CONTAINER SEES IT. A constant, not an operand: a path a container
# could be told is a path a container can be pointed at wrongly, which is the
# whole reason the environment transport was retired (W26291).
LOG_TARGET = attempt_log_format.TARGET

# The delivery's own directory mode, taken from the owner that ESTABLISHES it
# rather than restated. `adopt_workspace_group` chmods to
# `workspaces.WORKSPACE_DIR`, so a second constant here would be a second thing
# to keep true and `adopt` would refuse its own rooms the day they disagreed.
LOG_DIR = workspaces.WORKSPACE_DIR

# THE STREAMS THIS DELIVERY NAMES, and they are named rather than discovered so
# that a reader can say a log is MISSING. Discovery can only ever report what
# is there.
#
# `worker` is the wrapper's own earliest output -- W198667 review 2026-09-18:
# a provider-side tee cannot retain a failure that happens before the provider
# starts, and the reported incident was exactly such a failure.
# THE FORMAT HAS ONE OWNER and this is a reference to it, not a second copy.
# `baton_v12.attempt_log_format` imports nothing from `baton_v12` and travels
# into worker images the way `source_profiles` does, because a worker writes
# these declarations and a manager reads them -- and two implementations of one
# format is how they drift.
STREAMS = attempt_log_format.STREAMS

# WHAT A CAPTURE CAN HONESTLY BE. `absent` is "this stream was never created",
# which is a different sentence from `empty`, and reporting the first as the
# second is the defect this vocabulary exists to prevent.
CAPTURE_STATES = ("absent", "inaccessible", "empty", "live", "captured",
                  "truncated", "partial", "failed")

# WHERE THE WRITER'S OWN WORD IS KEPT, so it survives a restart and reaches
# every reader. Review 2026-09-18T01-04-54Z R1: a state held only in a return
# value was lost the moment anybody else looked.
#
# ONE SIDECAR PER STREAM, not one document for all of them. Review
# 2026-09-18T01-15-42Z R2: a shared document was loaded, modified and replaced
# without serialization, so two writers racing at the load lost one
# declaration -- and atomic REPLACEMENT of a document is not an atomic UPDATE
# of an entry in it. See `status_name`.
#
# AND BOUNDED, because metadata this manager reads back is input like any
# other: `MAX_STATUS` bounds the file and `MAX_REASON` the prose inside it.
MAX_STATUS = attempt_log_format.MAX_STATUS
MAX_REASON = attempt_log_format.MAX_REASON

# THE THREE A WRITER MAY DECLARE. Completion is NOT among them by accident:
# `captured` is a conclusion about a finished stream and only `finished()`
# reaches it, because file existence and a momentary EOF prove neither.
DECLARABLE = attempt_log_format.DECLARABLE

# How much a read hands back at once, and how much a follow reports having
# skipped. An operator surface is not a search engine and a log is not bounded
# by anything this manager controls.
MAX_READ = 1 << 20
MAX_FOLLOW = 1 << 16

# THE STAGING IDENTITY LIVES WITH THE ACT THAT USES IT, in the format module.
# Kept reachable under this name because it is the seam a case forces a
# deterministic collision through -- and because per-call NAMING is all it is.
# Review 2026-09-18T02-02-21Z corrected my own gloss on this: the pid plus a
# counter is not secrecy and not unguessability. `O_CREAT|O_EXCL|O_NOFOLLOW`
# and the creation-ownership tracking are what make the act safe.


class AttemptLogs:
    """One attempt's log room: where it is here, and what it is called there.

    A TYPED DELIVERY RATHER THAN A PATH, for the reason `ExchangeDelivery` is
    one: a function that took a string would admit any string, and what makes
    this room this attempt's is that this manager made it under that identity.
    """

    __slots__ = ("attempt_id", "root")

    def __init__(self, *, attempt_id, root):
        object.__setattr__(self, "attempt_id",
                           boundaries.identity(attempt_id, "an attempt id"))
        object.__setattr__(self, "root",
                           boundaries.text(root, "an attempt log root"))

    def __setattr__(self, name, value):
        raise ContractRefusal("policy", "denied",
                              "an attempt log delivery is frozen once made")

    def __eq__(self, other):
        return (type(other) is AttemptLogs
                and (other.attempt_id, other.root) == (self.attempt_id,
                                                       self.root))

    def __hash__(self):
        return hash((self.attempt_id, self.root))

    @property
    def log_root(self):
        """This attempt's own room under the delivery root.

        NAMED BY THE ATTEMPT, which is what keeps concurrent attempts apart --
        the required outcome asks for that explicitly, and two attempts sharing
        a directory would interleave two runs into one file.
        """
        return os.path.join(self.root, self.attempt_id)

    def place(self, stream):
        return os.path.join(self.log_root, named(stream) + ".log")

    @property
    def native_root(self):
        """Where a provider's OWN session files are kept, if it writes any.

        SEPARATE FROM THE STREAMS, because they are a different kind of thing:
        the streams are what this deployment captured and this is what the
        provider itself produced. An absent native root means the provider
        wrote none, and that is reported as `absent` rather than as an empty
        capture.
        """
        return os.path.join(self.log_root, "native")

    def mounts(self):
        """The ONE bind this delivery authorizes, and its direction.

        A triple rather than a mount document, exactly as `ExchangeDelivery
        .mounts` answers: `writable` is not a parameter a caller may relax.
        A read-only log room is a worker that cannot leave the evidence this
        whole delivery exists for, and `oci._log_mounts` refuses one either
        way -- this is the composer, that is the boundary, and they agree
        because the constant has one owner.
        """
        return ((self.log_root, LOG_TARGET, True),)


def materialize(root, *, attempt_id, workspace_group):
    """Make this attempt's log room BEFORE the runtime starts.

    Refuses an existing room rather than reusing one: a fresh attempt writing
    into another attempt's evidence is the concurrency defect the required
    outcome names. A restart uses `adopt`.
    """
    place = boundaries.text(root, "an attempt log delivery root")
    delivery = AttemptLogs(attempt_id=attempt_id, root=place)
    os.makedirs(delivery.log_root, mode=0o700, exist_ok=False)
    os.makedirs(delivery.native_root, mode=0o700, exist_ok=False)
    held = _gid(workspace_group)
    workspaces.adopt_workspace_group({"workspace": delivery.log_root}, held)
    workspaces.adopt_workspace_group({"workspace": delivery.native_root}, held)
    return delivery


def adopt(root, *, attempt_id, workspace_group):
    """Re-enter an existing log room WITHOUT destroying what is in it.

    THE RESTART CASE, and the reason it is a separate function. Partial
    evidence surviving abnormal termination and restart is a required outcome,
    so this proves the room is the one this manager made -- descriptor-relative
    and no-follow, as `exchange._own_directory` does -- and then leaves every
    byte alone.
    """
    place = boundaries.text(root, "an attempt log delivery root")
    delivery = AttemptLogs(attempt_id=attempt_id, root=place)
    opened = _own_directory(delivery.log_root, "an attempt log room")
    os.close(opened)
    if not os.path.isdir(delivery.native_root):
        os.makedirs(delivery.native_root, mode=0o700, exist_ok=True)
        workspaces.adopt_workspace_group({"workspace": delivery.native_root},
                                         _gid(workspace_group))
    return delivery


def _own_directory(place, what):
    try:
        opened = os.open(place, os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY)
    except OSError as failure:
        _denied(f"{what} is not a directory this manager made "
                f"({type(failure).__name__}); an entry of another type is "
                f"state this build cannot account for")
    held = os.stat(opened)
    if stat.S_IMODE(held.st_mode) != LOG_DIR:
        os.close(opened)
        _denied(f"{what} is mode {oct(stat.S_IMODE(held.st_mode))} and this "
                f"manager established {oct(LOG_DIR)}; a delivery whose modes "
                f"have moved is not the one it wrote")
    return opened


def _gid(workspace_group):
    """The configured group, from this manager's own frozen answer only."""
    if not isinstance(workspace_group, workspaces.WorkspaceGroup):
        _denied("an attempt log delivery takes this deployment's minted "
                "workspace group, not a bare integer")
    return workspace_group.gid


def named(stream):
    """The format's allowlist, in this manager's own refusal vocabulary.

    The RULE is `attempt_log_format.named`'s, applied at every public entry here
    and at the two internals that join a suffix, before a descriptor is opened
    or a room is held. What this adds is the translation: a worker's plain
    exception type is not part of the manager's vocabulary, and every other
    refusal a caller of this module can receive is a `ContractRefusal`.
    """
    try:
        return attempt_log_format.named(stream)
    except FormatRefusal as refusal:
        _denied(str(refusal))


def status_name(stream):
    """One sidecar per stream. The name is the format's; the hold is this
    module's, so a bad operand refuses as a `ContractRefusal` here too."""
    named(stream)
    return attempt_log_format.status_name(stream)


def record_capture(delivery, stream, state, *, reason=None):
    """The WRITER's own word about ONE stream, made durable and CONFINED.

    THE ACT IS `attempt_log_format.write_declaration`'S, and every property it
    carries was a defect here first: the staging entry is CREATED rather than
    opened, only an entry this call made is ever removed, and every byte is
    written before the replace so nothing is published that was not written
    whole. What this function owns is the manager's half -- the typed delivery,
    the room, and the refusal vocabulary.
    """
    named(stream)
    room = _room(delivery)
    try:
        return attempt_log_format.write_declaration(room, stream, state,
                                                    reason=reason)
    except FormatRefusal as refusal:
        _denied(str(refusal))
    finally:
        os.close(room)


def _declaration(delivery, stream):
    """This stream's declaration, read INSIDE the room and VALIDATED.

    The reading is `attempt_log_format.read_declaration`'s, so a worker and this
    manager believe exactly the same bytes. What is added here is the room --
    and the rule that a room this manager cannot even hold is REPORTED as
    corrupt rather than raised, because `locators` is the operator's whole
    picture and one unreadable room must not take the other streams' answers
    away with it.
    """
    named(stream)
    room = None
    try:
        room = _room(delivery)
    except ContractRefusal as refusal:
        return {"state": "corrupt", "why": refusal.message}
    try:
        return attempt_log_format.read_declaration(room, stream)
    finally:
        os.close(room)


# WHAT EACH DECLARED STATE MEANS, from the one place that owns the words. A
# second table here would be a second meaning for the same string.
_DECLARED = attempt_log_format.DECLARED


def capture_state(delivery, stream, *, reported=None):
    """What this stream HONESTLY is: the writer's word, then the file.

    R1, in the order that matters. THE WRITER'S WORD COMES FIRST AND SURVIVES
    THE ABSENCE OF A FILE. A writer that could not open the stream at all has
    `failed` to say and nothing to say it in, and answering `absent` there --
    "no log was created" -- reports a failure as a run that had nothing to say.

    THEN THE FILE, and the three answers it can give are kept apart. `absent`
    is "there is no such entry". `inaccessible` is "I could not ask", which a
    permission failure produces and which is NOT absence. Only after both of
    those does size decide between `empty` and content.

    AND CONTENT ALONE IS NEVER COMPLETENESS. A stream with bytes and no
    declaration is `live`: something is being written and no writer has said it
    finished. `captured` is reached only when a writer declared `finished`,
    because file existence and a momentary end of file prove neither.
    """
    named(stream)
    if reported is not None and reported not in CAPTURE_STATES \
            and reported not in DECLARABLE:
        _denied(f"{name_value(reported)} is not a capture state; the states "
                f"are {', '.join(CAPTURE_STATES)}")
    declared = _declaration(delivery, stream) or {}
    corrupt = declared.get("state") == "corrupt"
    if corrupt:
        # R3: A CORRUPT DECLARATION IS REPORTED, NEVER RAISED, and never
        # silently becomes an assertion of completeness. The stream's own log
        # is still readable and the other streams still answer.
        declared = {}
    if reported is not None:
        declared = {"declared": reported,
                    "reason": _DECLARED.get(reported, "reported by the caller")}
    said = declared.get("declared")
    found = _measured(delivery, stream)
    note = {"declaration": "corrupt" if corrupt else
            ("declared" if said else "none")}
    if said == "failed":
        # THE ONE STATE THAT OUTRANKS AN ABSENT FILE.
        return {**note, "stream": stream, "state": "failed", "bytes": found["bytes"],
                "why": declared.get("reason", _DECLARED["failed"]),
                "file": found["state"]}
    if found["state"] in ("absent", "inaccessible"):
        return {**note, "stream": stream, "state": found["state"], "bytes": 0,
                "why": found["why"], "file": found["state"]}
    if said in ("truncated", "partial"):
        return {**note, "stream": stream, "state": said, "bytes": found["bytes"],
                "why": declared.get("reason", _DECLARED[said]),
                "file": found["state"]}
    if found["bytes"] == 0 and said != "finished":
        return {**note, "stream": stream, "state": "empty", "bytes": 0,
                "why": "the log exists and nothing has been written to it",
                "file": found["state"]}
    if said == "finished":
        return {**note, "stream": stream, "state": "captured", "bytes": found["bytes"],
                "why": _DECLARED["finished"], "file": found["state"]}
    return {**note, "stream": stream, "state": "live", "bytes": found["bytes"],
            "why": "bytes are here and no writer has said this stream ended; "
                   "completeness is unknown",
            "file": found["state"]}


def _measured(delivery, stream):
    """What the ENTRY is, asked no-follow and relative to the held room.

    R2. `capture_state` used a following `stat` and `read` an ordinary `open`,
    so a symlink at a stream's name was followed and a sibling attempt's file
    was returned as this attempt's own captured output. The room is opened
    once, every entry is named RELATIVE to that descriptor, and nothing is
    followed.
    """
    named(stream)
    room = None
    try:
        room = _room(delivery)
        held = os.lstat(stream + ".log", dir_fd=room)
    except ContractRefusal as refusal:
        # A ROOM THIS MANAGER CANNOT HOLD IS REPORTED, NOT RAISED. `locators`
        # is the operator's whole picture, and one unreadable room must not
        # take the other five streams' answers away with it.
        return {"state": "inaccessible", "bytes": 0, "why": refusal.message}
    except FileNotFoundError:
        return {"state": "absent", "bytes": 0,
                "why": "no log was created for this stream"}
    except OSError as failure:
        return {"state": "inaccessible", "bytes": 0,
                "why": f"this log could not be inspected "
                       f"({type(failure).__name__}); that is not the same as "
                       f"its absence"}
    finally:
        if room is not None:
            os.close(room)
    if stat.S_ISLNK(held.st_mode):
        return {"state": "inaccessible", "bytes": 0,
                "why": "this stream's name is a link, and a log this manager "
                       "would have to follow out of the attempt's own room is "
                       "not this attempt's evidence"}
    if not stat.S_ISREG(held.st_mode):
        return {"state": "inaccessible", "bytes": 0,
                "why": "this stream's name is not a regular file; a special "
                       "file is not a log and reading one could block"}
    return {"state": "present", "bytes": held.st_size, "why": ""}


def _room(delivery):
    """The attempt's own directory, opened no-follow. Closed by the caller."""
    try:
        return os.open(delivery.log_root,
                       os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY)
    except OSError as failure:
        _denied(f"this attempt's log room could not be opened "
                f"({type(failure).__name__}); a room this manager cannot hold "
                f"is not one it will read a log out of")


def locators(delivery, *, reported=None):
    """Every stream this attempt has, where it is, and what it honestly is.

    THE OPERATOR SURFACE, and it needs no engine inspection: the paths are this
    manager's own and are readable whether the container is running, stopped or
    gone.
    """
    said = dict(reported or {})
    found = {"attempt_id": delivery.attempt_id,
             "log_root": delivery.log_root,
             "target": LOG_TARGET,
             "streams": [], "native": None}
    for stream in STREAMS:
        one = capture_state(delivery, stream, reported=said.get(stream))
        one["place"] = delivery.place(stream)
        found["streams"].append(one)
    found["native"] = _native(delivery)
    return found


def _native(delivery):
    """The provider's own session files, listed WITHOUT following anything.

    R2: this followed its path too. The room is held, the native entry is
    checked no-follow on that descriptor, and a link where the directory
    should be is reported rather than walked.
    """
    room = None
    try:
        room = _room(delivery)
        held = os.lstat("native", dir_fd=room)
        if stat.S_ISLNK(held.st_mode) or not stat.S_ISDIR(held.st_mode):
            return {"state": "inaccessible",
                    "place": delivery.native_root, "entries": [],
                    "why": "the native corner is a link or not a directory, "
                           "and this manager does not follow it out of the "
                           "attempt's own room"}
        opened = os.open("native", os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY,
                         dir_fd=room)
    except ContractRefusal as refusal:
        return {"state": "inaccessible", "place": delivery.native_root,
                "entries": [], "why": refusal.message}
    except FileNotFoundError:
        return {"state": "absent", "place": delivery.native_root,
                "entries": [],
                "why": "this provider wrote no native session output"}
    except OSError as failure:
        return {"state": "inaccessible", "place": delivery.native_root,
                "entries": [],
                "why": f"the native corner could not be read "
                       f"({type(failure).__name__})"}
    finally:
        if room is not None:
            os.close(room)
    try:
        with os.scandir(opened) as listing:
            # THE CAPTURE'S OWN RECORD IS NOT A SESSION FILE. It lives in this
            # corner because it describes these bytes and must outlive the
            # process that wrote them; presenting it as something the PROVIDER
            # wrote would be this reader inventing one more session file on
            # every attempt.
            entries = sorted(one.name for one in listing
                             if one.name != attempt_log_format.RETENTION)
    except OSError as failure:
        entries, state = [], "inaccessible"
        return {"state": state, "place": delivery.native_root, "entries": [],
                "why": f"the native corner could not be listed "
                       f"({type(failure).__name__})"}
    finally:
        os.close(opened)
    return {"state": "captured" if entries else "empty",
            "place": delivery.native_root, "entries": entries,
            "why": ("the provider's own session files are here" if entries
                    else "the room exists and the provider wrote nothing in it")}



# HOW MANY BYTES MAY BE READ BEYOND A BOUND to finish a character the caller
# has already begun. Three is the most any UTF-8 sequence can still need.
_COMPLETING = 3


def _incomplete(payload):
    """`(held, still_needed)` for a started-but-unfinished trailing sequence.

    NOT A DECODER. An incomplete sequence can only be at the END, so this looks
    at the last few bytes and stops at the first lead byte it can account for.
    """
    for back in range(1, min(_COMPLETING + 1, len(payload)) + 1):
        one = payload[-back]
        if one < 0x80:
            return 0, 0
        if one >= 0xC0:
            wanted = (2 if one < 0xE0 else 3 if one < 0xF0 else 4)
            return (back, wanted - back) if back < wanted else (0, 0)
    return 0, 0


def _completing(handle, payload):
    """EXACTLY the bytes that finish a character this slice cut in half.

    EXACTLY, and a first cut read three. Three bytes can carry the whole of a
    NEXT character's lead, so topping up by a fixed amount introduced the very
    split it was added to remove -- `→←↑↓` came back with a replacement
    character in the middle of it. What is read is what is missing.
    """
    _held, wanted = _incomplete(payload)
    if not wanted:
        return b""
    try:
        return os.read(handle, wanted)
    except OSError:
        return b""


def _whole(payload, at_end, state):
    """The prefix of these bytes that decodes without a partial character.

    AFTER THE TOP-UP, a trailing incomplete sequence means the FILE ends
    mid-character -- the writer has not written the rest yet, or never will.
    Those are different facts and they get different answers:

      A LIVE WRITER may still append the remainder, so the bytes are held back
      and the follower asks again. Progress is guaranteed because the top-up
      already completed anything the bound merely cut.

      A FINISHED WRITER will not, so what is there is all there will be and it
      is reported with replacement rather than withheld forever. Terminal
      malformed data is the writer's, and a reader that waited for it would
      never finish -- which is exactly the hang this Work exists to remove.
    """
    held, wanted = _incomplete(payload)
    if not wanted:
        return payload, at_end
    if state in ("live", "empty"):
        return payload[:-held], False
    return payload, at_end


def read(delivery, stream, *, from_byte=0, limit=MAX_READ):
    """A bounded window onto one stream, with what it HONESTLY is beside it.

    R1: this had no way to be told the writer's word and answered `captured`
    for a declared prefix. It asks `capture_state` now, which reads the durable
    declaration, so every reader agrees.

    R2: and it opens the entry RELATIVE TO THE HELD ROOM, no-follow and
    non-blocking, then proves the DESCRIPTOR is a regular file. A path checked
    before an ordinary `open` is a different object from the one that gets
    opened, and `O_NONBLOCK` is what keeps a special file from wedging a reader
    that promised to be bounded.
    """
    named(stream)
    if type(from_byte) is not int or from_byte < 0:
        _denied("a log read starts at a whole number of bytes")
    if type(limit) is not int or not 0 < limit <= MAX_READ:
        _denied(f"a log read is bounded by {MAX_READ} bytes")
    found = capture_state(delivery, stream)
    if found["file"] != "present":
        return {**found, "from_byte": from_byte, "bytes_read": 0, "text": "",
                "at_end": True}
    room = None
    handle = None
    try:
        room = _room(delivery)
        handle = os.open(stream + ".log",
                         os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                         dir_fd=room)
        held = os.fstat(handle)
        if not stat.S_ISREG(held.st_mode):
            return {**found, "state": "inaccessible", "from_byte": from_byte,
                    "bytes_read": 0, "text": "", "at_end": False,
                    "why": "the opened entry is not a regular file"}
        os.lseek(handle, from_byte, os.SEEK_SET)
        payload = os.read(handle, limit)
        # TOP UP A SPLIT CHARACTER RATHER THAN WITHHOLDING IT. Review
        # 2026-09-18T03-39-32Z [R1]: withholding alone could make NO PROGRESS
        # -- a completed log holding `€x` followed at `--bound 1` withheld the
        # one lead byte it had read, reported `bytes_read: 0`, and the command
        # read that as completion with nothing printed. A bound is a bound on
        # how much this hands back at once; reading the two or three bytes that
        # finish a character the caller has already paid for is not a second
        # slice, and it is what guarantees every admitted bound makes progress.
        payload += _completing(handle, payload)
        at_end = from_byte + len(payload) >= held.st_size
    except ContractRefusal as refusal:
        return {**found, "state": "inaccessible", "from_byte": from_byte,
                "bytes_read": 0, "text": "", "at_end": False,
                "why": refusal.message}
    except OSError as failure:
        return {**found, "state": "inaccessible", "from_byte": from_byte,
                "bytes_read": 0, "text": "", "at_end": False,
                "why": f"this log could not be read ({type(failure).__name__})"}
    finally:
        for one in (handle, room):
            if one is not None:
                os.close(one)
    # NEVER SPLIT A CHARACTER ACROSS TWO SLICES. Review 2026-09-18T03-27-44Z
    # [R2]: a bounded read that ended mid-sequence decoded with `replace`, so
    # a follower stepping through a multibyte log in small slices corrupted
    # every character that straddled a boundary -- and its caller could not
    # tell, because `bytes_read` counted the bytes it had been handed. What is
    # reported now is the bytes that decoded WHOLE, so the next slice resumes
    # at the character boundary and nothing is invented or lost.
    payload, at_end = _whole(payload, at_end, found["state"])
    return {**found, "from_byte": from_byte, "bytes_read": len(payload),
            "text": payload.decode("utf-8", "replace"),
            # `at_end` IS NOT COMPLETENESS, and the name says so. A reader that
            # has caught up with a stream still being written is at its end for
            # this instant only; `state` is what says whether it is finished.
            "at_end": at_end}


def follow(delivery, stream, *, from_byte=0, bound=MAX_FOLLOW):
    """The next slice, and where to ask from next. NO LOOP AND NO SLEEP.

    A follower is the CALLER's loop: a function that blocked would own an
    operator's terminal and would have to invent a termination rule for a
    stream whose writer it does not control. This answers what is there now,
    the byte to come back from, and whether anybody has said the stream ended.

    `from_byte` RATHER THAN `offset`: `test_dependencies` lists `offset` among
    the operands that are bookkeeping BY NATURE, beside `cursor` and `index`.
    What crosses here is a position in a named file the caller already read,
    spelled the way this package spells `from_instant`.
    """
    named(stream)
    found = read(delivery, stream, from_byte=from_byte, limit=bound)
    return {**found, "next_from_byte": from_byte + found["bytes_read"],
            "more_may_arrive": found["state"] in ("live", "empty")}


def _denied(message):
    raise ContractRefusal("policy", "denied", message)
