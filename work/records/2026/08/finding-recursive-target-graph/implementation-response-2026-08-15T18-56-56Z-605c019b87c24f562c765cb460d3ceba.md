# R92–R94 corrected — evidence

In reply to review message `e64c3124863376aa4840ca4f120db2b1`
(review-2026-08-15T18-48-00Z.md, claim
`38597051bd231305acf90863e1f0808f`). All four reviewer regressions
were reproduced red exactly as observed, then corrected to green.

## R92 — resolve is grammar-bound and catalog-bound

`cli._dispatch` resolve now:

1. runs every non-empty locator suffix — root form AND dossier form —
   through the ONE shared contained relative-path grammar
   (`transitions._validate_ref_path`, the R89 grammar): absolute,
   backslash, control, edge-whitespace, and empty/`.`/`..` components
   refuse at the syntax boundary. `pushcoin:../outside` and
   `WORK:../outside` both refuse with the "contained" wording.
2. requires an independent root to be LIVE in the accepted authority
   (`roots` catalog, `removed=0`) before consulting the resolver:
   `ghost:docs/note.md` refuses "not a live configured root" even when
   roots.json maps `ghost`. The resolver maps accepted root ids; it
   never authorizes new logical roots. The dossier form still obtains
   root/path from the canonical binding projection and appends only
   the validated suffix.

## R93 — phase two is an O_NOFOLLOW dir-fd boundary

`bootstrap_project` phase 2 no longer treats EEXIST as success and no
longer opens files by path:

- a directory `mkdir` that raises EEXIST revalidates the ACTUAL entry
  through `_chain_fd`: component-by-component
  `os.open(..., O_RDONLY|O_DIRECTORY|O_NOFOLLOW, dir_fd=...)` from the
  resolved base — a symlink anywhere on the managed chain raises ELOOP
  and refuses ("changed while bootstrap ran ... symlink"), naming the
  partial created set;
- every template write goes through that same chain: the parent fd is
  chain-opened, the file is created with
  `O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW, dir_fd=parent`, and the EEXIST
  byte-compare re-opens with `O_RDONLY|O_NOFOLLOW, dir_fd=parent` —
  never through a path that could traverse a raced symlink.

The reviewer's raced-mkdir regression now refuses with the symlink
message and the outside directory stays empty.

## R94 — every phase-two failure reports the exact partial set

Both writers catch OSError at the operation boundary and translate:

- bootstrap: any mkdir/open/write failure raises a structured
  `WorkError` — "bootstrap failed at <target>: <cause>. Created so
  far: [...]" — including the file O_EXCL created whose byte write
  then failed (appended to the created set before refusing). The
  injected PermissionError on `work/` now reports `tmpl/` as created.
- init: a byte-write failure reports the partial target alongside its
  earlier companions — "init failed writing BATON-SETUP.md ...
  Created so far, including the partial BATON-SETUP.md:
  ['roots.json', 'BATON-SETUP.md']". Nothing is cleaned up
  automatically; recovery stays manual per the one-shot ruling.

## Public workflow forms

WF-14 extended with the R92 public forms (source+packaged): escape
suffixes in both locator forms refuse "contained"; a
mapped-but-unconfigured root refuses "not a live configured root".
R93/R94 fault injections are not CLI-drivable and live in the focused
suite.

## Break-sweeps for the new guards

Defect in → red → restore → green, no residue: suffix grammar dropped
(3 red: focused + WF-14 both modes); liveness gate dropped (3 red);
no-follow chain dropped with EEXIST-means-success (raced symlink
escape red); partial-report translation dropped (both R94 regressions
red as raw PermissionError/OSError).

## Gate

Focused `test_ws6_project.py`: 12 passed (8 + the 4 reviewer
regressions, under `-W error::ResourceWarning`). All 56 workflow runs
green source+packaged. `just test-v11`: 507 parallel + 3 serial
green. Dossier: PROGRESS.md Step 46. STOPPED for re-review.
Production deployment, mailbox migration, shutdown, and cutover
remain held for Slawomir's manual operation.
