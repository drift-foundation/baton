# Independent managed review of a retained proposal

## 2026-09-22 — owner selects separate review Job

Work: W239533. This is the second Job in the owner-selected split of W236087.
W239528 establishes one implementation through valid proposal and cleanup;
this Job consumes that accepted immutable proposal in a separate reviewer run.
W236087 retains the later resume/correction proof. Separate Work, execution
identity and evidence are required; these are not stages of one enlarged run.

Acceptance: the real manager supplies review-specific criteria and the actual
retained proposal to an independent reviewer; a valid attributed verdict is
collected; execution stops and positive cleanup is recorded. The reviewer
judges actual bytes, with no fabricated verdict and no implementation performed
inside its review turn. The criteria may require a correction, but applying it
and restoring the implementation conversation belong to W236087.

No initial implementation, resume or correction execution here. Prepare focused
deterministic real-boundary coverage first and identify any real-provider question
before selecting a bounded live command. No live execution, destructive recovery,
or reuse of W236087's failed consumed grant is authorized by creation.

## 2026-09-23 -- the prerequisite is satisfied, and what it settled

W239528's live baseline was independently accepted by
[review-2026-09-23T04-15-56Z.md](../finding-v12-single-implementation-proof/review-2026-09-23T04-15-56Z.md)
(reviewer claim 244558, owner execution claim 244464), which accepts "the
narrow successful implementation/proposal/custody/stopped-runtime/positive-
cleanup baseline". PLAN step 1 is therefore done. It was accepted on the
COMBINED retained and independent evidence that review names, and this Job
should carry its limits forward rather than round them off:

  * No Authority, Job or Control SQLite store was opened by that reviewer, so
    ledger completion and publication state remain the retained supervisor's
    account. The line state this Job attaches to is read directly here, and
    `PROGRESS.md` records what was read and how.
  * The reviewer recorded a metadata discrepancy it explicitly did not treat
    as proof of a 3600-second invocation: `proposal/result.json`'s
    `provider.seconds_bound` is 3600 while `outcome.provider_turn` reports the
    selected 180. It is a retained diagnostic for a bounded follow-up, not an
    input to this Job's bounds.
  * That run was 7.485 provider seconds and exercised no timeout enforcement.

WHAT THE SUBJECT ACTUALLY IS. Read read-only from the accepted run's own
control store under this claim: v12 Authority `7ea319da93384b77bc3ddea38602d7a3`,
v12 Work `7ea319da-W1`, line
`line-0d5b62ba32f714e3dd0a8bb8a2c88ed1622ad5cf1dbf5db1d3bd40e0af044c8d` in
state `review-ready` at revision 1, current checkpoint
`checkpoint-ab8207baa93b5abc12393a67c1e04046e14bebd7e9defdf0940e168203b711a9`,
`frozen`, digest `sha256:9d3aa3ca7733d4ec983b5841f1b99be09e4dc98bdb45c8b255890772acdd9324`,
base `cee07eeb`, head `f84ae35d`, tree `5b4c0f45`, one changed path
(`harness.py`). Its producer is writer
`writer-a67688eb...`, worker `implementation-worker`, participant `baton.impl`,
principal `principal:baton.impl`, now `revoked` with reason `checkpoint`. The
line holds NO review attachment. The proposal is attachable and nobody has
reviewed it.

## 2026-09-23 -- G2 is answered: the separate Job recovers the line

W244180's preparation left the cross-Job binding open, and rightly: "A
brand-new unrelated line has no accepted producer checkpoint; copying the
proposal file or supplying a new Work ID does not create that provenance."

The supported arrangement is that the reviewer Job brings its OWN Job store,
submission, stage, attempt, criteria and outcome, and RECOVERS the producer's
line rather than creating one. `create_line` derives `line_id` from
`(authority_uuid, work_id)` alone and replays its committed creation when the
row is already there; `StageDeployment.line_for` calls it with the deployment's
Authority and the binding's `job_work_id` on every tick, so a second deployment
naming the same v12 Authority and Work reaches the same line and
`StageComposition._prepare` takes its current checkpoint. No row is copied, no
writer or checkpoint is manufactured, and no validator is weakened.

