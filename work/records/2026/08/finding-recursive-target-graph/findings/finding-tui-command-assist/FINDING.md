# Finding: the v11 command bar provides no context-sensitive assistance

## Observed

The v11 TUI exposes the full operation language through `:`, but presents an
empty input row. Operators must already remember command names, exact parameter
names, required versus optional inputs, and accepted values. The second trial
made even a basic dependency operation require instructions outside the TUI.

## Confirmed decision — 2026-08-15

**Confirmed by Slawomir during the second v11 trial.** The command bar provides
context-sensitive assistance as the operator types:

- after `:bl`, show command names beginning with `bl`;
- after a complete `block` plus a space, show its arguments, including the
  required `work=` and `on=` keys;
- as valid keys are supplied, update the assistance to reflect what remains;
- when a parameter has a closed value vocabulary, show the relevant values as
  that parameter is entered; and
- show the assistance on the right of the command input when space permits,
  without making typed text ambiguous or invisible.

The assist data comes from the same declarative command specification used by
the accepted key/value parser. Help text and executable grammar must not drift
into separately maintained truths. Assistance is read-only UI: typing,
completion display, and validation hints do not open an authority transaction,
mark messages seen, or mutate Work.

The compact fallback at narrow widths remains an implementation-review detail,
but the feature may not silently disappear or truncate the operator's input
into ambiguity. Tab completion and dynamic authority-value suggestions are not
yet part of this ruling.

This feature depends on the key/value command grammar. It is queued for the
next immutable revision; the current trial remains unchanged.
