# W341357 durable typed failure capture and replay — the producer slice

## This is a BOUNDED CHILD SLICE, and it starts from preserved partial work

Private committed base `bc925cf5c62d69426ed5862af4d41f4d2a967b0f`. Parent
W333486 owns the ordinary status/report integration, the full joined gate, the
installed-bundle proof and final acceptance, and **is serially blocked on you**.
You own one finite thing: **the producer contract — durable typed cessation
capture and truthful replay at the reclaim, settlement and cancellation
boundaries — plus its focused deterministic verification.**

**Read `RECOVERY.md` first.** It records the two parent runs, exactly which
bytes you are recovering, which bytes are deliberately left for the parent, and
the one defect already found in what you are given.

**Step one, before any design thinking:** apply the producer recovery input into
your own workspace, from the read-only mount:

- the tracked part, `/input/source/work/records/2026/10/finding-v12-attempt-failure-diagnostics/findings/finding-durable-failure-capture/recovery/producer.diff`,
  applied with the repository's patch-applying tool — it touches
  `worker_manager/documents.py`, `intake.py` and `attempts.py` only;
- the two new files, copied verbatim from
  `/input/source/.../recovery/v12/python/src/baton_v12/worker_manager/failure_cause.py`
  and `/input/source/.../recovery/v12/python/tests/manager/test_attempt_failure_cause.py`.

Every one is a pinned task input with a digest `verify-inputs.py` and
`prepare.py` both cross-check, including against the parent evidence it was
derived from and against the reviewer's independent hashes.
`recovery/INDEX.json` is the derivation record.

**These bytes are UNVERIFIED RECOVERY INPUT.** Run340352 froze no result, so
nothing accepted them: no candidate, no proposal, no verification. They are
**useful unaccepted work, not a certified design.** You are expected to keep
what is right, fix what is wrong, and change anything the accepted outcome
requires — the preservation language here is about not restarting from an empty
tree, and it **does not** protect a defect or override standing test authority.

## The milestone, and it is these five things

### 1. Fix the collision-as-authorization defect, with a failing case first

`RECOVERY.md` has the full account. `ensure_cessation_intent` treats
`ContractRefusal(code="operation-collision")` as proof that a durable intent
exists and as permission to order the effect. Against the committed store that
is backwards:

- `store.transact` → `store.replay` **returns the recorded value** when the row
  exists with a **matching** signature, so an **exact replay never raises**;
- `replay` raises `operation-collision` **only** when the row exists with a
  **different** signature or kind;
- `_identity` deliberately keeps the runtime **out** of the operation id so the
  runtime and correlation ride the **signature**.

So a collision means **an intent exists for this act and it describes different
operands** — and that is the one case where it is not authorization for the
effect now being ordered.

Required:

- **a deterministic case that fails on the recovered bytes first**, driving
  `record_and_raise_cessation_intent` to a genuine signature collision — same
  attempt, assignment, start operation, component and generation, **different**
  token-bound runtime or correlation — and showing the current code permits the
  effect. Write it, see it fail, then fix it. A fix with no prior failing case
  does not establish the defect existed;
- **resolve the mismatch explicitly.** Either refuse — the committed intent does
  not describe this effect, so no effect is ordered — or reconcile it in a way a
  reader can see, with the facts compared. `_same_account` already exists in the
  file and is applied to the outcome chain; it was not applied here. Do not
  invent a second comparison idiom if the existing one fits;
- **keep exact replay working and prove it separately.** Exact replay and
  changed-signature collision need **distinct** acceptance evidence, and a
  single case cannot stand for both.

### 2. Durable intent before the effect, on all three boundaries

The recovered `ensure_cessation_intent` raises when nothing was made durable,
which is the right shape. Carry it through and prove it where the effects are
actually ordered:

- **cancellation** — `attempts._order_quiescence`, before `agent.cancel` and
  `adapter.stop`;
- **settlement** — `intake.settle_revoked_resource`, before `govern.release`;
- **reclaim** — `intake.reclaim_expired_resource` and its own release path.

Required: a recording failure **observably prevents the effect**, under
interruption and under a crash between the intent and the effect. **A reportable
degradation is not a substitute for durable pre-effect intent** — if the intent
is not durable, the effect is not ordered. And this weakens **no** existing
fencing or cleanup: the Authority fence is taken before the cancellation path
reaches here, and on the settlement path the release simply has not happened and
the generation stays held. Prove both of those still hold rather than asserting
it.

### 3. Separately typed outcome, with a replay history that stays honest

The recovered `cessation_outcome_operation_id` revision chain with `supersedes`
is the right answer to "an uncertain first observation must not be an enduring
substitute for a later positive one". Finish and prove it:

- an **uncertain-to-positive** history keeps **both** records, names which is
  current, and does not rewrite the first;
- a **changed** observation does not collide with revision 0;
- the typed outcome stays separate from the derived cessation, so **no caller
  can file a stop failure as a cessation**;
- **absent is not quiescent**, and a **known typed stop/engine failure** is not
  an **unknown cessation**.

### 4. The read contract, versioned and secret-safe

