# Plan

**Status — 2026-08-21:** round-6 independent review in
`review-2026-08-21T03-44-38Z.md` is clean. The disposable external PoC has
completed its technical proof and may close. Repository relocation remains a
separate follow-up under parent-plan item 0ai: copy the reviewed snapshot into
the self-contained top-level `v12/`, verify it there, and only then retire the
external root without changing v11 paths.

1. [done] Revalidate this handoff after claim. Confirm the Baton repository
   baseline is clean, the external prototype root is separate and clean, Docker
   and Claude ACP are usable, and no production coordination path is selected.
2. [done] Inventory reusable v11 CLI/JSON and ACP pieces at commit `8835cd5`.
   Copy only what accelerates the proof into the external root and record each
   copied path and commit in the provenance manifest.
3. [done] Define minimal draft `0-spike` JSON envelopes for Job input,
   pre-claim offer/token, claim intent, assignment identity, activity, declared
   output, frozen result and terminal return. Treat them as disposable.
4. [done] Build the smallest external trusted manager that reads actionable
   state through the deployed Baton CLI/JSON interface, owns all mutations, and
   never opens SQLite or production state.
5. [done] Build the read-only pre-claim Claude ACP exchange and enforce token
   expiry, single use, exact Work/participant/runtime binding and replay refusal.
6. [done] After canonical claim success, start one isolated Docker worker,
   materialize and verify the directory fixture read-only, expose the separate
   writable result, run Claude, and collect structured activity/completion.
7. [done] Freeze and validate the result, compute manifests/digests, verify
   the expected deterministic transformation independently, and return the Job
   for review through Baton CLI/JSON.
8. [done] Run the expired/replayed-token negative case and prove there is no
   claim, writable worker or accepted output.
9. [done] Repeat the happy path from a fresh disposable authority, capture
   sanitized traces and prerequisite commands, and test the external prototype
   without modifying existing Baton product source.
10. [done] Record a go/revise/no-go conclusion and the smallest corrections
    proposed for W2's state machine, IN/OUT, worker-control and conformance
    contracts. Return W76 for independent review; implement no production port.
11. [done] Make recap publication effectively once or explicitly
    non-load-bearing, and reconcile pass/release against loss of the source
    claim rather than transient global unclaimed state. Cover immediate
    successor claims and committed-then-lost recap results.
