# W361912 — implementer progress

## claim362657 — connected manager-owned template Job creation

Answers `FINDING.md`, `PLAN.md` and `review-2026-10-26T18-44-13Z.md` under
handoff362654, consuming the independently accepted W361910 resolver.

### Base revalidated at claim start

Accepted base commit `19f02ce1295b4517a85f0822d48754efc982f388`
(`feat(v12): resolve versioned Job templates`), confirmed by
`git rev-parse HEAD`. All three accepted resolver members re-hashed against
`evidence/preparation-362639/ACCEPTED-BASE.json` and against the W361910
acceptance review's table, and all three agree:

| path | SHA256 |
| --- | --- |
| `v12/python/src/baton_v12/job_manager/__init__.py` | `bfebb949e201c9de01075e98e3872fc2f761d460bd57308192c10a0795cf580c` |
| `v12/python/src/baton_v12/job_manager/templates.py` | `64f9f3412c673d7bac7ace6190e3f8ddebba7056f90a279f07fc70efc0975e16` |
| `v12/python/tests/job_manager/test_templates.py` | `a45389dedc4008c937bca139effa6c08cba852c5c8d1ebc6e8cbfa97d6caab13` |

Scoped status for `v12/python` is empty; `v12/DESIGN.md` is the pre-existing
dirty approved-contract transcription and is preserved untouched.

### Read position

`detail work=W361912`, `work-events work=W361912` complete through seq362657
(`next_after` null, five prior events read including both `add_dependency`
rationales) and born thread `T361912` complete — one message at seq361912, no
newer discussion. Bound dossier `FINDING.md` including its
2026-10-26T18-44-13Z section, `PLAN.md`, `PLAN-HISTORY-362639.md`,
`review-2026-10-26T18-44-13Z.md` and `evidence/preparation-362639/` read in
full. The prerequisite's acceptance review
`../finding-v12-versioned-job-template/review-2026-10-26T18-18-45Z.md` read in
full, including its "Required downstream boundary" section, which this Work
owns.

### Source revalidated against the current tree

`job_manager/templates.py` (the accepted seams `resolve`, `owned_resolution`,
`submission_for_admission`, `resolution_digest`, `template_document`),
`submission.py`, `fresh_attempt.py`, `schema.py`, `documents.py`,
`execution_limits.py`, `tools/job_manager.py`, `tools/fresh_attempt_ports.py`,
`tools/bootstrap.py` and `tools/stage_execution.py`
(`servable_workers`/`_disagreements`/`_job_workers`).

### The gap, measured

`tools/job_manager.py` has `submit` (a normalized document an operator
authors), `fresh-attempt` (repeats a prior Job) and `status`/`serve`. Nothing
creates an ordinary Job from a task. `fresh_attempt_ports.DeploymentBinding`
binds by `like=<existing job_id>`, so it cannot bind a first Job of its kind.

And the digests an operator would have to fabricate are not theirs to know.
`stage_execution._disagreements` is the rule that decides which configured
worker may serve a stage, and it compares, per stage: the serving worker's
`launch_role` against the stage kind, its manifest's `work_ref.work_id`
against the binding's `job_work_id`, its `profile_name` and `profile_digest`
against the stage's, `job_input_identity(manifest)` against the Job's
`input_digest`, and its `policy_digest` against the Job's. Every one of those
is a fact the DEPLOYMENT holds about its installed workers. An operator typing
them is configuring the pool from a Job, and typing one wrong produces a
configuration that validates and whose stages no worker can ever be selected
for — the exact failure the pilot recorded.

### What is delivered this round

**This claim delivers the operation, its ports and its thin CLI with focused
verification, and it does NOT complete the FINDING's connected rehearsal or
its OBS-0 measurement.** Those are stated exactly in "Remaining scope" below
and are returned rather than claimed.

Candidate `candidate-362657/`, manifest
`e310e70caff0a714f6732a032165be14519c0d93fa38f3e4d539c0d62077789a`, eleven
members over base `19f02ce1295b4517a85f0822d48754efc982f388`.

| path | base | candidate |
| --- | --- | --- |
| `src/baton_v12/job_manager/creation.py` | new | `bf7928c195e2c643744e644e1ab1e9d810e57f5f0e5c6aadf803a3559692fe01` |
| `tools/creation_ports.py` | new | `63f2b3889afaecfd002324d494c992ad1c835cc9087d85351d0f059fc107c512` |
| `tests/job_manager/test_creation.py` | new | `91049a25082c99eef80f65e2358c38008f4913139feb6669b6ae0d900b15ec22` |
| `tests/tools/test_creation_ports.py` | new | `c0080ead0a824bee30a684f65c89f02012544a3eed5e00710f4392c91197432e` |
| `src/baton_v12/job_manager/schema.py` | `bba74451…13d5` | `8fe0ecfb767de7d355ed82c89ce6060f3efa3bf372f05fadde07d867af0f399f` |
| `src/baton_v12/job_manager/documents.py` | `2138a81d…468` | `b7ee4bb9def4eb26e14ee3a38bbab55000b6e8f897c67a632ba2711640f27350` |
| `src/baton_v12/job_manager/__init__.py` | `bfebb949…580c` | `50722a7496e2719afa9c67c6d331e18d28543f78b8c930beba91ff80aece907c` |
| `tools/job_manager.py` | `1634c9a4…7cd1` | `9f9008fd68a3f00ed41516c0127655cd24a5518df15294f22282c0f0dc66018f` |
| `tests/job_manager/test_store.py` | `ddceb613…b9c8` | `73c27abf44dbce537da99067f7b8245c51c8ab22d21c209f2de0d777ef131ceb` |
| `tests/job_manager/test_scheduling.py` | `6041b43d…a3b0` | `47f0043e3185394a9b07e00ff827bf1c2064dfeab7714f41328aeb5badf2d842` |
| `tests/job_manager/test_execution_limits.py` | `4bece59f…c2d7` | `03eb0d74d027e29c1d2901649139c21e562596376bf7b5e1d6a1134de89f0e43` |

**The three existing test files change one thing each and it is the same
thing.** `test_store.write_schema_2`, `test_scheduling`'s two schema-3
fixtures and `test_execution_limits`' schema-4 fixture each build a store with
today's build and subtract what came after the version they impersonate; each
one's own comments instruct that every relation added later must be subtracted
too, naming W156162, W197661 and W358969 in turn. This adds `template_jobs` to
those lists with the same note. No assertion, expectation or behaviour in any
existing test is changed.

### The command, and what it does not offer

    baton-v12-stack manager --store … --incarnation … --authority-uuid … \
        create --instance … --control … --authority … \
                --task w361912-a --statement "…" \
                --acceptance "…" --work-scope v12/python/src/… \
                [--test-scope v12/python/tests/…] [--template …] \
                [--provider-turn-seconds N] [--verification-command-seconds N]

There is no `--input-digest`, no `--policy-digest`, no `--profile`, no
`--profile-digest`, no `--work-id`, no `--document`, no `--manifest` and no
`--packet`. That absence is the deliverable: `stage_execution._disagreements`
is the rule that decides which configured worker may serve a stage, and five
of the six operands it compares are facts the DEPLOYMENT holds about the
workers it installed. A case asserts each of those flags is rejected by the
parser, so the absence cannot be undone without a test failing.

