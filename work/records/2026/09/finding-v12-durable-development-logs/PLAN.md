# Current state — review201428 signed off, awaiting owner disposition

Read review-2026-09-18T07-40-38Z.md and REVIEW-EVIDENCE-201428.json.
Selected private development logging outcome independently signed off; latest
malformed-state containment correction verified with 235 tests and prior probes.
Pass to configured baton.decide approver. No remaining implementation correction
requested. Preserve canonical evidence and separate W197661 lifecycle ownership;
Git and deployment actions remain with their owners. This supersedes earlier
current-action correction entries without rewriting their history.

# Current action — review201318 bounded correction

Read review-2026-09-18T07-23-56Z.md and REVIEW-EVIDENCE-201318.json.
Prior three restart findings accepted. Correct unhashable list/object carried-state
decoding before capture startup, test real caller containment and valid controls,
and preserve descriptor cleanup. Coordinate shared inputs and image attribution.
No extra permission gate; prior accepted behavior and evidence remain intact.

# Current action — review201212 changes requested

Read review-2026-09-18T07-09-49Z.md and REVIEW-EVIDENCE-201212.json.
Preserve unknown prior completeness; require successful carried persistence before
clearing prior evidence; distinguish unreadable carried records from absence. Cover
real caller failure/interruption/restart paths and retain all-successful/live-follow
controls. Normal declared-loss carry is accepted. Coordinate shared inputs and image
attribution; standing scope/test authority applies without another approval gate.

# Current action — review201085 changes requested

Read review-2026-09-18T06-53-11Z.md and REVIEW-EVIDENCE-201085.json.
Preserve earlier loss/unknown completeness across successful append/restart while
keeping active writers followable and the all-successful control captured. Add
real provider/wrapper restart regressions; coordinate shared paths and update image
attribution if input bytes change. Prior FIFO/hard-link and stale-finished fixes
are accepted; this supersedes full-completion claims only. Existing authority applies.

# Current action — review200927: shared stream and declaration corrections

Read `review-2026-09-18T06-27-53Z.md`, REVIEW-EVIDENCE-200927.json and review-probes-200927.py. Native alias/reserved-name corrections pass independent probes; both hashes match and 843 tests pass in two focused runs. Complete shared append_writer nonblocking/confinement behavior and prevent reused streams inheriting stale terminal declarations. Coordinate exact shared-format/worker/test paths with W197661 before edits and bind new artifact evidence honestly. Existing authority applies; no new permission gate. This supersedes older current-action summaries while preserving history. Reviewer owns only new review/evidence/probe and attributable FINDING/PLAN additions, not product/tests/PROGRESS.

# Current action — review200560 changes requested

Read `review-2026-09-18T05-32-05Z.md`, REVIEW-EVIDENCE-200560.json and review-probes-200560.py. Prior generation/parser and FIFO corrections pass; both candidate hashes match and 174 focused tests pass. Correct native destination hard-link aliasing before writes and the silently omitted provider bookkeeping-name collision, with ordinary append and restart controls. This explicitly supersedes the older current-action summaries below; full acceptance remains pending. Existing authority applies. baton.rvpc owns only the new review/evidence/probe and attributable FINDING/PLAN additions; implementer owns product/tests and PROGRESS. Preserve history and W197661 ownership/provenance.

# Current action — review200300 changes requested

Read `review-2026-09-18T04-53-08Z.md` and REVIEW-EVIDENCE-200300.json. Correct generation validation exceptions and nonregular data-descriptor blocking, with bounded normal-entrypoint regressions. Both prior candidate hashes and 162 tests pass; full acceptance remains pending. This supersedes earlier current summaries below. Existing authority applies; no new approval gate. baton.rvpc owns only this review/evidence and its FINDING/PLAN additions; implementer owns product/tests and PROGRESS. Preserve prior history and W197661 provenance.

# Current action — claim200182 response to review199997

Both findings were mine and both are corrected. The retention record is
VALIDATED where it becomes a decision -- closed entries, confined
single-component destinations, and a destination that must be the flattened
source or one of its own generations -- so a record naming `../escaped` writes
nothing outside the corner. And the data/record commit window is RECOVERABLE:
bytes go down first, the record follows, and a destination found ahead of its
record is believed only when its head and the source's agree over the reconciled
length. A record that could not be written is declared rather than discarded.
Returned to `baton.bug`; full Work acceptance remains pending. Existing
authority; no new permission gate.

