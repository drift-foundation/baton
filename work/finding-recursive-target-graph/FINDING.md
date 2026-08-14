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

### 2026-08-12 — proposed pinned finding binding and parallel evidence

**Proposed by Slawomir; design direction, not yet an implementation ruling.**
The choice must not be “track the finding in Baton” versus “track it under
`work/finding-*`.” They hold different, complementary material:

- the filesystem finding folder is the rich dossier: `FINDING.md`, `PLAN.md`,
  implementer progress, append-only reviews, reproductions, scripts, fixtures,
  data, screenshots, and other assets that belong together and are reviewed in
  Git;
- the Baton target is the live coordination object: lifecycle, owner,
  `next_actor`, readiness, dependency/containment edges, discussion, handoffs,
  decisions, and chronological evidence about that work.

A finding-bound target therefore carries an explicit configured-root/path
binding to the folder. Messages and other events are scoped to the target and
become the second evidence stream around the dossier; Baton does not ingest,
index, or compete with the folder's files. A substantial finding may have
several required descendant targets executing in parallel, while the folder
continues to hold their shared plans and assets. A child target needs its own
folder binding only when a real child finding folder exists; target hierarchy
must not manufacture duplicate filesystem dossiers.

“Pinned” means the OPEN TARGET remains visible in the responsible actors'
level-triggered work projections until an audited lifecycle transition closes
it. It must not mean leaving one message unclaimed or at the FIFO delivery
head: message pinning through delivery state would block unrelated traffic and
again make consuming a message erase or stall the underlying goal. One message
may be designated as the target's origin/summary anchor for navigation, but
the stable target—not that message—is the workflow identity and closure gate.

Finding folders remain mandatory-ephemeral branch work. On closure, Baton
records the resolution and, when available, the final Git repository/revision
locator that preserves historical access. Normal removal of the live
`work/finding-*` folder must not damage the target history, change authority
health, reopen delivery, or require quarantine. An open target may use a
floating configured-root/path binding while work is uncommitted; closure must
make explicit whether a durable Git locator exists rather than falsely
claiming Baton stored the folder.

This is consistent with protocol-11 reference semantics—references may move or
disappear without damaging a message—but its lifecycle and graph behavior
belongs to the 2.0 target model rather than the narrower protocol-11 external-
reference correction.

### 2026-08-12 — confirmed restart/replacement reconstruction goal

**Confirmed by Slawomir.** Agent memory and process lifetime are never part of
the workflow authority. When an agent is restarted, replaced, or reassigned,
the successor must be able to inspect the finding folder plus its bound Baton
target/discussion and reconstruct, without predecessor memory:

- what outcome is being pursued and why;
- which decisions are confirmed, superseded, proposed, or still open;
- what evidence and working assets exist and where they live;
- what has been implemented and independently reviewed;
- which required descendants or dependency neighbors remain open;
- who owns the next action and what that action is;
- what blocks closure and what acceptance checks remain.

Neither source alone is expected to duplicate the other. The folder supplies
the rich durable dossier; Baton supplies current live workflow and discussion.
Together they must be sufficient, and disagreement must be visible rather than
silently resolved by preferring whichever source an agent happened to read
first. Target views should therefore expose the binding and a compact current-
state/next-action summary, while repository policy keeps finding plans and
review status current at handoff boundaries.

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
- exact open-folder versus closed-revision binding schema, including whether a
  target may close without a durable Git revision and how that exception is
  audited;
- whether an origin/summary message is required, how evidence messages are
  pinned for navigation without affecting delivery state, and who may change
  those pins;
- exact typed dependency-edge vocabulary and cycle rules beyond containment;
- transactional target creation plus first-message and handoff commands;
- target-scoped notice audience rules;
- legacy protocol-10 import/migration treatment;
- retention and garbage collection for resolved target discussions;
- precise TUI graph, breadcrumb compression, keyboard navigation, and
  accessibility behavior;
