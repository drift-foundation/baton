# W385263 — shared monitoring proposal

Author: baton.codxpc (impl), 2026-11-19. Research complete; **PROPOSED, NOT APPROVED FOR IMPLEMENTATION**. Claim E385264. Source baseline and exact inspected bytes: `SOURCE-MANIFEST.json`. No tests or experiments run for this Work.

## Recommendation and alternatives

Extend the existing instance snapshot publisher into the one monitoring backend. Publish one versioned all-Job observation envelope; put validation, attribution, outcome interpretation and freshness in one pure read-model library. `just status` renders it once, the existing monitor refreshes it, and a future TUI filters/navigates the same model. Readers never collect telemetry, query stores, inspect containers or scan workspaces. There is no second coordination authority.

Alternative A, extending each UI's current interpretation, is smaller initially but preserves conflicting freshness and duplicates future collectors. Reject. Alternative B, a new daemon/database/event-stream service, offers independent history and push delivery but adds lifecycle, retention, reconnection and consistency costs without a current requirement. Defer. Recommended C reuses the current publisher, atomic file transport and read-only Job projection; a later transport may carry the same envelope without changing its semantics.

This fits DESIGN's read-only observation and activity-versus-progress requirements. Rich TUI behavior remains separate work. The proposal does not change DESIGN or any accepted contract until owner approval is pinned in FINDING and applicable normative text.

## Confirmed inventory and gaps

| Existing component | Reuse | Gap / qualification |
| --- | --- | --- |
| `tools/stack.py:1245` publish_once / publish | One instance publisher, atomic replace, default 5-second sleep between collections | Manager subprocess has no explicit timeout here; cadence includes collection time. Failure leaves previous snapshot. Bound collection and report source failures. |
| `job_manager/projection.py:930` status; `tools/job_manager.py:922` _status | All submissions, one materialized Job read view released before observation; read-only Control observation | Not a transaction spanning all sources; canonical recorded state can lag serving reconciliation. Fresh query is not current process proof. |
| `tools/worker_visibility.py:902` visibility | Versioned worker-visibility/1; per-field known/unknown, source paths, timestamp distinctions, attempt/episode checks | Runtime and exchange associations can be unverifiable; last contact and context usage explicitly unknown; freshness intentionally unspecified. It is not the installed monitor. |
| `tools/job_viewer.py:168,788` reader/Viewer | Bounded 4 MiB parse, schema validation, last-good disconnected behavior, pure list/detail rendering | Freshness tied to client poll interval (default 2 seconds); distinct from publisher cadence. Activity rendering rejects zero. |
| `tools/stack.py:1031,1151,1204` snapshot/outcomes/status | Outcomes and failures first, gates and fault codes, service health, runtime cautions | Stale when age exceeds 15 seconds; reader currently unbounded; outcomes interpreted separately from viewer. Service probes happen in status consumer. |
| `worker/claude_agent.py:4399,4433,4501`; `worker/baton_worker.py:2097,2160` | Existing optional byte-activity producer, atomic identity-bound mailbox, bounded latest-value thread | Native provider-file byte growth, not workspace edits or useful progress. Reused/injected HOME lacks proved baseline. No normalized provider/tool event feed found in inspected adapter. |
| `worker_manager/attempts.py:419,449`; `exchange.py:1104,1143` | Read-only persisted activity plus validated command/session binding at ingestion | Manager observation time is not provider occurrence time. Equal count does not refresh activity; source producer publishes positive values only although observation API accepts zero. |
| `worker_manager/oci.py:4192` EnginePort.observe | Existing exact runtime identity and uncertainty concepts | Inspect is not CPU/memory usage telemetry. Launch memory/CPU limits are not measurements; no usage sampler found in this boundary. |

Code paths above are relative to `v12/python/` except `worker/`, which is relative to `v12/`. See RESEARCH-EVIDENCE for records and interpretation limits.

