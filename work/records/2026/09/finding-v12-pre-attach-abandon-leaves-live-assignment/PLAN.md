# Plan

1. [done] Preserve W61984 run3 recovery and confirm through the public v12
   authority projection that its exact assignment remains active.
2. [done research] Traced the branch: `_pre_attach_recovered` receives no
   authority capability or reason and resolves from resource cleanup alone.
   Ordinary cancellation and attached abandonment have intentionally different
   capability/precondition sets; neither may be invoked with fabricated or
   weakened operands.
3. [approved 2026-09-02; pending isolated v12 scheduling] Factor the attached abandonment's durable intent
   and exact `AuthorityPort.cancel` crossing into a public pre-attach fence
   operation. Atomically commit the intent plus a state that blocks runtime
   start, fence the adopted exact assignment, record the fence, then continue
   existing positive-absence and resource cleanup. Require the exact fence
   before `resolved`; leave W61984's disposition precondition unchanged.
4. [pending review] Prove command-level exact fence and public authority
   projection; same-reason replay, changed-reason collision, wrong identity,
   start-versus-abandon races, crashes before/after the fence, no-runtime,
   no-credential and no-artifact-decision behavior. Re-run abandonment,
   cancellation, attempts, authority-port, dogfood operator and retry-engine
   gates.
