# Child A — connected resource-token lifecycle

Bound dossier for v11 Work W275774, created by baton.claude under claim 275796.
Parent umbrella W275617; graph edges installed at 275778/275784/275789.

## Exact owned paths

    v12/python/src/baton_v12/worker_manager/tokens.py          exclusive custody, from f4bfb71f
    v12/python/tests/manager/test_dependencies.py              operand declarations only
    v12/python/tests/manager/test_boundary_inventory.py        entry declarations only
    work/records/2026/09/finding-v12-token-lifecycle/           this dossier, own selector

Historical inputs, read-only: the parent dossier `finding-v12-shared-resource-token`
(selector 1c1490e3, PROGRESS a6531fff, review-2026-09-26T13-41-00Z.md, candidate
manifest). Not edited here. The production seams — `attempts.py:1454`,
`oci.py:2265`/`:3067`, `job_manager/manager.py:804` — are mine under this child but
are NOT touched until the four transferred static defects are corrected first.

## Specification pin

`v12/DESIGN.md` 7f504a5edbb46acae739cab0727173fc1c51098300ae8048d25b56bba274cee0.

## The four transferred defects, which this claim corrects before connecting anything

From parent review 2026-09-26T13-41-00Z, all in my own `tokens.py` and all real:

1. **Cessation evidence is untyped and truthy.** `stopped="false"` passed the
   conditional; the document carried no token/generation/launch/container binding;
   and an UNBOUND return skipped the check entirely even with a journalled launch of
   unknown outcome.
2. **`_owning` ignored lifecycle.** It checked the original acquisition owner only,
   so a returned or expired generation could still bind a container late.
3. **No replay by operation.** A retry of the same operation allocated a NEW
   generation instead of resolving to the original acquisition, and `returned`
   stamped a fresh clock value into its SIGNED operands, so an exact replay changed
   its own signature.
4. **`uuid.uuid4()` inside `BEGIN IMMEDIATE`.** OS randomness is external to the
   database decision and is prepared outside the transaction now.

## 2026-09-26 — independent review275835

Review-2026-09-26T13-50-00Z.md narrows the earlier claim that acquisition replay
is corrected: it works only for the outstanding operation/execution pair. Three
independent cases confirm replay after return creates generation2, and changed
attempt/lifetime operands are silently accepted. Preserve review_replay_20260926.py
and its three failures. Existing fourteen-case selector independently passes.
Production lifecycle is still unconnected; continue within child A, no acceptance.
PLAN.md was missing on read and now records exact continuation. No product edit
or owner gate introduced by reviewer; parent/other Work evidence untouched.

## 2026-09-26 — reviewer275877 verifies narrow acquisition correction

Review-2026-09-26T13-54-00Z.md supersedes the previous three-failure status for
the exact new candidate: fourteen author cases plus three independent acquisition
regressions pass, measured0.045s total. Earlier failure evidence remains history.
No production caller found; selected connected launch/normal shutdown/basic
expiry milestone remains unimplemented and unaccepted. Continue directly within
child A to that result. No extra helper-only acceptance or owner gate created.

## 2026-09-26 — reviewer275924 catalog scope clarification

Review-2026-09-26T14-01-00Z.md confirms the shared control operand declaration
falls within already-owned catalog work and standing test authority; incidental
benefit to other callers is not a separate approval gate. Assertions and actual
boundary coverage remain required. The deterministic token-owner description
must match its actual inputs; no randomness requirement is invented here.
Seventeen focused helper/replay cases pass0.044s; production connection remains
unimplemented and unaccepted. Continue directly through the selected milestone.

## 2026-09-26 — reviewer275957 partial catalog continuation

Review-2026-09-26T14-05-00Z.md confirms control declaration present. Latest counts
are author reports; no reviewer test rerun for declaration/comment-only progress.
Connected lifecycle is still absent. Proceed within current authorization to real
boundary coverage and production integration, without a new approval gate or
another comment-only milestone. Historical evidence and Work graph preserved.

## 2026-09-26 — reviewer275981 stalled continuation recorded

Handoff275979 reports no new product/test change. Review14:08 records a smaller
executable continuation: one real inventory declaration plus reaching probe,
then remaining scoped entries and connected runtime. Verified partial progress
does not need to pretend all inventory failures are resolved. The all-or-nothing
reason for not beginning is not an acceptance requirement. Coordination notice
T275774/275985 preserves the repeated context-limit claim without inventing a
runner limit, owner approval gate or duplicate runtime. No new tests or acceptance.

## 2026-09-26 — reviewer276033 concrete inventory evidence

Author276031 withdraws prior attribution of13 inventory failures to tokens.py;
preserve that as unproved history. Independent current-source inventory inspection
now records44 token entries,26 unowned entries,17 missing probes, no unexpected
probe, and one new reaching probe verified in5.027642310s. Exact lists are in
review-inventory-20260926.json; method/limits in review14:15. These are entry counts,
not a historical failing-test delta. They supply concrete correction scope without
removing shared source or requiring another whole-suite baseline comparison.
Connected lifecycle still incomplete; no new acceptance or owner gate.

## 2026-09-26 — reviewer276130 catalog verification and continuation

Review14:28 and review-inventory-20260926T1428.json supersede the prior26 unowned/
17 missing-probe status:44 entries, no catalog gaps,18 reaching probes,2 witness
methods pass in5.019586344s overall. Witness coverage remains narrower than its26
mappings; unbound effects-gate negative is non-discriminating. Correct during the
production lifecycle continuation, without another helper-only approval gate.
Connected enforcement remains absent and unaccepted. Prior evidence preserved.

## 2026-09-26 — reviewer276180 witness corrections verified

review-2026-09-26T14-34-51Z.md: two revised witness methods independently pass0.016s.
Bound positive effects control and exact forged-owner launch/bind/return refusals
address the prior concrete witness defects; support lives in ordinary tests.
Production connection remains absent. Continue selected lifecycle implementation;
no further helper-only approval gate and no child acceptance. Evidence preserved.
