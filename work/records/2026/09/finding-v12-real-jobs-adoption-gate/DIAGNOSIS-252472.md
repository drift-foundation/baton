# The live two-Job run of 2026-09-24T00:53Z — what is diagnosed, and what is not

baton.claude under claim 252472, answering owner 252468. **Read-only**: the
preserved instance `/home/sl/baton-instances/two-jobs-251156` was opened for
reading only. No deployed store was mutated, no container was deleted, no
cleanup was authorized, no store was reset and nothing was rerun.

## 1. The timeout binding — DIAGNOSED, CORRECTED, AND REGRESSED

The owner observed `provider_turn` limits of **3600 seconds from compatibility
defaults** on a run this packet declared at 180. The launch document the run
actually delivered says why in one member:

```
run/launch/attempt-79177c…/launch.json
  job_execution.execution_limits.requested            = {}
  job_execution.execution_limits.boundaries.provider_turn
      = {"default_seconds": 3600, "origin": "compatibility", "seconds": 3600}
```

`submission.stage_rows` stores each Job's optional `execution_limits` member
and `execution_limits.resolved` falls back to this build's frozen defaults when
it is absent. **My submission asked for nothing.**

And the reason runs one layer deeper than a missing member:
`documents.SUBMISSION_LIMITS_SCHEMAS` is `("baton.v12.job-submission/2",)`
alone. This packet composed `/1`, on which the per-Job `execution_limits`
member is **refused as unrecognised** — so the selected bound could not be
expressed in the document I was composing at all. Adding the member to `/1`
answers:

> a submitted Job also carries execution_limits, which this build's contract
> for it does not name

**Corrected**: `two_jobs.SUBMISSION_SCHEMA` is now `/2`, and
`two_jobs.requested_limits()` derives the asked-for ceilings from
`LIMITS["per_attempt_seconds"]` so the declared bound and the submitted operand
are one number by construction. A case asserts the member AND asks the product
what a submitted Job resolves to: `provider_turn` 180, `origin: "job"`.

**What this does NOT explain**: it is a binding discrepancy, and the owner said
so. Both containers exited within about two seconds, so no ceiling of any size
was reached. Correcting it removes a real defect from the packet and is not a
diagnosis of the fault.

## 2. The agent faults — NOT DIAGNOSED

What the retained evidence establishes, and no more:

  * both workers answered `describe` (`state-describe.json`: `answered`) and
    **faulted during `work`** (`state-work.json`: `faulted`);
  * `terminal.json`: `ending: faulted`, `fault_code: agent`,
    `answered: ["describe"]`, `disposition: null`, `manifest_digest: null`;
  * the harness therefore RAN and recorded its own ending — the failure is the
    agent inside it, not the exchange;
  * `run/launch/logs/attempt-*/native` is **empty** for both attempts, and the
    owner records empty Docker logs. So the provider's own output was not
    retained anywhere this dossier can read.

**I will not name a cause.** The owner's entry says explicitly "do not infer
authentication failure", and I have no evidence that would distinguish a
credential problem from a missing directory, a umask, a network refusal or a
CLI invocation fault. What the next claim needs is the provider's own stderr,
which nothing currently retains for a faulted turn — establishing WHERE that
output goes, and whether the worker image or the manager drops it, is the first
act rather than a guess about the agent.

## 3. The failure settlement — NOT DIAGNOSED

At 00:57:24Z canonical status still reported both implementations `starting`
with both runtimes `quiescent`, and after the interruption the outcome records
**12 cleanup sweeps and no committed cleanup for either attempt**:

```
cleanup = {"attempt-79177c…": {"cleanup": null, "why": "no committed cleanup"},
           "attempt-d514aa…": {"cleanup": null, "why": "no committed cleanup"}}
outstanding_cleanup = [both]
```

