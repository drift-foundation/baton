# Progress

No implementation has started. The exact recurrence is recorded for bounded
review; the immediate W85500 recovery remains an explicitly identified
stopgap.

## 2026-09-04T14:23:29Z — `baton.tuner`

Implemented the authorized configuration and release-surface portion. Config
validation now requires a non-self `runtime.actionOwner`; the README, three ACP
lifecycle templates, and two co-deployed examples name the explicit owner
contract. Added direct poke-over-live-claim coverage plus repeated-poke,
restart, canonical-release, and ordinary-resumption coverage without changing
the generic settlement state machine. Added template/example contract checks.

Verification:

- `npm test` under `tools/acp-baton-bridge`: 129 passed.
- `pytest tests/work/test_w459_fresh_contexts.py
  tests/work/test_w163_deploy_bridge.py`: 48 passed, 1 failed. The failure is
  the no-checkout deployed bridge importing absent
  `lib/codex-event-bridge/src/quarantine_store.mjs`.

The failure identifies a packaging path outside the currently enumerated
patch authority. Broad verification and review handoff wait for the recorded
scope decision; no release, proof workaround, or out-of-scope edit was made.

## 2026-09-04T14:36Z — `baton.tuner`

Reclaimed W85873 after Slawomir's bounded packaging ruling. Added only
`tools/codex-event-bridge/src/quarantine_store.mjs` to
`tools/deploy_work.py`'s `SOURCE_SHARED_GATE` and the corresponding installed-
file assertion in `tests/work/test_w163_deploy_bridge.py`. No assembler,
settlement, replay, incident, or store implementation was redesigned.

Verification:

- `pytest tests/work/test_w459_fresh_contexts.py
  tests/work/test_w163_deploy_bridge.py`: 49 passed, including the deployed
  no-checkout bridge and its shipped offline ACP suite.
- `just test-v11`: 3,336 parallel tests passed, then all 54 serial/race tests
  passed; its ACP bridge gate passed all 129 tests.

The packaging gate is cleared. The exact scoped candidate is awaiting
independent review; no release was built and no live service was cut over.

## 2026-09-04T19:24Z — `baton.tuner` — review response

Review `review-2026-09-04T19-20-16Z.md` accepted the existing 11-path bytes and
their three changed test paths, but found an unrecorded release dependency.
Read-only revalidation confirms that the active `pc-code-acp` input and its
canonical successor both omit `runtime.actionOwner`, and active `infra.json`
starts that service beside `claude-acp` in the ordinary lifecycle set. The new
bridge therefore refuses `pc.code` before its lease and first wait.

No identity was inferred and no deployment-owned or live configuration was
edited. The dependency is now recorded in FINDING and PLAN. W85873 waits for
`baton.ops` to name the authorized non-self owner and decide whether exact
scope expands to the canonical `pc.code` successor plus its verification or a
separate blocking Work owns that migration. Immutable proposal packaging,
release construction, and cutover remain pending that decision.

## 2026-09-04T19:36Z — `baton.tuner` — `pc.code` review correction

Reclaimed W85873 after the operator supplied the explicit owner and bounded
scope ruling. Added only `runtime.actionOwner: pc.slaw` to the canonical
`pc.code` successor template and an exact assertion to its existing Node
configuration preflight. The preflight exercises the template through the
candidate ACP config loader, so it proves the required non-self owner survives
validation. The active deployment-owned template was not edited, no owner was
inferred, and no settlement or lifecycle behavior changed.

Verification:

- `node verify.mjs` in the successor directory passed, including exact
  `pc.code` identity, `impl` role, and `pc.slaw` recovery owner.
- `npm test` under `tools/acp-baton-bridge`: 129 passed.
- `pytest tests/work/test_w459_fresh_contexts.py
  tests/work/test_w163_deploy_bridge.py`: 49 passed.
- `just test-v11`: 3,336 parallel tests passed, all 54 serial/race tests
  passed, and its ACP bridge gate passed all 129 tests.
- Focused source `git diff --check` passed across all 13 candidate paths.

The older Python successor verifier was run read-only and stops at its
pre-existing equality check between staged and currently deployed `control`
objects, before ACP-specific checks. It is unchanged and excluded from this
proposal; its live-topology drift is not hidden by weakening that guard. The
passing Node verifier is the configuration preflight authorized by this
correction.

The replacement proposal freezes 13 production/existing-test paths: the 11
paths already reviewed on 2026-09-04 plus the canonical `pc.code` successor
template and `verify.mjs`. Its existing test/verifier paths are exactly
`tools/acp-baton-bridge/test/acp_baton_bridge.test.mjs`,
`tests/work/test_w459_fresh_contexts.py`,
`tests/work/test_w163_deploy_bridge.py`, and the successor `verify.mjs`.
Nothing is deleted. The planned immutable locator is
`/tmp/w85873-proposal-2026-09-04T19-36-30Z`; release construction and live
cutover remain outside this proposal handoff.
