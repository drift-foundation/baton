# Plan: disposable v12 assignment authority

1. [done 2026-08-22] Pin the internal store schema and public operation
   boundary to W151 without coupling to v11 product modules or storage.
   `v12/src/authority/schema.mjs` is a fresh superset per SPEC §5;
   `v12/src/authority/index.mjs` is the boundary the next slice consumes.
   Self-containment is a regression (`test/authority_boundary.test.mjs`),
   not a claim.
2. [done 2026-08-22] Implement assignment contracts, generation-bearing
   claims, centralized assignment end, typed gates and exact close/cancel
   behavior. One `#endAssignment` helper serves every Handler-clear path and a
   regression walks all seven of them.
3. [done 2026-08-22] Implement durable operation replay, refusal and
   retirement with full-signature collision checks and restart reconciliation.
   Four durable operation states; retirement binds its operands, reason and
   terminal disposition.
4. [done 2026-08-22] Add positive, negative, retry, race and restart
   regressions against the real implementation; retain the 54/54 W151 model
   gate. 59 authority cases, including competing claims across REAL processes.
   Full v12 gate 137/137; W151 model 54/54.
   Evidence: `evidence/verification-2026-08-22.txt`.
5. [done 2026-08-22] Record implementation progress in implementer-owned
   `PROGRESS.md` and return for independent review without touching later M2
   slices. No Worker Manager, ACP, OCI/container, conformance-harness, root
   recipe or v11 product file was edited.

6. [done 2026-08-22] Correct the four P1s and the P2 from
   `review-2026-08-22T06-15-15Z.md`: remove the public store escape; give the
   proposal its ruled digest tuple and the four receipts their own identities,
   actors and configured capabilities; make durable refusal a property of the
   refusal and settlement authority explicit and fail-closed; restrict public
   transitions to derived scheduler outcomes; and make the race proof
   deterministic and diagnostic. Nine new regressions, 150/150.
   Evidence: `evidence/correction-2026-08-22.txt`.
7. [done 2026-08-22] Re-review returned two P1s. Split the one object into
   the trusted `V12Authority` bootstrap and the participant-bound
   `V12Session` runtime boundary, so a consumer can neither configure nor
   impersonate; and made the approval policy generation required and part of
   the replay identity. Three new regressions, 153/153.
   Evidence: `evidence/re-review-correction-2026-08-22.txt`.
8. [done 2026-08-22] Third review returned an identity TOCTOU and an ignored
   operand. Identity operands are now SNAPSHOTTED once into plain frozen data
   at the session boundary and normalized again in the core; `claim` refuses a
   supplied `participant`/`actor`. Four new regressions, 159/159.
   Evidence: `evidence/third-review-correction-2026-08-22.txt`.
9. [done 2026-08-22] Independent re-review signed off in
   `review-2026-08-22T12-48-13Z.md`. W2929 consumes `V12Session` rather than
   `V12Authority` — and receives only its session, not the store path or the
   trusted bootstrap.

## For review

The three derived rulings — refusing cancellation of a `v11` assignment,
fencing nothing on plan rejection, and the deployment-wide canonical target —
were reviewed on 2026-08-22 and stand; so does the Node 22.5 floor.

The corrections add two decisions worth an explicit look:

- **Configured capabilities are a new authority-owned fact.** §7 names the
  actors; it does not say where the grant lives. It lives in this authority,
  in a `capability` table, because the transitions that check it are here and
  a check whose input came from the caller would not be a check. A deployment
  may grant one participant several, which §10.12 permits.
- **Strict operands on the derived transitions.** `end` and `createWork`
  refuse an unknown operand rather than ignoring it. Ignoring `phase` is safe
  now that it cannot corrupt anything, but a caller whose operand is dropped
  believes it chose the outcome.
