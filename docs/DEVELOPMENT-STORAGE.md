# Development files and recovery

Development must be recoverable on another computer. An untracked file, a
local commit without a separate copy, or a persistent local directory alone
does not establish that recovery is possible.

| Class | Examples | Where it belongs |
| --- | --- | --- |
| Preserve | Source, tests, fixtures, dependency locks, instructions, decisions, handoffs, required acceptance evidence | Tracked repository paths, committed by the owner and copied to the repository's durable remote or backup |
| Disposable | Rebuildable packages, caches, virtual environments, scratch runs and intermediate outputs | Explicitly ignored paths; use disk-backed `work/scratch/` for development scratch |

Use `/tmp` only for short-lived temporary files, such as compiler side effects.
On this host it consumes memory and does not survive reboot. Do not put
continuation checkpoints, sole copies of evidence, or substantial scratch runs
there. Persistent scratch may also be deleted: promote necessary results to
the owning dossier before relying on them in a handoff.

For required artifacts unsuitable for Git, keep a checked-in manifest with
their durable storage locator, content digest, purpose and retrieval steps.
Verify retrieval before relying on that copy. Credentials belong in an
appropriate secret store, with setup instructions in the repository.

`work/records/` contains permanent dossiers. Generated-looking files there can
be immutable review candidates, acceptance evidence or executable test inputs.
Do not blanket-ignore databases, archives, logs or whole dossier directories.
Assess their references and recovery value before deciding their disposition;
preserve uncertain files. Existing tracked evidence is not disposable merely
because a similar artifact could be generated again.

Before a checkpoint, identify all changed and untracked source and test inputs,
including inputs loaded from dossiers. Include the required inputs and their
recovery instructions together. Label unfinished work honestly. Slawomir owns
staging, commits and transfers through Git; agents prepare and verify changes.
A clean status alone does not prove recoverability, since ignored files can
still contain accidental dependencies.

Cleanup must name specific disposable paths and their regeneration procedure.
Do not use bulk deletion or new ignore patterns to hide unclassified work.
Keep live coordination state outside the product repository and recover it
through its supported backup procedures; repository records do not replace
the authoritative Baton ledger.
