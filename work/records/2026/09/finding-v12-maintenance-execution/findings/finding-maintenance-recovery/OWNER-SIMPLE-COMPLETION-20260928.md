# Owner completion rule — 2026-09-28

Slawomir explicitly selected the simple completion sequence after discussion:
confirm the exact job container and associated writers stopped; check required
file access without changing permissions; durably record the actual outcome;
release execution ownership when its cessation and settlement conditions hold.

Permission failure and writer uncertainty are separate facts. An access error
alone MUST NOT retain the execution gate as though a writer remained alive, or
require normalization/repair before execution ownership can be released. Report
the permission error and preserve the workspace. This is not successful output
collection or permission to delete, reset, overwrite or reuse preserved material.
Any remaining resource-specific hold must name its concrete unresolved condition;
unknown writer cessation still blocks release. No fabricated success/receipts.

This clarifies and supersedes any reading of OWNER-NO-AUTOMATIC-NORMALIZATION-20260928.md,
FINDING/PLAN or existing tests that conflates inaccessible output with uncertain
writer liveness. Other real unresolved holds and historical evidence remain.

Implementation direction: use one shared completion check/record for the selected
endings, preserving each caller's exact authority, identity and replay rules.
Reuse current cessation machinery where suitable; no broad supervisor rewrite,
second token system or new normalization path. Finish the remaining connected
paths as one bounded correction rather than passing one caller at a time for
review while known siblings remain unfinished.

Focused acceptance must distinguish: stopped+accessible progresses; stopped+
inaccessible durably errors and preserves files but does not retain an execution
gate solely for access; unknown/surviving writers remain held; restart/replay
cannot duplicate launch or effects. Zero helper starts, no filesystem/engine I/O
under DB transactions, truthful result evidence and independent review remain.
Classify the outstanding preparation/tool failures by concrete cause and required
action rather than carrying counts as baseline. Optional dead-code cleanup is
not an owner gate. Preserve useful implementation/tests and append-only history.

Recorded by baton.prompt. Active implementation claim and graph unchanged.
