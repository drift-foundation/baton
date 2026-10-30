# W341357 — MAKE THE GATE USABLE. One bounded correction, from a real candidate.

## Read three documents, then start the clock

**`COMPLETION.md`** — how this turn ends and when. Unchanged, and the shortest
document here.

**`FIXTURE.md`** — the gate ran, what it measured, and exactly where the 16
failures live, with file and line citations read from the tree. **This is the
document that defines your work.**

**`RECOVERY.md`** — what you are given: the exact retained candidate from the
run before yours.

Private committed base `bc925cf5c62d69426ed5862af4d41f4d2a967b0f`. Parent
W333486 owns ordinary status/report integration, the full joined twelve-module
gate, the installed-bundle proof and final acceptance, and is serially blocked
on this child.

**What changed since the last turn, and it is good news.** The run before yours
**completed on its own at 461 seconds** and measured the gate for the first
time: **864 tests in 12.817s, exit 1, 9 failures and 7 errors, all 16 in
`tests.manager.test_maintenance`.** The 30-second ceiling fits. The lease is not
your problem this time. **Your problem is that the gate cannot currently pass in
the environment it runs in, and you are the one who finds out whether that is
true and fixes it in the fixture.**

## The shape of this turn, in order. Do not reorder it.

### Step 1 — monotonic start, apply the candidate, then CONFIRM THE DIAGNOSIS

Record a monotonic start as your **first act**. Then validate and apply the
sealed recovery input from the read-only mount at
`/input/source/work/records/2026/10/finding-v12-attempt-failure-diagnostics/findings/finding-durable-failure-capture/recovery-345039/`:

- `candidate.patch` — the **exact retained candidate**, applied with the
  repository's patch-applying tool. Its five changed paths, in full:

  ```
  v12/python/src/baton_v12/worker_manager/attempts.py
  v12/python/src/baton_v12/worker_manager/documents.py
  v12/python/src/baton_v12/worker_manager/failure_cause.py
  v12/python/src/baton_v12/worker_manager/intake.py
  v12/python/tests/manager/test_attempt_failure_cause.py
  ```

  The last two do not exist at the base; the patch creates them. Confirm all
  five after applying.
- `INDEX.json` — the derivation record, bound to the digests the reviewer
  published independently.

Then **confirm the two diagnoses in `FIXTURE.md` dynamically**, because neither
has been:

1. **Compare unchanged base against the retained candidate for
   `tests.manager.test_maintenance`, under the same pinned-root conditions.**
   This is the measurement nobody has: it decides whether those 16 cases are
   pre-existing in this environment or something the candidate caused. Report
   both counts. If base also fails 16, say so plainly — it is the single most
   useful fact you can produce this turn.
2. **Confirm that the subprocess in `MaintenanceCase.executed` really cannot
   resolve a parent-descriptor path**, rather than inferring it. Make the child's
   `returncode` and `stderr` visible first; an empty-output `IndexError` is a
   hidden failure, not a diagnosis.

### Step 2 — correct the fixture so the gate can run

You choose the files and the mechanism. Canonicalising the fixture-owned
derived paths is the reviewer's **suggestion**, not a prescription, and
`FIXTURE.md` carries my argument for why it is not a weakening — **confirm that
argument or reject it, do not assume it.**

What the correction must leave standing, all five:

1. **Every gate module, case and assertion.** Nothing dropped, skipped,
   narrowed, relaxed or deleted. All 16 defect cases must still exist and still
   mean what they mean. In particular
   `test_a_REPLACED_LINE_object_is_refused_by_the_COMPOSED_boundary` and
   `test_a_REPLACED_inputs_root_under_the_LINE_layout_still_refuses` must still
   **reach and prove their refusal** — a change that makes them pass by never
   reaching it has broken them.
2. **The verifier's pinned-descriptor boundary**
   (`claude_agent._pinned_environment`). Not widened, not disabled, not worked
   around.
3. **The production path and custody refusals**, including
   `workspaces._composed_line_roots`' `realpath(place) == place` and the
   device/inode object-identity check. These are product security checks. If
   your correction makes either unreachable, it is wrong.
4. **Both path shapes exercised**: the ordinary case and the pinned-root case.
   A fixture that only works under one of them is half a correction.
5. **Child-process access**: whatever path the fixture hands to a subprocess
   must be resolvable by that child, and a child failure must surface as a
   child failure.

Record **every changed fixture or test path, with its ownership**, in your
report. Standing test authority covers the necessary corrections; that is why
the record is required instead of another approval gate.

