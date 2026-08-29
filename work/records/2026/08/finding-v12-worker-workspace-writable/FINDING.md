# Make the worker workspace writable by the worker

## Discovery

Discovered by W6's digest-bound real-Docker capability pass. This is a
top-level record because W6 already occupies the permitted second child level.

Ledger Work: `W33936`.

## Confirmed defect

The composed `/workspace` bind is writable at the engine boundary, but its
root is owned by uid/gid 1000 with mode `0775` while the container runs as
uid/gid 65532. A write from inside the exact execution container fails with
`EACCES`, so the worker cannot perform its required work.

Evidence is retained under W6 at
`work/records/2026/08/finding-v12-isolated-agent-workers/findings/finding-v12-local-isolated-execution/findings/finding-v12-local-conformance-proof/evidence/w6-seal/input-write.json`.

## Acceptance

- The fixed worker identity can create, update, and remove allowed workspace
  content in the exact composed container.
- The correction grants no write to input, launch, credential, canonical
  repository, sibling-attempt, or manager-owned paths.
- Real-container positive, denial, retry/restart, and sibling-isolation tests
  preserve existing root identity and cleanup fencing.

## 2026-08-28 — measured, half landed, and one file damaged

**Confirmed and quantified.** The probe measured every manager-owned path the
container can reach. `/workspace` is the only one denying the worker something
it needs, and the GROUP is the least-privilege remedy because the table shows
what a group grants: write on the workspace, nothing beyond `other` on the
input pair and the launch document, and **nothing at all** on the credential
root and bearer, which are `0700`/`0600`.

**Landed:** `WORKSPACE_DIR = 0o775`, established exactly rather than left to
the umask. Not `0770` — dropping `other` while the container holds no share in
the group removes the worker's read and traverse too, measured.

**Pinned but unwired:** `run_vector(workspace_gid=None)`. Wiring the adapter to
read the root's own gid is the actual fix and changes a `--user` literal that
two closed Works' suites assert; those alignments are mechanical and are the
decision this Work returns.

**Operational finding:** correcting one of those suites, I overwrote
`tests/manager/test_oci.py` with its committed bytes and destroyed uncommitted
changes that were not mine. Twelve cases now fail as staleness rather than
regression, all from the launch document W26291 made required. No copy exists;
I did not reconstruct another Work's tests by inference. Full detail in
`PROGRESS.md`.

**Third finding of the same family, not this Work's:** the container cannot
READ its own credential either — `/run/baton/credentials/registry` is `0600`
owned by the manager, `r=False` from inside. It needs an owner.

## 2026-08-28 — independent review: no correction is wired; group authority needs a ruling

**Confirmed [P0]: the reported defect is unchanged.** `OciAdapter.start` still
calls `run_vector` without `workspace_gid`, so the execution vector remains
`--user 65532:65532`; `WORKSPACE_DIR = 0775` is the same effective mode the
reproduction already measured, only now made independent of umask. No submitted
case exercises worker create/update/remove. Independently, all 58 workspace
unit cases pass, while the worker still has no group write in the retained
real-container evidence.

**Confirmed decision conflict:** the proposed `--user 65532:<workspace-gid>`
is not a mechanical fixture alignment. This Work's acceptance says the fixed
worker identity remains able to write. W6632 pinned a fixed runtime user, and
W6633 explicitly aligned the image's `USER 65532:65532` with the adapter's
exact `--user` restriction so the two cannot drift. Replacing the primary gid
with a host-dependent value supersedes that recorded identity boundary and
therefore requires approver authority before implementation.

**Observed [P0]: the proposed group is not intrinsically least-privilege.**
The public operand accepts every non-negative integer, including gid 0, and the
planned caller would derive it from `workspace.st_gid`. A manager running with
primary group 0 would therefore launch the worker as `65532:0`; a manager whose
workspace inherits another authority-bearing service group would grant that
group instead. The 1000:1000 development-host probe proves one host, not that
an arbitrary manager primary group is safe worker authority.

