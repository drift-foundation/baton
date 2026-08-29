# Plan

1. [done 2026-08-28] Revalidate the live process tree and preserve exact
   PID/PPID/PGID/SID evidence plus the self-matching watcher and runaway-test
   mechanisms. Evidence:
   `evidence/reviewer-research-2026-08-28.md`.
2. [done 2026-08-28] Map the current outer-owner gap. The bridge has a setup
   deadline but no turn deadline; its direct-child stop and infrastructure
   process-group stop cannot reach tool-created sessions. ACP session ids can
   already survive an agent-process replacement.
3. [done 2026-08-28 UTC] Confirm the proposed v11 boundary: mandatory explicit
   `turnTimeoutMs`; one PID-namespace process domain per delivered turn;
   bubblewrap `--unshare-pid --die-with-parent` for the Claude deployment;
   positive domain exit before settlement/retry; terminal timeout reported as
   correlated `failed/cause=internal`; no separate runtime state.
4. [done 2026-08-28] Implement bridge configuration/deadline supervision,
   process-per-turn teardown and session reload; update the Claude launcher,
   supported templates, README, and installed-deployment preflight. Failure to
   establish or drain the domain fails closed.
5. [done 2026-08-28] Add the focused matrix from the research evidence:
   success/failure/timeout/cancel/shutdown/replacement teardown, `setsid`,
   self-matching watcher, runaway descendant, settlement race, session-id
   continuity, retry, and unrelated-process isolation.
6. [done 2026-08-28] Make W28681 a live prerequisite of W6636 and carry the
   attempt-domain invariant into W6636's owned destroy/settlement crossing:
   force-remove the exact container and observe positive absence before clean
   settlement or replacement.
7. [done 2026-08-28, with one operator step outstanding] Run focused ACP,
   deployment, and infrastructure
   gates; preflight the PID namespace from the actual service launch context;
   then run the full gate and obtain independent review.

## 2026-08-28 — implementation

- [done] 4a. `turnTimeoutMs` is mandatory configuration with no default. Every
  other timeout in this program has one because a wrong guess is merely slow;
  a wrong guess here either kills legitimate long work or leaves the defect
  open, so it is deployment policy and an undecided configuration does not
  start.
- [done] 4b. `promptText` races the prompt against the agent's death AND the
  wall-clock deadline. Streamed ACP updates never extend it: a legitimate tool
  may be silent while an infinite talkative one produces updates forever, and
  the matrix drives exactly that case.
- [done] 4c. One process domain per delivered turn. `settleDomain` destroys it
  before settlement on success, failure and deadline alike, and the next
  delivery builds a fresh one that resumes the retained ACP session id with
  `loadSession`. No session-rotation rule changed.
- [done] 4d. Teardown is PROVED rather than attempted. `stop()` sends TERM,
  waits a bounded grace, sends KILL, waits a bounded proof window, and raises
  `DomainTeardownError` if the exit cannot be shown. The previous version
  awaited the exit after KILL with no bound at all, which was the same
  hang-inside-recovery shape as the defect one layer down.
- [done] 4e. Fail-closed. An unprovable teardown publishes correlated
  `failed`/`cause=internal`, retains the readiness key, publishes no `idle`,
  starts no replacement domain, and ends the run.
- [done] 4f. A deadline is terminal for the delivery and reported through the
  EXISTING typed `failed`/`cause=internal` with its own detail and its
  `(work, episode, session)` correlation. No new runtime state was added.
- [done] 4g. The shipped Claude/pc.code launcher now passes `--unshare-pid`
  and `--die-with-parent` beside its mount boundary, and
  `pc-code-policy/preflight-process-domain.sh` ships beside it. That
  deployment's own `verify.mjs` refuses a staged launcher missing either flag
  and requires the preflight to be present; the bridge does not check it,
  because the bridge is ACP-generic and does not parse the configured command.
- [done] 4h. Template, README and policy-resource list updated.
- [done] 5. The focused matrix: mandatory-operand refusals, deadline reached
  and reported with correlation, chatty-infinite turn, teardown-before-`idle`
  ordering on success and on failure, one domain per turn with session
  continuity across processes, fail-closed unprovable teardown, bounded
  unprovable exit, shutdown teardown, and a real `setsid` tool descendant.
- [done] 6. The attempt-domain invariant is recorded in W6636's own
  `FINDING.md` under "Attempt-domain invariant carried in from W28681". The
  ledger prerequisite edge already exists (W28681 blocks W6636).

### Outstanding, and it is an operator step rather than a gap

- [operator] `preflight-process-domain.sh` must be run FROM THE SERVICE LAUNCH
  CONTEXT before the changed launcher is installed. Run from this managed
  turn it refuses with `No permissions to create new namespace`, exactly as
  the reviewer's probe did — reported as a fact rather than worked around,
  and the script refuses rather than passing vacuously.
- [operator] Installing the changed launcher, template and preflight into
  `/home/sl/.config/baton/acp/...` is the INSTALL.md cutover procedure and is
  not something an agent turn performs.

