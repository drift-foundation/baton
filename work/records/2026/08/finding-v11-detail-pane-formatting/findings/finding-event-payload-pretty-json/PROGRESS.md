# Progress

**Implemented by `baton.claude` and returned to `baton.bug` for independent
review on 2026-08-18.** Presentation only: no authority, schema or projection
change.

## Revalidation

Both edge cases FINDING.md pins were reproduced in the tree before anything
changed:

- `entry.get("payload") or {}` collapsed every falsy JSON value. A payload of
  `null`, `false`, `0`, `""` or `[]` rendered as `{}` — the reader asserting an
  empty object where the ledger holds a value with its own type and spelling.
- `textwrap.wrap(line, width, subsequent_indent="    ")` gave every indented
  line a fixed four-space continuation. Measured directly: a scalar at six
  spaces of nesting wrapped to four, showing the value at a depth it does not
  occupy.

## What changed

- `payload:` is a section label alone on its line; the JSON begins beneath it
  from `json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)`,
  supplied one logical line at a time before any terminal-width handling.
- An `_ABSENT_PAYLOAD` sentinel distinguishes a missing key from a present
  falsy value. `None` cannot do that job, because `null` is itself a payload
  the ledger can hold.
- The typed labels read the payload's own fields, so they now run only when it
  IS an object. Reaching `.get` on a list or scalar payload would have raised
  while painting — the same defect the falsy collapse was hiding.
- A new `soft_wrap()` replaces the generic wrapper: continuations keep the
  logical line's own leading spaces and add exactly two cells.

## One thing worth the reviewer's attention

`soft_wrap` is a **generalization** of the wrapper it replaces, not a new rule
bolted beside it. The old code branched: two spaces for an unindented line,
four for an indented one. Under "own indent + 2" a top-level line still
continues at two and a two-space fact line still at four — byte-identical for
every human label line — while a JSON line at six or eight spaces finally keeps
its depth. That is why no existing Event-reader expectation needed changing,
and `test_the_wrap_generalizes_the_old_label_behavior` pins it so the claim is
checkable rather than asserted here.

It also breaks hard when a token has no space in it. A long JSON token must
still be shown whole across lines; truncating it would be the silent clipping
the ruling forbids.

## Regressions

`tests/work/test_w48_event_payload_json.py` (77 tests). The block: label alone,
two spaces per level, arrays and nested objects in their JSON spelling,
deterministic key order proved by rendering the same payload built in two key
orders, Unicode unescaped, JSON escapes intact and never splitting a logical
line. Absent versus falsy: the empty-object fallback for a missing key, and
each of `{}`, `null`, `false`, `0`, `""`, `[]`, `0.0` keeping its own spelling;
plus non-object payloads not crashing the typed labels.

Parity: reassembling the unwrapped block parses back to the projected value,
both for an invented payload and for one the authority actually wrote. Nothing
folded, summarized or clipped — every leaf value is present and no ellipsis
appears.

The wrap: structural depth preserved, continuation always two cells deeper at
six indent levels, the generalization above, no character dropped at any width
from 8 to 40, an unbreakable token shown whole, short lines untouched, and a
pathologically narrow pane still terminating.

The reader: structure painted, a narrow pane keeping depth AND disclosing its
clipped tail, scrolling revealing the rest with its `(cont.)` mark, a resize
repainting from the same logical lines with no character lost, the empty
reader unchanged, common labels still preceding the payload, references and
related rows surviving, and painting at four widths by three scroll offsets
writing nothing to the authority.

## Break-sweeps

| Reintroduced defect | Result |
| --- | --- |
| The old one-line `json.dumps` | 28 red |
| `payload or {}` collapsing falsy values | 6 red |
| The old fixed-indent `textwrap` wrapper | 1 red |
| Continuation ignoring the line's own indent | 8 red |
| Hard break dropping the remainder instead of continuing | 37 red |
| Typed labels reaching into a non-object payload | 14 red |

## Gate

`just test-v11`: **1359 passed**, 32 serial, ACP 40/40.

## One thing done outside this Work's scope, deliberately

