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
destination Current AND the destination phase (`say ... pass-to=X
phase=review`, or derived from the destination route's stage role),
releases the sender's claim, and never claims for the recipient; entering
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
opens the selected Work's DETAILS (Threads above, the selected
Thread's Messages below, references under a separate Refs section),
u unfolds/re-roots the tree at the selected Work, Esc goes back,
Ctrl-W then h/j/k/l (or arrows, or w / another Ctrl-W) moves between
the detail panes, n pages forward through Messages or the Thread
list while more exists, p returns to the start (not a previous-page
step), s marks the shown page seen, z reveals closed rows, b opens
blocking/dependent links, q asks Exit? y/N on one row (y exits; n or Esc returns to the unchanged view). `:` opens the command bar: everything typed there is
the PUBLIC CLI grammar run as you (for example
`:create team=push kind=bug title="..." origin=self-initiated
body="..."`), with the public refusals. As you type, the bar shows context-sensitive assistance on the right — matching verbs, then the effective remaining required and optional keys (form conditions applied exactly as the parser enforces them), then closed values narrowed by your prefix — derived through a shared partial-command analyzer that speaks the same quoting and first-`=` rules as execution; malformed, unknown, or duplicated input shows the diagnostic instead. The assistance is read-only and yields to your input when space runs out. The caret stays visible at the insertion point; input longer than the row scrolls in a horizontal viewport (`<` marks the clipped left) and is never cut.

`::` (a second colon on the empty bar) opens the multiline **batch** buffer: Enter adds a line, `Ctrl-G` runs, `Esc` cancels — a visible legend names all three, and a pasted newline can never execute. Go first statically validates every line through the same parser (one refusal and nothing runs), then executes sequentially in written order, stopping at the first authority refusal; the pane honestly marks lines `ok` (completed — committed, never rolled back), `!!` (failed, with the public refusal), and `--` (unrun), and failed/unrun input stays editable. Mutating lines without an explicit `op-id=` carry a generated per-line identity retained across unedited retries, so a re-run replays committed results instead of duplicating them; completed lines are skipped. A batch is a command list, not a script: no variables, control flow, or expansion.

The table marks the operational **hot zone** with a slow terminal blink on the phase/status cell only: any open Work someone is executing (a non-null active claimant, any phase) and any open ready `review` Work awaiting its reviewer's claim. Blocked review, waiting, parked, and closed Work stay steady. The cue is presentation-only — it never moves selection, marks anything seen, or touches the authority — and the textual phase, readiness, and claimant facts remain authoritative on terminals that ignore blink. Every operation operand is one
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
