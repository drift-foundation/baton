# W385424 — R1/R2 correction over the frozen native candidate (K, owner-held arrangement)

K (`baton.prompt`, no claim; M385468) on review `review-2026-11-21T12-34-16Z.md` (E385465, changes requested). Isolated; not composed, not imported; the native packet (`evidence/native-attempt-be4fbac0-recovery/`) and the accepted W385427/W385454 bytes are untouched.

## Candidate

| | |
|---|---|
| Starting bytes | the frozen native candidate, listing `e686d8c271b97dc65af65f3266c75a9c374df000dd08db22a099bb014a452e12` (10 paths over `7ac02c7f`, native head `4c528624…`), re-verified path by path before editing |
| Changed here | 3 of the 10: `src/baton_v12/worker_manager/failure_cause.py` (`05f49b4a…` → `bcd53370…`), `tests/manager/test_attempt_failure_cause.py` (`62b690e9…` → `093db1a8…`), `tests/tools/test_job_observation.py` (`813d9a37…` → `f1aa0b8b…`); the other 7 are byte-identical to the native candidate |
| New listing | **`10f3d809254c3da937b4dc0761c9ec5971ea55ec2c0ed1fe6b21d50d3511eae0`** (`candidate.sha256`, all 10 paths); patch `correction-from-native.patch` `fb31d571…` (186 lines, applies to the native tree with `patch -p1`, reproduced and compared) |
| Base/candidate copies | `base/<path>` = native bytes, `candidate/<path>` = corrected, for the three paths; `manifest.json` carries every path's native, corrected and `7ac02c7f` digest |
| Overlay | W385454 tree `c6755437…` (`test_stage_execution.py` `03a7710e…`, accepted M385461) used ONLY to run the two deep compatibility cases; it is not part of this candidate and is named as such in `manifest.json` |

## R1 — a bounded open (`failure_cause._bound_bytes`)

The retained result is opened with `O_RDONLY | O_NOFOLLOW | O_CLOEXEC | O_NONBLOCK`; the type is still judged on the opened descriptor (`fstat`, `S_ISREG`) and the measured size and digest still bind the bytes. A FIFO left where the regular file was measured now opens at once and is refused as "not a regular file" without waiting for a writer; a regular file reads exactly as before (the flag has no effect on it). No change to the size/digest checks, the symlink refusal, the manifest/artifact identity binding or the caller's unknown reasons.

## R2 — absent is not null (`failure_cause._declared_members`)

The verification member is read with a sentinel: no member → `verification_attempted` and `verification_status` both unknown ("the retained result carries no verification member, so whether a command ran is unknown"); explicit `null` → attempted `(known, False)` with the status unknown, as before; a document → attempted `(known, True)` with the status owned only inside `EXIT_STATUS_RANGE`; anything else → both unknown, as before. The other declared members, the sealed disposition, `result_id`/`frozen_at`, the cause/revocation/cancellation axes and lifecycle separation are untouched. The operator sentence already distinguishes the cases (`job_observation`: "verification not attempted" / "verification … status N" / "whether verification ran is unknown"); no renderer change was needed.

## Verification

- **Public diagnostic path, new deterministic cases** (`tests.manager.test_attempt_failure_cause.TheWorkerDeclaredAxisIsComposedFromSEALEDEVIDENCE`): FIFO in place of the sealed result → the public `attempt_failure_cause_of` returns promptly (a 5-second watchdog that would supply a writer and record the wait is never triggered), every typed member unknown with the "does not recompute" reason, disposition and `result_id` still known, cause axis unmoved; missing verification member → both axes unknown with the "no verification member" reason while the other members still stand; explicit `null` → not attempted; valid status 0 → known; malformed member (`"ran"`, `7`, `[]`, `{"status": "one"}`, `{"status": 2**40}`) → status unknown, attempted unknown unless a document. Rendering (`tests.tools.test_job_observation`): an unknown verification axis renders "whether verification ran is unknown" in status, list and detail, never "not attempted". Class run: 20/20 and 39/39 with the module (`logs/declared-axis-2.log`). Honest accounting: `logs/declared-axis-1.log` is the first run of the new cases — the FIFO case was first written on a worker thread and hit the store's thread binding (`KeyError` on the thread's missing answer), and the malformed case wrongly expected `-1` outside `EXIT_STATUS_RANGE (-256, 65535)`; both are test-side corrections (watchdog on a timer, `2**40`), the product correction did not change.
- **The reviewer's own probes rerun on the corrected tree** (`probes/`, `probe.py` byte-copied from `review-E385465`; 10-second hard limit): `fifo` returns in 0.4 s ("returned"; was killed at 3 s on the native bytes); `missing-verification` reports `verification_attempted [false, null]`, `verification_status [false, null]` (was `[true, false]`); `nested-json` unchanged, 0.4 s.
- **Required four-module coverage, overlay named separately**: the reviewer's `run_focused.py` selection (the four mandatory modules minus the two deep cases) on the corrected tree WITHOUT the overlay: **Ran 271, OK** (266 + the 5 new cases; `logs/focused-266-candidate.log`, Git rejected on PATH, 2.8 s wall); the same on the overlay tree: **Ran 271, OK** (`logs/focused-266-overlay.log`). The two deep cases on the overlay tree under the established confinement (bubblewrap read-only host, W385427's fixture Git guard, fresh fixture roots, prepared interpreter, bytecode off): umask 077 **2/2 OK** (posture accepted at `0o730`), umask 022 **2/2 OK** (`0o775`); 442 confined Git invocations each, 0 refused, none outside the fixture roots (`umask-runs/SUMMARY.json`). So 273 required/added cases pass: 271 + 2. This is overlay verification, not pristine-native verification; the native attempt's exit 1 stays historical fact. `logs/stale/` keeps the first overlay runs made before the overlay copy was re-synced with the final test files (271 vs 270 tests, 1 F / 1 E from the stale test bytes) — a packaging slip of mine, disclosed, not a product result.

## Custody note

`narrative-current.sha256` is the supplemental digest of `evidence/native-attempt-be4fbac0-recovery/RECOVERY.md` as it now is (`7023f42d…`, after its append-only clarification); the stale entry in that packet's `evidence.sha256` is left as recorded, per the review.

## Boundaries

No composition with W385427 or W385454, no host import, no live-instance read or change, no Git mutation of the owner checkout or any existing repository (fixture Git only inside fresh confined roots under `/var/tmp/baton-v12-w385424-fix/verification-git/`, logged). The isolated trees under `/var/tmp/baton-v12-w385424-fix/` are disposable. Handoff: independent delta review of the three-path delta; then the serial composition of the three deltas with joined review before any host import and human checkpoint.