**Inferred from code, not a measured reproduction:** a healthy publisher sleeping five seconds can be shown stale by the monitor's default two-second threshold between publications, while status still shows fresh. Freshness needs one explicit policy independent of refresh frequency. Known zero versus unknown also needs one interpretation.

Current exchange operation/state can provide a **reported worker operation**. It does not establish a currently executing provider tool or its start time. Episode-open time may support episode elapsed time, not operation elapsed time. Runtime counts remain recorded runtime counts, not confirmed live containers. Preserve cancellation, diagnostic degradation, stale/noncanonical warnings and runtime uncertainty in every presentation.

Private raw development logs are already authorized and captured; their availability is not authority to republish their contents through monitoring. The newer durable-log ruling supersedes the older blanket capture prohibition. Do not parse/tail raw logs independently in readers or export prompts, tool arguments, filenames or output.

## Shared model and API (proposed names)

New envelope schema: `baton.v12.instance-observation/1`. Preserve job-status/9, worker-visibility/1 and existing stack JSON through explicit compatibility adapters. Do not add a freshness policy silently to worker-visibility/1. During migration publish legacy and new files from the same acquired observation; clients consume exactly one, never join two files by timestamp.

Envelope fields:

- `instance`: authority UUID plus an opaque configured instance key; authority alone may span more than one selected runtime. Current publisher has the configured authority UUID but no instance-id field in its published contract. Define the instance key as SHA-256 of the normalized selected instance configuration locator plus authority UUID, local to that installation; copied/relocated installations get a different key. No filesystem path is exposed. Publisher restart is not an instance change. If continuity across relocation is needed, select an explicit persisted installation UUID instead before implementing.
- `snapshot`: publisher incarnation generated at start, increasing sequence within incarnation, source schema, collection start/end, source query time, publication time, canonical flag, scope `all_jobs`, completeness and explicit refusal/degradation reasons. Sequence is not an authority revision. Cross-source observations are not advertised as one transaction.
- `services`: identity-qualified sampled supervisor/manager/publisher health, with sample time and source status. Keep manager acknowledgement separate from process existence.
- `jobs[]`: submission/Job identifiers, derived outcome, failures, waiting reasons, cancellation/control facts; `stages[]` contains stage state, current episode/attempt references, worker/allocation identities, token ownership/expiry, recorded runtime and exchange summaries, result/artifact references, diagnostics, outstanding cleanup and available historical episode facts. Preserve the OBS-1 field set even where a source is explicitly unknown.
- `sources`: collector support, last success/error and sampling policy. `limits`: byte/target limits, deferred samples and completeness. A partial metrics cycle never hides Jobs.

Every changing fact uses a common representation, for example (illustrative values, not an observed runtime):

```json
{"availability":"known","value":4096,"unit":"bytes",
 "source":{"component":"attempt_activity","field":"bytes_observed"},
 "observed_at":"2026-11-19T18:00:00Z","occurred_at":null,
 "association":"verified","reason":null}
```

Availability is a closed enum: known, unknown, unavailable, not_supported, not_applicable. Unknown values are null, not zero or empty strings. Known zero stays known. A fact can be known historically but stale now. Missing timestamp remains null with reason; read/query/publication time never substitutes for last worker contact. Raw error strings are bounded and sanitized; public reason codes are stable.

Attribution uses `(instance, Job, stage, episode, attempt)` and exact runtime/command/session identities where present. Preserve source identifiers rather than guessing equivalence. An old attempt remains historical and cannot update a new attempt's current activity. Runtime/exchange facts without proof of association stay `unverifiable`; do not retroactively label them verified because they occur on the same stage row. Optional new collectors must return exact binding identities before their sample becomes current. Do not invent absent historical telemetry.

Proposed pure API:

```text
project(status_document, service_samples, optional_samples, publication_metadata) -> envelope
read_snapshot(path, max_bytes) -> validated envelope or structured refusal
view(envelope, now, policy, selector=None) -> qualified read model
select(view, job=None, stage=None, attempt=None) -> focused view
```

