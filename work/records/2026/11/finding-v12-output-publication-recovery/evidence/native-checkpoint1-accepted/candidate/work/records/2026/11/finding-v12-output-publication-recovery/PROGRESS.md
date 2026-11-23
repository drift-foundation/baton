# Progress

Allocated for preparation; no implementation started.

## Checkpoint 1 delivered — W385695, 2026-11-23

Internal checkpoint 1 of CONTRACT-PROPOSED-385720.md section 8 is implemented
on 580b85a8: trust-root inspection, the exact owner decision and the CLOSED
admission boundary. Nothing of checkpoints 2 or 3 is implemented, claimed or
stubbed.

Delivered: installed `baton-v12-stack manager publication-inspect` and
`manager publication-decide` (`v12/python/tools/publication_decision.py`,
dispatched from `tools/job_manager.py`); the owner module
`baton_v12.job_manager.publication_recovery`; the two owner-port adapters in
`v12/python/tools/publication_ports.py`; the trust-root read
`workspaces.retained_output_of`; and `documents.publication_gate`.

Trust root. The original output is resolved FROM the Job/stage/episode through
the workspace owner, under `settlement_preparation` (completed preparation and
settled allocation/removal/cleanup/adoption/maintenance/custody writers), the
`device:inode` the preparation finished over, and no-follow measurement. There
is no path operand anywhere on the surface; a dossier copy cannot become the
trust root. Missing, replaced, unreadable, envelope-present, under-ceiling and
over-ceiling originals all HOLD, with the exact selector and operation named.

Producer attribution. The adapter's `result.json` is qualified against the
read-only admitted task (argv, task identity, declared base), the observed exit
0, the declared ending and the provider's own account; it is recorded as
`qualification: producer-evidence` with `independent_acceptance: false` and the
reviewer's independent verification, investigation and tests reported as still
owed under 3600 s per invocation and 900 s per command. Candidate, base and
path-set correspondence comes from the source-aware owner, which composes
`integration.git_profile`'s own vectors in a private bare repository created
and removed per read.

Admission boundary. An approval composes the real owner ports, re-establishes
the trust root, holds it to what the decision bound, reuses the original OPEN
Work, and then returns an explicit HELD PREREQUISITE naming all five missing
capabilities — the `/4` publication stage vocabulary, the `worker-pool/2`
publication lane, Job store generation 10, the deterministic publication worker
and the enforced control profile — each read from the owner that would hold it.
No Job identity is reserved, no Work binding is published, no submission is
recorded and no offer is issued; `execution_gate` reports a closed,
non-runnable gate. Checkpoint 1 is partial evidence and is NOT "resume
supported".

Owner selections held and proved at import: `output-publication-review/1` at
9960/4800/900/3600/900 with zero corrections, retries and continuations, a
16384-byte one-regular-file no-link provenance output, and W385694's exact
104857600-byte proposal declaration read from `role_contract` rather than
restated.

Focused acceptance: `tests.job_manager.test_publication_recovery_admission`
(66 cases) with the existing `test_retained_recovery_admission` and
`test_role_contract` regressions; 217 tests, zero failures, zero errors, zero
skips. No live provider, no engine, no container, no existing-instance
migration and no Git mainline operation.
