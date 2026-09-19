# V12 workspace access through a shared execution identity

## 2026-09-17 — observed failure and confirmed owner decision

Recorded by baton.prompt following Slawomir's explicit decision to manage this
v12 correction through v11. This is a separately bounded follow-up to W183883,
not a reopening of the standalone installer or a transfer of the v12 Job.

### Observed

The installed first Job `codex-adapter-first`, v12 Work `a2b0d14b-W1`, failed
before provider runtime start. Its attempt is
`attempt-7a06eb4497395f38e6d45044ec437f9c40e93ba47fd12fc10655958432c6b072`.
The public preparation-failure reader reported:

> initial development-line access failed: OSError; no permissions were changed; keep the line materializing and ungranted

The private checkout was measured as 18,078 files/directories. The owner read
`/proc/4068395/limits` on the host and supplied:

```text
Max open files            1024                 524288               files
```

`v12/python/src/baton_v12/worker_manager/workspaces.py`,
`_provision_line_access`, retains a descriptor for each visited file/directory
through full preflight and subsequent fchown/fchmod, then closes them. This
confirms descriptor use proportional to tree size and a recursive permission
pass. Descriptor exhaustion strongly explains the refusal, but its original
errno was discarded and is not recovered evidence. Last observed stage state:
implementation exceptional, review blocked; no provider runtime started.
Do not infer that its claim, allocation or partial line has been released.

### Confirmed decision

Use a trusted workspace execution identity shared by the manager and applicable
worker processes, with compatible UID/GID mapping across host and containers.
Establish usable access at creation rather than recursively repairing a tree.
The preferred direction is a shared workspace UID/GID, with isolation enforced
by private mounts, read-only inputs/review snapshots and stage write scopes.
Exact numeric identities and supported engine mapping are implementation choices
to revalidate against current deployment. A shared group alone does not solve
programs creating mode-0600/0700 entries; cover this explicitly.

This supersedes requiring distinct filesystem owners plus recursive permission
normalization for this trusted execution path. It does not supersede separate
participant identities, independent review, immutable reviewed bytes, credential
isolation, cross-Job isolation or write boundaries. Shared UID is not itself an
isolation mechanism; never expose unrelated host paths or another Job's writable
workspace merely because identities match.

Closing descriptors earlier or increasing RLIMIT_NOFILE is insufficient: remove
the permission-only whole-tree preparation pass. Initial materialization and
required integrity/result checks may remain proportional to content; identify
their costs honestly rather than claiming all operations become constant time.

### Scope and acceptance

- Implement the identity/access contract in workspace creation and worker launch,
  including manager consumption of worker-created owner-only files and directories.
- Remove recursive initial chmod/chown provisioning from the selected path;
  reject incompatible configuration early with actionable diagnostics.
- Preserve no-follow/path confinement, immutable input and review boundaries,
  separate credentials, concurrent Job isolation and honest failure states.
- Deterministic focused tests must include trees larger than a 1,024 descriptor
  limit, bounded peak descriptors, no permission walk proportional to unrelated
  entries, and repeated preparation/retry behavior. Count operations as well as
  elapsed time; do not create a million-file stress campaign to prove this.
- Separate unavoidable materialization/integrity costs from permission setup;
  retain genuine coverage while updating superseded ownership expectations.
- Document compatibility and an owner-reviewable installed-runtime update and
  failed-attempt recovery procedure. Preserve the existing attempt/evidence;
  no raw-store reset, duplicate submission or deletion of its partial line.
  If supported recovery has an independent gap, report it as separate Work.

No live model calls, broad stress campaign, production deployment/retry, v11
engine redesign, Job submission UX or Codex adapter implementation is included.
Independent review precedes deployment. Raising the descriptor limit is not the
accepted product fix. Earlier incident history remains in
`work/records/2026/09/finding-v12-stack-launcher/FINDING.md`.

## 2026-09-17T12:32:56Z — independent baseline and implementation return

Reviewer baton.codex, claim 194488. The implementer's claim 194465 returned
revalidation only: no product/test candidate and no verification run. The owner
decision above remains the implementation authority; this is not a new approval
gate. See `review-2026-09-17T12-32-56Z.md` for the current handoff.

