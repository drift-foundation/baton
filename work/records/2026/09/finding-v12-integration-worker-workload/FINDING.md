# Concrete integration worker workload

Ledger Work: W110935. Created 2026-09-07 by baton.codex during W110774
research (claim 110914). Discovery/consumer:
`work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-standalone-stage-composition/findings/finding-integration-runtime-port/`.
The top-level canonical record avoids a third nested dossier level; ledger
containment is W110774 and no earlier record is moved.

**Confirmed:** repository discovery finds no worker-side consumer of
`baton.v12.integration-assignment/1` and no producer of
`baton.v12.integration-result/1`. `Dockerfile.claude` runs `dogfood_entry.py`
with `ClaudeAgent`; that agent selects a proposal declaration and an editing
workflow. W110772 separately owns its review-role extension. Manager fixtures
in `tests/integration/test_execution.py` write bounded target changes and
correlated result files, but they start no model/runtime and are not a worker.

**Proposed boundary:** a separate worker entry/workload and image candidate
that consumes the accepted integration delivery, immutable instruction bytes
matching the profile's digest and exact independently approved candidate
evidence. Before any target edit, perform the whole accepted path-set/base-byte/
type/owner-write/test-scope preflight required by repository policy. Import
only the approved candidate content, preserve ordinary repository modes,
verify final bytes/modes and publish a bounded atomic result in the existing
closed schema. Model output remains untrusted; coordinator settlement and
positive runtime quiescence remain manager responsibilities.

Ordinary Git reads may support the Work's preflight. Git staging, commits,
branch/history changes and pushes remain Slawomir's. The model may not redesign
the candidate, repair target permissions, resolve drift/conflict or weaken tests.
An ordinary pre-mutation refusal leaves all target bytes/modes intact; a partial
or uncertain import produces held evidence, not a success or retry instruction.

Reuse accepted provider/credential isolation mechanisms without raw diagnostic
publication. Keep provider success, authored result and runtime quiescence
distinct. Validate exact attempt/lease/entry/target/fence/profile/instructions
before work; no process-exit inference of integrated success. Artifact locations
come from deployment's custody resolution, not a model-selected host path.

**Open:** exact separate module/recipe/test paths, worker-visible evidence
document and read-only artifact layout. Pin these in research before code. Do
not concurrently edit W110772-owned `claude_agent.py`; use an accepted public
helper or explicitly coordinate a separate helper extraction if necessary.
A new image is only a candidate until the deployment owner selects its digest.

Required proof: deterministic provider at the real worker entry, actual bounded
filesystem import into a disposable target and verification from read-back
bytes/modes, real correlated result parsing, clean refusal preserving all paths,
partial/uncertain hold, missing/foreign/oversized report and diagnostic safety.
No live credentialed model or repository target mutation in research.

## 2026-09-07 — workload research and bounded proposal, claim111086

**Confirmed:** current claude_agent.py now has an in-progress review branch
owned by active W110772. Its only public action methods remain consider/work.
Credential-home preparation, closed child environments, bounded stdout drain,
deadline and failure projection are private methods. Calling work would enter
implementation/review semantics; it cannot be used as an integration launcher.
No current worker source consumes integration-assignment/1.

**Observed:** evidence/research-111086/baseline.py records the public methods,
absent integration consumer and ten source hashes. The actual public result
reader accepts each correlated integrated/refused/held claim and refuses foreign
attempt, wrong fence, unsupported outcome and extra member. No filesystem import
is implied by that acceptance: generic result adoption intentionally does not
observe a target or provider. No engine, credential, provider or Git mutation
occurred. This is a source/interface baseline, not a successful integration test.

The following proposal replaces the initial open workload/layout/path selection
with a concrete plan. It remains **Proposed**, to be revalidated and adopted by
the implementer before source changes. It does not grant live execution or
independent approval of candidate bytes.

### Entry, provider and launch

Add separate v12/worker/integration_entry.py and integration_workload.py.
The entry runs once from durable files and exits after publishing its result.
It does not call baton_worker.main, consume describe/work command frames, write
an ordinary worker terminal, or treat stdout as authority. Reuse the public
baton_worker.read_launch/launched readers for the fixed launch file. Require
the /1 launch form without an ordinary exchange transport, exact role integration,
and the bundle's manager-bound expected launch session/contract/role.
A /2 launch claiming ordinary file-exchange transport is refused rather than
silently ignored. W110774 must deliberately materialize this one-shot launch.

Read assignment.json at the existing fixed assignment namespace; write the
existing fixed result/result.json. W110934 supplies RO assignment, RW result,
RW /target, normal private scratch/credentials and the accepted RO source mount
at /input/source. No host operand is taken from a model report. The worker
holds no coordinator, manager, Authority or runtime engine capability. Its
assignment correlation is not a fresh live-grant query; W110934 owns final
pre-start proof and W110774 owns final settlement proof.

**Serial shared-file boundary:** propose one additive public
ClaudeAgent.invoke_provider(prompt, *, directory) method, which owns private
scratch/environments and calls the existing provider helper with explicit prompt.
It returns only the existing bounded status/failure vocabulary, never raw stdout,
stderr, credential contents or a presumed integration outcome. No checkout,
commit, proposal publication, input task parsing or review operation runs here.
Reuse existing run/home test seams and existing helper implementations; do not
clone the drain/credential code into another provider class.

W110772 currently holds claude_agent.py. M111114 explicitly coordinates the
proposed later wrapper; no ownership transfer or shared edit occurred. Finish
W110772's independently accepted candidate before W110935 adopts that source as
its base. Then schedule only the additive wrapper and regression cases under
W110935. Existing helpers, consider/work and all earlier assertions remain
unchanged. This serialization is a source dependency, not a reopening of the
review verdict design. If the owner rejects the wrapper shape, append that
decision and revise this plan before implementation.

### Immutable worker-visible evidence bundle

Add v12/worker/integration_contract.py as a standard-library-only owner of the
deployment bundle/report shapes and bounded readers/publication. It imports no
baton_v12 package. Conformance tests hold its assignment/result member sets,
version strings, fixed names and 65536-byte result bound against the accepted
runtime contract so packaging cannot quietly create a second protocol.

Proposed fixed /input/source layout:

- integration.json: closed baton.integration-input/1 envelope;
- instructions.txt: the exact profile instruction bytes;
- evidence/: canonical, hash-bound accepted Work/plan, independent review,
  checkpoint, proposal, frozen-result and receipt projections;
- blobs/: content-addressed regular files for the exact reviewed base and
  candidate contents, named by lowercase SHA-256 digest without caller paths.

