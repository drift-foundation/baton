# Workflow coverage and implementation pass

Status: implementer pass over the reviewer's `WORKFLOW-TESTS.md` draft
Date: 2026-08-14
Owner: `baton.implementer`
Authorization: reviewer message `37c339edbafea3c6a1f06aefc3659314`
(C4 accepted; workflow-story CLI/JSON phase released)

## Legend

- **EXECUTABLE** — the step runs today through the public CLI/JSON surface
  (packaged or source, separate processes, config-seeded topology).
- **NEEDS-OPERATION** — the confirmed model covers the behavior but no
  engine/CLI/JSON operation exposes it yet. Sequenced below as a work slice;
  not implemented in this phase (serial discipline: surface growth is its own
  reviewed step).
- **NEEDS-RULING** — the behavior is not yet confirmed precisely enough to
  encode as an assertion; listed for the reviewer, never decided here.

The workflow gate implements every EXECUTABLE step as checkpoint assertions in
`tests/work/workflows/`; each test file's docstring names the steps it omits
and the slice or ruling that unblocks them.

## Per-workflow disposition

### WF-01 — one-team straight-through report

| Step | Disposition |
| --- | --- |
| 1 create at `lang.rsrch`, immutable origin | EXECUTABLE — except `classification=unknown`: the engine holds classification NULL until set and the CLI does not expose `--classification`; surfacing the initial value is WS-1 |
| 2 classify as confirmed defect + pass with planned Next | pass/Next EXECUTABLE; the public classification transition is NEEDS-OPERATION (WS-1). The enum already exists in the engine (`CLASSIFICATIONS`); whether the unset state is spelled `unknown` or `null` on the surface is a small vocabulary confirmation inside WS-1 |
| 3 evidence + pass to planned `lang.rev`, audited `return` | EXECUTABLE |
| 4 review closes `fixed` terminally | EXECUTABLE |

Gate: `test_wf01.py`. Asserts one Current at every checkpoint, Next visible
until consumed, `return` audit kind, terminal close with neither Current nor
Next and no recipient, per-handoff resolution snapshots in event order, origin
byte-stable across the whole story.

### WF-02 — request information without transferring Work

All five steps EXECUTABLE. Gate: `test_wf02.py`. Asserts the four distinct
states side by side — visibility (participation), attention (personal New),
obligation (actionable set), ownership (Current) — plus: `+` raises New with
no obligation, `@` creates exactly one obligation without moving Current, a
non-handler contribution does not discharge it, only explicit respond ends it,
seen cursors stay personal.

### WF-03 — provider rejects or requests more evidence

| Step | Disposition |
| --- | --- |
| 1 consumer `@lang.bug`, retains Current | EXECUTABLE |
| 2 request-more-evidence keeping the obligation active | EXECUTABLE as an ordinary contribution message while the obligation stays pending; a first-class "request info" disposition state is part of the NEEDS-RULING enum below |
| 3 rejection: no provider work, no edge, no false `fixed`; consumer decides independently | EXECUTABLE via `dispose` with an honest free-text disposition |
| exact classification/phase/disposition enums; effect of a non-satisfying provider outcome on a consumer dependency | NEEDS-RULING (WS-2) — already flagged as an open dependency in the reviewer draft; confirmed from the implementation side: nothing in the current engine distinguishes satisfying from non-satisfying dispositions |

Gate: `test_wf03.py` covers the executable spine (request, keep-alive
contribution, honest rejection, independent consumer close, no provider
artifacts anywhere). Branch matrix deferred to WS-2.

### WF-04 — one consumer, one provider fix

All steps EXECUTABLE except the classify leg of step 3 (WS-1, same as WF-01).
Gate: `test_wf04.py`. Extends the old gate scenario as the draft asks:
obligation and edge asserted as distinct records, only the edge gates
readiness, C4 structured endpoints at every checkpoint, drill-through from
both sides, provider close addressed to nobody, consumer verifies and closes
independently.

### WF-05 — three consumers converge on one provider Work

All steps EXECUTABLE except the label-versus-edge proof: there is no label
surface at all yet (first-class discussions and `#WORK` labels are WS-4), so
"labels never gate" cannot be stated positively. Gate: `test_wf05.py`. Three
independent public intake conversations, one provider record, exact fan-in of
three, second-blocker conjunction (BUILD-7), level-triggered close → reopen →
re-close with no inverse-path bookkeeping, noise-scoped default views next to
deliberate open-graph traversal.