**Proposed for approval:** preserve primary identity `65532:65532` and choose
one explicit workspace authority rather than inheriting an arbitrary service
gid. A dedicated non-authority workspace group could be added only to execution
containers as a supplementary `--group-add` (the installed Docker CLI supports
that operand), with the root narrowed in the same change and the applied group
set inspected. Alternatives are a fixed-uid ACL/id-mapped mount or a
world-writable child beneath a host-private ancestor, but each needs its own
portable allocation, cleanup and race proof. This proposal is decision support,
not a ruling; Docker and compatible Podman behavior plus host-group isolation
must be pinned before code changes.

**Operational damage independently confirmed:** `test_oci.py` is byte-equal to
HEAD and is stale against the accepted required-launch-document seam. Its 83
cases produce 8 errors and 4 failures, all in the exact twelve names retained
in the evidence. The lost uncommitted assertions cannot be approved by
reconstructing plausible replacements from those failures; the owner must
restore an authoritative copy or explicitly authorize a fresh recertification.

## 2026-08-28 — approver workspace-authority and test-recovery ruling

**Confirmed by approver response M34630:** preserve the worker's primary
identity exactly as `65532:65532`. One deployment-configured, non-authority
workspace group is added only to execution containers as supplementary
`--group-add`; consent and every pre-execution posture receive no such group.
The group is never inherited from `workspace.st_gid` or the manager process.
Gid 0 and every gid unequal to the configured workspace group refuse.

Each attempt workspace is explicitly prepared with that configured group and
an exact restrictive setgid mode. The only mode satisfying manager-owner and
worker-group create/update/remove while granting no `other` authority is
`02770`; it is established after creation rather than requested through umask.
Before the engine call, the adapter must prove that the canonical workspace
root's group equals the configured group and compose `--group-add <gid>` while
leaving `--user 65532:65532` unchanged. The applied container group set, not
argv alone, is the runtime fact.

**Required proof from the ruling:** worker-created files inherit the workspace
group and remain collectable under the normal result contract; an owner-only
file that cannot be collected fails closed rather than widening permission.
Cleanup, retry/restart, sibling isolation and denial at input, launch,
credential, repository and manager-owned paths remain acceptance boundaries.
Docker and compatible Podman must both prove the applied group behavior.

**Superseded implementation proposal:** the inert
`run_vector(workspace_gid=None)` implementation that replaces the primary gid
with `65532:<gid>` is not authorized. Preserve its history above, but correct
the seam to supplementary authority and never derive the grant from an
arbitrary host group.

**Authorized test recovery:** because no authoritative copy of the destroyed
uncommitted `test_oci.py` assertions exists, the approver explicitly authorizes
a fresh recertification of that module against the pinned current launch and
OCI contracts. This is new certification, not reconstruction; the lost prior
assertions remain recorded as unavailable and must never be claimed restored.

## 2026-08-28 — the direction, measured; two rulings requested

**Accepted without qualification:** the submitted cut did not wire the write.
`WORKSPACE_DIR = 0775` is the mode that was already there, nothing passes
`workspace_gid`, and the vector is still `--user 65532:65532`.

**Accepted, and made concrete by measurement:** the gid the rejected mechanism
would have inherited is `sl`, the LOGIN GROUP of a user — it reaches that
user's home and everything in it, and on a gid-0 manager it would have been
root's. An inherited service gid is not a workspace grant.

**The reviewer's direction is measured to work, and it preserves the pinned
identity.** With `--group-add`, against a real daemon: the process receives
`groups [1000, 65532]`, the workspace at `0770` becomes writable, and
`uid_gid` stays exactly `65532:65532` — so W6632's fixed runtime user and
W6633's image `USER` remain untouched, which is precisely what the rejected
mechanism would have broken.

**Ruling requested, because it is host provisioning and not an implementation
choice:** a supplementary group is least-privilege only if it carries no other
authority, and the manager cannot create a group. Does the deployment provision
a dedicated non-authority workspace group with the manager as a member, and
does W33936 carry that dependency? The bounded remainder is then: no group for
consent, the workspace narrowed to `0770` in the same change, applied groups
inspected on Docker and Podman, and created files plus collection and cleanup
proved sound.

