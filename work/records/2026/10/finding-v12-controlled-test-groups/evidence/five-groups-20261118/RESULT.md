# Five accounted group runs (M385102, review 2026-11-18T04-29-34Z)

K, copilot under owner claim E384905, no claim held. Verification and reporting only: no product, test or
plan edit preceded or followed these runs in this slice; nothing was retried.

## Snapshot

Owner commit `314e067c` ("fix(v12): preserve revoked replay boundaries and repair launch fixtures",
2026-11-17 22:27:50 -0700) holds the accepted G6, G1 and G3 candidates; `git status --short v12` lists
nothing (the one status line during the runs is this untracked evidence directory under `work/`, outside the
identity by construction). Content-bound source identity (`tools.source_identity --declared v12`): HEAD
314e067c9e3dc048054293f0d35ea9b25de2cdb2, changed files 0, consumed-input files 41, content digest
`194edb1f466ae2d4dc811c932ed2509f49e9c0b22bcff9429017fbde32cbb3b9`, identical before and after every one of
the five groups (`<group>.source.json`, `<group>.source-after.json`). No drift; HEAD unchanged throughout.

## Invocation

`run-five-groups.sh`: the `test-group` recipe's exact runner invocation on the prepared interpreter
(`tools/parallel_test.py --group G --account --keep-going --jobs 8`) plus `--summary` for the JSON ledger,
groups in the order authority, job_manager, manager-pure, tools-pure, integration, each once;
`TMPDIR=/var/tmp BATON_V12_DISK_ROOT=/var/tmp`; per-group timeouts 2400/3600/5400/5400/3600 s (INT, kill
after 120 s), none reached. Python 3.13.7, jsonschema 4.26.0, 32 CPUs, 8 workers (the guide's own example
count). Driver 05:30:30Z to 05:35:03Z. A first launch of the script aborted on an unbound shell variable
before any test started (nothing ran, no files written); the corrected script is the retained one.

## Result

| group | collected | executed | passed | opt skip | req skip | failed | fixture err | unaccounted | verdict | exit | elapsed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| authority | 423 | 423 | 423 | 0 | 0 | 0 | 0 | 0 | OK | 0 | 3 s |
| job_manager | 1524 | 1524 | 1524 | 0 | 0 | 0 | 0 | 0 | OK | 0 | 20 s |
| manager-pure | 4420 | 4420 | 4419 | 0 | 0 | 1 | 0 | 0 | FAILED | 1 | 66 s |
| tools-pure | 3341 | 3322 | 3318 | 0 | 0 | 4 | 2 | 19 | FAILED | 1 | 173 s |
| integration | 796 | 796 | 796 | 0 | 0 | 0 | 0 | 0 | OK | 0 | 9 s |
| total | 10504 | 10485 | 10480 | 0 | 0 | 5 | 2 | 19 | | | 271 s |

Errors, duplicates, uncollected, stray errors, unexpected successes, optional and required skips: all zero
in every group. `CONSOLIDATED.md` (from `consolidate.py`, reads only) lists every non-passing entry.

## Current remainder: 24 ids, 26 entries

KNOWN G2 (22 of 22, unchanged): `tests.tools.test_correction_restart`, one fixture cause. Both InvalidEvidence
classes error in `setUpClass` (19 ids never start, UNACCOUNTED) and three single tests fail, all on
`"failure": "preparation did not answer"`: the controller's preparation child exits 1 with an empty log;
the preparation record shows `describe` answered and `work` faulted with `fault_code: "agent"` over
`baton.worker-exchange/1` (tools-pure.log lines 1496-1558). The two `setUpClass (...)` fixture-event keys
are these classes, not new ids. The child's own trace is still unread: it is not in the failure text and
no `/var/tmp` root of this module was left behind.

NEW (2 ids, not in the known list):

