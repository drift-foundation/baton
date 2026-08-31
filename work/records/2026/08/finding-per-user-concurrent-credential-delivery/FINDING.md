# Make credential delivery per-user and concurrent

Work: W52821

## Finding

The supervised dogfood path currently requires an operator to copy a host
credential into the global path `/run/baton/credentials/<provider>` before a
run. This is unnecessary deployment ceremony and is incompatible with
multiple OS users running Baton concurrently with separate provider accounts.
A shared mutable credential slot must never become a serialization point.

The live W51487 proof also established a separate worker-facing defect: the
manager materializes an attempt slot as `0600` owned by the host manager uid,
then launches the container as uid 65532. The worker sees the path but cannot
read it. A credential-free reproduction shows that the existing supplementary
workspace group plus mode `0640` makes the slot readable without making the
bearer world-readable; worker preflight must test readability rather than path
existence.

## Confirmed direction — 2026-08-31

Credential resolution and materialization are per assignment, keyed by the OS
user, credential profile, assignment generation and attempt id. Each user has
a user-scoped runner under that user's uid. The runner reads only that user's
configured provider source, creates a unique attempt-private credential slot,
and exposes only that slot read-only to the worker container.

The shared Baton configuration does not carry host credential paths. There is
no global credential lock, shared mutable slot or process-global active
attempt. Different users and participants can run concurrently; serialization
comes only from explicit routing, claim limits or provider policy. The fixed
path inside each isolated container may remain
`/run/baton/credentials/<provider>`.

The global manually synchronized `/run/baton/credentials/*` source convention
is superseded for the eventual multi-user path. A local private-box dogfood
workaround may remain until this defect is implemented.

## Scheduling boundary

Do not interrupt or alter the first useful dogfood proof. This defect becomes
the next high-priority implementation concern only after W38956 closes
satisfying. Its Baton Work must be explicitly blocked on W38956 before any
research or implementation begins.

## Acceptance

- No user manually copies or refreshes a provider credential into a shared
  global path before ordinary execution.
- Two distinct OS users with separate credentials can run isolated attempts
  concurrently without sharing a source, slot, lock or mutable state.
- Attempt credential slots are unique, worker-readable, non-world-readable,
  read-only in the container and removed by exact-attempt teardown.
- An unreadable slot refuses before a provider turn with a safe typed cause.
- Shared Baton configuration and durable evidence contain no credential
  content or host-user credential path.
