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
- The manager performs an explicit launch-time capacity preflight for the
  disk-backed workspace, and scratch bounds remain explicit and enforced.
  Checkout, build/cache, test artifacts, output, and logs do not depend on
  tmpfs.
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

## Production-conversation correction — 2026-09-03

The readiness conclusion immediately above is **superseded** by the live
W71917 submission. The persistent manager admitted and claimed the stage and
started its interactive Docker runtime, but no production owner opened the
worker-entry conversation or sent `describe` and `work`; Claude therefore
never started while the stage misleadingly projected `running`. Confirmed
defect W81857 owns the durable, restart-safe production conversation and
truthful status correction. W71917 is blocked on W81857. A recorded manual
conversation may gather evidence from the retained runtime, but cannot satisfy
this Work's ordinary autonomous-production acceptance boundary.

## Production conversation gate cleared — 2026-09-04

W81857 closed satisfying at commit `756b720`. Its independently reviewed
production path publishes commands and observes receipts, state and terminal
outcomes through one durable per-attempt file exchange; the worker continues
without a live Job Manager, and a fresh manager recovers by rescan without
opening stdin/stdout or issuing a second provider invocation. Its source-bound
real-container gate passed.

W71917 is therefore ready as the first ordinary self-hosted v12 workload. The
retained pre-W81857 runtime is not resumed or injected into: it contains old
worker bytes and has no exchange mounts. Submit a fresh Job and attempt through
the integrated persistent Job Manager and production worker factory, using the
committed source/workspace dossier as its immutable instructions. The existing
no-dogfood and no-per-iteration-complete-archive boundaries remain in force.

## Planning ownership clarification — 2026-09-04

Live dependency identities, gates, phases, and closure state belong to Baton's
authoritative graph, not to `PLAN.md`. The plan now states only durable product
prerequisites and sequence so graph changes cannot make it stale. This finding
retains the Work identifiers above solely as chronological evidence of what
happened and why the launch conclusion changed; they are not a second source of
current scheduler truth.

## First ordinary self-hosted run6 outcome — 2026-09-04

Run6 proved the production path far enough to admit and claim the Work, start
the selected real Claude image, publish the durable command, run the provider,
and receive a durable terminal. Claude itself returned status 0 after editing
ten substantive paths. The attempt is nevertheless not a review candidate:

- the worker terminal is `faulted` because mandatory compilation returned 1;
- the selected Claude image contains Python 3.11 while this distribution
  requires Python 3.13 or newer, and the exact failure is unchanged
  `worker_manager/custody.py` syntax that passes on host Python 3.13.7;
- the compile verifier added 149 Python 3.11 cache paths, inflating the patch
  to 10,779,527 bytes; and
- after Docker recorded the container exited, the live Job Manager continued
  to report the stage `starting`, its runtime `running`, and no exchange.

The retained proposal is diagnostic evidence only and must not be imported.
The Python-floor/candidate-clean verification defect (W85497) and the missing
faulted terminal observation (W85500) each have their own top-level record
because both affect every future workload, not only this source/workspace
change. A fresh ordinary self-hosted attempt follows those bounded corrections;
no manual conversion of run6 into a successful answer is permitted.

## Fresh ordinary attempt authorized — 2026-09-04

Revalidation against commit `8f809a9` confirms that the worker-image Python
floor, candidate-clean verification, durable terminal observation, and
cross-authority attempt-identity corrections are integrated. The authority
graph records no remaining blocker for this Work. Slawomir approved a fresh
ordinary v12 attempt from that committed baseline.

The new attempt uses fresh Job, control, Authority, launch, credential, and
workspace state. It must run through the persistent Job Manager and production
worker factory. It neither revives a retained runtime nor uses the dogfood
operator or a per-iteration complete candidate archive. The resulting worker
candidate remains outside the repository until independent review and bounded
integration.

## First ordinary self-hosted run7 candidate — 2026-09-04

The persistent Job Manager admitted and claimed one fresh implementation stage,
started the selected Python-3.13 Claude image, published the durable
`describe`/`work` exchange, observed a successful terminal, froze and retained
the output, passed the v12 assignment to its review route, and destroyed the
runtime. The canonical v12 stage is `completed`; no second episode or provider
turn was created.

