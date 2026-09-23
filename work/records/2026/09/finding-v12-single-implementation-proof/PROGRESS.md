# Implementer progress — W239528

## 2026-09-22 — baton.claude, claim 239653, the baseline prepared

Owner reroute 239632: "Prepare only the implementation-through-cleanup baseline
under its FINDING/PLAN. Read W236087 review-2026-09-22T14-56-01Z.md, preserve
inherited changes and establish file ownership. Independent review before
returning the bounded operator command. No live execution, destructive
recovery, reviewer stage or resume."

No store was opened, no container started, no grant minted, no runtime cleaned
up, no live run performed and no mutating version-control operation run. No
file under `v12/` was edited.

**Ownership established first.** `detail work=W236087` answered `phase: block`,
`agent: null`, `claimed_at: null` -- its handler released safely, so there is no
concurrent claim. `OWNERSHIP-239528.md` records what this Job owns and what it
only reads. All ten digests in W236087's `review-evidence-239589.json` were
re-read at the end of this claim and every one matches, including
`PACKET-INPUTS-239485.json` at `5672cb74...`, so nothing inherited was
overwritten.

**Diagnosis carried and corroborated.** `DIAGNOSIS-239528.md` states the fault
as fact -- the provider created a branch inside the container and authored both
commits, `ClaudeAgent._unmoved` refused a history the adapter did not write, the
turn faulted with no manifest -- and the cleanup blockage: a faulted ending froze
and collected nothing, so no intake receipt exists and `authorize_cleanup` was
never reached, which the retained axis reading `pending` rather than
`blocked-on-intake` is what discriminates. New this claim: the corroboration
that this is existing, tested product behaviour, in
`tests/manager/test_claude_agent.py::ThePreparedLineRefusesWhatItCannotAccountFor::test_a_provider_that_committed_refuses_rather_than_being_adopted`.
The provider edits and verifies; the adapter commits and publishes.

**The baseline is code, not a description.**

* `baseline.py` -- W236087's supervisor reduced to one stage. `KINDS` is closed
  over `implementation`; `_BOUNDS` carries no `review_invocations` or
  `corrections` and `held_packet` refuses a packet that names one;
  `implementer_invocations` must be exactly 1. The packet proving, admission
  gate, termination discipline, cancellation seam, tri-state runtime accounting
  and cleanup journal reads are carried over unchanged.
* NEW: `_attributions` and `line_attribution`. The retained proposal's commit is
  read out of the manager's own durable line -- `writer_for_attempt` names it,
  `line_of` gives its path -- and author, committer and parents are checked. A
  commit attributed to anyone but `Baton worker <worker@baton.invalid>`, or with
  other than exactly the declared base as its single parent, is a shortfall.
  `_git_read` checks the verb against a closed reading list before the child
  starts and closes the environment; nothing here can write.
* `baseline_bindings.py` -- one submitted stage, one implementer invocation, the
  proposal output declared REQUIRED, `findings`/`logs` not declared at all, a
  fixture carrying no acceptance or review-feedback document, and task
  instructions that state the requirement and say who owns the commit.

**One product constraint was recorded rather than routed around.**
`stage_execution._held_workers` refuses a deployment naming no review worker:
"a Job that cannot be produced or independently reviewed serves nothing". That
invariant is about capability, not about what one submission asks for, so
`baseline_bindings` CONFIGURES a review worker with its own participant and
principal and never submits a review stage. Deleting it to make this Job look
smaller would have been relaxing an independence rule to pass a validator. The
result is a stronger claim: a reviewer was configured and launchable and this
run started exactly one container anyway, which
`test_a_reviewer_was_available_and_this_run_started_no_container` asserts.

**Verification.** 58 focused deterministic checks, measured 7.146396200994786s,
receipt in `verification-1.json` with `verification-1.log`. It records the
digests of the five W236087 ancestor files so the derivation is checkable rather
than asserted. Engine and provider subprocess are the two accepted seams;
version control, the adapter, the ending driver and the cleanup journal are real.
Cumulative measured across this Job: 7.146396200994786s.

The two cases this file exists for: the positive attribution over a real
adapter-authored commit, and `test_a_provider_that_commits_is_reported_and_never_settles`,
which reproduces W236087's live failure through the same real code and asserts
that this run reports it rather than settling.

**Prepared for the owner, not performed.** `OPERATOR-239528.md` and
`SELECTIONS-239528.json` carry the bounded command with every owner decision
marked; `PROVIDER-QUESTION-239528.md` states the one question that needs a real
provider and why a fake cannot answer it. The packet selects a NEW `run_id`
because `managed-correction-236087`'s grant is consumed.

**Outstanding and NOT done here**, all of it owner-side or another Job's:
W236087's faulted attempt recovery; its consumed grant; step 5a Authority
preparation; the operator's own selections; and the live run itself.

State: awaiting independent review. Passing to `baton.rvpc`.

## 2026-09-22 -- baton.claude, claim 240196, R1 and R2 complete

Review 2026-09-22T15:32:51Z requested changes on two counts before the operator
command; owner reroute 240193 selects both within the existing baseline scope.
Both are done. No store was opened on any deployed instance, no container
started, no grant minted, no runtime cleaned, no live run, no mutating
version-control operation, and no file under `v12/` edited.

**Both findings were reproduced against the current tree before anything was
changed.** The composer really does fail with `ModuleNotFoundError: No module
named 'baton_v12'` in a child with no inherited `PYTHONPATH`; `job-a` really
was hard-coded at three sites; and `_attempts_of` really does filter the status
projection to the selected Job, so an older Job's runtime was never going to
appear in this run's accounting whatever the operator document claimed.

**R2 -- a fresh run name is not a fresh Job, and this run accounts for one Job.**

