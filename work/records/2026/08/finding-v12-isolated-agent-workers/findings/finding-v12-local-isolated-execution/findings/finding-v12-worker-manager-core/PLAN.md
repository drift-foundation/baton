# Plan: durable v12 Worker Manager core

1. [done 2026-08-22] Revalidate the signed-off W2928 public boundary and pin
   manager/authority ownership: W2929 receives only a participant-bound
   `V12Session`, never the bootstrap, authority store path or raw store.
1a. [done 2026-08-22; W4487] The frozen decline-token contradiction is ruled
   and the affected contracts, schema, vectors and cross-contract freeze
   evidence are regenerated together. THE SHAPE TO IMPLEMENT: a decline
   carries `claim_token: null` and is authorized by the integrity-protected
   `offer.decide` binding `(offer_id, runtime_attempt_id, work_ref, decision,
   reason)`; the manager validates that whole binding against one issued
   offer with an unspent verifier, consumes the verifier and mints no claim.
   A stale, foreign, differently bound or operand-colliding decline refuses
   and terminates nothing; an exact replay returns the one committed decline.
   ACCEPTANCE IS UNCHANGED and still requires the exact unspent, unexpired
   bearer through the canonical claim transaction. W151 §7's token
   requirement for decline is explicitly superseded (W151 `SPEC.md` §1);
   worker-control §12 rule 14 carries the binding check no schema can
   express; conformance obligation `C-08` certifies it. Record:
   `work/records/2026/08/finding-worker-control-decline-token-conflict/`.
1b. [done 2026-08-22; W4487 review and re-review] TWO INTEGRITY BOUNDARIES
   the ruling above does not state, both found in independent review of it,
   and both load-bearing for the stores this item implements.
   (i) **The operation signature is recomputed, and its payload is exact.**
   worker-control §4.2 pins it as the canonical digest of
   `{"kind": <envelope kind>, "operands": <durable body operands>}` over §3.2
   bytes. A RECEIVER of a mutating command recomputes it and refuses
   `integrity.digest` on a mismatch BEFORE journalling the operation; a reply
   echoes its request's signature and is not recomputed. Without this a
   decline could change its durable reason, recompute only `body_digest`,
   retain the old signature, and be replayed as the first decline — which is
   what makes the tokenless decline effectively-once. §12 rule 9 carries the
   recomputation; conformance obligation `E-11` certifies it.
   (ii) **The claim-token verifier is ONE derivation**, owned by W151 §7:
   `"sha256:" + lowercase hex of SHA-256 over the bearer's own UTF-8 bytes`.
   The durable offer record stores exactly that, and worker-control's
   signature payload carries exactly that as `claim_token_verifier` (`null`
   for a decline). Do not derive a second value in the manager's stores: two
   derivations for one token is the defect this item inherited from the
   contracts and it was corrected there, not worked around here. A golden
   bearer is pinned in both models and the conformance package asserts they
   agree.
1c. [done 2026-08-22] Revalidate the implementation handoff after W4487
   closed satisfying. The old blocking decision in `FINDING.md` is explicitly
   superseded; the current public `V12Session` boundary still matches this
   plan; no 1.0 manager implementation exists; and all five gates pass. See
   `evidence/revalidation-2026-08-22T15-36-19Z.txt`.
2. [changes requested 2026-08-22; first slice] Implement exact worker-control 1.0
   schema/semantic validation and the separate shared durable
   offer/attempt/operation/session control store under the external state
   root.
   LANDED: `v12/src/worker_manager/contracts.mjs` (exact negotiation, §3.2
   canonical bytes and digests, the §4.2 operation signature with the pinned
   payload, W151's one token-verifier derivation, the §12 semantic rules, the
   closed error pairing, and a SEALED byte copy of the frozen schema);
   `schema.mjs` and `store.mjs` (the control store, its transaction/replay
   boundary with savepoint-scoped ordinary vs durable refusals, the manager's
   own operation journal, and the one-live-offer-per-Work partial unique
   index). 25 focused regressions.
   NOT LANDED: a chosen Draft 2020-12 validator, so unknown-field refusal is
   not yet covered. Named in `PROGRESS.md` rather than glossed.
   FIRST-SLICE REVIEW: before orchestration, close every item in
   `review-2026-08-22T16-37-37Z.md`: schema-prove envelopes before the reply
   signature exemption; return a complete exact negotiation; make
   canonicalization conform to the frozen restricted RFC 8785 value space;
   scope observation identity by incarnation; replay the complete durable
   refusal and use the manager clock; and refuse an incompatible control store
   without changing or leaking it. Retain the review reproductions as product
   regressions and return this slice for re-review.
2a. [done 2026-08-22; correction round] The six first-review boundaries above
   are corrected and independently reproduced as green. Evidence:
   `evidence/correction-first-slice-2026-08-22.txt`.
2b. [changes requested 2026-08-22; corrected-foundation re-review] Before
   orchestration, close all five boundaries in
   `review-2026-08-22T17-30-46Z.md`: replace the exported self-attested
   schema-proof boolean with an unforgeable/private validation path; return a
   copied validated envelope rather than a caller-owned alias; distinguish a
   missing journal row from a committed JSON `null`; reject invalid Unicode
   in member names as well as values; and validate the manager's own runtime
   profile digest before returning it as negotiated state. Retain all five
   additive regressions and return this foundation for another re-review.
2c. [done 2026-08-22; correction round two] The five corrected-foundation
   boundaries above are corrected and independently reproduced as green.
   Evidence: `evidence/correction-foundation-round2-2026-08-22.txt`.
2d. [changes requested 2026-08-22; foundation round-three re-review] Before
   orchestration, close all three boundaries in
   `review-2026-08-22T18-14-12Z.md`: implement the pure section-12 manifest
   trust entry promised by item 2, including the frozen query/overlap vectors;
   apply the durable-secret refusal at the operation-journal boundary rather
   than relying on each action to remember it; and distinguish a genuinely
   empty new store from an existing unowned database with no Baton metadata.
   Retain the two additive store regressions and return the foundation for
   another re-review.
2e. [done 2026-08-22; correction round three] All three closed. `validateManifest`
   is the copied, schema-first §12 trust entry — the one item 2 promised and
   never wrote, while the AJV setup justified disabling `format: "uri"` by
   naming a `validateUri` that did not exist. It implements the PURE document
   rules: work-id prefix, unique names, pairwise NON-OVERLAPPING destinations,
   credential/query/fragment-free locators read off the original text,
   omitted-member manifest digests, content-manifest sorting/uniqueness and
   aggregate and tree seals, git object-format consistency, the decidable half
   of artifact-reference validation, and the durable-secret walk — with
   artifact refs and content manifests found by a WALK rather than a field
   list. Rules 2 and 11 stay named and absent: both need orchestration state.
   The journal now refuses a committed result or sealed refusal carrying a
   secret, inside the transaction. The store initializes only a genuinely
   empty schema and refuses an existing unowned database without changing a
   byte. Five mutations, each independent; ONE OF MY OWN TESTS PASSED FOR THE
   WRONG REASON and M3 found it — the record's invalid vectors are patches and
   were not resealed, so both were refused for the digest rather than for the
   rule they name. 213 v12 (202 before), all four design models green, zero
   test-owned roots retained.
   Evidence: `evidence/correction-foundation-round3-2026-08-22.txt`.
2f. [changes requested 2026-08-22; foundation round-four re-review] Before
   orchestration, close all three boundaries in
   `review-2026-08-22T18-51-48Z.md`: refuse a URI when its parser rejects it
   rather than classifying every failure as opaque; compare normalized content
   paths by their UTF-8 bytes rather than JavaScript UTF-16 ordering; and make
   the journal's §13 guard detect the actual ephemeral bearer value in
   committed results, refusal messages and diagnostics, not only secret field
   names. Retain all four additive regressions and return the foundation for
   another re-review.
2f. [done 2026-08-22; correction round four] All three closed.
   `validateUri` treats a PARSE FAILURE as a refusal — it caught and ignored
   every one under the belief that a failure meant an opaque scheme, and with
   format assertions deliberately off nothing else was going to notice
   `https://[`; the opaque forms are measured to still parse and still answer
   to the original-text query/fragment rules. Content entries sort by UTF-8
   BYTES rather than JavaScript `<`, which is UTF-16 code units and disagrees
   with the frozen model about astral paths — a cross-language seal boundary.
   The durable-secret walk now examines VALUES as well as member names,
   refusing any string CONTAINING a known ephemeral bearer, with a
   remember/forget/withSecret lifecycle for the orchestration slice and the
   golden vector seeded because it is the one bearer this build holds as a
   constant; shape is explicitly not a substitute, and the verifier is
   explicitly not refused. Five mutations, each independent. 222 v12 (217
   before), zero test-owned roots retained, all four design models green.
   Evidence: `evidence/correction-foundation-round4-2026-08-22.txt`.
