# Plan

**Status — 2026-08-17:** signed off in
`review-2026-08-17T00-25-04Z.md`. W207 may close satisfying and release its
dependency on W163. A real source-tree `wait timeout=0` returned projection
5.0 with the unchanged W136/W148 typed participant-action shape; independent
review confirmed the exact-major gate, refusal matrix and complete gates.

## Revalidation — 2026-08-17

- `src/codex_baton_bridge.mjs::validateEnvelope()` is the sole product gate:
  it currently requires major 4/minor >=3 before applying the unchanged
  protocol, participant, authority, snapshot, timeout and action checks.
- Update that gate and diagnostic to major 5/minor >=0. Do not accept 4.x in
  the new source contract; the immutable old deployment retains its old
  bridge.
- Change the Node envelope fixture default to 5.0. Pin 5.0 and a later 5.x as
  accepted, and 4.3/another major/missing as refused without forwarding.
- Update every projection-4.3 operator statement in the bridge README. Keep
  the bridge external and read-only; no Baton package/distribution change.
- Focused gate: `cd tools/codex-event-bridge && node --test
  test/codex_baton_bridge.test.mjs`; then its complete `npm test`/`node
  --test`, followed by `just test-v11` and `git diff --check`.

1. Revalidate the exact projection-5 `wait` and participant-action envelope
   against the W136/W148 contract.
2. Change only the standalone Codex bridge's projection gate, fixtures,
   diagnostics and operator documentation; preserve all other refusal checks.
3. Prove projection 5.0 and later compatible 5.x additions are accepted while
   4.x and another major refuse without emitting an event.
4. Run the Node bridge suite plus the complete v11 gate and return for
   independent review before W163 or the next immutable deployment.
