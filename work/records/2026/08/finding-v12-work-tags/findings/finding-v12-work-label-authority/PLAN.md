# Plan

1. Re-read the parent decision record and revalidate its approved contract against the current v12 authority.
2. Wait for W16821, then consume only its canonical principal/scope API for `manage-work-labels` authorization.
3. Resolve and document the schema/versioning or rebuild boundary.
4. Implement normalized live labels, append-only mutation evidence, create/add/remove transitions, exact replay, and `changed:false` convergence.
5. Add deterministic projections and reusable all-of/none-of authority predicates without scheduler semantics.
6. Add the authority, authorization, terminal, replay, race, cardinality, and compatibility regressions enumerated in `FINDING.md`.
7. Record implementation state in implementer-owned `PROGRESS.md` and route for independent review.

## 2026-08-28 — implemented

1. [done] Parent contract revalidated against the delivered tree.
2. [done] Consumes W16821's seam only: `authorize`/`_require_capability` with
   the Work's own effective scope, and ONE decision shape joined from
   `authorization_decision` rather than a second spelling of the evidence.
3. [done] Schema disposition DERIVED, as the record requires: schema 3 as a
   clean initialization boundary under approver ruling M33752 — a version bump,
   not a migration.
4. [done] `labels.py` grammar, the live set, the append-only evidence,
   create/add/remove, exact replay and `changed:false` convergence.
5. [done] Deterministic sorted projection and all-of/none-of predicates with no
   OR grammar and no scheduler semantics.
6. [done] 28 regressions across grammar, cardinality, scope-resolved authority
   and its named negatives, terminal-closure maintenance, replay/collision/
   convergence, projections/predicates, and non-interference.
7. [next] Independent review. W29401 (protocol/CLI) and W29408 (TUI) remain the
   later children and are unstarted.

## 2026-08-28 — independent review changes requested

1. [required] Move Work load, scope resolution and `manage-work-labels`
   authorization inside the replay transaction body. Exact retry must consult
   the operation journal before current policy; first execution must serialize
   its decision, mutation, event and retained authorization against revocation.
2. [required] Add an explicit authority read-snapshot boundary and use it for
   `project_work` plus label predicates so Work rows and label membership come
   from one SQLite snapshot. Keep returned data freshly owned after the
   transaction ends.
3. [decision required] Resolve create-time attribution. Recommended: remove or
   withhold the internal bootstrap `labels=` surface and block W29401's create
   operands until a canonical attributable Work-creation provider exists,
   rather than inventing authorization in this child. Alternative: approver
   explicitly expands this cut to add that replayable creation decision.
4. [required] Add real competing-connection add/add, remove/remove, add/remove,
   final-slot/revocation races and the three retained reviewer regressions.
   Preserve terminal mutation, exact all-of/none-of semantics, and scheduler/
   Thread/OCI non-interference.
5. [verification] Run the complete authority, session/boundary/catalog,
   parallel-runner and manager projection gates, then the full source gate with
   unrelated failures attributed exactly and return for re-review.

## 2026-08-28 — implementation-ready after M34988, one version decision open

1. [approved] Replace unattributed bootstrap creation with one generic,
   replayable creation pipeline. Require `operation_id`; generate the explicit
   trusted-bootstrap attribution inside the Authority face; retain immutable
   effective scope and provenance. Initial labels share the creation act and
   transaction. Preserve a closed later-authorized arm that reuses W16821's
   decision evidence.
2. [approved] Make label events name their exact act kind/id and project the
   creation attribution for initial additions. Never return `decision: None`
   for a create-time addition and never infer its act from an id prefix.
3. [required correction] Put first-execution Work/scope lookup and label
   authorization inside replay; exact retry consults the operation journal
   before current policy.
4. [required correction] Add one explicit read snapshot and use it for the
   complete Work projection and label predicate reads.
5. [required proof] Add creation exact-retry/collision/bootstrap-attribution/
   no-caller-forgery tests and real competing-connection add/add,
   remove/remove, both add/remove orders, final-slot and revocation races.
   Retain the three failing reviewer regressions.
6. [decision required] Confirm authority schema 5 as the cumulative boundary
   after active W16823's approved schema 4. Rebase on W16823; never reuse or
   lower schema 4.
7. [verification] Run the complete authority and source gates and return for
   independent review with exact evidence. W29401 stays blocked until this
   provider is accepted.

## 2026-08-29 — implementation unblocked

6. [approved by M35127] Use authority schema 5 as the cumulative clean-
   initialization boundary after delivered W16823 schema 4. Do not reuse or
   lower schema 4.
1-5, 7. [ready for implementation] The M34988 creation-attribution design and
   replay, snapshot, race, projection and verification corrections remain
   current. The 31-case label module still has exactly the three retained
   reviewer failures, so no correction has landed out of band. Implement the
   complete unit and return it for independent review; W29401 remains blocked
   until this provider closes satisfying.

## 2026-08-29 — items 3, 4 and the race half of 5

3. [done] First-execution Work lookup and label authorization are inside the
   replay body; the signature is caller operands only, so an exact retry
   consults the journal before current policy.
4. [done] `ControlStore.read_snapshot` opens one explicit read transaction and
   both the complete Work projection and the label predicate read use it.
