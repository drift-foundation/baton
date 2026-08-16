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

## 2026-08-14 — implementation-plan blockers resolved

**Confirmed by Slawomir after review of `IMPLEMENTATION-PLAN.md`.** The first
v11 implementation slice uses these foundational rulings:

1. Protocol 11 products are application version `11.0.0`; historical “Baton
   2.0.0” wording is superseded and creates no second marketing or deployment
   version.
2. Team, member, and endpoint-kind protocol identities use canonical handles
   limited to six terminal display cells by wcwidth semantics, validated when
   registered and never abbreviated at render time. Each may carry an
   unrestricted descriptive display name. The fresh v11 authority receives
   new handles; protocol-10 identities and history are not migrated or
   rewritten.
3. V11 deliberately drops protocol 10's at-most-once delivery model. Messages
   are re-readable; personal `New` is attention derived from a member's seen
   cursor, not a delivery receipt. Reading never consumes or hides content.
4. List, search, count, detail projection, and other ordinary reads are pure.
   An intentional discussion open performs a separate idempotent seen-cursor
   transition that advances only the acting member through a committed message
   sequence. The transition is explicit in JSON and invoked deliberately by
   the TUI; another member's cursor and `New` are unchanged.

## 2026-08-14 — JSON/CLI-first implementation and adversarial soak

**Confirmed by Slawomir.** Implementation stabilizes the authority, data
model, transitions, canonical projection, and versioned JSON CLI before adding
the TUI. Agents must be able to use the packaged JSON surface alone to create
and navigate Work, communicate with `+`/`@`/`=>`, inspect obligations and
discussions, advance their own seen cursor, follow dependencies, and close or
unblock Work. This phase is exercised heavily by `baton.reviewer` and
`baton.implementer` against a fresh experimental v11 authority, including
concurrency, retry, crash-boundary, pagination, and cross-team scenarios.

Protocol 10 remains the coordination authority while that battle test is in
progress; an incomplete v11 tool never replaces the channel needed to report
its failures. Agents use only the packaged JSON/CLI contract during the soak,
not raw SQLite, source-private entry points, TUI scraping, or hand-reconstructed
state.

The TUI follows after the engine and JSON contract are stable. It consumes the
same canonical projection and transitions and may not invent separate workflow
semantics. Any missing state discovered while designing the screen is first
added to the shared projection and JSON contract with tests, then rendered.
Same-fixture TUI/JSON parity remains a release gate; it is deferred in sequence,
not removed from scope.

## 2026-08-14 — focused Gate A test entry point

**Confirmed by Slawomir after Gate A completion.** The repository exposes the
completed JSON/CLI vertical slice as one focused, repeatable Just recipe:
`just test-gate-a`. It runs the complete `tests/work/` suite, including the
adversarial soak, directly against the checkout. It does not build or require a
release candidate and does not replace the full `just build` then `just test`
release gate.

**Immediate naming supersession confirmed by Slawomir.** The recipe above is
named `just test-v11`, not `just test-gate-a`. The protocol-generation name is
the stable user-facing distinction: `just test-v11` runs only the v11 Work
suite, while `just test` continues to cover both v10 and v11.

**Focused-run presentation and concurrency confirmed by Slawomir.**
`just test-v11` reports each pytest node as it executes instead of rendering
quiet dots and percentages. It uses pytest-xdist with one worker per CPU made
available by `nproc`; xdist is a pinned development dependency so a fresh
`just venv` reproduces the command. This changes only the focused runner, not
the v11 semantics or the full release gate.

**Parallel-run harness correction.** The first 32-worker run passed all 89
tests but Python 3.13 emitted 48 warnings because three concurrency tests used
the platform's default `fork` start method from multithreaded xdist workers.
Those tests now explicitly use the safe `spawn` context. The warnings are
corrected at their source rather than filtered from the test output.

**Focused-run scheduling clarification confirmed by Slawomir.** Tests that
create their own 16-process contention or soak workloads are marked `serial`
and run once, without xdist. The remaining v11 tests run through xdist with
one worker per available CPU. The explicit spawn context remains as a harness
safety property, while the split prevents nested worker multiplication and
makes the two forms of concurrency visible in the recipe output.

## 2026-08-14 — Gate B authorized

**Confirmed by Slawomir after committing Gate A as `bed522d`.** Proceed with
Gate B exactly as scoped in `IMPLEMENTATION-PLAN.md` rev 4: render the stable
canonical projection in a v11 TUI, prove TUI/JSON semantic parity from the same
fixture, and exercise the scenario through packaged artifacts. Gate A's data
model and JSON semantics are the frozen foundation. A missing semantic value
or contradiction discovered during rendering is reported and ruled before the
shared projection is changed; it is not patched around in the TUI.

Presentation decisions deliberately left prototype-grade by the plan—column
priorities, sorting, keys, dependency navigation and narrow layouts—may be
implemented mechanically so long as they preserve the pinned borderless,
fixed-column, breadcrumb/drill model and do not create independent workflow
semantics. Protocol 10 remains the live coordination channel throughout Gate B.

## 2026-08-14 — open Gate B viewer-validation gap

**Observed by `baton.implementer` during B1 and held for ruling.** Every
viewer-relative projection read currently accepts an unknown `team.member` and
returns ordinary empty state. Consequently a misspelled `--viewer` opens an
apparently valid empty JSON/TUI world instead of refusing before curses starts.
Mutations already validate their actor, so reads and writes disagree about
whether the named identity exists.

The recommended correction is to validate the member on every viewer-relative
read (`home`, `children`, `new_count`, `obligations`, `detail`, and equivalent
surfaces) and return the existing structured `WorkError`/JSON error for an
unknown viewer. Viewer-less graph reads such as `links` and `breadcrumb` remain
unchanged, and validation is identity checking rather than a read ACL: the
open cross-team graph ruling still holds. Alternatives are a fallible client-
remembered `whoami` preflight or accepting the ambiguous empty console. B2 may
continue independently; the projection change and its strict xfail remain
blocked on Slawomir's choice.

## 2026-08-14 — v11 requires an instance configuration boundary

**Confirmed by Slawomir; supersedes the narrow per-read viewer-validation
proposal immediately above and pauses the Gate B authorization.** Protocol 10
has a `baton.json` that defines the instance rather than accepting an arbitrary
identity and discovering topology piecemeal. Protocol 11 requires the same
architectural boundary. Its configuration must define the instance's protocol
metadata and authority location together with the configured teams, roles,
routes, participants/members, display names, and assignments needed to resolve
a public `team.kind` endpoint to accountable responsibility.

The public identity term remains **participant**, as in protocol 10.
`--viewer` is not a second identity: the current implementation uses it both
for personal projections and as the author/actor of mutations. The eventual
CLI and TUI therefore open with `--config ... --participant team.member` (or an
equivalent participant selected by client configuration), validate the entire
configuration and that participant before returning JSON or entering curses,
and carry one validated participant context through reads and transitions.
Open graph visibility is unchanged; validating the actor is not an ACL.

The existing Gate A implementation is useful authority/transition evidence,
but it is not a complete operational slice: its dynamic registration commands,
`--authority`/`--viewer` surface, and direct treatment of endpoint kinds do not
implement the confirmed team/role/route/member model. Gate B must not cement
those omissions in presentation. Before more source implementation, the plan
must specify the v11 configuration schema, configuration-versus-authority
source of truth, generation/change lifecycle, route resolution and handler
assignment, participant validation, initialization/open failure modes, and
the migration of the existing Gate A tests and CLI surface.

**Configuration-path clarification confirmed by Slawomir.** Configuration may
carry the protocol-derived generation in its filename or in a containing
directory. The canonical deployment form is the existing nested layout,
`mailbox/v11/baton.json`: it keeps the stable `baton.json` filename and aligns
with versioned mailbox/application discovery. The document itself still
declares protocol 11 and is validated against the client and authority; a path
component is organizational evidence, never a substitute for the handshake.

**Authority-handshake supersession confirmed by Slawomir.** V11 has no
separate `WORK.json`. The proposed read-only handshake file is removed from the
design. `baton.json` carries the stable authority UUID and database identity in
its instance/mailbox tree; `work.sqlite3` stores the same UUID plus its accepted
configuration digest and generation. Open validates those facts directly.

Copying `baton.json` therefore preserves the identity of that mailbox. Creating
a genuinely new mailbox generates a new UUID before generation 1 is accepted.
The correction plan must define a crash-safe bootstrap for that initial write,
but must not introduce a third identity/configuration document.

## 2026-08-14 — configuration correction C1 authorized

**Confirmed by Slawomir.** C1 may implement the pure strict v11 `baton.json`
schema and loader. The approved boundary has first-class participant and route
configuration; participant records carry display names, roles and capabilities;
routes name their role and handlers and kinds resolve through named routes.
The authority UUID/database identity lives in `baton.json`, `work.sqlite3` is
its fixed sibling, and no `WORK.json` is created or read.

C1 performs no authority mutation. It validates strict JSON, protocol and
generation fields, handle grammar, displays, participant/team membership,
role assignments, route/role/handler coherence, kinds and their route mapping,
and the fixed database identity/path. C2 acceptance, generation transitions,
and responsibility-stranding policy remain outside this authorization.

## 2026-08-14 — configuration correction C2 authorized

**Confirmed by Slawomir after C1 acceptance.** C2 may implement the authority
side of the configuration contract. Generation-1 initialization binds the
`baton.json` authority UUID and accepted digest/generation directly to the
sibling `work.sqlite3` with crash-safe refusal/retry behavior; it creates no
`WORK.json`. Later acceptance reads a generation+1 proposal through the
special bounded acceptance path while ordinary open continues to refuse any
unaccepted digest.

Acceptance is one audited transaction. Authority topology tables are the
projection of the accepted configuration; the event records old/new
generation, digest and structural changes. Only a participant holding the
configuration capability in the currently accepted generation may accept a
proposal, so a proposal cannot authorize its own acceptor. Handler reassignment
occurs only through a generation bump. A proposal that would strand open Work
or pending obligations refuses and names the affected records. Retired or
removed identities preserve historical meaning and cannot be silently reused.

C2 does not authorize the public CLI migration, route-resolution transition
changes, projection 2.0, or resumed Gate B work; those remain C3 and later.

## 2026-08-14 — configuration correction C3 authorized

**Confirmed by Slawomir after committing accepted C1/C2 as `fad96b1`.** C3
may migrate the public CLI boundary to the accepted instance configuration.
The global authority locator becomes `--config PATH`; the acting identity is
`--participant team.member`; `--authority` and `--viewer` are removed rather
than retained as aliases. Every ordinary read, mutation, and TUI launch opens
through the bound-config lifecycle and validates the configured participant
before producing JSON or entering curses. This validation establishes who is
asking and does not narrow the approved open-graph visibility model.

`init` consumes generation 1 from `--config` and creates its fixed sibling
authority. The explicit acceptance command (`regen`, backed by
`accept_config`) requires `--participant` and applies the current-generation
configuration-capability gate already accepted in C2. The mutable registry
commands (`register-team`, `register-member`, `register-kind`, and
`retire-kind`) are removed: accepted configuration generations are the only
topology writer.

C3 changes the launch/identity/configuration surface only. It does not yet
authorize C4 endpoint-resolution recording or handler projection, projection
2.0 shape changes, the full C5 fixture/test migration, or resumed Gate B work.
Stop after focused C3 evidence and review.

## 2026-08-14 — configuration correction C4 conditionally authorized

**Pre-approved by Slawomir, effective immediately when C3 passes reviewer
re-review.** No additional human approval round is required between clean C3
acceptance and C4 implementation.

