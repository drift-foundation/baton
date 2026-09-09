# Approved allocation: open committed evidence without writes

## Current amendment — owner M128249 and M128251, 2026-09-09

This explicitly supersedes owner126833's blanket prohibition on persistent
store/journal artifacts **only for SQLite-managed WAL/SHM coordination sidecar
creation and maintenance during mode=ro opening, including refused opens**.
The historical allocation below is retained; this amendment controls wherever
its sidecar rule or additive-only test rule conflicts with that history.

Preserve database contents and committed evidence, coherent committed reads,
identity/schema validation, mutation refusal and unchanged serving behavior.
No database creation, schema changes, checkpoint, application sidecar cleanup,
permission change or write-capable fallback. No broader mechanism or new Job.

Keep the same five source/test paths. In tests/authority/test_store.py and
tests/integration/test_coordinator.py, relative to v12/python, the owner now
authorizes changing **only sidecar-effect expectations**, preserving all other
assertions. Additive tests remain allowed. Each child PLAN schedules its exact
bounded conversion. Independent review remains required; reconcile and carry
all prior verification usage within20s per provider without resetting budgets.
W122060 stays gated on both independent acceptances and retains11.123699s for
its later consumer join.

## Original allocation and proposal history

Owner M126833 approved the exact five-path, two-provider allocation below,
including additive tests and cumulative20s per provider. This supersedes the
proposal's pending-authority status; its original rationale is retained below.
W126880 binds findings/finding-readonly-authority-open; W126887 binds
findings/finding-readonly-coordinator-open. Each PLAN pins its public API and
exact path set, baton.impl returning baton.bug. Ordinary consumer claim126807
is independently verified by review-2026-09-09T09-54-24Z.md; its remaining
implementation verification budget is now11.123699s. Both providers gate final
read-only acceptance only. No broader allocation or new planning Job.

Reviewer proposal, claim126771; not new source authority. Diagnosis and public
evidence are in `evidence/consumer-126729/FINDING.md`, independently assessed in
`review-2026-09-09T09-31-41Z.md`. Owner126545's consumer and observation contract
stay unchanged. No private constructor/raw-SQL workaround is proposed.

## Requested decision and exact paths

Approve these two small implementation providers through baton.impl, returning
baton.bug for independent acceptance, including the additive tests below. Create
each Work and its dossier together after approval. They may be scheduled
serially by the implementer; neither owns the other's files.

| Provider | Proposed dossier beneath this record | Exact paths relative to v12/python |
| --- | --- | --- |
| Authority read-only opening | findings/finding-readonly-authority-open | src/baton_v12/authority/api.py; src/baton_v12/authority/store.py; tests/authority/test_store.py |
| Coordinator read-only opening | findings/finding-readonly-coordinator-open | src/baton_v12/integration/store.py; tests/integration/test_coordinator.py |

The existing W122060 consumer continues its ordinary serving path on its two
approved paths while this decision/provider work proceeds. These new providers
gate final read-only consumer acceptance, not the already-authorized ordinary
demonstration. Independent acceptance of both permits the consumer's status
factory to use them; it does not itself prove that factory or the lifecycle.

## Bounded API contract

Recommended public entry points are `Authority.open_readonly(path,
expected_authority_uuid=...)` and `IntegrationStore.open_readonly(path,
incarnation=..., clock=...)`, keeping the current owner object/readers and
disposal pattern. Pin the exact spelling/operands in each implementation dossier
before edits; an equivalent within-scope public opener is permitted, but a
consumer must not reach through private owner state. The coordinator remains
target-keyed and does not acquire an invented Authority identity.

Open only an existing recognized store, through a connection that cannot write.
Validate identity/schema against the same connection being returned, under a
coherent read snapshot, reusing each owner's current checks. Authority must
honor expected UUID; both must refuse missing/empty/foreign/incompatible stores
without creating or repairing them. Preserve applicable existing path-type and
non-adoption rules. Do not initialize schema, migrate, request a write lock,
change persistent journal mode, checkpoint, or change file permissions.

The public receipt/operation-result and coordinator entry/lease/history readers
must remain usable. The new handle must not allow a successful mutation through
its normal public API. Attempted mutations fail through the owner's established
refusal boundary before any write or external effect. Keep ordinary serving
open/create and accepted transactions unchanged; no new schema/version, runtime
session, package re-export or broader API redesign.

Read current committed data, including committed WAL data, coherently with
concurrent serving activity. Do not use an immutable-file assumption on a live
store, copy only its main database, or ignore journals to make permissions pass.
The new opener creates no persistent store/journal artifacts. If the SQLite/
filesystem combination cannot supply a safe non-writing view, refuse visibly
and preserve existing files rather than falling back to a write-capable open.
State any platform/WAL-sidecar access limitation precisely; a readable main file
alone does not prove the whole store is accessible.

## Focused acceptance

Add tests within the exact allocated files for normal readable committed
evidence, matching/mismatching Authority UUID, absent path without creation,
empty/foreign/incompatible files left unchanged, mutation refusal, existing
read-only files/directories where supported, and concurrent/WAL committed-read
visibility without modifying store contents/journal mode. Reuse existing
public creation and read helpers; preserve all existing assertions. No existing
test weakening/removal or unrelated fixture conversion is requested.

Declare a focused verification question and enforce cumulative20s per provider,
including iterative tests/probes; preserve every command, result and elapsed
time. Retain claim-start/final bytes and modes. Do not rerun unrelated accepted
provider suites. Any needed path or capability beyond this exact allocation is
reported before editing it.

After independent acceptance, W122060 integrates the public openers in its
already allocated stage_execution.py/test_stage_execution.py pair, using the
remaining19.535586s of its consumer budget, reduced by intervening ordinary
runs. Preserve exact committed integration/exclusion/terminal pass evidence and
read-only observations, then the existing committed-handoff reconstruction cut.
W119114 reuses those results for final custody proof. No new planning Job.
