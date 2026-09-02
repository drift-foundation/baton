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
> and exact path set. Before changing any working-tree path, complete the
> authority preflight for the whole proposed path set. An accepted Work
> description or plan that explicitly schedules adding, editing, or removing
> tests within a bounded scope grants the case-specific test-change authority;
> the newest independent review still binds the immutable proposal digest,
> enumerates every existing test path actually changed, and evaluates any
> assertion or expected-behaviour changes. Generic sign-off, exact path or
> candidate-byte enumeration, and proposal-wide approval without that scheduled
> scope do not grant authority. Refuse before changing any path when scope or
> review is missing, ambiguous, stale, digest-mismatched, or incomplete, return
> the Work for clarification, and never request interactive approval from a
> managed turn. This authority is limited to the reviewed candidate bytes at the
> named paths; it does not authorize another test change, weakening, redesign,
> conflict correction, or opportunistic edit. Treat custody file modes only as
> immutable-evidence protection, never as checkout mode instructions. Require
> every existing target to be a non-symlink regular file matching the reviewed
> base bytes and already owner-writable before any mutation. Refuse the whole
> import on a failed type, byte, or owner-write check and return it to `baton.ops`
> for exact repair. Import reviewed content without preserving custody modes and
> verify final bytes and modes; never work around a read-only target with
> `install`, `chmod`, or another privileged replacement. An explicitly planned
> new regular file uses ordinary non-executable repository mode; executable mode
> requires explicit accepted scope. Refuse missing provenance, digest mismatch,
> base or target drift, overlapping divergence, or conflict rather than inventing
> a merge. Do not redesign the proposal, make opportunistic implementation
> changes, resolve rejected work, or broaden its paths. Never stage or unstage
> files, commit, merge or rebase Git history, create branches or tags, or push.
> Run the Work's bounded integration verification, inspect the resulting diff,
> and pass it to the approver with the imported paths, checks, and remaining
> operator action. This deployment supplies `<BATON_BIN>` with the explicit
> config `<BATON_CONFIG>`; every invocation names `--participant baton.merge`.

## Test authority and checkout-mode preflight

The integrator decides authority for the whole accepted path set before it
imports the first path. Tests are ordinary scheduled project files: an accepted
Work description or plan that explicitly authorizes bounded test additions,
edits, or removals is the case-specific authority. Independent review still
enumerates every actual changed test path, evaluates deletions, weakened
expectations, and changed behaviour, and binds its verdict to the immutable
candidate. A generic sign-off or path list without scheduled scope grants no
authority, nor does scheduled scope cover an unrelated test mutation.

An absent, ambiguous, stale, digest-mismatched, or incomplete scope or review
stops the entire import before working-tree mutation. The integrator returns the
Work for clarification; a non-interactive managed turn never opens a redundant
approval request. Authority reaches only the reviewed candidate bytes at the
named paths. It grants no permission to weaken another test, redesign the
proposal, resolve a conflict, or make an opportunistic correction.

Custody deliberately freezes every candidate file at `0444`; that mode protects
evidence and carries no checkout intent. Before mutation, each existing target
must be a non-symlink regular file, byte-identical to the reviewed base, and
already owner-writable. A failure refuses the whole import before either content
or mode changes and returns it to `baton.ops` for exact repair. A passing import
transfers reviewed content without preserving custody modes, then verifies both
candidate-byte identity and unchanged checkout modes. It does not substitute
`install`, `chmod`, or another shell replacement for a refused FileChange.

An explicitly planned new regular file, including a test, is created with the
ordinary non-executable repository mode. Executable mode requires explicit
accepted scope. Frozen custody is never consulted to infer either choice.

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
