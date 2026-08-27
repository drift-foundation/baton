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

## Fifth review correction — 2026-08-25

The review's two doors are corrected as it asked. The **re-audit it asked for
in the same breath is what changed the shape of the fix**, and it is the part
worth reading.

**The re-audit was a probe, not a reading.** The previous four corrections were
each a careful argument about which doors quote their operands, and each
produced an incomplete answer. So this one drove every callable in
`worker_manager.__all__` with the live bearer in every operand it takes and
read what came back. **Thirty public surfaces answered with a refusal whose
message contained the bearer** — not two. The full list is in the evidence.

**And they are not all shape diagnostics.** `activate_assignment`,
`settle_claim`, `submit_claim`, `record_frozen_result` and
`publish_inquiry_answer` leak through `refused.precondition` messages that
simply NAME the attempt or operation they could not find. There is no walk to
put earlier at those doors and no shape validator to put it before;
`name_value` renders a rejected `str` verbatim by design, which is what makes
every refusal that names what it rejects a §13 surface.

**So the guard is at `ContractRefusal.__init__`.** That is third review [P1]'s
own lesson — a guard at the one crossing cannot be forgotten by a caller
written later — applied one layer further out than `boundaries.row`. Every
diagnostic in this distribution becomes durable and portable at that
constructor, which already establishes that the message is text, that it is
encodable and that it is bounded. **The acceptance's fourth line is "bounded
diagnostics that cannot themselves leak", and it belongs beside those three
rather than in a list of doors I maintain.** A refusal carrying a live bearer
is replaced by `integrity.secret-leak` with this build's own constant prose,
keeping the raising site's durability, because a leak found while composing a
diagnostic does not un-write what had already been written.

**The door-local walks are kept, and they are not redundant.** The crossing
catches CONTAINMENT. The walk at a door catches the half no message reveals: a
member NAMED for a secret is refused by its name whatever it holds. A door that
walks also answers about its operand rather than about the diagnostic somebody
tried to build from it.

**The review's refutation was right and I had it backwards.** The fourth
correction said an unowned caller document cannot be walked safely. `_walk`
traverses only exact built-in `dict`, `list`, `tuple` and `str` and returns
without reading anything else, so it runs no caller behaviour at all. Both
named doors walk the raw operand now, and so does `seal_refusal` — a third door
the re-audit found, which quoted a live bearer in its own type diagnostic.

**One recursion, found by asking the question rather than by asserting it.**
The first version raised the substitute through the same constructor. A case
that registers the substitute's own prose as a secret drove it to
`RecursionError`. The exemption is on that exact message, and it leaks nothing
because in the one case it fires the message is a constant containing no caller
data.

## The gate the probe became

`NoPublicRefusalQuotesALiveBearer` derives the same universe
`EveryPublicSurfaceIsAccountedFor` does — asserted EQUAL to it, so the two
cannot drift — drives every surface with the bearer live, and requires the
sweep to have driven something that refused, because a sweep where everything
returns `None` proves nothing. `TheRefusalConstructorIsTheOneCrossing` holds
the crossing itself: the substitution, its durability, the recursion, the
untouched ordinary refusal, the forgotten value, and the message owner's three
older rules still firing.

**The gate can fail — measured.** With the crossing disabled and nothing else
changed, `test_secrets` is `FAILED (failures=31)`.

## One defect of my own, recorded because it was mine

The first version of the handshake change replaced the literal label at
`boundaries.document(profile, "an agent-session profile")` with the local
`what`. The boundary inventory attributes an owned entry BY THE LITERAL LABEL
AT THE SITE — the comment two lines above says exactly that — and it raises
from inside a helper many cases call. One variable produced **546 failures**.
The literal is restored. It is here because "546" reads as a catastrophe and
was one character, and because the next person to tidy that call needs to know.

## Verification

`evidence/gate-after-fifth-correction-2026-08-25.txt`.

- `test_secrets` **70/70**, with the reviewer's additive two-door regression
  kept and both subcases answering `('secret-leak', False)`.
- Adjacent handshake, interrogation, store, offers, contracts-inventory, pod,
  text-sweep, dependencies and diagnostic-rendering: **295, OK**.
- Full source suite: **1182, 12 failures and 1 error**. Seven are
  `test_boundary_inventory` and six are the recorded `oci`/`worker_container`
  engine baseline. **None is this correction's**, and the boundary-inventory
  seven are proved rather than assumed: a copy of the tree with exactly this
  correction removed fails the same seven test names.
