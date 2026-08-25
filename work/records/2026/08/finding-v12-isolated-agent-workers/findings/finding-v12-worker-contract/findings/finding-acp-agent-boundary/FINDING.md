# Finding: specify the v12 ACP agent boundary

Canonical Baton Work: `W1440` (`43c55d4b-W1440`).

Child of `work/records/2026/08/finding-v12-isolated-agent-workers/findings/finding-v12-worker-contract/`.

## Assignment boundary

Specify ACP as the normalized inner agent-session endpoint beneath the frozen
outer worker-control contract. Define native ACP relay and non-ACP adapter
obligations, including an ACP-to-Codex-App-Server mapping. Do not add runtime,
repository, authority, proposal or integration lifecycle to ACP, and do not
implement an adapter.

## Required design output

1. A version/capability handshake and the minimum session surface: initialize,
   create a fresh assignment-scoped session, enforce the pinned mode/policy,
   prompt, normalize updates, handle permission requests, cancel and establish
   the strongest observable completion/quiescence fact ACP can supply.
2. A mapping from ACP session/update/permission/cancel outcomes to portable
   worker-control events and errors, with no claim or lifecycle authority
   inferred from agent prose, tool status or transport reachability.
3. Relay requirements for native ACP agents: identity preservation, audit,
   policy enforcement, bounded flow control, reconnect ambiguity and
   cancellation forwarding.
4. Adapter requirements for non-ACP runtimes. The Codex App Server profile must
   map initialization, thread/turn/item streaming, server-initiated approvals,
   `turn/interrupt` and terminal turn status without adopting experimental
   `process/*` or runtime-specific thread IDs as Baton protocol semantics.
5. Permission behavior: exact pinned policy is required; unavailable modes or
   unexpected approval requests fail visibly, grant nothing, and trigger the
   configured cancellation/quarantine path.
6. Conformance-ready examples for normal completion, user/agent cancellation,
   transport loss, duplicate/late events, policy refusal, approval races and
   ambiguous session death.

