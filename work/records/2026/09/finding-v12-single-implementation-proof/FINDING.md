# One managed implementation through proposal and cleanup

## 2026-09-22 — owner splits W236087 into separate Jobs

Work: W239528. Owner rejected adding incremental stages to the same growing
resume Job: split the Jobs and run them separately. This Job owns the first
baseline only. W236087 retains resume and its historical evidence. A separate
independent-review Job follows this baseline.

Observed precursor: W236087's live run admitted one implementation and no review;
the provider claimed all four workflow stages, while the adapter reported agent
fault, no readable proposal and no committed cleanup. Runtime was reported
quiescent, not positively cleaned. Exact fault and cleanup causes remain open;
see the source dossier review-2026-09-22T14-38-24Z.md and live-239365 evidence.

Acceptance: one implementation-only task through the real manager and worker
adapter; explicit provider edit/verification versus adapter commit/publication
ownership; independently inspected, attributed proposal bytes; stopped execution
and positive cleanup. No reviewer container, correction or resume in this run.
Do not count model prose as proposal acceptance or quiescence as cleanup.

Use focused deterministic coverage first. The later bounded real-provider run
asks whether the actual provider follows the adapter's edit-only contract and
its actual output passes collection through cleanup; a fake cannot establish
provider behavior. Prepare exact reviewed inputs/command before owner execution.
Creation does not authorize a live run, destructive recovery or reuse of the
failed consumed grant. Preserve all prior evidence and outstanding resources.

## 2026-09-22 -- claim 239653, the baseline prepared and the fault established

Owner reroute 239632 continues the split under this dossier's own scope. The
baseline is prepared as code and evidence, and is returned for independent
review; nothing was executed, recovered, enabled or closed.

**The precursor fault is no longer "observed"; it is established.** W236087's
provider created a branch inside its container and authored both commits
itself. `ClaudeAgent._unmoved` runs after the provider turn, before anything is
measured or published, and refuses when HEAD is not the revision the turn was
admitted at -- so nothing was published and the terminal carried no manifest.
The ownership boundary the FINDING asks to be explicit is:

    THE PROVIDER EDITS AND VERIFIES. THE ADAPTER COMMITS AND PUBLISHES.

This is existing, tested product behaviour rather than a claim made here:
`tests/manager/test_claude_agent.py` already carries
`test_a_provider_that_committed_refuses_rather_than_being_adopted`. The defect
was the packet's task document, which scripted four stages. Full evidence and
the cleanup diagnosis -- a faulted ending froze and collected nothing, so no
intake receipt exists and `authorize_cleanup` was never reached, which the
retained axis reading `pending` rather than `blocked-on-intake` discriminates --
are in `DIAGNOSIS-239528.md`.

**"Independently inspected, attributed proposal bytes" is a check, not a
phrase.** `baseline._attributions` reads the retained commit out of the
manager's own durable line and requires author and committer to be
`Baton worker <worker@baton.invalid>` with exactly the declared base as the
single parent. A proposal nobody can attribute does not settle this run. The
reader is read-only: its verbs are checked against a closed list before any
child starts.

**A deployment-level invariant was met rather than relaxed, and this is the one
decision here a later reader is most likely to question.**
`stage_execution._held_workers` refuses a configuration naming no review
worker: "a Job that cannot be produced or independently reviewed serves
nothing". The owner's split says this run has no reviewer container. Those are
compatible, because the invariant is about what a deployment is CAPABLE of and
the split is about what one submission asks for. So `baseline_bindings`
CONFIGURES a review worker, with its own participant and principal, and submits
one implementation stage. Deleting the worker to make this Job's deployment
look smaller would have been weakening an independence rule to pass a
validator. What the run establishes is therefore stronger than "no reviewer
existed": a reviewer was configured and launchable, and exactly one container
started.

**Reuse without overwriting.** `baseline.py` and `baseline_bindings.py` are
W236087's programs reduced to one stage, COPIED rather than imported: that Work
continues to change for resume, and a baseline whose proof moved with it would
not be a baseline. `verification-1.json` records every ancestor digest so the
derivation is checkable. All ten preserved W236087 digests were re-verified
unchanged; no product byte was edited.

Verification: 58 focused deterministic checks, 7.146396200994786s measured.

What is NOT established and is deliberately left to its owners: whether a real
provider follows the edit-only contract (`PROVIDER-QUESTION-239528.md`, an
owner-selected run), W236087's faulted-attempt recovery, its consumed grant,
and the review and resume Jobs.

## 2026-09-22T15:32:51Z — independent review, claim 239808

The preparation-complete claim above is superseded for the operator packet by
`review-2026-09-22T15-32-51Z.md`: changes requested. The deterministic baseline
passes all 58 focused checks, including attributed proposal and positive cleanup;
no live execution or recovery was performed.

