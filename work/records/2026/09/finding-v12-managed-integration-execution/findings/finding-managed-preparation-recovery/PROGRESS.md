# Progress — W170382 (group2)

Implementing claimant: baton.claude via baton.impl. Independent reviewer:
baton.codex via baton.feat. This file is author-owned; FINDING.md and PLAN.md
belong to the reviewer.

## Claim 170659 — revalidation and declared ownership

**The pinned prerequisite is revalidated against the current tree, not assumed.**
W170380 (group1) closed `satisfying`; its accepted candidate is
`findings/finding-managed-preparation-completion/candidate-170569.json`,
manifest SHA-256
`e3ba732f17fa0efb83f78dd92bb1f3692e14479bc6935389de878e85c2817fa3`, accepted in
`review-2026-09-14T16-19-56Z.md`. **All eight files in that manifest hash equal
in the working tree right now** — zero drift. So group1's path is the one I am
extending, and nothing here reimplements it.

**Declared ownership for this claim**, within the inherited nine-source/eight-test
slice2 boundary and serial with groups 1/3 on the coordinator/capacity/test paths:

- `v12/python/tools/integration_worker.py`
- `v12/python/tools/stage_execution.py`
- `v12/python/tests/tools/test_managed_preparation.py`

Generic worker/manager/scheduler/Authority, OCI/input/output/exchange/JobStore
schema and source owners remain reuse-only. Main `DEPLOYMENT` is protected.

**What group1 already proves, so that I do not re-prove it** (read from its
accepted case `OneManagedPreparationCompletes.complete`, not from its summary):

| Group1 case | Cut |
| --- | --- |
| `test_ordinary_sweeps_retain_and_adopt_one_real_preparation` | none |
| `test_publication_before_intent_recovers_the_same_request` | `decide` |
| `test_accepted_offer_recovers_without_a_second_bearer` | `submit_claim` |
| `test_committed_claim_recovers_before_attempt_recording` | `record_attempt` |
| `test_admitted_capacity_recovers_before_runtime_start` | `start` |
| `test_unexpected_pre_intent_fault_recovers_the_held_allocation` | `unexpected-decide` |
| `test_pre_intent_recovery_refuses_an_existing_child_work` | `unexpected-decide` + obstruct |

Group1's restart is **`runtime.close()` — the local worker cache only**; the
durable stores and the composition are never reopened. That is exactly the gap
this child's finish names.

**Baseline:** step 01, the parent's five focused modules, `OK`, **425 checks**,
**25.949488 s** supervised (180 s per-run limit, 5 s TERM + 5 s KILL, own
process group; group proved gone, no signal). Ledger `ledger-170382.json`.
This claim's runner is `/tmp/w170382_run.py`, inherited from the parent's
supervisor and the reviewer's.

## Claim 170659 — the selected cut positions, and what I did NOT finish

**Delivered.** `tests/tools/test_managed_preparation.py` is the only file
changed this claim; the seven other files of group1's accepted candidate are
byte-identical. No product source changed — the ordinary path already carried
these positions and needed no correction to be interrupted at them.

**The cut placement became a table, and every entry names a real owner on the
ordinary path.** Group1 resolved placement inline and knew three placements,
which was exactly enough for its five cuts. The remaining selected cuts fall on
owners that expression cannot name — the capacity registrar, the ordinary
`ManagerOperations`, the ending and the adoption. Nothing here introduces a
hook, a checkpoint or a test-only seam: each is the public operation the
preparation actually calls, patched where its caller resolves it.

Eight new cases, one per remaining selected cut:

| Case | Cut | Position |
| --- | --- | --- |
| `test_committed_intent_resumes_its_own_child_work_creation` | `create` | intent before Work creation |
| `test_created_child_work_resumes_before_capacity_registration` | `register` | creation before registration |
| `test_committed_claim_resumes_before_capacity_admission` | `admit` | claim before admission |
| `test_start_intent_resumes_when_the_adapter_never_answers` | `launch` | start intent before adapter return |
| `test_the_worker_answer_resumes_before_output_is_frozen` | `dispatch` | worker answer before freeze |
| `test_frozen_output_resumes_through_intake_and_attachment` | `conclude` | freeze before intake, intake before attachment |
| `test_cleanup_resumes_before_the_membership_is_ended` | `end` | cleanup before membership ending |
| `test_an_ended_membership_resumes_before_its_candidate_is_adopted` | `adopt` | ending before adoption |

Each inherits group1's whole finish: one fixture process, one child admit, one
delivery, worker exit 0, host trap proved and unreached, target bytes/revision/
tree unchanged, parent queued and unclaimed, root open, apply planned, runtime
destroyed, cleanup retained, and the same adoption after the cache is dropped.

**MY FIRST THREE OPERATIONS CASES WERE PASSING OVER THE WRONG WORKER, and the
reversal is what found it.** `ManagerOperations.launch/dispatch/conclude` are
also the producer's and reviewer's. Cutting the first call of that name
interrupted whatever ran first and then asserted a recovery that had nothing to
do with a preparation. `interrupts` now checks the call against the
preparation's own child attempt.

**Reversals, run against the final file and restored:**

| Reversal | Result |
| --- | --- |
| the operations cuts never fire on the preparation child | **3 cases fail** |
| the vacuous placement (cut the first caller of that name) | **PASSES** — which is exactly why the attribution check exists |
| the `create` cut moved to `planned` (a different owner) | **PASSES** — see the weakness below |

