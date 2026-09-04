# Drive the production runtime through its worker-entry conversation

Follow-up to W76207.

Ledger Work: W81857.

Discovered while launching W71917 as the first ordinary self-hosted v12 Job.

## Observed — 2026-09-03

The persistent Job Manager successfully recorded `sub-w71917-selfhost-1`,
issued and settled one offer, committed one claim, composed the assignment
roots, and launched Docker runtime
`c4c12927cd8857d1860ac157baf7aee9bb69bb03adc01613fdd4bfbddc08e75b`.
Its canonical stage projection then reported `running`.

The runtime was not performing the Work. `docker top` showed only PID 1,
`python3 /opt/baton/dogfood_entry.py`, at zero CPU; there was no Claude child,
no output activity, and no container log. The worker-entry program reads
framed requests from stdin and deliberately waits when none arrive.

Code inspection confirms that `tools.single_worker:factory` composes and
starts the interactive runtime but never calls
`worker_manager.worker_entry.converse`. The existing transport and real-engine
conversation proof are present, and the supervised dogfood deployment calls
them, but the production Job-manager composition does not. W76207's statement
that the launch seam was sufficient to carry W71917 is therefore narrower
than actual Work execution: it bootstraps a live runtime only.

## Confirmed defect

A production stage is projected as `running` after the container starts even
though no production component sends its `describe` and `work` operations.
The runtime can remain healthy and idle forever, so elapsed time or process
health cannot distinguish this state from useful execution.

## Direction

Add one production-owned, restart-safe post-start conversation act. It opens
the existing worker-entry transport against the exact journalled runtime,
sends `describe` then `work` with durable attempt-derived operation identities,
and records enough canonical state to prevent duplicate provider turns across
manager restart. A correlated answer, worker fault, transport loss, and
process death remain distinct outcomes. The result must feed the existing
output freeze/intake and runtime-ending owners rather than inventing Job-store
shadow state.

Do not mark a stage as actively working merely because its container was
started. Status must distinguish a started/waiting runtime from a conversation
that is actually in progress or has answered.

## Temporary W71917 stopgap

After this defect is on the ledger, the operator may drive the already-started
W71917 runtime once through the existing public worker-entry transport to keep
the vertical slice moving. That manual act is evidence and a stopgap, not the
fix. It must use the exact runtime and attempt identities, retain the complete
protocol outcome, and must not be described as autonomous Job-manager
execution. Raw provider stderr is not durable evidence because it may contain
credentials; retain its byte count and the structured protocol result instead.

## Acceptance

- A production-submitted implementation stage reaches a real provider turn
  without a human opening its channel.
- Restart before open, during the conversation, and after the correlated
  answer cannot silently duplicate or lose the turn.
- Status distinguishes runtime start, active conversation, answered, faulted,
  and lost states without interpreting silence as progress.
- A successful answer proceeds into the existing output and ending pipeline;
  failures remain inspectable and do not occupy unrelated capacity.
- Focused real-container evidence proves that Claude is spawned and output
  changes while the manager, not an operator command, owns the conversation.

## Test-change authority

This Work authorizes adding tests and editing existing tests under
`v12/python/tests/` for production conversation composition, restart,
correlation, status, output handoff, and failure isolation. Deleting or
weakening an existing expectation requires explicit independent review.

## Reviewer revalidation — 2026-09-04

### Observed — the retained production attempt is started, not working

The retained W71917 attempt is still a clean reproduction. Read-only Job
status reports implementation stage `running`, attempt
`attempt-1851504c0486e885c0d71be5f9b73e09c1352b4b11c9e7a5e97e904dc71ec76e`,
and runtime
`c4c12927cd8857d1860ac157baf7aee9bb69bb03adc01613fdd4bfbddc08e75b` with
runtime axis `running`. Engine inspection reports the container healthy, but
its only process is idle PID 1, `python3 /opt/baton/dogfood_entry.py`. The
attempt workspace has no frozen output or `output.json`.

This is not a stale display. `job_manager.projection._observed_state` maps an
attached runtime identity directly to the stage-specific running word.
`job_manager.manager._launch` asks the deployment only while the stage is
`claimed`; after `tools.single_worker._SingleWorker.start` attaches the
runtime, no later sweep owns a post-start act.

### Confirmed — the missing composition

`tools.single_worker.operations_from` supplies only
`start_runtime=worker.start`. `_SingleWorker._prepared` reconstructs delivery
capabilities and calls `request_runtime_start` or `reconcile_runtime`, then
returns. It does not retain a channel capability and does not call
`worker_manager.worker_entry.converse`.

The transport already has the required correlation semantics within one exec
session. `worker_entry.converse` composes the exact engine/runtime exec vector,
sends each caller-owned operation id once, requires correlated answers, and
returns the distinct `answered`, `faulted`, or `lost` ending with every answer
completed before the ending. `tools.dogfood_operator._after_start` is the one
existing deployment that composes `describe` then `work` and then drives the
quiescence, output, intake, retention, Authority pass, and cleanup owners.

