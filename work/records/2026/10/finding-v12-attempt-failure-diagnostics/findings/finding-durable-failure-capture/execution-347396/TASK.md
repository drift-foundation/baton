# W341357 — two producer defects. Reproduce each one first, then correct it.

## Read three documents, then start the clock

**`COMPLETION.md`** — how this turn ends and when. Unchanged.

**`FIXTURE.md`** — despite its name, **the two producer defects**, with the
citations read from the candidate's own bytes, plus the fixture work that must
survive. **This is the document that defines your work.**

**`RECOVERY.md`** — the exact retained candidate you start from.

Private committed base `bc925cf5c62d69426ed5862af4d41f4d2a967b0f`. Parent
W333486 owns ordinary status/report integration, the full joined twelve-module
gate, the installed-bundle proof and final acceptance.

**Where this stands.** The run before yours completed on its own at 733s and
**its sealed gate passed** — 864 tests, 12.631s, OK, exit 0, no skips,
independently confirmed. The lease, the ceiling and the storage pressure are no
longer your problems. **Two producer defects are**, and product acceptance is
withheld until they are corrected with evidence.

## The shape of this turn, in order. Do not reorder it.

### Step 1 — monotonic start, apply the candidate

Record a monotonic start as your **first act**. Then validate and apply the
sealed recovery input from the read-only mount at
`/input/source/work/records/2026/10/finding-v12-attempt-failure-diagnostics/findings/finding-durable-failure-capture/recovery-345822/`:

- `candidate.patch` — the **exact retained candidate**, applied with the
  repository's patch-applying tool. Its eleven changed paths, in full:

  ```
  W341357-VERIFICATION.json
  v12/python/src/baton_v12/worker_manager/attempts.py
  v12/python/src/baton_v12/worker_manager/documents.py
  v12/python/src/baton_v12/worker_manager/failure_cause.py
  v12/python/src/baton_v12/worker_manager/intake.py
  v12/python/tests/manager/disk_roots.py
  v12/python/tests/manager/input_roots.py
  v12/python/tests/manager/test_attempt_failure_cause.py
  v12/python/tests/manager/test_intake.py
  v12/python/tests/manager/test_maintenance.py
  v12/python/tests/manager/test_output.py
  ```

  `v12/python/tests/manager/test_attempt_failure_cause.py` does not exist at
  the base; the patch creates it. Confirm all eleven after applying.
- `INDEX.json` — the derivation record, bound to the digests the reviewer
  published independently.

**Then confirm the gate still passes before you change anything.** You are
starting from a green tree and you need to know it was green in your hands.

### Step 2 — REPRODUCE BOTH DEFECTS. Deterministically, at the production boundary.

Both findings in `FIXTURE.md` are **static traces**. Neither has been executed.
A failing case first is what makes the correction a fix rather than a claim.

**R1 — fresh observation versus exact replay.** Write a deterministic case at
the real production boundary that drives, under one held revoked generation with
no generation change and no token release:

1. a settlement observation of `quiescent` → revision 0;
2. a settlement observation of `running`/uncertain → revision 1;
3. **a third, fresh observation of `quiescent` again.**

Show what happens now: the recorder matches revision 0 on the facts, writes
nothing, and the reader keeps answering **revision 1, uncertain**. Then show the
reverse order, where a **stale positive** wins instead. Then add the case the
existing test does not cover: **a delayed exact redelivery of the old A**, which
must *not* supersede B.

**R2 — recording failure on the acting paths.** Inject an **outcome-write
failure after the durable intent has committed**, at the real **reclaim**,
**settlement** and **cancellation** boundaries — including the cancellation
**exception** branches. Show that today the caller returns the ordinary
held/refusal result and nothing tells an operator the known failure was not
captured. Include the malformed-fact branch, whose phrase `recording_degraded()`
does not recognise.

**Report the reproductions before the fixes.** If a trace does not reproduce,
say so plainly and do not fix what you cannot demonstrate — that happened last
run with the disk-full outcome and reporting it was the right answer.

### Step 3 — correct R1: separate a fresh observation from a replay

The mechanism, the files and the tests are **yours**. The cited locations are
evidence, not an exclusive edit list.

What the correction must achieve:

1. **a fresh A→B→A retains the third observation** — the newest accepted
   observation is what the current read names;
2. **an exact redelivery of the old A does not supersede B** — replay stays
   idempotent and writes nothing;
3. **history is preserved and bounded** — the supersession chain still shows
   that an uncertain observation was later replaced, and which is current;
4. the ownership and identity re-proof already applied to every revision stays
   applied.

**Do not** change `test_a_REPLAY_of_a_SUPERSEDED_revision_writes_NOTHING_MORE`
into a tip-only dedup test and lose old-replay correctness. Its expectation must
be evaluated against the **actual replay semantics**, not preserved merely to
keep the gate green — and if it needs to change, say exactly why and what now
covers what it covered.

