# baton — the v11 coordination product

`baton` is the protocol-11 Work authority: a strict `baton.json`
configuration, one SQLite authority per instance, a JSON CLI for
agents, and a curses console for humans. This document is the
operator quickstart shipped with every release; the repository's
design dossier holds the full rulings.

## Install

Each release is deployed into a NEW explicit immutable directory:

    just deploy-v11 /your/dist/baton-rN

Run that command from the Baton source checkout. The recipe owns the internal
packaging mechanism; operators do not invoke it directly.

The installed layout is:

    bin/baton     the executable (JSON CLI + `tui`)
    doc/               this document
    conf/              the configuration example and scaffold seeds
                       (init consumes them; a partial release refuses)
    tmpl/              the numbered dossier templates bootstrap vendors

Nothing outside the target directory is read or written; deploying
never touches an existing directory.

## Create a coordination home

    mkdir -p ~/your-home
    /your/dist/baton-rN/bin/baton init directory=~/your-home
    # edit ~/your-home/baton.json — teams, roles, routes, kinds;
    # conf/baton.example.json shows a complete valid document
    /your/dist/baton-rN/bin/baton --participant team.member \
        activate directory=~/your-home

`init` is one-shot and creates no database; `activate` is the one
authoritative validation and creates the SQLite authority only when
the document passes. A refusal leaves nothing behind.

## Use it

    BW=/your/dist/baton-rN/bin/baton
    $BW --config ~/your-home/baton.json --participant team.member home
    $BW --config ~/your-home/baton.json --participant team.member tui

Agent launchers resolve durable role instructions from the accepted
configuration rather than reading `baton.json` themselves:

    $BW --config ~/your-home/baton.json --participant team.member instructions role=ROLE

`role=` is always required — every role carries instructions, and the launch
role is named rather than inferred so a later second role cannot silently
change a session's persona. A missing or unheld role refuses before a launcher
creates or resumes a session.

The active claim is its own authority state, orthogonal to phase: `claim
work=WORK` records WHO is executing without touching WHAT stage the phase
names. One eligible handler of the live Route endpoint acquires open,
ready, non-waiting/non-parked Work — every condition rechecked inside the
write transaction, so an earlier `ready` observation is advisory and a
competing claim fails closed naming the recorded claimant. No execution
begins before the claim succeeds. A pass atomically records the
destination Route AND the destination phase through its own canonical
THREADLESS verb — `pass work=W to=team.kind comment="..."`
(W38: phase is a closed SCHEDULER axis — `queued` runnable and
unclaimed, `active` claimed, `waiting` gated, `parked` deferred, and
absent once terminal. A handoff hands over responsibility, not
activity, so it lands `queued` when the Work is runnable and `waiting`
when a gate holds it, whatever the destination role. `phase=` is
refused as an unknown key. The route's role still says whether this is
research, implementation or review — it just no longer masquerades as a
scheduler state, and `active` is reachable only by claiming);
`comment=` is durable handoff evidence stored with the authoritative
pass event itself, never a discussion message; `set-next=` plants the
planned return; `thread=` is refused as an unknown key — a Work
transfer has no thread-selection decision — releases the sender's
claim, and never claims for the recipient. A pass creates no Message,
advances no cursor, and changes no Message/My/New/obligation count;
conversation stays explicit through `say`. Plain `say` is discussion
(plus the `@ request=` operator); it carries no transfer keys; entering
waiting/parked and terminal close also release. Blocked Work keeps its
honest stage phase but cannot be claimed. An abandoned or yielded claim
is recovered with `release work=WORK expect=team.member reason=TEXT` —
live Route-handler authority, an exact compare-and-swap against the
recorded claimant, and a durable reason; it clears the claimant and
derives the scheduler state the Work lands in. The projection carries
`handler` (JSON) and the detail facts name the
claimant.

The console renders the same canonical projection the JSON surface
serves. It refreshes automatically on a timer — default every 2
seconds, configurable with `tui refresh=SECONDS` (positive) — and
that timer is the ONLY background read: ordinary keystrokes operate
on the cached projection and never poll the authority. A background
refresh is read-only and keeps the selection on the same Work.

The console has three top-level tabs, and they lead the header with
the participant identity right-aligned on the same row:

    [Jobs]   Teams    Inbox 3/1                              team.member