FOUR THINGS ARE NECESSARILY SHARED, and the reason is the product's, not a
convenience: the v12 Authority and Work (they ARE the line's identity), the
control store (the line, writer, checkpoint and attachment are rows in it), and
the workspace storage and nominated source (`create_line` recomputes
`line_path` from the control store's own configured storage and refuses an
`operation-collision` on any difference, then `_validate_line_object` re-proves
device and inode -- so a copy of the retained tree at another path is NOT
available, and running the review against a copy is not proposed).

THE SEPARATION IS REAL AND IT IS ELSEWHERE. The distinct v11 Work, claim,
dossier and evidence are preserved; so are the Job store, Job identity,
submission, stage, attempt, generation, criteria, launch home, credential home,
private-context storage, deployment state and outcome. Independence is decided
by `attach_review` on worker, participant and principal, and the producer's
three (`implementation-worker` / `baton.impl` / `principal:baton.impl`) differ
from the reviewer's (`review-worker` / `baton.review` /
`principal:baton.review`) on all three.

THE COST OF THAT ARRANGEMENT, STATED PLAINLY: the review appends its rows to
W239528's retained control store and its boundary under W239528's workspace
storage. It does not rewrite the producer's artifacts, and it cannot -- but
"separate execution" here means separate Job and evidence, not a separate
filesystem root, and a reader should not be left to infer otherwise.


## 2026-09-23T04:40:30.612117+00:00 — independent review of partial delivery, claim244729

Changes requested in review-2026-09-23T04-40-30Z.md. Direct sqlite3/SELECT attachment survey is not an authorized supported coordination interface. Existing ControlStore.open_readonly and snapshot are present in the selected source; use supported readers and record exact missing interfaces rather than bypassing them. This supersedes G2 fully-answered/DONE claims as accepted readiness, without removing historical observations or companion-file disclosure. Supervisor, validated packet write, operator commands and provider question remain undelivered. No helper/tests or deployed stores executed by reviewer. Return owner for correction/completion.

## 2026-09-23 -- the survey reads through supported interfaces (R1)

Review 2026-09-23T04:40:30Z refused the first `attachment.py` as a P1 and was
right. It opened the control store with `sqlite3.connect` and issued its own
`SELECT`s against `review_lines`, `line_checkpoints`, `line_writers` and
`review_attachments`. AGENTS.md does not qualify the rule: "Never read it
directly either: if a question about the coordination state can only be
answered by opening the store, that inability is the finding." `mode=ro` does
not exempt raw SQL from it.

The premise I built it on was true but incomplete. `ControlStore.open` can
initialize or migrate -- but `ControlStore.open_readonly` already existed, in
the current tree and in the selected `manager-source-242687` snapshot, and it
recognizes the schema and refuses an empty or unsupported store WITHOUT
migrating it. I did not look for it, and a correct premise led to a wrong
conclusion because of what I did not check.

WHAT THE SUPPORTED VERSION READS: `ControlStore.open_readonly`, one
`snapshot()` spanning the whole account, and `line_of`, `checkpoint_of` and
`writer_of`. The reviewer's second point was also right -- separate reads with
no explicit snapshot are not a coherent line/checkpoint/writer account, and
sequential test cases do not demonstrate one. The snapshot is now measured
rather than asserted.

THREE PUBLIC LOOKUPS DO NOT EXIST, and `attachment.GAPS` records each with the
supported alternative used in its place rather than routing around it:

  * No public function answers "the line for this Authority and Work" without
    creating one. So the packet NAMES `line_id` and `line_of` PROVES that line
    carries the expected Authority and Work. An operator reads the identity
    from the producer's retained `outcome.json`, which is a file.
  * No public reader lists a line's checkpoints. `checkpoint_of` answers one
    checkpoint's own line and revision, which is exactly what separates a
    superseded revision of this line from a checkpoint of another line. The
    listing was never needed for the decision.
  * No public reader lists a line's writers or attachments. `line_of` answers
    the state, and `review-ready` / `writing` / `reviewing` is the signal the
    validator itself acts on.

THE DISCLOSED PRODUCER ARTIFACTS ARE PRESERVED. The earlier raw-SQL survey
created `control.sqlite3-shm` and a zero-length `control.sqlite3-wal` beside
W239528's retained control store. They are still there, still disclosed, and
were not cleaned up or relabelled. `open_readonly`'s own docstring records the
same SQLite-owned behaviour, so using the supported opener does not make that
read retrospectively clean -- it makes the next one supported.


