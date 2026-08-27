# Reviewer research — 2026-08-27

## Current breadcrumb inventory

`src/baton_work/tui/app.py` paints a breadcrumb whenever the universal navigation stack is non-empty. The current breadcrumb-bearing pages are:

1. a contextual Work page on its `Jobs`, `Messages`, or `Events` local tab (`kind=work`);
2. search results (`kind=search`, no local tabs);
3. the dependency graph (`kind=links`, no local tabs), including graph recenter steps;
4. the participant poke view (`kind=pokes`, no local tabs); and
5. after W26328 lands, the flattened `Awaiting me` Jobs view (no local tabs).

Top-level Jobs, Teams, and Inbox have the global tab bar and no breadcrumb. Inbox-to-Work is deliberately a handoff into Jobs; Back returns to Jobs, not Inbox.

**Observed:** `nav` is browser-shaped interaction history, while `nav_segments()` derives structural Work ancestry plus page labels from those frames. Direct ancestor navigation exposes a new case: the deeper page must stay in history for one-step Back, but it must disappear from the displayed location. Popping frames loses the required history; merely appending an ancestor frame makes the old deeper location remain in the breadcrumb. Implementation therefore needs an explicit location-reset/current-location concept rather than treating an upward jump as repeated Back.

**Observed:** the existing header drops old segments and may slice the tail of one long title. It has no selected crumb, structured target, horizontal viewport, or textual focus report.

**Observed:** the existing Work breadcrumb projection already supplies stable `{id, title}` ancestry. Focus and direct navigation are session-local presentation state; no protocol, projection-version, or database change is required.

## Existing focus graphs

- Contextual Jobs, search, graph, and pokes each have one selectable body region.
- Work Messages has `threads`, `index`, and `reader`; Tab/Shift-Tab cycles them, and `Ctrl-W` moves geometrically.
- Work Events has `index` and `reader` with the same two focus mechanisms.
- Local Work tabs are selected by `[`/`]`; they are not a pane-focus stop.
- Command entry, reverse search, search text entry, batch entry, authored-prose prompts, and exit confirmation own their keys before page navigation.

No top-level page gains breadcrumb focus. While the breadcrumb is not focused, every existing key keeps its current meaning.

## Focus model proposed for approval

Add one breadcrumb focus flag and one stable crumb key to the captured navigation state. Viewport start is derived from the selected key and terminal width on every paint, so resize never changes selection.

The Tab cycles are:

- contextual Jobs: breadcrumb, table;
- Messages: breadcrumb, threads, index, reader;
- Events: breadcrumb, index, reader; and
- search, dependency graph, pokes, and Awaiting me: breadcrumb, body list.

Tab moves forward, Shift-Tab backward, and both wrap. In Work detail, extend the existing `Ctrl-W` geometry: Up from the top pane reaches breadcrumb and Down from breadcrumb returns to that top pane. Other single-body pages gain no new `Ctrl-W` grammar.

Up from the first selectable entry in a single-body page, from the first Thread while Threads is focused, or from the newest/top Events index entry may enter the breadcrumb. Down leaves the breadcrumb and restores the page's prior body/pane focus. Lower Message panes do not jump over Threads to reach the header.

On first focus, select the current/deepest crumb. While focused:

- `h`/Left and `l`/Right move among crumbs and hold at the ends;
- Left never means Back while breadcrumb is focused; Esc remains the unambiguous Back key;
- Enter on the current crumb is a pure no-op;
- Enter on another crumb performs one direct navigation;
- Down returns to the body; and
- `[`/`]`, `:`, `q`, and other view-level keys keep their existing ownership unless a text/modal surface already owns them.

Focus movement reads no authority data, changes no seen cursor or selection, and schedules no refresh.

## Structured crumb and direct-navigation contract

Render from structured crumb items rather than strings. Each item needs a stable key, display label, compact selector, target kind, optional Work id, and whether it is current. Compact selectors are:

- `Jobs` for the top-level Jobs location;
- the exact authority-local `W…` selector for Work crumbs; and
- `search`, `deps`, `pokes`, or `awaiting` for non-Work pages.

The complete title/query remains in the page itself; the compact selector is the identity that must never be clipped when the full crumb label cannot fit.

Direct navigation is a new interaction step, never a sequence of Back operations:

