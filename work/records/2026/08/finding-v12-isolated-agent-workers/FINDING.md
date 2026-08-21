# Finding: v12 isolated agent workers and gated integration

## Status

Confirmed operational direction for Baton v12. This record is a roadmap, not
authorization to change the v11 runtime or its current shared-checkout rules.

The original authoritative Baton Work was `W193` (`bec445ce-W193`), low
priority and parked until the v11 cutover and stabilization work completed.
That authority was retired. The record was recreated without message-history
migration as `W2` (`bcbb9dbf-W2`) on 2026-08-19. That authority was retired at
the schema-25 rollover. The record was recreated again without message-history
migration as current Work `W2` (`5f717eee-W2`) on 2026-08-20; that Work is the
one current ledger authority for this dossier.

On 2026-08-18, the project also confirmed the general invariant exposed by
this record's initial omission: every finding dossier must have exactly one
corresponding Baton Work bound to its canonical record path. Roadmap findings
remain visible by being parked; they are not kept off-ledger.

## Motivation

The v11 trial coordinates claims and handoffs authoritatively, but agents still
execute in one writable checkout. A provider can fail after claiming Work, a
replacement can be assigned, and the original process can later recover and
continue writing. Baton can fence late protocol operations, but it cannot fence
direct filesystem writes from an already-running process. Independent agents
can also change the same review target underneath one another.

The live W154/W155 review on 2026-08-18 demonstrated the latter failure mode:
W154 returned for review against the two-level Work tree, while W155 changed
the shared tree to three levels. W154's focused regression then observed a
different implementation boundary from the one it had been written against.

The W2938 design supersession on 2026-08-20 demonstrated the cancellation
failure directly. Claude had correctly claimed W2938 and begun editing the
shared checkout from the then-pinned Work-level Claim-column contract. The
approver subsequently ruled that claim-overdue belongs to one agent, not to N
Jobs. The reviewer could publish a stop message and poke, but could not mutate
or block claimed Work because only the current Handler owns its lifecycle;
while those notices waited for the active model turn, the worker continued
editing source and tests against the superseded contract. Terminating the
shared runner would stop future writes but could neither erase only that
attempt's edits safely nor prove which overlapping files belonged to it.

This is not a reason to weaken Handler authority. It is evidence that control
revocation and filesystem isolation must be the same operation in v12: revoke
the exact assignment generation, cancel/terminate its worker, fence later
publication, and discard or quarantine only its private checkout. Accepted
work and every other attempt remain untouched even if the stopped model never
cooperates with a graceful release.

## Confirmed v12 operational model

Each Work assignment executes as a disposable, isolated worker:

- one container or equivalently strong isolation boundary;
- one independent repository checkout, not a writable worktree sharing the
  canonical repository's Git metadata;
- one immutable base revision and one unique assignment generation/claim
  epoch;
- explicit role instructions, policy, toolchain, resource limits, repository
  roots, and scoped credentials;
- no ability to write the canonical checkout, canonical Git refs, or another
  worker's workspace.

**Scope clarification and partial supersession — 2026-08-20:** the requirement
that every assignment own a repository checkout is superseded by "Typed
assignment input sources" below. Every assignment owns an isolated private
workspace, but only a `git` source produces a repository checkout. Directory
and later source types retain the same isolation, immutable-input, fencing and
review boundaries without inventing Git state for non-Git Work.

The worker does not "finish" by modifying production state. It publishes a
candidate containing:

- a commit range or equivalent immutable patch/bundle;
- the base revision and assignment generation that produced it;
- focused and broad test evidence;
- dossier/progress updates and relevant logs;
- an explicit completion or inability-to-complete disposition.

An integration authority reviews the candidate and explicitly accepts,
rejects, or returns it for revision. Only that authority changes the canonical
repository. Agent-created commits are proposal artifacts in disposable worker
repositories, not canonical history.

## Unified agent boundary

Every model/vendor CLI is wrapped behind one model-neutral worker surface.
ACP is the common interaction boundary for agent sessions and turns; whether
the implementation underneath is Claude, Gemini, Codex, or another CLI is not
a Baton protocol concern.

ACP is not stretched into a container or Git lifecycle protocol. A small Baton
worker-control layer owns:

- create/start/cancel/stop/status;
- assignment and claim-epoch fencing;
- input manifest delivery;
- event, heartbeat, and log collection;
- candidate artifact publication;
- integration disposition and workspace retention.

Thus every agent can behave as an ACP agent while the supervisor, rather than
the model adapter, owns isolation and authoritative job lifecycle.

## Failure, recovery, and late workers

Failover is a fenced takeover, never an ordinary reroute:

1. Cancel/stop the original worker and seek a positive quiescence result.
2. Atomically revoke its exact claim epoch with compare-and-swap recovery.
3. Mint a new assignment generation and start a new isolated worker from the
   selected base revision.
4. Accept candidate publication only from the current generation.

If the original worker later returns, its generation is stale. It cannot
modify the replacement's checkout or submit an acceptable candidate. Its local
work is disposable by default. An operator may retain it briefly and salvage
evidence or a patch manually, but Baton never merges or revives it
automatically.

This deliberately trades some duplicated work for single-writer safety and a
reviewable integration boundary.

## Claim-gated execution — confirmed 2026-08-19

The W93 slice-4 return exposed the remaining v11 boundary directly:
`baton.claude` received the complete Work, edited its dossier and source, and
ran the full gate without ever claiming W93. The authority correctly continued
to show the Work queued and unclaimed, but a shared writable checkout gave the
protocol no mechanism to prevent execution outside that state.

V12 does **not** hide Work details to address this. Inspection needs the full
contract and evidence, and Baton's open collaboration model permits members to
read and discuss linked Work without owning it. Visibility and execution are
separate boundaries:

- an eligible agent may inspect the complete Work through a read-only worker;
- only a successful claim mints the participant/Work/assignment-generation
  capability that unlocks a writable worker;
- execution tools, candidate publication, and workflow revision require that
  live capability; and
- release, replacement, or claim revocation removes write and publication
  authority even if the provider process later recovers.

This is deliberately deferred to v12. V11 retains its documented
claim-before-execution rule, but the shared checkout cannot enforce it and the
project will not spend the stabilization cycle pretending otherwise.

### V11 enforcement boundary — clarified 2026-08-20

This clarification supersedes only the broad reading of the preceding v11
limitation; the historical incidents and the v12 capability boundary remain
authoritative. V11 now enforces claim before `pass` or terminal `close`, so an
unclaimed participant cannot complete Baton's authoritative execution
lifecycle. That is the strongest useful correction within v11.

V11 still cannot prevent a process from reading the full Work contract,
editing the shared writable checkout, or running tests before it claims. That
filesystem boundary is an accepted v11 limitation, not another v11 work item.
V12 corrects it by making writable execution and candidate publication
capabilities consequences of the exact successful claim.

### Assignment-generation identity — confirmed 2026-08-20

The successful atomic `claim` action generates the assignment-generation ID.
An offer, readiness episode, worker-process start, runtime incarnation, or
configuration acceptance cannot generate it, and an old ID is never reused.
The ID is a monotonically increasing generation scoped to one Work; durable
manifests carry its full authority/Work/participant/generation identity while
clients may render a compact form such as `W2@g3`.