C4 makes the accepted route configuration operational. Every use of a public
`team.kind` endpoint that establishes attention, an obligation, Current, or
Next resolves through the then-accepted route to its role and handlers and
records `(endpoint, route, role, handlers, configuration generation)` in the
committed event/obligation state. This includes initial Work creation and all
`+`, `@`, `=>`, and planned-Next operations; endpoint history must not be
partly resolved and partly bare. Later handler or route reassignment does not
rewrite that historical resolution.

Responsibility remains owed by the stable public endpoint, not personally by
the handler. Routes are accountability lookup, not an exclusive-access rule or
a dispatch pipeline: other members retain the approved team-wide visibility
and contribution model.

The current projection resolves Current/Next and other endpoint-bearing values
against the currently accepted configuration and exposes structured
`endpoint`, `route`, `role`, and `handlers` data. The JSON projection advances
to 2.0 and the envelope uses `participant`; obligations and links use the same
endpoint structure. The compact TUI continues to render the endpoint string in
its table columns and may expose routing detail on drill-in.

C5 scheduling/remaining fixture migration and C6 Gate B resubmission remain
separate. Stop after C4 evidence for reviewer sign-off.

## 2026-08-14 — workflow stories precede further TUI implementation

**Confirmed by Slawomir.** After C4, the next priority is the end-to-end
workflow suite in `WORKFLOW-TESTS.md`, driven through the public CLI and
versioned JSON projection. Heavy TUI implementation is blocked until the
approved operational stories can be expressed and pass through that machine
surface. If a workflow cannot be represented honestly in CLI/JSON, Baton does
not yet have stable semantics for a GUI to render.

The workflow phase may expose missing authority state, transitions, projection
fields, or unresolved rulings. Each discovery retains its failing workflow and
extracts a focused regression for the first broken phase/transition; both must
pass. The phase must not patch presentation around a missing engine operation,
weaken a workflow to match current code, or use TUI state as the only evidence
that a workflow works.

Existing small TUI checks may continue to guard already-built rendering and
refuse-before-curses behavior. No substantial new TUI navigation or interaction
surface is built until the CLI/JSON workflow gate is reviewed and accepted.
This supersedes any earlier sequencing that would move directly from the
configuration correction into Gate B/C6 TUI completion.

**Authorization clarification confirmed by Slawomir.** The CLI/JSON workflow
phase is pre-approved, conditional on a clean C4 reviewer sign-off. Once C4 is
accepted, `baton.reviewer` may release `WORKFLOW-TESTS.md` to the implementer
without another human review. Until that condition is met, C4 remains the
serial implementation item and the workflow document is preparation only.

## 2026-08-14 — classification default and compact presentation

**Confirmed by Slawomir after acceptance of the CLI/JSON workflow gate.** A
Work's classification is never represented as `null`. The canonical default
is the explicit value `unknown`; clients and agents must not infer absence or
special meaning from a missing/null value.

The protocol/JSON surface uses the full canonical word `unknown`. The TUI has
a separate presentation vocabulary capped at five display cells for this
column; the confirmed rendering for `unknown` is `unkwn`. Compact labels do
not become protocol identities and are not accepted as mutation values.

SQLite may encode the enum as integers or strings. That choice is an internal
storage detail: reads and audit records expose the canonical protocol value,
and storage encoding must not leak into JSON or TUI semantics.

This ruling settles classification's initial value and display budget. It does
not yet settle the separate operational-phase field, its enum, or its initial
and terminal transition rules.

## 2026-08-14 — operational-phase vocabulary, partially settled

**Confirmed by Slawomir during WS-1 vocabulary review.** `parked` is a
first-class operational phase for Work that has been deliberately suspended
and will not wake automatically. Its compact TUI rendering is `park`.
`parked` is distinct from ordinary queued Work and from Work waiting on a
recorded condition. `delayed` and `postponed` do not become additional
synonymous protocol phases.

The canonical phase `review`, if present in the final enum, renders as `rview`,
not `rev`; `rev` is readily read as “revision.” This correction supersedes the
earlier compact-label proposal made during discussion. The complete phase
enum, default phase, waiting/wake rules, and allowed transitions remain open.

**Risk clarification confirmed by Slawomir.** `parked` is retained for now,
but is intentionally dangerous: it names no dependency or other specific wake
condition, so Work may remain there indefinitely. Nothing may treat parking as
dependency-backed waiting or promise an automatic wake-up. The final
transition/UI design must keep that risk visible rather than making `parked` a
quiet substitute for classification, rejection, or an honest blocker.

**Enum and presentation approved by Slawomir.** Operational phase is a
non-null canonical value with this compact TUI vocabulary:

| Canonical JSON/audit value | Compact TUI value |
| --- | --- |
| `queued` | `queue` |
| `research` | `rsrch` |
| `waiting` | `wait` |
| `active` | `actve` |
| `review` | `rview` |
| `parked` | `park` |

New Work defaults to `queued`; creation may explicitly select another valid
phase. `open`/`closed` remains the independent lifecycle status, so there is
no redundant terminal `done` phase. Dependencies determine readiness and
blocking but do not rewrite operational phase. Passing Current likewise does
not silently change phase: any combined client action must commit and audit
both state changes explicitly.

Parking requires a non-empty reason, retains the one accountable Current, and
can resume only through an explicit `parked` to `queued` transition. The main
team/top-level projection exposes an always-visible parked count, and the TUI
renders that count in its summary so parked Work remains in the operators'
faces rather than disappearing into a filter. JSON exposes the same count for
agent parity. The complete authorization and allowed-transition rules remain
to be settled before WS-1 implementation begins.

**Waiting/wake clarification confirmed by Slawomir; supersedes the blanket
“dependencies ... do not rewrite operational phase” sentence above.** Entering
`waiting` requires a recorded specific wake condition. When that condition is
satisfied, the authority atomically transitions `waiting` to `queued` and
records an explicit `wake` audit event. This condition-bound wake is the only
dependency-driven phase change; dependencies do not otherwise rewrite phase.
It prevents loose ends from remaining falsely marked `waiting` after their
reason to wait has ended. `parked` remains the deliberate opposite: it has no
wake condition and returns to `queued` only by an explicit manual transition.

**Direct transition authority approved by Slawomir, with delegation held for
the clarification below.** A currently resolved handler of the Work's Current
route may explicitly change phase while the Work is open. Every phase change
is audited. The authority does not impose a false linear pipeline: ordinary
open phases may move between one another, including review/rework cycles.
`parked` may leave only through explicit `parked` to `queued`; `waiting` leaves
through its condition-bound audited wake; and closed Work refuses phase
changes. Creation may explicitly choose a valid phase and otherwise defaults
to `queued`.

These rules define direct handler authority, not exclusive personal control.
Slawomir additionally requires a handler to be able to delegate a decision to
another entity without necessarily transferring Current. That is distinct
from `@` consultation/required response and `=>` ownership transfer. The
delegation's scope, exercise, revocation, lifetime across pass/close, and audit
shape must be ruled before WS-1 implementation is released; delegation must
not create a second Current or silently broaden into general workflow control.

**Delegation simplification confirmed by Slawomir; supersedes the additional
scoped-delegation requirement immediately above.** Delegation is ownership
transfer: `=>team.kind` atomically passes Current and therefore transfers the
authority and responsibility to decide. Optional Next expresses the planned
return. Baton adds no second, micro-scoped decision-grant primitive. `@` remains
a required request for input while Current stays with the requester; the
responding endpoint supplies input but does not thereby acquire workflow
mutation authority. After `=>`, the former handler cannot keep acting as
Current, and the new Current route's resolved handlers hold direct transition
authority under the rules above.

**Wake-condition model confirmed by Slawomir; WS-1 semantics are now
settled.** `waiting` records one of two typed conditions:

1. aggregate Work readiness: at least one required gate is presently open,
   and wake occurs only when every required child and every explicit
   `blocked_by` Work is closed; or
2. one exact pending `@` response obligation, which wakes when that obligation
   is completed without granting its respondent mutation authority.

Entering dependency-backed `waiting` while no required gate is open, or
obligation-backed `waiting` with an obligation that is not pending, is refused
rather than creating a loose end. Satisfying only some of several Work gates
does not wake anything. The transaction that satisfies the last gate or named
obligation atomically changes `waiting` to `queued` and records `wake`; retry
and racing completion must not duplicate that event. An `@` obligation remains
semantically distinct from a dependency edge and does not join the Work
readiness predicate merely because it may be selected as a phase wake
condition.

The approved workflow expansion must now turn these rulings into executable
WF-01/WF-04 checkpoints plus focused authorization, transition, wake/race,
parking, projection, and reconfiguration regressions. Heavy TUI work remains
held; compact vocabulary and summary parity may be proved through the bounded
existing renderer/projection surface.

**Implementation-interpretation disposition by `baton.reviewer`.** Three
reported interpretations follow from the rulings and are accepted: creation
refuses `waiting` and `parked` because neither can omit its required condition
or reason; an obligation-backed wait names a pending obligation of that same
Work; and terminally closed Work refuses reclassification until explicitly
reopened. Mechanical truncation of the remaining canonical classifications is
not accepted as compact vocabulary and remains a human UX ruling before WS-1
can pass review.

## 2026-08-14 — complete Work authority matrix and classification labels

**Confirmed by Slawomir after the first WS-1 review; supersedes the unresolved
authority-matrix and compact-classification questions immediately above.**
Participation, visibility, and responsibility are separate. Open graph
visibility remains available to every configured participant, but neither
visibility, contribution, inclusion with `+`, nor an `@` obligation grants
workflow mutation authority.

The operation matrix is:

- a currently resolved handler of Current may classify, change phase, create
  `@` obligations, pass Current with `=>` and optionally set Next, change
  dependencies, create or attach child Work, and terminally close Work;
- after reopen restores Current, a currently resolved handler of that Current
  may perform the reopen;
- a resolved handler of the route named by one exact pending `@` obligation may
  respond to or otherwise dispose that obligation, but gains no other mutation
  authority;
- every configured participant may contribute ordinary messages, add `+`
  attention, and change only their own seen state; and
- every configured participant may read and drill through the open graph.

All workflow decisions above are checked against the live route-to-handler
resolution inside the committing authority transaction. `=>` changes who owns
those decisions; participation never substitutes for ownership. Machine
projections expose only the transitions actually available to the viewing
participant under this same live rule.

The complete canonical-to-TUI classification vocabulary is:

| Canonical JSON/audit value | Compact TUI value |
| --- | --- |
| `unknown` | `unkwn` |
| `suspected-defect` | `suspt` |
| `confirmed-defect` | `cnfrm` |
| `limitation` | `limit` |
| `duplicate` | `dupe` |
| `design-choice` | `desgn` |
| `rejection` | `rejct` |

These compact values are presentation only, never accepted protocol mutation
values. Unknown or unmapped canonical values fail visibly; clients must not
invent a label by truncation.

## 2026-08-14 — WS-2 immutable closure and reviewer-controlled verification

**Confirmed by Slawomir; supersedes every earlier rule and implementation
that permits reopening terminally closed Work.** Closure is an externally
observable terminal fact, not a status toggle. It may wake dependents, permit
downstream verification or release, bind a final dossier revision, and permit
dossier archival/removal. A later event cannot retract those consequences by
reopening the same Work.

