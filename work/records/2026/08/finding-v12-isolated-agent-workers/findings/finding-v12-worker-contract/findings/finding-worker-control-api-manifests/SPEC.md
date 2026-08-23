# Baton worker-control and manifest contract

Version: `1.0-design`  
Protocol family: `baton.worker-control`  
Manifest family: `baton.worker-manifest`  
Status: proposed normative design for W1439; not an implementation or wire
compatibility promise until approved.

**Amended 2026-08-22 by the W4487 decline ruling.** The frozen decline shape
below — `claim_token: null` — contradicted W151 `1-ruled` §7, which required
the bearer. The approver kept THIS shape and superseded W151. Nothing in this
document's schema or vocabulary changed; §0, §6.1, §12 and §13 now state the
authorization that replaces the bearer, and the evidence gained one valid and
two invalid decline vectors plus five model tests. See
`work/records/2026/08/finding-worker-control-decline-token-conflict/`.

**Amended a third time 2026-08-22 by that Work's re-review.** The
operation-signature payload said a bearer rides as "the verifier the manager
already holds" and its model computed a DIFFERENT value from the one W151
stores for the same token. §4.2 now names W151's exact derivation rather than
implying a second one; a golden bearer is pinned in both executable models and
the conformance package asserts they agree. Also a clarification, not a
supersession.

**Amended again 2026-08-22 by that Work's independent review.** §4.2 said the
operation signature is "the canonical digest of the operation kind and every
effective durable operand" and left the payload for each implementation to
guess; the new decline vector guessed the body digest, and nothing validated
it. §4.2 now FIXES the payload exactly, and §12 rule 9 states the
recomputation a receiver performs. This is a clarification of a rule that was
already normative, not a supersession: no document that satisfied the old
sentence as written stops being conformant. One consequence is new, and it is
called out where it lives — a `claim_token` operand enters the payload as its
verifier digest rather than literally, which §4.2 explains.

## 0. Scope and precedence

This contract specifies the transport-independent boundary between the trusted
Worker Manager and worker/runtime components, plus the durable manifests and
receipts exchanged with trusted verification and integration components. It
does not specify Baton Work scheduling, an ACP session protocol, Docker,
Podman, SSH, a provider API, a filesystem layout, or canonical Git mutation.

The signed-off W151 assignment contract at
`../../finding-v12-assignment-state-machine/SPEC.md` owns assignment identity,
claim generation, effectively-once settlement, cancellation fencing, typed
gates, immutable workflow receipts and the authority/control-store/artifact
ownership split. If this document conflicts with W151, W151 wins and this
design must be revised. This contract gives those facts wire and artifact
shapes; it does not create a second state machine.

**One conflict has been ruled the other way, explicitly (W4487,
2026-08-22).** W151 `1-ruled` §7 required a declining worker to present the
exact unspent claim token; §6.1 below carries the token for acceptance only
and `schema/worker-control-1.0.schema.json` mechanically requires
`claim_token: null` when `decision=decline`. Both contracts were frozen, so
no implementation choice could satisfy both. The approver kept this
document's non-secret decline envelope and superseded W151's token
requirement for decline; the dated supersession is written into W151 §1 and
the decision is recorded at
`work/records/2026/08/finding-worker-control-decline-token-conflict/`. The
general precedence rule above is unchanged — a ruling settled this one
conflict, and nothing here may settle the next one on its own authority.

The accepted `v12/` proof remains valid inside its explicit `0-spike` scope.
This design supersedes only these prototype choices for later work:

- `version: "0-spike"` becomes the negotiated protocol and manifest families
  below;
- authority-local `W…` selectors become full structured `work_ref` values;
- constant `generation: 1` becomes the authority-minted full
  `assignment_ref`;
- permissive extra fields become sealed core objects plus negotiated extension
  bags; and
- shallow type checks become the schema and semantic validation rules below.

No product, authority, runtime, adapter or schema migration is authorized by
this document.

## 1. Trust and component roles

The same JSON shapes cross different trust boundaries, so component role is
explicit and never inferred from transport location.

