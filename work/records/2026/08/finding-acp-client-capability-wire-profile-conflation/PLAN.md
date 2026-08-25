# Plan: separate ACP wire capabilities from the durable profile summary

1. [done 2026-08-23] Record the §2.2, SDK, durable-schema and executable-model
   disagreement discovered during W4 handshake review.
2. [done 2026-08-23] Revalidate the exact pinned SDK encode/decode boundary and all
   current consumers of `MINIMAL_CLIENT_CAPABILITIES`.
3. [done 2026-08-23; approved] Persist the literal structural ACP capability
   document as the one canonical representation. Preserve ACP names and
   omission semantics; remove the invented snake-case explicit-false summary
   instead of naming and maintaining two shapes. Any future provider-neutral
   model requires separately justified Work.
4. [queued for implementation] Append an explicit correction or supersession to the
   owning ACP finding and update SPEC, schema descriptions/examples, model,
   trace interpretation and focused contract regressions atomically.
5. [queued] Re-review W4 and every later adapter consumer against the corrected
   single contract.
4. [done 2026-08-23] Implemented as one contract change across seven
   artefacts. The frozen `clientCapabilities` definition admits
   `{fs: {}, terminal: false}` and nothing else — `fs` has no properties and
   `additionalProperties: false`, so a member present at all, even set false,
   refuses — with the removed shape quoted in its description. The executable
   model's constant is the ACP document and its validator is STRUCTURAL and
   order-independent. The captured trace's profile and both negative capability
   vectors are corrected and the profile RE-SEALED. The product schema copy is
   byte-identical, the v12 handshake keeps ONE exported constant, and every
   profile fixture in four v12 suites carries the ACP document and the new
   digest. THE RULING WENT FURTHER THAN THE HANDSHAKE ROUND'S WORKAROUND: that
   round named two representations on its review's instruction, and this
   ruling deletes the second rather than ratifying the split. Two assertions
   that encoded the removed shape are superseded and marked where they stood,
   one of them INVERTED — it asserted the two documents differed and now
   asserts the profile persists the same one the relay sends. The exact
   minimal-capability POLICY is deliberately unchanged. Three mutations, all
   witnessed.
   Evidence: `evidence/implementation-2026-08-23.txt`.
5. [queued] Re-review W4 and every later adapter consumer against the corrected
   single contract. Not discharged by item 4.
4. [changes requested 2026-08-23; independent review round 1] Make the
   structural validator prove JSON documents rather than accepting every
   empty-key object, retain null-prototype and order-independent documents,
   keep rejected values inside `policy.denied` without serializing their
   behavior, and make the two additive reviewer regressions pass. Evidence:
   `review-2026-08-23T19-36-46Z.md` and
   `evidence/review-round1-2026-08-23.txt`.
6. [done 2026-08-23] Closed. The validator proves an INERT JSON RECORD at both
   levels: an object, not an array, carrying `Object.prototype` or none, with
   exactly the expected own keys COUNTING the ones `Object.keys` hides, and
   every one of them a DATA member. `Object.create(null)` and either insertion
   order remain valid, as the review requires. THE OLD CHECK ASKED WHETHER THE
   OBJECT LOOKED EMPTY and the question is whether it IS the document §2.2
   sends. And the refusal stopped serializing what it refuses AT ALL THREE
   SITES — the review found the one on `terminal`; the envelope and `fs`
   refusals carried the same line and the same defect. The envelope is proved
   BEFORE its members are read, which is what makes those reads inert. Nine
   mutations: seven witnessed, one PROVABLY equivalent (`Array.isArray` throws
   only on a revoked Proxy, and every reflection on one throws, so the
   prototype read fails first), and one whose zero was a MISSING CASE that I
   then built. Three added cases, all properties over both levels or all three
   sites. Handshake 26/26.
   Evidence: `evidence/correction-round1-2026-08-23.txt`.
7. [queued] Unify the record proof with the one W2929's reconnect corrections
   built in `agent_reconnect.mjs`. The same four rules now have two
   implementations. NOT done here: that module is inside W4's open review
   round, and moving code out of a module under review puts the change in the
   wrong Work. The moment is W4 composition.
8. [queued] Re-review every later adapter consumer against the corrected
   single contract (was item 5). The review's sweep found no 1.0 source
   consumer retaining the removed constants; `v12/src/acp_session.mjs` and
   `tools/acp-baton-bridge` stay outside 1.0 scope as the accepted 0-spike and
   the earlier v11 bridge.
9. [changes requested 2026-08-23; independent review round 2] Reject Proxies
   before any reflection at both capability-record levels. A successful trap
   currently impersonates the exact document and runs caller code. Complete
   item 7 now by composing one shared, non-observing inert-record proof with
   W4 reconnect rather than adding a third divergent correction. Make both
   additive Proxy regressions pass while retaining ordinary and
   null-prototype records, order independence, and the closed refusal
   taxonomy. Evidence: `review-2026-08-23T20-20-01Z.md` and
   `evidence/review-round2-2026-08-23.txt`.
