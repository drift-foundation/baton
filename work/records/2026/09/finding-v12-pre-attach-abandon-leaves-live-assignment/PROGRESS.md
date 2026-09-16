# Progress

Not started. The run3 authority and recovery record remain disposable evidence;
W61984 continues only under a fresh authority and attempt identity.

## Claim 174231 — baton.claude, implementation

Unparked W63255 to `queued` at seq 174230 under the configured `baton.impl`
Handler, per poke 174223 and owner M174212, then claimed standalone at 174231.
Read the FINDING through the 2026-09-14 selection, the 2026-09-01 reviewer
revalidation, the approved 2026-09-02 direction, M174212's exact path list, and
`evidence/research-2026-09-01/README.md` in full — which my own W174050 pre-work
had flagged as unread.

### What was implemented

**`fence_pre_attach_abandonment(store, port, *, attempt_id, reason)`** in
`worker_manager/intake.py`, colocated with abandonment so it shares the private
intent and fence primitives, named as the research recommended rather than
widening `abandon_attempt` into two result shapes. It reuses `_abandon_intent`,
`_abandon_fence_operation_id` and `AuthorityPort.cancel`, and fences with the
**adopted record's own** operation id and reason so a resumed call reissues the
same authority act.

**`_no_start_declared`** is the eligibility body that closes the race. It runs
inside the declaration's own transaction: it requires `runtime_id is None` and
`execution_runtime == "not-started"`, calls the existing `_declared` for the
three attached checks rather than restating them, and moves the axis to
`cancel-requested` in the same transaction. That makes the two outcomes
exclusive — if a start won, this refuses and fences nothing; if this won,
`request_runtime_start` can no longer pass its own precondition.
`_abandon_intent` gained an optional `declare=` parameter defaulting to
`_declared`, so **attached abandonment commits exactly what it always did.**

**`_pre_attach_recovered`** now takes `port` and `reason` and calls the fence
**before** any resource account is taken, recording the exact answer in
`record["authority_fence"]`. A refused fence returns `_unresolved` naming it.

### Verification

- Step 10, both selected modules: `OK`, **780 checks**, supervisor 8.1 s.
- Supervised reversals, each restored:

| Reversal | Result |
| --- | --- |
| the fence answer is not recorded | **3 cases fail** (step 06) |
| the no-start guard removed | **1 case fails** (step 09) |

**Two earlier reversal attempts silently no-opped** — step 04 on an indentation
mismatch and step 08 on a string that occurs twice in the file — and both
"passed". I am recording them because a reversal that fails to apply looks
exactly like a reversal that proves nothing, and steps 06 and 09 are the real
evidence.

- Ledger `ledger-63255.json`: **10 rows, 65.024305 s**. No run timed out, none
  was signalled, every run proved its process group gone.

### Paths, against M174212's list

Changed: `worker_manager/intake.py`, `worker_manager/__init__.py` (export only),
`tools/dogfood_operator.py`, `tests/tools/test_dogfood_operator.py`.

**`tests/manager/test_attempts.py` was NOT changed** — no manager-side change
was needed, so there was nothing to cover there; the new operation's own race
case drives it directly from the operator module's fixture.
**`worker_manager/__init__.py` is not on M174212's list**; it carries only the
export line, without which the operation is unreachable. Flagging rather than
assuming it is covered.

### Scope held

`abandon_attempt`, `request_cancellation`, `AuthorityPort.cancel` and W61984's
finalizer are untouched. No output freeze, intake, retention, custody, review,
integration or Baton pass. No Git mutation, no engine, model or image.

Candidate `candidate-174231.json`.

## Claim 174442 — corrections after review 174408 and owner selection M174440

Read return174408, `review-2026-09-15T03-05-11Z.md`, `EXPORT-AMENDMENT-174362.md`
and the reroute. **Pinned the owner selection in FINDING.md and PLAN.md before
editing**, as M174440 requires: the export amendment is selected, limited to the
two import/`__all__` entries, with the accepted W32577 baseline
`cd783420…` and the proposed `cce4b686…` recorded.

### The defining outcome is now proved, and the review's fixture reading was off

**P1 #1 is resolved, and the correction runs in an unexpected direction.** The
review read the arc's `ArcSession` and took it for the abandonment crossing.
That is not what happens: the arc uses `ArcSession` to **run the worker**, while
`_for_abandonment` (`dogfood_operator.py:4535`) opens the **real disposable v12
Authority** this fixture creates in `setUp` and builds a real `DeploymentSession`
over it. My class inherits that fixture through
`ThePublicRetryRunsFromRealDurableState`.

