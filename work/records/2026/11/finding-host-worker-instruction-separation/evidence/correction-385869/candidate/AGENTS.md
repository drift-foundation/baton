# Baton host agent instructions

## Execution context

These are instructions for host agents developing Baton and coordinating through
v11. They apply when editing any source directory, including `v12/`. Directory
placement, a container, or a role name alone never changes execution authority.
A native v12 worker instead follows its explicitly delivered execution contract
and [worker instructions](docs/V12-WORKER-INSTRUCTIONS.md). Host-only claim,
dossier and protected-main Git procedures below are not its inner task loop.
Shared safety, task scope, honest evidence and protected-main boundaries still
apply. A mounted main checkout remains protected inside a container.

Use the actual launcher participant and explicit role; never impersonate another
participant. Follow the current canonical assignment and explicit owner decisions.
Keep history and temporary exceptions in the owning dossier. An explicit owner
exception recorded there governs only within its stated scope and lifetime.
Revalidate it before acting; never infer one from a blocker or extend it to sibling
or successor Work. Moving a ruling neither revokes it nor revives an expired one.

## Git, files and recovery

Slawomir alone owns the protected development repository's index, commits,
branches, tags, history and publication. Agents may inspect history/status/diffs
and edit authorized filesystem content, but never stage, unstage, commit, merge,
rebase, cherry-pick, reset, switch/checkout, stash, change branches/tags or push
that repository. “Ready,” “clean” and “committable” mean prepare and verify the
filesystem diff and report it; they do not grant Git mutation authority.

Within authorized work, Git mutations are permitted in real disposable fixture
repositories, isolated disposable staging copies and container execution
repositories: initialization, staging, commits, branches, merges, checkout/reset/
clean, local fetch and proposal/bundle creation need no extra command/test approval.
Staging copies are disposable working copies, not the protected index. Verify: no mutations through shared Git metadata, linked worktrees, mounts,
symlinks or remote pushes into protected repositories. Docker does not turn a
mounted development checkout into a disposable repository. This permission does
not select a live Job, deployment or broader scope.

Follow [development storage](docs/DEVELOPMENT-STORAGE.md). Preserve source,
fixtures, decisions, checkpoints and required evidence for recovery on another
computer. Use ignored disk-backed `work/scratch/` for disposable work; `/tmp` is
only for short-lived temporary files. Promote required evidence before cleanup
or handoff; scratch, a local commit and a digest alone are not durable backups.
Never blanket-ignore/delete unclassified dossier contents to make status clean.
Preserve uncertain artifacts and report recovery requirements. Keep credentials
out of ordinary artifacts and logs. Cleanup names owned disposable paths; optional
cleanup is never worth a destructive command or quarantining a participant.

Avoid wrapping long expressions merely for readability and avoid indentation
churn, especially in deeply nested code. Preserve others' edits. Before parallel
edits establish actual file ownership; coordinate overlap rather than overwriting.

## Product scope and development workflow

Read [v12/DESIGN.md](v12/DESIGN.md) before planning, implementing or reviewing v12
changes. It is the normative target, not a description of running v11 or a current
code inventory. Align acceptance with it; report concrete code/spec gaps instead
of weakening the spec to match implementation. Owner-approved specification
changes must be pinned in the owning FINDING and reflected in DESIGN before
implementation. Existing code, old proofs and passing subsets do not redefine it.

Deliver reliable independent parallel Jobs, isolation, recovery, attribution,
honest independently reviewed results, working context reuse and a lightweight
read-only monitor. Fresh isolated recovery remains supported. Context reuse is a
v12 deliverable, not a gate on initial adoption of accepted fresh-context Jobs.
Broader stress/performance, advanced scheduling/shared capacity, distributed
execution, richer TUI and broad consolidation/refactoring belong to later work.
Known work loss, duplicate effects, isolation, cleanup, attribution and false
success needed by the selected path are not deferred by calling them hardening.
No broad supervisor refactor or automatic integration is implied.

Implement, correct and verify ordinary authorized development directly under the
v11 claim protocol. Native v12 Jobs and bespoke launch packets are not required
for that development. Reuse retained candidates and focused evidence. Tests of
v12 orchestration still exercise the product boundary when needed. Existing live
provider, engine, deployment and selected execution boundaries remain; no live
run, install, deployment, takeover or protected Git mutation is implied.

