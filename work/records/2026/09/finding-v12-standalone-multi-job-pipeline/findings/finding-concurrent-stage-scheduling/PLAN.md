# Plan

1. [pending revalidation] Inventory the public offer, claim, attempt, session,
   and runtime-lane operations and the persistent manager's submitted Job
   projection.
2. [pending] Define pool configuration, eligibility, capacity, soft affinity,
   independent-opinion constraints, and stage-scoped dependency checks without
   introducing fixed exclusive personas.
3. [pending] Implement atomic selection/reservation and durable slot lifecycle
   around the existing concrete-offer and authority-claim boundary.
4. [pending] Compose implementation and review launch/settlement so every slot
   owns separate runtime, workspace, credential, output, and log identities.
5. [pending] Prove two implementation and two review slots, offer/claim races,
   fallback from unavailable affinity, independent reviewer separation,
   review-ahead, launch failure, wedged isolation, and restart recovery.
6. [pending independent review] Bind the verdict to the immutable proposal and
   enumerate every changed production and test path.

W32577 and unrelated exhaustive hardening do not gate this leaf unless a
measured failure makes the happy-path concurrency claim false.
