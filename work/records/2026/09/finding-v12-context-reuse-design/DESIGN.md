# Concrete context reuse and restoration for W161234

Recommended design, 2026-09-15. Author: baton.tuner, W174289 claim174293.
This is a selection packet, not implementation authority or independent acceptance.
All repository locators below use the `baton` root. Source paths are relative to
the repository unless a table explicitly says `v12/python/`.

## 1. Recommended selection

Implement serial restoration of one protected Claude CLI conversation for one
development line and actual producer. Give each correction a fresh attempt,
exchange session, context use and writable context working copy. Reuse only a
committed context generation whose previous invocation completed and whose old
runtime is positively excluded. Keep the immutable generation outside every
worker mount. A new attempt receives a private copy, never writable access to the
previous generation. Review and integration workers receive no producer context.

Use a new, closed **CLI context profile and context-use owner**, backed by the
existing ControlStore operation journal. Keep the current AgentSession protocol
unchanged. Its frozen profile admits only ACP and Codex App Server; the actual
Claude `--print` adapter is neither. Do not certify an ACP-shaped fixture profile
and attach it to a Claude process. This explicitly replaces the original
ADOPTION-AND-PROOF-161434.md proposal to open AgentSession rows for this CLI.
Fresh attempt/exchange identity and actual provider conversation identity remain
required. Generalizing AgentSession to another wire protocol is not needed for
this selected restoration contract.

Also replace the original proposed schema-19 migration with a journal-backed
owner. ControlStore schema18 explicitly has **no migration** and refuses other
versions. Its existing `transact` already provides atomic admission, exact replay
and durable refusal. New tables and a migration program would enlarge this Work
without establishing provider continuity. No schema number is reserved here.

Select three ordered implementation slices under W161234: context custody and
admission; normal serving delivery/receipt/ending; then useful correction and
counted reopen through accepted managed integration. Each slice has a concrete
finish below. A component-only result does not satisfy W161234.

One provider-specific fact remains unproved: the minimal credential-free state
layout and bounded identity result needed by **the existing one-shot CLI mode**.
Section 5 chooses a concrete candidate layout and a finite qualification question.
This does not reopen whether restoration is valuable or optional. The design can
be selected now; production profile certification must not assert that fact from
the different stream-mode experiment or from a deterministic fake.

## 2. Revalidated evidence and actual gaps

`BASELINE-174293.json` records 26 source/evidence hashes and matching current
bytes for all31 paths in accepted W170385 candidate174130. Its manifest SHA256 is
`c25fce9601aec574738dd554da54eab52ecf7bbf1e97f4ea14272d7a459e8bf8`.
The independent review at
`work/records/2026/09/finding-v12-managed-integration-execution/findings/finding-managed-apply-settlement/review-2026-09-15T02-43-53Z.md`
accepts the full proposal with300 passing selected checks. This design ran none.
W170385 is closed satisfying; final W170387/W161230 acceptance remains separate.
Canonical W161234 still has its W161230 gate. No edge is added or removed here.