# Current action — review199997 changes requested

Read `review-2026-09-18T04-07-54Z.md` and REVIEW-EVIDENCE-199997.json. Fix ignored metadata-write failures and data/record recovery window; validate/confine persisted destinations and staging/record files. Normal generation tests pass but full acceptance remains pending. Existing authority; reviewer holds no product paths. This supersedes older current summaries below.

# Current action — claim199918 response to review199876

The source-to-generation binding is DURABLE: a record inside the native corner
(`attempt_log_format.RETENTION`) holds each source's identity, destination,
offset and a digest of its retained head, so ticks and restarts resume the same
generation instead of measuring the original file again. The generation
namespace is `%23`, disjoint from every name `_flat` can emit. Both of the
review's probes re-run correct. Returned to `baton.bug` for independent review;
full Work acceptance remains pending. Existing authority; no new permission gate.

# Current action — review199876

Read `review-2026-09-18T03-48-00Z.md` and REVIEW-EVIDENCE-199876.json. UTF-8 prior probe corrected. Complete stable native generation mapping across ticks/restart, honest changed-source handling and collision-free generation names. Existing authority; reviewer holds no product paths. This supersedes older current summaries below.

# Current action — review199814 changes requested

Read `review-2026-09-18T03-39-32Z.md` and REVIEW-EVIDENCE-199814.json. Multi-tick native duplication fixed. Complete UTF-8 follow progress/live-byte handling and native generation/restart/truncation identity with honest root failures. Existing authority applies; reviewer holds no product paths. This supersedes older current summaries below and preserves history.

# Current action — review199735 changes requested

Read `review-2026-09-18T03-27-44Z.md` and REVIEW-EVIDENCE-199735.json. Fix native caller offset/failure propagation and complete confinement, then drain completed follow streams and wait correctly for absent streams. Prove actual multi-tick and deployed follow behavior. This supersedes older current summaries below; preserve historical evidence. Reviewer holds no product paths; existing authority applies.

# Current action — review199623 changes requested

Read `review-2026-09-18T03-10-39Z.md` and REVIEW-EVIDENCE-199623.json. Complete actual binary stdout tee, incremental native retention with collision-free paths/full bytes/honest failure and no-follow confinement, and usable deployed follow behavior. This supersedes older current summaries below; preserve historical decisions and proofs. Existing authority applies, reviewer holds no product path.

# Current action — review199387 changes requested

Read `review-2026-09-18T02-31-51Z.md` and `REVIEW-EVIDENCE-199387.json`. Complete production packaging, all affected startup/stdout capture, actual native-session retention, truthful subprocess failure states and runnable operator read/follow delivery with normal-boundary deterministic tests. Claim199285 is a partial implementation, not full acceptance. This current action supersedes earlier current-state summaries below; historical decisions and accepted bounded corrections remain preserved. Implementer owns product/test corrections; reviewer owns this review only. No additional permission gate.

# Current actionable state — bounded fixes accepted; complete capture wiring

Review199229 (`review-2026-09-18T02-02-21Z.md`) accepts the exact two-file R1/R2/R3 correction after 59 tests and independent probes. Complete R4 under existing authority; no separate half-wiring approval or reviewer product-path hold. Enumerate exact shared-writer/image/CLI paths, implement the integrated outcome and verify its capture/failure/restart behavior. Preserve history and append the claim199159 provenance correction for the mislabelled EVIDENCE-199021 episode.

# Current review disposition — changes requested, claim199005

Read `review-2026-09-18T01-25-03Z.md` and REVIEW-EVIDENCE-199005.json. Validate stream operands before filesystem access, preserve unowned staging entries on collision, and handle short/failed writes before publication. Then complete the integrated capture/lifecycle/operator outcome. No reviewer product-path hold or new approval gate.

# Current review disposition — changes requested, claim198940