### A weakness I found in my own cases and am NOT hiding

**The third reversal passes, so these cases do not discriminate their position.**
Moving the `create` cut onto `planned` leaves all fifteen green, because
"interrupt one step and recover" is true of *every* step on this path. Each case
therefore proves *that* the preparation recovers from an interruption at a named
owner; it does **not** prove that the named owner is the position its name
claims. The coverage is real and the positions are exercised, but the case names
currently promise more than the assertions deliver.

I started the fix — assert the durable facts true only at that position (intent
recorded and child Work absent; Work present and plan absent; claim committed
and member not admitted; admitted and no runtime; runtime present) read from
each owner at the instant of interruption. It is preserved unfinished at
`witness-attempt-170659.py`; it fails with `KeyError: 'execution_attempt_id'`
(the intent document does not carry that key where I read it) and one case
witnessing `no-intent` where `intent, child-work, no-plan` was expected. **This
is owed and is the first thing the next claim should finish.**

### The store/composition restart is NOT delivered

Group1's restart is `runtime.close()` — the local worker cache, with both
durable handles and the whole composed deployment still alive. This child's
finish requires reopening the stores and the composition. I implemented it and
it does not work; it is preserved at `restart-attempt-170659.py` with two
measured obstacles, so the next claim does not repeat the diagnosis:

1. **A restart cannot be taken inside the cut.** Closing the composition while
   the interrupted sweep is still unwinding tears the stores out from under it:
   `sqlite3.ProgrammingError: Cannot operate on a closed database` from
   `stage_execution.py:2913` in `_Serving.account`, several frames above. A
   process that died does not finish its own stack. Taking the restart after
   the sweep returns fixes this one.
2. **Releasing the retired composition kills the successor's Authority.** With
   the restart taken after the sweep, `create_work` on the *new* composition
   fails the same way from `authority/store.py:574`. The new Authority is
   provably live immediately after the rebuild, so something in the retired
   composition's release reaches it. Not closing the retired composition avoids
   that error but makes the restart weaker, and the post-runtime cuts
   (`dispatch`, `conclude`, `end`, `adopt`) then never adopt — the rebuilt
   composition keeps deferring. **I did not find the cause and am not guessing
   at one.**

### Verification

- Step 01 baseline, five focused modules: `OK`, **425 checks**, 25.949488 s.
- Step 03, with the matrix: `OK`, **433 checks**, 32.875 s.
- Step 04, final restored state: `OK`, **433 checks**, 33.161 s.
- Supervisor `/tmp/w170382_run.py`: 180 s per-run limit, own process group,
  5 s TERM + 5 s KILL escalation. No run timed out, none was signalled, every
  run proved its group gone.
- **This claim's measured spending: 4 rows, 98.462512 s** (`ledger-170382.json`).
  Group1's author cumulative 98.710505 s, the parent ledger 2442.624596 s and
  the reviewer's cumulative remain separate and preserved.

Candidate `candidate-170659.json`. Changed file
`v12/python/tests/tools/test_managed_preparation.py`,
`sha256:f8a410e8cc70f6832f6950078eabf6aad0ebbf0cea9892ddc6564540f91dd335`,
94737 bytes, mode `0o644` unchanged. No Git state was mutated. Deterministic
simulated engine/provider only — no Docker, image build, live model, install or
broad discovery.

### Remaining group2 scope, in full

Position discrimination (above); the store/composition restart (above); the
negative identity/profile/task/manifest/digest/length/source/harness matrix;
missing blob, symlink/escape, frozen-only and missing/quarantined intake; the
genuine causal combined/base/isolated matrix including combined success with
missing-fix base failure, conflict, and combined failure; timeout or start
failure at each position with the exact completed prefix and not-run suffix;
ordinary Job defaults/overrides and two distinct Jobs; refusal, cancellation
and uncertain endings preserving holds and driving ordinary termination/
exclusion/cleanup, with leader-first and TERM-resistant cases; required
direct/legacy coverage; and `DEPLOYMENT-SLICE2-DRAFT.md`.

## Claim 170804 — the review's two P1s, and what each cost

Read return170800, the full events and thread, and
`review-2026-09-14T16-44-44Z.md`. Still one changed file:
`v12/python/tests/tools/test_managed_preparation.py`; the seven other files of
group1's accepted candidate remain byte-identical and no product source changed.

### My handoff was unreadable and that was my error, not Baton's

Message 170744 transmitted the literal string `@/tmp/w170382-say.txt`. `say`
does not expand an `@file` argument; I assumed it did and never checked what was
actually posted. The reviewer preserved my intended text as `HANDOFF-170744.txt`
and correctly classified this as CLI misuse rather than a protocol defect. This
claim's handoff passes its actual text.

### P1 — the restart failure was a stale receiver in MY fixture

The reviewer found what I could not and I had it backwards. I wrote
`original_admit = preparation.admit`, a **bound** method on the preparation that
existed when the tracer was installed, and the class-level `traced` wrapper then
ignored its own `instance`. After a restart the sweep therefore kept driving the
**retired** object and its closed Authority and JobStore. My reported conclusion
— that releasing one Authority kills an independent successor — was a misreading
of my own bug; there is no evidence for it.

Corrected to `type(preparation).admit` and `original_admit(instance, *args)`,
with the reopen closing the retired runtime, composition, JobStore **and**
ControlStore after the interrupted sweep returns, then proving the old Authority
closed and the new one live and distinct. The external fixture worker process and
its engine state deliberately survive the rebuild — a restart whose runtime
vanished with it would never have to reconcile anything.

