# W156162 — candidate provenance, 29 paths, at a pinned revision

Gathered read-only at claim 160341 by `provenance-160341.py`, retained beside
this note; the machine figures are in `provenance-160341.json`, which now carries
a `summary` block as well as the per-path rows.

**Revision pinned: `f3fc9e12cc89bebf9524cd173103df7af67d5212`.** Review
2026-09-13T11:49:41Z made the point the earlier packets left implicit: equal base
hashes prove equality **at the enumerated paths**, not that a repository `HEAD`
could not have moved elsewhere. The generator now reads and records the actual
revision rather than inferring stability from the rows.

**No Git mutation.** Every invocation reads: `rev-parse`, `show`,
`diff --numstat`, `diff -U0`. Nothing was removed, imported, absorbed or excised.

`PROVENANCE-158092.md` (27 paths), `PROVENANCE-159612.md` and
`PROVENANCE-160261.md` (29 paths) and their JSON are **retained unchanged**. This
supersedes them without replacing them and is generated over the same path list,
so all four compare path by path.

## The shape of the candidate, labelled correctly

**29 paths: 6 new and 23 tracked-and-modified.** No path in the list is
unmodified, and none is missing from the worktree.

The second correction from that review is in the figures themselves. These
totals are for the **tracked modified paths only** — a new file has no base to
diff against, so the generator leaves its numstat and hunk count empty and none
of its lines appear here:

| Figure | Value | Covers |
| --- | ---: | --- |
| Added lines | **2569** | the 23 tracked modified paths |
| Removed lines | **132** | the 23 tracked modified paths |
| Hunks at `-U0` | **156** | the 23 tracked modified paths |
| New-file bytes | **423727** | the 6 new paths, which have no hunks at all |

The six new paths are `src/baton_v12/job_manager/execution_limits.py`, the two
`tests/job_manager/execution_limits_fixtures/` files, and the three
`test_execution_limits.py` modules under `tests/job_manager`, `tests/manager` and
`tests/tools`.

## What changed since the 160261 packet

Three paths, and every base hash is unchanged:

| Path under `v12/python` | Bytes | SHA256 |
| --- | ---: | --- |
| `tools/stage_execution.py` | 277475 | `ca15f08180556d3ebe310c6ad7e0a0548d925bdd2ebf8b6bff04e7dab793db9a` |
| `tests/tools/test_execution_limits.py` | 224003 | `4b90528c3a74ad847ec5ae85ead1a1b660df5315838a365e43891ad5d985dd6b` |
| `DEPLOYMENT.md` | 68484 | `79f2925847cc74be8e96805069f860904fe39d60d47bdd3fcfa838305bcd8a0e` |

The source change is **comment-only**: two passages that described the
pre-durable implementation. The test change is this Work's own scenario and its
corrected docstring. The document change is the operator-facing half of the same
correction.

## The documentation defect this packet corrects

The previous packet carried my own contradiction into the inventory. `DEPLOYMENT.md`
says at one point that the failure custody is durable and that reopened serving
runs no command, and the paragraph I added said there is **no** owner-recorded
durable outcome and that a fresh process **will** run the command once more. The
latter is false for the accepted retained-failure path, and it is corrected in
all three places rather than only in the prose:

- **The document** now distinguishes the two: the OUTCOME is in owner custody —
  a causal failure settles the result `blocked`, a post-import failure holds the
  target — and that is what makes a reopen quiet. The in-process retention is an
  **additional cache** that stops the repeat inside one composition.
- **The source** comments said a fresh process or a reopen would attempt the
  command again. They now say what is actually missing: an owner record of the
  **attempt itself**, so a process that dies between the command's failure and
  the owner's record leaves nothing to read. That is a crash-before-record limit,
  not an exactly-once guarantee.
- **The test** whose name and docstring described that pre-durable behaviour —
  and never drove it — is renamed to what it asserts:
  `test_the_retained_failure_is_keyed_by_the_work_it_is_about`.

## Correction 159640, carried and updated

`PROVENANCE-REVIEW-159640.md` corrected my prose counts and they stand: **6 new**,
**16 modified product-and-document** paths and **7 existing tests** — five of
those Job tests under owner ruling M157653, which approved exactly the changes in
`PROVENANCE-REVIEW-158105.md`, and two under the PLAN-scheduled setup-only
authority.

The two overlapping files at the default context the correction used:

| File | Hunks | This Work's | W71879's |
| --- | ---: | ---: | ---: |
| `tools/stage_execution.py` | 19 | 18 | 1 |
| `tests/tools/test_stage_execution.py` | 6 | 5 | 1 |

`test_stage_execution.py` is **unchanged since 159612** — same bytes, same hash —
so the correction's figure for it stands exactly. At `-U0` the same foreign change
reads as two adjacent hunks because its docstring and its code are separated by
unchanged lines; that is a context-width artefact and is stated so the two numbers
here do not look like a discrepancy.

## The foreign change, attributed and not removed

- `tools/stage_execution.py` — the read-only integration observation dropping a
  runtime precondition, so a reconciled completion with no runtime reaches the
  outer observer.
- `tests/tools/test_stage_execution.py` —
  `test_readonly_reconciled_completion_without_runtime_reaches_outer_observer`,
  the test for it.

**The change is W71879's**, per the reviewer's attribution at
2026-09-13T05:44:15Z: the completion-observation candidate 153138, whose methods
and base bytes match, and whose method hashes the reviewer's own audits have
re-verified since. It is **reported, not removed**.

**Separability, and its limit.** The two hunks are one change and its test,
textually separable, with no lines overlapping this Work's. That is a statement
about TEXT, not dependency: **no excised tree has been built or run**, so it is
uncertified that removing them leaves a passing tree — the foreign test would
fail without its source hunk.

## Integration preflight — still outstanding

This is a reviewed working-tree candidate, **not an integration proposal**. Its
preflight remains: the candidate and base revisions pinned (the base is pinned
above; the candidate is a worktree, not a commit), the path set and its authority
scope checked, the existing-test authority carried with it, and the two W71879
hunks disposed of by their owner. None of that is claimed here, and **no
full-feature or import sign-off is implied by this packet**.
