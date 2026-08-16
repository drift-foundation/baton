# W92 cutover inventory — resolved from checkpoint 6c3519e678a9f01849c7569d0542e894ed052a3e

Every disposition below is per-dossier and evidence-based; no move or removal
is inferred from a pattern. The append-only review journals inside moved
dossiers are never edited; historical citations of pre-cutover paths inside
markdown bodies remain as written history, exactly as retired trial messages
keep their immutable old-path references.

## A. Relocate to the canonical record layout (19 dossiers)

Target: `work/records/2026/08/<same-slug>/` (every surviving dossier's first
commit falls in 2026-08; the creation month is fixed at birth per the pinned
WS-6 ruling). Moves use `git mv` so history follows; nothing is committed by
the implementer.

Durable design/decision records and open items:

| Dossier | Why it survives |
|---|---|
| finding-recursive-target-graph | THE v11/2.0 design record (umbrella + children incl. this W92 dossier); active; cited by `src/baton_work/__init__.py` |
| finding-human-console | Normative human-console contract; cited by `src/baton_tui/state.py`, `tests/tui/test_tui_render.py`, `tests/tui/test_tui_driver.py`, `tests/packaging/test_docs_consistency.py` |
| finding-protocol-10-umbrella | Live protocol-10 decision provenance and cutover index; cited by `tests/packaging/test_retired_oracle.py` |
| finding-same-second-ordering | Cited by `src/baton_work/authority.py` (the ordering rule v11 replaces) |
| finding-next-release | Active v10 release track; production activation still pending |
| finding-protocol-11-reference-semantics | Queued protocol-11 design |
| finding-codex-app-server-event-bridge | Current event-connectivity work |
| finding-v10-cutover | Authorized 2026-08-13; execution still held for Slawomir |
| finding-reviewer-polling-reliability | Open defect, deferred not resolved |
| finding-runner-connection-handoff | Open transferred defect |
| finding-tui-refresh-stall | Open; root cause pending |
| finding-tui-bulk-select-trash | Deferred to protocol 11; queued |
| finding-tui-markdown-rendering | Deferred; queued |
| finding-message-reactions-voting | Confirmed direction; queued |
| finding-part-name-semantics | Approved, parked on adoption |
| finding-decision-obligations | Protocol-10 design record companion to reactions/voting |
| finding-claim-progress | Not implemented in the current stage; queued |
| finding-orphan-publication-link | Open defect, explicitly not fixed |
| finding-nonempty-message-bodies | Implementation awaiting final review |

## B. Leave in place pending the finding-next-release cleanup audit (6 dossiers)

These are resolved and shipped; their deletion is owned by the
finding-next-release step-2 audit, not by W92. They stay at their old
`work/finding-*` paths as legacy-pending-cleanup and gain no permanence:

- finding-config-regen-wording (docs corrected, signed off, shipped)
- finding-deployment-recipe (tooling signed off, shipped as tools/deploy.py)
- finding-save-message (shipped in 1.1.0)
- finding-tui-message-search (shipped)
- finding-live-first-mailbox-upgrade (v9→v10 migration record; resolved)
- finding-tui-sent-broadcast-missing (closed without correction)

`work/REVIEWER-DELEGATION-OFFER.md` (dated 2026-08-09 coordination note)
likewise stays for that audit.

## C. Remove (1 exact target)

- `work/finding-draft-post-replace-durability/` — an EMPTY untracked
  directory (zero files, created 2026-08-11, never populated). Nothing to
  preserve; `rmdir` only, never recursive.

## D. work/open human index (16 relative symlinks)

One symlink per record with still-open work, friendly name = slug:
recursive-target-graph, next-release, protocol-11-reference-semantics,
codex-app-server-event-bridge, v10-cutover, reviewer-polling-reliability,
runner-connection-handoff, tui-refresh-stall, tui-bulk-select-trash,
tui-markdown-rendering, message-reactions-voting, part-name-semantics,
claim-progress, orphan-publication-link, nonempty-message-bodies,
decision-obligations.

No symlink for the purely-historical records (human-console,
protocol-10-umbrella, same-second-ordering).

## E. Repository references to relocated paths (exact update list)

Permanent source/tests/docs citing a relocated dossier — updated to the
canonical record path:

- `src/baton_work/__init__.py:6` → finding-recursive-target-graph
- `src/baton_work/authority.py:12` → finding-same-second-ordering
- `src/baton_tui/state.py:2001` → finding-human-console
- `tests/tui/test_tui_render.py:2398,2853` → finding-human-console
- `tests/tui/test_tui_driver.py:4338,6848` → finding-human-console
- `tests/packaging/test_retired_oracle.py:13` → finding-protocol-10-umbrella
- `tests/packaging/test_docs_consistency.py:3` → finding-human-console
- `docs/EFFECTIVE-BATON.md` — the worked dossier-path examples move to the
  records layout
- `tests/packaging/test_packaging_isolation.py:484` — placeholder template,
  inspected at update time; changed only if it names a literal path

Living navigation documents inside the umbrella
(FINDING/PLAN/PROGRESS/SAME-SCHEMA-TRIAL-PLAN, never review journals) get
their self-references swept `work/records/2026/08/finding-recursive-target-graph/…` →
`work/records/2026/08/finding-recursive-target-graph/…`.

`docs/RELEASE-1.0.0.md` and all `review-*.md` journals are history and are
not rewritten.

## F. v11 authority state to carry forward

Bindings: NONE exist on any open trial Work (verified via `bindings` per
Work) — nothing to translate.

Still-relevant open Work to recreate in the fresh authority (4):
W3 init hint, W10 priority, W34 short selectors, W78 project
filters.

NOT recreated: W92 (completes at cutover), W11 "cut next v11 trial release"
(superseded by the W92 release itself — flagged for reviewer confirmation),
all closed Work, all trial threads/messages/queue state (retired with the
trial authority, references unrewritten).

Reviewer follow-up (v10 80bbe488, 2026-08-16): additionally recreate the
TUI Work-search request as PARKED (deferred beyond this release); pinned at
findings/finding-tui-work-search/ in the umbrella record — no earlier pin
was found to relocate.

Recreated total: 5 — 4 open + 1 parked. W2 (executable rename,
T2 #125), W4 (single-config roots, T4 #134), W6 (defct label,
T6 #143), W9 (exit confirmation, T9 #150), W12 (detail Work id,
T12 #156), W13 (key=value grammar, T13 #162), W14 (command-bar
assistance, T14 #170), W19 (multiline batch, T19 #180), and W84
(hot-zone blink cue) were implemented pre-cutover and are NOT
recreated — the fresh baton.json is born on the single-config
root model and the fresh CLI/TUI on the ruled compact vocabulary,
exit prompt, id-led detail header, the one key=value operation
grammar, its context-sensitive assistance, the `::` batch buffer,
and the hot-zone cue.

Selected next-schema persisted state (per the umbrella plan): W10
three-level priority and W78 canonical project metadata. (W84's original
timestamp/change-sequence design was superseded by the same-schema
active/review hot-zone cue and is queued as presentation work, not
selected persisted state.)
