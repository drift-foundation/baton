# Schedule concurrent v12 implementation and review stages

Ledger Work: W71877

Parent: `work/records/2026/09/finding-v12-standalone-multi-job-pipeline/`

## Confirmed scope

Compose pooled stage scheduling for independent implementation and review
work. The first deployment target is at least two concurrent implementation
containers and two independently schedulable review containers. Every offer
names one eligible participant/runtime profile, every successful claim and
attempt keeps its own authority identity, and every runtime has isolated
resources.

This leaf owns eligibility, capacity, soft continuation affinity, hard
independent-opinion separation, stage-scoped dependency checks, slot release,
and failure isolation. It reuses the persistent manager's submission/stage
state and the existing offer, claim, attempt, session, and runtime-lane
operations. It does not own source/workspace semantics, review checkpoint
format, verdict policy, or integration serialization.

## Observed baseline — 2026-09-02

- `worker_manager/offers.py` already owns concrete offer, acceptance, claim,
  expiry, settlement, and restart recovery operations.
- `worker_manager/lanes.py` prevents overlapping execution over one Work's
  assignment material; it is a per-Work execution interlock, not a global
  multi-Job pool scheduler.
- `worker_manager/sessions.py` owns posture-specific agent sessions and slot
  state within an attempt.
- No product component selects among a pool of eligible implementation or
  review runtimes, fills several independent slots, or advances review-ahead
  under stage-scoped dependency gates.

## Acceptance

- Configuration declares at least two implementation slots and two review
  slots with exact participant/runtime identities and capability eligibility.
- Two independent Jobs from one immutable baseline can be offered, claimed,
  and run concurrently without sharing a writable workspace, attempt,
  assignment generation, credential delivery, output, or log sink.
- Review can run concurrently with unrelated implementation. A reviewer is
  different from the candidate-producing runtime, and an explicit independent
  opinion cannot be satisfied by the prior reviewer.
- Ordinary continuation prefers useful context affinity but falls back to any
  eligible healthy slot without turning affinity into ownership.
- Implementation and integration dependency gates are checked at the named
  stage. An unrelated blocked stage does not hide review-ahead work whose
  contract is already knowable.
- A failed, refused, or wedged Job releases or quarantines only its own
  capacity according to recorded policy. Unrelated slots continue without a
  manager or v11 stack restart.
- Race tests prove one offer/claim winner per Job and no global slot leak on
  launch failure, normal completion, review completion, or process restart.

## Test-change authority

This Work authorizes adding tests and editing existing tests under
`v12/python/tests/` only for scheduler eligibility, capacity, affinity,
independence, stage-gate, race, and failure-isolation behavior described here.
Any deletion or weakened expectation must be explicit and independently
reviewed. Unrelated test mutations remain out of scope.
