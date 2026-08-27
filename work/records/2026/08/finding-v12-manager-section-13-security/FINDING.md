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

## Independent fifth-review finding — 2026-08-25

**Observed, P1.** The fourth correction fixes its four exact-data doors, but
`certify_agent_session_profile` and `record_inquiry_answer` both run
`boundaries.document` before §13. A malformed top-level operand equal to the
live bearer is therefore quoted by the ownership/type diagnostic and returned
as `integrity.schema`; the later walk is never reached.

One additive two-door regression observes `('schema', True)` — schema code and
the complete bearer present in the message — at both surfaces. The Python walk
is safe on the raw operand because it traverses only exact built-ins and ignores
behaviour-bearing types. Full analysis is in
`review-2026-08-25T13-19-17Z.md`.

## Implementation decision — 2026-08-25: §13 moves to the one crossing

Recorded by the implementer under the claim that answered the fifth review.
This SUPERSEDES nothing above: the door-local walks all stay, and the walk at
`boundaries.row` stays where third and fourth review put it. What changes is
that door-local ordering is no longer the whole rule for diagnostics.

**The re-audit was a measurement, and it did not agree with the review's
count.** The fifth review named two public doors and asked for a re-audit of
the other public document owners. Driving every callable in
`worker_manager.__all__` with the live bearer in every operand found **thirty**
public surfaces answering with a refusal whose message contained it — not two.
The exact list is in `evidence/gate-after-fifth-correction-2026-08-25.txt`.

**Why door-local ordering cannot converge on this.** The leak is not a property
of documents, of shape validators, or of the doors that own them. `name_value`
renders a rejected `str` operand verbatim by design, and an ordinary
`refused.precondition` naming the attempt it could not find leaks exactly as
`integrity.schema` does. Every refusal that names what it rejects is a
candidate, so "walk before the first diagnostic at each door" is a list with
one entry per public operation and one more for each one written later. This
Work has been corrected five times, and four of those corrections fixed the
doors that were named.

**So the rule is at `ContractRefusal.__init__`.** This is third review [P1]'s
lesson — a guard at the one crossing cannot be forgotten by a caller written
later — applied one layer further out than `boundaries.row`. Every diagnostic
in this distribution becomes durable and portable at that constructor: it is
journalled, sealed, logged and carried onto a wire, and that constructor is
already the owner that establishes the message is text, that it is encodable,
and that it is bounded. **A bounded diagnostic that cannot itself leak is the
fourth rule in that list**, and the acceptance names it in those words.

A refusal whose message carries a live bearer is replaced by
`integrity.secret-leak` carrying `SECRET_LEAK_MESSAGE` — this module's own
constant prose, which names nothing anybody was handed.

**The substitution keeps the durability it replaced.** A leak discovered while
composing a diagnostic does not un-write what the raising site had already
written, and a durable refusal replaced by a non-durable one would tell a
caller that nothing happened.

**The substitute is exempt from the rule, and the exemption leaks nothing.**
Raising from inside the constructor constructs another refusal, so a substitute
that could itself be found leaking recurses without a bottom — which it did,
under the first version of this correction, and the case that asks the question
is what found it. The exemption is on that exact message rather than on a flag
a caller could pass, and in the one case it fires the message is the constant,
which contains no caller data. A skipped check over a value with no caller data
in it is not a hole; unbounded recursion inside a refusal is.

**The door-local walks are kept and are not redundant.** The crossing catches
CONTAINMENT — a live value that reached a message. The walk at a door catches
the other half: a member NAMED for a secret is refused by its name whatever it
holds, and no message needs to quote it for that to be true. A door that walks
its operand also answers `secret-leak` about the operand rather than about the
diagnostic somebody tried to build from it, which is the answer that sends a
caller to the right place.

**The two doors the review named are corrected as it asked**, walking the raw
operand before `boundaries.document`. Its refutation of the fourth
correction's rationale is right and is now recorded in both docstrings: this
Python walk traverses only exact built-in `dict`, `list`, `tuple` and `str` and
returns without reading anything else, so it runs no caller behaviour and is
safe on an unowned operand. A third door, `seal_refusal`'s type diagnostic, was
found by the re-audit and is corrected the same way.

**Not moved, and the distinction is unchanged:**
`contracts.check_manifest_structure`, whose input is a raw caller document that
the schema must shape before anything traverses it.

## Independent sixth-review finding — 2026-08-25

**Observed, P1.** The constructor's recursion exemption compares the whole
replacement message for equality, but §13 compares live values by containment.
An arbitrary 32-character substring of `SECRET_LEAK_MESSAGE` is a valid bearer:
when that value is held live, the outer guard detects it and then returns the
exempt replacement with the complete bearer still present.

