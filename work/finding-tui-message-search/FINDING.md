# `/` cannot search retained messages

Status: **queued, lower priority**. Do not interrupt the active final
pre-release protocol/schema triage.

## User request — 2026-08-10

Slawomir requested that `/` allow a human to search through messages in the
Baton TUI. The unified MESSAGES list is retained activity and can grow long;
newest-first ordering makes recent work easy to find but does not help recover
an older conversation by subject or participant.

## Observed

- `/` has no current binding in `src/baton_tui/keys.py` or the TUI state
  machine.
- MESSAGES and the Sent filter already expose read-only row metadata and keep
  selection by row identity across refreshes.
- Opening unread directed work may create a claim, and receiving a notice
  records its seen receipt. A search convenience must not perform either
  action merely to decide whether a row matches.
- The current core/TUI boundary may not expose every retained body without an
  authorized open/materialize path. Full-content search therefore cannot be
  assumed to be a UI-only loop over already available bytes.

## Confirmed boundary

1. `/` is the message-search entry point.
2. Search is lower priority than the current release-finalization work.
3. Searching, filtering, moving among results, and cancelling search are
   read-only. They create no claim and no notice seen receipt.
4. This is a TUI/client feature unless later evidence demonstrates that a
   core query is required. It is not, by itself, a protocol/schema reason.

## Open UX and product decisions

- Search scope: list-visible metadata only (subject, other participant,
  direction, kind, state, date) versus retained body text where an authorized
  non-mutating read is available.
- Literal case-insensitive text versus regex or another query language.
- Incremental filtering of MESSAGES versus jump-to-next match while retaining
  the full list.
- Whether search also applies to the Sent filter and to the currently opened
  detail body.
- Result navigation keys and highlighting. Existing `n` is compose in normal
  navigation, so Vim-style `n`/`N` cannot be adopted without a defined search
  mode or another conflict-free state.
- Behavior across asynchronous refresh: preserve the selected result by row
  identity, admit new matches predictably, and never jump because row indices
  changed.

## Required regression boundary

When scheduled, cover at least:

1. `/` enters search only from an applicable navigation focus and Help lists
   the binding from the shared key table;
2. subject, participant, and other ruled fields match case and Unicode rules
   exactly as specified;
3. no-match, cancel, empty query, edit/backspace, next/previous result, and
   clearing search restore a stable list selection;
4. searching an unread directed row leaves it pending and unclaimed;
5. searching an unseen notice leaves it unseen;
6. results stay correct when polling adds or updates rows;
7. MESSAGES/Sent behavior follows the ruled scope rather than diverging;
8. narrow/short terminal rendering remains safe and the query/status surface
   does not reintroduce persistent screen noise;
9. pure state/render tests plus a packaged PTY path exercise the public TUI.

## Likely code surfaces to revalidate

- `src/baton_tui/keys.py`
- `src/baton_tui/state.py`
- `src/baton_tui/render.py`
- `src/baton_core/__init__.py` only if current read-only list APIs are
  insufficient
- `tests/tui/` and, only if the core boundary changes, `tests/core/`

Do not implement from this first capture without resolving the open search
scope and interaction decisions against the then-current TUI.
