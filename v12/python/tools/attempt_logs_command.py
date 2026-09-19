"""W198667 — the operator's own view of one attempt's raw output.

THE ACCEPTANCE THIS ANSWERS, in the review's words: a deferred or failed attempt
exposes its evidence "without direct store or Docker inspection". So this reads
a directory and nothing else. It opens no Authority, no Job store, no control
store and no engine; it starts nothing and it writes nothing. A log room is
readable whether its container is running, stopped or long gone, which is the
whole reason the delivery is a manager-owned directory rather than something
asked of an engine after the fact.

    baton-v12-stack logs --logs <launch-home>/logs --attempt <id> locators
    baton-v12-stack logs --logs <launch-home>/logs --attempt <id> \\
                         read --stream provider.stderr
    baton-v12-stack logs --logs <launch-home>/logs --attempt <id> \\
                         follow --stream provider.stdout
    baton-v12-stack logs --logs <launch-home>/logs --attempt <id> \\
                         follow --stream provider.stdout --once --from-byte 4096

THE OPERAND ORDER IS THE ONE ARGPARSE ACCEPTS, and it was wrong here. Review
2026-09-18T02-31-51Z [5]: `--logs` and `--attempt` are registered on the PARENT
parser, so they come BEFORE the subcommand -- the earlier examples put them
after it and would have been refused by the very program they documented. The
copyable forms above are exercised by
`tests/tools/test_attempt_logs_command.py`.

REACHED THROUGH THE DEPLOYED COMMAND, because an operator reading evidence
after an incident has the installed bundle rather than a checkout. This module
is not on an installed package path and no console script could reach it; the
bundle's own `logs` subcommand is the supported invocation, the same surface
`status` and `monitor` are reached by.

`--logs` IS THE DELIVERY ROOT, which is `<launch_home>/logs` for a deployment
laid out by `worker_manager.launch`. It is an operand rather than something
derived from a deployment document, because an operator reading evidence after
an incident may have the directory and not the configuration -- and because a
reader that opened a deployment document would be a reader that could be
pointed at a store.

MISSING IS NOT EMPTY, and this surface says which. Every answer carries the
honest capture state, the writer's own word where there is one, and `declaration`
saying whether that word was readable at all -- so "nobody has said anything"
and "the writer said nothing" are distinguishable at a glance.
"""

import argparse
import json
import sys
import time

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import attempt_logs


def _delivery(taken):
    """The typed delivery this command reads, from two operands.

    `AttemptLogs` rather than a path, for the reason the delivery is typed at
    all: a function that took a string would admit any string. Nothing here
    materializes or adopts -- an operator reading evidence must not be able to
    CREATE a room by asking about one, because a room made by a reader would be
    an empty one reported where an absent one belongs.
    """
    return attempt_logs.AttemptLogs(attempt_id=taken.attempt, root=taken.logs)


def _locators(taken, stream):
    print(json.dumps(attempt_logs.locators(_delivery(taken)), indent=1,
                     sort_keys=True), file=stream)
    return 0


def _read(taken, stream):
    found = attempt_logs.read(_delivery(taken), taken.stream,
                              from_byte=taken.from_byte, limit=taken.limit)
    if taken.text:
        # THE BYTES, for an operator who wants to read them rather than a
        # document about them. The state still goes to stderr, because a
        # capture that is `partial` or `failed` must not look whole just
        # because somebody piped stdout somewhere.
        sys.stdout.write(found["text"])
        print(f"[{found['state']}] {found['why']}", file=sys.stderr)
        return 0
    print(json.dumps(found, indent=1, sort_keys=True), file=stream)
    return 0


