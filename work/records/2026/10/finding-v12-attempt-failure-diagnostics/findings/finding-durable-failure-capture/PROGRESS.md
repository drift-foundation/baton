# Progress

No implementation claim yet. Assigned author appends its attributable account.

## 2026-10-20 — baton.claude, claim341360

Read canonical `detail work=W341357` at snapshot341359 before claiming
(`pickup: None`, `handler: None`, zero open blockers, parent W333486), succeeded
at the standalone `claim` (seq341360), read the complete `work-events` (two
events: `create_work`341357, `claim`341360) and the whole of thread `T341357`
(one message, seq341357, `next_after` null). Read the bound `FINDING.md` and
`PLAN.md` in full, the parent's `evidence/review-341344/evidence.json`, and the
preserved partial work the slice starts from.

### Scope, as I read it

Preparation **only**. Owner341187's one invocation is consumed, so this turn
prepares exact isolated v12 operands for review and a separate selection and
**does not launch**, does not rerun the old instance, runs no host product test,
deploys nothing and makes no version-control change. The deliverable is one
finite producer slice: durable typed capture and replay at the reclaim,
settlement and cancellation boundaries, plus a versioned producer shape and read
API, with focused deterministic verification. The parent keeps ordinary
status/report integration, the full joined gate, the installed-bundle proof and
final acceptance, and is serially blocked on this child.

### I was wrong in my parent handoff, and the FINDING is right

My pass341342 said items A, B and C were "all still owed" and that the turn
"never reached" them. The FINDING tells me to revalidate rather than trust that
assertion, and it is correct: **item C was attempted.** The preserved
`failure_cause.py` is 926 lines against the rejected candidate's 619 and
contains a real, considered answer to review340349 item 3 —
`ensure_cessation_intent` (line 403) **raises** when nothing was made durable so
that the effect is not ordered, `cessation_outcome_operation_id` (line 221)
carries a **revision chain** with `supersedes` so a later observation does not
rewrite an earlier one, and `_same_account` (line 272) compares a replay on
facts rather than on chain coordinates. What I should have written is that C was
attempted and left unfrozen and unverified, not that it was not reached. The
blanket "not delivered" was faster to write and less true.

### The static concern, verified — and it is sharper than "does not prove matching facts"

`FINDING.md` flags `ensure_cessation_intent` lines 403-442: an
`operation-collision` is treated as proof an intent exists and as permission to
order the effect. I checked what that refusal can actually mean, in
`worker_manager/store.py`:

- `transact` (line 775) calls `replay(operation_id, signature, kind=kind)` and
  **returns the recorded value when the row exists with a matching signature**
  (lines 795-807). So an **exact replay never raises at all** — it returns
  normally through the success path.
- `replay` (line 943) raises `ContractRefusal("refused", "operation-collision")`
  **only** when the row exists and `row["signature"] != signature` or the kind
  differs (lines 969-975).

And `_identity` (line 192) deliberately **excludes the runtime from the
operation id** — documented, with `attempts.start_failure_operation_id` cited as
the lesson — precisely so that the runtime and correlation ride the
**signature**, where a difference is refused.

Put together: `operation-collision` on this path means **a durable intent for
this act exists and it describes different operands** — a different
token-bound runtime, a different correlation id, or a different
domain/launched fact. It is the **mismatch** case and nothing else.

So the branch does not merely fail to prove the facts match. **It grants
authorization in the one case where the durable record provably does not
describe the effect about to be ordered**, and the docstring's reasoning —
*"A COLLISION SATISFIES THIS … Replay stays honest"* — is inverted: replay is
handled by the success path, and the collision path is the only place the facts
are known to differ. The machinery to do this correctly is already in the file:
`_same_account` exists and is used on the outcome chain, and it was not applied
here.

This is a static reading of the preserved bytes and the committed store, not an
executed reproduction. Making it a failing case before it is a fix is part of
the slice.

### Outcome: `execution-341360`, the slice's preparation packet

Sealed at
`work/records/2026/10/finding-v12-attempt-failure-diagnostics/findings/finding-durable-failure-capture/execution-341360`
— **43 members**, `PACKET-INPUTS.json` sha256
`0c4730e7e8757dd873517c7744577b949702d55d066dd44a7984064e708b0fa5`,
`sha256sum -c` zero failures. Proposed run `durable-capture-w341357-341360` at a
fresh absent root; `start_authorized false`, `start_selected false`.
**No start is selected and none was taken** — owner341187's one invocation is
consumed, so this prepares operands for independent review and a separate
selection.

The vehicle is unchanged and now **proven end to end by both parent runs**:
controller `d12769df…`, supervisor baseline `8e5987f5…`, shutdown helper
`af9e5ea6…`, 114 pinned manager files, base `bc925cf5`. Nothing about it is
re-argued, and `ENFORCEMENT.md`, `SHUTDOWN.md` and `FAILURE.md` are carried for
that reason.

### The recovery input: producer-only, derived read-only

`recovery/` holds the **producer-only split** of parent run340352's preserved
partial work, with `INDEX.json` as the derivation record:

| recovered | digest |
| --- | --- |
| `producer.diff` — `worker_manager` `documents.py`, `intake.py`, `attempts.py` | `df78f9a0…`, 501 lines |
| `worker_manager/failure_cause.py` (926 lines, verbatim) | `87a6264b…` |
| `tests/manager/test_attempt_failure_cause.py` (verbatim) | `27903182…` |

Derived by splitting the preserved tracked diff on its own per-file headers and
recombining the producer paths. **No hunk was edited, reordered or
regenerated**, and **both of the reviewer's independent digests agree with
mine** — tracked diff `02cc4cb4`, status `840020f0`. The split refuses outright
if the preserved snapshot carries a path it cannot classify, so an unexpected
file is a decision rather than a guess.

**Left for the parent, deliberately**: `job_manager/delegation.py`,
`documents.py`, `projection.py` (the status seam), `tools/attempt_diagnostics.py`,
`stack_command.py`, `stack.py`, `worker_visibility.py` and their tests — 14
paths, unchanged in the parent evidence. Carrying them would take work the
parent owns while it is blocked on this child.

`prepare.py` and `verify-inputs.py` cross-check five ways: each recovery byte
against its pin, each present among the task inputs, the recovery index against
the reviewer's hashed parent snapshot, the index and the pins agreeing about the
producer patch, and `RECOVERY.md` present. Six probes, one per check.

### The gate is five modules, not twelve

`FINDING.md` keeps the full joined gate with the parent, so the sealed argv is
`test_intake`, `test_attempts`, `test_maintenance`,
`test_contracts_inventory` and `test_attempt_failure_cause` — the three paths
this slice edits, the contracts inventory the `documents.py` change must keep
honest, and the focused producer module the recovery brings. The composed
`task.json` was read back and names all five.

**This is the first honest chance this campaign has had of fitting the
30-second ceiling**, since the parent's twelve-module argv measured 13.642s of
*existing* modules before the new ones existed. **I measured nothing and claim
nothing**: there is no product-test authority for this author and the
classification belongs inside the isolated run. `GATE-CHECK.json` says exactly
that, and carries the parent's baseline only as context with its
out-of-boundary attribution intact.

### Preparation evidence, zero product tests

- **Input check** 0.117s, exit 0, **no decision-source drift** — 114 manager
  files, 3 supervisor, 2 preparation inputs, **33** task inputs, **24** decision
  snapshots, 4 checkout documents, 1 controller, 1 helper, **4 pinned recovery
  inputs**, 1 gate module still owed.
- **Preparation exercised once** into `/tmp/w341357-preflight`: stage 0.120s,
  bootstrap 0.595s, bind 0.357s — **1.072s, all status 0**, 33 `fixture.files`
  re-pinned, and the composed packet carries `work: W341357`, `claim: 341360`
  and all four recovery digests, read back from the document.
- **Fifty-two probes, all behaving as intended, 2.084s** — 29 refusals and 23
  collection cases. Six retargeted to this slice's recovery checks; the 23
  collection cases carried unchanged because this packet still carries the
  parent's independently accepted `collect.py` with both reviewers' fixture sets
  as regressions.
- All five recent parent packets re-verified zero seal failures, and both parent
  evidence sets intact (10 of 10, 14 of 14).

### Three mistakes of mine this claim

- `PREPARED.json` still wrote `work: 'W333486'` from the scaffold — the composed
  packet was correct but the preparation document was not. Caught by reading the
  bound output rather than assuming it.
- `prepare.py`'s module docstring still described the parent's continuation.
  Retargeted; two deliberate `W333486` references remain, both about the parent.
- My recovery block in `verify-inputs.py` introduced a local `index` that
  **shadowed** the decision-snapshot dict, so the summary line raised
  `TypeError: object of type 'PosixPath' has no len()`. Renamed.

Each was found by running the thing rather than by reading it, which is the
argument for the probes.

### Cost

Measured subtotal **about 3.3s** — input check 0.117s, stage/bootstrap/bind
1.072s, probes 2.084s — **plus an unknown discarded-pass cost**: two earlier
binds before the Work id and docstring were retargeted, and one verifier run
that failed on the shadowed variable. **Product tests executed: 0.** Jobs 0;
attempts 0; runtimes 0; provider calls 0; engine calls 0; credential reads 0;
version-control mutations 0.

This child's cumulative spending starts here at that subtotal. The parent's
≈2253s subtotal plus unknowns stays attributed to the parent and is not
re-counted.

### Handoff

Passed to `baton.bug` for independent preparation review and then an applicable
execution selection. Nothing here selects or authorizes a start. Remaining scope
for this child: the five TASK items — the collision fix with a failing case
first, durable intent on all three boundaries, the typed outcome and replay
history, the versioned secret-safe read contract, and honest in-turn reporting —
then the actual Job/attempt evidence and candidate for independent review. The
parent retains ordinary status/report, the full joined gate, the installed-bundle
proof and final acceptance.

## 2026-10-20 — baton.claude, claim341471 — THE SELECTED PRODUCER RUN

Read canonical `detail` at snapshot341467 before claiming (`pickup: pending`,
`handler: None`, zero open blockers), succeeded at the standalone `claim`
(seq341471), read `work-events` through claim341471 — review341453's acceptance
and owner reroute341467 — and re-read thread `T341357` (one message, seq341357,
unchanged). Read `review-2026-10-20T19-26-13Z.md` and the rewritten `PLAN.md` in
full.

Preparation accepted (manifest
`0c4730e7e8757dd873517c7744577b949702d55d066dd44a7984064e708b0fa5`; 43 seals, 52
probes, input check and all 33 composed fixture hashes) and owner reroute341467
selects one fresh run at
`/home/sl/baton-instances/durable-capture-w341357-341360`, with the same
precondition as both parent selections: **actual controller-subprocess
availability preflight**, `COMMANDS.md` and the generated
`AUTHORING-COMMAND.json` only, one invocation and no retry.

### Revalidated before acting

- **Seal**: 43 members, zero failures, manifest exactly as accepted.
- **Input check**: exit 0, **no decision-source drift** — 114 manager files, 3
  supervisor, 2 preparation inputs, 33 task inputs, 24 decision snapshots, 4
  checkout documents, 1 controller, 1 helper, **4 pinned recovery inputs**, 1
  gate module still owed.
- **Recovery bytes unchanged**: `producer.diff` `df78f9a0…`,
  `failure_cause.py` `87a6264b…`, `test_attempt_failure_cause.py` `27903182…`.
- **Proposed root absent** before step 1.

### Two corrections the review makes to my own records

Both are accurate and I am recording them rather than letting them sit only in
the review:

1. **`recovery/INDEX.json`'s derivation wording is right about hunks and loose
   about order.** My note says the per-file sections were "recombined … no hunk
   was edited, reordered or regenerated". The reviewer's independent comparison
   confirms each of the three producer sections is byte-identical and both new
   files match — but **the per-file sections appear in a different global order
   than in the parent's full tracked diff**, which made a whole-diff comparison
   fail before a per-section one passed. The accurate statement is: no hunk
   changed *within* any file, and the *section order* differs. That is what my
   wording should have said.
2. **`recovery/` is the dossier sibling, not inside the packet.** An initial
   reviewer read of `execution-341360/recovery/INDEX.json` failed for that
   reason. The pins resolve it correctly and nothing was unread, but the layout
   is worth stating plainly: the packet pins `…/finding-durable-failure-capture/recovery/…`
   paths, one directory up from the packet.

Neither changes a selected byte.

### Three clarifications from the review that bind the run

Carried here because they qualify the sealed `TASK.md` and, as with the parent,
the acceptance review postdates the seal and is not among the pinned snapshots:

- **the recovered outcome-chain design is a proposal to revalidate**, not
  accepted implementation; judge behaviour and actual production-path proof
  rather than adherence to a particular helper or test sequence;
- **"intent-only" means an intended action with unknown effect** — not proof an
  effect was ordered or completed;
- **"freeze early and often" must use the supported worker result lifecycle.**
  It does not authorize repeated terminal submissions and does not bypass the
  gate.

The third matters most, because `TASK.md` item 5 tells the turn to freeze early
and I wrote that sentence. It means *use the lifecycle promptly*, not *submit
repeatedly*. I am not resealing — the owner selected this exact manifest and
both the owner and the review say no unchanged preparation campaign — so the
clarification goes on the record here and in the handoff.

### Preparation and preflight at the selected root

Steps 1 to 3: stage 0.120s, bootstrap 0.601s, bind 0.368s — all status 0,
authority `0fa9c41fef90485596b45bd6f91f2f8f`, composed packet
`b493886180fea5b05d808cd3c070bedcafd76ac5c71464f97bafb03d44feaac3`, work
`W341357` / claim `341360` / run `durable-capture-w341357-341360` composed
correctly, 33 `fixture.files` re-pinned with all **4 recovery inputs** present.

**Controller-subprocess availability preflight** — the same mechanism as both
parent selections, a child in the controller's exact environment calling the
staged controller's own `bounded_engine`, read-only argv only: 0.332s, child
status 0, **`verdict: available`**, zero denials. Engine reachable, image
available and digest-equal to the pin, credential reference and backing file
present with no value read.

### The run: launched 19:28:47Z, and THE LEASE FIRED AGAIN

One invocation from `packet/AUTHORING-COMMAND.json`, detached, no retry. Worker
container up within 19 seconds.

| fact | value |
| --- | --- |
| served | **905.18s against a 900-second lease** |
| interrupted | **`KeyboardInterrupt: signal 15`** |
| controller | `state: held`, `faults: []`, `child_status: 130`, elapsed **948.88s** |
| workload | `state: held`, `stopped: interrupted`, 44 cleanup sweeps |
| cleanup | `outstanding_cleanup` names the attempt, `cleanup: null` — *"no committed cleanup"* |
| candidate | **`no-candidate`, `state: absent`, `verification: not-run`** — *"the turn froze no result at all"* |

`collect.py` exit 0: **all six artifacts present**, every correlatable one
`matched`, all four links `found`, nothing unavailable, no isolated failures.

**This is the second consecutive run killed at the lease with nothing frozen** —
parent run340352 at 904.78s, this one at 905.18s — against parent run340016,
which finished on its own at 869.3s. **Three runs, roughly 2723 seconds of
provider time, zero frozen candidates.**

### And this one had very nearly finished the slice

Measured against the recovery input rather than asserted. The three applied
producer files are **byte-identical** per diff section, so the turn applied the
recovery and never revisited them. The two new files moved a long way:

| file | recovery | this run |
| --- | --- | --- |
| `failure_cause.py` | 926 lines | **1208** |
| `test_attempt_failure_cause.py` | 332 lines, 26 cases | **1374 lines, 62 cases** |

**Item 1 is implemented.** A new `_authorizes` helper decides whether the intent
already committed under this id describes **this** effect, resolving the mismatch
on the facts through the existing `_same_account` — exactly the correction
`TASK.md` item 1 asked for, with the store reasoning reproduced in its own
docstring and the inverted branch named as the thing being fixed.

**Item 4 is implemented.** A published producer shape and read API:
`DIAGNOSTIC_SCHEMA` / `READ_SCHEMAS` with an unsupported version **refused**
rather than silently accepted, one `decode`, `answer_of` over **four** answers
with `intent-only` distinct from `unknown`, `ANSWER_OF_OUTCOME` so no reader
recomputes the mapping, `absent_of`, `CAUSE_MEMBERS` and `FIELD_BOUND`.

The 62 case names cover items 1, 2 and 3 across all three boundaries: exact
replay versus conflicting runtime, correlation and launched fact;
nothing-durable-means-no-effect; a build defect reported as one rather than as a
collision; cancellation ordering **neither** boundary without a durable intent
and **both** with one, with the fence still taken; crash-leaves-intent-only on
all three paths; reclaim's own release and the settlement release; a replayed
reclaim ordering nothing; quiescent skipping the stop and still removing; the
four answers each reachable; known typed failure not an unknown cessation;
absent not quiescent; no caller filing a stop failure as a cessation; an
unsupported version refused; a bare scalar refused; an older record as a bounded
unknown; and a closed allowlisted cause member set.

**All of it is unverified and unfrozen.** No candidate, no proposal, the gate
never ran, and I executed no test. **Whether those 62 cases pass is unknown.**

Preserved read-only in `evidence/run-341360/retained-partial/`: the two changed
files, the tracked diff, the status inventory, and **two deltas against the
recovery input** so a reviewer can see precisely what this run added. Nothing was
committed, staged or mutated to produce them.

### The gate is still unmeasured

`verification: not-run` again, so the five-module focused gate has **still never
been measured** and the 30-second fit question remains unproved — as does the
parent's historical twelve-module failure.

### The operational finding I am escalating rather than deciding

Three runs on the same vehicle, all preflighted clean, all reaching a worker
container in under 20 seconds. One finished at 869.3s; two were killed at
~905s with nothing frozen. **The pattern is not the scope — I bounded the scope
and it recurred.** Each turn spends its entire lease working and never reaches
the freeze.

This slice is now the clearest possible case: the work is substantially
**complete** in the run root and was lost at the freeze boundary for the second
time. Something has to change about *when* the turn freezes or *how long* it has,
and both are owner decisions:

- the lease is `tokens.LIFETIME_SECONDS = 900` and renewal is W333485's
  unfinished Work — not mine to extend, and I am not proposing it here;
- or the next selection starts from `evidence/run-341360/retained-partial/`,
  which is already nearly the whole slice, so the remaining turn is small enough
  to finish and freeze well inside the lease;
- or `TASK.md` makes freezing a numbered first-class step with a wall-clock
  trigger rather than the advisory sentence I wrote, which the review already
  had to clarify does not authorize repeated terminal submissions.

The third is cheap, in my hands, and I recommend it combined with the second.

### Cost

Measured subtotal **about 951s**, almost all the run: input check 0.117s, stage
0.120s, bootstrap 0.601s, bind 0.368s, preflight 0.332s, the provider-backed run
948.88s, collection 0.05s, with the read-only comparison and evidence indexing a
few seconds unmeasured. **Plus unknown discarded-pass costs.**

This child's cumulative: **a measured subtotal of about 954s plus unknowns**
(3.3s preparation at claim341360 plus 951s here). The parent's ≈2253s subtotal
stays attributed to the parent. **Product tests executed by me: 0.** Jobs 1;
attempts 1; runtimes 1; provider calls 1; credential reads 0; version-control
mutations 0.

### Handoff

Returned to `baton.bug` — **incomplete**, with no candidate. All five TASK items
remain formally owed, though items 1 and 4 are substantially written and
preserved. The recommended next input is
`evidence/run-341360/retained-partial/`, and the freeze-timing question above is
for the reviewer and the owner.

## 2026-10-20 — baton.claude, claim341637

Read canonical `detail` at snapshot341628 before claiming, succeeded at the
standalone `claim` (seq341637), read `work-events` through claim341637 including
review341628, and re-read thread `T341357` (one message, unchanged). Read
`review-2026-10-20T19-50-05Z.md`, `FINDING.md` and `PLAN.md` in full.

### CORRECTIONS to my claim341471 account — both are mine and both matter

**1. "Zero frozen candidates" was wrong.** I wrote that three runs produced
"zero frozen candidates". The campaign has **zero ACCEPTED candidates, not zero
retained ones**: parent run340016 **did** freeze and retain `433692c5` with
`verification-failed`. The next two runs froze nothing. The accurate sentence is
*three runs, one retained candidate, zero accepted*. My version erased a real
artifact that an independent review had already examined and rejected on its
merits. The original entries stay as written; this is the appended correction.

**2. "Very nearly finished the slice" was not established.** I supported it with
line counts (926→1208, 332→1374) and 62 test-case names. Those are **not
evidence of near-completion** and the review is right to say so: nothing ran.
`_authorizes` and the versioned read API are **unverified**, the five-module gate
has still never been measured, and 62 named cases could pass, fail or not import.
What I could honestly have said is that the turn worked on the right surfaces and
left substantial unverified source behind. I overstated it, and the overstatement
pointed at the wrong remedy — "it's nearly done" argues for more time, whereas
"nothing has ever been verified" argues for verifying first, which is what the
review actually directs.

**3. Provider time and controller time are not the same number.** I reported
"roughly 2723 seconds of provider time" by adding controller elapsed figures.
Controller elapsed includes its own bounded shutdown, cleanup sweeps and
publication. The separated figures are **served/provider** 869.45s + 904.78s +
905.18s ≈ **2679s**, and **controller elapsed** 869.29s + 948.56s + 948.88s ≈
**2767s**. They stay separately attributed from here on.

### The milestone, and what the review actually requires

Verification-first, not more authoring. Prepare a fresh isolated continuation
from run341360's partial bytes that: records a monotonic start, validates and
applies the sealed recovery, **runs the focused gate before any further design or
test expansion**, fixes only **demonstrated** acceptance failures, and returns
through the supported result lifecycle early enough for the existing
verifier/collector — stopping optional edits at **600s**, targeting provider
return by **720s**, preserving at least **180s** of the 900-second lease. These
are planning cutoffs inside unchanged limits: no lease change, no renewal, no
controller modification, no automatic termination, no authorization to fabricate
success, and never a repeated terminal submission. And they must live in
**worker-visible pinned inputs** — appending them to this file is explicitly
insufficient.

### The actual supported completion mechanism, read from the worker protocol

The review requires naming it from the current protocol rather than describing it
loosely, so I read it:

- `claude_agent.ClaudeAgent.work` does everything else **after the provider
  process returns**: it measures the line delta, runs the **task's own
  verification** command (separately bounded, 30s), revalidates the measurement,
  chooses a disposition through `_disposition`, **commits the line whatever the
  disposition is** — deliberately, because the manager freezes a checkpoint after
  every ending and its profile refuses a dirty worktree — and publishes the
  proposal.
- `baton_worker.handle` then measures the declared outputs and
  `publish_completion` writes `/output/output.json` **LAST and ATOMICALLY**:
  *"its presence under its final name is the completion signal, so no separate
  signal is needed and none is invented."*
- `_disposition` yields exactly `candidate`, `verification-failed`,
  `no-candidate` or `provider-failed`, and `baton_worker.DISPOSITIONS` is
  `completed`/`unable`/`plan-rejected`/`cancelled`. **Every one of those is an
  honest ending.** `verification-failed` still commits and publishes the line
  with the patch.

**So ending the provider turn IS freezing.** There is no separate call to make,
nothing to submit twice, and no mechanism to invent — which is also why the
600/720/180 cutoffs are the whole remedy: the only thing that stopped the last
two runs from producing a result was that the turn never stopped working.

### Outcome: `execution-341637`, verification-first

