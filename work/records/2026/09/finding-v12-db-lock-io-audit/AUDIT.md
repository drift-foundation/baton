# W270520 — static audit of external I/O under database locks

Audit author: baton.tuner, claim270525, 2026-09-26 UTC. **Eleven confirmed
finding groups**, including the already-known `create_line` and removal work;
this is not eleven newly discovered defects. No product or test changes and no
runtime verification. Findings are source proofs of reachable operations, not
measurements of contention, deployment reachability, or independent acceptance.

## Authority, source identity, and method

Selection: this dossier's FINDING/PLAN and reroute270522. Owner clarification
M270535 and OWNER-DISPOSITION-20260926.md require audit return first; Slawomir
then selects a dedicated correction Job. No automatic execution Jobs. Governing rule:
`baton:work/records/2026/09/finding-v12-failed-run-resource-hold/FINDING.md`,
September25 short-transactions ruling and September26T01:04:01Z reaffirmation.
Application filesystem reads count; calling another store is external to the
transaction owner. SQLite's own storage I/O is excluded. An application callback
does not inherit that exception.

Read W270520 events through270525 and T270520 through270535, with no pagination
remaining. Read W257624 detail at snapshot270534, its current PLAN/checkpoint,
latest author progress, review-2026-09-26T01-32-28Z.md, events270471/270482/270485
and complete T257624 through266328. W257624 was held by baton.claude. Owner270482
selects restoration correction; this audit neither takes its ownership nor
accepts its changing candidate. Final coordination refresh read complete
handoff270572, review disposition270595 and Claude's new claim270605, plus
review-2026-09-26T01-49-21Z.md and its current checkpoint. The reviewer confirmed
successor-byte loss and false success in the concurrent-restorer residual and
returned it for correction under the existing authority. That is separately
owned evidence, not a test run or new finding count from this audit.

Static inventory covered all **104 Python files** in `v12/python/src` and
`v12/python/tools`. `transaction-inventory.txt` records **184 syntactic call
sites**, including wrappers, authority replay, snapshots and interpolated
savepoints. These are not 184 distinct transactions. `callback-calls.txt` is a
supporting direct-call inventory, not a complete call graph. Inspection traced
the concrete callback bodies, same-store readers, manual intervals, replay
witnesses, and the external chains below. Python AST parsing and file hashing
read source only; no product module was imported or executed.

`source-sha256-start.json` and `source-sha256-end.json` bind every inventoried
Python file to bytes and UTC observations. `source-excerpts.json` retains 49
original, line-numbered function excerpts and their whole-file SHA256 identities.
All line numbers below refer to that observation, not a future checkout. The
end manifest reports whether bytes changed during this audit. The report is
bounded by the dynamic-call and cold-import limitations below.

Paths below are relative to `v12/python/src/baton_v12/` unless stated otherwise.

## Transaction intervals shared by the findings

* **ControlStore:** `worker_manager/store.py:592` begins IMMEDIATE; `:603` calls
  `action(connection)` inside savepoint `act`; success records the result and
  commits, ordinary refusal/fault rolls back, and durable refusal records then
  commits. Findings F1–F8 occur before that transaction ends. Replay outside
  the lock may skip an action, but a fresh operation executes it under the lock.
* **JobStore:** `job_manager/store.py:821` begins IMMEDIATE; `:831` calls the
  action, followed by journal/commit or refusal/fault rollback. F9–F11 occur
  inside that interval.
* **IntegrationStore:** `integration/store.py:753` begins IMMEDIATE and `:766`
  invokes the action. `:756` also replays through a witness under that lock.
  Replay at `:846` otherwise owns a read snapshot; `:872` invokes its witness
  before snapshot exit. This indirect path was included, not presumed pure.
* **Authority Store:** `authority/store.py:574` begins IMMEDIATE, `:578` invokes
  the body; `replay:481` passes the operation through `_savepoint:437` inside it.
  `read_snapshot:530` begins DEFERRED, invokes the body and rolls back. Nested
  authority writes join the existing write; reads join it too.

## Confirmed findings and bounded correction obligations

### F1 — development-line creation scans and changes permissions under lock

**Confirmed, known W257624 overlap, high priority.**
`review_cycles.create_line:1089 -> ControlStore.transact -> act:1062–1087` calls
`_object:1067 -> review_cycles._object:803` (link/directory checks, realpath/stat),
`workspaces.prove_line_integrity:1080` (definition1168, descriptor/tree walk), and
`workspaces.establish_line_access:1081` (definition1101, realpath/open/fstat,
fchown/fchmod and the access proof). The earlier materialization at1045 is
outside the lock; the completing callback is not.

