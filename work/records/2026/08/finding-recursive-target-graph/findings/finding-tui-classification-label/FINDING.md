# Finding: confirmed-defect is rendered as `cnfrm`

## Observed

The first human v11 TUI trial renders the canonical classification
`confirmed-defect` as `cnfrm` in the `Cls` column. That abbreviation describes
the act of confirmation rather than the resulting classification and was not
clear to the operator.

## Confirmed correction

Render `confirmed-defect` as `defct` in the compact TUI presentation. Keep the
canonical authority value `confirmed-defect`, the `Cls` header, and every other
compact classification unchanged.

This is a separate queued Work item rather than an expansion of the completed
table-header case correction. The immutable `6d1b944` trial remains unchanged.

The live trial tracks this as v11 Work `26de18dd-W16` with discussion
`26de18dd-D16`.