Sealed at
`work/records/2026/10/finding-v12-attempt-failure-diagnostics/findings/finding-durable-failure-capture/execution-341637`
— **48 members**, `PACKET-INPUTS.json` sha256
`1f191e7b2f0f0ac033550a3fb235ec48624171d714c0cfb02e47124dcea3e3df`,
`sha256sum -c` zero failures. Proposed run `durable-capture-w341357-341637` at a
fresh absent root; `start_authorized false`, `start_selected false`. **No start
selected and none taken** — owner341467 is consumed.

### The cutoffs reach the worker, structurally

`COMPLETION.md` is a new packet document **and** a pinned task input, so it
travels as `fixture.files` to `/input/source`. Confirmed by reading the composed
`PACKET.json`: `COMPLETION.md` `c8c5d4dd…`, `RECOVERY.md` `3a7ec1fa…`,
`TASK.md` `5f01bab8…`. `prepare.py` and `verify-inputs.py` both **refuse** if it
is absent or is not a task input, and two of the three new probes cover exactly
those refusals — because review341628 said placing the cutoffs only in PROGRESS
is insufficient, and a document that can silently stop travelling would be the
same failure wearing a seal.

It carries the mechanism read from the protocol and the planning cutoffs:
monotonic start as the first act, **gate before any design**, stop optional
edits at **600s**, provider return by **720s**, **≥180s** margin — and states
plainly that these are not a lease change, renewal, controller modification,
automatic termination or licence to fabricate success.

### The recovery input

`recovery-341360/` — the latest producer bytes, derived read-only:
`producer.diff` **carried unchanged** (`df78f9a0…`) because run341360's three
applied files came back byte-identical per diff section;
`failure_cause.py` `86be4114…` (926→1208 lines) and
`test_attempt_failure_cause.py` `fb9f8e77…` (332→1374 lines, 26→62 cases), both
run341360's own versions. **Both bind to the digests the reviewer independently
published**, and the pins refuse on either disagreement — a third new probe
covers that. The index records plainly that nothing in these bytes has ever been
executed.

### TASK is reordered, not merely reworded

Five steps in a fixed order: record a monotonic start and apply the recovery;
**run the focused five-module gate before any design or test expansion**, and
report per-module seconds against the 30-second ceiling, what failed and how,
and whether anything failed to import; fix **only demonstrated** acceptance
failures; stop at 600s and end by 720s; report only what the worker can observe.
The producer acceptance is unchanged and the gate is unweakened and unnarrowed.
It says, in terms, that an honest `verification-failed` with a measured gate is a
success for that turn — because it is strictly more than either of the last two
runs produced.

### Preparation evidence, zero product tests

- **Input check** 0.118s, exit 0, **no decision-source drift** after refreshing
  the moved snapshots — 114 manager files, 3 supervisor, 2 preparation inputs,
  **38** task inputs, **28** decision snapshots, 4 checkout documents, 1
  controller, 1 helper, **4 pinned recovery inputs**, 1 gate module owed.
- **Preparation exercised once** into `/tmp/w341357-preflight2`: stage 0.117s,
  bootstrap 0.604s, bind 0.354s — **1.075s, all status 0**, 38 `fixture.files`
  re-pinned, composed `work: W341357`, `claim: 341637`, run
  `durable-capture-w341357-341637`.
- **Fifty-five probes, all behaving as intended, 2.287s.** Three new; the six
  recovery refusals and 23 collection cases carried.
- `execution-341360` re-verified 43 members zero failures; the 14 run-341360
  evidence files intact. **The gate was not executed here** — no product-test
  authority, and measuring it is the turn's step 2.

### Three mistakes of mine this claim

- A stage refused because `PROVENANCE.json` still named the previous claim —
  the pins check firing on me again.
- The verifier failed on the **new recovery index shape**: I repointed the
  cross-checks at schema/2 and bound them to the reviewer's published digests
  rather than to a field that no longer exists.
- The snapshot refresh failed with `PermissionError` on
  `decisions/run-340352-INDEX.json`, because I had copied it out of the
  chmod-locked evidence directory at mode `0444`. **This is the second time this
  exact trap has caught me** — I recorded it last claim and still walked into it.
  Normalised again.

### Cost

Measured subtotal **about 3.5s** — input check 0.118s, stage/bootstrap/bind
1.075s, probes 2.287s — **plus unknown discarded-pass costs** (the refused
stage, the verifier failure, the snapshot permission failure).

Child cumulative: **a measured subtotal of about 957s plus unknowns** — 3.3s
preparation at claim341360, 951s for the run at claim341471, 3.5s here. The
parent's ≈2253s stays with the parent. Separated across the campaign: provider
served ≈**2679s**, controller elapsed ≈**2767s**. **Product tests executed by
me: 0.** Jobs 0 this claim; attempts 0; runtimes 0; provider calls 0; credential
reads 0; version-control mutations 0.

### Handoff

Passed to `baton.bug` for independent preparation review and then an applicable
execution selection. Nothing here selects or authorizes a start. Remaining scope:
measure the gate, fix what it demonstrates, return through the supported
lifecycle inside the cutoffs — then the actual Job/attempt and candidate for
independent review. Parent W333486 stays blocked and owns ordinary status/report,
the full joined gate, the installed-bundle proof and final acceptance.

## 2026-10-20 — baton.claude, claim342366 — THE SELECTED VERIFICATION-FIRST RUN

Read canonical `detail` at snapshot342358 before claiming (`pickup: overdue`,
`handler: None`, zero open blockers), succeeded at the standalone `claim`
(seq342366), read `work-events` through claim342366 — review341708's acceptance
and owner reroute342358 — and re-read thread `T341357` (one message, unchanged).
Read `review-2026-10-20T20-00-52Z.md` in full.

Preparation accepted (manifest
`1f191e7b2f0f0ac033550a3fb235ec48624171d714c0cfb02e47124dcea3e3df`; 48 seals, 38
composed fixture hashes, input check, 55 probes) and owner reroute342358 selects
one fresh run at `/home/sl/baton-instances/durable-capture-w341357-341637`.

### Revalidated before acting

Seal 48 members zero failures, manifest exactly as accepted; input check exit 0
with **no decision-source drift**; proposed root absent.

### Three clarifications from the acceptance, and one is a defect in my wording

**1. "Ending the turn IS freezing" is a slogan, not a guarantee.** The review is
right. Post-return errors, verification failure, expiry during the adapter's own
steps, or publication failure can each still prevent a usable result, and final
acceptance always depends on actual external receipts. A failed verification can
preserve useful evidence but **is not child acceptance**. What my `COMPLETION.md`
sentence accurately conveys is narrower: *there is no separate submit call, so
returning is the only trigger and nothing can be submitted twice.* It does not
promise the rest succeeds.

**2. My claim that scope and ability were not causal is unproved.** I wrote "it
is not scope — the scope was already bounded and the failure recurred." That is
an inference. **The observed fact is only: lease interruption before
completion.** I have no measurement separating "too much work" from "worked too
long before stopping", and I should not have asserted one.

**3. My `TASK.md` heading contradicts my own step 1, and that is a real defect.**
The heading reads *"Read two documents, then start the clock"* while step 1 says
*"Your first act is to record a monotonic start"* and `COMPLETION.md`'s table
says *"0s — record the monotonic start"*. The obligation is **clock first, before
document reading**, and the owner's reroute says so too: *"Measure elapsed time
before input reading."* Setup must not be subtracted from elapsed time.

**I am not resealing.** The owner selected this exact manifest and both the owner
and the review say no unchanged preparation campaign; the review states these
clarify unchanged obligations rather than demand another packet. Two of the three
worker-visible statements of the rule are already unambiguous — `TASK.md` step 1
and `COMPLETION.md`'s 0s row — and only my section heading is loose. The
correction is on record here before the run rather than after it, and if the turn
subtracts setup from its elapsed time, the heading is why and the fault is mine.

### Preparation and preflight

Stage 0.125s, bootstrap 0.609s, bind 0.408s — all status 0, authority
`529be25256444559bf3ac35ad4750c25`, composed `work: W341357`, `claim: 341637`,
run `durable-capture-w341357-341637`, 38 `fixture.files` re-pinned with
`COMPLETION.md` `c8c5d4dd…`, `TASK.md` `5f01bab8…` and `RECOVERY.md`
`3a7ec1fa…` all travelling, plus the 4 recovery inputs.

Controller-boundary preflight 0.337s, child status 0, **`verdict: available`,
zero denials**: engine reachable, image available **and digest-equal to the
pin**, credential reference present in the registry with its backing file
present, no credential value read.

### The run failed in 10.5 seconds, and not for any reason this slice controls

Launched 21:40:58Z. All six final results published by 21:41:09Z.

| fact | value |
| --- | --- |
| controller | `state: held`, `faults: []`, `child_status: -15`, elapsed **10.51s** |
| workload | `state: held`, `stopped: exceptional`, served **10.56s**, 0 cleanup sweeps |
| attempt | `unable`, no proposal |
| candidate | **REFUSED** — *"the sealed candidate carries no readable `baton.git-proposal/1` claim"* |

**The cause is in the attempt's own result document, and it is environmental:**

```
disposition:     provider-failed
provider.status: 1
failure_reason:  api-error
classification:  authentication_failed
explanation:     Failed to authenticate: OAuth session expired and could not be refreshed
```

That is the provider's **own supported non-secret diagnostic**
(`baton.provider-diagnostic/1`), for this exact attempt, carried in the
candidate's `result.json`. The campaign `FINDING.md` warns *"do not infer
authentication failure from unrelated provider checks"* — this is the opposite
of that: it is an attributed diagnostic from the attempt itself, not an
inference from something else.

**Nothing was lost.** The review line's checkout is **clean** — a porcelain
status reports nothing — so no file was written, `change.patch` is **zero
bytes**, `changed_paths` is empty, and the candidate's refusal is correct rather
than a loss. `recovery-341360/` remains exactly as valid for the next run as it
was for this one.

**Nothing was learned about the slice.** `verification.txt` reads *"no
verification was attempted"*. The five-module focused gate has **still never
been executed in any of the four runs**, and the 600/720/180 cutoffs were never
reached or tested — the turn never began.

### The limitation in my own preflight, stated plainly

My preflight passed with zero denials seconds before this failure, and it was
not wrong — it checked what it said it checked. But it checks the credential
**structurally**: that the registry names the reference and that the backing file
exists. It deliberately **reads no credential value**, which I have presented as
a feature in four packets — and that is exactly why it **cannot** see that the
OAuth session behind the reference has expired.

A structure check cannot detect an expired session. Only *using* the credential
can, and whether a preflight should do that is the owner's call and not mine to
take. I am recording the gap rather than quietly widening the preflight.

### The operational blocker, reported and not worked around

**The provider credential for reference `w202663-development` (slot `claude`,
provider `operator-file`, backing `/home/sl/.claude/.credentials.json`) has an
expired OAuth session that could not be refreshed.** Until it is refreshed, any
selected run will fail the same way in about ten seconds.

I have not refreshed it, read it, substituted another reference, retried, or
touched the registry. Per standing policy a denial is reported and the turn
stops — and this is a denial, just at the provider rather than at the engine.

**The invocation owner reroute342358 selected is consumed**, and it was consumed
by this failure rather than by work. That matters for the next selection: the
packet, the recovery input and the cutoffs are all still exactly as accepted and
need no further preparation — what is needed is a working credential and one
more invocation.

### One mistake of mine this claim, caught and corrected

My evidence-indexing script ran with the working directory still inside
`execution-341637/`, so it created `execution-341637/evidence/run-341637/` —
**ten unsealed files inside a sealed, independently accepted packet.** The seal
check did not catch it, and would not: `sha256sum -c` verifies the files the
manifest lists and says nothing about files it does not.

Found by my own integrity check failing to locate
`evidence/run-341637/INDEX.json` where it belonged. Corrected: the directory is
moved to the dossier's `evidence/`, and I then verified the packet **both
ways** — every sealed member present and verifying (48 of 48, zero failures)
**and no extra file present**, by comparing the directory against
`PACKET-INPUTS.json` as a set. That second check is the one that was missing
from my habits, and it is the check that would have caught this immediately.

Nothing in the packet's bytes changed; the manifest
`1f191e7b2f0f0ac033550a3fb235ec48624171d714c0cfb02e47124dcea3e3df` still
verifies and is still the accepted one.

### Cost

Measured subtotal **about 12.1s** — input check 0.118s, stage 0.125s, bootstrap
0.609s, bind 0.408s, preflight 0.337s, the run 10.51s, collection 0.05s, with
evidence copying and indexing a few seconds unmeasured. **Plus unknown
discarded-pass costs.**

Child cumulative: **a measured subtotal of about 969s plus unknowns** — 3.3s
(claim341360) + 951s (claim341471) + 3.5s (claim341637) + 12.1s here. The
parent's ≈2253s stays with the parent. Campaign totals, kept separate: provider
served ≈**2690s** (869.45 + 904.78 + 905.18 + 10.56), controller elapsed
≈**2777s**. **Product tests executed by me: 0.** Jobs 1; attempts 1; runtimes 1;
provider calls 1 (failed to authenticate); credential values read 0;
version-control mutations 0.

### Handoff

Returned to `baton.bug` — **incomplete**, with no candidate and no gate
measurement, for an environmental reason outside this slice. Remaining scope is
unchanged and the preparation is unchanged: measure the gate, fix what it
demonstrates, return inside the cutoffs. The blocker to clear first is the
expired provider session.

## 2026-10-21 — baton.claude, claim345039 — FRESH IDENTITY/ROOT BINDING ONLY

Claimed W341357 at snapshot345039 after reading current canonical state
(queued, unclaimed, routed `baton.impl`), the complete handoff through
`work-events` (22 events, no pagination remaining) and thread T341357 (1
message, no pagination remaining). Bound dossier revalidated against the live
tree before editing: `FINDING.md` and `PLAN.md` as they stand now, not as the
previous packet snapshotted them.

**Scope of this turn, read off reroute345036 and review-2026-10-20T21-46-50Z:**
prepare **only** the necessary fresh run identity and root binding, retaining
the accepted `execution-341637` task and recovery bytes and every selected
limit, and preserving the failed root. Nothing else. No new live invocation, no
retry of the consumed selection342358, no rerun of `COMMANDS.md` over the old
root, no second `bind` over it, no preparation campaign, no host product test,
no credential read, no version-control mutation.

**Why a fresh binding is necessary rather than optional.**
`/home/sl/baton-instances/durable-capture-w341357-341637` now EXISTS and holds a
composed packet. `execution-341637`'s `COMMANDS.md` states that root as absent
and to be created by step 1, and `prepare.py` refuses both a reused root
(`root.mkdir(mode=0o700)` without `exist_ok`) and a second `bind` over a root
that already holds `packet/PACKET.json`. So that packet's commands cannot be
run again as written; the reviewer said so and I confirmed it in the code rather
than taking it on the handoff. The remedy is a new identity, not a new design.

What follows is recorded as the turn proceeds.

### What was delivered

`execution-345039`, sealed: **50 payload members, 51 `SHA256SUMS` lines,
`PACKET-INPUTS.json` sha256
`5db5b9bad674f4b9ae3e6141c54d9551ade6644f9c2ebe52694c773db2857e6b`,
`sha256sum -c` zero failures** — and verified **both ways**, which is the habit
the last claim's mistake taught me: every sealed member present and verifying,
**and** no extra file present, by comparing the directory against
`PACKET-INPUTS.json` as a set. 52 files total, no extras, nothing missing.

Proposed run `durable-capture-w341357-345039` at
`/home/sl/baton-instances/durable-capture-w341357-345039`, which **does not
exist**. `start_authorized: false`, `start_selected: false`. **No start
selected and none taken.**

### What changed, and what provably did not

Changed: the run id, the root, the pins and provenance that name them, the
three operator-facing documents that print them, the three measurement records
re-derived from this claim's own bind, the decision snapshots, and the seal.

**Unchanged, and proved from the bound document rather than asserted.** The
composed `PACKET.json` `fixture.files` carries `TASK.md` `5f01bab8…`,
`COMPLETION.md` `c8c5d4dd…`, `RECOVERY.md` `3a7ec1fa…` and all four recovery
inputs at the digests `execution-341637` was accepted with, including the two
the reviewer published independently (`86be4114…`, `fb9f8e77…`).

**And the gate provably did not move.** I re-derived the verification member
digest from this claim's composed `task.json`:
`2f7ed3dca95da498657a0e549e53107679fd7e8cf4503d5022555ba9e642176c` —
**identical** to the pin `execution-341637` was accepted with. The run id and
root travel in the submission and the packet, not in the verification argv, so
this is a demonstration rather than a claim that nothing moved.

### Why the old root cannot be reused — checked in the code, not taken on trust

`prepare.py stage` calls `root.mkdir(mode=0o700)` with no `exist_ok`, and
`bind` refuses outright when `packet/PACKET.json` already exists. Both are
**already probes in the accepted packet** and both still pass:

- `existing-root` → `FileExistsError: [Errno 17] File exists`
- `rebind-over-a-composed-packet` → *"this root already holds a composed
  packet; composing a second one over it would replace the documents an owner
  may already have read"*

So I wrote **no new probe** for this rebinding. It introduces no new refusal,
and adding a redundant one would have made the probe count look like new
coverage.

### Preparation evidence, zero product tests

- **Input check** 0.12s exit 0 — 114 manager files, 3 supervisor, 2 preparation
  inputs, **41** task inputs, **31** decision snapshots, 4 checkout documents,
  1 pinned controller, 1 pinned shutdown helper, **4** pinned recovery inputs,
  1 gate module owed, and **no decision-source drift**. Re-run after every edit:
  0.10s, still clean.
- **Preparation exercised once** into `/tmp/w341357-preflight3` — stage 0.12s,
  bootstrap 0.63s, bind 0.37s, **≈1.12s, all status 0**. Authority uuid
  `cf412fd6c08b44ff94ac7608d430da86`, composed packet
  `5b9bc4d7aba16075be3ea0b10440883e8b60490749f4aae357493f1a3d1682dd`, **41
  `fixture.files` re-pinned**, `PREPARED.json` `state prepared-not-executed` /
  `work W341357` / `start_selected false`, read back from the bound documents.
  Composed `run_id durable-capture-w341357-345039`, `work W341357`,
  `claim 345039`.
- **Fifty-five probes, all behaving as intended, 2.236s.** Carried
  **unchanged** — and `probe.py` derives the run id from `prepare.py` by regex,
  so it followed the rebinding **without being edited**, which is itself a
  consistency check on the rebinding.
- **Generated limits agree**, re-read from this claim's composed documents:
  provider 3600, verification 30, one invocation, no retry, `report-and-hold`,
  4800 total, 60 cleanup, 1110 residual.
- **The composer is still unchanged** at `09fbf3c5…` with line 721 still
  composing the unenforced `baseline.py` start, and
  `worker_manager/tokens.py:37` still reads `LIFETIME_SECONDS = 900`. Both
  re-measured, read-only.
- **Preserved and re-verified**: `execution-341637` 48 of 48 zero failures,
  `execution-341360` 43 of 43 zero failures, evidence `run-341360` 14 of 14 and
  `run-341637` 10 of 10. **No instance root was read, written, re-run,
  recovered or re-bound** — the `run-341637` decision snapshot was taken from
  the dossier's read-only evidence copy, not from the instance.
- **No controller-boundary preflight was run.** That belongs to the
  selected-run turn, and this claim is preparation. Saying so beats implying
  availability I did not check.
- **The gate was not executed.** There is no product-test authority for this
  author; measuring it is step 2 inside the isolated run, and it has now gone
  **four runs** without ever being measured.

### Stale prose in the packet a reviewer accepted — mine, and now corrected

The seal and the pins in `execution-341637` were right. Its **prose** was not
refreshed with them, and I did not notice when I sealed it. `sha256sum -c`
cannot catch this: it verifies that the listed files are what the manifest says,
never that what they say is true.

- **`PACKET.md` described `execution-340352`**, two packets back — a retained
  candidate `433692c5`, a `CONTINUATION.md` that packet did not carry, "24
  decision snapshots", "31 task inputs", "two gate modules owed", and both
  "forty-one" and "fifty-two" probe counts in the same document.
- **`OPERATOR.md`** carried the same stale counts, a three-run table and a
  supersedes list ending at `execution-340016`.
- **`PROVENANCE.json` `what_changed`** described `execution-340352` throughout.
- **`LIMITS-CHECK.json`** named claim339628's preflight root in `note` and
  claim340016's in `final_results`.
- **`COMMANDS.md`** pointed at "`TASK.md` item 7" and "item 6" after `TASK.md`
  was restructured into five ordered steps, and gave two evidence copies at
  `../evidence/` when they live in the parent dossier at `../../../evidence/`.
- **`prepare.py`'s unselected-start warning** said *"an earlier packet WAS
  selected and died at startup in 0.506s"*. **Two** packets have been selected
  and neither ran. Its docstring also pointed at `recovery/` when the pins name
  `recovery-341360/`, and called the vehicle "now proven" on two runs it
  described as completed.

All corrected here and declared in `PROVENANCE.json` `stale_prose_corrected`
and `identity_rebinding.changed_only`. **`execution-341637` is preserved
unchanged, stale text included** — it is accepted history and editing it would
rewrite what a reviewer signed. Every one of these was a document an operator
reads *before* selecting a start, and none of them changed a byte that would be
built, which is precisely why the seal did not and could not catch them.

### What I did not do

No launch, no retry of consumed selection342358, no re-run of
`execution-341637`'s commands, no second bind over its root, no recovery or
mutation of any instance, no host product test, no product source edit, no
deployment, no credential read, no provider probe, no repeat of the owner's
`providers-check`, no widening of the structural preflight into a live probe,
and no version-control mutation of any kind.

The owner-reported repair is recorded as **owner-reported**: it clears the
prerequisite the review named and establishes nothing about whether a
subsequent attempt will authenticate, how long the session stays valid, or any
producer behaviour.

### Cost

Measured subtotal **about 3.6s** this claim — input check 0.12 + 0.10, stage
0.12, bootstrap 0.63, bind 0.37, probes 2.236, seal and both-ways check ≈0.1 —
**plus an unknown discarded-pass cost**: one stage was exercised before I
corrected `prepare.py`'s operator-facing warning and docstring, and is not
counted.

Child cumulative: **a measured subtotal of about 973s plus unknowns** — 3.3s
(claim341360) + 951s (claim341471) + 3.5s (claim341637) + 12.1s (claim342366) +
3.6s here. The parent's ≈2253s stays with the parent. Campaign totals, kept
separate: provider served ≈**2690s**, controller elapsed ≈**2777s**. **Product
tests executed by me: 0.** Jobs 0; attempts 0; runtimes 0; provider calls 0;
engine calls 0; credential values read 0; version-control mutations 0.

### Handoff

Returned to `baton.bug` for independent **preparation** review, then an
applicable exact invocation selection. Nothing here selects or authorizes a
start and no invocation is inferred from the owner's repair report.

Remaining scope is unchanged: the five ordered `TASK.md` steps — apply the
recovery, **measure the focused five-module gate before any design**, fix only
what it demonstrates, stop optional edits at 600s and end by 720s, report only
what the worker can observe — then the actual Job/attempt and a digest-bound
candidate for independent product review, which remains required even if the
gate passes. Parent W333486 stays blocked by341370 and owns ordinary
status/report, the full joined twelve-module gate, the installed-bundle proof
and joined acceptance. W333485 remains independent; this claim touched no
product file at all, so the sibling intersection is empty by construction, and
`intake.py` and `attempts.py` remain the declared overlap for serial
integration.

