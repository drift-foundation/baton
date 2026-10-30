# W333486 actionable attempt failures and one read-only diagnostic report

Private committed base `bbdacb5d38f6cf2d2461e9da103d28f9ab30cc6c`. The
read-only nominated source at `/input/source` carries this packet's exact input
documents. They are **read, never edited and never transcribed**; the mount is
read-only on purpose and this task restores nothing into the private checkout.
There is no preserved candidate buffer: every byte this correction starts from
is committed at the declared base.

**This packet supersedes `../execution-333504`**, which is preserved unchanged.
What changed is recorded in `PACKET.md`; the substance is in items 1 and 3 and
in the locator obligation, and all of it comes from
`decisions/review-333691.md`.

Read these first, from the mount, before editing anything. The decision
documents are **immutable snapshots** taken at claim333707, not the live
mutable files — `decisions/INDEX.json` carries each one's source path and the
source digest it was taken from.

From **this packet's own directory on the mount** — immutable, digest-pinned as
the packet's `fixture.files`, so a drifted one refuses before any store opens:

| document | why |
| --- | --- |
| `decisions/FINDING.md` | the accepted outcome, the preserved axes and the ownership boundary |
| `decisions/PLAN.md` | the milestone and the frozen input |
| `decisions/review-333691.md` | the review this task answers; where it disagrees with the prose below, it wins |
| `decisions/owner-failure-evidence.md` | the attributed incident: exact identities, the null readers, and what is **not** established |
| `decisions/sibling-review-333618.md` + `sibling-blocker-*.json` | why this packet is held and must not be started |

From **the private checkout at the declared base**, because all three are
committed there and pinning a mutable mount copy of them would make the packet
refuse on an unrelated policy edit:

| document | why |
| --- | --- |
| `v12/DESIGN.md` | the normative specification; TOK-* for the resource token, HOST-* for the host, REC-4 for what an unknown must carry |
| `AGENTS.md` | repository policy, including the standing test-change authority |
| `work/records/2026/10/finding-v12-minimum-worker-visibility/FINDING.md` | the accepted discipline the new report must follow |

If a pinned input is absent or is not its declared bytes, **stop with the exact
failure**. No reconstruction from prose, from an older blob or from any
fallback.

## What is already recorded, stated precisely

The earlier revision of this task claimed "nothing records" the termination.
That was too broad and `decisions/review-333691.md` item 3 corrects it. What is
already journalled, by its own owner, with the store's own `settled_at`
instant:

- **`tokens.revoke` (`worker_manager/tokens.py:728`)** journals
  `resource-token.revoked:<domain>:<generation>` carrying the domain,
  generation, owner, bound container and the `expired_at` deadline that was
  blown. The revocation **is** durable evidence and must be read, not ignored.
- **`tokens.returned`** journals `resource-token.returned:<domain>:<generation>`
  — and it does so on **either** release path, which is what makes the
  completion instant recoverable regardless of which one ran (see item 1).
- `tokens.token_of` (`:303`) answers the whole token axis: acquired and current
  `expires_at`, `renewals`, `revision`, `renewals_remaining`, `renewed_at`,
  `expiry_judged_at`, `expired`, `timing_ambiguous` with its two instants,
  `revoked`, `returned`, `activating`, `activation_started`, the journalled
  `launch` and the bound `container`.
- `attempts` answers `attempt_runtime_of`, `attempt_activity_of`,
  `attempt_start_failure_of` and `attempt_preparation_failure_of`; the attempt
  row carries `execution_runtime`, `cleanup`, `observed_at`, `activity_bytes`,
  `activity_at`, `runtime_id` and the governed `workspace_device` /
  `workspace_inode`.
- `submission.execution_limits_of` and `execution_limits.resolved` answer a
  Job's requested and effective ceilings.

**What is actually missing is the causal/operation/outcome composition**: which
component ordered this exact runtime stopped, under which operation identity,
with what engine outcome, and whether cessation was established. No record
carries that, and no reader composes it from the pieces above. That — and not
"nothing records" — is this correction's gap.

