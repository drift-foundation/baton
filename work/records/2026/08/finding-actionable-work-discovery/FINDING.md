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

## 2026-08-28 independent review

**Confirmed P1:** The approved opaque continuation was implemented as a
positional integer offset into the current actionable set. A claim or routing
change that removes an earlier row between pages shifts every later row left,
so the next page starts too far forward and silently skips still-actionable
Work. This directly defeats the flattened view's discovery guarantee under the
shared-route race it is designed to expose. The CLI grammar and documentation
also expose the cursor as an integer (`after=25`) rather than an opaque token.

**Confirmed P2:** When the mandatory `Mine` column makes the ordinary table too
narrow, the refusal's calculated `need N cells` omits the Mine allocation.
The table correctly refuses instead of clipping, but it tells the operator to
widen to a width that can still be insufficient.

## 2026-08-28 — the reviewed defects, corrected

**Confirmed corrected — the continuation is a POSITION and never an offset.**
`next_after` was `start + len(page)` and the next page was `rows[start:start +
size]` of the actionable set as it stands at that later moment. The two are
not the same set. On a shared Route another handler winning a claim between
two pages is ORDINARY, and every row after the departed one then slides one
place forward — so the second slice begins one row too late and the Work that
crossed the boundary appears in no page at all. The reviewer's reproduction
walks it exactly: W2/W3 read, W2 claimed, `after=2` returns only W5, and the
still-actionable W4 has no locator anywhere. That is the one promise this verb
exists to keep, so the representation was never the point — the arithmetic was.

A keyset over the canonical order asks "after THIS position" instead. A
removal before the cursor changes nothing, and an arrival before it is already
behind the cursor and cannot be handed back twice. The one case a cursor
cannot follow is a row whose own rank changes across the boundary — it moved,
so continuing past it would mean something different — and the deliberate
refresh the contract already names is what that is for.

**Confirmed decision — the canonical order had to be made TOTAL first.** A
cursor compares positions, so two rows the order calls equal are two rows a
page can skip or repeat. `WORK_ORDER` stops at `created_seq`, and no mint
produces a tie today only because the identity is minted FROM that sequence
(`…-W{seq}`). That is a property of how ids happen to be spelled, and the
cursor depends on the ordering — so the identity is named as the final
tie-break in `WORK_ORDER_TOTAL`, which refines the canonical order and can
never reorder it, and the requirement stops being a coincidence.

**Confirmed decision — a token this authority did not mint is REFUSED.** The
tempting alternative is to treat an unreadable cursor as "start at the
beginning". That is the same defect wearing different clothes: the client
believes it has walked past a boundary it has actually been sent back behind,
and the Work between them is reported twice while the client is told nothing.
The scheme tag is checked first, so a later position shape refuses an old
token instead of misreading it as the new one.

**Confirmed corrected — the too-narrow refusal states a width that works.**
The refusal itself is right: identities are never clipped into ambiguity. The
number beside it was assembled by hand from `id_width`, while the judgment
that produced the refusal was made against the whole leading allocation —
which since this Work includes the mandatory `Mine` column and its separator.
So the single action the message asks for produced the same message again,
which is worse than printing no number at all, because an operator follows it.
The minimum is now derived from `layout_fits`' own expression against the same
lead that judgment was given, and it is EXACT rather than merely sufficient: a
number safely above the requirement would satisfy the review's letter while
telling an operator to surrender cells the table does not need.

**Confirmed scope — the refusal sentence itself still truncates on a very
narrow terminal, and that is pre-existing and untouched.** Below about
twenty-one columns `addnstr` cuts the message, and at the widths where the
number is on screen at all it is now the right number. Widening the message,
or wrapping it, is a presentation question this Work did not open and does not
own; it is named here rather than quietly fixed or quietly ignored.

## 2026-08-28 — independent re-review

**Confirmed P1:** `_cursor_position` accepts any well-shaped `w1` position and
does not bind it to a Work or current canonical-order position in this
authority. An invented token with impossible ranks and a nonexistent id is
accepted and returns an empty page while Work remains actionable. It also
prevents a changed cursor-row rank from producing the documented refresh
refusal. Exact output and durable reproduction are in
`review-2026-08-28T11-07-40Z.md` and
`evidence/w26328-review-forged-cursor.py`.

## 2026-08-28 — the re-review's [P1], corrected

**Confirmed corrected — shape is not provenance.** The first correction
established that a continuation DECODES and carries this scheme, recorded a
decision that a token this authority did not mint is refused, and then did not
check that it was minted here. A client could compose a well-formed token with
impossible ranks, a future sequence and an id belonging to nobody; every real
row compared as "at or before" it, and the page came back empty while Work was
still actionable. That is the same discovery failure the offset arithmetic
caused, reached through the cursor instead — and the decision I wrote was true
of the scheme tag and false of everything the token actually says.