**All eight restart cases now pass.** Reversals:

| Reversal | Result |
| --- | --- |
| the stale bound receiver restored | **8 restart cases fail** |
| durable handles left open across the restart | **passes** — so closing the two stores is correct but is *not* discriminated by these cases; only the old-Authority assertion is load-bearing |

### P1 — the cut positions were wrong, and are now corrected and witnessed

The reviewer's probe measured what my cuts actually interrupted. Three were not
the positions their names claimed, and I have moved them to the owners named in
the review:

| Was | Measured reality | Now |
| --- | --- | --- |
| `ManagerOperations.launch` | runtime not started, no runtime id, no exchange | kept, **renamed** to what it proves; the committed-start boundary inside `attempts.request_runtime_start` is still owed |
| `ManagerOperations.dispatch` | before the worker is commanded | `single_worker.request_freeze` — worker answer before freeze |
| `ManagerOperations.conclude` | answered, nothing frozen | `single_worker.request_intake` — freeze before intake; plus `reconciliation.attach_managed_phase` for accepted intake before attachment |

**Position discrimination is now real.** Each cut asserts the committed prefix
and absent suffix true only there, read from public owners at the instant of
interruption — capacity plan, intent, child Work, settled offer, assignment,
admitted membership, runtime, frozen output, accepted intake, ended membership.
The reviewer's shape corrections were all necessary: the intent carries
`execution_work_id` top level and `plan`; the claim's outcome is the existing
`offer.settle:<offer>` receipt, not the `claim.submit:<attempt>` key I invented;
`project_work` and `assignment_of` **refuse** on absence rather than answering
`None`, so `work_creation` and a guarded read are used instead.

**The two reversals that previously PASSED now fail:**

| Reversal | Before | Now |
| --- | --- | --- |
| `intake` cut moved onto the freeze owner | passed | **2 cases fail** |
| `create` cut moved onto `planned` | passed | **2 cases fail** |
| `freeze`/`intake` cuts never fire on the preparation child | — | **4 cases fail** |

A witness that raises is recorded as `("witness-failed", ...)` rather than being
absorbed by the sweep as an ordinary refusal — the exact failure mode the review
flagged in its own register probe, and one I had already hit: an exception in the
witness left `cut_reached` filled and the position silently unchecked.

### The register mismatch — recorded, NOT claimed covered

`ManagedPreparation.admit` registers capacity at `integration_worker.py:1229`,
**before** `PreparationExecution.prepare` decides an intent or creates the child
Work. The original packet `SLICE2-SCOPE-165724.md` required intent and creation
**before** registration. That state is therefore unreachable in group1's accepted
composition, and the witness confirms it: at the `register` cut nothing is
committed, and at `decide`/`create` the plan already is.

I have **not** reordered production to make a fixture green and have **not**
claimed the obligation covered. The case is renamed
`test_registration_resumes_before_any_intent_or_child_work`, which is what it
proves. **This is an open selection/implementation mismatch for the owning
FINDING/PLAN to resolve** — either a bounded correction within the selected
paths or a recorded selection amendment — before final slice2 acceptance.

### Verification

- Step 05, five focused modules: `OK`, **443 checks**, supervisor **37.609134 s**
  (inner unittest 37.411 s).
- Supervisor `/tmp/w170382_run.py`: 180 s per-run limit, own process group,
  5 s TERM + 5 s KILL. No run timed out, none was signalled, every run proved
  its group gone.
- **Ledger `ledger-170382.json`: 5 rows, 136.071647 s** across both claims.
  The reviewer is right that this is the *recorded subset*: my reversal and
  experiment runs this claim and last were executed outside the supervisor and
  have no per-run timings. I am preserving that unknown rather than
  reconstructing it. Group1 author 98.710505 s, parent ledger 2442.624596 s and
  reviewer cumulative 66.723386 s remain separate.
- Prose figures in my last handoff (32.875/33.161) were inner unittest timings,
  not supervisor durations; the supervisor values were 33.072147/33.371713 s.
  Corrected here.

Candidate `candidate-170804.json`. Changed file
`v12/python/tests/tools/test_managed_preparation.py`,
`sha256:dd71a6e01a5a36f0ca211336a1d722be838ad9fa329e63793ff41b5af05086d1`,
111035 bytes, mode `0o644` unchanged. No Git mutation, no product source change,
deterministic simulated engine with the real worker process only.

### Remaining group2 scope

Committed start intent with uncertain adapter outcome at
`attempts.request_runtime_start` (assert requested state/journal and no silent
second start); the register selection mismatch above; the
identity/profile/task/manifest/digest/length/source/harness refusals; missing
blobs, symlink/escape, frozen-only and missing/quarantined intake; the causal
combined/base/isolated positive and failure matrix, including combined success
with missing-fix base failure, conflict, and combined failure; per-position
timeout and start failure with exact completed prefix and not-run suffix;
defaults/overrides and two-Job isolation; refusal, cancellation and uncertain
endings preserving holds and driving ordinary termination/exclusion/cleanup,
with leader-first and TERM-resistant cases; applicable direct/legacy evidence;
the complete finite acceptance matrix; and `DEPLOYMENT-SLICE2-DRAFT.md`.

## Claim 172112 — the four selected windows, under owner decision M172097

