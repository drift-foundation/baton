# Implementer progress — §13 security surfaces

Created 2026-08-24 by `baton.claude` on claiming W6630.

## First claim, 2026-08-24: dossier and revalidation, no implementation

§13 and the closed W4 record were revalidated. The result is in `FINDING.md`:
the contract anchor is the `secret-leak` code, already in this distribution's
closed `integrity` pairing, and §13 has no `$defs` because it is BEHAVIOUR
rather than a shape — so the code is the contract and what was missing was the
rule that raises it. The frozen host's five design decisions were recorded so
they would be ported rather than re-derived.

Nothing was implemented: `W6630 → W6592` was installed, and W6592 was open with
changes requested. Enforcement had to apply TO the completed public and durable
surfaces rather than to a parallel set this Job named — a second enforcement
point would be a second definition of "durable surface", which is the failure
§13 exists to prevent.

## Second claim, 2026-08-25: the implementation

**`contracts/secrets.py` — the registry and the walk.** All five decisions are
carried: it is a WALK at any depth; both halves are independent; the value test
is CONTAINMENT rather than equality; the named-member set is the frozen six
matched case-insensitively; and there is a reference-counted registry whose
entries are forgotten by the act that acquired them however that act ends.

Two things are Python's rather than the frozen host's, and each is better here:

- **`held_secret` is a context manager, not a callback.** The host needed three
  review rounds of thenable handling to make its release wait for an
  asynchronous act; there is no such split in a `with` block, which ends when
  the block ends — on a return, a raise, or a `break`.
- **`live_secret` PROVES its operand** rather than answering False to anything
  that is not text. Answering "no" to a malformed question is how a caller
  concludes it asked a good one, which is the same rule W6627's quiescence gate
  carries.

**Why the registry is in `contracts` and not the manager.** The manifest
composite has to consult it and this package may not import from the one above
it. It is deliberately small and holds nothing that is not currently live.

**Where the walk is called.** The manifest composite (§13 before §12's rules,
after the schema); the agent-session profile certification, which is a
different frozen family with its own validator and would otherwise file bytes
nothing had walked; and `ControlStore._record` — the journal, which is the one
durable surface every mutating manager act passes through, carrying an
operation's identity, its full effective signature, its byte-stable result and
its sealed refusal.

**The bearer is made live for exactly the acts that spend it.** Registering it
in `issue_offer` and `accept_offer` is what turns the value half from a dormant
rule into an enforced one: a check against an empty registry reads as a leak
boundary while being nothing at all, which is the same failure a name-only
check would be. The scope is the journalled act and no wider — the bearer rides
back with the RESULT deliberately, and holding it across that return would make
the manager refuse to answer with the one value the caller is entitled to.

## The sweep is enumerated, not probed

`EveryDurableWriterIsGuarded` derives every INSERT and UPDATE in the manager
package from the AST, keyed by `(module, lexical site, table)`, and requires
each to be covered — by the journal walk or by a declared entry naming the rule
that covers it. The universe comes from the code, so a durable surface added
later without a guard fails the gate rather than waiting for somebody to think
of probing it, and the declared entries are checked for staleness in the other
direction.

That check earned its keep immediately: it found that `certify_profile` writes
`meta` rather than `profiles`, and that two of the entries I had written by
recollection named functions that do not write at all.

## One measurement worth recording

**The named-member half is unreachable through a frozen manifest, and the case
says so rather than pretending otherwise.** Every object in the frozen manifest
family is `additionalProperties: false` except `extensions`, whose
`propertyNames` pattern requires a reverse-DNS namespace with a version — so a
member called `authorization` is refused by the SCHEMA before §13 is reached.
The value half is what §13 adds at that surface. The case pins the reliance, so
if the schema ever stops carrying it the gate says so rather than leaving half
of §13 quietly unenforced there.

## Verification

`tests/manager/test_secrets.py` — **39 cases, all passing**, plus one added to
the contracts inventory's probe table.

    cd v12/python && just build
    # Ran 943 tests -- FAILED (failures=13, skipped=1)

**Forty cases added and one failure, and the failure is not this slice's.**
`test_quiescence_is_rechecked_inside_the_freeze_write` is the reviewer's
additive regression on W6628, posted while W6630 was being implemented. It
fails for a W6628 defect — `request_freeze` decides quiescence before
`store.transact` and does not re-read it under the write lock — and W6628 is a
separate Work, queued at `baton.impl` and not held by this claim. Fixing it
here would be executing Work nobody claimed, so it is reported and left. The
other twelve are the pre-existing `oci.py` and `workspaces.py` failures,
byte-identical to the lists in W6627's and W6628's dossiers.

