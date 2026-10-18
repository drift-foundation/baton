# Stable flat dossier binding and retention — W321688

## 2026-10-18 — selected bounded prerequisite

Owner M321677; decomposed under reviewer claim321681. Parent W39435;
joined consumer W321690 and umbrella W321608. Canonical record is this directory.
Original accepted assessment/decision:
`baton:work/records/2026/10/finding-v12-development-coordination-pilot/FINDING.md`.

Deliver the minimum supported public allocation/binding/readback path for one new
v12 Work, retaining a stable canonical flat locator independent of routing and
relationships. Existing v11 dossiers never move. Reuse Authority identity and
public APIs; do not make a label or filesystem path the scheduling authority.
Exact locator spelling is an implementation detail under W39435's approved rule.
Pin record ownership, evidence references, replay/collision semantics and the
retained-instance compatibility/backup/restore procedure. No wholesale migration,
graph UI or adoption of v11 stores.

Evidence locations: authority/api.py create_work/read projections; authority/schema.py
explicit clean-initialization boundary; tools/bootstrap.py and stack_command.py
packaged setup/surfaces. All are under v12/python. Current code has identities and
history but no inspected canonical dossier binding API. Do not silently turn old
proof-store clean initialization into data loss for retained pilot stores.

Acceptance: supported command/public read resolves exact authority+Work to one
stable dossier; exact retry replays, changed retry/collision/escape/wrong authority
refuses before partial effects; relation changes cannot rename it; absent or
inaccessible evidence is honest refusal. Disposable backup/restore rehearsal
preserves identities, receipts/history and retained artifacts; missing/mismatched
recovery-set members or possible old writer prevents writable admission. Slawomir
owns real backup/restore; no real instance copy/restore is authorized. Show closed
version/schema compatibility and explicit refusal, not guessed migration.


Implementation uses isolated candidate inputs and focused deterministic verification.
No live provider/engine, production deployment/config changes, speculative broader
scope or Git mutation. Reviewer owns FINDING/PLAN/reviews; actual implementation
author owns PROGRESS and records paths/test changes. Respect W61981/W321528 active
source ownership and pins; shared edits serialize. Evidence locations are not an
exclusive edit list. Independently review exact candidate bytes before acceptance.


## 2026-10-18 — review claim321887 requests corrections

review-2026-10-18T08-25-00Z.md records two reproduced P1 defects: incomplete recovery sets pass checks, and citation/verification follows symlinks outside the declared root.62 focused tests pass but miss these outcomes. All candidate manifest hashes match inspected files; no isolated immutable proposal accepted. M321894 requests the schema6/no-migration compatibility ruling asynchronously; corrections continue. Local isolated package verification is preparation and needs no separate deployment approval. Existing acceptance and downstream gates remain unchanged.


## 2026-10-18 — review claim322055 and owner decisions

M321965/M321966 resolves schema6 with schema5 refusal/no migration and preservation of old stores with old build; prior pending-schema wording is superseded. OWNER-EXECUTION-20261018.md permits near-completion bounded corrections for this Work only, not acceptance or v12 provenance. review-2026-10-18T08-48-00Z.md confirms remaining parent-replacement escape and retained-tree omission acceptance, plus mode=ro compatibility-read side effects.81 tests pass; evidence/review-322055 contains exact hash checks and disposable reproductions. These remain bounded corrections under the exception; preserve existing work and downstream gates.


## 2026-10-18 — review claim322176: real instance contract mismatch

review-2026-10-18T09-04-00Z.md records92 passing tests and matched hashes. Descriptor containment correction addresses prior race. Recovery still expects authority_store absent from actual instance.emit, while accepting omission of required retained roots as not-configured. Disposable real-emitter and omission reproductions are in evidence/review-322176. Finish one bounded real-instance integration milestone under existing exception; no accepted delivery or human checkpoint yet.


## 2026-10-18 — review claim322245 narrows remaining binding correction