2g. [changes requested 2026-08-22; foundation round-five re-review] Before
   orchestration, close both secret boundaries in
   `review-2026-08-22T19-11-31Z.md`: serialize an operation outcome exactly
   once and validate the same representation the journal records, so
   `toJSON`/getter behavior cannot inject a bearer after the walk; and preserve
   overlapping known-secret ownership plus the full lifetime of a
   Promise-returning scoped act. Retain all three additive regressions and
   return the foundation for another re-review.
2g. [done 2026-08-22; correction round five] Both closed, and both were in
   the secret boundary landed in round four. The journal validates the
   SERIALIZED representation: `_durable` serializes once, walks the parse of
   those exact bytes — `JSON.parse` runs no user code — and records the same
   bytes without reserializing, so a `toJSON` cannot show one value to the
   guard and another to the row. The registry became two registers with
   different lifetimes: the golden conformance bearer is PINNED and never
   released, and live values are REFERENCE COUNTED so an inner scope cannot
   end an outer owner's lifetime; `withSecret` transfers ownership to the
   continuation when its act returns a thenable and releases on settle,
   keeping synchronous throw cleanup. Six mutations, each independent — M1
   (wrong order) and M6 (second serialization) are separate halves of one
   rule and each needed its own case. 229 v12 (225 before), zero test-owned
   roots retained, all four design models green.
   Evidence: `evidence/correction-foundation-round5-2026-08-22.txt`.
   OFFERED TO THE REVIEWER: the alternative of deleting the scoped API until
   its real orchestration caller can define the lifetime was considered and
   not taken; both of its failure modes are regressions now, but removing it
   is a small change if preferred.
2h. [changes requested 2026-08-22; foundation round-six re-review] Before
   orchestration, close both boundary splits in
   `review-2026-08-22T19-31-47Z.md`: return the canonical parsed durable result
   on the first successful transaction so it agrees with exact retry and is
   not a caller-owned alias, without a second serialization; and capture a
   thenable continuation once so classification and settlement cannot observe
   different values or release a bearer before the represented act completes.
   Retain both additive regressions. The scoped API may stay. Return the
   foundation for another re-review; items 3 and 4 remain unstarted.
2h. [done 2026-08-22; correction round six] Both closed, and both were the
   round-five corrections split one level down. `_durable` returns
   `{bytes, committed}` from the ONE serialization, and `transact` returns
   `committed` — so the first caller and every replay are told the same
   thing, and the answer is nobody's alias; previously a `toJSON` gave the
   first caller the source object and the retry the parsed journal, two
   answers under one operation identity. `withSecret` CAPTURES the `then`
   continuation once and assimilates that callable with its original
   receiver, instead of reading `then` to classify and letting
   `Promise.resolve` read it again; a throwing getter still lands in the
   synchronous cleanup. Five mutations plus one honest non-result recorded.
   236 v12 (231 before), zero test-owned roots retained, all four design
   models green.
   Evidence: `evidence/correction-foundation-round6-2026-08-22.txt`.
   CLOSED BY THIS REVIEW: the scoped secret API stays; reference counting and
   ordinary Promise behaviour are sound, and one-read thenable adoption
   closes its remaining advertised boundary.
2i. [changes requested 2026-08-22; foundation round-seven re-review] Close the
   lifecycle-result inconsistency in `review-2026-08-22T19-49-19Z.md`:
   releasing the final dynamic registration of a pinned bearer must return
   false because the value is still live in `_PINNED`, matching
   `forgetSecret`'s documented boolean and the guard's actual state. Preserve
   reference counting, inert unbalanced release and permanent pinning; retain
   the additive regression and return the foundation for re-review. Items 3
   and 4 remain unstarted.
2i. [done 2026-08-22; correction round seven] `forgetSecret` consults
   `_PINNED` before reporting a value gone. It deleted the last dynamic
   registration and returned `true` while the guard went on refusing the
   value — not a leak, but an exported lifecycle answer contradicting the
   state it describes, which orchestration would reason from. Nested counts,
   inert unbalanced releases and permanent pinned protection are unchanged.
   Two mutations; the added case asserts AGREEMENT with the guard in both
   directions, because a boolean has two ways to be wrong and the reported
   case pins only one. 238 v12 (237 before), zero test-owned roots retained,
   all four design models green, and every gate in the tree green.
   Evidence: `evidence/correction-foundation-round7-2026-08-22.txt`.
2j. [changes requested 2026-08-22; foundation round-eight re-review] Close
   the other side of the lifecycle-result agreement in
   `review-2026-08-22T20-00-37Z.md`: an ordinary value with no dynamic owner
   is already gone, so a state-inert unbalanced release must report `true`
   while the equivalent pinned case reports `false`. Make the early no-owner
   branch consult current pinned/liveness state, retain the additive
   regression, and return the foundation for re-review. Items 3 and 4 remain
   unstarted.
2j. [done 2026-08-22; correction round eight] `forgetSecret`'s INERT
   branch — no dynamic owner at all — consults `_PINNED` too, so releasing an
   ordinary value twice reports it gone instead of contradicting a guard that
   already permits it. Same contradiction as round seven's, in the branch
   round seven did not fix. Reference counts, permanent pinning and the inert
   state transition are unchanged. Three mutations, one per branch. RECORDED:
   my round-eight agreement case never released a value twice, so it never
   asked this branch; and an earlier case of mine ASSERTED the wrong answer
   outright and had to be corrected. 239 v12, zero test-owned roots retained,
   all four design models green.
   Evidence: `evidence/correction-foundation-round8-2026-08-22.txt`.
2k. [signed off 2026-08-22; foundation round-nine re-review] No remaining
   finding in completed item 2. The no-owner branch now answers from current
   pinned/liveness state without changing state; ordinary/pinned and
   nested/last/no-owner release paths agree with the guard. Focused
   contract/store review is 78/78 and `git diff --check` reports no error.
   Evidence: `review-2026-08-22T21-05-52Z.md` and
   `evidence/review-foundation-round9-2026-08-22.txt`. Continue with items 3
   and 4; this bounded sign-off does not close W2929.
2k. [signed off 2026-08-22] Independent review accepted the round-eight
   correction and closed foundation item 2. Review:
   `review-2026-08-22T21-05-52Z.md`. Items 3 and 4 explicitly not reviewed.
3a. [done 2026-08-22; item 3 FIRST HALF] `offers.mjs` — the offer and the
   claim. Reads before entropy; the per-Work CAS decided by the database;
   the verifier stored and the bearer returned only after the commit;
   acceptance consuming the verifier, freezing the intent, deriving the fixed
   claim operation id and storing a SEPARATE settlement deadline; the one
   fixed claim submitted through the participant-bound session with its
   result recorded first; a lost result OBSERVED ONLY before the deadline and
   retired at or after it, with positive refusal evidence permitting
   immediate retirement and every path ADOPTING a bound retirement; a commit
   never seen recorded late; and the restart asymmetry — a prior
   incarnation's issued offer abandoned but visible, an accepted offer
   recoverable, this incarnation's own untouched. Six mutations. RECORDED:
   `validateOfferDecide` compared the verifier with `!==` and now uses
   `timingSafeEqual`; M6's first case was a tautology; and my first fixture
   set leaked twenty temporary roots. 256 v12 (239 before), zero test-owned
   roots retained, all four design models green.
   Evidence: `evidence/offer-claim-slice-2026-08-22.txt`.
3b. [changes requested 2026-08-22; item-3a independent review] Correct the
   seven executable boundaries in `review-2026-08-22T21-36-26Z.md`: bind the
   offer participant to the injected session before entropy; make exact local
   profile certification unavoidable; make offer-issue replay cover every
   durable operand and never pair a new bearer with an old verifier; expire by
   issued-only CAS while consuming the verifier and freeing the Work; persist
   and use the fixed authority claim signature; record the real authority's
   direct four-part assignment exactly; and make decline/restart abandonment
   unable to overwrite a concurrent acceptance. Retain all seven additive
   review cases, add deterministic decline/abandon-versus-accept races, and
   exercise claim/settlement through a real `V12Session` before returning.
   Evidence: `evidence/review-offer-claim-slice-2026-08-22.txt`.
