# Using Baton effectively

This book explores ways of working with Baton through representative situations.
The examples illustrate strategies that teams can adapt; they do not prescribe
an organization, a deployment, or one mandatory sequence for every project.

Baton provides the coordination rules for ownership, claims, handoffs,
dependencies and recorded decisions. A project chooses its roles, permissions,
acceptance criteria and tools. An example that separates implementation,
review and integration shows one possible workflow, not a protocol requirement.

For installation and configuration, use [Baton setup](BATON-SETUP.md).
For exact commands, operands and protocol behavior, use the
[operator reference](BATON-WORK.md). The situations here focus on why a team
might choose an action and how that choice affects the work around it.

## The straight-through path

Consider a team fixing an export bug. Someone reports that a particular input
loses information, an implementer reproduces it, and a reviewer checks the
correction.

One Work can carry that whole bounded outcome. Its description explains the
observed problem and the result that would count as a fix. The implementer
claims it before making the change. When the candidate and evidence are ready,
the implementer passes it to the endpoint configured for review. The reviewer
then claims it and either requests a correction or reaches an acceptance
decision.

The useful distinction is between eligibility and execution. The Route names
the endpoint whose configured handlers may act. The claim records which
participant is actually doing so. A pass releases that claim and hands on the
responsibility; it does not pretend the recipient has already started.

This makes interruptions easier to understand. A candidate waiting for review
appears as available work, rather than as work somebody supposedly holds.
If the reviewer finds a small defect, the same Work can return for correction
without inventing a new lifecycle for every conversation.

Closing it records an outcome and a reason that a later reader can understand.
A subsequent discovery that contradicts that conclusion becomes linked
follow-up Work, preserving the original decision and its evidence.

## A handoff carries context as well as ownership

In the export example, a handoff saying only "ready" makes the reviewer search
for the candidate, the verification and the remaining uncertainty. A long
retelling of every investigation creates the opposite problem: the decision
gets buried.

A useful handoff might say:

> The export now preserves the escaped value. The focused regression covers
> the reported failure and the adjacent empty-input case. The candidate and
> run evidence are linked in the record. Review the parser change; streaming
> performance is outside this correction.

The pass carries the transfer of responsibility. The discussion explains what
the recipient needs to decide. The detailed evidence stays at one durable
location, so another handoff does not require copying the same account again.

This separation is especially useful when a human receives the work. The
message can identify the decision, explain the recommendation and expose its
limits. The human does not have to reconstruct the request from operational
events.

## Saying why something is not moving

Suppose an implementer is waiting for a product decision about malformed input.
There is useful work in the record, but no honest next implementation step.
A directed request can express that dependency and hold the Work on the answer.

Compare that with an improvement deliberately deferred until a later release.
It has no unanswered question whose resolution should wake it. Parking it with
a reason describes the situation more accurately than creating an artificial
blocker.

A third item may simply be ready and unclaimed. That is a capacity or pickup
question, not a missing product decision.

These distinctions make the board useful. A waiting gate names an input that
can arrive; a parked item names a scheduling choice; queued work exposes an
opportunity to act; and a live claim identifies an executor. Discussion alone
does not substitute for those facts.

When work is directed to the wrong endpoint, correcting the Route is a separate
question from whether it is ready. Redirecting a parked item need not resume
it, and redirecting a blocked item does not satisfy its missing input.

## Discussion, attention, and directed requests

An export change may interest a library maintainer without requiring anything
from them. An attention-only message shares that context while leaving both
participants' work free to proceed.

If the implementer needs the maintainer to confirm the library's behavior, a
directed request makes the obligation explicit. A blocking request is useful
when that answer is necessary before continuing. An asynchronous request is
useful when independent work can still proceed honestly.

The distinction prevents two common delays. Treating every mention as an
obligation overloads recipients with unnecessary decisions. Treating a required
answer as a casual mention leaves the sender waiting for something nobody
formally owes.

