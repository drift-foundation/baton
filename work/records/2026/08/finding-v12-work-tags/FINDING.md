# Finding: v12 Work labels

**Status:** approved Work-label contract; serial implementation children
created and dependency-gated as Baton Work `W28880`

**Binding:** `baton:work/records/2026/08/finding-v12-work-tags`

**Roadmap:** `work/records/2026/08/finding-v12-isolated-agent-workers/`

## Confirmed requirement — 2026-08-27

V12 needs user-defined labels on Work. A team can attach zero or more labels such
as `v12`, a release name, or the identity that requested a feature, then use
those labels to filter Work later. The canonical protocol and TUI term is
**Work label** or **Job label**.

Labels are cross-cutting metadata. They are not a substitute for containment,
dependencies, Route, Handler, phase, priority, classification, or outcome.
No scheduler or authority behavior may be inferred merely from the spelling of
a label unless a later, separately recorded contract explicitly introduces that
behavior.

The feature must support both labels supplied when Work is created and durable
label changes later in its lifetime. Changes must remain attributable through
the Work event history, and projections must expose enough canonical data for
exact filtering.

## Terminology clarification — confirmed 2026-08-28 UTC

The earlier **tag** wording is superseded. A v12 Work label is one opaque key,
not a parsed `name=value` pair. Examples are `v12`, `release-foo` and
`requested-slaw`. If v12 later needs structured name/value metadata, that is a
separate attribute or annotation feature and must not silently change label
semantics.

The canonical dossier path and W28880 title retain their original `tags`
wording because bindings and historical ledger identity are not renamed.
Current product vocabulary, projection fields, filters, CLI help and TUI copy
must use **labels**.

## Proposed initial boundary

The following details remain proposals until reviewed and approved:

- model a Work's labels as a set rather than an ordered list;
- preserve a compact, case-insensitive canonical spelling suitable for both
  CLI input and TUI display;
- journal additions and removals with actor and time instead of silently
  replacing the complete set;
- do not inherit labels automatically through Work containment;
- support exact label filters first, then specify repeated-filter AND/OR
  composition rather than guessing.

## Open decisions

1. What grammar, normalization, length and cardinality limits apply?
2. Which participants may add or remove labels before, during and after a claim?
3. How do multiple label filters compose, and how are negated filters expressed?
4. Which projections, CLI commands and TUI surfaces expose and edit labels
   without consuming excessive horizontal space?
5. How are label mutations made idempotent and race-safe?

## Reviewer research — 2026-08-28 UTC

### Observed current boundaries

- The current Python v12 authority is an assignment/workflow authority, not a
  port of the complete v11 Work product. `authority/schema.py` gives `work`
  only identity, Route, lifecycle, assignment, contract and gate fields. There
  is no title, owning team/scope, priority, classification, containment,
  generic Work-event stream, list/search projection, CLI, or modular TUI in
  this implementation yet.
- `authority/core.py:create_work` is a trusted-bootstrap operation with no
  attributable creator. `project_work` is the one Work projection.
  `authority/session.py` enumerates every runtime transition and read, and its
  operation journal in `authority/store.py` provides exact-signature replay.
  A label implementation must deliberately extend all of these surfaces; a
  table alone would not make a protocol feature.
- The current schema is version 1 and `Store.open` refuses every other schema
  version; it has no migration path. Adding durable label tables therefore
  requires an explicit schema-version and rebuild/upgrade disposition.
- V11 already uses **label** for a different relation: `label`/`unlabel` attach
  a Thread to Work, and a Thread projection's `labels` member lists those Work
  associations. The Worker Manager also calls its OCI runtime identity facts
  `labels`. Neither is user-defined Work metadata, and neither may be merged
  with this feature.
- The approved W9901 architecture requires Work to carry an authority-owned
  effective scope and forbids deriving scope or authority from Route,
  repository or participant spelling. Provider W16821 owns that still-open
  principal/scope authorization seam. The present `(route, participant)` and
  deployment-global participant capability model cannot correctly authorize
  Work-label changes.
