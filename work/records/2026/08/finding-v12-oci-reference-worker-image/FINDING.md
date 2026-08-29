# Finding: build the OCI reference worker image and entry point

Promoted implementation record for the third bounded child of W5. Its Work is
contained by W5; the top-level dossier is the permanent record required by the
maximum-depth promotion rule.
Canonical Work: W6633.

## Confirmed boundary

Build a digest-pinned OCI image and `baton-worker` entry point using the
deterministic scripted M2 agent. Provider-native code remains opaque inside a
worker image; live provider certification belongs to M4. The worker has no
authority client, host runtime socket, nested runtime, host repository/config/
database access or hidden control channel.

Consent and execution are fresh posture-specific containers under one logical
runtime attempt. Consent receives no assignment, workspace, output or
execution tools. It is positively quiesced/destroyed before the execution
container is created after activation. The consent session is never promoted.

## Acceptance

- Reproducible image recipe with an immutable base/image digest and explicit
  runtime user/entrypoint.
- Protected framed control channel with bounded input/output and no ambient
  authority or engine access.
- Scripted consent, decline, execution, cancellation and fault fixtures.
- Image inspection proves filesystem/user/capability and entrypoint posture;
  secrets and assignment material do not enter image layers.
- Container-level negative tests prove consent cannot reach execution state.

The implementer creates and exclusively owns `PROGRESS.md` when claimed.

## Confirmed `baton.worker-entry/1` contract — 2026-08-25

Exclusive framed stdio attachment is transport isolation, not sufficient
message identity. Every request is one closed object with exactly the common
members `protocol`, `session`, `operation_id`, and `operation`, plus only the
operation-specific members below. `protocol` is exactly
`baton.worker-entry/1`; `session` is the manager-minted identity of this exact
posture-specific container session; and `operation_id` is unique and consumed
once within that session. Wrong-session, duplicate/replayed, missing, unknown
or extra members refuse before the request reaches the agent.

- `describe` has no operation-specific members.
- `consider` has no operation-specific members and exists only in consent.
- `work` has exactly the bounded text member `task` and exists only in
  execution.

Consent and execution use different session identities; an execution session
is never a continuation or promotion of consent. Responses echo `protocol`,
`session`, and `operation_id`. A success has exactly `ok: true` and `answer`;
a fault has exactly `ok: false`, `code`, and bounded `message`. Answer objects
retain their current closed sets: describe reports `protocol`, `posture`,
`operations`, and `environment`; consider reports `contract_digest`,
`decision`, and `reason`; work reports `disposition`, `workspace`, and `recap`.
The whole response remains frame-bounded.

`cancel` is not a worker-entry operation. Cancellation is the manager's
explicit runtime stop/termination path and must be exercised against the real
container; clean EOF from an input stream is not proof of intentional
cancellation.

## Confirmed startup-fault correlation — 2026-08-25

An entrypoint/bootstrap failure that still leaves the framing loop operable is
latched before any agent dispatch. The entrypoint then reads exactly one
bounded request identity envelope and returns the pending failure through the
normal closed fault response, echoing its `protocol`, `session`, and
`operation_id`, before exiting non-zero. Reading the envelope grants no task,
workspace, output, tool, or agent capability; a latched startup failure can
never reach the agent.

A failure that prevents the entrypoint or framing loop from starting cannot
truthfully produce a worker response. The Worker Manager already owns the
launched session and operation identity and settles that case as its own
correlated `worker_start_failed` runtime result from the container-engine
failure. The protocol never invents an uncorrelated startup-response shape.

## Review observations — 2026-08-25 final re-review

**Observed:** The corrected startup path reads one bounded identity envelope,
but returns a latched posture fault before comparing its protocol and session
to this container's expected identity. A wrong-session frame therefore receives
the pending startup fault rather than the contract's session refusal.

**Observed:** The daemon gate builds one image without an explicit platform
and checks only that its ID has digest syntax. It does not reproduce the build
or compare image identities, so the required reproducible pinned-platform
identity remains unproved.

**Observed:** The daemon gate's residual-container query discards every name
with the suite's own prefix before asserting emptiness. The assertion is
vacuous for exactly the resources it claims to detect.

