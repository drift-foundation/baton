# Proposed correction — genuine verification and phase-aware review evidence

**Deferred historical proposal, owner M111752 (2026-09-07).** The current
W71830 arrangement is ordinary implementer tests plus independent review; no
separate clean-verifier producer or service is required. FIRST-PROOF-PLAN.md
supersedes this document as the current bounded assignment proposal. The original
design and reasoning below are retained; their mandatory-producer wording is
not current milestone authority.

Planning owner: baton.codex, claim111614; owner instruction111612.
Status: proposed for ops disposition, not implementation or runtime authority.
This supersedes the preliminary five-path estimate in review16:11:31 as a
complete-delivery estimate. The discovered producer and later receipt interaction
must be accounted for; five local files alone cannot deliver the capability.

## What verification means

**Confirmed:** the 2026-08-20 ruling in
`baton:work/records/2026/08/finding-v12-isolated-agent-workers/FINDING.md`
(“Proposal review, approval, and integration”) defines mechanical verification
of one exact candidate tree as a separate gate before technical review.
Author tests are evidence, not certification. Its clean-verification ruling
requires a separate clean context and ties observations to the proposal, target,
candidate, image and actual required suites. A changed target/candidate needs
fresh corresponding evidence. No ruling here changes that requirement.

**Confirmed chronology:** W71918 review2026-09-05T13-03-27Z reproduced an
unrun reviewer creating eligibility with verification none. The implementation
response added completed/quiescent/frozen/passed and findings/logs checks; the
final review accepted that bounded candidate. The accepted documentation and
`test_verdict_requires_quiescent_frozen_verified_findings_and_logs` still require
passed verification. The fixture establishes it by setting an axis, however;
that did not deliver a production verification producer. W110772's real-custody
proof exposes the gap without withdrawing the earlier negative requirement.

**Confirmed contract:** worker-control SPEC section8.6 and
`verificationReceipt` in `v12/python/src/baton_v12/contracts/schema/worker-control-1.0.schema.json`
already define raw passed/failed/unable observations, verifier profile/image/
toolchain digests, nonempty suites and artifact-backed evidence. `receiptBase`
binds proposal ID/digest, constructed candidate-tree digest, target revision,
actor, policy generation and operation. Assessment accepted/rejected/inconclusive
is a separate receipt and must not overwrite the raw observation.

**Confirmed existing capabilities:**

- `Authority.verify` records an attributable, capability-authorized immutable
  raw observation for an already published proposal. It does not run a suite
  or retain the richer verification manifest. `Authority.receipt` and
  `proposal` return the corresponding durable receipt and proposal binding.
- `retain_manifest(..., "verificationReceipt")` and `load_manifest` can retain
  and validate the existing full schema. Validity/digest retention alone does
  not authenticate who ran the tests or turn a caller document into evidence.
- `attempts.observe` is a journalled projection owner, not a verifier. No
  production caller in the inspected review path establishes verification.
- `integration.driver._accepted_receipts` first requires accepted checkpoint
  eligibility and then writes verification passed. That ordering cannot supply
  the earlier verdict prerequisite, and its literal passed is not a test run.
- `tools.dogfood_operator._derived/_verified` actually rerun mechanical checks
  in the older operator workflow, but are private deployment helpers over that
  workflow's candidate/context. They are not a certified clean-verifier service
  or public review-attempt receipt producer. Do not import them into the generic
  manager or silently authorize host execution of candidate code.

**Missing producer, explicitly identified:** a deployment-owned clean mechanical
verifier, with its configured verification profile and Authority verify session,
must execute the required suites and publish their retained evidence before the
technical verdict. The review agent, claim parser and custody adapter are not
this producer. There is no accepted implementation of that service in the
inspected standalone path. Its delivery is a prerequisite, not a callback that
may return True. Recommend a separately accountable provider Work, created and
scoped by ops before implementation; no new dossier or dependency is fabricated
by this planning pass.

## Proposed producer/consumer contract

The producer is wired by trusted deployment configuration. It accepts a durable
subject, not a model-selected host path: Authority/Work, producer attempt and
assignment generation, retained proposal manifest digest/ID, exact frozen
checkpoint ID/digest, target revision and pinned verification profile/policy.
It reconstructs a clean candidate using the accepted profile boundary and runs
the configured required suites with bounded resources and separate evidence
storage. No canonical-target write, private-line mutation or inherited author
workspace grants are part of verification.

