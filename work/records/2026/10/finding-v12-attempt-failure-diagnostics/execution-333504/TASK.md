# W333486 actionable attempt failures and one read-only diagnostic report

Private committed base `bbdacb5d38f6cf2d2461e9da103d28f9ab30cc6c`. The
read-only nominated source at `/input/source` carries this packet's exact
input documents. They are **read, never edited and never transcribed**; the
mount is read-only on purpose and this task restores nothing into the private
checkout. There is no preserved candidate buffer: every byte this correction
starts from is committed at the declared base.

Read these first, from the mount, before editing anything:

| document | why |
| --- | --- |
| `work/records/2026/10/finding-v12-attempt-failure-diagnostics/FINDING.md` | the accepted outcome, the preserved axes and the ownership boundary |
| `work/records/2026/10/finding-v12-attempt-failure-diagnostics/PLAN.md` | the current milestone and the frozen input |
| `work/records/2026/10/finding-v12-native-pilot-instance-packet/OWNER-FAILURE-EVIDENCE-20261019.md` | the attributed incident: exact identities, the null failure readers, and what is **not** established |
| `v12/DESIGN.md` | the normative v12 specification; TOK-* for the resource token, HOST-* for the host, REC-4 for what an unknown must carry |
| `AGENTS.md` | repository policy, including the standing test-change authority |
| `work/records/2026/10/finding-v12-minimum-worker-visibility/FINDING.md` | the accepted discipline the new report must follow |

If a pinned input is absent or is not its declared bytes, **stop with the exact
failure**. No reconstruction from prose, from an older blob or from any
fallback.

## What is already true, so nothing below is re-derived

Revalidated at this base by the preparing implementer:

- `worker_manager/tokens.py:303 token_of` already answers the whole token axis:
  acquired and current `expires_at`, `renewals`, `revision`,
  `renewals_remaining`, `renewed_at`, `expiry_judged_at`, `expired`,
  `timing_ambiguous` with its two instants, `revoked`, `returned`,
  `activating`, `activation_started`, the journalled `launch` and the bound
  `container`. `LIFETIME_SECONDS` is 900 and `RENEWAL_LIMIT` is 4.
- `worker_manager/attempts.py` already answers `attempt_runtime_of`,
  `attempt_activity_of`, `attempt_start_failure_of` and
  `attempt_preparation_failure_of`, and the attempt row already carries
  `execution_runtime`, `cleanup`, `observed_at`, `activity_bytes`,
  `activity_at`, `runtime_id` and the governed `workspace_device` /
  `workspace_inode`.
- Every journal row carries the store's own `settled_at`, so no instant in
  this correction has to be guessed or stamped by a reader.
- `job_manager/submission.py:execution_limits_of` and
  `job_manager/execution_limits.py:resolved` already answer a Job's requested
  and effective ceilings, and `projection._job_limits` already reports them.

**The one thing nothing records** is that this manager terminated an exact
runtime because its governed generation went overdue.
`intake.reclaim_expired_resource` revokes, stops, removes, confirms and
settles, and journals no account of having done so: its outcome is an
in-memory dict handed to `tools/job_manager.py:_reclaiming`, reported in one
tick's sweep report, and `manager.serve` keeps only the last tick's. That is
why the owner's public start- and preparation-failure readers both answered
`null` for an attempt whose runtime was in fact destroyed — neither reader is
about this component, and the component that acted recorded nothing.

## The milestone, and it is exactly these five things

### 1. Capture the cause at the boundary that owns it

Give the reclaim its own durable, typed, manager-owned record.

- A new closed contract in `worker_manager/documents.py` `CONTRACTS` with its
  constructor and an exported member tuple, named for the act it records.
- A derived operation identity beside `intake.reclaim_operation_id`, derived
  from the attempt and the runtime it bound — so one attempt's one bound
  execution has exactly one account, and a reader can find it from the row
  alone without first resolving a generation.
