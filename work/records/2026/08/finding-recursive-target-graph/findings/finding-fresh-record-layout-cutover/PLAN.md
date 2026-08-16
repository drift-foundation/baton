# Plan

**Status — 2026-08-16:** active. W77, W74 and W71 are closed satisfying; the
final schema-14 tree is checkpointed at
`6c3519e678a9f01849c7569d0542e894ed052a3e`. Inventory and cutover may now
begin from that exact boundary.

1. Close W77, W74 and W71 through independent review, run `just test-v11`, and
   checkpoint the final schema-14 tree.
2. Inventory the exact durable dossiers, remaining open/parked Work, bindings
   and repository references that must survive. Refuse a guessed mass move.
3. Prepare the next schema/release with the already-parked persisted-state
   features selected for that authority.
4. Establish `work/records/YYYY/MM/...` and `work/open/...`; relocate durable
   current records only after targets and symlinks are explicitly verified.
5. Supersede the ephemeral-finding section in `AGENTS.md` with the permanent
   record/open-index policy at the same checkpoint.
6. Deploy the new immutable v11 executable, initialize a fresh coordination
   home, configure/activate it, and recreate only current Work with canonical
   bindings. Do not migrate the trial database.
7. Test JSON, CLI and TUI workflows in parallel with reliable v10 wakeups;
   retire the old v11 trial only after the fresh authority is accepted.

**Review status — 2026-08-16 10:27Z:** one runbook-only correction is required
before the W92 commit message is final: step 2 must use the pinned
`just deploy-v11 /home/sl/opt/baton/v11/<short-commit>` operator surface and
carry that exact immutable directory through later commands. See
`review-2026-08-16T10-27-05Z.md`.

**Signed off — 2026-08-16 10:28Z:** both runbook corrections are clean; see
`review-2026-08-16T10-28-57Z.md`. The reviewed W92+W108 tree is ready for
Slawomir's commit. Deployment, fresh-authority initialization, recreation,
parallel acceptance, and trial retirement remain held manual steps.
