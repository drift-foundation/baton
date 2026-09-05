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
