# Progress

## Step 1 — the marker is gone from both cells (2026-08-18)

`held_field` no longer prefixes `>`, and the Phase cell is
`phase_cell(...)` alone — `pickup_prefix` is deleted rather than left
returning a constant blank, because a function whose only job was the
marker is dead code once the marker is ruled out.

The trailing space went with it. A claimed row rendered `MM:SS ` purely
to align against the unclaimed `>MM:SS`; with no prefix, both forms are
the same shape and the column pads them. That is the supersession's
actual point: claimed and unclaimed now render IDENTICALLY in Held, and
`Current` — blank when nobody holds the Work — is the one cue.

Canonical projection is untouched. `current`, `claimed_at`,
`handoff_at`, `pickup`, readiness, waiting and parking are all
unchanged, and the JSON-carries-no-glyph check still passes.

## Step 2 — the suites that encoded the superseded presentation

Four suites asserted the marker. Each was inverted where the ruling
superseded it and left intact where it did not — the distinction
matters, because W65's other conclusions are still authoritative:

- **W65** (`test_w65_unclaimed_cue.py`) — the ruled state matrix now
  proves the marker is ABSENT across ready, passed, blocked, waiting,
  parked, claimed, released and terminal rows, and the released case
  additionally asserts `current is None`, which is the fact that
  replaced the glyph. The six-minute-invariance test keeps its subject
  and gains `>` to the things that must not appear.
- **W226** (`test_w226_held_pickup.py`) — timer ORIGINS are unchanged
  and still asserted: handoff while unclaimed, `claimed_at` once
  claimed, the falsifiable visible reset, a new interval per repass,
  and the cap. Only the spelling lost its prefix.
- **W47** (`test_w47_heartbeat.py`) — silence still never becomes an
  alert; the assertions that keyed on the trailing space now key on the
  absence of `!` and `>`.
- **Parity** — the branch requiring `>` on unclaimed Phase became a
  single assertion that NO row carries a marker on either surface.

Break-sweeps: restoring `>` in Held reds 5; restoring it in Phase reds
the parity suite.

## Not mine to fix — flagged rather than edited

`docs/BATON-WORK.md:222` still documents the retired glyph: that `>`
marks every open Work with no active claimant, and that an unclaimed row
reads `>MM:SS` since the committed handoff or `>-` when there is no
handoff to time. Every clause of that is now false.

The document belongs to W5 (`Rewrite public docs and architecture for
v11`), which is in review right now, and the ownership boundary ruled
during the route/current work says W15 does not edit it. Raised on the
thread instead, so the correction lands with its owner rather than
underneath an in-flight review.

## Evidence

- Gate: **1079 passed** + 5 serial + acp 36/36 on 32 cores.
- Break-sweeps: Held marker reds 5; Phase marker reds parity.
- Whitespace check clean.

## Step 3 — review round 1 (2026-08-18)

**The packaged proof.** `tests/work/test_w15_packaged_no_marker.py`
deploys the artifact, builds an instance through it, and drives it on a
real PTY with one handed-off unclaimed row and one claimed row — the two
renderings that used to differ only by the marker. The reviewer's point
is the right one: this marker lives entirely in presentation, so a
regression would reach an operator's screen without failing a single
unit test.

Three checks: the unclaimed row carries no `>`; no retired marker
appears anywhere in the drawn table; and drawing writes nothing to the
authority. The first guards against passing vacuously — it asserts the
claimed row NAMES its claimant and the unclaimed row does not, so the
absence of a marker is being read from genuinely unclaimed Work rather
than from a row that quietly got claimed.

Break-sweep at the packaged screen: restoring the Held marker reds 2,
and restoring the Phase marker reds the same 2.

**The stale prose.** Three descriptions asserted the opposite of their
own assertions — W226's module docstring still promising `>MM:SS`, a
Phase prefix and a claimed suffix; the overflow test still saying the
marker composes with the cap; and W65's module docstring still
presenting `>` as the ruling. All three now name the W15 supersession
and the bare timer, and say what survived it.

