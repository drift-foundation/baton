# W156162 — candidate provenance, 29 paths

Gathered read-only at claim 160261 by `provenance-160261.py`, which is retained
beside this note; the machine figures are in `provenance-160261.json` — per path,
its bytes and SHA256 at `HEAD`, its candidate bytes and SHA256, its added and
removed line counts, and its hunk count at `-U0`.

**No Git mutation.** Every invocation reads: `show`, `diff --numstat`,
`diff -U0`. Nothing was removed, imported or absorbed to make this packet look
clean, and no file was excised to improve a count.

`PROVENANCE-158092.md` / `provenance-158092.json` (27 paths, before owner ruling
M157653) and `PROVENANCE-159612.md` / `provenance-159612.json` (29 paths) are
**retained unchanged**. This supersedes them without replacing them, and it is
generated over the same path list so the three can be compared path by path
rather than re-derived from a working tree that other Works also touch.

## The shape of the candidate

**29 paths. 6 are new** — untracked at `HEAD`, so they have no base and no
hunks:

| New path under `v12/python` | Bytes | SHA256 |
| --- | ---: | --- |
| `src/baton_v12/job_manager/execution_limits.py` | 11558 | `073ea7104df1aa4c…` |
| `tests/job_manager/execution_limits_fixtures/PROVENANCE.md` | 2994 | `4a6cf1ca5c4a165b…` |
| `tests/job_manager/execution_limits_fixtures/golden-schema4.sqlite3` | 135168 | `bb9fa3aba268f461…` |
| `tests/job_manager/test_execution_limits.py` | 32824 | `2271ef93151b5a33…` |
| `tests/manager/test_execution_limits.py` | 17180 | `95087d91d67b89b4…` |
| `tests/tools/test_execution_limits.py` | 205812 | `18d7729c138d3b96…` |

The remaining **23 are modified**, and across the whole candidate that is
**+2548 / −132 lines in 156 hunks** at `-U0`.

**Every base hash is identical to the 159612 packet's**, so `HEAD` has not moved
under this candidate and the two packets are comparable line for line.

## What changed since the 159612 packet

Exactly three paths:

| Path under `v12/python` | Then → now | Why |
| --- | --- | --- |
| `tools/stage_execution.py` | `3ee83301…` → `633ce911…` | the runtime-owned cleanup lifecycle for a scratch tree that survived its disposal |
| `tests/tools/test_execution_limits.py` | `39c59b88…` → `18d7729c…` | this Work's own regressions, now 139 |
| `DEPLOYMENT.md` | `84f5dee1…` → `6c288f84…` | the prose corrections below |

Nothing else moved. In particular **no Job Manager, Worker Manager or
`integration` source changed** in those claims.

## Correction 159640, carried and updated rather than restated

`PROVENANCE-REVIEW-159640.md` corrected my prose counts and they are carried
here: **6 new**, **16 modified product-and-document** paths and **7 existing
tests**. Five of those existing Job tests changed expectations **under owner
ruling M157653**, which approved exactly the changes listed in
`PROVENANCE-REVIEW-158105.md`; the other two changed under the PLAN-scheduled
setup-only authority.

The two overlapping files, at the default context the correction used:

| File | Hunks | This Work's | W71879's |
| --- | ---: | ---: | ---: |
| `tools/stage_execution.py` | **19** (was 18) | 18 | 1 |
| `tests/tools/test_stage_execution.py` | **6** | 5 | 1 |

The one added `stage_execution.py` hunk since the correction is this Work's own:
the scratch registry and its release. `test_stage_execution.py` is **unchanged
since 159612** — same bytes, same hash, same 6 hunks — so the correction's figure
for it stands exactly.

At `-U0` the same foreign change reads as **two** adjacent hunks rather than one,
because its docstring and its code are separated by unchanged lines. That is a
counting artefact of the context width and is stated here so the two numbers in
this packet do not look like a discrepancy.

## The foreign change, attributed and not removed

- `tools/stage_execution.py` — one foreign hunk: the read-only integration
  observation dropping a runtime precondition, so a reconciled completion with no
  runtime reaches the outer observer.
- `tests/tools/test_stage_execution.py` — one foreign hunk:
  `test_readonly_reconciled_completion_without_runtime_reaches_outer_observer`,
  the test for the source hunk above.

**The change is W71879's**, per the reviewer's attribution at
2026-09-13T05:44:15Z: the completion-observation candidate 153138, whose methods
and base bytes match. It is **reported, not removed**.

**Separability, and what remains uncertified.** The two foreign hunks are one
change and its test, textually separable, with no lines overlapping this Work's.
That is a statement about TEXT and not about dependency: **no excised tree has
been built or run**, so it is uncertified that removing them leaves a passing
tree — the foreign test would certainly fail without its source hunk.

## The prose this packet corrects

`DEPLOYMENT.md` carried two statements that substantive work has overtaken, and
they are corrected with that work rather than left for a reader to discover:

1. It said a surviving temporary materialization is **named in the diagnostic**
   and stopped there. It now says the deployment **owns** it: the path and the
   diagnosis that named it are registered, released before the other handles, a
   path that survives the release too is reported with its exact location, and
   repeating the ordinary close after the cause is fixed disposes of it. The
   diagnosis is never rewritten by the cleanup.
2. It said the closed-and-reopened replay of the **post-import target hold** was
   *not yet proved*. It is proved: both holds are driven across a real reopen,
   read through each owner's own public readers, with the command,
   materialization and hold counts all at one.

And one limitation is now stated where a reader will meet it: **the retention is
this process's**, not an owner-recorded durable outcome — `HOST_OBSERVATION_CONTRACT`
still says what would make it durable. A new section also records what an operator
**cannot** do to a host hold, which is the measured recovery boundary rather than
a claim that no public capability exists.

## Integration preflight — still outstanding

This is a reviewed working-tree candidate, **not an integration proposal**. Before
it becomes one, its own preflight remains: the candidate and base revisions
pinned, the path set and its authority scope checked, the existing-test authority
carried with it, and the two W71879 hunks disposed of by their owner — landed with
it, excised and re-verified, or attributed in the proposal. None of that is
claimed here, and **no full-feature or import sign-off is implied by this packet**.