## 2026-09-23T04:50:12.450058+00:00 — supported survey correction accepted, claim244799

review-2026-09-23T04-50-12Z.md resolves original R1 for attachment.py/review_bindings.py: supported readonly reader and coherent snapshot. Remaining test follow-up: foreign attempt Work is still changed through raw SQL; construct it through supported admission instead.36 focused tests pass,2 direct-SQL cases explicitly excluded; evidence review-evidence-244799.json. R2 supervisor/validated executable packet/commands/provider question remains undelivered. No deployed access. Return owner for completion; no readiness claim.

## 2026-09-23 -- the R2 question the owner has to answer

W239533's remaining scope is a bounded review-only supervisor. Three claims
have now recorded it as outstanding, and the reason is not that it is merely
large. It is that there is no seam to build it on, and the only two ways to
get one are a decision this Job cannot take by itself.

WHAT WAS MEASURED, under claim 244877, reading W239528's accepted `baseline.py`
rather than guessing about it:

  * `AdmissionGate` is ALREADY kind-agnostic. It is constructed with
    `caps={kind: count}` and a `job_id`, and refuses by reading `self._caps`.
    A review Job passes `caps={"review": 1}` and nothing else changes. Its
    module-level `KINDS` constant is referenced nowhere but its own definition.
  * `Termination`, `_guarded`, `_attempts_of`, `_terminal`, `_observation`,
    `_cleanups`, `_refresh`, `_cancel_active`, `_runtime_facts`, `_origin`,
    `_publish`, `_turn_ceiling` and `survey` are all kind-agnostic too.
  * `_supervise` IS NOT. It is one ~400-line function that reads
    `bounds["implementer_invocations"]` directly, builds the caps dictionary
    inline, and calls `_workload_evidence`, which gathers proposals,
    attributions and provider-context evidence -- the implementation-shaped
    half. There is no parameter, no hook and no subclass point for a different
    stage kind or a different evidence shape.

SO THE REVIEW SUPERVISOR IS EITHER:

  (a) A DERIVED COPY of `baseline.py`, about 2000 lines, of which perhaps 60
      differ: the caps key, the bounds member, the outcome vocabulary, and
      `_workload_evidence` replaced by verdict collection through
      `review_driver.review_verdict_from_result`. Every ending, interruption
      and cleanup path in the copy then has to be driven deterministically
      again, because a copy nobody drove is not evidence.

  (b) A BOUNDED REFACTOR of `baseline.py` to expose the seam -- caps and
      workload evidence as operands -- after which this dossier's supervisor
      is a few hundred lines that IMPORT the accepted machinery, and W239528's
      own tests keep proving it.

(b) is better engineering and it is what "reuse accepted components" points
at. It also EDITS A FILE THIS JOB DOES NOT OWN: `baseline.py` belongs to
W239528, which is now canonically closed satisfying, and the owner's split
ruling deliberately separated the two dossiers so that neither Job's proof
moved when the other changed. Taking that decision quietly inside W239533
would be exactly the boundary violation the split exists to prevent.

THE QUESTION, in one line: may W239533 refactor W239528's accepted
`baseline.py` to expose a stage-kind and workload-evidence seam, or must it
carry a derived copy? Absent an answer this implementer will proceed with (a),
because it is the option that needs nobody's permission -- but it is the worse
one, and it should be chosen rather than defaulted into.


## 2026-09-23T05:08:49.176511+00:00 — fixture acceptance and R2 alternative, claim244917

review-2026-09-23T05-08-49Z.md accepts both supported-fixture corrections:38 tests pass, no skips,0.596305013s. R2 remains unfinished. Supersedes the preceding claim that only a full2000-line copy or editing the closed baseline can proceed: baseline._supervise is381 lines and a local review orchestration can import its kind-agnostic helpers without changing producer bytes. Reviewer recommends that bounded local specialization; no cross-dossier edit authorized. Evidence review-evidence-244917.json. Owner disposition next; no executable readiness or live authorization.

## 2026-09-23 -- the local specialization, and my framing was too narrow