The Job Manager deliberately owns none of those facts. Its store persists only
submission, stage/episode intent, and receipts for `admit` and `claim`.
Canonical runtime, activity, output, and failure observations come from the
Worker Manager through `delegation.ManagerOperations.observe`. Conversation
state belongs on that same canonical side; a Job-store conversation receipt or
column would violate W71875's no-shadow-state ruling.

### Confirmed — operation ids do not fence a manager restart

The statement that a caller-owned worker-entry operation id is
effectively-once is currently bounded to one invocation of the in-container
worker. `baton_worker.serve` keeps its `spent` set in process memory. A new
`docker exec` starts another process with an empty set, and the worker's
completion publication uses `os.replace`, so an existing `output.json` is not
a replay fence.

`evidence/repro-cross-session-replay.py` runs two independent worker-entry
processes against the same launched session, the same writable output, and the
same `describe:attempt-1` / `work:attempt-1` operation identities. Both
conversations answer and the shared provider is called twice:

```json
{"answered": [["describe", "work"], ["describe", "work"]], "endings": ["answered", "answered"], "work_calls": 2}
```

Therefore deterministic operation ids are necessary for correlation but are
not sufficient for restart safety. The canonical manager must durably grant
dispatch before the external channel is opened, and only the transaction that
created that grant may call `converse`. A replay or competing manager that
finds the grant must observe it and must not open a second exec session.

### Confirmed — exactly-once completion cannot be inferred after process loss

There is an unavoidable external-boundary window between committing the
dispatch grant and opening/sending on the exec channel. There is another
between the provider's answer and the manager recording it. The current
channel has no durable exec identity, reconnect operation, or correlated
result mailbox. A restarted manager therefore cannot distinguish “committed
before open”, “provider still running”, and “provider answered but the result
was lost”. Automatically sending again would duplicate a provider turn in at
least one of those cases.

The safe contract is at-most-once dispatch with explicit uncertainty: a
committed, unsettled dispatch survives restart, is shown as recovery-required,
and is never sent again. It may become `lost` only after a named recovery act
has positive evidence that the old exec/provider activity cannot still settle,
or under an explicitly accepted route policy that fences and abandons the
attempt. This satisfies “not silently lost”; it must not be described as
exactly-once delivery or automatic continuation.

The existing W44716 `abandon_attempt` composite is the owner for a failed or
lost started attempt after policy decides to end it. It records the exact
attempt/assignment/runtime/reason, fences at the Authority, proves runtime
absence, retains untrusted output, tears down deliveries, and releases the
lane. It deliberately does not fabricate a worker disposition, frozen output,
or intake. This Work must reuse it rather than create another failure ending.

### Confirmed — the successful ending has a fixed existing order

For an answered `work`, the existing public owners require this order:

1. positively quiesce and reconcile the exact runtime;
2. record the worker's returned disposition;
3. freeze the declared output for that disposition;
4. collect it and record the intake receipt;
5. decide every artifact's retention under the manifest's retained
   `retention_policy_digest`;
6. end the exact Authority assignment (the current supervised composition
   uses an effectively-once pass to a configured review Route); and only then
7. authorize runtime cleanup from the intake receipt and the retention
   decisions.

`authorize_cleanup` refuses while the assignment is live, so cleanup before
the Authority ending is not an implementation option. Conversely, ending the
assignment before intake can quarantine the result if the collection races
that ending. The pass therefore follows intake/retention and precedes cleanup.
The production implementation may factor the proven dogfood ordering, but it
must not copy its independent Git/tree verification: checkpoint and review
verification belong to W71918.

### Confirmed — existing session/interrogation rows are not this turn

`worker_manager.sessions` records the separately ruled provider-session axis,
and its own contract explicitly excludes turns, deadlines, outcomes, event
normalization, and provider binding. `worker_manager.interrogation` records
operator `probe`/`inquire` requests against one such provider session; an
inquiry is not the implementation Work operation and publishes its answer to
Baton. Reusing either row as the worker-entry `describe`/`work` dispatch would
silently change W6627's protocol. This production turn needs its own bounded
Worker Manager record.

## Proposed implementation contract

This section is decision support until the two ending-policy choices below are
accepted. The implementation must revalidate it against the current tree.

### Canonical conversation record

Add one Worker Manager conversation row per runtime attempt, with a request
operation journalled through `ControlStore.transact`. Bind the exact attempt,
fixed assignment, attached runtime id, launched session, fixed program, ordered
operations (`describe`, `work`), caller-owned per-operation ids, and configured
deadline. The row carries a closed state and only bounded safe evidence:

- `dispatching`: the grant committed; the external call may or may not have
  crossed;
- `answered`: both correlated operations answered and the `work` answer
  yielded one valid Worker Manager disposition;
- `faulted`: a correlated worker refusal/fault ended the conversation; and
- `lost`: the channel/process ended without the required correlated result.

An unsettled `dispatching` row observed by another incarnation is reported as
`recovery-required`; it does not authorize a second call. Record the answer
names, disposition, safe reason category, terminal process status, and stderr
byte count. Do not persist raw stderr, provider recap, or arbitrary answer
text, and run the durable-secret walk over every persisted diagnostic.