Proposed public interface: a configured provider's `verification_of(subject)`
answers pending/absent or the identities of an immutable full verification
manifest and its Authority receipt. An idempotent producer request starts the
separately owned work; a read never starts a runtime. These are capabilities
supplied by deployment, not booleans or caller-authored receipt mappings. The
producer's execution/workload/image/adapter files need their own researched path
inventory; this plan does not pretend those absent files are already delivered.

Publish the full verification manifest and retained suite artifacts first. The
Authority receipt's deterministic identity/operation must bind that manifest
digest through an explicit, non-circular derivation; the manifest's own receipt
identity is fixed before its digest, and the Authority receipt ID is derived
from that digest. Exact replay returns the same pair. A crash between manifest
retention and Authority acknowledgement resumes the same operation, never
creates a second differing verification receipt for the proposal. No arbitrary
manifest can be endorsed by reusing an unrelated Authority receipt.

The manager's adoption interface, proposed in `review_cycles.py`, is
`record_review_verification(control, *, attachment_id, verification)` with a
read-only `review_verification_of(control, attachment_id)`. It resolves the
attachment/checkpoint/producer and frozen reviewer result from their owners;
the configured verification capability supplies the exact proposal/evidence
selectors and the Authority reader. It re-reads and cross-checks:

- the published producer proposal against its retained manifest, frozen producer
  result, Authority/Work and generation;
- verifier actor/authorized receipt decision and configured profile, image,
  toolchain, policy generation and complete required-suite set;
- receipt target and proposal identity, full manifest digest, suite artifacts
  and observations; passed requires every required suite actually passed;
- candidate/checkpoint identity through the trusted source profile. Current
  `integration.driver` publishes `candidate_digest=proposal_head.hex`, a Git
  COMMIT, while the verification schema's candidate-tree digest is a content
  digest. Neither is interchangeable with checkpoint.tree by spelling. The
  Git-aware verifier must attest the commit/tree/content correspondence; the
  generic manager compares that owned binding and never guesses or runs Git;
- the review attachment's exact generation, checkpoint digest, result ID and
  completion/result-manifest digest, so evidence cannot be transplanted to a
  later correction or a different review.

The first profile refuses a constructed candidate different from the checkpoint
being reviewed; it must be reviewed as a new bound candidate, not silently
accepted because its proposal head is related. Keep target-current checks for
admission/integration distinct from historical evidence reads: an old verdict
remains auditable after the target advances, but is not current write authority.

Record the adopted immutable binding under one deterministic attachment-keyed
manager journal operation, using the existing operation/manifest stores; a new
schema/table is not presumed. Its signature includes every identity and both
receipt digests. Commit the verification-axis projection with that evidence
decision; do not merely call observe(passed) in the driver. Retained manifests
may be stored first, outside the transaction, then referenced after validation.
Use journal replay to complete a crash without rerunning suites. Terminal failed
or unable cannot later become passed for the same attempt; changed evidence
requires a new authorized attempt/proposal decision, not an overwritten axis.

Missing/pending evidence leaves the review held and verification none. Failed
or unable preserves that raw observation and cannot record a technical verdict,
including changes-requested/rejected, while passed verification remains a
precondition of all verdicts. An accepted assessment, accepted worker claim,
parsed report, exit from the review agent, or accepted intake never substitutes.

## Ordered lifecycle correction

For `end_review_from_result`, validate the configured verification capability
before external work, then retain the existing quiesce, observe, real freeze,
completion correlation, intake and retention order. Adopt/check the genuine
verification evidence before recording any verdict. Claim resolution may remain
read-only at its existing point; it cannot advance verification. Missing evidence
returns held, no fence/verdict/cleanup. `end_review` retains its explicit-verdict
contract and passed-verification prerequisite; do not break its legacy callers
merely to thread the new serving capability.

First verdict requires an active independent attachment, exact positively
quiescent runtime and completed disposition. A frozen result remains immutable
when its output axis advances to sealed. Accept sealed only with the matching
accepted intake receipt, exact result/manifest/artifact binding and required
retentions; quarantine or a sealed axis alone is insufficient. Preserve the
existing valid frozen pre-intake owner contract for explicit callers. There is
no sealed-to-frozen regression and no change to intake's transition.

