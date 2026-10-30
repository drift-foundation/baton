# Progress

## claim370272 — the selected execution

Owner E370247 authorizes operational execution under accepted packet binding
`29375db1f141bb4b64b3be38a9429264590d3a3d2a41dd196461d7c977eaf34f`. This
section is written **before the first operation** and is appended to as each
step completes, so it is the execution record rather than a summary of one.

### Pins re-validated immediately before applying (read-only)

    HEAD                         42bed8bb04a53380e565b1a63fb2bc702677f0d0   matches grant
    v12 porcelain                clean
    packet binding               29375db1…c977eaf34f                         MATCHES GRANT
    child binding (claim-369373) 92d9962a…893765723                          MATCHES GRANT
    default inventory            6ae52f7b…243284add                          MATCHES GRANT
    selected task digest         c21e6b93…c6bd98d7
    proposed_format              false
    seven proposal files         all still `proposed-not-granted`
    eight child artifacts        all SAME against claim-369373

The older `claim-369192`/`claim-369298` bindings show drift on files the later
accepted claims superseded; that is their history, and `claim-369373` is the
binding this grant names. Checked rather than assumed.

### The five selected fresh paths were absent at claim

    /home/sl/baton-instances/useful-template-job-w366962
    …-distro   …-mint.json   …-compose   …-phase2.json

Path absence is a momentary observation, not a reservation — the readiness
receipt says so and so does this. Each is created by the step that owns it, and
an occupied path **refuses** rather than being removed.

### The sequence, as it actually ran

    01:20:48  materialize  --into $DISTRO                      exit 0
              81 files, folder digest 0b7bc592…, archive 1da85eed… — BOTH pins
    01:21:11  mint_inputs.py --into $MINT                      exit 0
              943 bytes, sha256 4888a4be… — the packet's published figure
    01:21:11  identity                                         exit 0
              frozen true, both schema assets, native rpds in _internal,
              18e771f0 dirty disclosed and NOT relabelled
    01:21:20  bootstrap --inputs $MINT   (mint only)            exit 0
              authority 6dcb60dce5cd485b8bf03c24bc4afc82 GENERATED, no workers
    01:21:28  compose --proposed-grants --evidence $COMPOSE     exit 0
              work 6dcb60dc-W1, two lanes, manifest 91828f1e…,
              installed task digest c21e6b93… = the owner-selected task
    01:21:45  bootstrap --destination --repository-source       exit 0  (8s)
              both lanes, repo cloned, both nominated sources at 42bed8bb
    01:26:15  manager … create                                 exit 0
    01:26:25  start                                            exit 0
    01:26:30  a real container starts and a real provider turn begins

### Three defects in the accepted packet, found by executing it

**1. §5 before §6 cannot work on a fresh installation.** `create` opens the
control store **read-only** and a fresh install has none —
`ContractRefusal: a read-only manager requires an existing regular store`.
The only writable open in `job_manager` is `_serve`, so the control store is
created by *serving*.

**2. And `create` after `start` cannot work either.** `create_template_job`
takes an exclusive flock on the workspace instance guard, which the running
`manager serve` holds — *"another manager is already active for workspace …
only one Host manager may be active for one workspace and database"*.

So neither order works alone. The supported order is **install → start →
stop → create → start**, which is what this execution used; every command in
it is one the grant already authorizes, nothing was repaired and no Job was
re-admitted. The pilot packet never hit this because its `submit` verb takes
no `--control` at all.

**3. The workspace-storage prerequisite is missing.** `start` refused with
*"the configured workspace store … is not a directory this manager can see"*.
The **pilot** packet publishes this as *"Selection 2b — the workspace storage
prerequisite"*; the accepted packet dropped it. Created with `mkdir -p` after
reading the path from the emitted `deployment.json` and checking it is inside
the destination, exactly as the pilot packet instructs.

**4. `manager … status --observe` needs `BATON_V12_STAGE_EXECUTION_CONFIG`**,
which §§7 and 10 publish without. Refused until it was set.

### What the live run established — and it is the real answer