The request function returns whether this caller committed the fresh grant.
Only `true` reaches `worker_entry.converse`; replay returns the existing view.
Terminal settlement compares the exact request binding and changes the row
once under the write lock. A second, different settlement refuses. Deterministic
worker operation ids remain useful correlation labels, but the manager row is
the cross-process dispatch fence.

### Level-triggered Job-manager composition

Extend `job_manager.delegation.ManagerOperations` with injected deployment
capabilities for the post-start conversation and its ending, and add the
conversation public reader to `observation_of`. The Job store records no
conversation receipt. `manager.sweep` reacquires canonical state after launch,
then:

- asks conversation only for an attached, healthy attempt with no frozen
  output and no conversation row;
- asks ending for a terminal conversation whose output/cleanup owner still
  reports work owed; and
- catches a stage-local refusal/outcome so the next stage is still processed.

`tools.single_worker` supplies the real streaming subprocess channel, rebuilds
the exact attempt adapter from durable delivery state on every pass, and owns
the success/failure composition. It must add the Authority `pass_work`
capability rather than reach through the restricted session wrapper.

Status becomes a new version. The stage projection must not map “runtime id is
present” directly to active work: report a started/waiting state before the
dispatch grant, the stage-specific active word only while dispatch is owned,
an ending/handoff state after an answer but before frozen output, `completed`
from the existing frozen completed disposition, and `exceptional` for
faulted/lost or failed ending. Include the canonical conversation view beside
the runtime and output; absence is `not-requested`, not an inferred failure.

### Patch boundary

The expected production boundary is:

- `v12/python/src/baton_v12/worker_manager/`: schema/version, document
  constructors, one new conversation module/public exports, and no Job rows;
- `v12/python/src/baton_v12/job_manager/`: delegation observation/capability,
  level-triggered post-start/ending passes, and versioned truthful status;
- `v12/python/tools/single_worker.py`: configuration ownership, channel,
  exact runtime reconstruction, conversation, success/failure ending, and
  restricted Authority pass;
- `v12/python/DEPLOYMENT.md`: the new closed configuration/status contract;
  and
- focused additive/authorized tests under `v12/python/tests/`, plus the
  exhaustive parallel-test registry only if a new test module is added.

Do not change the worker protocol merely to make its process-local replay set
look durable. Do not add Job-store lifecycle columns, implement pool selection
(W71877), persistent checkpoints/correction policy (W71918), or integration
policy (W71878).

### Required regression matrix

- A fresh attached runtime is reported started/waiting; one sweep grants and
  opens exactly one `describe`/`work` conversation.
- Two managers racing the same attempt produce one dispatch grant and one
  channel call.
- Restart before the grant performs once; restart after the grant but before
  settlement performs zero additional provider calls and reports
  recovery-required.
- Restart after a recorded answer resumes only the owed output/ending steps;
  it never reopens the channel.
- Correlation mismatch, worker fault, channel-open loss, mid-frame loss,
  nonzero process exit, invalid/missing disposition, and timeout remain
  distinguishable and persist no raw stderr/credential material.
- Answered `completed`, `unable`, `plan-rejected`, and `cancelled` dispositions
  retain their canonical meanings; no manager fabricates one on failure.
- Success proves quiescence, freeze, intake, retention, exact-generation
  Authority ending, cleanup, and replay of every committed substep in order.
- Fault/loss uses only the accepted W44716 abandonment policy and releases the
  runtime lane; an unrelated stage is still visited in the same sweep.
- Status schema compatibility is explicit, including canonical-unavailable,
  absent conversation, dispatching, recovery-required, answered, faulted,
  lost, and post-answer ending states.
- A manager-owned real-container gate observes a provider child/output change
  without an operator opening the channel. The retained W71917 runtime can be
  used only as the already-recorded manual stopgap, not as proof of automation.

The focused baseline before implementation is green: 124 existing
`tests.manager.test_worker_entry` and `tests.tools.test_single_worker` cases
pass.

## Open decisions requiring approval

1. **Unsettled dispatch recovery.** Recommended: at-most-once/fail-closed. A
   restarted manager reports `recovery-required` and never automatically
   resends. Moving it to `lost` and invoking W44716 abandonment requires
   positive exec/runtime evidence or an explicit operator/route-policy act.
   The alternative is a larger worker/channel protocol with a durable result
   mailbox and reconnect identity; the current transport cannot honestly
   promise automatic continuation.
2. **Production success/failure ending policy.** Recommended for this final
   single-worker bootstrap: extend deployment schema `/3` with a bounded
   conversation deadline, `review_route`, and retention disposition; on
   successful intake retain the candidate, effectively-once pass the exact
   assignment to that Route, then clean up. Interpret the submitted
   `report-and-hold` terminal policy as authority to invoke W44716 abandonment
   for fault/loss while retaining its evidence. This ends the runtime without
   implementing W71918's checkpoint/correction state machine. If
   `report-and-hold` is intended to keep the live assignment/runtime instead,
   the acceptance that failures release unrelated capacity needs an explicit
   exception.

## Confirmed supersession — 2026-09-03 — file-only production exchange