These observations are reviewed in
`review-2026-08-25T07-19-30Z.md`; they do not supersede either confirmed
protocol ruling above.

## Independent fourth-review observations — 2026-08-25

**Observed, P1:** The three preceding corrections landed, but the daemon gate's
real containers do not use the manager adapter's unconditional runtime
restrictions. Channel, inspection and cancellation starts retain only
`--network none`; they omit cap-drop, no-new-privileges, fixed-user argv,
read-only root, resource ceilings and bounded tmpfs posture. A green run proves
the weaker container it launched, not the recorded capability boundary.

**Observed, P1:** The second supposedly independent image build shares the
first build's cache. Changing only the output tag does not force recipe
execution, so equal IDs can prove a cache hit rather than reproducibility.

Two daemon-free additive regressions isolate the argv defects. Full analysis
and correction boundary: `review-2026-08-25T09-47-54Z.md`.

## Independent fifth-review observation — 2026-08-25

**Observed, P1:** Cache isolation is now real, but it exposes that two
independent builds have different OCI image IDs. The correction compares equal
filesystem layers and selected config members instead and adds a test that
requires the image IDs to differ. This does not satisfy the confirmed
reproducible immutable image-digest acceptance or produce the one digest the
manager pins and launches.

The additive daemon-backed identity regression and correction/decision
boundary are in `review-2026-08-25T12-19-50Z.md`. A weaker layer-equivalence
contract requires an explicit approver supersession; implementation prose does
not supersede the confirmed acceptance.

## Implementation decision — 2026-08-25: the recipe has an output step

Recorded by the implementer under the claim that answered
`review-2026-08-25T12-19-50Z.md`. **No supersession of the acceptance is asked
for, and none is needed:** the review offered a deterministic image-output path
as the first way to satisfy it, and that path works on this deployment.

**The acceptance stands as confirmed.** A reproducible recipe with an immutable
image digest, and the digest the manager pins is the one two independent
executions agree on. The three-digest-plus-selected-config contract the
previous correction substituted is withdrawn.

**The record's measurement was incomplete, and correcting it is most of this
decision.** The record said two `--no-cache` builds differ only in the config's
wall clock, with the layers identical. They differ in four places, and the
fourth is the recipe's OWN LAYERS: `COPY x /opt/baton/x` writes a tar carrying
the directory entries the copy created, and their mtime is the build clock at
one-second resolution. The earlier reading was an accident of timing — two
builds inside one second agree, two that straddle a second do not. That also
explains the interaction the previous correction reported and could not
attribute, where two container cases passed alone and failed in a slower full
run.

**So the build is `docker build` followed by a normalizing output step**, in
`v12/python/tools/worker_image.py`. The engine builds under a staging tag; the
saved OCI layout has its receipt metadata normalized; the result is loaded
back, and the identity of that image is what the manager pins. An operator
reaches it the same way the gate does, through
`python3 -m tools.worker_image --tag …`, which prints the digest.

**What is normalized is only ever this recipe's own work, and the boundary is
derived from the pinned base rather than counted:**

- a layer is the recipe's when its diff id is not one of the base image's;
- a history entry is the recipe's when it is newer than the base's `Created`.

The base image's layers and provenance travel byte for byte. A normalizer that
rewrote them would be describing a different base from the one the recipe pins,
which is exactly what the digest pin exists to protect. Inside a rewritten
layer only DIRECTORY mtimes move: a regular file keeps the mtime it had in the
build context, because that is content the recipe carries rather than a clock
reading.

**The artefact is therefore the normalized image, not the engine's staging
output.** The staging tag is the tool's own, is derived from the target tag so
two builds cannot stage over each other, and is removed on every path. An image
nobody normalized is not what the manager pins.

**Removed from the recipe's claim, and named so the absence is deliberate:**
nothing about registries, signing or attestation. This produces one local image
identity for one pinned platform; publishing it is not this Job's.

## Independent sixth-review observations — 2026-08-26

**Observed, P1:** The normalizer does not establish that the built image
actually descends from the pinned base before it rewrites layers and certifies
a new digest. `_base_facts` discards the base layer order into a set, and
`normalize_layout` accepts any non-empty, non-total overlap. A layout containing
only one of two claimed base layers is therefore accepted. Set membership is
not ancestry; the built diff-id sequence must begin with the pinned base's
complete ordered sequence before every suffix layer can be called the recipe's.