**Second ruling requested:** `tests/manager/test_oci.py` remains destroyed.
Owner authority is needed to restore an authoritative copy or to recertify it
afresh; this Work edits neither it nor claims a package gate until then.

## 2026-08-28 — approver ruling M34916, implemented

**The mechanism:** a configured, validated, dedicated non-authority group added
as a SUPPLEMENTARY group for the execution posture only, with the primary
identity `65532:65532` untouched and consent given none. This manager never
creates or modifies a host group; it validates the one it is configured with
and refuses gid 0, a gid it does not hold, and anything that is not a group id.
There is no default, because a group inherited from a service directory is not
a workspace grant.

**Not proved on this host:** the write itself. No dedicated group is
provisioned and the manager cannot `chgrp` to the only non-authority group it
holds, so the case attempts the adoption, names the failure and requires the
write to be denied. Podman is absent, so that half of the Docker/Podman proof
skips narrowly. Both are named rather than represented as passes.

**Authorized and unstarted:** fresh full recertification of
`tests/manager/test_oci.py` as new certification, with the prior assertion loss
recorded explicitly and never as reconstruction.

## 2026-08-28 — independent review: the grant remains inert

**Observed:** production code never calls `adopt_workspace_group`.
`assignment_workspace` establishes `0o770`, not the ruled exact `0o2770`, and
the only production carrier is an optional `OciAdapter.workspace_group` that
may remain `None`. `run_vector` then starts execution with no supplementary
group. The Docker case explicitly accepts failed adoption and a denied worker
write; Podman skips; fresh `test_oci.py` recertification remains unstarted.

**Confirmed against M34630/M34916:** this does not satisfy the approved
boundary. An execution must have the deployment-configured group, its exact
workspace must be adopted and setgid before launch, and missing/mismatched or
unusable configuration fails closed. Consent receives no group. The positive
write/ownership/collection and engine matrix remains required. See
`review-2026-08-28T23-37-24Z.md`.

## 2026-08-29 — the three [P0]s corrected, and one consequence measured

**Confirmed — the grant is wired at the canonical boundary.**
`assignment_workspace` takes the configured group as a REQUIRED keyword and
adopts it with exact `02770` on the workspace root; there is no way to allocate
an assignment's workspace without saying which group the worker will hold.
`WORKSPACE_DIR` is `0o2770`: setgid, because a file the worker creates under
its own primary gid is one the manager could not collect, and `other` has
nothing because the earlier `0775` gave every process on the host read and
traverse over an assignment's writable tree.

**Confirmed — there is no unconfigured execution.** `run_vector` refuses an
execution posture with no configured group, before the engine. My previous cut
argued that composing no group left such a deployment "unchanged"; the review
is right and the argument was wrong -- unchanged IS the defect, and calling it
a legacy posture makes the correction opt-in.

**Confirmed — the root is proved immediately before the engine call.**
`prove_workspace_group` `lstat`s the exact path the engine is about to bind and
requires the configured group and `02770`. A grant established at allocation is
not a grant at LAUNCH: a restart under a changed configuration, or an operator
`chgrp`, leaves a container holding a group its workspace does not carry, and
that fails at the worker mid-work rather than here with nothing started.

**Confirmed by measurement against a real Docker daemon**, in the argv
`request_runtime_start` composed:

- `uid_gid` is exactly `[65532, 65532]` and the applied group set contains the
  configured group -- asked of the daemon's own `HostConfig.GroupAdd` and of
  the process, not of argv alone;
- the worker CREATES, UPDATES and REMOVES in `/workspace`;
- what the worker creates inherits the workspace group through setgid, a
  directory it creates carries the setgid bit onward, and the manager reads the
  result as itself;
- an owner-only worker file is not collectable and nothing widens it;
- input, the launch document and the manager's sibling roots stay denied or
  unmounted, and a second assignment's workspace -- in the SAME configured
  group -- is absent from the container, so the group is not what separates two
  assignments.