Compact Work, message, topic and assignment labels are UX conveniences only.
They are never persisted as identity, accepted as authoritative manifest
fields, or resolved implicitly by mutating protocol operations. Durable and
mutating references carry the full structured authority UUID, full Work ID,
participant and assignment generation as applicable. A client may display or
accept shorthand only to help a human choose, then must resolve and present the
full unambiguous identity before committing an operation.

The live claim and its generation are one fencing boundary. Release, pass,
terminal close, cancellation, or forced revocation invalidates that generation.
A later claim—including a reclaim by the same participant—generates the next
one. Candidate publication, writable execution capability, and test or proposal
evidence are accepted only for the current live generation, so a recovered
stale worker cannot publish over its replacement.

Exactly one worker runtime may execute under a live assignment generation. A
manager may reattach only when it can positively identify that same runtime;
otherwise it revokes the claim and requires a new claim and generation before
starting a replacement. Runtime attempt IDs, immutable proposal IDs,
`episode_seq`, participant runtime incarnation, and global configuration
generation remain separate identities with no claim authority.

### Proposal review, approval, and integration — confirmed 2026-08-20

Clean verification, technical review, approval, and integration are four
separate gates. Verification proves that one exact candidate tree passes its
required mechanical gates. A participant holding `rview` then judges technical
correctness, design, security, test adequacy, and the accompanying dossier
evidence. A participant holding `approv` separately authorizes that exact
reviewed candidate to enter the canonical repository. The trusted integrator
has no review discretion; it only performs the authorized compare-and-swap
update.

The reviewer receives a read-only workspace containing the exact candidate
tree, immutable proposal, dossier changes, and verifier results. Extra tests
are allowed, but the reviewer cannot edit the proposal. Review may accept,
request changes, or reject. A requested revision is a new immutable proposal
and must be verified and reviewed again; the old proposal is never rewritten.
Proposal rejection does not automatically close the Work, whose handler still
chooses its normal revision, non-satisfying, rejected, or cancelled lifecycle.

Review and approval records bind the proposal ID, candidate-tree digest,
verification result, target revision, and applicable policy generation. The
same participant may hold both `rview` and `approv` when configuration permits,
but the two actions remain distinct journaled decisions. If the canonical
target moves, integration refuses rather than resolving the conflict; the new
candidate is rebuilt and normally passes verification, review, and approval
again before integration.

### Git-mutation boundary at v12 cutover — confirmed 2026-08-20

**Scope clarified by "Gradual coexistence and rollout" below:** there is no
single global cutover. This exception activates only for an assignment running
under a certified isolated-worker profile. Participants still using the v11
shared-checkout path remain under the blanket Git-mutation prohibition during
the coexistence period.

The current blanket prohibition on agent Git mutation remains in force until
v12 isolation and capability enforcement are deployed. At that cutover the
rule becomes workspace-aware, not path-aware: agents still cannot mutate Git
in canonical checkouts, integration repositories, ordinary host sessions,
verifier workspaces, or reviewer workspaces.

A successfully claimed worker may mutate Git only inside the disposable
private proposal clone that the Worker Manager explicitly certifies for its
live assignment generation. It may change that clone's working tree, index,
local commits, and local branches and may refresh or rebase against the
manager-provided immutable target. The exception grants no authority to push,
change remotes, create canonical refs or tags, access writable canonical Git
storage, or integrate its own proposal. Publication goes through the Worker
Manager, and only the trusted integrator may import approved objects and
advance the canonical target by compare-and-swap.

Neither a pathname nor an agent's assertion establishes the exception. The
worker capability and certified runtime boundary do. The repository policy and
enforced worker cutover must change together so the future exception cannot be
misread as permission in today's shared checkout.

### Dossier ownership and plan rejection — confirmed 2026-08-20

An implementation assignment receives its committed `FINDING.md` and
`PLAN.md` as immutable inputs. The worker does not maintain a parent or
umbrella plan and does not rewrite its own plan during implementation. One live
claim permits one worker to update only its own record's implementer-owned
`PROGRESS.md` and add Work-scoped evidence. Parent status is derived from Baton
authority or updated separately by the parent's owner; `work/open/` maintenance
likewise belongs to trusted coordination tooling rather than worker proposals.

`PLAN.md` never carries mutable execution status. `PROGRESS.md` is the separate
execution journal: entries identify the assignment generation and record step
status, evidence, blockers, retries and handoff state without rewriting the
plan. A replacement generation appends its own attributable history rather
than editing away the prior attempt. Completion views derive current status
from that journal and canonical Baton events; a status transition alone is
never a plan revision.

This is a v12 cutover rule, not permission to violate today's repository
policy. The current `AGENTS.md` convention requiring queued/in-progress/done
marks in `PLAN.md` remains in force for the shared-checkout v11 process. At the
enforced v12 worker cutover, `AGENTS.md` and the PLAN/PROGRESS ownership split
change together; until then, agents continue the current convention.

### Assignment record output — confirmed 2026-08-20

After claim succeeds, every worker receives an assignment-generation-scoped
writable record-output area separate from both the read-only contract inputs
and its private source clone. The worker may place its `PROGRESS.md` journal,
research notes, reproductions, logs, fixtures, evidence and draft discovery
dossiers there. This is a logical manifest role, not a host pathname: a local
adapter may mount a directory while a remote adapter transfers the same
versioned artifact set over its control channel.

The area grants no direct write access to Baton's permanent record tree. The
trusted manager collects it, rejects path escape, symlink/reparse traversal,
unexpected file types, size/policy violations and detected credential leakage,
then binds accepted artifacts to the exact Work and assignment generation.
Normal progress/evidence becomes part of the immutable proposal or trusted
record materialization path. On cancellation or stale generation it is
preserved or quarantined according to policy and can never publish by itself.

A worker may prepare a complete discovered finding under this output area and
reference it from `file-discovery`. The manager uses that content to create the
new ledger Work and canonical dossier through the trusted materializer; the
draft's existence alone creates no Work, claim, dependency or lifecycle fact.

For the current Work, proposal publication collects the private source change
and validated record-output set into one immutable candidate. Verification,
technical review and approval bind both exact digests. On acceptance, the
trusted integrator materializes the worker-owned progress, research and
evidence at the Work's canonical record binding and advances the source target
as one atomic canonical commit/compare-and-swap. Nothing may be collected or
changed after approval without producing a new proposal revision and repeating
the gates. A record-output validation failure makes the proposal non-integrable.

Rejected or cancelled proposal output is retained or quarantined according to
policy and never silently enters the canonical record. A separately filed
discovery is not lost merely because its parent proposal is rejected: its own
ledger Work and materialization lifecycle remain independent once
`file-discovery` commits.

**Superseded in part by "Mounted output and trusted finding intake" below:**
the worker now writes to an adapter-provided mount rather than participating in
per-file transport, and a draft discovery does not create ledger Work until a
trusted intake agent accepts and materializes it. The generation-scoped output,
validation, sealing, joint review, and atomic current-Work integration rules
above remain authoritative.

### Live worker activity — confirmed 2026-08-20

