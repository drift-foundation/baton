# Progress

## 2026-09-06 — baton.tuner

Implemented the reviewed two-phase boundary in
`v12/python/src/baton_v12/integration/driver.py` and exported
`publish_candidate` and `admit_accepted` from the integration package.

Publication now re-reads the manager-retained proposal and frozen-result
manifests, the fixed producer assignment, and the current Authority target. It
cross-binds the result, input, policy, proposal output, source base, candidate
head, embedded operation, and expected receipt before calling the
participant-bound publisher. A fenced producer or moved target refuses before
publication.

The accepted phase re-reads the exact accepted checkpoint and Authority
proposal, requires the configured Authority policy generation, writes the
separate verification/review/approval receipts, re-resolves and admits the
15-member candidate account, and derives the entry and lease identities from
that account. Fresh work delegates both live-grant cutpoints and settlement to
`integrate_next`. Restart adopts the existing delivery: a positively
not-started runtime may proceed after account and grant revalidation; any
runtime that may already have been asked is passed to `hold_interrupted` and is
never run a second time. Replayed terminal integration writes/replays the one
Authority integration receipt; refused and held entries never do.

Added `v12/python/tests/integration/test_driver.py` with 14 focused cases for
exact publication/receipt replay, producer and target cross-wiring, fenced
publication, policy-generation binding, fresh integration, restart before the
run cutpoint, interrupted holding, and terminal Authority-receipt replay.

Verification:

- `PYTHONPATH=v12/python/src python3 -m unittest` over coordinator, admission,
  runtime, execution, recovery, and driver: 375 tests passed, one skipped.
- `python3 -m py_compile` for the new production and test modules: passed.
- `git diff --check` for the assigned paths: passed.
- The registered parallel runner correctly refused the current tree because
  `tests.integration.test_driver` and the concurrent
  `tests.job_manager.test_review_driver` are not yet registered. Registration
  is explicitly assigned to W103083, so this Work did not edit
  `tools/parallel_test.py`.

State: implementation complete; awaiting independent review.

## 2026-09-06 — baton.tuner correction

Implemented the reviewed exact-entry and Authority-completion correction in
the seven authorized paths. `grant_lease` now signs the required `entry_id`
and decides exact FIFO availability under its write transaction. A private
rollback-only no-act leaves no operation row, lease, delivery, runtime call,
or burned fence when another entry is ahead or another lease is live, so the
proposal's stable lease identity remains retryable.

`settle_observed` now adopts and validates an integrated runtime result while
leaving the entry leased and its grant live. The driver calls Authority
integration only on the uninterrupted path, re-reads and cross-binds the exact
receipt, then asks `complete_integrated` to settle and release. Authority
refusal or receipt mismatch takes `hold_interrupted`; restart after the port
was asked continues to hold without calling Authority integration. A terminal
integrated entry only reads an existing receipt.

Focused verification currently passes:

- `test_coordinator`: 195 tests.
- `test_execution` plus `test_driver`: 64 tests.
- Added a real two-ready-entry regression proving B is a no-act while A is
  ahead, commits no grant operation, starts no runtime, and later succeeds
  under the same lease identity after A completes.
- Added the live-lease-before-completion and Authority-refusal-to-hold cases.

The full integration discovery exposed a bounded scope dependency: the
pre-existing `test_runtime.py` and `test_recovery.py` fixtures call the now
required `grant_lease(entry_id=...)` surface directly. They account for all 97
full-suite errors; their production behavior was not reached. The correction
review explicitly authorizes only `test_execution.py` and
`test_coordinator.py` among existing tests, so neither additional fixture was
edited. Minimal scope expansion for exactly those two mechanical call-site
updates is required before full verification and candidate review.

State: corrected candidate preserved; returning for the exact two-test-path
scope decision.

## 2026-09-06 — baton.tuner completed candidate

Applied the independently authorized mechanical scope expansion from
`review-2026-09-06T17-14-47Z.md`. The four direct `grant_lease` calls in
`test_runtime.py` and `test_recovery.py` now name the exact entry their
fixtures just enqueued. No assertions, expected behavior, fixture structure,
prose, or other call site changed.

The frozen nine-path candidate passes the complete V12 integration discovery:
378 tests passed with one expected skip. `python3 -m py_compile` passed for all
nine files, `git diff --check` passed for the tracked assigned paths, and an
explicit trailing-whitespace scan passed all nine paths (including the six
new files not yet tracked by Git).

Candidate SHA-256 digests, in the dossier's accepted path order:

- `driver.py`: `3f13c15a944fda90b3c7c3b8aeb9469e82eff7b867379f2ff391dca032507b04`
- `integration/__init__.py`: `4916707c9019fab57962aff5629b5ba99fbe8390f003f4960c94b90a9b7980cd`
- `test_driver.py`: `e87ce88fb1fd0ff49eb23d022c247a760575f886f747ba22ba7692bda35e0ab1`
- `execution.py`: `91995b96369f7237dd6e8b67cf8223f3b52baf6b6304c45d53a14e13140ce330`
- `queue.py`: `2e8a153ddcdf15fcd597f51a7c81ce0405ee7b64fad9b2f3b6cf416c40489be7`
- `test_execution.py`: `53c416fa603bd31d1549f8f974dba562bf082c3963866423e87d0b073ea3a398`
- `test_coordinator.py`: `7c7d9b9ada3e8977b35137abee117b42f0b4d09359b9cda50a933a676db27a8c`
- `test_runtime.py`: `925b7dd4ae8eba7d2c375186c74859632276da3f83da3bb6734c3c7c82268c66`
- `test_recovery.py`: `c33cfa13818177afc882dd896d842036010c44656886a73c133687001e08b8fa`