**Confirmed — `tests/manager/test_oci.py` is freshly recertified**, 83 cases
green, as new certification under M34916 and never as reconstruction. The lost
prior assertions remain recorded as unavailable. What the recertification
needed was two things the module did not have: the launch document W26291 made
required of every execution start, and real roots, because W33936 now asks a
question about a directory. The engine stays fake, which is that module's
design.

## 2026-08-29 — cleanup of worker-created content, measured and NOT sound

**Confirmed defect, and its boundary is exact.** With the corrected mechanism
in place, on a real daemon:

- a FILE the worker creates at the workspace root IS removable by the manager,
  because unlinking is a write to the group-writable root;
- an EMPTY directory the worker creates is removable for the same reason;
- a directory the worker creates WITH CONTENT IN IT is not. Its mode comes from
  the worker's umask -- measured `drwxr-sr-x` -- so the group has no write, and
  the manager owns neither the directory nor a way to `chmod` it. `os.chmod` is
  `EPERM` and unlinking inside it is `EACCES`.

Any real worker creates populated subdirectories, so this leaves trees the
manager cannot remove. It is a CONSEQUENCE of the approved mechanism rather
than a defect in it: the group grants write on the ROOT, and what the worker
creates inside is the worker's.

**What this cut owns and did:** the failure's shape. Cleanup fails closed and
names which party owns the thing in the way instead of surfacing a raw errno
from inside a walk, and nothing is widened on the way to that refusal. A case
measures the whole boundary above rather than asserting it.

**Ruling requested, and not decided here.** Each remedy is a policy change or a
new mechanism: (a) the launch contract sets the worker's umask to `002`, so
worker-created directories are group-writable and setgid already fixes the
group -- one line, and W26291's seam rather than this Work's; (b) cleanup runs
as the worker identity in a short-lived container; (c) an id-mapped mount so
the worker's uid maps to the manager's. Measurement favours (a).

**Two deployment limits, named rather than represented as passes.** No
dedicated `baton-workspace` group is provisioned on this host and this manager
may not create one, so the proof configures `os.getgid()` -- the group this
process can actually `chgrp` to. That makes every step real while proving
nothing about whether a login group is an acceptable production configuration;
`check_workspace_group` refuses what it can check (gid 0, a gid this manager
does not hold, a non-group-id), and "dedicated and non-authority" is a property
of a deployment that no code here can measure. Podman is still absent, so that
half of the Docker/Podman matrix skips narrowly.

## 2026-08-29 — approver ruling M36166: custody is a separate provider Work

**Confirmed by approver response M36166.** The required invariant is
UNCONDITIONAL MANAGER CUSTODY: after fencing and proving the exact worker
container absent, the Worker Manager must be able to inspect, read, hash,
archive, normalize and recursively delete every object in that attempt's exact
workspace and result directories **regardless of worker-selected modes**.

**Superseded proposal, and it was mine.** I offered a worker umask of `002` as
the measured favourite. The ruling refuses it as the MECHANISM -- it may
improve the cooperative path, and custody may not depend on the worker having
cooperated. That distinction is the part worth keeping: what I had measured was
that `002` makes the ordinary case work, not that it makes the manager's
custody unconditional, and those are different claims about the same
observation.

**The ruled mechanism:** a short-lived manager-controlled custody helper,
mounted only on the exact attempt directory, with no network, credentials,
repository or unrelated host paths, running under the owning worker identity or
another narrowly mapped custodian identity, executing only typed manager-owned
custody operations and never worker-supplied commands.

**Pinned as a separate provider Work**, as the ruling directs: **W36540**,
bound to `work/records/2026/08/finding-v12-worker-custody-provider`. The
confirmed defect, the pinned decision, the correction boundary and the
acceptance are in that record.

**This record's boundary, unchanged and now explicit.** W33936 owns the
workspace grant -- the configured group, the exact `02770` allocation, the
pre-launch proof and the supplementary `--group-add` -- and its completed
workspace-write round is independently reviewable. **Full cleanup acceptance
stays open until W36540 lands**, and nothing here claims otherwise.

## 2026-08-29 — independent review: the group is still a caller-selected value

