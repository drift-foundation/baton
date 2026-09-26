# W270520 — static audit for external I/O under DB locks

## Current checkpoint — audit complete, owner disposition next

baton.tuner claim270525 delivered [AUDIT.md](AUDIT.md), supported by
[PROGRESS.md](PROGRESS.md), start/end SHA256 manifests, transaction/callback
inventories and retained source excerpts. Eleven confirmed finding groups;
includes known W257624 overlap. No implementation or independent acceptance.
Recommend F2 removal/intake first, then line creation and context reuse, with
exact path ownership selected by owner. Per
[OWNER-DISPOSITION-20260926.md](OWNER-DISPOSITION-20260926.md), return audit first;
Slawomir selects the dedicated correction Job. No automatic execution Jobs,
fix routing or new adoption gate. Dynamic callbacks/cold imports and excluded
subsystems are explicitly bounded in AUDIT.

The selected steps below are complete for this static audit, with the precise
coverage and limits reported rather than a repository-wide absence claim.
Discussion checkpoint: W270520 events270525/message270535; W257624
events270605/message266328, including newest changes-requested
review-2026-09-26T01-49-21Z.md. Source digests unchanged during audit; restoration
remains unaccepted and under correction. Only this dossier's audit files are tuner-owned;
prompt owns the separate disposition note; all product, tests and W257624
records remain read-only to this assignment.

## Selected audit steps (completed)

Owner selection and scope: FINDING.md, 2026-09-26. Route to baton.tune after
record preparation; no claim held by prompt. Tuner owns only this dossier.
Product changes under W257624 remain Claude-owned; do not interrupt them.

1. Read current W257624 state/checkpoint/latest review and existing no-I/O rule.
   Record discussion/event positions and source digests used for this audit.
2. Inventory v12 transaction wrappers, explicit BEGIN/context-manager/manual
   transactions and their callers. Cover worker_manager, job_manager, integration,
   authority, and tools. Trace indirect helpers, callbacks and error/replay paths
   until external I/O or a justified pure/database-internal boundary is known.
3. Write AUDIT.md with a coverage table, confirmed violations and unresolved
   boundaries. Each finding needs exact symbols/lines, lock-to-effect call chain,
   source identity, impact and a minimal correction boundary preserving exclusion,
   fencing, retry and attribution. Include source-only schedules/counterexamples
   where useful; do not execute them. Classify W257624 overlap explicitly.
4. Recheck digests for cited concurrently edited files; qualify stale observations.
   Return to baton.decide with concise counts, highest-priority next correction,
   exact uncovered scope and report path. No implementation or deployment authority
   follows from audit completion. Do not claim no violations while dynamic call
   boundaries remain unproved.

Static reading only: no runtime verification, tests, live models/engines, deployed
access, cleanup or Git mutations. No new acceptance gate or dependency edge.
Tuner records its attributable audit progress here or in PROGRESS.md; prompt
prepared FINDING/PLAN only. Canonical creation/thread:270520.
