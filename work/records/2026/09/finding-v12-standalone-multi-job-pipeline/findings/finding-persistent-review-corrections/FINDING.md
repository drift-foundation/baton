# Persist v12 review checkpoints and correction lines

Ledger Work: W71918

Parent: `work/records/2026/09/finding-v12-standalone-multi-job-pipeline/`

Decision source: W62098.

## Confirmed scope

Keep one manager-custodied private development line for a Work across serial
implementation and independent-review assignments. Workers and reviewers are
disposable; the private workspace is not. Every review handoff freezes an
immutable, read-only checkpoint and binds the reviewer verdict and logs to that
exact checkpoint. A changes-requested verdict returns the same line at the
reviewed checkpoint to a writable implementer assignment, with exactly one
writer.

The correction path does not restage from the canonical repository, clone or
copy the candidate again, overlay an uncommitted retained tree, or require an
intermediate canonical commit. Only a final independently accepted checkpoint
becomes eligible for the integration queue.

This leaf owns review/correction stage composition and checkpoint custody. It
uses W71917's workspace/mount contract and W71875's persisted stage state. It
does not own pool selection or integration policy.

## Review-ahead scheduling clarification — 2026-09-04

The earlier scheduling text treated the source/workspace prerequisite as a
gate on the whole Work. That is superseded. The prerequisite gates
IMPLEMENTATION, because implementation must attach to the accepted persistent
workspace contract; it does not gate independent review of this record's
stage model, identities, acceptance boundary, or planned evidence.

Protocol 11 cannot express a stage-scoped dependency directly. For this
review-ahead pass, correct the live dependency so the reviewer can claim the
Work now. Before leaving review, the reviewer records the still-open
source/workspace provider as a dependency again and reroutes the now-unclaimed
Work to implementation. The coarse protocol-11 dependency then holds the
implementation offer, which is the boundary it was intended to protect, and
closing the provider releases that offer without operator pacing.

Review-ahead approves no implementation bytes and never assumes that an
unfinished provider will remain unchanged. At implementation start, revalidate
the reviewed contract against the accepted provider outcome; a material
change returns the affected portion for targeted review rather than silently
building against stale assumptions.

## Observed baseline — 2026-09-02

- Worker Manager output freeze and custody can retain an immutable result, and
  v12 authority can record a review receipt.
- The supervised dogfood path tears down a single implementation attempt and
  returns to v11 for review; no persistent manager stage reconnects a rejected
  checkpoint to the same private Work line.
- W62098 run2 proved why copied retained candidates and immediate deltas are
  insufficient, then superseded them with ordinary Git ancestry and a
  persistent private-line ruling.

## Review-ahead contract review — 2026-09-04

**Observed:** The current Job Manager has exactly one stage per `(job_id,
kind)`: `job_manager/schema.py` enforces `UNIQUE (job_id, kind)` and
`job_manager/documents.py:stage_id` derives the identity from those two facts.
Its append-only `episodes` are successive attempts to ADMIT that one stage,
not successive candidate revisions. `changes-requested` is deliberately a
terminal state for the current review leaf, and only an
`abandoned-after-restart` admission episode is replaceable. Reusing either a
stage or an episode as a correction round would erase this distinction and
silently broaden admission-retry policy.

**Observed:** The current Worker Manager workspace is private to an
ASSIGNMENT, not to a Work. `worker_manager/workspaces.py:assignment_workspace`
allocates its home from `assignment_id`, and
`worker_manager/intake.py:_settle_cleanup` calls
`workspaces.discard_execution_roots` when that attempt ends. Those ordinary
attempt roots therefore cannot also be the durable development line: the
first disposable runtime ending would delete the line it was meant to hand
on.

**Observed:** The current Worker Manager technical-review axis and Authority
review receipt each choose one terminal alternative from `accepted`,
`changes-requested`, and `rejected`. Authority requires passed verification,
but its review operation currently binds a proposal identity, receipt
identity, actor, and disposition. It does not by itself name a development
line, assignment generation, checkpoint revision, base/head pair, or reviewed
path set. W71918 must supply that binding rather than infer it later from a
mutable workspace or from the current attempt.

