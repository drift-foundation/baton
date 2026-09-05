# Plan

1. [review-ahead complete 2026-09-04] Re-read the controlling private-line
   ruling, current Job Manager stage/episode contracts, source/workspace
   provider contract, assignment-private cleanup boundary, and Authority
   review receipt. Record the reviewed ownership, identities, transitions,
   refusals, and evidence below. This is contract and plan review only; no
   implementation bytes exist or are approved.
2. [done; returned for targeted review 2026-09-05] Revalidate this review
   against the accepted source/workspace finding, plan, production code,
   tests, and newest review. Record the exact provider symbols reused. If workspace identity,
   mount/custody capabilities, cleanup ownership, quota/re-adoption, source
   attachment, or result layout materially differs from this record, stop and
   return the affected contract for targeted review before production edits.

   The gate ran and three axes differ materially: there is no Work-scoped
   workspace owner to reuse, ordinary attempt cleanup still deletes the two
   roots a line would be, and the workspace bound is an admission-time
   capacity proof rather than a live ceiling. The durable pin is also
   per-attempt. Mount/custody, source attachment and result layout are
   unchanged. Contrary to the initial revalidation note, read-only attachment
   is not a concrete immutable-checkpoint answer because later writable line
   attachment can change the underlying directory. No production bytes were
   written; PROGRESS.md carries the implementer's evidence and the targeted
   review is recorded in FINDING.md and the newest append-only review.
3. [done; latest superseding owner ruling applied 2026-09-05] Add no predictive
   free-space gate, reservation, quota, byte/entry counter, or line-level
   capacity controller. Use the supplied runtime storage and report ordinary
   backend or `ENOSPC` failures against the attempt while preserving the line
   and checkpoints. For the first Git profile, freeze the exact commit and
   tree identity under a retained manager-owned checkpoint reference. A
   read-only view of the current line is valid only while it is proved at that
   checkpoint and no writer exists; the line pathname itself is never the
   checkpoint. Non-Git profiles fail closed without an equivalent immutable
   freeze/read capability, and there is no generic whole-tree copy fallback.
4. [changes requested 2026-09-05] Add a durable review-cycle owner above one-shot Job Manager stages
   and disposable Worker Manager attempts. Define an Authority-namespaced
   `development_line_id`, monotonic line revision, immutable checkpoint
   identity/digest, writable attachment generation, read-only review
   attachment generation, verdict identity, and exact accepted-checkpoint
   eligibility. Reuse the integrated Authority-namespaced identity helpers; do
   not overload stage, admission-episode, attempt, runtime, proposal, or
   receipt identities. Allocate line/checkpoint custody in a reserved namespace
   separate from assignment homes and prove assignment identity derivation
   cannot collide or traverse into it. Compose the accepted storage, adoption,
   capacity and mount primitives; do not assume they supplied a Work-scoped
   owner.
5. [changes requested 2026-09-05] Implement the journalled state machine:
   sole-writer implementation -> writer revoke plus checkpoint freeze ->
   read-only independent review -> either exact-checkpoint acceptance,
   same-line correction from that checkpoint, or terminal rejection. Keep
   review outputs separately writable, keep every prior checkpoint resolvable,
   and never transfer a verdict to a later revision. A checkpoint is the
   immutable artifact named by an ordinary handoff, never a lifecycle status.
   Internal provider-turn boundaries keep the assignment `working` and may
   persist progress without freezing a review checkpoint. A handoff may send
   the frozen checkpoint to review/approval or reassign the same line to
   another vendor/model/profile/session, fencing the old writer before
   attaching the new one.
   The Worker Manager owns the attempt and supervised processes across those
   turns. It must claim before provider/tool launch, fence every operation by
   assignment generation, refuse checkpoint/completion while a child is live,
   and never let a resumed stale session act from remembered ownership.
   Require a conforming agent to await every started command and test before
   voluntarily returning; treat surviving work as defensive containment for
   misbehavior or provider/transport loss, not a normal background-work API.
6. [changes requested 2026-09-05] Compose provider-backed line/checkpoint custody with disposable
   assignment roots. Ordinary attempt cleanup must remove only attempt-owned
   roots and must not delete or retarget the development line or checkpoints.
   The generic manager must not clone, copy/restage candidate trees, run Git,
   mutate the canonical target, or infer custody from a pathname supplied by a
   caller. Only the review-cycle owner may perform explicit terminal or
   recovery cleanup of the reserved namespace after retained evidence is no
   longer owed. Add no capacity policy beyond reporting concrete runtime or
   storage-backend failure.