The immutable proposal is retained at
`file:///home/sl/.local/state/baton/v12/w71917-run7/storage/attempt-52f7d8db784001dd9f81287043210bdbe6bbc85bdb560bc11874ddee8b600bab/custody/attempt-52f7d8db784001dd9f81287043210bdbe6bbc85bdb560bc11874ddee8b600bab/proposal`
with content digest
`sha256:c20afc41ee6c696cad610d7196e19647b94f290d66587ec576ede79dfe59f567`.
The provider returned status 0 and the required compile verification returned
status 0. `result.json` and `change.patch` agree on eleven changed paths. The
only changed existing tests are `tests/manager/test_dependencies.py` and
`tests/tools/test_single_worker.py`; three new source/workspace test paths are
also present.

This is implementation evidence, not approval. The proposal remains outside
the repository and awaits independent review against baseline `8f809a9`,
including discriminating source/workspace tests from a separate review copy.

## Run7 independent review — changes requested — 2026-09-05

Independent review reproduced the candidate's narrow manager tests but found
that the proposed source profile is never invoked by the production worker.
The real worker therefore still copies `/input/source` into its 64 MiB `/tmp`
scratch area instead of checking out the declared base into the disk-backed
workspace. The proposal does not satisfy the central acceptance path and is
not eligible for integration.

The review also found that cleanup can cross a same-filesystem bind mount,
the Git plan proves only that the declared commit exists rather than making it
the active checkout, restart can re-nominate a replaced source, the declared
live workspace quota is not enforced, and one existing terminal-observation
test still references the retired temporary directory. The exact candidate
regresses two pre-existing composed-worker tests. These are accepted-scope
defects, not optional follow-up hardening: source/workspace replacement
refusal, exact-base checkout, quota behavior, containment, restart adoption,
and preservation of existing behavior are explicit acceptance requirements.

The immutable run7 proposal and its digests remain evidence only. A correction
must connect the profile and declared base to real worker execution, place work
in the mounted disk workspace, prevent cleanup from entering any mount target,
preserve source identity across restart and handoff, enforce the declared live
quota, and restore the existing focused tests. It returns as a new immutable
proposal and digest for independent review. The complete evidence and exact
test accounting are in
`review-2026-09-05T03-51-18Z.md`.

## Object identity is durable; content identity is still refused — 2026-09-05

Pinned before implementation because it sits one word away from a rule this
record already states, and a reader who found only the code would reasonably
read it as contradicting that rule.

`adopt_source_boundary` says: "across a process restart the pinned inode is
recomposed from configuration rather than recovered from a durable record, so
what a restart proves is that the nominated path is still a real unaliased
directory outside this manager's storage ... not that the material behind the
path is the material an earlier incarnation saw. Recording that would be this
manager holding a content identity it is ruled not to take."

**The second sentence stands. The first is superseded.** The run7 review found
that a nominated path replaced while the manager is down is re-nominated and
accepted by the new incarnation, and that is a real hole in this record's own
acceptance — "a foreign/symlinked/replaced source or workspace refuses before
runtime start" does not carry an exception for a restart.

The distinction that makes both true at once is between two different things
the word "identity" covers:

- **Object identity** — the device and inode the manager itself observed when
  it nominated the directory. This is a fact about which OBJECT the path named,
  it costs no walk, no read, no hash and no enumeration, and this manager
  already pins it in memory and compares it within one incarnation. Persisting
  it changes nothing about what the manager looks at; it changes only how long
  the manager remembers what it already saw.
- **Content identity** — a digest, manifest or enumeration of what is INSIDE
  the tree. That is what the Git-agnostic ruling and the no-mandatory-walk
  ruling refuse, and it stays refused. A worker that needs to know which
  revision it received still verifies that itself against its own declared
  base.

So the correction persists the object identity and nothing else, and a restart
re-proves the recovered value exactly as a same-incarnation adoption does.

**It is recorded in the manager's own store, not in the input manifest.** The
retained manifest is per-attempt and already durable, which makes it the
obvious place and the wrong one: that document is also composed into the input
root and delivered read-only into the container, so a device number and an
inode written there are host filesystem facts handed to the worker, which has
no use for them and is the party the boundary exists to bound. The manager's
control store is where a manager-owned fact belongs.

