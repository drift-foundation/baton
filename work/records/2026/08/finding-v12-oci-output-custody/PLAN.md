# Plan

1. Revalidate the W6634 output-custody spike against current assignment, completion, and result-manifest contracts.
2. Pin the provider interface and manager-owned custody locations without importing credential or lifecycle-settlement ownership.
3. Implement bounded no-follow reads, exact manifest comparison, staged custody, live-secret rejection, freezing, and atomic sealing.
4. Add focused positive, negative, race, limit, replay, and real-OCI regressions.
5. Run focused and full v12 verification, then request independent review.

## 2026-08-27 — implementation

- [done] 1. W6634 revalidated against current contracts. Six of seven
  obligations met; the seventh — staging — reopened each measured path and was
  proved to admit host material into custody and to hang on one `mkfifo`.
- [done] 2. The provider interface pinned: `workspaces.copied_manifest` owns the
  single no-follow measure-and-copy, `sealing` keeps the §13 rule and passes it
  as `admits`, and custody stays a sibling of the assignment roots. No
  credential or lifecycle-settlement ownership imported.
- [done] 3. Bounded no-follow reads, exact manifest comparison, staged custody,
  live-secret rejection, freezing and atomic sealing — the last four already
  present and revalidated, the staging pass rewritten.
- [done] 4. Positive, negative, race, limit, replay and real-OCI regressions,
  plus a 12-mutation measurement over all three suites.
- [done] 5. Focused and full v12 verification run; returned for independent
  review.

### For review

- [judgement] One existing `test_sealing` case was REPLACED because the window
  it asserted no longer exists. The replacement asserts the stronger property.
  Mine to justify, not to settle.
- [SUPERSEDED — owned, and now fixed] This entry said `check_input_pair`'s
  three receiving parameters were unregistered in the contracts inventory, so
  the full-tree gate carried a seventh failure with no owner. Neither half is
  true any more, and the review's correction was itself overtaken: **W26296**
  (`work/records/2026/08/finding-check-input-pair-inventory-follow-up`) took
  ownership as a live blocker of W6636, and the registration has since landed
  — the three parameters are declared at `test_contracts_inventory.py:147`
  and that module is GREEN. **The accepted baseline is now SIX failures, all
  in `test_boundary_inventory`, not seven.** Verified on this tree rather than
  carried forward. Nothing in this Work touches any of it.

## 2026-08-27 — independent review changes requested

- [required] Open each worker-controlled source file with `O_NONBLOCK` as well
  as `O_NOFOLLOW`, prove the opened descriptor is regular, and add a bounded
  regression for replacement with a FIFO after listing but before open.
- [required] Add the missing nonblocking-source-open mutation to the custody
  harness; the current 12 mutations do not remove or observe this guard.
- [approved, message 27064] Retain the case-specific replacement of the
  existing moving-tree sealing test. The approver confirmed the old refusal
  asserted a retired two-read window and explicitly preserved the independent
  FIFO-race correction below.
- [evidence] Regenerate or append corrected evidence for the shell-expansion
  damage in sections 3 and 4, and correct the stale no-owner statement:
  W26296 now explicitly owns the `check_input_pair` inventory follow-up.
- [documentation] Correct `sealed_result`'s stale claim that the tree is
  measured twice; the implementation and the surrounding explanation now use
  one source pass followed by verification of manager custody.

## 2026-08-27 — review corrections applied

- [done] The [P1] race. `workspaces._read_exactly` now opens
  `O_RDONLY | O_NOFOLLOW | O_NONBLOCK`; the descriptor-level regular-file
  proof is retained and is what refuses the replacement. The reviewer's own
  `evidence/w26283-review-fifo-race.py` returns `integrity/path` instead of
  blocking.
- [done] The bounded regression.
  `test_a_file_replaced_by_a_pipe_after_listing_does_not_block` interposes on
  the REAL walk at the yield boundary, so the entry really was accepted as a
  regular file by the code under test, and bounds itself with `SIGALRM` —
  a regression here is a hang rather than a failure, and a hanging case takes
  the whole gate with it.
- [done] The mutation. `a post-listing pipe blocks the source open` removes
  the flag; the harness is now **13 of 13 caught**. The alarm is what keeps
  that mutation measurable instead of stalling the run.
