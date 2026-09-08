"""W38956 — the worker-entry TRANSPORT, and nothing above or below it.

`work/records/2026/08/finding-v12-first-useful-dogfood-task/`.

WHAT WAS MISSING. W6633 delivered a worker that speaks `baton.worker-entry/1`
over its own stdio, and W6632 delivered an adapter that starts one detached.
Nothing joined them: `test_lifecycle_composition` substitutes a `FakeSession`
for the conversation and writes the worker's output from the host fixture, so
the accepted arc has never once driven a real agent turn inside a real
container. This module is the piece that was absent, and it is deliberately the
SMALLEST piece that can be: a channel, a framing, a correlation rule and a
closed ending.

WHAT IT IS NOT, and each one is a boundary somebody could reasonably have put
here instead:

  NOT A SCHEDULER. It sends the operations it is given, in the order it is
  given them, once. It does not decide that a `work` follows a `describe`, does
  not retry, and does not choose an operation on a worker's behalf.
  NOT A SOURCE, GIT OR PROVIDER POLICY. Nothing here knows what the assignment
  asked for. The worker reads that from `/input`, which the manager composed
  and mounted before this module could have been called at all.
  NOT A SETTLEMENT. It reports what the channel did; `attempts.py` decides what
  that means for the runtime and `output.py` decides what it means for the
  result. A transport that settled anything would be a second opinion about a
  runtime it can only see one end of.
  NOT A SECOND START. `oci.exec_vector` names a runtime this manager already
  started and journalled; the id is the whole authorization, because everything
  an exec session can see was decided when the container was created.

TRANSPORT LOSS IS NEVER COMPLETION, and it is the reason the ending vocabulary
below has three words rather than two. A channel that ends, times out or
answers something this manager cannot read as a correlated frame has told us
nothing about what the agent did — the container may have finished its work and
lost its stream, or never have started the turn at all. Both are `lost`, and
neither may be reported as an agent answer. The durable answer is `/output`,
which the manager freezes and holds against its own declarations; this channel
is how the turn is ASKED FOR and is never what a result is read from.

WHY THE CHANNEL IS INJECTED. Every other outward act in this package crosses an
injected capability — `EnginePort` for a closed argv, the bearer mint, the
clock — and for the same reason: the manager composes and owns, and the
deployment supplies the one thing that touches the world. It also makes every
rule below provable without a daemon, which is what a transport most needs,
because the interesting cases are the ones a healthy daemon will not produce.

THE COPY OF THE WORKER'S CONTRACT IS DELIBERATE AND IS HELD. The worker cannot
import this package and this package cannot import the worker — that isolation
is the image's whole design — so the closed answer member sets appear in two
files. `tests/manager/test_worker_entry.py` reads the worker's literals out of
`v12/worker/baton_worker.py` and holds these against them, exactly as
`test_oci` already does for the launch document's members. Two copies of one
contract agree until they don't.
"""

import re

from ..contracts import ContractRefusal
from ..contracts.errors import name_value, type_name_of
from ..contracts.secrets import check_no_durable_secret
from . import boundaries

__all__ = ["ANSWER_MEMBERS", "CHANNEL_MEMBERS", "ChannelPort", "ENDINGS",
           "MAX_FRAME", "MAX_HEADER", "MAX_IDENTITY", "MAX_STDERR",
           "OPERATIONS", "PROTOCOL", "converse"]

# THE PROTOCOL THIS CHANNEL SPEAKS, by its versioned name. Compared by
# equality at both ends: a worker from another generation is not a peer to read
# the recognised parts out of.
PROTOCOL = "baton.worker-entry/1"

# The frame ceiling, both directions, and the worker's own. A manager that
# would write a larger frame than the worker will read would compose a message
# that can only ever be refused, and a manager with no read ceiling is one
# bounded by whatever the container writes.
MAX_FRAME = 1 << 20

# The length header's own ceiling, in DIGITS. Bounded separately from the body
# for the reason the worker bounds it separately: a peer that sends no newline
# must not be able to make this read forever, and a header is peer input like
# any other.
MAX_HEADER = 12

# An identity is a label this manager minted, not a payload.
MAX_IDENTITY = 256

# How much worker stderr is ever carried back. The worker's diagnostics are
# unbounded container-controlled text and this answer is the thing most likely
# to be written into an evidence transcript -- the same rule every other
# diagnostic in this manager is under. It is generous rather than terse because
# a provider-backed worker's stderr is where a failed turn explains itself, and
# a bound that truncates the explanation makes the failure harder to act on
# than the text is expensive to keep.
MAX_STDERR = 4096

