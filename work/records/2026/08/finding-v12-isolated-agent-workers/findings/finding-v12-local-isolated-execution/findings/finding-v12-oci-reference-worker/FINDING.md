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

## Canonical v11 rebinding — 2026-08-24

This record is now bound to v11 Work `W5`, contained by `W3`. The opening
`W2930`/`W1425` names are retired-authority locators retained as provenance;
they are not current coordination identities. W4 closed satisfying before W5
became ready.

## Prerequisite revalidation against the landed Python manager — 2026-08-24

**Observed:** W5 is not one implementation cut yet. Campaign PLAN item 20 now
requires milestones to contain bounded Jobs, and this record is already at the
maximum dossier nesting depth. Its implementation Jobs therefore need
top-level permanent dossiers with explicit forwarding links back to W5.

**Observed:** the Python Worker Manager exposes only the current runtime
adapter calls `start`, `list` and `stop` in
`v12/python/src/baton_v12/worker_manager/attempts.py`. Its public package says
output freeze, intake, cleanup, agent state machines, public composition and
positive runtime absence are absent rather than stubbed. In particular, an
empty adapter listing deliberately produces `execution_runtime=uncertain`;
there is no certified observation shape that can prove the exact runtime
absent, clear the authority gate or safely permit a second start.

That is correct fail-closed W4 behavior, but the original W5 acceptance assumes
the missing manager receivers already exist. W5 must not invent competing
manager envelopes or infer settlement from Docker/Podman status. Before the
integrated OCI lifecycle can land, M2 needs the separately ruled W4 follow-up
Jobs for:

1. the complete worker-control/agent-session contract inventory and public
   manager composition;
2. the agent-session state machines and runtime/agent adapter protocols;
3. the output freeze/collector handoff and sealed artifact verification;
4. intake, retention and cleanup; and
5. worker-control §13 redaction, credential and durable-surface enforcement.

These are manager-owned prerequisites, not hidden W5 implementation. The
lower-level filesystem materializer, OCI argv/policy builder and worker image
can proceed independently once their exact interfaces are pinned; lifecycle
composition, positive absence, collection and destruction cannot.

## Frozen-runtime facts revalidated — 2026-08-24

**Confirmed:** worker-control 1.0 makes the adapter a reporter, not an
authority. Start/cancel/inspect/collect/destroy operations are effectively once
under manager operation identities. A cancel reply is not death; `quiescent`
is not `destroyed`; zero listed runtimes is not positive absence; engine status
is diagnostic until normalized and accepted by the manager.

**Confirmed:** source and output rules are byte-bearing boundaries, not mount
configuration conveniences. Directory inputs contain only sorted regular
files and must match the declared tree digest/count/bytes. Git inputs resolve
the exact immutable `base_revision`; a moved optional ref refuses. Inputs are
read-only, workspaces and Git metadata are private per assignment, outputs do
not overlap inputs or one another, and collection reads sealed bytes only.

**Observed:** the frozen Node proof remains useful executable evidence but is
not an implementation base. Its strict containment, no-link copy, manifest,
canonical-mount, constrained argv and positive-removal checks are candidates
to port by behavior. Its direct Docker calls, operator credential copy,
Claude-specific entrypoint and two-container preclaim/execution layout are not
adopted merely because the old tests pass.

**Observed read-only baseline:** Docker client/daemon 29.1.3 is reachable with
API 1.52, cgroup v2, overlay2 and the built-in seccomp/AppArmor posture. The
locally available base resolves to
`node@sha256:3638d9a6fe4030bd716be989438248074489337ba3275657f93595428be4fc03`
(`sha256:9da0264d...` locally). This identifies available evidence; it does not
approve an unpinned tag or certify the future worker image.

## One topology ruling is required before decomposition — 2026-08-24

**Open:** the campaign says “one OCI container per assignment attempt,” while
the frozen assignment and agent-session contracts require one pre-claim
consent runtime/session with no assignment, workspace, output or execution
tools, followed by a distinct execution runtime/session that receives the
writable private workspace only after `assignment.activate`. OCI bind mounts
cannot be added to a running container. The frozen Node proof therefore used
separate consent and execution containers.