An active worker is encouraged to emit meaningful structured activity updates
through the worker-control channel so the UI does not reduce a long assignment
to an unexplained `working` state. Updates include plan-step start/completion,
current action, evidence produced, retry, blocker and handoff preparation. Each
update carries an idempotency key, Work ID, live assignment generation,
participant, immutable plan-step ID when applicable, and manager-observed time.
The trusted manager records it as a canonical Baton Event; only the current
generation may contribute live activity and stale updates fail closed.

These events are a live operational projection, not a claim, heartbeat,
permission grant or automatic lifecycle transition. They complement rather
than replace the worker-owned `PROGRESS.md` journal: the final journal and
proposal evidence remain durable record artifacts, while Events let Jobs,
Teams and Work details show what the worker most recently said it was doing
and for how long. Updates occur at meaningful boundaries and material changes,
not through a mandatory high-frequency stream that rewards noise.

### Isolated-worker discovery — superseded 2026-08-20

**Superseded by "Mounted output and trusted finding intake" below.** This
earlier ruling made the manager turn each worker discovery directly into child
Work. The current model keeps the worker deliberately simple: it writes draft
findings and assets to its mounted output and notifies the manager; a trusted
intake agent later decides what, if anything, becomes canonical Work.

An isolated worker files a newly discovered defect through an idempotent
structured `file-discovery` action on the same worker-control channel. The
intent carries title, classification, report, parent/discovery context,
private-workspace evidence references, and whether the discovery blocks the
current assignment. The worker neither opens the Baton authority nor writes a
canonical dossier directly.

The trusted manager commits canonical child Work and returns its Work ID.
Trusted coordination tooling then materializes the permanent record, binding
and human `work/open/` index. Until that idempotent materialization completes,
the new Work has a typed `record-materialization` scheduler gate and cannot be
claimed. Failure is visible and retryable; it never produces a schedulable
Work whose required record is missing or an off-ledger dossier.

Filing grants no claim or editing authority over the discovered Work. The
current assignment continues unless its worker explicitly reports the
discovery as a blocker, in which case the manager commits the corresponding
typed gate or dependency through normal authority operations. Filing therefore
preserves recursive discovery without silently interrupting the serial queue.

### Mounted output and trusted finding intake — confirmed 2026-08-20

The runtime adapter gives each successfully claimed assignment one private
writable mount at a stable path inside the worker. Its backing store is keyed
by the full assignment identity or an opaque assignment UUID—not merely Work
ID—so retries, fan-out attempts and stale workers cannot share or overwrite
output. The adapter may realize it as a local bind mount, managed volume, NFS,
SSH-mounted storage or another deployment mechanism. The worker sees only an
ordinary destination directory and neither implements nor configures SFTP,
rsync, object upload or canonical-repository access.

The worker writes progress, research, reproductions, support programs,
evidence and draft findings into that mount and emits lightweight activity or
completion notifications naming dossier-relative paths. A draft finding is
not yet a Baton finding and creates no Work, containment, dependency or
authority event beyond the notification. The Worker Manager preserves and
fences the assignment output; transport and mount health are adapter concerns.

At review/intake, a trusted agent reads the drafts and may reject, edit, merge,
split or reclassify them. For every accepted finding it creates the appropriate
child or independent top-level Work and canonical dossier together, preserving
provenance to the source Work, assignment generation and draft paths. The
worker neither chooses authoritative placement nor creates Baton jobs. This
trusted intake decision resolves the earlier child-versus-independent question
without forcing unrelated discoveries to gate their source Work.

For accepted source Work, the sealed mounted output is reviewed with the source
proposal and the integrator copies accepted current-Work artifacts into its
canonical dossier in the same commit. Discovery drafts selected as new Work
enter their own canonical Work/dossier lifecycle. Rejected or unused drafts
remain retained or quarantined according to policy and never become authority
merely because the worker wrote them.

Cancellation, forced stop, plan rejection, or proposal rejection does not
forfeit discovery drafts. The manager seals or quarantines the assignment
output and routes its draft findings to trusted intake with the source Work,
assignment generation, terminal/proposal disposition, and cancellation reason
as provenance. Intake may reject every draft, but each receives a deliberate
decision before retention or disposal. Inspecting a quarantined draft neither
accepts the source proposal nor grants the draft authority.

### Plan rejection — confirmed 2026-08-20

Plan immutability does not remove worker autonomy. A worker that discovers an
incorrect, unsafe, incomplete, contradictory, or infeasible plan may reject
that plan instead of implementing it. It stops execution, returns a typed
`plan-rejected` disposition with rationale and evidence, and ends its claim and
assignment generation. Partial workspace changes may be retained as
quarantined evidence but are not an integrable proposal. Plan rejection does
not automatically close the Work. It atomically places the Work behind a typed
`plan-revision` scheduler gate, so neither the same worker nor another worker
can immediately reclaim and retry the rejected input.

A human or separately claimed plan-editor Work may then produce an explicit
plan revision. The old plan remains durable history; the revision becomes a
new immutable assignment input. The plan owner explicitly satisfies the
`plan-revision` gate only after publishing that accepted revision; only then is
the implementation Work schedulable again. Any retry requires a new claim and
assignment-generation ID. Concurrent workers assigned to the same plan or
dossier are a scheduler/protocol invariant violation: stop and report it
rather than merging. Parallel child Work remains safe only across distinct
configured participants, each with its own claim, proposal, and dossier.

### Conflict handling — confirmed 2026-08-20

A worker may refresh or rebase its private proposal onto a moved canonical
target only when the replay is conflict-free. The result is a new immutable
proposal revision and must rerun verification, review, and approval against the
new exact target.

Any actual content conflict stops the assignment. The worker reports the old
base, current target, conflicting files, proposal identity, and available test
evidence without choosing a resolution. Its assignment generation ends, the
other accepted change remains canonical, and the Work is reissued from that
new base under a new claim-generation ID. The old proposal remains evidence
but is not mechanically merged.

Conflict resolution by an agent is allowed only as explicit separately planned
Work that names the conflict and intended semantics. Neither a generic scope
claim nor the trusted integrator grants discretion to resolve one.

## Claim-acceptance deadline and unreliable workers — confirmed 2026-08-20

An assignment offer does not itself authorize execution. For each handoff the
trusted Worker Manager issues the inside agent a short-lived, single-use claim
token bound to the authority, exact Work, configured participant, runtime
attempt and expiry. The worker receives only immutable inspection context and
that token. It must return an accept/claim intent carrying the token before it
may proceed. The token expiry is the one claim-acceptance deadline; there is no
second manager deadline competing with it.

"I am working" means that the manager validated the token and successfully
committed the canonical claim, which then mints the assignment generation. A
model message, runtime status, heartbeat, tool invocation, adapter correlation
or possession of an unspent token is not a claim.