3b. [done 2026-08-22] Item 3a corrected against
   `review-2026-08-22T21-36-26Z.md`, six P1. Acceptance freezes the
   authority's own `claimSignature` and every settlement uses it; both
   recording paths take the assignment `V12Session.claim` returns DIRECTLY;
   the participant is the session's binding and a disagreeing operand is
   refused before entropy; expiry CASes to `expired`, consumes the verifier
   and releases the per-Work slot; every issued-only transition CASes from
   `issued` alone so a stale decline or abandonment cannot overwrite an
   acceptance; certification is unavoidable, preferring the control store's
   own `profiles` row and refusing absence; and the issue signature covers
   every durable operand while an exact re-issue REFUSES rather than
   returning a bearer that does not derive the stored verifier. Eight
   mutations, seven bite; the issued-only CAS is recorded as UNWITNESSED
   because no reachable path reaches it today. Six cases added, including the
   whole claim path and both settlement windows against a REAL `V12Session`.
   269 v12, zero test-owned roots retained, all four design models green, and
   every gate in the tree green.
   Evidence: `evidence/correction-offer-claim-2026-08-22.txt`.
3c. [changes requested 2026-08-22; item-3a correction re-review] Close the
   three executable boundaries in `review-2026-08-22T22-01-32Z.md`: make a
   concurrent exact issue loser refuse without returning its newly minted
   bearer beside the winner's durable verifier; settle elapsed issued offers
   without depending on a late worker decision so TTL releases the Work and
   consumes the verifier; and include the durable authority UUID binding in
   the issue operation signature. Retain the five additive re-review cases;
   the two deterministic stale-read interleavings now witness and pass the
   issued-only CAS protection. Evidence:
   `evidence/re-review-offer-claim-2026-08-22.txt`.
3c. [done 2026-08-22] Item 3a's three remaining P1s closed. The DECIDING
   replay is the one inside `transact`, so a losing concurrent issuer refuses
   instead of returning the winner's record beside its own bearer — the
   pre-check answers the sequential case and is not the decision. TTL is
   manager-owned: `expireOverdue` runs at reissue and at restart recovery and
   needs no message from anybody, settling an elapsed offer visibly as
   `expired` with its verifier consumed. The issue signature carries the full
   authority-scoped binding, so the same identity against another authority
   collides rather than replaying. Six mutations, five bite; the sixth is
   INERT because the issued-only CAS neutralises it, recorded rather than
   papered over. 279 v12, zero test-owned roots, all four design models
   green, and every gate in the tree green.
   Evidence: `evidence/correction-offer-claim-round2-2026-08-22.txt`.
3d. [changes requested 2026-08-22; item-3a second-correction re-review] Make
   the concurrent exact-issue loser refuse from transaction/journal replay
   provenance, not by inferring replay from verifier inequality. Two exact
   issuers receiving the same injected bearer still have a winner and loser;
   the loser must not return successfully merely because their verifier
   values agree. Retain the additive regression in
   `review-2026-08-22T22-14-59Z.md`. Focused result: 118 passed, 1 failed.
   Evidence: `evidence/review-offer-claim-round3-2026-08-22.txt`.
3d. [done 2026-08-22] Item 3a's last P1: provenance was inferred from the
   PAYLOAD — inequality of verifiers proves a loss, equality proves nothing,
   and two exact issuers can receive the same injected bearer. `transact`
   runs the action only when it did not replay, so the action setting a flag
   IS the transaction boundary reporting which happened; nothing about the
   payload decides provenance. The verifier comparison stays with a different
   job — a store-defect invariant, not a decision. Three mutations; the
   "always replayed" one fails 38 cases, which is what load-bearing means.
   282 v12, zero test-owned roots, all four design models green, every gate
   in the tree green.
   Evidence: `evidence/correction-offer-claim-round3-2026-08-22.txt`.
3e. [signed off 2026-08-22; item-3a third-correction re-review] The
   transaction action marker, not verifier equality, now decides commit versus
   replay. The deterministic same-bearer loser refuses; genuine first commits
   proceed; the verifier comparison is only a post-commit integrity invariant.
   The sequential-reissue case is stopped by the optimistic precheck and is
   not independent marker-branch evidence, but the concurrent and positive
   cases cover both outcomes. Review:
   `review-2026-08-22T22-21-52Z.md`; evidence:
   `evidence/review-offer-claim-round4-2026-08-22.txt`. Continue the remaining
   item 3 and item 4 work; this bounded sign-off does not close W2929.
3e. [signed off 2026-08-22] Independent re-review signed off item 3a: the
   closure marker obtains replay provenance from the transaction boundary,
   the losing issuer refuses even on an identical injected bearer, and the
   verifier comparison is correctly classified as an integrity invariant.
   Review: `review-2026-08-22T22-21-52Z.md`. Its non-blocking note is
   addressed: the sequential-reissue case is retitled and no longer cited as
   branch evidence for the marker.
3f. [done 2026-08-22; item 3 SECOND SLICE] `attempts.mjs` — activation and
   runtime start. `assignment.activate` validates the live assignment field
   by field and fixes the manifest ONCE, before any writable adapter call;
   `start-requested` is durable BEFORE the adapter is touched; reconciliation
   identifies by opaque id PLUS the full assignment/profile labels, with zero
   waiting unless absence is positively proven, one reattaching, and mismatch
   or multiplicity cancelling; observations advance only through the frozen
   axes and `uncertain` never becomes `destroyed`. Seven mutations, each
   bites. One case of mine had to be corrected: walking the whole
   `execution_runtime` enum passes through the one transition the rule
   forbids, which is exactly where the two rules meet. 295 v12 (282 before),
   zero test-owned roots, all four design models green, every gate in the
   tree green.
   Evidence: `evidence/attempt-slice-2026-08-22.txt`.
   NOT IMPLEMENTED: cancellation ordering, output freeze, intake and cleanup
   — the rest of item 3 — and all of item 4.
3g. [changes requested 2026-08-22; item-3 second-slice review] Close the seven
   boundaries in `review-2026-08-22T22-34-55Z.md`: bind activation to this
   attempt's committed claim and the session's full four-part assignment;
   sign every durable attempt operand; journal and pass one fixed runtime-start
   operation before calling the adapter; derive positive absence from
   validated evidence rather than a caller boolean; CAS one immutable runtime
   id and cancel exact identity/label mismatches; replace enum ordering and
   public `allowReset` with per-axis transitions and a private narrow retry;
   and decide observations atomically with their durable source identity.
   Retain all 12 additive regressions. Evidence:
   `evidence/review-attempt-slice-2026-08-22.txt`.
3. [in progress] Implement restart-safe offer acceptance, fixed claim
   settlement, assignment activation, monotonic observations, cancellation,
   freeze, intake and cleanup against the injected authority session.
3g. [done 2026-08-22] The activation/runtime-start slice corrected against
   `review-2026-08-22T22-34-55Z.md`, seven P1. Activation binds three things
   that must ALL agree — the session's binding, THIS attempt's committed
   claim, and the live assignment — and persists, compares and labels all
   four assignment fields (schema 1 -> 2: `claim_generation` on offers,
   `assignment_participant` on attempts). `attempt.record` signs every
   durable operand. Runtime start commits one fixed signed `runtime.start`
   operation and hands its identity to the adapter. The caller-authored
   `absenceProven` boolean is gone and the retry path is CLOSED until item 4
   defines certified evidence. Attachment compare-and-swaps null-or-identical
   and a minted runtime with wrong labels cancels before the filter. An
   explicit per-axis transition map replaces enum order, terminal
   alternatives are immutable, and the public `allowReset` bypass is gone.
   Observations are decided inside the write against the expected value, in a
   savepoint, journalled by incarnation and source sequence, with a concurrent
   writer refused as a typed contract error rather than a raw SQLite one.
   Nine mutations: five bite directly, two are backed by the deciding SQL
   guard and now have a case driving it, one was witnessable and is witnessed,
   and one is unwitnessable by construction and recorded. 309 v12, zero
   test-owned roots, all four design models green, every gate in the tree
   green.
   Evidence: `evidence/correction-attempt-slice-2026-08-22.txt`.
3h. [done 2026-08-22] Second correction of the activation/runtime-start
   slice, against `review-2026-08-22T22-53-46Z.md` — four P1 and one P2. A
   unique index makes one offer per runtime attempt a DATABASE fact (schema
   2 -> 3) and the reader fails closed for a store written before it; I had
   called that branch unwitnessable by construction, and the construction was
   a property of the allocator rather than of the store. The durable
   observation identity is resolved before the current-value shortcut and the
   transition check, so an exact duplicate replays whatever the axis now says
   and a conflicting one refuses even at an inert value. The cancellation
   intent is reachable from every nonterminal runtime state, so an ambiguous
   inspection cannot disable the response to stronger later evidence. The
   attach identity carries the runtime, and a lost race re-reads and
   PRESERVES the fixed identity before cancelling for the different one. Only
   a locked database is translated as contention; every other storage failure
   keeps its own identity. Six mutations, five witnessed; one is equivalent
   rather than uncovered and is recorded. 317 v12, zero test-owned roots, all
   four design models green, every gate in the tree green.
   Evidence: `evidence/correction-attempt-slice-round2-2026-08-22.txt`.