So the real-Authority capability was already there. **The review is still right
about the test**: the defining outcome was reachable and I never asserted it.
Measured before and after the documented command, against the real store:

| | `phase` | `handler` | `slot_holder(participant)` |
| --- | --- | --- | --- |
| before | `active` | `baton.claude` | the Work |
| after | `block` | `null` | `None` |

`test_the_documented_command_fences_a_pre_attach_assignment` now asserts all six,
through two new helpers that open the fixture's own authority store and dispose
it. The partial-resource-account fence assertion is retained beside them.

Reversal (step 12): replacing the `port.cancel` crossing with a locally
constructed fence document — same shape, never sent — **fails the case**. The
assertion is on the authority's actual state, not on a returned dictionary.

### Provenance corrections

Both comments the review named are corrected. The `abandonment_owners` helper
now says plainly that its session is a **fixed-reply** one, and why that is the
right instrument for a case asserting a refusal. The race case no longer claims
a fresh observation selects the attached branch: as the review says, a requested
start may still have `runtime_id is None`, so the next observation may take the
pre-attach branch again. It proves the refusal and the absent declaration and
says nothing about which branch follows.

### Verification

- Step 13, both selected modules: `OK`, **780 checks**.
- Reversals, each restored: fence answer not recorded → 3 fail (06); no-start
  guard removed → 1 fail (09); **authority crossing replaced by a local
  document → 1 fail (12)**.
- Ledger: **13 rows, 85.431212 s**. No run timed out, none was signalled, every
  run proved its process group gone.

Candidate `candidate-174442.json`. `intake.py`, `__init__.py` and
`dogfood_operator.py` are unchanged since candidate-174231; only
`tests/tools/test_dogfood_operator.py` moved
(`sha256:24ca117e9fde375d…`, 367744 bytes, mode `0644`).

### Still owed from review 174408 — NOT delivered this claim

I am naming these rather than implying the matrix is complete:

- **Paired false/wrong-fence refusal** — absent, wrong-generation or
  not-true fence must leave the record unresolved, exit nonzero and prevent
  resource cleanup.
- **Substantive durable replay** — original-reason retry with **reopened
  owners** and a durable effect count, rather than comparing two returned
  dictionaries. My retry case still compares dictionaries and is therefore
  weak evidence; the review is correct about it.
- **Changed-reason collision.**
- **Abandonment wins before a public `request_runtime_start`** — no adapter
  start, no surviving start intent. Only the start-wins order exists.
- **Interruption after intent/before fence, and after fence/before cleanup**,
  with controlled deterministic cutpoints.
- **Resource refusal after the fence**, then successful original-reason retry.
- **Wrong fixed assignment/participant/eligibility refusal** before either
  fence or cleanup, and the retained non-effects.

## Claim 174593 — the defining success outcome, and a gap it exposed

Read return174577 and `review-2026-09-15T03-24-46Z.md`. The reviewer withdrew
the earlier `ArcSession` attribution and confirmed the command and the retry
already run against a real disposable v12 Authority with reopened production
owners. The remaining work was already authorized, so this claim continued it.

### The successful outcome, and why it was not reachable before

`_pre_attach_recovered` could not resolve in the shared fixture because
`recover_credentials` refuses when a credential lifecycle record names a
container the engine cannot find — "0 runtime(s) carry this attempt's labels".

**The FINDING's own observed state is the one that resolves.** W61984 run3
recorded *"No credential bearer, container or provider turn started"*. The new
`unbearered()` helper reaches exactly that: the shared fixture's activated,
never-started attempt with its bearer and lifecycle record removed. Everything
else — durable stores, real authority, real command — is unchanged.

`test_a_pre_attach_abandonment_resolves_and_releases_the_assignment` now proves
the defining criterion end to end: **status 0**, `resolved` true, `unresolved`
empty, the exact fence with the fixed generation, and — against the real
authority — `handler` `null`, `phase` `block`, the participant's slot released,
beside a complete resource account.

### A real gap in my own implementation, found by the paired refusal

Writing the paired refusal case failed, and it was **not** the test's fault:
`_pre_attach_recovered` recorded whatever fence answer it was handed **without
requiring it to be positively fenced for this fixed assignment.** The research
README says `resolved` additionally requires `fenced is true` and the fixed
generation; I had not implemented that.

