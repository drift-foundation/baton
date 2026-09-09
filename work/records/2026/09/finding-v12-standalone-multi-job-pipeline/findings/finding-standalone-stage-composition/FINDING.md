# Compose standalone v12 stage execution

Ledger Work: W103068

Parent: `work/records/2026/09/finding-v12-standalone-multi-job-pipeline/`

## Observed — 2026-09-06

The persistent Job Manager schedules implementation and review stages, the
Worker Manager owns durable workspaces and checkpoints, and the integration
package owns accepted-candidate admission, fenced execution, and manual
recovery. Those accepted components remain libraries. The only production
composition launches one implementation worker and returns its frozen result
to a v11 review Route.

Consequently one v12 submission cannot yet launch an independent reviewer,
record and act on its verdict, publish an accepted proposal, or drive the
serialized integrator. Performing those acts manually would violate the
two-Job proof's zero-ordinary-transition acceptance boundary.

## Confirmed boundary — 2026-09-06

Build the missing production composition as its own reviewed provider. It
composes accepted public interfaces and deployment profiles; it does not
redesign scheduling, workspace custody, checkpoint semantics, proposal
policy, integration ordering, or recovery.

The provider has three bounded leaves:

1. A review/correction stage driver launches the independently configured
   reviewer, freezes and attaches the checkpoint, records the verdict, and
   returns `changes-requested` Work to the same private development line.
2. A proposal/integration stage driver publishes the accepted candidate,
   admits its fully cross-bound account, obtains the target-global lease,
   invokes fenced integration, and records the completion or held recovery
   state.
3. A shared composition assembly binds both drivers to the persistent manager,
   profiles, credentials, status, and restart loop. It owns the common process
   and configuration boundary and follows the two disjoint drivers.

The first two leaves may advance concurrently only after they name disjoint
production and test paths. The shared assembly is not parallelized across
those paths. Reviewer and implementer use separate logical workers and agent
sessions even when an emergency profile maps both roles to one vendor.

## Acceptance

- One submitted Job advances from implementation through independent review,
  one same-line correction, accepted proposal publication, serialized
  integration, and terminal handoff without ordinary operator transitions.
- Every transition is driven from durable manager state and is safe to replay
  after process restart; container stdin/stdout lifetime is not the authority.
- Runtime launch uses explicit profiles and preserves role/session separation.
- Existing live-grant, custody, target-global lease, final-cutpoint, and
  operator-held recovery guarantees remain intact.
- Safe status and log locators remain observable throughout the composed path.
- The accepted provider supplies the exact commands, profiles, artifact roots,
  and verification surface required to freeze the two-Job proof plan.

## Non-goals

- Reopening accepted component contracts without a measured incompatibility.
- General remote adapters, a command-capable v12 TUI, or exhaustive hardening.
- Automatic policy decisions for uncertain or interrupted output.
- Running the two-Job acceptance proof inside this implementation Work.

## Independent plan revalidation — 2026-09-06

**Observed:** `job_manager.documents` admits implementation, review, and
integration stage kinds, and `scheduler.PooledManagerOperations` already
reserves a review worker after excluding the implementation worker,
participant, and principal. The persistent sweep nevertheless delegates the
same generic launch/exchange surface for every kind. The only concrete
deployment factory, `tools.single_worker`, rejects every kind and launch role
except one configured implementation Work and passes its result to a v11
review Route.

**Observed:** `worker_manager.review_cycles` is the accepted custody owner.
It creates one `(authority_uuid, work_id)` development line, grants a single
generation-fenced writer, freezes a checkpoint only after finalizing that
writer's Authority assignment, attaches a reviewer assignment for that SAME
Authority and Work, records an independently fenced verdict, and makes only
an accepted checkpoint integration-eligible. Consequently a Job's
implementation and review stages must name the same v12 Work. A submission
that gives those stages unrelated Work identities can be scheduled by the
generic parser but cannot be attached by the accepted review-cycle provider.
The production provider must refuse that shape before issuing an offer.

**Observed:** proposal publication is necessarily earlier than the initial
wording above implied. `Authority.publish` requires the exact LIVE producer
assignment. `review_cycles.freeze_checkpoint` calls
`finalize_quiescent_assignment`, which cancels and fences that assignment
before the checkpoint profile freezes the line. The retained reproduction
`repro-publish-after-fence.py` confirms that a publish attempted afterwards
refuses with `assignment generation was fenced and ended`.

