# Workflow acceptance tests

Status: reviewer draft for implementer review
Date: 2026-08-14
Owner: `baton.reviewer`

## Purpose

The v11 model must be tested as complete stories, not only as isolated verbs.
Each workflow begins with an initial report or milestone, follows the baton and
its evidence through the actors who actually handle it, and ends in an honest
terminal state. The test asserts the human-visible and agent-visible state at
each handoff: Current, Next, classification/phase, obligations, blockers,
personal New, route resolution, discussion history, and audit sequence.

These workflows consolidate already-confirmed behavior from `FINDING.md`.
They do not silently decide the still-open surfaces listed at the end.

## Workflow-to-regression rule

A workflow is an imaginary but realistic operational story. It is deliberately
broader than a unit test: its purpose is to make several individually plausible
states interact and thereby expose gaps, contradictions, or defects that a
transition tested alone may never reveal.

When a workflow exposes a defect:

1. preserve the failing workflow as the end-to-end acceptance case;
2. identify the exact phase boundary or transition where the first incorrect
   observable state appears;
3. add the smallest focused regression beside that transition; and
4. fix until both the focused regression and the original workflow pass.

The focused regression is the bug target; the workflow is the proof that the
fix works in the operational model that discovered it. Neither replaces the
other. Reducing a failing workflow until it passes would erase the interaction
evidence, while keeping only the workflow would make the defect slow and hard
to localize.

Every extracted regression should name its originating workflow and checkpoint
(for example, `WF-05 step 5: provider close with a second blocker`). The
workflow should name the defect/regression added from it. This creates a
traceable loop from story → observed failure → focused regression → repaired
story.

## Test discipline

1. Drive the workflow through the packaged JSON CLI as separate processes.
   Internal transition tests remain useful, but they are not workflow
   acceptance.
2. Start from one explicit `baton.json`; use configured participants and public
   endpoint kinds. Never seed topology through internal registry calls.
3. At every numbered checkpoint, assert the canonical JSON projection. TUI
   parity tests render selected checkpoints from the same authority; they do
   not duplicate the workflow or parse the screen as an API.
4. Restart between selected acts by closing all clients and opening the next
   command from `--config`. State must be reconstructable without process
   memory.
5. Assert every failed or raced operation leaves no partial rows, no sequence
   hole, and no changed workflow state.
6. Assert endpoint resolution twice:
   - committed history records the route, role, handlers, and config generation
     that applied when the operation occurred;
   - current projection resolves the stable endpoint through the currently
     accepted config.
7. Every workflow ends by checking the ordered audit trail and that no open
   Work lacks exactly one Current endpoint. A terminal Work has neither Current
   nor Next, and every terminal close records exactly `satisfying` or
   `non-satisfying` regardless of graph shape.
8. Run the core workflows from source and from the built artifact. A packaged
   workflow runs with `PYTHONPATH` removed.

Suggested home: `tests/work/workflows/`, with shared process driver and
scenario builders kept separate from the assertions.

## WF-01 — one-team straight-through report

The smallest complete workflow and the vocabulary baseline.

1. `lang.ada` creates a report at `lang.rsrch` with immutable
   `origin=external-report`, `classification=unknown`, and research phase.
2. Research classifies it as a confirmed defect and passes it to `lang.impl`
   with planned Next `lang.rev`. If the public UI offers classify-and-pass as
   one action, the audit still records both state changes explicitly.
3. Implementation posts evidence and passes to the planned `lang.rev`; the
   return consumes Next and audits as `return`.
4. Review records verification and terminally closes with `satisfying`.

Assert: one Current throughout the open lifetime; classification never changes
origin; the planned return is visible until consumed; terminal close has no
fake recipient; ordered route-resolution snapshots match every handoff.

Existing coverage: pass/Next/return and close are covered piecemeal and in the
current gate scenario. WS-1 extension now authorized: exercise public
classification and the explicit `research` to `active` to `review` phases,
including `review` to `active` rework, while proving pass and phase remain
distinct audited changes.

## WF-02 — request information without transferring Work

This pins the difference between `+`, `@`, and `=>`.

1. `push.sl` owns PUSH-1 at `push.rev`.
2. A message with `+lang.bug` raises Lang members' personal attention/New but
   creates no obligation and leaves PUSH-1 Current unchanged.
3. A later message with `@lang.bug` creates exactly one actionable obligation,
   records its resolution snapshot, and still leaves PUSH-1 at `push.rev`.
