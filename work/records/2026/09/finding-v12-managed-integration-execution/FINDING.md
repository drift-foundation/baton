# Managed, relocatable integration execution

## 2026-09-13T14:19:08Z — mandatory separate Work, owner decision

Recorded by baton.prompt. Slawomir requires integration execution to have the
same isolation and managed lifecycle as ordinary Jobs. Execution may take place
on a different farm machine, using the existing input/output protocol designed
to permit relocation. On consolidation he clarified: "not much of a choice
there, we need that - just as a separate job".

This separate Work owns the mandatory integration-execution prerequisite.
W156162 remains responsible for per-Job execution limits and their final
recovery/isolation acceptance. W103525 remains responsible for the selected
scheduler evidence and final certification. Do not fold this implementation back
into either consumer or treat it as an optional defer/drop item.

## 2026-09-14T10:31:53Z — the reported Authority `publish_answer` blocker is WITHDRAWN

Recorded by baton.claude at claim168398, correcting my own M168341 report.

I reported that `baton_v12.authority.Session` implements every member of
`AuthorityPort`'s `SESSION_OPERATIONS` except `publish_answer`, that a
real-Authority-backed port therefore could not be constructed, and that this was
an operational finding for the Authority's owner. **The fact is true and the
conclusion was wrong.** A BARE session does lack that member and a port over one
does refuse. But this deployment already decided what that capability is:
`tools/single_worker.py`'s `_AuthoritySession` supplies an explicit typed
`capability` refusal for inquiry publication, `_ManagerClaimSession` inherits it
and translates concrete Authority claim refusals, and production `_compose_one`
composes `AuthorityPort(_ManagerClaimSession(minted), claim_signature)` with the
Authority's real signature.

**No owner API is missing, no shared source change is needed, and no Work should
be filed against the Authority for this.** What I had was an adapter I had not
looked for. `integration_worker.manager_session` / `authority_port` reuse that
exact composition rather than writing a second one, because a second adapter
would be a second account of a capability this deployment has already decided.

The true half is kept as a boundary fact rather than as a reason for a fake:
`test_a_bare_session_is_not_a_port_and_the_adapter_is_why` asserts both that the
port refuses a bare session and that the adapter's added member is a refusal
rather than a successful-looking no-op. Nothing in the suite now requires a
missing capability to stay missing.

## 2026-09-14 — two Authority facts this fixture had been hiding

Both surfaced only once the participant session was real, and both are product
facts rather than test details.

1. **A principal holds ONE live claim across every endpoint address it acts
   through** (`Core._take_slot`). The shared capacity fixture pre-claimed a
   phase assignment so admitting cases had something to admit against; under a
   real Authority that spends the integration actor's only slot before the
   preparation can take it. This is also the enforcement behind the selected
   "the parent apply cannot claim or start during preparation" acceptance: it is
   the Authority's rule, not something the coordinator remembers to check.
2. **Creation replay is operand-exact.** Re-creating a child Work under the same
   `operation_id` but a different contract is refused -- "operation id was reused
   for different operands" -- rather than quietly treated as already created.
   That is the protection working: a resumption that could reach a *different*
   creation under one identity is exactly the second child Work the committed
   intent exists to prevent.

## Existing evidence and design history

Canonical predecessor dossier:
baton:work/records/2026/09/finding-v12-per-job-budgets/.
Read its FINDING.md owner ruling2026-09-13T13:47:40Z, PLAN.md,
MANAGED-INTEGRATION-DESIGN-2026-09-13.md, DESIGN-REVIEW-161103-2026-09-13.md
and the latest subsequent design/review history before design work. These records
stay at their original paths; carry references and explicit supersessions rather
than moving or rewriting history. M161051 records the owner's protocol decision;
M161222 coordinates this separate Work with the reviewer active on W156162.

The consolidation report in
baton:work/records/2026/09/finding-v12-deterministic-scheduler-stress/CONSOLIDATION-2026-09-13T14-10-03Z.md
identifies existing review gates: parent/child capacity is not yet represented,
portable custody belongs in the first slice, and the trusted target-owner
entrypoint needs an exact design. These are design findings to resolve, not
approved implementation mechanisms. Revalidate against the latest active review.

## Required outcome

- Candidate-executing integration preparation, reconciliation and verification
  use actual managed Docker execution with bound identity, per-Job limits,
  termination, positive stop evidence, recovery and explicit capacity accounting.
- Inputs, workspace content, results and evidence cross the existing input/output
  protocol boundaries. No coordinator-local pathname/inode or direct subprocess
  assumption may stand in for portable execution custody.
- Preserve independent judgments, exact result/proposal/attempt bindings,
  failure custody, target lease/fence checks and authorized publication. A failed
  attempt must not become success when capacity is released. Target repair and
  permission for a new result remain distinct explicit operations.
- Demonstrate the selected lifecycle with deterministic providers and disjoint
  workspace roots. Do not infer actual remote deployment or live engine behavior
  from simulated evidence; use specific live verification only for a question
  deterministic coverage cannot answer under existing repository policy.

No unallocated child execution, fabricated quiescence, host-only fallback,
implicit retry, second ad hoc transport or crash-before-record exactly-once
requirement is authorized. Containerizing only the coordinator is insufficient.
Trusted target-owner operations and their capabilities must be mapped explicitly
by the design, not casually moved into an untrusted execution worker.

## Authority and provenance

The owner selects the mandatory outcome and a separate Work. Initial execution
scope is design, decomposition and independent design review only. Produce exact
interfaces, files, schema/test authority, compatibility and verification bounds
before implementation. Preserve all prior candidates/reviews/spending in their
owning records; this separation does not reset or transfer either consumer's
verification budget. Define this Work's own explicit verification scope before
new tests. No implementation or test execution was done when creating this record.

## 2026-09-13T14:33:19Z — v2 adopted by reference for independent design review

**Confirmed, baton.codex claim161312:** W156162 claim161207 completed revised
design planning; owner M161222/M161232 required this separate mandatory Work.
Dependency161306 now blocks W156162 here and canonically released its old claim.
All current Work events/discussion, owning FINDING/PLAN and predecessor design/
independent-review/response records were read. No research or runtime verification
was repeated. Historical records remain at their canonical predecessor paths.

DESIGN-HANDOFF-161312.md binds exact SHA256s for v2, response161207, prior independent
review161103, predecessor handoff and research inventory. It adopts the existing
proposal, not an implementation. V2 explicitly names root/all-member capacity,
serial admission including parent apply, every release guard, portable result
storage and bounded old/new compatibility in slice one, target-owner interface
and exact legacy/managed test mapping. The additional fenced-before-start reader
must be independently checked against cancellation/start races; no attached
runtime, quiescence receipt or Authority-gate discharge may be fabricated.

**Owner criterion M161268:** final focused verification uses project-pinned
dependencies and records actual versions. Existing jsonschema mismatch remains
qualified historical evidence; resolve/revalidate it for selected final checks.
No separate environment project absent a concrete setup problem, and no live
provider/farm run is implied. This is now in current PLAN/handoff and v2.

**Proposed only:** slice1 focused deterministic owner tests with120s cumulative
author/30s independent-review subprocess budgets, persisted per-command operands
and failures charged. Independent design review and owner exact-slice authority
precede any test or product execution. Later runtime slices require their own
bounded selection. Zero measured verification spending in this Work at adoption;
W156162 author246runs2530.5844189850177s plus4unknown and reviewer147.7342205499972s
remain charged there; W103525 retains its own ledgers. No transfer/reset.

Return the digest-bound proposal to baton.impl for independent DESIGN review only,
then baton.feat for disposition and owner implementation scope. No source/test,
implementation PROGRESS, environment or Git state changed by this adoption.

## 2026-09-13T14:46:38Z — independent design response and exact disputed premises

**Confirmed, baton.codex claim161397:** read current detail, complete new Work
events and M161364, owning dossier and DESIGN-REVIEW-161344-2026-09-13.md.
DESIGN-RESPONSE-161397.md is the current addendum to the immutable predecessor
v2. It accepts the review conditions to guard only released transitions, retain
quarantine, test _completed_integration specifically and source exclusion from
the trusted adapter on the node executing the actual phase.

**Confirmed source discrepancies:** attempts.py TRANSITIONS explicitly permits
not-started→cancel-requested; _order_quiescence records that execution-runtime
observation BEFORE the runtime_id-is-None return. request_runtime_start calls
observe(start-requested) inside the journal transaction; _decide rereads and
rejects the illegal transition, including a stale pre-read. The review's claim
that the axis stays not-started is contradicted by those paths. Integration
schema.py:432 explicitly declares UNIQUE(canonical_target_id, source_proposal_id,
target_revision); strict store adoption compares that table definition. The
review's claim that the key is new is also contradicted by source. Both files
still match research-161207.json hashes; no intervening-byte explanation applies.
The old independent review is preserved, not edited or silently superseded.

**Proposed clarification, not self-approval:** the no-start reader requires the
committed cancellation execution AXIS, absence of any effective start operation
and the exact Authority fence. Cancellation intent/fence alone is insufficient;
start can win that window. Existing committed-start replay is explicitly excluded
even without an attached runtime. This replaces v2's ambiguous "cancellation
committed first" shorthand. No new start-transition latch is proposed until an
independent review identifies a real uncovered interleaving. Gate2 remains open.

The addendum retains existing result-key uniqueness, adds cross-representation
checks and precise pre-mutation refusal for malformed historical duplicate/shape
input, without redundant indexes, deduplication or a second target store. Exact
slice1 paths and additive tests remain the proposal; no generic transition or
later-runtime expansion. Return for focused independent re-review of these deltas,
then owner exact-slice selection. Do not repeat the full prior design research.

No tests, executable probes, runtime/provider calls, environment/source/test/
PROGRESS/Git mutations or direct coordination-store access. W161230 measured
verification remains0; proposed120s author/30s reviewer is not yet authority.
W156162 and W103525 costs remain in their original ledgers with no transfer/reset.

## 2026-09-13T14:59:52Z — all design gates accepted; exact slice1 selection prepared

**Confirmed, baton.codex claim161491:** current detail, all new Work events,
M161449 and full DESIGN-REVIEW-161426-2026-09-13.md were read. The independent
review accepts all five gates and explicitly withdraws its two prior incorrect
findings. This supersedes the open-gate2/re-review-next state above. Prior reviews
and the source-bound response remain unchanged history. Fresh design/response/
latest-review digests match and are bound in SLICE1-SCOPE-161491.md.

The narrowed fenced-before-start reader stays a read-only addition; no start
transition change or enumeration reader is needed. Derive its exact start ID
from the same attempt row, including runtime attempt, fixed assignment and
profile digest as _start_operation_id actually does. Any committed start blocks
proof without guessing whether the adapter ran. All six evidence facts and the
intent/fence/axis race distinction remain mandatory. Accepted release/quarantine,
cross-representation uniqueness and trusted execution-node evidence conditions
are carried into the packet's finish conditions.

**Proposed owner selection:** slice1 only, exact11 source paths plus DEPLOYMENT,
four new additive test paths,120s author/30s reviewer cumulative subprocess
allowance with persisted operands and all failures charged. No old test assertion
changes, generic transition rewrite, actual container/provider execution, image
installation or later-slice authority. Independent design acceptance is not
implementation authority; route the concrete packet to baton.decide, then pin
the ruling before a normal implementer handoff. No full-feature certification.

Both W156162 and W161234 are now canonically blocked on this prerequisite;
161487 records the latter and released its planning claim. Their separate
acceptance and spending remain unchanged. This planning turn ran no tests,
probes or runtimes and edited no product/test/PROGRESS/Git/environment state.
W161230 measured verification0; no predecessor budget reset or transfer.

## 2026-09-13T15:20:50Z — owner approves slice1 with amended600s/300s allowance

Pinned by baton.codex under claim161619 after reading current detail, complete
new Work events and owner response161614/return161615.

**Owner M161614, answering161508:**
> Approve SLICE1-SCOPE-161491.md path set and finish conditions, amending slice1 cumulative subprocess allowances to author600s/reviewer300s. Preserve persisted budget guards, deterministic verification, pinned dependencies and independent review. No later-slice authority, predecessor spending transfer or acceptance waiver.

Return161615 directs: pin this scope and amended allowance, then hand slice1 to
baton.impl, next baton.feat for independent candidate review. The ruling explicitly
supersedes the packet's proposed120s/30s allowance and pending-approval status;
its exact path set and finish conditions remain unchanged. The original scope
packet and independent reviews are preserved at their accepted digests.

IMPLEMENTATION-HANDOFF-161619.md carries the concrete authorization and exact
references. Approved scope remains11 source paths plus DEPLOYMENT and four new
additive test files, no old assertion changes, generic start rewrite, real runtime/
provider execution, installation or later-slice implementation. All five design
gates were independently accepted by review161426. Implementation is assigned to
the normal baton.impl claimant; this reviewer was not reassigned to product work.

At handoff preparation, measured W161230 verification remains author0/reviewer0.
Persist each command's fresh budget operands and charge all failures/timeouts;
the larger cumulative caps do not waive guards. W156162/W103525 costs remain in
their own records, and W156162/W161234 remain dependent on complete managed
execution. No tests/probes/runtimes or product/test/PROGRESS/Git/environment
changes occurred in this pinning turn. No additional approval gate is introduced.

## 2026-09-13T15:38:01Z — partial condition3 candidate: changes requested

**Confirmed, baton.codex claim161686:** author161638 delivered only the no-start
reader/document/new test. Fresh hashes match M161676/return161678. Append-only
review-2026-09-13T15-38-01Z.md binds those bytes and records two P1 evidence
validation defects: absence of a live assignment replaces positive Authority
fence evidence, and the committed local intent result/signature are not matched
to the fixed attempt/assignment/Authority operation. Durable probe-161686.py
reproduces acceptance of both absent Authority operation evidence and a foreign
intent through temporary owners/fake session boundaries. These are simulated
inconsistent evidence tests, not claims of observed corruption in a real ledger.

**Confirmed coverage:** existing new-reader/contract tests26 pass; independent
four probes yield the two defects and two passing actual interleavings (stale
start pre-read and committed start delayed at adapter entry without runtime row
edits). Add these and exact replay coverage to the approved new test file. No
generic start-transition change is indicated. Earlier accepted design corrections
remain intact. Reader condition3 is not yet signed off, and conditions1/2/4/5
plus DEPLOYMENT remain unimplemented.

**Scope qualification:** Authority session exposes operation_record/result;
AuthorityPort does not currently wrap them. Its existing project_work returns
fenced_generations but currently treats those values as unread. Revalidate the
existing public seam for positive exact-assignment fence evidence. If a new port
boundary is necessary, return the precise path/API amendment before editing it.
No private-session bypass or evidence waiver is authorized by this review.

**Verification:** review-ledger-161686.json records three guarded children and
all failures, including corrected reviewer fixture errors in the first probe run.
Cumulative reviewer0.691149097008747/300s, remaining299.30885090299125s; author
52.11094649601/600s, remaining547.88905350399s. Python3.13.7/jsonschema4.19.2
qualifies these defect checks; pinned4.26.0 final verification remains required.
No installation, provider/runtime launch or broad suite. Author inventory logs
report the same24 failures against candidate and baseline; review inspected logs
without repeating source replacement. That evidence remains unresolved, not
green acceptance. Earlier zero-spending/current-handoff wording is superseded by
this entry and current PLAN; historical records remain unchanged.

Return to baton.impl for corrections and the rest of the approved slice, carrying
exact scope and cumulative ledgers. Reviewer edits only FINDING/PLAN and durable
review evidence, not product/old tests/PROGRESS/Git. W156162/W161234 remain blocked
on complete managed integration; no partial sign-off releases those dependencies.

## 2026-09-13T15:47:57Z — condition3 corrections and remaining projection defects

**Confirmed, baton.codex claim161769:** author161737/M161765 corrected local
intent/result/signature matching and added actual stale-read/delayed-adapter
interleavings. Positive fenced-generation evidence through existing project_work
is an acceptable public seam; no new AuthorityPort wrapper is required. Independent
exact committed-start journal replay also passes without invoking its action.
These resolutions supersede the prior review's current action on those points;
the historical review remains unchanged.

**Remaining defects:** the projection is not required to name the fixed Work,
and the newly consumed fence entries are not fully owned before comparison or
diagnostics. probe-161769.py reproduces proof from a foreign/missing Work identity,
boolean generation, missing reason and duplicate generation. Mixed unmatched
string/integer generations raise raw TypeError during diagnostic sorting. Float
generation already refuses at the outer document boundary. These are simulated
inconsistent Authority-boundary responses, not observed corruption in the actual
Authority. Require the exact Work binding and closed typed unique fence records
within the approved reader/test scope; shared helpers stay unchanged.

Append-only review-2026-09-13T15-47-57Z.md binds exact candidate hashes and detailed
remaining work. New reader/contract tests33 pass. Independent5 methods demonstrate
the safe committed-start replay and five failing refusal assertions plus one
TypeError. review-ledger-161769.json carries prior spending and both guarded runs:
reviewer1.1686485070094932/300s, remaining298.8313514929905s. Author cumulative
56.971399261012266/600s, remaining543.0286007389877s. Earlier totals are superseded
as current balances, never reset. Python3.13.7/jsonschema4.19.2 remains qualified;
pinned4.26.0 final verification is outstanding. No installation/runtime/provider
or broad suite, and no repeat of the24 reported baseline inventory failures.

Return to baton.impl for these bounded corrections and the rest of the approved
slice1 (conditions1/2/4/5 and DEPLOYMENT still unstarted). Continue authorized work
when possible instead of returning solely because the partial reader is green.
No new scope approval within the accepted path set; no candidate sign-off,
later-slice authority or dependency release. Reviewer changed dossier records
only, with no product/shared-test/PROGRESS/Git mutation.

## 2026-09-13T16:00:12Z — prior defects corrected; bounded fixture amendment

**Confirmed, baton.codex claim161844:** author161797/M161835 corrected exact Work
binding, boolean/duplicate/missing-reason fence records and diagnostic type use.
The five independent probe161769 methods now pass, including committed-start
replay, along with40 reader/contract tests. This resolves those earlier concrete
findings; append-only review-2026-09-13T16-00-12Z.md supersedes their current
action wording while preserving the historical reviews.

**Remaining P2:** _owned_fences silently discards unknown entry members instead
of enforcing the required closed generation/cause/reason document. New independent
probe-161844.py reproduces acceptance of an added unrecognized field. Correct
using the existing closed boundary in the approved reader/new-test scope. No
AuthorityPort or generic start change is needed; condition3 is not fully signed
off yet. These are simulated boundary faults, not claims about the live Authority.

**Confirmed scope issue:** the approved capacity schema addition requires its
tables to be removed when the existing test_store.write_schema_2 fixture builds
an older schema by subtracting current objects. Otherwise strict migration
correctly reports those unexpected objects; author step15 records six affected
cases. The author reverted the capacity schema and its hash is unchanged. The
earlier CREATE-comment/insertion errors explain construction mistakes, not a
need to relax migration checks. No product migration changes were made here.

SCOPE-AMENDMENT-161844.md requests exactly two DROP statements in the ONE helper
MigratingPinsTheAuthorityWithoutRenamingAnything.write_schema_2 in
v12/python/tests/job_manager/test_store.py. There is no separate adjacent schema3
fixture to edit, correcting the author's request wording. Assertions and expected
behavior remain untouched. Review independently recommends the amendment; it is
not applied and remains subject to the owner's exact path selection.

Decision packet SHA256:
6b8d39adc1dbcd4f320a114879a428b6b3b0e7014e6742b97d8799f75d25e300.
Proposed migration-fixture-amendment-161844.patch SHA256:
d2f8ae3cc3de3c0159c0506e758fbcb8f5aa40b7d94b27ed9206c0d8bedf7dc0.
Current target base SHA256:
d6c9e17b5f5c5afb7f0be820533fda8e469f6b4eb566d59d524dbaeef2fc035b.

Route baton.decide for that precise amendment, next baton.feat to pin the ruling
and resume implementation of all remaining approved slice1 work. This scope
question follows SLICE1-SCOPE-161491.md's explicit exclusion of existing test
paths; no interactive confirmation or new blanket test permission is requested.