After verdict/fence and ordinary cleanup, eligibility and exact replay consume
historical evidence. Permit destroyed only for an already ended attachment with
its exact committed verdict, verification binding, fence and successful cleanup
journal (positive absent, complete/retained) plus surviving required custody.
Reuse intake.destroy_operation and ControlStore.replay/operation_record rather
than inventing a second cleanup history. Do not relax the shared writer
quiescence helper globally or let a destroyed/unrun reviewer create its first
verdict. Uncertain, failed cleanup, missing provenance and contradictory runtime
observations stay refused/held. This correction covers the immediate lifecycle,
not W110783's separate writer-fence restart matrix.

`integration.driver._accepted_receipts` must consume/revalidate the already
recorded genuine verification receipt instead of minting passed after acceptance.
Otherwise an earlier real receipt collides with Authority's immutable one-kind
receipt rule. Review and approval remain separately attributable later acts;
no Authority schema or permission relaxation is required for this change.

## Smallest recommended implementation split

**Consumer correction: request approval for seven fixed paths plus one bounded
inventory path**, after the provider interface above is accepted:

1. `v12/python/src/baton_v12/worker_manager/review_cycles.py`: evidence adoption/
   reader, passed verification, first-verdict and historical-cleanup checks.
2. `v12/python/src/baton_v12/job_manager/review_driver.py`: serving capability
   preflight and evidence adoption in the existing ending.
3. `v12/python/src/baton_v12/integration/driver.py`: consume the existing genuine
   verification receipt; preserve distinct review/approval/admission.
4. `v12/python/tests/manager/test_review_cycles.py`.
5. `v12/python/tests/job_manager/test_review_driver.py`.
6. `v12/python/tests/integration/test_driver.py`.
7. `v12/python/REVIEW-CYCLES.md`.
8. `v12/python/tests/manager/test_dependencies.py`: only exact additive operands
   introduced by the approved public interfaces if the existing inventory needs
   them. No assertion weakening or inventory exemption.

Tests in those existing modules add cases and extend fixture setup to produce
real verification evidence; preserve previous assertions and meanings. Any
required expected-behavior edit must be enumerated for owner scope before edits.
No new test module/registry, worker report change, schema migration, Authority
change or ordinary intake rewrite is presumed. A measured inventory/schema/API
gap must be recorded before widening this set.

**Producer delivery:** separate provider ownership for the clean mechanical
verifier and its receipt publication. Exact code/image/workload path inventory
must be frozen in that Work before implementation; selecting a generic runtime
from current code would conceal the absent capability. This is mandatory for
production completion. Deterministic tests may replace the external runtime
transport, but must execute a real trivial suite in their owned context, retain
its actual evidence and traverse real manifest/Authority/manager receipt owners.
No artificial observe(passed), pre-seeded verdict or invented successful receipt.

**Assembly wiring:** W103083 keeps its already owned serving/configuration paths.
It supplies the configured verifier capability and durable proposal/checkpoint
subject and schedules/waits for verification without an ordinary operator
transition. Do not seize its files in either provider correction. The provider
and consumer can be reviewed independently; none establishes the full composed
one-Job acceptance by itself.

## Required focused evidence

Prove genuine passed evidence through sealed first verdict, cleanup and later
eligibility; preserve same-line correction and rejected outcomes with real
passed verification. Run actual freeze-cutpoint re-entry and reconstructed
manager evidence adoption with one verifier run, one worker turn and one verdict.
Probe absent, pending, failed/unable, missing suite, wrong actor/profile/image/
policy, stale/foreign proposal or target, changed checkpoint/result/generation,
tampered digest/artifact, quarantine and conflicting receipt/operation. Missing
proof must leave zero fence/verdict/cleanup. Reopen retained artifact bytes after
cleanup and prove eligibility remains audit-resolvable; destroyed without exact
cleanup history cannot create a verdict. A successful read of historical evidence
must not authorize stale target integration.

Audit existing tests before repeats; run focused changed manager/driver suites,
then appropriate source/inventory gate once and retain exact current failures.
No new live execution, credential, image or canonical-target grant follows from
planning or source approval. Ops disposition is the next step; W110772 and its
three dependent gates remain open.
