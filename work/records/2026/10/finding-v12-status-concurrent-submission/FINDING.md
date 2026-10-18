# W319114 — concurrent submission can break Job status

## 2026-10-18 — selected preparation, claim319417

**Confirmed scope:** owner E319412 selects M319391: prepare the smallest useful
v12-executed correction and independent-review path, retain v11 coordination,
and return the runnable packet for owner execution selection. No live run is
authorized. This is not direct v11 implementation of the correction.

**Confirmed defect:** projection.status first calls stage_states, then rereads
job_rows/stages_of and indexes held by stage ID. Separate autocommit statements
can see a newly committed submission only in the second read, raising KeyError.
Discovery and deterministic two-handle reproduction are recorded in
baton:work/records/2026/09/finding-v12-status-readonly-opener/review-2026-10-18T01-45-33Z.md.
The first reproducer used public submit and real SQLite connections, with a
wrapper selecting the interleaving; it did not edit store rows directly.

**Accepted outcome:** coherent Job-store materialization, or a bounded explicit
safe retry/refusal under concurrent submission/advancement. Preserve status
shape, readonly openers, identity checks and ordinary serve callers. DB-1/DB-4
forbid holding Job-store transactions while calling operations, control-store
readers, filesystem observers or other external I/O. No cross-store atomicity
claim, custom SQLite reader, broad scheduling refactor or integration redesign.

**Proposed implementation direction:** separate materialization of the Job-owned
rows from external observations and document composition. Read the relevant
Job rows coherently, release the read boundary, then acquire external observations
and compose from those retained rows. An alternate bounded retry/refusal is within
the selected outcome. Merely catching KeyError and dropping a stage is not a
coherent result; wrapping the whole existing status function in BEGIN is unsafe.
The implementer chooses the exact necessary paths and tests.

**Decomposition:** one tightly coupled projection correction and its regressions,
one independently reviewable proposal. Splitting projection/store changes between
concurrent writers would add shared-file ownership risk without independent
acceptance. No child/dependency edges needed. W316915 acceptance remains intact.

**Execution preparation:** nominate repository source at exact committed base
9055843b5d258f5bfbb523815d034ee0c14075d6, use the accepted fresh implementation
composer/supervisor and existing worker image, and retain a proposal for an
independent baton.rvpc review through v11. The configured second worker is not
admitted by this single-implementation runner. Human integration remains separate.
W247941 and W236087 are reusable evidence within their recorded limits, not proof
of this code-changing task's verification or current credential validity.

Reviewer owns this dossier and preparation artifacts only. Product/test changes
belong solely to the future isolated v12 implementer. It may create commits only
inside its selected private Git workspace; host agents never mutate Git state.
No existing source, deployed instance, failed run, context or credential is changed.

Read checkpoint: E319412/events319417, T319114 through319391. No prior dossier
existed; binding revision1 attaches this canonical record. Nonexistent guessed
historical file names were resolved by reading the actual dossier sources; no
required policy or bound record is unreadable.


## 2026-10-18 — owner selects one live useful implementation Job

Slawomir agrees to the proposed OPERATOR.md execution: one fresh isolated v12
implementation at base9055843b, selected existing image/profile,600-second
provider turn,30-second verification,900-second total and60-second cleanup,
no automatic retry. Owner runs commands. This supersedes preparation-only/no-live
authority above solely for this bounded Job. Real-provider question and retained
proposal/cessation requirements are those in OPERATOR.md. Independent baton.rvpc
review through v11 and separate human integration remain required. No provider
execution or successful authentication is claimed by recording this selection.


## 2026-10-18 — selected live run held, no proposal

Prompt read owner-produced outcome at /home/sl/baton-instances/status-race-w319114-319417/packet/outcome.json; SHA256 a89f9104d0c7bb6f6b97a5eeef90f95536f2fd8cb017ebf7a6ebb64e0d427d17. Submitted02:37:38.208Z, finished02:47:46.268Z, served608.056 seconds. One implementation admission; stage exceptional, disposition unable, no proposal. Outcome records exact runtime bbc48f37732800b1cc83c1a67dfce094538c02e8f91740aaaa4772c79ff44024 destroyed and absent, retained cleanup, empty uncertainty/outstanding cleanup. These are supervisor observations, not fresh independent engine verification. No retry selected or performed.

Supported read-only status during execution succeeded02:47:39Z and reported activity848406 bytes observed02:47:32Z. Retained native transcript has286 records and tool activity through02:47:32Z; provider stdout empty, stderr contains stdin wait warning, stderr drain marked partial. Timing is consistent with600-second provider limit, but exact cause is not established by outcome alone. Do not label timeout confirmed without provider/runtime evidence.

After completion, the same supported status read refuses SQLITE_CANTOPEN with absent sidecars in this read-only environment. No writable fallback, direct database inspection or permission repair attempted. Use retained outcome/evidence and owner-run supported status if required. Next bounded reviewer diagnosis: determine cause, whether useful candidate bytes survive, exact verification/handoff state and minimal next action; no repeated live run or implementation directly in v11 selected.

## 2026-10-18 — diagnosis319578 supersedes no-artifact/unknown-timeout summary

