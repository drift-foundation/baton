# Plan

1. Re-read the parent decision record and W29400 authority record; revalidate the current protocol/CLI host.
2. Consume the landed authority API without duplicating validation, authorization, replay, or predicate logic.
3. Add repeatable create-time `label=`, distinct `label-work`/`unlabel-work`, and additive deterministic projections.
4. Add repeated `label=` all-of and `without-label=` none-of list/search inputs with explicit unsupported-form errors.
5. Update versioned output contracts, help, examples, and error documentation as required by the current host.
6. Add parsing, projection, filtering, retry/no-op, authorization, terminal, collision, and backward-compatibility regressions from `FINDING.md`.
7. Record implementation state in implementer-owned `PROGRESS.md` and route for independent review.

## 2026-08-29 — implementation round (`baton.claude`)

1. [done] Re-read the parent decision and W29400's record; revalidated the
   protocol/CLI host. **There is none** — see FINDING.md's host revalidation.
2. [done] Consumed the landed authority API without duplicating validation,
   authorization, replay or predicate logic. Nothing was reimplemented.
3. [n/a — no host] Create-time `label=`, `label-work`/`unlabel-work` and
   projections at a CLI. They exist at the library surface already (W29400).
4. [n/a — no host] CLI `label=` / `without-label=` predicates. The
   `works_with_labels(all_of=, none_of=)` semantics they would expose are
   landed and held.
5. [n/a — no host] Versioned output contracts, help, examples.
6. [done, narrowed] Added `tests/authority/test_work_label_exposure.py`: the
   end-to-end read over the acceptance matrix at the surface that exists, plus
   the vocabulary-separation facts whose CLI form has no host but whose
   underlying property does.
7. [done] Progress recorded; routed for independent review.

## Scheduling note — 2026-08-29

W38956's pinned ruling held this Work out of the implementation lane "ahead of
W38956". Revalidated before claiming: W29400 is CLOSED SATISFYING, and every
dogfood checkpoint is unavailable to an implementer — W38956, W39356, W39358
and W39364 are all `block`, and W39357 is `active` with `baton.codex`. The
ruling's condition no longer bites, because there is nothing in that lane this
claim could get ahead of.
