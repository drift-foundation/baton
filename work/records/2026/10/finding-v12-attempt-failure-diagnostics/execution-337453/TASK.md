# W333486 actionable attempt failures and one read-only diagnostic report

Private committed base `fb48797903160aa764229d58f3a5beaf29648bfc` — the human
checkpoint that integrated the accepted manager-guard correction, which itself
sits on the accepted authoring-enforcement correction. The
read-only nominated source at `/input/source` carries this packet's input
documents. They are **read, never edited and never transcribed**; the mount is
read-only on purpose and this task restores nothing into the private checkout.
There is no preserved candidate buffer: every byte this correction starts from
is committed at the declared base.

**This packet supersedes `../execution-333504`, `../execution-333707` and
`../execution-334663`**, all preserved unchanged. The first two pin the old
unenforced supervisor; the third was actually selected and **failed at
startup** because the controller composed two managers for one workspace.
`FAILURE.md` is that account and `ENFORCEMENT.md` is the current account of
the vehicle. Read both — this vehicle has been run once already.

Read these first. The decision documents are **immutable snapshots** taken at
claim334663; `decisions/INDEX.json` carries each one's source path and digest.

From **this packet's directory on the mount** — digest-pinned as the packet's
`fixture.files`:

| document | why |
| --- | --- |
| `decisions/FINDING.md` | the accepted outcome, the preserved axes, the ownership boundary, and its four dated supersessions |
| `decisions/PLAN.md` | the current milestone |
| `decisions/review-333812.md` | the review that accepted the task at design level |
| `decisions/review-334776.md` | the review that accepted the previous packet, and corrected one prose overstatement this task's item (b) must keep exact |
| `decisions/owner-failure-evidence.md` | the attributed incident: exact identities, the null readers, and what is **not** established |
| `decisions/enforcement-review.md` | the independent acceptance of the authoring correction whose bytes you are building on |
| `decisions/enforcement-integration.md` | how those bytes entered the tree, and its instruction to rebase any overlapping candidate onto them |
| `decisions/guard-review.md`, `decisions/guard-integration.md`, `decisions/guard-integration-result.json` | the manager-guard correction this base carries, and the reusable real-process proof |
| `decisions/failed-run-INDEX.json` | the first actual execution of this Work and its startup failure |
| `FAILURE.md` | what happened when the previous packet was started, and what the correction changed |
| `ENFORCEMENT.md` | the vehicle, the 900-second disclosure, the composer's wrong start command, and the two measured gate limits |

From the **private checkout at the declared base**:
`v12/DESIGN.md` (TOK-*, HOST-*, REC-4), `AGENTS.md`,
`work/records/2026/10/finding-v12-minimum-worker-visibility/FINDING.md`.

If a pinned input is absent or is not its declared bytes, **stop with the exact
failure**. No reconstruction from prose, from an older blob or from any
fallback.

## What is already recorded, and what is actually missing

Already journalled by its own owner, with the store's own `settled_at`:

- **`tokens.revoke`** journals `resource-token.revoked:<domain>:<generation>`
  with domain, generation, owner, bound container and the `expired_at` that was
  blown. Durable evidence — read it, do not ignore it.
- **`tokens.returned`** journals the return on **either** release path, which
  is what makes the completion instant recoverable regardless of which ran.
- `tokens.token_of` answers the whole token axis; `attempts` answers
  `attempt_runtime_of`, `attempt_activity_of`, `attempt_start_failure_of`,
  `attempt_preparation_failure_of`; the attempt row carries
  `execution_runtime`, `cleanup`, `observed_at`, `activity_bytes`,
  `activity_at`, `runtime_id`, `workspace_device`, `workspace_inode`;
  `submission.execution_limits_of` answers the ceilings.

**What is missing is the causal/operation/outcome composition**: which
component ordered this exact runtime stopped, under which operation identity,
with what engine outcome, and whether cessation was established. No record
carries that and no reader composes it. That is the gap.

The absence of a start-failure or preparation-failure record is **expected**
for these components, not proof of the proposed cause.

## REVALIDATE FIRST: the base moved under this design

