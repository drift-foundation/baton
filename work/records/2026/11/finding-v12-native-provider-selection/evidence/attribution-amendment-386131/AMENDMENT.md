# W385830 — bounded Codex attribution amendment and implementation plan

2026-11-25 UTC, baton.codxpc; claim E386131, routing E386130. Owner explicitly approved the bounded attribution change in the current instruction. This packet prepares the normative amendment and acceptance plan only; implementation waits for review and Slawomir's DESIGN checkpoint.

## Approved ruling and explicit supersession

Codex may be accepted on a clearly labelled configured-model evidence basis, recording requested model, exact executed invocation/configuration and CLI/image identity. This does not establish actual model participation, independent backend identity or absence of rerouting. Missing required evidence or an observed model mismatch/reroute refuses. Preserve stronger participation/contributor rules for other providers, including Claude review. No provider call or native activation selected.

This narrowly supersedes the Codex contributor-presence acceptance hold in the prior M386103/N4b and final-source-investigation entries, consolidated revision2 S7/sections6–7 and N1 acceptance clauses insofar as they require observed Codex participation as the sole acceptable basis. It does NOT change the meaning of a contributor, add configuration to participation sources, waive identity binding, or relax Claude's rules. Old evidence and accepted N4b99b69626 remain historical facts; today's code still holds Codex until the reviewed amendment is checkpointed and implementation separately delivered. No retroactive acceptance is inferred.

The exception is for the bounded selected Codex path grounded in retained0.169.0 evidence. A version update requires its own adapter/build qualification. Exact deployment image identifiers remain deployment evidence, not hard-coded DESIGN constants. The retained17d inventory image and46a tool image do not become a qualified native worker image by this ruling.

## Reviewable DESIGN change and ownership

DESIGN.patch inserts one contiguous exception immediately after the existing ID-4 model-attribution/publication-recovery paragraph. DESIGN.before.md captures the shared working bytes; DESIGN.proposed.md is the exact proposed result. identity.json binds both and the patch. It does not replace or undo unrelated existing edits. Shared v12/DESIGN.md was not edited. K/owner retains application/checkpoint ownership; M386132 posts this boundary. A directed include to baton.prompt was refused because no live endpoint resolves; no alternative identity was guessed. Any overlapping application needs renewed ownership coordination.

Before owner application, compare the current DESIGN digest with identity.json. If it differs, re-review the narrow hunk against current bytes; do not overwrite the shared file with the whole snapshot. No protected Git mutation is delegated. Suggested human checkpoint message: `Specify bounded Codex configured-model acceptance`. Record the actual checkpoint before implementation. Review of this packet does not certify code, a native image, or a live Job.

## Proposed implementation contract

Use a closed, explicitly versioned attribution representation that distinguishes evidence basis from acceptance outcome. Suggested basis values: `configured-model` for the selected Codex path and `participation` for the existing contributor path. Do not redefine legacy `/1` `matched` to mean both. Final names/schema are implementation details to freeze in the candidate, with both worker and host validators changed together; unsupported versions refuse.

For configured-model acceptance, retain requested selector and exact invocation evidence: executable/argv boundaries, model flag and effective relevant nonsecret options, configuration isolation/settings, CLI build proof, immutable image and adapter identity, producer attempt/Job/role and candidate binding, and safe digest/locator for the observed provider stream. Use the actual execution record validated against the delivered contract, not a reconstructed intended command. Exact prompt-bearing argv can be retained privately with content binding; public projections retain structure, instruction digest and evidence locator without credentials/private prose. Existing role/instruction digest checks remain mandatory. No real credential/session read is needed to implement deterministic checks.

Require complete supported terminal evidence for the bounded parser; preserve unknown/truncated/malformed refusal. Validate every required identity, including CLI/image/build selection against executed evidence; reject missing or inconsistent evidence. Keep contributors empty/unknown absent actual participation; show `Configured model accepted; actual participation unknown; no reroute observed` only when the retained supported observation is complete and carries no reroute indication. This is an observation-limited statement, not backend assurance. Positive mismatch/reroute evidence overrides otherwise complete configuration and successful exit. Ambiguous or unsupported input remains held/unclassified rather than converted into proof of no reroute.

Use only exact-build declared structured indicators or the exact source-defined Codex mismatch diagnostic shape for detection. Generated prose mentioning a model/reroute cannot create acceptance evidence. The current parser already fails closed on unsupported event shapes; implementation must preserve that property while giving known mismatch/reroute a specific refusal. Source-derived negative vectors must be labelled synthetic; do not fabricate a successful live fixture.

Host settlement, review admission and provider-free publication recovery must validate the explicit basis and preserve original producer binding. A publisher must not supply its own model or silently promote a configured basis to participation. Claude review still must meet its own contributor requirement. Configuration acceptance is only the attribution gate; it does not bypass output verification, independent review, cessation, isolation, credentials or other native qualification.

