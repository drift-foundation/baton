# Plan

**Status — 2026-08-18:** inventory and approvals are complete. The fresh
projection-9 authority is live, but the old combined supervisor restarted its
v10 consumers with this Codex session. The approved disconnect/reconnect gate
is now the active step; deletion remains bounded to the separately validated
`/home/sl/baton` inventory after v11-only process proof.

1. [done] Produce the exact live-process, deployment, alias, configuration,
   and mailbox-data inventory.
2. [done] Establish the safety ordering: W102 shutdown/reconnect completes
   before W101 removes any source or stack path imported by the live process.
3. [done — human] Destroy the mailbox archives with the live/stale mailboxes;
   no archive is required. The exact `/home/sl/baton` target was approved.
4. [done — human cutover] Record reconnection commands, stop the combined v10
   `codex-baton` stack, and verify every v10 consumer is gone. Start the
   standalone Codex app server, reconnect this session, and arm only the v11
   Codex readiness producer. Abort on any unexplained user, process, or path.
5. [done — human destructive gate] Re-enumerate the exact approved targets and
   reject links or unexpected members. The bounded attempt removed writable
   material and stopped on two immutable exact releases; Slawomir then removed
   those exact remaining trees. `/home/sl/baton` is absent.
6. [done — verify] Prove human TUI, Codex readiness, and ACP implementation traffic
   through v11 alone; scan processes/configuration for v10 references and
   record removal/recovery results.
7. [next] Close W3 satisfying to wake W4 for repository runtime removal.
