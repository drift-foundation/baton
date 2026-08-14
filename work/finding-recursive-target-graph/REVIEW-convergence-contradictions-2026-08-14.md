# Flagged: one real contradiction, two consequences, two questions

Asked to flag contradictions between the 2026-08-14 sections and my completed
review. There is one, it is sharp, and it is worth fixing before a prototype
hardens around either half.

First, though: the explicit-`@`-scope rule and the inert-`#WORK` clarification
**supersede my recommendation with a better one**. I proposed requiring the
qualified form `@team.kind #WORK-123`. Making `#WORK` inert and putting the
gate on an explicit cycle-checked `blocked_by` edge is cleaner: it removes the
ambiguity at the root instead of asking the tagger to disambiguate, and
"adding a label later never enlarges an existing obligation" falls out of it
rather than needing its own rule. Likewise the origin / classification /
status split is now stated more precisely than I stated it. No disagreement.

## THE CONTRADICTION: mutual hiding is a security boundary

2026-08-13, on cross-team links:

> A linked external record does not enter another team's default tables or
> personal `New` counts, but a member may drill from relevant local work into
> its high-level status, progress, current role/member, next endpoint when
> known, activity, immediate children, discussions, and links. **This is a
> noise boundary, not a security boundary.**

2026-08-14, on convergence:

> The consumer teams neither see one another's labels, Work, discussions, nor
> dependency edges merely because Lang related them.

These collide exactly at drill-through. If Pushcoin drills from its blocker
into LANG-42 and sees that record's **links**, **immediate children** and
**activity** — as the first passage permits — then Pushcoin learns that Web and
MariaDB have incoming edges. The fan-in is precisely the thing the second
passage forbids it to learn.

So the provider's incoming-edge set IS access-controlled, and that is a
security boundary by any honest definition. Two consequences follow, and
neither is optional:

**1. The external projection must be computed per viewer, not per record.**
There is no single "LANG-42 status object" that can be handed to any drilling
consumer. Each consumer sees LANG-42 plus ITS OWN edge, and no other edge. A
cached or shared projection cannot express that.

**2. The fan-in count must be excluded from consumer-visible projections, not
just the identities.** "The provider sees the related incoming reports and the
fan-in count" is right; a count leaking into the consumer view would tell
Pushcoin that two other teams are waiting on the same defect, which is the same
disclosure with the names filed off. Aggregates leak.

The cheapest correction is to amend the 2026-08-13 sentence: drill-through is a
noise boundary **for the fields the provider chooses to expose**, and the
provider's incoming dependency edges are not among them.

## A third consequence: refusals must be indistinguishable

"Cross-team Work cannot be selected by a member who does not own or otherwise
control that endpoint of the relationship" is right, and the refusal has to be
identical to "no such Work". A distinguishable refusal turns Work selection
into an enumeration oracle for another team's ids — which is the exact defect
`authorize_read` already guards against in this codebase, with the same
reasoning and the same wording. Reuse it rather than reinventing it.

## Question 1: is a within-team duplicate a classification or an edge?

`duplicate` appears as a classification value, and deduplication also appears
as an intake action that records a `blocked_by` edge. Those mean different
things and gate differently:

- `classification=duplicate` says this record will never be worked separately.
  It should terminate, and its dependents should be retargeted at the record it
  duplicates — otherwise they wait on something nobody will work.
- `blocked_by` says this record is real and distinct and is waiting.

The provider-side fan-in is clearly the second. What I cannot tell from the
sections is what happens when Lang decides an incoming report is a duplicate of
**another Lang report** — same team, both records local. If that is
`classification=duplicate` plus terminal close, then the consumer's edge into
the closed record must be retargeted atomically, or the consumer is blocked on
a terminated record. That retarget is exactly the "audited atomic relinking"
PLAN 9 asks for; it just needs saying that within-team dedup triggers it.

## Question 2: `@lang.research` violates the 6/6 rule

The canonical flow uses `@lang.research`. `research` is eight cells; the
confirmed limit is six. `review` (6) and `impl` (4) are fine, so the example
breaks only on that one endpoint — which is the useful kind of break, because
it shows the width rule biting a name somebody actually wants.

This is the same finding as required-correction 1 in
`REVIEW-tui-handles-new-2026-08-14.md`, where all 21 live participants violate
6/6. The two together suggest the bound wants to be a rule about the DISPLAY
handle with a separate canonical identity, rather than a rule about the
identity itself. If the bound stays on the identity, the canonical example
needs a name like `@lang.rsrch`, and I would rather flag that now than watch it
be silently abbreviated later — the same ruling forbids exactly that
abbreviation.

## Nothing else contradicts

One `Current` per Work with external dependencies as blockers, level-triggered
satisfaction, close having no author recipient, classification and pass as
separate audited decisions, rejection returning attention through the recorded
origin without claiming a fix: all of that is consistent with the review, and
the last point in particular closes the gap I raised about honest non-satisfying
dispositions.
