"""Read one PR candidate's review evidence through SUPPORTED surfaces only.

Review220364 [3]: OWNER-PR-FLOW's first draft opened control.sqlite3 with
raw SQL, which repository policy forbids; the gap it papered over is now
LOGGED instead (below) and this is the replacement. Everything here goes
through the store's own read-only open and `review_cycles`' PUBLIC readers
-- `line_of`, `checkpoint_of`, `verdict_of` -- each of which PROVES what it
answers against the committed act rather than believing a row.

THE LOGGED OPERATIONAL GAP, not permission for SQL: there is no supported
LIST surface from a Work id to its line/checkpoint/verdict identities. The
identities must arrive from the Job status projection or from a retained
record (CANDIDATE-PR-220329.json carries this candidate's), and a complete
operator readout (work id -> reviewed candidate) is a bounded read-only
exposure still to be pinned and implemented.

READ-ONLY: `ControlStore.open_readonly` never initializes or changes the
store; this script writes nothing anywhere.

    PYTHONPATH=src:. python3 read-candidate-220385.py \
        --control <instance>/db/control.sqlite3 \
        --checkpoint checkpoint-... --verdict verdict-... [--line line-...]
"""
import argparse
import datetime
import json
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(prog="read-candidate")
    parser.add_argument("--control", required=True,
                        help="the instance's control store path")
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--verdict", required=True)
    parser.add_argument("--line", default=None)
    taken = parser.parse_args(argv)

    from baton_v12.worker_manager import review_cycles
    from baton_v12.worker_manager.store import ControlStore

    def clock():
        # The store's frozen instant grammar: milliseconds, Z suffix.
        return datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%S.") + (
            f"{datetime.datetime.now(datetime.timezone.utc).microsecond // 1000:03d}Z")

    store = ControlStore.open_readonly(
        taken.control, incarnation="w202663-candidate-readout", clock=clock)
    try:
        answered = {
            "checkpoint": review_cycles.checkpoint_of(store, taken.checkpoint),
            "verdict": review_cycles.verdict_of(store, taken.verdict)}
        if taken.line is not None:
            answered["line"] = review_cycles.line_of(store, taken.line)
    finally:
        close = getattr(store, "close", None) or getattr(store, "dispose",
                                                         None)
        if close is not None:
            close()
    print(json.dumps(answered, indent=1, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