The accepted enforcement correction changed `worker_manager/intake.py` and
`worker_manager/attempts.py`. Four changes bear directly on this task, and the
earlier revision of it was written against the old bytes. Read the committed
diff before you design anything.

### a. The runtime identity now comes from the TOKEN, not the attempt row

`reclaim_expired_resource` now takes `runtime_id = overdue.get("container")`,
refuses `identity-mismatch` when the attempt names a different one, and
derives its correlation id as
`reclaim_operation_id(dict(attempt, runtime_id=runtime_id), generation)`.

So **any identity you derive must resolve the runtime the same way** — from
the token's bound container, substituted into the attempt row exactly as the
reclaim does. An identity derived from `attempt["runtime_id"]` is wrong here:
the token may bind a container **before** the attempt attaches it, so that
column can be `None` while a real writer exists. The earlier revision of this
task proposed exactly that mistake; do not carry it forward.

### b. A replayed reclaim issues no effect at all

```python
before = None
if overdue["revoked"]:
    before, _value, _why = attempts._observed(adapter, runtime_id)
if before not in ("absent", "quiescent"):
    adapter.stop_expired(...)
if before != "absent" and remove is not None:
    remove(...)
```

**Read those two conditions separately — they are not the same test.**
`before not in ("absent", "quiescent")` guards the **stop**, and
`before != "absent"` guards the **removal**. So:

| observed `before` | stop issued | removal issued |
| --- | --- | --- |
| `absent` | no | **no** |
| `quiescent` | no | **yes**, if a removal capability exists |
| anything else | yes | yes |

**Only an exact absence skips both effects.** A quiescent container still
exists and still holds its mounts, so it is still removed.
`decisions/review-334776.md` corrects a prose summary of mine that said
otherwise; the committed code and this table govern, and candidate review must
check the **stopped-but-present removal** case separately.

So durable intent must be **idempotent and replay-honest**: the first account
stands, and a pass that ordered nothing must not read as a pass that ordered a
stop — nor may a pass that removed without stopping read as one that did
neither. Record what this pass actually did, not what the act is for.

### c. There is a new held outcome: the token-bound runtime ceased, the attempt never attached

```python
if attempt["runtime_id"] is None:
    return {"reclaimed": "held", ..., "container": runtime_id,
            "why": "the token-bound runtime ceased; attachment/activation "
                   "remains unresolved and the resource stays held"}
```

Cessation of the bound container is **established**, and the attempt's own
termination is still **unresolved**. Those are two facts and your vocabulary
must carry both without collapsing them.

### d. Cancellation is a SECOND terminating component

`attempts._order_quiescence` now resolves the token-bound container after
`request_cancellation` takes the Authority fence, refuses a conflicting
identity, and when neither an attached nor a token-bound identity exists
answers `quiescence_not_ordered` with *"the assignment is fenced but an
unresolved launch is not proof of cessation"*.

So an Authority-fenced cancellation can stop a runtime, and a composed cause
that only knew about expiry reclaim would report `unknown` for an attempt that
cancellation actually ended. **Attribute cancellation as its own component**,
with its own operation identity and its own typed outcome.

`decisions/enforcement-integration.md` is explicit: rebase any overlapping
`intake.py`/`attempts.py` candidate onto these integrated bytes, with
independent review, and never overwrite or silently resolve a conflict.
**Preserve their semantics.** You are adding attribution, not redesigning
cessation.

## The milestone, and it is exactly these five things

### 1. Capture the cause across the paths that actually run

The reclaim is not one act with one release:

- `reclaim_expired_resource` revokes, stops, removes, observes — then
  `_resource_cessation` (`intake.py:1122`) answers `None` unless a committed
  cleanup carries both halves of its proof, and `_custody_already_committed`
  answers `None` for a running attempt whose roots were never normalized. The
  ordinary outcome for a reclaimed live attempt is therefore **`held`**, and
  the reclaim's own `govern.release` is never reached.
- `tools/job_manager.py:_reclaiming` then calls
  `intake.settle_revoked_resource`, and **its** `govern.release`
  (`intake.py:5909` before this base; re-locate it) finishes the generation.

