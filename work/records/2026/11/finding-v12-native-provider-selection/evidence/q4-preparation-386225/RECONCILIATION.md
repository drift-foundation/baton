# Claude qualification gates against existing selections

Sources are the dossier root (`FINDING.md`, `PLAN.md`, reviews), `evidence/phase-ending-owner-ruling/RULING.md`, `evidence/native-readiness-386143/PLAN.md`, `evidence/claude-inventory-386214/REPORT.md`, and the frozen source. Line numbers are of the files as they stand today.

## Already settled — no decision needed

| Gate | Settled by |
| --- | --- |
| Claude CLI build 2.1.247 | Owner, `FINDING.md:104`; recipe pin `v12/worker/Dockerfile.claude:63`. |
| Reviewer is Claude/Fable, named explicitly | Owner intent, `FINDING.md:5`, `:14`, `:36`. Exact strings are open (D1 below). |
| Contributor rule | Owner, `FINDING.md:50`: the requested model's mapped identity must appear among reported contributors; extras are recorded; no helper allowlist. Code: `modelUsage` keys on 2.1.247. Not relaxed by the Codex configured-model rule (`FINDING.md:447`). |
| Credential mode | Delivered read-only, slot `claude`, path `.claude/.credentials.json`, as implemented in `provider_policy/__init__.py` and described in `v12/PROVIDER-SELECTION.md` (first written in K's REV7 contract, `FINDING.md:99`). The reference name is open (D2). |
| Tool permission inside the container | Provider-neutral policy: full inside container, container is the boundary (`FINDING.md:14`, `:24`). Claude realization `--dangerously-skip-permissions`. |
| Separate homes | Owner, `FINDING.md:74`, `:136`: implementation and review never share a home. |
| Uncertainty goes to Slawomir, never a verdict or retry | Owner, `RULING.md:3`; implemented at `b5abf798`; 499 focused tests and my nine composed probes. |
| Uncertainty recipient value | Follows from the ruling: `decision_recipient` = `baton.slaw`. The reviewer value is the review worker's participant by construction. |
| Operator command for failed first initialization (L1) | Implemented at `b5abf798`. |
| Codex side | Q2 accepted (M386225): image `sha256:2c982530…` built from `b5abf798`, gpt-6-astra, login `codex-pushcoin-subscription`. Reused unchanged. |
| Final image for Codex | HEAD is still `b5abf798`, so `2c982530` is the final coherent Codex image. No Codex rebuild. |
| Activity-shape enumeration (old I3) | Superseded by the owner ruling, `RULING.md:5`. Not a gate. |
| Shared-login question | Does not arise for this Job: two providers, two logins, two homes. Same-provider sharing stays unqualified and is not needed. |
| No automatic retry, no integration provider call (no integration worker is configured) | `native-readiness-386143/PLAN.md:21`, `:63`. |

## Satisfied only by the run itself — not decisions

These are requirements C1–C5 for 2.1.247. Nothing retained proves them for current bytes.

| Requirement | Where it is met |
| --- | --- |
| C1 reports 2.1.247 offline; image files equal source | Selection A (offline). |
| C2 accepts an explicit `--model` on a fresh turn | Help text in selection A; actual acceptance in selection B. |
| C3 runs the selected selector without refusal or substitution | Selection B. |
| C4 output carries `modelUsage` | Selection B. |
| C5 contributors include the mapped identity | Selection B, held to D1's mapping. |
| Role label, instruction digest, exact candidate reach the reviewer | Selection B. |

## Genuinely open — owner choices

| # | Choice | Why it cannot be derived |
| --- | --- | --- |
| D1 | Exact Claude selector and the identity it must report | `FINDING.md:14`, `:50` and the inventory say no identifier is selected and none may be inferred. The only retained exact-build pair is historical: requested `claude-fable-5[1m]`, observed `claude-fable-5` (September, 2.1.247). |
| D2 | Claude credential reference | No reference is selected for this Work. A retained name from the October pilot is `operator-file:w202663-development`. |
| D3 | Container posture for the Claude reviewer | The accepted posture (open bridge egress, tool access to the login) is worded for Codex only (`RULING.md:7`). Limits for a two-provider Job are to be selected at this review (`native-readiness-386143/PLAN.md:65`). |
| D4 | Whether to prove the uncertainty path live | A real review ends in a verdict or in uncertainty; it cannot be steered. Deterministic proof exists. A live proof costs one more Claude call on a deliberately undecidable review. |

## Known limits carried into the run (not blockers)

- O1 uncertainty is a pull-only queue and is absent from Job status; O2 no owner continuation, review worker stays reserved; O3 unrouted uncertainty reaches nobody. `PATH.md` handles O1 and O3 by configuration and an explicit queue read; O2 means an uncertain Job ends held and the instance is stopped.
- Actual Codex contributors stay unknown. Real mount attestation beyond the worker's own passed preflight is not claimed.
- Broad baseline 1237/1240 unchanged. W386048 and W386057 separate.