* The Job identity is composed. `baseline_bindings._job_identity` derives
  `job-<run_id>` by default, so a fresh run identity is a fresh Job identity
  without an operator having to know they are two different things. `job-a` is
  refused by name: it is the identity already recorded in the W236087
  instance's Job store.
* `baseline.survey` reads `job_rows` and `stage_rows` BEFORE any owner act and
  refuses a Job identity the store already records. The collision used to
  surface at `submit`, which is after `prepare` has configured storage,
  certified a profile and minted a one-run qualification grant -- so the old
  behaviour spent an exactly-once grant to discover a run it could not make.
  `main` returns exit 2 for it, with nothing spent and no outcome written.
* The admission gate is now scoped to one Job. This closed a defect the
  reviewer's finding implies but does not state: `serve` sweeps the STORE, and
  the caps are counted by KIND, so an unrelated Job's eligible implementation
  stage would have been admitted here, spent this run's single invocation and
  started a container against work nobody selected. A foreign stage is refused
  before it reaches the composed deployment, and recorded in
  `foreign_admissions` rather than `gate_refusals` -- a refusal ends this run,
  and a stranger in the store must not be able to do that.
  `test_another_jobs_stage_never_spends_this_runs_invocation` drives a real
  second submission through the public API and asserts the stranger reached the
  gate and was turned away while this run still settled.
* The accounting claim is withdrawn rather than reworded. The outcome carries
  `job_id`, `preexisting_jobs`, `preexisting_stages` and an `accounting_scope`
  sentence saying plainly that a runtime belonging to another Job is NOT
  covered by it and its absence is NOT established by it. W236087's outstanding
  runtime stays outstanding, separately, whichever arrangement is selected.

**R1 -- the commands are commands now, and they are exercised as such.**

* `test_entrypoints.py` is new. `TheDocumentedComposerRunsAsDocumented` runs
  the exact command `OPERATOR-239528.md` prints, in a CHILD PROCESS with
  `PYTHONPATH` removed from the environment and then set to the bound source
  alone, with `cwd` at the filesystem root so nothing resolves relative to a
  shell -- over a RELOCATED copy of the real `baton_v12` and `tools` made with
  `shutil.copytree`. The reviewer's own reproduction is kept as a regression:
  without the binding it fails at the first product import AND writes nothing.
* `TheDocumentedSupervisorRunsThroughMain` drives `baseline.main` itself, which
  no test reached before: exit 0 on a settled attributed run, exit 1 on an
  elapsed bound with the engine asked to stop, exit 2 on a source this process
  does not import, and exit 2 on a Job identity the store already holds. The
  refusal case is the sharp one -- the relocated copy is byte-identical, so
  every pinned digest verifies and only `verify_imported_sources` can catch it.
* The operator document binds the interpreter, the import path and absolute
  program paths; carries an actual Step 5a with the Authority calls; and states
  `preflight`'s real limits -- it is a helper neither CLI main calls, a missing
  capability name is conclusive while a present one is not, and it cannot
  verify route handlers at all. The previous revision claimed it supplied the
  route-handler list, which contradicted the helper's own docstring.
* `SELECTIONS-239528.json` now separates retained facts from open choices. The
  image, worker adapter digest, manager source and installed runtime were
  re-read from disk under this claim and match `PACKET-INPUTS-239485.json`
  exactly: image `sha256:2e9e84ff...7456bd`, adapter `abdf903d...bb4d`, 106
  flat manager-source files, `baton-v12-stack` `04aa459a...a58a`. What stays
  open is named and explained.

**One thing I could not establish, stated rather than assumed.** The reuse
alternative -- running on the W236087 instance -- is now possible because the
Job identity no longer collides, but its faulted attempt still holds an open
assignment in that Work's scope, and whether the manager admits a new
assignment for the same participant while one is open needs that deployment's
stores opened. This claim did not open them. The operator document recommends
the fresh isolated instance and records the reuse path with that caveat
attached rather than buried.

**A fixture defect the Job identity change exposed and fixed.** The test
harness prepared one packet and supervised another; the qualification grant
binds `packet["context"]["job_id"]`, so once the two packets stopped sharing
`job-a` the opening admission had no grant for the Job it was admitting. The
fixture now prepares the packet it drives, and the packet's Job identity is
read from the submission it writes.

Verification: 77 focused deterministic checks, measured 15.704004109s, receipt
`verification-2.json` with `verification-2.log`. It records the digests of the
five W236087 ancestor files, so the copy-rather-than-import derivation stays
checkable. Engine and provider subprocess are the two accepted seams; version
control, the adapter, the ending driver and the cleanup journal are real.

Cumulative measured for W239528, naming every run I actually timed:
7.146396201 + 7.149914038 + 7.138971223 (claim 239653) + 15.684039575 +
15.704004109 + 7.187 + 6.480 + 7.670 (claim 240196) = **74.160325146s**. Short
diagnostic runs during development were not individually retained and are not
in that figure; the reviewer is right that the earlier handoff quoted a rerun
that was not in PROGRESS's total, and this entry fixes that by listing the runs
rather than quoting one.

All ten inherited W236087 digests re-verified byte-identical. `git diff --check`
clean. State: awaiting independent review.

## 2026-09-22 -- baton.claude, claim 242687, the expired-credential failure path

Owner pass 242683 after the accepted command RAN. The provider's OAuth token
had expired; the run reported nothing for 900 seconds and left its container
standing. The owner selects failure handling BEFORE credential renewal and
leaves the credentials expired. That decision was recorded in FINDING and PLAN
before any implementation, as the pass requires (`pin_242687.py`).

No credential renewal, no live rerun, no destructive recovery, no reviewer
stage, no resume. `/home/sl/baton-runs/single-implementation-239528/run` was
read and not modified, and no store belonging to it was opened; `live-242687/`
holds a read-only copy of its outcome, task, submission, four exchange events
and both provider logs.

