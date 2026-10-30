# Progress

## claim370562 — read-only diagnosis of the review fault

Diagnostic only, from parent W370268/E370543. No live run, no fresh attempt,
no second Job, no product or deployment edit, no deletion, no supervisor stop,
no direct store read, no provider invocation.

### The exact cause, and it is a declaration defect in my own preparation

`claude_agent._review` opens with `_selected(declared, REVIEW_OUTPUTS,
'review')`. `REVIEW_OUTPUTS` is `("findings", "logs")`. The review
assignment's declared outputs — read from the attempt's own retained
`/input/input.json` — are **exactly one**:

    {"name": "proposal", "type": "git-change-proposal", "required": true}

So `_selected` raises `TaskRefusal`: *"a review turn writes findings, logs and
this assignment declares no findings, logs"*. Even with those declared it
would refuse the next check, because `proposal` is marked `required` and a
review turn does not write it.

`TaskRefusal` is **not** a `WorkerFault` — its own docstring says it is
"raised rather than answered, because `baton_worker` turns an agent exception
into a bounded correlated fault frame with no traceback". So it lands in
`baton_worker`'s generic `except Exception`, which writes
`_faulted(…, "agent")` and, by explicit design, keeps "even the exception's
type name out of the durable document". That is precisely the terminal
observed: `ending faulted`, `fault_code agent`, nothing else.

**Why the implementation lane succeeded on the same manifest.** Its turn
selects `IMPLEMENTATION_OUTPUTS = ("proposal",)`: nothing missing, nothing
absent. The single-output declaration is exactly right for that lane and
exactly wrong for the other. The asymmetry is fully explained.

**Where the declaration came from, and it is mine.**
`capacity.sealed_manifest` takes `outputs` from the reviewed pilot manifest,
which declares only `[proposal]` because the pilot ran **one** implementation
worker and no review turn — `tools/next_run_bindings.py` says so in its own
comment. Correct for the pilot; wrong for a two-stage template Job.

**The product ships the correct reference.**
`tests/manager/test_claude_agent.py:2976`, `SHARED_DECLARED`: *"the union both
stages are launched under, because every stage of one Job matches that Job's
ONE input digest"* — `proposal`, `findings`, `logs`, each `required: False`.

### Absence of logs versus proof of no model run — labelled

**Proved:** the log driver is `json-file` and the image sets
`PYTHONUNBUFFERED`, so both streams were captured and unbuffered; `docker
logs` on the retained container returns **zero bytes** on each; the container
lived **2.102 s** (01:43:30.175 → 01:43:32.277), exit 1, not OOM-killed,
`State.Error` empty; the supported logs view reports the native room *empty*;
and the refusal is sited at the **first statement** of `_review`, before any
prompt is composed and before `_provider` is called.

**Inferred, not proved:** that no model was invoked. The inference is strong,
but no retained artifact records a call that did not happen.

**Not recoverable at all:** the refusal *message*. The product discards it at
two layers — the worker keeps the exception type out of the durable document,
and the manager's projection carries only a safe category/code. So the cause
above rests on reading the code against the retained declaration, not on
reading a recorded message. **That is the missing diagnostic capability**, and
it is worth fixing on its own: a correct refusal with no recoverable reason
cost this run a full diagnostic cycle.

### Runtime and cleanup, as read at 02:03:37Z

    implementation  completed    runtime destroyed   container REMOVED from the engine
    review          exceptional  runtime quiescent   container RETAINED, exited 1

Cessation is **established** for both lanes. Cleanup is **not settled** for
the review lane: reclamation is asymmetric, the diagnostic's cleanup axis is
unknown, and the manager log carries no reconcile record after 01:25:59Z. The
supervisors (169781, 169782) are therefore still running.

### The conclusion that decides the settlement

**This Job can never produce a verdict on this installation, so retry is not
an option.** The declaration is sealed into the installed manifest, both
stages must carry the same `outputs` because they match one input digest, and
a fresh attempt would relaunch the review under the identical declaration and
refuse identically. Selecting a retry would spend a provider turn to reproduce
a known refusal.

`evidence/claim-370562/SETTLEMENT.json` lays out five options with what each
needs: **A** read the candidate (available now, nothing required); **B** retry
(not available, do not select); **C** close honestly — `satisfying` would
refuse for want of an accepted review, so `non-satisfying` or `cancelled`,
and it is Slawomir's act; **D** recover the capability — correct the
composition, prove it deterministically for both roles, then one new install
at a fresh path and one new Job; **E** cleanup and supervisors.

### Verification and cumulative spending

This claim, all read-only: one container log read, one full container inspect
(env reported by key name only, no value), one image-field confirmation, one
inspect of the already-removed implementation container (confirming removal),
reads of both workers' exchange documents and the review attempt's retained
`/input`, reads of the review line checkout and the sealed candidate, five
product source reads, and four status/diagnostic reads. No container started
or removed, no live file written, no store opened directly, no product or
deployment edit, no retry, no second Job, no supervisor stop, no provider
invocation, no deletion, no owner act.

### Boundaries

Parent evidence, the accepted packet, the child records and all product files
were read-only. The candidate and the missing verdict are preserved exactly as
the run left them. No credential material was printed — the container's
environment is reported by key name only. `v12` is byte-clean and the source
checkout is unchanged.

**Not established:** the refusal message (discarded by design); whether the
image's worker code matches the checkout byte-for-byte, since no container was
started and nothing was copied out of the image; why reclamation did not run
for the review runtime.