Evidence that arrives after closure creates new Work with an audited
`follow_up_of` relationship to the closed record. That relationship preserves
history and context but does not gate workflow. Each affected consumer gains a
new explicit `blocked_by` edge to the follow-up Work; prior consumers are never
silently re-blocked. The closed Work, its disposition, and its old dependency
edges remain historical evidence. The v11 `reopen` operation and its automatic
re-block behavior are therefore removed rather than carried forward.

**Provider-outcome policy confirmed by Slawomir.** Provider closure records an
explicit satisfying or non-satisfying result; clients never infer that result
from classification or free-text disposition. Either terminal result ends that
provider gate and places the next decision in each affected consumer's court.
If it was the consumer's last open gate, dependency-backed `waiting` becomes
`queued`; with other gates open it remains waiting. The consumer's Current does
not move, and no provider result automatically classifies or closes consumer
Work. A satisfying result still requires consumer verification. A
non-satisfying result is visibly actionable and requires the consumer handler
to accept, work around, redirect, present more evidence, or close honestly;
it never appears as a delivered fix.

**Staged-verification policy confirmed by Slawomir.** A provider need not close
merely because it has a candidate solution. It keeps its Work open, publishes
the exact candidate/artifact, and creates separate exact `@` verification
obligations for whichever dependent-team routes it chooses. The provider
dependency remains open and unsatisfied: the obligation makes the selected
team actionable for testing without falsely clearing its blocked Work.

Verification responses carry feedback and evidence back to the provider.
They never vote, change classification, transfer Current, satisfy dependency
edges, or close Work automatically. The provider's responsible reviewer or
verifier chooses the evidentiary threshold: one team's result, every selected
team, or another explicitly judged threshold. As results arrive, that handler
may close with a satisfying result, continue review, request more evidence, or
resume research/implementation. A failed staged test therefore resumes work
while the provider record is still open; it creates no reopening problem.

**Verification-round clarification confirmed by Slawomir.** The provider
reviewer creates a round for one exact candidate and selects its exact verifier
routes. Three assignments display feedback progress as `0/3`, `1/3`, `2/3`,
and `3/3`. This fraction counts terminal feedback received, not confirmations
and not votes toward an automatic threshold. The projection also exposes each
assignment's state and reported result so `2/3` can visibly mean, for example,
one confirmation, one failure, and one pending assignment.

The reviewer may decide with no replies, one knowledgeable reply, every reply,
or any other evidence they judge sufficient. Changing the staged candidate
starts a new round; replies remain pinned to the exact candidate/round they
tested and never carry forward silently. Earlier rounds remain audit evidence.
Closing or abandoning a round explicitly withdraws any remaining assignments
and notifies their routes rather than leaving obsolete test work actionable.

**Time-based decision clarification confirmed by Slawomir.** A verification
round may carry an optional reviewer-selected `review_at` time. Reaching it
only makes the round due and notifies its responsible reviewer; it never
closes, satisfies, votes, fabricates feedback, or withdraws assignments. The
reviewer may decide that a candidate has had sufficient exposure without
negative reports—even at `0/N`—and close it as satisfying on that evidence.

That close records the round, exact candidate, received-versus-assigned count,
reported outcomes, elapsed exposure, pending assignments explicitly withdrawn,
and the reviewer's disposition/rationale. Baton records the basis of the
judgment rather than claiming certainty. A later contradictory result creates
follow-up Work under the immutable-closure rule; it never rewrites the earlier
evidence or reopens the record.

**Feedback-adjudication clarification confirmed by Slawomir.** A verifier's
report and the provider reviewer's assessment are separate immutable facts.
The verifier reports what it observed and attaches evidence. The provider
reviewer may accept that report as relevant evidence, reject it as invalid,
stale, unrelated, or attributable to the consumer's own system, or leave it
inconclusive. Rejecting a reported failure does not rewrite it into a pass and
does not claim the reporter observed something else.

`N/total` counts assignments that returned terminal feedback regardless of
the reviewer's assessment. Projections show both axes—for example, `failed /`
`rejected: consumer configuration error`—so receipt progress is never mistaken
for supporting or opposing evidence. The reviewer decides what weight, if any,
each response receives and records a rationale. A changed assessment is a new
superseding audit act, never an edit of the original report. No combination of
raw reports or assessments closes or resumes Work automatically.

**Due-for-review behavior confirmed by Slawomir.** When `review_at` arrives,
the round becomes visibly due and the responsible reviewer receives an
actionable review event. Work, phase, Current, dependencies, assignments, and
candidate state do not transition. The reviewer must make and audit the next
decision:

- extend the same candidate's testing period by setting a later `review_at`,
  retaining all feedback and pending assignments;
- accept the evidence as sufficient and terminally close the provider Work
  with an explicit satisfying result, rationale, round summary, and explicit
  withdrawal of feedback assignments no longer needed; or
- when evidence shows the candidate is not ready, continue/resume provider
  work through an explicit phase or Current transition.

Repeated extensions are visible history, not a hidden timer reset. No elapsed
duration, lack of feedback, response count, reported outcome, or assessment
selects one of these branches automatically.

**Verification vocabulary confirmed by Slawomir.** A verifier observation is
exactly `passed`, `failed`, or `unable`. The provider reviewer's assessment is
separately exactly `accepted`, `rejected`, or `inconclusive`. An assignment
that ends without a verifier report because the reviewer no longer needs it is
`withdrawn`. These are canonical JSON and audit values; compact TUI labels may
be added later without changing them.

The round progress fraction is `reported/assigned`: only assignments that
returned one of the three verifier observations increment its numerator.
Withdrawal never fabricates feedback and never increments that count. The
projection exposes withdrawn assignments and a separate withdrawal count, so a
round closed after one of three teams reports remains `1/3`, with two
withdrawals visible. Closure must not leave an assignment actionable.

## 2026-08-14 — WS-2 decision-challenge rulings

**Confirmed by Slawomir after the implementer's adversarial review.** Due is a
level-triggered actionable state derived from `review_at` and current time. It
appears in the responsible route's actionable projection and in an
always-visible due count; a blocking wait may return when the nearest deadline
arrives without mutating authority. Reaching time creates no audit row and
requires no scheduler. The later explicit extend, abandon, resume, or close is
the audited decision. Pure reads and restarts therefore cannot duplicate or
lose a one-shot due event because no such event exists.

A staged-verification assignment is a specialized exact `@` obligation. It
shares obligation identity, exact endpoint cardinality, route-resolution
snapshot, live handler authorization, pending/actionable semantics, and common
projection. Its structured verification detail records round, candidate,
observation, evidence, assessment history, and withdrawal, and it completes by
the specialized report or withdrawal operations rather than ordinary
respond/dispose. This subtype is ineligible as a WS-1 obligation-backed waiting
condition: feedback never automatically changes provider Work phase or wakes
it. The responsible reviewer explicitly decides the next Work transition.

New required `blocked_by` edges may target only open Work. A terminal record
cannot become a new blocker; later unresolved evidence uses new open Work with
non-gating `follow_up_of`, then an explicit required edge to that open record.
Existing edges and their terminal outcomes remain historical evidence.

**Every terminal close requires exactly one explicit outcome:
`satisfying` or `non-satisfying`.** This rule is independent of graph shape,
incoming-edge count, verification history, classification, and disposition
prose. The outcome records whether the terminal conclusion met the Work's
purpose. Either outcome ends every gate served by that Work; dependent and
parent handlers decide what to do with the result. Omission, an unknown value,
or attempting to infer the outcome from prose refuses.

Closed Work refuses further workflow mutation and new carrying discussion or
obligation activity. Reads, search, drill-through, breadcrumbs, historical
messages/events/links, and follow-up traversal remain available. A participant
may still advance only their own seen cursor over closed history, and creation
of separate new Work may point back through `follow_up_of`; neither operation
mutates the closed record.

## 2026-08-14 — independent-lane closure and live dependents

**Confirmed by Slawomir through the PushCoin/Lang scenario.** When Work closes,
every pending exact `@` obligation carried by that Work is atomically
`withdrawn`. Withdrawal removes the request from the owed route's actionable
state and is recorded with its route-resolution and close context. It does not
erase the request, its discussion, or any response that committed first.
Response/disposition/report versus close is serialized so exactly one legal
terminal state wins; no response may append to closed Work.

Withdrawal affects only the closing Work's requests. If another team already
accepted the discovery and created its own Work, that provider Work is an
independent lane: consumer closure never classifies, phases, parks, passes,
closes, rejects, or otherwise decides it. The provider may continue because a
locally resolved consumer report still reveals an API, UX, documentation, or
design defect that could trap other users.

Active provider projections expose one `DEP` counter: the number of open Work
records currently depending on this Work. Drilling the counter lists only
those live dependents. When a consumer closes it disappears from `DEP`; no
total or historical-dependent counter appears in the active table. Dependency
creation, consumer closure, obligation withdrawal, and all former relationships
remain in the journal/audit so a deliberate history review can explain why the
live count changed. The historical edge is evidence, not live demand.

## 2026-08-15 — WS-3 selected as the next serial phase

**Confirmed by Slawomir after WS-2 acceptance.** The next semantic slice is
WS-3, atomic provider deduplication, before first-class discussion labels,
effectively-once operation ids, dossier binding, or substantial TUI work.

The observed gap is that a provider accepting an external report currently
performs separate acts to associate the report with provider-owned Work and to
make that provider Work an explicit blocker of the consumer Work. A crash,
refusal, or race between those acts can leave context without the required
gate, or a gate without the association that explains it. WS-3 must define one
authorized transaction whose committed result is whole and whose refusal
leaves neither half.

This selection does not yet settle the public operation's shape. The design
pass must challenge whether an honest association can be represented before
WS-4 first-class discussions and `#WORK` labels exist, or whether WS-3 needs a
narrow Work-to-Work relation, a reordered dependency, or another explicit
boundary. It must also resolve actor authority, exact inputs and output,
idempotence/retry posture, N-consumer convergence, cycles, closed targets,
configuration changes, concurrent deduplication, audit identity, and the
consumer/provider projections. No implementation is authorized until that
shape is reviewed and any product choice is confirmed.

## 2026-08-15 — WS-3 atomic-acceptance rulings

**Confirmed by Slawomir after review of `WS3-DESIGN.md`.** A pending exact `@`
response obligation grants the live handler of its named route one narrow,
one-use authority to accept that request by atomically gating exactly the
requesting Work on provider Work. The grant comes from the consumer handler's
explicit request, changes no Current, grants no general consumer ownership,
and expires when that obligation is responded, disposed, withdrawn, or
accepted.

Accepting `--into` existing provider Work requires that request-route authority
and an open provider Work owned by the obligation endpoint's team. It does not
also require the actor to handle the provider Work's Current: new reports must
still converge after the provider baton has moved from bug intake to research
or implementation. The accept act records the provider's live Current
resolution as evidence, not as a second authorization gate.

An accepted request has the distinct terminal obligation state `accepted` and
names the provider Work structurally. Its dependency edge records nullable
`via_obligation` provenance; ordinary manual blockers keep NULL. This narrow
provenance answers why the gate exists without creating WS-4's reusable
discussion relation or `#WORK` labels.

Atomic `--create` may optionally attach the new provider Work beneath a parent
only when the accepting actor separately passes the existing live handler gate
for that parent's Current. Root creation remains available without that
additional authority.

Acceptance follows the existing typed-wait rule. If the consumer is waiting on
the accepted obligation itself, acceptance atomically wakes it to `queued`
after installing the new dependency; that blocker keeps readiness false and
the consumer explicitly decides whether to enter gates-waiting. A consumer
already waiting on all gates does not wake merely because another gate was
added. No automatic conversion between wait types occurs.