| Role | May assert | May not assert |
| --- | --- | --- |
| `worker-manager` | normalized observations, assignment projections read from the authority, operation results it settled, manager-observed ordering/time | a claim or receipt the authority did not commit; runtime death it did not prove |
| `worker-endpoint` | offer decision, activity, completion/inability intent, declared output paths | claim success, canonical Work phase, quiescence, accepted proposal or integration |
| `runtime-adapter` | start/cancel/inspect/collect/destroy observations about one opaque runtime | Baton authority state, proposal acceptance, portable semantics from engine-specific status |
| `verifier` | raw observation for one exact proposal/candidate/target and evidence | technical acceptance, approval or integration |
| `reviewer` | immutable technical-review receipt | verification observation, approval or canonical write |
| `approver` | immutable approval receipt | verification or integration |
| `integrator` | one compare-and-swap attempt and immutable receipt | conflict resolution, proposal editing or automatic Work close |

The Worker Manager is the only Baton authority client. A worker, adapter,
verifier or remote host never receives the Baton database, configuration,
executable or canonical write credentials merely because it speaks this
protocol.

## 2. Version and capability negotiation

### 2.1 Independent version axes

Protocol and manifests have separate exact versions:

```json
{
  "protocol": "baton.worker-control",
  "version": { "major": 1, "minor": 0 }
}
```

```json
{
  "schema": "baton.worker-manifest/input",
  "version": { "major": 1, "minor": 0 }
}
```

`assignment_contract: "v12-assignment-1"` is a third, authority-owned axis.
None substitutes for another.

### 2.2 Exact selection, no optimistic downgrade

Each connection begins with `control.hello`; the manager answers
`control.welcome`. Both list exact supported `(major, minor)` pairs rather than
ranges. The selected pair must appear in both lists. No common pair is
`refused.unsupported-version`; neither peer guesses compatibility or silently
downgrades.

Major versions change core meaning or required fields. A minor version may add
new message kinds, manifest schemas or capabilities, but never changes an
existing field's meaning. A peer speaks a minor version only when it implements
that exact schema. Core objects remain sealed at every minor version; additive
vendor or experimental data belongs only in a negotiated extension.

### 2.3 Capabilities and extensions

Capabilities use lowercase dot-separated names. Version 1.0 defines these
portable capabilities:

- `core.offer`
- `core.assignment`
- `core.runtime-lifecycle`
- `core.activity`
- `core.output-freeze`
- `core.proposal`
- `core.receipts`
- `core.errors`

A peer advertises only behavior it can actually perform in its declared role.
The welcome selects an intersection. A message requiring an unselected
capability is `refused.capability` before side effects.

`core.errors` is mandatory for every 1.0 connection. The remaining operation
mapping is closed: offer operations require `core.offer`;
`assignment.activate` requires `core.assignment`; runtime start, inspect,
cancel and destroy require `core.runtime-lifecycle`; activity requires
`core.activity`; result declaration, freeze, collection and retention require
`core.output-freeze`; proposal publication requires `core.proposal`; and
exchange of any workflow receipt requires `core.receipts`. A 1.0 Worker
Manager supports all eight; a narrower peer supports `core.errors` plus every
capability needed by the kinds it sends or receives.

Extensions use reverse-DNS keys in an explicit `extensions` object, for
example `org.example.runtime-metrics/1`. The hello exchange lists exact
extension names and versions. Sending an unnegotiated extension is
`refused.extension`; recipients never ignore a safety-relevant field merely
because it was placed in an extension bag. Extension values are JSON values
bounded by the negotiated byte limit and cannot alter identity, operation
signature, capability, lifecycle, digest, disposition or receipt meaning.

Unknown top-level or core-object fields are `integrity.schema`. There is no
protobuf-style unknown-field preservation in version 1.0.

## 3. Encoding, canonicalization and limits

### 3.1 JSON and transport

The portable encoding is UTF-8 JSON. Transport provides authenticated,
confidential, integrity-protected message delivery and explicit frame
boundaries. It may be stdio, a local socket, a secured network stream or a
store-and-forward channel. Transport connection, process identity, FIFO order
and reachability grant no Baton authority.

Delivery is at least once. Messages may be duplicated, delayed or observed
after reconnect. Mutating meaning therefore comes from `operation_id` and its
full signature, not from transport request IDs or ordering.

The negotiated limits include `max_frame_bytes`, `max_extension_bytes`,
`max_artifact_bytes`, `max_manifest_entries` and `max_activity_bytes`.
Receivers count encoded UTF-8 bytes before parsing nested untrusted content and
refuse over-limit input without partial action.

### 3.2 Canonical JSON and digests

Durable JSON digests use RFC 8785 JSON Canonicalization Scheme bytes and SHA-256:

```text
sha256:<64 lowercase hexadecimal digits>
```

