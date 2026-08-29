# Plan

1. Revalidate the W6 observation against current workspace creation and worker
   identity code.
2. Pin the least-privilege ownership/mode boundary.
3. Correct delivery and add real-container positive and negative regressions.
4. Run focused and package gates, then return for independent review.


## 2026-08-28 — implemented

1. [done] Revalidated inside the real composed container:
   `evidence/w33935-revalidation-2026-08-28.txt`. Two facts the finding did not
   have — the `/input` root is `0o775` and IS traversable, so only the files
   were unreadable; and the root refuses a write with `EROFS` from the
   read-only bind rather than from any mode, which is what makes a
   world-readable file safe here.
2. [done] `READ_ONLY_FILE` 0o444 and `READ_ONLY_DIR` 0o555 — the same two
   values `launch.py` already uses, held to each other by a case. Plus the
   half the constant does not fix: the mode is now ESTABLISHED with `fchmod`
   on the descriptor rather than requested at creation, where the umask ate it.
3. [done] `tests/manager/test_input_delivery.py`, 7 cases: positive read by
   uid 65532, write denial asked of both the engine and the container,
   restart/retry reuse through a second incarnation, sibling isolation, and
   the umask regression. Measured by removal, 6 of 6.
4. [done] Focused and package gates; the accepted boundary-inventory baseline
   is unchanged. [next] Independent review.

Not this Work's, and re-measured as still present: `/workspace` is `0o775`
uid 1000 and the container at 65532 cannot write it, so a worker cannot write
the outputs it declares. It needs an owner.

## 2026-08-28 — independent review changes requested

- [done] The two files are established at `0444` independently of umask and
  submitted real-container evidence shows the worker reading exact bytes.
- [required] Apply `READ_ONLY_DIR` to the completed host input root; the
  current constant is unused and the actual root remains replaceable at
  `0775`.
- [required] Replace the constant-only directory mutation with behavioral
  create/unlink/rename/replacement denial, plus cleanup/retry thawing of only
  the exact owned root.
- [operational limitation] This reviewer can run the daemon-free cases but is
  denied Docker-daemon access and did not request prohibited escalation.

## 2026-08-28 — review answered

2b. [done] The exact input root mode is established as `READ_ONLY_DIR` after
    the second document is installed. `0555` keeps the worker's traversal,
    which the real-container case measures.
3b. [done] `TheInputRootIsFrozenAndNotOnlyItsFiles`: create, unlink, rename,
    replace and replace-in-place denied on the host; the mode exact under every
    umask; cleanup removes a frozen root and thaws nothing else; recomposition
    still refused by its own rule. The class refuses to run as root.
4b. [done] The mutation that measured nothing is replaced by four that move the
    delivery — 9 of 9 — and one of those four was itself re-targeted after the
    harness reported it uncaught.

## 2026-08-28 — independent re-review changes requested

- [required] Freeze the completed input root's directory entry at its parent
  boundary. The current `0555` root protects its children, but its `0775`
  assignment-home parent still permits the whole root to be renamed and a
  writable replacement installed at the canonical path.
- [required] Add host behavioral cases for root rename and root replacement,
  proving the canonical path and exact bytes do not move. Preserve worker
  traversal/readability and the existing child create/unlink/rename denials.
- [required] Prove cleanup deliberately thaws only the exact owned assignment
  home and leaves a sibling assignment's parent and input root frozen; preserve
  retry/restart reuse.
- [required] Add a removal mutation for the parent-boundary freeze, rerun the
  real-container gate where Docker authority exists, and return for re-review.
- [operational limitation] This reviewer independently passed all seven
  daemon-free cases. The required Docker class remains denied access to
  `/var/run/docker.sock`; standing managed-turn policy forbids escalation.

## 2026-08-28 — re-review answered

2c. [done] The assignment home is frozen after every entry it will hold is
    provisioned, which is the only boundary that governs the `inputs` entry
    itself. `HOME_ENTRIES` is held to the two components that own the other
    three siblings.
3c. [done] `TheRootsOwnENTRYIsFrozenToo`: rename aside, new root at the
    canonical path, rename another directory onto it, remove, and add a sibling
    — each denied; the path and documents unmoved; what the frozen home still
    permits; cleanup reaching exactly one home.
4c. [done] 11 of 11, with the parent freeze measured by removal and two earlier
    mutations re-anchored after their lines moved.

## 2026-08-28 — independent second re-review changes requested

- [done] Preserve the valid correction: the frozen assignment home now denies
  rename/replacement of its `inputs` child, the declared sibling inventory is
  provisioned before closure, and cleanup handles a directory-only home. All
  12 daemon-free delivery/layout cases pass independently.
- [required] Resolve the assignment home's own stable-name boundary. Workspace
  storage remains writable, so the whole `0555` home can be renamed and a
  writable replacement installed at the canonical input path; the retained
  home-entry reproduction demonstrates exact replacement bytes.
