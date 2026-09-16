# First implementation packet — context admission and custody

Prepared by baton.tuner under W161234 claim174751, 2026-09-15. Status:
**ready for baton.ops execution selection**, not implementation admission or
product acceptance. The current claim edits only this dossier's preparation
evidence, FINDING and PLAN. No product/test edit, test, provider or engine run.

## Selected authority and revalidation

The owning FINDING's owner selection and reroute174747 select preparation from
the accepted architecture, with its independent review clarifications:

- baton:work/records/2026/09/finding-v12-context-reuse-design/DESIGN.md,
  SHA256 `5da337d20d0bd62ba3e2d65128ce046b0ef318bf1f1512cb47ee8ca44bcbf3c7`.
- The same dossier's review-2026-09-15T03-11-07Z.md,
  SHA256 `f9152ee645e4b82a92f4d2436e8aff998425dd4df90d5176e52ba57b2123c28d`.

That architecture is already accepted; no repeated architecture review is
requested. W161230 closed satisfying and discharged this Work's prerequisite.
Its final selected outcome is independently accepted in
baton:work/records/2026/09/finding-v12-managed-integration-execution/findings/finding-managed-integration-acceptance/review-2026-09-15T03-21-13Z.md
with ACCEPTANCE-174271.md and BASELINE-CLASSIFICATION-174271.md in that dossier.
Those records preserve deterministic qualification, historical red tests,
W129838, manual unknown-start/target recovery and the finite recovery cuts.
This packet does not certify a whole suite or live OCI/provider behavior.

BASELINE-174751.json records 57 comparisons: the selected design's 26-file
baseline plus the 31-path managed candidate174130. All product source comparisons
match. Two comparisons differ: the mutable release checklist has advanced; and
tests/tools/test_execution_limits.py now replaces the old schema-version-equals5
assertion with a version-at-least5 assertion and an explanatory comment. The
surrounding generation0 compatibility assertion is unchanged. This is an
observed later test change, **not accepted by this preparation**; its authorship
and independent acceptance are not established here. Do not attribute the old
300-test run to that changed test's current bytes. No such test runs in slice A.
The current manual matches accepted candidate174420. All four A paths below are
absent at this inventory; absence alone is not evidence of missing behavior.

Current source confirms ControlStore.transact's BEGIN IMMEDIATE, in-lock replay,
atomic result journal and durable-refusal semantics. Existing schema18 clean
initialization remains sufficient. The new context owner can read its own
operation rows through its implementation and publish outcomes through transact;
callers never query the journal or write synthetic ready records.

The final stage implementation ending still calls review_driver.end_implementation
then _finished. That driver owns quiescence, frozen/accepted result, retained
proposal, checkpoint/writer fencing and cleanup. Slice B inserts context
finalization between those calls; the ordinary ending obligation remains owed
until finalization succeeds. It does not move or replace the accepted driver.

## Exact first assignment proposed to ops

Select **A only**, one serial implementation claimant followed by independent
baton.feat review. Proposed editable product/test paths, all new regular files:

| Path under baton:v12/python/ | Owner and finish |
| --- | --- |
| src/baton_v12/worker_manager/provider_context.py | Context/profile/use identity, validated journal transitions, admission, historical finalization, hold and pure observations |
| src/baton_v12/worker_manager/context_delivery.py | Typed protected storage/delivery, descriptor pins, fresh per-use working copy, immutable generation publication/adoption and scoped disposal |
| tests/manager/test_provider_context.py | Real temporary ControlStore and owner-fixture identity, contention, replay, refusal and historical-finalization proof |
| tests/manager/test_provider_context_delivery.py | Real temporary filesystem custody, forbidden credential reads, object substitution and publication crash proof |

The implementing claimant appends its own PROGRESS and maintains the owning
FINDING/PLAN, exact candidate/patch/base-absence inventory and verification
evidence. This preparation does not write PROGRESS. Import new submodules directly;
no worker_manager/__init__.py exports, schema/store/documents edits, generic
port additions, production wiring or existing test edits are proposed for A.
Standing test authority supplies these scoped additions without another test
approval. A concrete required extra product boundary goes back for scope
disposition; it must not be implemented inside a fixture.

Ownership check: canonical W63255 at snapshot174782 is actively held by
baton.claude; its selected paths are intake.py, dogfood_operator.py, the bounded
__init__.py export and its selected tests. They remain read-only consumers here.
W61599 at snapshot174781 is queued to baton.ops for further design corrections;
its latest plan explicitly includes future stage_execution.py composition.
A's four new paths overlap neither selected path set. Ops selects one writer
for A; before B, re-read both owners and establish the exact serving-path handoff,
especially claude_agent.py, single_worker.py and stage_execution.py. These
snapshots do not reserve future ownership or interrupt another claimant.

