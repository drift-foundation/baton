"""W198667 — the capture declaration format, with ONE owner on both sides.

WHY THIS IS NOT IN `worker_manager`. A worker writes these declarations and a
manager reads them, and `baton_v12` does not travel into worker images --
`claude_agent` states the reason in its own words: "a worker that can import the
manager is a worker one bug away from holding the manager's capabilities." So
the format has two writers, and two implementations of one format is precisely
how they drift.

THE PRECEDENT IS ALREADY IN THE TREE and this follows it exactly.
`baton_v12.source_profiles` imports nothing from `baton_v12` and is copied into
images as a TOP-LEVEL package (`COPY python/src/baton_v12/source_profiles
/opt/baton/source_profiles`). This module is one file with the same property: it
imports `json`, `os` and `stat` and nothing else, so the manager reaches it as
`baton_v12.attempt_log_format` and a worker image reaches the same bytes as
`attempt_log_format`.

WHAT IT OWNS, and each is a fact both ends must agree on or the evidence is
worthless: which streams exist, which states a writer may declare, what each one
MEANS in prose, what the sidecar beside a stream is called, and the act of
putting a declaration there without ever writing outside the room it was given.

WHAT IT DOES NOT OWN. It never decides a capture STATE from a file -- that is
`worker_manager.attempt_logs.capture_state`, which relates a writer's word to
what is on disk and is a manager's judgement rather than a format. It holds no
path, opens no room and knows no attempt: every act here is relative to a
directory descriptor its caller already proved.

REFUSALS ARE PLAIN. `ContractRefusal` lives in `baton_v12.contracts` and cannot
come with this file, so the exception here is its own -- and the manager
translates it at its boundary rather than letting a worker's exception type
become part of the manager's vocabulary.
"""

import itertools
import json
import os
import stat

__all__ = ["DECLARABLE", "DECLARED", "FormatRefusal", "MAX_REASON",
           "MAX_STATUS", "NATIVE", "STREAMS", "TARGET", "append_writer",
           "RETENTION", "log_name", "named", "open_room",
           "read_declaration",
           "status_name", "write_declaration"]

# WHERE THE CONTAINER SEES THE ROOM. A constant on both sides rather than an
# operand: a path a container could be TOLD is a path a container can be
# pointed at wrongly, which is the whole reason the environment transport was
# retired (W26291). The manager's `attempt_logs.LOG_TARGET` is this value, read
# from here, so the mount and the writer cannot disagree about it.
TARGET = "/run/baton/logs"

# THE CAPTURE'S OWN BOOKKEEPING inside the native corner: which source filled
# which retained file, and how far. It lives with the bytes it describes so it
# survives the process that wrote it -- a binding that does not outlive its
# process is not a binding. It is NOT a provider session file and no reader
# presents it as one.
RETENTION = ".retention.json"

# Where a provider's OWN session files go, if it writes any. Separate from the
# streams because they are a different kind of thing: the streams are what this
# deployment captured and this is what the provider itself produced.
NATIVE = "native"

# THE STREAMS THIS DELIVERY NAMES, named rather than discovered so that a reader
# can say a log is MISSING. Discovery can only ever report what is there.
#
# `worker` is the wrapper's own earliest output: a provider-side tee cannot
# retain a failure that happens before the provider starts, and the incident
# this Work came from was exactly such a failure.
STREAMS = ("worker.stdout", "worker.stderr",
           "provider.stdout", "provider.stderr",
           "verification.stdout", "verification.stderr")

# THE FOUR A WRITER MAY DECLARE. Completion is not among them by accident:
# `captured` is a manager's conclusion about a finished stream, because file
# existence and a momentary end of file prove neither.
DECLARABLE = ("failed", "truncated", "partial", "finished")

# WHAT EACH ONE MEANS, in the words that reach an operator. The prose is part of
# the format rather than beside it: a worker and a manager that declared the
# same state with different meanings would agree on a string and nothing else.
DECLARED = {
    "failed": "the writer could not write this stream; whatever is here is "
              "what reached the file before it failed, and there may be no "
              "file at all",
    "truncated": "the stream reached this deployment's retention ceiling and "
                 "the rest was dropped as it arrived",
    "partial": "the drain ended on its own clock rather than at end of file, "
               "so this is a prefix of the stream rather than the stream",
    "finished": "the writer saw this stream to its end",
}

