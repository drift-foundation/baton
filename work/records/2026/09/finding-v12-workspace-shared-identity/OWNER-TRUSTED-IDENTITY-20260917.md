# Owner decision: deliberately configured, trusted UID/GID

2026-09-17, recorded by baton.prompt from Slawomir's explicit selection after
discussion of automatic startup validation versus a trusted deployment contract.

## Current contract

Support a deliberately configured, trusted UID/GID arrangement shared by the
manager and applicable worker processes. Document the supported host/container
mapping and operator configuration. Trust that configuration rather than
launching a container to discover or prove the effective mapping.

Perform cheap structural configuration checks (valid identity values, required
configuration, compatible declared settings). Report actual access failures
directly with actionable operation/path/error context. Do not claim the mapping
was experimentally verified. Sharing a UID/GID does not require an automatic
probe or a persisted observation record.

This EXPLICITLY SUPERSEDES the automatic runtime-identity observation requirement,
its startup/activation placement alternatives, persistent mapping proof/cache,
and associated probe lifecycle/cleanup acceptance obligations in earlier
FINDING, PLAN and review entries. Those entries remain historical evidence.
Previously discovered helper defects explain the abandoned approach; they do not
require further rounds to perfect a helper that is no longer part of the product
path. Remove the newly introduced probe machinery if it has no remaining caller,
and adjust its tests as part of the authorized scope. Do not remove unrelated
pre-existing engine cleanup coverage or leave known-unsafe reachable behavior.

## Still required

- Use the configured identity consistently in workspace creation, worker and
  applicable custody execution; create usable access without recursive permission
  normalization or one held descriptor per repository entry.
- Preserve private HOME/cache, credential boundaries, read-only input/review
  mounts, separate participant identities and cross-Job confinement. A shared
  filesystem identity is not itself an isolation mechanism.
- Demonstrate worker/manager access to owner-only files in both directions under
  the supported arrangement. Preserve necessary bounded-descriptor integrity
  checks and truthful failure reporting.
- Use short deterministic tests for the complete creation/launch/consumption
  path and incompatible declared configuration/access failure. Broad regression
  selection follows the separately recorded short-test cadence.
- Deliver one complete candidate for independent review. No live model or engine
  qualification, installed-instance mutation or failed-attempt recovery is added.
  Fresh timestamped deployment follows acceptance, preserving the old instance.

The implementer should update the current PLAN at the next owned edit to reflect
this supersession, and the reviewer should assess against this contract rather
than the abandoned automatic-probe design. This is owner direction within the
existing Work, not a new design-approval round.