Read `review-2026-09-18T01-15-42Z.md` and REVIEW-EVIDENCE-198940.json. Correct sidecar read/write confinement, concurrent declaration loss and malformed status handling, then deliver the complete wired capture/lifecycle/operator command outcome. Earlier direct stream/native corrections pass focused tests; no full delivery acceptance yet. No new authority gate or reviewer product-path hold.

# Current review disposition — changes requested, claim198868

Read `review-2026-09-18T01-04-54Z.md` and `REVIEW-EVIDENCE-198868.json`. Fix capture-state propagation and attempt-boundary reads, then finish wrapper/provider/verification/native capture, lifecycle wiring and actual operator commands before returning the complete candidate. Current 31 tests pass but miss reproduced defects; standing test authority covers the necessary expectation corrections. No new approval gate is introduced. Reviewer holds no product path; preserve accepted worker launch semantics and W197661 immutable image evidence during serial source edits.

# Current assignment — baton.claude

Latest owner selection on 2026-09-18 UTC retains Claude on baton.impl and supersedes the proposed tuner assignment before any reroute. Claude claims explicitly and owns implementation PROGRESS. No parallel tuner execution. Preserve Codex-owned files and changes; coordinate any shared-file handoff before editing. Return the completed candidate for independent review.

# Path ownership, enumerated before edits — claim198803

Recorded here before any edit, as the owner constraint and review198746 require.

**Claude owns and edits, this claim:**

| path | why |
| --- | --- |
| `v12/python/src/baton_v12/worker_manager/attempt_logs.py` | NEW. The dedicated attempt-log delivery: manager-owned host location created before worker startup, its fixed container target, the locator/read/follow surface and the honest capture-state vocabulary. |
| `v12/python/src/baton_v12/worker_manager/oci.py` | the writable mount for that delivery, owned by its own mount function beside `_exchange_mounts` and `_credential_mounts`, and held to the target constant. |
| `v12/worker/claude_agent.py` | the tee: provider stdout parsed AND retained byte-identically, provider stderr and both verification streams off `DEVNULL`, native session output retained, explicit partial/failed capture. |
| `v12/worker/baton_worker.py` | the wrapper's own earliest output, which a provider-side tee cannot reach. **Coordinated serially with W197661**, whose candidate this file is; see below. |
| `v12/python/tests/manager/test_attempt_logs.py` | NEW. The delivery, the locators, read/follow, and the failure vocabulary. |
| `v12/python/tests/manager/test_oci.py` | the mount's vector and its refusals. |
| `v12/python/tests/manager/test_claude_agent.py` | the tee, byte-identical parsed stdout, both channels on success and failure, drain/termination, and capture failure. |
| `v12/python/tests/manager/test_integration_worker.py` | the three later refusal sites review198746 asked for. |

**Not Claude's, and not edited:** every reviewer-owned review and
`REVIEW-EVIDENCE-*.json`; the reviewer's entries in FINDING and PLAN.

**W197661 coordination.** That Work is queued at `baton.bug` and its candidate
includes `v12/worker/baton_worker.py`. Its accepted images contain the OLD
`integration_entry.py` bytes, and this Work's slice does not retroactively
change those immutable images or their accepted silent-exit observation. Any
edit to `baton_worker.py` here builds on the accepted current bytes
(`8a5f4895…`) and never restores an earlier candidate. W194457's closure is not
permission to restore older versions of its paths.

# Current plan

Review198746 accepts only the two-file integration-diagnostic slice; the whole
Work remains incomplete. See review-2026-09-18T00-44-19Z.md and
REVIEW-EVIDENCE-198746.json. Continue authorized capture implementation across
manager delivery/mount, wrapper/provider/verification/native streams and
operator read/follow. Enumerate exact new paths before edits and coordinate
W197661's separate source/image freeze. Missing log storage is implementation
scope, not an additional approval gate. Preserve this partial candidate and
return the complete digest-bound outcome for review.

Owner-selected implementation: restore durable raw evidence for private v12 development runs. FINDING.md is the confirmed contract; this is a follow-up to W61599's closed minimum activity outcome, not a rewrite of that acceptance.