- The canonical v11 ledger has no Work-retitle operation. Its `revise` verb
  promotes a discussion message as the complete Work contract and does not
  change the title. The latest T28880 discussion asks to retitle W28880, while
  the restored confirmed terminology ruling says the historical title remains
  unchanged. This review follows the durable ruling unless it is explicitly
  superseded; it does not misuse contract revision as a retitle workaround.

### Inferred implementation ordering

The semantic design can be approved now, but implementation must consume the
authority-owned principal/effective-scope/grant decision from W16821. It must
not introduce a temporary flat-team or Route-handler authority rule that W16821
would immediately invalidate. The user-facing CLI and TUI pieces also depend
on a v12 Work list/search host that does not exist in the current Python tree;
they should be separate bounded cuts after the authority model.

## Proposed initial label contract — awaiting decision

Everything in this section is **Proposed**, not confirmed authority.

### 1. Opaque canonical key and set limits

- One supplied label is 1–64 ASCII characters matching
  `[A-Za-z0-9][A-Za-z0-9._-]{0,63}`. The authority normalizes ASCII `A-Z` to
  lowercase before comparing or storing it. Canonical output is therefore
  lowercase and byte-for-byte exact.
- `=`, whitespace, path separators, control characters and non-ASCII text are
  refused. Dots, underscores and hyphens carry no hierarchy or name/value
  meaning; the whole normalized string remains one opaque key.
- A Work holds at most 32 live labels. The collection has set semantics and
  projects in ascending canonical spelling. Repeated create/filter operands
  that collapse to the same normalized key refuse as ambiguous input rather
  than being silently deduplicated.
- No spelling or prefix is reserved for scheduler or runtime facts. If v12
  later needs authority-owned system metadata, it receives a separate typed
  field/table and projection rather than a magic user-label prefix.

This narrow ASCII grammar makes case-insensitivity deterministic across SQLite,
Python, JSON, CLI and TUI clients, keeps the complete projected set bounded by
about 2 KiB, and avoids Unicode case-fold or locale-dependent uniqueness.

### 2. Mutation authority and lifecycle

- Labels supplied by a Work-creation operation are authorized by the same
  authority decision that permits creation in the Work's effective scope.
- Later additions/removals require a dedicated `manage-work-labels` role/grant
  resolved by the authority for the Work's effective scope. Route eligibility,
  current claim, Handler identity, team-name similarity and plain membership
  grant nothing. The caller supplies neither principal nor scope.
- A label change is permitted independently of queued/active/block/parked
  phase and independently of the current claimant. The proposed baseline also
  permits owning-scope label maintenance after terminal closure, because it
  changes archive metadata without reopening or rescheduling Work. Every such
  act remains journalled. If terminal Work must instead be byte-for-byte
  immutable, that is one explicit decision to reverse before implementation.
- Work labels do not inherit to children and are not copied across follow-up,
  dependency, duplicate, pass or provider relationships. Every Work's set is
  explicit.

### 3. Durable set, event history and replay

- Store the current set in an indexed `work_label(work_id, label, ...)` relation
  with uniqueness on `(work_id, label)` and an inverse `(label, work_id)` index
  for exact filtering.
- Record every effective addition/removal in an append-only typed label-event
  journal. Each event carries the Work reference, canonical label, add/remove
  action, instant, and W16821's canonical authorization evidence: endpoint,
  principal, effective scope, role/grant provenance and accepted policy
  generation. Create-time labels are additions attributed to the creation act.
- Live-set mutation, label event, Work last-change marker where the later Work
  host has one, and operation-journal result commit in one transaction.
- The session transition takes a required operation id and includes Work,
  canonical label, action and authorization context in the authority-owned
  signature. An exact retry replays. Reusing the id with another operand
  refuses.
- Adding a present label or removing an absent label commits a successful
  `changed:false` result and no new label event. Concurrent same-direction
  operations therefore converge without fabricating changes. Add/remove races
  serialize; the event with the later committed sequence determines the live
  set. At the 32-label boundary, the cardinality check and insert occur under
  the same write transaction, so only one racing final-slot addition wins.

The exact event columns should reuse W16821's authorization-evidence shape,
not create a second provisional spelling while that provider is open.

