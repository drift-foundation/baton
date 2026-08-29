# Plan

1. [done 2026-08-28] Revalidated. The non-equivalence is measured on the tree
   and pinned in `PROGRESS.md`: interrogation's `timed-out` is an observation,
   deliberately non-terminal, and `deadline_at` exists nowhere else in
   `worker_manager`.
2. [PARKED 2026-08-28, seq 32814] Obtain and record the runtime deadline's
   authority meaning, owner, clock, policy generation, durable identity and
   ending. Blocked on approver obligation M32585, which is pending on parent
   W32382; a Work waits only on its own outstanding request, so this Work is
   parked rather than gated. Unpark when the ruling is pinned in `FINDING.md`.
3. Implement the smallest manager/authority composition seam without changing
   interrogation timeout or worker-disposition meanings.
4. Add positive, negative, restart, retry, race, stale-generation,
   policy-change, uncertainty and sibling-preservation tests.
5. Run focused daemon-free and required Docker gates, then return for
   independent review before parent W32382 can close.
