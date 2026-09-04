# Mount immutable v12 sources and persistent disk workspaces

Ledger Work: W71917

Parent: `work/records/2026/09/finding-v12-standalone-multi-job-pipeline/`

Decision source: W62098.

## Confirmed scope

Implement the generic runtime boundary ruled in W62098: one immutable
read-only source mount and one separate manager-custodied, disk-backed writable
Work workspace. Container tmpfs is bounded scratch only. Output and logs remain
separate durable manager-owned areas.

For the common local source, the input provider nominates the existing source
directory and the runtime bind-mounts that exact directory read-only. The
generic manager performs no Git operation and no mandatory source-tree copy,
snapshot, enumeration, or hash prelude. A Git profile names the exact base/ref
in metadata and instructs the worker to clone copy-safely inside its writable
workspace; non-Git profiles consume the same generic mount boundary according
to their own declared format.

This leaf owns mount/allocation/lifecycle semantics and retirement of the
copied/tmpfs bootstrap path. It does not own scheduler stage state, candidate
review cycles, Git proposal validation, or integration.

## Observed baseline — 2026-09-02

- `worker_manager/workspaces.py` allocates manager-owned input/workspace roots
  and still includes bounded directory measurement/copy helpers for staged
  inputs.
- `dogfood_operator.py` performs a mandatory source-tree preflight/copy and
  the bootstrap runtime uses small tmpfs capacity unsuitable for real builds.
- Existing OCI launch machinery already distinguishes read-only input from a
  writable output surface, but it does not yet expose the ruled nominated
  source plus persistent Work-workspace production profile.

## Acceptance

- Runtime launch receives a manager-validated source directory mounted
  read-only and a distinct manager-created disk-backed workspace mounted
  writable; neither path is caller-substitutable after validation.
- The local default reaches launch without walking, copying, snapshotting,
  enumerating, or hashing the source tree and without the manager running Git.
- A Git-aware worker clones copy-safely into the workspace, verifies the exact
  declared base, performs a real build/test-sized write exceeding 64 MiB, and
  cannot mutate the mounted source.
- A non-Git fixture consumes the same generic source/workspace mount contract
  without Git inference by the manager.
- Workspace quota and scratch bounds are explicit. Checkout, build/cache,
  test artifacts, output, and logs do not depend on tmpfs.
- Restart/relaunch re-adopts the one manager-owned Work workspace safely; a
  foreign/symlinked/replaced source or workspace refuses before runtime start.
- The copied per-file-hashed Git bootstrap path is retired from ordinary
  dogfood once this profile launches the same useful assignment; explicitly
  requested generic file snapshots remain possible under their own provider.

## Test-change authority

This Work authorizes adding tests and editing existing tests under
`v12/python/tests/` for source/workspace allocation, OCI mounts, copy-free
launch, disk capacity, containment, restart, Git-aware and non-Git fixtures,
and bootstrap retirement. Any deletion or weakened expectation must be
explicit and independently reviewed; unrelated test changes are excluded.

## Execution ordering — 2026-09-02

The scope above is approved as the first ordinary workload driven by the
persistent v12 Job manager from W71875. It does not return to the supervised
dogfood operator and does not create another per-iteration complete candidate
archive. Work begins only after W71875 is independently reviewed and integrated
so this leaf can exercise the durable submission, workspace, status, review,
and correction line it is intended to enable.

## Execution-order correction — 2026-09-03

The final sentence above is **superseded** where it treats W71875 alone as a
complete launch path. W71875 intentionally implements only `admit` and
`claim`; no production deployment composition yet starts the claimed runtime.
This Work therefore waits for the approved one-worker bootstrap W76207 as well
as W71875. Once W76207 is integrated, this remains the first ordinary
self-hosted v12 workload and still does not use the dogfood operator or a new
complete candidate archive.

## Launch-preflight correction — 2026-09-03

The readiness statement above is temporarily superseded by confirmed defect
W81115. Revalidation before the first real submission found that W76207's
production composer does not materialize the `/input/task.json` document the
certified Claude worker requires before provider execution. W71917 remains the
first ordinary self-hosted workload, but it waits for that bounded production
task-delivery correction rather than launching a container known to fail.

## Launch gate cleared — 2026-09-03

W81115 closed satisfying after implementing and independently validating the
production task-document delivery. The production factory now holds the exact
digest-bound task bytes during static validation and publishes them as the
read-only `/input/task.json` before source composition and input-root freeze.
Together with closed W71875 and W76207, this clears the recorded prerequisites
for the first ordinary self-hosted submission. W71917 is ready to enter the
persistent v12 Job Manager; the no-dogfood and no-new-candidate-archive limits
remain in force.