| Read source or evidence | What it establishes | What is still needed here |
| --- | --- | --- |
| `work/records/2026/09/finding-v12-live-session-workspace-detach/review-2026-09-07T20-20-41Z.md` | Independently accepted CLI2.1.247, actual model `claude-fable-5`, same real conversation/workspace after confirmed old-container shutdown; useful multiply-by2 to multiply-by3 correction in a replacement process | Production one-shot adapter adoption, protected generation custody and counted manager reopen. No new experiment merely to reprove restoration, cache savings or a timing ratio |
| That record's `evidence/live_supervisor_result_diagnostics.py:argv`, `start`, `result_projection` | Exact experiment used stream-json, `--session-id`/`--resume`, `/session/work`, retained `/session/home`, a fresh external credential link, observed model and session | It did not prove project-subtree-only restoration at normal serving cwd `/output`, fresh ephemera, or identity extraction from the existing one-shot JSON mode |
| W105982 canonical closure130086; `work/records/2026/09/finding-v12-private-line-custody-locators/PLAN.md` dated assembly update | Production confirmed shutdown remains; production detach is not adopted. Accepted W103083/W119114 evidence supplies retained result survival after ordinary cleanup | Context custody must obey the same exclusion boundary; a stopped CLI leader or terminal frame cannot release it |
| `v12/python/src/baton_v12/job_manager/review_driver.py:end_implementation` | Stop/reconcile, prove line consumable, freeze/correlate/intake/retain, publish while assigned, freeze checkpoint/fence, cleanup; `_cleaning_implementation` and `_resumed_implementation` handle recorded cuts | Compose context finalization after this owner returns and before the stage discharges/routes/settles its ending obligation |
| `v12/python/tools/stage_execution.py` implementation role `end` | Real registered ending obligation wraps the driver and survives unfinished final routing | Keep that obligation owed while context finalization is incomplete; no new generic ending algorithm |
| `v12/worker/claude_agent.py:work`, `_child_environments`, `_provider` | Git-line candidate really is `OUTPUT_ROOT`; provider HOME and ephemera are fresh; status0 presently discards the structured record; no open/resume arguments | Specific context delivery, success identity parsing, one-use invocation witness and retained receipt |
| `v12/python/tools/single_worker.py:_session_of`, `_adopted`, `_launch_document` | Fresh attempt-derived exchange identity and exact manager-derived launch adoption; no replacement launch after start | Add context-use binding to the same comparisons, never infer it from delivery bytes |
| `worker_manager/sessions.py:open_agent_session`, `adopt_provider_session`, `handle_transport_loss` and frozen `agent-session-1.0.schema.json` | Actual fixed assignment, fresh posture epochs, once-only ID adoption, terminal unknown, no resume/reprompt after lost transport; certified profile is a separate requirement | Reuse these invariants, not a falsely labelled CLI AgentSession. No edits to this protocol are proposed |
| `worker_manager/oci.py:run_vector`, `_roots`, specialized delivery owners | Generic execution roots remain inputs/workspace. Credentials, launch/exchange and source deliveries have explicit capabilities | Add one typed context delivery for selected implementation only; preserve the generic root allowlist |

Existing test bodies were inspected, not merely their filenames:

* `tests/tools/test_scheduler_trace.py:TheComposedOwnersSupplyAuthorizedTransitions.test_a_correction_opens_a_second_episode_on_the_same_line`
  obtains actual `ending.settlement_of`, `review_cycles.verdict_of` and the routed
  attempt. It stops at revised preparation. Preserve that evidence and finish a
  new useful-code scenario beyond it.
* `test_a_same_line_correction_keeps_its_worker_and_not_its_session` explicitly
  creates a session in the driver and proves the corrected attempt has none.
  Its universal-impossibility prose is too broad; its legacy-path assertions
  remain true. New coverage must not use driver-authored session IDs as reuse.
* `test_the_composed_deployment_reopens_and_continues` really recomposes durable
  stores while a second modeled runtime remains live. `launches_naming` counts
  nonzero engine starts by attempt operands. It finishes review, carries no
  provider-call counter and does not finish the selected managed import.
* `tests/tools/test_stage_execution.py:provider` actually writes candidate code
  at the provider subprocess seam and runs real Git/verifier commands. `turn`
  invokes real `baton_worker.serve_exchange` and `ClaudeAgent`. Extend this
  boundary in a new context-aware helper; the existing fake does not emit the
  required structured provider identity and must not be cited as doing so.
* `tests/manager/test_claude_agent.py` checks distinct verifier HOME, pinned
  verifier directory descriptors, credential-link placement, unreadable/absent
  credential refusal and no bearer reads. These are useful existing guarantees,
  not a complete confidentiality boundary between same-UID child processes.
* W103525's `CONSOLIDATION-2026-09-13T14-10-03Z.md` records accepted four terminal
  imports in each order and18 valid traces. Those terminal traces contain zero
  corrections and no reopen. Preserve old jsonschema mismatch qualifications.

Absent proposed files in Claude PREWORK do not prove all related behavior is
missing. Its statements that W170382 was still iterating and that private state
must never be retained are superseded by current canonical state and M174292:
**private context is retained securely; credentials are excluded; private content
is excluded from ordinary artifacts and public traces.**

## 3. Identity, journal and admission

Proposed module: `v12/python/src/baton_v12/worker_manager/provider_context.py`.
All names in this section are new APIs, not claims that they already exist.