## APIs and owner facts to implement in A

Names below refine the selected design's APIs; their closed operands must be
implemented and tested together. There is no caller-supplied healthy boolean.

| API boundary | Required owner facts / result |
| --- | --- |
| certify_context_profile(control, profile) | Closed, digest-bound dedicated CLI profile and provenance kind; deterministic qualification cannot enable a production profile |
| admit_context_use(control, jobs, authority, *, attempt_id, writer_id, profile_digest) | Actual implementation assignment/principal, original Job and limits, line/repo pins, current writer generation; derive context and deterministic use, open/restore and expected provider UUID |
| context_of(control, context_id); context_use_of(control, attempt_id) | Pure validated projection; opaque IDs, bounded status/reason/digests, no paths, manifest entries or provider prose |
| finalize_context_use(control, jobs, authority, *, attempt_id, storage, receipt_reader, runtime_reader, checkpoint_reader) | Resolve the original admitted use; read historical assignment/Job, accepted receipt, checkpoint and positive runtime exclusion; seal then journal exactly one generation |
| hold_context_use(control, *, attempt_id, reason, evidence_refs) | Exact current-use transition with a closed reason; cannot manufacture exclusion, health or restoration |
| retire_context(control, context_id, ...) | Selected design's explicit terminal disposition only after no active/unknown writer; no purge or automatic fresh-context fallback |
| materialize_context_use / adopt_context_use | Typed ContextDelivery from context owner plus configured protected storage; create only a fresh use, or adopt exact existing pins/operands |
| seal_generation / scoped discard | Owner-resolved use and positive exclusion, private allowlisted state only; exact operation staging, measured manifest and durable publication; discard only owned excluded staging/use paths |

The finalization signature above explicitly supersedes DESIGN's illustrative
receipt_body-only form in accordance with its selected review. Reader arguments
are owner capabilities, not unverified documents or boolean callbacks. Bind
their actual adapters to existing readers: attempts.assignment_of,
attempt_runtime_of and boundary_identity_of; intake.intake_receipt_of,
retentions_of and cleanup_of; review_cycles.writer_of/checkpoint_of/verdict_of;
and ending.settlement_of for the preceding correction's settlement. The receipt
reader also proves exact frozen digest/length, accepted artifact identity and
retention; provider JSON by itself cannot assert accepted collection.
Jobs/Authority supply their actual Job/assignment/principal facts. Do not expose
a fake owner-reader bypass in production to make A tests pass.

For finalization, an historical fenced assignment remains valid evidence of the
old use, not live invocation authority. Resolve its original protected root pins
and original operation before any fresh admission. Never call live admission
to recover an ending, recreate cleaned launch roots or request an engine start.
The current ending itself need not already be settled: finalization precedes its
settlement. A restore admission does require the prior actual correction verdict
and settlement, a newly routed attempt and a fresh writer grant on the same line.

## Transition and filesystem order

1. Validate closed types, identity/profile and immutable operands. Context identity
   binds Authority, Job, Work, line and actual actor/principal; profile/model or
   purpose changes refuse inheritance. Persist the first provider conversation
   UUID before delivery. Restore keeps that UUID with a fresh use/invocation.
2. Derive operation identity from **action, context, use and expected revision**;
   sign every immutable operand. In transact's write lock, derive the head only
   from validated committed transitions and recheck the predecessor and occupied
   use. A malformed row refuses; a refused row never becomes the state head.
   Competing admissions produce at most one successor. A durable refused
   competitor cannot consume the incumbent's finalize/hold identity. Exact failed
   replay stays failed; a distinct authorized transition uses its own identity.
   Changing op-id to evade a collision is prohibited.
3. Configure protected context storage outside source, credential, generic attempt,
   output, verification and intake roots. Pin ancestry and objects with no-follow
   descriptor-relative traversal. Before first runtime launch, establish a
   manager-readable custody/normalization policy for the runtime UID/group. A
   generation stays immutable and is never mounted writable; each use gets a
   fresh working copy, fresh cache/TMP and a fresh invocation witness.
4. Only the profile's positive state allowlist can enter a generation. Reject
   symlinks, hardlinks, special files, traversal, overlap, replacement, excessive
   entries/bytes and mismatching existing objects. The one exact volatile
   credential link is recognized by metadata and excluded without opening its
   target; a substituted link or ordinary credential file refuses. Invocation
   witnesses are outside restored state. Transcripts, paths and manifests remain
   private; public metadata carries bounded opaque identities and digests.
