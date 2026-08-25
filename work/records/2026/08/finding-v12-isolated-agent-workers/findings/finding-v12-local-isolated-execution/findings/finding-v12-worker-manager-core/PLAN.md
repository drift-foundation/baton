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
4l. [changes requested 2026-08-23; turn/outcome third re-review] Preserve the
   accepted complete-document secret scan and sealed-record disposition gate,
   then close four boundaries in
   `review-2026-08-23T14-47-38Z.md`: give every supervised turn a stable
   identity independent of prompt content so two same-prompt turns remain
   distinct; bind a genuinely new turn to the full durable session reference
   and a nonterminal session state while preserving replay after later close;
   resolve an exact committed turn before current ephemeral secret-liveness
   checks; and translate malformed input/summary shapes into the closed error
   taxonomy. Retain all six additive regressions. Full v12 gate 492/498 until
   corrected. Evidence: `evidence/review-agent-turn-round3-2026-08-23.txt`.
4l. [done 2026-08-23] All four closed. The turn identity carries the
   MANAGER-OWNED supervision window `(started_at, deadline_at)` that §5.1
   mints per supervised turn — no prompt content, stable across retry, and
   deliberately excluding the OBSERVED `ended_at` so a re-reported end
   collides rather than minting a second document. The window is a component
   and carries no uniqueness rule of its own, because an accepted case already
   shares one window between two prompts. `admitTurn` binds the full durable
   reference and a closed set of states a turn may SETTLE in, named positively
   from the frozen `sessionState` enum. Admission and the durable-secret scan
   both moved INSIDE the journalled transaction, so an exact retry replays and
   a changed one collides before either mutable check runs — one move
   answering two findings. Both malformed shapes report closed pairs. ONE
   DELIBERATE STRICTNESS: `not-started` and `initializing` are refused too,
   which is more than the review asked, and it is raised on the handoff
   because a later slice must move a session into an admitting state before
   recording a turn. Eight mutations, seven witnessed and one MEASURED as
   masked. 504 v12, zero test-owned roots, all four design models green, every
   gate in the tree green.
   Evidence: `evidence/correction-agent-turn-round3-2026-08-23.txt`.
4m. [changes requested 2026-08-23; turn/outcome fourth re-review] Preserve the
   accepted session admission, immutable-answer ordering and preceding
   regressions, then close `review-2026-08-23T15-09-47Z.md`: allocate or
   atomically validate one durable manager-owned identity per supervised turn
   rather than using a reusable timestamp window with prompt bytes as its
   fallback discriminator; prove non-cloneable policy-failure elements before
   clone; and translate malformed retained record bytes to the closed
   integrity taxonomy. Retain both additive regressions. Full v12 gate 504/506
   until corrected. Evidence:
   `evidence/review-agent-turn-round4-2026-08-23.txt`.
4m. [changes requested 2026-08-23; turn/outcome fourth re-review] Preserve the
   accepted session admission, replay-before-mutable-state ordering and the
   two closed pairs, then close the structural P1 in
   `review-2026-08-23T15-09-47Z.md`: the supervision window is reusable data
   rather than an allocated per-turn identity, so prompt bytes still decide
   whether one reused window means one act or two. Introduce a manager-owned
   turn token allocated at the supervision boundary and durably bound to the
   epoch, move prompt bytes into the effective signature, and revalidate the
   same-window/different-prompt fixture against the corrected contract. Also
   close two P2 escapes: raw `DataCloneError` for a non-cloneable policy
   failure and raw `SyntaxError` for unparsable retained record bytes. Retain
   both additive regressions. Full v12 gate 504/506 until corrected.
   Evidence: `evidence/review-agent-turn-round4-2026-08-23.txt`.
4m. [done 2026-08-23] All three closed. Schema 11 -> 12 adds
   `turn_allocations`: `allocateTurn` claims the next per-epoch ordinal under
   the write lock, the UNIQUE constraint makes epoch-local uniqueness a fact
   rather than an intention, the token derives from `(attempt, posture, epoch,
   ordinal)` alone, and `turns.turn_id` REFERENCES the allocation. `recordTurn`
   takes the token AS the identity — nothing is derived any more — and binds
   it to this epoch inside the write transaction. Prompt bytes moved to the
   effective signature, so a changed prompt under one allocated turn COLLIDES
   instead of becoming a quiet second turn; the exclusion of the observed
   `ended_at` is now structural. Both malformed shapes report closed pairs.
   TWO DELIBERATE CHOICES RAISED ON THE HANDOFF: allocation is not journalled
   (an abandoned ordinal is a visible gap, and journalling it would invent the
   identity allocation produces), and allocation does not ask the
   settle-admitting question (opening a turn asks whether the epoch exists;
   settling asks about the state that holds then). TWO EXISTING ASSERTIONS
   CHANGED because the ruling superseded them, and two fixtures revalidated
   with assertions untouched — all four named in PROGRESS and the evidence.
   Nine mutations: five witnessed, one witnessed only as a pair, two MEASURED
   as masked. 508 v12, zero test-owned roots, all four design models green,
   every gate in the tree green.
   Evidence: `evidence/correction-agent-turn-round4-2026-08-23.txt`.
4n. [changes requested 2026-08-23; turn-allocation fifth re-review] Preserve
   item 4m's durable per-epoch identity, prompt/signature separation and two
   closed-pair corrections, then close
   `review-2026-08-23T16-15-49Z.md`: allocation is the boundary that opens a
   supervised turn before its prompt, so under the same write lock it must
   admit the full durable provider-session reference and the frozen graph's
   positive START state (`ready`) before inserting. Keep record-time admission
   distinct so a legitimately opened turn can settle in every permitted later
   state and exact committed replay still precedes current state. Retain the
   additive exhaustive allocation regression. Full v12 gate 508/509 until
   corrected. Evidence: `evidence/review-agent-turn-round5-2026-08-23.txt`.
4n. [changes requested 2026-08-23; turn-allocation fifth re-review] Preserve
   the accepted schema-12 allocation, token identity, prompt/signature
   separation and both round-4 closed-error corrections, then close the P1 in
   `review-2026-08-23T16-15-49Z.md`: `allocateTurn` is the supervision
   boundary and admits only epoch existence, so it opens turns in every
   non-`ready` and terminal state and accepts a mismatched provider-session
   label. Admit allocation under the existing write lock against a positive
   START set and the full durable provider identity before inserting, keep
   `recordTurn`'s separate SETTLE checks, and migrate the exhaustive
   settlement case to open while ready and then move the state. Retain the
   additive regression. Full v12 gate 508/509 until corrected. Evidence:
   `evidence/review-agent-turn-round5-2026-08-23.txt`.
4n. [done 2026-08-23] Closed. `TURN_STARTING_SESSION_STATES` is `["ready"]` —
   §7.3 draws one edge that starts a prompt — and `admitTurnStart` checks it
   plus the full durable provider reference inside `allocateTurn`'s existing
   BEGIN IMMEDIATE, before the insert, so a refused opening leaves nothing
   behind. `admitTurnSettlement` keeps the separate SETTLE set, with the
   provider comparison factored into one `bindProviderSession` so the two
   boundaries cannot drift apart on that half. ROUND 4's REASONING FOR THE
   OMISSION IS SUPERSEDED and marked so in FINDING.md: opening asks the
   stricter question, and the rest of that argument was about fixtures rather
   than design. Two of my cases migrated to open-while-ready-then-perturb as
   the review directed; two of the reviewer's round-3 cases now resolve at the
   START boundary with assertions untouched, and mutations confirm both
   admission boundaries are still independently witnessed. Five mutations, all
   witnessed. 511 v12, zero test-owned roots, all four design models green,
   every gate in the tree green.
   Evidence: `evidence/correction-agent-turn-round5-2026-08-23.txt`.
4n. [signed off 2026-08-23; turn-allocation sixth review] Independent review
   accepted the fifth correction. Allocation admits the exact durable `ready`
   session and full provider identity under its write lock before inserting;
   settlement retains its distinct broader positive state set and provider
   check after immutable replay; and the migrated fixtures independently
   witness both settlement predicates. Full v12 gate 511/511; whitespace
   clean. Bounded: prompt/adapter composition, event normalization and
   transport-ambiguity re-identification remain open. Review:
   `review-2026-08-23T16-28-19Z.md`; evidence:
   `evidence/signoff-agent-turn-round5-2026-08-23.txt`.
4o. [delivered 2026-08-23; awaiting first review] Update normalization, frozen
   §6.1-6.4. Schema 12 -> 13 adds `agent_events`, whose PRIMARY KEY
   `(attempt, posture, epoch, source_seq)` IS the duplicate rule and whose
   `late`/`observation_seq` are columns beside the sealed frame rather than
   members of it. The closed ten kinds and the thirteen-row ACP table are
   transcribed and driven exhaustively in both directions; an unmapped update
   becomes `other`, counted, with no portable content; image/audio/resource
   and unseen block types are counted and dropped; tool calls take the
   provider's id and one of ACP's four statuses. The seal is verified before
   any other field, the full provider reference is bound, a same-seal
   duplicate replays the ORIGINAL observation and a different-seal one is
   `integrity.digest`, lateness is decided once at first sight, the pinned
   `max_event_bytes` refuses over-limit input without partial action, and the
   complete document is scanned for durable secrets. TWO EXCLUSIONS NAMED ON
   THE HANDOFF: §6.5's relay queue belongs with the adapter contracts (its
   durable half is already the turn record's dropped counters), and this
   boundary does not gate on session state because §6.4 gives it no state
   rule. Thirteen mutations, all witnessed. 540 v12 (was 511), zero
   test-owned roots, all four design models green, every gate in the tree
   green.
   Evidence: `evidence/event-normalization-slice-2026-08-23.txt`.
4o. [changes requested 2026-08-23; event-normalization first review] Preserve
   the accepted schema-13 ledger, closed taxonomy, counted/dropped blocks,
   seal-first admission, collision/lateness rules and secret scan, then close
   `review-2026-08-23T16-47-06Z.md`: keep agent reasoning out of portable
   content; consume the captured root-level ACP tool-call shape; return an
   owned authenticated copy of the durable sealed document on first answer
   and replay; derive and validate the durable turn binding from the seal; and
   enforce the event limit against complete canonical event bytes rather than
   its claimed source-byte count. Apply only the two explicitly authorized
   existing-test migrations and retain all six additive regressions. Full v12
   gate 540/546 until corrected. Evidence:
   `evidence/review-event-normalization-round1-2026-08-23.txt`.
4p. [changes requested 2026-08-23; event-normalization first review] Preserve
   the accepted schema-13 ledger, closed taxonomy, dropped blocks, ordering,
   collision, lateness replay and secret scan, then close four P1 boundaries
   in `review-2026-08-23T16-47-06Z.md`: keep `agent_thought_chunk` content out
   of portable evidence per §6.2; consume the captured ROOT-level ACP
   tool-call shape; return and replay-authenticate the same durable sealed
   document; use the sealed `turn_id` as the durable identity rather than an
   optional operand; and bound the canonical event bytes rather than the
   document's own `byte_count`. Two case-specific existing-test migrations are
   authorized. Retain all six additive regressions. Full v12 gate 540/546
   until corrected. Evidence:
   `evidence/review-event-normalization-round1-2026-08-23.txt`.
4p. [done 2026-08-23] All four closed. `agent-reasoning` joins the contentless
   set and its bytes are still counted; the tool-call path reads `toolCallId`
   and `status` at the update root as the frozen trace records them;
   `authenticateRetained` is shared by the reader and the REPLAY path so a
   duplicate answers from the record rather than from its index, and both
   answers carry the sealed document; the sealed `turn_id` is the durable
   identity and a redundant operand may only agree in both directions; and the
   bound measures `canonicalBytes(event)` while `byte_count` keeps its
   source-accounting job. THREE existing cases migrated on the review's
   explicit authority, each with the authority named beside it. CARRIED
   FORWARD, NOT RESOLVED: §6.2's prose names a tool-call `kind` that the
   frozen `toolCallView` forbids; no such member is invented and a case
   records the omission, but the inconsistency needs an owning record. Nine
   mutations: eight witnessed, one MEASURED as equivalent. 550 v12 (was 540),
   zero test-owned roots, all four design models green, every gate in the tree
   green.
   Evidence: `evidence/correction-event-normalization-2026-08-23.txt`.
4q. [changes requested 2026-08-23; event-normalization second review]
   Preserve every accepted 4p correction and close the two adjacent paths in
   `review-2026-08-23T17-01-19Z.md`: bind a retained event read to the full
   requested session reference, including provider-session id, and translate
   a non-durable value encountered while sealing into the closed
   `integrity.schema` pair without flattening an existing `ContractError`.
   Retain both additive regressions. The separate tool-call `kind` contract
   contradiction is W543 and is not resolved here. Full v12 gate 550/552
   until corrected. Evidence:
   `evidence/re-review-event-normalization-round2-2026-08-23.txt`.
4q. [changes requested 2026-08-23; event-normalization second review] Preserve
   the four corrected boundaries and all six first-review regressions, then
   close two in `review-2026-08-23T17-01-19Z.md`: bind the FULL requested
   session reference on retained reads, including `provider_session_id`,
   refusing a disagreement as `runtime-observation.identity-mismatch` while
   preserving null for a genuinely absent row; and translate non-durable
   caller input at the seal boundary into `integrity.schema` while preserving
   a more precise existing `ContractError`. Retain both additive regressions.
   Full v12 gate 550/552 until corrected. Evidence:
   `evidence/re-review-event-normalization-round2-2026-08-23.txt`.
4q. [done 2026-08-23] Both closed. The requested reference is a fifth witness
   in `authenticateRetained` beside the shape and the three digests; absence
   and disagreement are deliberately different answers, and a case holds both.
   `ownDurable` covers content, the tool call and diagnostics, with the seal
   wrapped separately because `canonicalBytes` is the other place a caller's
   value becomes durable — and a precise existing `ContractError` passes
   through unchanged, with a case that fails if the precise text is merely
   interpolated into a general refusal. TWO OF MY OWN MUTATION INSTRUMENTS
   WERE WRONG on the first pass and both were silent: one lost to `&&`/`||`
   precedence, the other satisfied by interpolation. Both are fixed, both now
   fail, and the episode is recorded because a zero-witness mutation is a
   claim about the code that was twice a defect in the instrument. Eight
   mutations: seven witnessed, one MEASURED as unreachable; one further
   comparison MEASURED as inert from the replay path. 555 v12 (was 550), zero
   test-owned roots, all four design models green, every gate in the tree
   green. The carried ACP tool-call `kind` conflict now has its own owner,
   W543, and is deliberately untouched here.
   Evidence: `evidence/correction-event-normalization-round2-2026-08-23.txt`.
4q. [signed off 2026-08-23; event-normalization third review] Independent
   review accepted both corrections: retained reads bind the complete
   requested session reference while preserving genuine absence, and every
   caller-supplied durable frame member crosses a closed ownership boundary
   without flattening precise canonical `ContractError` evidence. Focused
   event gate 44/44; full v12 gate 555/555; whitespace clean. Bounded: §6.5,
   adapter composition/contracts and transport-ambiguity re-identification
   remain open; W543 independently owns the tool-call `kind` contract
   conflict. Review: `review-2026-08-23T17-11-20Z.md`; evidence:
   `evidence/signoff-event-normalization-round2-2026-08-23.txt`.
4r. [signed off 2026-08-23; event-normalization second review] Independent
   review accepted the event slice through item 4q. The retained reader binds
   all four requested session-reference components while preserving genuine
   absence, and the seal boundary owns every caller-supplied durable member
   through the closed taxonomy while preserving precise canonical evidence.
   Focused 44/44; full v12 555/555. Bounded: §6.5, adapter composition and
   contracts, transport-ambiguity re-identification and W543 remain open.
   Review: `review-2026-08-23T17-11-20Z.md`; evidence:
   `evidence/signoff-event-normalization-round2-2026-08-23.txt`.
4s. [delivered 2026-08-23; awaiting first review] The handshake and the closed
   surface, frozen §2.1-§2.5. The required, refused, served-client-method and
   capability sets are MODULE constants, because §2.3 gives the version those
   sets and a profile that could restate them could disagree with them.
   `negotiateAcp` requires a currently certified profile, an EXACT pinned wire
   version with no downgrade, all five required methods and all six mandatory
   capabilities; `bindProvider` certifies a version-less provider by exact
   build and captured interface digest instead, and each door refuses the
   other's profile. The advertised client surface is compared EXACTLY, not as
   a subset, because a member ACP adds next version would pass a subset check
   on the day it appeared. `checkOutboundMethod` refuses all twenty-one
   whether or not advertised; `serveClientMethod` denies all eight as a §4
   violation rather than a capability question. The constants are transcribed
   from the frozen design model and the case file PARSES that model and
   compares member for member. FIVE EXCLUSIONS NAMED ON THE HANDOFF: §6.5,
   §8.1, §8.2, §8.4 and §8.5. Thirteen mutations: twelve witnessed, one
   MEASURED as unreachable; one instrument corrected before it was believed.
   569 v12 (was 555), zero test-owned roots, all four design models green,
   every gate in the tree green.
   Evidence: `evidence/handshake-slice-2026-08-23.txt`.
4t. [changes requested 2026-08-23; handshake first review] Preserve the
   accepted exact version/provider binding, certification, mandatory endpoint
   and session-capability checks, module-owned sets and all enumerated
   refusals. Close two boundaries in
   `review-2026-08-23T17-26-19Z.md`: separate §2.2's literal ACP wire
   `{ "fs": {}, "terminal": false }` from the durable normalized snake-case
   profile summary and compare the wire document structurally; then make both
   method guards allow-list boundaries so unknown/future outbound methods are
   `refused.capability` and every unadvertised client method is
   `policy.denied`. W641 owns the independent frozen-artifact conflict and
   does not excuse either product correction. Retain all four additive
   regressions. Full v12 gate 569/573 until corrected. Evidence:
   `evidence/review-handshake-round1-2026-08-23.txt`.
4t. [changes requested 2026-08-23; handshake first review] Preserve the
   accepted negotiation, provider binding, certification, mandatory
   method/capability checks and module-owned sets, then close two P1s in
   `review-2026-08-23T17-26-19Z.md`: separate §2.2's exact ACP WIRE
   capabilities `{fs:{},terminal:false}` from the durable normalized
   snake-case summary and compare structurally rather than by serialization
   order; and make both claimed closed method surfaces ALLOW lists rather than
   deny lists, preserving the known `session/update` agent-origin route. Four
   case-specific migrations are authorized. Retain all four additive
   regressions. Full v12 gate 569/573 until corrected. Evidence:
   `evidence/review-handshake-round1-2026-08-23.txt`.
4t. [done 2026-08-23] Both closed. `ACP_WIRE_CLIENT_CAPABILITIES` and
   `NORMALIZED_CLIENT_CAPABILITIES` are separately named documents and a case
   asserts they differ; the advertisement is compared structurally, and an
   `fs` member present AT ALL — even set false — is denied, because the wire
   withholds by absence. `checkOutboundMethod` admits only
   `KNOWN_AGENT_SURFACE`, the five required plus three optional that are every
   method existing in 1.0; `serveClientMethod` denies EVERY method, because
   nothing is advertised to enumerate against; and `routeAgentOriginCall` is a
   new named boundary owning the one agent-origin name. FOUR existing cases
   migrated on the review's explicit authority, each preserving its
   withholding, fresh-copy or routing assertion. Eight mutations, all
   witnessed — reverting either guard to what was delivered last round now
   fails. 574 v12 (was 569), zero test-owned roots, all four design models
   green, every gate in the tree green. W641 owns the frozen-artifact
   conflation and is untouched.
   Evidence: `evidence/correction-handshake-2026-08-23.txt`.
4u. [changes requested 2026-08-23; handshake correction re-review] Preserve
   every accepted item-4t correction, then close the directional overlap in
   `review-2026-08-23T17-39-42Z.md`: the five required endpoint methods span
   both directions, so the relay-outbound allow list must exclude the
   separately routed agent-origin `session/update`. Keep handshake validation
   at five; admit the other four required plus three optional methods
   outbound; retain `session/update` only through `routeAgentOriginCall`; and
   prove the two allow lists disjoint. One case-specific existing assertion
   migration is authorized. Retain the additive regression. Full v12 gate
   574/575 until corrected. Evidence:
   `evidence/re-review-handshake-round2-2026-08-23.txt`.