4. A non-handler Lang member may read and contribute, but that contribution
   does not silently discharge or take over the obligation.
5. Lang explicitly responds or disposes; the obligation leaves actionable
   state. Push continues and closes its own Work.

Assert: visibility, attention, obligation, and ownership are four distinct
states; only explicit response/disposition resolves `@`; only `=>` could move
Current; seen cursors remain personal.

Existing coverage: unit coverage for `+`, `@`, response/disposition, and
personal seen state. Missing: one public-CLI story demonstrating all four
projections together.

## WF-03 — provider rejects or requests more evidence

Not every report becomes provider Work or a promise to fix.

1. A consumer sends `@lang.bug` while retaining its own Current.
2. Lang research either requests more evidence, keeping the obligation/current
   intake leg active, or explicitly rejects/disposes it with an honest reason.
3. A rejection creates no provider defect, dependency edge, or false
   `fixed` result. The consumer decides independently whether to investigate,
   redirect, accept a limitation, or close its own report.

Assert: route intake is not an automatic pipeline; rejection and request-info
are visible dispositions; no silent transfer occurs; terminal state never
claims a fix that did not happen.

WS-2 extension: when Lang instead accepts and creates provider Work, its later
close must carry an explicit satisfying or non-satisfying outcome. Both end
that provider gate, but neither decides the consumer Work. The complete cases
are specified in the WS-2 battery below.

## WF-04 — one consumer, one provider fix

The canonical cross-team happy path.

1. Push creates PUSH-1 and asks `@lang.bug`; Push retains Current.
2. Lang accepts intake, creates LANG-42, explicitly links
   `PUSH-1 blocked_by LANG-42`, and responds with the provider Work id.
3. Lang moves LANG-42 through research → review → implementation → review,
   including a planned return.
4. Reviewer closes LANG-42 with an explicit satisfying provider outcome.
5. PUSH-1 becomes ready, Push verifies its side, and independently closes with
   `satisfying`.

Assert: the response obligation and dependency edge are distinct; only the
edge gates readiness; both Works keep independent Current endpoints; the link
is traversable from either side; provider close is not addressed back to one
author; Push resumes because its blocker changed state.

Existing coverage: most acts exist in `test_the_gate_scenario_end_to_end`.
Extend it with classification/phase, C4 structured endpoints, reverse
drill-through, consumer terminal close, and packaged parity.

## WF-05 — three consumers converge on one provider Work

The central cross-team dependency-web acceptance test.

1. Push, Web, and MariaDB independently create local reports and discussions;
   each routes an exact request through `@lang.bug`.
2. Lang relates all three incoming discussions to one provider-local LANG-42
   context and creates three explicit `consumer blocked_by LANG-42` edges.
   The labels are context only; adding/removing them alone changes no readiness.
3. Provider view shows fan-in three. Consumer default tables and personal New
   remain noise-scoped, but deliberate link traversal/browse may reveal the
   other linked Works because this is not a security boundary.
4. MariaDB also depends on an unrelated BUILD-7 blocker.
5. Closing LANG-42 with an explicit provider outcome queues Push and Web for
   their own decisions; MariaDB remains waiting on BUILD-7.
6. Later contradictory evidence creates new provider Work linked by
   `follow_up_of`. Only consumers given new explicit `blocked_by` edges become
   blocked; the closed LANG-42 and its old consumers are never reopened or
   silently re-blocked.

Assert: N:1 convergence, exact edge count, labels never gate, one-to-N terminal
outcome fan-out, multiple-blocker conjunction, default-view noise boundary,
open graph navigation, immutable closure, and no single return recipient on
provider closure.

Existing coverage: low-level graph/readiness in `test_edges.py`; partial JSON
drill coverage. Missing: three independent public report/intake conversations,
label-versus-edge proof, default/noise plus deliberate-open traversal in one
packaged workflow.

## WF-06 — recursive release with children and external blockers

This composes containment and dependency rather than treating them as separate
features.

1. Create a release/milestone root with two child Works.
2. One child follows WF-01 locally; the other is blocked by external provider
   Work following WF-04.
3. Closing the root while either child is open refuses and names the children.
4. Closing a child alone does not make the root ready while the external
   blocker remains; closing the blocker and final child does.
5. Later work is represented by a new child or provider follow-up and an
   explicit new edge; a terminal child or blocker is never reopened.
6. Personal New equals root-local unseen messages plus the recursively
   aggregated child counts, deduplicating any multiply related discussion.