The operator now holds the answer to what it must say — `fenced is True` and the
assignment equal to this attempt's fixed one — and returns `_unresolved` before
any resource act otherwise. `AuthorityPort.cancel` already relates a real fence
to the four members, but the **record** is what an operator reads and `resolved`
is what it claims; treating an unproved answer as proof would have rebuilt this
Work's own defect one layer higher.

`test_a_fence_that_did_not_fence_leaves_everything_unresolved` covers both
shapes — not-true, and true-but-for-another-assignment — and asserts nonzero,
unresolved, and that **no runtime account was taken**, so nothing destructive
followed an unproved fence.

### Also added

- `test_a_changed_reason_collides_and_never_fences_again` — a different reason
  is a different declaration; it collides, and the original fence stands.
- `test_the_original_reason_replays_one_durable_declaration` — a same-reason
  retry through **reopened owners** (the command opens its own stores and
  authority each run) yields the same fence **and exactly one committed
  `attempt.abandon` operation**, counted at the manager rather than inferred
  from two equal answers. That is the substantive replay evidence the review
  asked for; the weak dictionary comparison is superseded.

### Verification

- Step 17, both selected modules: `OK`, **784 checks**.
- Reversals, each restored: fence not recorded → 3 fail (06); no-start guard
  removed → 1 fail (09); authority crossing replaced by a local document → 1
  fail (12); **fence answer not held to what it must say → 2 fail (16)**.
- Ledger: **17 rows, 114.092386 s**. No run timed out, none was signalled,
  every run proved its process group gone.

### Provenance

`candidate-174593.json` binds four paths with hashes, byte counts and modes, and
records the accepted W32577 baseline `cd783420…` for `__init__.py` beside its
current `cce4b686…`, so the two selected export entries are the whole delta on
that file. `intake.py` and `__init__.py` are unchanged since candidate-174231.

### Still owed — NOT delivered

- **Both public start/fence orders.** Only the start-wins order exists, and it
  drives the manager operation directly rather than racing a public
  `request_runtime_start`. Abandonment-wins is absent.
- **Interruption after intent/before fence, and after committed fence/before
  cleanup**, with controlled deterministic cutpoints.
- **Resource refusal after the fence**, then a successful original-reason retry.
- **Wrong fixed assignment / participant / eligibility refusal** before either
  fence or cleanup, and the retained non-effects on
  output/intake/retention/review/integration and W61984's none-disposition.

## Claim 174768 — the remaining matrix completed

Revalidated `candidate-174593.json` against the tree before editing: all four
files matched. Direct completion per reroute 174746; **only the test file
changed this claim.**

### The six cases added

1. **`test_the_abandonment_wins_and_a_public_start_can_no_longer_pass`** — the
   other public order. After the fence, the ordinary **public**
   `attempts.request_runtime_start` refuses on its own precondition, the
   adapter is never reached, and **no `runtime.start` operation survives** for
   a later replay. With the existing start-wins case, both orders now exist.
2. **`test_an_interruption_after_the_intent_resumes_the_same_fence`** — cut one.
   The declaration commits, the authority call dies, and the retry adopts that
   declaration: **still exactly one `attempt.abandon` operation** afterwards,
   not a second under a fresh identity.
3. **`test_a_resource_refusal_after_the_fence_keeps_it_and_then_retries`** —
   cut two and its recovery. The fence commits, the credential teardown then
   refuses, and the durable record **still carries the exact fence**; the
   original-reason retry then completes with the same fence.
4. **`test_a_wrong_participant_refuses_before_any_fence_or_cleanup`** — identity
   held first: **zero** declarations committed.
5. **`test_the_ending_decides_nothing_about_output_or_custody`** — the retained
   non-effects: `output` stays `open` and `worker_disposition` stays `none`
   across a successful abandonment, so W61984's requirement is neither invoked
   nor relaxed.

### Two wrong turns worth recording

- I first drove the resource refusal through `_launch_after` raising
  `OperatorRefusal`. That **propagates out of the command** rather than becoming
  an unresolved account, so it proved nothing about the record. The refusal the
  pre-attach path actually absorbs is a `ContractRefusal` from the orphan
  teardown, and the case now uses that.
- My `attempt_row` helper **collided with an existing fixture method** of the
  same name and different signature, breaking two unrelated retry cases. Renamed
  to `abandoned_attempt_row`. Both were my errors, caught by the suite.

### Verification

