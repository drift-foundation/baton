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

**Superseded in part on 2026-08-26 by the artifact-neutral Worker Manager
ruling of 2026-08-25 (W14251).** This is a SUPERSESSION rather than a
clarification: documents that satisfied §7 as it was written stop being
conformant, because the vocabulary they used no longer exists.

The Worker Manager standardizes exactly two filesystem roles and their two
manifests — a read-only `/input/` carrying `input.json`, and an `/output/`
that is writable until quiescence and then frozen, carrying an `output.json`
published LAST. It validates envelope shape, identity, containment, completion
publication and generic integrity, and it never executes an ingestion
instruction or interprets payload semantics.

So §7 no longer describes HOW input is acquired. The acquisition
vocabulary — a source `type`, an absolute acquisition `uri`, the
version-control and directory source variants — and the three closed output
kinds are gone from the schema, from §3.3's source-URI rule and from §12
rules 4 and 7. §7.6 keeps them as dated history, because the reasoning that
was superseded is how the next reader knows why the current rule is not the
obvious one.

What did NOT change: the version-control object type stays, because four of
its six referents are the proposal and integration surfaces of §8.5 and §8.6,
which this supersession did not touch; and the URI grammar stays, because
artifact locators are still URIs this contract receives. What ended is the
manager reading a SOURCE's acquisition locator. See
`work/records/2026/08/finding-worker-control-artifact-neutral-io/`.

**Corrected 2026-08-26 by that Work's second review.** The first revision gave
`/output/output.json` the manager's own `baton.worker-manifest/result` schema,
which requires a freeze operation, a manager observation and custody artifact
references — so the contract told the WORKER to publish last a document only
the MANAGER can author. §7.3 and the new §8.7 separate the worker's completion
envelope from the manager's frozen-result receipt, which is what makes both
pinned sentences of the ruling true at once. §12 rule 3 is narrowed in the same
round: two fixed roots cannot alias by relative spelling.

**Amended 2026-08-26 by W19784, and this one is a DEFECT FIX rather than a
clarification or a supersession.** The revision above left the contract
unsatisfiable: §8.7 requires the worker's completion envelope to carry the
exact full `assignment_ref` including the authority generation, and §8.1 gives
`input.json` no generation because it is minted before any claim exists. No
other surface inside the execution container carried one — not the framed
`work` request, not the environment. A worker that obeyed the input contract
could not obey the output contract.

The fix delivers the ALREADY-DEFINED §8.2 assignment manifest, unchanged and
complete, at a second fixed read-only name `/input/assignment.json`. §7.0 now
describes three protocol documents in the same two filesystem roles; the
manager authors both input documents at their proper lifecycle moments and the
worker still authors only `/output/output.json`. §7.1 and §12 rule 3 reserve
the new name in its own root, and new §12 rule 16 states the cross-document
bindings that hold the pair together.

No document that satisfied the old text stops being conformant, because no
conformant execution container could be built under it. Explicitly rejected:
putting `assignment_ref` into `inputManifest`, putting assignment identity on
the `work` frame, and reviving an assignment environment string. See
`work/records/2026/08/finding-worker-completion-assignment-identity/`.

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

Artifact locators are absolute normalized URIs. They contain no userinfo,
credential, bearer token or fragment. Query strings are forbidden because they
routinely carry signed credentials or unstable selection parameters. A URI
scheme describes transport only and never selects semantics.

**Superseded 2026-08-26 (W14251).** This paragraph applied the same grammar to
a SOURCE URI, and a source no longer has one: the manager receives an already
staged read-only directory. The rule survives for the locators this contract
still carries — §9 artifact references — and one protection was lost with the
member it guarded. A durable source URI could not carry a query BECAUSE a query
is where a credential rides; that protection now belongs to whoever stages the
input, and it is recorded here rather than quietly dropped.

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

## 7. The two filesystem roles and their descriptors

Revised 2026-08-26 by the artifact-neutral ruling (W14251). §7.6 keeps what
this section used to say.

### 7.0 The two roles

A worker sees exactly two standardized places and three protocol documents:

```text
/input/                 read-only for the whole runtime
  input.json            MANAGER-authored, BEFORE claim: what is staged and how
                        it is to be consumed
  assignment.json       MANAGER-authored, AFTER claim: which live assignment is
                        executing this input
/output/                writable until quiescence, then frozen
  output.json           WORKER-authored: published LAST; what was produced and
                        how the result is to be consumed
```

