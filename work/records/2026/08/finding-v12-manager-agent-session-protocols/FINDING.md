# Finding: the manager's agent-session and runtime adapter protocols

Canonical Baton Work: W6627, a separately scheduled M2 manager prerequisite
from the closed W4 and W5 PLAN item 8. Dossier created 2026-08-24 by
`baton.claude` on claiming, because the assignment requires one before
implementation.

## Confirmed boundary

The Python agent-session state machines and the manager-owned runtime/agent
adapter protocols: distinct consent and execution axes, certified typed
observations including positive absence, effectively-once operation identities,
restart reconciliation, cancellation ordering, and the public composition hooks.

**Not here:** OCI commands, image or provider code, output acceptance, retention
and §13 surfaces. Those are W6632, W6633, W6628, W6629 and W6630.

## Revalidated against the current tree, not taken from the brief

**The frozen contracts exist and say what the assignment says they say.**

- `worker-control-1.0`'s `runtimeAttemptManifest.states` carries ten axes, and
  the two this Job owns are already separate and already differently shaped:
  `consent_runtime` admits `not-started, running, quiescent, uncertain,
  destroyed`, and `execution_runtime` additionally admits `start-requested,
  cancel-requested, stopping`. **The asymmetry is the topology written into the
  contract**: a consent container is never *asked* to start work or to be
  cancelled mid-turn, so it has no state for either.
- `agent-session-1.0` carries a *different* vocabulary again — `sessionState` is
  `not-started, initializing, ready, prompting, turn-ended, cancel-requested,
  agent-quiescent, unknown, closed` — with `posture` closed to `consent,
  execution` and `stateObservation` requiring `state` and `observed_at`.

**So there are three vocabularies, not one**, and that is the first design fact
this Job has to get right: the RUNTIME axis (is the container up), the SESSION
state (is the agent inside it ready to be prompted), and the POSTURE (which of
the two containers this is). Collapsing any two would be the "two live sources of
truth" defect this campaign keeps finding.

**What W4 already built, which this Job must consume rather than restate:**
`worker_manager.AXES` is exactly the ten frozen axes and `TRANSITIONS` already
carries the per-axis map — `consent_runtime` transitions are already pinned,
including `uncertain -> running | quiescent` and `destroyed` as terminal. W4 also
already ships `observe`, `record_attempt`, `activate_assignment`,
`request_runtime_start`, `reconcile_runtime` and `request_cancellation` with
effectively-once operation identities and the fence-before-stop ordering.

**The gap this Job actually fills** is therefore narrower than the title
suggests and should be stated plainly: the runtime axes and their journalled
observations exist; the **agent-session** state machine, its certified
observations, and the *adapter protocol contract itself* do not. Nothing in the
Python distribution defines what an agent adapter must answer — `attempts.py`
calls `agent.cancel(...)` and types the answer, but there is no protocol
document, no session axis, and no positive-absence evidence for a session as
distinct from a runtime.

## The M6617 topology, preserved

One logical `runtime_attempt_id` may span sequential consent and execution
containers. Consent is quiesced or destroyed **before** activation and is never
promoted. The two axes already encode this and the entry point W6633 built
already refuses promotion; this Job must not add a path that reintroduces it.

## Dependency

**W6627 → W6592.** These protocols must consume the completed contracts
inventory and public composition rather than defining a second public boundary.
W6592 is open with changes requested, so this Job cannot start.

## Acceptance

- Consent and execution session axes distinct, with the frozen `sessionState`
  vocabulary and no collapsing of runtime, session and posture.
- Certified typed observations, including **positive absence** of a session as
  distinct from an absent runtime.
- Effectively-once operation identities and restart reconciliation.
- Cancellation ordering preserved: fence, then agent, then runtime.
- Public composition hooks on W6592's boundary, not beside it.

The implementer creates and exclusively owns `PROGRESS.md`.

## Implementation decisions — 2026-08-25

Recorded by the implementer under the claim that built this slice. W6592 is
closed satisfying, so the dependency this Job waited on is discharged and the
public composition these protocols hang off is the one that was accepted.

