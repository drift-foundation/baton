# Show only meaningful Event relationships

## Observed — 2026-08-20

Every row in a Work's Events tab is already selected because it is related to
that Work. The reader nevertheless renders `roles: subject` for ordinary
direct Events. That line merely restates why the Event is on the screen and
uses protocol vocabulary that looks like a member role.

The typed relationship itself is not redundant in the projection. Cross-linked
Events use values such as `consumer`, `blocker`, `parent`, or `provider` to
explain why an Event primarily involving another Work appears here.

## Confirmed decision

- Preserve the canonical `roles` array and all Event relationship semantics in
  JSON/API output.
- In the TUI Event reader, omit the relationship line when the only value is
  `subject`.
- For one non-default value render `relation: <value>`.
- For multiple meaningful values render `relations: <comma-separated values>`.
- Do not display `subject` alongside a meaningful non-default relationship; it
  is the implicit baseline, not additional operator information.
- This is presentation-only and does not change Event membership, ordering,
  payloads, related-Work labels, or authority state.

## Acceptance boundary

- Direct create, claim, pass, close, and other subject Events show no redundant
  relation row.
- Dependency, parent, provider, duplicate, and other cross-linked Events name
  their meaningful relationship.
- Multiple meaningful relationships remain visible and deterministic.
- Narrow wrapping and scrolling retain the label and all values.
- JSON projections retain their complete typed `roles` array unchanged.
