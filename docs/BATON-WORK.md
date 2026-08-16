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
refresh is read-only and keeps the selection on the same Work. Keys: j/k select, Enter drill (tables, links, threads),
Esc back, o focused Work view, b blocking/dependent neighbors,
z reveal closed rows, n page forward through a thread's Msgs or the
thread list, p return to its start (not a previous-page step),
s mark the painted page seen, q quit. `:` opens the command bar: everything typed there is
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
