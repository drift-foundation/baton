# Plan

**Status — 2026-08-17:** the active public surface is rewritten and pinned by
focused regressions. The two Codex documents are split into their own tracked
child (W233) because they cannot be written until W101 lands.

1. [done] Replace `README.md` with a concise v11 entry point — topology, the
   three boundaries, a v11-only quickstart, the strict grammar, and links
   rather than a duplicated operator contract.
2. [done] Replace `docs/AGENTS-MAILBOX-PROTO.md` with the protocol-11 agent
   contract, keeping the stable filename and saying why. Round one corrected
   the `wait` contract to state BOTH halves — unclaimed Work for every
   eligible handler, and already-claimed Work returned to its exact claimant
   so a restart does not walk past its own assignment.
3. [done] Remove `docs/LEGACY-CUTOVER-ON-DEMAND.md` (live fallback guidance)
   and `assets/artwork/baton-tui.png` (the retired v10 inbox). No v11 image is
   claimed to exist; producing one needs a scratch authority and human review
   of what it exposes.
4. [done] Reconcile `tools/acp-baton-bridge/README.md`: co-deployment stated
   without contradiction, and the projection major no longer frozen in prose —
   it moves with the canonical gate, and a number restated here is a second
   source of truth that goes stale silently.
5. [done] Ship `doc/AGENTS-MAILBOX-PROTO.md` with the release so a team
   bootstraps its agent policy from the same exact release as its CLI.
6. [done] Standing acceptance regressions, replacing the one-time manual
   checks: deployed agent policy byte-equal to source and naming protocol 11;
   an active-document scan for retired launch paths and taught mailbox verbs;
   every README repository link resolving; both halves of the `wait` contract;
   and a self-retiring check that the README does not route readers into
   `EFFECTIVE-BATON.md` while it is still v10.
7. [done] Do not certify in-flight grammar. The README and agent policy
   describe the CERTIFIED release; the W159 wait-by-default wording was
   removed while that Work is still in review, and returns when it is
   accepted.
8. [split to W233] The two Codex documents. They must describe the shape that
   exists after W101 removes the v10 monitor stack, and W101 is itself held
   until W102 completes the standalone cutover.