The production-conversation direction, proposed conversation record, patch
boundary, regression matrix, and open decisions above are **superseded** where
they make a manager-owned stdin/stdout channel the authoritative Work path.
Slawomir ruled that an outer Job Manager's lifetime must not be coupled to the
container's lifetime. A manager restart must not destroy the only reader of a
provider response, make a healthy container unknowable, or require replaying
an uncertain pipe write.

Production manager-to-worker commands and worker-to-manager receipts, state
changes, and terminal outcomes use only durable files in one per-attempt
mounted exchange. Each producer publishes a closed JSON document atomically
under a stable operation identity in its own write namespace; repeat
observation is idempotent and neither side rewrites the other side's files.
The container's long-lived entry process consumes those commands, launches
the provider, and publishes its receipts and outcomes independently of the
manager process. Provider logs go directly to the attempt's mounted
`result/logs/`, and deliverables remain under `result/output/`.

After restart, the manager reconstructs the attempt by rereading the exchange
and result files and observing the exact container. It does not resend a
command merely because its former process lost a pipe, and it does not stop a
container merely because the manager restarted. The same durable operation
identity is visible on the request, receipt, state, and terminal response, so
an uncertain in-memory interval is not an uncertain assignment.

`worker_entry.converse` remains useful as a bounded diagnostic, test, and
dogfood transport. Production does not use it as its command or completion
authority. stdout and stderr may remain advisory observability streams, but a
missing reader cannot lose protocol state.

The manager may follow the durable exchange, event, and log files—equivalent
to `tail -f`, polling, or a filesystem notification—for low-latency status and
operator UX. That follower is only an optimization: if it disappears, the
files remain authoritative, and a restarted manager rescans from canonical
operation or sequence identity and catches up without losing an event.

W81857 now owns the smallest complete file path: publish one production
`describe`/`work` command sequence, let the existing container execute it,
publish a correlated terminal result, and let a restarted manager observe and
continue the successful output/ending path. Broader failure automation,
status polish, pooling, review checkpoints, and integration policy remain
separate hardening or downstream Work and must not delay this vertical slice.

## Reviewer revalidation of the file exchange — 2026-09-04

The supersession above is implementable in the current topology, with the
following boundaries made explicit. These are the implementation handoff; the
pipe-owned proposal and its open decisions remain superseded.

### Confirmed — the exchange must be a distinct delivery

The current attempt home has two container mounts: manager-frozen `inputs` and
group-writable `workspace`. The worker sees them as `/input` and `/output`.
Neither can safely hold both directions of the new control path:

- `inputs` and its parent are frozen before runtime start, so the manager
  cannot publish a later command there; and
- a command below `workspace` would also be reachable through the worker's
  writable `/output` mount. A read-only alias mounted elsewhere would not
  protect it: the worker could still rename or replace the same host entry
  through `/output`.

Add one attempt-private exchange delivery outside both assignment roots. It is
manager-created before runtime start and bound into the container at fixed
contract paths. Its parent is not writable by the worker. Under it:

- the manager owns a command directory, mounted read-only in the container;
  and
- the worker owns an event directory, mounted writable and read by the
  manager as untrusted input.

The delivery should live with, or be lifecycle-bound to, the existing launch
delivery: both are non-secret control material fixed before start, both belong
to the exact attempt/session, and both may be removed only after positive
runtime absence. Extending the launch delivery root is the smallest current
fit. `launch.adopt` must prove the static document, expected directory shape,
modes, and exact attempt/session on restart; `OciAdapter` must accept only the
typed delivery and compose only the fixed targets. Cleanup must remove dynamic
worker entries with a no-follow, descriptor-relative walk rather than widening
the current flat `launch.discard` loop.

The writable event namespace cannot be treated as authority merely because it
is durable. The provider runs under the same container identity and can reach
the container's mounts. Every worker-written document is therefore untrusted:
the manager bounds and no-follow opens it, closes its member set, checks its
session/attempt/operation identities and digest chain against the
manager-authored command, and adopts only facts the existing output/runtime
owners can independently verify. A terminal claim never substitutes for
validating `/output/output.json`, observing the exact runtime, or applying the
existing freeze/intake gates.

### Confirmed — one sequence, one durable dispatch fence

This bootstrap needs one command sequence per attempt, not a general queue.
The manager atomically publishes one closed document containing the exact
attempt, launched session, sequence identity, and the ordered operations
`describe` then `work`, each with its stable attempt-derived operation id. The
final filename is derived from the sequence identity rather than supplied as a
path. Publication requires exclusive/no-follow staging, a complete bounded
canonical JSON write, file `fsync`, rename within the directory, and directory
`fsync`; readers ignore staging names.

The long-lived PID 1 scans the fixed command directory. Before it dispatches
anything, it atomically publishes a receipt bound to the command digest. That
receipt is the durable replay fence: rescanning the directory or observing the
same command again never starts another provider turn. It then publishes
closed state events for the operations it actually reaches and one terminal
document with the same sequence/operation identities and one of
`answered`, `faulted`, or `lost`. The terminal document carries only bounded
protocol facts: completed operation names, safe fault code/class, worker
disposition when answered, and the completion-manifest digest. It carries no
recap, prompt, source excerpt, tool input/output, provider stdout/stderr, or
arbitrary diagnostic prose.