# Metadata a manager reads back is input like any other: `MAX_STATUS` bounds the
# file and `MAX_REASON` the prose inside it.
MAX_STATUS = 4096
MAX_REASON = 2000

# ONE CALL'S OWN STAGING IDENTITY. The pid alone is shared by every thread in a
# process, and the tee this exists for is two threads draining two streams at
# once; `next()` is one bytecode under the interpreter lock. This provides
# per-call NAMING and nothing else -- it is not secrecy, and it is not what
# makes the act safe. `O_CREAT|O_EXCL|O_NOFOLLOW` and the creation-ownership
# tracking below are.
_STAGING = itertools.count()


class FormatRefusal(Exception):
    """A declaration this format will not write or will not believe."""


def named(stream):
    """THE ONE PLACE a stream operand becomes a name anything here will open.

    DESCRIPTOR-RELATIVE IS NOT CONFINEMENT. `O_NOFOLLOW` governs the FINAL
    component only, and `dir_fd` resolves `..` exactly as any path does, so a
    parent-relative or absolute operand walks straight out of a held room with
    every descriptor rule satisfied. The ALLOWLIST is the confinement, and one
    that a single entry point bypasses is not one -- which is the defect this
    function was extracted from, found by review after two narrower fixes.
    """
    if type(stream) is not str:
        raise FormatRefusal(f"a stream is named by one of this delivery's own "
                            f"names; this is a {type(stream).__name__}")
    if stream not in STREAMS:
        raise FormatRefusal(f"{stream!r} is not a stream this delivery names; "
                            f"it names {', '.join(STREAMS)}")
    return stream


def log_name(stream):
    """What the raw stream itself is called inside the room."""
    return named(stream) + ".log"


def status_name(stream):
    """ONE SIDECAR PER STREAM, which is the whole of the concurrency answer.

    A single shared document was loaded, modified and replaced without
    serialization, and two writers racing at the load lost one declaration
    entirely -- atomic REPLACEMENT of a document is not an atomic UPDATE of an
    entry in it. Per-stream files need no serialization because no two writers
    touch one file: a stream is written by the one thing that writes it.
    """
    return named(stream) + ".status.json"


def declaration(state, reason=None):
    """The document a writer's word becomes, bounded."""
    if state not in DECLARABLE:
        raise FormatRefusal(f"{state!r} is not a state a writer declares; it "
                            f"declares {', '.join(DECLARABLE)}")
    if reason is None:
        said = DECLARED[state]
    elif type(reason) is not str or not reason:
        raise FormatRefusal("a capture note is non-empty text")
    else:
        said = reason
    return {"declared": state, "reason": said[:MAX_REASON]}


def write_declaration(room, stream, state, *, reason=None):
    """Put one stream's declaration in the room, or leave the room untouched.

    `room` is a DIRECTORY DESCRIPTOR the caller already proved. Nothing here
    resolves a path of its own, so this cannot write outside what it was given.

    THREE PROPERTIES, and each one was a defect first:

      THE STAGING ENTRY IS CREATED, never opened. An ordinary truncating open
      followed a symlink at that name and OVERWROTE the file it pointed at --
      an actual write outside the attempt's room.

      ONLY AN ENTRY THIS CALL MADE IS EVER REMOVED. The handler used to unlink
      on any failure, including the `FileExistsError` from the exclusive create
      itself -- so a refusal to touch somebody else's entry deleted it.

      EVERY BYTE BEFORE THE REPLACE. One `os.write` had its count ignored, so a
      short write published a truncated sidecar -- read back as corrupt, the
      stream reported absent -- while the caller was told the whole declaration
      had been recorded. A writer that accepts a prefix per call is legitimate;
      ignoring what it accepted is not. No progress is a failure rather than a
      reason to ask forever.

    Nothing is published unless it was written whole, so a valid declaration
    already recorded survives a failed attempt to replace it.
    """
    said = declaration(state, reason)
    payload = json.dumps(said, sort_keys=True).encode()
    if len(payload) > MAX_STATUS:
        raise FormatRefusal(f"a capture declaration is at most {MAX_STATUS} "
                            f"bytes")
    staging = f"{named(stream)}.status.{os.getpid()}.{next(_STAGING)}.staging"
    made = False
    try:
        # GROUP-READABLE, LIKE THE LOG IT DESCRIBES. Found by the real
        # container rather than by a unit case: the worker writes this as the
        # image's fixed uid and the manager reads it as its own, sharing only
        # the deployment's workspace group -- so a 0600 sidecar was a
        # declaration ONLY ITS WRITER COULD SEE. The manager then reported the
        # stream `live` with `declaration: corrupt`, which is a writer's word
        # lost to a mode. It is never world-readable and never group-WRITABLE:
        # one stream is written by the one thing that writes it.
        handle = os.open(staging,
                         os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o640, dir_fd=room)
        made = True
        try:
            written = 0
            while written < len(payload):
                moved = os.write(handle, payload[written:])
                if moved <= 0:
                    raise OSError("this writer accepted no bytes")
                written += moved
        finally:
            os.close(handle)
        os.replace(staging, status_name(stream), src_dir_fd=room,
                   dst_dir_fd=room)
    except OSError as failure:
        if made:
            try:
                os.unlink(staging, dir_fd=room)
            except OSError:
                pass
        raise FormatRefusal(
            f"this capture declaration could not be written "
            f"({type(failure).__name__}); the stream's own log and any "
            f"declaration already recorded for it are unaffected") from None
    return said