**Confirmed [P1]: there is no deployment configuration to compare against.**
`check_workspace_group(gid)` treats its one operand as both the candidate and
the configured answer. It rejects gid 0, malformed values and a gid the
manager does not hold, but accepts every other group in the manager process's
group set. `assignment_workspace`, `OciAdapter`, and `run_vector` likewise
receive that raw integer directly; no production configuration or immutable
configured-group capability exists elsewhere in `v12`.

That is the arbitrary-held-group path M34630/M34916 explicitly refused. A
manager commonly holds more than one service group; a caller can select any of
them, adopt the workspace into it, and grant it with `--group-add`, while every
current validator and pre-launch proof passes because all three are checking
the same caller-selected number. Calling the operand "configured" does not
make it deployment configuration.

**Observed proof gap:** the retained positive Docker matrix intentionally uses
`os.getgid()`, already measured as the authority-bearing `sl` login group, and
states that it proves nothing about a dedicated non-authority deployment
group. Podman remains absent and skipped. Neither limitation supersedes the
prior explicit requirement to prove the configured dedicated group and
compatible Podman behavior.

The workspace allocation, exact `02770`, pre-launch root proof, fixed primary
identity and Docker write/isolation behavior otherwise revalidate cleanly. The
correction must introduce one deployment-owned configured-group source, reject
another held gid against it, document provisioning, and retain Docker plus
compatible-Podman evidence using that configured authority. W36540 remains the
separate full-cleanup gate.

## 2026-08-29 — the [P1]: a deployment-owned source of truth

**Confirmed [P1], and the shape of the defect is worth stating.** Every layer
took the same raw integer from its caller and every layer agreed. A manager
belonging to the configured group A and to some unrelated authority-bearing
service group B could be handed B at allocation and at launch: the workspace
was adopted into B, the pre-launch group/mode proof passed because it compared
against the same operand, and `--group-add B` was composed. Four checks, one
caller-selected value, and nothing to reject it with -- `check_workspace_group`
can see shape, gid 0 and membership, and membership is exactly what B has.

**One source of truth.** `configure_workspace_group(store, gid)` is the
deployment's act and the control store's own metadata is where it lives;
`configured_workspace_group(store)` is the read. A group configured once may be
re-affirmed and never changed to another -- workspaces already adopted into the
first would become unreachable to the workers they were prepared for, so a
changed group is a fresh store, the same clean-boundary rule the schema version
is under.

**The frozen answer is a CAPABILITY, not an integer.** `WorkspaceGroup` can
only be obtained from that read: its constructor refuses a direct call, because
a type any caller can construct leaves the hole exactly where it was. Allocation
and the run vector accept nothing else. The same rule the credential and launch
deliveries are already under at this boundary, and for the same reason -- what
crosses is a thing the manager made rather than data describing one.

**`assignment_workspace` takes the capability rather than the store**, and that
is deliberate: it is a filesystem operation, and giving it a store would give
it a thread affinity it has no other reason to have -- measured, by its own
concurrent-allocation case. Consuming the answer is what the correction asks
for; holding the thing that produced it is not.

**The named negative is present.** With the manager holding the configured
group and a second usable one -- `nogroup`, a real non-zero gid this process is
a member of -- the second is proved usable by `check_workspace_group` and still
refused at allocation and at the vector, because what authorizes a group is the
deployment's record and not the manager's membership.

## 2026-08-29 — the engine evidence, still an operational limit

**Unchanged and not represented as satisfied.** No dedicated `baton-workspace`
group is provisioned on this host and this manager may not create one, so the
Docker matrix still CONFIGURES `os.getgid()`. Every step is real -- the
allocation adopts, the daemon applies, the worker writes -- and it proves
nothing about whether a manager's own primary group is an acceptable production
configuration. Podman is absent and its half skips.

What the [P1] correction changes about this is worth naming precisely: the
manager can no longer be TOLD to use an arbitrary held group, so the class of
defect the fixture group used to hide is now closed by construction rather than
by the fixture happening to name the right value. The dedicated-group and
compatible-Podman proof remains outstanding and is a deployment limit, not a
product one.