7. [changes requested 2026-09-05] Add focused positive, negative, replay, race, and recovery
   coverage under the authorized `v12/python/tests/` scope:
   ten correction rounds with fresh attempts and one line; no second source
   clone or candidate copy; concurrent writer refusal; read-only review with
   separately writable findings/logs; immutable/audit-resolvable old
   checkpoints; stale or operand-mismatched verdict refusal; Authority/Work
   identity isolation; exact-operation replay; crash recovery before and after
   freeze, writer revoke/grant, verdict, and correction reopen; attempt cleanup
   preserving the line; multi-turn `working` continuation without false
   failure, release, or checkpoint status; same-session continuation when
   supported; provider-turn return while a supervised child continues;
   completion refusal while that child is live; durable file-based control,
   progress, logs, output, and terminal evidence across manager restart; exact
   labeled-container reconciliation; stale-generation execution refusal;
   deliberate cross-model handoff with prior-writer fencing; and integration
   refusing intermediate, rejected, unreviewed, or later-than-accepted
   checkpoints. Add explicit assignment-namespace collision/traversal refusal,
   absence of a predictive capacity call across correction rounds as selected,
   later line writes leaving earlier checkpoint bytes unchanged, and refusal
   of a mutable directory offered as an immutable checkpoint. Prove a storage
   failure is attributed to only its attempt and does not delete the durable
   line or retained checkpoints; do not simulate a predictive capacity policy.
8. [focused verification passes but reviewed lifecycle gaps remain 2026-09-05] Run the provider's focused tests, new review-cycle
   tests, Authority and Job/Worker Manager contract suites, schema/contract
   regeneration checks if touched, the full v12 Python suite, and repository
   diff checks. Preserve any real-container or restart evidence required by
   the accepted source/workspace contract.
9. [changes requested 2026-09-05] Bind the exact proposal digest,
   base, changed production paths, and every changed test path. Review all test
   assertion/expected-behaviour edits under the granted scope and approve only
   the bytes actually presented. Proposal `f464588c...` is not approved; see
   `review-2026-09-05T13-03-27Z.md` and retained
   `repro-2026-09-05T12-58-34Z.py`.
10. [lifecycle corrected and resealed; registry follow-up waits on W71877;
    replacement proposal rejected on custody/verification 2026-09-05]
    Close the three findings in the newest
    review: make writer revocation an actual assignment/runtime/mount fence
    before freeze; require one quiescent frozen reviewer result and bind its
    findings/log/output evidence before verdict or eligibility; and resolve
    line custody only from the manager's configured workspace store. Retain
    the three-case reproduction as negative coverage. After W71877 releases
    `tools/parallel_test.py`, register both new suites and seal one new exact
    proposal for independent review.
11. [done; final proposal independently approved 2026-09-05]
    Preserve the corrected lifecycle bytes,
    fix the exhaustive boundary-inventory fixture and duplicate Authority-port
    ownership declarations, and pass the four standard unfiltered gates. After
    W71877 releases `v12/python/tools/parallel_test.py`, add both suite entries.
    Reseal one complete `baton.immutable-proposal/1` manifest with schema,
    record paths, known follow-up, digest recipe, and exact verification
    evidence; freeze the package root and every descendant directory to `0555`;
    then return the new digest for independent review. See
    `review-2026-09-05T13-53-35Z.md`.
12. [queued for exact integration 2026-09-05] Import only immutable proposal
    `sha256:46fdcf325d6cd1ba277cf5441275e08a3c46ff2e02dc367dbb74823c0a606453`
    from `/tmp/w71918-final/2026-09-05T14-11-22Z/proposal` after the whole-set
    base/type/owner-write/overlap/digest/custody preflight. Preserve the exact
    sixteen reviewed paths and `0644` target modes; refuse rather than repair
    any divergence. The approval and complete changed-test assessment are in
    `review-2026-09-05T14-18-29Z.md`.

The source/workspace provider is accepted and no longer an implementation
dependency. The two owner rulings in item 3 are now durable, so implementation
may proceed. Pool selection, live-ceiling hardening, and integration-
eligibility consumption remain separately scheduled capabilities.