3i. [done 2026-08-22] Third correction of the activation/runtime-start
   slice, against `review-2026-08-22T23-07-46Z.md` — two P1 and one P2. An
   accepted sourced observation consumes its `(attempt, incarnation,
   source_seq)` identity whether or not it moved an axis, so the identity's
   meaning no longer depends on where the axis already was; a manager-internal
   repeat stays inert because it mints a fresh sequence and consumes nothing
   anyone could reuse. Cancellation is idempotent for a stop already in
   flight — the DECISION is returned and `stopping` is left alone, rather than
   rewinding the axis to re-announce an intent the runtime is already carrying
   out; `destroyed` is excluded on purpose and says so. Contention is decided
   by SQLite's own result code (`errcode & 0xff` in {5, 6}) rather than by a
   substring of application-controlled prose. Six mutations, all six
   witnessed. 323 v12, zero test-owned roots, all four design models green,
   every gate in the tree green including the serial v11 cases.
   Evidence: `evidence/correction-attempt-slice-round3-2026-08-22.txt`.
3j. [signed off 2026-08-22; activation/runtime-start slice] Independent
   re-review accepted the round-3 corrections: the sourced no-change
   observation writes exactly one durable identity, cancellation discovered
   while a stop is in flight returns the decision without rewinding the axis,
   and contention is classified by SQLite's structured primary result code.
   Bounded: cancellation ordering, output freeze/intake/cleanup and all of
   item 4 remained unimplemented and unreviewed.
   Evidence: `evidence/re-review-attempt-slice-round4-2026-08-22.txt`.
3k. [done 2026-08-22; item 3 THIRD SLICE] Cancellation ordering.
   `requestCancellation` journals the manager's intent, then calls
   `session.cancel` so the authority atomically fences the generation, ends
   the assignment and installs the typed quiescence gate — and only after
   that returns does it announce `cancel-requested` and order the runtime
   stopped. Both operation identities are derived from the attempt and its
   fixed assignment so a restart names the act it already performed, and they
   are deliberately different strings because §4.2 makes the two journals two
   facts. There is no liveness pre-check: liveness is the authority's
   decision. THE AXIS is not rewound for a runtime already `stopping`, while
   THE ORDER IS re-issued under the same operation identity — an order that
   may have been lost must be repeatable, and the identity keeps the repeat
   one act rather than two. Nothing is ordered at all for a runtime observed
   `destroyed`.
   [Corrected 2026-08-22, `review-2026-08-22T23-40-54Z.md` P2: this said the
   order was not repeated, which contradicted both the implementation and its
   own regression. The drafting was mine; the rule below is the one that was
   built and tested.] The quiescence gate this installs is NOT
   satisfied here: it takes positive absence naming the exact runtime, which
   is the same certified-adapter evidence the retry path is closed for until
   item 4. Nine mutations, all nine witnessed; twelve regressions including
   the whole cancellation against a real `V12Authority`. 335 v12, zero
   test-owned roots, all four design models green, every gate in the tree
   green.
   Evidence: `evidence/cancellation-slice-2026-08-22.txt`.
3l. [changes requested 2026-08-22; cancellation-slice independent review]
   Close three: the slice omitted the AGENT cancellation the acceptance
   requires between the fence and the runtime stop; `orderStop` manufactured
   `stopped: true` from reaching the call boundary; and plan item 3k's retry
   sentence contradicted both the implementation and its own regression. The
   authority-first fence, the separate stable identities and the absent
   liveness race were accepted.
   Evidence: `evidence/review-cancellation-slice-2026-08-22.txt`.
3l. [done 2026-08-22] All three closed. The AGENT is an injected boundary
   like the runtime adapter and is ordered BETWEEN the fence and the runtime
   stop — `authority.cancel -> agent.cancel -> adapter.stop` — because an
   agent told to stop after its runtime is going away never hears the order;
   item 4 owns what a conforming agent must BE, but where its cancellation
   sits in the order is item 3's and is the subject of this slice. The
   parameter order is the act order and both boundary shapes are checked, so
   a swap refuses instead of cancelling the wrong one first. The word
   `stopped` is gone: reaching a boundary is not evidence of its effect, so
   the manager reports `ordered` — what it knows — and passes each settlement
   through uninterpreted, with positive quiescence arriving as an observation
   or not at all. Item 3k's retry sentence was my drafting error and is
   corrected in place with a dated note: the AXIS is not rewound, the ORDER is
   re-issued under the same operation identity. Five mutations, all five
   witnessed. 339 v12, zero test-owned roots, all four design models green,
   every gate in the tree green.
   Evidence: `evidence/correction-cancellation-slice-2026-08-22.txt`.
3m. [changes requested 2026-08-22; cancellation-correction re-review] Close
   one: a throwing agent boundary left `orderQuiescence` before the runtime
   stop was ordered, with the authority already fenced — so an unreachable
   provider left a fenced runtime running. The three prior corrections were
   accepted on their exercised paths.
   Evidence: `evidence/re-review-cancellation-slice-2026-08-22.txt`.
3m. [done 2026-08-22] Closed. A failed cooperative request does not veto the
   forceful one: the agent failure is CAPTURED, the runtime stop is ordered
   anyway, and only then is the failure re-thrown unchanged — the order stays
   agent-before-runtime and the classification stays the caller's. When both
   boundaries fail an `AggregateError` carries both in call order, because
   letting one propagate alone would be this boundary choosing which failure
   the caller may see. Four mutations, three witnessed; the fourth is
   equivalent — the failure path throws before the return, so a settlement
   assigned there is dead code — and one of my case titles was overclaiming
   as a result and is corrected. A failed agent cancellation is visible to
   the caller and is NOT durable: there is no agent-session evidence table
   yet (store surface item 7, owned by item 4), and that gap is recorded
   rather than glossed. 342 v12, zero test-owned roots, all four design
   models green, every gate in the tree green.
   Evidence: `evidence/correction-cancellation-round2-2026-08-22.txt`.
3n. [changes requested 2026-08-23; cancellation third review] Close one:
   `agentFailure = null` was both a legal thrown value and the no-failure
   sentinel, so an agent that threw `null` had its failure silently dropped
   and could not reach the aggregate. The prior corrections were accepted,
   and the absence of durable agent-failure evidence was accepted as an
   explicit item-4 boundary.
   Evidence: `evidence/re-review-cancellation-round3-2026-08-23.txt`.
3n. [done 2026-08-23] Closed. Presence is carried by its own boolean and the
   variable carries only the thrown value, so `null`, `undefined` and any
   other thrown value are re-thrown unchanged and reach the aggregate beside
   a simultaneous runtime failure. THIS CODEBASE ALREADY KNEW THIS:
   `ControlStore.replay` carries an earlier review note saying the same thing
   in the same words, and the lesson had been recorded without being
   generalized. A sweep of my own found the same shape once smaller —
   `?? null` collapsed "returned nothing" into "returned null", contradicting
   the comment directly above it — and both settlements are verbatim now.
   Four mutations, all four witnessed; Q2 exists because swapping which falsy
   value means absence moves the defect rather than removing it. 346 v12,
   zero test-owned roots, all four design models green, every gate in the
   tree green.
   Evidence: `evidence/correction-cancellation-round3-2026-08-23.txt`.
3o. [signed off 2026-08-23; cancellation-ordering slice] Independent fourth
   review signed off the whole cancellation-ordering slice through item 3n,
   with no findings: journal intent, fence, agent cancellation, runtime stop
   even when the agent throws; settlements verbatim; failure presence
   independent of its value. Bounded — output freeze, intake, cleanup and
   item 4 remain unimplemented.
   Evidence: `evidence/signoff-cancellation-ordering-2026-08-23.txt`.
3p. [done 2026-08-23; item 3 FOURTH SLICE] The output freeze. Schema 3 -> 4
   adds `outputs` and `output_artifacts`, and `SCHEMA_VERSION` now carries a
   per-version history because an incompatible binary refuses on that number.
   `requestFreeze` requires a fixed assignment, the bound session, a POSITIVE
   `quiescent` writer observation (`destroyed` is not one — gone is not
   finished), and a `worker_disposition` already recorded terminal and equal
   to the one declared; the liveness read runs inside the freeze transaction
   and is named in the code as only a read, because the authority is a
   different store. `recordFrozenResult` runs the shared `validateManifest`
   over a real `baton.worker-manifest/result` and then adds the four
   comparisons that entry cannot make — assignment, input and policy digests,
   disposition and settled freeze operation. The record identity is fixed per
   ATTEMPT rather than per digest, which is the whole mechanism behind "the
   same digest replays; changed bytes under the same identity refuse".
   Twelve mutations, eleven witnessed; R11 is equivalent because
   `validateManifest` already proved the declared digest recomputes, and the
   recomputation is kept for provenance rather than counted as a guard. 370
   v12, zero test-owned roots, all four design models green, every gate in
   the tree green.
   Evidence: `evidence/freeze-slice-2026-08-23.txt`.
