# Implementer progress — owning ContractRefusal's message and durability

Created 2026-08-25 by `baton.claude`. The review is right that this was missing:
the pass comments described the implementation and its two supersessions in
detail, and Baton discussion is coordination evidence rather than the durable
specification. This is the record.

## Revalidated against the current tree

`ContractRefusal` takes four inputs. The category and code were already owned by
a **build-time assertion**, and that is the correct taxonomy rather than an
omission: a bad `(category, code)` pair is the raising site's defect, not
something a caller sent. W6782's inventory found `message` and `durable` owned
by nothing at all.

## What is implemented

**The message is exact built-in text, UTF-8 encodable, and BOUNDED at 4,096
scalars.** Encodability alone was not the confirmed contract, and the review was
right to fail it: a refusal is journalled, logged and carried onto a wire, so an
unbounded one is a durable row whose size a raising site decides by accident.
That is the rule W1593 established for every other diagnostic in this manager,
applied to the value that carries them all.

The bound is counted in **Unicode scalars**, because that is what a reader and a
schema `maxLength` both count in, and it is exported as `MESSAGE_LIMIT` so no
second site can spell it differently. 4,096 is large enough for this package's
own composed prose plus several bounded operands — the widest measured refusal
in the campaign is under 500 — and small enough that the size of a durable row
is this contract's decision.

**Durability is exactly a Boolean** — `is not True and is not False`, not
`isinstance`, so nothing else is admitted at all. The truth value of an
arbitrary object is decided by running `__bool__`, and that would have run
*inside* the refusal handling of a transaction, which is where this build is
already failing and least able to survive a caller's code. A case proves a
hostile `__bool__` never runs.

Both are owned by an assertion, like the pair beside them, and for the same
reason: a refusal whose own message is the thing under suspicion explains
nothing.

## Three supersessions this caused, all recorded

1. **`test_store`'s `a durable refusal's message` sub-case.** It drove an
   unstorable message through `transact` to prove the store refuses it at the
   text column. That message can no longer be built, so the store boundary is
   unreachable through it. Migrated to assert the earlier owner.
2. **The store's own owner call.** `seal_refusal` wrapped the message in
   `boundaries.text(..., "a sealed refusal's message")`. No refusal that can
   exist could fail it, so the boundary and its inventory probe were **removed
   together** — this campaign's treatment for an unreachable boundary, and the
   ninth. The composed seal is still owned, because that text is this build's
   own value on its way into SQLite and the structure around the message is not
   the message. This is the review's second P1, and it is now done.
3. **W6782's inventory table.** Both `UNOWNED` exemptions are replaced with
   real owners and non-vacuous probes.

## Gate state

`tests.manager.test_contracts_inventory` and `tests.manager.test_store` — 62,
all pass. A 282-case sweep across the suites that raise refusals
(`test_handshake`, `test_offers`, `test_attempts`, `test_manifest_rules`,
`test_workspaces`, `test_oci`, `test_validate`) shows no refusal in this build
exceeding the bound.

**Not run to completion under this claim:** the full source suite and the locked
gate. The remaining known failure in the shared inventory is W6632's
allowed-roots case, which is a design question awaiting a ruling rather than a
defect.

## State

**Awaiting independent review.**

## The declaration landed — 2026-08-25

The `('caller', 'store.py:seal_refusal', 'refusal')` entry is now declared in
`STATED_OWNERS`, named in `WITNESSES`, and exercised by
`StatedRules.test_public_sealing_owns_the_refusal_before_reading_it`, which
requires a caller-local `integrity.schema` refusal and asserts **no attribute
was read** before the type was established.

**Verified by grep after writing, not by the edit's own success report.** Two
earlier attempts at this file failed to persist by two different mechanisms —
a block that vanished after passing, and an edit that asserted on its second
anchor and wrote nothing. Every change to it now confirms itself afterwards.

`EveryStatedOwnerHasAWitness` and the new case pass. The remaining
`test_every_owned_entry_has_exactly_one_probe` failures are the `workspaces.py`
and `oci.py` entries belonging to W6631 and W6632, whose complete declaration
block is written out in
`work/records/2026/08/finding-v12-oci-source-workspace-materializer/evidence/inventory-declarations-2026-08-25.txt`.