**Confirmed ordering correction:** the integration driver owns proposal
publication, but its publication function is called during the implementation
ending after the generic output and proposal manifest are frozen and proved,
while the producer assignment is still live. Only then may the review driver
fence the writer and freeze the immutable checkpoint. Acceptance of that
checkpoint later authorizes the separately attributable verification,
technical-review, and configured approval receipts and admission; it does not
create the proposal retroactively. This supersedes item 2 of “Confirmed
boundary” only where that item can be read as publication after acceptance.

**Observed missing transition:** a `plan-rejected` review output projects as
`changes-requested`, but that state is terminal to the current Job Manager.
Only an abandoned offer opens a replacement episode. There is no public,
journalled operation that atomically closes the completed implementation and
changes-requested review episodes and opens their correction successors. The
accepted line provider can grant a correction writer, but no durable
scheduler act can produce the new assignment it requires. This is a measured
composition incompatibility, so the review/correction leaf may extend the Job
Manager's episode/document/schema/projection contract narrowly; it may not
create a parallel scheduler or a second account of Worker Manager state.

**Confirmed receipt policy:** the driver does not infer approval from a model
answer. A closed deployment configuration supplies separately attributable
Authority sessions and the pinned approval policy generation. Verification,
review, and approval remain three immutable Authority receipts even if one
deployment deliberately grants several capabilities to one principal.

### Reviewed Work and path split

- W103076 owns review/correction orchestration and the narrow Job Store
  correction-cycle extension: `baton_v12/job_manager/review_driver.py`,
  `job_manager/{__init__,documents,episodes,projection,schema}.py`, and focused
  tests under `tests/job_manager/`. It does not edit runtime deployment tools,
  Authority, integration modules, or the shared test registry.
- W103077 owns the provider-neutral proposal/receipt/admission/execution
  driver: `baton_v12/integration/driver.py`, `integration/__init__.py`, and
  `tests/integration/test_driver.py`. It does not edit Job Manager correction
  state, runtime deployment tools, or the shared test registry.
- W103083 owns the concrete process and configuration assembly after both
  drivers are accepted: `tools/stage_execution.py`, the required extraction or
  parameterization in `tools/single_worker.py`,
  `tests/tools/{test_stage_execution,test_single_worker}.py`, and
  `tools/parallel_test.py`. It does not redesign either accepted driver.

The two driver leaves therefore have disjoint paths. The shared assembly is
blocked on both and owns every inevitable common production/test path.

## Approved bounded composition and ownership — 2026-09-06

Slawomir approved keeping W103874 as the five-path proposal-manifest producer
owned by K and W103083 as K's bounded shared assembly. The absent producer
must be accepted before assembly; its dossier corrects the earlier proposed
worker-side `proposal.publish` remedy. Publication stays manager-to-Authority.

This supersedes an exhaustive reading of Acceptance's restart requirement as
a first-delivery test matrix. Preserve restart-safe behavior, role/session
separation and held uncertainty, prove the composed correction lifecycle and
one representative restart cutpoint, and reuse independently accepted leaf
evidence. The production composition must actually use the retained-manifest
producer. A new missing capability gets its own Work rather than growing this
assembly's path set.

Expanded coverage is recorded as independent W103950, bound to
`work/records/2026/09/finding-v12-stage-composition-hardening/`, intended for
baton.tuner. It is deferred until assembly is stable and explicitly scheduled,
outside this provider's containment and critical dependency graph. Its new
test file is disjoint from K's production, existing tests and registry paths.

Scheduling correction later on 2026-09-06: Slawomir superseded the deferred,
explicit-scheduling wording above. W103950 is approved work waiting on the
assembly, represented by a dependency on W103083 rather than a park. The
reverse dependency is not introduced; initial delivery does not wait on it.

## 2026-09-07T15-51-57Z — mandatory custody proof in assembly acceptance

**Confirmed decision:** owner reroute111426 on W105982 accepts its independent
review-2026-09-07T15-46-38Z.md. Accepted configured runtime evidence establishes
positive-stop line access, read-only review, same-line correction and checkpoint
use; actual sealed-result retention and survival after ordinary cleanup remain
unproved. This ruling supersedes waiting for full W105982 closure as a
composition prerequisite, once this residual proof is recorded here and in
`baton:work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-standalone-stage-composition/findings/finding-shared-stage-assembly/`.