Read canonical state, all events since 170861, the full thread (5 messages, no
pagination outstanding), `REGISTRATION-ORDER-PROPOSAL-170867.md`, the updated
FINDING/PLAN and `review-2026-09-14T17-01-51Z.md`. Revalidated
`candidate-170804.json` against the tree before editing: the one changed file
hashes equal and the seven sibling files of group1's accepted candidate are
unchanged.

**The register mismatch I returned is resolved by owner decision, not by me.**
M172097 selects **early planned-capacity registration** and explicitly supersedes
the original "creation before registration" ordering. I did not reorder
production and did not need to: the pinned sequence is register → commit
immutable intent → create child → ordinary claim/attempt/assignment/admission →
launch.

### The four replacement windows

| Window | Cut owner | Committed prefix witnessed |
| --- | --- | --- |
| 1 — before registration | `integration_capacity.register_integration_capacity` | nothing |
| 2 — after registration, before intent | `PreparationExecution.decide` | `plan` |
| 3 — after intent, before child creation | `PreparationExecution.create` | `plan, intent` |
| 4 — after child creation, before offer | `PreparationRuntime.admit` | `plan, intent, work` |

**Window 4 is NOT `PreparationExecution.offer`, and that is measured rather than
assumed.** Review claim170764's accepted P2 moved issuing and accepting to the
configured child: `prepare` calls the injected `admit`, which is
`PreparationRuntime.admit` → `_SingleWorker.admit`. The `offer` helper is
unreached on the selected path, and a cut placed on it never fires — the case
failed with `cut_reached == []` until I moved it.

**The witness gained an `offered` fact** (`offer.issue:<offer>`), without which
window 4 and the claim window witness the same prefix and stop discriminating
each other. Reversals, all run and restored:

| Reversal | Result |
| --- | --- |
| window 4 claims the offer is already issued | **2 cases fail** |
| the `offered` fact is not read | **2 cases fail** |
| window 4 moved onto window 3's owner | **2 cases fail** |

Each window also has a store/composition restart variant, so all four are proved
across losing the coordinator handles as well as in-flight.

### A changed identity is refused before any new effect

`test_window_3_refuses_a_changed_child_work_before_any_effect` perturbs exactly
one operand — the child Work id — for exactly one sweep, and proves the refusal
names the committed decision:

    this orchestration already decided child Work '0000000a-W479843…' and these
    operands name '0000000a-999999…'; a resumed sweep runs the child its own
    intent committed, and a second one is the duplicate that intent exists to
    prevent

and that the witness before and after that sweep is identical — nothing was
created, offered or started. Reversing the perturbation to agree with the intent
fails the case.

**TWO FALSE POSITIVES OF MY OWN, both caught before they shipped.** First,
`assertRaises(ContractRefusal)` around `sweep` never fires: the delegation
absorbs the refused admit and carries on, which is the ordinary deferral this
whole path relies on. Second, counting `failures` accepted a sweep that advanced
normally, because `failures` collects *every* admit exception including the
nondurable "this admit stays owed" deferral that fires on every sweep. The case
now asserts the recorded refusal is not the deferral and names the decision.

**I dropped the changed-`request_digest` case rather than ship it.** Under that
perturbation the sweep advanced to a running runtime instead of refusing, so
either the guard does not cover that operand at window 4 or my substitution did
not disagree with it. I did not investigate far enough to say which, so the
request-identity rejection is owed, not claimed.

### Verification

- Step 07, five focused modules: `OK`, **448 checks**, supervisor **40.782820 s**
  (inner unittest 40.590 s). Baseline at claim start was 443.
- Supervisor `/tmp/w170382_run.py`: 180 s per-run limit, own process group,
  5 s TERM + 5 s KILL. No run timed out, none was signalled, every run proved
  its group gone.
- **Ledger `ledger-170382.json`: 7 rows, 217.539097 s** across all three claims.
  Still the *recorded subset* — reversal and experiment runs ran outside the
  supervisor and have no per-run timings; that unknown is preserved, not
  reconstructed. Group1 author 98.710505 s, parent ledger 2442.624596 s and the
  reviewer's cumulative remain separate.

Candidate `candidate-172112.json`. One changed file,
`v12/python/tests/tools/test_managed_preparation.py`,
`sha256:c54a5ed03889fe4eb3d2c652e68884b9ce03645b505f832bed81c15a7e4841a1`,
117693 bytes, mode `0o644` unchanged; seven siblings hash equal. No product
source change, no Git mutation, deterministic simulated engine with the real
worker process only.

### Remaining group2 scope

Changed-`request_digest` (and root/plan/profile/Job) identity rejection at the
windows; committed start intent with uncertain adapter outcome at
`attempts.request_runtime_start`; identity/profile/task/manifest/digest/length/
source/harness refusals; missing blobs, symlink/escape, frozen-only and missing/
quarantined intake; the causal combined/base/isolated positive and failure
matrix; per-position timeout and start failure with exact completed prefix and
not-run suffix; defaults/overrides and two-Job isolation; refusal, cancellation
and uncertain endings with leader-first and TERM-resistant cases; direct/legacy
evidence; the complete finite acceptance matrix; and
`DEPLOYMENT-SLICE2-DRAFT.md`.

## Claim 172200 — the real request negative, and the uncertain start

