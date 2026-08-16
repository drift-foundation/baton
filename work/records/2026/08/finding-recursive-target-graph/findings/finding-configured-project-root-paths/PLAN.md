# Plan

**Status — 2026-08-16:** active pre-cutover correction, sequenced after the
executable rename. W92 deployment and fresh-authority activation are blocked
until this plan reviews clean.

1. Revalidate every WS-6 root-catalog, resolver, activation, reference,
   bootstrap, packaging, and TUI assumption against the superseding decision
   in `FINDING.md` before editing implementation.
2. Define one strict `baton.json` root-entry shape that includes the explicit
   filesystem base needed to resolve each configured root. Keep durable asset
   addresses as `ROOT_ID:relative/path`; do not infer any base path.
3. Remove the runtime split in which ordinary clients know only root ids while
   selected verbs require a separately supplied `roots.json`. Reconcile the
   generated scaffold, activation, public CLI, TUI, examples, deployment
   assets, and documentation around the single explicit configuration.
4. Add workflow and packaged regressions with the coordination home,
   distribution, current working directory, and repository roots in unrelated
   locations. Prove that configured roots resolve and that absent, ambiguous,
   or inferred paths refuse instead of consulting host conventions.
5. Verify focused coverage and `just test-v11`, then return for review before
   the next immutable v11 distribution. Do not modify the current trial or
   v10 production deployment.

6. Update W92's runbook, scaffold/config examples, and recreation proof to use
   the accepted `baton.json` root base directly. Remove `roots.json` and
   `--roots-file` only from current runtime surfaces made obsolete by the
   confirmed single-config model; preserve frozen historical evidence.

**Closed satisfying — 2026-08-16 11:21Z.** Final review is clean at
`review-2026-08-16T11-21-53Z.md`; the live Work closed at authority sequence
141. The implementation reports 636 parallel plus 3 serial tests green and
the final targeted stale-text sweep/diff check pass. W4 is removed from W92's
recreation set. Deployment remains held by the continuing pre-cutover audit
and its other same-schema corrections.