- The **stable** facts ride the signature: the attempt, its fixed assignment,
  the start operation this followed, the conflict domain, the generation, the
  journalled launch and the typed reason. The facts **as they stood** ride the
  document and are read inside the act: the bound `runtime_id`, the state the
  adapter answered for that exact identity, `execution_runtime` and `cleanup`.
  This is `_record_and_raise_start_failure`'s established split, and the reason
  is the same: folding a changeable fact into the identity selects another row
  and never reaches the collision guard, while folding it into the signature
  makes an exact replay collide with itself.
- Written **after** the positive confirmation and **before** `govern.release`.
  A death between them must leave the cause recorded and the resource honestly
  held — never a freed resource with no account of what freed it.
- It must not replace the reclaim's outcome. A collision or an unsignable
  operand is carried in the pass answer the way `_record_start_failure`
  carries one; the first account, written when the manager knew most, stands.
- A **refused stop** and an **unproved cessation** are deliberately *not*
  terminations and must not be recorded as ones: nothing was established.
  The revocation is already durable, and the reader in (3) must answer
  `unknown` naming the evidence that is missing. If you conclude the refused
  stop deserves its own typed record, that is a separate kind with its own
  members — never this one wearing a weaker meaning.

### 2. One public reader for that record

A sibling of `attempts.attempt_start_failure_of`, held to the same discipline:
derive the identity from the row exactly as the recorder derives it, decode
through the journal's own `replay` for the declared kind, own the document
against its closed member set, and **re-prove every fact the identity is
derived from** against the attempt as it now stands. Absence is the ordinary
answer. A refused row under that identity is a collision, not evidence.

### 3. One composed typed cause, with explicit unknown

A new public reader in the Worker Manager that composes, from facts their
owners already hold and from nothing it derives itself, one answer to "what
ended this attempt, exactly":

- **Which component, and when.** The start failure, the preparation failure,
  the reclaim termination — or none, and then an explicit `unknown` that
  **names which records are absent**. A historical attempt that predates (1)
  reaches exactly this branch, and that is correct: a cause is never
  manufactured retrospectively, never recovered by reading raw SQL, a secret's
  contents or a private transcript, and never assembled from an exception
  `repr` or a guessed timestamp.
- **The token axis**, verbatim from `token_of`: domain, generation, acquired
  and current deadline, renewals, revision, remaining renewals, `renewed_at`,
  judged expiry, timing ambiguity and its instants, revoked, returned,
  activating. An expiry with `renewals=0` against a Job that allowed a longer
  provider turn is the pilot's exact shape and must be legible without
  arithmetic by the reader.
- **The execution axis**: `execution_runtime`, outstanding `cleanup`,
  `runtime_id`, the last observation instant and the activity projection with
  its own instant.
- **Safe locators only**: the attempt identity, the conflict domain, the
  governed workspace **object identity** (device and inode — an identity, not
  a path), the bound container identity, and the supported command through
  which retained raw output is read. No filesystem path, no transcript, no
  credential, no environment value, no provider output, no arbitrary exception
  text.
- Every member is either **known with its source**, or **unknown with a
  bounded reason**. A missing count is never a zero; an observed zero is a
  known zero.

### 4. Carry it to ordinary status, deciding nothing

- `job_manager/delegation.py`: an **optional** eighth observation member, for
  the reason `integration` is optional — an observation composed before this
  member existed is still a complete one, normalized to `None`, which means
  "nobody looked" rather than "nothing happened".
- `delegation.ManagerOperations.observe` supplies it from the control store it
  already holds. **Do not change `tools/job_manager.py` or
  `job_manager/manager.py`**: both the serving loop and the read-only
  `status` surface already reach `observe`, and those two files are the
  declared surfaces of sibling W333485.
