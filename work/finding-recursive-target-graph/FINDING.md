# Recursive target graph with target-scoped discussions

Status: **confirmed Baton 2.0.0 architectural restart by Slawomir on
2026-08-11; recorded for later design, explicitly deferred until after the
immediate 1.1 release.**

This is a top-level finding because it changes Baton's protocol, authority
model, CLI, readiness semantics, and human console together. It is not a child
of an existing product finding and may outlive the current release work.

## Origin and chronological decisions

### 2026-08-11 — live work must bind to durable goals

**Confirmed.** Git findings remain the durable dossier for product decisions,
evidence, plans, implementation progress, and append-only reviews. Baton owns
live workflow state. A stable binding may connect a Baton goal to a Git finding
without making either side a mutable mirror of the other.

The initial proposal treated a finding-bound work item as the primary object
and messages as its coordination stream.

### 2026-08-11 — micro-objectives are real but are not findings

**Confirmed.** Daily work contains bounded outcomes that can require several
handoffs without deserving their own `work/finding-*` folder. Producing a clean
reviewed commit message is the canonical example: implementer draft, reviewer
feedback, revision, approval, and delivery to Slawomir are real accountable
work, but not a separate Git dossier.

The interim proposal added one lightweight objective level beneath a large
work item.

### 2026-08-11 — the one-level/work-item split is superseded

**Superseded.** The restriction to one lightweight objective level and the
distinction between a large work-item type and a micro-objective type are not
current. Slawomir ruled that work forms an arbitrarily deep chain of targets:
there is a root goal, sub-targets, and further sub-targets as needed. Depth
changes scale, not semantics.

**Confirmed.** `target` is the single recursive workflow primitive. A root may
be a Git finding, release, incident, or another durable goal. Any target may
have child targets, including small operational results that carry no Git
folder of their own.

### 2026-08-11 — conversations always belong to a target

**Confirmed.** Messages without an objective are not useful workflow. Every
directed message, notice, artifact revision, review, handoff, and discussion
event has exactly one primary `target_id`. Messages may live at any level of
the target hierarchy. Replies inherit their target; starting unrelated work
means selecting or atomically creating another target.

The target's state is level-triggered workflow truth. Message delivery is
chronological evidence and discussion inside that target; consuming a message
must not make the target disappear from the next actor's work.

### 2026-08-11 — strict containment, graph navigation

**Confirmed.** Containment is stricter than the full relationship graph:

- every non-root target has exactly one containment parent;
- following containment parents yields exactly one root and one breadcrumb
  path;
- required open descendants gate ancestor closure;
- additional typed edges such as `blocks`, `depends_on`, `relates_to`, and
  `supersedes` may connect targets without becoming additional closure parents.

This preserves one answer to “what larger goal does this advance?” while still
supporting a graph for dependencies and navigation. Multiple containment
parents would make completion roll-up and requester authority ambiguous.

### 2026-08-11 — arbitrary depth, bounded TUI focus, visible ancestry

**Confirmed.** The data model has no UI-driven nesting limit. The TUI must
remain manageable by rendering a bounded local neighborhood around immediate
work rather than every level and edge at once.

Whenever a message or target is opened, the human sees how it is “part of” the
larger work through its ancestry breadcrumb, for example:

```text
root > A > B > C > D > E
```

At narrow widths the middle may be visually collapsed, but the root and the
deepest/current targets remain visible and the complete chain is navigable and
inspectable. A ten-level hierarchy must not require drawing ten expanded tree
levels merely to understand the current leaf.

## Confirmed target model

Every target needs at least:

- stable target identity;
- exactly one parent, except for a root;
- root identity and a reconstructible ancestor path;
- short title and explicit acceptance condition;
- lifecycle state;
- accountable owner and exact `next_actor`;
- required/optional relationship to its containment parent;
- current result plus immutable artifact/revision history;
- chronological discussion and transition events;
- optional Git root/path/revision binding when a durable dossier exists.

Containment must be cycle-free. Cross-target edges are typed, audited, and do
not alter containment roll-up.

## Confirmed closure/readiness behavior

- Resolving a leaf satisfies one gate on its parent; it does not automatically
  close the parent.
- A target becomes ready for its own acceptance only when its acceptance
  condition is met and its required descendants are terminal in an allowed
  state.
- Root closure is refused while required descendants remain open.
- Optional children may be cancelled with an audited reason.
- Adding or reopening a required descendant visibly reopens the ancestor gate.
- A target owed by participant P remains in P's next actions until an audited
  target transition changes `next_actor` or state. Message claim/receipt is not
  the readiness authority.

## Confirmed discussion behavior

Each target owns a chronological event timeline containing its human messages,
artifact revisions, reviews, handoffs, and state transitions. An event has one
primary target even when it references other targets. Cross-target navigation
is explicit; replies never silently retarget.

Target creation plus its first message must be available as one atomic, cheap
operation so mandatory target scope does not become authoring ceremony.

## Confirmed TUI direction

The target graph is the primary navigation model. “My next actions,” “work I
own,” “waiting,” and “recently resolved” are projections that select targets;
opening a result enters that target's discussion.

The focused screen should expose:

- the root and ancestry breadcrumb;
- the selected/current target and its discussion;
- its immediate children and their state/next actor;
- blocking/dependent neighbors on demand;
- acceptance, owner, next actor, Git binding, and remaining gates;
- collapsed resolved branches rather than an all-edges hairball.

