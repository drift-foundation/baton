# Frozen reviewer verdict channel

Ledger Work: W110772. Created 2026-09-07 by baton.codex during W103083
review of handoff M110672. Parent: standalone stage composition.

**Confirmed:** `v12/python/tools/stage_execution.py` defaults the serving
deployment to `_no_verdict`. `StageComposition.end` evaluates this callback
before calling `job_manager.review_driver.end_review`. No public serving input
supplies a real reviewer decision. The exchange terminal carries execution
disposition, not a verdict about a checkpoint. `end_review` validates its
verdict operand before quiescence/freezing; the sealed result metadata that
could carry a reviewer claim is retained later inside that ending. The concrete
worker emits proposal metadata but no review verdict channel.

**Confirmed consequence:** a completed review cannot advance the standalone
Job to either same-line correction or accepted integration. An injected
callback is useful test plumbing, not the missing production implementation.

**Proposed boundary, pending interface review:** preserve the generic exchange
and opaque result-metadata contracts. Define a bounded namespaced reviewer
claim tied to the reviewed checkpoint, emitted with separately declared findings
and logs. Resolve and validate it from the exact frozen review result inside
the ordered ending after freeze and before record_verdict. Keep attempt
disposition distinct from checkpoint verdict. Do not freeze early in deployment
code or turn a missing/malformed claim into an accepted/rejected decision.

Candidate owning paths to revalidate: `v12/worker/claude_agent.py`, its focused
`v12/python/tests/manager/test_claude_agent.py` coverage,
`v12/python/src/baton_v12/job_manager/review_driver.py`, and
`v12/python/tests/job_manager/test_review_driver.py`. A small dedicated claim
reader/test module may be preferable; freeze the exact path set before coding.
The shared `tools/stage_execution.py` hookup remains the assembly author's.
No assertion changes or shared-path edits are granted by this proposed inventory.

**Required result:** an actual worker-owned accepted/changes-requested/rejected
claim, read from immutable output and bound to the attempt/checkpoint, drives
the real review ending. Positive and negative evidence must include missing,
malformed, foreign-checkpoint and incomplete-review claims and replay after
freeze. Preserve independent identities, frozen findings/logs, custody order,
held uncertainty and no cleanup on unresolved evidence. One deterministic
worker is enough for this provider; the full lifecycle remains assembly work.

Discovery evidence: `../finding-shared-stage-assembly/PROGRESS.md` (M110672
checkpoint), `../finding-shared-stage-assembly/review-2026-09-07T14-12-42Z.md`,
and that record's `evidence/review-110736/candidate/` snapshots.

## 2026-09-07 — reviewer research, claim 110843

**Confirmed:** the capability remains absent. The executable baseline in
`evidence/research-110843/baseline.py` refuses findings/logs declarations with
`this dogfood workload declares exactly one output ... declares 2` and proves
that `end_review` requires its caller's verdict. `baseline.json` binds eleven
inspected source/test files by SHA-256. This is baseline evidence, not an
implemented provider or a live review proof.

**Confirmed:** `ClaudeAgent.work` selects one declaration, checks out a
candidate and runs an editing prompt. `_provider` discards successful stdout;
`_ran_provider` reads bounded diagnostic stdout only under the existing
credential ruling. Parsing a stdout word would neither produce separately
frozen findings/logs nor establish a review workload. The current image runs
this same agent through `dogfood_entry.py`.

**Confirmed:** `baton_worker.answered` supports multiple declarations, requires
an answer for each, and accepts `missing-optional` only when not required.
Generic metadata is opaque. `single_worker._matches` compares every stage
against the Job's ONE input digest: unrelated implementation/review manifests
cannot satisfy that contract. `integration.driver._one_output` requires one
present proposal by type; `review_cycles._review_result` requires findings and
logs. Those stage consumers supply the stage-specific presence checks below.

**Confirmed:** public `frozen_output_of`, `load_manifest`,
`attempts.assignment_of`, `review_cycles.review_of` and `checkpoint_of` supply
the result, fixed assignment, attachment and checkpoint evidence. No new store
reader or direct database access is required. The integration producer shows
how to cross-bind a claim from a retained result. `record_verdict` already
binds the complete manager-owned checkpoint digest, attempt, generation,
independent reviewer and frozen review result.

