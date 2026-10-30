# Retained documentation Job: disposition and settlement

Prepared by baton.tuner under W371320 / claim E371324, 2026-10-28 UTC.
Independent review and owner operational selection are pending. This procedure
prepares actions; it grants no execution authority.

**Result:** the installed CLI exposes non-satisfying authority closure, but no
supported standalone command was identified to settle this stopped, faulted
review attempt. Closure does not supply execution-token return or resource
cleanup. The original supervisor-stop prerequisite remains unsatisfied.

## Selection and evidence

This implements the preparation-only [FINDING](FINDING.md) and [PLAN](PLAN.md).
It reuses W370560's [cleanup research](../finding-v12-documentation-review-startup-fault/CLEANUP-RESEARCH-370686.md)
and [prepared commands](../finding-v12-documentation-review-startup-fault/SETTLEMENT-COMMANDS-370686.md),
and W370268's retained [outcome](../finding-v12-useful-documentation-execution/evidence/claim-370433/OUTCOME.json).
The original outcome's assertions that no model turn occurred and that observation
causality was confirmed are qualified by subsequent W370560 research/review;
empty provider logs alone prove neither assertion.

New read-only command receipts are in [evidence/claim-371324](evidence/claim-371324).
Each records the command, UTC interval, output, exit status and tool duration.
They are separate observations, not an atomic snapshot. Only selected safe
projections were collected: no credential/configuration dump or direct store read.
`--authority-store` below is an operand to the supported owning CLI, not permission
to open that database with another reader.

The installed executable reports `baton 12.0.0 (18e771f0, dirty)`; its SHA256 is
`ba962a2086310df238ff25cf282a3298f71ae9289594e6f7c83222ee8f4571ef`.
The version label alone is not provenance or installed/source equivalence.
Help proves command exposure only. Existing source research explains the expected
behavior; no closure, settlement or stop was dynamically exercised here.

## Exact identities and observed state

| Axis | Bound identity / latest observation |
| --- | --- |
| Instance | `/home/sl/baton-instances/useful-template-job-w366962` |
| Native authority / Work | `6dcb60dce5cd485b8bf03c24bc4afc82` / `6dcb60dc-W1` |
| Job / review stage | `job-template-job-guide-42bed8bb` / `job-template-job-guide-42bed8bb/review`, episode 1 |
| Authority assignment | `baton.reviewer-w366962`, generation 2, active/open; no close decision |
| Review attempt | `attempt-793b51aabf70b8b4469e8db90b12c7ecbe606a8abbbd2c2cf39f9a7214f945e5` |
| Exact review container | `a813a59f691c23022343cb25f3050df2c95386ae36b7dbab647fd4108d906ee6` |
| Fresh engine observation | Exited, Running=false, Restarting=false, Pid=0, ExitCode=1; finished `2026-10-28T01:43:32.27722424Z`; container still exists |
| Recorded execution | Review exceptional, runtime quiescent, cleanup pending; execution observation `2026-10-28T01:43:35.303Z` |
| Execution ownership | Diagnostic token returned=false, resource `workspace:66306:50372623`, resource generation 1; this is distinct from authority assignment generation 2 |
| Token launch / owner | `runtime.start:5e316e82fb46f36c4f9ad6bb791f97560c7e4e41746c38f466de00862f6c8268` / `c1ee03f980607abe42fbaeb13f74afcdc0d4d50ac128de072fd2da9181bbadee` |
| Token deadline | `2026-10-28T03:45:30.140Z`, expired=false at capture, no renewal; passing this time is not settlement evidence |
| Proposal | `integration-driver.proposal:4f11c905608c7b06eac7765d5ce65c817b72c2e252ea0fb760548846ce2bb819` |
| Candidate / base | `e6de29e5f945f692a42f689570d5c39edc4f61bc` / `42bed8bb04a53380e565b1a63fb2bc702677f0d0` |
| Acceptance | Authority verification, review, approval and integration receipts all null; worker-local verification is not an authority receipt |
| Implementation execution | Diagnostic reports completed/destroyed, cleanup retained, token returned=true; not independently re-inspected in Docker this turn |
| Supervisors | `status` reports stale PIDs 169781/169782; `ps` reports both processes present with manager/publisher commands for this instance |