4u. [changes requested 2026-08-23; handshake re-review] Preserve the accepted
   wire/durable split, structural validation, default-closed unknowns, denied
   client-call surface and the separate agent-origin route, then close the
   directional P1 in `review-2026-08-23T17-39-42Z.md`: the relay-outbound
   allow list is still the required five plus three and therefore still
   admits `session/update`, which the pinned SDK places in `CLIENT_METHODS`.
   Keep handshake validation at five, build the outbound list from the four
   relay-origin required names plus the three optional ones, and prove the
   two directional lists disjoint. Retain the additive regression. Full v12
   gate 574/575 until corrected. Evidence:
   `evidence/re-review-handshake-round2-2026-08-23.txt`.
4u. [done 2026-08-23] Closed. `REQUIRED_AGENT_METHODS` stays at five for
   handshake validation; `KNOWN_AGENT_SURFACE` is renamed
   `RELAY_OUTBOUND_SURFACE` on the review's authority and DERIVED as the
   required baseline minus `AGENT_ORIGIN_METHODS` plus the optional three, so
   the two directional lists cannot drift apart. Seven names;
   `checkOutboundMethod("session/update")` refuses and
   `routeAgentOriginCall("session/update")` still returns it. Revalidated
   against the pinned SDK 1.3.0 declaration rather than the prose. An added
   case proves the two surfaces PARTITION the baseline rather than merely
   avoiding each other, so a required name cannot be dropped from both
   unnoticed. Four mutations, all witnessed — including one that reproduces
   exactly what was delivered last round. 576 v12 (was 574), zero test-owned
   roots, all four design models green, every gate in the tree green.
   Evidence: `evidence/correction-handshake-round2-2026-08-23.txt`.
4v. [signed off 2026-08-23; handshake directional third review] Independent
   review accepted item 4u and the handshake slice through §2.1-§2.5. The
   five-member endpoint baseline remains mandatory at handshake; the seven
   relay-outbound names are derived directionally; `session/update` is
   refused outbound and accepted through its distinct agent-origin route; and
   the two lists partition the required baseline. Focused handshake 21/21;
   full v12 576/576; whitespace clean. Bounded: §6.5, adapter
   composition/contracts, permission handling and transport-ambiguity
   re-identification remain open; W543 and W641 remain independent. Review:
   `review-2026-08-23T17-48-38Z.md`; evidence:
   `evidence/signoff-handshake-round2-2026-08-23.txt`.
4v. [signed off 2026-08-23; handshake re-review] Independent review accepted
   the handshake slice through item 4u with no further findings in the bounded
   slice. Focused 21/21; full v12 576/576. Review:
   `review-2026-08-23T17-48-38Z.md`; evidence:
   `evidence/signoff-handshake-round2-2026-08-23.txt`.
4w. [delivered 2026-08-23; awaiting first review] The agent-session
   observation axis, frozen §7.3-§7.4. `SESSION_STATES` and
   `ALLOWED_SESSION_SUCCESSORS` are transcribed from the frozen model and the
   case file PARSES that model's table and compares edge for edge;
   `observeAgentSessionState` moves the durable axis inside the write
   transaction, treats a self-observation as a no-op answer rather than a
   regression, and refuses every forbidden edge as
   `runtime-observation.state-regression`; `satisfiesRuntimeQuiescenceGate`
   always answers false and validates its argument. All EIGHTY-ONE ordered
   pairs are driven in both directions. This closes the hole the turn slice
   recorded: nothing previously moved a session out of `not-started`.
   RAISED FOR AN OWNING RECORD, NOT FIXED HERE: `closeAgentSession` takes four
   edges the frozen table forbids, including `unknown -> closed`, and there is
   a contract question underneath about what frees a posture. Eight mutations:
   six witnessed, one witnessed only as a pair. 588 v12 (was 576), zero
   test-owned roots, all four design models green, every gate in the tree
   green.
   Evidence: `evidence/session-axis-slice-2026-08-23.txt`.
4x. [changes requested 2026-08-23; session-axis first review] Preserve the
   exact frozen table, all-pairs decision, transactional durable move,
   no-op self-observation, terminal behavior and runtime-quiescence
   separation, then close the P1 in
   `review-2026-08-23T18-02-11Z.md`: normalize the full §3.1 session reference
   before SQL and bind stored `provider_session_id` before both no-op and move
   decisions. Malformed references are `integrity.schema`; provider identity
   disagreement is `runtime-observation.identity-mismatch`; neither changes
   the row. Retain both additive regressions. W771 independently owns the
   close/posture-release contract conflict, which final W4 composition must
   revalidate rather than locally resolve. Full v12 gate 588/590 until
   corrected. Evidence: `evidence/review-session-axis-round1-2026-08-23.txt`.
4x. [changes requested 2026-08-23; session-axis first review] Preserve the
   accepted nine-state table, all eighty-one pairs, transactional moves,
   no-op self-observation, terminal behaviour, malformed-state taxonomy and
   quiescence separation, then close the P1 in
   `review-2026-08-23T18-02-11Z.md`: normalize and prove the COMPLETE session
   reference before the query, select the stored `provider_session_id` with
   the state, and bind it before BOTH the self-observation answer and the
   successor decision. Retain both additive regressions. Full v12 gate
   588/590 until corrected. Evidence:
   `evidence/review-session-axis-round1-2026-08-23.txt`.
4x. [done 2026-08-23] Closed. `sessionAxisRef` proves the complete reference —
   nonempty attempt id, one of the two postures, positive integer epoch, and a
   NONEMPTY provider id or null — as `integrity.schema` before any query; the
   stored provider id is selected with the state and compared inside the same
   transaction BEFORE the self-observation shortcut, because a no-op is still
   an observation and affirming another session's axis is the same mistake as
   moving it. THIRD OCCURRENCE of this finding in this Work and the record
   says so: the missing component authorizes nothing, so its absence never
   breaks a happy path, and eighty-one exhaustively driven transition pairs
   said nothing about it. Four mutations, all witnessed, including one that
   keeps the binding and moves it a single line past the shortcut. 592 v12
   (was 588), zero test-owned roots, all four design models green, every gate
   in the tree green.
   W771 acknowledged and untouched; FINAL W4 COMPOSITION MUST REVALIDATE ITS
   DISPOSITION before integrated session lifecycle work.
   Evidence: `evidence/correction-session-axis-2026-08-23.txt`.
4y. [signed off 2026-08-23; session-axis correction re-review] Independent
   review accepted item 4x and the agent-session observation axis through
   frozen §7.3-§7.4. Full-reference validation precedes SQL; provider identity
   is bound inside the same write transaction before both no-op and move
   decisions; and both disagreement directions leave the row unchanged. The
   exact table, all-pairs coverage, terminal behavior and quiescence separation
   remain green. Focused 16/16; full v12 592/592; whitespace clean. W771 is
   untouched and final W4 composition must revalidate its disposition. Review:
   `review-2026-08-23T18-11-15Z.md`; evidence:
   `evidence/signoff-session-axis-round2-2026-08-23.txt`.
4y. [signed off 2026-08-23; session-axis re-review] Independent review
   accepted the session axis through item 4x with no further finding in the
   bounded slice. Focused 16/16; full v12 592/592. W771 remains untouched and
   mandatory to revalidate at final W4 composition. Review:
   `review-2026-08-23T18-11-15Z.md`; evidence:
   `evidence/signoff-session-axis-round2-2026-08-23.txt`.
4z. [delivered 2026-08-23; awaiting first review] Reconnect ambiguity, frozen
   §8.4. `handleTransportLoss` moves the durable axis to `unknown` through
   `observeAgentSessionState` — so the full §3.1 reference is proved and bound
   as it is everywhere else — and answers with the three facts §8.4 names plus
   the outcome: no resume, no re-prompt, no new epoch without positive runtime
   re-identification, and `transport-lost` when a turn was in flight. The
   outcome is REPORTED and not recorded, because this boundary holds no turn
   token, prompt digest or supervision window and inventing them would mint
   evidence about a turn it never saw. Whether a turn was in flight is STATED
   rather than inferred. `repromptAfterTransportLoss` refuses
   `ambiguous.operation` whatever is sent, and
   `transportReachabilityReidentifies` always answers false.
   NAMED ON THE HANDOFF: W151 §9's re-identification GATE is not built — its
   FLAG is, so a later slice contends with a recorded `false` rather than a
   gap; `nextEpoch` is untouched and this slice adds no gate to it. Eight
   mutations, all witnessed. 601 v12 (was 592), zero test-owned roots, all
   four design models green, every gate in the tree green.
   Evidence: `evidence/reconnect-slice-2026-08-23.txt`.
4aa. [changes requested 2026-08-23; reconnect first review] Preserve the
   accepted `unknown` transition, idempotence, explicit outcome selection,
   absence of fabricated turn evidence, re-prompt refusal and reachability
   separation, then close both P1s in
   `review-2026-08-23T18-21-55Z.md`: snapshot and validate the four-member
   session reference once before mutation and use that same owned value for
   both the axis and answer; validate every supplied options container before
   the axis so malformed containers are `integrity.schema` and move nothing.
   Retain both additive regressions. The next-epoch flag is a reported,
   non-durable fact and does not discharge W151 §9's deferred enforcement
   gate. W771 remains mandatory at final W4 composition. Full v12 gate
   601/603 until corrected. Evidence:
   `evidence/review-reconnect-round1-2026-08-23.txt`.
4aa. [changes requested 2026-08-23; reconnect first review] Preserve the
   accepted `unknown` transition, idempotence, explicit outcome, absence of a
   fabricated turn record, `ambiguous.operation` refusal and reachability
   separation, then close two P1s in `review-2026-08-23T18-21-55Z.md`:
   snapshot the exact four-member §3.1 reference ONCE instead of re-reading
   and spreading the caller's object after the commit, and prove the supplied
   options envelope before any mutation. Retain both additive regressions.
   Full v12 gate 601/603 until corrected. Evidence:
   `evidence/review-reconnect-round1-2026-08-23.txt`.
4aa. [done 2026-08-23] Both closed. `normalizeAgentSessionRef` is exported
   from the axis module — no behaviour change there — so the reference is
   proved ONCE, before the durable observation, and the same snapshot goes to
   the axis and into the answer; the answer carries exactly the four members
   and is a fresh copy. The options envelope is proved before anything durable
   happens, and the member is read only when the KEY is present, because a
   default is for an argument nobody gave rather than one somebody gave
   wrongly. MY FIRST FIX REPEATED THAT MISTAKE ONE LEVEL DOWN and this slice's
   own earlier case caught it immediately. Six mutations: five witnessed, one
   MEASURED as equivalent; one of the five keeps every check and only moves
   the proof a line after the commit. 605 v12 (was 601), zero test-owned
   roots, all four design models green, every gate in the tree green. The
   next-epoch flag remains reported rather than durable enforcement.
   Evidence: `evidence/correction-reconnect-2026-08-23.txt`.
4ab. [changes requested 2026-08-23; reconnect correction re-review] Preserve
   the accepted one-read reference snapshot, exact fresh answer, primitive and
   array envelope refusals, explicit-member validation, and all §8.4 behavior.
   Close the remaining P1 in `review-2026-08-23T18-32-05Z.md`: an options
   document is a plain record, not any JavaScript object. Reject Dates, Maps,
   regular expressions, class instances and custom-prototype/inherited-member
   bags as `integrity.schema` before mutation; test `turnInFlight` as an own
   member. Retain the additive re-review regression. Focused 13/14 and full
   v12 605/606 until corrected. W151 §9 remains deferred; W771 remains
   mandatory at final W4 composition. Evidence:
   `evidence/re-review-reconnect-round2-2026-08-23.txt`.
4ab. [changes requested 2026-08-23; reconnect re-review] Preserve the accepted
   one-read reference ownership and the fresh four-member answer, then close
   the P1 in `review-2026-08-23T18-32-05Z.md`: the envelope guard accepts
   every non-array object, so a Date, a Map, a regular expression, a class
   instance and an inherited-member object take the absent default and commit
   `unknown`. Require a plain record — `Object.prototype` or null prototype —
   and test the optional member as an OWN member. Retain the additive
   regression. Full v12 gate 605/606 until corrected. Evidence:
   `evidence/re-review-reconnect-round2-2026-08-23.txt`.
4ab. [done 2026-08-23] Closed. `isPlainRecord` admits an object whose
   prototype is `Object.prototype` or null and nothing else — the only test
   that generalizes, since enumerating the exotic types this contract happens
   to know would admit the next one on the day it appeared. The optional
   member is read with `hasOwnProperty`, and refusal messages name a value by
   its constructor because a Map and a class instance both stringify to `{}`.
   THIRD ALLOW-RULE-IMPLEMENTED-AS-DENY-RULE in this Work, and the record says
   so: the previous round wrote "a default is for an argument nobody gave" and
   then tested `typeof === "object"`. Four mutations, all witnessed; the
   ownership one needed a prototype-pollution case to be reachable at all, and
   the reviewer's own case corrected one of mine. 624 v12, zero test-owned
   roots, all four design models green, EVERY GATE IN THE TREE GREEN —
   including the failure W771's handoff named and left for this round.
   Evidence: `evidence/correction-reconnect-round2-2026-08-23.txt`.
4ac. [changes requested 2026-08-23; reconnect correction third review]
   Preserve the accepted item-4ab plain-record and own-member boundary, then
   close the P2 in `review-2026-08-23T18-55-02Z.md`: refusal diagnostics must
   not serialize a rejected member or inspect a rejected object's prototype
   constructor. Return `integrity.schema` even for BigInt members and hostile
   custom-prototype bags, before mutation, and retain both additive
   regressions. Focused reconnect is 16/18. The current full v12 gate is
   624/631: these two W4 cases plus five independently owned W771 cases.
   Evidence: `evidence/review-reconnect-round3-2026-08-23.txt`.
4ac. [changes requested 2026-08-23; reconnect third review] Preserve the
   accepted plain-record boundary, then close the P2 in
   `review-2026-08-23T18-55-02Z.md`: `JSON.stringify` on a rejected BigInt
   leaks a raw `TypeError` and `describe()` runs an untrusted prototype's
   `constructor` getter. Use inert bounded type facts, do not serialize or
   inspect rejected caller behaviour, and translate unavoidable reflection
   failure. Retain both additive regressions. Evidence:
   `evidence/review-reconnect-round3-2026-08-23.txt`.
4ac. [done 2026-08-23] Closed. `describe` is built from `typeof`,
   `Array.isArray` and a wrapped prototype comparison — nothing serialized and
   no property of the value or its prototype read — and the member refusal
   uses it instead of serializing the member. The result is deliberately
   coarse, because a diagnostic that has to be exactly right about an
   untrusted value has to touch it. THE HELPER WAS MINE, ADDED LAST ROUND to
   improve a refusal, and it became a second escape route at the one moment
   the boundary had already decided to refuse. Three added cases: seven
   hostile shapes each hostile differently, an ACCEPTED document proved
   untouched, and the message proved still useful. TWO MEASUREMENTS rather
   than a count — the reflection wrapper alone is unreachable for ordinary
   values and the constructor read alone is caught by it; the pair is what the
   cases witness. One of my own cases asserted an assumed outcome rather than
   the rule that applies and was corrected. W4's own suites are green;
   the remaining v12 failures are W543's and W771's open rounds.
   Evidence: `evidence/correction-reconnect-round3-2026-08-23.txt`.
4ad. [changes requested 2026-08-23; reconnect correction fourth review]
   Preserve item 4ac's inert formatter and closed prior cases, then close the
   remaining P2 in `review-2026-08-23T19-13-23Z.md`: take one translated
   prototype snapshot for both classification and description, and inspect
   `turnInFlight` through one guarded own-property descriptor so accessors are
   refused without execution. Translate Proxy/reflection failures as
   `integrity.schema`, retain both additive regressions, and keep the session
   axis unchanged on refusal. Focused reconnect is 21/23; full v12 is
   633/642, with two W4, two W543, and five W771 failures. Evidence:
   `evidence/review-reconnect-round4-2026-08-23.txt`.
4ad. [changes requested 2026-08-23; reconnect fourth review] Preserve the
   accepted BigInt and hostile-constructor corrections, then close the
   remaining P2 in `review-2026-08-23T19-13-23Z.md`: `isPlainRecord` reflects
   UNWRAPPED before `describe` reaches its wrapped comparison, so a Proxy trap
   leaks an arbitrary Error; and reading an own `turnInFlight` accessor
   executes behaviour instead of reading document data. Take one translated
   prototype snapshot and inspect one guarded own-property descriptor. Retain
   both additive regressions. Evidence:
   `evidence/review-reconnect-round4-2026-08-23.txt`.
4ad. [done 2026-08-23] Closed. ONE translated prototype snapshot is taken and
   shared by the record test and the description, so there is a single place
   the reflection happens; `ownTurnInFlight` reads one guarded own-property
   descriptor and accepts absence or a DATA descriptor. THE RULE WAS RIGHT AND
   I HAD APPLIED IT AT ONE OF TWO SITES — last round's own comment said to
   translate reflection failure, and the first of the two calls was left bare.
   Five mutations: four witnessed, one MEASURED as masked, with the
   distinction stated — the guard that keeps a getter from running is reading
   the descriptor instead of the property, and the accessor branch is its
   explanation rather than a second guard. Two added cases: a Proxy trapping
   each reflection site, and an own accessor refused with the getter asserted
   not to have run. W4's own suites are green — reconnect 25/25, axis 16/16,
   turn 50/50 — and the six remaining v12 failures are W543's, W641's and
   W771's open rounds.
   Evidence: `evidence/correction-reconnect-round4-2026-08-23.txt`.
4ae. [changes requested 2026-08-23; reconnect correction fifth review]
   Preserve item 4ad's shared prototype snapshot and descriptor-based member
   read, then close the remaining P2 in
   `review-2026-08-23T19-42-22Z.md`: translate the `Array.isArray` failure a
   revoked Proxy can raise on both envelope and member diagnostic paths, and
   do not inspect the arbitrary value thrown by a descriptor trap when
   forming the translated refusal. Retain both additive regressions and keep
   the session axis unchanged on refusal. Focused reconnect is 25/27; full
   v12 is 646/652, with two W4, two W543 and two W641 failures. W771 is green
   at 25/25 in that full run. Evidence:
   `evidence/review-reconnect-round5-2026-08-23.txt`.
4ae. [done 2026-08-23] Closed. `Array.isArray` is inside the translated
   snapshot now, along with the prototype read, so EVERY classification this
   boundary performs happens in one guarded place and the next one added is
   inside the translation by construction. The descriptor catch takes no
   binding and its message is manager-owned text, the same whatever was
   thrown. THE COMMENT HAD CLEARED THE OPERATION THAT WAS FAILING: two rounds
   of prose said `Array.isArray` "invokes nothing", which is true and is not
   the property that matters — it throws on a revoked Proxy anyway. Beyond the
   review, and reported rather than folded in: having array classification in
   the snapshot exposed that `isPlainRecord` judged documenthood from the
   prototype alone, so a Proxy over an array wearing `Object.prototype` was a
   valid options envelope; one line tests the rule instead of inferring it.
   Five mutations, all witnessed — the first attempt at one did not PARSE,
   which `node --check` caught before it could look like a witness. Two added
   cases, both properties rather than instances: all three reflection traps
   with a thrown object whose every member is a throwing getter, and an array
   refused as envelope and as member, bare and Proxy-dressed. W4's own suites
   are green — reconnect 29/29, axis 16/16, turn 50/50, posture slots 25/25 —
   and the two remaining v12 failures are W641's open round.
   Evidence: `evidence/correction-reconnect-round5-2026-08-23.txt`.
4af. [changes requested 2026-08-23; reconnect correction sixth review]
   Preserve item 4ae's translated classification and manager-owned catch
   diagnostics, then close the accepted-path P1 in
   `review-2026-08-23T20-09-23Z.md`: a Proxy that returns plausible prototype
   and descriptor answers is behavior, not an ordinary/null-prototype record,
   and must be rejected without executing any trap on both envelope and member
   paths. A translated thrown trap is insufficient because successful traps
   currently author operands and can commit `unknown`. Retain both additive
   regressions. Focused reconnect is 29/31; full v12 is 654/658, with two W4
   and two W641 failures. Evidence:
   `evidence/review-reconnect-round6-2026-08-23.txt`.