While running the gate I found it red on
`test_w78_typed_timed_gates.py::test_closing_blocked_work_clears_its_terminal_gate`
— a regression the reviewer added to W78 while reviewing it. The defect is
real and mine: closing BLOCKED Work left a live gate episode on the terminal
row, because `phase` is NOT NULL and keeps its last value while the projection
derives terminal null from status. A closed row would have painted a `Wait`
cause and a running Held clock.

I fixed it in `close_work` rather than leaving the shared gate red under the
reviewer, strengthened W78's own phase/gate invariant (it closed only QUEUED
Work, which is why it missed this), and reported both on W78's thread. W78
remains with `baton.bug`; I did not take it back.

## Review round — the wrap must not trim JSON (2026-08-18)

The P1 is correct and was already fixed before this review reached me: I hit it
on the shared gate during another Work, repaired it, and reported it on T48.
The review was written against the tree as it stood before that. This round
verifies the repair properly rather than declaring it done, because "already
fixed" is the easiest thing to be wrong about.

### The defect, and the part I should have caught myself

`soft_wrap` broke at a space and then consumed it — `rstrip()` on the emitted
fragment, `lstrip(" ")` on the remainder. Ordinary display wrapping; wrong here,
because the ruling is that only the continuation indentation may be added and
every displayed character survives. A space inside a JSON string is DATA, so
`"alpha   beta"` came back as `"alphabeta"` and the reader silently rewrote a
value it existed to show faithfully.

It breaks AFTER the last space in the budget now, keeps that space on the line
it ended, and strips nothing from either side.

Worth recording plainly: I had a test for exactly this property and WEAKENED
it. `test_the_wrap_drops_no_character_at_any_width` originally compared the
reassembly for equality; when it failed I changed it to ignore spaces instead
of asking why a space had gone missing. That is accommodating a defect rather
than finding it, and it is why the review found this and I did not.

### Verifying it, this round

A one-off check of three hand-picked strings is the same mistake in a smaller
form, so the property is now checked over a broad sweep: ten awkward literal
shapes across nine widths, plus a deterministic 4,200-wrap sweep of generated
lines over repeated spaces, leading and trailing spaces inside strings,
all-space values, escapes, Unicode and unbroken tokens. Every case must
reassemble BYTE for byte after removing only the continuation prefix.

While writing it I got the harness wrong twice, in ways worth naming because
both would have produced a green test that proved nothing:

- measuring the continuation indent from the output. A fragment whose content
  begins with spaces is indistinguishable from indentation, so the measurement
  silently over-counts. The helper now states the contract's rule instead.
- computing the indent from the variable I generated the line with, rather than
  the line's actual leading run — which differ as soon as a generated body
  starts with a space. 20,011 apparent "failures" were my arithmetic; with the
  wrapper's own rule, 148,000 wraps came back lossless.

### One change beyond the repair

The review asks to retain the progress guarantee for pathological widths. It
was retained, but the sweep that removes the clamp HUNG rather than failing — a
guarantee whose only symptom is a freeze is one nothing can check. `room` is now
`max(1, …)`, so progress is structural: a future mistake in the clamp
arithmetic surfaces as a fragment too wide for the cell, which every caller and
test already asserts. Current output is unchanged, because with the clamp in
place `room` was never below one.

### Break-sweeps

| Reintroduced defect | Result |
| --- | --- |
| Trim at the break (the reviewed defect) | 106 red |
| Break BEFORE the space instead of after | 8 red |
| Progress clamp removed | 8 red — by assertion, previously a hang |

### Gate

`just test-v11`: **1565 passed**, serial **36 passed**, ACP **41/41**.

### One thing done outside this Work

The gate came up red on `test_status_refuses_a_stale_unix_socket_inode`, a
SECOND finding the reviewer added to W20 after I had passed it back. Real:
`_ready` for `unix_socket` stat-ed the path and checked the file type while the
http probe beside it makes a real request, so the two readiness kinds disagreed
about what readiness means. It now connects and closes. Fixed and reported on
T20; W20 remains with `baton.bug`.
