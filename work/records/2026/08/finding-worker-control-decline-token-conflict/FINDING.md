# Finding: worker-control decline token conflicts with W151

Canonical Baton Work: W4487. Discovered while researching W2929 at
`work/records/2026/08/finding-v12-isolated-agent-workers/findings/finding-v12-local-isolated-execution/findings/finding-v12-worker-manager-core/`.

## Observed — 2026-08-22

The frozen contracts give incompatible requirements for a declined offer:

- W151 `finding-v12-assignment-state-machine/SPEC.md` section 7 says
  `Decline` requires the exact unspent token and atomically consumes its
  verifier.
- Worker-control 1.0 `finding-worker-control-api-manifests/SPEC.md` section
  6.1 says the token is present for accept, while
  `schema/worker-control-1.0.schema.json` requires
  `claim_token: null` when `decision=decline`.

Both specifications are frozen and the schema mechanically rejects the W151
shape. A Worker Manager cannot satisfy both by implementation choice.

## Confirmed boundary

Do not accept a partial-validator workaround, silently ignore the W151 token
precondition, or send a schema-invalid decline. The authority owner must rule
which exact authorization terminates an issued offer without accepting it.
The superseded contract text must be marked explicitly, and the applicable
schema, executable vectors and cross-contract freeze evidence must be
regenerated together before W2929 implements decline.

## Proposed ruling

Prefer keeping worker-control's non-secret decline shape and clarify W151 so
an exact, integrity-protected `offer.decide` operation bound to
`(offer_id, runtime_attempt_id, work_ref, decision, reason)` may consume the
durable verifier without echoing the bearer. Acceptance alone would continue
to require and validate the bearer. This avoids transmitting a secret merely
to reject authority while retaining an exact CAS and effectively-once
operation. This is a proposal, not authority.

## Acceptance

- One contract explicitly supersedes its conflicting text.
- The 1.0 schema and prose accept the same decline document.
- Decline is bound to the exact issued offer, is effectively once, consumes
  the verifier, mints no claim, and cannot terminate another offer.
- Accept still requires the exact unspent, unexpired bearer.
- W151, worker-control and cross-contract executable gates pass.

## Authority ruling — confirmed 2026-08-22

The approver accepts the proposed non-secret decline shape. This ruling
supersedes W151 section 7 wherever it requires a declining worker to echo the
claim bearer. A decline carries `claim_token: null` and is authorized by the
integrity-protected `offer.decide` operation bound to the exact issued offer,
runtime attempt, Work, decision, and reason. The manager validates that binding
and atomically consumes the offer's durable verifier without minting a claim.

Acceptance remains different: it must present the exact unspent, unexpired
bearer and succeeds only through the canonical claim transaction. A stale,
foreign, replay-colliding, or differently bound decline refuses and cannot
terminate another offer. An exact replay returns the one committed decline.

Implementation must explicitly mark the conflicting W151 text superseded and
regenerate worker-control prose/schema, W151 vectors, and cross-contract freeze
evidence together before W2929 implements this transition.

## Implementation revalidation — 2026-08-22 (baton.claude, W4487)

Every claim above was re-checked against the tree before acting. The
contradiction is real and exactly as reported, the ruling is unchanged, and
nothing here supersedes it.

**Confirmed against the tree.** W151 `1-ruled` §7's `Decline` row reads
"agent through manager; exact unspent token". `worker-control-1.0.schema.json`
`$defs.offerDecideBody` requires `claim_token` to be present and constrains it
to `null` when `decision=decline`, so the W151 shape is a schema-invalid
document rather than a discouraged one. Both contracts were frozen by the M1
cross-contract approval of 2026-08-22.

**Confirmed: neither contract had modelled decline at all.** W151's
`evidence/assignment_state_model.py` had no decline path, and
`worker-control`'s vectors carried no `offer.decide` document of either
decision. The contradiction was therefore invisible to both executable
packages — which is why it surfaced during W2929 research rather than at
freeze. Adding the scenarios was not bookkeeping; it is what makes the ruled
shape checkable.

