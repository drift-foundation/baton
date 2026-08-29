# Plan: exact ended-runtime restart adoption

1. Revalidate W6636's running-adoption, exact-observation and cleanup contracts.
2. Create an exact exited-but-present runtime and restart the manager over the
   same durable store.
3. Reconcile, force-remove and observe absence before provider teardown and
   lane reuse.
4. Add mismatch, multiplicity, uncertainty and sibling-preservation negatives.
5. Run focused Docker/restart gates and return for independent review.

## 2026-08-28 — implementer round

- [done] 1. W6636's contracts revalidated; the fixture is subclassed, not
  restated.
- [done] 2. An exact exited-but-present runtime is created by the ordinary
  worker exit, and a second incarnation opens over the same durable store.
- [done] 3. Reconcile, force-remove and observed absence precede provider
  teardown and settlement.
- [partial] 4. Uncertainty and sibling preservation are covered; MISMATCH is
  not writable at this seam and the reason is recorded in `PROGRESS.md` and at
  the site. Multiplicity remains covered by W6636's real-daemon stranger case.
- [done] 5. Focused Docker and full manager gates run; returned for review.

## 2026-08-28 — independent review

- [accepted partial] Exact ended-container discovery through a second manager
  incarnation and the pre-cleanup replacement refusal are represented.
- [changes requested] Add a post-cleanup lane consumer; current assertions stop
  at terminal rows and prove no reuse after positive absence/provider teardown.
- [changes requested] Trace force-removal, exact absence observation, both
  provider teardowns, and subsequent reuse in their required order.
- [changes requested] Construct an unrelated sibling attempt/runtime/root and
  prove the ended-restart mismatch, multiplicity, uncertainty, and retry paths
  cannot delete or settle it. Explicitly supersede any genuinely unreachable
  acceptance member instead of treating it as partial completion.
- [verification blocked] Independent Docker replay was denied access to the
  daemon socket in the managed reviewer context; 133 daemon-free attempt tests
  passed and no real-engine review pass is claimed.

## 2026-08-28 — correction re-review

- [accepted] Shared trace proves remove, exact absence observation, credential
  teardown and launch teardown ordering.
- [accepted] A sibling credential root survives exact target cleanup.
- [accepted] A successor manager attempt is activated and started only after
  cleanup; pre-cleanup replacement remains refused.
- [required] Add the ended-restart mismatch/multiple-candidate real-engine
  negative and an actual sibling attempt/runtime preservation witness, or pin
  an explicit supersession for any provably unreachable acceptance member.

## 2026-08-28 — final review

- [done] Ended-restart multiplicity cancels and removes neither real candidate.
- [done] A real sibling runtime and sibling provider root survive exact target
  cleanup.
- [done] The unreachable row-mismatch wording is explicitly superseded by the
  reachable destroy-answer mismatch, which leaves cleanup retryable.
- [signed off] W32385's bounded Docker restart slice is complete; no Podman or
  separate negative/race certification is implied.
