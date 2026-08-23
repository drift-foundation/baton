# Plan: freeze the v12 worker contract

1. [done 2026-08-21] Revalidate the assignment against the parent roadmap,
   accepted assignment-state specification, current `v12/` proof, and ACP/App
   Server boundary evidence.
2. [done 2026-08-21, child W1439 closed satisfying] Pin the versioned
   worker-control API and typed input/output, capability, proposal, receipt,
   inspection and collection manifests in
   `findings/finding-worker-control-api-manifests/`.
3. [done 2026-08-21, child W1440 closed satisfying after four review rounds]
   Pin the normalized ACP relay/adapter boundary, including the Codex App
   Server mapping, in `findings/finding-acp-agent-boundary/`. The boundary is
   specified in that record's `SPEC.md`,
   `schema/agent-session-1.0.schema.json` and `evidence/`, including the
   captured Codex App Server approval-response schemas.
4. [done 2026-08-22, child W1441 closed satisfying after four review rounds] Pin the
   runtime-neutral black-box conformance contract and test-vector boundary in
   `findings/finding-worker-runtime-conformance/`. Both dependencies closed
   satisfying, so the ordering is met; the contract is specified in that
   record's `SPEC.md`, `schema/conformance-1.0.schema.json` and `evidence/`,
   with a 68-obligation, 107-case register whose coverage of the two frozen
   contracts is machine-checked rather than claimed.
5. [done 2026-08-21] Create the three bounded child Work with atomic canonical
   bindings and dependency edges matching items 2-4. W1439 is the one runnable
   slice; W1440 and W1441 are blocked on their recorded prerequisites.
5a. [done 2026-08-21] Approver accepted the decomposition and ruled that W1408
   waits explicitly on W1441 while W28 waits explicitly on W1408. These are
   scheduler dependencies for the approved milestone ordering, not consequences
   of containment.
6. [done 2026-08-22] Reconcile the three approved specifications into one M1
   freeze, independently review cross-contract consistency in
   `review-2026-08-22T04-41-06Z.md`, and hand the design gate to the approving
   endpoint before any implementation.
