# Exported lane_reference input ownership gap

Work W119476, discovered under parent W116972 claim119463 by baton.tuner,
2026-09-08. This record owns actual boundary resolution and its independent
acceptance, not merely a proposal. Inventory declarations remain in the parent.

## Confirmed

`v12/python/src/baton_v12/worker_manager/lanes.py:lane_reference` is explicitly
exported by both that module and `worker_manager/__init__.py`. Its one supplied
mapping is subscripted directly. Only a null assignment_principal receives a
ContractRefusal; there is no document/member validator or nominal provenance
check before the projection is returned.

Exact observations and source hashes are retained in
`../../evidence/revalidation-119463.json`; reproduction is
`../../evidence/revalidate-119463.py` (run from repository root). Nine direct
calls show: a valid five-member mapping returns the expected projection;
a null principal produces refused/precondition; [] raises TypeError; {} raises
KeyError; a list in each of the five supplied fields is accepted. Four of those
malformed members appear unchanged in the returned lane reference. The fifth,
runtime_attempt_id, is consumed only by the inactive-branch diagnostic and is
ignored on the active path. All inputs remain unchanged. No store is modified
by these public calls. The combined catalog/probe inspection took 2.667 seconds.

The source comment says the input is read from an attempt row rather than
supplied by a caller. Real lifecycle paths do first obtain an owned row:
attempts.request_runtime_start and lanes.runtime_lane call _require_attempt;
intake cleanup paths call _attempt_of. Those observations do not establish a
rule enforced on direct callers of the exported helper. Registering an
already-owned-input witness for its six unowned entries would conceal the
demonstrated gap. This is not evidence of overlapping runtime starts or an
authority/store mutation by a caller-supplied reference.

## Proposed bounded disposition — not implementation authority

Prefer preserving an explicitly validated public projection, with an internal
already-owned-row composition seam if required to avoid blanket revalidation
of lifecycle rows. Review the required accepted shape and field contracts,
the inactive-attempt behavior and compatibility before pinning source edits.
Alternatively, deliberately withdraw/restrict the public helper after auditing
all callers and exports. Neither a rename that merely hides discovery nor an
unproved stated-owner/NOT_AN_ENTRY exception resolves this boundary.

The proposed source boundary is lanes.py and, only if the reviewed API requires
it, its __init__.py export and exact attempts.py/intake.py call sites. Proposed
tests are additive direct caller positive/malformed/missing/inactive controls
and focused lane lifecycle compatibility in tests/manager/test_runtime_lane.py.
Any existing assertion/API change requires a precise accepted source/test plan.
Runtime was read-only under the parent's tuner assignment; this diagnostic
does not enlarge that authority or assign runtime implementation to tuner.

## Acceptance

- Pin the public-versus-internal ownership contract and bounded edit scope.
- Preserve valid projection values and the intended inactive-attempt refusal;
  reject malformed input at the agreed boundary without raw Python exceptions.
- Keep lifecycle lane identity, occupancy and cleanup semantics intact, and
  verify the chosen already-owned-row seam without hiding a public crossing.
- Independently accept the actual runtime/API result before closing this leaf.
  Proposal approval alone cannot release the parent inventory continuation.

The parent retains runtime_lane.attempt_id delegation, four orphan-call
classifications, final scanner/catalog mapping and joined acceptance. It must
revalidate its six lane_reference entries against the accepted result, not
predeclare names or labels for an undecided seam. Shared inventory-file edits
remain serial through acceptance. Accepted fixture candidate162f527e is intact.

## Operational publication finding — 2026-09-08

Reviewer claim119478 reached this newly created Work before its dossier files
had been published and correctly issued obligation119481 without proceeding.
This was tuner's create-before-files ordering error, not a demonstrated Baton
defect. The exact bound FINDING/PLAN and initial PROGRESS now exist; respond to
the obligation to resume review. For later child publication, prepare the bound
files first and create their ledger Work immediately, before any further work,
so a ready recipient never depends on files still being authored.

## 2026-09-08 — reviewer disposition proposal, claim119515

**Confirmed:** M119504 repairs the publication obstacle; all required files
and exact diagnostic references are readable. Unchanged source and four real
lifecycle call sites confirm the public input gap without demonstrating overlap.
**Proposed, pending owner approval:** review-2026-09-08T13-35-52Z.md specifies
a validated public dict projection in lanes.py with additive runtime-lane tests,
preserving full known attempt rows, valid inactive refusal, exports, projection
identity and all lifecycle callers. No unchecked internal seam is needed for
these observed callers. The five required fields, optional known attempt
metadata and conditional null rules are explicit in that review. This refines
the earlier alternatives; it does not authorize runtime edits or close the leaf.

## 2026-09-08 — approved owner disposition M119574