- [required] Do not repeat the parent-mode correction recursively. Pin either
  a custody mechanism whose stable identity does not depend on a name in a
  same-uid writable directory, including its allocation/race/cleanup contract,
  or an explicit approver narrowing of the recorded non-replaceability
  acceptance.
- [required] Add a behavioral regression at the assignment-home entry, plus
  positive allocation of another assignment and cleanup/retry/race coverage
  for whichever boundary is ruled. Measure removal of the actual authority
  mechanism and rerun the real-container gate where Docker authority exists.
- [operational limitation] This reviewer can run the daemon-free cases but is
  denied Docker-daemon access and did not request prohibited escalation.

## 2026-08-28 — the ruled trust model

5. [done] Approver M34768 narrowed non-replaceability to the untrusted worker
   and to accidental manager corruption, and retired the inode proposal. The
   six named properties are verified by `TheRuledTrustModel`; the collision
   refusal sits at publication, because a guard in `assignment_workspace`
   refuses the restart path and the suite proved it.
6. [next] Independent review.

## 2026-08-28 — independent third re-review changes requested

- [done] Preserve approver M34768's narrowed trust model and the readable,
  read-only, frozen input delivery corrections. The focused daemon-free suite
  otherwise passes independently.
- [required] Implement the ruling's exclusive per-attempt directory creation.
  Separate first allocation from authorized same-attempt restart lookup, or
  carry equivalent durable ownership evidence; do not adopt an arbitrary
  pre-existing home through `exist_ok=True`.
- [required] Refuse a contained symlink/alias or stale collision that would
  make two attempts answer with the same input root. Keep clean concurrent
  allocation and legitimate manager-restart adoption green.
- [required] Retain the failing reviewer case
  `TheRuledTrustModel.test_a_colliding_home_cannot_alias_another_attempts_root`,
  add the corresponding first-allocation/reopen race coverage, and preserve
  exact-attempt cleanup/retry and sibling isolation.
- [operational limitation] This managed reviewer ran 78 daemon-free focused
  cases but remains denied Docker-daemon access and did not request prohibited
  escalation. The implementer's real-Docker evidence was not independently
  rerun.

## 2026-08-28 — independent fourth re-review changes requested

- [done] The retained child-entry alias regression now passes, and the added
  regular-file, dangling-link, outside-link and restart cases are green.
- [required] Refuse an attempt home that is itself a symlink or resolves away
  from its exact path. Do this before its resolved location becomes the anchor
  against which the children are checked.
- [required] Retain
  `TheRuledTrustModel.test_a_colliding_home_cannot_alias_another_attempts_home`
  and keep legitimate restart lookup, concurrent distinct allocation,
  cleanup/retry, sibling isolation and readable/read-only delivery green.
- [operational limitation] The focused daemon-free set ran 83 cases: 82 passed
  and the new whole-home collision regression failed. Docker remains denied to
  this managed reviewer; no escalation was requested.

## 2026-08-28 — exclusive allocation

5b. [done] Exclusive first allocation separated from restart lookup: an
    existing entry must be this attempt's own directory, so aliases, stale
    files and dangling links fail closed while reopening still answers.
6.  [next] Independent re-review.

## 2026-08-28 — the anchor

5c. [done] The attempt home carries the same no-link/exact-path proof as its
    entries, applied before it becomes their anchor. Aliased homes of every
    shape fail closed; reopening a real home at its own path still answers.

## 2026-08-28 — independent fifth re-review changes requested

- [done] Exact-home and child aliases are refused; all retained structural and
  sequential-reopen regressions pass.
- [required] Close the `lexists`/`makedirs` race for the attempt home and every
  child entry. A creation loser must either validate/reopen the exact owned
  directory or raise `ContractRefusal`, never leak `FileExistsError`.
- [required] Retain
  `TheRuledTrustModel.test_first_allocation_race_answers_or_refuses_in_contract`
  and add the equivalent child-entry collision race. Preserve distinct-attempt
  concurrency, restart adoption, cleanup/retry and sibling isolation.
- [operational limitation] 85 daemon-free focused cases ran: 84 passed and the
  new allocation-race contract case failed. Docker remains unavailable to this
  managed reviewer; no escalation was requested.

## 2026-08-28 — the race

5d. [done] Create-or-prove is one owned operation at both levels; a lost race
    reopens in contract and no raw filesystem fault escapes. Race cases at the
    new seam for the home and the child, plus the reopen outcome.

## 2026-08-28 — independent sixth re-review

- [done] Home and child `os.mkdir` races pass without raw faults; both callers
  reopen the same exact roots.
- [done] All 88 focused daemon-free allocation, alias, restart, cleanup,
  isolation and readable/read-only delivery cases pass independently.
- [done] Scoped `git diff --check` is clean.
- [done] Signed off. Docker was not independently rerun because this managed
  reviewer lacks daemon access; the implementer's retained real-Docker and
  broader engine evidence remains the available certification.