`Tab` cycles them forward and `Shift-Tab` back; the selected tab is in
brackets, which is a TEXT cue and survives a terminal that ignores
bold. (`[`/`]` are unchanged and still belong to Work detail's
Messages/Events tabs.) There are no `[oblig] [park] [due]` header
counters any more: owed action is what Inbox is for, parked Work stays
visible and filterable in Jobs, and repeating either in a global header
was noise.

**Jobs** is the Work tree and everything hanging off it, exactly as
described below. **Teams** is an operational roster: every configured
member, the roles they hold, the routes they handle with the endpoints
those routes cover (W230 alternates included), the Work the authority
says they are holding right now, and what their RUNNER is doing.

Runner facts come from two sources and Teams keeps them apart, because
they answer different questions and can honestly disagree. The runtime
lease is what the member's ADAPTER observed — state, adapter family,
provider, model, the live session locator, and how old each of those
is. The last poke answer is what the AGENT said about itself when
somebody asked, including the auth and limit facts only it can see. A
disagreement between them is a fact worth showing, not one to
reconcile. Teams never guesses liveness from a process table or a
console session: a member with no lease reads "no lease" and one that
has never answered a poke reads "never asked", both of which mean
unknown and not "fine". It opens on the viewer's own team; `t` browses
every configured team, `p` pokes the selected member (the request is
authored in `EDITOR`), and `x` withdraws a poke this participant has
outstanding to them.

**Inbox** is participant-relative. It carries pending pokes addressed
to you, `@` obligations owed through a route you handle, due
verification trials your Route answers for, and unseen discussion in
threads your team has joined. Actionable WORK is deliberately absent —
that is Jobs, and one queue in two tabs makes "how much do I owe" a
number nobody can act on. The tab label is `total/unseen`, and the
whole label is bold whenever at least one row is an unresolved action
you owe, even one you have already read: seen state never hides that
you are the blocker. Rows name their type and say whether they are
owed or attention only; `Enter` opens the row's Work in Jobs, `a`
answers a poke or responds to an obligation (prose authored in
`EDITOR`), and `s` advances the seen cursor through the public
`mark-seen`. Seen state is reported only where the authority holds it:
a thread has a per-participant cursor, so a message row and an
obligation born from a message are seen exactly when that cursor has
passed them, while a poke and a due trial have no cursor and read
unseen until they resolve.

### Agent runtime state

Phase says which scheduler state a Work is in and Handler says who
holds the claim. Neither can say what that participant's runner is
DOING — so a turn parked on an interactive approval prompt looked
exactly like a turn making progress, and the only evidence was a
dispatcher log. The runtime lease is where that fact lives.

One configured participant has at most one live lease. An adapter
opens it, publishes transitions onto it, and ends it; every write names
the lease it holds, so a superseded runner fails closed instead of
restoring state its replacement has moved past.

    $BW ... --participant team.member runtime
    $BW ... --participant team.member runtime-history participant=team.member [after= limit=]

`runtime` is the current picture for every participant the viewer can
see; `runtime-history` is one participant's append-only journal, which
is what an incident is reconstructed from and which keeps each
incarnation's timeline separate. Both are read-only.

The published states are `idle`, `working`, `waiting-input`,
`retrying` and `failed`. `offline` and `unknown` are never published —
they are DERIVED at read time from a lease that ended or went quiet,
and every row says which it is through `provenance`
(`reported`/`derived`). Silence is never diagnosed: a runner that
stops renewing reads `unknown`, dated from the deadline it crossed,
and never `failed` and never `stuck`. States an operator can act on
carry a closed `cause` category — `approval`, `credential`, `input`,
`limit`, `provider`, `transport`, `internal` — with prose in `detail`.

These are the adapter's verbs, and a bridge normally issues them; they
are documented because an operator reads them in `runtime-history` and
may need to run one by hand:

    runtime-start   incarnation= adapter= [provider= model= session=]
                    [action-owner=] [rationale=] [expires-at=]
    runtime-state   incarnation= state= [cause= detail=] [work= episode=]
                    [session=] [expires-at=]
    runtime-end     incarnation= [cause= detail=]
    runtime-facts   incarnation= [source= observed-at= answers=] KEY=VALUE…
    runtime-refresh target=team.member