A faulted terminal with no `manifest_digest` collects no intake receipt, so the
ending never reaches `authorize_cleanup` — the same shape W236087 recorded for
its own stalled cleanup ("a faulted turn froze and collected nothing, so no
intake receipt exists and the ending never reached `authorize_cleanup`"). That
is a *resemblance*, not a diagnosis: I have not read this store's ending rows to
confirm which act is missing, and I am not going to assert a settlement rule
from a similar case.

**The supervisor behaved correctly and reported honestly**: admission closed
before cancellation, both assignments fenced, both runtimes confirmed quiescent,
`state: held`, every reason named. A stopped run with outstanding cleanup is
exactly what the outcome says it is.

## 4. The workspace-directory preparation — NOT ESTABLISHED

The owner names a "missing workspace-directory preparation". Both attempts do
have `scratch/`, `credentials/`, `custody/`, `workspace/`, `credential-state/`
and `inputs/` under `run/workspaces/attempt-*`, and Job A's `workspace/`
contains its `result-attempt-…` directory. **I have not identified which
directory was missing**, and comparing this layout against the accepted
single-implementation run is the next act. Recording it as unestablished is the
honest state; a correction to a directory I have not shown to be absent would
be a change without a cause.

## The cleanup these two attempts still need — NOT PERFORMED

Both runtimes are confirmed quiescent and both attempts are outstanding. The
supported path is the manager's own, and it is **an owner act**: the ending must
be settled before a destroy can be authorized, which is precisely what item 3
has not yet established. So this document does **not** print a cleanup command
yet — printing one derived from an undiagnosed settlement path is how an
operator ends up running an act nobody has justified.

What is safe to say now:

  * the two runtime identities and their attempts are named in
    `run/outcome.json` (`admitted_attempts`, `cancellation`);
  * `cancellation` already records `requested: true` for both, and the owner
    confirmed quiescence, so nothing is still executing;
  * ad hoc `docker rm` is **not** the procedure: it would remove the runtime
    without a committed cleanup record, leaving the manager's journal asserting
    less than the host does — which is the opposite of what an accounted stop
    means.

## Preserved

`/home/sl/baton-instances/two-jobs-251156` is untouched. Its stores, launch
deliveries, workspaces, exchange artifacts and outcome are as the owner left
them.

## Correction, claim 252571 — item 4 was not unknown, it was recorded

Review 2026-09-24T01:14:08Z: "FINDING's preceding owner startup entry
identifies it precisely... Append a correction to the diagnosis rather than
presenting the owner observation as an unknown directory."

That is right and the mistake is mine. Item 4 above says I had not identified
which directory was missing. The owner's entry of 2026-09-23 — one entry above
the one I was working from — identifies it exactly:

> the live supervisor refused in `worker_preflight` because its configured
> `run/workspaces` directory did not exist. Preparation declares that path but
> does not provision it.

`operations_from` raised **before** `submit` and before `supervise`, so that
invocation admitted nothing and started no container; an operator stopgap
created the one directory by hand. The attempt directories I looked at were
made by the LATER invocation, after that stopgap — so what I read as evidence
against a missing directory was evidence from after it had been created. I was
reading the wrong invocation's leftovers.

**Corrected in the packet, not just in the record.**
`prepare_two_jobs.PROVISIONED` names the four owned roots the composed
deployment declares — the workspace store, the launch home, the credential home
and the deployment state root — and `provision()` creates them 0o700 after the
composer has made `run/`, then reads the workspace store back through
`workspaces.check_workspace_storage`, which is the same judgment
`worker_preflight` makes. A case drives that check over the composed path
before and after preparation: absent is refused by name, provisioned is held.

**Item 4 above is therefore superseded.** The preserved failed instance was not
touched to establish this and is not repaired by it; the correction is on the
NEW-instance path.

## Correction, claim 252571 — what the 180 seconds actually bounds

Item 1 above describes the corrected ceiling without saying what it bounds.
Review 2026-09-24T01:14:08Z: it is per invocation — one provider turn and one
verification command — and **not** a total attempt lifetime. This packet has no
mechanism that bounds an attempt's whole life, and the earlier "180s per
attempt" wording claimed a guarantee these settings do not give. The total this
packet does bound is the RUN, at 600 seconds including the 60-second cleanup
reserve, which is `supervise`'s arithmetic.