3q. [changes requested 2026-08-23; freeze-slice independent review] Close
   four: the sealed result's freeze SIGNATURE was ignored (only the id was
   passed and compared); exact replay was hidden by a later output axis;
   "declared outputs only" was not enforceable because the store held a digest
   and not the input manifest; and schema 4 retained a summary rather than the
   immutable result manifest. The quiescence and disposition gates, the
   cross-store liveness description and the fixed per-attempt identities were
   accepted.
   Evidence: `evidence/review-freeze-slice-2026-08-23.txt`.
3q. [done 2026-08-23] All four closed. `freezeOperation` derives the WHOLE
   identity — id and signature — the id crosses to `adapter.seal` with it, and
   both halves are compared when the result returns. The fixed record identity
   is resolved BEFORE today's output axis, so an exact retry replays even from
   `sealed`. Schema 4 -> 5 adds `manifests(digest PRIMARY KEY, schema, body,
   retained_at)` holding RFC 8785 canonical bytes, with
   `outputs.manifest_digest` referencing it; `retainManifest` validates before
   storing and refuses a digest that would name two documents, and
   `loadManifest` parses fresh so a durable record is never handed out as an
   alias. Freeze resolves the attempt's input declaration from that table and
   compares the sealed outputs BOTH WAYS — every result output declared, every
   declaration answered, types equal, and a required output missing only under
   an inability disposition. Fourteen mutations, all fourteen witnessed. 385
   v12, zero test-owned roots, all four design models green, every gate in the
   tree green.
   Evidence: `evidence/correction-freeze-slice-2026-08-23.txt`.
3r. [changes requested 2026-08-23; freeze-correction re-review] Close four:
   `loadManifest` returned any retained row without validating its KIND, so a
   retained result manifest could be named as an attempt's input declaration;
   declared output constraints were never read; result retention bypassed the
   collision refusal with `INSERT OR IGNORE`; and exact replay still depended
   on the input row still being retained. The operation-identity corrections
   and the retained result document were accepted.
   Evidence: `evidence/re-review-freeze-slice-2026-08-23.txt`.
3r. [done 2026-08-23] All four closed. `loadManifest` REQUIRES the definition
   it must be — a caller that has not said what it expects has not checked
   anything — validates the body as that definition, and recomputes its digest
   against the key it was filed under. `retainCanonical` is the one place the
   digest/body collision is refused and both writers go through it. The
   declared constraints are enforced for everything the sealed observation
   proves: `max_bytes` against the content total or the artifact's declared
   size, `max_entries` against the entry count, and the media type against the
   allow-list literally, including an empty one. The immutable identity and
   its signature are computed FIRST and replay resolved there, so every check
   about today — bindings, declaration, axis — applies only to a genuinely new
   record. Nine mutations, all nine witnessed; T9 was inert until the branch
   it guarded became a decision, refusing an output that reports itself
   missing while carrying material. 396 v12, zero test-owned roots, all four
   design models green, every gate in the tree green.
   Evidence: `evidence/correction-freeze-round2-2026-08-23.txt`.
3s. [changes requested 2026-08-23; freeze third review] Close one: the
   correction refused a `missing-optional` output that carried material and
   left its converse open, so a `present` output with neither a tree nor an
   artifact froze as a satisfied REQUIRED output under a completed
   disposition. All four item-3r findings were accepted.
   Evidence: `evidence/re-review-freeze-round2-2026-08-23.txt`.
3s. [done 2026-08-23] Closed, to the contract rather than to the minimum that
   passes the case: §8.4 binds "every declared output's content/tree digest
   AND artifact reference", so a `present` output must carry both. The
   nullable members exist so a MISSING output can say so, not so a present one
   can choose which half to supply. That made the size computation's fallback
   unreachable, so both representations are bounded by the declaration now
   rather than whichever one happened to be there. Three mutations, all three
   witnessed; U2 satisfies the reviewer's case while accepting an output that
   supplies only one half, which is why a case of mine drives each half
   separately. 399 v12, zero test-owned roots, all four design models green,
   every gate in the tree green.
   Evidence: `evidence/correction-freeze-round3-2026-08-23.txt`.
3t. [signed off 2026-08-23; output-freeze slice] Independent sign-off through
   item 3s, with no open finding in the bounded slice: positive quiescence and
   exact live-assignment/disposition checks, the complete freeze operation
   identity across the adapter boundary, fixed result identity with collision
   refusal and replay before current state, typed digest-key-verified retained
   manifests, lossless canonical result durability across restart without
   caller aliases, bidirectional declaration/result checks, declared limits,
   and symmetric status/material consistency.
   Evidence: `evidence/signoff-output-freeze-2026-08-23.txt`.
3u. [done 2026-08-23; item 3 FIFTH SLICE — item 3 complete] Trusted intake and
   cleanup. Schema 5 -> 6 adds `intake`, holding the decision, its retention,
   the locator, the deadline and the assignment it was decided under —
   RETENTION IS NOT ACCEPTANCE, so a rejected draft retained under policy is
   sayable. `recordIntake` is NOT GIVEN A SESSION: "never publishes" is kept
   by handing the boundary no way to reach the authority, because a handle
   passed and not used is a rule enforced by good intentions. The cleanup
   operation identity is derived from the INTAKE STATE it was evaluated
   against, which is what makes the `blocked-on-intake` refusal durable to its
   own operation while a later re-evaluation is a new one; a counter would
   have satisfied the words and been caller-authored. `requestDestroy` waits
   for the assignment to be over, passes the adapter's settlement through
   uninterpreted, and moves the cleanup axis only on a positive `destroyed`
   observation. The pinned-discard-policy path is CLOSED, like the retry path,
   because a policy taken as an argument is a proof the caller writes. Ten
   mutations, all ten witnessed; V6's first attempt was not faithful and is
   recorded. 415 v12, zero test-owned roots, all four design models green,
   every gate in the tree green.
   Evidence: `evidence/intake-cleanup-slice-2026-08-23.txt`.
3v. [changes requested 2026-08-23; intake/cleanup review] Preserve the
   accepted separation of retention from acceptance, no-publication API
   boundary, fixed intake identity, durable blocked-on-intake re-evaluation,
   ended-assignment liveness check and positive-absence requirement. Close
   four boundaries in `review-2026-08-23T01-29-05Z.md`: require and durably
   bind intake to the exact sealed result manifest; scan every intake column,
   including nullable prose, for live secrets before writing; refuse cleanup
   completion until intake or a future durable pinned discard policy opens
   the gate; and validate a non-null retention deadline as a timestamp. Retain
   all four additive cases. Focused gate 16/20; full v12 gate 415/419.
   Evidence: `evidence/review-intake-cleanup-2026-08-23.txt`.
3v. [changes requested 2026-08-23; intake/cleanup independent review] Close
   four: intake could decide with no sealed material and recorded no material
   identity; `reason` bypassed the durable-secret boundary because the shared
   guard scans the operation RESULT and the result omitted it; positive
   runtime absence completed cleanup without the intake gate; and the
   retention deadline accepted arbitrary text.
   Evidence: `evidence/review-intake-cleanup-2026-08-23.txt`.
3v. [done 2026-08-23] All four closed. Intake requires a sealed output for the
   attempt and binds the decision to that output's result-manifest digest with
   a foreign key to the retained bytes (schema 6 -> 7) — a locator is where
   something is, not which immutable result was judged — and the fixture
   drives the REAL freeze path, because its first version decided the fate of
   material that did not exist. The exact durable record is assembled and
   scanned for secrets before any of it is written: a summary that omits a
   column is not a guard over that column. `settleCleanup` checks the POLICY
   gate before the absence one, because an observation proves the runtime is
   gone and says nothing about whether the material was retained or
   quarantined. The deadline is validated against the contract's canonical
   timestamp form. Five mutations, all five witnessed; W2 is blunt — the
   foreign key is the deciding guard — and the narrower claim is pinned
   separately. 423 v12, zero test-owned roots, all four design models green,
   every gate in the tree green.
   Evidence: `evidence/correction-intake-cleanup-2026-08-23.txt`.