`session=` on a state report is how a RECONNECT lands: an adapter that
resumed on a new session locator states it with the transition that
observed it, so the member's live locator is never left pointing at a
session that has gone. `expires-at=` is the explicit freshness
boundary — omitted, every report renews the lease from the configured
duration, which is what makes silence past the deadline mean something.

None of it is workflow authority. No runtime write claims, releases,
re-phases, passes, blocks or closes anything: `work=` on a state report
CORRELATES the runner with the assignment it believes it is serving,
and the Work table remains the only Handler. Recovery stays an explicit
operator or Handler action — Baton never auto-releases a claim because
a runner went quiet.

Where it shows up: the Jobs `Agent` column beside `Handler` (`-` when
the Work is unclaimed, which is a different fact from a runner nobody
can see), the Teams `State` column and Member details, and — for
`waiting-input` only — one owed row in the Inbox of the participant
the lease names as its action owner. With no action owner named, the
wait stays visible in Teams and Jobs and creates no guessed obligation.
Ordinary `working`/`idle` transitions never reach an Inbox.

`runtime-facts` publishes the safe operational inventory: `service`,
`dispatcher`, `readiness`, `workdir`, `log`, `version`, `retry-at`.
The key set is CLOSED and values that look like credentials are
refused, so a launcher configuration full of secrets cannot leak one
into a durable diagnostic — a signed URL is refused rather than stored
and redacted later by a reader who may never run. Each fact carries its
own `source` (`configured`, `reported`, `derived`) and the instant the
ADAPTER observed it, so a member's state can be seconds old while its
inventory is hours old and the screen says so.

`runtime-refresh target=` asks that participant's ADAPTER to republish
the inventory. It runs nothing, blocks nothing and never wakes the
model: the adapter notices it on the polling loop it already has and
answers from facts it holds. Each request carries a generation, and a
publication clears the exact generation it answered — so an answer to
an earlier question never retires a later one. When only the agent
itself can answer, that is `poke`, not this.

Both surfaces ride JSON as their own verbs — `teams` and `inbox`, no
operands, participant-relative — so an agent derives the same counts,
the same owed-action state, the same navigation targets and the same
satisfying verbs from typed fields rather than from glyphs.

