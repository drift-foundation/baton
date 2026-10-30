# Bounded authoring shutdown deadline correction — W338305

2026-10-20, baton.rvpc under coordination claim W338289/338291. Owner selection
is baton:work/records/2026/10/finding-v12-authoring-expiry-finalization/FINDING.md,
“owner selects the bounded shutdown correction”, conveyed by T338289/338289.
This is the selected product correction, separate from accepted diagnostic
W337955 and from its now-expired direct-execution exception.

Confirmed input: diagnostic review-2026-10-20T11-44-22Z.md in that record;
DIAGNOSIS SHA256 bada77bd740f53d712ff623e432afa8b3d7a5f10601b0fa7e021aee181e7c7ed.
Base fb48797903160aa764229d58f3a5beaf29648bfc remains current HEAD at preparation.
Controller v12/python/tools/authoring_enforcement.py SHA256
bc8c0363e44fedeae09c15a9065733227f08e279164ed68dc4b0e9e058a7c50f;
baseline work/records/2026/09/finding-v12-single-implementation-proof/baseline.py
SHA256 c1b0a10e609503df0ba7ebdc7455cc8518c9175882edd185b65f20c342c4bd2f.
Accepted reproduction retained in diagnostic evidence/review-338248. No new
execution or historical stack attribution is claimed here.

Confirmed mechanism: controller supervise_process:258–306 reserves a tail from
cleanup_seconds and kills before collecting RemoteGuard final state; baseline
supervise cleanup at1293 starts a fresh full allowance after signal handling and
pre-cleanup accounting. Child_main:459 reaches Guard.stop only after baseline
returns. Seven real-process/fake-engine comparisons established competing windows,
phase-dependent signal handling and delayed final publication. Unknown cessation
stays held even when a final report exists. Historical live blocked step is unknown.

Selected outcome: propagate one bounded shutdown allowance/deadline through the
coupled composition, reserving accounting, guard stop/join and publication time.
No fresh window may outlive the remaining outer allowance. Bound steps, not just
checks between potentially blocking steps. Cooperative cleanup publishes honest
workload/enforcement outcomes before cutoff; uncooperative cleanup/publication
produces bounded, attributable partial/unknown evidence. Preserve original total,
provider and token limits, single-manager guard and once-only admission. Preserve
exact-runtime/launch uncertainty holds; do not equate process death, expiry or a
report filename with cessation or success. Confirmed execution cessation/status
must not acquire a new output-quality/final-report release gate. DESIGN primary
lifecycle, LIM-4, OBS-3, REC-1 remain normative; no spec adjustment selected.

Acceptance behaviors: normal return, pre-serving cancellation/admission fence,
expiry in blocked serving sweep, absent writer with pending cleanup, cooperative
ending before outer cutoff, delayed and stuck publication on both sides of cutoff,
unknown engine/launch cessation, repeated signal during deferred cleanup, original
limit preservation, exact attribution of partial outcome and process/guard cleanup.
Use deterministic provider/engine boundaries with real owner composition; no
900-second wall replay. Existing accepted defect coverage must remain. The author
chooses tests/commands and necessary files; test changes are authorized by standing
policy. Existing tests/manager/test_authoring_enforcement.py and
 test_authoring_manager_guard.py are evidence/coverage locations, not an edit list.

Decomposition: keep the deadline/ending correction together: its cross-process
contract and final reports have one coupled acceptance result. Separate immutable
execution-packet preparation W338308 from product execution because preparation
can be reviewed before any live operation and exposes self-hosting risk. Renewal
W333485 and diagnostics W333486 stay separate consumers; W325959 joins acceptance.
Install both consumer dependencies on W338305, and W338305 on W338308. Correction
closure must include independent candidate acceptance and an observed accepted
base for consumers, not merely producer exit or packet acceptance.

Ownership: reviewer FINDING/PLAN/reviews; baton.codx preparation artifacts in the
packet record and later isolated product candidate only after execution selection.
Product PROGRESS belongs to actual author. Existing source locations above may be
changed in a future isolated candidate; original diagnostic evidence, sealed
packets and retained instances are never rewritten. Sibling product allocations
remain with their existing authors; shared source integration is serial. Broader
scheduling/renewal, general supervisor refactoring and diagnostic UX are excluded.