All schema integers are non-negative JSON safe integers unless stated
otherwise. Floating-point values, `NaN`, infinity and negative zero are
forbidden in durable manifests. Timestamps are UTC RFC 3339 strings with
millisecond precision, for example `2026-08-21T22:00:00.000Z`; timestamps are
evidence, never ordering or authorization.

`body_digest` is the SHA-256 digest of canonical `body`. A manifest's
`manifest_digest` is computed over that whole manifest with the
`manifest_digest` member omitted. Artifact `content_digest` is computed over
the exact artifact bytes and is never a digest of its locator.

### 3.3 Paths, URIs and content trees

Portable workspace paths are normalized POSIX-relative paths. They are
non-empty, use `/`, contain no empty, `.` or `..` segment, are not absolute,
and contain no NUL. A path names a logical role inside one private assignment
workspace, not a host path.

Source URIs are absolute normalized URIs. They contain no userinfo, credential,
bearer token or fragment. Query strings are forbidden in durable source URIs
because they routinely carry signed credentials or unstable selection
parameters. URI scheme describes transport only; source `type` selects
semantics.

Directory content manifests sort entries bytewise by normalized relative
path. Each entry carries path, byte length and content digest. Entries are
regular files only in version 1.0; links, devices, sockets, FIFOs and reparse
points refuse. The tree digest is over the canonical ordered entry array.

## 4. Durable identities

### 4.1 Work and assignment

```json
{
  "authority_uuid": "43c55d4b00ee85c84ae4ed134de36df5",
  "work_id": "43c55d4b-W1439"
}
```

The Work ID is the full canonical ID, not `W1439`. Its eight-hex authority
prefix must equal the first eight characters of `authority_uuid`.

```json
{
  "work_ref": {
    "authority_uuid": "43c55d4b00ee85c84ae4ed134de36df5",
    "work_id": "43c55d4b-W1439"
  },
  "participant": "baton.codex",
  "generation": 7
}
```

Generation is a positive authority-minted integer under a v12 assignment
contract. `offer_id`, `runtime_attempt_id`, `runtime_id`, `message_id`,
`event_id`, `result_id`, `proposal_id`, receipt IDs, readiness episode,
configuration generation and provider session IDs are separate opaque
identities with no claim authority.

### 4.2 Operations

Every mutation carries:

```json
{
  "operation_id": "opaque caller-stable identifier",
  "signature_digest": "sha256:..."
}
```

The signature is the canonical digest of the operation kind and every
effective durable operand, including full identities, digests, disposition,
reason, rationale and outcome prose. Transport correlation, retry count and
diagnostic timestamps are excluded.

**The payload is exact (clarified 2026-08-22, W4487 review).** Two peers that
compute a signature differently do not share an identity at all, so the bytes
are fixed here rather than left to each implementation:

```json
{ "kind": "<envelope kind>", "operands": { "<durable body operands>": "..." } }
```

taken over the §3.2 canonical encoding. Three consequences are worth stating
because implementations get them wrong in opposite directions:

- The KIND is inside the identity. The signature is therefore never the body
  digest: `output.freeze` and `output.collect` carry the same body, and one
  operation id reused across the two must collide rather than replay.
- `extensions`, `message_id`, `correlation_id`, `sent_at` and `sender` are
  outside the payload. §2 already forbids an extension from altering the
  operation signature; the rest are the transport correlation this section
  excludes.
- A bearer operand enters the payload as its VERIFIER digest, never
  literally. A signature is durable — it lands in the manager's operation
  journal and in W151's — and §13 keeps the claim bearer off every durable
  surface. Dropping the bearer instead would make an accept under a reused
  operation id with a DIFFERENT token an exact replay rather than a
  collision, which contradicts "every effective durable operand"; carrying it
  literally would put the one deliberate secret into durable state. So
  `claim_token` contributes `claim_token_verifier`, and `null` stays `null` —
  a decline's signature commits to the ABSENCE of a bearer exactly as
  positively as an accept's commits to which one was presented.

  **That verifier is W151's, and it is one exact value (clarified
  2026-08-22, W4487 re-review).** W151 owns the offer record, so it owns the
  derivation; this contract names it rather than defining a second one:

  ```text
  claim_token_verifier = "sha256:" + lowercase hex of SHA-256 over the
                         bearer's own UTF-8 bytes
  ```

  The token's own bytes, not a JSON encoding of them — hashing the encoding
  would bring quotes and escaping rules into the value, so two peers that
  escape a character differently would derive different verifiers, and hence
  different operation signatures, for the same acceptance. That is exactly
  what happened between the two models before this clarification, and it is
  the ambiguity the rest of §4.2 exists to remove. The value is the one the
  manager already stores for the offer (§6.1), so a receiver validates a
  signature without ever holding the bearer.