Confirmed R1: the documented composer lacks the bound import environment and
fails before writing without an implicit PYTHONPATH. “Step 5a” is absent and the
preflight helper cannot prove the route/scope facts claimed in the operator prose.
The exact standalone command remains to be prepared with reusable accepted inputs.

Confirmed R2: a changed run ID still composes `job-a`; the second submission to
one disposable Job store refuses the collision. Accounting filters by Job, so
the claim that this run reports a previous Job's outstanding runtime is also
unsupported. Select and test the exact isolated Job/store arrangement before
owner acts; keep W236087's outstanding runtime separate and preserved.

Evidence: `review-evidence-239808.json`, `review-tests-239808.log`, and
`review-probes-239808.py` / `review-probes-239808.json`. All ten preserved W236087
digests match. Reviewer measured 7.556328105s total; author measurements remain
separately attributed. Return to baton.decide with bounded correction scope.

## 2026-09-22 -- claim 240196, the operator command corrected

Review 2026-09-22T15:32:51Z accepted the deterministic baseline and refused the
operator command, on two counts that were both correct and both reproduced
against the current tree before anything was changed.

**A run identity is not a Job identity.** Every packet this composer wrote
named `job-a`, so "select a fresh `run_id`" did not make the documented
instance reuse executable: two such packets collide in one Job store at
`submit`, which is AFTER `prepare` has spent an exactly-once qualification
grant. The Job identity is now derived from the run identity, and
`baseline.survey` refuses a collision before any owner act.

**And one run accounts for one Job.** `_attempts_of` filters the status
projection to the selected Job, so an older Job's outstanding runtime was never
going to appear in this run's attempt discovery, cancellation or cleanup. The
operator document had claimed it would. That claim is withdrawn rather than
reworded: the outcome now names every other Job the store holds and states
plainly that it covers none of them.

**A defect the finding implies and the correction closes.** `serve` sweeps the
STORE, and the admission caps are counted by KIND. An unrelated Job's eligible
implementation stage would therefore have been admitted by this run, spending
its single invocation and starting a container against work nobody selected
here. Admission is now scoped to one Job, and a foreign stage is recorded as
foreign rather than as a refusal -- because a refusal ends the run, and a
stranger in the store must not be able to end a correct one.

**A command that cannot be run is not a command.** The documented composer
invoked plain `python3` and fails at its first product import in any child
without an inherited `PYTHONPATH`. Both entrypoints now bind the interpreter,
the import path and absolute program paths, and `test_entrypoints.py` runs them
as commands -- the composer in a real child process over a relocated copy of
the real source, the supervisor through `baseline.main` itself, which nothing
had executed before. The reviewer's reproduction is kept as a regression, and
the sharpest case is the packet bound to that byte-identical relocated copy:
every pinned digest verifies, and only `verify_imported_sources` catches it.

The document also overstated its own preflight, claiming it supplies a
route-handler list the helper's own docstring says it cannot produce. Its real
limits are now stated where they are relied on, and the artifact operands that
W236087 already selected and accepted are bound rather than blanked.

What could NOT be established is recorded as such: reusing the W236087 instance
is now possible, but its faulted attempt still holds an open assignment in that
Work's scope, and whether a new assignment is admitted alongside it needs that
deployment's stores opened. This claim did not open them, so the fresh isolated
instance is the recommendation and the caveat travels with the alternative.

Verification: 77 focused deterministic checks, 15.704004109s measured.

## 2026-09-22T16:50:58Z — independent review, claim 240287

Preparation accepted for the recommended fresh isolated instance only; exact
review: `review-2026-09-22T16-50-58Z.md`. This supersedes the original R1/R2
changes-requested state for that arrangement. 77 checks passed independently;
an additional real-main/real-compose probe retained an attributed proposal and
positive cleanup. Candidate hashes and all ten inherited preservation hashes
are bound in `review-evidence-240287.json`.

**The optional shared-store reuse interpretation above is not accepted and is
superseded by this boundary.** Admission is scoped, but recovery, runtime refresh
and existing endings are still forwarded by the proxy and swept store-wide.
New Job identity alone does not establish isolation from existing attempts.
Use fresh dedicated Authority/Job/control/integration stores, without another
concurrent worker/supervisor. Preserve W236087's old runtime separately. Shared
reuse would require its own selection and proof; it is not a new baseline gate.

The reviewer investigated step 5a leaving the canonical target unestablished.
Real composition still settled: retention in this implementation-only stage
does not exercise later publication. That hypothesis was disproved and is not
a baseline blocker. Exact probe results and the failed initial reviewer assertion
are preserved in the review evidence.

Owner provisioning/selections and a live run remain unperformed. Preparation
acceptance does not close W239528 or accept W239533/W236087. Actual proposal
bytes, execution stop and positive cleanup need independent acceptance after
any owner-selected run. Reviewer measured 17.603085144s this claim.

## 2026-09-22 -- OWNER: failure handling before credential renewal