- [done] The stale documentation. `sealed_result` said the measurement is
  taken twice and that the second one is the point. It now says the opposite,
  because the opposite is true: one pass is what removed the race rather than
  detected it.
- [done] The evidence. Sections 3 and 4 of
  `evidence/w26283-2026-08-27-custody-provider.txt` were damaged by
  shell expansion when they were produced. The damaged file is KEPT as
  history; `evidence/w26283-2026-08-27-review-corrections.txt` carries the
  sentences it lost, and the `check_input_pair` ownership correction.
- [recorded, my error] I re-asked the settled test-replacement approval as
  M28300 without reading this Work's own thread, where message 27064 already
  granted it. Withdrawn at M28315. Only `baton.decide` can dispose the
  obligation, so the Work reads `phase=block` on it until they do.

## 2026-08-28 — independent re-review changes requested

- [confirmed] The prior FIFO-race correction, bounded regression, approved
  moving-tree expectation, documentation correction, and 13th mutation are
  sound.
- [required] Enforce global and declared entry ceilings before reading the
  file that crosses them.
- [required] Bound each descriptor read to the smaller remaining global and
  declared byte allowance plus one byte. A size observed by `fstat` is not a
  bound on a worker-controlled regular file that can grow while open.
- [required] Preserve the existing global `policy/denied` versus declared
  `integrity/limit` taxonomy and global-first precedence when both cross.
- [required] Add bounded grow-after-`fstat` and read-before-entry regressions,
  plus mutations removing both guards. Evidence and exact required boundary:
  `review-2026-08-28T04-15-23Z.md` and
  `evidence/w26283-review-read-bounds.py`.
- [done, in the section below] Re-run focused custody tests, the expanded
  mutation harness, the real-engine suite, and the accepted full-tree
  baseline, then return for independent re-review.

## 2026-08-28 — re-review corrections applied

- [done] The entry ceilings run BEFORE the file that crosses them is opened.
  `_entry_ceilings` is one owner for both the global and the declared count,
  called from `copied_manifest` and from `directory_manifest`, which carried
  the identical late check.
- [done] The read is bounded. `_byte_allowance` returns what is left of the
  smaller remaining global/declared ceiling and `_read_all` takes at most that
  plus one byte, so a file grown after `fstat` cannot widen the work, the
  memory or the time. `_read_exactly` now REQUIRES that allowance: a reader
  with no bound is the defect, so it is not defaultable.
- [done] Taxonomy and precedence preserved. Global crossings stay
  `policy/denied`, declared crossings stay `integrity/limit`, and an equal
  crossing still answers globally — asserted for both ceilings rather than
  assumed.
- [done] Regressions. Eight cases in
  `ACeilingBoundsTheWorkItRefuses`: the crossing file is never read (declared,
  global, and on the measuring pass), an endlessly growing file is bounded
  (global, declared, and on the measuring pass), and both equal crossings
  still answer as policy. The growth cases bound themselves with `SIGALRM`
  for the same reason the post-listing FIFO case does — unbounded, they do not
  terminate at all.
- [done] Mutations. Three added: the entry ceiling moved back after the read
  in each of the two passes, and the descriptor read ignoring its allowance.
  The four existing ceiling anchors were re-pointed at the shared helpers.
  The harness is now **16 of 16 caught**.
- [done] Evidence. `evidence/w26283-read-bounds-corrected.py` exits 0 —
  9 bytes across 9 reads at ceiling 8, `['a']` read before the entry refusal,
  and the endless-growth probe refusing `policy/denied` in 9 bytes. The
  reviewer's own file is kept unedited; its entry probe interposes a
  three-parameter wrapper on `_read_exactly` and needs `**rest` now that the
  required correction gave that function its allowance operand.
- [done] Gates re-run: `test_workspaces` 57, `test_workspaces`+`test_sealing`
  103, the real-engine custody suite 8, `tools/parallel_test.py` 1518 tests
  with the accepted six `test_boundary_inventory` failures, and `--phase
  serial` 97 tests 0 failures.

## 2026-08-28 — independent third review

- [signed off] The prior entry-order and bounded-read P1 findings are corrected.
  Focused custody and adjacent suites are green, the canonical parallel run
  has only the accepted six boundary-inventory failures, and no new review
  finding remains. See `review-2026-08-28T04-56-33Z.md`.