1. Claim the bound Work and revalidate current code, later decisions and W197661 ownership before edits. Enumerate affected capture, startup, custody, viewer and test paths in this plan. Coordinate any overlap before concurrent edits; no foreground prompt implementation or managed-review substitution.
2. Implement stable attempt log storage and incremental stdout/stderr/native-log retention; remove DEVNULL disposal at affected boundaries while preserving parsed/protocol output and deadlines. Add missing startup refusal diagnostics and a simple operator locator/read/follow surface. Preserve partial logs and honest capture-failure reporting.
3. Verify the required outcome with short deterministic regression tests. Reuse unchanged evidence and the assembled-deployment smoke where applicable; do not run broad suites or live models merely because the Work changes hands.
4. Return the complete digest-bound candidate and evidence for independent review. Record concrete operator commands and any artifact rebuild requirements. Deployment and recovery stay separate.

Implementation progress belongs to the eventual claimed implementer. Product/test file ownership is not preclaimed by this planning record. No files outside this dossier and historical decision cross-references are modified by the prompt participant.

## Required ownership boundary

Before edits, enumerate implementation paths and check existing Codex-owned paths and changes. Claude cannot overwrite them; obtain an explicit shared-file handoff where needed. Keep smoke fixture/evidence changes disjoint; transfer any shared file explicitly before editing. Never overwrite newer bytes with an earlier candidate.


# R4's remaining integration, DECIDED — claim199021

