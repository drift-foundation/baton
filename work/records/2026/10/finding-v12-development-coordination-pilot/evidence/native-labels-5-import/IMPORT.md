# native-labels-5: reviewed host import + package verification (K, M385328)

Assignment: T321608 seq 385328 (coordinator), after joined-source acceptance and import readiness in `work/records/2026/11/finding-v12-retained-labels-candidate-review/review-2026-11-20T04-14-36Z.md`. Owner-held W321608 interactive arrangement; K holds no claim. Host import and local package verification only: no deployment, no Git mutation.

## Bound inputs

- Checkpoint: HEAD `86c1c22b9125176b0127fc4a86fa00855ed6d127` (unchanged throughout; `git` used read-only with `GIT_OPTIONAL_LOCKS=0`).
- Joined packet `evidence/native-labels-5-joined/`: manifest.json sha256 `ce1cb5aa41c3add9a12fea7713ac39f37b9e20c1239f64fa5ec27afe2d265cba`; joined.patch `1d7bbdedd69df2568de80228c4e1f96c1f51befeef64d813921f95a8257f509b`; reviewed preflight helper `preflight/import_preflight.py` `92605e24f4b77e0a72310f33c64a7915c9e4c09e7e92f8b9aa7fb98ec5c7f06d`. All three hashes and all 11 joined per-path hashes re-derived and found in the review (`preflight/revalidation.txt`).
- Accepted inputs: labels correction-3 manifest `d52ebd7e…`; W385263 monitoring manifest `7c1da2d2…`.

## 1. Preflight (read-only), immediately before the import

`preflight/preflight-before-import.json` + `.stdout`: verdict **ok, 11 checked, 0 refusals** (HEAD = checkpoint; path set clean; nine existing targets regular non-symlink owner-writable files at the reviewed base bytes; two new paths absent; candidate bytes = joined). Ancestor directories beneath the checkout verified real directories (`revalidation.txt`). The import helper re-ran the same preflight in-process and re-checked every target again right before writing.

## 2. Import (ordinary filesystem writes)

`import/import_joined.py` (sha256 in `import/helper-sha256.txt`): refuses the whole import before the first write on any mismatch; existing files rewritten in place (same inode, mode untouched: no chmod, no install, no rename-over); new files created `O_EXCL` mode 0644; nothing touches Git. `import/import-report.json`: **imported, 11 written**; `import/postflight.txt`: all 11 final sha256 equal the manifest's `joined`; modes preserved (0644/0664 as found; the two new files 0644); `git status --porcelain -- v12` = exactly 9 ` M` + 2 `??`; both registrations present in `tools/parallel_test.py` (`tests.tools.test_job_observation` line 428, `tests.tools.test_work_command` line 514); the six non-shared W385263 monitoring paths byte-identical to the accepted manifest; `import/diff-vs-joined-patch.txt`: the working-tree diff bodies and hunk ranges of the 9 tracked paths equal joined.patch, the 2 new files identical to the candidate.

## 3. Bounded integration on the host (`integration/`)

Runner registry via `Suite.check_registry/check_groups`: **189 modules, ok** (`registry.txt/.json`). `just test-one` over the eight affected modules on the prepared interpreter (3.13.7): **Ran 428 — OK, 0 skipped, 28.695 s** (`just-test-one.log`); per module 49/102/38/52/27/7/81/72 (`per-module.txt`). Disclosed: the first run used a disk-backed root under `work/scratch`, which the fixtures refuse as inside the checkout (38 failures, all that assertion; `just-test-one-first-root-inside-checkout-refused.log`). Rerun with `BATON_V12_STACK_TEST_ROOT=BATON_V12_DISK_ROOT=/var/tmp/baton-v12-labels5-import/integration` (disk-backed, outside the checkout, TESTING.md's documented fallback); `TMPDIR` stayed on `work/scratch/w383217/labels5-import/tmp`.

## 4. Candidate-bound packaged gate (`packaging/`)

`just --justfile v12/justfile test-packaging` (one build): pip resolved `requirements.build.lock` with `--require-hashes` (pyinstaller 6.16.0 and its pins were fetched from the index, hash-enforced, as the recipe does); PyInstaller built `build/out/distro` (gitignored; the previous d8f77700-stamped build output there was replaced). Bundle identity (`bundle-identity.json`, `bundle-version.txt`): `baton 12.0.0 (86c1c22b, dirty)`, frozen, executable sha256 **`1265b1ff4c014cf9149bbdeeec8dc91163c0f41b5c3a35484e7dfbc135f9cb25`**, three schema assets, native rpds. Disclosed: the recipe's test phase first ran with the same inside-checkout root and failed 13/24, all `test_packaged_creation` fixture-root refusals; `test_packaging` 11/11 ok including every-subcommand-offered (`gate-build-and-first-test-phase-root-inside-checkout-refused.log`). The recipe's exact final `exec` line was then rerun against the SAME bundle (not rebuilt; sha256 identical before and after) with the outside root: **Ran 24 — OK, 0 skipped, 14.155 s** (`packaged-tests.log`).

## 5. Bundled `work` CLI and `create --label` through the fresh bundle (`labels-cli/`)

`packaged_work_labels_probe.py` (disposable, not registered; sha256 in `probe-sha256.txt`) subclasses the packaged creation fixture: every command is the frozen executable as a subprocess with nothing of the checkout in its environment, against instances the bundle itself installs (`bootstrap --distro <bundle> --no-repositories`). Five cases, **Ran 5 — OK, 8.667 s, 41 bundle invocations** (`probe.log`, per-case `transcript-*.json` with argv/exit/stdout/stderr): `work --help` offers the four verbs; a Job-less install's `manager create --label Release-Foo --label V12` mints the Work with `["release-foo","v12"]`, `work labels` shows two `work-create` events, `work list --label/--without-label` selects it, the same request again reaches the same boundary without label guidance; a reused Work refuses relabel by name, the unprivileged bundled `label-work` is refused (exit 2, nothing changed), after `manage-work-labels` the act commits, an exact replay is byte-identical with no second effect, a same-identity different-operand act collides, `list` finds the label, `unlabel-work` removes it; full-capacity (32) drift → the refusal names unlabel-then-label, the adding act alone is refused at capacity, following the named acts restores the minted set, 36 events; malformed/duplicate labels refuse before any effect through both `create --label` and `work label-work`. Disclosed: the first run failed one case on the probe's own help-text assertion (argparse line wrap); assertion corrected, product bytes unchanged, first log kept.

## Limits and what remains

Not run / not claimed: full suite, group runs, Docker/image build, live model, native Job, installed-instance update or restart, deployment. No Git mutation, staging, custody-mode change or edit beyond the 11 accepted paths. Native-pilot acceptance is not asserted. The fresh_attempt raw-id observation remains for coordinator classification.

Prepared diff for Slawomir's checkpoint (human Git only): 9 modified + 2 new v12 paths above; dossier evidence directories under `work/records/...` are his to include. Proposed commit message:

```
v12: expose Work labels through the bundled work command and create --label

Add tools/work_command.py (label-work, unlabel-work, labels, list) wired as
`baton-v12-stack work`; apply create-time labels only to the Work this creation
mints (canonical Job/Work digest identity), refuse to relabel another creation's
Work with runnable guidance, restore a drifted minted set removal-first within
label capacity. Tests: test_work_command (new), creation, connected creation,
authority labels/exposure; registry retains the test_job_observation entry.
Reviewed: W385292 source + joined composition; import/package evidence in
work/records/2026/10/finding-v12-development-coordination-pilot/evidence/native-labels-5-import/.
```