The Worker Manager denies writable workspace, execution tools and publication
capability until that claim succeeds. A missing token, expired or replayed
token, token bound to different Work, participant or runtime, `working` report
without the matching claim, or pre-claim execution attempt fails closed and is
recorded as a typed contradiction. Token expiry ends that pre-claim handoff:
there is no Handler, assignment generation, writable workspace or partial
assigned work to preserve. Route policy controls notification, runtime cleanup
and whether or when to issue a fresh handoff, but cannot revive the token.
Because the old worker can no longer claim or unlock write/publication
capability, the manager may safely hand the still-unclaimed Work to another
eligible participant using a distinct new token. No cooperative acknowledgement
from the expired worker is required.

The authority's participant pickup obligation is the broader operator-facing
signal and remains unsatisfied across failed handoffs. A token expiry is
journaled as one handoff's `offer-expired` evidence; it neither creates a
second generic overdue state nor clears or restarts pickup age. Only a
successful canonical claim, or an explicit routing/lifecycle change that
removes the obligation, satisfies it. A participant already using its one live
claim slot does not incur another pickup obligation merely because more Work
is queued for its endpoint.

Repeated claim, cancellation, protocol, or publication violations are
operational evidence that one exact runtime profile is unreliable. A profile
includes the provider, model, CLI/adapter version, role instructions, and
policy—not merely a vendor name. Deployment policy may place that profile on
probation, remove it from automatic routing, or disable it until recertified.
The threshold and retry policy are configurable rather than protocol constants,
but every decision and its evidence are visible in runtime history.

This mechanism is enforcement, not a substitute for clear prompts. Workers
are still told how to claim and given a reasonable opportunity to comply; the
system nevertheless remains safe when a model ignores or misunderstands that
instruction.

### Deadline clock and policy — confirmed 2026-08-20

This clarification supersedes the earlier implication that every missed
deadline automatically cancels and force-terminates an active assignment. The
Worker Manager's clock is authoritative for the pre-claim token expiry and for
heartbeat, execution-budget, cancellation-grace, stop, and quiescence deadline
expiry. Live intervals use its monotonic clock; persisted UTC deadlines support
restart recovery. Worker, provider, container, and runtime-engine timestamps
are diagnostic only, and heartbeat freshness uses manager-observed arrival
time.

A pre-claim token expiry is self-enforcing: the token can no longer authorize a
claim, so the handoff ends without an assignment. For post-claim deadlines,
expiry is evidence rather than an implicit command. By default the manager
journals a typed expiry, exposes it in Jobs and Teams, preserves the claim,
workspace and partial work, and permits inspection or extension. Only the
route policy pinned into the assignment's policy digest may authorize an
automatic action. That action names its deadline and policy clause,
compare-and-swaps the current assignment generation, journals the result, and
preserves or quarantines recoverable work. A cancellation-grace policy may
force-stop because cancellation was already explicitly requested; an ordinary
elapsed work or heartbeat deadline never silently discards an attempt.

## Security and reproducibility boundary

- Credentials are least-privilege, assignment-scoped where possible, and are
  not baked into images or candidate artifacts.
- Repository policy and forbidden operations are enforced outside the model,
  at the container/supervisor boundary.
- Network, CPU, memory, time, and writable mounts are explicit manifest data.
- The worker image, toolchain, adapter, base revision, role instructions, and
  policy digests are recorded with the candidate.
- Logs and candidate artifacts are untrusted worker output until integration
  review accepts them.

## Non-goals for the current v11 release

- No v11 claim, route, ACP, or shared-checkout semantics are silently changed
  by this record.
- No attempt is made to make a writable shared checkout safe for concurrent or
  recovering agents.
- No recovered stale worker is allowed to resume authority merely because its
  provider became available again.

## Open design decisions — 2026-08-18 snapshot, partially superseded

- Exact worker-control API and manifest schema.
- OCI/Docker as the required runtime versus an isolation conformance contract.
  **Superseded 2026-08-20:** the v12 reference implementation is an OCI
  container runnable through Docker or Podman; a broader isolation conformance
  contract may be considered later but does not hold the reference path open.
- Candidate transport: restricted Git namespace, Git bundle,
  content-addressed artifact, or a combination. **Superseded 2026-08-20:** the
  core path is local and forge-independent, with an immutable local proposal
  artifact such as a Git bundle; a hosted merge request is only an optional
  adapter.
- Integration authority implementation and merge/rebase policy. **Superseded
  in part 2026-08-20:** the authority separation, pre-submission rebase rule,
  clean verification gate, and atomic integration rule are confirmed below;
  the implementation mechanism remains open.
- Candidate signing/attestation and provenance requirements.
- Workspace/log retention and manual salvage policy.
- Cache sharing without writable cross-worker state.
- Network and credential profiles for different roles and repositories.

## Typed assignment input sources — confirmed 2026-08-20

The human Work description explains what result is wanted. A separate
versioned assignment input manifest tells the trusted worker bootstrap what
material exists and how to materialize it. The model never infers an
acquisition operation from prose or from a URI scheme, and it does not choose
between `git clone`, a native copy, archive extraction, or another provider.

An assignment carries one or more named, ordered source descriptors. Every
descriptor has a source `type`, an absolute normalized `uri`, a stable
destination inside the private worker workspace, and type-specific immutable
identity. URI schemes such as `file`, `ssh`, and `https` describe transport;
they do not define source semantics. Supported schemes are runtime-adapter or
source-provider capabilities rather than a closed Baton protocol list. Git's
ambiguous scp-like `host:path` shorthand is not a durable locator. Credentials
and bearer tokens never appear in a source URI or persisted manifest; the
adapter supplies narrowly scoped ephemeral access outside the model session.

The first two source types are:

- `git`: carries a configured logical repository identity, uses the descriptor
  URI as its clone source, and adds an optional full `source_ref`, mandatory
  full immutable `base_revision`, and optional full `integration_ref`. The
  bootstrap performs clone/fetch/checkout and verifies the exact base revision
  before the agent starts. A branch may
  locate handed-off Work or name its intended integration target, but branch
  movement never silently changes an assignment. The immutable revision is
  authoritative; movement requires a new assignment generation or makes a
  later candidate stale at verification.
- `directory`: carries a snapshot URI plus an immutable content-manifest
  digest. The source provider materializes the exact file collection read-only
  at its declared destination and verifies the digest before the agent starts.
  A `file` URI does not imply `cp`, and an `https` or `ssh` URI does not imply
  archive or transfer behavior; `type: directory` selects the provider
  contract. The worker receives ordinary files and no synthetic Git repository.

Only after every source is materialized and verified does the bootstrap start
the agent with explicit stable input and output paths. Source destinations are
read-only. A directory-transformation Work writes its result to a separately
declared assignment-scoped writable output role; it never edits its input in
place. Git Work writes only inside its certified private proposal clone. In
both cases the output is untrusted, generation-bound material until the normal
verification, review, approval, and integration or delivery gates accept it.

Additional source types require their own versioned acquisition, immutable
identity, validation, containment, credential, and conformance rules. They are
never inferred as aliases for `git` or `directory`.

## Named assignment outputs — confirmed 2026-08-20

A complete Job combines two contracts. The human Work contract states what the
inputs mean, the transformation or implementation required, and the acceptance
criteria. The versioned machine manifest states how named inputs appear and how
named results are exposed, constrained, frozen, validated and collected. Prose
does not substitute for machine-readable IN/OUT roles, and the manifest does
not substitute for the human specification of a correct result.

