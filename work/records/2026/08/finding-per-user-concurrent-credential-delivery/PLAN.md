# Plan

1. [gate first] Block this Work on W38956 and do no further work until the
   first useful dogfood task closes satisfying.
2. Revalidate the live credential-slot permission reproduction and the
   current provider-source configuration boundary.
3. Specify user-scoped credential-provider configuration and concurrent
   attempt allocation without changing protocol vocabulary prematurely.
4. Correct attempt-slot access and worker readability preflight with focused
   positive, negative and teardown tests.
5. Prove two user-scoped runners can execute concurrently with distinct
   provider sources and attempt-private slots.
6. Remove the global manual staging requirement from the supported operator
   path and document migration from the private-box workaround.

## Revalidated scheduling state — 2026-08-31

1. [done, gate not satisfied] W38956 is terminal `non-satisfying`, not the
   satisfying close required above. Its terminality cleared the ledger edge but
   did not authorize steps 2-6.
2. [parked] Preserve this confirmed defect and its accepted direction without
   research or implementation. Resume only under an explicit superseding
   scheduling ruling or a recorded replacement successful-dogfood gate.
3. [not started] Original steps 2-6 remain the implementation-ready sequence
   once the scheduling gate is validly superseded or satisfied.

## Resumed vertical slice — 2026-09-01

1. [done] Record Slawomir's explicit scheduling supersession after W55758 and
   select W52821 as the first real repository change run through the supervised
   v12 worker path.
2. [done, reviewer revalidation 2026-09-01] Revalidate the current
   `--credential-file` path, credential home and slot materialization seams;
   freeze the smallest input set and task contract for one user-scoped runner.
   The current manager already owns attempt-private delivery, exact teardown,
   worker readability and lazy post-activation materialization. The open seam
   is the user-local `(provider, reference)` source resolver. Evidence and
   proposed task: `evidence/research-2026-09-01/`.
3. [done, approved 2026-09-01] Use the explicit private
   `--credential-sources` registry and remove the direct-file bypass; require
   current-uid/private ordinary-file proof; and permit a host path only in
   user-local configuration. Use one live worker now and prove future
   concurrency through isolated contexts and focused tests.
4. [next after approval, v12 worker] Implement the ruled user-scoped provider
   resolution and command wiring without changing the manager's credential,
   OCI or worker-readable-slot contracts and without a shared
   `/run/baton/credentials/*` source, global lock or process-global active
   attempt. Use `evidence/research-2026-09-01/task.json` and its closed source
   list.
5. [next, focused verification] Prove with two distinct configured user and
   provider contexts that source resolution, slots and teardown do not share
   mutable state. Do not start a second live worker for this slice.
6. [next, operator/reviewer] Inspect the retained proposal, independently
   review the bounded result, then accept or reject it through W52821. File any
   broader live-concurrency proof as a follow-up rather than extending this
   slice.
7. [deferred follow-up] Exercise two real OS-user runners concurrently after
   the single-worker path is in ordinary use.