- Step 20, both selected modules: `OK`, **789 checks**.
- Reversals, each restored: fence not recorded → 3 fail (06); no-start guard
  removed → 1 fail (09) and again → 1 fail (21); authority crossing replaced by
  a local document → 1 fail (12); fence answer not held to what it must say →
  2 fail (16).
- Ledger: **19 rows, 126.550349 s**. No run timed out, none was signalled, every
  run proved its process group gone.

### Provenance

`candidate-174768.json` records, per path, the current hash, byte count, mode,
the **prior candidate hash** and whether it changed this claim — three unchanged
since candidate-174593, one changed — plus the accepted W32577 baseline for
`__init__.py`, so the two selected export entries remain the whole delta there.

### Remaining

The eligibility refusal beyond wrong-participant is not separately covered;
`_require_assignment`/`_require_participant` and `_no_start_declared`'s own
checks are exercised, but a wrong **fixed assignment** case distinct from the
participant one is not. Naming it rather than implying the matrix is exhaustive.

## Claim 174869 — two of three remaining items, and one exact blocker

Only the test file changed this claim; the three source files are unchanged
since candidate-174768.

### Delivered

**`test_an_interruption_after_the_fence_resumes_one_authority_effect`** — the
real cut two. The fence **commits at the authority** and the process dies before
any resource act. The case reads the authority's own
`operation_record(authority.abandon-fence:…)`, confirms it exists **and that the
participant's slot is already released before any resource act ran**, then
retries and asserts the authority record is **unchanged** — one durable
authority effect, counted at the authority rather than inferred from the single
`attempt.abandon` row, which only ever proved one manager declaration. The
review was right to separate those two counts.

**`test_the_fence_adopts_the_declarations_own_operation_and_reason`** — the
adopted values. The answered intent carries the operator's reason, decision
`abandoned`, an `authority.abandon-fence:` operation id, and a fence whose
assignment equals the declaration's own. Reversal (step 25): fencing with a
freshly derived operation id and reason instead of the adopted ones **fails the
case**.

The public start-wins case now also asserts **no declaration, no
`cancel-requested` axis and no resource teardown** after its refusal.

### The exact blocker, reported rather than papered over

**The start-wins case still moves the axis directly, and I could not replace
that with a public start transaction in this claim.** Driving
`attempts.request_runtime_start` from this fixture refuses *before* its commit:

    attempt 'attempt-1' was claimed against an input manifest and no input
    root was named; a runtime is not started over a directory this manager
    has not held against its own assignment

So a genuine public-start cut needs this fixture to **hold an input root against
the assignment**, which `interrupted_before_attach` does not do. That is a
fixture capability, not a product gap, and it is the one decision left: either
extend the pre-attach fixture to hold an input root, or accept the labelled
state fixture. **The case's comment now says plainly that it is a state fixture
and why**, so no later reader mistakes it for a public-order proof.

### Verification

- Step 24, both selected modules: `OK`, **791 checks**.
- Reversals, each restored: fence not recorded → 3 fail (06); no-start guard
  removed → 1 fail (09, 21); authority crossing replaced by a local document →
  1 fail (12); fence answer not held to what it must say → 2 fail (16);
  **fence using freshly derived values rather than the adopted record → 1 fail
  (25)**.
- **Step 23 was a no-op reversal** whose patch did not apply and which therefore
  "passed" — recorded as non-evidence, with step 25 the real one. This is the
  third time a silent no-op has produced a false pass in this Work; matching on
  exact line numbers rather than multi-line strings is what caught it.
- Ledger: **23 rows, 151.620432 s**. No run timed out, none was signalled, every
  run proved its process group gone.

### Mapped to existing coverage, not duplicated

The shared fixed-assignment guard already holds generation, Authority, Work and
participant **before either branch**, as the review notes; the wrong-participant
case exercises it and no duplicate was added for the attached fixture. The
retained non-effects case covers `output` and `worker_disposition`.

## Claim 174943 — both remaining boundaries closed

Only the test file changed; the three source files are unchanged since
candidate-174768.

### 1. The crash cut moved before any resource act

My previous cut used `_launch_after`, which runs **after**
`adapter.recover_credentials` **and** the orphan teardown — so it proved a crash
during cleanup, not one between the committed fence and the first resource act.
The review is right.

`recover_credentials` is the **first** thing the branch does after fencing, so
the case now raises a **non-`ContractRefusal`** from it — nothing absorbs it into
an account — and asserts **zero** teardown and **zero** launch settlement calls
beside it. The real-Authority assertions are retained: the fence operation record
exists, the participant's slot is already released **before any resource act
ran**, and the retry leaves that authority record unchanged.