A worker process that finds its receipt without a terminal result must not
dispatch again. It reports the incomplete sequence if it can do so without
claiming an observation it lacks; otherwise the manager combines the durable
receipt with exact runtime observation and reports the sequence incomplete or
lost. In either case the provider call is not repeated.

### Confirmed — launch versioning selects the transport

The present image always enters the stdin framing loop, and its launch
document is the closed four-member `baton.worker-launch/1`. The file exchange
cannot be smuggled in through path discovery or an environment flag. Give the
production launch a new closed launch-document version that explicitly selects
`baton.worker-exchange/1`; its worker uses the fixed mounted directories.
Launch `/1` remains the explicitly allowed diagnostic/test transport used by
`worker_entry.converse`, not a production fallback.

The image recipes already copy `baton_worker.py`, so no second worker program
or provider-specific serve loop is needed. `dogfood_entry.py` continues to
inject `ClaudeAgent`; `baton_worker.main` selects the transport from the
validated launch document and passes the same agent to one shared operation
handler. The file path must reuse `handle`, input/assignment validation,
output measurement, and atomic `publish_completion`, not fork those rules.

Because the retained W71917 container contains the old worker bytes and has no
exchange mounts, it cannot satisfy the new acceptance. Do not inject code or
open an authoritative exec channel into it. The real-container gate requires a
new image candidate/digest and a fresh attempt whose input manifest and runtime
configuration bind that digest. The retained container remains only the defect
reproduction and the separately permitted manual stopgap.

### Confirmed — durable logs stay credential-safe

The supersession's phrase “provider logs go directly to `result/logs/`” is
**clarified and narrowed** by the earlier approved W61599/W43972/W39357
security decisions. `result/logs/` is not yet an implemented manager
capability, and raw provider/native/stdout/stderr bytes are credential-capable.
W81857 does not create that sink or persist those bytes.

For this slice the event directory is the durable log, and it contains only
the closed credential-safe receipt, state, and terminal documents described
above. Existing monotonic activity count/time may remain advisory. Broader
manager-minted safe-progress logs and their read/follow UI remain W61599.
Deliverables and `output.json` remain under the existing attempt `/output`
contract; the exchange terminal references the validated manifest digest
rather than moving, copying, or duplicating output under a new `result/output`
tree.

### Confirmed — manager composition is level-triggered and non-blocking

The Job Manager continues to own only when an act is owed. Extend its
deployment seam with file-exchange publication/observation, not a pipe handle
and not a Job-store receipt:

1. after launch, a sweep with an attached healthy runtime and no command asks
   the deployment to publish the one sequence and returns;
2. every later sweep rescans the exchange and exact runtime, deriving waiting,
   accepted/running, answered, faulted, lost, or incomplete without depending
   on a watcher cursor; and
3. an answered terminal with a matching completion manifest drives only the
   already-ruled successful quiescence, disposition, freeze, intake, and
   ending operations. Each substep remains replayable by its existing owner.

A filesystem watcher or tailer may reduce latency but holds no cursor whose
loss changes state. The next full scan is authoritative. Known fault/loss is
reported and contained to the stage; automatic abandonment/retry policy is not
added here. Pool scheduling remains W71877 and checkpoint/review correction
remains W71918.

No Worker Manager SQLite conversation table is required: the approved file
exchange is the durable request/receipt/outcome record. The Job store gains no
conversation column or receipt. `ManagerOperations.observe` (or an equally
closed injected deployment read) projects the exchange beside the existing
canonical runtime/activity/output facts, and status moves to a new schema that
distinguishes started/waiting, accepted/working, answered/ending, faulted,
lost/incomplete, and frozen terminal output. Runtime identity alone is no
longer rendered as active work.

### Revalidated implementation boundary

Expected production paths are bounded to:

- `v12/worker/baton_worker.py` for the versioned file serve loop and shared
  dispatch/publish logic; the image recipes need change only if their existing
  copy/entrypoint assertions require it;
- `v12/python/src/baton_v12/worker_manager/` for one exchange delivery module,
  launch delivery/version integration, fixed OCI mounts, strict file readers,
  and public projections—without a new lifecycle table;
- `v12/python/src/baton_v12/job_manager/` for the optional deployment
  capability, post-launch level-triggered pass, and truthful versioned status;
- `v12/python/tools/single_worker.py` and `v12/python/DEPLOYMENT.md` for the
  production file-exchange composition and closed deployment contract; and
- authorized focused tests under `v12/python/tests/`, with an additive
  `parallel_test.py` registry entry only if a new module is introduced.

Do not add a blocking production subprocess channel, persist raw provider
streams, trust worker files without revalidation, move output into a new tree,
add Job-store shadow state, or implement W71877/W71918/W71878/W61599 policy.

### Revalidated regression matrix

- Static holds reject wrong launch/exchange version, attempt/session,
  operation order, operation identity, digest, filename, member, size, mode,
  type, link, mount target, and cross-attempt delivery.
