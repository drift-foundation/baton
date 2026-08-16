# Plan

**Status:** queued after W77, W74 and W71; do not begin the cutover while the
schema-14 batch is active.

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
