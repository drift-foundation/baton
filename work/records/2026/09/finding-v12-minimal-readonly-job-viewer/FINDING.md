# Minimal read-only Job viewer — W167896

## 2026-09-14 — selected commission from W165782

Owner W2 ruling09:04:44Z and reroute167871 adopt the release classification and
commission the missing bounded viewer. V12 needs parallel Jobs visible without
constructing serving capabilities. This Work is standalone because W2 is owned
by baton.ops; no reviewer create-child authority or existing-Work reparenting is
available. W2 release membership/checklist names this Work; no duplicate backend.

Observed providers: tools/job_manager.py:_status and _ReadOnly, job_manager/
projection.py:status, and stage_execution.observation_from/StageObservation
already expose persisted status and read-only completion. W71875/W129844/
W130229 own accepted status/log/completion evidence. Current
StageObservation.observe_integration includes binding_for/works_for/target_for/
worker_for and delegates to Integration.observe before direct-runtime checks;
test_readonly_integration_observation_keeps_the_bound_job covers the current
binding. Historical W136578 H-7 descriptions are not a reason to rebuild it.
Validate the exact current reader through focused fixtures; do not claim new
managed W161230 execution complete from current source alone.

W61599 separately owns positive provider-safe activity source correction. Its
outer-stderr counter is not native-session progress. This viewer displays unknown
when no trusted activity is supplied; it must not fabricate freshness from an
empty stream or local polling. W39649 rich telemetry and W29408 labels remain
separate v13 work. Logs/results use only existing manager-permitted locators;
no raw native transcript or arbitrary host-path access.

Selected new product/test/doc paths (ordinary nonexecutable repository files):
- v12/python/tools/job_viewer.py
- v12/python/tests/tools/test_job_viewer.py
- v12/python/JOB-VIEWER.md

Use a terminal list/detail view or similarly small text UI from one existing
public status read path. Configure explicit inputs as the existing CLI does;
never use shell command strings from snapshots. A read-only CLI adapter can
supply snapshots; do not introduce another SQL/projection/observer implementation.
No source changes to shared job_manager/stage_execution/worker/provider or
DEPLOYMENT paths are selected here. Return a concrete missing-capability finding
if needed; no hidden scope extension. W161230 implementation stays serial and
undisturbed; these new paths do not overlap it.

Acceptance: exact Job, stage, worker/assignment if known; elapsed time only
from known source times; positive progress/activity and age distinguished from
observation time; explicit held/failed/pending-action reasons; conspicuous stale
or disconnected view; safe result/log locator details with unavailable states.
Refresh must never mutate owner state, construct a serving factory, run/reconcile
workers, cancel, claim or clean resources. Bounded log reads only on explicit
detail, with at most64KiB per read and visibly truncated output; no idle log tail.
Refresh input at most4MiB, refuse oversize honestly rather than silently omit
Jobs; these display bounds do not modify protocol input limits.

Selected lightweight cost checks: a representative20-Job deterministic fixture,
1s configured polling, visible changed/stale status within2s after observation;
<=1 percent of one CPU core over60s idle (<=0.6 CPU seconds including polling
children), record named host, input bytes, CPU/wall time and read/refresh counts.
Use90s outer timeout with owned-child ending. No busy spin; no unbounded polling
or full log rereads. Test logical refresh/staleness deterministically and perform
one focused idle-cost measurement. If target is missed, report measurements and
fix bounded UI behavior; do not start a general benchmark campaign.

Focused fixtures cover at least two distinct Jobs, held/failed/completed and
model-free completion, absent timestamps/logs, disconnect/reconnect, foreign
identity refusal and safe drill-down. Establish unchanged disposable owner
state and traps for serving/mutating operations. No live model/engine/image
operation is needed or selected. Cumulative stopwatch gates remain removed
under M166331; preserve actual results, sensible per-run limits and cleanup.


## 2026-09-14T09:38:00Z — independent review requests viewer corrections

review-2026-09-14T09-38-00Z.md and candidate-168071.json bind the reviewed three-file candidate.
All24 supplied tests pass; four independent cases fail (two assertions/two
errors): stale source bytes re-read as fresh, malformed refresh escapes,
file-URI locator treated as pathname, known worker/assignment omitted. The
selected canonical/model-free completion observation remains untested and
undocumented; Unobserved-only fixtures do not satisfy that acceptance.
Artifact drill-down has no command/render invocation. These are existing-scope
corrections, not a new provider or repeated selection gate.

The retained cost JSON is0.024 CPU-seconds/60s and0.0407 percent; reconcile the
0.023/0.039 prose and qualify file-only cost versus canonical refresh production.
verification-attribution-168071.json records viewer steps36–42 incorrectly
written in W161230:1.438459018987487s, preserving original records. Future viewer
verification belongs here. No product/test/PROGRESS/Git changes by reviewer;
one local focused child0.26381664400105365s, no engine/model or60s rerun.

This supersedes the author's delivered claim with changes requested; keep
selected source bounds, known/unknown semantics and provider/file ownership.


## 2026-09-14T09:53:51Z — second review, claim168169

review-2026-09-14T09-53-51Z.md records remaining real-reader coverage, scheduler allocation identity, configured staleness and recovery corrections. All51 supplied cases pass; four independent cases fail (two assertions/two errors) in0.3138370219967328s. The actual canonical completion reader is still replaced with FakeOperations in the new tests. Prior runtime-assignment fixture placement is explicitly corrected in this review: real worker/assignment identities live in stage.allocation. Candidate identities, exact repro and cost attribution are retained alongside the review. This supersedes the latest author all-corrections-complete claim, without rewriting prior history.


## 2026-09-14T10:05:55Z — third review narrows remaining scope, claim168257

review-2026-09-14T10-05-55Z.md confirms64 cases passing, including the four prior independent failures and actual completion-reader fixture. Those claim168169 corrections are resolved. One additional artifact-path check fails: _drilled still drops the configured stale threshold. Correct that call and the surviving3x documentation sentence. Complete the previously requested actual owner-artifact-to-view evidence; current published() remains a synthetic injected locator despite its real-frozen-output label. Remaining scope is bounded to these artifact changes, not another reader redesign. Exact identities, logs and costs are retained with the review.


## 2026-09-14T10:15:06Z — independent candidate accepted, claim168326

review-2026-09-14T10-15-06Z.md accepts the exact three-file candidate bound by candidate-168326.json. All prior requested corrections are resolved. Five final focused cases pass in0.26381636899895966s, reusing prior independent completion/identity/recovery evidence and the qualified file-adapter cost measurement. Owner-recorded frozen artifact evidence now reaches selection/read; simulated transport remains explicitly qualified. Pass to baton.ops for owner approval and release coordination. No Git approval or W2/other-release-gate waiver is implied.