- A half-written staging file is invisible; final publication is canonical,
  atomic, file-synced and directory-synced. Restart before and after each
  rename converges by rescan.
- Two manager instances publishing the same sequence result in one identical
  command; conflicting reuse refuses. Neither process waits on worker stdio.
- The worker publishes its receipt before provider dispatch. Repeated scans,
  manager restart during the provider call, and worker re-entry after a receipt
  produce exactly one provider invocation.
- Receipt, state, and terminal files are correlated and digest-bound. Missing,
  conflicting, reordered, replaced, oversized, linked, malformed, or foreign
  worker documents refuse or project incomplete; none becomes success.
- Raw recap/stdout/stderr and a registered live secret cannot cross into any
  durable exchange document. The existing output manifest is still validated
  independently before freeze.
- Status reports started/waiting before receipt, active only after receipt,
  answered/ending after a valid terminal, and faulted/lost/incomplete without
  interpreting silence as progress. Canonical-unavailable status says so.
- An answered real worker reaches the existing successful output/ending path
  after manager restart without a second command or provider call. A faulted
  stage does not stop observation of another stage.
- A real-container gate uses a freshly built/selected immutable image and
  proves that the provider continues while the Job Manager process is absent,
  publishes durable output/terminal state, and is recovered by a new manager
  through rescan alone.

The historical process-local replay repro remains valid evidence for why the
diagnostic stdin transport is not the production authority. The revalidated
launch, OCI, worker-entry, worker-image, Job launch/restart/status, and
single-worker baseline is green: 434 cases pass.

## Implementation decisions — 2026-09-04 — W81857

The revalidated boundary above left four choices open that the implementation
had to make. They are recorded here rather than only in the code, because each
one is the kind of thing a later reader would otherwise re-litigate.

### The transport is selected by a launch member, not by a directory

`baton.worker-launch/2` carries a fifth member, `transport`, whose only
accepted value is `baton.worker-exchange/1`. The schema decides the member set,
so no document is valid under both versions and there is no compatibility path.
`/1` stays exactly as it was and remains the diagnostic and test transport
`worker_entry.converse` speaks to.

The alternative — a worker that used the exchange whenever it found the
directories mounted — was rejected. It is the environment channel W26291
retired wearing a different name: a vocabulary with no version, where a manager
and a worker from two generations disagree silently instead of refusing.

### The reference worker never publishes `lost`

The terminal document's closed vocabulary is `answered`, `faulted`, `lost`, as
the revalidation says. The in-image worker publishes only the first two.

A process that re-enters and finds its own receipt with no terminal knows that
some earlier incarnation reached the provider and knows nothing else: whether
that provider is still running, already finished, or gone is not visible from
inside the container. Publishing `lost` there would be publishing an
observation this side does not have. It publishes nothing further and exits
non-zero; loss is the manager's derivation, from the durable receipt combined
with its own exact runtime observation, and this slice does not automate that
derivation into an ending.

### The status vocabulary gained exactly three words

`baton.v12.job-status/3` adds `starting`, `waiting` and `answering`.

- `starting` — the container is up and this control plane has not commanded it,
  or holds no exchange read at all. This is what the defect reported as
  `running`.
- `waiting` — the command sequence is published and the worker has not accepted
  it. The manager owes nothing and the container has not answered.
- `answering` — a correlated `answered` terminal exists and the output is not
  frozen. The turn is over and the ending is owed.

The stage-specific active word is earned by the worker's pre-dispatch receipt
and by nothing else, and an absent exchange read is projected as `null` beside
`starting` — "nobody looked", which is deliberately a different answer from an
exchange that has been read and carries no command.

### Deployment schema `/3` carries exactly three new members

`review_route`, `retention_policy_digest` and `retention_disposition`. They are
the three decisions the ending cannot be composed without, and none has a
default: a deployment that could freeze, collect and retain a result without
saying where the Work goes would be choosing a destination nobody named. The
ending itself adds no policy — it runs the already-ruled owners in the order
their owners fixed, and a faulted, lost or incomplete exchange is reported and
contained rather than abandoned.

## Correction decisions — 2026-09-04 — W81857, review pass 1

Independent review `review-2026-09-04T03-43-45Z.md` accepted the packaging and
returned five P1 findings, every one of which reproduced. Four of the five are
corrections to rules this record already pinned; the fifth changed a decision
and is recorded as such.

### The ending is owed until its LAST step settles, not its third

**Superseded in part on 2026-09-04 by "An unfinished ending is unfinished for
every reader" below.** WHEN an ending is owed is unchanged and is still this
rule. What is superseded is WHO can tell: this correction asked for an exchange
whose state was `answered`, and a reader that holds no exchange read therefore
skipped the rule entirely and reported a frozen, unfinished stage as
`completed`. Read the exchange condition as one of two sufficient signals, not
as a precondition.

The projection gave any frozen output precedence and asked `conclude` only for
`answering`, while the deployment freezes before intake, retention, the
Authority pass and cleanup. A death after the freeze therefore reported
`completed` forever with the assignment still live and the result never handed
to review.

