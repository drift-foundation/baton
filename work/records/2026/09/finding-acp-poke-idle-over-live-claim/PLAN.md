# Plan

1. [done] Record the W85500 claim/runtime contradiction, the completed poke
   turn, absence of an incident, and suppressed Work redelivery.
2. [done research 2026-09-04] Trace post-turn settlement and runtime
   publication for a non-Work ACP delivery while the participant already holds
   a claim. The live service runs immutable release/commit `8af006f`, which
   predates W55705 and publishes `idle` directly; current source already
   settles every action kind through `AcpSettlement` and passes all 127 ACP
   tests.
3. [implemented; focused ACP verification green 2026-09-04] Preserve the existing generic settlement
   state machine. Make the accepted required/non-self `runtime.actionOwner`
   contract consistent in config validation, ACP documentation, all shipped
   ACP templates/examples, and their deployment contract tests. Do not infer
   an owner or introduce poke-specific workflow authority.
4. [done; ACP suite and full v11 gate green 2026-09-04] Add the exact integration regression in which the delivered
   action is a poke and the independent post-turn canonical read still names a
   claimed Work. Assert `failed` with exact Work/episode, one durable `held`
   fence and incident, no `idle`, no automatic replay/release/acceptance, then
   cover repeated pokes, restart, eventual canonical release and ordinary poke
   delivery. Run the ACP suite, focused deployment/template tests, the
   no-checkout deployed suite, and `just test-v11`.
4a. [done; release-completeness gate green 2026-09-04] The no-checkout gate
   proves the release assembler omits the shared `quarantine_store.mjs`
   imported by the already-reviewed settlement module. Add only that shared
   file to `tools/deploy_work.py`'s `SOURCE_SHARED_GATE` and assert the
   installed file in `tests/work/test_w163_deploy_bridge.py`. Do not redesign
   the assembler, broaden the packaging audit, or inline or duplicate the
   accepted store.
5. [done; replacement proposal ready for review 2026-09-04] Independent working-tree
   review confirmed the 11-path implementation but found the co-deployed
   `pc.code` ACP input and its canonical successor lack the required external
   `runtime.actionOwner`. Use the accepted `pc.slaw` recovery participant and
   extend exact scope only to the canonical successor plus existing
   deployment/configuration verification. The successor now names `pc.slaw`
   and its Node preflight validates that exact owner through the candidate ACP
   loader. Treat the active deployed template as a later cutover target, not
   proposal source. Then bind the candidate digest and exact production/existing-test paths; preserve W55705's
   spent/unspent Work-wake distinction and incident coalescing.
6. [pending integration and release] Import only the reviewed candidate, obtain
   Slawomir's Git approval, and build a new immutable v11 release. Prove its
   packaged bridge includes `acp_settlement.mjs`, carries usable explicit-owner
   templates/examples, and passes its shipped ACP suite without checkout,
   npm, or network.
7. [pending operational cutover after W85500 claim settlement] Do not terminate
   the live ACP turn or infer W85500's outcome. Once its exact claim is
   canonically settled and every co-deployed ACP input passes the new bridge's
   owner validation, render `runtime.actionOwner` to each authorized recovery
   participant, cut the ACP services over through the lifecycle controller,
   and verify executable provenance, action owners, runtime state, settlement
   marker locations, and incident delivery before closing W85873.