Requirements, implementation shape yours:

- Capture **eligibility and intent at the boundary that orders the effect**,
  durably, **before** the engine is asked — so a crash between an effect and
  any later record cannot lose the fact that this manager ordered this exact
  container stopped and why. Carry the attempt, its fixed assignment, the start
  operation, the domain, the generation, the journalled launch, the
  **token-bound** container and the correlation identity handed to the engine.
- Capture the **outcome** separately (item 3). Intent is not outcome.
- **Never infer a successful stop or a termination from intent, or from
  absence.** `decisions/review-333812.md` fixes the definitive semantics: an
  exact correlated positive runtime observation can prove cessation; intent or
  uncorrelated absence cannot.
- Make **completion** attributable on **either** release path. Prefer reading
  `resource-token.returned`, which both journal, over adding a third record —
  but a captured intent or outcome **must not disappear because completion
  happened later on the other path**.
- Do the same for **cancellation** (d): its own component, its own operation,
  its own outcome, and the fenced-but-unresolved case reported as the typed
  fact it is.
- Preserve replay and collision discipline: stable facts on the signature,
  facts-as-they-stood in the document, read inside the act. An exact replay
  returns the first account; a changed fact collides rather than rewriting.
  Respect (b): a replay that performed no effect records no effect.
- Recording must never replace the acting path's outcome: a collision or an
  unsignable operand is carried in the answer the way `_record_start_failure`
  carries one. The first account, written when the manager knew most, stands.

**Prove the actual composition and restart at the external-effect cuts** —
revoke→observe→stop→remove→observe→record→release, the reclaim→settlement
handoff, and the cancellation fence→resolve→stop sequence — by driving the
production composition, not a fixture standing in for it.

### 2. Public readers for whatever you record

Siblings of `attempts.attempt_start_failure_of`, held to the same discipline:
derive the identity from the row exactly as the recorder derives it — including
the token-bound substitution from (a) — decode through the journal's own
`replay` for the declared kind, own the document against its closed member set,
and **re-prove every fact the identity is derived from**. Absence is the
ordinary answer. A refused row under that identity is a collision, not
evidence.

### 3. A known failure is not an unknown

The manager may know a **typed stop or engine failure** while cessation remains
**unknown**. Both must be preserved and exposed separately. The vocabulary must
distinguish at least:

- cessation positively established by an exact correlated observation —
  `absent` and `quiescent` are **not** the same fact;
- **a known typed stop/engine failure** — refused, timed out, or could not be
  asked — carried with its typed category and code, cessation explicitly
  unknown;
- an **uncertain observation**: the effect crossed and what exists now could
  not be established;
- an **exact-runtime mismatch** — which the accepted bytes now raise as
  `identity-mismatch` on both the reclaim and the cancellation path;
- a **lost reply**: the act may or may not have crossed;
- **cessation established for the token-bound container with the attempt's own
  attachment or activation unresolved** (c);
- **fenced but not ordered**: cancellation holds the Authority fence and no
  identity resolved (d).

None may be reduced to "no termination evidence". A recorded manager failure
must be reported **even when the agent sent no final message** — the pilot's
exact shape.

### 4. One composed typed cause, with explicit unknown

A new public reader in the Worker Manager composing, from facts their owners
already hold and nothing it derives itself:

- **Which component, under which operation, when, with what outcome** — start
  failure, preparation failure, expiry reclaim, settlement, cancellation — or
  none, and then an explicit `unknown` that **names which records are absent**.
  A historical attempt that predates item 1 reaches exactly that branch, and
  that is correct: a cause is never manufactured retrospectively, never
  recovered by reading raw SQL, a secret's contents or a private transcript,
  never assembled from an exception `repr` or a guessed timestamp.
- **The revocation**, read from the token journal rather than inferred.
- **The token axis** verbatim from `token_of`. An expiry with `renewals=0`
  against a Job that allowed a longer provider turn is the pilot's exact shape
  and must be legible without the reader doing arithmetic.
- **The execution axis**: `execution_runtime`, outstanding `cleanup`,
  `runtime_id`, the token-bound container when they differ, the last
  observation instant and the activity projection with its own instant.