**Observed, P1:** The recorded claim that concurrent builds cannot stage over
each other is false. `staging_tag(tag)` is exactly
`f"{tag}-unnormalized"`, so two invocations for the same destination share one
mutable engine tag. Either can save the other's build or remove that tag while
the other still needs it. Each invocation needs its own staging reference and
must clean up only that reference.

Two daemon-free additive regressions reproduce both failures. Full analysis
and correction boundary: `review-2026-08-26T00-41-16Z.md`.

## Independent sixth-review findings — 2026-08-26

**Observed, P1.** `_base_facts` returned a set of the base's diff ids and
`normalize_layout` treated set membership as ancestry, so a built layout
carrying one of two claimed base layers and not the other was accepted, its
remaining layers rewritten, and a digest returned as though the pinned base had
been established.

**Observed, P1.** `staging_tag` derived one mutable tag from the destination
alone, so two simultaneous builds for one destination shared it: either could
save the other's un-normalized image, and either cleanup could delete the tag
before the other had saved it.

Full analysis in `review-2026-08-26T00-41-16Z.md`.

## Implementation decision — 2026-08-26: ancestry is a prefix, the stage is an allocation

Recorded by the implementer under the claim that answered the sixth review.
Both correct the transformer the fifth correction added; neither supersedes the
deterministic-output decision itself.

**Ancestry is an ordered prefix.** An image descends from a base by carrying
that base's layers, in that base's order, at the FRONT. The base's layers are
kept as an ordered sequence — the engine already reports them in order — and
the built image must begin with that exact sequence, with at least one
recipe-owned suffix layer, before anything is rewritten. The recipe's layers
are then the suffix, taken by POSITION, which is stricter than membership in a
way membership could never be: a recipe layer whose digest happened to equal a
base layer's is still the recipe's, because of where it is.

**The staging reference is allocated per invocation, not derived from the
destination**, and it is threaded through build, save and cleanup.
`build_vector` takes it as an operand rather than deriving it, because a vector
that allocated its own would name a reference its caller could not save, remove
or read back — the same defect wearing a different hat. The destination stays in
the readable prefix so a leftover stage says which artefact it was on its way to
being.

**Both docstrings claimed the property they lacked** — "so two builds running at
once do not stage over each other" was written above the code that made them
share one tag. That is worth recording on its own: a comment asserting the
guarantee is what made the absence easy to miss in two reviews.

## Independent seventh-review observations — 2026-08-26

**Observed, P1:** The normalized image identity still includes regular-file
mtimes from the build context. Git does not preserve file mtimes, so two fresh
checkouts of identical worker bytes can produce different normalized layer and
image digests. The current two-build gate reuses one checkout and cannot expose
this. Reproducibility must remove ambient checkout clocks from every
recipe-owned tar member, not only directory entries.

**Observed, P1:** The per-invocation stage is removed through an unchecked
`subprocess.run`. If the engine refuses that removal after a successful load,
`build_worker_image` returns the pinnable identity anyway while its mutable,
unnormalized staging image remains. The tool's remove-on-every-path guarantee
must be an enforced success condition, not a best-effort side effect.

Two daemon-free additive regressions reproduce both failures. Full analysis
and correction boundary: `review-2026-08-26T02-37-11Z.md`.

## Independent seventh-review findings — 2026-08-26

**Observed, P1.** `_normalized_layer` replaced only directory mtimes and
explicitly treated a regular file's build-context mtime as content, so two
fresh checkouts of one revision produced two image identities.

**Observed, P1.** `build_worker_image` removed its staging image in `finally`
and discarded the result, so a refused removal left the mutable un-normalized
image under a readable tag while the function returned a pinnable identity.

Analysis in `review-2026-08-26T02-37-11Z.md`, which also gives explicit
confirmation to revise the file-mtime assertion.

## SUPERSEDED — the mtime half of the 2026-08-26 output-step decision

The decision recorded above for this Work said:

> **Inside a rewritten layer only DIRECTORY mtimes move.** A regular file keeps
> the mtime it had in the build context, because that is content the recipe
> carries rather than a clock reading.