Every output descriptor has a unique assignment-local name, a result `type`, a
stable writable path inside the private worker, required/optional status, and
applicable size, file-type, structure and validation constraints. Initial
result types include an immutable Git change proposal, a directory result, and
the separately validated record-output set. A Job may declare several outputs;
an undeclared path is never collected merely because the agent wrote there.

The worker receives local paths and result expectations, not an external
publication or delivery destination. It does not upload, copy back, push, or
choose where accepted material belongs. When the worker declares completion,
the trusted manager ends or fences further writes, freezes each declared
output, rejects path escape, links/reparse traversal, unsupported file types,
limits violations and detected credential leakage, computes its manifest and
digest, and binds the collected set to the exact Work and assignment
generation. Missing or invalid required output prevents a successful result;
an inability disposition may return evidence without pretending the requested
result exists.

The frozen output is untrusted candidate material. Verification and the
applicable technical-review and approval gates bind its exact digest. A later
change creates a new immutable result or proposal revision and repeats those
gates. Only trusted delivery, record-materialization or integration tooling may
write an approved result to an external destination or canonical repository.
Thus a directory transformation reads a digest-bound read-only input path and
writes a distinct declared output path, while Git Work writes a private clone
and returns a Git proposal; neither agent participates in the outside file
exchange or canonical publication mechanism.

## Confirmed local proposal and integration workflow — 2026-08-20

The v12 reference workflow is local-first and must not depend on GitHub,
GitLab, or another forge. A configured local canonical Git repository or bare
mirror is exposed to a worker read-only. The worker clones it into its own
private writable container filesystem; Baton does not prepare or share a
writable checkout. Inside that clone the worker may create any number of local
branches and commits.

Before its initial submission, the worker refreshes the current target and
attempts to rebase its private branch onto it. A clean rebase is followed by
the required tests. **Superseded 2026-08-20 by the later Conflict handling
ruling:** the earlier rule allowed a worker to resolve a conflict it judged
clearly inside the Work contract. The current rule permits only conflict-free
replay; every actual content conflict stops with evidence and requires a newly
planned assignment. Once submitted, a proposal is immutable. A later
correction or conflict-free rebase is a new proposal revision, never a rewrite
of the reviewed object.

The submission is a Baton **change proposal**, not a hosted merge-request
object. It records at least the Work and assignment-generation identities,
base revision, proposal head, target ref, immutable Git bundle or equivalent
object transport, implementation recap, and test evidence. A forge adapter
may publish the same proposal later, but the complete workflow must operate
offline against local repositories.

Author-container test results are evidence, not certification. Baton creates a
new clean verification container, clones the same read-only canonical source,
imports the immutable proposal, constructs the candidate merge against the
current target, and runs the required gates on that exact candidate tree.
Independent suites may run in separate verification containers. The accepted
evidence names the exact target, proposal, candidate tree, image, and test
results. If the target changes before integration, the candidate is stale and
the required verification is repeated; conflicts return to a worker.

The original worker never merges its own proposal. A distinct trusted
**integrator** (the merge-master function) holds canonical write authority.
Initially that participant may be the human approver. It imports only an
approved proposal, confirms that the canonical target still matches the
verified target using compare-and-swap, and atomically updates the target ref.
It does not resolve conflicts or edit the proposal. Canonical write credentials
are never present in worker or verifier containers.

## Confirmed container and ACP boundaries — 2026-08-20

The reference worker uses one OCI container per assignment attempt, usable
through Docker or Podman. The agent runtime runs directly inside that
container. OS/process sandboxing and agent permission policy remain useful
defense in depth, but an agent does not start a nested Docker/Podman sandbox
and receives no host container-runtime socket. A provider-managed remote
container, such as a cloud-agent backend, is modeled as a different external
worker implementation rather than nested inside the local reference worker.

The two interfaces have deliberately separate jobs:

- The outer, versioned **Baton worker-control API** owns assignment identity,
  claim-generation fencing, container lifecycle, repository inputs, health,
  logs, artifacts, proposals, verification, and disposition.
- The inner **ACP endpoint** owns the agent session: prompts, turns, tool and
  permission exchange, cancellation, and session events.

ACP is the normalized inner interface for every agent. A native ACP agent is
reached through a mediated **ACP relay** that preserves identity, audit,
policy, and cancellation. A non-ACP runtime is reached through a small
**ACP adapter**: for example, Codex uses an ACP-to-App-Server adapter. Standard
ACP remains standard; vendor-only capabilities use negotiated, namespaced
extensions and do not leak into Baton scheduling or Git lifecycle. The earlier
generic term "agent driver" is superseded by the precise terms ACP endpoint,
ACP relay, and ACP adapter.

## Confirmed runtime realization boundary — 2026-08-20

A trusted host-side **Worker Manager** implements the outer worker-control API.
For the reference deployment it selects an **OCI runtime adapter**, which
translates runtime-neutral operations such as start, cancel, inspect, collect,
and destroy attempt into Docker or Podman actions. The adapter may use a
validated argument-vector CLI or an engine API; that mechanism is deployment
code and is not Baton protocol vocabulary.

Starting an attempt resolves the pinned image, prepares the logical read-only
repository source, private writable workspace, proposal/evidence output, and
optional cache, applies resource/network/credential policy, starts the
`baton-worker` entrypoint, connects its control channel, and reports confirmed
state. Those are logical storage and policy roles. Bind-mount paths, volume
names, container ids, daemon sockets, and engine inspection payloads remain
opaque adapter details.

The Worker Manager keeps recoverable deployment state mapping one Baton
attempt id and assignment generation to its opaque runtime id. Runtime labels
carry enough non-secret identity to reconcile surviving containers after a
manager restart. Docker/Podman status and errors are normalized into Baton
worker states; engine output is diagnostic evidence, never coordination
authority.

### Remote worker adapters — confirmed 2026-08-20

Remote execution uses the same worker-control contract through another runtime
adapter. For example, an SSH adapter may authenticate a configured host, start
or reach `baton-worker` there, optionally launch its OCI container, and carry
the control stream. SSH commands, host keys, tunnels, process identifiers and
remote storage layout are adapter/deployment concerns; none becomes Baton
protocol vocabulary or coordination authority.

The trusted Worker Manager remains the only authority client. It sends
immutable digest-bound inputs, binds the short-lived claim token to the exact
remote runtime attempt, receives structured Events and intents, and collects
an immutable proposal artifact. The remote worker receives no Baton database
access, writable canonical Git remote, integration credential, or authority
to publish after its generation is revoked.

A transport loss is not proof that the remote process stopped. The manager
first fences claim/publication authority and records uncertain quiescence, then
follows route policy for reconnect, cleanup or replacement. Reattachment is
allowed only after positive proof of the same runtime and assignment
generation. A stale remote process may survive a partition but cannot claim
with an expired token or publish after revocation.

**Superseded 2026-08-20:** remote-adapter testing is not deferred until later
production conformance. The local OCI worker remains the first walking-skeleton
step, but the same bounded spike must then run the contract through an SSH or
equivalent adapter to a genuinely non-local worker before worker-control and
manifest schemas freeze. That early distributed scenario covers immutable
input delivery, token-bearing claim, live Events, proposal return, transport
loss, publication fencing and safe replacement. A loopback-only simulation is
useful testing but does not satisfy the non-local scenario.

