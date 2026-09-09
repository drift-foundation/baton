# Consumption-subject inventory coverage

Work W121034, child of W116975. Enriched by baton.tuner, claim121130,
2026-09-08. Accepted reader baseline912cce9a is bound by the sibling reader
review-2026-09-08T17-19-25Z.md; runtime/schema remain read-only.

## Confirmed source and exact additive scope

`review_cycles.consumption_subject` validates attempt_id and generation before
SQL. It selects writer_id from line_writers by that exact attempt/generation
and active state, requires exactly one row, then forwards its writer_id
unchanged to `writer_of`. That operation owns identity and complete-row
adoption. The envelope's rule is cardinality; its projected member's rule
belongs to the delegated identity validator. No runtime validation is missing.

In `v12/python/tests/manager/test_boundary_inventory.py`, add only:

- STATED_OWNERS `(adopted, review_cycles.py:consumption_subject, line_writers)`:
  exact-one active row selected for caller attempt/generation; the sole
  projected identity is forwarded to writer_of. Give this new entry its own
  additive StatedRules witness, overriding only its automatic generic mapping.
- DELEGATED `(adopted, review_cycles.py:consumption_subject, line_writers.writer_id)`
  to `(review_cycles.py:writer_of, caller:writer_id)`.
- Public caller probes for attempt_id / `a runtime attempt identity` using
  SURROGATE and generation1, and generation / `an assignment generation`
  using a valid attempt identity and generation0.
- An actual public adopted-member probe / `a line writer identity`: establish
  a genuine active writer with the existing named lifecycle fixture, change
  only its stored writer_id to empty text, then resolve consumption using the
  unchanged attempt/generation. This lookup does not use writer_id, so it must
  return the malformed member to writer_of's real validator.

These are new owners/probes/witnesses only. Preserve every previous mapping,
probe, guard, assertion and shared scanner node. Do not change existing fixture
or runtime/schema bytes. Helper residuals, nested fence probes and joined
module acceptance remain with their separate Work.

## Independent acceptance boundary

Add focused controls proving source forwarding and cardinality before use,
exact catalog ownership/pairs, genuine positive subject/path/pin, zero-match
refusal for wrong attempt/stale generation/revoked writer before delegation,
and the projected malformed key's exact SQL/validator path. Caller malformed
probes must refuse before SQL; absence must not satisfy their boundary guards.

The schema also has UNIQUE(runtime_attempt_id, assignment_generation), beyond
the per-line active-writer index. Pin that real constraint with an attempted
duplicate on a distinct genuine line, isolating it from the per-line index.
Do not fabricate a multirow result that the real schema excludes.

Reuse accepted scanner/reader results. One focused control run and one census/
preservation audit, cumulative15s; retain elapsed/log output even on failure.
Require exactly two newly owned entries, three added declared pairs (one newly
expected delegated pair and the two existing caller expectations), unchanged
other owners/pairs/residuals and exact preservation of prior AST/runtime.

## New-fixture/stimulus correction — 2026-09-08, claim121130

Initial focused output/candidate are retained in evidence/verification-121130.json
and candidate-121130.py. Three controls passed. Four exposed assumptions in
the new test code: boundaries.generation accepts zero, while create_line and
grant_writer return operation summaries rather than complete adopted rows.

This supersedes generation0 as the proposed malformed stimulus: use existing
SURROGATE, preserving the expected identity and generation labels. After the
new fixture creates its genuine line/grant, use existing line_of/writer_of
to return their complete adopted rows. No existing fixture or production
contract changes. Rerun only the four affected controls, then the still-unrun
census, reusing the three unchanged ownership/source/wrong-boundary passes.

## Candidate ready for independent acceptance — 2026-09-08

The bounded additive candidate and exact verification are recorded once in
`evidence/execution.md`. All seven focused controls pass across the retained
runs, and the census/preservation audit passes within the original budget.
No additional ownership rule, exception, runtime or shared scanner change
was needed. Subsequent helper/nested coverage and parent acceptance remain open.

## Independent acceptance — 2026-09-08, claim121190

**Accepted.** review-2026-09-08T17-30-34Z.md supersedes the pending acceptance
status. Candidatee9257948 matches retained evidence and the approved additive
scope. Release W121039; helper/nested coverage and parent joined acceptance
remain separate obligations.