Prioritize useful parallel delivery where scope, accepted inputs and actual
file/output ownership permit it. Preserve dependency gates and serialize overlap
and integration. Multiple claims or sessions alone are not parallel execution
proof. Native v12 coordination and execution remain the destination; v11 is the
one current coordination authority until explicit supported cutover. Preserve
existing Work identities and permanent records, classify changes explicitly,
and install scheduling relationships in the graph. Do not copy the backlog to a
second authority, silently reroute active work or build a permanent bridge merely
to preserve the temporary workflow. Preserve in-flight execution at safe boundaries.

## Verification and test authority

Read and follow [v12/python/TESTING.md](v12/python/TESTING.md) for all v12 test
writing, repair, selection and reporting. Declare affected logical groups. Use
its supported focused `just test-one` / `just test-group GROUP` recipes and
prepared interpreter, never an ambient interpreter. The guide owns current
invocation locations, registries, environment and accounting details.

Every test is required unless its exact id is in `OPTIONAL_SKIPS` with an owner
ruling. Unregistered skips, fixture skips/errors and never-started tests fail an
accounted run. New modules belong to exactly one execution registry and one group;
do not bind another module's test classes. Retain the log, JSON ledger and source
identity/header together; counts without collected counts do not prove coverage.
A full suite is a separately selected integration checkpoint, not routine
verification; retry after a fix is another selected checkpoint.

Agents in every role may add, edit, replace or remove tests, fixtures, assertions,
expected behavior and registry entries needed for the authorized outcome without
per-test/helper/path approval. Record affected paths and reasons in the owning
plan/handoff and coordinate ownership. This is documentation, not another gate.
Independent review evaluates changed expectations against accepted behavior;
never waive required acceptance or remove genuine defect coverage just to pass.
Scope, execution selection and exact reviewed-byte import remain required.

Use deterministic fake/replay providers and focused local tests by default.
Simulate at the normal provider boundary while exercising real affected owners,
coordination, runtime, workspace, merge, verification and final-result behavior.
Label simulations; never fabricate owner receipts or claim live coverage from a
fixture. Live models are for a selected question requiring the real provider
(authentication, protocol or model-dependent behavior). State that question and
why deterministic evidence cannot answer it. Reuse applicable live evidence;
integration/end-to-end labels or a handoff are not reasons for a live call.

Cumulative stopwatch budgets are not approval gates for ordinary focused
verification. Do not request replenishment solely because an old allowance is
exhausted or historically unknown. Use sensible per-run timeouts with termination
and cleanup time, record measured durations, and label estimates/unknowns. Do not
manufacture bounds, erase cost or treat missing seconds as proof processes ended.
Investigate concrete resource uncertainty. This does not change product Job
limits, waive a selected supervisor limit, authorize an excluded run/rerun or
select broad stress, live models or actual engine operations outside scope.

## Coordination and identity

Before consuming or publishing handoffs, read
[docs/AGENTS-MAILBOX-PROTO.md](docs/AGENTS-MAILBOX-PROTO.md) in full. Deployment
supplies the executable and explicit absolute config path: never infer either
from cwd or hard-code host deployment paths in policy. Use supported canonical
operations, never direct SQLite reads/writes or manual protocol reconstruction.
If an operation can only be answered by opening the store, report the missing
supported capability as a finding.

Launches name one participant and one explicit role. Identities:

| Participant | Responsibility |
| --- | --- |
| `baton.prompt` | Human-attached interactive copilot and coordinator; not a Route handler |
| `baton.rvpc` | Configured independent review handler |
| `baton.codex` | Registered reviewer outside the currently selected review route |
| `baton.claude` | Implementer identity; use canonical configured endpoint resolution |
| `baton.codxpc` | Additional implementer, selected by `baton.codx` / `implpc` |
| `baton.merge` | Distinct optional integration context |
| `baton.slaw` | Approver and human Git owner |
| `baton.tuner` | Final polish |

Resolve role-only instructions through the configured route and this team's
identities, never another domain or a guessed alias. Canonical state decides
which handler is eligible. Preserve existing claims when configuration changes.
Keep participant homes, contexts and readiness consumers separate. No hidden second
context or shared foreground/background identity. Publish only the mapped runtime;
visibility grants no readiness authority. Prompt discusses/coordinates but never
consumes managed readiness or impersonates a handler. Operator recommendations
include exact actionable commands, prerequisites, expected outcomes and separate
approval boundaries; a recommendation is not execution authority.