Assert: union-graph cycle refusal, breadcrumb/drill determinism, readiness as
the conjunction of children and blockers, and member-relative New roll-up.

Existing coverage: containment, union cycles, readiness conjunction,
breadcrumbs, and New decomposition are separate unit tests. Missing: complete
public workflow and multiply tagged discussion deduplication.

## WF-07 — announcement without a notice object

1. Baton creates an operations Work/discussion and publishes an ordinary
   message with `+*.*`.
2. Every matching member receives attention/New exactly once even when that
   member handles several matching endpoints.
3. No obligation is created, no Work Current moves, and nobody must react.
4. One member marks it seen; only that member's New changes.
5. Multi-destination or expanding wildcard `@` and `=>` forms refuse; a future
   bulk required-response operation would have to expose separate obligations.

Assert: there is no notice/broadcast authority object; exact selector expansion
is audited; fan-out deduplicates by member/message; attention is not
responsibility.

Existing coverage: wildcard `+`, cardinality refusal, and personal seen state
exist as unit tests. Missing: all-participant packaged workflow and confirmation
that no standalone notice surface appears.

## WF-08 — handler reassignment while work is live

This is the C4 history-versus-current acceptance scenario.

1. Under config generation 1, `@lang.bug` resolves through route `intake`, role
   `rsrch`, handler `ada`; create an obligation and a provider Current using it.
2. Accept generation 2, reassigning the same live route to handler `grace`
   under a coherent role assignment.
3. Historical events/obligation resolution still name generation 1 and `ada`.
4. Current Work/obligation projections name the stable endpoint and resolve
   current accountability to generation 2 and `grace`.
5. Grace responds/passes; the new event records generation 2. Nothing rewrites
   the earlier operation.

Assert: endpoint identity is stable, resolution snapshots are immutable,
current handler lookup changes, obligations are owed by endpoint rather than
person, and config acceptance is the only reassignment path.

This workflow is immediate C4 acceptance material.

## WF-09 — restart and concurrent completion safety

Run a shortened WF-04 with every act in a fresh process. At two points, race
legal competing terminal actions:

- two members try to respond/dispose the same obligation;
- pass and terminal close race on the same Work.

Assert: exactly one compatible transition commits; the loser receives a
structured refusal; sequence remains dense; restart reconstructs Current,
Next, blockers, obligations, personal New, and audit history; no open Work is
left without Current and no terminal Work retains Current/Next.

Open dependency: client-supplied operation-id/effectively-once retry is claimed
by the implementation plan but is not exposed by the current CLI. Retry
semantics need their own ruling or implementation before that part is added.

## Cross-surface acceptance matrix

| Workflow | JSON subprocess | Built artifact | TUI checkpoint parity | Race/failure |
| --- | --- | --- | --- | --- |
| WF-01 local lifecycle | required | required | home/detail/discussion | invalid pass/close |
| WF-02 request, no transfer | required | required | New + actionable | double disposition |
| WF-03 reject/evidence | required | required | status/disposition | invalid transition |
| WF-04 one provider | required | required | Current/Next/links | restart checkpoints |
| WF-05 convergence | required | required | fan-in + blockers | follow-up/relink |
| WF-06 recursive release | required | required | breadcrumb/New | union cycle |
| WF-07 announcement | required | required | per-member New | selector refusal |
| WF-08 reroute live work | required | required | current handler detail | generation race |
| WF-09 restart/race | required | required | final invariant only | primary subject |

## Coverage gaps exposed by the workflows

The present Gate A/C1–C3 implementation does not yet expose every confirmed
product behavior needed by these workflows:

- Discussion is still represented as messages directly attached to Work;
  first-class reusable discussions and many-to-many `#WORK` labels are absent.
- Public classification and operational-phase transitions are absent.
- Satisfying versus non-satisfying provider outcomes and staged verification
  are specified below but are not yet implemented.
- Atomic provider deduplication (discussion relation plus explicit dependency
  edge) has no public operation.
- Dossier/path/artifact/revision binding and restart reconstruction from the
  Git folder are separately deferred and should become another workflow once
  specified.
- Client operation ids/effectively-once retry are not on the current CLI.

Those gaps must be scheduled or explicitly deferred before the workflow suite
can be called complete. Existing narrow tests are evidence for components; they
do not substitute for the end-to-end workflows above.

### WS-1 authorized phase/classification matrix

Extend WF-01 and WF-04, then add focused regressions that prove:

- creation defaults to `classification=unknown`, `phase=queued`, while an
  explicit valid initial phase is preserved;