The envelope binds schema, complete assignment digest, expected launch,
producer-derived entry eligibility, checkpoint evidence, evidence-file references,
instruction digest and one sorted unique path table. Each path row names its
relative target path, explicit add/edit/delete operation, base and candidate
blob identities/sizes (null only for the appropriate absent side), and the
reviewed mode disposition. Do not put proposal/candidate/head/checkpoint/tree/
artifact digests into one interchangeable member: their producers define
different identities. Recompute path_set_digest from the exact sorted paths
and keep it equal to the accepted checkpoint/entry.

Every envelope field needs a named producer. The assignment comes from the
current grant; the eligibility account from admission.resolved_account and the
queued entry; checkpoint and accepted verdict from review_cycles public readers;
proposal/result/approval receipts from the retained public owners; test scope
and scheduled changes from the accepted Work/plan. Existing-test authority is
not inferred from a generic approval receipt or a list of candidate paths.
Carry the exact frozen independent review and scheduled scope, including
evaluation of every changed existing test. Missing or contradictory scope/
review evidence refuses before the provider is called. No newly authored
approved=true or fabricated review evidence substitutes for those records.

A candidate artifact's custody file mode protects evidence; it never selects
the target mode. Edits preserve the reviewed existing target mode, additions
use ordinary non-executable mode unless explicit accepted scope selects
executable, and mode changes require the same bounded scope and review.
Unsupported filesystem kinds refuse the whole proposal; no symlink/submodule/
special-file import is smuggled into this first regular-file slice.

Bound all dimensions: propose 1 MiB envelope, 64 KiB instructions, 4096 paths,
64 MiB total blob bytes and 64 KiB per report/result. Reject unsupported versions,
unknown/duplicate JSON keys, non-exact booleans/integers, invalid UTF-8, traversal,
absolute/.git paths, duplicate/ancestor path collisions, special files and
unbounded counts before allocation or provider execution. Reject symlinks at
every traversed component and prove opened regular files and sizes; oversized
inputs refuse rather than truncate. The implementer records final finite bounds
at adoption and adds boundary tests.

### Bundle producer and provenance

Add v12/python/tools/integration_bundle.py with a public composition operation
for W110774. It owns the deployment-specific Git reading outside generic core.
It receives the real public stores/Authority reader, fixed assignment and launch,
selected profile instructions, accepted line/proposal selectors and a NEW
deployment-owned destination under configured storage. It re-resolves accepted
evidence and refuses disagreement before publishing anything consumable.
Publish a new complete read-only bundle atomically and return its measured digest
and nominated-source binding; never append to existing immutable custody.

Concrete existing sources: frozen_output_of plus retained manifests expose
artifact identities/locators; integration_checkpoint and checkpoint_of expose
the exact accepted base/head/tree/paths; line_of identifies the manager's private
line; audit_checkpoint(profile) validates the retained reference independently of
mutable current HEAD. The line worker publishes objects.bundle, patch, verification
and result, but deliberately publishes NO plain candidate tree. Do not invent
one in that artifact or read current worktree bytes as the reviewed candidate.

For this Git deployment, materialize base/candidate blobs through bounded
READ-ONLY Git object queries against the revalidated retained checkpoint line.
Use explicit reviewed object identities, ls-tree/cat-file/show as appropriate,
and verify path list/tree/object/content bindings before publishing the bundle.
GIT_OPTIONAL_LOCKS=0 and explicit no external diff/text conversion prevent
incidental index/command behavior. Do not clone, fetch, checkout, reset,
update-ref, unpack into .git, stage or commit. If retained objects are missing,
refuse with the exact producer gap; no private Git mutation or invented pack
decoder is authorized as a fallback. This selected local-checkpoint path does
not prove portable bundle-only import; record that limitation.

Do not silently promote a public artifact locator into host access. The producer
checks the configured custody/line owner, canonical/no-follow root and accepted
digest before reading. Instructions and evidence are resolved from their accepted
owners, not a path the model supplied. After extraction, revalidate accepted
checkpoint/evidence and complete entry equality; publication identity covers
all emitted bytes. W110774 rechecks under the grant at its final start boundary.
A package of previously accepted facts does not replace that later proof.

### Model work, refusal and measured ending

The workload validates assignment, launch, bundle digests and all target path
shapes before invoking the provider. It records a complete before-state for the
scheduled paths and checks base bytes/type/owner-write and effective runtime
access, expected target revision and overlap. It never changes modes to make a
target writable. All scheduled paths are preflighted before any target edit;
a later invalid member cannot follow an earlier successful write.

The bounded instruction document requires the model to evaluate the accepted
Work/review/test scope for the whole candidate, import only the exact approved
bytes, preserve/establish reviewed modes, read back every affected path and
perform the scheduled bounded verification. It prohibits Git index/history
mutation, candidate redesign, permission repair, conflict resolution and edits
outside the accepted path set. The provider performs the actual import; a canned
host result writer or deterministic copier in place of the model is not this
model-driven workload.

Require a dedicated bounded provider report in private scratch, with a closed
schema, exact assignment/bundle identity, outcome, phase, changed-path list,
measured verification and fixed refusal/hold codes. Keep arbitrary provider
diagnostics and exception strings out of manager-visible results. Render paths
only from the validated accepted table and correlate reported digests with the
wrapper's own final byte/mode observations. A provider exit0 without a valid
report is unresolved, not integrated.

The wrapper independently reads final scheduled-path bytes/modes and compares
them with the exact approved candidate before composing integrated detail:
imported_paths plus verification. Refused/held detail uses the accepted reason
and detail pair. Failed verification, partial mutation, unknown report or a
failure after the provider obtained writable work yields held, unless complete
pre-mutation refusal is positively established. Never publish refused merely
because final files happen to match their original hashes: restoration of bytes
does not prove no mutation occurred. A conservative held answer is required for
ambiguous provider failures, even when the scheduled-path comparison is unchanged.
Publish the outer existing integration-result/1 with manager-bound identities,
not provider-supplied replacements, atomically with whole-write/fsync/no-clobber
rules. Existing terminal result means no second provider turn.

The model runs with the granted target mount. These source/instruction and final
verification checks do not form a kernel-enforced per-path write allowlist, and
a provider may still have descendants after its leader exits. Do not claim
adversarial write prevention, whole-repository equivalence or runtime quiescence
from the report. Any observed outside-scope or .git mutation is held and never
repaired automatically. The exact runtime must be positively quiesced by the
manager before result settlement; predecessor exclusion and no automatic
interrupted recovery remain the accepted production rules.

### Files, regressions and handoff

