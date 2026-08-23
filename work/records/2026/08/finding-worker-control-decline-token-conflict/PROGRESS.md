# Progress

Implementer: `baton.claude`. Canonical Baton Work: W4487.

**State: awaiting re-review.** Plan items 3, 4, 6, 8 and 9 are landed and verified;
the Work is passed back rather than closed. W2929 is blocked on it and stays
so until the re-review lands. The round-1 entries below are kept as history;
the round-2 entry at the end answers `review-2026-08-22T14-39-32Z.md`.

## What this Work is

Two FROZEN contracts gave incompatible requirements for one document. W151
`1-ruled` §7 required a declining worker to present the exact unspent claim
bearer; worker-control 1.0 §6.1 and its frozen schema require
`claim_token: null` when `decision=decline`. The schema mechanically rejects
the W151 shape, so no Worker Manager could satisfy both by implementation
choice — and the acceptance boundary explicitly forbade the three ways out
that do not involve a ruling (a partial validator, ignoring the precondition,
or sending a schema-invalid document).

`baton.slaw` ruled on 2026-08-22: keep the non-secret envelope, supersede
W151. This Work writes that ruling into the contracts.

## What landed

### The supersession, where the superseded text lives

W151 `SPEC.md` §1 gains "Superseded by W4487, 2026-08-22". It quotes the old
`Decline` row verbatim, says why it cannot stand, states what replaces it, and
— at equal length — what is NOT superseded: the exact binding, effectively-once,
verifier consumption, no claim, no capacity, and an untouched acceptance path.
The version header and the §0 change table point at it, so a reader who meets
the amended §7 row first is sent back to the history rather than left to assume
the contract always said this. §6 and §7 carry the replacement.

### The other side of the conflict, recorded as such

worker-control `SPEC.md` §0 records that the general "if this document
conflicts with W151, W151 wins" rule is INTACT and that this one conflict was
ruled the other way by an explicit ruling. §6.1 states the asymmetry and why
the two decisions prove themselves differently; §12 gains rule 14, the binding
check no schema can express; §13 gains the invariant that the bearer travels
only where authority is being taken; §14 lists the asymmetry among the
decisions approval covers. The schema's `offerDecideBody` gains a `$comment`
naming the ruling, so a reader of the frozen schema alone learns the `null` is
ruled rather than an oversight.

### Executable evidence, in all three packages

Neither contract had modelled decline at all — which is why the contradiction
survived the M1 freeze and surfaced during W2929 research.

- **W151** (`54 -> 61` tests): decline needs no bearer and kills the token;
  acceptance still requires the exact unspent bearer; a differently bound
  decline terminates neither offer; effectively-once with the reason in the
  signature; a stale decline changes nothing; a declined offer frees the Work
  for a fresh offer; a decline survives manager restart.
- **worker-control** (`12 -> 17` tests): a valid decline envelope with
  `claim_token: null`, invalid vectors for a decline carrying a bearer and an
  accept without one, `validate_offer_decide` for the binding, and the durable
  secret boundary.
- **conformance** (`68 -> 69` obligations, `107 -> 110` cases): obligation
  `C-08` with `C-decline-without-bearer`, `C-decline-carrying-bearer-refused`
  and `C-decline-wrong-binding-refused`. The last asserts that NEITHER the
  named offer nor the bound one is terminated — it would pass vacuously if it
  only checked the named one.

### The freeze note

The M1 cross-contract freeze in
`../finding-v12-isolated-agent-workers/findings/finding-v12-worker-contract/FINDING.md`
states that the family "reuses W151's complete identity and effectively-once
settlement rules" and pins each contract's counts. Both were false after the
amendment, so it now carries the exception, the ruling, and the new counts,
and says this is the first and so far only post-freeze change to the family.

## Verification

- `python3 -m unittest test_assignment_state_model.py` — 61 tests, 0 failures.
- `python3 -m unittest test_contract_model.py` — 17 tests, 0 failures.
- `python3 -m unittest test_conformance_model.py` — 73 tests, 0 failures. The
  register/matrix two-way agreement test is what proves the addition is
  complete rather than partial; the byte-identical shared-definitions test is
  what proves the schema `$comment` did not fork the family.
- `python3 -m unittest test_acp_boundary_model.py` — 56 tests, unchanged and
  still passing, so the third M1 child is unaffected.
- `python3 -B build_cases.py` regenerates `cases.json` from the one place the
  matrix is authored; the prose counts were updated from that output rather
  than by hand.
- 61 + 17 + 56 = 134 relevant design tests, which is the figure W2929's plan
  item 5 now carries.

## Scope

Design records only. No product, authority, runtime, adapter or schema
implementation was touched, and no file outside `work/records/` changed. The
decline path itself belongs to W2929, whose plan item 1a now names the exact
shape instead of an open ruling.

## Review notes