review-ledger-161844.json carries all prior spending plus three guarded children:
reviewer1.8098568630084628/300s, remaining298.19014313699154s; author17 runs
58.71567680201406/600s, remaining541.2843231979859s. Prior balances are superseded
as current totals without resetting them. Python3.13.7/jsonschema4.19.2 remains
qualified until pinned4.26.0 final verification. No installation, real runtime,
provider or broad-suite execution. No candidate sign-off, later-slice authority,
acceptance waiver or dependency release. Reviewer changed dossier records only.

## 2026-09-13T16:54:28Z — owner approves the exact fixture amendment

Pinned by baton.codex claim162161 after current canonical detail, successful
claim, complete new Work events and owner response M162156 to obligation161874.

**Owner M162156:**
> Approve SCOPE-AMENDMENT-161844.md and migration-fixture-amendment-161844.patch. Preserve existing budgets, assertions, acceptance conditions and independent review.

Return162157 directs pinning the amendment and handing remaining slice1
implementation to baton.impl. This ruling supersedes the amendment packet's
proposed/pending status and the original selected scope's exclusion of this exact
existing-test helper edit. It authorizes only the two stated DROP statements in
MigratingPinsTheAuthorityWithoutRenamingAnything.write_schema_2 within
v12/python/tests/job_manager/test_store.py, alongside the capacity schema addition.
No separate schema3 fixture or assertion edit is authorized. All other M161614
scope boundaries and safeguards remain.

The packet hash6b8d39adc1dbcd4f320a114879a428b6b3b0e7014e6742b97d8799f75d25e300,
patch hashd2f8ae3cc3de3c0159c0506e758fbcb8f5aa40b7d94b27ed9206c0d8bedf7dc0 and
target base hashd6c9e17b5f5c5afb7f0be820533fda8e469f6b4eb566d59d524dbaeef2fc035b
all match freshly. Original packets remain unchanged decision evidence.
IMPLEMENTATION-HANDOFF-162161.md carries exact scope, the remaining closed-fence
P2 correction and conditions1/2/4/5/DEPLOYMENT to the next implementing claimant.
No further permission request is needed within that approved scope.

No tests/probes or product/test/PROGRESS/Git/environment changes in this pinning
claim. Author stays58.71567680201406/600s, remaining541.2843231979859s; reviewer
stays1.8098568630084628/300s, remaining298.19014313699154s. Persisted guards,
pinned final dependencies, independent candidate review and original acceptance
remain. No budget reset, later-slice authority, sign-off or dependency release.

## 2026-09-13T17:06:59Z — reader corrected; capacity and fixture review

**Confirmed, baton.codex claim162221:** author162181/M162218 closed the fence-entry
document. Reader26/contracts15 tests pass and the independent unknown-member
regression passes. This resolves the prior remaining P2; condition3's source fix
is accepted in this partial review, with final pinned-dependency qualification
retained. review-2026-09-13T17-06-59Z.md binds current exact candidate hashes.

**Static capacity findings:** the preserved unwired integration_capacity.py does
not fully bind root/member identity to actual claims/configured capacity; admission
does not enforce reserved-root and successful-preparation/authorized-apply gates;
ending accepts arbitrary text instead of validated exclusion and lacks its claimed
recovery transition. Pending tests invent child identity and end with strings,
and call release with a completion reason rather than driving the required
_completed_integration branch. Required race/retry cases are absent. These are
source/test findings, not runtime reproductions against the reverted schema.
The14 author cases do not establish completion of accepted conditions1/2.

The reverted schema and scheduler guard have no exact preserved candidate locator
in the handoff/dossier; only the pending test and unwired module are named.
Restore and bind actual bytes on the next handoff. Review cannot infer a candidate
or its constraints from a green log, and did not reconstruct one from scratch.

**Explicit audit correction:** the earlier statement about one drop-based fixture
was true only within test_store.py. My suite-wide scope audit was incomplete.
The two schema3 fixtures in test_scheduling.py require the same subtraction;
wording implying no such separate fixtures exist is superseded. A broader search
also found test_execution_limits.py:schema_four copying current DDL except the
4→5 object. A measured probe of that real constructor with synthetic future
objects confirms all three capacity object names survive under a schema4 stamp.
This is fixture-construction evidence, not a candidate migration reproduction.
No change to the immutable real schema4 golden fixture is needed.

SCOPE-AMENDMENT-162221.md recommends exact constructor-only additions to those
two test paths, preserving assertions. It supplements the approved M162156
test_store amendment. Packet SHA256:
532c0a9d5dbcfa1ac199597e8755bd16b7c4cedc5a0fd3955e6d6e08b664ea04.
Proposed migration-fixtures-162221.patch SHA256:
d209fabced9d2964d9930aea8f7355e313f3fea1174e4812fe396ff8ca655211.
Route baton.decide for this exact added scope, next baton.feat to pin and hand
implementation back. No proposed product/test edits were applied by the reviewer.
The capacity corrections themselves remain within the original approved scope.

review-ledger-162221.json carries three guarded children and all earlier costs:
reviewer2.55111917200702/300s, remaining297.448880827993s; author24 runs
60.79389204701147/600s, remaining539.2061079529885s. Historical totals remain
history; no reset or predecessor transfer. Python3.13.7/jsonschema4.19.2 evidence
is qualified until pinned4.26.0 final checks. Conditions4/5/DEPLOYMENT remain.
No installation, real runtime/provider, broad suite, product/test/PROGRESS/Git
mutation by reviewer, full slice1 sign-off, later-slice authority or dependency
release. Current PLAN reflects the exact amended-scope decision and corrections.

## 2026-09-13T17:12:10Z — owner approves remaining exact fixture adaptations

Pinned by baton.codex claim162279 after current canonical detail, successful
claim, full new Work events and response M162274 to obligation162258.

**Owner M162274:**
> Approve SCOPE-AMENDMENT-162221.md and migration-fixtures-162221.patch for the exact fixture-construction changes. Retain M162156 approval, existing budgets, assertions, acceptance conditions and independent review.

Return162275 directs pinning and an implementation handoff carrying ALL findings
from review-2026-09-13T17-06-59Z.md, restored candidate provenance and completion
of accepted slice1. The extra whitespace in that return's review filename does
not identify another record; the exact existing filename is used here.

M162274 explicitly supersedes the second amendment's proposed/pending status and
the original exclusion of these exact test-constructor edits. It authorizes the
two schema3 drop-tuple changes in test_scheduling.py and schema_four DDL exclusion
in test_execution_limits.py alongside the capacity schema addition. M162156's
test_store.write_schema_2 approval remains; assertions, golden fixture and other
helpers remain outside those edits. No further permission is needed within the
approved scope, and no budget extension or acceptance waiver is granted.

Fresh matching hashes: packet
532c0a9d5dbcfa1ac199597e8755bd16b7c4cedc5a0fd3955e6d6e08b664ea04;
patch d209fabced9d2964d9930aea8f7355e313f3fea1174e4812fe396ff8ca655211;
test_scheduling base5780dc171e4b791d0488f78b3b531c7d31e04f833878523f2f38bf518b57f0ea;
test_execution_limits base2271ef93151b5a331008f2a1fcad5974ae3daa539cb6d9696eac56715074f215.
IMPLEMENTATION-HANDOFF-162279.md carries exact ownership, all substantive capacity
findings, pending conditions4/5/DEPLOYMENT and required restored candidate binding.
Earlier packet/review bytes remain unchanged historical evidence.

This pinning claim ran no tests/probes and changed reviewer records only, with no
product/test/PROGRESS/Git/environment mutation. Author stays60.79389204701147/600s,
remaining539.2061079529885s; reviewer stays2.55111917200702/300s,
remaining297.448880827993s. Guarded cumulative spending, pinned final dependencies
and independent review remain. No candidate sign-off, later-slice authority,
predecessor transfer or dependency release.

## 2026-09-13T17:13:52Z — standing test authority supersedes amendment gates

M162289 from baton.prompt carries Slawomir's confirmed ruling and directs this
reviewer to update FINDING/PLAN/handoff. Read the actual newly pinned
OWNER-TEST-AUTHORITY-2026-09-13.md and AGENTS.md section "Standing test-change
authority until further notice" after pass162291. This is authorized coordination
and planning following handoff; no new execution claim is inferred.

**Confirmed owner decision:** until Slawomir revokes it, all Baton Work and all
implementing/reviewing/integrating roles may make necessary test, fixture,
assertion, expected-behavior and registry changes within the authorized Work
outcome without per-test, helper or additional-test-path owner approval.

This explicitly supersedes older test-only approval/path restrictions, including
the W161230 gates underlying obligations161874 and162258 and narrow test wording
in the preceding approved scope/handoffs. Those approvals remain historical
evidence. No further test-only amendment return is required. Record paths/reasons
and coordinate ownership as documentation, not an approval gate. Current PLAN and
IMPLEMENTATION-HANDOFF-162279.md now carry the ruling ahead of older wording.

Independent review still checks expectations against accepted behavior. Required
acceptance and genuine defect coverage cannot be waived merely for passing tests.
Product scope, existing budgets, claims, Git ownership and reviewed candidate
provenance remain applicable. baton.prompt owns the policy and decision-note
edits; this reviewer changes only its planning/handoff records and communicates
the ruling to the implementation recipient. No test execution or budget change.

## 2026-09-13T17:23:49Z — restored partial candidate, changes requested

Claim162325 consumes return162322/M162320 and the current dossier. Independent
review-2026-09-13T17-23-49Z.md binds all ten matching candidate digests. The previous
unwired/missing-schema-provenance state is explicitly superseded by restored
schema, scheduler guard and capacity module at their approved paths. The three
historical migration constructors carry their approved fixes; standing M162289
test-change authority continues without another test-only amendment gate.

**Confirmed:** Job/Work/stage/episode derivation, stage-kind and participant checks,
reserved-root admission and successful-preparation ordering improve the previous
findings. **Still open:** actual owner claim/offer/profile/input/task binding,
collected preparation/authorization binding, owner-validated exclusion and recovery,
real completion-observation and admission/ending/release races. Root registration
also still accepts and stores caller authority_uuid unchanged; PROGRESS's claim
that all three identity operands disappeared is incorrect. JobStore owns the
Authority binding. The newest review requests its use and an attributable author
correction, without rewriting author-owned PROGRESS.

Conditions1/2 remain incomplete, conditions4/5/DEPLOYMENT remain pending, and prior
qualified reader acceptance remains. Return to baton.impl to complete approved
slice1 or name a concrete blocker, carrying the newest review and
IMPLEMENTATION-HANDOFF-162279.md. No new permission is needed inside this scope.

No tests/probes executed by this review of acknowledged unfinished work. Author
ledger161638:28 runs,62.26224235301197/600s, remaining537.737757646988s; latest
reported183 pass remains qualified by jsonschema4.19.2 versus required4.26.0.
Reviewer ledger162221 stays2.55111917200702/300s, remaining297.448880827993s.
No source/test/PROGRESS changes, dependency release, later-slice authority,
installation, live-provider execution or Git mutation.

## 2026-09-13T17:33:59Z — Authority correction and existing digest-owner surfaces

Claim162401 consumes return162398/M162392. New append-only
review-2026-09-13T17-33-59Z.md confirms the root Authority comparison and real
activated-assignment/Work/Authority checks. Its foreign-Authority probe passes;
the previous caller-controlled Authority finding is resolved, and the author has
appended the requested correction. Both changed and eight retained hashes match.

**Confirmed, superseding the claimed reader blocker:** claimed_offers_for exposes
the claimed offer's identity and digests; ControlStore.operation_record for
attempt.record:<attempt_id> exposes the committed immutable configured operands.
Both are existing public owner surfaces. probe-162401.py demonstrates these with
assignment_of in one ControlStore snapshot against real offer/accept/claim/activate
fixtures and a deterministic Authority fake. A new attempts.py reader is not
required to compare the planned member, claimed offer and recorded attempt.
The new review gives the exact owning symbols, validation requirements and
bounded implementation direction within the already approved capacity module.
No direct SQL/private reader or product-scope expansion is proposed.

**Observed P1:** the same probe confirms current admission accepts an unissued
planned offer and differing profile/input digests. Its observation assertion is
a defect baseline, not accepted behavior. Add real refusal regressions and owner
agreement coverage in implementation. Both-phase/parent-apply binding, collected
preparation/authorization, owner-validated ending/recovery, actual completion-path
and race coverage, conditions4/5 and DEPLOYMENT remain due. Prior reader acceptance
remains qualified. Return to baton.impl to complete the approved scope, with the
existing-reader blocker resolved rather than another permission request.

Guarded reviewer child0.21362990100169554s; cumulative2.7647490730087156/300s,
remaining297.2352509269913s, review-ledger-162401.json and review-run-162401-1.log.
Author35 runs64.13167826800782/600s, remaining535.8683217319922s, ledger161638.
Three independent research checks pass, one documenting the admission defect.
Author183-pass result was not repeated. Actual Python3.13.7/jsonschema4.19.2 remain
qualified against required4.26.0 final verification. Only reviewer records/evidence
changed. Standing M162289 test authority, budgets, product scope and Git ownership
remain; no slice approval, dependency release or later-slice execution.

## 2026-09-13T17:38:55Z — offer/digest comparisons added, slice still incomplete

Claim162443 consumes return162436/M162435 and records independent static review
in review-2026-09-13T17-38-55Z.md. Both changed and eight retained candidate hashes
match. The new single-snapshot offer/attempt-record composition and three-way
profile/input comparison address the previous permissive-admission reproduction
at source level; this supersedes the claim that those comparisons are absent.
The two refusal regressions correctly test offer identity and each planned digest.

**Open P2:** full signature envelope/operand/result ownership is still missing;
the implementation extracts operands from arbitrary JSON and checks only attempt
identity plus the compared digests. The offer's Authority and participant also
remain outside the cross-owner identity comparison. Add the bounded checks and
isolated malformed/contradictory record regressions described in the review, while
retaining the existing public-reader approach. No new source scope is needed.

Owner exclusion/recovery, actual parent/two-phase and task/content/authorization
binding, real completion-path/race coverage, conditions4/5 and DEPLOYMENT remain
unfinished. Return162436 names no new external blocker after118 seconds of author
custody. The next implementing claim must finish the accepted slice rather than
return after one more local correction/partial suite; a concrete completion
constraint, if any, must be stated. This is not an additional approval gate.

Author38 runs65.21625075602788/600s, remaining534.7837492439721s, ledger161638.
Reviewer unchanged2.7647490730087156/300s, remaining297.2352509269913s,
review-ledger-162401.json; no tests/probes this static review. Author185-pass
evidence remains qualified by jsonschema4.19.2 versus required4.26.0. Reviewer
records only; no product/test/PROGRESS/Git edits, slice acceptance, dependency
release or later-slice authority. Standing test-change authority remains in force.

## 2026-09-13T18:02:07Z — lifecycle progress, parent/content gaps reproduced

Claim162562 consumes return162560/M162559. New append-only review
review-2026-09-13T18-02-07Z.md confirms all ten candidate hashes and independently
runs52 capacity tests plus2 defect observations. Closed journal/complete offer
checks, explicit recovery and cancelled-settlement refusal, owner-resolved
exclusion and actual _completed_integration branch tests supersede the prior
absence/wrong-branch findings within the review's stated qualified limits.

**Confirmed P1:** apply Work/offer/attempt all differ from the actual parent
episode in the real current fixture, yet the claimed apply is admitted. Both
phase names and a parent-content digest do not bind the actual parent identity
required by accepted v2 section A. **Confirmed P1:** a caller digest is recorded
as successful preparation content while frozen_output_of is None before and
after; no freeze/collection occurs. Exclusion cannot supply output success or
derived-candidate authorization. These observations reject the handoff claim
that conditions1/2 are finished; they are defect baselines, not accepted outcomes.

**Open P2:** sequential order/replay and a patched _members index test do not
exercise competing store transactions. Preserve them and add controlled actual
connection contention/interleavings. The real completion-branch test is accepted
separately. Finish parent/task/collected-content/authorization binding together
with the approved portable owner contracts, compatibility/uniqueness, trusted
placement and DEPLOYMENT (conditions4/5). Author's working-context constraint is
recorded; scope and completion requirements remain unchanged.

One guarded child0.46390574499673676s, review-ledger-162562.json and
review-run-162562-1.log; reviewer cumulative3.2286548180054524/300s, remaining
296.77134518199455s. Author48 runs70.00656952105055/600s, remaining529.9934304789494s,
ledger161638.52 candidate tests pass and2 probes document the remaining defects.
Actual Python3.13.7/jsonschema4.19.2 remains qualified; author reports required
4.26.0 unavailable, .venv lacks metadata and pip absent. No installation authority
or attempt is inferred; final pinned verification remains outstanding while
authorized source work can continue. Reviewer records/evidence only; no product,
test, PROGRESS, Git, runtime/provider changes, slice acceptance or dependency release.

## 2026-09-13 — owner clarifies local information exchange, M162617

Recorded by baton.prompt from Slawomir's interactive clarification:

> we don't need to ensure today that we are capable of running across machines, but we need a clearly defined interfaces that exchanges information, with file:// or similar. This is no different than how we pass input to workers today

Required now: explicit integration input/output interfaces following the existing
worker exchange pattern, with file:// or equivalent local references to the
actual inputs, reports and output artifacts. Local managed Docker execution is
the delivery target. The boundary should permit a future transport/placement
implementation without making today's integration depend on reaching across
machines or interpreting another machine's private paths.

This explicitly supersedes any reading of the original relocatable/farm wording,
adopted v2 design, disjoint-root placement replay or later-slice acceptance as
requiring working cross-machine execution, remote transport/backend deployment
or a multi-host demonstration for W161230 closure today. Future relocation is
the reason to define the interface, not a capability to implement or certify now.
file:// is an acceptable example, not a mandate to invent a new URI scheme or
transport in place of the existing worker input/output mechanism.

The placement interface is the bounded local adapter between those explicit
references, managed execution and the existing target owner. Reuse current
worker delivery/collection interfaces; justify any integration-specific addition
by a concrete local need. No distributed service or farm abstraction is required.

Ordinary managed isolation/lifecycle, per-Job limits, actual parent/attempt
identity, real collected-result validation and authorized target publication
remain required. In particular, caller-supplied matching digests still cannot
substitute for collected output. The latest review's two P1 findings and actual
transaction-race coverage remain relevant to local correctness. No acceptance,
budget or candidate-review waiver follows from deferring remote execution.

Current PLAN carries this clarification; M162617 informs baton.impl and baton.feat.
Prompt edits only this finding and the plan, preserving the active implementer's
product/test/PROGRESS ownership. Apply the clarified local scope to remaining
interfaces, documentation and later-slice selection; preserve earlier decisions
as history rather than silently rewriting their accepted packets.

## 2026-09-13 — owner requires reuse of the existing input/output model

Recorded by baton.prompt after inspecting the current Job submission, worker
inputManifest/artifactRef schema and deployment contract. Slawomir confirms:

> yes, we must reuse this model - its OK that today we are local but we have a mechanism that we can extend if needed

Reuse is mandatory, not merely an example of an acceptable new interface. Job
input_digest identifies input; worker manifests describe artifacts with locator,
content_digest, bytes and media_type. Local deployment supplies task_document
and nominated_source paths, delivering task and source through the existing
worker input boundary. A locator is not automatically a host path: preserve the
existing distinction between an artifact reference and its local materialization,
including the task byte/digest checks. Reuse the existing output freeze/collection
model for integration results and bind their integration-specific contents to
the actual execution and target authorization.

This strengthens M162617 and supersedes any interpretation of portable contracts
or the placement interface that introduces a parallel general input/output,
artifact-reference, path-resolution or transport mechanism. Integration-specific
task/report contents and owner validation may be added where needed; compose
them with existing worker exchange rather than duplicate it. Local operation is
sufficient today. Preserve this extension boundary for future needs without
implementing or certifying cross-machine execution now.

Current PLAN reflects mandatory reuse. Prompt owns only this append and the plan
clarification; implementation, tests and PROGRESS remain with the live handler.

## 2026-09-13T18:21:26Z — local-scope review and new contract defects

Claim162696 consumes return162693/M162691 and owner M162617/M162634/M162659.
review-2026-09-13T18-21-26Z.md carries local delivery and mandatory reuse, with
W32577 tuner planning overlap coordination preserved. All13 candidate hashes match.
Actual parent identity, owner frozen-output presence (without caller digest) and
two-connection tests resolve the specific prior parent/absent-output/connection
findings within qualified deterministic coverage. This explicitly supersedes their
previous current-state descriptions; integration-specific report/content/grant
validation remains unfinished and is not inferred from a generic completed freeze.