# WHAT THIS TRANSPORT MAY BE ASKED TO SEND. The worker's own vocabulary, all
# three of it: `consider` is kept because it is a REAL operation of the
# contract that the one-container topology does not entitle a runtime to, and
# a transport that could not send it could not prove the worker refuses it.
OPERATIONS = ("describe", "consider", "work")

# EXACTLY WHAT EACH ANSWER IS. Held here as well as at the worker because this
# is the receiving side of an untrusted boundary: an answer with a missing,
# unknown or extra member is refused as it arrives rather than handed onward
# for somebody downstream to decide what it meant.
#
# The values are deliberately NOT typed beyond the closed set. What a
# disposition means is `output.py`'s question and what a recap says is nobody's
# -- this module's contract is the ENVELOPE, and a transport that started
# interpreting payloads would be the layer above it.
ANSWER_MEMBERS = {
    "describe": ("protocol", "operations", "launch"),
    "consider": ("contract_digest", "decision", "reason"),
    "work": ("disposition", "outputs", "recap"),
}

# The correlation every response carries back, and the two shapes it then is.
_ENVELOPE = ("protocol", "session", "operation_id")
_SUCCESS = _ENVELOPE + ("ok", "answer")
_FAULT = _ENVELOPE + ("ok", "code", "message")

# WHAT A CONVERSATION ENDED AS, closed and three-valued.
#
#   answered  every operation asked for came back `ok`, and the session ended
#             with a clean status. The worker did what it was asked.
#   faulted   the worker answered a CORRELATED fault. It is a refusal from the
#             peer, which means the channel worked and the request did not.
#   lost      the channel ended, timed out, or said something this manager
#             cannot read as a correlated frame -- including an engine that
#             could not open the session at all.
#
# `lost` is one word for several causes ON PURPOSE. What they have in common is
# the only thing a caller may act on: this manager does not know what the agent
# did. `why` says which one it was; the ending says what may be concluded.
ENDINGS = ("answered", "faulted", "lost")

# The channel capability's own surface, written out for the reason every port
# in this package writes one out: a member discovered missing halfway through a
# conversation is discovered after frames have already been sent.
#
# `close_input` IS A SEPARATE MEMBER FROM `finish`, and review [P1] is why it
# has to be. A conversation cannot be shown to be closed until the peer's
# stdout has reached EOF -- and the peer's stdout does not reach EOF until its
# stdin does, because the worker's loop ends on a clean end of input. So the
# send side has to close FIRST, then stdout is drained, and only then is the
# session waited on. Folding the close into `finish` would make those three
# one act and leave nowhere to observe what arrived in between; doing it in
# the other order deadlocks against a real worker.
CHANNEL_MEMBERS = ("send", "receive", "close_input", "finish")

# How many surplus bytes are read before this transport stops asking. A peer
# that keeps writing is not one to keep reading from, and the CONCLUSION is
# already fixed by the first byte -- this bound only decides how much of a
# hostile stream is drained before the session is waited on.
MAX_SURPLUS = MAX_FRAME

# What a finished channel answers. `status` is the exec session's own ending --
# the WORKER's, not the container's, because an exec session is a process and
# the container outlives it.
_FINISH = ("status", "stderr")

# BYTES, because a frame header is bytes off a stream and a str
# pattern applied to one is a TypeError rather than a refusal.
_DIGITS = re.compile(rb"\A[0-9]+\Z")


def _refuse(message, code="schema"):
    raise ContractRefusal("integrity", code, message)


class ChannelPort:
    """The ONE thing this transport does to the world: open a framed session.

    Typed at construction, and the §13 sweep lives here for exactly the reason
    it lives on `EnginePort.__call__` rather than in `run_vector`: every
    process on the host can read another's command line, so the property is
    about INVOCATION and invocation is what a port is. A vector composed
    somewhere and swept somewhere else is a sweep with a gap in it.
    """

    def __init__(self, open_channel):
        self._open = boundaries.capability(open_channel,
                                           "the channel's open operation")

    def __call__(self, argv, *, seconds):
        check_no_durable_secret(list(argv), what="a worker-entry vector")
        if type(seconds) is not int or type(seconds) is bool or seconds <= 0:
            _refuse(f"a worker-entry session is given a whole number of "
                    f"seconds to complete in; this is {name_value(seconds)}")
        channel = self._open(list(argv), seconds=seconds)
        for member in CHANNEL_MEMBERS:
            found = getattr(channel, member, None)
            if not callable(found):
                _refuse(f"the opened channel's {member} is "
                        f"{name_value(found)}; a {type_name_of(channel)} is "
                        f"not the framed session this transport was given")
        return channel


