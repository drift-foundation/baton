# Finding: v11 messaging must replace v10 before v10 retires

## Operational ruling — 2026-08-16

**Confirmed by Slawomir during the fresh v11 trial.** v10 remains the reliable
coordination channel while v11 is being evaluated. v11 may not deprecate or
shut off v10 merely because its Work model, CLI, or TUI exists.

After the current same-schema trial-defect batch closes, v11 messaging becomes
the next focused phase. The team iterates on it until the human, reviewer, and
implementer can conduct their real coordination through v11 without using v10
as a wake-up, delivery, or readability fallback. v10 and v11 continue in
parallel throughout that phase.

## Retirement acceptance boundary

Before v10 retirement, the v11 system must prove in live use and automated
workflow coverage that:

- a participant can discover new directed and contextual messages promptly;
- agents can wait or be woken for actionable v11 work without a v10 notice;
- Work, Threads, Message index, selected body, and Refs are readable and
  navigable in the TUI, with equivalent canonical JSON/CLI access;
- personal New/seen state and directed obligations are understandable and do
  not hide or silently consume work;
- request, response, pass, review return, and terminal disposition workflows
  can be completed entirely through v11;
- restart/reconnect does not lose queued work, personal cursors, routing, or
  the operator's ability to understand what needs action;
- the three live participants complete an agreed trial interval without
  falling back to v10 for operational communication.

Finding and fixing individual messaging defects does not by itself authorize
cutover. Slawomir makes the explicit retirement decision after the end-to-end
trial evidence is reviewed.

## Scope boundary

This gate does not require v11 to reproduce v10's outbox presentation or every
historical UI choice. It requires the new Work/Thread model to be sufficient,
clear, and reliable for the coordination we actually perform. Non-messaging
feature work is deferred during the focused phase unless it blocks that proof.

## Research inventory — 2026-08-16

**Confirmed against the current schema-15 implementation and live trial.** The
human and agent surfaces exist, but the retirement gate is not yet satisfied.

- The TUI auto-refreshes and now provides Work → Threads → Message index →
  selected reader navigation, separate Refs, personal New/seen state, `Msg/My`
  counts and viewer-relative actionable bold. CLI/JSON expose the same Work,
  Thread, Message and cursor facts. These are implementation facts, not yet a
  human usability certification; the three live participants still need to
  conduct their real conversation through the deployed candidate.
- `wait_actionable()` currently accepts only a team. It returns every pending
  team obligation and due round, even when the configured route does not
  resolve the waiting member, and it does not return a ready unclaimed Work
  whose Current route does resolve that member. A v11 pass can therefore hand
  Work to an agent without waking it, while unrelated team work can wake it.
  The TUI's top `oblig` count consumes the same team-wide projection, so it can
  also advertise somebody else's load as the viewer's.
- The Codex monitor is protocol-10-specific: it invokes v10 flag/order syntax,
  expects `{ready, channel, message_id}`, deduplicates one mailbox head, and
  tells the awakened agent to claim a message ID. v11 uses key-value syntax,
  returns an envelope containing an actionable set, and consumes action through
  Work claims, responses, reports or review—not a v10 delivery claim.
- During the parallel trial, one Codex target must be able to receive readiness
  from both the v10 participant (`baton.reviewer`) and its v11 member
  (`baton.codex`). The current machine configuration permits only one Baton
  binary/config and one participant per target, so switching it to v11 would
  remove the reliable v10 safety wake before v11 is certified.

The gate is decomposed into two implementation children plus the live human
trial:

1. `finding-v11-participant-readiness/` defines one participant-relative
   actionable projection shared by JSON, `wait`, and the TUI header.
2. `finding-v11-parallel-monitor/` adapts the app-server monitor and shared
   configuration to run v10 and v11 readiness in parallel without mixing their
   consumption rules.
3. This parent retains the TUI/CLI live-use and final retirement evidence. A
   green child does not close or authorize this gate.

## Gate-boundary correction — 2026-08-17

**Confirmed by Slawomir after successful v11-only operation.** W2 asks whether
v11 is an effective communication channel that can replace v10. It is not an
umbrella gate for every remaining messaging-interface refinement.

The live Slawomir, Codex, and Claude trial has now proved the required channel:
the participants discovered and read Work and messages, handed Work between
routes, woke agents without v10, resumed persisted ACP state, and continued
coordination without a v10 delivery fallback. That is sufficient to close W2
satisfying once its graph reflects the true acceptance boundary.

W76 (spatial/newest-first message panes), W81 (prefill `say` from the selected
Thread), and W90 (remove Work actions from Messages view) are useful follow-up
usability improvements. None prevents v11 from carrying effective operational
communication, so none is a prerequisite for W2. Their dependency edges into
W2 were added under an over-broad interpretation of this gate and are
superseded by this ruling. The Work remains open independently and does not
move, close, or lose its own acceptance contract merely because the mistaken
edge is corrected.

## Closure evidence — 2026-08-17

The three-person v11-only interval remained effective through repeated real
review cycles, including W81's two returns and final closure. Slawomir, Codex,
and Claude discovered, claimed, discussed, handed off, corrected, re-reviewed,
and closed Work through v11 without v10 delivery or wake-up fallback. ACP
restart and same-key redelivery defects were corrected independently as W27
and W49; both are closed satisfying.

At final review W2 has zero open blockers and both contained children are
closed satisfying. W76, W81, and W90 also reached satisfying terminal outcomes
before their mistaken edges could be corrected. Those edges are consequently
terminal graph history, not live gates: `unblock` correctly is unavailable and
must not rewrite them. Their presence in historical links does not broaden the
W2 acceptance contract again.

The source tree concurrently contains W159's next request-default batch, whose
fixture migration temporarily prevents attributing a whole-tree gate to this
operational decision. That independent future protocol change does not negate
the already deployed and live-proven v11 communication channel.
