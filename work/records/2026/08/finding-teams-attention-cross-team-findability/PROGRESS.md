# Progress

`PROGRESS.md` has one writer: the implementer (`baton.claude`).

## 2026-08-28 — claimed; the bounded v11 correction

Claimed W29146 at seq 31482. Evidence:
`evidence/w29146-mutation-harness.py`. No Git history or index was mutated.

### Revalidating the pinned decisions against the tree

Every pinned observation in `FINDING.md` was re-read against the current
source rather than carried forward, and all of them hold:

- `projection.teams()` returns every configured team in one snapshot, and each
  member already carries `pickup.next_work {work, local_id, title}`. The
  correction needed no new authority read.
- `Console.teams_need_attention()` scans that whole cached roster, so the
  global star was correct and stayed untouched.
- `team_rows()` dropped every non-own team whenever `teams_own_only`, which is
  the default — the cause and its concealment were the same cached data.
- `projection.search()` queries `work WHERE team = viewer_team` and published
  nothing about that scope.

`PROJECTION_VERSION` was at **12.7** rather than the 12.6 the dossier's
neighbours name, because W26328 advanced it in the meantime; this Work rolls
it to **12.8** as the plan pins.

### What was built

The `search` result gains `team`; the console reads it and the heading becomes
`search (team NAME): QUERY`, with the empty answer reading
`(no matches for 'QUERY' in team NAME)`. `team_rows()` keeps its own-team
default and adds every overdue foreign member; `team_exceptions()` and
`_team_scope()` are the single owners of "which of these are exceptions" and
"say so", because the scope line and the entry focus both need that answer and
three derivations would be three places to disagree. `_focus_attention()`
selects the first overdue member in visible-row order when the tab is starred
and moves nothing when it is not. `_team_selected()` falls back to the
viewer's own participant when a selected exception vanishes. Enter opens
`pickup.next_work` in ordinary Jobs detail and the footer advertises it only
when there is one.

### The mistake worth naming: a ruled behaviour I broke and then made explicit

The first version added `tab`, `team_cursor`, `team_member` and
`teams_own_only` to `NAV_STATE_FIELDS`, which looked inert — every existing
push happens from Jobs with those already where they say. It was not.
**W292 rules that an Inbox row HANDS THE OPERATOR OVER to Jobs and Back leaves
them there**, and W29146 rules the opposite for Teams. Capturing the tab
globally made which ruling applied depend on the ORDER of two statements at
each call site, and `test_the_inbox_handoff_lands_in_jobs_and_backs_out_there`
failed.

The tab and roster selection now ride in ONE explicit frame handed to
`_enter_detail(restore=...)` at the Teams call site. Every other navigation
path is byte-identical to before, and the two opposite rulings are each named
where the decision is rather than inferred from statement order. This is the
same shape as `_nav_capture`'s own docstring warning — a mode-specific
assumption is invisible until somebody walks the exact path that used it.

### Two existing assertions changed, both pinned by the dossier

- `test_w6_search.py::test_the_slash_mode_on_the_real_terminal` asserted the
  old `search: findable` heading and `(no matches for 'zzz')`. The dossier
  pins the new spelling and the regression matrix requires the team be
  visible, so both were updated to the team-qualified forms.
- Seven suites pinned `PROJECTION_VERSION == "12.7"`. Those are the exact
  version pins the dossier names as part of this patch boundary.

### Measured, not read

Harness: `evidence/w29146-mutation-harness.py`, over the new suite plus
W2938's pickup, W25's tab grammar, W6's search, W292's navigation and parity —
because a correction only its own tests notice has not been measured against
the rulings it had to keep.

**16 of 16 caught, none expected-unseen.** Two were UNSEEN on the first run and
both were defects in my CASES rather than in the code:

- the vanished-exception case set `team_member` without moving `team_cursor`,
  and the old `min(cursor, len - 1)` fallback happened to answer the same row
  from cursor 0 — so it proved nothing about the fallback. The operator it is
  written for is LOOKING at the exception, so the case now selects it properly
  and asserts the cursor on both sides.
- `window["team"]` and `self.team` are equal in every ordinary run, so a
  console that ASSUMED the scope passed everything. A case now makes the
  authority answer a different team and requires the header to report it,
  which is the only way to prove the header reports rather than restates.

### Gates

- the focused suite — 29 cases, green
- full v11 gate — see the pass comment for the exact counts
- full v11 gate — **3313 parallel passed, 54 serial passed, ACP 89 pass / 0 fail**
- mutation measurement on the final tree: **16 of 16**

## State

The bounded v11 correction is implemented and measured. Passed back for
independent review rather than closed.

### For review

- **The exception is a presentation exception over data `teams` already
  returns globally.** No authority, roster projection, pickup derivation or
  privacy boundary moved: this stops discarding the part of an existing read
  that the marker is about. If the judgement is that showing a foreign
  participant's row at all is a privacy question rather than a presentation
  one, that is a different contract than the one the dossier pins.
- **Entry focus picks the first overdue member in visible-row order, which can
  be an OWN-team member.** The star is deployment-global and own team sorts
  first, so an own-team cause is the one an operator should be looking at when
  there is one. The finding says "focuses the first overdue member in
  canonical visible-row order" and this reads that literally.
- **`Enter` from Teams returns; `Enter` from Inbox hands over.** Both are
  ruled, and they are opposite. The difference is now an explicit argument at
  the Teams call site rather than a property of `NAV_STATE_FIELDS`, because
  the global version broke W292 — recorded above.
- **V12 principal aggregation remains untouched.** Nothing here guesses that
  two `*.slaw` spellings are one human; the cross-team row appears because a
  configured participant is overdue, not because the viewer might be them.
