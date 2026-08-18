# Plan

1. [done] Approved the persistent exact-participant Baton primitive recorded
   in `FINDING.md`, rather than transient vendor-specific runner control.
2. [done] Revalidated the approved contract against the current authority and
   returned one explicit protocol proposal covering authorization, timeout,
   retry/redelivery, cancellation, idempotency, and rate limiting — see
   `PROPOSAL.md`. It also raises a rollout-order question the plan did not
   anticipate: a new action kind currently refuses the WHOLE envelope in both
   runner bridges. Four questions are left explicitly for the ruler rather
   than settled in code.
3. [pending: slice A] Implement the persistent exact-participant request and
   terminal response in the authority, CLI, JSON projection, and
   participant-relative `wait`. Prove with positive, negative, race, offline,
   replay, and restart tests that it neither belongs to Work nor mutates Work.
4. [pending: slice A] Define the normalized capability-based runner/provider
   and agent-status response fields. Unsupported facts are explicit
   `unknown`; credentials and unrestricted provider payloads never enter the
   authority.
5. [pending: slice A review gate] Independently review the schema, projection,
   JSON/CLI UX, redelivery behavior, and workflow non-interference before any
   runner consumes the new action kind.
6. [pending: slice B] Integrate the external Codex and generic ACP runners and
   test healthy, busy, idle, unavailable, authentication/rate-limit, and
   contradictory canonical-versus-agent state responses.
7. [pending: slice B review gate] Verify one vendor-neutral action/response
   contract drives both runner families; adapters translate capabilities but
   define no private poke semantics.
8. [pending: later presentation] Add concise TUI/operator presentation only
   after the JSON contract and live runner behavior are stable.
