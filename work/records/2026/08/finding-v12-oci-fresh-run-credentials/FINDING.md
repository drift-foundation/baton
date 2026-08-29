# OCI fresh-run credential delivery provider

Date: 2026-08-27
Parent discovery: W6636, `work/records/2026/08/finding-v12-local-oci-lifecycle-composition/`
Upstream implementation history: W6634, `work/records/2026/08/finding-v12-sealed-output-credentials/`

## Finding

**Confirmed:** W6636's diagnostic lifecycle review found that W6634's shared output/credential implementation remains provisional and cannot be used as the certification boundary for local OCI lifecycle composition. The W6636 approver ruling authorizes a separate provider Work for fresh-run credential delivery.

**Confirmed:** Assignment logical credential slots resolve through a trusted profile provider to opaque references. Bearer bytes must be registered as live before any materialization, written as mode-0600 files beneath an assignment-private mode-0700 volatile root, and mounted read-only at the fixed worker path `/run/baton/credentials`.

**Confirmed:** Bearer bytes must never appear in argv, environment, labels, durable records, diagnostics, or worker output. The live-secret registry remains armed through worker quiescence, output scanning, container removal, and credential-root deletion, and it forgets a bearer only after positive absence is established.

**Confirmed boundary:** This Work owns fresh-run delivery only. Output custody, the shared quiescence/removal/settlement crossing, restart adoption, recovery, reconciliation, and orphan convergence remain outside it and are owned by W6636 or its other providers.

**Proposed implementation boundary:** Revalidate the W6634 spike against the current manager and adapter contracts, then adopt only the portions that meet this finding. Provisional code is evidence, not accepted implementation.

## Acceptance

- Logical slots resolve without placing bearer material in assignment or runtime metadata.
- Fresh-run credential files and roots have the required permissions and fixed read-only mount semantics.
- Failure at every materialization/start boundary preserves live-secret tracking and converges to positive absence before forgetting.
- Tests prove secrets are absent from argv, environment, labels, durable documents, diagnostics, and output.
- Focused unit, mutation, failure-injection, and real-engine tests cover delivery and cleanup.

## Open

- Exact provider interface and volatile-root owner must be revalidated against the current v12 manager tree before implementation.

## 2026-08-27 — independent review

**Confirmed P1:** Failed materialization calls `_discard(root)` but ignores its
boolean absence proof, then forgets every bearer unconditionally. If removal
fails, bearer bytes remain in the volatile root while the live-secret registry
is disarmed. `evidence/w26284-review-reproductions.py` forces `_discard` to
answer false and observes `root_present=True bearer_live=False`.

**Confirmed P1:** `OciAdapter.start` asks the engine for duplicate candidates
before `run_vector` applies the live-secret sweep. The candidate selector puts
`runtime_attempt_id` into the engine argv. When a provider-supplied live bearer
equals that attempt identity, both preflight `ps` calls receive the bearer
before the later sweep refuses the run vector. The same reviewer reproduction
observes two engine calls and the bearer in both.

**Confirmed review gap:** The real-engine teardown case starts a container and
then invokes `CredentialHome.tear_down` directly, without first establishing
container removal or positive absence through the adapter. It therefore does
not prove the lifecycle ordering this finding requires; the shared
quiescence/removal/settlement crossing remains explicitly outside this
provider.

## 2026-08-28 — the reviewed P1s, corrected

**Confirmed corrected — an unprovable cleanup keeps the registry armed.**
`_discard` exists to answer whether the root is GONE, and the failed-
materialization handler threw that answer away and forgot every bearer
regardless. A filesystem that refused the removal therefore left the bearer
bytes readable while the registry guarding every later §13 scan was disarmed.
The handler now branches on the proof: a proved removal forgets and re-raises
the original failure; an unproved one keeps every bearer REGISTERED and
surfaces its own `policy/credential-lifetime` ending, because what an operator
must act on is a stranded bearer rather than the provider that was down a
moment ago.

**Confirmed decision — the §13 argv sweep has ONE owner, and it is the engine
port.** The sweep lived in `run_vector` and covered only the vector that
function composed, so `start`'s duplicate probe — which puts
`runtime_attempt_id` into a `--filter` argument, and runs before any vector is
composed — reached the engine first and unswept. A provider answer is
explicitly untrusted, so a bearer equal to the attempt identity was handed to
the daemon by the very call meant to run before anything happened.

The rule is about INVOCATION rather than composition: every process on the
host can read another's command line. So it moved to `EnginePort.__call__`,
which is what every vector actually passes through — the listing, the inspect,
the stop, the destroy, the run, and whatever is added next. Adding it beside
`run_vector`'s would have been four more copies of one rule and a fifth
waiting for the next vector somebody writes.

**Confirmed scope, on the real-engine cleanup case.** The review offered two
resolutions and this finding's own boundary chooses: the shared
quiescence/removal/settlement crossing is explicitly outside this provider, so
the engine suite stays inside fresh-run delivery and failure. The teardown case
no longer starts a container it cannot prove absent; it tears down a delivery
that never launched, which is a real ending this provider owns. The one
runtime-absence question this provider does own — a start the engine refused
settling through the adapter's real listing before the delivery is released —
is now covered against a real daemon. The post-runtime crossing remains W6636's.

**Why nineteen caught mutations were not sufficient, which is worth pinning.**
Both failed-materialization mutations watched a SUCCESSFUL removal, and the
argv mutation removed the sweep from the one vector that had it. A measurement
can be complete against the rules it chose to break and still miss the rule
nobody wrote down — here, that `_discard`'s answer is the guard and not its
call. The corrected harness drives the false answer and removes the sweep at
its single owner.