A RECEIVER of a mutating command recomputes this digest and refuses
`integrity.digest` on a mismatch, before the operation is journalled. A REPLY
is exempt from the recomputation: it carries the same operation as the request
it answers, so its `signature_digest` is the REQUEST's and its body is a
result rather than the operands; a reply's operation identity is proved by
correlation to a request whose signature was already validated.

An exact retry returns the committed result byte-for-byte. Reusing an ID with
a different signature is `refused.operation-collision` and changes nothing.
An authority operation may be `unsubmitted`, `committed`, durably `refused`,
or `retired` as W151 defines. A manager-owned mutation also has a durable
control-store operation record. Success at one boundary does not imply success
at the other; reconciliation queries both exact records.

## 5. Control envelope

Every frame has this sealed shape:

```json
{
  "protocol": "baton.worker-control",
  "version": { "major": 1, "minor": 0 },
  "message_type": "command",
  "kind": "runtime.start",
  "message_id": "01J5V12M1EXAMPLE",
  "correlation_id": null,
  "sent_at": "2026-08-21T22:00:00.000Z",
  "sender": {
    "role": "worker-manager",
    "instance_id": "manager-incarnation-9"
  },
  "operation": {
    "operation_id": "start:attempt-7",
    "signature_digest": "sha256:..."
  },
  "body_digest": "sha256:...",
  "body": {},
  "extensions": {}
}
```

- `message_type` is `command`, `reply` or `event`.
- Commands that may mutate require `operation`; pure hello/inspect commands
  set it to `null`.
- Replies carry the request's `correlation_id` and the same operation or null.
- Events set `correlation_id` and `operation` to null. Their body carries a
  source event ID and sequence; the manager adds its own observation sequence
  when it persists the normalized event.
- `message_id` deduplicates frames only. It cannot settle an operation.
- `sent_at` and `sender.instance_id` are diagnostics only.
- `body_digest` is checked before any body field is trusted.

## 6. Portable operation surface

### 6.1 Negotiation and offer

| Kind | Direction | Required body | Durable effect |
| --- | --- | --- | --- |
| `control.hello` | peer -> manager | role, supported exact versions, capabilities, extensions, limits, profile digest | none |
| `control.welcome` | manager -> peer | selected exact version, capabilities, extensions and effective limits | none |
| `offer.issue` | manager -> worker endpoint | `offer_id`, `runtime_attempt_id`, `work_ref`, human-contract digest/summary, input metadata, declared output metadata, policy/profile digests, expiry and ephemeral `claim_token` | manager already has durable offer verifier; raw token frame is never persisted |
| `offer.decide` | worker endpoint -> manager | exact offer/runtime/work binding, `decision=accept|decline`, reason, and the token for ACCEPT ONLY — `claim_token` is `null` for a decline | manager performs the W151 offer CAS; no claim or writable capability yet |

The claim token is the one deliberate secret field in the control protocol. It
is carried only on an ephemeral protected channel, marked `sensitive`,
redacted from logs/traces/errors, and never enters a persisted envelope,
manifest, event, artifact reference or operation result. The durable offer
record holds only its verifier/digest and binding.

**A decline carries no bearer, and that is now ruled rather than implied
(W4487, 2026-08-22).** Acceptance presents the exact unspent, unexpired
token because it is about to gain authority. A decline is authorized by the
integrity-protected envelope itself: the `offer.decide` body is bound to
`(offer_id, runtime_attempt_id, work_ref, decision, reason)`, the envelope
carries its `body_digest`, and the manager validates that whole binding
against the issued offer before consuming its durable verifier. That
consumption is what makes a decline terminal for the token — after it, no
bearer validates against that offer, exactly as after an acceptance — and
no claim is minted and no participant capacity is taken.

The two decisions therefore prove themselves differently on purpose. An
acceptance proves POSSESSION of the secret; a decline proves the exact
IDENTITY of the offer it is ending, which is all a terminal act on an offer
needs. Transmitting a secret in order to refuse authority would widen the
one deliberate secret's exposure and buy nothing. A stale, foreign,
differently bound or operand-colliding decline refuses under §11's
`refused/precondition` and terminates nothing; an exact replay returns the
one committed decline under §10's replay rules.