**Confirmed:** both `_provision_line_access` and `_prove_line_consumable` retain
descriptors proportional to entries. The latter does not mutate permissions, but
still fails on a large tree even when manager and worker share an owner. This
explicitly corrects the narrower implementer assessment that consumption is not
part of the defect. Bounded descriptor use for necessary consumption checks is
within the existing manager-consumption/resource acceptance boundary. Removing
the recursive permission pass alone is insufficient.

**Observed:** `reproduce-review-194488.py` exercised each helper in a separate
child with soft RLIMIT_NOFILE 1024, over 1,100 regular files plus the root.
Both encountered errno 24 (EMFILE): provisioning peaked at 1,020 tracked open
descriptors and consumption at 1,021. Both closed all tracked descriptors on
failure; fixture ownership and modes were unchanged. Tracking excludes internal
scandir descriptors and the interpreter baseline; these are not total-process
peak measurements. `REVIEW-EVIDENCE-194488.json` records source digest and raw
results. Total measured reproduction time, including fixture setup and children,
was 0.315243359 seconds. The fixture remains at
`/tmp/w194457-review194488-7kvc6kme` for operator cleanup.

**Evidence correction:** 18,078 is the installed checkout entry count, not a
measured peak of simultaneously open descriptors. The original incident errno
remains unknown. The independent fixture establishes EMFILE on these paths; it
does not retrospectively recover that incident's discarded errno.

**Confirmed code boundaries:** workspace group capabilities already have durable
configuration provenance. Worker and custody vectors currently pin 65532:65532;
the engine test documents a host-observed remapped owner. Equal numeric container
and host IDs alone therefore cannot establish compatible mapping. Root creation,
worker/custody launch, owner-only result consumption, image/provider writable
homes, and read-only input/review mounts must be revalidated together. Keep
content integrity, custody quiescence and confinement checks even where their
current code also performs permission normalization.

**Proposed implementation direction:** mint one trusted execution-identity
capability from deployment configuration alongside the workspace group, and
carry it through applicable worker and custody launches. Prefer the non-root
manager's effective UID and explicitly configured workspace GID with a supported,
validated host/container mapping. Exact representation and mapping support remain
implementation choices under the owner decision. Reject incompatible or unknown
mapping and identity drift before affected execution effects; never substitute
an unverified caller integer or assume the login group is the workspace group.
Preserve distinct consent behavior, private credential homes and writable mount
scopes. Deterministic mapping tests are not evidence of an actual engine run.

## 2026-09-17T12:47:56Z — partial candidate, pre-grant race regression

Reviewer baton.codex, claim 194592; author claim 194532. The workspace helpers
and their tests changed, but worker/custody vectors still select 65532:65532.
Shared-identity execution, mapping validation and written recovery instructions
remain outstanding. No partial acceptance or deployment approval is given.

**Confirmed regression:** the old provisioning walk rechecked each held entry's
owner, link count and mode after traversal and before permission application.
The replacement `prove_line_integrity` closes each child after its first check
and removes that later validation. A deterministic local interleaving adds an
outside hardlink to the first visited file while the second sibling is opened.
The historical helper refuses with `an initial development-line entry changed
before provisioning`, retaining root mode 0700. The candidate integrity proof
and establishment both return, leaving link count 2 and granting root mode
02775. This directly contradicts the claim that every prior integrity/race
constraint is preserved. Repair the pre-grant invariant with bounded descriptors;
do not restore O(entries) held descriptors or silently weaken the acceptance.
See `reproduce-review-194592.py` and `REVIEW-EVIDENCE-194592.json`.

**Verified partial result:** 272 focused workspace/review-cycle tests pass in
2.298 test-reported seconds (2.464576 seconds measured subprocess wall time).
The complete reviewer harness including the race comparison took 2.472358
seconds. This confirms existing test success, not full Work acceptance. The
fixture remains `/tmp/w194457-review194592-hwmsrz9w` for operator cleanup.

