# Make runtime credential slots readable without widening bearer custody

Work: W52800
Parent: W51487
Discovered by: `attempt-w51487-run3`

## Classification

**Confirmed defect.** A credential is materialized successfully and mounted at
the authorized target, but the fixed execution identity cannot read it. The
worker checks existence rather than readability, so the provider reports an
opaque not-logged-in exit instead of a typed delivery refusal.

## Observed

- Run3 used the credential replaced from an authenticated host session and
  reproduced run2's exact `provider-failed`, status-1, no-API-time result.
- A harmless manager-owned `0600` file bind-mounted as the slot is visible to
  uid 65532 but cannot be read: `os.access(..., R_OK) == False` and `open`
  raises `PermissionError(13)`.
- The same harmless file at `0640`, with the container holding its group as a
  supplementary group, is readable. No real credential was used in this
  reproduction.
- Evidence: parent `evidence/w51487-run3/blocker.md` and
  `review-2026-08-31T09-16-34Z.md`.

## Confirmed code boundary

- `v12/python/src/baton_v12/worker_manager/credentials.py` owns volatile
  credential materialization and pins `VOLATILE_DIR = 0o700` and
  `VOLATILE_FILE = 0o600`. Existing tests explicitly require manager-only
  readability.
- `v12/python/src/baton_v12/worker_manager/oci.py` owns the execution vector,
  fixes uid/gid 65532, adds the configured workspace group, and binds each
  credential file read-only at `/run/baton/credentials/<slot>`.
- `v12/worker/claude_agent.py::_prepared_home` owns adapter preflight. It tests
  only slot existence before symlinking the slot into the provider home.
- The source file's host parent does not need to be traversable by uid 65532
  once the engine binds the individual file, but the bound inode's uid, gid and
  mode still decide target readability.

## Decision required

The current manager-only `0600` rule and the runtime's need to consume the
credential cannot both remain true. The correction must explicitly define who
may read the live bearer; it must not make the credential world-readable or
silently depend on the manager's incidental primary group.

**Proposed:** keep manager ownership, assign each materialized slot to the
deployment's already-validated execution workspace group, create it atomically
at `0640`, retain the volatile root at `0700`, and keep the runtime bind
read-only. Add an adapter readability preflight using `os.access(slot,
os.R_OK)` so a broken delivery becomes a typed refusal without the adapter
opening or publishing bearer bytes.

The implementer must revalidate how the configured group reaches credential
materialization before changing code. If that group cannot be made an explicit
operand without collapsing ownership boundaries, return for a narrower
credential-reader-group ruling rather than inferring one.

## Decision — 2026-08-31

Approved the proposed immediate reader contract. Keep the volatile root
manager-owned at `0700`; create every live slot atomically at `0640` with the
explicit deployment-configured workspace group as its gid; retain the fixed
execution uid 65532, its already-authorized supplementary workspace group, and
the exact read-only OCI file bind. The adapter must distinguish missing from
unreadable slots before provider launch and must not open or publish bearer
bytes merely to diagnose readability.

The workspace group is sufficient for this MVP boundary: the manager-only
root prevents host traversal, while the container receives only its assigned
slot as an exact bind. A second credential-reader group would add provisioning
without narrowing what the container can see. This ruling does not authorize
global shared credential sources or permanent manual staging. W52821 owns the
later per-OS-user, per-profile and per-assignment source/materialization model;
this Work fixes the attempt-local reader contract needed to unblock dogfood.

Existing assertions and prose that require manager-only `0600` slots are
explicitly authorized to change to this ruled `0640` contract. Coverage must
include the explicit gid, denial without the supplementary group, teardown and
recovery, secret sweeping, and a real-container positive/negative proof.

## Implementation-start revalidation — 2026-08-31

The ruling still matches the current tree. The ordinary dogfood launcher
already reads one nominal `WorkspaceGroup` from the manager store before both
operations that need it: `_launched` assigns `group = _configured_group(store)`,
then calls `CredentialHome.materialize`, and later gives the same capability to
`OciAdapter`. No configuration vocabulary or second group lookup is needed.

The smallest safe manager boundary is a new required keyword-only
`workspace_group` operand on `CredentialHome.materialize`. It must require the
nominal `WorkspaceGroup`, not accept a bare integer, and validate it before
creating the attempt root. `_launched` passes the already-read capability.
Direct tests and the boundary inventory pass capabilities minted from their
manager stores. Retry construction does not rematerialize a credential.

Creation order is security-significant. Passing `0640` to `os.open` is
necessary but not sufficient because umask may narrow it, and changing gid
after writing would leave bearer bytes briefly assigned to an ambient group.
The safe order is:

1. exclusive-create the empty slot with a mode no broader than `0640`;
2. `fchown` that open descriptor to the explicit configured gid;
3. `fchmod` the still-empty descriptor to exact `0640` after `fchown`;
4. only then write the registered bearer bytes.

Any group or mode failure therefore unwinds an empty inode and the attempt
root; no bearer bytes reached the wrong permission. Tests should observe this
ordering rather than only the final `stat`, and should run under both permissive
and restrictive umasks.

Recovery also needs the ruled fact. `CredentialHome.adopt` currently proves
the slot is a file and reads it back for secret re-registration, but proves
neither gid nor mode. Give adoption the same nominal group capability and
refuse a live slot whose `lstat` is not exact `0640`, manager-owned, and in the
configured gid before reading it. The ordinary retry builder already has the
same configured group available. Teardown and orphan discard require no new
group operand because they remove exact manager-owned paths rather than grant
runtime access.

The adapter correction stays local to
`claude_agent._prepared_home`: after the existing missing check, require
`os.access(slot, os.R_OK)` and raise a distinct bounded `TaskRefusal` before
provider launch. `os.access` diagnoses the worker's effective identity without
opening bearer bytes. Preserve the existing no-fallback missing refusal and
the no-child-stream-publication rule.

Focused baseline before implementation:
`PYTHONPATH=src python3 -m unittest tests.manager.test_credentials
tests.manager.test_claude_agent` from `v12/python` ran 151 tests, all passing.
The reviewer cannot access the Docker socket; the implementer owns the required
real-container positive/negative gate.

## Acceptance boundary

- The bearer is never created at a mode broader than the ruled group-readable
  mode, even briefly; umask cannot accidentally decide it.
- Slot gid is the explicit configured grant, not an inherited or ambient group.
- The manager retains read/write lifecycle custody; the execution uid can read
  the read-only bind only through the ruled supplementary group; a container
  without that group cannot read it.
- Missing and unreadable slots produce distinct bounded typed refusals before
  provider launch, without reading or publishing credential content.
- Credential teardown, orphan recovery, failed-start cleanup, start replay,
  secret scanning and durable lifecycle evidence remain unchanged and
  secret-free.
- Unit tests pin literal modes, gid assignment, exclusive creation and adapter
  refusal. A focused real-Docker gate proves positive readability with the
  configured group and negative unreadability without it.
- After independent sign-off, W51487 resumes with fresh identities; no prior
  result or provider conversation is reused.
