# Progress

Not started. The child waits for the persistent manager and source/workspace
contracts and must preserve one writer over the manager-custodied Work line.

## 2026-09-05 — baton.claude — the W71917 revalidation gate (PLAN item 2)

PLAN item 2 is the mandatory entry gate and it is the whole of this turn: read
W71917's ACCEPTED outcome against what this record assumed, name the exact
provider symbols to reuse, and stop before production edits if any of the six
named axes materially differs.

**Three do.** No production bytes were written.

### What W71917 actually delivered

W71917 closed satisfying. Its final review approves exactly the 30 paths at
aggregate digest
`sha256:15291e091b85e5674dd074913eedd9a100e667dc1665fabd0a17af99c32c0a89`
against base `8f809a9`. Read fresh from the current tree rather than from that
record's prose:

- `worker_manager/source_boundary.py` — `nominate_source`, `NominatedSource`,
  `workspace_capacity`, `WorkspaceCapacity`, `compose_source_boundary`,
  `adopt_source_boundary`, `boundary_mounts`, `SourceBoundary`,
  `check_disk_backed`, `filesystem_of`, `source_mountpoint`,
  `source_consumption`, `declared_profile`, and the constants
  `SOURCE_TARGET` `/input/source`, `WORKSPACE_TARGET` `/output`,
  `SCRATCH_MOUNTS`, `MIN_WORKSPACE_BYTES`, `MAX_WORKSPACE_BYTES`,
  `CONSUMPTION_KEY` `baton.source-boundary/1`.
- `worker_manager/workspaces.py` — `assignment_workspace`,
  `adopted_assignment_workspace`, `discard_execution_roots`,
  `discard_workspace`, `configure_workspace_storage`,
  `configured_workspace_storage`, `prove_workspace_group`, `mount_table`,
  `mount_points`.
- `worker_manager/attempts.py` — `pin_boundary_identity`,
  `boundary_identity_of`.
- `worker_manager/oci.py` — `OciAdapter(source_delivery=…)` and the private
  `_source_mount`, which binds a boundary to the exact assignment roots a
  start composes.
- `worker_manager/schema.py` — `SCHEMA_VERSION = 16`, `attempts.source_device`,
  `source_inode`, `workspace_device`, `workspace_inode`.
- `baton_v12/source_profiles/` — `checkout_plan`, `PROFILES`
  (`generic`, `git`), `check_declared_base`, consumed by the worker and never
  by the manager.

### Axis by axis

**1. Workspace identity — MATERIALLY DIFFERENT.** This record's implementation
prerequisite says to "reuse its final Work-scoped workspace/mount/custody
owner rather than adding a parallel allocator." **W71917 delivered no
Work-scoped owner.** `assignment_workspace(workspace_group, storage,
assignment_id)` still allocates from the assignment identity, and its docstring
still says "TWO ROOTS, private to one assignment". Nothing in the accepted
30-path candidate introduces a development line, a Work-scoped root, or any
identity that outlives an attempt.

This record ALREADY OBSERVED that shape on 2026-09-02 as the pre-W71917
baseline and expected the provider to change it. It did not. So the
prerequisite sentence and this record's own "Confirmed boundary" — which says
W71918 owns durable line/checkpoint custody — now point in opposite
directions, and one of them has to give.

**2. Cleanup ownership — MATERIALLY DIFFERENT, and it is the same fact.**
`intake.py:_settle_cleanup` still calls `discard_execution_roots(storage,
assignment_id)`, which removes `inputs` and `workspace`. An ordinary attempt
ending therefore still deletes the tree a development line would have to be.
W71917 changed cleanup substantially — the mount-safe top-down walk — but not
its SCOPE.

**3. Quota / re-adoption — MATERIALLY DIFFERENT.** The quota this record's
revalidation axis names no longer exists. W71917's approved ruling superseded
it: `workspace_capacity` is a launch-time declared-capacity preflight, proving
only that the filesystem currently has the declared bytes free; `max_entries`
is removed from the closed configuration member set; there is no live byte or
entry ceiling, and a worker can fill the backing filesystem after admission.
Live enforcement is parked as W91072.