1. `tests.manager.test_diagnostic_rendering.TheRuledAssertionsRenderThroughSortedCollections.test_the_missing_probe_check_compares_a_sorted_list_with_an_empty_list`
   (manager-pure). CONFIRMED deterministic source-shape failure, not a race. The W10265 pin requires the
   FIRST `assertEqual` of `test_boundary_inventory.test_the_missing_probe_check_can_actually_fail` to compare
   `sorted(...)` against `[]`. Stage B of this Work (owner commit a8cbc9745, 2026-10-30, reviewed
   2026-10-30T21:08:28Z) rewrote that function to prove the guard against the current baseline, and its
   first `assertEqual` is now `assertEqual({pair[0] for pair in newly}, {dropped[0]})` (set comprehension
   against a one-element set; `test_boundary_inventory.py` line ~12397). Two accepted tests now contradict
   each other: the W10265 rendering pin and the Stage B baseline-relative proof. Not in B0 because Stage B
   postdates B0; manager-pure has not been run as a group since. Repair needs a choice between re-pinning
   W10265 to the Stage B shape (recorded ruling) or giving the Stage B assertion a sorted-list form; I
   propose nothing here.
2. `tests.tools.test_operator_verification_view.TheOperatorsViewRefusesWhatThePacketSays.test_the_view_is_gone_after_every_refusal`
   (tools-pure): `['dogfood-view-bbcoxzwc'] != []`. CONFIRMED: `dogfood_operator.VERIFICATION_TEMP_ROOT` is
   the shared host `/tmp`, the residue check lists every `dogfood-view-*` entry there (lines 361-364), and the
   module's three `OperatorViewCase` classes run as three concurrent shards that each materialize views in
   that root; `/tmp` held no `dogfood-view-*` entry after the run, so the view seen was another shard's
   live view, cleaned by its owner. B0 recorded this id failed and "VERIFIED OK now" on focused rerun.
   INFERRED: a cross-shard race under parallel execution, intermittent; the test's own operator left no
   view. Repair direction (proposed, not done): bound the residue check to views this test created, or give
   each test its own verification root.

## Fixture leak events (not test outcomes): 262 roots, 47 MB

Every new `/var/tmp` entry has an mtime inside the manager-pure window (05:30:54-05:32:00Z: 203 entries) or
the tools-pure window (05:32:00-05:34:53Z: 59 entries); authority, job_manager and integration left
nothing (`<group>.var-tmp-before/after.txt`). Attribution by prefix to the fixture that creates it
(`leaked-roots-before-removal.txt` has names and UTC mtimes):

| prefix | count | module | note |
|---|---|---|---|
| v12-credentials- | 129 | tests/manager/test_credentials.py | known leak site (`_release` never rmtrees) |
| v12-sealing- | 65 | tests/manager/test_sealing.py | NEW leak site |
| v12-w198667- | 5 | tests/manager/test_attempt_logs.py | frozen `launch/attempt-w198667` |
| v12-substituted- / v12-foreign- | 3 / 1 | tests/manager/test_maintenance.py | known leak site |
| v12-w110774- | 29 | tests/tools/test_integration_worker.py | known leak site (rmtree over frozen dirs) |
| w161230-operands-input- / w161230-trap-input- | 13 / 1 | tests/tools/test_managed_preparation.py | frozen `published*/source` |
| v12-ingest- | 11 | tests/tools/test_single_worker.py (setUp line 7028) | `rmtree(..., True)` over product-frozen `launch/attempt-1` |
| bare `tmp*` | 1 | tests/tools/test_single_worker.py line 400 | `mkdtemp()` with no cleanup |
| v12-w39358- | 4 | tests/tools/test_dogfood_operator.py | frozen `storage/attempt-*` |

Cleanup: 199 roots removed (`leaked-roots-removed.txt`); 63 remain (`leaked-roots-remaining.txt`: ingest 11,
w110774 29, w198667 5, w39358 4, operands 13, trap 1). Each remaining root holds directories the product
froze to 0555 (`stat` samples in the handoff log), which `rm -rf` refuses for the owner and which the
fixtures' own `shutil.rmtree(..., ignore_errors=True)` also could not remove; I did not change any mode.
`/var/tmp` is now 439 entries = baseline 376 + those 63 (`var-tmp-after-removal.txt`). The owner can remove
them with `remove-remaining-roots.sh` (check mode by default, `--remove` to act; it touches only the 63
named roots, all created in the run windows above). No older or uncertain root was touched.

## Not run, per the ruling

Full suite, scans, manager-engine, tools-packaged, supervised, Docker, live. No repair started; the next
step is the technical and priority review of this remainder.