The main screen is a three-level containment tree: top-level Work,
each root's immediate `↳` children, and their `  ↳` children in turn.
A `▸N` disclosure marks any visible row holding Work this window does
not show — the fourth level and below, or children a filter removed —
reached with `u`. The tree the console
paints is one canonical projection — the JSON verb `tree` (optionally
`tree WORK` for a re-rooted window) returns the identical rows,
summary and snapshot token, all read under one transaction. Keys: j/k select, Enter
opens the selected Work's DETAILS: the compact summary, the Thread
list, and below it a compact Message index (`M<seq>` labels over the
existing stable sequence, with author, time, and your personal
new/seen state) beside a reader showing exactly ONE selected message
— its metadata header, wrapped body, and references under a separate
Refs section. Work detail carries TWO tabs — `Messages` and `Events`,
with Messages the default and the active one shown in brackets. `]`
selects the next tab and `[` the previous, from anywhere in the detail
view, and the footer always advertises `[/] tabs`. Events is the Work's
append-only operational play-by-play: creation, classification,
priority, contract and binding changes, dependency additions and
corrections, claims, heartbeats, releases, phase/Route/Next moves,
passes, verification lifecycle, and terminal disposition — with `E<seq>`
as the visible stable identifier, the typed roles explaining WHY each
event belongs to this Work, the other Works it affected, and claim
intervals giving the work-time. One dependency act appears in BOTH
affected Works from the same authoritative event, with opposite roles.
Pure discussion and personal seen-cursor movement stay in Messages and
never inflate `Msg`/`My`/`New`; a workflow-bearing message act is
discoverable in Events without duplicating its body. Each tab keeps its
own focused pane, selection, page cursor and reader scroll, and `Ctrl-W`
stays pane-local to the active tab. The same facts ride JSON as
`work-events work=W [after=|before=|newest=|limit=]`, whose pages stay
canonical ascending. The Message index reads NEWEST-FIRST: entering a Thread selects
its newest Message, which is also its newest unseen one whenever
anything is unseen (the seen cursor is a monotonic sequence), so
screen-down selects older Messages and screen-up newer ones. Entry is
one bounded page read; the console never walks a whole Thread to
reach its tail. The split-area headings identify pane ROLES —
`Messages (N)` over the index and `Message M<seq>` over the reader —
never content already visible elsewhere: the Thread row alone owns the
discussion subject, the reversed index row owns selection, and one
blank separator row (spacing, not a border) divides the Thread list
from the lower panes. At usable width the index sits left of the
reader; at narrow width they stack, index above reader — never merged
into a flat stream. Selecting a Thread opens its newest Message, which
is also its newest unseen one whenever anything is unseen. u
unfolds/re-roots the tree at the selected Work,
Esc goes back, Ctrl-W then h/j/k/l (or arrows, or w / another
Ctrl-W) moves GEOMETRICALLY across the three regions — Threads sits
above both Message panes, index and reader sit beside each other, so
one upward move from the reader reaches Threads directly and an
unmapped edge direction stays put; a second Ctrl-W (or w) keeps the
three-pane cycle —
j/k or the up/down cursor keys select within the focused region (in the reader they scroll a
long body, tagged `M<seq> (cont.)`), n pages toward OLDER messages
through the Message index (or forward through the Thread list) while
more exists, p returns to the newest page (not a previous-page step), s advances your seen cursor
through the SELECTED message and no later one, z reveals closed
rows, [b] deps opens
the blocking/dependent neighbor view, p opens the poke view described
below, q asks Exit? y/N on one row (y exits; n or Esc returns to the unchanged view). `:` opens the command bar: everything typed there is
the PUBLIC CLI grammar run as you (for example
`:create team=push kind=bug title="..." origin=self-initiated
body="..."`), with the public refusals. As you type, the bar shows context-sensitive assistance on the right — matching verbs, then the effective remaining required and optional keys (form conditions applied exactly as the parser enforces them), then closed values narrowed by your prefix — derived through a shared partial-command analyzer that speaks the same quoting and first-`=` rules as execution; malformed, unknown, or duplicated input shows the diagnostic instead. The assistance is read-only and yields to your input when space runs out. The caret stays visible at the insertion point; input longer than the row scrolls in a horizontal viewport (`<` marks the clipped left) and is never cut.

`::` (a second colon on the empty bar) opens the multiline **batch** buffer: Enter adds a line, `Ctrl-G` runs, `Esc` cancels — a visible legend names all three, and a pasted newline can never execute. Go first statically validates every line through the same parser (one refusal and nothing runs), then executes sequentially in written order, stopping at the first authority refusal; the pane honestly marks lines `ok` (completed — committed, never rolled back), `!!` (failed, with the public refusal), and `--` (unrun), and failed/unrun input stays editable. Mutating lines without an explicit `op-id=` carry a generated per-line identity retained across unedited retries, so a re-run replays committed results instead of duplicating them; completed lines are skipped. A batch is a command list, not a script: no variables, control flow, or expansion.

Wakeups are PARTICIPANT-relative: `wait`
returns the one canonical action projection for your exact identity —
open ready unclaimed Work whose Route resolves to you (every eligible
handler until one claims; the claimant alone after, under the same
stable `work:` key), pending `@` obligations your endpoint owes
(`obligation:` keyed by seq), due verification trials your Route
answers for (`trial:` keyed per deadline generation, retired by
extension), and conversational pokes addressed to your exact
participant (`poke:` keyed by the poke's own sequence, offered last
because a question never displaces the workflow you were woken for).
`+`, plain posts, and personal New are attention, never
wakeups. The console's Inbox tab is these same personal facts, minus
the Work (which is Jobs), plus the unseen discussion `wait` never
carried; the team-wide parked count lives in the canonical summary and
in Jobs, not in a header counter.