Compound audit order must be truthful. For `--create`, total sequence order
must establish provider Work no later than the acceptance that names it. The
primary `accept` act may itself serve as the creation act when `created: true`,
recording all creation fields and providing the new Work's creation sequence;
a distinct consumer-visible response-message act may follow inside the same
transaction when two messages need separate sequence ids. A nested event
layout that sequences `accept` before a later `create_work` act is forbidden.

## 2026-08-15 — WS-4 first-class discussion design authorized

**Authorized by Slawomir after committing accepted WS-3.** WS-4 is the next
serial phase. It begins with a design/ruling round only; source, schema, tests,
and migration remain held until that design is reviewed and its unresolved
product choices are confirmed.

The design must replace today's Work-local message container with the already
confirmed semantic model: one discussion carries ordered messages and may be
related to many Work records through inert `#WORK` labels; one message belongs
to exactly one discussion; labels provide reusable context and never gate,
move Current, satisfy an obligation, or alter readiness. Required dependency
edges remain the sole workflow gates.

The pass must revalidate the older discussion rulings against the implemented
WS-1 through WS-3 authority rather than transcribing them mechanically. In
particular it must settle:

- discussion identity, creation, first-message atomicity, label add/remove,
  last-label/orphan behavior, ordering, audit payloads, and public JSON;
- the authority to apply a local or cross-team `#WORK` label, including the
  rule that a member cannot mutate another team's Work merely by knowing its
  id;
- `@`, `+`, and `=>` when a discussion has zero, one, or several labels:
  explicit Work selection, responsibility/participation state, follower
  promotion, and whether any operation may affect several Works;
- per-member seen cursors and `New` across multiply labelled discussions and
  containment descendants, with each message counted once at a common
  ancestor;
- visibility as open/noise-scoped rather than secret: default tables must not
  become an all-team stream, while deliberate traversal of relevant links and
  discussions remains possible;
- how WS-3 acceptance relates the incoming discussion to provider Work while
  preserving its separate explicit dependency edge and `via_obligation`
  provenance;
- discussion behavior when some labelled Work is terminal and other labelled
  Work remains open, including whether posting, relabelling, or removing the
  final live context is allowed;
- announcement `+*.*` behavior without a notice object, endpoint expansion,
  per-member deduplication, and zero responsibility/readiness effects; and
- fresh-schema versus compatibility boundary, refusal/race/retry/crash
  behavior, deterministic pagination/snapshots, and the smallest source plus
  packaged CLI/JSON workflow battery.

The design must explicitly identify contradictions, accidental coupling to
the current `messages.work` / `seen.work` representation, and any ruling that
cannot be implemented honestly without WS-5 operation ids or WS-6 dossier
binding. It must not start either later slice or substantial TUI work.

## 2026-08-15 — WS-4 dispositions confirmed except terminal/orphan boundary

**Confirmed by Slawomir after `WS4-DESIGN.md` review.** Any configured member
may add or remove a `#WORK` label for Work owned by their own team. Knowledge
of another team's Work id grants no labelling authority.

An operator that acts on Work affects exactly one currently labelled Work and
must pass that operation's existing Work authority gate. An omitted `--on` is
resolved only when the actor has exactly one **eligible** labelled Work for
that operation; foreign or otherwise unauthorized labels do not create false
ambiguity. Zero or several eligible Works refuse and require an exact `--on`;
an explicit selection outside the discussion's current labels refuses.

Discussion-team participation is distinct from responsibility. A team's own
`#WORK`, an incoming `@`, an incoming `=>`, or `+` records that team once as a
participant so the discussion remains discoverable after a particular
obligation ends. Participation is monotonic in WS-4, affects attention and
personal discovery only, and grants neither workflow authority nor access
control. The Work-scoped obligation remains the complete `@` accountability
lifecycle: pending to responded, disposed, accepted, or withdrawn.

Seen state is one monotonic cursor per member per discussion. Work-level `New`
counts the distinct unseen messages in discussions labelled to that Work or
its containment descendants. The decomposable projection exposes `own`, each
child's truthful count, `overlap`, and `total`, where `overlap` is the raw-sum
duplicate excess and `total = own + sum(children.new) - overlap`. A separate
participating-discussion surface uses the same cursor without adding those
messages to unrelated Work tables.

WS-3 acceptance atomically ensures the consumer's originating discussion is
labelled to provider Work while preserving the separate explicit dependency
edge and `via_obligation`. A pre-existing provider label is success, audited as
`existing`; otherwise the transaction audits `added`. Ordinary responses also
return to the originating discussion, and public obligation state names it.

WS-4 uses a fresh schema with no migration. It lands in two separately
reviewed slices. Slice A establishes the first-class model and explicit public
discussion/label/plain-post/seen/New surfaces; any Work-addressed bridge is
internal and temporary, never a certified public API. Slice B replaces the
operator and acceptance surfaces and removes that bridge before WS-4
acceptance. WS-5, WS-6, deployment, and substantial TUI work remain held.

**Still open:** whether unlabelled/orphan discussions are legal and whether a
discussion whose labels are all terminal remains postable. No implementation
is authorized until that last boundary is confirmed and this hold is
explicitly superseded.

## 2026-08-15 — WS-4 live-context discussion boundary

**Confirmed by Slawomir; supersedes the final hold immediately above.** A
discussion always has explicit Work scope. Creation requires at least one
authorized `#WORK` label, and removing its final label refuses. Labels may
name terminal Work, but a new plain message requires at least one currently
labelled open Work. Carrying operators additionally require their one exact
eligible open Work under the already confirmed authority rule.

When every labelled Work is terminal, the discussion remains durable,
readable, searchable, and navigable but is not postable. Continuing or
refining the subject requires new open Work—normally an immutable follow-up—
to be created and labelled first. A discussion spanning terminal and open Work
remains postable, so conversation may cross phases without reopening history.

The reason is scope integrity: allowing messages to accumulate after all Work
scope has ended would let the contract of the discussion drift outside the
work graph. New Work makes the changed contract explicit, schedulable, and
visible in readiness and ownership projections. Labelling does not itself
reopen, gate, or otherwise mutate terminal Work.

## 2026-08-15 — iteration is an invariant of open Work, not another state

**Clarified by Slawomir during WS-4 planning.** No new `candidate` phase or
linear lifecycle is requested. The existing open-phase set must remain
comfortably iterative. Ordinary open Work may move repeatedly among `queued`,
`research`, `active`, and `review` in any useful order, including review back
to active implementation, further research, another review, and another
candidate cycle. `waiting` and `parked` retain their explicit exit disciplines
but return Work to `queued`, from which iteration continues.

Candidate attempts and independent verification rounds are records within
open Work, not terminal states and not a one-way phase pipeline. A report,
assessment, due time, completed feedback set, or failed candidate never
automatically changes phase, changes Current, or closes Work. The responsible
handler explicitly decides whether to continue review, extend or abandon a
round, resume research/implementation, publish another candidate, wait, park,
or close with an honest terminal outcome.

JSON and TUI clients must expose this as an ordinary cyclic workflow. They may
show a common path for convenience, but must not imply or enforce
`research -> implementation -> done` as the only progression. Workflow tests
must preserve at least one multi-iteration candidate/review/rework cycle.

## 2026-08-15 — assigned Work is revised only by its current handler

**Confirmed by Slawomir while defining revision and cancellation behavior.**
Assignment freezes outsiders out of the Work contract; it does not freeze the
contract against responsible iteration. Once Work has a Current handler, no
other member—including its requester, parent handler, reviewer, or a
discussion participant—may edit that Work's plan, requirements, or acceptance
contract directly.

Participants may propose corrections and refinements in a labelled discussion.
The Current handler evaluates that evidence and may incorporate the agreed
change as an append-only Work revision. The revision preserves the Work
identity, prior revisions, discussion provenance, dependencies, and Current;
public JSON must make both the effective revision and ordered revision history
unambiguous. The write must name the expected prior revision so concurrent or
stale edits fail rather than overwriting one another. Transferring Current
transfers this editing authority.

A revision may correct or refine how the existing result is delivered. It
must not hide a new independently accountable result, test, proof, or review
contract: that is separate child Work, even when it shares the same handler and
discussion. A message that changes no required action remains discussion
evidence only. Terminal Work remains immutable and is continued through new
follow-up Work, never reopen or post-terminal revision.

This ruling does not yet settle cancellation authority or cancellation's
structured terminal disposition. Those remain separate product decisions; no
implementation may infer them from revision authority.

## 2026-08-15 — cancellation is Current-owned accelerated completion

**Confirmed by Slawomir; supersedes the binary-only terminal-outcome rule for
cancellation and resolves the open cancellation boundary immediately above.**
Cancellation is not a separate lifecycle form or transition. It uses the same
atomic terminal close mechanism as ordinary completion, with `cancelled` as a
third machine-readable outcome alongside `satisfying` and
`non-satisfying`. A cancelled close requires a non-empty rationale; clients
never infer cancellation by parsing prose attached to another outcome.

Discussion may propose, refine, or negotiate cancellation, just as it may
propose a Work revision. Only the resolved Current handler may commit the
close. Requesters, parent handlers, reviewers, and other participants cannot
terminate assigned Work by editing it or acting around Current; an authority
change must first transfer Current through the ordinary audited mechanism.

All three outcomes share the existing close transaction: clear Current and
Next, withdraw pending obligations and verification assignments, finish the
Work's dependency gate, propagate readiness, and make the Work immutable.
Cancellation does not cascade. Open children retain their own Current and must
be concluded separately before their parent may close. Dependents observe the
exact `cancelled` outcome, resume when their gate condition permits, and make
their own independent decision. Renewed effort is separate follow-up Work,
never reopening the cancelled record.

## 2026-08-15 — cancellation pinned for a future slice (relayed during Slice B)

**Pinned by Slawomir, relayed by the reviewer mid-Slice-B; the active slice is
unchanged.** Cancellation is an atomic close with terminal outcome `cancelled`
and a required rationale, committed only by the Work's Current handler. There
is no cascade and no child bypass. Implementation remains HELD until after the
Slice B review.

## 2026-08-15 — every terminal close has a structured outcome and rationale

**Confirmed by Slawomir; supersedes the three-outcome vocabulary and the
exceptional rationale rule in both cancellation sections immediately above.**
There remains one atomic close mechanism, but its terminal outcome is exactly
one of `satisfying`, `non-satisfying`, `rejected`, or `cancelled`. Every close,
including a satisfying one, requires a non-empty rationale. Terminal decisions
are durable review evidence and may not rely on readers reconstructing the
reason from discussion history.

The outcomes answer different questions:

- `satisfying`: accepted Work concluded and met its contract;
- `non-satisfying`: accepted Work was attempted or evaluated but did not meet
  its contract;
- `rejected`: the Current handler declined the report or premise during
  intake/triage—for example invalid, out of scope, not reproducible, or not
  this team's responsibility; and
- `cancelled`: valid Work was accepted or underway but deliberately stopped
  because it was no longer wanted.

Reasons may carry additional structured requirements without multiplying the
top-level outcome vocabulary. In particular, a duplicate is initially a
`rejected` close whose structured reason names the canonical Work through an
explicit `duplicate_of` relation; free text alone is insufficient. All four
outcomes otherwise share the authority, child, dependency, withdrawal,
immutability, and follow-up semantics of the ordinary close transaction.

## 2026-08-15 — Work revisions store complete content; structure comes from external templates

