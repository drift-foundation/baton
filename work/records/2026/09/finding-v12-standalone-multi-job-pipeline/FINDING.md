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