The publisher owns `project`; all clients use the same `read_snapshot/view/select`. The model owns outcomes, failure/gate precedence, activity labels, freshness, association and completeness. Renderers own layout only. `now` is injected: UI refresh ages facts without collecting anything or rewriting source times. No API above offers scheduling, cancellation, lease renewal or mutation. Existing lifecycle start/stop safety checks retain their direct process probes.

## Freshness, failure and resource bounds

Proposed common default: five-second publication cadence and stale at **age >= 15 seconds**, independent of UI poll interval. Compute age against source query time as well as publication time so a copied old observation cannot become fresh. Collection completion alone cannot refresh old source facts. Each sampled source has its own age and support state; fresh envelope does not refresh frozen activity. Future times/clock rollback produce clock-anomaly unknown, not negative elapsed or a fresh claim. A reader tracks monotonic elapsed after receipt so a stopped publisher continues to age. Source and publication wall clocks remain explicit for first read/restart.

Keep quietness separate: show “last byte growth 40 s ago,” not “stuck.” Useful progress means accepted outcomes/artifacts at their own recorded times; metrics never imply acceptance. Terminal activity is a historical absolute time, not an ever-growing alarm. Noncanonical/partial data cannot prove no Jobs/runtimes exist.

Move status's monitoring health probes into the publisher so the three UIs share their meaning. This changes service-health latency to sampled, qualified health; approve that tradeoff explicitly. If the publisher dies, cached service health becomes stale; a reader must not call a stale `running` value current. Absent/malformed snapshot yields unavailable plus last-good with original times, not an empty healthy system. Bootstrap status must explain publication absence. Start/stop still perform immediate ownership checks for operational safety.

Retain the 4 MiB read bound initially, apply it consistently, and cap publisher acquisition/output as well. If exceeded, publish a small explicit oversized/unavailable envelope and retain last-good as historical; never truncate Jobs while claiming all-Job completeness. This is a real scale limitation. Before raising the limit, measure realistic historical growth; pagination, if selected later, must bind all pages to one snapshot generation. No arbitrary per-submission constant is proof of a total instance bound.

Bound manager collection time/output and terminate/reap timed-out children; select timeout from measured normal collection latency in the approved deterministic validation. Optional samplers have separate deadlines so telemetry cannot block Job publication. No queued overlapping cycles, unbounded events or long DB locks. Retain latest on disk and last-good in reader memory; durable time-series history is outside the minimum scope.

## Signals, optional collectors and costs

| Signal | Minimum useful increment | Later cost / conditions |
| --- | --- | --- |
| Job outcomes, gates, failures; service health | Reuse existing sources, common semantics | O(stages + snapshot bytes), one collector regardless of client count |
| Reported worker operation / episode elapsed | Exchange operation/state and verified episode-open time; exact operation start unknown where absent | Typed operation-start/end events needed for real operation elapsed |
| Last byte activity | Existing persisted count/time and provenance | Existing Claude scan bounds: depth 4, 256 entries, 64 files, approximately 1-second worker polling; not free and not file-change count |
| Last worker/provider/tool event | Unsupported/unknown where no typed source exists | Add optional producer-side closed event vocabulary, attempt/command binding, sequence and manager receipt time; coalesce latest summaries, never raw stream parsing in UI |
| Container CPU/memory | `not_supported` | One adapter-owned sampler, exact runtime IDs, support checked per engine; no UI socket/exec |
| Workspace file changes | `not_supported` | Defer. Directory mtime is not recursive changes; repeated git status or recursive scans defeat cheapness. A bounded producer-side watcher needs overflow/resync semantics and reports observed notifications, not useful progress or necessarily unique files. |

Optional metric design: tentative 5–10-second period, maximum two in-flight requests, one-second request deadline and two-second cycle budget, up to 16 targets/cycle with fair rotation. These are proposed limits to validate, not measured engine capabilities. More targets remain explicitly deferred/stale; the Job list remains complete. Batch reads only if the selected adapter safely supports exact identities. Never call lifecycle reconciliation to collect metrics. Cancel and reap collector processes at shutdown.

