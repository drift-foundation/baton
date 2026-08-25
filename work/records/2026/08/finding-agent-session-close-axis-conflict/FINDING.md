# Finding: reconcile agent-session close with the observation axis

Discovered during W4/W2929 agent-session-axis review on 2026-08-23.
Canonical Baton Work: W771 (`2b077949-W771`).

## Observed

The frozen agent-session successor table and the signed-off session close
path disagree:

- Frozen ACP SPEC §7.3 and `evidence/acp_boundary_model.py` define a monotone
  nine-state observation axis. `not-started`, `prompting`,
  `cancel-requested`, and terminal `unknown` do not permit `closed` as a
  successor. §3.3 explicitly says `unknown` stays terminal because promoting
  it would record knowledge that was never observed.
- `v12/src/worker_manager/agent_session.mjs::closeAgentSession` updates every
  non-closed row directly to `closed`, bypassing the successor table.
- The retained W4 probe demonstrates four forbidden transitions:
  `not-started -> closed`, `prompting -> closed`,
  `cancel-requested -> closed`, and `unknown -> closed`.
- Existing signed-off session tests use `closeAgentSession` on a freshly
  opened `not-started` row to release the posture, so changing the function to
  obey the frozen table would intentionally invalidate an existing contract
  expectation rather than merely repair an untested path.

There is a second half to the conflict. The partial unique index
`agent_sessions_one_open_per_posture` frees a posture only when state is
`closed`; its durable comment explicitly says `unknown` does not free it.
Under the frozen successor table, a transport/session that ends before
initialization can move only `not-started -> unknown`, after which the posture
can never open another epoch. A literal local correction therefore strands
the posture rather than producing a coherent lifecycle.

## Confirmed boundary

This is an owning contract decision, not permission for W4 to pick whichever
existing artifact is convenient. Until ruled, the new session-axis module
must continue to refuse every forbidden edge and `closeAgentSession` must not
be silently rewritten or its signed-off cases weakened.

The ruling must preserve these distinct facts:

- `closed` asserts that terminal turn facts were observed for every turn the
  epoch started;
- `unknown` records absence of that knowledge and must never be relabelled as
  an observation;
- one posture cannot host two possibly live provider sessions; and
- a failed or never-completed initialization needs a defined recovery path
  rather than permanently stranding the posture by accident.

W4 cannot be considered an integrated monotone session lifecycle while a
public close path bypasses the axis. Other independent W4 slices may proceed,
but final composition and closure require this ruling and its implementation.

## Open decision

Choose and specify one coherent lifecycle. Candidate boundaries include a
distinct manager-close/order state or fact, a separately proved provider
absence/re-identification gate that releases an `unknown` posture without
calling it `closed`, or an explicit successor-table correction backed by a
changed meaning of `closed`. Any ruling must append an explicit correction or
supersession to the owning ACP record, update the model/schema/store index and
all product entry points together, and migrate existing close assertions only
with case-specific authority.

## Confirmed ruling — 2026-08-23

**Confirmed by Slawomir.** Preserve the provider-observation axis exactly as
evidence. `unknown` remains terminal and is never promoted to `closed` merely
because the manager ordered a close, lost transport, reached a deadline, or
wants to reuse the posture.

Posture occupancy is a separate manager-owned axis:

```text
available -> occupied -> recovery-required -> available
```

Opening a session atomically occupies the posture. A normally observed
provider-session close may return it to `available`. Ambiguity moves it to
`recovery-required`; silence and elapsed time never recover it automatically.
An explicit recovery must positively establish that the old provider session
cannot still act before returning the posture to `available`.

For the OCI reference runtime, the trusted manager recovers the slot as soon
as it verifies that the exact assignment container is stopped or absent. The
request to stop is not itself proof; the adapter must observe the exact
container identity no longer running. The runtime-neutral contract records
this as positive runtime-quiescence evidence rather than making Docker a
protocol concept.

Recovery does not rewrite observation history. The durable result may
therefore be:

```text
observation: unknown
runtime: stopped
slot: available
outputs: retained pending disposition
```

Stopping the container recovers execution capacity but does not implicitly
discard its filesystem, accept its output, or choose salvage/retention. Those
remain independent disposition decisions.

Implementation must separate the unique-posture constraint from
`agent_session_state`, replace the unconditional `closeAgentSession` state
rewrite, and update the formerly signed-off `not-started -> closed` tests with
the case-specific authority supplied by this ruling. Positive normal-close,
never-submitted, transport-loss, exact-container-stop, stale-container-id,
retry, crash/restart, and retained-output cases are required.

## Independent review — 2026-08-23

**Observed; changes requested.** Schema 14 correctly separates the two axes,
but its slot mutations do not yet bind an event to the epoch or runtime fact
it describes. Delayed epoch-1 ambiguity, recovery, or close can move or free
an occupied epoch-2 slot. A `provider-session-closed` label releases a session
whose durable observation is still `ready`, and any non-empty runtime identity
is accepted without comparison to the attempt's attached `runtime_id`.
Finally, the product transport-loss entry point records `unknown` but leaves
the same slot `occupied` rather than moving it to `recovery-required`.

The correction must make epoch identity part of every ambiguity and release
CAS (including idempotent retries), bind provider-close recovery to the same
epoch's durable `closed` observation, compare runtime evidence with the exact
durable assignment runtime, and compose transport loss with the slot movement
in an atomic or explicitly restart-repairable way. Recovery must continue to
leave observation and outputs unchanged. Five additive regressions preserve
these boundaries in `v12/test/worker_manager_posture_slots.test.mjs`.

The stale signed-off title `W2929: only CLOSING frees the posture` may be
renamed under this review's case-specific authority; its behavioral assertions
must be retained and strengthened rather than weakened. Full analysis and
verification are in `review-2026-08-23T18-49-02Z.md` and
`evidence/review-round1-2026-08-23.txt`.

## Independent re-review — 2026-08-23

**Observed; one P1 remains.** The first correction closes all three round-1
findings and all five retained regressions pass. However,
`handleTransportLoss` rolls its exact-epoch `unknown` observation back when
the separately durable slot fact has already advanced: a retry after positive
recovery refuses on `available`, and a delayed epoch-1 report refuses on an
epoch-2 slot and leaves epoch 1 falsely `ready`.

The strict slot mutation is correct to reject both movements; the product
composition is not correct to discard the independent observation with them.
As the delayed-close path already does, transport loss must durably record the
old epoch's observation while moving the slot only when that epoch still owns
an applicable slot. Two additive regressions preserve retry-after-recovery and
delayed-report/newer-epoch cases. Full analysis and verification are in
`review-2026-08-23T19-28-58Z.md` and
`evidence/review-round2-2026-08-23.txt`.

## Independent sign-off — 2026-08-23

**Signed off.** The second correction closes the remaining P1. An exact
epoch's transport-loss observation now lands independently of whether its
posture slot is still occupied by that epoch, already recovered, or occupied
by a newer epoch. Only an applicable same-epoch occupied slot moves; both
endings report the occupancy that actually holds; and the strict direct slot
API remains strict.

The current W4 integration and `v12/src` consumer sweep find only the intended
open, normal-close, and transport-loss compositions, with no adapter consumer
deriving posture capacity from provider observation. This discharges plan
item 5 on the reviewed tree. Posture slots are 25/25, agent sessions 18/18,
and the observation axis 16/16. The full v12 gate is 646/652; all W771 cases
pass and the six failures belong to W543, W641, and W4. Review and evidence:
`review-2026-08-23T19-48-06Z.md` and
`evidence/signoff-round3-2026-08-23.txt`.
