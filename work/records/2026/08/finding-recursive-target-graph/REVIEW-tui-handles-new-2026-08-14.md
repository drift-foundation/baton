# Review: v11 TUI navigation, 6/6 handles, and `New` semantics

Answering the three earlier requests in this thread that the Work-web message
did NOT fully absorb — it superseded terminology, not these decisions. Same
split as before: required corrections first, prototype choices after. No
implementation.

## Required corrections

### 1. The 6/6 rule is violated by every participant in the live mailbox today

Measured against `/home/sl/baton/mailbox/v10/baton.json`, which is the fresh
authority we cut over to two hours ago:

    participants: 21    violating 6/6: 21

    baton.implementer     team=5  member=11
    baton.reviewer        team=5  member=8
    dq.implementer        team=2  member=11
    human.slawomir        team=5  member=8
    ...

Not one address fits. `implementer` is 11 cells and `reviewer` is 8, so the
rule as written outlaws the two role names this entire project runs on.

This makes protocol-10 migration a REQUIRED part of the ruling rather than an
open item to settle later: the constraint cannot be enforced until it says what
happens to `baton.implementer`. Three honest options, and I do not think the
choice is mine:

- **shorten canonically** — `baton.impl` / `baton.rev`, a rename with a
  migration map, and every retained message's `to_participant` now names a
  handle that no longer exists;
- **split handle from display name** — the config already carries this idea for
  members (`sl`/`slaw` displayed as `Slawomir`). Apply it to the address:
  handle is 6/6 and width-safe, display name is arbitrary. Retained messages
  keep resolving because the handle is the identity;
- **relax the bound** for role components specifically.

The second is the only one that does not break history, and it is what the
finding already proposes for members — it just has not been carried to the
address.

### 2. "Six cells" needs a stated width algorithm, and validation at
### registration, not at render

Cells are not characters. A CJK name is two cells per character, an emoji two,
a combining mark zero. If the bound is checked as `len(str)` at config time and
the table lays out in cells at render time, a legal name still breaks a column.

Required: define width as terminal display cells with a named algorithm
(wcwidth semantics), reject over-wide handles when a participant is registered,
and never discover the problem during a draw.

### 3. `@team.kind` has no width guarantee, and it is what the table shows

The rule bounds `team` and `member` and derives `team.member <= 13`. But the
endpoint column shows `@team.kind`, and `kind` is unbounded. `@lang.deduplicate`
is 17 cells. Any column promising a fixed width for an endpoint is promising
something the grammar does not deliver.

Either bound `kind` too, or state that endpoint columns are elastic — but not
both a fixed-width endpoint column and an unbounded `kind`.

### 4. Identity is inelastic, so the TABLE must flex

"Must not silently truncate or automatically abbreviate canonical identities"
plus a fixed-width borderless table has a consequence worth writing down: when
a row cannot fit, the layout drops or reflows OTHER columns. The only column
that may be truncated is the neutral title, and that truncation must be
visible.

Otherwise the first narrow terminal produces exactly the silent abbreviation
the rule forbids.

### 5. `New` must be computed from a per-child breakdown, not a scalar

The ruling is that `New` is participant-relative and recursively aggregated
over the row's subtree, and that drill-down is immediate-children-only. Those
two together mean a nonzero count at the root tells a member that something,
somewhere below, is unread — and gives them no way to find it except walking
every branch.

The prototype affordance ("jump to the unread child") is deferrable. The
INVARIANT is not: aggregation must be derived from per-child counts and remain
decomposable. If it is stored or computed as one rolled-up number, that
affordance cannot be added later without recomputing the whole tree.

### 6. Do not blend the two counter definitions

`Unans.` was decremented by answer/disposition and not by viewing. `New` counts
visible messages since the member's own seen position. These are different
quantities with different drivers: one is workflow state, the other is a
cursor.

The superseded text should be struck rather than left readable as an
alternative, because the blended reading — "counts unread messages, and also
goes down when you answer" — is the one an implementer will land on, and it is
neither of the two rulings.

### 7. `New` and "unanswered" are orthogonal, and the table must not imply
### otherwise

Given that every member may contribute and that contributions by non-
responsible members do not discharge the route's responsibility, a row can
legitimately have `New = 0` and still be unanswered — someone read everything,
and nobody accountable has responded.

If the table shows `New` and nothing else, people will read it as "handled".
Show both signals or neither.

### 8. Deduplicate over discussion identity, not over tag edges

A discussion tagged into three targets must contribute at most one unread unit
to a member's roll-up. Count distinct discussion ids, not `(target, discussion)`
edges. And viewing a parent must not mark children seen — "seen state changes
no target workflow state" has to hold for the aggregate as well as the row.

## Prototype choices

(a) **Borderless fixed-width vs bordered.** Borderless reads well and is
    cheaper to align; whether it stays legible at depth is a screen question.
(b) **The initial columns and their priority order** under narrowing.
(c) **Breadcrumb elision at depth.** A breadcrumb at arbitrary depth is itself
    unbounded; eliding the MIDDLE of a breadcrumb (root … parent > current) is
    acceptable in a way that eliding an identity is not, but the exact rule can
    wait for a screen.
(d) **"Jump to the unread child"** — deferrable, provided invariant 5 holds.
(e) **Sorting and keys**, per PLAN 12.

## What I did not review

`8a352bef` is terminology that the Work-web message supersedes; I have closed
it as superseded rather than answering it twice. The lifecycle, endpoint,
dependency-web and `#WORK` questions are answered in
`REVIEW-work-web-2026-08-14.md` (`d7f575a9`).
