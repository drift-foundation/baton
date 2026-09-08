# Run a standalone multi-job v12 pipeline

Ledger Work: W71830

Related decisions: W2 and W62098.

## Observed — 2026-09-02

The v12 proof has established useful isolated pieces: manager authority,
container lifecycle, retained workspaces and results, independent review, and
bounded integration. Operating those pieces still requires Slawomir and the
interactive copilot to issue many transition-specific commands, prepare each
run, inspect receipts, recover orchestration state, and manually initiate the
next role. That is a component proof, not yet a standalone work system.

## Confirmed direction — 2026-09-02

The next product milestone is one persistent, host-side v12 Worker Manager
that accepts several Jobs and drives their ordinary lifecycle without an
operator acting as the scheduler. One submission is enough for the manager to
offer and claim Work, allocate isolated disk-backed workspaces, launch workers
on demand, retain outputs and logs, launch independent reviewers, return a
rejected checkpoint to the same private development line, and serialize
approved proposals through a dedicated integrator.

Implementation and review pools may run concurrently. Integration into one
canonical target is serialized. Independent Jobs may fork from the same
immutable source baseline; a dependent Job names its predecessor's accepted
commit and an explicit Work dependency. Workers and reviewers are disposable,
but a Work's private development line survives its correction cycle.

The initial v11 deployment remains only the external coordination ledger and
operator message bus while this milestone is built. It does not need a general
v11-to-v12 adapter. The operator may create one tracking Work, submit its
bounded input to v12, observe the v12 result, and close the v11 Work after the
result is reviewed. A native v12 scheduler and read-only status surface come
before a command-capable v12 TUI.

Ordinary success requires no per-transition shell commands. Human action is
reserved for product decisions, exceptional recovery, final Git ownership,
and conditions whose policy deliberately refuses automation. A wedged worker
is reported and contained; the first slice does not automatically discard,
accept, or reassign its output.

## Confirmed test-change authority — 2026-09-02

Tests are ordinary scheduled project files. When the accepted Work description
or plan explicitly authorizes adding, editing, or removing tests within a
bounded scope, that is the required case-specific approval. An implementer,
reviewer, or integrator must not stop later merely because the reviewed
proposal exercises that already granted authority, and a non-interactive turn
must never ask for redundant interactive approval.

The immutable review still enumerates and evaluates the actual changed paths
and binds its verdict to the candidate. Test deletion, weakened expectations,
or changed behaviour must be visible within the approved scope and review;
the Work description is not blanket permission for unrelated tests. A test
mutation absent from, or outside, that scheduled scope remains unexpected and
refuses before import. This clarifies the original guard: it protects against
unscheduled test changes, not against planned test work.

W71459 currently owns the affected v11 managed-integrator policy files. This
ruling must be incorporated there or applied after that ownership ends; no
parallel edit may race its active implementation.

## Minimal standalone acceptance

- A documented JSON/CLI submission starts at least two independent Jobs from
  one immutable baseline without transition-by-transition operator commands.
- The manager admits them through separate assignment/claim identities and
  runs at least two implementation containers concurrently in isolated,
  disk-backed workspaces.
- Each runtime receives an immutable read-only source mount, a separate
  writable workspace, durable output and log locations, and bounded scratch.
  The generic manager performs no Git operation and no mandatory source-tree
  copy, enumeration, or hash prelude.
- Each implementation produces an immutable review checkpoint and observable
  logs. Independent review runs in containers and binds its verdict to that
  checkpoint.
- At least one changes-requested cycle reuses the same private development
  line without another source clone or candidate-tree copy.
- Approved candidates enter one serialized integrator. The integrator checks
  provenance and target drift, imports only approved scope, and hands the
  prepared canonical diff to Slawomir without mutating Git history.
- One demonstration includes planned test-file modification and completes
  non-interactively; a companion out-of-scope test mutation refuses before
  changing the canonical target.
- A status command exposes queued, offered, claimed, running, reviewing,
  changes-requested, integrating, completed, and exceptional state together
  with runtime identity and safe log/activity locators.
- Failure of one Job does not wedge unrelated worker slots or require a full
  v11 stack restart.

## Deliberate non-goals for the first slice

- A complete interactive v12 TUI.
- Remote/SSH adapters beyond an explicit future profile seam.
- Fully automatic acceptance, conflict resolution, or wedged-output disposal.
- Exhaustive hardening before the two-Job vertical slice works end to end.
- Replacing Git ancestry or repository policy with Baton-specific lineage.