**Confirmed by Slawomir; resolves the remaining Work-revision content
boundary without authorizing its implementation during Slice B.** Baton v11
does not bake separate description, requirements, or acceptance fields into
the core Work schema. A revision promotes one durable discussion message as a
complete replacement statement of the Work contract. It may not be an
incremental prose patch such as “change B to D”: the effective revision must
be understandable directly through JSON without replaying earlier messages.

The append-only revision record names the Work, new revision number, expected
prior revision, promoted message, Current actor, rationale, and audit metadata.
Only Current may commit it under the previously confirmed compare-and-swap and
authority rules. The promoted message's rendered bytes are the durable
contract content; dossier files remain supporting plans, scripts, evidence,
and proofs rather than a mutable substitute for the audited revision.

Reusable structure belongs to an external template layer. A template is a
versioned file or bundle with placeholders to fill in—for example a bug
report, implementation plan, release gate, research question, or the finding
folder conventions used by this repository today. Templates may standardize
sections, validation, rendering, or machine-readable fields without changing
the Baton protocol. Future revisions may record immutable template identity,
version, and digest as provenance, but the fully rendered content remains
self-contained in Baton so historical Work never depends on a template still
being installed or unchanged.

## 2026-08-15 — close-outcome vocabulary refined for a future slice

**Refined by Slawomir, relayed by the reviewer mid-Slice-B; the active slice
is unchanged.** The terminal close outcomes become `satisfying`,
`non-satisfying`, `rejected`, and `cancelled`; all require a rationale. A
duplicate rejection additionally requires `duplicate_of` naming the
surviving Work. A future WF-10 covers all four outcomes. Implementation
remains HELD until after the Slice B review.

## 2026-08-15 — Work-revision mechanism pinned for a future slice

**Pinned by Slawomir, relayed by the reviewer mid-Slice-B; the active slice
is unchanged.** A Work revision PROMOTES one complete durable discussion
message into the append-only revision history; there are no fixed contract
fields. Structure comes from external versioned templates; the rendered
content stays self-contained. Implementation remains HELD until after the
Slice B review.

## 2026-08-15 — WS-5 effectively-once retry selected for design next

**Confirmed by Slawomir after the Work-revision slice was accepted.** Plan
WS-5 next, before WS-6 dossier binding, deployment/migration, or further TUI
expansion. This authorization is for a design and challenge pass only; it does
not release implementation.

WS-5 must replace the current documented “read before retry” limitation with a
real client-supplied operation identity for mutations. If a mutation committed
but its response was lost, retrying the same semantic request under the same
operation identity must recover the one committed result without performing a
second effect or consuming another sequence. Reusing the identity for a
different request must fail closed. Reads remain pure and need no operation
identity.

The design must settle the identifier's grammar and scope, whether it is
mandatory on every public mutation or how an optional convenience can still
state its weaker guarantee honestly, semantic request fingerprinting, exact
retry response shape, permanent versus bounded retention, and coverage of
configuration/init operations. It must define the one-transaction storage and
race algorithm, including simultaneous identical attempts, conflicting reuse,
commit-then-response-loss, refusal-before-commit, crash/restart, configuration
reassignment, and replay after later Work state has changed. Any unresolved
product choice returns for ruling before source changes.

## 2026-08-15 — WS-5 effectively-once retry design approved

**Confirmed by Slawomir after the corrected design passed review; supersedes
the design-only implementation hold immediately above.** The complete contract
is `WS5-DESIGN.md`; R76–R81 and the accepted review are recorded in
`review-2026-08-15T15-27-39Z.md`,
`review-2026-08-15T15-31-29Z.md`, and
`review-2026-08-15T15-35-09Z.md`. The approved product dispositions are:

- operation identity is an optional caller-supplied opaque UTF-8 token,
  unique per validated participant; agents and automation should normally
  retain and supply one, while an id-less call remains explicitly in the
  weaker read-before-retry tier;
- identity reuse is checked against a canonical semantic fingerprint of actor,
  operation, and validated typed input, excluding dynamic resolution output;
- a successful protected mutation, its domain event when any, its replayable
  result, and its operation record commit atomically. Exact retry is a pure
  replay; conflicting reuse refuses. Refusals record nothing and do not poison
  the identity; successful no-ops consume it without inventing a domain event;
- current accepted configuration validates the participant before replay.
  Removed identities receive no replay carve-out. Later Work state does not
  invalidate a replay that passed the current identity gate;
- every mutation result exposes exactly one `operation` shape: `null`,
  `{id, state: "committed"}`, or `{id, state: "replayed"}`. The stored domain
  result and original event sequence remain stable across replay;
- operation records are retained permanently for this protocol. Their own
  dense `recorded` cursor orders `operation-log`; nullable domain-event `seq`
  is provenance only and remains untouched by successful no-ops or replays;
- config regeneration participates in the same guarantee. Fresh `init` gains
  a required participant validated against the proposed generation-1
  document; protected re-init on an existing authority first applies the
  current-generation identity gate and then performs exact/conflicting lookup;
  and
- the executable contract is a separate WF-12 source-and-packaged battery,
  preserving accepted WF-09 unchanged.

This approval releases only the bounded WS-5 implementation gate recorded in
`PLAN.md`. WS-6, dossier/template binding, deployment, migration, and further
TUI expansion remain held.

## 2026-08-15 — WS-6 dossier binding shape: permanent records and a human open index

**Confirmed by Slawomir while WS-5 implementation is active; this pins WS-6
design point 1 only and does not release WS-6 implementation.** A dossier's
canonical repository location exists from creation and remains indefinitely:

```text
work/
  open/
    finding-friendly-name -> ../records/YYYY/MM/finding-stable-name
  records/
    YYYY/
      MM/
        finding-stable-name/
```

The year/month is chosen at creation and the canonical record path does not
move when Work changes phase or becomes terminal. The record holds the finding,
plan, progress, append-only reviews, reproductions, scripts, fixtures, data,
and other durable evidence. Repository growth and large-asset policy are later
operational concerns; this ruling makes the dossier itself permanent.

Baton Work bindings, messages, handoffs, reviews, and cross-references use
only the configured repository identity plus the canonical repository-relative
`work/records/...` path. They never use `work/open/...`, never require an
absolute local checkout path, and do not require a Git commit merely to keep
the evidence reachable. An immutable Git revision may later be recorded as
additional provenance, but is not the primary locator.

`work/open/` is a deliberately maintained human convenience view for sweeping
dossier-backed work outside Baton. Its relative symlinks are not protocol
state, not an agent communication address, and not an authority for Work
lifecycle. Closing Baton Work and removing its open symlink need not be atomic;
a terminal record left there is merely cleanup-pending. Cleanup unlinks only
the verified symlink and never recursively deletes or traverses its permanent
record. No Baton/filesystem reconciliation checker is required in WS-6.

Not every lightweight Baton Work needs a dossier or an open symlink. Once a
dossier exists, however, its canonical record path is the stable binding and
must not be renamed as a lifecycle operation. Later corrections to terminal
evidence are explicit history or follow-up evidence, never silent rewriting.

## 2026-08-15 — WS-6 binding authority and open-record semantics

**Confirmed by Slawomir; resolves WS-6 design points 2 and 3 without releasing
implementation.** A Work creator may establish its initial canonical dossier
binding atomically with Work creation, including when routing immediately
makes another endpoint Current. After creation and while Work remains open,
only the resolved Current handler may attach a previously absent binding or
correct/supplement an existing one. Discussion participants, requesters,
reviewers, parent handlers, and other outsiders may propose a change but cannot
commit it. Transferring Current transfers this authority.

Every post-creation binding change is append-only, names the expected prior
binding revision, carries a non-empty rationale, and preserves the complete
ordered history. Stale or concurrent changes refuse rather than overwrite.
Normal lifecycle does not revise the canonical path; correction exists for an
erroneous locator or additive provenance, not for moving a dossier at close.
Terminal Work freezes its binding history. A later problem creates explicit
follow-up Work and corrective evidence rather than a privileged locator
rewrite or reopening the terminal record.

An open binding identifies a deliberately mutable working-tree dossier. Its
files may be added, revised, or removed as the investigation progresses; Baton
does not hash-pin, ingest, or mirror those bytes. The canonical
`work/records/...` path itself is stable under the preceding ruling and must
not move. If the path is temporarily unavailable or mistakenly disappears,
the Work binding remains valid protocol state and the Baton authority remains
healthy: missing evidence is a visible repository/operational problem, not
message damage, quarantine, or authority corruption. No filesystem observation
may silently change Work state or binding history.

## 2026-08-15 — WS-6 closure does not relocate or seal dossiers

**Confirmed by Slawomir; supersedes the earlier proposed closure choice between
a required Git locator and an explained absence.** The permanent-record shape
removes that fork. Closing bound Work leaves its configured repository identity
and canonical `work/records/...` path unchanged. There is no archive move,
working-tree-to-Git conversion, required commit hash, sealing transaction, or
second “no durable locator” rationale.

An immutable Git commit may be appended by Current while Work is open as
optional provenance, but it is not required for closure or later navigation.
Every terminal close already carries its mandatory outcome rationale; WS-6
does not add another rationale merely because no Git revision was recorded.
Lightweight Work that never needed a dossier closes normally with no binding.
Bound Work closes with its existing append-only binding history and that
history then becomes terminally immutable under the preceding authority rule.
Removing an optional `work/open/` human-index symlink is later repository
housekeeping and has no Baton transition semantics.

## 2026-08-15 — WS-6 artifact addressing and validation boundary

**Confirmed by Slawomir; resolves WS-6 design points 5 and 6 without releasing
implementation.** Evidence that belongs to a bound dossier is referenced by a
normalized relative path beneath that dossier. The immutable message/reference
record also names the binding revision against which the path was published,
so a later append-only locator correction cannot silently reinterpret an old
reference. Resolution expands to the configured repository identity plus the
canonical `work/records/...` path; it never passes through `work/open/` and
never stores an absolute checkout path.

An independent configured-repository/root plus normalized relative path
remains legal for a resource that genuinely does not belong inside the Work's
dossier. This is an explicit independent reference, not an implicit second
dossier binding. Neither reference form hash-pins, ingests, copies, or makes
the referenced bytes part of Baton authority. Movement or disappearance is
ordinary external-reference failure and does not damage the message, Work, or
mailbox.

The committing transaction validates only protocol facts: acting authority,
expected binding revision, known configured repository/root identity, reference
shape, normalized relative path, and containment syntax (no absolute path,
empty component, `.`/`..`, or escape). It does not stat the path, traverse a
symlink, open Git, require a mounted checkout, or persist an availability
observation. Canonical reads therefore depend only on SQLite authority state.
WS-6 adds no `available`/`missing`/`different revision`/`unchecked` vocabulary,
background checker, or implicit repair. A client may encounter and display an
ordinary navigation error when a human asks it to open external evidence, but
that result is not authoritative state and performs no Baton mutation.

## 2026-08-15 — dossier templates are external team-owned scaffolds

**Confirmed by Slawomir; resolves WS-6 template provenance by excluding it
from the protocol.** Baton does not define, store, validate, identify, version,
or digest dossier templates. A Work revision remains complete and
self-contained in Baton; a dossier binding identifies the permanent repository
record, not the scaffold that may originally have created it.

Repository tooling may ship an initial standard finding scaffold. Its minimum
convention is a directory bundle containing `REPORT.md`, `PLAN.md`, and
`PROGRESS.md`, and it may include or create additional structure such as
reviews, tests, reproductions, scripts, fixtures, or `data/`. The template may
itself contain a repository-side manifest, placeholders, rendering rules, or
lint policy, but none of those become Baton authority or protocol schema.