- Current-route handlers may classify/change phase, while non-handlers and
  other teams are refused without mutation; accepted handler reassignment
  changes who may perform the next transition;
- every canonical phase and classification round-trips through JSON/audit,
  with `unkwn`, `queue`, `rsrch`, `wait`, `actve`, `rview`, and `park` kept as
  presentation-only compact values;
- ordinary open-phase transitions permit review/rework cycles, pass never
  silently changes phase, and closed Work refuses phase mutation;
- dependency-backed waiting requires at least one open required gate, wakes
  only after all required children and `blocked_by` Work close, and commits one
  atomic `waiting` to `queued` plus `wake` event at the last gate;
- obligation-backed waiting names one exact pending `@` obligation and wakes
  once when it completes, without treating the obligation as a dependency or
  granting its respondent workflow mutation authority;
- races and retries around the last dependency/obligation completion cannot
  lose or duplicate wake, and already-satisfied wait conditions are refused;
- parking requires a reason, retains Current, never auto-wakes, leaves only by
  explicit `parked` to `queued`, and updates the always-visible parked count in
  equivalent JSON and bounded TUI summary projections.

## WS-2 workflow battery — immutable closure and staged verification

These stories supersede every reopen step in the earlier workflows. They are
the end-to-end acceptance boundary for WS-2. Each numbered act is a packaged
JSON-CLI subprocess and each checkpoint reads one canonical snapshot. Selected
acts restart every client. The focused regressions that follow use the narrowest
authority boundary that can prove the same rule.

Canonical verifier observations are `passed`, `failed`, and `unable`.
Canonical provider assessments are `accepted`, `rejected`, and
`inconclusive`. `withdrawn` is a terminal assignment state that contains no
feedback. Round progress is always `reported/assigned`; withdrawal is shown
separately and never increments the numerator.

### WS2-WF-01 — one candidate, one verifier, satisfying close

1. Push owns PUSH-1, which is waiting on provider Work LANG-42.
2. Lang's Current reviewer publishes candidate `driftc-A` and creates round 1
   with one exact assignment to `@push.verify`.
3. Assert LANG-42 remains open, PUSH-1 remains blocked, the assignment is
   actionable for the live Push verifier, and the round reads `0/1`.
4. Push reports `passed` with evidence. Assert the immutable raw report,
   `1/1`, no dependency or Work transition, and no automatic assessment.
5. Lang records `accepted` with rationale. Assert this is a separate audit act
   and still changes no workflow state.
6. Lang closes LANG-42 with explicit `satisfying`, naming the round and
   rationale. Assert PUSH-1 changes `waiting` to `queued` only if this was its
   last gate; its Current, classification, and open status remain unchanged.
7. Push independently verifies its own Work and closes it.

### WS2-WF-02 — three mixed reports and reviewer adjudication

1. LANG-42 round 1 selects exact routes in Push, Web, and MariaDB; assert
   three independent assignments and `0/3`.
2. Push reports `passed`; Lang accepts it. Assert `1/3`.
3. Web reports `failed`; Lang rejects that report as a consumer configuration
   error. Assert the projection says `failed / rejected` with both rationales
   and reads `2/3`, never two approvals.
4. MariaDB reports `unable`; Lang leaves it `inconclusive`. Assert `3/3` and
   all three raw reports remain immutable.
5. Lang may explicitly continue work or close with either provider outcome;
   no count, observation, or assessment chooses the branch automatically.
6. Lang supersedes its assessment of Web with a new `accepted` act. Assert the
   prior assessment and raw `failed` report remain in audit history.

### WS2-WF-03 — due review, silence, extension, and withdrawal

1. Create a three-route round with `review_at=T`; assert `0/3`, zero withdrawn,
   and not due before T.
2. At T, assert one due review event for the responsible provider endpoint.
   Work, phase, Current, candidate, dependencies, and assignments are unchanged.
3. Restart and reread after T. Assert the round remains due without a duplicate
   notification or any automatic decision.
4. The reviewer extends the same candidate to T2. Assert the extension is an
   audit act, the due condition clears, and all reports/pending assignments are
   retained.
5. One team reports `passed`; the reviewer closes satisfying before T2 based
   on that report plus elapsed exposure.
6. Assert final progress remains `1/3`, the two pending assignments become
   `withdrawn`, `withdrawn_count=2`, both routes are notified, and neither
   withdrawal is presented as feedback.
