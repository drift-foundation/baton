# Plan: manager agent-session and runtime adapter protocols

1. [done 2026-08-24] Create this dossier and revalidate the frozen
   worker-control, agent-session and assignment-state contracts and the closed
   W4 record against the current tree. Recorded in `FINDING.md`: three
   vocabularies (runtime axis, session state, posture) that must not be
   collapsed; the deliberate asymmetry between the consent and execution
   runtime enums; and what W4 already ships, so this Job consumes it rather
   than restating it.
2. [blocked on W6592] Define the agent-session state machine over the frozen
   `sessionState` vocabulary, with consent and execution as distinct axes and
   `posture` as its own closed value. It hangs off W6592's public composition
   boundary rather than beside it, which is what the dependency is for.
3. [blocked on item 2] The adapter protocol contract: what an agent adapter
   must answer, typed, with **positive absence of a session** distinguished
   from an absent runtime — an agent that is gone and a container that is gone
   are different facts and the manager acts differently on each.
4. [blocked on item 3] Certified typed observations, effectively-once operation
   identities and restart reconciliation, reusing W4's journal rather than
   adding a second one.
5. [blocked on item 4] Cancellation ordering — fence, then agent, then runtime —
   preserved exactly as `request_cancellation` already orders it, with the
   session's own quiescence added without reordering the two that exist.
6. [blocked on item 5] Tests, evidence and independent review.

## Note on scope, for whoever routes this next

The title is broader than the gap. The runtime axes, their transitions and
their journalled observations are **already built** in W4 and green. What is
missing is the agent-session half and the adapter protocol document. Item 1
records the measurement; a reviewer may want to narrow the title to match it
rather than leave the Job looking larger than it is.

## Implementation — 2026-08-25

Status: **implemented and verified; awaiting independent review.** W6592 closed
satisfying, so items 2–6 were unblocked and are done.

2. [done] The agent-session state machine over the frozen nine, with consent
   and execution as distinct axes and `posture` as its own closed value.
   `sessions.SESSION_SUCCESSORS` is the §7.3 table; `unknown` is terminal and
   never becomes `closed`; `satisfies_runtime_quiescence_gate` always answers
   false and proves its argument rather than ignoring it.
3. [done] The adapter protocol contract — `AGENT_ADAPTER` (two operations) and
   `SESSION_OBSERVATIONS` (two closed SHAPES), with positive session absence
   distinguished from an absent runtime by a third recovery-evidence kind.
4. [done] Certified typed observations, an effectively-once opening identity
   derived from `(attempt, posture, intent)`, and `reconcile_agent_session` as
   the session half of restart reconciliation. W4's journal is reused; no
   second one was added.
5. [done] Cancellation ordering preserved exactly — fence, then agent, then
   runtime — with the session's own announcement added where the runtime
   axis's already was.
6. [done] Tests and evidence: `tests/manager/test_sessions.py`, 73 cases; the
   boundary inventory's ownership, probe and witness tables extended for every
   new entry; the text sweep's table extended for every new exported callable;
   the declared-operand list extended. `evidence/gate-baseline-2026-08-25.txt`
   and `evidence/gate-after-2026-08-25.txt` bound what this slice changed.
7. [next] Independent review.
8. [required — approver decision 2026-08-25] Extend the not-yet-certified
   agent-adapter contract with two distinct operator interrogations: `probe`
   for immediate typed control-plane observation without a model turn, and
   `inquire` for a queued conversational request with separate delivery
   acknowledgement and correlated model answer. Bind both to the exact
   assignment/session/operation identity and deadline; journal and expose
   queued, delivered, answered, timed-out, unreachable and runtime-absent
   outcomes without treating timeout as cancellation. The Worker Manager,
   never the worker, publishes conversational answers into Baton.

## Note on scope, resolved

The earlier note asked whether the title should narrow to match the measured
gap. It was not narrowed, and it did not need to be: the runtime axes W4 ships
are CONSUMED here rather than restated — the cancellation ordering and the
observation journal are W4's, extended — and the agent-session half plus the
adapter protocol are what this slice built. A reviewer expecting runtime axes
will find them where they already were, referenced.
