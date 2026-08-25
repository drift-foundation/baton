# Finding: ContractRefusal leaves its message and durability flag unowned

Discovered by W6782 while deriving every receiving entry on the public
`baton_v12.contracts` surface.

## Observed

`ContractRefusal(category, code, message, durable=...)` asserts its closed
category/code pairing but assigns `message` and `durable` without establishing
their contracts.

- A lone-surrogate message is accepted although refusals are stored, replayed,
  logged and mapped onto durable documents; attempting to encode it raises
  `UnicodeEncodeError` outside the refusal taxonomy.
- `durable` accepts any object although transaction code branches on its truth
  value. A behavior-bearing `__bool__` can therefore run while a refusal is
  being handled inside the manager transaction.

These are real exported receiving entries, not non-entry metadata. W6782's
inventory currently labels them `UNOWNED`, which records discovery but cannot
satisfy its one-owner/one-probe acceptance.

## Confirmed boundary

Own `message` as encodable, bounded durable text without running caller
behavior. Own `durable` as an exact built-in Boolean before any transaction
branches on it. Preserve the closed category/code build-time assertion and the
existing caller-local refusal taxonomy; do not turn invalid build-owned pairs
into caller refusals.

## Acceptance

- Unencodable/unbounded message input cannot escape later storage or logging.
- Non-Boolean and behavior-bearing durability values are rejected before their
  truth value can run.
- W6782 moves both entries from `UNOWNED` to their actual owner rules and adds
  non-vacuous probes.
- Focused contracts inventory, refusal, manager transaction, source and locked
  gates pass.

## Independent implementation review — 2026-08-25

**Confirmed corrected:** construction now rejects non-text and unencodable
messages before they can reach storage, and accepts `durable` only when it is
exactly `True` or `False`. A hostile `__bool__` is never run. The contracts
inventory no longer carries either `UNOWNED` sentinel; its focused 13 tests and
the store's focused 48 tests pass independently.

**Observed [P1]:** the confirmed message contract is *bounded* durable text,
and acceptance explicitly forbids an unbounded message escaping to storage or
logging. The constructor currently performs no length check, so a 100,000-
character public message is accepted. The additive
`test_a_message_cannot_be_an_unbounded_durable_value` fails because no
`AssertionError` is raised. The fixed bound itself needs an authoritative
ruling before correction.

**Observed [P1]:** the shared receiving-boundary inventory remains red at
`('caller', 'store.py:seal_refusal', 'refusal')`: its probe constructs a
lone-surrogate `ContractRefusal`, which the new earlier owner correctly makes
unreachable. The stale entry must be retired or replaced under that
inventory's own derived-universe rules; a handoff that knowingly leaves this
regression cannot satisfy the required source and locked gates.

**Operational finding:** this dossier has no `PROGRESS.md`. The implementer
passed completed code and detailed ephemeral commentary without creating the
implementer-owned durable progress record or updating the plan. Repository
policy requires confirmed decisions and implementation state to survive the
thread, so review cannot sign off until that record exists.

Review: `review-2026-08-25T00-33-39Z.md`.

## Confirmed message bound — 2026-08-25

`ContractRefusal.message` has a fixed maximum of 4,096 Unicode scalar values.
The existing encodability rule rejects surrogate code points before length is
accepted, so the bound is measured on the resulting Python text value without
calling behavior supplied by the caller. The limit is intentionally well above
the current sub-500-character diagnostics while remaining finite for durable
storage, replay and logging. A value of exactly 4,096 scalars is accepted;
4,097 is refused at the owning constructor boundary.

## Independent bound and serialization review — 2026-08-25

Disposition: **changes requested**.

**Confirmed corrected:** `ContractRefusal` establishes exact built-in text,
UTF-8 encodability, the approved 4,096-scalar maximum, and exact Boolean
durability without running rejected caller behavior. Exactly 4,096 passes and
4,097 asserts. The stale *message* owner and probe inside `seal_refusal` are
removed, `PROGRESS.md` now exists, and the contracts inventory is 14/14.

**Observed [P1]:** removing the unreachable message sub-boundary exposed that
the enclosing public `seal_refusal(refusal)` operand has no owner at all. The
manager receiving inventory reports
`('caller', 'store.py:seal_refusal', 'refusal')` with no layer, stated, or
delegated owner. `seal_refusal` immediately reads `.category`, `.code`,
`.message`, and `.durable`; a hostile object's `__getattribute__` therefore
runs and escapes as `AssertionError`. The additive
`test_public_sealing_owns_the_refusal_before_reading_it` preserves the failure.
Retire the unreachable message check without retiring ownership of the public
operand: establish an exact manager `ContractRefusal` before any member read,
declare/probe that entry, and retain the composed-seal write boundary.

**Observed:** `PROGRESS.md` says the limit is exported as `MESSAGE_LIMIT`, but
the public `baton_v12.contracts` surface neither imports it nor lists it in
`__all__`; only the private `contracts.errors` module does. Either expose the
single named rule on the package surface and cover it, or correct the durable
claim so it does not describe a public export that does not exist.

Independent results: contracts inventory 14/14; store 48/49 with only the new
public-sealing case red; the manager owner-completeness gate remains red and
the exact `seal_refusal` entry is independently confirmed unowned. Review:
`review-2026-08-25T00-44-40Z.md`.

## Public-sealing correction re-review — 2026-08-25

Disposition: **changes requested; runtime behavior is corrected but the
derived ownership record remains incomplete**.

**Confirmed corrected:** `seal_refusal` establishes an exact manager
`ContractRefusal` before member access, and the hostile-attribute regression
runs no caller behavior. `MESSAGE_LIMIT` is now genuinely exported from the
public contracts package at 4,096. Contracts inventory is 14/14 and store is
49/49.

**Observed:** the exact receiving entry
`('caller', 'store.py:seal_refusal', 'refusal')` still has no layer,
`STATED_OWNERS`, or `DELEGATED` owner. The new inline exact-type rule needs a
stated-owner declaration and checked non-vacuous witness. The newly public
`MESSAGE_LIMIT` also needs permanent package-surface coverage tying it to the
constructor's 4,096 edge.

**Operational finding:** `PROGRESS.md` was not appended for this round and
still reports the prior 62-test state and only W6632 as the shared-inventory
failure.

Review: `review-2026-08-25T00-51-03Z.md`.

## Final independent review — 2026-08-25

Disposition: **signed off**.

The exact public sealing operand is now a stated owner with a checked hostile-
object witness, the constructor's message/durability ownership remains green,
and `MESSAGE_LIMIT` is a real public 4,096 rule. This review added permanent
coverage tying that exported value to the constructor's accepted and refused
edges. Contracts inventory is 15/15 and store is 49/49.

The aggregate manager owner sweep remains red only on 16 concurrent OCI
entries; W7079's entry is present and has exactly its stated owner. Review:
`review-2026-08-25T00-55-28Z.md`.