| Object | Immutable identity and owner facts |
| --- | --- |
| Context | `context_id`, Authority UUID, Job, Work, line ID, actual producer participant and canonical principal, execution purpose `implementation`, registered private-repository object pin, CLI context profile digest. Derive lookup identity from Authority/Job/Work/line/actual actor; profile change refuses against that context rather than manufacturing another identity |
| Generation | Context ID, monotonically increasing generation, predecessor generation, producing use, sealed private manifest digest, bounded byte/file totals, receipt digest, source checkpoint ID/revision and positive runtime exclusion reference. The private manifest and paths stay in protected storage |
| Use | Fresh `use_id` deterministically bound to actual attempt, context and expected generation; use sequence, exact assignment/generation, writer ID/generation, line pin, task/input/policy digests, original Job execution-limits digest, runtime profile/image/adapter digests, expected conversation UUID and `open` or `restore` |
| Invocation | One fresh invocation ID for that use, exact argv-policy digest, prompt digest, provider process-start intent/witness and bounded terminal receipt. Never infer invocation count from session rows or the existence of this intent |

Use the existing ControlStore `operations` table and `transact`; no direct store
access by external callers. Owner readers validate kind, committed/refused state,
signature, closed result shape and predecessor digest. Journal one small,
nonsecret state transition per context revision. Deterministic operation IDs
include context ID and expected revision. A transaction rereads the predecessor,
checks the currently occupied use and appends the next revision under
`BEGIN IMMEDIATE`. Two connections cannot admit two uses from one predecessor;
different operands at the same revision refuse. Exact replay returns the old
result and never reopens an ended use. Public context/use readers derive state
from this chain; neither filesystem presence nor a cached Python object decides.
Keep documents flat enough for the existing canonical depth bound.

Suggested API contracts:

* `certify_context_profile(control, profile)` stores a closed, digest-bound CLI
  profile under its own journal kind. Evidence mode `deterministic` cannot stand
  in for a qualified production provider profile.
* `admit_context_use(control, jobs, authority, *, attempt_id, writer_id,
  profile_digest)` resolves `assignment_of`, the participant-bound live
  assignment, `writer_for_attempt`, `line_of`, Job/stage/episode and actual
  principal. Caller-supplied role, identity or “healthy” flags grant nothing.
* `context_of(control, context_id)` and `context_use_of(control, attempt_id)` are
  pure metadata readers. No process launch, directory repair or provider read.
* `finalize_context_use(control, *, attempt_id, delivery, receipt_body)` weighs
  receipt bytes against accepted frozen custody and inspects runtime/checkpoint
  owners before preparing and committing the next private generation.
* `hold_context_use(control, *, attempt_id, reason, evidence_refs)` records a
  closed reason with owner references; it cannot turn an unknown invocation into
  a completed one. `retire_context` requires no active/unknown writer and records
  retention disposition. Purging private generations is outside this first slice.

First admission requires a live implementation assignment and valid private-line
writer, selected profile and empty context history. Generate and persist an
expected UUID before exposing any delivery. For a correction, additionally prove
the previous context use finalized, old runtime destroyed/positively excluded,
old checkpoint retained, and the actual changes-requested verdict/settlement
routed this new attempt on this same line. Bind the newly granted writer
generation and its current repository pin; the pin is not a mutable path alias.
Use `ending.settlement_of`, `review_cycles.verdict_of`, `checkpoint_of` and writer
readers. Do not accept a context simply because a requested line ID matches.

Reject cross-Job/Work/Authority/line/principal/purpose/profile/model use, a replaced
repository object, missing retained generation, competing use, or unknown prior
turn. A newly chosen profile cannot silently start fresh for a line configured
to require reuse. Explicit context retirement/new-context selection is an owner
decision; it is not automatic failure recovery.

## 4. Protected custody and credentials

Configure one manager-controlled `context_storage` outside source/private-line,
checkpoint, declared output, verification, launch and credential storage. Prove
ancestry and descriptor object identities, not just string prefix inequality.
No arbitrary host path arrives from a provider or receipt. Layout:

```text
context_storage/<opaque-context-id>/
  generations/<n>/state/          # immutable, never mounted writable
  generations/<n>/manifest        # protected paths/digests; not a public artifact
  uses/<use-id>/home/             # only this admitted runtime may write
  uses/<use-id>/invocation        # bounded per-use execution witness
  staging/<operation-id>/         # manager-owned publication in progress
```