Impact: a filesystem stall or large tree holds the whole manager write lock;
permission effects may survive a database rollback. Proposed small correction:
keep the existing `materializing` ownership state, perform the integrity/access
work outside transactions, and condition publication on the exact owned line,
source/object pins and generation/state. Concurrent materializers and retries
must not change a published line. Do not merely relocate the final stat and
leave the walk/permission helpers inside. This site is explicitly retained as
out of scope in W257624's current restoration checkpoint.

### F2 — serialized workspace removal and intake completion perform deletion

**Confirmed, known W257624 R3 overlap, highest-priority correction group.**
`workspaces.discard_workspace:2790 -> _serialized_removal:1673 -> removal:1668`
executes `refuse_if_held:1669` and `removing:1670` under IMMEDIATE.
`refuse_if_held:1688 -> _real:1782` reaches realpath (filesystem link reads).
The first removal callback reaches `_remove:3169`: mount-table/tree inspection,
permission changes and deletion. The other caller,
`discard_execution_roots:2958`, supplies `_execution_roots_removed:2964`, which
opens/scans/stats/chmods/unlinks/rmdirs the execution roots.

There is also an enclosing-transaction entry:
`intake.authorize_cleanup:1257 -> _settle:4459 -> discard_execution_roots:4556`.
The nested branch at `workspaces:1634–1636` sees `in_transaction`, rechecks holds
and calls `removing()` directly. Fixing only the standalone `transact` at1673
would miss this path; even the outer realpath in `discard_execution_roots` then
runs under the intake transaction.

Impact: deletion and its preflight block unrelated manager writes; rollback
cannot restore removed data. Preserve R1 hold-vs-removal exclusion, both-root
overlap protection, object/alias/mount checks, exact per-call answers, cleanup
attribution and delayed-submitter exclusion. Use a short committed ownership
transition before removal, keep uncertainty held, and condition completion on
that ownership. Existing lifecycle machinery must be assessed first. Comments
at1573ff/2788/2946 that endorse lock-across-removal are superseded by the owner
rule. This report does not authorize their implementation or transfer files.

### F3 — context-use disposal removes files inside its completing transaction

**Confirmed, high priority; separately actionable from restoration.**
`context_delivery.discard_context_use:564 -> discard:555–563 -> _storage:556 ->
_open_absolute:32` opens and fstats paths; `_directories:151` opens the use/home;
`_clear_owned:567–599` scans/stats, changes directory permissions through
`_private`, unlinks/rmdirs and fsyncs. All run before ControlStore commit. The
intent at554 is already outside this completing transaction, but does not move
the destructive work out of it. No production caller of this exported disposal
function was found in the inventoried tools; its supported function body still
contains the violation, without claiming it ran in a deployed Job.

Proposed boundary: this disposal function and its existing lifecycle evidence.
Preserve finalized-use/positive-exclusion checks, delivered object pins,
published-generation retention, exact operation replay and refusal of foreign
objects. A durable intent must actually exclude competing disposal/use until
effects are settled; interrupted disposal cannot publish false completion.

### F4 — context admission and invocation binding perform filesystem and cross-store reads

**Confirmed, high priority for required context reuse.** Two concrete entries:

* `provider_context.admit_context_use:727/784 -> _transition:629 -> act:627 ->
  check -> _check_admission:790 -> _facts:670`.
* `bind_context_invocation:1176 -> commit:1172 -> _facts`.

`_facts:673 -> _job_attempt:662` reads Job stage/episode/job rows;
`:688` calls `authority.assignment_of`; `:691–702` opens/fstats the development
line and source via `context_delivery._open_absolute`, closes descriptors, and
reads Job execution limits. Admission additionally calls `_qualified:794 ->
qualification_deployment:137–147`, which opens the workspace storage root.
These are real nested calls, not just capability checks. Tool reachability is
explicit in `v12/python/tools/stage_execution.py:1311/1314`.

Proposed small corrections: admission first, invocation binding second if that
keeps each review bounded. Preserve exact context revision, writer/assignment,
Job and profile bindings, immutable object pins, qualification consumption and
stale-generation refusal. Bind prepared facts in a database-only conditional
transition and re-prove external facts at the actual launch/use boundary;
moving reads alone must not admit a stale or replaced context. Completed replay
and pending-admission retry require distinct coverage.

### F5 — opening an execution session reads the Authority under the manager lock