**Confirmed P1:** adopt_managed_result bypasses collected_report semantics. An
unknown kind, boolean status, undeclared commands/dropped suffix and not-collected
carrying status/completed commands all cross adoption unchanged. **Confirmed P1:**
managed_task rejects execution_limits.resolved's real owner document, while
accepting effective={} with generation999. Reuse the real Job limits semantics
and one complete report owner at every crossing; test actual owner output and
mutated serialized results. Three research checks record these defects rather
than approving their permissive behavior.

The new integration/__init__.py re-exports are outside the exact product scope;
remove the unnecessary additions and use the approved module directly. This is
not a test-change amendment or another approval gate. Continue remaining portable
storage/migration/shared uniqueness, actual task/content/derived-candidate/grant
binding, local placement and DEPLOYMENT. Do not build a parallel exchange or
require remote/multi-host certification. Existing claim/budget/source ownership
and independent review rules remain; no slice acceptance or dependent release.

Independent61 capacity +32 contract tests pass plus3 defect observations, one
guarded child0.7140777979948325s. review-ledger-162696.json and
review-run-162696-1.log retain evidence. Reviewer cumulative3.942732616000285/300s,
remaining296.0572673839997s; author59 runs78.28918114805128/600s,
remaining521.7108188519487s, ledger161638. Actual Python3.13.7/jsonschema4.19.2 is
qualified; pinned4.26.0 final and the recorded environment gap remain outstanding.
Reviewer records/evidence only; no source/test/PROGRESS/Git/install/runtime/provider
changes. Handoff retains current local scope and M162289 standing test authority.

## 2026-09-13T18:34:36Z — report adoption fixed; pinned limits values still forgeable

Claim162787 independently reviews return162768/M162767 in
review-2026-09-13T18-34-36Z.md. The report-adoption bypass is resolved for all four
previous malformed variants; real owner limits generations0/1 are accepted, and
integration/__init__.py is byte-equal to HEAD. These facts explicitly supersede
the previous current-state failures for those specific issues.

**Confirmed P1:** the new limits validator checks vocabulary/ranges and explicit
request consistency, but does not bind preserved values to the known generation.
Starting with the real resolved empty request, generations0/1 each accept provider
seconds7200 instead of3600, default_seconds7200 instead of3600, or both. Reuse the
owner's complete resolution after validating requested settings and exact types;
do not add another defaults authority. probe-162787.py records all six defects.
This narrows, rather than closes, the previous limits P1.

Independent52 contract cases and3 research checks pass, including the deliberate
defect observations; no acceptance of permissiveness. Reviewer child
0.16366126999491826s, cumulative4.106393885995203/300s,
remaining295.8936061140048s in review-ledger-162787.json. Author63 runs
81.31653186904441/600s, remaining518.6834681309556s. Qualified4.19.2 versus
pinned4.26.0 final verification gap stays recorded. The remaining accepted
storage/local-placement/task-content/grant work still must be completed; strict
store adoption is implementation context, not an external blocker. Preserve
M162617/M162634 mandatory local exchange reuse and W32577 file ownership.

## 2026-09-13T18:51:48Z — portable storage review requests corrections

Claim162882 reviews return162880/M162878; exact seven-path candidate table and
independent evidence are in review-2026-09-13T18-51-48Z.md. All hashes match.
The six forged-default values now refuse, explicitly superseding the prior
current-state numerical-default finding. Exact integer validation still accepts
True for a resolved1-second boundary; the owner rebuild must preserve types.

**Confirmed P1:** record_managed_result omits the immutable task from its replay
signature. Independently changing only task/input/harness digest returns the
original stored task without a collision. **Confirmed P1:** managed reads accept
simultaneous legacy/new representations for the same shared key, contrary to
accepted v2 reader ownership. **Confirmed storage mismatch:** the candidate owns
phase rows, while accepted v2 owns a portable result with existing state/history
semantics. Two phases for one proposal and admitted snapshot collide; the new
positive test changes the revision. Align result ownership without weakening
shared uniqueness or inventing revisions/derived identities. Condition4 is not
accepted as delivered.

**Confirmed P2:** upgrade rechecks only version under its write lock. Injecting
a concurrent missing-index change after preflight still commits schema6, which
normal open then refuses. Revalidate complete ownership under the mutation lock.
Complete malformed-data and populated live-lease/entry/result/journal preservation
coverage; current preservation tests inspect definitions and one target row.

Independent54 contract and21 storage cases pass. Final81-check run includes six
research checks deliberately observing defects, not approving them. First run
had one research error because the reviewer hypothesized float acceptance and
the existing POD owner correctly refused it; the boolean acceptance assertion
had succeeded. The corrected run preserves float refusal as a positive control.
Both guards/logs/costs are retained in review-ledger-162882.json and
review-ledger-162882-2.json: reviewer4.6338191269824165/300s,
remaining295.3661808730176s; author68 runs98.33473982804571/600s,
remaining501.6652601719543s. Qualified4.19.2 versus pinned4.26.0 remains.

Continue corrections and remaining placement/task-content/grant scope under the
current authority and local exchange reuse. Preserve W32577 file handback; no
new test-only approval, slice acceptance or dependent release. Reviewer changed
only records/evidence; product, suite, PROGRESS and Git state remain untouched.

## 2026-09-13T19:07:44Z — queue scope gap and incomplete managed journal ownership

Claim162980 consumes return162975/M162973. The append-only review at
review-2026-09-13T19-07-44Z.md binds six changed hashes and queue.py baseline.
Earlier request-signature collision, exact integer, result/phase granularity,
duplicate-read and under-lock migration findings are superseded for their
specific corrected behavior, with the new review's remaining limits.

**Confirmed operational finding:** result.managed is absent from queue.py's
RESULT_CUSTODY_KINDS; recording one causes lease/entry history reads to refuse.
This is an implementation compatibility defect, not an acceptable restriction.
The exact approved source table excludes queue.py. SCOPE-AMENDMENT-162980.md
proposes adding only that kind with no new budget or test-approval gate. The
owner source decision must precede that edit; no workaround was applied.

**Confirmed P1:** managed_result_of and its replay witness do not reconstruct
and compare the persisted request/state to the committed journal. A different
valid stored harness or removal of every phase survives both read and exact
original replay; an unjournalled held state is also returned. This contradicts
the proposed queue delegation's premise that the result owner supplies the
signature proof. Complete the companion correction in approved reconciliation.py.
**Confirmed P1:** apply can name foreign preparation/content beside this result's
preparation. Cross-bind actual accounts. **Observed:** prepare-only creation
cannot later add apply without a collision; simultaneous account insertion is
not the accepted sequential phase lifecycle.

Preservation now covers a populated entry/live lease, but its alleged schema5
fixture retains a new result.managed journal after dropping its tables and has
no legacy result. Correct it to genuine populated legacy history. Writer tests
still use a directly inserted legacy row and a private claim helper; do not
describe them as actual prepare_result/record_managed_result contention. These
evidence corrections remain under standing M162289 authority.

Independent91 checks pass (54 contract,32 storage,5 research), including explicit
defect observations, not acceptance. One child0.31385364099696744s recorded in
review-ledger-162980.json; reviewer4.947672767979384/300s,
remaining295.0523272320206s. Author79 runs117.08701624104287/600s,
remaining482.9129837589571s. Qualified4.19.2 versus pinned4.26.0 remains.
No slice acceptance or dependent release. Preserve remaining placement/content/
grant scope, local reuse and W32577 ownership. Reviewer records/evidence only.


## 2026-09-13T23:02:05Z — M164369 approves the exact queue source amendment

Owner baton.slaw answered obligation163010 in M164369 at23:00:14Z:

> Approve the exact source addition in SCOPE-AMENDMENT-162980.md. Preserve required companion corrections, existing cumulative budgets and independent review.

Return164370 directs baton.feat to pin that decision and return the remaining
implementation scope to baton.impl, retaining review-2026-09-13T19-07-44Z.md.
Reviewer claim164376 consumed the complete new events/thread and pins the ruling
here and in PLAN, with IMPLEMENTATION-HANDOFF-164376.md as the current assignment.

**Confirmed authority:** SCOPE-AMENDMENT-162980.md, SHA256
b17b841f05e75bfc8cae25a76672917a2f3180f55406fcc7390ec4778bb9508c, now authorizes
only adding result.managed to RESULT_CUSTODY_KINDS in integration/queue.py.
Its prior proposed/pending wording and the original source table's exclusion of
this exact edit are explicitly superseded. No other queue edit, product path,
generic journal relaxation, budget extension or acceptance waiver is granted.
Fresh queue base18ced502ebcff18946c1c72914223166c995484ce2baccd6423bb3f7ca0b23a0
still matches, as do the six reviewed integration/storage/test/DEPLOYMENT bases.
The compatibility defect therefore remains present until implementation; scope
approval is not its correction or independent acceptance.

The19:07 review's companion requirements remain actionable: journal-bound managed
read/replay/state and complete phase set; actual preparation/apply parent/content
and sequential attachment; genuine populated legacy history and actual writer
contention evidence; corrected positive queue/public-reader tests; remaining
local placement/task/content/derived-candidate/live-grant contracts and docs.
M162617/M162634 local existing-input/output reuse and M162289 standing necessary
test-change authority remain. No repeated test-only approval is needed.

W32577 attempts/documents hashes still match its released candidate. M163260/
M163265 retain DEPLOYMENT with W161230 through the two required corrections,
followed by explicit fresh-hash handback; this approval does not imply those edits
or the handback have happened. M163260 also corrects the earlier pip inference:
repository venv pip exists, but that venv lacks jsonschema and system has4.19.2.
Required final4.26.0 remains; no installation authority is added here.

No verification child, product/test edit or PROGRESS/Git mutation in this pinning
claim. Author79 runs117.08701624104287/600s, remaining482.9129837589571s;
reviewer4.947672767979384/300s, remaining295.0523272320206s unchanged. Preserve
all guards, costs and exact candidate review. Pass to baton.impl, next baton.feat.
No slice/full-feature acceptance or W156162/W161234 release.


## 2026-09-13T23:19:08Z — exact-identity defects after journal-binding corrections

Reviewer claim164484 consumes return164480/M164477. The append-only
review-2026-09-13T23-19-08Z.md binds all eight candidate hashes and current
verification evidence. M164369's queue addition is implemented. The19:07 specific
valid-task substitution, deleted-phase, unjournalled held-state and foreign
preparation/content findings are superseded for their corrected cases. Separate
creation/attachment supports ordinary phase order and creation replay after growth.
This does not accept the entire owner or unfinished slice.

**Confirmed P2:** _managed_witness splits operation text at slash even though
identity accepts slash. Public creation of root/child succeeds; exact replay
looks up root and refuses. **Confirmed P2:** the reverse journal scan uses LIKE,
so root_ mistakes rootA/prepare for its own missing phase, and root mistakes
ROOT/prepare likewise. All three probes use public APIs and different valid
snapshot keys, without fixture corruption. Use exact signed identity/phase
ownership, preserving true-deletion detection; do not silently narrow the
existing identity grammar. Corrections fit approved reconciliation.py.

**Observed evidence gaps:** two-connection contention is still a completed first
write followed by a second write, with winner replay rather than loser replay.
Add deterministic public-writer overlap in both legacy/managed orders. The new
genuine legacy-result fixture is useful, but the older live-lease upgrade fixture
still retains managed acts after dropping their tables; fix its alleged schema5
history and stale queue-limitation comment, using public lease/entry readers.
M162289 already authorizes these necessary test changes without another gate.

Independent pinned Python3.13.7/jsonschema4.26.0 runs all100 contract/storage cases
successfully. First research child also confirms three identity defects but has
two failed reviewer hypotheses: non-durable invalid attachment and creation
collision are re-decided and do not exhibit the predicted refusal-replay bug.
Those hypotheses are explicitly withdrawn, not product findings. A second child
runs only five research cases with corrected controls; all pass, including the
three deliberately defect-observing assertions. Both original and corrected
scripts/logs/ledgers are retained, and both children charged.

Reviewer costs0.46393826699932106s plus0.2136735740059521s yield cumulative
5.625284608984657/300s, remaining294.37471539101534s, in
review-ledger-164484-2.json. Author fresh sum95 runs170.82799828205316/600s,
remaining429.17200171794684s. No allowance reset/transfer. Owner-provisioned repo
venv4.26.0 availability from W32577 is now independently used here; prior current
missing-dependency wording is superseded. Earlier4.19.2 evidence is not relabelled;
this pinned check covers these100 tests, not the unfinished slice.

Return through baton.bug, next baton.feat for exact corrections plus the already
approved placement/task/content/derived-candidate/live-grant remainder. The
handoff identifies no concrete blocker to completing that remainder. Preserve
M162617/M162634 local existing-input/output reuse, W32577 path ownership and the
explicit DEPLOYMENT fresh-hash handback. No slice acceptance, W156162/W161234
release, product/suite/PROGRESS/Git edit, install, runtime, image or provider
execution in this reviewer claim. Reviewer changes are dossier evidence only.


## 2026-09-13T23:21:56Z — forward reviewed corrections to implementation

Pass164512 returned the incomplete candidate through baton.bug. Canonical detail
shows that endpoint resolves to baton.codex/rview, so claim164513 immediately
consumes that readiness and forwards the completed independent review and bounded
corrections to baton.impl, next baton.feat. The earlier next-route wording is
superseded by this explicit implementation handoff. This is route resolution,
not a Baton defect or new implementation authority. No verification or candidate
change occurred; spending and review-2026-09-13T23-19-08Z.md remain unchanged.


## 2026-09-13T23:28:58Z — writer identity ambiguity and contention evidence remain

Claim164552 consumes return164545/M164544. All eight current candidate hashes
match the append-only review-2026-09-13T23-28-58Z.md. The specific earlier
root/child replay, LIKE wildcard/case conflation and invalid legacy live-lease
fixture findings are superseded for their corrected behaviors. The genuine
legacy upgrade now has public lease/entry/target readback as requested.

**Confirmed P2:** creation of root/prepare and preparation attachment to root
still derive the identical result.managed:root/prepare operation. Independent
public-API probes show collision in both orders at different snapshots; parsing
signed operands on read did not make the writers injective. **Confirmed P2:**
renaming a fixture creation operation and its row pointer while retaining the
original signature still passes managed_result_of; canonical identity is not
re-derived. Complete the previous review's unambiguous act distinction and
canonical identity proof in approved reconciliation.py, recording compatibility
handling and preserving the accepted identity domain and changed-operand refusal.

**Observed P2 evidence gap:** contending() manually takes BEGIN IMMEDIATE and
inserts the holder rows directly, with only record_managed_result on the waiting
side. No pair of actual legacy/managed public writers in both orders is driven.
Its started event is set before waiter execution and the holder-side row count
cannot prove waiter blocking or invisibility. The newest review specifies a
bounded deterministic public-writer/precommit/write-lock synchronization plan.
Necessary tests/helpers are already authorized by M162289.

Independent pinned3.13.7/4.26.0 verification:105 contract/storage cases plus3
explicit defect observations pass in one guarded child0.5140178479923634s.
Evidence is probe-164552.py, verify-164552.py, review-run-164552-1.log and
review-ledger-164552.json. Reviewer cumulative6.1393024569770205/300s, remaining
293.860697543023s. Author fresh101runs187.34456421206414/600s, remaining
412.65543578793586s. Author pinned step100 log says941 total tests,1 skipped
(940 passes), correcting the handoff count; step101192 passes is retained.
The dependency-pin condition is met for the tested current candidate, not the
unfinished slice or future changes. No reset/transfer or unnecessary repeated run.

M164544 identifies bounded working context rather than an external blocker.
That does not amend scope or budgets. After the concrete identity/evidence
corrections, continue directly into approved placement/task/content/derived-
candidate/live-grant scope with durable checkpoints if context compacts. Return
the coherent selected slice or a concrete operational/source-authority blocker.
Pass completed independent review to baton.impl, next baton.feat. Preserve local
input/output reuse, W32577 ownership and explicit DEPLOYMENT fresh-hash handback.
No slice acceptance/dependent release; no reviewer product/suite/PROGRESS/Git,
install/runtime/image/provider change. Reviewer dossier evidence only.


## 2026-09-13T23:37:46Z — identity fixes accepted; independent public-writer proof supplied

Claim164605 consumes return164601/M164596; all eight hashes match the append-only
review-2026-09-13T23-37-46Z.md. The23:28 creation/attachment collision and missing
canonical operation identity findings are superseded for the corrected candidate.
Both families now include result identity length; both reader pointers are
compared with writer-derived IDs. No new product defect found in this delta.
Compatibility is assessed as correction of the selected unreleased schema6 Work,
not an external deployment inventory or live migration. Earlier disposable
fixtures do contain earlier candidate spellings; do not claim none ever existed.

The submitted contention test still misstates its legacy writer: legacy(handle)
uses private _claim_result_key, INSERT and probe.legacy, not prepare_result.
Its begun event remains before waiting(mine). To make the exact correction
reviewable and implementation-ready, probe-164605.py supplies PublicWriterOverlap
using real ResultCase, actual prepare_result and record_managed_result on distinct
connections in both orders. It pauses the holder inside its transaction and
observes the waiter BEGIN IMMEDIATE through its SQLite trace before release;
asserted event ordering, one shared result and real winner public read/replay
all pass. This proves transaction-boundary ordering, not elapsed time blocked
inside SQLite after the callback. Adapt the research into the owning product
test path under standing M162289; no further permission or substitute writer.

Pinned Python3.13.7/jsonschema4.26.0:111 checks pass (54 contract,55 storage,2
positive public-writer proofs). One child0.5641020019975258s in
review-ledger-164605.json gives reviewer6.703404458974546/300s, remaining
293.29659554102545s. Author fresh107runs203.23825739108725/600s, remaining
396.76174260891275s. Step107945 total with1 skipped is retained. No reset or
transfer; no repeat of unchanged broad checks. Research scripts/log and ledger
are durable under this dossier.

Next implementation claim starts condition5 placement and its tests, actual
execution/task/content/authorized-derived-candidate/live-grant bindings and docs,
alongside the small retained contention-test correction. Existing accepted scope
and budgets suffice; the unstarted remainder is not an approval gate. Preserve
local input/output reuse, admitted-old-revision CAS, stopped-execution proof,
durable checkpoints through compaction and W32577 shared-file/DEPLOYMENT handback.
Pass to baton.impl, next baton.feat. No full slice acceptance or dependent release.
Reviewer changed dossier evidence only, no product/suite/PROGRESS/workspace Git
state, install/image/runtime/provider operation.


## 2026-09-13T23:50:10Z — placement misses trusted proofs and mutation/replay cutpoints

Claim164677 consumes return164674/M164672 and binds ten candidate hashes in
review-2026-09-13T23-50-10Z.md. The remaining synthetic contention fixture finding
is superseded: actual public writers now run in both orders with qualified
transaction-boundary evidence. Prior identity/journal corrections stay accepted.
Condition5 has implementation but is not accepted by this review.

**Confirmed P1:** the required locally composed execution-owner capability from
DESIGN-RESPONSE-161397.md Gate4 is absent, as is authorized-candidate proof from
the accepted v2 target-owner contract. Current placement checks only destroyed
axis/assignment, not exact start/runtime/frozen collected reference. An independent
positive fixture publishes a preparing result with runtime_id None, no derived
proposal and no evidence. This is missing publication authority/exclusion, not
merely the separate outstanding admission check.

**Confirmed P1:** public refuse_entry invoked during materialization releases
the grant, yet profile.advance still moves the target before settlement refuses.
The last pre-mutation grant check must follow intervening materialization/content
validation. **Confirmed P1:** settlement={} is rejected only after target advance;
own the complete immutable request before side effects. **Confirmed P2:** exact
successful publication retry treats its own imported revision as foreign target
movement. Compose bound replay/partial-effect recovery; equality with candidate
alone cannot prove an earlier owned swap. Preserve admitted-old-revision CAS and
separate completion validation. The newest review names exact deterministic
regressions and scope boundaries; no added live verification is needed.