- exact restart-oriented status projection and how stale/disagreeing Git
  dossier versus Baton workflow state is detected and presented;
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

## 2026-08-13 — initial objective-first TUI navigation ruling

**Confirmed by Slawomir.** The TUI opens on a fixed-width table of top-level
objectives. It does not open on a message stream and it does not render the
whole target tree. Selecting an objective drills into another table containing
only that target's immediate children; the same interaction repeats at every
depth. A persistent ancestry breadcrumb shows the current location and permits
navigation back through the drilled path.

The table is borderless, like the current messaging console. Borders consume
scarce terminal columns without adding information; alignment comes from
fixed-width columns and responsive omission or compression at narrower
widths. The initial wide-table fields are:

- lifecycle status;
- objective/work-item title;
- recursive required-work progress;
- blocker summary;
- next actor;
- last update;
- an abbreviated numeric `Unans.` counter for messages the current participant
  still owes an answer.

`Unans.` is a participant-relative integer counter of actionable obligations,
not a count of unread discussion and not a boolean indicator. At a table row it
counts unanswered messages targeted at that participant on the row's target or
any descendant, so the top-level table reveals which objective needs attention
and each drill-down narrows the count until the responsible target is reached.
Answering or otherwise explicitly disposing of the obligation decrements it.
Exact response/disposition semantics remain part of the protocol design;
merely viewing an event must not decrement the counter.

Resolved children may be collapsed or filtered, but objective navigation,
progress, and unanswered-message visibility remain target projections. The
chronological discussion is opened within the selected target and is not the
application's primary start screen. Exact column widths, narrow-terminal
priorities, key bindings, sorting, and detail-pane behavior remain prototype
questions rather than ruled behavior.

## 2026-08-13 — compact participant handles

**Confirmed by Slawomir.** A v11 team handle is limited to eight terminal
display cells and a member handle is limited to eight terminal display cells.
With the separator, the canonical `team.member` address therefore occupies at
most seventeen cells. Participant identities must fit their allotted width;
the TUI must not make identities ambiguous through automatic abbreviation or
silent truncation.

This is both a protocol identity constraint and a TUI space budget. The exact
width-safe handle grammar, separator, migration of longer protocol-10
addresses, and optional longer descriptive metadata remain design questions.

## 2026-08-13 — participant handle limit tightened to 6/6

**Supersedes the 8/8 limit immediately above. Confirmed by Slawomir.** Team
handles and member handles are each limited to six terminal display cells.
Most team and member names can be abbreviated recognizably within that budget,
and the saved columns matter throughout the objective tables. With the
separator, canonical `team.member` addresses occupy at most thirteen cells.

The remaining rules and open questions from the earlier ruling still apply:
canonical identities are never silently truncated or automatically
abbreviated, while the width-safe grammar, separator, protocol-10 migration,
and optional descriptive metadata remain to be designed.

## 2026-08-13 — team, route, and member are distinct

**Confirmed by Slawomir.** Team, route, and member are three separate protocol
identities:

- the team owns the target/topic;
- the route owns the current responsibility;
- the member currently handles one or more routes and authors events.

Messages are addressed to a team and classified by kind. The receiving team's
route configuration maps the kind to one accountable route without requiring
the sender to know that team's members. A response records its actual member
author, but the message remains in the target's shared team discussion and is
not owned by that member.

Incoming-message responsibility and target-progress responsibility are related
but distinct transitions. A `bug` may first route to a review route for intake;
after acceptance, the target's next responsible route may become an
implementation route. The objective table shows the responsible route rather
than its current member handler. Target details may expose the current handler.
Reassigning a route to another member does not move the target or messages and
does not change their history.

The owning team may explicitly invite a named member of another team into a
target discussion. An invited member may see the shared discussion, receives
their own independent `New` projection, and may contribute under their real
member identity. Invitation is not team membership, route assignment, target
ownership, or responsibility transfer. Routine cross-team delivery still
addresses a team and kind rather than requiring knowledge of its staffing;
named invitation is a deliberate collaboration exception.