- Locked installed-layout build (`just build`): **1182, the same twelve
  failures and one error**, reproduced from site-packages rather than from
  `src/`, with the contracts package still exporting exactly 41 names — this
  correction adds no public name.

Nothing added to the suite's failures; nothing removed from it either. The
`test_boundary_inventory` seven belong to other in-flight Work that has that
file modified, and they name `documents.py:freeze_requested`,
`handshake.py:certified_agent_session_profile` and
`workspaces.py:materialize_git_source` — three sites this correction does not
touch. Reported, not fixed.

## State

**Awaiting independent re-review.** The claim is not released and no Git
operation was performed.


## Sixth review correction — 2026-08-25

The review is right, and the mistake was in my own comment rather than only in
my code. It justified exempting the substitute like this:

    "... which it can, if the live value happens to BE this build's
     substitute prose."

**BE.** Equality reasoning, three lines beneath a rule whose whole content is
that the value test is CONTAINMENT and not equality. The registry admits any
non-empty value and §13's own contract admits a 32-character claim token, so a
live bearer can be a substring of that constant — and the exempt replacement
carried the entire live value out.

**The replacement is proved now, not exempted.** It passes the same containment
test as every other message, and when the prose cannot pass it the message is
EMPTY. The empty message is safe by construction rather than by inspection: it
is the one string a non-empty value cannot be contained in, and
`remember_secret` refuses an empty value. That is also what bottoms the
recursion — the substitute's own construction re-enters the guard, and a
substitute of `""` cannot fail it — so the exemption was not even buying
termination that this does not buy honestly.

**What does not give way is the closed pair.** `integrity.secret-leak` is the
diagnostic and the raising site's durability still propagates; the readable
prose is the part that can be spent, and only when it would otherwise leak.

**One snapshot answers both questions.** A refusal asks the registry about two
strings now — the message and the replacement — and asking twice would let the
registry move between the answers. One snapshot makes them one decision, which
is the rule `_walk` already follows for a document.

## One of my own assertions was the defect

`test_the_substitute_is_this_build_s_own_prose_and_cannot_recurse` required a
refusal whose message IS the substitute prose to be constructed UNCHANGED while
that prose was live. That is the equality exemption written down as an
expectation. It is replaced by
`test_the_substitute_is_proved_by_containment_and_never_exempted`, which
requires that construction to refuse and the answer not to contain the live
value. Nothing was weakened; the replacement asserts strictly more.

Four cases are new: the empty fallback keeps the closed pair and the
durability; an empty message is accepted because it can carry nothing (the
terminal case, stated as its own fact, because without it the fallback has no
bottom); the prose is still used when it carries nothing live; and one snapshot
answers both questions, counted rather than assumed.

## Verification

`evidence/gate-after-sixth-correction-2026-08-25.txt`.

- `test_secrets` **75/75** (71 before), with the reviewer's additive regression
  kept as written and the full public-surface sweep untouched.
- **Can-actually-fail, measured**: restoring the equality exemption and the
  constant replacement fails the reviewer's case and both new ones that bear
  on it. The file was restored byte for byte.
- Adjacent twelve modules **485, OK**.
- Full source suite and locked installed-layout build both **1223, eleven
  failures**, and **`test_secrets` does not appear in that list**. It was the
  one W6630 failure the suite carried. Nothing was added; one was removed.

## Reported and not fixed

The eleven are seven long-standing `test_boundary_inventory` failures and four
reviewer regressions on Work this claim does not hold — two on **W6632**
(`test_oci`) and two on **W6633** (`tests.tools.test_worker_image_build`).
Both are routed to `baton.feat`, and each was reported on its own thread when
it was found.

## State

**Awaiting independent re-review.** The claim is not released and no Git
operation was performed.


## Seventh review correction — 2026-08-26

The review is right, and this is the SIXTH time this Work has been corrected
for one shape: a diagnostic standing in front of the guard. A manifest door, a
row boundary, two document owners, thirty public surfaces, the substitute
message — and now the two checks that run before the message is even looked
at, inside the very function the crossing lives in.

**The pair assertions rendered the rejected operand with `repr`**, so a live
bearer supplied as an invalid category or code left in an `AssertionError` the
crossing never saw. Classifying an invalid pair as a raising-site defect is
right and I have not changed it; it does not make an assertion carrying a live
secret safe.

**Proved, not suppressed.** `_rejected` names a rejected category or code from
what is safe to say: a non-string by its type, a string the registry says is
live by a sentence explaining why it is not quoted, and anything else
verbatim. A misspelled `integrty` is still quoted — that is the whole use of
the message — and only a live value gives way, to an explanation rather than to
silence, because a reader has to be able to tell a redaction from a missing
value.

