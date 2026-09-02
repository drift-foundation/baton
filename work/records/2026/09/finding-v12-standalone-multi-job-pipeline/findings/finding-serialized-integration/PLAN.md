# Plan

1. [pending coordination] Read W71459's terminal/latest ruling and current
   diff after its ownership ends; adopt that settled test-change policy without
   racing or broadening its v11 file set.
2. [pending revalidation] Map v12 proposal/review/integration receipts and the
   W65212 integrator contract to one scheduler-owned target queue.
3. [pending] Define queue/lease identity, eligibility, preflight, typed refusal,
   restart recovery, and success handoff records. Keep Git interpretation in
   the integration profile, not the Worker Manager.
4. [pending] Implement single-target serialization and whole-candidate
   preflight before the bounded integrator import.
5. [pending] Prove two-ready-proposal races, moved target, overlap/conflict,
   stale/mismatched review, missing objects, partial-write prevention, restart,
   one approved existing-test change, and one out-of-scope test refusal.
6. [pending independent review] Bind the exact proposal digest and enumerate
   every changed existing test path with case-specific approval evidence.

This leaf follows the persistent control-plane contract and may be designed in
parallel, but its v11 policy touchpoints wait for W71459 ownership to end.