**Confirmed.** `sessions.open_agent_session:344 -> _open:350 ->
_live_assignment:373/403 -> port.assignment_of:436` executes inside
ControlStore. The concrete adapter is
`authority_port.AuthorityPort.assignment_of:314–325 -> Session.assignment_of ->
authority.core.Core.assignment_of:1196 -> _work`, a query to the Authority's
separate database. A remote adapter could also wait on transport; remote use is
not needed to establish the cross-store violation.

Proposed boundary: execution-session admission. Preserve the exact assignment,
participant, profile policy, session epoch and atomic posture-slot occupancy;
non-execution postures need not acquire this external dependency. Stale prepared
authority facts must not authorize a session after fencing.

### F6 — output freeze request reads the Authority under the manager lock

**Confirmed.** `output.request_freeze:194 -> _request:219 ->
port.assignment_of:235`, with the same concrete Authority chain as F5. Proposed
boundary: freeze intent admission; preserve assignment equality, disposition
eligibility, monotonic output axis and operation replay. External freezing is
not the offending call here: the live-assignment read is.

### F7 — intake sealing reads the Authority under the manager lock

**Confirmed.** `intake.record_intake:654 -> _seal:732 ->
port.assignment_of:748` uses the F5 Authority chain before it writes the receipt
and sealed observation. Proposed boundary: custody classification/sealing.
Preserve accepted-versus-quarantined classification for ended or changed
generations, artifact measurements, exact receipt identity and cancellation's
recoverable flag. A cached answer that falsely labels stale output accepted is
not an acceptable fix.

### F8 — interrogation admission reads the Authority under the manager lock

**Confirmed.** `interrogation._ask:296 -> act:274 -> _still_live:168 ->
port.assignment_of:182` uses the F5 Authority chain. The agent `probe`/`inquire`
capability lookup in act is not itself proof of a provider invocation; actual
provider work follows the committed request. Proposed boundary: interrogation
admission; preserve session epoch, live fixed generation, stable replay and the
deadline stamped for the winning request. A completed retry must still work
when today's adapter or Authority is unavailable.

### F9 — abandoned-correction Job restart reads the worker store inside the Job write

**Confirmed, recovery-adjacent; does not review W257624's restoration candidate.**
`job_manager/episodes.restart_abandoned_correction:1218 -> act:1178–1188 ->
_excluded_correction:716 -> review_cycles.abandoned_correction_of(custody)` and
`intake.abandoned_gate_discharge_of(custody)`. `_prepared_line:763` reads line,
integration-checkpoint and writer records on `custody`; `_job_correction:888`
reads its verdict. `custody` is the worker ControlStore, not the Job connection.
The comment at1166ff acknowledges that the Job lock does not freeze that store.

Proposed boundary: this restart's evidence preparation and conditional episode
ending. Preserve the completed restoration/discharge pairing, exact old attempt
and generation, unsuperseded checkpoint/verdict, no active writer, no held Job
allocation, and effective-once episode replacement. Repeated cross-store reads
under the Job lock are neither permitted I/O nor a cross-database atomic proof.

### F10 — integration apply admission reads the coordinator inside the Job write

**Confirmed.** `integration_capacity.admit_integration_execution:1182 ->
perform:1166 -> _prove_grant:797` calls `integration.queue.live_grant:1788` at809 and reaches
`granted_context:1738 -> IntegrationStore.snapshot` and coordinator queries
while JobStore holds IMMEDIATE. This branch is conditional on `phase == apply`.
The authorization-owner call itself is before the transaction; do not conflate
it with the actual in-lock grant proof. Tool callers include
`tools/integration_worker.py:1839` and `tools/stage_execution.py:2848`.

Proposed boundary: apply-membership admission. Preserve exact lease/fence,
target/entry identity, collected preparation content, authorization binding and
serial membership. A released or superseded grant must not authorize a target
writer merely because its earlier read matched.

### F11 — integration ending reads worker and Authority stores inside the Job write

**Confirmed.** `integration_capacity.end_integration_execution:1422 ->
perform:1407 -> _collected_content:1243` reads worker frozen output/intake;
`:1408 -> _resolved_exclusion:1186` reads runtime under `control.snapshot` or
calls `attempts.unstarted_cancellation_of(control, port, attempt_id)`.
The latter correctly closes its *own* worker read snapshot before
`port.project_work` at `attempts:3197`, but the *outer Job write* is still open.
This is an enclosing-transaction violation that local helper comments miss.
Tool callers include `tools/integration_worker.py:1235/1476` and
`tools/stage_execution.py:5793`.