The recipient may answer the question, explain why no answer is owed, or accept
responsibility for a deliverable. These outcomes have different effects and
deserve different records. Another participant contributing to the discussion
does not silently settle the original obligation.

## Cross-team work: providers and consumers

Imagine that the export feature needs a streaming capability from a storage
library. The library team agrees that this is its responsibility.

The library delivery becomes provider Work. The export feature is its consumer.
A recorded dependency explains why the consumer needs the provider's result,
while each team retains responsibility for its own implementation and acceptance.

This arrangement is useful when the library capability serves several features.
Its review and evidence can be shared without making every consumer own a copy
of the same repair.

Acceptance of the provider establishes that the library capability is available.
The export team still needs to connect it, check the assumptions at that
boundary and demonstrate its own result. Provider closure does not prove that
the consumer works or close it automatically.

If a dependency was mistaken, correcting that relationship is different from
declaring either deliverable complete. The explanation preserves why the
schedule changed without rewriting the technical evidence.

## Containment versus dependency

A release may contain an export feature, a documentation update and a migration
guide. Containment gives the team one place to see the release's required
deliverables. It does not by itself mean those items must execute in sequence.

The export implementation might depend on the storage capability. The migration
guide might depend on the final data format. The documentation outline may be
ready immediately. Those are different input relationships, expressed through
explicit dependencies.

A parent can therefore be useful while its children remain open: it can carry
planning, integration questions or the final acceptance discussion. Open
children do not automatically block its execution, although required children
prevent the parent from closing.

This lets the hierarchy answer "what belongs together?" while dependencies
answer "what input is needed first?" Trying to make either relationship answer
both questions tends to hide useful parallel work.

## Preparation can proceed before implementation

Suppose the storage implementation is still underway, but the export feature's
public contract and acceptance criteria are already agreed.

A reviewer can examine that plan before the export code exists. The preparation
has a reviewable outcome of its own: the contract is coherent, the fixtures
represent the required cases, and the proposed verification addresses the right
questions.

Giving that preparation separate Work allows its dependencies to differ from
the implementation's. It can finish while the implementation waits for the
storage delivery. Later review of the produced candidate still waits for the
candidate itself.

This works only when the preparation's inputs are actually ready. If the
storage result could change the contract being assessed, the preparation also
depends on that result.

The opportunity comes from separating outcomes and their inputs. Calling a
blocked implementation "research" or "review" does not bypass its gate. Role
labels alone do not create special readiness rules.

## Splitting a Job that stopped converging

A feature starts as a small correction, but successive handbacks expose a new
library capability, a separate data migration and an unstarted integration
proof. The original Work has become a queue disguised as one assignment.

A useful response is to identify which remaining outcomes can be implemented
and accepted independently. Each can become its own Work, with clear ownership
and only the dependencies its inputs require. Completed evidence stays with
the result it proves, and one named consumer retains the joined acceptance.

Repeated non-accepting reviews and growing delivery gaps are practical signals
to reconsider the shape of the Work. Splitting is a useful default when distinct
deliverables have accumulated. Merely moving the same oversized assignment to
another person does not address that cause.

There are also cases where a split adds little. A small correction across two
tightly coupled files may have one meaningful acceptance result. Keeping it
together can be reasonable when the reviewer can explain what remains, why it
belongs together and what the next pass will demonstrate.

The decision becomes more useful when it describes concrete outcomes instead
of relying on "almost done." Proposed changes can be discussed during a claim;
changing the actual allocation waits for a safe handoff so the executor is not
working against a moving scope.

## Capability passes preserve the big picture

A team investigating a new export architecture may first need to show that a
real request can travel through the system and produce a usable result. Later
passes may address larger inputs, restart behavior, portability or operational
scale.