Review 2026-09-23T05:08:49Z proposed a third option and owner reroute 247154
selected it. It is better than either of the two I named, and the record should
say why my framing was wrong rather than quietly adopting the better answer.

I presented the choice as a ~2000-line derived copy or a refactor of a closed
Work's accepted file. Both premises were measured and both were true; the
inference was not. Because `baseline._supervise` exposes no seam, I concluded
that the whole of `baseline.py` had to move -- but only the ORCHESTRATION BODY
is implementation-shaped. `Termination`, `AdmissionGate`, `survey`, `_guarded`,
`_attempts_of`, `_refresh`, `_terminal`, `_observation`, `_cleanups`,
`_cancel_active`, `_origin`, `_publish`, `_turn_ceiling`,
`verify_imported_sources`, `verify_worker_image` and `_compose` are all
importable as they stand, and I had already measured that they were
kind-agnostic. A local specialization imports every one of them and writes only
what a review differs in. I had the measurement and drew the wrong conclusion
from it.

WHAT `review_supervisor.py` IS: the orchestration body, `review`-shaped; a
packet validator for this Job's schema, bounds and subject; and
`_verdict_evidence` in place of `_workload_evidence`. Everything else is
W239528's accepted bytes, bound by digest
`f27f3cd766f9271c4b3eddb6c657bca4770d18c11a74f377e717bef23df18fd5` and refused
before anything opens if the imported file is not those bytes. No global of
`baseline` is assigned and no attribute of it replaced; that is held by parsing
this program rather than by asserting it.

## 2026-09-23 -- what "no correction on changes-requested" actually means

The phrase is broader than the thing that can honestly be promised, and the
packet says so. `StageComposition.routed` opens the next round in the Job store
itself when a verdict answers `correction`. That is the ACCEPTED COMPOSITION'S
OWN ACT, and a supervisor that suppressed it would be weakening the composition
to make its own report tidier -- which is the shape review
2026-09-23T05:08:49Z explicitly refused in advance.

So the guarantee is narrower and exact: the admission gate's only cap is
`review`, so no correction CONTAINER can start; and the outcome reports the
opened ROUND as a fact, under `correction_rounds_opened`, because the Job store
really does hold one and it belongs to W236087's separately selected
correction. `correction_containers_started` is the outcome's own statement that
none started, and a non-empty one holds the run.

All three dispositions are successful reviews. The shortfall is a run that
produced no attributed verdict at all, which is why `_verdict_evidence` reads
the reviewer's FROZEN OUTPUT rather than a process exit status.


## 2026-09-23T11:30:47.221561+00:00 — executable preparation refused, claim247222

review-2026-09-23T11-30-47Z.md records reproduced startup self-identity refusal, invalid operator clock, and valid verdict read under the wrong field name.64 tests pass but none executes supervise/_supervise. Failure-publication and cleanup-reserve paths require actual orchestration proof. Permitting correction rounds narrows selected scope without owner selection and remains proposed, not accepted. This explicitly supersedes R2-complete/awaiting-live readiness and the preceding no-correction reinterpretation as authority. Earlier attachment/fixture acceptance retained. Evidence review-checks-247222.json; measured1.152729417s. No deployed access or live execution.

## 2026-09-23 -- four defects, and what each one says about the testing

Review 2026-09-23T11:30:47Z found four, and they are worth recording together
because three of them share one cause: the delivered suite tested what the
programs REFUSE and never once drove what they DO.

**R1, and it is the one that mattered most: the supervisor refused its own
packet.** `main` called the imported `verify_imported_sources(packet)` without
`program=`. That function is defined in `baseline.py` and defaults the running
program to its own `__file__`, so a packet correctly naming
`review_supervisor.py` failed with "this process is running .../baseline.py
and the packet binds .../review_supervisor.py" -- exit 2, before the engine or
any store. A default that is right for the module a function is DEFINED in is
wrong for every module that IMPORTS it, and the specialization's whole premise
is importing. The composer-to-`held_packet` test stopped one call short of it.

The same review found the operator page's step 1 passing `clock=lambda: "now"`
to `open_readonly`; the public instant grammar rejects that string, so the
documented survey could not run as printed. `attachment.now()` now exports the
formula and a case runs that exact block.

