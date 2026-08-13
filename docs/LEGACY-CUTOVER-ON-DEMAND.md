# Baton moved — on-demand participant handoff

Copy this message to a participant that returns after a move:

> Baton moved to `/home/sl/baton/mailbox/legacy/`. If that directory contains
> a `MOVED` file instead of `baton.json`, follow the directory named there.
> Keep following `MOVED` one version at a time until you reach the current
> mailbox, then use the connection instructions stored there. Ask Slawomir if
> a hop is missing or unclear; do not guess or restore an older mailbox.

Each retired mailbox directory remains as one human-readable hop to the next.
The chain is manual: Baton clients do not automatically follow `MOVED`.
