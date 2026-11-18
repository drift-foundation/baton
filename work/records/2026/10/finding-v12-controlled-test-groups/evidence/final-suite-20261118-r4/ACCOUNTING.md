ledger: work/records/2026/10/finding-v12-controlled-test-groups/evidence/final-suite-20261118-r4/test-all.summary.json
verdict ok: True

| collected | executed | passed | opt skip | req skip | failed | errors | fixture skip | fixture err | dup | unacc | uncoll | stray | unexp. success |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 11277 | 11277 | 11275 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

| group | collected |
|---|---|
| authority | 423 |
| integration | 796 |
| job_manager | 1524 |
| manager-engine | 237 |
| manager-pure | 4433 |
| scans | 494 |
| supervised | 1 |
| tools-packaged | 24 |
| tools-pure | 3345 |

accounting identity: passed 11275 + optional skipped 2 = 11277 of collected 11277

## failed (0)

## errors (0)

## unaccounted (0)

## duplicates (0)

## uncollected (0)

## unexpected_successes (0)

## required_skipped (0)

## fixture_skipped (0)

## fixture_errors (0)

## optional_skipped (2)
- tests.manager.test_source_boundary.CleanupNeverRemovesMaterialThisManagerDidNotCreate.test_a_real_same_filesystem_bind_mount_is_refused — this run cannot create a mount namespace, so the REAL same-filesystem bind mount is not exercised here; test_a_same_filesystem_mount_is_refused_though_its_device_matches proves the same boundary from 
- tests.manager.test_source_boundary.TheWorkspaceIsStorageAndScratchIsBounded.test_more_than_the_scratch_bound_really_fits_in_the_workspace — the >64 MiB disk-workspace proof writes more than the bootstrap container's whole 64 MiB tmpfs; set BATON_V12_LARGE_WORKSPACE_PROOF=1 on a host with room to run it

## stray_errors (0)

## phases
{
 "parallel source": {
  "errors": 0,
  "failures": 0,
  "ok": true,
  "ran": 10764,
  "shards": 1445,
  "skipped": 2
 },
 "serial source": {
  "errors": 0,
  "failures": 0,
  "ok": true,
  "ran": 512,
  "shards": 19,
  "skipped": 0
 },
 "supervised source": {
  "errors": 0,
  "failures": 0,
  "ok": true,
  "ran": 1,
  "shards": 1,
  "skipped": 0
 }
}
