# Ruling — draft glyph

**Decision (Slawomir, 2026-08-09): approved.** Use `✎` for a retained draft,
with lowercase `d` only when the terminal cannot render the UTF-8 glyph as one
display cell.

## Recommendation: `✎`

Use the one-cell pencil mark:

```text
✎  08-09 23:34  to baton.reviewer  Subject being drafted
```

It communicates “being written” without implying that anything was queued,
claimed, delivered, or completed. It is visually distinct from the existing
state vocabulary:

- `•` / `○` — inbound unopened/opened obligation;
- `▷` / `▶` — outbound queued/picked up;
- `✓` — finished;
- `!` / `N` — notices.

The renderer must prove `✎` occupies one terminal display cell before using
it. On a non-UTF or incompatible terminal, use lowercase `d`. Uppercase `D`
is deliberately not the fallback because it is the destructive discard-draft
command.

## Alternatives

- `◇` — clearly nonterminal and visually light, but does not naturally mean
  “draft” without consulting Help.
- `d` — maximally portable and explicit, but brings a letter back into the
  cleaner symbolic status column.

Avoid `*` because that already means an unopened obligation owed by me; avoid
`…` because it already denotes deep thread nesting and may read as merely
truncated; avoid either outbound triangle because a draft has not reached the
authority.

Reviewer recommendation: choose `✎`, with `d` solely as the established
encoding fallback.
