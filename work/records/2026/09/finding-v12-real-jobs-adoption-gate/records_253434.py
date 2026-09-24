"""Claim-253434: the composed abandonment route exists; its proof does not yet."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 253434; RETURNED INCOMPLETE

Review 2026-09-24T03:32:55Z answered the three behaviours I had left unread and
told me to implement without another review per research step. **The capability
is written.**

## DONE — the composed route, in the two owned product files

`v12/python/tools/single_worker.py` — `_Worker.abandon_attempt(attempt_id=,
reason=, stage=None)`, exposed on the composed operations beside
`cancel_attempt`. It composes the three operands
`intake.abandon_attempt` needs and calls it; nothing is re-implemented.

  * **roots from `assignment_workspace`, not `_mounted`.** The review's own
    finding: `_mounted` ALLOCATES, lets a stage composition answer a different
    pair, and refuses historical mounts — right for a start, wrong for a
    removal that must allocate nothing. This adopts the same pair
    `cancel_attempt` and `reconcile` use.
  * **the runtime is proved first.** `_credential`'s `not-started` branch
    MATERIALIZES a credential; abandonment ends an attempt whose runtime
    started, so that is refused by name before `_credential` is reached. A
    removal must not create a secret on its way to destroying one.
  * **the launch delivery is ADOPTED and its absence is a fact.**
    `launch.adopt` answers None for a delivery no container mounted; a removal
    that authored a replacement would turn lost evidence into state that looks
    valid. `stage` is optional for exactly that reason.
  * **so deleted or read-only roots and a removed credential reach
    `OrphanTeardown` or `None`** rather than forcing recreation — the replay
    property the review asked for.

`v12/python/tools/stage_execution.py` — `abandon_attempt` routes by the
RECORDED ALLOCATION exactly as `cancel_attempt` does, and fails closed three
ways: no recorded allocation, a worker this deployment does not compose, and a
worker composing no such capability. Never by guessed role.

## Evidence for what is written

  * `tests.tools.test_single_worker` — **162 tests, OK**, the suite that owns
    the edited worker file.
  * `tests.tools.test_stage_execution` — 424 tests, **12 errors**, and those
    errors are PRE-EXISTING: the identical suite run against the UNMODIFIED
    pinned snapshot's `tools/` answers the same 424/12. Proven by running it,
    not asserted. `PREEXISTING-ERRORS-247666.json` in the review-proof dossier
    records the same classes from claim 247666.

## NOT DONE

  1. the supervisor's explicit shutdown declaration for its own failed or
     stopped attempts;
  2. the seven acceptance boundaries with a fake adapter — receiptless fault,
     prior cancellation fence, repeat/crash replay, wrong allocation and
     missing capability, adapter refusal and uncertain absence, positive
     `retained` cleanup including the credential and launch roots, and an
     unaffected successful output. **Nothing here is verified as behaviour
     yet**; the two suites above establish only that the edit breaks neither;
  3. the new digest-bound manager snapshot, then fresh-run commands;
  4. the two operator grants documents with pure and fake-boundary validation
     and readback;
  5. the executed-image fault diagnosis.

## Standing constraints

The preserved deployed snapshot is immutable and was READ only — including for
the pre-existing-error proof. The failed instance stays preserved and
read-only. No live rerun, deployed-store mutation, container deletion or
cleanup execution.

## Ownership

baton.claude owns this dossier and, from claim 253397,
`v12/python/tools/single_worker.py` and `v12/python/tools/stage_execution.py`.
Reviewer-owned and immutable: ASSESSMENT-249338.md, every `review-*.md` and
`review-*.json`/`.log`. The owner owns the FINDING entries of 2026-09-23 and
2026-09-24.
"""

PROGRESS = """
## 2026-09-24 — baton.claude, claim 253434

### The route exists now, and the reviewer's findings are what made it writable

Three behaviours I had recorded as unread came back answered: `_adopted` runs
BEFORE the answered-terminal check, `_mounted` allocates and refuses historical
mounts, and a started `_credential` uses live proof or orphan teardown. That was
enough to design the capability instead of guessing at it.

`single_worker._Worker.abandon_attempt` composes the three operands
`intake.abandon_attempt` needs and calls it. The decisions worth naming:

  * roots come from `assignment_workspace`, not `_mounted` — a removal must
    allocate nothing, and `_mounted` allocates;
  * the runtime is proved attached BEFORE `_credential` is reached, because
    that helper's `not-started` branch materializes a credential and a removal
    must not create a secret on its way to destroying one;
  * the launch delivery is ADOPTED, and absent is a fact rather than a failure
    — `stage` is optional so a caller that cannot name one still gets a
    correct teardown rather than an authored replacement.

Together those give the replay property the review asked for: deleted or
read-only roots and a removed credential reach `OrphanTeardown` or `None`
instead of forcing a recreation.

`stage_execution.abandon_attempt` routes by the recorded allocation exactly as
the stop does, and fails closed three ways — no allocation, a worker this
deployment does not compose, and a worker with no such capability. Never by
guessed role.

### The 12 errors are not mine, and I proved it rather than saying it

`tests.tools.test_single_worker` passes 162. `tests.tools.test_stage_execution`
reports 424 tests with 12 errors — `'SimpleNamespace' object has no attribute
'reconciles'` and `'object' object has no attribute 'proposal'`, neither near
anything I touched.

Rather than assert that, I ran the identical suite against the UNMODIFIED
pinned snapshot's `tools/` with the checkout's `tests/` — 424 tests, 12 errors,
the same. So they pre-date this change. `PREEXISTING-ERRORS-247666.json` in the
review-proof dossier records the same classes from claim 247666.

### What is NOT established

Any behaviour of the new route. The two suites show the edit breaks nothing;
they do not exercise an abandonment. The seven boundaries, the supervisor
declaration, the snapshot, the grants and the image diagnosis are all
outstanding, and PLAN.md lists them individually.

### Verification spending

`tests.tools.test_single_worker` — 162 tests, OK, 10.167s.
`tests.tools.test_stage_execution` — 424 tests, 12 pre-existing errors,
162.089s; and the same suite on the unmodified pinned `tools/` at 163.197s,
which is the proof those errors pre-date the change.

These are PRODUCT suites rather than this dossier's named module, so they are
disclosed separately: the named suite subtotal stays **1047.869180986s**
(`verification-27.json`, 85 checks, 0 failures, pins agree), and
**335.453s** of product-suite time is disclosed beside it. One earlier
`test_stage_execution` attempt was killed by a 120s command timeout before it
could report; that run is unmeasured, and it is the same kind of overlap the
earlier ~120s unknown records.

State: returned INCOMPLETE through baton.bug with the remaining scope named.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 253434" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