## Work shape

This record is a milestone and decomposition owner, not one giant coding
assignment. Before implementation it must create bounded leaf Work for the
manager control loop, source/workspace mounting, concurrent slots, persistent
review/correction cycles, serialized integration, and the end-to-end proof.
Each leaf reports visible progress independently and may be scheduled in
parallel only when its owned paths and prerequisites do not overlap.

## Reviewer component map — 2026-09-02

**Confirmed reusable capability:** the Python Worker Manager already has
restart-safe operations for concrete offers/claims, attempts and activation,
agent sessions, runtime start/reconciliation/cancellation, output freeze,
custody/intake/retention/cleanup, assignment workspaces, and per-Work runtime
lanes. The v12 authority separately owns Work/claim/proposal and verification,
review, approval, and integration receipts. These are the operations the new
manager must compose; they are not missing components to reimplement.

**Observed missing composition:** the manager store has no submitted Job or
pipeline-stage relation and there is no persistent process deriving and
performing the next eligible act. The only full-path executable,
`v12/python/tools/dogfood_operator.py`, is a supervised one-attempt command
whose operator supplies grants/evidence and whose terminal handoff returns to
v11 review. `parallel_test.py` is a test harness. Neither is a native multi-Job
scheduler or status surface.

**Confirmed existing ownership:** W62098 already owns both the zero-prelude
read-only source plus disk-backed manager-custodied workspace boundary and the
immutable-review-checkpoint/same-private-line correction cycle. It is the
bounded source/workspace and review-cycle leaf for this milestone even though
it predates and remains canonically separate from this umbrella. Creating two
new child dossiers for those same contracts would duplicate ownership, so the
decomposition links and gates on W62098 instead.

**Confirmed integration foundation:** W65212 established the distinct trusted
integrator and its bounded import/refusal/Git boundary, while v12 authority
already records integration attempts. What remains is scheduler-owned
single-target queueing and composition. W71459 owns the overlapping v11
managed-integrator test-change policy until its current handoff ends.

**Not critical-path prerequisites:** W61599's safe live-progress/log follow
hardening and W32577's deadline/race cleanup remain independently recorded.
The standalone status must expose safe locators and exceptional state, but the
two-Job happy-path proof does not wait for raw/native live-log UX or the full
defensive matrix unless a measured defect would make the proof false.

### Recorded decomposition

- W71875 owns the persistent Job manager, submitted stage state, restart loop,
  and CLI/JSON submit/status surface.
- W62098 remains the external source/workspace and persistent review-cycle
  leaf.
- W71877 owns concurrent implementation/review pool scheduling and is blocked
  on W71875's control-plane contract.
- W71878 owns serialized accepted-proposal integration and is blocked on
  W71875, W62098, and W71459.
- W71879 owns only the clean two-Job end-to-end proof and is blocked on W71875,
  W71877, W71878, and W62098.

This graph permits W71875 and W62098 to advance independently, preserves
review-ahead in their dossiers despite v11's coarse implementation gates, and
keeps the integrated demonstration from becoming a repair bucket.

## Decomposition correction — 2026-09-02

The “Confirmed existing ownership” and “Recorded decomposition” paragraphs
immediately above are **superseded** where they treat W62098 itself as the
implementation leaf. After that first map was recorded, the reviewer consumed
W62098 thread message 71842: its confirmed decisions are inputs to bounded
W71830 leaves, and W62098 must not be implemented as one monolithic
assignment.

The corrected six-child decomposition is:

- W71875: persistent Job manager and submit/status loop;
- W71917: immutable read-only source and disk-backed writable workspace,
  applying W62098's source/workspace rulings;
- W71877: concurrent implementation/review stage scheduling, blocked on
  W71875;
- W71918: immutable review checkpoints and same-line corrections, applying
  W62098's review-cycle rulings and blocked on W71875 and W71917;
- W71878: serialized integration, blocked on W71875, W71918, and W71459; and
- W71879: the clean end-to-end proof, blocked on W71875, W71917, W71877,
  W71918, and W71878.

The incorrect coarse W62098 dependencies on W71878 and W71879 were removed and
replaced with the exact child dependencies. W62098 remains the chronological
decision/evidence owner at low priority; W71830's children own implementation.
W71875 and W71917 were routed to `baton.ops` for isolated v12 execution.

## Confirmed worker-pool and affinity ruling — 2026-09-02