**R2: every successful verdict was classified as invalid.**
`review_verdict_from_result` returns `verdict`, `result_id` and
`result_digest`; the collector read `disposition` and `verdict_id`, which it
does not answer, so a valid `accepted` became `None` and produced a shortfall.
The attachment reader supplies `assignment_generation`, not `generation`, so
the outcome recorded null. THIS COULD ONLY EVER HAVE BEEN FOUND BY A TEST THAT
EXERCISED THE SUCCESS PATH, and there was none: the delivered cases covered
missing verdicts, wrong checkpoints and foreign kinds, and every one of them
passed with the collector reading members that do not exist.

**R3: the orchestration was never driven.** Importing tested helpers does not
verify the 381 lines that ORDER them. Driving it found three real defects:
the submission and the turn-ceiling read sat OUTSIDE the publishing region, so
a colliding Job identity escaped with nothing on disk; the cleanup window's
progress read was unguarded and could do the same; and serving ran for the
whole `total_seconds` and THEN opened a further `cleanup_seconds`, so a packet
declaring 300 with 60 reserved could spend 360 -- "reserved" does not mean
that.

**R4 is a different kind of finding and the review was right to separate it.**
The previous claim narrowed the selected no-correction contract by prose:
it let `StageComposition.routed` open a correction round, asserted the round
"belongs to W236087", and guaranteed only that no container starts. No
accepted implementation supplies the authority to assign a round in W239533's
Job store to another Work. THE CONTRACT IS RESTORED AND THE LIMITATION IS
REPORTED: `routed` calls `open_correction` unconditionally and the composed
deployment exposes no operand that declines it, so preventing the round needs
a change in the owning implementation scope. This run therefore HOLDS when one
appears rather than redefining its scope, and `correction_rounds_opened` is
read from the Job store's own stage records instead of from attempt kinds --
the previous derivation reported nothing at all for a round opened and never
allocated an attempt, which is the exact shape a `changes-requested` ending
leaves behind.

Whether to accept a held outcome for that reason, or to select the product
change, is an owner decision and `OPERATOR-239533.md` says so where the effect
appears.


## 2026-09-23T11:56:42.091942+00:00 — R1/R2 accepted; R3/R4 unresolved, claim247389

review-2026-09-23T11-56-42Z.md accepts startup/clock/public return fixes and guards/reserve improvements. Remaining reproduced interruption gap: real submission commits then KeyboardInterrupt escapes with no outcome.79 tests pass but composition defers all runtime admissions, so real admitted lifecycle/no-progress/cancellation/frozen-output coverage is absent. Correction-round detection after opening does not satisfy owner247316 no-round/before-enabling requirement. This supersedes full R1–R4 resolved and awaiting-live status; report exact product limitation for owner decision, keep executable path fail closed. Evidence review-evidence-247389.json; measured1.311204790s.

## 2026-09-23 -- the no-correction boundary, implemented

Owner reroute 247421 selected "the smallest supported product change needed
for review-only completion without opening a correction round; preserve
existing correction behavior for other Jobs". The decision and the exact file
ownership are recorded in `OWNER-PRODUCT-CHANGE-247423.md`, written BEFORE any
product byte was edited, as that reroute requires.

THE CHANGE IS ONE OPTIONAL MEMBER AND ONE CONDITION.
`correction_policy: "open" | "decline"` on the stage-execution deployment,
absent meaning `"open"`. `held_configuration` owns the value where every other
member is owned; `StageDeployment` carries it; and `routed` declines to reach
`review_driver.open_correction` when it says `decline`, recording
`correction_declined` instead. Every existing deployment document carries no
such member and is unchanged -- the preservation half is a DEFAULT rather than
a migration.

WHY IT FAILS CLOSED RATHER THAN REPORTING. Review 2026-09-23T11:56:42Z R4:
"returning held does not undo that store effect". Claim 247318 detected the
round after the act; this declines before it. What is declined is the ROUND,
never the verdict: a reviewer remains free to answer any of the three
dispositions and nothing in this path reads or prefers one.

AND THE PACKET IS NOT RUNNABLE WITHOUT IT. `review_supervisor.held_packet`
reads the deployment document and refuses a packet whose `correction_policy`
is not `decline`, so the boundary is a precondition of running rather than a
promise in prose.