- `job_manager/documents.py`: `CONTRACTS["stage.status"]` gains the member and
  `STATUS_SCHEMA` moves to `baton.v12.job-status/7`, with the version note
  saying what a `/6` reader would not know was recorded.
- `job_manager/projection.py:_stage_status` reports it and **branches on
  nothing**. The stage state stays exactly what the existing axes decide. A
  diagnostic cause is not an acceptance, and an added member must not become a
  second way to reach `exceptional`.

### 5. One supported read-only report

A new `tools/attempt_diagnostics.py`, following `tools/worker_visibility.py`'s
accepted discipline precisely, because that discipline is the acceptance:

- a **pure projection over one status document**, read through the existing
  `tools/job_viewer.py:read_snapshot` rather than a second reader;
- **no store, no clock, no engine, no provider, no subprocess**. It never asks
  what time it is, so no age it reports could be a statement about how long
  the program has been looking;
- its own version, `baton.v12.attempt-diagnostics/1`, so a consumer can tell
  which document it holds;
- a **positive member allowlist** with a declared type per member. It forwards
  no nested object, so a future producer's addition cannot be published
  silently;
- per-fact provenance and bounded unknown reasons; no freshness verdict,
  because no freshness policy has been selected;
- and it is reached through **`tools/stack_command.py` `COMMANDS`**, the way
  `logs`, `record` and `disposition` are. An uninstalled source-only script is
  not the requested easy report. Add the subcommand to that table with the
  short docstring the table's entries carry.

## The axes that must survive, demonstrated rather than asserted

Each of these is a case, not a sentence in a comment:

- an **exceptional** stage does not prove runtime cessation;
- **missing artifacts** do not prove there are no retained partial edits;
- **observed activity** does not prove valid permission;
- a **diagnostic cause is not candidate acceptance**;
- a recorded manager failure is reported **even when the agent sent no final
  message** — which is the pilot's exact shape.

## Verification inside this Job

Outcome-based: choose the tests and commands that establish the behaviour. The
sealed argv below is the acceptance gate, not the whole of what you should run.

Exercise the **production** readers and the **production** report boundary —
not a hand-built fixture standing in for them — over:

- token expiry with zero renewals, and expiry after renewals;
- a start failure, a preparation failure, a provider-side ending and an engine
  failure;
- an **unknown historical cause**: an attempt with none of the three records,
  answering `unknown` and naming each absent record;
- a missing control store, a missing Job store, and denied access to either;
- malformed and redacted evidence, and a record whose signature no longer
  verifies;
- a **stale** observation, and an observation belonging to a **different
  episode or runtime identity** — reported as unknown with the reason, never
  re-attached;
- an unresolved termination (revoked, stop refused, cessation unproved) and
  outstanding cleanup;
- **secret canaries**: register a live secret, put its value where a naive
  implementation would quote it, and prove it reaches neither the record, the
  status document nor the report;
- and that every one of these reads **mutates nothing**: no claim, renewal,
  reconciliation, acknowledgement, retry, store creation or migration, and no
  application state change. Normal SQLite read-only sidecar behaviour is
  allowed. Prove the preserved source and state bytes are unchanged.

No live provider is needed for any of it.

### The sealed gate

The verification argv this packet carries runs these nine existing modules
plus the two new ones. The nine were measured against a clean export of the
declared base: **1091 tests, all passing, zero skips, 11.83s**.

```
tests.job_manager.test_status            0.343s   65
tests.job_manager.test_delegation        0.059s   44
tests.job_manager.test_documents         0.002s   31
tests.job_manager.test_tool              0.575s   72
tests.manager.test_intake                4.121s  207
tests.manager.test_maintenance           2.396s  148
tests.manager.test_attempts              4.048s  431
tests.tools.test_worker_visibility       0.277s   78
tests.manager.test_contracts_inventory   0.010s   15
```

A sealed argv cannot name classes that do not exist yet, so the two new module
names are **part of the contract**:

| new module | what it must cover |
| --- | --- |
| `v12/python/tests/manager/test_attempt_failure_cause.py` | the typed termination record, its public reader, and the composed cause with every unknown branch, every preserved axis and the secret canaries |
| `v12/python/tests/tools/test_attempt_diagnostics.py` | the report: its allowlist, its provenance and unknown reasons, its refusals, that it opens no store and spawns nothing, and that `stack_command.COMMANDS` serves it and dispatches to it |

**The ceiling is 30 seconds and it is not negotiable on this vehicle.** The
composer fixes `verification_command_seconds` at 30 in both places it appears
(`baseline_bindings.py:345`, the execution policy whose digest the submission
carries, and `:522`, the submission's own `execution_limits`), with no compose
parameter. The nine existing modules already spend 11.83s of it, so the two
new modules have roughly **18 seconds** between them. Keep them cheap: that is
a real design constraint on the tests, not a suggestion. If the gate cannot be
made to fit, **report that honestly with the measured numbers** rather than
deleting coverage to buy time.

**No skip is admitted.** The gate program fails on a skipped case, because a
skipped case is an unproven obligation wearing a passing exit status.

## Boundaries

- **No edit to anything under `/input`.** The mount is read-only on purpose.
- **Do not touch `tools/job_manager.py` or `job_manager/manager.py`.** They
  are sibling W333485's declared surfaces and the correction does not need
  them. `worker_manager/intake.py` is the one declared overlap risk; keep the
  edit to the reclaim path and nothing else in that file.
- **`tests.manager.test_boundary_inventory` does not pass at this base** and
  is excluded from the gate: measured alone on base bytes, 328 tests, 28
  failures, 1 error, 49.469s — stale declared owners for `review_cycles.py`,
  entries owned twice for `intake.py:discharge_quiescence_gate`,
  `intake.py:discharge_abandoned_quiescence_gate` and
  `interrogation.py:probe`, plus lane-coverage and probe-arrival failures. Do
  **not** try to fix it here and do **not** report it as this candidate's. But
  do keep its declarations honest for the boundary **you** add: register the
  new receiving entries and probes your change introduces, and report what you
  registered. A pre-existing failure is not a licence to add an unregistered
  boundary.
- **`tests.tools.test_packaging` is excluded too**, and for a different
  reason: it holds the source `COMMANDS` table against the **installed
  bundle's** help, and the bundle this instance runs was built before `record`
  and `disposition` joined that table, so it already fails on the host
  (`'disposition' not found`). Inside a private checkout it instead SKIPs,
  which the gate refuses. The packaged-table obligation therefore belongs to a
  source-level case in `tests.tools.test_attempt_diagnostics`. Do not rebuild
  the bundle and do not edit that module to make it pass.
- `tests.manager.test_dependencies` also fails at this base for reasons that
  predate this Work. Not yours.
- **No broad suite sweep.** Run the focused checks for what you changed, then
  the sealed argv.
- No image build, no container, no engine call and no provider call inside
  this task. No host product edit outside the private checkout, no
  integration, no self-acceptance, no deployment, no mutating version-control
  operation beyond what the line profile itself performs, and no edit to
  historical evidence.
- **The failed native pilot is preserved.** No retry, no mutation and no read
  of its credentials or transcripts.
- Independent review and the human Git checkpoint remain required. A retained
  candidate is not an accepted one.

## Honesty obligations

An unchanged host lease may still stop this authoring turn at 900 seconds:
sibling W333485's renewal correction is **not** in this base, and that is the
very defect this campaign is correcting. If the turn is terminated that way,
the preserved partial candidate plus an exact account of what is missing is
worth more than a green claim — and it is itself evidence for this Work.

Report honestly if the milestone is only partly reached. State which of the
five items are delivered, which tests were run, what they measured, and
cumulative verification spending. Do not label an environmental failure as
formal success, and do not weaken an existing assertion to obtain a pass.