3w. [changes requested 2026-08-23; intake/cleanup correction re-review]
   Preserve all four accepted item 3v corrections, then close the two P1
   durability boundaries in `review-2026-08-23T01-43-26Z.md`: resolve an
   existing intake operation's exact replay or collision from its committed
   binding before current output state, while keeping the sealed-output gate
   for a genuinely new decision; and authenticate every loaded intake row,
   including its exact result digest and decision operands, against the
   committed operation rather than treating a foreign key to any retained
   manifest as the full binding. Retain both additive cases. Focused gate
   24/26; full v12 gate 423/425.
   Evidence: `evidence/re-review-intake-cleanup-2026-08-23.txt`.
3w. [changes requested 2026-08-23; intake-correction re-review] Close two:
   exact intake replay and collision were hidden behind the current output
   index, and `intakeOf` returned every column but the assignment fields as
   trusted, so a row pointed at a second individually valid retained result
   passed the foreign key and was accepted by cleanup. The four item-3v
   corrections were accepted.
   Evidence: `evidence/re-review-intake-cleanup-2026-08-23.txt`.
3w. [done 2026-08-23] Both closed. An existing decision already NAMES its
   material, so the output index is consulted only when there is no decision
   to replay — which is exactly when nothing can be hidden by requiring it;
   the sealed-output precondition is untouched for a genuinely new decision.
   And the journal authenticates the row: its own columns are reassembled into
   the exact durable record, the signature recomputed and compared against the
   committed operation, with writer and reader building that record in ONE
   place. A mismatch is `integrity.digest` rather than
   `refused.operation-collision`, because a row disagreeing with its own
   committed decision is not a caller reusing an identity. Five mutations,
   four witnessed; X4 is MASKED rather than uncovered — two independent guards
   cover the non-result case and only removing both makes it fail, which is
   measured and written beside the case. 428 v12, zero test-owned roots, all
   four design models green, every gate in the tree green.
   Evidence: `evidence/correction-intake-round2-2026-08-23.txt`.
3x. [signed off 2026-08-23; intake/cleanup third review] Independent sign-off
   through item 3w. Existing intake identities replay or collide before
   current output state; genuinely new decisions retain the sealed-material
   gate; stored rows are authenticated against their committed signature and
   typed result manifest; missing journal evidence and every decision-operand
   mismatch fail closed. Focused gate 30/30; full v12 gate 429/429. Bounded:
   item 4, a future pinned discard policy, the no-frozen-result quarantine
   manifest and W2930 artifact-byte verification remain open. The sign-off
   also clarifies that writer and reader use separate record construction
   sites whose signature equality is enforced, superseding the earlier
   literal “one place” wording. Review:
   `review-2026-08-23T01-55-36Z.md`; evidence:
   `evidence/signoff-intake-cleanup-2026-08-23.txt`.
3x. [signed off 2026-08-23; intake/cleanup — ITEM 3 COMPLETE] Independent
   sign-off through item 3w with no behavioural finding, plus one durable
   wording clarification: "writer and reader build the record in one place"
   was true of the signature FORMULA and not of the code.
   Evidence: `evidence/signoff-intake-cleanup-2026-08-23.txt`.
4a. [done 2026-08-23] The sign-off's clarification, closed IN CODE rather than
   by weakening the claim: `recordIntake` builds its operands through
   `intakeRecord`, the same builder the reader uses, so adding a column
   changes both sides or neither.
4b. [done 2026-08-23; item 4 FIRST SLICE] Certifying one agent-session
   profile, by composing SHAPE, then the document SEAL, then POLICY. The
   frozen `agent-session-1.0.schema.json` is placed under
   `src/worker_manager/schema/` for the same reason the worker-control schema
   is. The policy layer states only what the schema cannot: the two postures
   carry different pinned policies. MEASURED — the codex branch of the schema
   already pins consent and execution to two different policy definitions, so
   the SHAPE check answers there and the policy rule decides only for ACP,
   whose branch shares one definition with a free-form `session_mode_id`; the
   case asserts what actually decides per family. The fixtures are the ACP
   boundary model's own profiles, digests included, and both seals recompute
   exactly under this manager's canonicalization — measured before the suite
   was written. Certification is BY DIGEST, so a re-edited profile under the
   same `profile_id` is a new profile. Six mutations, all six witnessed. 437
   v12, zero test-owned roots, all four design models green, every gate in the
   tree green.
   Evidence: `evidence/agent-profile-slice-2026-08-23.txt`.
4c. [changes requested 2026-08-23; item 4 first-slice review] Close both P1
   boundaries in `review-2026-08-23T02-12-31Z.md`: make the composing
   shape/seal/policy entry the only path able to create an `agent-session`
   certification, and scope every profile consumer to its exact kind so an
   agent-session digest cannot certify the separate runtime-profile offer
   axis. Retain all four additive regressions, including the passing inverse
   kind check and frozen schema byte-identity guard. Focused gate is 10/12 and
   full v12 is 439/441
   until corrected. Evidence:
   `evidence/review-agent-profile-slice-2026-08-23.txt`.
4c. [changes requested 2026-08-23; agent-profile independent review] Close
   two: the generic `certifyProfile` accepted `kind: "agent-session"` and
   wrote a caller-authored digest into the same table, so the new composing
   entry point was avoidable; and `certifiedProfile` was unscoped, so an
   agent-session profile satisfied an offer's RUNTIME certification. A schema
   byte-identity regression was added and passes.
   Evidence: `evidence/review-agent-profile-slice-2026-08-23.txt`.
4c. [done 2026-08-23] Both closed. The generic writer is
   `certifyRuntimeProfile` and takes NO kind — supplying one is refused rather
   than dropped, because silently dropping `agent-session` would have turned
   an attempted forgery into a successful RUNTIME one on the axis the caller
   never named. Both consumers name their kind and fail closed on a cross-kind
   row: agent-session and runtime are separate contract axes, and a digest
   certified under one is not certification under the other even when the
   bytes are genuine. Four mutations, all four witnessed; Z3 closes the
   cross-axis hole in the other direction and breaks the axis itself, which is
   why a case drives a runtime profile certifying a runtime offer. 443 v12,
   zero test-owned roots, all four design models green, every gate in the tree
   green.
   Evidence: `evidence/correction-agent-profile-2026-08-23.txt`.
4d. [signed off 2026-08-23; agent-profile correction re-review] Both P1
   findings are closed. Only the composing agent-session entry can create an
   `agent-session` certification; the runtime writer has a fixed kind and
   refuses a supplied one without writing; and offer issue requires a
   runtime-kind row. Both positive axes, both cross-axis negatives,
   withdrawal and frozen schema byte identity pass. Focused 14/14; full v12
   443/443. Bounded: sessions, turns, normalized events and adapter contracts
   remain. Review: `review-2026-08-23T02-22-39Z.md`; evidence:
   `evidence/signoff-agent-profile-2026-08-23.txt`.
4d. [signed off 2026-08-23; profile-certification first slice] Independent
   re-review signed off both P1 corrections with no remaining finding, and
   explicitly accepted refusing a supplied `kind` rather than ignoring it:
   ignoring it would turn an attempted cross-axis certification into a
   different successful one.
   Evidence: `evidence/signoff-agent-profile-2026-08-23.txt`.
4e. [done 2026-08-23; item 4 SECOND SLICE] Opening an agent session. Schema
   7 -> 8 adds `profiles.body` and `agent_sessions` keyed on
   `(runtime_attempt_id, posture, session_epoch)`. The certified profile BYTES
   are retained — a session pins a per-posture policy and a digest cannot be
   read for one — and re-validated and re-bound to their key on read, applying
   the freeze review's lesson before it could be found again. A fresh epoch
   per posture is decided by the store as the next one, with the two postures
   counting separately; the posture bindings are READ from the certified
   profile rather than restated; and the cross-field rule the frozen schema's
   own description says JSON Schema cannot express — an execution session's
   assignment belongs to the session's Work — is checked here. NO BATON
   CAPABILITY is kept by construction: the boundary takes no session, token or
   authority handle at all. Seven mutations, all seven witnessed; A2's first
   attempt was arithmetically identical and is recorded. 453 v12, zero
   test-owned roots, all four design models green, every gate in the tree
   green.
   Evidence: `evidence/agent-session-slice-2026-08-23.txt`.
4f. [changes requested 2026-08-23; agent-session opening review] Close all
   three P1 boundaries in `review-2026-08-23T02-36-51Z.md`: bind a retained
   profile's declared seal to both its recomputed bytes and row key; enforce
   at most one nonterminal session per posture with an atomic cross-manager
   guard/epoch allocation; and reproject the exact live assignment before
   opening execution while keeping the manager's authority capability away
   from provider and relay calls. Retain the three additive regressions and
   revise the freshness case to terminate an epoch before opening its
   successor. Focused gate is 10/13 and full v12 is 453/456 until corrected.
   Evidence: `evidence/review-agent-session-slice-2026-08-23.txt`.