**Confirmed boundary:** W71918 adds a review-cycle owner ABOVE the existing
one-shot stages and disposable attempts. It does not reinterpret a Job Manager
admission episode as a candidate revision, and it does not extend an attempt's
cleanup authority over the persistent line. The generic manager owns durable
line/checkpoint custody and orchestration without running Git. A source/profile
adapter may materialize and identify a Git checkpoint, but the generic
contract carries only validated opaque checkpoint evidence and attachment
capabilities.

**Required identity model:**

- A `development_line_id` is stable for one Authority plus Work across all
  serial implementation and review assignments. It is distinct from Job,
  stage, offer, attempt, runtime, proposal, and receipt identities. Any
  globally durable spelling includes the Authority UUID; W83781's final
  identity helpers must be reused if they land before implementation.
- A monotonically allocated line revision names each frozen checkpoint. A
  checkpoint identity and digest bind the line, revision, source/base and
  candidate/head references, and the actual reviewed path-set digest. The
  immutable checkpoint remains resolvable after a later revision exists.
- Each writable attachment binds the line revision it starts from and the
  current implementation assignment generation. Each read-only review
  attachment binds one exact checkpoint and its independent review assignment
  generation. Disposable attempts may change without changing either the
  line or checkpoint identity.
- A verdict operation binds Authority, Work, review assignment generation,
  checkpoint identity/digest and revision, base/head, reviewed path-set
  digest, reviewer actor, and disposition. Reusing an operation or receipt
  identity with any changed operand refuses rather than replaying a verdict
  over different bytes.

**Required transition model:**

1. Implementation holds the line's sole durable writer grant. Completing the
   turn revokes that grant and freezes revision `n` before review can attach.
2. Review receives checkpoint `n` read-only and a separate writable output
   root for findings and logs. Neither the producing runtime nor a mutable
   pathname is evidence for the reviewed bytes.
3. `accepted` makes exactly checkpoint `n` eligible for the separately owned
   integration stage. `changes-requested` keeps checkpoint `n` immutable and
   returns the SAME line, based at `n`, under one fresh implementation
   assignment generation; its next freeze creates revision `n+1`. `rejected`
   grants neither integration eligibility nor an implicit writer.
4. Advancing the line never transfers an earlier verdict to the later
   checkpoint. Integration must consume the accepted checkpoint named by the
   verdict, not "whatever is current" when the consumer runs.

**Required crash and concurrency semantics:** Freeze, writer revoke/grant,
review attachment, verdict recording, correction reopen, and integration
eligibility are journalled idempotent acts with all durable operands in their
signatures. A crash between any filesystem custody act and its projection
must resume or refuse without exposing a mutable checkpoint, two writers, an
unreviewed integration candidate, or a second revision for one replayed act.
The writer slot is manager-owned durable state; container/process liveness is
only an observation and cannot itself grant or release the slot.

**Implementation prerequisite:** W71917 remains unfinished. At implementation
start, re-read its accepted FINDING, PLAN, production paths, tests, and review.
Reuse its final Work-scoped workspace/mount/custody owner rather than adding a
parallel allocator. A material change to workspace identity, mount
capabilities, cleanup ownership, quota/re-adoption, source attachment, or
result layout returns the affected W71918 contract for targeted review before
production edits continue.

**Proposed patch boundary:** The implementation is expected to extend the
review-cycle/stage projection under `v12/python/src/baton_v12/job_manager/`,
the provider-backed line/checkpoint custody and attachment boundary under
`v12/python/src/baton_v12/worker_manager/`, and the corresponding frozen
documents/schemas only where the new identities cross a trust boundary.
Exact symbols and paths remain contingent on W71917's accepted shape. Pool
selection, Git command execution in the generic manager, approval policy, and
integration execution remain out of scope.

**Open, not blocking this review:** The final provider may choose the concrete
checkpoint primitive and storage layout. That choice must mechanically keep a
review checkpoint immutable while the same development line later becomes
writable; host mode bits alone are insufficient if both roles can still reach
one mutable tree. The provider revalidation resolves this concrete mechanism,
not the identity and transition requirements above.

## Long-running assignment checkpoint ruling — 2026-09-04

V12 assignments are not bounded by one model or transport turn. A useful run
may last hours and cross any number of provider turns. Ending one such turn
after a successful checkpoint is not assignment failure, claim orphaning, or
implicit release. Protocol 11 retains its existing turn-settlement and exact-
release recovery behavior; this ruling adds no v11 mechanism.