**Revised 2026-08-26 by W19784.** This said two documents, and that was a
defect rather than a simplification. §8.7 requires the completion envelope to
carry the exact full `assignment_ref` — Work reference, participant AND
authority generation — while §8.1 gives `input.json` a `work_ref` and
deliberately no generation, because it is minted before any claim exists. No
other frozen surface delivered the missing part: the framed `work` request
carries only the common worker-entry identity, and the execution environment
does not carry an assignment value. A worker consuming a structurally valid
input manifest therefore could not author a structurally valid completion
envelope at all.

The fix is a PATH AND A LIFECYCLE, not a new document. `assignmentManifest`
(§8.2) already holds the exact assignment identity, the runtime attempt, the
input-manifest digest, the policy and profile digests and the claim-receipt
binding. It is now delivered, unchanged and complete, at the second fixed
read-only name `/input/assignment.json`. Explicitly rejected: adding
`assignment_ref` to `inputManifest`, adding an assignment member to the `work`
frame, and any environment string or compatibility alias.

Three documents, still two filesystem roles. `/input/` gains no writable
surface and no new mount authority, and the assignment manifest carries no
bearer secret (§13).

**The lifecycle is normative, and so is the moment the identity is proved.**
Before the root is exposed to any container the manager holds the delivered
assignment manifest against its own live assignment, the runtime attempt it is
starting and the input digest the attempt was claimed against — §12 rule 17,
added 2026-08-27 because the first implementation of this ruling proved that
identity only at the freeze, which is after the agent has already run.

`input.json` is authored before claim, and its
bytes and digest never change afterwards — it is the pre-claim evidence the
result is measured against. After the claim commits, the manager materializes
`assignment.json` in the same root and validates its binding to that exact
input, the minted generation, the runtime attempt, the policy and the profile.
No container observes the input root during that transition. Only once both
documents are complete is the whole `/input` surface exposed to the execution
container, read-only. **Consent sees neither document**; consent mounts
nothing.

The manager's own receipt over the frozen tree is a FOURTH document in a place
the worker never sees — §7.3 and §8.7 say why it cannot be `output.json`.

Both paths are fixed constants of this contract rather than operands. A path a
manifest could vary is a path a runtime can be pointed at wrongly, and the
worker is told where to look by the contract rather than by the payload.

`/input/` is mounted read-only for the whole runtime, not merely
write-protected by convention: the input is evidence the result is measured
against, so a runtime that could edit it could edit what it is judged by.

`/output/` is writable until the manager proves quiescence and then frozen.
Freezing is what makes a result describable: a tree somebody may still be
writing to has no digest anybody can quote.

**The manager never interprets either payload.** It validates envelope shape,
identity, containment, completion publication and generic integrity. It does
not execute an ingestion instruction, does not resolve a locator, and does not
know what a version-control repository is. Those conventions may appear INSIDE
an opaque payload member; they are not worker-control vocabulary.

### 7.1 Staged-input descriptors

Every source descriptor in `input.json` has:

- unique assignment-local `name`;
- unique normalized relative `destination` under `/input/`;
- `required` boolean;
- `content_manifest`: the generic integrity evidence of §3.3 — sorted
  regular-file entries, tree digest, entry count, total bytes; and
- `consumption`: an OPAQUE namespaced payload describing how the staged
  material is to be consumed.

The ordered source array is significant.

**Corrected 2026-08-26 by this Work's third review.** This said destinations
cannot overlap "any output", which is the superseded shared-workspace rule and
contradicted §12 rule 3 after the code was corrected — two live normative
answers. Under §7.0's two fixed roots the actual rules are:

- staged-input destinations do not overlap EACH OTHER, and declared output
  paths do not overlap each other. Across the two roots they are never
  compared: `/input/repo` and `/output/repo` are disjoint by construction;
- no destination is `input.json` or `assignment.json`, or nested below
  either, because those are the two manager-authored protocol documents of the
  root it sits in;
- no declared output path is `output.json` or nested below it, for the same
  reason on the other side; and
- no destination reaches the control endpoint or manager-owned metadata.

`assignment.json` joined this list on 2026-08-26 with §7.0's third document,
and for the identical reason as `input.json`: a staged payload at that name
would replace a document the manager authored.