**Proposed implementation plan:** the following supersedes the initial
"pending interface review" inventory as the current recommendation. It does
not claim approver ratification or implemented behavior. The assigned author
must revalidate and record adoption or a dated correction before coding.

### Workload and claim

Keep worker-entry and generic manifest schemas unchanged. Add a concrete-agent
review branch, selected by validated launch `role=review` before implementation
checkout/publication. Preserve the single-output implementation workload and
task `/2` contract. For the shared Job, support one explicit declaration set:
`proposal` of type `git-change-proposal`, plus directory-result `findings` and
`logs`, all optional in the common manifest. Implementation must produce
proposal and answer the others `missing-optional`; completed review must produce
findings/logs and answer proposal `missing-optional`. Reject ambiguous or
unexpected shapes, rather than treating arbitrary multiple declarations as a
proposal. Also support review-only findings/logs declarations for bounded tests
and valid callers. Stage consumers still require their own outputs. Assembly
owns construction of the common manifest, not this provider.

The first review workload is explicitly the existing `git-line` checkpoint
profile. Read manager-mounted `/input/source` in place. Do not reuse the
implementation checkout, reserve files in the checkpoint, commit, or execute
the task's editing/verification workflow against that read-only line. Present
instructions as requirements to assess, with a review prompt and a bounded
report destination in the review workspace. Report only substantiated checks;
the task naming a verification command is not evidence it passed. Other review
profiles remain outside this delivery and refuse explicitly.

Use a dedicated provider-authored report file, not diagnostic stdout or an
exit-code-to-verdict mapping. Recommended closed file contract:
`{"schema":"baton.review-report/1","verdict":"accepted|changes-requested|rejected","findings":"bounded nonempty text"}`.
Own types, enum, duplicate-key refusal, a 1 MiB byte bound and descriptor-based
regular-file/path checks. Require a fresh destination; a previous report cannot
stand in for a new turn. After provider success, adopt a valid report into the
findings output. Produce separate adapter-authored logs with safe status/check
summaries. Preserve closed argv/environment, credential-root handling,
descriptor checks, timeouts and diagnostic redaction. Raw stdout/stderr and
credential contents never become logs, recap or errors. Findings are a
deliberately authored artifact, not a diagnostic-stream exemption. Failure,
timeout or malformed/missing report produces no successful review claim.

Place this namespaced claim on the findings output:

```json
{"baton.checkpoint-review/1":{"verdict":"accepted","base":"<full object name>","head":"<full object name>","tree":"<full object name>"}}
```

The four inner members are closed and typed. Verdict comes from the report;
base/head/tree are worker-observed facts about the reviewed source, not
provider-supplied manager identities. Use complete lowercase object names with
their original algorithm/width; verify source agreement before and after review.
Manager compares them to the attachment's exact frozen checkpoint. Assignment,
result/artifact ids, measured digests and checkpoint identity/digest remain
manager-owned. A claim on logs/proposal cannot substitute for findings, and
competing reviewer claims refuse.

### Public consumption and ordered ending

Keep both new functions in `job_manager/review_driver.py`:

* `review_verdict_from_result(control, *, attachment_id)` is a read-only public
  reader returning the validated closed claim. Resolve the attachment's
  attempt, its frozen output, retained `resultManifest`, fixed assignment and
  checkpoint through public owners. Require completed frozen review, matching
  result id/digest and assignment reference/generation, and separate present,
  measured, artifact-backed findings/logs. Validate base/head/tree against that
  checkpoint. Missing, malformed, foreign or unavailable evidence is a typed
  refusal, never a default decision. Read no mutable runtime path, clock,
  provider callback or raw store row.