- a Work ancestor opens that Work's contextual page; when jumping between contextual Work scopes, preserve the current local Jobs/Messages/Events tab, otherwise open Jobs;
- a prior search/deps/pokes/awaiting page restores the exact captured query, graph center/depth/expansions, page cursor, and selected identity it had when left;
- the Jobs crumb restores the exact top-level Jobs caller state; and
- the current crumb does nothing and records no history.

The jump captures the complete deeper page, appends one browser-history step, and resets the displayed location to the target. One Esc then restores the deeper page exactly—including its breadcrumb focus and selected crumb—even if several containment levels separate the two. The existing 64-step eviction rule and separately retained original caller remain unchanged.

## Viewport and textual feedback

Reserve the existing right-edge dispatch/filter/participant region first. In the remaining header cells, paint the maximal contiguous crumb run containing the selected crumb when focused, or the current crumb otherwise. Never slice a crumb token. If the full Work title cannot fit, substitute its exact `W…` selector; page labels use their compact selector. If even that token cannot fit, paint no plausible fragment and use the explicit narrow refusal below.

Use `…` as a standalone left and/or right viewport marker, so `… > parent > child > …` identifies which sides are omitted. The marker is never selectable.

While focused, replace the page-help footer (not command/status input) with:

```text
breadcrumb 3/5: W3 · h/l select · Enter open · Down page · Esc back
```

The ordinal and exact selector carry selection meaning without colour. At narrow widths, keep `breadcrumb 3/5: W3` whole before dropping help clauses. If the exact prefix itself cannot fit, render `(breadcrumb too narrow)` rather than a clipped selector. Command, batch, confirmation, and authored text surfaces retain priority and cannot be entered while the breadcrumb steals their input.

Empty crumb sets cannot be focused. A single crumb selects `1/1`; movement and Enter are no-ops, Down returns to the body, and Esc keeps Back semantics.

## Focused baseline

The pre-change navigation/focus baseline ran:

```text
./.venv/bin/python3 -m pytest -q \
  tests/work/test_w292_breadcrumb_navigation.py::test_direct_grandchild_entry_is_one_action_and_one_back \
  tests/work/test_w292_breadcrumb_navigation.py::test_a_works_own_pages_are_tabs_of_one_level_not_two_levels \
  tests/work/test_w292_breadcrumb_navigation.py::test_search_is_a_segment_and_keeps_its_exact_restoration \
  tests/work/test_w292_breadcrumb_navigation.py::test_the_links_page_is_a_segment_too \
  tests/work/test_w292_breadcrumb_navigation.py::test_a_narrow_header_keeps_where_you_are_and_who_you_are \
  tests/work/test_w1151_pane_focus.py::test_tab_cycles_the_message_panes_forward \
  tests/work/test_w1151_pane_focus.py::test_events_cycles_the_panes_it_actually_paints \
  tests/work/test_w1151_pane_focus.py::test_tab_and_the_chord_reach_the_same_states \
  tests/work/test_w4996_dependency_graph.py::test_enter_recenters_and_esc_restores_the_exact_prior_graph \
  tests/work/test_w17_poke_visibility.py::test_esc_returns_to_the_work_table
```

Result: `10 passed in 0.16s`.

## Regression matrix

- empty, one-, and many-crumb paths; full Work ancestry after a one-action deep entry;
- initial deepest selection, both horizontal key pairs, end holding, current Enter no-op, and exact selector footer;
- direct parent/root/top Jobs jumps followed by one Back to the exact deeper page and focus;
- same-tab Work-scope jumps from Jobs, Messages, and Events;
- exact restoration of search query/page/selection, graph center/depth/branch expansions, pokes, and Awaiting-me page state;
- Tab/Shift-Tab inverse cycles and `Ctrl-W` geometry in Messages and Events;
- boundary Up/Down for every single-body page and no jump from a lower pane;
- `[`/`]`, Left, Esc, command/batch/search text, modal confirmation, and unfocused keys retain their existing owners;
- selected crumb remains visible across narrow/wide resize without moving selection;
- long titles use exact `W…` fallback, both-side `…` markers, right-edge filter/dispatch/identity survival, and explicit impossible-width refusal;
- focus moves are pure: no authority read/write, seen movement, refresh, row selection, or page cursor change;
- history eviction still retains the original caller and direct jumps consume exactly one history entry;
- PTY, documentation, packaged console, and W26328 Awaiting-me integration.