**The same-incarnation handoff window is part of this decision.** The review
also found that the nomination descriptor is closed before the engine later
resolves the path. Re-proving at adoption narrows that window but does not
close it; closing it means keeping the validated object reachable through the
handoff rather than re-resolving a name. Whether that is a retained descriptor
or a resolution the adapter performs against the proved object is an
implementation choice, but the property is not optional: what the engine binds
must be the object the manager proved, not a path it re-reads.

## The workspace quota — DECIDED — 2026-09-05

**The earlier acceptance wording that called this a workspace quota is
superseded.**
The run7 review's [P1] is confirmed by reading the code and it is a real gap in
this record's own promises: `workspace_quota` validates that two numbers are in
range, `_capacity` asks the filesystem whether it currently has `max_bytes`
free, and then OCI supplies an ordinary writable bind mount. Nothing bounds
what the worker actually writes, and `max_entries` is never applied to the
mounted workspace at all. "Workspace quota and scratch bounds are explicit"
was the superseded acceptance wording; for scratch that was true and
kernel-enforced, and for the workspace it was a capacity check wearing a
quota's name.

The review offered two ways out:

**A — enforce a live ceiling.** A hard byte bound on a bind-mounted directory
needs one of: project quotas on the backing filesystem, a per-attempt loopback
image, or a storage driver whose size option this deployment can set. Every one
of those needs privilege or host configuration this deployment does not
currently have and which the certified image and rootless launch were
deliberately built without. A softer form is available without privilege — the
serving loop already sweeps, and it could measure the workspace and act on the
ceiling — but measuring means walking the workspace on a schedule, which is
cost this delivery has otherwise avoided, and it bounds nothing between two
measurements.

**B — record the weaker contract honestly.** Keep the two numbers as what they
demonstrably are: a DECLARED CAPACITY this manager proves the storage can meet
before it starts a runtime, and an admission bound on what a deployment may
ask for — not a limit the worker is held to while it runs. This costs no
privilege and no walk, and it makes the finding, `DEPLOYMENT.md` and the
member names agree with the mechanism. It also means a worker CAN fill the
backing filesystem, which is a real operational exposure and must be said out
loud rather than left implied.

**What must not happen is the third option**, which is to leave the current
text calling it a quota while the mechanism is B. That is the state the review
found, and it is the one thing neither ruling permits.

**Approved ruling: B for this Work.** Before launch, the manager proves that
the workspace's backing filesystem currently has at least the declared byte
capacity. That check is admission evidence only: it is neither a reservation
nor a live ceiling, and this Work makes no `max_entries` enforcement claim.
The code, field names, tests, and deployment documentation must describe that
weaker contract honestly. Scratch bounds remain real and kernel-enforced.

A worker can therefore fill the backing filesystem after admission. That is an
accepted MVP operational exposure, not an enforced quota. True live byte and
entry ceilings are separate v12 hardening Work because they change the storage
or privilege model; they are not on W71917's critical path.

## Corrected candidate review — changes requested — 2026-09-05

The fresh independent review of the working-tree correction is recorded in
`review-2026-09-05T05-51-35Z.md`. The capacity ruling, production profile
connection, exact-base checkout, restart identity persistence, and direct-child
mount refusal are present, but the candidate does not yet satisfy acceptance.

**Observed:** bottom-up cleanup detects a mounted directory only after visiting
its nested children; an independent probe deleted a nested foreign file before
raising the mount refusal. **Observed:** OCI accepts a genuine boundary proved
for one assignment together with another assignment's roots, including the
same host directory mounted read-write at `/output` and read-only at
`/input/source`. **Confirmed:** the already-recorded path re-resolution window
between source adoption and engine binding remains open. **Observed:** the
dogfood sender accepts invalid values for both members added to task schema
`/2`, deferring its promised preflight refusal to the worker.

The corrected bytes also remain mutable working-tree state with no new proposal
digest; the run7 digests bind superseded bytes. A subsequent review requires
the custody, handoff, and sender-validation corrections, discriminating focused
regressions, the durable real-container/provider gate already planned, and a
new immutable proposal with exact existing-test accounting.

