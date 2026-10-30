# W341357 — MEASURE FIRST, then fix the fixture storage. One bounded correction.

## Read three documents, then start the clock

**`COMPLETION.md`** — how this turn ends and when. Unchanged.

**`FIXTURE.md`** — what the last two gate runs measured, where the pressure
actually is, and the three claims of mine the reviewer corrected. **This is the
document that defines your work.**

**`RECOVERY.md`** — the exact retained candidate you start from.

Private committed base `bc925cf5c62d69426ed5862af4d41f4d2a967b0f`. Parent
W333486 owns ordinary status/report integration, the full joined twelve-module
gate, the installed-bundle proof and final acceptance.

**Where this stands.** The run before yours completed on its own at 789s —
**the lease is not your problem.** It moved the gate from `failures=9, errors=7`
to **`errors=16`, zero failures**: every path-comparison assertion and
line-layout refusal now passes. What is left is **one cause**:
`sqlite3.OperationalError: database or disk is full`, as **16 failing subtest
outcomes inside FOUR methods**.

**And nobody has measured why.** That is your first job, before you change a
line.

## The shape of this turn, in order. Do not reorder it.

### Step 1 — monotonic start, apply the candidate

Record a monotonic start as your **first act**. Then validate and apply the
sealed recovery input from the read-only mount at
`/input/source/work/records/2026/10/finding-v12-attempt-failure-diagnostics/findings/finding-durable-failure-capture/recovery-345388/`:

- `candidate.patch` — the **exact retained candidate**, applied with the
  repository's patch-applying tool. Its nine changed paths, in full:

  ```
  v12/python/src/baton_v12/worker_manager/attempts.py
  v12/python/src/baton_v12/worker_manager/documents.py
  v12/python/src/baton_v12/worker_manager/failure_cause.py
  v12/python/src/baton_v12/worker_manager/intake.py
  v12/python/tests/manager/disk_roots.py
  v12/python/tests/manager/input_roots.py
  v12/python/tests/manager/test_attempt_failure_cause.py
  v12/python/tests/manager/test_maintenance.py
  v12/python/tests/manager/test_output.py
  ```

  Confirm all nine after applying.
- `INDEX.json` — the derivation record, bound to the digests the reviewer
  published independently.

### Step 2 — REPRODUCE AND MEASURE. Before you change anything.

Run **only these four methods** first — the reproduction is small and fast on
purpose:

```
tests.manager.test_intake.TheQuiescenceGateIsDischargedFromTheCommittedCleanup.test_a_journalled_receipt_that_is_not_a_discharge_is_refused
tests.manager.test_intake.TheQuiescenceGateIsDischargedFromTheCommittedCleanup.test_a_receipt_about_something_else_is_refused_by_both_exits
tests.manager.test_maintenance.TheORDINARYEndingCompletesWithNoHelperOrItHolds.test_a_COMMITTED_cessation_for_ANOTHER_subject_moves_nothing
tests.manager.test_maintenance.TheORDINARYEndingCompletesWithNoHelperOrItHolds.test_an_UNREADABLE_listing_ANSWER_is_not_a_confirmed_absence
```

Then **measure, and write the numbers down**:

1. **The actual roots.** For every SQLite store and workspace these four
   methods create: the canonical path, and the **backing mount**. Do not infer
   it — read it.
2. **Capacity and headroom at that mount**: **available bytes AND available
   inodes**, sampled **before** the method, **during** the repeated subcases,
   and **after**. The composed profile's `tmp_bytes 67108864` /
   `shm_bytes 16777216` / `workspace_min_bytes 83886081` are **configured
   capacities, not observed free space** — the previous classification treated
   them as evidence and that was wrong.
3. **Per-subcase lifetime**: when each store is opened, and when its cleanup
   actually runs. The static lead is that it runs far too late.
4. **The high-water mark**: how much is live at the worst moment, and which
   method reaches it.
5. **The same-environment base/candidate comparison.** Run these four methods
   against the **unchanged pinned base** and against the candidate, in this
   same verifier environment, and report both sets of counts. **Absence of
   producer traceback frames is not a comparison** and must not be offered as
   one.

**If the measurement contradicts the static lead, say so and follow the
measurement.** The lead below is a lead.

### Step 3 — correct what the measurement demonstrated

The static lead, with exact citations — verify each before acting on it:

- `tests/manager/test_intake.py:2531-2535` calls `self.setUp()` **inside** a
  `subTest` loop. Each iteration registers another `addCleanup`, and
  `addCleanup` only runs when the **outer** test method ends, so every
  iteration's store stays live until then.
- `tests/manager/test_maintenance.py:2763`, `:2786` and `:2915` do the same
  shape with `self.addCleanup(case.doCleanups)`, deferring each sub-case's
  cleanup to the outer test.
- `tests/manager/test_output.py:101-104` — `OutputCase.setUp` creates
  `control.sqlite3` under `tempfile.TemporaryDirectory`, **not**
  `disk_backed_root`. So `BATON_V12_DISK_ROOT` does **not** relocate it. Do not
  assume otherwise.

