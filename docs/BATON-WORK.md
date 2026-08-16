# baton-work — the v11 coordination product

`baton-work` is the protocol-11 Work authority: a strict `baton.json`
configuration, one SQLite authority per instance, a JSON CLI for
agents, and a curses console for humans. This document is the
operator quickstart shipped with every release; the repository's
design dossier holds the full rulings.

## Install

Each release is deployed into a NEW explicit immutable directory:

    just deploy-v11 /your/dist/baton-work-rN

Run that command from the Baton source checkout. The recipe owns the internal
packaging mechanism; operators do not invoke it directly.

The installed layout is:

    bin/baton-work     the executable (JSON CLI + `tui`)
    doc/               this document
    conf/              the configuration example and scaffold seeds
                       (init consumes them; a partial release refuses)
    tmpl/              the numbered dossier templates bootstrap vendors

Nothing outside the target directory is read or written; deploying
never touches an existing directory.

## Create a coordination home

    mkdir -p ~/your-home
    /your/dist/baton-work-rN/bin/baton-work init ~/your-home
    # edit ~/your-home/baton.json — teams, roles, routes, kinds;
    # conf/baton.example.json shows a complete valid document
    /your/dist/baton-work-rN/bin/baton-work --participant team.member \
        activate ~/your-home

`init` is one-shot and creates no database; `activate` is the one
authoritative validation and creates the SQLite authority only when
the document passes. A refusal leaves nothing behind.

## Use it

    BW=/your/dist/baton-work-rN/bin/baton-work
    $BW --config ~/your-home/baton.json --participant team.member home
    $BW --config ~/your-home/baton.json --participant team.member tui

The console renders the same canonical projection the JSON surface
serves. It refreshes automatically on a timer — default every 2
seconds, configurable with `tui --refresh SECONDS` (positive) — and
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
blocking/dependent links, q quits. `:` opens the command bar: everything typed there is
the PUBLIC CLI grammar run as you (for example
`:create --team push --kind bug --title "..." --origin
self-initiated --body "..."`), with the public refusals.

## Project roots

    $BW resolve pushcoin:tmpl/work-basic-1.md --roots-file roots.json \
        --config ~/your-home/baton.json --participant team.member
    $BW bootstrap --root pushcoin --roots-file roots.json

`roots.json` is the machine-local resolver
(`{"roots": {"id": "/absolute/base"}}`); it never enters authority
state. `bootstrap` vendors this release's `tmpl/` into the resolved
project root and never overwrites anything.
