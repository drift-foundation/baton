# Plan

**Status — 2026-08-21:** complete and independently terminal-verified. The
migration was accepted in review round five, the external prototype root has
been removed, and one canonical prototype tree remains in this repository as
`v12/`. W126 is ready to close satisfying.

1. [done] Revalidate the parent placement ruling and W76's final clean review.
2. [done] Inventory the external tree and distinguish reviewed material from
   generated dependencies and disposable runtime state.
3. [done] Create and claim corresponding child Work W126.
4. [done] Copy the selected snapshot into self-contained top-level `v12/`.
5. [done] Prove 426-file byte parity, executable-mode preservation, and
   absence of excluded material.
6. [done] Install dependencies from the pinned lockfile and run the
   prototype's own test gate from `v12/` (59 passed).
7. [done] Replace retired external-root assumptions with the explicit
   disposable external state-root boundary, preserving the no-checkout-mount
   fence; add the self-contained `v12/justfile` and placement regressions.
8. [done] Re-run the unit gate and the bounded live proof (`proof-r7-migration`).
9. [done] Review round one: two blocking findings.
10. [done] One fail-closed placement authority used by every entry point
    before its first mutation; whole-checkout externality; constrained
    evidence labels (`proof-r8-placement`).
11. [done] Review round two: two further blocking findings.
12. [done] Bind `new-authority.sh` to the exact configured plan; require
    durable ownership evidence for root deletion (`proof-r9-ownership`).
13. [done] Review round three: the deletion path answered for an absent root.
14. [done] Require `owned` on the deletion path whatever the root's current
    existence (`proof-r10-absent-root`).
15. [done] Review round four: the new regression deleted a fixed shared path
    to make its fixture absent.
16. [done] Obtain absence by construction (`proof-r11-fixture`).
17. [done] Review round five: ACCEPTED.
18. [done] Remove the external prototype root and report that irreversible
    cleanup explicitly (`proof-r12-standalone`).
19. [done] Independently verify the removed-root fact, surviving canonical
    tree, standalone proof, focused gate, and clean repository-state boundary
    (`review-2026-08-21T07-04-00Z.md`).