## The source-object handoff: closed as far as a path-based engine allows — 2026-09-05

**Amended the same day by "Both bind sources, not one" below: the ruling this
section asks for covers the WORKSPACE as well as the source.** The reasoning
here is unchanged and the options are the same; what was too narrow was the
scope, and a source-only ruling would leave the writable half of one
substitution boundary unstated.

Pinned before the remaining half is anyone's to decide, because the earlier
ruling states the property absolutely — "what the engine binds must be the
object the manager proved, not a path it re-reads" — and this correction meets
it up to a boundary the manager does not own.

**What is now closed.** The second review's [P1] observed that
`adopt_source_boundary` proves `(device, inode)` and then the argv is composed
from a NAME, which `oci.canonical_source` resolves again and the engine
resolves a third time. `boundary_mounts` now re-proves the object at the moment
the binds are derived — the last instant at which this manager holds anything
but a string — and refuses when the path has been re-pointed since adoption.
A second gap the same review found is closed beside it: a `SourceBoundary` is
now bound to the exact allocated roots it was proved over, so a boundary
composed for one attempt cannot be handed to another attempt's start vector.

**What remains open, and it is not an implementer's choice.** The interval
between that proof and the engine's own resolution of the same pathname cannot
be closed while the engine takes a PATH. `docker` and `podman` accept
`--mount source=<pathname>` and resolve it themselves, in their own process and
their own mount namespace; there is no supported form in which this manager
hands the engine an object.

The two ways out, and their real costs:

- **A — hand the engine a descriptor-derived path.** The manager keeps the
  validated directory open and names it `/proc/<manager pid>/fd/<n>` as the
  bind source. The object is then unambiguous. It costs: a daemon that can read
  this manager's `/proc`, which excludes a remote or differently-namespaced
  engine; a recorded mount source that is meaningless once the manager exits,
  which is exactly what `oci._mounts_disagree` compares a restarted manager's
  observation against, so W81857's restart-safety would have to be reopened;
  and a descriptor held for the life of every runtime.
- **B — accept the residual interval and say so.** The manager proves the
  object as late as it can and the engine resolves the name microseconds
  later. An attacker who can replace a directory in that window can already
  replace it between any two operations the manager performs, and the
  nominated source is by construction material the deployment chose.

**Approved ruling pending.** This Work implements the narrowing either way,
since both options start from the same place, and takes neither privilege nor
restart-model change on its own authority. Until it is ruled, the acceptance
clause above is met at every boundary this manager owns and NOT at the
engine's own resolution, and `source_boundary.boundary_mounts` says so in as
many words rather than leaving a reader to infer that "re-proved" meant
"closed".

## The mount boundary is a pre-descent question — 2026-09-05

The run7 correction placed the cleanup's mount check inside a bottom-up walk
and reasoned that "a directory is always visited before its parent, so a
foreign mount is refused while every entry it holds is still there." That
reasoning is **superseded and was wrong**: it is true of a mount's own entries
and false of everything below them, because `os.walk(topdown=False)` yields a
mount's subdirectories before the mount itself. The second review reproduced
the resulting data loss — a nested file under a simulated mount was unlinked
and the refusal arrived afterwards.

The corrected rule is that the boundary is asked TOP-DOWN and the whole tree is
admitted before anything is removed. A refusal therefore precedes every unlink
in the tree rather than only those in the subtree that reached the mount, which
is also what makes a refused cleanup leave a state an operator can reason
about. The device comparison stays beside the kernel-table check for the reason
it was kept the first time.

## Third correction review — workspace identity is still path-only — 2026-09-05

The fresh review is recorded in
`review-2026-09-05T06-12-29Z.md`. It independently confirmed the top-down
cleanup, exact-assignment boundary, sender validation, image allowlist, and
last-manager-boundary source re-proof corrections.

**Observed:** a boundary composed over one writable workspace accepts a
different real directory created later at the same pathname. The independent
probe changed inode `40529730` to `40529733` and
`adopt_source_boundary` returned successfully; evidence remains at
`/home/sl/src/baton/.w71917-rereview-workspace-zc99t8dg`. The boundary records
device/inode identity for the source but only a path for the workspace, so its
claim that replacement rather than spelling is detected is true for only one
of the two mounted roots.