Proposed boundary: integration membership ending. Preserve positive runtime
absence or committed never-started cancellation, exact admitted assignment,
start-submission exclusion, accepted intake/content attribution and held-capacity
behavior on uncertainty. Reading receipts outside the write needs conditional
local completion and a sound monotonic/exclusion argument, not weaker checks.

## Coverage and compliant concrete patterns

| Surface | Inspection and result |
| --- | --- |
| Four store wrappers | Read begin/action/replay/savepoint/record/commit/refusal paths, read snapshots and create/open/migration intervals. Database schema construction uses embedded DDL; in-memory SQLite schema comparisons are database/library work, not another persistent authority. Arbitrary injected actions/clocks remain qualified below. |
| Authority core/API/session | Direct configuration/activity transactions plus all `_replay` entry sites and nested receipt preconditions. Concrete policy, route, assignment, label, proposal, receipt and gate helpers read/write the same Authority store or process owned values. Review/approval preconditions call `_disposition_of` on that store. No additional application filesystem/network effect identified in those concrete bodies. |
| Worker attempts | Record/activate/start reservation/failure/cancellation/finalization callbacks; manual boundary-identity transaction; observation, accounting and identified-runtime savepoints. Traced `_decide`, `_reconciled`, `_settled`, lane/session changes and document validation. Concrete callbacks use this store and owned values. Runtime launch/reconciliation adapter effects are outside their local transaction intervals. |
| Worker sessions/interrogation/output | F5/F6/F8. Manual session adoption/state/close/transport-loss and interrogation answer/settlement/publication transactions use same-store rows. `publish_inquiry_answer` calls the port before BEGIN. |
| Worker intake/custody/workspaces | F2/F7. Other intake request/retention/discharge/recordless completion callbacks use owned documents and same-store proofs. `_adopted_custody -> adopted_directory_custody -> _recorded_store` uses recorded configuration and journal replay, not the custodian engine. Custody `_claim_episode` checks holds under lock, then effects run outside it; normalization records the prepared answer afterward. |
| Worker review cycles | F1 plus known corrected/evolving cases below. Read grant/progress/freeze/attach/verdict callbacks and freeze's manual intent transaction; `_completed_review`, `_custodied_review`, `_cleaned_review` validate stored receipts/manifests. Profile freeze/validate and authority fencing occur outside freeze's local transactions. |
| Worker context | F3/F4. Other supplied `_transition` calls (deliver/hold/retire/finalize) carry owned payloads without a `check` callback; profile/qualification/storage/staging record callbacks hold prepared values. Admission's supplied check is explicitly traced, not classified pure. |
| Worker offers/manifests/handshake/posture/deadlines | Offer callbacks operate on rows; bearer generation precedes the transaction. Manual manifest retention and posture transitions use same-store SQL and pure documents. Handshake connection context performs an upsert; autocommit handles do not start a long transaction merely by entering that context. Deadline snapshots/callbacks use same-store proof; authority discharge precedes its receipt transaction. |
| Job submission/scheduler/manager/ending/episodes | Submission expands jobs/stages and first episodes in one store. Pool/reservation/move callbacks, including capacity releasability, use Job rows. Manager/ending callbacks record prepared receipts. Correction advancement's callback uses same-store episode/allocation facts; abandoned restart has F9. |
| Job integration capacity | F10/F11. Preparation recovery/intent, registration, recovery/ending state and failed-integration receipt callbacks use local rows/prepared values. Initial control snapshot at907 ends before outside authorization and the Job transaction. |
| Integration queue/reconciliation | Traced wrapper actions and `_proved`, `_witness`, `_managed_witness` replay into relationship/result readers, including managed task/result adoption and embedded limits validation. These concrete witnesses inspect owned documents and this coordinator's rows. Filesystem storage proofs/profile execution in reconciliation are outside the local action callbacks. Arbitrary witness supplied directly to the store is not proved safe. |
| Operational tools | All Python tools scanned for manual/implicit transaction syntax and wrapper calls. The two explicit coordinator snapshots in `stage_execution.py:3375/3517` contain coordinator reads; subsequent profile/authority work is outside. Traced tool callers of F4/F10/F11 and the delegation facade into AuthorityPort. No separate tools-level transaction owner found. Tool calls inherit the violations in their library callees; this is not an acceptance of all tool behavior. |