An accepted offer fixes one authority claim operation. `offer.decide` success
means only that consent was durably accepted before expiry. Writable execution
begins only after exact claim settlement and `assignment.activate`.

### 6.2 Assignment, runtime and activity

| Kind | Direction | Preconditions | Result/observation |
| --- | --- | --- | --- |
| `assignment.activate` | manager -> worker endpoint and adapter | exact successful authority claim; assignment manifest digest fixed | peer binds the full assignment and pinned input/policy/profile; no second runtime exists |
| `runtime.start` | manager -> adapter | exact live assignment; materialized and verified inputs; one fixed start operation | opaque runtime ID plus `start-requested|running` observation; ambiguity grants nothing new |
| `runtime.inspect` | manager -> adapter | attempt identity and optional exact assignment | monotonic observation with opaque runtime identity, state and diagnostic detail |
| `activity.emit` | worker endpoint -> manager | exact live assignment and bounded idempotency key | manager may commit normalized activity; stale or fenced activity refuses |
| `result.declare` | worker endpoint -> manager | exact live assignment; agent turn ended; declared output names only | `completed|unable|plan-rejected` intent and relative paths/evidence; no frozen result implied |

`runtime.inspect` is read-only. `running`, a provider message or a heartbeat
never manufactures a claim. Runtime observations move monotonically through
the W151 attempt axes; `destroyed` cannot regress to `running`, and
`unreachable` is not `destroyed`.

Activity carries `activity_id`, full assignment, immutable plan-step ID when
applicable, kind (`step-started`, `step-completed`, `action`, `evidence`,
`retry`, `blocker`, `handoff-preparation`), bounded summary and referenced
dossier-relative paths. The manager stamps observation time and canonical
event ordering. Activity is not a heartbeat, phase change or permission.

### 6.3 Cancellation and runtime end

| Kind | Direction | Preconditions | Result/observation |
| --- | --- | --- | --- |
| `runtime.cancel` | manager -> adapter/worker endpoint | authority already fenced and ended the exact assignment in one transaction | cancellation requested for the exact runtime; ACP cancellation is normalized separately by W1440 |
| `runtime.inspect` | manager -> adapter | same attempt/runtime identity | `quiescent`, `uncertain` or `destroyed`, with proof/evidence |
| `runtime.destroy` | manager -> adapter | ended/fenced assignment; retention and intake policy permit destruction | positive destroyed observation or explicit unavailable/uncertain error |

Cancellation order is fixed: authority fences publication and ends the
assignment first; then the manager asks the agent session to cancel and the
runtime to stop; then it inspects for quiescence. A successful cancel reply is
not proof of process death. Replacement remains behind the authority's
`runtime-quiescence:<generation>` gate until positive absence or the pinned
certified-isolation clause satisfies it.

### 6.4 Output, proposal and retention

| Kind | Direction | Preconditions | Result/observation |
| --- | --- | --- | --- |
| `output.freeze` | manager -> adapter/store | exact live assignment, declared outputs only, writer quiescent | immutable output manifest and digest; same digest replays, different digest refuses |
| `output.collect` | manager -> adapter/store | frozen output or ended assignment requiring quarantine | content-addressed artifact references and frozen-result or quarantine manifest |
| `proposal.publish` | manager -> authority/proposal store | exact live assignment under v12 contract, valid frozen result, current target/input/policy digests | one immutable proposal receipt; stale generation or target refuses |
| `output.retain` | manager -> store | explicit policy/disposition, exact attempt and material | retained/quarantined locator and deadline; retention is not acceptance |
| `runtime.destroy` | manager -> adapter | collection/intake boundary satisfied or pinned discard policy | cleanup observation only; never changes authority state |

Collection reads only sealed bytes. An undeclared path is not collected.
Freezing rejects traversal, links/reparse points, unsupported types, limit
violations, digest mismatch and detected secret leakage. Missing or invalid
required output prevents a successful result; `unable` may still carry bounded
evidence without pretending the requested output exists.

### 6.5 Replies and errors

Successful replies use `operation.reply` and carry `status=committed|observed`
plus the exact normalized result. A mutation refusal that wrote durable state
also returns a replayable result describing that durable refusal.