* `end_review_from_result(control, port, adapter, *, attachment_id,
  disposition, terminal, profile, retention_disposition,
  retention_policy_digest)` takes no caller verdict. Share the ordered core
  with existing `end_review`; preserve that explicit-operand API and its
  pre-stop checks. The serving entry performs capability/identity preflight,
  quiescence, observation, freeze, exact terminal/completion correlation using
  the existing helper, intake, retention, frozen-claim resolution,
  `record_verdict`, and cleanup in that order. Do not duplicate custody
  orchestration or freeze inside a deployment callback. The terminal is
  correlation evidence, not a verdict.

Preserve accepted/correction/held results. An unresolved claim has `verdict:
null`, no verdict record, no authorized cleanup or advancement, and a safe held
reason with frozen evidence identities. Current evidence-refusal categories
remain held; infrastructure unavailability remains retryable refusal. A valid
rejected claim still records its fence and permits existing cleanup before
returning held; it is distinct from unresolved evidence. Re-entry after freeze
derives the same claim from retained output and never invokes the worker again.
Keep post-writer-fence restart defect W110783 independently scoped.

### Exact path ownership and acceptance

The proposed implementation path set is exactly:

* `v12/worker/claude_agent.py`
* `v12/python/src/baton_v12/job_manager/review_driver.py`
* `v12/python/tests/manager/test_claude_agent.py`
* `v12/python/tests/job_manager/test_review_driver.py`

Schedule additive cases in the two existing test files. Preserve existing
assertions and fixture expectations; the separate production entry and legacy
declaration support make weakening them unnecessary. No new module or registry
change is needed. Record and review any required assertion change or path-set
extension explicitly. Reviewer research changes this dossier and the parent
plan, never implementer PROGRESS.

Acceptance needs actual `ClaudeAgent.work` with a deterministic process seam,
whose outputs go through generic measurement, real retained result custody and
the new ending into an accepted verdict. Do not replace the claim reader or
`record_verdict` in that joined proof. Prove changes-requested reaches existing
correction opening and rejected stays held. Focused boundary cases: failed or
incomplete worker; missing/malformed/unknown/competing claim; foreign result or
generation; base/head/tree mismatch; absent findings/logs; unsafe/oversized/stale
report; source mutation attempt; terminal mismatch; replay after freeze and
recorded verdict; no cleanup/correction on unresolved evidence. Audit safe
diagnostics and unchanged implementation/proposal behavior.

Run the two focused unittest modules with the interpreter selected by
`v12/python/justfile`, then that subtree's canonical `just test` once for the
candidate. Record commands, interpreter, counts, immutable candidate hashes
and boundary outcomes. This research ran only the bounded baseline, not the
implementation suite, Docker, provider network access or a live trial.

**Assembly interaction:** W103083 must call `end_review_from_result` with the
real terminal and public operands, replacing production reliance on
`_no_verdict`/an early injected verdict. Its owner also supplies common
declarations and one Job input digest. Shared serving/test paths remain outside
W110772. Assembly files changed during research; `baseline.json` binds the
inspected checkpoint, not ownership of their next bytes. Deliver the provider
first, then compose the full lifecycle. A rebuilt worker image remains a
candidate until separately selected under deployment policy.

**Operational lookup note:** guessed paths under
`baton_v12/tools/single_worker.py`, `worker_manager/freeze.py`,
`job_manager/integration_driver.py`, `source_profiles/git_line.py` and
`v12/python/README.md` did not exist. These were reviewer lookup mistakes,
not unreadable required dossiers or product defects. Repository discovery
located the actual modules above; no conclusion relies on a guessed path.

## 2026-09-07 — implementation adoption — baton.claude

**Revalidated.** All eleven files `evidence/research-110843/baseline.json`
binds are byte-identical in the current tree, including
`tools/single_worker.py` and `tools/stage_execution.py` at W103083's returned
candidate. Every confirmed claim above was re-checked against the source and
holds: `_one_declaration` refuses a second declaration; `answered` requires an
answer per declaration and admits `missing-optional` only when not required;
`_review_result` requires a `completed` frozen result carrying separately
frozen `findings` and `logs`; `record_verdict` binds the manager-owned
checkpoint, attempt, generation, reviewer identity and frozen review result;
`frozen_output_of`, `load_manifest`, `assignment_of`, `review_of` and
`checkpoint_of` are all exported and sufficient; and `retain_proposal` is the
producer pattern to follow. The launch document already carries `role`, which
`single_worker` fills from `launch_role`, so the review branch is selected by
a validated operand rather than by inspecting the filesystem.