Prompt may coordinate routine scope-preserving continuation, correction,
ownership, handoff and checkpointing. Specification changes require Slawomir's
explicit approval. Routine review corrections pass directly to the configured
implementation endpoint (currently `baton.impl`); use an explicit destination,
not an old `next=baton.decide`. Accepted delivery returns to the owner. Preserve
explicit owner sequencing and independent review. Escalate only a concrete
unresolved scope, product or authority decision with the blocked operation.

## Claim, execution and handoff

Read current canonical detail, then succeed at atomic `claim` before execution.
Route says who may claim; Handler records who is executing; Next is only the
planned successor. Readiness/discussion are not claims. `active` means claimed; `queued` is runnable,
`block` names a gate, `parked` is deferred; terminal Work has no phase. Competing
claims fail closed. No implicit takeover.

Issue each canonical Baton operation as ONE standalone direct execution request,
especially `claim`. Do not combine it with another read/mutation or wrap it in
shell control syntax, pipelines or newline batches. A denied exact invocation is
a deployment/policy incident; do not retry it in a stronger or broader wrapper.
Managed readiness turns are non-interactive: no escalation or unattended approval
request. Preserve a blocked operation and report it through supported Baton paths.

After claiming, read the complete current handoff via `work-events`, its thread
locators, current canonical scope/ownership/checkpoint, latest review and new
discussion and obligations since that checkpoint, following pagination. Record
the last message/event position read. Read the current bound record fresh and
revalidate captured claims. Expand into referenced/conflicting history when the
checkpoint is missing, stale or ambiguous. This targeted current-state reading
supersedes blanket rereading of all historical discussion or dossier material in
older procedural text; never omit new decisions or unresolved findings.

Claim means begin and continue authorized work, not wait for another go. Keep
one active readiness path per participant, never concurrent waits. `wait` is
read-only and claims nothing. Act on every wake in the same live turn; use the
supported response/acceptance/disposition verbs for directed obligations and
mark-seen for acknowledgments. Re-arm after each result while serving readiness;
terminal completion alone may not schedule another model turn. Answer pokes and
keep adapter runtime refresh requests with the adapter, as the protocol specifies.

Never end a turn holding a claim. Post the result in the owning thread and pass
completed work for independent review. If unable to continue, preserve an exact checkpoint and return incomplete work
through the authorized route (managed failure: `baton.bug`), naming remaining
scope, evidence, verification spending and blocked operation. A pass atomically releases
the claim; verify canonical Handler is cleared before final response. Resolve or
report a failed handoff in the live turn. Owner release/redelivery is exceptional
recovery, not normal cadence. Partial progress is not a new owner approval gate.

Handoffs use short labelled bullets: outcome; confirmed blocker and exact code
location; required change distinguished from suggestions; verification behaviors
and relevant failures; handoff condition. Name one bounded next milestone and
link the current PLAN rather than repeat the backlog. Code locations are evidence,
not an exclusive file-edit list. Verification is outcome-based; suggested commands
are optional unless an actual execution boundary applies. Continue through
focused verification instead of routinely returning partial edits.

## Permanent records and decisions

Baton discussion is coordination evidence, not the durable specification. Pin
confirmed product, UX, protocol and operational rulings in the owning FINDING
before implementation and update the current PLAN. Revalidate against current
code/protocol/later rulings. Append dated explicit supersession and rationale;
never silently rewrite history or leave contradictory rules both current.
Handoffs reference exact decision files. After restart recover from records,
not memory or a subject line. Log a Baton defect before any workaround, distinguish
misuse from a defect, label a stopgap and retain the real correction. Privileged
source/store access is not a substitute for supported user operations.

Dossiers are permanent canonical `work/records/YYYY/MM/finding-<stable-name>/`
records, created once and never moved, renamed, archived or deleted by lifecycle.
Bindings and handoffs use configured repository identity plus that relative
canonical path, never absolute paths, `work/open/` or a commit as primary locator.
`work/open/` relative symlinks are optional human navigation, not protocol state;
unlinking one never removes its record. Do not create new legacy `work/finding-*`
folders. Preserve existing records and explicit forwarding history.

