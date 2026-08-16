# Finding: v11 clients cannot locate configured repositories from `baton.json`

## Observed

The fresh v11 coordination home declares only portable root metadata in
`baton.json`:

```json
"roots": {
  "baton": {
    "display": "Baton repository"
  }
}
```

The absolute checkout mapping currently lives in a separate sibling
`roots.json`. Ordinary clients are launched with only `--config baton.json`,
and neither `home` nor `tui` accepts or automatically loads that resolver.
Only the explicit `resolve` and `bootstrap` commands currently accept
`--roots-file`. Consequently, the running TUI cannot derive that the durable
root id `baton` means `/home/sl/src/baton` and cannot reliably navigate assets
named by that root.

## Confirmed decision — 2026-08-15

**Confirmed by Slawomir during the second v11 trial. This explicitly
supersedes the earlier WS-6 ruling that `baton.json` declares only portable
root ids while a separately supplied machine-local resolver owns their
absolute paths.**

`baton.json` must configure the actual filesystem base for every source or
repository root used by that coordination instance. A client that has opened
and validated the explicit `baton.json` must have enough configuration to
resolve `ROOT_ID:relative/path`; it must not need an inferred or separately
discovered resolver merely to know where the configured repositories are.

There are no implicit filesystem paths. In particular, Baton must not infer a
repository from:

- the coordination home's directory;
- the process current working directory;
- the executable or distribution directory;
- `$HOME`, `~/src`, or another host convention;
- a team, participant, Work item, or root display name; or
- the incidental presence of a sibling file.

The distribution root, coordination home, and project repositories remain
distinct ownership domains. This correction changes how their explicit
association is configured; it does not make one path derivable from another.
`init` may scaffold incomplete root entries for the operator to edit, but
`activate` and every later client must consume the explicit accepted
`baton.json` configuration rather than filesystem guesses.

The second trial may continue with its known limitation while feedback is
collected. This finding is queued for the next revision; no live immutable
distribution or activated authority is rewritten in place.

## Scheduling correction — 2026-08-16

**Confirmed by Slawomir before schema-15 deployment.** W92 is the “next
revision” named above. This correction does not require a SQLite schema
change; it changes the strict `baton.json` configuration contract and runtime
root resolution. Deferring it until after the fresh authority is activated
would require immediately replacing or regenerating the configuration that
was supposed to bootstrap that authority.

Commit `6fe32fd` still accepts only `{ "display": ... }` in each
`baton.json` root entry and keeps absolute bases in separate `roots.json` input
used by selected commands. Its W92 runbook nevertheless tells the operator to
configure the repository root before activation. Adding the required base to
the committed strict config would be rejected as an unknown field, while
omitting it leaves ordinary clients unable to resolve repository assets.

Therefore this finding is a pre-cutover prerequisite. It must implement and
review the single-config model before the next immutable v11 distribution is
deployed or the fresh authority is initialized. Historical trial homes and
distributions remain unchanged; v10 remains untouched.