The reader must distinguish, as four different answers and not three:
**unknown**, **known typed failure**, **intent-only** (ordered, no outcome ever
recorded — the crash case the intent exists for), and **positively observed
cessation**.

- attribution is exact: attempt, fixed assignment, start operation, component,
  domain, generation, **token-bound** runtime and operation identity;
- **token-bound-before-attachment** is honoured — the runtime comes from the
  token's bound container, which can exist while the attempt row's own
  `runtime_id` is still `None`;
- **completion is attributable on either release path**, from the record both
  write;
- an **older record may honestly lack diagnostics** and must read as a bounded
  `unknown` that names what is absent — and an **unsupported document version
  must not be silently accepted**;
- every emitted field is bounded and allowlisted: **no credential, environment
  value, private transcript, provider text or arbitrary exception repr**, and a
  secret canary proves it;
- publish the **versioned producer shape and read API** explicitly, because the
  parent composes ordinary status and the report over exactly this and is
  waiting for it.

### 5. Report what you can actually observe

Unchanged, and both parent runs proved it necessary: the controller report, the
workload outcome and the shutdown progress file are published **after** your
turn ends. You cannot see them. Name them structurally unavailable to the worker
rather than reporting them present or absent. Your half is your progress per
item, the retained candidate with exact paths, which tests you ran and what they
measured, and the lease and cessation facts you **positively observed from
inside**.

**Do not plan around expiry, in either direction.** Run340016 finished on its own
at 869.3s; run340352 was cut off at 904.78s with nothing frozen. **Freeze early
and often** — a result that exists is worth more than a better one that does
not. If you must choose, land items 1 and 2 with their evidence and say
explicitly what remains.

## Verification: focused, deterministic, and inside this Job

`FINDING.md` keeps the full joined gate with the parent, so **this slice's gate
is five producer modules, not twelve**:

```
tests.manager.test_intake
tests.manager.test_attempts
tests.manager.test_maintenance
tests.manager.test_contracts_inventory
tests.manager.test_attempt_failure_cause
```

The first four exist at the base and must still pass. The fifth **arrives with
the recovery input** and is yours to extend — so the gate fails until you have
applied the recovery and made it pass, which is the point.

**This is the first honest chance this campaign has had of fitting the 30-second
`verification_command_seconds` ceiling**, because the parent's twelve-module argv
measured 13.642s of existing modules before the new ones existed. Report the
measurement either way: per-module seconds and the total. If it does not fit,
that is a real finding with numbers, not a failure to deliver — and **do not
weaken a test, remove coverage or relax an assertion to obtain a pass.**

Cover, deterministically and with no live provider:

- intent ordering under **recording failure** and under a **crash** between
  intent and effect, on all three boundaries;
- **exact replay** versus **conflicting runtime/correlation** collision, as two
  separate cases;
- **token-bound-before-attachment**;
- **stop failure versus unknown cessation**; **absent versus quiescent**;
- **uncertain-to-positive** observation history;
- **reclaim and settlement release attribution**, on both paths;
- **secret-safe bounded fields** with a canary, and an **honest old-record
  unknown**;
- and that every read **mutates nothing** — no claim, renewal, reconciliation,
  acknowledgement, retry, store creation or migration. Normal SQLite read-only
  sidecar behaviour is allowed.

## Boundaries

- **No edit to anything under `/input`.** The mount is read-only on purpose.
- **Producer paths are your allocation**: `worker_manager/failure_cause.py`,
  `documents.py`, `intake.py`, `attempts.py` and focused producer tests. These
  identify ownership, **not an exclusive edit restriction** — if the accepted
  outcome needs another shared-contract path, declare it rather than working
  around it.
- **Do not carry the parent's downstream partial work.** The `job_manager`
  status seam, `tools/attempt_diagnostics.py`, `stack_command.py`, `stack.py`,
  `worker_visibility.py` and their tests are the parent's and stay in the parent
  evidence. The parent is blocked on you, so there is no concurrent edit owner —
  which is exactly why you must not take its work.
- **Do not touch the vehicle**: `tools/authoring_enforcement.py`,
  `tools/authoring_shutdown.py` and the supervisor baseline are the accepted
  corrections you are running inside.
- **Preserve both completed runs and every parent packet.** No rerun, no
  recovery of an old instance, no mutation, no credential or transcript read.
- No image build, no container, no engine call, no provider call inside this
  task; no host product edit outside the private checkout; no integration, no
  self-acceptance, no deployment, no mutating version-control operation beyond
  what the line profile itself performs.
- Independent review and the parent's joined acceptance remain required. **A
  retained candidate is not an accepted one.**

## Honesty obligations

The lease is 900 seconds and enforced. It held on one parent run and fired on the
other, so **plan for the budget and pre-write no narrative either way**. If your
turn is cut short, the retained candidate and an honest account of what is
delivered and what is not is the deliverable.

Report which items are delivered, which are partial, which are untouched; which
tests ran and what they measured; and cumulative verification spending. Do not
label an environmental failure as formal success, and **do not weaken an
assertion to obtain a pass.** A failing gate honestly classified is worth more
than a passing one bought by deletion, and the review will check for exactly
that.
