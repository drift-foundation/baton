# Proposed bounded selector provider and test disposition

**Approved 2026-09-08, owner event121773.** Slawomir approved this exact
provider, four digest-bound test exceptions, restorations and exclusions.
This supersedes the pending/proposed status below, retained as history. The
consumer FINDING pins the ruling; actual provider and consumer acceptance remain
required. No other path or assertion change is granted.

Prepared by baton.codex, claim121221. **Proposed, awaiting owner disposition.**
review-2026-09-08T17-37-36Z.md owns the observations and reproductions. This
proposal supplies neither implementation authority nor acceptance.

## Separately acceptable provider

Create a new top-level finding/Work after approval, High serial baton.impl to
baton.bug, and gate W120425 on its actual independent acceptance. W120762 and
W120763 remain accepted; this fills the caller's missing cold selector, not a
retroactive claim that their approved APIs failed their own scope.

Proposed public API: `publication_for_attempt(manager, *, attempt_id)` returns
the same validated committed receipt as publication_of, or None for genuine
absence. It takes neither publisher nor a remembered manifest selector. Read
the existing local publication journal, identify the unique committed record
for that exact attempt and validate it through the existing owner contract,
including deterministic operation identity, signature, retained manifests and
assignment/result bindings. Refuse ambiguity and malformed/contradictory
candidate records rather than guessing or treating them as absence. Pin the
local selection algorithm and its corrupt-record boundary before edits; do not
add schema, store infrastructure, another journal or remote fallback.

Exactly three paths under v12/python:

- src/baton_v12/integration/driver.py
- src/baton_v12/integration/__init__.py (public export only)
- tests/integration/test_driver.py (additive controls; preserve every existing assertion)

Prove genuine publication followed by a new manager/seam with no remembered
selector, forbidden publisher access and SQL write denial; retained-only and
absent cases, foreign/malformed/ambiguous records, replay, and later target
movement. About15s focused controls and only newly affected tests, with retained
output/timing. The consumer's actual lifecycle proof remains separate.

## Exact consumer test exceptions requested

Only `v12/python/tests/job_manager/test_review_driver.py`; all named methods
below belong to TheImplementationResumeReadsRealCommittedCustody. Compare
evidence/review-120624-tests.py with review-121221-tests.py and their retained
review-121221-tests.patch (candidate SHA256
d6f0bb5d6c78d74cd48aff9e07d4afe4f4de1a4598a0b6939a21c2724addd3b7).
These are requested exceptions to event120736's preservation rule, not implied
by the author's prior unaccepted implementation.

1. Replace test_an_unsettled_cleanup_axis_refuses_before_the_owner_is_asked
   with the candidate's test_the_cleanup_axis_no_longer_decides_anything:
   changing only cleanup axes beside valid committed evidence preserves the
   exact successful answer, while the separate missing-journal test remains.
2. Replace the old test_a_checkpoint_that_is_not_this_writers_frozen_one_refuses
   pointer-absence/pointer-foreign expectations with the candidate's refusal
   when this writer's committed freeze journal is missing. Keep the additive
   pointer-independence control and require a further additive real-later-round
   positive proof. No unrelated checkpoint assertion may be removed.
3. In test_a_cleanup_axis_without_its_committed_destroy_refuses, replace the
   tolerated one Authority read with zero calls and the new owning-reader
   diagnostic, exactly as the candidate does. This strengthens the no-act rule.
4. Permit only the candidate assertion/fixture adjustments in
   test_the_ordinary_ending_leaves_every_record_a_resume_reads and
   test_the_recorded_steps_are_the_ones_the_resume_performs that measure real
   publication history and observe cleanup_of instead of authorize_cleanup.
   Preserve all other no-act, ordering, custody and correlation assertions.

Not requested and not approved by this proposal: deleting the missing retained
proposal test, dropping foreign proposal/manifest stimuli, changing the
ordinary return shape, omitting full equality, or further unrelated changes.
Restore those negative contracts in the consumer's original two-path correction;
any necessary owning-reader diagnostic adjustment must retain the same missing
record stimulus and refusal behavior. Keep the seven restored behavioral cases,
including the complete ordinary published answer. All other fixture additions
and cold/later-round controls remain additive within the existing scope.

After provider acceptance and this exact test disposition, W120425 retains only
review_driver.py and test_review_driver.py. Compose the new reader, close the
receiving-boundary/ordinary-answer findings, demonstrate cold and real-later-round
recovery under all forbidden-act guards, and return for independent review.
No assembly path, runtime/schema change, broad suite or Git mutation is granted.
