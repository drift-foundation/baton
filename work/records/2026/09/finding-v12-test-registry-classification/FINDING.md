# Classify unregistered tests without bypassing execution gates

## Assignment and discovery

W168703, tuner claim168782. Created from W32382 review168683 and M168703;
owner reroute168778 assigns bounded research and a plan, with no product/test
edits or broad collection/execution. The source evidence is
`baton:work/records/2026/08/finding-v12-local-oci-negative-race-endings/review-audit-168683.json`.
It reports20 modules missing from both parallel_test registries. The runner's
refusal is intentional fail-closed behavior; missing classification is the gap.

## Confirmed scope — 2026-09-14

Revalidate the exact missing list, inspect isolation, shared process/environment
state and external resources, identify owning Work scopes, and propose bounded
registry integration and deterministic validation. Preserve supervised opt-in
for engine/live-provider workloads, particularly W32577's runtime deadline engine
test. Registering it as ordinary serial work would bypass its reviewed supervisor.
Coordinate the shared runner and active leaf ownership. No W32382/W3 dependency
is introduced. This dossier binds the existing Work; it creates no duplicate Work.

No broad test collection, engine/model execution, image build, package install,
or product/test edit is authorized by this research assignment. Findings below
will distinguish observed source facts from proposed classifications.

## Research result — 2026-09-14 / claim168782

Observed: the runner is unchanged and still deliberately refuses the exact 20
unclassified modules before collection. Source inspection supports proposing
19 parallel class-shard additions and one supervised-only entry. Full rationale,
owners and resource conditions are in CLASSIFICATION-168782.md; the proposed
shared-runner path set, three-category validation and honest scoped/all semantics
are in PLAN.md. These proposals require independent plan acceptance, not an
implementation start inferred from this record. M168816 confirms W161230 owns
eight leaves and neither runner path; canonical owner snapshots are preserved.

Final audit detected concurrent leaf drift as expected from active W161230:
test_managed_preparation.py changed from 96c622d96855fc4aa81001563d99cfb4b131439baaf58d8bae0e2452073786bb
to df7534b46c45e09d04cc3bd0acd53b6ba78cb41216ade2c142bca33146e85836.
The original inventory is preserved. The added TheCoordinatorHostNeverPrepares
class was read: private temporary Git/export fixtures, context-managed mock
traps, sys.path mutation and source inspection; no new engine/model boundary.
The proposed isolation class remains P, but this is a moving source observation,
not an immutable executable candidate. Next author must revalidate later bytes
and shared fixtures. No test assertion correctness review is claimed here.

validate-classification-168782.py initially stopped on that hash mismatch (exit1,
elapsed not measured). It now emits all drift evidence and exits2 on drift;
validation-168782.json preserves that exit2 observation, not a green source
identity claim. Proposed coverage is nevertheless exactly 117, disjoint:
97 parallel, unchanged19 serial, one supervised. Current product registry still
refuses. This script imports only the runner definitions, not tests; AST/source
checks and filesystem names are not suite collection or runtime acceptance.

Measured research audit durations: initial inventory0.3044496189977508s and final
audit0.11942666899994947s, subtotal0.42387628799770027s. The failed intermediate
audit and read-only inspection time are unmeasured, so that subtotal is not a
cumulative upper bound. Test execution spending this claim:0s. No broad suite,
engine/model, image/build/install or product/test edits occurred. No runtime
claim or new execution/dependency authority follows from this research.

## Independent review — 2026-09-14 / claim168901

Confirmed: research is accepted, and the proposed 19 parallel additions plus
one separately supervised classification are technically accepted with the
mandatory refinements in PLAN.md. This supersedes the earlier pending-review
status, but not owner reroute168778's research-only execution scope. The concrete
implementation selection goes to baton.decide on this same Work: exactly
v12/python/tools/parallel_test.py and
v12/python/tests/tools/test_parallel_runner.py, plus dossier progress/evidence.
No leaf, supervisor, shared-fixture or justfile edit is proposed.

Observed: the runner inherits BATON_STATUS_HARDENING_EVIDENCE, whose status
fixture writes fixed method filenames. Proposed implementation must refuse a
nonempty destination before parallel collection when that leaf is selected.
Observed: deterministic budget tests safely import supervised fixture definitions
and use custom load_tests. The earlier blanket no-import wording is superseded:
preserve this inert import, never directly collect supervised modules, and reject
collected supervised-owned test IDs before any shard execution. No silently
filtered passing collection is acceptable. Closed metadata validation and honest
scoped success/default-all refusal complete the bounded proposal; full supervised
gate composition remains unselected.

