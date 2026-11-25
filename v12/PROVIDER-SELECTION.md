# Explicit provider selection and retained homes

Provider selection is opt-in. Existing deployment `/4`–`/6`, launch and policy
`/1` documents keep their existing execution path and identities. The new
single-worker deployment `/7` selects a shared `baton.worker-tool-policy/2`,
provider adapter `/2`, runtime profile `/2`, and worker launch payload `/6`
inside the existing exchange wrapper. Publication workers remain provider-free.

Composition requires four explicit values: provider, requested selector, exact
reported identity, and CLI build. There is no model mapping default or fallback.
`pool compose-worker` accepts `--provider`, `--requested-model`,
`--reported-identity` and the existing `--cli-build`. Only the shipped Claude
realization exists. No Codex arguments, image, credential reference or model
identifier are selected by this implementation.

The provider policy package is shared by the manager and worker image. Its
closed realization table binds the argv, environment, credential location and
mode, home mount, managed entries and participation sources to the adapter
digest. Changing a selector changes the worker profile identity; it does not
change the shared Job tool policy. Admission still enforces that Job identity.
A pool's separation class is derived from its selected providers and selectors.

### Optional service tier

A selection may carry one optional member, `service_tier`, beside the model.
`pool compose-worker --service-tier <tier>` sets it. It is accepted only where
the closed table `provider_policy.SERVICE_TIERS` names it for that provider and
exact CLI build; today that is `fast` for Codex 0.169.0, which adds exactly
`-c 'service_tier="fast"'` after the model argument and before the prompt.
Any other value, provider or build refuses. Nothing selects a tier
automatically, and no tier is a fallback for another.

Unset is spelled by omitting the member. A selection without it produces the
same selection, runtime profile, adapter and argv bytes as before, so every
existing digest is unchanged. A selected tier is part of the selection, appears
in the runtime profile and in the adapter's `argv_policy`, and therefore
changes the profile and adapter digests: it is a different execution identity.
The worker takes the tier only from its validated selection, and its argv is
compared with the manager's as for the model.

Requested is not observed. Attribution records `service_tier.requested` from
the selection and `service_tier.observed` as absent, with outcome `missing`;
no build has a declared source for the tier a provider actually served, and
argv, configuration echoes and the selection itself are never read as one.
The tier adds no hold cause. The retained 0.169.0 `exec` help evidences
`-c <key=value>` with a TOML value. It does not evidence that this build
recognizes `service_tier`, or how the key combines with
`--ignore-user-config`; both stay qualification observations. The production
realization supports explicit selection but does not select fast mode.

## Attribution

Before a selected provider turn, the adapter probes that program's `--version`
with disconnected stdin, a five-second bound and bounded anonymous-pipe
capture. The probe is not reported as a model invocation. The turn uses the
exact selected model argument. Its terminal bytes are retained through the
existing attempt-log source; no new collector or provider-text parser is used
for monitoring.

`baton.model-attribution/1` records the original attempt, Job, phase, provider,
requested selector, mapped identity, selected and measured CLI builds, sorted
contributors and their declared source fields, and the exact output hash and
attempt-log locator. It records no usage quantities, generated content or model
roles. Only a complete supported terminal success record contributes models;
unknown fields, prompts, errors and configuration echoes do not.

The mapped identity present among contributors with the exact selected build
is `matched`. An evidenced different identity or build is `conflicting`.
Missing, malformed, partial, oversized or unmeasurable evidence is `missing`.
The host independently checks the frozen claim against the bound selection and
complete retained log before checkpoint publication or verdict recording.
Missing/conflicting/invalid evidence holds the ending and opens no dependent
stage. A passing verifier does not override it. Immutable manager records bind
accepted attribution to its frozen result and checkpoint/verdict.

Publication recovery qualifies the original producing attempt's retained
`result.json` and log, bound to the exact retained output and candidate. The
admission records that evidence; the provider-free publisher carries a digest
reference to it, not a new producer claim. Custody and review handoff recheck
the original bytes and attribution. Replays cannot replace the binding or
repeat publication effects. Legacy recovery takes its previous path.

Status and monitor retain requested/reported/build/outcome diagnostics after
runtime cleanup. An attribution hold reports its typed missing/conflicting/invalid
cause and says owner action is needed; observation creates no owner record. Legacy attempts say `not selected (account default)`.

## Retained home

The manager derives `job-work/<authority-and-Job digest>/<worker digest>/home`
beside instance workspace storage. Structured canonical identities prevent
path interpolation and concatenation collisions. A private manager record
outside the mounted home names its plain authority/Job/worker identity, current
holder and creation state. Only `home` is mounted, at `/run/baton/provider-home`.

