# W156162 — candidate provenance, 29 paths, at a pinned revision

Gathered read-only at claim 160468 by `provenance-160468.py`, retained beside
this note; the machine figures, with a `summary` block, are in
`provenance-160468.json`.

**Revision pinned: `f3fc9e12cc89bebf9524cd173103df7af67d5212`** — read, not
inferred. Equal base hashes prove equality **at the enumerated paths**, not that
a repository `HEAD` could not have moved elsewhere.

**No Git mutation.** Every invocation reads: `rev-parse`, `show`,
`diff --numstat`, `diff -U0`. Nothing was removed, imported, absorbed or excised.

`PROVENANCE-158092.md` (27 paths) and `PROVENANCE-159612.md`,
`PROVENANCE-160261.md` and `PROVENANCE-160341.md` (29 paths), with their JSON,
are **retained unchanged**. This supersedes them without replacing them, over
the same path list, so all five compare path by path.

## The shape of the candidate, labelled

**29 paths: 6 new and 23 tracked-and-modified.** None unmodified, none missing
from the worktree.

These totals are for the **tracked modified paths only** — a new file has no base
to diff against, so the generator leaves its numstat and hunk count empty and
none of its lines appear here:

| Figure | Value | Covers |
| --- | ---: | --- |
| Added lines | **2587** | the 23 tracked modified paths |
| Removed lines | **132** | the 23 tracked modified paths |
| Hunks at `-U0` | **156** | the 23 tracked modified paths |
| New-file bytes | **424470** | the 6 new paths, which have no hunks at all |

## What changed since the 160341 packet

Three paths; every base hash is unchanged:

| Path under `v12/python` | Bytes | SHA256 |
| --- | ---: | --- |
| `tools/stage_execution.py` | 277833 | `02d83d92b6f9b0d44f42813239fb591b5d11fc13b35514665d5b4d36f6571d81` |
| `tests/tools/test_execution_limits.py` | 224746 | `66b1954ebd83781031a48170122a5014fbb63e29f4df3519300e8237d371071f` |
| `DEPLOYMENT.md` | 69337 | `0b52ed396755b816e730b8d6ebde3f0c61eafd81708fd5ed2636dc6fc96f6c7f` |

**The source change is comment-only**, and so is the constant beside it: no
execution path, successful or failed, behaves differently.

## The explanation this packet corrects, as a whole

The previous packet corrected the operator document but left the source
explanation contradicting itself: a paragraph saying the owner contract was
missing, that neither owner could represent a no-status failure, proposing a
`status: null` variant and calling `reconciliation` and `execution` out of
scope — with my correction appended *underneath* rather than retiring it.

It is rewritten as one explanation:

- **The contract exists and both owners carry it.** Owner ruling M157653
  approved the tagged closed answer; `reconciliation` admits it, validates it
  against the configured owner's own expectations, settles the result `blocked`
  and never authorizes it, and `execution` adopts the post-import form and holds
  the target. No exit status is invented and neither owner needs one.
- **So the outcome is durable**, and that is what makes a reopen quiet. The
  in-process retention is an **additional cache** for the measured
  twelve-runs-in-four-ticks repeat inside one composition.
- **What is still missing** is two halves of one narrower gap: no owner records
  the **attempt itself** (crash-before-record, not exactly-once), and a host
  failure leaves **no terminal account for the stage** — the reconciled branch
  answers `held` with no runtime, the scheduler settles capacity from episode
  endings and completions, so the stage stays `exceptional` and holds its
  integration capacity.

`HOST_OBSERVATION_CONTRACT` now names those two rather than the delivered
durability, `_host_retention` no longer points at it as what would make the
outcome durable, the comment beside the subprocess matches, and `DEPLOYMENT.md`
states both limits in operator terms — including what the capacity hold looks
like from outside and why `recover` reports nothing.

Two stale test commentaries went with it: the two-Job seam case no longer implies
that a borrowed fixture without a helper is an authority barrier (the third-Job
helper is in this Work's own test), and `_two_failed_results` keeps its first
diagnosis explicitly **historical** — the engine flag was my first reading, and
the same probe disproves it.

## Correction 159640, carried

**6 new**, **16 modified product-and-document** paths, **7 existing tests** —
five of those Job tests under owner ruling M157653, which approved exactly the
changes in `PROVENANCE-REVIEW-158105.md`, and two under the PLAN-scheduled
setup-only authority.

| File | Hunks (default context) | This Work's | W71879's |
| --- | ---: | ---: | ---: |
| `tools/stage_execution.py` | 19 | 18 | 1 |
| `tests/tools/test_stage_execution.py` | 6 | 5 | 1 |

`test_stage_execution.py` is unchanged since 159612. At `-U0` the foreign change
reads as two adjacent hunks, a context-width artefact stated here so the two
numbers do not look like a discrepancy.

## The foreign change, attributed and not removed

`tools/stage_execution.py` — the read-only integration observation dropping a
runtime precondition; `tests/tools/test_stage_execution.py` —
`test_readonly_reconciled_completion_without_runtime_reaches_outer_observer`.

**The change is W71879's**, per the reviewer's attribution at
2026-09-13T05:44:15Z (completion-observation candidate 153138), re-verified by
their later audits. It is **reported, not removed**. The two hunks are one change
and its test, textually separable with no overlapping lines — a statement about
TEXT and not dependency: **no excised tree has been built or run**.

## Integration preflight — still outstanding

A reviewed working-tree candidate, **not an integration proposal**. Its preflight
remains: the base revision pinned (above) and the candidate still a worktree
rather than a commit, the path set and its authority scope checked, the
existing-test authority carried with it, and the two W71879 hunks disposed of by
their owner. **No full-feature or import sign-off is implied.**
