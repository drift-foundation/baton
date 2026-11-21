# W385427 — monitor running duration and deadline countdown

## Owner decision — 2026-11-21

Owner observed that native Job w385424-status-cause-1 shows `elapsed 14m00s` for both running implementation and blocked review, although review has never executed. Owner requested running duration and time before expiry, accepted the semantics below, and explicitly assigned codexpc. Coordination: W385427/T385427; implementation endpoint baton.codx. This is separate from W385424's worker-declared failure reporting and W385331's messaging/discovery outcome.

Selected semantics:

- Job age is time since Job creation, clearly labelled.
- Running duration measures the actual invocation from an attributable recorded start, not Job creation, offer, claim or episode opening. A never-started blocked stage says `not started`; absent or ambiguous evidence says `unknown`.
- Remaining time names the earliest applicable provider-turn, stage or Job deadline. Distinct origins and limits must not be conflated. Do not invent a provider deadline by adding its limit to Job creation or claim time. If relevant timing is unavailable, qualify the answer rather than falsely declaring a known earliest limit.
- Activity age remains separate from runtime and deadline information.
- Use `timeout in` or an equally precise limit label, not a promise of eviction. Reached deadlines, enforcement requests and confirmed cessation are distinct facts. Never display a negative countdown as time remaining or imply deadline passage proves termination.
- One shared structured interpretation serves status, monitor and future TUI. Preserve snapshot observation time/freshness and honest stale/unknown qualifications. Timer arithmetic must not manufacture canonical state between snapshots.

Example (illustrative, not a demanded layout): implementation RUNNING, running 12m30s, provider timeout in 47m30s, activity observed 1m27s ago; review BLOCKED, not started. The implementer may choose a compact readable layout without a new design gate for routine formatting.

## Boundaries and parallel ownership

Codexpc owns an isolated candidate and this dossier's implementation progress. Native workers executing W385424 may also change tools/job_observation.py, tools/job_viewer.py, projection and associated tests. Do not edit the human checkout's product files, the native working line or any live instance/store/configuration; do not import either candidate during concurrent implementation. Deliver exact base/path/digest provenance so the coordinator can serialize overlapping integration and obtain review of the joined result.

Research current source/timing records before implementation. Initial relevant paths: v12/python/tools/job_observation.py (_elapsed, _stage_line), job_viewer.py and the existing status/observation producer; these are pointers, not a files-to-edit restriction. If an authoritative start/deadline is not exposed, use the existing owning record boundary for a minimal additive projection, or report a concrete missing fact; never infer it from activity/log size. No external I/O inside store transactions. Reuse DESIGN OBS-1/OBS-3, REC-1 and existing finite Job control semantics; this does not change timeout policy.

Focused deterministic tests by default. No live providers, engine operations, full suite, hazardous checkpoint_profiles, Git mutations, unrelated repairs, new monitoring framework or changes to the running Job. Independent review and human integration/Git remain required.

## Implementation revalidation — E385429

Confirmed: stage_view uses episode.opened_at as elapsed, even for blocked stages. Existing control report provides Job submission origin and independent stage/Job deadlines with trusted/uncertain timing. Exchange states report dispatched/answered/faulted without invocation timestamps; dispatched is written before provider invocation. Provider timeout is configured but no attributable actual provider start/deadline is in the shared snapshot. Runtime therefore stays unknown when an invocation could have started; no age/claim/dispatch substitution. Known never-started stages can say not started. Implement presentation from existing facts, explicitly qualifying missing provider timing. No new worker telemetry/collector or execution policy is selected; missing actual-start fact is a disclosed source limitation, not invented runtime.

## E385435 continuation — attributable provider-process timing

Owner explicitly requires finishing attributable start/end/provider deadline, not stopping at unknown. Selected implementation: observe successful provider Popen and direct-child completion at the adapter-owned boundary; publish an optional bounded invocation document through the existing command-correlated worker exchange, without a new collector or log parser. Report provider-process scope, attributable attempt/operation, actual start/deadline/end; never infer start from dispatch/activity. Missing process creation or custom test runner without proof stays unknown. Direct-child end is not proof descendants stopped. Shared interpretation compares its provider deadline with unchanged admitted Job/stage deadlines. Existing activity cadence may carry this independent diagnostic; timing must not branch canonical execution state. Awaiting overlap coordination before further host Python candidate edits.

## Owner ruling — confined fixture Git exception (2026-11-21, M385437)

Slawomir explicitly approved: allow the two compatibility tests to mutate Git only in newly created, confined disposable fixture repositories. This narrowly supersedes the no-Git-mutation restriction above for TheRealObservationReaderReachesTheView.test_a_foreign_job_still_refuses_against_the_real_reader and .test_the_view_renders_the_real_model_free_completion. It grants no mutation of the owner checkout, existing repositories, retained candidates, native execution lines or installed instances. Human Git ownership otherwise remains unchanged.

Implement and prove confinement before executing, retain operation/target logs and actual worker errors before cleanup, and preserve the real assertions and deterministic provider/engine boundaries. The prepared VERIFICATION-GUARD-PLAN.md under evidence/continuation-385435 describes the proposed enforcement; approval is not evidence that the guard already works. Stop on a confinement refusal rather than widening the exception. Required evidence remains in the dossier, not solely disposable scratch.

## E385443 implementation result and supersession

The E385429 revalidation statement that no worker timing producer is selected is superseded by the explicit E385435 continuation selection and its completed implementation. The initial absence of attributable facts remains true of the prior base, not the new candidate. Correlated optional invocation timing is diagnostic only; direct-child start/end and configured provider deadline feed the existing shared snapshot. Job/stage deadlines retain admitted origins. No lifecycle or termination authority is inferred from timing.

M385440 permits independently isolated shared-path deltas; M385442 confirms the narrow owner-approved fixture Git exception. Final confined tests both pass; original missing-schema worker error and subsequent guard omissions are retained in evidence/continuation-385443/DIAGNOSIS.md. Full candidate, test paths/reasons and final347+2 passing evidence are in evidence/continuation-385443/HANDOFF.md. Await independent review and serialized joined review with W385424; no live import or acceptance claimed.