### Step 4 — correct R2: make recording degradation visible

**Use the channel that already exists** —
`failure_cause.recording_degraded(reported)` →
`answer["diagnostic_degradation"] = reported`, as `intake.py:5710-5711`,
`intake.py:6058-6059` and `attempts.py:3647` already do — or another bounded,
compatible mechanism if you can justify it.

On **every** affected result and exception path:

1. the degradation is **visible to the caller**, bounded and secret-safe;
2. **the original engine refusal is not masked** — its message and classification
   survive unchanged;
3. **no cessation is inferred** from a recording outcome;
4. the uncertain **holds**, the **fencing** and the **cleanup** semantics are
   exactly as they were;
5. the **classification is consistent** — the malformed-fact phrase is
   recognised by the same classifier as the rest.

### Step 5 — the complete five-module gate, no skips

```
tests.manager.test_intake
tests.manager.test_attempts
tests.manager.test_maintenance
tests.manager.test_contracts_inventory
tests.manager.test_attempt_failure_cause
```

It passed before you started: 864 tests, 12.631s, OK, exit 0. Report counts,
failures, errors, skips and the actual duration against the 30-second ceiling,
and say whether your changes moved any of them. The sealed argv exits 1 on any
skip.

**Preserve every fixture correction the green gate rests on** — they are listed
in `FIXTURE.md` and they are not yours to undo.

**Iterate inside this one Job while the limits allow it:** reproduce, fix,
re-measure, then the full gate.

### Step 6 — UPDATE `W341357-VERIFICATION.json`

It already exists in the tree you applied. **Extend it; do not replace its
history.** Add, for this turn:

- the **reproductions** — for R1 the three observations in both orders and the
  delayed redelivery, with what the reader answered before and after; for R2
  each boundary with the injection point, the original behaviour and the
  degradation the caller saw;
- the exact **commands** as argv, and counts/failures/errors/skips/duration for
  every run;
- **what changed**, with each path and its ownership;
- **what you did not establish.**

It stays **evidence only** and **excluded from any later product import**, and
carries no credential, environment value, private transcript or provider text.

**Correlation keys:** the previous turn reported `run_id`, `outcome_path` and
`status_path` as absent-by-structure because nothing in the worker carried
them. That was right. Report only `work` and whatever your environment actually
provides, and **name the rest absent rather than guessing** — that instruction
was my error and this is the correction.

### Step 7 — stop at 600s, end by 720s

`COMPLETION.md` has the detail, unchanged. The last two runs returned at 789s
and 733s — both over the 720s target, by 69s and 13s. **Land inside it this
time:** reproduce small, fix narrowly, and end on time. Ending the turn IS
freezing.

### Step 8 — report what you can observe, and nothing else

The controller report, the workload outcome and the shutdown progress file are
published **after** your turn ends. Name them structurally unavailable to the
worker rather than reporting them present or absent.

**An honest `verification-failed` with both defects reproduced is worth more
than a green gate with neither.** A green gate bought by weakening an
assertion, a hold, a refusal or the replay semantics is a failure, and the
review checks for exactly that.

## Boundaries

- **No edit to anything under `/input`.** The mount is read-only on purpose.
- **This turn's allocation** is the producer outcome/read contract and its call
  sites — `failure_cause.py`, `intake.py`, `attempts.py`, `documents.py` — plus
  the focused producer tests and `W341357-VERIFICATION.json`. Declare anything
  else you genuinely need.
- **No producer redesign beyond this contract.** Two defects, not a rewrite.
- **Do not weaken the verifier or the production refusals**, and do not change
  `TMPDIR`, a resource limit or a capacity operand. No capacity change is
  selected and none is needed.
- **Do not carry the parent's downstream work.** The `job_manager` status seam,
  `tools/attempt_diagnostics.py`, `stack_command.py` and their tests are the
  parent's.
- **Do not touch the vehicle**: `tools/authoring_enforcement.py`,
  `tools/authoring_shutdown.py`, the supervisor baseline.
- **`attempts.py` carries a declared integration overlap** with W339626's
  candidate345109. Change it if the contract needs it, and **name every change
  there explicitly** in your report — it is reconciled serially under
  independent review, never by overwrite.
- **Preserve every earlier run and packet.** No rerun, no recovery of an old
  instance, no mutation, no credential or transcript read.
- No image build, no container, no engine call, no provider call inside this
  task; no host product edit outside the private checkout; no integration, no
  self-acceptance, no deployment, no mutating version-control operation beyond
  what the line profile itself performs.

## Honesty obligations

A passing gate is **not** acceptance — the review said so while confirming the
gate. Three of this author's earlier claims were corrected by review for being
stronger than their evidence, and the pattern was always the same: a plausible
story offered without the measurement that would settle it.

So: reproduce before you fix, report what did not reproduce, do not infer a
cause you did not observe, and do not keep a test green whose expectation no
longer matches the semantics. Report what you measured, what you changed, and
what remains unknown.