That is a weaker contract than a per-assignment workspace made it look, and it
matters MORE for a durable line than for a disposable attempt: a line that
survives ten correction rounds accumulates ten rounds of build output with
nothing bounding it, and the one admission-time proof happened before round
one.

Re-adoption itself is stronger than this record assumed and is good news:
`adopted_assignment_workspace` plus `adopt_source_boundary(boundary, roots,
pinned=…)` re-prove BOTH roots as objects — device and inode — against
`boundary_identity_of`, and `boundary_mounts` re-proves them again immediately
before the runtime binds are derived. A replaced source or workspace refuses at
every boundary the manager owns.

**4. The pinned identity is per-ATTEMPT, which the identity model must
resolve.** `pin_boundary_identity(store, *, attempt_id, source, workspace)`
writes four columns on the `attempts` row and is write-once under the store's
write lock: an exact repeat replays, a differing pair refuses. Across a
development line each correction round is a NEW attempt with a new row, so the
accepted mechanism deliberately re-pins per attempt and has no notion of
continuity between them. A line whose workspace object must be the same across
rounds needs that continuity stated somewhere; today nothing carries it.

**5. Mount and custody capabilities — UNCHANGED, and they answer this record's
one open question.** The runtime receives exactly two assignment binds:
`(source, /input/source, read-only)` and `(workspace, /output, writable)`, with
`/tmp` and `/dev/shm` as small non-executable tmpfs scratch. Read-only is not a
parameter on the source half.

That is a MECHANICAL answer to "Open, not blocking this review": a frozen
checkpoint delivered to a review attempt as its NOMINATED SOURCE is read-only
by mount rather than by mode bits, and the review attempt's own writable
`/output` is the separate findings-and-logs root this record requires.
`compose_source_boundary` refuses a source only where it contains or is
contained by THIS assignment's own two roots, so a manager-owned checkpoint
directory elsewhere under storage is nominatable — verified against the current
rule rather than assumed.

**6. Source attachment and result layout — UNCHANGED.** The manager still runs
no Git, walks/copies/hashes nothing, and carries the profile word as opaque
text; the worker performs its own checkout into `/output` through
`source_profiles.checkout_plan` and verifies its declared base. Collection is
still by DECLARATION — `output._compare_declared` refuses an undeclared path —
so a checkout and a candidate beside the declared proposal are workspace
material that goes away with the workspace.

### Disposition: stopped at the gate, as PLAN item 2 requires

Three of the six axes differ materially, so no production edit was made. The
three questions this returns for targeted review, each with the shape of the
answer it needs rather than a preference dressed as a finding:

1. **Who allocates the durable line?** W71917 leaves no Work-scoped allocator,
   so either this Work adds one — which the prerequisite sentence forbids in
   the same breath that its own Confirmed boundary requires it — or the
   prerequisite sentence is superseded to say the line allocator is W71918's,
   composed from W71917's proved mount/custody primitives rather than from a
   second copy of them.
2. **What keeps the line outside attempt cleanup?** `discard_execution_roots`
   deletes `inputs` and `workspace` at every ordinary ending. A line living
   under a root that call can reach is a line the first correction round
   destroys. Either cleanup's scope is narrowed with its own review, or the
   line lives under a storage area that call provably cannot name — and which
   one is a custody-ownership decision, not an implementation detail.
3. **What bounds a durable line's growth?** The accepted contract has no live
   ceiling and says so out loud. For one attempt that is an accepted MVP
   exposure; for a line that outlives ten rounds it is a different exposure
   with the same mechanism, and this record should say which it accepts before
   code assumes either.

Nothing else in the reviewed contract is contradicted: the identity model, the
transition model, the crash/concurrency semantics, the turn/process ownership
ruling and the evidence matrix all stand against the accepted provider, and
the checkpoint-immutability mechanism now has a concrete answer in axis 5.

## 2026-09-05T12:13:46Z — baton.tuner — implementation candidate awaiting review

Claimed W71918 only after the approver routed the explicitly authorized
implementation and test scope to `baton.tuner`. Re-read the complete dossier,
W71917 provider surface, and thread. The owner correction at message 93224
arrived after this claim; the candidate now follows it: persistent lines use
runtime-provided disk-backed storage with no predictive free-space reading,
reservation, quota, or live counter.