Errors use `control.error` and the taxonomy in §11. An ambiguous error never
instructs the caller to invent a new operation ID; it requires reconciliation
of the exact operation. Diagnostic provider text is bounded, redacted,
untrusted and never parsed for portable semantics.

## 7. Input and output descriptors

### 7.1 Common source fields

Every source descriptor has:

- unique assignment-local `name`;
- `type` selecting semantics;
- credential-free absolute normalized `uri` selecting transport;
- unique normalized relative `destination`;
- immutable type-specific identity;
- `required` boolean; and
- optional negotiated provider capability, never inferred from URI scheme.

The ordered source array is significant. Destinations cannot overlap each
other, any output, the control endpoint or manager-owned metadata.

### 7.2 Git source

`type: "git"` adds:

- configured logical `repository_id`;
- `object_format: "sha1"|"sha256"`;
- mandatory full immutable `base_revision` object ID;
- optional full `source_ref` used only to locate objects;
- optional full `integration_ref` naming the intended target; and
- acquisition policy digest.

The bootstrap materializes the private clone and verifies the exact object ID
before the agent starts. A branch never silently replaces
`base_revision`. Credentials stay outside the URI and manifest.

### 7.3 Directory source

`type: "directory"` adds `content_manifest` with sorted regular-file entries,
tree digest, entry count and total bytes. The provider materializes that exact
collection read-only. No Git repository is synthesized.

### 7.4 Output descriptors

Every output has unique `name`, `type`, normalized writable `path`,
`required`, and constraints: maximum bytes/entries, allowed media or file
types, link policy (always `forbid` in 1.0), and optional type-specific
validator digest.

Initial types are:

- `git-change-proposal`: a private Git clone/result plus immutable bundle or
  equivalent object transport; never a push or canonical ref;
- `directory-result`: a distinct tree, never in-place input mutation; and
- `record-output`: progress, research, evidence and draft findings for trusted
  intake, never direct canonical dossier access.

The worker sees local paths and constraints only. It never receives the
external delivery, canonical repository or permanent dossier destination.

## 8. Manifest family

All manifests are sealed objects with exact `schema` and `version`, a
`manifest_id`, `created_at`, `manifest_digest`, and an empty or negotiated
`extensions` bag. IDs are opaque; digests bind content.

### 8.1 Input manifest

`baton.worker-manifest/input` binds:

- `work_ref` and `assignment_contract` (but no generation before claim);
- immutable human contract artifact and digest;
- ordered source and output descriptors;
- role-instruction, policy, toolchain, worker-image and runtime-profile
  digests;
- explicit resource, network, mount, tool, credential-delivery and retention
  policy references/digests; and
- the record binding and immutable finding/plan input digests.

Credentials, environment values and host mount paths are absent. A policy
reference identifies reviewed policy content; it is not a free-form default.

### 8.2 Assignment manifest

`baton.worker-manifest/assignment` is minted only after claim success and
binds full `assignment_ref`, `assignment_contract`, `offer_id`,
`runtime_attempt_id`, input/policy/profile digests, authority claim receipt
digest/sequence, and activation time. Its generation must equal the authority's
current live generation. It is the only manifest that unlocks writable
execution and publication capability.

### 8.3 Runtime-attempt manifest

`baton.worker-manifest/runtime-attempt` binds the opaque attempt to the full
assignment when one exists, adapter name/version/digest, runtime profile,
pinned image/toolchain/policy digests, opaque runtime ID, and independent
monotonic observation axes for consent runtime, execution runtime, output,
worker disposition, proposal, verification, review, approval, integration and
cleanup. Adapter diagnostics are namespaced and cannot change these states.

### 8.4 Frozen-result manifest

`baton.worker-manifest/result` binds `result_id`, exact assignment, input and
policy digests, worker disposition, every declared output's content/tree
digest and artifact reference, evidence/log references, freeze operation and
manager observation. It records missing optional output explicitly and refuses
missing required output. A changed byte requires a new result ID and digest.

### 8.5 Proposal manifest

`baton.worker-manifest/proposal` binds:

- `proposal_id`, exact assignment and frozen result;
- input, policy, profile and output digests;
- source base revision and intended target revision;
- proposal head and immutable bundle/artifact digest for Git work, or exact
  directory result digest for non-Git work;
- author-test observations and evidence, explicitly not certification;
- implementation recap and dossier evidence; and
- the publish operation identity and immutable receipt digest.

The proposal is local and forge-independent. A hosted merge request may point
to it but cannot substitute for any bound field.

