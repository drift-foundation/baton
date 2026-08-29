# Restore Inbox after leaving an Inbox-opened detail

## Observed — 2026-08-28

From the top-level Inbox, opening an obligation or message enters the linked
Work/detail surface. Pressing Esc/Back then lands on Jobs instead of restoring
the Inbox page that initiated the navigation. The navigation history therefore
does not describe the operator's actual path.

This is current intentional behavior rather than an accidental code drift:
W292 specified Inbox entry as a handoff into Jobs, and its regression
`test_the_inbox_handoff_lands_in_jobs_and_backs_out_there` preserves that
exception. The later universal browser-history model established that Back
restores the previously viewed page regardless of hierarchy depth. Inbox is no
longer exempt now that it opens real obligation/message detail.

## Confirmed decision — 2026-08-28

The old Inbox-to-Jobs Back exception is superseded. Opening an obligation,
message, or linked Work from Inbox is one browser-history navigation step.
Esc/Back restores the exact Inbox frame that initiated it: team context,
filter, cursor, stable selected row, scrolling/page state, and pane focus where
applicable. The detail page may still use the linked Work as its content and
breadcrumb root; that does not change the caller recorded beneath it.

Repeated drill-down inside the opened detail continues to use the ordinary
bounded navigation history. Back unwinds those pages in visit order and then
returns to Inbox once. It never substitutes Jobs merely because the selected
entity belongs to Work.

## Acceptance

- Inbox obligation and message entry each push an Inbox restoration frame.
- One Esc from the directly opened detail restores the exact Inbox view and
  stable selection that opened it.
- Deeper navigation unwinds in browser-history order and ultimately restores
  that same Inbox frame.
- Jobs-, search-, Teams-, graph-, and poke-origin restoration remains
  unchanged.
- Navigation remains client-only and read-only: no protocol, schema,
  projection, message-seen, or workflow mutation is introduced.
- Real-key regressions cover Esc/Back plus selection/filter/page restoration.

## Current-tree revalidation — 2026-08-28

**Confirmed baseline.** The superseded behavior is still live and all three
focused cases preserving it pass:

- `tests/work/test_w292_breadcrumb_navigation.py::test_the_inbox_handoff_lands_in_jobs_and_backs_out_there`;
- `tests/work/test_w25_jobs_teams_inbox.py::test_enter_opens_the_rows_work_in_jobs`;
- `tests/work/test_w2597_detail_entry_focus.py::test_the_inbox_entry_path_uses_the_default`.

The first case manually reproduces the exception by changing `tab` to Inbox,
calling `_enter_detail`, changing `tab` to Jobs, and requiring Back to leave
Jobs visible. The real entry path in `Console._handle_inbox` does the same
thing in production order: it sets `self.tab = "jobs"` before calling
`_enter_detail`. `_enter_detail` then lets `_nav_push` capture the already-
changed frame, so the one durable browser-history fact says Jobs even though
Inbox was the caller.

**Confirmed shared mechanism.** `_nav_push` accepts an explicit `restore`
dictionary, keeps the first caller separately in bounded `nav_caller`, and
`_nav_pop` restores every key carried by that dictionary. The Teams-to-Work
path already uses exactly the required shape: `_handle_teams` passes
`{**self._nav_capture(), "tab": "teams", "team_cursor": ...}` to
`_enter_detail`, then switches the live detail handler to Jobs. Back restores
the Teams roster and stable member. Inbox should join this shared mechanism,
not add another return flag or special Back branch.

**Confirmed current Inbox frame.** The restorable Inbox-specific state is
`tab`, `inbox_cursor`, and the stable `inbox_key`. `_render_inbox` derives the
visible scroll window from `inbox_cursor` and terminal height, so restoring the
cursor restores the same visible window at the same size; `_inbox_selected`
reanchors that cursor from `inbox_key` after row insertion/removal. Inbox has
no local filter, continuation/page cursor, or pane-focus field today. The
viewer team/member are immutable Console identity, and the Jobs `work_filter`
does not filter Inbox. The decision's filter/page/focus clause therefore adds
no invented state now; any such future Inbox field must join this explicit
caller frame.