**Confirmed implication:** the pending object-to-engine ruling applies to both
mount sources. The workspace is checked for group and mode immediately before
launch but is also reduced to a pathname that the engine resolves later. The
ruling must either deliver both validated objects to the engine or explicitly
supersede the absolute no-substitution acceptance property for both residual
intervals. A source-only ruling cannot close the writable half.

The workspace identity correction itself is not pending that ruling: persist
and re-prove the object at composition/adoption and the last manager-owned bind
boundary, including across manager restart, and cover replacement by another
real directory rather than only by a symlink.

## Both bind sources, not one — 2026-09-05

The third correction review found that `SourceBoundary` pinned the source's
device and inode and held only the workspace's PATHNAME. A real directory
created at that pathname after composition was accepted by adoption: it
resolves to the same characters, it is a directory of its own, and it is on
real storage, so every question that was asked passed. The acceptance clause
already said a replaced source **or workspace** refuses before a runtime
starts, so this was a gap in this record's own promise rather than new scope.

**Corrected:** the boundary now proves both roots as OBJECTS, the durable pin
records both pairs in one write, and both are re-proved at adoption and again
where the runtime binds are derived. The same non-content rule governs the new
half exactly as it governs the old one — which OBJECT a path named, never what
is inside it.

**And the pending ruling is symmetric.** The residual interval recorded above
belongs to both bind sources, because the engine resolves the workspace's
pathname exactly as it resolves the source's. So the owner's choice is:

- **A — object delivery for BOTH roots.** The engine receives both validated
  directory objects rather than two pathnames, with the daemon-reachability
  and restart mount-comparison costs recorded above, paid twice.
- **B — supersede the absolute wording for BOTH residual intervals.** The
  acceptance clause is amended to say that a replaced source or workspace
  refuses at every boundary this manager owns, and that the engine's own
  resolution of each bind source pathname is an accepted residual interval.

A source-only ruling is not one of the options: it would leave the writable
half of the same boundary unstated, which is the shape of defect this record
has now corrected twice.

## Approved residual engine-resolution ruling — 2026-09-05

Slawomir chose **B** for both bind sources. The absolute acceptance wording
above is **superseded only for the two residual intervals between the
manager's final object-identity proof and the execution engine's resolution of
the source and workspace pathnames**. A replaced source or workspace still
refuses at every boundary the Worker Manager owns, including immediately
before it composes the runtime binds. The engine's subsequent resolution of
each pathname is an accepted MVP residual interval.

This ruling does not authorize descriptor-derived `/proc/<pid>/fd/<n>` mount
sources, daemon-namespace coupling, per-runtime descriptor retention, or a
reopening of restart mount comparison. It matches the current trusted-host MVP
boundary: prevent accidental substitution and detect replacement wherever the
manager can act, without claiming protection from a hostile process already
able to mutate the host paths during engine launch. Stronger object delivery
remains future hardening if the deployment threat model later requires it.

## Fourth correction review — the durable pin is not atomic — 2026-09-05

The fresh independent review is recorded in
`review-2026-09-05T06-27-02Z.md`. It confirms that the workspace is now proved
as an object in memory, against durable evidence after restart, and at the
last manager-owned bind boundary. The deterministic replacement gap from the
third review is corrected.

**Observed:** the persistence act does not keep its write-once promise under
concurrency. `pin_boundary_identity` reads an absent pin and then performs an
unconditional update on an autocommit connection. A two-connection probe
synchronized both callers after their absence reads; both returned success for
different source/workspace pairs, no caller refused, and the last update
silently replaced the first pair. Evidence remains at
`/tmp/w71917-pin-race-tf8rtvks`, with its driver at
`/tmp/w71917-pin-race.py`.

**Confirmed consequence:** two manager incarnations that compose on opposite
sides of a directory replacement can erase the original custody evidence and
make the replacement the durable answer. The first write must therefore be a
four-column compare-and-set, with exact replay versus collision decided in the
same transaction, and a forced two-connection regression must prove one
differing caller refuses. This is the concurrency form of the existing
replacement acceptance property, not new hardening.

