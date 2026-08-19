# Progress — implementer

Work `b06383c8-W25`. State: **awaiting review**.

## Handover: what the impl2 route left, and what became of it

W25 was claimed by `baton.gemini` (seq 71), force-released after its
runner abandoned edits (75/76), and reassigned to `baton.impl` (80). I
claimed it at seq 82. The pass comment said "shared-tree partial changes
left for revalidation", and it is worth writing down exactly what those
were, because none of it is silently deleted:

- **`projection.teams()` / `projection.inbox()`** — present, and not
  usable as written. `inbox` scanned every pending obligation without
  scoping to the viewer's team, queried `trials.status = 'pending'`
  where the table stores `'open'` (so the due-trial branch was dead
  code), and reported `unseen` as a copy of `total` under a comment
  saying "This is a simplification. Real unseen status would require
  tracking." `teams` read the roster tables directly and did not resolve
  route coverage. **Outcome: superseded.** Both were rewritten; the
  originals are quoted here so the record shows what was replaced, and
  the two problems they exposed — viewer scoping and a real `unseen` —
  are the two things the new versions are most careful about.
- **The TUI shell** — a skeleton. `render()` had gained a second body
  ahead of the original: header, tab dispatch, and a verbatim copy of
  the caret/status block, followed by the whole original render. The
  three tab painters were `pass`. `breadcrumb_text` returned the tab bar
  instead of a breadcrumb. `[`/`]` were bound to tab switching, which
  collides with Work detail's own Messages/Events tab keys (W123).
  **Outcome: superseded.** The duplicated body is gone, the painters are
  real, and the key conflict is resolved in favour of the documented
  older binding.
- **The ruled decisions it encoded** — tabs first, identity right, the
  legacy counters removed — came from this FINDING, not from that code,
  and they are implemented as ruled.

Copies of both partials were kept outside the tree while working
(`/tmp/gemini_partial_projections.py`, `/tmp/gemini_partial_render.py`);
they are not evidence and are not committed. What matters is recorded
above.

## Revalidation (PLAN step 1)

- **Confirmed** — W17 landed and closed while this record waited, so
  "preserve W17's narrow correction and integrate it" is now a
  statement about shipped code rather than about in-flight work.
- **Confirmed** — W39 closed in the same interval and fixed
  `participant_actions` to honour `route_selected`. That matters here
  directly: Inbox is built ON that projection rather than deriving owed
  again, so the fix arrives for free and cannot drift.
- **Superseded** — this record predates W17's `[poke:N]` counter, so its
  "the former `[oblig] [park] [due]` counters are removed" now covers a
  fourth counter it never named. Removing them all is the ruled intent;
  the supersession is recorded in W17's own test module and dossier.

## What was implemented

**Two projections** (`src/baton_work/projection.py`):

- `inbox()` — owed rows come from `participant_actions`, the SAME
  derivation `wait` consumes, so a console and a runner reading one
  identity can never disagree about who owes what. Attention rows are
  unseen discussion in threads the viewer's team has joined. Actionable
  Work is deliberately excluded: Jobs owns Work, and one queue in two
  tabs makes "how much do I owe" unactionable. `total`, `unseen`,
  `owed`, and `owed_action` ride the result; `owed_action` is
  independent of seen state by ruling.
- `teams()` — the roster, with route COVERAGE (each route's role and the
  endpoints that reach it, W230 alternates included), the Work each
  member canonically holds, and the runner facts from their most recent
  poke answer. Nothing reads a process table; a member who has never
  answered reports `null`, which means unknown.

**Seen, honestly.** A thread carries a per-participant cursor, so an
attention row and any obligation born from a message are seen exactly
when that cursor passes the message. A poke and a due trial have no
message and no cursor: they report `seen: false` until they resolve,
because presentation inventing a cursor would be a UI deciding a fact
the authority does not hold. This is the one design decision here that
the FINDING left open, and it is the reason the ruled
"seen-but-still-owed" case is reachable and tested rather than
theoretical.

**Two CLI verbs**, `teams` and `inbox`, no operands, participant-relative
— the interface-parity requirement, in typed fields rather than glyphs.

**Projection version 12.1.** Additive by this file's own discriminator:
no existing response changes, no new action kind, so no readiness
consumer meets an entry it cannot read. Five existing tests assert the
published version string literally and were updated from `12.0` to
`12.1`; each also calls `require_version("12.0")`, which still passes
and is the compatibility property they exist to prove.

**The shell** (`src/baton_work/tui/app.py`): tabs lead the header, the
identity is right-aligned and drawn last so no width can clip it away,
the legacy counters are gone, `Tab`/`Shift-Tab` cycle, and the bottom
row became one shared painter because all three tabs end in it.
**Inbox** and **Teams** are full views with their own selection anchored
on canonical identities. W17's answer chooser and its authored-prose
runner are REUSED by both — Inbox answers owed pokes, Teams sends and
withdraws them — rather than re-implemented.