4f. [changes requested 2026-08-23; agent-session independent review] Close
   three: the retained profile's DECLARED seal was never compared against its
   key; a posture could hold several concurrent open sessions because
   freshness and concurrency were built and tested as one rule; and an
   execution session opened against an assignment the authority had already
   ended, because the reprojection was missing — which my own structural
   "no Baton capability" case had defended.
   Evidence: `evidence/review-agent-session-slice-2026-08-23.txt`.
4f. [done 2026-08-23] All three closed. Declared, recomputed and the key are
   ONE fact — two of three witnesses agreeing is not agreement. A partial
   UNIQUE INDEX on `(attempt, posture) WHERE state <> 'closed'` decides
   concurrency, driven from a second connection, because a read of MAX and a
   separate insert is not an atomic allocator; `closeAgentSession` is the only
   thing that frees a posture and `unknown` deliberately does not, since
   re-identification after transport ambiguity is a gate this slice has not
   built. And the manager's participant-bound handle is a parameter, read once
   to reproject the full four-part assignment before the insert: I had
   conflated the trusted manager, which IS the Baton authority client, with
   the untrusted agent endpoint that must never receive a capability. Six
   mutations, all six witnessed. 458 v12, zero test-owned roots, all four
   design models green, every gate in the tree green.
   Evidence: `evidence/correction-agent-session-2026-08-23.txt`.
4g. [changes requested 2026-08-23; corrected agent-session re-review] Preserve
   the three item 4f corrections, then bind the authority session used to open
   execution to the assignment participant. `assignmentOf` is a Work
   projection, not proof that its reader is that assignment's participant; a
   genuine foreign participant session currently opens the execution session.
   Snapshot and compare the session participant before insertion, and retain
   the additive real-authority two-session regression. Focused gate 15/16;
   full v12 458/459. Review: `review-2026-08-23T02-51-57Z.md`; evidence:
   `evidence/re-review-agent-session-correction-2026-08-23.txt`.
4g. [changes requested 2026-08-23; agent-session correction re-review] Close
   one: `openAgentSession` checked only that the authority handle could
   ANSWER, and `assignmentOf` is Work-scoped — so a session genuinely minted
   for another participant opened an execution session. The three prior
   findings were accepted as closed.
   Evidence: `evidence/re-review-agent-session-correction-2026-08-23.txt`.
4g. [done 2026-08-23] Closed. The handle's participant is compared against the
   attempt's fixed assignment participant before anything is written, refused
   as `refused.precondition`, and a foreign or missing binding inserts
   nothing. The activation slice already carried this exact lesson in a
   comment I wrote — the claim says which assignment this attempt won, the
   binding says who is asking — and I re-derived only one of the two here. A
   consent session still needs no handle, because it exists before any claim.
   Three mutations, two witnessed and one MEASURED: reading the binding into a
   local is equivalent to reading it inline, since the value is used once and
   the stored participant comes from the attempt; the local is kept and the
   comment says so rather than implying a guard. 461 v12, zero test-owned
   roots, all four design models green, every gate in the tree green.
   Evidence: `evidence/correction-agent-session-round2-2026-08-23.txt`.
4h. [signed off 2026-08-23; agent-session opening third review] Independent
   review accepted item 4g and the complete bounded opening slice. A genuine
   foreign participant session and a missing binding refuse before projection
   or insertion; the attempt remains the source of the stored assignment;
   consent remains handle-free. All earlier digest, concurrency, closure and
   live-assignment corrections remain green. Focused gate 18/18; full v12
   461/461. Turns, normalized events, adapter contracts and ambiguity
   re-identification remain open. Review: `review-2026-08-23T03-01-41Z.md`;
   evidence: `evidence/signoff-agent-session-opening-2026-08-23.txt`.
4h. [signed off 2026-08-23; agent-session opening slice] Independent sign-off
   with no remaining finding: the handle's participant binding, the three
   retained profile-digest witnesses, one non-closed session per posture
   enforced by the database, `unknown` not freeing a posture, the live
   four-part reprojection, and the separate consent/execution bindings.
   Evidence: `evidence/signoff-agent-session-opening-2026-08-23.txt`.
4i. [done 2026-08-23; item 4 THIRD SLICE] The turn and its outcome. Schema
   9 -> 10 adds `turns`, with `deadline_at` NOT NULL and the derived permitted
   set stored beside the outcome. `selectTurnOutcome` takes the evidence a
   relay actually holds and REFUSES when none of it names an outcome, because
   the alternative to refusing is the inference §5.4 spends a section
   forbidding. The precedence is an argument rather than a convenience: a
   policy failure ends the turn where it happens, a terminal fact outranks an
   elapsed deadline because it ARRIVED, and transport death outranks the
   deadline because the epoch is gone. The ACP mapping is exact and an unknown
   stop reason is refused. The acceptance table is transcribed verbatim and
   driven exhaustively in both directions; `cancelled` and `policy-failed`
   permit nothing because the assignment is ended, and `timeout` and
   `transport-lost` permit nothing because they say the relay does not know.
   Eight mutations, all eight witnessed; D2 and D3 keep every mapping and only
   reorder the precedence, and both fail. 474 v12, zero test-owned roots, all
   four design models green, every gate in the tree green.
   Evidence: `evidence/agent-turn-slice-2026-08-23.txt`.
4j. [changes requested 2026-08-23; turn/outcome independent review] Preserve
   the accepted vocabulary, ACP mapping, precedence and exhaustive gate, then
   close five P1 boundaries in `review-2026-08-23T03-15-42Z.md`: implement the
   frozen Codex `failed` and `codexErrorInfo` mappings exactly; validate and
   seal a complete frozen turn record before semantic reads or persistence;
   retain the exact policy failures that select `policy-failed`; journal the
   durable turn act so exact retries replay and changed operands collide; and
   return no caller-owned alias. Revise the existing contradictory Codex test
   to the frozen §10.3/§10.6 table and retain all six additive regressions.
   Focused gate 13/19; full v12 474/480. Evidence:
   `evidence/review-agent-turn-slice-2026-08-23.txt`.
4j. [changes requested 2026-08-23; turn-slice independent review] Close
   five: the Codex terminal mapping contradicted the frozen table and my own
   case defended the contradiction; the durable turn bypassed its frozen shape
   and seal; the policy fact that selected the outcome was discarded; the act
   was neither replay- nor collision-safe; and the first answer aliased the
   caller's terminal fact.
   Evidence: `evidence/review-agent-turn-slice-2026-08-23.txt`.
4j. [done 2026-08-23] All five closed. `CODEX_TURN_STATUSES` carries the three
   §10.3 statuses and §10.6 is transcribed in full — eleven rows, each with an
   outcome AND the closed error pair — and driven exhaustively. The other four
   findings have one correction between them: build the complete frozen
   `turnRecord`, validate it against the placed schema BEFORE reading semantic
   members, seal it, and commit it through the manager's operation journal,
   whose byte-stable result is what the first caller and every retry receive.
   Schema 10 -> 11 adds the canonical `body`, its `document_digest` and a
   `policy_failures` column. ONE DELIBERATE DIVERGENCE: the review asks an
   unrecognized `codexErrorInfo` to refuse, and §10.6 ends "an unrecognized
   value takes the last row" — the frozen sentence is implemented, the quote
   sits beside the code and in the case, and the disagreement is raised on the
   handoff. Eight mutations, six witnessed and two MEASURED as masked or
   equivalent. 487 v12, zero test-owned roots, all four design models green,
   every gate in the tree green.
   Evidence: `evidence/correction-agent-turn-2026-08-23.txt`.
4k. [changes requested 2026-08-23; corrected turn-slice re-review] The prior
   review's unknown-`codexErrorInfo` refusal is superseded: frozen §10.6 says
   an unrecognized value takes its last row, and the implementation is right.
   Preserve the five otherwise-corrected boundaries, then close two P1s in
   `review-2026-08-23T03-32-55Z.md`: apply the durable-secret guard to the
   complete turn document before persistence, and prevent the disposition
   gate from trusting an unsealed summary independently of the canonical turn
   record. Authenticate loaded turn shape, all three digest witnesses and the
   requested turn identity; consume or cross-check that record for safety
   decisions. Retain both additive regressions. Focused gate 26/28; full v12
   gate 487/489. Evidence:
   `evidence/re-review-agent-turn-correction-2026-08-23.txt`.
