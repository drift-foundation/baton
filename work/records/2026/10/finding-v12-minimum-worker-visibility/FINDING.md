# Minimum useful v12 worker visibility

Work W324214, child of W39649. Owner selection: poke324196 on2026-10-18.
Prepare in v11; executable implementation must use v12 after concrete packet
review. This is the minimum read-only visibility slice, not full telemetry.

## Confirmed baseline — reviewer claim324211 on parent

Current observed committed HEAD6348161e608187393e45454db63c192a93f6deb3.
Revalidate and pin the committed base in the packet; exclude mutable sibling work.
`v12/python/src/baton_v12/job_manager/projection.py:status/_stage_status`
already emits allocation, current episode/attempt, runtime identity/assignment,
exchange state and activity. `documents.py` defines job-status/6 and a closed
stage shape. `worker_manager/attempts.py:activity_of` exposes attempt_id,
bytes_observed and observed_at; missing observations are null, not zero.
`tests/job_manager/test_status.py:Locators` covers runtime/activity forwarding.
`worker_manager/interrogation.py` separately supports probe/inquire and observed
last_activity_at; invoking these is not a read-only status operation and is not
selected here. No provider capability claims from the old August baseline are
re-certified by this source inspection.

## One bounded outcome

Make the supported read-only Job status usable for the question: which worker
and attempt is assigned, what runtime/exchange state was observed, when was
activity observed, and what last-contact/context information is actually known?
Use existing supported owner reads or the existing status document. Preserve
exact Job/stage/episode/attempt and allocation identity; show configured versus
observed facts distinctly. Report context used/limit and last contact explicitly
unknown when no validated structured source supplies them. Do not equate activity
bytes with context tokens or model progress, a receipt with continued contact,
query time with last contact, or no observation with zero/healthy/offline.

Per-field source/observation time or explicit unknown reason must make the answer
auditable. Preserve existing timestamps; status-query time is its own fact.
If a freshness threshold is exposed, pin its exact rule and test it; absence of
a selected threshold means unknown freshness, not an invented healthy state.
No new provider collection is necessary for this slice. A small separate versioned
view over status is sufficient if extending the closed status document would
unnecessarily broaden changes. The implementer chooses the supported presentation
and exact files within this outcome, documenting the consumer/version contract.

No polling side effects, provider/model call, new probe/inquire, terminal scraping,
new telemetry storage/migration, auth/quota mapping, CPU/network/log collection,
private transcript disclosure, context restoration or scheduling policy. No automatic
wedge verdict, renewal, cancellation, claim or acceptance. Preserve OBS-1/2/3 and
DB-1/4; observation must not acquire a writable store or mutate application state.

## Acceptance and preparation

Concrete packet carries committed source, task, selected exact focused test vector,
immutable fixtures, runtime/image/limits, provenance and supported command. Review
the packet before launch; no live run is selected by this preparation assignment.
Deterministic checks in v12 must cover assigned/unassigned worker, no runtime,
running runtime with no activity, observed zero versus unknown count, timestamped
activity, unsupported context/last-contact, stale/missing/malformed observation,
restart/episode identity separation, and read-only/no model or scheduler effects.
Expose no credentials, raw logs, command arguments or private context locators.
Include existing status regressions affected by the selected view; no broad suite.

Reviewer assesses exact resulting candidate and limitations; owner integrates and
owns Git. A prepared manifest or v11 claim is not a launched Job. Record actual
Job/attempt IDs only on launch and retain failures honestly.

## Ownership and independence

Packet author baton.codxpc owns this record's packet artifacts and PROGRESS after
claim; reviewer owns FINDING/PLAN/reviews. Future isolated worker owns its output.
Expected product boundary is job-status presentation/projection and focused new
visibility tests (job_manager/projection.py/documents.py or a separate tools view).
This is evidence of likely placement, not an exclusive edit list.
W321528 owns claude_agent.py/test_claude_agent.py and single-implementation-proof
baseline/test_baseline/test_candidates. W321689 owns authority api/core,
disposition/stack/bootstrap commands and recorded tests. Do not edit those paths
concurrently; use a separate command/view if registration would overlap, or arrange
serial ownership before touching a shared path. Preparation writes only this dossier.
No dependency on either sibling is needed for these independent inputs; their
unaccepted bytes are not inputs. W39649 retains joined acceptance and broader parked
scope. One child is sufficient for this small outcome; further telemetry stays parked.