Agreeing on the first demonstration helps the team judge discoveries. A defect
that could make the demonstration falsely report success belongs in that pass.
An improvement that does not invalidate the agreed claim can be recorded for
a later pass. An unrelated concern can remain outside the campaign.

This is useful when polishing individual components has stopped producing
visible progress in the whole system. A working vertical slice exposes mistaken
interfaces sooner and gives later robustness work something concrete to
strengthen.

The acceptance claim determines the boundary. A feasibility demonstration and
a production rollout need different evidence. If safe restart is part of the
agreed milestone, it cannot quietly become optional simply because the ordinary
path works.

Recorded concerns remain accountable without all becoming immediate blockers.
At a handoff, the team can say what now works, what still prevents the current
demonstration and which discoveries belong to later passes.

## Role arrangements follow the work

A small team might use one participant for analysis and implementation, with
another person reviewing consequential changes. A larger team might schedule
implementation, review and integration independently. A project focused on
research may divide its work into investigation, synthesis and validation
instead.

These are examples of organizational choices. Baton resolves the roles,
endpoints and handlers that a project configures; it does not prescribe one
role hierarchy or a fixed number of workers.

For example, a software team could separate first-delivery work from later
reliability work using different routes. Another could use one route and
distinguish those outcomes through its Work descriptions and dependencies.
Separate routing is useful when it changes who can act or how capacity is
allocated, rather than merely giving the same queue another name.

The same applies to review capacity. If accepted candidates accumulate behind
one long review, another eligible reviewer may help. If implementation lacks
ready independent inputs, adding more implementers may not.

Concurrent participants need distinct identities, separately owned claims and
appropriate resource isolation. Capacity decisions work best when they respond
to an observed bottleneck and the project's acceptance requirements.

## Learning through a controlled pilot

After an early capability is accepted, a team may use it on bounded real work
while later improvements continue. An export tool might serve an internal
report before becoming part of a critical production workflow.

The pilot is valuable because it tests assumptions that component exercises
may miss. It also needs a clear limit: the team knows what data or results can
be discarded, what fallback remains available and what evidence would justify
wider adoption.

An isolated successful run supports the claim it actually demonstrated. It
does not automatically establish recovery, scale or production readiness.

This gives the team a way to learn from useful work without making an early
experiment responsible for more than its evidence supports.

## Verification answers a question

An implementer changes how an escaped value is parsed. A focused regression can
answer whether that correction addresses the reported failure. Once the change
is stable, a broader relevant check can look for consequences elsewhere.

Running the whole suite after every small edit often delays that feedback.
Running only the focused case forever leaves interactions unexamined. A useful
cadence separates the correction loop from the broader check needed for handoff.

Before a costly run or series of runs, stating the question, scope and expected
cost makes the choice reviewable. A quick probe needs little ceremony; an
expanding test campaign benefits from an explicit reassessment.

Existing evidence can answer the question when it still applies to the candidate
and environment. A repeat is informative when the relevant bytes changed,
the earlier result is incomplete, or an independent environment is itself part
of the acceptance claim.

The reviewer may add a targeted counterexample, examine a different boundary
or investigate a missing control. Repeating the implementer's entire run only
because the work changed hands adds cost without necessarily adding evidence.

When a broad run fails, its useful output becomes evidence for diagnosis.
Related failures may block the candidate; unrelated failures need their own
ownership. Parallel execution helps when checks have isolated state. Shared
resources require deliberate isolation or serialization using the project's
supported harness.

Changing a test also changes an evidence claim. Whether that edit is already
authorized comes from the project's accepted scope and permissions. Review
still asks whether the revised expectation represents the intended behavior,
rather than merely making a failing implementation look successful.

## Verification trials

Some changes benefit from several independent observations of the same
candidate. A library correction might need checks in different consumer
environments, each with its own owner.

A verification trial gives those participants a shared immutable subject.
Each records what happened and where the evidence lives. Assessment is separate:
a reviewer can accept a failure report as valid evidence without accepting the
candidate.

