# WS-6 Slice B complete: the filesystem domain — evidence

In reply to the acceptance/release message `ecb0056258c06bd422e1b28db9afb15b`
(claim `e509ede0fbb3d73f463307620b64a445`). Correction: message id is
`ecb0056258c06bd422e1b28db9abf15b`.

## What was built (per M1–M6 + Amendments 1–7)

**Three location domains, none inferred from another.**

1. **`init DIR`** (`project.scaffold_home`) — the one-shot scaffold:
   valid strict-JSON `baton.json` (generation 1, fresh
   `authority_uuid`, empty teams/roots), an empty-`roots` `roots.json`,
   and `BATON-SETUP.md` instructions. No database. If ANY managed
   target (`baton.json`, `roots.json`, `BATON-SETUP.md`,
   `work.sqlite3`) exists, it refuses whole, naming the blockers and
   demanding manual inspection — init never adopts, resumes,
   overwrites, or deletes (the superseding R88 ruling).
2. **`activate DIR --participant`** — the renamed old `init`: the ONE
   authoritative validation and creation. A pristine or half-edited
   document refuses with the real semantic message and leaves no
   database; success is WS-5 protected (`--op-id` replays exactly).
   There is no `check` command (Amendment 5): activation IS the
   validation surface.
3. **`resolve LOCATOR --roots-file`** — read-only: work-form pins the
   effective binding through the canonical projection; root-form maps
   directly. The resolver (`{"roots": {id: "/absolute"}}`,
   `validate_root_id`, absolute paths only) is EXPLICIT input — never
   searched for, never persisted, never fingerprinted.
4. **`bootstrap --root --roots-file [--template]`** — two-phase vendor
   of this release's numbered templates (`tmpl/work-basic-1.md`,
   edition 1) plus `work/open` + `work/records` into one resolved
   project root. Phase 1 validates containment (realpath +
   symlink-walk) and byte-compares every existing target; phase 2
   creates with O_EXCL. Identical → already-present (inode/mtime
   proof); conflicting bytes, wrong types, symlinks, escapes → refusal
   without replacement. Nothing is deleted, overwritten, or written
   back to the distribution. Templates are sibling release assets
   beside `bin/` (M6) — build_release.py SNAPSHOT and deploy.py carry
   `tmpl/work-basic-1.md`; the zipapp embeds nothing.
5. Filesystem verbs refuse `--op-id` and `--ref`: they live outside
   the authority — no operation identity, no references, no events.

## Evidence

- **Focused** `tests/work/test_ws6_project.py` — 8 passed: scaffold
  validity + pristine-activate refusal leaving nothing; one-shot
  blockers by name; scaffold→edit→activate with exact op-id replay;
  strict/absolute resolver; vendor + inode-proof idempotence;
  conflict/type/symlink/escape refusals with the distribution
  untouched; unknown template/root; filesystem-operations-never-touch-
  authority (database sha256 unchanged, no resolver byte in the file).
- **WF-14** (`test_wf14.py`, source+packaged): packaged mode drives a
  TEMPORARY release layout (`bin/<archive>` + sibling `tmpl/` copied
  from the source tree). Byte parity with the distribution in both
  modes; relocation by editing `roots.json` alone (checkout moved on
  disk; every portable locator re-resolves; database hash unchanged
  across the whole filesystem story; no machine path in the file);
  adversarial matrix (unmapped root, missing base, traversal, unknown
  template, wrong type, symlink never followed, local template
  specialization never silently upgraded); the identity/reference
  guards; distribution immutability including the
  archive-without-sibling-tmpl refusal.
- **WF-15** (`test_wf15.py`, source+packaged): empty directory →
  `init` → one-shot re-run refusal → pristine activation refuses
  "teams must not be empty" leaving no database → half-edited strict
  refusal names the stray field, still nothing → protected activation
  succeeds and replays exactly → two members create/say/thread/home →
  a RACED activation of a second fresh home admits exactly one winner
  → partial-directory refusals by name.
- **Break-sweeps** (defect in → red → restore → green): silent
  overwrite/upgrade (4 red), symlink checks dropped (3 red), resolve
  writing into the authority (hash checkpoint red both modes),
  distribution write-back (4 red), one-shot init dropped via O_TRUNC
  adoption (3 red), filesystem identity/ref guard dropped (2 red).
- **Gate**: 503 parallel + 3 serial pass; all 56 workflow runs green
  source+packaged; `just test-v11` green. The 43 warnings are
  pre-existing fork/forkpty DeprecationWarnings from the PTY and
  multiprocessing tests under Python 3.13 xdist, not Slice B.

Dossier: PROGRESS.md Step 45. STOPPED at the review gate. Live
production deploy/migration/shutdown/cutover remain held for
Slawomir's manual operation.