Implemented Worker Manager schema 17 and a journalled review-cycle owner:

- one deterministic Authority-and-Work line under the reserved
  `.baton-review-lines/` namespace, pinned by device and inode outside every
  disposable assignment home; its immutable creation operands are durable
  before profile materialization and bind crash recovery;
- generation-fenced writer grants, durable progress, revoke-before-freeze,
  immutable monotonic checkpoints, independent review attachments, exact
  evidence-bound verdicts, and accepted-checkpoint-only integration
  eligibility;
- correction rounds reuse the same checkout while all prior checkpoints and
  operation results remain replayable after the line advances; each fresh
  correction grant revalidates that checkout against its named checkpoint;
- direct writer and read-only review mount composition with separately
  writable review output, repeated object proof at composition/adoption/mount,
  and no candidate-tree role copy;
- a Git checkpoint profile outside the standalone worker `source_profiles`
  package. It owns closed Git argument vectors and retains exact commit/tree,
  base/head, reviewed path set/digest, and manager reference evidence.

The accepted no-capacity ruling is tested with `os.statvfs` made fatal across
ten correction rounds and review-line composition/adoption. Ordinary W71917
assignment capacity behavior is unchanged. A real local-Git regression proves
an earlier retained ref remains resolvable after the mutable line advances.
Additional coverage exercises ten fresh correction attempts, exact historical
replay, restart at both lifecycle boundaries, sole-writer concurrency,
three-axis reviewer independence, stale generations, live-child completion
refusal, Authority/Work isolation, rejected/intermediate ineligibility,
assignment cleanup preservation, and reserved-namespace traversal refusal.

Verification on the current tree:

- 438 focused Worker Manager, source boundary, secrets/dependency, public text
  sweep, standalone worker import, checkpoint-profile and review-cycle tests:
  all pass, 3 existing skips;
- the four W71918 boundary inventory ownership/probe/witness gates: all pass;
- real Git checkpoint test: pass;
- `git diff --check` over the affected v12 and dossier paths: no output.

The full discovery gate was attempted. Its real-container classes refuse
because this non-interactive deployment cannot reach `/var/run/docker.sock`.
The current shared tree also contains W71877's active concurrent scheduler
candidate, whose known boundary-inventory and registry state accounts for the
remaining broad-gate failures. The full run initially found two W71918 defects
(standalone `source_profiles` import isolation and direct-probe foreign-key
fixtures); both are corrected and their focused regressions pass. Registration
of `test_checkpoint_profiles` and `test_review_cycles` in
`v12/python/tools/parallel_test.py` remains coordinated with W71877, which
currently owns and independently reviews that already-modified shared file.

## 2026-09-05T12:30:49Z — baton.tuner — final integrity hardening

Closed the final relational-evidence gaps found during self-review. Review
attachment now requires the checkpoint's retained writer to belong to the
same line, and verdict recording requires the attachment, frozen checkpoint,
current line, and transactional reread to agree. Integration eligibility now
requires the line's current accepted state plus an exact accepted verdict row
whose Authority, Work, revision, checkpoint digest, base/head/tree, and path
set all match the frozen checkpoint. Added corruption regressions for a review
attachment retargeted to another line and eligibility backed by a non-accepted
verdict.

The combined focused gate now runs 442 tests successfully with 3 existing
skips. The four selected boundary inventory ownership/probe/witness gates pass
after reconciling the new adopted-row declarations; the W71918-specific
unowned, double-owned, stale-owner, and missing-probe filters are empty.
`py_compile` for every changed Python module/test and repository-wide
`git diff --check` both pass. The broader inventory remains affected by the
concurrent W71877 candidate and the full real-container gate remains blocked
by this managed deployment's unavailable Docker socket.

## 2026-09-05T12:38:55Z — baton.tuner — sealed main proposal

The final time-of-use pass added profile validation immediately before a
review runtime receives the current line read-only; attachment-time validation
alone left a window in which the mutable checkout could change before mount.
A negative regression now refuses that mismatch. Line creation also refuses
source/line containment before allocating its reserved namespace, preserving
the accepted source/output anti-aliasing rule.

