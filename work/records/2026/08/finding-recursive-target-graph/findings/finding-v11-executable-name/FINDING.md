# Finding: the v11 distribution still installs `baton-work`

## Observed

The reviewed schema-15 cutover tree at commit `6fe32fd` still publishes and
documents:

```text
<release>/bin/baton-work
```

The schema-14 trial Work `8b92cb10-W2`, “Rename the v11 executable to baton”,
remains open, queued, ready, and Current `baton.bug`. It has no schema
dependency. W92 nevertheless placed it among Work to recreate after deploying
the next distribution.

## Confirmed decision — 2026-08-15

**Confirmed by Slawomir in the umbrella finding.** The product and installed
executable are named `baton`. `baton-work` was only a temporary development
name used to distinguish the experimental v11 engine from live v10. Protocol
generation and release identity belong in the immutable distribution path,
not in the executable name.

The already-deployed historical trials remain immutable under their existing
`bin/baton-work` paths. The next v11 distribution installs
`<release>/bin/baton` and all current-facing release documentation, examples,
machine-readable deploy output, generated next-step hints, and cutover
commands name that executable.

The repository recipe remains `just deploy-v11` while frozen v10 deployment
also exists. The internal packaging implementation may remain
`tools/deploy_work.py`; this finding changes the shipped product surface, not
the implementation module or the Python package name `baton_work`.

## Scheduling correction — 2026-08-16

**Confirmed by Slawomir before executing the W92 deploy.** W2 was incorrectly
scheduled for recreation after cutover. It is a same-schema prerequisite of
that cutover and must be implemented, reviewed, and closed satisfying before
another v11 distribution is deployed. Commit `6fe32fd` is a clean checkpoint,
not the distribution to launch.

W92 must remove W2 from the fresh-authority recreation set and update its
counts, runbook, and verification evidence after this correction. No v10
binary, deployment, mailbox, or coordination state changes.

## Acceptance boundary

- `just deploy-v11 NEW_EXACT_DIRECTORY` publishes exactly `bin/baton`, not
  `bin/baton-work`.
- Deploy JSON names the exact `bin/baton` executable and its `init` next step.
- Shipped/current operator documentation, setup text, examples, W92 runbook,
  and recreation-script instructions invoke `bin/baton`.
- Current artifact, packaging-isolation, init/activate, and end-to-end tests
  execute the renamed installed file.
- Frozen historical reviews, immutable deployed trials, and quoted evidence
  are not rewritten merely to erase the old name.
- `tools/deploy_work.py`, `src/baton_work`, and Python imports may retain their
  internal names.
- W2 leaves the W92 recreation set; every stated surviving-Work count and the
  idempotent scratch-recreation proof is updated accordingly.
- The complete v11 gate passes and v10 remains untouched.