**Reproduced first, from the run's own bytes.** Replaying the retained provider
stdout through the real `ClaudeAgent`, the real ending driver and the real
composed stage gave the live outcome exactly: `implementation answering`,
`stopped overall-bound-exceeded`, no committed cleanup, same shortfall. The
manager's own deferral row named the cause.

**Two defects, and the second only became visible once the first was fixed.**

1. `review_driver.end_implementation` performed publication as an
   UNCONDITIONAL step seven. `integration.retain_proposal` refuses -- rightly
   -- a frozen result that is not `completed`, so steps eight and nine (fence
   the assignment, `authorize_cleanup`) were never reached. `PUBLISHABLE`
   states the rule the module already states for its other ending, and all
   three entry points read it. Cleanup then committed positively -- and the
   stage still sat in `answering` for the whole bound.
2. `stage_execution`'s composed conclude returned `outcome: "held"` for a
   non-completed contextual turn. Holding the CONTEXT USE is right and is
   kept; `outcome: held` is the review vocabulary for "nobody may be scheduled
   on this", and `_finished` reads it as "the ending did not finish" and
   returns before `settle_ending`. Two different facts had one answer. The
   context hold now travels as its own member and the obligation settles.

**Measured on the same bytes**: before, `overall-bound-exceeded` at tick 901
with no cleanup; after, `exceptional` at tick 3 with `retained`/`absent`
cleanup, `outstanding_cleanup: []`, `state: held`, no proposal and no false
success. All four of the owner's requirements have their own check in
`test_failure_path.py`, which pins the retained bytes by digest.

**The reporting is actionable now.** The live run said
`KeyError: 'baton.git-proposal/1'` -- this program's own lookup. `_proposals`
reads the frozen disposition first, reports `ended 'unable' ... read the
attempt's retained provider log`, and the outcome carries a
`workload.dispositions` member so a failed run says what happened where an
operator can find it. A turn that froze no result at all is distinguished from
a completed one whose proposal could not be read.

**Nine accepted product tests changed expectation, and this is the part to
review first.** `tests/manager/test_claude_context.py` asserted through
`assert_owed` that an unhealthy provider terminal leaves the ending obligation
owed. Their SUBJECT is unchanged and still asserted -- the terminal is not
accepted, the context use never becomes `ready`, no generation is written, the
provider is not called again. What changed is the stage half, which is exactly
what the owner ruled wrong. `assert_owed` is KEPT for the cases that genuinely
still owe an ending (a COMPLETED turn whose context finalization refuses); those
call sites are untouched and still pass. The new `assert_reported_and_held`
carries the corrected contract and explains itself.

**Successful-result coverage is preserved.** `tests.job_manager.test_review_driver`
164/164; `tests.manager.test_claude_context` 81/81; this dossier's 87 checks
include every earlier attribution, entrypoint, Job-scope and packet case
unchanged. `tests.tools.test_stage_execution` runs 424 with the SAME 12
pre-existing `SimpleNamespace has no attribute 'reconciles'` fixture errors
that predate this Work, in the port/integration fixtures rather than the ending
path; they are reported, not touched.

Verification: 87 focused deterministic checks, measured 17.608050957s, receipt
`verification-3.json` with `verification-3.log`. Product suites measured
separately: review_driver 5.414s, claude_context 37.901s, stage_execution
159.202s.

Cumulative measured for W239528, listing the runs rather than summarising:
7.146396201 + 7.149914038 + 7.138971223 (claim 239653) + 15.684039575 +
15.704004109 + 7.187 + 6.480 + 7.670 (claim 240196) + 17.608050957 + 15.699 +
5.414 + 37.901 + 159.202 + 38.245 + 38.117 + 2.118 (claim 242687) =
**388.464376103s**. Short diagnostic runs were not individually retained.

State: awaiting independent review.

## 2026-09-22 -- baton.claude, claim 242906, R1 and R2 packet corrections

Review 2026-09-22T23:53:34Z ACCEPTED the product correction and refused the
failure command on two counts; owner reroute 242903 selects only those two
corrections. Both are done. No product byte changed under this claim, no store
was opened, no container started, no credential read, no live provider called,
no deployment provisioned and nothing recovered. Credentials remain expired.

**R1 -- the command would have run the uncorrected code, and the reviewer is
right.** `OPERATOR-FAILURE-242687.md` bound
`/home/sl/baton-runs/managed-correction-236087/manager-source` as its import
path. That snapshot was taken under W236087; I bound it without reading it. It
holds `review_driver.py` `b5b22535...ebe10c` and `stage_execution.py`
`33c78091...6e81` -- exactly the PRE-correction bytes -- so the documented
command would have imported the unconditional publication and the context-held
ending, and reproduced the 900-second stall it exists to disprove. I confirmed
that by reading those two files directly.

`snapshot_242687.py` prepares a SUCCESSOR snapshot at
`/home/sl/baton-runs/single-implementation-242687/manager-source`: the same
flat `baton_v12/` + `tools/` layout, 106 files, copied from the corrected
checkout. It then VERIFIES rather than assumes -- the two corrected modules
must carry the independently accepted digests (`9a8a4a81...20ae4`,
`ebc9be29...032896`) and the preserved snapshot must still carry the superseded
ones -- and refuses to write its manifest if either check fails. The old
snapshot is untouched: W236087's own packet is bound to those bytes, and the
reviewer said plainly that overwriting it is not the remedy.

`test_successor_snapshot.py` exercises it in three parts, because the claim has
three halves that can each be wrong alone: the snapshot carries the accepted
bytes and the preserved one still carries the superseded ones (asserted against
the FILES, not against the manifest that describes them, plus a check that the
two digests genuinely differ so the other two mean something); a CHILD PROCESS
with the documented `PYTHONPATH` reports which `review_driver.py` it actually
loaded and that `PUBLISHABLE` is present, with the reviewer's counterexample
kept as a regression -- the same child bound to the preserved snapshot answers
`False`; and the expired-credential replay settles against a packet whose
`manager_source` and `code_boundary` ARE the snapshot, at the owner's bounds.