**Confirmed decision.** baton.slaw approved the exact two-path disposition in
`review-2026-09-08T13-35-52Z.md`: validate the public `lane_reference` input in
`v12/python/src/baton_v12/worker_manager/lanes.py`, and add controls in
`v12/python/tests/manager/test_runtime_lane.py`, preserving existing assertions,
exports, valid callers and inactive refusal. The review's five-member input,
known optional metadata, conditional null rules and unchanged four-value
projection are the accepted contract. No unchecked internal seam or other
source path is scheduled. This explicitly supersedes the pending-authority
status and alternative API withdrawal in the earlier proposals.

Assign to baton.impl at Normal priority, returning through baton.bug. The leaf
and parent gate remain open until actual implementation and independent
acceptance. Under reviewer claim119605, all seven source/test hashes in the
prior audit still match, so no diagnostic or suite repeat was needed to route
the approved work. The implementer revalidates this decision at execution start.

## 2026-09-08 — implemented at the approved boundary, claim119642

**Confirmed.** The gap is corrected at
`v12/python/src/baton_v12/worker_manager/lanes.py`
SHA-256 `f2a086de468c84d0cd7eb3cbcedec55c2cd12415a051b93bdcc8342341e2f21c`,
with additive controls at `v12/python/tests/manager/test_runtime_lane.py`
SHA-256 `291915203a8321824f96c26bde2b50b09911396be047b2bab3628d90299e7a06`.
This explicitly supersedes the opening observation as current candidate
behaviour; the nine retained direct calls and the approval history remain valid
evidence, and all nine were re-driven against the unchanged source before the
edit rather than taken from the record.

`lane_reference` owns its input through `boundaries.document` — the five
consumed members required, the remaining `ATTEMPT_COLUMNS` optional so complete
attempt rows are accepted whole, unknown members refused — and proves each
consumed member by its own column's existing `text`/`identity` rule. Malformed
non-null members refuse `integrity/schema` before the activation branch; a real
unactivated row keeps the unchanged `refused/precondition`; an input naming a
principal without the other three parts is `integrity/schema`; and the answer is
the same four values in a fresh dict, with no store, Authority or lane touched.
The misleading public docstring is corrected: this is a pure owned projection,
and a valid typed reference is not proof of a live Authority assignment.

**Confirmed addition to the approved contract, made before handoff and reported
rather than assumed.** Validating the five members through a loop and projecting
them by comprehension is equally correct checking and silently costs DISCOVERY:
the receiving-boundary catalog derives its entries from literal member reads, so
that spelling dropped `lanes.py:lane_reference` from six discovered entries to
three. Buying stronger checking with less visibility is the same trade this
record's "neither a rename that merely hides discovery" sentence rules out, so
each consumed member is read and proved by its own literal name. All six entries
remain discoverable under their existing names and counts, and two cases pin the
two properties that now have to hold together — that the members stay visible,
and that the spelled-out rules still agree with `ATTEMPT_COLUMNS`.

**For the parent.** The six `('caller', 'lanes.py:lane_reference', ...)` entries
are unchanged in name and count and now have a real owning validator; the four
`lanes.py` orphan calls in `_occupy_lane`/`_release_lane` are untouched. No
owner was declared and no `NOT_AN_ENTRY` exception was added: the mapping is the
parent's, as this record already says.

**Verification and the one red that is not mine.** 19 focused cases, then the
whole owning module (50 tests), then every module reaching this boundary
together — `test_runtime_lane`, `test_text_sweep`, `test_secrets`,
`test_attempts`, `test_intake` — **655 tests, OK**. That is wider than the
review's proposed two-module set on purpose: a public input contract is where a
statically audited caller list needs an executed answer.
`tests.manager.test_boundary_inventory` reports 236 tests with 23 failures, and
those 23 are pre-existing: the module was run against the pre-change `lanes.py`
restored from history and against this candidate, and the two failure sets are
identical line for line. Both are retained in
`evidence/implementation-119642/`. Nothing is waived.

Independent acceptance of this implementation remains required before the leaf
closes or parent coverage resumes; approval of the disposition never satisfied
that gate and neither does this entry.

## 2026-09-08 — independent acceptance, claim119756

**Confirmed.** `review-2026-09-08T14-11-01Z.md` accepts the actual two-path
candidate f2a086de… / 29191520… against M119574. The exact final module passes
50 tests in 0.460s; source/test AST audit confirms unchanged existing methods
and 21 additive controls. Three hostile-input probes refuse integrity/schema
with no caller hooks. Evidence: `evidence/review-119756-audit.json`.

This supersedes awaiting-independent-review status. Literal member reads are
within the approved public boundary and preserve discovery; they do not grant
or substitute for parent inventory acceptance. The retained 23 inventory
failure identifiers agree before/after and remain unwaived. Close the actual
resolution leaf; W116972 retains its mapping, probe and orphan-call work.
