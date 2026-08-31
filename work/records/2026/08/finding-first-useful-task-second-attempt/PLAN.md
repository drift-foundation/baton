# Plan

1. [done] Wait for retained candidate custody and terminal
   retained resolution to pass independent review.
2. [done: superseded by task-scoped grant] Record the approved fixed grants:
   credential source `/run/baton/credentials/claude`, Docker network `bridge`
   and retention disposition `retain`. No numeric attempt cap applies while
   the task and grants remain unchanged.
3. [done] Revalidate the frozen task and whole input-document pair without
   claim, runtime or provider side effects. Evidence:
   `dry-revalidation-2026-08-31T08-46-13Z.md`.
4. [done: rejected and credential refreshed] Attempt `attempt-w51487-run2` resolved
   `retained`; independent review rejected its unchanged candidate because the
   provider exited 1 before attempting the task. M52739 records replacement
   from the authenticated host source; reviewer metadata/readability and frozen
   source revalidation passed without opening the credential. Evidence:
   `evidence/w51487-run2/`; review: `review-2026-08-31T08-57-18Z.md`.
5. [done: rejected] Attempt `attempt-w51487-run3` again resolved `retained`
   with an unchanged candidate. The refreshed credential refutes the run2
   authentication inference; credential-free reproduction locates a manager
   `0600` slot that uid 65532 cannot read, while the worker checks existence
   rather than readability. Evidence: `evidence/w51487-run3/`; review:
   `review-2026-08-31T09-16-34Z.md`.
6. [done] Correct and independently review the separately accountable
   credential-slot runtime-readability defect in
   `findings/finding-runtime-credential-slot-readability/`. W52800 closed
   satisfying; sign-off:
   `findings/finding-runtime-credential-slot-readability/review-2026-08-31T16-20-31Z.md`.
7. [done; awaiting independent terminal disposition] `attempt-w51487-run4`
   ran under the unchanged task-scoped grant with wholly fresh identities and
   a worker image rebuilt from the W52800-corrected tree. Exit 0, terminal
   `retained`, and the provider turn HAPPENED: the candidate adds four cases
   establishing all four of the frozen task's required facts, removes nothing,
   and leaves `preflight.py` untouched. Six mutations are each caught by the
   case that owns their fact; the harness rerun outside the worker reports 30
   tests, OK. The worker's own `verification-failed` is measured to be a
   property of the frozen harness inside the container — the UNMODIFIED source
   fails the same two pre-existing cases there — rather than a defect in the
   candidate. Acceptance record: `acceptance-2026-08-31T16-40Z.md`; evidence:
   `evidence/w51487-run4/`. The terminal accept or reject for W38956 is the
   reviewer's.