**R2 -- the operational finding is exactly right.** `OPERATOR-FAILURE-242687.md`
named `SELECTIONS-FAILURE-242687.json` and the dossier contained no such file,
so the lower bounds and the new run and store operands were prose rather than a
composed input anyone could review. That file now exists, and
`test_the_selections_name_this_snapshot_and_these_bounds` checks it against the
packet the replay actually proved rather than letting it drift.

It binds `total_seconds: 120` and `cleanup_seconds: 30` per owner reroute
242903, the successor snapshot, a new run identity
`single-implementation-242687` (the 239528 grant was consumed by its own
failure), and genuinely fresh dedicated Authority, Job, control and integration
stores.

**And I weakened an accepted boundary, which the reviewer caught.** The previous
precondition said the first run's instance was reusable and reduced the rule to
"no other live work". The accepted boundary excludes stores containing OTHER
WORK, and the first W239528 run left an unfinished ending and cleanup in those
stores -- that is preserved failure evidence, not an empty instance. Admission
filtering scopes new stages to this Job; it does not isolate store-wide
recovery and endings. The corrected preconditions say the first run's instance
is NOT reusable, and the selections point at fresh stores; a test asserts none
of the four store paths names the 239528 root.

The operator document also now tells an operator the one thing that would
silently reproduce the defect: check `manager_source.files` in the composed
packet, and if `review_driver.py` reads `b5b22535...` you are composing against
the preserved snapshot.

Verification: 100 focused deterministic checks, measured 19.205028231s, receipt
`verification-4.json` with `verification-4.log`. The 87 earlier checks are
unchanged and included; 13 are new. No product suite was re-run under this
claim because no product byte changed -- `PRODUCT-CHANGE-242687.json`'s after
hashes still describe the tree, and the reviewer verified all three
independently.

Cumulative measured for W239528, listing the runs: 7.146396201 + 7.149914038 +
7.138971223 (claim 239653) + 15.684039575 + 15.704004109 + 7.187 + 6.480 +
7.670 (claim 240196) + 17.608050957 + 15.699 + 5.414 + 37.901 + 159.202 +
38.245 + 38.117 + 2.118 (claim 242687) + 19.205028231 + 1.493 (claim 242906) =
**409.162404334s**. Short diagnostic runs were not individually retained.

State: awaiting independent review.

## 2026-09-23 -- baton.claude, claim 243174, the successful-baseline stall

Owner pass 243171, after a run in which the real provider DID follow the
edit-only contract. Findings were recorded in FINDING and the path pinned
BEFORE implementation, as that pass requires (`pin_243174.py`).

`/home/sl/baton-runs/single-implementation-success-239528/run` is preserved and
was read only; no store belonging to it was opened. Evidence copied to
`live-success-243174/`. **No file under `v12/` was edited under this claim**;
the three product paths accepted under claim 242687 still carry their accepted
after-hashes.

**The result that matters.** The provider completed in 18.3s over five turns
and reported: "The change is left uncommitted in the working tree (`git status`
shows ` M harness.py`); nothing else was touched." Verification printed
`READY`. The retained outcome carries one proposal authored AND committed by
`Baton worker <worker@baton.invalid>` with exactly the declared base as its
single parent, a destroyed runtime and `retained`/`absent` cleanup. That is the
first half of `PROVIDER-QUESTION-239528.md` answered.

**Finding 1, the custody failure, established rather than guessed.**
`context_delivery._private` refuses any custody directory carrying group or
other bits. Running the product's own `_state` measurement over the preserved
context home, with `{conversation_id}` resolved, reproduces the refusal
exactly: `protected custody owner or mode changed`. Seven directories the real
CLI created carry `0o755` -- `.claude/backups`, `projects`, `session-env`,
`session-env/<conversation>`, `shell-snapshots`, `projects/-output` and
`projects/-output/memory`. The state file and credential symlink are exactly as
the profile requires; it is the directories on the way to them.

Why no test caught it: the fixture's fake provider chmods its two state parents
to `0o700` -- it has always compensated for precisely this -- and the real CLI
creates four more directories besides those two. **Diagnosed, not fixed**:
whether the manager should tolerate a umask-created directory or the delivery
should impose the mode is a product decision with its own security reasoning,
and it is recorded as the next selection.

**Finding 2, corrected.** Once the context use is held, the composed stage
returns `provider-context-unproved` and never settles, so the stage projects
`answering` forever -- the same conflation corrected under claim 242687 for
`unable`, one branch over, now reaching a COMPLETED turn whose proposal was
produced, published and cleaned up. Nothing could change after that point and
the supervisor swept for 443 of 900 seconds.

`baseline.py` now stops when it stops moving. `STALLED_TICKS = 6` consecutive
identical observations of `(stage states, accountable attempts, each attempt's
cleanup axis)`, and every condition must hold throughout: the stages
non-terminal, at least one accountable attempt, and NO outstanding cleanup. Six
is argued rather than picked -- `serve` ticks at one second, so it is six
seconds of a run doing nothing, long enough that an ending mid-flight across
several journalled operations is not mistaken for a stall. An unreadable
progress read RESETS the counter rather than advancing it: failing towards
keeping the run alive is the only direction that cannot invent a stall. The
outcome reports `stalled_ticks`, `stalled_after`, and a held reason in its own
words. A shorter bound would have made the same non-answer arrive sooner; the
bound stays the backstop and this is the mechanism.

