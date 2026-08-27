# Plan

1. [done 2026-08-27] Confirm a one-snapshot, deterministic textual Work-graph
   export, with Graphviz DOT as the first format and no image rendering inside
   Baton.
2. [done reviewer 2026-08-27] Revalidate the existing `tree`, `links`,
   dependency neighbourhood, and relation projections. Specify the CLI
   grammar, graph scope, terminal-endpoint rule, export bounds, structured
   projection, exact deterministic DOT grammar, and refusal behavior. See
   `FINDING.md` and `evidence/design-baseline-2026-08-27.md`.
3. [done approver 2026-08-27] Confirmed the verb/formats, all-team
   `status=open` default, filtered endpoint closure,
   complete-without-pagination policy, public structured JSON/projection 12.6,
   and non-strict DOT v1/title encoding. `status=all` requires the explicit
   `changed-from`/`changed-until` half-open UTC-normalized range recorded in
   `FINDING.md`; the pair filters canonical `last_changed_at` and is optional
   for the other status scopes.
4. [next implementation] Add the canonical one-snapshot projection, pure DOT
   renderer, CLI surface, adversarial relationship/escaping/determinism tests,
   and user documentation without adding a Graphviz runtime dependency.
5. [then review] Independently verify graph completeness, typed direction,
   byte determinism, snapshot identity, hostile labels, and absence of image
   production or raw-store access.

## Implementation order after approval

1. Add `projection.work_graph` with fixed structured nodes/edges, canonical
   ordering, filtered incident-endpoint context, complete reads and one sampled
   `snapshot_seq` inside `_read_snapshot`.
2. Add pure `dot.render_work_graph_dot` over an already-built envelope. Buffer
   and validate all UTF-8 text before output; use a non-strict digraph and
   semantics-bearing `baton_*`/label attributes.
3. Add `work-graph format=json|dot status=all|open|closed [team=]
   [changed-from= changed-until=]`; keep JSON and `status=open` as defaults,
   require both time bounds for `status=all`, and make DOT the explicit
   raw-output branch. Bump projection 12.6.
4. Add the twelve acceptance groups named in `FINDING.md`, including more than
   existing UI/page caps, same-pair parallel relations, interleaved writes,
   hostile escString titles and authority/WAL read purity.
5. Update CLI help, effective operating guide and Work UI/API documentation;
   state that Baton emits DOT only and never invokes or bundles Graphviz.
6. Return for independent review before release packaging.

## 2026-08-27 — implementation

- [done] 4. `projection.work_graph`, the pure `dot.render_work_graph_dot`, the
  `work-graph` CLI surface with JSON default and raw `format=dot`, projection
  12.6, the twelve acceptance groups (57 cases) and the user documentation.
  No Graphviz runtime dependency was added.
- [next, reviewer] 5. Independently verify graph completeness, typed direction,
  byte determinism, snapshot identity, hostile labels, and the absence of image
  production or raw-store access. `PROGRESS.md` names three tree-driven
  corrections and two clarifications inside the ruling that want a second
  opinion.
- [for review] `FINDING.md` assumes any two of the four relation families may
  coexist on one pair; the authority in fact reaches only dependency +
  duplicate. Recorded rather than worked around, and the case uses the reachable
  pair.
- [for review] Six existing suites' `PROJECTION_VERSION` pins moved 12.5 -> 12.6
  as the mechanical consequence of the approved bump.

## 2026-08-27 — first independent review

- [accepted] The one-snapshot projection shape, four semantic directions,
  deterministic ordering, incident-endpoint closure, complete reads,
  non-`strict` DOT, hostile-title visibility/base64, raw-output buffering,
  range metadata, projection 12.6, documentation, and the mechanical version
  pin updates.
- [accepted clarification] Current authority rules reach dependency+duplicate
  as the parallel same-pair case, not arbitrary pairs of the four families.
  This still proves why DOT v1 must remain non-`strict`; the broader assumption
  in the original rationale is explicitly superseded in `FINDING.md`.
- [changes requested] Enforce the approved timezone-bearing RFC 3339 grammar
  before parsing/UTC normalization. Reject the three non-RFC ISO spellings in
  the additive reviewer case with empty DOT stdout.
- [changes requested] Make `dot.render_work_graph_dot` independently validate
  endpoint presence, duplicate typed edges, and the fixed relation/predicate
  pairing before it composes the document. Projection validation alone does
  not protect another structured renderer caller.
- [changes requested] Emit both `baton_scope=selected|context` and
  `baton_selected=true|false`; the readable role and the fixed structured
  member are complementary approved attributes.
- [changes requested, low risk] Include store-dependent team-scope validation
  in the same `_read_snapshot` as graph rows and `snapshot_seq`.
- [then review] Rerun the focused export suite, mutation measurement, adjacent
  boundary/dependency cases, full v11 parallel and serial gates, ACP bridge,
  and `git diff --check` before independent signoff.

## 2026-08-27 — second independent review

- [accepted] All four first-review corrections: strict RFC 3339 shape and
  case handling, shared renderer graph validation (including duplicate nodes),
  `baton_selected` beside readable scope, and snapshotted configured-team
  validation. The three reviewer regressions are unchanged and green.
- [changes requested] Preserve arbitrary RFC 3339 fractional-second precision
  across UTC normalization. Do not collapse distinct fractions beyond six
  digits through `datetime`'s microsecond field; canonical equivalent
  spellings without losing an instant.
