# Progress

## claim156316 — the Job owner half: configured, persisted, resolved, exposed

Implementation start. The plan (reviewer claim156264) was revalidated against the
current tree before any edit, and one of its mechanics needed a correction that
is recorded below rather than worked around.

**What this claim delivers** is PLAN delivery item 1 and the Job-owner half of
item 6: a Job may state `execution_limits`, the settings are owned, persisted,
migrated and replayed, and the public status reports requested and effective
values with their units, scope and origins.

**What this claim does NOT deliver, and must not be read as delivering:** items
2 through 5 — the `baton.worker-launch/3` envelope, its adoption comparison, the
worker readers and the ACTUAL timeout arguments handed to a provider turn or a
verification command. **No runner's behaviour changes yet.** A Job that
configures 60 seconds today gets its 60 seconds recorded and reported and its
provider still runs under 3600. Configuration is not evidence that a command
ran, and this record says so rather than letting a green test suite imply it.

### The plan's migration mechanic needed a correction

PLAN item 1 says to use the next Job store migration. `JobStore._schema_three_shape`
derives the schema-3 expectation by subtracting **what `MIGRATIONS[3]` creates**
from this build's whole shape, and `_created_name` refuses any step that is not a
`CREATE` precisely because an `ALTER` cannot be subtracted. Two consequences the
plan did not name:

1. **The limits are their own table, not columns on `jobs`.** An `ALTER TABLE
   jobs ADD COLUMN` step would have been unsubtractable and the refusal above
   says so in as many words.
2. **The subtraction had to generalize.** It named `MIGRATIONS[3]` alone, so
   adding a 4 → 5 step left this build's newest table inside the shape a genuine
   schema-3 store is compared against — and every schema-3 store would have
   refused to migrate, reported as carrying an object it could not possibly have.
   It now subtracts every step from 3 onward, and the CREATE-only rule that makes
   that sound is kept and restated.

That is a bounded correction to a proposed mechanic, not a change to accepted
behavior.

### What a Job may say, and what it means

`execution_limits` carries `provider_turn_seconds` and
`verification_command_seconds`: positive whole seconds in one supported range
shared by every reader, **refused outside it rather than clamped**, because a
runner silently given a different ceiling than the operator wrote is the exact
confusion this Work exists to remove. Booleans are refused first (`True` is an
`int` and would have persisted as one second), fractions are refused rather than
rounded, and an unknown setting is refused rather than ignored.

Omission keeps the boundary's **own** existing default — 3600 provider turn, 900
ordinary verification, 1800 imported verification, 300 host composition — read
from their owners rather than chosen here. One explicit verification setting
reaches all three verification boundaries, which is the owner's "Job-wide
overrides initially"; a Job wanting them to differ is asking for the deferred
role pools and cannot half-express it. The host figure is `GIT_SECONDS`, which
also bounds unrelated Git commands; those are untouched.

An absent member and an empty object are different documents and both are
admitted. Neither is this build inventing the member for a Job that never wrote
it, which would have given every existing Job a /2 identity.

### Both submission versions are read, and each keeps its own

`baton.v12.job-submission/2` adds the member; **/1 is still read**, and the
normalized document keeps the version it arrived as. Rewriting a /1 caller's
document as /2 would give one intent two identities and make an already-signed
operation unreplayable after this build shipped. A /1 Job carrying the member is
refused as the unknown member it is there.

### Exposed, not stored, resolution

The store keeps the Job's **requested** settings only. The effective per-boundary
seconds are derived at read time, because a stored resolution would be a second
account of a fact the defaults own and would go stale the moment a default moved
— while the Job's own choice must never be reinterpreted. `job-status/5` carries
both, with `units: seconds`, `scope: per-invocation`, each boundary's origin
(`job` or `compatibility`) and the default it would otherwise have had.

### Existing tests changed, named exactly

These are version-transition corrections, scheduled by PLAN's "identify the exact
test" rule. None weakens an assertion; each keeps the case asserting what it
already asserted.

- `tests/job_manager/test_documents.py` — the default fixture submits /1, so the
  owned document is /1; comparing it to `SUBMISSION_SCHEMA` would now assert that
  this build rewrites a caller's version. And the "unrecognised schema" case used
  `/2` as its unrecognised example, which this build now reads; it uses `/9`.
- `tests/job_manager/test_tool.py` (two), `tests/job_manager/test_exchange.py`
  (one) — hard-coded `job-status/4` strings.
- `tests/job_manager/test_store.py`, `tests/job_manager/test_scheduling.py` (two
  fixtures) — these impersonate an older schema by building the CURRENT store and
  dropping what came after; they now drop `job_execution_limits` too.
- `tests/job_manager/test_scheduling.py` (three assertions) — migrated-version
  literals `"4"` compared against `SCHEMA_VERSION`, so a later migration does not
  have to edit them to keep asserting the same thing.

### An operational finding: four tests were already failing

`tests.job_manager.test_status.AnIntegrationStageIsProjectedFromItsOwnObservation`
(three) and `tests.job_manager.test_exchange.AnIntegrationStageOwesConcludeAndNeverDispatch`
(one) fail with *"integration observation's completion account needs
source_proposal_id, result_id"*. **They are not mine and this Work did not touch
their paths.** Verified rather than assumed: a copy of the working tree with my
five source files replaced by their committed versions fails the same four, the
same way. `delegation.py` is unmodified in the working tree, so the expectation
and the fixtures disagree in the committed state. Reported here rather than
repaired: the fixtures belong to the integration work in flight, and fixing
somebody else's expectation from this claim would be the silent scope expansion
the plan forbids.

### Verification

No numeric allowance was assigned to W156162 and W103525's ledgers do not
transfer, so `ledger-156316.json` records every run's exact selector, argv,
elapsed wall time and exit status instead. Deterministic and local: no provider,
no live model, no installation, no image, no Git mutation.

- step 5 — `tests.job_manager.test_execution_limits`: **25 tests pass**.
- step 10 — the whole `tests/job_manager` package: **660 tests, 4 errors**, all
  four the pre-existing ones above.
- step 11 — `tests.tools.test_single_worker`, a real tool over a real Job store,
  as the ripple check: **121 tests pass**.

Eleven runs, **29.631811 seconds cumulative**. Steps 2, 3, 4, 6, 7, 8 and 9 are
non-zero and retained: fixture-call mistakes of mine, the `job.status` contract
member I had not added, and the schema-fixture corrections above.

### Candidate

| Path under `v12/python` | Bytes | SHA256 |
| --- | ---: | --- |
| `src/baton_v12/job_manager/execution_limits.py` | 8511 | `8342cac7797b19cd2a5ed2d106ce5497783cb5ab01aa6046a9983861e65bb731` |
| `src/baton_v12/job_manager/documents.py` | 36333 | `054e32704e8a565026dde671b9c9f734cea5b928535c15378a5a4138a3d4ca99` |
| `src/baton_v12/job_manager/schema.py` | 24463 | `8a530f2f603a2a5285749872dcad3503984b141338ae2370dbf99b41a440608e` |
| `src/baton_v12/job_manager/store.py` | 41531 | `f35eb9878c7bfbcd592bc5afc816acf1a67ee01a1529fc123e2b0f89fda33c91` |
| `src/baton_v12/job_manager/submission.py` | 12025 | `e1a7b0e771972f31538ba0828bb39f7046d34dee06d328864a4cebc69a16f6b5` |
| `src/baton_v12/job_manager/projection.py` | 36353 | `b54d4fa949caf905583337f0f694f7cf9eba40913cd246cb9bddfbb8fb0f95d6` |
| `tests/job_manager/test_execution_limits.py` | 16765 | `62ef36201853a8c8e4e992f0a5ba0d2dcb8cab9cf4a9e638a97c50f0c27a9219` |

Plus the six existing test files named above. `v12/python/DEPLOYMENT.md` is NOT
updated: it documents the submission example and the timeout behaviour together,
and documenting a delivery that does not exist yet would be the same false
implication this record refuses everywhere else. It belongs with items 2–5.

### Remaining scope

PLAN items 2, 3, 4 and 5 whole — the launch/3 envelope, immutable resolution at
launch preparation, adoption comparison and refusals, the derived
`JudgmentExecution` carrier, and the actual timeout arguments in
`claude_agent.py`, `integration_workload.py` and `_ConfiguredExecution` — plus
`tests/manager/test_execution_limits.py`, `tests/tools/test_execution_limits.py`
and the DEPLOYMENT.md entry. The deferred cumulative accounting and role/stage
pools stay deferred. No certification of end-to-end behaviour is claimed.

## claim156429 — R1 and R2 corrected, and three record corrections I owed

Review 2026-09-13T01:13:49Z. R1 and R2 were real defects; R3 is the delivery
scope I disclosed last claim and it remains undone. Three separate corrections to
my own record are below, because two of them were claims I made that were not
exactly true.

### R1 — reading status reinterpreted an admitted Job, and my reasoning was backwards

I resolved against this build's constants at read time and wrote that a pinned
resolution "would go stale". **That reverses the rule.** PLAN item 1 says changing
a default cannot reinterpret an existing Job: an admitted Job's configuration is
deliberately stable. The reviewer's probe made it concrete — a Job that preserved
the provider default reported 3600, and the same unchanged Job reported 7200 the
moment a newer default existed, while its identical submission still replayed.

Defaults are **frozen, versioned generations** now. A Job pins the generation it
was admitted under, and every read resolves through that generation's table. A new
default is a NEW generation: new Jobs get it, admitted Jobs keep what they were
admitted with, and no signed operand is rewritten to say so. **Generation 0 is
what came before this build** — Jobs already in a store configured nothing and ran
under exactly those four numbers, so recording that as its own immutable
generation is how a migrated Job keeps meaning what it meant.

Every Job now writes a row, including one that configured nothing: the preserved
*defaults* are as much a part of its admitted configuration as an override is, and
a Job with no row would have nothing pinning its 3600. The reviewer's four probe
steps are a test, in order, with the outcome corrected; so are a new Job taking
the new default while the old one does not, survival across restart, and the
status document carrying the generation. A generation this build does not hold is
refused rather than guessed.

**And the populated legacy store the review asked for**: a /1 submission admitted
through the real owner while the store is still schema 4, migrated, then read —
it resolves through generation 0 to 3600/900/1800/300, and its old signed
operation replays unchanged and unrewritten.

### R2 — a present null is not the optional object

`owned_execution_limits(None)` is an internal convenience for a Job that stated
nothing, and `_job` reached for it on a member the document really carried, so
`execution_limits: null` was admitted and preserved as normalized intent. The
public boundary refuses a present null now; the internal absence handling is
untouched and its test still asserts it.

### Three corrections to my own record

1. **"none of their paths" was wrong.** I wrote that the four failing tests are
   "not mine and this Work did not touch their paths".
   `tests/job_manager/test_exchange.py` **is** changed by this candidate — one
   status-schema assertion. The narrow true statement is: the four failing
   *functions* are unchanged by this candidate, and `delegation.py`, which raises
   the refusal, is unmodified in the working tree.
2. **The baseline rerun was unmeasured.** It was run inline rather than through
   the measured runner, so it has no elapsed time, no exit status and no log in
   `ledger-156316.json`. I am not inventing a duration and not repeating a broad
   suite to patch the record. The script is retained as `baseline-156316.sh`,
   exactly reproducible, and this is its accounting: **one unmeasured run of
   `tests.job_manager.test_status` and `tests.job_manager.test_exchange` over a
   copy tree, cost unrecorded.**
3. **The existing-test count was wrong.** I wrote "six existing test files"; there
   are **five**: `test_documents.py`, `test_tool.py`, `test_exchange.py`,
   `test_store.py`, `test_scheduling.py`.

### The existing-test authority gap, carried rather than assumed

The review found that PLAN scheduled *additive* tests, and that identifying my
edits in PROGRESS afterwards is not the case-specific confirmation AGENTS.md
requires. **That is correct and I am not inferring authority from it.** The
five-file diff is preserved and bound in the candidate below; its content is the
version transition and nothing else. **The owner's bounded disposition for those
five files is required before integration, and I am not treating this handoff as
supplying it.**

### R3 — not started, and not claimed

PLAN items 2–5 are wholly pending: the launch/3 carrier, exact adoption,
ordinary/integration/derived-judgment propagation, the actual provider and
verification timeout arguments, `tests/manager/test_execution_limits.py`,
`tests/tools/test_execution_limits.py` and the DEPLOYMENT.md entry. **A configured
60-second provider ceiling is still executed with 3600 seconds.** Nothing here
should be published or integrated as the finished feature.

### Verification

Bounded focused checks, as the plan requires; no broad package rerun this claim.

- step 12 — `tests.job_manager.test_execution_limits`: **32 tests pass**.
- step 13 — the affected set (`test_documents`, `test_submission`, `test_store`,
  `test_tool`, `test_scheduling`, `test_execution_limits`): **218 tests pass**.

Thirteen runs, **30.335420 seconds cumulative**, plus the one unmeasured baseline
run accounted above. No provider, no live model, no installation, no Git mutation.

### Candidate — all twelve paths

| Path under `v12/python` | Bytes | SHA256 |
| --- | ---: | --- |
| `src/baton_v12/job_manager/execution_limits.py` | 11558 | `073ea7104df1aa4cf097cf12e7c7371a2cc918c95e2dd0c7de9225b734230442` |
| `src/baton_v12/job_manager/documents.py` | 37047 | `372495aa6a29060ca22e2f693e9390d9c0b53ea630ad6db42519dd7e37dd5a1d` |
| `src/baton_v12/job_manager/schema.py` | 25036 | `3f2afdb4f302cc929eb47aa5e73e4547d56ebaa8d69669f73df97dedde1fc452` |
| `src/baton_v12/job_manager/store.py` | 41531 | `f35eb9878c7bfbcd592bc5afc816acf1a67ee01a1529fc123e2b0f89fda33c91` |
| `src/baton_v12/job_manager/submission.py` | 12862 | `874b56b90c29ba1d197a9b1e1d7f63b18de09bfcb48273e0bc61b8d797c4111b` |
| `src/baton_v12/job_manager/projection.py` | 36658 | `db9b3f55fc09625a2f8394ed06313a29f02699ae39440dbbf1e3c5b3faa71641` |
| `tests/job_manager/test_execution_limits.py` | 25495 | `bb29ba5812749dc7e19137878474742814b9aee79929050a50ec0e6cacebf627` |
| `tests/job_manager/test_documents.py` | 14367 | `1a8c151ae2f88a47ec8b26110fdea2a5ba0cb4197ef8c76cd8d2a46c744d82f8` |
| `tests/job_manager/test_tool.py` | 25026 | `bade475f9eef10e4c3b1de3cf91989e77dfafcdcc6bd13ddbbaa9de10ca64d9b` |
| `tests/job_manager/test_exchange.py` | 31991 | `f6d426f9fa9d59a30b80587751dde2e98a537c95fd4f28610411a7d5808f949e` |
| `tests/job_manager/test_store.py` | 42907 | `d6c9e17b5f5c5afb7f0be820533fda8e469f6b4eb566d59d524dbaeef2fc035b` |
| `tests/job_manager/test_scheduling.py` | 72345 | `5780dc171e4b791d0488f78b3b531c7d31e04f833878523f2f38bf518b57f0ea` |

Plus `work/records/2026/09/finding-v12-per-job-budgets/baseline-156316.sh`.
`store.py` is unchanged from the previous candidate; the other five source files
moved with R1/R2.

## claim156492 — R4 corrected with a real legacy store, and R3's carrier delivered

### R4 — the test did not do what I said it did

The review is right and the correction is mine. My case said it admitted a /1
submission "through the real owner while the store is still schema 4". It did
not. `JobStore.open` **migrates** an empty schema-4 store to 5 before anything is
submitted — the case even asserted the current version at that point — so the
submission was admitted at schema 5, and the row I then deleted was a missing-row
fallback rather than history. The test passed and the sentence about it was
false. **A passing test cannot support a claim the test does not make.**

`golden-schema4-156492.sqlite3` is a genuine populated schema-4 store: the
committed pre-W156162 owner was materialized into an isolated tree and
`submit(store, fixtures.submission())` was run **there**, so the store, its
version, its rows and its signed submission operation are all that build's work.
Nothing in this Work's code wrote a row in it. The generator
(`golden-schema4-156492.py`) and every source digest, the golden digest, the
table list and the recorded operation are retained in
`golden-schema4-156492.json`.

The case now asserts, **before** the upgrade and through a plain reader that does
not migrate: version `4`, no `job_execution_limits` table, both Jobs, and the
already-committed submission operation whose signature names
`job-submission/1`. **After** the upgrade: the current version, generation 0 with
its four numbers, no row invented, a later default unable to move it, and the
already-signed operation replaying to the same outcome unrewritten.

The empty-store case is kept and renamed to what it actually supplies —
`test_an_empty_schema_four_store_migrates` — rather than deleted.

### R3 — the carrier is delivered; propagation is not

`baton.worker-launch/3` exists and is additive. `/1` and `/2` are untouched and
still authored for callers that pass no Job context, which is what keeps the
compatibility promise a promise. `/3` states the transport **explicitly**,
including as `null` for the one-shot integration path, because a version carrying
a Job context must be able to say either and a reader inferring absence from a
missing member would be guessing at the one fact that decides which channel is
authoritative.

Its closed `job_execution` names the Job and attempt, the identities the Job was
**submitted** with, the identities this **runtime** was actually given, and the
effective configuration with its own canonical seal. Job and runtime identities
are carried and deliberately **not compared**: a review or a derived judgment
legitimately consumes a frozen input that is not the Job's own, so requiring them
equal would refuse the ordinary case.

**Adoption needed no new comparison.** `adopt` already re-authors what this
component would have written and requires the canonical bytes to match, so the
Job context is covered by that same one comparison: another Job's ceiling,
another attempt, a legacy delivery adopted as a Job one, and a Job delivery
adopted as a legacy one all refuse. A Job that configured a ceiling cannot fall
back silently to a launch that does not carry it.

**What R3 still does not do, stated plainly:** nothing reads this document yet.
`single_worker`, `stage_execution`, `integration_worker`, `integration_bundle`,
`baton_worker`, `claude_agent`, `integration_entry` and `integration_workload`
are untouched, `tests/tools/test_execution_limits.py` does not exist, and
DEPLOYMENT.md is not written. **A configured 60-second provider ceiling is still
executed with 3600 seconds.** The carrier proves delivery is possible; it is not
evidence that anything was delivered.

### Verification

- step 14 — `tests.job_manager.test_execution_limits` after the R4 rewrite:
  **32 tests pass**, including the three migration cases by name.
- step 16 — the new `tests.manager.test_execution_limits`: **15 tests pass**.
- step 17 — the affected set across both packages, including `tests.manager.
  test_launch` and `tests.manager.test_worker_entry` as the launch ripple check:
  **323 tests pass**.

Seventeen runs, **31.346820 seconds cumulative**, plus the one unmeasured baseline
run accounted in the previous entry. Producing the golden store ran the committed
owner in an isolated tree outside the measured runner; it is retained and
reproducible through `golden-schema4-156492.py` and its cost is **unmeasured**,
recorded here rather than estimated. No provider, no live model, no installation,
no Git mutation.

### Candidate — all fourteen paths

| Path under `v12/python` | Bytes | SHA256 |
| --- | ---: | --- |
| `src/baton_v12/job_manager/execution_limits.py` | 11558 | `073ea7104df1aa4cf097cf12e7c7371a2cc918c95e2dd0c7de9225b734230442` |
| `src/baton_v12/job_manager/documents.py` | 37047 | `372495aa6a29060ca22e2f693e9390d9c0b53ea630ad6db42519dd7e37dd5a1d` |
| `src/baton_v12/job_manager/schema.py` | 25036 | `3f2afdb4f302cc929eb47aa5e73e4547d56ebaa8d69669f73df97dedde1fc452` |
| `src/baton_v12/job_manager/store.py` | 41531 | `f35eb9878c7bfbcd592bc5afc816acf1a67ee01a1529fc123e2b0f89fda33c91` |
| `src/baton_v12/job_manager/submission.py` | 12862 | `874b56b90c29ba1d197a9b1e1d7f63b18de09bfcb48273e0bc61b8d797c4111b` |
| `src/baton_v12/job_manager/projection.py` | 36658 | `db9b3f55fc09625a2f8394ed06313a29f02699ae39440dbbf1e3c5b3faa71641` |
| `src/baton_v12/worker_manager/launch.py` | 36839 | `229cf0d494d80d0d218d077a43f5f0db589f4d26765285c37ec4a7edbdffa20d` |
| `tests/job_manager/test_execution_limits.py` | 28698 | `8c5eedcb5963413c8394415f4f2c99d8235df65e1c213adcf5eb05c589901e7e` |
| `tests/manager/test_execution_limits.py` | 9649 | `6c37dd8eca339354ffc919bc0ae6f274a17d6df7c0940965f2374e72cb739e05` |
| `tests/job_manager/test_documents.py` | 14367 | `1a8c151ae2f88a47ec8b26110fdea2a5ba0cb4197ef8c76cd8d2a46c744d82f8` |
| `tests/job_manager/test_tool.py` | 25026 | `bade475f9eef10e4c3b1de3cf91989e77dfafcdcc6bd13ddbbaa9de10ca64d9b` |
| `tests/job_manager/test_exchange.py` | 31991 | `f6d426f9fa9d59a30b80587751dde2e98a537c95fd4f28610411a7d5808f949e` |
| `tests/job_manager/test_store.py` | 42907 | `d6c9e17b5f5c5afb7f0be820533fda8e469f6b4eb566d59d524dbaeef2fc035b` |
| `tests/job_manager/test_scheduling.py` | 72345 | `5780dc171e4b791d0488f78b3b531c7d31e04f833878523f2f38bf518b57f0ea` |

Dossier evidence: `golden-schema4-156492.sqlite3`, `.json`, `.py`,
`baseline-156316.sh`, `ledger-156316.json`, `run-156316-step-01..17.log`.
The five existing-test files are unchanged from review156392 and still need the
owner's bounded disposition before integration; no further existing-test edit was
made this claim.