The six-display-cell limit applies independently to team, route, and member
handles. Canonical handles are never silently truncated or automatically
abbreviated.

**Approved as open review/design work.** K should review invitation history
scope, child-target inheritance and revocation together with the unknown-kind
fallback, exact per-member seen-cursor mechanics, explicit route reassignment
and disposition commands, compact addressing syntax, and how the TUI presents
route versus current handler. These are not yet implementation rulings.

## 2026-08-13 — cross-team invitations address a kind, not a member

**Supersedes the named external-member invitation above. Confirmed by
Slawomir.** A team invites another team's relevant capability into a target by
naming the destination team and message kind—for example, `team=drift` and
`kind=bug`. The receiving team's current configuration resolves that pair to
its accountable route and current handler. The sender neither names nor needs
to know a member such as Alice.

The invited team becomes a participating team for the topic, so its members
share visibility and may contribute. The resolved route alone is accountable
for handling the invitation; contributions by other members do not silently
transfer or discharge it. Responses identify their actual member authors.
Changing the receiving team's route mapping or handler does not rewrite the
invitation, target, or discussion.

There is no core cross-team named-member invitation. A message may mention a
person as useful context, but that mention carries no delivery, visibility, or
responsibility semantics. Open design work now concerns team/kind invitation
acceptance, participating-team and child-target scope, withdrawal, unknown
kinds, and route reassignment—not guest-member access.

## 2026-08-13 — shared topic discussion with personal New counters

**Supersedes the `Unans.` counter in the initial TUI ruling above. Confirmed
by Slawomir.** A target's discussion behaves like a team forum topic. Every
member of a participating team may see the complete discussion regardless of
which message kinds they route or handle, and any of them may contribute. A
route determines expected attention or handling; it is not a visibility filter
and does not make the routed member own the discussion.

The objective table uses a numeric `New` counter, not `Unans.`. `New` is
computed separately for the member viewing the table and counts all messages
in that row's target subtree that are visible to that member and newer than
that member's own seen position. It never exposes or incorporates another
member's unseen count. Consequently the same topic may simultaneously show
seven new messages to one member, one to another, and zero to a third.

Opening the discussion lets a member follow exchanges between other members
and join them—for example, a human may inspect a reviewer/implementer exchange
and intervene without first being its route handler. Advancing one member's
seen position changes only that member's `New` projection. It does not mark
anything seen for the team, answer a message, accept work, change the route,
or alter the target's owner, `next_actor`, blockers, readiness, or lifecycle.
Those remain explicit target workflow state.

Each routed message has one responsible team route even though the discussion
is shared. The member currently handling that route is accountable for the
route's intake or handling policy. Contributions from other members do not
silently take over, satisfy, or clear that responsibility; takeover,
reassignment, or disposition is an explicit audited transition. Conversely,
route responsibility does not imply that every message requires a reply: the
route's policy may classify a status update as no-action after it is noticed.

The exact seen-cursor granularity, explicit mark-seen interaction, treatment of
edits or non-message timeline events, and participating-team visibility rules
remain protocol and prototype questions.

## 2026-08-13 — current vocabulary and IRC-style discussion tags

**Confirmed by Slawomir; supersedes `target`/`topic` terminology and any
conflicting ownership or invitation wording above.** The current vocabulary is:

- a **team** is a group of members;
- a **member** is a concrete leaf actor such as K, Slawomir, Codex, or Claude;
- a **role** is a function assigned to members, such as reviewer,
  implementer, or approver;
- a **route** is a team's operational mapping from a public message kind to a
  responsible role and its current member handler or handlers;
- an **objective** is the recursive work/milestone object and is authoritative
  for status, progress, blockers, its current responsible route and handler,
  and the route expected next;
