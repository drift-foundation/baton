# W385263 research evidence

2026-11-19, baton.codxpc, E385264. Read-only source inspection; not executed acceptance or a patch candidate. SOURCE-MANIFEST.json records exact source hashes and HEAD; DESIGN-PROPOSAL.md supplies symbols/line references. No product changes, tests, builds, provider/engine experiments, live-instance changes or Git mutations. Tests: 0 executed; failures/skips and test duration: not applicable. No new performance measurement.

## Records and interpretation

- Current FINDING.md/PLAN.md and M385263 in T385263: design only, explicit owner gate.
- v12/DESIGN.md: DB-4, LIM-2, OBS-0a, OBS-1, OBS-2, OBS-3/3a require fact ownership, distinct clocks, supported instance selection, read-only monitor, activity versus progress and typed attributed diagnostics. No normative edits.
- work/records/2026/09/finding-v12-minimal-readonly-job-viewer/PLAN.md and v12/python/JOB-VIEWER.md: accepted file reader and historical benchmark; production/telemetry costs are excluded.
- work/records/2026/10/finding-v12-minimum-worker-visibility/FINDING.md and PLAN.md: accepted provenance projection, no freshness policy or new telemetry inferred.
- work/records/2026/10/finding-v12-useful-template-job-monitor/FINDING.md: installed monitor uses stack.monitor; worker_visibility is a separate projection. Source acceptance is not installed-capability evidence.
- work/records/2026/11/finding-v12-status-job-outcomes/FINDING.md and current stack source: preserve outcomes/failures first, qualified service health and runtime details.
- work/records/2026/09/finding-live-worker-log-observability/FINDING.md and work/records/2026/09/finding-v12-durable-development-logs/FINDING.md: newer ruling permits private raw development capture, not general monitor export. Older capture prohibition is superseded.

## Confidence and limitations

Confirmed: inspected functions/contracts/constants in proposal inventory. No normalized provider/tool event or usage sampler found at inspected adapter boundaries; this is not a claim that external engines/providers cannot supply them. Existing byte activity scans native-file metadata, not workspace changes. Relevant runtime/exchange association is explicitly unverifiable in worker_visibility.

Inferred: default monitor freshness can disagree with healthy publisher cadence, from 2-second versus 5-second constants; no experiment run. Cost scaling is analytical.

Proposed: schema/API, freshness/zero semantics, instance key, sampled services, limits, estimates and phases. None is owner-approved. Baseline is source identified by manifest, not live installation attestation. Unrelated pilot dossier changes were untouched. No broader test/engine discovery undertaken.
