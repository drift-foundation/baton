# Progress

**State — 2026-08-21:** complete. The migration was accepted in review round
five, and the final destructive step is done and verified.

## The irreversible step, reported explicitly

`/home/sl/src/baton-v12-poc` is removed. 17 MB, irreversible, and authorized
by the recorded boundary in `FINDING.md`, the parent plan's item 0ai, and
review round five, which accepted the migration and named this as the
remaining step.

**Pre-flight, all non-destructive.**

- 426/426 selected files present under `v12/`; exactly the ten documented
  placement-adaptation files differ, matching the reviewer's own round-one
  verification. Nothing missing.
- What the removal destroyed, stated rather than left implicit: `.git/` (one
  scaffold commit, no remote, reviewed content never committed to it),
  `node_modules/` (reproducible from the pinned lockfile), and `run/` +
  `work/` (disposable authority, attempt state and Job records). All four are
  exactly the categories the finding excluded from migration.
- No credential material remained in the removed runtime directories.
- No live configuration, script, recipe or test referenced the external path;
  the surviving string occurrences are the package/owner identifier and
  assertions that the path is absent.

**Post-flight.** `npm test` from `v12/`: **78 passed**. The complete bounded
live proof from `v12/` alone: **`proof-r12-standalone`, exit 0**, with the
whole-checkout walk again clean. The v11 gate: **2807 passed** (non-serial)
and **52 passed** (serial). `git diff --check`: clean.

## What this Work delivered, end to end

The reviewed W76 prototype now lives in this repository as the self-contained
`v12/` subtree, and it is the only copy. Getting there took five review
rounds, and every one of them found something real:

1. every state-creating and state-deleting entry point now validates through
   one fail-closed placement authority before its first mutation;
2. externality is asserted against the whole Baton checkout, not one subtree;
3. destructive operands must be the exact configured plan, not merely some
   descendant of the state root;
4. removing the state root requires positive, durable ownership evidence — a
   self-naming marker — and never path shape alone;
5. that requirement holds whatever the root's current existence, and the
   regression proving it obtains absence by construction rather than by
   deleting.

None of it weakened the reviewed W76 boundaries: `assertNoBatonCapability` is
untouched and still refuses to mount any path inside the checkout into a
worker, and the assignment lifecycle is exactly as reviewed.

## Nothing outstanding from this Work

- No v11 source, test, recipe, packaging or deployment path changed.
- Nothing was staged or recorded in history; the working tree carries `v12/`
  and this dossier for Slawomir.