The parity comment is kept but reframed as explicit history, per the
review's condition. While doing that I removed the
`phase == phase_cell(...)` assertion by accident in the first edit and
put it back; the comment now also explains why the `lstrip` stays —
it TOLERATES a marker rather than asserting one, so the assertion below
it is what actually forbids the marker from returning.

### Evidence

- Gate: **1082 passed** + 12 serial + acp 36/36 on 32 cores.
- Packaged break-sweeps: each restored marker reds 2.
- Whitespace check clean.

No authority, projection, timer-origin, or phase behaviour changed.

## Reopened round — the typed, timed gate (2026-08-18)

Implemented by `baton.claude` and returned to `baton.bug`. This is the
reopened slice: not a rename, an authority change. Schema 20, projection 10.0.

### Revalidation against the tree

Every confirmed-fact claim in FINDING.md's "Implementation revalidation" held.
The authority stored the single `waiting` phase plus either the aggregate
`gates` condition or one obligation, and both named silences were real: the
obligation→gates retarget committed no event, and a displayed blocker closing
behind another changed `first_open_blocker` with no readiness or phase change.

### The shape

`wait_type`/`wait_obligation` are REPLACED, not supplemented, by one committed
gate episode on the Work row: `gate_kind` (`work`|`message`), `gate_work`,
`gate_obligation`, `gate_started_at`, `gate_seq`. The old pair said which
condition would wake the Work but never which gate was holding it or since
when — so the row could not explain its own clock, which is the defect. Keeping
both would have left two sources of truth for the same fact.

Selection is one function, `_displayed_gate`, and it returns the CURRENT gate
unchanged whenever that gate still holds the Work. That is what makes the
episode stable: the answer differs only when the gate genuinely differs.

The episode is committed by `_retarget_gate`, called from `_recompute_ready`
and from every claimant-releasing landing. It sits **outside** the
readiness-flip branch deliberately — the case the ruling names, the displayed
blocker closing while another gate remains, does not flip readiness at all. A
recompute that changes nothing writes nothing, so this is free.

### Three decisions the ruling did not pin

**Children are gates.** The pinned rule names "the oldest open blocker by
permanent creation order", which is the case it was written for. But
`_open_gates` counts open required CHILDREN as well as blockers, so a
child-gated parent is `block` and runs a clock. Leaving children out of the
selection would have produced a `block` row with an empty Wait cell and a
running timer — the exact unexplained clock this Work removes, reappearing in a
new place. One order runs over both kinds, so the displayed gate depends on age
and never on category. This is visible: the epic in the TUI fixture now shows
`Wait W3` and its title takes the truncation that any other cue would cause.

**The blocking obligation is recorded, not rediscovered.** A Work can carry
pending obligations that never blocked it — `request wait=false` creates
exactly that. So the message gate is set explicitly by the blocking request and
identified thereafter from the stored episode. Rediscovering it from the
obligations table passes every other test in this file and still gets the
answer wrong the moment a `wait=false` obligation coexists with a real gate;
that case is now covered directly, and the break-sweep for it reds.

**The last gate is cleared by the wake, not by the retarget.** When the final
gate closes, `_retarget_gate` deliberately leaves the episode alone: the sweep
at the end of that same transaction is about to wake the Work, and it needs the
gate it is clearing in order to name it. Clearing one statement earlier erased
that evidence and, for an instant, described blocked Work as blocked by
nothing.

### Projection 10.0 — both halves are breaking

`waiting` → `block` changes the phase VALUE SET, and `waiting_on` → `gate`
changes what the field answers. A 9.x client would have had to combine
`waiting_on`, `first_open_blocker` and journal timestamps to get what `gate`
gives directly — and could not get it at all when the displayed gate changed
inside `block`, because the authority committed that silently. The major moves
so a 9.x demand refuses cleanly. The summary counter `waiting` follows its
phase and becomes `blocked`.

The wake event carries `cleared_gate` — the gate that cleared, typed and
located — beside `gate_now`, the episode boundary. Naming the first one `gate`
would have read as the current one.

### Playback stays honest

A gate change inside `block` writes `gate_now`, never `phase_now`. Recording it
as a phase transition would fabricate a phase change that never happened, and
the Events playback would show the Work leaving and re-entering a phase it
never left. `test_a_gate_change_inside_block_is_not_a_phase_transition` pins
exactly that: the phase-interval count is unchanged and the `block` episode
stays open across the gate change.

