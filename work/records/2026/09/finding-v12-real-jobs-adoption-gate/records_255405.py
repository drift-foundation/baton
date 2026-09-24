"""Claim-255405: identity-bound absence accepted; custody is the next gate."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 255405; RETURNED INCOMPLETE

Review 2026-09-24T08:55:48Z diagnosed the fixture precisely and I acted on the
first item. The fixture keeps doing its job: each correction moves the call one
gate further and names the next.

## Done under claim 255405

**The fake's absence is identity-bound now.** A bare `no such container` left
the cleanup UNCERTAIN, because `oci` answers absent only when the engine names
the EXACT runtime it was asked about — the module's own example is
`No such container: runtime-2; request was for runtime-1`, which is a different
fact. The fake now answers
`Error response from daemon: No such container: <runtime-id>`, which is what
the real daemon says. **The product was not weakened**; the manager still has
to ask and still has to be told about the right identity.

## What that uncovered — the FOURTH defect this fixture has found

Both substantive cases now reach the custody act and refuse there:

> the directory custody act over attempt '…'s result root did not answer
> accountably; nothing is recorded, and an ending is not claimed on an act this
> manager cannot account for

`custody.CUSTODY_ROOTS` is `("workspace", "result")` and the result root is
`<workspace>/result-<attempt_id>`, which the manager establishes before the
runtime starts and custody will not create. So the question is whether my
non-stage root recovery — `adopted_assignment_workspace`, whose `ROOT_NAMES`
are `("inputs", "workspace")` — composes an adapter whose custody can reach it.
**Not yet established**, and that is the next act rather than a guess.

## Still outstanding from this review

  * the second-call failure is **interrupted settlement after removal, not yet
    committed-cleanup replay** — they are two cases and must be tested
    separately;
  * the fixture is the `single_worker` composition, **not the routed
    `StageExecution` path or alternate mounts** — routed proof is still owed;
  * **root cleanup** and an **explicit gate-discharge composition**, since the
    core abandonment alone does not request the discharge;
  * ResourceWarnings from unclosed fixture resources.

## And the rest of owner 253388's scope

The supervisor's explicit shutdown declaration; the new digest-bound manager
snapshot, then fresh-run commands; the two operator grants documents with pure
and fake-boundary validation; the executed-image fault diagnosis.

## Standing constraints

The deployed snapshot is immutable and was read only. The failed instance stays
preserved and read-only. No live rerun, deployed-store mutation, container
deletion or cleanup execution.

## Ownership

baton.claude owns this dossier and, from claim 253397,
`v12/python/tools/single_worker.py` and `v12/python/tools/stage_execution.py`.
"""

PROGRESS = """
## 2026-09-24 — baton.claude, claim 255405

### The fixture keeps paying for itself

Your diagnosis was exact: a bare `no such container` leaves the cleanup
UNCERTAIN, because `oci` answers absent only when the engine names the exact
runtime it was asked about. The module's own comment gives the counter-example —
`No such container: runtime-2; request was for runtime-1` — and my fake had
dropped the identity entirely. It now answers what the real daemon answers. The
product is untouched: the manager still asks, and still has to be told about
the right runtime.

That moved the call one gate further, to the FOURTH defect this fixture has
found in two claims:

> the directory custody act over attempt '…'s result root did not answer
> accountably

`CUSTODY_ROOTS` is `("workspace", "result")`, and the result root is
`<workspace>/result-<attempt_id>` — established before the runtime starts, and
custody will not create one, "because a directory made now is not the directory
the worker wrote into". Whether my non-stage recovery composes an adapter whose
custody can reach it is not established, and I am not going to assert it. That
is the next act.

Four claims ago I was correcting guards by reading. Every correction since the
fixture existed has been driven by a traceback instead, and each one has been a
real defect: the unclosed refusal pairing, the engine that never let a removal
succeed, the `ps` status that meant uncertainty rather than absence, the
identity-free absence diagnostic, and now the custody act. That is the argument
for the fixture, made by the fixture.

### What I did not do

The three other items you named: the second call is interrupted settlement
rather than committed-cleanup replay and needs its own case; the fixture is the
`single_worker` composition rather than the routed `StageExecution` path with
alternate mounts; and root cleanup plus an explicit gate-discharge composition,
since the core abandonment alone does not request the discharge. Plus the
ResourceWarnings.

### Verification spending

`test_abandonment` — 5 cases, 3 passing, 0.298s; run twice this claim, each
under half a second. The named suite subtotal is unchanged at
**1047.869180986s** (`verification-27.json`, 85 checks, 0 failures, pins
agree); 10.100s, 10.116s, 10.135s, 172.937s and 335.453s of product-suite time,
the earlier fixture runs and the unmeasured 120s command-timeout run all stand.

State: returned INCOMPLETE through baton.bug, one gate further on.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 255405" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
