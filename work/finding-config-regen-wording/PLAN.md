# Plan — config regeneration wording

1. Preserve the frozen 1.0.0 artifacts and distribution manifest unchanged —
   active release rule. The 1.1 source documentation may now advance.
2. Revalidate the exact `regen` implementation and failure modes in the next
   documentation release window — **done 2026-08-11**. A generation+1 file is
   a proposal with no authority effect, but ordinary opens refuse its
   unaccepted digest/generation; refusal leaves authority unchanged.
3. Correct both `docs/AGENTS-MAILBOX-PROTO.md` and
   `docs/EFFECTIVE-BATON.md` with the exact proposed-config / audited-accept /
   restore-on-refusal / never-edit-SQLite wording in `FINDING.md` — **done by
   `baton.reviewer` at Slawomir's instruction on 2026-08-11**.
4. Run focused config/regen and documentation assertions, then independently
   review — **done and independently signed off 2026-08-11**. Author
   verification passed 8 focused tests plus literal documentation checks;
   `baton.implementer` then checked the claims against behavior and passed 11
   focused regen tests. See `review-2026-08-11T19-39-32Z.md`.
   Do not edit existing tests without case-specific authorization.
5. Verify the scratch 1.1 candidate manifest carries the new documentation
   hashes. Frozen canonical manifest replacement remains Slawomir's release
   action.