Cancellation is ordered and fail-closed:

1. revoke the attempt's candidate-publication authority;
2. request ACP cancellation and graceful worker shutdown;
3. apply the configured runtime stop deadline and force-stop if necessary;
4. seek positive quiescence and otherwise record the attempt uncertain only
   after publication fencing and isolation are established; and
5. retain or destroy the private workspace according to explicit policy.

If quiescence cannot be confirmed, the attempt is unhealthy/uncertain rather
than silently replaced. Generation fencing still rejects a late candidate,
and container isolation prevents the stale worker from touching another
workspace or the canonical repository.

The protocol describes an isolated worker attempt and its capabilities, not a
Docker command line. OCI image identities and digests may be durable
provenance because they are portable inputs; Docker-specific runtime ids and
storage names may be exposed as diagnostics but have no protocol semantics.

## Confirmed worker-runtime conformance contract — 2026-08-20

OCI is the certified reference implementation, not the definition of a Baton
worker. A container, VM, remote worker, or later isolation mechanism is
compliant only when the same conformance suite proves all of these invariants:

- every assignment generation receives one isolated private writable
  workspace;
- the canonical repository, its refs, and every other worker workspace remain
  unwritable, with no shared writable Git metadata;
- candidate publication requires the current live assignment generation, and
  revocation fences every later publication attempt from that generation;
- cancellation revokes publication authority before replacement; positive
  quiescence is preferred, while an explicit uncertain/unhealthy disposition
  may admit replacement only when generation fencing and isolation prevent the
  stale attempt from reaching canonical or replacement state;
- credentials are least-privilege, short-lived, and assignment-scoped where
  possible; are delivered through non-persistent mechanisms; and are absent
  from known durable surfaces under exact-canary and best-effort secret scans;
  detected leakage refuses publication;
- network, resource, mount, tool, and retention policies are explicit manifest
  inputs rather than runtime defaults inferred by the worker;
- worker output, including commits, tests, logs, and status claims, remains
  untrusted until clean verification accepts the exact candidate tree; and
- lifecycle state, health, cancellation, errors, artifacts, and proposal
  publication normalize into the versioned worker-control contract without
  exposing runtime-specific semantics;
- transport loss is never treated as proof that a remote process stopped;
  publication and generation authority are fenced before uncertain quiescence
  permits replacement; and
- remote reattachment requires positive proof of the same opaque runtime and
  assignment generation, while a merely reachable endpoint is insufficient.

The conformance suite also proves both deadline classes. For pre-claim handoff,
execution is denied, a status-only `working` report grants nothing, and token
expiry self-enforces refusal; route policy may clean up the runtime or issue a
fresh token but has no assignment generation to fence. For a post-claim
deadline, an explicit pinned policy clause may cancel and compare-and-swap
fence the exact current assignment generation. Repeated violations can remove
the exact runtime profile from automatic routing.

### Testable credential and quiescence boundary — confirmed 2026-08-20

This clarification supersedes the earlier absolute phrases that credentials
"cannot enter" arbitrary output and that replacement always requires confirmed
quiescence. A conformance suite cannot prove absence from every transformation
or prove that an unreachable runtime anywhere is dead.

Credential conformance proves non-persistent delivery, least privilege and
bounded lifetime, absence of injected canary secrets from the private
workspace, Git objects, proposal, manifest, evidence, retained logs, caches,
and retained runtime layers, and publication refusal on a detected match.
Best-effort scanning and redaction cover known encodings and secret patterns;
scope, revocation, and network policy carry the residual risk of arbitrary
transformation or exfiltration.

Cancellation always revokes candidate-publication authority first, then seeks
graceful shutdown, force-stop, and positive runtime quiescence. Generation
fencing and workspace isolation are the mandatory safety invariants. If the
manager cannot prove the old runtime dead, it records the attempt
`uncertain` and may admit a replacement only when the stale generation cannot
publish or access canonical state, the replacement workspace, shared writable
state, or reusable credentials. The suite exercises both confirmed-stop and
uncertain-runtime paths and proves every late stale publication is rejected.

### Runtime-profile probation without rerouting — confirmed 2026-08-20

Configured routing states which participants may handle an endpoint and does
not change merely because one execution stack is unhealthy. The Worker Manager
separately records dynamic eligibility for the exact runtime-profile digest:
participant, provider/model, adapter version, worker image, role instructions,
security policy, and toolchain. A materially different combination is a new
profile and requires certification rather than inheriting either trust or
probation by participant name.

Profiles are `certified`, `probation`, or `disabled`. Certified profiles are
eligible for automatic Work. Probation profiles are excluded from ordinary
automatic Work and may run only explicit diagnostic or recertification trials.
Disabled profiles cannot launch until an operator replaces or re-enables them.
Repeated claim, cancellation, leakage, protocol, or stale-publication failures
may move the exact profile out of certified status; recovery requires explicit
recertification rather than elapsed time.

The manager filters offers by this operational state without editing
`baton.json`, bumping its global generation, or rerouting existing Work. It may
offer to another certified configured handler when policy allows. When no
certified profile can serve the endpoint, Work remains honestly queued and
unclaimed at its configured route, and Jobs and Teams expose a typed
`no-certified-runtime` scheduler gate. No unavailable profile is represented
as offered, claimed, or working.

### Participant capacity — confirmed 2026-08-20

One Baton participant may hold exactly one live claim and therefore one live
assignment generation and worker at a time. V12 retains the authority invariant
enforced by `claim_work`; the Worker Manager cannot widen capacity behind it or
represent several workers as one Handler.

Parallel Work requires distinct configured participant identities, even when
those participants use the same provider, model, adapter, or role. Parallel
child Work is safe only across those distinct participants, each with its own
claim, runtime profile, proposal, dossier, pickup obligation, and accountable
Handler identity. Another certified configured handler is therefore the unit
of route-level parallelism and failover.

Fan-out of the same frozen problem is represented by a coordinating parent
Work plus one sibling child Work per independent attempt, never by several
claims on one Work. Every attempt has its own Work ID, participant, assignment
generation, isolated workspace, proposal and disposition. Selection records
the exact winning child Work, assignment generation and proposal; the parent
cannot record an unqualified winner whose producing attempt would have to be
guessed. Losing or superseded attempts remain attributable history and receive
explicit dispositions.

Passing this suite is required before a runtime implementation is described as
supported. A provider's claim of isolation or successful shutdown is not a
substitute for observable negative, race, crash, recovery, and stale-generation
tests.

## Remaining open design decisions after 2026-08-20

- Exact schemas and transports for the worker-control API, input manifest,
  proposal manifest, and verifier result.
- Worker Manager packaging and whether each OCI adapter uses an engine API or
  validated CLI argument vectors.
- Local proposal-store layout and the trusted integrator implementation.
- Candidate signing/attestation and provenance requirements.
- Workspace, log, bundle, and manual-salvage retention policy.
- Cache sharing without writable cross-worker state.
- Network and credential profiles for worker, verifier, reviewer, and
  integrator roles across multiple local repositories.

