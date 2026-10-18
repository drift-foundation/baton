# W324316 — terminal-result handoff preparation

## 2026-10-18 — assignment and confirmed baseline

Research owned by baton.rvpc, claim324340; binding324342. Assignment T324316
selects investigation and a proposed smallest supported completion contract before
implementation. No new live run, retry or deployment is selected. V11 remains
coordination authority; future implementation executes through a reviewed v12 Job.

Observed: W324214 remains unclaimed at baton.decide, episode324269 at snapshot
324341. Retained outcome for run worker-visibility-w324214-324217 ended held at
2026-10-18T16:34:08.887Z. Job job-worker-visibility-w324214-324217, attempt
attempt-af94020b411e17f33edbed32004267a80c789de8d949224e39a3a47fc5648a51,
v12 authority6849c91e5f46436dbcc039a2269d3b95. The outcome records exceptional/
unable, no proposal, no outstanding cleanup and exact-runtime absence. This is
retained supervisor evidence, not a new Docker observation or acceptance. The
reported authentication failure is a separate diagnosis; no retry was attempted.
Exact retained outcome, source locator and hashes: evidence/OBSERVATION.json.

Confirmed code surfaces:

- work/records/2026/09/finding-v12-single-implementation-proof/baseline.py:
  `_publish`913 atomically publishes outcome; `_supervise`1350 includes local
  Work, preparation claim, run, Job, admitted/observed attempts and uncertainty;
  `main`2012 prints outcome and exits. It intentionally does not mutate v11.
- The packet's claim324217 is preparation provenance, not current v11 execution
  ownership. It must never be treated as permission to pass/release W324214.
- v12/python/src/baton_v12/job_manager/projection.py `status`891 is the supported
  read-only observation seam. A supervisor process exit alone is not Job success
  or proof of stopped runtime. A held supervisor outcome may need diagnosis even
  when execution uncertainty remains.
- tools/codex-event-bridge/src/run_and_notify.mjs sends a socket build notification
  after child exit. It has no durable v11 result Work or restart reconciliation.
- v11 `create` supports atomic Work/thread creation and stable op-id replay.
  src/baton_work/transitions.py create_work989 permits top-level creation by a team
  member; child creation requires the parent's Route handler. A generic reporter
  cannot assume that capability.
- v11 `pass` requires the actual claimant; `reroute`4071 refuses claimed Work but
  has no expected-episode operand. Read-then-reroute can move a later unclaimed
  episode. `release` is exact-episode recovery, not a normal completion mechanism.

Operational observations: no dossier was bound at assignment start; now created
and bound. Exploratory paths tools/AGENTS.md, tools/job_status.py and
job_manager/status.py do not exist; applicable repository policy and real
projection.py were read. Guessed root result.json was absent; packet declares
packet/outcome.json, which was readable. These are locator corrections, not
missing runtime evidence or authority failures. No database was opened directly.

## Proposed smallest solution — pending selection

Use a host-side completion reporter beside the one-shot supervisor, with durable
registration before launch and reconciliation on restart. It creates ONE separate
top-level v11 result-collection Work through configured review endpoint (currently
baton.bug), using the canonical CLI and a selected reporter participant. The born
thread carries immutable origin/run/evidence identity and a clear unaccepted
outcome. Creation makes collection actionable; the review consumer must claim.
Notifications may follow but are not the handoff. See CONTRACT.md.

The reporter never changes the originating Work's route, claim, dependency,
outcome or phase. This supplies automatic independent collection without stale
episode takeover and without a v11 protocol amendment. Association is exact in
the immutable envelope; it is not falsely represented as a scheduling edge.
The result collector examines current origin state and coordinates any subsequent
handoff through supported claimed workflow. It cannot auto-accept the product.

If the required product outcome instead means automatically rerouting the SAME
origin Work, this design is insufficient: a supported conditional episode-bound
transition and explicit assignment ownership need separate selection. Do not
implement read-then-reroute as a substitute. This concrete choice, and the
authorized reporter identity, are the decision requested before packet preparation.

Decomposition: one bounded end-to-end reporter outcome; splitting persistence,
creation and restart handling would leave the observed defect unresolved. No
child or new dependency is justified for preparation. W321528 owns baseline.py
reporting changes, so propose a separate reporter module/launcher wrapper; W321689
authority/disposition paths and W324214 visibility paths remain untouched. Any
necessary overlap is coordinated before packet selection; paths are design
guidance, not an exclusive implementation restriction.

Normative alignment: v12/DESIGN.md DB-4/DB-7 require durable cross-store intent and
stable operation replay; ID-2/ID-4 preserve assignment and attempt identity;
primary lifecycle separates execution termination from output acceptance. No
specification change is proposed. Deployment activation and a real end-to-end
operator run remain separately selected after deterministic acceptance.

## 2026-10-18 — owner prioritizes leaving v11 coordination

Owner: "I don't want to spend too much time wiring v12->v11.. our priority is to jump off v11 for all coordination as well". Do not proceed with the proposed durable v12-to-v11 reporter or its actor/lifecycle infrastructure. The CONTRACT remains historical proposed design, not selected implementation. Manual terminal-outcome collection and explicit review routing remain the temporary operational path. Prioritize the existing W321608 v12-native coordination pilot and its W321689/W321690 prerequisites toward leaving v11 coordination. This supersedes the previous next-action request to select and implement the reporter. Preserve the observed pickup gap as a required question for v12-native coordination; do not declare it fixed. No existing backlog migration, production cutover, dependency removal or acceptance waiver is implied. Recommend parking W324316; canonical phase change remains owner-controlled.
