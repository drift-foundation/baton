# Finding: the Codex readiness bridge refuses the projection-5 candidate

## Parent

`finding-v11-messaging-cutover-gate` — discovered while independently
reviewing W179's approved projection-major correction.

## Observed

W179 advances Baton's JSON projection from 4.x to 5.0 because ordinary Work
message counters change meaning and the recursive breakdown changes shape.
The standalone `codex-baton-bridge` deliberately accepts only projection 4.x
minor 3 or later:

```text
projection 4.3 -> accepted
projection 4.7 -> accepted
projection 5.0 -> refused
```

That was correct for the deployed projection-4.3 candidate. It means the next
immutable projection-5 candidate cannot wake Codex unless the external bridge
is certified for the new envelope first. Starting the new Baton binary without
this correction would make the coordination authority usable interactively
but silently sever Codex readiness.

## Required correction — 2026-08-16

- Certify `codex-baton-bridge` against projection 5.0's participant-action
  envelope and require that major honestly.
- Do not weaken the refuse-not-guess validation of protocol, participant,
  authority, snapshot, timeout, action kinds, locators, or action-key
  agreement.
- Do not add a projection-4 alias or compatibility workaround to the new
  candidate. The immutable projection-4.3 deployment retains its matching old
  bridge; the new source/deployment pair speaks projection 5.
- Keep the bridge an external Codex integration. Nothing Codex-specific moves
  into Baton protocol or the Baton distribution.

## Acceptance

- A real projection-5 `wait` envelope validates and forwards each typed action
  exactly once.
- Projection 4.x, missing/malformed versions, and inconsistent action payloads
  refuse without forwarding.
- Participant/authority isolation, reconnect, deduplication, `--once`, and the
  one-consumer rule remain covered.
- Operator documentation and error text name projection 5 rather than the
  superseded 4.3 contract.
- The Node bridge suite and complete v11 gate pass before a new immutable
  candidate is launched.
