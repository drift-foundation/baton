# Plan — next Baton release

1. **Rule the release envelope** — **done 2026-08-11; updated 2026-08-12**:
   1.1.0, protocol 10, `examples/baton.json` included, editor-exit
   confirmation and whole-message save required; bulk archive deferred to
   protocol 11; polling reliability deferred.
2. **Audit and authorize 1.0 finding cleanup** — cleanup/reconciliation is
   authorized as needed, but deletion waits for a deliberate Git-owned pass
   after current 1.1 work lands.
3. **Establish isolation** — **ruled 2026-08-11**. No branch gate. Continue
   source work here; keep frozen 1.0 artifacts/manifests untouched and build
   candidates in scratch roots.
4. **Gate candidate deployment tooling** — **source signed off 2026-08-11** in
   `finding-deployment-recipe/review-2026-08-11T19-35-31Z.md`. Actual
   versioned candidate publication and deployed-path verification remain steps
   14–16 after coherent 1.1 artifacts/manifests exist. Permanent production
   destination remains next-major.
5. **Close the current materialization review** — **done and signed off
   2026-08-11**. Whole-message save remains governed by step 11.
6. **Gate TUI search** — **current MESSAGES/Sent source signed off 2026-08-11**
   in `finding-tui-message-search/review-2026-08-11T17-33-45Z.md`. Archived-view
   search remains a later Archive integration gate, and Slawomir performs the
   complete human trial during the deployed-candidate soak.
7. **Implement and review scoped-notice authoring** — **done and signed off
   2026-08-11**, including retained-audience and draft-version compatibility.
8. **Implement editor-exit confirmation** — **done and source signed off
   2026-08-11** in
   `finding-human-console/findings/finding-editor-send-confirmation/review-2026-08-11T18-25-02Z.md`.
   Final candidate build and human soak remain steps 14–16.
9. **Correct config-regen wording** — **source docs independently signed off
   2026-08-11** in
   `finding-config-regen-wording/review-2026-08-11T19-39-32Z.md`; candidate
   hash verification remains pending. No behavior or authority-schema change.
10. **Defer polling reliability** — **deferred by Slawomir 2026-08-11**. Keep
    the finding; do not make it a 1.1 release gate.
11. **Implement whole-message save** — **done and source signed off
    2026-08-11** in
    `finding-save-message/review-2026-08-11T23-26-58Z.md`. The ruled
    deterministic `.baton.json`, exact `baton save --output`, fixed-target TUI
    `M` path flow, transient refusal, external references, and
    no-clobber/idempotent publication pass focused and packaged-PTY review.
    Candidate exercise remains steps 14–16.
12. **Withdraw and defer bulk select/archive** — **ruled 2026-08-12**. SQLite
    is the metastore owner for participant-scoped archive metadata, so the
    protocol-10 JSON/UI implementation must not ship. K withdraws that scoped
    implementation and its tests/help while preserving independently approved
    1.1 work; the reviewer verifies the withdrawal. Protocol 11 owns the future
    schema and implementation.
13. **Reconcile included findings** — **done 2026-08-12**. The scoped-
    audience parent already marks its older WIP checkpoint superseded rather
    than deleting history; every included source finding has a current
    append-only approval. K reconciled the implementer-owned next-release,
    save-message, and search progress records to the final pre-RC state.
14. **Build the RC candidate** — **cleared for Slawomir 2026-08-12** after the
    scoped withdrawal approval and included-finding reconciliation.
    `baton.reviewer` sends the ruled direct Baton ping; Slawomir runs
    `just deploy DEST 1.1.0` to build
    and publish the 1.1.0 `baton` and `baton-tui` RC binaries into the chosen
    non-production, versioned candidate root. An agent does not choose `DEST`
    or run the deployment.
15. **Soak the RC candidate** — Slawomir uses those RC binaries against the
    existing protocol-10 mailbox. Do not replace frozen 1.0 repository
    artifacts or activate a stable production pointer.
16. **Independent release gate and human trial** — full suite, deterministic
    rebuild, artifact/manifest verification, CLI workflow, TUI trial including
    search, docs, and clean scoped diff; incorporate soak findings.
17. **Release decision** — Slawomir alone rebuilds/replaces release artifacts,
    commits, and tags. Production activation/permanent external deployment
    remains a separate next-major decision.

`baton.implementer` creates and exclusively writes `PROGRESS.md` when this
umbrella is accepted and started.

Baton 2.0.0's recursive-target architectural restart is recorded in
`work/finding-recursive-target-graph/` and is explicitly outside this 1.1 plan.
It does not delay or broaden the immediate release.
