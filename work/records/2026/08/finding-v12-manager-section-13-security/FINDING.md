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

## Implementation decisions — 2026-08-25

Recorded by the implementer under the claim that built this slice.

**The registry lives in `contracts`, not the manager.** The manifest composite
has to consult it and this package may not import from the one above it. It is
deliberately small, holds nothing that is not currently live, and every entry
is forgotten by the act that acquired it.

**`held_secret` is a context manager rather than a callback.** The frozen host
needed a callback and then three review rounds of thenable handling to make its
release wait for an asynchronous act. There is no such split in a `with` block:
it ends when the block ends, on a return, a raise or a `break`. The property
the host was reaching for is Python's by construction here.

**`live_secret` proves its operand.** Answering "no" to a malformed question is
how a caller concludes it asked a good one — the same rule W6627's quiescence
gate carries, applied one module over.

**The named-member half is unreachable through a frozen manifest, MEASURED.**
Every object in the manifest family is `additionalProperties: false` except
`extensions`, whose `propertyNames` pattern requires a reverse-DNS namespace
with a version, so a member called `authorization` is refused by the schema
before §13 is reached. The value half is what §13 adds at that surface, and a
case pins the reliance so the gate speaks if the schema ever stops carrying it.

**No golden pinned bearer.** The frozen host pins its conformance bearer in a
register that is never released, because nothing acquired it and so nothing may
hand it back. This distribution has no golden bearer in its Python fixtures, so
pinning one would add a value nothing uses and a branch nothing can drive. If a
conformance bearer lands, `_live` is the wrong register for it and a separate
pinned one is right; the reasoning is recorded so it is not re-derived.

**`threading` is added to the distribution's standard-library record.** The
registry's reference count is a read-modify-write over shared process state,
and a lost update means a bearer stops being live while an owner still holds it
— a leak boundary that silently stops guarding. The module is standard library,
so the locked build is unchanged, and the lock is held only around the
arithmetic.

**Not here, and named so the absence is deliberate:** provider login, OCI
injection mechanics, output collection, retention, and lifecycle composition.

## Independent review finding — 2026-08-25

**Observed, P1.** The derived coverage sweep enumerates SQLite writers but no
public surfaces. Consequently exported `manager_signature` can return
canonical protocol-identity text containing a live bearer verbatim, and
exported `seal_refusal` can return a portable refusal whose message contains
an interpolated live bearer. The later journal walk refuses either row, but it
cannot undo the public representation that has already been constructed and
returned.

The two deterministic regressions and full analysis are in
`review-2026-08-25T06-35-31Z.md`. The guards must be local to the public
construction boundaries, and the enumerated gate must cover applicable public
surfaces as well as durable writers.

**Partially resolved 2026-08-25.** `manager_signature` and `seal_refusal` now
walk before returning, and their regressions pass. Re-review found the public
inventory still omits exported class methods and accepts false safe-by-reason
classifications: `revive_refusal` and `certified_agent_session_profile` can
still return live-bearer surfaces. See
`review-2026-08-25T06-57-14Z.md`.

## Independent re-review finding — 2026-08-25

**Observed, P1.** The public sweep derives top-level `__all__` callables only;
it treats an exported class as one surface and omits its public methods.
Further, only the constructor class is probed. A prose-only reason incorrectly
claims public `revive_refusal` receives bytes already walked, although direct
callers supply arbitrary sealed text, and another claims retained profile
bytes were walked on write while the read boundary exists specifically because
later store edits are possible.

The three deterministic regressions and required correction are recorded in
`review-2026-08-25T06-57-14Z.md`.

## Independent third-review finding — 2026-08-25

**Observed, P1.** The second correction fixes the three reported paths, but
the public sweep still falsely classifies persisted journal reads as safe from
their write history. `ControlStore.operation_record` and `replay` both receive
an adopted row without a §13 walk, so a later edit to `operations.result` can
make both public methods return a currently live bearer. The store is already
documented as a receiving trust domain; shape adoption does not establish the
dynamic known-secret rule.

One additive regression drives both public reads and fails in both subcases.
Full analysis and the required read-side re-audit are in
`review-2026-08-25T09-30-45Z.md`.

## Independent fourth-review finding — 2026-08-25

**Observed, P1.** The central row guard runs after column validation. An
invalid typed column containing a currently live bearer is therefore quoted by
the column owner's schema diagnostic before §13 runs; public
`operation_record` returns a refusal whose message contains the complete
bearer. The guard must precede any content validator that can format the row's
values, not merely precede the successful return.

One additive regression records the leak. Full analysis is in
`review-2026-08-25T10-49-54Z.md`.
