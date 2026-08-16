# Plan — next Baton release

1. **Rule the release envelope** — **done 2026-08-11; updated 2026-08-12**:
   1.1.0, protocol 10, `examples/baton.json` included, editor-exit
   confirmation and whole-message save required; bulk archive deferred to
   protocol 11; polling reliability deferred.
2. **Audit and authorize 1.0 finding cleanup** — **partially complete
   2026-08-12**. Nine audited folders are removed in the current filesystem
   change. Correct the dangling durable-doc citation before sign-off. Retain
   `finding-human-console` until its permanent test dependency is moved or
   retired, and retain `finding-protocol-10-umbrella` until its still-live
   decision provenance and cutover index have an explicit owner.
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
14. **Build the RC candidate — built; post-build gate reopened:** the
    independently versioned product catalog and set-digest deployment redesign
    are approved in
    `finding-product-version-manifest/review-2026-08-12T18-40-02Z.md`.
    The one release-facing `just build` that prepares the complete CLI/TUI set
    is approved in
    `finding-product-version-manifest/review-2026-08-12T20-36-21Z.md`.
    Slawomir ran the single build and currency failures cleared. The first
    harness correction passed a synthetic reviewer environment, but the bare
    human rerun still failed 12 PTY cases. See
    `finding-product-version-manifest/findings/finding-post-build-test-gate/review-2026-08-12T21-33-09Z.md`.
    Deploy is not authorized. An agent does not choose `DEST`, rebuild release
    artifacts, or deploy them.
15. **Soak the RC candidate** — Slawomir uses those RC binaries against the
    existing protocol-10 mailbox. Do not replace frozen 1.0 repository
    artifacts or activate a stable production pointer.
16. **Independent release gate and human trial** — full suite, deterministic
    rebuild, artifact/manifest verification, CLI workflow, TUI trial including
    search, docs, and clean scoped diff; incorporate soak findings. After the
    product-manifest handoff and approval, human artifact build, and clean
    currency/full-suite gates, `baton.reviewer` explicitly notifies
    `human.slawomir` through Baton that deployment/activation/soak testing may
    begin.
17. **Release decision** — Slawomir alone rebuilds/replaces release artifacts,
    commits, and tags. Production activation/permanent external deployment
    remains a separate next-major decision.

`baton.implementer` creates and exclusively writes `PROGRESS.md` when this
umbrella is accepted and started.

Baton 2.0.0's recursive-target architectural restart is recorded in
`work/records/2026/08/finding-recursive-target-graph/` and is explicitly outside this 1.1 plan.
It does not delay or broaden the immediate release.
