# Finding: unclaimed Work must be reroutable

## Observation — 2026-08-19

W30 was open, queued, unclaimed, and explicitly selected to the `impl2`
alternate route. The owning-team reviewer needed to move it back to the
primary `impl` route because Gemini was not taking it. Canonical detail offered
the reviewer only `prioritize`; `pass` remained restricted to the currently
resolved route handler even though nobody held the Work.

The only available path was to wake Gemini solely so it could pass untouched
Work to Claude. That adds an unnecessary dependency on the very runner the
operator is trying to route around and can strand Work when that runner is
offline, overloaded, or broken.

## Confirmed decision — 2026-08-19

Open, unclaimed Work is reroutable by any active member of its owning team.
The operation records a durable reason and atomically selects the destination
endpoint and optional configured alternate route.

Claimed Work is never rerouted underneath its Handler. A reroute must refuse
if a claim exists; the claimant must pass it, or an explicit recovery must
release the claim first.

The claim-versus-reroute race is decided under the authority lock. Exactly one
operation commits against the observed unclaimed state, and the loser refuses
without partially changing Route, Handler, Phase, or Next.

Cross-team participants cannot reroute another team's Work merely because it
is unclaimed. Discussion and requests remain open, but workflow mutation stays
with the owning team.

## Required behavior

- Add an explicit public operation for rerouting open, unclaimed Work.
- Accept one destination endpoint, an optional configured alternate route,
  and a required durable reason.
- Resolve the destination and selected route inside the committing lock.
- Refuse terminal, claimed, foreign-team, missing-route, withdrawn-route, and
  no-op reroutes atomically.
- Preserve the Work identity, dossier binding, messages, dependencies,
  containment, priority, classification, and planned Next.
- Project the new Route consistently through direct and linked Work views.
- Record the correction in Work Events; it is not a discussion Message.

## Acceptance boundary

Cover primary-to-alternate and alternate-to-primary reroutes, a different
endpoint, no-op refusal, foreign-team refusal, terminal refusal, selected-route
withdrawal, and serialized claim-versus-reroute races in both orderings. Run
the focused transition/projection tests and the complete v11 gate.