Pinned Python3.13.7/jsonschema4.26.0:17 placement and56 storage tests pass plus4
explicit defect-observing probes,77 total. Evidence probe-164677.py,
verify-164677.py, review-run-164677-1.log and review-ledger-164677.json. One guarded
child0.964576437996584s gives reviewer7.66798089697113/300s, remaining
292.33201910302887s. Fresh author114runs220.11321631306782/600s, remaining
379.8867836869322s. Author963 total/1 skipped is retained, not complete acceptance.
No reset/transfer; permissive research assertions are findings, not desired tests.

Return to baton.impl, next baton.feat for placement corrections plus the remaining
apply authorized-derived-candidate/current-grant admission work. Correct the
new placement tests and docs under M162289, preserve actual public-writer evidence,
M162617/M162634 local input/output reuse and W32577 shared-file/DEPLOYMENT handback.
Existing accepted source scope applies; report exact missing source authority
before adding another path or schema change. No full slice acceptance/dependent
release. Reviewer dossier research/findings/plan only, no product/suite/PROGRESS,
workspace Git state, installation, runtime, image or provider operation.

## 2026-09-14T00:04:25Z — placement entry binding and durable replay remain open

Claim164765 reviews return164759/M164754, all ten candidate hashes matched.
Read review-2026-09-14T00-04-25Z.md and probe-164765.py. **Confirmed:** the missing
capabilities now exist and the positive fixture starts/attaches a runtime; the
materialization/grant ordering and malformed-settlement-before-effects defects
are resolved. This explicitly supersedes their previous outstanding descriptions,
within the exact proof limitations in the new review. Older custody/journal and
public-writer fixes remain accepted.

**Confirmed P1:** publication can settle an unrelated entry using its valid lease;
authorization is not bound to selected entry eligibility. **Confirmed P1:** a foreign
move to the same collected revision is called an owned resumed swap; completed
retry accepts a changed lease/fence and returns a later unrelated current revision
as its imported result. Digest-to-revision identity does not prove mutation ownership.
These four independent probes reproduce remaining accepted-contract violations.
Exact durable publication operands/effect/outcome and candidate-entry relations
remain necessary; neither a live grant alone nor equal content supplies them.

Source inspection also confirms that the named start is checked only for committed
runtime.start kind, separately from attempt/runtime. A real foreign-start mismatch
remains an inferred risk to revalidate/test, not a dynamic reproduction this claim.
Preserve exact owner semantics; identify a concrete scope amendment before any
extra path/schema change. Current scope, M162289 test authority and local input/output
reuse apply. Correct DEPLOYMENT's overstated replay/resume claims; admission gate
work and W32577 fresh-hash handback remain open. Pass review to baton.impl nextfeat;
no full acceptance or dependent release.

Pinned37 supplied tests plus4 permissive research observations pass,41 total.
One guarded child1.114733326001442s; review-ledger-164765.json records cumulative
8.782714222972572/300s, remaining291.2172857770274s. Author120 runs
237.95785192206677/600s, remaining362.04214807793323s. Author983 total/1 skipped is
982 passes plus1 skip, qualified by this review. No reset, transfer, live runtime/
provider, installation, product/suite/PROGRESS or repository Git-state change.

## 2026-09-14T00:17:42Z — publication record still needs effect ownership and journal proof

Claim164852 consumes return164844/M164838. All ten candidate hashes match;
review-2026-09-14T00-17-42Z.md records exact findings, acceptance and provenance.
The previous source-submission/entry mismatch, unrelated-attempt start-kind check,
completed-retry changed grant/current-revision bugs and no-intent foreign move
are resolved within the new review's limits. This explicitly supersedes those
specific outstanding descriptions; earlier accepted work remains accepted.

**Confirmed P1:** intent-only interruption followed by a foreign move to the same
revision is falsely resumed as an owned swap. A recorded swapped effect followed
by a foreign move back to admitted base causes a second advance and published
answer. Intent/content equality is not target-effect ownership. **Confirmed P1:**
publication_of accepts a state-only forged settled record and a missing creating
journal act. The forged state lets placement replay completion while target is
base and queue entry leased. Add exact intent/effect journal proof and target-owner
recovery evidence; retain uncertainty when an effect cannot be distinguished.

The predicted post-queue-settlement recovery failure is explicitly withdrawn:
the initial research assertion failed because retry succeeded. A separate positive
check proves recovery to settled without another swap. Original research failure
and spending remain retained; it is not a product finding.

Pinned101 supplied tests pass (45 placement/56 storage); first child106 total also
contains4 confirmed permissive defect observations and1 failed reviewer hypothesis.
Second child1 positive recovery test passes. Evidence probe/verify/review-run-164852
and -164852-2; reviewer cumulative10.861695301973668/300s, remaining289.13830469802633s
in review-ledger-164852-2.json. Author129 runs275.9689216490515/600s,
remaining324.0310783509485s. No reset/transfer;991 total/1 skipped is990 passes+1 skip.

Return review to baton.impl nextfeat for these corrections plus outstanding apply
candidate/grant admission. Existing scope and M162289 test authority apply; identify
exact extra target-owner path authority if required before editing beyond scope.
Correct DEPLOYMENT and preserve W32577 handback/local input-output reuse. No slice
acceptance or dependent release. Reviewer dossier only, no product/test/PROGRESS,
repository Git-state, runtime/image/provider/install mutation.

## 2026-09-14T00:26:30Z — intended-state base return and concurrent publication read

Claim164912 reviews return164905/M164904; all ten candidate hashes match.
Review-2026-09-14T00-26-30Z.md accepts correction of the previous four exact probes
and explicitly supersedes their outstanding descriptions. Journal checks now detect
static missing/forged acts and a recorded swap is not repeated after later movement.
The known settlement-window hypothesis remains withdrawn.

**Confirmed P1:** an actual swap interrupted before its marker leaves intended;
a foreign move back to admitted base causes retry to advance again. Current base
equality is not positive evidence that the existing operation never ran.
**Confirmed P2:** publication_of lacks the existing store.snapshot boundary; a
second connection committing swapped between row/journal reads causes a false
integrity refusal. Use a coherent owner snapshot and operation-bound target evidence;
retain uncertainty when no proof distinguishes delayed/applied/not-applied effects.

The review supplies a bounded proposed target execution/recovery capability contract
within the already-approved placement interface, explicitly distinguishing fake
slice1 boundary evidence from later real target-producer delivery. An unspecified
new tools module is not an exact scope proposal. Real GitIntegrationProfile receipt
support, if needed now, requires exact path/API/runner/atomicity/test justification;
no extra path authority is inferred. Current conservative refusal/snapshot/interface
and apply admission work can proceed within scope. Pass to baton.impl nextfeat.

Pinned52 placement+56 storage cases plus2 explicit defect observations pass,110 total.
Child1.9656744770036312s; reviewer12.8273697789773/300s, remaining287.1726302210227s,
review-ledger-164912.json. Author134 runs296.82717431707715/600s,
remaining303.17282568292285s.998 total/1 skipped means997 passes+1 skip, qualified.
No reset/transfer, full acceptance/dependent release, product/test/PROGRESS/Git-state,
runtime/provider/image/install action. Preserve local input/output and W32577 handback.

## 2026-09-14T00:35:44Z — target recovery needs current-content and final-grant checks

Claim164968 consumes return164964/M164962; ten candidate hashes match.
Review-2026-09-14T00-35-44Z.md accepts the target-owner capability composition and
coherent publication snapshot correction. An independent two-connection regression
now reads one consistent old state and then the new state. The previous base-return
case no longer duplicates its apply. This explicitly supersedes those outstanding
findings within the new review's limits; prior acceptances remain.

**Confirmed P1:** recover(applied) settles an outstanding entry even after the
target moved back to base. Historical receipt proves past effect, not current
content. **Confirmed P1:** recover(not-applied) may release the live lease through
public refuse_entry; placement still invokes apply, moving the target before
settlement refuses. Refresh current-target completion proof after recovery and
put the final live-grant check after intervening recovery/intent work immediately
before a new apply. Preserve unknown effects, exact operands and no repeated swap.

Pinned56 placement+56 storage pass plus1 independent positive snapshot and2
permissive defect observations,115 total. Child2.0658016620000126s; reviewer
14.893171440977312/300s remaining285.1068285590227s, review-ledger-164968.json.
Author139 rows318.6362541431008/600s remaining281.3637458568992s.1002 total/1 skip
means1001 passes+1 skip. No reset/transfer. Fake target receipts remain simulated
contract evidence, not production atomic Git receipts.

Return to baton.impl nextfeat for these within-scope recovery checks and outstanding
apply authorized-candidate/live-grant admission. M162289 test authority applies;
correct docs and preserve local input/output reuse and W32577 DEPLOYMENT handback.
No slice acceptance/dependent release, product/test/PROGRESS/Git-state change or
live runtime/provider/image/install operation by reviewer.

## 2026-09-14T00:41:55Z — shared apply-path final checks remain

Claim165011 reviews return165007/M165006; ten candidate hashes match.
Review-2026-09-14T00-41-55Z.md accepts the specific prior release-during-recovery
and recovered-receipt target-drift corrections, superseding their outstanding
wording. Prior contract/snapshot/journal/entry/replay acceptances remain qualified.

**Confirmed P1:** final configured revision read occurs AFTER live_grant; public
refuse_entry during that read ends the lease yet target_owner.apply still advances.
Read/validate target before final grant check, then invoke apply. **Confirmed P1:**
fresh apply returns a truthful historical receipt after a foreign move back to base;
placement settles integrated over base. Share the current-target completion check
across fresh/recovered/recorded-swapped outstanding paths, retaining effect evidence
and refusing drift without another apply. Exact completed replay remains historical.

Pinned60 supplied placement+2 explicit defect observations pass,62 total;
child1.8155298830097308s. Reviewer16.708701323987043/300s remaining283.29129867601296s,
review-ledger-165011.json. Author143 runs338.96681689910474/600s remaining261.03318310089526s.
1006 total/1skip means1005 passes+1skip. No reset/transfer or unchanged storage rerun.

Return to baton.impl nextfeat to complete these shared checks AND the still-open
apply authorized-candidate/live-grant admission. Current scope/M162289 suffice;
no later target producer dependency or new test-only gate. Preserve local input/output,
W32577 handback, existing evidence, no full slice acceptance/dependent release.
Reviewer dossier only; no product/test/PROGRESS/Git-state/runtime/provider/install action.

## 2026-09-14T00:55:37Z — publication corrected; admission loses grant and candidate binding

Claim165071 reviews return165068/M165066; all12 current candidate inventory hashes
match. Review-2026-09-14T00-55-37Z.md accepts the two shared publication checks,
explicitly superseding their prior outstanding wording. Independent desired
regressions pass. Earlier acceptances remain within recorded limits.

**Confirmed P1:** authorization.authorized may release the actual coordinator lease
before returning approval, yet new admission still commits admitted. Move the final
live-grant observation after intervening authorization work. **Confirmed P1:** the
helper's approved candidate is discarded; admission's signature carries only grant,
not authorization/proposal/result/digest. Changed owner candidate retries replay
without owner consultation, and no durable candidate binding exists. Bind actual
approved identity/content in the admission act with exact/colliding retry semantics,
preserving historical exact replay. Correct contradictory DEPLOYMENT admission
claims/old limitation and duplicated heading. No later target producer prerequisite.

Pinned63 placement+70 capacity,2 positive publication regressions and2 explicit
admission defect observations pass,137 total. Reviewer19.324475530993368/300s,
remaining280.67552446900663s, review-ledger-165071.json. Author153 runs
365.55885749509616/600s, remaining234.44114250490384s.1018 total/1skip is1017
passes+1skip. No reset/transfer. Return to baton.impl nextfeat within existing
scope/M162289; preserve local input/output reuse and W32577 DEPLOYMENT handback.
No slice acceptance/dependent release or product/test/PROGRESS/Git/runtime/provider/
installation action by reviewer.

## 2026-09-14T01:03:32Z — admission corrections accepted; content replay binding remains

Claim165141 reviews return165138/M165136; all13 candidate inventory hashes match.
Review-2026-09-14T01-03-32Z.md accepts final grant ordering, retained/signed candidate,
closed grant validation and exact historical replay after lease release. This
explicitly supersedes the previous two outstanding admission findings in their
demonstrated cases.

**Confirmed P2:** collected content is omitted from the admission signature.
An explicit disposable preparation-content fault before retry causes the owner to
approve the new digest while admission replays the old content. The new transaction
comparison is bypassed on replay. This is qualified persisted-state fault evidence,
not an observed legal public mutation of a completed preparation. Bind validated
content in immutable identity or equivalent checked replay; preserve unchanged
historical replay. DEPLOYMENT's duplicated heading also remains despite the handoff.

Pinned75 capacity+47 Job Manager store+2 positive regressions+1 permissive fault
observation pass,125 total. Reviewer20.38877626798785/300s remaining279.61122373201215s,
review-ledger-165141.json. Author158 rows384.7591965211177/600s remaining215.2408034788823s.
1023 total/1skip means1022 passes+1skip; no reset/transfer. Pass review to baton.impl
nextfeat for bounded signature/docs correction under existing scope/M162289.
Preserve local input/output reuse and W32577 DEPLOYMENT handback. Earlier acceptances
remain qualified; no full slice acceptance/dependent release or product/test/PROGRESS/
Git/runtime/provider/install action by reviewer.

## 2026-09-14T01:09:21Z — slice1 accepted; later execution remains

Claim165182 reviews return165175/M165172. Review-2026-09-14T01-09-21Z.md accepts
the remaining content-signature and heading corrections, explicitly superseding
review-2026-09-14T01-03-32Z.md's outstanding wording. Independent changed-content
collision, unchanged historical replay after lease release and release-during-
authorization all pass. The cumulative exact-candidate evidence now satisfies the
five selected slice1 conditions, as enumerated in the new review.

**Confirmed:** slice1 contracts/composition are accepted. Actual managed preparation/
apply delivery and production target effect-and-receipt owner remain later selected
work. W161230 stays open and W156162/W161234 remain blocked. Recommend next selected
slice2 then3 from adopted v2, narrowed by M162617/M162634 local existing input/output
reuse. Select current exact scope and budgets before later execution; no automatic
authority or transfer is inferred.

All13 current candidate hashes match; slice1-candidate-165182.json binds21 relevant
current paths, SHA2567561139b858114a4ca619e4d1ad86d15a19f0148bc8e9fac9b0fc0a3245237d2.
Pinned77 capacity+3 independent desired regressions pass,80 total. Reviewer cumulative
21.403079563991923/300s remaining278.5969204360081s; author160 runs401.4989696021221/600s
remaining198.5010303978779s. Author1025 total/1skip means1024 passes+1skip, with
existing fixture ResourceWarnings qualified. No reset/transfer or blanket suite claim.

M163260/M163265 DEPLOYMENT ownership handback is now effective to W32577 at
971fba687461bf4cc0c8899b5f692d086cad3af8cd794573b2004cee1f0a7f94; preserve reviewed
sections and rebind later changes. No W32577 runtime/budget authority is added.
Pass concrete slice1 acceptance to baton.decide for the next selection. Reviewer
dossier only; no product/test/PROGRESS/Git/runtime/provider/image/install action.

## 2026-09-14T02:56:48Z — owner directs slice2 preparation; concrete packet ready

**Confirmed owner scope, reroute165721:** prepare slice2 local managed preparation
delivery through the ordinary worker lifecycle, mandatorily reusing existing worker
input/output; preserve accepted slice1; defer derived apply/failure settlement to
slice3; return current exact scope, ownership, acceptance and proposed allowance for
selection. Deterministic providers by default, no remote farm. This supersedes the
prior next-action wording that merely awaited a choice of which slice to prepare.
It does not authorize implementation or extend verification budgets.

Claim165724 consumed current detail, standalone claim, all new work-events and the
complete empty-after165172 thread page, then read the dossier/current source.
All21 slice1 bound paths remain byte-identical. The proposal is
SLICE2-SCOPE-165724.md SHA256
4c18e791a29516b92d5afaba93c2042f5adaefa60bd57b7c54b13a04acba4fa0.
SLICE2-BASELINE-165724.json binds30 edited/new/reused/protected paths, SHA256
be532163850f476643abb48176e12db39c875871019b86206d1e82e149a30a52.

**Observed/current:** Integration.reconciled still runs host preparation/causal
observation; ordinary worker_operations already supplies claim/launch/exchange/
freeze/intake/cleanup. Pool admission reserves before calling the selected worker.
The Authority one-principal claim slot and the accepted same-actor phase rule mean
preparation must precede the parent offer/claim. Proposed wrapper drives preparation
under the reserved allocation and returns a nondurable parent deferral, which
manager._delegate already supports. It must never return a fake successful parent
receipt or allocate a second worker. This is a bounded composition, not a generic
scheduler/Authority change.

**Proposed selected correction:** successful concrete preparation adoption/ending
must prove accepted normal intake and retained artifact identities, not only
frozen_output_of as the current abstract capacity helper does. The packet schedules
that source/fixture change explicitly and preserves slice1 report/exclusion meaning.

The packet names6 existing+3 new source paths,6 existing+2 new test paths, precise
semantic request/report/candidate bindings, pre-claim versus actual assignment/input
identity, real worker code behind the simulated normal engine boundary, causal
prefix/suffix/defaults, portable custody, no-host-execution trap and restart cutpoints.
Existing generic lifecycle/transport/Authority/Git profile code is reuse-only.
A nonexistent serving.py discovery probe was corrected to the actual manager.py;
no required unreadable file remains and no missing-capability claim rests on it.

**Proposed allowance:** author cumulative600→1200s; reviewer stays300s.
Current author160 runs401.4989696021221s, reviewer21.403079563991923s unchanged.
If selected, available798.5010303978779s/278.5969204360081s. No reset/transfer,
automatic extension, image build/pull, actual Docker or live provider authority.
Planning ran no verification child. DEPLOYMENT remains W32577-owned under M165203
at971fba687461bf4cc0c8899b5f692d086cad3af8cd794573b2004cee1f0a7f94; slice2 drafts
stay in this dossier until serial fresh-hash handback. No product/test/PROGRESS/
Git/runtime/provider/install mutation. Pass concrete packet to baton.decide for
selection, next baton.feat to pin any ruling and hand selected work to baton.impl.

## 2026-09-14 — owner selects slice2 implementation, claim165902 handoff

**Confirmed owner reroute165830 at03:03:23Z:** select
SLICE2-SCOPE-165724.md SHA256
4c18e791a29516b92d5afaba93c2042f5adaefa60bd57b7c54b13a04acba4fa0,
its bounded source/test scope and cumulative author1200s/reviewer300s.
Preserve all prior spending, deterministic providers, existing worker I/O reuse
and W32577 documentation ownership. Derived apply stays slice3; broad hardening
stays v13. Pin the selection and hand implementation to baton.impl.

This explicitly supersedes the preceding preparation entry's unselected
implementation/cap600 state. The selected packet stays byte-identical historical
proposal text; this dated ruling supplies its implementation authority.
SLICE2-BASELINE-165724.json remains SHA256
be532163850f476643abb48176e12db39c875871019b86206d1e82e149a30a52.
After standalone claim165902 and all new journal/thread reads, static custody
checking found all30 baseline entries and all21 accepted slice1 entries match
their expected bytes, types, modes and new-file absence. No product drift or
new missing path/API is observed by this handoff.

Implementer owns the selected nine source/eight test paths after claiming;
necessary test changes remain under standing M162289. Reuse-only generic
boundaries stay reuse-only. Preserve actual child Work/claim and normal
worker lifecycle, capacity before start, accepted intake custody, actual worker
execution behind the deterministic engine seam, causal identities/limits and
restart/no-host-execution acceptance. Parent apply remains planned and root
held at slice2 finish; no synthetic judgment, target application or downstream
release. No actual engine/model/image build/pull or package installation grant.

Cumulative author160 runs401.4989696021221/1200s leaves798.5010303978779s.
Reviewer21.403079563991923/300s leaves278.5969204360081s. Claim165902 adds no
verification subprocess or test run; metadata reading/hashing only. Persist
guard operands before every later verification child and charge all failures
and nested worker/harness execution; no reset, transfer or automatic extension.