### Pinned implementation decisions

- **The supersession is written where the superseded text lives, with the old
  row quoted.** W151 §1 gains "Superseded by W4487, 2026-08-22", carrying the
  old `Decline` row verbatim, why it cannot stand, what replaces it, and — at
  equal length — what is NOT superseded. A reader who finds the amended §7 row
  first is pointed back to it from the version header and the §0 change table.
- **Worker-control records that this is the ONE conflict ruled its way.** §0's
  precedence rule ("if this document conflicts with W151, W151 wins") is not
  weakened in general. Quietly leaving it while the schema wins in practice
  would make the next conflict undecidable, so §0 says a ruling settled this
  one and that nothing here may settle the next one on its own authority.
- **The binding is a semantic rule, not a schema rule, and it is written down
  as one.** Schema can prove `claim_token` is `null` for a decline; it cannot
  prove the body names one issued offer. That check is what the bearer used to
  stand in for, so it is worker-control §12 rule 14 beside the twelve other
  rules the schema cannot express, and it is modelled in
  `validate_offer_decide`.
- **The conformance register carries it too.** Obligation `C-08` and three
  cases. The rule the two frozen contracts had to be re-ruled over must not be
  the one nothing certifies, and `C-decline-wrong-binding-refused` asserts that
  NEITHER the named offer nor the bound one is terminated — a case that would
  pass vacuously if it only checked the named one.
- **The M1 freeze note is amended, not left behind.** The freeze states the
  family "reuses W151's complete identity and effectively-once settlement
  rules" and pins each contract's counts. A supersession recorded in one
  contract while the freeze kept the old counts would describe a family that
  no longer exists, so all three were amended together and the freeze says so.
- **Acceptance was deliberately left alone, and there is a test for it.**
  "Decline carries no token" has an obvious wrong reading in which the bearer
  stops mattering. `test_accept_still_requires_the_exact_unspent_bearer` and
  `test_the_bearer_asymmetry_is_enforced_in_both_directions` exist so that
  reading fails loudly.

### Found while implementing, not in the ruling

- **The decline reason has to ride the operation signature.** W151 §7 already
  requires every durable operand — including prose — in the replay signature.
  Since the reason is now part of what authorizes the decline, reusing one
  operation id with different prose is an operand collision rather than a
  replay, and the scenario pins it.
- **A declined offer must free the Work for a fresh offer.** §6's per-Work
  uniqueness rule admits only one nonterminal offer, so `declined` being
  terminal is the whole practical point of declining rather than waiting for
  expiry. Nothing said so; the scenario now does.
- **Verifier consumption needed to become observable.** The model implied it
  through the offer's state name. "Consumes the verifier" is an acceptance
  criterion of this Work, so the record now carries an explicit
  `verifier_spent` fact that acceptance, decline and expiry all set, and
  acceptance refuses against it.

### Acceptance not established here

This Work amends design records. It authorizes no implementation: W2929 is
where the manager's decline path is written, and its plan item 1a now names
the exact shape to implement rather than an open ruling.

## Review round 1 — 2026-08-22T14:39:32Z

`review-2026-08-22T14-39-32Z.md` requested one P1. It was right, and it lands
on the sentence in "Found while implementing" directly above: the decline
reason rides the operation signature — and nothing on the worker-control side
recomputed that signature.

### [P1] The operation signature was never validated, so it could go stale

worker-control §4.2 defines the signature as "the canonical digest of the
operation kind and every effective durable operand". The new decline vector
set `operation.signature_digest` to the exact SHA-256 of the BODY, which
cannot be that digest because the kind is not in the body — and
`contract_model.validate_envelope()` verified only `body_digest` and never
recomputed the signature at all. The reviewer changed the vector's durable
`reason`, recomputed only `body_digest`, left the signature alone, and both
the frozen JSON Schema validator and the model accepted the document. A
manager journalling by that unchanged signature would treat conflicting prose
as an exact retry and replay the first decline.