Owner pass 242683, recorded here BEFORE implementation as that pass requires.

The owner ran the accepted bounded command on the fresh isolated instance. The
provider returned an OAuth authentication failure immediately. **The owner
selects failure handling before credential renewal, and the credentials are
left expired on purpose**: a deployment that only works when the token is valid
has not been shown to fail safely, and renewing first would have thrown away
the one set of real failure bytes this campaign has.

    "Owner selects failure handling before credential renewal. Leave
     credentials expired. Record this decision in FINDING/PLAN before
     implementation. Preserve /home/sl/baton-runs/single-implementation-239528/
     run, including outcome.json, provider logs and worker terminal events.
     Diagnose and correct unable-result settlement and cleanup. Use retained
     failure bytes in deterministic regressions through real manager/adapter
     boundaries. Require prompt actionable failure, stopped execution and
     positive cleanup, without a proposal or false success. Preserve
     successful-result coverage and prior evidence. Pass for independent
     review, then baton.decide with a bounded expired-credential failure-path
     command. No credential renewal, live rerun, destructive recovery,
     reviewer stage or resume in this correction."

The live run directory is preserved and was read only. Its evidence is
summarised in `DIAGNOSIS-242687.md`; nothing in it was modified, moved or
deleted, and no store belonging to it was opened.

### What the run showed

The provider failed in 31 ms -- `is_error: true`, `terminal_reason: api_error`,
`"Failed to authenticate: OAuth session expired and could not be refreshed"` --
and the adapter did exactly the right thing: it answered `ending: answered`,
`disposition: unable`, `fault_code: null`, with a real result manifest and no
proposal claim.

**The manager then sat in `answering` for the full 900-second bound and never
committed cleanup.** That is the defect, and it is a product defect rather than
a packet one: a deployment whose credentials expire takes fifteen minutes to
report a thirty-one-millisecond failure, and leaves the container behind.

### The cause, established

`review_driver.end_implementation` performs publication as an UNCONDITIONAL
step seven of nine. `integration.retain_proposal` refuses -- correctly, at its
own boundary -- when the frozen result's disposition is not `completed`:

    attempt '...' has no completed frozen result to propose

So steps one to six commit (quiesce, observe, freeze, correlate, intake
receipt, retention), step seven refuses durably, and steps eight and nine --
fencing the assignment and `authorize_cleanup` -- are never reached.
`_ending_owed` stays true, the stage projects `answering`, and every sweep
re-attempts `conclude` and records the same refusal until the bound elapses.
The manager's own deferral row names it exactly.

**This is not W236087's cleanup stall.** That one never reached
`authorize_cleanup` because a faulted turn froze and collected nothing, so no
intake receipt existed. Here the receipt DOES exist and every step up to
retention committed; the ending is blocked one step further on, at a
publication that cannot exist for a result with no candidate.

### The correction, and where it belongs

Publication is conditional on the result being `completed`. An `unable` or
`cancelled` implementation result has no candidate, so there is nothing to
retain, nothing to publish and nothing to read back on resume -- while the
assignment still has to be fenced and the runtime still has to be positively
cleaned up.

`review_driver` already states this rule for its own other ending: "The
`completed` disposition stays HERE because it is the review's own rule -- a
review that did not complete decided nothing -- rather than something every
ending owes." The implementation ending owes the same statement and did not
make it. The correction is that statement, applied consistently to the ordinary
ending and to both resume entries.

### What the correction measures, and what it cost

Same retained bytes, same real adapter, ending driver, composed stage and
cleanup journal: before, `stopped overall-bound-exceeded` at tick 901 with the
stage in `answering` and no committed cleanup; after, `stopped exceptional` at
tick 3 with `retained`/`absent` cleanup, nothing outstanding, `state: held`, no
proposal and no false success.

There were TWO defects, and the second was only visible once the first was
fixed. The second is in `stage_execution`: a non-completed contextual turn
returned `outcome: "held"`, which is the REVIEW vocabulary for "nobody may be
scheduled on this", and the composed stage read it as "the ending did not
finish" and returned before settling its obligation. Holding the provider
CONTEXT USE is right and is kept -- a generation whose turn cannot be accounted
for must never be finalized -- but it is not the same fact as the stage ending
being unfinished, and one answer was serving both.

Nine accepted cases in `tests/manager/test_claude_context.py` asserted the old
stage half through `assert_owed`. Their subject -- an unhealthy provider
terminal is not accepted and its context use never becomes `ready` -- is
unchanged and still asserted. `assert_owed` is kept for the endings that are
genuinely still owed. `DIAGNOSIS-242687.md` records this as the change most
worth a reviewer's attention.

Verification: 87 focused deterministic checks, 17.608050957s measured, plus the
product suites: `test_review_driver` 164/164, `test_claude_context` 81/81, and
`test_stage_execution` 424 with the same 12 pre-existing fixture errors that
predate this Work.