The schema also advances to 16 while its version-history comment ends at 15;
the workspace-pair cutover must be named as schema 16.

## Fifth correction review — the durable pin is atomically write-once — 2026-09-05

The bounded correction is independently verified in
`review-2026-09-05T06-35-26Z.md`. `pin_boundary_identity` now acquires the
SQLite write lock before reading, conditionally updates only a wholly unpinned
row, and decides exact replay or collision before ending that transaction.

**Observed:** replaying the two-connection probe now produces exactly one
successful answer and one `operation-collision`; a third connection reads the
successful pair. The four additive regressions pass, including the same forced
schedule, and the schema history now names what version 16 adds. No new
implementation finding was identified in this correction.

This verification does not supersede the three remaining gates: the owner has
not yet ruled on both residual engine path-resolution intervals, the durable
real-container/provider gate and broad sweep have not run, and no immutable
29-path proposal or digest exists. Final approval therefore remains pending
those gates and a fresh review of the exact frozen bytes.

## Durable provider and broad-gate verdict — 2026-09-05

Slawomir's interactive operator run exercised the corrected working tree from
a durable host process rather than from a bounded managed turn. The current
Claude worker image built from the required `v12` context as
`sha256:0697b6595aff0af2a39a81d492223bf33cf69877426ec859fe1abb90abd617e4`.
A fresh schema-16 control store, Job store and Authority then drove one
ordinary production `tools.single_worker:factory` episode against manifest
`sha256:a777442e738b885e2d77358884549f960cab9bced9a37153b56abbb5d707378c`.

**The production provider boundary passed.** The offer was issued and consumed
once, generation 1 was claimed once, the worker accepted the durable
`describe`/`work` exchange, Claude returned status 0, and the independent
verification command returned status 0. The retained proposal contains exactly
one declared changed path, `W71917_PROVIDER_GATE.txt`, at content digest
`sha256:695be1d1d7192d799a9874dd51be86db3cc306c903fd5819d3187fa263b66ae9`.
The source checkout contains no such path, the stage is `completed`, and the
runtime is positively `destroyed`. The retained candidate's verification was
then rerun outside the worker and passed.

**The broad repository gate is not clean.** The canonical parallel runner
refused before executing because `tests.manager.test_source_boundary` and the
unrelated `tests.tools.test_quiescent_assignment_finalization` belong to no
registry. Full discovery with the large disk-workspace proof enabled ran 3,683
tests in 48.424 seconds and reported six failures, 20 errors and 21 skips. One
error is the same registry refusal; the other 19 are the expected consequence
of the restricted process being unable to reach the Docker daemon. The six
source failures are one unrelated stale Authority test catalog and the five
already-recorded boundary-inventory failures. No failure was reported from
`tests.manager.test_source_boundary` itself.

The real-Docker registry was therefore run separately with host engine access:
235 tests ran in 179.002 seconds, with four failures and 13 skips. Every failure
was an engine-cleanliness assertion against residue that predated this run: one
hour-old `baton-w6633` container and image plus 31 retained
`baton-runtime.start-*` containers from 22 hours to five days earlier. The
functional Docker assertions passed and this run left no matching live or
exited container of its own. Ambient retained evidence must not be deleted or
silently attributed to this Work.

**Verdict:** the source/workspace mechanism and real provider path satisfy this
Work's functional acceptance, but these bytes are not yet eligible for the
immutable freeze. The Work's own new source-boundary module must be registered
in the canonical parallel runner and that corrected gate must be rerun. The
unrelated unregistered quiescence module and pre-existing catalog/inventory
failures remain separately attributable baseline work; they are not authority
to expand W71917 or to report the whole repository green.

## Digest-bound review — boundary inventory omissions are not baseline — 2026-09-05

The immutable-candidate review is recorded in
`review-2026-09-05T07-28-56Z.md`. It independently verified that the 30 v12
paths, modes and bytes match candidate digest
`sha256:daf2bd4f13eb8d095efdd0098e258ba494d2b74467a41b8b2141da6d74d6f52f`,
that the declared base is current `HEAD`, that the approved residual-interval
ruling is reflected in code and deployment documentation, and that the durable
provider evidence supports the recorded functional pass.

