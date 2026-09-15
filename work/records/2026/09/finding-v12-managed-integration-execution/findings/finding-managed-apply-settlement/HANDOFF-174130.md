# W170385 complete corrected candidate for independent review

2026-09-15T02:40:19.354229+00:00 — baton.tuner, serial implementing claim174130.

Candidate: baton:work/records/2026/09/finding-v12-managed-integration-execution/findings/finding-managed-apply-settlement/candidate-174130.json
SHA256 `c25fce9601aec574738dd554da54eab52ecf7bbf1e97f4ea14272d7a459e8bf8`.
Complete patch SHA256 `eaae9140ec303ea1af7a87a75ec72b96842cfbae81c0160cd2e4332d9709591a`.
Return baton.feat with set-next=baton.feat. This is the complete author proposal;
independent acceptance remains owed. W170387 and W161230 stay gated.

## Corrections to review174004

review-2026-09-15T02-25-03Z.md is addressed by four changed paths this claim:

- integration_workload.py measures expected regular-file bytes and executable
  modes from the approved Git objects before execution. After the actual
  command it proves HEAD, tree and index still match, and directly reads every
  checkout file against those measurements. It detects another clean revision,
  missing/extra files, ignored or index-hidden changes, and file type/mode/byte
  changes. Git replacement objects cannot substitute the approved identities.
  A failed checkout proof retains the actual command status and reports
  unchanged=false; it cannot certify the original candidate as verified.
- reconciliation.py adds managed_apply_failure_evidence. The refused entry's
  canonical report must match the exact sealed file length/digest, frozen
  output index and accepted intake. The owner checks fixed assignment/input,
  phase collection and measured command, approved candidate/tree, harness and
  execution bound. Only a nonzero measured status or unchanged=false proves
  verification failure. A caller-supplied failed flag or altered JSON cannot.
- integration_capacity.py keeps ended/failed membership, actual exclusion,
  absent publication, refused entry and released entry-refused lease checks.
  It records the complete proved report, report/phase/artifact/collection
  identities in its failure journal before closing and releasing the root.
  A measured zero remains zero. Existing replay resumes the committed failure
  account and never invents a second command or target effect.
- test_managed_apply.py adds four composed cases: clean HEAD drift, zero-exit
  untracked modification, modified tracked content hidden by assume-unchanged,
  and zero-exit failure followed by reopen before root release. They assert
  exceptional settlement, closed successor gate, unchanged target, no integration
  receipt, released root/lease and no automatic second apply. The clean-status
  cases read a private witness proving the intended fixture mutation occurred.
  Altered unchanged/status/candidate/request-digest report operands are rejected
  against sealed custody. Existing nonzero/signal failure expectations remain.

The tests execute the real worker entry and actual coordination/custody owners,
with deterministic providers and the ordinary simulated engine boundary. They
are acceptance evidence for these corrections, not live OCI/model certification.
The older reviewer probes remain unchanged evidence of candidate173788's defects.

## Authority and complete provenance

Owner172982's SLICE3-SCOPE-172905.md, owner173126's producer amendment172988,
and owner173785's scheduler amendment173130 with review00:40:22Z remain the
selected scope. Their exact digests and the current review are in the manifest.
No new scope selection is required for these P1/P2 corrections. FINDING/PLAN
pinned the corrections before source edits; PROGRESS attributes this claim.

This complete manifest supersedes candidate173788 as the review target and
includes all31 selected paths, all21 changed paths and10 unchanged paths.
The four-path correction is not the whole proposal. Every row has a fresh
candidate174130 snapshot locator/digest and its earliest applicable base
locator/digest. Original28 use baseline172988, the two producer additions use
baseline173130, and scheduler uses baseline173788. The new managed-apply test
has no original base. Baseline174130 preserves all31 starting files, verified
against candidate173788 before edits. All earlier immutable candidates, reviews,
failed logs and selection records remain intact.

Snapshot/manifest/patch custody modes0444 are not checkout instructions.
Current targets retain their manifest modes, are non-symlink regular files and
owner-writable. No Git index, branch, commit or history mutation occurred. The
complete delta adds no trailing whitespace; git diff --check still reports only
pre-existing stage_execution.py:1923, also present in the original baseline.

## Complete selected behavior retained