Manager parent directories are0700. Use directories follow the established
dedicated runtime-identity/group access arrangement, explicitly bound to the
profile; never broad world-readable modes. Validate each root and file using
no-follow descriptors, regular-file/directory checks, byte/file ceilings and
single-link policy for retained files. Reject symlinks, devices, sockets, traversal,
overlap and substituted objects. A credential slot is the one special volatile
link described below, and is never followed during retention. Do not chmod or
replace existing foreign/inaccessible roots to make admission succeed.

Materialize a new working copy from the immutable prior generation before
runtime start; preserve source generation unchanged. Provider scratch, caches,
TMPDIR and Python bytecode remain fresh per use. Verifier HOME/ephemera retain
their current independently pinned descriptors and never point into context.
Context storage is not a nominated source, candidate checkpoint, proposal output
or ordinary retained artifact. The worker gets its own use directory only; it
gets no sibling generation, other actor context or manager storage parent.

Keep credentials under the existing fresh `CredentialDelivery` and teardown
owner. The provider's per-use HOME has a `.claude/.credentials.json` link to the
fixed read-only `/run/baton/credentials/claude` slot. The context collector must
neither read that target nor copy that entry. Refuse a substituted link or regular
credential file. Do not snapshot the whole HOME or use a denylist-only copy of
unknown provider configuration. Section 5's closed state layout supplies positive
inclusion; unknown files are not silently made restorable state. No credential
value, transcript, provider prose, home path or context file list enters public
logs/results. Public metadata can name opaque context/use IDs, generations,
profile/receipt digests and closed failure codes.

This is an explicit delivery/retention boundary, not a claim that arbitrary code
sharing the provider UID cannot inspect another readable mount. Current source
already acknowledges verifier code runs in a credential-bearing runtime. Do not
claim kernel isolation or general secret detection from HOME separation. The
selected layout must never intentionally include credential/configuration stores;
an unexpectedly produced credential-shaped entry refuses promotion. A broader
hostile-provider sandbox redesign is not smuggled into this Work.

## 5. Actual CLI profile and the remaining qualification fact

Recommend profile family `baton.claude-context-profile/1`, separate from the
frozen AgentSession profile. Bind exact worker package/image digest, CLI build
and version, adapter digest, provider `claude-cli`, configured model argument,
accepted actual-model identity, Git-line source/checkpoint profile, fixed cwd
`/output`, HOME `/run/baton/context/home`, closed environment/argv policy, state
layout, receipt schema, file/byte limits and context retention policy. No model
alias silently substitutes for the configured actual-model identity.

Use CLI2.1.247 and the W106673 model pair (`claude-fable-5[1m]` requested,
`claude-fable-5` observed) as the **existing evidence reference**, not an assertion
that the current worker image has already certified this one-shot profile. A
deployment selects actual pinned image/model values; changed values require
matching qualification evidence, not a string claiming compatibility.

Proposed initial state layout `claude-project-session/1`: retain only the exact
project conversation subtree for the fixed cwd and expected session, beneath
the CLI's `.claude/projects` directory. The profile enumerates the project key,
session file naming rule and any required nested conversation state. Reject
foreign-session entries and all links/hardlinks. Recreate settings from fixed
nonsecret configuration; exclude `.credentials.json`, home config/auth stores,
debug logs, general history, caches and temporary files. Do not guess a path
encoding from `/output` or synthesize session JSONL. Manager custody treats
permitted conversation files as opaque private bytes.

**Open provider fact, with inspected evidence:** the accepted experiment retained
a whole session home and cache, used `/session/work` plus stream-json, and did not
export its private file layout. Normal `_provider` uses one-shot `--output-format
json` at `/output` and discards status0 stdout. Neither that source nor the public
restoration review proves that the proposed project subtree is sufficient, or
which bounded one-shot field attests the actual model. No protected transcript
or credential source was opened in this design.

Resolve precisely this question before certifying the production profile:
“For the pinned CLI/image, can one-shot open then restore at `/output` preserve
the same actual conversation using only the selected credential-free project
state, a fresh credential slot and fresh HOME configuration/cache; which exact
bounded result fields prove session, terminal success and actual model?” First
inspect the already pinned public provider implementation/interface and retained
nonsecret evidence. If that cannot answer it, propose one specifically selected
two-turn provider qualification with confirmed old-runtime shutdown. A fake can
test contract enforcement but cannot establish a third-party CLI persistence
format. This task authorizes no such execution. Do not repeat detach/performance
experiments or use whole-home copying as an unrecorded fallback. If additional
state is required, name the exact credential-free entries in this profile and
its reviewed qualification before enabling it.