**This explicitly SUPERSEDES the earlier safety conclusion under “The
substitute is exempt from the rule” that the exemption leaks nothing.** It
does not supersede the constructor's one-crossing placement or durability
propagation; only the claim that build-owned constant prose is necessarily
secret-free by value is false.

The deterministic regression and required correction are recorded in
`review-2026-08-25T22-52-21Z.md`. The replacement itself must be checked against
the live snapshot and have a recursion-free fallback when its preferred prose
overlaps a live value; being build-owned constant text does not make it
secret-free by value.

## Independent sixth-review finding — 2026-08-25

**Observed, P1.** The fifth correction's crossing guard exempted
`SECRET_LEAK_MESSAGE` from the live-value test so that raising the substitute
could not recurse, and the exemption proved only EXACT EQUALITY. §13's value
rule is containment; the registry admits any non-empty value and the
worker-control claim token admits any 32-character string, so a live bearer can
be a SUBSTRING of that constant and the exempt replacement carried the whole
live value out.

The additive
`TheRefusalConstructorIsTheOneCrossing.test_the_substitute_cannot_quote_a_live_bearer_substring`
registers the replacement's first 32 characters and observes them intact in the
answer. Full analysis in `review-2026-08-25T22-52-21Z.md`.

## Implementation decision — 2026-08-25: the replacement is proved, not exempted

Recorded by the implementer under the claim that answered the sixth review.
This SUPERSEDES the fifth correction's exemption and nothing else: the crossing
stays at `ContractRefusal.__init__`, and durability still propagates.

**The mistake was in my own comment.** It justified the exemption with "if the
live value happens to BE this build's substitute prose" — equality reasoning,
three lines beneath a rule whose entire content is that the value test is
containment and not equality.

**The replacement passes the same containment test as every other message**,
and when the prose cannot pass it the message is EMPTY. The empty message is
safe BY CONSTRUCTION rather than by inspection: it is the one string a
non-empty value cannot be contained in, and `remember_secret` refuses an empty
value. That is also what bottoms the recursion — the substitute's own
construction re-enters the guard, and a substitute of `""` cannot fail it, so
no exemption is needed to terminate.

**The closed pair does not give way.** `integrity.secret-leak` is the
diagnostic; the readable prose is the part that can be spent, and only when it
would otherwise leak.

**One snapshot answers both questions.** A refusal now asks the registry about
two strings — the message it was handed and the replacement it would use — and
asking twice would let the registry move between the two answers. The snapshot
is taken once and passed to both, which is the rule `_walk` already follows for
a whole document; `_carries_live_secret` takes an optional `live=` for exactly
this and every other caller is unchanged.

## Independent seventh-review finding — 2026-08-26

**Observed, P1.** The replacement-message correction is sound, but
`ContractRefusal.__init__` emits its category/code pairing assertions before
the centralized live-value guard. Both assertions interpolate the rejected
operand with `repr`. Because `ContractRefusal` is an exported public contract,
a currently live bearer supplied as either field leaves verbatim in the
`AssertionError` text even though the refusal object itself is never built.

This is the same one-crossing ordering defect found earlier for row and shape
diagnostics, now inside the crossing itself. The assertion taxonomy is still
correct: an invalid pair is a raising-site defect, not a manager refusal. What
is not correct is letting that assertion quote a live operand before §13.

The additive two-subcase regression and required correction are recorded in
`review-2026-08-26T01-53-20Z.md`. Preserve the closed pairing and assertion
taxonomy, but make both pre-guard diagnostics incapable of carrying the
category or code value (or otherwise prove/sanitize them before rendering).

## Independent seventh-review finding — 2026-08-26

**Observed, P1.** `ContractRefusal.__init__`'s category and code assertions run
BEFORE the §13 message guard and rendered the rejected operand with `repr`, so
a live bearer supplied as an invalid category or code escaped in an
`AssertionError` the crossing never saw. Classifying an invalid pair as a
raising-site defect is correct and unchanged; that taxonomy does not make an
assertion carrying a live secret safe. Analysis in
`review-2026-08-26T01-53-20Z.md`.

## Implementation decision — 2026-08-26: the pair operands are proved too

Recorded by the implementer under the claim that answered the seventh review.
It extends the crossing rather than superseding anything: the guard stays in
this constructor, durability still propagates, the pairing is still closed, and
an invalid pair is still a raising-site ASSERTION rather than a manager
refusal.

