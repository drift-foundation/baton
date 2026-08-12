# Plan

1. Complete the prerequisite TUI `m` boundary repair — **done and signed off
   2026-08-11**. The shared affordance/model rule and real-key regressions pass
   for answered, sent, seen-notice, and unread boundaries. See
   `review-2026-08-11T13-43-06Z.md`.
2. Create the required implementer-owned `PROGRESS.md` and record both review
   responses — **done 2026-08-11**.
3. Close the prerequisite review while keeping released `bin/baton`,
   `bin/baton-tui`, and their manifests untouched — **done 2026-08-11**.
4. Define the separate whole-message save representation and chosen-path UI —
   **approved by Slawomir 2026-08-11**. Implement one deterministic
   `.baton.json` immutable envelope, exact `--output` path through `baton save`,
   and TUI `M` path mode. Preserve ordered typed parts, external pinned
   references only, transient refusal, fixed row identity, and
   no-clobber/identical-resume publication.
5. Add new positive, negative, multipart, large-body, path/symlink, retry,
   authorization, fixed-target, CLI, and TUI/PTY regressions after the design
   ruling and alongside implementation — **done and signed off 2026-08-11**.
   Slawomir's later repository-policy ruling always authorizes additive tests,
   including the two one-member exhaustive-registry additions in this change;
   see `review-2026-08-11T23-26-58Z.md`.
6. Implement and review the whole-message operation in current next-generation
   source — **done and source signed off 2026-08-11 in
   `review-2026-08-11T23-26-58Z.md`** — then exercise it through the versioned
   1.1 candidate. Frozen 1.0 artifacts and live authority/config remain
   untouched during development.
