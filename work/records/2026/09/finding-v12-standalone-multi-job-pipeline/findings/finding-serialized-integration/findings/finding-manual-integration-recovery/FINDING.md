# Hold interrupted integration for manual recovery

Ledger Work: W101493

Parent: `work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-serialized-integration/`

## Confirmed scope

Expose interruption or inconsistent integration state as one durable,
inspectable operator-held condition. Preserve the queue entry, lease/fence,
target exclusion, runtime identity, logs, output and observed target/account
facts. Restart may observe and classify the condition but performs no automatic
retry, acceptance, Authority completion, cleanup, lease release, output
discard or reassignment.

This is tuner-suitable work only behind K's accepted shared boundary and in an
explicitly disjoint diagnostics/operator leaf. K owns any shared state,
interface, schema, export or final assembly change. A missing shared primitive
returns to K rather than being invented here.

## Acceptance boundary

- Interruption before, during or after import produces a typed operator-held
  condition and keeps the target unavailable.
- Status exposes safe locators and exact identities needed to inspect retained
  evidence without exposing credential content.
- No restart path silently retries, accepts, completes, cleans, releases,
  discards or reassigns the attempt.
- Explicit recovery refuses until the prior runtime is proved unable to mutate
  the target.
- Focused tests cover representative untouched, completed-looking, mixed and
  unknown states as holds; they do not implement automatic repair.