**One snapshot for the whole construction**, so the pair and the message are
decided against one view of the registry.

## A defect the review did not name, closed by the same change

`{value!r}` runs `__repr__`, which is caller-chosen code, inside a diagnostic.
This module's own `name_value` has refused to do that since W6782 — "a refusal
never RUNS the value it refuses" — and these two assertions were doing it. A
pair operand with a raising `__repr__` replaced the assertion with an exception
of the caller's choosing. It is named by its type now, read without metaclass
dispatch, and a case drives it with a hostile `__repr__`.

## Verification

`evidence/gate-after-seventh-correction-2026-08-26.txt`.

- `test_secrets` **81/81** (76 before): the review's regression kept as
  written, five added.
- **Measured to fail against the old rendering**: restoring `{category!r}` and
  `{code!r}` gives four failures and one ERROR, and the error is the hostile
  `__repr__` escaping the constructor — the unnamed defect showing itself.
  Restored byte for byte.
- Adjacent **590**; source suite and locked build both **1239, eleven
  failures**, and **`test_secrets` is not among them**.

## Reported and not fixed

- **W6632**, two `test_oci` cases, already reported on T6632.
- **W6633**, two new `tests.tools.test_worker_image_build` cases posted
  mid-correction. Both are real, and the first **contradicts a decision I
  wrote and defended**: I kept a regular file's mtime because it "came out of
  the build context and is content", but the version-control source carries
  bytes and the executable bit and NOT mtime, so two checkouts of one recipe
  differ and the reproducible identity depends on when each was populated. The
  second is a cleanup in a `finally` that discards its result, so a build can
  return a pinnable digest while its unnormalized image survives. Reported on
  T6633 with the direction I would take.

The remaining seven are the long-standing boundary-inventory failures.

## State

**Awaiting independent re-review.** The claim is not released and no Git
operation was performed.


## Eighth review correction — 2026-08-26

The review is right, and it is right in the way that matters: last round I
fixed the two reproductions I was shown and then wrote the general claim
anyway — "every diagnostic in this constructor is now behind the same rule".
Three more were standing.

**Membership hashed a rejected operand** before the safe renderer ran, so
`__hash__` — caller code — executed inside the check meant to own it, and an
unhashable operand escaped as a raw `TypeError`. **`_rejected` proved the
operand and not the text it composed**, so a live value equal to a substring of
its redaction sentence or of a rendered type name left verbatim: safe
provenance is not safe content, which is the sixth review's containment finding
in a second place. **And two assertions still used `type(value).__name__`**,
consulting a caller-controlled metaclass this module has refused to consult
since W6782.

**So the correction is a construction rather than three patches**, which is
what the review asked for. `_defect` owns the COMPLETE text of every assertion
leaving this constructor: preferred text, then a constant, then the empty
string, each proved against the same snapshot, the last terminal. It composes
nothing that re-enters the constructor, so there is nothing to bottom out.

The per-operand renderer stays, and the two layers do different jobs:
`_rejected` keeps an ordinary misspelled `integrty` quoted and the sentence
readable, `_defect` guarantees the invariant whatever was composed.

## What makes it a construction and not another claim

`test_every_assertion_in_the_constructor_goes_through_the_one_owner` reads the
source with `ast` and requires every `raise AssertionError` in `__init__` to
pass its text through `_defect`. Its sibling requires no `.__name__` lookup
anywhere in the class. **A diagnostic added tomorrow is proved tomorrow
instead of becoming the next reproduction** — which is the difference between
this and the decision I recorded last round.

## Verification

`evidence/gate-after-eighth-correction-2026-08-26.txt`.

- `test_secrets` **90/90** (84 before): the review's three kept as written,
  six added — the two AST gates, a hostile-hash case driven four ways, the
  whole-text give-way, a live TYPE NAME (the review's own example), and an
  ordinary-defect case covering all six assertions.
- **Measured to fail without the correction**: 7 failures and 8 errors,
  including all three of the review's. Restored byte for byte.
- Adjacent **682 OK**. Source suite and locked build both **1250, nine
  failures**, and `test_secrets` is not among them.
- **The tree was hashed before and after the build and was identical.** The
  previous W6632 evidence recorded a pair of numbers taken across a reviewer's
  edit; this pair is two measurements of one thing.

## Reported and not fixed

**W6633**, the two `tests.tools.test_worker_image_build` cases, already
reported on T6633. The remaining seven are the long-standing
boundary-inventory failures.

## State

**Awaiting independent re-review.** The claim is not released and no Git
operation was performed.