### The shape

**`job_manager/creation.py` — the manager-owned operation.** Modelled on
`fresh_attempt.admit` and reusing its cut order for its reasons:

  1. own the request, then derive and resolve -- no store is touched
  2. hold the instance guard, re-derive and re-resolve inside it, and refuse
     if the resolution is no longer the one this instance derives
  3. CUT A `_reserved` -- the identity, the submission name AND the full
     resolution digest, inside this store's write lock
  4. `_acquired` -- the holder compare-and-swap, so one runner publishes this
     identity's external effects
  5. CUT B -- the Work authorization, then the deployment binding, which is
     inert while no Job exists and so is the safe half to publish first
  6. `_servable` -- the selector asked for EVERY stage, after the binding
  7. `templates.submission_for_admission` -- the accepted consumption
     contract, inside the operation, at `execution_limits.CURRENT_GENERATION`
  8. CUT C -- `submission.submit`
  9. `_completed` -- the intent becomes `created` and the answer is journalled

**`tools/creation_ports.py` — two objects, neither holding a rule.**
`DeploymentDerivation` reads this instance's configuration THROUGH
`stage_execution.held_configuration` and answers the four facts: the Work from
the workers' own manifest `work_ref`, the Job input through
`job_input_identity` (the same projection `_disagreements` compares with, so a
heterogeneous pool stays derivable), the policy digest, and each lane's
profile. `NewJobBinding` is `fresh_attempt_ports.DeploymentBinding` plus
`create_binding` -- the verb that class could not have, because `bind` derives
from a `like` Job and an ordinary creation has no predecessor. The Work
authorization, the instance guard and the host exclusion are
`fresh_attempt_ports`' own classes, reused unchanged.

### The full resolution digest is the identity of the selected intent

W361910's acceptance review set this obligation and it is the part of the
design most likely to have been got wrong: "Task statement, acceptance and
work scope can differ without changing the legacy submission; a submission
signature alone is therefore insufficient to identify that complete selected
intent."

So `template_jobs` records `resolution_digest`, the `create` operation's
journal signature carries it, and `ChangedIntent` drives the hard half
directly: a changed statement, a changed acceptance contract and a changed
work scope each refuse as two creations — and a control case in the same class
shows `submission.submit` replaying the byte-identical document, which is
correct for `submit` and is exactly why the digest is recorded.

The row also stores the resolution DOCUMENT. The digest says which intent;
the document says what it was. `creation.resolution_of` reads it back through
`templates.owned_resolution` and refuses a row whose bytes do not digest to
the identity they are filed under.

### Two things measured rather than assumed

**The answer cannot nest the resolution.** `contracts.canonical` bounds a
document at depth 8 and a resolution carrying a normalized submission is
already at that bound, so an answer with `resolution` as a member is one
`store.transact` refuses to journal. I found this by writing it the obvious
way and watching the refusal. The answer carries the resolution's members
flattened; the document lives in the row.

**The deployment owner already refuses the incoherence I wrote a port check
for.** I expected to drive `DeploymentDerivation._agreed` with a document
whose review worker disagreed about the policy or the Work.
`held_configuration` refuses such a document first — "the bootstrap input
manifest names another policy", "a manifest that does not identify itself is
not one" — so a port reading its answer never sees one.
`TheOwnerRefusesIncoherenceBeforeThePortSeesIt` records that, and
`TheDerivationsOwnRefusals` drives the port's rule where it really is
reachable: two workers of one role carrying two profiles, which
`held_configuration` does not decide.

### Evidence

`evidence/claim-362657/`, with `HOW-THESE-WERE-RUN.txt` giving the roots, the
commands and an explicit list of what is not proved.

- **`tests.job_manager.test_creation`**: **62 cases, OK** — the operation over
  a real Job store, plus the CLI verb's wiring and its forbidden operands.
- **`tests.tools.test_creation_ports`**: **14 cases, OK** — the derivation
  against a real owned deployment document, and the round trip through
  `stage_execution.servable_workers`. Two control cases make the pass
  meaningful: one wrong derived input digest makes EVERY stage unservable with
  "the submitted input", and one wrong derived review profile makes only that
  stage unservable with "the workload profile digest" while the
  implementation stage still serves.
- **Whole `tests/job_manager`**: **1361 OK**, against 1299 OK on the base.
- **`tests.tools.test_stage_execution` + `test_packaging`**: **502 cases OK**
  on the candidate (488 OK on the base plus these 14), both exit 0. This is
  the suite that owns `servable_workers` and `held_configuration`.
- **`tests.tools.test_bootstrap`**: 135 cases with **17 errors on base and 17
  on candidate, byte-identical lists** — pre-existing in this root, none
  added.

### Remaining scope — returned, not claimed

Three acceptance items in `FINDING.md` are NOT satisfied by this candidate.

1. **The connected implementation → independent review → changes-requested
   correction → failed/held cycle for a CREATED Job is not driven.** The cases
   stop at a recorded, bound, servable Job whose review stage the real
   projection reports `blocked` behind its implementation. What exists to
   build on is `job_manager/review_driver.py`, the existing
   `tests/tools/correction_restart_trace.py` harness and
   `tests/job_manager/test_review_driver.py`'s line provider; the work is to
   drive one created Job through them and assert the findings, the correction
   round and the held result each retain their evidence and stay distinct from
   owner acceptance.
2. **The OBS-0 input-to-substantive-simulated-work interval is not measured.**
   No figure is offered and none should be inferred from the suite timings in
   the evidence, which are test-harness wall time and not a routine-start
   interval.
3. **`NewJobBinding.create_binding` is not driven against an installed
   instance.** It composes `bootstrap.prepare` through the inherited writer
   lock and atomic install write, and `tests.tools.test_bootstrap` runs beside
   it with no added failure — but no case installs an instance and then
   creates a Job in it end to end. This is the same limit the W358969 Work
   recorded for `DeploymentBinding.bind`, and it is the first thing to add.
   `DeploymentDerivation`, the other half, IS driven against a real owned
   deployment document.

Also unproved, and smaller: interruption is driven after the reservation and
after the binding, with the next run finishing the creation — but not INSIDE
`bootstrap.prepare` against a real instance; and whether a created Job then
SUCCEEDS is not proved, only that it is recorded, bound, unique, replayable
and servable.

### Cost

