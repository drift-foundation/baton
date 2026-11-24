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
adapter: once present, its private credential is never opened, compared,
replaced or copied outward by later starts. The production managed-entry list
is empty. Its helper supports exact digest-bound replacement and rejects
credential/provider-state collisions for separately selected instruction work.

Retained home state does not select session resumption. No resume/session
argument is added because a home is nonempty. Diagnostics identify the worker,
holder and retained state; ambiguous session activity remains unknown.

## Evidence and qualification boundary

Deterministic fixtures simulate providers and engines while exercising real
local admission, worker execution, Git fixture repositories, freezing, custody
and handoff. A simulated Codex realization tests shared-policy admission only;
it is not a Codex implementation or qualification. No container/image/provider
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