**The proposal is ADOPTED** with four clarifications, recorded here because
each is a decision a later reader would otherwise have to re-derive. None
extends the four-path set.

1. **`base` is the task's `declared_base`, verified present in the mounted
   line — not derived from the repository alone.** A repository cannot say
   which of its commits is the base a checkpoint was declared against;
   `GitCheckpointProfile.freeze` takes it as an operand. So the worker reads
   it from the frozen task document it was given and proves the mounted line
   actually contains that commit. `head` and `tree` remain purely observed
   (`rev-parse HEAD` and `HEAD^{tree}`). The manager still compares all three
   against the checkpoint's own evidence, so a worker that named a base it was
   not reviewing is refused there.
2. **The provider's report destination is a fresh private directory under the
   container scratch, not under `/output`.** Every `/output` subdirectory is a
   measured declared output, so a provider-authored file inside one would be
   collected and sealed as adopted material before this adapter had validated
   it. The adapter validates the report first and then AUTHORS the findings
   output from it.
3. **The findings output carries two adapter-authored files:** `report.json`,
   the validated closed document, and `findings.txt`, its findings text. The
   claim rides on the findings output's `result_metadata`, exactly as the
   proposal claim rides on the proposal output's.
4. **`end_review` is unchanged, including its lack of terminal correlation.**
   The new `end_review_from_result` takes `terminal` and correlates it, and
   the two share one ordered core. Passing `terminal=None` through that core
   is a no-op in `_correlated`, which is what keeps the existing entry point's
   behaviour identical rather than merely similar.

**Not adopted as written, and reported rather than worked around:** nothing.
The proposal's scope is implementable within the four named paths.

## 2026-09-07T15-19-16Z — independent review, claim 111187

**Confirmed; changes requested:** `review-2026-09-07T15-19-16Z.md` records three blocking boundaries: the serving ending permits absent terminal evidence; a competing proposal verdict escapes the findings/logs-only check; and FIFO report opening blocks before file-type validation. The report reader also adopts text the UTF-8 publication cannot encode. `evidence/review-111187/probe.py` and `probe.json` reproduce these against the exact four-file candidate. The joined tests pre-record their verdict and skip terminal correlation, so their acceptance claim is limited as explained in the review.

**Current correction scope:** preserve the four named paths and legacy entry; require/validate the new terminal, reject every competing output claim, make report adoption bounded for special files and valid output text, and repair this Work's newly added joined proof to start before the first verdict with matching terminal/custody evidence. Add focused negative cases and preserve all pre-existing test expectations. Implementation must record adoption before editing. Shared assembly and integration-worker paths remain gated; no deployment or live-provider act is implied.

### Operational finding at review handoff

**Observed:** the standalone canonical `pass work=W110772 to=baton.impl set-next=baton.bug` under the default execution boundary failed at `authority.py:1222` with `sqlite3.OperationalError: attempt to write a readonly database`. The immediately preceding canonical `say` succeeded as M111231. A subsequent canonical pass using the environment-required escalation mechanism succeeded as event 111233 and released the claim to implementation. No direct store access or protocol repair was attempted. This is an execution-authority discrepancy, not evidence of a candidate code defect; its precise policy cause remains open. The deployment owner should reconcile the installed managed-operation policy with the environment escalation requirement so a managed handoff needs no such retry.

## 2026-09-07 — correction adoption — baton.claude

Adopting `review-2026-09-07T15-19-16Z.md` in full. All three P1s reproduced
before anything was changed and all three were real. The corrections are
within the same four paths; nothing is widened.

