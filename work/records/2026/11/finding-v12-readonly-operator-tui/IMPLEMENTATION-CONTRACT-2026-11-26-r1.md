# W386308 — read-only TUI, first slice: implementation contract, revision 1

Revision 1, 2026-11-26, by K (`baton.prompt`, Fable 5.2). Supersedes IMPLEMENTATION-CONTRACT-PROPOSED-2026-11-26.md, which is kept unchanged. It records the owner's two decisions of 2026-11-26 and the pseudo-terminal findings. Preparation only: no product edit, no claim, no launch packet. The baseline commit does not exist yet, so none is pinned. Facts below were read from the tree at `76b2f2b2` and from rendering the retained A1 extract (`../finding-v12-shared-work-liveness/evidence/headline-386262/a1-public-extract.json`) through the current read model. Items marked *proposed* are mine and need the owner's or the implementer's agreement.

## Outcome

One terminal program that shows, for one instance, a compact list of Jobs and, for a selected Job, its phases. It refreshes in place, keeps the selection, says when what it shows is stale or unreadable, and exits without touching execution. It adds no new source of truth and no new words.

## What it is built on (existing, unchanged)

| Piece | Where | Used for |
| --- | --- | --- |
| Published snapshot `job-status/9` and `/10` | the instance's status file, as `monitor` reads it | the only input |
| `JobViewer.refresh`, `read_snapshot`, `Snapshot` | `tools/job_viewer.py` | bounded read, last-good retention, DISCONNECTED state, 4 MiB bound |
| `job_view(document, job)` | `tools/job_observation.py` | every word shown: `labelled_headline`, `headline_reason`, `summary`, and per phase `role`, `position`, `reason`, `facts`, `duration`, `timeout`, `activity`, `operation`, `attempt_id`, `model_attribution` |
| `STALE_SECONDS` (15 s), `Snapshot.stale`, observation and read ages | same | freshness |

Rules that follow from DESIGN OBS-1 and OBS-2:

- The TUI calls only these. It opens the status file read-only and nothing else: no store, engine, network, child process, log or cache file.
- It never edits or re-derives a headline, reason or state. A value the read model gives as `unknown` is shown as `unknown`.
- It does not edit `job_observation.py` or `job_viewer.py`. If a needed fact is missing from `job_view`, the implementer stops and reports it.
- Stdlib only (`curses`). No new dependency.

## Screens (retained A1 case; ages shown as `<age>` are computed at run time)

Job list, 80 columns:

```text
Baton v12 Jobs   1 Job · 1 needs a decision           !! STALE observed <age> ago
                                                   observed 2026-11-25T18:54:49Z

> job-w385263-a1                                               DECISION NEEDED
    job-w385263-a1/implementation: model-attribution-missing; owner action needed

 ↑↓ select   Enter open   n next needing a decision   r read now   q quit
```

Selected Job's phases:

```text
job-w385263-a1   DECISION NEEDED                      !! STALE observed <age> ago
  job-w385263-a1/implementation: model-attribution-missing; owner action needed
  1 admitted attempt(s) in nonterminal phases · Job age unknown

> implementation   answering — held for owner; admission admitted
      held: model-attribution-missing; owner action needed
      attempt 1 attempt-5c8cded2904fc3d5832ec474e045dde81fa63a770b5903e97a07abff7af532a2
      reserved on unknown
      duration unknown · timeout unknown · activity unknown · operation unknown
      Requested: not selected (account default)
  review           planned — waiting on job-w385263-a1/implementation (answering); admission unknown
      held: waiting on job-w385263-a1/implementation (answering)

 ↑↓ phase   Esc back   r read now   q quit
```

- List: one row per Job (`job_id`, `labelled_headline`), and the `headline_reason` beneath it when there is one. Header: Job count, and how many have headline DECISION NEEDED.
- Detail: the Job's headline, reason and `summary`; then one row per phase with `role` and `position`. Every phase shows its `reason`. The selected phase also shows the full attempt identity, every entry of `facts`, the timing line and `model_attribution`.
- A line too long for the terminal is cut with `…`; a fact is never wrapped into the next fact. Selection is shown by `>` and reverse video; nothing depends on colour.
- Rows are in the snapshot's own order (owner decision 2026-11-26). Jobs needing a decision are not moved to the top.

## Behaviour

**Keys.** `↑`/`k`, `↓`/`j` move; `PgUp`/`PgDn`, `Home`/`End` jump; `Enter`/`→` open the selected Job; `Esc`/`←`/`Backspace` go back; `n` moves to the next Job whose headline is DECISION NEEDED, in snapshot order after the selection, wrapping once to the top, and does nothing when there is none (owner decision 2026-11-26); `r` reads the snapshot now; `q` or `Ctrl-C` quits. Movement stops at the first and last row. Any other key does nothing. The key line is always on screen. No key changes anything outside this program.