## Confirmed authority-mediation boundary — 2026-08-20

The sandboxed agent never opens Baton's SQLite authority and never invokes a
host Baton executable. The trusted host-side Worker Manager owns all authority
access. The agent speaks only structured worker-control intents through its
normalized session boundary.

Claim remains explicit rather than becoming a controller-side guess:

1. the manager gives the agent the readable Work contract and a short-lived,
   single-use claim token bound to the exact Work, participant and runtime;
2. the agent returns an accept/claim intent carrying that token, and the Worker
   Manager validates it before submitting the canonical atomic claim as that
   configured participant;
3. only a successful claim mints the assignment generation and unlocks the
   private writable workspace, execution tools, and candidate publication;
4. a failed or timed-out claim starts no execution; and
5. pass, close, message, inability, and other workflow intents are likewise
   validated and committed by the manager rather than by mounting authority
   storage into the worker.

This resolves the design review's apparent contradiction between a read-only
pre-claim worker and the mutating claim operation: **read-only** describes the
worker's repository/execution capability, not the trusted manager's authority
channel. It also removes host coordination paths from model sandbox approval
policy. The v11 incident that pinned this boundary was a readiness-driven
Codex turn permanently waiting for approval merely to write its canonical
`claim`; v12 does not ask the sandboxed model to cross that boundary.

The manager may not claim merely because an event was delivered. Token issue,
the agent's token-bearing accept intent, the authority's successful
compare-and-swap, and capability activation are four ordered facts, with
failure between them visible and recoverable. An expired token cannot be
renewed in place; retry creates a new handoff token while the participant's
canonical pickup obligation remains open.

## Implementer design review checkpoint — 2026-08-20

The approver requested an independent Claude review of the pinned v12 design
before choosing implementation order. This handoff authorizes critique only:
revalidate the decisions and open questions against the current repository,
identify contradictions, missing invariants, impractical boundaries, and
ordering risks, and record recommendations in the Work discussion and an
append-only review artifact if warranted.

No v12 implementation, prototype, dependency addition, schema change, or
product-code edit is authorized by this checkpoint. When the review is
complete, Claude returns W2 to `baton.feat`; the reviewer and approver will
decide ordering separately.

## Required bounded end-to-end spike — confirmed 2026-08-20

V12 test-drives the operational model after the minimal assignment state
machine and identities are specified but before the worker-control and manifest
schemas become compatibility contracts. The spike uses a fixture repository,
disposable Baton authority, one real OCI worker, and draft `0-spike` manifests.
It never touches a production repository or deployment.

The walking skeleton exercises short-lived token offer, explicit claim and
assignment-ID minting, private edit and local commit, immutable proposal
publication, clean verification, technical review, approval, and
compare-and-swap integration. Verification, technical review, approval, and
integration use four distinct accountable actors rather than collapsing the
gates into one privileged process.

Before manifest schemas freeze, the spike also runs one directory-only
transformation with no Git source: the adapter materializes a digest-bound
read-only file collection, the bootstrap verifies it before agent start, the
agent writes only to the declared writable result output, and verification
binds the exact input and output digests. This proves that repository lifecycle
is a typed source capability rather than an assumption embedded in every Work.

Its required scenarios include an expired token that fails closed followed by
safe claim through a fresh token, `plan-rejected` gating until an accepted plan
revision, a real replay/rebase conflict that stops for separately planned Work,
competitive fan-out selecting the exact winning child Work/generation/proposal,
and cancellation of one active worker followed by replacement while the stale
generation proves unable to publish.

The cancellation scenario deliberately lets the post-claim cancellation-grace
deadline expire. The resulting force-stop must name the pinned route-policy
clause and policy digest, compare-and-swap the live assignment generation,
journal the disposition, and preserve or quarantine recoverable work. This is
separate from the self-enforcing pre-claim token expiry.

After the local OCI path works, the spike repeats the essential lifecycle on a
genuinely non-local worker through an SSH or equivalent runtime adapter. It
proves digest-bound input and proposal transfer, token/runtime binding,
activity-event delivery, disconnect handling, publication fencing and safe
replacement before the transport-neutral contracts become compatibility
promises.

The spike is bounded rather than a hidden v12 implementation. Its durable
deliverables are observed protocol traces, scenarios, fixtures, negative
tests, and corrections to the state machine, API, manifests, ACP boundary, and
conformance contract. Those tests seed the conformance suite. Temporary Worker
Manager wiring is disposable unless it independently satisfies the final
reviewed design. Production implementation begins only after the corrected
contracts are frozen.

The spike explicitly does not settle production credential profiles,
retention, cache sharing, candidate signing/attestation, or final local
proposal-store layout. Those remain reviewed design and production-hardening
Work; provisional spike choices create no compatibility promise.

## Disposable proof-of-concept isolation — confirmed 2026-08-20

The first single-agent Claude ACP proof of concept is an external black-box
consumer of the deployed v11 interface, not an experimental modification of
the existing Baton implementation. It may fail and be discarded without
leaving partially adopted mechanisms in the working product.

The PoC therefore owns a separate source root or repository, dependency lock,
tests, fixtures, draft manifests, worker image and disposable runtime state. It
does not modify `src/baton_work`, the existing ACP or Codex bridges, lifecycle
controller, `justfile`, v11 tests, release templates, production coordination
home, or current deployment. It may invoke the immutable deployed Baton
executable as a black-box client of documented CLI/JSON behavior and may speak
standard ACP, but it does not open the authority database.

**Superseding reuse clarification — 2026-08-20:** the earlier prohibition on
copying private implementation was too strong and is withdrawn. The PoC may
snapshot or copy any useful v11 source, bridge, CLI, JSON, test, fixture or
documentation material into its separate disposable root and modify that copy
without limit. Every copied seed records provenance to release commit
`8835cd5`; the prototype never imports through, symlinks to, or writes back to
the live Baton checkout. Reuse creates no compatibility or adoption promise,
and successful prototype code still enters Baton only through later reviewed
implementation Work.

The first proof concentrates on JSON contracts and command-line operation.
TUI design and implementation are explicitly out of scope: natural dispatch
is proven through ordinary Job creation/routing plus machine-readable state,
traces and results, not by building another human console.

The PoC uses its own disposable authority and harmless fixture inputs. The
only material retained in the Baton repository during the experiment is the
W2/child-Work decision record, observed traces and reviewed conclusions; no
prototype runtime source lands in existing Baton paths. Failure closes or
cancels the child Work and permits deleting the external prototype without a
product rollback. Success still authorizes no direct copy into v12: adopting
any mechanism requires a separately planned, reviewed implementation Work
against the then-current contracts.

This isolation does not weaken the walking-skeleton acceptance boundary. A
successful PoC still begins with the minimum assignment state machine, accepts
an ordinary dispatched Job through the public boundary, obtains an explicit
claim through the trusted manager, runs Claude through ACP in an isolated
worker, emits activity, and returns frozen declared output. A manually invoked
Claude process or a prototype that reaches into Baton's source or SQLite store
does not pass.

## Gradual coexistence and rollout — confirmed 2026-08-20