## 2026-09-22T23:53:34Z — independent review, claim 242852

`review-2026-09-22T23-53-34Z.md` accepts the product correction but supersedes
the command-prepared claim above: the command needs bounded corrections.
332 focused deterministic checks pass independently. Additional unable-ending
re-entry probes prove positive cleanup after one withheld cleanup and historical
replay without publication or another provider call. Changed context assertions
preserve failure/no-generation/no-repeat semantics while settling the stage.

Confirmed R1: OPERATOR-FAILURE's bound manager-source still contains both
PRODUCT-CHANGE **before** hashes. It would import the uncorrected logic. Prepare
a separately bound successor source containing the accepted bytes; preserve the
old source and test the actual bound failure packet deterministically.

Operational R2: the named SELECTIONS-FAILURE-242687.json cannot be read because
it does not exist. Deliver exact selections and bounds with fresh dedicated
stores. The prior review's exclusion of stores containing other work remains;
the first failed run's unfinished ending/cleanup is preserved outstanding work,
not a reusable empty instance. No recovery or credential renewal is authorized.

`review-evidence-242852.json` binds product/dossier hashes, independent tests,
the missing artifact and old source, with `review-replay-242852.py/.json` retaining
the extra probes. Original outcome matches the copy; ten inherited W236087 hashes
match. Reviewer measured 63.903260760s; no live execution or deployed-state change.
Return to baton.decide for bounded packet correction selection.

## 2026-09-23T00:06:24Z — successor packet accepted, claim 242948

`review-2026-09-23T00-06-24Z.md` supersedes the prior packet R1/R2 refusal for
the prepared successor artifact. The complete 106-file snapshot matches its
manifest and differs from the preserved tree only at the two accepted product
modules. Thirteen new checks pass. An independent child imports the actual
snapshot and runs baseline.main plus real composition over the expired-token
replay: held/exceptional, unable, positive cleanup, no proposal, one provider call.

**Preparation step 0 is already complete and must not be repeated.** The builder
currently deletes an existing destination before copying and verification; that
would replace the reviewed artifact. This operational finding is recorded here.
Acceptance binds the existing full-manifest snapshot, not a future rebuild.
The review explicitly supersedes the operator instruction to repeat step 0.

The selections file now exists with the requested 120/30 bounds and fresh dedicated
stores. For the linked Authority setup example, derive store/uuid/Work from the
new selections; do not use its older hard-coded 239528 store path. Old sources,
stores and unfinished cleanup remain preserved. Provisioning and live execution
are owner-side and unperformed. Credentials remain expired.

Evidence: `review-evidence-242948.json`, `review-tests-242948.log` and
`review-snapshot-242948.py/.json`. Reviewer measured 2.214450427s; previous
product/test acceptance is unchanged. Return to baton.decide, without closing
W239528 or treating expected-failure qualification as successful implementation.

## 2026-09-23 — owner executed bounded expired-credential run; review pending

Recorded by baton.prompt after owner reported completion and requested proceeding
to independent review. Run single-implementation-242687 finished at
2026-09-23T00:11:07.113Z; packet SHA256
076f75b21bfa48b69b229b76f7030c002c0a8a883dead031c8aebef2ffa357d1.
Copied outcome, packet, concrete selections, deployment, submission and original
provider stdout to live-failure-20260923T001107Z/ with source locators and SHA256
bindings in MANIFEST.json. No live store was opened or runtime changed by prompt.

Observed retained provider result: OAuth session expired and could not be
refreshed, is_error true, duration_ms 31. Outcome reports one implementation
admission, unable, held/exceptional, served_seconds 5.573039229988353, runtime
destroyed, cleanup retained/state absent, no outstanding cleanup or uncertainty,
and no proposal. Prompt inspected these files; independent live-evidence
acceptance remains pending. This supersedes the above unperformed-live status,
not the acceptance criteria or the historical reviews.

Owner selects independent review of this failure-path evidence next. Credentials
remain unchanged until acceptance; no renewal or further live execution selected
by this handoff. W239528 stays open for the successful implementation baseline.
W239533 and W236087 stay dependent. Earlier failed runtimes and consumed grants
remain separately outstanding; this outcome covers only its own Job.

## 2026-09-23T00:15:16Z — actual failure path accepted, claim 243014

Independent review `review-2026-09-23T00-15-16Z.md` accepts the retained actual
expired-credential run. All six manifest entries match originals and copies;
the real packet verifier and bound imports pass, with the accepted 106-file
snapshot. Original provider stdout reports OAuth expiration, one turn/31ms and
the same session as the outcome. The run reports unable/exceptional in
5.573039230s, destroyed runtime, positive retained/absent cleanup, no outstanding
cleanup, no proposal, no retry and no false success.

