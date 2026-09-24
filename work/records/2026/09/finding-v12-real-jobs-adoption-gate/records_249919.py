"""Claim-249919: the ASSIGNMENT generation, through the supported reader."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 249919

## Done under claim 249919

  * **The generation comes from the ASSIGNMENT, not the pool.**
    `allocation.generation` in the status projection is the POOL generation —
    `projection._stage_status` gets it from `scheduler.allocation_of`, which
    joins `pool_generations` — and the schema distinguishes the two axes on
    purpose. `generations_from` now reads
    `attempts.assignment_of(control, attempt_id)`, the supported reader for
    the durable assignment identity fixed to an attempt, which the accepted
    `baseline` uses for exactly this.
  * **Absence stays honest.** `assignment_of` REFUSES an attempt that has not
    activated an assignment; that refusal lands in `uncertainty` and the
    verdict for that attempt is simply not derived.
  * **The case no longer passes on a coincidence.** It asserted only that the
    value was not `None`, and both axes happened to be `1`. It now asserts the
    captured value EQUALS what `assignment_of` answers for that attempt.

45 focused checks, 0 failures, measured 13.07158866597456s,
`verification-13.json`.

## REMAINING

The generated-document success and its negatives — worker-turn seam,
disposable credential provider and registry, four attempts with BOTH frozen
verdicts and positive cleanup, then `main`'s no-result, deadline, failure and
interruption checks — and finally operator steps 4 and 7 plus this module's
docstring, which still says it "does not run anything".

## Ownership

Reviewer-owned and immutable: ASSESSMENT-249338.md, every `review-*.md` and
`review-*.json`/`.log`. baton.claude owns the rest of this dossier.
"""

PROGRESS = """
## 2026-09-23 — baton.claude, claim 249919

### Two axes that both happened to be 1

`allocation.generation` is the POOL generation. The projection joins
`pool_generations` for it, the schema distinguishes the axes deliberately, and
my check — "it is not None" — could not tell coincident counters apart. Two
axes that happen to share the value `1` is the easiest possible false pass, and
I had built one.

`generations_from` now reads `attempts.assignment_of(control, attempt_id)`:
the supported reader for the DURABLE assignment identity fixed to an attempt,
which the accepted `baseline` already uses for this exact purpose. The reviewer
found it in the pinned source and named the line.

It also REFUSES an attempt that has not activated an assignment, which is the
honest answer: the refusal lands in `uncertainty` and that attempt's verdict is
simply not derived.

And the case is no longer satisfiable by a coincidence: it asserts the captured
value EQUALS what `assignment_of` answers for that attempt, rather than that it
is merely present.

### Verification spending

45 focused deterministic checks, 0 failures, measured 13.07158866597456s,
receipt `verification-13.json` with `verification-13.log`. No new checks: one
existing case was strengthened rather than added to.

Cumulative MEASURED for W247941, every retained invocation preserved:
1.678180975 + 2.122556141 + 2.145897528 + 2.868183810 + 2.876618006 +
3.646601886 + 3.682941216 + 6.941682081 + 10.885859361 + 10.943187142 +
10.857 + 11.135997740 + 11.183168619 + 11.520278754 + 11.597300884 +
11.682510099 + 14.049334683 + 13.071588666 = **142.888887591s**.

State: returned INCOMPLETE through baton.bug.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 249919" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