Evidence: `evidence/gate-after-2026-08-25.txt`.

## One edit outside this module, named because it is one

`tests/manager/test_dependencies.py`'s `STANDARD_LIBRARY` record gains
`threading`. The registry's reference count is a read-modify-write over shared
process state, and a lost update there means a bearer stops being live while an
owner still holds it — a leak boundary that silently stops guarding, which is
exactly what §13 exists to prevent. "This package is single-threaded today" is
the kind of assumption this distribution has been corrected for, and the module
is standard library, so the locked build is unchanged. The lock is held only
around the arithmetic, never around a walk.

## Not done, and named rather than rounded up

- **Provider login, OCI injection mechanics, output collection, retention and
  lifecycle composition.** Not in the brief and not in the acceptance.
- **A golden pinned bearer.** The frozen host pins the conformance bearer in a
  register that is never released. This distribution has no golden bearer in
  its Python fixtures, so pinning one would be adding a value nothing uses and
  a branch nothing can drive — the shape this campaign has made me delete four
  times. If a conformance bearer lands, `_live` is the wrong register for it
  and a `_PINNED` one is the right one; the reasoning is here so the next
  implementer does not have to re-derive it.
- **W6628's P1.** Reported above; it is that Work's to fix.

## Review correction — 2026-08-25

**[P1] The sweep derived only the durable half, and the missing half was a
live gap rather than a paperwork one.**

The acceptance and PLAN item 5 both say durable AND public surfaces. I derived
every INSERT and UPDATE and stopped there — and two exported constructors
returned a leak before any row was written:

- `manager_signature` serialized its operands and handed back protocol
  identity containing the bearer verbatim. The journal refused the ROW
  afterwards, by which point the caller held the leak. "Secret bytes stay
  outside protocol identity" cannot be established by a guard that runs after
  the identity has been handed out.
- `seal_refusal` returned the portable refusal document with an interpolated
  bearer still in `message`. Sealing is the point a diagnostic BECOMES a
  portable document — which is exactly the bounded-diagnostic surface the
  acceptance names, and which my own FINDING calls the decision an implementer
  is most likely to miss. I wrote that sentence and then guarded the write
  rather than the surface.

**Both now walk before they answer**, over the operands and the sealed document
respectively rather than over the composed text — because the walk's named half
is about MEMBERS, and a `claim_token` operand is refused by its name before
serialization and would be an ordinary substring after it.

**The public half of the sweep is now derived too.**
`EveryPublicSurfaceIsAccountedFor` reads every exported callable from
`__all__` — the package's own promise — and requires each to be in exactly one
declared class, checked in both directions. The constructing ones are PROBED
against a live bearer, so their entries are facts rather than claims; the rest
carry a reason, including the one that deliberately returns the bearer to the
caller entitled to it.

One entry is classed by measurement rather than by probe and says so:
`record_frozen_result` walks its sealed operand through the manifest composite,
but that walk sits behind a precondition that the named attempt exists, so a
probe here would be refused for the earlier reason and prove nothing. The
composite is driven directly beside it.

    cd v12/python && just build
    # Ran 951 tests -- FAILED (failures=12, skipped=1)

**Twelve, byte-identical to the list this claim found.** The first pass
reported thirteen; the extra was the reviewer's in-flight W6628 regression,
which has since been corrected and returned.

## State

**Awaiting final review.**

## Second review correction — 2026-08-25

The re-review's [P1] is addressed, and the re-audit it asked for found a third
defect the reviewer had not named.

**The two named leaks.** `revive_refusal` is a public receiving door for
arbitrary sealed text; its inventory reason described `_revived`, the internal
replay path, whose input is a journal row this build wrote. It walks its own
input now, and `_revived` says out loud why it does not — re-walking a row
`_record` cleared would be blanket revalidation, and would make an exact
durable replay of a refusal quoting a since-forgotten secret fail on retry.
`certified_agent_session_profile` exists because a write-side guard cannot see
a later store edit, and already re-checks shape and digest for that reason;
§13 was the one rule left out of its own argument, and is part of it now.
Both moved from the prose-only class to the constructing one and are probed
there against a live bearer.