Equally: the absence of a start-failure or preparation-failure record is
**expected** for this component, because neither reader is about it. It is a
diagnostic limitation, not independent proof of the proposed cause.

## The milestone, and it is exactly these five things

### 1. Capture the cause across the paths that actually run

The reclaim is not one act with one release, and the earlier revision's "after
positive confirmation and before `govern.release`" named only one of two. The
production composition, revalidated at this base:

- `intake.reclaim_expired_resource` revokes, stops, removes, then observes. If
  the observation is `absent`/`quiescent` it calls `_resource_cessation`
  (`intake.py:1122`), which answers `None` unless a committed cleanup carries
  both halves of its proof — and `_custody_already_committed` returns `None`
  for a running attempt whose roots were never normalized. So the ordinary
  outcome for a reclaimed live attempt is **`held`**, with the reclaim's own
  `govern.release` never reached.
- `tools/job_manager.py:_reclaiming` then calls
  `intake.settle_revoked_resource` on a `held` or `returned` outcome, and
  **that** path's own `govern.release` (`intake.py:5909`) is what finishes the
  generation.

So the pilot's termination most plausibly completed on the **second** path, and
a capture bound to the first one would have recorded nothing about it.

**What this item requires**, with the implementation shape your choice:

- Capture **eligibility and stop intent at the boundary that orders the stop**,
  durably, **before** the engine is asked — so a crash between the stop and any
  later record cannot lose the fact that this manager ordered this exact
  container stopped because this generation was overdue. Carry the attempt, its
  fixed assignment, the start operation, the domain, the generation, the
  journalled launch, the bound container and the reclaim operation identity
  handed to the engine.
- Capture the **outcome** separately (item 3), because intent is not outcome.
- **Never infer a successful stop or a termination from intent, or from
  absence.** An ordered stop with no outcome record is exactly that, and the
  reader must say so.
- Make the **completion** attributable on **either** release path. Prefer
  reading `resource-token.returned`, which both paths journal, over adding a
  third record — but whatever you choose, a captured intent or outcome **must
  not disappear because completion happened later on the other path**.
- Preserve replay and collision discipline: stable facts on the signature,
  facts-as-they-stood in the document, read inside the act. An exact replay
  returns the first account; a changed fact collides rather than rewriting it.
- Recording must never replace the reclaim's outcome: a collision or an
  unsignable operand is carried in the pass answer the way
  `_record_start_failure` carries one. The first account, written when the
  manager knew most, stands.

**Prove the actual composition and restart at the external-effect cuts** —
revoke→stop, stop→remove, remove→observe, observe→record, record→release, and
the reclaim→settlement handoff — by driving the production composition, not a
fixture standing in for it.

### 2. Public readers for whatever you record

Siblings of `attempts.attempt_start_failure_of`, held to the same discipline:
derive the identity from the row exactly as the recorder derives it, decode
through the journal's own `replay` for the declared kind, own the document
against its closed member set, and **re-prove every fact the identity is
derived from** against the attempt as it now stands. Absence is the ordinary
answer. A refused row under that identity is a collision, not evidence.

### 3. A known failure is not an unknown — keep them separate

The earlier revision folded a refused stop into "unknown, because it is not a
termination". Not claiming termination was right; discarding the manager's own
knowledge was not. `decisions/review-333691.md` item 3: the manager may know a
**typed stop or engine failure** while cessation remains **unknown**, and those
two facts must be preserved and exposed separately.

So the outcome vocabulary must distinguish at least:

- cessation positively established (the exact identity observed absent, or
  quiescent — and those two are not the same fact either);
- **a known typed stop/engine failure** — the engine refused, timed out or
  could not be asked — carried with its typed category and code, with cessation
  explicitly unknown;
- an **uncertain observation**: the stop crossed and what exists now could not
  be established;
- an **exact-runtime mismatch**: the generation governs one container and the
  attempt now carries another;
