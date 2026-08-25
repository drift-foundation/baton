# Finding: worker-control §13 security surfaces in the Python manager

Canonical Baton Work: W6630, a separately scheduled M2 manager prerequisite
from the closed W4 and W5 PLAN item 8. Dossier created 2026-08-24 by
`baton.claude` on claiming, because the assignment requires one before
implementation.

## Confirmed boundary

§13 in the Python manager's contracts and durable/public surfaces: credential
references and assignment-scoped delivery authority, redaction, bounded
diagnostics, secret-free operations, labels, logs, store and artifacts, leak
refusal, and restart/cancellation semantics. **Secret bytes stay outside
protocol identity and durable state.**

**Not here:** provider login, OCI injection mechanics, output collection,
retention, lifecycle composition.

## Revalidated against the current tree

**The contract anchor exists, and it is an error code rather than a schema
shape.** `integrity` is closed to `digest, file-type, limit, path, schema,
secret-leak` — and `secret-leak` is already in the Python `ERROR_CODES`
pairing. Like retention (W6629), §13 has **no `$defs`** in the frozen schema:
it is prose in the spec and *behaviour* in the implementation, anchored by that
one code. Unlike retention, that is sufficient — the code is the contract, and
what is missing is the rule that raises it.

**The frozen host has a complete reference to port**, in
`v12/src/worker_manager/contracts.mjs`, and its design decisions are the ones
this Job should carry forward rather than re-derive:

1. **It is a WALK, not a top-level check**, because the boundary is about what
   a durable document *contains, at any depth*. A bearer nested inside a copied
   decision body is exactly as durable as one at the root.
2. **Both halves are needed and neither implies the other.** A field *named*
   for a secret is refused whatever it holds, because the name says the value
   is one; and a known secret *value* is refused wherever it appears, because a
   leak does not depend on what the leaking field was called.
3. **The value test is CONTAINMENT, not equality** — an interpolated refusal
   message carries the bearer just as durably as a bare field does. This is the
   subtle one, and it is the reason W1593's bounded-diagnostic work and this
   Job meet: a diagnostic that quotes an operand is a durable surface.
4. The named field set is `claim_token, password, authorization, access_token,
   refresh_token, private_key`, matched case-insensitively.
5. There is a **live-secret registry** with scope-based forgetting, and the
   synchronous cleanup covers a throwing `then` getter — a value whose
   classification failed was never handed to anyone.

**What exists in Python today:** the `secret-leak` code in the closed pairing,
and W4's offers slice, which already keeps the bearer out of the store (the
verifier is persisted and the bearer never is). **What does not exist:** any
walk, any registry, any leak refusal. So the enforcement surface is absent
while its taxonomy is ready.

## Why this Job matters more than its position in the queue suggests

**W6634's exhaustive credential leak refusal is blocked on this**, and W6632's
adapter labels, W6633's worker image and W1593's bounded diagnostics all touch
surfaces §13 governs. This is the rule that says a label, a log line, a store
row, an artifact and a refusal message are all durable surfaces — and four
Works have already been written against the assumption that something will
eventually check.

## Dependency

**W6630 → W6592.** §13 enforcement must apply *to* the completed contracts
inventory and public composition rather than inventing parallel public or
durable surfaces — a second enforcement point would be a second definition of
"durable surface". W6592 is open with changes requested.

## Acceptance

- The walk, at any depth, over every durable and public surface.
- Both halves: named fields and known values, with **containment** for values.
- Assignment-scoped delivery authority; secrets never in protocol identity.
- Bounded diagnostics that cannot themselves leak.
- Restart and cancellation semantics that forget rather than persist.

The implementer creates and exclusively owns `PROGRESS.md`.
