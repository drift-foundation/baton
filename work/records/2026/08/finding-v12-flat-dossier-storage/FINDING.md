# V12 canonical dossiers are a flat set

## Finding

The repository currently mirrors some Baton Work containment in dossier
directories such as `.../finding-parent/findings/finding-child/`. That makes a
mutable scheduler relationship look like permanent filesystem identity.
Reparenting, promotion, campaign regrouping, or folding a Job then either
leaves the path describing stale structure or demands a move that breaks the
canonical-path guarantee.

## Confirmed direction — 2026-08-29

V12 treats canonical dossier content as a set. Every dossier has one stable,
flat canonical record location independent of its current Work relationships.
Containment, dependency, campaign membership, follow-up, promotion, folding,
routing, and scheduling belong exclusively to the Baton authority and its
projections. No directory segment carries any of those semantics.

This supersedes the v12 direction that treated dossier-path flattening or
promotion as merely an indexing concern while retaining bounded canonical
directory nesting. It does not rewrite or move existing v11-era canonical
records: those paths remain immutable historical locators. The v12
materializer adopts the flat model for records created under the new contract.

Human navigation is recovered through Baton tree/graph/search views and, if
useful, generated disposable indexes. Such views are never authority and never
change a dossier's canonical identity. A dossier may retain internal files and
directories such as `FINDING.md`, `PLAN.md`, `PROGRESS.md`, `evidence/`, and
append-only reviews; "flat" applies to relationships between dossiers, not to
the contents of one dossier.

The exact collision-resistant record-name grammar is an implementation detail
still to be selected. It must be stable and must not encode mutable Work
relations.

## Acceptance boundary

- New v12 dossiers receive stable canonical locations in one record set.
- Reparenting or changing any Baton relationship never changes that location.
- No v12 scheduler or authorization decision is inferred from a path.
- Baton projections can reconstruct all Work relations without filesystem
  ancestry.
- Existing canonical records are not bulk-moved to simulate adoption.
- Generated navigation indexes are replaceable and non-authoritative.
