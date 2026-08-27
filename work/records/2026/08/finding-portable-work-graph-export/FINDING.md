# Export the authoritative Work graph as portable text

## Confirmed 2026-08-27

Operators need to export the current Work graph for inspection in external
graph tools. Baton's existing TUI dependency neighbourhood is intentionally
bounded and dependency-only; repeated `links` reads cannot form an
authoritative full export because each invocation may observe a different
snapshot.

## Decision

Baton exports a deterministic, portable TEXT representation of the graph. The
first interchange format is Graphviz DOT. Baton does not render SVG, PNG, PDF,
or another visual artifact and does not require the Graphviz runtime. An
operator redirects the textual output to a `.dot` file and may render or
import it with any external tool later.

The export is derived in one authority read transaction and names its snapshot
sequence. It contains stable Work identities and typed relationships rather
than inferring meaning from layout, colour, or line style. At minimum the
model distinguishes dependency, containment, follow-up, and duplicate
relations; every edge also spells its relation in text. Node ordering, edge
ordering, identifiers, labels, and quoting are deterministic so two unchanged
snapshots produce byte-identical output.

The authority projection and the DOT renderer are separate boundaries. The
projection remains structured data suitable for another textual renderer or
graph analysis later; DOT is an export format, not protocol state and not the
authority's internal model.

## Explicit exclusions

- No image generation or bundled graph-layout engine.
- No direct SQLite reads outside the canonical authority projection.
- No permanent exporter assembled from one `home` call followed by N
  independently snapshotted `links` calls.
- No styling-only semantics.

## Open design details

The implementation-ready review must decide the CLI verb and operands, default
scope, how open-only exports treat terminal relationship endpoints, bounded
versus complete export policy, and whether structured JSON is exposed beside
DOT. Those choices may not weaken the one-snapshot or text-only decisions
above.

## Reviewer revalidation — 2026-08-27

**Observed:** the existing projections answer different bounded questions and
cannot serve as a full export:

- `tree` is one snapshot, but team-scoped and capped at three containment
  levels;
- `dependency_neighborhood` is one snapshot, but dependency-only, directional,
  depth/page bounded and capped at 200 rendered occurrences;
- `links` carries all four relation families one hop at a time, but repeated
  calls sample different snapshots, and its downstream `blocks` list
  deliberately excludes closed consumers.

**Confirmed implication:** the exporter needs one new authority projection
over the canonical current relation sources. It must not call or crawl the
existing public views. Evidence and focused baseline:
`evidence/design-baseline-2026-08-27.md`.

## Proposed CLI contract for approval

The canonical verb is:

```text
work-graph format=json|dot status=all|open|closed [team=HANDLE]
```

- `format=json` is the default. It preserves the ordinary sorted JSON envelope
  and exposes the structured projection for graph analysis and future pure
  text renderers.
- `format=dot` writes raw UTF-8 DOT to stdout, suitable for `> work.dot`. The
  ordinary identity/config/projection-version checks still run first. A
  refusal writes the existing JSON error to stderr, exits nonzero and emits
  nothing to stdout.
- `status=all` is the default; omitting `team=` selects every team. Thus the
  zero-operand default is the complete current authority graph, open and
  terminal, across teams.
- `team=` and `status=` are graph-scope operands, not the participant-relative
  `home/tree` filter grammar. There is no `work=`, depth, page, limit, cursor or
  layout operand in the first version.

`format=dot` is the one deliberate raw-output exception. It is explicit so
existing automation can continue to assume JSON unless it asks for a portable
text artifact.

## Proposed structured projection

`projection.work_graph(store, *, team=None, status="all")` runs under one
reentrant `_read_snapshot` and returns:

```json
{
  "scope": {
    "team": null,
    "status": "all",
    "closure": "incident-endpoints"
  },
  "counts": {
    "selected_nodes": 0,
    "context_nodes": 0,
    "nodes": 0,
    "edges": 0
  },
  "nodes": [],
  "edges": [],
  "snapshot_seq": 0
}
```