def read_declaration(room, stream):
    """This stream's declaration, read inside the room and VALIDATED.

    `None` is "no writer has said anything". A `{"state": "corrupt"}` answer is
    "there is something here and it is not a declaration" -- REPORTED, never
    raised, and never silently turned into an assertion of completeness, because
    the readable operator picture is the whole point and one bad sidecar must
    not take the other five streams down with it.

    The sidecar is metadata and metadata obeys the rules the streams do:
    relative to the held room, no-follow, a regular file, a bounded read.
    """
    handle = None
    try:
        handle = os.open(status_name(stream),
                         os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                         dir_fd=room)
        held = os.fstat(handle)
        if not stat.S_ISREG(held.st_mode):
            return {"state": "corrupt",
                    "why": "this stream's capture declaration is not a regular "
                           "file; a special file is not a declaration"}
        if held.st_size > MAX_STATUS:
            return {"state": "corrupt",
                    "why": f"this stream's capture declaration is "
                           f"{held.st_size} bytes and this build reads at most "
                           f"{MAX_STATUS}"}
        raw = os.read(handle, MAX_STATUS)
    except FileNotFoundError:
        return None
    except OSError as failure:
        return {"state": "corrupt",
                "why": f"this stream's capture declaration could not be read "
                       f"({type(failure).__name__})"}
    finally:
        if handle is not None:
            os.close(handle)
    try:
        found = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return {"state": "corrupt",
                "why": "this stream's capture declaration is not UTF-8 JSON"}
    if type(found) is not dict:
        return {"state": "corrupt",
                "why": "a capture declaration is one JSON object"}
    said = found.get("declared")
    if said not in DECLARABLE:
        return {"state": "corrupt",
                "why": f"a capture declaration names one of "
                       f"{', '.join(DECLARABLE)}; this names {said!r}"}
    reason = found.get("reason")
    if type(reason) is not str or len(reason) > MAX_REASON:
        return {"state": "corrupt",
                "why": "a capture declaration's reason is bounded text"}
    return {"declared": said, "reason": reason}


def open_room(place=TARGET):
    """The log room's directory descriptor, or `None` if there is none.

    THE WORKER SIDE OF THE ROOM, and it answers `None` rather than raising for
    every ordinary reason it might not be there: an attempt launched by a
    deployment that composed no room, a `/1` diagnostic run, a mount that was
    not made. A worker whose RUN failed because its LOGGING was unavailable
    would be a worker that logging made less reliable, which is the opposite of
    why any of this exists.

    NO-FOLLOW AND A DIRECTORY, because everything under it is named relative to
    this descriptor afterwards: a link standing where the room should be is one
    a caller would otherwise write through.
    """
    try:
        return os.open(place, os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY)
    except OSError:
        return None


# HOW BAD EACH DECLARED STATE IS, so two of them can be compared. The order is
# the vocabulary's own meaning rather than a new rule: `failed` says bytes did
# not reach the file at all, `truncated` and `partial` say what is here is less
# than what there was, and `finished` is the only one that claims the file is
# whole. Worse always wins, because a later whole capture cannot make an
# earlier missing tail arrive.
SEVERITY = {"finished": 0, "partial": 1, "truncated": 2, "failed": 3}


