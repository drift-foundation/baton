"""Claim-252713: the abandonment correction meets a product-path blocker.

Review 2026-09-24T01:33:27Z authorized the bounded supervisor abandonment
correction and said to finish it "unless an actual operational blocker is
encountered", while also requiring that any new product path be coordinated
before editing. Both apply here, and this records why.

I set out to add the step and could not reach the operation. What I found
instead is stated below with its citations, plus the three narrowings the same
review asked for.
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
PLACE = HERE / "SETTLEMENT-252647.md"

APPENDED = """
## Claim 252713 — the supervisor correction is BLOCKED on a product path

I tried to add the abandonment step to `two_job_supervisor.supervise` and could
not reach the operation. `intake.abandon_attempt(store, port, adapter, ...)`
needs three things, and the composed deployment gives a supervisor only the
first.

**The stage composition routes cancellation and nothing like it.**
`stage_execution`'s `cancel_attempt` exists precisely because an orchestrator
cannot perform such an act itself — it looks the attempt's recorded allocation
up, finds the worker that started it, and calls THAT composition's own
capability, refusing when the worker "composes no cancellation capability".
There is no `abandon_attempt` anywhere in `tools/stage_execution.py`: grepping
the pinned file finds the word only in unrelated prose.

**And the worker composition declines abandonment on purpose.**
`tools/single_worker.py`, in the docstring of the act that ends a stage:

> **NO ABANDONMENT AND NO RETRY.** A faulted, lost or incomplete exchange is
> REPORTED -- the projection reads it as `exceptional` -- and this composition
> does not end it. W44716's abandonment is the owner for a started attempt
> policy decides to end, and deciding that is not this vertical slice's.

So the design is deliberate: the worker reports the fault and somebody with
policy standing ends it. What is missing is a supported route from an
orchestrator to that ending.

**The adapter is the hard part, not the port.** `single_worker`'s operations
object exposes `port` publicly, but its adapter is built per attempt by a
PRIVATE `_adapter(roots, delivery, orphan, launched)` over that attempt's own
delivery and mount roots. Composing one from outside would mean reproducing
that logic — and claim 172346 already measured what a wrongly composed adapter
costs: an observing adapter made `authorize_failed_start_cleanup` take its
not-delivered branch, the member was ended, and the credential root and launch
root both stayed on disk. An orchestrator assembling its own adapter is exactly
the "second composition nobody reviewed" this product refuses elsewhere.

**THE BLOCKER, stated as the correction it needs.** The supervisor step is one
call once the deployment can route it: a capability on the worker composition
that performs `abandon_attempt` with that worker's own port and per-attempt
adapter, reached through `stage_execution` the way `cancel_attempt` is. That is
a change to `tools/single_worker.py` and `tools/stage_execution.py` — product
files this dossier does not own — so it is reported here rather than written.
Everything else the correction needs is ready: the shutdown path knows exactly
which attempts it launched, and the read in this document establishes that
neither has a receipt, a start failure, a preparation failure or any discharge.

## Claim 252713 — three narrowings the review asked for

**Empty `pending_endings` does not prove nothing was ever requested or
refused.** It proves no composed-ending obligation is registered now. It does
not locate why ordinary observation registered none, and it does not close the
question of product involvement. That question travels with the fault
reproduction rather than being answered by this read.

**The assignments are NOT unfenced, and my earlier wording said otherwise.**
The owner's entry and `run/outcome.json` both report cancellation fencing for
both assignments. What abandonment adds is its OWN fence, under an operation
identity the product keeps "distinct from both the declaration and an ordinary
cancel" (`_abandon_fence_operation_id`) — so a prior cancel fence does not
satisfy it and does not conflict with it. `docker rm` remains outside scope,
but the reason is the missing ending record and the distinct fence, not an
unfenced authority.

**The four preconditions in the section above are not the whole preflight.**
`abandon_attempt` also owns the operands, the exact assignment, the
participant through the port, the runtime adapter's `destroy_abandoned`
capability, custody capability and eligibility — in that order, each step's
proof being the next one's precondition. Until the routing blocker above is
resolved, those cannot be composed against this deployment, so this document
does not claim recovery is executable.

## Claim 252713 — the supported recovery SURFACE, identified

`tools/dogfood_operator.py` carries the operator-facing form:

```
--abandon             end an attempt whose supervising process died before it
                      could freeze output or destroy its runtime; requires
                      --abandon-reason, needs no retained evidence and no
                      credential, delivers nothing, accepts no output and
                      writes a recovery record to --evidence
--abandon-reason      the operator's own account of why this attempt is being
                      declared over; calling the command IS the declaration,
                      so no timer and no clock decides it
```

It takes `--grants` (a document of operator decisions) and `--evidence`. **What
is not yet established is whether a grants document can name an attempt of a
STAGE-EXECUTION deployment**, since this tool composes its own store, port and
adapter for a single-worker shape. Reading `read_grants`/`_held_grants` against
this instance's deployment is the bounded next act, and until it is done a
runnable command would be a guess at operands.
"""


def main():
    body = PLACE.read_text(encoding="utf-8")
    if "claim 252713" not in body.lower():
        PLACE.write_text(body.rstrip("\n") + "\n" + APPENDED, encoding="utf-8")
    else:
        raise SystemExit("REFUSED: the blocker is already recorded")
    written = PLACE.read_text(encoding="utf-8")
    for present in ("BLOCKED on a product path",
                    "NO ABANDONMENT AND NO RETRY",
                    "are NOT unfenced", "not the whole preflight",
                    "the supported recovery SURFACE"):
        if present not in written:
            raise SystemExit(f"REFUSED: {present!r} is not in the document")
    print("the blocker and the three narrowings are recorded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
