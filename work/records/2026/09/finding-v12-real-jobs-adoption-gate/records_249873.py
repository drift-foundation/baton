"""Claim-249873: the real generation, from the allocation, captured while live."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 249873

## Done under claim 249873

  * **The REAL assignment generation, from the allocation.** The projection
    attempt the manager passes `launch` carries none — my previous recorder
    read a field that does not exist, and the case that seemed to prove it
    supplied a synthetic `7`. `generations_from` reads each stage's own
    ALLOCATION out of `baton.v12.job-status/4`, which is the owner's record of
    the assignment an attempt was prepared under and the generation
    `review_for_attempt` fences an attachment to.
  * **Captured while the allocation is live.** Read only at the end it came
    back empty: an allocation is a live record and a released one may no
    longer answer. It is now read each tick and at the stop, and the last
    value each attempt actually had is kept.
  * **The projection needs `observed_at`.** Without it the call raised and
    `_guarded` swallowed the refusal into `uncertainty`, so the map was empty
    and nothing said why. Supplied from the run's own clock.
  * The synthetic-generation assertion is REMOVED; that case now proves the
    stage and Job mapping only, and a driven case asserts the real
    generations with an empty `uncertainty`.

45 focused checks, 0 failures, measured 14.049334682989866s,
`verification-12.json`; 1 is new.

## REMAINING

The generated-document success and its negatives: the worker-turn seam, a
disposable credential provider and registry, four attempts with BOTH frozen
verdicts and positive cleanup, then `main`'s no-result, deadline, failure and
interruption checks — and finally operator steps 4 and 7 plus this module's
docstring, which still says it "does not run anything".

## Ownership

Reviewer-owned and immutable: ASSESSMENT-249338.md, every `review-*.md` and
`review-*.json`/`.log`. baton.claude owns the rest of this dossier.
"""

PROGRESS = """
## 2026-09-23 — baton.claude, claim 249873

### I recorded a field that does not exist

The projection attempt the manager hands `launch` is built from the stage
columns plus episode, offer and attempt identities. It carries NO generation.
My recorder looked for `assignment_generation` or `generation`, found neither,
and recorded nothing — and the case that seemed to prove otherwise supplied a
synthetic `7`, which proved only that a dict I wrote had the key I put in it.
That assertion is gone.

`generations_from` reads each stage's own ALLOCATION out of
`baton.v12.job-status/4` — the owner's record of the assignment an attempt was
prepared under, and the generation `review_for_attempt` fences an attachment
to.

### Two things it took to make that read work

**An allocation is a live record.** Read only after the run stopped, the map
came back empty. It is now read each tick and again at the stop, keeping the
last value each attempt actually had.

**`status` needs `observed_at`.** Without it the call raised, `_guarded`
swallowed the refusal into `uncertainty`, and the empty map looked like "no
allocations" rather than "the read never happened". This is the second time in
this Work that a guarded read hid its own failure from me; the difference is
that this time `uncertainty` was where I looked.

Driven over the real deployment both admitted attempts now report generation
1 with an empty `uncertainty`, and a case asserts exactly that.

### Verification spending

45 focused deterministic checks, 0 failures, measured 14.049334682989866s,
receipt `verification-12.json` with `verification-12.log`; 1 is new.

Cumulative MEASURED for W247941, every retained invocation preserved:
1.678180975 + 2.122556141 + 2.145897528 + 2.868183810 + 2.876618006 +
3.646601886 + 3.682941216 + 6.941682081 + 10.885859361 + 10.943187142 +
10.857 + 11.135997740 + 11.183168619 + 11.520278754 + 11.597300884 +
11.682510099 + 14.049334683 = **129.817298925s**.

State: returned INCOMPLETE through baton.bug.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 249873" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