No host product patch, revived exception, new live authoring run, recovery,
deployment or Git mutation is authorized by this record. Exact concrete launch
operands require review/selection. Missing runtime capability must be evidenced
at the supported boundary, not inferred from a known finalization risk.

## 2026-10-20 — owner selects direct implementation and verification exception

Slawomir explicitly approved the copilot's bounded bootstrap exception:
"yes, lets do direct this time". Recorded by baton.prompt. This selects direct
implementation in a disposable workspace, focused deterministic tests and repeated
correction/test iterations for W338305, including independent reviewer reproduction,
through independent candidate acceptance. The reason is the circular dependency
on defective v12 authoring/finalization and owner-mediated retries.

This supersedes the isolated-packet execution selection requirement above and
the no-direct-product-execution wording for W338305 only. Earlier exceptions remain
expired. Preserve packet-338345 and its static review as historical preparation;
do not launch it. W338308's execution-selection purpose is superseded by this
choice, not failed static review. The live handler must explicitly disposition its
obsolete gate and read back the graph; prose does not remove the dependency.

Accepted correction scope and acceptance behaviors above remain unchanged.
Implementer owns the bounded fix through its focused verification and ordinary
iterations; reviewer independently evaluates exact candidate bytes and reproduces
the real-composition cases with fake engine/provider boundaries. Use sensible
per-run timeouts and verify process/guard cleanup. No repeated owner approval is
needed for routine tests or corrections within this scope. Record actual changed
test paths and reasons; coordinate overlapping source ownership. Deliver retained
candidate/base provenance and honest measured/unknown results for human integration.

The exception excludes live engine/provider operations, deployment, retained-instance
recovery, Git mutation, renewal implementation and diagnostic UX. It expires at
independent acceptance. Human integration and a real v12 validation run remain
separate selections. Original limits, exact-cessation semantics, unknown holds and
independent acceptance must not be weakened to get a passing result. No DESIGN
change is needed. Diagnostic checkpoint70760ef is observed.

## 2026-10-20 — owner separates general policy from job-specific authority

Slawomir instructed that AGENTS should not generally name Jobs and requested its
cleanup. baton.prompt removed the duplicated temporary execution-exception
sections from AGENTS and replaced them with general guidance for recording bounded
owner exceptions in FINDING/PLAN/handoffs. This supersedes the location wording
above that treated AGENTS as a second copy of this exception. The direct
implementation/test/review authority recorded in this FINDING remains unchanged,
including its scope, exclusions and expiry. This is documentation cleanup, not
revocation or an additional execution gate.

## 2026-10-20 — direct correction dispatch, reviewer claim338466

Read full current events through338466 and thread through338449. Closed preparation
W338308 satisfying338463 while preserving its accepted static result and explicitly
superseding proposed launch. Detail readback338465 confirms no open blocker on this
correction and both consumer gates intact. Keep coupled correction as one bounded
outcome; no further decomposition needed. Route to codx for complete fix plus focused
verification under NEW exception, not partial edits followed by routine approval.
Current PLAN pins direct provenance/ownership and outcome-based verification; old
packet-specific command ceilings no longer define this direct execution vehicle.
No product code/test execution by reviewer during coordination.

## 2026-10-20T12:29:38Z — independent correction acceptance

baton.rvpc claim338596 accepts exact candidate manifest
 a2fe281fbeac8e0c2fa58628aafc2c658a704ed5063a0eed689babced4d2ba83
and archive c2bcbadbb141bf4ffbecbbd346a5d185205c7c4cc795b6c295f3dfad3f3395e6.
Review review-2026-10-20T12-29-38Z.md binds six changed paths, all1193 base/1196
candidate hashes, independent44-test pass including eleven process cases, measured
73.374157594s command time, cleanup and limitations. No integration/live run occurred.
The NEW W338305 direct exception now expires at this independent acceptance.
Human integration/checkpoint and real v12 validation remain separate selections;
keep consumer gates pending observed accepted corrected base. This supersedes the
implementation-in-progress milestone, not earlier history or simulation limits.