Three decisions this implementation had to make beyond the ruling — writing
the binding as a §12 semantic rule rather than stretching the schema, carrying
the rule into the conformance register, and amending the M1 freeze note — are
in `FINDING.md` under "Implementation revalidation" with their reasoning, along
with three things found while implementing that the ruling did not mention: the
reason riding the operation signature, a declined offer freeing the Work, and
verifier consumption needing to become an observable fact.

## Round 2 — 2026-08-22, answering `review-2026-08-22T14-39-32Z.md`

One P1, correct, and it lands on this record's own "found while implementing"
note: the decline reason rides the operation signature — and nothing
recomputed that signature.

### P1 — a signature that describes nothing is not integrity protection

worker-control §4.2 defines the signature as the canonical digest of the
operation kind and every effective durable operand. The decline vector set it
to the SHA-256 of the BODY, which cannot be that digest because the kind is
not in the body, and `validate_envelope()` never recomputed it. The
reviewer's reproduction — change the durable `reason`, recompute only
`body_digest`, keep the old signature — passed the frozen schema AND the
model, and a manager journalling by that signature would replay the first
decline against conflicting prose.

The ruling replaced a secret with an integrity-protected binding. A binding
nothing recomputes is a field.

### What landed

- **§4.2 fixes the payload**: the canonical digest of
  `{"kind": <envelope kind>, "operands": <durable body operands>}` over §3.2
  bytes, with the receiver's recomputation, the reply exemption, and the three
  exclusions (`extensions` by §2; transport correlation by §4.2 itself).
- **§12 rule 9** now carries the recomputation and its refusal
  (`integrity.digest`), **§14** adds the payload to the approved set, and the
  schema's `$defs.operation` gains a `$comment` so a reader of the frozen
  schema alone learns the signature is not the body digest.
- **A bearer operand rides as its verifier digest**, never literally. Two
  existing rules pulled opposite ways: a signature is durable and §13 keeps
  the bearer off durable surfaces, but dropping the bearer would make an
  accept under a reused operation id with a DIFFERENT token an exact replay
  rather than a collision. The verifier is what the manager already holds
  (§6.1). `null` stays `null`, so a decline's signature commits to the absence
  of a bearer as positively as an accept's commits to which one was presented.
  This is the one genuinely new consequence and it is argued in `FINDING.md`,
  not buried in the diff.
- **Evidence**: `operation_signature_payload`, `operation_signature` and
  `verify_operation_signature` in `contract_model.py`; the decline vector
  regenerated with the computed signature; one new invalid vector
  (`decline-reason-changed-with-stale-operation-signature`, the reviewer's
  exact reproduction); six model tests (`17 -> 23`). The envelope helper now
  COMPUTES each command's operation, so all seventeen envelope shapes assert
  the signature instead of sharing one fixed placeholder.
- **Conformance**: obligation `E-11` and two cases (`69 -> 70` obligations,
  `110 -> 112` cases, 111 local / 112 remote). `E-02` does not cover this —
  it starts from two signatures that already differ.
  `E-operation-signature-covers-kind` reuses one operation id across
  `output.freeze` and `output.collect`, whose bodies are byte-identical, so an
  implementation that signed the body alone would replay the freeze as a
  collect instead of colliding.
- **The M1 freeze note** gains a second amendment, marked a CLARIFICATION
  rather than a supersession, with the reason spelled out: §4.2 never said the
  signature was the body digest, so no conformant document becomes
  nonconformant.
- **W151 needed no change.** Its decline model already binds the reason into
  the replay signature and its collision regression passes; the two contracts
  agree on the operand set and neither includes the bearer. Re-checked rather
  than assumed.

### Two failures, kept separate

A document whose signature does not describe it is refused at validation
(`integrity.digest`). A document that honestly describes a DIFFERENT
operation under a reused id is refused at the ledger
(`refused.operation-collision`). Neither catches the other's case;
`test_a_reused_id_with_its_own_valid_signature_is_a_collision` validates the
second document successfully first, so the two stages are visibly distinct.

### Mutation-checked

Removing the `verify_operation_signature` call from `validate_envelope` fails
exactly three cases — the stale-signature vector, the stale-signature model
test and the reply-exemption test — and nothing else. Restored: 23/23.

### Verification

- `test_assignment_state_model.py` — 61 tests, 0 failures (unchanged).
- `test_contract_model.py` — **23 tests**, 0 failures (17 before).
- `test_conformance_model.py` — 73 tests, 0 failures; the pinned case count in
  `test_every_case_document_validates_and_reseals` moved `110 -> 112` with the
  register, and the register/matrix two-way agreement test is what proves the
  addition is complete rather than partial.
- `test_acp_boundary_model.py` — 56 tests, 0 failures, unaffected.
- `python3 -B build_cases.py` regenerated `cases.json`; every prose count in
  this entry is taken from that output, not from arithmetic.

### Operational finding — the frozen schema file was reformatted