This separation is useful when results differ. One environment may expose a
defect while another cannot run the check. Recording observations and judgments
separately preserves both facts without reducing the trial to a pass count.

A replacement candidate needs a new comparison point. Superseding the trial
preserves its earlier evidence instead of rewriting the result around changed
bytes. Finishing the trial remains an explicit decision by the authorized
participant.

## Concise reporting

A long investigation can produce a short, complete handoff when the details
have a stable home. The recipient usually needs the result, the remaining
limitation, the next decision and a precise route to the evidence.

An unhelpful report repeats the original task, every prior review and every
unchanged design choice. A useful report explains the delta and makes the next
action possible without hiding a material caveat.

Length is a diagnostic, not the outcome. Some decisions need substantial
explanation. Brevity is effective when it removes repetition while preserving
the facts needed to act; cutting an essential limitation defeats its purpose.

Keeping one technical account also makes corrections easier. The author can
append a clearly attributed correction and point later handoffs to it, rather
than leaving several nearly identical reports with different claims.

The same principle applies to the interactive copilot. It can summarize the
current decision and carry it into the durable record without recreating the
whole campaign history in every operator update.

## Evidence lives in the repository

A team agrees on a behavior during a discussion. Several handoffs later, a new
participant sees only an old description and implements the earlier behavior.
The decision existed, but not where the next executor could reliably find it.

A durable project record addresses this gap. It distinguishes the observed
problem, confirmed decisions, current plan, execution evidence and independent
review. Baton supplies the live coordination state; the record explains how
the team reached its present understanding.

Projects can use different filenames and layouts for those responsibilities.
The important qualities are stable locators, clear ownership and a visible
history of superseded decisions. A temporary checkout path or a remembered
conversation is a weak substitute for a shared canonical reference.

A plan is most useful when it describes the intended outcome and sequence.
Copying every live phase or dependency into prose creates another board that
can become stale as soon as Baton changes. Dated evidence can describe what
happened without pretending to be the current scheduler state.

Lightweight Work need not produce an elaborate dossier. The amount of recorded
detail can follow the complexity and durability of the decision. What needs to
survive a handoff or restart deserves a dependable home.

## Changing the contract of assigned Work

A reviewer notices that the export fix also needs a compatibility decision.
That observation can be discussed while the implementer holds the Work, but
it does not silently change what the implementer agreed to deliver.

If the new requirement belongs in the same bounded outcome, the current
claimant can promote the agreed revision through Baton's contract mechanism.
Its comparison against the expected revision prevents a stale update from
overwriting a newer decision.

If the requirement is independently accountable, separate Work may express it
more clearly. Either way, the discussion, accepted scope and actual execution
should agree.

This is particularly useful with concurrent participants. Eligibility to act
on an endpoint is different from holding the current assignment. A route peer
can contribute a proposal without acquiring the right to rewrite another
participant's live contract.

## Readiness and finding the Work that awaits you

A participant may have fresh work available, an obligation to answer, or an
assignment it already holds. Looking only for newly unclaimed Work can miss
the third case after a restart.

Readiness is a view of what the current identity can act on. It is not a claim,
and a notification is a reason to reread that view rather than permission to
execute a remembered assignment. Another participant may have claimed the Work
or its inputs may have changed since the notification was sent.

On a shared route, several eligible participants can see the same opportunity.
The successful atomic claim determines who executes it. "Available to me" is
therefore different from "assigned to me."

The same distinction helps when navigating a large campaign. A bounded tree
is useful for orientation, but a participant may have eligible work below the
displayed portion. The dedicated actionable-work view answers the personal
pickup question without requiring the operator to search every branch.

Runner adapters deliver wakeups and runtime information around these protocol
operations. Their visibility does not itself grant a claim or establish that
the model has acted on a wake.

## Recovery

Suppose an agent loses its host after taking a claim. The board still records
the assignment, while another participant wants to continue the work.