5. After actual accepted receipt/checkpoint and positive old-runtime exclusion,
   reopen the pinned use root and build only this operation's deterministic
   staging. Hash bounded allowlisted bytes, fsync staged contents and publication,
   then commit the generation transition. Receipt or provider exit alone is not
   exclusion. Inaccessible/replaced roots hold after exclusion; no chmod,
   relocation, broad home copy or caller-selected replacement path.
6. A crash before journal publication may validate an already-published matching
   generation or rebuild only its own incomplete staging from the same excluded
   pinned source. A mismatch never overwrites evidence. A committed missing or
   damaged generation holds. Reopen after commit adopts it without another copy,
   generation, provider call or engine start. Unknown invocation stays held even
   after later exclusion; no missing-result reprompt.

This proves the selected filesystem/protocol boundary, not a general same-UID
sandbox or detection of arbitrary secrets hidden inside permitted provider data.

## Focused deterministic verification and A finish

After ops selects execution, use project-pinned dependencies and record actual
interpreter/dependency versions, source/profile hashes and per-run elapsed time.
Proposed selector from v12/python, PYTHONPATH=src:tools:.:

```text
/home/sl/src/baton/.venv/bin/python3 -m unittest tests.manager.test_provider_context tests.manager.test_provider_context_delivery
```

Use an owning supervisor with a sensible initial 60s run ceiling, TERM5s/KILL5s
grace and positive process-group cleanup. This is a proposed run, not executed
evidence. Cumulative stopwatch totals are not execution gates. No provider,
engine, installation, image build, whole-suite discovery or existing integrated
trace rerun belongs to A.

Required meaningful cases: two real ControlStore connections racing admission;
same-operation exact success/refusal replay and changed operands; wrong
Authority/Job/Work/line/actor/purpose/profile/writer/repo pins; genuine predecessor
verdict/settlement and missing/stale generation; refused competitor followed by
successful incumbent finalization; historical fenced ending after cleaned generic
roots; no starts while recovering; inaccessible/replaced protected root hold;
credential target whose read would fail the test; symlink/hardlink/overlap and
size/count refusal; fresh copy versus immutable generation; fresh witness absent
from restore; crashes before publication and before journal commit; damaged
committed generation and pure observation with unchanged journal/files.
Use real public owner operations for fixture facts and real temporary files;
never insert fabricated ready rows. Deterministic provider-layout fixtures must
be labelled simulated and cannot qualify the production CLI profile.

A finishes when those ownership/custody outcomes are independently accepted on
the exact four-file candidate, with all failures and limits accounted for. It
does not finish W161234. B still owes versioned launch/receipt and normal serving;
C owes useful corrected code through independent review/managed import and
fresh-manager reopen with nonzero provider/engine counts plus deliberate
duplicate-detection negatives. Preserve the release checklist's specific
consumer reconciliations, including W61981/W62098/W62535, W110783 versus the
accepted driver/consumer, ordinary start-intent and refusal reason preservation.

## Separate provider qualification obligation

Read-only evidence inspected: W106673's accepted
baton:work/records/2026/09/finding-v12-live-session-workspace-detach/review-2026-09-07T20-20-41Z.md
and its public evidence/live_supervisor_result_diagnostics.py (argv and result
projection). They establish useful same-session correction after positive old
shutdown for CLI2.1.247, requested claude-fable-5[1m]/actual claude-fable-5.
The helper uses stream-json at /session/work and retained whole private home;
it does not establish the selected normal one-shot /output minimal state layout.
No private original, transcript or credential was read here.

Remaining exact facts: pinned production image/CLI/model; credential-free positive
state layout at the actual cwd; and one-shot terminal session/model/status fields
with bounded complete-record parsing. Keep qualification unavailable for that
production profile until owner-selected evidence proves these facts. An image
label, fixture or caller's healthy flag cannot supply it. Ops may separately
select a minimal two-turn provider-specific qualification if available nonsecret
evidence cannot answer it, with measured limits and confirmed first-runtime
shutdown. No such run or production enablement is authorized by this packet.
This open provider fact does not prevent selecting deterministic A.

## Return

Ops next: select the four-file A implementation claimant and focused verification,
preserve independent implementation acceptance, and separately schedule provider
qualification before production enablement. No new architecture gate is needed.
Preparation runtime verification spending is **0s**. A read-only inventory first
used the wrong candidate JSON key and failed before writing evidence; the corrected
inventory produced BASELINE-174751.json. No product behavior was executed.