Independent engine inspection confirms the exact runtime does not exist.
Operational inspection limit: the supported ControlStore.open_readonly refused
with OperationalError wrapped in ContractRefusal. No write-capable fallback was
used. Durable cleanup and unable disposition are accepted from the validated
reviewed-supervisor outcome, not a new direct journal read. Full evidence and
limits are in `review-evidence-243014.json` and the review.

This supersedes the pending independent failure-path acceptance above, not the
successful-implementation requirement. W239528 stays open; W239533/W236087 stay
separate/dependent. Return to baton.decide. No renewal, rerun, recovery or closure
was performed or selected, and prior failed instances remain separately outstanding.

## 2026-09-23 — owner selects fresh successful-baseline preparation

Recorded by baton.prompt: owner reports default Claude login renewed, usage
reset and a successful ping, then selects proceeding. This is owner-reported
provider availability, not evidence of the managed baseline succeeding.
Prepare a new dedicated instance and run identity
single-implementation-success-239528 under /home/sl/baton-runs/.
Reuse the accepted corrected 106-file manager snapshot at
/home/sl/baton-runs/single-implementation-242687/manager-source, the accepted
worker image, and fixture base 842ec458b7c3e270aaa34d126f7f0deecb08ccd0.
Use the original successful-baseline bounds (180-second provider turn,
900-second total, 60-second cleanup, one implementation invocation, no retry).
The 120/30 bounds were specific to the expected-failure qualification.
Preserve all consumed packets, stores, evidence and outstanding old resources.
No review container, correction or resume is added to this Job. Prepare concrete
bindings before the owner launches; independently review actual proposal,
attribution, stopped execution and positive cleanup before closing W239528.
This supersedes awaiting next owner selection, not prior evidence or review limits.

## 2026-09-23 -- the successful baseline run, and three findings

Owner pass 243171, recorded here BEFORE implementation as that pass requires.
`/home/sl/baton-runs/single-implementation-success-239528/run` is preserved and
was read only; no store belonging to it was opened. Copies of its outcome,
task, submission, context profile, provider and verification logs and a
recorded inventory of its context-home modes are in `live-success-243174/`.

### The result that matters, and it is good news

**The real provider followed the adapter's edit-only contract.** Five turns,
18.3 seconds, `is_error: false`, `terminal_reason: completed`, and its own
account:

> "`harness.py` now contains a single line, `print('READY')`... Exit code is 0.
> The change is left uncommitted in the working tree (`git status` shows
> ` M harness.py`); nothing else was touched."

The verification log reads `READY`. The retained outcome carries one proposal
attributed to `Baton worker <worker@baton.invalid>`, authored and committed by
the adapter, with exactly the declared base `842ec458...` as its single parent.
Runtime destroyed, cleanup `retained` with the engine's own absence sentence,
`outstanding_cleanup: []`.

That answers `PROVIDER-QUESTION-239528.md`'s first half: given
implementation-only requirements and an explicit instruction not to move HEAD,
this provider edited and did not commit. One run is one sample, and it is the
sample that was missing.

### Finding 1 -- the custody failure, established

`context_use` was held with reason `custody-invalid`, so the generation was
never sealed -- the context storage has no `generations/` directory at all.

**The cause is directory MODES inside the private context home.**
`context_delivery._private` refuses any custody directory whose mode carries
group or other bits:

    if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077 ...
        refuse("protected custody owner or mode changed")

Running the product's own `_state` measurement over the preserved home, with
the profile's `{conversation_id}` resolved, reproduces it exactly:

    snapshot=False  REFUSED -> protected custody owner or mode changed

**Seven directories the real CLI created carry `0o755`**: `.claude/backups`,
`.claude/projects`, `.claude/session-env`,
`.claude/session-env/<conversation>`, `.claude/shell-snapshots`,
`.claude/projects/-output` and `.claude/projects/-output/memory`. The CLI
created them with the ordinary process umask. `.claude` itself and
`.claude/sessions` are `0o700`, and the state file and the credential symlink
are exactly as the profile requires -- so nothing is wrong with the state; it
is the directories on the way to it.

**Why no deterministic test caught this.** The fixture's fake provider does

    for parent in (state.parent, state.parent.parent): parent.chmod(0o700)

-- it compensates for precisely this behaviour, which is why the harness has
always passed. And the compensation would not have been enough anyway: the
real CLI creates `memory/`, `session-env/`, `shell-snapshots/` and `backups/`,
which are not those two parents.

This is a real product/deployment gap. **It is diagnosed here and not fixed
here**: owner pass 243171 asks for the diagnosis and for the non-progressing
wait, and deciding whether the manager should tolerate a umask-created
directory, or the delivery should impose the mode, is a product decision with
its own security reasoning. It is recorded as the next selection.

### Finding 2 -- a terminal non-progressing condition still waits for the bound

