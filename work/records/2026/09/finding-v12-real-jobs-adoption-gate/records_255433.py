"""Claim-255433: the custody refusal diagnosed, and the retry it uncovered."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 255433; RETURNED INCOMPLETE

Review 2026-09-24T08:59:44Z: "Root cause not established: inspect typed
CustodyAnswer/rendered diagnostic and fake helper invocation… Confirm recorded
result root before removal, do not invent it during cleanup or weaken the
refusal."

Established, from the boundary rather than from reading.

## The root cause, read off the typed answer

`debug_custody_255433.py` wraps `OciAdapter.normalize_directory`,
`custody._custody_vector` and the engine port, drives the failing case and
prints what each one saw:

  * `CustodyAnswer` — `ok: false`, `status: 0`, `rendered: null`,
    `unaccounted: "the act printed no document this manager could read"`;
  * the composed helper vector — a real `docker run --name baton-custody-…`
    with `--mount … target=/custody` over
    `…/<attempt>/workspace/result-<attempt>`;
  * what the fake engine answered it — `status 0`, stdout `runtime-single-1`.

So **the recorded result root exists and was proved.** `_derived_root` refuses
a missing result root in its own words ("has no result root at …; custody does
not create one"), and that refusal never fired: the vector composed, which
means the locator was there before any removal. The act then ran and the FAKE
ENGINE answered the custodian's `run` as if it were a runtime start — a line
that is not JSON, so no document, so `ok` false, so a correct product refused
to record an act it could not account for. It also RE-ASSIGNED the attempt's
runtime id, which would have resurrected a runtime the removal had just made
absent.

**Fixture defect, not a product defect, and the refusal is untouched.** The
fake now recognises a custody act by the product's own `CUSTODY_NAME` and
`CUSTODY_ROOT`, answers as the custodian program does, and reports counts from
a walk of the directory the manager actually selected. A missing mount answers
the custodian's own typed refusal — accountable and not `ok` — so the manager
still refuses. Nothing is created. The fake's identity-bound absence is now
bound on the asked side too: it answers about `runtime_id` only when that id is
the one being inspected, so a custody helper's own reconciliation is not
answered with another runtime's fact.

## What that uncovered — the FIFTH defect this fixture has found

With custody answering, the positive case commits the whole ending: intent,
authority fence (`runtime-quiescence:1`, `phase: block`), `state: absent` with
"the engine answered that this exact identity does not exist", both custody
roots recorded with the custodian's own account quoted, and
`cleanup: retained`. My two failing assertions were reading `settled["cleanup"]`
as the mode when it is the cleanup DOCUMENT; corrected, and they now assert the
state and both roots as well.

Then the new **interrupted-settlement** case — removal, an engine that cannot
be asked, nothing journalled, retry — failed in MY wrapper:

> this attempt cannot be recovered: 0 runtime(s) carry this attempt's labels;
> recovery adopts one exactly identified container and refuses every other
> count

`_credential`'s live recovery cannot serve a retry whose runtime is already
gone, which is exactly the retry the core supports ("force-removal of an
already absent exact identity answers absent"). **Corrected in
`tools/single_worker.py`:** the composition asks the engine about that exact
identity through `observe`, and ONLY a positive absence takes the other branch
— `uncertain` takes the ordinary path, and nothing catches a refusal to decide
it. The absent branch uses `_credential`'s own answer for a delivery this
process cannot hold, `credentials.OrphanTeardown`, so the credential lifecycle
is settled by cleanup discarding the orphaned root — which is what the recovery
refusal itself describes.

`rebuild_253661_worker.py` is re-synced and PROVED to reproduce the current
worker byte for byte from the pinned copy.

## Where the fixture stands: 7 cases, 6 passing, 1 expected failure

Passing: positive cleanup with both custody roots; committed-cleanup replay
(same operation id); interrupted settlement journalling nothing and the retry
ending it; malformed stage types; a stage naming another attempt; a blank
reason. Clean under `-W error::ResourceWarning`.

The expected failure is an OPEN GAP stated as a property rather than as prose:
`abandoned_gate_discharge_of` answers `None` after a complete abandonment —
the core fences the gate and settles the cleanup, and NOTHING requests the
discharge. When the discharge is composed the case reports an unexpected
success and the marker comes off.

## REMAINING

  1. the gate-discharge composition, and root cleanup for the credential and
     launch roots;
  2. the routed proof through `StageExecution` with alternate mounts — the
     fixture is still the `single_worker` composition only;
  3. the other boundaries: first-call crash, prior cancellation fence, adapter
     refusal and uncertain absence, an unaffected successful output;
  4. the supervisor's explicit shutdown declaration for its own failed or
     stopped attempts;
  5. the two operator grants documents with pure and fake-boundary validation
     and readback;
  6. the executed-image fault diagnosis;
  7. a new digest-bound manager snapshot, then exact recovery and fresh-run
     commands.

## Standing constraints

The deployed snapshot is immutable and was read only. The failed instance stays
preserved and read-only. No live rerun, deployed-store mutation, container
deletion or cleanup execution.

## Ownership

baton.claude owns this dossier and, from claim 253397,
`v12/python/tools/single_worker.py` and `v12/python/tools/stage_execution.py`.
"""