**P1 — the serving entry requires the worker's completion envelope.**
`end_review_from_result` now owns the terminal's SHAPE before the first
external act and compares it against the frozen result after the freeze. The
two are deliberately separate questions: the shape can refuse while nothing has
happened, and the comparison needs a frozen result to be about. `end_review`
keeps its accepted no-terminal contract, and a case now drives that rather than
asserting it in prose — a caller that already holds a decision is not claiming
to have correlated anything.

**P1 — the competing-claim scan covers every output.** The reader walks the
whole frozen output set for the claim namespace and requires its sole
occurrence on `findings`. Naming the outputs to exclude is how the next output
added becomes a second opinion nobody looks for, and the common manifest a
shared Job declares names `proposal` expressly.

**P1 — the report boundary gets its own opener.** A descriptor-based
`O_NONBLOCK` open, regular-file proof on the descriptor, then the bounded read
— so a FIFO at the report name is refused rather than blocking outside the
provider's deadline. `_open_under` is unchanged and still owns the measured
tree walk; this is one fixed name in a directory the adapter created
exclusively, written by the least trusted process in the container. Report text
that no UTF-8 encoder accepts is refused at adoption rather than at
publication: adopting text is adopting the obligation to publish it.

**The joined proof is repaired rather than re-explained.** It starts with no
verdict recorded, carries the worker's real completion envelope, and runs over
the retained result the resolver actually reads — the freeze now answers
`frozen_output_of` for the exact attempt instead of a canned digest nothing
retained. The order assertion compares the WHOLE recorded sequence against
`REVIEW_RESULT_ENDING` rather than filtering it to the steps observed, which is
what let a missing `correlate` and `resolve` pass. `correlate` and `resolve`
are recorded by wrappers that delegate to the real functions; neither the
reader nor `record_verdict` is substituted.

**The broad-gate account was wrong in two ways and is corrected in PROGRESS.**
There are SIX boundary-inventory failures, not five. And the blanket "no
container started" was true of the focused workload demonstration and false of
the subtree gate, which runs live-engine suites; the two claims are now
separated rather than merged.

## 2026-09-07T15-37-14Z — correction review, claim 111328

**Accepted:** the three source corrections from `review-2026-09-07T15-19-16Z.md` resolve the reproduced terminal/competing-claim/report defects. Candidate source hashes and independent audit: `review-2026-09-07T15-37-14Z.md` and `evidence/review-111328/`. The first-verdict and whole-step assertions are improved; all182 original tests remain unchanged.

**Still incomplete; supersedes the claim that the joined-proof repair is complete:** the terminal digest is copied from the canned result vector, and freeze/intake/retention/cleanup are substituted. Public readers after the fixture ending show no intake receipt or retentions despite its accepted/cleaned-up answer. This is a test-proof gap, not an established production custody bug. Complete the previously scheduled real worker-completion-to-public-custody joined proof in the owned test_review_driver.py, with external seams deterministic and real owner-produced records. Preserve accepted source bytes unless a concrete failure demonstrates a needed correction. No live daemon/provider or shared serving work is required. See the exact bounded fixture, cutpoint, verification and return instructions in the new review.

## 2026-09-07 — bounded test-proof assignment — baton.tuner, claim111406

Owner reroute111403 assigns this correction to baton.tuner. Ownership is limited
to v12/python/tests/job_manager/test_review_driver.py and this dossier. Adopt
review-2026-09-07T15-37-14Z.md: add a deterministic joined proof using the actual
review worker completion envelope and public freeze/intake/retention/cleanup
owners, asserting their durable evidence and first verdict. Exercise interruption
at the actual after-freeze cutpoint and re-entry without another worker turn.
Preserve prior assertions, the accepted production source bytes and other test
paths. Report a required production correction rather than expanding this scope.

Revalidation confirms the current joined fixture uses _frozen_endings and seeds
its result/artifact rows; the terminal copies the published-vector digest. This
is the recorded proof gap, not evidence that production custody accepts it.
Existing isolated tests remain useful and will be preserved while the additional
joined proof closes this boundary. Run the new proof and focused review-driver
module, reuse the recorded broad gate for unchanged production bytes, append
attributable progress and return to independent review. No live provider/daemon,
image selection, shared serving edit or production correction is authorized.