**Why this is the same defect as the ruling, one layer down.** The ruling
replaced a SECRET with an integrity-protected BINDING. An integrity-protected
binding that nothing recomputes is not integrity-protected; it is a field. The
bearer at least had to be possessed.

### The payload is now exact, and that is a clarification

§4.2 fixes it as the canonical digest of

```json
{ "kind": "<envelope kind>", "operands": { "<durable body operands>": "..." } }
```

**This does not supersede anything.** §4.2 always required the kind and every
durable operand; it simply did not say in what shape, and two peers that
compute a signature differently do not share an identity. No document that
satisfied the old sentence as written stops being conformant. The old text is
therefore extended in place rather than quoted-and-replaced — the treatment
the W151 §7 decline row got, and rightly, because that one reversed a
requirement.

Three decisions inside the payload, each of which could defensibly have gone
the other way:

- **The kind is in the payload**, so the signature is never the body digest.
  `output.freeze` and `output.collect` carry the same body: an implementation
  that signed the body alone would replay a freeze as a collect under one
  reused operation id. That pair is now the conformance case.
- **A bearer operand rides as its VERIFIER digest, never literally.** This is
  the one genuinely new consequence, and it was forced by two existing rules
  pulling opposite ways. A signature is durable — it lands in the manager's
  operation journal and in W151's — and §13 keeps the claim bearer off every
  durable surface, so it cannot be carried literally. But dropping it would
  make an accept under a reused operation id with a DIFFERENT token an exact
  REPLAY rather than a collision, which contradicts "every effective durable
  operand" and would let a wrong bearer collect a committed claim result. The
  verifier is what the manager already stores for the offer (§6.1), so
  `claim_token` contributes `claim_token_verifier`, and `null` stays `null`:
  a decline's signature commits to the ABSENCE of a bearer exactly as
  positively as an accept's commits to which one was presented.
- **Replies are exempt from the recomputation.** §5 says a reply carries "the
  same operation" as its request, so its signature is the REQUEST's and its
  body is a result rather than the operands. Recomputing over a reply body
  would refuse every conforming reply. The exemption is keyed on
  `message_type`, and a test sends the same document as a command to prove the
  exemption is not a hole.

### Two failures, not one, and both are needed

The reviewer asked for the stale-signature vector and for the replay-ledger
collision case to be kept separate. They catch different documents:

| document | refused by | because |
| --- | --- | --- |
| changed reason, recomputed body digest, OLD signature | `integrity.digest` at validation | its signature does not describe it |
| changed reason, recomputed body digest, its OWN correct signature, REUSED operation id | `refused.operation-collision` at the ledger | it honestly describes a different operation under a committed id |

Neither catches the other's case, and only the first is new.

### Certification

`E-11` and two cases. §12 rule 9 required the signature to include every
durable operand and no obligation certified that anybody recomputed it —
which is exactly how the defect survived. `E-02` does not cover it: it starts
from two signatures that already differ.

### Open — the frozen schema file was reformatted

Adding the `$comment` to `$defs.operation` rewrote
`schema/worker-control-1.0.schema.json` in the family's `json.dumps(indent=2)`
style, which is what `conformance-1.0.schema.json` uses byte-for-byte but was
NOT this file's previous layout, and the previous bytes are not recoverable
from the working tree. The semantic content is unchanged: the file was read
with ordered pairs and rewritten with exactly one key added, so key order and
every value are preserved, and the schema's meaning is exercised by all 23
worker-control model tests plus the conformance package's byte-identical
shared-definitions and register/schema agreement tests. Recorded here rather
than left for the reviewer to discover from a whitespace diff.

## Re-review round 3 — 2026-08-22T14:57:26Z

`review-2026-08-22T14-57-26Z.md`: one P1 and one P2. Both right. The P1 is the
round-2 correction's own new consequence turning out to be wrong in a way
neither package could see.

### [P1] "The verifier the manager already holds" was two different values

