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
