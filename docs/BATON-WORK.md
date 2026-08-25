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

The active claim and the scheduler phase are ONE fact seen twice, not
two: `claim work=WORK` records WHO is executing and moves the Work to
`active` in the same transaction, because `active` means exactly that a
Handler holds it. So only `claim` reaches `active` — `phase to=active`
is refused and names the claim instead — and Handler and phase move
together here and in every releasing transition, which is what leaves
the invariant `active iff Handler` no window in which it is false. What
the phase does NOT say is what KIND of work this is: that is the
route's role, on its own axis. One eligible handler of the live Route
endpoint acquires open, ready, non-blocked/non-parked Work — every
condition rechecked inside the write transaction, so an earlier `ready`
observation is advisory and a competing claim fails closed naming the
recorded claimant. No execution
begins before the claim succeeds, and no HANDOFF happens without one
either: a pass is the current claimant's act, refused atomically for
any other actor including an eligible route peer, because handing Work
on is releasing a claim you hold. Moving Work nobody holds is
`reroute`, on the owning team's authority. A pass atomically records
the destination Route AND the destination phase through its own
canonical THREADLESS verb — `pass work=W to=team.kind comment="..."`
(W38: phase is a closed SCHEDULER axis — `queued` runnable and
unclaimed, `active` claimed, `block` gated, `parked` deferred, and
absent once terminal. A handoff hands over responsibility, not
activity, so it lands `queued`, whatever the destination role — and it
can land nothing else, since a claimant's Work is runnable by
construction: a gate arriving releases the claim. `phase=` is
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
block/parked and terminal close also release. `block` IS the phase such
Work is in — not a flag beside some other stage — and blocked Work
cannot be claimed, and therefore cannot be passed either; the refusal
names the phase and points at `reroute`. An abandoned or yielded claim
is recovered with `release work=WORK expect=team.member episode=N
reason=TEXT` — live Route-handler authority OR an owning-team member
holding the `recover` capability, an exact compare-and-swap against
both the recorded claimant and the assignment episode that claim was
offered under (`detail` publishes it as `episode_seq`), and a durable
reason; it clears the claimant and derives the scheduler state the Work
lands in, and the result names which `authorization` branch was used.
`episode=` is mandatory on every release including self-release,
because the claimant string alone cannot tell one claim from a later
one by the same participant. `recover` exists for the case the Route
cannot serve — the endpoint's only handler is the participant whose
managed turn died holding the claim — and is separate from `config`,
from Route membership, and from any runtime lease field. The projection carries
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

    [Jobs] [Teams] [Inbox *]                                 team.member

That row appears at the TOP LEVEL and nowhere else. The moment you
drill into something — a Work's detail, a re-rooted tree, a search, a
neighbour view — it is replaced by a breadcrumb naming the whole path
you walked, and the page you are on shows only its own tabs beneath
it:

    Jobs > the root > the child                              team.member
    [Jobs] [Messages] [Events]

Two tab rows on one screen would say you are in two places at once,
and one of them is a drill-down inside the other.

Those three local tabs belong to the Work the breadcrumb ENDS at, and
to nothing else. `Jobs` renders that Work as the tree root; `Messages`
and `Events` are that Work's own. Moving the highlight through the
tree changes which row you would open next and never which Work owns
Messages or Events — otherwise the conversation you were about to read
would move under you as you scrolled. A Work with children opens on
`Jobs`; one with none opens on `Messages` and keeps `Events` beside
it. Switching tabs is a local move: it changes no breadcrumb segment
and costs no Back.

`]` selects the next tab and `[` the previous one, with wrap-around.
They always act at the level you are ON: at the top level they move
between Jobs, Teams and Inbox; inside a drilled page they move that
page's own tabs and can never reach the top level. A drilled page with
no tabs of its own simply ignores them. They are the ONLY
tab-switching keys: `Tab` and `Shift-Tab` used to be aliases here and
are not any more, because Tab has a better job one level down. Where
the console is taking text — the command bar, a batch buffer, the
search line — `[` and `]` are typed characters like any other.

**Esc (or Left) goes back exactly one thing you did**, never straight
to the top — and each page comes back the way you left it: the same
row selected, the same local tab, the same pane. A search you drilled
a result out of is still there when you come back, and one more Esc
returns the table it was run from. Opening a Work from Inbox is a
HANDOFF into Jobs, so Back from there leaves you in Jobs rather than
returning to the Inbox row.

Back is browser history, not containment. The breadcrumb is
STRUCTURAL: it names the whole containment path of the Work you are
looking at, whether or not you opened each level. The Back stack
records what you actually DID. Opening a visible grandchild with one
Enter is one action, so one Esc returns to where you were, even though
the trail names two parents in between; explicitly opening the parent
and then its child is two actions and therefore two Escs. Selecting
rows, scrolling, filtering and moving between a page's local tabs
change nothing in that history, and going to the page you are already
on is not recorded at all.

The history is per session, bounded at 64 ordinary page transitions,
and starts empty on every launch. Past the bound the OLDEST ordinary
entry is dropped — but the page you originally drilled in from is kept
separately and is never dropped, so a long walk can always be left in
one Esc.

Narrow terminals drop the OLDEST breadcrumb segments and mark the
shortened trail with a leading `…`, because where you are now is the
part you cannot afford to lose. The participant identity keeps the
right edge at every width.

Every tab label is bracketed and the active one is HIGHLIGHTED. The
brackets say "this is a tab"; they do not say which tab you are in.

The Inbox tab carries one `*` while this participant owes an
unresolved action, and nothing at all when they do not. That is the
whole vocabulary: it is not a count, a severity, an error, or an
unseen marker, and unseen attention with nothing owed does not raise
it. It is derived from the same `owed_action` the `inbox` verb
projects, so the tab and the JSON cannot disagree; the `total` and
`unseen` counts live inside the Inbox view and in that projection,
beside the rows they describe.
A narrow terminal drops whole labels rather than painting half of one,
and the active tab is the last label it will drop.

There are no `[oblig] [park] [due]` header counters any more: owed
action is what Inbox is for, parked Work stays visible and filterable
in Jobs, and repeating either in a global header was noise.

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

Selecting a member opens its details as a two-column key/value table,
grouped into **Identity and routing**, **Workflow**, **Runner state**,
**Operational diagnostics** and **Last poke answer**. Every fact keeps
its own key — provider, model, session, incarnation, state, cause,
transition time, last contact and each operational fact — because
packing unrelated facts into one sentence is what makes a block like
this unreadable. Values share one column and a wrapped value continues
at that column rather than under its key, so a long session locator
still reads as one field's content and is recoverable in full on a
wide enough terminal.

**Operational diagnostics** is an inventory of what the adapter actually
published, so it holds exactly those facts and no row for one that is
absent. A published `Log` appears verbatim with its source and age; an
adapter that published none simply has no `Log` row, and a member that
published nothing at all has no section. Everywhere a fact IS present
the block follows the same rule — missing, `unknown`, stale and absent
stay visibly different from each other, and nothing is tidied into a
value that reads as reassuring. A terminal too short to hold
the block says how many rows it could not show and names `teams` as
the verb holding the whole record.

**Inbox** is participant-relative. It carries pending pokes addressed
to you, `@` obligations owed through a route you handle, due
verification trials your Route answers for, and unseen discussion in
threads your team has joined. Actionable WORK is deliberately absent —
that is Jobs, and one queue in two tabs makes "how much do I owe" a
number nobody can act on. The tab label carries `*` — and the label is
bold — whenever at least one row is an unresolved action you owe, even
one you have already read: seen state never hides that you are the
blocker. The `total` and `unseen` counts are in this view and in the
`inbox` verb, where the rows they count are visible. Rows name their type and say whether they are
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

Where it shows up: the Jobs `Run` column beside `Handler` (`-` when
the Work is unclaimed, which is a different fact from a runner nobody
can see), the Teams `State` column and Member details, and — for
`waiting-input` only — one owed row in the Inbox of the participant
the lease names as its action owner.

The two tables name different things and keep different columns.
`Handler` names the participant, so the Jobs column beside it says
only what that participant's runner is DOING and is headed `Run`. In
Teams a member is the row, so `Agent` there names the adapter family
(`codex`, `claude`, …) and `State` says what it is doing. The Members
table sizes itself to the terminal: `Role`, `Agent`, `State`, `Work`
and `Since` stay compact, and the room left over goes to the session
locator, which is shown COMPLETE whenever it fits. A narrow terminal
drops whole columns in a fixed order — `Session` first, because the
Member detail block below carries it in full — and anything it does
have to shorten ends in `…` rather than reading as a different,
shorter identifier. With no action owner named, the
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
summary and snapshot token, all read under one transaction.

Work that is CLAIMED below that three-level window is still shown,
because a roll-up that looks idle while somebody is working under it
is the one thing this view must not do. Beneath the deepest visible
ancestor of each such claim the console paints a `⋮` (or `...` where
the terminal's encoding cannot carry it) and then the exact active
Work, with its own identity, title, Handler and Run state:

    W2  Design v12 isolated workers
      ↳ W3  Prove local isolated execution
        ↳ W5  Build OCI reference worker and adapter
          ⋮
          ↳ W6631  Materialize exact source   team.member  working

The `⋮` says one or more containment levels were omitted. It is not a
Work: it has no Id, it cannot be selected, and no key acts on it. The
row under it is a real Work row and Enter opens it. An ancestor never
borrows its descendant's Handler or Phase — W5 above is still
unclaimed and still says so. Every concurrent claim gets its own row
rather than a count, one `⋮` is shared by all the claims under one
ancestor, and a claim already visible in the ordinary window is not
repeated. The same list rides JSON as `tree`'s `active_trails`, so
both surfaces read it from one snapshot.

Keys: j/k select, Enter OPENS the selected Work — and what that means
is decided by the Work, from the same child count the `▸N` disclosure
draws. A Work that contains other Work becomes the tree root and the
window (and its `⋮` groups) is recomputed beneath it. A Work that
contains none opens its DETAILS: the compact summary, the Thread
list, and below it a compact Message index (`M<seq>` labels over the
existing stable sequence, with author, time, and your personal
new/seen state) beside a reader showing exactly ONE selected message
— its metadata header, wrapped body, and references under a separate
Opening a Work puts the cursor in its MESSAGE INDEX. The Threads list
above it still selects the Thread — by the same New-first rule — and
still decides which Messages are shown; it simply is not where you
start, because most Work has one Thread and reading it was costing a
pane switch every time. `Shift-Tab` or `Ctrl-W k` reaches the Threads
list whenever the Work has several. This is the default for a FRESH
entry, from Jobs, from search results, or from an Inbox row's Work
context; moving between the detail tabs keeps whatever pane you chose.

Inside Work detail, `Tab` cycles pane focus forward through the panes
that view is painting and `Shift-Tab` cycles backward, wrapping — three
in Messages, two in Events. It is the discoverable alternative to
`Ctrl-W` plus `h`/`j`/`k`/`l`, which still moves geometrically and is
unchanged; the footer advertises both as `Tab/Ctrl-W panes`. Focus
movement is presentation only: it changes no selection, no seen state
and nothing in the authority. Where the console is taking text, Tab
keeps that surface's own contract — command-bar completion is still
completion.

Refs section. A Work page carries THREE tabs — `[Jobs]`, `[Messages]`
and `[Events]`, all bracketed like every other tab, with the active
one highlighted; a Work with children opens on `Jobs` and one without
opens on `Messages`. `]` selects the next tab and
`[` the previous, from anywhere in the detail view — the same keys and
the same wrap the top level uses — and the footer always advertises
`[/] tabs`. Events is the Work's
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
unfolds/re-roots the tree at the selected Work (the breadcrumb names
its whole containment path; one Esc leaves it), Esc goes back one
action, Ctrl-W then h/j/k/l (or arrows, or w / another
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
rows, u unfolds the selected Work explicitly (which is how you root at
a Work that has no children), [d] deps opens
the dependency NEIGHBOURHOOD GRAPH described below (from the table and
from search results alike), p opens the poke view described
below, q asks Exit? y/N on one row (y exits; n or Esc returns to the unchanged view). `:` opens the command bar: everything typed there is
the PUBLIC CLI grammar run as you (for example
`:create team=push kind=bug title="..." origin=self-initiated
body="..."`), with the public refusals. As you type, the bar shows context-sensitive assistance on the right — matching verbs, then the effective remaining required and optional keys (form conditions applied exactly as the parser enforces them), then closed values narrowed by your prefix — derived through a shared partial-command analyzer that speaks the same quoting and first-`=` rules as execution; malformed, unknown, or duplicated input shows the diagnostic instead. The assistance is read-only and yields to your input when space runs out. The caret stays visible at the insertion point; input longer than the row scrolls in a horizontal viewport (`<` marks the clipped left) and is never cut.

`::` (a second colon on the empty bar) opens the multiline **batch** buffer: Enter adds a line, `Ctrl-G` runs, `Esc` cancels — a visible legend names all three, and a pasted newline can never execute. Go first statically validates every line through the same parser (one refusal and nothing runs), then executes sequentially in written order, stopping at the first authority refusal; the pane honestly marks lines `ok` (completed — committed, never rolled back), `!!` (failed, with the public refusal), and `--` (unrun), and failed/unrun input stays editable. Mutating lines without an explicit `op-id=` carry a generated per-line identity retained across unedited retries, so a re-run replays committed results instead of duplicating them; completed lines are skipped. A batch is a command list, not a script: no variables, control flow, or expansion.


### The dependency graph

`[d] deps` opens the selected Work's dependency NEIGHBOURHOOD — the Work
between what it waits on and what waits on it — from the Jobs table and
from search results alike. It draws dependencies ONLY: containment stays
in the Jobs tree, and duplicates and follow-ups keep their own
projections.

```text
[W4487 open] --blocks--> [W2929 wait]
                         [W2929 wait] --blocks--> [W2930 queued]
                                                  [+3 dependents]
```

Every edge spells `--blocks-->` with the arrowhead at the CONSUMER, so
direction survives a pipe, a log paste and a screen reader. There is no
colour, no Unicode and no information in styling. Each Work is drawn as
its stable local selector and status, which is the same spelling every
other console surface and `local_id` in JSON use.

**What the graph promises.** It is exactly the canonical dependency
projection — upstream keeps every recorded blocker including a satisfied
one, downstream keeps only live consumers, and a renderer never invents
edge lifetime. It is also BOUNDED, and every bound is disclosed with an
exact count rather than left to be inferred:

- depth 1 to 3, shown in the footer as `depth N/3`;
- four direct neighbours per branch, with `[+N blockers]` or
  `[+N dependents]` naming exactly how many that branch is not drawing;
- `[+N deeper blockers]` / `[+N deeper dependents]` naming what the DEPTH
  bound cut off, which is a different absence opened by a different key;
- a 200-occurrence view cap, which says `view cap 200 reached` when it is.

A truncated graph that looked complete would be worse than no graph, so
none of those counts is ever a guess.

**Keys.**

| key | meaning |
| --- | --- |
| `j` / `k`, Up / Down | move to the next or previous Work or token |
| Enter on a Work | recenter the graph on it |
| Enter on `[+N blockers]` / `[+N dependents]` | draw one more page of THAT branch |
| `+` / `-` | change depth within 1..3 |
| Esc | back one level, ending at the table you came from |

`j`/`k` traverse one deterministic order — upstream outermost-to-centre,
the centre, then downstream centre-to-outermost, with each branch's
overflow token after its visible siblings. A Work drawn on several
relationships is ONE stop, and every one of its appearances is
highlighted.

Enter on a Work recenters IN THE GRAPH and does not jump to the Jobs
table. The depth is preserved, branch expansions reset, and the selection
becomes the new centre. Esc restores the exact prior graph — centre,
depth, selection and branch pages together — and the last Esc returns to
the table or search results you left, with its row and view state intact.

A depth-frontier token is opened with `+`, not Enter, because widening a
branch page and lifting the depth bound are different acts; pressing
Enter on one says so rather than doing the other.

**Narrow terminals lose layout, never a relationship.** The wide form
places each Work in its shortest-path column; when that will not fit,
the graph falls back to one edge per row, and then to source, arrow and
target on three rows. Every renderer draws the same Works and the same
edges in the same order, so `j`/`k` mean the same thing at every width
and a resize can never move an action to another Work. A terminal too
narrow for one complete selector refuses explicitly rather than clipping
an identity — a clipped id is a different Work as far as your eyes are
concerned.

If the store is damaged — a dependency cycle, or an edge naming Work the
authority does not hold — the page refuses visibly and names the exact
edge. It does not draw a smaller graph that looks complete.

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
at narrow widths. "Always" includes every drilled page: a breadcrumb
header carries the same tag beside the identity, and the trail is
shortened around both rather than over them. Search results are
themselves narrowed by the active filter, so that is exactly where the
disclosure has to survive.

Bold Titles are PERSONAL: a row is bold exactly when YOU can act on it — you hold its claim, or it is open/ready/unclaimed (not blocked or parked) with its Route resolving to you (every eligible handler until one claims; only the winner after), or you owe it an unresolved directed `@` (actionable even while blocked). Eligibility is TWO columns, not one: `Endpoint` is the stable
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
through Phase, Handler, and the final `Held` column — one MM:SS interpretation for every ordinary value (elapsed whole seconds, `00:00` through `99:59`, `∞` at 100 minutes and beyond). W15 removed the unclaimed `>` marker from both Phase and Held: the Handler column is blank when nobody holds the Work, so the marker restated a fact the row already carried. Held is a bare timer — since `claimed_at` while claimed, since the handoff while unclaimed, `-` with no origin — and Handler is what distinguishes the two intervals. The handoff instant stays in JSON as `handoff_at` beside the structured `pickup` state — claimed/pending/overdue — so agents read facts, never glyphs; `overdue` describes only a pickup that is actually possible, never blocked, parked, or terminal Work. W2938 removes the `New` column from this list for horizontal-space priority and adds NO replacement to it — personal unseen state is canonical JSON and stays visible everywhere it drives an action, in Inbox, Threads, Message indexes, Work detail and explicit `new` reads. A Job is queued and unclaimed; it is not the entity that owes a claim. The AGENT with free capacity owes pickup, one obligation per participant however many Jobs it could take, so that cue lives on **Teams** and never annotates a Work row.

**Claim pickup is a participant obligation.** A participant holds exactly ONE active claim across all Routes; a second is refused, naming the Work already held. That capacity unit is what makes "free capacity" answerable, and the pickup cue depends on it. An idle participant whose actionable pool — the unclaimed half of their `wait` action set — is nonempty owes exactly one pickup: **claim one actionable Job**. Ten offered Jobs are one obligation, not ten. Adding, removing, reprioritizing or reordering Work neither multiplies nor resets it while that pool stays continuously nonempty, including when a competing handler takes one of them. Claiming ANY eligible Work clears it, because the participant becomes busy; an emptied pool or lost Route eligibility clears it too. A participant who later becomes idle with Work still waiting starts a NEW interval, and the earlier elapsed time never resumes. The interval and its start are canonical, so they survive a client or runner restart, and `pending` versus `overdue` is derived at read time — no timeout event, no workflow mutation. The default threshold is 360 seconds; a deployment may set a positive `instance.pickup_overdue_seconds`, and the accepted value rides the `teams` read as `pickup_overdue_seconds` — acquired once inside the same snapshot the member states are derived in, so a response never announces one policy beside states computed with another. A missing or invalid accepted value is an invalid authority and refuses; the defaulting lives at acceptance, where omission legitimately means 360, and no client falls back to a local guess. Teams member rows carry `Pickup` — `-`, `pend` or `late` — an overdue member's row is bold, and member detail spells out the state, the elapsed interval and the canonical first actionable Work as a suggested next claim. That locator is diagnostic; it does not own the obligation. The top-level tab renders `[Teams *]` when at least one participant is overdue and plain `[Teams]` otherwise, reusing the Inbox `*` vocabulary rather than inventing another glyph; pending alone never stars, and the star carries no count. On a shared Route every idle eligible participant evaluates its own single interval, and the atomic claim stays the arbiter. Dependency readiness, blocking, and parking stay separate table and JSON facts: they explain why unclaimed Work may not be claimable, and never hide that it is unclaimed. There is no elapsed-time escalation and no claimant liveness suffix — a claimed agent can be alive and busy inside one model turn with no opportunity to call `heartbeat`, so silence is not treated as failure. Advanced on the ordinary refresh; no timeout mutates workflow authority. There is no indefinite animation; the phase cell blinks only as a short change cue — three scheduled refresh ticks after the console observes a genuine Phase change (cold on load and reconnect; keystrokes, redraws, resize, and immediate mutation refreshes neither consume nor restart it). The hot zone itself: any open Work someone is executing — which under W38 is exactly `phase=active`. Unclaimed, blocked, parked and closed Work stay steady; the personal pickup cue for ready unclaimed Work whose Route resolves to you is the separate bold-Title rule above. The cue is presentation-only — it never moves selection, marks anything seen, or touches the authority — and the textual phase, readiness, and claimant facts remain authoritative on terminals that ignore blink. Work carries one team-local priority —
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
marker; `[d] deps` remains the full neighbour view, now drawn as the
graph described under **The dependency graph** below; narrow layouts
omit the cue whole — never clipped or relabelled. The boolean Ready column
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
