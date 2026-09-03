# Plan

1. [done, reviewer revalidation 2026-09-03] Inventory the public offer, claim,
   attempt, session, cleanup and runtime-lane operations and W71875's submitted
   Job projection. The focused 146-test Job-manager suite passes at `efbad19`.
2. [done, proposed contract awaiting operator acceptance] Define the closed
   pool document, exact kind/profile eligibility, scheduler-owned allocation
   axis, soft affinity, hard producer/prior-reviewer exclusions, stage-scoped
   dependency use, and the existing attempt/runtime identity mapping without
   introducing fixed exclusive personas.
3. [blocked by W73629, then implementation] Implement atomic
   selection/reservation and durable slot lifecycle around the existing
   concrete-offer and authority-claim boundary. Bind adopted offers to the
   selected participant and preserve append-only stage episodes.
4. [pending composition] Compose implementation and review launch/settlement so every slot
   owns separate runtime, workspace, credential, output, and log identities.
   Reuse W71917 and W71918 outputs; do not implement their mount, checkpoint,
   correction, or verdict semantics here.
5. [pending focused verification] Prove two implementation and two review slots, offer/claim races,
   fallback from unavailable affinity, independent reviewer separation,
   review-ahead, launch failure, canonical cleanup release, wedged isolation,
   participant-bound adoption, and restart recovery.
6. [pending independent review] Bind the verdict to the immutable proposal and
   enumerate every changed production and test path.

Child status: W73629 is open and owns the abandoned-offer/stage-episode defect
found during revalidation. This parent cannot close until that child closes.

W32577 and unrelated exhaustive hardening do not gate this leaf unless a
measured failure makes the happy-path concurrency claim false.