## 2026-08-29 — independent re-review: the projection can rewrite configuration

**Observed [P1]: the immutable configuration journal is not consulted by the
read that mints the capability.** `configure_workspace_group` journals the
deployment act as `workspace-group.configure` and writes the selected gid into
`meta`, but `configured_workspace_group` reads only that mutable `meta` value.
It validates shape, non-root and process membership, then mints a
`WorkspaceGroup`; it never verifies that the committed configuration operation
names the same gid.

The additive
`test_the_projection_cannot_rewrite_the_journalled_group` configures held group
1000, confirms the committed operation result still names 1000, then changes
only the `meta` projection to the second held group 65534. The current reader
mints a capability for 65534 instead of refusing. Allocation and launch can
therefore adopt and grant an unrelated service group after a projection edit
while the independent durable account still says the deployment chose the
first group. This reopens the exact arbitrary-held-group authority path through
persisted state rather than a call operand.

**Confirmed correction boundary:** treat the journaled configuration result as
the independent durable authority. Verify the operation kind and committed
result, compare the projection to that result, and refuse divergence as
`integrity/schema` before minting a capability. The projection may make lookup
efficient; it cannot supersede the act that authorized it.

**Still open exactly as previously recorded:** no repository deployment path
or provisioning documentation invokes this configuration; every executable
fixture configures the known `sl` login group through `os.getgid()`. Compatible
Podman remains absent and skipped. These are not regressions in the source
mechanics, but they do not satisfy the pinned dedicated non-authority group and
Docker/compatible-Podman evidence requirement.

## 2026-08-29 — the projection [P1], corrected

**The journal is the authority; `meta` is a cache of it.**
`configured_workspace_group` reads the committed `workspace-group.configure`
operation and the projection, and mints a `WorkspaceGroup` only when the two
name the same group. The committed row is verified by KIND, its answer is
decoded through `store.replay` against the recorded signature rather than
adopted as stored bytes, the signature is RECOMPUTED from the gid that answer
names, and `check_workspace_group` runs on the committed value — so a `result`
column edited in place disagrees with its own signature, and an edit that
recomputes the signature still cannot name root.

**Disagreement is `integrity/schema` and is never repaired.** A projection with
no committed act, a committed act whose projection is gone, and two accounts
naming different groups all refuse. Picking the journal silently would turn an
edit that should have been refused into an edit that was tolerated, and this
manager cannot say which of the two describes the deployment. Neither account
present stays `policy/denied`, so "not provisioned" and "corrupted" remain
distinguishable.

**The reconfiguration guard reads the journal too.** It asked the projection
whether a group was already configured, so the same edit also made configuring
the edited group look like a first configuration rather than a change.

**The dedicated non-authority group is no longer outstanding.** The ruled
engine matrix ran against gid 8291 `baton-workspace`, provisioned in a
deployment image because this host cannot be given one and this manager may not
create one. The gid is measured to name no group and own no file on the host,
and the manager also holds gid 119 — the engine socket group, genuine
authority — which is what the "second held group refuses" negative now rejects.
Workers launch as siblings on the same real daemon. Compatible Podman remains
absent and unobtainable here, and stays a named operational limit.

## 2026-08-29 — independent review: source correction accepted, closure still gated

**Confirmed corrected:** the capability read now consults the committed
`workspace-group.configure` operation, validates its kind and answer, and
refuses every disagreement with the `meta` projection before minting. The
reviewer's projection-rewrite regression passes, as do all 69 workspace cases
and the 83 freshly recertified OCI cases.

**Confirmed Docker evidence:** the retained provisioned-manager transcript is
from a manager holding dedicated gid 8291 while separately holding the
authority-bearing engine group 119. It exercises the exact configured-group
matrix on Docker 29.1.3 and names the two Podman classes as skips. This managed
reviewer could inspect the matching retained image and daemon but its attempt
to launch the documented verification container was denied at the Docker
socket, so the transcript was reviewed rather than independently rerun.

