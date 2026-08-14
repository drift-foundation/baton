# v10 cutover: config repointed, restart is Slawomir's

## Done

`/home/sl/baton/conf/codex-event-bridge.json`:

    binary: app/baton-cli/legacy/bin/baton  ->  app/baton-cli/v10/v10.2.0/bin/baton
    config: mailbox/legacy/baton.json       ->  mailbox/v10/baton.json

Verified before handing it back: the 10.2.0 binary reports
`baton 10.2.0 (protocol 10)`, opens `mailbox/v10` — so the handshake against
`namespace: v10` passes — and `scan` answers on an empty queue. The previous
config is kept at `$JOB/tmp/bridge-legacy.bak`.

PLAN step 1: the only active claim on legacy was mine, on the GO message; this
reply releases it.

## Why I did not do step 3

The bridge stack is Slawomir's. They asked for it back ("shut it down, I run
it"), I handed it over, and it is running in their terminal — so stopping it
is theirs to do. Asked, and they chose the split: I repoint, they restart.

    # in Slawomir's terminal
    ctrl-C the running stack, then:
    just codex-baton /home/sl/baton/conf/codex-event-bridge.json

    # their console, on the successor
    /home/sl/baton/app/baton-tui/v10/v10.2.0/bin/baton-tui \
        --config /home/sl/baton/mailbox/v10/baton.json \
        --participant human.slawomir

## What happens at the restart

All ten monitors come up on v10, and this conversation moves with them: my own
monitor is armed on `mailbox/v10`. **Ping me there and I will answer there** —
that round trip plus a scoped-notice receipt is PLAN step 6, and I will report
both.

`mailbox/legacy` is untouched: 991 completed, 513 closed, and the three
cross-team messages from 2026-08-12 that stay behind by ruling.

## A note on where this file lives

`work/finding-product-version-manifest/` no longer exists. Commit `fb9420a`
("Release Baton 10.2.0 under protocol-generation layout") shipped the code and
the work notes were dropped rather than committed — reasonably, since I had
flagged that 115 note files probably did not belong in a code commit. The
consequence worth knowing: PROGRESS.md and every runbook that lived there are
gone from the working tree and are not in Git.

**They are not lost.** Every one was published as a durable Baton message part
before the commit, so they are recoverable from the authority with
`materialize`. That is the whole reason reports go through Baton rather than
staying in the terminal. If anyone wants them back on disk, say so and I will
project them out of the mailbox — but note they would come from
`mailbox/legacy`, which is the authority being retired, so recover before that
copy stops being consulted.
