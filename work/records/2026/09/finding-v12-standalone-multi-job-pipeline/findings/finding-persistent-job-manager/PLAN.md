# Plan

1. [pending revalidation] Choose one owner module/package for Job submission,
   persisted stage state and process startup; inventory the exact existing
   lifecycle calls it will compose.
2. [pending] Define versioned submission and status documents, including Job
   identities, source descriptors, stage-scoped dependencies, requested
   profiles, bounded test-change scope, and exceptional-policy boundaries.
3. [pending] Extend the manager store with only the scheduler-owned relations
   and atomic/idempotent operations needed to derive the next eligible act.
4. [pending] Implement the persistent loop by calling existing public manager
   and authority operations and reconciling their durable receipts on restart.
5. [pending] Add documented CLI/JSON submit and read-only status commands.
6. [pending] Prove idempotent resubmission, identity conflicts, restart at each
   stage boundary, dependency gating, and honest exceptional state.
7. [pending independent review] Review the immutable proposal before it enters
   the standalone pipeline integration sequence.

Do not absorb worker selection, workspace/source delivery, review policy, or
integration policy into this leaf.