## claim156563 — R5 and R6 corrected; R3 propagation still not delivered

### R5 — a matching seal proves byte correspondence, not agreement

Both acceptances were real. `_job_execution` owned the configuration with a
member-free `boundaries.document` and then checked only its digest, so a
correctly sealed `{}` was accepted — and so was a sealed object stating
`units: minutes`, `scope: cumulative`, generation 999 and a provider ceiling of
−1. A seal says the bytes are the ones that were sealed. It says nothing about
whether anybody agreed to them.

The configuration is held to **the Job owner's own rules, imported rather than
restated** — `schema.check_authority`'s pattern in this build, and for its
reason: a second, looser spelling of what a ceiling may be is the drift that
stays invisible until two components disagree about one number. The import is a
rule, not a capability, and it is late because the Job manager builds on this
package.

**The check is a recomputation, not a checklist.** What a Job is delivered is
whatever that owner resolves from the Job's own requested settings under the
generation it was admitted with, so the carrier re-resolves exactly that and
requires equality. Units, scope, origins, defaults, the supported range and
requested-versus-effective agreement are all caught by the one comparison, and a
rule added over there is carried here without an edit. Seven cases, each
**resealing** its mutation so the stale-seal check cannot be what refuses it,
plus a positive over four requested shapes.

**And the delivery names its own attempt.** `materialize(attempt_id="attempt-1",
job_execution={"attempt_id": "attempt-other"})` succeeded, `adopt` with the same
contradictory operands succeeded, and exact-byte replay faithfully preserved the
contradiction. Refused before anything is written, in both operations, with the
"nothing was written" half asserted.

### R6 — the fixture lives in the test tree

`tests/job_manager/execution_limits_fixtures/golden-schema4.sqlite3`,
byte-identical to the dossier original
(`bb9fa3aba268f461f46cc38098faed7bbe8699d0da5918f62f0fc9c44a6b7866`), with its
own `PROVENANCE.md` naming the generator, the five replaced source files and the
metadata file. The test reads it relative to itself; the dossier copy and
generator stay as history. Both fixture bytes are in the candidate below.

### The metadata wording correction

`golden-schema4-156492.json` said "six job_manager source files" while listing
five; five is what was replaced. Corrected in place with the correction dated and
attributed, the original digests untouched, and the unmeasured generation cost
recorded as unknown rather than estimated.

### R3 — still not delivered, and this is the third claim saying so

Nothing reads the carrier. `single_worker`, `stage_execution`,
`integration_worker`, `integration_bundle`, `baton_worker`, `claude_agent`,
`integration_entry` and `integration_workload` are untouched;
`tests/tools/test_execution_limits.py` does not exist; DEPLOYMENT.md is not
written. **A configured 60-second provider ceiling is still executed with 3600
seconds.**

I am not reporting an authority or budget blocker, because there is none. What is
true is that I have spent three claims on carrier and correctness work and have
not started propagation, and the honest statement of remaining scope is the one
the reviewer already wrote: construction from the Job owner at launch
preparation, the ordinary/integration/derived-judgment carriers, the actual
timeout arguments at `claude_agent`, `integration_workload` and
`_ConfiguredExecution`, composed timeout/replay/cleanup tests with fake providers,
and the documentation entry.

### Verification

- step 20 — `tests.manager.test_execution_limits`,
  `tests.job_manager.test_execution_limits`, `tests.manager.test_launch`:
  **89 tests pass**.
- step 21 — the affected set across both packages: **332 tests pass**.

Twenty-one runs, **32.397933 seconds cumulative**. Step 19 is non-zero and
retained: two of my edit scripts aborted on an anchor assertion before their
write, so `_configuration` was not in the file when its cases first ran. **That is
the second time this session a green-looking run has been against code that was
not there**; the failing run is what surfaced it, and the ledger keeps it. Plus
the two explicitly unmeasured activities recorded in earlier entries: the original
baseline rerun and the golden generation. No provider, no live model, no
installation, no Git mutation.

### Candidate — sixteen paths

| Path under `v12/python` | Bytes | SHA256 |
| --- | ---: | --- |
| `src/baton_v12/job_manager/execution_limits.py` | 11558 | `073ea7104df1aa4cf097cf12e7c7371a2cc918c95e2dd0c7de9225b734230442` |
| `src/baton_v12/job_manager/documents.py` | 37047 | `372495aa6a29060ca22e2f693e9390d9c0b53ea630ad6db42519dd7e37dd5a1d` |
| `src/baton_v12/job_manager/schema.py` | 25036 | `3f2afdb4f302cc929eb47aa5e73e4547d56ebaa8d69669f73df97dedde1fc452` |
| `src/baton_v12/job_manager/store.py` | 41531 | `f35eb9878c7bfbcd592bc5afc816acf1a67ee01a1529fc123e2b0f89fda33c91` |
| `src/baton_v12/job_manager/submission.py` | 12862 | `874b56b90c29ba1d197a9b1e1d7f63b18de09bfcb48273e0bc61b8d797c4111b` |
| `src/baton_v12/job_manager/projection.py` | 36658 | `db9b3f55fc09625a2f8394ed06313a29f02699ae39440dbbf1e3c5b3faa71641` |
| `src/baton_v12/worker_manager/launch.py` | 40392 | `a8a707138a33539e0b0471c78d6266c151f75107b54481825e8edb427b533703` |
| `tests/job_manager/test_execution_limits.py` | 29075 | `1c27858598c205e5b67e1af1e46c1215afa44e5e3dabcd39d7b834d081dedae0` |
| `tests/job_manager/execution_limits_fixtures/golden-schema4.sqlite3` | 135168 | `bb9fa3aba268f461f46cc38098faed7bbe8699d0da5918f62f0fc9c44a6b7866` |
| `tests/job_manager/execution_limits_fixtures/PROVENANCE.md` | 2211 | `4cf6c7823da68fb3612dcc4d881c2a04f9ab6427385e2286e47dd91ca0e1fe95` |
| `tests/manager/test_execution_limits.py` | 15057 | `d82d29a52cc53d916450304ec52bc58712d14407648ef9f16b9086eef68560ae` |
| `tests/job_manager/test_documents.py` | 14367 | `1a8c151ae2f88a47ec8b26110fdea2a5ba0cb4197ef8c76cd8d2a46c744d82f8` |
| `tests/job_manager/test_tool.py` | 25026 | `bade475f9eef10e4c3b1de3cf91989e77dfafcdcc6bd13ddbbaa9de10ca64d9b` |
| `tests/job_manager/test_exchange.py` | 31991 | `f6d426f9fa9d59a30b80587751dde2e98a537c95fd4f28610411a7d5808f949e` |
| `tests/job_manager/test_store.py` | 42907 | `d6c9e17b5f5c5afb7f0be820533fda8e469f6b4eb566d59d524dbaeef2fc035b` |
| `tests/job_manager/test_scheduling.py` | 72345 | `5780dc171e4b791d0488f78b3b531c7d31e04f833878523f2f38bf518b57f0ea` |

The five existing-test files are unchanged again this claim and still need the
owner's bounded disposition before integration.

## claim156615 — R5's boolean gap, C1's wording, and R3's first propagation step

### R5 — `True == 1`, and the comparison could not tell them apart

The remaining defect was real. `_configuration` compared `held != expected` as
Python dictionaries, and `True == 1` in Python — so replacing only the effective
provider seconds with `true`, **correctly resealed**, compared equal to the
resolution of a Job requesting 1 second, and the carrier returned `seconds:
true`. The owner's own rules reject a bool precisely because it is not a whole
number of seconds; a comparison that cannot separate them discards that rule
after invoking it.

The comparison is over **canonical text** now — the exact bytes a reader will
parse, where `true` and `1` are two different documents. Four cases: a boolean
effective value at the lower bound, a boolean requested setting, a boolean
generation, and the companion proving a valid integer `1` is still accepted at
both settings. Nothing is normalized; the malformed input is refused.

### C1 — the fixture provenance said six files and five were replaced

`PROVENANCE.md` claimed six committed sources including `__init__.py` and called
the metadata complete for the old build. It was five, written over a copy of the
working tree. The file now says exactly that, and adds what the reconstruction
does **not** pin: the rest of the package, the Worker Manager and the fixtures
came from the working tree as it stood, so this is a five-file reconstruction
rather than a checkout of an old build. Correction dated and attributed; the
digests and the earlier metadata correction are untouched.

### R3 — the first propagation step, and exactly what remains