Enumerated before editing, as the owner constraint requires. The previous three
claims left R4 as a question ("where do the logs live, and how does a worker
declare capture without importing the manager?"). This claim answers both, so
the next one starts from a decision. Neither answer is implemented yet and the
handoff says so.

## Where the host room lives: under the LAUNCH storage, beside the exchange

Measured against the tree, not chosen by preference. Three candidates:

| candidate | why not / why |
| --- | --- |
| a third root beside `inputs` and `workspace` | `workspaces.assignment_workspace` rules this out in its own words: "a future source stager or driver allocates its own private capacity under an explicit owner. Private ephemeral space is generic runtime capacity, not protocol vocabulary this manager provisions." |
| a new `log_home` deployment member | `single_worker._MEMBERS` is a CLOSED set and `baton.v12.single-worker-deployment/4` is frozen. Adding a member invalidates every existing `/4` document — including the three W197661 composed for its lifecycle exercise, which are under review right now. It would need a `/5`, which is a schema change this Work does not need. |
| **`<launch_home>/logs/<attempt>/`** | **selected.** `launch_home` is already the per-role manager-owned directory outside the checkout; the log room becomes a sibling of the attempt launch roots rather than a child of one, so no attempt id can collide with it. No schema change, no new operator selection. |

The delivery then RIDES WITH THE LAUNCH exactly as the exchange does —
`LaunchDelivery.exchange` says why in its own comment, and the same sentence is
true here: both are non-secret control material fixed before start and both
belong to the exact attempt.

**And `launch.discard` deliberately does NOT remove it.** The room is outside
the launch root, so a launch teardown leaves it alone — which is the required
outcome rather than an oversight: *partial evidence must survive error,
abnormal termination and restart*. Retention is the retention policy's
question, not a teardown's.

## How a worker declares capture: a shared writer, not a second implementation

The worker cannot call `attempt_logs.record_capture`: `baton_v12` does not
travel into worker images, and `claude_agent`'s own comment gives the reason —
"a worker that can import the manager is a worker one bug away from holding the
manager's capabilities". The sidecar format therefore has TWO writers, and two
implementations of one format is exactly how they drift.

The precedent is already in the tree and is what this follows:
`baton_v12.source_profiles` is a package that imports nothing from `baton_v12`
and is copied into images under its own top-level name, and
`worker-control-1.0.schema.json` is a packaged asset both ends hold. So the
declaration format gets ONE owner that both sides import, rather than a manager
copy and a worker copy.

## Paths, enumerated

| path | change |
| --- | --- |
| `v12/python/src/baton_v12/worker_manager/launch.py` | materialize/adopt the log room under `<launch_home>/logs`; carry it on `LaunchDelivery`; leave it alone in `discard`, and say so. |
| `v12/python/src/baton_v12/worker_manager/oci.py` | pass `logs_delivered=self.launch_delivery.logs.mounts()` at the one `run_vector` call site. |
| NEW, shared declaration writer (name to be settled with the image recipe) | the sidecar format with one owner, imported by the manager and copied into the image as `source_profiles` is. |
| `v12/worker/claude_agent.py` | the tee: provider stdout parsed AND retained byte-identically, provider stderr and both verification streams off `DEVNULL`, native session retention, capture state declared through the shared writer, with the owner's supersession of W39357 recorded AT THE SITE. |
| `v12/worker/baton_worker.py` | the wrapper's earliest output. Built on the accepted bytes `8a5f4895…`; never restores an earlier candidate. |
| the fixture/provider image recipes | must carry the shared writer, so both images are rebuilt; W197661's accepted immutable digests are NOT changed and no existing image is re-attributed. |
| `v12/python/tools/` operator command | a real `read`/`follow` over a named attempt. |
| `tests/manager/test_launch.py`, `test_oci.py`, `test_claude_agent.py`, `test_attempt_logs.py` | the integrated failure/concurrency/shutdown matrix across all producers and readers together. |

**Blast radius, stated rather than discovered later.** Creating a log room on
every launch changes what `test_launch`, `test_oci`, `test_worker_entry` and
the integration-worker suites observe on disk, and the image recipes change
means a rebuild. That is why this claim did not start it half-way: a partially
wired lifecycle with the adjacent suites unverified is worse than an unwired
one with the decision written down.


# R4's exact paths, enumerated before edits — claim199285

Review 2026-09-18T02-02-21Z asks for the remaining broad placeholders to be
replaced with exact paths, and for actual concurrent ownership to be
coordinated. Both, before anything is edited.

**Claude owns and edits, this claim:**

| exact path | change |
| --- | --- |
| `v12/python/src/baton_v12/attempt_log_format.py` | **NEW, and this is the shared writer's exact name.** The declaration format with ONE owner: the stream allowlist, the declarable states, their prose, the sidecar name, and the exclusive-create/write-whole/replace act. It imports nothing from `baton_v12` and raises its own plain exception, exactly as `baton_v12.source_profiles` imports nothing and travels under its own name. |
| `v12/python/src/baton_v12/worker_manager/attempt_logs.py` | delegates the format to that module and keeps the manager's own vocabulary (`ContractRefusal`, the typed delivery, the capture-state reading). No rule moves; one owner replaces two. |
| `v12/python/src/baton_v12/worker_manager/launch.py` | materialize/adopt the log room under `<launch_home>/logs/<attempt>/`; carry it on `LaunchDelivery`; `discard` deliberately leaves it, because partial evidence surviving teardown is the required outcome. |
| `v12/python/src/baton_v12/worker_manager/oci.py` | pass `logs_delivered` at the one `run_vector` call site from the launch delivery's own `mounts()`. |
| `v12/worker/baton_worker.py` | the wrapper's earliest output, written through the shared format module. Built on the accepted bytes `8a5f4895…`; never restores an earlier candidate. |
| `v12/worker/claude_agent.py` | the tee: provider stdout parsed AND retained byte-identically, provider stderr and both verification streams off `DEVNULL`, native session retention, capture state declared through the shared module, with the owner's supersession of W39357 recorded AT THE SITE. |
| `v12/python/tools/attempt_logs_command.py` | **NEW, and this is the operator command's exact name.** `locators`, `read` and `follow` over a named attempt's room. No engine, no store. |
| `v12/python/tests/manager/test_attempt_logs.py` | the shared-format delegation and the integrated matrix. |
| `v12/python/tests/manager/test_launch.py` | the room made before start, adopted on restart, surviving `discard`. |
| `v12/python/tests/manager/test_oci.py` | the bind reaching the vector. |
| `v12/python/tests/manager/test_claude_agent.py` | the tee, both channels on success and failure, and honest partial/failed state. |
| `v12/python/tests/tools/test_attempt_logs_command.py` | **NEW.** The operator surface. |
| `work/records/.../instance-198750/fixture-context/Dockerfile.fixture` | carries the shared writer; the fixture image is rebuilt and gets its own new digest. |

**Image recipes, exactly.** The accepted provider and integration images
(`sha256:35f36286…`, `sha256:dac354d8…`) are IMMUTABLE and are not rebuilt or
re-attributed by this Work; W197661's attribution of them stands untouched. The
recipe this Work rebuilds is its own labelled fixture.

**Not Claude's, and not edited:** every reviewer-owned review and
`REVIEW-EVIDENCE-*.json`; the reviewer's entries in FINDING and PLAN.

**Concurrent ownership, checked rather than assumed.** W197661 is queued at
`baton.bug` and its current candidate is `worker_manager/intake.py`,
`tests/manager/test_intake.py` and `instance-199021/verify_lifecycle.py`. None
of those is in the table above. `baton_worker.py` and `claude_agent.py` are in
neither Work's live candidate; both are edited here on their accepted bytes.


# The five corrections, with exact paths — claim199562

Enumerated before editing, as the review requires.

| finding | exact path | change |
| --- | --- | --- |
| 4 (defect) | `v12/worker/claude_agent.py` | `_Captured` learns the three outcomes a child really has: **never started**, **interrupted**, **completed**. `_ran` and `_ran_provider` declare from the outcome rather than from reaching a `finally`. A stream whose child never ran is `failed`, not `finished`. |
| 2 | `v12/worker/integration_entry.py` | the ordinary branch enters the same capture the managed branch reaches through `baton_worker.main`, so an integration startup refusal is retained. |
| 2 | `v12/worker/baton_worker.py` | the wrapper tees **stdout as well**, byte-for-byte, without changing what a caller sees. |
| 1 | `v12/worker/Dockerfile.claude`, `v12/worker/Dockerfile.integration` (and the prepared build contexts that mirror them) | carry `attempt_log_format.py` into the supported images. Historical selected digests are preserved; any new image is its own provenance. |
| 3 | `v12/worker/claude_agent.py` | the provider's own session files are retained into the delivery's native corner, incrementally, proved with a deterministic fake provider that really writes them. The credential symlink is not followed and no credential is read. |
| 5 | `v12/python/pyproject.toml`, `v12/python/tools/attempt_logs_command.py` | a real installed entrypoint and copyable examples whose operand order is the one argparse actually accepts; the follow gap is either closed or documented as a gap rather than described as delivery. |
| tests | `v12/python/tests/manager/test_claude_agent.py`, `test_attempt_logs.py`, `tests/tools/test_attempt_logs_command.py`, `tests/manager/test_integration_worker.py` | real-boundary cases for each of the above, driven through `_ran`/`_ran_provider` and the real entrypoints rather than by selecting declaration states by hand. |

**W197661 coordination.** That Work is queued at `baton.bug`; its candidate is
`job_manager/schema.py`, `manager.py`, `projection.py`, `documents.py`,
`tools/stack.py` and its job-manager test paths. None of those is in the table
above. Its immutable image digests and its retained failed disposable attempt
are not touched.


# The two corrections, with exact paths — claim200454

Enumerated before editing, as the standing review requirement asks.

| finding | exact path | change |
| --- | --- | --- |
| R1 (defect) | `v12/worker/claude_agent.py` | `_generation_of` decides a bounded ASCII numeral through `_GENERATION` rather than `isdigit` plus `int()`, so validation over untrusted input is total; a malformed entry is dropped and declared while the provable entries survive. |
| R1 sweep | `v12/worker/claude_agent.py` | `RecursionError` is caught beside `UnicodeDecodeError`/`ValueError` at every bounded decode in this file — the retention record, the review report and the task document. A bound on bytes is not a bound on depth. |
| R2 (defect) | `v12/worker/claude_agent.py` | `_retained_size` answers `None` for a destination that is not a regular file, and `_reconciled` starts a generation rather than writing into it; `_appended` acquires BOTH data descriptors with `O_NONBLOCK` and refuses either one unless `fstat` says regular. |
| tests | `v12/python/tests/manager/test_attempt_logs.py` | 12 cases in one new class: both malformed generation suffixes and the suffix boundary itself, a legitimate generation still believed, the nested document, an existing destination fifo and directory, a destination swapped under a held reader, a source swapped with and without a writer, and the bounded-decode sweep. Bounded children where a defect would otherwise hang the suite. |

**Nothing else is edited.** `attempt_log_format.py`, `attempt_logs.py`,
`baton_worker.py`, `launch.py`, `oci.py`, the tools command and every image
recipe are untouched this claim, so no image input changed. W197661 is queued at
`baton.bug`; its candidate paths, its instance episode and its image attribution
are not touched here.


# The two corrections, with exact paths — claim200870

Enumerated before editing, as the standing review requirement asks.

| finding | exact path | change |
| --- | --- | --- |
| R1 (defect) | `v12/worker/claude_agent.py` | `_acquired` is the one owner of destination acquisition: `O_EXCL` when claiming a name nothing holds, `fstat` proving `S_ISREG` **and** `st_nlink == 1` on the descriptor that will be written, and exactly ONE rotation when neither holds. `_appended` acquires before it positions the source, because acquiring can rotate. |
| R2 (defect) | `v12/worker/claude_agent.py` | `_flat` escapes a flattened name that would collide with the record or its staging namespace (leading `.` becomes `%2E`); `_walked` no longer skips any source name. |
| tests | `v12/python/tests/manager/test_attempt_logs.py` | 11 cases in one new class: the reviewer's alias probe, the source kept separately, `O_EXCL` observed at the real open, an ordinary single-link append as the control, an alias created AFTER the destination was, a corner whose fresh name is also unusable stopping after one rotation, the reserved name and its prefix retained, resumed across a restart, the escape staying injective, and the record itself still not being a session file. |

**Nothing else is edited.** `attempt_log_format.py`, `attempt_logs.py`,
`baton_worker.py`, `launch.py`, `oci.py`, the tools command and every image
recipe are untouched, so no image input changed: all three of
`fixture-199918`'s context copies are byte-identical to this tree. W197661 is
queued at `baton.bug` with its own candidate; its paths are untouched here and
its two suites run green against this tree.


# The two corrections, with exact paths — claim201008

Enumerated before editing, and the shared-file overlap checked first:
**W197661's live candidate is `instance-200564/*` plus
`tests/manager/test_w197661_verifier.py`**, none of which is touched here, and
its suites run green against this tree.

| finding | exact path | change |
| --- | --- | --- |
| R1 (defect) | `v12/python/src/baton_v12/attempt_log_format.py` | `append_writer` acquires nonblocking, creates a fresh entry with `O_EXCL` rather than adopting one, and refuses a descriptor that is not a regular file with exactly one link. It answers the refusal into an optional `refused` list so the caller can say WHY. |
| R2 (defect) | `v12/python/src/baton_v12/attempt_log_format.py` | **NEW** `clear_declaration`, and `append_writer` calls it before answering a handle: a terminal word that no longer describes the bytes is removed, and a clearing that fails refuses the handle. Metadata only; the bytes are never touched. |
| both | `v12/worker/claude_agent.py` | `_Captured` passes its own `refused` list and carries the sentence into the declaration a reader meets. |
| both | `v12/worker/baton_worker.py` | `_TeeStream` does the same, which is what puts a reason on the wrapper's earliest output. |
| tests | `v12/python/tests/manager/test_attempt_logs.py` | 15 cases through the REAL callers: a bounded child proving the fifo no longer blocks, the fifo and alias declared with their reasons, a directory refused, the WRAPPER's own stream through `_TeeStream`, an ordinary stream and a restart append as controls, the second writer not inheriting, the operator state through the real `follow` while the second writer is open, the earlier bytes preserved, a second writer that finishes saying so, an interrupted second writer reading live, a clearing that fails refusing the handle, and clearing touching metadata and never bytes. |
| image evidence | `fixture-201008/` | **NEW** context, image `sha256:d1a9021c…` and smoke, for the bytes that actually changed. `fixture-199918` is untouched. |

**Not edited:** every reviewer-owned review and `REVIEW-EVIDENCE-*.json`; every
prior `EVIDENCE-*.json`; `fixture-199285` and `fixture-199918`; W197661's
candidate paths.


# The remaining restart-honesty correction, with exact paths — claim201156

Shared-path ownership checked first: **W197661's live candidate is
`instance-200564/*` plus `tests/manager/test_w197661_verifier.py`**, none of it
touched here, and its suites run green against this tree.

| finding | exact path | change |
| --- | --- | --- |
| R1 (defect) | `v12/python/src/baton_v12/attempt_log_format.py` | `SEVERITY` and `worst` give the four declarable states an order that is the vocabulary's own meaning; `carried_name`, `read_carried` and `carry_declaration` keep a per-stream CUMULATIVE record; `append_writer` carries the prior word into it instead of discarding it, and hands the worst back to the caller. An unreadable cumulative record reads as the worst thing it could have said. |
| R1 | `v12/worker/claude_agent.py` | `_Captured` collects what was carried and `_aggregate` widens its own outcome to the completeness of the whole file, with a reason naming the earlier generation. |
| R1 | `v12/worker/baton_worker.py` | the wrapper's tee does the same, which is the path a restart really takes. |
| tests | `v12/python/tests/manager/test_attempt_logs.py` | 13 cases: the reviewer's detected-short-write probe through the real capture AND the real `follow`, the raw bytes preserved, every prior loss state surviving, the worse of two winning, the ALL-SUCCESSFUL control still ending `captured`, an active second writer still keeping follow alive, the loss durable while that writer is open, a clean first capture writing no record, an unreadable record treated as the worst, the record not being one of the streams, and both wrapper paths. |
| image evidence | `fixture-201156/` | **NEW** context, image `sha256:23edb0ca…` and smoke for the bytes that actually changed. `fixture-201008` and `fixture-199918` are untouched. |


# The three restart-honesty corrections, with exact paths — claim201274

Shared-path ownership checked first: **W197661's live candidate is
`instance-200564/*` plus `tests/manager/test_w197661_verifier.py`**, none of it
touched here, and its suites run green against this tree.

| finding | exact path | change |
| --- | --- | --- |
| R1 | `v12/python/src/baton_v12/attempt_log_format.py` | `carry_declaration` treats bytes with no declaration as `partial`; `_has_bytes` is the distinction between prior bytes and an empty new stream, and answers True when it cannot tell. |
| R2 | same | the prior sidecar is cleared only when `_write_carried` succeeded; otherwise the acquisition refuses and the evidence stays. The refusal reason names both halves. |
| R3 | same | `read_carried` answers `None` only for genuine absence; every open or read failure and every non-regular record answers `failed`. |
| tests | `v12/python/tests/manager/test_attempt_logs.py` | 13 cases: the unknown ending and its wrapper twin, a corrupt prior declaration, an empty new stream and the all-successful restart as controls, an active writer keeping follow alive, the failed carry refusing and keeping the evidence, that refusal not stopping the child, the refused writer's bytes reaching nothing, an inaccessible record, a non-regular record, a read failure, and a genuinely absent record still reading as absence. |
| image evidence | `fixture-201274/` | **NEW** context, image `sha256:f62733c6…` and smoke. `fixture-201156`, `fixture-201008` and `fixture-199918` are untouched. |


# The malformed-record containment correction — claim201391

Shared-path ownership checked first: **W197661's live candidate is
`instance-200564/*` plus `tests/manager/test_w197661_verifier.py` and
`tests/manager/test_importing_fixture.py`**, none of it touched here, and its
suites run green against this tree.

| finding | exact path | change |
| --- | --- | --- |
| R1 | `v12/python/src/baton_v12/attempt_log_format.py` | `declared_state` is the one place a value becomes a state: a string that is one, or `None`. `read_carried` decodes totally over every JSON value type and answers `failed` for anything that is not a state; `worst` routes both operands through it; `carry_declaration` guards its severity lookup. |
| tests | `v12/python/tests/manager/test_attempt_logs.py` | 9 cases: every JSON value type decoded without raising, valid states still reading as themselves, a clean stream untouched, the CHILD still getting a usable stream, no descriptor leaked, `worst` answering on either side, `declared_state` itself, and both wrapper paths including the real stream still receiving its text. |
| image evidence | `fixture-201391/` | **NEW** context, image `sha256:f7bcc603…` and smoke. Every earlier fixture episode is untouched. |