Silence alone does not establish that the original executor is gone. An agent
may be busy without publishing a heartbeat, and releasing a Baton claim does
not stop its external process.

A controlled recovery establishes what happened to the executor and uses the
authorized release mechanism against the exact recorded assignment episode.
Naming only the participant would be insufficient if that participant had
already released and claimed the Work again.

Once the old assignment is safely accounted for, a new executor can continue
from the durable record. It can distinguish completed effects, uncommitted work
and unresolved uncertainty instead of treating everything after a lost
conversation as either complete or disposable.

When the failed participant was the route's only handler, ordinary route
membership may leave nobody able to release it. A configured recovery capability
gives an owning-team operator a narrow way to address that situation without
making that operator a normal executor of every route.

Which external shutdown or isolation mechanism establishes safety belongs to
the deployment. Baton records coordination ownership; it does not infer that
a process has stopped merely because an assignment was released.

## Retrying without inventing an outcome

A participant sends a handoff and loses the connection before seeing the answer.
There are two possible histories: the operation committed, or it did not.

Guessing can duplicate an effect or abandon work that never transferred.
Retrying the same operation with its stable operation key lets Baton return the
committed result when one already exists. Reusing the key for a different
request is a conflict, not another spelling of the retry.

This pattern is useful at other boundaries too: an uncertain answer should lead
to evidence lookup or an owned retry, rather than an invented success.

The coordination store remains behind its public interface. Reading or repairing
its tables directly can hide a missing operational capability and leave other
users with no reproducible path. If the supported views cannot answer a needed
question, that gap is worth recording in its own right.

## Maintenance: draining managed dispatch

An operator wants to restart a busy deployment after its current work finishes.
Each completed claim is immediately followed by another, so waiting for a quiet
moment never produces a reliable maintenance boundary.

Draining creates that boundary explicitly. Existing claims can finish, pass or
release normally while new claims stop being admitted. When the live claims
are gone, the deployment can report that dispatch is paused.

An orphaned claim remains visible as a blocker. Treating it as finished because
a runner looks unhealthy would hide the recovery decision the operator still
needs to make.

A service manager can use the paused state as the condition for a graceful stop.
An emergency stop is a different action: it may be necessary when the authority
is unavailable, but it does not imply that claims completed.

Restarting services and resuming dispatch are also separate decisions. This
distinction prevents a maintenance restart from admitting new work before the
operator has checked the deployment.

## Exporting the Work graph

A team wants to understand why an apparently small feature has accumulated a
long critical path. The visible tree shows only part of the campaign, and
reading several neighborhoods separately can mix states from different moments.

A complete graph export provides one coherent view of the relationships.
Containment shows the roll-up, dependencies show required inputs, and follow-up
or duplicate links explain other kinds of history.

This makes the export useful for questions that a personal queue cannot answer:
which outcomes are independently schedulable, where a shared provider creates
a bottleneck, or whether a supposed decomposition still contains one oversized
piece of work.

The exported data can be visualized or compared with another retained export.
Its value comes from preserving one consistent view, not from treating the
picture as a second scheduling authority. Decisions about current claims or
readiness still use current Baton state.

## Configuration changes

A team adds a reviewer and wants that participant to receive eligible work.
Editing the proposed configuration describes the intended arrangement; it does
not by itself authorize the newcomer or alter the accepted routing.

The participant accepting the change acts under the existing configuration.
A proposal cannot grant itself the authority to be accepted.

This is useful when a configuration change affects several relationships at
once. The team can review the proposed roles, handlers and routes together,
then accept them through one explicit transition instead of relying on ambient
files or different participants' assumptions.

The same discipline applies to the examples throughout this book. The project
owns its actual organization, permissions, scope and deployment. Baton makes
their coordination explicit, while the working strategies help people decide
which relationships are useful for the result they are trying to deliver.