Read-only research across `templates.py`, `submission.py`, `fresh_attempt.py`,
`schema.py`, `store.py`, `documents.py`, `execution_limits.py`,
`tools/job_manager.py`, `tools/fresh_attempt_ports.py`, `tools/bootstrap.py`,
`tools/stage_execution.py` (`_disagreements`, `servable_workers`,
`_served_deployment`, `held_configuration`), `contracts/{pod,canonical,
manifest}.py`, and the existing `test_fresh_attempt`/`test_stage_execution`
fixtures. Test runs: the creation suite about twelve times during development
(the instructive failures were the depth-8 journal refusal described above;
`_bound`'s `except Exception` swallowing a simulated crash, which W361910's R4
review had already ruled against and which is now caught by a source
assertion; the derivation being asked a third time for the answer, now the
one it was composed from; a changed intent arriving as a generic
operation-collision, now its own named refusal; and four test-side mistakes of
mine — a `fresh_attempts` row with no prior Job, a SQLite handle closed from
the wrong thread, a `None` sentinel colliding with a fixture default, and an
assertion that every refusal names the top-level member a caller passed).
The whole `tests/job_manager` suite four times; `tests.tools.test_bootstrap`
once on each root; `tests.tools.test_stage_execution` plus `test_packaging`
once on each root at ~254s. No live provider, no engine, no total
manufactured.

### Boundaries

No Git operation of any kind, in the repository or in the scratch roots. The
canonical `v12/python` tree is byte-unchanged and the scoped status for it is
empty; `v12/DESIGN.md` remains the pre-existing dirty approved-contract
transcription and is untouched. Per the PLAN's split I wrote only
`candidate-362657/`, `evidence/claim-362657/` and this file; `FINDING.md`,
`PLAN.md`, `PLAN-HISTORY-362639.md`, `review-2026-10-26T18-44-13Z.md` and
`evidence/preparation-362639/` are the reviewer's and are unmodified, as is
every file in the W361910 dossier. No live provider, engine, credential read,
deployment, install, instance operation, migration or cutover. No store
opened, copied or traversed outside the disposable ones these cases create.

## claim362931 — R1 and R2 corrected; R3 reproduced and returned as a specification gap

Answers `review-2026-10-26T19-22-51Z.md` under handoff362925. Base
`19f02ce1295b4517a85f0822d48754efc982f388`, unchanged. At claim start all
eleven members of `candidate-362657` and its `MANIFEST.json` were re-hashed
and all twelve match what that manifest and the reviewer's
`evidence/review-362892/CANDIDATE-CHECK.json` record; the scoped status of
`v12/python` was empty. `candidate-362657/` is preserved untouched and the
corrected candidate is `candidate-362931/`.

**R1 and R2 are real, are mine, and are corrected here. R3 is real, is
bigger than a correction, and is returned with the executable reproduction
the review asked for.**

### Read position

`detail work=W361912`, `work-events` complete through seq362931
(`next_after` null) and thread `T361912` complete — one message at seq361912,
no newer discussion. `review-2026-10-26T19-22-51Z.md`, `FINDING.md`, `PLAN.md`
and all of `evidence/review-362892/` read in full, including `probe.py`,
`PROBE-RESULTS.json`, `CANDIDATE-CHECK.json` and the three FOCUSED logs.

### What is delivered

Candidate `candidate-362931/`, manifest
`02090c1c505a055722e15de6c3e06f3e9ed0b940619055a69253549a0169fc9b`, thirteen
members over base `19f02ce1295b4517a85f0822d48754efc982f388`. Six changed
since `candidate-362657` and two are new to the candidate — `submission.py`
and `fresh_attempt.py`, which R1 required.

| path | base | candidate-362931 |
| --- | --- | --- |
| `src/baton_v12/job_manager/creation.py` | new | `9b7c67f6e760dc24ef75b9217888391c8b18e19824973c27cbb3d4a44035b381` |
| `src/baton_v12/job_manager/submission.py` | see MANIFEST | changed (R1) |
| `src/baton_v12/job_manager/fresh_attempt.py` | see MANIFEST | changed (R1) |
| `src/baton_v12/job_manager/schema.py` | see MANIFEST | changed (`request_digest`) |
| `tests/job_manager/test_creation.py` | new | changed (R1, R2) |
| `tests/tools/test_creation_ports.py` | new | changed (R3 reproduction) |

The exact digests for all thirteen are in `candidate-362931/MANIFEST.json`,
which also records each member's digest in `candidate-362657` and whether it
changed. `candidate-362657/` is preserved byte-untouched. The seven unchanged
members — `documents.py`, `__init__.py`, `tools/creation_ports.py`,
`tools/job_manager.py` and the three schema-fixture test files — are
byte-identical to the reviewed candidate.

### R1 — one identity has one owner, across all three entry points

**Confirmed exactly as reported, and the sentence that was already in the
code names the defect.** `submission._unclaimed` carries a W358969 R6 comment
reading "ONE IDENTITY HAS ONE OWNER, and until now this knew about only half
of them" — and I added a third half without extending it. There are three
entry points into one Job identity space: ordinary submission, fresh-attempt
retry and template creation.

The correction is one `_RESERVATIONS` statement in `submission.py` — a UNION
over `fresh_attempts` and `template_jobs`, both of which carry the same three
identifying columns for the same reason, with a fourth column naming which
admission holds it so the refusal can say so. One statement rather than two
queries, because two queries are two chances to add a fourth relation to only
one of them. `fresh_attempt._reserved` gained the symmetric check, and
`creation._reserved`'s two separate fresh-attempt queries became one over
both names.

The refusal is ORDINARY, not durable, and `submission._unclaimed` already
says why in as many words: this operation identity is derived from the
submission id, which belongs to the RESERVATION HOLDER, so sealing a refusal
under it would let an intruder's rejected document permanently block the one
submission the reservation exists to admit. A case drives two refused
intruders and then the holder's own completion.

`OneIdentityHasOneOwnerAcrossEveryEntryPoint` drives every pair in both
arrival orders, including the reviewer's exact interruption, the
reserved-submission-name case, the exact reserved document still consuming
its reservation, the real `fresh_attempt.admit` refusing a reserved creation
identity (through that suite's own owner fakes rather than a reimplementation
of its insert), and an unrelated ordinary submission alongside a created Job
still recording normally.

### R2 — the replay is the caller's intent, and only that

**Confirmed, and it was a design error rather than an oversight.** I keyed the
journal signature on the resolution digest, which carries this deployment's
DERIVED facts. The review's probe completed a creation, changed one derived
digest, repeated the identical request and got "different creation".

The correction separates two facts that were conflated. What the caller asked
for is immutable — template selection, task, both scopes, acceptance,
overrides — and `_asked` now digests the OWNED request into
`request_digest`, derives the Job and submission identities from the request
alone, and the replay is keyed on those three members before the deployment is
asked anything at all. What the deployment derived is recorded in the new
`request_digest`/`resolution_digest` column pair as the created Job's
provenance and is never compared on replay.

Two consequences I took deliberately:

- **The derivation is now read exactly ONCE, inside the guard.** The first
  candidate read it twice and compared the readings; that comparison is how a
  replay came to depend on a fact the caller never stated. With nothing
  composed outside the guard there is nothing to go stale and no comparison
  to get wrong.
- **Three of my own cases were wrong and are corrected, not deleted.**
  `test_a_changed_derivation_is_a_different_creation` asserted the defect and
  is now `..._is_the_SAME_creation_and_replays`; `..._read_again_inside_the_guard`
  is now `..._read_exactly_once_inside_the_guard`; and
  `test_a_replay_asks_no_owner_anything` reset counters it never asserted —
  the review caught that its comment promised more than the code delivered,
  and every counter it resets is now checked.

