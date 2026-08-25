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

THE TWO POSTURES ARE TWO CONTAINERS AND THIS PROGRAM KNOWS WHICH IT IS IN.
`BATON_WORKER_POSTURE` is `consent` or `execution` and nothing else. The
posture is checked ON EVERY OPERATION rather than once at start, because the
rule the topology exists for is that a consent container never becomes an
execution one -- and a check that ran once at start is a check a later message
can walk past.

WHAT A CONSENT WORKER HAS: the human contract and the role instructions, and
the ability to answer `accept` or `decline`. WHAT IT DOES NOT HAVE: the
assignment, the workspace, any output path, and any execution tool. It cannot
be promoted; there is no message that turns it into an execution worker,
because promotion is what a fresh container after activation exists to
replace.

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

POSTURES = ("consent", "execution")

# What each posture may be ASKED. Two closed sets rather than one set plus
# conditionals: the whole rule is readable in four lines, and an operation
# added without a posture decision fails rather than defaulting into both.
OPERATIONS = {
    "consent": ("describe", "consider"),
    "execution": ("describe", "work"),
}

# What a REQUEST may carry, per posture. Closed, like the operations: the frame
# is an input boundary and a consent worker handed assignment material in one
# would be holding what its posture withholds.
REQUEST_MEMBERS = {
    "consent": ("operation",),
    "execution": ("operation", "task"),
}

# Environment a worker is allowed to see. Anything else in the image's
# environment is not this program's business, and naming the set is what makes
# "the assignment did not reach the consent container" checkable.
ENVIRONMENT = {
    "consent": ("BATON_WORKER_POSTURE", "BATON_WORKER_CONTRACT",
                "BATON_WORKER_ROLE"),
    "execution": ("BATON_WORKER_POSTURE", "BATON_WORKER_CONTRACT",
                  "BATON_WORKER_ROLE", "BATON_WORKER_ASSIGNMENT",
                  "BATON_WORKER_WORKSPACE", "BATON_WORKER_OUTPUT"),
}


class WorkerFault(Exception):
    """A refusal this program can report as a frame rather than a crash."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


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
            raise WorkerFault("protocol", "the frame header ended early")
        if piece == b"\n":
            break
        header += piece
        if len(header) > 12:
            raise WorkerFault("protocol", "the frame header is not a length")
    if not header.isdigit():
        raise WorkerFault("protocol", "the frame header is not a length")
    length = int(header)
    if length > MAX_FRAME:
        raise WorkerFault("protocol",
                          f"a frame of {length} bytes is larger than the "
                          f"{MAX_FRAME} this channel carries")
    body = stream.read(length)
    if len(body) != length:
        raise WorkerFault("protocol", "the frame body ended early")
    try:
        document = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise WorkerFault("protocol", "a frame is not UTF-8 JSON") from None
    if type(document) is not dict:
        raise WorkerFault("protocol", "a frame is one JSON object")
    return document


def write_frame(stream, document):
    body = json.dumps(document, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")
    if len(body) > MAX_FRAME:
        # OUR OWN OUTPUT IS BOUNDED TOO. An agent that produced an enormous
        # recap would otherwise make this program the thing that broke the
        # channel it is responsible for.
        body = json.dumps({"ok": False, "code": "bounds",
                           "message": "the answer exceeded the frame ceiling"},
                          sort_keys=True,
                          separators=(",", ":")).encode("utf-8")
    stream.write(str(len(body)).encode("ascii") + b"\n" + body)
    stream.flush()


def posture_of(environment):
    given = environment.get("BATON_WORKER_POSTURE")
    if given not in POSTURES:
        raise WorkerFault("posture",
                          f"a worker runs as one of {', '.join(POSTURES)}; "
                          f"this container says {given!r}")
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


def handle(request, posture, environment, agent):
    """One operation, with the POSTURE CHECKED EVERY TIME."""
    operation = request.get("operation")
    if type(operation) is not str:
        raise WorkerFault("protocol", "a request names one operation")
    if operation not in OPERATIONS[posture]:
        # NOT "unknown operation". The distinction is the point of the
        # topology: `work` is a real operation that this container is not
        # entitled to, and saying so is what makes the negative test meaningful.
        raise WorkerFault(
            "posture",
            f"a {posture} container is not asked to {operation!r}; it answers "
            f"{', '.join(OPERATIONS[posture])}")
    # ENVIRONMENT FILTERING IS NOT ENOUGH. Review [P1]: `visible` proves the
    # container was BUILT right, and the framed request is the other door into
    # the same process -- a consent worker handed an assignment, a workspace or
    # an output path IN A FRAME would be holding exactly what its posture
    # withholds, however carefully the environment was filtered.
    #
    # The members a request may carry are closed per posture for the same
    # reason the operations are: a member this posture cannot act on is one the
    # sender believes was read.
    intruders = sorted(name for name in request
                       if name not in REQUEST_MEMBERS[posture])
    if intruders:
        raise WorkerFault(
            "posture",
            f"a {posture} container is not given {', '.join(intruders)}; a "
            f"member its posture withholds is refused rather than ignored")
    seen = visible(environment, posture)
    if operation == "describe":
        return {"protocol": PROTOCOL, "posture": posture,
                "operations": list(OPERATIONS[posture]),
                "environment": sorted(seen)}
    if operation == "consider":
        return agent.consider(seen, request)
    return agent.work(seen, request)


def serve(stdin, stdout, environment, agent):
    """The loop. Every fault becomes a frame; nothing becomes a traceback.

    A worker that died on a malformed frame would leave the manager waiting for
    a runtime that is gone, and reconciliation would have to infer what
    happened from engine state -- which is exactly what the manager is built
    not to do.
    """
    # EVEN THIS ONE. Review [P1]: a bad posture raised out of `serve`, so the
    # one fault that means "the manager built the wrong container" was the only
    # one that arrived as a crash rather than as an answer -- and a worker that
    # dies leaves the manager waiting for a runtime that is gone.
    try:
        posture = posture_of(environment)
    except WorkerFault as fault:
        write_frame(stdout, {"ok": False, "code": fault.code,
                             "message": fault.message})
        return 1
    while True:
        try:
            request = read_frame(stdin)
        except WorkerFault as fault:
            write_frame(stdout, {"ok": False, "code": fault.code,
                                 "message": fault.message})
            return 1
        if request is None:
            return 0
        try:
            write_frame(stdout, {"ok": True,
                                 "answer": handle(request, posture,
                                                  environment, agent)})
        except WorkerFault as fault:
            write_frame(stdout, {"ok": False, "code": fault.code,
                                 "message": fault.message})
        except Exception as failure:                       # noqa: BLE001
            # THE AGENT'S FAILURE IS NOT THIS PROGRAM'S CRASH. It is reported
            # as a fault frame with a bounded description and no traceback: a
            # traceback would carry paths from inside the image out through the
            # channel.
            write_frame(stdout, {"ok": False, "code": "agent",
                                 "message": f"the agent failed: "
                                            f"{type(failure).__name__}"})


def main(argv=None, stdin=None, stdout=None, environment=None, agent=None):
    from scripted_agent import ScriptedAgent

    return serve(stdin or sys.stdin.buffer, stdout or sys.stdout.buffer,
                 environment if environment is not None else dict(os.environ),
                 agent or ScriptedAgent())


if __name__ == "__main__":
    sys.exit(main())