def _follow(taken, stream, sleep=None):
    """Follow one stream until its writer says it ended, or the operator stops.

    W198667 review 2026-09-18T03-10-39Z [R3]. This answered ONE slice and asked
    the operator to write the loop, which the previous review had already
    declined -- so the loop is here, and the termination rule it needs is one
    this delivery already has rather than one this command invents.

    IT ENDS WHEN THE STREAM DOES, on the WRITER'S word. `more_may_arrive` is
    false once the capture state is no longer `live` or `empty`: a writer has
    declared `finished`, `partial`, `truncated` or `failed`, and each of those
    is an ending. A stream nobody ever spoke for keeps the follower waiting,
    which is correct -- silence is not an ending, and pretending otherwise is
    the whole class of defect this Work removes.

    `--once` KEEPS THE ONE-SHOT FORM, because a script that wants a position
    and a slice should not have to interrupt a loop to get one.

    INTERRUPTION IS THE OPERATOR'S AND IS SAID OUT LOUD. Ctrl-C leaves the
    follower and prints where to resume from, so a long tail can be picked up
    exactly where it was dropped rather than re-read or skipped.
    """
    waiting = sleep if sleep is not None else time.sleep
    delivery = _delivery(taken)
    at = taken.from_byte
    while True:
        found = attempt_logs.follow(delivery, taken.stream, from_byte=at,
                                    bound=taken.bound)
        if taken.once:
            print(json.dumps(found, indent=1, sort_keys=True), file=stream)
            return 0
        if found["text"]:
            stream.write(found["text"])
            stream.flush()
            at = found["next_from_byte"]
            # MORE BYTES ARE ALREADY HERE, SO TAKE THEM BEFORE DECIDING
            # ANYTHING. Review 2026-09-18T03-27-44Z [R2]: a completed
            # ten-byte stream read at `--bound 3` printed `abc` and returned
            # SUCCESS. `more_may_arrive` says the WRITER may append; it says
            # nothing about whether the slices already retained have been
            # emitted, and terminating on it mid-file loses the rest silently.
            continue
        at = found["next_from_byte"]
        if not found["more_may_arrive"] and not _pending(found):
            print(f"[{found['state']}] {found['why']}", file=sys.stderr)
            return 0
        try:
            waiting(taken.interval)
        except KeyboardInterrupt:
            print(f"[interrupted] resume with --from-byte {at}",
                  file=sys.stderr)
            return 0


def _pending(found):
    """Whether a stream that has said nothing yet is still worth waiting for.

    Review 2026-09-18T03-27-44Z [R2]: following an ABSENT stream returned 0 at
    once, which contradicted this command's own promise that a stream nobody
    has spoken for keeps the follower waiting. `attempt_logs.follow` sets
    `more_may_arrive` for `live` and `empty` only, and `absent` is neither --
    but absence is exactly the state a follower started before its writer is
    in, and treating it as completion reports a run that never began as one
    that finished.

    `inaccessible` IS NOT ABSENCE and is not waited on: a room this manager
    cannot read is a condition to report rather than one to sit on, and keeping
    those three apart is the whole vocabulary.
    """
    return found["state"] == "absent"


def main(argv=None, *, stream=None):
    stream = sys.stdout if stream is None else stream
    parser = argparse.ArgumentParser(
        prog="baton-v12-stack logs",
        description="Read one attempt's retained raw output. Opens no store "
                    "and reaches no engine.")
    parser.add_argument("--logs", required=True,
                        help="the attempt-log delivery root, which is "
                             "<launch home>/logs for a deployment this "
                             "manager laid out")
    parser.add_argument("--attempt", required=True,
                        help="the runtime attempt id whose room to read")
    commands = parser.add_subparsers(dest="command", required=True)

    listing = commands.add_parser(
        "locators", help="every stream, where it is, and what it honestly is")
    listing.set_defaults(run=_locators)

    for name, run in (("read", _read), ("follow", _follow)):
        one = commands.add_parser(
            name, help=("a bounded window onto one stream" if name == "read"
                        else "the next slice and where to ask from next"))
        one.add_argument("--stream", required=True,
                         help="one of " + ", ".join(attempt_logs.STREAMS))
        one.add_argument("--from-byte", type=int, default=0,
                         help="the position to read from; a follow's own "
                              "next_from_byte comes back here")
        if name == "read":
            one.add_argument("--limit", type=int, default=attempt_logs.MAX_READ,
                             help="how many bytes at most")
            one.add_argument("--text", action="store_true",
                             help="write the log's own bytes to stdout and the "
                                  "capture state to stderr")
        else:
            one.add_argument("--bound", type=int,
                             default=attempt_logs.MAX_FOLLOW,
                             help="how many bytes at most per slice")
            one.add_argument("--interval", type=float, default=1.0,
                             help="seconds between slices while the stream is "
                                  "still being written")
            one.add_argument("--once", action="store_true",
                             help="answer one slice and the byte to resume "
                                  "from, instead of following")
        one.set_defaults(run=run)

    taken = parser.parse_args(argv)
    try:
        return taken.run(taken, stream)
    except ContractRefusal as refusal:
        # AN OPERATOR'S REFUSAL IS PROSE, not a traceback. Every refusal this
        # can produce names a stream that is not one of the six, a room this
        # manager did not make, or an operand out of range -- each actionable
        # as it stands.
        print("refused: " + refusal.message, file=sys.stderr)
        return 2


if __name__ == "__main__":                                  # pragma: no cover
    raise SystemExit(main())
