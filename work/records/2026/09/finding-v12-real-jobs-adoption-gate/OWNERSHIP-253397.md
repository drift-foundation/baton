# Exclusive product-file ownership, and the capability it is for

Owner 253388 selected the bounded composition capability review
2026-09-24T01:41:28Z proposed, and required exclusive ownership of the two
product files to be coordinated **before** edits. This document is that
coordination artifact, and the design pin the capability is implemented
against.

## Claimed, exclusively, by baton.claude for W247941

    v12/python/tools/single_worker.py
    v12/python/tools/stage_execution.py

**Neither file has been edited under claim 253397.** Everything below is read
from the current tree and recorded so the next claim implements against a
specification rather than a guess. The preserved deployed snapshot
`/home/sl/baton-runs/independent-review-247947/manager-source` is immutable and
is not the edit target; the edit target is the checkout, and a NEW reviewed
snapshot is taken afterwards.

## Why a design pin and not the edit

The adapter is the whole risk. Claim 172346 measured what a wrongly composed
one costs: an observing adapter made `authorize_failed_start_cleanup` take its
not-delivered branch, the member was ended, and the credential root and the
launch root both stayed on disk. Abandonment tears down deliveries a start
already created, so it needs the RECOVERED adapter, not the observing one.

`cancel_attempt` is the wrong template for that reason. It composes
`self._adapter(roots, None, None, None)` over
`workspaces.assignment_workspace(...)` — correct for a stop, which "reads only
the runtime id and the operation id out of its request", and wrong for a
removal that owns deliveries.

## The construction the capability must reuse

`_Worker.ending` already recovers exactly this, for an attempt it did not start
in this process (`tools/single_worker.py`, the answered-ending path):

```python
launched = self._adopted(stage)
state    = attempt_runtime_of(self.control, attempt_id)
roots    = self._mounted(stage, attempt_id, checkpoint=False)[0]
delivery, orphan = self._credential(attempt_id, state, roots, launched)
adapter  = self._adapter(roots, delivery, orphan, launched)
```

That is the sequence to reuse, with **one deliberate difference**: the ending
refuses unless the exchange reports an `answered` terminal, and abandonment
exists precisely for the case where it does not. So the capability shares the
adapter recovery and must NOT share the terminal precondition.

What must be established before writing it, and has not been:

  1. whether `_adopted(stage)` and `_mounted(stage, …)` behave for a FAULTED
     attempt, and what each refuses — the ending reaches them only after a
     correlated answered terminal, so their behaviour here is unread;
  2. whether `_credential` can recover a delivery for an attempt whose worker
     faulted, and what it answers when the credential root is already gone;
  3. what `stage` document the capability needs and how the routing supplies
     it — `stage_execution.cancel_attempt` routes by `allocation_of(attempt)`
     with no stage in hand, and abandonment may need one.

## The shape the review specified

  * **`single_worker`**: a capability that owns the per-attempt adapter and
    custody construction above and calls the existing
    `intake.abandon_attempt(control, port, adapter, attempt_id=…, reason=…,
    retention_policy_digest=…)`. Nothing re-implemented.
  * **`stage_execution`**: route by recorded allocation exactly as
    `cancel_attempt` does, and **fail closed** on an unknown allocation, a
    worker this deployment does not compose, or a worker composing no such
    capability.
  * **the supervisor**: supply an EXPLICIT selected shutdown declaration, for
    its own failed or stopped attempts only. Fault observation alone must not
    abandon arbitrary work — the product is emphatic that "calling this
    operation IS the declaration" and that no timer decides.
  * **the answered path is untouched.**

## The acceptance the review specified

Deterministic, at the normal boundary, with a fake adapter: receiptless fault;
prior cancellation fence; repeat and crash replay; wrong allocation and missing
capability; adapter refusal and uncertain absence; positive `retained` cleanup
including the credential and launch roots; and an unaffected successful output.
**A successful call is not positive cleanup** — the cleanup record is.

Then a new digest-bound manager snapshot, and only then a fresh-run command.
