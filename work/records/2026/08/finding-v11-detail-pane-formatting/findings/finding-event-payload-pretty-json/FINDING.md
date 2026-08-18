# Finding: Event payload JSON is painted as one wrapped line

## Observed

`WorkTUI._event_lines()` currently appends `payload: ` followed by
`json.dumps(payload, sort_keys=True)`. Nested objects and arrays become one
long line, and the reader's generic wrapping obscures their structure.

## Confirmed decision — 2026-08-18

The Event reader keeps its human summary and then renders the complete payload
as JSON with exactly two spaces per nesting level. Keys remain deterministic,
Unicode remains readable, and JSON strings, booleans, numbers, nulls, arrays,
and objects retain their JSON spelling. The empty payload renders as `{}`.

`payload:` is a section label on its own line; the opening brace begins on the
next line. Each JSON logical line is supplied separately to the reader before
terminal-width handling. If a scalar line exceeds the pane, a visual soft wrap
preserves its leading structural indentation and gives continuations an
additional two-cell indent. Wrapping is presentation only and never changes
the projected payload.

The common typed labels above the payload remain concise and the complete
payload is never folded, summarized, or silently clipped. Reader scrolling,
focus, resize behavior, and continuation disclosure remain unchanged.

## Implementation revalidation — 2026-08-18

**Confirmed current-code facts.** W47 has landed and the Event index is now a
fixed-column table. The remaining defect is confined to the Event reader:
`_event_lines()` still appends one `json.dumps(..., sort_keys=True)` line and
`_paint_event_reader()` sends every logical line through a generic wrapper.
No authority or projection change is needed.

Two edge cases are part of the implementation boundary:

- `entry.get("payload") or {}` converts valid falsy JSON payloads (`null`,
  `false`, `0`, `""`, and `[]`) into `{}`. Only an actually absent payload may
  use the empty-object fallback; a present JSON value retains its type and
  spelling.
- the current wrapper gives every already-indented line one fixed four-space
  continuation indent. A deeply nested JSON scalar therefore loses its
  structural depth when it wraps. Continuation indentation is the logical
  line's existing leading spaces plus exactly two more cells.

Produce the payload block from deterministic
`json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)` logical
lines. Paint `payload:` alone, then the opening JSON line beneath it. Terminal
soft wrapping must preserve every displayed JSON character while adding only
the continuation indentation; it must not reserialize, summarize, fold, or
mutate the projected value.

## Revalidated acceptance boundary

- Exact logical-line tests cover an absent payload, `{}`, every falsy scalar,
  nested objects/arrays, Unicode keys and values, escaped strings, and stable
  key order.
- Reassembling the unwrapped JSON block parses to the original projected value.
- Wide and narrow reader tests prove structural indentation, a long nested
  scalar's continuation depth, clipped-tail disclosure, scrolling, and resize
  without omitted payload content.
- Common typed labels, references, newest-first index order, selection, focus,
  and Events paging remain unchanged.
- Reading, wrapping, scrolling, and resizing write nothing to the authority;
  JSON output and TUI rendering remain views of the same complete payload.