Independent source-only audit review-audit-168901.json measured
0.16415512398816645s and retained exit2 for the original inventory's known
managed-preparation drift. All 20 leaf and seven shared-fixture hashes matched
the tuner's final snapshot at this audit. This is source classification evidence,
not parallel-runtime acceptance. Active ownership and bytes must be revalidated
at implementation start. No tests were imported, collected or executed; no
engine/model, image/build/install or product/test edits occurred in this review.
The review is review-2026-09-14T11-42-00Z.md. Work stays open for selection and
implementation; no W32382/W3 dependency or duplicate Work is introduced.

## 2026-09-14T12:11:28Z — owner selects bounded tuner implementation

Slawomir explicitly approved the reviewed two-file implementation after prompt
restated the pending decision. This supersedes reroute168778's research-only
restriction for this selected increment and the awaiting-selection statements
above. The independent review-2026-09-14T11-42-00Z.md and all mandatory PLAN
refinements are adopted. Assign baton.tuner through baton.tune; completed
implementation returns to baton.feat for independent candidate review.

Selected product/test paths are exactly v12/python/tools/parallel_test.py and
v12/python/tests/tools/test_parallel_runner.py, plus this dossier's attributable
progress/evidence. Add the 19 reviewed parallel entries and one non-executable
supervised entry, retaining existing serial/METHOD_SPLIT behavior and exhaustive
validated classification. Default/all continues to refuse before collection
until supervised acceptance is composed; explicit scoped results identify the
omitted obligation. Preserve the reviewed evidence-environment guard, safe
transitive imports/custom load_tests, and rejection of supervised-owned test
selection before shards. Do not filter away coverage and report a pass.

Revalidate current leaf/shared-fixture bytes and file ownership before product
edits; M168816's separation from active W161230 remains the coordination basis,
not authority to overwrite subsequent changes. No leaf/shared-fixture/justfile
or supervisor edits. Focused deterministic fake-suite and source-registry
verification is selected as specified in PLAN; broad collection, ordinary
serial engine workloads, engine/model execution, image work and installs remain
outside this increment. Standing test authority applies to the selected runner
regressions. No implementation, full-suite success or Work closure is claimed
by this decision. Existing research/drift/cost evidence remains unchanged.

## 2026-09-14 — selected implementation complete, awaiting review

Tuner claim169136 implements the owner-selected two-file boundary. PROGRESS.md
and HANDOFF-169136.md record the implementation, source revalidation and focused
proof; candidate-169136.json binds exact bytes. Registry classification now
covers117 modules (97 parallel/19 serial/1 supervised) without granting the
supervised execution. Default/all still intentionally refuses; scoped success
names omitted supervised acceptance. Configured evidence output and leaked
supervised-owned IDs refuse under the accepted rules. Historical research-only
and missing-registry observations remain valid descriptions of their snapshots.

Independent candidate review remains required before Work closure. No broad
suite, ordinary serial engine proof, supervisor composition, live provider or
full-source acceptance is claimed. No dependency or containment change.

## 2026-09-14T12:24:15Z — independent candidate acceptance, claim169199

The owner-selected two-file increment is accepted in
review-2026-09-14T12-24-15Z.md. Exact candidate/base/patch/current hashes and modes
match candidate-169136.json, manifest SHA256
59059cc4ca81ea1b3fc5737ce29f7f9cd57b615534f0589ea3fc94f9d7f033c5.
All117 modules are classified exactly once with19 parallel additions,
unchanged19 serial/METHOD_SPLIT and1 supervised metadata entry. Required
precollection refusals, honest scoped output, evidence-variable protection,
safe fixture imports and pre-shard supervised-ID refusal are implemented.

All48 independent focused fake-suite/static-registry checks pass in
13.076128424989292s; exact results/command/environment are retained in
review-run-169199.json/.log. No actual leaf collection, engine/model/image or
broad-suite execution. One moving W161230 leaf changed during review; its
resource/fixture shape remains compatible with the selected parallel class,
as recorded in review-preservation-169199.json and the review. Leaf correctness
and ownership remain with W161230. Candidate and justfile remain unchanged.

This supersedes awaiting independent review. The selected classification and
safe scoped-dispatch outcome is complete and supports W168703 satisfying
closure. Separately supervised full acceptance remains uncomposed by design;
default/all still refuses and no full-suite success is asserted. No dependency,
containment, Git or source-ownership change follows. Reviewer wrote only
dossier review/audit/results and current FINDING/PLAN; prior evidence and
PROGRESS remain untouched, with measured costs separately attributed.