### WF-06 — recursive release with children and external blockers

All steps EXECUTABLE except multiply-related discussion deduplication (needs
first-class discussions, WS-4). Gate: `test_wf06.py`. Root refusing closure by
naming its open children, readiness as the conjunction of children and
blockers, reopen flipping the root back, member-relative New decomposing
exactly (own + children), union-graph cycle refusal exercised through the
public CLI.

### WF-07 — announcement without a notice object

All steps EXECUTABLE. Gate: `test_wf07.py`. `+*.*` reaching every member
exactly once (a member handling several endpoints still counts one message),
zero obligations anywhere, Current unmoved, one member's mark-seen changing
only that member's New, wildcard/comma `@` and `=>` refused, the exact
expansion audited in the event, and no notice verb or notice object anywhere
on the surface (the refusal changes no authority byte).

### WF-08 — handler reassignment while work is live

All steps EXECUTABLE, including step 5 via a pass (the draft's "responds/
passes"): a generation-2 pass records a generation-2 snapshot. Verified
against the C4 surface before writing the gate: the obligation ROW and events
keep the generation-1 snapshot; the obligations/detail PROJECTIONS resolve
`owed_by`/`current` live through the accepted generation — the draft's
step-3/step-4 split is exactly what the implementation does, no contradiction.
Gate: `test_wf08.py`, with the route actually named `intake` and the
`ada → grace` reassignment done by `regen` through the CLI.

### WF-09 — restart and concurrent completion safety

| Step | Disposition |
| --- | --- |
| every act in a fresh process | EXECUTABLE (each CLI call is a process; no client state exists to leak) |
| two members race respond/dispose on one obligation | EXECUTABLE — truly concurrent processes; exactly one commits, the loser gets a structured JSON refusal |
| pass races terminal close | EXECUTABLE with one caveat stated in the test: both orders are individually legal (pass-then-close commits both; close-then-pass refuses the pass), so the assertion is serialization-consistency — the committed history equals one of the two legal serials, losers get structured refusals, never a merged or partial state |
| refusals leave no partial rows / no sequence hole | EXECUTABLE (event count and density asserted around every refusal) |
| restart reconstructs everything | EXECUTABLE (final checkpoint re-reads all state from `--config` alone) |
| client operation ids / effectively-once retry | NEEDS-RULING then NEEDS-OPERATION (WS-5): the plan claims it, the CLI does not expose it — confirmed absent |

Gate: `test_wf09.py`.

### Cross-surface matrix

JSON-subprocess and built-artifact columns: implemented — every workflow runs
in both modes (source tree via `-m baton_work.cli`, and the zipapp artifact
with `PYTHONPATH` stripped). TUI-checkpoint-parity column: DEFERRED to the
C5/C6 window by the authorization ("do not start heavy TUI work"); the small
existing TUI guards remain as they are. Race/failure column: implemented
inside the workflow files per the matrix rows.

## Sequenced missing slices

Ordered by dependency and value; each is a separate reviewed step, none is
started in this phase.

1. **WS-1 — public classification (and phase vocabulary).** Engine transition
   `classify` (enum already fixed), event kind, CLI verb + `--classification`
   on create, projection field already carried. Unblocks WF-01.2 and WF-04.3
   fully. Smallest slice; one vocabulary confirmation (surface spelling of the
   unset state) inside it.
2. **WS-2 — disposition semantics ruling.** Satisfying vs non-satisfying
   obligation/close dispositions and their effect (if any) on consumer
   dependencies. Pure ruling first; WF-03's branch matrix follows it.
3. **WS-3 — atomic provider deduplication.** One public operation that relates
   an incoming discussion and creates the dependency edge atomically (WF-04/
   WF-05 currently do it in two steps, which is honest but not atomic).
   Needs a small shape ruling, then engine+CLI.
4. **WS-4 — first-class discussions and `#WORK` labels.** Largest slice;
   unblocks WF-05's label-versus-edge proof and WF-06's multiply-related
   dedup. Needs its own design/ruling round.
5. **WS-5 — client operation ids / effectively-once retry.** Ruling on retry
   semantics, then CLI surface; completes WF-09.
6. **WS-6 — dossier/path/artifact/revision binding.** Separately deferred by
   the draft; becomes its own workflow once specified.

## Contradictions found

None. The one candidate — WF-08's historical-row versus live-projection split
for `owed_by` — was checked against the C4 implementation and the draft
describes exactly what the code does.
