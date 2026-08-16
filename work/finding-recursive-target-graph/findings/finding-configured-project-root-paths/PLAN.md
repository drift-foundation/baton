# Plan

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