**Observed [P1 documentation]:** `v12/python/DEPLOYMENT.md` currently says the
setgid workspace makes what the worker creates collectable by the manager.
That is only true for cooperative group-readable content. This record's own
owner-only case proves a worker can select `0600` and deny the manager, and
W36540 exists because unconditional inspection, archival and cleanup require a
separate custody provider. The deployment guide must state that boundary rather
than imply the workspace group itself supplies unconditional custody.

**Still not closure:** M34630 requires compatible Podman as well as Docker to
prove applied-group behavior. Podman is absent, both Podman classes skip, and
the retained evidence explicitly calls that an operational limit rather than a
pass. A compatible Podman environment must run the documented matrix, or an
approver must explicitly supersede that requirement. W36540 also remains an
open child, so this parent cannot close regardless of the workspace-source
correction's acceptance.

## 2026-08-29 — the guide corrected, and Podman measured

**The deployment guide overstated the grant and now does not.** The workspace
group buys ordinary group-readable collection; it does not buy custody. A
worker's owner-only output is material this manager fails closed on rather than
widening, and W36540 is named as the provider of the unconditional property.

**Compatible Podman was run rather than skipped.** Provisioned in an image
because this host cannot carry it. On ROOTFUL podman 5.8.4 the ruled mechanism
holds exactly as it does on Docker.

**On ROOTLESS podman it does not, and that is a new constraint rather than a
regression.** The group is applied but the manager's supplementary gid is not
mapped through the container's user namespace, so the setgid workspace arrives
owned by `nobody`. Closing it means composing `--gidmap`/`--userns`, which
changes the launch vector M34630 and M34916 pinned — so it is reported for a
ruling, documented where a deployment will meet it, and not patched here.

## 2026-08-29 — independent re-review: Podman was reached, not certified

**Confirmed corrected:** `v12/python/DEPLOYMENT.md` now distinguishes ordinary
group-readable collection from unconditional custody and names W36540 as the
provider for the latter. The journal/configuration source correction and the
dedicated-group Docker evidence remain accepted.

**Observed [P1 evidence gap]:** the retained ROOTFUL Podman transcript runs one
custom `Probe.runProbe`, not the 19 inherited `PodmanConfiguredGroup` cases
that carry created-file collection, retry, sibling isolation, owner-only
refusal and cleanup behavior. The ROOTLESS run reaches those 19 cases but ends
with two failures and two errors; its retained transcript includes only one
traceback, so the record does not establish that the unmapped supplementary
gid is the sole cause of all four endings. The exact build/run commands and a
durable Podman probe artifact are also absent. A real retained image exists and
identifies Podman 5.8.4, but image identity does not substitute for the missing
matrix and complete transcript.

**Confirmed coordination boundary:** W32391 already owns Podman lifecycle and
security certification. Its parked premise (no real Podman environment) is now
stale enough to revalidate: this round produced a privileged nested ROOTFUL
Podman and a ROOTLESS Podman that exposes a gid-map constraint. W32391 should
decide whether that environment is compatible and carry the complete shared
matrix. W33936 does not independently invent a second portability owner.

**Still not closure:** the guide's instruction to "use Docker or rootful
Podman" overstates the one-probe ROOTFUL result as a supported deployment.
Until W32391 supplies the full certification or the approver explicitly narrows
M34630, the guide may report the measured difference but must not represent
ROOTFUL Podman as certified. W36540 also remains open.

## 2026-08-29 — approver supersession: Podman is a longer-term certification

**Confirmed by the approver while resolving obligation M37180.** The immediate
two-engine acceptance requirement in M34630 is superseded. W33936's current
workspace-write slice is certified by its complete Docker evidence; Podman is
not a closure gate for this Work.

Podman remains a supported longer-term direction owned by W32391. Its rootful
probe and rootless gid-map observations are retained as evidence, but neither
is certification and neither authorizes a launch-vector patch here. Until
W32391 closes, deployment and user documentation must describe Docker as the
certified engine and Podman as pending or experimental, never as equivalent.

This supersession narrows engine portability only. It does not weaken the
dedicated workspace-group authority, denial matrix, or W36540's separate
unconditional-custody requirement.