**That is superseded as of 2026-08-26.** The build context is a checkout, and a
checkout does not pin mtimes: the version-control source carries file bytes and
the executable bit and nothing about when a working tree was populated. Two
fresh checkouts of one revision therefore produced two identities, which is the
ambient-clock dependency the whole output step exists to remove.

The superseded text is kept because the distinction it drew is the instructive
part: I separated "the copy created it" from "the context supplied it", and the
line that matters is **what the source of truth actually pins**. It pins
neither.

**Every member time in a recipe-owned layer is normalized now**, and nothing
else is: bytes, mode, link target, ownership ids and member order are content
and survive. Everything else in the output-step decision — ordered-prefix
ancestry, the allocated stage, the base travelling byte for byte — stands
unchanged.

## Implementation decision — 2026-08-26: cleanup cannot report success

A refused staging removal is now a failure of the build that reports it, and
the raise is placed after the `finally` so an earlier failure stays primary: a
build that failed and then could not clean up is reported as the build failure
it is, with the cleanup evidence in the log rather than replacing it. Only a
run that completed build, save, normalize and load turns a refused removal into
its own failure, because that is the run whose success would otherwise be a lie.

## Independent eighth-review observations — 2026-08-26

**Confirmed, blocking contract supersession:** The approved artifact-neutral
worker boundary in
`work/records/2026/08/finding-v12-isolated-agent-workers/FINDING.md` and its
PLAN requires the OCI worker to receive read-only `/input` with `input.json`
and declared payloads, writable `/output`, and private ephemeral space, then
publish `/output/output.json` last. Git and other artifact semantics belong to
workers, drivers and manifests, not the host Worker Manager. The umbrella PLAN
explicitly orders revision of the older worker-control/conformance contracts
before OCI reference-worker or host-manager implementation.

The current reference worker still consumes an inline `task` frame, exposes
`BATON_WORKER_ASSIGNMENT`, `BATON_WORKER_WORKSPACE` and
`BATON_WORKER_OUTPUT`, and returns a `workspace` member. It neither consumes
`/input/input.json` nor publishes `/output/output.json`. Those surfaces certify
the superseded contract and cannot be signed off or corrected piecemeal before
the prerequisite contract revision is pinned.

That prerequisite is ledger Work `W14251`; `W6633` is blocked on it.

**Observed, P1:** The seventh cleanup correction handles a nonzero staging
removal only after the protected build completed. When an earlier build step
already failed, a nonzero removal result is discarded without the promised
actionable evidence. If `subprocess.run` itself raises while removing the
stage, its exception replaces the earlier build failure. Two daemon-free
additive regressions reproduce both paths. Full analysis and correction
boundary: `review-2026-08-26T04-26-30Z.md`.

## Independent ninth-review outcome — 2026-08-26

**Confirmed corrected:** staging cleanup no longer replaces or hides the
primary build failure. `_cleaned_up` converts either a nonzero removal or a
raised removal exception into bounded actionable evidence; the protected
failure retains primacy and carries that evidence as a note, while the same
cleanup outcomes on an otherwise successful path prevent an image identity
from being returned. The three cleanup regressions and the retained
daemon-free image gates pass independently.

**Confirmed, required implementation remains:** ledger Work `W14251` is now
closed satisfying and no longer blocks this Work, but the reference worker
still implements the superseded boundary: `work` requires inline `task`, the
execution posture exposes `BATON_WORKER_ASSIGNMENT`,
`BATON_WORKER_WORKSPACE`, and `BATON_WORKER_OUTPUT`, the scripted agent reads
those values, and the answer returns `workspace`. There is still no consumer
of `/input/input.json` and no last, atomic publisher of
`/output/output.json`.

The following is the controlling reference-worker slice derived from the
closed W14251 contract. It supersedes only the old worker I/O members; the
common protocol/session/operation identity, posture separation, replay fence,
framing, bounded faults, and consent behavior remain live:

1. A `work` frame carries only the common identity envelope. It carries no
   inline assignment or `task`; the execution worker reads the assignment
   manifest from the fixed, read-only `/input/input.json` path and validates
   its schema and expected assignment/session binding before dispatch.
2. The execution environment is the consent environment set. The three
   assignment/workspace/output variables named above are removed; fixed
   `/input`, `/output`, and private ephemeral locations are the only worker I/O
   topology.