- a **lost reply**: the act may or may not have crossed.

None of these may be reduced to "no termination evidence". A known manager
failure must be reported **even when the agent sent no final message**, which
is the pilot's exact shape.

### 4. One composed typed cause, with explicit unknown

A new public reader in the Worker Manager that composes, from facts their
owners already hold and from nothing it derives itself:

- **Which component, under which operation, when, and with what outcome.** The
  start failure, the preparation failure, the reclaim intent and its outcome —
  or none, and then an explicit `unknown` that **names which records are
  absent**. A historical attempt that predates item 1 reaches exactly that
  branch, and that is correct: a cause is never manufactured retrospectively,
  never recovered by reading raw SQL, a secret's contents or a private
  transcript, and never assembled from an exception `repr` or a guessed
  timestamp.
- **The revocation**, read from the token journal rather than inferred: its
  generation, the `expired_at` it blew, and the journal's own instant.
- **The token axis**, verbatim from `token_of`. An expiry with `renewals=0`
  against a Job that allowed a longer provider turn is the pilot's exact shape
  and must be legible without the reader doing arithmetic.
- **The execution axis**: `execution_runtime`, outstanding `cleanup`,
  `runtime_id`, the last observation instant and the activity projection with
  its own instant.
- **Safe locators only** — see the locator obligation below.
- Every member is either **known with its source**, or **unknown with a
  bounded reason**. A missing count is never a zero; an observed zero is a
  known zero.

### 5. Carry it to ordinary status, and one supported read-only report

- `job_manager/delegation.py`: an **optional** additional observation member,
  for the reason `integration` is optional — an observation composed before it
  existed is still complete, normalized to `None`, meaning "nobody looked"
  rather than "nothing happened".
- `delegation.ManagerOperations.observe` supplies it from the control store it
  already holds. **Do not change `tools/job_manager.py` or
  `job_manager/manager.py`**: both the serving loop and the read-only `status`
  surface already reach `observe`, and those two files are sibling W333485's
  declared surfaces.
- `job_manager/documents.py`: `CONTRACTS["stage.status"]` gains the member and
  `STATUS_SCHEMA` moves coherently, with the version note saying what the older
  reader would not know was recorded.
- `job_manager/projection.py:_stage_status` reports it and **branches on
  nothing**. The stage state stays what the existing axes decide. A diagnostic
  cause is not an acceptance and must not become a second route to
  `exceptional`.
- A new `tools/attempt_diagnostics.py` following `tools/worker_visibility.py`'s
  accepted discipline: a **pure projection** over one status document read
  through the existing `tools/job_viewer.py:read_snapshot`; **no store, no
  clock, no engine, no provider, no subprocess**; its own schema version; a
  **positive member allowlist** with a declared type per member and no
  nested-object forwarding; per-fact provenance and bounded unknown reasons; no
  freshness verdict, because no freshness policy has been selected.
- Reached through **`tools/stack_command.py` `COMMANDS`**, the way `logs`,
  `record` and `disposition` are. An uninstalled source-only script is not the
  requested easy report.

  **A source-level case is not proof that a rebuilt bundle carries the
  command.** Assert the table and the dispatch in source, and state the
  remaining deployment obligation explicitly in the module and in your report:
  the installed bundle must be rebuilt before an operator actually has this
  verb. Do not claim otherwise and do not rebuild the bundle here.

The implementation files and schema names above are **design proposals to
revalidate**, not permission gates. If revalidation shows a better boundary,
take it and say why — except for the two sibling-owned files, which are a
coordination boundary rather than a design choice.

## The locator obligation, which is a demonstration and not a field

`decisions/review-333691.md`: device and inode identify a workspace *object*
and are **not by themselves a usable retained-output locator**. The report must
let an operator actually find the relevant retained evidence, without
disclosing private content.