review-2026-10-18T09-12-00Z.md verifies94 passing focused tests and current candidate hashes. Real instance construction, required roots and copied identity probes improve prior findings. Remaining P1: missing selector or changed selector authority UUID still yields a clean recovery-check. Evidence/review-322245 reproduces both with real disposable stores. Finish required selector digest/identity binding under existing bounded exception; no full candidate acceptance yet.

## 2026-10-18 — review claim322366

review-2026-10-18T09-29-00Z.md confirms missing-selector and wrong-authority refusals and 100 focused tests passing in0.363s. Remaining P2: JSON null selector bypasses malformed validation and crashes with TypeError; exact real-fixture reproduction and digest checks in evidence/review-322366. Frozen bundle remains unverified because PyInstaller is absent; source entry-script evidence is not freezing evidence. Small bounded correction remains within owner near-completion exception.

## 2026-10-18 — independent acceptance claim322469

review-2026-10-18T09-42-00Z.md accepts exact correction-322441 candidate bytes:102 focused tests pass0.400s, old reproductions refuse, fresh frozen command passes all eleven recovery scenarios. Earlier missing-PyInstaller operational finding is superseded: prepared v12 interpreter contains it; isolated build succeeded without install/network. Source stamp unknown in verification copy is disclosed. No integration/commit/deployment; owner handoff and W322125 actual checkpoint remain.

## 2026-10-18 — post-power-outage continuation by baton.prompt

Owner requests reading up and resuming after server power loss. Canonical W321688 remains unclaimed at baton.decide, accepted handoff E322484; discussion read through M322030. W322125 remains the human checkpoint. Runtime roster reports restarted services and no held Baton claims. All twelve candidate digests and RECOVERY.md match independent review2026-10-18T09-42-00Z; every current target matches correction-322441/DIGESTS.json host_tree_now (recovery test absent as recorded), with regular owner-writable existing files. Resume human-plus-agent reviewed-byte integration of the four recorded differences, followed by focused deterministic verification. This is integration of independently accepted bytes, not new product implementation or managed review. Preserve other Work, pending owner disposition, dependency gates and human Git ownership.

Post-outage integration completed: the four recorded differences now match accepted bytes, with all twelve final pins verified.102 focused tests pass0.385s; git diff --check passes. Evidence in evidence/resume-20261018. No Git mutation, deployment or live execution. W321688 owner disposition and actual human checkpoint W322125 remain pending; successor gates were not bypassed.

## 2026-10-18 — human Git checkpoint observed

Slawomir reports commit complete. baton.prompt observed commit `433b09d6963ca9789700849b640e242e772b9867` (`v12: add stable dossier bindings and validated retained-instance recovery`) and verified all twelve committed product/test blobs against the independently accepted candidate digests. Commit contains the selected product paths, AGENTS.md ruling and this dossier; other Work changes remain outside it. This fulfills the physical human Git checkpoint requested by W322125. Canonical snapshot323908 still shows W322125 open at baton.decide, unclaimed; owner ledger closure remains distinct from the observed commit. W321688 owner disposition likewise remains outstanding until recorded by its authorized endpoint. No deployment or successor execution is implied.

Owner closure confirmed 2026-10-18: canonical W321688 is closed with outcome satisfying after Slawomir executed the owner close. W321689 is now queued at baton.impl, unclaimed at observation. W322125 remains open pending separate checkpoint-ledger closure; the human commit is already verified above.

Checkpoint-ledger closure confirmed 2026-10-18: W322125 is closed satisfying. Canonical observation shows W321689 active with baton.claude and W321528 ready, queued at baton.impl with no open blockers. No routing or claims changed by prompt.

## 2026-10-18 — owner retires completed execution exception

With W321688 closed satisfying and checkpoint W322125 closed satisfying, owner directs removal of W321688 as an active exception. The conditional near-completion exception in AGENTS.md and OWNER-EXECUTION-20261018.md is now expired/superseded as active authority; its historical justification and accepted execution provenance remain preserved. Remove the exception paragraph from AGENTS.md. The standing isolated-v12-Job requirement and concrete-blocker rule remain in force for future product work.