def declared_state(value):
    """One declarable state, or `None` for anything that is not one.

    Review 2026-09-18T07-23-56Z [R1]: `value in SEVERITY` is a DICTIONARY
    MEMBERSHIP TEST, and a list or an object out of a JSON document is
    unhashable -- so a malformed record raised `TypeError` where a validation
    was meant to happen. Membership answers a question only about values that
    can be looked up; the type has to be checked first, and this is the one
    place that does it.
    """
    return value if type(value) is str and value in SEVERITY else None


def worst(one, other):
    """The worse of two declared states, or whichever one is one."""
    one, other = declared_state(one), declared_state(other)
    if one is None:
        return other
    if other is None:
        return one
    return one if SEVERITY[one] >= SEVERITY[other] else other


def carried_name(stream):
    """Where this stream's CUMULATIVE completeness lives.

    Beside the sidecar and never in place of it: the sidecar is about the
    writer that published it and this is about every byte in the file.
    `attempt_logs.locators` enumerates `STREAMS` by name, so this entry is not
    mistaken for one.
    """
    return status_name(stream) + ".carried"


def read_carried(room, stream):
    """The worst completeness any earlier generation of this stream declared.

    `None` ONLY WHEN THERE GENUINELY IS NO RECORD -- the ordinary first
    capture and the ordinary clean restart, where nothing was ever written.

    ANYTHING ELSE IS `failed`. Review 2026-09-18T07-09-49Z [R3]: this answered
    `None` for every open or read error and for a record that was not a
    regular file, so an INACCESSIBLE history read exactly like an absent one
    and a later clean append published `captured` over it. Only the malformed
    document was conservative, which is the opposite of the rule: a history
    this capture cannot read is a history that cannot establish completeness.
    """
    try:
        handle = os.open(carried_name(stream),
                         os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                         dir_fd=room)
    except FileNotFoundError:
        return None
    except OSError:
        return "failed"
    try:
        if not stat.S_ISREG(os.fstat(handle).st_mode):
            return "failed"
        raw = os.read(handle, MAX_STATUS)
    except OSError:
        return "failed"
    finally:
        os.close(handle)
    try:
        found = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, RecursionError):
        # A CUMULATIVE RECORD THAT CANNOT BE READ IS NOT PERMISSION TO CLAIM
        # COMPLETENESS. It is treated as the worst thing it could have said.
        return "failed"
    # TOTAL OVER EVERY JSON VALUE. A document that decoded is not a document
    # that says something: `declared` may be a list, an object, a number or
    # `null`, and `declared_state` answers `None` for every one of them rather
    # than raising on the two that are unhashable. What cannot be read as a
    # state is the worst thing it could have been.
    said = declared_state(found.get("declared")) if type(found) is dict \
        else None
    return said or "failed"


def carry_declaration(room, stream):
    """Move this stream's declaration into its cumulative record, and clear it.

    Review 2026-09-18T06-53-11Z [R1], and this is a consequence of my own last
    correction. Clearing the stale word was right -- a terminal declaration is
    about BYTES and stops being true when somebody appends -- but clearing it
    UNCONDITIONALLY destroyed the earlier writer's evidence of LOSS. The
    reviewer drove the real capture through a short write it detected itself,
    let a second writer append cleanly, and watched the reader answer
    `captured`, "the writer saw this stream to its end", over a file whose
    middle was never restored.

    SO THE TWO FACTS ARE SEPARATED. The sidecar answers "what did the writer
    that published it see", which is why clearing it keeps a reopened stream
    honestly `live`. This record answers "is the WHOLE FILE complete", which
    no later writer can improve: a new success cannot prove an earlier missing
    tail arrived.

    ONLY LOSS IS CARRIED. A `finished` generation adds nothing, so the
    ordinary clean restart writes no record at all and the all-successful
    control still ends `captured`.
    """
    said = read_declaration(room, stream) or {}
    declared = said.get("declared")
    # AN ENDING NOBODY VOUCHED FOR IS NOT A CLEAN START. Review
    # 2026-09-18T07-09-49Z [R1]: only DECLARED loss was carried, so bytes left
    # by a writer that never said how it ended -- the interrupted case, and a
    # corrupt declaration, which has no `declared` member either -- were
    # treated exactly like an empty new stream. A later clean append then
    # published `captured` over a prefix nobody ever vouched for.
    #
    # AN EMPTY STREAM IS STILL A CLEAN START, which is the distinction that
    # keeps the ordinary first capture free: what makes this `partial` is
    # BYTES with no trustworthy ending, not the absence of a sidecar.
    if declared is None and _has_bytes(room, stream):
        declared = "partial"
    held = worst(declared, read_carried(room, stream))
    # `SEVERITY.get` WOULD RAISE ON THE SAME SHAPES, and `worst` has already
    # answered `None` for anything that is not a state -- but the guard is
    # written here too rather than relying on a caller's invariant.
    if declared_state(held) is not None and SEVERITY[held] > 0:
        # AND THE PERSISTENCE HAS TO SUCCEED BEFORE THE OLD EVIDENCE GOES.
        # Review [R2]: this ignored the answer and unlinked the sidecar
        # anyway, so an ordinary `OSError` in the helper destroyed the only
        # record of a loss and a later writer published `captured` over it.
        # The caller refuses the handle instead -- which contains the failure
        # in the LOGGING rather than in the child, because a refused handle
        # leaves the stream on `DEVNULL` and declared `failed` while the
        # provider runs exactly as it would have.
        if not _write_carried(room, stream, held):
            return False, held
    try:
        os.unlink(status_name(stream), dir_fd=room)
    except FileNotFoundError:
        pass
    except (OSError, FormatRefusal):
        return False, held
    return True, held