The supported path is the deployed `logs` subcommand over
`worker_manager.attempt_logs`, whose own contract is
`baton-v12-stack logs --logs <launch-home>/logs --attempt <id> locators`. It
opens no store and no engine, and `missing is not empty` is already its rule.

So:

- emit the attempt identity and whatever locator the **manager itself
  recorded** (the frozen result's `artifacts`), under the allowlist;
- emit the exact supported invocation shape and name the one operand the
  operator must supply — the delivery root — and say why this report does not
  resolve it: a report that resolved a deployment document would be a reader
  that can be pointed at a store;
- keep device/inode, explicitly labelled an object identity and explicitly
  **not** a path and **not** a locator by itself;
- and **demonstrate the round trip**: a case that takes the report's emitted
  locator fields, feeds them to the supported `attempt_logs` reader over a real
  retained delivery, and shows the operator reaches the retained evidence —
  while the report itself carries no stream content, no credential, no
  environment value and no private text.

## The axes that must survive, demonstrated rather than asserted

Each is a case, not a sentence in a comment:

- an **exceptional** stage does not prove runtime cessation;
- **missing artifacts** do not prove there are no retained partial edits;
- **observed activity** does not prove valid permission;
- a **diagnostic cause is not candidate acceptance**;
- an **ordered stop** does not prove a stop happened, and an **absent record**
  does not prove nothing happened;
- a recorded manager failure is reported **even when the agent sent no final
  message**.

## Verification inside this Job

Outcome-based: choose the tests and commands that establish the behaviour. The
sealed argv is the acceptance gate, not the whole of what you should run.

Exercise the **production** composition and the **production** report boundary
— not a fixture standing in for them — over:

- the **actual reclaim-to-settlement composition**: reclaim returning `held`
  after a positive observation, `settle_revoked_resource` finishing the
  generation at its own release, and the captured cause surviving that handoff;
- **restart and replay at every external-effect cut** named in item 1,
  including a crash after the engine stop and before any outcome record, and an
  exact replay of each act;
- **a denied or refused stop**, an engine **timeout**, an engine that **cannot
  be asked**, an **uncertain observation**, an **exact-runtime mismatch** and a
  **lost reply** — each reported as the typed fact it is, with cessation
  unknown where it is unknown;
- token expiry with zero renewals, and expiry after renewals;
- a start failure, a preparation failure and a provider-side ending;
- an **unknown historical cause**: an attempt with none of the new records,
  answering `unknown` and naming each absent record, while still reporting the
  revocation the token journal does hold;
- a missing control store, a missing Job store, and denied access to either;
- malformed and redacted evidence, and a record whose signature no longer
  verifies;
- a **stale** observation, and one belonging to a **different episode or
  runtime identity** — reported as unknown with the reason, never re-attached;
- outstanding cleanup, and an unresolved termination;
- **secret canaries** on every one of the failure paths above: register a live
  secret, put its value where a naive implementation would quote it — an engine
  stderr, a refusal message, an exception repr — and prove it reaches neither
  the record, the status document nor the report;
- the **locator round trip** described above;
- and that every one of these reads **mutates nothing**: no claim, renewal,
  reconciliation, acknowledgement, retry, store creation or migration, and no
  application state change. Normal SQLite read-only sidecar behaviour is
  allowed. Prove the preserved source and state bytes unchanged, and instrument
  the affected transaction boundaries for external I/O.

No live provider is needed for any of it.

### The sealed gate

The verification argv runs nine existing modules plus the two new ones. The
nine were measured against a clean export of the declared base: **1091 tests,
all passing, zero skips, 11.830s** — `test_status` 0.343s/65,
`test_delegation` 0.059s/44, `test_documents` 0.002s/31, `test_tool`
0.575s/72, `test_intake` 4.121s/207, `test_maintenance` 2.396s/148,
`test_attempts` 4.048s/431, `test_worker_visibility` 0.277s/78,
`test_contracts_inventory` 0.010s/15. These are the preparing author's
measurements, not independent product acceptance.

`test_intake` and `test_tool` are in the gate specifically because item 1's
composition lives across them.

A sealed argv cannot name classes that do not exist yet, so the two new module
names are **part of the contract**:

| new module | what it must cover |
| --- | --- |
| `v12/python/tests/manager/test_attempt_failure_cause.py` | the typed records, their public readers, the reclaim-to-settlement composition and its restart cuts, the known-failure/unknown distinction, the composed cause with every unknown branch, every preserved axis, and the secret canaries |
| `v12/python/tests/tools/test_attempt_diagnostics.py` | the report: its allowlist, provenance and unknown reasons, its refusals, that it opens no store and spawns nothing, the locator round trip, that `stack_command.COMMANDS` serves and dispatches it, and the explicit rebuilt-bundle obligation |

**The ceiling is 30 seconds and is not negotiable on this vehicle.** The
composer fixes `verification_command_seconds` at 30 in both places it appears
(`baseline_bindings.py:345`, the execution policy whose digest the submission
carries, and `:522`, the submission's own `execution_limits`), with no compose
parameter. The nine existing modules spend 11.83s, leaving roughly **18
seconds** for the two new ones. That is a real design constraint on the tests.
If the gate cannot be made to fit, **report it honestly with the measured
numbers** rather than deleting coverage to buy time.

**No skip is admitted.** The gate program fails on a skipped case, because a
skipped case is an unproven obligation wearing a passing exit status.

## Boundaries

- **No edit to anything under `/input`.** The mount is read-only on purpose.
- **Do not touch `tools/job_manager.py` or `job_manager/manager.py`.** Sibling
  W333485's declared surfaces. `worker_manager/intake.py` is the one declared
  overlap risk; keep the edit to the reclaim and settlement paths.
- **`tests.manager.test_boundary_inventory` does not pass at this base** and is
  excluded: measured alone on base bytes, 328 tests, 28 failures, 1 error,
  49.469s, which would exceed the ceiling by itself. That remains an
  **explicitly unverified baseline report** by the preparing author, and no
  cleanup of it is selected. Do **not** try to fix it and do **not** report it
  as this candidate's. Do keep its declarations honest for the boundary **you**
  add: register the receiving entries and probes your change introduces, and
  report what you registered.
- **`tests.tools.test_packaging` is excluded too**: it holds the source command
  table against the **installed bundle**, which predates `record` and
  `disposition`, so it already fails on the host, and inside a private checkout
  it SKIPs — which the gate refuses. Also an explicitly unverified baseline
  report. Do not rebuild the bundle and do not edit that module to pass.
- `tests.manager.test_dependencies` also fails at this base for reasons that
  predate this Work. Not yours.
- **No broad suite sweep** and no unrelated test cleanup or weakening. Run the
  focused checks for what you changed, then the sealed argv.
- No image build, no container, no engine call and no provider call inside this
  task. No host product edit outside the private checkout, no integration, no
  self-acceptance, no deployment, no mutating version-control operation beyond
  what the line profile itself performs, and no edit to historical evidence.
- **The failed native pilot is preserved.** No retry, no mutation, no read of
  its credentials or transcripts.
- Independent review and the human Git checkpoint remain required. A retained
  candidate is not an accepted one.

## Honesty obligations

**Do not expect this vehicle to enforce its own lease.** `HOLD.md` has the
evidence: the supervisor calls `serve` with no reclaim pass, so an expired
workspace generation is **not** reclaimed here at all. The earlier revision of
this task warned that the lease might stop the turn at 900 seconds; that claim
transferred the native pilot's behaviour to a vehicle that does not share it,
and it is withdrawn. What is true is the reverse and is why this packet is
held: on this vehicle the lease is **unenforced**, not strict.

Report honestly if the milestone is only partly reached. State which items are
delivered, which tests ran, what they measured, and cumulative verification
spending. Do not label an environmental failure as formal success, and do not
weaken an existing assertion to obtain a pass. A preserved partial candidate
with an exact account of what is missing is worth more than a green claim.
