# B5 first batch: the four InitialStableLineAccess long-root failures (M385052)

K, copilot under owner claim E384905, no claim held. Review: `review-2026-11-18T01-45-36Z.md`.
Prior evidence: `evidence/review-owner-selections-20261117/regression.log` (four failures under a
long fixture root), `regression-short.log` (the same source passing under a short root).

## Diagnosis

`workspaces._access_failure` renders the failing path through `contracts.errors.name_value`, the
sixty-code-point rule for a REJECTED VALUE; `prove_line_integrity`'s `inside` sentence renders the
line root the same way. The four tests assert the WHOLE root (`assertIn(str(self.line), said)`),
and the W194457 owner decision of 2026-09-17 that they witness is "report actual access failures
directly with actionable operation/path/error context". Under a fixture root longer than about
forty characters the root was cut to a prefix an operator cannot `ls`, so the assertions were
right and the rendering was wrong: the contract conflict is between a path-sized rule the
diagnostic needs and a value-sized rule it borrowed. Reproduced before any edit under a
142-character disk-backed root: 4 failures (`before-long-root.log`).

## Correction

- `contracts/errors.py`: `_PATH_LIMIT = 1024` and `path_value(value)` -- the same inert `ascii()`
  rendering as `name_value`, bounded at the path limit (`_rendered(value, _PATH_LIMIT)`: the input
  is cut first and the escaped form is cut again, so astral code points cannot inflate it); a
  non-`str` is named as a rejected value. Exported in `errors.__all__` (the `contracts` package
  `__all__`, which the contracts inventory derives its universe from, is unchanged). Two whole
  paths plus the longest access prose stay under `MESSAGE_LIMIT` (4096).
- `worker_manager/workspaces.py`: `_access_failure` and `inside` render through `path_value`.
  The entry stays in the rendered slot and the root in the sentence after it, as the `named`
  docstring explains; both are now whole up to the path rule's bound. No other site changed: the
  other ninety-odd `name_value(path)` renderings in the package are outside this bounded slice and
  are noted below as observed, not corrected.
- Not done: no shorter test root, no weakened assertion. The four original tests are unchanged
  except a dated docstring note in `test_an_unreadable_entry_NAMES_the_operation_and_the_entry`.

## Witnesses added (test_workspaces.py)

- `InitialStableLineAccess.test_a_long_line_root_is_named_in_full_by_every_access_refusal`: a line
  root three components of forty characters deep under the fixture root (so it exceeds sixty code
  points whatever TMPDIR is); all four refusals (open root, open entry, list directory, set group
  and mode) name the operation, the errno and the WHOLE root with no ellipsis, under the message
  limit; the proofs perform no permission act and establishing performs one chown before its
  chmod fails.
- `InitialStableLineAccess.test_a_line_root_beyond_the_path_bound_is_named_by_its_prefix`: a root
  of six 200-character components (longer than `_PATH_LIMIT`) is cut and marked, its first
  `_PATH_LIMIT - 2` characters survive, the errno survives, the message stays under the limit.
- `PathValueIsTheBoundedPathRule` (3): a path within the bound renders whole (including one of
  exactly `_PATH_LIMIT - 2` characters); beyond it the escaped form is bounded (astral case too);
  a lone surrogate renders without raising; non-text falls to `name_value`; the export exists; two
  whole paths plus prose fit the message limit.

## Verification (focused; no scans group/full/Docker/live)

| run | root | result | log |
|---|---|---|---|
| InitialStableLineAccess, before the fix | long (142 chars) | 4 failures of 24 | before-long-root.log |
| InitialStableLineAccess + PathValueIsTheBoundedPathRule | short (/var/tmp) | 29 OK | after-short-root.log |
| same | long (142 chars) | 29 OK | after-long-root.log |
| test_stopped_settlement + test_intake + test_workspaces (the reviewer's regression set) | short | 382 OK, 9.0 s | after-short-root-three-modules.log |
| same | long | 382 OK, 9.1 s | after-long-root-three-modules.log |
| test_dependencies.AnExportedLabelIsCallerInput, test_contracts_inventory, test_text_sweep (export/label/sweep rules the new export could touch) | short | 20 OK | affected-scans-classes.log |
| test_boundary_inventory HelperDeclarationsHaveExactAccounting, StatedRules, StageCProtections (read workspaces source) | short | 149 OK, 89.0 s | boundary-inventory-classes.log |

382 = the reviewer's 377 + the five new tests. Long root used:
`/var/tmp/baton-b5-long-root-reproduction-20261118-aaaaaaaaaa/<40 b>/<40 c>` (142 characters);
zero leftovers under it after every run; the directory chain was removed afterwards. No source
drift: the working tree over owner commit 438eefa6 differs only in the three candidate paths
(`git status --short v12`).

## Candidate

`CANDIDATE-SHA256.txt` (errors.py, workspaces.py, test_workspaces.py); `candidate.diff` against
438eefa6: 3 files, +178/-9.

## Observed, outside this slice

About ninety-five other refusals in the package render a filesystem path through `name_value`
(source_boundary.py's nominated-source refusals, credentials.py's root, and others). Each is
bounded at sixty code points and would cut a long path the same way; none is covered by the four
B5 failures. Listed here as debt for a later B5 batch or a coordinator decision, not changed.