Read return172197, all events since 172170, the full thread (6 messages, no
pagination outstanding), `review-2026-09-14T21-01-03Z.md` and
`review-request-probe-172173.py`. Revalidated `candidate-172112.json` and the
seven group1 siblings against the tree before editing. Owner ordering M172097
remains pinned; no new ordering decision was needed.

**Per review172197 I now supervise experiments as well as final runs**, so every
reversal below is a ledger row with its own log, and I iterated locally under
one claim instead of returning after each pass.

### The request negative I dropped — the reviewer found where it belongs

I had changed a top-level `request_digest` field on the resolver's answer.
**Nothing reads that field.** `_recovered` derives the real digest from the
immutable **published** request and compares it against the intent, so an unused
field changes nothing, the sweep advances normally, and my case was passing on
the ordinary deferral. The disagreement now goes in at the publication reader —
`ManagedPreparation._published`, with one valid request member changed — which
is where the authoritative answer comes from.

Windows 3 and 4 both refuse there, with the message pinned:

    ... must name one request ...

and the witness before and after the refused sweep identical — nothing created,
offered or started. **No product guard was added to reject unused fixture
metadata**, per the review's explicit instruction. This is simulated reader
disagreement, not on-disk tamper or custody evidence, and the cases claim
nothing about those.

Supervised reversals (steps 08–12):

| Reversal | Result |
| --- | --- |
| the published request is not changed | **2 cases fail** (step 08) |
| the pinned refusal phrase is wrong | **2 cases fail** (step 11) |
| the child Work operand is not changed | **1 case fails** (step 10) |
| `DENIAL` emptied | passes (step 09) — an empty substring asserts nothing; step 11 is the real check |
| the "stays owed" deferral guard removed | passes (step 12) — redundant given the pinned message, kept as belt-and-braces |

### The committed start with an uncertain adapter answer

`attempts.request_runtime_start` commits its signed `runtime.start` and **only
then** calls the adapter. The case loses the adapter's answer at the fixture's
engine boundary *after* the runtime is really running — an adapter that never
ran is not uncertain, it is simply not started.

**I expected this to resume. It does not, and that is the selected finish.** The
scheduler marks the allocation `recovery-required`; the committed intent puts it
outside the accepted pre-intent recovery; every later sweep refuses:

    stage assignment 'attempt-01128b4b…' is 'recovery-required'; an intent
    accounts capacity that is actually held

That refusal **is** "unknown start remains held" from the Observable finish. The
case asserts it: a journal row existed at that instant with no `runtime_id`
reported, exactly one fixture process, no adoption, allocation still
`recovery-required` (not reset to `reserved`, not released), root open, apply
planned, parent queued, target bytes/revision/tree unchanged. Proof line:

    {"proof": "uncertain-start-remains-held", "adopted": false,
     "allocation": "recovery-required", "apply": "planned",
     "fixture_processes": 1, "parent": "queued-unclaimed", "root": "open"}

Supervised reversals (steps 13–15): the adapter answer never lost → **fails**;
the hold claimed `reserved` → **fails**; a second runtime claimed → **fails**.

### Verification

- Step 16, five focused modules: `OK`, **451 checks**, supervisor **45.622665 s**
  (inner unittest 45.417 s). Baseline at claim start was 448.
- Supervisor `/tmp/w170382_run.py`: 180 s per-run limit, own process group,
  5 s TERM + 5 s KILL. Across all 16 recorded rows: **no run timed out, none was
  signalled, every run proved its process group gone.**
- **Ledger `ledger-170382.json`: 16 rows, 437.217026 s** across four claims.
  From this claim on, experiments are in the ledger; the earlier claims'
  reversal runs remain an unrecorded unknown and are preserved as such. Group1
  author 98.710505 s, parent ledger 2442.624596 s and reviewer cumulative
  91.838663 s remain separate.

Candidate `candidate-172200.json`. One changed file,
`v12/python/tests/tools/test_managed_preparation.py`,
`sha256:5eb09c8ff9f594eab6b443646d02c786880ae303d5e3ece11fb2c4d0fefc4a4d`,
124925 bytes, mode `0o644` unchanged; seven siblings hash equal. No product
source change, no Git mutation, deterministic simulated engine with the real
worker process only.

### Remaining group2 scope

Root/plan/profile/Job identity negatives (request and child Work are done);
identity/profile/task/manifest/digest/length/source/harness refusals; missing
blobs, symlink/escape, frozen-only and missing/quarantined intake; the causal
combined/base/isolated positive and failure matrix; per-position timeout and
start failure with exact completed prefix and not-run suffix; defaults/overrides
and two-Job isolation; refusal, cancellation and uncertain endings with
leader-first and TERM-resistant cases; direct/legacy evidence; the complete
finite acceptance matrix; and `DEPLOYMENT-SLICE2-DRAFT.md`.

## Claim 172286 — the known failed start is ENDED (product change)

Read return172282, all events since 172254, the full thread (7 messages, no
pagination outstanding), `review-2026-09-14T21-15-19Z.md` and
`review-start-state-172256.py`. Revalidated `candidate-172200.json` and the
seven group1 siblings before editing.

### I classified a known live failed start as an unknown outcome

The review is right and the measurement is decisive. `request_runtime_start`
catches the engine exception, `_settled_and_recorded` identifies the **exact**
runtime and atomically attaches it beside a durable `runtime.start-failed`
record. The manager had already asked. My case asserted only the snapshot taken
at the instant of the fault plus the scheduler holds, so it passed while a known
live worker sat cleanup-pending forever — terminated only by fixture teardown,
which is not the product ending anything. "Unknown start remains held" is a real
outcome but it is not this one.

