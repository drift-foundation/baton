# Separate Event metadata from its raw payload

## Observed — 2026-08-20

The Event reader presents its concise typed metadata and the complete raw JSON
payload as adjacent lines. Although `payload:` labels the second section, the
lack of vertical separation makes the JSON read like one more metadata field
and slows scanning between the human summary and audit record.

The existing `roles:` field is typed relationship metadata. `subject` means
the selected Work is the Event's direct subject; other values such as
`consumer`, `blocker`, `parent`, or `provider` explain why a relational Event
appears in this Work's history. This Work does not change those semantics.

## Confirmed decision

- Insert exactly one blank visual row between the final typed metadata row and
  the `payload:` section.
- Use spacing rather than a horizontal rule; it creates the boundary without
  spending width or introducing terminal-glyph compatibility concerns.
- Keep `payload:` and the complete two-space-indented JSON unchanged.
- The separator is presentation only: it does not alter Event projection,
  ordering, scrolling, clipping disclosure, or authority state.

## Acceptance boundary

- Events with only common metadata show one blank row immediately before
  `payload:`.
- Events with related Works, claim intervals, typed payload labels, or refs
  still show exactly one separator after the last such row.
- Narrow wrapping does not multiply or erase the logical separator.
- Continued/scrolled readers remain honest about their position and clipping.
- Event navigation remains read-only.