5. [half done] The competing-connection matrix is in — add/add, remove/remove,
   add-racing-remove, final slot, revocation racing first execution — over real
   second Authority objects from real threads. The creation exact-retry,
   collision and bootstrap-attribution cases wait on items 1 and 2.
1, 2, 6. [NOT STARTED] The attributable/replayable creation pipeline, the exact
   label-event act attribution and the schema 5 allocation are untouched. The
   schema is deliberately still 4: M35127 requires 5 allocated ONCE as the
   cumulative boundary, and spending it on a cut that does not carry the
   creation work would burn it for nothing.

## 2026-08-29 — second independent review: changes requested

1. [confirmed corrected] Retain replay-before-policy and the single-snapshot
   projection/predicate reads; their original reviewer regressions are green.
2. [required] Track read and write transaction state distinctly. A write may
   join an existing write, but must refuse rather than silently run inside a
   read snapshot and then be rolled back after reporting success.
3. [required] Tighten the real-connection race matrix so raw SQLite/transport
   faults fail the case. Assert committed/convergent outcomes or named contract
   refusals, and at least one effective transition where the requested pair
   cannot both legitimately be no-ops.
4. [required, unchanged] Implement the complete M34988 creation pipeline,
   typed initial-label attribution, replay/collision/no-forgery tests and
   schema 5 boundary.
5. [verification] Run the focused Store and Work-label modules, the complete
   authority suite and the applicable source gates before re-review.

## 2026-08-29 — third independent review

1. [accepted] The Store distinguishes read from write nesting and refuses a
   write inside a read snapshot. The reviewer regression passes.
2. [accepted] The competing-connection harness uses thread-owned connections,
   rejects raw faults and missing answers, requires an effective transition,
   and asserts exact convergent/event/cardinality outcomes.
3. [required, unchanged] Complete the attributable and replayable Work
   creation pipeline, typed initial-label act attribution, schema 5 allocation
   and creation replay/collision/no-forgery matrix.
4. [cleanup with item 3] Remove the superseded `coherent()` commentary that
   still calls two losing writers legitimate; it contradicts the corrected
   harness and the Store contract even though the assertions are now right.
5. [verification] Re-run focused and complete authority gates after the
   creation/schema half lands, then return for final independent review.

## 2026-08-29 — fourth independent review: changes requested

1. [accepted] Retain required creation operation identity, public initial
   labels, replay placement, schema version 5, and non-null create-time event
   attribution.
2. [required P0] Implement the approved immutable `work_creation` act keyed by
   Work and unique operation identity. Persist the closed creation kind and
   explicit bootstrap provenance; keep genuine authorization decisions for
   the future authorized arm rather than representing bootstrap as a direct
   grant decision. Expose the creation attribution with the creation result
   and Work read as approved.
3. [required P0] Persist `act` beside `act_id` on every label event and join
   the exact named attribution. Remove `_act_kind_of` inference.
4. [required] Put effective scope in the canonical creation signature and
   capture one instant for Work, creation act, operation result and every
   initial label event.
5. [required proof] Add named creation exact-retry, collision,
   bootstrap-attribution, effective-scope canonicalization and no-caller-
   forgery cases. Retain the four reviewer regressions.
6. [verification] Run the focused modules and complete authority/source gates
   before final re-review; W29401 remains blocked.

## 2026-08-29 — fifth independent review: changes requested

1. [accepted] Preserve the immutable `work_creation` relation, persisted label
   event act kind, effective-scope creation signature, and shared
   Work/creation/initial-label instant.
2. [required P0] Include the immutable creation attribution in every ordinary
   Work projection, inside the same read snapshot, not only in the create
   transition's immediate result or a separate optional read.
3. [required] Project each label event's persisted `act_id` beside `act`, and
   join create-time attribution by the exact named act identity rather than by
   Work alone.
4. [required] Thread the one captured creation instant into the operation
   journal record so every durable fact of the atomic creation shares it.
5. [required proof] Add named creation collision and attribution-forgery cases
   and retain all reviewer regressions. Re-run the focused and complete
   authority gates; W29401 remains blocked pending acceptance.

## 2026-08-29 — sixth independent review: changes requested

1. [accepted] Ordinary Work creation attribution, exact event act identity,
   shared operation instant and the creation replay/collision/forgery matrix
   are complete; retain the 52-case focused and 342-case authority gates.
2. [required compatibility] Add `creation` to the Worker Manager's closed
   unread projection registry. Naming it is not consuming it; omission makes
   the manager refuse the complete authority projection.
3. [required gate correction] Update the projection-inventory extractor to
   read the canonical `_projected` dictionary after the snapshot refactor.
   Preserve exact registry equality and the full-projection acceptance case.
4. [verification] Run the focused authority suites and
   `TheProjectionContractMatchesTheAuthorityItReads`; W29401 remains blocked
   until all are green and this provider is accepted.

## 2026-08-29 — seventh independent review: accepted

1. [accepted] `creation` is registered as unread Worker Manager projection
   metadata and the exact projection compatibility boundary accepts a whole
   authority projection.
2. [accepted] The inventory extractor follows the canonical `_projected`
   dictionary while preserving exact member comparison.
3. [verified] Work-label authority 52/52, projection compatibility 2/2 and the
   complete authority suite 342/342 pass.
4. [done] W29400 is complete. W29401 remains subject to W38956's pinned
   campaign scheduling and must not take the implementation lane ahead of the
   useful Docker dogfood milestone.