For the selected one-shot path, compose `--session-id <expected-uuid>` on open
or `--resume <expected-uuid>` on restore, an explicit pinned model and the
existing bounded provider invocation. Closed settings/MCP/tool policies belong
to the certified profile; do not silently import the stream experiment's argv
or its sandbox assertions. Parse only a complete bounded JSON terminal record:
expected UUID, exact success discriminator, explicit non-error and qualified
actual model fields. Duplicate JSON keys, truncation, missing identity, wrong
model/session or status0 with an error record cannot yield a healthy context.
Keep existing stderr suppression and bounded draining. Output token counts/cache
fields may remain unreported; no cached-token savings percentage is acceptance.

## 6. Delivery, receipt and normal serving sequence

New `worker_manager/context_delivery.py` owns `ContextDelivery`,
`materialize_context_use`, `adopt_context_use`, `seal_generation` and a narrowly
scoped per-use discard after exclusion. It resolves the admitted use from the
manager, validates its exact object pins, and returns typed mount pairs. Add a
single specialized context mount at `/run/baton/context`; do not widen
`oci.ROOT_NAMES`. Consent, reviewer, judgment, preparation and apply purposes
reject this delivery. A context-required implementation cannot downgrade by
omitting the delivery. Materialization/replay never repairs missing live storage.

Propose closed `baton.worker-launch/4`: all `/3` members plus `provider_context`.
That member contains schema, context/use/invocation IDs, use sequence, expected
generation and private manifest digest, mode, expected conversation UUID,
context profile digest and task digest. Runtime attempt and Job provenance stay
in their existing fields and are cross-compared. It carries no host locator,
transcript or credential. Preserve exact `/1`, `/2`, `/3` shapes. Compare expected
`/4` bytes from context owner + current Job/assignment owners on both initial
materialization and reopen. A context-enabled use requires `/4`; old deployments
remain explicitly context-free. Coordinate the actual next version at execution,
without reserving it or asking another schema-number approval.

Add a declared `provider-context-receipt` directory output containing one
`receipt.json`, separate from proposal/review claims. Context-enabled input
composition declares it mandatory; a legacy profile does not invent it. Suggested
closed receipt family `baton.provider-context-receipt/1` contains context/use/
invocation IDs, attempt and delivery digest, task/prompt digests, open/restore,
expected and observed UUID, profile/CLI/model identity, measured process status,
terminal classification and complete-record flag. No state files or provider
prose. A provider-supplied UUID alone is not a manager receipt.

The manager weighs this receipt's exact bytes against the ordinary frozen file
digest/length, indexed artifact and accepted intake, and cross-checks assignment,
input, task, runtime, context use and expected conversation. Reuse the custody
pattern accepted in W170385's `managed_apply_failure_evidence`, without importing
integration ownership into the context module. The artifact is evidence; only
the context owner can commit a restorable generation.

Normal order:

1. Stage preparation resolves the actual live claim and writer; admit one
   context use and materialize its fresh working copy before ordinary start.
2. Compose/adopt launch and context delivery from owner facts. Existing
   `request_runtime_start` journals before the adapter; start uncertainty remains
   ordinary recovery-required, not permission for another use.
3. Worker validates launch/profile/use, writes an exclusive per-use invocation
   intent before `_ran_provider`, then performs one provider call. A repeated
   exchange command adopts its existing result or reports unknown; it never
   calls the provider merely because a completion file is missing.
4. Write the bounded receipt and normal result. The worker cannot mark context
   ready. A provider-successful turn may still have a failed verification; retain
   those separate facts. Initial supported healthy reuse follows ordinary
   completed implementation and an actual correction verdict.
5. Execute the existing `review_driver.end_implementation` ordering unchanged.
   Its completed cleanup/retained result/checkpoint evidence proves the old
   runtime is excluded. A terminal frame or provider exit is insufficient.
6. Before stage gate discharge/routing/final obligation settlement, finalize the
   context use: adopt receipt, prove exclusion and checkpoint, validate the
   permitted private state, stage/hash a new immutable generation, then commit
   the context transition. Only now can a future correction consume it.
7. Continue the existing ending's discharge, route and settlement. A crash in
   step6 leaves that same ending obligation owed; reentry finishes context
   publication from exact retained facts, without provider or engine restart.