The AST search was supplemented by textual checks for BEGIN, SAVEPOINT,
commit/rollback, connection contexts, isolation settings and sqlite connections.
It includes the three f-string savepoints in `attempts.py`, which a literal
`BEGIN` search misses. No lock-held logging-stream, file-hash, live-provider or
engine invocation was confirmed beyond the filesystem/cross-store chains above;
this is a bounded finding, not an assertion that arbitrary callbacks cannot do so.

## Known correction and candidate classifications

* **Already accepted bounded correction:** `grant_writer` in W257624's
  review-2026-09-26T01-32-28Z.md. Current callback compares recorded object pins
  and local state; `_proved_line_object` and access proof occur before it. An
  initial object proof still runs on replay, outside the local transaction.
  This audit reuses that review as history and runs no acceptance tests.
* **Evolving, separately owned:** `restore_abandoned_correction`. Observed bytes
  have intent revocation and a database-only completing callback, with profile
  restoration between the transactions. They differ from accepted grant-only
  file SHA256 `0f994874aef4dea2d5f2bc665d1ec1b305ec3b4c94dc3bba6d15d9476a72101b`.
  That observation is neither independent acceptance nor a concurrency-safety
  verdict. Subsequent independent review-2026-09-26T01-49-21Z.md rejects these
  same bytes for overlapping restoration, successor-byte loss and completion
  replay returning success. Preserve owner270482's no-concurrent-restorer/
  successor requirement; claim270605 continues that correction. This audit
  does not reinterpret the residual as needing new permission.
* **Known open neighbors:** F1/F2 overlap explicitly retained W257624 work.
  F9 is a caller-side Job-store boundary, separately reportable even if worker
  restoration is corrected. Owner disposition must coordinate exact paths;
  none has been transferred here.

## Unresolved dynamic boundaries and exclusions

1. All four stores accept callable bodies/actions; IntegrationStore accepts a
   replay witness, provider-context transition accepts `check`, and stores/core
   accept injected clocks. Repository-supplied concrete callbacks were traced
   as above; arbitrary caller implementations cannot be proved I/O-free by
   this static audit. Default/tool clocks inspected use local time formatting,
   not a remote clock. Type/callability checks alone do not constrain effects.
2. Adapter properties/capability lookup can execute Python descriptors. The
   concrete Authority port crosses another store (confirmed above), but an
   arbitrary `custodian_image_digest` property or adapter attribute remains a
   dynamic boundary, not proof of an engine call. No monkeypatched deployment
   object was inspected.
3. Function-local imports exist under transactions. Warm imports return loaded
   modules, while a cold interpreter may read Python/package files.
   `contracts/frozen.py` also reads schema bytes at import. The common import
   path loads document/contract modules before manager transactions, but this
   audit does not prove every cold/lazy import ordering. Do not claim a universal
   no-filesystem-I/O invariant until that boundary is addressed or explicitly
   constrained. No cold-start probe was authorized or run.
4. Scope excludes v11 production code, frozen Node implementations, tests as
   execution targets, dossier harnesses and non-v12 bridge/deployment tools.
   No reachable helper outside the v12 source/tools surface was needed to
   establish the confirmed chains. Standard-library file operations were
   classified by their explicit call sites; third-party/native internals and
   Python descriptor overrides were not audited exhaustively. Database engine
   internal I/O remains the stated exception.
5. There was no deployed-store read, engine/provider call, test, timing probe,
   resource cleanup, Git mutation or new dependency/adoption gate. Static file
   reads/hash checks are audit work, not runtime proof. `v12/tools` does not
   exist; discovery resolved the operational-tool root to `v12/python/tools`.
   Initial absence of this new dossier's optional PROGRESS was recorded and
   resolved by creating the tuner-owned audit progress file.

## Recommended owner disposition

First select a bounded correction for **F2**, with separate handling of its
standalone-removal and enclosing-intake entries if necessary, while preserving
W257624's current restoration ownership. Then **F1**, and **F4** for context
reuse; F3 is a distinct destructive-disposal correction. F5–F8 can be separate
small admission/sealing Jobs sharing the same authority-fact discipline;
F9–F11 are distinct cross-store conditional-completion Jobs. This ordering is a
recommendation, not a release classification or an implementation instruction.

For each selected correction, propose focused deterministic evidence at the
actual external call boundary: owner connection outside a transaction, unrelated
database progress during a paused external call, exact competing caller/retry
behavior, stale-generation refusal and failure remaining held. These are future
acceptance obligations; none was executed here. A timeout or a stat moved outside
the lock alone does not prove ownership/exclusion. Reuse existing lifecycle
machinery before considering wider design. Owner selection and independent
review remain responsible for those correction candidates.