What decides that the ending finished is the manager's own **cleanup axis**,
which `authorize_cleanup` is the last step to move: `complete`, `retained` and
`failed` are settled, and `pending` and `blocked-on-intake` are not. An
answered exchange keeps owing `conclude` until that axis is terminal, however
much of the middle already committed, and the whole composition is re-entrant
at every boundary a crash can land on.

### Publication takes the final name by `link`, and stages under a unique name

One fixed `.publishing` name plus `O_EXCL` turned a single crash into a
permanent wedge at both ends: the staging file survived, no final document
existed, and every later incarnation — and every concurrent second manager —
refused. The staging name is now unique per publication, so it cannot collide;
stale staging is invisible to readers, which open the derived final name only,
and the teardown removes it.

The manager takes the final name with `link` rather than `rename`. Both are
atomic; only `link` **fails closed** on an existing name, which turns a race
into a comparison — an identical command is adopted, a different one refuses,
and a command the worker may already have receipted is never clobbered. The
worker still uses `replace`, because a state event is legitimately published
twice for one operation.

### A byte ceiling is not a credential-safety boundary

Every scalar member of a worker-written document was "any bounded string", and
the provider shares the container identity that owns the event namespace. Each
member now has a closed vocabulary or a canonical grammar — `accepted_at` is a
manager-grammar instant with a real calendar behind it, `fault_code` is one of
this worker's own closed codes, `disposition` is the frozen worker vocabulary,
`manifest_digest` is a canonical sha256 — and the ending decides which of them
apply at all. §13's durable-secret walk runs over the whole projection as the
second line, so a member added later without a shape rule cannot walk past it.

One refused document makes the whole exchange `unreadable` rather than leaving
the members that happened to parse standing beside it.

### The active word needs a receipt AND a running runtime

A receipt is durable and a process is not. Only `uncertain` was treated as
exceptional, so a container that died mid-turn kept its receipt and kept being
reported as working — the original defect one layer down. The active word now
requires both, and every other axis value with a receipt and no terminal is the
pinned incomplete outcome: reported, contained, and authorizing no replay,
because turning it into an ending needs positive evidence and a named recovery
act this slice does not add. `answering` is deliberately exempt: the ending
quiesces the runtime on purpose.

### Superseded — what the terminal's digest is compared against

The `Implementation decisions` section above says the terminal carries "the
digest of the completion envelope already published under the existing
`/output` contract". That is still what the WORKER publishes. What it is
compared with is **superseded**: the first correction compared it against the
frozen result's own `manifest_digest`, and that is a different document — the
manager's result manifest, not the worker's envelope. Comparing the two would
have refused every honest attempt, which is what the real-composition
regression measured.

The comparison is against the sealed result's `completion_manifest_digest`.
`sealing` opens `/output/output.json` itself, validates its shape against the
declarations and recomputes its digest over the bytes it read, so this holds
the worker's claim against **this manager's own independent answer about the
same file**. It happens after the freeze commits, because that answer does not
exist before, and before intake, retention, the pass and cleanup — a mismatch
leaves the durable freeze and settles nothing further.

A worker that completes its sequence and cannot read back its own completion
envelope now publishes `faulted` with code `output` rather than an answer with
a null digest: asking the manager to accept a correlation the worker could not
make is not an answer.

## Correction decisions — 2026-09-04 — W81857, review pass 2

Independent review `review-2026-09-04T04-17-15Z.md` accepted the packaging and
all five prior corrections, and returned two protocol-critical omissions and
one cleanup defect. All three reproduced.

### The schema member is the discriminator, and it is now compared

Every worker document carried `schema` in its closed member set and nothing
compared it, so a document explicitly identifying itself as another protocol
was read as this one because it had the right member names at the right fixed
filename. That is the silent cross-generation agreement the versioned launch
document exists to refuse, one contract down.

Each event kind is now held to its own pinned schema by equality, and the KIND
is checked before the CORRELATION: "this is not a receipt" is a different and
prior answer to "this is not THIS exchange's receipt", and asking them in the
other order would report a foreign protocol as a correlation failure.

### A terminal is the end of a sequence, so its beginning must exist

**Superseded in part on 2026-09-04 by "The exact reachable state vector"
below.** The requirement stated here — the receipt, plus an `answered` state
for each answered operation, plus a `faulted` state on the operation a faulted
ending stopped on — is still required and is not weakened. What is superseded
is the LAST clause of it, "and no operation it does not claim may be sitting
there answered": rejecting only a later `answered` state left every other
impossible tail acceptable. Read that clause as replaced by the exact-vector
rule below.

The receipt, the state events and the terminal were read independently, and a
correlated terminal decided the ending on its own. A worker or provider that
wrote **only** an answered terminal therefore skipped the pre-dispatch replay
fence and every per-operation event and was still projected as a successful
answer — which contradicts the pinned matrix directly, and is worst for the
receipt, because that file is the durable proof that dispatch was fenced
before any provider ran.

A terminal now requires its receipt, and its state evidence is derived from its
own claim: every operation it says it answered carries an `answered` state, a
faulted ending carries a `faulted` state for the operation it stopped on, and
no operation it does not claim may be sitting there answered. `lost` is held to
its answered prefix and nothing further, because by definition nobody observed
what became of the operation it stopped on.

