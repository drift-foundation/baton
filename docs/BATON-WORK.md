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

The active claim is its own authority state, orthogonal to phase: `claim
work=WORK` records WHO is executing without touching WHAT stage the phase
names. One eligible handler of the live Current endpoint acquires open,
ready, non-waiting/non-parked Work — every condition rechecked inside the
write transaction, so an earlier `ready` observation is advisory and a
competing claim fails closed naming the recorded claimant. No execution
begins before the claim succeeds. A pass atomically records the
destination Current AND the destination phase through its own canonical
THREADLESS verb — `pass work=W to=team.kind phase=review comment="..."`
(phase derived from the destination route's stage role when omitted;
`comment=` is durable handoff evidence stored with the authoritative
pass event itself, never a discussion message; `set-next=` plants the
planned return; `thread=` is refused as an unknown key — a Work
transfer has no thread-selection decision) — releases the sender's
claim, and never claims for the recipient. A pass creates no Message,
advances no cursor, and changes no Message/My/New/obligation count;
conversation stays explicit through `say`. Plain `say` is discussion
(plus the `@ request=` operator); it carries no transfer keys; entering
waiting/parked and terminal close also release. Blocked Work keeps its
honest stage phase but cannot be claimed. An abandoned or yielded claim
is recovered with `release work=WORK expect=team.member reason=TEXT` —
live Current-handler authority, an exact compare-and-swap against the
recorded claimant, and a durable reason; it clears only the claimant.
The projection carries `active` (JSON) and the detail facts name the
claimant.

The console renders the same canonical projection the JSON surface
serves. It refreshes automatically on a timer — default every 2
seconds, configurable with `tui refresh=SECONDS` (positive) — and
that timer is the ONLY background read: ordinary keystrokes operate
on the cached projection and never poll the authority. A background
refresh is read-only and keeps the selection on the same Work.

The main screen is a two-level containment tree: top-level Work with
each root's immediate `↳` children; a `▸N` disclosure marks a child
holding deeper children, reached with `u`. The tree the console
paints is one canonical projection — the JSON verb `tree` (optionally
`tree WORK` for a re-rooted window) returns the identical rows,
summary and snapshot token, all read under one transaction. Keys: j/k select, Enter
opens the selected Work's DETAILS: the compact summary, the Thread
list, and below it a compact Message index (`M<seq>` labels over the
existing stable sequence, with author, time, and your personal
new/seen state) beside a reader showing exactly ONE selected message
— its metadata header, wrapped body, and references under a separate
Refs section. The split-area headings identify pane ROLES —
`Messages (N)` over the index and `Message M<seq>` over the reader —
never content already visible elsewhere: the Thread row alone owns the
discussion subject, the reversed index row owns selection, and one
blank separator row (spacing, not a border) divides the Thread list
from the lower panes. At usable width the index sits left of the
reader; at narrow width they stack, index above reader — never merged
into a flat stream. Selecting a Thread opens its first personal-new message
when one exists. u unfolds/re-roots the tree at the selected Work,
Esc goes back, Ctrl-W then h/j/k/l (or arrows, or w / another
Ctrl-W) moves across the three regions (Threads, index, reader),
j/k select within the focused region (in the reader they scroll a
long body, tagged `M<seq> (cont.)`), n pages forward through the
Message index or the Thread list while more exists, p returns to the
start (not a previous-page step), s advances your seen cursor
through the SELECTED message and no later one, z reveals closed
rows, [b] deps opens
the blocking/dependent neighbor view, q asks Exit? y/N on one row (y exits; n or Esc returns to the unchanged view). `:` opens the command bar: everything typed there is
the PUBLIC CLI grammar run as you (for example
`:create team=push kind=bug title="..." origin=self-initiated
body="..."`), with the public refusals. As you type, the bar shows context-sensitive assistance on the right — matching verbs, then the effective remaining required and optional keys (form conditions applied exactly as the parser enforces them), then closed values narrowed by your prefix — derived through a shared partial-command analyzer that speaks the same quoting and first-`=` rules as execution; malformed, unknown, or duplicated input shows the diagnostic instead. The assistance is read-only and yields to your input when space runs out. The caret stays visible at the insertion point; input longer than the row scrolls in a horizontal viewport (`<` marks the clipped left) and is never cut.

`::` (a second colon on the empty bar) opens the multiline **batch** buffer: Enter adds a line, `Ctrl-G` runs, `Esc` cancels — a visible legend names all three, and a pasted newline can never execute. Go first statically validates every line through the same parser (one refusal and nothing runs), then executes sequentially in written order, stopping at the first authority refusal; the pane honestly marks lines `ok` (completed — committed, never rolled back), `!!` (failed, with the public refusal), and `--` (unrun), and failed/unrun input stays editable. Mutating lines without an explicit `op-id=` carry a generated per-line identity retained across unedited retries, so a re-run replays committed results instead of duplicating them; completed lines are skipped. A batch is a command list, not a script: no variables, control flow, or expansion.

Wakeups are PARTICIPANT-relative: `wait`
returns the one canonical action projection for your exact identity —
open ready unclaimed Work whose Current resolves to you (every eligible
handler until one claims; the claimant alone after, under the same
stable `work:` key), pending `@` obligations your endpoint owes
(`obligation:` keyed by seq), and due verification rounds your Current
answers for (`round:` keyed per deadline generation, retired by
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
Six minutes without a successful beat renders the informational `!`
suffix on the Age cell (`12:04!`); the next beat clears it. The alert
is never a lease: Baton never auto-releases, transfers, rephases, or
admits a second claimant on staleness — recovery stays the explicit
release path. Only the exact current claimant may beat (rechecked in
the committing transaction), the audited event journal is the record,
and canonical JSON exposes `heartbeat_at` scoped to the current claim
epoch so every client reaches the same conclusion.

Work lists filter composably over canonical
facts — `home`, `tree`, and `tui` take the same optional operands
(`team= status= phase= current= category= ready= new= priority=`, full
canonical values only, AND composition, one value per field), and the
console's `:filter` shares the exact grammar (bare `:filter` clears;
state is client-local and restart-cold). `current=me` means you resolve
as a handler; `new=true` means your personal New is nonzero. Filtering
runs inside the canonical snapshot: a matching child keeps its
nonmatching parent as `filter_match:false` context, the team summary
stays global, and the active filter is always disclosed — `Filter:N`
right-aligned on the header plus a dedicated clause line that viewports
at narrow widths.

Bold Titles are PERSONAL: a row is bold exactly when YOU can act on it — you hold its claim, or it is open/ready/unclaimed (not waiting or parked) with its Current resolving to you (every eligible handler until one claims; only the winner after), or you owe it an unresolved directed `@` (actionable even while blocked). Other people's activity reads through Phase, Current, and the final `Age` column — elapsed time since the current claim committed (MM:SS under an hour, HH:MM through 99 hours, `99h+` beyond, `-` unclaimed), advanced on the ordinary refresh from the canonical `claimed_at` fact. There is no indefinite animation; the phase cell blinks only as a short change cue — three scheduled refresh ticks after the console observes a genuine Phase change (cold on load and reconnect; keystrokes, redraws, resize, and immediate mutation refreshes neither consume nor restart it). The hot zone itself: any open Work someone is executing (a non-null active claimant, any phase) and any open ready `review` Work awaiting its reviewer's claim. Blocked review, waiting, parked, and closed Work stay steady. The cue is presentation-only — it never moves selection, marks anything seen, or touches the authority — and the textual phase, readiness, and claimant facts remain authoritative on terminals that ignore blink. Work carries one team-local priority —
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
