# Plan

**Status — 2026-08-17:** inventory complete; waiting for Slawomir's explicit
target and disconnect-window approval. No deletion is authorized.

1. [done] Produce the exact live-process, deployment, alias, configuration,
   and mailbox-data inventory.
2. [done] Establish the safety ordering: W102 shutdown/reconnect completes
   before W101 removes any source or stack path imported by the live process.
3. [next — human] Decide whether the mailbox archives are destroyed with the
   live/stale mailboxes or copied to a separately approved non-executable
   historical location, then approve the exact `/home/sl/baton` targets.
4. [human cutover] Record reconnection commands, stop the combined v10
   `codex-baton` stack, and verify every v10 consumer is gone. Start the
   standalone Codex app server, reconnect this session, and arm only the v11
   Codex readiness producer. Abort on any unexplained user, process, or path.
5. [human destructive gate] Re-enumerate the exact approved targets and reject
   links or unexpected members. Remove only those targets; never retry a
   failure with a broader or stronger deletion.
6. [verify] Prove human TUI, Codex readiness, and ACP implementation traffic
   through v11 alone; scan processes/configuration for v10 references and
   record removal/recovery results.
7. [then] Unblock W101 repository runtime removal.