`TheReplayIsTheCallersIntent` drives replay after a reopen, after the
derivation becomes unavailable entirely, and after the default generation
moves; that one intent spelled in two member orders is one creation; and —
the hazard the review named — that every caller-stated member still refuses
when it changes, member by member, with the recorded Job untouched.

### R3 — reproduced, and it is a specification gap rather than a correction

**The reviewer's inference is correct, and it is decisive.** I investigated it
first because it could have changed the design, and it does.

  1. `single_worker._task_bytes(given["task_document"],
     manifest["human_contract"])` reads the task from the DEPLOYMENT's
     configured path at static preflight and holds it as immutable bytes —
     "a change to the configured path afterwards cannot change what a later
     composition publishes". Its signature takes a path and a manifest
     artifact; there is no Job operand.
  2. `stage_execution._Stage.prepare_context` delivers exactly
     `worker.given["task_bytes"]` to the provider.
  3. `contracts.manifest` classifies `human_contract` as JOB INTENT — "which
     task, by content digest" — and `JOB_INPUT_EXCLUDED` deliberately does
     NOT contain it, so the task is INSIDE `job_input_identity`, which is
     what `_disagreements` compares against the Job's `input_digest`.

(1) and (2) mean a created Job executes the installed task. (3) means the gap
cannot be closed by deriving a different `input_digest`: a case drives
`stage_execution.servable_workers` with an input identity that names the
REQUESTED task and every stage is refused with "the submitted input".

So the honest statement is: **the requested statement, acceptance criteria and
selected work scope are retained as provenance in `template_jobs` and reach
no worker.** Five cases in `TheRequestedTaskDoesNotReachTheWorker` assert each
fact and the consequence, from the owning code.

**What closing it would take, and why I did not do it here.** The task
document would have to become per-Job, which means each serving worker's input
manifest must be composed per Job so its `human_contract` names the requested
task — and `task_document` is currently a deployment-level operand read once
at preflight and digest-bound to the installed manifest. That is a change to
the deployment configuration model owned by `bootstrap`, `single_worker` and
`stage_execution`, not to this operation. SCH-1a forbids the shortcut
explicitly ("no operator-authored manifests or bespoke launch packets"), so I
am not inventing a per-Job manifest surface to route around it. This needs the
owner's decision about where a per-Job task document lives before the
connected proof can mean anything — a connected rehearsal built on the current
model would prove that the INSTALLED task runs, which is exactly the false
success the review warns about.

### Evidence

`evidence/claim-362931/`, with `HOW-THESE-WERE-RUN.txt` and a before/after
table for both counterexamples.

- **The reviewer's `probe.py`, run UNCHANGED**: its `theft` case now raises
  instead of succeeding, so the script never reaches its own print. The
  traceback is `REVIEWER-PROBE-UNMODIFIED.stderr`; its stdout is empty and
  both files are kept so that is legible.
- **`probe-corrected.py`**: the same two constructions with the refusal
  caught. R1 — `foreign_submission.refused` true, `durable` false, and
  `original_resume` "completed" with both stages recorded. R2 — `replayed`
  true, `derivation_asked_on_replay` 0, `recorded_provenance_unchanged` true.
- **`tests.job_manager.test_creation`**: **76 cases, OK** (62 before).
- **`tests.tools.test_creation_ports`**: **19 cases, OK** (14 before).
- **Whole `tests/job_manager`**: **1375 OK**, against 1299 on the base root.
- **`test_stage_execution` + `test_packaging` + `test_creation_ports`**:
  **507 OK, exit 0**, against 488 OK exit 0 on the base.
- **`tests.tools.test_bootstrap`**: 17 errors on base and candidate,
  byte-identical lists.

### Remaining scope — unchanged plus R3's consequence

1. **The per-Job task document is an owner decision, not an implementation
   choice.** Stated above with its three owning code facts and its
   reproduction. Until it is settled, a connected
   implementation/review/correction/held rehearsal would prove the installed
   task runs.
2. **The OBS-0 interval is not measured.** No figure is offered.
3. **`NewJobBinding.create_binding` is not driven against an installed
   instance**, and interruption inside `bootstrap.prepare` is not driven. Same
   limit W358969 recorded for `DeploymentBinding.bind`.

### Cost

Read-only investigation of `single_worker._task_bytes`,
`stage_execution.prepare_context`, `contracts/manifest.JOB_INPUT_EXCLUDED` and
`validate.verify_manifest_digest` — the R3 question, taken first because it
could have changed the design. Then `submission._unclaimed`,
`fresh_attempt._reserved` and `store.replay` again. Test runs: the creation
suite about ten times (the instructive failures were my own three invalidated
case claims, an accumulating fake counter I asserted without resetting, a
contrived helper that reproduced the rule instead of driving it — replaced
with the real `fresh_attempt.admit` — and a refusal reading "by the a fresh
attempt" because I put the article in a SQL column, which
`test_fresh_attempt` caught); the ports suite four times (twice on a manifest
edit that invalidated its own self-digest, which §12 requires recomputing);
whole `tests/job_manager` three times; `test_bootstrap` once;
`test_stage_execution`+`test_packaging`+`test_creation_ports` once at ~248s;
both probes twice. No live provider, no engine, no total manufactured.

### Boundaries

No Git operation of any kind, in the repository or in the scratch roots. The
canonical `v12/python` tree is byte-unchanged and the scoped status for it is
empty; `v12/DESIGN.md` remains the pre-existing dirty transcription.
`candidate-362657/` and `evidence/claim-362657/` are preserved exactly, as is
every file in `evidence/review-362892/` — the reviewer's `probe.py` was
executed from where it sits and not copied or edited. Per the PLAN's split I
wrote only `candidate-362931/`, `evidence/claim-362931/` and this file. No
live provider, engine, credential read, deployment, install, instance
operation, migration or cutover.

## claim364551 — the connected creation, and the three defects it found

Answers the review at handoff E364548: one milestone — actual supported
CLI/package creation through real disposable owner stores and additive
binding/bootstrap, including interrupted publication recovery.
`candidate-364551/` is seeded from the accepted child candidate-364329
(manifest `006a7b427648976b7263b87fe497689d13e0fb3d5274bc4c2dad070bf8e925c5`)
over base `19f02ce1`; every earlier candidate is preserved byte-untouched.

### A correction to my own scratch roots, first

Every earlier claim of this Work and its child built roots from `v12/python`,
`v12/worker`, `v12/DESIGN.md` and the v12 JSON files, and reported 17
`test_bootstrap` errors as pre-existing. They were MINE: that suite reads
`v12/STACK.md` through `_DISTRIBUTION.parent`, which those roots never had.
On a root carrying the whole of `v12/` (minus `node_modules`) and without the
stray `v12-w71917-*` fixture directories, **`tests.tools.test_bootstrap` is
135 OK**. The errors were identical on base and candidate, so nothing rested
on them being product behaviour — but calling them pre-existing was wrong,
and it is also what kept the real install path out of reach for five claims.

