# Implementer progress — bound a refusal diagnostic by its rule

Created 2026-08-24 by `baton.claude`, the implementer, when the implementation
claim began. Two reviews recorded that this file was missing and that reviewers
do not write it; this is that file, and it starts where the claim starts rather
than pretending to cover the reviewing that came before it.

## The correction — 2026-08-24

The review's P1 was exact and I have not argued with any of it. `own_record`
refused on unexpected members and returned, so a document that broke **both**
sides of the exact-record rule was told about one of them. A session reference
carrying `authority_uuid` and seven unexpected members heard about the seven
and never learned that `work_id`, `participant` and `provider_session_id` were
the point — and neither branch said how many members had actually arrived, so
"three and four more" left the reader to guess whether that was most of the
document or a corner of it.

One diagnostic now carries the whole rule:

```
a session reference is an exact record of 4 named members and 8 received
members arrived: it needs 'work_id', 'participant', 'provider_session_id'; an
exact record does not carry 'unexpected-0', 'unexpected-1', 'unexpected-2' and
4 more; an extra member in an exact record is one the sender believes was read
```

308 characters. Only the clauses that are **true of this document** appear: a
record that breaks one side is not told about a violation it did not commit,
because a diagnostic that overstates teaches the reader to stop believing it.

### The part that is not the message

`counted_sample_of` replaces `sample_of`'s `list(names)[:3]`. **A bounded output
is not a bounded operation** — W2929's words, and the reason this Work exists.
The old sampler copied the whole rejected name set in order to slice three
names off the front, and a caller that also needed the count either walked the
names twice or built that list itself. One walk now answers both, keeps at most
the shown names and copies nothing else, so `own_record` can hand it a
**generator** and a wide record's extra names are never materialized at all.
The membership test is a `frozenset` of *our own* required names — this
contract's small fixed cost, not the rejected value's.

`sample_of` survives as a one-line call to it, so the bound and the "and N more"
format still have exactly one definition.

## Mutation — 14 of 14 killed, after the first round showed my witness was weak

The first round had a survivor worth recording, because it was a defect in **my
test**, not in the code:

> **E1, "the sampler copies its names again"** — putting `list(names)` back in
> front of the walk left every behavioural case green.

My generator case asserted the names were walked once, and that is still true
of the mutant: `list()` consumes the generator exactly once and then walks the
copy. The property this Work is about is a property of the **code shape**, and
nothing observable from outside distinguishes the two. So it is now checked
where it lives, with a narrow structural case that forbids materializing *the
operand* — `list`, `tuple`, `set`, `sorted`, `len`, `reversed` or a subscript
applied to it — while leaving the small bounded list of shown names alone. E1
dies on the second round.

Also killed: the sample bound dropped; the omitted count dropped and off by
one; the extra branch returning early again; the received count dropped or
reported as the *rule's* count; either clause dropped; a clause emitted whether
or not it was true; the membership test taken from the wrong side; an extra or
a missing member admitted; and the plural rule inverted.

## What I did not touch, on purpose

- **The frozen Node reference.** `records.mjs` and its three red cases are
  measurement evidence, not a work item. Host-side JavaScript is frozen and the
  ruling says so twice.
- **A public Python capability boundary.** Revalidated against the current
  tree rather than taken from the review: `clientCapabilities` appears in
  `contracts/schema/agent-session-1.0.schema.json` and **nowhere else in the
  Python source or tests**. There is still no consumer at which to prove the
  black-box capability refusal, and inventing one so a test could pass would be
  building the boundary backwards. Final sign-off stays blocked on the
  separately scheduled manager composition work, as PLAN item 12 says.
- **The verdict, the exact-POD rules, the caller-local closed refusal pair, the
  inertness guarantees and the coarse no-enumeration behaviour.** All signed
  off; all still pass.

## Verification

- Focused: `tests.manager.test_pod` — 31 methods, all pass. The reviewer's four
  additive methods are green, including the five subtests that were red.
- Full Python gate: `just gate` — 585 tests at source and the same 585 in the
  locked build.
- The three Node cases remain red exactly as before, unchanged and untouched.

## State

**Awaiting independent review of the primitive correction.** The capability
consumer acceptance stays blocked on the composition work; this Work should not
close on the primitive alone.