4af. [done 2026-08-23] Closed. A Proxy is refused BEFORE any reflection, by a
   NON-OBSERVING test (`node:util/types.isProxy`, which reads an internal slot
   and runs no trap) rather than by another try/catch, which a successful trap
   would simply walk past. FIVE ROUNDS WENT INTO MAKING REFLECTION FAIL SAFELY
   AND THE HOLE WAS THE ORDINARY CASE: every guard assumed a hostile value
   misbehaves, and a Proxy over `{}` that answers plausibly needed no exception
   at all — it ran caller code AND committed the epoch. One guard covers both
   paths because both classify through one helper. One assertion of my own is
   superseded and marked where it stood: a Proxy-dressed array is now named
   "a Proxy" because it never reaches array classification; bare arrays still
   say "an array" and the refusal is unchanged. Four mutations, all witnessed
   — my first attempt at one measured zero and was not the mutation I meant,
   the third instrument slip in two days. One added case, a property: every
   one of a Proxy's thirteen traps instrumented across six operands with none
   permitted to run, INCLUDING one whose answers would have been correct, plus
   a positive half proving the guard does not simply refuse ordinary data.
   RAISED FOR A RULING, NOT DECIDED: the same defect exists on a session
   REFERENCE — measured, four get traps run and it is accepted — in the
   signed-off axis on every observation path. Reconnect 32/32; the two
   remaining v12 failures are W641's second review.
   Evidence: `evidence/correction-reconnect-round6-2026-08-23.txt`.
4ag. [signed off 2026-08-23; reconnect correction sixth review] Independent
   review accepted item 4af. The non-observing Proxy guard precedes all
   reflection on both envelope and member paths; live, revoked and
   accepted-looking Proxies run no trap and move no axis; ordinary and
   null-prototype records remain accepted. Focused reconnect/axis/turn/posture
   suites are 32/16/50/25. Full v12 is 662/664, with both failures owned by
   W641's open handshake correction. Review:
   `review-2026-08-23T20-28-51Z.md`; evidence:
   `evidence/signoff-reconnect-round6-2026-08-23.txt`.
4ah. [open decision; final W4 composition] Rule the session-reference
   container boundary explicitly. `normalizeAgentSessionRef` currently
   accepts a Proxy and runs four `get` traps, while item 4aa deliberately
   accepted a one-read owned snapshot to prevent disagreement. Decide whether
   §3.1 references are inert data records or structural values read once. An
   inert ruling must supersede item 4aa explicitly and prove exact own data
   members through W641's shared primitive; rejecting Proxies alone while
   ordinary accessors still execute is incomplete.
4ai. [queued; composition ownership] W641 owns the shared inert-record
   extraction and its two failing handshake regressions. W4 must consume and
   revalidate that primitive at composition, not edit the same helper
   concurrently under two Work claims. Revalidate W771 posture lifecycle and
   W151 §9 next-epoch enforcement in the same final composition pass.
4ai. [done 2026-08-23] Consumed and REVALIDATED. `agent_reconnect.mjs` calls
   W641's `records.mjs` and keeps no copy; I did not edit that module.
   Revalidation is not "the suites are green" but "they would go red if the
   dependency changed", so it was measured by MUTATING THE SHARED MODULE:
   removing the Proxy test fails 4 reconnect cases, deciding after the traps
   run fails 3, dropping the prototype rule fails 5. Reconnect 32/32,
   unchanged from the signed-off 4af. W771's posture lifecycle revalidated at
   the W4 boundary (open occupies in one transaction, close releases only its
   own slot, transport loss recovers an applicable same-epoch occupied slot;
   25/18/16 green; no further `v12/src` consumer). W151 §9 unchanged and still
   deferred, named so that "revalidated" does not quietly mean "not looked
   at". Evidence: `evidence/composition-revalidation-2026-08-23.txt`.
4aj. [done 2026-08-23] THE CLOSED TAXONOMY, SWEPT. Six rounds established that
   a refusal must never serialize what it refuses and each round fixed the ONE
   site the reviewer found; nobody swept. Measured: ELEVEN diagnostic sites
   across six modules lost the closed pair to `JSON.stringify(x ?? null)` on a
   BigInt, a circular object, a throwing `toJSON` or a trapping Proxy. One
   helper now — `nameValue` in `contracts.mjs`, beside the `ContractError` it
   builds, calling `records.mjs` for shapes rather than duplicating it. The
   diagnostic is still worth reading: a string primitive cannot throw, so a
   method name is SHOWN and bounded at 60 characters, and only values with
   behaviour are reduced to a shape.
4ak. [done 2026-08-23] OPERANDS THAT REACHED SQLITE UNPROVED — a different
   class found by the same sweep. `turnRecordOf`, `eventRecordOf` and
   `attempts.attemptRow` bound caller operands straight into prepared
   statements, so an object produced SQLite's own binding error and a trapping
   Proxy an arbitrary Error of the caller's choosing. Each proves its operand
   first; `eventRecordOf` proves the reference through §3.1's own normalizer
   and uses THE ONE OWNED COPY for both the query and the retained binding.
   ABSENCE AND REFUSAL STAY DIFFERENT ANSWERS: a well-formed id naming nothing
   still answers null.
4al. [done 2026-08-23] TWO COPIES OF §3.1 THAT HAD DIVERGED, not merely
   duplicated: `turnSessionRef` ACCEPTED an empty `providerSessionId` that
   `normalizeAgentSessionRef` REFUSED, so the same reference was valid at one
   boundary and invalid at the other. No ruling needed — the frozen
   `$defs.providerSessionId` is `minLength: 1`; the axis was right and the
   turn copy had dropped "nonempty" from its check and from its own message.
   The case that owns it drives BOTH copies through one table, because the
   defect was that nothing compared them. STILL LOOSER THAN FROZEN and NOT
   fixed here: neither copy enforces `maxLength` or `opaqueId`'s pattern —
   that changes what is ACCEPTED and belongs with 4ah.
4am. [queued; for the 4ah ruling] Measurements, not a decision: ordinary
   accessors RUN and are accepted (four of four); item 4aa's one-read
   protection HOLDS (measured, one read, so check and answer cannot
   disagree); a class instance and even an ARRAY carrying the four members are
   accepted; extra members are accepted and dropped; and the frozen
   `$defs.agentSessionRef` is ALREADY `additionalProperties: false` over
   exactly those four, which is contract evidence for the inert reading though
   it governs the document form. The blast radius grew by one: 4ak routed
   `eventRecordOf` through the axis normalizer. If inert is ruled,
   `recordFault(ref, [the four])` does it exactly and BOTH copies must change.
4an. [changes requested 2026-08-23; final composition review] Preserve the
   accepted shared-record composition, W771 revalidation, empty-provider-id
   alignment and the 162-cell closed-taxonomy sweep, then close the two
   independent findings in `review-2026-08-23T20-55-23Z.md`: prove the full
   frozen opaque-id grammar and 160-character bound before every SQL lookup
   so malformed identity is not reported as absence/precondition; and bound
   Symbol/BigInt diagnostic renderings as well as strings. Retain all three
   additive reviewer regressions. Full v12 is 678/680, with only those two
   reviewer cases failing. Evidence:
   `evidence/review-composition-round1-2026-08-23.txt`.
4ao. [proposed ruling; awaiting Slawomir] Resolve item 4ah as one explicit
   contract decision. Reviewer recommendation: the in-process §3.1 reference
   is the same exact inert four-member record as the frozen document form;
   prove it through W641's shared primitive, enforce the frozen member bounds,
   and explicitly supersede item 4aa's structural one-read boundary. Do not
   treat this proposal as authority until ruled.