**POSITIVE SESSION ABSENCE IS A THIRD EVIDENCE KIND, and it is an addition
beyond the frozen Node host.** `posture_slots.mjs` recognises two ways a
posture may be recovered — `provider-session-closed` and `runtime-absent` —
and this Job's acceptance requires that positive absence of a SESSION be
distinguishable from an absent runtime. Those two cannot express it: an agent
process can die inside a container that is still running somebody's code, and
before this the only way to recover that posture was to destroy a container
doing nothing wrong. `session-absent` is therefore added, proved against the
exact `provider_session_id` the epoch durably holds, and it recovers the
posture while satisfying no runtime gate. **This is a divergence from the
frozen host and the host should follow**; it is written here rather than left
for a reader to discover from a diff.

**The agent adapter contract is `AGENT_ADAPTER` and `SESSION_OBSERVATIONS`.**
Two operations — `cancel`, which existed as a call with nothing behind it, and
`observe_session`, which is new — and a closed set of answer SHAPES rather than
of names. There is deliberately no `unknown` or `unreachable` member: an
adapter that could not tell reports nothing, which is what transport loss is
for, and giving "I could not look" a place in that set is how it would come to
be read as "there is nothing there".

**Opening a session takes a caller-supplied `intent`.** The effectively-once
identity is derived from `(attempt, posture, intent)`. It cannot be derived
from the attempt and posture alone: two sessions in one posture are a real
thing — the second begins after the first slot is recovered — so an identity
without the caller's own intent would replay the FIRST session's answer to a
deliberate second opening. This is the same shape `claim_operation_id` already
uses, and it is what makes a restart mid-open name the act it performed
instead of burning a second epoch.

**Cancellation gained a fourth reported axis and reordered nothing.** The
session's `cancel-requested` is announced where the runtime axis's own
announcement already is — before the agent is asked — so fence, then agent,
then runtime is untouched. The announcement never writes `agent-quiescent`:
that is what a provider was OBSERVED to reach. A session already past the
point where §7.3 permits `cancel-requested` does not veto the cancellation,
because refusing the whole act because the conversation had ended would leave
a fenced runtime running.

**`boundaries.generation` is not the rule for a session epoch.** It counts
from zero and is the ASSIGNMENT generation's; the frozen `positiveInt` this
member is typed as counts from one. `posture_slots._epoch` owns it directly,
and the `generation` call written there first was measured as unreachable and
deleted rather than left standing.

**Not in this slice, and named so its absence is deliberate:** turns and their
deadlines, event normalization, agent-origin routing, and the App Server's
provider binding. The brief names none of them and the acceptance names none
of them; this slice answers what a session IS, what may be observed about it,
and what a manager does when the answer is nothing.

## Confirmed operator interrogation split — 2026-08-25

The v11 conversational `poke` conflates two facts: whether the adapter/session
can be observed now, and whether a model has accepted and answered a new
conversational request. V12 exposes them as different manager-owned
operations before the agent-adapter contract is certified:

- `probe` is an immediate control-plane observation. It does not require or
  consume a model turn. It reports the exact runtime, session and assignment
  identity, current session state, last activity and available provider/runtime
  diagnostics through a closed typed answer.
- `inquire` is a conversational request to the agent. The adapter first
  acknowledges whether the request is queued or delivered; the eventual model
  answer is a separate correlated result at a safe turn boundary.

Both operations bind the exact assignment generation, posture-specific
session identity, effectively-once operation identity and manager-observed
deadline. Their observable outcomes distinguish queued, delivered, answered,
timed out, adapter unreachable and runtime absent. A timeout is an observation,
not implicit cancellation or authority to discard work.

The worker receives no Baton or SQLite capability. The Worker Manager journals
the interrogation and publishes any conversational answer into Baton with its
participant and operation provenance. A committed Baton request is therefore
never represented as proof that the adapter or model saw it.

## Operational finding — the v12 Python gate was already red

**Observed 2026-08-25, before any edit under this claim:** the v12 Python
distribution's own gate fails with 13 failures at the tree as it stands. Every
one names `oci.py` or `workspaces.py` — W6632's and W6631's modules — across
`test_oci`, `test_boundary_inventory` and `test_dependencies`. The exact list
is `evidence/gate-baseline-2026-08-25.txt`.

This is reported rather than worked around. It is not this Job's to fix, and
it means "the gate is green" is not a sentence this slice can honestly say —
so the claim it makes instead is the one it can prove: `evidence/
gate-after-2026-08-25.txt` is the same list minus one, diffable against the
baseline, with nothing added.