**Selection across refresh.** Selection is a `job_id` in the list and a `stage_id` in the detail, never a row number.

- After a refresh the same identity is selected and on screen, wherever it now sits. The view does not jump if the row is still visible.
- If the selected Job or phase is not in the new snapshot, its row is replaced by one line, `<id> — not in the current snapshot`, which stays selected until the operator moves. Old content is not shown as current. A detail view of a vanished Job shows that line and the way back.
- With nothing selected yet, the first row is selected.

**Refresh.** One read per interval, the monitor's default of 5 s, `--interval` as `monitor` has it. `r` adds one immediate read. A read is never an act.

**Stale and unreadable.**

- Observation at least 15 s old: `!! STALE observed <age> ago` on every screen, with the observation instant. Reading again does not make it fresh.
- A failed read (missing file, mid-write truncation, over 4 MiB, not JSON, unknown schema, malformed Job): `!! DISCONNECTED <cause>` and the last good content stays, marked with when it was last read. The next good read clears it.
- Before the first good read: `not read yet`, no Jobs, the program stays up.
- Snapshot age and a phase's activity age stay separate values.

**Exit.**

- `q` and `Ctrl-C`: terminal restored, exit 0.
- `SIGTERM`, `SIGHUP`, terminal closed: terminal restored, exit nonzero by signal convention.
- Internal error: terminal restored first, then one line on stderr, exit 1.
- Not a terminal on stdin or stdout: refuse with a line naming `monitor`, exit 2, nothing drawn.
- Terminal smaller than 60×8 (*proposed*): one line saying so, redrawn on resize. Resize redraws without losing selection.
- Quitting leaves every Job, worker and file as it was.

**Command.** *Proposed*: `baton-v12-stack tui --instance …` beside `monitor`, and `python -m tools.job_tui --status PATH`. `monitor`, `status` and `view` are unchanged.

## Structure the tests need

`tools/job_tui.py` keeps three pure functions apart from the terminal: a state value (screen, selected identities, scroll), `step(state, key, view)` and `frame(state, snapshot, now, wall_now, rows, columns)` returning text lines and the selected line. The `curses` loop only reads keys, calls these and paints. Cases 1 to 11 run on the pure functions with scripted keys and snapshot sequences; cases 12 to 14 run the real program under a pseudo-terminal.

## Deterministic acceptance cases

No engine, provider, credential or store. Fixtures are status documents.

| # | Situation | Expected |
| --- | --- | --- |
| 1 | three Jobs: IN PROGRESS, DECISION NEEDED, QUEUED | one row each with `labelled_headline`; reason line only where `headline_reason` is non-empty; header `3 Jobs · 1 needs a decision` |
| 2 | retained A1 extract | list and detail carry exactly the strings `job_view` returns for headline, reason, positions, reasons and facts (compared to `job_view`, not to copied literals) |
| 3 | selected Job goes IN PROGRESS → DECISION NEEDED between two snapshots | same Job selected; headline and reason change in place; header count changes |
| 4 | a Job is inserted above the selection; Jobs reorder | the same `job_id` stays selected and visible |
| 5 | selected Job absent from the next snapshot | the `not in the current snapshot` line, selected; moving selects a neighbour; no stale content |
| 6 | detail open; phases change state; selected phase disappears | same `stage_id` selected; then the placeholder line |
| 7 | observation 14 s old, then 15 s, then a newer snapshot | no banner; STALE banner on list and detail; banner clears |
| 8 | good read, then each of: file missing, truncated JSON, 4 MiB + 1, unknown schema, malformed Job | DISCONNECTED with the cause; last good content kept and marked; next good read recovers |
| 9 | status file absent at start | `not read yet`; no exit |
| 10 | every key at top, middle and bottom rows; `n` with none, one and several DECISION NEEDED Jobs; unknown keys | the stated movement; no wrap; unknown keys change nothing |
| 11 | 60 and 200 columns; more rows than fit; resize | cut with `…`, selected row on screen, selection kept |
| 12 | under a pseudo-terminal: `q`; `Ctrl-C`; `SIGTERM` | terminal attributes equal before and after; exit codes as stated; no child process left |
| 13 | a whole session under an audit hook | only the status path is opened, read-only; no SQLite connection; nothing created or written |
| 14 | stdout is a pipe | exit 2, the refusal line, nothing drawn |
| 15 | a `job-status/10` snapshot with an open and a closed MANUAL Job | `labelled_headline` and the closed counts line as `job_view` gives them |
| 16 | existing `tests.tools.test_job_viewer`, `test_job_observation`, `test_stack` | pass unchanged, apart from the new verb's entry |

