# Proposed P amendment — publish a candidate, then authorize its import

**Approved in full by owner baton.slaw, return136350, 2026-09-10T12:58:09Z.**
Reviewer136357 records that approval; the pending-ruling/proposed-authority
language below is superseded. The substantive amendment is preserved unchanged.
Parent contract/scope and parent/P/Q/R plans now pin its execution boundary.
This approves implementation and the separate NEW30s author ceiling, not P's
candidate or successor dispatch before independent acceptance.

Proposed by baton.codex, W133117 claim134088, for an explicit owner ruling.
Not implementation authority. This replaces the incomplete two-path proposal
in FINDING's author134000 entry as the proposal currently recommended for
decision; it does not supersede accepted owner133106 until approved.

## Decision requested

Approve the order, state/receipt contract, exact paths, acceptance and budget
below together. An ordinary derived Authority publication creates a candidate
identity on which independent participants can record receipts. It confers no
queue rank, lease, target write or import permission. Only separately proved
authorization permits import admission. Preserve the immutable original
submission, causal history and final exact target check.

The implementer's real-Authority probe establishes that existing
`verify/review/approve` require a published proposal. This is a limitation of
that API, not proof that every possible independent evidence service must work
that way. Reusing these existing attributable, rereadable receipts is the
recommended bounded design; no Authority changes or new evidence service.

## State and operation contract

Use existing state names with the following explicit meanings. Update schema
checks and journal chains together; do not merely move two function calls.

| State | Proved custody | May resolve an import account? |
| --- | --- | --- |
| preparing | Immutable preparation intent | No |
| held | Failed reconciliation and retained reason | No |
| prepared | Separate immutable combined content | No |
| blocked | Retained failing combined observation | No |
| awaiting-evidence | Retained passing causal observations; no proposal yet | No |
| published | Exact derived proposal exists; authorization incomplete | No |
| authorized | Derived publication plus independent accepting receipts, all bindings current | Yes, after full revalidation |
| imported | Q's exact terminal transition, entry and receipt linkage | Terminal read only |

Order: prepare; record observations; publish from awaiting-evidence; obtain and
adopt real derived-proposal verification/review/approval; resolve authorized
import account. A blocked combination never publishes or authorizes. Negative
review/approval remains retained by its owner and cannot be presented as an
accepting local authorization. A corrected candidate needs a new immutable
identity and independent evidence, never an overwrite of the rejected one.

`publish_result(store, publisher, *, result_id, input_digest, policy_digest)`
keeps its named arguments but must prove/pin the input and policy digests
against the accepted owning Job, not merely accept arbitrary strings. The
derived result's distinct identity/digest carries the combined content and
retained execution basis; it does not borrow the original frozen result.
Publication is eligible only from a passing observed result under its live
fixed integration assignment. Retries recover the exact publication at the
original operands before considering any later target or assignment.

Replace the author proposal's unchanged evidence signature with an explicit
reader boundary:

`record_result_evidence(store, authority, verification, reviewer, approver, *, result_id)`

The three configured participants own the completed decisions; their existing
scoped sessions record the ordinary receipts on the derived proposal. This
operation adopts the Authority's own receipts and authorization decisions,
checks the configured actors and independence, and stores a digest-bound
authorization. It does not invent accepting decisions while adapting shapes.
Read approval policy generation from the actual receipt and compare it to the
Authority's current generation; remove the caller-supplied generation as a
source of approval authority. Missing or nonaccepting receipts leave the
candidate unapproved. An identical completed adoption is replayable; changed
operands, receipt bindings or policy refuse rather than rewriting history.

`resolve_import_account` keeps its current owner arguments, requires
authorized state, and rereads original eligibility, live integration
assignment, exact derived proposal, all three actual receipts/current policy,
storage/profile content and exact target. Published alone always refuses.
The resulting account preserves both source and result identities. Q/R must
consume this authorization boundary; their source remains gated until P is
independently accepted. Direct-import behavior remains its accepted contract.

## Receipt-to-execution binding without new Authority fields

Authority receipts do not contain `observations_digest` or `observed_by`.
Do not pretend a shape adapter can read those fields. Instead bind through
the immutable proposal and the result digest it names:

1. Define one closed derived-result digest basis in P containing the result
   identity, original submission provenance, fixed integration assignment,
   prepared head/tree/content digest, pinned target, accepted Job input/policy
   digests, observer identity and retained causal-observations digest.
2. Derive the distinct frozen result digest from that authoritative custody
   basis and publish it in the ordinary derived proposal. Pin/read back every
   field, including input and policy, in the local publication act.
