# Progress

Implementer-owned.

## Revalidation against the current tree — 2026-08-19

The observation holds. `top_tab_segments()` built the Inbox label as
`f"Inbox {box['total']}/{box['unseen']}"`, and the two counters do come
from independent derivations — `total` is every row, `unseen` is the
rows whose thread cursor has not passed them, and pokes and due trials
have no cursor at all, so they read unseen until they resolve. That is
exactly why the label almost always showed `n/n`: the kinds that can
diverge are the message-born ones, and the rest cannot.

Two things needed checking against W110, which landed since the finding
was written and is still in review:

- the label is now built inside `top_tab_segments()`, which brackets
  every tab; the marker goes INSIDE the brackets, so W110's rule that a
  narrow header draws whole labels or none covers the marker for free
  and it can never be the part that gets cut;
- W110 made the ACTIVE tab a highlight rather than a bracket. The
  finding requires the two cues to stay independent, and they are: the
  highlight is `A_REVERSE` applied by the painter, `*` is text from
  `owed_action`, and a test asserts an owed-and-not-selected Inbox
  shows the marker without the highlight.

W25's bold rule is untouched and NOT superseded — the finding
supersedes "only the `total/unseen` text". So an owed Inbox is both
bold and marked. That is deliberate redundancy in two channels, and the
text channel is the one that survives a terminal ignoring weight.

## What changed

`top_tab_segments()` appends `" *"` to the Inbox label when
`box["owed_action"]` is true, and nothing otherwise. One line, and the
comment beside it records why the counters left. Everything else the
finding names — the rows, the counters, `owed_action`, the JSON — is
untouched; `inbox_view()` is the same cached read it always was, so the
tab and the rows still cannot disagree.

`docs/BATON-WORK.md` now shows `[Jobs] [Teams] [Inbox *]`, states the
marker's whole vocabulary (not a count, not a severity, not an unseen
cue, not raised by attention), and says where the counts went.

## Superseded assertions edited

The finding supersedes the `total/unseen` TEXT and nothing else, so the
edits are narrow and each one keeps the property its test was
defending:

- W25's `test_the_inbox_label_carries_total_and_unseen` became
  `test_the_inbox_counts_stay_where_their_rows_are`. It still asserts
  the counters are derived and correct (`total == 3`, `unseen == 3`) —
  it now asserts they are NOT on the tab, which is the whole ruling.
- W17's header case asserted `Inbox 0/0` then `Inbox 1/1`, with a
  comment that "an absent counter and a zero one are different facts".
  That distinction is preserved verbatim in the new spelling: `[Inbox]`
  then `[Inbox *]`.
- W25's and W17's real-terminal cases, and W110's bar-text assertions,
  move to the new label.
- W136's two personal-header cases and `test_parity`'s console/JSON
  agreement asserted the counts appeared in the header. Each was really
  defending "the header is the VIEWER's own projection, not the team's"
  — so each now asserts the MARKER agrees with that viewer's
  `owed_action`, which is the same property through the new cue.

## Verification

- `tests/work/test_w167_inbox_owed_marker.py` — new, **24 passed**:
  zero, one and many owed actions (three genuinely distinct rows, one
  marker), no digit anywhere in the bar, seen-but-owed keeping the
  marker, unseen attention never raising it, another participant's
  owed action staying theirs, resolution lowering it, the label
  agreeing with `owed_action` at every step of a four-state sequence,
  the painted header, a timer `tick()` lowering it through the cache
  rather than needing a keystroke, widths from 10 to 60 with the label
  drawn whole or not at all, the counters still projected, the
  documentation, the two cues staying independent (an owed but
  unselected Inbox carries `*` and W25's bold but NOT the active
  highlight; selecting it adds the highlight and changes nothing
  else), and a REAL terminal showing `[Inbox *]` and then `[Inbox]`
  after the poke is answered.
- W25 **36 passed**, W17 **35 passed**, W110 **31 passed**.
- The complete v11 gate, `just test-v11`, exits 0 on this tree:
  **2416 passed** (parallel), **40 passed** (serial), both bridge
  suites green.

## Boundary with W110 and W137

Both are in review and share this uncommitted working tree; separating
them is a Git operation my role forbids, so the boundary is stated.
W167 owns exactly: the `" *"` branch in `top_tab_segments()`, the
`top_tabs()` docstring example, the Inbox tab paragraphs in
`docs/BATON-WORK.md`, `tests/work/test_w167_inbox_owed_marker.py`,
and the label-text edits in the W25/W17/W110/W136/parity tests listed
above.
