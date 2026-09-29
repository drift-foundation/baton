"""The deterministic half of the two selected useful tasks' verification. W247941 claim 305440.

STRUCTURE ONLY, and that bound is the point: this decides whether each Job produced a file at the
exact path, in UTF-8, under the line bound, carrying every required heading, and whether the Job
changed ONLY that file. It decides nothing about whether the prose is true -- that is the independent
semantic review, which may answer `accepted`, `changes-requested` or `rejected`, and a structural
pass is not evidence for any of them.

REFUSES RATHER THAN REPORTS. Every failure exits non-zero and names the first thing wrong, because a
checker that prints a warning and exits 0 is a checker a pipeline ignores.

NO STORES, NO ENGINE, NO GIT MUTATION. The changed-path set is supplied by the caller (the proposal's
own patch already names it); this opens files under a candidate root and nothing else.
"""
import argparse
import json
import os
import sys

# THE CONTRACT, kept beside `USEFUL-TASKS-305440.md` and asserted against it by the test that owns
# this file. Changing one without the other is the drift this pairing exists to prevent.
TASKS = {
    "job-a": {
        "path": "docs/v12-parallel-operator-notes.md",
        "line_bound_exclusive": 100,
        "headings": (
            "## One manager, two Jobs",
            "## Launch",
            "## Status",
            "## Stop",
            "## When the outcome is not success",
            "## Limits, honestly",
        ),
    },
    "job-b": {
        "path": "docs/v12-evidence-map.md",
        "line_bound_exclusive": 100,
        "headings": (
            "## What is proved deterministically",
            "## What one real Job proved",
            "## What is not proved yet",
            "## What is deferred, and why",
            "## Where a claim would break",
        ),
    },
}


class TaskRefusal(Exception):
    """A structural requirement this candidate does not meet."""


def _refuse(message):
    raise TaskRefusal(message)


def checked(job_id, root, changed):
    """Every structural fact about one Job's proposal, or a refusal naming the first failure."""
    if job_id not in TASKS:
        _refuse(f"{job_id!r} is not one of this packet's two Jobs: "
                f"{', '.join(sorted(TASKS))}")
    held = TASKS[job_id]
    # THE CHANGED SET FIRST, because a correct document beside an extra changed file is still a
    # Job that took something the other one owns.
    wanted = [held["path"]]
    if sorted(changed) != wanted:
        _refuse(f"{job_id} may change exactly {wanted} and this proposal changes "
                f"{sorted(changed)}")
    place = os.path.join(root, held["path"])
    if not os.path.isfile(place):
        _refuse(f"{job_id}'s only file {held['path']!r} is absent under {root!r}")
    with open(place, "rb") as reading:
        raw = reading.read()
    try:
        body = raw.decode("utf-8")
    except UnicodeDecodeError as bad:
        _refuse(f"{held['path']!r} is not UTF-8: {bad}")
    lines = body.split("\n")
    # A TRAILING NEWLINE IS NOT A LINE. Counting it would make a 100-line file 101 and refuse a
    # document that meets the bound.
    counted = len(lines) - 1 if lines and lines[-1] == "" else len(lines)
    # UNDER 100 MEANS 99. W247941 review 2026-09-29T12-11-11Z: `> max_lines` admitted a
    # 100-line file against a contract that says "under 100 lines", so the probe passed at the
    # exact value the brief excludes. The bound is now `>=`, and `max_lines` is named
    # `line_bound_exclusive` so the next reader cannot mistake it for an inclusive maximum.
    if counted >= held["line_bound_exclusive"]:
        _refuse(f"{held['path']!r} is {counted} lines and the contract is UNDER "
                f"{held['line_bound_exclusive']}, so {held['line_bound_exclusive'] - 1} "
                f"is the most it may be")
    missing = [one for one in held["headings"] if one not in lines]
    if missing:
        _refuse(f"{held['path']!r} is missing required headings, first: "
                f"{missing[0]!r}")
    return {"job_id": job_id, "path": held["path"], "lines": counted,
            "bytes": len(raw), "headings": list(held["headings"]),
            "line_bound_exclusive": held["line_bound_exclusive"],
            "changed": wanted, "structural": "pass"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job", required=True, choices=sorted(TASKS))
    parser.add_argument("--root", required=True,
                        help="the candidate worktree this proposal was produced in")
    parser.add_argument("--changed", required=True, action="append",
                        help="one changed path, repeated; the proposal's own set")
    taken = parser.parse_args(argv)
    try:
        answer = checked(taken.job, taken.root, taken.changed)
    except TaskRefusal as refused:
        print(json.dumps({"structural": "refused", "why": str(refused)},
                         indent=2, sort_keys=True))
        return 1
    print(json.dumps(answer, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