### 4. Canonical projections and exact filtering

- Every canonical Work row/detail projection exposes `labels` as a fresh,
  sorted array of canonical keys, including empty `[]`. A separate paged label
  event read, or the eventual unified Work-event view, exposes attribution.
- Work list, tree and search filters accept repeatable `label=` and
  `without-label=` operands. All filters compose with existing canonical facts
  by AND. Repeated `label=` means the Work has **every** named label; repeated
  `without-label=` means it has none of the named labels. Supplying one key in
  both groups refuses as contradictory.
- The initial contract has no implicit OR. A future disjunction needs a
  separately named operand such as `any-label=` and its own bounded group; it
  must not silently change repeated `label=` from intersection to union.
- Matching is normalized then exact membership, never substring, SQL `LIKE`,
  title-query expansion, or interpretation of separators. The existing
  title/id search query remains title/id search; label operands narrow that
  result. A label-only listing uses the canonical list/tree filter.
- The projection and label predicates are read in one authority snapshot.
  Filtering belongs only to the read view; it cannot affect readiness, Route,
  ordering, claim eligibility or dispatch.

### 5. CLI and TUI vocabulary

- Creation adds repeatable `label=` operands on every path that atomically
  creates Work.
- Later mutations use explicit `label-work work=... label=...` and
  `unlabel-work work=... label=...` verbs. The existing `label thread=...` and
  `unlabel thread=...` Thread–Work relation remains unchanged and unambiguous.
- Detail always renders the complete sorted set as a wrapped `Labels:` field.
  A wide Jobs table may show a comma-separated `Labels` column, but the entire
  column drops before operational identity/state columns at narrower widths;
  labels never force truncation of Route, Handler, phase or Work identity.
- Active `label=`/`without-label=` clauses use the existing dedicated filter
  disclosure and remain visible on drilled/search pages. The list need not
  paint every matching label merely to prove why a row matched.

### 6. Scheduler and runtime non-interference

Adding, removing or spelling labels such as `v12`, `priority-high`,
`route-impl`, `contract-v12`, `blocked`, or a participant name changes only the
label set, label journal and ordinary last-change metadata. It does not alter
contract, phase, gate, readiness, priority, Route, Handler, dependency,
containment, outcome, offer selection, worker input, OCI runtime labels,
capacity or authorization. User Work labels must not be copied into the Worker
Manager's OCI label map, where a label is an execution-identity fact.

## Proposed implementation cuts

1. Authority model: grammar owner, versioned persistence, indexed live set,
   append-only event, create/add/remove operations, replay, projection and
   exact filter predicates; blocked on W16821's authorization seam.
2. Protocol/CLI host: create-time operands, distinct mutation verbs, common
   list/search filters, help and JSON projection versioning.
3. Modular TUI: detail rendering, optional wide Jobs column, filter entry and
   disclosure, narrow-width behavior.
4. Independent conformance and migration/rebuild proof before acceptance.

## Required conformance matrix

**Grammar and limits:** empty, 1/64/65-character boundaries; ASCII case
normalization; disallowed `=`, slash, whitespace, control and non-ASCII input;
duplicate-after-normalization create/filter operands; 32/33-label boundaries;
stable sorted projection.

**Authority and lifecycle:** creation attribution; granted principal in the
derived scope; ungranted principal, plain member, Route handler and claimant
negative cases; queued/active/block/parked parity; terminal mutation according
to the approved ruling; revoked-grant race; caller-supplied scope/principal
refusal.

**Retry and race:** exact operation replay; operation-id collision; concurrent
add/add and remove/remove convergence; add/remove ordering; two additions
racing for the final cardinality slot; projection interleaving that proves one
snapshot rather than a Work row from before and labels from after.

**Projection and filtering:** empty/nonempty projections; exact rather than
substring matching; repeated positive intersection; repeated negative
exclusion; contradictory filters; composition with status/phase/Route/Handler/
priority/title query; pagination; closed visibility; fresh-owned result data.

