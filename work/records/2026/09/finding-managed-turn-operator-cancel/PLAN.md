# Plan

Current: candidate195504 independently accepted under reviewer claim195517;
prepared working-tree change goes to baton.ops for owner approval. Exact digest,
seven product paths and evidence limits are in review-2026-09-17T15-16-29Z.md.
139/139 deterministic tests pass independently. No further implementation change
is requested. No production deployment or live-provider certification is claimed.

2026-09-17: owner assigned implementation to tuner; canonical ledger owns claim
and route state. FINDING.md contains the accepted outcome.

1. Inspect existing bridge control, turn identity, ACP cancellation and settlement
   paths. Pin the smallest command/continuation contract and exact file ownership.
2. Implement targeted cancel and explicit continuation through the existing
   session-owning bridge. Preserve claim semantics and process cleanup guarantees.
3. Run short deterministic cases first: busy cancellation, idle/repeated/stale
   requests, cancel-vs-completion race, tool-call settlement/timeout, no automatic
   old-turn redispatch, and continuation with revised instructions. Expand only
   for affected integration boundaries; no repeated broad suite sweeps.
4. Document executable operator examples, provide candidate/evidence and pass to
   independent review. Do not deploy or cancel a production turn during this Work.

Likely scope: tools/acp-baton-bridge source/tests/README and a narrowly required
operator control wrapper. Coordinate any shared infra path before editing.
