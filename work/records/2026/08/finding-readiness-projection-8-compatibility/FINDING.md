# Readiness bridges reject projection 8

## Observed — 2026-08-17

After the `137d7fc` cutover created a projection-8.0 authority, both deployed
readiness paths refused every `wait` result:

```text
projection "8.0" does not carry the projection-7 participant-action contract
```

The refusal affects both `codex-baton-bridge` and `acp-baton-bridge`, because
the ACP client imports the Codex bridge's shared `validateEnvelope` gate.
Consequently neither `baton.codex` nor `baton.claude` can receive readiness
events from the new authority.

## Confirmed cause

`tools/codex-event-bridge/src/codex_baton_bridge.mjs` accepts only projection
major 7. The projection was advanced to 8 for claimant-authority changes, but
the participant-action envelope consumed by the readiness bridges retained
the same fully typed contract. A canonical projection-8 `wait timeout=0`
contains the required protocol, participant, authority, snapshot, timeout,
action kind, action key, episode, generation, Work locator, phase, and title
fields.

The bridge tests remained pinned to projection 7 and therefore did not run
the validator against the release's current projection constant.

## Decision

The shared readiness validator accepts projection 7.x and 8.x envelopes and
continues validating every consumed field and cross-field invariant. It does
not accept arbitrary future projection majors. The error names the supported
7/8 participant-action contract.

The bridge acceptance suite must exercise projection 8 positively and retain
negative coverage for missing, pre-7, and unsupported future projection
majors. A repository-level regression ties the bridge's accepted current
projection to `baton_work.jsonapi.PROJECTION_VERSION`, so a future projection
bump cannot ship another silent readiness outage.

## Acceptance

1. Both readiness bridges accept the canonical projection-8 envelope.
2. Projection 7 remains accepted for the bounded transition compatibility.
3. Missing, pre-7, and unsupported future majors fail closed by name.
4. All typed action and action-key consistency checks remain unchanged.
5. The ACP and Codex bridge suites pass.
6. A live source bridge can consume the new authority before another release
   is built; the next distribution co-deploys the corrected bridge.