Teams own their copies of these scaffolds. They may extend, fork, replace, or
specialize them as their work evolves; useful conventions may later flow back
into the shipped standard without changing old Work, old dossiers, or Baton
compatibility. Git records the actual rendered files and their evolution. Any
scaffold command or repository lint is an external convenience and must not be
required to reconstruct Baton Work history.

This future-facing convention does not rename or rewrite the existing finding
folders during the active v11 implementation. Repository migration and the
exact scaffold/creation command remain separately planned operational work.

## 2026-08-15 — clarification: the dossier template is an instructional Markdown file

**Clarified by Slawomir; supersedes the “directory bundle” and automatic
rendering implications in the immediately preceding template ruling.** A
finding template is a versioned Markdown instruction/pattern describing how an
implementer is expected to turn an accepted report or research result into a
managed dossier. It is not a directory copied verbatim, a protocol object, a
machine-required manifest, or a fixed renderer input.

The implementer reads the template together with the actual report/research
and creates the appropriate permanent record scaffold. The standard pattern
expects at least `REPORT.md`, `PLAN.md`, and `PROGRESS.md`; the implementer adds
context-appropriate files and directories—such as reviews, tests,
reproductions, scripts, fixtures, or `data/`—when the work requires them. The
template defines responsibilities, content expectations, and management
conventions rather than pretending every finding has the same physical tree.

Teams may evolve or specialize their Markdown instruction file and may feed
successful conventions back into the standard. Baton neither knows which
template was followed nor validates the resulting filesystem shape. Git and
repository review own the resulting dossier; Baton retains only its canonical
binding and self-contained Work/discussion history.

## 2026-08-15 — standard templates ship with the CLI and are vendored at bootstrap

**Confirmed by Slawomir; completes the WS-6 template distribution boundary
without releasing implementation.** The Baton source repository owns the core
numbered Markdown patterns under top-level `tmpl/`, for example
`tmpl/work-basic-1.md`. Materially changed instructions receive a new numbered
file rather than silently rewriting the earlier edition.

The build includes the core template files in each exact versioned CLI product
release beside `bin/`, `doc/`, and `conf/`:

```text
app/baton-cli/v<major>/v<full-version>/tmpl/
```

Project bootstrap copies the selected core templates into that repository's
own top-level `tmpl/` and creates the initial `work/open/` and `work/records/`
structure. It does not symlink the project to the installed release, does not
make the project depend on `~/baton`, and refuses rather than overwriting a
conflicting existing file. Installing a newer Baton release never silently
updates a project's templates; adoption or import of a newer standard is an
explicit repository change.

After bootstrap, the project owns its vendored templates and repository policy
selects the current default. Teams may add local numbered variants and later
propose useful conventions back to the shipped standard. Template files are a
versioned CLI-product asset and repository convention, not a protocol version,
mailbox authority record, or requirement for reading historical Work. Source
and packaged bootstrap behavior must use the same template bytes and produce
the same initial filesystem shape.

## 2026-08-15 — WS-6 preserves configured roots as the portable address vocabulary

**Confirmed by Slawomir; clarifies the approved repository-identity/local-
resolver ruling.** A Baton authority spans many teams and repositories, so the
durable address is not a bare repository-relative path and is not inferred
from the Work's team. It is always a configured root id plus a normalized path
relative to that root, retaining the useful protocol-10 address concept:

```json
{
  "root": "pushcoin",
  "path": "work/records/2026/08/finding-x"
}
```

`baton.json` declares the portable root identifiers accepted by the authority.
A root normally identifies a repository checkout for dossier use, but it is a
general configured base and is independent of team routing: one team may use
several roots and several teams may reference one root. Dossier bindings,
dossier-relative artifact resolution, and independent repository/file
references all use this one `ROOT_ID:relative/path` vocabulary.

The approved portability split changes only where the absolute path lives.
Unlike v10, the accepted authority configuration does not bind a logical root
id permanently to `/home/...`; an explicitly supplied machine-local resolver
maps each configured root id to its checkout/base path. Every participant sees
and communicates the same durable root id and relative path even when local
absolute paths differ. Missing local resolution affects only explicit
navigation/bootstrap, never canonical authority reads, Work lifecycle,
message health, or SQLite state.

## 2026-08-15 — WS-6 asset references are available to every mutation

**Confirmed by Slawomir; rejects the proposed Slice-A restriction to only
`create` and `say`.** Baton must not decide that evidence may be cited by one
kind of authoritative act but not another. Every public mutation may carry an
ordered set of typed asset references. This includes ordinary discussion
messages and compound or lifecycle acts such as response, acceptance,
assessment, revision, and closure when their actor needs to identify supporting
evidence.

The references commit atomically with the act, event, effect, and optional
WS-5 operation record. They are part of the mutation's normalized typed input
and therefore its semantic fingerprint: an exact retry repeats them exactly,
while changed reference identity/order is a different request. A mutation
that produces more than one message or record must preserve explicit
per-result reference placement; it may not silently discard, duplicate, or
guess which result a reference supports.

This is availability, not obligation. Any act may carry zero references, and
templates or routes may recommend evidence without making filesystem content
part of Baton authority. Pure reads carry no references because they author no
act.

## 2026-08-15 — WS-6 references do not require discussion labels

**Confirmed by Slawomir; rejects the proposed rule that a dossier-relative
reference may name only Work currently labelling the discussion.** Any
existing bound Work may be cited by its explicit Work id, immutable binding
revision, and artifact path. The system is open, and a reference is evidence
metadata rather than an access-control or workflow edge.

`#WORK` labels remain intentional reusable discussion context. Citing evidence
does not implicitly add a label, alter discussion participation, create a
dependency, or mutate workflow. Requiring a label merely to cite an artifact
would clutter context and could be bypassed by a less precise independent
`ROOT_ID:path` reference. The explicit bound-Work reference is therefore
preferred when that provenance is known, regardless of current labels.

## 2026-08-15 — v11 trials run beside the live v10 coordination authority

**Confirmed by Slawomir; operational acceptance boundary.** Protocol-11
CLI/TUI test drives must run in parallel with, not replace or mutate, the
deployed protocol-10 mailbox and clients used to coordinate this work. The v11
trial uses its own config, authority database, client processes, and runtime
paths. Testing, restart, bootstrap, and failure injection against v11 must not
stop, rewrite, migrate, lock, or otherwise disturb the v10 channel.

The first v11 TUI trial is therefore not a cutover. v10 remains available for
review handoffs and recovery throughout v11 development; an eventual adoption
or clean-start cutover is a separately planned and explicitly coordinated
operation.

## 2026-08-15 — unbound Work refuses only the dossier-relative reference form

**Confirmed by Slawomir; resolves WS-6 M3.** A dossier-relative reference must
name an existing immutable binding revision. Work with no binding has no
dossier locator to anchor, so that form refuses clearly without mutation
rather than fabricating revision zero, guessing a root, or silently weakening
the reference.

This does not prevent citing the asset. The author may use the independent
configured `ROOT_ID:relative/path` form immediately. After Current establishes
a Work binding, later references may use the stronger Work plus binding-
revision form. The refusal protects provenance; it is not an availability or
access restriction.

## 2026-08-15 — binding locators enforce the permanent year/month record shape

**Confirmed by Slawomir; rejects the proposed prefix-only WS-6 M4 validation.**
A canonical dossier binding has exactly this repository/root-relative shape:

```text
work/records/YYYY/MM/<stable-record>
```

Baton validates the literal `work/records/` prefix, an exactly four-digit year,
a two-digit month from `01` through `12`, and one safe non-empty stable-record
component, in addition to the general normalized POSIX containment grammar.
The binding identifies the dossier root; files and subdirectories beneath it
belong in artifact-relative paths, not extra binding components.

This string-shape validation preserves the scaling reason for the year/month
layout and prevents teams from quietly collapsing permanent records back into
one opaque directory. It does not check that the year/month matches creation
time, stat or create the directory, inspect its contents, traverse symlinks, or
make filesystem availability authoritative.

## 2026-08-15 — root retirement preserves citation through existing bindings

**Confirmed by Slawomir; refines WS-6 M5.** A new Work binding, any appended
binding correction/provenance revision, and a new independent
`ROOT_ID:relative/path` reference require a root that is live in the accepted
configuration. Root identifiers are never reused with another meaning.

A dossier-relative reference to an existing immutable binding revision remains
legal after that revision's root is retired. It cites already-accepted
historical provenance rather than creating a new root binding. Existing
bindings and references remain readable, and local navigation may still
resolve them when the machine-local mapping remains available.

An open Work whose effective binding uses a retired root may append a
correction naming a live root under the ordinary Current/CAS/rationale rules.
Root retirement requires no special stranding gate because immutable bound
evidence remains citable; it neither invalidates Work nor rewrites history.

## 2026-08-15 — templates are deployed assets, not zipapp resources

**Corrected by Slawomir; resolves WS-6 M6 and rejects K's proposed
`importlib.resources` embedding.** Core template files are independent product
assets in the exact versioned CLI release:

```text
app/baton-cli/v<major>/v<full-version>/tmpl/
```

They are not built into the `baton-work`/Baton CLI zipapp. The release
candidate and deployment manifest carry `tmpl/` beside `bin/`, `doc/`, and
`conf/`, and deployment installs those bytes as separate files. The installed
bootstrap command reads the exact release's sibling template directory. A
standalone/copy-isolated application binary that lacks its release assets must
refuse bootstrap clearly rather than hiding a second embedded copy or silently
manufacturing a template.

Slice B therefore may change candidate assembly, manifests, release-layout
validation, generic installer logic, and temporary-target deployment tests so
the separate template assets are preserved byte-for-byte. It does not deploy
to `~/baton`, create a production mailbox, migrate a repository, or perform a
cutover. Source execution reads the source `tmpl/`; installed execution reads
the deployed sibling `tmpl/`; parity requires the bytes and bootstrap result to
match.

## 2026-08-15 — software distribution and project workspace are distinct

**Clarified by Slawomir; part of the WS-6 template/bootstrap boundary.** The
Baton distribution/install root and a participating project root are different
ownership domains and may live anywhere. A future system distribution could be
under `/usr/lib/baton`; the current user distribution may be under `~/baton`.
That location contains versioned application binaries, documentation,
configuration examples, and the shipped read-only default templates. Users and
teams do not edit their project conventions or dossiers there.

A configured project root is the repository/workspace selected through the
portable root id and machine-local resolver. The project owns its copied
`tmpl/`, `work/open/`, `work/records/`, and dossier contents, normally through
Git. Project teams may edit and version those copies independently of the Baton
software distribution.

Use distinct verbs and documentation: distribution **deploy/install** places
versioned product assets in the distribution root; project **bootstrap** copies
selected defaults from one exact installed release into one explicitly
resolved project root. Bootstrap never writes back into the distribution,
links a project to it, or makes later distribution upgrades rewrite project
files.

## 2026-08-15 — distribution, coordination home, and project roots are three domains

**Clarified by Slawomir; supersedes any two-root wording that conflates
coordination state with a project workspace.** Baton has three independently
located ownership domains:

1. The **distribution root** contains immutable versioned software and product
   assets. For example, `~/opt/baton` may contain exact CLI/TUI releases with
   their `bin/`, `doc/`, `conf/`, and `tmpl/` payloads.
2. The **coordination home/instance root** contains operational mailbox state:
   accepted/proposed instance configuration, SQLite authority, machine-local
   root resolver, operation records, and other instance-owned state. It may
   live under `~/baton`, `~/.baton`, or another explicit location and does not
   contain the installed application merely because both are named Baton.