- a **discussion** is a reusable conversation carrying messages and related to
  any number of objectives;
- a **message** is a member-authored contribution to exactly one discussion.

Members have compact stable usernames and separate human-friendly display
names: `sl` or `slaw` may display as `Slawomir`. Identity and configuration use
the username; discussion presentation may use the display name. The confirmed
six-cell budget applies to compact team and member handles. Public route tags
also preserve the six-plus-six compact form described below; exact role-handle
and display-name constraints remain open.

Discussions use IRC-like typed tags:

- `#OBJECTIVE` relates the discussion to an objective;
- `@team.kind` asks that team's configured route for the kind to participate.

`#` tags behave like reusable Gmail labels: they are many-to-many, give no
discussion a primary or home objective, may cross objective trees, teams,
repositories, releases, and phases, and do not copy or move messages. They are
context/indexing relationships only and never change objective workflow state.

Applying `@lang.bug`, for example, is an audited operational invitation. Lang
resolves `bug` through its current routing configuration to a responsible role
and handler; Lang becomes a participating team; all Lang members may see and
contribute to the discussion; and the resolved route remains accountable until
explicitly transitioned. No member is addressed. Route-tag state and removal
cannot be inert label deletion because visibility and responsibility have
already been created; pending/active/resolved/declined/withdrawn semantics
remain for design and review.

An objective's `New` projection counts distinct messages unseen by the viewing
member across discussions carrying relevant `#` tags, including descendant
objectives. Multiply tagged discussions are deduplicated at common ancestors.
Discussion and tag activity never substitutes for the objective's explicit
status, current route/handler, or next route.

## 2026-08-13 — work lifecycle, endpoint tags, and cross-team dependency web

**Current direction confirmed by Slawomir and queued for K's architectural
review; naming called out below remains reviewable.** `Objective` is too
prescriptive for an unconfirmed report. A reported compiler crash may become a
confirmed defect, research item, design choice, accepted MVP limitation,
duplicate, or rejection without being renamed to “fix ...”. `Work` is the
current neutral umbrella candidate. A row has an explicit type/category,
status, neutral title, responsible endpoint/handler, personal `New` count, and,
when known, a planned successor. Milestone, finding/report, research, and
action are distinct useful types or categories; K should review the smallest
honest type model rather than assume the list is final.

The current collaboration vocabulary is refined as follows:

- **team**: a group of members;
- **member**: a concrete leaf actor with compact username and separate display
  name, for example `sl`/`slaw` displayed as `Slawomir`;
- **role**: reviewer, implementer, approver, or another function held by
  members;
- **endpoint**: the public `@team.kind` address that holds the baton;
- **route**: the receiving team's internal mapping from an endpoint kind to a
  responsible role and current member handler or handlers.

A route is dispatch, not a predetermined pipeline. `@lang.bug` may research,
accept, reject, request information, redirect, deduplicate, or categorize the
report. The reporter establishes who has the baton now and need not know what
comes next. A planned successor is optional while work is active and is chosen
by the current handler, not encoded in the route.

Tagging is the central communication grammar:

- `#WORK` gives a reusable discussion work-context label;
- `@team.kind` gives one endpoint accountable responsibility;
- `+team.kind` CCs/follows an interested endpoint without responsibility,
  readiness, blocking, or required disposition effects.

Other team members may inspect and contribute to a shared discussion without
taking its baton. A `+` follower may later be atomically promoted to `@` during
a handoff. `New` remains each member's own unseen count; visibility,
subscription, and responsibility are separate projections.

Relinquishing active work has exactly two honest forms. A nonterminal pass
atomically completes the current endpoint leg and activates a named successor.
A terminal close records an authorized disposition, has no current or next
endpoint, and propagates through containment and dependency edges. There is no
fake terminal recipient. No open work may be left without a responsible
endpoint.