**Finding 3, corrected, and the owner's question answered from the file.**
`outcome.json` WAS retained -- 4127 bytes at 18:34 for a run that began at
18:26, complete and internally consistent. This is read from the file, not
inferred from the exception. What was missing is that `main` never caught
`SupervisorInterrupted`, so the operator got a traceback and the one thing they
needed -- where the outcome is -- was the one thing not printed. `main` now
prints the interruption, the retained outcome's path, its state and stop
reason, and the document, and exits 130. A held ending names its outcome path
too.

**And the builder finding from review 2026-09-23T00:06:24Z.**
`snapshot_242687.py` deleted its destination before copying, so a rerun would
have destroyed the snapshot independent review had just verified and bound --
a reviewer had to tell an operator not to run it. A builder whose safety
depends on nobody running it twice is not safe. It now REFUSES an existing
destination, offers `--verify` to re-check one and `--rebuild-into <path>` to
make another, and never removes a tree. `--verify` confirms the bound snapshot:
106 files, accepted bytes present, preserved snapshot unmoved.

**Reproduced through actual composition.** `test_no_progress.py` stops the
fixture compensating: it leaves the context home as a real CLI leaves it, AFTER
the turn -- which is the live ordering, since the adapter published its receipt
over those modes without complaint and it was the manager that refused later.
The real `finalize_context_use` then refuses for the real reason. Context
integrity is asserted (the use is held and never `ready`), and so is
no-false-success (the run is `held` and the proposal it really produced is
still reported). Three cases guard the other direction: an ordinary successful
run still settles with `stalled_ticks: 0`, an unreadable progress read never
invents a stall, and an outstanding cleanup is never called stalled.

Verification: 112 focused deterministic checks, measured 24.356673542s, receipt
`verification-5.json` with `verification-5.log`. The 100 earlier checks are
unchanged and included; 12 are new.

Cumulative measured for W239528: 409.162404334s (through claim 242906) +
24.356673542 + 8.536 + 5.164 + 3.979 + 5.170 (claim 243174) =
**456.368077876s**. Short diagnostic runs were not individually retained.

State: awaiting independent review.

## 2026-09-23 -- baton.claude, claim 243284, R1/R2/R3

Review 2026-09-23T00:50:59Z requested three corrections; owner reroute 243281
selects all three. Done. No file under `v12/` was edited under this claim; the
three product paths accepted under claim 242687 still carry their accepted
after-hashes. No store opened, no container, no credential, no live run, no
renewal, no recovery, no closure.

**R1, P1, and it was mine.** The progress read I added under claim 243174
called `_guarded` with DISPOSABLE `uncertainty=[]` and `interrupted=[]` lists.
`_guarded` catches `BaseException`, so the `KeyboardInterrupt` the installed
handler raises was swallowed there, the predicate returned True and ORDINARY
SERVING RESUMED. The reviewer's actual-composition probe injected SIGINT before
any provider turn and watched a whole turn execute afterwards; a direct
`KeyboardInterrupt` vanished into a `settled` outcome. I introduced that while
correcting a different stall, and it is exactly the kind of regression the
no-progress rule was supposed to prevent.

The read now catches `Exception` only. An unreadable journal is still
progress-neutral -- it resets the counter rather than advancing it, failing
towards keeping the run alive -- and its diagnostic goes into the run's REAL
`uncertainty` list instead of being discarded. `KeyboardInterrupt` and
`SystemExit` travel out of the predicate, out of `serve`, and into the shutdown
handler that already existed; the fix is to stop standing in front of it.

Four regressions at that exact boundary:
`AnInterruptionAtTheProgressReadStopsServing` covers the signal shape and the
direct shape, each asserting NO further provider turn, a retained interrupted
outcome and a non-zero `main` status; a third keeps the ordinary-failure
direction and asserts the diagnostic is kept; a fourth drives `main` to 130.

**R2.** `--rebuild-into` changed only the destination tree and still wrote the
fixed `MANAGER-SOURCE-242687.json`, so a successor replaced the accepted
predecessor's manifest and the default `--verify` then checked the old tree
against the new one. A successor that destroys its predecessor's evidence is
the same mistake the snapshot existed to avoid. `manifest_for` now pairs each
snapshot with its own manifest, an existing manifest is refused as firmly as an
existing tree, and `--verify` checks the selected PAIR and refuses a manifest
that names a different path. Five regressions over disposable trees only,
including the defect itself -- the bound manifest must be byte-identical after
a successor is built -- and each cleans up the manifest it creates.

**R3.** `BOUNDS.total_seconds` is 300 rather than 900, argued rather than
picked: it covers one provider turn at its own 180-second ceiling plus the
launch, the exchange, the ending's nine journalled steps and the publication,
and it no longer has to cover a run that stopped moving, which
`STALLED_TICKS` detects in six. Measured against the two real runs -- 31 ms and
18.3 s of provider time -- 300 leaves two minutes of headroom over a
full-length turn neither came close to using.

`OPERATOR-SUCCESSOR-243284.md` and `SELECTIONS-SUCCESSOR-243284.json` deliver
the concrete successor packet: the verified successor snapshot, 300/60 bounds,
a new run and Job identity, and fresh dedicated stores -- EVERY earlier
instance now holds other work and none is reusable.

**And the packet says first that it is NOT successful-baseline ready.** Owner
reroute 243281 is explicit about this and it is right: the custody-mode blocker
is unresolved, so a run today will reach it. What it will do differently is
report it in about six seconds instead of spending its bound, and name the
retained outcome. That is better reporting, not an end-to-end proof, and the
document, the selections `_unresolved_blocker` block and this entry all say so
rather than leaving a reader to infer it.

Verification: 121 focused deterministic checks, measured 25.037361138s, receipt
`verification-6.json` with `verification-6.log`. The 112 earlier checks are
unchanged and included; 9 are new.

Cumulative measured for W239528: 456.368077876s (through claim 243174) +
25.037361138 + 11.524 + 5.716 + 5.848 + 1.618 (claim 243284) =
**506.111439014s**.

