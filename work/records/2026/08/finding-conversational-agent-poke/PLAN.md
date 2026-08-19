# Plan

1. [done] Approved the persistent exact-participant Baton primitive recorded
   in `FINDING.md`, rather than transient vendor-specific runner control.
2. [done] Revalidated the approved contract against the current authority and
   returned one explicit protocol proposal covering authorization, timeout,
   retry/redelivery, cancellation, idempotency, and rate limiting — see
   `PROPOSAL.md`. It also raises a rollout-order question the plan did not
   anticipate: a new action kind currently refuses the WHOLE envelope in both
   runner bridges. All four ruler questions are settled in `FINDING.md`:
   self-poke, optional explicit timeout, newest-pending deduplication, and one
   rollout containing both tolerant consumers and poke emission.
3. [done: slice A] Implement the persistent exact-participant request and
   terminal response in the authority, CLI, JSON projection, and
   participant-relative `wait`. Prove with positive, negative, race, offline,
   replay, and restart tests that it neither belongs to Work nor mutates Work.
4. [done: slice A] Define the normalized capability-based runner/provider
   and agent-status response fields. Unsupported facts are explicit
   `unknown`; credentials and unrestricted provider payloads never enter the
   authority.
5. [done: slice A review gate] Publish the accumulated candidate
   under a new projection major because a pre-widening consumer refuses the
   new action kind. Preserve strict validation of every known action and the
   accepted slice-A contract.
6. [done: slice B] Integrate the external Codex and generic ACP runners and
   test healthy, busy, idle, unavailable, authentication/rate-limit, and
   contradictory canonical-versus-agent state responses.
7. [done: slice B review gate] Verify one vendor-neutral action/response
   contract drives both runner families; adapters translate capabilities but
   define no private poke semantics.
8. [pending: later presentation] Add concise TUI/operator presentation only
   after the JSON contract and live runner behavior are stable.