class _Lost(Exception):
    """A channel this manager can conclude nothing from.

    Deliberately not a `ContractRefusal`: a refusal is this manager declining
    something, and losing a channel is not a decision anybody made. It becomes
    the `lost` ending, which is the whole vocabulary a caller acts on.
    """


class _Reader:
    """One frame at a time, out of a stream that answers in pieces.

    `receive` is allowed to return short -- a pipe does -- so the buffering is
    here rather than being a requirement on every channel implementation. What
    is NOT here is any tolerance about the framing itself: the header is digits
    and a newline, the body is exactly the promised length, and a stream that
    ends inside either is lost rather than partially interpreted.
    """

    def __init__(self, channel):
        self._channel = channel
        self._held = b""

    def _more(self):
        """One more read, and EVERY way it can fail is a `_Lost`.

        Review [P1]: this called `receive` outside any exception boundary, so a
        channel enforcing the caller's own `seconds` bound by raising
        `TimeoutError` escaped `converse` unchanged -- past the three closed
        endings, past the `finish` that ends the session, and out to a caller
        that was promised peer behaviour always answers one of them.
        `ChannelPort` deliberately hands the deployment that bound, so a
        channel raising when it expires is the ORDINARY implementation of the
        contract rather than a broken one.
        """
        try:
            piece = self._channel.receive(4096)
        except Exception as failed:                        # noqa: BLE001
            raise _Lost(f"the channel's receive failed: "
                        f"{type_name_of(failed)}") from None
        if type(piece) is not bytes:
            raise _Lost(f"the channel answered {name_value(piece)} where this "
                        f"transport reads bytes")
        if not piece:
            return False
        self._held += piece
        return True

    def frame(self):
        """The next whole frame's bytes, or `None` at a clean end of stream."""
        while b"\n" not in self._held:
            if len(self._held) > MAX_HEADER:
                raise _Lost("the frame header is not a length")
            if not self._more():
                if not self._held:
                    return None
                raise _Lost("the stream ended inside a frame header")
        header, self._held = self._held.split(b"\n", 1)
        if len(header) > MAX_HEADER or not _DIGITS.match(header):
            raise _Lost("the frame header is not a length")
        length = int(header)
        if length > MAX_FRAME:
            raise _Lost(f"the worker sent a frame of {length} bytes and this "
                        f"channel carries {MAX_FRAME}")
        while len(self._held) < length:
            if not self._more():
                raise _Lost("the stream ended inside a frame body")
        body, self._held = self._held[:length], self._held[length:]
        return body

    def surplus(self):
        """How many bytes the worker wrote that this conversation never asked
        for -- INCLUDING the ones it had not written yet.

        Review [P1]: this used to be `trailing()`, which answered only what was
        already BUFFERED when the last expected frame was parsed. A peer that
        returned the one correlated answer and made a second frame available on
        the NEXT read therefore passed: nothing read again, nothing established
        EOF, and `finish` reported only a status -- so an unsolicited frame sat
        unread while the session was reported `answered`. That is a false clean
        ending at the least trusted boundary this manager has, and it
        contradicted this module's own stated rule.

        So the stream is READ to its end. The caller closes the send side
        first; a worker whose stdin has ended finishes its loop and closes
        stdout, so EOF here is the peer's own ending rather than a timeout.

        BOUNDED, because a peer that keeps writing must not keep this reading.
        The answer counts BYTES rather than carrying them: what a caller
        decides is whether there was surplus at all, and keeping unsolicited
        container output around to put in a diagnostic is how it ends up in a
        log.

        ANSWERS `(bytes, why)`, and review [P1] is why it is two values rather
        than one. This returned a count and turned every drain failure into
        `1` -- so a timeout while draining was reported as "the worker wrote 1
        byte", which is a fabricated measurement. A timeout IS loss and it is
        NOT evidence that any byte was written, and a transport that cannot
        tell those apart is inventing the more alarming of the two. `why` is
        `None` when the drain reached a real EOF, and names the failure
        otherwise; the count is only ever bytes actually read.
        """
        seen = len(self._held)
        self._held = b""
        while seen <= MAX_SURPLUS:
            try:
                piece = self._channel.receive(4096)
            except Exception as failed:                    # noqa: BLE001
                return seen, (f"the channel's receive failed while draining "
                              f"to its end: {type_name_of(failed)}")
            if type(piece) is not bytes:
                return seen, (f"the channel answered {name_value(piece)} "
                              f"where this transport reads bytes")
            if not piece:
                return seen, None
            seen += len(piece)
        return seen, None