Official Codex evidence: [Codex App Server](https://learn.chatgpt.com/docs/app-server),
read 2026-08-21. The current proof's local ACP SDK baseline is 1.3.0; that
version is evidence, not the portable contract version.

## Acceptance boundary

The result must make it impossible to confuse agent-session cancellation with
runtime quiescence, an App Server thread with a Baton participant, or an ACP
permission decision with assignment capability. Experimental vendor surfaces
may be adapter-private diagnostics only.

## 2026-08-21 design record

### Revalidated baseline

- **Confirmed.** W151 (`../../finding-v12-assignment-state-machine/SPEC.md`)
  remains the normative owner of assignment identity, generations, fencing,
  typed gates, effectively-once settlement and receipt authority. This child
  imports those rules and adds no state to that machine.
- **Confirmed.** W1439 (`../finding-worker-control-api-manifests/SPEC.md`)
  remains the outer contract. Its error taxonomy is CLOSED for version 1.0, so
  this child maps into it and adds no category and no code. Its precedence
  clause is unchanged, so a conflict here is a defect here.
- **Confirmed.** The ACP surface was re-derived from
  `@agentclientprotocol/sdk` 1.3.0 as vendored under `v12/node_modules/`:
  `PROTOCOL_VERSION = 1`; thirteen `SessionUpdate` variants; five `StopReason`
  values (`end_turn`, `max_tokens`, `max_turn_requests`, `refusal`,
  `cancelled`); `RequestPermissionOutcome` of `cancelled` or `selected`;
  `PermissionOptionKind` of `allow_once`, `allow_always`, `reject_once`,
  `reject_always`; four `ToolCallStatus` values; and client capabilities
  `fs`, `terminal` plus five capabilities the SDK marks UNSTABLE.
- **Confirmed.** ACP's `session/cancel` is a NOTIFICATION with no response.
  The observable cancellation fact is the turn ending with
  `stopReason: "cancelled"`, which is a fact about a conversation.
- **Confirmed.** The accepted proof at `v12/src/acp_session.mjs` already
  demonstrates capability negotiation before session use, exact required
  permission mode with no fallback, an unexpected permission request treated
  as a policy failure, and a manager-owned turn deadline distinct from setup
  supervision. `SPEC.md` generalizes these four; it does not adopt the
  prototype's process-local session handling or its single hard-coded posture.
- **Observed.** The prototype's ACP SDK baseline of 1.3.0 remains evidence,
  not a portable contract version. `SPEC.md` §2.1 pins the wire version per
  certified profile and refuses a mismatch rather than naming a literal.

### Codex App Server facts not previously recorded

The parent record cited the App Server as a bidirectional JSON-RPC interface
with thread/turn/item streaming, server-initiated approval requests and
explicit turn interruption, and marked `process/*` and WebSocket transport
experimental. Re-reading the official documentation on 2026-08-21 confirmed
all of that and added two facts the mapping depends on:

- **Confirmed.** The approval surface is FOUR request families, not one:
  `item/commandExecution/requestApproval`, `item/fileChange/requestApproval`,
  `item/permissions/requestApproval` and `mcpServer/elicitation/request`, plus
  the experimental `tool/requestUserInput`. Each has its own answer vocabulary,
  and the granting answers (`accept`, `acceptForSession`,
  `acceptWithExecpolicyAmendment`) differ per family. A single "refuse the
  approval" rule would not have covered them.
- **Confirmed.** `turn/interrupt` is a REQUEST with a reply, unlike ACP's
  cancellation notification. The reply is not an outcome; the observable fact
  remains `turn/completed` with status `interrupted`. `SPEC.md` §10.6 states
  this explicitly because the reply is exactly the sort of acknowledgement an
  implementer would otherwise treat as proof.
- **Confirmed.** The experimental surface is broader than `process/*` and
  WebSocket alone: `thread/turns/list`, `thread/items/list`,
  `thread/backgroundTerminals/*`, `experimentalFeature/list`,
  `environment/info`, `permissionProfile/list`, `collaborationMode/list`,
  dynamic tools and `dynamicToolCall` items, `additionalPermissions` in
  approvals, and `tool/requestUserInput`. `plugin/*` is under development and
  `thread/rollback` is deprecated. `SPEC.md` §10.7 excludes all of them and
  enforces the exclusion at the handshake by never setting
  `capabilities.experimentalApi`.
- **Confirmed.** `thread/status/changed` carries `notLoaded`, `idle`,
  `systemError` and `active`. None is a quiescence observation.

### Decisions proposed for approval

`SPEC.md` §15 states the eight decisions as one compatible set. In summary:
the agent session is a fourth independent version axis; the relay is the ACP
client and withholds filesystem and terminal capability structurally; one
fresh session per runtime attempt with no reuse, resume, fork or re-prompt;
exact mode pinning with an approval request treated as a policy failure that
grants nothing; the closed turn-outcome and normalized-event vocabularies,
with turn outcome gating but never deciding disposition; cancellation as
ordered intent plus observed quiescence, where agent quiescence never
satisfies a runtime-quiescence gate; the Codex App Server profile with its
exclusions; and reuse of W1439's error taxonomy unchanged.

### Acceptance boundary, met

The assignment required that the result make three confusions impossible.
`SPEC.md` §7.4 states all three as a table, gives the reasoning for each, and
`evidence/test_acp_boundary_model.py` asserts each mechanically:
`satisfies_runtime_quiescence_gate` returns false for every session state
including `agent-quiescent`; deriving a participant from a provider session id
is a refusal rather than a function; and no permission answer this contract
produces selects an option or grants a scope.

This child changes design records only. No protocol, authority, application,
runtime or adapter implementation was added or modified.

## 2026-08-21 corrections after review `review-2026-08-21T22-53-56Z.md`

The reviewer requested changes and supplied reproducible counterexamples. All
of them were reproduced against the submitted artifacts before anything was
changed. The record below keeps the original claims above as chronological
history and marks exactly what is superseded.

### Recorded source fact corrected: the ACP client capability inventory

**Superseded.** The "Revalidated baseline" section above lists `fs`,
`terminal` "plus five capabilities the SDK marks UNSTABLE" and §2.2 of the
first `SPEC.md` revision named those five as `plan`, `auth`, `elicitation`,
`nes` and `session`. That was wrong about two of the eight members.

**Confirmed 2026-08-21**, by re-reading the doc comments of
`ClientCapabilities` in the vendored
`@agentclientprotocol/sdk` 1.3.0 type declaration member by member:

| Member | Marked UNSTABLE by the declaration |
| --- | --- |
| `fs` | no |
| `terminal` | no |
| `session` | **no** |
| `plan` | yes |
| `auth` | yes |
| `elicitation` | yes |
| `nes` | yes |
| `positionEncodings` | **yes** |

`session` is stable and was misrecorded as unstable; `positionEncodings` is
unstable and was omitted entirely. The schema's sealed capability object was
conservative enough that no document was affected, but the recorded fact was
wrong and a later reader would have inherited it. §2.2 now states that the
relay withholds every client capability, stable ones included, and gives the
reason: withholding by default costs nothing, while advertising by default
means every future SDK release silently widens the boundary.

### Codex App Server operands, confirmed by re-reading the official docs

Re-read <https://learn.chatgpt.com/docs/app-server> on 2026-08-21 for the
specific operands the mapping needs.

- **Confirmed.** The documented `initialize` carries NO protocol version in
  either direction. Its request takes `clientInfo` (`name`, `title`,
  `version`) and an optional `capabilities` object with `experimentalApi`,
  `optOutNotificationMethods`, `requestAttestation` and
  `mcpServerOpenaiFormElicitation`; its response reports the user agent and
  platform. **This supersedes** the first revision's Codex profile, which
  pinned `pinned_wire_version: 1` and applied ACP's exact-match rule to it.
  Pinning a number the provider never sends is worse than no check, because it
  looks like one. §2.1 now routes such a provider through an exact
  `provider_binding` instead.
- **Confirmed.** `thread/start` takes `model`, `cwd`, `approvalPolicy`
  (`never`, `onRequest`, `unlessTrusted`), the legacy `sandbox` string
  (`readOnly`, `workspaceWrite`, `dangerFullAccess`), `personality`,
  `serviceName`, and the experimental/beta `dynamicTools`, `permissions` and
  `historyMode`.
- **Confirmed.** `turn/start` takes `threadId`, `input`, and overrides for
  `cwd`, `model`, `effort`, `personality`, `summary`, `outputSchema`,
  `approvalPolicy`, `sandboxPolicy` (an object whose `type` may be `readOnly`,
  `workspaceWrite`, `dangerFullAccess` or `externalSandbox`, with
  `networkAccess`) and `collaborationMode`. Because a turn may override the
  thread default, §10.3 now requires the policy to be re-sent IN FULL on every
  turn: an unpinned turn inherits, and an inherited default nobody restated is
  not a pinned policy.
- **Confirmed.** The approval reply shapes differ per family.
  `item/commandExecution/requestApproval` and
  `item/fileChange/requestApproval` take a string; `item/permissions/`
  `requestApproval` takes `{permissions, scope}` where `permissions` is the
  GRANTED SUBSET; `mcpServer/elicitation/request` takes `{action, content}`.
  **This supersedes** the first revision, whose model returned the string
  `"decline"` for all four — invalid JSON-RPC for two of them, which would
  leave the request hanging rather than denied. §10.5 now specifies a typed
  denial per family and the tests assert each complete payload.
- **Observed, and deliberately not relied upon.** The reviewer reports that
  the current page documents environment-variable remote authentication rather
  than the `--ws-auth` flag names the first revision cited; this
  implementer's re-read still returned those flag names alongside a
  `CODEX_REMOTE_TOKEN` environment variable. The discrepancy is recorded
  rather than resolved, because it does not need resolving: §10.1 now rests
  the WebSocket exclusion on the transport being marked experimental and
  unsupported, plus the independent fact that any remote form puts a bearer
  credential in the session path. Neither depends on how the credential is
  spelled, so the exclusion no longer has an obsoletable rationale.

### Decisions changed by this round

1. **Shared definitions are reproduced verbatim, not re-derived** (`SPEC.md`
   §0.3). The first revision locally re-derived `workRef`, `assignmentRef`,
   `participant`, `artifactRef` and the integer bounds, and the copies
   diverged: `W0` was admitted, participants could lead with a digit and could
   not contain an underscore, artifacts used `byte_length` instead of `bytes`
   with a looser media type, and integers had no JSON-safe maximum. A document
   valid under this child could therefore be invalid under the contract this
   child says takes precedence. The definitions are now byte-identical and a
   test asserts it.
2. **Session cardinality is `(runtime_attempt_id, posture, session_epoch)`**
   (§3.2). The first revision said "one fresh session per runtime attempt"
   while also requiring two postures under W151's single fixed attempt
   identity. Both could not be true. `posture` is now part of
   `agent_session_ref`, the epoch counter is scoped per posture, promoting a
   consent session into an execution session is a refusal in the model, and a
   `consent-then-execution` trace exercises the whole sequence.
3. **All three forbidden session bindings are enforced** (§3.2). The first
   revision's schema accepted an execution session with no assignment, a
   consent session with one, and an assignment belonging to a different Work.
   The first two are now schema conditionals; the cross-Work equality and the
   authority-prefix rule are required semantic checks with negative vectors,
   because JSON Schema cannot express them.
4. **Normalized events are sealed documents** (§0.2, §6.4). The first
   revision's §0.2 said all four documents carry `document_digest` while the
   event schema had no such member, and the executable ledger consumed an
   ad-hoc shape with a top-level `session_epoch` the schema forbade — so the
   schema tests and the semantic tests proved things about two different
   objects. Events now carry `document_digest`, the ledger consumes the schema
   shape and returns a sealed document, and tamper and reseal coverage exists.
5. **The error taxonomy is enforced pairwise in the schema** (§11). The first
   revision left `code` as a free string, so a persisted `policyFailure` could
   introduce a code that no longer belonged to any category. The schema is now
   a `oneOf` over the seven categories with their exact code enums, and a real
   code under the wrong category is refused as firmly as an invented one.

## 2026-08-21 corrections after review `review-2026-08-21T23-18-11Z.md`

Second review; three executable gaps and one set of superseded prose. All four
counterexamples reproduced before anything changed.

### Provider response shapes, confirmed from the provider's own schemas

**Superseded.** The first correction round specified the denial for
`item/commandExecution/requestApproval` and `item/fileChange/requestApproval`
as the bare string `"decline"`. That is the decision MEMBER, not the response.

**Confirmed 2026-08-21** by generating the schemas from the installed CLI
(`codex-cli 0.149.0`, `codex app-server generate-json-schema`):
`CommandExecutionRequestApprovalResponse` and
`FileChangeRequestApprovalResponse` are both `type: object` with `decision`
REQUIRED; `PermissionsRequestApprovalResponse` requires `permissions` and
defaults `scope` to `turn`; `McpServerElicitationRequestResponse` requires
`action`. The bare string validates false against the provider schema and the
object validates true. All four denials are now complete response objects, and
the four schemas are captured verbatim under
`evidence/provider-schemas/codex-app-server/` with their provenance, so
conformance is validated against the provider's contract rather than against a
payload this record authored. The certified
`provider_binding.interface_digest` is the digest of that captured bundle.

The reviewer's point behind the finding is the durable one and is now recorded
in `SPEC.md` §10.5: a self-authored equality assertion cannot prove
provider-shape conformance. The first revision asserted equality against a
reply the provider would have rejected, and the assertion passed.

### Decisions changed by this round

1. **The event boundary is one sealed contract in both directions**
   (`SPEC.md` §6.4). **Superseded:** the previous round's claim that
   `EventLedger` consumed and returned the sealed schema shape. It did
   neither — it silently discarded any supplied `document_digest` without
   verifying it, so a tampered sealed event was accepted and re-sealed, and it
   appended a `replayed` member to the returned document, which
   `additionalProperties: false` forbids and which invalidated the digest. The
   ledger now verifies the seal BEFORE reading any other field and returns the
   document exactly as given.
2. **Lateness and observation sequence leave the sealed event** (§6.4,
   schema `normalizedEvent`). **Superseded:** `late` and `observation_seq` as
   event members. They describe an OBSERVATION, not the frame, and sealing
   them in meant the same frame observed twice would carry two digests — so an
   ordinary retransmission became indistinguishable from a spliced stream.
   They now travel in the ledger's outcome beside the document, and a replay
   reports the original observation rather than minting a second.
3. **One validator certifies every profile** (§12.7a). **Superseded:** the
   previous `validate_postures`, which checked only that the two policies
   differed plus two booleans. Swapping the Codex posture policy objects while
   leaving the booleans honest certified consent with `workspaceWrite` and a
   workspace cwd — the inverse of normative §10.2 — and passed both schema and
   semantics. The posture operands are now schema constants bound to their
   posture, the workspace and declared-output invariants are schema constants,
   and `validate_profile` enforces the whole certification on every path.
4. **The method and capability sets belong to the version** (§2.3).
   **Superseded:** `required_agent_methods` and `refused_agent_methods` as
   profile members. A sealed profile could declare `["session/new"]` and still
   negotiate successfully, because negotiation consulted a separate hard-coded
   constant and never compared the two. Rather than make the profile lists
   exact and keep two live sources of truth, the members are removed;
   `session_capabilities` is a schema constant of exactly the six.
5. **A request operand is never a caller-chosen path** (§3.2, §12.7b). The
   request builders took a bare `cwd`, so an execution workspace could be
   passed to a consent-posture build. They now take a role-to-path map and the
   PROFILE selects the role.

### Superseded prose removed from live normative text

§0.2, §2.4 and §8.2 still stated session lifetime, `session.fresh` and the
relay journal scope as `(runtime_attempt_id, session_epoch)` after §3.2 had
superseded that cardinality, and §3.2 itself still said every session uses the
materialized assignment workspace although a consent session has neither. All
four now carry the posture. A chronological correction in the finding history
does not help an implementer reading the normative sections, so live text that
contradicts a recorded supersession is itself a defect.

## 2026-08-21 corrections after review `review-2026-08-21T23-32-48Z.md`

Third review; two integrity bypasses in the executable certification boundary.
Both counterexamples reproduced before anything changed. The reviewer accepted
the second-round corrections.

### Decisions changed by this round

1. **Certification composes shape, seal and policy at one entry point, in that
   order** (`SPEC.md` §12.7a). **Superseded:** the previous round's claim that
   `validate_profile` was "the ONE certification validator". It checked policy
   fields only. It never validated the document against the durable schema and
   never verified its seal, and both `negotiate_acp` and `bind_provider`
   called only that function — so a profile carrying the supposedly removed
   `required_agent_methods`, resealed, reached ACP negotiation despite
   `additionalProperties: false`, and a profile whose certified execution
   model was changed while retaining the old digest reached provider binding
   with an invalid seal. A request builder would then have acted on the
   tampered model.

   The general lesson is recorded in the specification rather than only in the
   fix: proving shape, seal and semantics in three separate tests does not
   make the runtime path compose them. Reading a policy field out of a
   document whose seal was never verified is reading whatever the last writer
   put there. The semantic-only check survives as `certify_profile_fields`,
   explicitly named a PARTIAL helper so isolated vectors can exercise one rule
   at a time, and it is no longer reachable under the certification name.

2. **A session record is validated only together with its profile** (§12.6).
   **Superseded:** the optional `profile=None` parameter added in the previous
   round. Omitting it returned before the profile digest, pinned policy and
   negotiated capabilities were checked, which preserved exactly the
   non-compositional path the second review had asked to remove. The profile
   is now a required operand, the record's own shape and seal are accepted
   before any binding field is read, and the cross-field-only rules live in
   the separately named `validate_session_binding_fields`.

3. **No durable entry aliases a caller's object** (§0.2, §12.9a).
   **Superseded:** the previous round's ledger, which verified the seal
   correctly and then stored the caller's exact dictionary and returned that
   same object. A caller could mutate what it was handed and thereby mutate
   the ledger's durable entry in place, leaving an invalid seal on evidence
   nobody deliberately wrote to and making replay comparison depend on whether
   an unrelated caller retained a reference.

   The correction states the underlying rule generally, because it is not
   specific to the ledger: sealing is a statement about BYTES, and "unchanged"
   means byte equality rather than object identity. Every component that
   accepts a sealed document now takes its own copy and returns a copy, and
   the certification entry points do the same.

## Clarification: posture occupancy is not the observation axis — 2026-08-23

**Nothing in §3.3, §7.3 or the successor table is superseded by this note.**
The nine-state agent-session axis stands exactly as frozen, `unknown` remains
terminal, and it is never promoted to `closed`. This clarification records
what that axis is NOT, because a consumer implemented it as though it were
also a resource lock.

**Observed in the v12 manager (W771, `2b077949-W771`).** The store enforced
"at most one live session per posture" with a partial unique index on
`agent_session_state`, so posture occupancy was a PROJECTION of what the
provider had been observed to do. The only value that freed a posture was
`closed` — which asserts that a terminal turn fact was observed for every turn
the epoch started. A session that ended before it initialized therefore had a
choice between stranding its posture forever and inventing an observation, and
the close path chose the second: it wrote `closed` over four states this
document's own successor table forbids, including `unknown`.

**Confirmed ruling by Slawomir, 2026-08-23**, recorded in full at
`work/records/2026/08/finding-agent-session-close-axis-conflict/`. Occupancy
is a separate manager-owned axis, `available -> occupied ->
recovery-required -> available`. Opening a session occupies the posture
atomically; a normally observed provider-session close returns it; ambiguity
moves it to `recovery-required`; and **silence and elapsed time never recover
it**. Leaving `recovery-required` takes positive evidence that the old
provider session cannot still act — for an OCI reference runtime, the adapter
observing the exact assignment container stopped or absent. A request to stop
is not that evidence; the observation is.

**Recovery does not rewrite observation history**, which is the point of the
separation. This durable result is coherent and is the normal shape after
transport loss:

```text
observation: unknown   runtime: stopped   slot: available   outputs: retained
```

Recovering a slot recovers EXECUTION CAPACITY only. It does not discard a
filesystem, accept an output or choose salvage; those remain independent
disposition decisions.

**For an implementer reading §7.3 alone:** the axis answers what the provider
was seen to do. It does not answer whether a posture may be reused, and a
consumer that derives the second from the first will eventually have to invent
the first to get the second.

## Correction: the tool-call `kind` — 2026-08-23 (W543)

**§6.2's row and `$defs.toolCallView` contradicted each other, and the
contradiction is corrected rather than left to each reader.** The prose said
`tool_call` "carries the ACP `toolCallId`, `kind`, `status`"; the schema
permitted only `tool_call_id`, optional `title` and `status` with
`additionalProperties: false`. A consumer following the prose expected
evidence the schema forbade; one following the schema silently discarded a
field the prose required. **The superseded schema shape and the superseded
prose row are both quoted in §6.2.1**, so the next reader can see which way it
was resolved and why.

**Confirmed ruling by Slawomir, 2026-08-23**, recorded in full at
`work/records/2026/08/finding-acp-tool-call-kind-contract-conflict/`: `kind`
is **portable but OPTIONAL advisory evidence**, copied verbatim when the
provider supplies one of the pinned ACP 1.3 `ToolKind` values and **omitted**
when it does not. **Baton never invents one** — absence does not become
`other`, and no title, tool name, command text, adapter family or later status
may be used to infer it. A value outside the pinned ten **refuses** rather
than silently widening a frozen contract. The field may support presentation
and decides no permission, policy, tool authority, turn outcome, success,
failure or disposition.

**Revalidated against the pinned SDK rather than inferred from either
artefact**, as the ruling required: `@agentclientprotocol/sdk` 1.3.0 declares
`kind?: ToolKind` on `ToolCall` and `kind?: ToolKind | null` on
`ToolCallUpdate`, and its `ToolKind` is exactly `read`, `edit`, `delete`,
`move`, `search`, `execute`, `think`, `fetch`, `switch_mode`, `other`. The
SDK's own comment — "Helps clients choose appropriate icons and UI treatment"
— is the presentation-only boundary the ruling states.

**The captured trace is now a positive example rather than an undecidable
gap.** `evidence/traces.json` records root-level `toolCallId` and `status`
with no `kind`, which is exactly the absent case: a provider that supplies no
kind produces a portable view without the member.

Changed in one act: this record's §6.2 row and new §6.2.1, `toolCallView` and
the new `toolKind` definition in the frozen schema, `normalize_tool_call` and
five focused cases in the executable model, the byte-identical product schema
copy, the v12 normalizer, and the v12 regressions — including one v12
assertion that required a supplied kind to be DISCARDED, which this ruling
supersedes and which is marked as superseded where it stood.

**Amended on independent review of the correction, 2026-08-23.** The first
draft quoted the SDK's nullability distinction and then normalized both
sources identically, which erases the only difference the declaration states.
An OMITTED member is absence on either source; an explicit `null` is the SDK's
own "not supplied" only on `tool_call_update`, and on the initial `tool_call`
it **refuses** as `integrity.schema`. And a refusal now tests the value's
SHAPE before its membership of the vocabulary, so no invalid value can leave
this boundary as a raw language exception instead of the closed pair: the
JavaScript consumer no longer serializes what it is rejecting and the Python
consumer no longer hashes it. Both consequences are stated in §6.2.1.

## Correction: one ACP capability representation — 2026-08-23 (W641)

**The frozen schema and the executable model required a representation §2.2
does not describe, and the correction REMOVES it rather than naming it.**
§2.2 says the relay's ACP `clientCapabilities` are exactly
`{ "fs": {}, "terminal": false }`. The `clientCapabilities` definition in this
record's schema instead REQUIRED `fs.read_text_file: false` and
`fs.write_text_file: false`, and `evidence/acp_boundary_model.py` used that
shape as `MINIMAL_CLIENT_CAPABILITIES`, validated it as the advertisement and
returned it as the negotiated document. A consumer copying the model —
which W4 did — sent snake_case field names on a transport that has none.

**Confirmed ruling by Slawomir, 2026-08-23**, recorded in full at
`work/records/2026/08/finding-acp-client-capability-wire-profile-conflation/`:
agent-session 1.0 keeps **one** ACP capability representation. The canonical
value is the pinned ACP wire structure, the profile persists that same
structural document, and the relay sends an owned copy of it. ACP's member
names and **omission semantics** are authoritative — an absent `readTextFile`
or `writeTextFile` means the capability was not advertised, and Baton does not
synthesize an explicit `false` to restate it.

**This supersedes the candidate boundary that would have kept a normalized
summary as a second named shape.** The `read_text_file`/`write_text_file`
representation is the contract defect to remove, not a representation to
maintain. A future provider-neutral capability model would be separately
justified Work with its own versioned contract.

**Validation is structural and order-independent.** JSON member order carries
no meaning, while an added member, a changed value, an enabled capability, a
snake_case transport member or an unsupported shape refuses `policy.denied`.
The exact minimal-capability policy of §2.2 is unchanged: withholding is still
total, and `session` is still stable and still not advertised.

Changed in one act: this record's `clientCapabilities` definition, the
executable model's constant and its structural validator, the captured
`evidence/traces.json` profile and its two negative capability vectors (with
the profile re-sealed), the byte-identical product schema copy, the v12
handshake constant and its consumers, and the focused regressions in both the
model and v12 — including two assertions that encoded the removed shape, each
marked superseded where it stood.