Each node has the fixed members `id`, `local_id`, `team`, `title`, `origin`,
`classification`, `priority`, `status`, `phase`, `outcome`, `created_seq` and
`selected`. `phase` is null for terminal Work; `outcome` is null for open Work.
The projection does not add Route, Handler, message, attention or dossier facts
that are not graph identity or current node state.

Each edge has the fixed members `relation`, `predicate`, `source`, `target`,
`relation_seq` and `via_obligation`. `via_obligation` is the dependency value
or null for every other relation. Direction is semantic and fixed:

| relation | source -> target | predicate | relation sequence |
| --- | --- | --- | --- |
| `dependency` | blocker -> consumer | `blocks` | `edges.created_seq` |
| `containment` | parent -> child | `contains` | child `created_seq` |
| `follow-up` | predecessor -> successor | `followed_by` | successor `created_seq` |
| `duplicate` | rejected duplicate -> canonical survivor | `duplicate_of` | duplicate `closed_seq` |

This is the current graph, not relationship audit history. Removed dependency
edges are absent; current `edges` rows remain present even where the `links`
downstream drill would hide a terminal consumer.

## Proposed scope and terminal-endpoint rule

Scope is selected first. With no filter every node is selected. With `team=` or
`status=`:

1. select every Work matching the operands;
2. include every current typed edge incident to at least one selected node;
3. include the other endpoint of each such edge as `selected: false` context;
4. do not recursively expand relations incident only to context nodes.

This makes every selected node's direct typed adjacency complete, never emits a
dangling edge, and does not let one terminal predecessor pull an unbounded
history chain into an open-only export. DOT spells `scope=selected|context` in
both attributes and the readable node label. An empty selection is a valid,
metadata-bearing empty graph.

In particular, `status=open` retains a closed blocker, predecessor or other
terminal endpoint when it is incident to selected open Work. Terminal context
is explicit; it is never promoted to a matching open row or silently dropped.

## Proposed completeness and snapshot policy

The export is **complete-or-refuse**. It has no UI depth, occurrence, page or
row cap and no truncation member. The implementation reads all Work rows and
all current dependency rows in a constant number of ordered statements inside
one transaction, derives the other three relation families from those Work
rows, validates the whole projection, samples `snapshot_seq` inside the same
transaction, then rolls back.

For DOT, the full text is rendered and validated in memory before the first
stdout write. An application refusal therefore cannot leave a syntactically
valid-looking partial graph. Ordinary sink failures such as a full destination
disk remain I/O failures rather than authority semantics.

Cycles are represented, not traversed or hidden: DOT is a graph interchange
format and a complete export is useful for inspecting damaged topology. A
missing endpoint, duplicate typed edge, invalid fixed relation value, unknown
team, or malformed renderer input refuses with the exact offending relation.
No fallback omits an invalid row or edge.

## Proposed deterministic ordering

- Nodes: `(created_seq, id)` ascending.
- Edges: `(relation_seq, relation_rank, source, target)` ascending, with rank
  `dependency`, `containment`, `follow-up`, `duplicate`.
- JSON object keys: the existing CLI `sort_keys=True`; array order is the
  canonical order above.
- DOT graph attributes, node attributes and edge attributes: lexicographic by
  attribute name. Statements follow graph metadata, nodes, then edges.
- UTF-8 with LF line endings and exactly one final LF.
- No generated-at time, participant, config path, working directory or random
  value. Identical authority UUID, snapshot and scope yield byte-identical DOT
  for every authorized participant.

## Proposed DOT format version 1

The document begins with non-`strict` `digraph "baton_work"`. It MUST NOT use
`strict`: Graphviz merges parallel edges with the same tail and head, while two
Works may simultaneously have dependency, containment, follow-up or duplicate
relations.

The graph carries quoted attributes:

- `baton_authority_uuid`
- `baton_dot_version="1"`
- `baton_projection_version`
- `baton_protocol_version`
- `baton_snapshot_seq`
- `baton_scope_status`
- `baton_scope_team` (`*` when unfiltered)
- `charset="UTF-8"`

