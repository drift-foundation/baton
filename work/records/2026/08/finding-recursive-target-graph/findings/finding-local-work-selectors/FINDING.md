# Finding: v11 Work cannot be identified compactly from the list view

## Observed

The second-trial release gate required commands containing canonical ids such
as:

```text
block work=8b92cb10-W11 on=8b92cb10-W27
```

The list view does not show those ids, and full authority-prefixed identifiers
consume substantial space even though every command already runs against one
explicitly selected authority. An operator cannot construct an exact graph
command using only the visible list rows.

## Confirmed decision — 2026-08-15

**Confirmed by Slawomir during the second v11 trial.** Every Work exposes its
generated authority-local short selector, derived from the permanent Work
sequence, for example `W11`. It is not a manually assigned abbreviation, title
alias, or mutable label.

The Work list has a compact `Id` column:

```text
Id   Title                                  Blk Dep
W11  Cut next v11 trial release              14   0
W27  Show live blocker and dependent counts   0   1
```

Commands accept either the full canonical Work id or the short selector:

```text
block work=W11 on=W27
block work=8b92cb10-W11 on=8b92cb10-W27
```

Resolution is always scoped to the one explicit authority opened by the
client. Like a short Git object name, a compact selector is a convenience over
canonical identity, not a second identity. A missing, malformed, or ambiguous
selector refuses by name; Baton never guesses from title, cursor position,
creation order, or a partial match that names more than one object. The current
`W<positive-sequence>` construction is unique and never reused within an
authority; the ambiguity refusal keeps the resolution contract fail-closed if
the selector space is ever extended.

JSON exposes both the canonical `id` and explicit `local_id`. Work details show
both. Repository records, cross-authority material, and other durable external
references retain the full canonical id when authority context is not already
fixed. The `Id` column grows to fit `W100`, `W1000`, and later values and never
silently truncates identity.

This is separate from merely showing the canonical id in Work details. It is
queued for the next immutable revision and does not rewrite the current trial.
