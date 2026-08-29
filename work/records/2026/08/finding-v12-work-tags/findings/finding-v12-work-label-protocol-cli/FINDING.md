# Expose v12 Work labels through protocol and CLI

## Status

Approved implementation cut, ordered after W29400.

## Parent and decision authority

This child was decomposed from W28880. The approved contract and chronological history are in `work/records/2026/08/finding-v12-work-tags/FINDING.md`. Core storage, authorization, mutation, replay, and predicates belong to sibling W29400 at `work/records/2026/08/finding-v12-work-tags/findings/finding-v12-work-label-authority/`.

## Confirmed boundary

- Canonical Work creation accepts repeatable `label=` inputs everywhere the v12 product exposes Work creation.
- Later mutations use distinct `label-work` and `unlabel-work` operations. They are not overloads of Thread `label`/`unlabel` or OCI label vocabulary.
- Detail and machine-readable projections expose the normalized, deterministically sorted live label set.
- Work list/search accepts repeatable `label=` predicates with AND/all-of semantics and repeatable `without-label=` predicates with exclusion/none-of semantics. Positive and negative predicates compose; no OR syntax is introduced in this cut.
- Convergent mutations return success with `changed:false`; exact operation replay preserves the original result.
- Help, protocol examples, and errors use the product term “Work labels” and document grammar, cardinality, normalization, authorization, terminal mutation, and filtering semantics.

## Host boundary

Implementation must revalidate the current v12 protocol and CLI host after W29400. If a canonical Work create/list/search surface is still absent, document the observed absence and split or park only the unavailable exposure rather than introducing a parallel CLI or protocol product.

## Acceptance and regression matrix

- Create accepts zero, one, and repeated labels; normalized duplicates do not consume extra cardinality.
- Mutation covers add, remove, terminal Work, unauthorized access, exact retry, convergent no-op, conflicting operation reuse, and stable error contracts.
- JSON/detail/list projections remain deterministic and backward-compatible for unlabeled Work.
- Repeated positive filters are AND, exclusions are none-of, mixed filters compose, and unsupported OR-like forms fail explicitly.
- CLI parsing proves Work-label commands cannot dispatch Thread-label or OCI-label behavior.
- Existing unfiltered list/search behavior, output versions, and help remain compatible except for intentional additive fields/options.

## Non-goals

No label inheritance, global label registry, scheduler meaning, implicit route/team labels, OR query language, or fuzzy matching is part of this cut.
