# Plan

1. [complete 2026-09-06] Revalidate the accepted checkpoint, review, approval
   and coordinator entry contracts against the committed item-3 foundation.
2. [unblocked 2026-09-06 by W101714] Enumerate the one generic cross-binding
   account and its refusal taxonomy without adding VCS vocabulary or changing
   K-owned shared boundaries. The revalidation that blocked this was right:
   `profile_account_digest` had no accepted producer, and neither did
   `profile_version` or `proposal_manifest_digest`. All three are REMOVED.
   `scope_digest` does have one, which this record had never named: the
   accepted Job's `test_scope`.

   THE ACCOUNT TO ADMIT AGAINST is fifteen members, each with a named accepted
   producer: `authority_uuid`, `work_id`, `assignment_generation` from the
   attempt's assignment; `line_id`, `checkpoint_id`, `verdict_id`,
   `checkpoint_digest`, `path_set_digest` from W71918's checkpoint verdict;
   `proposal_id`, `candidate_digest`, `result_id`, `result_digest`,
   `expected_target_revision` from Authority's `publish` operation and its
   `proposal` row; `profile_kind`, which renames the accepted checkpoint
   evidence's own `profile` member; and `scope_digest`, the digest of the
   accepted Job's `test_scope`. Admission re-resolves each one from that
   surface and never from a caller operand.
3. [complete 2026-09-06] Implement admission in a disjoint leaf module and add
   focused replay, mismatch, scope and race tests.
4. [answered by K 2026-09-06; W101714 carries the change] The K-owned account
   is the fifteen members in item 2. The tuner makes no shared-interface
   change; if that account turns out to be insufficient for a refusal this
   leaf owes, return the finding to K rather than widening it here.
5. [complete 2026-09-06] Run focused admission/coordinator gates and
   independent implementation review. K added the one shared parallel-registry
   member under M102221; the tuner independently reran the focused and broad
   parallel gates. Independent review
   `review-2026-09-06T14-16-33Z.md` signed off with no findings.