State: awaiting independent review.

## 2026-09-23 -- baton.claude, claim 243990, remaining R2/R3

Review 2026-09-23T01:02:06Z closed R1 and left four narrow corrections; owner
reroute 243987 selects exactly those. Done. No file under `v12/` was edited;
the three product paths accepted under claim 242687 still carry their accepted
after-hashes. No store opened, no container, no credential, no live run, no
provisioning, no recovery, no closure.

**R2 -- truthful creation provenance.** The CLI called the builder with the
ORIGINAL's claim for every build, so a successor created under a different
assignment still recorded 242906. A manifest naming the wrong episode is worse
than one naming none: it reads as evidence somebody produced under review that
nobody did. `--claim <seq>` is now required for a successor and refused before
anything is copied; the original replays its own `ORIGINAL_CLAIM` and its
historical manifest is untouched. The manifest distinguishes CREATION from
RECIPE -- `created_by_claim` is the episode that ran it, `recipe.original_claim`
and `recipe.original_path` are what it shares with the original -- because a
successor shares the recipe and does not share the authorship. Three CLI
regressions: the claimless refusal, the recorded provenance, and the original's
claim still reading 242906.

**R3 -- four defects in the successor command, all real.**

* `$BASE` was invoked but never assigned, so in a fresh shell it expanded
  empty. It is bound now from the fixture repository step 2 creates, and the
  document says `$BASE` must also be the Authority's canonical target.
* Precondition 3 linked `OPERATOR-239528.md`'s step 5a, which literally opens
  `/home/sl/baton-runs/single-implementation-239528/db/authority.sqlite3` and
  writes to it. That is a write-capable example pointed at a preserved
  instance holding an unfinished Job. The successor now carries its own
  preparation block reading STORE, UUID, Work, participants and receipts from
  `$SEL`, with an assertion that refuses if an older instance creeps in.
* The comparison table credited the REFUSED draft's pre-correction snapshot
  and 900-second bound to `OPERATOR-FAILURE-242687.md`, which was ACCEPTED and
  already carries the corrected snapshot and 120/30. Two tables now: what this
  successor changes against the accepted failure packet (300/60, and which
  ending it expects to reach), and separately what has changed since the
  refused draft.
* No test referenced the actual successor selections or its document.
  `test_successor_packet.py` reads the delivered file as delivered -- bounds,
  bound snapshot, every store the successor's own with all four older roots
  named and excluded, run and Job identity, supervisor digest, and which
  members are still `<OWNER>` -- asserts the document's four corrections, and
  composes the real selections substituting ONLY the `<OWNER>` members, then
  runs the documented composer as a child process with `PYTHONPATH` bound to
  the real successor snapshot. `manager_source` and `code_boundary` travel
  verbatim, because substituting them would test a tree nobody ships.

**The custody blocker stays explicit.** The document still opens with it, the
selections still carry `_unresolved_blocker`, and
`TheDocumentSaysWhatItIsNotReadyFor` asserts both rather than trusting them to
stay.

Verification: 139 focused deterministic checks, measured 25.444851811989793s,
receipt `verification-7.json` with `verification-7.log`. The 121 earlier checks
are unchanged and included; 18 are new.

Cumulative measured for W239528: 506.111439014s (through claim 243284) +
25.444851812 + 25.374094302 + 0.408 + 1.618 (claim 243990) =
**558.956385128s**.

State: awaiting independent review. Successful baseline still not ready, and
the packet says so first.

## 2026-09-23 -- baton.claude, claim 244098, the custody mode

Owner reroute 244096 selects the remaining custody-mode correction. The
decision was recorded in FINDING and the three paths pinned BEFORE any edit, as
that reroute requires (`pin_244098.py`). No live run, no deployed
provisioning, no image rebuild, no recovery, no reviewer stage, no resume, no
closure. Nothing chmods the retained evidence.

**The manager's checks are preserved exactly.** `context_delivery._private`,
`_state`'s link and special-file refusals and the credential-slot symlink rule
are untouched. The defect was never that the check was wrong; it was that the
deployment handed the provider a process that creates world-readable
directories and then asked the manager to accept them.

**Established rather than assumed**, which the reroute asks for explicitly.
`subprocess.run(..., umask=0o077)` was exercised against a real child: an
`os.makedirs` tree, an `os.mkdir` with an EXPLICIT `0o755`, and a file all came
out `0o700`/`0o700`/`0o700`/`0o600`. `mkdir` applies `mode & ~umask`, so a
child under this mask cannot create a group- or other-readable directory even
when it asks for one, and the mask is inherited by its descendants. The
`umask` operand is `Popen`'s own and is applied after fork without
`preexec_fn`, which matters because the provider spawn already runs beside a
reader thread and `preexec_fn` is documented unsafe with threads.

The observed evidence is consistent with exactly this: the seven non-private
directories are all `0o755`, which is `0o777 & ~0o022`, and the two private
ones are the CLI asking for something stricter. **The one residual risk is
stated rather than hidden**: `chmod` is not masked, so a provider that made a
directory permissive after creating it would still be refused -- which is the
right outcome, is its own finding if it ever happens, and is why the check is
not weakened.

**Only the provider child.** A mask on the whole worker would also narrow what
the adapter writes into the shared private line, whose group access the
deployment configures on purpose. `PROVIDER_UMASK` is applied to the provider
spawn and to nothing else, and a focused case asserts no other child's mask
moved.

**The fixture stops compensating, which is the deterministic proof.**
`tests/manager/test_claude_context.py`'s fake provider had always chmodded its
two state parents to `0o700` -- the fixture-only repair that is exactly why no
deterministic test ever saw this. It now creates `memory`, `backups`,
`shell-snapshots`, `sessions` and `session-env` the way a real CLI does and
chmods nothing. All 81 context checks still pass, which means the adapter's
mask is what makes them compliant; remove the mask and they fail on a layout
the fixture never touches.

