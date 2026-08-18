# Finding: Current must name the active claimant

## Observed

The protocol currently projects the routing endpoint as `current` and the
exact claimant separately as `active`. In the live v11 trial this made W104
appear to have a Current worker (`baton.impl`) even though nobody had claimed
it. It also made an active phase look like evidence of execution when it was
only a routed handoff awaiting pickup.

W101 exposed the inverse failure: Claude remained the active claimant while
describing the Work as blocked. The route alone could not tell the operator
whether anybody was actually executing the Work.

## Confirmed decision — 2026-08-17

**Confirmed by Slawomir.** `Current` means the exact participant who presently
holds the Work's authority-backed claim. It is null while the Work is
unclaimed. Routing and execution identity are separate protocol facts:

- `route` is the endpoint whose resolved handlers are eligible and expected to
  claim or otherwise handle the Work, for example `baton.impl`;
- `current` is the exact claiming participant, for example `baton.claude`, and
  is null unless a claim exists;
- `next` remains the optional destination endpoint for the subsequent
  handoff.

This supersedes the *terminology* in the parent finding's earlier “Current and
phase move together on handoff” decision. Its atomic handoff rule remains:
`pass` changes `route` and derives the destination phase in one transaction,
releases the sender's claim, and never claims for the recipient. The recipient
later claims explicitly; only that successful claim populates `current`.

Authorization continues to resolve from `route`, never from the display name
of a claimant. Claim release, pass, waiting, parking, dependency blocking,
terminal close, and recovery clear `current` according to their existing
rules. Configuration changes may change route eligibility but must not rewrite
the identity captured by a live claim.

## Public projection and TUI

Canonical JSON uses structured facts rather than glyphs:

```json
{
  "route": {"endpoint": "baton.impl", "handlers": ["claude"]},
  "current": null
}
```

After `baton.claude` claims the Work, `current` becomes the structured
participant identity. The TUI presents Route and Current separately. An
unclaimed routed Work shows Current as `-` and retains the separately ruled
pickup cue; a claimed Work shows the participant and starts Held from the
claim instant.

The old endpoint-valued `current` and claimant-valued `active` projection must
not remain as two competing meanings. Compatibility aliases would preserve
the ambiguity this change removes. This is a v11 trial schema/projection
change and is exercised with a fresh trial authority rather than migration of
production data.

## Acceptance boundary

- Create, pass, reroute, dependency, waiting, parking, release, close, and
  restart projections preserve the route/current distinction.
- A pass changes route and phase, clears current, and leaves the recipient
  unclaimed.
- A successful eligible claim alone populates current; claim races still
  produce exactly one current participant.
- Blocked, parked, waiting, terminal, and otherwise unclaimed Work never
  projects a current participant.
- Route authorization, transition discovery, readiness, CLI JSON, ACP
  readiness envelopes, Events, and the TUI all agree on the same names and
  identities.
- Tests reject stale consumers that interpret route membership as current
  execution.

## Revalidation against the current tree — 2026-08-17

The approved distinction is not present under different names; the current
tree implements the exact ambiguity observed in the trial:

- `src/baton_work/authority.py` stores the route as
  `work.current_team/current_kind` and the claimant as
  `active_team/active_member`;
- `src/baton_work/projection.py` publishes those as endpoint-valued `current`
  and participant-valued `active` in detail, tree, links, and readiness;
- `src/baton_work/transitions.py` correctly gates claims through the endpoint
  and stores the exact claimant separately, so the behavioral invariant can
  be retained while the names change;
- `src/baton_work/cli.py` and `projection.py` define `current=` filters as
  endpoint eligibility, including `current=me`;
- `src/baton_work/tui/app.py` renders the endpoint under Current and separately
  consults `active` for personal actionability, hot state, and Held; and
- the workflow, parity, packaged, readiness, heartbeat, pass, filter, scenario,
  and TUI suites assert the old names extensively.

Because this is a fresh v11 trial schema, the implementation should rename the
storage columns too: `route_team/route_kind` for eligibility and
`current_team/current_member` for the live claimant. Keeping the old internal
names would make later authority code repeat the same conceptual mistake.

Public filters split consistently. `route=` filters endpoint eligibility and
retains the useful `route=me` meaning; `current=` filters the exact claimant
and `current=me` means “claimed by this viewer.” Events that currently say
`was_current_kind` become route-named evidence. No compatibility aliases are
kept in the fresh projection.