On reentry, resolve an existing use/ending by its original operation identity
before attempting fresh admission. A historical fenced assignment can prove an
old ending, but cannot authorize a new invocation. Conversely, immediately before
an unstarted runtime is launched, repeat the current claim, writer, profile and
context-use checks. A saved delivery is not continuing execution authority.

The per-use working root survives ordinary attempt cleanup because it belongs
to the separate context owner. That is deliberate custody, not leaked generic
workspace. A published generation is fsynced before its journal commit; a crash
between filesystem publication and commit revalidates the deterministic staging/
generation path and measured bytes before committing. It never overwrites an
existing mismatching generation. A committed missing/damaged generation is held.

## 7. State and recovery rules

| Durable situation | Required behavior |
| --- | --- |
| Use admitted; no runtime start requested | Exact adoption may finish delivery. Changed operands refuse. Cancellation may release unused admission only after proving no start/invocation and retiring its delivery |
| Start requested; result ambiguous | Preserve ordinary recovery-required plus occupied context use. No second runtime/provider, no same-context correction |
| Invocation intent exists; terminal record absent/partial | Unknown use; no automatic resume/reprompt. This deliberately does not promise crash-before-record exactly-once execution |
| Valid terminal receipt; old runtime still alive or exclusion unknown | Collected evidence only. Hold use; do not read/promote mutable state or admit restore |
| Runtime excluded; receipt absent, identity mismatched, or state invalid | Hold with exact use/attempt and closed reason. Do not fall back to a fresh conversation or label it a successful reuse |
| Receipt and exclusion valid; generation staging incomplete | Ending remains owed. Resume only its custody operation, from the same pins and bytes |
| Generation committed; final stage routing incomplete | Adopt historical generation and replay the existing stage ending. No repeated provider call or duplicate generation |
| New correction with a matching committed predecessor | Fresh attempt/exchange/use, same actual provider UUID; actual owner verdict and new writer grant required |
| Profile/actor/line changes or explicit retirement | Refuse implicit inheritance. Preserve prior evidence; any new-context policy is explicit selection, never relabelled restoration |

Pure observation reports `unavailable`, `admitted`, `running`, `ending`, `ready`,
`held` or `retired`, plus exact use/attempt and closed reason/evidence references.
These are context states, not a new scheduler phase or a claimed session state.
Existing unknown AgentSession states and `handle_transport_loss` rules are
untouched. Context unknown also stays a hold even if someone later stops the
runtime: exclusion proves no writer remains, not which unobserved turn ran.
Manual disposition can retire evidence; automatic reconstruction/reprompt is
outside the selected scope.

## 8. Exact recommended path ownership and implementation order

No path below is assigned by this design alone. After owner selection and the
original W161230 gate, assign one serial implementation claimant, with independent
review. Revalidate W170387's final interfaces and all shared paths then. Current
W63255 owns `worker_manager/intake.py`, `tools/dogfood_operator.py` and their named
tests; this design proposes no edits to those paths.

Paths in the next table are under `v12/python/` unless explicitly prefixed.

| Slice | Proposed editable paths | Bounded finish |
| --- | --- | --- |
| A: context metadata, custody and profile | NEW `src/baton_v12/worker_manager/provider_context.py`; NEW `src/baton_v12/worker_manager/context_delivery.py`; NEW `tests/manager/test_provider_context.py`; NEW `tests/manager/test_provider_context_delivery.py` | Journal-derived metadata, atomic competing-use refusal, fixed identity/profile/layout, snapshot publication/adoption and credential exclusion with no provider invocation. Production profile qualification status is explicit |
| B: normal serving | `src/baton_v12/worker_manager/launch.py`, `src/baton_v12/worker_manager/oci.py`, `tools/single_worker.py`, `tools/stage_execution.py`, `v12/worker/baton_worker.py`, `v12/worker/claude_agent.py`; NEW `tests/manager/test_claude_context.py`; selected existing `tests/manager/test_launch.py`, `tests/manager/test_oci.py`, `tests/manager/test_claude_agent.py`, `tests/tools/test_single_worker.py`, `tests/tools/test_stage_execution.py` for necessary fixture/closed-configuration additions | Required `/4` delivery reaches the real implementation provider seam; actual identity receipt collected; context finalized after driver cleanup and before stage settlement; failed/unknown uses hold; legacy paths stay supported |
| C: complete proofs | NEW `tests/tools/correction_restart_trace.py`; NEW `tests/tools/test_correction_restart.py`; W161234 dossier evidence; owner-routed `DEPLOYMENT.md` change after independent review | Useful revised code and independent review/import; declared reopen with actual provider/engine counters and rejecting duplicate negatives; final candidate/environment/provenance bundle |