7. Repeat the close branch at `0/3` in a separate fixture to prove silence may
   inform a human decision but can never impersonate a report.

### WS2-WF-04 — failed candidate and a replacement round

1. Create LANG-42 in `research`, explicitly move it to `active` while producing
   candidate `driftc-A`, then explicitly move it to `review` for independent
   evaluation. Push reports `failed`; Lang assesses it `accepted` as relevant
   evidence.
2. Assert LANG-42 remains open, remains in `review`, and its dependency remains
   unsatisfied. Neither the report nor assessment changes phase or Current.
3. Lang explicitly returns `review -> active` for rework. This is ordinary
   iteration within the same Work, not reopen, follow-up, or a new state.
4. Publish different candidate `driftc-B`, then explicitly return
   `active -> review`. Assert this creates round 2;
   candidate identity is immutable inside round 1 and its report does not
   carry into round 2's `0/N`.
5. Pending round-1 assignments are explicitly withdrawn and notified. Both
   rounds remain ordered audit evidence.
6. Complete round 2 and close explicitly from `review`; only this close ends
   the provider gate. Pin the ordered phase history
   `research -> active -> review -> active -> review`, and run the complete
   story through both source and packaged CLI/JSON.

### WS2-WF-05 — non-satisfying close returns the decision to consumers

1. Push and Web wait only on LANG-42; MariaDB waits on LANG-42 and BUILD-7.
2. Lang closes LANG-42 with explicit `non-satisfying` and rationale.
3. Assert Push and Web become `queued`; MariaDB remains `waiting`; all three
   retain their Current endpoint and classification.
4. Assert each consumer projection makes the non-satisfying result visible and
   actionable but never says fixed, verified, or resolved.
5. Each consumer independently chooses to work around, redirect, add evidence,
   or close honestly. Provider close addresses no single return recipient.

### WS2-WF-06 — immutable close, later contradiction, selective follow-up

1. LANG-42 satisfies three consumers and closes. Record all resulting wake
   events and consumer states.
2. A later Push test contradicts the result. Every public attempt to reopen or
   mutate LANG-42 refuses without changing bytes, sequence, or dependents.
3. Lang creates LANG-57 with `follow_up_of=LANG-42`; assert the relationship is
   navigable but non-gating.
4. Add a new `PUSH-1 blocked_by LANG-57` edge. Assert Push is gated according
   to its live phase, while Web and MariaDB are not silently re-blocked.
5. If Web later proves affected, add its own explicit edge. Closing LANG-57
   fans out only across those new edges. Old LANG-42 history is unchanged.

### WS2-WF-07 — shared provider, selected verifier subset

1. Five consumer Works depend on LANG-42, but Lang selects only Push and Web
   for staged verification.
2. Assert the round total is two, not five; only the exact selected route
   handlers receive actionable assignments.
3. Contributions from other configured participants remain readable evidence
   but neither complete an assignment nor affect the counter.
4. Reviewer closes after the selected evidence. The explicit provider outcome
   fans out through all five dependency edges, while round reports remain
   exactly the selected two teams' evidence.

### WS2-WF-08 — abandon a round without closing Work

1. Create a candidate round with one reported and two pending assignments.
2. The provider reviewer abandons the round while keeping LANG-42 open.
3. Assert `1/3`, two withdrawals, route notifications, immutable candidate and
   report history, and no provider/consumer lifecycle change.
4. Late responses to either withdrawn assignment refuse. A later candidate
   requires a new round and new assignments.

## WS-2 focused regression matrix

Every row below is mandatory. Where a workflow is named, the narrow regression
must cite that workflow and checkpoint.