Once the context use is held, `stage_execution`'s composed conclude returns
`outcome: "held"` with `provider-context-unproved` and never reaches
`settle_ending`, so the registered ending obligation stays owed and the stage
projects `answering` forever -- exactly the shape corrected under claim 242687
for the `unable` disposition, one branch over. Claim 242687 deliberately left
this branch alone; this run is the case that shows the same conflation reaches
a COMPLETED turn whose proposal was produced, published and cleaned up.

**Nothing can change after that point.** The runtime is destroyed, the cleanup
is committed, the proposal is retained, and the context hold is durable. The
supervisor nevertheless kept sweeping, and the owner interrupted it at 443
seconds of a 900-second bound.

The supervisor is where this Job can act: a run whose canonical state stops
changing while its stage cannot advance must stop and say so, rather than
spending its whole bound discovering that nothing is happening. A shorter
justified default bound is the backstop, not the mechanism.

### Finding 3 -- the interruption was reported as a traceback

**The outcome WAS retained.** `outcome.json` exists, written at 18:34 for a run
that began at 18:26, and it is complete and internally consistent: `stopped:
interrupted`, `interrupted: "KeyboardInterrupt: signal 2"`, the attribution,
the cleanup and `final_canonical_read: true`. This is read from the file rather
than inferred from the exception, as the owner asked.

What the operator saw was an uncaught `SupervisorInterrupted` traceback out of
`main`. `supervise` deliberately raises it after retaining the outcome -- an
operator who pressed Ctrl-C is owed both the outcome and the process exiting --
but `main` never catches it, so the one thing the operator needed, the path of
the retained outcome, was the one thing not printed.

## 2026-09-23T00:50:59Z — independent review, claim 243244

Read `review-2026-09-23T00-50-59Z.md`. Custody-mode refusal and the retained completed proposal are
independently corroborated; the selected correction is not accepted yet.
R1: the new progress read swallows serving-time interrupts; actual-composition
SIGINT probe permits a provider turn afterward, and direct KeyboardInterrupt
can be lost into settled success. R2: rebuilding into a fresh snapshot still
overwrites the fixed historical manifest. R3: the shorter baseline backstop and
successor command/packet selected by owner pass 243171 are missing.
These findings supersede correction-complete/readiness claims for scheduling,
while preserving the historical diagnosis and implementation account.
112 focused tests pass; counterexamples and hashes are retained in review evidence.
Return baton.decide for bounded correction selection. No live run or recovery.

## 2026-09-23T01:02:06Z — independent review, claim 243325

Read `review-2026-09-23T01-02-06Z.md`. R1 accepted: actual SIGINT and direct KeyboardInterrupt
probes now stop before any further provider turn and retain interruption.
121 tests pass. R2 snapshot/manifest preservation is accepted, but CLI successor
creation still records old claim 242906. R3 shorter 300/60 backstop and explicit
custody warning are accepted; BASE is undefined, linked step 5a still names the
old store, and the actual successor selection lacks entrypoint verification.
These narrow remaining corrections supersede the all-corrections-complete
scheduling claim. Preserve historical packets; return baton.decide. No live run.

## 2026-09-23T02:58:25Z — R2/R3 accepted, claim 244032

Read `review-2026-09-23T02-58-25Z.md`. Successor creation provenance now travels through the CLI;
predecessor manifest remains unchanged. BASE and successor-specific preparation
are explicit, actual selections compose through the documented entrypoint, and
an independent disposable Authority probe validates step 5a and canonical base.
36 focused checks plus the preparation probe pass (2.278290415s measured).
This supersedes the prior remaining-R2/R3 corrections-requested state.
R1 remains accepted at unchanged bytes. Custody mode decision remains open;
no successful-baseline readiness, live execution, recovery or closure follows.
Return baton.decide.

## 2026-09-23 -- OWNER: the custody mode is fixed at creation, not at the check

Owner reroute 244096, recorded here BEFORE implementation as it requires:

    "Owner selects the remaining custody-mode correction. Record the decision
     before implementation: preserve private-context ownership, mode and
     symlink checks; make the provider execution/delivery path create
     compliant private directories. Establish whether restrictive creation
     permissions solve the observed CLI behavior; do not assume or
     blanket-chmod retained evidence. Reproduce the real directory layout
     deterministically without fixture-only permission repairs, preserving
     negative custody coverage. Keep scope within the separate implementation
     baseline."

**The manager's checks are not weakened.** `context_delivery._private` keeps
refusing any custody directory whose owner differs or whose mode carries group
or other bits, `_state` keeps refusing a link or special file, and the
credential slot keeps having to be exactly the expected symlink. The defect was
never that the check was wrong; it was that the deployment handed the provider
a process that creates world-readable directories and then asked the manager to
accept them.

### What the evidence shows