`checkpoint` is a first-class immutable handoff artifact, not a lifecycle
status. Freezing one atomically records the assignment generation,
development line and revision, workspace/candidate identity, completed
progress, durable logs and outputs, and current verification evidence. An
exact replay is idempotent; operand changes under the same operation or
checkpoint identity refuse. The ordinary implementation-to-review handoff
revokes the writer, freezes the checkpoint, and names it as the review input.
The same handoff boundary may deliberately reassign continuation to another
vendor, model, profile, or fresh session after the old writer is fenced.

A provider turn ending during a long run is not itself a handoff and creates
no new Work status. The assignment remains `working`; the manager persists
ordinary progress and schedules another provider turn against the same
workspace and preferred session. A run may cross any number of those internal
turns before it freezes a checkpoint for review, approval, or reassignment.

Review and approval always name the frozen checkpoint they observed. A
decision may resume the preferred worker, assign a different worker, request
another correction, or make the checkpoint integration-eligible. None of
those choices requires cloning/restaging the candidate, committing it to the
canonical repository, discarding prior logs, or inventing a new Work. Every
checkpoint remains audit-resolvable after later revisions exist.

## Turn and process ownership ruling — 2026-09-05

The Worker Manager, not one ACP/app-server turn, owns the assignment attempt,
its container, and every supervised process. A provider turn is a replaceable
communication exchange inside that attempt. Its return, timeout, transport
loss, or provider failure cannot by itself release the assignment, declare the
Job complete, or destroy work that the manager still records as running.

The manager obtains the durable claim before it launches the provider or
admits any tool execution. Every later command, progress event, result, and
checkpoint is fenced by the current assignment generation. A resumed session
that remembers an earlier claim cannot act under a released or superseded
generation; context affinity never overrides canonical ownership.

Agent communication and observation use durable files under the attempt's
manager-owned roots. Input, control messages, progress, logs, output, and
terminal evidence do not depend on a live stdin/stdout pipe. The manager may
tail those files, but neither the manager process nor one provider transport
must remain alive for the container to preserve them.

A provider response may end while supervised tools continue. In that case the
attempt remains `working`, the manager continues to own and observe those
processes, and a later provider turn may resume after their durable outcome is
available. Completion, checkpoint handoff, or writer release refuses while a
tracked child remains live. Untracked background work is a worker-contract
violation, not a reason to pretend the attempt finished.

That containment is not permission for ordinary agent behavior. An agent must
await every command it starts, especially tests, before voluntarily ending its
turn. Internal multi-turn continuation exists for provider/context boundaries,
not as a way to abandon a running tool and report progress early. Agent
compliance is nevertheless never the safety proof: transport loss, provider
failure, or a misbehaving model can still return with children alive, and the
supervisor must contain that case mechanically.

On restart the manager reconciles its durable attempt state with containers
identified by exact manager-owned labels and republishes idempotent state
events. It does not infer completion from its own prior death or blindly adopt
an unrelated process. A stopped or wedged runtime leaves its output available
but untrusted until shutdown is proved; policy or an operator then chooses
review, retry, reassignment, or discard.

## Accepted-provider revalidation — 2026-09-05

**Observed:** W71917 did not add a Work-scoped workspace owner. Its
`workspaces.assignment_workspace` and `adopted_assignment_workspace` allocate
and re-open roots under an assignment identity. Its ordinary settlement calls
`discard_execution_roots`, which deletes that assignment's `inputs` and
`workspace`; `discard_workspace` owns removal of the entire assignment home.
The accepted provider therefore supplies reusable storage, adoption and mount
PRIMITIVES, not the durable line allocator assumed by the earlier review.

**Superseded prerequisite:** The earlier instruction to "reuse [W71917's]
final Work-scoped workspace/mount/custody owner rather than adding a parallel
allocator" is superseded because no such owner exists. The confirmed boundary
above already assigns that missing ownership to W71918. W71918 must add one
Authority-and-Work-namespaced review-cycle line/checkpoint owner ABOVE and
separate from assignment homes, while composing W71917's accepted
`WorkspaceStorage`, group, disk-backed-capacity, source-boundary and mount
identity primitives. This is the one W71918 owner, not a competing second
owner for assignment roots.