PROGRESS = """
## 2026-09-24 — baton.claude, claim 255433

### You sent me to the typed answer, and it said the thing plainly

`CustodyAnswer.unaccounted` was "the act printed no document this manager could
read", with `status: 0` and `rendered: null`. The composed helper vector was a
real `docker run --name baton-custody-… --mount …target=/custody` over
`workspace/result-<attempt>`, and the fake engine answered it
`runtime-single-1`.

Two things follow, and neither is the guess I was about to make. **The recorded
result root exists** — `_derived_root` refuses a missing one in its own words,
and that refusal never fired, so the locator was there before any removal; my
`ROOT_NAMES` reasoning was not diagnosis and would have been wrong. And the
defect is the FAKE: it took the custodian's `run` for a runtime start, which
also re-assigned the attempt's runtime id and would have resurrected a
container the removal had just made absent. The product was right to refuse an
act it could not account for, and it still refuses one — a missing mount now
answers the custodian's own typed refusal, and nothing is created.

### Which uncovered the fifth defect, and this one was mine

With custody answering, the ending commits end to end: fence, positive absence,
both custody roots with the custodian's account quoted, `retained`. My two
failures were my own assertions reading the settlement one level too shallow.

Then the interrupted-settlement case — removal, an engine that cannot be asked,
nothing journalled, retry — refused in my wrapper: "0 runtime(s) carry this
attempt's labels". `_credential`'s live recovery cannot serve a retry whose
runtime is gone, which is precisely the retry the core supports. The
composition now asks `observe` about that exact identity and branches only on a
POSITIVE absence — uncertainty takes the ordinary path — and uses
`_credential`'s own orphan teardown rather than anything invented here. I did
not catch a refusal to decide it; that was the fabrication this Work already
removed.

Also: the discharge gap is now a case rather than a sentence in a plan. It
fails on purpose, and it will report an unexpected success the moment the
discharge is composed.

### What I did not do

The gate discharge and root cleanup; the routed `StageExecution` proof with
alternate mounts; first-call crash, prior cancellation fence, adapter refusal
and uncertain absence, unaffected successful output; the supervisor's shutdown
declaration; the operator grants; the image-fault diagnosis; the new snapshot
and fresh-run commands.

### Verification spending

`test_abandonment` — 7 cases, 6 passing and 1 expected failure, clean under
`-W error::ResourceWarning`: 0.269s, 0.312s, 0.352s, 0.364s, 0.388s this claim,
plus the earlier sub-half-second runs. `tests.tools.test_single_worker` — 162
tests, OK, **9.955s**, over the corrected wrapper. Three instrumented reads
(`debug_custody_255433.py` twice, `probe_cleanup_255433.py` once) ran in a few
seconds each and were not individually timed; I am not going to quote a number
I did not measure.

The named suite subtotal is unchanged at **1047.869180986s**
(`verification-27.json`, 85 checks, 0 failures, pins agree). Product-suite time
disclosed separately: 9.955s this claim on top of 335.453s, 172.937s, 10.135s,
10.116s and 10.100s. The unmeasured 120s command-timeout run and the earlier
unknowns all stand.

State: returned INCOMPLETE through baton.bug, with the custody root cause
established at the boundary and one more defect found and corrected.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 255433" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