Implementation concurrency comes from multiple isolated worker sessions, not
from one session holding several assignments and not from duplicating static
profiles as `impl2`, `impl3`, and so on. A reusable runtime profile describes
the image, adapter, credentials provider, capabilities, resource policy, and
other launch posture. A pool may instantiate that profile several times, but
each live worker has its own logical worker identity, agent session, private
workspace, and at most one active assignment.

The first implementation assignment on a candidate line establishes durable
affinity between that candidate/workspace and its logical worker. Independent
Work may use other workers concurrently, but review returning changes to an
implementation line offers the new correction assignment to the same worker
identity and preserves its workspace and, when supported, its model session.
Review releases the implementation assignment; affinity is not a hidden claim
and does not let one worker hold several assignments.

The protocol and status surface distinguish three identities:

- `worker_id` is the durable logical agent/context used for affinity;
- `incarnation_id` identifies one concrete container/process start; and
- `assignment_id` identifies one offered-and-claimed execution episode.

A restarted container may therefore have a new incarnation while continuing
the same logical worker and candidate line. If that worker cannot be resumed,
the manager does not silently erase affinity or pretend a replacement is the
same worker. It reports the condition and follows an explicit fallback policy:
resume the candidate with a replacement worker, restart implementation, or
await operator direction. Additional runtime profiles are warranted only for
a materially different model, toolchain, credential source, resource class,
or security posture—not merely to obtain another concurrent slot.

## Bootstrap correction — 2026-09-03

The six-child ordering above assumed that W71875's persistent process could
launch W71917 as its first ordinary workload. Revalidation after integration
found that assumption false. The implemented Job Manager deliberately owns
only `admit` and `claim`: its deployment factory can issue and deliver a
bearer, but no production deployment composition currently turns the claimed
stage into a workspace-backed runtime. The source says runtime start waits on
W71917/W71877, while W71917 says it must execute through that runtime. That is
a bootstrap cycle, not an operator command that can be wished away.

The approved correction adds one bounded prerequisite leaf before W71917. It
builds the trusted, production deployment composition needed to drive one
claimed implementation stage into one live worker by composing existing
public Authority, Worker Manager, OCI adapter, credential, launch and legacy
workspace capabilities. This is the final v11-coordinated bootstrap exception:
it may use the existing bootstrap workspace boundary, but it must not call the
retired dogfood operator or create another complete candidate archive.

The new leaf owns no source/workspace redesign, pool scheduling, review loop,
or integration policy. W71917 remains the first ordinary self-hosted v12
workload and replaces the bootstrap workspace boundary with its approved
immutable-source and persistent-workspace contract. W71877 remains approved
but does not start implementation ahead of this bootstrap and W71917.

## Production stage-composition placement — 2026-09-06

The clean two-Job proof revalidated every accepted provider and found no
interface drift. It found a missing production composition instead: the
control plane can schedule implementation and review, but the only production
launcher drives one implementation worker and hands its result back to a v11
review Route. No production path launches the independent review runtime,
freezes and records its verdict, returns a changes-requested checkpoint to the
same private line, publishes the accepted proposal, or invokes serialized
integration.

The owner approved a separate high-priority composition provider under this
milestone. The proof remains an evidence-only leaf and must not absorb
credential, image, network, or deployment authority merely to make itself
pass. The provider is decomposed into a review/correction driver, a disjoint
proposal/integration driver, and a final shared composition assembly. The
first two may proceed concurrently under explicit path ownership; the shared
assembly follows them and is owned by the primary implementer. The two-Job
proof waits on the accepted provider and then reruns its entry gate unchanged.

## W71830 delivery takes precedence over speculative features — confirmed 2026-09-07

Slawomir emphasized that reaching W71830 is the immediate priority and that
delivery is being delayed by features whose necessity has not been demonstrated.
The critical path stays minimal and safe. A proposed addition must identify
the concrete failure or missing indispensable capability that prevents this
record's accepted standalone proof, and use the smallest correction that
resolves it. Generality, extensibility and hypothetical future failures do not
by themselves justify another prerequisite. Reuse accepted components and
existing evidence; keep optional improvements deferred in their owning records.

The general clean-verifier service proposed during W110772 planning is the
specific scope expansion being corrected. Its full service design is deferred;
W110772 must return the smallest honest verification arrangement and concrete
sealed-result/cleanup correction. Any necessary change to an existing acceptance
contract must be stated explicitly, with its limitation, rather than silently
manufacturing passing evidence. Isolation, authorized target access, independent
review and exact retained candidate/result evidence remain first-proof needs.

