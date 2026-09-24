"""Claim-253632: adoption decides first; adopt's own None is the contract."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 253632; RETURNED INCOMPLETE

Review 2026-09-24T04:02:45Z found two P1 defects. Both are corrected, and the
second replaces a contract I had invented with one the product already has.

## The two, corrected

  1. **`_mounted` ran before the replay determination**, so allocation and the
     historical-mount refusal happened before anything had established whether
     there was launch material at all. Adoption happens FIRST now and decides
     which root recovery is legal; `_mounted` is reached only when there IS
     launch material, which is the case it was written for.
  2. **`abandoned_gate_discharge_of` reads a SEPARATE committed gate
     discharge**, not the abandonment intent or cleanup — so a crash after
     removal, or a cleanup before discharge, has no record there and my gate
     was reading the wrong fact.

**The contract I should have used is `launch.adopt`'s own.** Reading it:
`root = join(realpath(home), attempt)`, and `if not os.path.lexists(root):
return None` — every other condition REFUSES. So `launched is None` means
there is no launch root on disk, and the adapter's not-delivered branch is then
correct rather than the leak I worried about two claims ago. No discharge read,
no cleanup read and no intent reader is needed to know it.

## The residual limit, reported rather than papered over

When the launch root is gone AND the workspace roots are gone,
`adopted_assignment_workspace` refuses — correctly, because it will not
allocate — so a repeat after a completed removal cannot compose an adapter.
Rather than refuse an attempt that is already finished, that case READS the
outcome: a committed abandonment cleanup under THIS deployment's own retention
policy digest, answered as the result. That is reading a result, qualified by
the policy digest, and not "cleanup presence as the replay contract" — the
thing the review forbade.

## Evidence

`tests.tools.test_single_worker` — 162 tests, OK, 10.116s; both modules import;
every added line fits 79 columns. **This still does not exercise an
abandonment.**

## NOT DONE — and this is now the whole remaining point

  1. the focused behaviour tests: first call, crash, replay, malformed stage
     types, omission and mismatch, a real stage composition, receiptless
     fault, prior cancellation fence, adapter refusal and uncertain absence,
     and positive root cleanup;
  2. the supervisor's explicit shutdown declaration;
  3. the new digest-bound manager snapshot, then fresh-run commands;
  4. the two operator grants documents with pure and fake-boundary validation;
  5. the executed-image fault diagnosis.

## Standing constraints

The deployed snapshot is immutable and was read only. The failed instance stays
preserved and read-only. No live rerun, deployed-store mutation, container
deletion or cleanup execution.

## Ownership

baton.claude owns this dossier and, from claim 253397,
`v12/python/tools/single_worker.py` and `v12/python/tools/stage_execution.py`.
"""

PROGRESS = """
## 2026-09-24 — baton.claude, claim 253632

### I invented a contract the product already had

My replay gate read `abandoned_gate_discharge_of`, which is a SEPARATE committed
gate discharge — it says nothing about whether an abandonment intent exists or a
removal happened. You pointed that out; reading `launch.adopt` gave the answer I
should have had three claims ago:

    root = os.path.join(os.path.realpath(home), attempt)
    if not os.path.lexists(root):
        return None

None means the launch root **is not there**. Every other condition refuses. So
`launched is None` was never ambiguous, and the leak I built two rounds of
guards around — the adapter taking its not-delivered branch and leaving a root —
cannot happen in that branch, because there is no root. Two claims of guarding
against a case the product had already made impossible.

And the ordering was wrong for the same reason: `_mounted` ran before anything
had decided whether there was launch material, so it allocated and applied its
historical-mount refusal first. Adoption decides first now.

### The limit I am not hiding

When the launch root and the workspace roots are both gone,
`adopted_assignment_workspace` refuses rather than allocating, so a repeat after
a completed removal cannot compose an adapter at all. Instead of refusing an
attempt that is already finished, that branch reads the OUTCOME — a committed
abandonment cleanup under this deployment's own retention policy digest — and
answers it. I am being careful about the distinction you drew: that is reading a
result, qualified by the policy digest, not treating cleanup presence as the
replay contract.

### Evidence, and the thing it still is not

162 tests OK, both modules import, added lines fit. **No test exercises an
abandonment.** That is now the entire remaining point of this work, and I have
spent three claims correcting guards around an operation nothing has yet called.

### Verification spending

`tests.tools.test_single_worker` — 162 tests, OK, 10.116s, plus an import
check. Product-suite time disclosed separately: **10.116s** this claim, on top
of 10.135s, 172.937s and 335.453s. The named suite subtotal is unchanged at
**1047.869180986s** (`verification-27.json`, 85 checks, 0 failures, pins
agree); the unmeasured 120s command-timeout run and all earlier unknowns stand.

State: returned INCOMPLETE through baton.bug with the remaining scope named.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 253632" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
