# Plan

1. [pending] Revalidate this handoff after claim. Confirm the Baton repository
   baseline is clean, the external prototype root is separate and clean, Docker
   and Claude ACP are usable, and no production coordination path is selected.
2. [pending] Inventory reusable v11 CLI/JSON and ACP pieces at commit `8835cd5`.
   Copy only what accelerates the proof into the external root and record each
   copied path and commit in the provenance manifest.
3. [pending] Define minimal draft `0-spike` JSON envelopes for Job input,
   pre-claim offer/token, claim intent, assignment identity, activity, declared
   output, frozen result and terminal return. Treat them as disposable.
4. [pending] Build the smallest external trusted manager that reads actionable
   state through the deployed Baton CLI/JSON interface, owns all mutations, and
   never opens SQLite or production state.
5. [pending] Build the read-only pre-claim Claude ACP exchange and enforce token
   expiry, single use, exact Work/participant/runtime binding and replay refusal.
6. [pending] After canonical claim success, start one isolated Docker worker,
   materialize and verify the directory fixture read-only, expose the separate
   writable result, run Claude, and collect structured activity/completion.
7. [pending] Freeze and validate the result, compute manifests/digests, verify
   the expected deterministic transformation independently, and return the Job
   for review through Baton CLI/JSON.
8. [pending] Run the expired/replayed-token negative case and prove there is no
   claim, writable worker or accepted output.
9. [pending] Repeat the happy path from a fresh disposable authority, capture
   sanitized traces and prerequisite commands, and test the external prototype
   without modifying existing Baton product source.
10. [pending] Record a go/revise/no-go conclusion and the smallest corrections
    proposed for W2's state machine, IN/OUT, worker-control and conformance
    contracts. Return W76 for independent review; implement no production port.