Homes are excluded from source, workspace, launch, credentials, context storage
and repository roots. They are not input/output artifacts, custody, or cleanup
roots. Separate Jobs and workers get separate empty homes. Correction and
manager restart retain the same worker's home. A new holder requires positive
runtime cessation and settled cleanup at least as recent as recorded activity.
Unknown or stale evidence defers start for the manager's next ordinary pass.
It does not create an owner-decision item.

A durable preparation ending with no recorded start intent is positive evidence
that this holder never started a runtime. A successor may acquire that home;
the manager refuses any delayed start of the ended attempt, including inside
the start transaction. A requested start without confirmed cessation stays held.

Claude uses a reference to the existing read-only credential delivery. The
shared preparation helper also supports a first-use seed for a future selected
adapter. The host manager resolves the configured source and copies it once,
before launch. It keeps an initialization receipt outside the mounted home;
the helper also keeps path-bound lifecycle metadata inside the home. Later
starts validate those receipts and credential metadata without opening the
credential, source, or source registry. Provider-refreshed contents are preserved.
Missing credentials, damaged/missing receipts, and interrupted initialization
produce an explicit recovery condition; there is no automatic reseeding or
migration of old unmarked seeded homes. A separate Job/worker gets its own seed.
Qualification setup uses `tools.qualification_credentials.prepare_selected`
with a separately selected source configuration, never a manual per-Job copy.
The private selected source configuration is needed only on first initialization;
no source writeback or credential hash is produced. The production managed-entry list
holds exactly the worker-instruction entry described below; the helper replaces
it by exact digest at every start and rejects credential/provider-state
collisions.

Retained home state does not select session resumption. No resume/session
argument is added because a home is nonempty. Diagnostics identify the worker,
holder and retained state; ambiguous session activity remains unknown.

## Worker instructions and execution-context label

Every provider turn under a selected provider policy receives two things from
Baton, and nothing else:

- **Worker instructions.** The exact bytes of `docs/V12-WORKER-INSTRUCTIONS.md`,
  from a byte-identical packaged copy in `provider_policy` (a test fails when
  the two differ). They are the adapter's one managed home entry,
  `.claude/CLAUDE.md` for Claude, placed before the provider starts and
  replaced at every start. Files the provider writes in its home are left alone.
- **Execution-context label.** A short fixed text at the front of the prompt,
  followed by one blank line and the unchanged task prompt. It says the run is
  a native v12 worker, names the launch role (`implementation` or `review`),
  names the worker-instruction file and its digest, and says which host-only
  procedures in the source tree's `AGENTS.md` and `docs/HOST-INTEGRATION.md`
  do not apply. It carries no Job, attempt or protocol identifier.

Baton does not remove or hide the source tree's `AGENTS.md`. The label is how
a worker is told how to treat it. The label states applicability only: it
grants no permission and is not a security boundary.

The label template digest, its role list and the managed entry are members of
the adapter document, so they are inside the adapter digest that admission, the
attempt record and the provider delivery carry. The worker reports the role and
the digest of the label it prefixed; the manager recomputes both from the
admitted adapter and the worker's configured role at the ending. A missing or
different report holds the result as `context-label-missing` or
`context-label-mismatch`, in the same way as an attribution hold, and status
shows the role, both digests and whether the label was reported.

A role outside the list, a changed template, or absent, changed or oversized
packaged instructions refuse before any provider process. An adapter composed
by an earlier build is refused, not reinterpreted. Launches without a selected
provider policy, context-reuse workers and provider-free workers are
unchanged: same prompts, no label, no managed entry.

Delivery covers fresh invocations only. A correction or continuation under a
selected provider policy is a new invocation in the retained home with a
handoff; it is not a resumed conversation and nothing reports it as one.

What deterministic tests show is what Baton composed, placed, passed and
bound. They do not show that the pinned CLI loads the home file by itself, or
that a model read or followed the label. The label names the file so that
delivery does not depend on automatic loading. Model-visible confirmation
belongs to the separately selected qualification turn.

## Evidence and qualification boundary

Deterministic fixtures simulate providers and engines while exercising real
local admission, worker execution, Git fixture repositories, freezing, custody
and handoff. Synthetic path-table fixtures test shared-policy admission; the
production-mapping pipeline also runs with deterministic providers. Neither is
native engine or provider qualification. No container/image/provider
qualification is implied, and existing installations require separately
selected packaging and qualification before native use.