### The composition, in the generic owners' own order

**This is a product change**, in two of my declared paths. Both blockers the
review named are addressed:

- `ManagedPreparation._failed_start` runs **before** the ordinary admission and
  before any re-deciding of intent. It has to: a later sweep re-enters
  `PreparationExecution.prepare`, whose intent replay reaches capacity's parent
  facts and refuses the `recovery-required` allocation outside the narrow
  pre-intent exception, so `poll` is never reached again.
- The ending itself is the ruled order, reusing generic owners unmodified:
  1. **Fence at the Authority** — `AuthorityPort.cancel` on the fixed
     assignment. `authorize_failed_start_cleanup` refuses while the assignment
     is live and says why: a runtime stopped first would be torn out from under
     an assignment the authority still believes is executing.
  2. **`worker_manager.intake.authorize_failed_start_cleanup`**, authorized by
     this manager's own `runtime.start-failed` record rather than by output
     nobody froze.
  3. **`end_integration_execution(outcome="failed", exclusion="runtime-destroyed")`.**

`PreparationRuntime.adapter` composes the child worker's **own** observing
adapter exactly as `_SingleWorker` does when it identifies rather than starts —
assignment workspace roots, and no credential, launch delivery or orphan, since
all three exist for a start.

**Nothing is fabricated and nothing is released.** No terminal, result or intake
is invented; no second Work, claim or runtime is created; pre-intent recovery is
not widened; the root allocation stays held and apply stays planned.

### What the case now proves

    {"proof": "known-failed-start-is-ended", "runtime": "destroyed",
     "cleanup": "retained", "prepare": "ended", "adopted": false,
     "allocation": "recovery-required", "root": "open", "apply": "planned",
     "fixture_processes": 1, "parent": "queued-unclaimed"}

read from the owners, not from the absence of an exception: the start-failure
record exists, the runtime reaches `destroyed` with its result directory
`retained`, **the failure record still names the same `runtime_id`** so the
identity it was authorized by is preserved, and the membership is `ended`.

**The worker is proved gone against the process, not a record.** The fixture
engine now honours `rm` — the failed-start destroy — as it already honoured
`stop`, because a destroy that left this deployment's own worker running would
be a removal proved only against a record. `stop` follows an answered ending so
the process is already exiting; `rm` follows a failed start, where nothing asked
it to stop.

Supervised reversals (steps 17–19):

| Reversal | Result |
| --- | --- |
| the failed-start ending never runs | **1 case fails** |
| the Authority fence is skipped | **1 case errors** — the generic owner refuses a live assignment, exactly as documented |
| the membership is not ended | **1 case fails** |

### Verification and a baselined pre-existing failure

- Step 20, five focused modules: `OK`, **451 checks**, supervisor **46.047220 s**.
- Step 21, `test_stage_execution` + `test_single_worker`: **13 errors**, 57.517544 s.
- Step 23, the same two modules with **both sources restored to group1's
  accepted candidate bytes**: **13 errors**, 57.686464 s. Pre-existing,
  not introduced by this product change. (Step 22 is the same restore against my own module and
  fails 1 case, which is reversal H's signal — my new case depends on the
  change.)
- Across all 23 recorded rows: no run timed out, none was signalled, every run
  proved its process group gone.
- **Ledger: 23 rows, 692.951428 s.** Group1 author 98.710505 s, parent ledger
  2442.624596 s and reviewer cumulative 100.323193 s remain separate; the first
  three claims' unsupervised reversal runs remain an unrecorded unknown.

Candidate `candidate-172286.json`. **Three changed files** — the first product
change of this child:

- `v12/python/tools/integration_worker.py`
  `sha256:870656c0761d056310e5c846d163f95fc1273e987f3ce01ad1523ea09a7d3491`,
  97142 bytes, mode `0o644`
- `v12/python/tools/stage_execution.py`
  `sha256:762c7f5542c1a44b6ded477729ae96477b18471aca59921275eb5b2a7d8d33d7`,
  311452 bytes, mode `0o664`
- `v12/python/tests/tools/test_managed_preparation.py`
  `sha256:c86e6f82b5543a0cc6c719a179313bb694db9c5f2d9c8df1a8d5985e644c0d12`,
  127301 bytes, mode `0o644`

Modes unchanged; the five other group1 candidate files hash equal. No Git
mutation, no generic-owner edit, deterministic simulated engine with the real
worker process only.

### Remaining group2 scope

The review's other two required states: a **genuinely inconclusive** adapter
observation (assert the owner's uncertain state, preserve holds, forbid silent
relaunch or fabricated absence, and treat later exact observation as new
recovery evidence), and a **restart across the failed start** — my
`uncertain=True` path `continue`s and so skips the owed-restart handling.
Then: root/plan/profile/Job negatives; on-disk identity/task/manifest/digest/
length/source/harness and custody negatives; missing blobs, symlink/escape,
frozen-only and missing/quarantined intake; causal combined/base/isolated and
limits; two-Job isolation and defaults/overrides; cancellation/refusal and
leader-first/TERM-resistant ordinary cleanup; direct/legacy evidence; the
complete finite acceptance matrix; and `DEPLOYMENT-SLICE2-DRAFT.md`.

## Claim 172393 — the deliveries are torn down, and the failed start restarts