This confirms and strengthens the existing minimal-slice/non-goals boundary;
it does not add another architecture or planning milestone. Finish the necessary
stage composition, perform the accepted two-Job proof through W71879, and use
its observed failures to decide what further work is needed. W110934's OCI
safety review continues. W110772 scope-correction message111720 and its current
FINDING/PLAN carry the immediate coordination. Recorded by baton.prompt from
Slawomir's interactive direction; no implementation or execution grant added.

## Current verification is implementer testing plus review — confirmed 2026-09-07

Slawomir clarified the exact current delivery boundary: the implementer runs
the ordinary required tests (for example, `just test`), and the independent
reviewer may run additional or broader tests as needed. That is the verification
workflow for now. No separate verification agent, Job stage, service or clean
certification producer is required for W71830. The subsequently discussed
model-operated verification stage is a future option, not scheduled work.

This supersedes the earlier unresolved instruction to find a separate minimum
verification arrangement for this milestone, and defers the earlier clean
verification-context prerequisite insofar as it would require that additional
stage or producer before W71830. Ordinary test evidence and independent review
remain required; their results must be reported honestly. They must not be
represented as a separate clean certification that did not occur.

W110772 must reconcile its existing verification gate and documentation with
this explicit milestone decision alongside the actual sealed-output and
post-cleanup corrections. Do not clear the gate by synthesizing a passed
observation or reinstate a verifier project to preserve an obsolete milestone
assumption. The active Handler owns the corresponding detailed decision/plan
updates and bounded source/test proposal. Keep evidence history and identify
the exact changed expectations; this ruling is not blanket test-edit authority.
Recorded by baton.prompt while W110772 is actively held by baton.codex.

## Reviewer owns proactive decomposition judgment — confirmed 2026-09-07

Slawomir requested a standing EFFECTIVE-BATON rule so he need not repeatedly
notice oversized Jobs and request a split himself. He selected the reviewer
as the best owner of that judgment and authorized the documentation change.
The W110772 partial handbacks, its explicit lifecycle/ordinary-test split and
the later proof-only takeover motivate this rule; they do not add another
milestone or change any current claim.

Clarify the guide's existing "Campaigns contain bounded Jobs" rule: reviewers
assess decomposition at initial plan review and when a material partial
handback, scope expansion or independent deliverable appears. By the second
implementation/review cycle that leaves substantial accepted work incomplete,
record a split-or-continue decision without waiting for an operator prompt.
This is a mandatory judgment point, not a mandatory numeric split. A narrow
converging correction can remain whole with a concrete reason and next outcome;
reassignment alone does not reset the incomplete-handback count.

The decision distinguishes independently acceptable outcomes from one coherent
multi-file correction, proposes exact ownership/dependencies and one joined
acceptance check where needed, and considers other eligible capacity or a
bounded tuner assignment. Required proof stays with its promised capability;
optional features remain deferred. Do not add Work merely to hide incomplete
acceptance or make the critical path appear shorter.

Existing claim, scope and route authority remains unchanged. The reviewer may
enact an already authorized split at a safe handoff; otherwise it returns one
concrete allocation for the exact additional authority needed. Do not rewrite
scope underneath a live Handler or introduce a new planning-only approval loop.
Recorded by baton.prompt before editing docs/EFFECTIVE-BATON.md.

### Same-session clarification — splitting is the default after failure or gaps

Slawomir corrected the burden of proof: repeated unsuccessful reviews or exposed
substantial work gaps must trigger splitting, rather than require someone to
prove a split would help. This supersedes the open-ended split-or-continue
framing above. The reviewer must either split at the safe handoff or record a
specific justified exception before routing another undivided implementation
pass. Two successive non-accepting implementation/review cycles are the latest
decision point; an exposed substantial omitted deliverable triggers it earlier.

A continue exception must identify the exact remaining acceptance and evidence
that no useful independent piece can be separated, or a concrete shared change
that must be completed together. State the bounded next deliverable and reassess
at its handback. Confidence, convenience, vague coordination cost or "almost
done" do not discharge that burden. Reassignment does not reset the trigger.
Existing claim/scope authority and the minimum safe milestone boundary remain.

## State the evidence need before running tests — confirmed 2026-09-07

Slawomir approved making "before running tests, state what new question the run
answers" an explicit EFFECTIVE-BATON requirement. This strengthens the existing
two-stage cadence and reviewer evidence-reuse rules; it does not require another
approval or waive any required verification gate.

