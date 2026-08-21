# Plan

1. [done] Record the live forced-restart failure and trace it to the
   unconditional persisted-state refusal in `_start_guarded()`.
2. [done] Revalidate the narrow all-recorded-identities-stopped recovery rule;
   retain explicit refusal for every mixed, live, reused, mismatched, changed,
   malformed, or ambiguous state. The 2026-08-21 reviewer revalidation in
   `FINDING.md` pins the process-absence proof and configuration checks.
3. [parked] Confirm the proposed implementation boundary in
   `FINDING.md`, especially the definitive pidfd-backed absence proof and the
   refusal of changed, state-only, or structurally impossible records. The
   2026-08-21 ruling defers this until v12 lifecycle ownership is concrete or
   continued v11 use justifies a v11-specific correction.
4. [parked] Reuse one terminal cleanup operation from
   startup rollback, explicit `stop`, and dead-state recovery, including
   rendered-context cleanup, without broadening process ownership or calling
   termination from the recovery path.
5. [parked] Add focused reboot/disappearance, fresh-context,
   partial/empty-state, fail-closed inversion, and serialized retry tests from
   the matrix in `FINDING.md`.
6. [parked] Run the lifecycle suite and complete v11 gate, then independently
   review before deployment.
