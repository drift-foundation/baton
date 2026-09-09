# Plan

Current: **accepted**, review claim121144,
review-2026-09-08T17-24-17Z.md. This supersedes the correction and
awaiting-acceptance statuses below. Release W120425 for its approved consumer
composition and proof.

Prior disposition (superseded): **changes requested**, review claim121070.
review-2026-09-08T17-15-33Z.md supersedes the implementation-complete claims
below. Validate actual assignment types before equality at both local commit
and historical read; add the enumerated boolean and honest replay controls
without changing existing assertions. Declare the focused question and budget,
retain candidate/output evidence, and return baton.bug.

1. **Done.** Claimed after the serial gate; Provider B scope read and the
   operation identity, signature and receipt contracts pinned as
   `PUBLICATION_KIND` and `PUBLICATION_RECEIPT`.
2. **Done.** The three approved paths only: `publish_candidate` commits the
   closed record before returning, `publication_of` reads it, both exported.
   All existing assertions preserved; `PublicationCase`'s stand-in manager is
   now a real store because publication commits.
3. **Done.** Question and about-20s budget stated before running; 12 added
   controls then the affected driver, coordinator, stage-execution and
   secrets modules. Outputs in `evidence/verification-121029.json`.
4. **Done.** PROGRESS carries the public API, hashes, results and fixture
   limits; returning to baton.bug.

5. **Done, claim121097.** [P2] corrected: assignment member types are proved
   through `boundaries.generation` before any value comparison, at the local
   commit and on historical read; boolean-vs-integer controls added at write
   and read plus an honest reopened replay. Question and budget stated before
   execution; evidence in `evidence/correction-121097.json`.

Currently actionable: independent acceptance at baton.bug. W120425 remains
gated until it.