### What the milestone found

Driving `tools/job_manager.py create` against an instance installed by
`tools/bootstrap.py` refused three times before it worked, and each refusal
was a real defect no fixture could see — because the two suites that exercise
the additive binding compose its inputs themselves.

1. **`install-inputs.json` was never written by anything.**
   `fresh_attempt_ports._install` reads it and its docstring already claimed
   `bootstrap.install` wrote it. Nothing did. So on a real install every
   additive binding — an ordinary creation's and a fresh attempt's — refused
   with "there is nothing here to add to". Fixed in `tools/instance.py` (the
   layout names the document, as it names every other document an instance
   owns) and `tools/bootstrap.py` (the installer writes it under the same lock
   and inside the same unwind as the selector and the justfile).
2. **The document `install` is handed is not one `prepare` accepts.** `main`
   adds the resolved `authority_uuid` for the selector, and that member is
   SUPERSEDED as an input — `prepare` refuses a document naming one. Keeping
   the handed document made the first binding refuse with "nothing reads
   authority_uuid", which is the same defect's second half: a kept document
   that cannot be prepared is no more use than an absent one. What is kept is
   now what was accepted.
3. **The servability question was asked without the Job's own task.** A Job
   created against a deployment that composes a per-Job task submits that
   task's Job-scoped input identity — `_task_agrees` refuses the creation if
   it does not — and the selector derives compatibility from the document a
   worker would serve the Job under, composed from the task it reads out of
   the `template_jobs` row. That row is written by the same operation, after
   this question. So every configured worker was judged against the INSTALLED
   identity and the creation refused "this deployment configures no worker
   that can serve the 'implementation', 'review' stage of the Job this
   request creates" for a pool that serves it. Fixed by passing the derived
   task document through `creation._servable` and the port's `serving` into
   the selector, which already takes that operand. The port contract gained
   an operand, so the test fakes that implement it were updated with it.

### The suite

`tests/tools/test_connected_creation.py`, **14 cases**, on
`test_bootstrap.ValidFixture` — whose workers are the accepted stage
fixture's and whose Authority identity is persisted before anything is
composed, which is the fresh-install order itself.

- a real install leaves a preparable input document, and says where;
- the supported command, entered with an operator's argv, creates one Job:
  every digest derived, the binding published with the derived producer, the
  Job entry appended beside the one the install already named, the submission
  admitted, the Job's own task document written, both resolved stages
  servable by a named worker;
- two ordinary creations bind two Jobs with two distinct tasks;
- replay answers the same Job and resolution digest, publishes nothing twice,
  leaves one created-Job row;
- changed intent under the same Job refuses and leaves the first untouched;
- interruption BEFORE the prepare leaves the harmless direction (install
  document names the Job, configuration does not bind it, no submission) and
  the same command finishes it without a second entry; interruption AFTER the
  binding leaves the binding and no submission, and the same command finishes
  it. Neither leaves a stage a scheduler could offer;
- four refusals — unsupported source, absent template, meaningless override,
  foreign Job store — each leaving the configuration and install document
  exactly as they were, with the foreign store never created;
- packaged resources: the template the answer names is the one this build
  carries with the roles the stages were resolved from, and the selector the
  install emitted carries the runtime digest and schema assets, read back off
  the instance.

### Verification

Candidate root `/tmp/w361912-551`, base root `/tmp/w361912-base`, both built
from the whole of `v12/`; `PYTHONPATH=src:.`

- **`tests.tools.test_connected_creation`: 14 OK.**
- **Whole `tests/job_manager`: 1375 OK.**
- **Six tools suites** (bootstrap, instance, packaging, creation_ports,
  connected_creation, job_task_delivery): 370 cases, ONE failure —
  `test_packaging.test_every_subcommand_this_command_serves_is_offered`,
  which fails identically on the BASE root (the deployed command does not
  offer `attempt-diagnostics`; nothing here touches `tools/stack.py`).
- **`test_single_worker` on the base root**: the one failure this Work has
  carried from the start.

### What remains for this Work

- The connected implementation/review/correction/held RESULTS and the whole
  OBS-0 input-to-substantive-work interval. The child proved the
  implementation and review runtimes reach a started container with the
  requested task; correction and held results, and the interval measurement,
  are not touched here and no figure is offered.
- A FRESH ATTEMPT has the same servability hole as defect 3 above when the
  prior Job carries a task document: `fresh_attempt` asks `serving` without
  one, and the new Job's row does not exist yet. I did not change that path —
  it is W358969's — and the port's new operand defaults to `None`, so its
  behaviour is exactly what it was. Reported rather than silently fixed.
- The CLI surfaces refusals as typed exceptions rather than exit codes, for
  every command. Uniform and not this Work's to change; the suite asserts what
  the product does.

### Cost

Reading: `job_manager._create`/`_creation_request`, `creation_ports`
(`NewJobBinding`, `DeploymentDerivation`, `instance_identity`, `agreeing`),
`fresh_attempt_ports` (`_install`, `_publish_install`, `serving`,
`InstanceOwnership`), `bootstrap` (`layout`, `install`, `main`, `prepare`,
`SUPERSEDED`, `without_installer_members`), `instance.layout`, and
`test_bootstrap`'s `ValidFixture`/installer fixtures. Probes: seven — the
installed layout, the state-root deployment, the missing control store, the
missing install document, the superseded member, the servability
disagreements before and after the binding is published. Test runs: the new
suite seven times (four failing: two assertions about state the reservation
cut writes before the submission, a CLI exit code this command does not
produce, and a runtime digest that is not prefixed); `tests/job_manager`
twice (52 errors the first time, from the port contract's new operand
reaching fakes that did not accept it); the tools group three times. No live
provider, no container engine, no deployed-instance mutation, no cutover, no
version-control operation.

### Boundaries

No Git operation of any kind. The canonical `v12/python` tree is
byte-unchanged. Every earlier candidate and evidence directory is preserved
exactly, including `candidate-362931/` and the child's accepted
`candidate-364329/`. I wrote `candidate-364551/`, `evidence/claim-364551/`
and this section. The bound `FINDING.md`/`PLAN.md` and every review are the
reviewer's and are unmodified.

## claim364768 — custody over the document I added

Answers `review-2026-10-26T23-51-22Z.md`: ownership-safe installer input
publication and unwind. `candidate-364768/` is seeded from
`candidate-364551` (manifest
`eec22c9f347798e583a4a6478a4368ab58f788c612393bd6838b5d272b97d440`); earlier
candidates are untouched.

### The reviewer is right, and the probe proves all three

I added a write and gave it none of the custody this module keeps for every
other document an instance owns. `_publish` renames a `.tmp` into place and
asks nobody about either name, so:

1. a regular `install-inputs.json` carrying foreign bytes was OVERWRITTEN and
   the install still published a selector;
2. a LINK at the temporary name was followed by the write, and the rename then
   promoted that link onto the real name;
3. a failure after the write LEFT the document behind — while the comment I
   put beside it claimed it was inside the same unwind as the justfile and the
   selector. That comment was wrong when I wrote it.

### The correction