**The method universe.** `exported()` now walks an exported class's public
attributes, so the five `ControlStore` methods and the eight `AuthorityPort`
members are each classified with a reason describing that method's own public
path. `test_the_method_universe_is_derived_and_not_listed` asserts the
enumeration against `dir()` for both classes, so a method added tomorrow is in
the universe tomorrow and an enumeration that quietly covered one class fails.

**The third defect, found by the re-audit and real.**
`record_inquiry_answer` writes the answer body through a direct `UPDATE`, not
through `transact` — so `_record`'s walk never ran on it, while both of its
inventory entries claimed it did. An answer body carrying a live bearer
reached the `interrogations.answer` column unguarded. It is walked at its own
boundary now, with three regressions. The lesson the reviewer stated is the
one that found it: a reason is evidence only when it describes the path that
actually runs.

## Verification

`evidence/gate-after-second-correction-2026-08-25.txt`.
`tests.manager.test_secrets` is 52/52. The full suite carries the same twelve
pre-existing `oci.py`/`workspaces.py` failures this dossier has recorded
throughout, minus the three the re-review left, plus four reviewer-authored
cases on W6627 and W6633 — Work this participant has already passed back,
reported rather than fixed. The locked installed-layout build reproduces the
identical verdict from site-packages.

## State

**Awaiting independent re-review.** The claim is not released and no Git
operation was performed.

## Third review correction — 2026-08-25

The review was right, and the fix is one line further out than it asked for.

**The walk is at `boundaries.row`.** The column contract proves the column SET
and the column SHAPES and says nothing about content — which is the gap — and
that function's own docstring already calls the store a receiving trust
domain. Every adopted row in this manager comes through it, so the two public
doors the review named are covered and so is every other persisted-row
projection: `claimed_offers_for`, `agent_sessions_of`, `posture_slot`,
`frozen_output_of`, `interrogation_of`, `interrogations_of`.

Putting it in the two named readers would have satisfied the finding and left
the shape that produced it. This Work has been corrected three times now for
reasons that described a path other than the one that ran; a guard at the one
crossing cannot be forgotten by a projection written later, and the re-audit
correction 2 asked for is then true by construction rather than by my having
looked carefully.

**The split is kept and is now the point.** The rule refuses a value this
process is HOLDING. A forgotten one is absent from the registry, so its row
stays readable and an exact durable replay still returns it. And it cannot
collide with the one sanctioned disclosure: `issue_offer` answers with the
bearer to the caller entitled to it, and the offer row stores a verifier and
never the bearer — asserted against both the column set and the row's actual
bytes.

## Verification

`evidence/gate-after-third-correction-2026-08-25.txt`. `test_secrets` 57/57
with the reviewer's regression kept and both subcases refusing
`integrity.secret-leak`. Full suite 1084, reproduced byte for byte from the
locked installed layout. Nothing added by this correction; three new failures
are W6627 reviewer cases, checked against this change — none raises or
mentions `secret-leak` and none touches an adopted row.

## State

**Awaiting independent re-review.** The claim is not released and no Git
operation was performed.

## Fourth review correction — 2026-08-25

The centralized walk was right and its ORDER was wrong. `boundaries.row`
walked last, after every column rule, and several of those rules name the
value they reject — so a live bearer in a malformed typed column was quoted
into a public schema diagnostic before the walk could answer with the bounded
refusal. The row never left; the validator quoted its secret into the refusal
that did.

The walk is the first content check after the copy now, which is safe because
the copy is already exact built-in data. And because the shape is not specific
to that function, the same ordering is applied at every public door whose
input has already been made exact: both profile paths and the public revival
door. `check_manifest_structure` is deliberately left alone — its input is a
raw caller document, so the schema must establish the shape before anything
traverses it, and that distinction is now recorded rather than left to be
re-derived.

Two cases: all four doors must answer `secret-leak` with no bearer in the
message, and — the other half — the ordinary schema refusal must survive when
nothing is held, because a correction that turned every malformed document
into `secret-leak` would be a different defect with a green gate.

## Verification

`evidence/gate-after-fourth-correction-2026-08-25.txt`. `test_secrets` 60/60.
Full suite 1102, and the locked installed-layout build against a verified idle
engine reports the same 13. Nothing added; the review's one removed. The
single remaining non-baseline failure is W6633's, in review.

## State

**Awaiting independent re-review.** The claim is not released and no Git
operation was performed.