## Finite implementation allocation after checkpoint

1. Revalidate accepted99b69626 and subsequent checkpoints/ownership. Freeze the paired versioned evidence contract and actual invocation capture at the existing worker runner boundary. Likely files: v12/worker/codex_agent.py and the shared claude_agent.py runner only where necessary; coordinate K/shared ownership before edits.
2. Add the provider-specific evidence branch and diagnostics in v12/python/src/baton_v12/provider_policy/attribution.py, paired host validation/settlement/recovery in worker_manager/model_attribution.py and existing caller/schema boundaries discovered by references. Preserve existing participation parser and legacy unset behavior. Do not broadly loosen every `matched` consumer.
3. Add deterministic focused coverage in existing model attribution/Codex/provider selection/recovery test modules; update v12/PROVIDER-SELECTION.md and affected operator documentation to label evidence strength. Keep registry ownership explicit if a new module is needed. Return one complete bounded candidate for independent review; native activation remains separately gated.

The allocation is a plan, not an active shared-file reservation or implementation authorization before the checkpoint. No runtime/source changes made in this packet.

## Focused acceptance checks (planned, not executed)

| ID | Input/behavior | Required result |
| --- | --- | --- |
| A1 | Selected qualified Codex build, exact executed model argv/config, matching CLI/image/attempt/candidate, supported complete successful stream, no mismatch indication | Configured-model acceptance; actual participation unknown; contributors not manufactured; label visible in diagnostics and review handoff |
| A2 | Independently remove requested model, executed invocation proof, CLI proof, immutable image proof, retained output evidence or producer binding | Held/missing; no candidate acceptance or review admission; output preserved |
| A3 | Change requested vs invoked model, CLI build/image identity, attempt/Job/role, candidate digest or configuration after capture | Invalid/conflicting refusal, no fallback to intended profile; altered private invocation digest detected |
| A4 | Known exact-build mismatch/reroute indication plus otherwise valid configuration and successful terminal exit | Explicit refusal overrides positive evidence; no retry/provider call; both no-header and equal-header cases must never be inferred from silence |
| A5 | Complete stream without reroute; truncated/malformed/unknown stream; model/reroute words only in generated/tool prose | First says only no reroute observed; incomplete stays held/unknown; prose never proves participation or rerouting absence |
| A6 | Existing Claude requested contributor present/absent/conflicting and multiple contributors | Existing stronger results and complete contributor union unchanged; configured-model branch cannot rescue Claude |
| A7 | Legacy unset selection and old `/1` records; unsupported/mixed evidence versions | Existing unset behavior unchanged; old records not relabelled or upgraded; unknown version refuses |
| A8 | Producer settlement and restart/publication recovery, same versus changed bindings | Same labelled basis revalidated/replayed without duplicate effects; publisher identity cannot replace producer; mismatch held |
| A9 | Codex implementation to Claude review with deterministic providers | Configured producer provenance reaches exact review input; Claude contributor requirement still enforced; neither review identity nor outcome rewrites producer evidence |
| A10 | Synthetic secret/private-prompt sentinels in invocation evidence | Public result/status/diagnostic contains no secret or private prompt; private locator/digest binds exact evidence; no credential read |

Affected logical groups: manager-pure, tools-pure, job_manager (recovery); declare any added integration group only if joined testing actually uses it. Use prepared-interpreter supported `just test-one` commands from v12 for existing tests.manager.test_model_attribution, tests.manager.test_codex_draft, tests.tools.test_codex_selection, tests.tools.test_provider_selection and tests.job_manager.test_provider_attribution_recovery. Follow TESTING.md for an accounted focused selection and retain logs, collected/executed ledger, source identities/header together; test-one alone is not accounted coverage. Do not run full suite or affected incident groups as a shortcut. Git-mutating fixtures must be in verified independent disposable repositories, outside protected discovery. No tests are run for this documentation-only packet.

## Remaining gates and evidence

Next milestone: independent amendment/plan review, then Slawomir's DESIGN checkpoint, then bounded implementation and independent candidate review. Remaining native gates include a qualified coherent worker image/realization, supported task event coverage beyond the observed terminal family, joined pipeline qualification, applicable credential/shared-refresh qualification and explicit Claude qualification. C1 and separate Work remain separate. No additional source research or provider probe selected.

Read through canonical E386131/M386128; ownership scope M386132. Pre-existing shared edits preserved. Verification for this packet: one-hunk patch applies exactly to captured DESIGN bytes; result digest matches proposed snapshot; no shared DESIGN edit; evidence manifest checks. These are document checks, not runtime acceptance.
