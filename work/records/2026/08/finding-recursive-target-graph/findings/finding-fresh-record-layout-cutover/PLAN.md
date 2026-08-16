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

**Deployment hold — 2026-08-16:** Slawomir stopped before deploying commit
`6fe32fd`. The open-Work audit has already found W2
(`findings/finding-v11-executable-name/`), W4
(`findings/finding-configured-project-root-paths/`), W6
(`findings/finding-tui-classification-label/`), W9
(`findings/finding-tui-exit-confirmation/`), W12
(`findings/finding-tui-work-id-discovery/`), W13
(`findings/finding-key-value-command-grammar/`), and W84
(`findings/finding-tui-recent-work-cue/`) incorrectly placed in the
post-deploy recreation set. The next distribution must install `bin/baton`,
the fresh authority's accepted `baton.json` must already contain each
repository's explicit base, confirmed defects must render as `defct`,
normal-navigation `q` must use the ruled exit confirmation, a selected Work's
canonical id must be visible in its detail view, and v11 operations must use
the one strict `key=value` grammar. The superseded W84 timestamp design is now
the same-schema active/review hot-zone cue and is no longer parked. These all
require no fresh authority. Continue auditing every open Work before fixing
the final sequence. Do not deploy, initialize the fresh authority, or run
recreation until all pre-cutover items review clean, leave the recreation set,
and the corrected tree is committed.

**Cutover correction — 2026-08-16 13:57Z:** the fresh authority is activated
and all five creates are committed, but the parked transition was refused
because the script attempted it as `baton.claude` instead of the configured
`baton.feat` review handler `baton.codex`. Correct the script's phase actor,
pin it with a regression, then rerun the effectively-once script to finish the
outstanding transition. Verify exactly five rows, four open and one parked.

**Recreation complete — 2026-08-16:** the corrected rerun replayed all five
stable create operations and committed the one outstanding parked transition
at authority sequence 7. Fresh-authority recreation is complete. Parallel
participant/TUI acceptance remains before retiring the prior trial home.