3. **Project roots** are the configured source/work repositories. They own
   vendored editable templates, `work/open/`, `work/records/`, and permanent
   dossiers.

No domain's path is inferred from another. An installed executable receives an
explicit coordination config (and explicit local resolver where needed); the
resolver maps portable root ids to project roots. Distribution deployment does
not create or move mailbox state. Mailbox initialization does not install
software or bootstrap a project. Project bootstrap does not create an
authority, install Baton, or write into the coordination home except through a
separately requested Baton operation.

## 2026-08-15 — current locations and optional Git management

**Clarified by Slawomir; operational placement, not protocol identity.** Today
the configured project roots normally live under `~/src/*`. A coordination
home may live under `~/src/`, `~/baton`, or another explicit location and may
itself be Git-managed for recovery/provenance. Neither choice changes durable
root ids or makes a project path derivable from a team.

Git around a coordination home is external management. Baton does not invoke
Git, infer authority from a commit, merge SQLite, or claim that copying a live
database plus WAL sidecars is a consistent recovery point. If SQLite authority
snapshots are committed, producing a stopped/checkpointed or SQLite-backup-
API-consistent snapshot is a separate explicit recovery procedure outside
WS-6. Configuration, local resolver, runbooks, and other ordinary files may be
versioned according to the coordination repository's policy.

The software distribution has the opposite lifecycle: its location is stable
and each exact version directory is immutable. New releases are installed as
new exact product directories; project or coordination Git activity never
modifies installed release bytes.

## 2026-08-15 — WS-6 references cover configuration acts and refuse no-op loss

**Clarifies the mutation-wide reference ruling after K's corrected-plan
review.** `init`/generation-one activation and `regen` are public mutations and
therefore may carry the same ordered typed references as every other public
mutation. Configuration evidence is not a special reference-free island. A
fresh authority may use independent references validated against the proposed
root catalog; dossier-relative references naturally require an already
existing bound Work and therefore cannot be invented during fresh activation.

A protected mutation that discovers it has no domain act to commit must refuse
when references were supplied. In particular, a losing/no-op `mark-seen`
cannot silently discard its references or attach them to a nonexistent event.
The whole attempt refuses with an explicit "nothing committed to carry the
evidence" result. Exact replay of an earlier committed operation remains the
ordinary WS-5 replay case rather than a new no-op.

## 2026-08-15 — proposed coordination-home initialization UX

**Proposed by Slawomir; exact activation spelling remains open before WS-6
implementation.** Starting from an empty writable coordination home should
begin from the installed CLI without hand-copying release files:

```text
mkdir ~/baton
cd ~/baton
<exact-install>/bin/baton init .
```

This first command scaffolds the coordination home from exact-release
configuration examples: an editable instance-config template, an explicit
machine-local root-resolver template, and required state directories. The
operator then edits the templates to declare the real roots, teams, roles,
routes, participants, and assignments. A pure `baton check .` validates the
complete prospective instance and reports all schema/address/topology errors
without creating or changing authority state.

No canned SQLite authority may be copied from the distribution or bound to a
placeholder config: its UUID, accepted digest, participants, and routes belong
to this one configured instance. After `check` succeeds, a separate explicit
generation-one activation creates the unique SQLite authority atomically under
a named configured participant; only then do CLI/TUI members start against the
accepted config. The current generation-one operation is named `init`, so the
public spelling of scaffold versus activation must be resolved without two
ambiguous meanings.

Coordination-home scaffolding also does not vendor dossier templates into a
project. Exact-release `tmpl/` assets remain distribution inputs to the
separate project `bootstrap` operation, which copies them into a configured
project root. This preserves the three-domain ownership boundary.

## 2026-08-15 — coordination-home onboarding uses init then activate

**Confirmed by Slawomir; supersedes the proposed separate `baton check .`
step immediately above.** The public onboarding flow has two operations:

```text
baton init .
# operator edits the generated coordination configuration
baton activate . --participant team.member
```

`init DIR` is a filesystem scaffold only. It creates the editable
coordination-home configuration templates and required directories without
creating, copying, or binding SQLite authority state. It is safe against
replacement, symlink traversal, partial failure, and repeated invocation under
an explicitly defined existing-scaffold rule.

`activate DIR --participant ...` performs the one authoritative strict
validation of the completed generation-one `baton.json`, validates the named
participant against that proposed topology, and only then atomically creates
and binds the unique SQLite authority. Any lexical, schema, identity, route,
root-catalog, generation, or topology error refuses with structured JSON and
leaves no database or accepted state. A concurrent activation has exactly one
winner under the existing create-if-absent boundary; retry follows WS-5.

There is no separate `check` command in this slice. A failed `activate` is the
validation result and remains safe to retry after editing because validation
failure commits nothing. This avoids two validation paths that could drift or
suggest that a check succeeded under rules different from activation. The
machine-local resolver remains non-authoritative and is validated when an
explicit resolver-consuming operation uses it; missing local mappings do not
invalidate canonical authority activation.

This does not prohibit a later optional pure `check` convenience. If exposed,
it must call the same reusable validator as `activate`, write nothing, and
remain outside the required onboarding path. The supported first-use UX stays
the two-step `init` then `activate` flow; users do not have to preflight one
command merely to run the command that performs the same validation again.

## 2026-08-15 — init is deliberately one-shot and never cleans up

**Confirmed by Slawomir; supersedes review R88's requested automatic
partial-scaffold recovery.** `baton init DIR` requires every Baton-managed
target in that coordination home to be absent. If any managed config,
resolver, setup file, database, scratch marker, or other defined Baton state
already exists, `init` refuses before writing anything and names what blocked
it. It does not compare or adopt existing bytes, resume a partial scaffold,
overwrite an edited config, infer that an earlier invocation completed, or
remove anything.

The refusal explains the two ordinary interpretations: initialization may
already have run, or an interrupted/partial attempt left files for inspection.
The operator decides which is true and, if cleanup is appropriate, removes the
specific files manually before retrying. Baton never automates that destructive
decision. A phase-two failure reports every file it created so the operator has
an exact cleanup set; a later invocation still refuses until those files are
explicitly handled.

This is an intentional operational tradeoff, not an unhandled recovery gap.
`activate` remains independently atomic and retry-safe under WS-5; project
`bootstrap` may remain idempotent because its inputs are fixed release bytes,
not newly generated instance identity.

## 2026-08-15 — Slice B follows accepted Slice A; production execution stays human-owned

**Confirmed by Slawomir; clarifies the WS-6 release and deployment gates.**
When the Slice A correction passes reviewer inspection and its focused and
full v11 gates are clean, Slice B is released immediately without another
product-disposition stop. Slice B remains exactly the bounded resolver,
template-distribution, coordination-home onboarding, project-bootstrap, and
temporary-target acceptance work already specified; acceptance of Slice A
does not broaden that scope.

Installing or cutting over a production deployment is a separate operational
act and remains Slawomir-owned. Agents may implement and test the generic
distribution/install machinery against isolated temporary targets in Slice B,
but do not deploy to a live production root, create or migrate a production
mailbox, stop production participants, or perform cutover. Production
deployment is expected to be a manual operator step unless Slawomir later
explicitly authorizes a particular operation.

## 2026-08-15 — protocol 10 is no longer part of the v11 development gate

**Confirmed by Slawomir after WS-6 acceptance.** Protocol 10 is already the
working, deployed coordination system. V11 development does not repeatedly
rebuild or retest v10 merely because both generations share this repository.
The v10 runtime remains available as the live channel while v11 is developed,
but it is frozen and outside the ordinary v11 verification scope.

This supersedes the earlier plan item that preserved `just build` followed by
the combined `just test` as a prerequisite for each v11 candidate phase. V11
changes use focused v11 tests plus `just test-v11`; packaging checks exercise
the v11 product and its own distribution assets against isolated targets.
Work on v10 resumes only for a separately identified production-blocking v10
defect, not as routine regression coverage for v11.

The immediate next product phase is therefore Gate B TUI completion and
TUI/JSON parity over the accepted v11 engine, followed by a packaged parallel
v11 trial. It is not v10 retesting and it is not production cutover.

## 2026-08-15 — corrected Gate B TUI phase authorized

**Approved by Slawomir after the next-phase review.** Gate B now proceeds as a
v11-only phase over the accepted canonical engine and projection. Its product
vocabulary is Work, not objective, and its participant-relative recursive
message counter is `New`, not the superseded `Unans.` counter. The TUI renders
canonical values; it does not invent progress, blocker, last-update, or other
workflow semantics absent from the shared projection.

B1 completes the bounded borderless Work navigation and focused Work view
through the shared projection with real-PTY evidence. B2 expands one shared
fixture into semantic TUI/JSON parity for rows, personal counts, drill links,
and actionable state. B3 drives the ruled scenario through the packaged v11
TUI rather than source-private entry points. Focused v11 evidence and
`just test-v11` are the gate; no v10 build or test is part of it.

Pane arrangement, responsive widths, sorting, keys, and detail presentation
may be implemented as bounded prototypes because they carry no separate
workflow semantics. They return at the Gate B review stop for human trial and
refinement. Any missing canonical state or product contradiction returns for
ruling before the projection is changed.

Only after Gate B acceptance may the packaged v11-only parallel trial begin.
Its paths, roster, and real workflows are selected then. V10 remains live and
untouched; migration, production deployment, shutdown, and cutover remain
held.

## 2026-08-15 — Gate B must hand the human a safe parallel TUI trial

**Confirmed by Slawomir as Gate B acceptance behavior.** When Gate B is done,
Slawomir must be able to launch the packaged v11 TUI himself and perform
feedback/testing without affecting the production v10 system. The handoff
therefore includes exact commands for the packaged v11 executable and an
explicit, separately initialized v11 coordination-home config and database.
No command may infer, open, lock, migrate, stop, or rewrite a v10 path.

The Gate B evidence proves the packaged TUI against an isolated instance and
the review response supplies the trial launch sequence. Selection of the real
trial path, participants, project roots, and workflows remains a deliberate
post-acceptance choice; the product must already make that choice sufficient,
without another source change. Human trial observations become ordinary v11
Work and may drive further iterations before any production cutover is
considered.

## 2026-08-15 — human deploys the v11 distribution, then initializes coordination

**Clarified by Slawomir.** At the end of Gate B, the repository must provide a
v11-only deployment command that Slawomir can run against an explicit
distribution destination directory. That operation installs the immutable v11
product layout—executables, documentation, configuration examples and
templates—into the chosen distribution root. It does not create or activate a
real coordination home and does not touch v10.

After deployment, Slawomir personally runs the installed v11 product's public
`init`, edits the generated coordination configuration, and runs `activate`.
The Gate B handoff gives the exact commands and resolved installed executable
path but does not perform those real operator steps. Tests may exercise the
same sequence only against isolated temporary roots.

The distribution destination and coordination home are distinct location
domains. Calling the former a `dist` directory never makes it an authority,
mailbox, project root, or mutable template workspace.

## 2026-08-15 — Slawomir starts the parallel three-participant trial

**Confirmed by Slawomir.** After manually deploying v11 and completing the
real `init` / edit / `activate` sequence, Slawomir brings the human,
`baton.reviewer`, and `baton.implementer` into that isolated v11 coordination
instance for a joint test drive. The generated configuration is edited to
declare the trial participants, teams, roles, routes and roots before
activation; joining does not mutate or infer topology after the fact.

The trial runs beside v10. V10 remains live as the proven coordination and
recovery channel while all experimental Work, discussions, transitions and
TUI feedback occur in the separate v11 authority. A v11 defect never requires
shutting down, migrating, or repairing v10. Findings from the trial are
reported and reviewed before any later cutover decision.

