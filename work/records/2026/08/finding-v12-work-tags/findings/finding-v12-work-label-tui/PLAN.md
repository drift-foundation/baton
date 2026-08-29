# Plan

1. Re-read the parent decision and the W29400/W29401 records; revalidate the current canonical v12 TUI host.
2. Consume only protocol projections and filter state; do not duplicate label validation or query semantics in view code.
3. Add the wrapped detail `Labels` field and an optional lowest-priority wide-table labels column.
4. Disclose active positive and exclusion filters using existing TUI interaction and layout conventions.
5. Add detail, width, wrapping, ANSI measurement, filter disclosure, resize, focus, refresh, and unlabeled compatibility regressions.
6. Record implementation state in implementer-owned `PROGRESS.md` and route for independent review.
