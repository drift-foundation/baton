# Reviewer polling reliability and monitor lifecycle

Status: confirmed Codex-runner operational defect; deferred from 1.1 by
Slawomir on 2026-08-11.

## Symptom

The reviewer repeatedly reports that polling is active, but the waiter process is
absent from `/ps`. A turn-owned `wait` process can disappear after returning a
ready result, and a detached wrapper also exited immediately when it treated the
ready-result exit status as fatal. This leaves messages pending until a human
explicitly asks for another poll.

## Impact

The mailbox remains healthy, but communication stalls because readiness does not
reliably lead to a claim. This violates the operating contract that the reviewer
must continuously listen and process every claim promptly.

## Evidence

- Multiple claimed/replied messages were followed by a reported waiter session,
  yet `ps -Af` showed no `wait --participant baton.reviewer` process.
- The shell loop assumed status 3 was the only non-terminal result. In practice,
  `wait` returned status 0 with `{\"ready\": true,...}`; the loop exited on that
  status instead of continuing to the next wait.
- A detached monitor cannot itself wake a new conversational turn or claim a
  message; it must be advisory and its lifecycle must be explicit.

## Contract questions

1. What are the exact exit statuses for timeout, readiness, damage, and usage
   errors, and how must a monitor handle each?
2. How can a persistent monitor surface readiness without consuming or stranding
   claims?
3. What supervisor/deployment mechanism keeps the monitor alive across turn
   boundaries, and how is liveness visible in `/ps`/doctor?

## Scheduling ruling — 2026-08-11

Slawomir deferred this from 1.1 as Codex-specific runner integration that may
eventually be solved by proper monitor support. Preserve the observed Baton
exit-status/level-trigger evidence and the honest external-runner limitation.
Do not add an arbitrary-command wake hook or claim the foreground waiter is a
durable solution. Current reviewer operation continues with one explicitly
verified, turn-owned wait loop.

## Recurrence evidence — 2026-08-11T17:33:34Z

The failure also affects the implementer and can strand an actual claim, not
only delay readiness. `baton.implementer` claimed reviewer message
`111459e5e45765eb52708c971dd17635` at 17:33:34Z as claim
`7bf0cc88808e83f94d711b4ae7f6b1cb`, then the implementer's Codex turn stopped.
At 17:44Z the authority still reported that claim `active` with no terminal
timestamp while the human observed K idle. The message contained concrete
editor-review changes K had not yet answered; this was not an empty queue.

At the same time, the reviewer turn's one foreground loop was continuously
present as a shell plus Baton child, handled repeated timeout exit 3 results,
and claimed the human's 17:44:32Z message at 17:44:35Z. A UI/runner may label a
model blocked in `wait` as idle even though its readiness path is healthy; that
presentation is distinct from the implementer's genuinely stopped turn.

This recurrence sharpens the required boundary: a runner must not allow a turn
to end with an active claim, and read-only readiness alone cannot recover a
turn that already did so. Starting a second waiter is not a remedy; it neither
owns the stranded claim nor satisfies the single-consumer rule. Recovery needs
the same participant's turn resumed or an explicitly authorized claim-recovery
workflow.