**Required cleanup boundary:** The durable line and every checkpoint use a
reserved manager namespace which attempt/assignment identity derivation cannot
address. Ordinary attempt cleanup remains limited to the disposable roots it
already owns. It cannot delete, rename, retarget or adopt the reserved line
namespace. The review-cycle owner alone performs explicit terminal,
abandonment and recovery cleanup after retained checkpoint/verdict obligations
are satisfied. Allocation and cleanup tests must prove containment and refuse
an assignment identity that collides with or traverses into the reserved
namespace.

**Observed:** W71917's capacity proof compares the filesystem's currently
available bytes with a declared launch requirement. It deliberately does not
reserve capacity and does not enforce a live byte or entry ceiling while a
workspace grows. Its `attempts.pin_boundary_identity` and
`boundary_identity_of` also pin one attempt's source/workspace objects; they do
not establish a durable identity across correction assignments. W91072 is the
separately parked limitation for live workspace ceilings.

**Open owner ruling — growth:** W71918 cannot claim that W71917 bounds the
accumulated persistent line. Either (A) this milestone explicitly accepts an
admission-only posture, repeats the accepted free-capacity proof before EVERY
writable attachment/correction round, monitors and cleans retained storage,
and states that no live line-size/entry ceiling exists until W91072; or (B)
W71918 is blocked on a live-ceiling mechanism. Option A preserves the already
accepted W71917 exposure but is not a quota and does not prove that an admitted
line cannot exhaust its filesystem. The owner must choose and record one
posture before implementation.

**Observed:** W71917's `source_boundary.boundary_mounts` can attach a nominated
directory read-only to one runtime and separately attach writable output. Its
composition/adoption and per-attempt pins prove object identity. They do not
freeze the underlying directory after that same development line is later
attached writable to a correction assignment. A read-only bind protects the
reviewer from writing; it does not protect an earlier review from later writes
through another attachment.

**Superseded open point:** The earlier statement that provider revalidation
would resolve the concrete checkpoint mechanism is superseded: accepted
W71917 supplies no immutable checkpoint primitive. A checkpoint cannot be the
mutable line directory merely mounted read-only. The mutable line and every
immutable checkpoint are distinct objects, as W62098 requires, and advancing
the line must leave all earlier checkpoint bytes and identities unchanged.

**Open owner ruling — checkpoint primitive:** Before implementation, choose
and record the profile-specific freeze/materialization contract that satisfies
that distinction without another source clone, candidate restage or whole-tree
role-transition copy. A Git-backed profile may use immutable commit/object
identity in the persistent private repository and share its object store, but
the exact reviewed tree still needs a mechanically immutable read-only
attachment or inspection capability. The generic manager carries and verifies
opaque checkpoint evidence/capabilities; it does not run Git or infer
immutability from a path or mode bit. Non-Git profiles need their own equally
explicit snapshot capability rather than silently inheriting Git semantics.

**Confirmed unchanged provider surface:** W71917's source/result layout,
read-only source and writable result attachment, object-identity verification,
disk-backed storage proof and assignment-root adoption remain suitable
building blocks. The affected W71918 contract is limited to durable line
allocation/cleanup, cross-assignment identity, accumulated-growth posture and
checkpoint immutability. No W71918 production bytes were written before this
targeted review.

## Operator ruling — first-slice growth posture — 2026-09-05

The first slice accepts the already exposed admission-only capacity posture.
Before every writable attachment, including every correction round, the
review-cycle owner repeats the accepted disk-backed free-capacity proof against
the line's current storage. Failure refuses the new writer attachment while
preserving the line and retained checkpoints for inspection or explicit
cleanup. The check is never described as a reservation, quota, or proof that a
running worker cannot exhaust the filesystem.

Live byte and entry ceilings remain separately scheduled hardening. Until they
exist, status exposes accumulated line storage and the operator may explicitly
retain or clean a terminal line. This accepted limitation must not expand the
review-cycle leaf into live filesystem policing or block the first useful
implementation/review/correction path.

## Operator ruling — Git checkpoint primitive — 2026-09-05