def converse(channel_port, *, engine, runtime_id, program, session,
             operations, seconds, operation_ids):
    """Ask ONE runtime for these operations, in order, over one exec session.

    Answers a closed record and raises nothing for a peer's behaviour: every
    way this can go wrong is one of the three `ENDINGS`, because a caller
    deciding what a runtime is has to be able to write that decision down.

        {"ending": ..., "why": ..., "answers": [...], "status": ...,
         "stderr": ..., "argv": [...]}

    `answers` carries one record per operation ACTUALLY completed, in order --
    so a `work` that faulted after a `describe` succeeded leaves the
    `describe`, which is the difference between "the worker cannot talk" and
    "the worker refused this request".

    THE OPERATION IDS ARE THE CALLER'S. They are the manager's effectively-once
    identities and the worker consumes each exactly once per session, so a
    transport that minted them would be minting operation identity for the
    layer above it -- and a replay would be indistinguishable from a first
    attempt. Required, one per operation, and required to be distinct: two
    operations sharing an id is a conversation whose second half the worker
    will refuse as a replay, and composing it would be composing a request that
    cannot succeed.
    """
    if type(channel_port) is not ChannelPort:
        channel_port = ChannelPort(channel_port)
    boundaries.identity(session, "the launched worker session")
    if len(session) > MAX_IDENTITY:
        _refuse(f"a worker session identity is at most {MAX_IDENTITY} "
                f"characters; this is {len(session)}")
    # THE SHAPE BEFORE THE ITERATION, and W39666 is the second time this
    # package has paid for the difference. `exec_vector` began `list(program)`
    # until a review measured what `list("python3")` composes; these two began
    # `list(operations)` and `list(operation_ids)`, so a caller passing `None`
    # or `7` left through a raw `TypeError` -- past this manager's whole
    # contract vocabulary, at a boundary the inventory was about to record an
    # owner for. A claimed owner that a non-iterable escapes is not an owner.
    #
    # `str` IS THE ONE THAT MATTERS HERE, exactly as it does for a program.
    # `operations="describe"` iterates eight characters, none of which is an
    # operation this channel speaks, so today it refuses -- but it refuses by
    # naming `'d'`, which describes neither what the caller passed nor what is
    # wrong with it.
    for named, value in (("operations", operations),
                         ("operation_ids", operation_ids)):
        if type(value) not in (list, tuple):
            _refuse(f"a conversation's {named} is a list or tuple; this is "
                    f"{name_value(value)}. A string iterates one CHARACTER at "
                    f"a time, so accepting one would ask for a conversation "
                    f"nobody composed")
    asked = list(operations)
    ids = list(operation_ids)
    if not asked:
        _refuse("a worker-entry conversation asks for at least one operation")
    for one in asked:
        if one not in OPERATIONS:
            _refuse(f"{name_value(one)} is not an operation this channel "
                    f"speaks; it speaks {', '.join(OPERATIONS)}")
    if len(ids) != len(asked):
        _refuse(f"a conversation carries one operation identity per operation; "
                f"this asks {len(asked)} and names {len(ids)}")
    for one in ids:
        boundaries.identity(one, "a worker-entry operation identity")
        if len(one) > MAX_IDENTITY:
            _refuse(f"a worker-entry operation identity is at most "
                    f"{MAX_IDENTITY} characters; this is {len(one)}")
    if len(set(ids)) != len(ids):
        _refuse("an operation identity is consumed once per worker session; "
                "this conversation names one twice, and the worker would "
                "refuse the second as a replay")
    # THE VECTOR IS COMPOSED BY THE ADAPTER'S OWN VECTOR FUNCTION, so the
    # engine name, the runtime identity and the exec restrictions are decided
    # in one place with the rest of this component's argv. Imported at the call
    # rather than at the module, because `oci` imports enough of this package
    # that a top-level cycle is a real risk and this is the only reference.
    from .oci import exec_vector
    argv = exec_vector(engine, runtime_id=runtime_id, program=program)
    answers = []
    try:
        channel = channel_port(argv, seconds=seconds)
    except ContractRefusal:
        raise
    except Exception as failed:                            # noqa: BLE001
        # AN ENGINE THAT COULD NOT OPEN THE SESSION AT ALL. This is `lost` and
        # not a refusal: nothing was asked, so nothing about the runtime is
        # known -- and in particular this does NOT mean the container is
        # absent, which is `observe`'s question and is answered by asking the
        # engine rather than by failing to reach it.
        return {"ending": "lost", "why": f"the channel could not be opened: "
                                         f"{type_name_of(failed)}",
                "answers": answers, "status": None, "stderr": "", "argv": argv}
    reader = _Reader(channel)
    ending, why = "answered", None
    try:
        for operation, operation_id in zip(asked, ids):
            request = {"protocol": PROTOCOL, "session": session,
                       "operation_id": operation_id, "operation": operation}
            _send(channel, request)
            answer = _answer(reader, operation, operation_id, session)
            answers.append(answer)
            if not answer["ok"]:
                # A CORRELATED REFUSAL ENDS THE CONVERSATION, and the reason is
                # this transport's rather than the worker's.
                #
                # The worker's own behaviour after a fault is not uniform: a
                # LATCHED launch fault answers once and exits non-zero, while
                # an ordinary refusal -- an entitlement, a malformed request --
                # leaves an operable loop that would answer again. So the
                # decision here is a decision: a conversation is a plan whose
                # steps depend on the ones before them, and continuing past a
                # step that failed would be executing the rest of a plan whose
                # precondition did not hold. The caller composes another
                # conversation if that is what it means to do.
                #
                # THE ENDING SAYS NOTHING ABOUT THE STATUS, deliberately. An
                # entitlement refusal is a healthy worker ending 0, and calling
                # that unclean would report a working container as a lost one.
                ending, why = "faulted", answer["message"]
                break
    except _Lost as lost:
        ending, why = "lost", str(lost)
    # THE SEND SIDE CLOSES HERE, ON EVERY PATH, and before anything else is
    # concluded. It is what lets the worker end its own loop, so the drain
    # below reads to a real EOF instead of waiting on a peer that is waiting
    # on us. A close this manager cannot perform is itself a loss: the session
    # cannot be shown to have ended.
    if not _closed_input(channel) and ending != "lost":
        ending, why = "lost", "the channel's send side could not be closed"
    if ending != "lost":
        # SURPLUS IS CHECKED ON THE ANSWERED PATH AND THE FAULTED ONE. After a
        # fault this conversation sent nothing further, so anything the worker
        # wrote afterwards is exactly as unsolicited as it would have been
        # after a success -- and a peer saying things nobody asked for is a
        # channel this manager cannot conclude from, whichever way the last
        # request went.
        surplus, undrained = reader.surplus()
        if surplus:
            # WHAT WAS MEASURED, and it is measured whether or not the drain
            # then failed: bytes this conversation did not ask for are the
            # stronger fact and are stated first.
            ending = "lost"
            why = (f"the worker wrote {surplus} byte(s) this conversation did "
                   f"not ask for")
        elif undrained is not None:
            # A CHANNEL THAT COULD NOT BE DRAINED TO ITS END is a session this
            # manager cannot show ended, and saying so is different from
            # claiming the worker wrote something.
            ending, why = "lost", undrained
    finished = _finished(channel)
    if finished is None:
        return {"ending": "lost",
                "why": (why if ending == "lost"
                        else "the session's ending could not be read"),
                "answers": answers, "status": None, "stderr": "", "argv": argv}
    status, stderr = finished
    if ending == "answered" and status != 0:
        # THE WORKER ANSWERED AND THEN DID NOT END CLEANLY. `serve` returns 0
        # only on a clean end of input with nothing latched, so a non-zero
        # ending after complete answers is a worker that did something this
        # conversation did not see. It is not `faulted` -- nothing was refused
        # -- and it is certainly not `answered`.
        ending = "lost"
        why = (f"every operation was answered and the worker-entry session "
               f"ended {status}; a clean session ends 0")
    return {"ending": ending, "why": why, "answers": answers,
            "status": status, "stderr": stderr, "argv": argv}