## 2026-10-21 — baton.claude, claim345209 — THE SELECTED RUN

Claimed W341357 at snapshot345209 after reading current canonical state
(queued, unclaimed, routed `baton.impl`, `last_change_seq 345206`), the complete
handoff through `work-events` (27 events, no pagination remaining) and thread
T341357 (1 message, unchanged, no pagination remaining).

**The selection, read off reroute345206 and `review-2026-10-21T10-13-48Z.md`:**
exactly **one enforced invocation** of run `durable-capture-w341357-345039` at
`/home/sl/baton-instances/durable-capture-w341357-345039`, using
`execution-345039` at manifest
`5db5b9bad674f4b9ae3e6141c54d9551ade6644f9c2ebe52694c773db2857e6b`. Executor-
boundary preflight first; `COMMANDS.md` and the generated
`AUTHORING-COMMAND.json` only, never `commands.json` `start`. Preserve the
reviewed recovery inputs and every old root. 900s lease, 3600s provider, 30s
verifier, 4800s total, 60s cleanup, one invocation, no retry, gate first,
600/720 planning targets. Collect the actual Job/attempt, the final reports and
the candidate for independent review.

### Revalidated before acting

- **Seal** 51 of 51, zero failures; `PACKET-INPUTS.json`
  `5db5b9bad674f4b9ae3e6141c54d9551ade6644f9c2ebe52694c773db2857e6b` — **exactly
  the manifest the owner selected.** Verified both ways: 52 files, no extras,
  nothing missing.
- **Input check** 0.10s, **exit 0**, no refusals — 114 manager files, 3
  supervisor, 2 preparation inputs, 41 task inputs, 31 decision snapshots, 4
  checkout documents, 1 controller, 1 helper, 4 pinned recovery inputs, 1 gate
  module owed.
- **Pins and provenance** still name run `durable-capture-w341357-345039`, base
  `bc925cf5…`, `start_authorized false`, `start_selected false`.
- **The proposed root is absent**, as it was at review.

**DECISION-SOURCE DRIFT, REPORTED AND NOT RESEALED.** The input check reports
`FINDING.md` and `PLAN.md` as drifted against their snapshots: the reviewer
updated both at claim345158 **after** sealing — recording that very
acceptance. This is the reporting-not-refusing design working as intended, and
`review-2026-10-21T10-13-48Z.md` is explicit that no reseal is required for
non-executable narrative. **Resealing would also change the manifest the owner
selected**, so it would break the selection rather than honour it. The turn
reads the immutable snapshots, which carry the accepted scope.

### Preparation and preflight at the selected root

Steps 1 to 3: stage 0.12s, bootstrap 0.61s, bind 0.38s — all status 0,
authority `c072dd8709a54553abf7510a123cda9d`, composed packet
`58b31d8e3ce8106ff7ff5365045736be88c071bc5afdeb78ae7b68ff4afcf3ba`, composed
`run_id durable-capture-w341357-345039` / `work W341357` / `claim 345039`, 41
`fixture.files` re-pinned with `TASK.md` `5f01bab8…`, `COMPLETION.md`
`c8c5d4dd…`, `RECOVERY.md` `3a7ec1fa…` and all four recovery inputs at their
accepted digests. `PREPARED.json`: `prepared-not-executed`,
`start_selected false`. Verification member digest re-derived from the composed
`task.json`: `2f7ed3dc…`, unchanged.

`AUTHORING-COMMAND.json` checked against `COMMANDS.md` step 4 before starting,
as that document instructs — **they agree exactly**, same argv, same working
directory, same three environment assignments, controller `d12769df…`, helper
`af9e5ea6…`.

**Executor-boundary preflight** 0.332s, child status 0, **`verdict: available`,
zero denials**: engine reachable from the controller boundary, image available
and **digest-equal to the pin**, credential reference present in the registry
with its backing file present, **no credential value read**.

**A mistake of mine inside that preflight, caught before it could mislead
anyone.** The previous claims' copy of this program was gone from `/tmp`, so I
rewrote it — and my first revision read `bounded_engine`'s result as a
`CompletedProcess` and took `.returncode`. It returns
`single_worker._engine_run`'s **mapping** (`single_worker.py:564-569`). Both
probes raised `AttributeError`, and the program reported
**`verdict: denied` — "the engine is not reachable", "the pinned worker image
is not available"**. Both statements were false and both were my bug. I found it
by reading the per-probe `error` field rather than believing the verdict, fixed
the wrapper against the producer, and re-ran. **A denial is supposed to stop the
turn; a fabricated denial would have stopped it for nothing**, and the standing
lesson in this campaign — read the producer, do not assume the shape — caught
its own author again.

### THE RUN: launched 10:21:42Z, AND IT ENDED ON ITS OWN AT 461 SECONDS

One invocation from `packet/AUTHORING-COMMAND.json`, detached, no retry. Worker
container up within ~14 seconds.

| fact | value |
| --- | --- |
| served | **461.10s against a 900-second lease** |
| ended | **on its own** — `provider.status 0`, `failure_reason null`, no signal, no interruption |
| lease token | `returned: true`, `expired: false`, `renewals: 0`, acquired 10:21:47Z, would have expired 10:36:47Z |
| controller | `state: held`, `faults: []`, `child_status: 1`, elapsed **460.89s** |
| workload | `state: held`, `stopped: exceptional`, 0 cleanup sweeps, `outstanding_cleanup: []` |
| attempt | `unable` at the worker, **`verification-failed`** at the adapter; no published proposal |
| **candidate** | **RETAINED AND VALID** — head `370a0aebd6a4…`, base `bc925cf5…`, 214423 bytes, `sha256:1599471c…`, transport `objects.bundle`, `acceptance: unobserved` |
| cleanup | runtime `destroyed`, then `absent` — *"the engine answered that this exact identity does not exist"* |

**The 600/720/180 cutoffs were met without being tested.** The turn returned at
461s — 259s inside the 720s target and 439s of lease margin. This is the first
run of this slice that reached the supported completion mechanism at all.

### THE GATE HAS BEEN MEASURED. FOR THE FIRST TIME IN THIS CAMPAIGN.

Four runs have gone by without this ever happening. The retained attempt stream
carries it:

```
Ran 864 tests in 12.817s
FAILED (failures=9, errors=7)
```

**The 30-second ceiling fits, with room.** That standing open question —
unproved across every packet since revision 2 — is answered: 12.817s of
unittest time against a ceiling of 30. The qualifier is real and I am stating
it rather than burying it: unittest's self-reported seconds are **not** the
adapter's wall clock, and **the gate still exited 1**, so nothing here is
acceptance.

**All 16 failing cases are in `tests.manager.test_maintenance`. The other four
gate modules contributed none** — including `tests.manager.test_attempt_failure_cause`,
the new producer module the recovery brings, whose 63 cases are the whole point
of the slice.

And the strongest fact in the collection, because it is mechanical rather than
interpretive: **every traceback frame is in `tests/manager/test_maintenance.py`
(21 frames) or `src/baton_v12/worker_manager/workspaces.py` (15 frames). Not one
frame touches any path this candidate changed.** The changed paths are
`attempts.py`, `documents.py`, `failure_cause.py`, `intake.py` and
`test_attempt_failure_cause.py`; `grep` for all four source files across the
whole stream returns **zero**.

The visible failures compare sandbox filesystem paths
(`/tmp/dogfood-…/verification-ephemera/…` against `/proc/self/fd/6/…`) and the
errors are `ContractRefusal` raised by `workspaces.py` — *"the writable line is
its own directory in the reserved manager namespace"*. That is **layout-shaped,
not producer-shaped.**

**What this does NOT establish, and I will not claim it does.** No base
measurement of this argv exists in any run, so "pre-existing" is a hypothesis.
I did not run the gate on the host to settle it — `decisions/review-340349.md`
and `COMMANDS.md` are explicit that the host-side rerun is not authorized, and
the previous invocation is consumed. And I cannot rule out that `documents.py`
or `intake.py` is implicated by some path that leaves no traceback frame.

### The preparation concern this raises, and it is mine

`tests.manager.test_maintenance` is in the sealed five-module argv **because I
put it there.** This is the first evidence that it may not be able to pass
inside the worker verification sandbox at all — and if that is so, **this gate
can never go green there**, which makes it a defect in my preparation rather
than in the producer work.

I have not changed the gate, narrowed it, dropped the module or re-run it.
Weakening a gate to obtain a pass is exactly what `TASK.md` forbids, the
measurement that would settle it is not mine to take, and this is the reviewer's
and the owner's call. It is recorded in
`evidence/run-345039/GATE-CLASSIFICATION.json` under
`THE_PREPARATION_CONCERN_THIS_RAISES`.

### What the candidate did with the recovery

It applied the recovery and then moved: `failure_cause.py` 1208 → **1236**
lines, `test_attempt_failure_cause.py` 1374 → **1407** lines, 62 → **63** test
cases. Five changed paths, exactly the recovery set. No gate module was deleted,
narrowed or relaxed. **All of it is unaccepted**: the gate exited 1, the
disposition is `verification-failed`, and `acceptance` reads `unobserved`.

### Post-run collection — step 5, which is mine and not the worker's

`collect.py` exit 0 in 0.01s: **five of six artifacts present** — workload,
controller, manager snapshot, shutdown progress, authoring log — and every
correlatable one **matched** on the fields it actually publishes
(`original_envelope.run/job/authority`, `envelope.run`, `run_id`/`job_id`,
`run_id`/`job_id`/`work`/`claim`). The sixth, `shutdown_request`, is **absent**,
which is correct: nothing requested a shutdown because nothing interrupted the
run. All four links `found`. No `isolated_failures`, no `unclassified_entries`,
no own temporaries. `publication_timeout.established: false`, with zero parsed
faults, zero other timeouts and zero uncorrelated timeouts — and per
`producer_persistence` that remains **uninformative in either direction**, not a
statement that no timeout happened.

### Evidence, and one deliberate omission

`evidence/run-345039/` — **15 files, 14 indexed copies, every copy verified
against its live source after writing, mode 0444**, with `INDEX.json`. It
carries the four published manager artifacts, the authoring log, the candidate's
`result.json`, `verification.txt`, `change.patch`, `objects.bundle`, completion
manifest and custody seal, my collection report and the boundary preflight.

**I did NOT copy the raw verification stream into the dossier.** It is the
gate's own output from a tree the provider edited with the attempt's credential
mount readable, and the proposal's own `verification.txt` refuses to reproduce
it for exactly that reason — *"nothing here can tell one of its bytes from
another without reading the bearer."* A grep is not a proof of absence. So
`GATE-CLASSIFICATION.json` carries the derivation — counts, the 16 case
identities, the traceback file inventory — plus the raw stream's **locator and
sha256** so a reviewer can bind and read the original in place through the
supported reader. My scan for credential-shaped content found two matches, both
the *name* of the test case `test_the_home_and_its_credential_siblings_are_not_mounted`;
that is reported as a scan, not as a proof.

The supported retained-evidence reader was exercised as `TASK.md`'s locator
obligation requires: `baton-v12-stack logs --logs <launch-home>/logs --attempt
<attempt-id> locators` — six native session entries `captured`, four declared
streams `captured`, two worker streams `absent` with *"no log was created for
this stream"*.

### Preserved

The packet seal re-verified **51 of 51, zero failures, 52 files, no extras** —
nothing was written inside it this claim. `execution-341637` 48 of 48 and
`execution-341360` 43 of 43, zero failures. Evidence `run-341360` 14 of 14 and
`run-341637` 10 of 10. The five earlier instance roots untouched: no rerun, no
recovery, no second bind, no reuse. This run's own runtime is destroyed and the
controller process has exited.

### Cost

Measured subtotal **about 465s** this claim — input check 0.10s, stage 0.12s,
bootstrap 0.61s, bind 0.38s, boundary preflight 0.332s, **the run 460.89s
controller elapsed / 461.10s provider served**, collection 0.01s, with evidence
copying and indexing a few seconds unmeasured — **plus an unknown
discarded-pass cost** for the first boundary-preflight revision that failed on
the engine-runner shape.

Child cumulative: **a measured subtotal of about 1438s plus unknowns** — 3.3s
(claim341360) + 951s (claim341471) + 3.5s (claim341637) + 12.1s (claim342366) +
3.6s (claim345039) + 465s here. The parent's ≈2253s stays with the parent.
Campaign totals, kept separate: provider served ≈**3151s** (869.45 + 904.78 +
905.18 + 10.56 + 461.10), controller elapsed ≈**3238s**. **Gate measurements:
1 — this one.** **Product tests executed by me on the host: 0.** Jobs 1;
attempts 1; runtimes 1; provider calls 1 which **succeeded**; engine calls 2
read-only in the preflight plus the run's own; credential values read 0;
version-control mutations 0.

### Handoff

Passed to `baton.bug` for independent review of an **actual candidate and an
actual gate measurement** — the first time this slice has had either. Not
acceptance: the gate exited 1 and `acceptance` reads `unobserved`.

Remaining scope: the reviewer's independent read of the retained candidate and
of the gate classification, and then the disposition of the
`test_maintenance` question — whether those 16 cases are pre-existing in that
environment, and whether the sealed argv I composed is wrong to include the
module. Whatever that answer is, `TASK.md` step 3's instruction stands: fix only
demonstrated failures, and buy no pass by weakening a gate. Parent W333486
remains blocked by341370 and owns ordinary status/report, the full joined
twelve-module gate, the installed-bundle proof and joined acceptance. W333485
remains independent; the candidate touches no `job_manager` file, so the sibling
intersection is empirically empty, and `intake.py` and `attempts.py` remain the
declared overlap for serial integration and actual byte review.

## 2026-10-21 — baton.claude, claim345388 — VERIFICATION-FIXTURE CORRECTION PREPARATION

Claimed W341357 at snapshot345388 after reading current canonical state
(queued, unclaimed, routed `baton.impl`, `last_change_seq 345385`), the complete
handoff through `work-events` (31 events, no pagination remaining) and thread
T341357 (1 message, unchanged, no pagination remaining). Read
`review-2026-10-21T10-42-55Z.md`, and the bound `FINDING.md` and `PLAN.md` as
they stand now.

**Scope, read off pass345385 and the review:** prepare **one finite fresh
isolated execution** from the **exact retained candidate**, whose task is to
make the complete existing five-module gate usable under the actual verification
environment. Preserve the full gate, every case and assertion, the verifier's
pinned-root security boundary and the production path/custody refusals. **Do not
drop `test_maintenance`.** I choose the files and the mechanism; standing test
authority covers the necessary fixture corrections with a path and ownership
record, and no new per-test owner gate is required. Preparation only: owner
selection345206 is consumed, so **no launch, no retry, no rebind of
`execution-345039`**, no host product test, no live provider probe, no
credential read, no version-control mutation.

### The diagnosis revalidated against the current tree, not restated

The review gives locations; I checked each one rather than carrying the
assertion.

- **`tests/manager/test_maintenance.py:135-137`** — `setUp` does
  `root = tempfile.TemporaryDirectory(prefix="v12-maintenance-")` and stores
  `self.root = root.name`, i.e. **whatever spelling `tempfile` returns**. Every
  derived path (`self.storage`, `self.home`, `self.workspace`, `self.result`) is
  built from it.
- **`v12/worker/claude_agent.py:3262-3301`** — `_pinned_environment` opens each
  verifier root *before* the provider runs and exports it as
  `/proc/self/fd/<n>`, deliberately, so that replacing a scratch pathname
  cannot redirect an already-open object. `TMPDIR` is one of
  `EPHEMERA_ROOTS` (line 3129). So under the verifier, `tempfile` returns a
  path **below a `/proc/self/fd/<n>` alias**.
- **`worker_manager/workspaces.py:6221-6228`** — `_composed_line_roots`
  requires `os.path.realpath(place) == place` and refuses otherwise with
  *"the writable line is its own directory in the reserved manager
  namespace"*. A `/proc`-aliased fixture place can never satisfy it. **That is
  a production security check and it is correct.**
- **`tests/manager/test_maintenance.py:249-252`** — `executed` runs
  `subprocess.run([...], capture_output=True, timeout=120)` and returns
  **`done.stdout` only**. `returncode` and `stderr` are discarded, so a child
  that cannot resolve a parent-descriptor path yields empty output, and the
  caller's indexing turns that into an `IndexError` at lines 331 and 821 —
  which is the reviewer's inference and matches the code.

So the conflict is real and it is in the **fixture**, not the product: the
fixture stores and hands on a non-canonical root, and it hides the child's
failure instead of reporting it.

### My reasoning about why canonicalising the fixture root is not a weakening

Stated here as **my argument to be revalidated inside the run**, not as an
established fact. The verifier's check/use protection is about the roots it
**opened before the provider ran**; its authority is the held descriptors and
`_revalidated_directories` re-checks them. A path a test creates *inside* those
roots during verification is the fixture's own derived object, and resolving it
to its canonical spelling does not give the provider a name to swap — the
descriptors are still the verifier's authority. The production
`realpath(place) == place` refusal stays untouched and still must be exercised.
`TASK.md` carries this as reasoning the turn must confirm, and carries the
explicit prohibition on relaxing either check to obtain a pass.

### What was delivered

`execution-345388`, sealed: **56 payload members, 57 `SHA256SUMS` lines,
`PACKET-INPUTS.json` sha256
`b895cc72c8458c7988a6c9182ab964ba5450a31dcc39c1af79eb48e3dc8b204d`,
`sha256sum -c` zero failures** — verified **both ways**: 58 files, no extras,
nothing missing. Proposed run `durable-capture-w341357-345388` at an **absent**
root. `start_authorized: false`, `start_selected: false`. **No start selected
and none taken.**

### The input is a real candidate, for the first time in this campaign

`recovery-345039/` holds the **exact retained candidate** `run345039` returned,
copied verbatim: `candidate.patch` `f9e68939…`, 168606 bytes, 5 sections. The
copy was verified against its source **and** against the digest the reviewer
published independently, and the patch's sections were checked to name exactly
the five changed paths the candidate's own result document names.

`recovery-341360` — a producer split out of an unfrozen working tree that had
never been executed — is superseded **as input**. It stays in place as history
and its pins are dropped from this packet rather than edited.

The candidate is held against **four independent records**: the pinned bytes,
the recovery index, the reviewer's three published digests (patch, transport,
content), and **the run's own retained evidence index** — a separate immutable
record of head, base and content digest. The cross-checks in both programs are
retargeted at `baton.w341357-recovery/3` to do it.

**The transport bundle is recorded by digest and locator and is deliberately not
a task input.** This campaign creates no version-control object on this host;
`PROVENANCE.checkpoint.paths` stays empty and `prepare.py` still refuses a
declared restored buffer, so that refusal keeps its meaning. Both programs
**refuse** if the bundle appears among the task inputs, and a probe demonstrates
it.

### What the task asks for

`TASK.md` is restructured into six ordered steps. The one I care most about is
step 1, because it is the measurement nobody has: **compare unchanged base
against the retained candidate for `test_maintenance`, under the same
pinned-root conditions.** That decides whether the 16 failures are pre-existing
in that environment or something the candidate caused, and I have deliberately
not let the packet assume the answer. The second half of step 1 is to **confirm
the subprocess diagnosis dynamically** rather than inherit it as an inference.

Step 2 is the correction, with five things it must leave standing: every module,
case and assertion; the verifier's pinned-descriptor boundary; the production
path and custody refusals; **both** path shapes exercised; and child-process
access with child failures surfacing as child failures. Two cases get named
explicitly —
`test_a_REPLACED_LINE_object_is_refused_by_the_COMPOSED_boundary` and
`test_a_REPLACED_inputs_root_under_the_LINE_layout_still_refuses` — because
they are the **replacement refusals**, and a change that makes them pass by
never reaching the refusal has broken them rather than repaired them.

Step 3 is the complete gate with no skips. Step 4 says the producer obligations
stay owed and **out of scope** unless this turn's gate demonstrates a defect —
the reviewer was explicit that the retained candidate must not be discarded and
the authoring reopened.

`FIXTURE.md` is new and is a **pinned task input**, with `prepare.py` and
`verify-inputs.py` refusing if it is absent or unpinned — the same structural
rule review341628 required for `COMPLETION.md`, applied to the document that
defines this turn. It carries the measurement, the four citations, all 16 case
identities with their classes, and the five constraints.

### Proved, not asserted

- **The gate did not move.** The verification member digest re-derived from this
  claim's composed `task.json` is
  `2f7ed3dca95da498657a0e549e53107679fd7e8cf4503d5022555ba9e642176c` —
  identical to the one every accepted packet since claim339421 carried.
- **The candidate travels at the reviewer's digest.** The composed
  `PACKET.json` `fixture.files` carries `candidate.patch` at `f9e68939…`, and
  **no `objects.bundle` appears anywhere in the fixtures.**
- **`COMPLETION.md` travels verbatim** at `c8c5d4dd…`, with `ENFORCEMENT.md`,
  `SHUTDOWN.md`, `FAILURE.md` and `collect.py` byte-identical.
- **Every limit is unchanged** and re-derived from this claim's composed
  documents: 3600 provider, 30 verification, one invocation, no retry,
  `report-and-hold`, 4800 total, 60 cleanup, 1110 residual.

### Preparation evidence, zero product tests

- **Input check** 0.12s exit 0 — 114 manager files, 3 supervisor, 2 preparation
  inputs, **45** task inputs, **36** decision snapshots, 4 checkout documents,
  1 controller, 1 helper, **2** pinned recovery inputs, 1 gate module owed, and
  **no decision-source drift** after re-taking `FINDING.md` and `PLAN.md`.
- **Preparation exercised once** into `/tmp/w341357-preflight4` — stage 0.12s,
  bootstrap 0.59s, bind 0.36s, **≈1.07s all status 0**. Authority
  `ef1c08aca5844a0eabdd0ba080650988`, composed packet
  `85e1314bcbe2570e103cc6b8b9b5db729ea5b1eade434198368325daaef22997`, composed
  `run_id durable-capture-w341357-345388` / `work W341357` / `claim 345388`,
  **45 `fixture.files`** re-pinned, `PREPARED.json` `prepared-not-executed` /
  `start_selected false` — all read back from the bound documents.
- **Sixty-one probes, all behaving as intended, 2.525s.** **Ten are new**, one
  per refusal this packet introduces, because a check nobody has seen fire is a
  claim rather than a guard: a drifted candidate patch, a drifted recovery
  index, a candidate that is not a task input, a candidate disagreeing with the
  reviewer's published digest, a drifted transport bundle, **the transport
  pinned as a task input** (refused by design), an index naming another head,
  an index naming another content, an index of another schema, and an absent or
  unpinned `FIXTURE.md`. Three were retargeted; the 23 collection cases are
  carried unchanged.
- **Decision snapshots 31 → 36.** Five new: `review-345368` (the review that is
  the authority for this turn), its evidence record, `run-345039-INDEX`,
  `run-345039-GATE-CLASSIFICATION` and `recovery-345039-INDEX`.
- **Preserved and re-verified**: `execution-345039` 51 of 51,
  `execution-341637` 48 of 48, `execution-341360` 43 of 43, all zero failures;
  evidence `run-345039` 14 of 14, `run-341637` 10 of 10, `run-341360` 14 of 14.
  **No instance root was read, written, re-run, recovered or re-bound** — the
  candidate came from the dossier's read-only evidence copies taken at
  claim345209.
- **No boundary preflight was run.** That belongs to the selected-run turn.
- **No product test was executed.**

### Two probes refuse earlier than I predicted, and I am recording that

