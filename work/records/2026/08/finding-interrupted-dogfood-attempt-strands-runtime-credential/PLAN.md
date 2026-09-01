# Plan

1. [done] Preserve the run7 temporary tree, stop the exact runtime, remove the
   bearer without reading it, and keep the partial workspace output untrusted.
2. [done] Inventory run7 through safe filesystem metadata and public v12
   manager surfaces. Redacted scripts/results are under `evidence/`; no store
   was opened directly and no credential content was read, copied or hashed.
3. [done] Trace `dogfood_operator`, `abandon_attempt`, OCI runtime removal,
   credential recovery/teardown and narrow handoff retry across an interrupted
   process and restart.
4. [done] Reproduce the post-discard recovery gap against an offline copy.
   The granted and assignment-derived credential homes split root from record;
   adoption refuses, the retry builder sees no delivery, and positive absence
   would be misreported as `not-delivered`.
5. [done: reviewer proposal; revalidate at implementation] Record the recovery
   contract: explicit W44716 abandonment, one credential-home owner, no-read
   orphan teardown after positive runtime absence, a public recovery mode that
   does not require lost evidence or a credential, no partial-output
   acceptance, and exact replay/idempotence.
6. [done] Add the ruled
   recovery path and credential teardown that does not depend on the ordinary
   arc reaching freeze/intake. Reuse `abandon_attempt` when a runtime is
   attached; a pre-attach interruption instead receives exact bounded orphan
   cleanup and invents no terminal attempt. Do not create a second authority
   fence/runtime/terminal ending. The credential-home contract is option (a)
   and the accepted grants contract does not move.
7. [partly done — see PROGRESS for the exact uncovered cases] Cover
   interruption at every boundary from credential
   materialization through freeze, runtime present/absent/uncertain,
   credential present/absent/mismatched, process restart, repeated recovery,
   provider failures, real non-secret credential restart, and refusal to
   accept partial output. Re-run the three recorded 557-test baseline suites.
8. [review] Independently verify exact runtime/credential absence, durable
   ending, no bearer publication, no newer-attempt action and no automatic
   acceptance of the interrupted workspace.

## 2026-09-01 implementer round

9. [done] The credential-home contract is recorded as option (a): one owned
   `CredentialHome` capability shared by materialization, publication, retry
   and teardown. Option (b) would move the accepted grants contract and needs
   a supersession; none is appended.
10. [done, and it refutes my own filing] `discard_orphan` does NOT foreclose
    `abandon_attempt`. A recovery-shaped adapter answers
    `{'lifecycle_state': 'not-delivered'}` for the credential — reachable, and
    a false positive claim rather than a refusal. The recovery command must
    carry the credential owner so the ending says `torn-down` or `unresolved`.
11. [done; signed off in review 2026-09-01T03-45-20Z] Both decisions above,
    before item 6 proceeds. The reviewer revalidated the false `not-delivered`
    ending and option (a), and pinned the pre-attach cleanup clarification.

## 2026-09-01 second implementer round

12. [done] `credentials.OrphanTeardown` plus `CredentialHome.orphan_evidence`
    and `.tear_down_orphan`: a typed, exact-record, no-read ending for a
    credential whose materializing process is gone. It holds both proved homes
    so the legacy run7/run8 split is ended by HOLDING both, never by following
    the `credential_root` member of a record.
13. [done] `OciAdapter` takes `credential_home` (option (a)'s one owner) and
    `credential_orphan`. `_torn_down` answers `torn-down` after positive
    absence and `unresolved` without it; `not-delivered` survives only where
    nothing was ever delivered. An adapter holding both a delivery and an
    orphan is refused.
14. [done] `attempt_runtime_of` is a new public read, and it exists so the
    recovery branches on durable manager state rather than on the wording of
    a refusal. `label_context` is exported for the pre-attach proof.
15. [done] `dogfood_operator --abandon --abandon-reason` with `_for_abandonment`
    and `recover_abandoned`: two branches on that read, a new closed
    `RECOVERY_MEMBERS` document under the same three write holds, no
    credential operand, no restage/offer/claim/provider/freeze/intake/
    retention/pass, and the workspace output neither read nor promoted.
16. [done] `_launched` and `_for_retry` now pass the granted `CredentialHome`
    into the adapter, so materialization, publication, adoption and teardown
    have one owner.
17. [partly done] 29 new regressions. The uncovered matrix rows are named
    exactly in PROGRESS.md rather than implied to be covered.