Work records are owned and normally listed by one team, while typed links may
cross teams and are deliberately navigable on demand. A linked external record
does not enter another team's default tables or personal `New` counts, but a
member may drill from relevant local work into its high-level status, progress,
current role/member, next endpoint when known, activity, immediate children,
discussions, and links. This is a noise boundary, not a security boundary.

Many local reports may converge on one provider problem and one local record
may depend on several provider problems. On intake, the provider may create new
work or deduplicate the report onto existing work. Successful terminal closure
of the provider record satisfies every qualifying incoming dependency edge and
recomputes all parents and dependents; it is not addressed to an author or a
single “next” recipient. Dependents with other blockers remain blocked. A
non-satisfying disposition propagates its honest outcome without pretending a
fix was delivered. Required cross-team dependency edges need global cycle
checks, audited atomic relinking, and bounded one-hop/default TUI projections
rather than an all-teams hairball.

**Open for Slawomir/K review.** When one discussion has several `#WORK` labels,
an `@team.kind` application must define which local work record or records gain
the routing/dependency obligation. Implicitly applying it to every label risks
blocking unrelated work; requiring explicit selection is the reviewer's
recommendation. Also resolve the exact Work type/category model, route-tag
lifecycle and return behavior, multiple simultaneous external blockers,
cross-team drill depth, and which high-level external activity contributes a
local system event.

## 2026-08-14 — explicit route scope, one Current, provider-side convergence

**Confirmed by Slawomir after K's review.** Applying `@team.kind` is an
accountability write to exact Work, not an implicit operation on every `#`
label in a discussion:

- exactly one eligible local `#WORK` permits the bare endpoint tag;
- two or more require explicit selection of one or more exact Work records;
- none is refused unless Work creation is a separate explicit part of the
  operation.

Adding another `#` label later never enlarges an existing endpoint obligation.
Removing a label never cancels one. Cross-team Work cannot be selected by a
member who does not own or otherwise control that endpoint of the relationship.

Each Work record has at most one owning-team `Current` endpoint and current
member handler. External dependencies are blockers, not additional current
owners. Thus one Pushcoin record may remain owned by `@push.review` while
waiting on `@lang.bug` and `@build.cert`; each provider's own Work has its own
independent `Current`. A nonterminal pass changes the one current endpoint. A
terminal close clears it and has no next endpoint.

Different teams may report the same underlying provider problem without
learning about one another. Each keeps its own team-local Work, labels, and
discussion. The provider may deduplicate the reports by applying the same
provider-local `#WORK` label to several incoming discussions and linking every
consumer blocker to that one provider Work record. For example, Pushcoin,
Web, and MariaDB discussions may each be independently routed through
`@lang.bug`, while Lang labels all three `#LANG-42` in its own view. The
consumer teams neither see one another's labels, Work, discussions, nor
dependency edges merely because Lang related them.

The provider sees the related incoming reports and the fan-in count. Successful
terminal closure of the single provider Work satisfies all qualifying
consumer edges through level-triggered readiness recomputation. Each consumer
then independently becomes ready or remains blocked by its other gates. The
close has no author recipient and exposes no consumer to another consumer.

**Clarification confirmed by Slawomir.** Applying the provider's `#WORK` label
never creates, satisfies, removes, or retargets a workflow gate. During intake,
“relate/deduplicate to existing `#LANG-42`” may be presented as one UI action,
but its authority transaction records two distinct relationships: the inert
discussion label and an explicit required `consumer blocked_by LANG-42` edge.
The edge is cycle-checked and is the only gate. Adding or removing the label
alone cannot affect readiness, and provider closure follows incoming required
edges rather than searching discussions for matching labels.

## 2026-08-14 — canonical report, research, defect, implementation example

**Confirmed by Slawomir.** A routed report does not begin as a confirmed defect
or promise to fix. Work preserves separate facts:

- immutable **origin**, such as external report, self-initiated work, or parent
  decomposition;