### Regressions

`tests/work/test_w78_typed_timed_gates.py` (29 tests) walks the revalidated
acceptance boundary clause by clause: first dependency blocks/releases/starts;
a non-displayed dependency does not reset; closing OR removing the displayed
gate selects the next and resets; clearing the last queues and stops; a
blocking request enters `block M…` at publication; response and disposition
each queue or retarget with a new episode start; unrelated events
(heartbeat, message, priority, classification, refresh) do not reset;
claim/release/pass/queued/parked/terminal all render `-`.

Beyond the boundary: the two-unclaimed-rows observation reproduced and fixed;
an invariant that a visible timer implies a visible cause, driven over five
phases at once; the cue's `+N` on Work gates and its absence on Message gates;
child gates and the oldest-wins order across both kinds; the non-blocking
obligation cases; the wake payload; and a phase/gate agreement invariant driven
through every path that moves either.

The `unrelated events` cases differ in how load-bearing they are and the test
says so: `priority` and `classification` do stamp the Work row, so they catch a
retarget wired into the row-change path; `message` and `heartbeat` never touch
this row at all, so they guard a future change rather than today's code.

### Break-sweeps

| Reintroduced defect | Result |
| --- | --- |
| Episode restamped on every recompute | 1 red |
| Episode restamped on every row touch | 2 red |
| Cue reads the blocker list again | 4 red |
| Held falls back to the handoff origin | 5 red |
| Message gate rediscovered from the obligations table | 1 red |

The last one first came back GREEN, which is why the two non-blocking-obligation
tests exist: the reasoning behind recording the gate was sound but untested, and
untested reasoning is indistinguishable from a guess.

### Superseded expectations

