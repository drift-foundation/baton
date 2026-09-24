"""Claim-249945: the supervised success — four attempts, two frozen verdicts."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 249945

## Done under claim 249945 — R4's success

**A supervised run reaches four attempts, two frozen attributed verdicts and
positive cleanup for every runtime it launched, and settles.** Measured:
`admissions {implementation: 2, review: 2}`, `verdicts {job-a: accepted,
job-b: accepted}`, cleanup `retained` for all four attempts,
`outstanding_cleanup []`, `state: settled`.

  * **The worker-turn seam.** `supervise(..., turns=...)` invokes a caller's
    deterministic turn each serving tick, exactly where a container would
    answer. In a real deployment the runtime IS the turn; this build has no
    daemon, so the seam stands at the same boundary every accepted v12
    lifecycle fixture uses. A caller that supplies none gets a run that starts
    nothing, and the outcome says so rather than calling it success.
  * The verdicts are DERIVED through `review_verdict_from_result` from each
    Job's own frozen result, with the assignment generation read through
    `attempts.assignment_of` — not counted, not read off a status row.
  * **The module docstring is corrected.** It said the module "does not run
    anything" long after `supervise` and `main` were added; it now says what
    is here and what is still simulated.

46 focused checks, 0 failures, measured 17.32002149100299s,
`verification-14.json`; 1 is new.

## REMAINING

  * `main`'s no-result, deadline, failure and interruption checks — the
    supervisor's own are proved, but not through the entry point.
  * Operator steps 4 and 7, replaced by the tested bounded command.

## Ownership

Reviewer-owned and immutable: ASSESSMENT-249338.md, every `review-*.md` and
`review-*.json`/`.log`. baton.claude owns the rest of this dossier.
"""

PROGRESS = """
## 2026-09-23 — baton.claude, claim 249945

### The supervised success

A run through `supervise` over the composed `/2` deployment now reaches four
attempts — two implementations and two reviews — collects BOTH Jobs' verdicts
derived from their own frozen results, records `retained` cleanup for every
runtime it launched, has nothing outstanding, and settles. That is R4's
success, and it is the first time this Work has had one.

What made it possible is the **worker-turn seam**: `turns` is invoked each
serving tick, exactly where a container would answer. In a real deployment the
runtime IS the turn; this build has no daemon, so the seam stands at the same
boundary every accepted v12 lifecycle fixture uses. A caller that supplies none
gets a run that starts nothing, and the outcome still says so.

Two small things cost more than they should have. The `turns` callback raised
`NameError: copy` for three whole ticks and the run still reported four
admissions — because `_guarded` records a failed turn as uncertainty and carries
on, which is right for a real turn and meant my own broken callback looked like
a quiet run. The uncertainty list is where I found it. And the import I thought
I had added twice had not landed either time; the third attempt asserted the
file's own import block afterwards.

### The docstring that outlived its claim

This module said it "does not run anything" for several claims after
`supervise` and `main` were added. Stale prose about my own code is the thing I
keep being caught by, so it now says what is here and what is still simulated.

### Verification spending

46 focused deterministic checks, 0 failures, measured 17.32002149100299s,
receipt `verification-14.json` with `verification-14.log`; 1 is new.

Cumulative MEASURED for W247941, every retained invocation preserved:
1.678180975 + 2.122556141 + 2.145897528 + 2.868183810 + 2.876618006 +
3.646601886 + 3.682941216 + 6.941682081 + 10.885859361 + 10.943187142 +
10.857 + 11.135997740 + 11.183168619 + 11.520278754 + 11.597300884 +
11.682510099 + 14.049334683 + 13.071588666 + 17.320021491 =
**160.208909082s**.

State: returned for independent review with `main`'s four negatives and the
operator steps named as remaining.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 249945" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