The token is now bound to its Work inside the read snapshot: the named row must
exist, and its CURRENT total-order position must be the one the token names.

**Confirmed decision — the binding is over `work`, not over the actionable
set.** This is the part that could quietly undo the first correction. A claim
or a reroute on a shared Route moves a row out of the actionable set WITHOUT
moving it in the canonical order, so continuing after it means exactly what it
meant — and that is the ordinary case this whole feature exists for. A binding
written against claimability would satisfy every forged-cursor case and refuse
the one the first [P1] was about, so a mutation makes exactly that mistake and
is caught by the ordinary continuation cases rather than by the new ones.

**Confirmed consequence — an ordinary claim of a BLOCKING row now refuses.**
The blocking preference is part of the canonical order and one of its clauses
is `handler_team IS NULL`, so a cursor row that was holding somebody up ranks 0
while unclaimed and 1 once claimed. On that one kind of row a perfectly
ordinary shared-route claim genuinely moves the position, and the continuation
is refused with the refresh named. This is a real narrowing of the inter-page
claim case, and it is a narrowing toward the honest answer: continuing past a
position a row no longer occupies skips or repeats the rows in between, and a
client cannot detect either. The deliberate refresh the contract already names
is now reached as a FACT rather than as a judgement about when to use it.

**Confirmed scope — a Work leaving the set entirely does not move it.**
Closing the cursor row keeps its position when it has no open dependents, so
the continuation stays valid. Refusing there would cost the pages after it for
a reason no client could act on, and it has its own case because it reads like
it should refuse and must not.

## 2026-08-28 — independent third review

**Confirmed P1:** the corrected continuation is bound to an existing Work and
its current canonical-order position, but not to the participant-relative view
that produced it. With two disjoint Routes, a real continuation returned to
Grace is accepted by Ada's read and places Ada after a Work that was never in
Ada's result. Ada receives an empty page while two Work items remain
actionable. This is not a hand-built-token concern; the token is returned by
the same authority and passed unchanged.

Bind the continuation to its viewer/query scope as well as its Work position,
while preserving the whole-`work` position check that permits a same-view
cursor row to leave the actionable set without invalidating later pages. Exact
evidence and the required regression boundary are recorded in
`review-2026-08-28T11-39-31Z.md` and
`evidence/w26328-review-cross-view-cursor.py`.

## 2026-08-28 — the third review's [P1], corrected

**Confirmed corrected — a continuation names WHOSE question it continues.**
The `w1` token carried only a position in the canonical order, and that order
is a fact every viewer shares. `actionable-work`, however, answers a
participant-relative question — so a real, authority-minted, unedited cursor
from one participant's page was a valid cursor in another's, and every row
before that position dropped out of their answer. Two disjoint Routes are the
whole reproduction: Grace's page-one cursor names a Work that sorts after
everything Ada can claim, and Ada reading through it gets an empty page while
her own Work is still waiting.

The row binding from the previous round fixed an INVENTED position and left
this untouched, because nothing in it is invented. The token now carries the
resolved viewer and `_cursor_view` compares it.

**Confirmed decision — the scheme moves with the shape.** A `w1` token names a
position and no viewer, so reading one as current would take the participant
binding off exactly the tokens that predate it — the population the binding
exists for. `w2` is a different tag as well as a different arity, and a
mutation asserts the tag actually moved.

**Confirmed decision — the view check runs BEFORE the row is looked up, and it
does not say "refresh".** A cursor belonging to another participant is not a
snapshot that moved. Telling its holder to refresh would send them round a
loop that cannot terminate: their next page would be this page again. The two
refusals name two different mistakes, and a case asserts the wording stays
apart.

**Confirmed scope — the binding is on the VIEW, not on claimability.** A cursor
row that merely stopped being actionable FOR THE SAME VIEWER still continues,
which is what the first correction exists for and the regression a view
binding most easily causes. It is asserted on both sides: in the suite and in
the corrected evidence.

## 2026-08-28 — independent final review

**Confirmed corrected and signed off.** The `w2` continuation binds the
participant-relative view before checking its whole-`work` row position. A
genuine cursor from a disjoint participant Route refuses without misleading
refresh guidance, while the same viewer continues after an unchanged cursor
row leaves the actionable set. The prior forged-position, moved-rank, keyset
pagination, total-order and mandatory-width corrections remain intact. See
`review-2026-08-28T12-43-41Z.md`.
