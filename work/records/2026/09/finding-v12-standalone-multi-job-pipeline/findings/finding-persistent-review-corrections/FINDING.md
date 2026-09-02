# Persist v12 review checkpoints and correction lines

Ledger Work: W71918

Parent: `work/records/2026/09/finding-v12-standalone-multi-job-pipeline/`

Decision source: W62098.

## Confirmed scope

Keep one manager-custodied private development line for a Work across serial
implementation and independent-review assignments. Workers and reviewers are
disposable; the private workspace is not. Every review handoff freezes an
immutable, read-only checkpoint and binds the reviewer verdict and logs to that
exact checkpoint. A changes-requested verdict returns the same line at the
reviewed checkpoint to a writable implementer assignment, with exactly one
writer.

The correction path does not restage from the canonical repository, clone or
copy the candidate again, overlay an uncommitted retained tree, or require an
intermediate canonical commit. Only a final independently accepted checkpoint
becomes eligible for the integration queue.

This leaf owns review/correction stage composition and checkpoint custody. It
uses W71917's workspace/mount contract and W71875's persisted stage state. It
does not own pool selection or integration policy.

## Observed baseline — 2026-09-02

- Worker Manager output freeze and custody can retain an immutable result, and
  v12 authority can record a review receipt.
- The supervised dogfood path tears down a single implementation attempt and
  returns to v11 for review; no persistent manager stage reconnects a rejected
  checkpoint to the same private Work line.
- W62098 run2 proved why copied retained candidates and immediate deltas are
  insufficient, then superseded them with ordinary Git ancestry and a
  persistent private-line ruling.

## Acceptance

- The manager creates or adopts one durable development-line identity per
  Work and permits exactly one writable assignment to attach at a time.
- Review handoff freezes an immutable checkpoint without copying the whole
  candidate tree merely to change roles; the review container receives it
  read-only and writes findings/logs separately.
- The reviewer is independent from the producing runtime and its verdict binds
  Work, assignment generation, checkpoint digest/revision, base/head, and the
  actual reviewed path set.
- Changes requested returns the same private line at that checkpoint to an
  implementer. A later checkpoint remains distinct and the earlier one stays
  resolvable for audit.
- Ten synthetic correction rounds run with fresh disposable containers and no
  second source clone, candidate-tree restage/copy, concurrent writer, or
  canonical target mutation.
- Restart at implementation-to-review and review-to-correction boundaries
  resumes the owed stage idempotently and preserves every checkpoint/verdict.
- Only the final accepted checkpoint becomes integration-eligible;
  intermediate/rejected checkpoints cannot enter the integration queue.

## Test-change authority

This Work authorizes adding tests and editing existing tests under
`v12/python/tests/` for development-line custody, checkpoint freeze/attachment,
review verdict binding, changes-requested reuse, one-writer enforcement,
restart, and integration eligibility. Any deletion or weakened expectation
must be explicit and independently reviewed; unrelated tests are excluded.