The console surfaces pokes in the Inbox, as rows that name their type:
a poke is conversation addressed to one participant and carries no
workflow authority, so the row says `poke` beside the obligations and
attention rather than being folded into either. While one is waiting
the bottom row says so and names where to go. `p` opens the poke
record — the questions asked OF you, which you answer, and the ones
you asked, which you may withdraw — owed ones first, each row carrying
the action as text (`answer`, `withdraw`), the canonical state beside
it, which end of the conversation you are on, and the question itself;
the block beneath shows the chosen poke whole, with its deadline and
its one terminal answer when it has them. `a` answers: a one-row
chooser offers the grammar's own `state=` vocabulary and your editor
takes the explanation, so no sequence is ever copied out of JSON. `x`
withdraws a pending one. Answered, cancelled, superseded and timed-out
pokes stop being owed and stay readable as history. The verbs are
exactly the public `poke-answer` and `poke-cancel`, with the public
refusals; the console adds presentation, not a second delivery path,
and `pokes` remains the authoritative read.

Work counters describe the DIRECT visible scope: a row's or detail
header's `Msg`, `My`, and `New` cover exactly the threads labelled
directly to that Work — the same conversations entering the Work
exposes — with thread-less verification assignments staying on their
own Work. Every contained child reports its own direct counters;
closed, collapsed, or nested descendants never inflate a visible
parent, and a thread deliberately labelled to several Works counts in
each direct view (visible reuse). The recursive union exists only in
the explicitly named breakdown (`new work=W`): `own`, per-child
subtree counts, `overlap` for multiply-labelled dedup, and
`subtree_total` — clients never project that union into a plain cell.
Agent JSON and the human console read the same direct defaults.

`/` searches Work: a one-line query bar
(typing reads nothing; Enter submits ONE canonical `search query=...`),
matching case-folded title substrings and canonical/local id prefixes
across every Work your team owns — nested items included, message
bodies excluded. The active filter narrows results; closed rows follow
the ordinary visibility rule; results page behind an explicit
continuation cursor in stable creation order. Enter opens a result's
normal details (and returns to the results); `/` starts a replacement
query; Esc restores the exact prior window. The same projection rides
JSON as `search query= [after= limit=]` plus the filter operands.

Claimed Work keeps a liveness heartbeat: the
claim is the initial beat, and the current claimant sends
`heartbeat work=Wn` every two minutes while executing or reviewing.
Silence renders NOTHING: an agent can be alive and busy inside one
model turn with no opportunity to beat, so the console shows no
staleness alert and never infers failure from a missing call.
Liveness was never a lease either — Baton does not auto-release,
transfer, rephase, or admit a second claimant on staleness, and
recovery stays the explicit release path. Only the exact current claimant may beat (rechecked in
the committing transaction), the audited event journal is the record,
and canonical JSON exposes `heartbeat_at` scoped to the current claim
epoch so every client reaches the same conclusion.

Required dependency edges are explicit, reviewable workflow decisions:
`block work=WORK on=BLOCKER rationale="..."` records why Work must wait.
If that live edge was itself a mistake, the consumer Work's Route handler
uses `unblock work=WORK on=BLOCKER rationale="..."`; this corrects only the
exact open edge, recomputes readiness atomically, and never closes or edits
either Work. Both verbs require their rationale and support `op-id=`. The
immutable event ledger retains the addition and correction even though the
live graph no longer contains a corrected edge. Finished blockers leave
historical edges and are never rewritten through `unblock`.

Work lists filter composably over canonical
facts — `home`, `tree`, and `tui` take the same optional operands
(`team= status= phase= route= handler= category= ready= new= priority=`, full
canonical values only, AND composition, one value per field), and the
console's `:filter` shares the exact grammar (bare `:filter` clears;
state is client-local and restart-cold). `route=me` means you resolve
as a handler — eligibility; `handler=me` means you HOLD the claim, and
unclaimed Work matches neither. `new=true` means your personal New is
nonzero. Filtering
runs inside the canonical snapshot: a matching child keeps its
nonmatching parent as `filter_match:false` context, the team summary
stays global, and the active filter is always disclosed — `Filter:N`
right-aligned on the header plus a dedicated clause line that viewports
at narrow widths.

