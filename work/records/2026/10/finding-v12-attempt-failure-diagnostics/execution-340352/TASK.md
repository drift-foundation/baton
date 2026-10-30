# W333486 actionable attempt failures and one read-only diagnostic report

## THIS IS A CONTINUATION. Your first act is to apply the retained candidate.

Private committed base `bc925cf5c62d69426ed5862af4d41f4d2a967b0f`. **But you do
not start from it empty.** Run `attempt-diagnostics-w333486-340016` already ran
this task once: it produced 1621 insertions across 8 files, failed its gate, and
**retained a candidate** at head `433692c5003d7f3a91a1acab7efdb471d5597235`.
`decisions/review-340349.md` rejected that candidate with three static blockers.
`CONTINUATION.md` is the full account — **read it before anything else.**

**Step one, before any design thinking:** apply the retained candidate patch into
your own workspace with the repository tool for applying a patch, from

```
/input/source/work/records/2026/10/finding-v12-attempt-failure-diagnostics/evidence/run-340016/candidate-change.patch
```

That patch is a pinned task input, digest
`sha256:3af1822dc0d08851466105f17cbf5e9e26248ff75dc3d9352a9a43b979058e3e`;
`verify-inputs.py` and `prepare.py` both cross-check it against the sealed
candidate record. Apply it in your own workspace and confirm the result matches
the eight `changed_paths` in `decisions/candidate-result.json`. **Do not restore
anything into the private checkout** and do not try to fetch the candidate's
version-control objects — the patch bytes are the whole delivery.

**Then correct the three blockers.** You are not restarting: the candidate's
capture design, its `_known`/`_unknown` discipline, its token-bound identity
rule, its explicit `unknown` with `absent_records`, its allowlisted report and
**both of its new test modules** are work to keep and build on. Starting over
from an empty tree would discard accepted design and is explicitly not what the
review asked for.

The read-only nominated source at `/input/source` carries this packet's input
documents. They are **read, never edited and never transcribed**.

**This packet supersedes `../execution-333504`, `../execution-333707`,
`../execution-334663`, `../execution-337453`, `../execution-339421`,
`../execution-339628`, `../execution-339868` and `../execution-340016`**, all
preserved unchanged. The eighth was **selected and actually ran** — the first
authoring invocation this Work has ever completed — and the run, its instance and
its retained candidate are preserved as evidence. `FAILURE.md` is the account of
the *earlier* startup failure, `SHUTDOWN.md` of the ending behaviour,
`ENFORCEMENT.md` of the vehicle, and `CONTINUATION.md` of the completed run and
the candidate you are continuing.

Read these first. The decision documents are **immutable snapshots** taken at
claim340352; `decisions/INDEX.json` carries each one's source path and digest.

From **this packet's directory on the mount** — digest-pinned as the packet's
`fixture.files`:

| document | why |
| --- | --- |
| `CONTINUATION.md` | **start here**: the completed run, the retained candidate, the three blockers re-verified against its bytes, and what to keep |
| `decisions/review-340349.md` | the review that rejected the candidate. The authority for your milestone |
| `decisions/run-340016-INDEX.json`, `decisions/candidate-result.json` | the run's own evidence index and the candidate's own disposition record |
| `decisions/review-340327-evidence.json` | the reviewer's independent hashing of all ten evidence pairs |
| `decisions/FINDING.md` | the accepted outcome, the preserved axes, the ownership boundary |
| `decisions/PLAN.md` | the current milestone |
| `decisions/review-333812.md`, `decisions/review-334776.md`, `decisions/review-337566.md` | the reviews that fixed the cessation semantics, the replay wording and revision 4 |
| `decisions/review-339623.md` | worker/operator split for post-run collection; absence names no cause; overlap declaration instead of file bans |
| `decisions/review-339861.md`, `decisions/collector-probes-339847.json` | four collector defects and the fixtures that found them |
| `decisions/review-340012.md`, `decisions/collector-probes-339992.json` | three more, and the producer-order disproof of a persistence claim |
| `decisions/owner-failure-evidence.md` | the original attributed incident |
| `decisions/enforcement-review.md`, `decisions/enforcement-integration.md`, `decisions/guard-review.md`, `decisions/guard-integration.md`, `decisions/guard-integration-result.json`, `decisions/shutdown-finding.md`, `decisions/shutdown-review.md`, `decisions/shutdown-integration.json` | the three accepted vehicle corrections whose bytes you run inside |
| `decisions/failed-run-INDEX.json` | the earlier startup failure |
| `FAILURE.md`, `ENFORCEMENT.md`, `SHUTDOWN.md` | the vehicle |

From the **private checkout at the declared base**:
`v12/DESIGN.md` (TOK-\*, HOST-\*, REC-4), `AGENTS.md`,
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

