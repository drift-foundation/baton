# The connected packet proof — actual partial harness and the exact next step

W236087 claim 309960, superseding CONNECTED-NEXT-309871.md. Review
2026-09-29T22-36-24Z localized the previous blocker and I fixed it; this records
where the run reaches now, with the reproduction command the review asked for
(including `doCleanups`).

## THE REVIEWER'S DIAGNOSIS WAS RIGHT AND MY CLAIM WAS WRONG

I said a real attempt had been admitted. It had not: zero admissions, no runtime,
and the episode `attempt_id` that appeared in cleanup accounting exists BEFORE a
worker admission. The identity in the cleanup list established nothing. That
claim is withdrawn.

THE CONFIRMED BLOCKER, FIXED. The manager's deferral said exactly what was wrong:
"no worker this deployment configures for the 'implementation' stage can serve
Job 'job-a': {'implementation-worker': ['the workload profile', 'the workload
profile digest']}". `submission_document` requested
`accepted['profile_name']/['profile_digest']` -- the FRESH workload -- while
`worker_deployments` offered `CONTEXT_PROFILE_NAME` and the certified profile's
`runtime_profile_digest`. `workload_profile(profile)` is now the single source
both documents read, and `held_packet` refuses the pair when the stages request a
profile no configured worker offers -- a cross-document check, because neither
document alone was wrong.

## Where the run reaches now

    admissions        {'implementation': 1, 'review': 0}   (was 0 and 0)
    provider turns    1 attempted
    stage states      implementation 'exceptional', review 'blocked'
    stopped           'serving-failed'
    serving_failure   AttributeError: 'NoneType' object has no attribute
                      'document'

## The exact command

    cd /home/sl/src/baton/work/records/2026/09/finding-v12-managed-session-resume
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/home/sl/src/baton/v12/python/src:/home/sl/src/baton/v12/python \
    /home/sl/.local/state/baton-v12-venv/bin/python -B -c \
      "import connected_packet_trace as c
       w = c.ConnectedPacket(); w.setUp()
       try:
           held, outcome = w.run_packet(dispositions=['accepted'])
           print(outcome['stopped'], outcome['serving_failure'])
       finally:
           w.doCleanups()"

## The one open question, localized

`serving_failure` is the scenario hook's own fault, not the manager's: the hook
calls `self.mounted(held.composed, 'implementation', attempt)`, which reaches
`worker._adopted({...}).document`, and `_adopted` answered None -- so at the
moment the projection reads `waiting`, this run's attempt has no ADOPTED LAUNCH
for that worker to mount. The accepted trace mounts successfully at the same
projection state, so the difference is between the two paths into `waiting`: the
gate this supervisor wraps admits, claims and launches, and only `admit` is
recorded as an admission in the outcome. The next step is to establish whether
the claim/launch happened for this attempt and, if not, which of the gate's three
calls the manager did not reach -- reading the canonical status BEFORE the
shutdown closes the gate, as the review directs. No scheduler change, no extra
sweep and no raised step limit: the previous blocker was a real refusal and this
one is to be read, not masked.

## A supervisor reporting gap this found, fixed here

`serving_failure` was appended to `held_because` only when the result was not
already FAILED, so the one line naming WHY the loop stopped was dropped exactly
when a reader needed it. It is recorded in the outcome unconditionally now, and
that is how the diagnosis above was obtained at all.

## What the run has NOT reached

No provider child ran (`child_diagnostics()` is empty), no verdict was recorded,
and no context save or restore happened. The four asserted endings remain owed.

## Honest boundaries of this fixture

`ConnectedPacket.serving` reproduces the packet's preparation with INDIVIDUAL real
owner API calls -- `configure_workspace_storage`,
`context_delivery.configure_context_storage`, `certify_context_profile`,
`authorize_qualification_run` -- rather than invoking `baseline.prepare` itself.
The acts are the real ones and the grant is minted in disposable stores only; what
is NOT exercised is `baseline.prepare`'s own composition of them, and the
installation seam (`tools.bootstrap`) is simulated by writing the two instance
facts `bind` reads. The completed proof should either drive `baseline.prepare` or
keep this boundary recorded exactly as here.
