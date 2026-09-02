# Proposal integration

`baton.merge` is the dedicated managed Handler for the Baton team's `integ`
route. It sits between independent review and human approval:

```text
implementation -> independent review -> integration -> approval/commit
```

Integration here means importing an accepted immutable proposal into the
current working tree and proving the resulting diff is ready for the human Git
owner. It does not mean merging Git history.

## Role contract

The accepted configuration should carry this role text, with the deployment's
installed binary and explicit config paths substituted where shown:

> You are `baton.merge`, the dedicated proposal integrator. Before your first
> assignment read `baton:AGENTS.md`, `baton:docs/EFFECTIVE-BATON.md`, the exact
> Work dossier, and its newest independent review. Own final integration review
> and import only the independently approved immutable proposal paths into the
> current working tree. Verify the review-bound digest, declared base, current target,
> and exact path set. Refuse missing provenance, digest mismatch, base
> or target drift, overlapping divergence, or conflict rather than inventing a
> merge. Do not redesign the proposal, make opportunistic implementation
> changes, resolve rejected work, or broaden its paths. Never stage or unstage
> files, commit, merge or rebase Git history, create branches or tags, or push.
> Run the Work's bounded integration verification, inspect the resulting diff,
> and pass it to the approver with the imported paths, checks, and remaining
> operator action. This deployment supplies `<BATON_BIN>` with the explicit
> config `<BATON_CONFIG>`; every invocation names `--participant baton.merge`.

For the Baton team, the corresponding accepted configuration shape is:

```json
{
  "kinds": {
    "merge": { "display": "Integration", "route": "integ" }
  },
  "participants": {
    "merge": { "display": "Integrator", "roles": ["integ"] }
  },
  "roles": {
    "integ": { "display": "Integrator", "instructions": "<role contract above>" }
  },
  "routes": {
    "integ": { "handlers": ["merge"], "role": "integ" }
  }
}
```

## Managed runtime

The shipped infrastructure and dispatcher templates provide the three distinct
pieces the participant needs:

- one fresh `integrator` Codex context launched as `baton.merge` with role
  `integ`;
- one `baton-integrator` dispatcher target bound to only that context and
  identity; and
- one `codex-integrator-readiness` consumer forwarding only `baton.merge`
  readiness to that target.

Generate the deployment-owned execution policy for every dispatcher target,
including `baton.merge`, into one staged file as documented in
`conf/codex-event-bridge.template.json`. The generator emits the exact managed
workflow operations and deliberately grants no Git command or broad shell
authority.

Configuration acceptance, drain/restart, and Git mutation remain approver
operations. After acceptance, prove the target is loadable with the lifecycle
status check, compare its fresh thread id with the runtime publication, and
route the first independently reviewed proposal to `baton.integ`.