The implementation must not resolve this by pre-mounting a writable workspace
before claim, mutating a consent session into execution, or moving
provider-native agent code onto the trusted host. The recommended
clarification is:

- one OCI container per **posture runtime** under one `runtime_attempt_id`;
- a read-only, non-executing consent container is positively quiesced/destroyed
  before activation; and
- one separately created execution container receives the exact activated
  assignment and its private writable workspace.

This preserves both physical capability timing and the two frozen runtime
axes, but it narrows/supersedes the campaign's ambiguous singular-container
phrase. Approver confirmation is required before child Jobs and image/runtime
contracts are created.

## Proposed bounded W5 Jobs after the ruling

Because this record is at maximum nesting depth, create these as ledger
children of W5 bound to promoted top-level records:

1. **Source and workspace materializer:** Python regular-file tree hashing,
   strict directory copy, exact Git object/ref verification, private writable
   clone/workspace creation, non-overlap and race/symlink refusal. No engine
   mutation.
2. **OCI adapter core:** closed Docker/Podman command vectors and inspection
   decoder; exact image/policy/profile resolution; canonical mount sources;
   fixed non-secret labels; start/list/inspect/stop/destroy and certified
   positive-absence observations. No provider SDK or authority access.
3. **Reference worker image:** digest-pinned image plus `baton-worker`
   entrypoint and protected framed control channel. M2 uses the deterministic
   scripted agent required by conformance; live provider certification stays
   in M4. Provider-native implementation remains opaque inside the image.
4. **Sealed output collector and credentials:** assignment-scoped,
   non-persistent credential delivery; quiescence-before-freeze; declared
   regular-file output only; byte/tree recomputation; immutable staging and
   leak refusal before the manager accepts an observation.
5. **Local OCI lifecycle composition:** compose the reviewed parts with the
   completed manager receivers, exercise mutable Docker through the trusted
   adapter, prove restart/duplicate-start/cancel/absence/intake/destroy
   ordering, and exercise the same adapter contract through Podman when it is
   available. This is implementation integration; W6 remains the independent
   109-case `local-oci` certification.

The detailed source review and conformance-case inventory are retained in
`evidence/w5-intake-revalidation-2026-08-24.txt`.

## Consent/execution OCI topology — confirmed 2026-08-24

Slawomir approved the recommended clarification. One logical
`runtime_attempt_id` may span two sequential posture-specific OCI containers:

- a restricted consent container has no writable execution capability;
- consent is positively quiesced and destroyed before activation; and
- only after successful claim and activation is a distinct execution
  container created with the private writable workspace.

The consent container is never promoted and its future workspace is never
pre-mounted. This supersedes the ambiguous “one OCI container per assignment
attempt” wording: the durable identity is one attempt, while physical
containers are posture-specific capabilities whose lifetimes do not overlap.
The ruling is message M6617 on W5's canonical thread.

## Decomposed implementation Jobs — 2026-08-24

The five W5 children and their promoted permanent records are:

1. W6631 — source/workspace materializer,
   `work/records/2026/08/finding-v12-oci-source-workspace-materializer`;
2. W6632 — constrained OCI adapter core,
   `work/records/2026/08/finding-v12-oci-adapter-core`;
3. W6633 — reference worker image and entry point,
   `work/records/2026/08/finding-v12-oci-reference-worker-image`;
4. W6634 — sealed output and assignment-scoped credentials,
   `work/records/2026/08/finding-v12-sealed-output-credentials`; and
5. W6636 — local OCI lifecycle composition,
   `work/records/2026/08/finding-v12-local-oci-lifecycle-composition`.

Manager-owned prerequisites are W6592 (contracts inventory/public
composition), W6627 (agent-session/runtime protocols), W6628 (output receiver),
W6629 (intake/retention/cleanup), and W6630 (section 13 security). W6634 must
wait on W6628 and W6630. W6636 must wait on all five component Jobs and all five
manager Jobs. Those two children are implementation-routed, so their exact
edges are owed by `baton.impl`; reviewer authority cannot mutate their graphs.
