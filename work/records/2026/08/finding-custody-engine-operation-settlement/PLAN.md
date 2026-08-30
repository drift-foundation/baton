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
6. [parked hardening] If operational evidence justifies automatic settlement,
   resume W44342 and give a separate provider implementation Work explicit
   file ownership. Do not hide it inside generic `EnginePort`.
7. [superseded] Do not add the proposed W43974-on-W44342 dependency. W44342 is
   not a gate on W43974 or the first useful dogfood run.
