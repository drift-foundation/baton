# Baton repository agent rules

## Git usage (strict)

- Use `git` only for reviewing history, status, and diffs (for example,
  `git status`, `git diff`, `git log`, `git show`, and `git blame`).
- Slawomir alone owns the Git index, commits, branches, tags, and history.
  Agents never stage or unstage changes (`git add`, `git restore --staged`,
  and equivalents).
- Agents never perform mutating Git operations, including `git commit`,
  `merge`, `rebase`, `cherry-pick`, `reset`, `checkout`/`switch`, `stash`,
  branch/tag operations, or pushes.
- A request to make the repository “ready,” “clean,” or “committable” means
  prepare and verify filesystem changes, then report the remaining diff to
  Slawomir. It does not authorize an agent to mutate Git state.
- Do not wrap long calls or expressions merely for readability; avoid
  indentation churn, especially in deeply nested code.
- The following general test-confirmation rule is superseded until further
  notice by the standing authority below. Agents may always add tests without case-specific confirmation. This includes
  new test files/functions and additive cases or members in existing exhaustive
  test registries. Editing or weakening an existing test's assertions or
  expected behavior still requires clear, case-specific confirmation. An
  accepted Work description or plan that explicitly schedules adding, editing,
  or removing tests within a bounded scope is that confirmation; it is not
  blanket authority for a test mutation outside the scheduled scope.

### Standing test-change authority until further notice

Owner ruling 2026-09-13: do not require separate test approvals until Slawomir
revokes this authority. This applies to all Baton Work and all implementing,
reviewing and integrating roles, including current Work. Agents may add, edit,
replace or remove tests, fixtures, assertions, expected behavior and registry
entries as needed for the authorized Work outcome without per-test, per-helper
or additional-test-path owner approval.

This ruling supersedes the general case-specific test-confirmation rule above
and older test-only approval/path restrictions in accepted plans and handoffs,
including W161230's exact test-path amendment gates. Record affected test paths
and reasons in the owning plan/handoff and coordinate file ownership; this is
documentation, not another approval gate. Independent review still evaluates
changed expectations against accepted behavior. Do not waive required acceptance
or remove genuine defect coverage merely to obtain a pass. Product scope,
execution budgets, claims, Git ownership and reviewed candidate/provenance
requirements remain applicable. This standing ruling supplies test-change
authority for integration preflight; the integrator still imports only the
independently reviewed candidate bytes.

Decision history:
[W161230 owner ruling](work/records/2026/09/finding-v12-managed-integration-execution/OWNER-TEST-AUTHORITY-2026-09-13.md).

### W71830 standing test-change authority (historical campaign ruling)

Owner ruling 2026-09-09T16:36Z: until W71830 completes or Slawomir revokes this
authority, all test changes needed for its accepted scope are preapproved.
This covers W71830, its descendants and explicitly recorded prerequisites,
for every implementing, reviewing and integrating role. Agents may add, edit,
replace or remove tests, fixtures, assertions, expected behavior and test
registry entries without further per-test owner approval. This exception
supersedes campaign additive-only, per-method approval and other-test
preservation restrictions, including M128669/M129177 and the amendment in M129247.