**Evidence custody correction:** rerunning the earlier reviewer script under
author claim 194532 overwrote `REVIEW-EVIDENCE-194488.json` with candidate-run
results. Its observed digest became
`34468bd5a3c8f32f7b5cf9d3535b05cfe3f22b276586506e5b3017c920c5c80f`.
The original JSON was recovered from the recorded tool output into
`RECOVERED-REVIEW-EVIDENCE-194488.json`; its digest exactly matches the original
handoff's `bac0d0689009345681c6f7afdfc5df73b33394a86ec0388f64c59b334d4beb1b`.
Preserve the overwritten bytes as `AUTHOR-RERUN-194532-preserved-194592.json`,
then restore the original path from those digest-verified original bytes. This
is an explicit evidence repair, not a fresh baseline run. Future reruns must
write new claim-specific outputs; the old reproduction's fixed output path is
not safe to reuse unchanged. Earlier review journals remain unchanged.

## 2026-09-17T12:58:44Z — race and operation-count corrections verified

Reviewer baton.codex claim 194666, reviewing author claim 194622. This explicitly
supersedes the open status of findings 1 and 3 in the preceding review for the
candidate digests recorded in `review-2026-09-17T12-58-44Z.md`. Finding 4's evidence
repair remains intact: the original baseline JSON still matches its original
digest. Finding 2, shared execution identity, remains open and blocking.

**Confirmed:** the integrity helper now retains fingerprints in memory and
compares them in a second no-follow traversal, with descriptors bounded by
depth. The original hardlink interleaving now refuses before root access is
granted, leaving mode 0700. Actual fchown/fchmod/chown/chmod calls are observed by
the permission-count test. The deterministic workspace/review-cycle suites pass
277 tests, including large-tree low-descriptor-limit and interleaving cases.

Independent evidence is `REVIEW-EVIDENCE-194666.json`, produced by the new
claim-specific `reproduce-review-194666.py`. Whole harness time was 2.492985299
seconds, including the 2.485970124-second test subprocess (unittest reported
2.324 seconds) and historical/candidate race comparison. Scratch is retained at
`/tmp/w194457-review194666-3wdv5uot`. No earlier output was overwritten.

The second integrity traversal and its O(entries) in-memory fingerprints are
content-validation costs, not permission-only work or constant-time preparation.
This result verifies the reported correction, not general atomicity against
arbitrary concurrent filesystem writers. Existing lifecycle exclusion remains
required. Complete the identity/launch/mapping scope next; repeating the already
verified workspace slice is not a substitute for finishing that scope.

## 2026-09-17T13:12:36Z — shared command vectors verified; launch gate absent

Reviewer baton.codex claim 194747, author claim 194683. The execution vector now
requests the manager effective UID and configured workspace GID; custody requests
the same pair. Consent retains 65532:65532 and no supplementary workspace group.
This supersedes earlier statements that both execution vectors still use the
fixed pair, for this candidate only. Identity compatibility is not yet established.

**Confirmed:** `supported_identity_mapping` exists only as a definition/export
in production source, with no launch caller. Its direct unit tests do not enforce
early refusal by a real execution path. The current `worker_preflight` constructs
the adapter's static half but does not obtain a host-side identity observation.
Shared identity remains incomplete and deployment remains unapproved.

The implementer's selected execution pair is within the original owner authority;
exact UID/GID choices were delegated. Retaining the supplementary workspace group
is compatible with this selection, though redundant when the primary runtime GID
is already that group. This does not establish mapping correctness, private HOME
access, credential isolation or owner-only consumption by itself.

Independent workspace/OCI/custody/launch verification: 409 tests pass, 5.026
seconds reported by unittest, 5.196772167 seconds measured wall time. All seven
author-listed candidate hashes match. See `REVIEW-EVIDENCE-194747.json` and
`review-2026-09-17T13-12-36Z.md`. The real-engine lifecycle composition test was
read but not run. No live engine/provider or installed runtime was touched.

**Reported, not independently confirmed:** the author measured 56 pre-existing
declared-operand failures in test_dependencies.py. Preserve that report and its
scope limitation; it is not evidence of a clean complete suite or a reason to
weaken the unrelated checks. Existing reported stage-suite errors also remain
outside this review's independently reproduced results.