`TheRealLayoutIsCompliantBecauseOfTheMaskNotARepair` makes that unmissable:
every directory under the context home is private, the observed layout is the
one created, the manager's own `_state` -- the function that refused the live
run -- accepts it, and the context generation actually seals (`status: ready`,
which the live run never reached). **Negative custody coverage is preserved**:
`ACustodyModeTheRealProviderProduces` still drives a whole run whose home is
made readable after the turn and still expects the stall, and a fifth case
chmods the sealed home and asserts `_state` refuses with the live run's exact
message.

Verification: 143 focused deterministic checks, measured 26.850900484991143s,
receipt `verification-8.json` with `verification-8.log`; 4 are new. Product
suites: `test_claude_agent` 224, `test_claude_context` 81,
`test_review_driver` 164 -- 469 together in 59.258s, no failure or skip.

Cumulative measured for W239528: 558.956385128s (through claim 243990) +
26.850900485 + 25.560063872 + 59.258 + 38.230 + 14.917 + 7.197 (claim 244098)
= **730.969349485s**.

State: awaiting independent review.

## 2026-09-23 -- baton.claude, claim 244216, the corrected worker image

Owner reroute 244214 selects the corrected worker-image build and the successor
packet. The selection was recorded in FINDING and the accepted source verified
in the tree BEFORE the build, as that reroute requires (`pin_244216.py`
refuses if the tree is not the accepted `18c34ff5...f9d8d`).

No live provider execution. No deployed provisioning, recovery, reviewer stage,
resume or closure. No file under `v12/` was edited this claim.

**Coordination with W244180.** The tuner's Work is bound to
`work/records/2026/09/finding-v12-review-job-preparation/` and was active when
this claim began. There is no file overlap: that dossier is its own, this one
is W239528's, and nothing here touches it or W239533.

**The image.** `baton-v12-claude-worker:w239528-244216`, built from
`v12/worker/Dockerfile.claude` over the accepted source, at
`sha256:c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8ad9d6cad334ca2`.

**Verified from INSIDE the artefact, not from the build context.** Every digest
was read out of a container started FROM the image, `--network none
--read-only` with the entrypoint overridden; the recipe makes exactly this
point about itself. `opt/baton/claude_agent.py` is `18c34ff5...f9d8d`, and
`PROVIDER_UMASK` was read back by name as `0o77` from the running image rather
than inferred from the digest. The provider CLI is unchanged at 2.1.247.
`IMAGE-ARTIFACT-244216.json` records the whole `/opt/baton` inventory.

**The predecessor is preserved and that was checked before anything was
written.** `baton-v12-claude-worker:w236087-236349` is still tagged, still
`sha256:2e9e84ff...7456bd`, and still carries `abdf903d...bb4d` -- the adapter
WITHOUT the correction. Every earlier packet in this campaign binds it, and
W236087's own packet still names it. `image_244216.py` refuses if that digest
has moved, and refuses if the new image turns out to be the same artefact.

**The packet binds what was verified.** `SELECTIONS-SUCCESSOR-244216.json`
carries the built reference and config digest, the four worker-file digests
read from inside the image, fresh dedicated stores under
`/home/sl/baton-runs/single-implementation-244216/`, a new run and Job
identity, and the retained 180/300/60 bounds.
`TheCorrectedImageIsWhatThePacketBinds` asserts the selections agree with the
artefact record file by file -- a packet naming a digest other than the one
that was verified would bind an image nobody checked -- and that the new
artefact is distinct from the preserved one.

**What it can and cannot answer, in the document and in the selections.** It
CAN answer whether the real CLI under the provider mask leaves a context home
the manager can seal, which is the one thing no deterministic test can
establish and the reason this image exists. It CANNOT answer that it will:
review 2026-09-23T03:19:21Z is explicit that the retained `0o755` modes are
consistent with umask creation but do not exclude an explicit `chmod` or a
reset mask. If the CLI does either, the run reaches the same custody hold --
reported now in about six seconds rather than at the bound -- and that is a NEW
finding rather than a failure of the packet. The operator document says which
outcome means which, and tells an operator to check
`worker_image.config_digest` before running, because binding
`sha256:2e9e84ff...` would silently ask the old question again.

Verification: 151 focused deterministic checks, measured 26.85811222800112s,
receipt `verification-9.json` with `verification-9.log`; 8 are new.

Cumulative measured for W239528: 730.969349485s (through claim 244098) +
26.858112228 + 0.408 (claim 244216) = **758.235461713s**. The image build and
its verification are artefact work rather than test time and are recorded in
`IMAGE-ARTIFACT-244216.json` instead.

State: awaiting independent review.

## 2026-09-23 -- baton.claude, claim 244292, the preparation step

Review 2026-09-23T03:30:58Z R1; owner reroute 244290 selects only it. Done. No
image rebuild, no live provider, no deployed provisioning, no recovery, no
reviewer stage, no resume, no closure. No file under `v12/` was edited.

**R1, and it was a real trap.** `OPERATOR-SUCCESSOR-244216.md` told an operator
to follow `OPERATOR-SUCCESSOR-243284.md`'s step-5a block "with `$SEL` pointing
at this packet's selections" -- but that block hardcodes the 243284 selections
path and asserts `"single-implementation-243284" in store`, so pointing it at
the 244216 file raises `AssertionError` before `Authority.open` is reached. A
preparation step that cannot be pointed at the packet it is documented beside
is not a preparation step.

`prepare_instance.py` is that step, parameterized. It takes `--selections` and
`--base`, and its freshness check is DERIVED from the selections' own `run_id`
rather than naming a run -- a helper carrying a literal would be the same
defect one release later. It refuses before opening anything if a store does
not name this run, if one names a consumed instance, if any `<OWNER>` member is
unresolved, or if `--base` is not a full object name. Then it performs the acts
the old block performed. The document references it instead of reprinting a
block that only ever worked for one packet.