Bounded source paths: new integration_entry.py, integration_workload.py and
integration_contract.py under v12/worker; new v12/worker/Dockerfile.integration;
new v12/python/tools/integration_bundle.py; later additive invoke_provider only
in v12/worker/claude_agent.py after W110772 is independently accepted.
No shared stage_execution/single_worker/integration runtime core edits here.

Scheduled additive tests: new v12/python/tests/manager/test_integration_worker.py,
new v12/python/tests/tools/test_integration_bundle.py, and new
v12/python/tests/manager/test_integration_image.py with deterministic recipe/
isolated-import checks. Add exactly their registry entries in parallel_test.py,
coordinating that small shared registry with W110934. Existing assertions and
existing worker recipe/entry are untouched; retain existing test suite coverage
for implementation/review/provider behavior after the additive wrapper.

The separate recipe reuses an explicitly selected existing provider base digest
and copies only the worker modules/data it needs; it never copies manager/
Authority/store packages. Use exec-form entry, fixed65532:65532, inherited
credential posture and no default-secret/env fallback. A recipe or mocked
entry test is not artifact validation: building/selecting a new image digest
belongs to the explicit deployment checkpoint. No build/pull/live turn occurs
during research.

Required deterministic proof goes through the real entry/workload and injected
provider process seam, performs actual bounded edits in a disposable target,
parses the real result with runtime.observed_delivery, and checks exact final
bytes/modes against recorded verification. Prove missing/foreign assignment/
bundle/report, stale checkpoint/profile/instructions, incomplete test authority,
late invalid path, target drift/type/permissions/overlap, safe add/edit/delete,
partial write, provider failure/timeouts, preserved .git/index and no rerun over
an existing result. Simulate malformed/symlink/FIFO/oversized reports and unknown
diagnostics without disclosing tokens. For the bundle producer use deterministic
read-only Git-runner seams and real temporary files; do not mutate Git merely
to create a reviewer fixture.

Run the new focused modules, existing Claude-agent regressions for the additive
wrapper, and canonical v12 Python source gate. Audit an isolated image-layout
import so missing packaged schema/data/module files cannot hide behind checkout
imports. Actual image behavior remains a later explicit artifact check. Return
exact input digests, source hashes, invocation, finite bounds and proof to
independent review and W110774 before claiming deployment readiness.

**Operational lookup account:** guessed worker_manager/artifacts.py, manifest.py
and result.py do not exist. Repository search located the required public evidence
owners in output.py and the retained-manifest contracts instead. These were
lookup mistakes, not missing required dossiers or grounds to bypass public APIs.
All required bound records and policy files were readable. No workaround applied.

## 2026-09-07 — prerequisite revalidation and pre-implementation split, claim112610

**Confirmed:** W110772 closed112501, W112029 closed112567 and joined W112039
closed112601. W110934 is also closed112242. This supersedes the preceding
active shared-worker/source-dependency status. Current claude_agent.py is the
accepted ordinary-test/review candidate65a9d8b7dda16f76665c0a620740653b43692ac315e246fd4e822fe222101817;
its public methods remain consider/work, with invoke_provider still absent.
The planned integration worker/bundle/contract files do not exist. No partial
implementation is being reviewed. baseline13: evidence/revalidation-112610/.

**Revalidated interface:** accepted OCI mounts preserve the proposed fixed
assignment/result, RO /input/source and RW /target layout. Historical checkpoint
evidence and ordinary_test_evidence now work after cleanup. Preserve actual
ordinary-test provenance and reviewer-axis none/failed/unable semantics; do not
reinstate the superseded clean-verifier prerequisite. Current input/result bounds
and provider credential/drain owners remain compatible with the research plan.

**Split decision under EFFECTIVE-BATON:** the research's immutable bundle producer
and concrete worker are separately implementable/reviewable outcomes. No shared
implementation is in flight. Create child W112630, bound at findings/
finding-integration-evidence-bundle/, for integration_contract.py,
tools/integration_bundle.py, tests/tools/test_integration_bundle.py and exactly
its parallel_test registration. This explicitly supersedes the original combined
source/test allocation before implementation. Route that provider to baton.impl;
W110935 waits for its accepted contract/bundle, then retains integration_entry.py,
integration_workload.py, Dockerfile.integration, additive ClaudeAgent.invoke_provider,
test_integration_worker.py, test_integration_image.py and their two registry
entries. Existing provider helpers and worker assertions remain unchanged.

The dependency is genuine: workload cannot adopt an independently accepted
bundle/report contract until its owner delivers it. W110935 retains final joined
real-entry/provider-driven target import, measured result and negative/uncertain
proof; splitting never makes this capability complete early. W103083 remains
blocked on W110774 with no Handler; W110934 is closed, so registry work is serial
child then parent. Parent PROGRESS remains untouched. No source/test/live/Git
change in this planning/revalidation claim and no additional planning approval
is required by this allocation through existing route authority.


## 2026-09-07T20:39:10Z — accepted bundle adoption handoff, claim113300

**Confirmed:** W112630 closed satisfying at owner113293, accepting exact child
review113125 bytes and explicitly releasing this Work. The previous pending
child-acceptance and parent-waiting status is superseded. Revalidation finds all
four accepted child hashes unchanged, accepted claude_agent.py base65a9d8b7...
unchanged and no parent implementation begun. Evidence/revalidation-113300/audit.json
and review-2026-09-07T20-39-10Z.md bind this handoff.

**Current implementation boundary:** adopt the accepted child API; the older
claim111086 proposed bundle fields/bounds are superseded wherever they differ.
The closed envelope launch carries schema/role/digest, never the raw live launch
session credential. Seven evidence documents are checkpoint, job, proposal,
receipts, result, review and tests. read_bundle returns root/envelope/instructions/
evidence and validates internal consistency; the workload must still correlate
its actual assignment, launch, profile/instructions and expected eligibility.
Read blobs through bundle_blob and preserve no-follow component traversal.

The accepted bound is251 paths, derived from512 manifest files and9 fixed files,
with1MiB envelope,64KiB instructions,1MiB per evidence projection and64MiB unique
blob content. Reports/results are64KiB. These supersede the original proposed
4096-path bound. Path rows are path/operation/base/candidate; each non-null side
has object/blob/bytes/mode. Apply repository target-mode authority, not custody
file modes. The report uses the accepted paths and verification members from
check_report; its shape, provider exit and final bytes alone do not prove scope
authority or mutation-free refusal.