## Decisions taken here, for review

- **`Tab`, not `[`/`]`, switches top-level tabs.** `[`/`]` are Work
  detail's Messages/Events keys, documented and tested. One pair of keys
  meaning two tab sets at two levels is learned twice and confused
  forever.
- **The standalone poke view (`p`) is kept**, now as the poke RECORD —
  both directions, terminal history included — while Inbox owns the owed
  pokes and Teams owns sending and withdrawing. They are not duplicate
  authority reads: Inbox reads `participant_actions`, the record reads
  `pokes`, and they answer different questions. **Open for review:**
  whether the record should eventually fold into Teams entirely. I did
  not decide that unilaterally, because W17 is closed and signed off.
- **Inbox excludes actionable Work** — argued above and asserted by a
  test, including that `wait` still carries both.

## Existing tests changed, and why

Every change below is a contract this FINDING explicitly moved; none
weakens an assertion, and each kept its original question:

- `test_w74_header.py` (3) — its "identity plus live summary" premise is
  superseded; the tests now ask the same three questions of the new
  header. A dated supersession note heads the module.
- `test_w17_poke_visibility.py` (13 assertions) — the poke COUNT moved
  from `[poke:N]` to the Inbox; one helper, `poke_cue()`, is now the
  single place that knows where it lives. The module docstring carries
  the supersession.
- `test_parity.py` (2) — parity now runs against `inbox`, with the
  obligation half still checked against `obligations` so an aggregate
  cannot hide a disagreement; the parked half asserts the canonical
  summary and the Jobs row.
- `test_w136_participant_actions.py` (2) — the personal-vs-team question
  is asked of the Inbox counts.
- `test_tui.py`, `test_w71_navigation.py` (4) — header-shape assertions.
- Five version-literal assertions, as described above.

## Tests added

`tests/work/test_w25_jobs_teams_inbox.py` — 32 cases: tab order,
selected-tab distinctness without colour, right-aligned identity,
`Tab`/`Shift-Tab` cycling, the detail keys NOT switching top-level tabs,
narrow-width behaviour, removal of every legacy counter, Inbox
`total/unseen`, seen-but-still-owed bolding, unbolding when nothing is
owed, mixed poke/obligation/trial/message rows, due trials, Work
excluded from Inbox but not from `wait`, contextual navigation, the
shared answer chooser, responding, marking seen, selection stability,
Teams own-team default and cross-team browsing, roles/routes/canonical
claims, never guessing liveness, raw structured answer inspection,
poking and withdrawing, and CLI/JSON parity including that the Inbox
owed set IS the wake set. One real-pty run drives the tabs end to end.

One defect in my own code was found by these tests and fixed: the Inbox
selection anchor matched `None == None` against an attention row's null
action key, silently moving the operator's selection.

## Response to review `review-2026-08-19T13-18-01Z.md` (changes requested)

**R1 accepted; the defect was real and mine.** `_render_header` painted
the whole tab string with one attribute, so `owed_action` bolded Jobs
and Teams along with Inbox. The cue then said something is owed and hid
which tab holds it — the one question it exists to answer.

The header is now painted label by label, and only the Inbox label takes
the weight. `top_tab_segments()` returns the pieces and `top_tabs()`
joins those same pieces through one `TAB_GAP` constant, so the painted
columns and the joined string cannot drift apart; the selected-tab
brackets, the widths and the right-aligned identity are unchanged.

**The reviewer's second point is the more important one.** The focused
fake screen discarded `addnstr`'s attribute argument, so 70 passing
cases could not have caught this — the tests were blind to the whole
class. `AttrScreen` now records attributes and reconstructs row 0 as
`{column: (character, attribute)}`, which is what a human looking at the
top line actually sees. Four regressions ride on it:

- only the Inbox label is bold while an action is owed, and Jobs and
  Teams are not;
- nothing is bold when nothing is owed;
- the weight follows `owed_action` and not `unseen` in BOTH directions —
  reading the question does not quiet it, and answering it does;
- the painted bar starts with exactly `top_tabs()`, so the two spellings
  of the layout stay in step.

Verified against the pre-fix painter: it bolds `[Jobs]   Teams    Inbox
1/1` and the new check fails on it, while the fixed painter bolds
`Inbox 1/1` alone.

## Verification

- Round 1: `test_w25_jobs_teams_inbox.py` 32 passed;
  `test_w17_poke_visibility.py` 38 passed against the new shell; the
  complete gate 1988/40/ACP green.
- Round 2 (after R1): **74 passed** across both focused suites — 36 W25
  cases, four of them new and attribute-aware, plus W17's 38.
- The complete v11 gate, `just test-v11`, exits 0 on this tree:
  **1994 passed** (parallel, `-m "not serial"`), **40 passed** (serial),
  and the external ACP bridge acceptance green.

Nothing here was verified by inspection alone.
