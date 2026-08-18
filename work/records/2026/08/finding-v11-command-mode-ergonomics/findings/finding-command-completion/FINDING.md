# Finding: command mode hints do not complete canonical input

## Observed

The command assistant can display matching verbs, keys, and closed-vocabulary
values, but the operator must still type every character. Long outcome and
classification values are error-prone even when the intended unique prefix is
already clear.

## Confirmed decision — 2026-08-18

Tab turns the existing context-sensitive analysis into conservative editing:

- a unique command prefix completes the command and a following space;
- a unique operand-name prefix completes through `=`, so `ou<Tab>` in a
  `close` command becomes `outcome=`;
- a unique closed-vocabulary value prefix completes the full canonical value
  and a following space, so `outcome=sat<Tab>` becomes
  `outcome=satisfying ` and `outcome=non<Tab>` becomes
  `outcome=non-satisfying `;
- with multiple candidates, Tab extends only their common prefix. If that
  makes no progress, the existing hint area lists the candidates; a repeated
  Tab does not silently choose one; and
- with no candidate or malformed context, the buffer is unchanged and the
  canonical diagnostic remains visible.

Completion uses the same quote-aware partial-token analysis and declarative
grammar as parsing and assistance. It replaces only the live token, preserves
all earlier text and quoting, never expands the shell, and never reads the
authority. Full spellings remain mandatory at execution; shorthand is an input
gesture, not accepted grammar. Dynamic selector/path/identity completion is out
of scope for this slice.
