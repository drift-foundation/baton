# Plan

1. Re-read the parent decision record and W29400 authority record; revalidate the current protocol/CLI host.
2. Consume the landed authority API without duplicating validation, authorization, replay, or predicate logic.
3. Add repeatable create-time `label=`, distinct `label-work`/`unlabel-work`, and additive deterministic projections.
4. Add repeated `label=` all-of and `without-label=` none-of list/search inputs with explicit unsupported-form errors.
5. Update versioned output contracts, help, examples, and error documentation as required by the current host.
6. Add parsing, projection, filtering, retry/no-op, authorization, terminal, collision, and backward-compatibility regressions from `FINDING.md`.
7. Record implementation state in implementer-owned `PROGRESS.md` and route for independent review.
