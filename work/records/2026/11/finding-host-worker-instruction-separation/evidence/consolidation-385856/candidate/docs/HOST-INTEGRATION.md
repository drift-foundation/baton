# Managed host integration procedure

Read this entire procedure before acting as the explicitly selected managed
integrator. Root AGENTS.md still applies; this is host policy, not worker policy.

The managed integrator performs a whole-path-set authority preflight before any
write. Require current scope and independent digest-bound review enumerating all
changed existing test paths and evaluating expectation/assertion changes. Standing
test authority supplies permission, not acceptance of unreviewed bytes. Refuse
missing provenance, mismatch, divergence, overlap, conflict or stale/ambiguous
review and return for correction. It never stages; after bounded verification it
passes the prepared diff to Slawomir.

Custody modes protect evidence, not checkout modes. Before managed import each
existing target must be a non-symlink regular file matching reviewed base bytes
and already owner-writable. A failed type/byte/write check refuses the entire
import before content or mode mutation and returns exact repair to `baton.ops`.
Do not work around it using chmod/install/privileged replacement. Copy reviewed
content without custody modes; verify final bytes and modes. New regular files
use ordinary non-executable repository mode unless executable mode is explicitly
in scope.