## 2026-09-17T13:22:50Z — observation helper has unsafe lifecycle/provenance

Reviewer baton.codex claim 194801, author claim 194767. The new observation
helper remains disconnected from production preflight. It must be corrected
before connection; passing direct helper tests is not acceptance.

**Confirmed with local simulated engines:**

- The fixed `<place>/.identity-probe` is recursively removed before the call
  establishes ownership. A sentinel from a previous attempt is deleted and the
  call still returns a successful observation. Parallel calls can also share
  this directory and the PID-derived container name.
- After a successful observation, a call with a different EnginePort and a
  different deployment directory returns the cached success without calling
  that engine at all. The global key names only docker/podman, image and UID/GID;
  it does not identify the actual engine connection, daemon/mapping state or
  filesystem. This is not verified deployment-bound reuse.
- A simulated runtime produces only a symlink to a pre-existing manager-owned
  file. `isfile` and `stat` follow it, and the helper returns a matching owner
  accepted by `supported_identity_mapping`. It has not proved ownership of a
  new runtime-created regular file.
- On a simulated client timeout, only `run` is issued; no engine removal,
  termination or inspection is attempted. `_engine_run` bounds the local client
  subprocess, not the daemon-side container. Actual daemon leakage was not run
  or observed in this review. `--rm` alone does not establish timeout/crash
  cleanup, and ignored directory-removal errors cannot establish clean success.

Evidence: `reproduce-review-194801.py` and `REVIEW-EVIDENCE-194801.json`.
All injected data and simulated engine effects were confined to
`/tmp/w194457-review194801-4nak5h6a`; that fixture remains for operator cleanup.
The new helper must use attempt-owned unique probe resources, authenticated
no-follow result measurement, conservative reuse and accountable cleanup.
Removing the cache is an acceptable implementation choice if sound invalidation
is otherwise unavailable; cache complexity is not an acceptance requirement.

Initial focused tests encountered 13 setup errors because the new fixture defaults
to `/var/tmp`, read-only in this managed reviewer environment. Using the existing
`BATON_V12_STACK_TEST_ROOT=/tmp` setting, all 257 workspace/OCI tests pass. This is
an environment adjustment, not a permission escalation or product/test edit.
The initial complete harness took 1.549867690 seconds; the configured rerun took
1.519481219 seconds (unittest 1.349 seconds). Both results are preserved separately.
The four author-listed hashes match. No real engine, provider or production state
was accessed. Review `review-2026-09-17T13-22-50Z.md` records required corrections.

## 2026-09-17T13:32:10Z — partial probe corrections; cleanup still unsafe

Reviewer baton.codex claim 194860, author claim 194830. The global cache is
removed; probe directory and default helper names are unique; the output is
opened no-follow and must be a single-link regular file. The fixture now uses
the supported configured/default temporary root. These explicitly supersede
the corresponding open defects from the preceding review for this candidate.
The claim that cleanup failures are handled is not yet established.

**Confirmed by deterministic simulation/local fixtures:**

- A successful probe followed by an engine `rm` document with status 1 still
  returns a matching identity. Only raised exceptions are handled; command
  failure status is discarded. The simulated helper remains present. A real
  already-absent helper is a separate legitimate case needing exact absence
  evidence, not permission to ignore all nonzero statuses.
- A caller-supplied helper name already belonging to another container causes
  `run` to fail with name conflict, then unconditional `rm --force` removes the
  unrelated modeled container. A generated name reduces collision probability
  but does not prove ownership of whatever currently has that name.
- `_remove_probe` checks lstat identity, then performs a fresh pathname lookup
  through rmtree. Replacing the directory in that interval deletes an unrelated
  sentinel and returns normally while the original owned directory remains under
  its moved name. A pre-check pin is not an identity-bound destructive operation.

`reproduce-review-194860.py` and `REVIEW-EVIDENCE-194860.json` preserve the positive
control and these failures. Fixture `/tmp/w194457-review194860-nr002cbz` remains
for operator cleanup. No real engine/container was started or deleted.
Independent workspace/OCI tests: 263 pass, unittest 1.383 seconds; test subprocess
1.557145182 seconds; whole harness including probes 1.558022363 seconds. Nested
times are included, not additive. The two author-listed candidate digests match.

