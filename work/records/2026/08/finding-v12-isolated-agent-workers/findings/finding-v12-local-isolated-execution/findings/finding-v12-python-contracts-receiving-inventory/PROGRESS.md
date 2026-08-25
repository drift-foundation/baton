# Implementer progress — the contracts package's receiving inventory

Created 2026-08-24 by `baton.claude` on claiming W6782.

## Delivered

`v12/python/tests/manager/test_contracts_inventory.py` — **11 methods, all
passing**, over the contracts package's **18 exported callables and 40
receiving entries**.

**The universe is derived, not declared** — the rule the manager's inventory had
to learn three times. It comes from the package's real `__all__` and the actual
signature of every exported callable, so a parameter added without an owner
appears here whether or not anybody remembered it. A case guards the guard: an
inventory that read its universe from the ownership table would report a clean
sweep over exactly the entries somebody listed, so the derivation is required to
disagree with that table.

**An entry is `(operation, parameter)`, keyed lexically.** `check_uri(uri)` and
`validate_fragment(document)` are different crossings that happen to share
words, and a key by parameter name alone would merge them.

**One owner and one non-vacuous probe per entry.** Each probe drives the real
exported operation and requires a `ContractRefusal`; both directions are
checked, so an owner with no probe and a probe with no owner each fail. The
probe gate is itself proved able to fail by handing it a call that succeeds.

**The private-body path is pinned structurally.** `check_manifest_structure`
must call `_relate_work_ref` and `_check_content_manifest` and must **not** call
the public wrappers — owning the same value twice is the blanket revalidation
4bz forbids — and each public wrapper must validate its fragment and then
delegate. Read from the AST, so it stays true when the composite is edited.

## What the inventory found on its first run

Two entries with **no owner at all**, which is what an inventory is for:

- **`ContractRefusal.message` accepts unencodable text.** A refusal is a durable
  value that gets stored and logged, and a lone surrogate reaches it; the case
  demonstrates the message coming back and failing to encode.
- **`ContractRefusal.durable` takes any object** although it is read as a flag.

A third result worth recording as a *correction to my own expectation*: the
category and code **are** owned, but by a **build-time assertion** rather than a
refusal. That is the right taxonomy — a bad `(category, code)` pair is this
build's defect and not something a caller sent — so the table marks them
`ASSERTED` and they are witnessed by their own case rather than by a refusal
probe. Requiring a `ContractRefusal` there would have asserted the wrong
taxonomy and quietly pushed somebody to widen the closed pairing.

**The two gaps are recorded, not corrected.** `errors.py` is closed W4's
primitive, and this Job is routed to inventory the contracts package rather than
to reopen it. The cases pin the current behaviour so the gaps cannot be
forgotten, and so the day either is fixed the suite fails and tells somebody to
move the entry from `UNOWNED` to a stated rule.

## State

**Awaiting independent review.** No W6592 public composition, §13 or retention
work was touched.

## Correction — 2026-08-25: the two gaps are closed, not merely recorded

The section above is now false and is corrected here rather than rewritten,
because the record should show what was true when and what changed.

**W7079 closed satisfying.** The two entries this inventory derived with no
owner — `ContractRefusal.message` and `.durable` — have real owners, and
neither uses the `UNOWNED` sentinel any more. Both name the constructor's
**build-time assertion**, which is the same taxonomy already used for the
closed category/code pairing and is the right one: an unencodable message, an
over-long one or a non-Boolean flag is the raising site's defect, not something
a caller sent.

**Their witnesses are direct and non-vacuous.** The message rejects non-text
and unencodable values, accepts exactly 4,096 Unicode scalars and asserts at
4,097; durability rejects non-Boolean and behaviour-bearing values *without
invoking a hostile `__bool__`* and accepts exactly `True` and `False`. This
review added permanent coverage that the public `contracts.MESSAGE_LIMIT` is
the constructor's one 4,096 rule — so the bound cannot be spelled differently
in two places, which is the defect a named constant exists to prevent.

**Focused result: 15/15.** The public surface is unchanged at 18 callables and
40 receiving entries; the newly exported constant is deliberately not callable
and creates no receiving entry.

**Gate attribution, named rather than described as green.** The aggregate
manager owner sweep is red only on entries belonging to **W6632** (`oci.py`) and
**W6631** (`workspaces.py` witnesses and probes), both of which are in review
with those items recorded as outstanding on their own dossiers. Nothing red in
that sweep belongs to this Work.

## State

**Corrected and awaiting re-review.** The inventory's own acceptance is
satisfied: the universe is derived, every entry has one owner, every owner has a
non-vacuous probe or a named witness, and the private-body path is pinned
structurally.

## Record correction — 2026-08-25: the universe is 39 entries

Measured against the current tree rather than taken from the review:
`len(exported_operations())` is **18** and `len(universe())` is **39**. Both
earlier sections of this record say 40, and that is superseded.

The count moved because the universe is **derived**, not declared — which is the
property this file exists to have. It is recomputed from `__all__` and the live
signatures on every run, so a parameter that goes away takes its entry with it
and no table has to be edited to keep the number honest. A hand-maintained
figure in prose is the one place it can drift, and it did: 40 was true when I
wrote it and stopped being true without anything failing, because nothing in the
suite asserts the total.

That is worth saying plainly rather than just correcting the digit. The
inventory's own guarantees — one owner per entry, one non-vacuous probe or named
witness per owner, and the private-body path pinned structurally — are all
checked mechanically and remain green at 15/15. The count in this record is the
only part that was ever a claim rather than a check.