**The provider authenticated and a real model ran.** The attempt's native log
root carries the provider's own session files: a project transcript that grew
past 470 KB, a tool-results file, a session key, a shell snapshot. Activity
observed by the manager climbed 161 KB → 401 KB → 759 KB → 843 KB → 1.09 MB →
1.23 MB. This is not a simulation, and no earlier proof in this campaign could
reach it.

**And the stage is `exceptional` anyway.** From the first observation the
implementation stage projects `exceptional` — *"failed: stage ended
exceptionally"* — **while its runtime is still `running` and still
producing**. The cause the projection gives is
`exchange: unreadable {category: policy, code: denied}`. The review stage sits
`blocked`, *"held: waiting on …/implementation (exceptional)"*, with its own
attempt id and its own participant.

**The worker is answering correctly.** `state/launch/<attempt>/events/` holds
a current `receipt.json`, `state-describe.json`, `state-work.json` and
`activity.json`; `command/` holds the manager's own `sequence-….json`. The
directory modes are **exactly** what the manager requires — `command` 755 vs
`COMMAND_DIR` 0o755, `events` 2770 vs `WORKSPACE_DIR` 0o2770, gid 1000 vs the
configured `workspace_group` 1000 — and `getfacl` shows no extended entries.

**The exact denial is NOT established, and one of my own diagnostics was
circular.** The projection carries only the safe category and code; the prose
is deliberately not durable. My first reproduction called `launch.adopt` with
the session and contract read from the attempt's *own* `launch.json`, so it
necessarily matched and returned `ok: true` — the serve loop compares against
the **manager's** recorded operands, not the document's. That reproduction
proves nothing and is withdrawn; it is kept in evidence rather than deleted.

### Left running, deliberately

A runtime is live, so **no supervisor was stopped**. The grant is explicit
that cessation and settled cleanup must precede any stop, and that a context
boundary must produce a continuation checkpoint rather than an orphaned run.
`evidence/claim-370272/29-CONTINUATION.json` (sha256 `68b39eaf…`) carries the
instance, the command, every native identity, the state at checkpoint, the
exact resume invocations, the provider-turn ceiling (~02:26:30Z) and what must
not be done on resume.

### Boundaries

Operator actions were the authorized sequence and observation, nothing else.
No deletion, no retry, no second Job, no integration, no mode changed, no file
in the attempt tree touched, no credential printed — the one credential-shaped
thing read was the provider's 157-byte stderr, a stdin warning. I did not
write the deliverable: the candidate and the verdict belong to the v12
workers. The source checkout is unchanged and `v12` is byte-clean. The closed
packet and child records were read-only inputs.

**Not established:** no useful candidate was collected, no independent verdict
was reached, no held result exists, and no OBS-0 endpoint was measured. The
Job has not completed and this is not a completion report.

## claim370433 — resumed observation of the same Job

Answers `review-2026-10-28T01-41-07Z.md`. One milestone: keep observing this
exact admitted Job through its natural outcome. No new owner selection is
needed and none is sought. No product or deployment repair, no instrumentation
injected into live processes, no fresh attempt, no second Job, no deletion, no
integration, and no supervisor stop before cessation and settled cleanup.

### Two corrections I owe, both the reviewer's and both accepted

1. **My `refresh_runtime` quotation was wrong.** I read its docstring as a
   current rule that an exceptional stage can never reconcile. It describes
   the **historical defect that hook fixes**; the function names
   exceptional-runtime reconciliation as its purpose. Withdrawn. Whether this
   run reconciles is a question for observation, not for that source argument.
2. **"Only a live provider could catch this" was too broad.** A deterministic
   worker/exchange fixture over a real composed Job launch plus read-only
   observation could test the identity agreement the reviewer located. Live
   authentication and model execution are separate evidence. Narrowed.

### State at resume (01:41:57Z)

    implementation  exceptional   runtime running   1 564 020 B   exchange unreadable
    review          blocked       held on the implementation stage
    episode         not ended, corrections 0, artifacts null
    supervisors     169781 / 169782 present; a runtime process also present