## 2026-08-28 — independent review changes requested

- [required] Make the deployment verifier inspect the executable launcher
  contract rather than matching flag names that also occur in comments; add a
  negative mount-only-launcher regression.
- [required] Update `successor/INSTALL.md` to install and byte-check the new
  preflight resource and to run it from the service launch context before
  activation, with fail-closed rollback/paused-dispatch instructions.
- [required] Prove domain-owner termination removes detached and busy
  descendants while leaving an unrelated process untouched. The current green
  unit test reports that its descendant survived and is not acceptance proof.
- [required] Bound `turnTimeoutMs` to the actual Node timer range and repair the
  chatty-infinite fixture so it emits and asserts valid ACP activity.
- [pending operator verification] After those corrections, run the exact
  service-context namespace/descendant preflight and preserve its result before
  acceptance.
- [pending] Re-run focused bridge, deployment verifier, infrastructure,
  teardown-race and regression gates, then return for independent review.

## 2026-08-28 — review corrections applied

- [done] [P0] The launcher gate no longer reads prose. `verify.mjs` RUNS the
  staged launcher against a recording stand-in for bwrap and reads the argv it
  actually composed, requiring both flags to be present, to precede the agent
  executable, and to sit beside a surviving read-only bind. My own explanatory
  comments are what made the previous `includes()` check vacuous.
- [done] [P0] And the gate proves its own reachability on every run: a copy
  with the functional flags removed from the ARGS line and every comment
  retained must be refused, and the probe first checks that both flag names
  still appear in that copy — otherwise it would pass a free-text check too
  and prove nothing.
- [done] [P0] `INSTALL.md` installs `preflight-process-domain.sh` in both the
  fresh cutover and the reconciliation path, byte-compares it and the launcher,
  backs the launcher up before overwriting it, restores it and removes the
  preflight on both rollback paths, and carries a MANDATORY service-context
  process-domain section whose nonzero result keeps dispatch paused.
- [done] [P0] `verify.mjs` now refuses a staged set where any template-required
  policy resource is missing from the staged directory OR has no INSTALL
  COMMAND whose destination is that path. A mention is not enough — that is the
  same free-text mistake, and the probe that proves this gate can fail removes
  EVERY satisfying line rather than one.
- [done] [P1] The preflight runs the real trial. It creates the domain, starts
  an escaped (setsid) descendant and a busy descendant inside it, terminates
  the owner, awaits its exit, and requires both gone while an unrelated process
  of the same shape survives. Typed exit codes name which half failed.
- [done] [P1] `turnTimeoutMs` above the runtime's signed 32-bit timer ceiling
  is REFUSED rather than clamped, with the maximum named in the message and in
  the README. `2147483647` and `2147483648` are both driven, and the case
  measures the runtime's own truncation rather than asserting the constant.
- [done] [P1] The chatty fixture emits VALID ACP updates (`toolCallId` was
  missing, so the SDK refused every one and the deadline was reached over a
  silent agent). The case now requires zero refusals, at least two streamed
  beats, at least one update reaching the bridge's handler, and THEN the same
  deadline outcome.
- [noted] The v12 handoff correction is the reviewer's: W6636's PLAN.md now
  carries the pending force-remove/positive-absence work, preserving W6636 as
  the single implementation owner.

### Still outstanding, and it is the same operator step

- [operator, MANDATORY BEFORE ACCEPTANCE] The service-context descendant
  teardown trial. The strengthened preflight IS that trial, and it still cannot
  run from a managed turn: this context refuses with exit 3, "could not create
  the required PID namespace". The reviewer is right that a green suite here
  cannot substitute for it.

## 2026-08-28 — second independent review changes requested

- [required] Make the descendant preflight prove exact descendant identities,
  not tokens also carried by the outer owner's argv. Add a negative trial in
  which the owner runs but creates no descendants; it must refuse.
- [required] Make the fresh-cutover procedure create every backup its rollback
  consumes, including an explicit absent-launcher case, and make the staged
  verifier establish path-local backup/rollback pairing.
- [required] Reset runtime correlation per action and prove an early failure
  of a second action cannot inherit the first action's Work, episode, or
  session.
- [operator, still mandatory] After those corrections, run the exact
  service-context descendant teardown preflight and preserve its result before
  acceptance.
- [verified] ACP bridge 88/88, Codex event bridge 420/420, staged verifier
  green, and targeted diff check clean. The preflight's no-descendant negative
  reproduction currently exits 0 incorrectly; see
  `review-2026-08-28T07-51-55Z.md`.

## 2026-08-28 — second-review corrections applied

- [done] [P0] The preflight proves EXACT HOST IDENTITIES and liveness, not
  command-line matches. The descendants publish liveness by appending to their
  own files — something no argv can do — and their host pids are read out of
  the process tree below the owner, required alive before termination and
  absent after it. All `pgrep -f` token matching is gone: the control process
  is started by the script so its pid is known, and nothing is proved by a
  pattern any more.
