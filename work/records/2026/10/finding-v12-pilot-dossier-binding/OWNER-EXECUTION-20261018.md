# Owner ruling — 2026-10-18

Owner: "if W321688 is nearly done we can accept it but this is why we need to
make all future work go through v12 unless there is a blocker".

Conditional exception for this Work only: preserve already-authored shared-tree
changes, assess remaining correction size, and finish bounded corrections if
nearly complete. Independent review still must accept exact bytes and required
recovery/containment behavior before a scoped human commit. This is not candidate
acceptance or a claim of isolated v12 execution. Keep immutable candidate/base/path/
digest evidence; no cleanup/reset or opportunistic edits to other Work. If the
remaining work is substantial, prepare execution through v12 instead.

This supersedes a requirement to discard/reimplement or repeat already completed
W321688 work solely to change its execution mechanism; it preserves provenance
and acceptance requirements. It does not grant an exception to W321689/W321690
or other future product implementation.

All future product work executes through v12 unless a concrete blocker is recorded
in its owning Work with the exact unavailable operation and bounded fallback.
V11 coordination and candidate packaging alone do not establish v12 execution.
AGENTS.md carries the standing policy. Slawomir retains all Git operations.

Schema decision is separately resolved by owner response321966 to obligation321894:
schema6 selected, schema5 refused with no migration; retain old stores and matching
build. No production deployment or migration selected.