The final current-tree focused gate runs 444 tests successfully with 3 existing
skips; the selected boundary gates, Python compilation, and `git diff --check`
remain clean. Reconstructed the main candidate from Git base
`6532e6ff2f966ea6c6612326f3b0c5450026c63b` and repeated the focused and
boundary gates there successfully.

Sealed the 15 main production, documentation, and test paths as immutable
proposal `sha256:f464588c1bc914672f4b6aef4d4a563fec171ee665cefa463c28da43463d72f3`
at `/tmp/w71918-main/2026-09-05T12-37-42Z/proposal`; patch digest is
`sha256:e641c431b75f08dba22ca88ed7f9b267cd9406081950061be3cf86eb5b953415`
and candidate-manifest digest is
`sha256:798c2ae822be27fb3bfd90a70322da6eb492ad90578d7f449618653149810f86`.
All package directories from `/tmp/w71918-main` down are non-symlink `0555`
directories, every evidence member is a non-symlink regular `0444` file, all
digests recompute, and all base members match the named Git base. Dossier
history is deliberately excluded so append-only review can continue.

The only unscheduled byte is the two-module addition to
`v12/python/tools/parallel_test.py`. W71877's independently reviewed proposal
still owns that shared path and is queued overdue for operator approval and
integration. Editing it now would invalidate W71877's exact proposal and
create the target overlap the integration contract forbids. The sealed main
proposal therefore excludes the registry and names this follow-up explicitly;
the registry must be appended and reviewed after W71877 releases the path.

## 2026-09-05T13:40:00Z — baton.tuner — review corrections and replacement proposal

Reclaimed W71918 after independent review rejected proposal `f464588c...`.
Implemented all three requested corrections without changing the retained
proposal or review evidence:

- checkpoint preparation now requires the writer attempt's exact attached
  runtime to be positively quiescent with a terminal disposition, atomically
  revokes the database writer grant, commits/replays the existing
  `finalize_quiescent_assignment` decision, and fences the exact Authority
  generation before the checkpoint profile can freeze;
- runtime-storage roots now carry a manager-only revocable grant requirement.
  Ordinary boundary composition refuses those roots, runtime composition
  refuses ungranted roots, and adoption plus final mount derivation recheck the
  live grant. A boundary minted before revocation therefore refuses after it;
- verdict recording now requires the reviewer runtime to be quiescent and
  completed, output frozen, verification passed, and separate frozen
  `findings` and `logs` artifacts. The verdict durably binds the complete
  frozen-result summary/manifest digest and committed Authority fence;
  integration revalidates the checkpoint, verdict, attachment, attempt,
  result, and both digests;
- `create_line`, `writer_boundary`, and `review_boundary` no longer accept a
  storage operand. Every custody act resolves the Worker Manager's committed
  `workspace_storage` answer at use time.

The review-cycle regression now drives the retained reproduction's three
negative seams: an already-minted writer boundary refuses adoption and mounts
after freeze (including recomposition through either public composer), an
unrun/unverified review or one missing findings/logs cannot fence or record a
verdict, and caller-selected storage is absent from the public API and cannot
mint line custody. It also proves a completed review's previously minted
read-only boundary is revoked after verdict.

Verification on the shared tree:

- 260 focused review-cycle, checkpoint-profile, source-boundary, dependency,
  secret, store, and public-text tests pass with 3 existing skips;
- 625 additional attempts/workspace/OCI unit assertions pass; the remaining
  real lifecycle class stops at its required Docker prerequisite because this
  managed deployment cannot access `/var/run/docker.sock` (one existing skip);
- the W71918 inventory slice covers 160 receiving entries with zero unowned,
  double-owned, stale-stated-owner, missing-probe, or extra-probe entries, and
  its focused stated-owner witness passes;
- all 14 changed Python files compile, and repository `git diff --check` is
  empty.

Sealed the corrected 15-path replacement proposal at
`/tmp/w71918-correction/2026-09-05T13-40-00Z/proposal`. Proposal digest is
`sha256:b8b0af5e2baf6a8f1cfde67568842d272b52e94f925ee2fc45cd6784677cbc02`,
patch digest is
`sha256:033d1d68420ea7f02c97a9781ac20b817dd85e7e683a5bbb843f5b6cb8041f81`,
and candidate-manifest digest is
`sha256:b606119a7e90a89a4993f0beba47e5ffb258d9ed0f0af547c738abc7743e19d8`.
All 46 package entries are non-symlinks with `0444` files and `0555`
directories; all candidate/base bytes, Git-base bytes, sizes, modes, and
digests recompute.

