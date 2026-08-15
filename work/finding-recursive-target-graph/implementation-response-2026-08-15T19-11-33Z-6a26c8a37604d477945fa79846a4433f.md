# R99 implemented — and a contradiction in its reproduction harness, reported for ruling

In reply to review message `6a26c8a37604d477945fa79846a4433f`
(review-2026-08-15T19-07-47Z.md, claim
`8ca0c910ecf9c1f7e6bc0514823a3a41`).

## What was done

The R99 ruling is implemented exactly as prescribed: every managed
directory is created with `os.mkdir(name, dir_fd=parent)` through the
held O_NOFOLLOW parent fd — never a pathname — and the
created-or-existing child is validated through that same parent fd.
The `rmdir` repair is REMOVED entirely; there is no cleanup delete on
any path. A parent unlinked after its fd was opened makes the
fd-relative mkdir itself fail (verified: ENOENT) and the operation
refuses with the structured created-so-far report, touching nothing
outside the root.

I did not modify any reviewer-authored regression, and I am stopping
here because the ruled primitive and the current reproduction harness
contradict each other. Per the standing discipline I am reporting the
contradiction for ruling instead of choosing.

## The contradiction

The three mkdir-injecting regressions arm their faults by
intercepting `os.mkdir` and comparing the first argument against
ABSOLUTE paths (`base/tmpl`, `base/work`, `base/work/open`). That
presumes path-based creation:

1. Under the ruled fd-relative creation, mkdir receives the RELATIVE
   name (`"tmpl"`, `"work"`, `"open"`) with `dir_fd=`. The absolute
   comparisons never match, no race or fault is ever injected, and
   bootstrap legitimately succeeds — so
   `test_bootstrap_refuses_a_parent_symlink_inserted_after_validation`,
   `test_bootstrap_reports_the_exact_partial_creation_set`, and
   `test_bootstrap_creates_nested_directories_through_the_no_follow_chain`
   now fail DID NOT RAISE. Observed focused result: 13 passed, these
   3 failed — a structural artifact of the injection seam, not an
   escape.
2. No absolute-path variant can satisfy the nested regression either,
   because its intercept ITSELF performs the outside creation: on any
   `os.mkdir(base/work/open)` call it swaps the parent and then calls
   the real mkdir with that same absolute pathname, which follows the
   symlink and creates `outside/open` (POSIX ignores `dir_fd` for
   absolute paths — verified empirically). From that moment the test
   can only end with `outside` non-empty, or empty via a delete that
   its own `deleted == []` assertion forbids. Every implementation
   fails one arm; the previous rounds observed exactly those two
   failure modes.

So: fd-relative creation (the ruled, correct boundary) makes the
injection points unreachable; path-based creation makes the nested
regression self-defeating. The product contract and the harness
cannot both hold as written.

## Proposed resolution (for your ruling, not applied)

Keep the R99 fd-relative implementation, and re-key the three
regressions' injection seams to the fd-relative boundary, e.g.:

- parent-symlink EEXIST case: intercept `mkdir` where
  `path == "tmpl" and "dir_fd" in kwargs`, plant the symlink at the
  absolute path via the test's own primitives, raise
  `FileExistsError`; the chain revalidation refuses ELOOP, nothing
  outside, nothing deleted.
- partial-set case: intercept `("work", dir_fd)` and raise
  `PermissionError`; the structured report names `tmpl`.
- nested-race case: intercept `("open", dir_fd)`, unlink/swap the
  parent via absolute paths, then call the real
  `mkdir("open", dir_fd=...)` — it fails ENOENT against the unlinked
  parent (verified), the operation refuses, `outside` stays empty
  with no delete, and `deleted == []` holds.

If you prefer a different seam (e.g. a named product-level
`_mkdir_at(parent_fd, name)` the tests patch directly), the
implementation is one rename away.

## Status

`src/baton_work/project.py` carries the R99-conformant creation (no
cleanup delete anywhere). Focused: 13/16 with the three structural
harness failures above; the full gate was NOT claimed green — it
cannot be while the harness contradiction stands. All other Slice B
suites (resolver strictness, short writes, WF-14/WF-15) are
unaffected. Awaiting your ruling; production operations remain held
for Slawomir.
