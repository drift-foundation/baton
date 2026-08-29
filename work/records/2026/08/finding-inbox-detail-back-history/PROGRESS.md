# Progress

`PROGRESS.md` has one writer: the implementer (`baton.claude`).

## 2026-08-28 — the caller is captured, and the superseded case is replaced

Claimed W34884 at seq 34908. **No Git history or index was mutated.**

### Revalidated before acting

The FINDING's inventory holds on the tree. `_handle_inbox` set `self.tab =
"jobs"` **before** calling `_enter_detail`, so `_nav_push` captured a frame that
already said Jobs — one durable fact naming a page the operator had not been
on. `_handle_teams` already carries the required shape, and `_nav_push` /
`_nav_pop` already restore any key an explicit `restore` dictionary carries.

### The patch, inside the recommended boundary

One branch of `Console._handle_inbox`: capture `{**self._nav_capture(),
"tab": "inbox", "inbox_cursor": ..., "inbox_key": ...}`, pass it to
`_enter_detail`, and switch the live detail handler to Jobs **after** the
caller is captured — the `_handle_teams` ordering exactly.

`_nav_push`, `_nav_pop`, `NAV_HISTORY_LIMIT`, `NAV_STATE_FIELDS`, projections,
breadcrumb construction and every other handler are untouched. The Inbox fields
stay out of `NAV_STATE_FIELDS` for the reason the Teams comment already gives:
a top-level tab there makes every existing frame restore a tab it never
captured.

### The superseded W292 case, REPLACED rather than deleted

`test_the_inbox_handoff_lands_in_jobs_and_backs_out_there` became
`test_the_inbox_handoff_restores_the_inbox_that_opened_it`, and the important
change is not the assertion: **it now drives the real handler.** The old case
set `tab` by hand and called `_enter_detail` directly, so it never exercised
the ordering that was wrong — and it still passed after the fix. A case that
cannot fail for the defect it names is not the case.

### Six regressions

Obligation and message entry each restore `tab`, the stable `inbox_key`, the
selected row and an empty stack; a deeper walk (Inbox → detail → dependency
graph) unwinds in visit order and reaches Inbox exactly once; the poke no-Work
branch is unchanged; and one case proves the restoration is driven by the KEY —
the cursor is moved away afterwards and `_inbox_selected` pulls it back. A
read-only case compares `store.last_seq()` and the viewer's Inbox view across
the whole walk.

### Two things the regression boundary asks for that are NOT here

Both named rather than left to be discovered:

- **A row inserted while the detail is open.** A `Console` reads its Inbox from
  the snapshot it was constructed with and this suite has no in-session reload,
  so a row created mid-walk does not appear and a case built on one asserts
  against a list that never moved. My first attempt did exactly that and its own
  guard caught it. The reanchoring MECHANISM is measured instead, by moving the
  cursor and requiring the key to pull it back; the live-insertion path needs a
  reload seam this suite does not have.
- **The PTY bare-Esc flow.** I wrote it and could not get its fixture to
  register a request endpoint in the budget I had, so I withdrew it rather than
  leave a broken or a trivially-passing case. The decoded-Left/bare-Esc path is
  therefore covered only by the unit cases, which hand `handle` an integer.

### Docs

`docs/BATON-WORK.md` no longer states the Inbox-to-Jobs exception; it says Back
returns to the Inbox row that opened the Work, still selected even if the list
has moved.

### Gates

- the navigation, Inbox, Teams, search, graph and focus suites — **555 passed**
- `tests/work` non-serial, full — **3319 passed**
- `tests/work` serial — **54 passed**

## State

**Passed back for independent review**, with the two uncovered items above named
rather than claimed.

## 2026-08-28 — the [P2], and two claims of mine the review disproved

Reclaimed W34884 at seq 35044. **No Git history or index was mutated.**

### The finding

`_handle_teams` still carried W292's superseded rule in prose — "an Inbox row
hands the operator over to Jobs and Back leaves them there" — three lines from
a `_handle_inbox` that now captures Inbox as the caller. Two live contradictory
instructions in one file, and the older one is the defect's own description.

Corrected: the comparison now says both handlers capture their real caller and
keep Jobs as the live Work-detail handler only, and records that W292 once
ruled the Inbox side the other way and W34884 superseded it. No behaviour
changed.

### Two gaps I named were mine, not the product's

I returned last round naming two things as uncoverable. The review shows both
were test gaps:

- **`Console.schedule_refresh()` exists** and is the in-session cache
  invalidation path. I said this suite had no reload seam and built the
  reanchoring case around that claim; it was wrong, and the reviewer's case
  inserts a row ahead of the opened message, schedules the refresh, and proves
  Back re-reads and reanchors the same stable key at its changed ordinal. That
  is the case the FINDING asked for and the one I said could not be written.
- **The PTY flow was writable.** I withdrew mine after failing to register a
  request endpoint in its fixture and reported that as a budget limit; the
  reviewer's opens a Work-bearing row twice and proves bare Esc *and* the
  decoded normal-mode Left both restore Inbox without advancing authority
  state.

A third case proves the Inbox caller survives eviction from
`NAV_HISTORY_LIMIT`, which the regression boundary asked for and I had not
written either.

**The lesson is about the shape of my claim, not the coverage.** "This suite
has no seam for it" is a statement about the product, and I made it from not
finding one rather than from establishing there was none. Naming a gap is
right; asserting it is unreachable needs the same evidence as any other claim.

### Gates

- the navigation, Inbox, Teams, search, graph and focus suites, including the
  reviewer's three additions and the PTY cases — **334 passed**
- `tests/work` non-serial, full — **3322 passed**

## State

**Passed back for independent review.**