| Area | Focused assertions |
| --- | --- |
| Authorization | Only a live Current handler may create, extend, or abandon a round, assess feedback, resume provider work, or close. Only the live exact assignment-route handler may report. A reporter cannot assess or close merely because it participated. Accepted route reassignment changes future authority without rewriting historical resolution snapshots. |
| Exact cardinality | One assignment names one exact endpoint. Wildcard or comma-expanded `@` refuses. Duplicate route selection within one round refuses or canonicalizes before commit; it never creates two obligations for one endpoint. |
| Candidate pinning | Candidate/artifact identity is required and immutable per round. Any candidate change requires a new round. Report evidence is pinned to its assignment, round, and candidate. |
| Assignment states | The only terminal paths are pending to reported with `passed`, `failed`, or `unable`, and pending to `withdrawn`. A second report, report after withdrawal, repeated withdrawal, or mutation of raw evidence refuses without partial state. |
| Assessment history | `accepted`, `rejected`, and `inconclusive` never alter raw observation. Reassessment appends a superseding act with actor and rationale; history remains ordered and projections identify the effective assessment. |
| Counters | Numerator counts reported assignments regardless of observation or assessment. Withdrawals never increment it. Projection separately exposes assigned, reported, pending, and withdrawn counts and remains internally consistent after every act. |
| Due time | Before/at/after `review_at` boundaries are deterministic. Due is derived and actionable, not a workflow transition. One deadline generation produces at most one notification across reads and restart; extension records a new generation/deadline. Clock-zone rendering cannot alter stored ordering. |
| Reviewer discretion | `0/N`, partial, and complete feedback all permit—but never cause—an authorized explicit extend, resume, abandon, satisfying-close, or non-satisfying-close decision with rationale. |
| Terminal outcome | Every Work close names exactly `satisfying` or `non-satisfying`, independent of graph shape, classification, prose, or verification history; omission and unknown values refuse. Either outcome ends every gate served by that Work but never mutates a consumer's Current, classification, or terminal status. Last-gate wake and multiple-gate preservation match WS-1 rules. |
| Immutable close | No reopen command, transition advertisement, authority method, or accepted schema value remains. Closed Work rejects new rounds, assignments, assessment, phase, pass, and dependency mutation except creation of a separate follow-up relationship from new Work. |
| Follow-up | `follow_up_of` is non-gating and preserves closed history. A new `blocked_by` may target only open Work; an affected consumer gates on separately created open follow-up Work. Cycle and duplicate-edge rules apply to the new edge; unrelated old consumers remain unchanged. |
| Atomic close | Every close outcome, all pending carried-`@` withdrawals and route visibility, pending verification-assignment withdrawals, dependency results, last-gate wakes, and audit sequence commit together. Answer/dispose/report versus close yields exactly one legal terminal assignment state. Fault injection at each write boundary proves all-or-nothing rollback and dense sequence. |
| Live dependents | Active projections expose `DEP` as the count of open Work currently depending on this Work; drilling it lists that same live set. Consumer close removes it from `DEP` but never mutates provider Work. Historical edges and the acts explaining count changes remain journal evidence; no total/historical counter enters the active table. |
| Races | Serialize report versus withdrawal, extension versus close, assessment versus close, two provider closes, two reports, and new-round versus old-round abandonment. Exactly one compatible result commits; losers get structured refusals and cannot duplicate wake, due, or notification events. |
| Restart/retry | Restart reconstructs rounds, candidates, deadlines, reports, assessments, withdrawals, effective provider outcomes, follow-up links, and actionable endpoints. Retrying a completed operation never duplicates effects; if operation identifiers remain unavailable, the public retry limitation is stated and tested at the supported boundary. |
| Configuration generations | Open assignments retain committed endpoint/config snapshots while current accountability resolves through the accepted generation. Removing or reassigning a handler cannot make history ambiguous; authorization follows the live coherent config or refuses visibly. |
| JSON/projection | Canonical JSON exposes round id/order, candidate, due state, `reported/assigned`, all four counts, per-assignment route/state/raw evidence/effective assessment, reviewer rationale, provider result, withdrawals, and links at one `snapshot_seq`. Reads are pure and deterministic. |
| TUI parity boundary | The bounded renderer uses the same snapshot and may compact labels only through an explicit mapping. It must distinguish due, pending, reported, and withdrawn and show raw result separately from assessment. Full navigation remains a later TUI gate. |
| Audit | Dense ordered acts preserve actor, endpoint resolution snapshot, config generation, exact candidate, selected verifier set, evidence references, timestamps, extensions, supersessions, rationale, explicit outcome, and withdrawals. No free text substitutes for a canonical state. |

## WS-2 execution and stop gate

Implement in three reviewable groups:

1. immutable close, explicit provider outcomes, follow-up links, dependency
   propagation, and removal of every reopen surface;
2. candidate rounds, exact assignments, reports, assessments, counters,
   abandon/withdraw, and canonical JSON; then
3. due review, notifications, extension, transaction-fault injection, races,
   restart, packaged workflows, and bounded renderer parity.

Each group adds its focused regressions before or with authority changes, then
runs the affected workflow stories. The final gate runs every WS-1 and WS-2
workflow from source and built artifacts plus `just test-v11`. Stop for review
after the complete battery passes; heavy TUI navigation, migration, deployment,
and unrelated C5/C6 work remain outside WS-2.