3. The scripted agent receives the validated assignment content it needs and
   reports only a disposition, recap, and the names of outputs it produced. It
   does not choose host paths, return a workspace, or author the completion
   envelope.
4. The worker cross-checks those output names against the assignment's closed
   output declarations, measures each declared result beneath `/output`, and
   authors the W14251 `completionManifest` itself, including the required
   assignment reference, disposition, and per-output name, type, path, status,
   content manifest, and result metadata.
5. `/output/output.json` is published last and atomically through a private
   same-directory temporary name followed by rename. Its presence is the
   completion signal; refusal, validation failure, interruption, or partial
   output must never expose a completion manifest.
6. The correlated `work` answer is exactly `disposition`, `outputs`, and
   `recap`; `outputs` is a bounded list of output names. Ephemeral material is
   never a result unless the agent placed it under a declared output and the
   worker measured it before publishing completion.

Full independent review and verification evidence:
`review-2026-08-26T21-11-48Z.md`.

## Independent tenth-review outcome — 2026-08-26

**Confirmed partial implementation:** the execution worker no longer accepts an
inline task or publishes a workspace answer, the three obsolete worker I/O
environment variables are absent, and completion publication uses a private
same-directory temporary file followed by rename. Those are necessary parts of
the ninth-review contract, but the slice is not yet conformant or reviewable as
a whole.

**Confirmed, P0 contract gap:** the W14251 `inputManifest` deliberately contains
`work_ref` and no assignment generation, while its separate
`assignmentManifest` owns the complete `assignment_ref`; the execution contract
standardizes only `/input/input.json` and `/output/output.json`. The current
worker nevertheless requires a complete `assignment_ref` inside `input.json`.
That invented input document is neither a schema-valid `inputManifest` nor a
document supplied by the closed contract, and no remaining work-frame or
environment member can provide the identity required in the worker-authored
`completionManifest`. A canonical valid input-manifest vector is therefore
refused before the agent runs. The contradiction is now the durable follow-up
`work/records/2026/08/finding-worker-completion-assignment-identity/` and ledger
Work `W19784`; this Work is blocked on that decision and contract correction.

**Confirmed, P1 response defect:** the correlated `work` answer's `outputs`
member contains complete per-output completion records rather than the pinned
bounded list of output names. The agent's name-only report must remain distinct
from the completion manifest authored and published by the worker.

**Confirmed, P1 declaration-enforcement defect:** the worker accepts only a
small open subset of each output declaration and measures results without
enforcing the declaration's constraints. In the additive regression, a file
larger than the declared one-byte ceiling still produces success and publishes
`output.json`. Once W19784 fixes the source of assignment identity, the worker
must validate the exact canonical manifest fields it consumes and enforce the
closed declaration, path, required-output, entry-count, and byte limits before
completion becomes visible.

**Confirmed, acceptance gate not met:** the implementer reported the primary
direct suite red at 52/58 and left the daemon-backed container suite untouched
and unrun. Independent execution reproduced the original six failures; the
three new contract regressions bring the module to 61 tests with five failures
and four errors. There is no built-container evidence for the actual read-only
input mount, writable output mount, private ephemeral area, absence of obsolete
environment members, or atomic-last publication. Full analysis and exact
evidence: `review-2026-08-26T22-31-32Z.md`.

## Approved resolution of the tenth-review contract gap — 2026-08-26

The P0 uncertainty above is **superseded as an open decision**, not erased as
history. W19784 approved the existing complete `assignmentManifest` at fixed
read-only `/input/assignment.json`, alongside unchanged pre-claim
`/input/input.json`. The manager materializes it after claim and before the
execution input root becomes observable; consent sees neither document.

The reference worker now has one exact completion-identity source: validate
both closed manifests and their cross-document bindings before agent dispatch,
then copy `completionManifest.assignment_ref` only from `assignment.json`.
There is no environment, framed-request or compatibility fallback. W6633
remains blocked until W19784 implements and verifies that approved contract;
the name-only result, declaration-limit, stale fixture and built-container
findings from the tenth review remain independently live.

## Independent eleventh-review outcome — 2026-08-27

