# Plan

1. [done] Preserve W52821 run5b's candidate, evidence and exact verification
   failures without importing the proposal.
2. [done, reviewer revalidation 2026-09-01] Trace the frozen task, input
   manifest, source staging, worker `_verify`, custody and operator `_derived`
   boundaries. The worker uses a closed environment missing the import root;
   the operator inherits ambient environment; neither has a repository-shaped
   immutable evidence source or a context outcome vocabulary.
3. [done, baseline] Reproduce 99 pass/3 missing-fixture errors in an isolated
   candidate copy, then materialize the candidate at `v12/python`, the one
   vector at its canonical `work/records/...` path, `cwd=v12/python` and
   `PYTHONPATH=src`. The exact 102-test vector passes. Evidence:
   `evidence/research-2026-09-01/README.md`.
4. [done, approved 2026-09-01] Use a Python-specific contained relative import
   root list with no arbitrary environment map; use task-selected contained
   relative working/candidate/input paths; and record separate closed context
   and command-result axes. Preserve task v1 as a refusing frozen contract
   rather than widening it in place.
5. [pending explicit scheduling] In a fresh isolated v12 attempt, stage a
   second manager-copied immutable input source and materialize fresh private
   review roots for worker and operator. Keep the candidate output narrow and
   use no ambient environment or host path.
6. [pending verification] Add the missing/extra/type/path/overlap, absent
   input, context-versus-test-outcome, ambient-environment, no-mutation,
   cleanup and credential-free durable-surface matrix recorded in
   `FINDING.md`.
7. [pending independent gate] Run the W52821-equivalent 102-test vector with
   zero skips and zero context errors inside the worker and in a separately
   materialized operator review root.
8. [pending reviewer] Independently inspect and rerun the retained proposal
   before any repository import.