**Every diagnostic in this constructor is now behind the same rule, and this
was the last one in front of it.** The same shape has been corrected at a
manifest door, a row boundary, two document owners, thirty public surfaces and
the substitute message itself; the two pair assertions were the remaining
diagnostics that ran before the guard, inside the very function the guard
lives in.

**Proved rather than suppressed.** `_rejected` names a rejected category or
code from what is safe to say: a non-string by its type, a string the registry
says is live by a sentence explaining why it is not quoted, and anything else
verbatim. A misspelled `integrty` is still quoted, because that is the whole
use of the message; only a live value gives way, and it gives way to an
explanation rather than to silence.

**One snapshot for the whole construction**, so the pair assertions and the
message guard decide against one view of the registry.

**And a defect the review did not name, closed by the same change.** `{value!r}`
runs `__repr__` — caller-chosen code — inside a diagnostic, which this module's
own `name_value` has refused to do since W6782 on the grounds that "a refusal
never RUNS the value it refuses". A pair operand with a raising `__repr__`
replaced the assertion with an exception of the caller's choosing. It is named
by its type now, read without metaclass dispatch.

## Independent eighth-review finding — 2026-08-26

**Observed, P1.** The seventh correction is sound for exact string pair
operands, but the assertion crossing is not yet complete. Pair membership
hashes malformed operands before `_rejected` can own them; `_rejected` does
not prove its redaction or inert type-name output by containment; and the later
message/durability type assertions still use metaclass-dispatched
`type(value).__name__`. These paths respectively run caller code, repeat the
sixth review's substitute-substring leak, leak a live type name, and let a
caller-selected metaclass value leave in public assertion text.

Three additive regressions exercise six category/code/message/durability
subcases. The 84-case focused gate has four failures and two errors; the prior
81 cases pass. Full analysis and the required whole-assertion correction are
in `review-2026-08-26T03-10-29Z.md`.

## Independent eighth-review finding — 2026-08-26

**Observed, P1.** Three manifestations of one ordering/ownership defect in
`ContractRefusal.__init__`: membership hashed a rejected operand before the
safe renderer ran, so caller `__hash__` executed and an unhashable operand
escaped as `TypeError`; `_rejected` proved the operand but not the text it
composed, so a live value equal to a substring of its redaction sentence or of
a type name left verbatim; and the message-type and durability-type assertions
still used `type(value).__name__`, consulting a caller-controlled metaclass.
Analysis in `review-2026-08-26T03-10-29Z.md`.

## Implementation decision — 2026-08-26: assertions are covered by construction

Recorded by the implementer under the claim that answered the eighth review,
which asked for exactly this: cover constructor assertions BY CONSTRUCTION
rather than one exemption per reproduction.

**`_defect` owns the complete text of every assertion leaving this
constructor.** It composes nothing that re-enters the constructor, so there is
nothing to bottom out: the preferred text, then a constant, then the empty
string, each proved against the same snapshot and the last terminal because a
non-empty value cannot be contained in it.

**Two layers, doing different jobs.** `_rejected` redacts only the operand so
an ordinary misspelled category is still quoted and the sentence still says
what was wrong; `_defect` guarantees the invariant whatever the operand
renderer or a type name composed. Safe provenance is not safe content.

**Shape before membership**, so nothing is hashed before it is known to be
text — the rule `is_closed_pair` has followed since W6782, applied at the site
that raises. And `type_name_of` at both remaining sites.

**And the construction is checked rather than claimed.** An AST case requires
every `raise AssertionError` in `__init__` to pass its text through `_defect`,
and a sibling requires no `.__name__` lookup anywhere in the class. The
decision recorded after the seventh review — "every diagnostic in this
constructor is now behind the same rule" — was true when written and had
nothing keeping it true. This one does.

## Independent ninth-review conclusion — 2026-08-26

**Confirmed, signed off.** The eighth correction closes all three
manifestations from `review-2026-08-26T03-10-29Z.md`: exact-string shape is
established before membership, complete assertion text passes through the
one-snapshot containment owner, and message/durability type descriptions use
the metaclass-safe helper. The AST gates cover every current explicit
constructor assertion and forbid the unsafe `.__name__` form.

The focused 90-case gate passes independently, the source and installed-layout
`errors.py` and `secrets.py` mirrors are byte-identical, and the full source
gate contains no W6630 failure. Its seven failures are the recorded
boundary-inventory baseline. Four Docker-dependent classes could not start in
this managed reviewer context because the daemon socket is unavailable; no
escalation was attempted under standing managed-turn policy. The implementer
evidence records the corresponding reachable-daemon source and locked-build
gates over one unchanged tree.

Full analysis is in `review-2026-08-26T04-12-33Z.md`.