7. [done 2026-08-23] Discharged, and pulled forward from W4 composition on the
   second review's explicit instruction. There is ONE record proof now,
   `v12/src/worker_manager/records.mjs`; both `agent_handshake.mjs` and
   `agent_reconnect.mjs` call it and neither keeps a copy. A Proxy is rejected
   FIRST by a non-observing discriminator, because a successful trap walks
   past a try/catch. The callers keep their own taxonomies — the module
   returns facts and prose, never a `ContractError`, since `integrity.schema`
   and `policy.denied` are the callers' policies. The module header carries
   the six rules six review rounds produced, because none of them is obvious
   and each cost a round. NO ASSERTION IN EITHER SUITE CHANGED: the shared
   vocabulary is reconnect's existing vocabulary, chosen so W4's in-review
   cases keep passing unedited.
   Evidence: `evidence/correction-round2-2026-08-23.txt`.
9. [done 2026-08-23] The P1 itself: a Proxy whose traps ANSWER passed a proof
   built to catch traps that THROW, at both capability levels. Closed by item
   7's shared primitive — one fix, not two. Eight mutations: six witnessed
   across ALL THREE suites (which is the composition working), one whose zero
   was a missing case I then built (`Object.setPrototypeOf([],
   Object.prototype)` is an ordinary array wearing the document prototype),
   and one MEASURED UNREACHABLE — the descriptor wrapper's only witness was a
   descriptor-trapping Proxy, which the Proxy test now rejects long before it.
   Kept, not counted. Six new cases for the primitive's own contract.
   FULL v12 IS 670/670.
10. [queued] Re-review every later adapter consumer against the corrected
   single contract (was item 8, was item 5).
11. [changes requested 2026-08-23; independent review round 3] Require every
   expected JSON member to be an enumerable data descriptor. The shared proof
   currently accepts non-enumerable required members, so an ACP envelope whose
   `fs` and `terminal` fields are hidden validates even though its serialized
   document is `{}`. Retain the shared Proxy-first primitive, caller-specific
   taxonomies, reconnect behavior, ordinary/null-prototype records, insertion
   order, and hidden-extra-member refusal. Make both additive regressions
   pass. Evidence: `review-2026-08-23T20-37-50Z.md` and
   `evidence/review-round3-2026-08-23.txt`.
11. [done 2026-08-23] Closed. `recordFault` requires every expected member's
   descriptor to be ENUMERABLE as well as a data descriptor. THE RULE HAS TWO
   DIRECTIONS AND I IMPLEMENTED ONE: round one's "looking empty is not being
   the empty document" was applied by counting hidden own keys, so an extra
   non-enumerable member could not smuggle a `toJSON` past the proof — and
   then the EXPECTED members were proved by property access alone, so an
   envelope whose `fs` and `terminal` were both non-enumerable passed while
   `JSON.stringify` of it was `{}`. Both values readable, neither on the wire.
   Still an inert descriptor check: the value is never read, no behaviour
   runs, Proxy handling untouched. Nothing else changed — empty records,
   null-prototype records, order independence, hidden extra-member refusal,
   accessor refusal and both caller taxonomies all stand, with reconnect
   32/32 and no assertion edited. Four mutations, all witnessed, including
   re-measuring the two neighbouring rules to confirm this did not make either
   redundant. The added case asserts the PROPERTY rather than the branch —
   acceptance implies the JSON document, checked against `JSON.stringify`
   itself — and states explicitly that the converse is NOT claimed, because
   the proof is deliberately stricter than the wire. FULL v12 IS 677/677.
   Evidence: `evidence/correction-round3-2026-08-23.txt`.
12. [queued] Re-review every later adapter consumer against the corrected
   single contract (was item 10).
12. [done 2026-08-23] Current consumer sweep complete. W4's handshake is the
   only agent-session 1.0 transport consumer and uses the one ACP-shaped
   document. The accepted pre-1.0 spike and earlier v11 bridge remain outside
   this contract's recorded scope; no later 1.0 adapter retains the removed
   summary. A future adapter is reviewed when introduced rather than kept as
   an unschedulable open item here. Evidence:
   `evidence/signoff-round3-2026-08-23.txt`.
13. [signed off 2026-08-23; independent review round 4] Accepted item 11's
   enumerable-data-descriptor correction and closed the current consumer
   sweep. Records 8/8, handshake 29/29, reconnect 32/32, ACP boundary model
   66/66, and schemas identical. Full v12 678/680; both failures belong to
   W4's open composition correction. Review:
   `review-2026-08-23T20-59-26Z.md`.