## 2026-09-07 — public custody exposes a production blocker — baton.tuner, claim111406

**Confirmed.** The bounded joined proof requested by owner reroute111403 and
`review-2026-09-07T15-37-14Z.md` reaches a production refusal. Both an
uninterrupted first ending and re-entry immediately after a real freeze resolve
the worker's claim as `accepted`, then return `outcome=held`, no verdict and no
cleanup. The refusal is:

> a review verdict requires frozen output and passed verification

The actual ending runs quiesce, observe, freeze, correlate, intake, retain,
resolve and record_verdict. Public freeze retains a result whose completion
digest equals the actual `baton_worker.publish_completion` envelope. Public
intake records accepted custody; public retention records both artifacts.
Recomputing their custody-tree digests agrees with the receipts. Each scenario
invokes the worker once; the interrupted scenario reuses the same frozen result
and has no intake, retention or verdict at its cutpoint.

**Confirmed source boundary.** `job_manager/review_driver.py:_ended_review`
calls `_collected` before `review_cycles.record_verdict`.
`worker_manager/intake.py:_record` observes output `sealed` when recording
custody (line 735), whereas
`worker_manager/review_cycles.py:_completed_review` (line 984) requires output
exactly `frozen` and verification `passed`. The legitimate custody transition
therefore makes the required verdict precondition unsatisfiable in this
ordering. This is a product composition defect, not missing Authority or
container access: the refusal is in the real manager owner after actual
file-backed freeze and intake have succeeded.

**Open production decision.** The implementation owner must reconcile the
verdict precondition with the ordered custody contract and establish the
correct verification owner/evidence. Merely resetting output to `frozen`,
seeding a passed-verification observation, or substituting a verdict would
conceal the failure. No such workaround or production change was made. The
appropriate production correction requires a new explicit bounded assignment;
it is outside tuner ownership of the test path and this dossier.

**Supersession of acceptance claims.** Earlier statements that the joined proof
was complete are superseded as evidence of public-owner lifecycle acceptance
by this dated finding and the latest review. Their isolated tests still pass,
and the accepted three source corrections remain byte-identical. The capability
is not ready to release W103083, W110935 or W106673 on this evidence.

Evidence: `evidence/tuner-111406/custody-blocker-probe.py` and its JSON output,
`joined-proof.txt`, `focused-module.txt`, and `candidate.json`. The probe uses
disposable test stores and public evidence readers; it verifies the observed
blocked custody path rather than manufacturing the desired success. The two
new acceptance tests remain failing, without expected-failure decoration.

## 2026-09-07T16-11-31Z — independent blocker confirmation, claim111561

**Confirmed:** return111506 preserves all four reported hashes and the complete
prior111559-byte test prefix. The tuner stayed within owner111403's test-only
scope. Independent first-ending and actual freeze-reentry probes observe
`output=sealed` AND `verification=none` from the unchanged attempt owner at
record_verdict. Both resolve accepted but retain two artifacts and return held
with no verdict or cleanup. This confirms a production incompatibility rather
than a remaining mock-custody proof defect. It does not complete acceptance.

**Confirmed distinction:** permitting sealed output alone cannot resolve the
separate verification requirement. Passed verification is an explicit W71918
contract and regression expectation; no producer in the inspected manager/
review ending supplies it. Generic observe is storage, not verification. Later
Authority integration receipts require an already accepted checkpoint, so they
are not an available earlier prerequisite without an explicit contract change.
No verification fact may be inferred from provider success, verdict or intake.

**Inferred related boundary:** the same precondition is used by integration
eligibility, but normal cleanup changes runtime quiescent to destroyed. Require
a post-cleanup eligibility proof when correcting lifecycle evidence checks;
that cutpoint is not yet reachable through the failing first-verdict case.

**Proposed owner disposition:** authorize a bounded production correction only
after identifying the trusted verification evidence owner/contract. Preserve
the existing passed-verification rule unless an explicit owner supersession
changes it. The exact proposed five-path surface, positive/refusal/replay tests,
policy interaction and evidence limits are in
`review-2026-09-07T16-11-31Z.md`; independent audit and retained bytes are in
`evidence/review-111561/`. This proposal grants no source or assertion edits.
Return to ops; all three dependent gates remain. The earlier accepted source
corrections are not withdrawn, and no public-custody success is claimed.

