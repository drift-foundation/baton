# README ruling — offline, sandboxed peer coordination

Place the following value proposition immediately after the opening paragraph
and before the screenshot:

> Baton needs no Internet connection or coordination service. It runs fully
> offline and can be completely sandboxed. Participants coordinate as peers
> through a shared SQLite mailbox; there is no privileged coordinator, daemon,
> or always-on server.

This deliberately says "coordinate as peers" rather than claiming direct
network peer-to-peer transport: the peers are symmetric, but they communicate
through the shared mailbox.

Remove the HTML comment below the screenshot that calls it stale and
side-by-side. The current image is the post-trial stacked layout, and the PLAN
already records it as current; leaving the comment makes the README contradict
both the artifact and its recovery record.

## References

- `README.md`
- `assets/artwork/baton-tui.png`
- `work/finding-human-console/PLAN.md`
