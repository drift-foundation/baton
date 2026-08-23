# Plan: v12 ACP agent boundary

1. [done 2026-08-21] Revalidate the frozen outer worker-control vocabulary and
   current ACP/App Server capabilities. W1439's `SPEC.md`, schema and evidence
   were re-read at their current state; the ACP surface was re-derived from
   `@agentclientprotocol/sdk` 1.3.0 as vendored under `v12/node_modules/`; the
   Codex App Server surface was re-read from its official documentation. See
   `FINDING.md`, "Revalidated baseline", and the 2026-08-21 corrections that
   supersede two of its recorded facts.
2. [done 2026-08-21] Specify the minimum normalized ACP session, update,
   permission and cancellation contract. `SPEC.md` §2-§7.
3. [done 2026-08-21] Specify native relay and non-native adapter obligations,
   including the Codex App Server profile. `SPEC.md` §8-§10.
4. [done 2026-08-21] Add valid/invalid traces for policy, cancellation,
   disconnect, duplicate and late-event behavior.
   `schema/agent-session-1.0.schema.json`, `evidence/traces.json` (19 traces,
   78 negative vectors, 3 invalid document vectors after three review rounds),
   the captured provider response schemas under `evidence/provider-schemas/`,
   and the executable model and tests in `evidence/`.
5. [done 2026-08-21] First independent review. `baton.codex` requested changes
   in `review-2026-08-21T22-53-56Z.md`: four P1 findings (shared identity
   definitions diverged from W1439 and the schema permitted three forbidden
   session bindings; normalized events were unsealed and the ledger consumed a
   different shape; consent/execution cardinality contradicted itself; the
   Codex profile was not executable) and two P2 findings.
6. [done 2026-08-21] Correct all six. Every counterexample was reproduced
   first, then fixed and re-run. See `PROGRESS.md`, "Response to
   review-2026-08-21T22-53-56Z".
7. [done 2026-08-21] Second independent review. `baton.codex` requested
   changes in `review-2026-08-21T23-18-11Z.md`: three executable gaps (the
   command and file approval replies omitted the response object; the event
   ledger neither consumed nor returned the sealed document; profile
   certification did not enforce the policy the profile recorded) and one set
   of live prose still stating the superseded cardinality.
8. [done 2026-08-21] Correct all four, capturing the provider's own approval
   response schemas as evidence rather than re-asserting self-authored
   equality. See `PROGRESS.md`, "Response to review-2026-08-21T23-18-11Z".
9. [done 2026-08-21] Third independent review. `baton.codex` requested
   changes in `review-2026-08-21T23-32-48Z.md`: the combined certification
   path accepts schema-invalid or tampered profiles and permits session
   validation without the profile it claims; the event ledger also aliases
   caller-owned mutable dictionaries, allowing accepted evidence to change in
   place.
10. [done 2026-08-21] Correct both. Certification is one entry point composing
    durable shape, then seal, then policy, before any policy field is read;
    the profile is a required operand of session-record validation; and no
    durable entry aliases a caller's object, in either direction. The
    semantic-only checks survive as explicitly named partial helpers. See
    `PROGRESS.md`, "Response to review-2026-08-21T23-32-48Z".
11. [done 2026-08-21] Fourth independent review signed off in
    `review-2026-08-21T23-42-10Z.md`; return the child for approval.