## 2026-09-07 — verification semantics and correction plan, claim111614

**Confirmed from the owning contract:** owner111612 preserves passed
verification. The earlier isolated-workers ruling defines this as mechanical
checks of an exact candidate in a clean verification context, independently
of author evidence and technical review. Worker-control SPEC section8.6 and
its existing verificationReceipt/receiptBase schemas already distinguish raw
passed/failed/unable from assessment and bind proposal, target, candidate,
verifier profile/image/toolchain/policy, suites and retained artifacts.
W71918's response to its unrun-reviewer defect added the passed axis guard but
no production evidence producer; its fixture directly establishes that axis.

**Confirmed existing interfaces and missing composition:** Authority.verify
authenticates and stores an immutable attributable receipt; it does not run
checks or retain the detailed manifest. Manager retain_manifest/load_manifest
can own the full verificationReceipt shape but do not certify its author.
The older dogfood operator actually reruns tests, yet its private host workflow
is not a public clean-verifier service for standalone review. No accepted such
producer is present in the inspected serving path. The trusted producer must
be a configured clean mechanical verifier with a verify-capable Authority
session, supplying actual suite evidence before verdict, not the review agent,
claim reader or custody receipt.

**Proposed bounded correction:** `CORRECTION-PLAN.md` pins the producer request/
read contract, digest-bound receipt pair, manager adoption/journal interface,
required subject comparisons, first-verdict sealed custody and historical
eligibility after proved cleanup. It preserves failed/unable/none refusals and
forbids resetting axes or treating claim acceptance as verification. It also
distinguishes the producer's Git commit identifier from the constructed
candidate-tree content digest; profile-owned evidence must bind both.

**Supersedes the preliminary five-path complete-delivery estimate:** publishing
real verification before verdict also requires the integration driver to
consume that existing receipt, rather than later minting another passed
receipt. The proposed consumer scope is seven fixed paths plus one bounded
additive operand inventory path, enumerated in CORRECTION-PLAN. A separately
accountable clean-verifier provider still needs its own exact code/runtime
scope; the plan identifies the absent capability instead of pretending a
boolean callback delivers it. W103083 retains assembly wiring ownership.

**Disposition requested:** approve/refine this split and assign the producer
before production implementation. This is planning, not source authority,
verification-semantic relaxation or dependent-gate release. Cross-record history
is appended in W71918's canonical FINDING/PLAN; its prior accepted review remains
historical evidence. Research baseline and source/contract inventory are retained
in `evidence/planning-111614/`. No production/test assertions, runtime, image,
credential, or coordination dependency were changed by this claim.

## 2026-09-07 — owner narrows the first-proof scope, baton.prompt

Slawomir confirmed that the v12 critical path should remain minimal and safe,
with general hardening deferred. After discussing the missing verification
producer, he agreed that the general-purpose clean-verifier service proposed
in CORRECTION-PLAN.md should not automatically become a prerequisite for the
first standalone proof. This supersedes the scope direction in owner111686
to establish that general service as a critical-path provider. Preserve the
earlier proposal and evidence as history; its complete-delivery architecture
is deferred, not the current implementation assignment.

The next bounded plan must address the actual sealed-output and post-cleanup
lifecycle defects and determine the smallest honest verification arrangement
using existing isolated execution facilities. Identify what checks run, which
exact candidate they cover, and how their real results are consumed. Do not
build a reusable verifier framework merely to satisfy the current axis guard.
If even that bounded arrangement exceeds first-proof scope, return the exact
proposed milestone/contract change and its limitation for explicit disposition.
This direction does not itself remove the passed-verification requirement,
authorize fabricated passed evidence, weaken tests or release dependent gates.

Isolation, exact candidate/result binding, authorized target access, independent
review and retained evidence remain necessary first-proof boundaries. The
general verifier design may be retained as deferred work under the existing
bound records; creating a new service Work is not required by this ruling.

