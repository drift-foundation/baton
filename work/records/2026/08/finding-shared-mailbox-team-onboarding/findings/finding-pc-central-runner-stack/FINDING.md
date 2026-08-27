# Pushcoin central runner-stack pilot

## Parent and trigger

This is the bounded implementation child of
`work/records/2026/08/finding-shared-mailbox-team-onboarding/`.

On 2026-08-25, after generation 2 made the `pc.*` identities authoritative,
Slawomir approved adding Pushcoin's v11 runners to the existing Baton
lifecycle stack. This explicitly supersedes the parent's earlier repo-local
stack choice for this pilot only.

## Confirmed boundary

- Keep the current authority, schema, Baton binary, and generation-2
  `baton.json`.
- Extend the existing shared lifecycle manifest rather than creating a second
  lifecycle home.
- Reuse the existing Codex app-server, dispatcher, and event socket.
- Mint fresh Codex contexts on each managed start for:
  - `pc.prompt`, role `prompt`, with no readiness consumer;
  - `pc.plan`, role `rview`, with exactly one readiness consumer;
  - `pc.tuner`, role `tuner`, with exactly one readiness consumer.
- Add one Claude ACP service for `pc.code`, role `impl`, with its own
  per-start state directory.
- Run every `pc` context and agent in `/home/sl/src/pushcoin`.
- Keep `pc.slaw` human-operated; launch no runner for it.
- Generate exact execution-policy entries for the new managed participants.
  Preserve the repository Git-mutation prohibition.
- Give every new service a distinct name and log locator. Runtime publication
  must identify only its exact participant.
- Do not restore Gemini.

## Deployment boundary

Prepare successor files without modifying the live inputs. The operator will
drain dispatch, stop the shared stack, install the reviewed successors, start
the stack, verify health and participant runtime state, then resume dispatch.
The central stack restart is an accepted cost of this pilot.

## Acceptance

1. Manifest preflight succeeds before any process launches.
2. The dispatcher target map is one-to-one by participant and thread.
3. `pc.plan` and `pc.tuner` each have exactly one readiness process;
   `pc.prompt` has none.
4. `pc.code` starts through the ACP bridge with participant `pc.code`, role
   `impl`, and Pushcoin as its working directory.
5. Existing `baton.*` runtimes still start healthy and retain their identities.
6. Canonical `teams`/`runtime` reads show the four agent-backed `pc`
   participants live and `pc.slaw` offline as a human identity.
7. A controlled Pushcoin smoke Work can move through planning, implementation,
   review, and approval without any participant crossing repositories or
   sharing a readiness path.

## Review correction — 2026-08-25

Independent review found that Pushcoin's live `AGENTS.md` still requires
protocol 10, retired `pushcoin.reviewer`/`pushcoin.implementer` identities, and
ephemeral `work/finding-*` dossiers. That policy cannot govern the generation-2
`pc.*` runners safely and is an explicit pre-start prerequisite, not a reason
to weaken the staged identities.

The successor set therefore includes a literal `pushcoin-AGENTS.md` migration
to protocol 11, the five accepted `pc.*` identities, standalone canonical v11
operations, permanent `work/records/YYYY/MM/...` dossiers, and the existing
strict Git-mutation prohibition. The operator must install and byte-verify
that durable repository policy while dispatch is paused and before any new
runner starts. The live Pushcoin file remains untouched during staging.

## Post-cutover corrections — 2026-08-25

The first controlled smoke exposed two deployment prerequisites that the
reviewed successor did not make reproducible:

- `pc.code` uses an isolated `CLAUDE_CONFIG_DIR`, so the operator must
  provision a non-empty, mode-600 credential file in that profile before the
  ACP service starts. Credentials remain deployment-owned and never enter the
  staged successor set.
- A fresh ACP turn received only the phrase “canonical v11 CLI” and could not
  discover the executable or config without searching deployment files. The
  ACP template must export the exact launcher-owned `BATON_BIN`,
  `BATON_CONFIG`, `BATON_PARTICIPANT`, and `BATON_ROLE` values to the agent
  environment, and Pushcoin policy must tell the runner to use and validate
  them rather than infer a deployment.

The operator recovered authentication and the controlled smoke W10856 then
closed satisfying through `pc.plan`, `pc.code`, independent `pc.plan` review,
and `pc.slaw` approval. The smoke also confirmed `/home/sl/src/pushcoin` as the
working directory and a read-only kernel mount on Pushcoin's Git metadata.
The successor recipe now treats both discoveries as pre-start gates and names
the real endpoint sequence (`pc.rsrch` -> `pc.impl` -> `pc.rsrch` -> `pc.ops`)
rather than mistaking route-role names for endpoints.

The same post-cutover observation found stale `[Teams *]` attention in the
v11 TUI while canonical Home and Teams showed no actionable pickup. That is a
separate display/cache defect, does not invalidate runner provisioning, and is
deferred to v12 UI design unless v11 is retained.

## Reconciliation smoke correction — 2026-08-25

The operator installed the two reviewed reconciliation inputs, verified their
exact bytes, restarted all eight services healthy, and proved the rendered
`pc.code` ACP launcher environment. Fresh smoke W12181 then exposed the same
locator omission on the Codex side: `pc.plan` received repeated readiness
turns but could not claim because its new context had no canonical Baton
executable, config, participant, or role.

This supersedes the narrower assumption that correcting the ACP template was
sufficient for the end-to-end smoke. The child finding
`findings/finding-codex-launcher-contract/` owns the Codex bootstrap defect;
W10198 remains open until that correction is independently reviewed and the
fresh smoke reaches `pc.ops`.