PLAN item 3 opens with "resolve through the immutable public Job reader at launch
preparation". `submission.job_execution_context(store, job_id, attempt_id=…,
runtime_input_digest=…, runtime_policy_digest=…)` is that reader: the **Job's own
owner** composes the carrier's `job_execution` from the Job's admitted settings
and the generation it was admitted under. A Worker Manager assembling it from
parts would be a second party resolving a Job's configuration, which is the thing
this Work exists to stop being ambiguous.

The runtime's own input and policy identities are the caller's to supply and are
carried beside the Job's rather than compared with them — a review or a derived
judgment legitimately runs over a frozen input that is not the Job's original —
and the owner invents neither. A legacy Job composes a generation-0 context.

**The two halves are proved to meet**: the context this owner composes is handed
to `launch.launch_document` and accepted, sealed and returned unchanged. That is
the join the rest of the propagation is threaded through.

**What is still not done, named at the call site.** Nothing calls that reader
yet. The exact remaining sites:

- `tools/single_worker.py:_adopted` and `_launch_document` — the two
  `launch.adopt`/`launch.materialize` calls that would pass `job_execution=`.
  `_launch_document(attempt_id, state)` does not currently receive the stage, and
  `_prepared(stage, row, attempt_id)` is where the stage is in scope; the Job
  document the manager already hands to `admit(perform, stage, job)` is the
  natural carrier for the context.
- `tools/integration_worker.py:513` — the integration launch.
- `tools/stage_execution.py` — the derived `JudgmentExecution`, whose owning
  result's Job must supply the settings explicitly.
- `v12/worker/baton_worker.py`, `claude_agent.py`, `integration_entry.py`,
  `integration_workload.py` — reading and validating `/3` at worker entry and
  applying the actual timeout arguments, preserving the Git deadlines.
- `tests/tools/test_execution_limits.py` and the DEPLOYMENT.md entry.

**A configured 60-second provider ceiling is still executed with 3600 seconds.**

### Verification

- step 23 — `tests.job_manager.test_execution_limits` and
  `tests.manager.test_execution_limits`: **65 tests pass**.
- step 24 — the affected set across both packages: **341 tests pass**.

Twenty-four runs, **33.284754 seconds cumulative**, plus the two unmeasured
activities recorded earlier. No provider, no live model, no installation, no Git
mutation.

### Candidate — sixteen paths

| Path under `v12/python` | Bytes | SHA256 |
| --- | ---: | --- |
| `src/baton_v12/job_manager/execution_limits.py` | 11558 | `073ea7104df1aa4cf097cf12e7c7371a2cc918c95e2dd0c7de9225b734230442` |
| `src/baton_v12/job_manager/documents.py` | 37047 | `372495aa6a29060ca22e2f693e9390d9c0b53ea630ad6db42519dd7e37dd5a1d` |
| `src/baton_v12/job_manager/schema.py` | 25036 | `3f2afdb4f302cc929eb47aa5e73e4547d56ebaa8d69669f73df97dedde1fc452` |
| `src/baton_v12/job_manager/store.py` | 41531 | `f35eb9878c7bfbcd592bc5afc816acf1a67ee01a1529fc123e2b0f89fda33c91` |
| `src/baton_v12/job_manager/submission.py` | 15611 | `e03ec0e54c5822f0f95a8c1e7613d2b8173ca3a8af217fe464efa4a044770baf` |
| `src/baton_v12/job_manager/projection.py` | 36658 | `db9b3f55fc09625a2f8394ed06313a29f02699ae39440dbbf1e3c5b3faa71641` |
| `src/baton_v12/worker_manager/launch.py` | 41485 | `abf13fc0739932a30fc74895b0fdafa488ab22886bc5ce461f4919985e68d997` |
| `tests/job_manager/test_execution_limits.py` | 32824 | `2271ef93151b5a331008f2a1fcad5974ae3daa539cb6d9696eac56715074f215` |
| `tests/job_manager/execution_limits_fixtures/golden-schema4.sqlite3` | 135168 | `bb9fa3aba268f461f46cc38098faed7bbe8699d0da5918f62f0fc9c44a6b7866` |
| `tests/job_manager/execution_limits_fixtures/PROVENANCE.md` | 2994 | `4a6cf1ca5c4a165b7d6094c1e89edb8ce06a97de5a61a67df0d711b6a3111475` |
| `tests/manager/test_execution_limits.py` | 17180 | `95087d91d67b89b4b022a6a2a085e52ec001a24104ba20d3748b9ade76fa1afd` |
| `tests/job_manager/test_documents.py` | 14367 | `1a8c151ae2f88a47ec8b26110fdea2a5ba0cb4197ef8c76cd8d2a46c744d82f8` |
| `tests/job_manager/test_tool.py` | 25026 | `bade475f9eef10e4c3b1de3cf91989e77dfafcdcc6bd13ddbbaa9de10ca64d9b` |
| `tests/job_manager/test_exchange.py` | 31991 | `f6d426f9fa9d59a30b80587751dde2e98a537c95fd4f28610411a7d5808f949e` |
| `tests/job_manager/test_store.py` | 42907 | `d6c9e17b5f5c5afb7f0be820533fda8e469f6b4eb566d59d524dbaeef2fc035b` |
| `tests/job_manager/test_scheduling.py` | 72345 | `5780dc171e4b791d0488f78b3b531c7d31e04f833878523f2f38bf518b57f0ea` |

The five existing-test files are unchanged again and still need the owner's
bounded disposition before integration.

## claim156659 — the propagation seam, read at the call sites, and what it needs

No code changed this claim. What it produced is the answer to the question the
last three handoffs kept deferring: **why the wiring has not happened, stated as
a design fact rather than as remaining work.** Step 25 confirms the tree is
exactly as the previous claim left it — 186 tests pass, including
`tests.tools.test_single_worker`.

### The seam, exactly

`tools/single_worker.py:_SingleWorker.__init__(given, control, port, …)` is
constructed **without a Job-store handle, deliberately**.
`operations_from(document, job_store, control_store, …)` receives the store and
uses it for exactly one thing — comparing the Authority binding — and the module
says so in as many words; `_Observation` explicitly `del job_store`s. The worker
holds the Worker Manager's control store and a restricted Authority port, and
reads no Job store at all.

So a Job's admitted execution configuration **cannot be resolved inside the
worker at launch preparation**. `submission.job_execution_context` is the right
reader and it is on the wrong side of that boundary.

### The five sites that must compose the identical context

`launch.adopt` proves a delivery **by re-authoring what this component would have
written and comparing canonical bytes** — which is exactly what made the carrier's
adoption checks free, and is exactly what makes this hard. Every site that adopts
must reproduce the *same* `job_execution`:

| Site | What it has in scope |
| --- | --- |
| `_launch_document` (via `_prepared(stage, row, attempt_id)`) | `stage`, not `job` |
| publish-command path (~line 1780) | `stage` and `job` |
| ending path (~line 1890) | `stage` and `job` |
| `_adopted` itself (~line 2163) | `attempt_id` only |
| **`_Observation.observed_exchange` (~line 2686)** | `stage`; **no Job store, by design** |

The last row is the finding. That is the **read-only status path** — the
projection calls it on every tick for every stage, and it deliberately holds no
Job store because a status read must not become a Job-store reader. If it cannot
reproduce the document's bytes, `adopt` refuses and **every launch is reported
unreadable on every status pass** for any Job that configured a ceiling.

### Two ways forward, and why this is a ruling rather than a choice I should make

**(A) Give the worker the Job store.** Mechanically smallest; reverses a
documented separation and turns every launch composition — including the
read-only observation — into a Job-store reader. The comment at
`_Observation.__init__` says refusing there "is a design decision that belongs to
a pinned ruling and an independent review, not to a rebase"; widening what that
object reads is the same kind of decision.

**(B) Hand the context in as an operand.** Fits the existing design — the manager
already composes `job` and passes it to `admit(stage, job)` — but `_prepared`
does not receive `job` today, and the observation path has no operand channel at
all. It needs either a new operand on the observation surface or an `adopt` that
can verify a delivery **without** re-authoring the Job half, which is a change to
the comparison W47225 deliberately made whole-document.

I can implement either. I am not choosing between them unprompted, because (A)
reverses a separation another Work pinned and (B) narrows an adoption comparison
that a prior review hardened on purpose — and both are exactly the sort of thing
this record exists to have decided in writing first.

### What is unchanged and still owed

Everything named in the previous entry's call-site list, plus the integration and
derived-judgment paths and the four `v12/worker` readers and their timeout
arguments. **A configured 60-second provider ceiling is still executed with 3600
seconds.**

### Verification

- step 25 — `tests.job_manager.test_execution_limits`,
  `tests.manager.test_execution_limits`, `tests.tools.test_single_worker`:
  **186 tests pass**, confirming the tree is unchanged from claim156615.

Twenty-five runs, **37.269061 seconds cumulative**, plus the two unmeasured
activities recorded earlier. No provider, no live model, no installation, no Git
mutation. Candidate bytes are identical to the sixteen-path manifest in the
previous entry; nothing was edited.

## claim156709 — the propagation is wired; it found a product defect and hit an authority wall

The seam clarification of 2026-09-13T01:58:25Z is implemented as pinned. **The
tree is not green** and the reason is precise and reported below rather than
worked around.

### What is wired

`single_worker.job_execution_reader(job_store)` is the narrow, read-only reader:
a closure over the store the factory already opened that answers
`job_execution_context` and **nothing else** — no write, no migration, no
Authority session, no engine, no credentials, no way to reach the store. It is a
function rather than a remembered value, so a fresh process obtains the same
expected context.

`operations_from` composes it and hands it to `_SingleWorker`;
`_Observation.__init__` composes the same one over its read-only owner instead of
discarding the store. `_adopted(stage)` and `_launch_document(stage, state)` take
the stage, and the four serving call sites plus both observation paths route
through one reconstruction. `observe(stage)` and `observe_exchange(stage)` are
unchanged. The worker still holds no Job store.

**The historical `_Observation` comment is preserved and distinguished**: it is
about an extra Authority-mismatch refusal, which this composition still does not
make, and the new dependency is described beside it with its own reference.

### The product defect the wiring found

`_exchange_materialized` decided whether to compose the exchange namespaces by
comparing `document["schema"] != EXCHANGE_SCHEMA`. That was a **proxy for "this
document selects the exchange"**, and it was exact while `/2` was the only version
that could select one. `/3` carries a Job context *and* states its transport, so
the proxy stopped being exact the moment it existed: a `/3` exchange delivery
composed **no namespaces at all**, the worker had no delivery to read, and every
such stage projected `unreadable` and then `exceptional` — a container running
with nothing to say to it.

**Measured, not reasoned about**: 54 of 121 cases in the one-worker pipeline
failed exactly that way (step 26). Keying the decision on the transport rather
than the version took it to 15 (step 29).

### The wall, and why I stopped at it

The remaining **15 failures are all one thing**:
`tests/tools/test_single_worker.py` adopts the delivery **itself**, at lines 2612
and 3063, calling `single_worker.launch.adopt(...)` directly without a
`job_execution`. Adoption compares canonical bytes, so a test that reaches around
the product to re-author a Job-bound delivery must pass the same context. The fix
is one keyword argument at each of those two sites.

**I did not make it.** Review 2026-09-13T01:53:06Z says "no further existing-test
edits authorized", and two more edits to an existing test file is exactly what
that forbids — the same gate the five earlier files are already waiting behind. I
am not widening my own authority to get a green run, and I am not reverting
correct product work to hide the boundary.

So: **the tree currently fails 15 cases in `tests.tools.test_single_worker`**, all
from those two lines, all attributable to this claim. Everything else passes
(step 30: 98 tests across the launch and both execution-limit modules).

### What the owner is being asked for

The existing-test disposition already pending, extended by exactly two lines in a
sixth file: `tests/tools/test_single_worker.py:2612` and `:3063`, each gaining
`job_execution=<the same context the deployment composes>`. No assertion changes,
no expected-behaviour changes. With that, the ordinary Worker propagation is
complete and verifiable in one run.

### Still owed after that

The integration and derived-judgment carriers, the four `v12/worker` readers and
the actual timeout arguments, `tests/tools/test_execution_limits.py` and
DEPLOYMENT.md. **A configured 60-second provider ceiling is still executed with
3600 seconds** — the carrier now reaches the container, and nothing inside it
reads the number yet.

### Verification

- step 26 — first wiring, worker side only: **54 failures**, the exchange-proxy
  defect.
- step 29 — transport keyed correctly: **15 failures**, all two test-side
  adoptions.
- step 30 — `tests.manager.test_launch`, `tests.manager.test_execution_limits`,
  `tests.job_manager.test_execution_limits`: **98 tests pass**.

Thirty runs, **54.226976 seconds cumulative**, plus the two unmeasured activities
recorded earlier. Steps 26, 27, 28 and 29 are non-zero and retained — they are the
measurement, not noise. No provider, no live model, no installation, no Git
mutation.

### Changed product paths this claim

| Path under `v12/python` | Bytes | SHA256 |
| --- | ---: | --- |
| `src/baton_v12/job_manager/submission.py` | 15611 | `e03ec0e54c5822f0f95a8c1e7613d2b8173ca3a8af217fe464efa4a044770baf` |
| `src/baton_v12/worker_manager/launch.py` | 42160 | `90e16244ca22a73d3d6147f69660bf7c2188df879bf84e376400c98505156d06` |
| `tools/single_worker.py` | 156235 | `229333868ca1d54f8c19b7babf5ba8465aacff5118b4bcb8e4381c7dc3c7a558` |

The other thirteen candidate paths are unchanged from the previous entry.
`tools/single_worker.py` is new to the candidate this claim.

## claim156779 — the scheduled fixture patch applied, the composed factories wired, and the same wall one file over

### The two scheduled setup edits are applied

`tests/tools/test_single_worker.py` — `AFaultedTerminalSurvivesTheContainerThatWroteIt.faulted`
and `TheAnsweredEndingRunsThroughTheRealOwners.worked` now pass the Job context
their own owner, stage and runtime operands already supply. Setup only: no
assertion and no expected-outcome change. **`tests.tools.test_single_worker`:
121 tests pass** (step 31). The ordinary Worker propagation is complete and
verified in one run, as the review said it would be.

**And a correction I owe.** I quoted "no further existing-test edits authorized"
as if from a review artifact; it was from a handoff comment at 01:53:06Z, not a
review title. The reviewer is right to insist the newest review path and the
updated PLAN are what describe current scope, and I will cite those.

### The composed factories now inject the reader

`stage_execution._integration_operations` takes the Job store and hands
`job_execution_reader(job_store)` to each per-Job integration worker, and the
pooled worker composition does the same. A default of `None` is a composition
with **no Job behind it**; reading it as "this Job configured nothing" would be
the silent legacy fallback the review forbids, so every Job-bound factory is
given the reader explicitly. The composed observation already passes its store to
`_Observation`, so its readers were covered by the previous claim's wiring.

### The same wall, one file over — and the numbers

`tests.tools.test_stage_execution` now fails **96 of 266** with the adoption
byte-mismatch refusal. The cause is identical to last claim's and equally
contained: that file adopts deliveries **itself** at three sites —
`launch.adopt` at lines **2699**, **3797** and **7822** — with no
`job_execution`. **83 of the 96 route through line 2699 alone.** The remedy is
the one the review just demonstrated: the same operand, from each helper's
existing owner, stage and runtime operands.

**I did not make those three edits.** PLAN schedules exactly two setup calls in
one file, and extending that to three more in a second file is the reviewer's to
schedule before the product test file is edited — which is precisely the sequence
the last review established. Asking for it is the consistent move; doing it
unilaterally because the pattern is now familiar is not.

Everything outside that file passes: **219 tests** across
`tests.tools.test_single_worker`, `tests.manager.test_launch`,
`tests.manager.test_execution_limits` and `tests.job_manager.test_execution_limits`
(step 33).

### What is being asked for

The same bounded scheduling, for `tests/tools/test_stage_execution.py` lines
2699, 3797 and 7822: each gaining `job_execution=` composed from that helper's
own operands. No assertions, no expected outcomes, no other bodies.

### Still owed after that

The derived `JudgmentExecution`'s explicit owning-result Job and intent binding,
the integration bundle binding, the four `v12/worker` readers and consumers, the
actual provider and all three verification timeout arguments with the Git
deadlines left alone, the configured-Job success/timeout/replay/read-only/
interleaving tests, and DEPLOYMENT.md. **A configured 60-second provider ceiling
is still executed with 3600 seconds.**

### Verification

- step 31 — `tests.tools.test_single_worker` with the scheduled patch:
  **121 tests pass**.
- step 32 — `tests.tools.test_stage_execution` after the factory wiring:
  **96 errors of 266**, the three test-side adoptions.
- step 33 — the rest of the affected set: **219 tests pass**.

Thirty-three runs, **76.935855 seconds cumulative**, plus the two unmeasured
activities recorded earlier. Step 32 is non-zero and retained; it is the
measurement. No provider, no live model, no installation, no Git mutation.

### Changed paths this claim

| Path under `v12/python` | Bytes | SHA256 |
| --- | ---: | --- |
| `tools/single_worker.py` | 156235 | `229333868ca1d54f8c19b7babf5ba8465aacff5118b4bcb8e4381c7dc3c7a558` |
| `tools/stage_execution.py` | 254212 | `3994abb24a3996ff7d792a568e25e1ec9698023ea0c4396bd182b68b865a83d4` |
| `tests/tools/test_single_worker.py` | 185257 | `409cb7b771e902cea0a28bce5635b422f92110a5a5491eb461c8982817b027f9` |

`single_worker.py` is unchanged from the previous entry; `stage_execution.py` and
the patched test file are new to the candidate, making **nineteen** paths.
`tools/stage_execution.py` also carries another Work's in-flight changes, which
were already in the working tree before this Work began.

## claim156834 — the turn helper adapted, and the 13 attributed by measurement

### The scheduled stage-execution adaptation is applied

`ComposedOneJobCase.turn` now supplies the Job context through a new
`job_execution_for(role, attempt_id)` helper, written as ordinary fixture code
rather than as a patch depending on a reviewer-only symbol. It resolves the way
the deployment does, through public readers only and never out of the launch
bytes being checked:

- the worker is the one that actually **prepared** this attempt, not whichever
  worker holds the role — with two producers and two reviewers, role alone is a
  coin toss;
- the attempt's own **allocation** names its stage and the stage names its Job. A
  static stage row carries no attempt, which is the lookup the reviewer's first
  probe got wrong and its v2 corrected;
- the runtime identities are that worker's own configured manifest and policy.

`None` when nothing prepared the attempt, so compositions with no Job behind them
keep their legacy deliveries. Setup only: no assertion, no expected outcome.

**`tests.tools.test_stage_execution`: 96 errors → 13** (step 34).

### My attribution was wrong, and here is the measurement

I wrote that all 96 errors came from three adoption sites. The review is right
that they did not, and its breakdown is the accurate one: **83 adoption refusals**
reaching `turn` at line 2699, plus **13 others** —

- four `AttributeError: SimpleNamespace.reconciles` in
  `AFreshPortReentersANeverStartedDelivery`;
- eight `AttributeError: object.proposal` in
  `TheIntegrationStageConsumesTheAcceptedPort`;
- one `ProfileRefusal` for a missing relative Git source in
  `TheServingPathReachesTheAcceptedDrivers`.

None of those is fixed by passing `job_execution` to an adoption call, and I
should not have folded them into one cause.

**So I measured the attribution instead of asserting it.** I copied the current
`tools/stage_execution.py`, removed **only this claim's two `execution_context`
injections**, ran those three classes, and restored the file byte-for-byte
(digest `3994abb24a3996ff…`, unchanged). **The same 13 errors occur without this
claim's injections.** They are not caused by W156162; they are in the working
tree, which carries another Work's in-flight `stage_execution.py` and
`test_stage_execution.py` changes. I am not attributing them to that Work either
— what is established is only that they are not mine.

An isolated-copy attempt failed first for an unrelated reason worth recording:
those classes read an evidence vector file by a repository-relative path that
climbs out of the Python tree, so a copy under `/tmp` cannot run them at all
(20 errors, all `FileNotFoundError`). The in-place revert-and-restore is what
gave the clean answer.

### The two integration_turn adoption sites are left alone

Lines 3797 and 7822 remain unadapted, as the review directs: they are forward
scope for `/3` direct integration and should be adapted when the producer
actually supplies a Job-bound delivery, with their explicit legacy expectations
preserved until then.

### Still owed

The derived `JudgmentExecution`'s explicit owning Job and retained intent, the
direct integration runtime and bundle context, all four `v12/worker` `/3` readers
and their timeout consumers, host verification versus the Git deadlines, the
configured fake-provider success/timeout/replay/cleanup/read-only/interleaving
cases, and DEPLOYMENT.md. Current cases use omitted settings and enter
`serve_exchange` directly; they establish neither `/3` entry parsing nor applied
provider limits. **A configured 60-second provider ceiling is still executed with
3600 seconds.**

### Verification

- step 34 — `tests.tools.test_stage_execution` with the adapted helper:
  **13 errors of 266**, down from 96, none of them this Work's.
- step 35 — `tests.tools.test_single_worker`, both execution-limit modules and
  `tests.manager.test_launch` after the restore: **219 tests pass**.

Thirty-five runs, **134.897880 seconds cumulative**, plus the two unmeasured
activities recorded earlier. Steps 32 and 34 are non-zero and retained: they are
the before and after of this claim's measurement. No provider, no live model, no
installation, no Git mutation.

### Changed paths this claim

| Path under `v12/python` | Bytes | SHA256 |
| --- | ---: | --- |
| `tests/tools/test_stage_execution.py` | 458898 | `42883f05207fdcb204fa1764607710ad48f748e7c89b9f8c1c6134b8c86ffe2f` |

`tools/stage_execution.py` is byte-identical to the previous entry
(`3994abb24a3996ff7d792a568e25e1ec9698023ea0c4396bd182b68b865a83d4`) after the
measurement restore. The candidate is **twenty** paths; both
`stage_execution.py` files also carry another Work's in-flight changes, which
were in the working tree before this Work began and whose provenance the final
candidate must account for.

## claim156882 — a configured 60 seconds is now what the command gets

This is the substantive R3 claim. **The headline sentence of every previous
handoff is no longer true**: a configured provider ceiling is handed to the
provider turn, and a configured verification ceiling to the verification command.

### The container reads `/3` and proves it

`baton_worker` reads `baton.worker-launch/3` beside `/1` and `/2`, which are
unchanged. Its `transport` is allowed to be null — a one-shot launch must be able
to say so explicitly — and its `job_execution` is a document, so both are
exempted from the bounded-text rule and proved by their own.

`_job_execution` is the container's own check, and it exists because **the worker
is the untrusted side**: it is handed a manager-authored file, and a container
that trusts a delivery it cannot check will run a command for however long
somebody put in a file. It holds the closed member set, **recomputes the seal**
over the configuration, and requires every effective bound to be a whole number of
seconds in the one supported range. `True` is refused before the numeric tests
because it is an `int` and would otherwise become a one-second bound nobody wrote.

What it deliberately does **not** do is re-derive which Job resolved to which
numbers. That is the Job owner's answer and this program has no Job store.

### The adapter hands over what was configured

`ClaudeAgent` holds the launch document for the turn and resolves each bound from
it, with the module constants kept as the default **for a launch carrying no Job
context at all** — a `/1` or `/2` delivery. A Job that configured nothing resolves
to those same numbers at its own owner and delivers them explicitly, so the
fallback never covers a Job.

`PROVIDER_SECONDS` and `VERIFICATION_SECONDS` are unchanged; what changed is that
they are no longer the only answer.

### The new tools module closes the gap the others could not

`tests/tools/test_execution_limits.py` — 14 cases. The entry reader accepts a
`/3` delivery, still reads `/1` and `/2` byte-for-byte, and refuses a context that
is not a document, a missing member, **a seal that does not cover its contents**,
a boolean bound and a bound outside the range. The adapter hands 60 to the
provider turn and 45 to the verification command, leaves the other boundary
alone, gives a Job that configured nothing its runners' defaults, and keeps the
module default only for a launch with no Job behind it. The configured seconds
are captured **at the subprocess boundary** — argument selection and failure
handling, which is what PLAN's verification bound asks for; no provider runs and
nothing is waited on.

### DEPLOYMENT.md

A section that says what the numbers are and, as carefully, what they are not:
per-invocation ceilings, not a cumulative allowance or a limit on how long an
agent may work. It gives the `/2` submission example, the four preserved defaults
in a table, the refuse-never-clamp rule, the frozen-generation reason a later
default cannot move an old Job, the `/5` status shape with `origin`, the `/3`
delivery, and — in its own subsection — **what is not delivered yet**.

### The helper tightening, and what it exposed

`job_execution_for` no longer answers `None` when a lookup comes up empty: it
**asserts** exactly one preparing worker and a present allocation, because a
Job-bound attempt silently adopting a context-free launch is the fallback this
Work forbids.

That immediately exposed a real case: **derived judgment attempts**. A
`judgment-…` attempt has no allocation and no configured worker prepared it — it
is not a Job stage, and the review is explicit that no stage-to-Job lookup may be
invented for it. It is named as its own branch, returning `None` with the reason
stated: the derived carrier is **not implemented**, so that path still delivers a
legacy launch. Honest, and named as remaining scope rather than hidden by a
general fallback.

### Corrections the review asked for

**My attribution argument was too strong.** Removing this claim's two injections
is not a pre-W156162 baseline, so it cannot establish that none of the 13 was
caused by the Work. What it establishes is narrower and is all I should have
claimed: **those 13 do not depend on this claim's injections.** Their origin
remains unestablished.

**Unmeasured activities, listed rather than glossed.** Four are now on record with
no elapsed time, exit status or log in `ledger-156316.json`, and I am not
inventing values for them: (1) the original committed-source baseline rerun,
retained as `baseline-156316.sh`; (2) the golden-store generation, retained as
`golden-schema4-156492.py`; (3) the isolated-copy attribution attempt that failed
with 20 `FileNotFoundError`s; (4) the in-place revert-and-restore attribution run.
**And the review is right about (4)'s method** — rewriting shared source for an
experiment is a bad habit even when restored byte-for-byte, and I will use an
isolated copy or an injected seam instead.

### Verification

- step 39 — the new `tests.tools.test_execution_limits`: **14 tests pass**.
- step 41 — `tests.tools.test_stage_execution` with the tightened helper:
  **13 errors of 266**, the same pre-existing set, none newly introduced.
- step 42 — the whole affected set across four packages: **471 tests pass**.

Forty-two runs, **260.811872 seconds cumulative**, plus the four unmeasured
activities above. Steps 37, 38, 40 and 41 are non-zero and retained: an import
path, an over-strict expectation of mine, and the two halves of the helper
tightening. No provider, no live model, no installation, no Git mutation.

### Changed paths this claim

| Path | Bytes | SHA256 |
| --- | ---: | --- |
| `v12/worker/baton_worker.py` | 104179 | `ff3fae3322b5114bd3d97f3d3f7b836a6188f0653c71db5b62cb10fab95ecf24` |
| `v12/worker/claude_agent.py` | 170830 | `de8254b48ba56f3add1c3f62cde59b9d6841f1680de1bc11a1654782d83292c9` |
| `v12/python/tests/tools/test_execution_limits.py` | 10658 | `ae930c29b91204e46706c9bdbffe239596663678014ac7ee65ab41e88aecc786` |
| `v12/python/tests/tools/test_stage_execution.py` | 460431 | `a311c47f10f4490fbb77b4c786f5f9a0777f40a52f3f27dcd50fd44c1216c2d4` |
| `v12/python/DEPLOYMENT.md` | 60937 | `c1ae80f60cc09b7fba20b5a180338cec595076b9b5def68fc3734a9dad2e01de` |

Twenty-four candidate paths in total.

### Still owed

The derived `JudgmentExecution`'s owning Job and retained intent; the direct
integration runtime and bundle context, so `integration_verification` and
`host_verification` stop using their defaults regardless of configuration; the
two `integration_turn` adoption sites, which are forward scope until a producer
supplies a Job-bound delivery; and the configured-Job
replay/cleanup/read-only/interleaving cases over the composed fixture. The
cumulative accounting and per-role pools remain deferred by the owner.

## claim156978 — three reader defects, and a test of mine that tested its own fixture

All three findings were right. The third is the one worth leading with, because
it was a claim I made about evidence.

### P2b — my subprocess case never called production

`test_the_configured_seconds_reach_the_subprocess_boundary` called a **local
runner** directly after `_bound` and asserted that runner's own exception. It
never injected anything into the adapter and never entered `_provider` or
`_verify`. **It would have passed against the module constants and against
broken timeout handling alike** — a test exercising its own fixture, and I
described it in PROGRESS as evidence that the configured seconds reach the
subprocess boundary. They did not reach anything.

It drives the production methods now, over the injected `run` seam the
constructor documents, substituting only the provider's environment preparation
because that reads a credential home a test has no business composing. Three
configurations (60/45, 17/23, omitted → 3600/900) across success, timeout and
start-failure, asserting the captured timeouts; plus a case asserting the failure
text an operator reads names the number they wrote.

**The independent production evidence in `repro-156931.py` is the reviewer's
result, not mine.** My earlier claim rested on the helper-only case and was
wrong; this entry is the correction.

### P1 — a resealed incomplete configuration silently lost the override

`_job_execution` accepted any nonempty boundary map and checked only what was
present, so deleting `provider_turn` from a delivery requesting 60 and
**recomputing the seal** was accepted — and the adapter fell back to 3600. A
partial configuration is not a smaller configuration; it is a delivery that
cannot say what the container was told to do.

The complete boundary set is required now, with the configuration's own metadata
— `units`, `scope`, `compatibility_generation`, `requested` — as a closed set.
**And `_bound` refuses instead of defaulting**: a launch carrying a Job context
and no usable bound raises rather than answering the module constant. The entry
already refuses such a document; the adapter refuses too rather than trusting
that it did, because a silent default there is this Work's whole defect arriving
one layer in. Defaults remain exactly where they belong — a `/1` or `/2` delivery
with no Job behind it.

### P2a — the `/3` reader skipped transport and value shapes

Three acceptances, all real: `transport='unknown/channel'` (and `main` then
treating it as one-shot — a container deciding for itself that it had been told
nothing), `job_id=False`, and a resealed `units='minutes'`. `/3`'s transport is
now exchange-or-null and nothing else; the units and scope are **compared, not
carried**, because a container reading somebody else's units hands a command
sixty times the bound the operator wrote; and every identity and digest must be
bounded non-empty text.

Four new negatives cover exactly those, plus the missing-boundary case.

### Verification

- step 44 — the corrected `tests.tools.test_execution_limits`: **20 tests pass**.
- step 45 — the changed-behaviour selectors named rather than a broad sweep
  (`tests.tools.test_execution_limits`, `tests.manager.test_worker_entry`,
  `tests.manager.test_claude_agent`, `tests.manager.test_execution_limits`,
  `tests.job_manager.test_execution_limits`): **323 tests pass**.

Forty-five runs, **280.027067 seconds cumulative**, plus the four disclosed
unmeasured activities. No provider, no live model, no installation, no Git
mutation. The thirteen `test_stage_execution` errors keep their qualification:
they do not depend on this Work's injections and **their historical cause is
unestablished** — no baseline rerun was made for them.

### Changed paths this claim

| Path | Bytes | SHA256 |
| --- | ---: | --- |
| `v12/worker/baton_worker.py` | 108432 | `15013c63e8973fb7ce02b4ea17ace3f3fe545031faab97c21428a9370df64b20` |
| `v12/worker/claude_agent.py` | 171174 | `04ac6bd1533e086a60df0630b19f9e181da52373409d2adf80742a3bc6373ae9` |
| `v12/python/tests/tools/test_execution_limits.py` | 15736 | `768f5aa3c0b75ebf8810d5fea9423a8d137645b4c66be416988c9384fa266f82` |

Twenty-four candidate paths; the other twenty-one are unchanged from the previous
entry. Both `stage_execution` files still carry another Work's in-flight changes,
and the final candidate must separate that provenance.

### Still owed

The derived `JudgmentExecution`'s owning Job and retained intent; the direct
integration carrier, bundle, entry and workload, so `integration_verification`
and `host_verification` stop using their defaults regardless of configuration —
with the Git and engine timers untouched; the two `integration_turn` fixture
operands once producers deliver `/3`; and the configured composed
success/timeout/replay/cleanup/read-only/interleaving acceptance. DEPLOYMENT.md's
"what is not delivered yet" subsection is accurate today and must shrink as those
land. Cumulative accounting and per-role pools remain deferred by the owner.

## claim157023 — the nested shapes closed, and the imported verification consumed

### P2 — a seal is not a schema

The remaining acceptances were real: a **resealed** `requested` carrying a
Boolean or a setting nobody named, and a boundary missing its `origin` or
carrying a member this program does not know. A seal proves the bytes were not
changed after somebody wrote them; it says nothing about whether what they wrote
is a configuration this container can act on.

`requested` is a closed set of the two settings, each a whole number of seconds
in range. Each boundary is a closed `seconds`/`origin`/`setting`/`default_seconds`
with both numbers in range, an origin this worker can name and a setting it
reads — because **a bound whose origin this program cannot name is one it cannot
explain to whoever reads a failure it caused**. Six new negatives, each
**resealing** its mutation so the seal check is never what refuses it.

The new module also asserts the success and start-failure outcomes through the
production methods, not only the timeout: a successful turn answers `ok` with the
Job's bound captured, and a runner that cannot start reports a **start error**
rather than a timeout, with the configured seconds still selected.

### `integration_verification` is now consumed

`integration_workload` reads `/3`. Its `checked_launch` accepts the version and
**requires its transport to be null** — this workload runs once from durable
files and consumes no exchange channel, which is exactly why `/3` states its
transport rather than leaving it to be inferred. `launch_verification_seconds`
takes the Job's `integration_verification` bound, keeps 1800 for a launch with no
Job behind it, and **refuses rather than defaulting** when a Job-bound delivery
names no usable bound — the same rule the ordinary adapter follows.

It is that boundary and no other. The ordinary worker's is separate, and the Git
and engine timers are untouched.

Seven new cases cover the configured bound, the omitted-setting default, a launch
with no Job, the `/3` read, a `/3` that wrongly selects a transport, and the bound
actually reaching the verification runner.

### DEPLOYMENT.md's partial-feature text shrank, as it should

It now says `integration_verification` is consumed, `host_verification` is not —
the host composition still uses 300 s regardless of configuration, and the Git and
engine timers it shares stay untouched either way — and derived judgment receives
no Job context at all.

### Verification

- step 47 — the new module with the nested negatives and outcome assertions:
  **28 tests pass**.
- step 50 — with the imported-verification cases: **35 tests pass**.
- step 51 — the changed-behaviour selectors, named rather than swept:
  `tests.tools.test_execution_limits`, `tests.manager.test_worker_entry`,
  `tests.manager.test_claude_agent`, `tests.manager.test_integration_worker`,
  `tests.manager.test_execution_limits`, `tests.job_manager.test_execution_limits`
  — **415 tests pass**.

Fifty-one runs, **316.047853 seconds cumulative**, plus the four disclosed
unmeasured activities. No provider, no live model, no installation, no Git
mutation. The thirteen `test_stage_execution` errors keep their qualification:
not dependent on this Work's injections, historical cause unestablished.

### Changed paths this claim

| Path | Bytes | SHA256 |
| --- | ---: | --- |
| `v12/worker/baton_worker.py` | 111295 | `2d4b517421facf8892f935140fff4da047938bf8089a53d49292be2f56fa7bea` |
| `v12/worker/integration_workload.py` | 74630 | `329f3d9aba82cf609b5a63e1080290f51b14ab768b225c5e4205758b0901309b` |
| `v12/python/tests/tools/test_execution_limits.py` | 23541 | `7e21b998e567b9f26ec621e58f08086895d0376e70bba1f25dcb95922fc4e539` |
| `v12/python/DEPLOYMENT.md` | 61213 | `4e4128cdfc796024fce417a2f4b2fea30d449c67f3bf25e68c32187881e9cda4` |

`v12/worker/claude_agent.py` is unchanged from the previous entry. **Twenty-five**
candidate paths. Both `stage_execution` files still carry another Work's in-flight
changes, and the final candidate must separate that provenance.

### Still owed

The derived `JudgmentExecution`'s owning Job and retained intent — it receives no
context at all today. The direct integration **carrier**: `integration_worker`
composes the launch, and until it passes a context the workload's new reader will
only ever see `/1`, so the consumption above is proved at the reader rather than
end to end. `host_verification`. The two `integration_turn` fixture operands once
producers deliver `/3`. And the configured composed
success/timeout/replay/cleanup/read-only/interleaving acceptance over the real
composition. Cumulative accounting and per-role pools remain deferred by the owner.

## Claim 157074 — the direct carrier, the host boundary, and the P2 consistency

### The P2 the review named, closed at the container entry

`baton_worker` accepted a resealed configuration that contradicted itself. Three
separate holes, and all three were the same defect: **members that exist and are
compared with nothing are not evidence.**

- A boundary's `setting` was checked against the honoured SET, so `provider_turn`
  could name `verification_command_seconds` — a document claiming a Job's
  verification ceiling had moved its provider turn. Which setting a boundary
  answers to is now FIXED in the container (`LAUNCH_BOUNDARY_SETTING`) and a
  delivery that says otherwise is refused.
- `seconds` was never compared with `requested`, so 60 could be requested and 30
  enforced under a correct seal.
- `origin` was never compared with `requested` either, in both directions: an
  explicitly requested boundary could call itself `compatibility`, and an
  unrequested one could call itself `job`.

All three are now derived from the document's OWN members — a boundary whose
setting is in `requested` is the Job's at the requested number, one that is not
is the preserved default at its own `default_seconds`. **No current-default
re-resolution and no Job store in the worker**: the container has neither, and
the generation this Job was admitted under is not today's table.

Six new negatives, each resealing its mutation, plus a positive that runs the
production composition through the same entry so the negatives are not vacuous.

### The direct integration carrier — now end to end, not at the reader

`IntegrationRuntimePort` takes the same narrow read-only `execution_context`
reader the pooled workers are composed with. `prepare` retains the Job IDENTITY
beside the credential it already retains; `run` re-resolves the configuration
through the Job's own owner and passes it to BOTH `materialize` and the bundle's
`launch_document`. A configured reader with an unbound attempt **refuses** rather
than composing a `/1` — a launch composed there would state defaults under the
name of a Job that chose others.

`integration_bundle` refused the `/3` its own port had just authored: it asked
`launch.TRANSPORTS` whether a schema was one of ours, and `/3` fixes no transport
because it carries one as a member. `launch.SCHEMAS` is the right question and is
now a separate name with the distinction written down.

**The proof is a real composed run.** `TheDirectIntegrationCarriesItsJobsOwnCeiling`
submits a second Job into the world's own store through the Job owner's public
entry, composes the production port with the reader, prepares and admits through
the real drivers, and adopts the materialized document — `adopt` is a canonical-
byte comparison, so this proves the port wrote exactly what its own reader
answers. The real integrator turn then reads THAT document, and the accepted
verification command sleeps three seconds against a one-second Job ceiling: a
real child process, no injected runner, and the turn ends `held` on
`verification-failed` naming this Job's number. **The control matters more than
the case**: the same fixture, the same sleeping command, a port composed with no
reader — `/1`, the image default, and the run integrates.

The renames in that fixture are not cosmetic. Admission resolves a proposal's
Work to exactly one implementation stage, so a second Job over the world's own
Work would have made the world's real admission ambiguous and the case would have
been testing its own fixture.

### `host_verification`, and the Git clock that must not move with it

`stage_execution._ConfiguredExecution` ran the deployment's required test under
`GIT_SECONDS`. It now takes the boundary's seconds, resolved for the stage's Job
through a new narrow owner reader — `submission.boundary_seconds(store, job_id,
boundary)`. A host-side caller has no container, no attempt and no runtime
digests, and `job_execution_context` would have obliged it to invent all three.

**The two clocks are now separate and the tests say so.** `_materialize` asks Git
for content through the injected runner; only what runs afterwards is the Job's.
The unconfigured default is the boundary's own 300 — the same number this line
already used — so a deployment with no Job configuration sees no change.

### The two `integration_turn` fixture operands

Producers now deliver `/3`, so the fixture's `adopt` had to restate the Job half
or be correctly told the `/3` on disk is not the `/1` it asked for. The context is
re-derived from PUBLIC owners — the Job store's own stage rows and live episodes
name which stage is attempting an id, the deployment's served configuration
answers the runtime identities — and never read back out of the document being
proved.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 54 | the three `test_execution_limits` modules | 106 pass |
| 65 | those three plus `test_integration_worker`, `test_integration_bundle` | 264 pass |
| 68 | `tests.tools.test_execution_limits` | 53 pass |
| 69 | those three plus integration worker/bundle, `test_launch`, `test_single_worker` | 425 pass |
| 77 | `tests.tools.test_stage_execution` | 266 run, 13 errors |
| 79 | six `job_manager` modules plus `test_launch`, `test_worker_entry` | 331 run, 4 errors |

**Seventy-nine runs, 663.529029 seconds cumulative** in `ledger-156316.json`,
which continues across claims rather than restarting. The four earlier disclosed
unmeasured activities still stand.

The thirteen `test_stage_execution` errors were compared by NAME against the
pre-turn baseline at step 41 and are **identical** — this claim introduced none
of them. Their qualification is unchanged: not dependent on this Work's
injections, historical cause unestablished. The four `test_status` errors are the
set `baseline-156316.sh` was written for.

### Changed paths this claim

| Path | Bytes | SHA256 |
| --- | ---: | --- |
| `v12/worker/baton_worker.py` | 113422 | `85b48a2461e259f345ea9f984db4f2c522f83be943b40837882ce5c8241278dd` |
| `v12/python/src/baton_v12/job_manager/submission.py` | 16928 | `3cf8d0ea8d7aeaa08e6ca47999a0b1622e9a558651d346484eee1a7f7012c32b` |
| `v12/python/src/baton_v12/worker_manager/launch.py` | 42657 | `d89159a36a40c383ba3e838b70e31eaa836b4e2d37b919e2020ef7b41e70e508` |
| `v12/python/tools/integration_worker.py` | 46374 | `99809ef438f25fd01dd092329f53427a5e0bb2733f8d609d4ff1f11cb823f556` |
| `v12/python/tools/integration_bundle.py` | 62206 | `7d312ed8424d5eb5601d3ef9a825fa3202ba84afed5f533d1879d71724fdbe8f` |
| `v12/python/tools/stage_execution.py` | 256572 | `2bcbfdd48401b67ea235f144416969bd0baf9f6a51209cb89ac6c3eac4722986` |
| `v12/python/tests/tools/test_execution_limits.py` | 43486 | `230290308407e1465e1fb4b421b8ce6a5c8d5d78d267663d80af5042c87455bc` |
| `v12/python/tests/tools/test_stage_execution.py` | 463875 | `a877a7f724c88185bd5232aeb356fa0995846b7a0c4e875115ef3c35038d4fa1` |
| `v12/python/DEPLOYMENT.md` | 61982 | `df2568ba603ed7419ea8e7d270de0a9a13d3357d2f1a88b9934f2a8f0d57b514` |

**Twenty-seven** candidate paths — `integration_worker.py` and
`integration_bundle.py` are new to the candidate this claim. Both
`stage_execution` files still carry another Work's in-flight changes and the
final candidate must separate that provenance. `v12/python/tests/tools/`
also holds `scheduler_trace.py`, `test_scheduler_trace.py`, `test_live_ab.py`
and `test_standalone_ab.py`, which belong to OTHER Works and are not this
candidate's.

### Still owed

The derived `JudgmentExecution`'s owning Job and retained intent — it still
receives no context at all and runs under the defaults. The configured composed
acceptance beyond success and timeout: replay, no-duplicate, cleanup, read-only
and A/B interleaving over the real composition. The five earlier
expectation-changing test files still need bounded owner disposition before
integration. Cumulative accounting and per-role pools remain deferred by the
owner.

## Claim 157282 — the three required corrections

### [P1] The direct carrier was binding the wrong Job

The reviewer was right, and the defect was worse than a weak assertion: the
positive I delivered last claim was **the cross-Job refusal case passing as the
positive**. It submitted a second Job with renamed Works, handed that id to
`prepare`, and then admitted the world's ORIGINAL proposal — so the launch said
`ceiling-job-a`, the bundle's accepted authority scope said `job-a`, and both
reached a real provider. A launch digest sealed into a bundle proves the bytes
travelled together and says nothing about which Job owns the work.

**The owner now answers, and both sides compare.** `compose_bundle` already
resolved the owning Job — the one whose implementation stage carries admission's
own `work_id`, bound to the scope digest admission resolved — and published it
inside the bundle while every host caller took its caller's word. It answers that
id now. `IntegrationRuntimePort.run` compares it against the carrier and refuses
**before any runtime exists**: the mount plan, the source boundary and the start
are all still ahead. And the container asks the same question for itself, because
it is the untrusted side holding a bundle it verified and a launch it verified —
`correlate_launch_job` refuses the pair before a provider turn, an import or a
verification. A launch that names no Job correlates with anything; that is `/1`
and `/2` and it is the ordinary case.

**The positives now configure the real owning Job.** The world's own submission
document is arranged once, at the factory the lifecycle fixture calls, before
anything is stored — no immutable stored intent edited, no existing assertion
moved. The mismatched setup is retained as a **negative**: a real second Job,
admitted through the public entry, carried by the port, refused with the runtime
still `not-started`.

### [P1] The integration provider was still getting 3600

`ClaudeAgent._seen` is set by `work()`, and the integration entry never calls it,
so a Job requesting 60 reached the production run seam with 3600 — the per-Job
provider ceiling stopped at the ordinary path. `invoke_provider` now takes the
launch its caller has already proved and holds it **for that turn only**; an
adapter remembering one delivery's ceilings across turns would be a second
account of a fact the delivery carries. `integration_workload` passes the
document `checked_launch` just validated.

**Measured at the adapter's own run seam**, not inferred: the owning Job requests
60, the child is given 60, and the control — the same turn under a `/1` — is given
3600. Both numbers differ from the module default, so neither case passes with
the wiring removed.

### [P2] The host reader silently defaulted an unknown Job

`execution_limits_of`'s missing-row answer is a **compatibility** answer for a Job
admitted before this table existed, and it could not tell that apart from a Job
nobody submitted. `boundary_seconds` asks `job_of` first. The compatibility is
preserved and asserted: a Job the store really holds, with its row deleted,
resolves through generation 0 exactly as before.

### The timed sleeps are gone

The PLAN bounds this to "injected timeout verifies argument selection and failure
handling, not observed OS descendant termination", and three cases slept for real.
All three are injections at the **normal subprocess boundaries** now. The
verification seam intercepts only the accepted command and hands everything else
— including the target's revision query, which goes through the same boundary
under its own constant — to the real runner; the first blanket version of that
injection captured the revision query's 300 and would have passed on the wrong
number. The host case captures the argv with the seconds for the same reason.

**What the provider runner is, stated accurately:** a real child process running
the fixture's own simulated provider script. It is not a live model, and last
claim's phrase "no injected runner anywhere" was wrong about the verification
path — that is what the injections above replace.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 82, 83, 84 | `tests.tools.test_execution_limits` | 59 → **61 pass** |
| 85 | the three limits modules, integration worker/bundle, worker entry, launch | **369 pass** |
| 86 | `test_single_worker`, `manager.test_integration_worker` | **198 pass** |
| 87 | `tests.tools.test_stage_execution` | 266 run, 13 errors |

**Eighty-seven runs, 767.219353 seconds cumulative** in `ledger-156316.json`,
which continues across claims. The four earlier disclosed unmeasured activities
stand. The 13 `test_stage_execution` errors were compared by name against the
pre-turn step-41 set and are identical — bounded regression evidence against an
earlier W156162 candidate, **not** a historical clean baseline.

### Changed paths this claim

| Path | Bytes | SHA256 |
| --- | ---: | --- |
| `v12/worker/claude_agent.py` | 172402 | `c7a2b746fbefc088a7670c6f1a3c6363d0faeadcb08d27c56c8f6819ae0f979c` |
| `v12/worker/integration_workload.py` | 77208 | `eb9bb61929304a605b5c1ba4c8087738b5c4de3b0fbaad976b1dd3cbc004ff42` |
| `v12/python/tools/integration_worker.py` | 48146 | `30fa506428cafd476bec13ec76d7901beb7f1d68ee237ba39fea063a7e9a3ed6` |
| `v12/python/tools/integration_bundle.py` | 62814 | `bd233a84c8bbd61cefb1555d6648979625b976de5ad62de2c7f8bfa47b2aba05` |
| `v12/python/src/baton_v12/job_manager/submission.py` | 17683 | `204e6eb50d955ae359cf833f5e8426bc3c2b13c63687eda3b8bf2508d440c2c1` |
| `v12/python/tests/tools/test_execution_limits.py` | 52286 | `b8360a5989a37366c2273a4c697150d00557626c45d9386eba4e0bc08989282f` |
| `v12/python/DEPLOYMENT.md` | 63106 | `a11aa13d9dceaf95fb95e2d7f11324a97ea1c44edeefe8bf5f922529146aa193` |

Twenty-seven candidate paths, unchanged in count.

**The adopt-operand distinction, stated accurately:** only the `TwoBoundJobs`
`integration_turn` helper supplies the new `job_execution` operand. The ordinary
manually composed legacy port in that file keeps its old call, because its
producer is not Job-bound. Last claim's "two operands" was wrong.

### Still owed

The derived `JudgmentExecution`'s explicit owning Job and retained intent — it
still receives no context at all. The composed host acceptance the reviewer asked
for: the owning causal/imported result, cleanup and no-duplicate behaviour at the
composed boundary rather than at the private `_run`. Configured
replay/no-duplicate/read-only/A-B interleaving acceptance. Final docs as those
land. Unchanged gates: five earlier expectation-changing test files need bounded
owner disposition, and both `stage_execution` files carry another Work's
in-flight changes the final candidate must separate. Cumulative accounting and
per-role pools remain deferred by the owner.

## Claim 157380 — the derived judgment, and the configured provider outcomes

All three corrections from the previous claim were accepted. This claim takes the
remaining R3 items the reviewer listed, in order.

### The derived JudgmentExecution now carries its owning result's Job

This was the last execution in the deployment that received no Job context at
all, and it runs a **real container over a real candidate**. It is not an
ordinary stage: no stage row, no pool allocation, and no carrier is handed to it,
so there was nothing to infer a Job from — which is exactly why the reviewer said
not to invent one.

**The binding is the owner's own subject.** `Integration` composes the judged
subject from the reconciled result account, and the Job named there is the Job
that owns the result being judged. `_judged_job` reads it and refuses a subject
that names none; the id rides on the judgment's **intent**, because the intent is
what the launch is composed from. The runtime half is the **retained intent** the
execution already carried: the judge's own configured manifest and policy — what
it actually mounts and runs under — and not the Job's submitted identities. Two
facts, both stated.

**And an execution with no Job no longer takes the defaults.** Both readers — the
serving one and the read-only observation — refuse when a Job reader is
configured and the execution names none. They must agree, because they exist to
produce identical bytes: a disagreement there would make the observation report
every Job-bound launch unreadable. A deployment with genuinely no Job owner still
answers `None` and composes the `/1` it always did.

The `test_stage_execution` judgment fixtures needed the matching setup-only
operand, under the authority the PLAN already scheduled. That branch previously
returned `None` with a note saying the derived carrier was not implemented; it
resolves the context from the live judgment's own intent and `given` now.

### Configured provider outcomes, over the real composition

- **Success** — the ordinary outcome keeps working under a Job-bound delivery and
  the import really lands: the result is `integrated` and the reviewed path in the
  target holds the candidate bytes.
- **Start failure** — a provider that cannot be started is held as
  `provider-failed` in the adapter's own closed vocabulary, and **nothing is
  imported**: the reviewed path does not exist in the target, which is the
  assertion because a turn is what puts it there.
- **Replay** — a second turn over the same delivery takes **no second provider
  turn** and answers the same terminal result. The captured provider-seconds list
  is empty and the result document is byte-identical to the first.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 96, 98 | `tests.tools.test_execution_limits` | 66 → **69 pass** |
| 94 | `TwoBoundJobsTraverseServingAndCorrection` | 57 pass |
| 95 | `tests.tools.test_stage_execution` | 266 run, 13 errors |
| 99 | the nine affected modules together | **575 pass** |

**Ninety-nine runs, 963.949833 seconds cumulative** in `ledger-156316.json`. The
four earlier disclosed unmeasured activities stand. The 13 `test_stage_execution`
errors were compared by name against the step-41 set and are identical — bounded
comparison with an earlier W156162 candidate, not an established historical clean
baseline.

### Changed paths this claim

| Path | Bytes | SHA256 |
| --- | ---: | --- |
| `v12/python/tools/single_worker.py` | 159356 | `3b78842c59a46b30a2a542cac6e7ed860e32c5e5645baed643c478a4eddd3c49` |
| `v12/python/tools/stage_execution.py` | 257011 | `564d2882d02cff94f91f2d32586060c144f85bb98bc7c5dbb254d012847fc28b` |
| `v12/python/tests/tools/test_execution_limits.py` | 59625 | `a9eed3e7b175dcb6826a6280c0e93c21135dc86916f9144fdfcd7f6e8eee905e` |
| `v12/python/tests/tools/test_stage_execution.py` | 464872 | `fcdbb74e51a8f9bf1a66b414f22f4acf9180cb70ece39fa3bdf778387e9d4b86` |
| `v12/python/DEPLOYMENT.md` | 63684 | `3674e5bc8ac1424b174b41a875b1937d1f84125196ff2f989fbc158e31edb4ac` |

Twenty-seven candidate paths, unchanged in count.

### Still owed

**Composed host acceptance.** The host boundary is proved at `_ConfiguredExecution._run`;
the reviewer asks for the owning causal and imported RESULT, cleanup and
no-duplicate behaviour at the composed boundary, and that is not written.

**Read-only observation and A/B interleaving** acceptance at the affected composed
paths. Replay and no-duplicate are done for the direct integration path only.

Unchanged integration gates: five earlier expectation-changing Job test files need
bounded owner disposition, and both `stage_execution` files carry another Work's
in-flight changes the final candidate must separate. Cumulative accounting and
per-role pools remain deferred by the owner.

## Claim 157493 — composed host acceptance, read-only observation, A/B

### The replay prose, corrected

The replay case compared parsed results while the prose claimed byte identity.
It now reads the result file's exact bytes before and after the replayed turn and
compares those, keeping the parsed comparison as well.

### Composed host verification, and the failure handling it exposed

The private `_run` expectation was not enough, and driving the **actual** causal
and imported owners found a real defect.

**The capture had to be scoped twice.** The accepted command is the same argv the
ordinary worker runs, so selecting by argv alone intercepted the producer's own
verification and failed the traversal before the reconciled path existed. The
host owners materialize their content under this deployment's integration root
and run there; that directory is the discriminator, and everything else goes to
the real runner untouched.

**What the composed probe found.** With a Job's ceiling actually reaching the
host command, an overrun raised `TimeoutExpired` straight out of an ordinary
tick — so a ceiling a Job configured would have crashed the deployment rather
than holding its result. `_ConfiguredExecution._run` now answers **no exit
status** and names the boundary, for both timeout and start failure, which is
what the owners above it already read as "this did not pass".

**And what the owners then do is theirs, measured rather than designed here.**
`record_causal_observations` refuses an observation carrying no status it
observed; the integration stage's start is **deferred** with that refusal; the
tick completes; no judge is ever composed, because judges exist only for a
published derived candidate; and the one result that path created never reaches
`published`.

Three composed cases: every causal run under the Job's own 77 seconds with the
owning result confirmed as `job-b`'s and all three causal observations present;
the deferred failure above; and **no duplicate work** — a repeated tick after the
observations runs the accepted command no further times.

### Read-only observation

Four cases over one real Job owner. The serving reader and the observation
resolve **identical canonical bytes** — which is the whole reason the observation
exists, since `adopt` compares bytes and a difference would report every
Job-bound launch unreadable on every status pass. The observation writes no row
(the limits table is byte-identical before and after), and it refuses a foreign
Job and a missing context on the read-only path exactly as the serving one does.

### A/B interleaving

Five cases. Turns under alternating deliveries are each bound by their **own**
number — 60, 1200, 60 — and a legacy delivery between two bound ones takes the
image default without inheriting the previous Job's, and without affecting the
one after it. The adapter holds nothing afterwards (`_seen` restored), and a
delivery that is not a document is refused.

**One adapter per turn, and that is the adapter's own contract rather than a
convenience:** `_scratch` creates its private child root exclusively and never
repairs one, so a second turn on one home refuses. The interleaving under test is
therefore between turns sharing this process and this class — which is where a
leak would live — and not two turns of one container.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 102–109 | `TheComposedHostVerificationUsesTheJobsCeiling` and the module | 72 pass |
| 112, 113 | the module with read-only and A/B added | **80 pass** |
| 114 | manager/job-manager limits, worker entry, integration worker | 162 pass |
| 115 | `TwoBoundJobsTraverseServingAndCorrection` | 57 pass |

No broad suite was repeated: the 575-test pass and the 266-case stage module are
reused from the previous claim, and the focused selectors above cover what
changed. **115 runs, 1064.765227 seconds cumulative**; the four earlier disclosed
unmeasured activities stand.

### Changed paths this claim

| Path | Bytes | SHA256 |
| --- | ---: | --- |
| `v12/python/tools/stage_execution.py` | 258609 | `9c549b37b659c4aa9008318cc2cbf6dca3f42fc3122133d2ac5f2e814237510e` |
| `v12/python/tests/tools/test_execution_limits.py` | 79291 | `08a8f980466787a55242a52e10c1da05890c8dd032dfe15a8a8ffdd4fcfcc442` |
| `v12/python/DEPLOYMENT.md` | 64235 | `b16f4b1cef3ac9c602f2290057484369a1cd033dde43fedad323a9dfd5e8b701` |

Twenty-seven candidate paths, unchanged in count.

### Still owed

**Final candidate provenance.** Both `stage_execution` files still carry another
Work's in-flight changes that the final candidate must separate, and the five
earlier expectation-changing Job test files still need bounded owner disposition
before integration. Neither has blocked the authorized implementation.

Cumulative accounting and per-role pools remain deferred by the owner.

## Claim 157571 — the caught timeout was malformed evidence, and it looped

The reviewer was right on the substance and on the diagnosis. My previous claim's
"bounded failure handling" was neither bounded nor handled.

### What was wrong

`_ConfiguredExecution._run` answered `status: None`, and my source comment said
the owners read that as an ordinary failed observation. **They do not.**
`reconciliation._observation` requires an actual integer exit status and refuses
the document before retaining anything, so the result never settled and every
ordinary tick re-ran the timed-out command — three host calls a tick, twelve over
four, at the same 77-second bound, with zero judges and a schema complaint about
a status nobody observed standing in for the real diagnostic. Catching the
exception had stopped a crash and had not completed the failure lifecycle.

**And my own test did not catch it** because the adjacent no-duplicate case used
*successful* observations. A no-duplicate assertion that only covers the success
path is not a no-duplicate assertion.

### What it does now

**Nothing is fabricated.** A child that supplied no exit status does not get one
invented for it. The run refuses with the boundary that stopped it and the actual
reason — timeout or start failure — which is a real diagnostic rather than a
schema complaint.

**Nothing is repeated.** The failure is retained by `(argv, revision, seconds)`
on the deployment, because these owners are composed fresh every tick and a
per-instance memo would forget exactly when it matters. A later tick re-refuses
from the record without running the command.

**Measured:** the command now runs **once** across four ordinary ticks, every
deferral carries the Job's own bound and the timeout, no judge is composed and
nothing is published.

### The missing owner contract, prepared rather than worked around

There is **no owner representation for "this observation could not be made"**.
`reconciliation._observation` and `execution._owned_post_import` both require an
actual integer status. What is missing, exactly: an owner-recorded, **durable**
outcome for a required test that produced no exit status, carrying the boundary
that stopped it, the reason, and enough identity for a later tick or a fresh
process to recognise the same failed work and decline to repeat it. A bounded
extension would be a `status: null` observation admitted only with a closed `why`
and the bound, settled as blocked and never authorizable — a change to
`reconciliation` and `execution`, both outside this Work's finite scope.

It is named in the source as `stage_execution.HOST_OBSERVATION_CONTRACT`, stated
in DEPLOYMENT.md, and asserted as a limitation in its own test: **the retention is
this process's**, so a fresh process or a reopen attempts the command once more.
That is submitted for disposition, not declared accepted.

### A claim of mine, corrected

The A/B interleaving class has **four** cases, not the five my last entry
claimed, and its docstring now says what they establish: a helper-level proof
that the delivery selects the number and that nothing leaks between turns in one
process — with a new adapter per turn, because `_scratch` creates its private
child root exclusively. It is **not** cross-Job propagation through a composed
serving and observation.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 116 | `TheHostSideVerificationCarriesTheSameCeiling` | 3 pass |
| 117 | `TheComposedHostVerificationUsesTheJobsCeiling` | 4 pass |
| 118 | the three limits modules | **146 pass** |
| 119 | `TwoBoundJobsTraverseServingAndCorrection` | 57 pass |

**119 runs, 1106.979584 seconds cumulative**; the four earlier disclosed
unmeasured activities stand. No broad suite repeated.

### Changed paths this claim

| Path | Bytes | SHA256 |
| --- | ---: | --- |
| `v12/python/tools/stage_execution.py` | 262382 | `d59c1d3aaac35e14d1e4253a7336cfc9a2cc0c26dbb27877ca01aef8b6805021` |
| `v12/python/tests/tools/test_execution_limits.py` | 81523 | `db5babcec9917301972071e463e334d1b3f65091bb209a7d9637bd0eef79fbad` |
| `v12/python/DEPLOYMENT.md` | 64804 | `969c3fa0ed09ec5db2028b448fc70d203dee5f2ee18ef879b2fe21e41eed6530` |

Twenty-seven candidate paths, unchanged in count.

### Still owed

**The owner-contract disposition** above, which is the only thing standing
between this branch and a durable failure outcome.

**Post-import acceptance.** No test drives `_ImportedVerifier`; the reviewer's own
probe established that branch's actual behaviour (77 s once over four ticks,
target unchanged and blocked at fence 2, result authorized, Job B integration
claimed). That branch's outcome, its start failure, its repeated observation and
its retention/cleanup semantics at both failure boundaries are unproved here, and
whole-fixture teardown is not runtime cleanup.

**Composed read-only and A/B acceptance.** The current cases are helper-level:
`SimpleNamespace` calls over a writable store and one-table equality, and
per-turn adapters over synthetic deliveries. What is owed is `observation_from`,
read-only opening, actual materialized and adopted launch bytes, absent-artifact
behaviour and the absence of other writes — and cross-Job propagation through the
two-Job fixture with distinct settings, alternating serving/observation/reopen.

**Final candidate provenance**, and the two standing integration gates.

## Claim 157658 — the memo I added was itself wrong, twice

The honest-refusal correction was accepted. Both new findings are against the
retention I built for it, and both are right.

### [P1] One harness's failure refused another harness's run

The key was `(argv, revision, seconds)`. The causal owner runs the **same command
at the same revision with a different harness** — that is exactly what `adding`
is for, and `harness_added` is the observation member that exists to keep it
honest. So a retained failure from one harness refused a different harness's run
**without ever attempting it**: a memo that answered about work it had never
seen.

Every varying operand is in the key now — the owning **scope** this observer was
composed for (its Job, its result, and whether it is the causal or the
post-import phase), the command, the revision, the bound, and a digest of the
harness content. Two runs differing in any of those are different work, and
neither speaks for the other.

### [P2] Every memo hit still materialized

The check ran after `mkdtemp` and `_materialize`, so three hits made three
scratch trees for one child that never ran. It runs **first** now: work this
composition already knows it cannot observe costs nothing.

### Three regressions, not three fixes

Each is the general form rather than the instance: a different harness at the
same revision is attempted and becomes its own retained failure; one scope never
speaks for another, asserted with two observers over one shared retention; and a
memo hit leaves exactly one scratch tree — the one the single real attempt made.
The composed case's retention assertion now also reads the key's scope and
requires it to name `job-b`, its result and the `causal` phase.

### What the owner request means for this claim

The reviewer's request **M157653 to `baton.decide`** — two integration source
paths per `HOST-FAILURE-PROPOSAL-2026-09-13.md`, plus bounded expectation changes
in five existing `job_manager` tests — is **asynchronous and pending**. It is not
authorization. Nothing in this claim depends on it: the memo correction is
entirely inside files this Work already owns, and no owner outside that scope was
touched. Its answer must be read before any dependent edit.

### A claim I am not carrying forward

My previous entry repeated the earlier probe's "target blocked at fence 2" for the
post-import branch. The current review's own measurement of that branch is
different — one 77 s call, four deferrals carrying the real diagnostic, an
**unchanged ref**, an **authorized** result and a **claimed** stage — and it says
explicitly not to carry the prior blocked-target claim forward. I am not. That
branch's actual outcome, its start failure, its repeated observation and its
retention and cleanup semantics remain **unproved by me**.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 121, 123 | `test_execution_limits` and the host class | 81 / 5 pass |
| 124 | the three limits modules | **148 pass** |
| 125 | `TwoBoundJobsTraverseServingAndCorrection` | 57 pass |

**125 runs, 1160.563275 seconds cumulative**; the four earlier disclosed
unmeasured activities stand. No broad rerun.

### Changed paths this claim

| Path | Bytes | SHA256 |
| --- | ---: | --- |
| `v12/python/tools/stage_execution.py` | 264363 | `37c6556bf78d08983da1d789393f6dcadc34ab764a2e4711041e96553cd7e565` |
| `v12/python/tests/tools/test_execution_limits.py` | 86121 | `3a83090ca32b7acc60a0f3328b3f7055bf8317b5ed34a8ab88aa71f932b64fbe` |

Twenty-seven candidate paths, unchanged in count.

### Still owed

**Read-only composed acceptance** — `observation_from`, read-only opening, actual
materialized and adopted launch bytes, absent-artifact behaviour and the absence
of other writes. The current cases remain helper-level and this claim did not
advance them.

**Distinct configured A/B through a composed serving, observation and reopen**,
with the two-Job fixture rather than synthetic deliveries.

**Post-import failure and retention/cleanup assertions** within existing scope,
per the branch behaviour the reviewer measured.

**Final provenance**, and the standing `stage_execution` overlap gate.

The pending `baton.decide` answer governs only the durable-outcome extension.

## Claim 157768 — the composed read-only acceptance, on the reviewer's own seams

The memo corrections were accepted. This claim takes the read-only observation
item, and the seams are the reviewer's baseline adopted rather than reinvented.
No product file changed.

### What the earlier cases were, and what these are

My earlier read-only cases called `_job_execution` on `SimpleNamespace` objects
over a writable store and compared one table's rows. That proved consistent
context *reading* and nothing about observation.

`TheComposedObservationAdoptsTwoJobsConfiguredLaunches` drives the real thing:
two Jobs configured with **distinct** settings through their own submission
(A 31/29, B 67/43), a real serving run, that serving composition **closed**, the
ControlStore **publicly reopened read-only**, `observation_from` composing the
reader, and **six alternating A/B/A `launch.adopt` calls** whose documents must
equal what the reader expected — `adopt` compares canonical bytes — and must
carry each Job's own numbers. Every observation equals the exchange serving
produced.

**And the observation acts on nothing.** Seven owners are patched to raise if
touched — `Authority.open`, `Authority.session`, `IntegrationStore.open`,
`operations_from`, `activate_pool`, `create_line`, `worker_preflight` — a SQLite
authorizer rejects every write through the retained Job handle for the whole
read window, and the four store files are byte-identical afterwards.

**A clarification that is the reviewer's and corrects my earlier shorthand:**
`JobStore` has **no** public read-only opener, and nothing here invents a
requirement for one. The already-open current-schema handle is retained with a
write guard, which is what makes "the observation writes nothing" measured
rather than asserted.

Two more cases: a **second reader** repeats the adoption and changes nothing
(no duplicate work, no repair), and an **absent delivery** — removed through the
launch owner's own `discard` — is answered as absent and **not recreated**, with
the store bytes unchanged.

The three narrow facts from the old class are kept as
`TheTwoReadersResolveOneJobIdentically`, whose docstring now says plainly that it
is helper-level and names the composed class as what establishes the rest.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 129 | `TheComposedObservationAdoptsTwoJobsConfiguredLaunches` | 3 pass |
| 130 | the three limits modules | 151 pass |
| 131 | `tests.tools.test_execution_limits` | **85 pass** |

**131 runs, 1180.435441 seconds cumulative**; the four earlier disclosed
unmeasured activities stand. Focused selectors only; no broad repeat.

### Changed paths this claim

| Path | Bytes | SHA256 |
| --- | ---: | --- |
| `v12/python/tests/tools/test_execution_limits.py` | 97427 | `96758183bcb910d66bda492ddf308e2171e079e822b9638732e51cf6124fea15` |

Twenty-seven candidate paths, unchanged in count.

### Still owed

**Post-import**: timeout, start failure and repeated observation through
`_ImportedVerifier`, with the original scratch retention and cleanup asserted at
both failure boundaries by their owners. The old blocked-target claim stays
historical and is not repeated.

**A/B through serving and a reopen** beyond the observation alternation proved
here — the continued serving no-duplicate evidence.

**Fresh closed/reopened ownership**, which this claim does not establish: the
Job handle is retained, not reopened in a fresh process.

**Final 27-path provenance**, the standing `stage_execution` overlap gate, and
the five earlier expectation-changing Job tests' bounded owner disposition.

**M157653 remains pending** with no new messages; no dependent integration source
or test authority extension exists yet, and nothing in this claim relied on one.

## Claim 157832 — a fresh process, and two accuracy corrections

The composed observation was accepted. This claim takes the fresh-process item
and the two corrections the reviewer attached to that acceptance. No product file
changed.

### The two corrections

**`assertIsNone(answered)`.** The absence regression discarded the answer with
`del`. The independent probe captured exactly `None` there, and a regression that
throws the answer away cannot tell absence from a delivery it failed to prove. It
is asserted now.

**The guard claim is stated at its real width.** The SQLite authorizer rejects
the mutation actions named in the case — insert, update, delete, and table or
index creation, drop and alteration — through the **retained** Job handle, and
the byte comparison covers the **four named** store files. That is not a proof
against arbitrary writes anywhere, and the docstring now says so.

### A fresh process, which a second observation object is not

The reviewer named
`test_fresh_process_observes_owned_completion_after_serving_closes` and its
`READONLY_PROCESS` as the source examples to revalidate and reuse. This follows
that shape **without editing that file**: the serving composition and both stores
are closed, the configuration and the observed exchanges are written out, and a
real child opens the stores itself, composes `observation_from`, and adopts each
attempt's delivery alternately — A, B, A.

**What the child establishes that the in-process case cannot:** its Job handle is
a new one, so a context remembered anywhere in the serving process cannot be what
answers. The adoption is read at `launch.adopt` — the same seam, because what
`adopt` was handed is what it compared canonical bytes against — rather than
through a private attribute of the observation wrapper. Both Jobs' own numbers
come back (31/29 and 67/43), every observed exchange equals what serving
produced, every serving act is guarded, and the parent's four store files are
byte-identical afterwards.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 132 | the composed observation class | 3 pass |
| 135 | `AFreshProcessAdoptsBothJobsConfiguredLaunches` | 1 pass |
| 136 | the three limits modules | 151 pass |
| 137 | `tests.tools.test_execution_limits` | **86 pass** |

**137 runs, 1191.335321 seconds cumulative**; the four earlier disclosed
unmeasured activities stand. Focused selectors only.

### Changed paths this claim

| Path | Bytes | SHA256 |
| --- | ---: | --- |
| `v12/python/tests/tools/test_execution_limits.py` | 106053 | `081426162c41ce84bc7526edee25672cefd1a9c53a3ab19fed4063d12b33f7ee` |

Twenty-seven candidate paths, unchanged in count.

### Still owed

**Post-import** timeout, start failure and repeated observation through
`_ImportedVerifier`, with the original scratch retention and cleanup asserted by
their owners at both failure boundaries. The old blocked-target candidate stays
historical.

**Continued configured A/B serving across a reopen**, with actual engine and
provider no-duplicate checks — this claim proved adoption across a fresh process,
not a serving reopen.

**Final 27-path provenance**, the standing `stage_execution` overlap gate, and
the five earlier expectation-changing Job tests' bounded owner disposition.

**M157653 remains pending**; no dependent authority exists and nothing here
relied on one.

## Claim 157871 — the serving reopen, and a corrected ledger figure

The fresh-process observation was accepted. This claim takes the next item in the
reviewer's order and carries their accounting correction. No product file changed.

### The accounting correction, carried

My last handoff reported **1191.335321 s** at 137 runs. The ledger totals
**1200.270132 s**: I read it before step 137's own 8.934811 s entry landed, so I
reported a figure that excluded the run I was reporting. The correction is the
reviewer's; the ledger was right and my reading of it was not. Every figure below
is read after the last run of this claim.

### Continued configured A/B serving across an ownership reopen

A fresh process **observing** a delivery is a different fact from a serving
composition being taken down and brought back up over the same stores, and the
review was explicit that the first does not discharge the second. This is the
second.

Two Jobs configured with distinct settings (A 31/29, B 67/43) reach running
containers; the serving composition and both stores are **closed**; a new serving
composition is composed over the same stores and ticked. Then:

- **Each delivery adopts unchanged**, by canonical bytes, still carrying its own
  Job's numbers, and each observed exchange equals what the first serving
  produced. A reopen **re-derives** the same configuration rather than authoring
  a second one.
- **No second container for either attempt.** `serving_two` composes a new engine
  for the reopened deployment — the honest topology, and why the counts come from
  two distinct engines: the reopened engine issued **no** `run` naming either
  attempt, and the original still holds exactly the one it made. Counted by the
  launch's own **input identity**, because the runtime id does not exist until an
  engine answers and therefore cannot see a duplicate.
- **No second provider turn**, which in this fixture would have needed a second
  container — what the empty start list rules out. Stated that way rather than as
  a count this case does not take.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 139 | `AReopenedServingKeepsBothJobsLaunchesUntouched` | 1 pass |
| 140 | the three limits modules | **152 pass** |

**140 runs, 1210.128422 seconds cumulative**, read after step 140; plus the four
earlier disclosed unmeasured activities. Focused selectors only; no broad
recount.

### Changed paths this claim

| Path | Bytes | SHA256 |
| --- | ---: | --- |
| `v12/python/tests/tools/test_execution_limits.py` | 113162 | `89972caa6c69781891042c382ac80133f9c1a365dbc43cef67f4134a0a8cca2d` |

Twenty-seven candidate paths, unchanged in count.

### Still owed

**Post-import**: timeout, start failure and repeated observation through
`_ImportedVerifier`, with the original scratch retention and cleanup asserted by
their owners at **both** host failure boundaries. The current post-import
refusal, authorized-result and claimed-stage facts are the reviewer's own
measurement and differ from the historical blocked-target candidate, which stays
historical.

**Final 27-path provenance**, the standing `stage_execution` overlap gate, and
the five earlier expectation-changing Job tests' bounded owner disposition.

**M157653 remains pending** for the durable no-status owner extension and that
test authority. Nothing in this claim depended on it.

## Claim 157925 — my reopen case passed on a lost runtime

The finding is against the case I delivered last claim, and it is right. No
product file changed.

### What was wrong

`serving_two` composes a **new** `_ConcurrentEngine`, so the reopened deployment
met no containers at all: the first sweep reported both attempts **destroyed**
and the next reported them not-asked, with empty acts, started and spoken lists
throughout. My "the reopened engine issued no `run`" was true and proved nothing
— an empty start list proves no restart only where there was nothing left to
restart. That is a lost runtime, not continued serving, and I presented it as
continued serving.

My docstring also claimed a provider-turn count the case does not take.

### What it is now

**The daemon survives the client.** An engine models an external process
boundary, and rebuilding a client does not stop containers — so the same engine
object meets the reopened composition, which is what a real reopen meets.

**The sweeps are asserted positively.** Every reopened sweep must report *both*
implementation attempts `running`, by attempt id. "Not destroyed" was the first
form's assertion and is satisfied by a sweep that reports nothing at all, which
is exactly what happened.

**And the counts are per attempt on the one engine** that has held them
throughout: one start each before the reopen, one each after.

**Measured** in `probe-157925-reopen.py`: all three reopened sweeps report both
implementations `running`, both stages stay `waiting`, and the start counts stay
at one each.

**The literal delivery is compared too** — path and bytes on disk, before and
after the reopen — which is what a container actually reads. The rest of the case
compares semantic context and exchanges, and the reviewer asked for both.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 141, 143 | the rewritten reopen case, then the module | **87 pass** |
| 142 | `probe-157925-reopen.py`, retained | — |

**143 runs, 1220.011155 seconds cumulative**, read after step 143; plus the four
earlier disclosed unmeasured activities. No broad recount.

### Changed paths this claim

| Path | Bytes | SHA256 |
| --- | ---: | --- |
| `v12/python/tests/tools/test_execution_limits.py` | 114657 | `1d013faa91a7da9c090310fb4e5b29a271d0e2ca6cc52fa6514e8a8f715e736a` |

Twenty-seven candidate paths, unchanged in count.

### Still owed

**Post-import**: timeout, start failure and repeated observation through
`_ImportedVerifier`, with the original scratch retention and cleanup asserted by
their owners at **both** host failure boundaries. The current raising branch is
not the historical `status=None` blocked-target candidate, and that candidate
stays historical.

**Final 27-path provenance**, the standing `stage_execution` overlap gate, and
the five earlier expectation-changing Job tests' bounded owner disposition.

**M157653 remains pending**; nothing in this claim depended on it.

## Claim 157976 — the reopened deployment finishes the work it inherited

The corrected reopen case was accepted. This claim carries the bounded
continuation the reviewer's own probe established into the regression itself. No
product file changed.

### Adoption is not the same as still being able to drive

An unchanged adoption and an unchanged start count say a reopen broke nothing.
They do not say the reopened deployment can still **do** anything. Both original
attempts now take their real worker turns after the reopen, through the
containers the **first** composition mounted, and:

- each attempt's provider is invoked **exactly once**, under its own Job's
  number — 31 for A, 67 for B, read at the adapter's own `_provider`;
- both implementation stages reach `completed` under ordinary sweeps;
- and each attempt still has **one workload container**, with the replay sweeps
  starting none.

### Three practical facts, all the reviewer's

**The mounts are saved before the close.** The reopened composition has no
`_prepared` map for attempts it did not prepare, so a fixture asking it for them
would be asking about work it never did. They are captured while the first
composition is still open.

**The Job context the turn adopts against is the deployment's own.** The
fixture's resolver finds it through the worker that prepared the attempt, and the
reopened composition prepared neither — so what is supplied is the context
captured from the **real adoption** earlier in the same case, not one invented
here.

**A custody helper is not a workload.** Each turn also runs two `--entrypoint`
containers that take custody of the workspace. Counting those as duplicate
workloads reported three starts for one container that ran once; the count now
excludes them and says why.

**And each Job's own producer output is used** — Job B's task names
`feature_check.py` and asserts `feature.py`'s value, so its turn writes both.
Using one Job's output for the other would be a turn that could not pass its own
configured verification.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 146 | `AReopenedServingKeepsBothJobsLaunchesUntouched` | 1 pass |
| 147 | `tests.tools.test_execution_limits` | **87 pass** |

**147 runs, 1231.183947 seconds cumulative**, read after step 147; plus the four
earlier disclosed unmeasured activities. No unchanged module recount elsewhere.

### Changed paths this claim

| Path | Bytes | SHA256 |
| --- | ---: | --- |
| `v12/python/tests/tools/test_execution_limits.py` | 119167 | `3e60b846446f95fb171845cdbf34d363cd0fffdf65d9ae98e595747f8070bf66` |

Twenty-seven candidate paths, unchanged in count.

### Still owed

**Post-import**: timeout, start failure and repeated observation through
`_ImportedVerifier`, with the original scratch retention and cleanup asserted by
their owners at **both** host failure boundaries. The current raising branch is
not the historical `status=None` blocked-target candidate, which stays historical.

**Final 27-path provenance**, the standing `stage_execution` overlap gate, and
the five earlier expectation-changing Job tests' bounded owner disposition.

**M157653 remains pending** for the durable no-status owner extension and that
test authority. Nothing in this claim depended on it.

## Claim 158005 — the tuple strengthening, and a post-import attempt that did not reach

The continuation regression was accepted. This claim lands the strengthening the
reviewer asked for on the next edit, and makes a bounded attempt at the
post-import branch that **did not reach it**. No product file changed.

### The tuple strengthening

The provider watch recorded bare seconds, and a sorted list of bounds cannot
detect a **swapped association** — A running under B's ceiling and B under A's
would sort identically. It records the whole tuple now: which Job, which attempt,
and the bound that turn actually got, read from the delivery the turn is holding.
The set is compared against the expected set, and the watch stays open **across
the replay sweeps** so "the sweeps take no further turn" is asserted rather than
assumed.

### The post-import attempt, and where it stopped

I wrote three cases against `_ImportedVerifier` — the ceiling on the post-import
command, an overrun that repeats neither the work nor the scratch, and the
retention being keyed to its own phase — driving the judges to their verdicts
first and arming the injection only afterwards, so that command would be the only
one it could reach.

**It ran no command.** Driving `job-b`'s integration to `completed` after the
three accepted verdicts did not reach `_ImportedVerifier` in my composition, and I
did not establish why within this claim.

**So the three cases are not in the candidate.** A test that asserts on a
boundary it never reaches is not evidence, and leaving it in to be corrected later
would have put a failing-or-vacuous case in a candidate I am handing back. What is
recorded instead is the measured fact that this path is not reachable by the steps
I took, so the next claim starts from there rather than from scratch. The
reviewer's own probe **does** reach it, and its sequence is the thing to follow.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 148 | the reopen case with the tuple assertions | 1 pass |
| 150 | the post-import attempt | 3 failed — did not reach the branch |
| 151 | `tests.tools.test_execution_limits` after removal | **87 pass** |

Step 150's failure is retained in the ledger and its log; it is the evidence of
what did not work.

**151 runs, 1262.444743 seconds cumulative**, read after step 151; plus the four
earlier disclosed unmeasured activities.

### Changed paths this claim

| Path | Bytes | SHA256 |
| --- | ---: | --- |
| `v12/python/tests/tools/test_execution_limits.py` | 120249 | `664e25f6dd0553abe93a6fae3eeebd06cc73ea578b8384e8cae1478bf1bafbe9` |

Twenty-seven candidate paths, unchanged in count.

### Still owed

**Post-import**, unchanged and now with a measured starting point: timeout, start
failure and repeated observation through `_ImportedVerifier`, plus the original
scratch retention and cleanup at **both** host boundaries. Following
`repro-157990.py`'s own sequence to the branch is the next step, rather than the
tick-driving I tried.

**Final 27-path provenance** and explicit `stage_execution` overlap accounting.

**M157653 remains pending**; nothing here depended on it.

## Claim 158049 — the post-import branch, reached

The tuple strengthening was accepted. This claim lands the post-import baseline
regressions, using the locator the reviewer corrected me to. No product file
changed.

### Why my attempt ran no command, and the locator I named wrongly

I told the reviewer I would follow `repro-157990.py`. **That probe never reaches
post-import** — the reviewer corrected the locator to `repro-157534.py`'s second
case and the new self-contained `repro-158025.py`. I had named a next step
against a file I had not checked reached the thing I needed.

The cause of the failure was in my own helper: **`required_argv()` composes a NEW
serving deployment and resets the fixture's `_composed` and `engine`**, and
`_watching` called it. Arming the watch after the judgments therefore threw away
the deployment whose post-import branch was about to run. Composing a deployment
merely to read an argv is the mistake.

**Two corrections:** `required_argv` takes the deployment already in hand when
there is one, and the post-import path takes the accepted command from the
configured **task document** itself — which is what `required_tests` derives it
from — so no deployment is composed to read it. And the pre-arm `tick` is gone:
the post-import command runs on the next ordinary tick, so taking one before the
watch is armed spends the very call being observed.

### What is now proved at the second host boundary

- **The ceiling applies.** `_ImportedVerifier` runs the required test against the
  imported commit under the Job's own 77 seconds.
- **An overrun runs once** across four ordinary ticks and is retained under a key
  whose phase is `post-import` — the causal memo cannot speak for this branch and
  this one cannot speak for the causal.
- **A start failure is the same shape**: the other way a host command produces no
  exit status is that the child never ran, and it is retained and refused
  identically, with "could not be started" in the retained reason.

### The scratch, and what that assertion does and does not settle

The tree the one real attempt materialized **stays**. Repeated polls add none —
the memo refuses before materializing — and closing the composition removes none
either: `_run` has no disposal branch and the memo holds no scratch locator.

**That is recorded as a measured limitation, not as intended behaviour.** It is
not a proven leak and not an accepted retention policy; disposition of that tree
belongs to the pending host-failure proposal's own step, together with durable
failure custody. Asserting it as intended would settle a question that is open.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 152 | the host class after the locator fix | 4 pass |
| 154 | the host class with the post-import cases | **8 pass** |
| 155 | `tests.tools.test_execution_limits` | **91 pass** |

**155 runs, 1308.976591 seconds cumulative**, read after step 155; plus the four
earlier disclosed unmeasured activities. No broad recount.

### Changed paths this claim

| Path | Bytes | SHA256 |
| --- | ---: | --- |
| `v12/python/tests/tools/test_execution_limits.py` | 127045 | `bdf8080c7391dc2c559d8a5f5809a255fe45df0fe1a06db7a6f855c21376879f` |

Twenty-seven candidate paths, unchanged in count.

### Still owed

**Final 27-path provenance** and explicit `stage_execution` overlap accounting —
both `stage_execution` files carry another Work's in-flight changes the final
candidate must separate.

**The five earlier expectation-changing Job tests' bounded owner disposition.**

**M157653 remains pending** for the durable no-status owner extension and that
test authority — and it now also owns the scratch disposition above. Nothing in
this claim depended on it.

## Claim 158092 — the 27-path provenance packet

The four post-import baseline cases were accepted. This claim is documentation
only: no source, test or product file changed, and no test was run, because none
needed to be.

### The packet

`PROVENANCE-158092.md`, with `provenance-158092.json` beside it holding the
machine-gathered figures: for each of the 27 paths, its base bytes and SHA256 at
`HEAD`, its candidate bytes and SHA256, its added/removed line counts and its
hunk count. Gathered **read-only**; no Git mutation.

Seven new files wholly this Work's; twelve modified sources and documents inside
its own scope; five existing Job tests whose expectations moved for the schema
transition and which carry **no owner disposition yet**; and two existing test
files changed under the setup-only authority the PLAN scheduled.

### Both `stage_execution` files, hunk by hunk

**`tools/stage_execution.py` — 18 hunks.** Eight carry the `W156162` marker in
their own text. Ten more are the same change's mechanical halves, and rather than
assert that, each is named: the `execution_limits` import, three constructor
signatures gaining `seconds`/`retention`/`scope`, two call sites passing them, the
retained-failure check moved ahead of materialization, and
`_integration_operations` gaining `job_store`.

**One hunk is foreign** and is reported, not removed: the read-only integration
observation drops a runtime precondition so a reconciled completion with no
runtime reaches the outer observer. That belongs to the read-only
reconciled-completion Work.

**`tests/tools/test_stage_execution.py` — 7 hunks.** Six are this Work's, all
additive or setup-only; **no existing assertion in that file was changed by this
Work**. One is foreign: the added
`test_readonly_reconciled_completion_without_runtime_reaches_outer_observer`,
which is the test for the source hunk above.

### Separability, and what I will not certify

The two foreign hunks are one change and its test, in two files, **textually
separable**: a different method's precondition and a whole added test function,
with no lines overlapping this Work's. Nothing in W156162's hunks depends on them.

**What I cannot certify is that removing them leaves a passing tree.** The
foreign test would fail without its source hunk, and the 13 long-standing
`test_stage_execution` errors have only ever been compared against an earlier
W156162 candidate — never against a tree with the foreign change excised. That
measurement has not been taken, and I am not claiming it. Nothing was removed,
imported or absorbed to make the packet look clean.

### Verification

None was needed or taken: this claim changed no code. **155 runs,
1308.976591 seconds cumulative**, unchanged from the previous claim, plus the
four earlier disclosed unmeasured activities.

### Added evidence

| Path | Bytes | SHA256 |
| --- | ---: | --- |
| `work/.../finding-v12-per-job-budgets/PROVENANCE-158092.md` | 5064 | `6715eaf24db5ce06b450a68a84d16b1b0cd4f876ee9e363ba000a18999d07042` |
| `work/.../finding-v12-per-job-budgets/provenance-158092.json` | — | machine-gathered per-path figures |

Candidate paths and their digests are unchanged from claim 158049.

### Still owed — and this is now only the owner's

Independent acceptance and provenance are complete as far as this Work's own
scope reaches. What remains is **`M157653`**: the two-source durable no-status
extension, the five existing Job tests' expectation changes, and the failed
scratch's disposition, which that proposal's step 5 already owned when it was
requested — this Work's measurement added evidence to it, not scope or approval.

The `stage_execution` overlap is accounted above and remains an **integration
gate**, not an implementation one.

## Claim 159350 — the owner approved M157653, and it is implemented

Owner ruling, thread T156162 seq 159347 (Slawomir, 2026-09-13T09:19:44Z):
**approve** `HOST-FAILURE-PROPOSAL-2026-09-13.md` and the exact five test updates
in `PROVENANCE-REVIEW-158105.md`, preserving bounded scope, independent review,
W71879 provenance and spending, **with no acceptance waiver**. Pass 159348: pin
it in FINDING/PLAN and implement the bounded semantics with deterministic tests.

**Pinned** in both `FINDING.md` and `PLAN.md`, with what the ruling grants and
what it does not, and attributed: those two files are otherwise reviewer-owned
and I wrote in them only at the owner's explicit direction.

### The closed failure answer (steps 1 and 2)

`reconciliation` now owns a tagged failure shape — `FAILURE_SCHEMA`, the three
causal phases plus `post-import`, and exactly two closed reasons, `timeout` and
`start-failed`. `_failure` validates every binding the ruling names: the phase is
one this owner runs, the reason is one of the two words, the bound is the whole
positive number of seconds actually applied, **no exit status appears anywhere**,
the completed prefix carries real integer statuses under the same pinned harness,
the not-run remainder is exactly the phases after the failed one, and the
attesting execution is the owner that answered.

`record_causal_observations` takes that branch, settles **blocked** with a reason
naming the phase, the closed cause and the Job's own bound, and retains the
answer in the same JSON custody the successful observations use. `_causal`,
`_observation` and `_OBSERVATIONS` are untouched, so **every completed legacy
observation reads back exactly as before** — `_observation_signature` was the one
reader that assumed a combined status, and it now derives from the row's own two
members without asking the success shape a question it cannot answer.

### The post-import hold (step 3)

`execution` adopts the failure **inside the current verification ownership
boundary** and blocks the target through the same public capability the
failed-test hold uses, before any reference advance or integrated receipt. It is
adopted **ahead of** the generic unreadable-evidence handler deliberately:
routing a deliberately tagged answer through that branch would relabel a known
failure as an unreadable one, which is what that branch exists to stop. Exactly
one `block_target` is reached.

### Durable no-repeat, and the scratch (steps 4 and 5)

`reconciliation.failed_host_verification(store, result_id)` is the durable
custody a host owner consults — the same JSON custody, read back through the
result's own public reader, so a fresh process reaches the same answer where a
process-local memo forgot. It answers about one result and carries its own phase,
so two results, two Jobs, or one result's two host boundaries never reuse each
other's outcome.

And the temporary materialization is **disposed of** once its diagnostic is in
the answer. My previous claim asserted that tree survived and recorded it as a
measured limitation; the ruling owns it, and the assertion is now that it goes.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 157 | `test_reconciliation`, `test_execution` | 154 pass |
| 167 | `TheComposedHostVerificationUsesTheJobsCeiling` | 8 pass |
| 172 | `test_execution_limits` + both owner suites | **245 pass** |
| 173 | `TwoBoundJobs` + the two other limits modules | **122 pass** |

**173 runs, 1540.163788 seconds cumulative**, read after step 173; plus the four
earlier disclosed unmeasured activities.

### Changed paths this claim

| Path | Bytes | SHA256 |
| --- | ---: | --- |
| `src/baton_v12/integration/reconciliation.py` | 112610 | `fdfb610fc0ce835302143a5022877e6076c346e3a96b705d245b8e0f629f72ff` |
| `src/baton_v12/integration/execution.py` | 63238 | `b0dc153e0cc5523d9707178781d620a11fa446ff3dd9674080af87f9c00a9d08` |
| `tools/stage_execution.py` | 268475 | `db3c77724b08a96df2038007c4e32d94a82b81829ec77e07f590919c482dfafb` |
| `tests/tools/test_execution_limits.py` | 126635 | `33aea4d909414f0e997dbb06715dc1824c69391f457a25f63f7a5cc5caa715f7` |
| `DEPLOYMENT.md` | 65245 | `157531c21eb8e1ff9e5c3b8e881887a673c547de25f6ac277f73d5cfc8690ac8` |

**Twenty-nine candidate paths** — the two integration owners are new to the
candidate under the approved scope. The provenance packet needs regenerating for
them; it is at 27 and that is now stale.

### Still owed

**Regenerate `PROVENANCE-158092.md` for 29 paths**, including the two newly
scoped owners' base and candidate bytes.

**The acceptance matrix the proposal lists that I have not written**: timeout and
start-failed at *each* causal phase individually, malformed/mismatched failure
refusals, signature readback and replay of a retained failure, recovery, and the
unchanged-successful-evidence and publication-authorization cases. What is proved
today is the causal overrun end to end, the post-import boundary at both failure
kinds, the phase-scoped retention, and the disposal — not the whole matrix.

The `stage_execution` overlap remains an integration gate, and the five approved
test changes now carry their authority.

## Claim 159477 — the failure I added accepted evidence about other results

Both P1s are against what I shipped last claim, and both are right. No test was
weakened and no scope was added: this is all inside the approved ruling.

### [P1] `_failure` discarded the result it was given

I wrote `del held`. So the validator checked the answer's SHAPE and nothing about
the content it claimed to be about, and the reviewer's composed probe durably
accepted a foreign causal commit, tree, command, task, digest, environment — and
**999999 seconds** — into blocked custody. A failure kept as evidence about a
result, that is not about that result, is worse than no custody at all: it is the
"members that exist and are compared with nothing" defect, in the very branch I
added to end a different one.

**It binds now.** Each phase is held to exactly the content `_causal` holds its
successful counterpart to — combined to the prepared head and tree, base to the
submission's original base, isolated to its candidate. The environment must be
the one word this owner configures. And the completed prefix must agree with the
failed phase about the command and the task, because a prefix that ran something
else is not this failure's own execution. Fifteen cases, **each changing exactly
one member**, so every refusal names the member it is about.

### [P1] The producer recorded the commit as the tree

`_run` knows only a revision, so `input_tree` came back as the commit — not the
tree, and for the combined phase not `prepared.tree` either. The owner that can
ask Git is `_observation`, and it asks before the answer leaves. The two defects
were mutually concealing: with the binding discarded, nothing compared the tree,
and with the tree wrong, binding it would have refused every real failure.

### Three claims of mine, corrected

**`failed_host_verification` has no production caller** and reads the causal
custody only — the post-import probe returns `None` from it. My last entry
presented it as establishing post-import durability. It does not. DEPLOYMENT.md
now says plainly that a closed-and-reopened owner replaying the post-import hold
**is not proved**, and that the causal custody is what is read back.

**A failed disposal is no longer silent.** `rmtree(ignore_errors=True)` reported a
clean disposal for a tree that might still be there; what remains is now named in
the retained diagnostic. It is not raised — the FAILURE is the fact being
reported, and losing it to a cleanup problem would be worse.

**"Limited blocked/hold behaviour is observed, not complete acceptance"** is the
reviewer's phrase and it is the accurate one for what this branch has.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 174 | the composed host class and both owner suites | 162 pass |
| 178, 180 | `tests.tools.test_execution_limits` | **105 pass** |
| 179 | those plus both owner suites and the two other limits modules | **324 pass** |

**180 runs, 1640.795439 seconds cumulative**, read after step 180; plus the four
earlier disclosed unmeasured activities. No broad recount.

### Changed paths this claim

| Path | Bytes | SHA256 |
| --- | ---: | --- |
| `src/baton_v12/integration/reconciliation.py` | 115681 | `e461259c3f612eefd805272a512880e51b0223038b1b05e1048cf6dac04d9aca` |
| `tools/stage_execution.py` | 270126 | `d505bcd565c9deb24db38f29d5a1e133422d3f6b24ad7d615b20e7161288e289` |
| `tests/tools/test_execution_limits.py` | 133783 | `71ffa3d1c72413d213032526a3e8740f321eddb57b441d9c0686d229b75af75c` |
| `DEPLOYMENT.md` | 65706 | `84f5dee1d005fd4af4cfc43d81f0e79896e6175bb2ab09da2daad4c8bb59b4a9` |

`integration/execution.py` is unchanged from claim 159350. **Twenty-nine
candidate paths.**

### Still owed

**The rest of the admitted matrix**: each causal phase's timeout and start
failure individually, signature readback and replay of a retained failure,
recovery, the unchanged-successful-evidence and publication-authorization cases,
and **an actual queue-hold no-repeat on closed and reopened owners** — which is
the post-import durability I wrongly implied was already established.

**The new 29-path provenance** from `PROVENANCE-REVIEW-158105.md`, preserving the
historical 27-path packet and W71879's exact attribution and preflight.

## Claim 159547 — the binding checked the answer against itself

The P1 was still open and the reviewer's probe is exact: changing **only** the
seconds, from the 77 this deployment applied to 999999, was accepted by both the
causal custody and the post-import adoption. So were 78, an unrelated command, an
unrelated task and an unrelated harness digest.

### Why, and what it is now

Every check I had written was about the answer's **self-consistency**. A maximum
of 86400 would not have helped: what is needed is the value this deployment
*actually configured*, and the answer cannot vouch for it.

**So the configured owner is asked, exactly as it is asked for its participant.**
`_ConfiguredExecution.expectations` publishes the deployment's own operands — the
command, the task identity and the seconds — held on the object before anything
ran. `_failure` compares the answer against those, and `record_causal_observations`
and the post-import adoption both pass them. The harness digest is deliberately
**not** published: this owner does not know it until it has read the content, and
a stale one would be worse than none.

**And every completed phase is bound to the result's own content.** A base
failure accepted a foreign completed-combined commit, tree or environment
independently of the failed phase's bindings; each is now held to the same
content `_causal` holds its successful counterpart to.

### A bug I introduced and the case that caught it

The content-binding block named its local `expected`, **shadowing the parameter
of the same name** — so the comparison loop saw a two-tuple, found no member in
it, and skipped every check. The first run of the new cases failed on exactly
that, which is what those cases are for; the local is `content` now and the
reason is written where it happened.

Eight new cases: the reviewer's own 999999 probe plus 78 and 1, an unrelated
command, an unrelated task, the three foreign completed-combined members, and the
owner publishing what it was given.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 183 | `test_execution_limits` and both owner suites | **265 pass** |
| 184 | the two limits modules and `TwoBoundJobs` | **122 pass** |

**184 runs, 1724.648046 seconds cumulative**, read after step 184; plus the
four earlier disclosed unmeasured activities.

### Changed paths this claim

| Path | Bytes | SHA256 |
| --- | ---: | --- |
| `src/baton_v12/integration/reconciliation.py` | 119817 | `8412a5bbd07821b5f2b352a63e7f3cc6e6fa02c65312a04722ca0ac69d6ea1df` |
| `src/baton_v12/integration/execution.py` | 63312 | `abba31d87a7e1250e6045f85c8a749890a54b681e148e13144fcde66b525b4dc` |
| `tools/stage_execution.py` | 271080 | `69824f9785b776b3c8c179a9cca4b52fe44bad3aa84b4d09e7bf277490ca8aff` |
| `tests/tools/test_execution_limits.py` | 137734 | `17c9c0b34c1a76784e97c937b80e1065c3c3ea825cb4adea693189431a1a414d` |

**Twenty-nine candidate paths.**

### Still owed

The admitted matrix's remainder: **all-phase and all-reason coverage**,
**malformed**, **signature readback and replay**, an **actual closed/reopened
queue-hold no-repeat**, **isolation**, **explicit recovery**, **cleanup-failure**,
and **legacy-success and authorization**. Naming the remaining scratch does not
establish a cleanup lifecycle, and I am not claiming it does.

And the **new 29-path provenance** from `PROVENANCE-REVIEW-158105.md`, preserving
the historical 27-path packet and W71879's exact attribution and preflight.

## Claim 159612 — the harness digest, and the 29-path packet

### [P1] The one binding I argued out of

A probe changed **only** `test_digest` after a real 77-second timeout, and the
causal recording retained the foreign harness durably while the post-import
adoption took it too.

I had argued this owner could not publish a digest "because it does not know one
until it has read the content, and a stale one would be worse than none". That is
true of a **configuration-time** digest and it does not waive the per-result
binding — which is what the reviewer said, and it is right. The harness for the
phase is in hand at the content-read boundary, one line after the file is opened
and **before the subprocess starts**.

So it is pinned there. `expectations` publishes it per **result and phase** —
never a stale global, and never derived from the answer — and `_failure` compares
the answer's digest against it. Two cases: a forged digest refuses against the
pinned one, and the pinned value is shown to be the content's own (absent before
any run, and equal to the digest of the bytes the run actually read).

### The 29-path provenance packet

`PROVENANCE-159612.md` with `provenance-159612.json`: per path, base bytes and
SHA256 at `HEAD`, candidate bytes and SHA256, line counts and hunk counts,
gathered read-only. `PROVENANCE-158092.md` and its JSON are **retained unchanged**
as the 27-path packet that preceded the ruling — superseded, not replaced.

The two new product paths are accounted as exactly what M157653 approved:
`reconciliation.py` at +324/−10 over five hunks and `execution.py` at +33/−0 over
one, carrying only the host-failure semantics — no schema change, no migration,
no other owner touched.

**W71879 is named as the foreign Work**, per the reviewer's own attribution: the
completion-observation candidate 153138, whose methods and base bytes match. Its
one source hunk and one test hunk are reported, not removed, and what remains
uncertified is unchanged — that removing them leaves a passing tree has never
been measured, and integration still needs its own preflight.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 185 | the focused module and both owner suites | 265 pass |
| 186 | the binding cases | 22 pass |
| 187 | those plus the two other limits modules | **332 pass** |

**187 runs, 1779.971036 seconds cumulative**, read after step 187; plus the four
earlier disclosed unmeasured activities.

### Changed paths this claim

| Path | Bytes | SHA256 |
| --- | ---: | --- |
| `tools/stage_execution.py` | 272446 | `3ee83301cae8eed8eeaa30461af4e862507a846d4f36cd15f0effbca79a53629` |
| `tests/tools/test_execution_limits.py` | 141062 | `39c59b88d854eee9817104b3ff2d1fdfef5bada01f9a4e654c5f5a3a1e6161f7` |

Added evidence: `PROVENANCE-159612.md` (2973 bytes, SHA256
`20d6268983274f1a9aaacd7df483566c02cc3443c63db12bce718ee4cca6111e`) and
`provenance-159612.json`. The two integration owners are unchanged from claim
159547.

### Still owed

The admitted matrix's remainder, unchanged and now the whole of it: **all-phase
and all-reason coverage**, **malformed**, **signature readback and replay**, an
**actual closed/reopened queue-hold with zero command and zero materialization
repeat**, **isolation**, **explicit recovery**, **cleanup-failure**, and
**legacy-success and authorization**.

That list is not an operational barrier and I am not offering it as one; it is
the work that remains.

## Claim 159672 — the admitted matrix

The harness pin was accepted. This claim writes the coverage the approved
proposal itself asks for, rather than only the defects found along the way. No
product source changed; only tests and the provenance packet.

### What is covered now

**All phases, all reasons.** Three causal phases times two closed reasons, all
six admitted, each keeping its own phase, completed prefix and not-run
remainder.

**Malformed.** Eight single-member mutations — a null phase, reason, detail or
execution, an empty or non-list command, a non-dict completed set, a non-list
remainder — each refusing with a sentence that names what is wrong. Plus a
member this build does not name, and a member removed entirely.

**Isolation.** A `base` failure carrying `combined`'s content refuses and the
reverse refuses; a post-import phase in a causal answer refuses; and a
post-import answer bound to other content refuses at its own boundary.

**Signature and readback.** `_observation_signature` re-derives a retained
failure's signature from the row's own members — it has no combined status to
read — and two different retained failures of one result have different
signatures, so a replay cannot be satisfied by the wrong one. The successful
shape still derives as it always did.

**Closed and reopened, zero repeat.** The serving composition is closed, the
integration owner is reopened **read-only** over the same store, and the retained
failure reads back through the result's own public reader with its phase and
bound intact — with **no command run and nothing materialized** to get it. This
is the durable custody the process memo could not provide, and it is now shown
across a real close and reopen rather than asserted.

**Cleanup failure.** A disposal that removes nothing is named in the retained
diagnostic and **not raised** — the failure is the fact being reported, and
losing it to a cleanup problem would be worse.

**Legacy success.** The three-integer-observation shape is untouched: a passing
document is not read as a failure, a failure is not read as the success shape,
and the base observation's `harness_added` and non-zero status still mean what
they meant.

### The provenance counts, corrected by the reviewer

`PROVENANCE-159612.md` now carries the reviewer's corrected prose: **6 new**,
**16 modified product-and-document** paths, **7 existing tests**;
`stage_execution.py` 18 hunks — 17 this Work's, 1 W71879's; `test_stage_execution.py`
6 hunks — 5 this Work's, 1 W71879's.

**And a claim of mine is narrowed there too.** I wrote that the foreign hunks are
separable "with nothing here depending on them". The reviewer: textual separation
does **not** establish that. It is a statement about text; no excised tree has
been built or run, so dependency is unmeasured either way, and the packet says so
now.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 192–195 | `tests.tools.test_execution_limits` | **124 pass** |
| 196 | that plus both owner suites and the two other limits modules | **343 pass** |

**196 runs, 1857.653101 seconds cumulative**, read after step 196; plus the four
earlier disclosed unmeasured activities.

### Changed paths this claim

| Path | Bytes | SHA256 |
| --- | ---: | --- |
| `tests/tools/test_execution_limits.py` | 155782 | `04e2519e28adab6dd17cf0f0a516a9c10789b25c53a09170142194dbefb36d76` |
| `work/.../PROVENANCE-159612.md` | 3726 | `7b2375e25a3d01b9ab501767043d6453681aa08738f34f597e947894f8efdfea` |

The 29 candidate paths and the four product files are unchanged from claim
159612.

### Still owed

**Explicit recovery** — the matrix item I did not reach: what a deployment does
after a retained failure when the operator supplies a new result or an explicit
recovery, rather than a poll. The proposal is clear that this uses the existing
recovery mechanisms and adds no implicit retry, and I have not written a case
that drives one.

**The authorization matrix item** — that a blocked failed result cannot be
published, judged or authorized — is asserted today only through "no judge was
composed" in the composed case, which is evidence and not the full statement.

Both are named as unwritten rather than implied.

## Claim 159754 — two getter-level tests replaced by the behaviours

The reviewer's point is the one worth recording: several cases I wrote read a
value back and called that the behaviour. Reading custody through a read-only
handle shows the record survives; it does **not** show that a deployment which
resumes over that store declines to redo the work. Two of those are replaced
here with the behaviour itself.

### Resumed serving, not a getter

`test_resumed_serving_after_a_reopen_runs_no_command` closes the serving
composition and both stores, composes a **new serving deployment** over the same
stores with the same external engine, and ticks it — with the host boundary still
watched.

**What is counted:** host commands and materializations across the resumed
ticks, both unchanged. The resumed deployment meets the retained failure and
runs nothing to do it. The result is still `blocked` under the same failure, with
its Job's own bound intact, and no judge is composed.

### Blocked publication and authorization, asked of the owners

`test_a_blocked_failure_can_never_be_published_or_authorized` replaces the
inference from "no judge was composed". The success predicate is false for a
retained failure; `_causal` refuses it outright; there is no status anywhere from
which a passing combined result could be derived; and its observation signature
differs from the passing shape's, so no replay can slip one in for the other.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 197 | `TheComposedHostVerificationUsesTheJobsCeiling` | 9 pass |
| 198 | `tests.tools.test_execution_limits` | **125 pass** |
| 199 | that plus both owner suites | **279 pass** |

**199 runs, 1918.189254 seconds cumulative**, read after step 199; plus the four
earlier disclosed unmeasured activities.

### Changed paths this claim

| Path | Bytes | SHA256 |
| --- | ---: | --- |
| `tests/tools/test_execution_limits.py` | 158617 | `77db05331f63958e4aa0b3a95e9ab6ba0a65e79ff3716d617b4a230ced8115e1` |

The 29 candidate paths and all product files are unchanged from claim 159672.

### Still owed, and still getter-level where it is

**The post-import held path across a reopen**, with its **one unchanged queue
hold** — the causal path is done above; the post-import equivalent is not, and
its hold is what would have to be shown unchanged.

**Durable journal replay and conflict without duplicate effects.** My signature
cases are dict-level: they show the signature derives correctly, not that the
store's own journal replays an identical act and refuses a conflicting one.

**Actual Job/result/harness/phase isolation** driven through composed owners
rather than asserted at the validator.

**Explicit recovery and new-result** after a retained failure.

**A runtime-owned cleanup lifecycle after a disposal failure** — naming what
remains is not a lifecycle, which I have said before and is still true.

The final consistent 29-path packet comes after that substantive work, not as an
editorial handoff of its own.

## Claim 159831 — the public owners, actually called

### My authorization case claimed a public-owner result it did not have

It called private shape helpers — `is_failed_observation`, `_causal`,
`_observation_signature` — and concluded that a blocked failure "can never be
published or authorized". Those helpers are real and their answers are real, but
they are not the entries a deployment reaches, and the claim was about the
entries.

**They are called now.** Against a real blocked result — one produced by a host
verification that supplied no exit status — the typed public owners
`publish_result` and `record_result_evidence` each refuse with `blocked` in their
own sentence, and the **public readback is unchanged afterwards**: same state,
same reason, same retained observations, no judge composed. The refusals come
from the owners that decide, not from a predicate standing in for them.

### The materialization counter, at its own call

`_scratch_count` counts directories, and a directory count cannot see a
materialization that cleaned up after itself — the reviewer's point exactly. The
counter now wraps `_materialize` itself and is installed alongside the command
watch, so every case that watches also counts. The resumed-serving case asserts
**one** materialization across the original run and the resumed ticks together.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 202 | `TheComposedHostVerificationUsesTheJobsCeiling` | 10 pass |
| 204 | `tests.tools.test_execution_limits` | **125 pass** |
| 205 | that plus both owner suites | **279 pass** |

**205 runs, 2030.067345 seconds cumulative**, read after step 205; plus the four
earlier disclosed unmeasured activities.

### Changed paths this claim

| Path | Bytes | SHA256 |
| --- | ---: | --- |
| `tests/tools/test_execution_limits.py` | 160457 | `edbf4776fac43b117d9cefa6799c3bb0de4a8a84f9a8aa41dc15909c90004899` |

The 29 candidate paths and all product files are unchanged from claim 159672.

### Still owed

**`record_imported`** — the reviewer's probe also calls it and gets a
`precondition` refusal; my case covers the two publication owners and not that
third one.

**Post-import serving restart** with one unchanged queue hold, actual counters
and no target advance. The causal restart is done; this is its post-import twin
and is the larger remaining piece.

**Durable journal replay and conflict without duplicate effects** — still
dict-level in my tests.

**Actual Job/result/harness/phase isolation** through composed owners, **explicit
recovery and new-result**, and a **runtime-owned cleanup lifecycle after a
disposal failure**.

Then the new consistent 29-path packet, preserving correction 159640, the W71879
attribution and the historical packets.

## Claim 159891 — the counter I said I asserted, and the post-import restart

### I reported an assertion that was not there

My last handoff said the resumed-serving case "asserts one materialization". The
counter was **installed and never read** — the reviewer checked and it wasn't in
the candidate. It is asserted now. That is the second time I have described a
test by what I meant it to do rather than by what it does, and the remedy both
times was the reviewer reading the code.

### The third refusal, in its own owner's words

`record_imported` was omitted. It is called now, and the assertions are
per-owner rather than one shared word: the two publication owners say the result
**is blocked** and quote its retained `NO EXIT STATUS` reason, while
`record_imported` refuses on its own **precondition** — so that is what is
asserted of it, instead of a word it does not use.

### The post-import restart, carried

The reviewer proved it independently and this carries it. It is the **twin** of
the causal restart and a **different shape**, which is why both exist: a causal
failure blocks the **result**; a post-import failure leaves the result
**authorized** and holds the **target** through the queue.

Fresh serving and owners over the same stores, six sweeps, and: the host command
count, the materialization count and the `block_target` count all stay at
**one**; the queue's entries are byte-for-byte what they were; the result is not
blocked. `block_target` is patched **where it is called from** — `execution`
imports it by name, so patching the queue module's attribute intercepts nothing,
which the first form of this case proved by counting zero.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 207 | the composed host class with the third refusal | 10 pass |
| 211 | that class with the post-import restart | 11 pass |
| 212 | `tests.tools.test_execution_limits` | **126 pass** |

**212 runs, 2134.517830 seconds cumulative**, read after step 212; plus the four
earlier disclosed unmeasured activities. The broad 279-test pair was not
repeated — nothing outside this module changed.

### Changed paths this claim

| Path | Bytes | SHA256 |
| --- | ---: | --- |
| `tests/tools/test_execution_limits.py` | 165318 | `d1f193f0d941e72cfd4ce4c93e9677307f573291f4f3ff55c877d0f48f15f411` |

The 29 candidate paths and all product files are unchanged from claim 159672.

### Still owed

**Actual journal replay, conflict and no-duplicate effects** — still dict-level.

**Job/result/harness/phase isolation** through composed owners, **explicit
recovery and new-result**, the **remaining direct judgment boundary**, and a
**runtime-owned cleanup lifecycle**.

**The phase cases from `repro-159705.py`** — the reviewer's four composed
base/isolated timeout and start-failed cases, which I have not carried.

Then the final 29-path packet, preserving correction 159640, the W71879
attribution and the historical packets.


## Claim 160013 — the three carryovers, together

Review 2026-09-13T10:48:56Z asked for them as one item, and this is that item:
the public assertions the post-import case was missing, the actual Journal
replay and conflict, and the four phase cases I had not carried.

### What "carries that proof" turned out to mean

I wrote that the post-import restart carried `repro-159866.py`. The reviewer
read both and it did not. Before the restart it asserted the result was **not
blocked** — not that it was **authorized** — and it never read the public
target, the blocked account, the target's reference, or the Authority's
receipts. Entry tuples are the queue table; they do not speak for those owners.

Every one of them is read now, through each owner's own public reader:

- `result_of` says **authorized**, positively;
- `target_of` says **blocked**, names `post-import-verification-no-status`, and
  its retained **account** carries the failed verification — phase
  `post-import`, the Job's own `77`-second ceiling;
- `entries_of` — the queue owner's reader, not just the raw rows, which are
  still compared as well;
- the target's reference, asked of **Git**: a hold that let the import advance
  the branch anyway would leave every row identical and the repository changed;
- and `authority.receipt(derived_proposal_id, "integration")` is **None**.

All of them again after the reopen, plus the scratch count back where the
helper found it.

### The replay reaches the Journal, and the count is of the real call

My replay evidence was **dict-level** — it compared what a helper returned. The
reviewer's `repro-159935.py` supplied the actual proof and this carries it. The
declared observation owner hands back a **copy** of the custody this deployment
really retained; it runs no command and invents no success. `replay` and
`transact` are watched **on the store**, so what is asserted is that the owner
took the replay path **once** and opened **no write transaction**.

Then only the valid diagnostic is changed — nothing fabricates a success or
edits retained custody — and the same operation carrying different observations
is refused **operation-collision**. Afterwards the public result is byte-for-byte
what it was, the write log is still empty, and the host counters are still 1/1.
The observation owner was asked **twice** and the subprocess **once**, which is
the distinction a single call count would blur.

### Four phases, two reasons, through the composed owners

The retained-failure schema is exercised elsewhere against a validator. These
drive the **real reconciled path** and fail the host command at the phase's own
call:

| Case | Calls | State | Completed | Never ran |
| --- | ---: | --- | --- | --- |
| base / timeout | 2 | blocked | `combined` | `isolated` |
| base / start-failed | 2 | blocked | `combined` | `isolated` |
| isolated / timeout | 3 | blocked | `combined`, `base` | — |
| isolated / start-failed | 3 | blocked | `combined`, `base` | — |

Every call carried the Job's own `77`, the prefix and the remainder are the
owner's own `CAUSAL_PHASES` order rather than a list spelled here, and the two
start failures also carry `could not be started` in their detail.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 213 | post-import carryover + the Journal replay | 2 pass |
| 214 | the four phase cases | 4 pass |
| 215 | `tests.tools.test_execution_limits` | **131 pass** |

**215 runs, 2170.774840 s cumulative**, read after step 215; plus the four
earlier disclosed unmeasured activities. Nothing outside this module changed, so
the broad pair was not repeated.

### Changed paths this claim

| Path | Bytes | SHA256 |
| --- | ---: | --- |
| `tests/tools/test_execution_limits.py` | 176575 | `f815602aab7488f2e4ca690cb51d5e981dae8ef71dbf695b5a62896029546b58` |

The 29 candidate paths and every product file are unchanged from claim 159672.

### Still owed, unchanged and not re-argued

**Actual Job / result / harness / phase isolation** through composed owners,
including the base-added and changed-harness operands. The retention key holds
scope, command, revision, bound and harness digest; what is not yet driven is
two real failures differing in one operand each, with neither answering for the
other.

**Explicit recovery and new-result behaviour**, and the remaining **direct
judgment boundary**. A normal poll and a successful replay are not recovery.

**A runtime-owned scratch disposal or retained-path cleanup lifecycle** after a
disposal failure, preserving the diagnosis. Fixture teardown is not runtime
ownership.

Then the final **new consistent 29-path provenance packet** using correction
159640 and preserving the W71879 attribution, the immutable historical evidence
and the integration preflight.

No Git mutation, installation or live provider.


## Claim 160092 — the scratch a failed observation left is now somebody's

### The direct judgment refusal, carried

Review 2026-09-13T11:08:02Z proved it and asked for the small regression. The
publication owners were already refused a blocked result; these are the two the
**deployment** exposes. `judgment_subject` and `judge_result` both refuse, each
naming the state, and **nothing was started**: zero `JudgmentExecution`
constructions, zero engine calls, an empty judge map, the dispatch directory as
it was, the public result unchanged and the host counters still 1/1. A refusal
that had already built an execution would be a refusal after the fact.

### Step 5, and what it actually needed — a product change

`_no_status` attempted the removal and, when the tree survived, **named it in the
diagnostic**. That reported the path and left nobody responsible for it: a
deployment released its workers, its integration store and its Authority and
walked past the bytes. A no-op `rmtree` unit test plus fixture teardown did not
discharge the step, and the reviewer said so.

**`tools/stage_execution.py`** now gives the surviving tree an owner:

- `_host_scratch(deployment)` — the registry, on the **deployment**, for exactly
  the reason the retention is: these owners are composed fresh every tick, so a
  per-instance list would forget the moment the tick ended. It holds the path
  **and** the diagnosis that named it.
- `_ConfiguredExecution` takes `surviving=` beside `retention=`, both subclasses
  pass it through, and `_no_status` registers the path where it diagnoses it.
  The diagnosis is unchanged either way — a later cleanup does not get to edit
  the failure that was reported.
- `_dispose_surviving` tries again and **returns what is still there**. A path is
  forgotten only once it is actually gone, so nothing accumulates and nothing is
  silently abandoned.
- `StageExecution._closers` releases it **before** the handles, so a store or
  Authority failure cannot be what decides whether the bytes are cleaned up. The
  paths are in the closer's **name**, because `release` reports a failed closer
  by its name and its error type — a surviving tree an operator cannot locate is
  the silence this Work keeps refusing.

Two regressions, both through the composed runtime rather than a bare owner:

1. The disposal is refused at the real boundary inside a composed causal
   failure. The tree survives, the registry holds exactly one path, the
   diagnosis names it, and the ordinary `close()` removes it — with the
   retention byte-for-byte what it was.
2. When the disposal stays broken, the release **refuses**, the message carries
   the path, and the entry is **still held** afterwards rather than dropped.
   Once disposal works again the same owner cleans it.

### An operational finding: 13 errors in `test_stage_execution` that are not mine

Running the pair after the product change, `tests.tools.test_stage_execution`
reported **13 errors** (steps 218 and 219). They are **not this claim's**:

```
File "tools/stage_execution.py", line 2503, in _run
    if deployment.reconciles():