**The reserved names are reserved in their OWN root only.** An output called
`input.json` or `assignment.json` sits under `/output/` and collides with
nothing. Reserving every protocol name in both roots would be forbidding a
spelling rather than protecting a document. And NESTING COUNTS:
`input.json/data` requires that name to be a directory while the protocol
document is a file, so it is the same collision.

**`consumption` is opaque and that is the whole point.** The manager carries
it and never reads it. A member the manager interpreted would be a second
place that decides what an input means, and the first is the party that staged
it. A worker that needs to know the material is a version-control checkout
reads that from `consumption`; the manager cannot tell and does not ask.

**How the directory was populated is outside this contract.** The manager
receives an already staged read-only tree and the integrity evidence for it.
Whoever staged it is answerable for how, including for the credential
protections §3.3 used to carry.

### 7.2 Output descriptors

Every output has unique `name`, an OPAQUE `type`, normalized writable `path`
under `/output/`, `required`, and constraints: maximum bytes/entries, allowed
media or file types, link policy (always `forbid` in 1.0), and optional
type-specific validator digest.

The `type` is an opaque identifier. The manager compares it, carries it into
the result and never branches on it. Two declarations may not name the same
tree or nest one inside the other: the same bytes under two names are two
artifacts with two identities, and retention would then decide twice about
material that is once.

The worker sees local paths and constraints only. It never receives the
external delivery, canonical repository or permanent dossier destination.

### 7.3 The worker's completion envelope, and publication last

**Corrected 2026-08-26 by this Work's second review.** This section identified
`/output/output.json` with `baton.worker-manifest/result` — a document whose
schema requires `freeze_operation`, `manager_observed_at` and custody artifact
references, none of which exists until after the worker is quiescent. So the
contract told the worker to publish last a document the worker cannot author.
That was an unimplementable cycle rather than an ambiguity.

**THERE ARE TWO DOCUMENTS AND THEY HAVE TWO AUTHORS.** This is a separation
rather than a supersession: it is the reading under which both pinned sentences
of the 2026-08-25 ruling are true at once — the worker "writes every durable
result below `output/` and publishes `output.json` last", and the manager,
"after quiescence, performs only format-neutral duties: … freeze or snapshot
the declared output, compute generic integrity evidence, and bind the frozen
tree to the assignment generation."

| | `/output/output.json` | the frozen-result receipt |
| --- | --- | --- |
| schema | `baton.worker-manifest/completion` | `baton.worker-manifest/result` |
| author | the WORKER | the MANAGER |
| when | last, before quiescence | after quiescence, at freeze |
| where | inside `/output/` | manager custody, never `/output/` |
| says | what I produced and where | what I took custody of and under which operation |

The worker's envelope carries, per declared output: `name`, the opaque `type`,
the declared relative `path`, a `status` of `present` or `missing-optional`,
the content manifest when present, and `result_metadata` — an OPAQUE namespaced
payload the manager carries and never reads. It carries **no freeze operation,
no manager observation and no custody locator**, because those are facts about
an act that has not happened yet.

`result_metadata` exists because the ruling's own example needs somewhere to
go — a worker reporting a commit identifier as format-specific output
metadata. Under the superseded closed output kinds that identifier was
vocabulary; under an opaque type it has no home unless the envelope provides
one.

**`output.json` is published LAST**, after every durable result is written.
That ordering is what makes it trustworthy: it exists only if everything it
describes already succeeded, so its presence is the completion signal and no
separate one is needed.

The manager VALIDATES that envelope — shape, identity, containment, completion
publication and generic integrity — and holds it against the input manifest it
answers under §12 rule 15: one answer per declared output, no extras, no
omissions, exact `name`/`type`/`path`, and no `missing-optional` answer for a
required declaration. Only then does it produce its own receipt over the frozen
tree. §8.4 and §8.7.

**Published means published atomically.** Writing bytes into the final name is
not publication: a process stopped inside that write leaves the name existing
and empty, and a reader cannot distinguish it from a settled answer. The bytes
become visible under the final name only once they are complete.

A missing OPTIONAL output is answered explicitly rather than by silence. The
declaration was made and it is answered; a receiver that saw nothing would
lose the fact that the worker was asked. A missing REQUIRED output refuses.

### 7.4 Unresolved identifiers are not results

