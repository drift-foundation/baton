# Plan

1. [done] Record the two managed-turn failures and the confirmed bounded
   pre-approval rule.
2. [done] Update `docs/PROPOSAL-INTEGRATOR.md` and `AGENTS.md` with
   whole-path-set preflight before any mutation, the three required approval
   facts, generic-approval insufficiency, candidate-bounded authority, refusal,
   and the prohibition on interactive approval requests.
3. [done] Preserve the reviewed generation-5 evidence and prepare a
   generation-6 candidate under this record. Its accepted-config delta is only
   the generation number and `teams.baton.roles.integ.instructions`; retain the
   candidate digest and an approver rollout/fresh-context checklist.
4. [done] Add a new focused W71459 test module covering the durable
   policy/role/config parity, all positive and refusal wording, and the exact
   generation-5-to-6 delta. Run it with the W65212 deployment guard and the
   existing role/configuration regression slice; do not edit existing test
   expectations without a separately recorded case-specific approval.
5. [done; signed off 2026-09-02] Independent re-review accepts the policy,
   role, exact generation-6 candidate, corrected rollout checklist, and its
   ordering guard. See `review-2026-09-02T20-47-25Z.md`.
6. [done; live acceptance failed 2026-09-02] Place W33937's digest-bound
   four-test-path approval in an explicit `baton.ops` handoff, begin the
   deployment drain, recover the exact W33937 claim under that drain fence, and
   verify dispatch reaches `paused`. Then stop, accept generation 6, and restart
   into a fresh integrator context for the retry. The semantic preflight accepted
   the handoff, but the lower Codex execution policy still requested interactive
   approval on the first existing-test edit and quarantined the context.
7. [done; bounded operator fallback] The failed episode remains evidence and
   the independently reviewed six-path W33937 candidate was imported and
   verified by the operator. W33937 closed satisfying; this fallback is not
   represented as managed integration.
8. [done; approver selected fail-closed operator repair] Retained
   W61984 and W64268 managed sessions show that `baton.merge` used
   `cp --preserve=mode --parents` from frozen custody, copying its deliberate
   `0444` protection mode into live targets. Slawomir selected fail-closed
   operator repair: existing targets must already be owner-writable non-symlink
   regular files matching reviewed base bytes; otherwise the whole import
   refuses before mutation and returns to `baton.ops`. No privileged
   `install`/`chmod` capability is added. Planned new regular files use ordinary
   non-executable repository mode; executable mode requires explicit scope.
9. [done; independently signed off 2026-09-02] Update `AGENTS.md`,
   `docs/PROPOSAL-INTEGRATOR.md`, and a new generation-7 deployment candidate
   with the confirmed mode boundary and clarified test-change authority. Keep
   generation 6 immutable. Add a new focused test module rather than weakening
   existing expectations; the scheduled scope explicitly authorizes these
   additive policy/configuration regressions.
10. [decomposed; pending approver execution] Complete the three accountable
    child gates:
    - W72003: accept/deploy the exact reviewed generation-7 candidate and prove
      a fresh healthy `baton.merge` runtime;
    - W72011, blocked on W72003: prepare, independently review, and import one
      exact scheduled additive change to an owner-writable existing test
      without prompt or custody-mode leakage; and
    - W72013, blocked on W72003: use separate immutable candidates to prove an
      otherwise authorized read-only target and an owner-writable out-of-scope
      test both refuse before any content or mode mutation.
11. [pending final independent assessment] After W72003, W72011, and W72013
    close satisfying, review their retained configuration, proposal, preflight,
    runtime, byte, mode, and refusal/completion evidence. Close W71459 only if
    the whole acceptance boundary is demonstrated.