- **`custody` asks about both names.** `install_inputs` and
  `install_inputs_temporary` join the link/outside loop, and either name
  existing is refused outright, exactly as the justfile and the selector are —
  before any effect, and asked again under the destination's lock.
- **The write is the justfile's own pattern.** `os.open` with
  `O_CREAT | O_EXCL | O_NOFOLLOW`, the identity pinned by
  `_identity_of_handle` the moment the file exists, the document written
  through that handle. There is no temporary and no rename anywhere, so there
  is nothing for a link to own: either this attempt creates the name or it
  does not exist.
- **The unwind covers it,** through `_remove_if_still_ours` — so a file
  somebody replaced between the create and the failure is left alone and
  reported as "no longer the installer input document this attempt made", and
  a failed install leaves no stale owned input to block the retry.
- The layout names the temporary (`install-inputs.json.partial`) so custody
  can refuse it; `instance.layout` and `bootstrap.layout` both answer it, as
  they answer every other document of an instance.

### What is asserted

`TheInstallerInputIsOwnedOrRefused`, eight cases: a foreign regular document
refused with its bytes intact and nothing published; a link refused with the
link and its target intact; a dangling link refused; a link at the temporary
name refused and not followed; a stale `.tmp` link INERT — the install
succeeds, the link and target are untouched and the creation still works,
which is a stronger answer than refusing it; a selector failure removing only
what this attempt made, with a retry that installs and creates; a document
replaced during the failure left alone; and a successful install owning a
regular file at that name, leaving no temporary of either spelling, with a
second install into the same destination refused.

**The reviewer's own probe**, with its one `installed()` assertion relaxed so
it can report instead of raising, is in `evidence/claim-364768/` with its
output: `existing` refused with bytes preserved and no selector,
`temp-symlink` succeeding with the foreign target untouched,
`temp-partial-symlink` refused by custody, and `failed-selector` leaving no
input document behind.

### Verification

Candidate root `/tmp/w361912-768`, base root `/tmp/w361912-base`, both the
whole of `v12/`; `PYTHONPATH=src:.`

- **`tests.tools.test_connected_creation`: 22 OK** (14 inherited + 8).
- **Whole `tests/job_manager`: 1375 OK.**
- **Six tools suites: 378 cases**, ONE failure —
  `test_packaging.test_every_subcommand_this_command_serves_is_offered`,
  which fails identically on the base root and is untouched here.

### What remains for this Work

Unchanged from claim364551 and acknowledged in the PLAN: the packaged-command
proof (a frozen bundle this environment cannot build), the reported
fresh-attempt task-lineage gap, the full correction/held workflow, and the
OBS-0 interval — no figure is offered.

### Cost

Reading `custody`, `serialized`, `install`'s unwind, `_remove_if_still_ours`,
`_identity_of_handle` and `_publish`. Test runs: the connected suite four
times (two failing — an assertion against the cleanup's own wording, and a
replacement that was indistinguishable from my own file because an unlinked
inode can be handed straight back, now renamed over instead); the tools group
and `tests/job_manager` once each; the reviewer's probe twice. No live
provider, no container engine, no deployed-instance mutation, no
version-control operation.

### Boundaries

No Git operation of any kind. The canonical `v12/python` tree is
byte-unchanged. Every earlier candidate and evidence directory is preserved
exactly; the reviewer's `install_probe.py` was read where it sits and copied
under a new name rather than edited. I wrote `candidate-364768/`,
`evidence/claim-364768/` and this section. The bound `FINDING.md`/`PLAN.md`
and every review are the reviewer's and are unmodified.

## claim366433 — the joined workflow, and how long the start actually took

Answers `PLAN.md`'s one remaining milestone and the handoff at E366429.
`candidate-366433/` is seeded from the owner-accepted package child
`candidate-366250`
(`9d3cb6830cbda604b2d15cec8d23269d42232a147a8521278fd16481a2f39b98`); **one
member changed — a new test file — and no product byte changed in this claim.**
That last sentence is the result as much as the suite is: the joined workflow
needed no correction.

### What was revalidated before anything was written

All 30 members of `candidate-366250` re-hashed to their recorded candidate
digests, and all 30 `base` digests re-hashed against the current tree: no
drift. `BASE_COMMIT` is the checked-out `18e771f0`.

### The fixture constraint, decided before the first test

The repository already has a full-lifecycle harness —
`test_stage_execution.ComposedOneJobCase` — and it is the obvious place for
this milestone. I did not use it. Its `setUp` runs `init`, `add` and `commit`
against a real repository, and standing policy forbids an agent performing a
mutating version-control operation without scoping that to the working tree.

So the joined path is driven on the no-version-control composition this Work's
own children established: the deployment-configured checkpoint profile with no
VCS behind it, and `no_version_control()`, which replaces `subprocess.run`/
`Popen` with wrappers that **raise** on any argv whose program is `git`. That
makes the boundary provable rather than promised: 15 passing cases is the
evidence that nothing spawned version control. Only
`ComposedOneJobCase.quiescing` — its multi-container engine double — is
borrowed, and it performs none.

### The workflow, in `tests/tools/test_joined_workflow.py` (15 cases)

**The verdict is the reviewer's, read back out of custody.** The review
container writes a `report.json` and a `baton.checkpoint-review/1` claim; the
real `review_verdict_from_result` reads them from accepted custody and
cross-binds them against the checkpoint the reviewer was attached to. The
fixture reads the three objects FROM the checkpoint rather than composing them,
because a fixture that invented them would be proving that refusal instead of
this path. The verdict is durable, recorded once, naming `baton.reviewer` at
revision 1.

**Independence is read, not asserted.** Two attempts, two participants
(`baton.claude` produced, `baton.reviewer` judged), two containers with
different runtime ids — and the reviewer's prepared boundary is the frozen
checkpoint's checkout, not the line the producer holds a writer on.

**The correction round is the product's own act.** Nothing in the suite calls
`open_correction`: the ticks after the review turn reach the composition's own
`routed`, which opens the next round from the recorded verdict. What the case
reads is a second implementation attempt with a *running* runtime, the line
`writing` again on the same line with the reviewed checkpoint still `frozen`
and the attachment `ended`, and the first round and the review both
`destroyed` and both kept.

**And round two is served the requested task.** This is the joined proof's
point and the place no earlier case looks: a correction that silently
delivered the installed document would be W363066's defect returning one round
later. The bytes in round two's own input root are the created Job's own task;
the statement, every acceptance criterion and every selected scope path are
the ones `creation.resolution_of` records; and the identity round two was
claimed against is the Job's own, not the installed manifest's.

**Round one's evidence survives it:** both earlier attempts still
`completed`/`sealed`/`retained`, both input roots still carrying the requested
task, and the verdict still readable from its own frozen result.

**A rejection stops without accepting anything.** The verdict records
`rejected`, the line's state is `rejected` at revision 1, no correction round
opens, no second implementation attempt is ever made — and the producer's
material is still sealed and retained, which is what makes a rejection
reviewable rather than a deletion.