Record affected test paths and their reason in the owning plan/handoff and
coordinate file ownership; do not turn that record into another approval gate.
Independent review must evaluate the changed expectations against accepted
behavior. Required acceptance results and genuine defect coverage cannot be
waived merely to pass tests. Product source scope, execution budgets, claims,
Git ownership and integration candidate/provenance checks remain applicable.
For integration preflight, this ruling supplies the campaign's test-change
authority; the independently reviewed candidate still binds the imported bytes.
Do not request another per-test approval or block solely on older permission
wording. Outside this campaign, and after its completion, the general rule above
applies. Decision history:
[W71830 FINDING](work/records/2026/09/finding-v12-standalone-multi-job-pipeline/FINDING.md#2026-09-09t1636z--standing-test-change-authority-through-w71830-completion).

## V12 delivery and v13 hardening boundary

### Normative v12 specification — owner 2026-09-26

Read [v12/DESIGN.md](v12/DESIGN.md) before planning, implementing or reviewing
v12 changes. It specifies the target v12 system, not the running v11 deployment
or an inventory of current code. Align bounded Work and acceptance with its
requirements; report concrete code/spec gaps rather than weakening the spec to
match implementation. Pin owner-approved changes in the owning FINDING and update
DESIGN before dependent implementation. Current plans, evidence and exact review
signoff remain in their owning Work records. All existing claim, scope, review,
execution and human Git ownership rules continue to apply.

Owner ruling 2026-09-14: deliver v12's reliable parallel development Jobs and a
lightweight read-only Job monitor, then use that parallelism to accelerate v13
hardening. Execution correctness, isolation, recovery, context reuse and honest
reviewed result collection remain v12 requirements. Broader stress/performance,
advanced scheduling/shared capacity, distributed execution and richer TUI work
belong to v13; known work-loss, duplicate-effect, isolation or false-success
defects are not deferred merely by calling them hardening.

Pin and classify remaining Work in the current v11 authority now. Preserve
existing Work identities, canonical records and evidence; move selected execution
to v12 after readiness, without prematurely copying the backlog or introducing a
second coordination authority. Individual dependency/containment changes require
an explicit recorded classification; this release ruling does not close unfinished
Work or silently alter a live assignment. Exact decision and next planning action:
[W2 release boundary](work/records/2026/08/finding-v12-isolated-agent-workers/FINDING.md#v12-parallel-delivery-enables-v13-hardening--confirmed-2026-09-14).

### Fresh-attempt recovery and optional session reuse — owner 2026-09-16

The optional-reuse release classification below is superseded by the September
23 ruling immediately following this historical entry. Fresh-attempt recovery
and its accepted evidence remain valid.

The owner now selects fresh, isolated attempts from known inputs as the minimum
v12 recovery path. Failures must be actionable, prior execution stopped or
fenced, and effects/results correctly attributed and independently accepted.
Production provider-session reuse is optional, not a minimum-release gate.
This explicitly supersedes the mandatory context-reuse part of the Sep14
release ruling above and earlier Sep15 release sequencing; it does not waive
isolation, cleanup, recovery correctness or duplicate-effect/false-success
defects. Preserve accepted historical proofs and unfinished reuse evidence.
W177936 is classified as deferred optional production session reuse; its active
handler must preserve work and release safely, not be silently rerouted.
Exact ruling and next bounded readiness check:
[W2 fresh-attempt recovery](work/records/2026/08/finding-v12-isolated-agent-workers/OWNER-FRESH-ATTEMPT-RECOVERY-20260916.md).

### Required context reuse for v12 delivery — owner 2026-09-23

Owner changes the delivery target to independent parallel development Jobs with
working context reuse before moving to v13. Reuse is required because progress
without it is too slow. This supersedes the September 16 optional-reuse
minimum-release classification, while preserving accepted fresh-attempt evidence
and recovery behavior. Historical acceptance is not proof of this expanded target.

Owner clarification later on September 23: reuse is a v12 deliverable, not a
prerequisite to initial adoption. Begin using v12 for independently accepted
parallel Jobs on supported fresh contexts, with reuse among the first v12 Jobs.
This explicitly supersedes the September 22 wait-for-restoration adoption gate
and any interpretation of the first September 23 ruling that blocks initial
adoption on reuse. It does not assert parallel readiness without evidence or
authorize a particular live run, deployment change or silent dependency change.

Finish the bounded implementation, independent-review and resume/correction
proofs and establish the selected parallel workflow with reuse. Broad refactoring,
consolidation, robustness and hardening remain v13 work; fix concrete execution,
isolation, cleanup, attribution and false-success blockers needed for v12 now.
This is no selection of a broad supervisor refactor, automatic integration,
additional live execution, or silent claim/dependency changes. Human-plus-agent
integration remains the default. Exact ruling:
[W2 required reuse](work/records/2026/08/finding-v12-isolated-agent-workers/OWNER-REQUIRED-REUSE-20260923.md).

## Development verification time accounting

Owner ruling 2026-09-14: cumulative stopwatch budgets are not approval or
execution gates for ordinary focused deterministic verification in the current
v12 delivery/v13 development campaign. This supersedes earlier cumulative
author/reviewer caps, remaining-bank admission checks and demands to reconstruct
missing historical seconds before another ordinary test iteration, including
W161230's prospective1200s grant in M166281. No replenishment request is needed
solely because a cumulative test allowance is exhausted or historically unknown.

Use sensible per-run timeouts appropriate to the Job and test, with process
termination and cleanup time. Predictions guide planning; they are not exact
evidence or additional approval gates. Record measured durations when available,
mark unknowns and estimates honestly, and preserve existing evidence. Do not
manufacture upper bounds or erase costs. An unproved historical total is not
proof that old processes ended; investigate concrete resource uncertainty
separately without turning missing seconds into a development blocker.

Selected product scope, focused-test scope, execution boundaries, isolation,
cleanup and truthful independent acceptance remain required. Materially different
execution such as live models, actual engine operations excluded by the owning
scope, or broad stress campaigns needs its own selection. This does not authorize
a previously excluded run or rerun, remove a reviewed single-run supervisor's
limits, or change product Job timeout semantics. No broad discovery merely to
settle historical accounting. Exact decision and correction:
[W161230 finding](work/records/2026/09/finding-v12-managed-integration-execution/FINDING.md#2026-09-14t042423z--cumulative-test-time-is-not-a-development-gate).

## V12 verification defaults

Owner ruling 2026-09-12: for all future v12 work, use deterministic fake/replay
providers and focused local tests by default. Live provider/model execution is
reserved for a specific question that needs the real provider, such as actual
authentication, provider protocol behavior or model-dependent output. State that
question and why deterministic coverage cannot answer it in the owning Work;
this is a scope explanation, not an additional approval or reviewer-model gate.
Do not run live models merely because a test is an integration/end-to-end test,
a change was handed off, or a fresh run identity was prepared. Reuse applicable
live evidence rather than repeating it in the normal development loop.

Simulate the provider at its normal boundary while exercising the real
coordination and affected runtime, workspace, merge, test and final-result
behavior. Label simulated evidence accurately; never fabricate owner receipts
or claim live-provider coverage from a fixture. Extend deterministic coverage
when needed instead of defaulting to a live call. Existing execution authority,
budgets and genuine provider-specific acceptance obligations still apply.

This standing default applies beyond W71830 and supersedes older blanket
live-provider verification requirements for ordinary v12 development iterations.
Decision and measured feedback-time comparison:
[W71830 FINDING](work/records/2026/09/finding-v12-standalone-multi-job-pipeline/FINDING.md#2026-09-12t154509z--deterministic-provider-default-for-all-future-v12-work).

## Coordination identities

- Read `docs/AGENTS-MAILBOX-PROTO.md` in full before publishing or consuming Baton handoffs. The local deployment supplies the executable and explicit absolute config path; never infer or hard-code either in repository policy.
- This project's coordination identities are `baton.prompt` for Slawomir's
  human-attached interactive copilot (`prompt`), `baton.codex` for the managed
  background reviewer (`rview`), `baton.claude` for the implementer (`impl`),
  `baton.merge` for proposal integration (`integ`), `baton.slaw` for the
  approver (`approv`), and `baton.tuner` for final polish (`tuner`). Resolve
  role-only instructions to those identities; never
  substitute a participant from another domain. Every agent launch names both
  its participant and one explicit role it holds.
- `baton.prompt` reads, discusses, creates and coordinates Work from the one
  interactive context, but it is not a Route handler and never consumes Baton
  readiness. Routed review, research and planning Work belongs to the one
  managed `baton.codex` context. Never launch a hidden second context under
  either address or use one participant for both foreground and background
  execution. Each runtime publisher reports only the exact context mapped to
  its participant; runtime visibility does not imply a readiness consumer.
- `baton.merge` is a distinct managed context, not an alias for implementation,
  review, tuning, or approval. It imports only an independently approved,
  digest-bound proposal into the current working tree after checking its base,
  path set, and target for drift or overlap. It refuses missing provenance,
  digest mismatch, divergence, overlap, or conflict rather than redesigning or
  correcting the proposal. It never stages files or mutates Git history; after
  bounded integration verification it passes the prepared diff to
  `baton.slaw` for approval and Git ownership.
- Before changing any working-tree path, `baton.merge` completes the authority
  preflight for the whole proposed path set. An accepted Work description or
  plan that explicitly schedules adding, editing, or removing tests within a
  bounded scope grants the case-specific test-change authority; the current
  standing test-change authority above supplies it until revoked. The newest
  independent review still binds the immutable proposal digest, enumerates
  every existing test path actually changed, and evaluates any assertion or
  expected-behaviour changes. Generic sign-off, exact path or candidate-byte
  enumeration, and proposal-wide approval without that scheduled scope do not
  grant authority on their own; the standing ruling supplies test authority
  without another owner-approved test-path amendment. Refuse before changing any path when scope or review is
  missing, ambiguous, stale, digest-mismatched, or incomplete: the integrator
  returns the Work for clarification and will never request interactive
  approval from a managed turn. Approval is limited to the reviewed candidate
  bytes at the named paths and does not authorize another test change,
  weakening, redesign, conflict correction, or opportunistic edits.
- Custody file modes protect immutable evidence and are never checkout mode
  instructions. Before any import, `baton.merge` requires every existing target
  to be a non-symlink regular file matching the reviewed base bytes and already
  owner-writable. A failed type, byte, or owner-write check refuses the whole
  import before content or mode mutation and returns it to `baton.ops` for exact
  repair. The integrator imports reviewed content without preserving custody
  modes and must verify final bytes and modes. It must never work around a
  read-only target with `install`, `chmod`, or another privileged replacement. An
  explicitly planned new regular file uses ordinary non-executable repository
  mode; executable mode requires explicit accepted scope.
- Run exactly one active readiness path per participant — never two concurrent
  `wait`s for the same address. Two consumers need two participant addresses,
  not one shared identity. Act on every wake immediately: `claim` the Work
  before executing it, and `pass` or `close` it rather than leaving it held.
- `wait` is read-only: it blocks until actionable state or timeout and creates
  no claim. An active agent keeps one `wait` armed, polls its terminal, then
  acts explicitly — `claim work=` to take Work, `respond`/`accept`/`dispose`
  to answer a directed `@` obligation, `mark-seen` to acknowledge messages.
  Re-arm `wait` after every result. Never leave a successful readiness result
  unattended; terminal completion may not itself schedule a new model turn.
- The SQLite instance is the only coordination authority. Never mutate it with raw SQL or manually reconstruct protocol state. Never read it directly either: if a question about the coordination state can only be answered by opening the store, that inability is the finding.

## Confirmed decisions are pinned before implementation

Owner coordination delegation 2026-09-26: `baton.prompt` monitors canonical Work
state and evidence and coordinates routine continuation, corrections, ownership,
handoffs and milestone checkpoints within the accepted specification and selected
scope. Any proposed specification adjustment requires Slawomir's explicit approval
before changing the specification or implementing the adjusted behavior. This
delegation grants no Route-handler impersonation, managed readiness consumption,
Git mutation or bypass of independent review. Scheduling relationships are
recorded in Baton's graph, not substituted with document prose. Exact ruling:
[Owner coordination](work/records/2026/09/finding-v12-shared-resource-token/FINDING.md#owner-coordination-ruling--2026-09-26).

- `docs/EFFECTIVE-BATON.md` is a shared methodology book for all projects and
  users: worked examples and adaptable strategies, not a prescribed setup.
  Role splits are examples, not protocol requirements. Keep concrete Job IDs,
  transient state and deployment recipes out of the book; exact operations
  belong in reference manuals. Project-specific decisions,
  temporary permissions and campaign exceptions belong in this project's
  `AGENTS.md` and owning Work records, not in the shared book.
- Baton discussion is coordination EVIDENCE, not the durable specification. A ruling that exists only in a message thread is one context loss away from being re-litigated or silently reversed.
- Before implementing a confirmed product, UX, protocol, or operational decision, write it into the owning record's `FINDING.md` under `work/records/YYYY/MM/finding-<slug>/`, and reflect its queued/in-progress/done state in the applicable `PLAN.md` or umbrella. If no owning record exists, create one before editing implementation.
- Findings preserve the CHRONOLOGICAL history of decisions; plans and umbrellas name the one that is currently actionable. The two answer different questions — "how did we get here" and "what is true now" — and collapsing them loses whichever the reader needed.
- At implementation start, REVALIDATE the recorded ruling against current code, protocol, and later decisions. If it has changed, append an explicit dated supersession or clarification with its rationale and update the plan. Never delete or rewrite an old decision as though it had never been made: the reasoning that was superseded is how the next reader knows why the current rule is not the obvious one.
- A superseding decision must explicitly mark the old text superseded. Two live rules that contradict each other are worse than either alone, because both look authoritative.
- Implementation and review handoffs reference the exact decision files.
- After a restart or context loss, resume from those repository records — never from memory, and never from a subject line.

This gate exists because a ruled decision was lost: the console's `Enter` behaviour was agreed, never written into its finding, and the implementation later contradicted it. `AGENTS.md` is this rule's one owner; it is agent policy and is not duplicated in the README.


## Review findings tracking (`work/records` dossiers)

**Superseded 2026-08-16 at the schema-14 cutover (checkpoint `6c3519e6`):**
finding dossiers are no longer ephemeral `work/finding-*` folders. A dossier
is a PERMANENT record created at its canonical path and never moved, archived,
or deleted by lifecycle:

```text
work/
  open/
    finding-friendly-name -> ../records/YYYY/MM/finding-stable-name
  records/
    YYYY/
      MM/
        finding-stable-name/
```

- The year/month is chosen at creation and the canonical `work/records/...`
  path does not change when Work changes phase or becomes terminal. The record
  holds the finding, plan, progress, append-only reviews, reproductions,
  scripts, fixtures, data, and other durable evidence.
- Baton Work bindings, messages, handoffs, reviews, and cross-references use
  only the configured repository identity plus the canonical repository-
  relative `work/records/...` path — never `work/open/...`, never an absolute
  checkout path, and never a Git commit as the primary locator.
- `work/open/` is a deliberately maintained human convenience index of
  relative symlinks for sweeping still-open records. Its links are not
  protocol state and carry no lifecycle semantics; unlinking a closed
  record's symlink is later housekeeping and never touches the record.
- Not every lightweight Baton Work needs a dossier or an open symlink. Once a
  dossier exists its canonical record path is the stable binding; later
  corrections to terminal evidence are explicit follow-up history, never a
  silent rewrite or a rename.
- Every finding dossier MUST have exactly one corresponding Work on the
  authoritative Baton ledger, bound to its canonical `work/records/...` path.
  Create the Work and dossier together when possible. If research creates the
  dossier first, create its ledger Work immediately before any further work or
  handoff. A deferred or roadmap finding is parked on the ledger; it is never
  left as an off-ledger folder. The reverse is intentionally not required:
  lightweight Work may still exist without a dossier.
- Remaining `work/finding-*` folders are LEGACY items pending the deliberate
  cleanup audit owned by `work/records/2026/08/finding-next-release/`; no new
  folder is ever created there.

The working process is unchanged by the layout:

- Slawomir and the reviewer normally create, research, prioritize, and queue
  findings. The implementer stays on the current serial item rather than
  spending implementation cycles reconstructing queued decisions.
- A top-level record owns `FINDING.md`, `PLAN.md`, and implementer-owned
  `PROGRESS.md`. The finding records observed behavior, evidence, decisions,
  and acceptance boundaries; the plan orders current work; progress is the
  implementer's claim of current state.
- Reviewer research should make the next item implementation-ready: include a
  minimal repro/baseline, exact code paths and symbols, confirmed facts versus
  hypotheses, recommended patch boundary, interactions, positive/negative/
  race/retry regressions, focused verification, and unresolved decisions.
  Label uncertain material **Observed**, **Confirmed**, **Inferred**,
  **Proposed**, or **Open**. Reviewer proposals are decision support, not
  authority; the implementer must revalidate them against the current tree.
- Findings are worked serially to completion. Reviewer work may continue on
  queued findings, but the implementer does not switch merely because a queued
  record changed.
- When starting an item, read its whole record fresh and re-check every
  captured claim. Earlier work may have resolved or invalidated it. Record an
  explicit resolved/superseded outcome rather than silently deleting stale
  work or reimplementing it.
- Discovery is recursive and role-neutral. Either role may immediately file a
  new defect; filing does not interrupt the serial queue. Human/reviewer still
  own formal enrichment and priority by default.
- A causally tied child lives at
  `work/records/YYYY/MM/finding-<parent>/findings/finding-<child>/`, with its
  own `FINDING.md`, `PLAN.md`, and `PROGRESS.md`. The child names its
  parent/discovery context; the parent plan/progress indexes the child and
  status. Use a top-level record instead when it is independent, separately
  scheduled, or may outlive the parent.
- Do not encode hierarchy/order with dotted names or numeric prefixes. Keep at
  most two child levels. Promote a deeper or independently scheduled child to
  top level as a NEW record with an explicit forwarding note in the old one —
  the old canonical path stays valid history and is never rewritten.
  A parent cannot close while it contains an open child.
- `PROGRESS.md` has one current writer at a time: the participant who actually
  makes the implementation change under the authorized Work claim. Progress
  ownership is not reserved to `baton.claude`; it belongs equally to an
  explicitly assigned tuner, reviewer, approver, prompt participant, or other
  Handler when that participant performs the change. If implementation passes
  through serial claim episodes, each actual change author appends an
  attributable entry and never rewrites or deletes a prior author's account.
  A participant that only reviews or discusses the change still records input
  in FINDING/PLAN, evidence files, or append-only review journals, never in
  progress.
- Each review pass is append-only
  `review-YYYY-MM-DDTHH-MM-SSZ.md` in that record root (UTC). Never edit or
  delete an earlier review. The implementer records its response and current
  awaiting-review/changes-requested/signed-off state in `PROGRESS.md`.
- Before parallel edits, establish file ownership explicitly. Implementation
  handoffs reference the exact finding, plan, progress, and newest review
  paths discussed.
- Anything that must stand alone regardless of the record (tests, user docs,
  durable repository policy) still lives outside it; a record is evidence and
  decision history, not a hiding place for product artifacts.

## The active-work claim (finding-active-work-claim, 2026-08-16)

- No participant starts implementation, review, or other execution owned by
  the Work's Route endpoint before the atomic `claim` operation SUCCEEDS,
  and a competing claim fails closed.
- Route, Handler and Next are three different questions: which endpoint MAY
  claim, which member IS executing, and which endpoint is planned next. The
  claim records the Handler.
- Phase is not orthogonal to the claim. It is a closed scheduler axis —
  `queued`, `active`, `block`, `parked`, and nothing at all once terminal —
  and `active` means exactly "a Handler holds it". Only `claim` reaches
  `active`; a `block` row names the one gate holding it.
- Discussion and planning while unclaimed are fine. A pass releases the
  claim and derives the destination phase from the destination Route
  atomically; the recipient claims explicitly once the Work is ready.

## Delivery continuity and bounded context — owner 2026-09-23

Routine review corrections within accepted scope pass directly to the configured
implementation endpoint (currently baton.impl); accepted delivery passes to the
owner. Use an explicit pass to implementation rather than consuming an old
next=baton.decide when correction is the disposition. Escalate only a concrete
scope, authority or product decision, with the exact blocked operation. Partial
progress or a voluntarily ended turn does not require renewed owner approval.
Continue authorized work while possible; if execution must end, preserve an
exact continuation checkpoint and release through the existing claim protocol.
Review of partial progress must not turn ordinary continuation into an owner gate.
This supersedes older owner-return defaults for routine corrections, including
W239533 handoffs. It does not bypass independent acceptance or live-run selection.

Keep the current PLAN/checkpoint concise: accepted facts, next executable
milestone, exact owned paths, latest review/evidence references and concrete
blockers. Preserve FINDING history and append-only reviews. On assignment or
resume, read current canonical detail, complete current handoff, current scope,
ownership, checkpoint, latest review and new discussion since the recorded
checkpoint; follow referenced or conflicting history as needed. Record the
last discussion/event position read. If the checkpoint is missing, ambiguous
or stale, expand the read until current authority is clear. This explicitly
supersedes blanket whole-dossier/all-historical-discussion rereading below and
in docs/AGENTS-MAILBOX-PROTO.md for this team; never omit pending obligations,
new owner decisions, relevant evidence or unresolved review findings.

At a safe handoff, maintain a durable checkpoint before supported runner
compaction or context replacement. Preserve participant identity, exclusive
readiness consumption and claim safety; never reset an active worker or start
a duplicate consumer. Compaction/replacement requires a verified supported
runner operation, not deletion of session files. A claimed turn limit must name
observed runner/provider evidence; normal end_turn is not proof of exhaustion.

Owner ruling 2026-09-26: every major milestone requires a human-owned Git
checkpoint, including completed independently reviewed Jobs and major accepted
slices. This supersedes the earlier merely optional/practical milestone-WIP
wording. At the milestone handoff, agents must identify the checkpoint due,
prepare a truthful change/verification summary and a concrete commit message
for Slawomir, and record the commit identity after observing the human's commit.
Carry a pending checkpoint explicitly in the current PLAN/handoff until it is
fulfilled. Do not silently forget it or describe a proposed commit as made.
Routine correction passes are not each a new major milestone. Durable checkpointing
before supported context replacement remains required as described above.

Agents never stage, commit or otherwise mutate Git state. A Git checkpoint is
a recovery aid, not acceptance evidence. Human absence is not a performance
defect. Decision and first explicitly named milestone:
[Required milestone checkpoints](work/records/2026/09/finding-v12-design-alignment-audit/FINDING.md#2026-09-26--every-major-milestone-requires-a-human-git-checkpoint).

For early v12 workflow improvements, carry explicit continuation/correction/
acceptance/owner-decision outcomes, durable continuation checkpoints and safe
context maintenance into Jobs. These improvements are not extra adoption gates;
initial adoption still follows independent review and concrete parallel-Job proof.

## Non-interactive managed turns

- On every Work readiness turn, read current canonical state with `detail` and
  succeed at the standalone claim before Work execution. Then read the complete
  current handoff comments through `work-events` and all associated discussion
  through the `thread` locators in `detail`, following pagination. Do not filter
  away comments, thread locators, messages or continuation instructions. Read
  the bound dossier and revalidate its current scope before editing.
- Continue authorized work within the live turn. Never end a turn holding a
  Work claim, even after recording progress. Successfully pass completed work
  for independent review or return incomplete work through `baton.bug`, carrying
  exact remaining scope, evidence and cumulative verification spending. Before
  any final response, confirm through canonical state that you no longer hold
  the claim. If handoff fails, resolve or report the exact operational blocker
  within the live turn; owner release and redelivery are exceptional recovery,
  never normal work cadence. Preserve partial work and cumulative budgets.
- Every canonical Baton operation is
  ONE standalone direct execution request.
  This binds `claim` above all, because it is the mandatory first act. Issue
  it alone —
  never combined with `detail` or another read, another mutation, a shell
  wrapper, or shell control syntax such as `&&`, `;`, a pipe or a
  newline-separated batch. The deployment authorizes an EXACT canonical
  invocation, so a batch containing one is a different command and is not
  authorized: the read succeeds, the mutation is refused as a read-only
  database, and the Work stays unclaimed. An exact operation that still fails
  when issued alone is a deployment or policy incident — report it through
  Baton as one, and
  never retry it inside a broader command.
- A Codex context launched by readiness is non-interactive. It never requests
  escalation and never retries a denied command with
  `sandbox_permissions=require_escalated`; either act within its installed
  policy or report the exact blocker through Baton.
- Optional cleanup is never worth quarantining the participant. In particular,
  a managed reviewer leaves its exact temporary reproduction path for the
  operator instead of issuing a destructive shell command merely to remove
  it. Tests and repository helpers should clean up resources they own through
  their already-authorized execution boundary.
- If required verification cannot run without new authority, stop before the
  prohibited act, preserve the evidence, and relinquish or block the Work with
  an actionable explanation. Do not turn a permission refusal into a stronger
  command or an unattended approval request.

## Baton defects and workarounds

- Never work around a Baton defect without logging a finding for it first. Log the finding, then a short-term workaround is acceptable — but only as a stated stopgap, never as the fix, and the finding is what carries the real correction.
- This applies with particular force to agents working inside Baton's own source tree. Privileged access to the source and the store lets an agent reach past a gap that every other team hits head-on. Doing so hides the defect, produces a false report of success, and advances nothing: other teams have the CLI and nothing else, and cannot route around what this repository can.
- The finding states what was observed, separates what is genuinely Baton's defect from the agent's own misuse of the tool, and proposes a direction. Filing it is not optional because the workaround happened to be easy.


## Additional managed reviewer — owner 2026-09-18 UTC

Owner selects reviewer `rview-pc` (canonical `baton.rvpc`), role `rview`, as an additional Codex app-server reviewer using its own Codex home and separate supervised context/readiness consumer. This supersedes the sole-managed-reviewer wording above: `baton.codex` remains a reviewer and `baton.rvpc` joins the review pool after configuration acceptance. Resolve generic review handoffs through the configured route; each reviewer uses only its own participant identity and claims Work atomically. Never reuse another participant's context or readiness path. Coordinate exact file ownership before parallel changes; Claude must not overwrite Codex-owned files or changes, and reviewers must not overwrite each other's work. Historical reviews remain append-only. Prompt remains non-routable. Decision and deployment preparation: `work/records/2026/09/finding-rview-pc-reviewer/` (W200075).

Owner follow-up 2026-09-18 UTC: for now, all Baton rview routing goes through `baton.rvpc` alone. This supersedes the two-handler pool selection above once generation11 is accepted. Keep `baton.codex` registered but outside that route; do not interrupt existing claims. Other teams and non-review roles are unchanged.

## Human-plus-agent integration default — owner 2026-09-21

The owner clarifies that `baton.merge` is not the standard integration process. Humans plus an assisting agent review and integrate accepted results; automating integration is not a required product outcome or release gate. Do not infer a managed-integrator handoff from a generic request to integrate merely because that participant is configured. Use it only when specifically selected. This supersedes any default-workflow interpretation of the configured integrator descriptions above, while retaining their provenance/path/claim rules whenever that participant is selected. Git staging, commits and history remain Slawomir's. This clarification does not itself release a live claim, discard prepared work or change accepted proposal bytes. Decision history: `work/records/2026/09/finding-v12-initial-claude-worker-pool/FINDING.md`, 2026-09-21T14:09:14Z.

## Additional Codex implementer — owner 2026-09-21

Owner selects coder `codx-pc`, canonical `baton.codxpc` (six-cell member limit), role `impl`, backed by `/home/sl/.codex-pushcoin` in its own supervised context. After configuration acceptance, endpoint `baton.codx` routes through `implpc` exclusively to this implementer. Existing Claude and reviewer routes remain unchanged; `baton.rvpc` remains the independent reviewer. This supersedes any assumption that only Claude may implement: each implementer uses its exact launcher identity and a successful exclusive claim, preserves prior changes, and hands off for independent review. Adding this participant does not release Claude's failed claim or authorize concurrent edits to W177936. Decision and installation packet: `work/records/2026/09/finding-codx-pc-implementer/` (W232334).
