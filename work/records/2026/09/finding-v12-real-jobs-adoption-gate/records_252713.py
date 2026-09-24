"""Claim-252713: the abandonment route is blocked; the operator's is not."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 252713; RETURNED INCOMPLETE

Review 2026-09-24T01:33:27Z authorized the bounded supervisor abandonment
correction and said to finish it "unless an actual operational blocker is
encountered", and separately that any new product path must be coordinated
before editing. **I met exactly that blocker.**

## The blocker, with its citations

`intake.abandon_attempt(store, port, adapter, ...)` cannot be reached from a
supervisor through the composed deployment.

  * **`stage_execution` composes no abandonment route.** Its `cancel_attempt`
    exists because an orchestrator cannot perform such an act itself: it finds
    the attempt's recorded allocation, routes to the worker that started it,
    and refuses when that worker "composes no cancellation capability". There
    is no `abandon_attempt` in the pinned file at all.
  * **`single_worker` declines abandonment on purpose**: "NO ABANDONMENT AND
    NO RETRY. A faulted, lost or incomplete exchange is REPORTED … W44716's
    abandonment is the owner for a started attempt policy decides to end, and
    deciding that is not this vertical slice's."
  * **The adapter is the hard part.** `port` is public on the worker's
    operations; the adapter is built per attempt by a private
    `_adapter(roots, delivery, orphan, launched)`. Claim 172346 already
    measured what a wrongly composed one costs — a member ended with its
    credential and launch roots still on disk.

So the supervisor step is one call once the deployment can route it, and the
routing is a change to `tools/single_worker.py` and `tools/stage_execution.py`
— product files this dossier does not own. **Recorded, not written.**

## What is NOT blocked, and is now established

**The operator's own recovery surface is composable.**
`dogfood_operator --abandon --abandon-reason` is the supported receiptless
ending, and its `GRANT_MEMBERS` is a CLOSED set of 32 members that
`read_grants` refuses to see incomplete or extended. Every one is obtainable
from artifacts the preserved instance already holds — the served deployment per
worker, the attempt's own records through the readers already used, the
preparation, and the operator's own incarnation and instant.
`SETTLEMENT-252647.md` lists which member comes from where.

So it is the orchestrator route that is blocked, not the recovery. Composing
one grants document per attempt, holding it against `read_grants` and
`preflight`, and printing the two invocations with their readback is the next
act and needs no product change.

## Also corrected under this claim — the three narrowings the review asked for

  * empty `pending_endings` proves no obligation is registered NOW; it does
    not prove nothing was ever requested or refused, and that question travels
    with the fault reproduction;
  * the assignments are **not** unfenced — the owner and the outcome both
    report cancellation fencing; abandonment adds its own fence under an
    identity the product keeps distinct from a cancel, so a prior fence
    neither satisfies nor conflicts with it. My earlier wording was wrong;
  * the four preconditions are **not** the whole preflight: the operation also
    owns the operands, the exact assignment, the participant through the port,
    the adapter's `destroy_abandoned` and custody capabilities, and
    eligibility.

## REMAINING

  1. the owner's decision on the abandonment route through the composition — a
     coordinated product path, which is the blocker above;
  2. the composed, held and printed recovery commands with their readback;
  3. the executed image's diagnostic provenance and the deterministic fault
     retention trace;
  4. the deterministic faulted/no-receipt/prior-cancel-fence/replay/adapter-
     refusal/positive-cleanup proof, which needs item 1 to exist first;
  5. corrected fresh-run commands.

## Evidence

No suite change this claim — documents only, and the review said no broad
rerun is needed for reader-only findings. `verification-27.json` (85 checks,
0 failures, 72.99730089001241s, pins agree) stands.

## Ownership

Reviewer-owned and immutable: ASSESSMENT-249338.md, every `review-*.md` and
`review-*.json`/`.log`. The owner owns the FINDING entries of 2026-09-23 and
2026-09-24. baton.claude owns the rest of this dossier. `tools/single_worker.py`
and `tools/stage_execution.py` are product files this dossier does not own.
"""

PROGRESS = """
## 2026-09-24 — baton.claude, claim 252713

### I went to write the correction and could not reach the operation

The abandonment step is one call, and the composed deployment gives a
supervisor no way to make it. `stage_execution` routes cancellation through the
worker that started the attempt precisely because an orchestrator cannot
perform such an act itself, and it composes nothing similar for abandonment.
`single_worker` declines abandonment in its own words — "NO ABANDONMENT AND NO
RETRY … deciding that is not this vertical slice's". And the operation needs a
per-attempt adapter that worker builds privately from its own delivery roots;
claim 172346 already measured what happens when that adapter is composed wrong.

So this is a product path, and the review's own instruction is to coordinate
one rather than edit it. Recorded in SETTLEMENT-252647.md with the citations,
and not written.

### What I could establish instead, and it is the useful half

The operator's recovery surface is composable. `dogfood_operator --abandon` is
the supported receiptless ending and its `GRANT_MEMBERS` is a CLOSED set of 32
that `read_grants` refuses to see incomplete or extended — so there is no
guessing about shape. Every member is obtainable from what the preserved
instance already holds, and the document now says which member comes from
where.

That changes the standing answer: it is the ORCHESTRATOR route that is blocked,
not the recovery. Last claim I said a runnable command needed operand
composition I had not done; now I know it needs no product change and exactly
what it needs. I still have not printed it, because a grants document assembled
and never held against `read_grants` and `preflight` is an operand list rather
than a command, and this dossier has already paid for printing an unchecked
recipe.

### Three things I had stated too broadly

Empty `pending_endings` proves no obligation is registered now — not that
nothing was ever requested or refused, and not why ordinary observation
registered none.

**The assignments are not unfenced.** The owner and the outcome both report
cancellation fencing for both. What abandonment adds is its OWN fence under an
identity the product keeps distinct from a cancel, so a prior fence neither
satisfies nor conflicts with it. My earlier sentence about an unfenced
authority was wrong, and the reason `docker rm` is out is the missing ending
record and that distinct fence.

And my four preconditions were not the whole preflight: the operation also owns
the operands, the exact assignment, the participant through the port, the
adapter's `destroy_abandoned` and custody capabilities, and eligibility.

### Verification spending

No suite receipt this claim: the changes are documents, and the review said no
broad rerun is needed merely to review a reader-only finding.
`verification-27.json` — 85 checks, 0 failures, 72.99730089001241s, pins agree
— stands as the current receipt.

Named suite subtotal unchanged at **1047.869180986s**. Measured this claim:
several sub-second read-only greps and reads of the pinned product source and
the preserved instance. Earlier disclosed costs and the ~120s timeout overlap
stand unchanged.

State: returned INCOMPLETE through baton.bug, on a named operational blocker.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 252713" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