## 2026-10-18T16:32Z — exact packet independently accepted

Review `review-2026-10-18T16-32-01Z.md` accepts the exact packet for owner live
selection: manifest ac6a77a06b6a311a6a7b7b87523baf8dbfd5b6e7c2ec6a7d9f2813b99e118aed.
Selected solution is a separate read-only status-file consumer with explicit
unknown contact/context/freshness and unchanged job-status/6. Input/provenance
checks pass; no product candidate or execution is accepted. Execution access for
the exact destination remains an operational prerequisite; no root substitution.
This supersedes preparation-pending status only. Broader scope and sibling claims
are unchanged; parent joined acceptance remains gated on this delivery.

## 2026-10-18 — operator run held and result-pickup gap observed

Owner reports retained outcome at /home/sl/baton-instances/worker-visibility-w324214-324217/packet/outcome.json. Prompt read outcome: Job job-worker-visibility-w324214-324217, attempt attempt-af94020b411e17f33edbed32004267a80c789de8d949224e39a3a47fc5648a51, finished16:34:08.887Z, state held, implementation exceptional/unable, no proposal reported. Outcome reports runtime ec7e1bd162d9f2c156ed477007fe7753953a0727144baa188dfae7f7d516b38b destroyed and exact identity absent, with no uncertainty or outstanding cleanup. Retained provider.stdout.log reports terminal_reason api_error: "Failed to authenticate: OAuth session expired and could not be refreshed"; zero API duration/input/output tokens. This is an observed provider failure, not a code verdict. Preserve the spent run; no retry was performed. Canonical v11 Work remains queued at baton.decide with no handler, so no automatic terminal-result pickup occurred. Owner identified the coordination gap; independent diagnosis and any fresh selected execution remain separate from acceptance.

## 2026-10-18 — owner reports credentials refreshed

Owner states "all credentials refreshed" after the observed OAuth-expired failure. Record as owner-reported credential repair, not an independently established successful authentication. Preserve spent run worker-visibility-w324214-324217 and its outcome; no credential contents were inspected or recorded and no retry was launched by prompt. Any subsequent execution uses a fresh reviewed run identity/destination and explicit selection under the existing no-retry boundary.

## 2026-10-18T16:44Z — independent held-run diagnosis

Review review-2026-10-18T16-43-57Z.md under claim324367 confirms provider authentication_failed, expired OAuth, zero API duration/tokens and no verification. Fresh Docker inspect reports the exact recorded runtime absent; retained outcome records destroyed with no outstanding cleanup or uncertainty. Preserve one spent invocation; owner-reported refresh is not a successful authentication proof. Correction to the earlier no-proposal wording: custody retains provider-failed result.json, empty change.patch and no-verification marker, but no candidate head or changes. Exact copies/digests and source locators are in evidence/review-324367/. Effective900s versus result3600s reporting and omitted failed artifacts belong to existing W321528; no scope expansion here. Prepare a fresh reviewed packet under the same visibility outcome, with no launch until explicit new selection. This supersedes PLAN's unlaunched current status, not historical packet review. W39649 remains gated and W324316 owns completion handoff.

## 2026-10-18T16:47Z — fresh packet independently accepted for selection

Review review-2026-10-18T16-47-25Z.md accepts preparation-324377 manifest930f1101a08eb8f6126eb4c1c1d16df01f32e74af5d45afc9df310b292ed2793 for explicit fresh execution selection. Exact task unchanged, base6348161e,110 manager/3 supervisor committed hashes and8 generated artifact hashes independently checked; old packet intact. New run worker-visibility-w324214-324377 destination absent; no launch/attempt or auth proof. Use preparation-324377/OPERATOR.md for concrete commands and unchanged limits. This supersedes preparation-pending checkpoint only. Owner priority ruling parks W324316 bridge: manual collection continues temporarily, native coordination pilot separate. No automatic bridge or migration is selected.

