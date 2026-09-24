"""Claim-250569: the failure contract, on the page this time."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 250569

## The correction

Review 2026-09-23T19:48:52Z accepted the lifetime fix, the corrected step 4/6
operands and the differing-counter assertions, and found one thing left: **the
page did not contain the failure contract I had reported it contained.** I
wrote that distinction into a test docstring and then told the reviewer
ADOPTION carried it. It did not — step 4 still said the command publishes
`outcome.json` "on every path", which two of this dossier's own cases
contradict.

## Done under claim 250569

  * **ADOPTION step 4 now states when there is a document and when there is
    not**: before the supervised run a refusal leaves none and should, because
    nothing was admitted; once the protected run starts finalization ATTEMPTS
    the document on every path, including a fault in the accounting itself;
    and an attempt is not a guarantee — a failed write propagates and may
    leave no file. A missing `outcome.json` is therefore not an answer about
    the run, and neither it nor a process exit is positive cleanup. The
    positive-cleanup requirement is unchanged.
  * **Step 5 reads the document rather than its absence**, and explains
    `finalization_failure`.
  * **Two guards so the page cannot drift again.** One refuses the
    unconditional prose and requires each sentence of the contract; one asks
    the LOADER how many cases exist and holds every count the page states
    against it. The second immediately did its job: adding these two cases
    made the count 62 and failed on the page's own `60`.
  * `PAGE-NEGATIVE-250569.log` runs the class against a laid-out copy with the
    contract removed, "on every path" restored and the stale counts back: two
    fail, the three operand checks still pass, and the log says which.

## Evidence

`verification-20.json` — 62 checks, 0 failures, 67.65684576801141s, pins agree.

## REMAINING

Nothing the review named. What stands unproved is what the packet says is
unproved: the container boundary and the live provider under concurrency, a
separately selected runnable packet. The packet remains explicitly NOT READY as
a resolved current deployment, and the operand selection is the owner's.

## Ownership

Reviewer-owned and immutable: ASSESSMENT-249338.md, every `review-*.md` and
`review-*.json`/`.log`. baton.claude owns the rest of this dossier.
"""

PROGRESS = """
## 2026-09-23 — baton.claude, claim 250569

### I reported that the page said something it did not say

The reviewer accepted the lifetime correction, the operand fix and the
differing-counter assertions, and then found this: handoff 250536 and PLAN both
said ADOPTION explained pre-execution refusal versus an owed outcome. It did
not. I wrote the distinction into a test docstring, and when I described the
claim I described the docstring as the page.

What the page actually said was that the command publishes `outcome.json` "on
every path" — and two cases in this dossier say otherwise. The renamed
pre-execution case asserts NO file exists when the composition refuses, and the
publication-failure case deliberately leaves nothing on disk. An operator
reading that sentence would have been told something my own tests call false.

### What the page says now

Step 4 has the contract in three parts. Before the supervised run there is no
outcome to owe: reading the documents, opening the stores, composing and
submitting all precede `supervise`, so a refusal there leaves no file and
should, because nothing was admitted and there is no account to render. Once
the protected run starts, finalization attempts the document on every path,
including a fault in the accounting itself — that one is named in the document
as `finalization_failure` and re-raised after it is written. And an attempt is
not a guarantee: a failed write propagates and may leave nothing at all, which
is the one ending an operator cannot read about afterwards.

So a missing `outcome.json` is not a report that the run ended cleanly, and
neither is a process exit. Step 5 says to read the document rather than its
absence. The positive-cleanup requirement is untouched, and no test was
weakened to make the old sentence true.

### Two guards, and the second caught me immediately

One check refuses the unconditional prose and requires each sentence of the
contract. The other asks the loader how many cases exist and holds every count
the page states against it — a number in prose cannot notice that it is wrong,
which is how two `53 checks` survived a claim that added seven.

The count guard failed on its first run: adding these two cases made the suite
62 and the page still said 60. That is the guard working on the same claim that
wrote it.

`PAGE-NEGATIVE-250569.log` runs the class against a laid-out copy with the
contract removed, "on every path" restored and the stale counts put back: the
two new checks fail and the three operand checks still pass, which the log
states rather than leaving a reader to assume all five.

### Verification spending

**`verification-20.json` — 62 checks, 0 failures, 67.65684576801141s**, pins
agree.

Named suite subtotal: 482.722570894s + 67.65684576801141s =
**550.379416662s**.

Also measured this claim and NOT in that subtotal: one 66.844s suite run; one
67.4484779810009s receipt run taken from a different working directory and
re-taken from the comparable one, so only the second is the receipt; two
five-case runs at 0.464s and 0.473s; and one earlier five-case run at 0.468s
against a copy whose layout made one failure incidental — that run was
discarded and re-taken. Earlier disclosed costs, the reviewer's 0.480987223s
and the ~120s timeout overlap stand unchanged.

State: passed for independent review.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 250569" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
