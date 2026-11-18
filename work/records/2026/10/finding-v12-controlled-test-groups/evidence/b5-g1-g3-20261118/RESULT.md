# B5 first cycle (M385095): G1 nine launch/exchange ids REPAIRED; G3 two recovery ids returned as a decision

K, copilot under owner claim E384905, no claim held. Source: owner commit 2e330649 plus the uncommitted
accepted G6 candidate (attempts.py, stage_execution.py, two tools tests) plus this cycle's three test files;
content digest 797efca0… identical before and after the G1 module run (`source.json`, `source-after.json`).
`tokens.py` is byte-identical to the checkpoint. Before-evidence: `b5-reconciliation-20261118/unresolved-ids.log`.

## G1 — nine ids, all test-side alignments to the accepted /5 wrapper (no product change)

The owner's question answered (TESTED): the `/4`-with-`session` document is the PRODUCT's payload. The
accepted contract is AMENDMENT-376531 ("one current worker-launch/5 wrapper {schema, wire_profile,
payload}; payload preserves the /2-/4 shapes"), implemented at the one authoring point
`launch.launch_document`: when the FILE EXCHANGE is the selected transport the authored document is the `/5`
wrapper and the mode-specific `/2`/`/3`/`/4` document is its payload; a launch naming no transport (the
one-shot integration launch) stays unwrapped. The worker's `baton_worker.launched` opens the wire first
(`_unwrapped`) and answers the validated payload, and REFUSES a bare file-exchange payload ("without the
'baton.worker-launch/5' wrapper … an unwrapped file-exchange launch is not one this worker executes"). The
failing tests predated the wrapper. Nothing was built by a fixture, and no protocol was weakened.

- `test_launch.TheContextLaunchIsClosed` (3): the adopted delivery is asserted as the `/5` wrapper with the
  pinned wire profile; `launched(wrapper)` equals the `/4` payload member for member; `launched(payload)`
  refuses; omission/extra/downgrade mutations are driven INSIDE the payload and, additionally, at the wrapper
  (extra member, missing or foreign `wire_profile`); the wrong-role/uuid/attempt/binding refusals read the
  payload's members.
- `test_execution_limits.TheVersionMovesWithTheMember` (2): with the exchange transport the wrapper is `/5`
  with exactly `WRAPPER_MEMBERS` and the payload is the `/2` or `/3` document (`payload_of`); the one-shot
  `/3` launch without transport is asserted NOT wrapped.
- tools `test_execution_limits` (4): the fresh-process child script called `launch.payload_of` while it had
  imported the module as `launch_owner` (a `NameError` in the test's own child, not in the product); the
  `SimpleNamespace` reader doubles gained what the W363066/W370555 readers now resolve through --
  `_given_for` for the serving reader and `job_task=None` for the observing one -- with the installed
  document as the answer, which is the identical-bytes property the class pins.

## G3 — two ids: specification question, returned without implementing (G3-DECISION.md)

Both expect a same-operation replay of a committed reservation to answer the recorded token after the
generation was REVOKED by a deadline sweep with the engine unavailable ("without revival"); the product
refuses at `journal_launch -> _acting_record -> _owning` while `acquire` replays. A measured reorder
(replay before ownership) made both pass and broke three accepted stopped-settlement FENCE witnesses, so it
was reverted; the packet gives the exact behaviour and three options (recommended: fence refuses first,
revocation replays, new acts still refuse). Revoke-on-unavailable itself is not contested.

## Verification (focused; no group/full/Docker/live)

| run | result | log |
|---|---|---|
| the nine G1 ids, one invocation | 9 OK | g1-nine-ids-after.log |
| tests.manager.test_launch (module) | 37 OK | g1-test-launch-module.log |
| tests.manager.test_launch + test_execution_limits + tests.tools.test_execution_limits (modules) | 207 OK, 95 s | g1-modules.log (identity stable) |
| the two G3 ids, product restored | 2 ERROR, original refusal | g3-two-ids-after-revert.log |
| the two G3 ids under the (reverted) reorder | 2 OK | g3-two-ids-after.log |
| token-related modules under the (reverted) reorder: native_stop_restart, serving_renewal, native_permission, stopped_settlement, stopped_settlement_joined, attempt_failure_cause, authoring_enforcement, maintenance | 3 FAIL (fence witnesses), rest OK | g3-token-modules.log |

## Candidate

`CANDIDATE-SHA256.txt`: tests/manager/test_launch.py, tests/manager/test_execution_limits.py,
tests/tools/test_execution_limits.py. `candidate.diff` against 2e330649 covers those three; the accepted G6
candidate's four files remain beside them unchanged. No product file changed this cycle.

## Leaked fixture roots: attributed, recorded, removed

26 roots created during this cycle's runs (03:26Z token modules; 03:29Z and 03:32Z G1 module runs) were
listed in full (`leaked-roots-before-removal.txt`) and removed (`leaked-roots-removed.txt`); /var/tmp is
back to the 376-entry baseline, listing identical. Families and leak sites for the bounded final cleanup:
`v12-w110774-*` (tests/tools/test_integration_worker.py:73, rmtree over frozen subtrees; imported by
tests/tools/test_execution_limits.py), `v12-foreign-*` and `v12-substituted-*` (tests/manager/test_maintenance.py:3262
and :3305, `mkdtemp` with no cleanup; empty directories). Nothing older was touched.
