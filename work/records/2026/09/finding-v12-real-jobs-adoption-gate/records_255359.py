"""Claim-255359: the fixture exists, RUNS, and calls the operation."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 255359; RETURNED INCOMPLETE

Owner 255356: "First deliver and run a focused fixture invoking actual composed
abandonment and replay through fake engine/provider boundaries; use its
failures to correct the implementation."

**`test_abandonment.py` exists, runs, and calls the operation.** Five of my
claims corrected guards around code nothing had ever executed; this one
executed it.

## The fixture

It subclasses the product's own `AFaultedTerminalSurvivesTheContainerThatWroteIt`,
which drives a REAL correlated faulted terminal — the real `baton_worker` over
the real exchange, an agent that fails its turn, then the container exits
unasked. That is the live two-Job state exactly: runtime started, worker never
answered, `fault_code: agent`, no receipt. The engine is that fixture's fake CLI
runner, extended to answer a removal, so no container, image, provider or
network is reached.

## What it found — three defects, by running

  1. **`category="refused", code="schema"` is not a closed pair**, and this
     build ASSERTS on an unclosed pairing rather than raising the refusal — so
     my typed refusal would have crashed on every malformed stage. It is
     `integrity`/`schema`. Corrected in both owned files.
  2. **The fake engine answered `inspect` with `Running: True` forever**, so
     the force-removal was followed by an observation that still saw the
     runtime and the abandonment settled `failed`. Fixture work: a removal now
     answers `ps` with an EMPTY list — absence — and `inspect` non-zero. My
     first attempt answered `ps` non-zero and the manager correctly called
     that "the engine could not list runtimes", which is uncertainty, not
     absence.
  3. **The replay path does not survive the recovery my wrapper performs.**
     The second call refuses with "0 runtime(s) carry this attempt's labels;
     recovery adopts one exactly identified container" — the container is gone,
     so `_credential`/`_adapter` recovery cannot complete, while the CORE's own
     replay would not have needed it. This is the reviewer's "interrupted
     recovery without allocation" case, now reproduced rather than argued
     about.

## Where it stands: 3 of 5 pass

Passing — malformed stage types refuse without crashing; a stage naming another
attempt is refused; a blank reason is refused.

Failing, and both are real:

  * **the first call commits no abandonment cleanup** readable at
    `abandonment_cleanup_of(..., retention_policy_digest=config[...])`. The
    call no longer raises, so the operation ran; whether the record is absent
    or I am reading it under the wrong digest is the next thing to establish.
  * **the repeat cannot recover**, per defect 3 above.

## REMAINING

  1. those two failures, which are the next corrections;
  2. the rest of the boundaries: first-call crash, prior cancellation fence,
     adapter refusal and uncertain absence, positive root cleanup including
     credential and launch roots, and an unaffected successful output;
  3. the supervisor's explicit shutdown declaration;
  4. the new digest-bound manager snapshot, then fresh-run commands;
  5. the two operator grants documents with pure and fake-boundary validation;
  6. the executed-image fault diagnosis.

## Standing constraints

The deployed snapshot is immutable and was read only. The failed instance stays
preserved and read-only. No live rerun, deployed-store mutation, container
deletion or cleanup execution.

## Ownership

baton.claude owns this dossier and, from claim 253397,
`v12/python/tools/single_worker.py` and `v12/python/tools/stage_execution.py`.
"""

PROGRESS = """
## 2026-09-24 — baton.claude, claim 255359

### The operation has now been called

Five claims of mine corrected guards around code nothing had executed. You and
the owner both said to stop doing that and run it. `test_abandonment.py` runs
it, over the product's own faulted-terminal fixture — a real correlated
`fault_code: agent` terminal written by the real `baton_worker`, with the
container exiting unasked, which is the live two-Job state exactly.

It found three things in one sitting, which is the argument for having done it
five claims ago:

**My typed refusal would have crashed.** `refused`/`schema` is not a closed
pair and this build ASSERTS on an unclosed pairing instead of raising — so
every malformed stage would have hit an `AssertionError` rather than the
refusal I wrote. It is `integrity`/`schema`. I had "fixed" the malformed-stage
crash two claims ago and introduced a different one in the fix.

**The fake engine never let a removal succeed.** It answers `inspect` with
`Running: True` forever, so the force-removal was followed by an observation
that still saw the runtime and the abandonment settled `failed`. That is
fixture work, and my first attempt at it answered `ps` non-zero — which the
manager correctly read as "the engine could not list runtimes", uncertainty
rather than absence. An empty list is absence; a failed call is not.

**The replay does not survive my wrapper's recovery.** The repeat refuses with
"0 runtime(s) carry this attempt's labels" — the container is gone, so the
credential and adapter recovery cannot complete, while the core's own replay
would not have needed them. That is the interrupted-recovery case the reviewer
named, now reproduced.

### Where it stands, plainly

Three of five pass. The two that fail are the substantive ones: the first call
commits no cleanup record readable at the digest I read with, and the repeat
cannot recover. Both are next, and both are now failures with tracebacks rather
than positions in an argument.

### Verification spending

`test_abandonment` — 5 cases, 3 passing, 0.285s, run several times during
correction; each run under half a second. Product-suite time disclosed
separately as before: nothing added this claim beyond these runs. The named
suite subtotal is unchanged at **1047.869180986s**
(`verification-27.json`, 85 checks, 0 failures, pins agree); 10.100s, 10.116s,
10.135s, 172.937s and 335.453s of product-suite time and the unmeasured 120s
command-timeout run all stand.

State: returned INCOMPLETE through baton.bug, with a running fixture and two
named failures.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 255359" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