Bold Titles are PERSONAL: a row is bold exactly when YOU can act on it — you hold its claim, or it is open/ready/unclaimed (not waiting or parked) with its Route resolving to you (every eligible handler until one claims; only the winner after), or you owe it an unresolved directed `@` (actionable even while blocked). Eligibility is TWO columns, not one: `Endpoint` is the stable
`team.kind` address a reader types, and `Via` is the selected internal
route that decides who may claim it — with W230 alternates, one endpoint
can be offered through two routes to two different agents, and a single
column showing the address hid that. `Handler` remains the exact
participant after a claim, so before a claim Endpoint plus Via say where
the Work is offered and after one Handler says who took it. Under width
pressure Via is dropped before Endpoint, and both before Handler; whole
columns go rather than identities being truncated. Terminal Work reports
no route at all — eligibility is a live question — so both cells read
`-` there, exactly as Handler does. Other people's activity reads
through Phase, Handler, and the final `Held` column — one MM:SS interpretation for every ordinary value (elapsed whole seconds, `00:00` through `99:59`, `∞` at 100 minutes and beyond). W15 removed the unclaimed `>` marker from both Phase and Held: the Handler column is blank when nobody holds the Work, so the marker restated a fact the row already carried. Held is a bare timer — since `claimed_at` while claimed, since the handoff while unclaimed, `-` with no origin — and Handler is what distinguishes the two intervals. The handoff instant stays in JSON as `handoff_at` beside the structured `pickup` state — claimed/pending/overdue — so agents read facts, never glyphs; `overdue` describes only a pickup that is actually possible, never dependency-blocked, waiting, parked, or terminal Work. Dependency readiness, waiting, and parking stay separate table and JSON facts: they explain why unclaimed Work may not be claimable, and never hide that it is unclaimed. There is no elapsed-time escalation and no claimant liveness suffix — a claimed agent can be alive and busy inside one model turn with no opportunity to call `heartbeat`, so silence is not treated as failure. Advanced on the ordinary refresh; no timeout mutates workflow authority. There is no indefinite animation; the phase cell blinks only as a short change cue — three scheduled refresh ticks after the console observes a genuine Phase change (cold on load and reconnect; keystrokes, redraws, resize, and immediate mutation refreshes neither consume nor restart it). The hot zone itself: any open Work someone is executing — which under W38 is exactly `phase=active`. Unclaimed, waiting, parked and closed Work stay steady; the personal pickup cue for ready unclaimed Work whose Route resolves to you is the separate bold-Title rule above. The cue is presentation-only — it never moves selection, marks anything seen, or touches the authority — and the textual phase, readiness, and claimant facts remain authoritative on terminals that ignore blink. Work carries one team-local priority —
`high`, `normal` (the default), `low` — an ordering signal only, never
a lifecycle fact. `create priority=...` records it at birth;
`prioritize work=... as=...` is the audited effectively-once revision,
open to any configured member of the OWNING team (other teams discuss
urgency in Threads). Root siblings and each child group rank high,
normal, low then creation order without leaving their parent. The
two-cell `Pr` column renders `Hi`/`No`/`Lo` and is the first column
omitted at narrow widths; JSON always carries the full strings.

The table's `Wait` field shows the inline dependency cue, arrowless:
`Wn` names the deterministic first OPEN blocker (oldest by creation)
and `Wn+N` adds the count of remaining open blockers; a row with no
open blocker has an empty cell, and satisfied edges leave it (the
ledger keeps history). `↳` remains exclusively the containment-tree
marker; `[b] deps` remains the full neighbor view; narrow layouts omit
the cue whole — never clipped or relabelled. The boolean Ready column
is gone: the cue names what must finish.

Every Work carries its authority-local short
selector — the `Id` column leading the table (`W11`, growing to fit
`W1000` and never truncating) and `local_id` beside `id` in JSON. Every
Work-valued operand accepts either spelling (`work=W11` or
`work=<authority>-W11`), resolved strictly against the ONE opened
authority: malformed, foreign, or missing selectors refuse by name, and
nothing is ever guessed from titles, cursor position, or partial
matches. Every operation operand is one
strict order-independent key=value token — the same grammar as the
standalone CLI (W13); the conventional options before the verb
(--config, --participant) are launcher context and stay put.

## Project roots

    $BW --config ~/your-home/baton.json --participant team.member \
        resolve locator=pushcoin:tmpl/work-basic-1.md
    $BW --config ~/your-home/baton.json bootstrap root=pushcoin

Every root in the accepted `baton.json` declares its explicit absolute
`base` — the single root config; there is no separate resolver file and
no filesystem inference. `bootstrap` vendors this release's `tmpl/`
into the resolved project root and never overwrites anything.