| 17 | a review held with no usable report, as the post-W386299 read model reports it | the held-review sentence appears on the review row in list reason or detail exactly as `job_view` gives it |

Cases 12 to 14 must run, not skip, wherever verification runs. See the pseudo-terminal section.

## Out of scope

Any command that changes a Job; artifact or log reading; more than one instance; mouse; colour themes; filters and sorting; new snapshot members; changes to the words of status or monitor; a web page.

## Likely files

| File | Change | W386299 changes it first |
| --- | --- | --- |
| `v12/python/tools/job_tui.py` | new | no |
| `v12/python/tests/tools/test_job_tui.py` | new | no |
| `v12/python/tools/stack.py`, `stack_command.py` | add the `tui` verb | `stack.py` yes |
| `v12/python/tools/parallel_test.py` | register the new test module in one group | only if W386299 adds a test module |
| `v12/python/tests/tools/test_stack.py` | the verb list | yes |
| `v12/python/JOB-VIEWER.md` | a TUI section | yes |
| `v12/DESIGN.md` | OBS-2: record that the read-only TUI is selected (owner-approved text, before code) | yes |
| `tools/job_observation.py`, `tools/job_viewer.py` | none | yes, both |

## Baseline (owner decision 2026-11-26)

The launch baseline is the verified checkpoint that contains W386299: the commit Slawomir makes after W386299's accepted candidate is imported on top of `76b2f2b2` and re-verified. That commit does not exist yet. The launch packet names it; this contract does not.

What follows from that choice:

- The TUI is written against the read model as W386299 leaves it. Case 17 is part of acceptance. If W386299 delivers the held-review sentence through a `job_view` member other than `reason` or `facts`, the TUI shows that member too; the implementer reads the imported code, not this guess.
- MANUAL Jobs (`job-status/10`, `labelled_headline`) are present; case 15 is unconditional.
- Both worker images must be rebuilt and requalified from that commit before a native launch. `76b2f2b2` already changed `v12/worker/claude_agent.py` and `provider_policy/__init__.py`, and W386299 changes `claude_agent.py` again. The images qualified from `f1825d74` equal source only up to `67fd60f8`.
- The shared files with W386299 (`stack.py`, `test_stack.py`, `JOB-VIEWER.md`, `DESIGN.md`, possibly the test registry) are no longer a rebase risk between the two: the TUI starts from W386299's result.

## Pseudo-terminal for cases 12 to 14

What the tests must do, because a worker runs verification with a closed environment (no `TERM`) and all three standard streams on `/dev/null`:

- Allocate their own pseudo-terminal (`pty.openpty`), start the TUI as a child with the slave as its controlling terminal, and set `TERM` themselves.
- Choose `TERM` as the first of `xterm`, `vt100`, `linux`, `ansi` for which `curses.setupterm` succeeds. If none does, the test fails with that reason. It never skips.
- Send `q`, `Ctrl-C` and `SIGTERM` in three sessions and compare the terminal attributes before and after.

Host evidence (`evidence/pty-probe-K/`): started with an empty environment and `/dev/null` streams, a probe allocated its own pseudo-terminal, drove a curses child to draw and to end on `q`, `Ctrl-C` and `SIGTERM`, and found the attributes restored each time. A plain `curses.wrapper` child dies by signal on `Ctrl-C` and exits 1 on `SIGTERM`; the exit codes this contract states therefore need explicit handling, which the tests check.

What is known about the worker container from source, not from a run:

- The manager composes `--read-only`, `--cap-drop ALL`, `--security-opt no-new-privileges`, `--pids-limit 512`, no `--tty`, no device or `/dev` override. The launcher requires user `1000:1000`.
- The images are `node:22-trixie-slim` plus Debian `python3`. On this host the `_curses` module belongs to `libpython3.13-stdlib`, which Debian's `python3` depends on.

Still needs a real container (none of this was run):

1. That a process with that posture and user can open `/dev/ptmx` and its slave under `/dev/pts`.
2. That the image's `python3` imports `curses`.
3. That the image carries a terminfo entry for one of the four names.
4. That cases 12 to 14 finish inside the 300 s verification bound together with the rest.

*Proposed*: settle 1 to 3 as one added inventory assertion in the image qualification gate that the rebuild needs anyway, run with the worker's own posture flags: allocate a pseudo-terminal and call `curses.setupterm` on it. That is an owner-run engine step; it is not selected here.

## Owner decisions recorded

- Baseline: the verified post-W386299 checkpoint (2026-11-26).
- List order: snapshot order; `n` jumps to the next DECISION NEEDED Job (2026-11-26).

No UX question is open. Before a launch packet: the baseline commit must exist, the images must be rebuilt and requalified from it with the pseudo-terminal assertion, and the OBS-2 text must be in DESIGN.
