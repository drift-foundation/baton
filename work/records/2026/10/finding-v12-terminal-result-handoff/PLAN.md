# Current disposition — v11 bridge implementation not selected

Owner 2026-10-18 prioritizes moving all coordination to v12. Do not implement
or prepare deployment of the proposed v12-to-v11 reporter. Preserve CONTRACT.md
as an unselected proposal and the observed terminal-pickup gap as evidence.
Manual result collection/review routing is the temporary path. Recommend parking
this Work; no ledger transition has been performed by prompt.

Continue the existing W321608 native-coordination path through W321689/W321690.
Native result pickup remains an acceptance question there; a running engine alone
does not prove coordination readiness. No automatic backlog migration or cutover.

The earlier plan below is superseded as scheduling guidance, retained as history.

---

# Current milestone — completion contract prepared

W324316 claim324340 completed read-only investigation and proposed CONTRACT.md.
FINDING.md records current API capabilities, stale-episode gap and source evidence.
No implementation, product test, new Job/attempt, deployment or provider retry.
Existing observed run/attempt is preserved in evidence/OBSERVATION.json.

Next decision: select separate deduplicated result-collection Work through the
configured review endpoint, plus reporter identity/lifecycle ownership. This is
the supported minimal alternative to unsafe automatic same-Work reroute. If
same-Work transfer is mandatory, select the exact-episode transition prerequisite
instead; current reroute cannot supply it.

After selection, route bounded v11 packet preparation to available implementation
endpoint, then independent packet review, selected v12 execution, independent
candidate review and human Git checkpoint. Do not activate automatically. A
suggested future checkpoint is `Add durable v12 result collection handoff`.

Reviewer owns this dossier's FINDING/PLAN/CONTRACT/evidence; future implementer
owns PROGRESS and records actual source/test paths. Prefer separate reporter and
wrapper to preserve W321528 baseline.py, W321689 authority/stack/bootstrap and
W324214 visibility ownership. No sibling depends on this unimplemented adapter;
their already-selected manual result collection may continue. Joined acceptance
is one reporter result across success/failure/restart, not a telemetry expansion.