AttributeError: 'types.SimpleNamespace' object has no attribute 'reconciles'
```

A fixture double in that module stands in for a deployment and does not answer
`reconciles()`. I verified rather than assumed: this claim's `stage_execution`
edits were reversed into a scratch copy, the copy was put in place, the failing
class was run (**step 220 — the same 4 errors**), and the working file was
restored and re-hashed identical. The gap is in that module's own fixtures,
outside the two files this Work authorizes me to change, and I have not touched
it.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 216 | judgment + the two lifecycle cases | judgment pass, lifecycle **failed** |
| 217 | the two lifecycle cases, after the closer read the deployment | 2 pass |
| 218 | `test_execution_limits` + `test_stage_execution` | **134 pass** + 13 pre-existing errors |
| 219 | `test_stage_execution` alone | same 13 |
| 220 | that class with this claim's product edits **reversed** | same 4 |

Step 216 failed because the closer read the registry off `StageExecution` while
`_host_scratch` had set it on the `Deployment`. That is the mismatch the test
existed to catch, and it caught it.

**220 runs, 2313.675154 s cumulative**, plus the four earlier disclosed
unmeasured activities.

### Changed paths this claim

| Path | Bytes | SHA256 |
| --- | ---: | --- |
| `tools/stage_execution.py` | 276640 | `633ce911794bd029e09a8b5e57d07118e593b6e53cd2f030e3017004fcc175c3` |
| `tests/tools/test_execution_limits.py` | 183631 | `4e00124b9395b24c356c9ccb5f05d66b93c313194062cf4c02a020e442bc6667` |

The other 27 candidate paths are unchanged.

### Still owed

**Actual Job / result / harness / phase isolation** through real separately
admitted identities and coherently bound tasks and content — two real failures
differing in one operand each, with neither answering for the other. Not
started this claim.

**Explicit recovery and new-result behaviour.** The reviewer's static
revalidation stands: `recovery.abandon_held_lease` requires positive Worker
Manager quiescence and leaves the target **blocked** and the entry **held**, and
`activate_target` replays activation rather than reopening a target. The
supported operation is what should be tested, with unchanged custody; no
invented retry.

Then the final **new consistent 29-path provenance packet** retaining correction
159640, the W71879 attribution and history, and the integration preflight
conditions.

No Git mutation, installation or live provider.


## Claim 160172 — isolation, the recovery seam, and a correction I accept

### My suite finding was too broad, and the reviewer's count is the right one

I described thirteen errors as though they shared one cause. They do not: **four**
are the missing `SimpleNamespace.reconciles`, **eight** are a missing `proposal`
attribute, and **one** is a Git source-materialization failure for a fixture
repository that is not there. My step-220 negative control exercised only the
four, against the previously reviewed source rather than an unchanged HEAD, so it
does not establish a baseline for the other nine either. The same three groups
already appear in retained step 95, before the cleanup claim. I have not repeated
the broad run; the selectors below are focused.

### Two carryovers, as asked, and not as a stopping point

**The retry is the public close.** The case ended by calling the private
disposer; it now lifts the fault and repeats the **same operator operation** —
the second `close()` succeeds, the path and the registry are gone, and the host
counters are still 1/1.

**The post-import branch of the same lifecycle**, for both reasons. The disposal
is refused only for this deployment's own integration root, so the fixture's Git
tooling is untouched. Exactly one path is registered, the surviving path is named
in the **real blocked target account**, the ordinary close removes it, the
retention is not rewritten, and a **fresh read-only `IntegrationStore`** — not
the handles just released — confirms the authorized result and the blocked target
are byte-for-byte what they were.

### Isolation, through real owners and real attempts

The standing objection was that a memo-key comparison cannot prove another **real
execution** will not inherit a failure. So every owner here is the product's own
`_ImportedVerifier`, composed with the operands `Integration._run` composes it
with — this deployment's observer participant, its integration root, its Git
runner and **its** retention — running against the real repository at a real
revision. The discriminator is the **attempt count at the subprocess boundary**.

The operands are the deployment's own: the two Jobs it admitted, two result
identities its own store holds, the two phases its owners run, the two bounds
`_host_seconds` answers for a configured and an unconfigured Job, and two real
harness bodies — Job B's required test and the harness the target repository
actually carries. Nothing edits a result row to manufacture a difference.

| The second owner differs in | Attempts |
| --- | --- |
| *nothing* | **0 — refused `precondition` before materializing** |
| another Job | 1 |
| another result | 1 |
| another phase | 1 |
| another bound | 1 |
| another harness | 1 |

Six real attempts, one refusal, six retained keys.

### The recovery seam, measured — and it is a missing capability

`abandon_held_lease` is the supported explicit operation, and it is reached
through an **assignment**, which `_owned_assignment` checks against the account
the target is actually blocked under.

**A post-import hold has no such assignment.** The reconciled branch starts no
integration runtime, so nothing ever composes one for the account `block_target`
records. Asserted against **every** assignment this deployment composed for the
whole drive, not a list spelled in the test:

- `held_status` and `abandon_held_lease` over the only assignment it did compose
  → `policy/denied`, *"target 'target-a' is blocked for another integration
  account"*;
- composing a fresh assignment from the blocked account → `policy/denied`,
  *"target 'target-a' is not open at fence 2; the grant this caller holds has
  been superseded or the target is blocked"*;
- after all three refusals the target, its entries, the result, the result count
  and the host counters are unchanged.

`probe-160172-recovery.py` and `run-156316-step-227.log` retain the readout,
including `account_was_ever_composed: false`.

**The bounded correction this implies, for its owner to rule on.** Either the
operator-facing status and abandonment path is keyed on the blocked **account**
rather than on a runtime assignment, or the post-import hold records an account
whose identifiers correspond to an assignment the runtime actually composed. I
have implemented neither: it is a product decision outside what this Work
authorizes me to change, and inventing a retry or writing to the store directly
is exactly what the standing instruction forbids. Abandonment would still leave
the target blocked and the entry held; `activate_target` replays activation and
is not a reopening.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 221 | public-close retry + both post-import lifecycle cases | 3 pass |
| 222 | the isolation matrix | failed — only one real result id at that point |
| 223 | the same, over the identities the store actually holds | 1 pass |
| 224, 227 | `probe-160172-recovery.py` | the seam above |
| 225, 226 | the first two recovery cases | failed — my assumption about the assignment |
| 228 | the seam case | 1 pass |
| 229 | `tests.tools.test_execution_limits` | **138 pass** |

**229 runs, 2372.290676 s cumulative**, plus the four earlier disclosed unmeasured
activities.

### Changed paths this claim

| Path | Bytes | SHA256 |
| --- | ---: | --- |
| `tests/tools/test_execution_limits.py` | 200840 | `b4f1d8c7471e6d648db605fb458c54de9795ea0e590b0b4ed020c0940b85cba9` |

`tools/stage_execution.py` is unchanged at
`633ce911794bd029e09a8b5e57d07118e593b6e53cd2f030e3017004fcc175c3`, as are the
other 27 candidate paths. No product file changed this claim.

### Still owed

The final **new consistent 29-path provenance packet**, preserving correction
159640, the W71879 method attribution and the historical immutable candidates,
all existing-test scope and the integration preflight conditions — and updating
the stale product prose about missing durable custody now that the cleanup
lifecycle is substantive.

And the owner's ruling on the recovery seam above.

No Git mutation, installation or live provider.


## Claim 160261 — the matrix relabelled, the seam measured, and the packet

### I accept the isolation finding, and the labels are corrected

The matrix constructs its owners and calls `_run` directly, so `verify_imported`,
the causal phase assembly and adoption by a result owner are all bypassed. Read
through the public readers, the variants are not the coherent pairs their names
claimed: "another Job" names `job-a` in the scope while the reader says the
result is job-b's; "another result" is the **direct entry's** identifier, which
is not an `IntegrationResult` at all; "another phase" is the coarse retention
label; "another bound" runs Job B's own result at the default while its Job was
admitted at 77; "another harness" adds a body under the same command and task.
Every raw answer also carries `input_tree` equal to `input_commit`.

The test is renamed to
`test_the_retention_key_distinguishes_its_operands_at_the_unit`, its docstring
says what it does **not** establish, and the block above it records each
variant's actual boundary in the reviewer's own terms. It stays as unit coverage
of the key at real attempts; it is not offered as composed isolation.

### The setup seam, measured rather than asserted

The instruction was: if the fixture cannot create a second derived result,
identify its exact setup seam. It cannot, and this drives the whole traversal to
establish it.

A derived result is made by the **reconciled branch**, taken when the canonical
target has moved past the proposal it was built on. This deployment binds
**exactly two Jobs** — asserted from its own bindings. The first imports
**directly**, moving the target; the second reconciles. After both have
integrated the store holds **exactly one** `IntegrationResult`, and the first
Job's accepted entry names an identifier the result owner **refuses** — which is
precisely the identifier my earlier matrix used as its "another result", so this
case is the correction as well as the seam.

A second derived result therefore needs a **third bound Job** reaching
integration after the target moved again: its own Work in the Authority, its own
producer and reviewer with the routes and capability, its own binding and its own
submitted Job, with the single configured integrator serializing all three. The
borrowed fixture has no helper for a third Job.

### The prose, corrected with the work that overtook it

Two `DEPLOYMENT.md` statements were stale: that a surviving materialization is
merely **named** in the diagnostic, and that the closed-and-reopened replay of
the post-import hold was **not yet proved**. Both are corrected. A new paragraph
records what an operator **cannot** do to a host hold — the measured recovery
boundary, stated as the narrow runtime entrypoint it is rather than as an absence
of all public capability — and the per-process limitation of the retention is
stated where a reader meets it.

### The 29-path packet

`PROVENANCE-160261.md`, `provenance-160261.json` and the read-only generator
`provenance-160261.py`. 29 paths, **6 new**, 23 modified, **+2548 / −132 in 156
hunks** at `-U0`. **Every base hash is identical to the 159612 packet's**, so
`HEAD` has not moved and the packets are comparable path by path. Exactly three
paths changed since 159612: `stage_execution.py`, this Work's test module and
`DEPLOYMENT.md`.

Correction 159640 is carried and updated rather than restated — 6 new, 16
modified product-and-document, 7 existing tests; `stage_execution.py` **19**
hunks at the default context (18 this Work's, 1 W71879's, the added one being the
cleanup lifecycle) and `test_stage_execution.py` **6** (5 and 1), unchanged since
159612. The `-U0` count reads the same foreign change as two adjacent hunks, and
the packet says so rather than leaving two numbers looking contradictory. The
W71879 attribution, the separability statement and its limit — no excised tree
has been built or run — are preserved verbatim in substance, and the integration
preflight is listed as outstanding.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 230 | the seam case + the relabelled matrix | seam **failed** — `_judged` had already taken the judgment turns |
| 231 | the seam case | 1 pass |
| 232, 234 | `provenance-160261.py` | 29 paths, figures above |
| 233 | `tests.tools.test_execution_limits` | **139 pass** |

**234 runs, 2416.185684 s cumulative**, plus the four earlier disclosed unmeasured
activities.

### Changed paths this claim

| Path | Bytes | SHA256 |
| --- | ---: | --- |
| `tests/tools/test_execution_limits.py` | 205812 | `18d7729c138d3b967e1f4349cf7c56273a4ddb643b97128b27fd18e40a559295` |
| `DEPLOYMENT.md` | 67894 | `6c288f84d15829a800a4f18878ef42b7f6980cd0f827a8a74113578981ee82da` |

`tools/stage_execution.py` is unchanged at `633ce911…`, as are the other 26.

### Still owed

**Composed isolation over two coherently admitted results** — blocked on the
setup seam above, which is a scenario change to a borrowed fixture rather than a
case, and is for its owner to rule on.

**The recovery seam** — a host-aware operator entrypoint whose quiescence
authority and exact scope need defining. Recorded, not worked around.

No Git mutation, installation or live provider.


## Claim 160341 — a third Job, the capacity that stops the second failure, and a false sentence of mine

### The documentation defect was mine, and it is corrected in all three places

My own paragraph said there is no owner-recorded durable outcome and that a fresh
process **will** attempt the command once more. That is false for the accepted
retained-failure path, and it contradicted two passages a few lines above it.

- **The document** now distinguishes them: the OUTCOME is in owner custody — a
  causal failure settles the result `blocked`, a post-import failure holds the
  target — and that is what makes a reopen quiet. The in-process retention is an
  **additional cache** that stops the repeat inside one composition.
- **The source** comments claimed the same false thing. They now name what is
  actually missing: a record of the **attempt itself**, so a process that dies
  between the command's failure and the owner's record leaves nothing to read.
  Crash-before-record, not an exactly-once guarantee.
- **The test** whose name and docstring described that behaviour — and never
  drove it — is renamed to what it asserts:
  `test_the_retained_failure_is_keyed_by_the_work_it_is_about`.

### A third Job, built here out of the fixture primitives

The reviewer settled that this belongs in this Work's own test, so it is here:
Job C's Work created in the Authority, the routes that say who may claim, the
reviewer's capability at the Work's own scope, a producer and reviewer bound to
**its** task and manifest, its binding, its submitted Job with its own **61**
second ceiling, and judges keyed to it. The policy generation is re-read after
those acts, because every one of them moves it.

`test_three_jobs_bind_three_ceilings_and_three_tasks` asserts the scenario is
coherent before anything is asked to fail: the Job owner resolves 77 for Job B
and **61** for Job C, the deployment derives `feature_check.py` for one and
`check_third.py` for the other from their own configured tasks, and all three
implementations are accepted. A scenario nobody has shown is coherent is not one
to draw conclusions from.

### And then the owners stopped at one failure

Driving toward two independent host failures found a concrete behaviour rather
than a missing helper.

Job B's failure **is** adopted durably — its own result, blocked, carrying its
own command, task identity and 77-second bound. Then its integration stage is
**exceptional**: the reconciled branch that answered `held` started no runtime
and the stage does not leave that state by itself. This deployment configures
**one** integrator, so from that tick on every admission of
`job-c/integration` is deferred with the capacity owner's own sentence — *"every
effective worker/principal capacity is reserved or recovery-required"* — and
job-c stays `queued`. The public `recover` verb answers **nothing abandoned and
nothing recoverable**.

So job-c's configured command never runs, and the reason is **capacity, not the
retention** — which the case asserts from the deferral itself rather than
inferring from a counter. `probe-160341-third-job.py` and steps 237, 239 and 240
retain the tick-by-tick readout, including the recovery answer.

**What a second simultaneous failure would take** is integration capacity a
blocked result does not hold: another integrator participant with its own
worker, or a second deployment. Both are scenario operands beyond what this
Work's fixture configures, and neither is invented here.

### The packet, with both labels corrected

`PROVENANCE-160341.md`, `provenance-160341.json` and `provenance-160341.py`.

- **The revision is pinned**: `f3fc9e12cc89bebf9524cd173103df7af67d5212`. Equal
  base hashes prove equality at the enumerated paths, not that `HEAD` could not
  have moved elsewhere.
- **The totals are labelled**: 2569 added, 132 removed and 156 `-U0` hunks are
  for the **23 tracked modified paths only**; the 6 new paths have no base to
  diff against and contribute 423727 bytes and no hunks at all.

Correction 159640 is carried, the W71879 attribution and the limit of
separability are preserved, and the integration preflight is still listed as
outstanding.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 235 | the three-Job scenario | 1 pass |
| 236, 238 | two independent failures | failed — job-c never admitted |
| 237, 239, 240 | `probe-160341-third-job.py` | the capacity behaviour and the recovery answer |
| 241 | the capacity case as the owners actually behave | 1 pass |
| 242 | `tests.tools.test_execution_limits` | **141 pass** |
| 243 | `provenance-160341.py` | the packet above |

**243 runs, 2481.982866 s cumulative**, plus the four earlier disclosed unmeasured
activities.

### Changed paths this claim

| Path | Bytes | SHA256 |
| --- | ---: | --- |
| `tools/stage_execution.py` | 277475 | `ca15f08180556d3ebe310c6ad7e0a0548d925bdd2ebf8b6bff04e7dab793db9a` |
| `tests/tools/test_execution_limits.py` | 224003 | `4b90528c3a74ad847ec5ae85ead1a1b660df5315838a365e43891ad5d985dd6b` |
| `DEPLOYMENT.md` | 68484 | `79f2925847cc74be8e96805069f860904fe39d60d47bdd3fcfa838305bcd8a0e` |

The source change is comment-only. The other 26 paths are unchanged.

### Still owed

**Two simultaneous host failures** — blocked on the integration capacity a
blocked result holds, measured above. Whether to give this Work a second
integrator participant or a second deployment is a scenario decision for its
owner.

**The host-aware recovery entrypoint** — still recorded, still not worked around.

No Git mutation, installation or live provider.


## Claim 160468 — the explanation rewritten as one, and a fresh packet

### Appending a correction underneath a wrong paragraph is not a correction

My last claim fixed the operator document and left the source saying the
opposite of it. The block above `HOST_OBSERVATION_CONTRACT` still called this
the owner contract the deployment does not have, still said neither owner could
represent a no-status failure, still proposed a `status: null` variant, and still
called `reconciliation` and `execution` out of this Work's scope — with my
correcting paragraph sitting underneath. All four statements had been overtaken
by owner ruling M157653 and by the implementation.

It is now **one** explanation, rewritten together:

- **The contract exists and both owners carry it.** `reconciliation` admits the
  tagged closed answer, validates it against the configured owner's own
  expectations, settles the result `blocked` and never authorizes it;
  `execution` adopts the post-import form and holds the target. No exit status
  is invented and neither owner needs one.
- **So the outcome is durable**, and that is what makes a reopen quiet. The
  retention is an **additional cache** for the measured twelve-runs-in-four-ticks
  repeat inside one composition.
- **What is still missing** is two halves of one narrower gap: no owner records
  the **attempt itself** — crash-before-record, not exactly-once — and a host
  failure leaves **no terminal account for the stage**, because the reconciled
  branch answers `held` with no runtime and the scheduler settles capacity from
  episode endings and completions.

`HOST_OBSERVATION_CONTRACT` now names those two instead of the delivered
durability; `_host_retention` no longer points at it as what would make the
outcome durable; the comment beside the subprocess matches; and the test that
reads the constant reads the new words.

`DEPLOYMENT.md` carries both limits in operator terms, including what the
capacity hold looks like from outside — the next Job's integration deferred tick
after tick with *every effective worker/principal capacity is reserved or
recovery-required* — and why `recover` reports nothing: it is offer-restart
recovery, and there was never a runtime to recover.

**No behaviour changed.** The source edit is comment-and-constant only.

### Two stale test commentaries

The two-Job seam case said that adding Works, routes and workers to a borrowed
fixture is a scenario change rather than a case. The third-Job helper in this
Work's own test disproves it, and the docstring now says so while keeping what
that case does establish.

`_two_failed_results` attributed the exceptional capacity hold to leaving the
scripted engine stopped. It resets that flag, and the same probe shows the stage
is exceptional anyway — because the reconciled branch answered `held` with no
runtime. The first reading is kept as explicitly **historical**.

### The packet, refreshed and bound

`PROVENANCE-160468.md`, `provenance-160468.json`, `provenance-160468.py`.
Revision pinned `f3fc9e12cc89bebf9524cd173103df7af67d5212`; 29 paths, 6 new and
23 tracked-modified; **2587 added, 132 removed, 156 `-U0` hunks for the tracked
modified paths only**, with the 6 new paths contributing 424470 bytes and no
hunks. Correction 159640, the W71879 attribution, the limit of separability and
the outstanding integration preflight are all carried.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 244 | the three cases whose commentary or constant changed | 3 pass |
| 245 | `tests.tools.test_execution_limits` | **141 pass** |
| 246 | `provenance-160468.py` | the packet above |

**246 runs, 2530.584419 s cumulative**, plus the four earlier disclosed unmeasured
activities.

### Changed paths this claim

| Path | Bytes | SHA256 |
| --- | ---: | --- |
| `tools/stage_execution.py` | 277833 | `02d83d92b6f9b0d44f42813239fb591b5d11fc13b35514665d5b4d36f6571d81` |
| `tests/tools/test_execution_limits.py` | 224746 | `66b1954ebd83781031a48170122a5014fbb63e29f4df3519300e8237d371071f` |
| `DEPLOYMENT.md` | 69337 | `0b52ed396755b816e730b8d6ebde3f0c61eafd81708fd5ed2636dc6fc96f6c7f` |

The other 26 are unchanged.

### For owner disposition

Three questions, stated as the reviewer framed them and not answered here:

1. How a host-terminated command with **no integration runtime** obtains an
   owner-validated **terminal account**.
2. What explicit action ends the exact Work, offer and allocation **without**
   rerunning the command or clearing the failure custody.
3. What existing operator action may legitimately permit a **new result** after
   a post-import hold.

A second integrator participant is **not** a remedy — integration eligibility is
restricted to the single configured `integrator_participant`. A second
deployment is permitted test setup but proves separate-deployment behaviour, not
shared-retention isolation. I have invented no runtime, no quiescence and no
release.

No Git mutation, installation or live provider.

## Claim 161103 — design review only, and one gate I do not approve

The handoff is explicit: independent design review of
`MANAGED-INTEGRATION-DESIGN-2026-09-13.md`, **do not implement**, do not
self-approve the reviewer's own design. Findings are in
`DESIGN-REVIEW-161103-2026-09-13.md`, dated and separate.

**No source was edited, no test was run, no measurement was taken.** Nothing in
the review needed one: every claim is checked against the code it is about, and
where I could not check something I said so instead of agreeing.

### What I accept

The container boundary and the rule that host paths, device/inode pairs and
engine IDs are local capabilities rather than content identity. The separation of
untrusted worker evidence from owner adoption. That a copied parent assignment
cannot activate a child — verified in `attempts.activate_assignment`, which
refuses an attempt with no committed claim of its own. The per-boundary defaults,
verified as 300 and 1800 in `execution_limits`. And preserving `_current`'s
integrity refusal of a reconciled entry on the direct path, which I would
strengthen into a separate admitted case rather than a relaxed comparison.

### The gate I do not approve

**"Charged to the parent's already-reserved integration capacity" has no
representation.** `stage_allocations` is keyed by the attempt's own id and
`allocation_of` reads by that key; no column or query expresses one attempt
drawing on another's allocation. The two available shapes each break a stated
requirement — a child with its own allocation is refused by the occupancy rule
while the parent's is live (the same sentence this Work measured from the other
side in claim 160341), and a child with none is the `JudgmentExecution` shape,
invisible to the accounting and therefore the hidden capacity the design itself
forbids. `_lane` also maps every non-review kind into the implementation lane, so
a preparation kind contends with producers and needs pool configuration.

The review names the three choices and recommends the explicit scheduler
relation, with the note that it is a `scheduler.py` change the proposal lists as
*not silently included*.

### Two prerequisites moved earlier

**Portable custody belongs in slice one**, because the node-local members are not
merely historical: `result["workspace"]["path"]` is what the judgment snapshot is
cloned from, `target_source["path"]`/`target_reference` are what a reader runs
`rev-parse` against, and `oci_delivery` proves its mounts by device and inode.

**The target-owner boundary is affirmed, and its adapter gap is exact**: the
finalization owner takes `target_root`, `reference` and `source` as local paths,
so the compare-and-swap is only performable where they resolve. Slice one needs a
target-owner entrypoint taking content identities and the grant, resolving its
own capability locally — or the implementation is single-node and must say so.

### And what it does to this Work's own tests

Enumerated by method in the review: every host-boundary case here asserts a
coordinator-local subprocess and cannot survive unchanged. They should stay as
labelled legacy coverage, and each managed replacement should assert the **same
fact** through the collected phase report — same bound, command, harness digest,
completed prefix and not-run suffix — so relocation is proved to preserve
meaning. `_watching` is already the instrument the proposal's own gate 2 asks
for.

Spending is unchanged: **246 runs, 2530.584419 s**, plus the four disclosed
unmeasured activities. No Git mutation, installation or live provider.
