# Plan: OCI reference worker and local runtime adapter

1. [blocked on Worker Manager child] Revalidate the landed runtime-neutral
   adapter and worker-session contracts.
2. [pending] Build the pinned worker image/entry point and constrained OCI
   lifecycle adapter with restart-reconcilable identity.
3. [pending] Implement read-only Git and directory input materialization,
   private workspace, declared output and assignment-scoped credential policy.
4. [pending] Implement cancel/inspect/collect/destroy, positive-absence and
   retention behavior with isolation and stale-generation regressions.
5. [pending] Run focused container/runtime tests, record implementer progress,
   and return for independent review.