The Claude 2.1.247 `modelUsage` contributor list is **drafted and unqualified**.
The written account in
`work/records/2026/09/finding-v12-production-context-qualification-preparation/review-2026-09-22T03-24-23Z.md`
and that dossier's FINDING entry for run 234686 describe successful terminal
fields with two `modelUsage` keys and no direct model member.
`REVIEW-EVIDENCE-235117.json` records the original output digest and checks;
it does not itself name the field and is not retained raw output.
The original temporary `provider-1.json` (SHA-256
`defc5df0fd333f646e8798c6df68b64bb91cdcf414324dfb3694ad5e7f16c556`)
is unavailable. An attested description and digest do not satisfy raw-output
provenance. The owner explicitly permits this draft for deterministic source
work; **native use remains gated on qualification** that validates the sources
against actual output from the exact CLI build and retains those raw bytes in
the dossier by path and digest. All fixtures are synthetic. Codex has no
qualified participation sources here.

Selected retained-home workers currently leave provider-session activity
unknown: a retained home is not an empty baseline. Home retention does not imply
session resumption. The CLI build is measured by the worker; the host validates
its binding but does not independently run the CLI. The supervised review wrapper,
version-probe format/bound and terminal-size bound still require qualification.


## Codex adapter join: evidence and remaining gates

The Codex adapter and entry use the shared worker lifecycle, instruction label,
managed-entry preparation and result metadata. Its argv and version decoder
are grounded in the retained Codex 0.169.0 offline inventory. Empty prompts,
leading hyphens and exact exec subcommand words refuse before invocation. The
version probe must establish 0.169.0 before a turn can start.

The bound `context_label.roles` is the single role source: Codex serves fresh
implementation only. Composition, configuration revalidation and the worker
check it. The logical delivered credential slot is `codex`; this names the
Baton mount, not the vendor credential file. Claude keeps its existing slot
and legacy context path.

The production Codex realization uses the retained 0.169.0 lookup and selected
successful detached probe: `HOME=/run/baton/provider-home`,
`CODEX_HOME=$HOME/codex`, credential `codex/auth.json`, managed worker instructions
`instructions/WORKER.md`. These are part of the adapter identity. The explicit
prompt label requires reading the delivered instructions; placement does not
claim automatic vendor loading. The closed environment ignores ambient Codex
configuration. Composition supports fresh implementation only. This source
mapping does not qualify a built native worker image or select execution.

The host automatically seeds each new Job/worker home once, from the configured
source registry's exact provider/reference pair. Codex file delivery is explicit
and byte-valued: `UserCredentialSources.resolve_file` preserves every byte,
including whitespace and multibyte content. Delivery, first seed, retained-file
validation and qualification copying all enforce **1 through 1,048,576 bytes**.
An empty file is incomplete. Oversized files refuse without truncation or content
in diagnostics. Legacy string-token bounds and Claude delivery remain unchanged.
Restart preserves refreshed bytes without opening the original source; lost or
invalid initialized credentials require recovery, never silent re-seeding.

Failed first-initialization recovery is an explicit host API, never startup:
`worker_manager.provider_home.recover_failed_initialization(mount, control,
receipt_id=..., decision_id=...)`. Use the exact retained `HomeMount`, its control
store and the external receipt identity. The API checks their admitted selection
and home binding, exclusive home custody, a durable failed-preparation fence
proving no runtime ever started, and an unchanged metadata snapshot of the home.
It does not read credential contents. Legacy incomplete receipts without this
snapshot, changed homes, successful initialization and other runtime states
retain their hold. A directory restored after mutation still has changed ctime.

Withdrawal keeps the original receipt and runtime proof in one immutable
`credential-withdrawal-<receipt_id>.json` beside the home, outside its mount.
Repeated/concurrent identical decisions return that audit. Before transferring
custody, a separately authorized call with the same operands plus
`authorize_retry=<new-decision-id>` records permission for a subsequent first
initialization. Withdrawal alone permits no retry; authorization does not read a
source or launch anything. The next initializer rechecks the snapshot and writes
a new receipt linked to the old receipt and authorization. Normal claim/runtime
and credential-access authority still apply. Never remove receipt files by hand.

Codex 0.169.0 terminal parsing recognizes the retained fresh successful turn
family: thread.started, turn.started, completed agent messages and paired
command_execution items, then one final turn.completed with the evidenced
usage shape. It requires exit zero, a complete bounded UTF-8 JSONL stream,
unique JSON members and consistent item lifecycle. Unknown fields/events,
truncation, unfinished items, nonzero exits and unevidenced failure shapes
remain unclassified. This conservative parser does not claim coverage of other
Codex tools or failure families. Sanitized fixtures retain the observed event
structure; negative mutations are robustness tests, not live failure evidence.

