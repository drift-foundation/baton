# Verification — staged W10198 successors

Run on 2026-08-25 without modifying the live deployment inputs.

## Structural and policy preflight

`python3 successor/verify.py`:

```text
infra preflight: 6 contexts, 8 services, existing Baton entries unchanged
pc topology: 3 Codex targets, 2 readiness consumers, 1 Claude ACP service
working directory: /home/sl/src/pushcoin; Gemini references: 0
Pushcoin policy: protocol 11, five pc.* identities, permanent dossiers
```

`node successor/verify.mjs`:

```text
dispatcher preflight: 6 unique targets
execution policy: 6 exact participant profiles + Docker inspection profile
ACP preflight: pc.code/impl policy resources readable from staged set
```

The lifecycle check loads a temporary in-memory-path-adjusted copy of the
literal-install manifest, so it reads the staged templates rather than the
still-live predecessors. No service or context is launched.

## Syntax and hard-policy probes

- All four JSON inputs pass `jq empty`.
- Both policy shell scripts pass `bash -n`.
- `git_guard.py` compiles successfully.
- `git diff --check` is allowed by the guard.
- `git commit -m prohibited` is denied with exit 2.
- nested `bash -lc git\\ add\\ .` is denied with exit 2.

## Live baseline hashes

The exact read-only source inputs are pinned in
`successor/SOURCE-SHA256SUMS`. The operator recipe requires those hashes to
match before drain, making later live drift a stop-and-re-review condition.

## Independent-review correction

The staged `pushcoin-AGENTS.md` replaces retired protocol-10 commands,
`pushcoin.reviewer`/`pushcoin.implementer`, and ephemeral `work/finding-*`
dossiers with protocol 11, the accepted five `pc.*` identities, standalone
canonical operations, and permanent `work/records/YYYY/MM/...` records. The
operator recipe backs up, installs, and byte-verifies this policy before start.
The live Pushcoin file remains unchanged during staging.

## Post-cutover verification and reconciliation staging

The initial cutover completed and controlled smoke W10856 closed
`satisfying`. Its canonical thread records the complete participant path:
`pc.plan` claimed at `pc.rsrch`, `pc.code` claimed at `pc.impl`, independent
`pc.plan` review received the Work at `pc.rsrch`, and `pc.slaw` closed it from
`pc.ops`. The smoke verified the exact Pushcoin working directory, performed
no repository writes, and confirmed that the kernel read-only mount refuses a
write beneath `/home/sl/src/pushcoin/.git`.

Canonical `runtime` at snapshot 11291 showed `pc.prompt`, `pc.plan`,
`pc.tuner`, and `pc.code` live and idle with no cause/detail failure;
`pc.code` reported `/home/sl/src/pushcoin` as its configured workdir.
`pc.slaw` remained offline with no runner, as designed. The isolated
`pc.code` credential exists as a regular mode-600 file; its contents were not
read or emitted.

The smoke also exposed the missing authentication and locator preflights now
recorded in `FINDING.md`. The corrected staged set exports exact Baton
binary/config/participant/role values into the ACP agent environment, requires
the runner to validate them, provisions credentials without packaging or
printing them, and uses registered endpoints rather than the nonexistent
`pc.rview` spelling.

Re-run staging evidence:

```text
infra preflight: 6 contexts, 8 services, existing Baton entries unchanged
pc topology: 3 Codex targets, 2 readiness consumers, 1 Claude ACP service
pc.code launch contract: exact Baton locators and identity exported
working directory: /home/sl/src/pushcoin; Gemini references: 0
Pushcoin policy: protocol 11, five pc.* identities, permanent dossiers
dispatcher preflight: 6 unique targets
execution policy: 6 exact participant profiles + Docker inspection profile
ACP preflight: pc.code/impl policy resources readable from staged set
ACP locator preflight: exact binary/config/participant/role exported
```

All four JSON inputs and both policy shell scripts pass syntax checks. The
managed tuner could not independently run `tools/infra.py status` because the
read-only lifecycle operation opens `run/infra.lock` for writing and the
managed sandbox refused that path with `EROFS`; policy forbids escalation.
The operator-owned reconciliation therefore retains lifecycle `status` as an
explicit gate, alongside canonical `runtime`, rendered-context equality, and
a fresh authentication/locator smoke.