V12 isolated workers do not replace the v11 execution path in one deployment
swap. Both modes coexist during a gradual rollout, and the migration unit is a
configured participant/runtime profile rather than the Baton installation,
team, repository or authority as a whole. This supersedes every reading of the
earlier "v12 cutover" wording as one global switch.

A participant is attached to exactly one execution mode at a time. A legacy
shared-checkout readiness consumer and the Worker Manager never consume Work
for the same participant identity concurrently. New isolated capacity uses a
distinct configured participant and certified runtime profile; routes may make
legacy and isolated participants available according to explicit policy, but
one concrete offer and claim always names exactly one participant and one
execution mode. One Work or assignment generation is never fanned out across
both modes implicitly.

Legacy participants keep the current v11 claim, filesystem and Git policy.
Only a successfully claimed assignment under a certified isolated profile gets
the v12 private-workspace, scoped Git exception, typed IN/OUT, proposal and
generation-fencing capabilities. The same authority may coordinate both kinds
of participant, but it must project their execution mode honestly and never
represent a legacy claim as isolated merely because Worker Manager services
are installed.

Rollout proceeds by adding and certifying isolated participants, directing a
small explicit Work subset to them, observing the complete lifecycle, and
expanding route policy only after review. Rollback stops new offers to the
isolated profile, fences or deliberately disposes its live assignments, and
routes later Work to an eligible legacy participant; it does not require
replacing the authority or undoing unrelated v11 Work. Removal of the legacy
path is a later explicit adoption decision after no route depends on it, not a
premise of the PoC or initial production use.

## Second implementer design review checkpoint — 2026-08-20

After the approver resolved all ten findings from the first review, W2 is
handed to `baton.claude` for review only. Re-read the complete record and the
first append-only review, then test the newly pinned clarifications for internal
contradictions, missing safety boundaries, feasibility, and whether the bounded
spike can answer the remaining implementation questions.

This handoff authorizes no v12 implementation, prototype, dependency addition,
schema change, or product-code edit. Record findings and recommendations, then
return W2 to `baton.feat` for ordering and explicit authorization.

## Final implementer design review checkpoint — 2026-08-20

The approver has now ruled every finding in
`review-2026-08-20T16-00-50Z.md`. The record pins one live claim per
participant, child-Work fan-out with an exact winning attempt, token-gated
pre-claim handoff, plan-revision gating, immutable plans with a separate
progress journal, generation-bound activity, isolated-worker discovery,
presentation-only shorthand, and the expanded bounded-spike contract.

Claude performs one final consistency review of the complete current
`FINDING.md`, `PLAN.md`, `review-2026-08-20T11-37-13Z.md`, and
`review-2026-08-20T16-00-50Z.md`. This is review only: no v12 implementation,
prototype, dependency, schema, or product-code change is authorized. Confirm
that the second-review findings are resolved without introducing a new
contradiction and return W2 to `baton.feat`. A clean return is the requested
commit/deployment checkpoint; any remaining issue must be concrete and
decision-ready.

## Closure consistency review checkpoint — 2026-08-20

The final review returned six non-blocking residuals in
`review-2026-08-20T16-31-16Z.md`. The record now requires remote partition and
proof-bound reattachment conformance, exercises a post-claim
cancellation-grace policy/CAS in the spike, qualifies parallel children by
distinct participant, states the v12 PLAN/PROGRESS cutover boundary, and
separates pre-claim token expiry from post-claim policy fencing.

The approver then simplified discovery/output: a worker receives one private
assignment-scoped writable mount, writes progress/evidence/draft findings, and
only notifies the outside. A trusted intake agent—not the worker or manager
automatically—decides whether to reject, edit, merge, split, or materialize a
draft as child or independent Work. This explicitly supersedes automatic
`file-discovery` Work creation and resolves the sixth review choice.

Claude performs one narrow review-only closure pass over the current record and
`review-2026-08-20T16-31-16Z.md`. Confirm that those residuals are resolved and
that the supersessions leave no competing live rule. No implementation,
prototype, dependency, schema, or product-code change is authorized. Return W2
to `baton.feat`; a clean return is the commit/deployment checkpoint.

## Final clean review disposition — 2026-08-20

The closure pass left one question: whether cancellation or rejection forfeits
draft findings. The approver ruled that it does not. Item 0aa and "Mounted
output and trusted finding intake" now route sealed or quarantined drafts from
all four terminal paths to trusted intake with source-disposition provenance,
without accepting either the source proposal or the drafts merely by reading
them.

Claude performed the final yes/no check in
`review-2026-08-20T16-58-40Z.md`. Result: **clean**. The sole residual is
resolved, generation fencing remains intact, the superseded automatic-filing
text is unambiguously historical, and no competing live rule remains. No v12
implementation was authorized or performed by any design review pass.

## Prototype repository placement supersession — 2026-08-20

The requirement that the disposable v12 prototype remain in the separate
top-level repository `/home/sl/src/baton-v12-poc` is superseded after the
initial isolation proof. V12 remains isolated from the existing v11 product,
but its durable development home is the self-contained top-level `v12/`
subtree of this Baton repository.

`v12/` owns its own `justfile`, package and lock metadata, `src/`, tests,
scripts, fixtures, configuration, manifests and container definitions. It is
independently buildable and testable without invoking a v11/root recipe. While
v12 remains experimental, root recipes do not delegate into it and no root
build, package, deployment or release surface includes it. Only a later
explicit adoption Work may add that integration. Generated
dependency trees, downloaded images, credentials, authorities, logs and
runtime state remain excluded. Existing v11 paths, including
`src/baton_work/`, v11 tests, bridges, recipes and deployment files, remain
outside the prototype's edit boundary until a separately approved integration
Work says otherwise. This keeps the original discardability and no-v11-change
guarantee while avoiding a second product repository that would have to be
folded back after success.

The already-built external PoC remains the implementation reviewed by W76.
Relocating it is a bounded follow-up after that review: preserve provenance,
copy only source-controlled prototype material—including dependency manifests
and lockfiles—into `v12/`, exclude generated dependencies and runtime state,
verify the same gates there, and retire the
external root only after the in-repository copy is verified. The approver has
explicitly authorized removing `/home/sl/src/baton-v12-poc` at that point so
there is one canonical prototype location; it is not retained as an archive.

## Interactive and managed execution identities — confirmed 2026-08-21

V12 distinguishes the one human-attached interactive copilot from managed
background workers. One participant identity is bound to exactly one live
execution context: an interactive and a managed context never share the same
participant merely because they use the same model, role, or provider.

The interactive copilot has one user-attached session. Each background
participant has one Worker Manager-owned execution context. Internal
conversation threads are not participant identities and do not independently
claim or schedule Work. Parallel execution uses distinct participants or
assignment attempts, and delegation by the copilot routes Work to a background
participant instead of creating a hidden second context under the copilot's
identity. Runtime state such as `Run` therefore describes the participant's
sole execution context without pretending to aggregate unrelated threads.

This is a deferred production-model requirement, not an acceptance condition
for the current single-Claude walking-skeleton PoC or its repository migration.
No separate Work is created yet; implementation is ordered only after the PoC
has demonstrated the more fundamental isolated-worker lifecycle.