**A held result is attributed truthfully.** A producer that ANSWERS `unable`
leaves the stage `exceptional` with review `blocked`; the disposition is the
worker's own answer, attributed to the participant that ran it; the material is
`sealed` and `retained`, which is what `report-and-hold` means. The case that
matters most is the negative one: nothing was frozen, no reviewer was
attached, no verdict exists and the line never left `idle` at revision 0 — so
there is nothing an operator or a later round could mistake for an accepted
candidate. Its input root still holds the task it was given.

**None of the three outcomes is an owner decision.** `nothing_was_owner_accepted`
asks three owners rather than assuming: the Authority's canonical target is
unmoved, the resolved workflow has exactly two stages (implementation then
independent review, which is SCH-1a's own sentence), and no attempt ever ran
for the configured integration participant.

### The OBS-0 interval

Measured on that same path, with the endpoints written into the class rather
than implied, and reported in `evidence/claim-366433/obs0-interval.json`.

    whole interval          0.128 s      (bound: 60 s)
      creation              0.010 s
      scheduling            0.108 s
      launch to work entry  0.010 s

It **opens** when the operator's selection arrives — a task id, a statement,
acceptance criteria and a selected work scope — and **closes** when the
assigned agent enters `work()` in its own runtime. The producing agent stamps
`time.monotonic()` there itself, so the closing endpoint is the agent's own.
The three legs are asserted to sum to the whole, so nothing was measured
outside what is reported.

**Inside, all of it:** the installed worker configuration read and proved; the
whole creation (template resolution, full-resolution digest, identity
reservation, Work authorization, deployment binding published and prepared,
per-Job task composed, submission admitted); every scheduler tick that follows
(offer, claim, principal allocation, writer grant, input root composed and
frozen, launch document, credential delivery, runtime start); and the in-image
startup through the worker's preflight.

**Outside, and OBS-0a is why:** the one-time install and the deployment's own
start — the stores, the configuration validation, the profile certification,
the session mint and the pool activation. That is `just start`, once per
deployment rather than once per task, and SCH-2's scheduler is persistent by
design. **Nothing per-run is outside.** There is no packet to engineer, no
script to author and no manifest to write, which is the clause OBS-0 adds
about not excluding per-run engineering by calling it task work — and
`test_the_measured_path_required_no_authored_procedure` reads that off the
recorded resolution rather than describing it: the caller's half carries a
statement, acceptance criteria and two scopes and **no `sha256:`, manifest,
launch or workspace member anywhere in it**, while the identities the Job
needed are the deployment's own derivations.

**The correction round is measured as a routine start too**, from the recorded
verdict to the second agent's own `work()` entry, because OBS-0a names retries
as routine. It is also well inside the bound.

**What the figure is NOT, said plainly.** The container engine and the provider
inside the workload are this suite's declared seams, so it contains no image
pull, no container start, no provider authentication and no model latency. It
is evidence about everything this product does between an operator's words and
the agent's first substantive act, on a prepared local deployment with local
SQLite stores, no version control and no network — and nothing more. **The
suite's own 34-second duration is not a startup figure and is not offered as
one.**

### Verification

Candidate root `/tmp/w366433`; `PYTHONPATH=src:.`

- **`tests.tools.test_joined_workflow`: 15 OK.**
- **Whole `tests/job_manager`: 1375 OK.**
- **Eight tools suites** (joined_workflow, job_task_delivery,
  retry_task_lineage, connected_creation, creation_ports,
  fresh_retry_line_recovery, bootstrap, instance): **444 OK**.
- **The same eight plus `test_correction_restart`: 450 cases, 3 failures and
  2 errors — all five in that suite and all five PRE-EXISTING ON THE BASE.** I
  added that suite to the run myself because this claim is about the
  correction workflow, and I am keeping the log rather than reporting only the
  eight-suite number. Its scenario harness reports "preparation did not
  answer" from `setUpClass`; the same six cases fail identically in
  `/tmp/w366433-base`, the tracked tree at `18e771f0` with no overlay at all.
  No product byte changed here or in the accepted candidate, so neither can
  cause it. Both logs are in the evidence directory.

The carried observations from the retry review stand unchanged and unweakened:
the baseline status-inventory failure and the undisposed Authority-handle
warning are still separate diagnostics, and nothing here touched those tests.

### Cost

Reading `review_driver`'s `end_review_from_result`, `review_verdict_from_result`,
`_review_claim` and `open_correction`; `stage_execution`'s `routed` and its
`correction_policy`; the `checkpoint_verdicts`, `review_lines`,
`review_attachments` and `line_checkpoints` schemas; `single_worker`'s judgment
reader; `ComposedOneJobCase` and `TheComposedJobTraversesReviewAndAcceptance`
(to establish that the existing lifecycle harness commits and is therefore
unavailable); `scripted_agent`; and DESIGN OBS-0/OBS-0a in full. Probes: four —
the review turn and verdict on the no-VCS path, the correction round and what
survives it, the rejected and held outcomes, and the interval itself. Test
runs: the new suite six times (two failing — a case that asserted the caller's
request shape against the wrong column, and a draft that bound two other
suites' case classes at module level and so re-ran their assertions here);
`tests/job_manager` once; the tools group three times; the base tree twice. No
live provider, no model, no container engine, no deployed-instance mutation, no
install, no migration, no cutover.

### Boundaries

No Git mutation of any kind, and this claim's suite proves it rather than
promising it: `no_version_control()` raises on any `git` argv, so 15 passes is
the assertion. The only version-control calls anywhere in this claim are
`rev-parse`, `log`, `status`, `diff` and `archive`, all reads. The canonical
`v12` tree is byte-unchanged and **no product file changed**. Every earlier
candidate — `candidate-362657`, `candidate-362931`, `candidate-364551`,
`candidate-364768` — and every child candidate and evidence directory is
preserved and re-verified. The bound `FINDING.md` and `PLAN.md` and every
review are the reviewer's and are unmodified; I wrote `candidate-366433/`,
`evidence/claim-366433/` and this section.

### What remains for the owner, not for me

The human evidence checkpoint `PLAN.md` records as due per owner E366414 is
still unobserved, and `PLAN.md` says this final parent milestone will require
one as well. Suggested message for this claim's bytes:
`test(v12): prove the joined creation workflow and its startup interval`.
Neither is a continuation gate and neither is mine to perform.

## claim366616 — the measurement, corrected on the connected owner path

Answers `review-2026-10-27T16-27-58Z.md`. **Both findings were right and
neither was a near miss.** `candidate-366616/` is seeded from `candidate-366433`
(`36f50a504872872a566f1b941b4f1c27501eb235b57aadd9395d1626baded322`, all 31
members re-hashed to their recorded digests and all 31 base digests re-hashed
against the current tree before anything was written: no drift). Two members
changed, both tests; **no product byte changed in this claim or in the one
before it.**

### What I got wrong, plainly

**R1.** My interval's report said it included "Work authorization, deployment
binding published and prepared". It did not. `test_joined_workflow` borrows
`test_job_task_delivery`'s creation ports, and those are `test_creation`'s
`FakeDerivation`, `FakeAuthorization`, `FakeBinding` and `FakeOwnership`. I
borrowed a helper for its convenience and then described the operation as
though the helper were not there — and the supported command's own parsing and
composition were never in the interval at all. The reviewer's probe printed the
four fake types; there is nothing to argue with.

**R2.** My correction case called `judged(...)`, which runs sixteen
reconcile/sweep rounds before returning, and *then* started the clock. So the
routing, the allocation, the preparation and the launch I claimed to be
measuring had already happened; the probe observed the second runtime already
`running` when the timer opened. The figure I reported was close to meaningless
and the label on it was wrong.

Neither is evidence that the product is slow. Both are evidence that I measured
the wrong thing and then wrote a confident report about it.

### The corrected measurement, on the connected path

`tests/tools/test_connected_startup.py`, 7 cases. The instance is **installed by
the real `bootstrap.main`**, the Job is created by the **real
`tools.job_manager.main`** with the operator's own argv, and behind that command
the admission owners are the **real adapters**: `DeploymentDerivation` reading
the instance's emitted configuration, `WorkAuthorization` on the instance's own
Authority, `NewJobBinding` publishing into `install-inputs.json` and calling
`bootstrap.prepare` — which revalidates the whole deployment — and
`InstanceOwnership` taking the real instance guard. The pool is then composed
from that same installed configuration and serves the Job through real in-image
turns.

That the owners were real is asserted **from their effects**, not described:
the published binding is read out of the instance's own `deployment.json`, the
appended entry out of `install-inputs.json`, and the open Work out of the
instance's own Authority. A fake records those; it does not perform them.

    initial interval        0.157 s      (bound: 60 s)
      command + admission   0.040 s
      scheduling + launch   0.113 s
      runtime startup       0.004 s

    correction interval     0.294 s      (bound: 60 s)
      verdict to launch     0.290 s
      runtime startup       0.004 s

**The correction clock now opens before anything it measures** — immediately
after the review turn returns, with no reconciliation in between — and the
suite *asserts the verdict relation is empty at that instant*, so the verdict
is not yet recorded. The review said "if opening earlier is simpler, report
that conservatively and accurately rather than backdating an observation", and
this opens earlier than the point it was asked to open at. The figure is larger
than my previous one because it finally contains the work: the ending that
records the verdict, the routing, `open_correction`, the allocation, the writer
grant, the input root, the launch and the second agent's startup. A second case
reads each of those effects out of the stores afterwards, so "inside the clock"
is checked rather than claimed.

Both reports are retained, in one document, each with its own endpoints, its
inclusions, the one-time exclusions, the seams and an explicit
`not_established` list — `evidence/claim-366616/obs0-intervals.json`, which
names the report it supersedes in its own `supersedes` member.

### What was removed, and what was kept

`test_joined_workflow.TheRoutineStartupInterval` is **gone**, because it was the
defect; its four cases are not re-homed and its text is preserved verbatim at
`evidence/claim-366616/REMOVED-TheRoutineStartupInterval.py.txt`. The
supersession is recorded in that file's own docstring so a later reader meets it
where the class used to be. `evidence/claim-366433/` is untouched, including its
`obs0-interval.json`.

The **eleven workflow cases are unchanged** — the verdict read from frozen
output, independence, the correction round opened by the loop and served the
requested task, round one's evidence surviving, the rejection, the held
`unable` result and its negative checks, and the three owner-acceptance reads.
Review 2026-10-27T16-27-58Z verified all of those independently and they never
depended on the admission owners being real: what they read is the loop, the
ending, the attachment and the stores.

### The seams, named and not called owners

The container **engine** is `_ConcurrentEngine` (no image pull, no container
start). The **provider** is `scripted_agent` (no model, no credential
authentication). The **checkpoint profile** has no version control behind it,
and both suites install runners that **raise** on any `git` argv — so 18
passing cases is the evidence that none was spawned, not a promise. The
installed one-folder **runtime** is `test_bootstrap`'s stand-in directory and
nothing here executes it; that the real frozen command creates and replays
ordinary Jobs is W366246's accepted proof, reused rather than re-run, which the
review expressly allows.

**Not established, stated so no summary has to infer it:** the correction round
is measured to the second agent's first substantive act — a completed corrected
candidate and a second review are not reached. The proposal and the verdict are
synthetic deterministic content, not an applicable version-control change and
not a live model's judgment.

### Verification

Candidate root `/tmp/w366616`; `PYTHONPATH=src:.`

- **`tests.tools.test_connected_startup`: 7 OK.**
- **`tests.tools.test_joined_workflow`: 11 OK.**
- **Whole `tests/job_manager`: 1375 OK.**
- **Nine tools suites** (connected_startup, joined_workflow,
  connected_creation, job_task_delivery, retry_task_lineage, creation_ports,
  fresh_retry_line_recovery, bootstrap, instance): **447 OK**.

`test_correction_restart` is not in this run. Its 3 failures and 2 errors were
reported last claim with a base rerun proving them pre-existing, and both logs
are preserved in `evidence/claim-366433/`; nothing here touches it and no new
base rerun is offered for it. The status-inventory and Authority-handle
observations remain unwaived and unweakened.

### A carried observation, unchanged

Under `-W always::ResourceWarning` the connected cases report "unclosed
database" from `tools/job_manager.py`'s `create`, which composes
`WorkAuthorization.opened` and lets the process exit without disposing the
Authority. This suite reaches it precisely *because* it uses the real CLI. It is
pre-existing — claim366250 recorded it and the parent FINDING carries it — it is
harmless for a command-line process, and no product byte was changed for it.
Every handle this fixture opens is disposed or cleaned up.

### Cost

Reading the review in full; `creation_ports`' four real adapters;
`bootstrap.main`/`prepare`; `tools/job_manager._create`; `test_bootstrap`'s
`ValidFixture.workers`; and the reviewer's own `timing_boundary_probe.py`.
Probes: three — composing the pool over a really installed configuration,
driving a CLI-created Job to a running runtime there, and the full connected
round through the review turn and the correction. Test runs: the new suite five
times (two failing — the installed configuration has no `job_bindings` member
at the top level, and my own wrong expectation that round two's runtime would
be `destroyed` when the clock closes at its agent's first act and nothing has
ticked since); the workflow suite twice; `tests/job_manager` once; the tools
group once. No live provider, model or container engine; no install beyond the
disposable ones the cases make; no migration or cutover.

### Boundaries

No Git mutation of any kind, and both suites prove it rather than promising it.
The only version-control calls anywhere in this claim are `rev-parse`, `log`,
`status`, `diff` and `archive`, all reads. Canonical `v12` byte-unchanged and no
product file changed. `candidate-366433` and every earlier candidate, every
child candidate and every evidence directory — including claim366433's
superseded interval report — are preserved and re-verified. The bound
`FINDING.md` and `PLAN.md` and every review are the reviewer's and are
unmodified; I wrote `candidate-366616/`, `evidence/claim-366616/` and this
section.

The human evidence checkpoints `PLAN.md` records remain pending and are not
mine to perform. Suggested message for these bytes:
`test(v12): measure routine and correction startup on the connected path`.