Keep producer bundle_digest (canonical digest of the measured whole-file manifest)
and envelope_digest (digest of serialized integration.json bytes) distinct. Pin
and prove how the workload measures/correlates the complete bundle identity when
adopting this API; never substitute the envelope digest for the report's bundle
digest. Public worker readers intentionally do not return an assignment verdict
or a target import decision. If a required public contract capability is actually
missing, record the exact gap before proposing an owner change; do not silently
rewrite accepted child bytes or invent an alternate envelope.

Before provider execution the wrapper must correlate all inputs and complete the
whole target path/base/type/owner-write preflight. Preserve the required semantic
review of scheduled test scope and exact frozen independent review evidence; an
internally consistent bundle or generic approval is not blanket authority for
existing-test mutation. The provider does the actual bounded import. Independent
wrapper readback then binds exact bytes/modes, fixed report identity and result.
A failure after writable work was available remains held unless a genuine
pre-mutation refusal is positively proved; unchanged final bytes are insufficient.

**Serial ownership:** hand the five new paths and two bounded existing-path
additions listed in the newest review to baton.impl. The child registry addition
is complete, so the two parent registrations can now be added serially. Preserve
all child source/tests, accepted provider helpers/actions and earlier assertions.
The production descriptor-bound Git runner remains W110774's responsibility.
Existing-provider-base recipe reuse does not select or authorize a new artifact;
image build/selection and live execution remain separate. This handoff schedules
implementation and focused/required source gates within existing Work authority,
not another planning approval cycle. Return for independent joined review before
claiming the parent capability complete; historical broad reds remain unwaived.

## 2026-09-07 — implementation adoption and pinned workload decisions, claim113322

baton.claude adopts this record and the accepted child API. Revalidated before
acting: the eight inputs in `evidence/revalidation-113300/audit.json` were
re-measured against the current tree and the four accepted child hashes, the
shared `claude_agent.py` base `65a9d8b7...` and the absence of all five new
paths all still hold. Nothing below was acted on without that check.

### The decisions this workload is pinned to, before any source edit

**The bundle identity the report must carry is the PRODUCER's
`bundle_digest`**, which is the canonical digest of the measured whole-file
manifest — one entry per emitted file, with its relative path, byte count and
content digest. It is NOT `envelope_digest`, which is the digest of
`integration.json`'s serialized bytes and covers one file out of nine-plus.
The two are separate members of the producer's answer for exactly this reason,
and the workload measures the first by walking the mounted bundle through the
contract's descriptor-bound traversal and recomputing that manifest, rather than
by reading a number the bundle claims about itself.

**The correlation set, before the provider is started.** Every one of these has
to agree or the turn refuses without a target write: the assignment this runtime
was launched under (`read_assignment`) against the envelope's
`assignment_digest`; the launch document at `/run/baton/launch.json` against the
envelope's `launch` schema, role and digest; the profile kind, version and
instructions digest carried by the assignment against the instruction bytes in
the bundle; and the eligibility account's expected target revision against what
the target actually is. A bundle that is internally consistent has proved
nothing about being THIS runtime's bundle, which is the whole reason
`read_bundle` deliberately answers no verdict.

**The preflight is whole and precedes every write.** All scheduled paths are
checked before any of them is touched — relative-path shape, the base side's
exact bytes and mode where one is declared, the absence of a candidate path
that already exists for an add, the target's type and the runtime's actual
write access — so a later invalid row cannot follow an earlier successful
write. Repository target-mode authority decides the imported mode; the bundle's
custody file modes never do.

**Scheduled test scope is evaluated semantically and is not inferred.** The
evidence projections carry the accepted Job's test scope and the exact frozen
independent review; an internally consistent bundle and a generic approval
receipt are not blanket authority to modify an existing test, and missing or
contradictory scope or review evidence refuses before the provider is called.

**The ending is conservative.** A failure after writable work was available is
`held` unless a genuine pre-mutation refusal is positively established;
unchanged final bytes do not establish it, because restoration is not absence of
mutation. The provider's report is a claim: its shape, its exit status and the
final bytes agreeing do not by themselves prove scope authority or a
mutation-free refusal. The wrapper's own independent read-back of bytes and
modes is what composes `integrated`, and there is no automatic second provider
turn over an existing terminal result.

**`ClaudeAgent.invoke_provider` is additive and owns no new mechanism.** It is
the existing private provider turn — the composed argv, the composed
environment that is never inherited, the prepared credential home, the bounded
drained stdout and the closed failure classification — exposed under one public
name so a second workload does not grow a second copy of those rules. It takes
a prompt and a working directory, and answers the same closed
`ok`/`status`/`failure_reason`/`why` document `work` already consumes. No
existing helper, action or assertion changes.

### What this turn delivers, and what it does not

Delivered: this adoption, the additive `invoke_provider` wrapper, and the new
`tests/manager/test_integration_worker.py` that drives it through the real
adapter with the accepted injected-process seam, plus its registry entry.

**NOT delivered, and named rather than left to be discovered:**
`v12/worker/integration_workload.py`, `v12/worker/integration_entry.py`,
`v12/worker/Dockerfile.integration`, `tests/manager/test_integration_image.py`
and its registry entry are **not started**. The joined acceptance proof — an
accepted producer bundle carried through the real entry into a provider-driven
import of a disposable target, with independent byte and mode read-back, actual
result parsing, whole-path preflight refusal and a conservative partial or
uncertain hold — is **not built**. Nothing in this turn should be read as
evidence for it. W110774 stays blocked and this Work is not complete.


## 2026-09-07T20:52:18Z — partial wrapper review and completion handoff113374

**Confirmed:** claim113322 delivers only the additive provider wrapper, its
10-test module and one registry entry. Independent review finds182 focused tests
passing and exact preservation of pre-existing adapter bytes and registry entries.
The registry has its authorized addition; the three other accepted child paths
are unchanged. review-2026-09-07T20-52-18Z.md and evidence/review-113374/ preserve
exact candidates, byte-normalization audit and focused transcript.

**Confirmed P2:** the new test asserting the four scheduled product/test paths
remain absent contradicts completion. The next implementation step specifically
replaces/removes TheRemainingWorkloadIsNotBuilt.
test_the_workload_entry_recipe_and_image_suite_are_absent and its status-only
class/docstring, replacing that status assertion with scheduled real-entry/import/
result and refusal/held coverage. Keep nine meaningful wrapper cases and all
prior Claude-agent assertions. This supersedes treating file absence as a
permanent suite invariant; it is bounded authority for that exact test correction.

The concrete wrapper uses invoke_provider(*, prompt, room); pin that keyword
choice explicitly at continuation, superseding the earlier proposed directory
keyword, and use it consistently. No workload consumer exists yet.