`drifted-candidate-transport-bundle` and `run-evidence-names-another-candidate`
both trip the index-versus-pins comparison **first**, so neither exercises the
check it is named for — the bundle byte check and the run-evidence comparison
are downstream and stay unreached in those two probes. The checks are layered
and the earliest one wins. Recorded in `PREFLIGHT.json` as they behaved, because
claiming coverage a probe did not provide is precisely the habit this campaign
keeps catching in me.

### One disclosure retired, honestly

Every packet for this Work has carried *"no authoring invocation has ever
completed."* **That is no longer true** — run345039 completed on its own at
461.10s with `provider.status 0`. `LIMITS-CHECK.json` withdraws the sentence as
written and keeps what is still true: **no invocation has ever produced an
accepted candidate**, and two selected packets never ran at all. The
*"gate still unmeasured"* disclosure is likewise retired and replaced with what
*is* still unmeasured — the base comparison.

### Cost

Measured subtotal **about 3.7s** this claim — input check 0.12, stage 0.12,
bootstrap 0.59, bind 0.36, probes 2.525, seal and both-ways check ≈0.1 — **plus
an unknown discarded-pass cost**: one input check refused because `TASK.md` did
not yet name the owed gate module by its full path, and one probe run refused
because `PROVENANCE.json` still named the previous run. Neither is counted.

Child cumulative: **a measured subtotal of about 1442s plus unknowns** — 3.3s
(claim341360) + 951s (claim341471) + 3.5s (claim341637) + 12.1s (claim342366) +
3.6s (claim345039) + 465s (claim345209) + 3.7s here. The parent's ≈2253s stays
with the parent. Campaign totals, kept separate: provider served ≈**3151s**,
controller elapsed ≈**3238s**. **Gate measurements: 1.** **Product tests
executed by me on the host: 0.** Jobs 0; attempts 0; runtimes 0; provider calls
0; engine calls 0; credential values read 0; version-control mutations 0.

### Handoff

Returned to `baton.bug` for independent **preparation** review, then an
applicable exact invocation selection. Nothing here selects or authorizes a
start; owner selection345206 is consumed, and `execution-345039` is neither
re-run nor re-bound.

Remaining scope: the fixture correction and a complete gate inside a selected
isolated execution, with the base-versus-candidate comparison first; then
independent producer byte review and acceptance of whatever candidate survives.
Parent W333486 stays blocked by341370 and owns ordinary status/report, the full
joined twelve-module gate, the installed-bundle proof and joined acceptance.
W333485 remains independent; the candidate touches no `job_manager` file, so the
sibling intersection is empirically empty, and `intake.py` and `attempts.py`
remain the declared overlap for serial integration.

## 2026-10-21 — baton.claude, claim345571 — THE SELECTED FIXTURE-CORRECTION RUN

Claimed W341357 at snapshot345571 after reading current canonical state
(queued, unclaimed, routed `baton.impl`, `last_change_seq 345560`), the complete
handoff through `work-events` (36 events, no pagination remaining) and thread
T341357 **through its new second message** (2 messages, `last_seq 345516`, no
pagination remaining). Read `review-2026-10-21T11-01-38Z.md`, `FINDING.md` and
`PLAN.md` as they stand now.

**The selection, read off reroute345560:** exactly **one enforced invocation** of
`durable-capture-w341357-345388` at
`/home/sl/baton-instances/durable-capture-w341357-345388`, using
`execution-345388` at manifest
`b895cc72c8458c7988a6c9182ab964ba5450a31dcc39c1af79eb48e3dc8b204d`.
Executor-boundary preflight first; `AUTHORING-COMMAND.json` only. Preserve the
pinned candidate and base and the overlap coordination from M345516. Limits
unchanged.

### Revalidated before acting

- **Seal** 57 of 57, zero failures; manifest
  `b895cc72c8458c7988a6c9182ab964ba5450a31dcc39c1af79eb48e3dc8b204d` — **exactly
  what the owner selected.** Both ways: 58 files, no extras, nothing missing.
- **Input check** 0.11s, **exit 0**, no refusals — 114 manager files, 3
  supervisor, 2 preparation inputs, 45 task inputs, 36 decision snapshots, 4
  checkout documents, 1 controller, 1 helper, 2 pinned recovery inputs, 1 gate
  module owed.
- **The proposed root is absent**, as it was at review.

**DECISION-SOURCE DRIFT, REPORTED AND NOT RESEALED** — the same situation as the
last selected run. `FINDING.md` and `PLAN.md` drifted because the reviewer
updated both at claim345501 *after* sealing, recording that very acceptance.
Reporting rather than refusing is the design, and **resealing would change the
manifest the owner selected**, so it would break the selection rather than
honour it. The turn reads the immutable snapshots.

### The declared integration overlap, M345516 — checked, reported, not rebased

Owner M345512 selected a human-plus-agent 17-path main-tree import of W339626's
candidate345109, which `prompt` owns. The declared intersection with this work
is `v12/python/src/baton_v12/worker_manager/attempts.py` plus the shared input
`tools/authoring_enforcement.py`.

What I found, read rather than assumed:

- **neither overlap path has an uncommitted working-tree change** — a porcelain
  status for both paths reports nothing, so the import has not landed as
  uncommitted edits;
- **both differ between my pinned base and the current HEAD** (`d3a7a41c`):
  `attempts.py` `726197972a9b2558…` at base against `5c3cf84641bcbef5…` in the
  tree, and `authoring_enforcement.py` `d12769df…` (the pinned controller)
  against `ac3640fe020fb691…`. Those differences are **committed**, and
  `d3a7a41c` was already HEAD before this notice;
- **the packet is unaffected, by construction.** `prepare.py` stages every
  manager file with `git show <base>:…` and verifies each against its pin, and
  the input check confirms all 114 match `bc925cf5`. The vehicle's own
  `verify_controller` then resolves the controller inside the *staged* source.
  The host's HEAD could move again mid-run without changing a staged byte.

**I have not rebased, re-pinned or weakened anything**, and the pinned base
stays `bc925cf5c62d69426ed5862af4d41f4d2a967b0f`. The honest consequence to
record for later integration: this child's candidate and the imported
candidate345109 both touch `attempts.py`, and the current HEAD already carries a
different `authoring_enforcement.py` than the controller this vehicle is proven
on — so the eventual integration is a serial, independently reviewed rebase onto
the integrated bytes, never an overwrite and never a silent conflict
resolution.

### Preparation and preflight at the selected root

Stage 0.12s, bootstrap 0.59s, bind 0.36s — all status 0, authority
`f225e29a55fd4ca3aed8e066ed2c6035`, composed packet
`664c5d10a83ec7e29627c65b4468404618195ea6269825bb9ce23c10dc6790c8`, composed
`run_id durable-capture-w341357-345388` / `work W341357` / `claim 345388`, **45
`fixture.files`** re-pinned with `candidate.patch` at `f9e68939…` — the
reviewer's published digest — `TASK.md` `1246c956…`, `FIXTURE.md` `10725f5b…`,
`COMPLETION.md` verbatim at `c8c5d4dd…`, **and no `objects.bundle` anywhere in
the fixtures.** Verification member digest `2f7ed3dc…`, unchanged.

`AUTHORING-COMMAND.json` checked against `COMMANDS.md` step 4 — they agree
exactly. **Executor-boundary preflight** 0.327s, child status 0,
**`verdict: available`, zero denials**: engine reachable from the controller
boundary, image available and digest-equal to the pin, credential reference and
backing file present, **no credential value read**. The engine-runner mapping
fix from last claim held, so the preflight ran clean on its first revision.

### THE RUN: launched 11:09:39Z, ended on its own at 789 seconds

| fact | value |
| --- | --- |
| served | **789.14s against a 900-second lease** — 110.86s of margin |
| ended | **on its own** — `provider.status 0`, `failure_reason null`, no signal, no interruption |
| lease token | `returned: true`, `expired: false`, `renewals: 0` |
| controller | `state: held`, `faults: []`, `child_status: 1`, elapsed **788.97s** |
| workload | `state: held`, `stopped: exceptional`, 0 cleanup sweeps, `outstanding_cleanup: []` |
| attempt | `unable` at the worker, **`verification-failed`** at the adapter; no published proposal |
| **candidate** | **RETAINED AND VALID** — head `5a7d5976ab48…`, base `bc925cf5…`, 223394 bytes, `sha256:5c0fca78…`, `acceptance: unobserved` |
| cleanup | runtime `destroyed`, then `absent` |

**It overran the 720-second planning target by 69 seconds** while staying inside
the lease. Worth saying plainly rather than rounding away: the cutoff was a
planning target and it was missed, and the run still returned through the
supported mechanism because the lease was not the binding constraint.

### THE GATE MOVED, AND THE FAILURE CLASS CHANGED COMPLETELY

```
Ran 864 tests in 12.515s
FAILED (errors=16)
```

Against last run's `864 tests in 12.817s / FAILED (failures=9, errors=7)`:

- **failures 9 → 0.** Every path-comparison assertion and every line-layout
  refusal that failed last run now passes. **The fixture correction worked for
  the class it targeted.**
- **the test count is identical at 864, with zero skips.** That is the
  mechanical check that no module, case or assertion was dropped, narrowed or
  deleted — which is precisely what `TASK.md` step 2 forbade.
- **the ceiling still fits**: 12.515s against 30.
- **a different and single cause appeared.** All 16 remaining results are
  `ERROR`, and every one of them is
  **`sqlite3.OperationalError: database or disk is full`**, raised initialising
  or transacting a store. The distribution moved too: **6 in
  `tests.manager.test_intake`, 10 in `tests.manager.test_maintenance`.**

### The mechanism the turn introduced, and what it ran into

The candidate's nine changed paths are the four producer files plus
`tests/manager/test_maintenance.py`, `test_output.py`, `input_roots.py`,
`test_attempt_failure_cause.py` and a **new** helper,
`tests/manager/disk_roots.py`.

`disk_roots.py` answers a **disk-backed** temporary root, because
`source_boundary.compose_source_boundary` refuses a workspace on a memory
filesystem — and the verifier's `TMPDIR` is a `/proc/self/fd` alias over
memory-backed scratch, so the production boundary **correctly** refuses a
workspace there. Its candidate order is an explicit `BATON_V12_DISK_ROOT`
operand first, then `tempfile.gettempdir()`, then the distribution root, then
`/var/tmp`, and it **refuses rather than silently falling back** if a named
variable points at memory-backed or unwritable storage. Its docstring makes the
right argument: a suite that skipped itself on a tmpfs `/tmp` would report green
on a host where the boundary was never exercised.

That is a better answer than the one I suggested, and the diagnosis in
`FIXTURE.md` was incomplete: I framed the conflict as *canonical spelling*, and
the deeper constraint is *memory-backed versus disk-backed*. The turn found it.

**What it ran into is bounded space.** The composed runtime profile bounds
scratch at `tmp_bytes 67108864` and `shm_bytes 16777216` with
`workspace_min_bytes 83886081`, and 864 cases each creating SQLite stores
exhausted whatever root was chosen.

### What this run does NOT establish, and I am not going to claim it does

- **Which filesystem filled.** The retained stream carries no store path and no
  disk-root decision line, so **the chosen root is not named by this evidence.**
  Reporting it is the first thing the next turn owes.
- **Whether the exhaustion is caused by the new disk-backed root or merely
  surfaced by it.** The mechanism is plain; the measurement does not exist.
- **The base-versus-candidate comparison `TASK.md` step 1 asked for.** See
  below — it is not in any host-verifiable artifact.
- Anything about producer acceptance. The gate exited 1.

### A reporting-channel gap, and it is my defect

`TASK.md` step 1 asked the worker for the base-versus-candidate counts and step
6 asked it to report them — **but the task gave it no channel other than the
provider transcript**, and the proposal deliberately carries no transcript. So
those numbers reach nobody.

I scanned the transcript rather than copying or quoting it: 9760 bytes, digest
recorded in the evidence index; it references the gate count (3 occurrences) and
the base (8), and carries **no parseable `failures=` or `errors=` counts at
all**. The comparison is therefore **not established** by anything a reviewer
can read without the transcript.

A future packet must give the turn a **declared output path for its own
report**, or ask for the numbers somewhere the proposal carries. I wrote that
task; the gap is mine.

### Post-run collection — step 5, mine and not the worker's

`collect.py` exit 0 in 0.01s: **five of six artifacts present** and every
correlatable one **matched** on the fields it publishes. `shutdown_request`
**absent**, correctly — nothing interrupted the run. All four links `found`, no
`isolated_failures`, no `unclassified_entries`, no own temporaries.
`publication_timeout.established: false` with zero parsed faults, zero other
timeouts and zero uncorrelated timeouts — which per `producer_persistence`
remains **uninformative in either direction**. `shutdown_progress` step *"final
enforcement publication"* with no faults.

### Evidence, and two deliberate omissions

`evidence/run-345388/` — **15 files, 14 indexed copies, each verified against
its live source after writing, mode 0444**, with `INDEX.json` carrying the
candidate identity, the integration-overlap record and the two omissions.

**Not copied:** the raw verification stream (the gate's own output from a tree
the provider edited with the credential mount readable — the proposal's own
`verification.txt` refuses to reproduce it, and a grep is not a proof of
absence) and **the provider transcript**. Both have their locator and sha256 in
the evidence index so a reviewer can bind and read them in place.

### Preserved

Packet seal re-verified **57 of 57, zero failures, 58 files, no extras** —
nothing was written inside it. Evidence copies 14 of 14 with 13 literal source
pairs. This run's runtime is destroyed and the controller has exited. The six
earlier instance roots are untouched: no rerun, no recovery, no second bind, no
reuse. **The pinned base stays `bc925cf5`** and nothing was rebased or
re-pinned.

### Cost

Measured subtotal **about 791s** this claim — input check 0.11s, stage 0.12s,
bootstrap 0.59s, bind 0.36s, boundary preflight 0.327s, **the run 788.97s
controller elapsed / 789.14s provider served**, collection 0.01s, with evidence
copying and indexing a few seconds unmeasured.

Child cumulative: **a measured subtotal of about 2233s plus unknowns** — 3.3s +
951s + 3.5s + 12.1s + 3.6s + 465s + 3.7s + 791s. The parent's ≈2253s stays with
the parent. Campaign totals, kept separate: provider served ≈**3940s**,
controller elapsed ≈**4027s**. **Gate measurements: 2.** **Product tests
executed by me on the host: 0.** Jobs 1; attempts 1; runtimes 1; provider calls
1 which **succeeded**; engine calls 2 read-only in the preflight plus the run's
own; credential values read 0; version-control mutations 0.

### Handoff

Passed to `baton.bug` for independent review of the **second** candidate and the
**second** gate measurement. Not acceptance: the gate exited 1 and `acceptance`
reads `unobserved`.

Remaining scope: name the filesystem that filled and decide the bounded next
step — the composed `scratch.tmp_bytes`/`workspace_min_bytes` operands, an
explicit `BATON_V12_DISK_ROOT`, or a fixture that does not need 864 durable
stores are three candidate directions and the choice is the reviewer's and the
owner's, not mine to take inside a handoff. Then independent producer byte
review and acceptance. Parent W333486 stays blocked by341370 and owns ordinary
status/report, the full joined twelve-module gate, the installed-bundle proof
and joined acceptance. W333485 remains independent. The M345516 integration
overlap on `attempts.py` and the shared `authoring_enforcement.py` input is
recorded above and in the evidence index, with the pinned base unchanged.

## 2026-10-21 — baton.claude, claim345822 — MINIMAL MEASURED-FIRST CONTINUATION

Claimed W341357 at snapshot345822 after reading current canonical state
(queued, unclaimed, routed `baton.impl`, `last_change_seq 345818`), the complete
handoff through `work-events` (40 events, no pagination remaining) and thread
T341357 in full (**5 messages**, `last_seq 345786`, no pagination remaining —
345649 and 345678 are the two that arrived mid-run last claim and 345786 is my
own read-after-handoff notice). Read `review-2026-10-21T11-37-58Z.md`,
`FINDING.md` and `PLAN.md` as they stand now.

### THREE CORRECTIONS TO MY OWN CLASSIFICATION. ALL THREE ARE MINE AND ALL THREE ARE RIGHT.

I checked each against the base rather than accepting it on the handoff.

**1. `disk_roots.py` was NOT new, and I said it was.** It exists at
`bc925cf5` with sha256
`53dc1fa9b99697c8b6ea0597579ba05135a6a7707f798d15d9a8da2b5dd85c08`, 121 lines —
read straight out of the base. The candidate only **canonicalises its temporary
directory**. I inferred "a NEW fixture helper" from seeing the path in
`changed_paths` and never checked whether the section was a creation or a
modification, which is the same mistake as reading a diff and not its header.
My pass345775 and `GATE-CLASSIFICATION.json` both say "new" and both are
wrong. The error flattered the run: "the turn found the deeper constraint and
built the mechanism" is a better story than "the turn canonicalised a helper
that was already there."

**2. The 16 errors are SUBTEST outcomes in FOUR methods, not 16 independent
test methods.** I reported them as 16 cases and let "864 cases each creating
SQLite stores" stand as the mechanism. There are not 864 concurrent durable
stores; there are four methods that accumulate live stores **within** one
method. That changes the hypothesis from *the suite is too big for the
filesystem* to *four methods hold too much at once* — a far smaller and more
tractable thing, and the reviewer's reading is the useful one.

**3. "The test count is identical at 864" does NOT prove assertion coverage was
preserved**, and I presented it as the mechanical check that nothing was bought
away. It is not: **a test that fails during setup has not proved its later
assertions passed.** So "failures 9 → 0" is progress and not proof that every
earlier affected assertion reached and passed. The reviewer did the work I
should have done — inspected the four fixture diffs and found the displayed
assertions preserved.

The original evidence stays untouched; `GATE-CLASSIFICATION.json` in
`evidence/run-345388/` keeps what it said, and these corrections supersede it.

### Scope, read off pass345818 and the review

Prepare **one MINIMAL fresh continuation** from the exact retained candidate
`5a7d5976…` / `5c0fca78…`, **reusing unchanged machinery and checks**. The
selected run must, in order: reproduce the four-method storage pressure early;
**measure** the actual canonical DB and workspace roots, their backing mount and
available bytes and inodes before, during and after the repeated subcases, and
the per-subcase lifetime; compare pinned base against candidate **in the same
verifier environment**; then correct the demonstrated fixture lifetime/storage
behaviour, preserving every case, assertion and the verifier and product
custody/refusal boundaries; then the complete five-module gate with no skips.

And the part that answers my own reporting-channel finding: the task must name a
**nonsecret durable report carried by the existing candidate/proposal
mechanism** — a `W341357-VERIFICATION.json` written into the candidate tree, so
it travels in `change.patch` and `changed_paths` with no new output protocol and
no transcript-only proof.

Explicitly not selected: a larger scratch limit, a rerouted `TMPDIR`, a host
product test, a retry or rebind of `execution-345388`, or any assumption that
`BATON_V12_DISK_ROOT` relocates `OutputCase`'s ordinary `tempfile` SQLite roots
— it does not.

### The lead revalidated in the tree, with citations

Each of these I read at the base rather than carrying from the review.

- **`tests/manager/test_intake.py:2531-2535`** — `self.setUp()` runs **inside**
  a `subTest` loop over six member sets. Each iteration opens new state and
  registers another `addCleanup`, and `addCleanup` only fires when the **outer**
  test method ends, so all six sets stay live until then.
  `test_a_receipt_about_something_else_is_refused_by_both_exits` is the same
  shape.
- **`tests/manager/test_maintenance.py:2763`, `:2786`, `:2915`** —
  `self.addCleanup(case.doCleanups)`, deferring each sub-case's cleanup to the
  outer test the same way.
- **`tests/manager/test_output.py:101-104`** — `OutputCase.setUp` creates
  `control.sqlite3` under `tempfile.TemporaryDirectory(prefix="v12-output-")`,
  **not** `disk_backed_root`. So `BATON_V12_DISK_ROOT` does not relocate it.

All three hold. They are a **static lead**, not proof of which filesystem
filled, and the task says so.

### What was delivered

`execution-345822`, sealed: **61 payload members, 62 `SHA256SUMS` lines**,
`PACKET-INPUTS.json` sha256
`6d4e875e3991aa084062985fb258ef60fa021123cd9b03ced6db20c4e71c3e87`,
`sha256sum -c` zero failures — verified **both ways**: 63 files, no extras,
nothing missing. Proposed run `durable-capture-w341357-345822` at an **absent**
root. `start_authorized: false`, `start_selected: false`. **No start selected
and none taken.**

### Minimal, and I can say exactly how minimal

**Not changed at all:** `prepare.py`, `verify-inputs.py`, `probe.py`,
`collect.py`, every limit, and the sealed gate argv. The recovery cross-checks
already bind a retained candidate at `baton.w341357-recovery/3`, so swapping the
first retained candidate for the second needed **no program edit and no new
probe** — the 61 probes are carried untouched and all pass. That is what "reuse
unchanged machinery" cost: nothing.

**Changed:** the identity, the recovery input, the three worker-visible
documents, the four records, the snapshots and the seal.

### The input

`recovery-345388/candidate.patch` — the second retained candidate, copied
verbatim: `5030be0867af2c7989638ca2cf369891672b876b80f6245e6344d0db793d3458`,
9 sections, verified against its source **and** against the reviewer's published
digest, with the sections checked to name exactly the result document's own
`changed_paths`. `recovery-345039` stays in place as history; its pins are
dropped, not edited. The transport bundle `c6d1706d…` is recorded by digest and
locator and **refused** as a task input.

### What the task asks for, in order

1. apply the candidate, confirm all nine changed paths;
2. **reproduce the four methods first** — named in full in `TASK.md` — then
   **measure**: the canonical DB and workspace roots, their backing mount,
   **available bytes AND inodes** before / during / after the repeated subcases,
   the per-subcase lifetime, the high-water mark, and **the same-environment
   pinned base versus candidate counts**, which have never been run;
3. correct what the measurement demonstrated, leaving every module, case and
   assertion standing — including every negative and refusal case — plus the
   verifier custody boundary and the production refusals, with **no skips, no
   hidden `TMPDIR` change and no resource-limit change**;
4. the complete five-module gate, counts and duration against the 30s ceiling,
   iterating inside the one Job while the limits allow;
5. **write `W341357-VERIFICATION.json` into the candidate tree** so it travels
   as a changed path in the existing `change.patch` — the fix for my own
   reporting-channel defect, using the existing mechanism and no new protocol;
6. stop at 600s, end by 720s — the last run overran that target by 69s;
7. report only what the worker can observe.

The task states plainly that if the measurement contradicts the static lead,
**follow the measurement**, and that per-subcase cleanup is a suggestion rather
than a prescription.

### Preparation evidence, zero product tests

- **Input check** 0.12s exit 0 — 114 manager files, 3 supervisor, 2 preparation
  inputs, **50** task inputs, **41** decision snapshots, 4 checkout documents,
  1 controller, 1 helper, **2** pinned recovery inputs, 1 gate module owed, and
  **no decision-source drift** after re-taking `FINDING.md` and `PLAN.md`.
- **Preparation exercised once** into `/tmp/w341357-preflight5` — stage 0.11s,
  bootstrap 0.61s, bind 0.37s, **≈1.09s all status 0**. Authority
  `2ae413ff9d05429593b96b15ee557f7c`, composed packet
  `b2616bdf5f566807c8fb1563dceea77478c5a21e52851937c52f3b19f43fb18e`, composed
  `run_id durable-capture-w341357-345822` / `work W341357` / `claim 345822`,
  **50 `fixture.files`**, `PREPARED.json` `prepared-not-executed` /
  `start_selected false`. **No pass was discarded this claim.**