- mutable **classification**, initially unknown and later perhaps suspected
  defect, confirmed defect, limitation, duplicate, design choice, or rejection;
- operational **status/phase**, including research and waiting for evidence;
- exactly one current endpoint/handler plus an optional planned successor.

Research is therefore an operational phase in this confirmed example, not the
historical origin and not proof of defect classification. A Lang record may
remain `classification=unknown`, `status=waiting_evidence`, and
`current=@lang.research` while several independent reports are deduplicated
onto it. The research endpoint remains accountable while parked; no next
endpoint need be predicted.

Classification and baton transfer are distinct audited decisions. Changing
`unknown` or `suspected_defect` to `confirmed_defect` never silently changes
the current endpoint. The current member may confirm and pass in one atomic UI
operation, but the authority records both changes. Team policy defines which
roles may make each classification transition and may suggest or constrain
successors without becoming a hidden automatic pipeline.

A typical Lang flow is:

```text
@lang.research --suspected defect--> @lang.review
@lang.review   --confirmed defect--> @lang.impl
@lang.impl     --implementation complete--> @lang.review
@lang.review   --fixed and verified--> terminal close
```

If the research member also holds the reviewer role and is authorized to
confirm defects, the first review leg may be skipped and the confirmed record
passed directly to `@lang.impl`. After implementation the independent review
leg remains. Terminal reviewer closure has no next endpoint and satisfies all
qualifying incoming dependency edges through level-triggered recomputation.

Reject, request-information, redirect, duplicate, defer, and
accepted-as-limitation remain valid research dispositions. A rejection ends
the provider's intake leg honestly and returns attention through the recorded
origin relationship; it never claims a fix was delivered.

## 2026-08-14 — linked cross-team Work is deliberately discoverable

**Confirmed by Slawomir; supersedes the mutual-hiding language in “explicit
route scope, one Current, provider-side convergence” above.** Baton v11 is an
open coordination system, not a security boundary between teams. Team-owned
Work stays out of unrelated teams' default tables and personal `New` counts to
control noise. Once an explicit relationship links one team's Work to another,
however, a curious member may deliberately drill through that relationship and
inspect the related graph. This includes discovering that other teams have
linked reports against the same provider Work and using those links to judge
whether their problems are related.

The provider may therefore expose its fan-in count and linked consumer Work;
those facts do not require a per-viewer projection that hides every other
consumer. “Not shown by default” must never be specified or implemented as
“must not be seen.” Exact detail fields and navigation depth remain TUI
prototype questions, but the authority model must preserve navigable links and
must not treat cross-team graph discovery as unauthorized enumeration.

**Clarification confirmed by Slawomir.** Baton follows an open-source
coordination model: the graph contains no team-private secrets. Team ownership,
routes, default tables, subscriptions, and `New` projections reduce noise and
assign responsibility; they are not read-access controls. A member who
deliberately browses or searches another team's Work must not be blocked merely
because no prior relationship exposed it. Explicit links make relevant Work
easy to reach, but do not grant visibility that was otherwise forbidden.

**Notice consequence confirmed by the same ruling.** Protocol-10 notice scope
does not survive as a v11 content-read ACL. In v11, notice scope selects whose
attention projection, delivery state, and personal `New` count receive the
notice; it does not make the notice bytes secret from other members who
deliberately browse or search for them. An out-of-scope read does not create a
delivery, seen receipt, or disposition and therefore does not weaken the
scoped audience's at-most-once delivery semantics. Migration must explicitly
retire protocol 10's audience-only `authorize_read` rule rather than widening
it accidentally as a side effect of unrelated implementation.

**Receipt clarification confirmed by Slawomir.** If the reader belongs to a
notice's frozen audience, every content-read path must atomically record that
member's delivery/seen receipt before returning the bytes. Open browsing is not
a receipt-free side door for an intended recipient. If the reader is outside
the audience, the same content remains readable but no receipt, seen state, or
disposition is recorded. Thus personal `New` continues to mean unread for the
member, while content visibility remains open. Migration also retires the
indistinguishable non-member refusal that protected protocol 10's notice id
space; restoring it would incorrectly turn the noise boundary back into a read
barrier.