Seven directories under the live context home carry `0o755` --
`.claude/backups`, `projects`, `session-env`, `session-env/<conversation>`,
`shell-snapshots`, `projects/-output` and `projects/-output/memory`. Two carry
`0o700`: `.claude` and `.claude/sessions`. `0o755` is exactly `0o777 & ~0o022`,
the ordinary umask default; the two private ones are the CLI asking for
something stricter. Nothing in the evidence is a directory that could only be
`0o755` through an explicit `chmod`.

### What was ESTABLISHED, not assumed

`subprocess.run(..., umask=0o077)` was exercised against a real child under
this interpreter (3.13.7):

    0o700  dir   a          (os.makedirs)
    0o700  dir   a/b
    0o700  dir   a/b/c
    0o700  dir   d          (os.mkdir with an EXPLICIT 0o755)
    0o600  file  f

`mkdir` masks its mode argument, so a child under `umask 0o077` cannot create a
group- or other-readable directory **even when it asks for one**, and the mask
is inherited by its descendants. The `umask` operand exists on `Popen` from
Python 3.9 and is applied in the child after fork without `preexec_fn`, which
matters here because the provider spawn already runs beside a reader thread and
`preexec_fn` is not thread-safe.

**The one residual risk, stated rather than hidden**: a provider that
explicitly `chmod`s a directory permissive AFTER creating it would defeat a
umask, because `chmod` is not masked. The retained evidence does not show that
-- every non-private mode is exactly the umask default -- and the manager's
unchanged check would refuse it, which is the right outcome and would be a
separate finding. This correction is therefore necessary, sufficient for the
behaviour actually observed, and honest about what it does not cover.

### Where it goes, and where it deliberately does not

**Only the provider child.** A umask set at worker entry would also apply to
everything the adapter writes into the shared private line, whose group-based
access the deployment configures on purpose; narrowing that would be a
different change with different consequences. The provider is the only party
that creates the context home's directories, so it is the only party whose
creation mask moves.

### What the retained evidence is NOT

Nothing chmods `/home/sl/baton-runs/single-implementation-success-239528/`. The
owner said not to blanket-chmod retained evidence and that is a record of what
a real run produced; repairing it would destroy the only proof of the
behaviour this correction addresses.

### And the fixture stops compensating

`tests/manager/test_claude_context.py`'s fake provider has always chmodded its
two state parents to `0o700` -- the "fixture-only permission repair" that is
exactly why no deterministic test ever saw this. With the creation mask
corrected, the repair is unnecessary and is removed, so the fixture's child
creates its directories the way a real one does and the adapter's umask is what
makes them compliant. `ACustodyModeTheRealProviderProduces` is preserved
unchanged as the negative coverage: a home that is NOT compliant must still be
refused.

## 2026-09-23T03:19:21Z — custody source accepted, claim 244167

Read `review-2026-09-23T03-19-21Z.md`. Provider-child umask077 correction and bounded test
changes accepted; custody checks remain unchanged. 325 focused checks plus
022/077 composition and full14-entry creation probes pass (62.334816458s).
This establishes deterministic creation behavior, not actual CLI behavior under
a corrected image. Later chmod/resetting umask remains refused by custody.
The current packet still binds the old adapter; successor image/artifact and
packet preparation remain outstanding. No live run or successful baseline proof.
The exact context-test before/after chain supersedes stale all-three-earlier-paths
unchanged shorthand in PRODUCT-CHANGE/OWNERSHIP. Return baton.decide.

## 2026-09-23 -- OWNER: build the corrected worker image, bind it, prepare the packet

Owner reroute 244214, recorded here BEFORE execution as it requires:

    "Owner selects corrected worker-image build and successor packet
     preparation using source accepted in review-2026-09-23T03-19-21Z.md.
     Record selection before execution. Preserve existing images, consumed
     instances and evidence; build a distinct image, verify accepted adapter
     bytes, bind actual image and worker digests, and provide exact bounded
     commands retaining 180/300/60 limits. Coordinate with tuner W244180
     without overlapping files."

### What is selected

A DISTINCT image, `baton-v12-claude-worker:w239528-244216`, built from the accepted source. The existing
`baton-v12-claude-worker:w236087-236349` at `sha256:2e9e84ff23319778760d5b22c70d543d4290931510a3ab3ecf40bcdaad7456bd` is PRESERVED and is not retagged,
rebuilt or removed: it is what every earlier packet in this campaign is bound
to, and W236087's own packet still names it.

The adapter bytes that must be in it are the ones independent review accepted
at 2026-09-23T03:19:21Z: `v12/worker/claude_agent.py`
`18c34ff52faa150237df0c8d0206b805801ee71cb9e7a4ec6e84e4379d7f9d8d`, carrying `PROVIDER_UMASK = 0o077`. The build VERIFIES that
digest inside the built artefact rather than trusting the build context, for
the reason the recipe already gives about itself: "a recipe naming a suite and
an image carrying an interpreter are two facts and only the second one runs."

### What the image does and does not settle