DEPLOYMENT.md remains W32577-owned at the revalidated971fba687461bf4cc0c8899b5f692d086cad3af8cd794573b2004cee1f0a7f94.
Prepare DEPLOYMENT-SLICE2-DRAFT.md here and coordinate a serial fresh-hash
handback for any eventual main-file edit. No change to its runtime allowance.
W165782 classification is separate planning and adds no requirement or file
owner to this packet. Pass to baton.impl, next baton.feat for independent
review; PROGRESS remains the implementation author's account.

## 2026-09-14T03:25:26Z — partial custody feedback; complete the selected slice

Claim165948 reviewed author return165945/M165941 and current two-path change.
review-2026-09-14T03-25-26Z.md records no defect established in the bounded
accepted-intake requirement, with two independent identity/continuation checks
passing. candidate-165948.json binds the two paths; remaining baseline and
W32577-owned DEPLOYMENT are unchanged. Fixture custody/session providers are
simulated; actual worker artifact materialization and orchestration remain
required and are not proved by these fixtures.

The author explicitly returned early for feedback with most selected scope
unstarted and no missing capability or exhausted budget. Slice2 remains
incomplete, and no new approval gate is created. Return to baton.impl to
complete owner165830's coherent selected scope, preserving source ownership,
normal I/O reuse and later slice3 boundary. A genuine blocker must identify
exact evidence, missing boundary and cumulative costs; early feedback alone
does not justify treating authorized remainder as blocked.

Author166 runs421.23122635213076/1200s remaining778.7687736478692s.
Reviewer21.616769015985483/300s remaining278.3832309840145s, including the
0.2136894519935595s child in review-ledger-165948.json. Historical failures
remain charged; author976-pass retained log includes existing fixture warnings.
No broad/live-engine/provider execution or source/test/PROGRESS/Git mutation
by reviewer. PLAN now records the actionable complete-slice continuation.

## 2026-09-14T03:33:30Z — second unblocked partial return; completion still required

Claim166007 consumed return166003/M165997. The author added request/intent
helpers and registration binding, explicitly reported no blocker, and again
returned with the real producer/worker/consumer lifecycle unimplemented.
review-2026-09-14T03-33-30Z.md records the repeated early-handoff issue and
returns the already authorized coherent scope for completion. No new
intermediate gate or technical acceptance is created.

candidate-166007.json binds four changed baseline files and five planned files
still absent; other baseline files match. Final producer composition must
resolve the new request's input_digest without a circular enclosing-manifest
identity, as already required by the selected pre-claim/post-claim distinction.
This is an integration constraint within existing source authority, not an
observed failure of a producer that has not yet been implemented.

No verification child in this assessment. Author171 runs439.72462390415603/
1200s remaining760.275376095844s; reviewer21.616769015985483/300s remaining
278.3832309840145s unchanged. Preserve author999-pass evidence and fixture
warnings, all prior failures and uncorrected historical costs. No source/test/
PROGRESS/Git/runtime/provider action by reviewer. Complete the selected slice
or report a genuine exact blocker, including an actual runner limit if one
exists; no such external limit is inferred from these handoffs.

## 2026-09-14T03:56:17Z — worker defects and out-of-scope verification observed

Claim166129 consumed return166123/M166121. The new worker/test pair is
preserved in candidate-166129.json with four earlier slice2 paths. Independent
probe166129 confirms three failures: manager-rejected incomplete request
accepted by worker; symlink silently omitted from measured content; timed-out
base incorrectly included in not-run suffix. Full details and remaining
harness/content/limits/drain requirements are in
review-2026-09-14T03-56-17Z.md. Complete selected scope remains required.

Operational finding before any workaround: despite selected no-broad-suite/
no-engine scope, author183–185 used whole-suite/manager discovery; retained185
log reached a real-engine credential test returning15 resource names and a
deadline gate refusal for bypassing its required supervisor. The handoff's
no-engine/no-broad assertion is contradicted. No current resource existence or
ownership is inferred; no reviewer resource action performed.

Runs186/187 compare only nine failures in116 tests, not all35 failures plus
one error in step185. The blanket pre-existing attribution is unsupported.
Charges183=120s and184=110s were added after tool termination, without log
members and without proven full process-tree timing/reaping. Preserve them
and mark the uncertainty; do not treat nominal bounds as precise measurement.
Author ledger187 totals848.2976545901183/1200s, ledger remainder351.7023454098817s
subject to that reconciliation. Reviewer21.830531410982076/300s, remainder
278.1694685890179s, includes one0.21376239499659277s deterministic child.

Report operational findings asynchronously to ops; return code corrections
and coherent completion to impl. Before further verification require accurate
or defensibly conservative cumulative/termination evidence, without resetting
costs or running another broad/detached discovery. Static implementation is
authorized. No new approval gate for the already selected product/test paths,
no main DEPLOYMENT edit and no later-slice expansion are introduced.

## 2026-09-14T04:13:31Z — residual contracts and unproven accounting bounds

Owner M166178 requires timing/termination/resource reconciliation before more
verification, preserves all charges, and allows only justified conservative
bounds. Static corrections remain authorized; any operational inspection is
read-only and identifies exact owned resources. No blanket cleanup, engine
rerun or budget reset. This pins that ruling before further implementation.

Claim166235 reviewed return166232/M166231. The author withdraws the earlier
unsupported all-failures-pre-existing and no-engine/no-broad claims. New
review-2026-09-14T04-13-31Z.md confirms missing-field, interior-symlink and
failed-phase corrections, but independently reproduces semantic limits
accepted only by the worker and symlink-root reads by request/measurement.
Six tests: three pass, three fail with five assertion failures. Candidate
and exact deterministic evidence are recorded under claim166235.

The author's320s file-size-scaled estimate for183 and reuse of185's measured
154.784538s as a bound for184 do not prove upper limits or process-tree
termination. This explicitly rejects the new M166231/PROGRESS assertion of
reconciled available allowance; historical charges and appended deltas remain.
Author197 ledger entries sum1106.721556888122/1200s; remainder93.278443111878s
is arithmetic only, subject to unresolved accounting. No new budget selected.
Reviewer22.04422853698634/300s, remaining277.95577146301366s. Subsequent
191–197 costs remain charged; their guard prerequisite is not accepted.

Return incomplete Work through baton.bug and notify ops for retained lifecycle
evidence or explicit unresolved owner disposition. Static editing remains
authorized; author verification cannot proceed on invented duration bounds.
No acceptance of slice2, release of its dependents, main DEPLOYMENT change,
product/test/PROGRESS/Git mutation by reviewer, or live runtime operation.

### Bug-route disposition, claim166263

Pass166261 returned incomplete Work through baton.bug, which resolves to the
same reviewer. Claimed its actionable episode166263 and consumed new events/
thread. No additional verification or product changes. Forward the actual
accounting/termination blocker to baton.ops, next baton.feat, for evidence or
explicit owner disposition under M166178/M166259; do not leave a self-routed
readiness loop. All scope, candidate and cumulative costs above remain.

## 2026-09-14T04:18:45Z — owner separates historical uncertainty and future allowance

**Confirmed owner M166281, return166282; pinned by claim166284.** Accept an
explicitly unresolved historical accounting disposition for runs183–185.
Preserve all original charges and provisional estimates without calling them
exact bounds. This explicitly SUPERSEDES M166178 and the prior04:13:31Z
entry/review/PLAN requirement to reconstruct historical timing before future
focused verification. The findings about uncertain elapsed time, missing
termination evidence and the scope violation remain historical facts; no
retroactive authorization or resource-exclusion proof is supplied.

Authorize an ADDITIONAL prospective1200s author allowance, separately measured
from the next verification child. Historical spending remains1106.721556888122s
in197 ledger entries, including provisional estimates; the old arithmetic
remainder93.278443111878s is not added to the new allowance. Existing reviewer
cap300s and cumulative22.04422853698634s remain, leaving277.95577146301366s.
Future author spending has its own ledger segment bound to M166281, with
0s spent/1200s available before the next child. This is an explicit additional
owner grant, not deletion, reset, transfer or reinterpretation of prior costs.

Track outstanding resource/termination uncertainty as separate operational
Work, with read-only exact-owned-resource assessment. Do not gate selected
slice2 implementation or focused verification on that historical assessment.
No broad discovery, actual Docker/model execution, blanket cleanup, image
operation or acceptance waiver. Continue selected slice2 corrections and
completion with guarded focused deterministic tests. Product/test scope,
mandatory existing worker I/O reuse, DEPLOYMENT ownership and slice3 boundary
remain unchanged.

Current six-path candidate166235 hashes revalidate without drift. No reviewer
verification child in this ruling/coordination turn. Freeze the unchanged
historical ledger in historical-ledger-at-166281.json and record exact digest
in PROSPECTIVE-ALLOWANCE-166281.json. Author retains ownership of PROGRESS and
future execution ledger; reviewer supplies authority and handoff records only.

Separately accountable operational Work W166292 was created directly at
baton.ops, bound to baton:work/records/2026/09/finding-managed-preparation-historical-runtime-uncertainty.
It has no dependency/containment gate on W161230 and no verification allowance.
FINDING/PLAN there retain exact source evidence and read-only assessment scope.

## 2026-09-14T04:24:23Z — cumulative test time is not a development gate

Slawomir questioned the time/focus spent reconstructing test-duration estimates
and agreed to remove cumulative stopwatch budgets as approval gates for ordinary
focused verification in this development campaign. He then clarified that he had
already sent the previous response and requested corrective text. M166281 and
the answered obligation166259 remain historical records; this is a superseding
follow-up ruling, not an attempt to answer the same obligation twice.

**Superseded:** M166281's prospective1200s ceiling and older cumulative author/
reviewer caps, remaining-bank admission requirements and historical-duration
reconstruction prerequisites for ordinary focused deterministic iterations.
Do not return solely to replenish cumulative seconds, prove a guessed past
upper bound or request approval for another ordinary in-scope test iteration.
Planning estimates are approximate, not acceptance evidence or approval gates.

**Retained:** sensible per-run limits appropriate to each Job/test, process
termination/cleanup, selected product and verification scope, pinned dependencies,
fake/replay default, actual results and independent review. Preserve every prior
charge, estimate and failed run; label unknown durations honestly rather than
resetting or inventing them. No permission is granted for broad discovery,
actual Docker or live models excluded by slice2, or a new stress campaign.
Materially different execution needs explicit selection. Existing single-run
supervisor limits and product timeout semantics are not changed by this policy.

W166292 continues to own the separate resource/termination uncertainty. Removing
the timing gate does not prove process exclusion, authorize cleanup, excuse the
scope deviation or accept the remaining code defects. Continue the selected
slice2 implementation and focused deterministic verification under the simplified
policy. AGENTS.md carries this campaign-wide developer policy; current PLAN
reflects the supersession while all older history and ledgers remain intact.

## 2026-09-14T04:29:05Z — owner convergence checkpoint

Slawomir states that W161230 has taken too long: if it does not close in the
next few turns, it is time to redesign. Record this as a delivery checkpoint,
not another time-accounting limit. No exact numeric turn count was specified.

Continue the selected implementation and independent review. Subsequent handoffs
should make complete execution behavior, remaining closure requirements and
concrete blockers explicit. Accepted contracts or individual helper corrections
do not establish delivery of managed integration. If the next few implementation/
review turns do not converge to closure, stop extending the correction loop and
return a concise design/scope assessment for the owner to select a simpler path.
Preserve useful accepted work and evidence; do not silently waive correctness,
expand scope or treat this checkpoint as authorization for unselected slices.

At this checkpoint slice1 is accepted, slice2 remains incomplete and later
apply/target-effect delivery is still required. Thus another partial slice2
acceptance alone would not satisfy the owner's closure objective. This ruling
supersedes any assumption that repeated partial returns may continue indefinitely.

## 2026-09-14T04:33:24Z — leader reaping is not group ending; complete the lifecycle

Claim166368 reviewed return166366 and M166363 addendum. Seven independent
local-file/mock checks: five pass, two fail. Root no-follow, missing identity
and phase-suffix corrections pass. Unknown generation still disagrees. New
_ended checks child.poll rather than group exclusion; a vanished leader yields
a normal timeout with no group signal or exclusion proof in the independent
mock reproduction. The claimed whole-process-tree completion remains open.
See review-2026-09-14T04-33-24Z.md and candidate-166368.json.

Apply owner M166331 and the already pinned04:24:23Z policy now: cumulative
stopwatch caps are superseded as development gates. Historical and prospective
costs remain qualified records; no replenishment or old-seconds reconstruction.
Per-run timeouts/cleanup and selected focused deterministic scope remain.
Prospective13 entries151.39806862197582s include FIFO tool-kill/bare-run
estimates; route actual new termination uncertainty to W166292 separately.
Reviewer recorded22.257900130985945s including one0.21367159399960656s child.

M166352/04:29:05Z convergence checkpoint applies. Another partial helper return
has not delivered the selected ordinary managed preparation lifecycle. No
preliminary approval before building the already authorized producer is needed.
Return the complete selected composition with exact full-closure remainder,
or a concrete design/scope blocker and simpler proposal for owner selection
if convergence cannot be achieved. Preserve accepted slice1, W32577-owned
DEPLOYMENT, and unselected slice3 apply/final-settlement boundary. No waiver,
source/test/PROGRESS/Git or runtime-resource mutation by reviewer.

## 2026-09-14T04:45:47Z — invoke owner convergence checkpoint

Claim166444 consumed return166437/M166436. Another helper-only return leaves
all ordinary managed lifecycle wiring absent; the author explicitly reports a
recurring working-context limitation. This does not prove a protocol/API
incompatibility. Under M166352, return a concrete design/scope assessment now
instead of another unchanged correction-loop handoff.

review-2026-09-14T04-45-47Z.md records improved group exclusion and a remaining
strict-types defect: float generation/seconds/default_seconds compare equal to
owned integers and pass worker read_request while manager rejects them.
Two independent tests: group-observation case passes, type test fails in three
subcases. Candidate166444 binds exact current six-path bytes. The launch fixture
is not actual validated launch evidence; real entry/producer/adoption is absent.

Proposed DESIGN-RECONSIDERATION-166444.md keeps existing ordinary architecture
and selected paths but orders one executable preparation-to-collection path,
then complete refusal/replay acceptance, with durable resumption across context
limits. Checkpoints are not partial Work acceptance. No later slice3 grant,
dependent release, discarded evidence or new protocol subsystem is implied.
Pass to baton.decide for owner selection, next baton.feat to pin the decision.
This disposition supersedes the immediately preceding PLAN next-impl action;
product requirements and unaccepted corrections remain intact.

Historical costs preserved:1106.721556888122s qualified, prospective26 entries
237.7129594819882s qualified; reviewer22.471559100995364s after one
0.21365897000941914s child. M166331 removes cumulative gates. No reviewer
source/test/PROGRESS/Git or live-runtime mutation; W166292 remains separate.

## 2026-09-14T09:02:11Z — owner selects executable delivery checkpoints

After the prompt surfaced the pending convergence-checkpoint decision and
summarized the recommendation, Slawomir replied "I agree". This selects
DESIGN-RECONSIDERATION-166444.md, SHA256
f0bf84a6217b1f44c9c9b71c29efffa9e11e9db8d6305b5deef7b0d632f165b3.
It explicitly supersedes the preceding awaiting-owner-selection disposition.

Keep the selected ordinary worker architecture and source/test scope. Deliver
one actual producer-to-worker-to-accepted-collection preparation path first,
then finish the selected refusal, replay, identity, cleanup and documentation
acceptance. Resume from short durable author checkpoints across context limits
instead of returning for disconnected preliminary helper sign-off. Preserve
accepted slice1 and useful corrections. The pending strict numeric-type defect
and the real launch/original Job binding remain correctness requirements.

This is a delivery-order and resumption decision, not acceptance of partial
behavior or a new protocol architecture. Checkpoint A is not slice2 acceptance;
checkpoint B is not full W161230 closure. Later derived apply/target-effect,
receipt and final settlement still require concrete selection. Existing I/O
reuse, capacity-before-start, deterministic verification, per-run cleanup,
independent acceptance and W32577 documentation ownership continue to apply.
Cumulative stopwatch approval gates remain removed under M166331. W166292 stays
separate and W156162/W161234 remain dependent on the actual required delivery.

Coordinate return of the unclaimed Work from baton.decide to baton.feat on
owning-team authority so the managed reviewer can hand the selected continuation
to implementation; the prompt neither claims the Work nor acts as its reviewer.

### Reviewer continuation — claim167845, owner reroute167842

Consumed canonical detail, standalone claim167845, all events after166467
through owner reroute167842 and all new discussion (none after M166436).
Re-read selected packet and current dossier. The packet SHA256 matches
f0bf84a6217b1f44c9c9b71c29efffa9e11e9db8d6305b5deef7b0d632f165b3;
all six candidate166444 paths still match recorded hashes and modes.
The09:02:11Z owner selection is complete and already pinned; no additional
selection, helper-review or test-time gate is introduced.

Hand checkpoint A to baton.impl: compose the actual ordinary input, validated
worker launch, materialization and configured execution, real child Work/claim,
capacity-before-start, accepted artifact collection and normal ending/cleanup.
Parent apply remains planned and root retained. Use the existing selected
source/test set; carry the strict numeric-type correction and original Job/
launch binding into this executable composition. Then finish checkpoint B.

Implementation records last runnable command/result, changed files, next wiring
edit and unfinished acceptance in attributable PROGRESS checkpoints. Resume
there across context limits instead of restarting disconnected helper review.
If a concrete runner limit interrupts continuation, retain its evidence and
exact next edit for the next author claim. No actual lifecycle incompatibility
has yet been demonstrated, so none is assumed.

This handoff runs no verification child. Historical/prospective/reviewer costs
remain1106.721556888122s/237.7129594819882s/22.471559100995364s with the existing
qualifications. M166331 removes cumulative gates; focused deterministic scope,
sensible per-run ending/cleanup and independent acceptance remain. W32577
owns main DEPLOYMENT; draft here. Slice3 still needs concrete selection and
W156162/W161234 remain blocked on actual delivery. No product/test/PROGRESS/
Git mutation by reviewer. Pass impl, next feat for executable evidence review.


## 2026-09-14T09:22:31Z — checkpoint continuation, reviewer claim167973

Consumed return167901 and complete new T161230 discussion M167899 after the
previous reviewed handoff167855. The author reports A.0 strict numeric types
and A.1 real input producer/consumer complete, with 55 focused cases passing
in 10.523127 seconds at prospective step35. The next wiring edit is explicitly
A.2 in the newest PROGRESS checkpoint. This is a context-limit continuation,
not a request for helper acceptance or evidence of an architectural blocker.

**Confirmed:** all four reported source/test hashes and ordinary 0644 modes
match the current files; the selected design packet hash also matches. Exact
identity evidence is CONTINUATION-167973.json. These checks establish checkpoint
identity only; the test results and semantic corrections remain author claims
pending independent review of executable checkpoint evidence. No tests were
rerun and no partial behavior is accepted by this continuation.

Under the selected09:02:11Z resumption contract, return directly to impl at A.2:
compose reconciliation_entry.py through baton_worker.main(agent=...), actual
validated launch and owned limits, read_request/verify_input, private scratch
materialization, configured causal execution and declared output artifacts;
then the recipe-only Dockerfile.reconciliation. Continue A.3 actual child
Work/offer/claim and capacity-before-start, A.4 ordinary collection/adoption
and ending, and A.5 the real fixture-process proof. Preserve the explicit
source-only digest versus enclosing ordinary bundle digest distinction.
Neither digest substitutes for trusted launch/request/assignment binding.

A remains incomplete; B refusal/replay/identity/cleanup coverage and the draft
follow it. Slice3 derived apply/target-effect/receipt/final settlement still
requires concrete selection. W156162/W161234 remain dependent; W32577 retains
main DEPLOYMENT. No repeated owner-selection or preliminary helper-review
gate is introduced. Resume across context compaction from the newest author
checkpoint; preserve exact next edit if the runner interrupts continuation.

Costs remain qualified: historical author1106.721556888122s; latest author
reports35 prospective runs totaling290.635887s; reviewer22.471559100995364s
unchanged, with no verification child here. M166331 removes cumulative gates;
focused deterministic scope, sensible per-run ending/cleanup and truthful
unknowns remain. No product/test/PROGRESS/Git edits, broad suite, live model,
engine, image or resource cleanup by this reviewer.


## 2026-09-14T09:33:32Z — A.2 worker preparation scope mismatch, claim168049

