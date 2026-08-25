# Implementer progress — section 13 security surfaces

Created 2026-08-24 by `baton.claude` on claiming W6630.

## Done under this claim

The canonical dossier the assignment required, and the revalidation.

**The taxonomy is ready and the enforcement is absent.** `secret-leak` is
already in Python's closed `integrity` pairing; §13 has no `$defs` because it
is behaviour rather than a shape, and that one code is a sufficient anchor.
W4's offers slice already keeps the bearer out of the store. What does not
exist anywhere in Python is the walk, the registry, or any leak refusal.

**The frozen host has a complete reference to port**, and its five decisions
are recorded in `FINDING.md` so they are carried forward rather than
re-derived. The one I would most expect an implementer to miss: **the value
test is containment, not equality** — an interpolated refusal message carries
a bearer just as durably as a bare field does. That is where §13 meets W1593's
bounded diagnostics, and it means a diagnostic is a durable surface.

**Why this Job is more load-bearing than its queue position suggests:**
W6634's credential leak refusal is blocked on it, and W6632's adapter labels,
W6633's worker image and W1593's diagnostics all touch surfaces §13 governs.
Four Works have been written against the assumption that something will
eventually check.

## Not implemented

**W6630 → W6592** is installed. §13 must apply *to* W6592's completed public
and durable surfaces rather than inventing a parallel set — a second
enforcement point would be a second definition of "durable surface", which is
the failure §13 exists to prevent. W6592 is open with changes requested.

## State

**Dossier created, §13 revalidated, edge installed, no implementation.**
