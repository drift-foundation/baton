# Progress

Implementer-owned.

## Revalidation against the current tree — 2026-08-19

The observation holds exactly. `_team_detail` built a list of prose
lines and wrapped them with `soft_wrap`: `roles:` at two spaces,
`route X (role): …` at two, `adapter codex provider=… model=…` packing
three facts into one sentence, `incarnation … · since … · last contact
…` packing three more, and the poke answer's five runner fields on one
line. Labels started wherever the sentence put them.

Two neighbours needed checking:

- **W93** owns the fields. Nothing here reads or writes the authority
  differently — `teams()` is unchanged and a test asserts the roster
  JSON is byte-identical in the facts it carries.
- **W137** (in review) made the member TABLE responsive. That is the
  row above; this is the block below, and they share only the width.

## What changed

`kv_lines(sections, width)` is a new module-level function beside the
renderer, and `_team_detail` became five small builders that return
`(key, value)` pairs. The split is deliberate: the section builders
hold WHAT is shown and `kv_lines` holds HOW, so a later section is one
list entry rather than another paragraph of formatting.

The value column is computed across the WHOLE block, not per section,
so an operator's eye lands in one place and stays there. A wrapped
value continues at the value column. A key longer than the cap — a
third of the usable width — keeps its whole text on its own line with
the value beginning on the next, because truncating a label produces
something that reads like a different label.

Three cases the finding implies and this had to decide:

1. **A member with no lease** gets ONE `Lease` row saying the adapter
   has never published runtime state, not a dozen rows of `-` that
   would read as a runner actively reporting nothing.
2. **`Log` is always present**, as ruled: the locator with its source
   and age, or "not published — this runner's adapter has published no
   log locator". An operator hunting for a log must be told it was
   never published rather than handed a path from a deployment they
   hope is running.
3. **`Stale` is its own row** beside `Lease expires`. The deadline and
   whether it has passed are different facts, and a reader should not
   have to subtract one from the clock to learn the other.

Below roughly forty columns the two columns stop being two columns —
a value with four cells is not a value — so the block STACKS: key on
its own line, value indented under it. Still every fact, still in
order, still inside the screen.

## One consequence I had to handle

Giving every fact its own row made the block about twenty-five lines
where the prose was ten. At a 24-row terminal the lower sections —
including the ruled `Log` row — fell off the bottom, and the old code
simply stopped drawing, which looks identical to a block that ended.

Two changes, both presentation:

- the member LIST now takes at most half the available rows when a
  member is selected, instead of everything up to its old floor;
- when the block still does not fit, the last line says how many rows
  were not shown and names `teams` as the verb holding the whole
  record. That is the shape the pokes view already uses, so it adds no
  new vocabulary and no new key.

I did NOT add a detail scrollbar or scroll keys: the finding says
selection, scrolling and actions remain unchanged, and inventing a
gesture is a bigger change than the finding describes. Flagged here as
a judgement call — if the reviewer wants the block reachable in full on
a short terminal, that is a scrolling decision and belongs to its own
record.

I also did not add the runner's own `work`/`episode` correlation to the
block. It is a genuinely useful fact and W93 rules that the
disagreement between it and the Handler should be visible, but it is
not a fact this block exposes today and the finding asks for
presentation only.

## Superseded assertions edited

The finding supersedes the prose FORM of this block, so every
assertion that pinned a sentence moved to the row that now carries the
same fact. Each kept its property:

- W93's approval case asserted `waiting-input (reported)` and
  `approval` on one line, and `provider=OpenAI` with `model=gpt-5.6`
  on another. They are four rows now and the test asserts four rows —
  which is the ruling, not a weakening.
- W93's inventory, refresh, `no lease` and `since …` cases move to
  `Workdir`/`Log`, `Refresh`, `Lease` and `Since`.
- W25's `holding W2`, `route main (dev): …` and the raw-answer case
  move to `Holding`, `Route` and the answer's own keys.
- W137's `provider=OpenAI` moves to the `Provider` row.
- Five of those cases now paint a 40-row virtual screen, because the
  block is legitimately taller than the 24 rows they used to assume.
  Nothing else about them changed.

## Verification

- `tests/work/test_w184_member_detail_table.py` — new, **33 passed**:
  the five sections in order, one value column across the whole block,
  wrapped continuations at that column with the locator recoverable
  from the pieces, a long key keeping its text, empty sections
  omitted, every identity/workflow/runner/diagnostic/answer fact
  present with its own key, the `Log` row in both the published and
  the never-published case, no-lease and never-asked and `unknown`
  staying distinguishable, widths from 200 down to 12 never painting
  past the edge, a narrow block carrying every key, a wide one
  recovering the whole session, resize idempotence, one row per route,
  the projection asserted unchanged, selection/scope/actions still
  working, the short-terminal disclosure, the documentation, and a
  REAL terminal at 120×44 painting the sections, the session and the
  log locator.
- W93 **91 passed**, W25 **36 passed**, W137 **212 passed**,
  W167 **24 passed**.
- The complete v11 gate, `just test-v11`, exits 0 on this tree:
  **2449 passed** (parallel), **40 passed** (serial), both bridge
  suites green. One of my own W93 slice-7 scenarios also had to paint
  taller for the same reason as the five cases above.

## Boundary with W110, W137 and W167

All three are in review and share this uncommitted tree; separating
them is a Git operation my role forbids, so the boundary is stated.
W184 owns exactly: `KEY_INDENT`/`SECTION_INDENT`/`KEY_GAP`,
`kv_lines`, `_wrap_value`, `_team_detail` and its five `_detail_*`
builders, the listing-share and overflow-disclosure changes in
`_render_teams`, the member-detail paragraphs in `docs/BATON-WORK.md`,
`tests/work/test_w184_member_detail_table.py`, and the superseded
assertions listed above.


## Response to review `review-2026-08-19T20-57-39Z.md`

**R1 — partial poke telemetry rendered Python's `None`.** Accepted; a
real defect and a careless one. `answer_poke` lets the three context
counters be supplied INDEPENDENTLY, so an answer carrying only
`context_limit` is ordinary rather than exceptional — and my
`str(value)` turned the two it omitted into the word `None`, which is
an implementation spelling and not this surface's absent-value
vocabulary. It is exactly the substitution the rest of this block
exists to prevent: an operator would read `None` as something the
agent said.

The fix is to stop stringifying at the call site. `kv_lines` already
renders an absent value as `-`, so the raw value is handed to it and
each counter keeps its own key whatever arrives — what the agent
reported and what it left out stay separate facts. Nothing else moved:
no projection, transition, schema or protocol change, and `kv_lines`
itself is unchanged.

I checked the rest of the block for the same shape while I was there.
`str()` appears nowhere else in the detail builders; every other value
reaches `kv_lines` raw, so `None` cannot leak from any of them.

The reviewer's regression passes unedited.

- `tests/work/test_w184_member_detail_table.py` — **34 passed**.
- The adjacent suites (W93, W25, W137, W167, W110) — **394 passed**.
- The complete v11 gate, `just test-v11`, exits 0 on this tree:
  **2450 passed** (parallel), **40 passed** (serial), both bridge
  suites green.