Adding the `$comment` to `$defs.operation` rewrote
`schema/worker-control-1.0.schema.json` in the family's
`json.dumps(indent=2)` layout — byte-for-byte what
`conformance-1.0.schema.json` uses, but NOT this file's previous layout,
which is not recoverable from the working tree (the subtree is untracked, so
Git holds no copy). The semantic content is unchanged and the claim is
checkable: the file was parsed with ordered pairs and rewritten with exactly
one key inserted, so key order and every value are preserved, and its meaning
is exercised by the 23 worker-control tests plus the conformance package's
byte-identical shared-definitions and register/schema agreement tests. The
whitespace diff is large and I would rather the reviewer read this than
discover it. Reported, not worked around.

### Scope

Design records only. No product, authority, runtime, adapter or schema
implementation was touched, and no file outside `work/records/` changed.

## Round 3 — 2026-08-22, answering `review-2026-08-22T14-57-26Z.md`

One P1 and one P2, both right. The P1 is round 2's own new consequence being
wrong: I introduced `claim_token_verifier`, described it as the value W151
already stores, and computed a different one.

### P1 — two contracts, two verifiers, one name

worker-control computed `digest(bearer)`: SHA-256 over the bearer's JCS JSON
encoding, quotes included. W151 stored SHA-256 over the bearer's raw UTF-8
bytes as bare hex. For `"x" * 43`:

```text
W151 stored        cc0b1c2c66f3bb9fd1a081c626ba1bef62f6f96441a43be15268523776ac26a1
worker-control     sha256:6162a6f0b60f2860a9712724c281a7e83d2a74adf304a9dbaf54d43d5aeceadf
```

Different hashed byte sequences. Two conforming peers would compute different
operation signatures for the same acceptance — the ambiguity §4.2's
clarification existed to remove, reintroduced by the clarification.

**Why both packages were green.** Each asserted its own self-consistency: 23
worker-control tests about the worker-control helper, 61 W151 tests about the
assignment model. Neither could see the other. That is the third time in this
record that checking against the other side rather than against my own reading
is what found the defect.

### Changed

- **W151 §7 pins the derivation**, because W151 owns the offer record:
  `"sha256:" + lowercase hex of SHA-256 over the bearer's own UTF-8 bytes`.
  Two decisions inside it, both stated in `FINDING.md` rather than left in the
  diff: the token's OWN BYTES (a JSON encoding drags escaping rules into the
  value), and the `sha256:` prefix (§3.2's one representation, and it names
  the algorithm). The prefix half changes what W151's offer record STORES —
  said plainly, not presented as reformatting.
- **worker-control §4.2 names that derivation** instead of defining a second
  one; §14 adds it to the approved set; the model repeats it verbatim rather
  than importing across independent design records.
- **A golden pair is pinned as LITERALS in both models.** A comparison of two
  recomputations agrees with any derivation, including two wrong ones that
  match; a literal fails when either side moves.
- **The conformance package carries the cross-contract case**, because that is
  the package whose job is agreement between contracts — it already asserts
  the shared schema definitions are byte-identical rather than trusting two
  copies. It compares both derivations over bearers neither package pins and
  asserts the value W151's OFFER RECORD holds equals worker-control's
  `claim_token_verifier`.
- The M1 freeze note gains its third amendment.

### The decline vector did not move

A decline carries `claim_token: null`, so no derivation is involved and its
operation signature is byte-identical before and after. That is what says the
correction touches the acceptance path only, and I checked it rather than
assuming it.

### P2 — the W2929 handoff

`finding-v12-worker-manager-core/PLAN.md` gains item 1b naming BOTH integrity
boundaries found in review — the §4.2 operation-signature recomputation, and
this verifier derivation with an explicit instruction not to invent a second
one in the manager's durable stores — and item 5's design-test count moves to
144, with 122 and 134 kept as the superseded history of how it moved.

### Tests

- W151 `61 -> 64`: the golden pair against a literal; the bytes are hashed and
  not a JSON encoding of them, over tokens whose encodings differ from their
  bytes; and the OFFER RECORD stores exactly that verifier.
- worker-control `23 -> 24`: the same derivation, the same golden literal, the
  explicit assertion that it is NOT `digest(bearer)`, and that a decline's
  operand stays `null`. The round-2 case that asserted `digest("x" * 43)` is
  corrected — it was asserting the defect.
- conformance `73 -> 74`: the cross-contract golden case.

Mutation-checked: reverting either derivation fails the cross-contract case
(and, in worker-control's direction, two of its own).

### Verification

`64 / 24 / 74 / 56`, all passing. Relevant design-test total 144
(`64 + 24 + 56`), which is the figure W2929's plan item 5 now carries.
`cases.json` is unchanged this round — the register gained nothing, because
contract agreement is not a runtime obligation.

### Unchanged

Design records only; no file outside `work/records/` changed. The schema
reformatting disclosed last round is unchanged and the reviewer has ruled it
not a semantic finding.

### State

**Awaiting re-review.**