Read return172390, all events since 172344, the full thread (8 messages, no
pagination outstanding), `review-2026-09-14T21-34-01Z.md` and
`review-deliveries-172346.py`. Revalidated `candidate-172286.json` before
editing.

### I used an observing adapter for a destructive ending

The review is right and the cause is exactly where it says. `_adapter(roots,
None, None, None)` makes `OciAdapter._torn_down` and `_launch_ended` take their
**not-delivered** branches, so `authorize_failed_start_cleanup` settled and the
membership ended while the credential root and the launch root both stayed on
disk. My own comment said deliveries exist for a start and an ending performs
none — that omitted **recovery and teardown of the deliveries the start already
created**. `cleanup=retained` is result custody and authorizes retaining
neither of them.

`PreparationRuntime.adapter` is now composed the way `_SingleWorker.ending`
composes it, through the same owners and nothing new: `_mounted` for the roots
the launch mounted, `_credential` for the delivery — or the `OrphanTeardown`
capability when the start committed before its engine call and the materializing
process is gone — and `_adopted` for the launch delivery, which **adopts**
durable state and never authors a replacement under a container that may already
hold the mount. Nothing is rematerialized and no successful terminal is faked.

The case now reads both roots directly, **before** its own fixture removes its
tree — that removal is test resource ownership and proves nothing about the
product:

    {"proof": "known-failed-start-is-ended", "runtime": "destroyed",
     "cleanup": "retained", "credential_root": false, "launch_root": false,
     "prepare": "ended", "adopted": false, "allocation": "recovery-required",
     "root": "open", "apply": "planned", "fixture_processes": 1,
     "parent": "queued-unclaimed"}

Supervised reversals (steps 24–26): the observing adapter restored → **1 case
fails**; the launch delivery not adopted → **1 fails**; the credential
delivery/orphan not recovered → **1 fails**.

### The restart across the failed start

The review was right that my `uncertain=True` path `continue`d and so skipped
the owed-restart handling. Worse, once I removed the `continue` the handler fell
through into the pre-intent branch's `raise`, so the fault escaped. The branches
are now exclusive, and `test_a_restart_across_a_failed_start_still_ends_it_once`
closes the composition and both stores after the fault and rebuilds them:
everything the ending knows — committed intent, fixed assignment, current
runtime, this manager's own start-failure record — it reads back from an owner.
The same single ending follows.

**MY FIRST VERSION OF THIS CASE PROVED NOTHING and the reversal caught it.**
Removing the reopen left it green, because the uncertain path skipped the
`reopened` assertion. It now asserts exactly one restart was taken; step 29
reruns that reversal and the case **fails**.

### Verification

- Step 30, five focused modules: `OK`, **452 checks**, supervisor
  **49.152210 s**. Baseline at claim start was 451.
- Supervised reversals: steps 24, 25, 26, 27 (passed — the defective first
  form), 29 (fails after the fix).
- Across all 30 recorded rows: no run timed out, none was signalled, every run
  proved its process group gone.
- **Ledger: 30 rows, 919.456969 s.** Group1 author 98.710505 s, parent ledger
  2442.624596 s and reviewer cumulative 106.705591 s remain separate; the first
  three claims' unsupervised reversal runs remain an unrecorded unknown.
- **I did not re-baseline the 13 pre-existing `test_stage_execution` errors this
  claim.** The reviewer notes my step 21/23 comparison shows the same 13 case
  and final-exception signatures after fixture-path normalization but is "not
  clean"; I am not claiming more than that pairing showed.

Candidate `candidate-172393.json`:

- `v12/python/tools/integration_worker.py`
  `sha256:870656c0761d056310e5c846d163f95fc1273e987f3ce01ad1523ea09a7d3491`,
  97142 bytes, mode `0o644` (unchanged this claim)
- `v12/python/tools/stage_execution.py`
  `sha256:41a626f1cc52f45121e2c1c1424fd3fa3cf5fac6d6f2154924ca58974f8d61fe`,
  312396 bytes, mode `0o664`
- `v12/python/tests/tools/test_managed_preparation.py`
  `sha256:1f15c89730fe5fce6f1a2ee8e93cc9715342600c56a2a11b1a400a7accdd03f4`,
  129945 bytes, mode `0o644`

Five group1 siblings hash equal. No Git mutation, no generic-owner edit,
deterministic simulated engine with the real worker process only.

### Remaining group2 scope

A **genuinely inconclusive** adapter observation (assert the owner's uncertain
state, preserve holds, forbid silent relaunch or fabricated absence, treat later
exact observation as new recovery evidence) and **partial delivery** recovery —
both still owed. Then root/plan/profile/Job negatives; on-disk identity/task/
manifest/digest/length/source/harness and custody negatives; missing blobs,
symlink/escape, frozen-only and missing/quarantined intake; causal
combined/base/isolated and limits; two-Job isolation and defaults/overrides;
cancellation/refusal and leader-first/TERM-resistant ordinary cleanup;
direct/legacy evidence; the complete finite acceptance matrix; and
`DEPLOYMENT-SLICE2-DRAFT.md`.

## Claim172593 — baton.tuner, late-identity design preparation

M172570 selected immutable late-identity authorization; M172588 reassigned the
current design and later reviewed-scope implementation to tuner. I read canonical
detail, succeeded at claim172593, read complete work-events and all11 messages
in T170382 (no continuation), current policy/guide and full child dossier, latest
review/proposal, relevant parent selection/current rulings and actual owners.
Prior Claude progress remains unchanged.