Slawomir subsequently requested a message on W110934 because he had approved
prematurely. Current CLI state distinguishes W110934's active OCI mount review
from W110772's queued verifier planning. The coordination message must preserve
that distinction rather than infer cancellation of the OCI safety corrections.
Slawomir then confirmed the Work-number mistake. The requested scope-correction
message belongs to W110772; W110934's OCI review continues.

## 2026-09-07 — ordinary tests plus review, owner M111752; claim111746

**Confirmed owner supersession:** W71830's FINDING, “Current verification is
implementer testing plus review”, now explicitly chooses ordinary implementer
tests and independent reviewer checks for the current milestone. This supersedes
the prior entry's unresolved search for a separate minimum verification producer,
owner111686's provider assignment, and owner111612/claim111614's requirement to
preserve a separate clean-verification producer as a prerequisite. The earlier
CORRECTION-PLAN.md remains deferred history. No verifier service, agent, Job stage
or new provider Work is scheduled. The review attempt's verification axis must
not be manufactured as passed to accommodate its obsolete guard.

This milestone ruling supersedes the W71918 reviewer-axis passed prerequisite
and the 2026-08-20 clean-context requirement insofar as another producer is required
before W71830. It preserves ordinary required tests, independent technical review,
isolation, exact candidate/result identities and truthful retained evidence.
Detailed source/test edits still require the bounded assignment below; the owner
ruling is not blanket assertion-change or runtime authority.

**Confirmed existing evidence and actual gap:** claude_agent._verify already
runs the frozen task command, preserves its real status/argv in result.json and
verification.txt, and revalidates candidate bytes before publication. No new
runner is needed. The current proposal metadata does not carry that observation
to integration.driver, which currently writes verification passed from accepted
checkpoint eligibility alone. Removing the reviewer-axis guard without correcting
that unconditional receipt would manufacture evidence and is not proposed.

**Proposed smallest bounded data correction:** FIRST-PROOF-PLAN.md carries actual
ordinary test facts through a separate namespace in the existing proposal output,
compares them to the existing trusted task selection and exact retained producer/
checkpoint, then records the existing Authority raw observation as ordinary tests
under this milestone policy. It never claims clean certification and never sets
the reviewer verification axis. Missing, failed or foreign required-test evidence
cannot produce passed/admission. Independent review and Authority approval remain
separate acts. The receipt interpretation is explicitly part of the proposed
source assignment; no Authority/schema expansion or second verifier is needed.

**Proposed lifecycle correction:** accept properly cross-bound sealed review
custody for the first verdict while preserving completion, positive quiescence,
independence and findings/logs. After positive ordinary cleanup, read exact retained
verdict/fence/result/cleanup history without requiring a destroyed runtime to
regress to quiescent. Missing history cannot create a verdict or eligibility.
The actual two failing custody proofs remain unchanged and must become passing.

The exact nine fixed source/test/doc paths, one bounded operand inventory path,
specific changed expectations and W103083-owned assembly input are in
FIRST-PROOF-PLAN.md. This supersedes both the earlier five-path estimate and the
seven-path clean-provider consumer proposal as the current requested assignment.
Current graph snapshot111751 has no separate clean-verifier provider Work or
new W110772 provider edge; W61981 stays parked. No provider was created under the
superseded request, so no provider lifecycle correction is required.

Baseline15 source/test/doc hashes and graph evidence: evidence/planning-111746/.
No production/test assertion, progress, runtime, image, credential or dependency
was changed. W110772 returns the bounded plan to ops; its three dependent gates
remain. Existing failing required gates are reported honestly, not waived here.

**Operational lookup notes:** exploratory searches named nonexistent
v12/python/src/baton_v12/worker/claude_agent.py, source_profiles/git.py and
integration/proposal.py. Repository inventory resolved the actual owners to
v12/worker/claude_agent.py, source_profiles/checkout.py and integration/driver.py,
which were read. These were reviewer path guesses, not missing required records
or Baton defects. All required dossier/policy records were readable.
