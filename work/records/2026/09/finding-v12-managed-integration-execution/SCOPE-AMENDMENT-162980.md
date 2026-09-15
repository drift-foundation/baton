# Proposed source-scope amendment — queue custody vocabulary

2026-09-13T19:07:44Z, baton.codex, claim162980. Owner decision requested;
this packet does not grant authority or approve candidate bytes.

The implementer reports M162973, and independent review confirms, that a valid
result.managed journal act makes queue history refuse the coordinator. Both
lease_of and entries_of require that history. The operational finding and its
reproduction are pinned in FINDING.md and review-2026-09-13T19-07-44Z.md.

The exact approved slice1 source table in SLICE1-SCOPE-161491.md omits queue.py
and says: "No other source paths" and "If an additional boundary is necessary,
return the exact missing scope before editing it." M162289 supersedes test-only
restrictions, not this product-source boundary. This is why the amendment goes
to the owner through Baton; no interactive permission or test amendment is needed.

## Exact additional source change

Authorize baton.impl to add only result.managed to RESULT_CUSTODY_KINDS in
`v12/python/src/baton_v12/integration/queue.py`. Current base SHA256:
18ced502ebcff18946c1c72914223166c995484ce2baccd6423bb3f7ca0b23a0,
117048 bytes. Revalidate the base and coordinate ownership before editing.

```diff
 RESULT_CUSTODY_KINDS = ("result.prepare", "result.prepared", "result.observed",
-                        "result.publish", "result.evidence", "result.imported")
+                        "result.publish", "result.evidence", "result.imported", "result.managed")
```

No other queue.py changes, new product path, generic journal relaxation or
protocol change. Existing six kinds keep their behavior. Unknown kinds still
refuse. Queue continues to own journal positioning and delegate result operand
ownership; it must not become a second result validator.

## Required companion work and verification

The proposed addition is necessary but is not independently sufficient. The
current managed reader does not rederive its journal signature, contrary to the
implementer's explanation of the delegation. Complete the new review's task,
phase-set, source and state journal-binding corrections in already approved
reconciliation.py before presenting a complete candidate. Mere well-formed JSON
cannot stand in for the operation that produced it. Preserve the existing
target/rank/lease/fence ownership and the managed result's actual parent/content.

The existing test authority covers replacing the two queue-defect observations
in tests/integration/test_managed_storage.py with positive lease/entry/history
checks after recording a managed result; add exact replay, unknown-kind refusal
and malformed managed-journal/result refusal coverage. Correct the historical
preservation fixture to start with a genuine populated schema5 record/history.
Keep populated live lease checks through public readers after upgrade. Update
the already approved DEPLOYMENT.md limitation when the integrated fix is verified.
No broader suite or live execution is required merely for this amendment.

Keep M161614 cumulative bounds: author117.08701624104287/600s,
remaining482.9129837589571s; reviewer4.947672767979384/300s,
remaining295.0523272320206s. No reset, transfer or additional allowance. Persist
guards before children and charge failures. Qualified4.19.2 evidence does not
waive pinned4.26.0 final verification. W32577 shared-file ownership stays intact.

Approve this exact source addition, or specify the adjustment. On approval,
baton.feat pins the decision and hands the amended slice back to baton.impl for
all remaining corrections and placement/task/content/grant scope, then independent
candidate review. No slice acceptance or release of dependent Work follows.
