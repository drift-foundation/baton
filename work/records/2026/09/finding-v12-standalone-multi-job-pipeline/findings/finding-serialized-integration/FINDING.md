# Serialize accepted v12 proposals through integration

Ledger Work: W71878

Parent: `work/records/2026/09/finding-v12-standalone-multi-job-pipeline/`

Related: W65212, W62098, and W71459.

## Confirmed scope

Compose one scheduler-owned integration queue per canonical target. Only an
immutable proposal checkpoint with a bound independent-review acceptance may
enter it. The distinct Git-aware integrator validates base/head/object
availability, review and proposal digests, approved path scope, current-target
drift, and repository policy before importing one proposal at a time into the
working tree. Conflict, overlap, missing provenance, stale review, or policy
ambiguity refuses the whole import and schedules no hidden correction.

The generic Worker Manager remains artifact-neutral. It retains and hands off
the frozen result; it does not run Git or interpret proposal ancestry. The
integrator does not redesign, auto-merge, mutate Git history, or approve its
own result. Slawomir retains final Git ownership.

## Observed baseline — 2026-09-02

- V12 authority already records proposals, verification/review/approval
  receipts, and integration attempts, but no persistent scheduler serializes
  integration work for a shared target.
- W65212 established and deployed the distinct `baton.merge` role and its
  bounded working-tree import/refusal contract. It is a v11 deployment proof,
  not the v12 queue/control-plane composition.
- W62098 rules ordinary Git base/head ancestry and explicit Work dependencies;
  no Baton-specific path-lineage or merge algorithm may be introduced.
- W71459 owns the current v11 integrator test-change preauthorization policy.
  This leaf must consume the settled rule after that ownership ends and must
  not edit the same files concurrently.

## Acceptance

- Accepted proposals for the same canonical target enter a durable FIFO or
  otherwise deterministic queue and at most one holds the integration lease.
  Independent targets need not share that lock.
- Eligibility requires a final immutable checkpoint, its exact base/head and
  durable Git objects, a matching independent-review acceptance, and an
  explicit approved path/test-change scope.
- The integrator preflights the whole candidate before any canonical target
  path changes. Missing/mismatched provenance, target movement, overlapping
  divergence, conflict, or out-of-scope paths refuse with a typed result.
- A scheduled existing-test modification inside the bounded Work/plan scope
  imports non-interactively after review. A companion unscheduled or
  out-of-scope test mutation refuses before any canonical target path changes.
- A failed integration leaves the queue and canonical target recoverable and
  does not block unrelated implementation/review capacity.
- Successful import exposes the exact proposal/review identities, imported
  paths, verification evidence, and prepared working-tree diff to Slawomir;
  neither manager nor integrator stages or commits it.
- Restart and two-ready-proposal races prove single-target serialization and
  idempotent recovery without duplicate or partial import.

## Test-change authority

This Work authorizes adding tests and editing existing tests under
`v12/python/tests/` and the bounded integrator-policy test surface needed to
prove this leaf. It explicitly authorizes one planned existing-test behavior
change fixture for the positive integration case and one out-of-scope mutation
fixture for preflight refusal. Any real test deletion or weakening must be
named by path in the proposal and independent review. W71459's owned v11 policy
files remain excluded until its claim and handoff finish.
