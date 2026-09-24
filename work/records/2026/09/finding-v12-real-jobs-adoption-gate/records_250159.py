"""Claim-250159: the traceback captured before the guard, and what it names."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 250159

## Done under claim 250159

  * **The callback's traceback is captured BEFORE `_guarded` converts it.**
    The guard turns a failed turn into one line of uncertainty — right for a
    run, useless for a diagnosis. The diagnostic now wraps the callback, keeps
    the frames, prints them in its receipt and re-raises. Nothing is
    suppressed and no delivery is fabricated.
  * **The frame is retained** in `DIAGNOSTIC-250159.log`:

        test_two_jobs.py:751 in turns -> self.turn(...)
        tests/tools/test_stage_execution.py:2797 in turn
            delivered.document, delivered.document["session"], ...
        AttributeError: 'NoneType' object has no attribute 'document'

    `delivered` comes from `launch.adopt(self.config["launch_home"],
    attempt_id=..., session="session-" + digest(attempt_id)[7:31],
    contract=self.config["launch_contract"], role=role, ...)` at line 2770.
    **`adopt` answered None**: there is no delivery it recognises for that
    attempt under those operands.

## What that means, and what it does NOT

The fixture's `turn` adopts a delivery keyed by launch home, attempt,
session, contract and role. Through `main` one of those does not match what
the run actually wrote. **Which one is NOT established** — I read the call
site and stopped there rather than name a candidate I have not tested.

The next claim compares the five operands `adopt` is given against what
`main`'s composition wrote for the same attempt. That is a bounded comparison
with a printed receipt, not a theory.

## REMAINING

That comparison; then the `main` success and negatives, lifecycle protection,
the generation regression through `main`, the operator recipe, and the
diagnostic's own pinning and `status(None)` gaps.

## Ownership

Reviewer-owned and immutable: ASSESSMENT-249338.md, every `review-*.md` and
`review-*.json`/`.log`. baton.claude owns the rest of this dossier.
"""

PROGRESS = """
## 2026-09-23 — baton.claude, claim 250159

### The traceback, before the guard converted it

`_guarded` turns a failed turn into one line of uncertainty. That is right for
a run — a real worker turn that fails is the run's business, not an exception
to escape through — and useless for a diagnosis. The diagnostic now wraps the
callback, keeps the frames, prints them and RE-RAISES, so nothing is
suppressed and no delivery is fabricated to get past it.

### What the frames say

Retained in `DIAGNOSTIC-250159.log`:

    test_two_jobs.py:751 in turns -> self.turn(...)
    tests/tools/test_stage_execution.py:2797 in turn
        delivered.document, delivered.document["session"], ...
    AttributeError: 'NoneType' object has no attribute 'document'

`delivered` is `launch.adopt(self.config["launch_home"], attempt_id=...,
session="session-" + digest(attempt_id)[7:31],
contract=self.config["launch_contract"], role=role, ...)`. **`adopt` answered
None** — there is no delivery it recognises for that attempt under those
operands.

So the turn is reaching the right place and finding nothing to adopt. One of
the five operands does not match what the run actually wrote through `main`.
**Which one is not established.** I read the call site and stopped, because
the last three claims each cost a review cycle to a candidate I had not
tested. The next claim prints the five operands beside what `main` wrote.

### Verification spending

No new suite receipt. `verification-17.json` (47 checks, 0 failures,
26.044478883006377s) stands; last claim's confirming run measured 26.036s and
the reviewer has folded it in.

Cumulative MEASURED for W247941, adopting the reviewer's arithmetic:
**289.943033529s**, plus the diagnostic runs, which I do not receipt, and the
earlier ~120s timeout execution whose overlap remains UNKNOWN.

State: returned INCOMPLETE through baton.bug.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 250159" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
