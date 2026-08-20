# Omit unpublished member logs

## Observed — 2026-08-20

In the Teams member-detail table, every configured participant currently
shows:

```text
Log  not published — this runner's adapter has published no log locator
```

The repeated sentence consumes a wide row without giving the operator a
locator or an action. It makes the table larger while every member says the
same thing.

## Confirmed decision

- When a runtime adapter publishes a `log` fact, keep the `Log` row with the
  exact locator, source, and observation age.
- When no `log` fact exists, omit the `Log` row entirely. Do not guess a path
  and do not replace absence with explanatory boilerplate.
- If no operational facts remain, the existing key/value renderer may omit
  the empty Operational diagnostics section as it already does for every
  empty section.
- This is presentation only. Runtime facts, adapter contracts, projections,
  poke responses, and Teams actions do not change.

This explicitly supersedes the missing-log presentation rule in
`work/records/2026/08/finding-teams-member-detail-table/FINDING.md`; the
published-log rule remains authoritative.

## Acceptance boundary

1. A member with a published log fact still shows its exact locator, source,
   and age.
2. A member without a log fact has no synthetic `Log` row and no `not
   published` sentence anywhere in its detail table.
3. Mixed members render independently; one participant's locator never leaks
   into another participant's details.
4. Wide, narrow, and truncated detail layouts remain aligned and honest.
5. Focused W184/Teams tests and the full v11 gate pass before independent
   review.
