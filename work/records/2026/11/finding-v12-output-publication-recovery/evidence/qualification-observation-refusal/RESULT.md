# Qualification observation correction

Installed r2 manager composed, but its publisher refused publication as a worker role. StageObservation passed the ordinary stage ROLES instead of WORKER_ROLES to the existing read-only reader. Corrected that one argument; no new serving or credential capability enters observation.

New regression reproduced the refusal. First post-fix fixture lacked the configured workspace group (log retained); corrected setup now composes then closes the serving side before reading, matching real startup. Three startup/observation regression tests pass; three existing read-only observation tests pass. Earlier 454-test run covers the preceding credential correction, not this later delta. No engine/build/installation performed for this correction.

The r2 manager ran during the startup wait. Supported status reports manager/publisher absent. Exact Docker label queries for the two producer attempt IDs returned no containers. No blanket cleanup was performed. The manager log shows both Jobs reuse d2f90ce4-W1; the second admission is deferred while the first holds that Work. Therefore the reviewed setup's two-Job construction is not a valid two-independent-originals fixture. Next qualification uses separate fresh instances, one scenario per instance; do not rerun r2 or silently mutate its Work bindings.

Next: packaging via /tmp/baton-w385695-rebuild-r2.py. Keep prior instances and images. Source remains uncommitted, with the owner retaining Git control. No independent review of coordinator changes claimed.