The supervisor discrepancy is unresolved. Neither stale-PID text nor a fresh
snapshot proves supervisor cessation or safe process ownership for signalling.
The diagnostic explicitly supplies no freshness verdict, and its newly composed
timestamp does not refresh the old execution observation. Fresh Docker inspection
establishes cessation of this exact confined container at inspection time, not
authority closure, token return, accepted output or destruction.

## Read-only preflight

Run each command independently. Retain its timestamp, exit status and safe output.
Do not proceed to an effect on an unreadable or mismatched identity. A missing
container, engine error or newly running/restarting state requires assessment;
none substitutes for the expected positive exited observation.

```sh
/home/sl/baton-instances/useful-template-job-w366962/distro/baton-v12-stack disposition pending --authority-store /home/sl/baton-instances/useful-template-job-w366962/db/authority.sqlite3 --authority-uuid 6dcb60dce5cd485b8bf03c24bc4afc82 --work 6dcb60dc-W1 --participant baton.tuner
```

```sh
docker inspect --format '{{json .State}}' a813a59f691c23022343cb25f3050df2c95386ae36b7dbab647fd4108d906ee6
```

```sh
/home/sl/baton-instances/useful-template-job-w366962/distro/baton-v12-stack attempt-diagnostics /home/sl/baton-instances/useful-template-job-w366962/state/status.json
```

```sh
/home/sl/baton-instances/useful-template-job-w366962/distro/baton-v12-stack status --instance /home/sl/baton-instances/useful-template-job-w366962/instance.json
```

```sh
ps -o pid,ppid,stat,lstart,args -p 169781,169782
```

Compare the pending assignment with the retained expected-assignment file below,
not merely its participant. Compare the diagnostic Job, stage, episode, attempt,
runtime and token bindings with the table. Stop on a replacement assignment,
unexpected proposal/receipt, changed executable or new native close decision.
Do not rewrite the expected assignment to accommodate drift. These checks guide
the operator; the close's assignment comparison remains the atomic guard.

## Non-satisfying authority closure: future owner selection only

W370560 consumes this procedure after independent review. The owner must explicitly
select closure before executing it. These next commands are for Slawomir as
`baton.slaw`; the preparation agent did not execute under that identity.

First, the owner checks current capability and all identity preconditions again:

```sh
/home/sl/baton-instances/useful-template-job-w366962/distro/baton-v12-stack disposition pending --authority-store /home/sl/baton-instances/useful-template-job-w366962/db/authority.sqlite3 --authority-uuid 6dcb60dce5cd485b8bf03c24bc4afc82 --work 6dcb60dc-W1 --participant baton.slaw
```

Require `holds.close=true`. The tuner read returned `holds.close=false`, as expected
for this participant; it does not establish the owner's current capability.
The existing expected-assignment file must retain SHA256
`56836ce3ba5c484ff2e39e3304d11ed58b6d739f7cde4d416bae2337fab3a1ca`:

```sh
sha256sum /home/sl/src/baton/work/records/2026/10/finding-v12-documentation-review-startup-fault/evidence/research-370686/expected-assignment.json
```

Its JSON names exactly authority/Work above, participant `baton.reviewer-w366962`
and generation 2. The prepared command below is unchanged from W370560, including
its stable operation identity and rationale. The incompatible-declarations
diagnosis in that rationale is supported by source/deterministic research, not
an exact installed-runtime exception proof. If the owner chooses different
operands, prepare and review that new request rather than silently revising this one.

