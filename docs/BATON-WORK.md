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
the blocking/dependent neighbor view, q asks Exit? y/N on one row (y exits; n or Esc returns to the unchanged view). `:` opens the command bar: everything typed there is
the PUBLIC CLI grammar run as you (for example
`:create team=push kind=bug title="..." origin=self-initiated
body="..."`), with the public refusals. As you type, the bar shows context-sensitive assistance on the right — matching verbs, then the effective remaining required and optional keys (form conditions applied exactly as the parser enforces them), then closed values narrowed by your prefix — derived through a shared partial-command analyzer that speaks the same quoting and first-`=` rules as execution; malformed, unknown, or duplicated input shows the diagnostic instead. The assistance is read-only and yields to your input when space runs out. The caret stays visible at the insertion point; input longer than the row scrolls in a horizontal viewport (`<` marks the clipped left) and is never cut.

`::` (a second colon on the empty bar) opens the multiline **batch** buffer: Enter adds a line, `Ctrl-G` runs, `Esc` cancels — a visible legend names all three, and a pasted newline can never execute. Go first statically validates every line through the same parser (one refusal and nothing runs), then executes sequentially in written order, stopping at the first authority refusal; the pane honestly marks lines `ok` (completed — committed, never rolled back), `!!` (failed, with the public refusal), and `--` (unrun), and failed/unrun input stays editable. Mutating lines without an explicit `op-id=` carry a generated per-line identity retained across unedited retries, so a re-run replays committed results instead of duplicating them; completed lines are skipped. A batch is a command list, not a script: no variables, control flow, or expansion.

Wakeups are PARTICIPANT-relative: `wait`
returns the one canonical action projection for your exact identity —
open ready unclaimed Work whose Route resolves to you (every eligible
handler until one claims; the claimant alone after, under the same
stable `work:` key), pending `@` obligations your endpoint owes
(`obligation:` keyed by seq), and due verification trials your Route
answers for (`trial:` keyed per deadline generation, retired by
extension). `+`, plain posts, and personal New are attention, never
wakeups. The header's oblig/due counters are these same personal facts;
the parked count stays team-wide.

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

Bold Titles are PERSONAL: a row is bold exactly when YOU can act on it — you hold its claim, or it is open/ready/unclaimed (not waiting or parked) with its Route resolving to you (every eligible handler until one claims; only the winner after), or you owe it an unresolved directed `@` (actionable even while blocked). Other people's activity reads through Phase, Handler, and the final `Held` column — one MM:SS interpretation for every ordinary value (elapsed whole seconds, `00:00` through `99:59`, `∞` at 100 minutes and beyond). W15 removed the unclaimed `>` marker from both Phase and Held: the Handler column is blank when nobody holds the Work, so the marker restated a fact the row already carried. Held is a bare timer — since `claimed_at` while claimed, since the handoff while unclaimed, `-` with no origin — and Handler is what distinguishes the two intervals. The handoff instant stays in JSON as `handoff_at` beside the structured `pickup` state — claimed/pending/overdue — so agents read facts, never glyphs; `overdue` describes only a pickup that is actually possible, never dependency-blocked, waiting, parked, or terminal Work. Dependency readiness, waiting, and parking stay separate table and JSON facts: they explain why unclaimed Work may not be claimable, and never hide that it is unclaimed. There is no elapsed-time escalation and no claimant liveness suffix — a claimed agent can be alive and busy inside one model turn with no opportunity to call `heartbeat`, so silence is not treated as failure. Advanced on the ordinary refresh; no timeout mutates workflow authority. There is no indefinite animation; the phase cell blinks only as a short change cue — three scheduled refresh ticks after the console observes a genuine Phase change (cold on load and reconnect; keystrokes, redraws, resize, and immediate mutation refreshes neither consume nor restart it). The hot zone itself: any open Work someone is executing — which under W38 is exactly `phase=active`. Unclaimed, waiting, parked and closed Work stay steady; the personal pickup cue for ready unclaimed Work whose Route resolves to you is the separate bold-Title rule above. The cue is presentation-only — it never moves selection, marks anything seen, or touches the authority — and the textual phase, readiness, and claimant facts remain authoritative on terminals that ignore blink. Work carries one team-local priority —
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
