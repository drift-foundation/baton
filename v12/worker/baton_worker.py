"""`baton-worker`: the entry point inside the OCI reference image.

W6633 (`work/records/2026/08/finding-v12-oci-reference-worker-image`), the
third bounded child of W5.

THIS FILE IS THE WHOLE PROGRAM INSIDE THE IMAGE, and that is the design rather
than a convenience. It imports NOTHING from `baton_v12` -- no manager, no
contracts package, no authority client -- because a worker that could import
the manager is a worker one bug away from holding the manager's capabilities.
The image contains this file, the scripted agent beside it, and a Python
runtime. A case asserts the import graph, because "we did not import it" is a
property somebody will break by accident.

THE CHANNEL IS FRAMED AND BOUNDED. Every message is one length-prefixed JSON
document on stdin, answered on stdout:

    <decimal byte length>\\n<exactly that many bytes of UTF-8 JSON>

Length-prefixed rather than newline-delimited because a newline is a byte an
agent's own output legitimately contains, and a protocol whose framing a
payload can forge is a protocol with no framing. Both directions are bounded:
an oversized frame is refused before it is read into memory, not after.

EXCLUSIVE STDIO IS TRANSPORT ISOLATION, NOT MESSAGE IDENTITY -- the approved
`baton.worker-entry/1` ruling, 2026-08-25. Every request is one closed object
carrying `protocol`, `session`, `operation_id` and `operation`, plus only that
operation's own members. `session` is the manager-minted identity of THIS
exact posture-specific container session and arrives in the environment;
`operation_id` is consumed once within it. Wrong-session, replayed, missing,
unknown and extra members all refuse before the request reaches the agent.

Consent and execution therefore hold DIFFERENT session identities, and an
execution session is never a continuation or a promotion of a consent one:
there is no message that turns one container into the other, because a fresh
container after activation is what promotion was replaced by.

THERE IS EXACTLY ONE RESPONSE SHAPE AND IT IS CORRELATED. Every response
echoes the request's own `protocol`, `session` and `operation_id`; a success
adds `ok: true` and `answer`, a fault adds `ok: false`, `code` and a bounded
`message`. A frame this program cannot read an identity envelope out of is
answered with NO FRAME at all and a non-zero exit -- the ruling forbids
inventing an uncorrelated response shape, and the Worker Manager already owns
the launched session and settles that case from the engine.

THE TWO POSTURES ARE TWO CONTAINERS AND THIS PROGRAM KNOWS WHICH IT IS IN.
`BATON_WORKER_POSTURE` is `consent` or `execution` and nothing else. The
posture is checked ON EVERY OPERATION rather than once at start, because the
rule the topology exists for is that a consent container never becomes an
execution one -- and a check that ran once at start is a check a later message
can walk past.

WHAT A CONSENT WORKER HAS: the human contract and the role instructions, and
the ability to answer `accept` or `decline`. WHAT IT DOES NOT HAVE: the
assignment, the workspace, any output path, and any execution tool.

A BOOTSTRAP FAULT IS LATCHED, NOT RAISED -- the approved startup-correlation
ruling. A container built with the wrong posture or carrying material its
posture withholds still has an operable framing loop, so it reads exactly one
bounded request identity envelope, returns the pending failure through the
ordinary correlated fault, and exits non-zero. Reading that envelope grants no
task, workspace, output, tool or agent capability: a latched failure can never
reach the agent.

STDOUT IS THE CHANNEL, so nothing else may write to it. Diagnostics go to
stderr. A `print` in an agent would otherwise corrupt a frame, which is the
kind of failure that looks like a protocol bug for a week.
"""

import json
import os
import sys

PROTOCOL = "baton.worker-entry/1"

# The frame ceiling, both directions. Large enough for a human contract and a
# recap, small enough that a hostile or looping agent cannot exhaust the
# container's memory through the channel.
MAX_FRAME = 1 << 20

# The identity members are bounded on their own, well below the frame: an
# identity is a label the manager minted, not a payload.
MAX_IDENTITY = 256

# The bounded prose a fault carries. Bounded here rather than at the frame so
# the worker reports what went wrong instead of the channel reporting that the
# worker said too much.
MAX_MESSAGE = 2000

POSTURES = ("consent", "execution")

# What each posture may be ASKED. Two closed sets rather than one set plus
# conditionals: the whole rule is readable in four lines, and an operation
# added without a posture decision fails rather than defaulting into both.
OPERATIONS = {
    "consent": ("describe", "consider"),
    "execution": ("describe", "work"),
}

# The common envelope every request carries, and then EXACTLY the members each
# operation adds.
#
# Review [P1]: this used to be keyed by POSTURE, so an execution `describe`
# carrying `task` succeeded -- a member `describe` has no use for, accepted
# because some other operation of that posture does. Closure that is one level
# coarser than the contract is closure over the wrong thing.
COMMON_MEMBERS = ("protocol", "session", "operation_id", "operation")