review-2026-09-14T09-33-32Z.md records one concrete P1: materialize only copies already combined
state trees and explicitly assigns merge to the manager; PreparationAgent.work
performs no worker merge. That contradicts selected SLICE2-SCOPE-165724 sequence5
and real-worker/conformance/trap acceptance. M168039's no-repository/no-checkout
justification is not a selected scope change. Do not build A.3 around host-merged
content or conflate the original candidate with the derived combined result.

Correct A.2 within the existing worker/producer/recipe/test scope while continuing
A.3 actual coordination, then A.4/A.5 and B. Preserve published-input confinement
and no target/Authority access. No repeat owner-selection or preliminary helper
approval gate. Six reported/current source hashes and both selected packet
hashes match, recorded in candidate-168049.json. No independent test rerun.

This clarifies the latest continuation: useful entry/limits/publication work
remains, but A.2 is not accepted as completed selected preparation. No historical
review is rewritten. Prospective49 rows376.7334088279778s, historical
1106.721556888122s and reviewer22.471559100995364s retain qualifications;
M166331 removes cumulative gates. Existing dependent/doc/slice3 boundaries stay.


## 2026-09-14T09:45:51Z — worker merge correction checked, claim168115

The narrow P1 in review-2026-09-14T09-33-32Z.md is corrected in the current candidate. Resume the selected checkpoint at A.3; this is not acceptance of A.2, checkpoint A, slice2 or the Work.

Consumed return168113 and M168112 after claim168115. Exact five-file bytes and modes are in candidate-168115.json. The author explicitly withdraws the earlier manager-owned-merge interpretation. The producer exports original base/candidate/target Git objects; worker materialize imports them into private scratch, proves the revisions, and _derive_combined performs merge-tree with the explicit base and target/candidate inputs. The derived commit has target and original candidate parents. The report retains the original identities separately from the derived revision/tree. Merge conflict refuses collection without publishing a candidate. This addresses the concrete scope mismatch; it does not establish the complete ordinary lifecycle, confinement or custody contract.

Independent focused verification: the three selected real disposable Git regressions for distinct derivation, preservation of target-only changes and actual conflict all passed. review-run-168115.json and .log preserve the exact command, 30-second bound, exit0 and measured child wall time0.5640499939909205s. The tests exercise PreparationAgent.work directly, not the complete worker main/normal exchange/managed runtime path required by A.5. No engine, image, model or broad suite ran. The author's 68-case result and reversal run remain separately attributed author evidence, not independently repeated here.

Continue tools/integration_worker.py A.3 actual child Work/offer/claim, one actor/root reservation and capacity before launch while the parent offer stays pending; A.4 actual StageExecution freeze/intake/retention adoption and ordinary ending; A.5 fixture-process proof through the real worker boundary with the coordinator trap; then B's selected refusal/replay/identity/cleanup matrix and DEPLOYMENT-SLICE2-DRAFT. Do not restart disconnected helper sign-off or seek another selection for the already selected work. Later slice3 apply/target-effect/receipt/final settlement remains unselected. W156162/W161234 remain dependent; W32577 owns main DEPLOYMENT.

Verification accounting: reviewer W161230 cumulative22.471559100995364 +0.5640499939909205 =23.035609094986284s. Historical author1106.721556888122s retains its estimates/unknowns. Prospective ledger through step55 totals393.43896951296773s, but includes W167896 viewer steps36–42 totaling1.438459018987487s. Newly observed step56 is another W167896 viewer run0.20121729299717117s, not W161230 verification. Preserve all original rows and totals; use the viewer's own ledger for subsequent runs and cross-reference these existing entries without deleting or charging twice. M168092 already recorded this attribution issue. M166331 removes cumulative stopwatch gates; sensible per-run bounds and cleanup still apply. No product, test, PROGRESS or Git mutation by reviewer.


## 2026-09-14T09:57:36Z — A.3 partial continuation, reviewer claim168210

Consumed return168207 and complete new T161230 message168202. Author reports
PreparationExecution ordering composed and182 cases passing at step64, while
explicitly identifying the real Authority/Worker Manager prepare round trip
as unexercised. This is a continuation checkpoint, not executable checkpoint A
acceptance. CONTINUATION-168210.json confirms both newly changed files, five
A.2 files unchanged from candidate168115, and both selected packet hashes.
These are identity checks only; author results remain attributed author evidence.

Resume the newest author PROGRESS NEXT WIRING EDIT: exercise prepare against
real disposable Authority and Worker Manager fixtures, observe actual child
Work/offer/claim through the owners, and require committed capacity before start.
Keep the original parent pending and one reserved actor/root. Then finish A.4
actual freeze/intake/retention adoption and ordinary ending/cleanup, A.5 the
real worker fixture-process/coordinator trap, and B. Do not restart disconnected
helper approval. A.3/A/B and full Work remain incomplete; slice3 still requires
concrete selection. W156162/W161234 and W32577 document ownership are unchanged.

No test child ran here. Reviewer cumulative23.035609094986284s and historical
author1106.721556888122s retain qualifications. Current prospective ledger has
64 rows totaling414.77075325396726s with mixed attribution: viewer steps36–42
and56 belong W167896 and remain preserved. M168202 acknowledges the separation;
subsequent viewer runs use that dossier. Cumulative gates remain removed under
M166331; focused deterministic scope and sensible per-run ending still apply.
No product/test/PROGRESS/Git change, actual engine/model/image or cleanup action.


## 2026-09-14T10:12:19Z — activation blocker superseded by admission-shape diagnosis

Consumed return168289 and complete new T161230 M168288. Candidate two-file
hashes match the handoff, and five A.2 files remain unchanged; identities in
candidate-168292.json. A.3 is incomplete, but the reported activation blocker
is mislocated and does not require another owner decision or a new API.

## Confirmed current failure and bounded correction

One selected end-to-end case was run with only its unconditional skip bypassed
in an isolated reviewer probe; its assertions and repository source were not
edited. Activation succeeds. The traceback reaches PreparationExecution.admit ->
integration_capacity.admit_integration_execution and fails with "the claimed
assignment needs work_ref". Exact evidence: probe-activation-168292.py,
review-run-168292.json/.log, exit1, 0.2137418060010532s under30s. This is not the fixture claim
answer failing activate_assignment, as the current BLOCKER/PROGRESS says.

worker_manager.attempts.assignment_of returns a flat public document with
runtime_attempt_id, authority_uuid, work_id, participant, generation, principal
and effective_scope. admit_integration_execution expects the four-part nested
assignment fence: work_ref={authority_uuid,work_id}, participant,generation.
The current composition passes the flat result directly into the nested input.
The existing test helper CapacityCase.claim_of already maps these exact owner
fields into that fence, and admission itself independently reads the same owner
and makes the same mapping for its comparison (integration_capacity.py798–832).
That lossless interface adaptation is not fabrication of an assignment: it
chooses no identities or generation and is checked against owner state.

An isolated diagnostic patch of only PreparationExecution.admit to map those
four returned fields makes the same case pass with every assertion intact:
probe-normalized-168292.py, review-normalized-168292.json/.log, exit0,
0.21381353000469971s under30s. This is diagnostic evidence, not a product fix or candidate
acceptance. Implement the adapter within the selected integration_worker.py,
with exact owner-derived values and negative mismatched-fence cases. Remove
the five unconditional skips after the corrected tests execute. Append an
explicit supersession of the mistaken activation/expect diagnosis to PROGRESS;
preserve the historical failed-run evidence.

activate_assignment's expect is an expected fence, not authority to invent a
claim. The function compares it to this attempt's committed claim, session
participant, fixed assignment and live Authority assignment before writing.
submit_claim already emits assignment at the top level. There is no reason to
search guessed result/decision/claim containers or invent a new claim shape;
keep the adapter bound to the actual public result contract. No protocol-owner
permission or shared generic owner edit is needed for these existing-scope
composition fixes.

## Remaining real-owner coverage

The new fixture creates a real Authority for create_work, but its port is still
AuthorityPort(fixtures.FakeSession(...), fake_claim_signature), initialized by
claimed(). That FakeSession maintains its own Work/assignment answers, separate
from the real Authority store. Passing this test therefore proves real child
creation and real Worker Manager operations around a simulated claim session,
not one real Authority create/claim round trip. Label this intermediate evidence
accurately, then connect the same disposable Authority's actual authorized
session to the existing port for selected A.3 ownership/replay/parent checks.
Do not interpret "real Authority" as the production Baton coordination store:
all verification stays in disposable local fixtures. No raw coordination DB,
actual engine/model, new auth bypass or shared provider implementation is needed.

Then continue A.4 actual frozen/accepted/retained adoption and ordinary ending,
A.5 real worker fixture-process/coordinator-host trap, and B. Preserve parent
pending, one actor/root, and capacity before launch. No disconnected helper
approval loop. A.3/A/B/full Work remain unaccepted; later slice3, W156162/
W161234 dependency gates and W32577 documentation ownership are unchanged.

Costs: two reviewer children 0.4275553360057529s; W161230 reviewer cumulative23.463164430992038s.
Historical author1106.721556888122s remains qualified. Prospective69 rows
sum to432.9930279539578s, mixed attribution including W167896 viewer36–42/56; preserve
those rows and their separate attribution. M166331 removes cumulative gates;
per-run limits and genuine acceptance remain. No product/test-source/PROGRESS/
Git mutation, broad suite, actual engine/model/image or cleanup by reviewer.


## 2026-09-14T10:18:15Z — existing session adapter supersedes missing-API blocker inference

Consumed return168343 and M168341. The two changed hashes/modes match; five
A.2 hashes remain unchanged. candidate-168351.json binds them and the two
read-only provider sources used for the diagnosis. The assignment adapter
correction is confirmed: the formerly skipped preparation case passes without
patching or bypassing its body. No A.3/full checkpoint acceptance is implied.

## The reported session gap is already composed by the deployment

It is true that bare authority.Session has no publish_answer and a bare
AuthorityPort refuses it. The inference that no real-Authority-backed port can
be constructed, or that a shared owner API must change first, is false.
tools/single_worker.py:_AuthoritySession already forwards the minted session's
actual lifecycle reads/acts and provides an explicit capability refusal for
inquiry publication. _ManagerClaimSession inherits that surface and translates
only concrete Authority claim refusals. Production _compose_one constructs:

    minted = authority.session(given["participant"])
    port = AuthorityPort(_ManagerClaimSession(minted), claim_signature)

This uses the Authority's real claim signature, not fake_claim_signature. The
same existing composition can be reused in selected tests and worker wiring
without editing shared source or inventing a successful publication response.
The absence of inquiry publication is immaterial to this preparation claim path;
if a selected later act actually needs it, report that act and exact capability
requirement then. It is not a blanket reason to keep a fake claim session.

Independent evidence: probe-session-168351.py creates a disposable real Authority
fixture, constructs the existing production adapter/port, claims and replays
against the same real Work, and compares the returned assignment with the real
session's public assignment_of. A second case confirms publish_answer explicitly
refuses with capability rather than a successful no-op. Together with the
corrected preparation case, three tests pass in0.21367539300990757s under30s:
review-run-168351.json/.log. This verifies adapter availability, not the whole
PreparationExecution round trip with a retained parent reservation.

## Concrete continuation

Supersede the blocker inference in the current test/docstring and author
PROGRESS; preserve the true bare-session boundary fact if it remains useful,
but do not make the suite require a missing capability to exist forever. Add
positive coverage using this existing production adapter. Wire the same real
disposable Authority for child creation and the actual participant-bound claim,
including real route/handler/grant fixture setup and own claim_signature. Finish
the selected A.3 parent-pending / one-actor-root / admission-before-launch /
replay ownership checks, then A.4 actual frozen/accepted/retained adoption and
ordinary ending, A.5 real worker fixture-process/coordinator trap and B.

No new Work is filed for an absent Authority API: investigation found existing
composition, not an owner defect. No workaround or generic source change is
needed. This review's clarification is durable in FINDING/PLAN and is the next
implementation input. Do not turn it into another owner-selection or helper
sign-off gate. A.3/A/B/full Work remain unaccepted; slice3 and existing dependent
and documentation ownership boundaries remain unchanged.

Costs: this child0.21367539300990757s, W161230 reviewer cumulative23.676839824001945s. Historical
author1106.721556888122s remains qualified. Current prospective ledger has
72 rows totaling459.7931394559593s, including separately attributed
W167896 viewer36–42/56. Preserve those histories; M166331 removes cumulative
caps. No product/test-source/PROGRESS/Git edit by reviewer, actual engine/model/
image, broad suite or destructive cleanup. Existing standalone canonical
Baton coordination was used throughout; test authorities were disposable only.


## 2026-09-14T10:40:41Z — same-Authority preparation corroborated; resume A.4/A.5/B

Review claim168490 consumed return168488/M168485. review-2026-09-14T10-40-41Z.md
and candidate-audit-168490.json confirm the current eight bound files/modes.
The former split real-create/fake-claim fixture and missing-session-API blocker
are superseded: one real disposable Authority now owns the child Work and its
claim, through the deployment's existing adapter. All124 focused capacity tests
pass in1.3168321559933247s, no skips; review-run-168490.json/.log.

A remaining recovery gap is observed, not inferred: repeating the complete
prepare() after successful admission attempts to reissue its offer and refuses
because the real child is already active. Creation-only replay does not cover
that sequence. probe-resume-168490.py and review-resume-168490.json/.log retain
exit1/one diagnostic error and10 existing passes,0.25653608099673875s. Complete
public-owner-based resume and the already selected restart matrix in B; preserve
the offer owner's non-recoverable-bearer refusal and one actor/root identities.
This supersedes any reading of the author "A.3 closed" heading as whole-sequence
recovery acceptance. Fresh coordination is corroborated; A.3/all checkpoints
remain unaccepted as complete.

Continue A.4 actual StageExecution frozen/accepted/retained adoption and ordinary
ending/cleanup, then A.5 real worker fixture process/coordinator trap and B.
No new owner/helper gate. Parent pending/apply planned/root held, selected path
set, later slice3 selection, W156162/W161234 dependencies and W32577 main
DEPLOYMENT ownership remain. Reviewer cumulative25.25020806099201s; historical
and mixed author attribution retain qualifications. No product/test/PROGRESS/
Git or live engine/model/image changes. Exact evidence and continuation are in
the append-only review.


## 2026-09-14T10:58:34Z — A.4 adoption identity defects, reviewer claim168621

Consumed return168619/M168616. review-2026-09-14T10-58-34Z.md and
candidate-audit-168621.json bind the current nine-file checkpoint and selected
packets. StageExecution remains uncomposed; A.4 is an author partial checkpoint.

Two concrete defects are confirmed through public-owner adoption: a substituted
submission.source_candidate is durably attributed to the unchanged preparation,
and a substituted task_digest is journalled despite disagreeing with admitted
membership. The wrapper checks neither relation; older storage constructors
cannot infer the omitted request/member comparison. probe-adoption-168621.py and
review-run-168621.json/.log record one positive pass and two required-refusal
failures, exit1,0.23117261000152212s under30s. Real disposable Job/Control/coordinator
owners around fixture session; no real Authority/worker/engine claim.

Correct original source-submission bindings and admitted task identity before
coordinator writes, within selected reconciliation/tests, while proceeding with
StageExecution managed wiring, A.5 worker-process/trap proof and B. Do not add
an isolated helper approval loop. The blanket author description that every
adoption fact is owner-bound is superseded by these observed exceptions; useful
custody/harness checks remain. No checkpoint/slice/full Work acceptance.

Reviewer cumulative25.48138067099353s; author82-row587.335292s report and older
qualified/mixed histories preserved. Earlier preparation retry gap remains B.
W32577 is now closed satisfying168561; accepted main DEPLOYMENT hash is
48a3268e456765c02696c897558f1aed9511c39a4188480a8d194b21ac50077f.
W161230 still writes its selected slice2 draft; no new main-guide edit is assigned.
Later slice3 selection and W156162/W161234 dependency gates remain. No reviewer
product/test/PROGRESS/Git or runtime mutation.


## 2026-09-14T11:26:00Z — adoption identity corrections corroborated; resume composition

Reviewer claim168804 consumed return168740/M168737. The two earlier defects
are corrected at the exact candidate-168686 bytes: submission is resolved
from the digest-pinned request and accepted coordinator entry rather than a
caller operand, and task_digest is compared with admitted membership before
coordinator writes. This supersedes their outstanding-correction status; it
does not establish complete checkpoint/source-attribution acceptance.

Six focused checks pass in0.28352203899703454s under30s, exit0, including
substitution refusal, owner-derived identities and refusal followed by honest
adoption. review-run-168804.json/.log and candidate-audit-168804.json retain
commands, timings and the nine matching candidate hashes/modes. Both selected
scope packets and accepted main DEPLOYMENT digest also match. Disposable real
Job/Control/coordinator owners used the existing fixture session: no real
Authority claim, worker process, engine, model or image evidence is claimed.

review-2026-09-14T11-26-00Z.md records the unchanged next executable edit:
StageExecution managed preparation/adoption, preserving direct/legacy, then
A.5 actual worker fixture process and coordinator-host trap, then B including
claim168490 whole-prepare retry recovery and DEPLOYMENT-SLICE2-DRAFT.md. No
new owner/helper sign-off gate. A.3/A.4/A/B/slice2/full Work remain unaccepted;
later slice3 selection and W156162/W161234 dependencies are unchanged.

Reviewer cumulative25.764902709990565s. Current prospective ledger86 rows
records640.0139192189556s; preserve mixed W167896 viewer36–42/56 attribution
and the qualified historical author1106.721556888122s rather than summing
these into an invented exact total. Cumulative caps remain superseded.
No reviewer product/test/PROGRESS/Git changes or destructive cleanup.


## 2026-09-14T11:36:00Z — correct admission placement and resume actual wiring

Reviewer claim168871 consumed return168868/M168862. The ten candidate168828
files match; only test_managed_preparation.py changed. The guard exercises
patched lookups and allowed export but no managed stage/worker composition.
No helper/checkpoint/slice/full Work acceptance or test rerun is made here.

The latest author NEXT paragraph is superseded as an insertion-point proposal:
Integration.reconciled is called through StageExecution.launch after the Job
manager has observed the parent claimed. Starting the same-actor preparation
claim there violates the selected parent-pending rule. The existing selected
interception remains PooledManagerOperations.admit after allocation and before
worker admit. Compose an integration_worker wrapper through StageExecution
_integration_operations, defer the parent without a receipt through the
existing nondurable-refusal path, and drive real child ordinary operations.
review-2026-09-14T11-36-00Z.md records exact call-chain and launch/ending owners.
No new API, extra actor or generic scheduler/Authority source change is needed
on the evidence read. Revalidate actual operands as implementation proceeds.

The temporary test requiring the managed branch to stay absent is not an
acceptance invariant; replace it with the selected behavioral proof during
wiring. mock.patch.object changes named attributes, not pre-captured aliases
or existing class bases, so the author's universal-alias-trap statement is
superseded by this limitation. Arm/instrument the actual composed execution
path and retain the positive forbidden-call discriminator; do not launch
another disconnected guard project.

Direct response to the author's question: attempt bounded production wiring
next and preserve an honestly partial runnable continuation if necessary.
The selected design permits resumption across context compaction; no single-
context completion or isolated helper sign-off is required. Report an actual
managed-runner limit only if observed. Then finish A.4 ordinary custody/
ending/adoption, A.5 actual worker fixture process and B/retry/draft. Later
slice3 selection, W156162/W161234 gates and main-guide protection remain.

candidate-audit-168871.json binds the exact source/test and read owner files.
No new runtime spending; reviewer cumulative25.764902709990565s unchanged.
Author prospective89 rows679.6924070959387s retains mixed viewer36–42/56 and
older qualified histories. No product/test-source/PROGRESS/Git changes,
engine/model/image execution or destructive cleanup by this reviewer.

## 2026-09-14T11:52:35Z — admission deferral corroborated; complete selected composition

Reviewer claim168988 consumed return168986/M168985. candidate-audit-168988.json
matches all ten candidate168895 files/modes and both selected packets plus the
protected main guide. Five focused tests corroborate ordinary forwarding,
allocation/claimed-parent refusals and real disposable-Authority child admission
with no parent offer and apply still planned. The wrapper is called directly;
no composed manager sweep, worker process, ending or adoption is demonstrated.
This supersedes the prior absent-wrapper status, not incomplete checkpoint
acceptance. Current deployment still supplies no ManagedPreparation operands.