Before a test command or a named batch answering one question, every executing
role records the concrete question, selected scope and why existing evidence
does not answer it for the current candidate. The reason precedes execution;
routine role-based repetition, habit or reassurance is insufficient. Reuse
adequate retained evidence and choose the smallest run that resolves an actual
gap. A repeat must identify the relevant changed bytes/environment, missing or
unusable evidence, or independently required boundary that makes it informative.

W112029's repeated broad sweeps while its assigned component proof remained
absent illustrate the scheduling problem. Finish the missing focused acceptance
before another broad sweep unless that sweep answers a separate named blocking
question. Record results against the stated question and retain unresolved
failures honestly. This is an agent operating rule, not new CLI enforcement.
Recorded by baton.prompt before the guide edit.

### Same-session clarification — focus on cumulative test cost

Slawomir clarified that the mandatory pre-run justification targets larger
tests, suites and series of tests that consume material time. Quick targeted
one-off probes usually need no separate ceremony. This supersedes the universal
per-command wording above. Apply the requirement to suites, broad sweeps and
any individual run or planned series expected to consume about a minute or
more; assess cumulative cost rather than treating each command as an exemption.
State an approximate budget and the evidence question before that campaign,
then reassess repeated or growing campaigns before spending more time. Reuse
valid evidence; report cheap probes normally without a separate justification
entry for each. No required gate or failed result is waived.

## 2026-09-08 — critical-path preparation approved

Slawomir approved preparing the next port/assembly handoff and demonstration
checklist while the current worker review finishes. W110774's bound record now
owns HANDOFF-CONTRACT-2026-09-08.md and the separately approved normal-continuation
driver extension. W103083 retains shared assembly and one-Job custody proof.
Implementation follows existing claims and accepted-provider gates; this ruling
adds no separate Work or review campaign. Every acceptance recommendation should
include the exact operator closure command and identify what closure releases.

The proof preparation is in findings/finding-two-job-pipeline-proof/
PREPARATION-2026-09-08.md. It is a pre-freeze checklist, not a passed run or live
execution authority. The possible third fault Job is explicitly proposed pending
owner guidance; earlier approved acceptance requirements remain in force.

## 2026-09-08 — demonstration plan approved

Slawomir approved PREPARATION-2026-09-08.md in the W71879 record, including
two Jobs intended to complete and a third small Job carrying the deliberate
failure, all in one submission. This supersedes the earlier pending scenario
question and exact-two-document wording of the demonstration plan. Both successful
integrations, required runtime overlaps, independent review/correction, scoped
test modification, companion refusal and failure containment remain mandatory.
No automatic retry, ordinary operator transition or stack restart repairs the run.
The final base, exact paths/documents, deployment identities, commands, metrics
and budgets still require the existing concrete freeze and material-delta review;
this approval is not a claim that the demonstration ran or passed.

## 2026-09-08 — model judgement for permitted change scope

Slawomir confirmed that this milestone should rely on the integrator model to
judge whether candidate changes fall within the permitted scope. He declined
spending substantial time on mechanical enforcement now. The prompt's proposed
deterministic file-and-operation allowlist is superseded and is not a W71830
prerequisite. Owning detail is findings/finding-two-job-pipeline-proof/FINDING.md,
"integrator model decides permitted change scope". W115604 is narrowed to the
selected model boundary and a minimal scenario using existing capabilities;
retain honest observed evidence and existing identity/review/preflight checks.

## 2026-09-08 — protect critical-path execution and review capacity

Slawomir directed prompt to optimize the critical path after observing that
High-priority tuner remediation competes for the single reviewer's time.
Keep direct W71830 prerequisites High; lower the separate remediation program's
High items to Normal, preserving existing Low items. Post-demonstration W103525
certification also becomes Normal. This supersedes equal-High treatment of
those activities, not their scope, evidence requirements or ultimate completion.
At snapshot119148 the recorded sequence is W119113 preparation, W119114
composed one-Job lifecycle/custody proof, then W103083 joined acceptance.
The approved W115599 successor placement and W115604 evidence decision should
be pinned and prepared while Claude executes, so multi-Job composition is ready
after assembly acceptance. Final freeze and the actual demonstration remain
gated on accepted capability. Preserve independent review, use focused checks,
and do not add exhaustive certification or repeat whole suites per small fix.
Priority is an ordering signal, not preemption: finish a bounded held review,
then prefer ready critical-path work over repair reviews. Newly created
noncritical repair children keep Normal priority unless an observed blocker
justifies promotion. No lifecycle release or new implementation authority follows.
