# Finding: v11 Work-table headers are incorrectly all caps

## Observed

During the first real v11 TUI trial, Slawomir observed that the Work table
renders headings as `TITLE`, `ST`, `PHASE`, and so on.

## Confirmed UX

Headers use an initial capital, not all capitals: `Title`, `St`, `Phase`,
`Cls`, `Prog`, `Dep`, `Ready`, `Current`, `Next`, and `New`. This is a
presentation-only correction; canonical projection field names and the
internal responsive-column identifiers do not change.

The already-published `6d1b944` directory remains immutable. The correction
ships in the next v11 trial distribution.

## Implementation result

K implemented the correction under v11 Work `26de18dd-W2` and returned it to
the reviewing endpoint through discussion sequence 13. The renderer now
capitalizes display labels while retaining the uppercase internal responsive
column identifiers and canonical projection fields. Wide, narrow and
escape-return PTY expectations were updated; the immutable `6d1b944` trial was
not modified.

Reviewer inspection found the delta exact, `git diff --check` clean and the
focused PTY suite green. K's returned evidence reports 33 focused tests and
the full v11 gate at 541 parallel plus 3 serial passed.