**Observed:** the broad parallel gate's five boundary-inventory failures are
not solely pre-existing baseline. Their exact failure sets include all four
new source/workspace identity columns, the new `pin_boundary_identity` and
`boundary_identity_of` operands, OCI's new source-delivery operand, and the
new source-boundary types, operations, consumed declaration members, and
workspace capability entries. The candidate edits the inventory test only to
add four columns to two fixture rows; it declares no owners and supplies no
probes for the newly discovered entries.

**Confirmed consequence:** the candidate expanded the missing-owner and
missing-probe sets guarded by the repository's fail-closed boundary inventory.
An unchanged failing test name or total is not an unchanged failure. Every
W71917-introduced entry must be classified and probed without weakening the
assertions, the corrected parallel phase must be rerun, and the resulting
bytes require a new manifest and digest. The current digest remains durable
review evidence but is not approved for integration.

## Superseding-digest review — two stated witnesses do not prove their entries — 2026-09-05

The fresh digest-bound review is recorded in
`review-2026-09-05T07-57-56Z.md`. The correction removes every W71917 entry
from the residual missing-owner, missing-probe, orphan-owner and untracked-
column sets, and its 30-path manifest exactly binds digest
`sha256:cdd285d098dd67dc449be864a016f6cf3c539e9418a45de700eae7e39c140199`.

**Observed:** the correction adds 35 stated-owner entries, not the 29 reported
in progress and the handoff. Together with ten layer/delegated probes and four
persisted-column exemptions, all 49 W71917 inventory entries are classified.
The count correction is documentary; it does not change the frozen bytes.

**Observed:** the stated owner for the exported `mount_table.what` and
`mount_points.what` operands says no caller can supply them, but the witness
only scans internal call sites. A direct caller can supply either operand. On
an unreadable-table path both operations interpolate that value without
`label_of`; an object whose `__format__` raises escapes as `RuntimeError`
instead of the manager's closed refusal. The structural witness therefore
proves a different fact from the caller entry it declares.

**Observed:** the witness registered for
`OciAdapter.__init__.source_delivery` calls `run_vector` directly with its
different `source_delivered` operand. It never invokes the constructor entry,
never proves its exact-type owner, and bypasses the constructor-held value's
path to `_source_mount`.

**Confirmed consequence:** the exact missing-entry sets are corrected, but
the inventory is still green only because two declarations are backed by
witnesses that do not exercise their claimed boundaries. Bound and probe the
public diagnostic operands at their real door, exercise the OCI constructor
entry and held-value path, rerun the gates, and supersede this digest before
integration.

## Final digest-bound review — approved exact candidate — 2026-09-05

The final independent review is recorded in
`review-2026-09-05T08-20-30Z.md`. It approves exactly the 30 paths, modes, and
bytes in `candidate-2026-09-05T08-16-44Z.manifest`, at aggregate digest
`sha256:15291e091b85e5674dd074913eedd9a100e667dc1665fabd0a17af99c32c0a89`
against base `8f809a945715e5156ee60500fbe5257e2b478cd5`.

**Confirmed:** `mount_table`, `mount_points`, and `check_disk_backed` each
bound their exported diagnostic operand at the operation's own door. The
behavioral witness drives hostile formatting, a surrogate, overlong text, an
integer, and `None` through the real refusal paths. The original hostile
object now reaches a closed `ContractRefusal` from both mount-table operations
without executing caller formatting.

**Confirmed:** the OCI witness now invokes `OciAdapter.__init__`, proves its
exact-type and posture rules, asserts that it retains the exact accepted
boundary, and drives that retained value to the assignment-root provenance
refusal during `start`. It no longer substitutes `run_vector`'s different
operand for the constructor entry it claims to witness.

**Confirmed:** the manifest's base, 30-path set, modes, per-path digests, and
aggregate all match the current candidate. The two-path correction passes its
focused witnesses and 1,353-test focused sweep. The canonical parallel gate
reproduces 3,646 tests with only the six separately attributable failures and
no W71917 failure-content regression. No new finding remains open against the
reviewed candidate. Any candidate drift requires a new manifest and review.