## 2026-10-20 — corrected base delivered; owner requests next run

Slawomir imported the exact reviewed patch and committed
bc925cf5c62d69426ed5862af4d41f4d2a967b0f. baton.prompt independently compared
all six committed paths with accepted candidate hashes; all match. This satisfies
the pending human integration/checkpoint above. No new product changes or Git
mutations were performed by prompt.

Owner now asks to do another run. Coordinate fresh bounded v12 execution using
the corrected base and host/controller inputs, with exact operator commands and
final-result/cessation observations. Existing sealed authoring packets use older
inputs and are not selected for retry. The reviewer should disposition accepted
base delivery and resolve/read back dependent gates through its authorized claim,
then prepare the concrete next run, preferably useful consumer work. No scope
reapproval is needed for the accepted correction. Actual execution operands must
be concrete before launch; no retained-instance recovery, unbounded retries or
revival of the direct exception is inferred.

## 2026-10-20 — corrected-base acceptance and consumer continuation, claim339397

Observed owner commit bc925cf5c62d69426ed5862af4d41f4d2a967b0f. Independent
read-only comparison of all six committed and current checkout paths matches the
accepted CANDIDATE-338472 bytes; INTEGRATION-339397.json records exact hashes.
This completes corrected-base delivery; independent44-test acceptance remains
applicable without repeating execution. Direct exception remains expired.

Owner event339385 requests another bounded run with concrete commands. Preserve
existing consumer identities: W333486 diagnostics is the preferred next useful
run (no repeated incomplete renewal attempt); W333485 renewal remains separately
allocated. Prepare fresh packets on corrected committed inputs, never edit or
retry sealed historical packets. Actual host controller AND staged baseline and
shutdown helper must use accepted bytes. Preparation is not launch selection.

Classify W337955 scheduling gates as fulfilled diagnostic evidence: accepted
review and owner diagnostic checkpoint70760ef plus accepted correction commit
above satisfy their purpose. Remove those now-stale scheduling edges only;
W337955 remains open at its owner endpoint for terminal disposition, preserving
its containment/evidence. Closing this correction satisfies its own consumer
edges. W325959 stays the joined acceptance consumer; neither sibling is accepted.

The independent consumer outcomes are already decomposed. Packet refreshes may
proceed independently within their own dossiers, with existing author ownership;
no shared source edits and no direct implementation. Require exact fresh
root/run/image/network/credential-reference operands, one invocation/no retry,
initial900-second token,3600 provider/30 verifier,4800 total/60 cleanup limits,
actual runtime compatibility, corrected shutdown/final-result collection and
honest expiry/unknown-cessation evidence. Owner-facing short commands must come
from verified fresh packet inputs, not guessed substitutions into old commands.

Canonical disposition readback339432: W338305 closed satisfying339412, no handler;
W333485 and W333486 each have zero open blockers. Diagnostic stale edges removed
339409/339410; correction edges remain satisfied historical dependencies.
W333486 fresh preparation passed baton.impl339418 and claimed by baton.claude;
W333485 preparation passed baton.codx339431 and queued unclaimed at readback.
Both remain open and gate joined consumer W325959. No rvpc claim remains on these
three Works. Exact launch commands are a required fresh-packet deliverable, not yet
available or represented as accepted; no run was launched by this coordination.

## 2026-10-30 — Owner-approved removal of duplicate expanded candidates

Slawomir approved preserving the candidate archive and restoration instructions
instead of two untracked expanded copies. All 1,196 regular files in each of
`candidate-338472/` and `review-338596/candidate/` were verified byte-for-byte
against `candidate-338472.tar.gz`; the archive SHA256 matches CANDIDATE-338472.json.
Only those matching untracked files are removed. The archive, manifests, patch,
review reports and composition evidence remain. Historical paths are recoverable
using RESTORE-CANDIDATE-338472.md; no historical review or evidence is rewritten.
This supersedes retaining these two expanded copies, not the permanent dossier.
