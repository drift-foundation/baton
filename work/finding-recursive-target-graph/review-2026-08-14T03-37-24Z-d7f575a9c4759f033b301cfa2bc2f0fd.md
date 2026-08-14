# Review: Work, endpoint tags, and the cross-team dependency web

Reviewing the 2026-08-13 section and PLAN 6–12 as asked. No implementation.
I have separated **required corrections** (things that are wrong or undecidable
as written, and would have to be redone) from **prototype-deferrable** choices.

## The explicit open question, answered

**Yes — `@team.kind` must select the exact local Work record(s), explicitly.**
I agree with the recommendation and would go further about the reason.

"It risks blocking unrelated work" is the consequence; the defect is that
applying an endpoint tag is a WRITE to one record's accountability and
dependency edges, and a write with an ambiguous target is wrong independent of
what it happens to hit. The fan-out makes it worse in a specific way: one `@`
gesture against three `#WORK` labels creates three obligations, each of which
then needs its own disposition. The tagger consented to one act and owes three.

Concretely, and failing closed:

- discussion carries **exactly one** `#WORK` → bare `@team.kind` is
  unambiguous and allowed;
- **two or more** → bare `@team.kind` is REFUSED, with the labels listed; the
  qualified form `@team.kind #WORK-123` is required (repeatable if the tagger
  really means several);
- **none** → refused, or an explicit "create Work from this discussion" act.
  Silently minting a record from a tag hides an origin nobody chose.

## Required corrections

### 1. Type is being asked to do two jobs; split origin from classification

The section is right that a reported compiler crash must not be renamed to
"fix ..." — but the fix is not a better umbrella noun. It is that a Work record
has TWO facts, with different mutability:

- **origin** — how it entered the system (external report, self-initiated,
  decomposition of a parent). Immutable. It is history.
- **classification** — what we currently believe it is (defect, design choice,
  accepted limitation, duplicate, rejected, research). Mutable, and legitimately
  `unknown` until intake decides.

Collapsing these into one mutable `type` means a stable id's type changes
underneath every reference to it, and "was this reported by a user?" becomes
unanswerable after triage. Collapsing them into one immutable type means intake
cannot do its job.

**`milestone` should not be a type at all.** It is a structural position: a Work
with children and no executable action of its own. If it is a type, a record
that acquires children must change type, and a record that loses its last child
must change back — mutation driven by the shape of the graph rather than by any
decision. Derive it.

`research` is the genuinely ambiguous one: it reads like a phase of a report
("we are researching it"), not a kind of thing. I would let the prototype
decide that one — see deferrable (a).

Smallest honest model I can defend: `Work { id, origin (immutable),
classification (mutable, nullable), status, title, current endpoint, optional
planned successor, parent }`.

### 2. An endpoint tag must resolve at tag time, and fail closed

`@team.kind` is simultaneously an ADDRESS (stable, owned by the receiving
team's config) and an ACCOUNTABILITY ASSERTION (per-Work, mutable). They have
different lifetimes, and the model does not currently say what happens when the
first changes under the second.

Required:

- an unknown `kind`, or one the receiving team has retired, is REFUSED AT TAG
  TIME and visibly to the tagger. A tag that lands nowhere is the same defect
  class as a stranded claim: the sender believes work is owed and nobody owes
  it;
- accountability records store the RESOLVED endpoint together with the
  resolution time, so later renames do not silently re-point history;
- retired endpoint names are never reused. Reuse makes old records lie.

### 3. A pass must resolve its successor before it completes its leg

"A pass requires an atomic successor" is right, and the failure mode is
specific: the named successor may be unroutable — unknown kind, retired
endpoint, a team with no current handler for that kind. If the current leg
completes first, the result is open work with no responsible endpoint, which
this finding forbids in the same paragraph.

So the transaction is: resolve the successor against the receiving team's
CURRENT route, and refuse the whole pass if it does not resolve. Never complete
first and resolve after.

### 4. Fan-out and reopen must be level-triggered, not event-triggered

PLAN 7 already says "level-triggered readiness". I want to state why it is
load-bearing and where else it applies, because this is the clause most likely
to be quietly dropped during implementation.

A provider's terminal close satisfies N incoming edges. If that is implemented
as an event that walks dependents and marks them ready, then: a crash mid-walk
leaves half the graph updated, a replay double-applies, and — decisively —
**reopen cannot retract it**. Recomputing each dependent's readiness from the
current state of its blockers is idempotent, survives replay, and makes reopen
fall out for free rather than needing its own inverse-propagation path.

The same applies to closure propagating through containment.

### 5. Cycle checking is over the UNION of containment and required dependency

The section asks for "global cycle checks" on required cross-team edges. Two
graphs exist — containment and dependency — and closure is said to propagate
through both. A cycle in the union is therefore a deadlock even when neither
graph alone contains one. Check the union.

Say the cost out loud: a global check on insertion makes cross-team required
edges a serialization point. That is defensible for REQUIRED edges (a cycle
there means everyone waits forever), but it means edge insertion is not a
local, always-available operation, and the TUI has to be able to say "this
edge was refused because it would close a loop through `@web.bug`".

### 6. `New` aggregates over containment only, never over dependency

A "recursively aggregated numeric New counter" over a graph with cross-team
links has three failure modes: a shared child counted once per parent, a
counter whose value reveals the existence of items the member may not read,
and unbounded recomputation as the web grows.

Required: aggregate over the containment TREE only; count each discussion item
at most once per member via that member's own seen cursor; never aggregate
across the team boundary — which is exactly what "does not enter unrelated
default tables or `New` counts" already promises for linked external records.

### 7. Stable Work ids and the 2.0 authority boundary interact (PLAN 6 + 13)

PLAN 6 wants stable Work ids; PLAN 13 contemplates a clean 2.0 authority with
1.x traffic NOT imported. Then 2.0-minted ids must be incapable of colliding
with ids referenced by retained 1.x messages, or a link in an old message
silently resolves to a new, unrelated record. Qualify ids with the authority
uuid or a generation prefix. This is cheap now and unfixable later.

## Deferrable to the prototype

These are real questions, but the answer depends on seeing rows on a screen,
and deciding them now would be guessing with extra steps.

(a) **Whether `research` is a type or a status.** Both are defensible; the
    tell will be whether a research row ever needs to outlive the question that
    prompted it.
(b) **Drill depth.** One hop by default is a reasonable starting guess; whether
    it needs to be configurable is a usage question.
(c) **Column priorities, sorting, keys, narrow-terminal layout** — PLAN 12
    already says prototype first, and I agree.
(d) **Which external activity contributes a local system event.** Depends on
    what the noise actually feels like; too tight and people miss handoffs, too
    loose and the local table becomes the other team's log.
(e) **Exact vocabulary** (`Work` itself, `+` vs another CC glyph). Naming is
    worth one prototype cycle before it is frozen into a schema.

## One thing I would not let pass without a sentence in the product

The finding says cross-team drill-through is "a noise boundary, not a security
boundary". That is a legitimate choice and I am not arguing it — but it should
be stated where a user can read it, not only in the design record. Someone will
eventually put something sensitive in a Work title on the assumption that
another team cannot see it. If that assumption is ever needed, retrofitting it
is a schema change and a data audit, not a filter.
