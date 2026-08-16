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
