# HOLD — this packet is prepared and MUST NOT BE STARTED

Recorded by `baton.claude`, claim333707, on the instruction of
`decisions/review-333691.md` item 1.

This is not a caution. Steps 0 through 3 of `OPERATOR.md` (verify, stage,
bootstrap, bind) are authorized preparation and produce no execution. **Step 4,
start, is held.** The hold is lifted by an owner decision on the shared
authoring prerequisite, not by this packet, not by a reviewer and not by the
passage of time.

## The blocker, and it is shared rather than this packet's own

This packet selects the same authoring vehicle as sibling W333485's
`execution-333532`: the `baseline.py` supervisor from
`work/records/2026/09/finding-v12-single-implementation-proof`, pinned here at
the declared base as `c1b0a10e609503df0ba7ebdc7455cc8518c9175882edd185b65f20c342c4bd2f`.

That supervisor has **no expiry-reclamation path at all**. Revalidated
read-only this claim against the pinned base bytes:

- `baseline.py:1207` calls `serve(job, gate, clock=clock, sleep=sleep,
  should_continue=should_continue, interval=1)` — with **no `reclaim=`
  argument**.
- `job_manager/manager.py:833` declares `reclaim=None`, and `:859`/`:879` run a
  reclaim pass **only** `if reclaim is not None`. So on this vehicle no reclaim
  pass runs on any tick.
- Compare `tools/job_manager.py:_serve`, the native serving entry point, which
  supplies `reclaim=getattr(operations, "reclaim", None) or _reclaiming(...)`.
  The native synchronous reclaim is **not a proved drop-in replacement** for
  this supervisor's loop.
- `baseline.py:1196` checks the overall bound only **between** passes, and
  `:1252ff` reaches cancellation only after the serving loop returns, so a
  blocking pass is not preempted.

## Why that blocks a 3600/4800 start

The requested bounds are provider turn 3600s inside a 4800s total, while the
governed workspace lease is `tokens.LIFETIME_SECONDS = 900` with no renewal at
this base. On a vehicle with no reclaim pass, an expired generation is **not
withdrawn, not stopped and not returned** — so the start would run roughly
3900s past expiry with its resource governance unenforced. That is the opposite
failure from the native pilot's, and it is still a failure.

## A correction to the superseded packet

`../execution-333504/OPERATOR.md` warned that the native pilot's 903-second
termination might stop the authoring turn at 900 seconds. **That claim is
withdrawn.** It transferred the native `tools/job_manager.py` reclaim's
behaviour to a vehicle that does not have it; `decisions/review-333691.md`
item 1 names the implication unsupported, and the code above is why. The
superseded packet is preserved unchanged with that error in it;
`TASK.md`'s honesty section and this document carry the correction.

## Reused evidence — not re-run

`decisions/review-333691.md` is explicit: reuse W333485's falsification, do not
repeat it and do not seek separate launch approval for this packet. Snapshotted
here:

| snapshot | source |
| --- | --- |
| `decisions/sibling-review-333618.md` | `work/records/2026/10/finding-v12-serving-token-renewal/review-2026-10-19T16-34-00Z.md` |
| `decisions/sibling-blocker-RESULT.json` | `…/evidence/review-333618/RESULT.json` |
| `decisions/sibling-blocker-SUMMARY.json` | `…/evidence/review-333618/SUMMARY.json` |

That reviewer's probe, over the same bounds this packet requests, drives eight
simulated 600-second blocking sweeps and reaches its first cancellation at
**4808 simulated seconds** with cleanup held — against a 900-second lease. Its
manifest is `a44b24d8ea66882b8ca90d8cbdd51095d7606cd5135fe8ad8e86c44684e8c771`
over three verified files; command 0.260102891s.

Its stated limitation travels with it and is not softened here: the
scheduling, status and cancellation boundaries are **simulated**. It disproves
a supervisor timing guarantee. It does **not** execute real tokens, Docker, a
provider, Job admission or positive cessation, and it claims no exhaustive
search and no universal impossibility.

**No falsification was re-run this claim.** The only thing done here was the
read-only revalidation of the four code locations above.

## What would lift the hold — none of it this packet's to grant

`decisions/sibling-review-333618.md` records two routes, both owner decisions
and both explicitly *not* reviewer-granted authority:

1. one narrow temporary exception to v12-only execution, scoped to isolated
   filesystem implementation and deterministic verification of the authoring
   enforcement prerequisite itself; or
2. selection of an already independently accepted authoring vehicle with exact
   provenance and evidence for blocking-interference enforcement.

A known unproved packet is not recommended as that vehicle. Routine
preparation may **not** silently patch the host to bypass the bootstrap
dependency, and this packet does not.

## What this hold does not block

- **This packet's preparation**, which is complete and sealed. Diagnostics
  preparation continues independently of the sibling's production renewal
  outcome; no dependency on that whole outcome is warranted merely because the
  authoring prerequisite is shared.
- **This correction's verification design.** `TASK.md`'s cases are
  deterministic checks inside the private checkout against fake engine and
  provider boundaries; they do not need the supervisor to run a reclaim. The
  hold is about whether it is safe to *start* an authoring run, not about
  whether the task is verifiable once one is.

## Canonical state when this was written

W333485 was at `last_change_seq` 333725, `phase: active`, claimed by
`baton.rvpc` at `baton.bug`. `decisions/review-333691.md` records it as
queued to `baton.decide` at 333692 with no execution exception granted; it has
moved since, and the owner decision remains pending either way. **Read current
canonical state rather than this paragraph** — it is a timestamp, not a gate.
The gate is the owner's decision.