Confirmed timeout from sealed provider failure; a three-file sealed partial candidate
exists at head aa637298bac292058b659df5d147fbddd82c49a6. This explicitly supersedes
the earlier literal "no proposal" and unknown-cause statements, while preserving
the exceptional/unable result. Supervisor excludes noncompleted outputs from its
successful-proposal inventory; provider seconds_bound3600 is stale metadata beside
the explicit effective600s timeout. Exact container independently absent.83 focused
tests pass in0.189s; adapter formal verification was skipped. See review-2026-10-18T02-50-40Z.md
and evidence/diagnosis-319578 for hashes/custody/provenance and remaining review.
No retry or product edit. Proposed next milestone: independent deterministic review
of retained candidate before selecting any fresh v12 correction.


## 2026-10-18 — routine deterministic candidate-review continuation

Prompt coordinates independent review of sealed head aa637298bac292058b659df5d147fbddd82c49a6 under the owner-selected task, prior independent-review requirement and standing routine-continuation delegation. Diagnosis319578 established artifact viability, not acceptance. Its proposed owner selection is satisfied for this bounded deterministic review by existing authority; no new live-provider run, correction execution or integration is selected. This supersedes the pending-owner-review gate in the diagnostic checkpoint only. Preserve timeout/unable as the run outcome. Review exact bytes, changed test expectations, submission/advancement and caller-held transaction/external-observation boundaries.

## 2026-10-18 — independent review319604 requests one correction

Candidate aa637298b fixes the measured submission race and passes focused and
serving verification, but caller-owned read_snapshot boundaries remain active when
status/stage_states invokes external observations. R1 violates DB-1/DB-4; safe
early refusal without ending caller work is within accepted scope. Exact review:
review-2026-10-18T02-54-37Z.md. This supersedes pending-review status with changes requested; no
specification change, live retry, direct v11 implementation or integration selected.
Prepare a fresh bounded v12 correction packet from the retained checkpoint and R1
for owner execution selection. Preserve spent outcome and candidate evidence.

## 2026-10-18 — R1 preparation accepted for execution selection

Review319725 accepts prepare_r1.py packet319624 for owner selection with proposed
900s turn/1500s total/60s cleanup/30s verification, one fresh invocation, no retry.
Base aa637298b is correct for the correction delta, but remains changes-requested
until final review: packet wording "accepted work" is not integration signoff.
Final review binds full9055843b -> aa637298b -> new-head ancestry and cumulative
final bytes/paths. Owner-only source reconstruction is unexercised; its result is
digest/commit/tree/parent gated before bootstrap/provider. No live authority
created here. Exact review review-2026-10-18T03-10-20Z.md and OPERATOR-319624.md carry selection and limits.


## 2026-10-18 — owner-executed R1 run held with retained candidate

Owner ran reviewed packet319624. Outcome at /home/sl/baton-instances/status-race-r1-w319114-319624/packet/outcome.json records907.880s, exceptional/unable, exact runtime88049037c8d1c36e76f58ce67423d4db3c15e0fdbf4f38285ead135f1f932b29 destroyed/absent, empty uncertainty/outstanding cleanup. Prompt has not independently inspected engine state. Sealed proposal/result.json explicitly confirms provider timeout900s; stale seconds_bound3600 remains diagnostic error. Candidate head14a8934ec891f24e468b1b00e0adb90c95179f03 survives over aa637298b, with projection.py/store.py/test_status.py changed. Formal adapter verification is null; no candidate acceptance or successful run claim. Supervisor no-proposal wording again omits unsuccessful retained artifacts.

Next under existing independent-review/continuation authority: reviewer verifies retained artifact provenance and cumulative9055843b->aa637298b->14a8934e change, R1 transaction exclusion, regressions, and actual reason provider continued until its limit. Examine tool/test activity for unnecessary work or blocking; do not presume another larger timeout is the solution. No new live run, spent-run reuse or integration selected. Preserve both attempts.

## 2026-10-18 — cumulative code accepted independently, both run failures retained

Review321452 accepts cumulative9055843b -> aa637298b ->14a8934ec891f24e468b1b00e0adb90c95179f03
bytes; R1 caller-boundary exclusion is resolved.406 independent tests pass3.234s
from a tracked-file Python copy. Exact final files/base hashes/cumulative patch
are in evidence/review-321452/CANDIDATE.json. This supersedes changes-requested
code status, not either exceptional/unable runtime outcome or absent formal
verification. Owner integration consideration next; no live retry selected.

Second timeout diagnosis:96 focused and978 Job-manager tests passed before worker
started whole Python tree with timeout3000 at07:21:09Z; that call remains unanswered
when900s provider limit ends. Avoid another automatic time increase. Specific
broad-test hang unproved. Long-TMPDIR basename assertion issue observed separately;
no test_store_readonly edit. Exact review review-2026-10-18T07-32-54Z.md governs acceptance and limits.


## 2026-10-18 — integration continuation toward owner commit

Owner previously directed that once correction and independent review clear, prepare the commit checkpoint. Review321452 now accepts cumulative9055843b->aa637298b->14a8934e. Prompt routes exact reviewed three-file candidate through configured baton.merge for whole-path authority/base/digest/type/mode/overlap preflight, content-only import and bounded integration verification, then return to baton.decide for human Git ownership. No direct R1-only import, conflict repair, new product edits or live run authorized. Both timeout outcomes remain unchanged.
