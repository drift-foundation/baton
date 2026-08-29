# Surface v12 Work labels in the TUI

## Status

Approved implementation cut, ordered after W29401.

## Parent and decision authority

This child was decomposed from W28880. The approved contract and chronological history are in `work/records/2026/08/finding-v12-work-tags/FINDING.md`. It consumes the authority cut W29400 and protocol/CLI cut W29401 without redefining their semantics.

## Confirmed boundary

- Work detail renders the normalized sorted label set in a dedicated, wrapped `Labels` field with an unambiguous empty state consistent with current detail conventions.
- A labels column may be added to wide Work tables only if the current width budget supports it. It is optional and must be dropped before operational identity, status/phase, route/handler, blockers, or other action-critical columns.
- Active positive and exclusion filters remain visible in the TUI so a narrowed result set cannot be mistaken for the complete Work set.
- TUI input and display use exact normalized Work-label semantics from the protocol layer; the TUI does not add fuzzy matching, OR, inheritance, or local-only interpretation.
- Labels are metadata only and receive no scheduling, readiness, route, or attention styling semantics.

## Host boundary

Implementation must revalidate the canonical v12 TUI after W29401. If the Work list/detail/filter host is still incomplete, record the exact unavailable surface and park or split it rather than create a parallel UI state model.

## Acceptance and regression matrix

- Detail covers empty, one, many, maximum-length, and wrapped label sets.
- Wide tables show labels when space permits; progressively narrow widths retain operational columns and never corrupt ANSI-aware measurement or truncation.
- Positive, exclusion, and mixed active filters are disclosed and round-trip through the protocol semantics.
- Keyboard focus, selection, refresh, and resizing remain stable while labels or filter disclosure change.
- Existing unlabeled Work views remain readable and no Thread/OCI label vocabulary leaks into the Work UI.

## Non-goals

No label editor, autocomplete registry, label coloring taxonomy, fuzzy finder, scheduler action, or OR query builder is approved by this cut.
