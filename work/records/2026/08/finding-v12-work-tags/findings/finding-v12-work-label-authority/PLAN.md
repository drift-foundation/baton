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