**This changed the worker's publication order.** The completion envelope is now
read back BEFORE `work`'s `answered` state is published rather than after the
loop: publishing `answered` and then faulting over a missing envelope would
emit exactly the contradiction the manager now refuses, and the manager would
reject the whole exchange instead of reading the fault.

### One cleanup boundary per publication, at both ends

The staging unwind began only after the write, the mode and the file sync had
all succeeded, so an ordinary transient failure in any of them left the staging
file behind. Unique names had stopped that being a permanent wedge; they did
not stop it being one leaked file per failure, which contradicted the
publisher's own stated invariant. Creation, write, mode, file sync, link or
replace, directory sync and close now sit under one boundary at both ends,
with no weakening of durability or of the no-clobber rule.


## Correction decisions — 2026-09-04 — W81857, review pass 3

Independent review `review-2026-09-04T04-31-34Z.md` accepted the packaging, the
schema discriminator, the publication cleanup boundary and the worker's
reordered envelope read, and returned one P1 on the causal validator.

### The exact reachable state vector

**This supersedes the last clause of "A terminal is the end of a sequence, so
its beginning must exist" above.** That rule required the answered prefix and
then rejected only a remaining `answered` state, which is a check on the parts
rather than on the history. Four contradictions passed it: a `work` event
before `describe` had completed; a `lost` ending beside a positively observed
fault; a `lost` ending after the whole sequence was answered; and a
`dispatched` event for an operation the sequence had already stopped faulted
before. None of them is a history the reference worker can publish, and "the
parts I checked agree" is not the same claim as "this is a history".

The ending now decides the WHOLE state map, member for member, and the map is
compared exactly:

- **`answered`** — every commanded operation `answered`, and nothing else.
- **`faulted`** — the answered prefix, the next operation `faulted`, and no
  state after it, because the sequence stopped there.
- **`lost`** — the answered prefix, at most the next operation `dispatched`,
  no fault anywhere, and not a completed sequence. Loss is the ABSENCE of an
  observation: a worker that saw a fault saw one, and a sequence that finished
  did not go missing.

`lost` is the one ending with an optional slot, and that is its honest shape
rather than laxity. A process that died between publishing `dispatched` and
receiving an answer leaves exactly that event; one that died before publishing
it leaves none. Both are real crash boundaries this transport exists to
survive, and a rule strict enough to refuse the contradictions above has to
accept them or it refuses the states it was built for. A third value in that
slot is not a boundary.


## Correction decisions — 2026-09-04 — W81857, review pass 5

Independent review `review-2026-09-04T07-00-54Z.md` returned three P1s: one on
the product, one on the acceptance helper, and one on the packaging.

### An unfinished ending is unfinished for every reader

**This supersedes the exchange-dependent half of "The ending is owed until its
LAST step settles" above.** That rule was right about WHEN an ending is owed and
wrong about WHO can tell: it asked for an exchange whose state was `answered`,
and the read-only `job_manager status` surface is given no deployment factory
and therefore has no exchange to read. The same durable state read back
`answering` from a serving manager and `completed` from that surface -- the
freeze-window defect wearing the one disguise the pass-2 correction did not
cover. It was reported in this record's progress and wrongly set aside as
somebody else's scope. It is not: it is inside this Work's accepted status
boundary and it is the read-only form of the defect this Work exists to remove.

The owed ending is now derived from canonical Worker Manager state alone. The
cleanup axis is asked FIRST, so a settled ending is settled for every reader.
Otherwise the ending is owed if EITHER the exchange says `answered` OR this
manager holds a frozen output -- because nothing but the ending freezes one, so
a frozen result beside an unsettled cleanup is an ending in progress however
the reader learned of it. `exchange: null` remains the availability fact and
reports that nobody looked; it no longer decides whether a stage is finished,
and a dependent gate cannot open on a stage whose ending is still owed.

### An acceptance gate that cannot fail is not a gate

`evidence/gate-real-container.py` computed every acceptance member and then
printed JSON and exited zero whatever they said. It now fails closed on all of
them -- the channel-free engine record, the single command and receipt, the
absence of staging residue, the durable output, the container's own exit 0, the
removed exchange and runtime, the completed ending, and the manager's absence
during the turn -- and its verdict is both a member of the evidence and the
process's exit code, so a reader of the document and a reader of `$?` cannot
disagree.

It also bound nothing to the reviewed source: it accepted any image and proved
only that AN immutable image ran. It now requires the proposal's own candidate
digest for `v12/worker/baton_worker.py` and measures the worker file inside the
selected image by copying it OUT -- `create` plus `cp` executes nothing from
the artefact, so the measurement does not depend on trusting the thing being
measured. A mismatch refuses before anything is composed.

### A verification note is generated, never transcribed

The immutable manifest carried a note saying the real-container gate "was NOT
run" beside a member saying it was, because the note was moved between packages
by string edits and one edit silently failed to match. Prose transcribed
between packages is prose nothing checks. The note is now COMPOSED from the
measured members every time, so a member and the sentence about it cannot
disagree.