**What is missing is the causal/operation/outcome composition**: which component
ordered this exact runtime stopped, under which operation identity, with what
engine outcome, and whether cessation was established. No record carries that
and no reader composes it. That is the gap.

The absence of a start-failure or preparation-failure record is **expected** for
these components, not proof of the proposed cause.

## REVALIDATE FIRST: what moved under this design

`worker_manager/intake.py` and `worker_manager/attempts.py` are **byte-identical
between `fb487979` and this base** — I verified that read-only this claim, so
(a) to (d) below are the same facts revision 4 carried, re-confirmed at their
current line numbers. (e) is new. Read the committed code before you design
anything.

### a. The runtime identity comes from the TOKEN, not the attempt row

`reclaim_expired_resource` (`intake.py:5611`) takes
`runtime_id = overdue.get("container")`, refuses `identity-mismatch` when the
attempt names a different one, and derives its correlation id as
`reclaim_operation_id(dict(attempt, runtime_id=runtime_id), generation)`.

So **any identity you derive must resolve the runtime the same way** — from the
token's bound container, substituted into the attempt row exactly as the reclaim
does. An identity derived from `attempt["runtime_id"]` is wrong here: the token
may bind a container **before** the attempt attaches it, so that column can be
`None` while a real writer exists. An earlier revision of this task proposed
exactly that mistake and withdrew it; do not carry it forward.

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

### c. There is a held outcome: the token-bound runtime ceased, the attempt never attached

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

`attempts._order_quiescence` (`attempts.py:3490`) resolves the token-bound
container after `request_cancellation` takes the Authority fence, refuses a
conflicting identity, and when neither an attached nor a token-bound identity
exists answers `quiescence_not_ordered` with *"the assignment is fenced but an
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

### e. NEW — the vehicle's own ending is now bounded, and its reports are deadline-aware

This is about the run you are inside, and about one axis of what you build.
`SHUTDOWN.md` is the full account; the parts that bear on this task:

- `tools/authoring_shutdown.py` (**new at this base**) gives one process-local
  shutdown budget derived from `bounds.cleanup_seconds` and capped by the outer
  watchdog's transmitted deadline, subdivided across `cleanup`, `accounting`,
  `workload-publication`, `guard-stop` and `guard-publication`. A repeated
  `begin()` does **not** renew it.
- `bounded(deadline, step)` arms a real-time alarm so blocking main-thread
  steps can be interrupted. It is **cooperative**: it is not proof that
  arbitrary kernel I/O can always be interrupted, and process kill and reap
  remain the backstop.
- The controller report gains `shutdown_deadline` and `shutdown_progress`, and
  `RemoteGuard.stop(timeout=…)` takes a **bounded** final snapshot read,
  returning `state='held'` with the fault appended when it cannot finish. The
  held wording is now *"manager terminated without final enforcement report;
  retained observations do not resolve unknown effects."*
- On a publication `TimeoutError` the controller **returns 1 without renewing
  its budget**, deliberately refusing to manufacture a result and leaving the
  earlier manager, workload and phase evidence as the record. **It does not
  guarantee that nothing was written.** Revision 5 of this task claimed it
  "writes nothing"; that claim is **withdrawn as false**. The bound at
  `authoring_enforcement.py:586-594` wraps `temporary.write_text`, `os.replace`
  **and** `print` in one `bounded(...)` block, so a `TimeoutError` raised during
  the `print` follows an **already-completed `os.replace`** — the final report
  exists — and one raised during `write_text` can leave a partial
  `.enforcement-*.tmp`. No filesystem non-effect follows from that exception.

**The rule, and it is both a reporting obligation and a product axis: a missing
or partial final report is INCOMPLETE. It is never success, never acceptance and
never proof of cessation.** `decisions/shutdown-review.md` states it three ways;
PLAN states it as *no startup success or producer exit substitutes for
final-result acceptance*. Phase evidence identifies the last step **entered** —
it is not a sampled stack and not an independent cessation receipt.

**And absence names no cause.** This is the second half of the correction, and
it is a product axis as much as a reading rule. A final report that is not there
means **the final result is unavailable and why is unknown** — nothing more.
Revision 5 said an absent `enforcement-*.json` "means the outer publication did
not fit"; that inference is wrong, because never started, an import or startup
failure (`FAILURE.md` is exactly that case), process death, a permission or
mount failure, and publication errors that are not timeouts all leave no report
too. So distinguish four states and never collapse them:

| state | what you observed | what it licenses |
| --- | --- | --- |
| **absent** | the path does not exist, and you could read its directory | final result unavailable, cause unknown |
| **inaccessible** | the read failed — permission, mount, I/O | unavailable, cause unknown, and **not** absent |
| **pending** | a `.tmp` sibling exists, so publication was entered and did not complete | unavailable **so far**; not absent and not failed |
| **unknown cause** | present but unparseable, **not a JSON object**, or its identity does not correlate | unavailable as evidence; say which |

**This vehicle persists no publication fault reliably, so absence proves
nothing — and that is sharper than revision 7 had it.**
`decisions/review-340012.md` item 3 established it from the producer's statement
order, and a reader of yours must not claim more. `Shutdown.call`
(`authoring_shutdown.py:72-86`) enters `bounded(deadline, step)` first — an
exhausted deadline raises **there**, before any write — then writes its snapshot
carrying the faults of **earlier** calls, then runs the step, then on failure
appends that step's fault to memory only and re-raises. So a step's own fault
reaches disk only if a **later** `Shutdown.call` writes successfully:

| step | recordable? | why |
| --- | --- | --- |
| `outer outcome publication` (`authoring_enforcement.py:588`) | **no** | not a `Shutdown.call`; the handler at `:592-595` returns 1 and records nothing |
| `final enforcement publication` (`:493`) | **no** | the **last** `Shutdown.call` in the controller's `finally`; nothing follows to flush it |
| `workload publication` (`baseline.py:1461`) | **not reliably** | later calls exist in `main` (`:2796`, `:2884`) but are reached only if control gets there, and each re-enters `bounded()` against the same exhausted deadline |

So: **an absent publication fault is the expected state even when a publication
really did time out.** Naming a timeout still requires a fault naming a
publication step in a **correlated** artifact — a `TimeoutError: manager startup
snapshot` is a real timeout **of something else** — but the honest default is
*unknown*, and a reader that treats absence as informative in either direction is
wrong. If you build a reader over these artifacts, carry this limit in it.

**And a `pending` verdict must come from the artifact's own temporary.** Read the
producers, because the names are not what you would guess: the workload's
temporary is `outcome.json.partial` (`baseline.py:1006`, `path + ".partial"`),
while `with_suffix('.tmp')` *replaces* `.json`, so the controller's is
`outcome.json.enforcement-<pid>-<ns>.tmp` and not `...json.tmp`. And
`outcome.json.manager-*.json` matches `...json.progress.json`, so a progress file
can be mistaken for a manager snapshot. Revision 7 of this packet's own collector
made both mistakes; `decisions/review-340012.md` items 1 and 2 are the account.

**Correlate through the shape each artifact actually has.** The controller report
has **no top-level `run_id`**: its identity is `original_envelope`
(`authoring_enforcement.py:40-52`, stored at `:580`) carrying `run`, `job`,
`authority`. The workload outcome carries `run_id`, `work`, `claim`, `job_id`
(`baseline.py:1453-1458`). The progress file carries `run_id`, `job_id`, `step`
(`authoring_shutdown.py:76-78`). A reader of yours that demands one shape of all
three will report `unresolved` for every real controller report — which is
exactly the defect review339861 caught in this packet's own collector. Prefer
**exact linkage** where the vehicle gives it: the controller names its own
`enforcement_path`, `authoring_log` and `manager_report_path`, and the progress
file for that incarnation is `<manager_report_path>.progress.json`.

**And one malformed artifact must not cost you the others.** A report whose top
level is a JSON array is an observation about that report; it is not an exception
that abandons the rest of the evidence. Your readers carry the same obligation.

## The milestone, and it is these seven things

**Items 1 to 5 are mostly DONE in the candidate you just applied.** Read what is
there before you write anything: `failure_cause.py` already composes the typed
cause with explicit `unknown` and `absent_records`, resolves the runtime from the
token, keeps known-with-source and unknown-with-reason as the only two shapes,
and reports the revocation beside an unknown cause. `tools/attempt_diagnostics.py`
already allowlists and refuses nested-object forwarding. Both owed test modules
already exist. **Your job is items A, B and C — the three blockers — plus item 6
and item 7.** Everything else is review, preserve and extend.

### A. CONNECT THE SEAM. This is the one that matters most.

`decisions/review-340349.md` blocker 1. The candidate changes **no `job_manager`
file at all**: `job_manager/projection.py:_stage_status` emits no
`attempt_diagnostics`, `failure_cause.attempt_failure_cause_of` has **no
production caller**, and the report reads only `stage["attempt_diagnostics"]`. So
ordinary status cannot carry the account and the report can only ever see a
fixture. **Fixtures on both sides of an unjoined seam prove nothing.**

Required: the same owner-backed facts travel into **ordinary versioned status**,
and the report consumes **those actual bytes**.