**Per-subcase cleanup is a suggestion, not a prescription.** You choose the
mechanism. Necessary fixture and test edits have standing authority; record
every changed path with its ownership.

What the correction must leave standing:

1. **Every gate module, case and assertion** — including every negative and
   refusal case. A change that makes a refusal case pass by never reaching the
   refusal has broken it.
2. **The verifier's custody and security boundary** and the production path and
   object-identity refusals. Not widened, not relaxed, not made unreachable.
3. **No skips.** The sealed argv exits 1 if anything is skipped, by design.
4. **No hidden `TMPDIR` change** and **no resource-limit change.** If your
   measurement shows the limit is genuinely the binding constraint, **report it
   with the numbers** — that is a finding and an operand decision for the owner,
   not something to take inside this run.

**An equal test count does not prove assertion coverage.** A test that failed
during setup never proved its later assertions. If you cannot show an assertion
still runs, say so.

### Step 4 — the complete five-module gate, no skips

```
tests.manager.test_intake
tests.manager.test_attempts
tests.manager.test_maintenance
tests.manager.test_contracts_inventory
tests.manager.test_attempt_failure_cause
```

Report counts, failures, errors, skips and the actual duration against the
30-second `verification_command_seconds` ceiling. The last two runs measured
864 tests in 12.817s and 12.515s; say what yours measures.

**Iterate inside this one Job while the limits allow it** — reproduce, fix,
re-measure, then the full gate. That is the fast cycle the owner asked for.

### Step 5 — WRITE THE REPORT INTO THE CANDIDATE TREE

Create **`W341357-VERIFICATION.json`** at the repository root of your working
tree, so it travels as a changed path in the candidate's own `change.patch`.
**This is the only reporting channel that reaches a reviewer** — the proposal
carries no transcript, and the previous turn's numbers were lost for exactly
that reason.

It must carry, and all of it must be nonsecret:

- `base` and the candidate `head` you produced;
- the **exact commands** you ran, as argv;
- for the focused reproduction and the full gate: `tests`, `failures`,
  `errors`, `skips`, `duration_seconds`;
- the **base-versus-candidate** counts from step 2, side by side, with the
  environment stated as identical;
- the selected **roots**, their **mounts**, and **available bytes and inodes**
  before / during / after, plus the **high-water** observation;
- the **cleanup result**: what ran, when, and whether anything stayed live;
- what you changed, with each path and its ownership;
- what you did **not** establish.

**It is evidence only and must be excluded from any later product import.** Say
so inside the file. Carry **no** credential, environment value, private
transcript or provider text in it.

### Step 6 — stop at 600s, end by 720s

`COMPLETION.md` has the detail, unchanged. The last run returned at 789s and
**overran the 720s target by 69 seconds** — inside the lease, but the target was
missed. Measure first, fix small, and end on time. Ending the turn IS freezing:
there is no submit call and nothing to submit twice.

### Step 7 — report what you can observe, and nothing else

The controller report, the workload outcome and the shutdown progress file are
published **after** your turn ends. Name them structurally unavailable to the
worker rather than reporting them present or absent. Your half is
`W341357-VERIFICATION.json` plus the lease and cessation facts you **positively
observed from inside**, and your correlation keys: `run_id`, `work`, `claim`,
your pid, `outcome_path`, `status_path`.

**An honest `verification-failed` with the measurements written into the
candidate is a success for this turn.** A green gate bought by weakening
anything in step 3's list is a failure, and the review checks for exactly that.

## Boundaries

- **No edit to anything under `/input`.** The mount is read-only on purpose.
- **This turn's allocation** is the verification fixtures and the producer paths
  the candidate already touches, plus `W341357-VERIFICATION.json`. Declare
  anything else you genuinely need.
- **The producer obligations stay owed and out of scope** unless this turn's
  gate demonstrates a producer defect. `decisions/FINDING.md` is unchanged and
  a reviewer reads those bytes once the gate is assessable. Do not reopen the
  producer design and do not add producer features.
- **Do not touch the vehicle**: `tools/authoring_enforcement.py`,
  `tools/authoring_shutdown.py`, the supervisor baseline.
- **Preserve every earlier run and packet.** No rerun, no recovery of an old
  instance, no mutation, no credential or transcript read.
- No image build, no container, no engine call, no provider call inside this
  task; no host product edit outside the private checkout; no integration, no
  self-acceptance, no deployment, no mutating version-control operation beyond
  what the line profile itself performs.
- Independent review and the parent's joined acceptance remain required. **A
  retained candidate is not an accepted one** — this is the third in this
  campaign and the first was rejected on its merits.

## Honesty obligations

Three claims in the previous handoff were wrong and the review corrected them.
They are in `FIXTURE.md` so you do not repeat them: `disk_roots.py` was **not**
new; the 16 errors are **subtest** outcomes in four methods, not 16 methods and
not 864 concurrent stores; and an equal test count proves **nothing** about
assertion coverage.

Measure before you conclude. Do not label an environmental failure as formal
success, do not weaken an assertion or a refusal to obtain a pass, and do not
claim a comparison you did not run. Report what you measured, what you changed,
and what remains unknown.