## 2026-08-15 — v11 deployment has a `just` operator surface

**Confirmed by Slawomir at the parallel-trial launch.** The implementation of
the v11 immutable distribution may remain in `tools/deploy_work.py`, because
zipapp construction, release-asset copying, hashing and atomic publication are
not usefully reproduced in shell. That Python module is internal packaging
machinery, not the command handed to an operator.

The repository-level operator command is:

    just deploy-v11 EXPLICIT_NEW_DISTRIBUTION_DIRECTORY

The recipe is deliberately named `deploy-v11` while the frozen v10 `deploy`
recipe still exists. It is a thin, transparent call into the one deployer and
does not add a second implementation. It preserves every existing boundary:
the destination must be new and explicit; deploy installs only immutable
distribution assets; it does not initialize or activate a coordination home;
and it does not touch v10.

## 2026-08-15 — the product and executable are named `baton`

**Confirmed by Slawomir after deploying the first Gate B trial.** `baton-work`
was a temporary development name used to distinguish the v11 Work engine from
the live v10 executable. It is not a separate product name and must not become
the name of future releases, including production releases.

The product and installed executable are `baton`. Protocol generation and
release identity are expressed by the immutable distribution path, for
example `.../baton/v11/<release>/bin/baton`, not by renaming the executable.
The already-deployed `6d1b944` trial may continue under its existing
`bin/baton-work` path so its immutable bytes are not rewritten. The next v11
distribution must rename the installed executable and all current-facing
documentation/examples to `baton` before production is considered.

## 2026-08-15 — repository roots are configured in `baton.json`

**Confirmed by Slawomir during the second v11 trial. This explicitly
supersedes the earlier WS-6 ruling that `baton.json` carries only portable root
ids while absolute paths live exclusively in a separately supplied
machine-local resolver.** See
`findings/finding-configured-project-root-paths/FINDING.md`.

The explicit coordination configuration must tell a validated client where
each configured source/repository root is. No client may infer a filesystem
base from the coordination home, current directory, distribution, `$HOME`,
`~/src`, team identity, display name, or a discovered sibling file. Durable
references remain `ROOT_ID:relative/path`, but the root id's actual base is
configured in `baton.json`, so a TUI or JSON client opened with that config can
resolve the same assets without a hidden second configuration input.

The three ownership domains remain distinct; this correction makes their
association explicit rather than inferential. It is queued for the next
revision and does not rewrite the currently deployed immutable trial.

## 2026-08-15 — Work priority is deliberately three-level and team-local

**Confirmed by Slawomir during the second v11 trial.** See
`findings/finding-work-priority/FINDING.md`. Work has exactly `high`, `normal`,
and `low` priority, with `normal` as the default. No `urgent`, numeric, or
finer tier is provided because additional levels invite priority inflation.

Priority orders otherwise-actionable Work but changes no readiness,
dependency, Current/Next, route, handler, phase, status, or closure semantics.
The owning team may revise its priority through an audited operation; another
team may discuss urgency but cannot mutate it. JSON exposes the full value and
the compact TUI uses `Pri` with `High`, `Norm`, and `Low`.

## 2026-08-15 — TUI-required Work identity must be discoverable

**Observed during the second v11 trial.** See
`findings/finding-tui-work-id-discovery/FINDING.md`. A Work created through the
command bar returns its stable id only transiently, while neither the Work
table nor focused view shows that id. The same command bar requires exact ids
for `block`, `detail`, `phase`, and related operations. Missing the creation
result therefore forces an external JSON lookup by non-unique title.

The TUI must provide an exact, persistent way to discover or target the
selected Work. It must not guess from a title, sequence expectation, stale
cursor, or invisible row. The precise compact interaction returns for review;
this is queued trial feedback and does not rewrite the current distribution.

## 2026-08-15 — v11 operations use key/value grammar with contextual assist

**Confirmed by Slawomir during the second v11 trial.** See
`findings/finding-key-value-command-grammar/FINDING.md` and
`findings/finding-tui-command-assist/FINDING.md`. After the verb, CLI and TUI
operations use strict order-independent `key=value` tokens, for example
`block work=<consumer> on=<provider>`. Values containing spaces are quoted;
tokens split at the first `=`; unknown, missing, malformed, or duplicate
singular keys refuse; only declared repeatable keys repeat. The current
positional/`--option` operation dialect is replaced rather than retained as a
parallel v11 grammar. Global executable options remain outside this operation
grammar.

The `:` command bar assists incrementally from the same declarative command
specification the parser consumes. A partial verb shows matching commands; a
complete verb shows its parameters; supplied keys narrow the remaining help;
and closed value vocabularies appear in context. Assistance renders to the
right when space permits, remains usable at narrow widths, and performs no
authority or seen mutation. The assist feature depends on the grammar feature;
neither changes the current immutable trial.

## 2026-08-15 — `::` opens an explicit multiline command batch

**Confirmed by Slawomir during the second v11 trial.** See
`findings/finding-tui-command-batch/FINDING.md`. `:` remains the assisted
one-line command interaction with Enter-to-execute. `::` instead opens a
multiline batch buffer: Enter adds a line, pasted newlines stage commands, and
visible `Ctrl-G` Go launches the batch.

Go syntax-validates every line before executing anything, then runs commands
sequentially and stops at the first authority refusal. Completed, failed and
unrun lines remain distinguishable; no rollback or all-or-nothing claim is
made. Batch staging is read-only, and execution must preserve safe per-command
retry identity. This is deliberately not a file-backed scripting language:
there are no variables, control flow, shell expansion, file execution, or
recursive includes in this feature. It depends on the accepted key/value
grammar and does not replace or weaken contextual one-line help.

## 2026-08-15 — Work exposes separate live blocker and dependent counts

**Confirmed by Slawomir while wiring the second-trial release gate.** See
`findings/finding-live-dependency-counters/FINDING.md`. The current `Dep`
column counts open Work depending on this Work, so a release gate waiting on
many corrections displays zero while each correction increments. The graph is
correct, but the one ambiguous counter hides the opposite direction and
misleads operators.

Canonical projections expose both `open_blockers` and `open_dependents`. The
TUI renders them as `Blk` and `Dpts`. Both counts are live only: provider
closure removes one blocker from each consumer, while consumer closure removes
one dependent from each provider. Terminal outcomes and historical edges stay
in links/events and never remain in these active counters. Restart and rebuild
must reproduce the same values.

**Presentation supersession confirmed later on 2026-08-15.** The W71
two-level containment tree makes `Prog` and dependency counters too expensive
and noisy in the main Work table. The TUI therefore removes `Prog` and the
existing `Dep`; it does not add `Blk`/`Dep` columns. Indentation/disclosure
shows ordinary parent-child gating, while arbitrary many-to-many graph counts
appear in Work details/links.

The canonical machine contract above is not superseded: JSON preserves
`progress.children/closed` and replaces ambiguous `dep` with explicit
`open_blockers` and `open_dependents`. W71 absorbs that remaining projection
work; W27 is cancelled as a separate item.

## 2026-08-15 — Work has an authority-local short selector

**Confirmed by Slawomir during the second v11 trial.** See
`findings/finding-local-work-selectors/FINDING.md`. The list view exposes a
compact generated `Id` such as `W11`, and every Work-valued CLI/TUI parameter
accepts either that authority-local selector or the full canonical id. JSON and
details expose both `local_id` and `id`.

The selector is permanent, generated, never reused and resolved only within
the client's explicit authority. Missing, malformed, foreign, or ambiguous
input refuses; titles, cursor position and expected creation sequence never
stand in for identity. The TUI never truncates the `Id` column as sequence
width grows. Full canonical ids remain the durable form where authority context
is not already fixed.

## 2026-08-15 — Work lists show total Messages and my pending requests

**Confirmed by Slawomir during the second v11 trial.** See
`findings/finding-work-message-action-counts/FINDING.md`. The list adds compact
`Msg/My`, such as `41/1`: total distinct Messages in the row's overlap-safe
Work scope, followed by unresolved directed `@` obligations the current viewer
is eligible to answer in that same scope.

`My` is not unread mail, `+` inclusion, ownership, or somebody else's pending
request. Resolving or withdrawing the obligation decreases `My`; an ANSWER is
itself a Message and may simultaneously increase `Msg`. `New` remains the
separate personal seen-cursor count. JSON exposes explicit full fields and the
projection is read-only and rebuildable from existing canonical state.

## 2026-08-15 — next trial iteration preserves the current SQLite schema

**Confirmed by Slawomir after reviewing the second-trial queue.** See
`SAME-SCHEMA-TRIAL-PLAN.md`. The next iteration intentionally delivers only
work that can restart against the existing schema-14 authority. It adds no
migration, replacement database, shadow authority, or in-place data rewrite.
The packaged acceptance gate reopens a preserved copy of the current authority
and proves its existing history remains usable.

`W10` priority stays open for a later fresh-authority release because priority
adds persisted Work state. It is removed from the scope of the same-schema
release, not deleted or falsely closed. The existing `W11` release gate cannot
withdraw its already-recorded W10 edge; Slawomir therefore closes W11
`cancelled` as superseded and creates a follow-up gate containing only eligible
work. Any other item found to require a database-schema change is likewise
deferred rather than smuggled into this iteration.

Configuration/projection/client changes are eligible only when they preserve
schema 14 and reopen the same authority honestly. In particular, explicit root
paths may use audited config regeneration only if that gate holds; otherwise
W4 returns for deferral.

During this iteration v10 is the reliable communication path and v11 is the
desired workflow record. Implementer handoffs and completion wakeups travel
through v10; the corresponding progress, evidence and Current/Next transition
must also be recorded against the exact v11 Work. A v10 completion is not
accepted until the reviewer verifies that repository evidence and v11 state
agree. This dual recording is temporary trial discipline, not a claim that
either authority automatically mirrors the other.

## 2026-08-15 — terminal Work has no operational phase

**Confirmed by Slawomir during the second v11 trial.** This narrowly
supersedes the earlier statement that operational phase is globally non-null.
Phase is a property of open Work only. While Work is open, `phase` remains one
required canonical value and may never be null. Once Work closes, no
operational phase remains: canonical JSON reports `phase: null` and the TUI
renders `-`.

There is still no synthetic terminal `done` phase. Status plus terminal
outcome state the lifecycle result; displaying a stale last phase such as
`queue` beside `c/sat` falsely implies that closed Work remains actionable.
The append-only audit/event history preserves the last open phase and the
close transition, so removing phase from terminal state loses no history.

See `findings/finding-terminal-work-no-phase/FINDING.md` and its plan.

## 2026-08-16 — fresh-schema Work requires classification at submission

**Confirmed by Slawomir during the records/open cutover. This supersedes the
2026-08-14 rule above that new Work defaults to the canonical classification
`unknown`.** The fresh authority does not accept an unclassified Work item.
Its submitter must choose one concrete canonical classification at creation,
even when that choice is only the submitter's current best assessment.

The current handler may reclassify the Work at any later open-state point as
evidence and understanding change. Claiming the Work active therefore does not
require a redundant reclassification ceremony; the classification already
exists. Submission classification is an initial accountable assessment, not
an immutable verdict and not proof that another team has accepted the
submitter's diagnosis.

The fresh-schema vocabulary and creation surface must make omission and
`unknown` refuse. Historical schema-14 records retain their recorded
`unknown` values; this ruling does not rewrite the retired trial authority.

See `findings/finding-active-work-claim/FINDING.md` for the separate atomic
active-participant claim that gates execution.