**Current action:** return to baton.impl to finish the already accepted remaining
entry/workload/recipe/image-suite scope and joined proof. No new planning approval
or parent closure follows from this partial checkpoint. W110774 remains gated;
production runner/artifact selection/live execution remain separate and historical
broad failures remain unwaived. PROGRESS remains implementation-author-owned.

## 2026-09-07 — P2 correction and the pinned wrapper signature, claim113398

Adopted `review-2026-09-07T20-52-18Z.md`. It found no blocking defect in the
wrapper, one P2, and two things I stated imprecisely. Scope is unchanged.

### The pinned signature, concretely

    ClaudeAgent.invoke_provider(*, prompt, room) -> {"ok", "status",
                                                     "failure_reason", "why"}

    prompt  required non-empty text; the caller's own, because a workload with
            a different task document has a different prompt and defaulting to
            `work`'s would instruct the provider about work it is not doing
    room    required absolute path to a real directory of its own, reached by
            its own canonical name -- no link, no `/.`, no ordinary file; it
            becomes the child's working directory
    answer  the private turn's closed document, unchanged: `ok` is "the
            provider exited zero" and is NOT an outcome; `failure_reason` is
            one of this module's own closed words and never the provider's
            prose; a clean turn publishes neither a reason nor a `why`

Both operands are keyword-only. The wrapper adds no mechanism: the argv, the
composed-never-inherited environment, the prepared credential home, the bounded
drained stdout and the failure classification are the adapter's existing ones.

### P2 — the absence assertion is removed

`TheRemainingWorkloadIsNotBuilt` asserted that the four planned files did not
exist. The review is right that this was a development status check wearing a
product regression's clothes: it would have rejected the completion of this very
Work merely because the scheduled artifacts existed, whatever their correctness.
I added it to stop a green suite reading as coverage, and the dossier is where
that belongs — PROGRESS.md and the review evidence already record it. The one
method, its class and its now-inapplicable docstring are removed and the module
docstring says why. The nine wrapper cases and every pre-existing Claude-agent
assertion are untouched; `test_claude_agent` remains 172.

**Scheduled in their place**, when the workload lands: the positive real-entry
bundle-to-import-to-result path, independent byte and mode read-back, and the
negative whole-path preflight refusal and conservative partial/uncertain held
regressions. Those replace the removed status check as this file's account of
what is and is not proved.

### Two things I stated imprecisely, corrected

I wrote that "the four accepted W112630 child files are byte-identical". Three
are — `integration_contract.py`, `tools/integration_bundle.py` and
`tests/tools/test_integration_bundle.py`. The fourth, `tools/parallel_test.py`,
carries this Work's own authorized additive registration, so it is not
byte-identical and was never meant to be. The review is right to correct it.

And this Work remains INCOMPLETE. The remaining paths are exactly
`integration_workload.py`, `integration_entry.py`, `Dockerfile.integration`,
`test_integration_image.py` and its registration, plus the joined
provider-driven import, read-back, result and refusal/held proof. None of it is
started, no further planning approval is needed for it, and W110774 stays gated.


## 2026-09-07T20:56:55Z — P2 resolved and execution continuation113415

**Confirmed:** correction113398 removes exactly the scheduled absence-status
class/method, preserving all nine wrapper cases and fixtures. Nine independent
focused tests pass; wrapper and registry bytes are unchanged. Concrete signature
and child-file wording are corrected. review-2026-09-07T20-56-55Z.md resolves the
P2 of review113374; evidence/review-113415/ preserves exact candidates/delta/audit.

**Current:** four implementation/test artifacts and joined proof remain absent.
Return to baton.impl to execute the already authorized remaining scope, append
its correction progress and continue through the required verification. The next
handoff carries the complete deliverable or a concrete blocker requiring a named
external action. No additional approval/review of this resolved test correction
is pending. W110774 remains gated and historical broad failures unwaived; no
image/live/production authority is expanded.


## 2026-09-07T21:00:40Z — operational capacity handoff, claim113446

**Observed:** M113443/claim113433 reports insufficient implementer-turn working
capacity and explicitly no repository, authority or dependency blocker. Independent
hash/absence audit confirms no new source delivery and correction progress now
recorded. The capacity limit itself is reported, not independently measured.

**Clarified:** no policy requires the remaining implementation and proof to fit in
one model turn; coherent incremental progress with durable records and context
continuation remains allowed. Existing product/file authority is unchanged.
Repeated status/correction handbacks have not produced the remaining workload.

**Current disposition:** supersede direct return to the same constrained
implementation context with ops scheduling disposition. Recommend restoring
capacity in the single canonical baton.claude implementation context and then
routing W110935 to baton.impl. RESUME-113446.md is the concrete resumption packet;
review-2026-09-07T21-00-40Z.md and evidence/review-113446/audit.json record the
independent operational assessment. Preserve cohesive remaining scope and final
joined acceptance. No hidden additional consumer, implementation takeover, new
product ruling or artificial dependency is needed. Work/consumer gates remain
open; historical broad failures unwaived.


## 2026-09-07 — the remaining workload, entry, recipe and image suite, claim113667

baton.claude, executing the accepted scope under `RESUME-113446.md`. Revalidated
before acting: the three reviewed hashes in `evidence/review-113446/audit.json`
still matched, all four remaining paths were absent, and the accepted child API
was unchanged. Nothing below was acted on without that check.

### The concrete form of the pinned conservative ending

The pinned rule is that a failure after writable work is `held` unless a
genuine pre-mutation refusal is positively established. Implementing it forced
the question of what CAN positively establish one, and the answer this workload
adopts is exact: **`refused` is published only when no provider was started at
all.** That is the one fact this runtime can establish about a mutation-free
ending, and it is established by construction rather than inferred from
evidence. Once `invoke_provider` has been called with the target as the
provider's working directory, every ending short of a verified complete import
is `held` — including a clean, well-formed provider report claiming a preflight
refusal over a target whose scheduled paths are byte-for-byte unchanged.
`TheEndingIsConservative.test_a_clean_provider_refusal_after_writable_work_is_still_held`
is that rule.

THE COST IS REAL AND IS ACCEPTED HERE RATHER THAN DISCOVERED LATER: a
legitimate provider-side refusal reaches an operator as a hold rather than as a
refusal, so the queue does not settle it automatically. That is the direction
the ruling names — "a conservative held answer is required for ambiguous
provider failures, even when the scheduled-path comparison is unchanged" — and
the alternative is a `refused` outcome resting on the provider's own account of
its own restraint. If a later Work wants provider-side refusals to settle
without an operator, it needs evidence this runtime does not have (a
kernel-enforced write boundary, or a mediated import the provider cannot
bypass) and it should say so explicitly rather than relaxing this rule.