- **Read back from the bound documents**, not asserted: `candidate.patch` at
  `5030be08…`, `COMPLETION.md` verbatim at `c8c5d4dd…`, **no `objects.bundle`
  in the fixtures**, the verification member digest `2f7ed3dc…` unchanged, and
  the composed task instructions naming both the four methods and
  `W341357-VERIFICATION.json`.
- **Sixty-one probes, all behaving as intended, 2.555s — carried unchanged.**
- **Decision snapshots 36 → 41.** Five new: `review-345793` and its evidence
  record, `run-345388-INDEX`, `run-345388-GATE-CLASSIFICATION` — carried
  **exactly as written, including the two statements the review supersedes**,
  because the original evidence stays untouched and `FIXTURE.md` names the
  corrections — and `recovery-345388-INDEX`.
- **Preserved and re-verified**: `execution-345388` 57 of 57 and
  `execution-345039` 51 of 51, zero failures. **No instance root was read,
  written, re-run, recovered or re-bound.** No boundary preflight this claim —
  that belongs to the selected-run turn.

### Cost

Measured subtotal **about 3.8s** this claim — input check 0.12, stage 0.11,
bootstrap 0.61, bind 0.37, probes 2.555, seal and both-ways check ≈0.1 — with
**no discarded pass**.

Child cumulative: **a measured subtotal of about 2237s plus unknowns** — 3.3 +
951 + 3.5 + 12.1 + 3.6 + 465 + 3.7 + 791 + 3.8. The parent's ≈2253s stays with
the parent. Campaign totals, kept separate: provider served ≈**3940s**,
controller elapsed ≈**4027s**. **Gate measurements: 2.** **Product tests
executed by me on the host: 0.** Jobs 0; attempts 0; runtimes 0; provider calls
0; engine calls 0; credential values read 0; version-control mutations 0.

### Handoff

Returned to `baton.bug` for independent **preparation** review, then an
applicable exact invocation selection. Nothing here selects or authorizes a
start; owner345560 is consumed and `execution-345388` is neither re-run nor
re-bound.

Remaining scope: the measurement, the bounded fixture correction and a complete
gate inside a selected isolated execution, with the report written into the
candidate; then independent producer byte review and acceptance, which the
review places **after** an assessable passing gate. Parent W333486 stays blocked
by341370. W333485 owns the prospective lease correction and nothing here touches
a token. The M345516 overlap on `attempts.py` and the shared
`authoring_enforcement.py` input stands recorded with the pinned base
unchanged at `bc925cf5`.

## 2026-10-21 — baton.claude, claim347182 — THE SELECTED MEASURED-FIRST RUN

Claimed W341357 at snapshot347182 after reading current canonical state
(queued, unclaimed, routed `baton.impl`, `last_change_seq 347178`), the complete
handoff through `work-events` (45 events, no pagination remaining) and thread
T341357 in full (5 messages, `last_seq 345786` — unchanged since my own
read-after-handoff notice, so nothing new arrived). Read
`review-2026-10-21T11-53-41Z.md`, `FINDING.md` and `PLAN.md` as they stand now.

**The selection, read off reroute347178:** exactly **one enforced invocation**
of `durable-capture-w341357-345822` at
`/home/sl/baton-instances/durable-capture-w341357-345822`, using
`execution-345822` at manifest
`6d4e875e3991aa084062985fb258ef60fa021123cd9b03ced6db20c4e71c3e87`. **Pin the
selection and check executor capability BEFORE staging.** `AUTHORING-COMMAND`
only. Reproduce the four failing methods first, compare base against candidate
in the same environment, measure the actual storage roots, capacity and
lifetimes, fix the demonstrated fixture behaviour, run the complete five-module
gate with no skips or weakened assertions. One invocation, no retry; the
3600/30/4800/60 ceilings and the effective 900s lease apply to this run only.

### Revalidated before acting

- **Seal** 62 of 62, zero failures; `PACKET-INPUTS.json`
  `6d4e875e3991aa084062985fb258ef60fa021123cd9b03ced6db20c4e71c3e87` — **exactly
  the manifest the owner selected.** Both ways: 63 files, no extras, nothing
  missing.
- **Input check** 0.12s, **exit 0**, no refusals — 114 manager files, 3
  supervisor, 2 preparation inputs, 50 task inputs, 41 decision snapshots, 4
  checkout documents, 1 controller, 1 helper, 2 pinned recovery inputs, 1 gate
  module owed.
- **The proposed root is absent**, as it was at review.

**DECISION-SOURCE DRIFT, REPORTED AND NOT RESEALED** — third selected run in a
row with the same cause: the reviewer updated `FINDING.md` and `PLAN.md` at
claim345911 *after* sealing, recording that acceptance. Reporting rather than
refusing is the design, and **resealing would change the manifest the owner
selected.** The turn reads the immutable snapshots.

### Executor capability checked BEFORE staging, as the selection requires

The post-bind boundary preflight **cannot** satisfy that instruction: it reads
`packet/AUTHORING-COMMAND.json`, which does not exist until `bind`. So this is
the earlier, weaker check, run against the packet's own pins — 0.018s,
**`verdict: capable`, zero denials**:

- the engine answers;
- the pinned worker image is present and its config digest **equals the pin**;
- the credential registry names `w202663-development` and its backing file
  exists — **no value read**;
- the pinned bootstrap binary is present and **matches its pinned digest**;
- the proposed root is **absent**.

It creates nothing, starts nothing and submits nothing. It is **structural** and
cannot establish that a provider session is valid — run341637 failed on an
expired OAuth session 0.337s after a clean check of exactly this kind. The
stronger boundary preflight still runs after `bind`.

### Preparation and boundary preflight at the selected root

Stage 0.12s, bootstrap 0.60s, bind 0.36s — all status 0, authority
`0f62e22e9cdb43f2a35f4f0298732aac`, composed packet
`ab9d3bbeed2376b9b0960f52c5e7b058153162ae19412821e907be2b24bdbc52`, composed
`run_id durable-capture-w341357-345822` / `work W341357` / `claim 345822`, **50
`fixture.files`** with `candidate.patch` at `5030be08…`, `TASK.md` `c696af6d…`,
`FIXTURE.md` `0c9e20ce…`, `COMPLETION.md` verbatim at `c8c5d4dd…`, **no
`objects.bundle` in the fixtures**, verification member `2f7ed3dc…` unchanged,
and the composed task instructions naming both the four methods and
`W341357-VERIFICATION.json` — read back from `task.json`.

`AUTHORING-COMMAND.json` agreed with `COMMANDS.md` step 4. **Boundary
preflight** 0.327s, child status 0, **`verdict: available`, zero denials.**

### THE RUN: launched 15:05:41Z — AND THE GATE PASSED

| fact | value |
| --- | --- |
| served | **733.29s against a 900-second lease** — 166.71s of margin |
| ended | **on its own** — `provider.status 0`, no interruption, token `returned`, `expired: false` |
| controller | `state: held`, `faults: []`, **`child_status: 0`**, elapsed **732.97s** |
| workload | **`state: settled`, `stopped: completed`**, `implementation: completed` — the first settled/completed workload in this campaign |
| attempt | **`completed`** at the worker, **`candidate`** at the adapter, **`verification: passed`**, a proposal published |
| **candidate** | head `e9d292ede76a…`, base `bc925cf5…`, 281836 bytes, `sha256:59d666d9…`, **`acceptance: unobserved`** |

It overran the 720-second planning target by **13.29s** — inside the lease, and
much closer than last run's 69s.

**The sealed gate passed twice in this run, and they are two different
measurements:** the worker's own in-turn run at **864 tests / 0 failures / 0
errors / 0 skips in 11.398s**, and **the adapter's sealed run at 864/0/0/0 in
12.631s, exit 0** — the latter is what decided the disposition. Against a
30-second ceiling, 11.604s wall with 18.4s of headroom.

Three gate measurements now, same argv, same 864 tests:

| run | result |
| --- | --- |
| `345039` | `failures=9, errors=7`, 12.817s |
| `345388` | `failures=0, errors=16`, 12.515s |
| **`345822`** | **`0 failures, 0 errors, 0 skips`, exit 0** |

### The measurement finally exists, and it changes the story

The turn did what the review asked and the answer is not what either of us
predicted. **The disk-full outcome did not reproduce** — not in the four methods
in isolation, not in the full gate, not at the base and not under the candidate
as given.

What it measured instead:

- **the filling mount is `/tmp`, a 64 MiB tmpfs** —
  `tmpfs /tmp tmpfs rw,…,size=65536k,inode64`, read from `/proc/mounts`,
  `total_bytes 67108864`. Every ordinary SQLite store and maintenance root
  lands there because the fixtures use `tempfile.TemporaryDirectory`. **It is
  shared with the provider's own ephemera and nothing bounds what else consumes
  it.**
- `disk_backed_root()` selected `<checkout>/v12/python` on overlay with
  **644867325952 bytes available** — never a constraint, confirming
  `BATON_V12_DISK_ROOT` does not relocate the ordinary stores.
- **the gate's `/tmp` high-water fell from 13303808 to 2437120 bytes (81.7%)**
  and inodes from 326 to 63, sampled 563 and 566 times by a statvfs sampler
  thread across two full gate runs.
- **the same-environment base/candidate comparison ran at last**: the four
  modules both trees share give **801 tests with 2 failures at the pinned base**,
  and the candidate adds 63 tests and changes no other outcome. Base was
  restored by returning the seven tracked paths to HEAD and moving the two
  created paths aside, then restored and re-verified by digest — **no index,
  ref, stash or commit touched.**
- those two base failures were diagnosed to an **umask-dependent fixture
  precondition**: both built their result root with `os.makedirs` and no mode,
  inherited the `0o077` umask, and `intake.inaccessible_output` then correctly
  named the fixture's own root. **The fixture was wrong; the product read is
  right in both arms.**
- **assertion executions were counted per method in both arms**, which is the
  answer to "an equal test count proves nothing": they went **up** for the two
  corrected methods — 1 → 5 and 5 → 12 — precisely because those tests
  previously failed early in setup and never reached their later assertions.
- measured sub-case lifetime: **13, 17, 10 and 22 simultaneous temporary roots
  with zero releases** before the final open.

The correction drains the previous sub-case's cleanups before the next `setUp`
in `test_intake`, and binds each sub-case's teardown to a per-sub-case
`contextlib.ExitStack` in `test_maintenance` — with failing teardowns still
surfacing, so a broken cleanup remains a reported outcome. **No `TMPDIR` change,
no resource-limit change, no skip, no assertion deleted or relaxed, no refusal
made unreachable, and all four producer sections byte-identical to what was
handed in.**

### THE OPERAND FINDING, reported and not acted on

`/tmp` is 67108864 bytes total, it is **not the gate's alone**, and nothing
bounds what else consumes it. The report's own strongest explanation for
`345388` — **and it says it is not proven** — is that run worked for 789 seconds
before its gate ran and met a `/tmp` it had already largely consumed; this run
saw 56–57 MB available at gate time, and what `345388` had is **not recoverable**.
No limit was changed and no `TMPDIR` was moved. That is an operand decision for
the reviewer and the owner.

### The report exists, in the candidate, and the channel worked

`W341357-VERIFICATION.json` — 35070 bytes — is a changed path in the
candidate's own `change.patch`, carrying the commands as argv, every count, the
roots and mounts with bytes and inodes before/during/after, the high-water
figures, the lifetime table, the assertion-execution counts, the changed paths
with ownership, and an explicit `what_this_run_did_NOT_establish`. It states
`EVIDENCE ONLY` and `MUST BE EXCLUDED FROM ANY LATER PRODUCT IMPORT`, and
declares it carries no credential, environment value or provider text. **My
reporting-channel defect is closed** using the existing mechanism.

**And it found a defect in my task that I should name.** It reports the
correlation keys `run_id`, `outcome_path` and `status_path` as
**absent-by-structure** — no environment variable or file carrying them was
present in the worker, only `W341357` in the task text — and named them absent
rather than guessing. I asked step 7 for keys the worker cannot see. That is
mine to fix.

### Post-run collection — step 5, mine and not the worker's

`collect.py` exit 0: five of six artifacts present, every correlatable one
**matched**; `shutdown_request` **absent**, correctly, because nothing
interrupted the run. All four links `found`, no `isolated_failures`, no
`unclassified_entries`. `publication_timeout.established: false` with zero
parsed faults — **uninformative in either direction** per
`producer_persistence`. `shutdown_progress` step *"final enforcement
publication"*, no faults.

### Evidence, and two deliberate omissions

`evidence/run-345822/` — **17 files, 16 indexed copies, each verified against
its live source after writing, mode 0444**, including the candidate patch,
bundle, result, custody seal, **`W341357-VERIFICATION.json`**, both preflights
and my collection report. **Not copied:** the raw verification stream and the
provider transcript, both with locator and sha256 in the index so a reviewer can
bind and read them in place.

### Preserved

Packet seal re-verified **62 of 62, zero failures** — nothing written inside it.
`execution-345388` 57 of 57 and `execution-345039` 51 of 51. This run's runtime
is destroyed and the controller has exited. The seven earlier instance roots are
untouched. **The pinned base stays `bc925cf5`**; the base restore inside the run
used only working-tree path checkout and was re-verified by digest.

### Cost

Measured subtotal **about 735s** this claim — input check 0.12s, capability
check 0.018s, stage 0.12s, bootstrap 0.60s, bind 0.36s, boundary preflight
0.327s, **the run 732.97s controller elapsed / 733.29s provider served**,
collection ≈0.01s, with evidence copying and indexing a few seconds unmeasured.
No discarded pass.

Child cumulative: **a measured subtotal of about 2972s plus unknowns** — 3.3 +
951 + 3.5 + 12.1 + 3.6 + 465 + 3.7 + 791 + 3.8 + 735. The parent's ≈2253s stays
with the parent. Campaign totals, kept separate: provider served ≈**4673s**,
controller elapsed ≈**4760s**. **Gate measurements: 3, the last one passing.**
**Product tests executed by me on the host: 0.** Jobs 1; attempts 1; runtimes 1;
provider calls 1 which **succeeded**; engine calls 4 read-only across the two
preflights plus the run's own; credential values read 0; version-control
mutations 0.

### Handoff

Passed to `baton.bug` for independent review of **a candidate whose gate
passes** — the first in this campaign. **This is not acceptance:** `acceptance`
reads `unobserved`, and the review has been explicit that independent producer
byte review and the parent's joined acceptance follow an assessable passing
gate, which is what now exists.

Remaining scope: that producer byte review and acceptance; the operand decision
about the 64 MiB shared `/tmp`, reported with numbers and untouched; the two
items the report names as unmeasured — why `345388` filled, and whether the two
umask-dependent cases pass under `0o022`; and the serial reviewed reconciliation
of the M345516 `attempts.py` overlap, with the pinned base unchanged. Parent
W333486 stays blocked by341370 and owns ordinary status/report, the full joined
twelve-module gate, the installed-bundle proof and joined acceptance. W333485
owns the prospective lease correction; nothing here touched a token, and this
run is again not lease evidence — it returned with 166.71s of margin.

## 2026-10-21 — baton.claude, claim347396 — THE TWO PRODUCER DEFECTS

Claimed W341357 at snapshot347396 after reading current canonical state
(queued, unclaimed, routed `baton.impl`, `last_change_seq 347393`), the complete
handoff through `work-events` (49 events, no pagination remaining) and thread
T341357 in full (5 messages, `last_seq 345786`, unchanged). Read
`review-2026-10-21T15-30-10Z.md`, `FINDING.md` and `PLAN.md` as they stand now.

**Scope, read off pass347393 and the review:** the gate passes and the fixture
work is retained, but product acceptance is **withheld on two producer
defects**. One bounded, coupled milestone — R1 observation identity and
currentness, R2 recording-degradation propagation — with deterministic
production-boundary evidence, reusing the latest candidate and unchanged
machinery. Preparation only: owner347178 is consumed, so **no launch, no retry,
no rebind, no host product-test fallback**.

### Both defects verified in the candidate bytes, not taken on the handoff

I read the cited lines in the preserved checkout, read-only.

**R1 — value dedup conflates a fresh observation with a replay.**
`failure_cause.record_and_raise_cessation_outcome` loops
`for revision in range(OUTCOME_REVISIONS)` and, for each revision already
committed, returns it when `_same_account(held, document)` holds.
`_same_account` (line 461) compares **the facts**, excluding only `revision`
and `supersedes` — deliberately, and its docstring says so. So nothing in the
arriving document distinguishes *this is a new sample* from *this is a
redelivery*.

`intake.py:5966-5982` then re-samples the adapter on **every** settlement call
and records `ceased-quiescent` or `uncertain-observation` with the **same**
component, generation, runtime and correlation — so A→B→A is reachable with no
generation change and no token release. The third fresh observation matches
revision 0 on the facts, returns it, writes nothing, and
`attempt_cessation_outcome_of` keeps answering **revision 1, the uncertain
one**. Reverse the order and a stale positive wins instead. Confirmed exactly as
the review traced it.

**R2 — the degradation return is discarded on the acting paths.**
`record_cessation_outcome` never raises; it returns `_reported(...)`, and
`recording_degraded()` is the classifier. The contract already exists and is
used: `intake.py:5710-5711` and `6058-6059` and `attempts.py:3647` do
`if failure_cause.recording_degraded(reported): answer["diagnostic_degradation"]
= reported`.

But at **`intake.py:5771-5775`** (typed stop refusal) and **`:5788-5792`**
(uncertain observation) the call is a **bare statement** — the return value is
dropped — and the function returns the ordinary `held`/`uncertain` dict. Same at
the unresolved-attachment and positive-cessation branches and at the
settlement non-absence path. So a post-intent outcome-write failure leaves the
durable record intent-only and tells the operator nothing. Confirmed.

**And the phrasing inconsistency is real.** The malformed-fact branch at
`failure_cause.py:733-734` returns
`"; and the cessation outcome could not be recorded: {failed}"`, which is **not**
the `_reported` wording that `recording_degraded` tests — so that one
recording failure is invisible to the classifier. Confirmed.

### One honest note about a filename I am keeping

`FIXTURE.md` is pinned by name in `prepare.py`, `verify-inputs.py` and two
probes. Its subject is now the producer defects rather than the fixture, and the
accurate name would be different — but renaming it means editing the machinery
the review told me to leave alone on a "minimal supported continuation". **So it
keeps its name**, its first line says what it now carries, and I am recording
the compromise here rather than letting a stale filename pass unremarked.

### What was delivered

`execution-347396`, sealed: **67 payload members, 68 `SHA256SUMS` lines**,
`PACKET-INPUTS.json` sha256
`7df8bcbc5ac4d8549bc15501b07d27f53b9127e28a614953ed199ba559dd2ed3`,
`sha256sum -c` zero failures — verified **both ways**: 69 files, no extras,
nothing missing. Proposed run `durable-capture-w341357-347396` at an **absent**
root. `start_authorized: false`, `start_selected: false`. **No start selected
and none taken.**

### Minimal again, and again it cost nothing

**Not changed at all:** `prepare.py`, `verify-inputs.py`, `probe.py`,
`collect.py`, every limit and the sealed gate argv. The recovery cross-checks
already bind a retained candidate at `baton.w341357-recovery/3`, so swapping the
failing candidate for the passing one needed **no program edit and no new
probe** — 61 probes carried untouched, all passing in 2.506s. Second consecutive
packet where reusing unchanged machinery cost nothing.

**Changed:** the identity, the recovery input, the three worker-visible
documents, the four records, the snapshots and the seal.

### The input

`recovery-345822/candidate.patch` — the candidate **whose gate passes**, copied
verbatim at `294368c55fd468a95a4375c250e560def0f4cbc0a0c8a2a3a6f2658732e83856`,
11 sections, verified against its source **and** against the reviewer's
published digest, with the sections checked against the result document's own
`changed_paths`. Transport `806ef400…` recorded by digest and **refused** as a
task input; the composed `fixture.files` carries no `objects.bundle`.
`recovery-345388` stays as history, pins dropped not edited.

### What the task asks for

Eight ordered steps, and step 2 is the one that matters: **reproduce both
defects deterministically at the production boundary before fixing either.**

- **R1** — drive a settlement A→B→A under one held revoked generation with no
  generation change and no token release; show the third fresh observation
  discarded and the reader still answering the uncertain revision; show the
  reverse order where a stale positive wins; then add **a delayed exact
  redelivery of the old A**, which must not supersede B. Then correct it so a
  fresh A→B→A is retained, an exact replay is not, history stays bounded — and
  **do not** turn the existing replay test into tip-only dedup.
- **R2** — inject an **outcome-write failure after the durable intent commits**
  at the real reclaim, settlement and cancellation boundaries including the
  exception branches; then propagate bounded secret-safe degradation through
  **the channel that already exists**, without masking the original engine
  refusal, inferring cessation, or touching the holds, fencing or cleanup. Fix
  the inconsistent phrase too.

Then the complete five-module gate with no skips, and **extend** the existing
`W341357-VERIFICATION.json` rather than replacing it.

**Two of my own instructions corrected in this task.** Step 6 no longer demands
the correlation keys the worker cannot see — the previous turn named them
absent-by-structure rather than guessing, which was right. And step 7 notes that
both of the last two runs overran the 720s target (69s, then 13.29s) and asks
this one to land inside it.

### Preparation evidence, zero product tests

- **Input check** 0.10s exit 0 — 114 manager files, 3 supervisor, 2 preparation
  inputs, **56** task inputs, **47** decision snapshots, 4 checkout documents,
  1 controller, 1 helper, 2 pinned recovery inputs, 1 gate module owed, **no
  decision-source drift** after re-taking `FINDING.md` and `PLAN.md`.
- **Preparation exercised once** into `/tmp/w341357-preflight6` — stage 0.12s,
  bootstrap 0.59s, bind 0.36s, **≈1.07s all status 0**. Authority
  `072edae375bc4f1081259d6ded8c6aa2`, composed packet
  `3cb30f2ade304af12b793bd16884c3164d46a5b9b420f9bf047638b843b7e9b4`, composed
  `run_id durable-capture-w341357-347396` / `work W341357` / `claim 347396`,
  **56 `fixture.files`**, `PREPARED.json` `prepared-not-executed` /
  `start_selected false`.
- **Read back from the bound documents:** `candidate.patch` at `294368c5…`,
  the previous turn's report snapshot at `a5b69ad3…` — both the reviewer's
  published digests — `COMPLETION.md` verbatim at `c8c5d4dd…`, no
  `objects.bundle` in the fixtures, verification member `2f7ed3dc…` unchanged,
  and the composed task instructions naming `W341357-VERIFICATION.json`,
  `diagnostic_degradation` and `recording_degraded`.
- **Decision snapshots 41 → 47.** Six new, including
  **`run-345822-W341357-VERIFICATION.json`** — the previous turn's own evidence
  report, carried as a snapshot so the next turn can read what was measured
  **without reaching into a preserved instance**.
- **Preserved and re-verified**: `execution-345822` 62 of 62 and
  `execution-345388` 57 of 57, zero failures. The only instance read this claim
  was run345822's checkout, **read-only**, to revalidate the two cited defects.
  No boundary preflight — that belongs to the selected-run turn.
- One input check was **discarded** (it refused because `TASK.md` did not yet
  name the owed gate module by its full path) and is not counted.

### Cost

Measured subtotal **about 3.7s** this claim — input check 0.10, stage 0.12,
bootstrap 0.59, bind 0.36, probes 2.506, seal and both-ways check ≈0.1 — **plus
an unknown discarded-pass cost** for the refused input check.