**Tested through supported interfaces, not prose.** `test_preparation.py`
drives `prepare_instance.prepare` against a DISPOSABLE Authority made with
`Authority.create`, then reads the results back through the Authority's own
public readers: `project_work` for the Work and scope, `capabilities_of` for
each of the four grants, `policy("canonical_target")` for the base. The same
delivered selections then go through `baseline_bindings.compose`, so
preparation and composition are exercised over ONE document. The freshness
check is also asked about the PREDECESSOR's selections and answers
`single-implementation-243284` -- which is the point: it is not that 243284 was
wrong, it is that a literal cannot answer for two packets.

**A claim of mine was wrong and the measurement corrected it.** The helper's
first draft said in its own docstring that a second run would refuse, and the
operator page repeated it. Driving it twice showed otherwise: `create_work` is
journalled under an operation identity derived from the run, so a repeat
REPLAYS and answers the same Work and scope. Both documents now say that, and
`test_a_repeat_replays_the_same_act` holds them to it. I have left the
correction visible in the docstring rather than quietly rewriting it.

**Outcome diagnoses qualified.** The document's `no-progress` entry asserted a
mechanism -- "the CLI did something a mask cannot govern" -- that no run has
shown. Each entry now names a STATE and what to read, in order, and says
plainly that an explicit `chmod` and a reset umask are both consistent with
non-private directories and the modes alone do not separate them. The
`overall-bound-exceeded`/traceback entry no longer calls itself a regression in
advance.

**The reviewer's inspection limit is disclosed on the page.** Its no-network
read-only container was denied Docker API access before it could read content,
and it took no stronger retry or fallback. So the inside-image byte and version
claims are AUTHOR evidence, independently corroborated at the image-metadata
level but not independently re-read from inside the image, and the document
says so rather than leaving the reader to assume otherwise.

Verification: 166 focused deterministic checks, measured 27.029541312003857s,
receipt `verification-10.json` with `verification-10.log`; 15 are new.

Cumulative measured for W239528: 758.235461713s (through claim 244216) +
27.029541312 + 0.073 + 4.906 (claim 244292) = **790.244003025s**.

State: awaiting independent review.

## 2026-09-23 -- baton.claude, claim 244389, R1/R2 and the real entrypoint

Review 2026-09-23T03:42:19Z R1 and R2; owner reroute 244386 selects both and
adds the entrypoint test. Done. No image rebuild, no live provider, no deployed
provisioning, no recovery, no reviewer stage, no resume, no closure. **No file
under `v12/` was edited.**

**R1 -- the documented command could not run as printed.** Step 5a imports
`baton_v12.authority`, and the block did not bind `PYTHONPATH`; the reviewer
ran it in a fresh shell and got `ModuleNotFoundError`. Every other command on
that page binds the selected manager source and this one simply did not. It
now reads `PYTHONPATH="$BOUND" "$PY" -B "$DOSSIER/prepare_instance.py"`, and the
page says why, naming the review that found it.

**R2 -- the freshness check could be walked around.** `fresh()` compared
consumed-instance names with `in` against the raw store string and exempted any
name equal to the run, so `/home/sl/baton-runs/single-implementation-244216/../
single-implementation-239528/jobs.sqlite3` passed: the substring matched the
run, the exemption fired, and the check let a store inside a CONSUMED run
through. It now normalizes the path first and compares COMPONENTS, requires the
run to be a component of each store rather than a substring, and refuses a
consumed `run_id` outright with no exemption. A valid new instance still
replays, which is the behaviour measurement established last claim and which
the R2 work had to preserve rather than trade away.

**The entrypoint is now exercised as an entrypoint.** Earlier cases drove
`prepare_instance.prepare` in-process; `TheDocumentedEntrypointRunsThroughComposition`
runs the command the page prints, as a subprocess, from `/`, against a
disposable Authority, and then composes the SAME resolved document through
`baseline_bindings`. It reads the results back through the Authority's own
public readers, and a companion case runs the same command with `PYTHONPATH`
unset and holds it to the exact failure the review reported -- so R1 has a
regression, not just a corrected sentence.

**Three things the test surfaced, each recorded rather than smoothed over.**
The freshness check refused the fixture's own store paths, because they do not
lie under a run directory -- that is the check working, so the case copies the
disposable Authority into a run-named directory instead of weakening it.
`create_work` refused the fixture's existing Work under a different operation
identity, correctly: preparing a successor must not adopt somebody else's Work,
so the case derives a fresh name that still carries this Authority's prefix.
And the bound source cannot be the fixture's tiny `boundpkg` tree, so it is
derived from where this process actually imported `baton_v12`; the comment says
why, since binding the fixture tree would have made the R1 regression pass for
the wrong reason.

Verification: 174 focused deterministic checks, measured 27.046156366996s,
receipt `verification-11.json` with `verification-11.log`; 8 are new.

Preservation, checked at the end of this claim rather than asserted: all five
product paths carry their currently accepted after-hashes -- the
`test_claude_context.py` entry in `PRODUCT-CHANGE-242687.json` is superseded by
`PRODUCT-CHANGE-244098.json`, whose `before` equals it exactly, and the tree
matches the later record. Both images are unchanged
(`sha256:c862c055...`, `sha256:2e9e84ff...`), the bound manager-source snapshot
verifies at 106 files, all ten inherited W236087 digests are byte-identical,
and `git diff --check` is clean. No mutating Git operation was performed.

Cumulative measured for W239528: 790.244003025s (through claim 244292) +
27.046156367 + 1.569 (claim 244389) = **818.859159392s**.

State: awaiting independent review.