## 2026-10-18T17-37-19Z — retained partial implementation and timeout diagnosis

review-2026-10-18T17-37-19Z.md records selected run324377 timeout900s with retainedd35fb29c and exact runtime independently absent.76 native tool calls show useful model execution and active debugging near cutoff; the prior no-implementation/unproved-auth status is superseded for this attempt, not future runs.222 focused tests leave4 failures/4 errors after correct fixture disk setup. Structure/timestamp defects, fixture/assertion problems and missing operator document bound the remaining correction. Preparation-only continuation preserves candidate and evidence; no retry/launch selected and W39649 gate remains.

## 2026-10-18T17:38:47Z — owner revises proposed continuation allowance

Poke324810 pinned in OWNER-CONTINUATION-324810.md: proposed3600s provider and adjusted supervisor total (reviewer proposes4200s), separate30s formal verification/60s cleanup, supported context reuse preferred, no launch. This supersedes unchanged900s/1500s instructions for next preparation only. Exact spent packets were fresh and unconfigured for managed context; native logs are not a finalized reusable generation. Preserve exact retained candidate. Preparer must report supported reuse or concrete blocker; independent packet review and execution selection remain.

## 2026-10-18T17-43-27Z — revised continuation packet accepted for selection

review-2026-10-18T17-43-27Z.md accepts preparation324832 manifestd176f186fa7d89208d976296d0bd1a1be485721fa1d0b447bbaacebd505a4345 after independent hashes/generated-limit/full-patch checks.3600 provider/4200 total/30 verification/60 cleanup, one invocation/no retry. Fresh-context proposal justified by recorded missing managed predecessor and qualification-specific composer; failed context read is not journal absence. Owner execution selection remains next; no launch or product acceptance.

## 2026-10-18T17:44:45Z — interrupted-session recovery deferred, successful reuse retained

Owner poke324905 pinned at baton:work/records/2026/10/finding-v12-development-coordination-pilot/OWNER-INTERRUPTED-SESSION-RECOVERY-324905.md. Interrupted-provider-session recovery is deferred and does not gate current3600s continuations or native coordination cutover. Successful-turn context reuse remains required for v12. Preserve all findings/evidence and candidate checkpoints; revisit if longer runs show material interruption loss. This supersedes any broader gating interpretation of earlier reuse investigation, not its facts. No launch authorized; existing claims/dependencies unchanged.

## 2026-10-18T17-48-31Z — continuation startup argv overflow

# Startup diagnosis — claim324945

- Outcome this turn: selected M324917 run worker-visibility-w324214-324832 is spent, held/exceptional after7.960952522s. Job job-worker-visibility-w324214-324832; attempt-872d660470b775a58314f84c78261b08bd253c176490cece6e4dce2d7b1ca5d3. Provider start-error/OSError, effective3600s; no candidate head/changed paths/formal verification. Exact runtime independently absent. Prior d35fb29cb3c12c7a50ce5f88f439fc304fa99118 remains the continuation input. No retry or provider probe.
- Confirmed blocker: task instructions194776 UTF-8 bytes; composed prompt195345 bytes. v12/worker/claude_agent.py:_provider puts prompt in one argv member; _ran_provider forwards it to subprocess. Host deterministic /bin/true exec succeeds with131071-byte argument and fails with errno7/E2BIG at131072 and195345 bytes (page4096). This packet cannot cross that invocation boundary. Retained result erases errno to OSError, so actual historical errno is inferred, not observed. This is an input-size failure, not evidence of credential failure or timeout exhaustion. Evidence: evidence/review-324945/{STARTUP-PROBE.json,outcome.json,result.json,CESSATION.json}.
- Required change: prepare a new fresh identity and manifest under unchanged product scope and3600/4200/30/60 limits. Preserve full102391-byte retained patch and exact candidate; reduce diagnostic duplication in the actual task while retaining complete original failure evidence in this dossier. Carry a concise actionable summary of every failure class and selected acceptance. Preserve spent324832 unchanged. Do not solve this by weakening candidate provenance, dropping acceptance, changing the worker/image directly or retrying. Suggestions: retain full patch plus compact failure summary; keep final composed prompt comfortably below the observed per-argument limit. If this cannot fit, return a concrete supported input-transport proposal before execution.
- Verification behaviors: measure final composed UTF-8 prompt including wrapper and NUL; deterministic inert exec must accept its argument shape, with oversize negative case; all existing packet hash/base/source/candidate reconstruction checks still apply. No authentication inference. Test commands are optional implementation choices; product correction remains via v12. Review corrects prior packet acceptance: review-2026-10-18T17-43-27Z.md missed this argv boundary and does not authorize reuse of the spent packet.
- Handoff condition: preparer owns only new preparation artifacts and attributable PROGRESS; reviewer owns FINDING/PLAN/reviews/evidence. Return concrete packet for independent review, then fresh owner execution selection. W39649 gate retained. No independent child needed for this bounded packet correction; generalized worker prompt transport is not selected. Interrupted-session recovery remains deferred, successful-turn reuse remains in v12 target. W321528 sibling task116987 bytes is below this particular threshold; this diagnosis alone does not revoke its packet or claim execution success.