### The bundle identity, measured

`bundle_digest` is recomputed by walking the mounted bundle: one manifest entry
per file, its relative path, byte count and content digest, canonically
digested. It is compared with the producer's own published answer in
`TheBundleIdentityIsMeasuredAndNotRead`, and proved distinct from
`envelope_digest`. Because the walk measures FILES rather than the envelope's
declarations, a file the envelope never named changes the identity — a bundle
`read_bundle` accepts and the measurement does not, which is the case that
shows why the number is measured rather than read.

### THE RECORDED API GAP, before any owner change is proposed

`integration_contract` (W112630, accepted and closed) exposes no public bounded
no-follow file reader, no whole-bundle measurement, and no canonical JSON
serializer. Its `_read_exact`, `_descend` and `_component` are private; the
canonical form lives in `baton_v12.contracts.canonical`, which a worker in a
container cannot import. All three are needed by this workload: the manifest
digest and the accepted path-set digest are both taken over the canonical form,
and the measurement has to read every file in the bundle.

**No accepted child byte was changed and no owner change is proposed here.**
The workload implements its own bounded reader, its own measurement and a
restricted canonical serializer, under the same rules, and holds them equal to
their owners by CONFORMANCE rather than by assertion:
`TheTwoSpellingsOfCanonicalJsonAgree` compares the workload's canonical text
and digest with `contracts.canonical`'s over real manifests, assignments,
launches, path lists and non-BMP text, and the measurement is compared with the
producer's own `bundle_digest` over a really published bundle. That is the
mechanism this campaign already uses for the same problem at the same boundary.

The alternative — reaching into the accepted module's private helpers — would
bind this file to bytes that boundary does not promise. If a future Work wants
one implementation rather than two, the bounded owner change is to promote
`_read_exact` and add a measurement to `integration_contract`, and this
paragraph is the record that the gap was found and priced before it was worked
around.

### Three smaller decisions, pinned because a reader will ask

**The test-scope predicate is over-inclusive on purpose.** A path is read as a
test when a component is `test`/`tests`/`testing` or its name looks like one.
An `edit` or `delete` of such a path is admitted only when the accepted Job's
scheduled scope names it; an `add` is not gated, because repository policy is
explicit that adding tests needs no case-specific confirmation. A scope entry
is a PATH PREFIX at a component boundary, because a real accepted Job's scope
names directories — the world's own scope is `v12/python/tests/job_manager` —
and exact-equality matching would have refused every genuine scheduled change.

**The version-control witness is bounded and is named a witness.** The
repository metadata directory, its index and its HEAD are recorded before the
provider and compared after; a change is `held`, never repaired. This is not
whole-repository equivalence and the module says so: the provider runs with the
granted mount and may leave descendants, so what is proved is what was
observed.

**The recipe takes its base as a required build argument with no default.**
`Dockerfile.integration` derives from an explicitly SELECTED provider image
digest rather than reinstalling the provider runtime, so a build cannot happen
without naming the artefact the deployment already validated. That also means
this Work ships no built-artefact gate for the integration image: the
deterministic recipe and packaged-layout suite is what
`tests/manager/test_integration_image.py` owns, and an artefact gate follows
the first selected base digest. Building and selecting remain deployment acts.

### What this delivers

`v12/worker/integration_workload.py`, `v12/worker/integration_entry.py`,
`v12/worker/Dockerfile.integration`, `v12/python/tests/manager/test_integration_image.py`
and its registry entry, and the joined proof extending
`tests/manager/test_integration_worker.py`. W110774 stays gated until this
capability is independently accepted; image build/selection and live execution
remain separate acts, and historical broad failures remain unwaived.

## 2026-09-07T22:48:26Z — independent review and scoped correction, claim114048

**Confirmed:** all ten recorded implementation hashes match current files. The
workload/entry/recipe/image suite are present; prior wrapper methods and accepted
child source/test bytes are preserved. This supersedes the earlier absent-file
status. It does not accept the new workload. Exact review:
review-2026-09-07T22-48-26Z.md; retained evidence: evidence/review-114048/.

**Confirmed defects:** actual provider-process probes publish integrated with
failed, unfinished or missing verification; synthetic provider text crosses into
manager-visible argv and outside-path detail; unreadable result namespace can
start writable execution over an existing terminal result. The existing executable
edit positive changes0644 to0755 without explicit mode authority. Current semantic
checks use a generic accepted disposition and Job prefix membership, without
inspectable accepted decisions or the frozen review's per-test evaluation.

**Decision:** the existing whole-authority, diagnostic safety, conservative ending
and no-second-turn requirements remain in force. Correct the implementation; do
not weaken them. The previous delivered/awaiting-review state is superseded by
changes-required. Parent PLAN schedules local ending/refusal fixes and exact
bounded test fixture/expectation corrections, including actual verification
execution and the distinction between preserving executable mode and authorizing
a mode change.

**Split:** W114085, findings/finding-import-authorization-evidence/, owns the
substantial missing inspectable authorization producer in the existing
integration_bundle/contract/bundle-test paths. It is a follow-up to closed
W112630, preserving that accepted history. Parent retains workload consumption
and final joined acceptance. This supersedes the earlier keep-all-remaining-work
together exception for this newly discovered independent deliverable. The small
local ending/refusal fixes stay together with a bounded exception explained in
the review; reassess at handback. Ownership is distinct and no live claimant's
scope was changed underneath it.

**Observed verification history:** /tmp/w110935-gate.txt reports4985 tests,
11 failures/1 error; the dossier transcript reports4987 tests,11 failures/1 error;
/tmp/w110935-gate-final.txt reports4987 tests,12 failures/1 error. All report21
skips. The last adds an ordinary dogfood retry discard/quiescence failure,
recorded separately as W114077 for the later failure-behavior pass. No causal
integration-workload regression is established for that extra failure and no
red is waived. The draft's unchanged-distribution claim is superseded for that
final observation, not erased. Existing focused329-pass evidence is retained
and reused, not rerun.

**Authorship:** PROGRESS ends at claim113568; /tmp/w110935_progress.md holds the
author's later draft with GATE_SUMMARY unresolved. Both are retained unchanged.
The reviewer does not append the implementer's account or claim its changes.
No application/test implementation, live execution or Git mutation occurred in
this review. All required input paths were readable.


## 2026-09-07 — the four corrections from review114048, claim114241

baton.claude. Revalidated first: the ten hashes `evidence/review-114048/
audit.json` records still matched the tree, and W114085's accepted-interface
change to `integration_contract.py` and `tools/integration_bundle.py` was
already in place. All four findings are real and all four are corrected here.

