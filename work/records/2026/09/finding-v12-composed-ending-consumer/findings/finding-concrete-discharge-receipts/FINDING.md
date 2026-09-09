# Concrete quiescence discharge receipts

W124782, parent W122060, follow-up to closed W119548. Created124782 during
reviewer claim124772. Owner124767 approves item1 of
`baton:work/records/2026/09/finding-v12-composed-ending-consumer/PROVIDER-ALLOCATION-PROPOSAL-2026-09-09.md`.
Read that complete item and the parent `review-2026-09-09T03-44-04Z.md`.

**Confirmed:** concrete Authority returns evidence kind `runtime-absent` after
committing gate satisfaction. Manager intake expects `runtime-quiescence` and
refuses before committing its receipt. Parent evidence/review-124645-probe.py
and JSON capture the absent receipt and downstream consumer bypass.

**Approved ownership:** baton.tune, High, returning baton.bug. Exactly
`v12/python/src/baton_v12/worker_manager/intake.py` and
`v12/python/tests/manager/test_intake.py`. Bounded existing fake-response and
expectation corrections are authorized only where gate-discharge cases encode
the wrong returned kind. Preserve all unrelated assertions. No Authority,
schema, registry, consumer or other provider edits. Ownership remains reserved
through independent acceptance, disjoint from W124784's concurrent impl paths.

**Acceptance:** align receipt validation with the concrete Authority contract;
preserve exact original assignment, gate, runtime and operation correlation.
Prove concrete-session local commit and remote-success/local-loss replay after
later Work movement, plus wrong-kind/generation/authority and unreachable
runtime refusals. Do not weaken absence proof or use current gate absence as
proof of a committed local receipt. Consumer bypass correction remains W122060.
No capability expansion. Cumulative20s focused verification, no inventory run.

## 2026-09-09 — implementation revalidation, baton.tuner claim124831

Confirmed against current source: Authority `Core.satisfy_gate` returns the
validated evidence kind. Both intake's fresh-answer check and its persisted
receipt reader incorrectly require the gate kind. Correct both to
`RUNTIME_ABSENT`; retain the separately derived generation-bound gate token and
all assignment/runtime/operation correlations. The scoped fake correction is
local to the discharge test class; the shared fake's owning file is excluded.
Base bytes and modes are retained in `evidence/implementation-124831/base.json`.

## Independent acceptance — 2026-09-09, claim125006

Exact candidate accepted in `review-2026-09-09T04-30-45Z.md`. The ordinary
receipt and committed-effect replay correction remains necessary under the
campaign04:13Z/M124896 narrowed recovery ruling. No stronger intermediate
same-attempt proof follows from retaining the provider's useful replay controls.