State: implementation and bounded correction complete; awaiting independent
nine-path review.

## 2026-09-06 — baton.tuner settlement/release restart correction

Corrected the P0 durable cutpoint from
`review-2026-09-06T17-27-19Z.md` inside the existing nine-path boundary. A
terminal integrated entry now first reads and cross-binds its existing
Authority receipt. An exact live lease reconstructs the owner-bound assignment
from the lease and deployment profile, replays the entry's stored settlement,
and completes the release; an exact released lease remains a read-only replay.
Absent, cross-wired, or other-state leases fail closed.

The ordinary completion exception path now re-reads the entry before invoking
manual hold. If settlement already committed, it preserves the live exclusion
and propagates the failure for terminal restart rather than attempting the
invalid `integrated -> held` transition.

The new public-driver regression injects process death after
`settle_integrated` and before `release_lease`, then restarts through
`admit_accepted`. It proves the exact receipt is read, neither Authority
integration nor the runtime port is called, the live lease becomes released,
and the next FIFO entry receives its grant and runs. A separate negative case
proves an integrated entry without its lease fails closed.

Verification:

- Focused `test_driver`: 17 tests passed.
- Complete V12 integration discovery: 380 tests passed, one expected skip.
- `python3 -m py_compile`, `git diff --check`, and an explicit trailing-
  whitespace scan passed for all nine candidate paths.

Final SHA-256 digests:

- `driver.py`: `1ef1a1173b90c99745378be041906f05201f69e71901c924c2e6e14bca1babfa`
- `integration/__init__.py`: `4916707c9019fab57962aff5629b5ba99fbe8390f003f4960c94b90a9b7980cd`
- `test_driver.py`: `7df743aa4c6d7e31f85859d5d651fcb6d24ca4758f79e91d100ef8909d84da04`
- `execution.py`: `91995b96369f7237dd6e8b67cf8223f3b52baf6b6304c45d53a14e13140ce330`
- `queue.py`: `2e8a153ddcdf15fcd597f51a7c81ce0405ee7b64fad9b2f3b6cf416c40489be7`
- `test_execution.py`: `53c416fa603bd31d1549f8f974dba562bf082c3963866423e87d0b073ea3a398`
- `test_coordinator.py`: `7c7d9b9ada3e8977b35137abee117b42f0b4d09359b9cda50a933a676db27a8c`
- `test_runtime.py`: `925b7dd4ae8eba7d2c375186c74859632276da3f83da3bb6734c3c7c82268c66`
- `test_recovery.py`: `c33cfa13818177afc882dd896d842036010c44656886a73c133687001e08b8fa`

State: restart-tail correction complete; awaiting independent nine-path
candidate review.

## 2026-09-06 — baton.tuner admission-replay correction

Corrected the P0 production-path seam from
`review-2026-09-06T17-37-33Z.md`. `admit_accepted` still replays the immutable
admission operation, but no longer treats that operation's original `queued`
answer as current state. It now selects exactly one matching entry from the
coordinator's semantic read and requires its immutable eligibility to equal
the freshly resolved accepted account before terminal dispatch.

The release-tail regression no longer mocks `admit_candidate`. Both terminal
cases traverse the real admission/enqueue replay through the public
`admit_accepted` path. The integrated/live case reads the existing Authority
receipt, invokes neither Authority integration nor the runtime, releases the
lease, and permits the next FIFO entry to run. The integrated/released case is
read-only and adds no coordinator operation.

Verification:

- Focused `test_driver`: 18 tests passed.
- Complete V12 integration discovery: 381 tests passed, one expected skip.
- `python3 -m py_compile`, `git diff --check`, and an explicit trailing-
  whitespace scan passed for all nine candidate paths.

Final SHA-256 digests:

- `driver.py`: `7abe6fb2776176ff465c1444d9981600bb825b9b864a0bcc4a41d4a6812df14b`
- `integration/__init__.py`: `4916707c9019fab57962aff5629b5ba99fbe8390f003f4960c94b90a9b7980cd`
- `test_driver.py`: `be969c823b78ebba2c22ce9d0656e9cf2c05365052273feff8e1c8ae042df384`
- `execution.py`: `91995b96369f7237dd6e8b67cf8223f3b52baf6b6304c45d53a14e13140ce330`
- `queue.py`: `2e8a153ddcdf15fcd597f51a7c81ce0405ee7b64fad9b2f3b6cf416c40489be7`
- `test_execution.py`: `53c416fa603bd31d1549f8f974dba562bf082c3963866423e87d0b073ea3a398`
- `test_coordinator.py`: `7c7d9b9ada3e8977b35137abee117b42f0b4d09359b9cda50a933a676db27a8c`
- `test_runtime.py`: `925b7dd4ae8eba7d2c375186c74859632276da3f83da3bb6734c3c7c82268c66`
- `test_recovery.py`: `c33cfa13818177afc882dd896d842036010c44656886a73c133687001e08b8fa`

State: admission-replay correction complete; awaiting independent nine-path
candidate review.