Each dossier has exactly one corresponding authoritative Work. Create both
together, or bind a research-created dossier immediately before further work or
handoff. Deferred findings are parked on the ledger, not left off-ledger.
Lightweight Work need not have a dossier or open symlink. Later corrections to
terminal records are explicit follow-up history. A parent cannot close with an
open contained child.

The current host dossier procedure permits causally tied children at
`.../finding-parent/findings/finding-child/` with their own FINDING, PLAN and
PROGRESS. Name parent/discovery context and index child status in the parent.
Independent or separately scheduled work may use a top-level record. Avoid dotted
or numbered hierarchy names and more than two child levels; promotion creates a
new record with a forwarding note, never rewrites the old locator. Native v12's
flat-record target is governed by DESIGN; directory ancestry never installs a
scheduling dependency.

FINDING preserves chronological observations, decisions and reasoning. PLAN names
accepted facts, current state, one next executable milestone, ownership,
review/evidence references and concrete blockers. PROGRESS is an attributable
implementation account with one current writer: whoever actually implements
under the claim, not a permanently reserved participant. Append each author's
entry; reviewers who only discuss/review write findings, plans, evidence or
append-only review journals instead. Preserve prior accounts.

Each review is a new `review-YYYY-MM-DDTHH-MM-SSZ.md` at the record root; never
edit/delete an earlier review. Implementers record response and current review
state in PROGRESS. Handoffs point to FINDING, PLAN, PROGRESS and newest review.
Tests, user docs and durable policy that must stand alone live in normal product
locations, not hidden in dossiers. Keep transient identities, exceptions and deployment recipes out of shared
methodology (`docs/EFFECTIVE-BATON.md`); operations belong in reference manuals.

## Review, decomposition, integration and checkpoints

Reviewer enrichment makes bounded work executable: minimal repro/baseline, exact
symbols, observed versus confirmed versus inferred/proposed/open claims, bounded
patch direction, interactions, positive/negative/race/retry acceptance and real
unresolved decisions. Revalidate at execution; append resolved/superseded outcomes
for stale claims instead of deleting history or reimplementing fixes. Discovery
is role-neutral and recursive; filing a defect does not silently interrupt the
current serial item. Human/reviewer own formal priority/enrichment by default.

Reviewers proactively assess decomposition at assignment start and when repeated
handoffs fail to converge. Split distinct independently deliverable outcomes;
keep tightly coupled correction together. Pin rationale, finite outcomes, exact
file ownership, acceptance and joined consumer in FINDING/PLAN. Coordinate before
changing an active executor's allocation. Authorized v11 handlers create child
Work and real dependency edges through supported operations and read back the
graph before dependent execution. Route the first executable slice without an
extra routine approval round; keep the umbrella open through joined acceptance.
Do not expand scope, weaken acceptance, take over claims or mutate protected Git.
For v12, verify its actual ownership/dependency mechanisms rather than transplant
v11 commands or Route assumptions.

Human plus agent integration is the default. Managed `baton.merge` is used only
when explicitly selected; it is not an alias for implementation/review/approval
or a mandatory release gate. Any import checks independently reviewed exact
candidate bytes, base, path set, target drift and ownership. Never correct or
redesign content while claiming to import the accepted candidate.

When selected as managed integrator, read and follow the complete
[host integration procedure](docs/HOST-INTEGRATION.md) before any write. Its
whole-path authority, exact-byte review, test-path and target-mode preflight
requirements are mandatory; refuse before import if any check fails.

Every major accepted milestone requires a human Git checkpoint. Prepare a truthful
change/verification summary and concrete commit message; carry it pending in the
PLAN/handoff until observing the human commit and recording its identity. Routine corrections are not major milestones. Checkpoints aid recovery, not
acceptance; human absence is not a performance defect.

Before supported compaction/context replacement, preserve a durable concise
checkpoint including identity, scope, owned paths, candidate/evidence, pending
obligations and claim/runtime state. Preserve exclusive readiness and claim
safety. Verify the runner operation is supported; never delete session files,
reset an active worker or launch a duplicate consumer. A claimed runner/provider
limit needs observed evidence; ordinary end_turn is not exhaustion. Native
workflow improvements must carry explicit continuation/correction/acceptance/
owner-decision outcomes without becoming extra adoption gates.
