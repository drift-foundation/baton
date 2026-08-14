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
   nor Next.
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
4. Review records verification and terminally closes `fixed`.

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

Open dependency: exact classification/phase/disposition enums and how a
non-satisfying provider outcome affects a consumer dependency still require a
specific ruling before every branch can become an executable assertion.

## WF-04 — one consumer, one provider fix

The canonical cross-team happy path.

1. Push creates PUSH-1 and asks `@lang.bug`; Push retains Current.
2. Lang accepts intake, creates LANG-42, explicitly links
   `PUSH-1 blocked_by LANG-42`, and responds with the provider Work id.
3. Lang moves LANG-42 through research → review → implementation → review,
   including a planned return.
4. Reviewer closes LANG-42 as fixed and verified.
5. PUSH-1 becomes ready, Push verifies its side, and closes independently.

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
5. Closing LANG-42 unblocks Push and Web; MariaDB remains blocked by BUILD-7.
6. Reopening LANG-42 re-blocks every still-open dependent; re-closing
   recomputes again without inverse-path bookkeeping.

Assert: N:1 convergence, exact edge count, labels never gate, level-triggered
fan-out, multiple-blocker conjunction, default-view noise boundary, open graph
navigation, and no single return recipient on provider closure.

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
5. Reopening a child or blocker makes the root not ready again.
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
| WF-05 convergence | required | required | fan-in + blockers | reopen/reclose |
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
- Satisfying versus non-satisfying dependency dispositions are not yet
  distinguished precisely enough for WF-03.
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
