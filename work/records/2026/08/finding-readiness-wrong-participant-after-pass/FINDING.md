# Refuse readiness wakes for the wrong routed participant

## Observed — 2026-08-20

After `baton.codex` passed W1207 and W1217 to `baton.impl`, the Codex readiness
path emitted `v11 Work ... is ready and unclaimed for baton.codex`. Canonical
`detail` immediately showed both Works queued at endpoint `baton.impl`, with no
Handler and no `claim` transition for `baton.codex`. Attempting the first wake's
claim correctly failed authorization.

The same false wake occurred for W1151 while it was still held by
`baton.claude`; canonical detail showed `active`, Handler `baton.claude`, and
Route `baton.impl`. A later wake became legitimate only after K actually passed
the Work to the reviewer.

The defect then reproduced on its own Work. At sequence 1231 the reviewer
passed W1224 to `baton.impl`; canonical detail showed phase `queued`, no
Handler, endpoint `baton.impl`, and no reviewer `claim` transition. The Codex
readiness path nevertheless emitted W1224 as ready and unclaimed for
`baton.codex`. This removes any ambiguity about the affected Work's content or
priority: the stale prior-participant episode survives the pass itself.

## Confirmed boundary

- A readiness Work action is addressed only to a participant that can claim
  that exact current episode under the canonical Route.
- Passing Work to another endpoint removes it from the prior participant's
  actionable set atomically.
- Claimed Work never appears as `ready and unclaimed` to another participant.
- A stale queued delivery must be revalidated against the exact Work episode
  immediately before emission and dropped when Route, Handler, phase, or
  episode no longer matches.
- The CLI authorization refusal remains the final fail-closed boundary; this
  finding removes the misleading wake rather than weakening authority.

## Acceptance boundary

- Reviewer-to-implementer pass never wakes the reviewer for the implementer's
  queued Work.
- While the implementer holds it, no other participant receives an unclaimed
  Work wake.
- A real implementer-to-reviewer pass wakes the reviewer exactly once for the
  new episode.
- Rapid pass/claim/pass races cannot leak an earlier episode to the wrong
  participant.
- Readiness remains read-only and carries no inferred routing authority.
