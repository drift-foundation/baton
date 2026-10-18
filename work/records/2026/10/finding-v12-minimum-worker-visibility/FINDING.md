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
