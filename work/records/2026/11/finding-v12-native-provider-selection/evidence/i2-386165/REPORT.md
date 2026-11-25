# W385830 I2 candidate — independent review

2026-11-25 UTC, baton.codxpc. Successful claim E386173 after routing/ownership
M386168–M386172. Incoming canonical discussion read through M386172; own progress
M386174/M386175. Base **2d9a1f5afd84bfdcef461798d2418be3e6d65a9d** contains both
required I1 and D1/D2 checkpoints. The earlier ownership-pending preflight is
historical; its source copy and baseline were reused, not repeated.

## Candidate and ownership

**sha256:87c3ba728e7fe75e649816a3bc44ae0bb6ff7bc6b3b915a84e70bbb495aa1627**, **22 paths**. `candidate.tar`,
`candidate-manifest.json` and `candidate.patch` retain exact reviewable bytes,
baseline hashes, member hashes and target-drift checks. All shared target bytes
still match baseline. Implementation is in the isolated independent repository
`work/scratch/i2-386165/source`; no product import or protected Git mutation.
The archive excludes DESIGN and all five W386057 isolation prerequisite paths.
The five prerequisites were used unchanged, retained separately and hashed in
the manifest. K/owner retains shared import/checkpoint ownership.

## Delivered behavior

- Production Codex realization from retained 0.169.0 evidence: HOME
  `/run/baton/provider-home`, CODEX_HOME `$HOME/codex`, `codex/auth.json`, managed
  `instructions/WORKER.md`. Closed environment, explicit instruction label,
  fresh implementation role, exact-build probe and R1 guards remain. No ambient
  configuration, source discovery or execution activation is added.
- Host first-initialization automatically resolves the configured source once.
  Explicit file-slot delivery uses exact bytes; the source resolver, volatile
  delivery/adoption, home seed/retained validation and qualification launcher
  enforce the same inclusive 1,048,576-byte bound. Empty files refuse. Legacy
  token handling/limits and Claude remain unchanged. Byte secrets enter the
  reference-counted durable-secret guard before file writes and leave only on
  confirmed cleanup. Tests use synthetic data only.
- D1 explicit `recover_failed_initialization` API: exact admitted manager/home/
  holder/path binding, exclusive home lock, durable failed-preparation proof
  with no runtime start and unchanged bounded metadata snapshot. Original receipt
  and withdrawal audit remain outside the mounted home. Concurrent/repeated
  withdrawal returns one audit. Separate retry authorization is required; the
  next initialization creates a new linked receipt. Missing credentials after
  success, changed home, old unsupported receipt, wrong binding or uncertain
  runtime retains the hold. Restart never needs the original source or silently
  reseeds. No conversation resume is implemented.
- Production-mapping simulated Codex implementation reaches independent Claude
  review through real owners. Codex remains labelled configured-model, actual
  participation unknown, contributors empty; Claude retains stronger participation
  evidence. The simulation also checks actual child environment, managed bytes
  and copied synthetic login file. It is not native/provider qualification.

## C5–C8 dispositions

| Follow-up | Disposition and limit |
| --- | --- |
| C5 | Contract refusal in image retention writes a content-free immutable refusal hold, then returns the lifecycle observation. A previously good receipt cannot mask failed contradictory retention, including after reopen. A globally unwritable control journal cannot persist lifecycle either; no promise to bypass broken authority storage. |
| C6 | Late engine resolution appends an immutable supplement bound to the original receipt. Both orders agree before assessment; absence never erases resolution. Frozen assessment/recovery bindings are never silently rewritten or upgraded. |
| C7 | One attempt has one start. Changed StartedAt, including a same-container restart, is conflicting execution evidence and keeps the hold. |
| C8 | Existing engine image-identity normalization accepts Podman bare hexadecimal IDs for exact-container observation and image resolution. Tags/malformed IDs still refuse; no profile-derived digest-kind assumption. |

Claude/legacy attempts acquire no image-receipt hold. All image evidence here is
synthetic engine output at the normal boundary. CLI identity remains
adapter-recorded/host-validated, not independently measured backend identity.

## Focused verification and accounting

Affected groups: **manager-pure, tools-pure, job_manager**. Prepared interpreter,
supported `just --justfile v12/justfile test-one`, external disk-backed fixture
root and unchanged isolation preflight. No new modules/registry changes.
`final-selection.json` names the exact selection. This is explicit ID accounting
around test-one, **not registry-accounted test-group/full-suite verification**.

Final run `final3`: **1240 collected / 1240 executed /
1237 passed / 3 failing IDs**, 54.263172s, exit1.
No skips, duplicates, unaccounted/uncollected IDs, source drift or timeout.
**The run is not green.** All three failures and all five failure blocks exactly
match the retained pre-change baseline (`baseline-comparison.json`):

1. `tests.manager.test_secrets.EveryDurableWriterIsGuarded.test_every_durable_writer_is_covered`: six existing uncovered review_cycles writer/table pairs.
2. `tests.manager.test_secrets.EveryDurableWriterIsGuarded.test_no_declared_coverage_is_stale`: three stale freeze_checkpoint table declarations.
3. `tests.manager.test_secrets.EveryPublicSurfaceIsAccountedFor.test_every_exported_callable_is_in_exactly_one_class`: existing unclassified `retained_output_of`.

These are reported, not waived or removed. No additional failure remains.
The correction selection passed18/18 before final joined verification. Boundary
checks include below/at/above file limit, multibyte/invalid UTF-8/whitespace exact
bytes, empty and oversized retained files, secret-free refusals, legacy token
limits, failed initialization/no automatic retry, real owner start fencing,
concurrent withdrawal, separate retry/new receipt, foreign binding, unchanged
home verification, refreshed-source independence, production role/home pipeline,
image supplement/reopen/tamper and frozen-binding refusal.

All 10 retained runs (baseline included) total **245.215088s** measured
wall time (`verification-account.json`). Intermediate implementation/fixture
mistakes are retained in their logs and corrected; the stale no-realization
expectations were replaced by approved mapping plus unknown-provider/role guards.
All raw logs, collected-ID lists, JSON outcomes, headers and before/after source
identities remain together. Fixture root was empty and removed; source and durable
candidate/evidence retained. `git diff --check` passed. No protected metadata
cleanup, build, container, real credential read or provider call occurred.

## Review and remaining finite route

Next milestone: **K independent exact-byte I2 review**, routine corrections
returned directly to the implementer; then owner import/checkpoint. Suggested
commit: `Realize Codex homes and audited subscription credential lifecycle`.
No unresolved owner decision blocks this source candidate.

Native-readiness plan remains `../native-readiness-386143/PLAN.md`: Q1 selected
coherent-image build/offline engine/mount/tool qualification; Q2 selected editing
turn capture; I3 only evidence-backed editing event support if needed; Q3 final
image qualification; Q4 explicitly selected Codex implementation → qualified
Claude review and retained verdict. Existing detached login/instruction evidence
is reused, not relabelled native. The recipe pins0.169.0 and includes Git/Python;
actual built tool availability, entrypoint/source/UID bindings and engine receipt
capture still require Q1. Explicit Claude model/source/qualification and execution
limits remain at the selected live boundary. Refresh/shared-login service safety
is unqualified; keep its finite separate criterion. Fast, resume, W386048 and
W386057 remain separate/unselected. No native activation is enabled by this report.

Handoff: M386176, pass E386177 to baton.bug. Canonical snapshot386177 confirms
queued, gate null and Handler null. Claim released.
