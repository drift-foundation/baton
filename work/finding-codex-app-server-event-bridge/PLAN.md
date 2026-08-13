# Plan

1. **Done:** inspect `codex-cli 0.147.0` help, generate authoritative app-server schemas, and supersede the original single-thread architecture with the N-target dispatcher model.
2. **Done:** refactor `CodexClient` into a server-scoped, thread-ID-based protocol adapter and prove two-thread concurrent peer subscriptions against the installed app-server.
3. **Done:** implement and verify target routing, per-target and global bounds, target-scoped deduplication, concurrent independent dispatch, overload retry, ambiguous-delivery handling, reconnect-all reconciliation, and clean reconnect-loop shutdown.
4. **Done:** implement and verify the Unix sender, bounded `run-and-notify`, build-result watcher, example multi-server/multi-target configuration, foreground documentation, and a real Baton-PONG producer-edge smoke.
5. **Queued:** verify normal-TUI continuity, effective settings, and approval ownership, then run the manual one-server/five-thread/five-TUI acceptance gate without terminal automation.
6. **In progress:** replace the partial app-server-only operator recipe with a supervised app-server + bridge + Baton-monitor stack recipe, gate monitor startup on successful initial resume of every configured thread, and verify startup/failure cleanup behavior.