CPU: preserve cumulative CPU time plus sample interval; derived percent defines 100% as one core and may exceed 100. First sample/reset/runtime change has unknown delta. Memory: expose an explicitly named engine-defined byte measurement; distinguish cache-inclusive usage from working set and configured limit. Engine adapter validation is required before selecting the metric's name/formula. Unsupported engines remain explicit. No cross-runtime delta or fallback matching by display name.

Typed worker events should use a new optional versioned diagnostic document/capability, reusing bounded atomic mailbox and validation patterns. Closed operation kinds and start/end/event timestamps can be exported without tool arguments. Missing support is normal. Receipt time, worker occurrence time and publisher time remain separate. Delivery failure must not fail or delay mandatory worker work. Historical private log capture is unchanged.

Historical cost evidence: JOB-VIEWER.md records 20 deterministic Jobs, 60 seconds at one-second polling, 39,129-byte snapshot, 0.025 CPU-seconds including children (0.0409% of one core), 60 refreshes/zero failures and slowest read 0.4 ms. This measures the old file reader/render loop only, not publisher, database observations, worker scans or new samplers. No benchmark was rerun here. Reader work grows approximately clients × bytes × refresh rate; collection cost is independent of clients. Existing publisher subprocess and full projection recur each cycle and need measurement before a performance claim.

## Minimal implementation and acceptance plan — requires approval

1. Pin approved schema, freshness/zero rules and compatibility decisions in FINDING and applicable DESIGN text. One implementer owns common model/publisher/consumer migration; serialize any shared-file overlap with K before edits. Extract pure validation/identity logic from worker_visibility and viewer, common outcome/failure logic from stack. Preserve old public contracts with adapters and independent fixtures.
2. Publish the new envelope from the existing publisher using existing sources only. Add bounded acquisition, sampled services, common age handling, completeness and error reporting. Switch status and monitor to the shared library; status keeps outcomes/failures before service health and retains runtime details. Provide focused selectors for future TUI. No TUI implementation, metrics, raw log processing or new worker events in this minimum slice.
3. After independent acceptance, optionally approve a separate typed-operation/event slice and a separate CPU/memory sampler slice. File watching and durable history remain deferred. Rich TUI consumes the accepted API in separately selected work.

Planning estimates, not measured promises: minimum slice 3–5 implementer-days plus 1–2 review/correction days; typed worker events 3–5 days; adapter metrics 2–4 days plus engine-specific validation. Shared contracts, identity gaps and fixture migration dominate uncertainty. Avoid estimating a watcher until its semantics are selected.

Proposed deterministic verification (none run now): same inputs produce identical outcomes, failure reasons, freshness and unknowns in status/monitor/future-consumer fixture; zero versus absent; stale boundary including exactly 15 seconds and poll-interval independence; old query copied freshly; stopped publisher, clock rollback/future timestamps; malformed/oversized file and last-good retention; publisher incarnation restart and retired-attempt samples; noncanonical/partial data cannot prove absence; no consumer DB writes, engine calls, workspace scans or provider calls. Test service states independent of Job failures and recorded runtime versus live-runtime distinctions. Bound stalled child collection/output and prove termination/reaping. Synthetic 20-Job and larger historical snapshots measure CPU/wall/bytes for publisher and readers separately; no live model needed. Optional samplers later add deterministic timeout, reset, identity mismatch, unsupported engine and fairness tests; any actual engine run needs its own selected question/scope.

## Decisions for baton.decide / Slawomir

Approve or revise (1) existing publisher plus shared pure library, rather than a new service; (2) new envelope and legacy compatibility migration, instance-key semantics, common 15-second freshness and known-zero handling; (3) sampled service-health latency and honest unavailable state before publication; (4) minimum existing-source slice only versus separately selecting events/metrics. Cross-installation identity continuity, larger-than-4-MiB support and new collectors are explicit limitations/options, not silently delivered features. No current execution blocker prevents review of this proposal. Implementation remains prohibited until explicit owner approval is recorded.
