# The settlement gate, read rather than resembled — and the recovery it implies

baton.claude under claim 252647. Every fact below comes from
`settlement_252647.py`, which opens the preserved instance's Job and control
stores through `open_readonly` and asks the **public readers only** — no SQL,
no act, no cleanup, nothing started. The receipt is `SETTLEMENT-252647.json`.

Review 2026-09-24T01:25:43Z named the starting points and they were the right
ones: `ending.intent_of`, `ending.settlement_of`, `ending.ending_of`.

## What every reader answers

| Read | `attempt-79177c…` (job-a) | `attempt-d514aa…` (job-b) |
| --- | --- | --- |
| `attempts.attempt_runtime_of` | recorded, assignment fixed | recorded, assignment fixed |
| `attempts.attempt_start_failure_of` | none | none |
| `attempts.attempt_preparation_failure_of` | none | none |
| `intake.intake_receipt_of` | **none** | **none** |
| `intake.gate_discharge_of` | **none** | **none** |
| `intake.abandoned_gate_discharge_of` | **none** | **none** |
| `intake.cleanup_of` | **none** | **none** |
| `intake.abandonment_cleanup_of` | **none** | **none** |
| `output.frozen_output_of` | **none** | **none** |

And on the Job side, for all four stages at episode 1 — both implementations
and both reviews:

```
ending.intent_of(...)      -> None
ending.settlement_of(...)  -> None
ending.ending_of(...)      -> None
ending.pending_endings()   -> []
```

## The gate, stated exactly

**No composed-ending obligation was ever registered, so nothing is owed and
nothing was waiting.** `pending_endings` is empty: the manager does not consider
an ending outstanding for either attempt. The twelve cleanup sweeps the outcome
records therefore had nothing to settle — they were not blocked, they were
unemployed.

**And the distinction the review asked for**: this is a **missing result**, not
withheld cleanup authority. The chain is

> faulted terminal, no `manifest_digest` → no intake receipt → no gate
> discharge → no cleanup authority

and every link is absent in the read above, in that order. Nothing refused;
nothing was asked.

## The product HAS a door for this, and this packet does not use it

`intake.abandon_attempt` is the manager's **fourth ending**, for exactly this
case. `tools/dogfood_operator.py` says so in as many words:

> An attempt whose runtime started and whose worker never answered has no
> receipt, no start failure and no refusal — and now has its own public
> operation, authorized by an operator's explicit declaration.

It carries its own fence and its own removal order, and its `reason` is the
operator's declaration — "it reads no clock and no timer decides". Its
companions are `abandoned_gate_discharge_of` and `abandonment_cleanup_of`, both
of which answered absence above.

**So the settlement defect is in my supervisor, not in the product.**
`two_job_supervisor.supervise` closes admission, cancels through
`baseline._cancel_active`, drives sweeps and reads the cleanup journal. It has
**no abandonment step**, so an attempt that faulted without a receipt can never
reach a cleanup record however many sweeps run — which is precisely what the
live run reported and precisely why it reported it honestly as outstanding.

The ordinary receipt path must NOT be used here, and the reason is recorded in
the product: a stop ordered before the fence "recreates exactly the unsafe
boundary W44716 was introduced to remove — the authority may still consider the
worker live while its runtime is stopped". Abandonment owns its own fence, so it
must be the act, not a stop followed by a cleanup.

## The recovery these two attempts need

**PREPARED, NOT EXECUTED.** Nothing below was run; executing it is an owner act
and this claim is not authorized to perform it.

Preconditions, each of which the read above already establishes:

  1. both runtimes are **quiescent** — the owner confirmed it and
     `cancellation` in `run/outcome.json` records `requested: true` with the
     manager's own observation for both;
  2. neither attempt has an intake receipt, a start failure or a preparation
     failure — so the receiptless ending is the correct one and the ordinary
     receipt path is not available;
  3. neither has any gate discharge or cleanup, ordinary or abandoned — so this
     is a first ending rather than a repeat;
  4. the retention policy digest is the one the served deployment names:
     `sha256:0f4cd2d13c46e81cb6e721119e48b342efb3a7a0d831e241c429601aa2eae45a`.

The supported operation is `worker_manager.abandon_attempt(store, port,
adapter, attempt_id=…, reason=…, retention_policy_digest=…)`, and the supported
SURFACE that composes its `port` and `adapter` from a deployment is
`tools/dogfood_operator.py`. **This dossier does not yet print a runnable
invocation**, and the reason is specific rather than cautious: `abandon_attempt`
takes a live Authority `port` and an engine `adapter`, so the exact operand
composition for THIS deployment has to be read out of
`tools/dogfood_operator.py`'s own entry point and shown to compose against
`run/deployment.json` before it is printed as a command. That is the next act
and it is bounded.

**Readback, once it is run**, through the same readers used above — and these
are the values that mean it worked:

```
intake.abandoned_gate_discharge_of(control, attempt_id)   -> a discharge record
intake.abandonment_cleanup_of(control, attempt_id=…,
        retention_policy_digest=…)                        -> cleanup "retained"
```

`retained` is positive cleanup in the accepted vocabulary, alongside
`complete`; missing, failed or uncertain is not.

**`docker rm` remains the wrong act**, and now for a stated reason rather than
a principle: it would remove the runtime while the Authority still holds the
assignment unfenced, which is the boundary `abandon_attempt` exists to close.

## What this does not say

It does not diagnose WHY the agents faulted. The tracing of the executed
image's own diagnostic path is a separate, unstarted item, and this read says
nothing about it.

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

It takes `--grants` (a document of operator decisions) and `--evidence`.

**And the grants set is CLOSED and fully available from this instance.**
`GRANT_MEMBERS` names exactly 32 members and `read_grants` refuses any missing
or extra one, so there is no guesswork about the shape. Every member is
obtainable from artifacts the preserved instance already holds:

  * from the served `run/deployment.json`, per worker — `engine`, `storage`,
    `launch_home`, `control_store`, `authority_store`, `credential_home`,
    `credential_slots`, `credential_profile`, `image_digest`, `network`,
    `review_route`, `retention_disposition`, `adapter_name`, `adapter_digest`,
    `retention_policy_digest`, `policies`, `record_binding`,
    `assignment_contract`, `human_contract`, `role_instructions_digest`,
    `runtime_profile_digest`, `toolchain_digest`, `labels`;
  * from the attempt's own records, through the readers used above —
    `attempt_id`, `offer_id`, `work_ref`, `participant`, `generation`;
  * from the preparation — `source`, `task_path`;
  * and `incarnation` and `now`, which the operator chooses for the recovery
    process itself.

So **a runnable recovery command is composable**, and that is a finding rather
than a hope: it is the abandonment ROUTE FROM THE ORCHESTRATOR that is blocked,
not the operator's own surface. What remains is to compose one grants document
per attempt from those exact sources, show `read_grants` and `preflight` accept
it against this deployment, and print the two invocations with their readback.
That is the next act and it needs no product change.

**It is still not printed here**, because a grants document assembled but never
held against `read_grants` and `preflight` is an operand list, not a command —
and this dossier has already learned what printing an unchecked recipe costs.