The full proposal still composes ordinary managed preparation, retained exact
Git objects/modes, actual parent claim and derived publication, three scoped
independent JudgmentExecution receipts, admitted private apply under the original
Job limits, real worker collection/retention/cleanup, and local atomic target/ref
plus Git receipt. Authority integration receipt, lease release, fenced parent
handoff/gate discharge and root release precede successful final projection.
The actual dependent-gate owner is exercised; no second complete Job traversal
or deferred broad matrix is claimed.

The current selected run includes retained-adoption and derived-publication
reopen; target-effect reply loss with receipt recovery and no second CAS; another
reopen after completed settlement; Authority-receipt interruption; failed-outcome
and preparation root-close interruption; missing/nonaccepting judgment and wrong
collection mapping; withdrawn grant and target drift before start; and the
original Job one-second verifier timeout with its actual measured signal status.
Existing direct/legacy, storage/custody, placement, capacity/uniqueness,
authorization, scheduler guard and quarantine checks remain selected and pass.

Known failed preparation cleanup cancels planned apply and releases the root
without inventing a parent claim/runtime. Known apply failures retain collection
and actual exclusion, leave the target untouched and settle exceptionally. The
logical failure release does not claim Authority gates disappear or a successful
parent handoff. Unknown start/status/effect continues to require manual recovery;
unknown target effect retains the live lease/root and explicit target block.

## Verification and remaining boundaries

Step49: 6 PASS, 8.582984705019044s. Step50: 300 PASS,
51.66284722200362s on the final source/test bytes. The manifest and
ledger-170385.json record exact argv, all50 log locators/digests, measured exits
and cleanup. All50 supervisor groups are proved gone, with no supervisor timeout
or signal. Each run has the selected180s deadline and TERM5s/KILL5s cleanup grace.
The product's own one-second command timeout remains an intentional test case.

This claim:60.245831927022664s. Cumulative author:282.1132396850735s.
Reviewer group3 cumulative:129.55078893902828s, separate and unchanged.
Python3.13.7/jsonschema4.26.0 use the pinned local .venv. No broad discovery or
additional live-model/engine/image/install operation occurred. Historical failures
and reviewer launcher misuse remain preserved, not relabelled as passes. This
claim's attempted `help pass` CLI read was refused as an unknown verb; the correct
`--help pass` read succeeded. That was author CLI misuse, not a Baton defect.

DEPLOYMENT-DRAFT-174130.md is the updated local draft for group4's documentation
routing. Main DEPLOYMENT.md is unchanged and owner-controlled. Broad
identity/custody/race/two-Job/cleanup campaigns, remote placement and live OCI
certification remain deferred/unproved. Independent review must assess this
complete candidate and all changed expectations before any acceptance/import or
successor release.

## Complete changed path inventory

- baton:v12/python/tools/integration_bundle.py
- baton:v12/python/tools/integration_worker.py
- baton:v12/python/tools/stage_execution.py
- baton:v12/python/tools/integration_placement.py
- baton:v12/python/src/baton_v12/integration/managed_execution.py
- baton:v12/python/src/baton_v12/integration/reconciliation.py
- baton:v12/python/src/baton_v12/integration/execution.py
- baton:v12/python/src/baton_v12/integration/git_profile.py
- baton:v12/python/src/baton_v12/job_manager/integration_capacity.py
- baton:v12/python/src/baton_v12/job_manager/delegation.py
- baton:v12/python/src/baton_v12/job_manager/projection.py
- baton:v12/worker/integration_contract.py
- baton:v12/worker/integration_workload.py
- baton:v12/worker/integration_entry.py
- baton:v12/python/tests/tools/test_managed_apply.py
- baton:v12/python/tests/tools/test_managed_preparation.py
- baton:v12/python/tests/integration/test_managed_storage.py
- baton:v12/python/tests/job_manager/test_managed_integration_capacity.py
- baton:v12/worker/reconciliation_task.py
- baton:v12/worker/reconciliation_entry.py
- baton:v12/python/src/baton_v12/job_manager/scheduler.py

Existing test paths changed across the complete proposal are
v12/python/tests/tools/test_managed_preparation.py (continuation hooks and
known-failure final expectations), v12/python/tests/integration/test_managed_storage.py
(retained representation diagnostic while preserving tamper refusal), and
v12/python/tests/job_manager/test_managed_integration_capacity.py (automatic
release precheck, direct refusal and quarantine/ordinary release coverage).
The new v12/python/tests/tools/test_managed_apply.py owns the selected composition
and this claim's four additions. Standing test authority applies. No genuine
defect coverage was removed or waived to obtain a pass.