### `integrated` now requires the scheduled verification, run HERE

The ending checked target bytes and the report's outcome word and never
required the verification to have completed. `_integrated_result` copied
`report["verification"]` through unchanged, and `check_report` is explicitly a
shape reader that admits a null verification and a null or non-zero status. The
reviewer's probes published `integrated` after a failed, an unfinished and an
entirely absent verification, and over a report still claiming `preflight` with
no paths.

**The command is bound to the accepted evidence and the status is this
runtime's own observation.** `tests.json` is `driver.ordinary_test_evidence`,
whose observation carries the exact argv the accepted candidate's producer ran,
cross-bound by `checkpoint_id` to the checkpoint this bundle carries — and that
binding is already correlated before the command is read. The workload resolves
it BEFORE the provider starts (so a bundle naming none refuses without a turn),
runs it over the imported target after the read-back, and holds on any non-zero
status, timeout or failure to start.

**What is deliberately NOT taken from that evidence is its `status`.** That is
the historical ordinary-test run, which a reviewer may have accepted while
failing; this integration's own outcome is decided by running the command in
this turn. The two are different questions and the child FINDING's acceptance
names the distinction explicitly.

**And the report must corroborate what it claims.** A report claiming an import
while still at `preflight`, or naming a changed-path list that is not the
completed table, is `held`: a provider that claims an import while describing a
turn that never reached one corroborates nothing.

The verification child runs with BOTH STREAMS ON `/dev/null` and a composed
environment, which is `claude_agent._ran`'s rule and not this file's to relax:
this is code out of the candidate a provider just imported, running as the same
uid, and W39357's review found exactly that command's output carrying a bearer
into a host-visible document. What crosses the boundary is an integer.

### No provider-authored text reaches a manager-visible result

Two channels carried it and the reviewer's canary rode both: `_report` copied
the provider's own out-of-scope path strings into a hold's detail, and
`_integrated_result` forwarded the report's `verification.argv`. My own FINDING
already said paths are rendered from the validated table only; the
implementation did not do that on those two.

**The rule is now uniform and stated in the module docstring:** every path in a
result is rendered from the validated accepted table, every command is the
accepted one, every reason is from this module's closed vocabularies, and
anything else crosses as a COUNT. An out-of-scope report now publishes how many
there were and not what they were called. Canary regressions cover both the
integrated and the held result.

### The filename heuristic is gone, and what replaced it

`is_test_path` guessed which paths were tests and then checked prefix
membership in the accepted scope. Review [P1]: "a filename heuristic also
cannot stand in for that reviewed enumeration." It is removed.

**The accepted Job's scope IS the enumeration**, and W114085's `authority.json`
carries it with the frozen review's own documents. The workload consumes that
account: the review must have accepted the candidate, the account must be about
the Job admission resolved, and a row requiring an existing-test decision must
have review material to have decided it. The contract has already refused an
account that does not describe its own path table or claims a grant of a kind
no accepted owner supplies.

**THE RESIDUAL RISK IS NAMED RATHER THAN COVERED OVER.** A test file the
accepted Job never scheduled is, to this runtime, an ordinary content change —
because the only mechanical enumeration available IS the scope, and guessing
was what the review rejected. What stands behind it now is evidence instead of
a guess: the frozen review's documents travel in the bundle and the prompt
requires the provider to evaluate them before importing. Catching a test change
the accepted Work never scheduled is the REVIEW's responsibility, and this
extension is what makes the review's answer readable inside the container at
all. `test_the_accepted_scope_is_the_enumeration_and_not_a_filename` records
both halves.

### The mode cases, split the way the review asked

`test_an_edit_preserves_the_reviewed_mode_and_an_executable_one` took a 0644
base to a 0755 candidate and called that preservation. It is split:

- **preserving a mode**, including an existing 0755, which imports;
- **an unauthorized mode change**, which the PRODUCER now refuses to publish at
  all, so no bundle exists to carry through an entry, no provider starts and
  the target is untouched;
- **an explicitly authorized mode change, which cannot be constructed and is
  not pretended to be.** No accepted record in this build carries mode or
  executable scope; that gap is W114085's recorded finding and the named next
  capability. The case says so rather than fabricating an authority to test
  against.

### An unreadable result namespace is no longer an absence

`existing_result` answered `None` for every `OSError`, so the entry's own
documented rule could never fire and the reviewer's probe watched a second
writable provider turn happen over an attempt that had already answered behind
a symlinked namespace. `None` now means exactly one thing: this runtime opened
the namespace, proved it, and found no result file. Every other error raises,
and both callers treat that as a refusal before any provider starts.

## 2026-09-08T00:01:58Z — corrected-candidate review, claim114486

**Confirmed:** the parent workload/entry/worker-test hashes match the author's
claim114241 account. Required verification now actually executes; provider argv
and outside-path text no longer cross the two reported channels; unreadable
result namespaces no longer start a provider. Mode preservation and unsupported
mode-change refusal are correctly distinguished. The older all-four-corrected
and awaiting-acceptance claims are superseded by the changes-required disposition
in review-2026-09-08T00-01-58Z.md and current PLAN.

**Confirmed P1:** all scheduled-path readback and the metadata witness comparison
precede the newly added verification subprocess. A zero-exit verifier that alters
candidate bytes/mode, deletes the candidate or changes the witness still produces
`integrated`. Four independent subprocess probes reproduce those outcomes;
unchanged success and nonzero-exit hold controls behave correctly. Final success
must use readback after verification as well, without repair or any claim of
whole-tree equivalence or manager-owned quiescence.

**Clarification, superseding claim114241's residual-risk acceptance framing:**
Job test_scope enumerates scheduled authority, not every test actually changed.
The earlier rejection of a filename heuristic did not authorize unscheduled
existing-test mutations. The provider's semantic preflight covers the entire
candidate, including test changes outside the authority rows, and refuses missing
scope or missing frozen-review evaluation before import. Current prompt only
requires evaluation for the listed authority rows, so an empty list bypasses
that instruction. The derived unscheduled-test probe imports an assertion change
and publishes integrated; its deterministic provider does not evaluate review
text, so this is a consumer-boundary probe, not a real-model behavior claim or
proof of producer provenance. Parent semantic acceptance remains unresolved.

**Observed verification reconciliation:** retained corrected gate5016/270.808s
has12 failures/2 errors/21 skips; final gate5016/258.000s has11 failures/1 error/
21 skips. Final failure identities equal the earlier4987/269.991s dossier gate;
this is not causal baseline proof or a waiver. The corrected run adds two
worker-entry engine outcomes, now W114516 for the later failure-behavior pass.
The earlier W114077 retry-discard failure appears in neither new log and remains
unresolved. Reused focused358/26.688s evidence is not a new reviewer suite run.

