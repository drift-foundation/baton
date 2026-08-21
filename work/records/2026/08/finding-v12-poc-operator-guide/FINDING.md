# Finding: make the v12 proof operable from its own guide

## 2026-08-21 — Observed

The isolated-worker proof now lives as the self-contained `v12/` subtree and
has a detailed architectural README. The guide names the three recipes and the
important security boundaries, but an operator still has to infer the actual
run sequence from implementation files and `poc.json`: which values must be
reviewed first, which paths are intentionally disposable, what success
produces, and how a fail-closed refusal should be investigated.

This is independent documentation and final-polish work. It does not change
the v12 worker contract, the proof implementation, Baton v11, or the active
containment/claim correction.

## 2026-08-21 — Confirmed boundary

- Make `v12/README.md` sufficient for a careful operator to configure and run
  the existing proof without reconstructing the workflow from source.
- Preserve the prototype's disposable/non-product status and every existing
  security qualification. Do not turn a PoC observation into a product claim.
- Explain the configuration values an operator must inspect, the normal
  command sequence, where generated state and evidence appear, and the first
  useful diagnostic locations after refusal.
- Keep host-specific values in the example configuration explicit; document
  them rather than silently generalizing or changing them.
- Documentation and closely related recipe/help-text polish are in scope.
  Manager, protocol, authority, container, and test behavior are not.
- Re-run documentation-adjacent checks that already exist; do not weaken a
  gate or change an assertion to make prose pass.

## Acceptance

1. A new operator can identify prerequisites and configuration edits before
   the first mutation.
2. The guide gives an ordered happy-path invocation and says what artifacts
   prove success.
3. Failure guidance points to existing logs, traces, or commands and retains
   fail-closed semantics.
4. No v11 or v12 application/protocol source is changed.
5. The change is returned for independent review rather than closed by the
   author.