THE CHANGE HAD A DEFECT AND THE PRODUCT SUITE FOUND IT. The first version read
`self.deployment.correction_policy` inside `routed` -- and `routed` IS the
deployment's own method, so 38 product cases answered `AttributeError`. The
suite now runs 424 with 12 errors, and those 12 are the pre-existing
`Integration._run` fixture errors recorded before this Work: each fails inside
that function's producer-proposal read and none names `correction_policy` or
`routed`. `PRODUCT-CHANGE-247423.json` records the before and after digests and
that accounting.

## 2026-09-23 -- an interrupt during the first owner act lost the outcome

Review 2026-09-23T11:56:42Z R3a. The submission publishing region added under
claim 247318 caught `Exception` only. The installed termination handler raises
`KeyboardInterrupt`, which is not an `Exception`, so an interrupt arriving
during `submit` or the turn-ceiling read escaped through `supervise`'s
`finally` -- which only restores handlers -- leaving a COMMITTED stage with no
outcome on disk.

An owner act is exactly where this matters most: it is the first moment the run
has changed anything. The guard now catches `BaseException`, records the
interruption, skips serving, and re-raises `SupervisorInterrupted` at the end
by the same path every other interruption takes -- after the accounting and
after the publication. The regression wraps the real public `submit`, lets it
COMMIT, and then injects the interrupt, which is how the reviewer reproduced
it.


## 2026-09-23T12:20:24.805295+00:00 — R3a accepted; R4 source mechanism and remaining proof

Review claim247547: review-2026-09-23T12-20-24Z.md. Independent committed-submission interrupt now publishes outcome and raises SupervisorInterrupted. Correction-policy source branch accepted at recorded318e9a4b...after hash; full composed ending still pending R3b.86 focused tests pass/1.302250807s. Required packet follow-up: current selections still bind old242687 snapshot without correction_policy; preserve it and bind a successor containing accepted source. Author12 product-suite errors remain uncorroborated as pre-existing in this review. NOT RUNNABLE status retained. Evidence review-evidence-247547.json.


## 2026-09-23T12:45:47.569527+00:00 — item 5 independently supported; lifecycle still outstanding

Claim247699, review-2026-09-23T12-45-47Z.md. Five focused configuration/packet tests pass. Independent same-test baseline/current source comparison reproduces the same twelve errors (eight missing proposal, four missing reconciles), corroborating non-regression for the selected change; traceback absence alone was not proof. Measured test time2.361050477s. Items1–4/6 remain incomplete and packet NOT RUNNABLE. Supersedes the prior unresolved item5 corroboration concern only. Evidence review-evidence-247699.json and review-baseline-comparison-247699.json.


## 2026-09-23T12:57:02.097283+00:00 — report contract diagnosed and composed verdicts independently proved

review-2026-09-23T12-57-02Z.md (claim247796): findings lists are refused by _review_report; passing string findings through the existing fixture operand settles accepted and changes-requested with attributed frozen verdict and positive cleanup, zero correction rounds. Current fixture still has zero discoverable cases. Supersedes the claim247757 unknown-cause hypothesis only; failure coverage/source binding and complete packet remain unfinished, NOT RUNNABLE. Independent evidence review-probe-247796.json and review-changes-requested-247796.json,3.324525589s. Author unmeasured probe spending must remain unknown rather than excluded from an exhaustive total.


## 2026-09-23T13:04:00.673225+00:00 — items1/2 accepted; item3 completion claim superseded

review-2026-09-23T13-04-00Z.md claim247855: eight new lifecycle tests pass in4.056475030s. Independent successful lifecycle supported; admitted interruption/failure accounting partial. Missing admitted no-progress/uncertain-cleanup/shutdown-interruption cases, gate-order observation and total-bound assertions mean item3 remains incomplete, superseding author247823 completion claim. Items4/6 remain outstanding; NOT RUNNABLE. Direct continuation to baton.impl under M247805. Evidence review-evidence-247855.json and review-tests-247855.log.


## 2026-09-23T13:10:01.374442+00:00 — gate ordering accepted; remaining item3 claims narrowed

