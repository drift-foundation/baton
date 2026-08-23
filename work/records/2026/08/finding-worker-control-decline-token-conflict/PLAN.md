# Plan

1. [done 2026-08-22] Pin the W151 versus worker-control 1.0 contradiction and
   bind it to W4487.
2. [done 2026-08-22] Rule that decline keeps `claim_token: null`; the exact
   integrity-protected `offer.decide` binding consumes the verifier without
   echoing the bearer. Acceptance alone requires the bearer. Mark W151's
   conflicting token requirement explicitly superseded.
3. [done 2026-08-22] Regenerate the affected contracts, schema, vectors and
   executable cross-contract evidence — TOGETHER, because a supersession
   recorded in one frozen contract while the others keep the old text and
   counts describes a family that no longer exists.
   - W151 `SPEC.md`: version header, §0 change table, §1 dated supersession
     with the old row quoted, §6 and §7. Evidence: seven decline scenarios,
     54 -> 61 tests.
   - worker-control `SPEC.md` §0/§6.1/§12 rule 14/§13/§14, and a `$comment`
     on `offerDecideBody` naming the ruling. Evidence: one valid and two
     invalid decline vectors, `validate_offer_decide`, 12 -> 17 tests.
   - conformance `SPEC.md` and register: obligation `C-08` and three cases,
     68 -> 69 obligations and 107 -> 110 cases, 109 local / 110 remote.
   - the M1 cross-contract freeze note in
     `../finding-v12-isolated-agent-workers/findings/finding-v12-worker-contract/FINDING.md`.
4. [done 2026-08-22] Returned the ruled shape to W2929: its plan item 1a now
   states the exact decline shape to implement instead of naming an open
   ruling, and items 2-4 are no longer queued behind this Work.
5. [done 2026-08-22] Independent review of the amendment:
   `review-2026-08-22T14-39-32Z.md`, changes requested, one P1.
6. [done 2026-08-22] Correct the P1: the operation signature was never
   recomputed, so a decline could change its durable reason, recompute only
   its body digest, keep the old signature and replay the first decline.
   - worker-control `SPEC.md` §4.2 fixes the payload exactly, states the
     receiver's recomputation and the reply exemption, and explains the
     bearer's presence as its verifier digest; §12 rule 9 carries the
     recomputation; §14 adds it to the approved set; the schema's `operation`
     definition gains a `$comment`.
   - Evidence: `operation_signature_payload`/`operation_signature`/
     `verify_operation_signature`, the regenerated decline vector, one invalid
     vector for the stale signature, and six model tests (17 -> 23).
   - conformance: obligation `E-11` and two cases (69 -> 70 obligations,
     110 -> 112 cases, 111 local / 112 remote).
   - the M1 freeze note gains its second amendment, marked a CLARIFICATION
     rather than a supersession and saying why.
7. [done 2026-08-22] Independent re-review:
   `review-2026-08-22T14-57-26Z.md`, changes requested. The operation
   signature recomputation works, but worker-control and W151 derive different
   verifier values from the same bearer, and W2929's downstream plan still
   carries the pre-review signature boundary and test count.
8. [done 2026-08-22] Correct the P1: the bearer-to-verifier transformation
   added by item 6 computed SHA-256 over the bearer's JCS JSON encoding, while
   W151 — the contract that OWNS the offer record — stored SHA-256 over the
   bearer's raw UTF-8 bytes as bare hex. Two values for one token, each
   package green against itself.
   - W151 `SPEC.md` §7 pins the one derivation,
     `"sha256:" + lowercase hex of SHA-256 over the bearer's own UTF-8 bytes`,
     with the version header and §0 change table pointing at it;
     `token_verifier` in its model is what the offer record stores.
     Evidence 61 -> 64.
   - worker-control `SPEC.md` §4.2 NAMES that derivation rather than defining
     a second one, and §14 adds it to the approved set; the model repeats it
     verbatim. Evidence 23 -> 24.
   - conformance gains the cross-contract golden case comparing both
     derivations, over bearers neither package pins, and comparing the STORED
     offer verifier with the signature payload operand. 73 -> 74 model tests;
     the register is unchanged, because contract agreement is not a runtime
     obligation.
   - a golden bearer and its verifier are pinned as LITERALS on both sides, so
     a change to either derivation fails a comparison instead of moving its
     own expectation with it.
   - the M1 cross-contract freeze note gains its third amendment.
9. [done 2026-08-22] Correct the P2: `finding-v12-worker-manager-core/PLAN.md`
   gains item 1b naming BOTH integrity boundaries found in review — the §4.2
   operation-signature recomputation and this verifier derivation, with an
   explicit instruction not to derive a second value in the manager's durable
   stores — and item 5's design-test count moves to 144, with the earlier 122
   and 134 retained as the superseded history of how it moved.
10. [done 2026-08-22] Independent re-review signed off with no findings:
   `review-2026-08-22T15-34-43Z.md`. W4487 may close satisfying and unblock
   W2929.
