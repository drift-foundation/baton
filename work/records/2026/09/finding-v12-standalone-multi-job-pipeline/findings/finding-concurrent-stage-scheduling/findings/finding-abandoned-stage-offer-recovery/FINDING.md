# Recover abandoned Job-stage offers after restart

Ledger Work: W73629

Parent: `work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-concurrent-stage-scheduling/`

## Observed — 2026-09-02

The Worker Manager correctly abandons an `issued` offer owned by an earlier
manager incarnation because no durable fact proves its bearer was delivered.
The Job manager, however, retains the stage's `admit` receipt, derives the
stage as `offered`, and continues to owe only `claim`. The canonical offer is
now `abandoned-after-restart`, so every claim attempt is an ordinary deferred
precondition and the stage never returns to an admissible state.

The retained reproduction is
`/tmp/w71877-abandoned-offer-repro.py`. Against `efbad19` it reports:

```text
{'recovered': {'abandoned': ['offer:job-a/implementation'], 'recoverable': []}, 'stage_state': 'offered', 'owed': ['claim'], 'offer_state': 'abandoned-after-restart'}
```

This predates W71877's pool implementation. Adding a durable worker
reservation around the existing path would turn the stage wedge into a pool
capacity leak as well.

## Confirmed boundary

An abandoned offer is immutable history and its receipt must not be deleted or
rewritten. Recovery needs a new offered-and-claimed execution episode with
fresh offer and runtime-attempt identities, while the status projection keeps
the abandoned episode visible. The Worker Manager remains the owner of offer
settlement; the Job manager consumes a public canonical offer observation and
decides that a new episode is owed.

W71877 must not hide this by freeing a slot while leaving the stage permanently
`offered`, nor by treating the old offer as live. Scheduler reservation release
may compose the corrected canonical ending once this Work closes.

## Acceptance

- A restart after offer issuance but before acceptance records the old offer
  as abandoned and makes a fresh stage episode admissible.
- The fresh episode has distinct offer, attempt, and assignment identities;
  the old receipt and abandonment remain auditable.
- Reconciliation is idempotent across a second restart and cannot issue two
  live offers for one stage episode.
- A delivered-and-accepted offer remains recoverable and is never replaced.
- Status distinguishes the abandoned episode from the new queued/offered
  episode without storing a shadow copy of offer state.

## Test-change authority

This Work authorizes additive tests and edits under `v12/python/tests/job_manager/`
for abandoned-offer observation, episode replacement, restart races, and
status history. No deletion, weakening, or unrelated test change is authorized.
