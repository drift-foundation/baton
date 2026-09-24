"""Claim-249739: two of the four remaining R4 tasks done."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 249739

**Two of R4's four remaining tasks are done. Two are not.**

## Done under claim 249739

  * **Bounded ending EXECUTION.** The reserved window is now DRIVEN, not
    recorded: with admission closed, ordinary `sweep`s settle the endings this
    run started, each pass inside what is left of the TOTAL and bounded to
    `CLEANUP_SWEEPS` acts so a fast clock cannot spin. It stops as soon as
    nothing is outstanding.
  * **ONE executable bounded entrypoint.** `two_job_supervisor.main` takes
    `--deployment`, `--submission`, `--job-store`, `--control-store`,
    `--incarnation`, `--outcome` and the two bounds; it opens the stores,
    composes the operations through `stage_execution.operations_from`,
    submits, serves bounded, stops, publishes, and closes every handle it
    opened on every path. Exit 0 means `settled`.

42 focused checks, 0 failures, measured 11.183168619027128s,
`verification-8.json`.

## NOT done — the two the reviewer will ask about again

1. **Success through the generated documents**: four attempts, BOTH frozen
   verdicts and positive cleanup. The supervisor's loop cannot complete a
   review without a worker turn, and the accepted fixture drives those turns
   OUTSIDE the serving loop. The shape this needs is a turn seam on
   `supervise` that the witness supplies with the fixture's own deterministic
   turn — designed, not written.
2. **The affected negative checks against the entrypoint**: no-result,
   deadline, failure and interruption through `main` rather than through
   `supervise`.

## The operational constraint, stated plainly

These handoffs keep arriving partial because each claim's working budget runs
out before all four tasks can be written AND verified. That is not an external
blocker and needs no owner decision; it is why the remaining two are named
exactly rather than attempted and left unproved.

## Ownership

Reviewer-owned and immutable: ASSESSMENT-249338.md, every `review-*.md` and
`review-*.json`/`.log`. baton.claude owns the rest of this dossier.
"""

PROGRESS = """
## 2026-09-23 — baton.claude, claim 249739

Two of the four remaining R4 tasks are done.

### The reserved window is driven now

It was recorded and nothing happened inside it. Closing the gate stops the
NEXT runtime; what settles the ones already started is the manager's ordinary
sweep, and with admission closed it can finish endings without being able to
admit anything. Each pass is inside what is left of the TOTAL, and the number
of acts is bounded by `CLEANUP_SWEEPS` — a bound on the window alone would let
a fast clock spin through it. It stops as soon as nothing is outstanding.

### One command that can actually be typed

`main` takes the deployment and submission `two_jobs.py` wrote, the two stores,
an incarnation and an outcome path; it opens the stores, composes the
operations through `stage_execution.operations_from`, submits, serves bounded,
stops and publishes — and closes every handle it opened on every path. Step 7
previously named `job`, `control` and `composed` without defining them, which
is not an instruction.

### What I did not do, and why it is named rather than half-written

A success through the generated documents with four attempts and BOTH frozen
verdicts needs something the supervisor cannot do alone: a review cannot
complete without a worker turn, and the accepted fixture drives those turns
OUTSIDE the serving loop. The honest shape is a turn seam on `supervise` that
the witness fills with the fixture's own deterministic turn. It is designed and
not written, and the negative checks through `main` depend on it.

### Verification spending

42 focused deterministic checks, 0 failures, measured 11.183168619027128s,
receipt `verification-8.json` with `verification-8.log`. No new checks: both
changes are inside paths the existing whole-path cases drive, and the entry
point's surface was exercised directly rather than by a new case.

Cumulative MEASURED for W247941, every retained invocation preserved:
1.678180975 + 2.122556141 + 2.145897528 + 2.868183810 + 2.876618006 +
3.646601886 + 3.682941216 + 6.941682081 + 10.885859361 + 10.943187142 +
10.857 + 11.135997740 + 11.183168619 = **80.967874505s**.

State: returned INCOMPLETE through baton.bug, with the two remaining tasks
named and the reason they are not attempted-and-unproved stated.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 249739" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
