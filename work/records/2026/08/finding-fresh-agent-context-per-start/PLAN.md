# Plan

1. [done 2026-08-19 — slice 1: contexts mint after their `after`
   services are ready] Define lifecycle ordering: app-server, fresh role/session
   bootstrap, runtime target map, dispatcher/readiness, then ACP workers.
2. [done 2026-08-19 — Codex and ACP managed-start freshness signed off]
   Remove static Codex Thread ids from the operator-maintained
   deployment contract, persist runtime locators only under private `run/`
   state, and ensure every configured ACP participant receives fresh selection
   state on a later managed start without weakening W27's same-run refusal.
3. [done 2026-08-19 at the controller level] Add restart coverage proving two starts mint different contexts
   while preserving participant-relative Work recovery.
4. [done 2026-08-19 at the controller level] Cover partial bootstrap failure and cleanup without adopting or
   reusing an older context.
5. [awaiting operator 2026-08-19 — controller/authority proof accepted;
   real Codex + ACP two-start deployment proof remains] Obtain independent
   review and deployment proof.
