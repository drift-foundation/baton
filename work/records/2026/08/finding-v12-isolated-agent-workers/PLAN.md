# Plan

**Status — parked as Baton Work `W193`; roadmap only. No v12 implementation
has started.**

1. [pending] Model assignment generations, read-only pre-claim inspection,
   claim-capability-gated writable workers, cancellation, quiescence,
   stale-worker rejection, and integration dispositions as one protocol state
   machine.
2. [pending] Specify the versioned worker input manifest and candidate output
   manifest, including base revision, role/policy/toolchain digests, tests,
   logs, and dossier evidence.
3. [pending] Specify the Baton worker-control API separately from ACP; keep ACP
   as the model-neutral session/turn boundary behind each worker.
4. [pending] Build one reference isolated worker using an independent clone in
   an OCI/Docker container, with canonical repository and Git refs unwritable.
5. [pending] Adapt Claude and Gemini through the same ACP worker contract; add
   Codex through the same contract or a conforming adapter.
6. [pending] Implement candidate publication and an integration review path
   where only the integration authority can update canonical history.
7. [pending] Exercise crash, provider overload, cancellation race, late
   recovery, duplicate assignment, stale candidate, conflicting candidates,
   rejected review, revision, and manual-salvage workflows.
8. [pending] Run a multi-agent trial with concurrent independent Work and
   verify that no worker can alter another worker or the canonical checkout.
9. [pending] Define migration, deployment, operating documentation, retention,
   and observability before considering v12 production adoption.
