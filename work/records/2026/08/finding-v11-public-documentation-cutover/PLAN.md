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
8. [done — resolved 2026-08-19, not by this Work] The two Codex documents.
   They were held until W101 removed the v10 monitor stack. That removal
   landed with the v11 cutover: `stack.mjs` and `baton_source.mjs` are gone,
   nothing imports them, and both documents already describe the standalone
   app server, the generic dispatcher and the separately launched
   `codex-baton-bridge` whose entry points exist. Re-read and verified rather
   than rewritten; the split child needs no successor on the current ledger.
9. [done 2026-08-18] Add the confirmed product one-liner, distinguish generic
   ACP-compatible agents from the separate Codex bridge, and explain provider
   resilience plus model/persona assignment as reasons to use Baton.
10. [done 2026-08-18] Make the architecture diagram version-neutral by naming
    its durable middle layer `Baton protocol authority`.
11. [done 2026-08-18] Remove config, database, and `wait` mechanics from the
    product diagram; retain local dossiers and the Codex/ACP adapter boundary.
12. [done 2026-08-19] Return the two parked items now that both are certified:
    W159's blocking default for directed requests, and the EFFECTIVE-BATON
    link (W104 landed, and its self-retiring check stopped constraining).
13. [done 2026-08-19] Teach the FOURTH wake class. `wait` returns pokes and
    the shipped agent contract taught three kinds; the policy and the README
    now carry the poke primitive, and a standing check derives the kinds from
    `participant_actions` so a fifth one fails on the day it ships.
14. [done 2026-08-21] Add concise product positioning to `README.md` for
    coordination under parallel and interrupted execution, and for the
    durable ledger as the source from which a team reconstructs truth without
    relying on chat history or memory. Keep the copy product-focused and do
    not describe early-product rough edges.

**Status — 2026-08-19:** the record's inventory is complete on the current
tree. `teams` and `inbox` (W25) are deliberately absent from the certified
documents while that Work is in review.