### 8.6 Verification and workflow receipts

`baton.worker-manifest/verification` records one verifier's raw
`passed|failed|unable` observation for the exact proposal, target, constructed
candidate-tree digest, verifier profile/image/toolchain/policy, suites and
evidence. A separate `verification-assessment` receipt records
`accepted|rejected|inconclusive`; raw observation and assessment never overwrite
one another.

`technical-review`, `approval` and `integration` are separate immutable
receipt schemas. Each binds its own ID and operation, proposal ID/digest,
candidate tree, exact target revision, actor, policy generation, disposition,
rationale and created time. Integration additionally binds the target
compare-and-swap observation and resulting revision when successful, or one
durably journalled refused attempt. No receipt automatically closes Work.

A second differing write to any receipt ID or operation refuses. Exact replay
returns the original receipt. Revision creates a new proposal and new receipts.

## 9. Artifact references and evidence

An artifact reference contains opaque `artifact_id`, media type, byte count,
content digest and a credential-free locator. The locator is an absolute URI
without userinfo, query or fragment. It locates content already protected by
access policy; it is not a signed URL, bearer capability or integrity check.

Every evidence reference carries its artifact reference plus a purpose from
the closed set `log`, `test-output`, `manifest`, `trace`, `dossier`,
`reproduction`, `diff`, `bundle`, `candidate-tree`, `attestation`. Evidence is
untrusted until the applicable verifier/reviewer accepts it.

Known secret-key names and secret-shaped values are redacted before durable
event/error/log publication. Exact canary scans cover workspace, outputs, Git
objects, proposal, manifests, evidence, retained logs, caches and retained
runtime layers. A detected match yields `integrity.secret-leak` and refuses
publication. Redaction is not proof of absence and does not replace scoped,
short-lived credentials and network policy.

## 10. Retry, ambiguity and ordering

1. A frame retry may repeat `message_id`; an operation retry must repeat the
   same `operation_id` and signature. Neither retry mints identity.
2. Exact committed replies replay byte-for-byte. A different signature under
   the same operation ID is a collision and changes nothing.
3. Connection loss after send is ambiguous. The caller queries/replays the
   exact operation; it does not infer from current Handler, runtime reachability
   or output presence.
4. Manager-owned start, cancel, freeze, collect, retain, intake and destroy
   records are effectively-once in the control store in addition to any
   authority operation.
5. Runtime observations carry `source_seq` scoped to one runtime incarnation.
   The manager records `observation_seq` scoped to the attempt. Exact duplicate
   observations replay; a lower or contradictory state is
   `runtime-observation.state-regression`.
6. Frozen bytes, results, proposals and receipts are immutable. Recomputing the
   same digest is observation/replay; a different digest is a new object or a
   refusal, never mutation in place.
7. Every assignment-owned command compares the full assignment. A newer
   generation held by the same participant does not settle or authorize the
   old command.

## 11. Closed portable error taxonomy

`control.error.body` contains `category`, `code`, `summary`, `retry`,
`operation_state`, optional exact identities, and bounded redacted diagnostics.
Categories and codes are closed in version 1.0:

| Category | Codes |
| --- | --- |
| `refused` | `precondition`, `unsupported-version`, `capability`, `extension`, `operation-collision`, `already-terminal` |
| `ambiguous` | `operation`, `runtime-start`, `collection` |
| `unavailable` | `transport`, `authority`, `artifact-store`, `source-provider` |
| `policy` | `denied`, `profile-uncertified`, `credential-lifetime`, `retention` |
| `integrity` | `schema`, `digest`, `path`, `file-type`, `limit`, `secret-leak` |
| `stale-assignment` | `ended`, `generation`, `contract`, `target` |
| `runtime-observation` | `identity-mismatch`, `duplicate-runtime`, `quiescence-unknown`, `state-regression` |

`retry` is one of:

- `never`: the same request cannot succeed;
- `exact`: repeat/query the same operation only;
- `after-state-change`: a new operation may be attempted only after the named
  gate/policy/dependency changes; or
- `reconcile`: outcome is unknown and capability remains denied until exact
  reconciliation.

`operation_state` is `unsubmitted`, `committed`, `refused`, `retired` or
`unknown`. An unavailable lookup is `unknown`, never `unsubmitted`. Provider
error strings do not select category or retry policy; the trusted adapter maps
observed facts to this taxonomy and retains raw detail as untrusted evidence.

