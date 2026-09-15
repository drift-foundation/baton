# Proposed deployment addition — awaiting DEPLOYMENT.md handback

Draft for `v12/python/DEPLOYMENT.md`; that file remains owned by W161230.
Candidate API, not an enabled deployment default or a background scheduler.

The trusted manager may select a deadline when it starts an activated runtime:

```python
request_runtime_start(store, adapter, attempt_id=attempt_id, inputs=inputs,
    deadline_policy={
        "policy_digest": recorded_attempt_policy_digest,
        "policy_generation": 1,
        "duration_seconds": 900,
        "action": "cancel",
    })
```

The duration is a positive whole number of seconds; the policy generation is a
positive integer. The digest must match the attempt's recorded policy. The
manager pins the selection, fixed assignment and its own start/deadline instants
before the adapter starts. Retries must preserve the selected policy, including
an explicit selection of `None`. A new unconfigured start pins no deadline.
A committed legacy start with no pin stays unconfigured and cannot acquire a
deadline retroactively. Restart never extends the original deadline.

`deadline_of(store, attempt_id=...)` reads the pin. The orchestration caller
decides when to invoke `observe_deadline(store, authority_port, attempt_id=...)`:
it returns `None` before expiry and commits the first reached observation at or
after expiry. The operation accepts no caller timestamp. Reaching a deadline
does not itself cancel a worker or change an execution/output axis.

`advance_deadline(store, authority_port, agent, adapter, attempt_id=...,
retention_policy_digest=...)` applies the persisted policy. `report-only` returns
the observation without destructive actions. `cancel` commits the existing
cancellation intent and obtains the Authority fence before stopping/removing the
exact runtime. The supplied adapter needs stop, deadline destruction and directory
custody capabilities. The Authority port must support gate discharge in the
deployment; a callable wrapper alone does not establish the optional underlying
session operation is installed.

A genuine intake receipt continues through ordinary retention cleanup. A
receiptless deadline ending preserves the untrusted output directory and records
retained custody without inventing a worker disposition, intake receipt or
abandonment. Output arriving concurrently holds cleanup for its actual owner.
Unknown engine/start/provider facts remain retryable and hold capacity. An
attempt that truly never started uses the existing six-fact no-start proof; it
does not fabricate runtime absence or a gate discharge.

`deadline_cleanup_of(store, attempt_id=..., retention_policy_digest=...)` validates
committed deadline cleanup evidence. Local cleanup and the Authority gate have
separate durable identities. `discharge_deadline_quiescence_gate(store,
authority_port, attempt_id=..., retention_policy_digest=...)` carries the exact
proof to its gate; an interrupted remote receipt can be retried without another
removal. This seam does not change per-Job provider-turn or verification-command
limits, nor does it change interrogation timeout semantics.
