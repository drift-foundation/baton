# Plan: move acquisition outside the artifact-neutral core manager

1. [done 2026-08-26] Revalidate W6631's full dossier, public exports, callers and tests
   against the 2026-08-25 artifact-neutral-manager supersession and W14251's
   preserved schema patch. Separate generic path/integrity/workspace duties
   from Git/directory acquisition behavior.
2. [done 2026-08-26] Identify whether an already pinned source-stager/driver boundary
   consumes the acquisition behavior. If yes, re-home only that behavior and
   record the exact owner; if not, remove it rather than inventing a new
   contract.
3. [done 2026-08-26] Remove acquisition-aware operations and descriptor interpretation
   from `baton_v12.worker_manager`, its exports and its manager inventories.
   Preserve generic private-path, read-only-input and cleanup invariants.
4. [done 2026-08-26] Correct focused tests and additive negative cases: the core
   manager cannot choose Git/directory acquisition, an already staged input is
   accepted generically, and no stale export/inventory owner survives.
5. [done 2026-08-26] Re-run W6631-focused gates and the distribution slice W14251
   measured. Prove W14251's neutral schema no longer fails on definitions named
   by the removed/re-homed manager surface.
6. [next] Independent review. Pass back rather than close.


## Implementation - 2026-08-26

2. There is NO pinned stager or driver owner: the ledger has none, the records
   have none, and the umbrella names one only descriptively. So the
   assignment's own alternative applies and the acquisition half is REMOVED
   rather than re-homed.
5. The acceptance criterion is measured: with W14251's preserved schema patch
   applied to both copies, `tests.manager.test_workspaces` is 22/22, where
   before it refused every request. Both copies were then RESTORED -- this Work
   unblocks that revision and does not land it.

Two long-standing boundary-inventory failures were this module's and went with
it. Full suite 1289 tests, 7 failures and 2 errors, none this Work's; one of
them is a NEW W6629 defect of mine, described in
`evidence/gate-2026-08-26-removal.txt`.


## Independent review changes requested — 2026-08-26

6. [resolved 2026-08-26] The first review requested correction of one P1
   acquisition-specific workspace surface and one P2 stale module contract.
   Review journal: `review-2026-08-26T09-47-16Z.md`.
7. [done 2026-08-26] Removed the `git` root from `assignment_workspace` and
   the OCI adapter's closed `ROOT_NAMES`; updated retained workspace, mount and
   concurrency tests to require only generic manager-owned roots while
   preserving input/workspace containment, cleanup, posture, and isolation.
8. [done 2026-08-26] Replaced the W6631 acquisition-era module docstring and
   empty source-delivery section with the artifact-neutral duties that remain.
9. [done 2026-08-26] Kept
   `test_no_git_metadata_root_survives_the_acquisition_cut` and
   `test_the_assignment_root_contract_is_artifact_neutral`; reran the focused
   workspace/OCI and inventory/security gates and returned for independent
   review.


## Independent re-review changes requested — 2026-08-26

7/9. [verified] The Git root is gone from both manager/OCI contracts, both
additive regressions pass, and the combined focused suite is 97/97.

8. [done 2026-08-26] The workspace production-module contract is corrected.
The contradictory private-Git-root paragraph is gone from `oci.py`; the
workspace test module now describes the retained generic
measurement/workspace cases, and the unused `SHA1` and `MOVED` fixtures are
gone.

10. [done 2026-08-26] Final independent review passes 98 workspace/OCI cases,
24 workspace cases against an independently copied neutral-schema revision,
and the dependency/public-operand checks. Focused inventory checks remain
intercepted only by the concurrent W6634 sealing boundary recorded in the
review evidence. Signed off and passed back rather than closed.