4an. [done 2026-08-23] P1 closed. Item 4ak proved "nonempty string" and the
   frozen `$defs.opaqueId` also bounds length at 160 and fixes the grammar
   `^[A-Za-z0-9][A-Za-z0-9._:-]*$` — so a string with a space or 161
   characters was a legitimate lookup, and a malformed identity collapsed into
   ABSENCE at the turn read and into a precondition at the attempt read. IT
   WAS INCOMPLETE IN THE DIRECTION THE ITEM WAS ABOUT. One proof now,
   `opaqueIdFault` in `contracts.mjs`, called by every boundary that types an
   identifier as `opaqueId`: the turn read, the attempt read, the §3.1
   normalizer (and through it the event reader's third SQL operand) and the
   posture-slot boundary. The frozen `providerSessionId` `maxLength: 512` is
   enforced with it. THE CONTAINER QUESTION IS UNTOUCHED — this proves the
   MEMBERS the frozen schema types, and 4ah is still open.
4aq. [done 2026-08-23; tracking correction from duplicate 4ao] P2 closed.
   `nameValue` bounded the branch I had thought
   about: strings were truncated and `String(value)` was returned unbounded for
   numbers, bigints and symbols, so a 1000-character symbol description
   rendered at 1008. I had been reasoning about whether a value is safe to
   CONVERT; the rule is whether the result is safe to KEEP. One bound, applied
   where the rendering is produced.
4ap. [done 2026-08-23] Not asked for, and necessary: fixing only the named
   boundaries would have MINTED A FRESH 4al — `posture_slots.requireAttempt`
   kept its own "nonempty" check, so a string with a space would have been a
   valid attempt id there and invalid everywhere else. It calls the shared
   proof now. Found by writing the property test BEFORE the fix. And
   `turnSessionRef` delegates to the axis normalizer rather than being a
   second aligned copy: alignment is a state, and two implementations kept in
   step by a regression drift the first time only one is edited — which this
   correction was about to do. Ten mutations; V9 measured zero and was a
   MISSING CASE (the provider bound had no witness), now covered at exactly
   512 and 513. Two added properties: ten identifiers × five boundaries
   asserting they AGREE rather than that each refuses, and the rendering bound
   over seven values plus the other half, that short values are not eaten.
   FULL v12 IS 682/682.
   Evidence: `evidence/correction-composition-round1-2026-08-23.txt`.
4ah. [OPEN RULING; relayed to baton.slaw, not decided by the implementer] The
   reviewer recommends the in-process §3.1 reference be the exact inert data
   record the frozen schema describes, proved through W641's `recordFault`,
   explicitly superseding item 4aa's structural one-read boundary. WHAT 4an
   CHANGED ABOUT THE DECISION: the MEMBER half is done either way — both
   frozen member bounds are enforced in one place at every boundary — so what
   remains is purely the CONTAINER, whether a class instance, an array, an
   accessor-backed object or one with extra members may carry the four proved
   members. And the cost of ruling "inert" fell: there is ONE normalizer now
   instead of two, so the ruling has one implementation to change.
4ar. [changes requested 2026-08-23; composition correction review] Preserve
   the accepted shared opaque-id proof, bounded diagnostic rendering,
   posture-slot unification and one §3.1 normalizer, then make the frozen
   provider-session limit count Unicode characters rather than JavaScript
   UTF-16 code units. Retain the additive exactly-512/513 astral-character
   rows. Focused taxonomy is 8/9 and full v12 681/682, with only that case
   failing. Review: `review-2026-08-23T21-08-54Z.md`; evidence:
   `evidence/review-composition-round2-2026-08-23.txt`.
4ar. [done 2026-08-23] P1 closed. THE BOUND WAS RIGHT AND THE RULER WAS WRONG:
   JavaScript `.length` counts UTF-16 code units and JSON Schema `maxLength`
   counts Unicode characters, so a provider session id of 512 ASTRAL
   characters has a `.length` of 1024 — valid under the frozen contract and
   refused by the hand-written proof that exists to be faithful to it. Item
   4an checked the NUMBER against the frozen schema and not the MEASURE. One
   ruler now, `withinCharacters` in `contracts.mjs`, exported as
   `withinFrozenLength`; fast and exact together, since a code point is never
   more than one code unit, so a string short enough in code units skips the
   iteration entirely. Applied at the two OTHER rulers as well rather than
   only where the review found it: the `opaqueId` limit, MEASURED AS
   EQUIVALENT for the verdict (its grammar admits only ASCII) but corrected
   because the wrong unit produced a FALSE DIAGNOSTIC; and the diagnostic
   bound, which sliced by code unit and could cut a surrogate pair in half,
   putting a lone surrogate into a message that may be retained. My own first
   draft of a case row assumed GRAPHEMES — `maxLength` counts CODE POINTS, so
   a combining sequence that renders as one glyph is two characters — and the
   row asserts the contract's unit now, with the reason beside it. Seven
   mutations, all witnessed, including one that keeps the fast path and
   deletes the exact count, which is the plausible way this gets broken later.
   FULL v12 IS 683/683.
   Evidence: `evidence/correction-composition-round2-2026-08-23.txt`.
   Tracking: the review's renumbering is accepted — the completed P2 is 4aq
   and 4ao stays with the open container ruling beside 4ah.
4as. [changes requested 2026-08-23; Unicode-ruler review] Preserve item 4ar's
   correct code-point verdict and surrogate-safe output, then stop bounded
   diagnostics from materializing the complete caller-sized tail through
   `[...text]` before slicing. Retain the additive iterator-count case: a
   1,000-character input currently yields 1,063 characters for a 61-character
   answer. Focused taxonomy 10/11; full v12 683/684. Review:
   `review-2026-08-23T21-19-33Z.md`; evidence:
   `evidence/review-composition-round3-2026-08-23.txt`.
4as. [done 2026-08-23] P2 closed. A BOUNDED OUTPUT IS NOT A BOUNDED OPERATION:
   `bounded` probed the length cheaply and then spread the WHOLE string to
   slice sixty characters off the front — 1,063 iterator steps and a full-size
   array for a 61-character answer. I fixed what I could see in the OUTPUT and
   left the work proportional to what was being discarded; round two was about
   measuring in the contract's unit and this is the same helper measuring
   inefficiently, which is the same mistake at a different depth — I checked
   the ANSWER and not the ACT. And it is a REFUSAL path, so this is "a refusal
   must not run the value it refuses" one property over. One pass that stops:
   at most 61 characters are ever visited, and the cheap code-unit test in
   front means an ordinary short value is not iterated at all. Four mutations;
   the short-circuit one measured zero as a behavioural EQUIVALENCE and I
   witnessed it instead of reporting it, by counting iterator yields for a
   SHORT name the way the review counted them for a long one — an optimisation
   nothing observes is an optimisation nothing protects. The added case is the
   general property: five boundaries with 20,000-member or 40,000-character
   operands, each refusing in under 500 characters, plus the short-input yield
   count so both halves are pinned. FULL v12 IS 685/685.
   Evidence: `evidence/correction-composition-round3-2026-08-23.txt`.
4at. [reported to W641, not fixed here] W641's shared `recordFault`
   interpolates every own member NAME of a rejected record. MEASURED: a
   capability envelope with 20,000 members produces a correct
   `policy.denied` whose message is 269,042 characters. Same defect as 4as, in
   the module W4 consumes. Item 4ai reserves `records.mjs` to W641, which is in
   its own review round, so a fix from here would put the change in the wrong
   Work. W641 had CLOSED satisfying by the time this was measured, so its
   thread would not take the report either — raised instead as follow-up Work
   W1593, bound to `work/records/2026/08/finding-unbounded-refusal-diagnostics`
   with the measurement. W4's new case carries the numbers and the two rows it
   should grow once W1593 is closed.
4au. [signed off 2026-08-23] Item 4as is accepted. The implementation stops
   after code point 61, preserves a 60-code-point surrogate-safe prefix, and
   skips iteration for ordinary short strings. The focused discarded-tail
   regression passes. Full v12 is currently 684/687; the three failures are
   exactly the additive W1593 record-diagnostic regressions and do not reopen
   4as. Review: `review-2026-08-23T21-33-40Z.md`; evidence:
   `evidence/signoff-composition-round3-2026-08-23.txt`.
4av. [decision required; route to baton.decide] Rule on the still-open 4ah/4ao
   container question before W4 can close. If the proposed inert exact-record
   contract is approved, explicitly supersede item 4aa and route implementation
   through W641's shared primitive; otherwise record why the structural
   one-read container remains authoritative. W1593 is independent follow-up
   Work and its three expected red regressions do not block this ruling.
4aw. [approved 2026-08-23; implementation next] Slawomir ruled that section
   3.1 session references are plain old data: an exact four-member ordinary or
   null-prototype record with own enumerable data properties. Explicitly
   supersede item 4aa's structural one-read boundary, retain no compatibility
   for Proxies, accessors, arrays, class instances, hidden members, or extras,
   and implement the proof through W641's shared inert-record primitive before
   returning W4 for one bounded independent review.
4ax. [supersedes item 4aw's implementation placement 2026-08-23; review next]
   Preserve the exact POD ruling but do not extend host-side JavaScript or
   W641's `records.mjs`. Replan W4 as the Python Worker Manager, carrying the
   reviewed durable state, replay, session, event, refusal, and conformance
   decisions forward as reference evidence. Return the revised Python boundary
   for approval before implementation; provider-native JavaScript remains
   confined to isolated worker images.
4au. [signed off 2026-08-23] Independent review signed off item 4as. The
   discarded-tail regression passes. The review also ENABLED the two capability
   rows I had left commented in W4's property case, so one property now guards
   both W4's five boundaries and W641's shared primitive — the right shape, and
   it means W4's suite cannot go green until W1593 lands.
   Review: `review-2026-08-23T21-33-40Z.md`.
4av. [done 2026-08-23; input for the ruling, NOT a decision] Re-measured every
   4ah fact against the CURRENT tree, since the ruling was being asked for on
   measurements taken several corrections ago. Accessors still run and are
   accepted; class instances, arrays carrying the four members, extra members
   and A PROXY are all still accepted; item 4aa's one-read guarantee still
   holds. THE PROXY ROW IS THE SHARPEST: the reconnect OPTIONS envelope refuses
   a Proxy before any reflection after six review rounds, and the REFERENCE
   beside it does not — two operands of one call, two answers to "may a
   document be a program".
   THEN MEASURED THE COST rather than estimating it: applied
   `recordFault(ref, [the four])` temporarily, ran the whole gate, reverted,
   and counted every reason it would refuse. 228 refusals, and they decompose
   very unevenly — 168 are ONE benign cause (a reference written without
   `providerSessionId`, valid today because the API reads `?? null`), most of
   the rest are values ALREADY refused today, and only ELEVEN are genuinely new
   container refusals. THIS EXPOSES A THIRD OPTION THE FRAMING DID NOT NAME:
   whether `providerSessionId` is required at the API or optional-in-absence.
   The cost people would associate with "inert" is almost entirely that
   question and not the container question, and the two are separable.
   Evidence: `evidence/ruling-input-4ah-2026-08-23.txt`.
4ay. [approved 2026-08-24] Replan W4 as a
   separately installable `v12/python/` Worker Manager package. It owns frozen
   schema package data, exact validation/canonicalization, a separate SQLite
   control store, manager orchestration and a runtime-neutral adapter port. It
   imports no v11 or host-side Node module and reads no dossier at runtime.
   Review: `review-2026-08-24T04-06-44Z.md`; evidence:
   `evidence/python-boundary-revalidation-2026-08-24.txt`.
4az. [approved blocking prerequisite 2026-08-24] There is no Python authority
   session for W4 to consume. Create separately owned Python authority Work,
   restore authority -> manager dependency ordering, and give W4 only its
   already-minted participant-bound session. Do not copy authority state into
   W4 and do not bridge to the frozen Node authority as a workaround.
4ba. [approved 2026-08-24] Python 3.13 is the trusted-host floor. Keep one
   self-contained `v12/python/` distribution with `pyproject.toml` for package
   intent and `requirements.lock` for the full hash-locked resolution. Use a
   real pinned Draft 2020-12 validator; the current repository venv has none.
   Product tests assert byte identity of packaged schemas with their canonical
   dossier assets. Authority and manager may share the distribution but never
   a module owner, store file, connection, schema or transaction.
4bb. [pending after approval] Implement contracts/POD/refusals first. Python
   POD means exact built-in dict/list and JSON primitives, with section 3.1 an
   exact four-member dict. Reject subclasses, duplicate decoded keys, invalid
   Unicode, non-string keys, bool-as-integer, floats and unsafe integers before
   durable use. Retain bounded W1593-style explanations without rendering the
   rejected value.
4bc. [pending after 4bb review] Implement the separate SQLite control schema,
   manager operation journal, canonical retained values, transactional CAS,
   exact replay/collision and multi-process race/restart tests.
4bd. [pending after 4bc review] Implement offer issue/decision/expiry,
   verifier consumption, fixed claim submission/settlement and recovery
   against the injected Python authority session. No adapter write occurs
   while claim outcome is ambiguous.
4be. [pending after 4bd review] Implement attempt axes, activation,
   cancellation ordering, output freeze/record, intake and cleanup. Keep agent
   and runtime quiescence, output, workflow and cleanup observations distinct.
4bf. [pending after 4be review] Implement profile/handshake/session/turn/event
   and posture-slot state machines, preserving fresh epochs, bounded events,
   observation replay/lateness, unexpected-approval denial and exact inert
   references.
4bg. [pending after 4bf review] Compose one public manager-core surface and
   narrow adapter protocols, run the portable vector/catalog, unit, race and
   restart gate, then return W4 for bounded independent review. W5 owns the
   Python host OCI adapter and all provider-native code remains inside the
   opaque worker image.
4bh. [approved 2026-08-24] Choose runtime Draft 2020-12 validation. Pin
   `jsonschema` 4.26.0 and its complete Python 3.13 resolver closure in the
   hash-locked `requirements.lock`; provision the offline wheelhouse with the
   exact pure-Python and platform-specific artifacts. Option B's test-only
   oracle and option C's partial first cut are rejected.
4bi. [authorized test migration for 4bb] Revise W2845's distribution-wide
   empty-dependency assertions: keep `baton_v12.authority` standard-library
   only, prove its supported surface still exposes no manager or validator
   capability, and give the Worker Manager a separate exact allowlist for its
   pinned validator dependency. Retain the locked offline installed-layout
   gate and every authority isolation assertion.
4bj. [required throughout the Python port] Retain the frozen Node authority,
   `v12/src/worker_manager/*.mjs`, and their executable tests unchanged as the
   comparison oracle until each portable obligation has an independently
   reviewed Python equivalent. Map language-specific mechanisms to portable
   properties explicitly; a lower Python test count is not evidence of parity.
4bk. [pending after 4bg sign-off] Create a deliberate retirement step for the
   superseded host-side Node authority/manager implementation and tests. It may
   run only after the portable obligation catalog, Python unit/race/restart
   gates and production import/entry-point audit pass independently. Preserve
   essential historical evidence in the dossier; never remove the oracle as
   incidental cleanup during implementation.
4ay. [prerequisite revalidated 2026-08-24; one still open] W4 was routed to
   implementation because its ledger dependency closed, which is not the same
   event as the boundary's approval landing. Revalidated both prerequisites
   against the current tree. PREREQUISITE ONE IS MET: W2845 is closed
   satisfying and delivers exactly the injected object `authority_port.py` was
   specified to type -- claim, settle_operation, activity, cancel, end,
   pass_work, publish, install_gate, satisfy_gate, the project/slot/operation
   reads, `Session.participant`, and `claim_signature` exported so the manager
   consumes the authority-owned signature rather than reinventing it.
   PREREQUISITE TWO IS HALF MET: the Python floor and the hash-locked offline
   build exist and are proven, but the wheelhouse holds only pip and
   setuptools, and jsonschema 4.19.2 is an ambient system dist-package that the
   isolated `--ignore-installed --require-hashes` build cannot see. Measured:
   the minimum runtime closure is SIX distributions and one of them, `rpds-py`,
   is a compiled Rust extension with no pure-Python fallback -- so provisioning
   is an environment change, not a file edit. Three options are measured rather
   than recommended in the evidence: provision the wheelhouse, keep the
   validator at TEST time only against the frozen schemas as oracle, or narrow
   cut A to everything except schema validation. The frozen schemas are not the
   problem: both still hash to their canonical dossier assets and both pass
   `check_schema` under Draft 2020-12. Nothing implemented; no file under
   `v12/python` created or changed.
   Evidence: `evidence/w4-prerequisite-revalidation-2026-08-24.txt`.
4az. [implementation cut A part one 2026-08-24; review next] The decision route
   returned W4 to implementation with no ruling recorded, no reply on the
   thread and no change to the wheelhouse. Blocking twice with nothing
   delivered would be the wrong answer, so I looked at what the ruling actually
   decides: ONE SEAM. Implemented everything in cut A that is needed under all
   three options -- the `baton_v12.contracts` package, the frozen schema assets
   as package data, the exact-POD ownership, section 9's closed refusal
   pairing, the bounded diagnostics and the section 3.2 canonicalizer. The
   validation seam is ABSENT, NOT STUBBED, and a case asserts no exported name
   claims to validate. The assumption is stated rather than hidden: the return
   to implementation is read as authorization for the option-independent core
   and NOT as an answer to the validator question, which stays open.
   THE PORT'S ONE REAL HAZARD, found and closed: RFC 8785 orders member names
   by UTF-16 CODE UNITS, which `Array.prototype.sort` gives the frozen host for
   free and which Python's `sorted()` does NOT -- the two disagree for an
   astral name beside one in U+E000..U+FFFF, so a transliteration would have
   produced different canonical forms and different digests while passing every
   test written from the Python side. The 21 vectors are GENERATED FROM the
   frozen host and all match byte for byte.
   Twenty-one mutations, all witnessed. Four began as zeros and all four were
   my tests rather than equivalences -- including an agreement case that
   compared a PRODUCTION HELPER to the schema, which a helper returning the
   schema's own codes made agree with itself. 40 regressions added, the suite
   is 227 -> 267, `just gate` green from source and from the installed wheel
   with both slices and the schema assets proved to have travelled.
   Evidence: `evidence/cutA-part-one-2026-08-24.txt`.
4bl. [changes requested 2026-08-24; Python Cut A part-one review] Preserve the
   accepted exact-POD, byte-identical schema and 21-vector canonical foundation,
   then close three additive regressions: obtain type names without invoking a
   caller-controlled metaclass, keep the exported category/code pairing from
   opening under caller mutation, and bound the final escaped diagnostic rather
   than only its pre-render input. The reviewed source suite is 267/270 with
   exactly those three failures. The durable runtime-validator ruling has now
   landed, so complete approved items 4bh/4bi in the same correction: pin and
   provision `jsonschema==4.26.0` plus its full Python 3.13 closure, retain the
   authority module's standard-library-only invariant, and deliberately replace
   the superseded distribution-wide empty-dependency assertions. Return the
   complete contracts cut for re-review. Review:
   `review-2026-08-24T09-56-54Z.md`; evidence:
   `evidence/review-cutA-part-one-2026-08-24.txt`.
4ba2. [cut A complete 2026-08-24; re-review next] Three findings closed, all
   reproduced first. Naming a rejected type ran the caller's METACLASS, because
   a class is an instance of its metaclass and `__name__` is ordinary attribute
   dispatch; `type.__getattribute__` closes the reported shape, and probing the
   correction found TWO MORE it does not close -- a metaclass `__name__`
   descriptor that raises and one that answers non-text -- both mutations with
   no witness until the case existed. The closed pairing was a public mutable
   dict the check itself consulted, so it is private and frozen now with the
   readable vocabulary beside it and a case proving they agree; opening a whole
   CATEGORY was a second escape the reviewer's code-only regression could not
   see. And the diagnostic bound was applied to the escaper's INPUT while
   `ascii()` expands an astral character to ten, so both the operation and the
   output are bounded now.
   THE RULED VALIDATOR IS IN: jsonschema 4.26.0 and its measured five-distribution
   closure, hash-locked from the artifacts, installing offline under
   `--require-hashes`. The wheelhouse moved into the distribution because the
   system one holds two artifacts and is not writable; whether 3.2 MB of wheels
   are COMMITTED is raised rather than answered, since the tree carries
   essentially no binaries today. The library decides the contract and this
   package decides the diagnostic: `error.message` is never used, ownership runs
   first so the validator only walks exact built-ins, and combinators are
   followed to the failure underneath them -- which my own case found, because
   "the document breaks oneOf" is true and helps nobody.
   Item 4bi's migration done: the authority's import scan is scoped to its slice,
   its two stale distribution-wide assertions are replaced by ones that measure
   the property rather than the file, and the manager has its own exact
   allowlist. Nineteen mutations, sixteen witnessed; three equivalences reported
   with reasons, one of them a cap that is UNREACHABLE against the whole schema
   and had to be witnessed where it can be reached. 30 regressions added, the
   suite is 267 -> 297, `just gate` green from source and from the wheel.
   The frozen Node oracle is untouched and still runnable.
   Evidence: `evidence/cutA-complete-2026-08-24.txt`.
4bm. [changes requested 2026-08-24; complete Cut A re-review] Retain the 297
   delivered cases and five additive reviewer methods. Name rejected types
   without invoking metaclass descriptors; freeze the authoritative refusal
   pairing's outer container; remove or constrain caller-supplied validator
   execution; construct fixed validators from caller-independent schema data;
   and enforce the exact ownership depth/width bounds before canonical bytes or
   digests are produced. Correct the stale no-validator and empty-runtime-
   dependency comments. The reviewed source suite is 297/302 methods, reported
   as six failures and one error because one method has three failing subtests.
   Proposed repository shape, pending Slawomir: retain the 3.2 MB local
   wheelhouse because the approved default gate is self-contained, offline and
   hash-locked and no separate artifact provisioner exists. Review:
   `review-2026-08-24T10-15-14Z.md`; evidence:
   `evidence/re-review-cutA-complete-2026-08-24.txt`.
4bn. [changes requested 2026-08-24; Cut A correction re-review] Retain the 302
   delivered methods and two additive regressions. Remove caller control of
   recursive traversal state from exported `canonical_text` and `own`; public
   wrappers initialize the counter and private helpers alone carry it. The
   delivered source and installed gates are green, while the reviewed source
   suite is 302/304 with exactly the two negative-depth bypasses failing. Review:
   `review-2026-08-24T10-24-07Z.md`; evidence:
   `evidence/re-review-cutA-correction-2026-08-24.txt`.
4ba3. [cut A correction 2026-08-24; re-review next] Four P1 authority seams and
   one P2 shared bound, all reproduced first, all closed, with the reviewer's
   five methods retained. THE SAME LINE CORRECTED TWICE is the instructive part:
   `type.__getattribute__` skipped a metaclass `__getattribute__` override and
   still invoked a DESCRIPTOR the metaclass installed, because any lookup that
   consults the metaclass consults the caller. I corrected the mechanism I had
   been shown instead of the rule underneath it -- the same mistake as fixing
   the one site a review names, now made at the level of one expression. The
   name binds `type.__dict__["__name__"]` directly.
   The pairing's outer container was an ordinary dict while the comment beside
   it promised frozen all the way down; privacy is not an isolation boundary and
   the authority's session face says so in as many words. Two doors still took a
   caller program: `validate_against` invoked any supplied object's
   `iter_errors` (identity, not shape, closes it -- asking whether it has the
   method is asking the attacker to confirm their credentials), and the
   validators were built over the exported readable schema dicts, so editing a
   projection rewrote the contract. And the frozen depth and width were enforced
   at `own` but not at the equally public canonical surface -- a rule applied at
   one of N sites, for the fifth time in this campaign -- so the bounds now live
   with the canonicalizer and `pod` takes them from there. Depth is checked
   during the descent so extreme nesting cannot escape as a raw RecursionError.
   Both stale statements corrected. Nine mutations, all witnessed, no zeros.
   Suite 297 -> 302, `just gate` green from source and from the wheel. The
   wheelhouse arrangement is unchanged, so the reviewer's repository-shape
   proposal stays open for Slawomir.
   Evidence: `evidence/cutA-correction-2026-08-24.txt`.
4ba4. [cut A traversal-state correction 2026-08-24; re-review next] Reproduced
   first: a caller could pass a negative `_depth` to either exported door and
   canonicalize or own a document past the frozen limit. A leading underscore
   names a convention, not a boundary. The previous correction SHARED the depth
   and width bounds and left the enforcement STATE of that shared rule as a
   parameter of both public functions -- the same defect one level lower, and
   the second round running in which I corrected the mechanism a review named
   rather than the rule underneath it. Each public operation takes only its
   genuine operands now, with the descent in a private helper.
   AND THE RULE IS CHECKED RATHER THAN THE TWO FUNCTIONS: a standing case
   refuses any public operation in this package whose parameters are bookkeeping
   rather than declared operands, with its own vacuous-pass modes refused.
   Measured: a future `digest(value, seen=None)` -- no underscore at all --
   fails it, which is the half an underscore check would have missed.
   Seven mutations. One was a MISSING CASE (`own`'s own label bounding was only
   ever exercised through `own_record`) and one a GENUINE REDUNDANCY that I
   removed rather than reported. Suite 304 -> 307, `just gate` green from source
   and from the wheel. Wheelhouse arrangement untouched.
   Evidence: `evidence/cutA-traversal-state-2026-08-24.txt`.
4bo. [signed off 2026-08-24; advance to 4bc] Python Cut A is independently
   complete. The former traversal arguments are absent from both exported
   signatures, private helpers initialize at zero, the two negative-depth
   regressions remain green, and the package-wide declared-operand audit guards
   the underlying rule. Source and installed gates both pass 307/307 under the
   locked offline environment. Begin the separate SQLite control-store/journal
   slice in item 4bc. The local-wheelhouse repository-shape ruling remains
   pending and does not block that work. Review:
   `review-2026-08-24T10-28-27Z.md`; evidence:
   `evidence/signoff-cutA-traversal-state-2026-08-24.txt`.
4bc-done. [implementation cut B 2026-08-24; review next] The separate control
   store, its store-KIND marker, the manager's operation journal, transactional
   CAS, exact replay and collision, real-process races and restart. Ownership
   before adoption: a genuinely empty schema is initialized and anything else
   must carry this manager's marker or be refused with nothing changed. Presence
   is its own fact, so an exact retry of a null-returning operation replays
   rather than running again. The whole sealed refusal is stored, so a durable
   `policy.retention` replays as itself rather than as a rebuilt
   `refused.precondition`. Nothing is written -- WAL included -- until the store
   is proved ours. The store KIND is added beyond the port, because version 1 is
   true of the authority's store too and telling a caller the wrong VERSION when
   it is the wrong PRODUCT sends them to fix the wrong thing.
   TWO DEFECTS FOUND IN MY OWN CODE BY RUNNING IT: the journal row was never
   written on the success path, so effectively-once did the opposite of its name;
   and `executescript` commits before it runs, which would have ended the
   transaction the DDL must be atomic inside.
   Sixteen mutations, all witnessed. Three began as zeros with three different
   answers: a case that proved nothing (a leaked connection holds no lock, so it
   counts file descriptors now), my own ill-formed mutation, and a window four
   racing processes did not happen to land in -- now opened on purpose by a
   competing connection committing during the peek. The race also proves it
   raced, by pid. 27 regressions added, the suite is 307 -> 334, `just gate`
   green from source and from the wheel; the frozen Node oracle is untouched and
   still runnable.
   Evidence: `evidence/cutB-control-store-2026-08-24.txt`.
4bp. [approved 2026-08-24; supersedes the repository-local/offline-artifact
   clauses in 4bh, 4bi, 4bl, 4bm and 4bo] Keep `jsonschema==4.26.0`, its full
   Python 3.13 closure and exact hashes authoritative in
   `requirements.lock`, but remove `v12/python/wheelhouse/` and every
   downloaded wheel or source distribution from the repository deliverable.
   Normal setup creates a disposable venv and downloads only the locked,
   hash-verified artifacts from the configured package index. Retain the
   installed-layout gate against that constructed environment; repository-
   local `--no-index` installation is no longer a requirement. External
   caches, mirrors and certified artifact bundles remain deployment concerns.
   Ignore the exact generated-artifact directory `v12/python/wheelhouse/` in
   `.gitignore`; do not hide all `*.whl` files globally.
4bq. [changes requested 2026-08-24; Cut B review] Retain the 334 delivered
   methods and four additive regressions. Re-read empty/owned state after taking
   the initialization write lock so concurrent first openers either initialize
   or adopt the compatible winner; translate every incompatible `meta` shape to
   the closed integrity refusal without mutation; bind stored kind and signature
   as one collision identity on first record and replay; and enforce exactly one
   committed-result or refused-outcome shape in the journal schema. Implement
   approved item 4bp in the same correction: remove repository-local artifacts,
   retain the exact hash lock, and keep an installed-layout gate that downloads
   only matching artifacts into a disposable environment. Reviewed source is
   334/338 methods, reported as five failures and two errors. Review:
   `review-2026-08-24T10-42-01Z.md`; evidence:
   `evidence/review-cutB-control-store-2026-08-24.txt`.
4bc-corr. [cut B correction and item 4bp 2026-08-24; re-review next] Three P1
   and one P2 closed, all reproduced first, the reviewer's four methods
   retained. The instructive one: `transact` re-reads inside the lock and I had
   written the comment explaining why -- and `open` decided emptiness OUTSIDE
   the lock, so concurrent first openers resumed into the same CREATE TABLE. The
   same sentence, the same file, applied at one of two sites, and the first time
   I had already written the rule down in the module where I then failed to
   follow it. A NAME IS NOT PERMISSION: `meta(id INTEGER)` escaped as a raw
   SQLite error, and the two foreign shapes are now told apart because the
   second message is wrong about the first. TWO CALLER ACCOUNTS OF ONE FACT: the
   kind lives in the journal and inside the signature and neither was compared,
   so a retry with a different kind replayed the first success -- bound at the
   write AND compared at replay, because unreachable is not unnecessary. The
   journal row invariant is a CHECK now and the schema version went to 2 with
   it, since a store written under the weaker table cannot satisfy the rule this
   build enforces; the invariant caught two of my own fixtures.
   ITEM 4bp IMPLEMENTED: the wheelhouse is gone, the build downloads the locked
   closure under `--require-hashes`, and the wheelhouse case became
   `TheHashesAreTheArtifactsOwn` -- the mechanism superseded, the property kept.
   THE FIRST LOCKED DOWNLOAD WAS REFUSED, because pip and setuptools had been
   hashed from Debian's repackaged wheels and the index serves different bytes;
   both re-measured, and the refusal is the mechanism working.
   AND A DEFECT IN MY OWN GATE: the source stage resolves the AMBIENT
   jsonschema 4.19.2 while the lock pins 4.26.0, so a green source run had been
   proving the code against a version this distribution does not pin, quietly,
   for two rounds. The stage says which validator it resolved now, the
   pinned-version case reports rather than skipping invisibly, and a case
   asserts the gate includes the locked stage.
   Seventeen mutations, all witnessed. Six began as zeros: five missing cases,
   and one case that measured PROSE -- it searched the whole justfile for
   `--require-hashes`, which the comment above the command contains. 12
   regressions added, the suite is 334 -> 346.
   Evidence: `evidence/cutB-correction-and-4bp-2026-08-24.txt`.
4br. [changes requested 2026-08-24; Cut B correction re-review] Retain all 346
   delivered methods and the two additive reviewer methods. Make the supplied
   manager signature prove the exact boundary it claims: exact POD object,
   exactly `kind` and `operands`, and byte-for-byte canonical serialization,
   before any journal write. An indented equivalent, a missing operand member,
   or an extra member currently becomes a durable identity even though
   `manager_signature` cannot produce it. Correct the remaining active
   justfile/test prose that still describes the superseded offline wheelhouse
   mechanism. Reviewed source is 348 methods with three failures and one skip;
   all 345 others pass. The independent installed run was blocked before
   installation by restricted DNS; delivered evidence records 346/346 locked
   installed. Review: `review-2026-08-24T10-53-27Z.md`; evidence:
   `evidence/re-review-cutB-correction-2026-08-24.txt`.
4bc-sig. [cut B signature identity 2026-08-24; re-review next] One P1 and one
   P2 closed, both reproduced first, the reviewer's two methods retained.
   CHECKING THAT TWO ACCOUNTS AGREE IS NOT CHECKING THAT EITHER IS TRUE: the
   previous round bound the kind to the signature, which was the right fix for
   that finding and the wrong depth for the rule -- so an indented spelling, a
   document with no `operands` and one with an extra member were all accepted
   and journalled as durable identities `manager_signature` cannot produce.
   Equivalent operations could acquire different byte identities and data
   outside the operand set could enter replay identity. The signature is now
   owned as exact POD, required to carry exactly `kind` and `operands`, and
   compared BYTE FOR BYTE against the canonical serialization of that owned
   document, all before the journal transaction opens.
   The P2 was stale gate prose describing the mechanism item 4bp removed -- the
   second round running in which stale prose was the finding -- so the rule is
   CHECKED now: a removed mechanism may be mentioned only after a line marking
   the passage as history. The check's own first version scoped that marker to a
   PARAGRAPH and the live sentence shared a block with the historical note, so
   the escape hatch swallowed the drift it was written to catch; line-scoped now.
   `--no-index` is deliberately not on the removed list, because the second
   install uses it correctly and banning a word is not banning a mechanism.
   Seven mutations, four witnessed and three reported as measured equivalences
   with reasons. 3 regressions added, the suite is 346 -> 349.
   RAISED, NOT ACTED ON: the reviewer's independent `just build` could not reach
   the configured index, so their locked stage stopped before installing. That is
   the ruling working as written, and it changes who can run the full gate -- a
   managed turn without egress can prove the source stage and not the locked one.
   Recorded so the gap is not rediscovered.
   Evidence: `evidence/cutB-signature-identity-2026-08-24.txt`.
4bs. [changes requested 2026-08-24; signature correction re-review] Retain all
   349 delivered methods and the additive kind-boundary method. Validate the
   separate operation kind as exact, non-empty, encodable text before caller
   behavior, comparison, replay or SQL, and share that rule with
   `manager_signature` so the exported helper cannot manufacture an unusable
   identity. Null currently escapes as a raw NOT NULL fault; integer 7 commits
   after SQLite coerces it to text and then collides with its own exact retry;
   empty text commits; a behavior-bearing operand has its `__eq__` executed.
   Reviewed source is 350 methods, reported as three failures, one error and one
   environment-dependent skip; all 345 others pass. The signature-document and
   active-prose corrections are accepted. Independent locked installation was
   blocked before installation by restricted DNS; delivered evidence records
   349/349 locked. Review: `review-2026-08-24T11-02-11Z.md`; evidence:
   `evidence/re-review-cutB-signature-2026-08-24.txt`.
4bc-text. [cut B durable-text boundary 2026-08-24; re-review next] One P1
   closed, all four shapes reproduced first, the reviewer's method retained.
   THE THIRD THING: the previous rounds established that the two accounts of the
   kind AGREE and that the signature IS one this manager could produce, and
   neither establishes that the value entering a TEXT column is durable text.
   The integer case shows why -- `7` agreed with itself, produced a canonical
   signature, committed, and SQLite stored `"7"`, so the operation could never
   be replayed by the caller that created it. `durable_text` is that rule in one
   place, run BEFORE any comparison so a hostile operand is refused without its
   `__eq__` being invoked.
   AND IT APPLIES AT SIX SITES, NOT ONE. The review named the kind; a sweep found
   the same `UnicodeEncodeError` leaking from the operation identity, the settled
   instant, the sealed refusal text and BOTH READ PATHS. Sixth time this campaign
   and the second time in this cut, so the sweep is the fix. The exported
   `manager_signature` proves it too, because a helper that can build an identity
   the store must refuse invites the caller to discover the rule by hitting it.
   Two things my own cases taught me: the READS fault on an identity they are
   checking is absent, and the clock is proved at OPEN rather than at the
   transaction -- better than what I was testing for, so the case moved to where
   it happens. Nine mutations, eight witnessed; ONE EQUIVALENCE where I corrected
   the COMMENT rather than the code, because the rollback protects those writes
   and the ordering does not. 3 regressions added, the suite is 349 -> 352.
   Evidence: `evidence/cutB-durable-text-2026-08-24.txt`.
4bt. [changes requested 2026-08-24; durable-text correction re-review] Retain
   all 352 delivered methods and the conditional exported-boundary regression.
   The six SQL text paths and `manager_signature` are accepted. The shared
   `durable_text` implementation helper was newly exported with a caller-
   controlled `what` label that is rendered directly: a hostile label executes
   `__format__`, and a 100,000-character label produces a 100,061-character
   refusal. Prefer removing the helper from both `__all__` surfaces; if it is
   deliberately public, apply the existing bounded no-code label rule. The
   exact `.gitignore` boundary from item 4bp is independently accepted:
   `v12/python/wheelhouse/` alone is ignored, setup/lock files remain visible,
   and there is no global `*.whl` ignore. Reviewed source is 353 methods with
   one reviewer failure and one environment skip; all 352 delivered pass.
   Review: `review-2026-08-24T11-09-02Z.md`; evidence:
   `evidence/re-review-cutB-durable-text-2026-08-24.txt`.
4bc-label. [cut B exported-label boundary 2026-08-24; re-review next] One P1
   closed, both shapes reproduced first. THE DEFECT WAS THE EXPORT, NOT THE
   CODE: `_durable_text` was correct where it was called from, and adding one
   name to two `__all__` lists made its internal label a caller operand -- so a
   hostile label ran its `__format__` during a refusal and a 100,000-character
   one produced a 100,061-character message. A diagnostic label is this
   package's prose at an internal call site and caller input the moment the
   function is exported, and that distinction is invisible in the function body.
   The authority slice was corrected for ten such helpers and I recreated the
   class here by widening a surface no caller had asked for. The helper is
   private and unexported now, which is the review's preferred resolution.
   AND THE RULE IS MECHANICAL, because remembering it has now failed twice:
   `AnExportedLabelIsCallerInput` resolves every name in both packages' `__all__`
   and refuses any exported function that takes a label without bounding it. ITS
   FIRST RUN FOUND TWO MORE -- `validate_worker_control` and
   `validate_agent_session` were safe only because their callee bounds the label,
   which is a property holding where somebody looked; they bound their own now.
   Four mutations, all witnessed, plus the reviewer's conditional method firing
   on a re-export. One instrument error of mine: a blanket text rename broke the
   definition and 38 cases errored at once. 3 regressions added, the suite is
   352 -> 355.
   Evidence: `evidence/cutB-exported-label-2026-08-24.txt`.
4bu. [signed off 2026-08-24; advance to 4bd] Python Cut B is independently
   complete. The private durable-text rule is absent from both exported
   surfaces; the retained conditional regression and the non-vacuous
   cross-package exported-label audit pass. All earlier initialization,
   ownership, schema, transaction, collision/replay, canonical-signature,
   durable-refusal and SQL-text findings remain closed. The exact no-wheelhouse
   ignore boundary is accepted. Independent source is 355/355 with one explicit
   ambient-version skip; implementer evidence records 355/355 in the locked
   environment with none skipped. Begin offer/claim issue, settlement and
   recovery under item 4bd. Review: `review-2026-08-24T11-13-41Z.md`; evidence:
   `evidence/signoff-cutB-exported-label-2026-08-24.txt`.
4bd-done. [implementation cut C 2026-08-24; review next] The injected authority
   port, the offers table at schema version 3, and the whole offer/claim
   boundary: issue with every check before entropy, accept/decline with binding
   before secret and constant-time possession, the fixed derived claim
   operation id, submission through the bound session, observe-only settlement
   before the deadline, late recording of a commit the manager never saw, and
   asymmetric restart recovery.
   TWO DECISIONS MADE RATHER THAN INHERITED, both written into the code: the
   port names only the five session members cut C uses, because naming all
   thirty-two would be a capability nobody granted; and the authority's claim
   signature arrives BY INJECTION rather than by import, so the manager consumes
   the authority's own derivation without depending on its module graph.
   Item 4bd's own sentence is a case: no adapter write occurs while the claim
   outcome is ambiguous, so the `live` answer writes nothing and says so.
   A DEFECT MY OWN FIXTURE FOUND: the one-live-offer index escaped as a raw
   `sqlite3.IntegrityError`, and the case that should have caught it was mine,
   written as `assertRaises(Exception)` -- the weak assertion I have criticised
   in other people's cases. It names the closed pair now, and naming it is what
   found the defect.
   Twenty-eight mutations, twenty-six witnessed. Six began as zeros: three were
   my instrument (including a case that VARIED TWO THINGS, so it measured
   neither), and three were missing cases -- the concurrent commit marker, the
   authority in the signature, and the terminal CAS, which expiry makes
   reachable against an `accepted` row. Two equivalences reported with reasons.
   39 regressions added, the suite is 355 -> 393.
   AND THE OPERAND SWEEP CAUGHT ITS OWN PROXY: the rule that the declared list
   stay smaller than the surface was a stand-in for "the list must not become the
   answer", and cut C made it wrong rather than strict. The property is stated
   directly now -- no declared operand may be bookkeeping by nature, and none may
   be stale.
   Evidence: `evidence/cutC-offers-and-claims-2026-08-24.txt`.
4bv. [changes requested 2026-08-24; Cut C re-review next] Retain all 393
   delivered methods and the five additive review methods. Close four contract
   boundaries before signoff: validate all four injected session operations as
   callable at AuthorityPort construction; apply the accepted durable-text rule
   before SQL and exact instant grammar before time comparisons; refuse a
   nonpositive/non-exact-integer TTL before reads or entropy (or remove the
   caller operand); and make schema version 3's documented all-five-or-none
   acceptance invariant real across every state, with an explicit schema
   version transition. Independent source inventory is 398 methods plus one
   ambient-version skip: the five probes expose eight assertion failures and
   two raw UnicodeEncodeError results while all 393 delivered methods remain
   green. Review: `review-2026-08-24T11-29-52Z.md`; evidence:
   `evidence/review-cutC-offers-and-claims-2026-08-24.txt`.
4bd-corr. [cut C correction 2026-08-24; re-review next] Three P1 and one P2
   closed, all reproduced first, the reviewer's five methods retained.
   THE ONE THAT MATTERS MOST IS THE ONE I WROTE MYSELF: cut B established the
   shared durable-text rule and applied it at six sites, and cut C then declared
   a LOCAL weaker `_text` one file over -- accepting lone surrogates and treating
   any nonempty string as an instant. Seventh time this campaign a rule has been
   applied at one of N sites, and the first where the other site was mine and
   three days old. Both rules are imported now, so there is one of each. AND THE
   INSTANT IS A SECOND PROPERTY: encodable text keeps a value out of SQLite's
   way, and the frozen grammar keeps it out of a COMPARISON's way. The clock is
   held to both, because every deadline this manager compares derives from it.
   The port typed existence rather than callability, so a null `claim` was
   discovered as a raw `TypeError` after the claim identity had been frozen -- the
   one moment the manager cannot retreat from. A duration is an operand and is
   proved before the reads it precedes. And the offers CHECK named three fields
   while its comment said five and constrained only one state; the states divide
   cleanly now and the schema version went to 4 with the shape.
   Fifteen mutations, fourteen witnessed. Three zeros were missing cases -- a
   clock answering prose, the acceptance DEADLINE half of the invariant, and
   every earlier schema version rather than the first. THE FOURTH WAS A GENUINE
   REDUNDANCY, REMOVED RATHER THAN REPORTED: `type(x) is bool or type(x) is not
   int` cannot decide anything the second clause does not, because `type(True)`
   is `bool`. 7 regressions added, the suite is 393 -> 400.
   Evidence: `evidence/cutC-correction-2026-08-24.txt`.
4bw. [changes requested 2026-08-24; Cut C correction re-review] Retain the 400
   delivered methods, the five passing original reviewer methods and four new
   additive methods. The original callable, shared-instant, nonpositive-TTL and
   schema-v4 corrections are accepted. Complete the durable-text sweep at six
   remaining sites: offer-id lookup shared by submit/settle, expiry's optional
   Work filter, both profile-certification key parts, and the injected claim-
   signature answer before acceptance writes. Also prove that a positive exact
   TTL and clock-plus-duration fit the frozen deadline domain before authority
   reads or entropy; `10 ** 100` currently escapes as `OverflowError` after the
   reads. Full source is 404 methods with two failures, five raw errors and one
   ambient-version skip; the four new methods account for every nonpassing
   result. Review: `review-2026-08-24T11-38-34Z.md`; evidence:
   `evidence/re-review-cutC-correction-2026-08-24.txt`.
4bd-sweep. [cut C derived sweep 2026-08-24; re-review next] Two P1 closed, the
   reviewer's four methods retained. THE FINDING BEHIND BOTH FINDINGS IS MY
   EVIDENCE: last round I wrote that I had swept every SQL and time boundary,
   and I had PROBED THE ENTRY POINTS I COULD THINK OF. The review enumerated the
   code and found six more -- two claim paths looking offers up by unproved
   identity, an optional Work filter, both certification key parts, and the
   injected signature's ANSWER. Cut B's sweep was real because it walked the
   AST; cut C's was recall wearing a sweep's clothes, and the two read the same
   in the evidence. Probing measures imagination; enumeration measures the code.
   Fixed at the OWNING boundaries as the review specifies: the lookup proves its
   identity in `_offer_row` rather than at each caller, the optional filter is
   proved, both certification key parts are proved because canonicalizability is
   not durable text, and the injected derivation's answer is proved because a
   capability is trusted to be the authority's and not to be correct.
   REPRESENTABILITY IS A THIRD PROPERTY after integer and positive, and it
   belongs to the SUM; the deadline is computed before the authority is read at
   all now, which makes "before reads or entropy" true rather than nearly true.
   AND THE SWEEP IS DERIVED: every exported callable must appear in a table with
   one valid call and its text operands, each is driven with a lone surrogate,
   and a completeness case asserts the table names every exported callable -- so
   adding one without adding a row fails the gate. Seven mutations, six
   witnessed; one equivalence where the comment now claims the smaller true
   thing. 7 regressions added, the suite is 400 -> 407.
   Evidence: `evidence/cutC-derived-sweep-2026-08-24.txt`.
4by. [anti-loop redesign required 2026-08-24; Cut D stays unstarted] Retain the
   407 delivered methods, all nine passing prior reviewer methods and two new
   additive methods. The six durable-text corrections and positive-duration
   overflow correction are accepted, but the confirmed 4bx anti-loop condition
   is met: calendar-impossible fixed-width text survives outside the claimed
   inventory, escaping as raw ValueError during arithmetic and silently
   expiring a live offer during comparison; the sweep's settlement-clock row is
   also vacuous because absent `offer-1` refuses before spoiled `now` is read.
   Return the CENTRALIZED BOUNDARY LAYER for explicit redesign, not another
   named-site patch. Derive a complete inventory of every public operation and
   caller text, SQL identity, injected/callback result, instant and deadline
   boundary from the code, and make every probe establish valid preconditions
   and prove it reached its named boundary. Full source is 409 methods with one
   failure, one raw error and one ambient-version skip; the two new methods
   account for both nonpassing results. Reviews:
   `review-2026-08-24T11-45-39Z.md` and
   `review-2026-08-24T11-46-38Z.md`; evidence:
   `evidence/re-review-cutC-derived-sweep-2026-08-24.txt`.
4bx. [confirmed anti-loop gate 2026-08-24; applies to the next Cut C re-review]
   Verify the correction's code-derived, non-vacuous inventory of every public
   operation and its text, injected-result, SQL and deadline boundaries. Do not
   sign off from the nine retained witness methods alone. If another instance
   of the same durable-text, instant, deadline-representability or persistent-
   identity class survives outside that inventory, stop the correction loop,
   keep Cut D unstarted and return the centralized boundary layer for explicit
   redesign rather than requesting another named-site patch.
4bz. [confirmed centralized-boundary rule 2026-08-24; governs 4by redesign]
   Validate exactly once on entry to each receiving trust domain. Treat caller
   values, adopted persistent data and injected/callback/adapter/agent results
   as receiver input; own them before trusted processing or effects. Do not
   revalidate ordinary internal returns after admission. Emit outbound contract
   documents only through closed canonical constructors, leaving the next
   receiver to own them at its boundary. Make the Cut C inventory name each
   trust-domain entry and owning validator rather than every downstream use.
4by-done. [centralized boundary layer 2026-08-24; re-review as one unit] The
   anti-loop gate answered with a redesign rather than another named-site patch.
   WHY THE LOOP HAPPENED: my inventory came from recall and my probes proved
   that a refusal happened rather than WHICH boundary refused. Both halves are
   mechanical now.
   `boundaries.py` owns five kinds -- text, identity, instant, deadline, injected
   -- and every refusal NAMES ITS BOUNDARY, which is what makes vacuity
   detectable. An instant is THREE properties: fixed-width digits do not
   establish a calendar, and the calendar does not establish the grammar --
   `2026-8-24T0:0:0.1Z` is a real moment that parses cleanly and SORTS WRONG.
   THE INVENTORY IS DERIVED: an AST walk collects every boundary call and
   attributes it transitively to every exported operation that can reach it --
   ten operations, twenty-eight boundaries, none listed by hand, and a call with
   no literal label RAISES rather than being skipped. It found two things on its
   first run: a hand-written copy of the text rule beside the layer, and a loop
   that hid seven labels from any walk. Both corrected, the loop unrolled,
   because a rule that is applied and cannot be SEEN to be applied is a rule the
   next reviewer takes on trust.
   EVERY PROBE PROVES IT ARRIVED by asserting the exact label, with real
   preconditions; the vacuity guard is itself proved by driving the review's own
   vacuous shape. Five boundaries no caller can reach are declared WITH REASONS
   and each claim is checked by spoiling the operand that would reach it and
   requiring the earlier boundary to refuse first.
   Twelve mutations, all witnessed, three of them the machinery checking itself.
   One began as a zero and produced the padding finding. 10 regressions added,
   the suite is 407 -> 417. CUT D REMAINS UNSTARTED.
   Evidence: `evidence/cutC-boundary-layer-2026-08-24.txt`.
4ca. [anti-loop redesign still required 2026-08-24; Cut D stays unstarted]
   Retain the 417 delivered methods, all eleven passing prior reviewer methods
   and six new additive methods. The calendar-instant correction and exact-
   label vacuity mechanism are accepted. The inventory is not PLAN 4bz's trust-
   entry inventory: it derives existing validator calls, drops exports with no
   reached call, collapses class methods and repeated `(kind, label)` call
   sites, and checks only a global union. AuthorityPort, claim_operation_id and
   revive_refusal are absent while the gate stays green. Derive public caller,
   persistent-adoption and injected/callback RESULT entries independently of
   validators, key each by owning entry/call site, and require one owner plus a
   non-vacuous probe. The missing universe is live: malformed adopted result and
   refusal rows escape as JSONDecodeError/KeyError; integer project_work faults;
   integer claim is recorded and advances state; integer settlement is silently
   treated as live. Do not patch those six witnesses locally -- correct the
   centralized model and closed document owners. Full source is 423 methods
   with three failures, three raw errors and one ambient-version skip. Review:
   `review-2026-08-24T11-58-38Z.md`; evidence:
   `evidence/review-cutC-central-boundary-layer-2026-08-24.txt`.
4cb-done. [trust domains delivered 2026-08-24; outbound constructors still owed]
   The six live witnesses in 4ca all traced to the same thing: `caller` was the
   only receiving domain I had ever named, so I had been patching sites inside
   it while two whole domains crossed the boundary unowned. `boundaries.DOMAINS`
   is now caller / adopted / injected, with three new kinds to carry them --
   `document` (an exact fresh dict, optionally with exactly these members),
   `alternative` (a document that must be ONE OF a closed set, discriminated),
   `adopted` (persistent text decoded and owned, refusing rather than faulting).
   EVERY INJECTED ANSWER IS OWNED AT THE PORT rather than at its users:
   projection, slot holder, claim, settlement and signature. ADOPTED BYTES ARE
   OWNED AT THE DECODE, which is where the domain is crossed: `replay` and
   `revive_refusal`. That closes all six.
   THE OTHER HALF OF THE RULING IS DELETION, and the double validations were
   mine: `deadline` re-owned its from-instant AND its own answer, `accept_offer`
   owned an id twice, `issue_offer` re-owned a uuid the projection had owned.
   The from-instant one is the lesson: last round I documented it as an
   "unreachable entry with a reason", which sounded like rigour and was me
   writing up a double validation as a defended edge. A boundary no caller can
   drive is usually a boundary that should not be there.
   THE INVENTORY NOW FINDS AN UNOWNED ENTRY. Its universe came from the
   validators, so an entry with no validator was invisible by construction;
   entries are now read from the code independently -- 55 (52 caller, 2 adopted,
   1 injected) against 36 owned subjects, 25 stated pairings and 9 delegations.
   Putting the universe back on the validators fails 32 cases and failed none
   before.
   Ten mutations: eight witnessed; two began as zeros and were MISSING CASES of
   my recurring shape -- no test drove a non-text slot holder, and none supplied
   a settlement `kind` outside the four, which is the exact hazard the closed set
   exists for. One is a MEASURED EQUIVALENCE and is left as one: the
   owned-twice guard has nothing to catch today, so what is proved instead is
   that its counting would see a second claim.
   NOT DONE, AND OWED: 4bz's closed canonical constructors for outbound
   documents. Every operation still assembles its answer as an inline dict. I
   named this gap answering poke=4478 and name it again here rather than let
   "4bz addressed" stand for it.
   Suite 417 -> 425, all pass at source and in the locked build. CUT D REMAINS
   UNSTARTED. Evidence: `evidence/w4-trust-domains-4bz-2026-08-24.txt`.
4cc. [changes requested 2026-08-24; Cut D stays unstarted] Retain the 425
   delivered methods, all six passing prior reviewer methods and three new
   additive methods. The previous adopted journal and broad injected-result
   defects are accepted, but the centralized model is not complete. The
   adopted inventory still begins with existing `boundaries.adopted` calls, so
   an unowned SQLite offer row is invisible; a malformed persisted `settle_by`
   reaches comparison without refusal. `document` permits extra members and
   `alternative` validates only the discriminator vocabulary, so injected
   answers are not closed shapes: an extra Work member is accepted and a
   committed settlement without `result` advances the offer to claimed with a
   null assignment. Finally, the probe gate remains keyed by global
   `(kind, label)` rather than requiring one reachable probe for every
   `(domain, lexical owner, entry)`. Correct the centralized trust-entry model,
   not the three witness sites, and complete 4bz's already acknowledged closed
   canonical outbound constructors before re-review. Full source is 428 methods
   with three failures and one ambient-version skip; the new methods account for
   every failure. Review: `review-2026-08-24T12-14-23Z.md`; evidence:
   `evidence/review-w4-trust-domains-4bz-2026-08-24.txt`.
4cd-done. [closed shapes, adopted rows, one probe per entry, outbound
   constructors 2026-08-24; re-review as one unit] The three P1s said one thing
   about last round: I corrected the INSTANCES a review demonstrated and left
   the MODEL able to produce more.
   ADOPTED ENTRIES NOW COME FROM THE SQL. The universe is discovered by parsing
   the text each `execute` is handed and keeping every SELECT, keyed by the
   table -- a structure that exists whether or not anybody owned the result.
   Five crossings; `boundaries.row` owns a row's COLUMN SET as well as its
   values against a per-table contract that lives beside the DDL, because the
   CHECK binds what THIS build writes and an adopted row is one somebody else
   wrote. The three offers-table read sites became one. A new `json` column kind
   proves a persisted result decodes AT THE READ and returns the stored bytes,
   so `replay` no longer decodes through the layer -- that was the second
   validation of one crossing.
   `sqlite_master` is declared with a reason rather than owned: I wrote a
   `boundaries.text` there and could not drive it, which is the unreachable-
   boundary shape my own last round was corrected for.
   CLOSED MEANS CLOSED BOTH WAYS. `document` refuses a member its contract does
   not name; `alternative` takes a per-variant contract rather than a
   vocabulary, so `{"kind": "committed"}` no longer advances an offer to
   `claimed` with a null assignment. The projection contract is split into the
   five members the manager reads and the ten it knows the authority emits, and
   the split is checked against the AUTHORITY'S OWN SOURCE rather than against
   the fake.
   THE INVENTORY IS KEYED THE SAME WAY THREE TIMES: (domain, lexical site,
   subject), where the site is module, class and function. 58 entries (46
   caller, 7 injected, 5 adopted), 43 probes one per (entry, label), 28 stated
   owners each naming a witness test that must exist, 5 delegations whose label
   is read from the delegate's own code, 3 declared exceptions. Building it
   corrected two things I had written down wrong: replay's kind and signature
   are COMPARED against the journalled row rather than delegated to `_agreeing`,
   and a decline's reason rides the manager signature rather than reaching SQL
   unowned.
   THE OUTBOUND CONSTRUCTORS ARE DELIVERED. `documents.py`: one contract table,
   ten constructors, every operation answering through them. The reason is not
   tidiness -- `_settle_terminal` answers differently when its CAS loses and
   `_record_claim` is reached from four callers, so a document's shape was a
   property of the PATH, and one whose members depend on the branch that built
   it cannot be owned at the far end against anything.
   Sixteen mutations: fifteen witnessed. Five began as zeros; four were missing
   cases -- the column-set half of `row` (every probe corrupted a value), and
   three about outbound STABILITY rather than outbound refusal, since these
   answers are journalled and member order and omitted-versus-null are durable
   facts. The fifth was the projection contract, where the fake agreed with the
   contract and the authority had never been asked. One is a measured
   equivalence and stays one: every entry has a probe, so the assertion saying
   so has nothing to catch; that the pairing would NOTICE a missing probe is its
   own case.
   Suite 425 -> 455, all pass at source and in the locked build. CUT D REMAINS
   UNSTARTED. Nothing under 4bz is outstanding.
   Evidence: `evidence/w4-closed-shapes-and-outbound-2026-08-24.txt`.
4ce. [changes requested 2026-08-24; Cut D stays unstarted] Retain the 455
   delivered methods, the three passing PLAN 4cc reviewer regressions and six
   new additive methods. Exact member/variant sets, SQL-derived adopted rows and
   outbound constructor routing are accepted. The trust-entry universe is still
   incomplete: it omits variadic parameters, injected attribute values and the
   caller-supplied capability objects explicitly removed by `NOT_INPUTS`.
   Consequently an unencodable bound participant constructs, a non-callable
   bearer mint performs authority reads before raw TypeError, and nine public
   `**members` constructors are absent from the claimed every-parameter
   inventory. Exact POD/member sets also do not own semantic member contracts:
   integer projection authority_uuid is issued, a claim for another participant
   is recorded, and text generation escapes as sqlite3.IntegrityError after the
   claim. Finally, replay re-adopts a refusal already owned at `_operation_row`.
   Extend the one lexical universe/owner/probe key to every signature form,
   capability value and semantically consumed injected member; type capability
   operands at construction/entry; separate public refusal revival from the
   trusted already-owned replay decoder. Do not patch the six witnesses locally.
   Full source is 461 methods with 13 failure reports, two raw errors and one
   ambient-version skip; the six new methods account for every nonpassing
   result. Review: `review-2026-08-24T12-46-50Z.md`; evidence:
   `evidence/review-w4-closed-shapes-outbound-2026-08-24.txt`.
4cf-done. [every input form, semantic member contracts, split refusal revival
   2026-08-24; re-review as one unit] Last round made the universe structural
   for the domain a review had demonstrated; this one says the structure was
   still a SUBSET of the language. Ordinary parameters, capability calls and
   SELECTs are three of the forms a value arrives in, presented as all of them.
   AN EXCLUSION NOBODY CHECKS IS A HOLE WITH A COMMENT OVER IT. `NOT_INPUTS` is
   now {self, cls}: every signature form is read, a capability's bound VALUE is
   its own entry, and a capability OPERAND is an entry whose owner is named --
   `mint_bearer`, `action`, `clock` and `claim_signature` typed at their own
   sites by a new `capability` kind, `session` typed per operation at
   construction, `store` and `port` named to CONSTRUCTED_BY, which must point at
   a site that exists and owns something. `__init__` counts as public whatever
   its underscore, since a naming convention is not a trust boundary.
   A MEMBER SET IS NOT A FIELD CONTRACT. Exact POD is the safe representation of
   a document and says nothing about what its members mean: an integer
   authority_uuid was issued into an operation signature, a claim naming another
   participant was recorded, and a text generation reached an INTEGER column
   after the authority had already answered. Twelve injected member entries are
   now discovered structurally -- a member READ on a capability-origin value,
   followed one level into this module's helpers and keyed to the CROSSING --
   and each is owned: identities as identities, the generation as a whole number,
   and the two parts that are RELATIONSHIPS (whose participant, which Work)
   compared rather than shaped. `_assignment` owns the claim answer and a
   committed settlement's result, because they are one document arriving twice.
   REPLAY NO LONGER RE-ADOPTS ITS REFUSAL. The `json` column contract names the
   members it must decode to, so the sealed pair is owned once at the read;
   `_revived` constructs from an already-owned document and the public
   `revive_refusal` keeps its own boundary.
   THE MACHINERY CAUGHT TWO THINGS BEFORE A READER DID: a shared owner produced
   a label with no literal part and the inventory refused it (labels are now
   literal-or-template, and a probe asserts the FULL label so one aimed at the
   claim answer cannot be satisfied by the committed claim); and the generation
   range turned out to be already owned by the exact-POD rule one layer up -- a
   second owner for one property, unreachable, and deleted rather than
   documented, the third such this campaign.
   Inventory: 115 entries (83 caller, 27 injected, 5 adopted), 58 probes, 47
   stated owners each naming a witness that must exist, 5 delegations, 2
   constructor exceptions, 3 declared exceptions.
   Twenty mutations: eighteen witnessed; two missing cases (a generation past
   the frozen range, which produced the redundancy finding; a record beside a
   `live` settlement, the one path whose point is that the manager writes
   nothing); two measured equivalences left as ones, with their mechanisms
   proved separately.
   Suite 455 -> 473, all pass at source and in the locked build. CUT D REMAINS
   UNSTARTED. Evidence:
   `evidence/w4-input-forms-and-field-contracts-2026-08-24.txt`.
4cg. [changes requested 2026-08-24; Cut D stays unstarted] Retain the 473
   delivered methods and four new additive regressions. The 4cf input-form
   additions are accepted, but semantic field completeness is not: the shared
   assignment owner shapes `authority_uuid` without relating it to the
   authority frozen on the offer, so direct and late committed claims from a
   different authority are recorded. A retirement record's `reason` and
   `disposition` are present but not typed, and the inventory does not enumerate
   them after the boolean alias that consumes the record. An adopted sealed
   refusal likewise proves only its four member names; integer `category`
   passes the row contract and replay escapes as AssertionError. Extend the
   centralized universe to semantic nested fields and relationships in both
   injected and adopted domains, and give each one owner and one reachable
   probe. Correct `_assignment`, the retirement field contract and the sealed
   refusal's closed pair at their shared crossings; do not patch the four
   witnesses independently. The inventory's 51 methods remain green while full
   source is 477 methods with four failures and one ambient-version skip, which
   triggers the 4bx/4by anti-loop gate again. Review:
   `review-2026-08-24T13-14-01Z.md`; evidence:
   `evidence/review-w4-semantic-field-relations-2026-08-24.txt`.
4ch-done. [assignment relationships, adopted field contracts, one origin tracker
   2026-08-24; re-review as one unit] Two P1s, both instances of a sentence I
   had already written down.
   A FOUR-PART IDENTITY IS NOT OWNED IF ONE RELATIONSHIP IS ONLY SHAPED. I made
   `_assignment` compare the Work and the participant and typed the authority as
   durable text without relating it -- so a well-formed assignment from another
   authority entirely was accepted for this offer, advanced it to `claimed` and
   recorded the foreign generation. Three of the four parts are relationships;
   the authority now comes from the offer's own adopted row and is compared on
   both the direct and the late-commit path.
   A MEMBER SET IS NOT A FIELD CONTRACT, in the two places I had not applied it.
   A retirement's `reason` and `disposition` were checked for PRESENCE while the
   manager records one and BRANCHES on the other, so an integer reason was
   adopted as the terminal decision; both are text now. And `Column.members` was
   a tuple of NAMES, so a persisted refusal with an integer category passed the
   row and reached `ContractRefusal`, whose pairing check is an ASSERTION --
   replay escaped as AssertionError. A `refusal` column kind owns the whole seal
   at its one adopted crossing: the members, the §9 CLOSED PAIRING, the text
   message and the durable marker.
   THE UNIVERSE FOLLOWS A CROSSING WHEREVER IT IS SPELLED. The gap was in the
   ORIGIN TRACKING rather than in any owner: it stopped at a boolean default, at
   a helper's return and at a list of rows -- and there were TWO trackers that
   had drifted, so a crossing handed INTO a helper was followed and the same one
   handed back OUT was not. One `_source` now follows every shape, to a
   fixpoint. Adopted origins name the READ as well as the table (`meta` is read
   at two places), and a column that is read is its own entry with its own
   probe: 29 adopted entries where there were 5.
   AND THE CIRCULARITY THAT CREATED. Generating the column probes from the
   universe means both shrink together if the tracking breaks -- this campaign's
   own finding, arriving inside my fix. So a SECOND mechanism, using none of the
   tracking, scans for column-named member reads and is compared against it;
   three mutations are caught by that and by nothing else.
   Inventory: 143 entries (85 caller, 29 injected, 29 adopted), 84 probes, 49
   stated owners each naming a witness that must exist, 5 delegations, 2
   constructor exceptions, 3 declared exceptions.
   Sixteen mutations, ALL WITNESSED; six began as zeros. Three were one missing
   case -- every sealed-refusal case I had written spoiled the CATEGORY, so the
   pairing, the message rule and the durable marker had never been driven, which
   is testing the first field of four and calling it the contract.
   Suite 473 -> 480, all pass at source and in the locked build. CUT D REMAINS
   UNSTARTED. Evidence:
   `evidence/w4-relationships-and-adopted-fields-2026-08-24.txt`.
4ci. [changes requested 2026-08-24; Cut D stays unstarted] Retain the 480
   delivered methods, the four passing PLAN 4cg reviewer regressions and three
   new additive methods. Assignment authority and retirement fields are
   accepted. The new adopted seal owner is not closed: it consults exported
   mutable `ERROR_CODES`, so a caller can widen the readable vocabulary, let an
   invented persisted pair pass the row contract, and reach `_revived` as an
   AssertionError. It also performs mapping membership before typing category,
   so a list category escapes as TypeError. Public `revive_refusal` still owns
   only the four member names: malformed category/pair escape, integer message
   is accepted, and false durable is rewritten true. The inventory exposes only
   the caller entry `sealed`, not its four semantic fields, and remains 54/54
   green while full source is 483 methods with four subtest failures, two raw
   errors and one ambient-version skip. Give the seal one authoritative closed
   semantic owner, independent of the mutable readable vocabulary, and extend
   the centralized universe to semantic fields of caller-supplied structured
   values. Apply it once at public revival and once at adopted replay; preserve
   the trusted `_revived` constructor. Review:
   `review-2026-08-24T13-34-30Z.md`; evidence:
   `evidence/review-w4-sealed-refusal-owners-2026-08-24.txt`.
4cj-done. [one authoritative seal owner, caller-domain semantic fields
   2026-08-24; re-review as one unit] Two P1s, and both are the same mistake in
   different clothes.
   A CLOSED PAIR CANNOT BE OWNED BY A VALUE CALLERS CAN WIDEN. I closed the
   adopted refusal's pairing against `ERROR_CODES`, which is the READABLE
   vocabulary and an ordinary mutable dict the contracts layer keeps
   deliberately non-authoritative -- its own case proves a caller may append to
   it without opening the frozen pairing. So that boundary was closed against
   something widenable while `ContractRefusal` stayed shut, and the disagreement
   surfaced as an AssertionError to a caller replaying its first answer. I used
   the public name because it was public; what I needed was the AUTHORITY, and
   the two are not the same thing. `contracts.errors.is_closed_pair` is now that
   shared question over the private frozen pairing, and it TYPES BEFORE IT
   PLACES -- `x in mapping` on a list raises rather than answering, so a list
   category had been escaping as TypeError from the boundary meant to own it.
   TWO DOORS INTO ONE DOCUMENT, AND I FITTED A LOCK TO ONE. 4cf split public
   revival from trusted replay correctly; 4ch gave the ADOPTED half a field
   contract and left the PUBLIC half checking four member names. This campaign's
   defect class arriving inside the correction for it. One `boundaries.sealed`
   now owns the members, the pairing, the message and the durable marker, and
   both doors call it.
   CALLER-DOMAIN SEMANTIC FIELDS ARE ENTRIES. The inventory held
   ('caller', 'store.py:revive_refusal', 'sealed') and nothing about its members
   -- injected documents had member entries and adopted rows had column entries
   because a parameter was not an ORIGIN. It is now, so one rule finds
   `sealed.category`, `claim.generation` and `operations.refusal` alike. Three
   domains, no domain-specific exception, which is what the last four reviews
   have each been about. `sealed.durable` is deliberately NOT an entry: nothing
   outside the layer reads it, and inventing a read to make an entry appear
   would be the decoration this file exists to stop.
   Inventory: 148 entries (90 caller, 29 injected, 29 adopted), 87 probes, 51
   stated owners each naming a witness that must exist, 5 delegations, 2
   constructor exceptions, 3 declared exceptions.
   Ten mutations, ALL WITNESSED, no zeros. G1 has a single witness -- the
   reviewer's own, which widens ERROR_CODES and requires the boundary to stay
   shut -- and that is the honest shape: there is one way to observe "this does
   not consult the widenable value".
   Suite 480 -> 483, all pass at source and in the locked build. CUT D REMAINS
   UNSTARTED. Evidence:
   `evidence/w4-one-seal-owner-and-caller-fields-2026-08-24.txt`.
4ck. [independent review signoff 2026-08-24; Cut D may begin] PLAN 4cj is
   accepted. The three PLAN 4ci reviewer methods pass; the shared seal owner
   types before consulting the private frozen pairing, remains closed when the
   readable vocabulary is widened, and is used once by both public revival and
   adopted replay. Caller parameters now seed semantic member discovery, and
   the public seal's category, code and message have distinct entries and
   probes; durable is consumed and tested inside the shared owner without a
   decorative downstream read. Focused seal plus inventory: 57/57. Full source:
   483/483 with one retained ambient-version skip. The independent locked gate
   passed its source stage but could not fetch `jsonschema==4.26.0` because the
   configured index was unreachable by DNS; no offline wheelhouse or authorized
   alternate path exists, so the review records that operational limitation
   rather than claiming a locked pass. Implementer evidence records 483/483 in
   its locked environment. Review: `review-2026-08-24T13-47-05Z.md`; evidence:
   `evidence/signoff-w4-one-seal-owner-2026-08-24.txt`.
4cl-done. [Cut D first slice 2026-08-24; runtime start and cancellation next]
   PLAN 4be covers attempt axes, activation, cancellation ordering, output
   freeze, intake and cleanup. This delivers the first three, in the order the
   frozen host slices ITSELF: `record_attempt` under an identity that signs all
   eight durable operands, `activate_assignment` binding the attempt to THIS
   attempt's own committed claim through the participant-bound session, and
   `observe` moving per-axis transitions inside one savepoint against the exact
   value the update compares, journalled by SOURCE IDENTITY.
   ABSENT RATHER THAN STUBBED and named in the module's own docstring: runtime
   start, reconciliation and cancellation ordering -- which introduce the
   injected runtime adapter and agent boundaries -- then output, intake and
   cleanup. The oracle carries the same sentence for the same reason: what a
   conforming adapter must BE is a later item's, and until then positive absence
   cannot be proven.
   Schema 5: `attempts` with an all-four-or-none assignment CHECK and ten axis
   columns, `observations` keyed by (attempt, incarnation, source_seq), and one
   claimed offer per attempt. THE VOCABULARY AND THE TRANSITIONS ARE DIFFERENT
   THINGS -- the CHECKs say what an axis may SAY, the frozen map says what may
   FOLLOW what -- and a case asserts the two agree.
   THE INVENTORY IS NOW LOAD-BEARING, and writing a new module against it was
   the first real test of that. It caught three things before any reader: a
   shared owner whose label had no literal in it (the second time this
   campaign); a blanket rename that ate its own definition, which is the exact
   defect I recorded three cuts ago; and two unreachable owners over
   `COALESCE(MAX(x), 0) + 1`, deleted rather than documented. The universe grew
   148 -> 194 with no hand-written addition to the discovery.
   Eighteen mutations, sixteen witnessed. Two zeros were missing cases of ONE
   shape -- a guard one process cannot reach alone -- now driven the way they
   happen: a store written before the unique index, and a trigger another build
   could have put on the observations table.
   H14 IS A MEASURED EQUIVALENCE AND THE MEASUREMENT IS THE FINDING: activation's
   compare-and-swap does not refuse a racing second manager, because both derive
   the SAME operation identity and the journal replays the first answer before
   the second act runs. I KEPT THE SWAP and flag it as a judgement call --
   unlike the five unreachable VALIDATIONS this campaign has made me delete, it
   is the write's own condition rather than a duplicate check.
   AN INSTRUMENT FAILURE IS RECORDED: the first mutation run hit an execution
   cap and was killed between writing a mutant and restoring it, leaving the
   tree mutated and the next baseline dirty -- a fourth shape after the false
   zero, the false non-zero and the stale bytecode. The restore is in a
   `finally` now and the discarded results are not reported.
   Suite 483 -> 514, all pass at source and in the locked build. Evidence:
   `evidence/w4-cut-d-attempt-axes-2026-08-24.txt`.
4cm. [changes requested 2026-08-24; next Cut D slice stays unstarted] Retain
   all 514 delivered methods and three additive reviewer regressions. The
   attempt record, three-way assignment agreement, frozen per-axis transitions,
   source-first observation replay and savepoint rollback are accepted. Keep
   activation's defensive compare-and-swap; H14 may remain a measured
   equivalence through today's one public operation identity.
   Three P1 boundaries remain. An identical activation beginning after the
   first commit returns from the fixed-row shortcut before the journal and
   synthesizes `already_fixed=True`, while the committed and racing-replay
   answer is `False`; one operation therefore has timing-dependent results.
   Observation's axis and value membership checks run before typing and lists
   escape as raw TypeError. A stale multi-manager savepoint raises raw
   `sqlite3.OperationalError: database is locked` because the Python port
   omitted the frozen host's result-code-based, contention-only translation.
   Correct the shared retry, vocabulary and contention boundaries; preserve raw
   non-contention storage faults. Full source is 517 methods with two failures,
   two subtest errors and one retained skip, all in the new witnesses; every
   delivered method passes. Review: `review-2026-08-24T15-19-08Z.md`; evidence:
   `evidence/review-cut-d-attempt-axes-2026-08-24.txt`.
4cn-done. [Cut D first slice corrected 2026-08-24; re-review before the next
   slice] Three P1s, and each is a rule this dossier already contains that I did
   not carry into the new module. Worth stating: the boundary model is
   mechanical now and catches a missing OWNER, but it does not catch a rule I
   know and did not apply.
   THE JOURNAL ANSWERS FIRST. `activate_assignment` returned from its
   already-fixed branch before reaching the journal, so the first call committed
   `already_fixed=False`, a later exact retry synthesized `True` from the row,
   and a contender that read before the commit replayed the journalled `False`
   -- one act, two answers, chosen by arrival time. The signature is derived
   before the branch and `store.replay` answers first. The ORDER is deliberate:
   the fixed-assignment MISMATCH is decided first (a precondition about the
   attempt, refused with what actually differs rather than as an operation
   collision), then the journal with full-signature collision intact, then the
   already-fixed fallback -- which now means what it always should have, an
   attempt found fixed with no act of this build's to reproduce.
   A CLOSED SET TYPES BEFORE IT ASKS. `axis not in TRANSITIONS` and
   `value not in moves` were asked of the raw operand, so a list escaped both as
   a raw TypeError while the inventory declared them owned. This is the same
   defect PLAN 4cj corrected for the sealed pairing ONE ROUND EARLIER, in code I
   wrote after that correction.
   ONLY CONTENTION IS TRANSLATED, by SQLite's own RESULT CODE and never by
   prose, with the primary code masked out of the extended one. A locked
   database at this boundary means one thing -- another writer is deciding this
   attempt -- and a constraint, a disk fault or a schema failure keeps its own
   identity, because a caller told to retry a constraint violation retries it
   forever.
   Nine mutations, ALL WITNESSED. J8 began as a zero and was a missing case of a
   shape the frozen host had already recorded as its own P2: every failure I had
   driven differed in code AND in wording, so matching on prose passed
   everything. The witness is a trigger raising `busy provider invariant:
   database is locked by policy`.
   THE REVIEW RULED ON MY QUESTION and the activation compare-and-swap stays:
   H14 is a legitimate measured equivalence through today's single public
   operation identity, and that does not make the write's own condition
   redundant.
   Suite 514 -> 518, all pass at source and in the locked build. Runtime start,
   reconciliation and cancellation remain unstarted. Evidence:
   `evidence/w4-cut-d-replay-types-and-contention-2026-08-24.txt`.
4co. [independent review signoff 2026-08-24; next Cut D slice may begin] PLAN
   4cn is accepted with no remaining correction finding. Exact activation
   replay consults the byte-stable journal before the no-journal fixed-row
   fallback; a four-part mismatch retains its specific precondition diagnostic,
   full signatures remain compared, and the defensive compare-and-swap stays.
   Axis and value type before membership. Observation contention is classified
   only from SQLite's BUSY/LOCKED primary result codes, with extended codes
   masked; a constraint whose application prose says busy and database is
   locked keeps its own identity. Full source: 518/518 with one retained skip.
   The independent locked gate repeated the green source stage but could not
   fetch `jsonschema==4.26.0` because the configured index was unreachable by
   DNS; implementer evidence records the locked pass. Review:
   `review-2026-08-24T15-48-04Z.md`; evidence:
   `evidence/signoff-cut-d-replay-types-contention-2026-08-24.txt`.
4cp-done. [Cut D second slice 2026-08-24; output, intake and cleanup remain]
   The rest of the frozen `attempts.mjs`, and the ordering IS the content.
   `request_runtime_start` commits a fully signed operation and hands its
   identity to the adapter, so the adapter and a restart settle the same act.
   `reconcile_runtime` decides by IDENTITY and by the FULL labels, and mismatch
   or multiplicity CANCELS rather than starting another -- with the minted
   runtime checked BEFORE the filter, because one carrying another assignment's
   labels is not absent, it is wrong, and this call caused it.
   `request_cancellation` fences at the authority FIRST, then orders the agent
   and then the runtime, and never claims either happened.
   Two injected capabilities enter: the runtime adapter and the provider agent.
   POSITIVE RUNTIME ABSENCE still cannot be proven -- it needs certified adapter
   evidence a later item defines -- so the retry path stays closed and says so,
   and this takes no `absence_proven` operand.
   TWO DELIBERATE DEPARTURES FROM THE ORACLE, both reported: the cancellation
   answer is NESTED rather than merged, because a document whose member set
   depends on the branch that built it cannot be owned at the far end; and the
   lost-race catch is NARROWED to the compare-and-swap's own refusal, because
   the oracle's broad catch swallows an operation COLLISION and answers it as a
   cancellation.
   THE INVENTORY FOUND A MODELLING GAP: `cancel` exists on the authority session
   AND on the provider agent, so a member name alone stopped identifying a
   crossing. For those capabilities the holder's name is now part of the
   member's identity. The adapter's start answer and every listed runtime are
   owned at the crossing because the manager COMPARES their ids and labels; the
   two settlements are stated with the pinned reason, since they are forwarded
   uninterpreted. Three derived identities are private, for the reason
   `_fixed_assignment` is.
   241 entries (152 caller, 52 injected, 37 adopted), 141 probes, 79 stated
   owners each naming a witness that must exist, 17 delegations, 2 declared
   unprobed entries checked to be owned.
   Seventeen mutations, fifteen witnessed. K6 WAS A REDUNDANT CHECK AND IS GONE:
   an early mismatch test in `_attach` changed no verdict, because the
   compare-and-swap refuses that case and the lost path answers the same from a
   FRESHER read -- the sixth duplicate of a write's own condition removed. K17
   is a measured equivalence whose value is that it makes K7 OBSERVABLE: the
   narrowed catch has nothing to catch today, and K7 measures zero under the
   oracle's broad catch and one under the narrow one.
   Suite 518 -> 541, all pass at source and in the locked build. Output freeze,
   intake and cleanup remain unstarted. Evidence:
   `evidence/w4-cut-d-runtime-and-cancellation-2026-08-24.txt`.
4cq. [changes requested 2026-08-24; output, intake and cleanup stay unstarted]
   Retain all 541 delivered methods and two additive reviewer regressions. The
   second slice's start-before-adapter journal, full runtime labels, minted
   mismatch ordering, fixed attachment identity, fence-before-agent-before-
   runtime order, failure retention, nested answer and narrow race catch are
   accepted.
   Two P1 boundaries remain. `_attach` commits the runtime identity and journal
   result before its separate `observe(... running)` call. A fault in that gap
   followed by a store reopen replays `attached`, skips the action and strands
   the durable execution axis at `start-requested`. Make attachment, running
   observation and result one atomic act, or establish equivalent atomic replay
   repair. `AuthorityPort.cancel` relates authority, Work and participant in a
   returned fence assignment but only shapes generation; a fence for generation
   2 therefore authorizes both shutdown boundaries for an attempt fixed to
   generation 1. Relate all four returned assignment parts to the exact
   `expect` before anything below the fence runs.
   Full source is 543 methods with two failures and one retained skip, both
   failures in the new witnesses; all delivered methods pass. Re-review this
   correction as one unit before beginning output, intake or cleanup. Review:
   `review-2026-08-24T16-47-16Z.md`; evidence:
   `evidence/review-w4-runtime-cancellation-durability-2026-08-24.txt`.
4cr-done. [Cut D second slice corrected 2026-08-24; one test premise changed,
   reported for ruling] Two P1s.
   AN EFFECT OUTSIDE THE TRANSACTION IS NOT PART OF THE ACT. `_attach`
   committed the runtime identity and the operation result and THEN observed
   `running`, so a fault between them left a committed attachment whose exact
   retry replayed the recorded answer without running the action -- answering
   `attached` forever while the durable axis still said `start-requested`. The
   observation is inside the journalled transaction now, which is what the
   observation savepoint was built for.
   A CHANGE TO A RETAINED REVIEWER TEST, reported rather than made quietly: the
   review recommended exactly this remedy, and under it the crash in that test
   commits NOTHING -- so its two premise assertions describe a state the fix
   makes impossible. Those two lines now assert what atomicity produces (no
   attachment at all); everything after the store close/reopen is exactly as
   written, because that is the property the case exists for. If the review
   prefers the other offered remedy -- a committed attachment a later replay
   heals -- I will implement that instead; the choice is not mine to assume.
   A FENCE FOR ANOTHER GENERATION IS NOT THIS CANCELLATION. The port related the
   authority, the Work and the participant and left the GENERATION only
   shape-checked, so a fence of generation 2 was accepted for an attempt
   expecting generation 1 and both downstream boundaries were then ordered with
   no evidence that THIS attempt's generation had been fenced. All four members
   are compared against the exact expected assignment before either can run.
   Three mutations, all witnessed -- including one that relates three members
   and not the fourth, which is the finding's own shape.
   Suite 541 -> 543, all pass at source and in the locked build. Output freeze,
   intake and cleanup remain unstarted. Evidence:
   `evidence/w4-cut-d-atomic-attach-and-exact-fence-2026-08-24.txt`.
4cs. [independent correction signoff 2026-08-24; later Cut D slices may begin]
   PLAN 4cr is accepted. The running observation is inside the attachment's
   journalled transaction, and the retained fault/reopen witness proves the
   runtime id, observation and result are atomic. The two changed intermediate
   assertions are approved as the stronger remedy PLAN 4cq recommended. The
   reviewer renamed the test because its old “committed replay repairs” name
   described the alternative mechanism; no behavior changed.
   The returned fenced assignment is compared with the exact expected
   four-part assignment before either downstream cancellation boundary. A
   different generation refuses and orders nothing. Focused: 2/2. Full source:
   543/543 with one retained skip. The independent locked attempt reached the
   resolver but the configured index hostname was unavailable; implementer
   evidence records the locked pass. Output freeze, intake and cleanup may
   proceed. Review: `review-2026-08-24T17-06-21Z.md`; evidence:
   `evidence/signoff-w4-atomic-attach-exact-fence-2026-08-24.txt`.
4ct-done. [Cut D groundwork 2026-08-24; the output slice decomposes further
   than 4be reads] Revalidating the remaining work against the tree changed the
   plan, which is what the revalidation is for. Output freeze is not one
   transition: `output.mjs` depends on `manifests.mjs` for retention, on three
   tables this store does not have, and on `validateManifest` -- which in the
   frozen host is not a schema call but EIGHT distinct §12 rules over the
   document.
   So this round delivers the two rules that are about the DOCUMENT ALONE:
   `validate_fragment`, which reads the frozen worker-control schema at a
   DEFINITION rather than at the envelope, and `verify_manifest_digest`, §12's
   identity rule. NOT named `validate_manifest`, because delivering half a rule
   under the name of the whole is the floor-versus-contract mistake this dossier
   already carries. Still to come and named rather than implied: no durable
   secret, well-formed Work and assignment references, artifact locator URIs,
   content-manifest sorted-unique paths and totals, an input manifest's unique
   names and non-overlapping destinations; then retention, the outputs and
   artifacts tables, then freeze and record.
   TWO DECISIONS FOR THE REVIEWER. A definition is a NAME, never a subschema --
   the frozen host accepts an inline fragment and this does not, because a
   caller-supplied subschema is a program this boundary would compile and run,
   the same seam `validate_against`'s identity check closes, arriving as data.
   And the fragment subschema is {$schema, $id, $defs, $ref} and nothing else,
   because keeping the envelope's `oneOf` would make every fragment have to be
   an envelope to validate as itself. Each fragment validator is built from the
   same PRIVATE parse and joins the owned set.
   Eight mutations, seven witnessed. M4 began as a zero and the reason is worth
   keeping: my first case was a REFUSAL, which proves nothing, because a
   fragment held to the envelope is refused too and for a reason nobody reading
   the message would notice. The POSITIVE case is the one that says it. M5 is a
   real equivalence left as one -- once the declared digest is verified it
   equals the recomputed one, and what recomputation buys is PROVENANCE, which
   the frozen host says of its own equivalent line.
   AN INSTRUMENT NOTE: M5's first run reported a threaded store case as its only
   failure. Alone it passes three times, so that was TIMING NOISE rather than a
   witness -- a false non-zero, the second of that shape here, checked rather
   than banked.
   Suite 543 -> 555, all pass at source and in the locked build. Evidence:
   `evidence/w4-manifest-fragment-and-digest-2026-08-24.txt`.
4cu. [independent groundwork signoff 2026-08-24; remaining §12 may proceed]
   PLAN 4ct is accepted and both design questions are ruled. The public
   fragment boundary accepts a frozen `$defs` name, never caller-supplied schema
   data; every runnable validator remains package-built and identity-owned. A
   fragment validator carries exactly `$schema`, `$id`, `$defs` and its `$ref`,
   without the root envelope's `oneOf` or other root constraints.
   Definition type precedes membership, documents are exact-POD owned before
   validation, and digest identity is recomputed over every member except its
   own declaration. The canonical frozen input-manifest vector passes both
   helpers. This narrow decomposition is accepted because it does not claim the
   still-queued semantic rules. Focused: 22/22. Full source: 555/555 with one
   retained skip. The independent locked attempt reached resolution but the
   configured index hostname was unavailable; implementer evidence records the
   locked pass. Review: `review-2026-08-24T17-42-45Z.md`; evidence:
   `evidence/signoff-w4-manifest-fragment-digest-2026-08-24.txt`.
4cv-done. [§12 manifest semantics 2026-08-24; §13 and retention remain]
   `contracts/manifest.py` carries the rules that are about what a manifest
   MEANS: a Work id carrying its authority's prefix (§4 -- an id without it is a
   reference to somebody else's Work wearing this one's name); §12 rule 4's
   absolute, readable, query-free and fragment-free locators; §12 rule 6's
   bytewise-sorted-and-unique entries with the declared count, byte total and
   tree digest all recomputed; and the composite, which walks every artifact and
   content manifest AT ANY DEPTH and adds an input manifest's unique names,
   non-overlapping destinations and single object namespace.
   STILL NOT THE WHOLE §12 TRUST ENTRY, and named so: §13's durable-secret rule
   is absent because its second half needs a reference-counted live-bearer
   registry this distribution does not have, and shipping the member-NAME half
   under the whole rule's name is the floor-versus-contract mistake already
   recorded here. The composite is `check_manifest_structure` and becomes the
   entry when the secret rule lands beside it.
   TWO MORE UNREACHABLE BOUNDARIES DELETED, the seventh and eighth. Every path
   member of a manifest is typed `relativePath`, whose pattern already refuses
   what `check_relative_path` refuses; and `assignmentRef.generation` already
   carries `minimum: 1`. NEITHER RELIANCE IS IMPLICIT -- a case pins each of the
   schema's own guarantees, so if either stops the gate says so.
   Seventeen mutations, all witnessed. Five began as zeros and FOUR WERE ONE
   MISSING CASE WITH ONE CAUSE: every URI case I had written spoiled the same
   clause, so the fragment, the relative locator and the unreadable one were
   never driven. A rule with four clauses needs four cases; testing the first
   clause four times is not testing the rule. The fifth had a different cause --
   the published vector carries a DIRECTORY source, so the versioned-source
   branch had nothing to drive it, and the case now builds that source from the
   schema's own required members.
   THE VECTOR IS THE BASELINE: every case spoils exactly one thing in the
   conformance vector the worker-contract finding published and reseals it, so
   the identity rule does not refuse it before the rule under test is reached.
   ONE DECLARED WIDENING: `urllib` joins the manager's standard-library
   allowlist for §12 rule 4, because re-implementing a URI parser to avoid a
   standard-library import would be writing the thing the rule leans on. No
   runtime dependency is added.
   Suite 555 -> 567, all pass at source and in the locked build. Evidence:
   `evidence/w4-manifest-semantics-2026-08-24.txt`.
4cw. [changes requested 2026-08-24; §13 and retention stay unstarted]
   Retain all 567 delivered methods and four additive reviewer regressions. The
   semantic relationships, recursive walks, canonical-vector baselines,
   schema-first order and two schema-owned deletions are accepted.
   Two P1 boundaries remain. `urlsplit` is a permissive splitter, not the frozen
   host's strict URL constructor, and its discarded result means durable
   userinfo is never checked. Reject credential-bearing userinfo plus malformed
   authority/port forms the splitter accepts, while preserving the original-
   text query and fragment rules. `urllib` remains an accepted standard-library
   dependency.
   `check_work_ref` and `check_content_manifest` are explicitly exported but
   index unowned caller values, leaking TypeError/KeyError and executing hostile
   dict methods. Give each public function a schema-owning wrapper and call a
   private trusted semantic body from the composite so nested values are not
   validated twice.
   Full source is 571 methods with five failure reports, eight raw errors and
   one retained skip, all in the new witnesses; every delivered method passes.
   Re-review this correction before starting §13 or retention. Review:
   `review-2026-08-24T18-32-54Z.md`; evidence:
   `evidence/review-w4-manifest-semantics-boundaries-2026-08-24.txt`.
4cx-done. [URI parsing and exported owners 2026-08-24; §13 and retention next]
   Two P1s.
   CALLING A LENIENT PARSER AND DISCARDING ITS ANSWER IS NOT PARSING. `check_uri`
   ran `urlsplit` inside a try and threw the result away, so all it proved was
   that the splitter did not raise -- and `urlsplit` hands back a hostname
   containing a space, a port that is not a number, and userinfo without
   objecting. `worker:secret@host`, a credential in a durable locator and the
   exact thing §12 rule 4 exists to keep out, was accepted. The answer is read
   now: userinfo first, because a credential-bearing locator has a REASON and
   the reason is the part a reader acts on; then the authority against RFC
   3986's own alphabet; then the port, whose accessor is where `urlsplit`
   finally raises. `@` is in the alphabet deliberately -- the authority IS
   `[userinfo "@"] host [":" port]`, and leaving it out would refuse a
   credential-bearing locator for the wrong reason.
   AN EXPORTED RULE OWNS ITS OWN OPERAND. `check_work_ref` and
   `check_content_manifest` are public and indexed their arguments as though the
   composite had already schema-owned them, so a direct caller's malformed value
   escaped as TypeError or KeyError and a dict SUBCLASS executed hostile
   `__getitem__` inside the trusted layer. One public wrapper that validates the
   fragment, one private body the composite calls with values it already owns.
   Seven mutations, ALL WITNESSED; two began as zeros. P2 IS THE SAME SHAPE AS
   LAST ROUND'S URI ZEROS, ONE ROUND LATER: my case supplied both halves of the
   userinfo, so dropping the user-name half changed no verdict. Half a check
   passes a test written against the whole, and I have now made that mistake
   twice in one function.
   P7 IS STRUCTURAL and needed a structural check: putting the public wrapper
   back inside the composite validates one document twice, and both orders
   accept and refuse the same inputs, so no behavioural case can see it. The
   witness reads the composite's own AST -- the mechanism the manager's
   inventory uses one layer down. WORTH NAMING: 4bz's not-owned-twice rule has
   been enforced by that inventory since it was written, and the CONTRACTS
   package is not in it. This is the first double validation the inventory could
   not have caught, and a review caught it instead.
   Suite 567 -> 573, all pass at source and in the locked build. Evidence:
   `evidence/w4-uri-parsing-and-exported-owners-2026-08-24.txt`.
4cy. [one URI correction remains; contracts inventory ruled before §13]
   Accept the public schema-owning wrappers, private composite bodies,
   structural no-double-validation witness, userinfo coverage, authority
   alphabet and port checks from 4cx. Retain all 573 methods.
   One P1 parser disagreement remains: `check_uri("https://")` sees an empty
   `urlsplit` netloc and skips the authority checks, but the frozen JavaScript
   URL constructor refuses the same text. Refuse this parser-incomplete
   absolute locator and rerun source plus locked verification. §13 and
   retention remain unstarted until this correction is reviewed.
   Then add one separate contracts-package anti-loop inventory slice before
   §13. Derive its entries from the package's actual public exports, record the
   semantic owner and probe for each covered contract boundary, and pin the
   structural rule that an already-owned nested value reaches a private body
   rather than re-entering a public owning wrapper. The existing manager
   inventory excludes contracts and therefore could not prevent the boundary
   and double-validation defects found in 4cw. Do not fold this prevention
   slice into the URI correction.
   Current full source: 573 tests, one additive failure (`https://`) and one
   retained skip; every delivered test passes. Review:
   `review-2026-08-24T19-04-46Z.md`; evidence:
   `evidence/review-w4-uri-correction-2026-08-24.txt`.
4cz-done. [empty authority 2026-08-24; contracts inventory is the next slice]
   `check_uri` ran its authority and port rules only when the split found a
   NON-EMPTY netloc, so `https://` returned unexamined while the frozen host's
   constructor throws for it. The clause is guarded by the SCHEME now, not by
   the netloc.
   MEASURED RATHER THAN REASONED ABOUT. The obvious rule -- an empty authority
   is invalid -- is wrong, and I checked before writing it: the frozen
   constructor throws for `https://` and `http://` and accepts `file://`,
   `file:///x`, `artifact://`, `foo://`, `urn:x:y` and `mailto:a@b`. So the rule
   is that the schemes which REQUIRE a host must have one, and `_HOST_REQUIRED`
   is that measurement rather than a policy this build invented. `file://`
   staying valid matters: it is a form the contract uses, and a rule refusing
   every empty authority would have refused it while looking stricter.
   Three mutations, all witnessed. The one worth having is "every scheme
   requires a host" -- the rule I would have written without measuring -- and
   what catches it is the list of forms the frozen constructor accepts.
   THE REVIEW'S PREVENTION DECISION IS ACCEPTED AND QUEUED: a contracts-package
   anti-loop inventory as its own slice, derived from the package's real public
   export set, naming each semantic owner and probe and structurally pinning the
   private-body path, BEFORE §13. Retention, the outputs tables and freeze/record
   stay behind both.
   Suite 573 -> 574, all pass at source and in the locked build. Evidence:
   `evidence/w4-empty-authority-2026-08-24.txt`.
4da. [changes requested 2026-08-24; special-scheme parse parity remains]
   Accept the restored refusal of `https://`, `http://` and `ftp://` and the
   preserved acceptance of empty-authority opaque and `file` forms. Retain all
   574 delivered methods plus the two additive reviewer regressions.
   One P1 remains in the replacement rule. The frozen WHATWG constructor
   accepts `https:x`, `https:/x` and `https:///x`, assigning host `x`; Python's
   `urlsplit` reports an empty `netloc`, so `_HOST_REQUIRED` refuses all three.
   The corresponding `worker@example.test` forms are userinfo in the frozen
   parse and must still refuse for that reason. Do not remove the host-required
   guard and reopen `https://`; derive the host and userinfo decision from the
   frozen special-scheme behavior rather than directly from `urlsplit.netloc`.
   Full source is 576 methods with three errors, three failure reports and one
   retained skip, all in the additive witnesses; every delivered method
   passes. Re-review this correction before the separately ruled contracts-
   package anti-loop inventory. §13 and retention remain unstarted. Review:
   `review-2026-08-24T19-25-16Z.md`; evidence:
   `evidence/review-w4-special-scheme-host-2026-08-24.txt`.
4db-done. [one parser decides the host 2026-08-24; contracts inventory next]
   My last correction was half a correction: it asked `urlsplit` for `netloc`
   and then applied a measured scheme list, composing two facts from DIFFERENT
   PARSER MODELS. The frozen reader normalizes `https:x`, `https:/x` and
   `https:///x` to `https://x/` with host `x`; Python reports an empty netloc for
   each, so three accepted forms were refused as hostless -- and worse,
   `https:worker@example.test` carries a CREDENTIAL that the same disagreement
   hid behind a "no host" refusal. A remedy that merely accepted the shorthand
   forms would have reopened that boundary while looking like a fix.
   The authority of a host-requiring scheme is derived the way the frozen reader
   derives it: skip ANY NUMBER of `/` or `\` after `scheme:`, read to the next
   `/`, `\`, `?` or `#`, split userinfo at the LAST `@`. Everything else keeps
   the split's own answer, because `artifact:x`, `urn:x:y` and `mailto:a@b`
   carry no authority in either model. Every form is measured against the frozen
   constructor and the measurements are in the evidence.
   MY OWN MUTATION TESTING CORRECTED THE CODE, NOT THE TEST. I wrote the port
   split as "everything after the LAST colon"; a mutation to the first colon
   changed no verdict, so I measured both and found MY version wrong --
   `https://a:b:8080/x` throws at the frozen constructor and my rule accepted it
   with port 8080. THAT IS A FOURTH ANSWER for a zero-scoring mutation, beside
   missing case, redundant code and real equivalence: THE MUTANT IS RIGHT. It is
   the first time this campaign has produced one.
   Nine mutations, all witnessed; three began as zeros. R8 needed an IPv6
   literal WITHOUT a port, since with one both spellings agree, and R9 needed a
   userinfo case on a NON-special scheme, because every credential case I had
   written used a special one.
   Suite 574 -> 580, all pass at source and in the locked build. The
   contracts-package anti-loop inventory remains the next slice; §13 and
   retention stay behind it. Evidence:
   `evidence/w4-one-parser-decides-the-host-2026-08-24.txt`.
4dc. [changes requested 2026-08-24; pin the URI parser strategy first]
   Accept the shorthand-host and userinfo correction from 4db and retain all
   580 delivered methods plus two additive reviewer regressions.
   One P1 remains. `_whatwg_authority` derives a field boundary, `_AUTHORITY`
   checks a broad alphabet and `_check_authority` checks only whether a port is
   decimal. That is not the frozen constructor's host parse. It accepts ports
   above 65535, malformed bracket hosts, unmatched brackets and invalid percent
   escapes that the frozen reader refuses. It also rejects an empty port marker
   the frozen reader accepts and removes. Replacing `split.port` widened the
   ordinary non-special path as well as the new special-scheme path.
   This is the third correction on the same equivalence boundary. Before
   another implementation edit, pin one durable strategy in FINDING and this
   plan: either use a vetted WHATWG implementation for the frozen accepted
   surface, or explicitly narrow BOTH runtimes to one canonical URI subset and
   record the frozen-host supersession. Do not hand-copy another selected
   WHATWG clause and call it a parser. Preserve all earlier query, fragment,
   userinfo, malformed-authority and empty-host regressions.
   Current full source is 582 tests with six additive failure reports, three
   additive errors and one retained skip; all 580 delivered tests pass. Re-
   review the pinned strategy and correction before starting the contracts-
   package inventory. §13 and retention remain unstarted. Review:
   `review-2026-08-24T20-03-48Z.md`; evidence:
   `evidence/review-w4-derived-authority-is-not-a-parser-2026-08-24.txt`.
4dd. [confirmed 2026-08-24; implement and independently review]
   SUPERSEDES the 4d/4da/4db requirement to preserve the frozen constructor's
   complete WHATWG acceptance surface. Implement the smaller canonical URI
   grammar recorded in FINDING in BOTH retained runtimes from one shared vector
   corpus. Preserve the credential, query, fragment and malformed-authority
   refusals, but deliberately refuse special-scheme shorthand, opaque forms,
   empty non-file authorities and empty ports. Validate ports as 1..65535 and
   hosts according to the recorded DNS/IPv4/bracketed-IPv6 subset. Do not add a
   WHATWG dependency and do not copy more WHATWG productions. The bounded Node
   edit is an explicit exception to the no-new-Node-host-feature rule solely so
   the retained oracle enforces the superseding shared contract.
   Re-run the full source and locked Python gates plus the retained Node oracle,
   then obtain independent acceptance before starting the contracts-package
   inventory. §13 and retention remain behind that acceptance.
4dd. [decision requested 2026-08-24; NO implementation edit made] The review
   requires the URI parser-equivalence strategy pinned before the next edit, and
   I have made none. Source is red by the review's design: 582 with six failures
   and three errors, all of them its additive methods, and all 580 delivered
   tests pass.
   THE MEASUREMENT THAT DECIDES IT, and neither review has named it: the frozen
   constructor NORMALIZES. Ten of nineteen accepted forms come back as a
   DIFFERENT STRING -- uppercase hosts lowercased, non-ASCII punycoded,
   percent-escapes decoded, leading-zero ports trimmed, empty port markers
   dropped, and the one-, no- and three-slash shorthands rewritten. So "accept
   exactly what the frozen reader accepts" cannot be a rule over the ORIGINAL
   TEXT, and this module's own §12 rule 4 comment says the opposite about how
   these rules must work. A durable locator whose meaning depends on a
   normalizing parser is one two conforming readers can disagree about, which is
   the failure §3.3 exists to prevent.
   STRATEGY 1 (a vetted WHATWG parser in Python) needs WHATWG host parsing,
   percent-decoding, IDNA and port normalization -- `urllib` does none of them --
   so it means a SECOND runtime dependency, reopening 4bh's one-dependency
   ruling and 4bi's import allowlist. It cannot be verified here either: the
   index has been unreachable by DNS for several rounds, and I will not claim a
   package exists or resolves offline without measuring it. It would also keep
   the normalization property above.
   STRATEGY 2 (one smaller canonical grammar both runtimes enforce) is
   RECOMMENDED: lowercase scheme; opaque form or exactly two slashes; no
   userinfo in any form; host either a bracketed IPv6 literal or a lowercase
   ASCII registered name with no percent-encoding; port `[1-9][0-9]{0,4}` at
   most 65535 or absent; no query or fragment. Nothing in it needs
   normalization, so every rule is literally checkable in either runtime.
   IT SUPERSEDES: uppercase, non-ASCII and percent-encoded hosts; empty and
   leading-zero ports; underscore, doubled-dot and leading-hyphen names; AND the
   shorthand slash forms the last two reviews had me add. That last row is why
   this needs a recorded ruling rather than my judgement. Every retained
   regression is still refused by the grammar; the shorthand-acceptance methods
   are the only ones that would change, and they would change by ruling.
   The grammar's accepted and refused sets belong in the published vector file
   the manifest rules already drive from, so both runtimes are held to one list.
   Evidence: `evidence/w4-uri-strategy-decision-2026-08-24.txt`. The contracts
   inventory, §13 and retention stay unstarted behind this.
4de-done. [shared canonical locator grammar, both runtimes 2026-08-24]
   Implements the confirmed decision and the approver's follow-up: opaque forms
   excluded, the bounded Node edit and the superseded test migrations
   authorized.
   `v12/fixtures/uri-vectors.json` carries 20 accepted and 50 refused forms and
   is THE AUTHORITY FOR BOTH RUNTIMES -- not two implementations that agree
   today. `contracts/manifest.py` and `worker_manager/contracts.mjs` both
   enforce the grammar over the ORIGINAL TEXT, with no parse and no
   reconstruction anywhere in it, and both suites read the same corpus.
   The IPv6 literal is the one place a library decides -- `ipaddress` in Python,
   the constructor's own hostname round-trip in Node -- and both additionally
   require it to be lower case and to come back as the SAME TEXT, because an
   address that only becomes valid after normalization is not canonical.
   `urllib` LEAVES the Python allowlist and `ipaddress` joins it: the grammar
   needs no URI parser at all now, a smaller surface than the widening I asked
   for two rounds ago.
   EVERY SUPERSEDED ASSERTION IS NAMED in PROGRESS and in the evidence rather
   than deleted: four Python cases that required shorthand, empty port markers,
   empty authorities or opaque forms to be ACCEPTED; two that expected the
   shorthand credential forms to refuse with the userinfo reason rather than at
   canonical syntax; three changed expected phrases; and on the Node side two
   changed phrases plus one renamed case whose whole premise -- that opaque
   forms stay accepted because refusing a parse failure "costs the contract
   nothing" -- the ruling supersedes. Query, fragment, canonical userinfo,
   malformed authority, empty host and every port refusal are retained
   unchanged, and a case asserts the corpus still carries each.
   Python gate 574/574 at source and in the locked build; the Node locator cases
   and the new shared-vector case pass.
   AN OPERATIONAL FINDING, REPORTED RATHER THAN FIXED OR HIDDEN: the frozen
   prototype's Node suite has three PRE-EXISTING failures about refusal MESSAGE
   LENGTH -- one reports a 269,042-character refusal for a 20,000-member
   capability envelope -- none of which calls `validateUri`. My edit lost no
   export (39, none missing) and touched no shared helper. They are outside this
   boundary and outside W4's scope, so I have not changed them; silently
   repairing somebody else's failing gate would misreport what this round did.
   Evidence: `evidence/w4-canonical-locator-grammar-2026-08-24.txt`.
4df. [changes requested 2026-08-24; canonical IPv6 and DNS bounds]
   Accept the shared original-text grammar, vector ownership, authorized test
   migrations, dependency change and bounded Node correction from 4de. Retain
   its 574 delivered Python tests and the common corpus, now extended from 50 to
   54 refused forms.
   One P1 boundary has two remaining clauses. Python `_check_ipv6` must enforce
   the same canonical literal it claims: admit only the IPv6 character alphabet
   and require `str(IPv6Address(literal)) == literal`. This refuses leading-zero,
   uncompressed and scoped forms that Node already refuses. Both runtimes must
   also enforce that every DNS label is at most 63 ASCII bytes and the complete
   host is within the DNS textual bound; the current regex accepts a 64-byte
   label while calling it DNS.
   Full Python is 574 tests with four additive failures and one retained skip;
   all delivered tests pass. The focused Node contracts file is 56 pass and one
   additive failure; its three new IPv6 vectors pass. Re-run source, locked and
   focused Node verification, then obtain independent acceptance before the
   contracts-package inventory. §13 and retention remain unstarted. Review:
   `review-2026-08-24T21-42-03Z.md`; evidence:
   `evidence/review-w4-canonical-locator-ipv6-dns-2026-08-24.txt`.
4df-done. [canonical IPv6 text, DNS bounds, and the family with no agreed
   spelling 2026-08-24]
   Both P1s are implemented in both runtimes: the IPv6 literal is held to ONE
   CANONICAL TEXT (`str(IPv6Address(literal)) == literal` in Python, the
   constructor's own hostname round-trip in Node) over a literal alphabet that
   keeps scope ids away from the parser, and a DNS name is bounded to 63 bytes
   per label and 253 written, with 253 accepted and 254 refused in both.
   IMPLEMENTING P1a EXACTLY AS PRESCRIBED WOULD HAVE LEFT A DISAGREEMENT, and a
   differential sweep found it: the prescribed alphabet admits the dot, and for
   the IPv4-MAPPED range `::ffff:0:0/96` THE TWO LIBRARIES' CANONICAL SPELLINGS
   ARE EACH OTHER'S REFUSALS -- `ipaddress` writes `::ffff:1.2.3.4` and the
   frozen constructor writes `::ffff:102:304`, each rejecting the other's text.
   No spelling of a mapped address satisfies both, so a locator one runtime
   wrote would be unreadable to the other, which is the §3.3 failure the ruling
   exists to prevent. The family is EXCLUDED in both runtimes alongside
   shorthand and the opaque forms, and admitting it later is a versioned
   contract change. The alphabet is therefore `[0-9a-f:]` with no dot, which is
   a NARROWING of what the review prescribed and is named as such.
   The exclusion is the mapped RANGE and not everything shaped like it:
   `::ffff:1` is `0:0:0:0:0:0:ffff:1` and stays accepted.
   EVIDENCE THE CORPUS CANNOT GIVE: two differential sweeps, 1,532 general
   locators and 10,162 IPv6 spellings, ZERO disagreements between the runtimes;
   the same sweeps reported three before the exclusion, all of them the mapped
   family, which is how it was found.
   Mutation round over exactly this cut: 18 of 20 killed. THE TWO SURVIVORS ARE
   REPORTED: deleting or widening the Node alphabet clause survives, because
   that constructor already refuses everything the clause would catch -- probed
   over every ASCII character outside the alphabet in seventeen positions, with
   nothing round-tripped unchanged. The clause is KEPT and the distinction is
   the point: it is unreachable because of what a THIRD-PARTY NORMALIZER does in
   this runtime version, not by construction, and it is the only clause there
   that fixes the grammar without asking that normalizer. Its assumption is now
   pinned by its own case, so a runtime that starts round-tripping a scope id
   fails a test instead of widening a durable locator in silence.
   Two clauses DELETED as measured redundant: the lower-case check in both
   runtimes, which the alphabet already subsumes.
   Python gate 577/577 at source and in the locked build; Node `npm test` 691
   with the three pre-existing message-length failures unchanged and untouched.
   Evidence: `evidence/w4-locator-bounds-2026-08-24.txt`.
4dg. [technical correction passes; mapped-family ruling required 2026-08-24]
   Accept the canonical IPv6 text implementation and both DNS bounds. Focused
   Python is 10/10, the full Python source is 577/577 with one retained skip,
   and the focused Node contracts file is 60/60. The three unrelated Node
   message-length failures remain outside W4.
   One product decision remains before terminal signoff: confirm or reject the
   proposed exclusion of the complete IPv4-mapped IPv6 range. The confirmed
   grammar admitted bracketed IPv6 generally, while the implementation now
   refuses this family because Python and Node have no common same-text
   canonical spelling. If approved, pin the exclusion explicitly and close W4
   satisfying under umbrella PLAN item 20. If rejected, choose which shared
   spelling rule supersedes the same-text requirement before another edit.
   Do not start contracts inventory, §13 or retention in W4. Review:
   `review-2026-08-24T22-00-43Z.md`; evidence:
   `evidence/review-w4-locator-bounds-ruling-2026-08-24.txt`.
4dh. [signed off; W4 terminal 2026-08-24]
   Approver confirmed that the shared canonical locator grammar excludes the
   complete IPv4-mapped IPv6 range. This preserves cross-runtime same-text
   canonicality; any later admission is a versioned grammar change.
   Independent verification remains 577/577 Python with one retained skip,
   60/60 focused Node contracts, and a shared corpus of 20 accepted and 58
   refused locators. The three unrelated Node message-length failures remain
   outside W4 under W1593/W2929. Close W4 satisfying under umbrella PLAN item
   20. Contracts inventory, §13 and retention remain separate M2-contained
   Jobs and do not continue in W4. Review:
   `review-2026-08-24T22-08-19Z.md`; evidence:
   `evidence/review-w4-terminal-signoff-2026-08-24.txt`.
