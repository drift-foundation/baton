# `/` cannot search retained messages

Status: **current MESSAGES/Sent source signed off in append-only review
`review-2026-08-11T17-33-45Z`; Archived-view integration and Slawomir's human
trial remain 1.1 release gates.**

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

## Confirmed resolution and implementation — 2026-08-11

The “Open UX and product decisions” section above is resolved for v1 and is no
longer actionable:

- metadata only: author/other party and subject; no body search;
- case-insensitive literal substring using `casefold`, never regex;
- filter the active list in place, including Sent;
- typing filters incrementally; Enter keeps the filter; `/` then Esc clears it;
- filtering, navigation, refresh, and cancellation remain read-only and
  preserve claims, unseen notices, obligations, and row identity.

The implementation and focused/PTY coverage exist in the working tree. It has
not changed the released 1.0.0 binaries. Before inclusion it still needs a
durable append-only independent review record, human trial, and the isolated
next-generation build/deployment gate.

## Human-trial sequencing — 2026-08-11

Slawomir wants to try search himself from the deployed 1.1 candidate before
clearing the release. Independent source/focused/PTY review happens before the
candidate build; the human trial is then recorded from the versioned deployed
tree during the soak. Human trial is not a prerequisite to building the thing
that must be tried, but remains a prerequisite to final release clearance.

## Independent review state — 2026-08-11

`review-2026-08-11T16-48-36Z.md` requests changes. Incremental filtering and
Sent refresh currently restore `sent_cursor` through `_all_sent_rows`/the raw
unfiltered result even though the cursor indexes the filtered `sent_rows`
view. The focused tests pass but omit that index boundary. Correct by captured
row identity in the filtered view, add narrowing/refresh/cancel regressions,
and obtain a new append-only approval before candidate build.

## Archived-view inclusion — 2026-08-11

Slawomir confirmed that search includes archived entries. When the 1.1 Archive
feature lands, `/` applies to Archived with the same metadata-only literal
`casefold()` filter, identity preservation, refresh behavior, and no-read/no-
claim/no-receipt boundary as MESSAGES. The active-view filter model remains:
Archived search filters archived rows in place, while MESSAGES continues to
hide them until restored. The Archive finding owns the view lifecycle and
acceptance coverage; this finding continues to own the shared search
semantics.

## Independent re-review state — 2026-08-11

`review-2026-08-11T17-24-04Z.md` accepts the filtered Sent capture and refresh
correction but requests one test-fixture fix. The synthetic recipient
`acme.reviewer` itself matches the first query character `m`, so the leading
subject row is never filtered out and a restored `_all_sent_rows` capture does
not fail the intended incremental regression. Use a nonmatching recipient (or
equivalent query), assert the first narrowing removed the leading row, prove
the deliberate break fails, and return for append-only sign-off.

## Source sign-off — 2026-08-11

`review-2026-08-11T17-33-45Z.md` signs off the current MESSAGES/Sent source.
The fixture now uses a nonmatching other party, asserts the first narrowing
actually removed the leading row, and fails under a restored full-list capture
exactly at the wrong-row jump. Archived-view integration remains open under
`work/finding-tui-bulk-select-trash/`, and the deployed-candidate human trial
remains required before release clearance.
