# Finding: build the OCI reference worker and local runtime adapter

Work `W2930`, child of W1425. This M2 slice follows the durable Worker Manager
core W2929.

## Confirmed boundary

Implement one OCI container per assignment attempt, runnable through a
constrained Docker or Podman adapter, plus the `baton-worker` entry point. The
agent runs directly in that container: no nested runtime and no host runtime
socket. The manager remains the only authority client.

Support both a pinned read-only Git source materialized into one private
writable workspace and a digest-bound read-only directory source with a
separate declared writable result. Runtime ids, engine payloads and host paths
remain adapter diagnostics, never protocol identity.

## Recommended patch ownership

Own the v12 worker image/entry point, OCI adapter, container/runtime modules,
Git and directory materializers, workspace/output/credential policy, fixtures
and focused tests. Do not change authority semantics, manager control-store
ownership, provider adapters, proposal integration, or root/v11 release paths.

## Acceptance

- Resolve the pinned image and policy, validate explicit mounts/resources/
  network/user/capabilities, and launch with stable non-secret identity labels
  sufficient for restart reconciliation.
- Prohibit authority/config/database/executable, canonical repository, shared
  writable Git metadata, other worker state, runtime socket and nested runtime
  reachability; canonicalize mount sources before launch.
- Verify Git base/ref and directory tree digests before activation; inputs are
  read-only and every assignment receives a distinct writable workspace.
- Normalize start/inspect/cancel/collect/destroy through the adapter; prove
  exact runtime identity, fence before stop, quiescent versus destroyed, and
  positive absence before replacement or cleanup.
- Collect only declared output after runtime quiescence, recompute digests,
  refuse undeclared/missing/symlinked/over-limit output, and retain or seal
  recoverable cancellation material according to policy.
- Exercise Docker and, where available, the same adapter contract through
  Podman without changing worker-control vocabulary. Add negative/race/restart
  tests and leave provider certification to M4.

The implementer creates and exclusively owns `PROGRESS.md` when this Work is
routed for implementation.
