# Plan

1. Revalidate failed-start reconciliation, worker-disposition provenance,
   authority ending, output custody, intake/retention and cleanup contracts.
2. Pin the manager-owned failed-start record and the no-envelope custody rule;
   keep it distinct from every worker disposition.
3. Implement the bounded composition through existing exact reconciliation,
   authority, custody, adapter and provider owners.
4. Add real post-create fault plus restart, retry, mismatch, multiplicity,
   uncertainty, custody-failure and sibling-preservation regressions.
5. Run focused daemon-free and required Docker gates, then return for
   independent review before W32382 can close.

## 2026-08-28 — reviewer gate

- [done] Revalidated that current intake quarantine is frozen-result custody,
  not a no-envelope path.
- [done] Approver M33800 selected the existing unique per-generation,
  per-attempt result directory as the untrusted custody boundary and rejected
  a second copied quarantine result.
- [done] Pinned the ruled identity, trust, custody, retention, cleanup, and
  proposal-exclusion semantics in `FINDING.md` before production edits.
- [required] Complete plan items 3–5; PLAN 1–2 research alone does not satisfy
  W32648.

## 2026-08-28 — PLAN 3, first unit

3a. [done] The manager-owned failed-start record: `runtime.start-failed`,
    journalled as its own act because the start operation has already
    committed by the time the failure happens. The journal is the record;
    identity is the attempt, the fixed assignment, the start operation, the
    attached runtime and the typed failure, so an exact retry replays and any
    changed fact collides. A refusal keeps its closed pair; a fault is
    preserved as a fault, because the pairing has no `refused/start-failed`.
3b. [next] The ruled cleanup crossing: authorized by that record rather than by
    an intake receipt, fencing before destruction, exact removal, positive
    absence, delivery-root settlement, `cleanup = retained`, and the result
    directory left in place for later explicit retention cleanup.
4.  [next] The real Docker post-create fault and the restart, mismatch,
    multiplicity, uncertainty, custody-failure and sibling matrix.

## 2026-08-28 — independent review changes requested

3a. [required correction] Give the one start act one stable failed-start
    operation identity. Keep runtime, settled axis and typed failure in the
    signed operands/result so changed facts collide instead of selecting a
    second operation row. Replace the submitted two-record expectation with
    collision plus first-record-preservation coverage.
3b. [still required] Implement the ruled cleanup crossing only after 3a is
    corrected: authorize from the exact durable record, fence before destroy,
    remove the exact attached runtime, positively observe absence, settle
    delivery roots, retain the untrusted result directory, and finish at
    `cleanup = retained` without worker disposition or proposal admission.
4.  [still required] Cover restart at every boundary, exact retry, changed
    failure/runtime/assignment collision, multiplicity, uncertainty, cleanup
    failure, and sibling preservation; include the real Docker create-then-
    fault path with no fabricated envelope or output.
5.  [verification] Repeat the focused attempts/dependency gates, engine-owned
    suites and required real-Docker gate, then the package gate with existing
    unrelated failures attributed exactly.

## 2026-08-28 — W34998 provider dependency

3b. [blocked on W34998] Consume, but do not redefine, the sibling no-envelope
    failed-start destroy command and adapter capability. Resume this composition
    only after W34998 closes satisfying; the ledger carries that dependency.

## 2026-08-29 — 3a revalidated, 3b implemented

3a. [done, revalidated] The stable failed-start identity and its collision
    case are in the tree; the prose that still described the superseded
    identity is corrected.
3b. [done] `authorize_failed_start_cleanup`, `failed_start_destroy_operation`,
    `_failed_start_record`, `_destroyed_failed_start` and
    `_settle_failed_start_cleanup`, consuming W34998's command and capability
    and reusing the observation, provider-ending and axis owners rather than
    repeating them.
4.  [done] Ruled ending, record-authorization, fence-before-destroy,
    uncertainty, surviving runtime, unresolved provider, exact retry, changed
    policy, restart, retained result directory and sibling preservation.
5.  [done] Focused, package and every serial engine-owning suite.

## 2026-08-29 — independent review changes requested

3b. [required correction] Bind the committed `runtime.start-failed` journal
    result back to the exact current attempt and runtime before invoking
    `destroy_failed_start`. Verify the journal kind and the result's fixed
    assignment, start operation, runtime identity and settled execution state;
    mismatch must refuse as durable integrity failure with no adapter call.
4.  [required correction] Replace the real Docker post-create-fault case's
    fabricated disposition/freeze/intake path with the manager-owned
    `authorize_failed_start_cleanup` crossing. Prove no worker evidence is
    invented, the exact container and delivery roots are gone, and the result
    directory remains retained untrusted.
5.  [verification] Make the additive exact-runtime-binding regression pass,
    run the focused manager suite, the real Docker composition case and the
    serial engine registry, then report the package gate with unrelated
    worktree failures attributed exactly.

## 2026-08-29 — independent re-review complete

3b. [done] The committed failed-start record is verified as the exact
    attempt/start/runtime authorization before destroy; changed runtime and
    wrong journal kind refuse before the adapter.
4.  [done] The real Docker post-create-fault case uses the no-envelope cleanup
    crossing directly and proves no worker evidence or intake is fabricated.
5.  [done] Independent daemon-free attempts/dependency gates and scoped diff
    check pass. Retained serial evidence records the required Docker case
    green; reviewer daemon access remains unavailable and is reported rather
    than represented as an independent run.