An output whose artifact is named only by an identifier the manager cannot
resolve to bytes it holds is not a durable result. The manager takes custody
of bytes and publishes a locator for what it holds; a reference to something
somewhere else is a promise, and a promise cannot be frozen.

### 7.5 Private ephemeral space is capacity, not protocol

A runtime may be given private scratch space. It is CAPACITY: it has no
standardized path, no manifest, no declaration and no guarantee of surviving
the runtime. Nothing in either manifest names it, and a worker may not treat
its presence, size or location as contract.

This is stated because the obvious alternative is wrong. A third standardized
path would be a third protocol artifact — one more thing to declare, contain,
freeze, measure and retain — bought for something that is an implementation's
convenience rather than a party's need.

### 7.6 Superseded acquisition and result vocabulary (2026-08-25)

Kept as dated history. None of the following is live vocabulary; the schema
carries none of it. It is recorded because the reasoning that was superseded
is how the next reader knows why the current rule is not the obvious one.

**Common source fields.** A source descriptor carried `type` selecting
semantics, a credential-free absolute normalized `uri` selecting transport, an
immutable type-specific identity, and an optional negotiated provider
capability never inferred from URI scheme.

**Version-control source.** `type: "git"` added a configured logical
`repository_id`, `object_format: "sha1"|"sha256"`, a mandatory full immutable
`base_revision` object ID, optional full `source_ref` and `integration_ref`,
and an acquisition policy digest. The bootstrap materialized a private clone
and verified the exact object ID before the agent started; a branch never
silently replaced `base_revision`.

**Directory source.** `type: "directory"` added a `content_manifest` the
provider materialized read-only, synthesizing no repository.

**Three closed output kinds.** `git-change-proposal`, `directory-result` and
`record-output`.

**Why they went.** Each made the Worker Manager a party to what its payloads
MEAN. Acquisition put a transport, a credential path and a repository model
inside a component whose contract is that it decides nothing; the closed
output kinds made every new kind of work a change to this contract. The
replacement is two generic envelopes with an opaque payload member each.

**And what did not go with them.** The version-control OBJECT type stays: four
of its six referents are the proposal and integration surfaces of §8.5 and
§8.6, which this supersession did not touch. Removing it wholesale would have
deleted vocabulary that is still load-bearing somewhere else.

## 8. Manifest family

All manifests are sealed objects with exact `schema` and `version`, a
`manifest_id`, `created_at`, `manifest_digest`, and an empty or negotiated
`extensions` bag. IDs are opaque; digests bind content.

### 8.1 Input manifest

`baton.worker-manifest/input` is the `/input/input.json` of §7.0. It binds:

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

**"No generation before claim" is load-bearing, not incidental.** This document
is minted before any claim exists, so it cannot name one; its bytes and digest
never change afterwards. That is why §8.7's completion envelope cannot be
satisfied from this manifest alone, and why 2026-08-26 (W19784) delivered
§8.2 beside it rather than adding assignment identity here — which would have
collapsed pre-claim evidence and post-claim authority into one mutable
lifecycle.

### 8.2 Assignment manifest

`baton.worker-manifest/assignment` is minted only after claim success and
binds full `assignment_ref`, `assignment_contract`, `offer_id`,
`runtime_attempt_id`, input/policy/profile digests, authority claim receipt
digest/sequence, and activation time. Its generation must equal the authority's
current live generation. It is the only manifest that unlocks writable
execution and publication capability.

**Delivered to the execution worker at `/input/assignment.json` since
2026-08-26 (W19784).** The document is unchanged — no member was added,
removed or aliased for this. What is new is that it now has a fixed read-only
path inside the execution container, materialized after the claim commits and
before the input root is mounted (§7.0), and that it is the ONE source from
which a worker takes the `assignment_ref` §8.7 requires. §12 rule 16 states
the bindings that hold it to the `input.json` beside it.

### 8.3 Runtime-attempt manifest

`baton.worker-manifest/runtime-attempt` binds the opaque attempt to the full
assignment when one exists, adapter name/version/digest, runtime profile,
pinned image/toolchain/policy digests, opaque runtime ID, and independent
monotonic observation axes for consent runtime, execution runtime, output,
worker disposition, proposal, verification, review, approval, integration and
cleanup. Adapter diagnostics are namespaced and cannot change these states.

### 8.4 Frozen-result manifest

