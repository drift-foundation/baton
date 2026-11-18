# B5 batch G6: the three tools singletons (M385088 + M385090) — all three repaired

K, copilot under owner claim E384905, no claim held. Review: `review-2026-11-18T02-32-07Z.md`.
Source: owner commit 2e330649 (the accepted diagnostics and secrets/boundary slices checkpointed) plus
this slice's two files; content digest 805f48c5… identical before and after every run (`source.json`,
`source-after.json`). Before-evidence for all three: `evidence/b5-reconciliation-20261118/unresolved-ids.log`.

## G6-2 — test_single_worker.AFaultedTerminalSurvivesTheContainerThatWroteIt.test_a_real_observing_status_run_mutates_no_durable_state — REPAIRED (test)

The reconciliation's note that the observing run created `inputs/assignment.json` was wrong: unittest's
truncated diff showed that path as the first extra ELEMENT of the longer list, and it is present in both
inventories. The untruncated diff (`run-maxdiff.py`, retained in the reconciliation note) shows exactly
four added files: `control.sqlite3-shm`, `control.sqlite3-wal`, `jobs.sqlite3-shm`, `jobs.sqlite3-wal`.
Those are the footprint of the two READ-ONLY connections `status --observe` opens: on a WAL-mode database
a `mode=ro` connection brings the `-shm` index and an empty `-wal` into existence and cannot remove them
when it closes, because removal is a checkpoint and a reader may not checkpoint. The accepted contract is
OBS-1 as the owner clarified it on 2026-10-18 (W316915, DESIGN.md): status opens existing databases through
validated read-only connections, changes no application data or schema, and "SQLite's normal sidecar and
locking behavior is acceptable". `ControlStore.open_readonly`'s docstring states the same boundary.

So the inventory now measures that contract instead of contradicting it: every file's bytes are still
hashed, except that the `-shm` index (not durable content) is not inventoried and a `-wal` is inventoried
BY ITS FRAMES -- one holding frames is a write and fails; one holding only its 32-byte header or nothing
reads as absent. Nothing else is excluded, and the run is then held to exactly the allowed footprint: no
sidecar before (the stores were closed), exactly the four sidecars after, both `-wal` files frameless (size
<= 32), every pre-existing durable file byte-identical. An observing run that wrote a frame, a row or any
application file fails this test as before.

## G6-3 — test_stage_execution_hardening.ConstructionUnwindsConcreteHandles.test_worker_construction_failure_closes_every_acquired_handle — REPAIRED (product)

A genuine leak. `StageExecution._closers` yielded a worker's closer only when its operations had a
`release` attribute; a worker's operations are `single_worker._Operations`, which closes through `close`
and has no `release`, so the condition was false for every worker. A construction that failed after the
implementation worker was composed (the test cuts at the review worker) unwound the coordinator and the
Authority and left the implementation worker's handles open -- and the same gap applied to any `release()`
of a composed deployment. Correction (`tools/stage_execution.py`): the closer is whichever of `release` or
`close` the operations expose. `_Operations.close` hands its disposer over once, so a worker the serving
loop already closed is not closed twice, and the original construction failure is still the one raised
(`release` collects closer failures and the test asserts the injected failure propagates).

## G6-1 — test_quiescent_assignment_finalization.TheQuiescentAssignmentIsEndedAndNothingElseIs.test_it_takes_no_agent_and_no_runtime_capability — REPAIRED (test + one product correction), after M385090

Diagnosis: `finalize_quiescent_assignment` grew two keyword-only operands under W275774 -- `govern`, the
resource-token governor whose ONE capability the finalizer asks for is `release` (the token the start
reserved is returned once the authority has fenced the assignment), and `cessation`, the evidence the
caller's own observer produced (a document, not a capability). Neither is an agent and neither can stop,
cancel or observe a runtime; the port is required because ending an assignment IS an authority act.

M385090 resolved the mode blocker (coordinator restored owner-write; content unchanged, ACLs unchanged;
`review-b5-tools-20261118/checkout-mode-repair.json`). The prepared patch was applied and then extended:

- `test_it_takes_no_agent_and_no_runtime_capability` pins the six names, asserts no agent / adapter /
  engine / runtime / stop / cancel operand, and that both governance operands are keyword-only and default
  to None (opt-in).
- `test_a_governed_finalization_asks_the_governor_only_to_release` MEASURES the order: the authority port's
  `cancel` and the governor's `release` both record into one list. Governance without cessation refuses
  with `precondition` and the list is empty -- no fence, no release. With the evidence the list is exactly
  `["fence", "release"]`; `release` is asked once with the attempt, the start operation identity and the
  caller's evidence; a governor offering any other attribute is never consulted (`__getattr__` raises); no
  runtime is stopped, the observed axis is not re-announced; a governed replay answers the same decision
  and fences and releases again idempotently.