review-2026-09-23T13-10-01Z.md claim247893:15 lifecycle cases pass. Gate-state observation and exact outstanding identity accepted. Exact claimed nonfinishing bound case instead settles in3 simulated seconds with0 cleanup sweeps; no serving+cleanup bound proof. Shutdown-specific interruption assertion and admitted no-progress remain outstanding. Supersedes author247870 three-of-four-complete interpretation for bounds/shutdown. Evidence review-evidence-247893.json; measured8.306612300s. Direct implementation continuation; NOT RUNNABLE.


## 2026-09-23T13:15:08.145296+00:00 — reached deadline and observed shutdown accepted

review-2026-09-23T13-15-08Z.md claim247931 accepts previous R1/R2 corrections at the selected deterministic boundary;5 focused tests pass4.491119177s. Withheld admitted turn reaches deadline, controlled schedule remains within total, cancellation interruption observed and outcome published. Admitted no-progress and items4/6 remain unfinished. Evidence review-evidence-247931.json. Direct implementation continuation; NOT RUNNABLE.


## 2026-09-23T13:20:42.954621+00:00 — successor source bytes accepted; item4 remains partial

review-2026-09-23T13-20-42Z.md claim247981 verifies both106-file snapshots with zero missing/extra/drift; only stage_execution.py differs, at accepted6a212c3a... digest. Snapshot/path binding accepted. Supersedes author247947 item4-done claim: its required exact-source preparation/startup is still unexecuted. No-progress and complete packet remain outstanding; NOT RUNNABLE. Evidence review-evidence-247981.json,0.008175629s; no unchanged suite rerun.


## 2026-09-23T13:25:28.271153+00:00 — successor composition accepted; startup claim corrected

review-2026-09-23T13-25-28Z.md claim248011:2 focused tests pass0.770625345s. Actual composition and exact-manifest/import helper checks accepted. Generated startup program calls3 helpers, never main; supersedes author247997 main-executed/item4-complete interpretation. Actual disposable main entrypoint proof, admitted no-progress and full packet remain outstanding. Evidence review-evidence-248011.json. Direct implementation continuation; NOT RUNNABLE.


## 2026-09-23T13:35:00.350586+00:00 — actual main startup accepted with explicit scope

review-2026-09-23T13-35-00Z.md claim248076:actual main case passes8.602200050s, disposable stores/survey/submission/outcome, status1 no-runtime hold with Deferring composition and simulated image inspect. Closes main-never-called finding; does not establish successful reviewer execution through main. Admitted no-progress and full packet remain outstanding. Reported preliminary242s must remain visible separately from suite-only subtotal. Evidence review-evidence-248076.json; NOT RUNNABLE.


## 2026-09-23T13:41:04.035546+00:00 — multi-Job fixture identity diagnosis

review-2026-09-23T13-41-04Z.md claim248112: inherited states reads first Job; diagnostic public-status selection of REVIEW_JOB makes review complete with final positive cleanup. Still overall-bound-exceeded/stalled_ticks0, so serving-time no-progress conditions remain unproved. Current fixture also deliberately adds integration, reported as correction-round hold. Evidence review-probe-248112.json and review-job-selector-248112.json;4.183597788s. No candidate implementation edits; direct continuation, NOT RUNNABLE.


## 2026-09-23T13:46:58.926666+00:00 — confirmed unallocated-attempt suppression of no-progress

review-2026-09-23T13-46-58Z.md claim248158 traces42 real cleanup reads. Review cleanup is positive during serving; extra blocked-stage attempt has no runtime but is counted outstanding until shutdown origin classification excludes it as unallocated. Thus local serving/shutdown accountable-set mismatch, not necessarily changing observation, suppresses stall detection. Supersedes author248135 fourth-condition explanation. Exact supported-origin/local-supervisor continuation in review; no baseline/product edits authorized by this finding. Evidence review-cleanup-trace-248158.json,2.115041870s. NOT RUNNABLE.


## 2026-09-23T13:52:06.553459+00:00 — no-progress logic accepted; origin-read interruption regression

review-2026-09-23T13-52-06Z.md claim248195:3 no-progress cases pass2.201875895s. New _serving_origin uses _guarded with discarded interrupted=[]; injected KeyboardInterrupt returns foreign instead of stopping serving. Preserve ordinary exception fail-closed accounting but propagate termination to existing shutdown/publication handler; targeted admitted boundary regression required. Supersedes full item3-complete claim pending this regression fix. Evidence review-evidence-248195.json; NOT RUNNABLE.


