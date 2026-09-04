# Plan

1. [review-ahead complete 2026-09-04] Review the scheduler-owned target queue
   against current Authority proposal/verification/review/approval/integration
   receipts, the accepted Job Manager stage boundary, W62098's Git lineage,
   the settled `baton.merge` contract, and W71459's test-change/mode policy.
   Record the ownership, identity, eligibility, ordering, fencing, refusal,
   crash and evidence requirements. This approves the contract and plan only;
   it creates or approves no implementation bytes.
2. [implementation entry gate] Revalidate the reviewed contract against the
   accepted persistent checkpoint and correction-line implementation. A
   material mismatch in checkpoint identity, verdict binding, immutable
   custody, path-set evidence, or integration eligibility returns the affected
   contract for targeted review before production edits.
3. [pending implementation] Introduce a stable canonical-target identity
   separate from the mutable expected/current revision. Define immutable,
   Authority-namespaced queue entries, transactionally allocated enqueue rank,
   one-live-lease-per-target uniqueness, monotonic lease fencing and explicit
   terminal/recovery states. Ensure all Authorities permitted to address one
   checkout share its lock, while distinct targets do not serialize each
   other.
4. [pending implementation] Admit an entry only from one exact final checkpoint
   carrying valid proposal/base/head/object transport, passed verification,
   accepted newest review, approved Authority receipt, reviewed path-set
   digest, and scheduled test-change scope. Exact replay returns the same rank;
   stale checkpoint, changed operands, incomplete authority or mismatched scope
   refuses before enqueue.
5. [pending implementation] Compose the live lease with the sole trusted
   Git-aware integration capability. Revalidate eligibility and target revision,
   run `baton.merge`'s whole-path provenance/authority/type/base/mode/overlap
   preflight before mutation, import only reviewed bytes without custody modes,
   and run bounded final-byte/mode and Work verification. The generic Worker
   Manager receives no canonical checkout and runs no Git.
6. [pending implementation] Record the Authority integration receipt and
   target-revision advance only after real import and verification. Make direct
   integration without the live lease/fence impossible. Journal enough state
   to reconcile all-base, all-candidate and mixed/diverged restart observations
   without duplicate import, false success, lock release on uncertainty, or a
   hidden correction.
7. [pending verification] Prove same-target FIFO/rank and two-ready races,
   independent-target concurrency, stable locking across target revisions and
   any shared-target Authorities, enqueue/lease replay collisions, stale fence
   refusal, prior-holder recovery, moved target, missing Git objects,
   stale/mismatched review or approval, old correction checkpoint, path-scope
   mismatch, overlap/conflict, symlink/non-regular/read-only/base-drifted target,
   crash before/during/after import and Authority completion, one scheduled
   existing-test change, and one out-of-scope test refusal. Assert every
   negative case mutates neither target bytes/modes nor Authority target state.
8. [pending integration verification] Run the complete Authority, Job Manager,
   integration-policy and provider checkpoint suites plus focused real Git/
   working-tree restart and race gates. Verify schema/document regeneration if
   touched, full v12 Python tests, and `git diff --check`.
9. [pending independent implementation review] Bind the exact proposal digest,
   base, production paths, and every changed existing test path. Evaluate all
   assertion/expected-behaviour changes under the scheduled scope and approve
   only the presented bytes and their retained verification evidence.

Contract review runs ahead of component completion. Before handoff to
implementation, restore the component dependency that supplies accepted
checkpoints and correction lines, allowing that gate to release the review
claim, then reroute the blocked Work to implementation. Implementation remains
blocked until that provider is accepted.