Reuse-only owners: `schema.py`, `store.py`, `documents.py`, `sessions.py`,
`handshake.py`, frozen contracts, `review_cycles.py`, `job_manager/review_driver.py`,
generic attempts/intake/retention/credentials, scheduler/Authority and accepted
integration code. New context documents have their own closed composers; use
existing identity/secret/canonical validators. No new generic port method,
migration, AgentSession wire variant, live detach, engine operation design or
image build is implied. If the composition demonstrably needs another source
boundary, report that exact required change for scope disposition; do not hide
it in a test helper.

This is a deliberate amendment to the old three-slice path proposal: remove
schema/store/documents edits and production AgentSession adoption; move custody
delivery ownership into A; explicitly include necessary existing launch/OCI/
workload/serving tests in B. Standing test authority already permits those scoped
changes. Preserve positive refusal/unknown coverage and record expectation
changes in the implementing handoff; no new per-method permission gate.

Implementation order inside B: establish the qualified provider profile contract;
then closed launch/delivery checks and negative admission; then worker one-use
execution/receipt; then manager frozen receipt/custody ending; finally enable the
selected context-required implementation configuration. Do not advertise reuse
after only adding tables, metadata rows, argv flags or fake session names.

## 9. Focused deterministic acceptance

These commands are **proposed, not run**. From `v12/python`, use the pinned
repository `.venv/bin/python3` with `PYTHONPATH=src:tools:.` through an owning
per-run supervisor. Suggested ceilings are60s for A,180s for B and each C
scenario, with TERM5s/KILL5s grace and positive group cleanup. Tune a run ceiling
to the selected fixture; cumulative historical seconds are not an admission gate.
Record actual interpreter/dependency versions and source/config/profile hashes.

```text
-m unittest tests.manager.test_provider_context tests.manager.test_provider_context_delivery
-m unittest tests.manager.test_claude_context tests.manager.test_launch tests.manager.test_oci
-m unittest tests.tools.test_correction_restart.UsefulCorrection
-m unittest tests.tools.test_correction_restart.CountedReopen tests.tools.test_correction_restart.InvalidEvidence
```

Run the affected existing workload/serving negatives with exact selectors chosen
from the inspected tests when B's final delta is known; do not turn this into a
broad discovery run. Reuse W170385's accepted300-test evidence and select only
new integration regressions justified by an actual shared-path change.

A must prove same-transaction competing admission, exact replay, wrong actor/
principal/Job/line/profile refusal, predecessor and object-pin drift refusal,
missing/damaged generation hold, private state surviving ordinary cleanup,
credential exclusion with a synthetic forbidden-to-read slot, replacement links/
hardlinks refusal, pure observation and interrupted generation publication.
Use existing ControlStore instances and real temporary directories, not fabricated
“context ready” rows. No provider or engine is needed for these owner checks.

B must drive `ClaudeAgent` through its existing process seam and real exchange.
The deterministic provider receives open/resume operands, writes a private
conversation-state fixture and changed code, and emits a bounded identity result.
It must restore from delivered state rather than a Python dict surviving reopen.
Test wrong UUID/model, status0 error/missing/partial result, changed receipt,
context omission/downgrade, wrong role/mount, one-use replay, cleanup refusal,
unknown transport and no automatic reprompt. Assert context bytes are absent from
proposal/checkpoint/public receipt/trace and provider/verifier ephemera differ.

C has two scenarios, each under100 logical ticks:

1. **UsefulCorrection:** an initial deterministic provider writes a meaningful
   function with the wrong requirement (for example multiply-by2). Genuine
   verifier execution and a real independent changes-requested review produce
   the next same-line episode. A fresh admitted use restores the previous UUID
   from its retained state and writes multiply-by3. Execute a separately pinned
   verifier over revised bytes, finish independent review and the accepted
   managed preparation/judgment/apply/target-receipt/final-outcome path. Record
   old/revised code digests, actual verdict/routing/checkpoints, fresh attempts/
   exchanges/uses, one provider UUID, actual target bytes and integration receipt.
   Reviewer mounts and identities must exclude producer context and writable line.