**Notice search clarification confirmed by Slawomir.** Search and browse
results for notices are metadata-only: they may expose subject, author, scope,
timestamps, and other non-content fields, but no body snippet or attachment
bytes. Opening a result is the content read and, for an in-audience member,
atomically records the receipt before returning bytes. A broad search must not
silently mark every matching notice seen. Work and discussion search may show
content snippets because those objects do not carry notice at-most-once receipt
semantics.

## 2026-08-14 — TUI and agent JSON have semantic parity

**Confirmed by Slawomir.** Agents must be able to navigate and understand the
v11 Work graph with the same effect as a human using the TUI. The TUI is not a
separate authority and its screen layout is not an automation API. Both the TUI
and machine clients consume one canonical semantic projection; the TUI renders
that projection as tables, breadcrumbs, detail views, and discussions, while
the CLI exposes it as versioned JSON without terminal formatting.

The JSON navigation surface must provide at least:

- the viewer's default top-level Work rows;
- the current scope and complete breadcrumb as stable Work ids;
- immediate children for deterministic drill-down;
- type, immutable origin, mutable classification, operational status, neutral
  title, progress, readiness, exactly one current endpoint/handler, optional
  planned successor, blockers, and personal attention counters;
- typed containment and dependency links, including deliberate cross-team
  traversal;
- related discussions, messages, artifacts, and dossier references;
- the viewer's actionable/current responsibilities separately from unseen
  message counts; and
- the explicit transitions currently available to that actor, without
  implying that merely reading performs one.

Machine fields use stable ids, enums, numbers, booleans, and structured
relations rather than preformatted display strings. Every response identifies
its JSON projection/schema version, protocol version, viewer, query scope, and
authority snapshot or equivalent consistency token. Lists have deterministic
ordering and explicit bounded pagination. Unknown fields remain safely
ignorable within a compatible projection version; incompatible versions fail
clearly rather than degrading into plausible but false output.

At minimum, equivalent read operations must cover default/home listing, Work
detail, child listing, typed links, discussion listing/detail, and personal
attention/actionable work. Mutating pass, classify, link, tag, disposition,
and close operations also return structured results describing the committed
state. Streaming readiness may use JSON Lines or another framed form, but must
carry the same stable identities and semantics. Agents never parse TUI text,
column positions, colors, glyphs, or breadcrumbs to recover protocol state.

Semantic parity does not require visual parity. Responsive column dropping,
title elision, key bindings, and breadcrumb elision are TUI presentation;
structured JSON retains the complete values. A parity test suite must feed one
authority state through the shared projection and prove that TUI-visible rows,
counts, drill relationships, and actionable state agree with the JSON result.

## 2026-08-14 — announcements are ordinary messages with broad selectors

**Confirmed by Slawomir; supersedes the v11 notice-content, receipt, and notice
search rulings above.** V11 has no standalone notice object and no separate
broadcast object. Those sections remain migration analysis of protocol 10's
notice abstraction, not current v11 product semantics. An announcement is an
ordinary message in a discussion, related to Work with `#WORK` like any other
message.

Broad selectors compose with the existing tag grammar:

- `+*` places the message in every member's attention and personal `New`
  projection without creating responsibility or requiring disposition;
- `@*.kind` expands the named kind across teams and creates one accountable
  routed obligation for each matching team endpoint; and
- `@*.*` is valid and deliberately makes every configured endpoint of every
  team responsible, potentially creating several obligations per team.

For example, `#BATON-OPS +*` tells everyone about a shutdown. Adding
`@*.ops` means every team's operations route must act and dispose of its own
obligation. The publication records the exact selector expansion so the
sender and agents can determine who received attention and which endpoints
owe action. These remain ordinary discussion messages; “broadcast” is only a
convenient description of broad selection.