4k. [changes requested 2026-08-23; turn-correction re-review] The §10.6
   disagreement is resolved IN THE IMPLEMENTATION'S FAVOUR — the re-review
   supersedes its own prior point and confirms an unrecognized
   `codexErrorInfo` takes the final row. Two remaining: the turn body could
   durably retain a live bearer, because the journal scans the summary it
   commits and that summary omits `evidence` and `adapter_diagnostics`; and
   the disposition gate read the unsealed `permitted` column rather than the
   sealed record.
   Evidence: `evidence/re-review-agent-turn-correction-2026-08-23.txt`.
4k. [done 2026-08-23] Both closed. `assertNoDurableSecret` runs over the exact
   owned document before anything can be inserted or journalled — a scan over
   a projection is a scan over the projection. The gate consumes the sealed
   record and requires the summary columns to AGREE with it, because a drifted
   query column is an integrity failure wherever it is found and the next
   reader may be one that only has the column; and `turnRecordOf` binds a
   fourth witness, the identity the caller asked for, since three digests can
   agree while the record answers to somebody else's turn. Five mutations,
   three witnessed and two MEASURED as masked or inert. 492 v12, zero
   test-owned roots, all four design models green, every gate in the tree
   green.
   Evidence: `evidence/correction-agent-turn-round2-2026-08-23.txt`.
4. [in progress] Implement provider-neutral agent-session profile,
   session/turn/event normalization and runtime/agent adapter contracts with
   deterministic scripted adapters; no Docker/provider mutation in this slice.
5. [after implementation] Run schema, negative, retry, race and restart
   gates at every durable boundary; keep the current v12 and the 144 relevant
   W151/worker-control/agent-session design tests green, and record
   implementer progress and return for independent review.
   The design-test count moved with the W4487 rounds and each figure is
   superseded by the next: 122 before the amendment; 134 after it
   (W151 54 -> 61, worker-control 12 -> 17); **144 now** (W151 61 -> 64,
   worker-control 17 -> 24, agent-session 56 unchanged) after the review and
   re-review added the operation-signature recomputation and the pinned
   verifier derivation. The conformance package is 74 and is counted
   separately, as it always has been.
3h. [changes requested 2026-08-22; correction re-review] Close the remaining
   boundaries in `review-2026-08-22T22-53-46Z.md`: enforce one offer/claim per
   runtime-attempt identity; resolve observation source replay/collision before
   current-state transition logic; let later mismatch or multiplicity enter
   cancellation from uncertainty; preserve a concurrent attachment winner and
   translate the different runtime into cancellation instead of attach-operation
   collision; and classify only actual SQLite lock contention as a competing
   observer. Retain all six additive cases. The focused gate is 27/33 and the
   full v12 gate is 309/315 until corrected. Evidence:
   `evidence/re-review-attempt-slice-2026-08-22.txt`.
3i. [changes requested 2026-08-22; second-correction re-review] Close the
   remaining boundaries in `review-2026-08-22T23-07-46Z.md`: durably consume
   every accepted adapter source identity even when its axis value is already
   current; make multiplicity discovered while `stopping` return the safety
   cancellation response without regressing the axis; and classify SQLite
   contention from structured or exact lock indicators rather than a `busy`
   substring in arbitrary prose. Retain all three additive cases. The focused
   gate is 35/38 and the full v12 gate is 317/320 until corrected. Evidence:
   `evidence/re-review-attempt-slice-round3-2026-08-22.txt`.
3j. [signed off 2026-08-22; third-correction re-review] Independent review
   signed off the activation/runtime-start slice through item 3i. Sourced
   no-change observations consume and replay one durable identity;
   cancellation while `stopping` returns the decision without rewinding the
   axis; and SQLite contention is decided only by BUSY/LOCKED primary result
   codes. Focused gate 41/41; full v12 gate 323/323. Review:
   `review-2026-08-22T23-21-33Z.md`; evidence:
   `evidence/re-review-attempt-slice-round4-2026-08-22.txt`. W2929 remains in
   progress for cancellation ordering, output freeze/intake/cleanup and all
   of item 4.
3l. [changes requested 2026-08-22; cancellation-slice review] Preserve the
   accepted authority-first fence, refusal behavior, stable separate operation
   identities and real-authority coverage, then close the three boundaries in
   `review-2026-08-22T23-40-54Z.md`: keep cancellation ordering open until the
   required post-fence agent-cancellation act is represented (or append a
   confirmed superseding decision that makes 3k only a runtime-side partial
   slice); never report `stopped:true` solely because `adapter.stop` returned;
   and reconcile 3k's “not repeated while stopping” prose with the code and
   regression that deliberately re-order that stable stop operation. Retain
   the additive stopped-fact regression. Focused gate 53/54; full v12 gate
   335/336. Evidence:
   `evidence/review-cancellation-slice-2026-08-22.txt`.
3m. [changes requested 2026-08-22; cancellation-correction re-review] Retain
   the three corrected boundaries from item 3l, then ensure a throwing agent
   cancellation boundary cannot suppress runtime stop after the authority has
   already fenced and ended the assignment. Preserve agent-before-runtime
   call order, expose the agent failure to the caller, and never promote either
   settlement to positive quiescence. Retain the additive injected-failure
   regression. Focused gate 57/58; full v12 gate 339/340. Review:
   `review-2026-08-22T23-55-38Z.md`; evidence:
   `evidence/re-review-cancellation-slice-2026-08-22.txt`.
3n. [changes requested 2026-08-23; cancellation failure-handling review]
   Retain the corrected post-fence ordering and ordinary failure aggregation,
   then separate agent-failure presence from its thrown value. `null` is a
   legal JavaScript throw value and cannot also mean “no failure”: the current
   sentinel silently returns success after such a failure. Retain the additive
   null-failure regression. Focused gate 60/61; full v12 gate 342/343. Review:
   `review-2026-08-23T00-05-09Z.md`; evidence:
   `evidence/re-review-cancellation-round3-2026-08-23.txt`.
3o. [signed off 2026-08-23; cancellation-ordering fourth review] Independent
   review accepted the slice through item 3n. Authority fencing precedes both
   post-fence acts; agent failure cannot suppress runtime stop; single and
   dual failures remain visible for every thrown value; settlements remain
   verbatim; and none becomes runtime-quiescence evidence. Focused gate 64/64;
   full v12 gate 346/346. Bounded: output freeze, intake, cleanup and item 4
   remain unimplemented, including durable agent-session failure evidence.
   Review: `review-2026-08-23T00-13-56Z.md`; evidence:
   `evidence/signoff-cancellation-ordering-2026-08-23.txt`.
3q. [changes requested 2026-08-23; output-freeze review] Preserve the accepted
   quiescence, disposition, liveness, manifest-validation and fixed-identity
   boundaries, then close four findings in
   `review-2026-08-23T00-30-49Z.md`: validate the complete freeze operation
   including its signature; resolve exact record replay before later output
   state can hide it; compare result outputs with a trusted digest-verified
   input declaration; and retain a canonical full result manifest rather than
   only its summary/artifact subset. Retain both additive regressions and add
   declared/missing/type mismatch plus reopen/full-manifest durability cases.
   Focused gate 24/26; full v12 gate 370/372. Evidence:
   `evidence/review-freeze-slice-2026-08-23.txt`.
3r. [changes requested 2026-08-23; corrected output-freeze re-review] Preserve
   the corrected complete freeze identity, output-axis-independent replay,
   full result retention and bidirectional declaration comparison, then close
   four boundaries in `review-2026-08-23T00-49-18Z.md`: validate a loaded
   declaration specifically as an input manifest and against its digest key;
   enforce every declared output constraint decidable from the sealed result;
   refuse rather than ignore an existing result-manifest digest/body
   collision; and resolve exact result replay before current input-retention
   state. Retain all four additive cases. Focused gate 39/43; full v12 gate
   385/389. Evidence: `evidence/re-review-freeze-slice-2026-08-23.txt`.
3s. [changes requested 2026-08-23; second-correction output-freeze re-review]
   Preserve all four corrected item 3r boundaries, then close the symmetric
   status/material rule in `review-2026-08-23T01-02-53Z.md`: a required output
   cannot become a successful result merely by saying `present` while carrying
   neither a content manifest nor an artifact. Retain the additive case.
   Focused gate 50/51; full v12 gate 396/397. Evidence:
   `evidence/re-review-freeze-round2-2026-08-23.txt`.
3t. [signed off 2026-08-23; output-freeze fourth review] Independent review
   accepted the slice through item 3s. Missing output carries no material;
   present output binds both its content manifest and artifact reference; both
   representations are bounded; and all earlier identity, replay, retained
   manifest, declaration and constraint corrections remain green. Focused
   gate 53/53; full v12 gate 399/399. Bounded: intake, cleanup, W2930 artifact
   byte verification and item 4 remain open. Review:
   `review-2026-08-23T01-12-35Z.md`; evidence:
   `evidence/signoff-output-freeze-2026-08-23.txt`.
