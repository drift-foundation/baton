# Plan

1. [done 2026-08-26 reviewer] Reproduced the split between the correct
   start-scoped `claude-acp.json`, its launcher-free `agent.env` and prompt,
   and the stale persistent participant `load.json`.  Recorded live and source
   evidence in `FINDING.md` and `evidence/baseline-2026-08-26.md`.
2. [done 2026-08-26 reviewer] Defined the top-level validated `baton` section
   as the one launcher source.  Every ACP readiness prompt receives the shared
   JSON-quoted four-field block; the spawned environment derives the same four
   values, and conflicting explicit values fail before model/session use.
3. [done 2026-08-26] Reuse the shared pure launcher renderer, compose
   it into every ACP action prompt, derive/check the four environment entries,
   and update the ACP templates/examples/README.  Preserve current W11910 and
   W12229 work in the overlapping files; change no protocol or session rules.
4. [done 2026-08-26] Add the exact-presence, all-action-kind,
   new/load, environment parity/conflict, participant isolation, no-inference,
   refusal, and retry/recovery regressions recorded in `FINDING.md`.  Run the
   focused ACP/shared-renderer suites, template/example validation,
   `just test-v11`, and `git diff --check`.
5. [pending review] Independently review the implementation and full gate,
   with special attention to pre-wake conflict refusal and absence of a second
   independently maintained contract.
6. [pending operator] Drain, release, and restart with a fresh start-scoped ACP
   session while leaving the stale persistent file in place.  Certify that the
   first prompt carries the successor pair and the first standalone canonical
   claim succeeds through it.  A repin or reused session is not acceptance.

**Status 2026-08-26:** reviewer research is complete and the correction is
implementation-ready.  The current 69-test ACP suite is green but has no
prompt/environment launcher-presence assertion, which is the measured gap.


## Implementation - 2026-08-26

3. [done] One source, two carriers. `runBridge` renders the shared
   `launcherContract` once from the accepted configuration, before the first
   wait/spawn/session/prompt, and every delivered action's prompt carries it.
   `validateConfig` derives the same four values into `agent.env` last, so
   they also override an ambient parent value, and refuses BY KEY when an
   operator spells a conflicting one. Templates and README updated.
4. [done] Seven regressions, including the REAL spawned subprocess observing
   the four values with a template that omits them. All seven measured to fail
   against the pre-change carriers. Two existing assertions had their anchors
   moved from end-of-text to end-of-line; their wording is unchanged.
   `tools/acp-baton-bridge` 69 -> 77/77, and the full v11 gate passes 3067
   parallel, 52 serial and 77 ACP.

**Note for item 5.** `tools/codex-event-bridge` is 413/414 in the same tree.
That failure belongs to W11910's seventh review, not to this Work, and no file
of it is touched here. Evidence:
`evidence/gate-2026-08-26-implementation.txt`.

## Independent review correction — 2026-08-26

5. [changes requested] Runtime behavior and the full gate are independently
   green. Review journal:
   `review-2026-08-26T08-11-35Z.md`.
7. [next P2] Update the stale “CODEX-ONLY” paragraph beside
   `launcherContract` to record the supersession: the renderer is shared,
   `readRoleInstructions` still returns role prose alone, Codex composes the
   block into developer instructions, and ACP composes it into readiness
   prompts plus its derived child environment.
8. [next] Rerun the shared role-instruction test and `git diff --check`, then
   return for independent sign-off. Item 6's rollover and first-claim smoke
   remain operator-owned and blocked on sign-off.

## Independent correction re-review — 2026-08-26

9. [done] The shared renderer source paragraph is corrected and its new
   source-comment gate passes.
10. [changes requested P2] Update the Codex bridge README launcher section to
   name ACP's two current carriers: the authoritative block in every readiness
   prompt and the same four values derived into the child environment. Remove
   the Codex-only/environment-only statements while preserving the W12229 to
   W14828 chronology.
11. [next] Update the stale comment and failure wording in the existing
   `the ACP adapter's shared read still returns accepted prose alone` case.
   Keep its assertion: the shared reader returns role prose alone because each
   adapter composes the launcher block outside that read.
12. [next] Keep the additive README regression, rerun the role-instruction and
    ACP suites plus `git diff --check`, then return for sign-off. Item 6's live
    rollover and first-claim smoke remain operator-owned.


## Independent final re-review — 2026-08-26

10/11. [verified] All user-facing and source-level launcher documentation now
names ACP's prompt and derived-environment carriers and preserves the W12229 to
W14828 supersession. The role-prose-only assertion remains intact with correct
reasoning.

12. [done] Codex bridge 420/420, ACP bridge 77/77, templates parse, and
`git diff --check` is clean. The reviewer added a passing all-surfaces
two-carrier assertion to make the documentation gate match its claim.

5. [done, signed off] Independent repository review is complete with no open
implementation finding.

6. [done, operator acceptance 2026-08-28] The successor `dd1dc3e` stack
   started a fresh start-scoped Claude ACP session while the stale persistent
   `load.json` still named `14aecfb`.  The rendered prompt/environment contract
   named the exact `dd1dc3e` binary, live config, participant, and role, and the
   session's first recorded standalone claim succeeded through that pair.
