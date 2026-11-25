# Bounded N4b candidate for independent review

baton.codxpc, claim E386105, route E386104, ownership M386106. Base **f875ed01b51b6b7541ad169b560004e47731ad34**. Candidate **sha256:5539eef92754e69d38e93c79abd6e020f9ed5368cc0b23f423beb9fc8da5fbe1**, eight paths, retained in candidate-files.tar.gz with candidate-manifest.json, delta.patch and packaging.json. Protected product files were not edited/imported. The source copy is an independent clone, not a worktree or shared Git metadata. K owns no overlapping edits; Claude worker, DESIGN and the five W386057 isolation paths are unchanged.

## Outcome and boundary

The Codex adapter now recognizes the observed complete successful fresh-turn stream, requiring exact supported event shapes, consistent unique item lifecycles, terminal usage shape, newline-complete bounded UTF-8 JSONL and integer process exit zero. Duplicate JSON keys, malformed/truncated/oversized input, unknown fields/events, repeated/reordered endings, unfinished commands, mismatched command identity/status and unevidenced failures remain unclassified. It uses the existing 64KiB capture bound plus a 1,024-event parsing limit. This intentionally supports only the observed agent_message and successful command_execution family; other Codex tools, failed commands and failure-event families are not qualified or guessed.

Terminal success does not mean candidate acceptance. Codex attribution explicitly stays `missing`, with no contributors or contributor sources, even if passed a Claude-shaped terminal or a configuration model. The production participation table remains empty for Codex. No private session discovery/ingestion or resume mechanism was added. The session turn_context projection is a negative-evidence fixture only. Requested/observed service tier remains distinct; fast is unselected. Host frozen-result validation still holds the ending as `model-attribution-missing`, with no publication, checkpoint or verdict binding. The owner-confirmed M386103 interpretation is preserved without specification relaxation.

The exact eight paths are:

- v12/worker/codex_agent.py — bounded terminal recognition and unchanged R1/argv/build/role guards.
- v12/python/src/baton_v12/provider_policy/attribution.py — explicit Codex missing-attribution branch; Claude branch unchanged.
- v12/python/tests/manager/test_codex_draft.py — observed replay at the normal provider seam, terminal refusal matrix, provenance and no-contributor tests.
- v12/python/tests/tools/test_codex_selection.py — real host assessment/ending functions with mocked external storage/log boundaries: terminal success remains held; foreign/configuration evidence cannot become Codex participation.
- v12/python/tests/manager/fixtures/codex-0.169.0/turn-success.sanitized.jsonl — derived observed successful stream.
- v12/python/tests/manager/fixtures/codex-0.169.0/turn-context.projection.json — only observed type/model, diagnostic configuration evidence, not the private session.
- v12/python/tests/manager/fixtures/codex-0.169.0/turn-provenance.json — source report/build/image, raw-output hash and sanitization/fixture hashes.
- v12/PROVIDER-SELECTION.md — Codex behavior, observed J1 evidence and remaining native gates.

## Retained evidence and privacy

Source evidence is the selected live-probe-prompt REPORT.md/RESULT.json and two specifically identified private files at /var/tmp/baton-codex-q1-live-386097: live/private-output/turn.stdout and the session file/line named by RESULT.json. No credential file, source registry, stderr, other sessions or entire home was read/copied. No raw private text was printed into tool output. sanitize.py records the positive-selection transformation: all thread/item identifiers consistently replaced; agent prose, command and command output replaced by fixed markers; event ordering, field sets, status, exit and observed numeric usage preserved. No successful output fixture was invented. Session evidence is explicitly a lossy type/model projection, not a complete session-shaped success fixture.

Negative mutations are deterministic robustness inputs, never purported live failure observations. Private home, refreshed credentials and complete sessions remain at the private location; sanitized fixtures are durable test evidence, not a private recovery backup. The original raw-output digest links local provenance but does not replace retained bytes. Repository tests consume only fixtures under v12; no new module or execution registry entry was needed.

## Focused verification and accounting

Affected logical groups: **manager-pure, tools-pure**. Selected only tests.manager.test_codex_draft, tests.tools.test_codex_selection, tests.tools.test_provider_selection and tests.manager.test_claude_agent, through supported `just test-one` on the prepared interpreter. run-focused.py retains independently collected IDs, per-ID outcomes, exact command/header, source identity before/after and complete logs. test-one itself has no registry accounting; this report uses the retained explicit ID ledger and does not claim a full group/suite run.

- focused-01: 380 collected/executed/passed, 37.297730094s, but **source drift** because I corrected the Codex credential-gate documentation during the run. Retained as superseded evidence, not accepted verification.
- focused-02: **380 collected, 380 executed, 380 passed**, 37.196738566s, zero nonpassing/skips/duplicates/unaccounted/uncollected IDs, no timeout or source drift. This verifies the final candidate. Total measured focused test time: 74.494468660s; collection/identity/preparation time is outside that figure.
- legacy-comparison.json: 12 exact baseline/candidate Claude attribution serializations byte-identical, including valid, conflicting, missing, malformed, failure and partial inputs. Existing Claude integration/worker tests also passed; worker/claude_agent.py is untouched.
- git diff --check passed. final-audit.json verifies archive/path/hash equality, unchanged inherited isolation files, and empty owned /var/tmp/baton-n4b-386105 fixture root. The independent source clone is retained for review. No protected Git cleanup or private-home cleanup.

Five W386057 files were inherited **only in the disposable verification tree**, pinned by inherited-isolation.json and excluded from this candidate. No broad affected-group rerun, engine operation, build, provider invocation, native Job or protected Git mutation occurred. An initial CLI `help verb=reroute` misuse was rejected; supported `--help reroute` clarified the operation. A subsequent reroute request refused because K's E386104 had already routed the Work; no stronger wrapper/retry was used and the standalone E386105 claim succeeded.

## Remaining qualification gates and next milestone

1. **Actual contributor evidence remains absent.** Stdout has no model field; private turn_context.model is configuration, not participation or independently attested backend identity. Under the accepted contributor requirement Codex candidate acceptance remains held. Resolving this requires authoritative actual-participation evidence from a qualified source, or an explicit owner specification decision; this candidate does neither.
2. **Native Codex admission/qualification remains disabled.** No production realization/managed-home entry was installed. Detached authentication and instruction role/digest success establish only the selected probe. Native credential/home integration, finished-image/worker qualification and end-to-end Codex implementation → Claude review acceptance remain outstanding.
3. **C2/C3 and shared-login refresh** remain open: first-initialization recovery procedure, native credential-size bound and concurrent/shared source refresh behavior. Retained-home/resume work is not included.
4. **Explicit Claude qualification**, other Codex terminal/tool/failure families and service-tier recognition/served-tier evidence remain unproved as previously recorded. W386048 and W386057 remain separate. No additional live call is requested or selected here.

Next bounded milestone: independent exact-byte review of this eight-path candidate against the preserved contributor requirement, sanitized provenance and focused ledger, then owner import/checkpoint if accepted. Suggested checkpoint message: `Parse evidenced Codex terminal completion while holding missing attribution`. No source import or human Git checkpoint has occurred.