## 12. Required semantic validation beyond JSON Schema

JSON Schema validates local shape. A conforming implementation also proves:

1. Work ID prefix matches authority UUID.
2. Every assignment generation is positive and matches the live authority
   projection for assignment-owned action.
3. Names and destinations are unique; input/output destinations do not overlap.
4. URI and locator fields contain no credentials, userinfo, query or fragment.
5. Manifest and body digests recompute over canonical bytes.
6. Content manifests are sorted, unique, within limits and match aggregate
   count/bytes/tree digest.
7. Git object ID length matches object format and immutable base is present.
8. Artifact byte length and content digest match collected bytes.
9. Every operation signature includes all effective durable operands, and a
   receiver RECOMPUTES it over the exact §4.2 payload before journalling a
   mutating command. A signature that does not describe the request it
   arrived with is `integrity.digest` and changes nothing — recomputing the
   body digest alone leaves a stale signature that would otherwise replay a
   different operation's committed result (W4487 review).
10. Selected capabilities and extensions authorize every sent kind/field.
11. Observation axes never regress and no runtime observation changes Baton
    phase, Handler, contract or generation.
12. Receipt chains bind one exact proposal/candidate/target; no receipt from a
    different revision is reused.
13. Secrets are absent from every durable surface and detected leakage refuses
    publication.
14. An `offer.decide` binding matches the issued offer exactly. Schema proves
    only that `claim_token` is `null` for a decline and a string for an
    accept; the manager additionally proves that `offer_id`,
    `runtime_attempt_id` and `work_ref` name one issued offer with an unspent
    verifier, so a decline can never terminate a differently bound one
    (W4487).

## 13. Security and privacy invariants

- The authority and canonical repository are never mounted or exposed through
  this API.
- Pre-claim offers contain inspection metadata only; they expose no input bytes,
  writable output, execution tools or publication capability.
- Writable paths and publication activate only after exact claim settlement
  and assignment-manifest validation.
- Credentials are delivered out of band through non-persistent,
  assignment-scoped mechanisms; manifests carry only policy/profile digests.
- The claim token is transmitted only where authority is being TAKEN. A
  decline carries `claim_token: null` and is authorized by its exact
  integrity-protected binding (W4487), so refusing an offer never puts the
  one deliberate secret on the wire.
- Logs, activity, errors and diagnostics are bounded and redacted at the trust
  boundary. Worker output remains untrusted even when schema-valid.
- Cancellation kills publication authority before runtime stop is attempted.
- Retention, inspection or salvage never revives an ended assignment or makes
  output canonical.
- Runtime-specific extensions cannot weaken a portable core invariant.

## 14. Design evidence and approval boundary

`schema/worker-control-1.0.schema.json` is the machine-readable shape contract.
`evidence/vectors.json` contains canonical valid and invalid documents.
`evidence/contract_model.py` and `evidence/test_contract_model.py` exercise the
cross-field, digest, retry, observation-order and stale-generation rules that
JSON Schema alone cannot express. They are design evidence only and import no
Baton or `v12/` product implementation.

Approval is requested for these decisions as one compatible set:

1. exact protocol/minor negotiation with sealed core objects and negotiated
   extensions, rather than optimistic minor-version parsing;
2. RFC 8785 plus SHA-256 canonical digests for durable JSON and artifact
   references;
3. credential-free, query-free durable URIs and logical relative workspace
   paths;
4. the operation, manifest, receipt and closed error vocabularies above; and
5. the explicit split between schema validation and required semantic
   validation; and
6. (W4487, 2026-08-22) the asymmetric `offer.decide` authorization — the
   bearer for acceptance, the exact binding for decline — which supersedes
   W151 §7's token requirement for decline and is the one place this contract
   wins a conflict with W151; and
7. (W4487 review, 2026-08-22) the exact §4.2 operation-signature payload,
   including the bearer's presence as its verifier digest. This is what makes
   decision 6 effectively-once: a decline authorized by a binding rather than
   a secret needs an identity that cannot be detached from the operands it
   commits to; and
8. (W4487 re-review, 2026-08-22) that the verifier in that payload is W151's
   ONE derivation — SHA-256 over the bearer's own UTF-8 bytes, serialized
   `sha256:<64 lowercase hex>` — rather than a second value computed here.

Approval freezes the design vocabulary for the dependent ACP and conformance
children. It does not authorize implementation or claim that any runtime is
certified.
