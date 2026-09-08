# Plan

1. [done; parent review 2026-09-06] Revalidate the accepted interfaces, correct
   the proposal-publication cutpoint, and freeze the exact production and test
   path set in FINDING. No implementation bytes were reviewed.
2. [done; baton.tuner 2026-09-06] Add the two-phase provider-neutral driver:
   live-producer proposal publication, then accepted-checkpoint receipts,
   candidate admission, target-global leasing, fenced integration, and
   terminal/held settlement.
3. [done; focused verification 2026-09-06] Prove success, refusal, uncertain recovery, live-
   grant revalidation, receipt separation, and restart replay without duplicate
   canonical writes or an automatic recovery decision.
4. [done; contract re-review 2026-09-06] Correct the queue-head
   binding and the Authority-completion cutpoint described in
   `review-2026-09-06T16-57-02Z.md`. The driver must never attribute the entry
   selected by `grant_lease` to a different caller-selected proposal, and the
   live target lease must remain held through Authority completion. A restart
   after the model was asked must take the ruled operator-held path rather than
   completing a missing Authority receipt. The exact-head and completion
   contracts plus the bounded four-path seam expansion are pinned in FINDING.
5. [done; baton.tuner 2026-09-06] Implement the exact-entry FIFO grant
   and defer successful coordinator settlement/release until the driver has
   written and re-read the exact Authority integration receipt under the live
   grant. Refusal or uncertainty retains the lease and enters manual hold;
   terminal replay only reads an already-existing receipt.
6. [done; baton.tuner 2026-09-06] Add two-ready/out-of-order queue coverage and
   an injected crash/refusal at Authority completion. Prove that the imported
   entry and Authority receipt are the same accepted account, that the next
   target writer cannot start before completion, and that restart does not
   automatically finish the missing receipt. Update the existing execution and
   coordinator expectations explicitly scheduled in FINDING. Add only the
   required exact `entry_id` keyword to the four direct `grant_lease` call
   sites in `test_runtime.py` and `test_recovery.py`, then retain their original
   assertions and the full regression matrix.
7. [done; baton.tuner 2026-09-06] Correct the
   settlement/release restart cutpoint in the existing nine-path boundary.
   An integrated entry with a live lease and exact existing Authority receipt
   must replay settlement/release to completion without invoking Authority
   integration or the runtime; a released lease remains a read-only terminal
   replay. Add the injected cutpoint and next-FIFO-entry regression.
8. [done; baton.tuner 2026-09-06] Correct the
   admission-replay seam described in
   `review-2026-09-06T17-37-33Z.md`. The driver must refresh the exact current
   coordinator entry after immutable enqueue replay and must cross-bind it to
   the resolved accepted account before terminal dispatch. Replace the mocked
   current-entry substitution with a production-path restart regression for
   integrated/live and integrated/released leases.
9. [done; baton.codex 2026-09-06] Independently verify the corrected bounded
   nine-path candidate, real admission replay at both terminal lease states,
   focused and complete integration suites, compilation, and diff hygiene. No
   findings remain.