- [changes requested] Own every fixed structured node/edge member's type and
  nullability before graph semantics or rendering. In particular,
  `selected` is exactly bool and `title` is exactly text; malformed renderer
  input refuses with `WorkError` naming the member.
- [then review] Rerun the now 66 focused cases, updated mutation measurement,
  adjacent and full gates, ACP bridge, and `git diff --check`.

## 2026-08-27 — first review answered

- [done] All four review findings: an explicit RFC 3339 grammar before parsing
  (with case normalization, since §5.6 makes `T`/`Z` case-insensitive and
  `fromisoformat` rejects a lower-case `z`); the renderer running the SAME
  validator as the projection rather than a second copy of its rules;
  `baton_selected` beside `baton_scope`; and the configured-team read moved
  inside the export's own snapshot.
- [next, reviewer] Second review pass. The three reviewer regressions are
  unmodified and pass; four cases were added for these fixes.

## 2026-08-27 — second review answered

- [done] Both findings: the RFC 3339 fraction is carried independently of
  `datetime` so arbitrary precision survives, with an explicit ordering key
  because variable-length fractions cannot be compared as text; and
  `validate_work_graph` now owns every fixed member's type and nullable domain
  for both boundaries, with the renderer's own presence checks removed rather
  than kept beside it.
- [next, reviewer] Third review pass. Five reviewer regressions across two
  passes are unmodified and pass; three cases were added this round.

## 2026-08-27 — third independent review

- [accepted] Both second-review corrections: arbitrary RFC 3339 fraction
  preservation/canonical ordering and exact fixed-member type/nullability
  ownership. The five earlier reviewer regressions remain green.
- [changes requested] Make the shared validator own the closed `status`,
  `phase`, and `outcome` vocabularies before DOT rendering. A string's Python
  type alone does not make it a valid node state.
- [then review] Rerun the now 72 focused cases, updated mutation measurement,
  adjacent and full gates, ACP bridge, and `git diff --check`.

## 2026-08-27 — third review answered

- [done] Closed-vocabulary ownership in the shared validator, covering all SIX
  members that carry a domain rather than the three the review named, reusing
  the authority's own tuples and asserting that reuse by identity.
- [done] A boundary rule holding the read side's new import of `transitions` to
  closed vocabulary: names only, text or tuples of text, never the module and
  never a callable.
- [next, reviewer] Fourth review pass. Six reviewer regressions across three
  passes are unmodified and pass; two cases were added this round.

## 2026-08-27 — fourth independent review

- [accepted] Closed-vocabulary ownership for all six fixed-domain node
  members, including the three requested in the third review; canonical value
  reuse; and the bounded read-side vocabulary import.
- [changes requested] Validate status/phase/outcome as one paired node state,
  and require `via_obligation=null` on every non-dependency edge. Correct the
  older nullability case that currently asserts an impossible open/null-phase
  combination rather than the two valid paired states.
- [changes requested] Share a whole-result validator between projection and
  renderer that owns fixed scope semantics and proves selected/context/node/
  edge counts from the arrays. Keep configured-team existence in the
  projection's read snapshot.
- [then review] Rerun the focused suite, updated mutation measurement,
  boundaries, adjacent and full gates, ACP bridge, and `git diff --check`.

## 2026-08-27 — fourth review answered

- [done] Cross-member invariants in the shared validator: status/phase/outcome
  as ONE node state, and `via_obligation` as dependency-only provenance.
- [done] The validator owns the WHOLE result — the scope document and all four
  counts proved from the arrays — and the projection runs it on its own output
  before answering.
- [done] The interval rule deduplicated: `_export_scope` parses operands and
  delegates every result rule to `_export_scope_document`.
- [done] My own case that asserted `phase=null` on an open node, which the
  confirmed schema forbids, corrected to the two valid paired states.
- [next, reviewer] Fifth review pass. Fifteen reviewer regressions across four
  passes are unmodified and pass.

## 2026-08-27 — fifth independent review

- [accepted] Coupled node/edge state validation, whole-result scope/count
  validation, projection self-validation, interval-rule deduplication, and
  correction of the previously contradictory nullability case.
- [changes requested] Require each non-null bound in a structured scope to be
  its canonical UTC-normalized `_export_instant` value before DOT rendering.
  Keep the public operand path accepting and normalizing every legal RFC 3339
  spelling; enforce the result invariant symmetrically on both bounds.
- [then review] Rerun the focused suite and proportional gates, including
  mutation measurement and `git diff --check`.

## 2026-08-27 — fifth review answered

- [done] A structured scope bound must EQUAL its canonicalization, both bounds,
  so one normalized scope has one document. The operand path still accepts every
  legal RFC 3339 spelling, with cases for both halves and for the end-to-end
  promise.
- [done] The snapshot-sequence sample is now observed deterministically at the
  connection as well as end to end; its mutation detection had been racy and
  was silently passing.
- [next, reviewer] Sixth review pass.

## 2026-08-27 — sixth independent review

- [done] Both structured bounds require their canonical UTC-normalized value;
  public operands still accept and normalize every legal tested RFC 3339
  spelling, and equivalent scopes produce byte-identical DOT.
- [done] Independent focused and boundary verification: 95 passed and 5
  passed; `git diff --check` clean. The implementer's full parallel/serial,
  ACP, and mutation gates are recorded in the final review.
- [done, signed off] No review findings remain. W24755 may close satisfying;
  see `review-2026-08-27T17-21-50Z.md`.