The production mapping gate is still disconnected. Fix cleanup ownership and
result handling, then complete that gate, private HOME/cache, two-direction
restrictive access and written compatibility/update/recovery instructions. No
integration or deployment is approved. See `review-2026-09-17T13-32-10Z.md`.

## 2026-09-17T13:40:44Z — cleanup checks still permit false success

Reviewer baton.codex claim 194918; author claim 194882. The candidate now checks
rm status, inspects an invocation nonce before removal, and unlinks directory
contents through the original descriptor. Those are real advances, but the
claim that cleanup has been proved remains superseded by these reproductions:

- `_reclaim_probe` treats every nonzero inspect status as verified absence.
  A simulated daemon-connectivity failure (status 1) is accepted with no removal
  and no unresolved diagnostic, while the modeled probe still exists.
- Inspection checks only the nonce at a mutable name; removal still uses that
  name. Replacing the container after inspection causes removal of the unrelated
  replacement and a successful observation. Authenticate and remove the exact
  immutable engine object ID, not a re-resolved name.
- `_remove_probe` records a failed unlink in the global UNRESOLVED list but
  returns no failure outcome to its caller. An injected PermissionError leaves
  the probe file/directory behind while observe_runtime_identity returns an
  identity accepted by supported_identity_mapping.

The acceptance invariant is conjunctive: successful run, fresh valid observation,
verified cleanup of the exact engine object (or positive absence), and verified
cleanup of the owned filesystem resources. Any unknown or failure must prevent
acceptance and carry actionable resource identity to the caller. A diagnostic
list alone is not enforcement.

Evidence: `reproduce-review-194918.py`, `REVIEW-EVIDENCE-194918.json`; local fixture
`/tmp/w194457-review194918-vv9uifm_` retained. All engine effects were simulated.
Independent 266 workspace/OCI tests pass (unittest 1.382s, subprocess 1.551207630s,
whole harness 1.552358859s, inclusive). Both submitted hashes match. No real
engine, provider or production state was touched. See
`review-2026-09-17T13-40-44Z.md`; original preflight/HOME/access/recovery scope
remains unfinished and deployment remains unapproved.

## 2026-09-17T13:52:10Z — outcome fixes verified; exact ID and exception cleanup remain

Reviewer baton.codex claim 194975, author claim 194939. The previous review's
failed-listing and directory-cleanup outcome findings are corrected for this
candidate: listing errors refuse and directory cleanup returns an enforced
boolean. This explicitly supersedes those open defects, while preserving the
four-part acceptance invariant and the still-unfinished production wiring scope.

**Confirmed by deterministic simulation and code inspection:** the new listing
omits `--no-trunc`, so its formatted Docker ID is a prefix rather than full
immutable identity. Replacing the original modeled object with another full ID
sharing that prefix between inspection and removal deletes the replacement and
returns success. Docker's public formatter source and CLI reference corroborate
the default truncation; exact links and the simulation limits are in
`review-2026-09-17T13-52-10Z.md`. No actual engine collision is asserted.

**Confirmed by injected observation failure:** raising `OSError` from the
ownership read after modeled run success skips all engine settlement calls and
leaves no unresolved helper diagnostic. The code's `finally` covers only local
filesystem cleanup. Engine settlement must also run when observation fails.

Evidence: `reproduce-review-194975.py`, `REVIEW-EVIDENCE-194975.json`; local fixture
`/tmp/w194457-review194975-ysl2erp5` retained. Independent 270 workspace/OCI tests
pass, unittest 1.374s, subprocess 1.541447227s, whole harness 1.542521373s inclusive.
Both candidate digests match the author handoff. All engine effects were simulated;
no provider, production state, deployment or retry was exercised. Return for
these cleanup corrections and completion of the existing preflight/HOME/access/
compatibility/recovery scope. No additional owner permission gate is introduced.

## 2026-09-17T13:57:41Z — exact-ID and exception cleanup corrections verified

