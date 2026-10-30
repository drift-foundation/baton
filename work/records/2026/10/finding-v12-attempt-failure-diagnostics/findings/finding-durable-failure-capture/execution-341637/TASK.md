# W341357 durable typed failure capture and replay — VERIFICATION FIRST

## Read two documents, then start the clock

**`COMPLETION.md`** — how this turn ends and when. Shortest document here and
the one that decides whether this run produces anything. Two consecutive runs
before yours were killed by the lease with **nothing frozen**.

**`RECOVERY.md`** — what you are given and what has never been executed.

Private committed base `bc925cf5c62d69426ed5862af4d41f4d2a967b0f`. Parent
W333486 owns ordinary status/report integration, the full joined twelve-module
gate, the installed-bundle proof and final acceptance, and is serially blocked
on this child. You own the producer contract and its focused verification.

## The shape of this turn, in order. Do not reorder it.

### Step 1 — record a monotonic start, apply the recovery

Your **first act** is to record a monotonic start so you can check elapsed time
against it. Then validate and apply the sealed recovery inputs from the
read-only mount at
`/input/source/work/records/2026/10/finding-v12-attempt-failure-diagnostics/findings/finding-durable-failure-capture/recovery-341360/`:

- `producer.diff` — apply with the repository's patch-applying tool; it touches
  `worker_manager` `documents.py`, `intake.py` and `attempts.py` only;
- `v12/python/src/baton_v12/worker_manager/failure_cause.py` — copy verbatim;
- `v12/python/tests/manager/test_attempt_failure_cause.py` — copy verbatim.

Every one is digest-pinned and cross-checked by `prepare.py` and
`verify-inputs.py`, including against the digests the reviewer independently
published. `recovery-341360/INDEX.json` is the derivation record.

### Step 2 — RUN THE FOCUSED GATE. Before any design. Before touching a test.

```
tests.manager.test_intake
tests.manager.test_attempts
tests.manager.test_maintenance
tests.manager.test_contracts_inventory
tests.manager.test_attempt_failure_cause
```

This is the sealed argv's membership and it is also your first real
measurement. **Nothing in the recovered bytes has ever been executed** — not
`_authorizes`, not the read API, not one of the 62 cases in that last module.

Report, in your own words and pasting no raw output:

- **per-module elapsed seconds and the total against the 30-second
  `verification_command_seconds` ceiling.** This answers a question this
  campaign has carried unproved since the parent's second revision: **does the
  gate fit?** If it does not, that is a finding with numbers, not a failure;
- **what failed and how** — by module, case name and assertion, enough for a
  reviewer to act, carrying no credential, environment value, private
  transcript or provider text;
- **whether anything failed to import or collect**, which is a different fact
  from a failing assertion.

**Do not design, refactor or add cases before this measurement exists.** If the
gate passes outright, say so with the numbers and move to step 4.

### Step 3 — fix ONLY what the gate demonstrated

Not what you suspect, not what reads badly, not what could be tidier. **A
demonstrated acceptance failure.** For each one: the case, the behaviour, the
change, and the re-measured result.

The producer acceptance in `decisions/FINDING.md` is unchanged and nothing here
weakens it — durable pre-effect intent on all three boundaries, exact replay
versus changed-signature collision, recording failure and crash, the typed
outcome and its replay history, both release paths, the four-answer read
contract, bounded secret-safe fields, honest old-record unknown. If a case that
*should* exist is missing, you may add it; that is coverage, not redesign.

**What you may not do:** weaken a test, delete a case, relax an assertion,
narrow the gate, or introduce a broad new feature to make something pass. The
review checks for exactly that.

### Step 4 — stop at 600s, end by 720s

`COMPLETION.md` has the detail. At **600s elapsed, stop optional edits** and
summarise the exact state. **By 720s the provider turn ends** — you stop, it
returns, and the adapter then measures the delta, runs the task's verification
(up to 30s), revalidates, picks a disposition, commits the line whatever that
disposition is, and publishes. **None of that happens if the lease kills you
first**, and that is precisely how the last two runs produced nothing.

**Ending the turn IS freezing. There is no submit call and nothing to submit
twice.**

### Step 5 — report what you can observe, and nothing else

The controller report, the workload outcome and the shutdown progress file are
published **after** your turn ends. You cannot see them; name them structurally
unavailable to the worker rather than reporting them present or absent. Your
half:

- the gate measurement from step 2, and the re-measurement after any fix;
- which acceptance obligations are demonstrated, which are not, and which you
  did not reach;
- the retained changes with exact paths;
- the lease and cessation facts you **positively observed from inside**;
- your correlation keys: `run_id`, `work`, `claim`, your pid, `outcome_path`,
  `status_path`.

**An honest `verification-failed` with a measured gate is a success for this
turn.** It is strictly more than either of the last two runs produced.

## Boundaries

- **No edit to anything under `/input`.** The mount is read-only on purpose.
- **Producer paths are your allocation**: `worker_manager/failure_cause.py`,
  `documents.py`, `intake.py`, `attempts.py` and focused producer tests.
  Ownership, not an exclusive edit restriction — declare anything else you
  genuinely need rather than working around it.
- **Do not carry the parent's downstream work.** The `job_manager` status seam,
  `tools/attempt_diagnostics.py`, `stack_command.py` and their tests are the
  parent's. It is blocked on you, so there is no concurrent edit owner — which
  is exactly why you must not take its work.
- **Do not touch the vehicle**: `tools/authoring_enforcement.py`,
  `tools/authoring_shutdown.py` and the supervisor baseline.
- **Preserve all three completed runs and every packet.** No rerun, no recovery
  of an old instance, no mutation, no credential or transcript read.
- No image build, no container, no engine call, no provider call inside this
  task; no host product edit outside the private checkout; no integration, no
  self-acceptance, no deployment, no mutating version-control operation beyond
  what the line profile itself performs.
- Independent review and the parent's joined acceptance remain required. **A
  retained candidate is not an accepted one** — the parent's `433692c5` was
  retained and rejected on its merits.

## Honesty obligations

The recovered bytes are **unverified input, not a certified design**. Line
counts and test-case names are not evidence that code works — my own previous
handoff made that claim and the review rejected it. Find out what is true.

Report which obligations are demonstrated, which tests ran and what they
measured, and cumulative verification spending. Do not label an environmental
failure as formal success. Do not weaken an assertion to obtain a pass. And do
not write until expiry: **a measured failure returned at 720s beats an unmeasured
improvement killed at 905s**, twice over, because that is the actual record.