- a production caller composes the cause into the ordinary status document — the
  observation member is composed in `job_manager/delegation.py`
  `ManagerOperations.observe`, and `job_manager/projection.py:_stage_status` is
  where a stage's members are emitted;
- the member is **versioned** and owned, so an older document reads as unknown
  rather than failing, and a newer reader does not silently accept a shape it
  does not own. `STATUS_SCHEMA` moves if the document's shape moves;
- **episode and runtime correlation is preserved** across the join: the status
  row's attempt, episode and runtime identity must still agree with the token's
  bound container after composition;
- the read stays **read-only** — no claim, renewal, reconciliation,
  acknowledgement, retry, store creation or migration;
- and the demonstration is **one real failed-attempt status row** read through
  the ordinary reader, whose bytes the report then consumes. Not two shapes
  invented independently.

### B. ONE OWNED SHAPE ACROSS ALL THREE SIDES

`decisions/review-340349.md` blocker 2. Today the producer and the report
disagree even if the member were attached verbatim:

| producer composes | report expects | result |
| --- | --- | --- |
| `_known(value, source)` wrappers for `start_failure`, `preparation_failure`, `revocation`, `completion`, `token`, `domain`, `generation` | raw scalars in `EXECUTION_MEMBERS`/`WORKSPACE_MEMBERS`, and `_typed` refuses nested objects | a recorded **known** value is reported **unknown** |
| `outcome` = the nested outcome document, scalar in `outcome_state` | `CAUSE_MEMBERS` has `("outcome", (str,))` | unrecognised |
| `correlation_id` | a top-level `operation_id` | absent |
| token, renewal, completion, start and preparation facts | not in the member lists at all | silently dropped |

Required: **one explicit owned and versioned diagnostic shape** across producer,
ordinary status and shareable report — including the required limits, token,
time and causal fields. Decide where the wrapper lives and make all three sides
agree; either the report understands `known`/`value`/`source`, or the status
member carries scalars with the provenance beside them. Either is defensible;
**two different answers is not.** Verify the actual production composition, not
two fixtures.

Keep what the wrappers are *for*: a known zero is not a missing count, and an
unknown still names what is absent.

### C. MAKE THE DURABLE INTENT ACTUALLY DURABLE, AND REPLAY TRUTHFUL

`decisions/review-340349.md` blocker 3. `record_cessation_intent` is documented
"NEVER RAISES" and returns prose; **all four acting call sites discard it**, and
two order effects immediately after:
`attempts._order_quiescence` → `agent.cancel`/`adapter.stop`, and
`intake.settle_revoked_resource` → `govern.release`. So under a recording failure
the effect happens with **no durable intent** — the exact property the design
promised.

Required, without weakening existing fencing or cleanup:

- the promised order actually holds: **intent durable before the effect is
  ordered**, on both the cancellation and the settlement paths. A recording
  failure must be **observable** — reported, and not silently stepped over. You
  may decide that some failures must refuse the effect and others must proceed
  with a recorded, reportable degradation; what you may not do is promise
  durability and deliver best-effort;
- `record_cessation_outcome` must stop swallowing collisions. Outcome identity
  is fixed by attempt/assignment/start/component/generation, so an **uncertain**
  first observation followed by a **later positive** one collides under the same
  id and the first is retained. **A historical uncertainty must not become an
  enduring substitute for better later evidence.** Decide the rule — a
  distinguishing identity, or an explicit supersession that keeps both and says
  which is current — and make a reader able to see it;
