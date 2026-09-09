# Progress

No runtime implementation has started. This leaf was created from the parent's
diagnostic evidence under baton.tuner claim119463. FINDING.md and PLAN.md name
the proposed bounded disposition and required actual acceptance; runtime/API
changes remain unauthorized pending that disposition. The eventual assigned
implementation author appends progress here under its own successful claim.

## 2026-09-08 — publication repair, baton.tuner response to obligation119481

The Work was created before its bound files were written, and the reviewer
correctly stopped when readiness arrived during that interval. FINDING.md,
PLAN.md and this initial PROGRESS.md now exist at the exact binding. The nine
direct observations and current catalog/source hashes are retained in the
parent evidence/revalidation-119463.json, with its reproduction alongside.
No runtime/API/test review is presumed from the earlier incomplete publication.

## 2026-09-08 — W119476 claim119642 — baton.claude — in progress

**Revalidation before any edit.** The approved ruling is M119574 over
`review-2026-09-08T13-35-52Z.md`, and I re-checked it against the current tree
rather than acting on the record alone.

The nine retained observations reproduce exactly, at the unchanged source:
a valid five-member mapping returns the four-part projection; a null principal
gives `refused/precondition`; `[]` raises a raw `TypeError` and `{}` a raw
`KeyError`; and a list in each of the five consumed fields is accepted, four of
them appearing unchanged in the returned reference while a malformed
`runtime_attempt_id` is ignored on the active path.

**Caller compatibility audited before deciding the contract is safe.** Every
call site was read, not assumed:

- production — `attempts.request_runtime_start`, `lanes.runtime_lane` and the
  two `intake` release sites — passes a row from `_require_attempt`/`_attempt_of`,
  and both come through `boundaries.row`, which answers a plain `dict` carrying
  exactly `ATTEMPT_COLUMNS`. The approved contract accepts that unchanged;
- `tests/manager/test_runtime_lane.py` passes full row dicts, including
  `dict(row, assignment_participant=...)` and a real unactivated row whose
  Work, Authority and scope are all null;
- `tests/manager/test_boundary_inventory.py` passes `attempt_row_of`, which is
  the same full-row shape;
- `tests/manager/test_text_sweep.py` names `lane_reference` in its surface table
  with a two-member sample and **declares no text operands for it**, so that
  sample is never invoked — only the name-completeness case reads the entry.

No caller passes a partial mapping, so the five-required/known-optional contract
needs no internal unchecked seam. That is what the review predicted; I checked
it rather than inheriting it.

### Verification question and budget, recorded before any run

**Question:** does the validated public boundary refuse every malformed direct
input at `integrity/schema` while leaving all four production callers, the
existing lane identity/occupancy/restart/contention/cleanup behaviour and the
inactive-attempt refusal exactly as they were? No retained result answers it —
the diagnostic measured the gap, not a correction.

**Scope and budget:** the new focused class first, then
`tests.manager.test_runtime_lane` once for lifecycle compatibility, then the
three other modules that call this helper (`test_boundary_inventory`,
`test_text_sweep`, `test_secrets`) because they are the ones a changed public
refusal could break. Proposed budget 30 seconds for the first two as the review
set; the three caller modules are added because a public contract change is
exactly the case where "the callers I audited statically" needs an executed
answer. No daemon, no ordinary suite, no full inventory sweep.

### Delivered: the validated public boundary and its controls

**Exactly the two approved paths changed, and nothing else.**

| Path relative to `v12/python` | SHA-256 |
| --- | --- |
| `src/baton_v12/worker_manager/lanes.py` | `f2a086de468c84d0cd7eb3cbcedec55c2cd12415a051b93bdcc8342341e2f21c` |
| `tests/manager/test_runtime_lane.py` | `291915203a8321824f96c26bde2b50b09911396be047b2bab3628d90299e7a06` |

The test change is **purely additive** — no existing line was removed, and the
only edits outside the appended classes are two import lines. Exports, the
`__all__` lists, `_lane_id`, occupancy, release, `runtime_lane`, `_adopted` and
every production call site are untouched.

**The source correction, exactly the approved contract.** `lane_reference` now
owns its input through `boundaries.document`, requiring the five consumed
members and naming the remaining `ATTEMPT_COLUMNS` as optional metadata, so a
complete attempt row — the shape all four production callers send — is accepted
whole and an unknown member is refused rather than ignored. Each consumed member
is then proved by its own column's existing rule: `runtime_attempt_id` and
`work_id` by `identity`, `authority_uuid`, `assignment_principal` and
`assignment_scope` by `text`. The projection is the same four values in a fresh
dict; no Authority is resolved, no store is consulted and the lane-id derivation
is unchanged.

Two orderings are the contract rather than incidental:

- every non-null consumed member is proved BEFORE the activation branch, so
  malformed input is `integrity/schema` even when the attempt is also
  unactivated. A real unactivated row — null Work, Authority, scope AND
  principal — still reaches the unchanged `refused/precondition` and is not
  reported as malformed;
- an input naming a principal but missing one of the other three parts is
  `integrity/schema`. The table's own CHECK keeps the four activation columns
  together, so three quarters of a lane is a broken relation rather than an
  unactivated attempt.

The misleading docstring is corrected. It claimed the input was read from an
attempt row rather than supplied by a caller and that there was no operand
through which a caller could name a lane; the helper is exported from two
places, so that described how the lifecycle happens to call it and not a rule
anything enforced. It now says what is true: a pure owned projection, and a
valid typed reference is **not** proof of a live Authority assignment.

**One thing the approved contract did not anticipate, corrected before handoff.**
My first version validated the five members through a loop over `LANE_INPUT`
and projected them with a comprehension. That is correct checking and it
silently cost DISCOVERY: the receiving-boundary catalog derives its entries from
literal member reads, so `lanes.py:lane_reference` dropped from six discovered
entries to three. This Work's own finding rules out "a rename that merely hides
discovery", and buying stronger checking with less visibility is the same trade
in a different spelling. Each consumed member is therefore read and proved by
its own literal name, all six entries stay discoverable, and
`test_every_consumed_member_stays_visible_to_the_inventory` fails if a later
refactor loops them away again. The cost is that the two rule spellings could
drift from `ATTEMPT_COLUMNS`; that is pinned by
`test_each_consumed_member_is_held_to_its_own_column_rule`.

**For the parent's inventory continuation:** the six
`('caller', 'lanes.py:lane_reference', ...)` entries are unchanged in name and
count and now have a real owning validator. The four `lanes.py` orphan calls in
`_occupy_lane`/`_release_lane` are untouched. Mapping them is the parent's, as
its record says; I declared no owner and added no `NOT_AN_ENTRY` exception.

**Controls added, 21 cases in two classes.** `ThePublicLaneReferenceOwnsItsInput`
covers the minimal valid input, a complete active row, a fresh non-aliasing
answer, the preserved inactive refusal on both a synthetic and a real
unactivated row, non-documents (`[]`, `()`, text, integer, `None`, `object()`),
the empty document, each required member missing, every consumed member spoiled
six ways with its boundary label asserted, unstorable text refused where the
document is owned, the malformed attempt id on BOTH branches, malformed-beats-
inactive ordering, known metadata accepted, an unknown member refused, an
activated input missing each reference part, and that the projection touches no
store and names a lane nobody holds. Every refusing case also asserts the input
was not mutated. `TheValidatedBoundaryLeavesEveryLifecycleCallerAlone` drives
the start, the public projection and a settled cleanup release.

### Verification

Question, scope and budget were recorded above before any run.

- Focused, the two new classes: **19 tests, OK, 0.114s**.
- The whole owning module: `tests.manager.test_runtime_lane` — **50 tests, OK,
  0.461s**, covering identity, occupancy, restart, contention and cleanup
  compatibility unchanged.
- Every other module that reaches this boundary, together:
  `test_runtime_lane test_text_sweep test_secrets test_attempts test_intake` —
  **655 tests, OK, 6.175s**. This went beyond the review's proposed two-module
  set deliberately: a public input contract is exactly the case where "the
  callers I audited statically" needs an executed answer, and `test_attempts`
  and `test_intake` own the other three production call sites.
- `tests.manager.test_boundary_inventory` — **236 tests, 23 failures, 18.0s.**
  Those 23 are **pre-existing and unrelated**, and I measured that rather than
  assuming it: I ran the module against the pre-change `lanes.py` restored from
  history and against this candidate, and the two failure sets are **identical**,
  line for line. Baseline `/tmp` measurement is reproduced in
  `evidence/implementation-119642/`. The failures are the boundary-inventory
  debt this Work's own parent and
  `work/records/2026/09/finding-v12-unresolved-suite-checks/` own; none is
  waived and none is mine.
- No daemon, no ordinary suite, no full inventory sweep, no repeat of the
  retained diagnostic beyond the one revalidation above.

### Revalidation of the diagnostic itself

Before editing, the nine retained observations were re-driven against the
unchanged source and all nine reproduced exactly: valid returns the projection,
null principal refuses `refused/precondition`, `[]` raises `TypeError`, `{}`
raises `KeyError`, and a list in each of the five members is accepted — four
travelling into the answer and `runtime_attempt_id` ignored. After the
correction the same nine inputs give: one projection, one `refused/precondition`,
and seven `integrity/schema` refusals, with no input mutated.

**State: awaiting independent review.**
