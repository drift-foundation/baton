# Colliding-lane returned-key inventory stimulus

Work W119374, child of W116972. Created 2026-09-08 by baton.tuner under
claim119365, following the independent module-scope review at
../../../finding-module-scope-review/review-2026-09-08T06-42-22Z.md.

## Confirmed receiver and exact change

The existing `EveryProbeProvesItArrived.spoiling_colliding_lane` in
`v12/python/tests/manager/test_boundary_inventory.py` inserts the derived
lane key, then runs `UPDATE runtime_lanes SET lane_id = ?` with the malformed
identity before calling `request_runtime_start`. In
`v12/python/src/baton_v12/worker_manager/lanes.py:_occupy_lane`, an insertion
collision is followed by `SELECT * FROM runtime_lanes WHERE lane_id = ?`.
Changing the stored key prevents this exact lookup from returning the row;
the retained failure reports an ordinary unknown holder instead of adoption.
`_adopted` owns the returned row through `boundaries.row` and the derived-key
relation check. Runtime source is read-only.

The owner-approved lanes stimulus scope and independent plan assessment permit
this exact existing-case correction after pinning it here: for `lane_id` only,
keep the valid derived key in storage and corrupt that column in the returned
collision row, immediately before the real `_adopted` validator. Preserve the
entry `(adopted, lanes.py:_occupy_lane, runtime_lanes.lane_id)`, expected label
`a persisted runtime lane`, corruption value, category/code checks and
wrong-boundary guard. All other column update stimuli remain as written.
Use a scoped row factory recognizing the complete runtime-lane column set;
restore the exact original factory in `finally`. Controls must prove that the
exact collision lookup returned that row, rather than merely seeing the label
from another reader.

## Acceptance and ownership

Own only this fixture branch, its explanatory text, additive controls in the
same test file and this dossier. Prove valid collision-row adoption with the
ordinary contention refusal, malformed returned-key `integrity/schema`
refusal at the named boundary, wrong/earlier-refusal rejection and factory
restoration. Preserve all scanner/catalog/aggregate assertions and runtime.
Retain focused and bounded lanes-probe evidence for independent review.

The parent retains the seven unowned entries, four orphan calls and joined
module coverage. This independently acceptable fixture does not discharge
those inventory results. Serial shared-file ownership lasts through acceptance.

## 2026-09-08 — implementation result, baton.tuner claim119384

Candidate `162f527e3476dcffcc937996df6c36d2d26505dfd7ea156eee6657e7433b30d5`
corrects the exact returned-key fixture. Six focused controls and all 17 lane
probes pass. The query trace and observing original factory prove that exactly
one complete lane row arrived from the collision-key SELECT, with a valid
stored identity and the current attempt as holder. The real validator rejects
the subsequently malformed identity; restoring the factory exposes a row that
the same real validator accepts. Valid returned-key control instead yields
ordinary contention with the exact real holder/reason. The existing guard
rejects both that contention and a real earlier absent-attempt precondition.

`evidence/audit.json` binds the base and candidate and verifies that all other
AST content, runtime and schema are unchanged. `evidence/candidate.patch`
contains only the fixture branch and additive six-control class. This result
awaits independent acceptance, with module inventory coverage retained above.

## 2026-09-08 — independent fixture acceptance, baton.codex claim119445

**Confirmed:** review-2026-09-08T13-26-16Z.md accepts the exact returned-key correction
and its controls at candidate162f527e. This explicitly supersedes the pending
acceptance status above. Runtime/schema, all other AST content and aggregate
expectations are unchanged. Parent inventory/coverage remains a separate result.
