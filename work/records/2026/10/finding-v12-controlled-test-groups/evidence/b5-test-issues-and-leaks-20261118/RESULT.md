# Two queued test issues + nine fixture leak sites (M385106, review 2026-11-18T06-32-07Z)

K, copilot under owner claim E384905, no claim held. Test-side only: no product byte changed. Candidate over
committed 314e067c: `candidate.diff` (14 files, +320/-49; `CANDIDATE-SHA256.txt`), which INCLUDES the two
accepted G2 files (`correction_restart_trace.py`, `test_correction_restart.py`, unchanged since M385105,
not yet committed) plus the twelve files of this batch. Source identity (`tools.source_identity --declared
v12`): HEAD 314e067c, changed 14, consumed 41, digest
`56749070b61684261fd5f0bf3a53ec3fb0157ece3fe2ff9b08512411e86f9217`, identical before and after the batch
(`source.json`, `source-after.json`) and still current at handoff. Groups touched: manager-pure and
tools-pure (the inventory assertion is in the scans group's `test_boundary_inventory`; one focused id of it
was run, no group). No live/Docker/group/scans/full run.

## 1. Diagnostic-rendering pin (manager-pure) — both intentions kept

`tests/manager/test_boundary_inventory.py` `EveryProbeProvesItArrived.test_the_missing_probe_check_can_actually_fail`:
the Stage B assertion `assertEqual({pair[0] for pair in newly}, {dropped[0]})` becomes
`assertEqual(sorted({pair[0] for pair in newly}), [dropped[0]])`. Same verdict (exactly the dropped probe is
newly unprobed against the current baseline); a nonempty difference now renders in one fixed order, which is
what W10265 ruled. `tests/manager/test_diagnostic_rendering.py`: the stale pin
`test_the_missing_probe_check_compares_a_sorted_list_with_an_empty_list` is REPLACED by
`test_the_missing_probe_check_compares_sorted_lists` (id change recorded here): first `assertEqual` has a
`sorted(...)` measured side, a list (not a set) expected side with exactly one element, and neither side is a
set literal or set comprehension. The module's other pins are unchanged. Results: `diagnostic_rendering.log`
10/10 OK (1.0 s); `inventory_probe_check.log` the changed inventory id 1/1 OK (7.4 s).

## 2. Operator-view residue under concurrency (tools-pure) — ownership, not serialization

`tests/tools/test_operator_verification_view.py`: `OperatorViewCase.private_views()` patches
`dogfood_operator.VERIFICATION_TEMP_ROOT` (module attribute read at call time; `_derived_in_view` runs
in-process) to a root under the case's own home, and `views_left_in()` lists it. Both residue checks
(`test_the_view_is_removed_and_the_retained_output_is_not`, `test_the_view_is_gone_after_every_refusal`) plant
a FOREIGN `dogfood-view-*` directory there first and require exactly that one to remain, untouched. NEW
`test_a_concurrent_shards_view_is_neither_a_leak_nor_removed`: two refusals and one derived run, the foreign
view (with content) inspected after each. Product `discard_view` is unchanged (it already removes only its own
root). Results: `operator_view.log` 39/39 OK (6.3 s); CONCURRENCY: four simultaneous `just test-one` runs of
the module over the shared host `/tmp` (`concurrent-1..4.log`, `concurrent.exit.txt`): 4× 39/39 OK in 7 s
wall, zero `dogfood-view-*` left in `/tmp` afterwards (`concurrent.tmp-views-after.txt`). The original race
listed `/tmp` globally; it cannot recur because no case lists the shared root any more.

## 3. Nine fixture leak sites — one shared remover, fixture-owned roots only

`tests/manager/disk_roots.py` gains `remove_owned_root(place)`: refuses a link or a non-directory root,
restores owner access (0700) on every REAL directory under the root via `scandir` (so 0-mode and 0555
directories are entered), never follows a symlink, then `shutil.rmtree` WITHOUT `ignore_errors` so a fixture
that cannot remove its own root reports it instead of leaking silently. Proved in `tests/manager/test_sealing.py`
`TheFixtureRemovesItsOwnFrozenRoot` (3 cases): a root with 0555 dirs, a 0444 file and a 0-mode dir is removed
whole; a symlink inside the root to an outside tree is removed as a link while the outside 0555/0444 target keeps
its bytes and modes; a link or a plain file as the root is refused and left in place.

| site | before | after |
|---|---|---|
| tests/manager/test_credentials.py `_release` | chmod walk, never removed | `remove_owned_root(home_place)` |
| tests/manager/test_sealing.py `_release` | chmod walk, never removed | `remove_owned_root(root)` |
| tests/manager/test_attempt_logs.py setUp (v12-w198667) | `rmtree(ignore_errors)` over frozen launch | `remove_owned_root` |
| tests/manager/test_maintenance.py foreign root (v12-foreign) | no cleanup | `addCleanup(remove_owned_root)` after the refusal |
| tests/manager/test_maintenance.py `substituted()` (v12-substituted) | no cleanup | `addCleanup` only when the helper made the dir |
| tests/tools/test_integration_worker.py setUp (v12-w110774) | `rmtree(ignore_errors)` over frozen attempts | `remove_owned_root` |
| tests/tools/test_managed_preparation.py trap/operands inputs (w161230-*) | `rmtree(ignore_errors)` over 0555 publication | `remove_owned_root` |
| tests/tools/test_single_worker.py ingest setUp (v12-ingest) | `rmtree(ignore_errors)` over frozen attempt | `remove_owned_root` |
| tests/tools/test_single_worker.py line ~400 bare `mkdtemp()` | no cleanup | prefixed root + `remove_owned_root` |
| tests/tools/test_dogfood_operator.py `OperatorCase` (v12-w39358) | `rmtree(ignore_errors)` over frozen storage | `remove_owned_root` |