REQUEST_MEMBERS = {
    "describe": COMMON_MEMBERS,
    "consider": COMMON_MEMBERS,
    "work": COMMON_MEMBERS + ("task",),
}

# What each answer is, exactly. Validated before it is framed, because an
# answer is what crosses the worker boundary and an agent is the least trusted
# thing inside this container -- a missing, unknown, extra or wrong-typed
# member must not become a frame the manager then has to interpret.
ANSWER_MEMBERS = {
    "describe": ("protocol", "posture", "operations", "environment"),
    "consider": ("contract_digest", "decision", "reason"),
    "work": ("disposition", "workspace", "recap"),
}

# Environment a worker is allowed to see. Anything else in the image's
# environment is not this program's business, and naming the set is what makes
# "the assignment did not reach the consent container" checkable.
ENVIRONMENT = {
    "consent": ("BATON_WORKER_POSTURE", "BATON_WORKER_SESSION",
                "BATON_WORKER_CONTRACT", "BATON_WORKER_ROLE"),
    "execution": ("BATON_WORKER_POSTURE", "BATON_WORKER_SESSION",
                  "BATON_WORKER_CONTRACT", "BATON_WORKER_ROLE",
                  "BATON_WORKER_ASSIGNMENT", "BATON_WORKER_WORKSPACE",
                  "BATON_WORKER_OUTPUT"),
}