`baton.worker-manifest/result` is the MANAGER's receipt over the frozen tree.
**It is not `/output/output.json`** — see §7.3 and §8.7. It binds `result_id`,
exact assignment, input and policy digests, worker disposition, every declared
output's content/tree digest, artifact reference and opaque `result_metadata`,
evidence/log references, freeze operation and manager observation. It records
missing optional output explicitly and refuses missing required output. A
changed byte requires a new result ID and digest.

**A `completed` receipt MUST carry `completion_manifest_digest`**, naming the
exact worker envelope §7.3 says the manager validated before freezing.
Corrected 2026-08-26 by this Work's fourth review: the member was optional with
a sequencing excuse, which left the contract giving two answers about one
completed result — either no worker envelope existed, or the manager declined
to bind the one it validated, and nothing durable told them apart.

`unable`, `plan-rejected` and `cancelled` receipts MAY omit it. Those are the
endings where the worker may have died before publishing anything, and
requiring an envelope there would require the worker to have succeeded in order
to be recorded as having failed. **Whenever an envelope WAS validated, the
receipt binds its digest whatever the disposition became** — the shape admits
it on every disposition and requires it only where its absence is otherwise
ambiguous.

There is no version or capability that relaxes this. 1.0 is the only version
this contract admits, and widening the version vocabulary to preserve a bypass
would be inventing a negotiation nothing performs.

It lives in manager custody and is published atomically there. The worker never
writes it and never reads it.

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

### 8.7 Worker completion envelope

**Added 2026-08-26 by this Work's second review**, to give `/output/output.json`
a schema the worker can actually author. §7.3 states the split and why.

`baton.worker-manifest/completion` is the file the worker publishes LAST inside
`/output/`. It binds the exact `assignment_ref`, the worker's own
`disposition`, and one entry per declared output carrying `name`, the opaque
`type`, the declared relative `path`, `status`, the content manifest when
present, and opaque `result_metadata`.

**"The exact `assignment_ref`" means copied from `/input/assignment.json`.**
Until 2026-08-26 this requirement had no satisfiable source: §8.1 carries no
generation and nothing else in the container carried one, so a worker obeying
the input contract could not obey this one. W19784 closed that by delivering
§8.2 at a fixed read-only input path. The worker copies the value; it does not
reconstruct, infer or accept it from an environment value or a request frame.

**What it deliberately does not carry**, and each absence is the same reason:
the worker cannot know it yet.

- no `freeze_operation` — the freeze is an act the manager performs after the
  worker is quiescent, under an operation identity the worker never sees;
- no `manager_observed_at` — an observation the worker has not been observed
  for;
- no artifact reference — a custody locator names where THIS MANAGER put the
  bytes, and at publication time it has not taken them.

The worker's disposition is its own claim about its work, not a settlement. The
manager records it, refuses a missing required output regardless of it, and
settles the attempt itself.

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
3. Names are unique across sources and outputs. Destinations do not overlap
   WITHIN the staged-input set, and do not overlap WITHIN the declared-output
   set. No staged-input destination is `input.json` or `assignment.json`, or
   nested below either — **`assignment.json` added 2026-08-26 (W19784)** with
   §7.0's second manager-authored input document — and no
   declared output path — in either the input manifest or the completion
   envelope — is `output.json` or nested below it: each root's protocol
   manifest name is reserved in that root. **Narrowed 2026-08-26 (W14251 second review):** this compared the two
   sets against each other, on the superseded shared-workspace model. Under
   §7.0's two fixed roots `/input/repo` and `/output/repo` are disjoint, so
   equal or nested relative spellings across the two roles cannot alias. A name
   stays unique across both, which is a different rule: a name is how one
   manifest's declarations are told apart, and two roles sharing one is
   ambiguous wherever the name is used.
4. Artifact locator fields contain no credentials, userinfo, query or
   fragment. **Narrowed 2026-08-26 (W14251):** this named source URIs too, and
   a source no longer carries one. The party that stages `/input/` is
   answerable for the protection that rule used to give it.
5. Manifest and body digests recompute over canonical bytes.
6. Content manifests are sorted, unique, within limits and match aggregate
   count/bytes/tree digest.
