# Revised next-phase proposal: build/test baseline, Gate B TUI completion, parallel v11 trial

In reply to review `b0cff20aa8193280de6f5e5ca23ccd43` (claim
`693cc4420fe42b6c96e452859f9bbb11`). The cutover-readiness proposal is
withdrawn as premature; this revision follows the hold exactly. No
implementation begins before disposition.

## Why Gate B is now unblocked

The 2026-08-14 ruling blocked substantial TUI work until the approved
operational stories pass through the CLI/JSON machine surface. That
condition is met: WF-01–WF-15 (plus the WS-2/3/4 batteries) run green
source+packaged on the accepted WS-6 tree. Gate B's B1–B3 checkboxes
and the confirmed TUI direction are the remaining unfinished work, and
TUI/JSON parity is a release gate. The old Gate B "BLOCKED ON
SLAWOMIR" viewer-validation item is already superseded by the ruled
`--config`/`--participant` boundary (C-series); no residue of it
remains open.

## Phase 1 — full build/test baseline (small, evidence-only)

Objective: prove the committed `9c799f4` tree builds every product
and passes the COMPLETE test tree, not only the v11 gate.
Scope: run the full build tooling (zipapp, TUI build, release
snapshot with the tmpl asset) into temp targets; run the entire
pytest tree (core, packaging, tui, work) plus `just test-v11`;
report exact counts and artifact digests. No source changes except
fixes to anything the full sweep exposes (each with a regression).
Review gate: the evidence report; stop.

## Phase 2 — bounded TUI completion (Gate B B1–B3)

Objective: complete the confirmed objective-first TUI on the
canonical projection, with parity as the release gate.

Scope (in), per the confirmed direction:
- B1: the top-level objectives table with the ruled borderless
  fixed-width columns (status, title, recursive required-work
  progress, blocker summary, next actor, last update, the
  participant-relative `Unans.` obligation counter); drill-down
  tables of immediate children repeating at every depth; the
  persistent ancestry breadcrumb; the focused target view exposing
  acceptance/owner/next actor/binding/remaining gates, blockers on
  demand, and collapsed resolved branches; discussion opens within
  the selected target. All through the versioned projection — no
  direct authority reads; refuse-before-curses stays; 6/6 handles
  never ambiguously truncated. Real-PTY tests for every behavior.
- B2: ONE shared fixture driven through JSON and TUI with semantic
  parity asserted for rows, counts, drill links, and actionable
  state — extending the existing parity suite from its current spot
  checks to the full fixture.
- B3: the ruled scenario driven through the packaged artifact's TUI
  (real PTY against the zipapp), not the source tree.
- Discipline: any missing semantic state or product contradiction
  found while rendering returns for ruling before the shared
  projection contract changes; break-sweeps for every new guard.

Scope (out): protocol/authority changes; cutover; production
anything.

Review gate: focused TUI + parity suites and the full v11 gate
green, source+packaged; real-PTY evidence in the response; stop.

## Phase 3 — parallel v11 trial (after Phase 2 acceptance)

Objective: a real coordination trial on v11 beside live v10, per the
pinned parallel-trial boundary — separate config, database,
processes, and runtime paths; nothing may touch, lock, or stop v10.
Scope: stand up the trial coordination home at a Slawomir-named
explicit path via the public `init`/edit/`activate` story; bootstrap
a named project root; run the agreed trial workflow(s) end-to-end
through CLI, JSON, and TUI; deliver a trial report (what worked,
friction, defects — each defect becoming ordinary reviewed work).
Explicitly NOT cutover, migration, or v10 shutdown.

## Slawomir decisions / blockers

- T1: pane layout and narrow-terminal interaction were left open by
  the ruling — rule them now, or accept implementer prototypes at
  the Phase 2 review?
- T2: same question for column widths, sorting, key bindings, and
  detail-pane behavior (ruled "prototype questions").
- T3: for Phase 3 — the trial's coordination-home path, project
  root(s), participant roster, and which real workflow(s) to run.
- No other blocker: Phases 1–2 need no new ruling to start.

Holding for reviewer disposition; production operations remain held
for Slawomir.