- **Safe locators only** — see below.
- Every member either **known with its source**, or **unknown with a bounded
  reason**. A missing count is never a zero; an observed zero is a known zero.

Snapshot state is evidence, never a replacement for current authority
(`decisions/review-333812.md`): report what was recorded, and do not let a
stale record outrank a current axis read.

### 5. Carry it to ordinary status, and one supported read-only report

- `job_manager/delegation.py`: an **optional** additional observation member,
  for the reason `integration` is optional — an observation composed before it
  existed is still complete, normalized to `None`, meaning "nobody looked".
- `delegation.ManagerOperations.observe` supplies it from the control store it
  already holds. **Do not change `tools/job_manager.py` or
  `job_manager/manager.py`** — W333485's declared surfaces; both the serving
  loop and the read-only `status` surface already reach `observe`.
- `job_manager/documents.py`: `CONTRACTS["stage.status"]` gains the member and
  `STATUS_SCHEMA` moves coherently, with the version note saying what the older
  reader would not know was recorded.
- `job_manager/projection.py:_stage_status` reports it and **branches on
  nothing**. The stage state stays what the existing axes decide. A diagnostic
  cause is not an acceptance and must not become a second route to
  `exceptional`.
- A new `tools/attempt_diagnostics.py` following
  `tools/worker_visibility.py`'s accepted discipline: a **pure projection**
  over one status document read through
  `tools/job_viewer.py:read_snapshot`; **no store, no clock, no engine, no
  provider, no subprocess**; its own schema version; a **positive member
  allowlist** with a declared type per member and no nested-object forwarding;
  per-fact provenance and bounded unknown reasons; no freshness verdict,
  because no freshness policy has been selected.
- Reached through **`tools/stack_command.py` `COMMANDS`**, the way `logs`,
  `record` and `disposition` are.

  **A source-level case is not proof that a rebuilt bundle carries the
  command.** Assert the table and the dispatch in source, and state the
  remaining deployment obligation explicitly in the module and in your report.
  Do not rebuild the bundle.

The files and schema names above are **design proposals to revalidate**, not
permission gates — except the two sibling-owned files, which are a
coordination boundary, and the accepted `intake.py`/`attempts.py` semantics,
which you extend rather than rewrite.

## The locator obligation: a demonstration, not a field

Device and inode identify a workspace *object* and are **not** a usable
retained-output locator. The supported path is the deployed `logs` subcommand
over `worker_manager.attempt_logs`:
`baton-v12-stack logs --logs <launch-home>/logs --attempt <id> locators`.