Every node identifier is the quoted canonical Work id. Every node has a
human-readable single-line `label` which spells local id, team, status,
phase/outcome, selected/context scope and title. Semantic attributes are
`baton_*` strings for every structured node member. Null phase/outcome is the
literal string `null`. `baton_title_b64` plus
`baton_title_encoding="base64-utf8"` preserves the exact title independently
of label escaping.

Every edge is one explicit `source -> target` statement with
`label="RELATION: PREDICATE"` and fixed `baton_relation`, `baton_predicate`,
`baton_relation_seq` and `baton_via_obligation` attributes. Relation text is
therefore machine-readable and visible without colour, style or layout.
Parallel typed edges remain separate statements.

No colour, rank, cluster, shape or line style carries Baton meaning. Baton
does not invoke a Graphviz command, discover Graphviz, or render an image.

## Proposed hostile-text encoding

DOT identifiers and values are always double-quoted. The renderer:

- escapes `"` for DOT syntax;
- protects every user backslash so title text such as `\N`, `\G`, `\E`,
  `\T`, `\H`, `\L`, `\n`, `\l` and `\r` cannot become Graphviz `escString`
  substitutions;
- emits printable Unicode unchanged under explicit UTF-8;
- renders control and format code points visibly as `<U+XXXX>` in `label`;
- retains the exact UTF-8 title bytes separately in `baton_title_b64`.

No HTML-like label is used. Quotes, backslashes, comment markers, brackets,
semicolons, leading `#`, tabs, NUL, RTL/format controls and non-ASCII titles
must remain one node statement and cannot create DOT structure.

## Required implementation and verification boundary

Recommended files and symbols:

- `src/baton_work/projection.py`: `work_graph` and its fixed node/edge builders;
- new `src/baton_work/dot.py`: pure renderer and quoting helpers;
- `src/baton_work/cli.py`: `work-graph` grammar/dispatch and explicit raw DOT
  branch after the same participant/config/version validation;
- `src/baton_work/jsonapi.py`: projection 12.6;
- new `tests/work/test_w24755_work_graph_export.py`;
- public help plus `docs/EFFECTIVE-BATON.md` and `docs/BATON-WORK.md`.

Acceptance cases:

1. all four relation types, exact directions, predicates and sequences;
2. same endpoint pair with several relation types remains several DOT edges;
3. open/team filters retain terminal/cross-team endpoints as marked context,
   never dangling, and do not expand context-only relations;
4. a closed dependency consumer remains in the full current projection even
   though `links.blocks` hides it;
5. more than 500 nodes and more than 200 edges export completely with no page,
   depth, occurrence or continuation fields;
6. an interleaved writer is wholly before or after nodes, edges, counts and
   `snapshot_seq`, never mixed;
7. repeated JSON projections and DOT bytes are deterministic; DOT is identical
   across participants for one authority/snapshot/scope;
8. hostile titles listed above neither inject syntax nor trigger `escString`
   substitutions, while base64 decodes to the exact UTF-8 title;
9. malformed operands and damaged endpoints refuse with empty DOT stdout;
10. cycles and parallel typed edges are exported without recursive walking;
11. a full read leaves the authority and WAL byte-identical;
12. execution succeeds when no `dot`/Graphviz executable or library exists and
    never attempts a subprocess or image output.

## Approval points

**Proposed for approver confirmation:**

1. `work-graph`, JSON default, explicit raw `format=dot`.
2. Default scope all teams and all statuses.
3. Filtered scope closes only over incident endpoints and marks context.
4. Complete-without-pagination policy; application refusals emit no partial
   DOT.
5. Structured JSON is public beside DOT and projection 12.6.
6. Non-`strict`, semantics-in-text DOT v1 with exact-title base64.

No implementation should start until these choices are confirmed or explicitly
superseded in this finding.

## Approver ruling — 2026-08-27

The proposal is approved with one scope correction and one bounded-history
addition.

1. `work-graph`, JSON default and explicit raw `format=dot` are confirmed.
2. The zero-operand scope is all teams with `status=open`, not `status=all`.
   This is the useful current operational graph; terminal history must not
   bury it by default.
