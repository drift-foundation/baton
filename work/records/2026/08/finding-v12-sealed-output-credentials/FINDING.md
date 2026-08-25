# Finding: seal OCI output and assignment-scoped credentials

Promoted implementation record for the fourth bounded child of W5. Its ledger
Work is contained by W5; this dossier is top-level under the maximum-depth
promotion rule.
Canonical Work: W6634.

## Confirmed boundary

Implement the worker-side/adapter-side sealed artifact collector and ephemeral
credential delivery that the manager-owned output and section-13 receivers can
consume. Credentials are assignment-scoped, non-persistent, absent from image
layers, argv, labels, logs, durable store and collected output. Output is read
only after quiescence, never overlaps an input or another output, contains only
declared bounded regular files, and is copied into immutable staging before its
manifest/count/bytes/digest observation is emitted.

The manager remains the only authority that accepts an observation, settles an
attempt, applies retention or authorizes cleanup. This component neither
invents manager envelopes nor equates engine status with sealed output.

## Acceptance

- Missing, undeclared, linked, special, changing, over-count and over-byte
  outputs refuse without an accepted partial artifact.
- Freeze/copy/hash is ordered after quiescence and detects replacement races.
- Credential injection and teardown leave no value in diagnostic/durable or
  artifact surfaces, including failure and cancellation paths.
- Restart/retry is idempotent by manager operation/artifact identity.
- Handoff uses only the separately owned manager output/security contracts.

The implementer creates and exclusively owns `PROGRESS.md` when claimed.
