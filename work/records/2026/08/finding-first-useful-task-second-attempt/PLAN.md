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
7. [done; independently reviewed with changes requested] `attempt-w51487-run4`
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
   `evidence/w51487-run4/`. Independent review found that the nominated-engine
   case supplies and expects the same literal `"docker"`, so it cannot catch a
   production hard-code of that value. Review:
   `review-2026-08-31T17-15-35Z.md`.
8. [attempted twice; blocked, not abandoned] Produce a clean fresh result whose
   test injects a non-default engine sentinel and proves `_observed_readable`
   forwards it. Preserve the remainder of run4's test-only patch and verify
   that a literal `"docker"` substitution in production is caught. Return the
   retained result for independent review; do not mutate run4's retained
   candidate or apply it automatically to the canonical checkout.

   The review's finding was first confirmed by mutation against a writable copy
   of the retained candidate — the literal-`"docker"` substitution leaves the
   harness at exit 0 while the other six mutations are each caught
   (`evidence/w51487-run5/run4-engine-recheck.md`). `attempt-w51487-run5` and
   `attempt-w51487-run6` then both resolved `retained` with `provider-failed`,
   status 1 and an untouched candidate, so no correction was produced.
   Acceptance record: `acceptance-2026-08-31T17-26Z.md`.
9. [blocked on the operator] Verify or refresh the staged credential source
   `/run/baton/credentials/claude` without publishing its bytes, or report that
   the account itself is refusing. run6 excludes the rebuilt worker image by
   control; delivery, task, network, posture, retention, arc and credential
   READABILITY are all measured good. Until this is settled an unchanged retry
   reproduces the same result, so item 8 does not resume.
10. [ruled] The rebuild-per-attempt instruction in item 7's handoff is
    superseded by the approver ruling at W55361 event 55641: reuse the image
    already selected by immutable digest, and rebuild only on an explicit
    upgrade/source/security/platform/refresh event, validating and recording
    the new digest before selecting it. The selected digest is
    `sha256:8af96742…`, whose four `COPY` layers are byte-identical to run4's
    accepted artefact. Appended to `FINDING.md` under the implementer claim, as
    M55659 asked.
