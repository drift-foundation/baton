# Exact OCI runtime observation during reconciliation

Date: 2026-08-27
Parent discovery: W6636, `work/records/2026/08/finding-v12-local-oci-lifecycle-composition/`

## Finding

**Observed:** `reconcile_runtime` in `v12/python/src/baton_v12/worker_manager/attempts.py` currently treats any matching result from `docker ps --all` as a running worker and does not ask the adapter to observe the matched container's exact runtime state.

**Confirmed:** An exited, dead, or otherwise quiescent container can therefore be misclassified as running. W6636's approver authorized a separate correction Work for exact runtime observation.

**Confirmed boundary:** This Work owns the production observation seam: select by exact assignment identity, require unambiguous multiplicity, invoke `adapter.observe`, and expose running, quiescent, absent, or uncertain state to reconciliation. W6636 retains the broad restart/adoption matrix, shared settlement crossing, and orphan convergence policy.

**Proposed:** Fail closed on duplicate candidates, observation errors, identity mismatch, or unrecognized engine state. Do not infer running state from list membership.

## Acceptance

- Reconciliation lists by exact assignment identity and calls `adapter.observe` on the unique candidate.
- Running, quiescent/exited, absent, and uncertain states remain distinguishable through the manager seam.
- Duplicate containers, observation failures, and identity mismatches fail closed and never report running.
- Unit and real-engine regressions prove an exited container is not classified as running.
- The focused lifecycle diagnostic is converted to a positive production-seam proof.

## Open

- The exact public state type and division between adapter normalization and manager policy must be revalidated before implementation.
