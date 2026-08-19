# Finding: run readiness for every configured Codex participant

## Observation — 2026-08-18

The projection-12 deployment manifest configures two Codex targets,
`baton-reviewer` and `baton-tuner`, but launches only one Baton readiness
producer: `baton.codex` to `baton-reviewer`. A poke addressed to
`baton.tuner` remains pending even though the Codex app server, dispatcher,
and tuner thread are healthy.

The dispatcher resumes a target thread and accepts forwarded events; it does
not poll Baton on that participant's behalf. Each Codex-backed participant
therefore requires its own `codex-baton-bridge` process with a unique
participant and target. Sharing `baton.codex` would violate the one-active-
readiness-path rule and would use the wrong identity.

## Confirmed requirement

- Add a lifecycle-owned readiness service for `baton.tuner` targeting
  `baton-tuner`.
- Preserve the existing independent `baton.codex` producer.
- The manifest must reject duplicate participant ownership as it does today.
- Prove a tuner poke is forwarded, answered through canonical Baton, and does
  not create duplicate delivery to the reviewer.

## Acceptance boundary

Update the deployment/example lifecycle topology and focused regressions as
needed. A one-shot tuner producer may be used only as a recorded cutover
canary; the durable correction is lifecycle ownership through `just start`.

## Implementation revalidation — 2026-08-19

The stable `/home/sl/baton-v11` locator resolves to the `aba69d0` coordination
home. Its dispatcher configuration already contains two distinct targets:
`baton-reviewer` binds `baton.codex`/`rview`, while `baton-tuner` binds
`baton.tuner`/`tuner`. The lifecycle manifest and healthy owned state contain
only the reviewer-side `codex-readiness` process; neither contains a tuner
producer. Canonical poke 13 to `baton.tuner` is still pending, matching the
reported failure.

The durable manifest correction is a separate
`codex-tuner-readiness` service with `participant: baton.tuner`, the same
canonical Baton binary/config and event socket as the reviewer producer, and
`--target baton-tuner`. Both producer services depend directly on the
dispatcher. Downstream ACP services may depend on both so the declared startup
order does not advance past an incomplete Codex readiness set. The controller's
existing unique-participant validation remains the fail-closed ownership gate.

The current owned set is healthy and will not be restarted by implementation
or automated tests. A source one-shot tuner producer may forward the already
pending poke as the cutover canary; its exact output, the canonical answer, and
target-specific dispatcher evidence must be recorded before handoff. The live
manifest change prepares the next reviewed lifecycle restart rather than
silently adopting a sixth process into the current five-service state.

## Implementation evidence — 2026-08-19

The checked-in example and the deployed `aba69d0` manifest now declare
`codex-tuner-readiness` with the canonical `baton.tuner` participant and
`baton-tuner` dispatcher target. The example regression proves the reviewer
and tuner paths use distinct participants and targets, share only the event
socket, start after the dispatcher, and still fail closed when a duplicate
participant is introduced. The setup guide now describes one readiness
producer per configured Codex participant.

The live canary is recorded in both authorities. Canonical poke 72 was asked
at `2026-08-19T12:25:33Z`; the dispatcher logged only `baton-tuner`
`v11-action-ready` events at `12:25:40.252Z`, with no reviewer event at that
timestamp. `baton.tuner` answered the poke through canonical Baton at sequence
88, and the old pending poke 13 became superseded. The three tuner events are
the three ready tuner-routed Work items, not duplicate delivery to the
reviewer.

No lifecycle restart was performed. The original five PIDs remain unchanged,
only the reviewer readiness producer is currently durable, and `just status`
truthfully reports the edited six-service manifest as `partial-or-stale`: the
five existing services are `configuration-changed` and the new tuner service
is stopped. This is the expected pre-review state; the next approved lifecycle
restart must establish the durable sixth process.

Focused verification passed:

- `tests/work/test_w20_infrastructure_lifecycle.py`: 46 passed.
- `tools/codex-event-bridge` `npm test`: 46 passed.
- Deployed-layout packaging regression: 1 passed.
- `git diff --check`: clean.

The full `just test-v11` gate was attempted against the shared tree: 1,820
tests passed and 136 failed. The failures are in concurrent, unrelated W17
projection/TUI changes (for example, the participant-actions header test sees
an empty breadcrumb), not in the W22 lifecycle files. W22 therefore returns
with its focused and packaging gates green and the unrelated full-tree gate
failure called out for independent review rather than modifying application
code outside the tuner assignment.