## 2026-09-23T13:57:49.093672+00:00 — origin-read interrupt fix independently accepted

review-2026-09-23T13-57-49Z.md claim248240 resolves prior R1;2 focused regressions pass13.059195031s. Supervisor digest701fc686981e96f63eef06e9725608d5c72a782f0d6ff9f9b612d5d84c63b4af; Exception-only fallback preserves uncertainty and termination reaches shutdown/publication. Item3 correction resolved; item6 complete packet remains unfinished, NOT RUNNABLE. Evidence review-evidence-248240.json.


## 2026-09-23T14:11:01.328954+00:00 — complete preparation independently accepted; live result not established

review-2026-09-23T14-11-01Z.md claim248320 accepts consolidated item6 packet;25 checks pass0.006716731s, exact candidate digests review-packet-digests-248320.json. Supersedes prior preparation-awaiting-review status only. NOT RUNNABLE until owner resolves12 inputs, Authority preparation/handler evidence, fresh retained-subject checks and explicit bounded live selection. Separate main/real-lifecycle proof limits remain; W239533 stays open pending actual accepted result. Pass baton.decide.


## 2026-09-23 — actual selected composer CLI refuses documentation metadata

baton.prompt records owner execution of /tmp/prepare-w239533-248377.py.
review_bindings.main passes selections["compose"] directly via **kwargs;
the accepted template includes _manager_source_note, which compose does not
accept. The CLI raises TypeError before entering compose. The selected root
and selections.json exist; run/ does not exist. No worker was launched.
This is a template/CLI compatibility defect missed by preparation acceptance
and prompt input resolution, not an operator error.

Stopgap: preserve selections.json unchanged and create a separately named
executable selections copy omitting only compose._manager_source_note.
Use the unchanged reviewed composer; preserve all substantive operands.
Durable correction belongs to W239533: make template and CLI agree and test
the actual selected template through the actual entrypoint. This note does
not claim that the recovery composition or live review has succeeded.


## 2026-09-23 — concrete live entrypoint refuses bounds documentation note

Owner invocation of review_supervisor.py on independent-review-248377 refused
before stores opened: bounds._note is unexpected. review_bindings copied this
metadata from the accepted selections into PACKET.json; supervisor requires
exactly the five execution-bound members. Packet hash
4405c96d4bffea78eebda64eefb8f55ab07559fa1e16aa50b2a1fb9bb36912bc
is preserved. This is a second template/composer/startup compatibility defect,
not an operator error. Registration previously succeeded; no review was admitted
by this refused invocation.

Recorded stopgap: create PACKET-executable.json beside the original, removing
only bounds._note, with all five limits and all artifact bindings unchanged.
Validate the transformed document through the actual held_packet reader before
writing it. Preserve both packet hashes. Permanent correction belongs to this
Work: metadata normalization at composition and the actual resolved template
through startup, not independent synthetic packet fixtures.


## 2026-09-23T14:45:57.561764+00:00 — live evidence retained; independent reader operationally refused

review-2026-09-23T14-45-57Z.md (claim248523) preserves executed/original packets, outcome and provider logs with hashes in live-review-248377/MANIFEST.json. Packet-only metadata removal and artifact checks pass; exact Docker runtime absent. Live outcome reports accepted55.409s/positive cleanup. Supported ControlStore.open_readonly refuses with OperationalError, so frozen attribution is not independently accepted. Cause remains unknown, no unsupported store fallback. Two previously logged metadata compatibility defects remain routine corrections; return baton.impl with no live rerun. Supersedes preparation-only/no-execution state, not acceptance obligations.


## 2026-09-23T15:00:25.913896+00:00 — live independent review and template corrections accepted

review-2026-09-23T15-00-25Z.md claim248639 supersedes prior incomplete acceptance. Supported pinned read-only opener now succeeds; one coherent public-reader snapshot independently derives exact retained accepted verdict, verifies populated independent identities and confirms retained/absent cleanup. Earlier OperationalError cause remains unknown.38 focused template/packet checks pass0.888220837s. Evidence review-attribution-248639.json and review-tests-248639.json/.log; retained original manifest unchanged. R1/R2 resolved for delivery; pass baton.decide for closure, no rerun. One live proof only, no reliability-rate or live disagreement claim.