**Confirmed corrected:** W19784 is closed satisfying. The worker consumes the
two fixed manager-authored documents, validates their closed top-level shapes,
self-digests and cross-document bindings before dispatch, and copies the
delivered complete assignment identity into the completion envelope. The P0
dependency from the tenth review is resolved.

**Confirmed, P1:** the correlated `work` answer still returns the complete
worker-output records instead of the pinned bounded list of output names.

**Confirmed, P1:** declared output constraints remain ignored. A one-byte
ceiling accepts the scripted 34-byte result and publishes completion.

**Observed, P1:** declaration paths are joined without validating normalized
relative syntax or containment. The additive `../tmp/escaped` regression
writes outside `/output` into the private ephemeral tree, then publishes a
completion manifest and success frame. Exact analysis and evidence:
`review-2026-08-27T02-43-39Z.md`.

## Independent twelfth-review outcome — 2026-08-27

**Confirmed corrected:** the eleventh review's names-only response, declared
entry/byte ceilings, relative-path grammar, containment, overlap and reserved-
manifest findings are materially corrected. The retained daemon-free gate is
156/156 green and implementer evidence records the built-container gate 41/41.

**Observed, P1:** the new declaration proof derives member names but does not
enforce the frozen value types and maxima it consumes. Seven schema-invalid
descriptor/constraint values all reach the agent instead of refusing before
dispatch.

**Observed, P1:** `measured()` inspects symlinks only in the `files` list from
`os.walk`. A directory symlink is silently omitted, after which the worker
publishes completion and returns success despite `link_policy: forbid`.

Full analysis and exact evidence:
`review-2026-08-27T03-14-22Z.md`.

## Operator checkpoint after the twelfth correction — 2026-08-27

Finish only the correction already claimed in response to the twelfth review,
then return W6633 for one independent review. At the end of that review the
reviewer passes W6633 to `baton.ops` regardless of whether the verdict is clean
or requests more changes. It must not pass back to `baton.impl`, and K must not
start a thirteenth correction round before the approver reviews the accumulated
scope and evidence.

This is scope control, not a claim that the active implementer is stuck. The
Work has already crossed twelve review rounds; another automatic review-to-impl
loop would conceal the need to decide whether the remaining boundary is worth
finishing for the first Docker proof.

## Independent checkpoint-review outcome — 2026-08-27

**Confirmed corrected:** every consumed output descriptor and constraint value
is held to its shipped frozen rule before agent dispatch, including JSON types,
const, pattern, lengths, maxima/minima, unique array items, item rules and the
validator-digest `oneOf`. Unsupported rule keywords fail closed. Directory
symlinks now participate in the same whole-tree refusal as file symlinks.

The two retained reviewer regressions and complete 162-case daemon-free cut are
green. Implementer evidence records the expanded built-container gate 43/43;
the managed reviewer could not independently open the Docker daemon and did
not escalate. No new defect was found in the twelfth correction.

Per the mandatory operator checkpoint, this accepts the correction but does
not terminally sign off the accumulated twelve-round Work. W6633 passes to
`baton.ops` for an accept/narrow/split/stop decision and must not begin another
implementer round without that authorization. Full review:
`review-2026-08-27T03-40-23Z.md`.

## Approver closure ruling — 2026-08-27

W6633 closes **satisfying**. The checkpoint review found no new defect, the
complete daemon-free cut is 162/162 green, and the implementer's self-cleaning
Docker gate records 43/43 green. The Work now supplies the deterministic,
restricted OCI reference image and artifact-neutral worker entrypoint required
for the first live Docker proof.

This ruling does not certify the broader manager lifecycle, credential
recovery, or end-to-end orchestration. W6636 owns lifecycle composition and
W17110 owns the live ping-pong proof; a failure there becomes separately
bounded Work rather than reopening this twelve-round campaign.

## 2026-08-28 — primary image identity preserved under W33936

Approver response M34630 does not change this image's `USER 65532:65532` or
the adapter's matching primary `--user 65532:65532`. W33936 may grant one
deployment-configured, nonzero, non-authority workspace group as supplementary
execution-only authority after proving the mounted workspace carries it.
Consent receives no such group. The extra runtime group is an adapter/workspace
capability and never an image-default identity, so the exact primary alignment
this record accepted remains live.
