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

## Replan under campaign item 20 — 2026-08-24

6. [done] Revalidate the canonical W5 binding, frozen worker-control,
   agent-session and conformance contracts, the landed Python manager boundary,
   the frozen Node evidence and the read-only local Docker baseline. Evidence:
   `evidence/w5-intake-revalidation-2026-08-24.txt`.
7. [done 2026-08-24; approved in M6617] Reconcile the campaign's singular-container
   phrase with the frozen consent/execution postures and physical mount timing.
   Recommend one posture-specific OCI container for consent and a distinct one
   for execution under the same runtime attempt; never pre-mount writable
   execution capability or promote the consent session.
8. [done 2026-08-24] Created the separately reviewed M2 manager follow-up
   Jobs for contract/public composition, agent sessions and adapter protocols,
   output/collection, intake/retention/cleanup, and §13 security. Record only
   real dependency edges; pure materializer/image work need not wait for every
   manager receiver.
   Jobs: W6592 contracts/public composition, W6627 agent/runtime protocols,
   W6628 output receiver, W6629 intake/retention/cleanup, and W6630 section 13
   security.
9. [done 2026-08-24] Created five bounded W5 child Jobs, each with a
   promoted top-level permanent dossier: materializer/workspace, OCI adapter
   core, reference worker image/entrypoint, sealed output/credential boundary,
   and local lifecycle composition. The final composition depends on the four
   component Jobs and the applicable manager prerequisites.
   W6631 materializer, W6632 adapter core, W6633 image, W6634 output/credentials
   and W6636 lifecycle composition. W6634 requires W6628/W6630; W6636 requires
   W6631/W6632/W6633/W6634 and W6592/W6627/W6628/W6629/W6630.
10. [in progress] Route only implementation-ready children to `baton.impl`; W5
    remains the roll-up. Each child receives its own tests, evidence and
    append-only independent review. Do not create `PROGRESS.md` here.
11. [pending] Close W5 only after all contained implementation Jobs close
    satisfying. W6 then owns the independent complete 109-case `local-oci`
    conformance assessment; counts from W5 component tests do not certify it.
12. [done 2026-08-24; decomposition review] W5 is blocked on all five children.
    W6631, W6632 and W6633 are independently implementation-ready. Because
    dependency mutation follows Route authority, `baton.impl` must install the
    recorded manager edges on W6627-W6630, W6634 and W6636 before executing
    those Jobs. Exact messages and the full DAG are recorded in
    `evidence/w5-decomposition-2026-08-24.txt` and
    `review-2026-08-24T22-43-25Z.md`.
13. [queued high priority 2026-08-26] Before the broad W6636 integration
    matrix, run one deterministic real-Docker ping-pong proof through the
    reviewed Python manager and OCI worker boundaries. The promoted top-level
    record is
    `work/records/2026/08/finding-v12-docker-ping-pong-smoke/`; it waits only
    on W6633 and W6634, and W6636 consumes its satisfying result.
13a. [supersedes item 13's prerequisite clause 2026-08-26] Run W17110 now as a
     disposable tracer-bullet using a spike-only image and minimal Python glue.
     It no longer waits on W6633 or W6634. Preserve W17110 as a prerequisite of
     W6636, label all temporary implementation honestly, and let the production
     component Jobs decide what—if anything—to reuse after the Docker concept
     has been demonstrated.
13b. [supersedes item 13's deterministic-worker scope 2026-08-26] W17110 tests
     real agents in order: Claude first, then Codex. Each runs inside its own
     spike container, receives a correlated ping through the smallest practical
     wrapper, returns pong, and leaves redacted packaging/auth/start/result/
     cleanup evidence. Both must succeed for the two-provider proof; neither
     spike implementation is production conformance.
