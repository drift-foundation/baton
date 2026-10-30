# Durable typed failure capture and replay

2026-10-20, reviewer baton.rvpc claim341344, decomposition of W333486 within its accepted diagnostic scope. Parent owns joined ordinary status/report, installed-bundle and full acceptance. This child owns an independently reviewable producer contract before downstream composition.

Observed: run340352 hit its900-second lease, returned no frozen candidate and never ran its verification gate. Partial tracked.diff plus four new files survive in parent evidence/run-340352/retained-partial/. They are unverified input, not a proposal or accepted patch. Parent evidence/review-341344/evidence.json verifies14 copies and6 source pairs. Preserve originals and derive a separately pinned recovery input in preparation; verify tracked diff base and new-file hashes before isolated application. Do not mutate or resume the old instance.

Bounded outcome: durable pre-effect cessation intent and separately typed outcome at reclaim, settlement and cancellation boundaries; exact attempt/assignment/start/domain/generation/token-bound runtime/operation attribution; reader distinguishes unknown, typed failure, intent-only and positively observed cessation. Replay preserves historical evidence and later observations without making an old uncertainty permanent or converting collision into authority for different effects. Both release paths and existing fencing/cleanup behavior remain required.

Concrete static concern in retained failure_cause.py:ensure_cessation_intent (lines403-442): an operation-collision is treated as proof an intent exists and permits effects, without proving that old intent describes the current facts. A different runtime/correlation signature is not durable authorization for the new effect. Reject or resolve that mismatch explicitly; exact replay and changed-signature collision need distinct acceptance evidence. This is a static finding, not an executed reproduction. Revalidate the partial implementation rather than assuming the handoff assertion that item C was not reached; this function and outcome revision chain show C was attempted.

First slice acceptance: isolated deterministic production-boundary tests establish intent ordering under recording failure and crash; exact replay vs conflicting runtime/operation; token-bound-before-attachment; stop failure vs unknown cessation; absent vs quiescent; uncertain-to-positive observation history; reclaim/settlement release attribution; secret-safe bounded fields and honest old-record unknown. Deliver versioned producer shape/read API, exact base/path/digest candidate and actual v12 Job/attempt/evidence. Keep tests focused to this slice; parent retains full joined gate and historical failure classification.

Ownership: configured baton.impl owns isolated child preparation/candidate/PROGRESS. Primary producer paths are worker_manager/failure_cause.py, documents.py, intake.py, attempts.py and focused producer tests. These identify allocation, not an exclusive edit restriction; coordinate any additional shared contract path before parallel edits. Parent status/report work is serially blocked until child acceptance, so no concurrent edit owner. The retained whole partial snapshot is preserved; select only necessary producer changes for this child and leave downstream partial changes available to parent. No product source edits in host tree.

Authority: reviewer decomposition ruling permits this finite split without new scope approval. Owner341187 selected the completed one invocation only; no next start, lease extension, host product-test fallback, deployment or Git mutation selected. Prepare exact isolated v12 operands, then independent preparation review and applicable execution selection. A routine correction is not an owner scope gate. No extra live provider solely for deterministic verification.

## 2026-10-20T19:26:13Z — producer preparation independently accepted

Review341441 accepts execution341360 preparation manifest0c4730e7e8757dd873517c7744577b949702d55d066dd44a7984064e708b0fa5; review-2026-10-20T19-26-13Z.md.43 seals,52 probes, input verification and33 composed fixture hashes pass. Three producer diff sections and two new files match preserved parent bytes (global file-section order differs, no hunk changes). Recovery remains unverified input. Supersede preparation-in-progress state only; product acceptance and new execution selection remain outstanding. Parent dependency341370 remains.

## 2026-10-20T19:50:05Z — second lease interruption; verify and return first

Review341624 verifies14 copies and6 source pairs from run341360; review-2026-10-20T19-50-05Z.md. No frozen candidate and verification not-run; source/test growth is not acceptance. Owner341467 invocation consumed. Correct campaign narrative: parent340016 did retain a failed-verification candidate; zero candidates are accepted, not zero retained. Preserve immutable evidence.

Current milestone supersedes open-ended producer authoring: fresh isolated continuation from latest preserved bytes, focused gate first, only evidence-driven fixes, then supported provider completion with planned600s editing cutoff/720s return target under unchanged900s lease. Pin actual supported completion instructions into worker task, not only outer PROGRESS. This is task planning, not a controller/lease change or new execution selection. Parent remains blocked on actual child acceptance.

## 2026-10-20T20:00:52Z — verification-first preparation accepted

Review341697 accepts execution341637 manifest1f191e7b2f0f0ac033550a3fb235ec48624171d714c0cfb02e47124dcea3e3df; review-2026-10-20T20-00-52Z.md.48 seals,55 probes, input verification and38 composed fixture hashes pass. Worker-visible COMPLETION/TASK pin verification-first and600/720 planning targets under unchanged lease. Provider return enables but does not guarantee freezing/publication; actual external evidence remains acceptance. Supersede continuation-preparation-in-progress only. No new run selected; parent remains blocked.

