# Plan

## Current disposition — 2026-09-07

Owner accepted the exact signed-off four-path candidate; all four hashes still
match the final review. The bounded capability is complete and available to the
manifest composer. Earlier planning and review stages below are historical;
actual live access/custody remains in its separately bound providers. No Git or
deployment action is part of this disposition.

1. [done; baton.claude 2026-09-06] Revalidate the private-line and
   concrete-worker output contracts. Outcome in FINDING: the persistent line,
   the real head, the retained checkpoint ref and correction continuity all
   have reusable substrate and retained-ref evidence in
   `test_checkpoint_profiles.test_real_git_keeps_an_old_checkpoint_after_the_
   line_advances`. The concrete worker never commits and works in a copied
   non-repository tree the line cannot see. Independent review below identifies
   the additional completion/correction and compatibility seams needed before
   this becomes an implementation-ready plan.
2. [superseded; baton.claude 2026-09-06] The first pinned design, claim, path
   set and test scope. Kept in FINDING as history: it is how a two-file answer
   that did not survive its own completion path was reached, and why the
   selector in item 3 is not overengineering.
3. [done; baton.claude 2026-09-06] Revise the dossier-only plan against
   `review-2026-09-06T23-54-31Z.md`. Every correction was re-checked against
   the tree and held. The revised plan in FINDING pins: a third source-profile
   word `git-line` so the workload is selected and never inferred; an explicit
   three-row compatibility matrix in which `generic` and non-line `git` are
   untouched; immutable base B and turn-entry head E as separate facts, with
   the claim's `base` staying B so `source_base == target_revision` survives
   every correction round; reserved control/output paths including the
   completion document, its staging name and the manager's `result-*`
   namespace, written before the entry cleanliness check, with tracked-path
   collision and gitignore-metacharacter refusals; one worker commit whose
   parent is E, proved by `Hn^ == E` and by comparing `cat-file blob` against
   the already measured bytes; and a cumulative `B..Hn` bundle resolved from a
   recipient holding only B. Path set is now two production files
   (`source_profiles/checkout.py`, `worker/claude_agent.py`) and two additive
   test files. The earlier existing-test-change request is WITHDRAWN: keeping
   `proposal/candidate/` for the existing workloads makes it unnecessary.
4. [review done; owner accepted 2026-09-07] Independent re-review
   `review-2026-09-07T00-09-06Z.md` recommends the four-path revised plan WITH
   the FINDING's 2026-09-07 amendments: per-command hook suppression, complete
   committed-change identity including deletions, and additive hook/filter/
   deletion proofs. Owner acceptance authorizes this bounded implementation;
   existing tests remain additive-only and Git ownership rules remain intact.
5. [separate provider] Runtime access provisioning is recorded in
   `work/records/2026/09/finding-v12-private-line-runtime-access/`.
   The 2026-09-07 source correction supersedes the alleged missing-root
   refusal: custody derives the ordinary attempt root, not the substituted
   line root. Triage produced the separate line-custody provider W105982 at
   `work/records/2026/09/finding-v12-private-line-custody-locators/`.
   Live assembly needs both providers; bounded worker acceptance is independent.
6. [done; baton.claude 2026-09-07] Implemented the real head and the declared
   durable object output in the two accepted production paths, with strictly
   additive coverage in the two accepted test paths — 543 test lines added and
   none removed, so no existing assertion changed. All four inputs matched the
   re-review's recorded digests before the first edit. Every accepted amendment
   is in: `core.hooksPath` suppression with a mutating `prepare-commit-msg`
   hook proved not to run; complete measured/committed equality by exact path
   set, raw blob comparison, deletion absence and a content-filter refusal.
   The bundle's advertised reference is settled by execution — `<base>..HEAD`
   resolves for a recipient holding only the base — and real completion
   publication precedes a successful `GitCheckpointProfile.freeze` over the
   same line, twice, against an unchanged base.
7. [original cases resolved; independent correction review 2026-09-07]
   `review-2026-09-07T01-06-23Z.md` reproduces missing measured-to-committed
   inclusion for an ignored verification dependency, execution of an index
   hook, and stale bundle retention on a no-op correction. Their probes now
   pass in retained correction evidence and the corresponding fixes were
   inspected in `review-2026-09-07T01-16-13Z.md`.
8. [resolved; independent review 2026-09-07] Complete byte equality now compares
   every measured candidate file with its committed blob through one batch,
   regardless of Git status/diff membership. The tracked-byte probe passes in
   retained evidence; reviewed in `review-2026-09-07T01-22-56Z.md`.
9. [signed off; pending owner acceptance/closure] The same review binds the
   four final candidate hashes and supplies the worker claim contract for the
   manifest composer. All candidate findings are resolved at this bounded
   capability; live assembly remains separately gated. No generic Git adapter, no bulk
   archive work, and no change to the generic Worker Manager or integration
   coordinator. Runtime-access and line-custody remain separate providers.