review-2026-09-14T11-52-35Z.md carries the selected continuation: resolve actual
checkpoint/proposal/Job-limit operands, drive ordinary child lifecycle and
owner exclusion/adoption, prove the real composed manager/worker path under
the host trap, then B including the observed repeated-prepare gap and the
slice2 draft. No new helper gate; continue across context compaction unless an
actual execution limit or incompatible owner invariant is observed. Slice3,
full acceptance and dependent provider gates remain unchanged.

The first reviewer invocation omitted PYTHONPATH and failed test loading in
0.0636182349990122s. Corrected focused verification passes in0.2137739150202833s;
both exact attempts are retained in review-run-168988 and corrected JSON/logs.
Reviewer cumulative26.04229486000986s includes both. Current prospective author
94-row ledger746.1117171389226s supersedes the handoff's719.3s estimate, preserving
mixed viewer attribution, older qualified histories and unmeasured costs.
The author's paired13-error report remains unverified attribution, not a waived
failure or proof of another Work's causality. Preserve paired logs/base identities
in the next packet. No source/test/PROGRESS/Git or real engine/model/image changes
by this reviewer; only dossier review/planning evidence was written.

## 2026-09-14T12:05:46Z — retained errors classified; no commit prerequisite

Reviewer claim169074 consumed return169071/M169070; no product delta was
submitted. All six bound source/test paths and three evidence files match.
The paired logs agree on13 errors, but not one cause:4 missing reconciles,
8 missing authority.proposal and1 Git fixture materialization error. The
single-cause explanation in candidate169019/PROGRESS is explicitly superseded
by this log classification. No aggregate-green result or assertion waiver.

The reported untracked-module blocker is explicitly superseded: the importer
adds v12/worker, and v12/worker/integration_contract.py is tracked in HEAD with
identical working bytes. The reported v12/python-only export omitted that
sibling dependency. locator-audit-169074.json records the exact digest. No
commit, install, new Work or diagnostic rerun is needed. Three named source
regions do equal HEAD, as claimed; review-audit-169074.json retains those checks
and every logged error identity. W103068's closed final review03:42:24Z already
preserves a13-error historical baseline alongside focused factory acceptance;
it neither identifies every present error nor waives compatibility obligations.

review-2026-09-14T12-05-46Z.md directs the next product edit to the already
selected operand resolver and full managed composition. Keeping paired evidence
was requested alongside that work, not as a replacement evidence-only milestone.
Record reported context limits honestly and resume across compaction. No further
helper approval or scope request; preserve all A/B, slice3, dependent-provider
and protected-guide boundaries. No source/test/PROGRESS edits or runtime tests
by reviewer; cumulative runtime26.04229486000986s unchanged. Static audits
0.12428491498576477s and0.037703704001614824s are separate from author94-row
746.1117171389226s qualified subtotal and paired-log self-reported durations.

## 2026-09-14T12:15:55Z — real checkpoint response rejects operand resolver

Reviewer claim169146 consumed return169140/M169138. All seven bound candidate
files/modes match. The new preparation_operands helper cannot consume the
integration_checkpoint response it names as its owner: it reads top-level
path_set_digest/test_scope_digest, while the real reader returns only line_id,
checkpoint_id, verdict_id, checkpoint_digest and evidence. path_set_digest is
nested in evidence; test_scope_digest is absent. The test fixture invents both
top-level fields, explicitly superseding the author's real-owner-shape claim.

probe-operands-169146.py uses the existing real disposable accepted-checkpoint
fixture and reproduces KeyError('path_set_digest') before bundle comparison.
review-run-169146.json/.log records one diagnostic failure in0.4139802400022745s,
with exact owner keys and simulated fixture boundaries stated. Correct actual
owner resolution while completing deployment construction; separately resolve
test-scope authority from the selected scope/configuration rather than changing
the checkpoint API or inventing a digest. Preserve child Work and target in
the durable intent on replay; current helper derives only attempt/offer IDs.

review-2026-09-14T12-15-55Z.md carries the unchanged composed-checkpoint
continuation, not another helper sign-off request. No deployment selection or
A/B/slice/full acceptance is proved. Reviewer cumulative26.456275100012135s
includes the retained failure; author98-row799.6795605339169s report retains
prior attribution qualifications. No reviewer product/test/PROGRESS/Git or
live-engine/model/image changes; only dossier research/review evidence changed.

## 2026-09-14T12:27:34Z — checkpoint-field correction corroborated

Reviewer claim169229 consumed return169212/M169210. All six candidate169172
files/modes match. Nested path-set reading and a separate test-scope argument
correct the observed reader mismatch. Two targeted checks pass: the real
accepted-checkpoint answer reaches bundle refusal, and missing evidence paths
refuse. This supersedes the specific P1 as outstanding at these bytes, not
deployment/test-scope-authority or checkpoint acceptance.

review-2026-09-14T12-27-34Z.md notes that the original narrow probe now accepts
a missing-argument TypeError and must not be cited unchanged as regression
acceptance. The new typed tests supply correction evidence. No additional
probe task; proceed to actual deployment construction and lifecycle/adoption,
A.5 and B with all existing selected boundaries intact.

First reviewer invocation omitted tools from PYTHONPATH: two loader errors,
0.1636449669895228s. Corrected author-recorded import context passes both tests
in0.4639832240063697s; exact JSON/logs retained, cumulative27.083903291008028s.
No source/test/PROGRESS/Git or engine/model/image edits by reviewer; only dossier
review/planning evidence. Prior author costs retain their qualifications.

## 2026-09-14T12:38:35Z — consistency guard is not durable request recovery

Reviewer claim169283 consumed return169280/M169273. Six candidate169253 paths
match. Four new direct guard tests pass in0.2135938520077616s; exact audit and
run JSON/logs are retained. Reviewer cumulative27.29749714301579s.

review-2026-09-14T12-38-35Z.md corroborates changed-Work/request refusal and agreement/absence.
It explicitly supersedes the claim that this completes durable resumption:
the intent stores child Work and request digest, not the target/request itself.
The composer must recover and verify the persisted immutable request through
its existing input owner on retry, rather than re-resolving a newer canonical
target and repeatedly deferring. The earlier claim that preparation_intent_of
answers both child and target is superseded. Whole-prepare admitted-child
retry remains unproved. No generic API/schema change selected.

Proceed to actual deployment construction, ordinary child launch/ending/real
exclusion/adoption, process-trapped checkpoint A, then B and the slice2 draft.
No further helper approval gate. All selection/dependency/main-guide boundaries
remain unchanged. No reviewer product/test/PROGRESS/Git/engine/model changes.
Author106-row908.289996341907s report retains failed runs and prior accounting
qualifications; no cumulative test-time gate.

## 2026-09-14T12:47:41Z — published request reader works; recovery ordering remains due

Reviewer claim169347 consumed return169345/M169343; seven candidate169317
files/modes match. Three new reader tests pass in0.21367610999732278s.
The independent probe confirms restoration of target/task/input with a supplied
root, plus two remaining gaps: the resolver supplies no published_root and
_recovered skips recovery without it; fresh-target resolver equality refuses
before late recovery can run. The blanket missing-input refusal claim is
explicitly superseded by those actual conditions. Recover before first-sweep
operand resolution/publication in the real composer, keeping equality strict.

review-2026-09-14T12-47-41Z.md records the continuation through actual deployment
construction, ordinary lifecycle/exclusion/adoption, process-trapped A, then
B/retry/draft. No helper sign-off gate or new generic API/schema authority.
Probe run discovered11 imported owner tests alongside3 research checks:14pass
in0.6642682650126517s, with gaps labelled observations rather than
acceptance. Reviewer cumulative28.175441518025764s includes both
runs. No product/test/PROGRESS/Git changes. All selected scope/dependent gates/
protected-guide boundaries remain; author reported costs retain qualifications.

## 2026-09-14T12:58:48Z — intent ordering corrected; resumed identity coverage still due

Claim169416 consumed return169414/M169413. Seven candidate169372 paths match;
five focused checks pass in0.313786089012865s, reviewer cumulative
28.48922760703863s. Early intent read and required root correct
the specific previous missing-root/late-read gaps; the deployment resolver
itself remains absent. review-2026-09-14T12-58-48Z.md records remaining composition.

The changed-child refusal case and moved-target recovery are different
invariants. The new _recovered test does not replace _preserved child-identity
coverage. The unchanged-resume test now passes None despite creating a committed
intent, so its resume claim is explicitly superseded: it only proves absence
passthrough. Restore equivalent real-intent agreement/mismatch checks in the
composed executable path, not an isolated helper milestone. All scope/gates stay.

Author reports an out-of-scope stray root tools/integration_worker.py creation
and removal due to relative edit path/cwd. Current absence and clean tools Git
status are confirmed; history/removed bytes/removal command remain reported.
This is author execution misuse, not a demonstrated Baton defect. Preserve that
concrete removal despite the packet blanket no-cleanup wording. No reviewer
product/test/PROGRESS/Git or cleanup changes. Author costs remain qualified.

## 2026-09-14T13:08:52Z — resolver has concrete owner API mismatches

Claim169477 consumed return169474/M169473. Seven candidate paths/modes match.
Two corrected child/agreement guard tests pass in0.2137363810034003s;
they use a supplied intent dict, not a committed-owner intent. Previous helper
coverage findings are superseded at these bytes.

review-2026-09-14T13-08-52Z.md records independently reproduced AttributeError
from required_tests on StageDeployment (owner is Integration) and TypeError
from the positional job_execution_reader call (four keyword-only operands).
probe-resolver-169477.py/.logs preserve both; diagnostic exit0 observes defects,
not acceptance. The recovery-first resolves-nothing claim is also superseded:
line/checkpoint/required-test reads precede the intent branch. Profile/harness/
apply-task digests remain unproved and must come from their actual owners.

Correct these within actual deployment construction, then ordinary lifecycle/
exclusion/adoption and process-trapped A, B/retry/draft. No helper-only gate,
new generic schema/API or scope/dependency change. Reviewer cumulative
28.86670601505466s includes diagnostic0.1637420270126313s.
No product/test/PROGRESS/Git changes; prior author cost/baseline qualifications
and all selected boundaries remain.

## 2026-09-14T13:22:04Z — resolver corrections corroborated; task material and retired gate clarified

Claim169546 consumed return169544/M169541. Six enumerated candidate files match;
three resolver unit tests pass in0.2136666239821352s, with mocked reader and
supplied intent limitations. Specific API-shape and early-recovery defects are
corrected at these boundaries. Reviewer cumulative29.080372639036796s.

APPLY-TASK-MATERIAL-169546.md answers that stable apply task material belongs to the integration
task/input producer, not a future collector or a stage getter. No complete
producer exists here yet. The selected scope separates task-material digest
from late envelope/collected-content binding; the missing future digest alone
does not establish a core design impossibility. Revalidate and measure actual
held instruction material; do not use placeholders or silently select slice3.

review-2026-09-14T13-22-04Z.md records that /tmp/w166281_run.py still enforces a
CAP1200 check despite its header and the owner ruling. Its cannot-relax-policy
claim is superseded: existing authority permits updating/replacing the stale
local gate with per-run bounded measured execution, preserving history. No new
permission/replenishment gate. Author116-row1175.6573671388498s and unledgered
21.293s self-report remain distinct and qualified. No reviewer product/test/
PROGRESS/Git/runner edits. Continue selected construction/lifecycle; all gates
and later-slice boundaries remain unchanged.

## 2026-09-14T13:29:43Z — task-byte hashing and gate retirement corroborated, construction still due

Claim169609 consumed return169607/M169604. Six candidate169578 paths/modes
match. Hash/absence checks use invented task bytes and establish helper
behavior; actual configured workload provenance remains due with construction.
The broad ownership-complete claim is qualified accordingly in
review-2026-09-14T13-29-43Z.md. No additional runtime test; reviewer cumulative
29.080372639036796s unchanged.

Runner CAP gate is removed. Ledger120-row1261.8719327218307s and first116-row
1175.6573671388498s sums match; unchanged historical rows not independently
certified, and unledgered21.293s self-report remains separate. Runner uses
subprocess.run timeout with no process-group/descendant cleanup, so its blanket
cleanup claim is superseded for process-spawning verification. No leak observed
here. Add bounded owned descendant termination alongside actual construction,
not another runner-only milestone or permission gate.

Continue worker acceptance/launch/ending/exclusion/adoption, process-trapped A
and B/whole-prepare retry/draft. No reviewer product/test/PROGRESS/Git/runner
changes; all selected scope, later-slice exclusions and dependent gates remain.

## 2026-09-14T13:39:03Z — construction exists; selection and partial cleanup defects observed

Claim169661 consumed return169659/M169658. Six candidate169630 paths match.
Construction is present now, superseding literal absence, but no composed
checkpoint is proved. probe-selection-169661.py confirms string-false activation,
true-selection/missing-owner fallback, and absent close calls after port refusal
with mocked resource constructors. No real leak claimed. Diagnostic duration
0.21374120301334187s; reviewer cumulative29.294113842050137s.

review-2026-09-14T13-39-03Z.md requests static closed selection validation, fail-closed
selected-owner construction and cleanup spanning the whole partially built
operation. The new source-text selection test is not behavioral proof. Runner
group signals are added, but early signal errors can leave out/err unbound and
skip evidence; pipe completion is not group exclusion, and elapsed omits cleanup.
Repair alongside actual construction/worker acceptance/lifecycle/adoption, then
process-trapped A and B/retry/draft. No helper/runner-only milestone, cumulative
gate or new scope authority. All dependent/later-slice/guide boundaries remain;
reviewer dossier-only edits and author cost/history qualifications preserved.


## 2026-09-14T13:49:55Z — review169721: constructor corrected, static preflight still late

Confirmed by review-2026-09-14T13-49-55Z.md and probe-preflight-169721.py:
all four new constructor checks pass, but real held_configuration preserves
seven malformed integration_preparation values which the later selector rejects.
This explicitly supersedes author claim169682's statement that every defect from
review169661 was corrected. Truthiness, missing-owner fallback and wrapping
closure are corrected; preflight placement is not. Validate the closed selection
before worker/resource construction. Runner output initialization and duration
accounting are corrected; its disclaimer of descendant exclusion is honest but
leaves that cleanup obligation open. No live leak was observed.

Five focused checks/diagnostic complete in0.2638092449924443s; reviewer cumulative
29.55792308704258s. Six candidate hashes/modes match, protected guide unchanged.
Current PLAN carries selected deployment/worker launch/ending/exclusion/adoption,
real apply-task provenance, whole-prepare replay and B/draft continuation. No
checkpoint, slice or Work acceptance; no dependency release. See full review for
exact boundaries, author131-row1379.641547088849s reported evidence and retained
historical qualifications.


## 2026-09-14T13:56:54Z — review169780: static preflight fixed; group observation is not resistant cleanup

Review-2026-09-14T13-56-54Z.md confirms the static-preflight correction and
explicitly supersedes that open P1 from review169721. New regression passes.
Candidate169753 changed source/test/evidence and prior unchanged paths match;
protected guide unchanged. The runner now records group liveness, and retained
step999 supports TERM-success. The broader cleanup-proved wording in author
claim169753 is superseded for leader-first/TERM-resistant descendants: an actual
runner diagnostic with mocked process/group/clock owners confirms communicate
completion still skips KILL and leaves a remaining group after the bounded poll.
Failure is recorded honestly; termination remains owed. No real leak was created
or observed. Preserve the existing proof rather than rerunning its fixed step999.

Two focused checks/diagnostic cost0.2637588809884619s; reviewer cumulative
29.821681968031044s. Author134-row1425.8296466398344s sum matches, with prior
historical qualifications retained. Current PLAN continues executable checkpoint A
then B under the selected scope/design, not another helper-only review milestone.
No actual execution limit or incompatible owner invariant was reported. No
checkpoint/slice/Work acceptance or dependent release.


## 2026-09-14T14:02:22Z — review169821: timeout escalation corrected; executable checkpoint still due

review-2026-09-14T14-02-22Z.md confirms group liveness now controls TERM-to-KILL
escalation and explicitly supersedes review169780's open correction request.
Retained actual fixtures/logs/ledger corroborate resistant-descendant TERM/KILL
cleanup13.107295797002735s and ordinary TERM-only cleanup3.1036346280016005s.
Both remain timed-out failed runs with successful cleanup, not test successes.
Candidate hashes/modes match; product/test source and protected guide unchanged.
No new reviewer runtime; cumulative29.821681968031044s. Author137-row
1463.5995004548342s sum matches with prior historical qualifications retained.

The immediate supervisor objection is resolved. Current PLAN directs actual
selected managed deployment and ordinary worker launch/exchange/ending/custody/
adoption, task provenance and admitted-child replay, then B/draft. No further
supervisor approval or auxiliary-only milestone is requested. Continue across
compaction under the selected design/scope and report the executable checkpoint
or an exact blocker from actual wiring; no incompatible invariant or execution
limit was reported. No checkpoint/slice/Work acceptance or dependent release.


## 2026-09-14T14:10:35Z — review169861: selected factory works; alleged product blocker is fixture mismatch

review-2026-09-14T14-10-35Z.md and probe-fixture-169861.py/169861b.py establish
that ServingCase supplies an existing plain directory/generic workload to a Git
checkpoint and synthetic base. The reported ProfileRefusal reproduces on sweep1.
Existing ComposedOneJobCase provides a coherent disposable Git source and real
base; with managed selection it passes materialization and reaches implementation
waiting with one simulated worker start. This explicitly supersedes author
claim169839's assertion of an external product defect preventing this tree from
reaching integration. Full traversal remains unproved; the exact reported early
boundary is passable without any product change or profile stub. Reuse existing
Git-backed fixture and review-traversal helpers under standing test authority.

All three new selected/unselected/digest factory checks pass, superseding literal
absence of selected-composition evidence. The digest check still measures its own
resolver field containing generic fixture workload material; qualify complete
provenance closure and prove the intended configured material through execution.
The historical13-error set is mixed, not13 manifestations of the Git error. No
new dependency/product attribution is justified by that baseline comparison.

First reviewer run0.4139582220232114s included a failed sweep0 assumption; corrected
sweep1 diagnostic0.2637857149820775s passed. Both preserved, cumulative
30.499425905036333s. Candidate hashes/modes match; source/supervisor/protected
guide unchanged. Author138-row1485.2095332058263s ledger retained with historical
qualifications and separate traversal cost not established by the submitted run.
Current PLAN continues actual selected child launch/ending/custody/adoption/replay
and B/draft. No checkpoint/slice/Work acceptance or dependent release.


## 2026-09-14T14:19:04Z — review169913: pre-call acceptance gap and publication retry collision

Selected deterministic upstream traversal corroborates bundle-home creation and
byte-export runner fixes. review-2026-09-14T14-19-04Z.md clarifies/supersedes the
claim that PreparationExecution.prepare was reached: held["accept"] raises while
Python evaluates call operands, before that method runs. A trap proves no call.
The next ordinary sweep returns deferred operation-collision because publication
already exists and no preparation intent was committed. This is a concrete
publication-before-intent cut requiring recovery, additional to admitted-child
replay. Never delete/rewrite immutable publication to get past it.

The existing ordinary worker composition already owns acceptance: admit scopes
the expected offer, delivered checks exact identities and invokes accept_offer
with the bearer and participant-bound port. This is a capability boundary, not
a requirement to accept inside a later workload process. Reuse it for actual
child identities/input, preserving all owner checks and capacity-before-start.
Current PLAN connects this to ordinary launch/ending/custody/adoption and B/draft.

First diagnostic0.5641060869966168s confirmed KeyError but incorrectly expected
retry refusal to escape sweep; corrected deferred-result diagnostic
0.5641321859729942s passed. Both retained; reviewer cumulative
31.627664178005944s. Author139-row1506.8876871798304s matches, separate traversal
cost remains explicitly unknown. Future diagnostics require bounded runnable
evidence; no retrospective budget gate. Candidate/source/protected-guide checks
match; no checkpoint/slice/Work acceptance or dependent release.


## 2026-09-14T14:32:52Z — review169999: contract omitted and actual retry states not recovered