def _send(channel, request):
    """One request, framed, or a lost channel.

    The manager's own frame is bounded too. A request this transport composes
    is small by construction -- four bounded identities -- so a frame over the
    ceiling here would mean a caller got past the operand checks above, and
    writing it would be writing a frame the worker is required to refuse.
    """
    import json

    body = json.dumps(request, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")
    if len(body) > MAX_FRAME:
        _refuse(f"this request is {len(body)} bytes and the channel carries "
                f"{MAX_FRAME}")
    try:
        channel.send(str(len(body)).encode("ascii") + b"\n" + body)
    except Exception as failed:                            # noqa: BLE001
        raise _Lost(f"the request could not be written: "
                    f"{type_name_of(failed)}") from None


def _answer(reader, operation, operation_id, session):
    """One response, correlated FIRST and read afterwards.

    The order is the content, and it is the same order the worker uses. A frame
    that is not this session's, this operation's or this protocol's is not an
    answer to what was asked -- so it is refused before anything in it is read
    as a result. A transport that checked the payload first and the correlation
    after would already have interpreted somebody else's answer.
    """
    import json

    body = reader.frame()
    if body is None:
        raise _Lost(f"the worker ended the channel without answering "
                    f"{operation}")
    try:
        document = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise _Lost("the worker sent a frame that is not UTF-8 JSON") from None
    if type(document) is not dict:
        raise _Lost("the worker sent a frame that is not one JSON object")
    for member in _ENVELOPE:
        value = document.get(member)
        if type(value) is not str or not value or len(value) > MAX_IDENTITY:
            raise _Lost(f"the worker's answer carries no readable {member}")
    if document["protocol"] != PROTOCOL:
        raise _Lost(f"this channel speaks {PROTOCOL} and the answer says "
                    f"{name_value(document['protocol'])}")
    if document["session"] != session:
        raise _Lost("the answer names another container session; a manager "
                    "reads only the session it minted for this runtime")
    if document["operation_id"] != operation_id:
        raise _Lost(f"the answer correlates to another operation than "
                    f"{name_value(operation_id)}; answers arrive in the order "
                    f"they were asked for")
    if document.get("ok") is True:
        _closed(document, _SUCCESS, "a successful answer")
        answer = document["answer"]
        if type(answer) is not dict:
            raise _Lost("a successful answer carries one JSON object")
        _closed(answer, ANSWER_MEMBERS[operation], f"a {operation} answer")
        return {"operation": operation, "operation_id": operation_id,
                "ok": True, "answer": answer}
    if document.get("ok") is False:
        _closed(document, _FAULT, "a fault")
        for member in ("code", "message"):
            if type(document[member]) is not str:
                raise _Lost(f"a fault's {member} is text")
        return {"operation": operation, "operation_id": operation_id,
                "ok": False, "code": document["code"],
                "message": document["message"][:MAX_STDERR]}
    raise _Lost("the worker's answer says neither ok nor not-ok")


def _closed(document, members, what):
    """A closed member set, and the reason it is closed rather than checked.

    An extra top-level member is how a second alias for an identity arrives,
    and this campaign has rejected those explicitly before. A missing one is a
    document this manager would have to guess the rest of. Neither is a frame
    to read the recognised parts out of.
    """
    missing = sorted(name for name in members if name not in document)
    extra = sorted(name for name in document if name not in members)
    if missing or extra:
        raise _Lost(
            f"{what} is exactly {', '.join(members)}"
            + (f"; missing {', '.join(missing)}" if missing else "")
            + (f"; unexpected {', '.join(extra)}" if extra else ""))


def _closed_input(channel):
    """End the request side of the channel, and say whether it ended.

    Separate from `_finished` because the ORDER is the content: the worker's
    loop returns on a clean end of input, so its stdout cannot reach EOF until
    this has happened. A transport that waited for the peer first would be
    waiting for something it had not allowed to occur.
    """
    try:
        channel.close_input()
    except Exception:                                      # noqa: BLE001
        return False
    return True


def _finished(channel):
    """The session's own ending, or nothing this manager can read.

    ALWAYS CALLED, on every path including a lost one, because the channel owns
    a process and a transport that abandoned one on the way out would leave the
    caller with a live exec session and no handle to it. What it CANNOT do is
    turn a bad ending into a good one, so a `finish` this manager cannot read
    is itself a loss rather than an absent status quietly treated as zero.
    """
    try:
        answer = channel.finish()
    except Exception:                                      # noqa: BLE001
        return None
    if type(answer) is not dict or sorted(answer) != sorted(_FINISH):
        return None
    status, stderr = answer["status"], answer["stderr"]
    if type(status) is not int or type(status) is bool:
        return None
    if type(stderr) is not str:
        return None
    return status, stderr[:MAX_STDERR]
