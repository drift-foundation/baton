# Plan: prove v12 local isolated execution

1. [done 2026-08-22] Bind W1425 to this canonical record and revalidate
   the assignment against the campaign decisions, W151 state machine, frozen
   M1 contracts, current `v12/` proof and available local OCI tooling.
1a. [implementation active as top-level W2845; live policy verified 2026-08-22]
   Provision and independently verify exact read-only
   managed policy rules for `docker version`, `docker info`,
   `docker inspect`, and `docker image inspect`. Keep every mutable Docker
   operation behind the future trusted Worker Manager adapter.
2. [done 2026-08-22] Pin the smallest implementation slices and their dependency order
   for the OCI reference worker, trusted Worker Manager/local runtime adapter,
   the required v12 assignment-authority substrate, and one complete local
   lifecycle proof: authority -> manager -> OCI worker/adapter -> conformance.
3. [done 2026-08-22] Define exact implementation ownership, acceptance evidence,
   positive/negative/race/restart tests and focused verification for each
   slice without pulling M3 proposal integration or M4 provider certification
   into M2.
4. [done 2026-08-22; approver message 2914] Keep M2 self-contained under
   `v12/`: its disposable v12 authority exclusively owns W151 state. Do not
   modify `src/baton_work/`, v11 behavior, or release surfaces.
5. [done 2026-08-22] Created and bound W2928 authority, W2929 manager,
   W2930 OCI worker/adapter and W2931 local proof. Established the explicit
   W2928 -> W2929 -> W2930 -> W2931 dependency chain; W1425 waits on W2931,
   and only W2928 is runnable at `baton.impl`.
6. [pending after children] Reconcile independently reviewed child results
   against the frozen M1 contract and return M2 for approval.