3. `changed-from=` and `changed-until=` are an optional pair for
   `status=open|closed` and are BOTH mandatory for `status=all`. The interval
   is half-open: `changed-from` is inclusive and `changed-until` is exclusive.
   Both accept only timezone-bearing RFC 3339 instants, normalize to UTC, and
   refuse an empty or reversed interval.
4. The range selects nodes by canonical `last_changed_at`. That member is
   therefore added to each structured node and its DOT `baton_*` attributes.
   Incident endpoints remain explicit context even when their timestamp falls
   outside the range. The result is the current graph of Work touched during
   the interval, not historical reconstruction of graph state during it.
5. Filtered incident-endpoint closure, complete-without-pagination export,
   public structured JSON with projection 12.6, and non-`strict` DOT v1 with
   exact-title base64 are confirmed without amendment.

Examples of the approved surfaces are:

```text
work-graph
work-graph format=dot
work-graph format=dot status=all changed-from=2026-08-01T00:00:00Z changed-until=2026-09-01T00:00:00Z
```

`status=all` without both bounds refuses. Baton still emits text only and
never invokes or bundles Graphviz.

## Independent review — 2026-08-27

**Confirmed clarification:** the earlier DOT rationale overstated which
relation families can coexist on one endpoint pair in the current authority.
Containment plus dependency is refused as a required-edge cycle; follow-up
plus dependency cannot be created because the predecessor is terminal;
containment plus duplicate cannot close while the child is open. Dependency
plus duplicate is reachable and is sufficient to require a non-`strict`
digraph. The broader coexistence claim above is superseded by this reachable
account; the non-`strict` format decision is unchanged.

**Confirmed clarification:** `baton_scope_changed_from` and
`baton_scope_changed_until`, using `*` when absent, correctly extend DOT v1
with the approved interval and make the entire scope explicit in the document.

**[P1] Confirmed:** `_export_instant` uses `datetime.fromisoformat`, whose
accepted language is broader than RFC 3339. A space separator, ISO week date,
and basic date/time spelling are currently accepted and normalized even though
the approved CLI contract says only timezone-bearing RFC 3339. The public
boundary needs an explicit RFC 3339 grammar before normalization.

**[P1] Confirmed:** the renderer does not satisfy its independent-boundary
contract. Projection-side `_export_validate` rejects duplicate typed edges,
missing endpoints and relation/predicate disagreement, but
`dot.render_work_graph_dot` never invokes equivalent validation. A structured
caller can therefore obtain a complete-looking DOT document containing an
exact duplicate edge, a dangling endpoint, or a forged predicate. The
renderer must own those failures before composing bytes.

**[P1] Confirmed:** `baton_scope=selected|context` does not supersede the
separate approved requirement for one `baton_*` attribute per structured node
member. Both fit without conflict. DOT must retain `baton_scope` for the
readable role and add `baton_selected=true|false` for the projection's exact
boolean member.

**[P2] Observed:** team existence is queried by `_export_scope` immediately
before `_read_snapshot`, so not every authority read used to answer the export
is in the named transaction. Move store-dependent scope validation under the
same read snapshot (while retaining refusal before rendering) so configuration
acceptance cannot race the graph read.

Reviewer regressions are additive in
`tests/work/test_w24755_work_graph_export.py`. The resulting focused run is 57
passed and 3 failed; details are in
`review-2026-08-27T16-08-50Z.md`.

## Second independent review — 2026-08-27

**Confirmed corrected:** the three first-review regressions pass. The public
RFC 3339 shape is checked before parsing; lower-case `t`/`z` is normalized;
the configured-team read is inside the graph snapshot; the renderer invokes
the shared graph validator; and DOT carries both `baton_scope` and
`baton_selected`. Duplicate nodes are now refused as well as duplicate edges.

**[P1] Confirmed:** RFC 3339 permits one or more fractional-second digits, but
`datetime` stores only microseconds. The current normalization accepts
`2026-08-27T00:00:00.0000001Z` and
`2026-08-27T00:00:00.0000009Z`, then silently collapses both to
`2026-08-27T00:00:00.000000Z`. Different approved bounds must remain different
scope instants. Preserve arbitrary fractional precision during offset-to-UTC
normalization (and canonicalize equivalent trailing-zero spellings) rather
than truncating it through `datetime`.

