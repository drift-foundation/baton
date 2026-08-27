# Remove acquisition from the core manager and preserve an explicit source-stager boundary

W15232, follow-up to W6631 under W5.

Follow-up to W6631 (`W5: Materialize exact source and private workspaces`),
discovered while W14251 revised worker-control for the artifact-neutral manager
ruling pinned in
`work/records/2026/08/finding-v12-isolated-agent-workers/FINDING.md`.

## Observed — 2026-08-26

W6631 delivered `v12/python/src/baton_v12/worker_manager/workspaces.py` with
public `materialize_git_source` and `materialize_directory_source` operations.
Those operations choose and execute acquisition semantics inside the core
manager and validate their operands against the frozen `gitSource` and
`directorySource` definitions by name.

W14251's attempted artifact-neutral schema revision removes those definitions.
The unchanged workspace module then refuses every acquisition request before
the contract/vector changes can be measured. The reproducer and provisional
schema patch are preserved in W14251's dossier:

- `work/records/2026/08/finding-worker-control-artifact-neutral-io/evidence/gate-blocked-on-workspaces-2026-08-26.txt`;
- `work/records/2026/08/finding-worker-control-artifact-neutral-io/evidence/schema-patch-2026-08-26.diff`;
- `work/records/2026/08/finding-worker-control-artifact-neutral-io/evidence/revise_schema.py`.

## Confirmed decision — 2026-08-26

W14251 remains a contract/conformance revision and is not widened to delete or
re-home shipped manager code. This follow-up to W6631 owns the implementation
boundary.

The core Worker Manager is artifact-neutral. It receives an already staged,
read-only input directory and its generic integrity envelope; it does not
choose an acquisition operation, understand Git/directory/archive/provider
semantics, or execute clone/copy/extract behavior. The umbrella ruling states
that population of the staged directory is outside the Worker Manager and may
be performed by a source stager.

Therefore this Work removes the acquisition-aware public surface from the core
manager. If the existing exact-copy/Git logic remains required by an already
pinned downstream path, re-home it behind an explicitly named source-stager or
driver boundary outside `baton_v12.worker_manager`; otherwise remove it and its
stale public inventory/tests. Do not invent a second acquisition contract to
preserve code that the superseding ruling made ownerless.

W14251 gates on this Work. The ordering is deliberate: the acquisition-aware
module can be removed or re-homed while the old schema remains present, leaving
a green distribution; W14251 can then remove the obsolete schema vocabulary,
vectors and conformance expectations without a contradictory shipped manager
surface.

## Acceptance

- `baton_v12.worker_manager` exports no Git- or directory-acquisition
  operation and interprets no acquisition-specific descriptor.
- Generic manager-owned duties remain: assignment-private paths, read-only
  staged input, writable/private workspace containment, integrity/identity
  checks, and cleanup.
- Any retained acquisition implementation has an explicit non-manager owner
  and boundary consistent with the umbrella's source-stager rule; otherwise it
  is removed.
- Public exports, boundary/secret inventories, focused tests and distribution
  gates agree with the new ownership.
- W14251's preserved neutral-schema patch no longer fails because code names
  `gitSource` or `directorySource`.

The implementer creates and exclusively owns `PROGRESS.md`.

## Independent review — 2026-08-26

**Confirmed P1.** The acquisition entry points and descriptor validators are
gone, but acquisition-specific workspace behavior remains inside the retained
`assignment_workspace` helper. It still creates and returns a root named
`git`, and its contract says that root holds per-assignment Git metadata. The
retained tests require all three `inputs`, `workspace`, and `git` roots.
`worker_manager.oci` independently closes its assignment-root contract over
the same three names and requires the Git root even though neither posture may
mount it. The pinned ruling is broader than deleting the old public method
names: the core
manager does not understand Git, and private ephemeral capacity is generic
rather than a Git protocol surface.

The call-graph partition classified `assignment_workspace` as generic as a
whole and therefore missed the acquisition-specific branch inside it, while
the review search named the same leak in the OCI root vocabulary. Remove the
`git` root from the helper, OCI root contract, callers and tests; a future
Git-capable driver may allocate private capacity under its own contract. Keep
the generic input/workspace containment and cleanup behavior.

**Confirmed P2.** The module-level contract still says this component rebuilds
and delivers sources, injects `GitPort`, and owns private Git metadata, and the
file ends under an empty `delivering a source` section. This is now false
public documentation for the shipped module and should be replaced by the
artifact-neutral measurement/workspace contract that survived the cut.

The additive regression, exact lines, and verification are recorded in
`review-2026-08-26T09-47-16Z.md` and
`evidence/review-2026-08-26T09-47-16Z.txt`.

## Independent re-review — 2026-08-26

**Confirmed corrected:** `assignment_workspace` now creates and returns only
the generic `inputs` and `workspace` roots. `oci.ROOT_NAMES` closes the adapter
over the same two roots, and the focused workspace/OCI suite passes all 97
cases, including both review regressions. No executable manager code retains a
Git metadata root or acquisition operation.

**Observed P2:** two acquisition-era documentation remnants still contradict
that corrected boundary. The live OCI root commentary says a private `git`
root exists as manager-owned metadata even though the immediately following
contract correctly has only two roots. The workspace test module's top-level
contract still describes the deleted Git acquisition/ref cases and fake
repository, and it retains unused `SHA1` and `MOVED` fixtures from those
deleted cases. These do not reopen the functional correction, but acceptance
requires the retained tests and live boundary documentation to agree with the
new owner.

Exact evidence is recorded in `review-2026-08-26T12-19-34Z.md` and
`evidence/review-2026-08-26T12-19-34Z.txt`.

## Final independent review — 2026-08-26

**Confirmed corrected and signed off.** The remaining acquisition-era
documentation is gone: the live OCI commentary states the exact generic
two-root contract, and the workspace test contract describes only the
measurement, isolation, containment and cleanup behavior that survives this
cut. The deleted Git fixtures are absent.

The focused workspace/OCI slice passes all 98 cases. An independent copy of
the distribution was then revised with W14251's preserved neutral-schema
script; the workspace suite passes all 24 cases against that copy, directly
confirming that removal of `gitSource` and `directorySource` no longer breaks
this manager surface. The dependency/public-operand checks pass. The focused
inventory checks that can reach completion pass; the two that cannot are
intercepted first by `sealing.py:_relative`, a concurrent W6634 boundary with
no literal inventory label, and do not name a W15232 surface.

Review and exact evidence:
`review-2026-08-26T13-33-08Z.md` and
`evidence/review-2026-08-26T13-33-08Z.txt`.
