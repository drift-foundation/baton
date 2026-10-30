# B3 — re-baseline and first two slices (2026-10-30)

Author: K under owner claim E384905; HEAD `84f66f43`. Scope: C5 (next-run flow)
and C7 (authoring lifecycle, credentials doubles, runtime lane, reconciliation
worker) per PLAN, in the recorded non-overlap scope. No product change. Files
and digests: CANDIDATE-SHA256.txt. No full suite, engine, live model, Git
mutation or other agents.

## Re-baseline at the current tree (c5-rebaseline.log, c7-rebaseline.log)

C5: 48 → 3 failures since B0 (the CLI drift is gone at HEAD); the three left
are in `test_next_run_flow`. C7: 34 (27 failures, 7 errors) over six modules.

## Slice 1 — test doubles behind the product's keywords (slice1-doubles.log)

- `test_credentials`: four `observe` lambdas take `seconds=None` (the adapter's
  `_removed` calls `observe(runtime_id, seconds=...)`).
- `test_authoring_enforcement`: the `_adapter` double takes keyword operands.
  THIS ALSO CLEARED the seven cancellation failures (`'running' != 'quiescent'`,
  no Authority fence recorded): the TypeError inside the cancellation path was
  being recorded as a fault, so nothing was product behaviour.
  Result: 144 tests OK across both modules (2.4 s).

## Slice 2 — fixture drift against moved product contracts

- `test_authoring_manager_guard` and `shutdown_fixture` imported the historical
  proof's `baseline.py` from its dossier and patched THAT module; the controller
  imports `tools.authoring_baseline`, so every patch missed and the real
  `held_packet` refused the fixture packet. Both now patch the module the
  controller imports. Guard: 7 OK (slice2-guard.log). The shutdown fixture also
  pins `tools/authoring_shutdown.py`, which `verify_controller` requires.
  Shutdown matrix: 11 → 3 failing modes (slice2-shutdown.log).
- `test_runtime_lane`: two assertions of a `complete` cleanup ending encoded
  superseded automatic removal; the accepted execution-only rule (W285465
  review 2026-09-28, `intake._settled_ending`: no directory custody taken →
  `retained`) is what the Custodian double's answer settles. Aligned, with the
  lane release still asserted. 50 OK.
- `test_reconciliation_worker`: two outer `assertRaises(ContractRefusal)`
  encoded a refusal the product replaced (ffc8a19b, `_identify`): a running
  observation after a cancellation is recorded as `stopping` with an
  inconclusive note; the cancellation stands. The tests now assert that
  recorded state; the journal-only judgment they are about is unchanged. 26 OK.
- CONSUMED_INPUTS consumer note for the dossier `baseline.py` corrected (only
  `test_authoring_enforcement`'s child still imports it); sweep/identity 88 OK.

## Open after these slices

| cluster | remaining | finding | classification |
|---|---|---|---|
| C5 | 3 (`test_next_run_flow`) | the flow's serving loop fails with `ProfileRefusal: Git line materialization failed: fatal: could not open '/dev/null' ... Permission denied` inside the product's confined git run; this sandbox opens `/dev/null` and clones fine directly | likely an interaction between the flow's confinement and this session's tool sandbox; an unsandboxed run was refused by the session policy. NEEDS a run outside this sandbox (reviewer/owner) before classifying as product |
| C7 shutdown matrix | 3 modes (`blocked_sweep`, `absent_cleanup`: `report['enforcement']['attempts'][*]['token']` is None; `unknown`: no row with a revoked, unreturned token) | enforcement report rows no longer carry the token settlement the test expects | product-vs-expectation (token lifecycle under shutdown; commits 30245386/8876bf95); needs reading before any change |

C7 total after slices: 34 → 3. Measured: slice runs 0.1–35 s each; the shutdown
matrix is the long one (35 s, eleven real controller processes).

## Slice 3 — C5 root cause and fix (after review 2026-10-30T09:29:47Z)

The owner's and the reviewer's outside-sandbox reproductions settled that the
tool sandbox was not the cause. Diagnosis by reading the LAST run of each
failing test rather than the first (the `denied` run whose `/dev/null` text I
had quoted is the fixture's own scripted W339626 denial and is EXPECTED to be
refused): the real runs end `exceptional`, "froze no result at all", and the
flow trace ends after `docker start` with the fixture worker's thread dying
(`worker-error`, previously truncated in the log):

    KeyError: 'session'   at next_run_flow_fixture.py run_worker

A trace record added before that line (`worker-launch`) shows the launch
document the manager now delivers is `baton.worker-launch/5` with members
`schema`, `wire_profile`, `payload` -- a WIRE launch. The fixture read the file
with `json.loads` and indexed `['session']` as if it were the unwrapped
document, which is how the real worker read it before the wrapper existed.
Fix: the fixture reads and unwraps the launch the way the real entry does,
`baton_worker.launched(baton_worker.read_launch(place), place)`, and keeps the
`worker-launch` trace record. Nothing in product or confinement changed; the
null-device rule was never involved (c5-diagnostic.log holds the diagnosis
run; slice3-next-run-flow.log the fix: 3 OK, 25.5 s). My earlier classification
in B3-SLICES.md ("likely the sandbox") was wrong and is superseded by this.

## Slice 4 — C7's three shutdown-matrix modes (after review 2026-10-30T16:20:31Z)

Recorded in full in `evidence/c7-2026-10-30/C7-SETTLEMENT.md`. Short form:
the "three modes" were the visible part of a vacuous matrix. Since 30245386
the enforcement controller composes a permission envelope for every start and
refused the fixture's 20 s provider turn inside a 4 s window, so EVERY mode's
attempt was `not-started` with no token and the eight "passing" modes measured
nothing. Fixture fitted to the envelope (Job limits 2 s + 1 s, packet turn 2 s,
diagnostic bounds 10/4 s, no injected token duration); the three modes'
settlement assertions retargeted from the injected-2 s-token expiry reclaim to
the controller's accepted `stop_at` contract (production cancellation stops
the exact runtime; the token stays held, neither returned nor revoked, for the
stopped-settlement owner; an unaskable engine preserves fence and hold with the
fault carried), citing `held_before_expiry` and its tests. Matrix 4 OK/60.2 s
(eleven modes, real runtimes); six C7 modules 231 OK/75.4 s. C7: 34 → 0.
