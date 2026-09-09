# Same-transition diagnosis before further allocation

Claim129055; candidate identity and full bytes: manifest.json. Exact independent
probes/results: probe.py, probe.json, run.log, verification.json. Three controls
pass; review usage0.245344/3s. Author carry is11.021/20s, leaving8.979s. No
whole-module rerun: the reported168-test result was read from the retained log.

## Confirmed: declaration and last-minute checks do not serialize effects

The original duplicate interleaving still resets successor scratch from999 to1.
The changed return is refused/operation-collision, after the destructive effect.
Revoking the writer in the intent cannot distinguish a crashed restorer from
another live restorer: both enter the new recorded-intent branch. The new test
named test_an_in_flight_duplicate_cannot_reset_a_successors_checkout explicitly
asserts the overwritten revision. It demonstrates the defect, not acceptance.

Proposed correction within the existing review_cycles.py boundary: retain the
committed intent, then serialize the profile effect and successful line release
inside the existing store.transact action. That owner already takes BEGIN
IMMEDIATE, rechecks replay under the lock, invokes the action, journals its
result and commits together (store.py:499–588). Re-read owned evidence and
exclusion under that serialization before any profile write. A later identical
call must wait/refuse or replay before its effect; it cannot enter a second
profile effect while the first can release the line. Explicitly contain
same-connection reentry before nested transaction execution. Preserve retry
after a fault/partial filesystem effect, keeping the prior intent and no false
completion; ordinary non-durable refusals and faults already roll back in this
store owner. Do not turn a transient profile failure into a durable terminal
refusal that prevents retry.

This is a proposal to revalidate, not implemented evidence. The tradeoff is
holding the store's write lock across bounded local restoration. The claim that
only a new schema lease or a grant_writer change can solve this was not
established: the existing serialization owner has not been used around the
effect. No schema, grant_writer edit or additional path allocation is approved
or needed for investigating this bounded approach.

## Confirmed: a pathname comparison is not an object-bound write

The new lstat checks reject an already-present symlink. They still leave the
check-to-effect interval: the injected real Git runner replaces the path after
the final check and before reset executes. Outside tracked bytes change from
abandoned scratch to the checkpoint; only afterwards does _same_object raise
ProfileRefusal. This is the same ownership gap at the next boundary, not a new
feature request. Keep the nominated object held through command execution and
bind destructive commands to that object, with safe metadata/path handling.
Another pathname check after the effect is insufficient. Revalidate a concrete
object-bound approach within checkpoint_profiles.py and the existing runner
contract before editing; report an exact missing capability if one remains.

## Confirmed: the retry branch drops evidence validation

After a failed profile call commits the new intent, corrupt only the disposable
retained verdict principal and retry. The retry performs one profile effect
and returns correction-ready; abandoned_correction_of immediately refuses the
result with integrity/schema. The fresh act and completed-reader changes fix
the prior principal counterexamples only on those branches. The recorded-intent
branch calls writer_of rather than writer_for_attempt, skips both A readers
and verdict_of, and _fixed_intent does not bind the result back to its signature
or the full historical owners. Revalidate the same fixed relationships on
every unfinished retry before any effect; preserve valid completed historical
reads without requiring mutable current state.

## Confirmed: additive-only test authority was exceeded

Two existing methods in tests/manager/test_review_cycles.py changed relative to
the retained first candidate:

- test_a_revoked_writer_has_no_correction_to_restore changes its deletion
  setup from the completion to all recovery operations.
- test_a_failed_restoration_admits_nobody changes the expected writer state
  from active to revoked.

Both are in AnAbandonedCorrectionIsRestoredToItsRetainedCheckpoint. Authorship
does not exempt a previously existing test from AGENTS.md's authority rule.
Owner128669 and the correction handoff authorize additive provider tests only.
Restore these methods from evidence/review-128972/candidate/ and add regressions
without changing existing assertions or setups. The proposed serialization can
preserve revocation at completion and therefore does not require those edits.