def _has_bytes(room, stream):
    """Whether this stream's log already holds anything.

    A read error answers True: bytes that cannot be counted are not bytes
    that can be assumed absent, and the consequence of guessing wrong here is
    a stream reported complete that never was.
    """
    try:
        held = os.stat(log_name(stream), dir_fd=room, follow_symlinks=False)
    except FileNotFoundError:
        return False
    except (OSError, FormatRefusal):
        return True
    return not stat.S_ISREG(held.st_mode) or held.st_size > 0


def _write_carried(room, stream, state):
    """The cumulative record, replaced atomically, by `write_declaration`'s
    own three rules: created never opened, only this call's entry removed,
    every byte before the replace."""
    payload = json.dumps({"declared": state}, sort_keys=True).encode()
    staging = f"{named(stream)}.carried.{os.getpid()}.{next(_STAGING)}.staging"
    made = False
    try:
        handle = os.open(staging,
                         os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o640, dir_fd=room)
        made = True
        try:
            written = 0
            while written < len(payload):
                moved = os.write(handle, payload[written:])
                if moved <= 0:
                    raise OSError("this writer accepted no bytes")
                written += moved
        finally:
            os.close(handle)
        os.replace(staging, carried_name(stream), src_dir_fd=room,
                   dst_dir_fd=room)
    except OSError:
        if made:
            try:
                os.unlink(staging, dir_fd=room)
            except OSError:
                pass
        return False
    return True


def clear_declaration(room, stream):
    """Remove a declaration that no longer describes this stream's bytes.

    Review 2026-09-18T06-27-53Z [R2]: a writer declared `finished`, a SECOND
    writer for the same stream appended beside it, and the sidecar still said
    finished -- so the real reader answered `captured`, "the writer saw this
    stream to its end", `more_may_arrive: false`, over a file that was still
    growing. A follower exits on that. Closing the second capture with
    `declare(None)`, which explicitly asserts that nobody knows how this ended,
    left the stale word standing too.

    A TERMINAL WORD IS ABOUT BYTES, NOT ABOUT A NAME. The first writer's
    declaration was true of the file as it was; it is not true of the file once
    somebody appends. ABSENCE IS THE HONEST INTERVENING STATE -- the reader
    calls a stream with bytes and no declaration `live`, which is exactly "we
    do not know whether this is all of it" -- so the stale word is removed
    rather than replaced by a lie in either direction.

    THE BYTES ARE NEVER TOUCHED. This removes metadata only; the earlier
    writer's output stays exactly where it is, which is the whole point of
    appending.

    Answers True when nothing stale remains -- including the ordinary case
    where there was never anything there -- and False when something is there
    and could not be removed, which the caller must not append under.
    """
    try:
        os.unlink(status_name(stream), dir_fd=room)
    except FileNotFoundError:
        return True
    except (OSError, FormatRefusal):
        return False
    return True