Frozen-directory and foreign/substituted-resource behaviour is untouched: the product still freezes what it
delivers, the maintenance refusals still prove the manager leaves the foreign tree alone, and cleanup runs
only on roots the fixture itself made (`mkdtemp`), after the case's assertions.

## Residue accounting (every run: `/var/tmp` listed before and after; `summary.tsv`)

| module / id | result | time | new `/var/tmp` entries |
|---|---|---|---|
| tests.manager.test_sealing | 68/68 OK | 1 s | 0 |
| tests.manager.test_credentials | 110/110 OK | <1 s | 0 |
| tests.manager.test_attempt_logs | 213/213 OK | 3 s | 0 |
| tests.manager.test_maintenance | 149/149 OK | 4 s | 0 |
| tests.tools.test_integration_worker | 40/40 OK | 11 s | 0 |
| tests.tools.test_managed_preparation (see note) | 100/100 OK | 114 s | 0 |
| tests.tools.test_single_worker | 253/253 OK | 20 s | 0 |
| tests.tools.test_dogfood_operator | 359/359 OK | 9 s | 0 |
| tests.tools.test_operator_verification_view | 39/39 OK | 7 s | 0 |
| tests.manager.test_diagnostic_rendering | 10/10 OK | 1 s | 0 |
| ...test_boundary_inventory.EveryProbeProvesItArrived.test_the_missing_probe_check_can_actually_fail | 1/1 OK | 8 s | 0 |
| operator-view module ×4 concurrently | 4× 39/39 OK | 7 s | 0 (and 0 views in /tmp) |

In the five-group run these same modules left 262 roots; `/var/tmp` is 376 before and after every run here.

NOTE (observation, not repaired, queued): `tests/tools/test_managed_preparation.py` imports `integration_bundle`
as a TOP-LEVEL module. That resolves only because the runner starts every shard as
`python tools/parallel_test.py ...` (sys.path[0] = `tools/`); under `just test-one` the module fails to import
(`ModuleNotFoundError: integration_bundle`), and the unmodified HEAD version fails identically
(verified from a temporary copy at its real location, removed afterwards). It was therefore run here with the
runner-equivalent path (tools first, then root, then src; exact command in `summary.tsv`/`run-batch.sh`
annotation). The import is unrelated to this batch's changes; fixing it (`from tools import integration_bundle`
or an explicit path insert like the module already does for `worker/`) is a separate small item because
`integration_bundle` may be imported under two names by other code.

## Not done, per the ruling

No group retry, no full suite. Remaining known items: the import observation above. Next, after review: owner
Git checkpoint, then the exact durable-log full-suite command and prerequisites for Slawomir.

## Correction after review 2026-11-18T06-49-00Z (M385108): the import, and the evidence record

Import: `tests/tools/test_managed_preparation.py` line 33 now reads `from tools import integration_bundle as bundle`,
the spelling `test_integration_bundle.py` and `test_managed_apply.py` already use and the one `tools/*` use for
each other (`from . import integration_bundle`), so there is one module object under every entry point. The module
has no patches of `bundle` (uses: `compose_preparation_input`, `published_preparation_request`,
`PREPARATION_OBJECTS`, `PREPARATION_REQUEST_DOCUMENT`, `PREPARATION_SOURCE_DIRECTORY`, `BUNDLE_FILE`); its
`sys.path.insert(WORKER)` for `reconciliation_entry`/`reconciliation_task` is unchanged. No assertion changed.

Verification (`summary.tsv` appended lines, `per-run-listings/`):
- ordinary `just test-one tests.tools.test_managed_preparation`, no caller sys.path adjustment:
  `managed_preparation_fixed.log` 100/100 OK in 113.1 s, residue 0.
- fresh-process shard entry, exactly the runner's child invocation (`python tools/parallel_test.py run-shard
  shard-entry.plan.json` with `PYTHONPATH=<root>:<root>/src`): class
  `ThePublishedInputIsMeasuredTheSameWayAtBothEnds`, `shard-entry.report.json` ran 10, executed 10, ok, residue 0.

Evidence record corrected: the RESULT text above said the earlier workaround command was annotated in
`summary.tsv`/`run-batch.sh`; it was not. `summary.tsv` now carries, as appended comment lines, the verbatim command
actually used (runner-equivalent sys.path: tools first, root, src), the fact that the driver's original failed
line was rewritten in place, and a pointer to `batch-console-initial.txt` line 6 where the initial failed
invocation's summary (`FAILED (errors=1)`, 0 s) is preserved. The initial failed run's log file was overwritten by
the rerun and is not recoverable; the failure text as observed was
`ModuleNotFoundError: No module named 'integration_bundle'` at line 33, which the reviewer reproduced independently.
`per-run-listings/` now holds every per-run `/var/tmp` before/after listing from scratch (25 from the batch, plus
the two runs here); each pair differs by 0 entries.

Candidate now 14 files (+326/-50 over 314e067c; `candidate.diff`, `CANDIDATE-SHA256.txt` regenerated); identity
`source-after-import-fix.json`. No remaining known item from this batch.
