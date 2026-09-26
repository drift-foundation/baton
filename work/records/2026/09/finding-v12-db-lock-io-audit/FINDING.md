# External I/O under database locks — W270520

## 2026-09-26 — owner selects Tuner code audit

Slawomir requests: "let's have tuner review the code to ensure we don't have
more of those mistakes". This selects a static code audit for further violations
of the existing rule: never hold a database lock while doing external I/O;
the database/library's own internal I/O is the exception. Application callbacks
do not become exempt because a database wrapper invokes them. Reads, stat/path
validation, hashing files, filesystem writes, logging to external streams/files,
subprocesses, engine/provider/network operations and calls into another authority
or store must be traced rather than presumed safe.

Context: W257624's grant_writer correction was independently accepted in
`baton:work/records/2026/09/finding-v12-failed-run-resource-hold/review-2026-09-26T01-32-28Z.md`.
Claude is now implementing the separately selected restore_abandoned_correction
correction under that Work. This audit neither changes that assignment nor
accepts its evolving candidate. Historical lock-across-I/O comments and prior
acceptance cannot override the owner rule recorded in that dossier's September
25 ruling and September 26 reaffirmation.

Selected scope: v12 production Python source and operational tools, beginning
with worker_manager, job_manager, integration and authority transaction owners,
then every caller/callback and manual transaction boundary in that surface.
Follow reachable repository helpers outside that surface when needed to decide
whether I/O occurs under a lock. Tests are read-only supporting context. Report
the precise audited boundary; do not claim repository-wide absence from a v12
audit or a grep-only inventory. No v11 or unrelated subsystem expansion unless
needed by a reachable call chain; record such exclusions explicitly.

Deliver actionable, source-bound findings and coverage, not fixes. For each
confirmed violation name the lock owner, transaction interval, call chain,
external effect, source lines/digest and safety obligation a correction must
preserve. Separate confirmed violations, unresolved dynamic calls, compliant
patterns, known W257624 work and already-corrected sites. Record changing bytes
and do not treat concurrent edits as proof of acceptance. Recommend small
independently reviewable corrections and priorities; do not invent a new lease
architecture or an adoption gate.

Tuner owns only this dossier after claim. Product/tests, W257624's dossier,
review journals and other authors' progress remain read-only. No tests, probes,
engine/provider calls, deployed-store inspection, cleanup, Git mutation or
implementation in this assignment. Use supported Baton reads for coordination;
never inspect its database directly. Findings in this bound Work remain durable;
owner disposition selects subsequent implementation and additional Work.

## 2026-09-26 — tuner static audit result

Under claim270525, baton.tuner completed AUDIT.md: eleven confirmed finding
groups across worker filesystem operations, context admission/disposal,
worker-to-Authority reads, and Job-to-worker/coordinator reads under transaction
locks. Counts include known W257624 neighbors; they do not assert eleven new
independent defects. The report binds source lines to SHA256 manifests and
retained excerpts, separates concrete compliant patterns from unresolved dynamic
callbacks/import ordering, and recommends bounded corrections for owner selection.

Highest-priority recommendation is workspace removal plus its enclosing intake
transaction (F2); line creation and context reuse are also confirmed. Current
restoration changes remain Claude-owned W257624 work and receive no independent
acceptance here. No product/test changes, runtime tests/probes, provider/engine
calls, deployed access, cleanup, Git mutation or adoption gate. Per M270535 and
OWNER-DISPOSITION-20260926.md, findings return to Slawomir for selection of a
dedicated Job; recommendations authorize no automatic execution or fix routing.