2. **CountedReopen:** after a real deterministic provider call and durable result,
   close manager handles and recompose over the same stores and protected state.
   Keep engine observations/counters outside those handles. Continue correction,
   review and managed import. Count actual calls at `_ran_provider`/the provider
   process seam by use/invocation/attempt and exact open/resume operands; count
   actual engine starts independently by their input attempt/operation identity.
   Both pre-reopen baselines must be positive. Reopen must not increment the old
   use or start its runtime again; a legitimate new correction increments its
   distinct use once. Report durable manager recomposition, not host/power loss.

An independent companion validator binds owner facts to both counter streams and
the unchanged scheduler trace digest. Separately inject a duplicate provider call
and duplicate engine start and require the same validator to reject each. Also
reject missing positive baselines, an absent actual reopen, changed verdict/
checkpoint/attempt attribution and forged context receipt. These are labelled
synthetic invalid evidence, never owner receipts. No count is inferred from
AgentSession lists, allocated tokens or unique operation IDs. This supplies the
missing non-vacuous proof without rerunning all18 predecessor schedules.

## 10. Release consumer reconciliation and selection request

M167954 and `work/records/2026/08/finding-v12-isolated-agent-workers/RELEASE-CHECKLIST-167877.md`
assign bounded current-consumer questions, not nine new prerequisite Works.

| Existing owner/question | Concrete reconciliation in the selected proof |
| --- | --- |
| W7 | Record the actual context/correction/reopen case list and managed receipt chain; preserve unproved legacy thresholds |
| W44342 | Count ordinary engine starts at actual input identities and reuse accepted W170382 start-intent/restart evidence. A remaining duplicate is a concrete finding, not an assumed need for a new engine operation |
| W61981 | Bind actual verifier argv, task/input and independently pinned verifier HOME/ephemera to original Job limit provenance. Reuse W156162 and W170385 accepted command-bound evidence |
| W62098 | Compare original import base, private line and review checkpoint to retained preparation objects and actual managed target receipt; do not trust a final ref alone |
| W62535 | Use selected entry-preflight fixtures to show a rejected context profile/delivery creates no provider invocation or stranded usable context; report any surviving older pre-staging defect to its owner |
| W110783 with W124784/W122060 | Read the checkpoint-fenced cleanup and completed-cleanup reentry owners already present in `end_implementation`; compose context finalization around them. Attribute any supersession to accepted evidence, not a new restart clone |
| W114077/W114516 | Compare affected ordinary retry/ending behavior only if the chosen context cut reaches it. No broad intermittent engine reproduction; unknowns remain unproved |
| W144335 | Check frozen receipt/intake replay preserves the original held reason in the selected context/managed path. Existing owner keeps any residual; no repair through a viewer |
| W144813 | Check first launch/context-delivery refusal remains attributable on reentry and no runtime is started to replace missing evidence; retain existing owner for any residual |

These are recommended checks and current source/evidence mappings, not completed
consumer acceptance. No listed Work is closed or reclassified by this design.
W63255's supported-abandon fence is already selected independently; neither its
old conditional checklist text nor current parallel implementation enlarges this
assignment.

Request concrete owner selection of this journal-backed, dedicated-CLI-profile,
protected-generation design and its A/B/C path set, with the provider-layout/
one-shot identity qualification explicitly named. Independent design review and
the original W161230 gate still precede implementation. The original record's
owner should append this selection and update its current plan, preserving old
decisions and their exact supersession. In particular replace old cumulative
120/30,300/75,420/105 approval/refusal wording and per-test permission gates with
current standing policy; preserve measured historical costs and sensible run
timeouts. Do not silently edit those original records from this separate Work.

No tests, probes, provider/model/engine runs, builds, Git mutations or additional
workers were used in this design. New measured verification is0s. Source reads
and hash comparisons are design evidence, not executed acceptance. Guessed
`worker_manager/agent_profiles.py`, `worker_manager/turns.py`, a
`v12/contracts/schemas` glob and `tests/tools/test_handshake.py` did not exist;
the actual handshake/frozen schema and `tests/manager/test_handshake.py` were
located and read. No mandatory bound input remains unreadable. All writes stay
inside this separate design dossier.
