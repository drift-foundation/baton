"""Claim-249799: success now requires RESULTS; the success case is not written."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 249799

## Done under claim 249799

  * **Success requires RESULTS, not admission counts.** `verdicts_of` derives
    each bound Job's verdict through `review_driver.review_verdict_from_result`
    — the manager's own deriver, which refuses unless the frozen result
    belongs to that attachment's attempt, its retained manifest names the same
    result and assignment at the same generation, and the base, head and tree
    match the checkpoint's evidence. A Job with no derived verdict HOLDS the
    run, whatever its counters say. Nothing reads a disposition off a status
    row.
  * **The final cleanup read is after the last sweep.** A cleanup that settled
    on the last sweep was previously reported as outstanding by a read taken
    before it.
  * The empty-run case now asserts the RESULT-based reason and an empty
    `verdicts` map, rather than the admission-count reason it replaced.

43 focused checks, 0 failures, measured 11.59730088399374s,
`verification-10.json`.

## REMAINING — one coherent piece of work

**The generated-document success and the four negatives through `main`.** It
needs three things, and the reviewer has named the shape of all of them:

1. A **worker-turn seam** so review stages can complete inside a supervised
   run — the accepted fixture drives its deterministic turn OUTSIDE the
   serving loop, and `serve` has no hook for it.
2. A **disposable credential provider and registry** at the normal boundary,
   because the production provider rightly refuses `credential_sources: null`.
3. The success case itself (four attempts, both frozen verdicts, positive
   cleanup) and then no-result, deadline, failure and interruption through
   `main`.

**Operator step 7 and step 4 stay as they are** until that case exists: I will
not rewrite the page to advertise a command whose success is unproved.

## Ownership

Reviewer-owned and immutable: ASSESSMENT-249338.md, every `review-*.md` and
`review-*.json`/`.log`. baton.claude owns the rest of this dossier.
"""

PROGRESS = """
## 2026-09-23 — baton.claude, claim 249799

### Success is about results now

`verdicts_of` derives each bound Job's verdict through the manager's own
`review_verdict_from_result`, which refuses unless the frozen result belongs to
that attachment's attempt, its retained manifest names the same result and the
same assignment at the same generation, and the base, head and tree the
reviewer reports are the checkpoint's own. A Job with no derived verdict holds
the run whatever the admission counters say, and nothing here reads a
disposition off a status row.

The empty-run case was asserting the admission-count reason; it now asserts the
result-based one and an empty `verdicts` map. The old rule was a weaker
statement of the same intent, and keeping both would have let the weaker one
pass for the stronger.

### The final cleanup read moved

It was taken before the last sweep, so a cleanup that settled on that sweep was
reported as outstanding. It is now taken after.

### What is left is one piece of work, not four

The generated-document success needs a worker-turn seam (the accepted fixture
drives its deterministic turn OUTSIDE the serving loop, and `serve` has no hook
for it) and a disposable credential provider at the normal boundary, because
the production provider rightly refuses `credential_sources: null`. The four
negatives through `main` then contrast against it. I have not built any of it,
and I am not rewriting operator step 7 to advertise a command whose success is
unproved.

### Verification spending

43 focused deterministic checks, 0 failures, measured 11.59730088399374s,
receipt `verification-10.json` with `verification-10.log`. No new checks: the
change is inside a path the existing cases drive, and one existing case was
retargeted onto the stronger rule.

Cumulative MEASURED for W247941, every retained invocation preserved:
1.678180975 + 2.122556141 + 2.145897528 + 2.868183810 + 2.876618006 +
3.646601886 + 3.682941216 + 6.941682081 + 10.885859361 + 10.943187142 +
10.857 + 11.135997740 + 11.183168619 + 11.520278754 + 11.597300884 =
**104.085454143s**.

State: returned INCOMPLETE through baton.bug.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 249799" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