A public phase rename supersedes every `waiting` expectation in the suite, and
FINDING.md authorizes it ("old projection spelling is not a compatibility
constraint"). 22 files: the phase literal, the removed columns, `waiting_on`,
the summary counter, the compact vocabulary, the version pins, and the wake
payload. Three needed judgement rather than substitution and each carries its
reason at the assertion:

- `test_w226_held_pickup.py` / `test_w65_unclaimed_cue.py` — the handoff timer
  origin they pinned is the defect. Rewritten to walk the new ruled states;
  `handoff_at` is still asserted present as history.
- `test_tui.py` / `test_parity.py` — the epic's `Wait W3` widens the cue column
  and the title truncates. Parity now compares the drawn title as the prefix it
  is; identities are never abbreviated and are still checked whole.
- `test_w25_real_cursor_keys.py` — it compares three screens for equality, and
  a `block` row now runs a live clock. The timer is normalized out rather than
  the test being made to race it.

### Gate

`just test-v11`: **1261 passed**, 32 serial, ACP 40/40.

One thing the reviewer should know about that evidence: another participant is
working in this same checkout (W101 is `active` on `baton.tune`). Files changed
under me mid-run — `tools/codex-event-bridge/src/config.mjs` and its guard in
`test_w4_v10_runtime_removed.py` were rewritten between two of my runs, and the
ACP suite grew from 38 to 40 tests. Nothing in that overlaps this Work's
surface, but the gate figure above includes their in-flight state.

## Review round — the terminal gate (2026-08-18)

The P1 is correct and was already repaired before this review reached me: I hit
it on the shared gate during W48, fixed it, and reported it on T78. The review
was written against the earlier tree. This round checks each of its conditions
rather than resting on the one test being green.

### The defect

`close_work` made the status terminal but left `gate_kind`/`gate_work`/
`gate_obligation`/`gate_started_at`/`gate_seq` on the row. Reachable through
the public contract, exactly as the review says: a route handler may close Work
while an independent blocker stays open. The terminal detail then projected
`phase: null` beside a live Work gate, and the row rendered a `Wait W…` cause
with a running Held clock — the `block iff gate` invariant broken at the one
boundary where the phase column stops being the phase.

### Each condition, checked

- **cleared atomically in terminal close** — one guarded call in the same
  transaction that ends the phase episode.
- **event evidence preserved** — the close event carries
  `gate_now: [{work, kind: null, …}]` beside its `phase_now`. Verified on a
  fresh authority, and now PINNED: nothing tested it, and the replay
  reconstructs nothing, so an unrecorded boundary is absent forever rather than
  derivable later.
- **not merely hidden in projection** — the projection is untouched; the stored
  row itself is empty afterwards.
- **the additive regression retained** — kept as written.

### Two things this round added

**A test for the evidence half**, and one for its opposite: a Work closing with
no gate must record NO boundary, because inventing one would put an episode
ending in the ledger for an episode that never existed. The sweeps show the
three halves are independently pinned — failing to clear reds 3, clearing
without recording reds 1, recording unconditionally reds 1.

**The schema comment was wrong in the other direction.** It said `gate_kind` is
"NULL exactly when the phase is not `block`". After this fix a Work closed while
blocked has `gate_kind` NULL while the `phase` COLUMN still reads `block` —
because it is NOT NULL and keeps its last value, which is precisely why the
projection derives the terminal null from `status`. The comment now says what is
true: NULL exactly when the Work is not blocked, closed rows included, and the
phase column cannot be the test for that. The review noted the row contradicted
the comment; the comment was the part that needed correcting.

### Break-sweeps

| Reintroduced defect | Result |
| --- | --- |
| Terminal gate not cleared | 3 red |
| Row cleared, no episode boundary recorded | 1 red |
| Boundary recorded even with no gate | 1 red |

### Gate

`just test-v11`: **1567 passed**, serial **36 passed**, ACP **41/41**.

## Review round — the retarget boundary (2026-08-18)

The P1 is correct and was already repaired before this review reached me: I hit
the reviewer's regression on the shared gate during W154, fixed it, and
reported it on T78. This round proves the conditions the review attaches to
that repair, one of which is a risk the repair itself creates.

### The defect, and the argument it overturned

`_sweep_wakes` retargeted the stored row from `M…` to `W…` and started a new
timer, but called `_retarget_gate(..., payload=None)`, so `_gate_now` had
nowhere to write. The row was right and the play-by-play lost the transition.

I had made that choice deliberately and defended it in a comment: the new gate
sits on the row with its own start instant, so no event seemed necessary. The
review's reasoning defeats it, and it is my own W47 principle turned back on
me — the row describes only the LATEST episode, so the boundary vanished the
moment the gate changed again, and since the replay reconstructs nothing an
unrecorded boundary is absent forever rather than derivable later. PROGRESS.md
had also claimed a gate change inside `block` writes `gate_now`, which was true
of every path except this one.

`_sweep_wakes` now takes the causing operation's payload; all five call sites
thread it. What did NOT change is the deliberate absence of a `wake` EVENT for
the retarget — one whose from and to are both `block` would be a false
actionability signal — and `phase_now` is still absent, so no phase transition
is fabricated. That separation is exactly why `_gate_now` exists apart from
`_phase_now`; the shape held up, and the mistake was choosing not to use it.

### The condition the review attaches, which is the repair's own risk

"prove that final-gate clear still records exactly one honest boundary rather
than duplicating or fabricating one." That is precisely what threading the
payload makes easy to get wrong: the clearing path could now write the boundary
twice, once onto the response and once inline on the wake, leaving a replay
that sees one episode end at two sequences.

It does not, and that is now pinned rather than observed. Two tests count the
boundaries after a final clear — one for `respond`, one for `dispose` — and
require exactly one, on the `wake`. The wake is the honest place: it is the
transition that DID make the Work actionable again, unlike the same-phase
retarget. A sweep that passes the payload into the clearing path reds both.

### Also covered

Disposal, which the reviewer's test does not reach. A boundary recorded for
`respond` and not for `dispose` would be a hole shaped exactly like the one
just closed.

### Break-sweeps

| Reintroduced defect | Result |
| --- | --- |
| The retarget loses its payload | 2 red (respond and dispose) |
| The final clear also writes onto the causing event | 2 red |

### Gate

`just test-v11`: **1608 passed**, serial **37 passed**, ACP **41/41**.