Delivered LATE-START-DESIGN-172593.md: exact proposed12-path amendment, proof
operation/reader, atomic attachment and immutable receipt, distinct cleanup API
and adapter body, replay/current-observation separation, crash/race/partial
delivery/custody matrix, focused verification and file ownership. This is the
owner-requested design deliverable, not prerequisite implementation or group2
completion. Independent baton.feat design review must precede generic edits.

DESIGN-BASELINE-172593.json binds all proposed paths and verifies the eight
candidate172393/sibling files against reviewer172443: hashes, sizes and modes
match. Existing known-failure receipt/runtime comparison remains untouched.
Changed only dossier design/status/evidence; no product, test or Git mutation.
No test or engine/model run: new verification spending0s. Prior author recorded
subset919.4569689099153s and reviewer cumulative124.07460133001587s are preserved,
with older unknown experiments still unknown; group1/parent costs stay separate.

Next: independent design review on baton.feat, set-next=baton.tune. Then approved
prerequisite implementation and remaining full group2 matrix/draft under a new
claim, followed by independent candidate review. No Work closure, import approval
or group3/parent release. DESIGN-HANDOFF-172593.json binds this design handoff.

## Claim172672 — baton.tuner, manual recovery and remaining evidence

Consumed owner M172655 and review172649; automatic late-identity design is
superseded. All eight candidate/sibling hashes revalidated before editing.
Current exclusive source/test ownership: v12/python/tools/integration_worker.py,
v12/python/tests/tools/test_managed_preparation.py, and only necessary causal
cases in v12/python/tests/manager/test_reconciliation_task.py. Baseline bytes
retained in baseline-172672.json and baseline-172672/. Generic owners remain
reuse-only. First revalidate reporting, add the bounded actionable manual
recovery message and prove unknown/restart holds, then map existing evidence
and complete remaining selected requirements. No new permission/budget gate.

### 2026-09-14T22:34:21Z — consumed scope reductions and bounded default correction

M172691 defers unfinished partial-delivery work; M172730 defers the expanded adversarial/causal/limit/two-Job matrix to v13. Stop expansion. The narrow known-failed-start cleanup guard and four passing teardown retries were completed before consuming the partial-delivery deferral; the four identity cases and causal component cases likewise predate consumption of M172730. Preserve that evidence, but do not claim the wider matrices proved. No generic protocol/API work is implemented. Add only the demonstrated wrong-default correction pinned above; exclusive file ownership additionally includes v12/worker/reconciliation_entry.py, already in accepted source scope, with preserved baseline. Finish retained-scope evidence and deployment draft for independent review.

Operational read finding: initial lookups of repository-root DEPLOYMENT.md and v12/DEPLOYMENT.md failed because those were incorrect locators. `rg --files -g DEPLOYMENT.md` resolved the selected manual to v12/python/DEPLOYMENT.md; its relevant slice1 section was read successfully. No required file remains unread for this correction/draft; no main-manual edit.

### 2026-09-14T22:39:04Z — retained scope complete, awaiting independent review

Consumed M172741 and its22:33:45Z shutdown-matrix deferral. Delivered visible
manual-recovery reporting through the actual sweep action detail, preserving
unknown state, original receipt, one runtime and all unresolved holds across
restart. Known-failed-start cleanup now ends membership only after ordinary
cleanup retained/complete, fixing the22:27 premature-ending finding. The concrete
wrong1800s default was reproduced by172681 and corrected to the original sealed
Job-owned host_verification300s boundary, preserving explicit overrides and other
defaults. No generic owner code changed.

Changed source: integration_worker.py and reconciliation_entry.py. Changed tests:
test_managed_preparation.py (manual/restart reports, teardown guard, retained four
identity cases, corrected default expectation/override) and test_reconciliation_task.py
(retained causal component failures). All exact repo paths/baselines/candidate
bytes are in candidate-172672.json and delta-172672-*.patch. Test changes are
within standing authority; existing wrong-default assertion is corrected against
the accepted behavior, not weakened to obtain a pass. Other historical assertions
and independent reviews remain preserved. Five prior sibling hashes still match
reviewer172443; full17 selected source/test paths are captured for review context.

Final focused run172682:148 tests passed,66.34870723698987s; git diff --check
passed for all four changed source/test paths. No product/test edits followed
that run. This claim11 supervised rows cost129.28244445097516s; author ledger
41 rows totals1048.7394133608905s. Every run group gone, no timeouts/signals;
failures and fixture mistakes retained. Reviewer124.07460133001587s, group1
author98.71050525197643s and parent2442.624596s remain separate; older experiments
still unknown. No additional testing is justified after the passing focused run.

ACCEPTANCE-172672.md maps retained behavior and exact limits of evidence, records
all failed runs, and explicitly labels deferred v13 matrices unproved. Local
DEPLOYMENT-SLICE2-DRAFT.md covers the actual selection/lifecycle/custody/manual
recovery and later-apply limits; main v12/python/DEPLOYMENT.md was not edited.
No OCI build/pull/engine execution/model, generic API, Git mutation, automatic
late-identity recovery or deferred campaign. The completed narrow teardown tests
do not certify the deferred partial-delivery protocol.

Next: pass W170382 to baton.feat set-next=baton.tune for independent review of
this immutable candidate and retained scope. This is an author completion claim,
not independent acceptance, Work closure, import approval or group3/parent release.