The exact pane layout and narrow-terminal interaction remain open. The
behavioral requirement is bounded focus without losing root/current ancestry
or navigation at arbitrary depth.

## Git relationship

**Confirmed.** A target does not need a finding folder merely because it
exists. Substantial targets can be promoted by attaching a Git binding without
changing target identity or losing prior discussion. Git remains authoritative
for the dossier; Baton remains authoritative for live target state. Baton never
stages, commits, or otherwise mutates Git.

## Examples

```text
LANG-42  Fix parser recovery                 [root; Git finding]
└─ T-17  Prepare the accepted change         [target]
   ├─ T-18  Obtain reviewer source sign-off  [target]
   └─ T-19  Produce reviewed commit message  [target]
```

T-19 may contain several immutable candidate/review revisions. Closing it
advances T-17 without creating a finding. Discussion may also live directly on
LANG-42, T-17, or T-18; every message's breadcrumb makes that level explicit.

## Open design questions

These are not authorized implementation choices yet:

- exact lifecycle states and which terminal child states satisfy a required
  gate;
- target creation, reparenting, promotion, cancellation, reopen, and deletion
  permissions;
- whether reparenting is ever allowed after events exist, and how its audit
  preserves historical ancestry;
- stable portable target identifiers and Git binding/digest schema;
- exact typed dependency-edge vocabulary and cycle rules beyond containment;
- transactional target creation plus first-message and handoff commands;
- target-scoped notice audience rules;
- legacy protocol-10 import/migration treatment;
- retention and garbage collection for resolved target discussions;
- precise TUI graph, breadcrumb compression, keyboard navigation, and
  accessibility behavior;
- protocol/schema/version boundary and coexistence with protocol 10.

## Release boundary

**Confirmed by Slawomir on 2026-08-11:** record this direction now so it is not
lost, then focus on the immediate release. No protocol-11 target implementation,
authority migration, CLI surface, or TUI graph work is queued as part of 1.1.
Frozen 1.0 artifacts and the live protocol-10 authority/config remain untouched.

## Operational validation during the 1.1 workflow — 2026-08-11

**Observed.** The immediate release demonstrated why this is workflow
authority, not merely a graphical inbox:

- The root objective is “release Baton 1.1.” Its active descendants include
  deployment readiness, config wording, whole-message save, bulk archive,
  candidate build, soak, and release decision.
- After one child received source sign-off, the remaining ordered work was
  written in Markdown but no level-triggered target named the next actor. The
  implementer and reviewer could both wait while actionable release work
  existed. Slawomir had to ask for status and explicitly restart delegation.
- Answering “where are we?” required the reviewer to reopen and reconcile the
  umbrella plus deployment, config, save, bulk, search, and editor records. A
  root target with descendant states would have answered directly.
- Returning deployment changes to the implementer required another directed
  message. If that delivery or wake is missed, the work is delayed again; a
  target whose `next_actor` remains the implementer would stay visibly owed.
- The deployment review itself immediately produced nested objectives: close
  command/payload certification, then close true no-replace publication,
  staging cleanup, verification, and durability. Those discussions belong at
  their respective target depth while remaining part of the same release.
- Config wording advanced independently in non-overlapping files, but its
  independent sign-off and candidate-hash gates remain dependencies. A graph
  can expose safe siblings and blockers without pretending all work is either
  one flat queue or unrelated messages.

**Confirmed implication.** The target graph supplies execution semantics:
durable next action, closure gates, dependency visibility, and instant root
status. Breadcrumbs such as
`1.1 > candidate readiness > deployment > publication integrity > no-replace`
make each message's purpose and contribution explicit. The graph must therefore
drive readiness and status; rendering it is the human interface to that model,
not the model's only purpose.

## Baton 2.0.0 restart ruling — 2026-08-11

**Confirmed by Slawomir.** This target graph and target-scoped collaboration
model is Baton's next major milestone: **Baton 2.0.0**.

The earlier description of this as an incremental “protocol-11 direction” is
**superseded as the implementation strategy**. The exact authority protocol
number remains an open design detail, but the product/release boundary is not:
2.0.0 is a start-over effort that replaces the primary workflow and
collaboration flow rather than layering targets onto the current
message/claim-centric model.

**Confirmed reuse rule.** No 1.x subsystem is presumed to carry forward.
Useful pieces may be cherry-picked only after they are revalidated against the
target-first architecture. Likely candidates for investigation include typed
content manifests, external hash-pinned references, audited/idempotent
transition techniques, config/authority integrity checks, and tested
filesystem publication primitives. Their current APIs, schemas, lifecycle
semantics, and TUI placement are not thereby approved for reuse.

**Confirmed replacement direction.** The current attempt improved message
transport and human coordination but does not reach far enough because a
message/claim remains the work unit and readiness can disappear independently
of the underlying goal. Baton 2.0.0 begins from recursive targets,
target-local discussions, durable next action, closure roll-up, and dependency
navigation as its primary model. Messages become events within that model.

This ruling does not authorize 2.0 implementation during 1.1. The restart gets
its own later architecture/reuse audit and clean development isolation; no live
authority, frozen release, or current 1.1 serial item is changed for it.