Running that witness found the product refusing LATE: the `cessation is None` check sat beside the release,
after the decision was committed and `port.cancel` had fenced the generation, so a governed call without
its evidence ended the assignment and then refused, leaving the resource held (the first run recorded
`['fence']` before the refusal). The finalizer's own docstring puts operand ownership "before any durable
write and long before the authority is asked" (step 1), and this is a caller-shape fault knowable up front.
Correction (`attempts.py`): the evidence is required beside the capability check at the top, with the same
message; the late check is gone (the release itself unchanged: after the fence, once). This does not alter
the accepted W275774 order -- release after fencing -- it moves a shape refusal in front of every effect.

## Verification (focused; no group/full/Docker/live)

| run | result | log |
|---|---|---|
| the three G6 ids, one invocation (before M385090) | 2 OK (G6-2, G6-3), 1 FAIL (G6-1, then unapplied) | three-ids-after.log |
| tests.tools.test_stage_execution_hardening (module) + test_single_worker.AFaultedTerminalSurvivesTheContainerThatWroteIt (class) | 14 OK | affected-classes.log |
| tests.tools.test_stage_execution (whole module; the closer change's regression) | 477 OK, 254 s | stage-execution-module.log |
| tests.tools.test_quiescent_assignment_finalization (whole module, incl. the two G6-1 witnesses), after the product correction | 49 OK | finalizer-module.log (source-finalizer*.json stable) |
| finalizer regression set (test_fresh_retry_line_recovery, test_retry_task_lineage, test_attempts, boundary_inventory.EveryProbeProvesItArrived, test_driver.TheOrdinaryCommandTraversesPublicAdmission) | 509 OK, 149 s; no root left under /var/tmp (376, baseline) | finalizer-regressions.log (source-finalizer.json / source-after.json stable) |

## Candidate

`CANDIDATE-SHA256.txt`: tools/stage_execution.py, tests/tools/test_single_worker.py,
src/baton_v12/worker_manager/attempts.py, tests/tools/test_quiescent_assignment_finalization.py.
`candidate.diff` against 2e330649: 4 files, +145/-12. `finalization-test.proposed.patch` is the pre-M385090
prepared form, superseded by the applied and extended test.

## Leaked fixture roots: attributed, recorded, removed

Eight roots under /var/tmp were positively attributed to this Work's runs by creation time against the
run logs: four `v12-credentials-*` at 02:04:58Z, inside the 84-id reconciliation run (02:03:45Z-02:05:38Z,
`b5-reconciliation-20261118/unresolved-ids.log`, which ran tests.manager.test_credentials ids), and four
`v12-w110774-*` at 02:39:36Z, inside the test_stage_execution module run (started ~02:35:33Z, 255 s). Their
full listings (modes, sizes, paths) are retained in `leaked-roots-before-removal.txt`; they held only
fixture material (a control store, credential/inputs/workspace dirs; launch-home and bundle trees), no
evidence. Exactly those eight were removed (`leaked-roots-removed.txt`); /var/tmp is back to the 376-entry
scans baseline, listing identical. The older roots of both families (dated 2026-10-30 and earlier) are
NOT attributed to this session and were retained.

Leak sites, for the bounded final cleanup (not changed here; no credentials edits):

- `tests/manager/test_credentials.py:79-116` (`CredentialCase.setUp` / `_release`): the fixture `mkdtemp`s
  `v12-credentials-*` and its cleanup `_release` only restores modes (0o700/0o600) -- it never removes the
  root, so EVERY case leaves one. Fix shape: `shutil.rmtree(self.home_place)` after the mode restoration.
- `tests/tools/test_integration_worker.py:73-74`: `addCleanup(shutil.rmtree, self.root, True)` over a root
  that the test freezes read-only (`dr-xr-xr-x` bundle/evidence directories, 16 of them in the four roots);
  `rmtree(ignore_errors=True)` cannot unlink entries inside a read-only directory and swallows the error, so
  the frozen subtrees survive. Fix shape: thaw (chmod u+rwx, topdown) before rmtree, or rmtree with an
  onexc handler that thaws and retries.

## Observed, not changed

The two fixture leak sites above are recorded for the bounded final cleanup and were not edited in this slice; older leftover roots of both families (2026-10-30 and earlier) are retained as not attributable to this session.