7. Version-control object ID length matches object format and the immutable
   base is present, **on the §8.5 proposal and §8.6 integration surfaces**.
   **Narrowed 2026-08-26 (W14251):** this also compared a SOURCE's object
   format against its base revision — a sha1 base under a sha256 repository is
   a different object namespace rather than a shorter digest — and a source no
   longer declares either. The rule is unchanged where the object type still
   lives.
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
15. **Added 2026-08-26 (W14251 third review).** A worker completion envelope is
    held against the input manifest it answers, and the relations are exact.
    For every declared output there is EXACTLY ONE answer; every answer names a
    declared output, so there are no extras and no omissions; each answer's
    `name`, `type` and `path` equal the declaration's; and no `required`
    declaration is answered `missing-optional`. A declaration's `required` flag
    is the manager's, and a worker that could answer a required output missing
    would be settling its own attempt.

    THIS RULE NEEDS TWO DOCUMENTS, which is why it is stated here rather than
    in the completion envelope's own validation. A function handed one document
    can prove that envelope is internally consistent — unique names,
    non-overlapping paths, a status that agrees with its integrity evidence —
    and nothing about whether it answers the assignment that was made. The
    manager holds both and performs this comparison before it freezes.

16. **Added 2026-08-26 (W19784).** The two manager-authored documents in
    `/input/` are held against each other, and a party that reads them —
    the worker before it dispatches an agent, the manager before it mounts the
    root — proves they are ONE delivery:

    - the assignment manifest's `assignment_ref.work_ref` equals the input
      manifest's `work_ref`;
    - the assignment manifest's `input_manifest_digest` equals the input
      manifest's own `manifest_digest`, which is what proves these two files
      are that pair rather than one of them beside a newer other; and
    - `policy_digest` and `runtime_profile_digest` are equal on both.

    Each document is separately closed, digest-bound and structurally valid on
    its own; none of that says they are about one thing, which is why this is a
    semantic rule and not a schema one.

    THE GENERATION IS DELIBERATELY NOT COMPARED. The input manifest has none
    (§8.1) — that asymmetry is the entire defect W19784 answers — so
    `assignment.json` is the ONE source of the participant and authority
    generation the completion envelope must carry, and the worker copies it
    from there and from nowhere else.

    `assignment_contract` is deliberately not compared EITHER, and that is not
    an omission. Under 1.0 the frozen schema pins it to
    `const: "v12-assignment-1"` on both documents, so two structurally valid
    manifests cannot disagree about it; the obligation is discharged one layer
    earlier. A version that widened that vocabulary would move the comparison
    into this rule.

17. **Added 2026-08-27 by W19784's own review.** THE PAIR RULE IS NOT AN
    AUTHORIZATION, and the two must not be confused. Rule 16 proves the two
    documents are one delivery; it cannot prove that delivery is the one the
    manager authorized, because a pair minted for a superseded generation, a
    different participant or another runtime attempt agrees with itself
    perfectly.

    So before the manager exposes `/input/` to any container it holds the
    delivered assignment manifest against its OWN live values — the four-part
    assignment it activated, the runtime attempt it is starting, and the input
    manifest digest the attempt was claimed against. All three, and before the
    root is written; a manager that composed first and checked afterwards would
    already have created the thing it was deciding about.

    **The moment is normative, not just the check.** The same comparison stated
    only at custody is a rule that fires after the agent has run: the container
    was mounted, the worker read material nothing had authorized, and the
    refusal arrives too late to have prevented anything. The comparison at
    custody stays — an envelope is a second document and deserves its own
    proof — but it is defence in depth rather than the boundary.

    The worker performs neither of these, and cannot: which generation is live
    is a fact about the authority, and a container is the one party with no way
    to ask. What the worker owns is §12 rule 16 and the closedness of the two
    documents it was handed.

    **AND THE ROOT THAT WAS PROVED IS THE ROOT THAT IS MOUNTED.** Added the
    same day, because the first implementation of this rule proved one
    directory and then started a runtime whose mount plan was an independent
    value — free to name a sibling root of the same assignment, to land the
    proved source at some other path, or to mount nothing at `/input` at all.
    Containment and writability were checked and said yes, because they are
    about a different question.

    So exactly one read-only bind of that exact source lands at the fixed
    `/input`, and where no root was authorized nothing may claim that path.
    "The manager did not say" is not a reason to expose an unproved directory
    where the worker will look for its assignment.

    A proof about one value is not a proof about another, and two boundaries
    that never compare their operands are two boundaries that can both pass
    while the container is wrong.

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