W71877 remains queued overdue at `baton.ops` (snapshot 93942), so its accepted
proposal still owns `v12/python/tools/parallel_test.py`. The corrected proposal
again excludes that path; registration remains the explicit post-W71877
follow-up and is not misreported as complete.

## 2026-09-05T14:02:44Z — baton.tuner — second review corrections; registry gate remains

Reclaimed W71918 after the independent correction review accepted the three
lifecycle fixes but rejected proposal `b8b0af5e...` on package custody,
manifest completeness, and the exhaustive inventory gate. Preserved the
accepted lifecycle behavior and corrected the inventory model:

- the coherent verdict-probe fixture now represents the accepted line and
  ended review attachment that its already-present accepted verdict and
  integration-eligibility rows assert, so all adopted verdict decoders are
  reached rather than short-circuited by an earlier lifecycle precondition;
- removed the two redundant local `AuthorityPort.cancel` capability checks and
  their probes. `AuthorityPort.__init__` is the existing single owner of every
  `port` operand and `finalize_quiescent_assignment` still performs the exact
  fence. This resolves the two duplicate-owner declarations without weakening
  any valid writer or reviewer fence.

The exact four unfiltered inventory gates now pass. The focused checkpoint,
review-cycle, store, workspace, dependency, source-boundary, secret, text-sweep,
and Claude-agent suite passes 445 tests with 3 existing skips.

W71877 has integrated its reviewed registry byte but remains open and queued
for `baton.ops` approval, so it has not released
`v12/python/tools/parallel_test.py`. W71918 is explicitly blocked on W71877
rather than overlapping that path or sealing another knowingly incomplete
proposal. When the dependency closes, append the two suite entries, rerun the
gates, and seal one complete `baton.immutable-proposal/1` package with immutable
custody from the package root downward.

## 2026-09-05T14:12:47Z — baton.tuner — complete final proposal sealed

W71877 closed satisfying and committed its reviewed serialized-registry byte
at base `947a11de13a7de0d7abb17056c1e0170aa7a4145`. Appended
`tests.manager.test_checkpoint_profiles` and
`tests.manager.test_review_cycles` to the parallel registry with their exact
isolation rationale; no W71877 path remains under active proposal custody.

Current-tree verification passes: 445 focused tests with 3 existing skips, the
four exact unfiltered inventory gates, 36 parallel-runner registry tests,
Python compilation, and `git diff --check`. The actual registered parallel
phase collects both new modules and each passes. Its whole-base result remains
3712 tests with the same 6 failures and 3 skips reproduced from a clean archive
of committed base `947a11d`: one stale authority catalogue enumeration plus
five broader exhaustive boundary-inventory baseline assertions. W71918 adds no
failure to that baseline.

Sealed the final 16-path proposal at
`/tmp/w71918-final/2026-09-05T14-11-22Z/proposal`:

- proposal digest
  `sha256:46fdcf325d6cd1ba277cf5441275e08a3c46ff2e02dc367dbb74823c0a606453`;
- patch digest
  `sha256:c19f71987533cf90524ac843a7d2889b020b506dab0fa6bde3e4ba1b4529cd3b`;
- candidate-manifest digest
  `sha256:d0b3dd780700783e3d52279eecf8e670cb064d770505c2282a9a4356dd4a6dd7`.

The complete `baton.immutable-proposal/1` manifest binds 16 candidate paths,
the empty record-path set, resolved registry status, digest recipe, and actual
verification. Patch reconstruction from the named base matches all 16
candidate members byte-for-byte; 11 base members, 16 candidate members, patch,
candidate manifest, and proposal digest all recompute. The package has 49
descendant entries. Every file is a non-symlink regular `0444` file and every
directory from `/tmp/w71918-final` downward is a non-symlink `0555` directory.
The reconstructed focused suite passes 445 tests with 3 existing skips when
given the deployment's required disk-backed test root; its four inventory and
36 registry gates also pass.