## 2026-10-20T21-46-50Z — selected run failed provider authentication

Review342415 (review-2026-10-20T21-46-50Z.md) verifies10 evidence hashes,6 source pairs, custody diagnostics/empty patch and unchanged48-member seal. The attempt reports supported authentication_failed; no verification or product acceptance. Owner342358 selection consumed. This supersedes the prior no-run-selected state: execution341637 has now run and its root must be preserved. Structural preflight does not establish session validity. Operational credential repair and a separately selected continuation are outstanding; fresh identity/root binding is necessary unless a supported recovery path is explicitly selected. Accepted producer/task/recovery scope is unchanged; parent341370 dependency remains.

## 2026-10-21 — owner reports provider access restored

Slawomir reports in the interactive prompt: "I logged into claude and providers-check (just) finished ok". Recorded by baton.prompt as owner-reported operational evidence; no credential contents inspected and no independent provider check repeated. This supersedes the outstanding credential-repair prerequisite above, not the historical failed attempt or its consumed selection.

Continue the existing bounded preparation milestone: retain reviewed execution341637 task/recovery bytes and limits, prepare only necessary fresh run identity/root bindings and resultant seals, and preserve the failed instance. Return for independent preparation review and applicable exact invocation selection. This report does not select a new live invocation or establish producer acceptance. Current canonical read before coordination: snapshot345035, unclaimed queued baton.decide, episode342420; latest review remains review-2026-10-20T21-46-50Z.md.

## 2026-10-21T10-13-48Z — fresh identity preparation accepted

review-2026-10-21T10-13-48Z.md accepts execution345039 manifest5db5b9bad674f4b9ae3e6141c54d9551ade6644f9c2ebe52694c773db2857e6b.51 new seal lines, complete52-file inventory,48 previous seal lines,41 composed fixture hashes and unchanged gate verified. Input check passes0.118200679s. Supersedes fresh-binding preparation-pending state only; no new execution selected and no product acceptance. Required exact invocation selection remains with owner; preserve consumed341637 and parent dependency341370.

## 2026-10-21T10-42-55Z — retained candidate, failed gate and concrete fixture-path diagnosis

review-2026-10-21T10-42-55Z.md verifies run345039 evidence and candidate1599471c21d9427e83883a6346d9e846295c3f222296c320b68933f178b0b096. Owner345206 invocation consumed; completed gate864 tests12.817s fails9/errors7, all test_maintenance. This supersedes no-execution-selected/current-preparation-only state. Static unchanged-base fixture paths retain /proc/self/fd aliases while product composition requires canonical paths; two subprocess empty-output errors plausibly share descriptor-path cause and need dynamic confirmation. No gate exclusion or claim of a passing base. Next bounded correction is same-environment fixture compatibility and full unchanged-module gate, prepared through baton.impl with retained candidate provenance before applicable exact execution selection. No producer acceptance or parent unblock.

## 2026-10-21T11-01-38Z — fixture-correction preparation independently accepted

review-2026-10-21T11-01-38Z.md accepts execution345388 manifestb895cc72c8458c7988a6c9182ab964ba5450a31dcc39c1af79eb48e3dc8b204d as preparation only.57 seals/full58 files, exact retained candidate patch,45 composed fixture hashes and unchanged full verification argv verified; targeted downstream run-evidence mismatch refusals pass. Supersedes correction-preparation-pending state only. Exact one-invocation selection remains outstanding, owner345206 consumed, producer candidate unaccepted and parent341370 blocked.


### Post-review coordination — message 345516

After review345501 and pass345519, read T341357 through345516. Prompt reports owner M345512 selected integration of W339626 candidate345109, with prompt owning its bounded 17-path main-tree import. Overlap with this work is `v12/python/src/baton_v12/worker_manager/attempts.py` and shared input `tools/authoring_enforcement.py`. Preserve W341357 retained candidate, sealed continuation inputs and pinned base unchanged; report later integration overlap explicitly rather than silently rebasing or weakening pins. This notice selects neither a W341357 main-tree import nor a new invocation. Preparation acceptance remains limited to the sealed packet; executor-boundary preflight must evaluate current inputs before any selected execution.

## 2026-10-21T11-37-58Z — second candidate fails storage gate; classification corrected

Review345793 (review-2026-10-21T11-37-58Z.md, evidence/review-345793.json) verifies14 evidence copies/13 source pairs and gate864/12.515s/16 subtest errors in4 methods. Candidate5a7d5976/content5c0fca78 remains unaccepted; producer/test patch sections unchanged. disk_roots existed at base; only canonical spelling changed. This explicitly supersedes pass345775 claims of a newly introduced helper, count-alone coverage proof and proven new-disk-root causation. Repeated setup/deferred fixture cleanup is confirmed statically, exhausted filesystem remains unmeasured. Next minimal continuation measures those4 methods and fixes demonstrated fixture lifetime/storage with preserved assertions/full gate and durable nonsecret report. No owner scope choice required for routine fixture correction; exact fresh invocation still requires selection because345560 consumed. No host test or live run.
