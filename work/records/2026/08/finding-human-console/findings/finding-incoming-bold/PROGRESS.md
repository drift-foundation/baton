# Progress — incoming work is bold until handled

Implementer journal. The reviewer owns FINDING.md and PLAN.md.

## What shipped

One predicate and one style name, both in the renderer:

- `render.row_is_owed(row)` — the rule, readable and assertable without a
  screen.
- `render.STYLE_OWED` — emitted by `render_styled` for the screen rows whose
  list row is owed, via `_owed_screen_rows`, which mirrors
  `_selected_screen_row` exactly so the emphasis and the selection stripe
  cannot land on different rows.
- `driver` maps it to `curses.A_BOLD` and ORs it into all three blit branches
  rather than adding a fourth.

Nothing else moved. No core, protocol, schema, CLI, delivery, claim or receipt
change; the renderer reads rows the model already loaded.

## Decisions

**Composed, not exclusive.** `STYLE_OWED` is added to the style set beside
`STYLE_SELECTED`, and the driver ORs the attributes. The alternative — a style
that wins an either/or — makes the unread mark vanish under the cursor, which
is the specific failure the ruling calls out ("moving the cursor over an owed
row must not make the unread emphasis disappear").

**`claimed` stays owed.** Opening a message is not answering it. Clearing the
mark on claim is the obvious first cut and it would tell the human their work
was done the moment they looked at it.

**Damage is orthogonal.** `_status_glyph` lets `damaged` override the glyph;
`row_is_owed` deliberately does not. A damaged incoming row that is still
pending is still my move, arguably more so.

**Unknown states get nothing.** Only `pending`/`claimed` are owed and only
`seen` clears a notice. An unrecognised store state is exactly where a guess
would be wrong, and `exceptional_badge` already says so in the glyph column.

## Mistake made and caught by a test I wrote

The first version of the predicate was "not outbound, and pending or claimed".
It read `direction` and `row_type` with `.get(...)`, and SENT rows carry
NEITHER field — they are a different row shape rendered by `_sent_pane`. So
every row in the sent list looked like unanswered incoming work and the whole
outbox went bold: emphasis on every row, which means emphasis on nothing.

`test_outbound_rows_are_never_owed` caught it because it asserts in the SENT
view specifically. The rule is now DEFAULT-DENY on identity — a row is
emphasised only if it says what it is — and the table test carries the
no-fields row as an explicit case so the shape cannot be forgotten again.

I also shadowed the existing `_packaged_console` helper by appending a second
function with the same name and a different signature, which broke ten
unrelated packaged PTY tests until I noticed they were failing for my reason
rather than their own. Appending to a long test file is not free; the name was
already taken and I did not look.

## Evidence

`tests/tui/test_tui_render.py`, eight tests — pending owed, claimed still
owed, replied and closed not owed (with an untouched control so the rule is
shown to have cleared those two rather than stopped emphasising anything),
unseen notice owed and seen notice not, outbound never owed, selected row
keeps its emphasis, no authority write, and the rule table itself.

The no-write tripwire compares the full public read-only `dump()` before and
after three render+refresh cycles — not a spot check, so a receipt, a claim or
any transition introduced by drawing shows up. It reads the authority the way
every other reader reads it and never opens the database.

`tests/tui/test_tui_pty.py::test_owed_rows_are_bold_on_the_packaged_console`
is evidence 8: it drives the rebuilt `bin/baton-tui` over a real PTY, parses
SGR 1 runs out of the transcript, and asserts the owed subject is bold while
an already-closed subject in the same transcript is not — then answers it out
of band, relaunches, and asserts the emphasis is gone. `_bold_text` treats 0
and 22 as bold-off and deliberately does NOT treat 7 as a reset, because a
selected owed row is drawn bold AND reversed.

Deliberate breaks, each failing a NAMED test:

- `claimed` dropped from the owed states → `test_a_claimed_incoming_row_stays_owed`
  and the rule table.
- Emphasis suppressed on the selected row →
  `test_the_selected_row_keeps_its_owed_emphasis` and three more.
- Driver stops translating `STYLE_OWED` to `A_BOLD` → ONLY the packaged PTY
  test fails; every pure renderer test still passes. That is the exact gap
  evidence 8 exists to close, and it is worth stating plainly: the style set
  can be perfectly correct while the screen shows nothing.

Focused suites on the final bytes: `tests/tui` + `tests/packaging` 1630
passed; the documentation and extraction-purity gates 28 passed. The complete
release gate was NOT run — the reviewer runs it once on the combined candidate.

`bin/baton-tui` rebuilt (`24f08cb1c73ac0ecbe4108e24c4926dc7c2690e35bbc1626652440543361e04a`).
`bin/baton` is byte-identical to before this change, as it must be: the agent
artifact carries no console code.