**Confirmed entry coverage.** There is no Inbox row of kind `work` — actionable
Work belongs to Jobs. The one `_handle_inbox` Enter branch covers every Inbox
row whose canonical projection supplies non-null `work`, including obligation,
message, due-trial, runtime and incident rows. Pokes correctly remain in Inbox
because they name a participant and carry no Work context. Permanent coverage
must exercise obligation and message rows explicitly and keep the poke no-op.

**Confirmed breadcrumb boundary.** The linked Work continues to paint the
ordinary Jobs/Work structural breadcrumb. `breadcrumb_items` deliberately
builds the Work trail from a `Jobs` top crumb, while the actual caller lives in
the restore frame beneath it. This matches the confirmed decision: do not
rename the Work breadcrumb to Inbox or change breadcrumb focus/jump semantics.

## Recommended patch boundary

- In `src/baton_work/tui/app.py`, change only the Work-bearing Enter branch of
  `Console._handle_inbox`: capture one explicit restore dictionary containing
  `_nav_capture()` plus `tab="inbox"`, `inbox_cursor`, and `inbox_key`; pass it
  to `_enter_detail`; switch the live detail context to `tab="jobs"` only
  after the caller has been captured. Follow `_handle_teams`' ordering.
- Do not add Inbox fields globally to `NAV_STATE_FIELDS`. The existing Teams
  precedent keeps top-level-tab state local to the one transition that owns
  it, avoiding unrelated frames restoring tabs they never captured.
- Do not change `_nav_push`, `_nav_pop`, `NAV_HISTORY_LIMIT`, projections,
  authority transitions, message-seen state, fresh detail defaults, local
  tab/pane handlers, or breadcrumb construction.
- Update `docs/BATON-WORK.md:166-172`: remove the Inbox-to-Jobs exception and
  state that Back restores the Inbox row that opened the Work.

## Regression boundary

- Replace (do not delete) the superseded W292 assertion with a real Inbox-row
  entry requiring one Esc/Left to restore `tab="inbox"`, the same stable
  `inbox_key`, cursor-derived window, and empty navigation stack.
- Parameterize or pair obligation and message entry. Preserve the existing
  fresh Work-detail focus assertion and the poke-with-no-Work behavior.
- While detail is open, insert a row that sorts ahead of the caller, refresh,
  then Back and render; selection must reanchor to the captured key rather than
  remain at the old ordinal.
- Add a deeper walk (for example Inbox → Work detail → dependency page): first
  Back restores Work detail, second Back restores Inbox exactly once. Exercise
  more than `NAV_HISTORY_LIMIT` ordinary transitions or reuse the existing
  bounded-history harness to prove the original Inbox caller remains in
  `nav_caller` after eviction.
- Add a PTY/real-key flow that opens Inbox with `]`, selects a Work-bearing row,
  presses Enter and bare Esc/decoded Left, and observes Inbox restored. Assert
  `store.last_seq()` and the viewer's seen cursor are unchanged throughout.
- Keep Jobs, search, Teams, graph, poke, Awaiting-me and breadcrumb-focus
  restoration suites green; those origins share `_nav_pop` and are the
  principal non-regression boundary.

**Open decisions:** none. The product ruling, current state inventory, caller
representation and patch boundary are all determined.

## Independent review — 2026-08-28

**Confirmed:** the implementation captures the explicit Inbox caller before
switching the live detail handler to Jobs. Real obligation and message entry,
deeper unwind, stable-key restoration after an actual refreshed insertion,
bounded-history eviction, poke no-op, read-only state and PTY bare-Esc/decoded-
Left paths all pass.

**Changes requested:** `src/baton_work/tui/app.py:5926` still states the
superseded rule that Back from an Inbox-opened Work leaves the operator in
Jobs. Correct that production comment to match this finding and the behavior;
no behavioral change is requested. Full review:
`review-2026-08-28T23-30-27Z.md`.

## Independent re-review — 2026-08-28

**Signed off:** the stale production comment now records W34884's supersession
and matches the accepted implementation. The three reviewer acceptance cases
pass again and scoped diff checking is clean. Final review:
`review-2026-08-28T23-42-05Z.md`.
