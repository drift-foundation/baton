# Finding: certify v12 parallel scheduling with deterministic traces

Ledger Work: W103525

## Placement — confirmed 2026-09-06

This certification stage starts immediately after the standalone multi-Job
v12 pipeline milestone represented by W71830 is accepted. It does not block or
broaden that milestone.

The purpose is to validate the scheduler before model latency, provider
availability, and non-deterministic completion times obscure its behavior.
Scheduler correctness must be provable without invoking an AI model.

## Confirmed test contract — 2026-09-06

Use Python-scripted actors, controlled completions, and a logical clock to
exercise multiple teams with pools of implementation and independent-review
workers. The durable event trace is the evidence and a validator asserts
causal partial orders and final state invariants.

The certification covers:

- dependencies preventing premature stages without serializing unrelated
  Jobs;
- role, capability, team, and repository eligibility;
- implementation/review session separation;
- same-line correction affinity to the original healthy implementation
  worker and session;
- explicit fallback as the only intentional affinity break, with a fresh
  session;
- one live offer/claim per worker slot and no duplicate execution;
- work-conserving dispatch: no compatible slot remains idle while eligible
  Work exists;
- priority governing between explicit priority pools, affinity selecting
  within a pool before creation chronology, and creation order breaking the
  remaining ties;
- restart, replay, and repeated observation producing the same canonical
  result without duplicating effects; and
- a trace shape that a later read-only v12 TUI can render as stable Job rows
  plus chronological offers, claims, handoffs, corrections, fallbacks, and
  integration transitions.

Independent Jobs may complete in any order and workers may take arbitrary
amounts of time. Tests assert only required `this-before-that` relationships;
they do not invent a total completion order.

A later live Claude/Codex exercise validates adapters, credentials, latency,
and observability. It is not the oracle for scheduler correctness.

## Deferred details

Exact pool sizes, workload counts, timing thresholds, randomized interleaving
strategy, and TUI presentation remain open until the parallel scheduler is
available. This record fixes the certification boundary, not those mechanics.