## 2026-10-18T17-52-17Z — corrected argument-safe packet accepted

# Independent corrected packet review — claim324987

Accept preparation-324963 for fresh execution selection only. Manifest a111cef07fef5c35a43acfda1f7897706d9a3251825fc61b455c48a1f35e03c8; base372281f4a473300efb474d5a6573954c15ade367. Retained unaccepted candidate d35fb29cb3c12c7a50ce5f88f439fc304fa99118 remains exact.

Independently checked12 packet inputs, all repository pins,111 committed runtime files,3 supervisor helpers,8 generated artifacts and exact generated task text. Full retained patch is embedded in task; independent fresh reconstruction matches both prior reviewed candidate hashes. Evidence: evidence/review-324987/CHECK.json. Final destination /home/sl/baton-instances/worker-visibility-w324214-324963 absent at review.

Using committed pure _prompt composer and actual generated task, inert /bin/true accepts111073-byte prompt (111074 including NUL);131072-byte negative raises errno7/E2BIG. This removes the diagnosed argv-size blocker with19998-byte headroom; it proves no authentication or provider completion. Author ARGV-CHECK additionally uses pinned provider argument flags. Required malformed envelope/time, actual restart lifecycle, semantic safety assertions, missing documentation and focused status/viewer/visibility acceptance are preserved. Original raw failures/probes remain in prior evidence. TASK opening inherited sentence saying the full log is included below is stale: its later explicit text and OPERATOR correctly identify the compact failure summary; no acceptance depends on a nonexistent embedded raw log.

Generated limits3600 provider/4200 total/30 verification/60 cleanup, one invocation/no retry, independently checked. Fresh context plus exact candidate remains selected proposal; interrupted-session recovery deferred under324905, successful-turn reuse target retained. Commands in preparation-324963/OPERATOR.md name new identity and destination; spent324832 is never reusable. Prior failed invocation and evidence preserved.

Next: owner fresh execution selection, isolated v12 correction and focused verification, independent exact-candidate review, integration and human checkpoint. W39649 gate remains. No new Job/attempt submitted, product test, live provider/engine or product edit this review; no launch authority inferred. Preparation completeness is not product acceptance.

## 2026-10-18T19-32-03Z — independent retained-candidate acceptance

Accept exact retained candidate4c1dcab6972cfff9a7f8d1964df65253533f10fd for the bounded read-only worker-visibility outcome, subject to owner delivery and exact reviewed-byte integration. Base372281f4a473300efb474d5a6573954c15ade367. No source changes or broader telemetry selected by this review. Evidence manifest SHA25625d04fbaf39572c8cb4aa9c24a89a1389e8e72a7f1557cfb26dc5e6f258d45bb under evidence/review-325713/.

## Exact reviewed paths

All three are additions relative to the base, not edits to existing product or test files:

- v12/python/tools/worker_visibility.py — SHA2563e224adf84a7f5ba6839429f4023b69ec3c19cfff95f1b55de4cc43fabdafa7c
- v12/python/tests/tools/test_worker_visibility.py — SHA2566d427a6cffde885d18a2aacead7164f61b705c262ec5cf4d54c59c15a205fa28
- v12/python/WORKER-VISIBILITY.md — SHA256904d93f5c62680fc03b9c12d283d476e017305cb4ddbf18eeaeed826f2ff803e

