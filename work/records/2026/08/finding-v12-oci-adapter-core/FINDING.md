# Finding: build the constrained OCI adapter core

Promoted implementation record for the second bounded child of W5. Its Work is
contained by W5 while this permanent dossier is top-level because the parent
record is already at maximum nesting depth.
Canonical Work: W6632.

## Confirmed boundary

Implement a runtime-neutral Python adapter core for Docker and compatible
Podman: closed command vectors, image/profile/policy resolution, canonical
mount sources, fixed non-secret reconciliation labels, bounded diagnostics and
typed start/list/inspect/stop/destroy observations. The engine reports facts;
it never decides assignment authority, settlement or retry.

The adapter must prove the exact runtime identity and positive absence rather
than treating an empty list, a stop acknowledgement or engine prose as death.
Drop all capabilities, deny privilege escalation and nested runtime/socket
access, apply fixed user/resource/network/filesystem policy, and never mount
authority/config/database/repository internals or another worker's state.

No source materialization, provider code, output acceptance, credentials or
manager lifecycle orchestration belongs here.

## Acceptance

- Golden Docker and Podman argv/inspect vectors share one worker-control
  vocabulary and reject unknown/contradictory engine data.
- Exact label and image/profile/policy digests survive restart reconciliation.
- Stop, quiescent, destroyed and positive absence remain distinct.
- Duplicate starts, stale identities and ambiguous multi-match listings fail
  closed without inferring authority from engine state.
- Mutable engine smoke tests are isolated and leave their own resources absent.

The implementer creates and exclusively owns `PROGRESS.md` when claimed.

## Independent correction re-review — 2026-08-25

Disposition: **changes requested; the returned correction is partial**.

**Confirmed:** the six original reviewer regressions are corrected. Engine
names are valid derivations, inspection binds the exact runtime, absence prose
names the requested identity, label members use their semantic rules, unknown
manager-prefixed labels refuse, and mount spellings are canonical. The prior
39-case OCI module passes.

**Observed [P1]:** the required assignment-owned mount allowlist is still
absent. The adapter accepts `/srv/repositories/baton/.git` because it is not
under one of `_FORBIDDEN`'s system prefixes. Nothing in `run_vector` or
`OciAdapter` receives the assignment's permitted input/workspace roots, so the
boundary cannot distinguish a legitimate assignment mount from repository or
other-worker state. The additive
`test_a_repository_outside_assignment_owned_roots_is_not_mountable` fails.

**Observed:** resolved image/profile/policy/adapter identity is still not bound
as one input to argv and reconciliation labels; the constructor receives only
the image digest and accepts caller-supplied labels independently. The
receiving inventory/probes and the dossier-required isolated Docker cleanup
smoke plus compatible Podman coverage also remain absent, as PROGRESS states.

Review: `review-2026-08-25T00-19-47Z.md`.

## Assignment-root API ruling requested — 2026-08-25

**Confirmed:** adding `/srv/repositories` or `.git` to `_FORBIDDEN` would make
one regression pass while preserving the denylist defect. A mount is admissible
only because its canonical source equals or is segment-wise contained by a
root owned by this assignment, not because its spelling avoided known system
prefixes.

**Proposed for approval:** `run_vector` and `OciAdapter` require the exact
`assignment_workspace` root record plus a closed posture. The record has
exactly `inputs`, `workspace`, and `git`; `git` is manager-private and never
mountable. Consent permits no assignment-root mounts. Execution permits the
`inputs` root or its descendants read-only and the `workspace` root or its
descendants with the requested writability; a writable inputs mount refuses.
`_FORBIDDEN` is removed once this positive proof owns the question. Roots alone
are insufficient because they cannot select consent versus execution topology.

The approver must confirm this public contract change before implementation.

## Confirmed assignment-root API — 2026-08-25

The proposed positive authority model is approved. `run_vector` and
`OciAdapter` require both a closed `posture` and one exact
`assignment_roots` record containing exactly `inputs`, `workspace`, and `git`.
Roots alone never select posture.

Consent permits no assignment-root mount. Execution permits the canonical
inputs root or a segment-wise descendant only read-only, and the canonical
workspace root or a segment-wise descendant with the explicitly requested
read/write mode. The private git root is never mountable. Writable inputs,
foreign or other-assignment roots, ambiguous/overlapping roots, and nested or
overlapping source/target spellings refuse. `_FORBIDDEN` is removed when this
positive ownership proof lands; path admissibility is never inferred from
avoiding a list of known-bad prefixes.

This ruling does not close the other review corrections: resolved
image/profile/policy/adapter identity, receiving inventory/probes, isolated
Docker cleanup evidence, and compatible Podman coverage remain required.

## Assignment-root implementation re-review — 2026-08-25

Disposition: **changes requested**. The denylist is removed and the required
root/posture API corrects the original repository, host, socket, private-Git,
writable-input and consent cases. The positive proof remains incomplete:
lexical `normpath` containment accepts a symlink descendant resolving outside
the assignment, overlapping roots are accepted, and nested source/target
mounts are accepted despite the explicit ruling. Three additive methods
produce four focused failures; the prior 45 cases pass.

Resolved image/profile/policy/adapter identity remains split, the inventory
currently has 20 unowned and 17 owned-but-unprobed OCI entries, and isolated
Docker/Podman evidence remains absent. Review:
`review-2026-08-25T03-01-06Z.md`.
