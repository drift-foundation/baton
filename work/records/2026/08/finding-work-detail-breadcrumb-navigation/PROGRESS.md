# Progress

**State — 2026-08-21:** round-two review finding corrected and re-verified;
awaiting independent review.

## Response to `review-2026-08-21T06-58-22Z.md`

Confirmed and fixed. This one is a regression I introduced, not a pre-existing
gap: `_render_header` returned immediately after painting the breadcrumb, so
W5's `Filter:N` tag became reachable only at the top level. I re-ran the
reviewer's own reproduction against the fix and it now reads

```text
top:            [Jobs]  [Teams]  [Inbox]        Filter:1 lang.ada
Work detail:    Jobs > the root                 Filter:1 lang.ada
re-root:        Jobs > the root                 Filter:1 lang.ada
search:         Jobs > search: root             Filter:1 lang.ada
```

The reviewer's framing is the right one: W292 supersedes the global TAB ROW
inside a drill and nothing else. Search is what made this urgent rather than
cosmetic — results are themselves narrowed by the active filter, so a drilled
page without the disclosure showed a reduced result set with nothing saying
why.

## What changed

- `src/baton_work/tui/app.py` — `_filter_tag()` is now the ONE definition of
  when that tag appears and what it says; both the top-level header and
  `_render_breadcrumb` paint it from there, so they cannot disagree about
  when. The breadcrumb reserves both right-edge units — the tag and the
  identity — where the trail's room is decided, so the trail is shortened
  around them rather than half-erased by them. The normalized-clause line is
  untouched.
- `tests/work/test_w292_breadcrumb_navigation.py` — three new cases, 21 in
  total: an active filter is disclosed in direct Work detail, in a re-rooted
  table (which also keeps its clause line), and in search results; the tag and
  the identity both survive 100/72/56/44 columns with the trail shortened
  around them and a shortened trail announcing itself; and no filter means no
  tag, because the disclosure is a fact about the filter rather than
  decoration.
- `docs/BATON-WORK.md` — "always disclosed" now says out loud that it includes
  every drilled page, and why search is where it matters most.

## Verification

- `tests/work/test_w292_breadcrumb_navigation.py`: **21 passed**.
- W292 with W5, W71, W74 and W110: **70 passed** before the new cases; the
  full gate below covers them after.
- The complete v11 gate: **2810 passed** (non-serial) and **52 passed**
  (serial).
- The reviewer's reproduction re-run against the fix, quoted above.
- `git diff --check`: clean.

## Boundaries held

- No authority, projection, schema, transition or CLI change.
- W5's clause line, the navigation stack, the local tab rows and the read-only
  walk are unchanged; this round restored a disclosure the drilled header had
  dropped.

## Not done here

- Teams and Inbox gain no page drill; they have none today.
- Nothing was staged or recorded in history; the working tree carries the
  diff for Slawomir.
