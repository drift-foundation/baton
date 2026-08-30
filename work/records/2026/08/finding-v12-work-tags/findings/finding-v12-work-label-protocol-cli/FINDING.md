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

## Host revalidation — 2026-08-29 (`baton.claude`, W29401 impl claim)

The Host boundary above required this before anything was written, and it
decides most of the cut.

### Confirmed: v12 has no CLI and no protocol host

The v12 product is a Python distribution — `baton_v12.authority`,
`baton_v12.contracts`, `baton_v12.worker_manager`. Every `argparse` /
`sys.argv` under `v12/` belongs to a test harness (`tools/parallel_test.py`),
a build tool (`tools/worker_image.py`) or the ping-pong spike. There is no
`create`, `list`, `search`, `detail` or `label-work` command anywhere in the
product, and no protocol host serving one. The canonical CLI this repository
operates through is the **v11** binary, which is a different product and is not
W29401's to extend.

So the finding's own instruction applies: document the absence, park the
unavailable exposure, and do not introduce a parallel CLI or protocol product.

### Confirmed: the approved contract is ALREADY exposed at the surface v12 has

W29400 landed the model at the only creation, mutation, projection and search
surfaces that exist, and the acceptance matrix's substance is satisfied there.
Driven directly during this revalidation, not inferred:

| Confirmed-boundary bullet | Where it lives now | Held by |
|---|---|---|
| creation accepts repeatable `label=` | `Authority.create_work(..., labels=())` | `test_work_labels`, and `test_work_label_exposure` end-to-end |
| distinct `label-work` / `unlabel-work` mutations | `Session.label_work` / `unlabel_work` | `test_work_labels` |
| projections expose the normalized, sorted live set | `project_work()["labels"]`, `labels_of()` | both suites |
| list/search `all_of` AND, `none_of` none-of, composing | `Authority.works_with_labels(all_of=, none_of=)` | both suites |
| convergent mutation `changed:false`, exact replay | core add/remove + operation journal | `test_work_labels` |
| no OR syntax; contradictions refuse explicitly | `works_with_labels` refusal | both suites |

`tests/authority/test_work_labels.py` is 52 cases and green; the additive
`tests/authority/test_work_label_exposure.py` is 7 more.

### Confirmed, and it constrains whoever builds the CLI: the two label
### vocabularies OVERLAP in spelling

`canonical_label`'s grammar admits dots, so `baton.v12.work_id` — an OCI
runtime label KEY this manager writes on every container — is a valid **Work**
label. Only the `key=value` form is refused, and only because `=` is outside
the alphabet.

That is not a defect. The parent decision says no spelling is reserved and no
behaviour is inferred from one, and a Work wearing a runtime-shaped label is
unchanged in every fact anything reads — now asserted rather than assumed.

It IS a constraint on the exposure this Work exists to build: **a CLI must
separate Work labels from Thread labels and runtime labels by the COMMAND it
dispatches, never by inspecting how a label is spelled**, because the
spellings are not disjoint. The acceptance bullet that asks CLI parsing to
prove non-dispatch is therefore about command routing, and a future
implementer who tried to disambiguate on the label text would build exactly
the confusion the bullet exists to prevent.

### What is parked, and it is only the hostless exposure

Nothing below has a surface in the current product, and none of it can be
built without inventing one:

- repeatable `label=` operands on a CLI Work-creation command;
- `label-work` / `unlabel-work` CLI commands;
- `label=` / `without-label=` CLI list/search predicates and their
  unsupported-form errors;
- help text, protocol examples and versioned CLI output contracts;
- CLI parsing regressions proving Work-label commands cannot dispatch
  Thread-label or OCI-label behaviour.

These are parked with W29401 rather than split into a new record, because they
are the whole of what remains and they become actionable together the moment a
v12 CLI or protocol host exists. The library-surface half of the cut is done.