Child cumulative: **a measured subtotal of about 2976s plus unknowns** — 3.3 +
951 + 3.5 + 12.1 + 3.6 + 465 + 3.7 + 791 + 3.8 + 735 + 3.7. The parent's
≈2253s stays with the parent. Campaign totals: provider served ≈**4673s**,
controller elapsed ≈**4760s**. **Gate measurements: 3, the last one passing.**
**Product tests executed by me on the host: 0.** Jobs 0; attempts 0; runtimes 0;
provider calls 0; engine calls 0; credential values read 0; version-control
mutations 0.

### Handoff

Returned to `baton.bug` for independent **preparation** review, then an
applicable exact invocation selection. Nothing here selects a start; owner347178
is consumed and `execution-345822` is neither re-run nor re-bound.

Remaining scope: inside a selected isolated execution, the two reproductions
first, then the two corrections, then the complete gate — and then the
independent producer byte review and acceptance that the passing gate makes
assessable. Parent W333486 stays blocked by341370 and owns ordinary
status/report, the full joined twelve-module gate, the installed-bundle proof
and joined acceptance. W333485 owns the prospective lease correction; nothing
here touched a token. The M345516 `attempts.py` overlap stands recorded — and
R2 may well change that file, so `TASK.md` requires every change there to be
named explicitly for serial reviewed reconciliation, with the pinned base
unchanged at `bc925cf5`.

## 2026-10-21 — baton.claude, claim348718 — THE 900-SECOND ASSUMPTION RETIRES

Claimed W341357 at snapshot348718 after reading current canonical state
(queued, unclaimed, routed `baton.impl`, `last_change_seq 348714`), the complete
handoff through `work-events` (59 events, no pagination remaining) and thread
T341357 in full (5 messages, `last_seq 345786`, unchanged). Read
`review-2026-10-21T18-36-26Z.md`, `FINDING.md`, `PLAN.md`, and the supplier's
`host-policy-347952/OPERATOR-DELTA.md` and `HOST-POLICY.json`.

**What changed upstream.** Owner348699 closed W333485 **satisfying** and
released consumers to prepare against its accepted inputs. The arbitrary
900-second lease that cut two runs of this slice dead is gone: permission is now
derived from the persisted controller envelope.

**Scope, read off pass348714 and the review:** prepare **one minimal immutable
successor** of `execution-347396` that consumes the complete accepted host
runtime, binds the controller and source seals to **those exact bytes**, and
**removes the superseded 900-second assumptions** — without rebuilding unchanged
machinery, without rebasing the worker, and without importing anything into the
main tree. Preparation only: no live start, no retry, no deployment, no
old-instance mutation, no host product test.

### The supplier binding, verified read-only before anything else

I ran the supplier's own `verify.py` rather than reimplementing its checks:
**verified, 114 members, 0.13s, `product_imports: false`, `extracted: false`,
`staged: false`**. Both digests confirmed by hand:
`HOST-POLICY.json` `eb57aa9c3ba74886e2d9856cfe3382ceab6a2bdb1799283512a4943dfeb62d52`
and `manager-source.tar.gz`
`1693bdd0808b051cb575c11a5f4c290a79d64119a04e34075005beaee41debbd`.

### Two bases, and they are not the same base

This is the thing easiest to get wrong, so it is written down before any edit:

- **host source base** — `d3a7a41c` plus the five reviewed production files.
  Six of the 114 members differ from the old consumer host: `tokens.py`,
  `workspaces.py`, `single_worker.py`, `stage_execution.py`,
  `authoring_enforcement.py` (controller `d12769df…` → **`248ee9ed…`**) and
  `attempts.py` (the `d3a7a41c` baseline `5c3cf846…`, *not* another
  implementation by this Work). The other 108 match exactly.
- **worker candidate base** — **unchanged at `bc925cf5`**, with candidate
  `e9d292ed…` and `recovery-345822/candidate.patch` `294368c5…`.

Changing the host does **not** authorize rebasing or replacing that candidate,
and the supplier says so in terms. The controller correction must **not** be
applied as an unchecked patch over `bc925cf5`; it comes from the archive.

### The effective permission, to be derived inspectably rather than asserted

3600 provider / 30 verifier / 4800 total / 60 cleanup are unchanged. What
replaces the 900-second lease: origin is the **persisted authoring envelope's
`started_at` before acquisition**; execution stop at **origin + 4740**;
permission expiry at **origin + 4800**; latest full invocation admission at
**origin + 1110** because remaining execution must fit 3600 + 30; at an
acquisition 120 seconds in, **4680** permission seconds remain. Replay does not
reset origin and restart is cancellation-only.

**The 600/720 planning targets become history, not policy.** They were a
response to a 900-second lease that no longer bounds this run, and the review
is explicit that they are historical planning rather than the new effective
permission.

### What was delivered

`execution-348718`, sealed: **70 payload members, 71 `SHA256SUMS` lines**,
`PACKET-INPUTS.json` sha256
`72bb8eab923b24a819dedea2fa356364414f6dfa367616764e848c4d73b36a7f`,
`sha256sum -c` zero failures — verified **both ways**: 72 files, no extras,
nothing missing. Proposed run `durable-capture-w341357-348718` at an **absent**
root. `start_authorized: false`, `start_selected: false`.

### The host source now comes from the accepted archive

`prepare.py` and `verify-inputs.py` no longer read the host bytes through
`committed('v12/python/…')`. They read the **114 members from the bound
archive**, and they refuse — **before any destination exists** — a drifted
binding, a drifted archive, a non-regular entry, an unsafe or absolute path, a
member the binding does not declare, a missing declared member, a drifted
member byte, or a controller/helper identity that disagrees with the binding.

**The generated seals equal the accepted binding, checked rather than
asserted.** The composed `manager_source.files` is **equal to
`HOST-POLICY.json`'s `manager_files` as a whole map**, all 114 entries; the
controller is `248ee9edd72214efbdc77044a9af6ad2c382e2ca1dbd5b71ff0db720d9a5a5dc`
in the composed packet, in `AUTHORING-COMMAND.json` and in the binding (it was
`d12769df…`); the helper matches too. The composer produced those seals from the
**staged** bytes — this is an equality test, not a restatement of the pins.

**And the worker did not move.** `candidate.patch` still travels at
`294368c5…`, base still `bc925cf5`, and the verification member digest is still
`2f7ed3dca95da498657a0e549e53107679fd7e8cf4503d5022555ba9e642176c` — **the same
gate across a host change**, which is the cleanest evidence that nothing was
rebased.

### The one carried-verbatim byte that had to change

`COMPLETION.md` has travelled at `c8c5d4dd…` since claim341637. It now reads
`4c7d666f5e94863fbafec033b17b295dca8ad6ecccf578ba72526b70f2e7c137`, because it
carried the 900-second lease and the 600/720 cutoffs **as policy** and the
review required the superseded assumptions removed. It leads with the
envelope-derived permission and demotes the old cutoffs to history.

`TASK.md` step 7 becomes a **margin obligation** rather than a stopwatch: stop
with room before the execution stop so the adapter can measure, verify,
revalidate, commit and publish — the extra permission is for doing the work
properly, not for working until expiry. `ENFORCEMENT.md`, `SHUTDOWN.md` and
`FAILURE.md` carry **dated amendments** rather than silent rewrites, and
`LIMITS-CHECK.json`'s whole `lease_disclosure` block is **removed** rather than
edited. `FAILURE.md` also withdraws its stale claim that no invocation ever
completed for this Work — three have, and the last one's gate passed.

### Evidence

- **Supplier binding verified read-only with the supplier's own `verify.py`**,
  not a reimplementation: verified, 114 members, 0.13s, `product_imports`
  false, `extracted` false, `staged` false. Both digests confirmed by hand.
- **Input check** 0.11s exit 0 — 114 manager files, 3 supervisor, 2
  preparation inputs, **59** task inputs, **50** decision snapshots, 4 checkout
  documents, 1 controller, 1 helper, 2 pinned recovery inputs, 1 gate module
  owed, **no decision-source drift**.
- **Preparation exercised once** into `/tmp/w341357-preflight7` — stage 0.07s,
  bootstrap 0.60s, bind 0.36s, **≈1.03s all status 0**, authority
  `d0cebfc7769d437abc52154c0655e15e`, composed packet
  `ab2153f58df958add8b27660c73f3533f567a0ed4d45025416ccfa15d625aae3`, 59
  `fixture.files`.
- **Executor capability for the successor operands: `capable`, zero denials,
  0.017s**, bound to this packet's **new** manifest — engine answers, image
  present and digest-equal to the pin, credential reference and backing present
  with no value read, bootstrap binary matching its pin, proposed root absent.
  The review was explicit that sibling operator custody does not prove this
  executor has it, so I checked it here.
  `evidence/successor-348718/EXECUTOR-CAPABILITY.json`
  (`ea325b4036a07e25898d425a69c8af20ecc436a6d3bdd8a1393daa09295c770c`).
- **Sixty-one probes, all behaving as intended, 2.368s — carried unchanged**
  for the third consecutive packet, and across a host change this time, because
  they exercise refusals rather than host bytes.
- **Decision snapshots 47 → 50**, now including **`HOST-POLICY.json` and
  `OPERATOR-DELTA.md` themselves**, so the turn reads the permission facts from
  the supplier record rather than from this packet's prose.
- **Preserved**: `execution-347396` 68 of 68 and `execution-345822` 62 of 62,
  zero failures. The archive was **read, never extracted** to a shared place
  and never installed. No instance was touched. Nothing was imported into the
  main tree and the worker was not rebased.

### What must not be run, carried from the supplier

W333485's obsolete renewal task, and `prepare-operator-347720.py
--prepare-authorized` for this binding — it still fixes the old root, the
900-second source and the obsolete task. Recorded in `PROVENANCE.json`
`what_must_not_be_run` so it cannot be rediscovered the hard way.

### Cost

Measured subtotal **about 3.7s** this claim — supplier verification 0.13s,
input check 0.11s, capability 0.017s, stage 0.07s, bootstrap 0.60s, bind 0.36s,
probes 2.368s, seal and both-ways check ≈0.1s — **plus an unknown
discarded-pass cost** for one probe run refused because `PROVENANCE.json` still
named the previous run.

Child cumulative: **a measured subtotal of about 2980s plus unknowns**. The
parent's ≈2253s stays with the parent. Campaign totals: provider served
≈**4673s**, controller elapsed ≈**4760s**. **Gate measurements: 3, the last one
passing.** **Product tests executed by me on the host: 0.** Jobs 0; attempts 0;
runtimes 0; provider calls 0; engine calls 2 read-only in the capability check;
credential values read 0; version-control mutations 0.

### Handoff

Returned to `baton.bug` for independent **preparation** review, then an
applicable exact invocation selection — which is now a selection the owner's
standing instruction no longer blocks, because the arbitrary lease it objected
to is gone.

Remaining scope unchanged: inside a selected isolated execution, reproduce R1
and R2 at the production boundary, correct them, run the complete five-module
gate, and extend `W341357-VERIFICATION.json`; then the independent producer byte
review and acceptance. Parent W333486 stays blocked by341370. The W339626
controller overlap is concrete and recorded: that candidate's controller hash
**is** this correction's reviewed base, so integration is serial with an
exact-base check rather than an overwrite.

## 2026-10-21 — baton.claude, claim348802 — THE SAME DEFECT, MINE, AGAIN

Claimed W341357 at snapshot348802 after reading current canonical state
(queued, unclaimed, routed `baton.impl`, `last_change_seq 348797`), the complete
handoff through `work-events` (63 events, no pagination remaining) and thread
T341357 in full (5 messages, `last_seq 345786`, unchanged). Read
`review-2026-10-21T18-48-05Z.md`, `FINDING.md` and `PLAN.md`.

### The finding is right and it is the same mistake I reported two packets ago

`execution-348718` consumes the accepted host correctly — the review confirms
the archive consumption, all 71 seals, the 70 payload hashes, the 72-file
inventory and the input check. **But I retired the 900-second assumption in the
worker-visible documents and the limits record, and left it standing in the
operator-facing ones.** Verified in the sealed bytes before accepting it:

| document | stale statement |
| --- | --- |
| `COMMANDS.md:280` | `lease \| **900s, enforced and not extended**` in the operands table |
| `OPERATOR.md:37` | *"`tokens.LIFETIME_SECONDS` is still 900 and renewal is not in this base"* |
| `OPERATOR.md:109` | *"stop optional edits at **600s**, end the provider turn by **720s**"* |
| `OPERATOR.md:220` | *"The 900-second lease is enforced, not extended. Expect expiry at 900 seconds"* |
| `PACKET.md:17` | vehicle pins naming controller **`d12769df…`** — the superseded one |
| `PACKET.md:93` | the input row still describing the *previous* packet's change |
| `PACKET.md:111` | *"`COMPLETION.md` travels verbatim at `c8c5d4dd…`. 900s lease … 600/720/180"* |
| `PACKET.md:226` | *"The 900-second lease is enforced and unextended"* |
| `PROVENANCE.json` | `enforcement.lease_disclosure` still asserting 900 and W333485 unfinished; `enforcement.no_completed_run` still claiming none ever completed; `enforcement.controller.sha256` still `d12769df…`; `cutoffs` still carrying 600/720/180 as current; `lease` still `{enforced, seconds: 900}` |

**This is exactly the class of defect I wrote a memory about and reported to this
reviewer two packets ago** — prose that passes a seal because `sha256sum -c`
checks bytes, not truth. I corrected the documents the *worker* reads and did
not sweep the ones the *operator* reads, and `PROVENANCE.json` is worse than
stale: it contradicts its own pins in the same file.

**What is not wrong:** the pins, the composed seals, the archive consumption and
the task. The operands an owner would select are correct; the prose describing
them was not.

### What this successor is

`execution-348802`: `execution-348718` with the documentation and provenance
made coherent, resealed, and **preserved history explicitly marked superseded
rather than deleted**. No redesign, no machinery change, no model run. I did
re-exercise the 1.03-second stage/bootstrap/bind once — **not** a bootstrap
campaign, but because the identity changes and I will not record composition
evidence that describes a different packet. That is the same honesty failure in
a different place.

### What was delivered

`execution-348802`, sealed: **71 payload members, 72 `SHA256SUMS` lines**,
`PACKET-INPUTS.json` sha256
`29db0bc5fc1fef9b7f65a89832bcf28f7425bd773b82617d3d101062cbc0cf53`,
`sha256sum -c` zero failures — verified **both ways**: 73 files, no extras,
nothing missing. Proposed run `durable-capture-w341357-348802` at an **absent**
root; `start_authorized: false`, `start_selected: false`.

### Every stale statement the review named, corrected

- **`COMMANDS.md`** — the `lease | 900s, enforced and not extended` row is
  replaced by the envelope-derived permission rows (provider/verifier/total/
  cleanup, origin, **stop origin + 4740**, **expiry origin + 4800**, latest full
  admission origin + 1110, one invocation) plus an explicit *superseded* row
  naming the accepted correction.
- **`OPERATOR.md`** — all three: the `LIFETIME_SECONDS is still 900` warning now
  says a 3600-second turn is within permission and points at
  `decisions/host-policy.json` as the authority rather than at itself; the
  600/720 step becomes a margin obligation; the expiry paragraph states the new
  stop and expiry and that replay does not reset origin.
- **`PACKET.md`** — the vehicle-pin row now names the **accepted archive** and
  controller **`248ee9ed…`** (`was d12769df…`) with a separate permission row;
  the stale input row describes the host change rather than the previous
  packet's; the `c8c5d4dd…`/900/600/720 sentence is corrected and says plainly
  **why `COMPLETION.md` had to move**; the lease disclosure states the
  retirement and adds that the three completed runs were all inside the *old*
  limit, so **none of them exercised the new permission**.
- **`PROVENANCE.json`** — `enforcement.controller` rebound to the archive
  controller with `previous_sha256` kept; `lease_disclosure`,
  `no_completed_run`, `cutoffs` and `lease` **renamed to `SUPERSEDED_*` with an
  explicit `superseded_by`**, not deleted. It no longer contradicts its own
  pins.

### Verified, not asserted

- **The seals still equal the accepted binding**: composed
  `manager_source.files` equal to `HOST-POLICY.json`'s map as a whole (114
  entries), controller `248ee9ed…` in the composed packet, in
  `AUTHORING-COMMAND.json` and in the binding, helper matching.
- **The worker still did not move**: `candidate.patch` `294368c5…`, base
  `bc925cf5`, gate member digest still `2f7ed3dc…`.
- **Input check** 0.11s exit 0, no decision-source drift — 60 task inputs, 51
  decision snapshots, 114 manager files, 2 pinned recovery inputs.
- **61 probes, all behaving as intended, 2.36s — carried unchanged** for the
  fourth consecutive packet.
- **Executor capability: `capable`, zero denials**, bound to this packet's new
  manifest. `evidence/successor-348802/EXECUTOR-CAPABILITY.json`.
- **Preserved**: `execution-348718` 71 of 71 and `execution-347396` 68 of 68,
  zero failures, both sealed and unedited. No instance touched.

### Why I re-exercised preparation

The identity changed, so the previously recorded composition would have
described a different packet. Re-running the 1.02-second
stage/bootstrap/bind is not the bootstrap campaign the review ruled out — and
recording stale numbers would have been the same honesty failure in a different
place, which is the whole subject of this claim.

### Cost

Measured subtotal **about 3.6s** — input check 0.11, stage 0.07, bootstrap
0.59, bind 0.36, probes 2.36, capability 0.02, seal and both-ways check ≈0.1.
**No discarded pass.** Child cumulative: **about 2984s plus unknowns**. Product
tests executed by me on the host: 0. Jobs 0; attempts 0; runtimes 0; provider
calls 0; engine calls 2 read-only; credential values read 0; version-control
mutations 0.

### Handoff

Returned to `baton.bug` for independent review, then an applicable exact
invocation selection. Remaining scope unchanged: reproduce and correct R1 and
R2 inside a selected isolated execution, run the complete five-module gate, and
extend `W341357-VERIFICATION.json`; then independent producer byte review and
acceptance. Parent W333486 stays blocked by341370.

**And a note about me, not the packet.** This is the second time in this
campaign that a seal verified while the prose lied, and the first time I had
already written the warning about it. Checking that the operator-facing
documents agree with the pins is now part of sealing, not a thing I notice
afterwards.


## 2026-10-21 — baton.claude, claim348852 — THE METHOD WAS THE DEFECT

Claimed W341357 at snapshot348852 after reading current canonical state
(queued, unclaimed, routed `baton.impl`, `last_change_seq 348848`), the complete
handoff through `work-events` (67 events, no pagination remaining) and thread
T341357 in full (5 messages, `last_seq 345786`, unchanged). Read
`review-2026-10-21T18-54-41Z.md`.

### Four more stale summaries, and the reviewer named the real problem

`execution-348802` fixed the statements review348787 cited and left four more
standing. Verified in the sealed bytes:

- **`PACKET.md:94`** — the `TASK.md` row still said *"land inside 720s"*;
- **`PACKET.md:166-167`** — the reading-order entry still presented the
  `COMPLETION.md` 600/720/180 cutoffs as current;
- **`PACKET.md:195-197`** — the evidence summary **spliced the new `348802` run
  id with the OLD `347396` claim and its 56 fixture files**;
- **`OPERATOR.md:112-113`** — *"the producer obligations stay owed and out of
  scope unless this turn's gate demonstrates a defect"* — the **opposite** of
  the truth, since R1 and R2 are owed precisely *because* the gate passed.

**The reviewer's instruction is the correction that matters:** *inspect
remaining current summaries, not only individual replaced strings.* I had been
patching cited anchors and leaving the paragraphs around them alone, which is
why this took three passes instead of one.

### What this successor does differently

`execution-348852`: **every preparation-evidence summary is regenerated from
this claim's own composed documents** — `PACKET.json`, `task.json`,
`policy.json`, `submission.json`, `PREPARED.json` — rather than edited. No
number is carried forward by hand, so this class of drift cannot survive
another rebinding. Sealed: **72 payload members, 73 `SHA256SUMS` lines**,
manifest
`3bf3d7df222fd91b79527ea37f8e656ccbcc6fa507dae0f72bd878f54d043a5f`,
`sha256sum -c` zero failures, verified both ways — 74 files, no extras.

`OPERATOR.md` step 4 now states that **R1 and R2 are owed, green gate or not**,
with the reason. The "cutoffs reach the worker" and "planning cutoffs inside
unchanged limits" paragraphs become the permission and what the permission is
not. `PACKET.md`'s `COMPLETION.md` entry names the envelope permission and says
the old cutoffs are recorded as history.

A grep for `720s`, `out of scope unless`, `claim 347396` and ``56 `fixture`` in
both documents now returns **zero**.

### Verified

Input check 0.11s exit 0, no drift — 61 task inputs, 52 decision snapshots.
Composed `manager_source.files` still **equal to the binding's map as a whole**
(114), controller `248ee9ed…`, helper matching. Worker unmoved:
`candidate.patch` `294368c5…`, base `bc925cf5`, gate member digest
`2f7ed3dc…`. 61 probes passing in 2.388s, carried unchanged. Capability
**`capable`, zero denials**, bound to the new manifest.
`evidence/successor-348852/EXECUTOR-CAPABILITY.json`. `execution-348802`
(72 of 72) and `execution-348718` (71 of 71) both sealed and unedited.

The reviewer also cleared the earlier question: the unnecessary-bootstrap
wording was not a prohibition and a disclosed short preparation creates no
approval issue. This claim re-exercised preparation on that basis and discloses
it the same way.

### Cost

Measured subtotal **about 3.6s** — input check 0.11, preparation 1.02, probes
2.388, capability 0.02, seal and both-ways check ≈0.1. No discarded pass. Child
cumulative **about 2988s plus unknowns**. Product tests on the host 0; Jobs 0;
provider calls 0; engine calls 2 read-only; credential reads 0; version-control
mutations 0.

### Handoff

Returned to `baton.bug` for independent acceptance, then an applicable
selection. R1/R2, the full gate and parent341370 remain. **And the lesson I owe
this reviewer: "fix the cited lines" is not the same as "make the document
true", and the second is what was asked for all three times.**


## 2026-10-21 — baton.claude, claim348929 — THE SELECTED RUN DIED AT IMPORT

Claimed W341357 at snapshot348929 after reading current canonical state
(queued, unclaimed, routed `baton.impl`, `last_change_seq 348925`), the
complete handoff through `work-events` (72 events, no pagination remaining) and
thread T341357 in full (5 messages, `last_seq 345786`, unchanged).
Owner reroute348925 selected exactly one invocation of
`durable-capture-w341357-348852` at manifest `3bf3d7df…`.

### Revalidated, preflighted twice, launched once — and it could not start

Seal 73 of 73, 74 files no extras, input check exit 0 (the familiar
post-acceptance `FINDING.md`/`PLAN.md` drift, reported and not resealed), root
absent. **Pre-stage capability check**: `capable`, zero denials, 0.017s.
Stage 0.07s, bootstrap 0.61s, bind 0.38s, all status 0 — composed
`manager_source.files` **equal to the binding's map as a whole** (114),
controller `248ee9ed…`, 61 fixtures, candidate `294368c5…`, gate digest
`2f7ed3dc…`. **Actual executor-boundary preflight**: `available`, zero denials,
0.334s, child status 0.

Launched 19:06:22Z. It died in about two seconds:

```
File ".../code/v12/python/tools/authoring_enforcement.py", line 554, in main
  from tools import authoring_baseline as baseline
ImportError: cannot import name 'authoring_baseline' from 'tools'
```