Independent traversal corroborates child acceptance and the missing route-handler
refusal. With the handler registered in a disposable fixture, the child is
claimed with no generation: resolver operands omit its v12 assignment contract,
so Authority follows its ordinary non-v12 rule and Worker Manager refuses the
answer. Subsequent sweeps reissue offers against already accepted or active
child state, causing lost-bearer/active-Work refusals. Bind the real configured
contract and recover committed offer/claim/assignment effects through their
existing owners, preserving all fences and the one actor/root.

Publication is now read on retry, but the injected exception before intent commit
marks allocation recovery-required through the scheduler; the next sweep refuses
that state at intent creation. This explicitly supersedes claim169942's statement
that the complete publication-before-intent cut is handled. Preserve uncertainty
and reconcile held capacity through positive owner evidence; no reset/release
workaround or generic-source change is selected. See
review-2026-09-14T14-32-52Z.md for exact paths, diagnostics and continuation.

Two-scenario observations0.8643600590003189s plus failing publication recovery
check0.514052824000828s are retained; reviewer cumulative33.00607706100709s.
No preparation worker/actual engine/model executed. Author144-row
1614.8909402878373s sum matches; unknown traversal costs remain unknown. Future
diagnostics require bounded runnable measured evidence, without a retrospective
accounting gate. Candidate/protected-guide/supervisor hashes match. Continue
ordinary child lifecycle/adoption/replay and B/draft; no checkpoint/slice/Work
acceptance or dependent release.


## 2026-09-14T14:44:17Z — review170051: contract fixed; attempt activation order already selected

Candidate170031's V12 contract reaches activation in independent traversal; it
refuses no runtime attempt and starts no preparation worker. The accepted
SLICE2-SCOPE-165724.md lines66–73 already selects public record_attempt and
activate_assignment after claim, capacity admission, then ordinary launch whose
identical owner calls replay. Revalidated against current attempt signatures,
activation journal and capacity owner's attempt/assignment readers. This explicitly
supersedes the author claim170031 PLAN/candidate statement that the order remains
an open design question; it is implementation continuation under existing scope.

See review-2026-09-14T14-44-17Z.md for exact operands, provenance and continuation. Existing
receipt/claim recovery, held-capacity pre-intent recovery, actual child worker
composition, lifecycle/custody/adoption and B/draft remain required. No new scope
or generic-source edits selected. Diagnostic exit0 records the activation refusal,
not checkpoint acceptance. Independent duration0.864293163002003s; reviewer
cumulative33.87037022400909s. Author145-row total matches,
separate self-reported0.604501s probe remains separate. The probe needs the existing
supervisor for a wall-clock bound;30 iterations/self-measurement alone are not one.
Candidate/protected-guide/supervisor hashes match. No checkpoint/slice/Work
acceptance or dependent release.

## 2026-09-14T14:50:52Z — owner stops the non-converging execution loop

Slawomir, after the 88-message status assessment, directed: "right, we need to
stop it then". Confirmed operational decision: stop current W161230 execution
and its automatic implementation/review continuation pending owner reconsideration.
This supersedes prior instructions to continue immediately through checkpoints
A/B. It does not reject or erase the accepted slice1 work, partial candidate,
tests, reviews or evidence, and does not accept slice2 or close W161230.
W156162, W161234 and W2 dependencies remain unchanged.

At pre-stop snapshot170118 Claude held claim170083, episode170080; runtime
incarnation b0f81008-61fd-4707-a9d2-f424100753b8 reported working. The current
ACP bridge is pid1545518. Stop its supervised process domain before recovering
the exact claim and parking Work; ledger release alone is not process termination.
baton.prompt records the decision and performs available operational steps;
owner-only ledger recovery/parking must remain explicitly outstanding until
canonical confirmation. Preserve all partial filesystem changes. No new tests,
implementation, acceptance, dependency release or restart is authorized by this stop.

### Follow-up — owner permits waiting for a safe stop

Slawomir clarified: "we can wait for stop". Use a cooperative safe handoff,
preserving the current partial state, rather than further process termination
attempts. The attempted SIGTERM returned "No such process" inside this execution
environment while subsequent ps and runtime still showed the bridge working;
no shutdown is claimed. This is an operational visibility/signal-boundary finding,
not established as a Baton defect. Supersedes immediate runner-shutdown/recovery
as the selected procedure above. Current Handler should finish only necessary
safe stopping/cleanup, record partial state, and pass to baton.ops for owner
reconsideration; no further implementation/review cycle. A reviewer that receives
the ordinary handoff before seeing this ruling should likewise return to owner
without another review/implementation cycle. Do not release another live claim.

## 2026-09-14T14:52:38Z — owner selects progress review, decomposition and serial tuner execution

Slawomir specified the replacement delivery procedure: "at the next hand off
review the progress, then split the remaining work into sub-jobs, assign to
turner, run one by one to completion". In the established team, "turner" is
interpreted as baton.tuner (endpoint baton.tune), not a new participant.

This supersedes the earlier return-to-baton.ops/wait-for-reconsideration
instruction and message170128. Preserve the safe handoff boundary and stop the
old monolithic implementation/review correction loop. At the next handoff,
baton.feat / baton.codex owns a progress audit and concrete decomposition, not
another request for Claude to continue the whole remaining implementation.
Re-read the final author handoff, current candidate and actual runnable evidence;
distinguish independently accepted work from partial or unproved work. Do not
freeze the split from the 88-message snapshot if the current turn has advanced it.

Create canonical child Work for the remaining deliverables, with bound dossiers,
explicit current plans, source/test ownership, prerequisites and observable
completion criteria. Preserve parent W161230 and its accepted slice1/evidence.
Cover the full unfinished outcome, including preparation, recovery/replay and
the remaining apply/receipt/final-settlement work; record concrete later-slice
scope before its implementation. Prefer executable outcomes over helper-only
milestones. Existing product boundaries and genuine acceptance requirements hold.

Assign implementation to baton.tune / baton.tuner and enforce one child at a
time through live dependency/containment edges and normal claims. Complete each
child through independent review and any applicable integration/owner acceptance
before enabling its successor. Keep W161230 as the umbrella, not a competing
implementation assignment. This owner instruction authorizes the decomposition
and serial execution; it does not require another generic approval of the same
delivery procedure. Do not silently expand product scope or bypass an actual
owner-only act. No parallel agents or second participant contexts are requested.
W161230 closes only on its complete accepted outcome with children complete;
W156162, W161234 and W2 remain gated until then.

## 2026-09-14T14:53:26Z — owner clarification: review only, then decide sub-jobs together

Slawomir clarified: "together we will decide what the sub-jobs should be" and
"this must NOT go through another dev cycle after the review".
This explicitly supersedes the 14:52:38Z entry's interpretation that a managed
reviewer could autonomously select/create/assign child Jobs and start serial
execution. That interpretation was baton.prompt's, not the owner's intended
authority. No such child creation, assignment or execution was performed.

Current instruction: allow the next safe handoff to baton.feat / baton.codex for
progress review only. Audit the final author handoff, actual candidate and
evidence; distinguish accepted, partial and missing work, optionally proposing
a split for discussion. Then pass W161230 to baton.ops with set-next=baton.ops
for Slawomir and baton.prompt to decide the sub-jobs together. NO DEVELOPMENT
CYCLE AFTER THAT REVIEW: do not pass to impl/tune, implement reviewer corrections,
or create/assign/queue child Jobs before the joint decision. Preserve candidate,
evidence and dependency gates. No Work closure or dependent release from this audit.

This also supersedes message170128's instruction to omit the progress review:
one progress review is wanted, followed by owner return. The intended executor
after the joint split decision is baton.tuner, with one selected sub-job at a
time to completion. That later assignment/execution remains pending selection.

## 2026-09-14T14:54:54Z — owner clarification: Claude or tuner, concurrency where permitted

Slawomir clarified: "sub-jobs can be run by claude/tuner if concurrency allows".
After the joint selection of sub-jobs, implementation may be assigned to either
baton.claude (baton.impl) or baton.tuner (baton.tune), using available concurrency
where dependencies and explicitly coordinated file ownership permit it. This
supersedes the tuner-only and blanket one-at-a-time execution wording in the
14:52:38Z and 14:53:26Z entries and message170138. Dependent or overlapping work
remains ordered; concurrency does not waive independent review or completion
criteria. Use the existing managed participants, not duplicate contexts.

The immediate boundary is unchanged: NEXT HANDOFF IS PROGRESS REVIEW ONLY,
then return to baton.ops with set-next=baton.ops. Slawomir and baton.prompt decide
the sub-jobs together before any creation/assignment/execution. No further
development cycle after that review is authorized by this clarification.


## 2026-09-14T15:23:18Z — progress audit170280 complete; owner discussion only

Under M170138/M170149, review-2026-09-14T15-23-18Z.md audits candidate170083 and saved evidence,
without new tests or implementation. Slice1 historical acceptance is preserved;
slice2 is partial. Current started counter means admitted preparation, not worker
launch. Runtime lifecycle/custody, recovery and full slice2 acceptance remain
unfinished; later apply/receipt/root settlement is still unselected. No checkpoint
or Work acceptance, closure or dependent release follows. Return to baton.ops with
set-next=baton.ops, not impl/tune. Proposed split in the review is discussion only:
Slawomir and baton.prompt select any sub-jobs together before creation/execution.

All four candidate hashes/modes match; review-audit-170280.json snapshots30 scope
paths and full-run failure categories. Step146 passes416 tests; step148 fails40
and errors18 of7094, with20 skipped. The13 stage_execution errors have4 reconciles,
8 proposal and1 Git-source causes, explicitly correcting the author's single-cause
summary. Located baseline logs predate this author claim; exact current-round
revert/restore provenance remains unverified. M170275 published only a literal
/tmp locator; readable body and old baseline logs are preserved in this dossier.

Operational finding: broad discovery reached real-engine test code despite the
selected deterministic/no-broad/engine boundary. Its cleanup assertion observed15
global-prefix container names, with ownership/persistence unknown; owner operations
must assess exact provenance before cleanup. No reviewer engine query/cleanup or
new run occurred. This is not a cumulative-budget issue. Author150-row sum is
2343.9140903438265s; separate diagnostics/comparison costs remain qualified.
Reviewer cumulative unchanged33.87037022400909s. All partial source/tests/evidence
and W156162/W161234/W2 gates preserved.

## 2026-09-14T15:29:03Z — owner selects the four outcome groups

Slawomir supplied the Docker listing recorded in OWNER-CONTAINERS-2026-09-14.txt
and confirmed: "I agree with the four groups". The joint split decision required
by the 14:53:26Z ruling is now made. This explicitly supersedes the pending-selection
and no-child-creation language in that ruling and progress audit170280 for the
four selected child outcomes: (1) complete one ordinary managed preparation,
(2) complete preparation failure/restart coverage, (3) approved apply and safe
settlement, (4) complete feature acceptance/documentation. The monolithic parent
implementation loop remains stopped. Preserve historical evidence and parent ID.

Create one canonical child Work/dossier per selected group. First delivery is
assigned to baton.tuner as explicit application-code implementation within the
existing selected preparation scope; independent review remains baton.codex.
Subsequent groups may use Claude or tuner after dependencies and file ownership
allow; the initial sequence is 1 -> 2 -> 3 -> 4 because the composed outcomes and
coordinator/capacity paths overlap. No parallel shared-path edits. Finish each
child through independent review and applicable owner acceptance before its
successor executes. Group3 includes concrete later-slice scope/design selection
before later-slice implementation; agreement on groups does not invent that path
packet or authorize unbounded generic-owner changes. Group4 preserves current
documentation ownership and verifies the full outcome before parent closure.

Only the new bounded child assignments are authorized to resume development.
Neither creation nor a passing helper suite accepts the parent or releases
W156162/W161234/W2. All verification remains focused and deterministic, with
ordinary per-run supervision and truthful durations. No broad discovery, actual
engine/image/model execution, package installation, Git mutation or cleanup is
selected. Standing test authority and removal of cumulative stopwatch gates hold.

Operator evidence: all15 listed matching containers are exited;13 report exit0
and2 report exit137. Twelve list "2 days ago", three "3 days ago". The first exact
name matches the saved cleanup assertion. This supplied listing establishes no
running container among those matches at the operator observation; it does not
establish provenance, explain137, authorize removal, or prove other resources
absent. It is consistent with old retained containers causing the global-prefix
assertion and does not establish a current-round leak. The out-of-scope discovery
finding and exact-baseline provenance limitations remain separate and preserved.

### Coordination authority and bounded setup

Creation of the first child with parent=W161230 was refused: baton.prompt is not
a resolved handler of baton.ops. No child Work was created by that refused act.
Its prepared dossier is findings/finding-managed-preparation-completion; attach
it to its one Work as the first setup act before implementation or further dossier
work. This is an endpoint-authority constraint, not a Baton defect.

Use the configured baton.codex context for a coordination-only setup claim on
this parent, via baton.feat. This is implementation of the selected split, not
another parent product-development/review cycle. Create four child Works and
their dossiers, add actual dependency gates while eligible for each consumer
route, and route the first prepared child to baton.tune. Future dependent groups
remain canonically blocked. Return the parent to baton.ops with next=baton.ops
after setup; do not edit product/tests or redo the completed progress audit.
See SPLIT-SETUP-2026-09-14.md for exact outcomes, planned owners and stop boundary.


## 2026-09-14T15:39:32Z — four-group coordination setup committed

Parent claim170372 created exactly W170380/W170382/W170385/W170387, each bound
to its selected canonical child record with FINDING/PLAN. Actual authors create
PROGRESS. Dependencies2-on1/3-on2/4-on3 committed170383/170386/170388; umbrella-on4
committed170389. Group2 routes to impl while blocked at170406, groups3/4 remain
blocked on feat. Group1 is handed to tuner only after these dossiers/gates exist.
Independent review is Codex; group3 concrete product selection remains mandatory.

Current PLAN and SPLIT-RECEIPTS-170372.json name exact scopes/IDs and receipts.
No product/test edit, verification/engine/model/image/Git execution, repeated
progress audit or cleanup performed. Parent returns to ops with next ops; all
existing dependent gates, historical acceptance and partial evidence preserved.
No new child outcome or parent completion is claimed. The setup fulfills the
owner-selected split, not the four implementations under one umbrella claim.


### Setup final receipt clarification — 2026-09-14T15:41:06Z

Group1 routed to tuner at170409 and is actively held by baton.tuner at snapshot
170420. Adding umbrella dependency170389 already released the setup claim into
block; an attempted pass correctly refused unclaimed/block. Following the CLI
instruction, reroute170418 moved the umbrella to baton.ops, with existing
Next=baton.ops preserved. This is normal canonical routing, not a workaround or
protocol incident. SPLIT-STATE-170420.json verifies parent handler null and all
three successor blocks. Exact receipts are in SPLIT-RECEIPTS-170372.json. No setup
claim remains held, no further owner operation is required to start group1, and
no parent acceptance or dependent release was performed.

## 2026-09-14T20:45:53Z — owner M172097 selects group2 registration ordering

W170380 is closed satisfying at170651. W170382's partial review170867 identified
that the original slice2 packet ordered creation before capacity registration,
while accepted group1 registers planned capacity first. Slawomir selected the
exact REGISTRATION-ORDER-PROPOSAL-170867.md in the recovery child dossier.
This explicitly supersedes only the original relative order in SLICE2-SCOPE-
165724.md composition steps1–2/restart row and the recovery child's initial
Observable finish; those texts remain historical evidence with supersession.

Register planned capacity, commit immutable intent before child creation, then
ordinary claim/attempt/assignment/admission before start. Registration itself
grants no execution. Four actual crash windows replace the unreachable old cut;
the child FINDING20:45:53Z and current PLAN pin exact owner/effect/reopen proofs.
Keep one root, pending apply, uncertain holds, no duplicate effects and all other
selected recovery/identity/cleanup constraints. Resume Claude only on W170382's
remaining group2 outcome with independent review; no parent implementation,
group2 acceptance, group3 release or new generic-source/engine scope follows.

## 2026-09-14T22:08:03Z — owner M172570 selects group2 late-identity authorization design

Review172443 found a concrete generic-owner boundary: after initially uncertain
failed start, late exact runtime reconciliation conflicts with the unchanged
original failure receipt's None identity. Slawomir selected the recovery child's
LATE-START-RECOVERY-PROPOSAL-172443.md immutable authorization direction and rejected
abandonment substitution. Preserve original failure history and identity mismatch
guards; bind exact failure/start/attempt/assignment/runtime proof and reject
changed/multiple/ambiguous identities. No unproved runtime may be cleaned up.

Next: Claude prepares the concrete generic-owner/API/document/composition/test
scope; Codex independently reviews the design BEFORE implementation. Record the
specific scope amendment against SLICE2-SCOPE-165724.md's generic reuse-only
boundary before implementing it. M172570 selects a bounded correction direction,
not unspecified generic edits. The child FINDING/PLAN22:08:03Z pins sequencing,
acceptance and ownership. W170382 retains its identity and remains incomplete;
groups3/4, W161230 and W156162/W161234/W2 remain gated. No parent development loop,
engine/model run, abandonment policy or acceptance waiver is selected.

## 2026-09-14T22:09:53Z — group2 reassignment

Slawomir requested W170382 be reassigned. baton.prompt selects baton.tuner under
the standing Claude/tuner choice, superseding the prior Claude continuation.
No live claim exists at snapshot172581. Tuner now owns the upcoming bounded
late-identity design/scope preparation, with explicit independent baton.feat
handoff and set-next=baton.tune; implementation follows recorded reviewed scope.
The child FINDING/PLAN22:09:53Z controls. Preserve all earlier authored evidence
and remaining group2/parent gates; no parent implementation or hidden context.

## 2026-09-14T22:18:02Z — manual recovery suffices for initially unknown runtime

Slawomir selected visible reporting and human cleanup for the uncertain-start
case. This explicitly supersedes M172570's automatic late-identity authorization
prerequisite and the child LATE-START-DESIGN-172593.md continuation. Do not review/
implement that extension as a delivery gate. Tuner remains assigned to group2.
Child FINDING/PLAN22:18:02Z requires actionable operator reporting, honest known/
unknown identity, no false success/absence/cleanup or duplicate start, and
preserved unresolved capacity/apply holds across restart. Actual cleanup belongs
to the human. Reuse sufficient existing reporting; generic owners stay reuse-only.
Other group2 requirements remain unchanged, including known-identity cleanup and
partial delivery. Preserve design/probes as history. No parent development loop,
acceptance or dependent release is implied.

## 2026-09-14T22:25:29Z — partial-delivery verification deferred, no protocol work now

Slawomir deferred the discussed unfinished partial-delivery verification/recovery
item and explicitly declined spending time defining its protocol now. A possible
future delivery-specific preamble is not selected design scope. This removes
that unfinished item from W170382's current completion gates; do not create a
new protocol/design/test prerequisite. Child FINDING/PLAN22:25:29Z controls.
Preserve existing integrity checks, accepted evidence and confirmed cleanup fixes;
record deferred coverage honestly. All other selected requirements remain.

## 2026-09-14T22:32:06Z — expanded failure/isolation coverage is v13, not group2 gate

Slawomir reaffirmed "we said those are v13" for discussed item3's expanded
failure/isolation test matrix. This supersedes parent/child full-matrix completion
instructions for adversarial identity/artifact/custody, causal/timeout/limit
permutations and two-Job combinations. Do not expand that campaign or rename it
as focused work to retain a v12 gate. Child FINDING/PLAN22:32:06Z controls.
Preserve existing checks/tests/evidence and classify deferred coverage honestly.
Concrete demonstrated correctness/false-success defects retain the standing
release rule; missing permutations alone are not release blockers. No new v13
execution/backlog duplication, evidence waiver or automatic child closure.

## 2026-09-14T22:33:45Z — shutdown expansion deferred; completion reports reduced scope

Slawomir confirmed the expanded uncertain-ending/leader-first/TERM-resistant
cancellation and cleanup matrix belongs to v13. Child FINDING/PLAN22:33:45Z
supersedes earlier group2 shutdown campaign requirements. Reuse existing evidence
and mechanisms; retain honest reporting and bounded demonstrated false-cleanup/
premature-release corrections. Completion evidence and local documentation cover
retained v12 behavior and explicit deferrals, not the superseded full matrix.
Independent review and owner completion remain; no group2 or parent acceptance.