The first implemented checkpoint profile is Git. A checkpoint is the exact
commit and tree object identity frozen in the persistent private repository,
retained by a manager-owned checkpoint reference and bound with the line,
revision, base, head, and reviewed path-set digest. It is never the mutable
development-line pathname, its current mode bits, or an archive/copy of the
candidate tree. The Git profile owns Git operations and validation; the
generic manager carries only validated opaque checkpoint evidence and
capabilities.

Freeze requires a quiescent sole writer, a clean candidate at the exact commit,
and durable revocation of the writer before review attachment. For the current
revision, the profile may expose the same private line read-only without a
clone or role-transition copy only while its checkout is proved to match the
checkpoint and no writer grant exists. Verdict recording revalidates that
identity. A correction writer is granted only after the review attachment ends
and starts from the reviewed commit; later line writes cannot change the
retained commit/tree objects or transfer the earlier verdict.

Earlier checkpoints remain addressable by their recorded object identities and
manager-owned references after the line advances. Profile-owned inspection can
read them from the shared object store without making the generic manager run
Git or infer immutability from a path. A non-Git profile fails closed until it
supplies its own equivalent immutable freeze and read capability; this slice
does not invent a generic whole-tree copy fallback.

## Superseding operator ruling — runtime-provided storage — 2026-09-05

The earlier requirement to repeat a free-capacity proof before every writable
attachment is superseded. W71918 adds no predictive free-space gate,
reservation, quota, byte counter, entry counter, or storage controller. Disk
capacity is a property of the supplied runtime environment just as CPU and
memory are; it may change or auto-resize after any observation, so a
point-in-time probe is not an execution guarantee.

The manager uses the supplied storage and records ordinary allocation, mount,
write, and `ENOSPC` failures against the affected attempt. Such a failure does
not authorize deletion of the durable line or retained checkpoints, and it
does not affect unrelated workers. An adapter may still report a concrete
backend refusal when creating or mounting storage, but W71918 does not predict
capacity or refuse work based on an advisory free-space reading. Existing
source/workspace-provider behavior is not expanded or redesigned by this
leaf; no new line-level capacity check is composed over it.

## Acceptance

- The manager creates or adopts one durable development-line identity per
  Work and permits exactly one writable assignment to attach at a time.
- Review handoff freezes an immutable checkpoint without copying the whole
  candidate tree merely to change roles; the review container receives it
  read-only and writes findings/logs separately.
- The reviewer is independent from the producing runtime and its verdict binds
  Work, assignment generation, checkpoint digest/revision, base/head, and the
  actual reviewed path set.
- Changes requested returns the same private line at that checkpoint to an
  implementer. A later checkpoint remains distinct and the earlier one stays
  resolvable for audit.
- Ten synthetic correction rounds run with fresh disposable containers and no
  second source clone, candidate-tree restage/copy, concurrent writer, or
  canonical target mutation.
- Restart at implementation-to-review and review-to-correction boundaries
  resumes the owed stage idempotently and preserves every checkpoint/verdict.
- A multi-hour assignment crosses multiple provider turns while remaining
  `working`, without false failure, release, or a new checkpoint status. Its
  ordinary handoff can freeze a checkpoint for review/approval or transfer the
  same line to another model after fencing the prior writer.
- Provider/tool launch is impossible before the durable claim; stale session
  generations cannot execute. Provider-turn return does not kill or complete
  manager-owned work, and checkpoint/completion refuses while a supervised
  child remains live.
- A conforming agent waits for every tool and test it started before returning.
  A deliberately abandoned background task is reported as contract failure;
  the same quiescence fence still contains an accidental or provider-caused
  early return.
- Manager restart reconciles exact labeled containers and durable file-based
  progress, logs, outputs, and terminal evidence without depending on a
  surviving stdin/stdout connection.
- Only the final accepted checkpoint becomes integration-eligible;
  intermediate/rejected checkpoints cannot enter the integration queue.

## Test-change authority

This Work authorizes adding tests and editing existing tests under
`v12/python/tests/` for development-line custody, checkpoint freeze/attachment,
review verdict binding, changes-requested reuse, one-writer enforcement,
restart, and integration eligibility. Any deletion or weakened expectation
must be explicit and independently reviewed; unrelated tests are excluded.

## Independent implementation review — changes requested 2026-09-05