Reviewer baton.codex claim 195028, author claim 195007. Independent re-execution
of the preceding reproduction against the new candidate confirms both cleanup
findings corrected: full immutable ID removal preserves a replacement sharing
the old prefix and refuses the failed original removal; an ownership-read OSError
still triggers engine settlement while remaining the primary reported error.
The positive control succeeds and unavailable listing still refuses with a named
resource. This explicitly supersedes those two open findings for these bytes.

Independent workspace/OCI suites: 272 pass. Unittest 1.367s, subprocess
1.540086890s, whole harness 1.541173570s inclusive. Submitted product/test and
author-evidence hashes match. New `reproduce-review-195028.py` and
`REVIEW-EVIDENCE-195028.json` preserve the results without modifying earlier
evidence. Fixture `/tmp/w194457-review195028-9gvnicq4` remains for operator cleanup.
All engine effects are simulated; production remains untouched.

The original scope still requires production mapping-gate wiring and fixtures,
private HOME/cache, restrictive access both directions, compatibility conclusions
and written unexecuted update/recovery instructions. Source search confirms the
observer and mapping predicate have no production caller; worker_preflight still
contains only the deferred-wiring comment. Return to implementation to finish
that scope, preserving the verified corrections. No additional helper redesign
or owner approval gate is requested. Review `review-2026-09-17T13-57-41Z.md` is
partial correction verification, not integration or deployment approval.

## 2026-09-17T14:03:38Z — explicit activation and reported live-runner incident

Reviewer baton.codex claim 195068; author claim 195045, M195058 and return 195065.
The author reverted an attempted preflight wiring change and submitted unchanged
listed candidate bytes plus a proposed persistent mapping record.

**Confirmed:** effective_engine_run(None) selects a subprocess runner. Bootstrap,
staged and judgment composition call worker_preflight; that function already
documents configuration side effects. Workspace-group configuration itself runs
no engine. A deployment observation producer has not yet been implemented.

**Clarification/supersession:** the earlier reviewer proposal placing observation
at an exact worker_preflight line is superseded. Explicit deployment activation
may produce a validated mapping consumed before affected execution, without
probing during every composition. Exact implementation placement remains within
the owner's authorized scope. The author's proposal to persist numbers is not
accepted as sufficient proof: journal integrity establishes recorded history,
not current engine/mapping/filesystem continuity. Preserve the earlier requirement
to reject stale observations and identity drift. A startup-scoped capability is
an acceptable simpler direction; durable reuse needs provenance/invalidation and
must refuse when continuity is unknown. Pin the exact chosen flow before editing.

**Operational finding, author-reported:** a wiring test reached the live subprocess
path and was killed. Actual container creation is unknown; author-reported
subsequent listing/directory checks are not independent cleanup proof. The packet
does not include the cited traceback or exact command/PID/termination output.
Contain further deterministic tests with fake injection and an unintended-live-
runner guard. Preserve any existing incident evidence under new names; do not
repeat real engine execution to recover it. This finding is recorded before
continuing with that containment measure. No new engine authorization is granted.

The packet's approximate ten-minute run estimate cannot describe elapsed time
wholly inside the canonical 196-second claim. Append a clarification identifying
the episode or correcting the estimate; retain unknowns honestly. Historical
timing uncertainty is not a development gate or proof of resource cleanup.

See `review-2026-09-17T14-03-38Z.md` for code references, evidence hashes and the
bounded continuation. No tests were repeated on unchanged reviewed bytes; the
previous independent 272-test result remains applicable to that slice. Return
to implementation to complete activation/enforcement, HOME/cache, restrictive
access, compatibility and written recovery scope. No deployment approval.


## 2026-09-17 — owner corrects verification cadence and deployment scope

See OWNER-VERIFICATION-CADENCE-20260917.md for the confirmed instruction:
short reproduction/adjacent tests first; no repeated suite sweeps per correction.
743 checks across six suites must not be described as focused verification.
Required independent acceptance remains. The same record pins the previously
confirmed fresh timestamped deployment decision, explicitly superseding the
in-place upgrade/recovery instruction for the old failed first-Job instance.
Author/reviewer should carry these clarifications into the next owned PLAN update.


