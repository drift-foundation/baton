# Accounted scans-group run (M385050, review 2026-11-18T01-30-50Z)

K, copilot under owner claim E384905, no claim held. One run, verification and reporting only: no
product, test or dossier-plan edit preceded it in this slice; no repairs followed it.

## Snapshot

Owner commit `438eefa6` ("fix(v12): bind renewal decisions and verify boundary provenance",
2026-11-17 18:31:57 -0700) contains the reviewed callback-trace candidate: all fourteen digests of
`evidence/callback-trace-20261117/CANDIDATE-SHA256.txt` verify against the committed tree
(`sha256sum -c`: 14 OK) and `git status --short v12` lists nothing. Content-bound source identity
(`tools.source_identity --declared v12`): HEAD 438eefa68f592e159f42cf1d190c7d7de4afde12, changed
files 0, consumed-input files 41, content digest
`52a08680eb445edf3e22eac53b7acb8029a29743bac58f30a8e74bfa3a1cd934`; identical before and after
(`scans.source.json`, `scans.source-after.json`). No drift.

## Invocation

`run-scans.sh`: the `test-group` recipe's exact runner invocation on the prepared interpreter
(`tools/parallel_test.py --group scans --account --keep-going --jobs 4`) plus `--summary` for the
JSON ledger, which the recipe does not write; `TMPDIR=/var/tmp BATON_V12_DISK_ROOT=/var/tmp`;
per-run timeout 3300 s (INT, kill after 60 s). Python 3.13.7, jsonschema 4.26.0, 32 CPUs, 4 workers.

## Result

| total | value |
|---|---|
| collected | 494 (test_boundary_inventory, test_contracts_inventory, test_dependencies, test_source_boundary, test_text_sweep; 75 shards) |
| executed | 494 |
| passed | 492 |
| optional skipped (registry) | 2 |
| required skipped | 0 |
| failed / errors / stray errors | 0 / 0 / 0 |
| fixture skips / fixture errors | 0 / 0 |
| duplicates / unaccounted / uncollected / unexpected successes | 0 / 0 / 0 / 0 |
| accounting | passed 492 + optional skipped 2 = 494 of collected 494 -> OK |
| runner exit / elapsed | 0 / 138 s (01:34:02Z to 01:36:20Z) |

Optional skips, both in `OPTIONAL_SKIPS` with their recorded reasons:
`tests.manager.test_source_boundary.CleanupNeverRemovesMaterialThisManagerDidNotCreate.test_a_real_same_filesystem_bind_mount_is_refused`
(no mount namespace on this host) and
`tests.manager.test_source_boundary.TheWorkspaceIsStorageAndScratchIsBounded.test_more_than_the_scratch_bound_really_fits_in_the_workspace`
(selected by BATON_V12_LARGE_WORKSPACE_PROOF=1). No failed ids.

Cleanup: `/var/tmp` listing identical before and after (376 entries, `var-tmp-before.txt`,
`var-tmp-after.txt`); the run left nothing. Files: `scans.log` (header + runner output + footer),
`scans.summary.json` (ledger), the two identity documents, `run-scans.sh`.

Not run, per the ruling: full suite, B4/B5, Docker, live. The four long-root diagnostics remain
recorded for B5 (`review-owner-selections-20261117/regression.log`).