**Mandatory first-delivery acceptance:** the assembled lifecycle must bind the
launched attempt and durable line/object pin to its actual completion and frozen
sealed result, record real public intake/retention receipts, and run ordinary
manager-authorized cleanup. Afterwards reopen the retained manifest and artifact
bytes at recorded locators, verify their digests, and reopen the same persistent
line with its durable pin validated. Show retained sibling custody stayed outside
every writable worker mount. Path inequality, Git checkpoint references, fixture
teardown and canned receipts do not prove this boundary. Cross-link the actual
proof and independent acceptance into
`baton:work/records/2026/09/finding-v12-private-line-custody-locators/`.

This requirement is part of W103083/W103068 lifecycle acceptance, not the deferred
hardening matrix. Preserve the existing assembly five-path focused-test/fixture
authority, custody additive-only scope and serial ownership; identify any extra
path, assertion change or execution scope before execution for scoped disposition.
Claim111429 performs documentation and only the approved W103068-on-W105982 edge
correction. No runtime or implementation is authorized by this administrative act.
W105982 and experimental child W106673 stay open; their closure/adoption gates
and production confirmed shutdown remain unchanged.

## 2026-09-07 — W112039 bounded review-ahead, owner M112547, claim112565

Owner M112547 authorizes temporary removal of the W112029 dependency solely to
claim and map accepted evidence while preserving final acceptance and downstream
gates. This supersedes waiting to perform any mapping until both provider
closures; it does not supersede the two-provider acceptance prerequisite.
The 13 current candidate hashes agree with both independent reviews. Existing
proof covers the ordinary path and lifecycle boundaries separately; the two
smallest final joins are actual admission after real freeze re-entry and public
admission refusal after missing cleanup history. Exact evidence map and limits:
evidence/joined-review-112565/REVIEW-AHEAD.md. No source/test edit or broad run.
Before relinquishing, re-read W112029 and restore its dependency if open; if
closed, continue the already authorized exact-candidate joined acceptance.

## 2026-09-07T18:45:07Z — W112039 joined acceptance, claim112565

**Confirmed:** W112029 closed satisfying112567 against its accepted manifest
before final execution; W110772 was already closed satisfying112501. Owner
M112547 therefore authorizes continuing the joined review without restoring an
open-provider gate. The two mapped gaps now pass: actual ordinary evidence and
real review-freeze re-entry reach durable Authority admission and exact replay;
missing cleanup history refuses before all receipt/admission effects. All13
candidate hashes match both accepted providers before/after, with no source/test
edit or broad rerun. This supersedes the preceding review-ahead pending-final-
checks status. Joined acceptance is recorded in review-2026-09-07T18-45-07Z.md
and evidence/joined-review-112565/. Close W112039 satisfying only; downstream
ownership, other dependencies and live restrictions remain unchanged.

## 2026-09-08 — approved multi-Job successor placement, M119126

**Confirmed owner ruling:** Slawomir approved the separate successor provider
under the stage-composition owner after independent shared-assembly acceptance,
as proposed in review-2026-09-08T12-29-16Z.md in the two-Job proof record.
This explicitly supersedes the pending-placement status of that recommendation.
Preserve the current one-Job assembly/custody/restart scope. Split multi-worker
configuration/pool composition from per-Job deployment/line binding, and require
joined acceptance before the demonstration freeze. The reviewer creates bounded
plans and dependencies before implementation. Shared source/test files are
owned serially, not by concurrent claims.

The successor's canonical record is
`baton:work/records/2026/09/finding-v12-multi-job-deployment/`. Its dossier is
promoted to a top-level path to retain readable paths and bounded dossier depth;
Baton containment still places it under the stage-composition owner. The two
implementation children each own only `v12/python/tools/stage_execution.py`
and additive controls in `v12/python/tests/tools/test_stage_execution.py`.
An explicit new multi-Job configuration variant preserves the old one-Job
schema/refusals; enumerate its exact document/interface before editing. No
external schema, scheduler/driver redesign, extra source path, unrelated test
assertion change, live runtime grant or manual-transition workaround follows.