**Non-interference:** suggestive user labels leave every scheduler and
assignment field unchanged; no child/follow-up/pass inheritance; Thread labels
and their commands remain unchanged; Worker Manager OCI labels and runtime
reconciliation receive no user Work labels.

**TUI:** wide and narrow Jobs layouts, wrapped detail, zero/one/many labels,
active-filter disclosure on root/drilled/search views, case normalization, and
safe rendering of the maximum set.

## Decision request

Approval is needed for the proposed package, especially these coupled choices:

1. 64-character ASCII-lower canonical grammar and 32-label cardinality;
2. scope-resolved `manage-work-labels` authority, not Route/claim/membership;
3. audited label maintenance after terminal closure;
4. repeated `label=` as AND, `without-label=` as negation, and no first-cut OR;
5. convergent `changed:false` no-ops with no fabricated label event; and
6. retaining the historical W28880 title per the durable ruling, or explicitly
   superseding that ruling and creating a separate retitle capability rather
   than misusing `revise`.

## Confirmed Work-label baseline — 2026-08-28 UTC

**Approved by Slawomir in T28880 message 29384:** adopt the complete proposed
initial label contract above without replacement:

1. labels are 1–64 ASCII characters in the recorded grammar, normalized to
   lowercase, with at most 32 live labels per Work;
2. later mutation uses scope-resolved `manage-work-labels` authority consuming
   W16821, never Route eligibility, claim ownership, participant spelling or
   plain membership;
3. label additions/removals remain audited and permitted after terminal Work
   closure;
4. repeated `label=` filters intersect, `without-label=` excludes, and the
   initial contract has no implicit OR;
5. adding an existing label or removing an absent label returns
   `changed:false` without fabricating a label event;
6. later mutations use distinct `label-work` and `unlabel-work` verbs, leaving
   the existing Thread–Work `label`/`unlabel` relation unchanged; and
7. W28880 retains its historical title. No Work-retitle capability is added,
   and `revise` remains solely contract promotion.

The **Proposed** labels in the earlier section preserve the chronological
decision history. This confirmed ruling makes that package authoritative. The
implementation cuts and conformance matrix recorded there are current; a
replacement must explicitly supersede the affected numbered rule.

## Implementation ordering — confirmed dependency

W16821 is still open and blocked behind W5 at snapshot 29388. W28880's
implementation cannot start by recreating a flat `(route, participant)`
authorization rule: it consumes W16821's principal/effective-scope/grant
decision and its exact evidence shape. The implementation is therefore split
into serial authority, protocol/CLI, and TUI children, with the first child
blocked on W16821 and each later child blocked on the preceding cut. The parent
remains open until every child is satisfying and the complete feature receives
independent review.

The serial children created on 2026-08-28 are:

1. W29400, authority model —
   `work/records/2026/08/finding-v12-work-tags/findings/finding-v12-work-label-authority/`,
   blocked on W16821;
2. W29401, protocol and CLI —
   `work/records/2026/08/finding-v12-work-tags/findings/finding-v12-work-label-protocol-cli/`,
   blocked on W29400; and
3. W29408, TUI —
   `work/records/2026/08/finding-v12-work-tags/findings/finding-v12-work-label-tui/`,
   blocked on W29401.

All three children are routed to `baton.impl`. Their dossiers narrow the one
approved parent contract; they do not independently reopen its decisions.

## 2026-08-28 — create-time attribution ruling

**Confirmed by approver response M34988:** choose the bounded attributable
creation provider now. There is one generic, replayable Work-creation pipeline.
Its first attribution kind is explicit trusted bootstrap, generated by the
authority rather than accepted from a caller. Every creation has a required
operation identity, immutable creation act, effective scope and honest
bootstrap provenance; initial labels commit in that exact creation transaction
and name that exact attribution. The envelope must admit a later authorized
creation kind carrying the real endpoint, principal, grant provenance and
policy generation without replacing the pipeline. Retained bootstrap-created
Works remain permanently and visibly bootstrap-attributed and are never
backfilled.

**Confirmed unchanged:** W29400 also owns the replay-after-revocation,
single-snapshot projection/predicate, concurrency and projection corrections
identified by its first independent review.
