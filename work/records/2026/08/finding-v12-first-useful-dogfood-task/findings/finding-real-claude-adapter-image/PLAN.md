# Plan

1. Revalidate W17110's pinned Claude image facts and the current
   `baton_worker.main(agent=...)` seam.
2. Implement a worker-side Claude adapter with a closed argv, bounded prompt
   and response, explicit fixed credential slot and typed failure mapping.
3. Add the dogfood image/entrypoint without importing the spike lifecycle.
4. Copy the exact staged source into bounded private scratch, run the frozen
   task there and author only the declared proposal tree.
5. Prove positive shape and provider negatives without a live credential;
   build/probe the image if the engine gate is available.
6. Return W39357 for independent review. Do not begin operator composition or
   authorize a live credential/network posture under this claim.
