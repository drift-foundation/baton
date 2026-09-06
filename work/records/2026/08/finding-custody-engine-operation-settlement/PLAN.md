# Plan

1. [done] Revalidate the exact custody provider call path and identify every
   place a local CLI timeout is currently treated as engine-operation
   settlement.
2. [done] Establish what Docker can prove after client interruption:
   cancellation, completion, discoverable pending state, or none of those.
3. [done] Compare the smallest viable provider boundaries against restart,
   retry, crash and late-create races.
4. [done] Recommend a boundary with exact states, ownership, regressions and
   focused verification. The recommendation is durable provider acceptance
   followed by provider-owned asynchronous settlement; direct API context
   cancellation is insufficient.
5. [done: approver ruling 2026-08-30] The dogfood pilot retains W43974's
   fail-closed `UNRESOLVED` stopgap. It does not acquire the independently
   supervised provider in this pass.
6. [superseded 2026-09-05] Do not make an independently supervised durable
   engine-operation provider the default next solution. It remains optional
   later hardening for engine-resource reconciliation, not a prerequisite for
   preventing an ambiguously launched container from executing Work.
7. [superseded] Do not add the proposed W43974-on-W44342 dependency. W44342 is
   not a gate on W43974 or the first useful dogfood run.
8. [parked follow-up after the standalone pipeline proof] Specify and implement
   the minimal restart-durable attempt lifecycle: inert container start,
   optional declared `check`, atomic ready or refusal publication, durable
   activation and claim acknowledgement, `work`, optional `cleanup`, positive
   quiescence and manager-owned destroy. Reuse existing attempt, activation and
   quiescence machinery; do not introduce a generic hook framework, mandatory
   pause, or universal resource preflight.