CANDIDATE.json binds original custody result, bundle, patch and verification marker. The isolated v12 Job was job-worker-visibility-w324214-324963, attempt-a656133b19c94ada69a2b95cc97fac87e2d9831f2f9aac253c4c89146196abaf. Provider status0, bound3600s. Original formal verification status1 remains unchanged:226 tests7.306s,2 failures in existing job_viewer integration fixtures, each unable to advance integration from claimed to integrating. Original Job is held/exceptional/unable, served1448.150533039s; no published proposal. A retained candidate and independent acceptance are different from a completed original run. Runtime9a66794da614b73ef85c996dc602725543c96853671ee97fc86005e92a7d56d6 independently absent via docker inspect exit1/no such object. No uncertainty/outstanding cleanup reported; invocation spent.

## Independent result and scope

Materialized exact candidate Python modules/tests and required vectors from read-only Git objects into /var/tmp/baton-w257624/w324214-review325713-u5kndxdb. Ran the unchanged selected focused command in explicit credential-free environment:226 PASS5.174s,5.668202s wall. FOCUSED.json/log records argv/environment. Repeated only to diagnose concrete environment uncertainty, without explicit disk-root variable:226 PASS5.190s,5.719598s wall. No skip or assertion edit. Tests construct disposable private Git histories; canonical index/history untouched.

Reviewed implementation, operator guide and continuation test/source diff. The view is a separate file consumer, schema worker-visibility/1 over job-status/6, with no writable store, clock sampling, provider/engine/probe/claim side effects or locator following. Known facts retain exact source paths; observed zero differs from unknown. Configured profile is separate from runtime; activity and allocation association check current attempt/episode; runtime/exchange unverifiable association is explicit. Query time is not contact, last-contact/context unsupported, freshness unknown without policy. Existing accepted scope does not require new collection or packaging/deployment registration.

Prior defects are resolved: required jobs/stages refuse absent/null/malformed envelopes rather than drop rows; timestamps obey the producer instant grammar and calendar; restarted episode uses its own actual offer/claim/activity before adversarial old-episode substitutions. Test changes compare reported values/keys instead of rejecting explanatory prose containing healthy/fresh/transcript; they retain planted-secret/locator exclusion and add semantic unknown/freshness assertions. Standalone operator documentation now exists and names supported CLI/API, canonical false, observation provenance, unknowns and limits. Minor wording: MAX_TEXT is measured with Python len(str), i.e. characters, although the document table calls it bytes; fixed 4MiB serialized-input ceiling remains. This is not an acceptance blocker for bounded text/secret exclusion.

## Honest limit of failure diagnosis

The worker's exact two integration-admission stalls were NOT reproduced independently. Pinned descriptor environment without a disk-root selection produces earlier git-setup failures (2tests0.028s), consistent with the separately confirmed W325695 descendant-path issue but not the same historical failure. With explicit disk root, both affected existing tests pass under pinned HOME/TMPDIR/cache descriptors (2tests4.905s). PINNED-DISK/TICK-REPORTS capture real supported sweep results. Do not claim descriptor aliases explain the historical integration stall or claim a clean worker end-to-end run. Existing test_job_viewer and runtime modules are unchanged by this candidate; the bounded visibility contract and complete selected focused vector pass independently. Preserve this unknown as follow-up evidence under W325695's verification-environment diagnosis, not an invented visibility correction or a reason to repeat live providers.

## Disposition

Return baton.decide for owner acceptance and human integration/checkpoint of these exact three added files, preserving source-base drift checks and modes. No automatic import, Git mutation, deployment, launch or retry. Parent W39649 consumes this minimum slice and remains responsible for its broader separately parked telemetry scope; this review does not close that backlog. No further decomposition needed for the completed cohesive visibility surface. Reviewer FINDING/PLAN/evidence updated; author PROGRESS and prior packet/artifacts untouched. Prior candidates and failures retained. Historical aggregate verification time remains unknown; this review records its measured runs above without resetting earlier costs.