### Step 3 — run the COMPLETE five-module gate, with no skips

```
tests.manager.test_intake
tests.manager.test_attempts
tests.manager.test_maintenance
tests.manager.test_contracts_inventory
tests.manager.test_attempt_failure_cause
```

The sealed argv admits **no skip** — it exits 1 if anything is skipped, by
design. Report, in your own words and pasting no raw output:

- **the counts and the actual timing** against the 30-second
  `verification_command_seconds` ceiling. The previous run measured 864 tests in
  12.817s; say what yours measures and whether the correction moved it;
- **what still fails and how**, by module, case name and assertion, enough for a
  reviewer to act, carrying no credential, environment value, private
  transcript or provider text;
- **whether anything failed to import, collect or was skipped**, each a
  different fact from a failing assertion.

### Step 4 — the producer obligations are still owed, and are NOT this step's work

`decisions/FINDING.md` is unchanged: durable pre-effect intent on all three
boundaries, exact replay versus changed-signature collision, recording failure
and crash, the typed outcome and its replay history, both release paths, the
four-answer read contract, bounded secret-safe fields, honest old-record
unknown. The candidate's 63 cases reported no failure last run — **useful
evidence, not independent signoff.**

Fix a producer defect **only if this turn's gate demonstrates one.** Do not
reopen the producer design, do not refactor it, and do not add producer features.
A reviewer reads those bytes after the gate is usable.

### Step 5 — stop at 600s, end by 720s

`COMPLETION.md` has the detail and nothing about it has changed. The previous
run returned at 461s with 439s of lease margin, so this is comfortable rather
than tight — **and that is not a licence to use the slack.** At **600s stop
optional edits** and summarise; **by 720s the turn ends.** Ending the turn IS
freezing: there is no submit call and nothing to submit twice.

### Step 6 — report what you can observe, and nothing else

The controller report, the workload outcome and the shutdown progress file are
published **after** your turn ends. Name them structurally unavailable to the
worker rather than reporting them present or absent. Your half:

- the **base-versus-candidate comparison** from step 1, with both counts;
- the subprocess diagnosis, confirmed or refuted;
- every changed fixture/test path with its ownership;
- the complete gate measurement from step 3, and what still fails;
- which producer obligations are demonstrated, which are not, which you did not
  reach;
- the lease and cessation facts you **positively observed from inside**;
- your correlation keys: `run_id`, `work`, `claim`, your pid, `outcome_path`,
  `status_path`.

**An honest `verification-failed` with a complete measured gate and a confirmed
base comparison is a success for this turn.** A green gate bought by weakening
anything in step 2's list is a failure, and the review checks for exactly that.

## Boundaries

- **No edit to anything under `/input`.** The mount is read-only on purpose.
- **This turn's allocation** is the verification fixture and the producer paths
  the candidate already touches. Declare anything else you genuinely need rather
  than working around it.
- **Do not weaken the verifier or the production refusals.** If the only way you
  can see to make the gate pass is to relax one of them, **stop and report
  that** — it is a real finding and it is the honest answer.
- **Do not carry the parent's downstream work.** The `job_manager` status seam,
  `tools/attempt_diagnostics.py`, `stack_command.py` and their tests are the
  parent's. It is blocked on you, which is exactly why you must not take its
  work.
- **Do not touch the vehicle**: `tools/authoring_enforcement.py`,
  `tools/authoring_shutdown.py` and the supervisor baseline.
- **Preserve every earlier run and packet.** No rerun, no recovery of an old
  instance, no mutation, no credential or transcript read.
- No image build, no container, no engine call, no provider call inside this
  task; no host product edit outside the private checkout; no integration, no
  self-acceptance, no deployment, no mutating version-control operation beyond
  what the line profile itself performs.
- Independent review and the parent's joined acceptance remain required. **A
  retained candidate is not an accepted one** — this is the second retained
  candidate in this campaign and the first was rejected on its merits.

## Honesty obligations

The candidate you are given is **retained and unaccepted**. Its gate ran and
exited 1. Its 63 producer cases reporting no failure is evidence, not signoff.
Line counts and case names are not evidence that code works — a previous handoff
of mine made that claim and the review rejected it.

The absence of changed paths from a traceback does **not** prove the candidate
is innocent, and there is **no base measurement of this argv in any run**. That
is why step 1 asks for the comparison instead of letting you assume the answer.

Do not label an environmental failure as formal success. Do not weaken an
assertion, a production refusal or the verifier to obtain a pass. Report which
obligations are demonstrated, what you measured, and cumulative spending.