```sh
/home/sl/baton-instances/useful-template-job-w366962/distro/baton-v12-stack disposition close --authority-store /home/sl/baton-instances/useful-template-job-w366962/db/authority.sqlite3 --authority-uuid 6dcb60dce5cd485b8bf03c24bc4afc82 --participant baton.slaw --work 6dcb60dc-W1 --operation-id w370560-nonsatisfying-close-370686 --outcome non-satisfying --rationale 'Implementation candidate retained; review assignment faulted under incompatible output declarations; no independent verdict or accepted useful Job outcome. Preserve all evidence and unresolved cleanup.' --expect-assignment /home/sl/src/baton/work/records/2026/10/finding-v12-documentation-review-startup-fault/evidence/research-370686/expected-assignment.json
```

Expected effect: an honest non-satisfying authority ending of the exact assignment,
with existing proposal/evidence recorded as preserved. It does not accept the
candidate, publish a verdict, return the runtime token, destroy resources or stop
supervisors. Non-satisfying closure takes no candidate-acceptance operands.

For a lost/ambiguous response, retain the request and run pending; if retry is
needed, submit the identical command and unchanged assignment JSON. The original
operation identity must not be replaced merely to obtain another effect. Changed
operands, wrong assignment, missing capability or other refusal are a stop:
preserve the response, re-read pending and return the exact blocker to W370560.
Do not edit the store, drop the assignment precondition or use another actor.
A refusal may follow durable request binding; do not assume it means every
protocol record is absent.

Postcheck with the owner pending command: require the recorded non-satisfying
close decision/outcome, ended authority assignment and preserved proposal with
no invented acceptance receipts. Retain both close answer and pending output.
Repeat Docker inspection and diagnostics separately; report actual token,
runtime, cleanup and resource facts even if authority closure succeeded.

## Settlement gap and preservation

Installed top-level and manager help plus W370560's bounded source research find
no standalone operator operation for this faulted attempt's abandonment/settlement.
The ordinary answered-stage path does not supply that operation. The existing
library `abandon_attempt` is not an installed operator procedure. A future command
or selected correction must establish exact cessation, durable failed execution
status and release of this execution's ownership while preserving its workspace
and evidence. The present diagnostic still reports returned=false and cleanup=pending.

This is the concrete missing step, not a recommendation to invoke Python internals,
raw SQL, direct Docker removal, token reset or a fresh attempt. Expiry alone is
not a successful alternative. W371074 owns the generic settlement API/design;
W370688 owns successor output preparation. Neither preparation nor future source
acceptance installs a fix in this retained instance.

Resource retention and resource destruction are separate decisions. Keeping this
exited container and workspace is not evidence of an active writer, and destruction
is not required by the normative primary lifecycle to release proven stopped
execution ownership. Conversely, merely keeping them does not prove the installed
manager recorded that release. Preserve the original candidate, private state,
logs and historical evidence; no removal/copy/permission repair is selected.

## Supervisor stop: separate, unselected action

The original W370268 grant requires cessation AND settled cleanup before stop.
That condition is not established. A later owner selection may either follow
proved settlement or explicitly select an exception that retains unresolved
resources/holds and their recovery responsibility. An exception does not settle
them and does not authorize a successor writer.

Before any selected stop, revalidate instance, current native state and runtime
cessation, and resolve the stale-status/present-process discrepancy through a
supported process-ownership assessment. Do not signal the numeric PIDs manually.
The command prepared by W370560 remains:

```sh
/home/sl/baton-instances/useful-template-job-w366962/distro/baton-v12-stack stop --instance /home/sl/baton-instances/useful-template-job-w366962/instance.json
```

This targets supervised processes, not containers or authority disposition.
Current source documents ownership checks, termination waits and repeat-stop
handling, but does not prove these installed processes can be safely stopped.
If refused/unresolved, retain the records and report failure; do not escalate to
kill, record deletion or another stop mechanism. After a selected execution,
retain the command result, rerun status and process inspection, and independently
recheck Docker/diagnostic state. A zero exit alone cannot override contradictory
process evidence or establish settlement. No stop readiness is claimed here.
