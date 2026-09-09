# Bounded decision requested from owner128669

Current-policy supersession,2026-09-09: AGENTS.md's W71830 standing test-change
authority supersedes the test-permission limits and per-method gate in this
historical decision. The accepted25s cumulative budget remains. Use current
PLAN.md for execution; no further per-test approval is required.

## Approved amendment — owner129177, 2026-09-09

Owner129177 in T128692 approved the four exact conversions and mandatory
restoration below, and extended only W128692 to25s cumulative carrying19.534s
used, leaving5.466s. The existing four-path scope and all other assertions/setup
remain fixed. This approved amendment supersedes the pending-request status and
20s/additive-only restriction below solely for these named changes and B's cap.
The original request is retained as decision history. Pinning/dispatch is under
reviewer claim129181; independent acceptance is still required before C/W119114
consumption. No source candidate is approved by this scope amendment.

W128692 remains unaccepted. Review-2026-09-09T16-16-51Z.md records the exact
candidate and remaining defects. No additional source path, schema, Job or
scheduler feature is proposed.

## Recommendation

Authorize the four specific test conversions below, require restoration of the
separately removed original admission test, and extend only W128692's author
verification cap from20s to25s CUMULATIVE. Preserve19.534s already used, leaving
5.466s; do not reset its usage or any other Work's cap. This permits bounded
correction of object-bound profile execution, full historical receipt ownership,
and focused independent acceptance before downstream consumption.

The current authority is owner128669's explicit “Provider tests remain additive”
and20s cap. AGENTS.md requires case-specific confirmation for modifying existing
test assertions/expected behavior, including an author's own unaccepted tests.
The reviewer cannot supply that missing authority or enlarge the cap.

## Exact test conversion scope requested

In v12/python/tests/manager/test_review_cycles.py, within
AnAbandonedCorrectionIsRestoredToItsRetainedCheckpoint:

1. Replace test_the_intent_takes_the_exclusion_before_the_profile_is_asked with
   test_the_effect_and_the_release_happen_in_one_serialized_act: prove the
   writer stays active during the effect and is revoked with line release at
   successful completion. This corrects the abandoned early-revocation design.
2. Replace test_an_in_flight_duplicate_cannot_reset_a_successors_checkout with
   test_an_in_flight_duplicate_cannot_reach_a_second_effect: require no second
   effect and no successor admission while restoration is in flight. The old
   case explicitly asserted overwritten successor scratch as its residual.
3. Replace test_a_duplicate_that_completed_is_not_reported_as_this_call with
   test_a_second_connection_replays_without_entering_the_effect, plus an
   additive actual overlapping-connection control. Require exactly one effect
   and an identical committed replay; do not bless a collision after damage.

In v12/python/tests/manager/test_checkpoint_profiles.py, within
RestoringOneCheckoutToItsRetainedCheckpoint:

4. Replace test_a_substitution_between_the_writes_is_refused with
   test_a_substitution_between_the_writes_follows_the_held_object: allow
   completion only on the still-held original object, while all distinct
   foreign objects remain unchanged. Add substitution at the command boundary,
   not just between returned commands.

Restore test_an_admission_during_the_restore_stops_the_completion in the manager
class byte-for-byte from evidence/review-128972/candidate/. It is not included
in the requested removal/conversion authority. Preserve both already-restored
methods and every other existing test assertion/setup. All further tests remain
additive. The reviewer has not approved the current source candidate; the
decision grants bounded test-edit scope, with corrected final bytes still
requiring independent review.

## Implementation and verification boundary after approval

Only the same four owner128669 paths may change: review_cycles.py,
checkpoint_profiles.py and their two manager test modules, relative to
v12/python/src/baton_v12 and v12/python/tests/manager as already bound.
Pin the approved amendment and exact approach in FINDING/PLAN before edits.
Use the existing serialized effect/completion, the demonstrated object-reference
approach (revalidated), and A's public historical owners. Run focused negative,
positive, retry and actual concurrency controls under the extended cumulative
cap. Return through baton.impl -> baton.bug; C and W119114 stay gated until
independent acceptance. No new allocation or blanket test authority.
