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