**Clarification confirmed by Slawomir.** `@*.*` must not be blocked merely
because narrower selection is usually cleaner. The TUI and JSON interface may
preview its exact expansion and warn that it creates duplicate team
obligations, but the sender may intentionally proceed—for example, when the
installation has only a handful of participants and every route should act.

**Route-size clarification confirmed by Slawomir.** The protocol and examples
must not assume every team defines an `ops` route; that convention implies a
larger or more specialized team than many Baton installations have. For a
small installation where every configured endpoint should stop, the shutdown
form is `#BATON-OPS +* @*.*`. `@*.ops` is available only when teams actually
define that kind and the sender intentionally wants one operations obligation
per matching team.

**Selector-shape clarification confirmed by Slawomir; supersedes the `+*`
shorthand above.** Wildcard attention uses the same `team.kind` shape as
accountability: `+*.*` expands across every configured endpoint but creates no
responsibility and requires no reaction or disposition. It is the ordinary
form for “notify everyone; we will proceed regardless.” Because a member may
handle several matching routes, attention and `New` are deduplicated by
member-and-message identity; expansion must never show the same message several
times to one member. A shutdown notification that will be forced is therefore
`#BATON-OPS +*.*`; add `@*.*` only when every endpoint must explicitly act.

## 2026-08-14 — inclusion, response request, and ownership transfer are distinct

**Confirmed by Slawomir; supersedes every earlier statement that `@team.kind`
itself transfers Work accountability or ownership.** The stable endpoint
identifier is `team.kind`; the leading operator states what relationship this
operation creates:

- `+team.kind` optionally includes the endpoint for attention, with no response
  or disposition required;
- `@team.kind` directs a message to the endpoint and requires a response or
  explicit disposition, while the originating Work remains owned by its
  existing `Current`; and
- `=>team.kind` passes the Work baton, atomically changing its one `Current` to
  that endpoint. The recipient owns the next action until it passes or closes
  the Work.

Thus `@lang.bug` means “answer this request, but the Work is still mine,” while
`=>lang.bug` means “this Work is yours to handle.” `+` contributes personal
attention/`New`; `@` additionally enters the endpoint's actionable response
projection; `=>` enters the recipient's current-Work projection. All three are
audited, but only `=>` mutates Work ownership. A planned `Next` may identify the
intended return endpoint without performing that later pass.

Wildcards preserve the same distinction. `+*.*` notifies every matching
endpoint without requiring reaction. `@*.*` creates a required response from
each expansion target while the coordinator retains the Work baton. Because a
Work has exactly one `Current`, `=>` resolves to one exact endpoint and
`=>*.*` cannot transfer one Work to many owners. Multi-Work bulk passes, if
provided, remain an explicit operation over individually identified Work.

The TUI may render `=>` as the pass arrow, while JSON records structured
operators such as `include`, `request_response`, and `pass`; agents never infer
workflow effects from punctuation. Exact withdrawal rules for unresolved `@`
response obligations remain to be ruled.

**Cardinality clarification confirmed by Slawomir; supersedes `@*.*` and every
other multi-destination `@` form above.** `+` is the only fan-out operator. It
may name a comma-separated selector list and may use wildcard expansion, for
example `+lang.bug,build.review` or `+*.*`; resulting attention is deduplicated
per member and message. `@` names exactly one resolved destination for one
required response, and `=>` names exactly one resolved destination for one
Work pass. Neither accepts comma-separated destinations or a wildcard that
expands to several endpoints.

If a future bulk operation needs required responses from several endpoints, it
must explicitly create and report separate single-destination `@` obligations;
it is not one multi-destination request hidden behind `@*.*`. Likewise one Work
never gains several owners through a broad `=>`. The ordinary forced shutdown
that needs attention but no acknowledgements remains `#BATON-OPS +*.*`.
