# Plan

1. [done] Record the distinct integration role, its initial workflow boundary,
   refusal rules, Git boundary and W61984 first-use artifact.
2. [in progress] Add `baton.merge`, role/route `integ`, and kind `merge` to the
   Baton configuration and durable role instructions. Repository policy and
   role contract are implemented; live generation acceptance remains.
3. [in progress] Add the dedicated Codex context, dispatcher target, readiness
   consumer and exact execution-policy generation for `baton.merge`. Shipped
   templates and guards are implemented; live policy installation remains.
4. [pending] Validate and accept the next configuration generation, drain and
   restart the managed stack, and prove the integrator target healthy.
5. [pending] Route W61984 to `baton.integ`; have the new participant claim it,
   import only the independently signed run10 proposal, run bounded integration
   verification and pass the resulting working-tree diff to `baton.ops`.
6. [pending] Independently verify the first integration evidence and record any
   general v12 integration-stage requirements discovered by the trial.