Review `review-2026-09-05T13-03-27Z.md` binds immutable proposal
`sha256:f464588c1bc914672f4b6aef4d4a563fec171ee665cefa463c28da43463d72f3`
and records three integration blockers. Package digests, custody,
reconstruction, 444 focused tests, and four inventory gates pass, but those
tests do not prove the lifecycle this Work requires.

First, revoking a writer changes database state but does not revoke the
already-minted roots/source boundary or an existing writable bind; the retained
capability remains adoptable after checkpoint freeze. Second, a review attempt
with no runtime, result, verification, frozen output, findings, or logs can
record `accepted` and create integration eligibility. Third, raw storage path
operands let the lifecycle create and mount a line under caller-selected store
B even when the manager durably configured store A.

The retained `repro-2026-09-05T12-58-34Z.py` demonstrates all three against a
fresh reconstruction. Mechanically fence writer assignment/runtime authority
before freeze, require and bind quiescent frozen review results and logs before
verdict/eligibility, and derive every line custody/mount act from the manager's
configured workspace store. Then add the two new suites to the serialized
parallel registry after W71877 releases it and publish a new exact proposal.

## Implementation response to independent review — 2026-09-05

The three review findings are implemented in replacement proposal
`sha256:b8b0af5e2baf6a8f1cfde67568842d272b52e94f925ee2fc45cd6784677cbc02`.
The writer's database grant is revoked only after the exact runtime is
positively quiescent with a terminal disposition; its existing manager-owned
finalization decision then fences the Authority generation before profile
freeze. Lifecycle roots carry a revocable-grant requirement that cannot be
dropped by choosing the ordinary boundary composer, and the live grant is
checked during both adoption and final mount derivation.

A review verdict now requires a completed, positively quiescent attempt with
frozen output, passed verification, and separately retained `findings` and
`logs` artifacts. The complete frozen-result summary (including the retained
manifest digest) and exact committed Authority fence are redundant durable
verdict fields and are revalidated before integration eligibility is returned.
Every line creation and writer/reviewer mount resolves the committed
`workspace_storage` configuration; the three public lifecycle operations no
longer accept a raw storage path.

The serialized registry remains deliberately unresolved: W71877 still owns
`v12/python/tools/parallel_test.py`, so adding the two suites there before its
accepted proposal integrates would create an unreviewed overlap. This does not
weaken the corrected lifecycle proposal; it preserves the explicit follow-up
recorded by review and PLAN item 10.

## Independent correction review — changes requested 2026-09-05

Review `review-2026-09-05T13-53-35Z.md` binds replacement proposal
`sha256:b8b0af5e2baf6a8f1cfde67568842d272b52e94f925ee2fc45cd6784677cbc02`.
The three prior lifecycle blockers are substantively corrected: writer freeze
now includes quiescence, live-grant revocation and the exact Authority fence;
verdict and eligibility bind completed frozen review evidence; and all line
custody derives from committed workspace storage.

The proposal is still refused. Its package root and timestamp directory remain
writable `0775`; its reduced manifest omits the immutable-proposal schema,
record-path set, known registry follow-up, digest recipe, and verification
record; and the standard four boundary-inventory gates fail 21 subtests on a
fresh reconstruction. Nineteen failures are a verdict-probe fixture that never
reaches the declared decoder, and two are duplicate ownership declarations for
the new Authority ports. Correct those package/test defects, wait for W71877 to
release the shared serialized registry, register both suites, and reseal one
complete exact proposal.

## Implementation response to correction review — 2026-09-05

The verdict-probe fixture now carries the accepted line and ended attachment
that its accepted verdict and eligibility rows assert, so every declared
verdict decoder is reached. The redundant local Authority-port capability
checks and their probes are removed; `AuthorityPort.__init__` remains the one
existing owner of every port operand, while the same quiescent finalization
operation performs both writer and reviewer fences. All four exact unfiltered
inventory gates pass.

W71877 closed satisfying and committed the shared registry baseline at
`947a11de13a7de0d7abb17056c1e0170aa7a4145`. Both W71918 suites are now
registered as isolated parallel modules on top of that base. The final package
uses the complete `baton.immutable-proposal/1` manifest, records the resolved
registry status and verification, and freezes the package root, timestamp,
proposal, and all descendant directories to `0555` with evidence files `0444`.

