# Plan

1. [review-ahead complete 2026-09-04] Re-read W62098's latest review-cycle
   ruling, W71875's current Job Manager stage/episode contracts, W71917's
   unfinished provider contract, the assignment-private workspace cleanup
   boundary, and Authority's review receipt. Record the reviewed ownership,
   identities, transitions, refusals, and evidence below. This is contract and
   plan review only; no implementation bytes exist or are approved.
2. [implementation entry gate: W71917] Revalidate this review against
   W71917's ACCEPTED finding, plan, production code, tests, and newest review.
   Record the exact provider symbols reused. If workspace identity,
   mount/custody capabilities, cleanup ownership, quota/re-adoption, source
   attachment, or result layout materially differs from this record, stop and
   return the affected contract for targeted review before production edits.
3. [pending] Add a durable review-cycle owner above one-shot Job Manager stages
   and disposable Worker Manager attempts. Define an Authority-namespaced
   `development_line_id`, monotonic line revision, immutable checkpoint
   identity/digest, writable attachment generation, read-only review
   attachment generation, verdict identity, and exact accepted-checkpoint
   eligibility. Reuse W83781 authority identity helpers if present; do not
   overload stage, admission-episode, attempt, runtime, proposal, or receipt
   identities.
4. [pending] Implement the journalled state machine:
   sole-writer implementation -> writer revoke plus checkpoint freeze ->
   read-only independent review -> either exact-checkpoint acceptance,
   same-line correction from that checkpoint, or terminal rejection. Keep
   review outputs separately writable, keep every prior checkpoint resolvable,
   and never transfer a verdict to a later revision.
5. [pending] Compose provider-backed line/checkpoint custody with disposable
   assignment roots. Ordinary attempt cleanup must remove only attempt-owned
   roots and must not delete or retarget the development line or checkpoints.
   The generic manager must not clone, copy/restage candidate trees, run Git,
   mutate the canonical target, or infer custody from a pathname supplied by a
   caller.
6. [pending tests] Add focused positive, negative, replay, race, and recovery
   coverage under the authorized `v12/python/tests/` scope:
   ten correction rounds with fresh attempts and one line; no second source
   clone or candidate copy; concurrent writer refusal; read-only review with
   separately writable findings/logs; immutable/audit-resolvable old
   checkpoints; stale or operand-mismatched verdict refusal; Authority/Work
   identity isolation; exact-operation replay; crash recovery before and after
   freeze, writer revoke/grant, verdict, and correction reopen; attempt cleanup
   preserving the line; and integration refusing intermediate, rejected,
   unreviewed, or later-than-accepted checkpoints.
7. [pending verification] Run the provider's focused tests, new review-cycle
   tests, Authority and Job/Worker Manager contract suites, schema/contract
   regeneration checks if touched, the full v12 Python suite, and repository
   diff checks. Preserve any real-container or restart evidence required by
   the accepted W71917 contract.
8. [pending independent implementation review] Bind the exact proposal digest,
   base, changed production paths, and every changed test path. Review all test
   assertion/expected-behaviour edits under the granted scope and approve only
   the bytes actually presented.

Independent contract review proceeds ahead of the unfinished workspace
provider. Before leaving review, restore that provider as the implementation
gate and reroute the Work to implementation. The gate then releases
implementation automatically when its provider closes; no operator must watch
for it. Pool selection and integration-eligibility consumption remain
separately scheduled capabilities.