- emit the attempt identity and whatever locator the **manager itself
  recorded** (the frozen result's `artifacts`), under the allowlist;
- emit the exact supported invocation shape and name the one operand the
  operator must supply — the delivery root — and say why this report does not
  resolve it: a report that resolved a deployment document would be a reader
  that can be pointed at a store;
- keep device/inode, labelled an object identity, explicitly **not** a path and
  **not** a locator by itself;
- **demonstrate the round trip**: a case that takes the report's emitted
  locator fields, feeds them to the supported `attempt_logs` reader over a real
  retained delivery, and shows the operator reaches the retained evidence —
  while the report carries no stream content, no credential, no environment
  value and no private text.

## The axes that must survive, demonstrated rather than asserted

- an **exceptional** stage does not prove runtime cessation;
- **missing artifacts** do not prove there are no retained partial edits;
- **observed activity** does not prove valid permission;
- a **diagnostic cause is not candidate acceptance**;
- an **ordered effect** does not prove it happened, and an **absent record**
  does not prove nothing happened;
- **quiescent is not absent**: a stopped-but-present container is still a
  container holding its mounts;
- an **uncorrelated absence** does not prove cessation; only an exact
  correlated positive observation does;
- a recorded manager failure is reported **even when the agent sent no final
  message**.

## Verification inside this Job

Outcome-based: choose the tests and commands that establish the behaviour. The
sealed argv is the acceptance gate, not the whole of what you should run.

Exercise the **production** composition and the **production** report boundary
over:

- the **actual reclaim-to-settlement composition**: reclaim returning `held`
  after a positive observation, settlement finishing the generation at its own
  release, and the captured cause surviving that handoff;
- the **cancellation path** (d): fenced with an attached identity, fenced with
  only a token-bound identity, fenced with neither, and a conflicting identity
  refused;
- the **token-bound-before-attachment** case (a) and (c), including the new
  held outcome;
- the **replay effects** (b), as three distinct cases: a revoked generation
  observed **`absent`** orders neither stop nor removal; one observed
  **`quiescent`** skips the stop but **still removes**; anything else does
  both — and the record distinguishes all three;
- **restart and replay at every external-effect cut**, including a crash after
  an engine effect and before any outcome record, and an exact replay of each
  act;
- a denied or refused stop, an engine timeout, an engine that cannot be asked,
  an uncertain observation, an exact-runtime mismatch, and a lost reply;
- token expiry with zero renewals, and expiry after renewals;
- a start failure, a preparation failure and a provider-side ending;
- an **unknown historical cause**: an attempt with none of the new records,
  answering `unknown` and naming each absent record, while still reporting the
  revocation the token journal does hold;
- a missing control store, a missing Job store, denied access to either;
- malformed and redacted evidence, and a record whose signature no longer
  verifies;
- a **stale** observation, and one belonging to a **different episode or
  runtime identity** — reported as unknown with the reason, never re-attached;
- outstanding cleanup, and an unresolved termination;
- **secret canaries** on every failure path: register a live secret, put its
  value where a naive implementation would quote it — engine stderr, a refusal
  message, an exception repr — and prove it reaches neither the record, the
  status document nor the report;
- the **locator round trip**;
- and that every read **mutates nothing**: no claim, renewal, reconciliation,
  acknowledgement, retry, store creation or migration, no application state
  change. Normal SQLite read-only sidecar behaviour is allowed. Prove the
  preserved source and state bytes unchanged, and instrument the affected
  transaction boundaries for external I/O.

No live provider is needed for any of it.

### The sealed gate

Ten existing modules plus the two you must create. Re-measured at **this**
base against a clean export — **the preparing author's evidence, not
independent product acceptance**: **1124 tests, all passing, zero skips,
14.095s**.

```
tests.job_manager.test_status            0.452s   65
tests.job_manager.test_delegation        0.059s   44
tests.job_manager.test_documents         0.003s   31
tests.job_manager.test_tool              0.586s   72
tests.manager.test_intake                4.133s  207
tests.manager.test_maintenance           2.382s  148
tests.manager.test_attempts              4.003s  431
tests.tools.test_worker_visibility       0.274s   78
tests.manager.test_contracts_inventory   0.010s   15
tests.manager.test_authoring_enforcement 2.193s   33
```

**`tests.manager.test_authoring_manager_guard` is deliberately NOT in the
gate, for a measured ceiling reason rather than a coverage judgement.**
Measured here: **17.643s for 7 tests** — it spawns real processes. With the
ten modules above it would put the sealed gate at **31.7s before your two new
modules exist**, over a ceiling fixed at 30. Its coverage is carried by the
reused accepted proof in `decisions/guard-integration-result.json` (79 tests,
PASS, 15.278s, authority337376). You do not edit `authoring_enforcement.py`;
if that ever changes, run that module as a focused check **outside** the
sealed argv and say so.

`test_intake`, `test_tool` and `test_attempts` are in the gate because item 1's
composition lives across them. `test_authoring_enforcement` is in it because
your change touches `intake.py` and `attempts.py`, which that module now
covers — **do not break the accepted enforcement correction.**

A sealed argv cannot name classes that do not exist yet, so the two new module
names are **part of the contract**:

| new module | what it must cover |
| --- | --- |
| `v12/python/tests/manager/test_attempt_failure_cause.py` | the typed records, their public readers, reclaim-to-settlement and cancellation composition with restart cuts, the token-bound identity rule, replay-with-no-effect, the known-failure/unknown distinction, the composed cause with every unknown branch, every preserved axis, and the secret canaries |
| `v12/python/tests/tools/test_attempt_diagnostics.py` | the report: allowlist, provenance and unknown reasons, refusals, that it opens no store and spawns nothing, the locator round trip, that `stack_command.COMMANDS` serves and dispatches it, and the explicit rebuilt-bundle obligation |

**The ceiling is 30 seconds and is not negotiable on this vehicle.** The
composer fixes `verification_command_seconds` at 30 in both places it appears
(`baseline_bindings.py:345` and `:522`), with no compose parameter. The ten
existing modules spend **14.095s**, leaving roughly **15.9 seconds** for the
two new ones. That is a real design constraint, and
`decisions/review-334776.md` is explicit that the 30-second fit for the new
modules **remains unproved** and that no coverage may be removed to force a
pass. If the gate cannot be made to fit, **report it honestly with the
measured numbers**.

**No skip is admitted.** The gate program fails on a skipped case.

`tests.manager.test_authoring_enforcement` needs
`work/records/2026/09/finding-v12-single-implementation-proof` present at the
checkout root — it spawns a real supervisor. Measured: 1 error without it, all
33 passing with it. The private checkout carries it; see `ENFORCEMENT.md`.

## Boundaries

- **No edit to anything under `/input`.** The mount is read-only on purpose.
- **Do not touch `tools/job_manager.py` or `job_manager/manager.py`** —
  W333485's declared surfaces. `worker_manager/intake.py` and
  `worker_manager/attempts.py` are the declared overlap: keep edits to
  attribution on the reclaim, settlement and cancellation paths, **preserve the
  committed enforcement semantics**, and expect serial integration.
- **Do not "fix" `baseline_bindings.py`.** Its `start` command is wrong for
  this vehicle (`ENFORCEMENT.md`) and correcting it is host product work this
  Work does not own. Report it; do not patch it.
- **`tests.manager.test_boundary_inventory` does not pass at base** — an
  explicitly unverified baseline report, measured 328 tests / 28 failures /
  1 error / 49.469s at the previous base, excluded from the gate, with no
  cleanup selected. Do not fix it and do not report it as this candidate's. Do
  keep its declarations honest for the boundary **you** add: register the
  receiving entries and probes your change introduces, and report what you
  registered.
- **`tests.tools.test_packaging` is excluded too** — it holds the source
  command table against the installed bundle, which predates `record` and
  `disposition`, so it already fails on the host, and inside a private checkout
  it SKIPs, which the gate refuses. Also an unverified baseline report.
- `tests.manager.test_dependencies` also fails at base for reasons that
  predate this Work. Not yours.
- **No broad suite sweep** and no unrelated test cleanup or weakening.
- No image build, no container, no engine call and no provider call inside this
  task. No host product edit outside the private checkout, no integration, no
  self-acceptance, no deployment, no mutating version-control operation beyond
  what the line profile itself performs, no edit to historical evidence.
- **The failed native pilot, all three earlier packets and the failed
  execution-334663 instance are preserved.** No retry, no rerun, no runtime
  recovery, no mutation, no credential or transcript read.
- Independent review and the human Git checkpoint remain required. A retained
  candidate is not an accepted one.

## Honesty obligations

**Expect the 900-second lease to be enforced.** The controller makes the
initial lease real rather than ignored; production renewal is still W333485's
unfinished work, so the 3600/4800 ceilings are **not** a promise of a
3600-second authoring run. If your turn is terminated that way, preserve the
partial candidate, account for what is missing, and report the actual expiry,
cleanup, retained-output and recovery behaviour you observed — that is evidence
for this Work, not a failure to hide.

**And know that this vehicle has failed once already.** `FAILURE.md` records
the previous packet's selected run dying at startup in 0.506s because the
controller composed two managers for one workspace. That exact defect is
corrected at this base, but one corrected startup refusal is not a
demonstration that a full authoring invocation completes here. No such run has
ever completed for this Work. If yours does not either, the honest account of
how far it got is the deliverable.

Report honestly if the milestone is only partly reached. State which items are
delivered, which tests ran, what they measured, and cumulative verification
spending. Do not label an environmental failure as formal success, and do not
weaken an existing assertion to obtain a pass.