### The natural outcome, reached while observing

    01:42:41  impl exceptional   running     1 608 711 B   review blocked
    01:44:26  impl COMPLETED     destroyed   artifact 82 420 B   review exceptional
    01:46:10  review has its own runtime, its own participant, generation 2
    01:48:06  review worker wrote a terminal: faulted
    01:51 … 01:55  steady: 1 review episode, 0 corrections

**The reviewer's hypothesis is confirmed, and my earlier reading was wrong.**
At 01:37 the only supported views said the implementation stage was
`exceptional` with the exchange `unreadable (policy/denied)`. At 01:44 that
same stage resolved to **`completed`** with a real artifact and a destroyed
runtime, **with no intervention of any kind**. So `exceptional` + unreadable
exchange did not mean serving had failed — it was a reporting defect, exactly
where the reviewer located it (`_Observation._job_execution` rebuilding the
installed manifest where serving uses `_given_for(stage)`).

The operational consequence is worth stating plainly: **for about eighteen
minutes every supported view told an operator this Job had failed while it was
working normally.** That is the defect worth fixing, and it is a reporting
defect rather than a serving one.

### The implementation lane succeeded

    disposition     candidate
    why             "the candidate changed the source and its own verification passed"
    changed_paths   ["v12/TEMPLATE-JOBS.md"]      ← exactly the selected scope
    base / head     42bed8bb… / e6de29e5…
    provider        status 0, failure_reason null, seconds_bound 3600
    artifact        proposal, 82 420 B, sha256:40c8b565…, sealed in custody
    patch           49 185 bytes creating v12/TEMPLATE-JOBS.md

**And the verification contract this campaign composed ran inside the worker
and passed** — `verification.txt` records `exit: 0` for
`guide_contract.SCRIPT`. The product deliberately withholds that command's
stdout/stderr, and says why: it is code from the tree the provider edited,
running with the credential mount readable, so an operator reruns it from the
collected tree instead. That is a product decision, not a gap here.

### The review lane faulted, and produced no verdict

    ending      faulted          fault_code  agent
    answered    ["describe"]     disposition null
    container   exited, exit code 1, not OOM-killed, 01:43:32.277Z
    provider    NO output: the logs view reports the native room `empty` —
                "the room exists and the provider wrote nothing in it"

Independence *is* established — its own attempt, container, participant and
generation — and the implementation gate opened correctly. But the review
never reached a model turn. **Why it faulted is not established**: `agent`
and exit 1 with no stream is all the retained evidence carries.

**No correction opened, and that is correct rather than a gap.** A
`changes-requested` *verdict* opens a correction; a *faulted* review is an
exceptional stage with no verdict to correct against. The owner's no-ceiling
correction grant is simply not engaged.

### Cessation yes, cleanup no — so nothing was stopped

Cessation is **established**: the implementation container is gone, the review
container is exited, neither is running. Cleanup is **not settled**: the
diagnostic's cleanup axis is unknown, the review runtime still projects
`quiescent` rather than destroyed, and the exited container is still present
in the engine. The grant requires cessation **and** settled cleanup before any
supervisor stop, so `169781` and `169782` are still running.

### Verification and cumulative spending

This claim: 7 timestamped samples through the supported views (stack status,
installed `attempt-diagnostics`, `logs … locators`, the published snapshot),
two read-only container inspections, and read-only reads of the retained
candidate and both workers' exchange documents. No store was opened directly,
no live file touched, no instrumentation injected, no patch, no retry, no
second Job, no deletion, no integration. Previous claim: the install and
admission sequence and 64 evidence files, all preserved.

### Boundaries

I did not write the deliverable and did not impersonate a worker, reviewer or
owner — the candidate is the v12 implementation worker's and the missing
verdict is the review worker's to have produced. No credential material was
printed. The source checkout is unchanged, `v12` is byte-clean, and the closed
packet and child records were read-only inputs.

**Not established:** no independent verdict exists and none can be inferred;
why the review agent faulted; the exact exchange denial, which the projection
withholds by design; no owner acceptance, no integration, no OBS-0 endpoint.