def append_writer(room, stream, refused=None, carried=None):
    """One stream's own log, opened to APPEND inside the room AND OWNED.

    APPEND, NEVER TRUNCATE. A second incarnation writes beside the first: the
    required outcome is that partial evidence survives error, abnormal
    termination and restart, and a file emptied by the act of re-opening it
    would lose exactly what it exists for.

    `O_NOFOLLOW` at the final component and every name relative to the room, so
    nothing here writes outside what its caller proved. `None` when the entry
    cannot be acquired -- see `open_room` for why that is not a failure -- and
    a bounded sentence appended to `refused` saying which of the reasons it was.

    THREE PROPERTIES THE NATIVE CORNER LEARNED FIRST, and review
    2026-09-18T06-27-53Z [R1] found this shared opener without any of them
    while all six streams go through it, including the wrapper's earliest
    output:

      NONBLOCKING ACQUISITION. A fifo at `provider.stdout.log` blocked this
      open waiting for a reader, and the reviewer's bounded child was killed at
      two seconds. Capture must not be able to strand the thing it captures,
      and this open happens BEFORE the provider starts.

      A REGULAR FILE, ASKED OF THE DESCRIPTOR. `O_NOFOLLOW` refuses a symlink
      at the name and says nothing about a fifo or a device, and a device opens
      perfectly well and swallows everything.

      AND ONE THIS ROOM OWNS. A hard link is a second name for the INODE
      rather than for the path, so a confined name and a no-follow open cannot
      see it: the reviewer linked an empty file from outside the room at
      `provider.stdout.log` and watched raw provider bytes land there while the
      capture declared `finished`. The inode's own link count is the question.

    A NEW ENTRY IS CREATED RATHER THAN ADOPTED, for the same reason: `O_CREAT`
    alone takes whatever is already at the name, which is how the aliased file
    became a destination.

    AND A STALE TERMINAL DECLARATION IS CLEARED BEFORE THE CALLER CAN APPEND
    [R2]. A handle is not answered while a previous writer's word still stands
    over bytes this one is about to extend; if that word cannot be removed,
    this refuses rather than appending underneath it.

    BUT ITS LOSS IS CARRIED, NOT DISCARDED. Review 2026-09-18T06-53-11Z [R1]:
    clearing unconditionally destroyed the earlier writer's evidence that
    bytes were missing, so a later clean append published `finished` over a
    file whose middle never arrived. `carry_declaration` moves that fact into
    the stream's cumulative record first, and the worst state any generation
    has declared is appended to `carried` for the caller to publish with its
    own outcome.
    """
    def note(said):
        if refused is not None and said not in refused:
            refused.append(said)

    try:
        name = log_name(stream)
    except FormatRefusal:
        return None
    fresh = True
    try:
        os.stat(name, dir_fd=room, follow_symlinks=False)
        fresh = False
    except OSError:
        pass
    flags = (os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW
             | os.O_NONBLOCK)
    if fresh:
        flags |= os.O_EXCL
    try:
        handle = os.open(name, flags, 0o640, dir_fd=room)
    except OSError as failure:
        note(f"this stream's log could not be opened "
             f"({type(failure).__name__})")
        return None
    try:
        held = os.fstat(handle)
    except OSError as failure:
        os.close(handle)
        note(f"this stream's log could not be measured "
             f"({type(failure).__name__})")
        return None
    if not stat.S_ISREG(held.st_mode):
        os.close(handle)
        note("this stream's log is not a regular file, so nothing was "
             "written into whatever is there")
        return None
    if held.st_nlink != 1:
        os.close(handle)
        note("this stream's log is also linked elsewhere, so writing into it "
             "would put this attempt's bytes outside its own room")
        return None
    cleared, held = carry_declaration(room, stream)
    if not cleared:
        os.close(handle)
        note("this stream's earlier completeness could not be carried or its "
             "previous declaration could not be cleared, and appending would "
             "either report somebody else's ending as this capture's or lose "
             "the only record that bytes were already missing")
        return None
    if carried is not None and held is not None:
        carried.append(held)
    return handle


def write_all(handle, payload):
    """Every byte, or the count that actually reached the file.

    Answers how much was written. A caller that needs to declare `failed` or
    `truncated` needs to know the difference, and a short write silently
    treated as a whole one is the defect this whole module was corrected for
    once already.
    """
    written = 0
    while written < len(payload):
        try:
            moved = os.write(handle, payload[written:])
        except OSError:
            return written
        if moved <= 0:
            return written
        written += moved
    return written