- [done] [P0] The reviewer's stand-in is now a gate. `verify.mjs` runs the
  staged preflight against a `bwrap` whose whole body is a sleep and requires
  a refusal, so the mandatory gate's own non-vacuity is checked on every
  verify — no namespace needed, so it runs wherever the verifier does.
- [done] [P1] The fresh cutover backs the launcher up before overwriting it,
  guarded because a genuinely fresh install has none; both rollbacks are
  guarded symmetrically and the absent-backup case is defined explicitly —
  remove the launcher this cutover installed rather than leave it behind.
- [done] [P1] `verify.mjs` establishes that every backup a rollback restores
  is PRODUCED ON THAT SAME PATH, holding the fresh sections apart from the
  reconciliation. Finding an install command somewhere in the document is the
  free-text mistake one level up.
- [done] [P1] `correlation` is reset per ACTION. A later failure can no longer
  publish the preceding action's work, episode or session.
- [done] Both new verifier gates and the corrected preflight were driven to
  failure and back; the correlation regression was measured against the
  pre-fix source before being trusted.

### Still outstanding, unchanged

- [operator, MANDATORY BEFORE ACCEPTANCE] The service-context run of
  `preflight-process-domain.sh`. It now refuses here with exit 3 for the right
  reason (no namespace), refuses a launcher that starts nothing with exit 4,
  and refuses a launcher that starts descendants but does not reap them with
  exit 6 — naming the exact surviving host pids. None of that substitutes for
  running it where the service starts.

## 2026-08-28 — third independent review changes requested

- [required] Compare heartbeat growth from a post-teardown baseline rather
  than from counts captured while descendants are still running.
- [required] Add a positive verifier probe whose stand-in starts both
  descendants, reaps the complete tree on owner termination, and must exit 0.
  Tighten the no-descendant probe to require its intended exit-4 reason rather
  than accepting every nonzero failure.
- [operator, still mandatory] Run and preserve the exact service-context
  preflight after its portable positive and negative gates are sound.
- [verified] ACP bridge 89/89 and staged verifier green. The retained
  successful-reaper reproduction exits 6 incorrectly; see
  `review-2026-08-28T08-41-58Z.md`.

## 2026-08-28 — third-review correction applied

- [done] [P1] The "have they stopped writing" baseline is taken AFTER positive
  pid absence, not before the signal. The pre-teardown counts answer only "did
  they ever run"; comparing post-teardown files to pre-signal counts called a
  final heartbeat written during teardown evidence of survival, so a launcher
  that reaped its complete tree was REFUSED — the opposite timing defect to
  the one before it.
- [done] The verifier gained the successful-reaper stand-in as a POSITIVE
  gate. A gate with only a negative probe cannot see a preflight that rejects
  the behaviour it exists to require, which is exactly what happened.
- [done] The no-descendant probe now requires exit 4 specifically rather than
  any nonzero status. "It failed somehow" would be satisfied by a preflight
  that failed for a missing tool, and would stop saying anything the day the
  script grows another early exit.
- [done] Both new gates driven to failure and back: the pre-fix baseline
  timing makes the positive gate refuse, and a preflight exiting 9 makes the
  exact-reason gate refuse.
- [done] Four outcomes measured on the corrected script: exit 0 for a
  successful reaper, 4 for a launcher that starts nothing, 6 for one that
  starts descendants but owns nothing, 3 for real bwrap in this context.
- [done] Gates: acp-baton-bridge 89/89, codex-event-bridge 419/419, staged
  verify.mjs green, whitespace clean.

### Still outstanding, unchanged

- [operator, MANDATORY BEFORE ACCEPTANCE] The service-context run. The
  portable gate now accepts the successful-reaper case and refuses the two
  failure shapes, but no managed turn can create the namespace this deployment
  actually needs.

## 2026-08-28 — fourth independent review

- [signed off] The post-absence heartbeat baseline fixes the reproduced false
  negative. The retained complete-tree reaper exits 0; the starts-nothing
  stand-in exits exactly 4; the staged verifier passes; ACP bridge 89/89 and
  Codex event bridge 420/420 pass; targeted diff hygiene is clean.
- [operator, MANDATORY BEFORE ACCEPTANCE] Run this exact staged
  `preflight-process-domain.sh` from the actual service launch context and
  preserve an exit-0 result before installation/closure. This managed context
  still exits 3 because it cannot create the required PID namespace. See
  `review-2026-08-28T09-21-45Z.md`.

## Operator acceptance — 2026-08-28

- [done approver/operator] The exact staged process-domain preflight passed
  from the normal host service-launch context. It created and positively
  reaped the escaped and busy descendants while leaving the unrelated control
  alive; the exact output is preserved in
  `evidence/operator-service-context-preflight-2026-08-28.txt`.
- [next approver] Close W28681 satisfying. Repository correction and the real
  service-context kernel boundary are both independently established.