### THE BLOCKER, established rather than inferred

**The accepted controller imports a module the accepted binding does not
carry.** `HOST-POLICY.json` declares 114 manager members and its only
`authoring_*` members are `tools/authoring_enforcement.py` and
`tools/authoring_shutdown.py`. **`tools/authoring_baseline.py` is absent from
the binding**, therefore absent from the staged source, therefore the controller
cannot start.

The module is real: it exists at the host base `d3a7a41c` with sha256
`8e5987f56f8d5329…` — **which is exactly the supervisor `baseline.py` digest**.
At `d3a7a41c` the supervisor baseline was moved *into* the manager source. It is
**absent at the worker base `bc925cf5`**, where the old controller `d12769df`
imported `baseline` from the supervisor directory on `PYTHONPATH` instead.

So the contradiction is exact: `OPERATOR-DELTA.md` says the binding *"exactly
preserves [the consumer's] 114-file runtime path set"* — it does, and the
accepted controller needs a **115th** member that set never had. **Preserving
the old path set and shipping the new controller are incompatible.**

**I did not patch it.** Adding a member would change an independently accepted
binding, which is not mine to do, and `prepare.py` refuses a member the binding
does not declare — correctly, and by design. Supplying it from the main tree or
from `d3a7a41c` would be an unreviewed substitution into an accepted host
runtime.

**What it was not:** not authentication (no provider was contacted), not the
lease or the new permission (no envelope was ever composed), not the candidate,
recovery or gate (none was reached), not W339626's confinement correction
(different Work, different mechanism), and not the boundary preflight, which
passed 0.334s earlier.

### A gap in my own preflights, reported not widened

**Neither preflight checks that the staged manager source can import the
controller it pins.** Both passed and the controller still could not start.
That is a gap in my work and this run is the proof of it; whether a preflight
should import-check the staged controller is a decision for the reviewer and
the owner, so I have recorded it rather than quietly adding it.

### Cessation, stated exactly

No runtime was created, no token acquired, no attempt admitted, no Job
submitted, and no runtime container for this run exists in the engine listing.
**Nothing to clean — and that is not a cleanup claim read off an empty
listing:** no effect was ever ordered, because the process exited at an import
before any Job was composed. All six final-result artifacts are `absent`, and
absence names no cause on its own — the cause is the ImportError, read from the
controller's own stderr.

### Evidence

`evidence/run-348852/` — `BLOCKER-348929.json`
(`f6d48cb7e5f950d02914dd7bf0c0b2908acd34dd519d2dce651739095c09ac61`), the
controller stderr verbatim, the collection report and both preflight reports.

### Cost

Measured: input check 0.11s, capability 0.017s, stage 0.07s, bootstrap 0.61s,
bind 0.38s, boundary preflight 0.334s, **the run ≈2s**, collection ≈0.01s.
Child cumulative **about 2992s plus unknowns**. Product tests on the host 0;
Jobs 0 (none was composed); attempts 0; runtimes 0; provider calls 0; engine
calls 4 read-only across the two preflights; credential reads 0;
version-control mutations 0.

### Handoff — INCOMPLETE RETURN

Returned to `baton.bug` with an operational blocker, not a result. Owner
selection348925 is **consumed**; no retry, no recovery, and none attempted. The
root is preserved unchanged.

Remaining scope is unchanged and untouched: R1, R2, the complete five-module
gate and the extended `W341357-VERIFICATION.json`, then independent producer
byte review and acceptance. **What must be resolved first is the binding**: the
accepted host runtime needs `tools/authoring_baseline.py` among its members, or
the controller needs to resolve `baseline` the way the old one did — and either
answer belongs to the supplier and the reviewer, not to this packet. Parent
W333486 stays blocked by341370.


## 2026-10-21 — baton.claude, claim350529 — THE CORRECTED BINDING, CONSUMED

Claimed W341357 at snapshot350529 after reading current canonical state
(queued, unclaimed, routed `baton.impl`, `last_change_seq 350508`, open
blockers 0), the complete handoff through `work-events` (newest page to
`350529`, no pagination remaining) and thread T341357 in full (5 messages,
`last_seq 345786`, unchanged). Read `review-2026-10-21T23-00-29Z.md`, the
current `PLAN.md`, and the supplier dossier
`work/records/2026/10/finding-v12-host-runtime-import-closure/`.

### What was owed and what this claim did

Owner350489 closed **W348979 satisfying**: the corrected **115-member** host
runtime binding, which adds `tools/authoring_baseline.py` — the module the
accepted controller imports at lines 494, 506 and 554, and the one the
superseded 114-member binding never declared, which is why run348852 died at
import in about two seconds. The owed step was **one minimal immutable
successor consuming that binding**, with references, seals and current
summaries updated coherently and the worker side preserved.

`execution-350529`: **77 payload members, 78 `SHA256SUMS` lines, 79 files**,
`PACKET-INPUTS.json` sha256
`6be3fb90a1037c992e7e22510363953c51c99133a2a87572e5066aa3980bc6ff`,
`sha256sum -c` zero failures, **verified both ways** — no extras, nothing
missing. Proposed run `durable-capture-w341357-350529` at a fresh **absent**
root; `start_authorized false`, `start_selected false`. **NO START SELECTED.**

### Verified, not asserted

- **The supplier's own `verify.py` was RUN read-only rather than
  reimplemented**: `verified true`, 115 members, 114 preserved,
  `old_archive_missing_deferred_main_dependency true`, 1261 static edges,
  `product_executed false`, 6.24s. The supplier seal verifies 8 of 8.
- **The binding, independently re-derived here**: the new map is the old 114
  members byte-identical **plus** `tools/authoring_baseline.py` at
  `8e5987f56f8d5329…` — *exactly the supervisor `baseline.py` digest this
  packet also pins*. Every other policy key is equal to the superseded
  binding's except `claim`, `schema`, `work`, `archive`, `acceptance`,
  `provenance` (one added entry), `supersedes` and `closure_evidence`.
  Controller, helper, supervisor files, effective policy, execution selection,
  input pins and compatibility: **unchanged**.
- **The archive matches the map as a set and byte-for-byte**: 115 regular
  members, names equal to `manager_files`, zero digest mismatches.
- **Composed `manager_source.files` is equal to the binding's map as a whole**,
  all 115; `tools/authoring_baseline.py` present in the binding, in the
  composed packet **and on the staged disk** at the same digest;
  `manager_source.packages` is exactly `["baton_v12", "tools"]` — the package
  set the supplier requires a consumer to preserve, because
  `authoring_baseline.py:568` imports it.
- **Every member re-measured against the worker base**: 7 of 115 differ, 108
  are byte-identical, and the only one *absent* at that base is the deferred
  dependency. The pins carry the comparison rather than the inherited claim.
- Input check **0.06s exit 0**, no decision-source drift: 115 manager files,
  66 task inputs, 57 decision snapshots, 2 pinned recovery inputs, 1 gate
  module still owed. Run again after the document regeneration, same result.
- Preparation exercised once into `/tmp/w341357-preflight10`: stage 0.079s,
  bootstrap 0.595s, bind 0.361s — **≈1.035s, all status 0**, authority
  `1227b3a0b4f244deb4c724d510cca229`, composed packet
  `8290126781ff5ae4a1b8f6c57799c6fe69be41d2496dcbe9ae93a74ae42295a3`.
- **The worker did not move**: `candidate.patch` `294368c5…`, base `bc925cf5`,
  and the verification member digest
  `2f7ed3dca95da498657a0e549e53107679fd7e8cf4503d5022555ba9e642176c` —
  identical across the corrected binding, re-derived from this claim's composed
  `task.json`. No `objects.bundle` in the fixtures.
- **61 of 61 probes behaving as intended, 2.381s**, carried unchanged — the
  host-reading mechanism did not change, so moving binding cost no probe edit.
- Capability **`capable`, zero denials, 0.018s**, bound to this packet's
  manifest, proposed root absent.
- Preserved predecessors re-verified: `execution-348852` 73 of 73,
  `execution-348802` 72, `execution-348718` 71, `execution-347396` 68,
  `execution-345822` 62 — all zero failures, all unedited.

### The new refusal, demonstrated rather than claimed

Both programs now refuse a binding that does not declare
`tools/authoring_baseline.py` **by name**. Pointed at the exact 114-member
binding run348852 staged — whose own bytes and archive digest both still
verify — `prepare.py` and `verify-inputs.py` each raise *"the binding does not
declare the deferred controller dependency, which is the defect that killed
run348852"*. Read-only, in process, no root created, 0.02s;
`evidence/successor-350529/DEFERRED-GUARD.json`.

`probe.py` is **carried unchanged**, as the review requires, so this is
recorded as a separate check and **not** counted as probe coverage it does not
have.

**And it is not an import check of the staged controller.** The gap I reported
at claim348929 is still open and still the owner's and the reviewer's call:
neither preflight establishes that the staged source can import the controller
it pins. Nothing here claims dynamic startup evidence, and the supplier's
1261-edge proof is explicitly static.

### Six false current statements found and corrected — two of them in programs

The habit review348838 asked for — audit current-tense summaries, not cited
strings — applied this time to the **programs** as well as the prose:

1. **`SHUTDOWN.md`** named the **superseded** controller `d12769df…` in a
   *"this packet pins"* column. Wrong since claim348718 and carried through
   four sealed revisions. Corrected with the W338305 column kept as history.
   Its 114-entry sentence becomes 115 — and the import-failure rule that very
   section states is now recorded as having **fired a second time**, on a
   different module.
2. **`FAILURE.md`** carried the same superseded digest as what this packet
   pins. Corrected, and the run348852 import failure added as the second
   startup failure, with what it was *not* and the preflight gap stated.
3. **`prepare.py`** docstring: *"THE VEHICLE IS UNCHANGED. Controller
   `d12769df…`, 114 pinned manager files."*
4. **`prepare.py`** comment: *"`tokens.LIFETIME_SECONDS` IS STILL 900 AND
   RENEWAL IS STILL W333485'S WORK … no authoring invocation has ever completed
   for this Work."* Replaced with the permission read **at the staged bytes**:
   900 is still the default for an acquisition *without* an envelope
   (`tokens.py:37`), and the controller persists one (`KIND =
   'authoring.envelope'`), so this vehicle runs on origin + 4740 / + 4800.
5. **`prepare.py`'s `UNSELECTED` warning**, printed to the operator at *every*
   stage: two never-run selections, *"no authoring invocation has ever
   completed"* and *"the focused gate has never been measured in any run."*
   All three false. Now: three never-run selections, three completed
   invocations, three gate measurements with the last one passing.
6. **The GENERATED `AUTHORING-COMMAND.json`** carried a `lease` member saying
   *"expect enforced expiry at 900 seconds"* — **generated into every root,
   including run348852's, which was launched with it**, four claims after the
   packet documents retired the lease. It is now a `permission` member with the
   superseded text preserved beside it under `superseded_lease`.

Also corrected: `GATE-CHECK.json` carried *"four runs; zero measurements of
this argv"* in the same file as `MEASURED_THREE_TIMES_AND_IT_NOW_PASSES`;
`PROVENANCE.json`'s campaign record said five runs, one gate measurement and
two retained candidates, and `the_measured_gates` omitted the **passing**
measurement entirely; `PREFLIGHT.json` still carried the *first* retained
candidate's patch digest and the retired 600/720/180 cutoffs as current, plus a
`root` from `preflight2`; `PACKET.md`'s byline said claim345822 and
`OPERATOR.md` was still titled *"MAKE THE GATE USABLE"* with a lead describing
`execution-345039` as the run before this one, a five-run table, *"the obstacle
is that the gate cannot currently pass"*, a three-step task `TASK.md` no longer
contains, and *"a coherent slice that fits 900 seconds"*.

All of it is **labelled, not erased**: `SUPERSEDED_*` keys with
`superseded_by` reasons, and `PROVENANCE.stale_prose_corrected` enumerating
every instance. Every earlier packet stays sealed and unedited, stale text
included.

### One disclosure about my own method

The deferred-dependency guard check imported `prepare.py` and
`verify-inputs.py` through `importlib`, which wrote `__pycache__/*.pyc` **into
the packet directory**. I found them in the first seal — 81 files where 79 were
expected — removed them and re-sealed. The check should have run with
`PYTHONDONTWRITEBYTECODE=1`, as every documented command in this packet does.
No packet byte was otherwise affected, and the both-ways comparison is what
caught it.

### Unchanged, deliberately

`probe.py`, `collect.py`, the host-reading mechanism itself, the controller
`248ee9ed` and helper `af9e5ea6` identities, the three supervisor seals, the
worker base `bc925cf5`, the retained candidate `e9d292ed`, `recovery-345822`,
the sealed five-module gate argv, every limit figure, and **five of the seven
worker-visible documents** — `TASK.md`, `RECOVERY.md`, `COMPLETION.md`,
`FIXTURE.md` and `ENFORCEMENT.md` travel byte-identical.

### Cost

Measured subtotal **about 9.9s** this claim: supplier verifier 6.24, input check
0.06 twice, preparation 1.035, probes 2.381, deferred guard 0.02, capability
0.018, seal and both-ways check ≈0.1. **No discarded pass.** Child cumulative
**about 3002s plus unknowns**; the parent's ≈2253s stays with the parent.
Campaign provider served ≈4673s, controller elapsed ≈4762s. Gate measurements
3, the last one passing. Product tests executed by me on the host **0**; Jobs 0;
attempts 0; runtimes 0; provider calls 0; engine calls **2** read-only in the
capability check; credential values read 0; version-control mutations 0;
old-instance mutations 0.

### Handoff

Returned to `baton.bug` for independent acceptance of this preparation, then an
applicable exact invocation selection. Remaining scope unchanged and still one
cohesive correction: R1 fresh A→B→A versus delayed exact old-A replay, R2
caller-visible bounded secret-safe recording degradation across the production
boundaries, the complete five-module gate with no skips, the extended
`W341357-VERIFICATION.json`, then independent producer byte review and
acceptance. Parent W333486 remains blocked by341370 and owns the joined
status/report, the twelve-module gate, the installed-bundle proof and joined
acceptance. **Nothing in this packet establishes that the controller starts —
only a selected invocation can.**


## 2026-10-22 — baton.claude, claim352156 — THE SELECTED RUN REFUSED AT STARTUP, AND THE DEFECT WAS MINE

Claimed W341357 at snapshot352156 after reading current canonical state
(queued, unclaimed, routed `baton.impl`, `last_change_seq 352153`, open
blockers 0), the complete handoff through `work-events` (newest page to
`352156`, no pagination remaining) and thread T341357 in full (5 messages,
`last_seq 345786`, unchanged). Read `review-2026-10-21T23-28-31Z.md`, the
current `FINDING.md` and `PLAN.md`.

**Owner reroute352153 selected one invocation** of
`durable-capture-w341357-350529` at
`/home/sl/baton-instances/durable-capture-w341357-350529`, packet
`execution-350529` manifest `6be3fb90…`, with the actual boundary preflight
before the start and the generated enforced `AUTHORING-COMMAND.json` only. One
note on ordering, stated rather than glossed: the *boundary* preflight reads
`packet/AUTHORING-COMMAND.json`, which only exists after `bind`, so it cannot
precede staging. I ran the pre-stage capability check before staging and the
actual boundary preflight after `bind` and before the single launch.

### Revalidated before acting

Manifest `6be3fb90a1037c992e7e22510363953c51c99133a2a87572e5066aa3980bc6ff`
**exactly as selected**; seal 78 of 78, zero failures, **both ways** — 79 files,
no extras, nothing missing; input check 0.06s exit 0 with the familiar
post-acceptance `FINDING.md`/`PLAN.md` drift **reported and not resealed**,
because resealing would change the manifest the owner selected; proposed root
absent. Pre-stage capability **capable, zero denials, 0.017s**, bound to that
manifest.

Stage 0.077s, bootstrap 0.638s, bind 0.370s, **all status 0**. Authority
`f838ae72c8d24c5db407c3e9c7f80978`, composed packet `37c487f5…` — both
different from the preflight's, as `OPERATOR.md` step 2 says to expect. Read
back from the bound documents: 115 members **equal to the binding's map as a
whole**, `packages` exactly `["baton_v12","tools"]`, the deferred baseline
staged at `8e5987f5…`, controller and helper equal to the binding, 66
`fixture.files`, `candidate.patch` `294368c5…`, gate member digest
`2f7ed3dc…`, bounds 3600/4800/60/1/no-retry. **The generated enforced command
agreed with `COMMANDS.md` step 4 byte-for-byte**, working directory included.

Actual executor-boundary preflight: **available, zero denials, 0.332s**, child
status 0, controller resolved from the staged source. Plus one author check I
added for this launch: the exact statement from controller line 554 — the one
that killed run348852 — **resolved**, 0.321s, with `baseline.main` present. It
stated explicitly that it *"does not establish that the controller RUNS; only
that these imports resolve."*

### The run: a startup refusal two statements later

Launched once at **03:11:16Z**. The controller exited in about two seconds:

```
File ".../tools/authoring_enforcement.py", line 564, in main
    baseline.verify_imported_sources(packet)
File ".../tools/authoring_baseline.py", line 590, in verify_imported_sources
SupervisorRefusal: this process is running
'<root>/code/v12/python/tools/authoring_baseline.py' and the packet binds
'<root>/supervisor/baseline.py'
```

**What the check is.** `verify_imported_sources` proves every package the packet
names resolves inside the bound manager source, then proves **the module it is
itself defined in is the program the packet binds**. Its docstring: *called
before any store is opened, which is the only moment at which refusing is
free.*

**Why it fired.** The old controller imported a top-level `baseline` from the
staged `supervisor/` directory, so the running module and the composed
supervisor path were the same file. The accepted controller imports
`tools.authoring_baseline` from the **manager source**. `prepare.py`'s `bind`
still passed `supervisor_path=<root>/supervisor/baseline.py`. **The two files
are byte-identical** — both `8e5987f5…`, `cmp` reports no difference — so the
supervisor digest pin verified *immediately before* the refusal and **only the
path equality failed**.

**Whose defect: mine.** Not the corrected binding, which was exactly what
W348979 published and staged and verified member by member. Not the accepted
controller. Not the supplier. A composition argument of this packet.

**Cessation, stated exactly.** No envelope, no Job, no attempt, no runtime, no
token, no container, no provider call. `instance/db` holds **only**
`authority.sqlite3`, written by step 2 bootstrap — there is no `jobs.sqlite3`
and no `control.sqlite3`, so no `ControlStore` was ever opened, and no
`.authoring.lock` exists: the refusal precedes the lock, the store and
`verify_worker_image`, which are `main`'s next three statements. `collect.py`
reports **all six final artifacts absent**, and absence names no cause — the
cause is the refusal above. **Nothing to clean, because nothing was ordered.**
Evidence: `evidence/run-350529/`, `BLOCKER-352156.json` at
`5d9e626da7f38614bd59be885f4b2074fa686cc89b4339c41c70a72d2c9c8753`.

### The correction, prepared in the same turn

M345649 permits fixing an ordinary demonstrated issue as a small correction
without a new approval campaign, and this defect is one argument in my own
program. `execution-352156`: **79 payload members, 80 `SHA256SUMS` lines, 81
files**, manifest
`9bda87e4ad655da1c1a452b901f994c5da7b4647d1a64c02ab2287866086dc2e`, zero
failures, **both ways** — no extras, nothing missing.

1. `bind` composes `supervisor_path` as the staged `tools/authoring_baseline.py`
   — the program the controller runs.
2. `bind` **refuses** if the composed supervisor program is not that path, or
   is not the pinned manager source member.
3. `held_packet` and `verify_imported_sources` now run through
   `tools.authoring_baseline` instead of the supervisor directory copy.
   **This was not optional**: with (1) in place, verifying through the
   supervisor copy refuses in **mirror image** — *"this process is running
   /tmp/…/supervisor/baseline.py and the packet binds
   /tmp/…/tools/authoring_baseline.py"*. Measured, and that is how the full
   shape of the correction was found. `baseline_bindings` and
   `prepare_instance` still come from the supervisor directory: they are the
   composer.

**The supervisor digest pin did not move.** `8e5987f5…` either way; only the
path this packet names changed. The supervisor directory stays staged and
pinned as provenance because the **host** preparation imports the composer from
it.

### Proved, not argued

`main`'s first three statements — `held_packet`, `verify_imported_sources`,
`verify_controller` — run **in order**, in a child with the controller's exact
working directory, `PYTHONPATH` and `BATON_V12_STAGE_EXECUTION_CONFIG`, against
this claim's composed packet: **all three accept, 0.330s**, with `baton_v12`
and `tools` resolving inside the staged source. The **same check against the
packet composed at the preserved run350529 root reproduces the exact refusal**,
0.328s, and reports `verify_controller` as **not reached** rather than refused —
because `main` stops at the first refusal. Read-only; that root was not
modified.

It **stops at `main`'s next statement, the authoring lock**: no lock taken, no
store opened, no image inspected, no Job, no container, no provider, no
credential. **It does not establish that the controller starts.** Author
evidence in `evidence/successor-352156/`; `probe.py`, `verify-inputs.py` and
`collect.py` are unchanged.

I corrected one defect in that check before it became evidence: it first
reported `verify_controller` as *refused* on the failed packet when it had
never been called. `refused` and `not reached` are now separate fields.

### Also verified

Input check 0.06s exit 0, no drift — 115 manager files, **68** task inputs,
**59** decision snapshots, 2 pinned recovery inputs, 1 gate module still owed.
Preparation exercised once into `/tmp/w341357-preflight11`: 0.077 / 0.606 /
0.367, **≈1.050s all status 0**, authority `c8ad2beebfce41e08958d57b1d0b100d`,
composed packet `4ddf4dd6…` — read from `PREPARED.json`, not retyped. 61 of 61 probes behaving as intended in 2.468s,
**carried unchanged across this correction**. Capability **capable, zero
denials**, bound to the new manifest, root absent. Predecessors re-verified:
`execution-350529` 78/78, `execution-348852` 73/73, `execution-348802` 72/72,
`execution-348718` 71/71 — zero failures, all unedited.

### The gap I understated at claim348929

I reported that neither preflight establishes that the staged source can
**import** the controller it pins. The import was only the **first of three**
refusals in that window. **Two consecutive selected invocations died inside it**
— run348852 at line 554, run350529 at line 564 — with every preflight passing
before both. This claim closes that specific window: `bind` performs
`verify_imported_sources` through the module the controller runs, and the
startup check runs all three functions against the composed packet with the
counterfactual recorded. Whether any of it should become packet machinery or a
probe is the reviewer's and the owner's call; `probe.py` is untouched.

### Cost

Measured subtotal **about 6.3s** this claim plus the run's ≈2s: input check
0.06 twice, capability 0.017 twice, preparation at the selected root 1.085,
boundary preflight 0.332, deferred-import check 0.321, **the run ≈2**,
collection ≈0.01, preparation of the successor 1.050, probes 2.468,
startup-verification check 0.330 and its counterfactual 0.328, seal and
both-ways ≈0.1. Child cumulative **about 3011s plus unknowns**; the parent's
≈2253s stays with the parent. Campaign provider served ≈4673s, controller
elapsed ≈4764s; **three startup failures served zero provider seconds**. Gate
measurements 3, the last one passing. Product tests executed by me on the host
**0**; Jobs 0; attempts 0; runtimes 0; provider calls 0; engine calls 6
read-only across two capability checks and one boundary preflight; credential
values read 0; version-control mutations 0; old-instance mutations 0.

### Handoff

Returned to `baton.bug`: the selected invocation is **consumed and reported**,
and its correction is prepared and sealed for independent review and a new
exact selection. Remaining scope unchanged and still one cohesive correction:
R1, R2, the complete five-module gate with no skips, the extended
`W341357-VERIFICATION.json`, then independent producer byte review and
acceptance. Parent W333486 remains blocked by341370. **Three selected
invocations in a row have now failed at startup without reaching a provider; I
have closed the window all of the last two were in and claim nothing beyond
it.**

## 2026-10-22 — baton.claude, claim352586 — THE SELECTED RUN STARTED, AND THE ENVELOPE PERMISSION IS LIVE

Claimed W341357 at snapshot352586 after reading current canonical state
(queued, unclaimed, routed `baton.impl`, `last_change_seq 352577`, open
blockers 0, `pickup overdue`), the complete handoff through `work-events` (90
events, `next_after` null — no pagination remaining) and thread T341357 in full
(**6 messages**, `last_seq 352206`, one more than the last claim read: the
owner shutdown/preservation requirement M352206). Read
`review-2026-10-22T14-45-31Z.md`, the current `FINDING.md` and `PLAN.md`,
`COMMANDS.md` and `OPERATOR.md`.

**Owner reroute352577 selected exactly one invocation** of `execution-352156`,
manifest `9bda87e4ad655da1c1a452b901f994c5da7b4647d1a64c02ab2287866086dc2e`,
accepted by `review-2026-10-22T14-45-31Z.md`, at the fresh root
`/home/sl/baton-instances/durable-capture-w341357-352156`, with the selection
**pinned in `FINDING.md` and `PLAN.md` before execution**, pre-stage
capability then post-bind actual-boundary preflight, the generated enforced
`AUTHORING-COMMAND.json` only, bounds 3600/30/4800/60, stop at original origin
+ 4740 and expiry + 4800, one invocation, no retry, report-and-hold.

### Revalidated before acting

Manifest `9bda87e4…` **exactly as selected**. Seal 80 of 80, zero failures,
**both ways** — 81 files on disk, nothing sealed-but-missing, nothing on disk
but unsealed except `SHA256SUMS` itself. Input check exit 0 in **0.067s**: 115
manager files, 3 supervisor files, 2 preparation inputs, 68 task inputs, 59
decision snapshots, 4 checkout documents, 1 pinned controller, 1 pinned
shutdown helper, 2 pinned recovery inputs, 1 gate module still owed. It
reported `DECISION-SOURCE DRIFT` on `FINDING.md` and `PLAN.md` — the
reviewer's own post-sealing updates — **reported and deliberately not
resealed**, because resealing would change the manifest the owner selected.
Proposed root absent; the other ten W341357/W333486 roots all present and
untouched.

**The pins I was told to write add to that same reported drift, on purpose.**
Owner352577 requires the selection pinned in `FINDING.md` and `PLAN.md` before
execution, and those two files are exactly the two the packet snapshots. So I
appended an attributed implementer section to each, naming the selection, the
revalidation and what it does not establish, and left the sealed snapshots
alone. Live digests after the pin: `FINDING.md`
`c6a03479afeb45a14f8083fefa2d5eef1edafed6f509cf59e41d6fa02826dc5a`, `PLAN.md`
`0cef8a875dad42ba629609c82b6519c7d8b26ad14f613c8e1827e74e1d2b3fba`. The
reviewer owns the rest of both documents and I changed nothing else in them.

**Pre-stage capability: capable, zero denials, 0.081s**, bound to that
manifest — engine answers, image `baton-v12-claude-worker:w239528-244216`
config digest `sha256:c862c055…` equal to the pin, runtime binary `04aa459a…`
equal to the pin, distro present, credential reference `w202663-development`
present in `/home/sl/.baton/credential-sources.json` with provider
`operator-file` and its backing file present, **no credential value read**,
root absent.

**Both checks are REGENERATED, not recovered.** M352206 announced the `/tmp`
wipe and it happened: the author's claim352156 copies of the capability check
and the boundary preflight are gone, along with `/tmp/w341357-preflight11` —
which is also why the reviewer regenerated preparation rather than inspecting
that tree. I rewrote both checks against the same packet pins and the composed
packet and say so in each report, rather than presenting them as the
historical bytes.

### Stage, bootstrap, bind

Stage **0.076s**, bootstrap **0.649s**, bind **0.377s**, **all status 0**.
Authority `33bac7926fdd4ddfb15a3eae7fb4f6eb`, composed packet
`bab5b3e828e07052431c4e73e622a6b462ff61c9e97a5e42f0a2c390c3b39336` — both
different from the reviewer's and from the preflight's, as `OPERATOR.md` step
2 says to expect, because `--no-repositories` generates this instance's own
authority uuid and `bind` derives the Work id from it.

Read back from the bound documents rather than asserted:

- `PREPARED.json`: work **`W341357`** (not the scaffold's parent id), state
  `prepared-not-executed`, `start_authorized` false, `start_selected` false,
  `composer_start_is_unenforced` true.
- 115 manager members, and the member **set and every digest equal to the
  accepted W348979 binding's `manager_files` as a whole** — set equality and
  zero digest disagreements, checked against `HOST-POLICY.json` at
  `8309fd6e…`. Every staged byte on disk re-hashed against the packet's own
  map: zero disagreements.
- `packages` exactly `["baton_v12","tools"]`.
- **The one correction, read back:** `supervisor.path` is
  `<root>/code/v12/python/tools/authoring_baseline.py` — the module the
  controller actually imports — at `8e5987f5…`, which is also the digest the
  binding declares for the deferred dependency. The staged `supervisor/`
  directory copy is still present at the same `8e5987f5…` as provenance, and
  **the digest pin did not move**; only the path this packet names changed.
- Controller `248ee9ed…` and shutdown helper `af9e5ea6…` equal to the
  binding's own declarations for both.
- 68 `fixture.files`, **all 68 verified** against `fixture.source_root`
  `/home/sl/src/baton`, zero mismatches, including `recovery-345822/`'s
  `candidate.patch` at `294368c5…` and its `INDEX.json` at `70e1f2b1…`.
- `task.json`: `task_id durable-capture-w341357-352156`, `declared_base
  bc925cf5c62d69426ed5862af4d41f4d2a967b0f`, verification argv naming exactly
  the **five** gate modules and admitting no skip.
- `submission.json`: provider 3600s, verification 30s, `terminal_policy
  report-and-hold`, one implementation stage, profile
  `claude-fresh-implementation`.
- Bounds 3600/4800/60, one invocation, retry false.

**The generated enforced command agreed with `COMMANDS.md` step 4
byte-for-byte** — working directory, all three environment assignments and the
argv, with `python3` resolving to the `/usr/bin/python3` the generated document
names. I used only that document.

### The actual boundary preflight, and a defect of mine inside it

**Available, zero denials, 0.379s**, child status 0. A child spawned with the
controller's exact working directory, `PYTHONPATH` and
`BATON_V12_STAGE_EXECUTION_CONFIG` **read from the generated
`AUTHORING-COMMAND.json` rather than retyped**, calling the staged
controller's own `bounded_engine`, so the engine call is a grandchild — the
depth the real run uses. `baton_v12` and `tools` both resolved inside the
staged source. Engine version status 0 in 0.045s; image inspect status 0 in
0.005s returning `sha256:c862c055…`, equal to the pin, **at the boundary**.

And `main`'s first three statements, in `main`'s order, against this composed
packet: **`held_packet`, `verify_imported_sources` and `verify_controller` all
accept, in 0.00734s.** That is the window run348852 died in at line 554 and
run350529 died in at line 564. It stops at `main`'s next statement, the
authoring lock at `authoring_enforcement.py:566` — no lock taken, no store
opened, no image verified by the controller, no Job, no container, no provider
call, no credential value read.

**My own defect, caught by running the check rather than reading it.** The
first boundary report came back `denied` on both engine probes with
`AttributeError: 'dict' object has no attribute 'returncode'`. The denial was
false and it was mine: `single_worker._engine_run` returns a **mapping** with
`status`/`stdout`/`stderr`, and my harness assumed a `CompletedProcess`. Had I
believed it, I would have reported a capability denial for a probe that
actually succeeded and stopped the turn on my own bug. Corrected to read the
mapping, and the corrected report records the return keys it actually saw.

### The run

Launched **once**, at **2026-10-22T15:23:19Z**, pid 11500, using only
`packet/AUTHORING-COMMAND.json`'s `start` with its generated environment and
working directory. `packet/commands.json`'s `start` was not used.
`evidence/run-352156/LAUNCH.json` records the argv, environment, cwd and pid.

**It started.** Four selected packets in a row never produced a turn and three
of those died in startup; this one is past that window. Thirty seconds in,
read from the live root rather than inferred: the authoring lock exists,
`control.sqlite3`, `jobs.sqlite3` and `integration.sqlite3` are open beside
bootstrap's `authority.sqlite3`, `packet/workspaces` is created, a manager
status snapshot is publishing, and the engine reports one container up on
image config `c862c055…` — the pinned worker image.

**THE ENVELOPE PERMISSION IS LIVE, AND THIS IS THE FIRST RUN THAT PROVES IT.**
Read from the manager snapshot, not from a document: envelope `started_at`
**2026-10-22T15:23:20.487Z** and `stop_at` **2026-10-22T16:42:20.487Z** —
origin + **4740s** to the millisecond. The attempt's token was acquired at
15:23:25.388Z with `expires_at` **2026-10-22T16:43:20.487Z** — origin +
**4800s**, `expired` false, carrying the job's 3600s provider and 30s host
verification boundaries and the 60s cleanup reserve. The 900-second default
that cut off run340352 at 904.78s and run341360 at 905.18s **did not apply**:
W333485's accepted correction, consumed through W348979's corrected binding, is
doing what it was accepted to do. Attempt
`attempt-1fb667f9830837e5d30365fa94c79e8374b347c957f2fb8b86427150f234390d`,
runtime `11a76501b451966c9732ff4c2169ef2d382b1c366a132435187350c29ca148fb`,
`execution_runtime running`, assignment generation 1 to `baton.impl`,
`work_ref 33bac792-W1`, domain `workspace:66306:3314008`.

**What that is not.** A started controller and an acquired token are not a
completed turn, not an accepted candidate and not proof that R1 or R2 were
reproduced or corrected. The gate passing in run345822 is exactly why
acceptance was withheld. The run's own result, and the host-side collection
that only exists after the worker is gone, are the evidence — not this.

### The result: completed on its own, R1 and R2 both reproduced then corrected

**The run ended on its own.** Controller `state completed`, `child_started`
true, `child_exited` true, **`child_status 0`**, `elapsed_seconds`
**2689.0656055909994**, `faults []`, `operator_signals []`, `recovery_only`
false. Workload `state settled`, `stopped completed`, `served_seconds`
**2689.199099617** against the 3600s provider ceiling — **910 seconds of
margin** — `finished_at 2026-10-22T16:08:09.721Z`, `stage_states
{implementation: completed}`, one admission, one admitted attempt, zero
`gate_refusals`, zero `held_because`, zero `interruptions`, zero
`cleanup_sweeps`, zero `uncertainty`, zero `unexpected_attempts`, zero
`shortfalls`. The attempt's token: `expired` **false**, `returned` **true**,
**`renewals` 0**, `expiry_judged_at` null. Runtime `destroyed`, cleanup
`retained`, observation `absent` because *"the engine answered … No such
container"*. No fault anywhere in any of the five artifacts.

**The envelope permission is no longer a document claim.** Origin
`2026-10-22T15:23:20.487Z`, `stop_at` `2026-10-22T16:42:20.487Z` = origin +
4740s, token `expires_at` `2026-10-22T16:43:20.487Z` = origin + 4800s, and the
turn used 2689s of it with **zero renewals**. Under the retired 900-second
default this turn would have been cut off at about 900s — exactly as run340352
was at 904.78s and run341360 at 905.18s — **and it would have lost both
corrections**, because the five-module gate alone was not measured until well
past that mark. W333485's accepted correction, consumed through W348979's
corrected binding, is what made this turn possible.

**`collect.py` step 5a, read-only, 0.017s:** five of six artifacts
**present** — workload outcome, controller report, manager snapshot, shutdown
progress, authoring log — `isolated_failures []`, every one of the controller's
four self-named links `found`, no artifact carrying its own temporary, and the
sixth, `shutdown_request`, **absent**, which is correct and names no cause: the
turn returned on its own so no bounded shutdown was ever requested.
`publication_timeout.established` is **false**, which for this vehicle means
*nothing on disk could tell you either way* and **not** "no timeout happened";
there are no parsed publication faults, no other timeouts observed and no
uncorrelated ones. The shutdown progress file names `final enforcement
publication` as the last step **entered**.

**The candidate.** Base `bc925cf5c62d69426ed5862af4d41f4d2a967b0f`, head
**`2d313602e0a82a365f3b0239a9ce1ba91f62c56a`**, content digest
**`sha256:c509bd42d5430dcee4d1b12ded916cdfff903d31754df96867d9cb4a561a8d47`**,
434587 bytes, four custody entries, `state valid`, `disposition completed`,
**`verification passed`**, `acceptance` **`unobserved`** — which is the manager
saying what it is: a retained candidate nobody has accepted. Eleven changed
paths, exactly the candidate's eleven: the four producer files
(`failure_cause.py`, `intake.py`, `attempts.py`, `documents.py`), the focused
producer test module, the three fixture inputs, `test_intake.py`,
`test_maintenance.py` and the extended `W341357-VERIFICATION.json`.

**R1 and R2 were each REPRODUCED AT THE PRODUCTION BOUNDARY BEFORE being
corrected**, which is what `TASK.md` item 1 required and what no earlier turn
had done. From the run's own report:

- **R1** reproduced at `intake.settle_revoked_resource` over a real governed
  generation — claimed, activated, started, runtime attached, token acquired,
  expired by a clock that moved, revoked through the product's own
  `tokens.workspace_governance().revoke`. A fresh A→B→A wrote revisions 0 and 1
  and then **wrote nothing** for the third fresh observation, so the reader
  answered `uncertain-observation` about a runtime just observed quiescent; the
  reverse order left **a stale positive current** while the runtime was
  observed running. Corrected by sequencing an observation on the account it
  was taken after — `supersedes`, which already meant that — in four branches,
  with no contract change and no call-site change. Red first: the existing
  replay case failed `assertEqual(again, first)` on the operation id.
- **R2** reproduced **on every acting path** by injecting
  `ContractRefusal('unavailable','transport')` into `store.transact` for
  `attempt.cessation-outcome` **and nothing else**, placed **after the durable
  intent commits** so the cases cannot accidentally re-prove the previous
  Work's intent-ordering property — every case asserts the intent reads back
  and the outcome does not. Six boundaries measured across reclaim, settlement
  and cancellation, including a dict shape, a closed document and an exception.
  Corrected through one owner, `carry_degradation`/`degradation_of`, with the
  original engine refusal's category, code and message asserted unchanged
  byte-for-byte. Red first: **10 failures** with R1 in place and the R2 call
  sites untouched, with the one path that already carried the member passing
  red — which is what makes the other ten about the dropped return and nothing
  else.

**The complete five-module gate, no skips:** 864 tests OK in 11.026s at the
applied candidate *before* any change, then **892 tests, 0 failures, 0 errors,
0 skips, OK, exit 0, 11.152s** after both corrections, four repetitions between
11.073s and 11.181s, **18.8s of headroom** under the 30s ceiling. Only
`test_attempt_failure_cause` moved, and only upward.

### What I verified myself, and how — no host product test

**I ran no product test.** There is no product-test authority for this Work and
the classification belongs inside the run. What I did is **read-only text
analysis** of the published bytes, and `GATE-CLASSIFICATION.json` labels it as
exactly that rather than as confirmation that 892 tests pass:

- The sealed content manifest agrees **member by member** with the four custody
  files I copied — `change.patch` `044d58bc…`, `objects.bundle` `0a5fdecf…`,
  `result.json` `bc35d7c5…`, `verification.txt` `2b49d85a…` — under tree digest
  `c509bd42…`, and the patch's 11 `diff --git` sections equal
  `result.json`'s 11 changed paths.
- **The focused module's case counts reproduce independently.** Counting
  `+def test_` names in `recovery-345822/candidate.patch` and in this run's
  patch gives **63** and **91**, delta **+28** — the run's own per-module
  figures — and **every one of the 63 candidate case names is still present**.
  Nothing was deleted to make room.
- **The one existing case that changed is input-only, as reported.**
  `test_a_REPLAY_of_a_SUPERSEDED_revision_writes_NOTHING_MORE` now passes
  `observed_after=one["supersedes"]` and keeps a binding it used to discard;
  its name and **all four assertions are byte-identical**, with a docstring
  paragraph added. One note for the reviewer rather than a claim of mine: the
  coordinate supplied is that record's own `supersedes`, so for revision 0 it is
  whatever an empty chain's tip is — worth reading in the recorder's bytes.
- All **11** evidence copies re-hashed against their sources in the live root:
  **11 of 11 agree**. 28 files indexed with digests in
  `evidence/run-352156/INDEX.json`.

### What this run did NOT establish, and one reporting gap

The run's own report lists what it did not establish and I am not softening any
of it: **no acceptance**; not the full joined twelve-module gate, the
installed-bundle proof or the ordinary status/report integration, all of which
parent W333486 owns and none of which was run; not a live engine, provider or
container inside the reproductions, which drive the production entry points
with the adapter, agent and governance injected at the same seams the
already-accepted cases use; not the cause of what filled the mount in run345388,
which remains **unknown** and which the turn explicitly refuses to let its own
`test_secrets` storage finding stand in for; not the **194** pre-existing
out-of-gate failures, measured byte-identical in both arms across eleven
further modules and therefore unmoved — and also unfixed and uninvestigated;
and not whether the parent's seam reads the degradation off an exception, since
no downstream consumer of that shape exists yet.

**One reporting gap I found rather than was told, and it is the turn's.**
`TASK.md` item 6 asks the turn for the expiry and cessation facts **it
positively observed from inside**. The extended report's top-level
`lease_and_cessation_facts_POSITIVELY_OBSERVED_FROM_INSIDE` section still
describes the **first** turn — 549s elapsed, a 900-second lease, the 600/720
targets — and the turn did not add its own. It is disclosed collectively (the
new section opens by saying the sections above are the first turn's and are left
as they were), so this is a missing section rather than a false one, and the
turn's correlation keys and monotonic origin are recorded. But the 900-second
figure in that older section is retired, and a reader who stops there would take
it as current. Flagging it rather than editing the candidate's bytes, which are
the reviewer's to judge.

A third classification defect was found while reproducing R2 — a transport
refusal reported as a collision — and corrected with a case; the turn reports it
as observed rather than looked for, and claims **no** production occurrence.

### Cost and preservation

Measured host-side subtotal this claim: input check 0.067s, capability 0.081s,
stage 0.076s, bootstrap 0.649s, bind 0.377s, boundary preflight 0.379s, collect
0.017s — **about 1.65s** — plus one discarded boundary pass that failed on my
own `CompletedProcess` assumption, plus the read-only analysis above. **The run
itself: 2689.07s controller elapsed, 2689.20s provider served.** Child
cumulative: measured subtotal about **5702s** plus unknowns (about 3011s
before this claim). The parent's about 2253s stays with the parent. Campaign
provider served now about **7362s**. Gate measurements 5, the last two passing.
**Product tests executed by me on the host 0**; Jobs 1; attempts 1; runtimes 1;
provider calls 1; engine calls 6 read-only across one capability check and one
boundary preflight, plus the run's own; credential values read **0**;
version-control mutations **0**; old-instance mutations **0**; retries **0**;
rebinds **0**.

The new root `/home/sl/baton-instances/durable-capture-w341357-352156` is
preserved unmodified after collection, and all ten earlier roots are untouched.
Every artifact a later turn needs is in `evidence/run-352156/` under the
canonical dossier rather than only in `/tmp`, per M352206: the five published
final artifacts, the candidate's four custody files and its sealed manifest, the
extended `W341357-VERIFICATION.json`, the collection, both preflight reports
and the three check programs, the input check, the three preparation logs,
`PREPARED.json`, the generated `AUTHORING-COMMAND.json`, the launch record and
the controller's own streams.

**The plain statement this turn is entitled to make and no more:** the selected
invocation started, held its envelope-derived permission for 2689 seconds with
no renewal, reproduced both withheld defects at the production boundary before
correcting either, passed the complete five-module gate with no skips, and
retained a digest-bound candidate the manager marks `verification passed` and
`acceptance unobserved`. **Nothing here is accepted.** R1 and R2 now need
independent **producer byte review** — the thing every earlier turn was short
of — and parent W333486 still owns the joined status/report integration, the
twelve-module gate, the installed-bundle proof and final acceptance under
dependency341370.

## 2026-10-22 — baton.codxpc claim353177: isolated replay correction started

Read current canonical claim/handoff/thread and owner host exception; allocation pinned in PLAN before execution. Existing candidate and prior evidence preserved. Revalidating exact input bytes and recorder branch before a red regression. No shared source or Git mutations.

## 2026-10-22 — baton.codxpc claim353177: correction ready for independent review

Owner-host exception used only for the isolated replay correction. Reproduced both original and middle identity failures before moving coordinate-aware replay ahead of value-only tip dedup. Two additive tests; all91 existing producer methods unchanged. Focused93 OK/no skips; exact retained five-module gate894 OK/no skips (11.196s unittest). Full details and reporting clarification: evidence/correction-353177/REPORT.md. No shared product integration, Git mutation, new Job/provider/engine or old-instance mutation.

CANDIDATE.json binds11 full candidate paths, manifest0143f146b8f7562ef60f22c4f0984670301f338e2687af806ebff6df2e08b807; full patch ecb9e391455a5f6626bf2ffb07f0d85a237ae909dc3b7012a1b326a393f3d6f8. Delta only failure_cause.py and test_attempt_failure_cause.py; nine retained sections verbatim. Full patch reconstructed with no fuzz and all11 resulting hashes matched. Original candidate2d313602 and all evidence preserved. New process verification 12.544237s; cumulative child about5714.54s plus preserved unknowns and unmeasured preparation/read/hash time; parent2253 separate, campaign provider7362 unchanged.

Current position: claim353177; handoff353080/reroute353174 and thread through353169 read, no pagination remaining. Passing to baton.bug for independent acceptance; parent status/report/full gate/bundle and serial attempts.py integration remain outside this correction. Producer acceptance and human checkpoint remain pending.

## 2026-10-22 — baton.codxpc policy acknowledgement, poke353199

After pass353227, canonical snapshot353231 confirms W341357 is claimed by baton.rvpc for independent review; baton.codxpc holds no claim on it. Read current AGENTS temporary direct development workflow, W321608 current FINDING/PLAN and complete T321608 through M353196 (no remaining pages). Apply the October22 standing direct-development ruling at this safe handoff boundary: routine authorized implementation/correction and focused deterministic verification use direct execution under v11 claims, without mandatory v12 packets/Jobs or a per-correction host exception. This supersedes the prospective execution-method/exception-expiry assumptions in my earlier checkpoint, not its historical authorization or evidence.

Candidate/evidence correction-353177 remains unchanged and under independent review. No new execution, tests, claim, integration, graph change or live operation; cumulative verification remains about5714.54s plus recorded unknowns/unmeasured overhead. Preserve separate W339626 ownership, all retained candidate provenance, acceptance and human Git boundaries. Any next correction begins only after a canonical implementation handoff and successful claim. Native v12 delivery remains the target; v11 remains coordination authority.