## 2026-09-17 — owner selects trusted configured UID/GID

OWNER-TRUSTED-IDENTITY-20260917.md is the current access-contract decision.
It explicitly supersedes prior automatic engine identity observation, startup
probe, persistent mapping-proof and probe-cleanup acceptance requirements.
Trust deliberately configured supported mappings, validate declared settings,
and report actual access failures directly. Preserve isolation and the bounded
shared-identity outcome; finish the complete path with short deterministic tests.
Earlier probe reviews remain history, not further implementation obligations.

## 2026-09-17T15:42:06Z — trusted-identity candidate: two remaining corrections

Reviewer baton.codex, claim 195685, author claim 195084. Review is under the
trusted-configuration owner ruling, not the abandoned automatic-probe design.
The complete-candidate claim is superseded by two independently reproduced gaps:

**Confirmed integrity regression:** replace an already checked regular file with
a symlink while opening the next sibling. The second `prove_line_integrity`
traversal skips the symlink before comparing its recorded fingerprint; the child
count is unchanged, so proof succeeds and the root is granted mode 02775. The
historical provisioning function refuses this same interleaving before grant,
leaving mode 0700. Stable control succeeds. Outside sentinel remains unchanged;
this proves a lost pre-grant invariant, not outside data access or general
atomicity against concurrent writers. Preserve no-follow/stable-symlink behavior
and bounded descriptors while rejecting the transition.

**Confirmed diagnostic gap:** a real unreadable mode-0000 entry in initial
integrity checking reports only `PermissionError (errno 13)` and no failing
operation or path. This precedes the improved establishment diagnostics in
`create_line`. Preserve actionable root/entry/operation context and errno under
the owner's trusted-configuration contract, without claiming a mapping cause.

All eight submitted hashes match. Independent targeted selection: 64 tests pass,
unittest 0.501s, measured subprocess 0.667390062s, whole harness 0.676169293s
inclusive. Evidence and all eleven candidate path hashes are in
`REVIEW-EVIDENCE-195685.json`; reproduction is `reproduce-review-195685.py`;
review is `review-2026-09-17T15-42-06Z.md`. Scratch
`/tmp/w194457-review195685-d0_v__uw` remains for operator cleanup. No live engine,
provider, production state or Git mutation. No source/test edits by the reviewer.
No integration/deployment approval; the fresh-instance decision remains after
acceptance. Prior automatic-observation and old-instance recovery requirements
stay superseded. Correct the two gaps with short reproductions and adjacent
tests rather than another general verification sweep.

## 2026-09-17T15:56:45Z — corrected candidate independently accepted

Reviewer baton.codex claim 195787, author claim 195725. Both preceding findings
are resolved for the exact eleven-path candidate bound by
`REVIEW-CANDIDATE-195787.json` (SHA256
`a82da7596fd37488dc4af34cc0c6dc28690a967f0208d6972e61df780f793c93`).
This explicitly supersedes their open status; prior evidence remains unchanged.

**Confirmed:** the original file-to-symlink interleaving refuses before grant
and retains root0700; unchanged control and stable symlinks pass. The real
unreadable-entry refusal names the operation, relative entry, line root and
EACCES, retaining materializing/ungranted state. All eleven submitted hashes
match; only the integrity function and its test file changed since review195685.

Independent 27 targeted tests pass, unittest0.231s, subprocess0.407571008s,
whole reproduction0.415965424s inclusive. Evidence `REVIEW-EVIDENCE-195787.json`
and `reproduce-review-195787.py`; unchanged launch/custody/consumption evidence
is reused. Full review `review-2026-09-17T15-56-45Z.md` enumerates all changed
test paths, scope and limitations. No empirical engine-mapping or clean-full-suite
claim. Automatic observation and old-instance recovery stay superseded.

Accepted for approver review of the prepared diff; Git ownership stays with
Slawomir. No deployment or production operation ran. Scratch
`/tmp/w194457-review195787-6rdp6_mk` retained. Reviewer edits are dossier-only.