**[P1] Confirmed:** shared graph validation now owns topology but still does
not own the fixed member types. A renderer input with `selected="false"` is
treated as selected because the string is truthy; a non-text title later
escapes as `AttributeError` during base64 encoding. Validate the structured
node and edge member types/nullable members before semantic graph validation,
and raise `WorkError` naming the offending member before composing DOT.

The two additive second-review regressions leave the focused result at 64
passed and 2 failed. See `review-2026-08-27T16-24-41Z.md`.

## Third independent review — 2026-08-27

**Confirmed corrected:** arbitrary RFC 3339 fractional precision now survives
UTC normalization and equivalent trailing-zero spellings canonicalize without
collapsing distinct instants. The shared validator also owns every fixed
node/edge member's exact Python type and nullable domain. The five regressions
from the first two review passes are unchanged and green.

**[P1] Confirmed:** fixed node-state members still have no value-domain
validation. The renderer accepts `status="bogus"`, `phase="review"`, and
`outcome="done"`, then emits each as complete-looking readable and
machine-readable DOT state. The graph schema's two statuses, four scheduler
phases, and four terminal outcomes are closed authority vocabularies, not
arbitrary strings. Validate those three domains in the shared graph validator
and raise `WorkError` naming the member before rendering.

The parameterized additive regression reports 3 failed. See
`review-2026-08-27T16-39-54Z.md`.

## Fourth independent review — 2026-08-27

**Confirmed corrected:** the shared validator now owns all six fixed member
vocabularies, including the three named by the third review. The authority's
canonical values are reused and the read-side import is bounded to vocabulary
data. The correction baseline is 73 focused cases, all green.

**[P1] Confirmed:** value-domain checks still do not validate state as a whole.
The renderer accepts open nodes with null phase or non-null outcome, closed
nodes with non-null phase or null outcome, and a non-dependency edge with
non-null `via_obligation`. These contradict the approved node-state and edge
provenance schema even though each individual member passes its type/domain
check.

**[P1] Confirmed:** the renderer's “whole input validated” boundary still
excludes fixed scope semantics and counts. Forged scope status/closure, an
unpaired malformed range bound, and counts inconsistent with the arrays all
render without refusal. Validate the entire structured result once and share
that enforcement between projection and renderer; configured-team existence
remains the projection's snapshotted store-dependent check.

Nine additive cases fail on the two gaps while the prior 73 remain green. See
`review-2026-08-27T16-54-31Z.md`.

## Fifth independent review — 2026-08-27

**Confirmed corrected:** coupled node/edge state, fixed scope/count semantics,
producer-side validation, and the corrected paired-nullability case all land.
The fourth-review regressions are unchanged and green; focused and boundary
runs report 86 and 5 passed.

**[P1] Confirmed:** direct structured range bounds are RFC-valid but need not
be the canonical UTC-normalized strings the projection promises. The scope
validator discards `_export_instant`'s canonical return and DOT emits the
original offset, letter case, or trailing-zero fraction. Equivalent normalized
scopes can therefore produce different bytes. Require both non-null structured
bounds to equal their canonical values while preserving the public operand
path's acceptance and normalization of legal alternate spellings.

Six additive cases fail, covering three non-canonical spellings on both
bounds. See `review-2026-08-27T17-09-43Z.md`.

## Sixth independent review — 2026-08-27

**Confirmed corrected and signed off.** Both structured bounds must now equal
their canonical UTC normalization, while the public operand path continues to
accept and normalize legal offset/case/fraction spellings. End-to-end cases
prove equivalent operand spellings produce byte-identical DOT. The focused
suite reports 95 passed, boundaries 5 passed, and `git diff --check` is clean.

All preceding review findings remain corrected. The final independent review
is `review-2026-08-27T17-21-50Z.md`; W24755 is ready to close satisfying.