Round 2 introduced `claim_token_verifier` and described it as the value W151
already stores. It computed `digest(bearer)` — SHA-256 over the bearer's JCS
JSON encoding, quotes included, `sha256:`-prefixed. W151's manager stored
SHA-256 over the bearer's raw UTF-8 bytes as bare hexadecimal. For `"x" * 43`:

```text
W151 stored        cc0b1c2c66f3bb9fd1a081c626ba1bef62f6f96441a43be15268523776ac26a1
worker-control     sha256:6162a6f0b60f2860a9712724c281a7e83d2a74adf304a9dbaf54d43d5aeceadf
```

Different hashed byte sequences, so two conforming peers derive different
operation signatures for the same acceptance — the exact ambiguity §4.2's
clarification existed to remove, reintroduced by the clarification.

**Why neither package caught it, which is the part worth keeping.** The 23
worker-control tests asserted the worker-control helper against itself; the 61
W151 tests asserted the assignment model against itself. Both were green and
both were describing the same thing differently. A self-consistent answer to
the wrong question is what a test written from one side of a boundary
produces, and it is the third time in this record that measuring against the
other side is what found the defect.

### One derivation, owned by the contract that owns the record

W151 owns the offer record, so W151 §7 now pins it:

```text
verifier = "sha256:" + lowercase hex of SHA-256 over the bearer's own UTF-8 bytes
```

Two decisions inside that, and both could have gone the other way:

- **The token's own bytes, not a JSON encoding of them.** A bearer is a secret
  string, not a JSON document. Hashing its encoding brings the quotes and the
  escaping rules into the value, so a peer that escapes `"`, `\` or a
  non-ASCII character differently — or does not use JCS for a bare string at
  all — derives a different verifier for the same secret. The bytes have one
  answer. This is the half worker-control had wrong.
- **The `sha256:` prefix.** The family's one digest representation (§3.2), what
  the frozen schema's `digest` type accepts, and it names the algorithm, so
  changing it later is visible rather than a silent reinterpretation of 64 hex
  characters. This is the half W151 had wrong, and correcting it changes what
  W151's offer record stores — stated plainly rather than presented as
  reformatting.

Both are clarifications rather than supersessions: W151 never said what the
verifier was, and worker-control never said the payload used a second value.
Nothing previously stated is reversed.

### The golden pair, and why it is a literal

`GOLDEN_BEARER` / `GOLDEN_VERIFIER` are pinned as LITERALS in both models. A
comparison of two recomputations would agree with any derivation, including
two wrong ones that happened to match; a literal fails when either side moves.
The conformance package — the one whose job is cross-contract agreement, and
which already asserts the shared schema definitions are byte-identical rather
than trusting two copies — carries the case that compares them, over bearers
neither package pins, and asserts that what W151's OFFER RECORD stores equals
the `claim_token_verifier` in worker-control's signature payload.

Mutation-checked: reverting either derivation fails the cross-contract case.

### The decline vector did not change, and that is the point

A decline carries `claim_token: null`, so its verifier operand is `null` and no
derivation is involved. The frozen decline vector's operation signature is
byte-identical before and after this correction, which is what says the
correction touches the acceptance path only.

### [P2] The W2929 handoff described the pre-review contract

W4487 exists to unblock W2929, and its plan named the decline shape without
either integrity boundary found in review. `finding-v12-worker-manager-core/
PLAN.md` gains item 1b carrying both — the operation-signature recomputation
with its exact payload, and this verifier derivation with an explicit
instruction not to derive a second value in the manager's stores — and item
5's design-test count is corrected to 144, with the earlier 122 and 134 kept
as the superseded history of how it moved rather than overwritten.

## Re-review round 4 — 2026-08-22T15:34:43Z

`review-2026-08-22T15-34-43Z.md`: signed off with no findings. The two
contracts now produce one verifier from the same bearer, the conformance case
tests the real stored-offer-to-signature-operand boundary rather than either
package against itself, and W2929 carries both integrity rules and the updated
144-test gate. Focused verification passed at `64 / 24 / 74 / 56`; `git diff
--check` is clean.
