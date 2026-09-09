# Adopted-column owner precedence misidentifies valid receiving probes

W120785, discovered by baton.tuner under W116975 claim120754 on2026-09-08.
This shared scanner/accounting prerequisite is separately scheduled from the
review_cycles module and retains its own top-level record.

## Observed and confirmed

Canonical evidence lives in
`baton:work/records/2026/08/finding-v12-global-boundary-inventory-debt/findings/finding-review-cycles-inventory/evidence/`:
`census-120754.json`, `labels-120754.py`, `labels-120754.json`, and
`execution-120754.md`. Accepted test baseline is
bf6160f596ad917fdb4296963d2c272adf3f328b2e78e279dc1f1eb4da7bf00c;
review_cycles runtime is774fae6bd09c9dfe9a1f47b6149c9cfbe375d22c6461a95a7aa7d251b7d02da6,
schema56c54054b5170b49a77ef4af0b13dd7f8ff8ee14564785c449e726df48ed7df1.

Two unchanged real public probes, both using the retained empty-string stimulus:

| Entry (adopted) | Actual integrity/schema refusal | Selected inventory label |
| --- | --- | --- |
| checkpoint_of / line_checkpoints.fence | a persisted line checkpoint's fence is durable text | a persisted assignment fence |
| integration_checkpoint / integration_eligibility.verdict_id | persisted integration eligibility's verdict_id is durable text | a checkpoint verdict identity |

Both actual labels match the existing catalog pair. Their full source sites
are prefixed `review_cycles.py:`. The census reports these correct existing
pairs as orphaned and demands later labels instead.

Confirmed source chain: `integration_checkpoint` calls `boundaries.row` with
INTEGRATION_ELIGIBILITY_COLUMNS before forwarding owned verdict_id to
`_verdict_row`. Its column kind is identity and the later helper calls the same
`boundaries.identity` rule. An ordinarily malformed ID cannot pass the first
identical check and fail the second. The catalog's empty-string probe reaches
the real receiving owner; changing only its expected label is false evidence.

`checkpoint_of` likewise adopts LINE_CHECKPOINT_COLUMNS before `_fence`.
The fence column owns durable JSON with required intent/fenced members before
the later helper repeats the outer document shape. A separate JSON-valid
list-intent probe reached the digest guard, not the claimed outer document
label; deeper intent validation and digest prerequisites remain distinct.

In `v12/python/tests/manager/test_boundary_inventory.py`, `_owned_here`
selects exact-subject labels before covering row labels. `layer_labels` and
`EveryProbeProvesItArrived.expected` therefore mask these real row owners.
`_boundary_claims` mirrors the same precedence for occurrence accounting.
The rule is accepted shared scanner behavior, outside W116975 module edits.
No scanner, runtime, catalog, stimulus or existing assertion was changed during
discovery. This is an inventory accounting defect, not evidence of absent
runtime validation.

## Proposed correction boundary; open design decision

Research the smallest shared correction preserving the actual receiving row
owner when a later helper repeats its column rule, while retaining genuine
deeper document/member validation. Assess `_owned_here`, `_boundary_claims`
and their subject/column metadata; a blanket preference for rows could hide
the very nested checks this inventory must discover. Do not apply that shortcut.
Determine whether ownership selection, duplicate-call accounting or both need
change and prepare an exact candidate/affected-pair census for disposition.

Required controls: the two real public probes retain their valid labels;
minimal row-plus-identical-identity and row-plus-repeated-document fragments;
positive nested-member validation beyond the row contract; absent/removed
validator and unrelated later-call negatives; exact call provenance and
independent discovery. Preserve wrong-boundary/category/code checks and all
aggregate empty-set expectations. Never inject corruption after the first
owner merely to satisfy an unreachable later-label expectation.

Research/proposal Work grants no shared scanner or existing-test mutation
authority. Obtain a bounded disposition before implementation, retain an actual
implementation dependency before accepting a proposal-only result, and require
independent acceptance of the correction before module accounting resumes.
The module's four unowned entries and22 orphan-call rows remain its own
revalidation/coverage responsibility; this finding neither exempts nor fixes them.

## Independent research — 2026-09-08, claim120810

**Confirmed:** the bound dossier is readable; tuner response120807 resolves the
earlier missing-record incident. Current test/runtime/schema hashes match the
reported baseline. Source review confirms both repeated rules and their actual
row-first flow. The nullable fence guard and JSON member contract are material;
neither establishes the nested intent's semantics.

**Observed:** one read-only census took2.863s within15s and found exactly two
adopted entries with both exact and covering-row occurrences. Full provenance,
1382 entries and731 occurrence records are retained in evidence/research-120810.json.
The initial module pair comparison omitted delegated labels; its module
residual lists are superseded by evidence/research-120810-corrected-pairs.json,
which reuses the complete retained catalog without rerunning discovery. No
runtime or accepted scanner/test bytes changed.

**Proposed:** PROPOSAL-2026-09-08.md gives the exact single-file authority and
controls for two explicit, source-witnessed duplicate-check relations, preserving
all other selections and actual call obligations. The data-only simulation
changes exactly two pairs (missing7→5; orphan2→0); it is not implementation proof.
Keep nested-member debt separate and visible. Request owner disposition and keep
W120785 open through actual correction and independent acceptance.

## Confirmed implementation allocation — 2026-09-08, owner120878

Slawomir approves PROPOSAL-2026-09-08.md's bounded single-file implementation,
with **Normal priority**, superseding its proposed High priority and the
research-only/unapproved disposition. Execute serially at baton.tune, returning
baton.bug for independent acceptance. All proposal exclusions and additive
controls remain binding, including the cumulative15s focused verification
budget. W120785 stays open and W116975 stays gated until actual implementation
acceptance. The approval does not change any technical acceptance boundary.

## Implementation handback — 2026-09-08, claim120897

The approved two-relation correction is implemented. Exact delegate queries
retain their prior behavior; row selection applies only to the reviewed
adopted entries. Witnesses validate semantic fingerprints before recomputing
call spans, and repeated checks link to the exact claimed row occurrence.
Canonical implementation/verification account:
`evidence/execution-120897.md`. Independent acceptance remains required;
the remaining module and aggregate coverage is not claimed here.

## Independent acceptance — 2026-09-08, claim120976

**Confirmed accepted.** review-2026-09-08T17-02-16Z.md supersedes pending
implementation acceptance. The final candidate passes independent scope and
public-probe checks, with the retained exact census/control evidence reused.
Close W120785 satisfying; W116975 resumes its remaining module scope.
