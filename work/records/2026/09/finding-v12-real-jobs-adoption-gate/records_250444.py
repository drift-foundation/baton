"""Claim-250444: the handler lifetime, the recipe operands, and an axis."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 250444

## Done under claim 250444

  * **The handler lifetime is the WHOLE run now.** Review
    2026-09-23T19:22:24Z injected a fault after serving and cleanup and
    measured `installed=True, restored=False, outcome_exists=False`: my
    `finally` surrounded `_publish` alone while the comment above it said it
    surrounded everything. An outer `try` now spans `install()` to the end; a
    fault after serving is named in the document as `finalization_failure`,
    forced to `held`, published and re-raised; the outcome is completed from
    honest defaults so a half-accounted run writes a readable document; and
    `finished_at` goes through a guard, because the injected fault WAS the
    clock.
  * **The post-serving region is covered.** Three cases with a recording
    termination: a finalization fault, the reviewer's own final-clock fault,
    and a publication that fails. `LIFETIME-NEGATIVE-250444.log` runs them
    against the pre-correction bytes — two fail, and the third passes there
    too, which the log says plainly rather than claiming three.
  * **The pre-execution contract is precise.** The case that claimed to
    publish an outcome does not reach a publication: the composition refuses
    before `supervise` is entered. It is renamed, asserts no outcome file
    exists, and the page states where the line is.
  * **The recipe's operands agree.** Step 6 inspected `<run root>/db/...`
    while step 4 opened `<run root>/...`. Corrected, and three checks read the
    PAGE and hold every printed flag against the commands' own `--help`.
    `RECIPE-NEGATIVE-250444.log` fails them against the bad page.

## The axis question answered the other way

I went to LABEL the pool/assignment distinction unproved, as the review
permits, and the check I wrote to record the limitation disproved it: every
allocation carries pool generation 1 while the review attempts activate
assignment generation 2. **The axes differ in this witness**, so a supervisor
reading `allocation.generation` would publish 1 where the assignment is 2 —
and `review_for_attempt` fences an attachment to the activated generation, so
that is a verdict read that refuses rather than a cosmetic difference. The case
asserts the difference and the page says so.

## Evidence

`verification-19.json` — 60 checks, 0 failures, 67.43637445801869s, pins agree.

## REMAINING

Nothing the review named. What stands unproved is what the packet says: the
container boundary and the live provider under concurrency, a separately
selected runnable packet.

## Ownership

Reviewer-owned and immutable: ASSESSMENT-249338.md, every `review-*.md` and
`review-*.json`/`.log`. baton.claude owns the rest of this dossier.
"""

PROGRESS = """
## 2026-09-23 — baton.claude, claim 250444

### The comment was why I stopped looking

`termination.restore()` sat in a `finally` around `_publish` alone, and the
comment above the install said "INSTALLED AROUND EVERYTHING AND RESTORED AT THE
END". It was not. The reviewer injected a fault in the final clock call, after
serving and cleanup, and measured `installed=True`, `restored=False`,
`outcome_exists=False` — this process holding a signal handler for a run that
was over, with nothing on disk.

An outer `try` now spans from `install()` to the end. A fault after serving is
caught, named in the document as `finalization_failure`, forced into `held`,
published by the outer `finally` and re-raised — not converted into a tidy
return. The outcome is completed from honest defaults first, so a run that died
half-accounted writes a document that says which members it never reached
rather than one that reads like a finished run. And `finished_at` goes through
`_moment_of`, because a finalizer that re-raises on the same call it is
recovering from protects nothing.

### The only fault I had ever injected was one the guard absorbs

That is the reviewer's point and it is the right one: my interruption case
raises inside the guarded turn, which `_guarded` exists to absorb, so no check
of mine had ever entered the region between `gate.stop()` and the publication.
Three now do, with a recording termination so no real handler is touched — a
finalization fault, the reviewer's final-clock fault, and a failing
publication.

`LIFETIME-NEGATIVE-250444.log` runs them against the pre-correction bytes. Two
fail — `restored` is False, and the clock fault propagates unguarded. The third
passes on the old bytes too, because the old `finally` did cover the
publication; the log says so, because claiming three would be taking credit for
a check that was already green.

### Pre-execution is a different promise

`main`'s composition refuses before `supervise` is entered, so nothing has been
admitted and there is no account to render. The case that asserted that refusal
was named `..._publishes_an_outcome`, which claimed the opposite. Renamed, and
it now asserts that no outcome file exists. The page states where the line is:
before `supervise`, a refusal and no document; after it, every path publishes.

### The page an operator types from

Step 6 inspected `<run root>/db/jobs.sqlite3` while step 4 opened
`<run root>/jobs.sqlite3`. Nothing here could catch it — every other check
reaches the live objects, and the objects were right. What was wrong was the
text. Three checks now read the page: one store per axis across the whole page,
and every printed flag held against the commands' own `--help` rather than
against a second list kept here that would drift on its own.
`RECIPE-NEGATIVE-250444.log` fails two of them against the bad page.

### The check I wrote to record a limitation disproved it

The review allowed me to label the pool/assignment distinction unproved, and
that is what I sat down to do: read both axes, assert they are equal under this
witness, and say that nothing here separates them.

They are not equal. Every allocation carries pool generation 1 — `reserve`
stamps the current pool generation — while the review attempts activate
assignment generation 2. So the difference the review asked for twice was
already in this run and my two previous answers had simply never looked at both
numbers at once. The case asserts the separation and its consequence: a
supervisor reading `allocation.generation` publishes 1 where the assignment is
2, and `review_for_attempt` fences an attachment to the ACTIVATED generation,
so the wrong axis is a verdict read that refuses.

### Verification spending

**`verification-19.json` — 60 checks, 0 failures, 67.43637445801869s**, pins
agree.

Named suite subtotal: 415.286196436s + 67.43637445801869s =
**482.722570894s**.

Also measured this claim and NOT in that subtotal: three intermediate suite
runs at 47.348s, 60.404s and 67.484s; the lifetime negative proof at 13.224s;
the recipe negative proof at 0.474s; one three-case run at 0.464s; and two
single-case runs at 6.465s and 6.474s. Earlier disclosed costs and the ~120s
timeout overlap stand unchanged.

State: passed for independent review.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 250444" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
