# The amended Gate B handoff: a real v11-only deploy command

In reply to follow-up `21fb9695d63413f0fd06b31bea5178aa` (claim
`ffead4410078f5156d60e8a36fafaaef`).

## What changed

1. **`tools/deploy_work.py`** — the v11-only deployer. It shares
   nothing with the frozen v10 `tools/deploy.py`, reads no v10
   catalog, and never touches a v10 path. It builds the baton-work
   zipapp (`cli:entry`, `/usr/bin/env python3`, executable bit) and
   publishes the ruled release layout — `<target>/bin/baton-work`
   plus the sibling `<target>/tmpl/` numbered assets (M6: never
   embedded) — by ONE atomic rename of a scratch directory beside
   the target: the visible state is the complete distribution or
   nothing. The explicit target must NOT already exist (an exact
   release directory is immutable — each release is a NEW directory);
   a missing parent refuses; nothing is ever adopted, overwritten,
   or deleted.
2. **Temp-only acceptance** (`tests/work/test_deploy_v11.py`): the
   ruled layout with byte-equal assets and no zipapp embedding;
   immutability and missing-parent refusals; and the INSTALLED
   executable running the whole onboarding story — init → edit →
   activate → create → home → bootstrap (vendoring the DEPLOYED
   sibling tmpl, proving release-layout asset resolution) → the
   deployed TUI on a real PTY. Nothing touches a real distribution,
   home, or v10.
3. Your five new TUI regressions are green, implemented as specified:
   the responsive budget always fits (drop order now
   CLS→DEP→PROG→PHASE→READY→NEXT; ST/CURRENT/NEW and the title
   survive to the narrowest checked widths); a full page of open
   rows RESERVES the hidden-closed footer line so the collapse is
   never silenced by a full viewport; long tables SCROLL so the row
   Enter will act on is always painted; the focused view lists the
   projection-declared `available_transitions` as `can: ...`.

## The handoff commands (deploy-based, superseding the zipapp steps)

Choose your distribution directory and coordination home; nothing is
inferred. Verified end-to-end on this machine with the complete v10
mailbox tree hash-identical before and after:

    cd ~/src/baton
    python3 tools/deploy_work.py ~/opt/baton-work/r1

    mkdir -p ~/baton-v11
    ~/opt/baton-work/r1/bin/baton-work init ~/baton-v11
    # edit ~/baton-v11/baton.json — your teams (see BATON-SETUP.md)
    ~/opt/baton-work/r1/bin/baton-work --participant TEAM.MEMBER \
        activate ~/baton-v11
    ~/opt/baton-work/r1/bin/baton-work \
        --config ~/baton-v11/baton.json --participant TEAM.MEMBER tui

The deployer prints the executable path and archive sha256; every
subsequent act (create/say/home/bootstrap/tui, JSON or console) runs
through that one installed executable. The `~/opt/baton-work/r1` and
`~/baton-v11` names above are EXAMPLES — both are yours to choose;
the tool refuses to guess and refuses to reuse an existing directory.

For the joint trial (human + reviewer + implementer beside live v10):
once you have activated the home with the three participants in its
teams, the reviewer and I join with the same executable and
`--config <home>/baton.json --participant <us>`. Awaiting your
chosen paths and roster (decision T3); v10 stays the live channel
throughout, per the pinned parallel-trial boundary.

## Sweeps and gates

Break-sweeps, all bit and restored (no residue): deployer
overwriting in place; templates embedded in the zipapp; sibling
assets dropped; scrolling dropped; the footer reserve dropped; the
transitions line dropped; the drop-order truncated.

Focused: 28 passed (TUI incl. your five regressions, parity,
packaged, deploy). `just test-v11`: 526 parallel + 3 serial passed.
Dossier: PROGRESS.md Step 51. Automated acceptance stayed temp-only;
production operations remain held.
