# W61981 bounded reassessment — 2026-10-18

Reviewer: baton.rvpc, claim E321589. Scope: owner M321579/E321581.
Source inspected: 3dcf6dc4bcee97e932d17c93ac13c5811b3af188; no product edits.

## Disposition

Do not close. W319114 establishes useful, independently accepted task-specific
verification, but does not implement the approved declared-context contract.
This is a source/evidence assessment, not a new execution proof. No tests, live
providers or broad suites were run for this reassessment.

## Finite obligation mapping

“Missing” includes partial existing mechanisms where the complete obligation is
not established; it does not discard their accepted historical evidence.

| Obligation | Disposition and exact evidence |
| --- | --- |
| Declare imports, cwd, candidate placement and required immutable inputs | **Missing.** `v12/worker/claude_agent.py:117,4802` and `v12/python/tools/dogfood_operator.py:701,768` accept exactly seven task members. `verification` remains an argv list. No declared context members exist. Worker `_verify:4028` and operator `_verified:3226` run with `cwd=candidate`. |
| Closed, matching worker/operator import environment | **Missing overall.** Worker `_closed_environment:3152` supplies a closed environment, now including isolated cache/temp roots as well as HOME/PATH; the September claim that it contains only HOME/PATH is historical. Operator `_verified:3269` explicitly inherits `os.environ`, overriding three cache/temp variables. Neither derives declared Python import roots. Existing operator comments explain legacy behavior; they do not establish owner supersession of the approved new contract. |
| Complete sealed inputs with exact provenance; no-follow, bounded materialization | **Missing as a verification-context feature.** Git-line source provenance and full repository candidates can supply particular fixtures, but no task-declared required-input inventory/layout preflight guarantees this. September evidence demonstrates one fixture plus candidate can run the exact 102-test vector; it is historical manual materialization, not current paired holder acceptance. |
| No absolute/escaping/noncanonical paths, duplicate destinations or overlap; refusal before materialization/provider | **Missing for the new context grammar.** Existing task/source-profile validation is useful but there is no verification-layout grammar to validate. Generic source validation cannot discharge tests of absent contract members. |
| Separate complete worker and independent review views, exact candidate changes/deletions, retained candidate and sealed input unchanged | **Missing.** Both verifiers execute directly in their candidate. Operator `_derived:3157` snapshots and `_unchanged_by_verification:3449` detects changes on successful verification; detection is not a disposable derived view. Independent W319114 review used a separate tracked copy, but that manual process is not implemented by both holders. |
| Closed context ready/refused plus missing-input/invalid-layout/materialization/start-failure causes | **Missing.** Worker publication at `claude_agent.py:2126,2151` carries status/argv; operator `_derived:3201` carries verification_status/argv. No closed context axis distinguishes missing fixture/import errors from assertion failures. |
| Closed command not-run/passed/failed/timed-out, actual exit status only, candidate verdict only ready plus passed/failed | **Missing.** Worker `_verify` maps timeout/start failure to null status with safe text; these are not the approved two durable axes. W319114 adapter verification was absent on timed-out runs; independent acceptance correctly did not claim it passed. Preserve that honesty. |
| Timeout/start/partial-materialization cleanup preserving candidate/input | **Missing for the new derived view.** Operator `_verified` already cleans its external ephemera in finally; worker has isolated verifier roots and bound execution. These mechanisms are useful but do not prove cleanup of an unimplemented context materializer or candidate preservation on every new failure branch. |
| No child output, credentials, host paths or arbitrary exception prose in durable result | **Satisfied in part, new contract acceptance missing.** Worker `_verify` documents discarded streams; operator captures bounded display output in temporary storage and removes it. No new context-cause payload exists to assess. Preserve these controls and verify all added durable branches with safe structural facts only. This is not a fresh global security audit. |
| Both holders agree on version/members/types; legacy contracts refuse new semantics | **Missing for verification context.** Current constants agree on task /2, but its added members are source_profile and declared_base (W71917), not the September approved context. Exact-member validation already refuses extra context keys. The /2 name is occupied by another frozen shape. |
| W52821-equivalent 102 tests, zero skips/import/fixture errors in worker and independent context | **Missing paired implementation proof.** `evidence/research-2026-09-01/README.md` records 102 passing in manually assembled review context (0.252s). It does not establish current worker and operator materialization. W319114's different focused gate does not replace this acceptance. |
| Fresh isolated correction and independent review before import | **Missing for W61981.** No W61981 implementation candidate exists. W319114's reviewed/imported candidate fixes concurrent status; its acceptance is preserved, not borrowed as this correction. |
| Manager copies a second verification source | **Explicitly superseded** by September27 ruling and DESIGN ART-2/ART-3: generic manager must not recursively copy/hash nominated source. Source driver owns governed preparation. Current TOK-7 allows governed host preparation followed by the leased container; September27 wording does not impose a mandatory maintenance container. REV-2 still requires independent review and exact candidate binding; it does not require a whole-tree copy merely to change roles. |

## W319114 evidence reconciled

`baton:work/records/2026/10/finding-v12-status-concurrent-submission/review-2026-10-18T07-32-54Z.md`
records 406 focused tests passing from a clean tracked Python copy with explicit
imports, short TMPDIR and fixture root. Provider evidence includes 96 focused and
978 Job-manager tests; formal adapter verification remained absent on both failed
600/900-second attempts. These are different evidence surfaces, not one complete
adapter gate.

`baton:work/records/2026/10/finding-v12-status-concurrent-submission/INTEGRATION-321492.md`
records initial relative-import errors, then a long-temporary-path diagnostic
assertion failure, then 406 passing in 3.230s with package-qualified imports and
short TMPDIR. No assertion was weakened. This confirms that manually selected
context can establish the selected candidate's correctness, and that context is
still operationally significant. It neither supplies a general declaration nor
supersedes W61981's acceptance. Full repository staging solves particular fixture
availability; it does not classify missing declared inputs before execution.

## Smallest correction direction and decision

**Proposed owner clarification:** retain the approved Python-specific context and
outcome semantics, but assign them a fresh task version (suggested /3) and matching
result versions, preserving current /2 source-profile/base behavior. Do not widen
/2 silently or reinterpret its historical evidence. This is the concrete contract
collision requiring owner selection before dependent implementation, not a renewed
approval request for the already approved import/layout/outcome semantics.

After selection, prepare one bounded paired worker/operator correction using the
existing source driver: declared contained layout/imports/required inputs, private
verification views from frozen inputs, and the two outcome axes. Keep the manager
protocol unchanged unless research demonstrates a necessary gap. No arbitrary
environment map, broad runner refactor, automatic inference of all test fixtures,
or live-model proof is selected. The original missing/extra/type/path/overlap,
ambient-environment, mutation/deletion, timeout/start/partial-materialization and
safe-durable-output regressions remain required; preserve the paired 102-test gate.

Decomposition assessed: the schema, materializer and both consumers have one
coupled acceptance result. Keep the initial correction together; independently
review the resulting immutable candidate before integration. An argv-only import
patch would leave the defining context-versus-verdict defect open. If execution
shows genuinely separable outcomes, install child Work/dependencies before release;
no child or dependency is created by this reassessment.

W321528 retains its independent packet and pins. Any later correction touching the
worker must be scheduled serially after its ownership is released, with fresh
source binding. This document neither changes W321528 allocation nor installs a
Baton dependency gate. Reviewer owns only this dossier/new evidence. PROGRESS is
unchanged because no implementation occurred.