## Final independent implementation review — approved 2026-09-05

Review `review-2026-09-05T14-18-29Z.md` approves exactly final proposal
`sha256:46fdcf325d6cd1ba277cf5441275e08a3c46ff2e02dc367dbb74823c0a606453`
against base `947a11de13a7de0d7abb17056c1e0170aa7a4145`: sixteen paths, no
record paths, and ordinary non-executable `0644` target modes. All package,
base, member, patch and custody checks pass; fresh reconstruction is exact.

The 445-test focused suite, four unfiltered inventory gates and 36 registry
tests pass. The registered parallel phase collects and passes both new suites.
Its six failures are the same six failure identities reproduced independently
from a clean archive of the committed base, so W71918 adds no broad-suite
regression. The final inventory fixture and port-owner corrections are within
PLAN item 11's explicit test authority and weaken no lifecycle assertion.

Only the reviewed immutable proposal may enter integration. Any changed byte,
mode, path set, base, custody, provenance or target preflight result requires a
new review.

## 2026-09-07 — follow-up verification composition planning under W110772

**Confirmed follow-up history, not a rewrite of the accepted W71918 proposal:**
W110772's real public-custody proof reaches record_verdict with output sealed
and verification none. Its review2026-09-07T16-11-31Z independently confirms
that first-verdict blocker. Owner111612 assigned baton.codex claim111614 to
trace this record's semantics and propose a bounded correction while preserving
passed verification; this does not reopen or mutate this Work's ledger state.

The passed-verification requirement added after the unrun-reviewer finding is
still required. Its earlier mechanical-verification contract is owned by
`baton:work/records/2026/08/finding-v12-isolated-agent-workers/FINDING.md`
and worker-control SPEC section8.6. It concerns genuine required-suite results
for an exact candidate, distinct from review disposition, report parsing and
artifact custody. The W71918 tests establish the axis but do not supply a
production producer. Authority.verify records an authorized observation; a
separate clean verifier must actually produce and retain the detailed evidence.

**Proposed follow-up:** adopt the full retained verification manifest together
with its attributable Authority receipt, bind that evidence to the exact
proposal/checkpoint/review attempt and result in the manager journal, then
project passed. Accept legitimate sealed output only with cross-bound accepted
custody. Historical eligibility after ordinary cleanup must use the committed
verdict, verification, fence, positive cleanup and retained-result evidence;
it must not require a destroyed runtime to regress to quiescent or allow an
unrun reviewer to create its first verdict. Writer quiescence is unchanged.

Exact proposed interfaces, seven fixed consumer paths plus bounded operand
inventory, missing clean-verifier provider, later integration-receipt reuse,
and focused acceptance are in
`baton:work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-standalone-stage-composition/findings/finding-review-verdict-channel/CORRECTION-PLAN.md`.
Ops disposition and exact producer scope precede implementation. No verification
rule, production byte, prior test assertion or historic sign-off is superseded
by this planning entry. W110772 owns follow-up execution and its remaining gates.

## 2026-09-07 — milestone verification supersession, owner M111752

**Confirmed owner ruling; follow-up recorded by baton.codex claim111746:**
W71830 now uses ordinary implementer tests plus independent review, with additional
reviewer checks as needed. No separate clean-verifier agent, stage or service is
required. This explicitly supersedes the previous follow-up entry's mandatory
clean producer and reviewer-attempt passed-axis prerequisite for this milestone.
The accepted W71918 proposal and its original reviews remain unchanged history.

W110772's FIRST-PROOF-PLAN.md at
`baton:work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-standalone-stage-composition/findings/finding-review-verdict-channel/`
proposes the exact correction: actual ordinary test evidence drives admission,
no fabricated reviewer-axis passed, cross-bound sealed first verdict and exact
historical custody after cleanup. The existing negative test's reviewer-axis
expectation is explicitly scheduled for owner disposition; failed/unrun required
test refusal moves to actual admission and is not deleted as a requirement.
Isolation, independent completed review, findings/logs, exact checkpoint/fence
and retained evidence remain. The separate clean-verifier architecture is
deferred. Ops assigns the bounded source/test proposal before implementation.
W71918's ledger remains terminal; W110772 owns this follow-up and its gates.
