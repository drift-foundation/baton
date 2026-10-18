# W324214 — minimum read-only worker visibility

Implement in the private v12 workspace at base6348161e608187393e45454db63c192a93f6deb3.
Read v12/DESIGN.md OBS-1/2/3 and DB-1/4. This is a bounded view over existing
baton.v12.job-status/6, not telemetry collection. No live provider/engine calls
from the worker, no migrations, scheduler acts, probe/inquire, terminal scraping,
CPU/network collectors, credentials, transcripts, or context restoration.

Deliver a separate tools.worker_visibility module callable as
python3 -m tools.worker_visibility --snapshot STATUS.json (JSON output). It reads
an existing status file only; no DB, serving factory, command subprocess or
provider. Offer an importable projection function for tests/consumers. Keep
job-status/6 unchanged. New output uses baton.v12.worker-visibility/1, documented
in v12/python/WORKER-VISIBILITY.md with a practical existing-status consumption
example. No command registration in stack_command/bootstrap is needed.

Output one row per current stage, including unassigned stages, with exact Job,
Work, stage, kind, episode, attempt and allocation identities. Preserve configured
profile identity separately from observed runtime ID/execution state and exchange
state. Explicitly distinguish unallocated from unknown/malformed. Never attach an
old episode/attempt's activity or allocation to a new one; no history fallback.
Use explicit safe allowlists rather than forwarding entire nested objects.

For each reported worker/allocation/runtime/exchange/activity/contact/context
fact expose its source JSON field path, original observation time when present,
and explicit unknown reason when unavailable. Preserve the snapshot observed_at
as snapshot query time only; never present it as runtime contact or activity time.
Do not invent per-field observation times when the source has none. Always report
last_contact, context_used and context_limit unknown with reason unsupported by
this status contract. Activity bytes are bytes, not tokens or model progress.
Observed integer zero is a known zero; null/missing/malformed is unknown.
Never render a missing count as zero or a quiet runtime as healthy/offline.

No freshness threshold is selected: freshness is explicitly unknown with reason
no freshness policy selected. Old timestamps remain historical observations and
cannot acquire fresh/healthy status on repeated reads. Query/local read time, if
included, must be named separately and never alter source facts. Validate schema,
structure, used member types, timestamps and attempt association. Refuse unsupported
versions and malformed envelope safely; malformed optional observation either
refuses explicitly or becomes unknown with a bounded reason, never valid evidence.
Do not echo arbitrary invalid input into errors. Bound file input size using the
existing viewer conventions; do not follow/open locators within status. Expose no
credentials, raw logs, command argv, private-context paths or arbitrary payloads.

Relevant existing boundaries: tools/job_viewer.py read_snapshot validates status
schema/structure; job_manager/projection.py status/_stage_status projects allocation,
current episode/attempt, runtime.assignment and runtime.activity plus exchange.
worker_manager activity owner emits bytes_observed/observed_at. Revalidate actual
producer shape, especially runtime lacking a direct attempt field and activity
carrying one. Use actual projection-produced fixtures rather than only invented
JSON. Do not claim provider capability certification.

Create focused tests in tests/tools/test_worker_visibility.py; drive actual status
projection fixtures as tests/tools/test_job_viewer.py and tests/job_manager/test_status.py
do. Required cases: assigned/unassigned; missing runtime; runtime without activity;
zero versus unknown; timestamped activity; unsupported contact/context; stale,
missing and malformed observations; restarted episode/attempt association; schema
refusal; safe filtering; unchanged repeated-source timestamps; file/CLI input; no
DB open/model/probe/scheduler/subprocess/writes by the view. Use traps at these
boundaries, not a green test that merely asserts the implementation's own output.

Focused verification: tests.tools.test_worker_visibility,
tests.tools.test_job_viewer, tests.job_manager.test_status. Use fake/replay only,
real disposable coordination fixtures as applicable. Required tests cannot be
skipped or weakened for a pass. Stop once these and directly affected checks pass;
no whole-tree discovery or broad reassurance suite. Missing fixtures are an honest
failure, not permission to copy unrelated hidden inputs or discard coverage.

Ownership: W321528 owns claude_agent.py and its tests, and the historical
single-implementation-proof supervisor/tests. W321689 owns authority api/core,
disposition/stack/bootstrap commands and its tests. Do not change those paths.
This new view/test/doc can proceed independently. Other necessary paths are
outcome-bound, but report a concrete overlapping edit before touching it.

Return promptly with exact candidate base/head/tree, changed paths, focused test
results and limitations. No self-acceptance, integration or retry. A successful
execution is not independent acceptance. Retain partial output honestly on failure.