It makes a live run POSSIBLE on the corrected adapter. It does not make one
authorized, and it does not establish the CLI's behaviour under the new mask --
review 2026-09-23T03:19:21Z is explicit that the retained `0o755` modes are
consistent with umask creation but do not exclude an explicit `chmod` or a
reset mask, and only a real turn under this image can answer that. The packet
says so.

### Coordination with W244180

The tuner's Work is bound to `work/records/2026/09/finding-v12-review-job-
preparation/` and is preparing the operator recipe for the REVIEWER Job
W239533. It was `active` and working when this claim began. There is no file
overlap: that dossier is its own, this one is W239528's, and the product paths
below are pinned here. Nothing in this claim touches its dossier or W239533.

### The recipe is not reproducible, and that is measured rather than assumed

`Dockerfile.claude` records it: two builds of an unchanged tree produced
different digests, identical in the base and `COPY` layers and differing only
in `npm install` and `apt-get install`, because the `FROM` is a tag, apt takes
what the mirror serves and the pinned provider runs a `postinstall` that
fetches a native binary. So the ARTEFACT is selected by digest, not by recipe,
and the packet binds the digest this build actually produced.

## 2026-09-23T03:30:58Z — image metadata corroborated; preparation correction needed

Review claim244257: `review-2026-09-23T03-30-58Z.md`. Both image config digests and four selected
worker hashes agree with artifact evidence; source acceptance remains unchanged.
R1: new recipe references step5a that hard-codes243284 SEL and store assertion;
selecting244216 still fails before Authority.open. Provide and test the actual
new preparation without changing consumed artifacts. Eight binding checks pass.
Independent inside-image inspection was denied Docker API access; no stronger
retry/fallback used. Exact limit recorded in review-evidence-244257.json.
This supersedes operator-preparation-complete status, not source acceptance.
Return baton.decide; no live execution, provisioning, recovery or closure.


## 2026-09-23T03:42:19.949762+00:00 — independent preparation review, claim244326

Changes requested: review-2026-09-23T03-42-19Z.md. Parameterized helper resolves the predecessor hardcoding, but the documented command lacks the bound-source import path and fails before Authority.open; known consumed run names bypass freshness refusal when equal to run_id. Reproduced through disposable supported interfaces and pure selection checks. Fifteen tests pass but omit main and do not connect preparation to composition. Evidence review-checks-244326.json. Prior source/image acceptance and execution exclusions retained.


## 2026-09-23T03:57:30.927689+00:00 — preparation corrections independently accepted

Reviewer baton.rvpc claim244441: review-2026-09-23T03-57-30Z.md. R1 bound-source command and R2 consumed-identity/path checks are resolved, superseding their outstanding status in review-2026-09-23T03-42-19Z.md. Twenty-three focused tests pass and separate selected-interpreter/snapshot preparation, replay and subsequent composition of the exact same disposable selections succeed. Five product hashes unchanged. Evidence review-checks-244441.json; measured0.658085888s. Owner next-action selection remains; no live custody/proposal/cleanup success or Work closure is claimed. Prior image-inspection limitation retained.


## 2026-09-23 — owner live baseline settled; independent acceptance pending

baton.prompt records Slawomir's completed execution of single-implementation-244216.
The retained outcome reports settled/completed in 13.813865043 seconds, one
implementation admission, no retry, no holds, no uncertainty and no outstanding
cleanup. Exact runtime 4e6a605a2c9f3f039635bd9b06407788addde49767f8df03cf501b3676d49623
is reported destroyed with retained positive absence evidence. Proposal head
f84ae35d2ce87c97a88cb5fc9787c93afa91adc6 has sole parent
cee07eebada62102e4a9ec9b88b4b804a102ce7e and Baton worker attribution.

Original packet and outcome are copied verbatim into live-success-244216/ with
a SHA256 manifest and original locator. This records supervisor evidence, not
an independent re-observation of runtime, context custody or proposal validity.
Owner requests proceeding to independent acceptance. Reviewer should inspect
retained provider/result/proposal and context evidence via supported read-only
interfaces, verify exact runtime cleanup where permitted, and state any access
limits. No rerun, recovery, review-stage execution or resume is selected.
W239528 remains open pending acceptance; W239533 remains its dependent.


## 2026-09-23T04:15:56.273324+00:00 — live baseline independently accepted, claim244558

review-2026-09-23T04-15-56Z.md accepts the narrow single-implementation-244216 proof. Original/copied manifest matches, attributed single-parent proposal and bundle verified; only harness.py changes to READY. Sealed context manifest and private modes independently checked. Exact Docker runtime independently absent. Ledger state remains retained supervisor evidence; no store opened. Pending independent acceptance above is superseded. Observed diagnostic discrepancy: result provider.seconds_bound retains default3600 despite selected180 and actual bound-resolution path; no timeout exercise inferred from this short success. Preserve for bounded follow-up. Return owner for disposition, no closure/reviewer stage/resume.