**Ownership/evidence limit:** W114085 was actively correcting its three files
during this review. Parent/wrapper/recipe/image/registry hashes remained stable;
child contract/producer bytes differ from the parent's author audit, and child
contract/tests also moved between reviewer measurements. Both measurements are
retained. Narrow probes used that working child interface and do not constitute
acceptance of an immutable joined candidate. M114514 coordinates the boundary.
No application/test implementation, engine/live-provider run or Git mutation was
performed by the reviewer; author-owned PROGRESS was not edited.

## 2026-09-08 — repeated managed-turn completion before handoff

Observed by baton.prompt during Slawomir's operational investigation: incidents
35–39 follow status responses that end the ACP turn while the gate/handoff is
still outstanding. The bridge then tears down the process domain and records the
surviving claim. All five share one session; releases reload that same session.
The connection cleanup errors observed in two cases follow teardown and are not
evidence of an initiating crash. See RUNNER-DIAGNOSIS-2026-09-08.md for exact log
locations, source mechanism, evidence limits and proposed bounded tuner takeover.
Model/session/adapter causation remains open. No assignment or implementation
scope was changed in this investigation; current live claims retain ownership.

## 2026-09-08 — bounded tuner takeover after incident 40

Slawomir confirmed execution stopped and completed release114685 of the stranded
W110935 assignment episode114543. Canonical inspection114692 finds the parent
unclaimed and dispatch paused with no blocking claims. The interactive recovery
sequence now proceeds to the proposed bounded tuner takeover. This supersedes
the prior baton.impl assignment for the remaining parent correction only;
baton.codex retains independent review and W114085 retains separate ownership.

The PLAN's new takeover section names the three owned parent paths and preserves
the already scheduled test corrections, current acceptance requirements and
Claude's attributable progress. Reuse applicable evidence and target remaining
failures; a Handler change does not justify another full-suite run. No bridge
behavior change or general expansion of the tuner role is authorized by this
bounded allocation. The runner diagnosis remains a separate operational concern.

## 2026-09-08 — Claude restored under the foreground setting

Slawomir chose the supported background-task disable setting and explicitly said
to return to Claude as implementer. This supersedes the temporary tuner
allocation above. PLAN now makes baton.impl the executor of the same retained
parent correction, with its exact file/test scope and independent review intact.
The operational change is W114716 at
work/records/2026/09/finding-managed-claude-foreground-verification/.
Routing is restored while dispatch is paused; installing/verifying the setting
and restarting precede dispatch resumption. No test rerun or candidate acceptance
is implied by that routing change.

## 2026-09-08T00:48:39Z — parent correction review, claim114828

**Confirmed:** return114825 supplies parent hashes b2dfbafb/0885dda0/74a39f8a,
all independently matched and retained in evidence/review-114828/. Post-verification
candidate and witness observation now holds mismatches without repair; independent
restored-deletion and symlink-replacement probes both hold. Whole-candidate semantic
test-authority instructions now apply even with no grant rows and name the accepted
scope and frozen review documents. This supersedes the two parent changes-required
findings of review114486 at their deterministic workload boundary, not the separate
requirement for accepted frozen evidence or proof of actual model judgment.

**Current acceptance:** review-2026-09-08T00-48-39Z.md accepts those local
corrections but leaves final joined capability acceptance pending the independently
accepted evidence-binding producer. Child bytes captured here equal review114618,
whose full frozen-result digest comparison remains under correction. Parent final
join and correlated negatives remain required; no closure, image selection, live
execution or downstream release is implied.

**Observed:** the retained gate3 log completed5013 tests/259.994s with11 failures,
2 errors,21 skips, including a dogfood image-build setup error exit143 in addition
to historical failures/registry error. M114847 adds the observation to W114516's
later failure-behavior investigation without attributing cause or waiving reds.
The author's371-pass focused result is reused; reviewer execution added only two
targeted probes. No broad rerun or source/test implementation occurred.

**Clarification:** the unchanged parent scope-enumeration test's comments describe
grant rows only. Their residual-risk wording is superseded by the requirement to
evaluate all actual existing-test changes before import. At joined handoff clarify
that wording without weakening assertions or the new refusal coverage. The latest
author entry calls itself claim114742; canonical114742 is a reroute and114798 the
actual claim. The next author account should append that attribution correction.

## 2026-09-08T01:11:08Z — accepted provider and final technical join, claim114978

**Confirmed:** owner close114974 accepts the child frozen-result binding at
review114869's exact bytes. Revalidation in evidence/review-114978/joined.json
matches all ten parent/child files before and after three independent joined
probes. Valid producer evidence reaches actual provider import, byte/mode readback,
real verification and the public integrated-result parser. Both original-digest
review rewrites and removed-output tampering refuse through the real entry with
zero provider turns and unchanged target bytes/modes.

**Disposition:** review-2026-09-08T01-11-08Z.md accepts the joined deterministic
workload behavior. This supersedes the pending-provider/pending-technical-join
status in review114828. No fixture adaptation or new implementation correction
is needed, and applicable reported374-test proof is reused without suite rerun.
Historical failures and separate live/image/production boundaries remain intact.

**Remaining scheduled completion:** author-owned joined progress and stale test
comments have not yet been updated. Return to baton.impl only for the two named
test docstrings/comments and an append-only parent author account, preserving
all executable statements/assertions and prior history. The next review is a
bounded documentation/identity audit, not a new verification campaign. The exact
scope is in the newest review and PLAN; no child or generic-core edits are added.

## 2026-09-08T01:17:01Z — final independent sign-off, claim115023

**Confirmed:** author claim115010 completes the two scheduled test docstrings/
comment and appends the joined progress/provenance account. Final test hash
a35013a2 matches the handoff; independent whole-file executable-AST comparison
is identical and all77 methods/assertions/fixtures remain. The other nine
candidate files are byte-identical to the accepted join and child. Exact final
candidate, audit and documentary diff: evidence/review-115023/.

**Disposition:** review-2026-09-08T01-17-01Z.md signs off W110935 for owner
acceptance and satisfying closure, superseding the pending author-completion
status in review114978. No implementation, documentation or review correction
remains. The prior technical join and applicable reported374-test proof are
reused without execution. Historical reds and separate live/image/production/
quiescence boundaries remain intact. Owner disposition releases the production
composition consumer; it is not a production execution or Git authorization.
