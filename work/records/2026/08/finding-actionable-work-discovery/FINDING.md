# Make all participant-actionable Work discoverable

## Confirmed 2026-08-27

The Jobs tab does not report the total number of Jobs awaiting the current
participant, and the bounded containment tree gives no reliable cue when an
actionable Job is nested below the visible levels. Operators can therefore
know neither how much Work awaits them nor where a deeply nested item lives.

## Decision

Expose one participant-relative actionable-Work projection derived in the
same authority snapshot as the Jobs rows. A Work is actionable for the viewer
when it is open, ready, queued, unclaimed, and its CURRENT Route resolves to
that participant. Blocked, parked, terminal, already claimed, and merely
planned `Next` destinations do not count. The header total counts each Work
once regardless of how many visible ancestors roll it up.

The Jobs tab reports the total, for example `[Jobs 6]`. Every visible tree row
also exposes a textual `Mine` cue over its entire containment closure:

- `me`: the row itself is actionable;
- `+N`: N actionable descendants;
- `me+N`: both the row and N descendants; and
- blank: nothing actionable in that subtree.

The authority computes descendant counts beyond the TUI's display-depth
limit; the client never infers a zero from omitted descendants. Styling may
reinforce the cue but never carries its meaning alone.

Provide a flattened “Awaiting me” Jobs view listing every matching Work
regardless of containment, with its complete breadcrumb. Opening a result and
returning restores that filtered view. The ordinary containment tree remains
available and unchanged.

On a shared Route the projection means “available to this participant,” not
exclusive assignment or several pickup obligations. Documentation must state
that distinction. Directed message obligations remain Inbox concerns, member
pickup health remains a Teams concern, and neither is folded into the Jobs
count.

## Projection boundary

At minimum the one-snapshot response carries a unique
`actionable_for_viewer` summary count and, per displayed Work,
`viewer_actionable` plus `actionable_descendants`. These are derived current
facts, not stored workflow state. A projection-version change may be required;
no database schema is justified merely to render them.

## Open implementation details

Reviewer research must select the flattened-view key/command, zero-count and
narrow-layout spelling, breadcrumb representation, paging behavior, and exact
projection ownership while preserving the confirmed counting semantics.

## Reviewer specification — 2026-08-27

Research and the focused baseline are recorded in
`evidence/reviewer-research-2026-08-27.md`.

**Observed:** the bounded `tree` projection cannot locate queued actionable
Work below its three displayed levels. `active_trails` pierces that bound only
for claimed Work. Search requires a title/id query and does not represent the
participant's complete claimable set.

**Confirmed distinction:** the existing bold-Title predicate is not the new
counting predicate. Bold also covers the viewer's held claim and directed `@`
obligations; W26328 counts only open, ready, queued, unclaimed Work whose exact
current Route resolves to the viewer. Planned Next and all Inbox/Teams action
classes remain excluded.

**Proposed projection:** derive the claimable set, its unique total, every
displayed row's self membership, and complete descendant roll-ups in one
snapshot with fixed statement cost. Publish `actionable_for_viewer`,
`viewer_actionable`, and `actionable_descendants` on the Jobs tree/home
surface, including active-trail rows. Add a paged `actionable-work` read across
all owning teams, ordered by canonical `WORK_ORDER`, with complete structured
breadcrumbs. This is additive projection 12.7 and needs no schema change.

**Proposed interaction:** always spell the global count, including `[Jobs 0]`;
add a whole, natural-width, non-truncating `Mine` column with blank/`me`/`+N`/
`me+N`; and use `m` to open the flattened `Awaiting me` Jobs view. Flattened
breadcrumbs use the existing ` > ` grammar and soft-wrap completely. Paging is
100 by default (accepted 1..500), with opaque continuations; Enter or claim and
Back preserve the filtered view's page and id selection.

**Supersession boundary:** W2938 remains authoritative that pickup lateness is
one participant obligation on Teams, never N Work alerts. W26328 supersedes
only W2938's horizontal “no replacement” statement: `Mine` is an availability
locator, not `Claim`/`Pickup`, and must not depend on `member_pickup`, capacity,
or overdue time.

**Open for approver:** confirm the proposed names, key, exact zero/narrow
spelling, all-team flattened scope, complete wrapped breadcrumb, paging, and
the bounded projection ownership above before implementation.

## Approved implementation contract — 2026-08-27

The reviewer specification is approved with one deliberate scope correction.
Projection 12.7 carries the participant-relative actionable total, row facts,
complete descendant roll-ups, and the paged `actionable-work` read without a
database schema change. The TUI always spells the total, including `[Jobs 0]`;
`m` opens the all-team `Awaiting me` view; entries carry complete wrapped
breadcrumbs; and paging, navigation restoration, current-Route resolution,
shared-route meaning, and the W2938 separation apply as specified above.

The `Mine` column is mandatory only on the ordinary Jobs containment tree.
Its whole blank/`me`/`+N`/`me+N` value remains non-truncating there, but the
column is not added automatically to `Awaiting me`, search, dependency graphs,
or every other specialized table that happens to render Work. In particular,
`Mine` would be redundant in a view whose membership already means actionable
for the viewer and would unnecessarily consume scarce horizontal space.
