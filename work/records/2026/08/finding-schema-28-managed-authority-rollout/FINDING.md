# Roll out the schema-28 managed authority

## Observed — 2026-08-22

The current working tree contains one interdependent release batch: schema-28
dispatch control, exact orphan-claim recovery, managed Docker inspection,
dependency-graph presentation, and the current v12 proof. The deployed
`c529b28` authority is schema 27 / projection 12.3 and cannot accept the new
`recover` or `dispatch` contract. W4303 and W4615 therefore cannot complete
their live acceptance against the currently deployed executable.

W6175 is the one rollout gate. It waits on W2845 and W4996 so an immutable
release is never built from a moving or operator-unaccepted tree. W4303 and
W4615 wait on W6175 so their approval rows name the actual remaining act
rather than appearing independently overdue.

## Confirmed rollout boundary — 2026-08-22

1. **Freeze only after both prerequisites finish.** W2845 must pass its
   corrected credential-bearing exact-policy matrix and close. W4996 must
   finish console wiring, independent review, and close. No Handler may remain
   active when the release gate starts.
2. **Prove the complete source before committing.** Run `just test-v11` (xdist
   uses every available CPU), the complete Codex event-bridge suite, the v12
   suite, and `git diff --check`. Audit every untracked path against an owning
   Work; do not stage by assumption. Slawomir alone stages and commits.
3. **Publish one immutable artifact from the committed tree.** Deploy to
   `/home/sl/opt/baton/v11/<commit>` and never overwrite a prior distribution.
   Record the archive digest and exact executable.
4. **Create a fresh authority.** Schema 27 is never upgraded in place. Initialize
   `/home/sl/baton-v11.<commit>` with the new executable. Before activation,
   preserve the accepted Baton team, roots, role instructions and launchers,
   grant `baton.slaw` exactly `config`, `recover`, and `dispatch`, and use
   lifecycle manifest version 2 with its explicit Baton binary/config/
   participant control triple. Activate generation 1 only after those inputs
   are exact.
5. **Install only a proved execution policy.** Generate every managed-workflow
   participant profile plus the one deployment-wide
   `managed-docker-inspection` profile into a staged file. Audit it as the
   exact generated set and run W2845's corrected live matrix against the
   immutable candidate. Install it only after every positive and negative
   case passes and temporary credential cleanup is confirmed.
6. **Recreate only surviving Work.** The terminal v11 correction and rollout
   Works stay as history in the old authority. Recreate the still-open W28
   v12 campaign subtree in the new authority with deterministic operation IDs,
   canonical dossier bindings, containment and dependency edges. Trial/chat
   history is intentionally not migrated. Verify the reconstructed tree
   before it becomes canonical.
7. **Cut over recoverably.** Keep the old stack running while the artifact,
   new home, configuration, policy, and reconstructed ledger are prepared.
   Once the old authority has no active Handler, stop its managed stack,
   repoint `/home/sl/baton-v11` to the new home, and start the new stack. If
   startup or health verification fails, repoint to the untouched old home
   and restart it. Never delete either home during rollout.
8. **Run live acceptance before declaring success.** Verify all services
   healthy; perform an exact `recover` release using the new assignment
   episode; exercise `running -> draining -> paused -> running`, refusal of a
   post-boundary claim, and `stop-drained` refusal/success in the corresponding
   states; inspect W4996's `[b] deps` against a recreated two-blocker v12 Work;
   and confirm prompt, reviewer, tuner, Claude and Gemini runtime paths.
9. **Close the old acceptance gates authoritatively.** After the new deployment
   passes, close W6175 satisfying in the old authority, then close W4303 and
   W4615 with their exact live evidence. Preserve the retired authority as
   immutable history. The new authority carries only unfinished Work.

## Rollback boundary

The cutover changes one symlink only after the new authority is prepared. A
failed preflight never stops the old stack. A failed post-cutover start rolls
back the symlink and restarts the old stack; it never edits, deletes, or
reinitializes the old home. New-schema state is never copied into the old
database, and the old database is never opened by the new executable as a
migration shortcut.

## Acceptance

- W2845 and W4996 are terminal and independently accepted before freeze.
- All four source gates pass on the exact committed tree.
- The immutable artifact and fresh authority identify the same commit.
- The new accepted configuration grants only the ruled capabilities and the
  lifecycle manifest is version 2.
- Exact policy matrix, runtime health, recovery, drain, restart, TUI graph,
  and reconstructed-ledger checks pass.
- W6175, W4303 and W4615 close with evidence; the old home remains recoverable.