The separate handled-`OrphanTeardown`-refusal case stays, accurately labelled as
the *later-cleanup* evidence it always was rather than as this cut.

### 2. The public start now really commits

The reviewer supplied what I was missing: the fixture **already composes**
`roots["inputs"]` at `dogfood_operator:1258` and hands it to the start at
`:1289`. The new `started_operands()` helper captures those exact operands where
the fixture patches `request_runtime_start`, so the case drives the **real**
public start with the real input root instead of seeding an axis. The adapter
then fails, leaving the axis off `not-started` with nothing attached.

**The commit is asserted, not assumed:** exactly one journalled `runtime.start`
operation exists before the pre-attach fence is attempted. The fence then
refuses, and the case still proves no declaration, no `cancel-requested` axis and
no resource teardown.

Reversal (step 27): driving that start with `inputs=None` instead of the real
root **fails the case** — so the operands are load-bearing rather than
decorative.

### Attribution corrected

The review is right that **step 25 failed the real-Authority record lookup
case, not the intent-shape case.** My previous note attributed it to the
adopted-values case. Corrected here; the disclosed no-op step 23 remains
recorded as non-evidence.

### Verification

- Step 26, both selected modules: `OK`, **791 checks**.
- Reversals, each restored: fence not recorded → 3 fail (06); no-start guard
  removed → 1 fail (09, 21); authority crossing replaced by a local document →
  1 fail (12); fence answer not held to what it must say → 2 fail (16); fence
  using freshly derived values → **1 fail (25), against the real-Authority
  record lookup**; public start without the real input root → 1 fail (27).
- Step 23 was a no-op whose patch never applied; retained as **non-evidence**.
- Ledger: **25 rows, 164.137709 s**. No run timed out, none was signalled, every
  run proved its process group gone.

Candidate `candidate-174943.json`; `test_dogfood_operator.py` is the only path
changed this claim, recorded with its prior candidate hash beside the current
one, and the accepted W32577 baseline still recorded for `__init__.py`.

## Claim 175002 — the pending start cut, corrected

The sole remaining correction. Only the test file changed; the three source
files are unchanged since candidate-174768.

**My cut was `uncertain`, not pending, and the review measured it.** A
`RuntimeError` is an `Exception`, so `request_runtime_start` **caught it and ran
ordinary failed-start settlement** before rethrowing — the public projection at
that hook showed `execution_runtime=uncertain`, `runtime_id=null`,
`start_failure_present=true`. So the case proved a refusal after an **uncertain
failed start**, and a guard that admitted `start-requested` while rejecting
`uncertain` would have passed it.

**Corrected to a `BaseException`**, which that handler does not catch: the
commit stands, no settlement runs, and what remains is exactly the state a
process killed between the commit and the attach leaves behind. Before the fence
is attempted the case now asserts all four facts the review named:

- `execution_runtime == "start-requested"`
- `runtime_id is None`
- exactly one journalled `runtime.start` operation
- `attempt_start_failure_of(...) is None` — with the message "ordinary
  failed-start settlement ran, so this is not the pending cut"

The fence refusal and its absent effects — no declaration, no `cancel-requested`
axis, no resource teardown — are preserved unchanged.

**Reversal (step 29):** changing `Interrupted(BaseException)` back to
`Exception` **fails the case**, because settlement then runs and the
`start_failure` assertion catches it. That is the distinction the review asked
for, made load-bearing rather than described.

### Verification

- Step 30, both selected modules: `OK`, **791 checks**.
- Reversals, each restored: fence not recorded → 3 fail (06); no-start guard
  removed → 1 fail (09, 21); authority crossing replaced by a local document →
  1 fail (12); fence answer not held to what it must say → 2 fail (16); fence
  using freshly derived values → 1 fail (25, against the real-Authority record
  lookup); public start without the real input root → 1 fail (27);
  **`Exception` instead of `BaseException` → 1 fail (30's predecessor, step
  29)**.
- Step 23 remains recorded as a no-op and **non-evidence**.
- Ledger: **28 rows, 185.042900 s**. No run timed out, none was signalled, every
  run proved its process group gone.

Candidate `candidate-175002.json`; `test_dogfood_operator.py` is the only path
changed, recorded with its prior candidate hash and the accepted W32577 baseline
still beside `__init__.py`.