class WorkerFault(Exception):
    """A refusal this program can report as a frame rather than a crash."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message[:MAX_MESSAGE]


class Uncorrelated(Exception):
    """A failure this program cannot answer, because it has no identity to
    answer under.

    Deliberately NOT a `WorkerFault`. The approved ruling forbids inventing an
    uncorrelated response shape, so a frame whose identity envelope cannot be
    read produces no frame at all -- the Worker Manager already owns the
    launched session and settles that case from the engine rather than from a
    worker message nobody can match to a request.
    """


def read_frame(stream):
    """One length-prefixed frame, or None at a clean end of input.

    The length is read BYTE BY BYTE up to the digits a ceiling can have, so a
    peer that sends no newline cannot make this read forever -- the bound is on
    the header as well as on the body, because a header is caller input too.
    """
    header = b""
    while True:
        piece = stream.read(1)
        if not piece:
            if not header:
                return None
            raise Uncorrelated("the frame header ended early")
        if piece == b"\n":
            break
        header += piece
        if len(header) > 12:
            raise Uncorrelated("the frame header is not a length")
    if not header.isdigit():
        raise Uncorrelated("the frame header is not a length")
    length = int(header)
    if length > MAX_FRAME:
        raise Uncorrelated(f"a frame of {length} bytes is larger than the "
                           f"{MAX_FRAME} this channel carries")
    body = stream.read(length)
    if len(body) != length:
        raise Uncorrelated("the frame body ended early")
    try:
        document = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise Uncorrelated("a frame is not UTF-8 JSON") from None
    if type(document) is not dict:
        raise Uncorrelated("a frame is one JSON object")
    return document


def write_frame(stream, document):
    body = json.dumps(document, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")
    if len(body) > MAX_FRAME:
        # OUR OWN OUTPUT IS BOUNDED TOO, and the replacement KEEPS THE
        # IDENTITY. A bounds fault that dropped the correlation would be the
        # uncorrelated shape arriving by the back door.
        body = json.dumps(
            {"protocol": document.get("protocol"),
             "session": document.get("session"),
             "operation_id": document.get("operation_id"),
             "ok": False, "code": "bounds",
             "message": "the answer exceeded the frame ceiling"},
            sort_keys=True, separators=(",", ":")).encode("utf-8")
    stream.write(str(len(body)).encode("ascii") + b"\n" + body)
    stream.flush()


def _bounded(value, what):
    if type(value) is not str or not value or len(value) > MAX_IDENTITY:
        raise Uncorrelated(f"{what} is bounded non-empty text")
    return value


def identity_of(request):
    """The request's own identity envelope, or nothing this program can answer.

    Read BEFORE anything else and read the same way whatever the request turns
    out to be, because a response correlates to a REQUEST: the three members
    echoed back are the ones the sender put on the frame, so even a refusal is
    matchable to the frame that caused it.

    A request that does not carry a readable envelope is `Uncorrelated`. There
    is no fault frame for it, and that is the ruling rather than an omission.
    """
    if "protocol" not in request or "session" not in request \
            or "operation_id" not in request:
        raise Uncorrelated("a request carries protocol, session and "
                           "operation_id")
    return {"protocol": _bounded(request["protocol"], "a protocol"),
            "session": _bounded(request["session"], "a session"),
            "operation_id": _bounded(request["operation_id"],
                                     "an operation id")}


def success(identity, answer):
    return {**identity, "ok": True, "answer": answer}


def failure(identity, fault):
    return {**identity, "ok": False, "code": fault.code,
            "message": fault.message}


def posture_of(environment):
    given = environment.get("BATON_WORKER_POSTURE")
    if given not in POSTURES:
        raise WorkerFault("posture",
                          f"a worker runs as one of {', '.join(POSTURES)}; "
                          f"this container says {given!r}")
    return given


def session_of(environment):
    """The identity the manager minted for THIS container session.

    Without it nothing this program says can be correlated to anything, so its
    absence is not a fault frame -- it is the case the ruling hands to the
    Worker Manager, which already owns the launched session and settles it as
    `worker_start_failed` from the container-engine result.
    """
    given = environment.get("BATON_WORKER_SESSION")
    if type(given) is not str or not given or len(given) > MAX_IDENTITY:
        raise Uncorrelated("a worker session identity is bounded non-empty "
                           "text and arrives from the manager")
    return given


def visible(environment, posture):
    """What this posture may see, and the proof that nothing else arrived.

    A consent container that could read `BATON_WORKER_ASSIGNMENT` would be a
    consent container holding the assignment, whatever it chose to do with it.
    So the presence of a member outside the posture's set is a REFUSAL rather
    than something to ignore: it means the manager built the wrong container,
    and continuing would hide that.
    """
    allowed = ENVIRONMENT[posture]
    intruders = sorted(name for name in environment
                       if name.startswith("BATON_WORKER_")
                       and name not in allowed)
    if intruders:
        raise WorkerFault(
            "posture",
            f"a {posture} container carries {', '.join(intruders)}, which its "
            f"posture is not given; this container was built wrong")
    return {name: environment[name] for name in allowed if name in environment}


def check_answer(operation, answer):
    """The agent's answer, against the closed set the contract pins.

    THE LAST BOUNDARY BEFORE THE FRAME. The agent is the least trusted thing
    inside this container, and an answer is what crosses out of it -- so a
    missing, unknown, extra or wrong-typed member is refused here rather than
    handed to a manager that would then have to decide what it meant.
    """
    if type(answer) is not dict:
        raise WorkerFault("answer",
                          f"a {operation} answer is one JSON object")
    wanted = ANSWER_MEMBERS[operation]
    missing = sorted(name for name in wanted if name not in answer)
    extra = sorted(name for name in answer if name not in wanted)
    if missing or extra:
        raise WorkerFault(
            "answer",
            f"a {operation} answer is exactly {', '.join(wanted)}"
            + (f"; missing {', '.join(missing)}" if missing else "")
            + (f"; unexpected {', '.join(extra)}" if extra else ""))
    for name, value in answer.items():
        # `workspace` is the one member a posture may legitimately not have,
        # and null is how it says so rather than by omitting the member --
        # absent and null are different documents and only one of them is an
        # answer to the question.
        if value is None and name == "workspace":
            continue
        if type(value) is str and len(value) <= MAX_FRAME:
            continue
        if type(value) is list and all(type(entry) is str for entry in value):
            continue
        raise WorkerFault(
            "answer",
            f"a {operation} answer's {name} is bounded text or a list of it")
    return answer


def bind(identity, expected):
    """THE COMMON CONTRACT, and it holds on every path this program has.

    The order is the content. A frame that is not for this session is not a
    request to this container at all, so it is refused before any question
    about entitlement: answering "you are not asked to work" would be
    answering a question somebody else was asked.

    Re-review [P1]: this used to live inside `handle`, which the latched
    bootstrap path never reaches -- so a container with a pending posture
    fault echoed an arbitrary peer's session and disclosed its own failure to
    whoever asked. Startup correlation supplies an operation identity; it does
    not suspend the binding. Lifted out so the one caller that decides what to
    answer establishes the correlation FIRST, whatever it goes on to say.
    """
    if identity["protocol"] != PROTOCOL:
        raise WorkerFault(
            "protocol",
            f"this channel speaks {PROTOCOL}; the frame says "
            f"{identity['protocol']!r}")
    if identity["session"] != expected:
        raise WorkerFault(
            "session",
            "this frame names another container session; a worker answers "
            "only the session the manager minted for it, and an execution "
            "session is never a continuation of a consent one")


def handle(request, identity, posture, environment, agent, spent):
    """One operation, with the POSTURE CHECKED EVERY TIME.

    The protocol and the session are `bind`'s and are established before this
    is reached; what remains here is entitlement, shape and the replay fence.
    """
    operation = request.get("operation")
    if type(operation) is not str or operation not in REQUEST_MEMBERS:
        raise WorkerFault("protocol", "a request names one known operation")
    if operation not in OPERATIONS[posture]:
        # NOT "unknown operation". The distinction is the point of the
        # topology: `work` is a real operation that this container is not
        # entitled to, and saying so is what makes the negative test meaningful.
        raise WorkerFault(
            "posture",
            f"a {posture} container is not asked to {operation!r}; it answers "
            f"{', '.join(OPERATIONS[posture])}")
    wanted = REQUEST_MEMBERS[operation]
    missing = sorted(name for name in wanted if name not in request)
    extra = sorted(name for name in request if name not in wanted)
    if missing or extra:
        raise WorkerFault(
            "protocol",
            f"a {operation} request is exactly {', '.join(wanted)}"
            + (f"; missing {', '.join(missing)}" if missing else "")
            + (f"; unexpected {', '.join(extra)}" if extra else ""))
    if operation == "work" and type(request["task"]) is not str:
        raise WorkerFault("protocol", "a work request names one text task")
    # ONE USE PER SESSION, CONSUMED BEFORE DISPATCH. An id that reached the
    # agent is spent whatever the outcome, because this program cannot know
    # whether the first attempt's side effects happened -- and "it failed, so
    # you may send it again" is exactly the reasoning a replay fence exists to
    # refuse.
    if identity["operation_id"] in spent:
        raise WorkerFault(
            "replay",
            f"operation {identity['operation_id']!r} was already used in this "
            f"session; an operation id is consumed once")
    spent.add(identity["operation_id"])
    seen = visible(environment, posture)
    if operation == "describe":
        return check_answer(operation,
                            {"protocol": PROTOCOL, "posture": posture,
                             "operations": list(OPERATIONS[posture]),
                             "environment": sorted(seen)})
    if operation == "consider":
        return check_answer(operation, agent.consider(seen, request))
    return check_answer(operation, agent.work(seen, request))


def serve(stdin, stdout, environment, agent):
    """The loop. Every answerable fault becomes a correlated frame; nothing
    becomes a traceback.

    A worker that died on a malformed frame would leave the manager waiting for
    a runtime that is gone, and reconciliation would have to infer what
    happened from engine state -- which is exactly what the manager is built
    not to do.
    """
    try:
        expected = session_of(environment)
    except Uncorrelated:
        # NOTHING THIS PROGRAM SAYS COULD BE MATCHED TO A REQUEST. The ruling
        # hands this to the manager, which already owns the launched session.
        return 2
    # THE BOOTSTRAP FAULT IS LATCHED, NOT RAISED. The framing loop is still
    # operable, so the failure is answered through the ordinary correlated
    # shape after exactly one identity envelope -- and it never reaches the
    # agent, because the dispatch below is not on this path at all.
    latched = None
    try:
        posture = posture_of(environment)
        visible(environment, posture)
    except WorkerFault as fault:
        latched, posture = fault, None
    spent = set()
    while True:
        try:
            request = read_frame(stdin)
        except Uncorrelated:
            return 1
        if request is None:
            # A clean end of input is the manager closing the channel. It is
            # NOT cancellation -- cancellation is the manager's runtime stop
            # path and this program never sees it as a message.
            return 1 if latched is not None else 0
        try:
            identity = identity_of(request)
        except Uncorrelated:
            return 1
        # THE BINDING FIRST, ON BOTH PATHS. Re-review [P1]: the latched return
        # below used to come before any correlation check, so a container that
        # had failed to start answered a frame minted for somebody else's
        # session and told them what had gone wrong inside it.
        try:
            bind(identity, expected)
        except WorkerFault as fault:
            write_frame(stdout, failure(identity, fault))
            # A LATCHED CONTAINER STILL ANSWERS EXACTLY ONCE AND EXITS
            # NON-ZERO. Which fault it names changed; how many frames it
            # writes, and that it dispatches nothing, did not.
            if latched is not None:
                return 1
            continue
        if latched is not None:
            write_frame(stdout, failure(identity, latched))
            return 1
        try:
            write_frame(stdout, success(
                identity,
                handle(request, identity, posture, environment, agent,
                       spent)))
        except WorkerFault as fault:
            write_frame(stdout, failure(identity, fault))
        except Exception as failed:                        # noqa: BLE001
            # THE AGENT'S FAILURE IS NOT THIS PROGRAM'S CRASH. It is reported
            # as a fault frame with a bounded description and no traceback: a
            # traceback would carry paths from inside the image out through the
            # channel.
            write_frame(stdout, failure(
                identity,
                WorkerFault("agent",
                            f"the agent failed: {type(failed).__name__}")))


def main(argv=None, stdin=None, stdout=None, environment=None, agent=None):
    from scripted_agent import ScriptedAgent

    return serve(stdin or sys.stdin.buffer, stdout or sys.stdout.buffer,
                 environment if environment is not None else dict(os.environ),
                 agent or ScriptedAgent())


if __name__ == "__main__":
    sys.exit(main())
