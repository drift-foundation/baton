# Finding: Work dependencies are invisible in the main list

## Observed

During the fresh v11 trial, `Show claim age in Work lists` was correctly
blocked by `Bold hot Work titles as a reliable cue`. The main Work table showed
only `Ready = no`; it did not show the blocker or an arrow relating the two
rows. An operator therefore had to leave the list and open `[b] deps` merely to
learn the relationship already controlling the row.

The existing `↳` presentation is working as designed for the single-parent
containment tree. It shows roots plus immediate children, at most two levels
per view. A dependency is a separate many-to-many graph edge and must not be
rendered as a child.

## Confirmed decision — 2026-08-16

**Confirmed by Slawomir during the fresh v11 trial.** The main Work table must
show both kinds of relationship without conflating them:

- `↳ Wn Title` remains the marker for an immediate containment child;
- `← Wn` on a Work row means that Work is blocked by the named open Work;
- when several open blockers exist, show one deterministic local selector and
  the remaining count, for example `← W23 +2`;
- `[b] deps` remains the full dependency-neighbor view.

Remove the `Ready` column once the dependency cue lands. A boolean `no` hides
the identity and shape of the gate; the arrow explains what must finish. A row
with no open blocker has no dependency cue. Closed or otherwise satisfied
historical edges do not remain in the live list cue; the audit ledger retains
their history.

The cue uses canonical projection data and authority-local Work selectors. It
must not infer a blocker from title, row order, cursor position, or an extra
per-row authority read. Narrow layouts may omit the dependency cue as one
whole responsive field, while `[b] deps` remains available; they must never
clip or relabel it into containment.