Terminal completion is separate from attribution and candidate acceptance.
The observed stdout contains no participation source. Private session
turn_context.model records CLI configuration only; it is neither contributor
proof nor independently attested backend identity. No session ingestion or
resume behavior is added. The owner-selected Codex exception uses `baton.model-attribution/2`, explicitly
labelled `configured-model`, with `actual_participation: unknown` and empty
contributors. It does not reinterpret `/1` records. The host selects this basis
from the admitted Codex selection; Claude continues to require `/1` participation.
Only build 0.169.0 is qualified for this observation surface; a consistently
renamed build such as 0.172.0 still refuses.

The adapter captures the actual call vector as a safe invocation receipt in
`provider.invocation`: argv prefix, exact prompt UTF-8 digest/length, full argv
digest, producing selection/phase, measured CLI build, context/instruction digest,
validated environment policy and exit status.
It contains no prompt content or private environment paths. This is
adapter-recorded and host-validated, not independently host-observed execution.
The host compares the result claim to that complete retained receipt and validates
the selection, CLI build, immutable image, adapter/profile and attempt bindings.
A missing receipt, image/build/configuration proof, changed receipt or failed/
incomplete supported stdout holds acceptance. Frozen result and ending owners
bind that evidence to the retained candidate; recovery revalidates both streams.

Codex host acceptance additionally requires a retained `baton.launched-image/1`
receipt from exact-container engine inspection at reconciliation. It records
container `Id`, immutable `Image`, positive `State.StartedAt`, assignment labels
(including attempt and generation), admitted image/profile/selection identity
and host recording time. Create argv, labels alone, and a successful start
request do not supply this proof. A fast-exited container can supply positive
start history. A removed container without a retained receipt remains unknown.

When a selected registry digest differs from the engine image/config ID, the
adapter inspects the selected image and requires the same observed `Id` plus a
matching `RepoDigests` digest. This resolution comes from the engine, never the
profile or worker metadata. Unavailable resolution or a different image holds
Codex acceptance. Later absence cannot erase retained proof; contradictory
observations retain the original receipt and record a separate conflict hold.
A later engine resolution may append an immutable supplement bound to the first
receipt; either observation order works before assessment freezes. It cannot
upgrade an already frozen assessment. One attempt means one runtime start:
changed `StartedAt`, including a same-container restart, holds acceptance.
Podman bare hexadecimal image IDs are normalized only from engine inspection.
Contract refusal while retaining evidence records a content-free durable refusal
hold and leaves the lifecycle observation intact. An unwritable control journal
cannot promise persistence of either evidence or lifecycle; it must be repaired
before normal management continues.

The host journal operation locator and receipt digest bind the evidence to the
frozen assessment, ending and original-producer recovery candidate. Recovery
never substitutes the publisher's image. Replay preserves the first receipt;
changed evidence cannot silently upgrade a frozen assessment. These holds do
not change cessation or token-release rules. Claude `/1` and legacy unselected
attempts have no new image-receipt requirement. Diagnostics distinguish admitted
image, engine-observed image, receipt locator and host acceptance. CLI measurement
remains adapter-recorded and host-validated, not independently host-measured.
An unqualified or unknown CLI build has an incomplete reroute observation and
no claim to the qualified 0.169.0 observation surface.

A supported complete exec --json stream with no exact-build mismatch error item
is labelled "no reroute observed". It never proves rerouting absent: missing and
equal server model headers are indistinguishable here. The source-defined
`model rerouted: ... -> ... (HighRiskCyberActivity)` error item refuses acceptance,
even with exit zero and valid configuration. Generated text is not this event.
Another build must requalify the observation surface. JSONL splits only on LF;
legal Unicode separators inside strings remain content. Requested model and service tier never supply
observed participation. Claude terminal and attribution behavior is unchanged.

The selected detached probe established authentication and instruction digest/
role for its selected copy and image, not native worker qualification. Production mapping and deterministic credential recovery/size handling are
implemented. Finished-image/offline engine qualification, editing-turn event
coverage and native joined execution with explicitly qualified Claude remain
outstanding. Actual Codex contributors remain unknown; shared-login/refresh
service behavior is not established by synthetic tests. No new provider call or build is
implied by terminal parsing. Provider-selected
integration is a separate open issue and is not enabled by the Codex guards.