- and prove it on the **production paths**, not on a seam: interruption, a
  recording failure, and an uncertain-to-positive replay, on **both release
  paths** (the reclaim's own `govern.release` and
  `settle_revoked_resource`'s). `decisions/review-340349.md` is explicit that its
  finding is static and that those injected tests have **not** been run.

### 6. Report what you can actually observe — and nothing you cannot

Unchanged from the previous revision, and the run proved it right: the
controller's report, the workload outcome and the shutdown progress file are all
published **after** your turn ends, so you cannot see them and must not report
them as present, absent, complete or incomplete. Name them structurally
unavailable to the worker. Your half is your progress per item, the retained
candidate with exact paths, which tests you ran and what they measured, the
lease and cessation facts you **positively observed from inside**, and your
correlation keys (`run_id`, `work`, `claim`, your pid, `outcome_path`,
`status_path`). The operator and the reviewer collect the rest.

**One correction from the completed run: do not plan around expiry.** The
previous turn ended on its own at 869.3s with 30.5 seconds of margin against the
900-second lease; `provider.status` was 0. The lease is still 900s and still
enforced, so it may fire — but it did **not** last time, and an account that
blames expiry for an outcome expiry did not cause is a false account.

### 7. NEW — CLASSIFY THE GATE RESULT. The previous run could not.

The run's gate **exited 1** and its output is withheld by design: it ran with the
attempt's credential mount readable, so the stdout and stderr are exactly what a
proposal must not carry. A generated line in `verification.txt` suggests the
operator rerun it on the host. **`decisions/review-340349.md` is explicit that
this is not authority** — AGENTS applies, there is no product-test exception for
W333486, and the one selected invocation is consumed. **So the classification is
yours, inside this run, and it is a deliverable.**

Run the sealed gate yourself during your turn and report, in your own words and
without pasting raw output:

- **which modules failed and how**, by name and assertion — enough for a
  reviewer to act, carrying no credential, environment value, private transcript
  or provider text;
- **per-module elapsed seconds**, and the total against the **30-second**
  `verification_command_seconds` ceiling. This answers the question this campaign
  has carried unproved since revision 2: **does the gate fit with the two new
  modules?** If it does not, say so with the numbers — that is a real finding and
  not a failure to deliver;
- **whether the ceiling was material to the previous run's exit 1** — a genuine
  test failure, a timeout kill, or both — or that you could not tell, and why;
- and if you cannot reach the gate at all, say that plainly with what you did
  reach.

**Do not weaken a test, remove coverage or relax an assertion to obtain a pass.**
A failing gate honestly classified is worth more here than a passing one bought
by deletion, and the review will check for exactly that.

## The standing specification: items 1 to 5

These are the obligations the candidate was written against and the ones your
corrected work is still judged by. They are reproduced verbatim from the task the
run executed, so that you can check what it built against what was asked rather
than against a summary. **Most of this is already present in the patch you
applied — review it, keep it, extend it. Item A above is where the candidate
stopped short, and items 1 and 5 below are the ones it did not finish.**

### 1. Capture the cause across the paths that actually run

The reclaim is not one act with one release:

- `reclaim_expired_resource` revokes, stops, removes, observes — then
  `_resource_cessation` (`intake.py:1122`) answers `None` unless a committed
  cleanup carries both halves of its proof, and `_custody_already_committed`
  (`intake.py:5756`) answers `None` for a running attempt whose roots were
  never normalized. The ordinary outcome for a reclaimed live attempt is
  therefore **`held`**, and the reclaim's own `govern.release`
  (`intake.py:5750`) is never reached.
- `tools/job_manager.py:_reclaiming` then calls
  `intake.settle_revoked_resource` (`intake.py:5781`), and **its**
  `govern.release` (`intake.py:5927`) finishes the generation.

Requirements, implementation shape yours:

- Capture **eligibility and intent at the boundary that orders the effect**,
  durably, **before** the engine is asked — so a crash between an effect and any
  later record cannot lose the fact that this manager ordered this exact
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
  its own outcome, and the fenced-but-unresolved case reported as the typed fact
  it is.
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
ordinary answer. A refused row under that identity is a collision, not evidence.

### 3. A known failure is not an unknown

The manager may know a **typed stop or engine failure** while cessation remains
**unknown**. Both must be preserved and exposed separately. The vocabulary must
distinguish at least:

- cessation positively established by an exact correlated observation —
  `absent` and `quiescent` are **not** the same fact;
- **a known typed stop/engine failure** — refused, timed out, or could not be
  asked — carried with its typed category and code, cessation explicitly
  unknown;
- an **uncertain observation**: the effect crossed and what exists now could not
  be established;
- an **exact-runtime mismatch** — which the accepted bytes raise as
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
  `runtime_id`, the token-bound container when they differ, the last observation
  instant and the activity projection with its own instant.
- **Safe locators only** — see below.
- Every member either **known with its source**, or **unknown with a bounded
  reason**. A missing count is never a zero; an observed zero is a known zero.

Snapshot state is evidence, never a replacement for current authority
(`decisions/review-333812.md`): report what was recorded, and do not let a stale
record outrank a current axis read.

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
  `tools/worker_visibility.py`'s accepted discipline: a **pure projection** over
  one status document read through `tools/job_viewer.py:read_snapshot`; **no
  store, no clock, no engine, no provider, no subprocess**; its own schema
  version; a **positive member allowlist** with a declared type per member and
  no nested-object forwarding; per-fact provenance and bounded unknown reasons;
  no freshness verdict, because no freshness policy has been selected.
- Reached through **`tools/stack_command.py` `COMMANDS`**, the way `logs`,
  `record` and `disposition` are.

  **A source-level case is not proof that a rebuilt bundle carries the
  command.** Assert the table and the dispatch in source, and state the
  remaining deployment obligation explicitly in the module and in your report.
  Do not rebuild the bundle.

The files and schema names above are **design proposals to revalidate**, not
permission gates — except the two sibling-owned files, which are a coordination
boundary, the three vehicle files from (e), which you do not touch, and the
accepted `intake.py`/`attempts.py` semantics, which you extend rather than
rewrite.

## The locator obligation: a demonstration, not a field

Device and inode identify a workspace *object* and are **not** a usable
retained-output locator. The supported path is the deployed `logs` subcommand
over `worker_manager.attempt_logs`:
`baton-v12-stack logs --logs <launch-home>/logs --attempt <id> locators`.

- emit the attempt identity and whatever locator the **manager itself recorded**
  (the frozen result's `artifacts`), under the allowlist;
- emit the exact supported invocation shape and name the one operand the
  operator must supply — the delivery root — and say why this report does not
  resolve it: a report that resolved a deployment document would be a reader
  that can be pointed at a store;
- keep device/inode, labelled an object identity, explicitly **not** a path and
  **not** a locator by itself;
- **demonstrate the round trip**: a case that takes the report's emitted locator
  fields, feeds them to the supported `attempt_logs` reader over a real retained
  delivery, and shows the operator reaches the retained evidence — while the
  report carries no stream content, no credential, no environment value and no
  private text.

## The axes that must survive, demonstrated rather than asserted

- an **exceptional** stage does not prove runtime cessation;
- **missing artifacts** do not prove there are no retained partial edits;
- **observed activity** does not prove valid permission;
- a **diagnostic cause is not candidate acceptance**;
- an **ordered effect** does not prove it happened, and an **absent record**
  does not prove nothing happened;
- **quiescent is not absent**: a stopped-but-present container is still a
  container holding its mounts;
- an **uncorrelated absence** does not prove cessation; only an exact correlated
  positive observation does;
- a recorded manager failure is reported **even when the agent sent no final
  message**;
- **an incomplete final report is not an acceptance, and a deadline-bounded
  publication failure is not cessation evidence.** A reader that turns a missing
  report into either one is wrong in the same way as one that turns an absent
  record into proof that nothing happened;
- **an unavailable report names no cause.** Absent, inaccessible, pending and
  unknown-cause are four different facts and a reader must keep them apart; and
  a bounded publication failure guarantees no filesystem non-effect, so "the
  report is missing" never licenses "nothing was written". Item (e) has the
  table;
- **a cause is named only from evidence that is both SPECIFIC and CORRELATED.**
  A timeout of some other step is not a publication timeout; a fault in an
  artifact about another run is not evidence about this one; and where the
  vehicle cannot record a cause, the honest answer is unknown rather than the
  most likely story. Item (e) has the publication-step table;
- **NEW: where the producer does not persist a fault, its absence is EXPECTED
  and informative in neither direction.** This vehicle records no publication
  fault reliably — so "no timeout fault on disk" is not evidence that there was
  no timeout, and finding one is parsing, not proof that the producer records
  them. Reason from the producer's statement order, not from what a field name
  suggests;
- **NEW: evidence belongs to the artifact whose name it carries.** One
  artifact's temporary says nothing about another's publication, and a file
  whose name merely resembles another's is not that other. Both mistakes were
  made in this packet's own collector and are now regression probes;
- **NEW: an artifact is correlated through its own shape, and one malformed
  artifact does not invalidate the rest.** Demanding a field the producer does
  not publish yields a false `unresolved`; aborting on a bad shape loses
  evidence that was perfectly readable.

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
- the **token-bound-before-attachment** case (a) and (c), including the held
  outcome;
- the **replay effects** (b), as three distinct cases: a revoked generation
  observed **`absent`** orders neither stop nor removal; one observed
  **`quiescent`** skips the stop but **still removes**; anything else does both —
  and the record distinguishes all three;
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
- a **stale** observation, and one belonging to a **different episode or runtime
  identity** — reported as unknown with the reason, never re-attached;
- outstanding cleanup, and an unresolved termination;
- **an incomplete final result**: a status document whose recorded facts are
  partial the way a bounded publication failure leaves them, proving the report
  says *incomplete* and neither *cessation* nor *accepted*;
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

Ten existing modules plus the two you must create. The numbers below were
measured at **this** base against a clean export with a deliberately useless
ambient `PYTHONPATH`: **1124 tests, all passing, zero skips, 13.642s** unittest
time / 14.007s measured.

**AND THERE IS NOW A REAL MEASUREMENT OF THIS GATE, WITH ONE UNKNOWN.** The
completed run executed exactly this sealed argv against its candidate and it
**exited 1**, with the output withheld by design. So the gate has been run once
on real work and the result is: fails, cause unclassified. Item 7 makes
classifying it your deliverable. The figures below remain the pre-run baseline.

**Read that attribution carefully, because it is not preparation evidence.**
These figures were obtained by **direct host product test execution at
claim339421, outside that claim's preparation-only boundary**; the preparing
author recorded the error in `PROGRESS.md` and `decisions/review-339623.md`
item 3 is the finding. They were **not** re-measured at claim339628 — rerunning
them to tidy the provenance would repeat the same mistake — and they are **not**
independent product acceptance. Treat them as a useful prior measurement with a
known defect in how it was obtained, and measure your own gate yourself.

```
tests.job_manager.test_status             65
tests.job_manager.test_delegation         44
tests.job_manager.test_documents          31
tests.job_manager.test_tool               72
tests.manager.test_intake                207
tests.manager.test_maintenance           148
tests.manager.test_attempts              431
tests.tools.test_worker_visibility        78
tests.manager.test_contracts_inventory    15
tests.manager.test_authoring_enforcement  33
```

**Two real-process modules are deliberately NOT in the gate, both for a
measured ceiling reason rather than a coverage judgement.** Both measurements
come from the same out-of-boundary claim339421 execution described above, so
these two exclusion decisions rest on measurements obtained outside the
preparation boundary — stated here rather than laundered:

| module | measured | coverage carried by |
| --- | --- | --- |
| `tests.manager.test_authoring_shutdown_deadline` | **51.333s / 4 tests** — over the whole ceiling by itself | `decisions/shutdown-review.md`: 44 tests, no skips, 72.891s unittest, authority338596 |
| `tests.manager.test_authoring_manager_guard` | **19.888s / 7 tests** — would put the sealed gate at 33.5s | `decisions/guard-integration-result.json`: 79 tests PASS, 15.278s, authority337376 |

You edit none of the three files those modules cover. **If that ever changes,
run the affected module as a focused check outside the sealed argv and say so.**

`test_intake`, `test_tool` and `test_attempts` are in the gate because item 1's
composition lives across them. `test_authoring_enforcement` is in it because
your change touches `intake.py` and `attempts.py`, which that module covers —
**do not break the accepted enforcement correction.**

A sealed argv cannot name classes that do not exist yet, so the two new module
names are **part of the contract**:

| new module | what it must cover |
| --- | --- |
| `v12/python/tests/manager/test_attempt_failure_cause.py` | the typed records, their public readers, reclaim-to-settlement and cancellation composition with restart cuts, the token-bound identity rule, replay-with-no-effect, the known-failure/unknown distinction, the composed cause with every unknown branch, every preserved axis, and the secret canaries |
| `v12/python/tests/tools/test_attempt_diagnostics.py` | the report: allowlist, provenance and unknown reasons, refusals, that it opens no store and spawns nothing, the incomplete-final-result case, the locator round trip, that `stack_command.COMMANDS` serves and dispatches it, and the explicit rebuilt-bundle obligation |

**The ceiling is 30 seconds and is not negotiable on this vehicle.**
`baseline_bindings.py:345` composes `"verification_command_seconds": 900 if
contextual else 30` and `:522` repeats the 30 — and the `contextual` branch
discards this packet's task and verification entirely in favour of the built-in
`TASK_INSTRUCTIONS` and `["python3", "harness.py"]` (lines 363 and 367). A
fresh-context packet is the only shape that can carry this task, so 30 it is.
The ten existing modules spend **13.642s**, leaving roughly **16.36 seconds**
for the two new ones. That is a real design constraint, and
`decisions/review-334776.md` is explicit that the fit **remains unproved** and
that no coverage may be removed to force a pass. If the gate cannot be made to
fit, **report it honestly with the measured numbers**.

**No skip is admitted.** The gate program fails on a skipped case.

`tests.manager.test_authoring_enforcement` needs
`work/records/2026/09/finding-v12-single-implementation-proof` present at the
checkout root — it spawns a real supervisor. Measured: 1 error without it, all
33 passing with it. The private checkout carries it; see `ENFORCEMENT.md`.

## Boundaries

- **No edit to anything under `/input`.** The mount is read-only on purpose.
- **Overlap is declared, not prohibited.** Revision 5 made
  `tools/job_manager.py` and `job_manager/manager.py` an absolute forbidden list
  purely because W333485 declared them. `decisions/review-339623.md` item 4
  corrected that: both candidates are isolated, and policy requires actual
  overlap coordination and serial reviewed integration rather than immutable
  file prohibitions. So:
  - **the expected shape is still that you do not need them.** The composed
    observation member lives in `job_manager/delegation.py`
    `ManagerOperations.observe`; `tools/job_manager.py:_status` only supplies a
    read-only operations object. Prefer the surfaces in `decisions/FINDING.md`.
  - **if the accepted outcome genuinely requires an edit there**, make it —
    and declare the exact overlap (file, symbol, why) to W333485 before the
    combined candidate exists, keep it to what the outcome needs, change no
    shared tree, and expect serial independent integration. An undeclared edit
    to a sibling-declared file is the actual violation; a declared, necessary
    one is not.
  - `worker_manager/intake.py` and `worker_manager/attempts.py` are the
    **already-declared** overlap with the accepted corrections: keep edits to
    attribution on the reclaim, settlement and cancellation paths, **preserve
    the committed enforcement semantics**, and expect serial integration.
  - **vehicle repair is still out of scope** and this is not a licence to
    broaden: the point is that necessity is judged against the accepted
    outcome, not against a file list.
- **Do not touch the vehicle**: `tools/authoring_enforcement.py`,
  `tools/authoring_shutdown.py` and
  `work/records/2026/09/finding-v12-single-implementation-proof/baseline.py`
  are the accepted corrections you are running inside. Their proof is reused
  rather than re-run, and the two excluded real-process modules are excluded on
  the condition that you do not edit them.
- **Do not "fix" `baseline_bindings.py`.** Its `start` command is wrong for this
  vehicle (`ENFORCEMENT.md`) and correcting it is host product work this Work
  does not own. Report it; do not patch it.
- **`tests.manager.test_boundary_inventory` does not pass at base** — an
  explicitly unverified baseline report, measured 328 tests / 28 failures /
  1 error / 49.469s on an earlier base's bytes and **not re-measured this
  claim**, excluded from the gate, with no cleanup selected. Do not fix it and
  do not report it as this candidate's. Do keep its declarations honest for the
  boundary **you** add: register the receiving entries and probes your change
  introduces, and report what you registered.
- **`tests.tools.test_packaging` is excluded too** — it holds the source command
  table against the installed bundle, which predates `record` and
  `disposition`, so it already fails on the host, and inside a private checkout
  it SKIPs, which the gate refuses. Also an unverified baseline report.
- `tests.manager.test_dependencies` also fails at base for reasons that predate
  this Work. Not yours.
- **No broad suite sweep** and no unrelated test cleanup or weakening.
- No image build, no container, no engine call and no provider call inside this
  task. No host product edit outside the private checkout, no integration, no
  self-acceptance, no deployment, no mutating version-control operation beyond
  what the line profile itself performs, no edit to historical evidence.
- **The failed native pilot, all eight earlier packets, the failed
  execution-334663 instance AND THE COMPLETED RUN at
  `/home/sl/baton-instances/attempt-diagnostics-w333486-340016` with its
  retained candidate are preserved.** No retry, no rerun, no runtime
  recovery, no mutation, no credential or transcript read.
- **Both temporary direct-implementation exceptions have expired** and neither
  ever covered diagnostics. `AGENTS.md` at this base still shows the older
  W321689 exception section because the host's replacement of it is an
  uncommitted edit; it is expired either way and grants nothing here.
- Independent review and the human Git checkpoint remain required. A retained
  candidate is not an accepted one.

## Honesty obligations

**The lease is 900 seconds, enforced, and it did NOT fire last time.** The
completed run ended on its own at 869.3 seconds with `provider.status 0` — 30.5
seconds of margin. So plan for the budget, but do not pre-write an expiry
narrative: an account that blames expiry for something expiry did not cause is a
false account, and this author has already had to withdraw that prediction once.

**Expect the 900-second lease to be enforced.** `tokens.LIFETIME_SECONDS` is
still 900; production renewal is still W333485's unfinished Work. The
enforcement correction made that lease real and the shutdown correction made the
ending bounded — **neither extends it** — so the 3600/4800 ceilings are not a
promise of a 3600-second authoring run. If your turn is terminated that way,
preserve the partial candidate and account for what is missing: the retained
candidate checkpoint, your progress per item, and the expiry and cessation facts
**you positively observed from inside**. Item 6 is how — and it is also where
you will find that the host-side final results are the operator's and the
reviewer's to collect, not yours to guess at.

**A bounded first milestone is allowed.** PLAN says so explicitly: if the
outcome cannot fit 900 seconds, deliver a coherent bounded slice and state the
remaining work explicitly — without weakening final acceptance, removing
coverage or promising full completion in one run. The whole outcome stays open
even if a first run yields partial work.

**And know that this vehicle has failed once already.** `FAILURE.md` records the
previous selected run dying at startup in 0.506s because the controller composed
two managers for one workspace. That defect is corrected, and so is the ending
behaviour — but **no authoring invocation has ever completed for this Work**,
and two corrected failures are not a demonstration that this one completes. If
yours does not either, the honest account of how far it got is the deliverable.

Report honestly if the milestone is only partly reached. State which items are
delivered, which tests ran, what they measured, and cumulative verification
spending. Do not label an environmental failure as formal success, and do not
weaken an existing assertion to obtain a pass.