3. Read each actual Authority receipt; cross-bind its proposal ID, kind,
   configured actor/authorization decision, accepting disposition, candidate
   and target to that exact proposal, and approval generation to current
   policy. Re-derive the proposal's result digest from immutable custody.
4. Retain the full receipt identities/documents and journal the authorization
   over that basis. Verify the chain again at admission. A receipt for the
   original proposal, another result, another observation basis or old policy
   cannot satisfy it. Actual observer execution and technical review remain
   required; a receipt label does not replace them.

This is a concrete proposed binding through existing public fields. Prove the
real-session round trip before dependent implementation, within the approved
bounded budget. Return an exact further amendment if that proof fails; no
Authority source expansion is implied.

## Finish the existing storage-isolation requirement

Reviewer134088 additionally reproduced preparation using the original producer
line as the workspace: actual stat values pass, and preparation writes a new
reference in that producer repository. Fix within P before acceptance.

Use the existing Manager `line_of` read to resolve its owned `line_path`,
`line_device`, `line_inode` and nominated source storage. Establish the real
Git repository/storage identities through the standalone profile, and reject
workspace overlap/aliasing with the producer line, its protected source, or
the dedicated target before any object/ref write. Canonical path comparisons
alone do not cover symlinks or shared Git common directories. Preserve the
existing actual device/inode checks and test a valid separate workspace.
No Manager schema/source change is needed to read the existing fields.

## Exact implementation and test scope

Amendment implementation paths (all already in P's accepted allowlist):

- `v12/python/src/baton_v12/integration/reconciliation.py`: order, owner
  resolution, immutable publication/receipt bindings, replay/admission and
  producer/workspace isolation checks.
- `v12/python/src/baton_v12/integration/schema.py`: state checks and typed
  publication/evidence fields consistent with the new order.
- `v12/python/src/baton_v12/integration/git_profile.py`: read-only repository
  identity/isolation capability used before existing effects.
- `v12/python/tests/integration/test_reconciliation.py`: replace the
  pre-evidence-publication refusal expectation with publication-without-import
  refusal; prove actual derived receipts/executions, bindings, crashes/retries,
  negative outcomes, state tampering and storage aliases; preserve previous
  collision, stale-assignment, policy, terminal and source-immutability coverage.

Other P paths are unchanged for this amendment unless a further exact scope
amendment is returned first. Existing `test_admission` and `test_coordinator`
changes remain bound to candidate134000; `test_driver` remains unchanged.
W71830 standing test authority plus this scheduled scope supplies permission
for the stated expectation changes; it does not waive defect acceptance.

After owner approval, append explicit supersession to parent
`INTEGRATION-CONTRACT-v1.md` sections3/5/6 and
`INTEGRATION-SCOPE-v1.md` P/Q/R interfaces; update parent/P and gated Q/R plans
to this order. Preserve their prior text as decision history. These dossier
updates precede amendment implementation. No shared methodology-book edit,
Authority source change, Q/R implementation, live-store migration or Git
mutation is authorized.

## Acceptance and proposed budget disposition

Focused named methods only, retaining full command/setup/stdout/stderr/timing:
real derived publication without evidence cannot enqueue/import; real
independent accepting receipts authorize only the exact content/executions;
source receipts stay unchanged; combined-fail/negative review/missing or
foreign receipt/stale policy refuse; interruption after Authority publication
or receipt creation recovers identical custody; later retries preserve prior
proofs; fake terminal linkage and producer/target workspace aliases refuse
before writes. Include the required causal base-fail/isolated-pass/combined
witness and relevant old direct-import/schema compatibility controls.

Measured author history is56.46s plus explicit unmeasured spending under77s;
reviewer is2.5708062942139804/8s. No exact author remainder is certified.
The author's claimed insufficiency is a forecast, not a measurement of the
unknown historical remainder.

**Proposed owner disposition:** preserve that historical ledger and its
unavailable measurements/output; retire use of the uncertain old P author
remainder for this amendment. Authorize a NEW, separately recorded30s author
ceiling for the exact amendment above, adding30s to the campaign authorization
rather than resetting past spend or borrowing the15s contingency/Q/R time.
Keep the existing8s reviewer ceiling and remaining5.42919370578602s. The30s is
a reviewer estimate: approximately2s owner-API proof/preflight,18s focused
correction controls,10s failure/retry allowance, all setup included. It is not
a guarantee of completion and it does not authorize spending before the ruling.
Stop before insufficiency and return a measured gap. No broad suite/live/OCI
run or historical rerun to manufacture missing evidence.

The owner may reject or replace this budget proposal. Rejection of the order
does not accept the current test-only evidence fixture: P remains unaccepted
until an explicitly approved independent owner design is implemented and
reviewed. No Q/R gate clears by this decision request alone.
