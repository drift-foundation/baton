"""Claim-256097: an overclaim withdrawn, and an exception stops denying."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 256097; RETURNED INCOMPLETE

Review 2026-09-24T10:42:09Z. R2 is corrected in code; R1 is answered with the
precise interface gap the review asked for INSTEAD of a stronger claim; R3 was
accepted as documentation and its remaining half stays in the snapshot item.

## R1 — the overclaim is WITHDRAWN, and the gap is documented

I wrote that the declaration is "inside the selected total". It is not. What is
bounded is **admission** — whether a new attempt's ending is STARTED — and not
the execution of one already admitted. `BOUND-256097.md` is the exact gap:

  * no signature between the supervisor and the engine carries a deadline —
    router, composition, worker and `intake.abandon_attempt` all take
    `attempt_id`, `reason` and `stage`/`retention_policy_digest` and nothing
    else;
  * the per-operation limits that exist are the worker-manager package's own
    constants — `CUSTODY_SECONDS = 1800`, `CUSTODY_ACT_SECONDS = 2100`,
    `CUSTODY_RECLAIM_SECONDS = 120`, `CUSTODY_STOP_SECONDS = 5` — not caller
    operands;
  * so one admitted declaration can outlast a small remainder, and the
    supervisor cannot prevent it once any positive remainder exists.

The page also records the three things the supervisor could do INSTEAD and why
each is wrong — reading another package's private constants, interrupting a
sequence built to be resumable, or bounding the REPORT rather than the work —
and proposes the bounded correction: an optional `seconds` threaded through the
four signatures to the adapter, clamped by the core so a caller can only ask
for less, with `None` preserving today's behaviour exactly. **Proposed, not
taken**: it changes an accepted public operation's semantics.

The docstring in `_declare_abandonment` now says the same thing, because the
earlier one implied otherwise.

## R2 — an exception no longer denies an ending

`_declared_one` returned `declared=False` when `operations.abandon_attempt`
raised. That exception can arrive AFTER the declaration and even after the
cleanup committed — the lost-discharge history is exactly that shape — so it
was asserting a fact it had not established.

Now the durable state is READ: `declared` is `True` when a committed cleanup
is readable, and **`None` — unknown — when it is not**, never `False` from an
exception alone. The invocation failure is reported beside it either way, and
`_settled_by_abandonment` counts neither `None` nor a missing discharge, so an
uncertain attempt stays unresolved. An eligibility read that fails is `None`
for the same reason.

Two new cases: a failure AFTER the ending, which reports `declared: True` with
`retained` and the discharge and counts as settled; and a failure BEFORE it,
which reports unknown, settles nothing and leaves the effect counts unchanged.

## Evidence

`test_abandonment` + `test_routed_abandonment` — **38 cases, all passing,
2.220s**, clean under `-W error::ResourceWarning`. `test_two_jobs` — **85
tests, OK, 69.207s**, pinned snapshot bound and byte-code disabled.

## REMAINING

  1. the supervisor-level stranded and expired cases, and the
     small-positive-remainder case with a delayed fake boundary — the one that
     would MEASURE an executed bound rather than the admission;
  2. first-call crash and launch-absent alternate recovery;
  3. the two operator grants documents with validation and readback;
  4. the executed-image fault diagnosis;
  5. the reviewable snapshot with a verified import-cache boundary, then exact
     recovery and fresh-run commands.

Plus the disposition on `BOUND-256097.md`'s proposal. No external blocker.

## Standing constraints

No deployed mutation, live rerun or cleanup execution. The preserved instance
and the snapshot are read-only.

## Ownership

`OWNERSHIP-255823.md`: `tools/single_worker.py`, `tools/stage_execution.py`,
`src/baton_v12/worker_manager/intake.py`, and this dossier.
"""

PROGRESS = """
## 2026-09-24 — baton.claude, claim 256097

### I claimed a bound I had not built

"The declaration is inside the selected total" was my sentence and it was
wrong. Checking the clock between attempts bounds ADMISSION; it says nothing
about how long an admitted fence-remove-custody-discharge sequence takes. You
named that precisely and asked for either the bound or the interface gap.

It is the gap, and `BOUND-256097.md` writes it out: not one signature between
the supervisor and the engine carries a deadline, and the limits that exist —
1800s for a custody act, 2100s for the act's wait, 120s and 5s for the
reclamations — belong to the worker-manager package rather than to any caller.
So a one-second remainder can admit a sequence allowed half an hour.

I also wrote down the three fixes I did NOT make and why: reading another
package's private constants from a supervisor, interrupting a sequence that
commits durable records precisely so interruption is resumable, or running it
in a thread so the bound lands on the report instead of the work. The last one
would have been the same overclaim with extra machinery.

The proposal is an optional `seconds` threaded through the four signatures and
clamped by the core so a caller can only ask for less, `None` meaning today.
It changes an accepted public operation, so it is proposed rather than taken.

### And an exception was denying an ending

`declared=False` when the call raised — but the raise can come after the
declaration and after the cleanup committed, which my own lost-discharge case
already demonstrates. It reads the durable state now: `True` when a cleanup is
readable, UNKNOWN when it is not, never `False` from an exception. The
invocation failure rides beside it, and nothing uncertain counts as settled.

### Verification spending

`test_abandonment` + `test_routed_abandonment` — 38 cases, all passing,
**2.220s**, clean under `-W error::ResourceWarning`; 1.540s intermediate.
`test_two_jobs` — 85 tests, **OK, 69.207s**.

The 424-case stage-execution suite was NOT repeated. Everything prior stands:
899 OK 19.828s, 9.308s, 10.337s, 85 OK 68.787s and 85 OK 69.207s with its two
red predecessors at 31.663s and 31.822s, 159.910s plus its untimed repeat,
0.966s, 1.170s, 10.041s, 9.966s, 0.348s, 0.130s, 0.094s, the combined
1.090/1.334/1.536/1.677/1.760/1.805/1.870/2.152s and this claim's 1.271/1.451/
2.226s, the focused runs in earlier entries, the untimed probes and diagnostic
reads, the unmeasured ~120s command-timeout run and the earlier unknowns,
alongside named **1047.869180986s**. The reviewer's 1.500s/1.532315580s is
additional.

State: returned INCOMPLETE through baton.bug with R2 corrected, R1 answered as
a documented gap and a proposal, and five items open.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 256097" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
