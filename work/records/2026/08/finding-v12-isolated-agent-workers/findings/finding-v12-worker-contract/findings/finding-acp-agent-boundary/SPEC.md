# Baton ACP agent-session boundary contract

Version: `1.0-design`
Session family: `baton.agent-session`
Status: proposed normative design for W1440; not an implementation or wire
compatibility promise until approved.

## 0. Scope and precedence

This contract specifies the INNER boundary: how a trusted Baton component
drives one agent conversation for one runtime attempt, and how everything that
conversation produces is normalized into the outer worker-control vocabulary.

It specifies nothing else. It does not acquire source, materialize input,
start or stop a runtime, mint an assignment, publish a proposal, decide
intake, or touch the Baton authority. Those belong to W151 and W1439 and are
referenced here, never redefined.

Precedence is strict and one-directional:

1. `../../finding-v12-assignment-state-machine/SPEC.md` (W151) owns assignment
   identity, generations, fencing, typed gates, effectively-once settlement,
   runtime observation axes and receipt authority.
2. `../finding-worker-control-api-manifests/SPEC.md` (W1439) owns the outer
   protocol family `baton.worker-control`, the manifest family
   `baton.worker-manifest`, canonicalization, digests, limits, the credential
   and URI exclusions, and the CLOSED portable error taxonomy.
3. This document owns only the agent session beneath them.

If this document conflicts with either, that one wins and this design must be
revised. Nothing here adds a state to W151's machine or a category to W1439's
error taxonomy.

The accepted `v12/` proof remains valid inside its explicit `0-spike` scope.
Its `src/acp_session.mjs` already demonstrates four of the rules below —
capability negotiation before session use, exact required permission mode with
no fallback, an unexpected permission request treated as a policy failure, and
a manager-owned turn deadline distinct from setup supervision. This contract
generalizes those from one prototype against one adapter into a portable
boundary; it does not adopt the prototype's process-local session handling,
its single hard-coded posture, or its ad-hoc update channels.

### 0.1 Why this is a separate version axis

W1439 §2.2 permits a MINOR version to add manifest schemas, and W1439 §2.1
already treats `assignment_contract` as a third independent axis rather than a
field of the first two. Following that precedent, the agent session is a
FOURTH independent axis with its own family and its own exact version:

```json
{
  "session_family": "baton.agent-session",
  "version": { "major": 1, "minor": 0 }
}
```

The alternative — bolting agent-session state onto the frozen
`baton.worker-manifest/runtime-attempt` axes in W1439 §8.3 — was rejected
deliberately. The runtime-attempt axes describe a RUNTIME. An agent session is
a shorter-lived thing that lives inside one runtime, can end many times over
inside one attempt in later versions, and can be absent entirely for a runtime
that runs no model at all. Merging them would make `execution runtime` mean
two different things depending on which component wrote it, which is precisely
the confusion §12 exists to forbid.

An agent-session record is therefore bound BY DIGEST from the runtime-attempt
manifest's adapter diagnostics. Adapter diagnostics may be extended and cannot
alter portable lifecycle semantics (W1439 §8.3), which is exactly the
containment this axis needs.

### 0.2 The four documents

This family has four sealed documents, and no more:

| Document | Minted by | Lifetime |
| --- | --- | --- |
| `profile` | profile certification | pinned; one per certified agent runtime profile |
| `session` | the Session Relay | one per `(runtime_attempt_id, posture, session_epoch)` |
| `turn` | the Session Relay | one per supervised turn |
| `event` | the Session Relay, sequenced by the manager | one per normalized update |

Their durable digest member is `document_digest`, deliberately NOT
`manifest_digest`. W1439 §8 gives `manifest_digest` a precise meaning inside
`baton.worker-manifest`, and an agent-session document is not a member of that
family. Sharing the member name would make the two indistinguishable to
exactly the reader who most needs to tell them apart. It is computed the same
way — RFC 8785 canonical bytes, SHA-256, with the digest member itself omitted
(W1439 §3.2).

All four are sealed, including the normalized event. An event is a durable
document that a verifier reads later, so it carries its own digest for the
same reason the others do.

Sealing is a statement about BYTES. A component that accepts a sealed document
verifies the digest before reading any other field, and takes its own copy
rather than retaining the submitter's object; a component that returns one
returns a copy too. Byte equality is what "unchanged" means here. An entry
that aliases the caller's structure can be edited after acceptance, which
leaves an invalid seal on evidence nobody deliberately wrote to — and makes
every later comparison depend on who else still holds a reference.

### 0.3 Shared definitions are reproduced, not re-derived

W1439 owns `work_ref`, `assignment_ref`, `participant`, the artifact and
evidence references, the digest and timestamp forms, and the JSON-safe integer
bound. This family reproduces those definitions VERBATIM in
`schema/agent-session-1.0.schema.json`, and
`evidence/test_acp_boundary_model.py` asserts they stay byte-identical.

The rule this enforces is worth stating plainly, because a near-copy looks
harmless: **a document valid under this child must never be invalid under the
contract this child says takes precedence.** A locally re-derived
`participant` pattern or a relaxed artifact shape is not a spelling
difference; it is a second contract wearing the first one's name. If W1439
later revises one of these, the equality test fails and this document is
revised with it rather than drifting quietly.


A fifth axis already exists and is not ours: the ACP wire `protocolVersion`, a
plain integer owned by the Agent Client Protocol itself. §2 pins it; it is
never a Baton version.

## 1. Component roles

Five roles appear in this document. Trust is a property of the role, never of
the transport, the process tree or the reachability of a socket.

| Role | Trusted | Owns | Never |
| --- | --- | --- | --- |
| Worker Manager | yes | the only Baton authority client; assignment, fencing, deadlines, all outer control operations | speaks ACP directly |
| Session Relay | yes | one ACP CLIENT for one runtime attempt; policy pinning, normalization, redaction, flow control, the relay journal | holds Baton credentials, mutates authority state, or writes the workspace |
| Runtime Adapter | yes | runtime start/inspect/cancel/destroy per W1439 §6.2-6.3; for a non-ACP runtime it also hosts the normalizing adapter of §9 | interprets agent prose or reports facts stronger than its provider supplies |
| Agent endpoint | **no** | the conversation; tool calls inside its own runtime | is a Baton participant, holds a claim, or receives any Baton capability |
| Worker endpoint | **no** | the in-runtime component that later sends `result.declare` per W1439 §6.2 | is the same thing as the agent |

The Session Relay is the ACP CLIENT and the agent endpoint is the ACP AGENT.
That direction matters: in ACP the client is the side that grants filesystem
and terminal capability, answers permission requests and receives session
updates. Placing the relay on the client side is what makes §4's refusals
possible at all.

A relay handles exactly one runtime attempt. Two assignments never share one
ACP connection, one session, or one relay journal. Multiplexing would make the
per-assignment fence in §7 unenforceable at the transport layer.

## 2. Handshake and negotiated surface

### 2.1 A version is pinned where one exists, and certified where one does not

ACP has a wire version. The Codex App Server does not. These take two
different certification routes, and one is never spelled with the other's
vocabulary.

**ACP: pinned exactly, refused on mismatch.**
The relay sends `initialize` with the exact `protocolVersion` pinned in the
runtime profile, and the exact `clientInfo` naming the relay build.

ACP defines the response `protocolVersion` as "the protocol version the client
specified if supported by the agent, or the latest protocol version supported
by the agent". A response that does not equal the pinned integer therefore
means the agent does not support the pinned version. The relay refuses:
`refused.unsupported-version`, no session, no prompt, no downgrade, no retry
at a different version. Choosing a wire version is a profile-certification
decision, not something a live attempt gets to negotiate downward.

The observed ACP baseline for this design is `PROTOCOL_VERSION = 1` as shipped
by `@agentclientprotocol/sdk` 1.3.0 in the accepted proof. That is EVIDENCE of
what exists today. The portable rule is "pinned exactly and refused on
mismatch", never the literal `1`.

**A provider with no wire version: certified by binding.**
The App Server documents no `protocolVersion` anywhere in its initialization
(§10.1). There is therefore nothing to negotiate, nothing to compare, and no
downgrade to refuse — and copying ACP's rule onto it would produce a profile
that pins a number the provider never sends, which is worse than no check at
all because it looks like one.

Such a provider is certified instead by an exact `provider_binding`: the
server build identity, the SHA-256 digest of the interface description that
build was certified against, the certification instant, and
`experimental_api: false`. The adapter refuses `policy.profile-uncertified`
when the observed build or interface digest is not the certified one.

This REPLACES version negotiation for that provider; it is not a second
spelling of it. A profile carries exactly one of the two, and the schema
refuses a profile that carries both or neither. Asking an ACP profile for a
provider binding, or a provider profile for a version negotiation, is
`refused.unsupported-version`.

### 2.2 The relay advertises almost nothing

This applies to ACP, where the relay is the client. For the Codex App Server
the equivalent boundary is §10.1's `capabilities` object and §10.7's exclusion
list.

The relay's ACP `clientCapabilities` in 1.0 are exactly:

```json
{ "fs": {}, "terminal": false }
```

with `fs` empty (no `readTextFile`, no `writeTextFile`) and EVERY other client
capability omitted or null.

Every other one, not every unsafe one. The 1.3.0 declaration lists eight
members: `fs` and `terminal` are declared here as empty and false;
`positionEncodings`, `plan`, `auth`, `elicitation` and `nes` are marked
UNSTABLE by the SDK itself; and `session` is stable and is nonetheless not
advertised. Withholding by default costs nothing — an unadvertised capability
is one the agent simply does not have — while advertising by default means
every future SDK release silently widens the boundary.

This is the single most important line in the handshake, and it is a
capability boundary rather than a preference. ACP's client methods
`fs/read_text_file`, `fs/write_text_file`, `terminal/create`,
`terminal/output`, `terminal/release`, `terminal/wait_for_exit`,
`terminal/kill` and `mcp/connect` are capabilities the CLIENT grants to the
agent. The relay runs OUTSIDE the runtime's isolation boundary. Advertising
`fs` or `terminal` would hand the agent a file and process capability that
reaches around the very isolation the runtime exists to provide, and no
permission mode inside the agent can take it back.

An agent that calls an unadvertised client method is a policy failure
(§4.4), not a feature request.

### 2.3 Required and optional agent surface

**These sets belong to the version, not to a profile.** A certified profile
does not restate them, and the schema gives it nowhere to. A document that
could restate a rule could disagree with it, and a certified profile that
disagrees with the policy actually enforced is worse than no profile: it is a
second source of truth wearing the first one's authority. The same applies to
the six capabilities of §2.4, which a profile declares as an exact constant or
not at all.

Baseline, required of every agent endpoint, native or adapted:

`initialize`, `session/new`, `session/prompt`, `session/cancel`,
`session/update`.

An endpoint that cannot present all five is not an agent endpoint under this
contract and is refused `refused.capability` at handshake.

Optional, and usable only when the agent advertises it AND the runtime profile
pins its use:

`session/set_mode` (required in practice by §4.1 whenever the pinned policy
names a mode), `session/set_config_option`, `session/close`.

Refused in 1.0 whether or not advertised:

`session/load`, `session/resume`, `session/fork`, `session/list`,
`session/delete`, `authenticate`, `logout`, `providers/*`, `nes/*`,
`document/*`, `mcp/message`.

The history-bearing three — `load`, `resume`, `fork` — are refused for a
specific reason and not as caution. Each imports prior conversation the
manager did not materialize, did not digest-bind into the input manifest, and
cannot attribute to any assignment. W1439 §8.1 binds every input by digest;
a resumed session is unbound input entering through the side door.

### 2.4 Baton agent-session capabilities

Distinct from ACP's own capabilities. The relay and the agent endpoint agree
on a closed set that the manager records in the session record:

- `session.fresh` — a new session per `(runtime_attempt_id, posture, session_epoch)`, per §3.2 (mandatory in 1.0)
- `session.mode-pin` — the pinned mode can be enforced exactly
- `session.prompt` — one supervised turn
- `session.cancel` — cancellation can be ORDERED (never: observed)
- `session.update-normalization` — updates map to §6's closed set
- `session.permission-refusal` — approval requests can be refused without grant

All six are mandatory for a 1.0 agent session. `session.reuse` deliberately
does not exist in 1.0; there is nothing to negotiate.

### 2.5 Experimental and vendor surfaces

Every surface an underlying protocol marks unstable, experimental or under
development is ADAPTER-PRIVATE DIAGNOSTIC MATERIAL. It may appear in the
relay journal and in namespaced adapter diagnostics. It may never appear in a
normalized event, a portable observation, a manifest field, a disposition, a
gate, or an error category.

For ACP 1.3.0 this covers at least `providers/*`, `nes/*`, `session/fork`,
`document/*`, `mcpCapabilities.acp`, the agent-side `positionEncoding`, the
five client capabilities the declaration marks UNSTABLE
(`positionEncodings`, `plan`, `auth`, `elicitation`, `nes`), and every `_meta`
member. ACP reserves `_meta` and states that implementations MUST NOT make
assumptions about values there; a Baton relay therefore reads `_meta` only
into diagnostics and never into a normalized field. §10.7 gives the
corresponding list for the Codex App Server.

## 3. The assignment-scoped session

### 3.1 Session identity is not assignment identity

```json
{
  "agent_session_ref": {
    "runtime_attempt_id": "opaque manager attempt id",
    "posture": "consent | execution",
    "session_epoch": 1,
    "provider_session_id": "opaque, adapter-private"
  }
}
```

`posture` is part of the identity, not a property of it, for the reason §3.2
gives: one W151 runtime attempt hosts two different sessions, and they must
not be confusable.

`session_epoch` is a positive integer minted by the relay, monotonically
increasing within one `(runtime_attempt_id, posture)` pair, and incremented
for every new transport connection or new provider session. It is how §8.4
distinguishes "the same conversation" from "a conversation that merely looks
the same". Its counter is per posture, so a consent session and an execution
session under the same attempt both start at epoch 1 and are still distinct
identities.

`provider_session_id` is whatever the underlying protocol calls its session or
thread — an ACP `sessionId`, a Codex `threadId`. It is opaque, adapter-private
and diagnostic. Three things it explicitly is NOT:

- it is not a `work_ref` or an `assignment_ref`;
- it is not a Baton participant address, and no configured participant is ever
  derived from it; and
- it is not a claim, a Handler, a generation, or evidence of any of them.

`agent_session_ref` never appears in an `assignment_ref`, never substitutes
for one, and never authorizes anything. It labels evidence.

### 3.2 One fresh session per attempt, posture and epoch

W151 binds ONE `runtime_attempt_id` to the offer and later to the assignment,
and tracks the consent runtime and the execution runtime as separate axes on
that one attempt. This boundary follows it exactly:

**One fresh provider session per `(runtime_attempt_id, posture,
session_epoch)`.** At most one is open per posture at a time; a second
concurrent session for the same posture is
`runtime-observation.duplicate-runtime`.

A consent session is never reused as an execution session, and the model
refuses the promotion rather than leaving it to convention. It has no
workspace, no declared output and no assignment, and §4.2 says the postures
are never interchangeable — so "reuse" would mean either running execution
under a consent policy or mutating a live session's policy underneath the
agent. Starting execution is therefore a SECOND provider session under the
same manager attempt, with its own epoch counter, its own connection, its own
relay journal and its own pinned policy.

An earlier revision of this document said "one fresh session per runtime
attempt" while also requiring both postures. Those two statements could not
both be true. The rule above supersedes that phrasing; the two-posture
requirement was the one that was right.

The relay calls `session/new` exactly once per epoch with:

- `cwd` set according to the posture: for an execution session, the absolute
  workspace root the runtime adapter materialized for this exact assignment;
  for a consent session, the empty read-only scratch root, since a consent
  session has neither an assignment nor a workspace (§4.2). A profile pins the
  ROLE — `scratch` or `workspace` — and the adapter supplies the path for that
  role; a request builder never accepts a caller-chosen path, because that is
  how an execution workspace ends up mounted into a consent session;
- `mcpServers` empty, unless the pinned policy digest names servers, in which
  case exactly those and no others; and
- `additionalDirectories` omitted.

An execution session is never created before the exact live assignment is
projected (W1439 §6.2, `assignment.activate`), and its record carries that
exact assignment. A consent session is created before any claim exists and its
record carries `assignment_ref: null`, bound to the offer and attempt instead.

Three bindings follow, and all three are enforced rather than described:

| Rule | Enforced by |
| --- | --- |
| an execution session carries an exact assignment | schema conditional |
| a consent session carries none | schema conditional |
| the session ref's posture equals the record's posture | schema conditional |
| the assignment's `work_ref` equals the session's `work_ref` | semantic check (§12.4) |
| the Work ID carries its authority UUID prefix | semantic check (W1439 §12.1) |

The last two are cross-field equalities JSON Schema cannot express, so they
are required semantic validation with their own negative vectors rather than
prose.

### 3.3 Session end

The relay ends a session by `session/close` when the agent advertises it, and
otherwise by closing its side of the transport. Both are ORDERS, not
observations, and neither by itself closes the epoch's evidence.

The session record reaches `closed` only when a terminal turn fact was
observed for every turn the epoch started. An epoch that ends without one ends
at `unknown` and STAYS there — `unknown` is terminal, and it is the honest end
of an epoch whose ending nobody observed. Promoting it to `closed` because the
relay stopped listening would record knowledge that was never acquired.

Session end is not runtime end. Runtime end is W1439 §6.3 and W151's
`runtime-quiescence:<generation>` gate, and §7.4 forbids conflating them.

## 4. Policy: mode pinning and permission behaviour

### 4.1 The pinned policy is exact

Every posture pins a complete, provider-specific policy. For ACP that policy
is exactly one `session_mode_id`; for the Codex App Server it is the complete
`thread/start` and `turn/start` operands of §10.2 and §10.3. An ACP
`session_mode_id` is not an App Server policy and the schema refuses a profile
that offers one in the other's place.

**ACP.** The runtime profile names exactly one `session_mode_id`. After
`session/new` the relay:

1. reads `modes` from the response;
2. refuses `policy.denied` if `modes` is absent or `availableModes` is not an
   array — a mode that cannot be enforced has not been enforced;
3. refuses `policy.denied` if the pinned id is not in `availableModes`; and
4. calls `session/set_mode` when `currentModeId` differs, and refuses
   `policy.denied` if that call fails.

**Codex App Server.** The relay sends the complete pinned operands on
`thread/start` AND re-sends them on every `turn/start`, then compares what the
provider reports back. Any divergence is `policy.denied`.

Either way there is no fallback, no nearest match, and no "most restrictive
available" rule. A worker running under a permission posture nobody chose is
worse than a worker that did not run, because the second failure is visible.

### 4.2 Two postures, never interchangeable

| Posture | When | Workspace | Output | Claim | Purpose |
| --- | --- | --- | --- | --- | --- |
| `consent` | before any claim | none | none | none exists | the agent decides whether to accept the offered contract, and may produce a plan |
| `execution` | after `assignment.activate` | the materialized private workspace | the declared outputs | exact live assignment | the assigned work |

They carry different pinned policies, and a profile in which the two are equal
is refused at certification, not at run time. A profile whose consent posture
claims a workspace or a declared output is refused there too. The consent
posture performs no tool calls, has nowhere to write, and holds no Baton
capability of any kind; it cannot produce an accepted result or an assignment.

Any consent-posture session that issues an approval request, attempts a client
method, or reports a tool call with status `in_progress` or `completed` is a
policy failure. There is nothing for it to legitimately do.

### 4.3 An approval request is a failure, not a question

Under a pinned non-interactive policy, `session/request_permission` must never
arrive. When it does, the relay:

1. answers `{"outcome": {"outcome": "cancelled"}}` — the one ACP outcome that
   selects NOTHING;
2. never returns `{"outcome": "selected"}` with any `optionId`, whatever the
   option's `kind` (`allow_once`, `allow_always`, `reject_once`,
   `reject_always`) says — including the rejecting kinds, because selecting a
   REJECT option is still the client participating in an interactive decision
   loop the policy said would not occur;
3. records the request, its `toolCall.title` and the option set as bounded,
   redacted diagnostics;
4. marks the turn `policy-failed` (§5.2); and
5. enters the cancellation and quarantine path of §7.

An approval race — a request that arrives after cancellation was ordered, or
concurrently with one — takes the same answer. `cancelled` grants nothing in
either ordering, so there is no window in which racing changes the outcome.
This is why the answer is fixed rather than conditional on relay state.

### 4.4 Policy drift

Four further conditions are policy failures with the same handling:

- a `current_mode_update` moving the session off the pinned mode, or a
  provider reporting operands that differ from the pinned ones;
- an agent call to a client method the relay did not advertise (§2.2); and
- an agent call to a method §2.3 refuses.

The relay answers the underlying protocol's error for the call itself and
independently fails the turn. Answering an unadvertised `fs/write_text_file`
with an error and then continuing the turn would leave an agent probing the
boundary in a session Baton still treats as clean.

## 5. The turn contract

### 5.1 One supervised turn

The relay issues `session/prompt` with `prompt` content assembled only from
digest-bound material named in the input manifest (W1439 §8.1). Prompt content
in 1.0 is `text` and `resource_link` blocks — ACP's baseline — and other block
types require both the agent's `promptCapabilities` and an explicit profile
pin.

Every turn carries a MANAGER-OWNED deadline, separate from and additional to
any setup supervision. This is not defence in depth; setup supervision covers
`initialize`, `session/new` and `session/set_mode` and stops there, so a live
but silent agent inside a prompt would otherwise hold the canonical Handler
for as long as it stayed quiet, with no bound at all. A relay that cannot
express a positive turn deadline is refused at handshake.

### 5.2 Closed turn-outcome vocabulary

Every turn ends in exactly one of these, and nothing else:

| Outcome | Meaning | Turn conclusively ended? |
| --- | --- | --- |
| `completed` | the agent ended its turn normally | yes |
| `refused` | the agent declined to act | yes |
| `truncated` | a model or turn budget ended it | yes |
| `cancelled` | the turn ended after cancellation was ordered | yes |
| `agent-failed` | the agent reported a terminal error for this turn | yes |
| `policy-failed` | §4 was violated | yes (the relay ends it) |
| `timeout` | the manager deadline elapsed with no terminal fact | **no** |
| `transport-lost` | the epoch died before any terminal fact | **no** |

The last two are the honest ones. They say the relay does not know, and §5.4
forbids resolving them by inference.

ACP `StopReason` maps exactly:

| ACP `stopReason` | Baton turn outcome |
| --- | --- |
| `end_turn` | `completed` |
| `refusal` | `refused` |
| `max_tokens` | `truncated` |
| `max_turn_requests` | `truncated` |
| `cancelled` | `cancelled` |

A JSON-RPC error response to `session/prompt` is `agent-failed`. The error
payload is bounded, redacted, untrusted diagnostics and is never parsed to
select a different outcome.

### 5.3 What a completed turn does and does not prove

This table is the acceptance boundary of this contract, and every row is a
claim somebody could otherwise make from the same evidence.

| Fact | A terminal `stopReason` proves it? |
| --- | --- |
| the agent's turn ended | **yes** |
| the agent will send no further updates for this turn | **yes** |
| the agent process stopped | no |
| the runtime is quiescent | no |
| the workspace stopped changing | no |
| background work the agent started stopped | no |
| the declared output exists | no |
| the declared output is complete or correct | no |
| the work was done | no |
| Baton may publish | no |

A terminal `stopReason` is a fact about a CONVERSATION. Everything in the
lower rows is a fact about a RUNTIME or about Baton's authority, and it is
established by W1439 §6.2-6.4 and W151 respectively — `runtime.inspect`,
`output.freeze`, the exact live assignment.

### 5.4 Never infer a turn outcome

- Silence is not completion. A quiet agent is `timeout` at the deadline.
- Transport closure is not completion, cancellation or failure. It is
  `transport-lost`.
- An empty or absent update stream is not completion.
- A tool call reaching status `completed` is not turn completion, and a tool
  call reaching `failed` is not turn failure. ACP's `ToolCallStatus`
  (`pending`, `in_progress`, `completed`, `failed`) describes one tool call.
- Agent prose is never a turn outcome. An agent that writes "I have finished
  and everything passes" has produced text.
- Reachability of the transport, liveness of the process, or a heartbeat at
  any layer is not a turn outcome.

### 5.5 Turn outcome does not decide disposition

The worker endpoint declares disposition through `result.declare` (W1439
§6.2). The relay's turn outcome only GATES whether such a declaration may be
accepted at all:

| Turn outcome | Manager's handling |
| --- | --- |
| `completed` | accept `completed`, `unable` or `plan-rejected` as the worker declares |
| `refused` | accept only `unable` |
| `truncated` | accept only `unable` |
| `agent-failed` | accept only `unable`, and only once the workspace is quiescent and evidence is sealed |
| `cancelled` | accept none — the assignment is already ended and fenced (§7.1); material goes to `output.collect` quarantine |
| `policy-failed` | accept none — cancellation and quarantine |
| `timeout` | accept none — ambiguous path (§8.4) |
| `transport-lost` | accept none — ambiguous path (§8.4) |

A `plan-rejected` disposition is a decision by a trusted component about a
digest-bound plan, and it installs W151's `plan-revision:<plan digest>` gate.
It is never inferred from a `plan` or `plan_update` session update, and never
from the agent saying its plan was rejected.

## 6. Update normalization

### 6.1 The closed portable event set

A normalized agent event has a kind from exactly this set:

`agent-message`, `agent-reasoning`, `tool-call`, `tool-call-update`, `plan`,
`mode-change`, `usage`, `session-info`, `commands-changed`, `other`.

`other` is the deliberate escape hatch and carries only the source kind string
plus its bounded diagnostics. It exists so that an update type this contract
has never seen is COUNTED rather than dropped or guessed at.

### 6.2 ACP mapping

| ACP `sessionUpdate` | Normalized kind | Notes |
| --- | --- | --- |
| `agent_message_chunk` | `agent-message` | text and resource-link content only |
| `agent_thought_chunk` | `agent-reasoning` | content is diagnostics; never portable evidence |
| `user_message_chunk` | `other` | the relay authored the prompt; an echo is diagnostic |
| `tool_call` | `tool-call` | carries the ACP `toolCallId`, `kind`, `status` |
| `tool_call_update` | `tool-call-update` | status only from ACP's four values |
| `plan` | `plan` | digest-bound before any use beyond display |
| `plan_update` | `plan` | superseding entry under the same plan id |
| `plan_removed` | `plan` | explicit removal entry |
| `current_mode_update` | `mode-change` | also checked against §4.4 |
| `config_option_update` | `other` | |
| `session_info_update` | `session-info` | |
| `usage_update` | `usage` | integers only; never a limit or a decision |
| `available_commands_update` | `commands-changed` | |

### 6.3 Content restrictions

Normalized events carry `text` and `resource_link` content. `image`, `audio`
and embedded `resource` blocks are NOT inlined into a durable event under any
circumstance; the relay records the block type and byte count and drops the
bytes, or refuses the update as `integrity.limit` when the profile pins strict
handling. Inlining agent-supplied bytes into a durable event turns an
untrusted stream into permanent storage that every later reader must
re-validate.

Every normalized event is bounded by the negotiated `max_activity_bytes`
(W1439 §3.1) and redacted per W1439 §9 BEFORE it is durable — the relay is the
trust boundary, so redaction happens at the relay, not downstream.

### 6.4 Ordering, duplicates and lateness

Every normalized event is a SEALED document (§0.2): the relay stamps
`document_digest` over its canonical bytes before it is durable. A consumer
verifies that seal BEFORE it reads any other field, and answers with the same
sealed bytes — an event whose digest was never checked has no claim on any
rule below, and a consumer that appends its own bookkeeping to the document
invalidates the seal it just verified. It stores and returns copies rather
than the submitted object, per §0.2.

**What the seal covers is the FRAME, and nothing about observing it.**
`late` and the manager's `observation_seq` are properties of an OBSERVATION,
so they travel beside the document and are never folded into its bytes. The
reason is concrete: a retransmitted frame is the same frame. If lateness were
sealed in, the same frame observed twice — once before a turn ended and once
after — would carry two different digests, and an ordinary duplicate would be
indistinguishable from a spliced stream. Its lateness was decided when it was
first seen, and a replay reports that original observation rather than minting
a new one.

The relay assigns `source_seq`, a positive integer scoped to one
`(runtime_attempt_id, posture, session_epoch)`. The manager assigns its own
`observation_seq` when it persists the event, exactly as W1439 §10.5 requires
for runtime observations, and records it beside the sealed document. Replay
and drop status are reported the same way.

- Sequence is per epoch. A new epoch restarts at 1, and the epoch and posture
  are both part of the identity, so it never collides.
- An event whose `agent_session_ref` is not this session's is
  `runtime-observation.identity-mismatch`, and a non-positive `source_seq` is
  `integrity.schema`.
- A duplicate `source_seq` with identical content replays and is not persisted
  twice. With DIFFERENT content it is `integrity.digest` — the transport lied
  about ordering or the stream was spliced, and neither is a merge to attempt.
  Both sides are sealed, so the two `document_digest` values ARE the
  comparison; nothing has to be reconstructed to make it.
- A late event arriving after its turn's terminal fact is recorded with its
  own sequence and marked late. It never reopens the turn, never changes the
  turn outcome, and never contributes to a disposition.
- ACP's `messageId` groups chunks into one message. It is a grouping hint for
  display and it is not ordering, not identity, and not authority.

### 6.5 Flow control

The relay holds a bounded queue with pinned depth and byte caps. On overflow
it applies backpressure where the transport allows, and otherwise drops with a
COUNTED, durable overflow record naming the count and the byte total. An
unbounded relay queue turns a chatty agent into manager memory exhaustion, and
a silent drop turns a partial record into an apparently complete one.

Overflow never fails the turn by itself; it is evidence, and a profile may
pin a threshold above which it becomes a policy failure.

## 7. Cancellation

### 7.1 The order is fixed and it is not negotiable

```text
1. AUTHORITY   one transaction: fence the exact generation, end the
               assignment, clear Handler, derive phase=block with gate
               runtime-quiescence:<generation>          [W151 §7, ruling 1]
2. AGENT       order the agent session to cancel        [this contract]
3. RUNTIME     order the runtime to stop                [W1439 §6.3]
4. OBSERVE     inspect for quiescence, then absence     [W1439 §6.3, W151 §10.8]
```

Step 1 first, always. Publication authority dies before anything is asked to
stop, so there is no window in which a still-running agent holds a live
generation. Steps 2 and 3 are ORDERS. Step 4 is the only one that produces a
fact.

### 7.2 ACP cancellation is a notification

`session/cancel` is a NOTIFICATION. It has no response, no acknowledgement, no
error, and no completion. Sending it proves exactly one thing: that the relay
sent it.

ACP specifies that a cancelled turn ends with `stopReason: "cancelled"`. That
response — when it arrives — is the observable fact, and it is a fact about
the TURN. The relay therefore:

1. records `cancel-requested` with the send time;
2. waits for a terminal turn fact up to the pinned cancel-drain deadline;
3. on `cancelled` (or any other terminal `stopReason`), records
   `agent-turn-cancelled` with the observed reason; and
4. on deadline expiry with no terminal fact, records
   `agent-quiescence-unknown`.

The cancel-drain deadline is a manager-owned deadline distinct from the turn
deadline of §5.1, and it is pinned separately in the profile. A turn that
reaches step 4 takes outcome `timeout` — a manager deadline elapsed with no
terminal fact, which is exactly §5.2's definition — and it is reported as
`runtime-observation.quiescence-unknown`. It is NOT `cancelled`: `cancelled`
means the turn was observed to end, and nothing was observed here.

An agent that answers `end_turn` after cancellation was ordered is still
recorded as its observed reason with the cancellation noted. Relabelling it
`cancelled` would erase the fact that the agent finished on its own terms.

### 7.3 The agent-session observation axis

`agent_session_state` moves monotonically and never regresses:

```text
not-started -> initializing -> ready -> prompting -> turn-ended -> closed
                                          |
                                          +-> cancel-requested -> agent-quiescent
                                          |                    -> unknown
                                          +-> unknown
```

- `agent-quiescent` means a terminal turn fact was observed after cancellation
  was ordered. The conversation is over.
- `unknown` means no terminal fact was observed. It is not a failure state and
  it is not `closed`; it is the absence of knowledge, recorded as such.
- A later weaker observation refuses as `runtime-observation.state-regression`,
  reusing W1439's existing code rather than minting one.

### 7.4 Agent quiescence is not runtime quiescence

**`agent-quiescent` NEVER satisfies `runtime-quiescence:<generation>`.**

This is the acceptance boundary the assignment named, so it is stated flatly
and its reasoning is given rather than assumed. The gate asks whether the
RUNTIME that held generation N is absent. A finished conversation says nothing
about that: the agent process is still resident, its child processes are still
whatever it left them, background work it started is still running, its
filesystem is still mounted, and a new prompt would be served immediately.
`quiescent` and `destroyed` are different observations and only the second is
positive proof of absence (W151 §6), and an agent turn ending is weaker than
either.

The gate is satisfied only by W1439 §6.3 runtime inspection reaching positive
absence, or by W151's pinned certified-isolation clause journalled with its
evidence. There is no third path, and this contract does not create one.

The three symmetrical confusions this section forbids:

| Never read | As |
| --- | --- |
| an agent turn ending | the runtime being quiescent or destroyed |
| a provider thread or session id | a Baton participant, Handler or assignment |
| an ACP permission decision | assignment, workspace or publication capability |

## 8. Native relay obligations

### 8.1 Identity preservation

The agent endpoint receives the prompt content and nothing else. It never
receives, and the relay never forwards into any field or any prompt block:

- the Baton executable, configuration, database or any path to them;
- an authority UUID, `work_ref`, `assignment_ref`, generation or participant
  address as a CAPABILITY (a Work identifier may appear in the digest-bound
  human contract as TEXT the agent reads, which grants nothing);
- a claim token, offer token, credential or bearer of any kind — W1439 §6.1
  keeps the claim token on an ephemeral channel and it never reaches a session
  at all; or
- any route, endpoint or handler configuration.

In the other direction: any Baton-shaped identifier appearing in agent output
is UNTRUSTED PROSE. The relay never resolves it, never binds to it, and never
compares it to canonical state to "confirm" anything.

### 8.2 Audit

The relay keeps an append-only journal for one `(runtime_attempt_id, posture,
session_epoch)`, recording every JSON-RPC frame in both directions with the
relay's own observation time, redacted per W1439 §9 before it is durable. A
consent session and an execution session under the same attempt therefore have
separate journals, because they are separate sessions.

The journal is bound by digest into the agent-session record and referenced
from the runtime-attempt manifest's adapter diagnostics. It is evidence and it
is untrusted material for every consumer; it is never parsed to recover a
turn outcome, a disposition, or an identity.

### 8.3 Policy enforcement

The relay enforces §2.2, §2.3, §4 and §6.3 itself, at the boundary, before
the frame reaches anything durable. A relay that forwards a violation and
relies on a downstream check has already failed: downstream sees a normalized
event, and normalization is exactly where the violating detail was dropped.

### 8.4 Reconnect ambiguity

**A lost transport ends the epoch. The relay never resumes and never
re-prompts.**

The reasoning is specific rather than general caution. A turn that was
in flight when the transport died may have completed, partially completed, or
not started — and it had a writable workspace. Re-prompting a fresh session
with the same content would re-run side effects the manager cannot enumerate,
against a workspace that already contains the first attempt's partial output.
ACP 1.0 has no resumable turn: `session/load` and `session/resume` restore
CONVERSATION, not an in-flight turn, and §2.3 refuses them anyway.

So: the turn outcome is `transport-lost`, the session state is `unknown`, and
the attempt enters W151's ambiguity path — settle the exact operation, inspect
the exact runtime, and grant no capability while ambiguous. A new epoch may be
minted only after the runtime is positively re-identified per W151 §9
("Runtime running": reattach only with positive proof of the same runtime and
assignment; transport reachability alone is insufficient), or the assignment
is cancelled and a replacement waits behind the quiescence gate.

Transport reachability returning is not the runtime being the same runtime.

### 8.5 Cancellation forwarding

The relay forwards cancellation as §7.2 specifies: promptly, once, without
waiting for the manager's runtime step, and without treating the send as an
outcome. A relay whose transport is already dead records the send as failed
and the state as `unknown` — it does not report `agent-quiescent` because
there is no longer an agent to be quiescent.

## 9. Non-ACP adapter obligations

An adapter fronts a runtime whose agent speaks something other than ACP. It
presents §2-§8 to the manager and speaks the provider's protocol privately.

Four obligations, all of them refusals:

1. **Present the normalized boundary, not the provider surface.** Every
   provider concept maps to §5.2, §6.1 and §7.3 or it does not cross. There is
   no passthrough mode and no provider-shaped field in a portable event.

2. **Never report a fact stronger than the provider supplies.** If a provider
   cannot distinguish "the turn ended" from "the process ended", the adapter
   reports the weaker one. If it cannot distinguish "cancelled" from
   "finished", it reports what it observed and marks the ambiguity. Inventing
   the stronger fact is how a `runtime-quiescence` gate gets satisfied by a
   conversation.

3. **Refuse rather than approximate.** A provider with no equivalent of the
   pinned mode fails `policy.denied` at session setup. A provider that cannot
   refuse an approval without granting something fails the same way. A
   provider whose only cancellation is process termination does not have
   `session.cancel` and is refused at handshake — the manager will use the
   runtime path, which is honest, instead of a cancel that is really a kill.

4. **Bind adapter identity.** Adapter name, version and build digest are bound
   in the runtime-attempt manifest (W1439 §8.3). A different adapter build is
   a different adapter; conformance results do not carry across.

Adapter diagnostics are namespaced (`com.openai.codex-app-server/1`, and so
on) and cannot change portable states.

## 10. Codex App Server profile

Normative profile for adapting the OpenAI Codex App Server, whose JSON-RPC
interface is described at [Codex App Server](https://learn.chatgpt.com/docs/app-server)
(read 2026-08-21). The mapping is written against the STABLE surface only.

### 10.1 Handshake — no version to negotiate

| App Server | Baton |
| --- | --- |
| `initialize` request with `clientInfo` and `capabilities` | §2.1 provider binding |
| `initialized` notification | handshake complete; no session yet |

**The documented `initialize` carries no protocol version, in either
direction.** Its request takes `clientInfo` (`name`, `title`, `version`) and
an optional `capabilities` object; its response reports the user agent and
platform. There is nothing to pin and nothing to refuse a downgrade against,
so §2.1's provider-binding route applies: certification binds the exact server
build and the digest of the interface description it was certified against,
and an observed build or digest that is not the certified one is
`policy.profile-uncertified`.

`capabilities.experimentalApi` is **false**, always. Setting it is what
unlocks the experimental families §10.7 excludes, so the exclusion is enforced
at the handshake rather than by declining to call them later. The certified
binding records that value, so a profile cannot be certified with it on.
`optOutNotificationMethods`, `requestAttestation` and
`mcpServerOpenaiFormElicitation` are pinned by the profile if used at all and
are never varied per attempt.

The App Server answers a request sent before `initialize` with "Not
initialized" and a repeated `initialize` with "Already initialized". Both are
adapter-internal sequencing errors; neither is a Baton state.

Transport is stdio or a local socket. **WebSocket transport is excluded**
because the documentation marks it experimental and unsupported. That reason
is sufficient on its own and this contract rests on nothing further: the
remote-authentication mechanism has changed spelling between readings of the
page, and an exclusion whose rationale cites a flag name would need revising
every time the flag does. Separately and independently, any remote form
carries a bearer credential in the session path, which §8.1 and W1439 §13
exclude regardless of how it is configured.

### 10.2 Session and the pinned thread policy

| App Server | Baton |
| --- | --- |
| `thread/start` | §3.2 fresh session for one posture; the returned thread id becomes `provider_session_id` |
| `thread/started` notification | session `ready` |
| `thread/closed` notification | epoch ended; §7.3 applies |
| `thread/resume`, `thread/fork`, `thread/read`, `thread/list`, `thread/loaded/list`, `thread/inject_items`, `thread/rollback` | **refused**, per §2.3 |

The thread id is opaque, adapter-private and diagnostic. §3.1 applies without
exception: a thread is not a participant and not an assignment.

A certified profile pins the COMPLETE `thread/start` operands for each
posture. `session_mode_id` has no meaning here; these do:

| Operand | Consent | Execution |
| --- | --- | --- |
| `approvalPolicy` | `never` | `never` |
| `sandbox` | `readOnly` | `workspaceWrite` |
| `cwd` | the empty read-only scratch root | the materialized private workspace |
| `model` | pinned | pinned |

`approvalPolicy` is `never` in both postures and the schema pins it to that
constant, because `onRequest` and `unlessTrusted` are precisely the settings
that PRODUCE the approval requests §4.3 treats as policy failures. Choosing
either would mean certifying a profile whose normal operation is a refusal.
`dangerFullAccess` and `externalSandbox` are never pinned.

The profile names the cwd's ROLE — `scratch` or `workspace` — never a host
path, because the path is per-assignment and a profile that named one would
be a profile for one assignment.

`thread/status/changed` carries `notLoaded`, `idle`, `systemError` and
`active`. All four are adapter diagnostics. **`idle` is not quiescence** — it
is a thread with no active turn, which is §5.3's second row and nothing below
it. Mapping `idle` onto a Baton quiescence observation is the single most
plausible error available in this profile, which is why it is named here.

### 10.3 Turn

| App Server | Baton |
| --- | --- |
| `turn/start` | §5.1 supervised turn |
| `turn/started` (`status: "inProgress"`) | session `prompting` |
| `turn/completed` `status: "completed"` | turn outcome `completed` |
| `turn/completed` `status: "interrupted"` | turn outcome `cancelled` |
| `turn/completed` `status: "failed"` | turn outcome `agent-failed`, refined by §10.6 |
| `turn/steer` | **not used in 1.0** — one prompt per turn |
| `turn/start` operands | re-pinned in full on every turn; see below |
| `turn/diff/updated` | diagnostics; never an output descriptor and never collected |
| `turn/plan/updated` | normalized `plan`; entry statuses `pending`, `inProgress`, `completed` are the provider's and are not §5.2 outcomes |

**The policy is re-pinned on every `turn/start`, in full.** `turn/start`
accepts `approvalPolicy`, `sandboxPolicy`, `cwd`, `model` and other overrides
of the thread defaults, so a turn that omits them INHERITS whatever the thread
carries. A thread-level default nobody restated is not a pinned policy: it is
a value the profile happened to set once, and one `thread/start` the adapter
did not send — a reattach, a resumed connection, a provider default change —
silently replaces it. Re-pinning makes the operative policy a fact about the
turn.

The pinned execution turn is therefore `approvalPolicy: "never"` with
`sandboxPolicy: {"type": "workspaceWrite", "networkAccess": false}`, and the
pinned consent turn is `approvalPolicy: "never"` with
`sandboxPolicy: {"type": "readOnly"}`. An observed operand that differs from
the pinned one, in either stage, is `policy.denied` and the turn is
`policy-failed`.

`collaborationMode` is experimental and is never sent. `outputSchema`,
`effort`, `summary` and `personality` are pinned by the profile or omitted;
they are never varied per attempt, because a per-attempt variation is a policy
nobody certified.

The App Server's three terminal statuses do not include ACP's `refusal`,
`max_tokens` or `max_turn_requests`. The adapter does not synthesize them from
prose or from token counts; §10.6 handles the one case the provider does
report structurally.

### 10.4 Items

`item/completed` is authoritative for an item; `item/started` and every
`item/*/delta` notification are advisory streaming. The adapter normalizes
from `item/completed` and treats deltas as bounded diagnostics.

| Item type | Normalized kind |
| --- | --- |
| `agentMessage` | `agent-message` |
| `reasoning` | `agent-reasoning` |
| `plan` | `plan` |
| `userMessage` | `other` |
| `commandExecution`, `fileChange`, `mcpToolCall`, `collabToolCall`, `webSearch`, `imageView` | `tool-call` / `tool-call-update` |
| `dynamicToolCall` | **refused** — experimental (§10.7) |
| `contextCompaction`, `enteredReviewMode`, `exitedReviewMode` | `other` |

`fileChange` items are `tool-call` evidence. They are not an output
descriptor, not a frozen result, and not a proposal; output is W1439 §6.4 and
§7.4, reading declared paths from the sealed workspace.

### 10.5 Approvals

Every server-initiated approval is an unexpected approval under a pinned
non-interactive policy, so §4.3 applies to all of them:

**Each family has its own response schema, so each has its own typed denial —
and every one of them is an OBJECT.** The provider's four response schemas all
declare `type: object`; `"decline"` on its own is the decision MEMBER, not the
response. A reply the provider cannot parse leaves the request hanging, which
is a worse failure than an honest grant, because nothing reports it.

| Request | Denial response | Never |
| --- | --- | --- |
| `item/commandExecution/requestApproval` | `{"decision": "decline"}` | `"accept"`, `"acceptForSession"`, `{"acceptWithExecpolicyAmendment": …}` as the decision |
| `item/fileChange/requestApproval` | `{"decision": "decline"}` | `"accept"`, `"acceptForSession"` as the decision |
| `item/permissions/requestApproval` | `{"permissions": {}, "scope": "turn"}` | any non-empty `permissions`, `"scope": "session"` |
| `mcpServer/elicitation/request` | `{"action": "decline", "content": null}` | `{"action": "accept", …}` |
| `tool/requestUserInput` | **unanswerable** — experimental (§10.7) | answering it at all |

The permissions family takes a GRANTED SUBSET and a scope rather than a
verdict, so its denial is the empty subset at the narrowest scope. There is no
documented cancel form for it, and none is needed: an empty subset grants
nothing in either ordering.

Where the turn is already being cancelled, the two decision-shaped families
answer `{"decision": "cancel"}` and the elicitation family answers
`{"action": "cancel", "content": null}`. Neither grants, so the approval race
of §4.3 resolves identically whichever ordering happens.

**Conformance here is validated against the provider's own schemas, never
against a payload this record wrote.** `evidence/provider-schemas/`
`codex-app-server/` holds the four response schemas captured from the
certified build, and the certified `provider_binding.interface_digest` is the
digest of that bundle. An equality assertion against a self-authored payload
proves only that the record is self-consistent, which is exactly what the
first revision of this section proved while specifying a reply the provider
would have rejected.

`additionalPermissions` in an approval request is experimental and is never
populated. In every case the turn becomes `policy-failed` and §7 follows —
answering is how the relay stays well-behaved toward the provider, not a
reason to continue.

`serverRequest/resolved` is a confirmation notification and is diagnostics.

### 10.6 Cancellation and errors

`turn/interrupt` is a REQUEST, so unlike ACP's notification it has a reply.
The reply is still not an outcome: it means the interruption was accepted for
processing. The observable fact remains `turn/completed` with status
`interrupted`, and §7.2's four steps are unchanged — `cancel-requested` on
send, `agent-turn-cancelled` on the terminal notification,
`agent-quiescence-unknown` on drain-deadline expiry.

`codexErrorInfo` on a failed turn maps into W1439's CLOSED taxonomy. Nothing
new is minted:

| `codexErrorInfo` | Turn outcome | Reported as |
| --- | --- | --- |
| `ContextWindowExceeded` | `truncated` | `unavailable.source-provider` |
| `UsageLimitExceeded` | `agent-failed` | `unavailable.source-provider` |
| `HttpConnectionFailed`, `ResponseStreamConnectionFailed`, `ResponseStreamDisconnected`, `ResponseTooManyFailedAttempts` | `agent-failed` | `unavailable.transport` |
| `Unauthorized` | `agent-failed` | `policy.denied` |
| `SandboxError` | `agent-failed` | `policy.denied` |
| `BadRequest`, `InternalServerError`, `Other` | `agent-failed` | `unavailable.source-provider` |

`ContextWindowExceeded` is the one case where the provider reports the budget
exhaustion structurally, which is why §10.3 defers to here rather than calling
every failure `agent-failed`. The raw `codexErrorInfo` string is retained as
untrusted diagnostics; it selects nothing beyond this table, and an
unrecognized value takes the last row.

### 10.7 Excluded surfaces

Adapter-private diagnostics at most; never portable, never called:

- **Experimental (`capabilities.experimentalApi`)**: the whole `process/*`
  family (`process/spawn`, `process/writeStdin`, `process/resizePty`,
  `process/kill`, `process/outputDelta`, `process/exited`),
  `thread/turns/list`, `thread/items/list`, `thread/backgroundTerminals/*`,
  `experimentalFeature/list`, `environment/info`, `permissionProfile/list`,
  `collaborationMode/list`, dynamic tools and `dynamicToolCall` items,
  `additionalPermissions` in approvals, and `tool/requestUserInput`.
- **Under development**: `plugin/list`, `plugin/read`, `plugin/install`,
  `plugin/uninstall`.
- **Deprecated**: `thread/rollback`.
- **Experimental transport**: WebSocket, per §10.1.
- **Outside this boundary entirely**: `command/exec` and its family, `fs/*`,
  `thread/shellCommand`, `config/*`, `configRequirements/read`, `skills/*`,
  `hooks/list`, `marketplace/*`, `app/*`, `mcpServer/*` management,
  `model/list`, `modelProvider/capabilities/read`, `feedback/upload`,
  `windowsSandbox/*`, `externalAgentConfig/*`, `review/start`.

The last group is not excluded for being unstable. Those are host-application
capabilities — running commands, writing files, editing configuration,
installing plugins. The manager does not call them, and an adapter that
exposes them upward has moved the isolation boundary without saying so.

`process/*` deserves its own sentence, because it is the one an implementer
would most plausibly reach for: it starts processes OUTSIDE the sandbox. It is
experimental, and even if it were stable it would be the wrong tool — runtime
lifecycle is W1439 §6.2-6.3, through the runtime adapter, against an opaque
runtime identity the manager can inspect.

## 11. Errors: reuse, never extend

W1439 §11 declares its taxonomy CLOSED for version 1.0. This contract adds no
category and no code, and the schema enforces that rather than trusting it:
`errorCategoryCode` is a `oneOf` over the seven categories, each with its own
exact code enum. An invented code is refused, and so is a REAL code under the
wrong category — `policy.state-regression` is as invalid as
`policy.agent-said-no`, because a pair is the unit and either half being right
proves nothing.

Agent-session failures map into the existing taxonomy:

| Agent-session condition | Category.code |
| --- | --- |
| pinned ACP wire version not supported | `refused.unsupported-version` |
| version negotiation attempted against an unversioned provider | `refused.unsupported-version` |
| uncertified provider build or interface digest | `policy.profile-uncertified` |
| missing required agent method | `refused.capability` |
| refused method used (§2.3) | `refused.capability` |
| unnegotiated extension or `_meta` relied upon | `refused.extension` |
| mode absent, unavailable, or drifted | `policy.denied` |
| provider policy operands drifted from the certified ones | `policy.denied` |
| unexpected approval request | `policy.denied` |
| unadvertised client method called | `policy.denied` |
| consent-posture session acting | `policy.denied` |
| event over the negotiated byte limit | `integrity.limit` |
| duplicate `(epoch, source_seq)` with different content | `integrity.digest` |
| unnormalizable content block | `integrity.schema` |
| event from a different agent session | `runtime-observation.identity-mismatch` |
| a second concurrent session for one posture | `runtime-observation.duplicate-runtime` |
| execution session with no assignment, or consent session with one | `refused.precondition` |
| assignment bound to a different Work | `integrity.schema` |
| observation regression on `agent_session_state` | `runtime-observation.state-regression` |
| agent quiescence unknown after cancel drain | `runtime-observation.quiescence-unknown` |
| agent endpoint unreachable | `unavailable.transport` |
| provider or model backend failure | `unavailable.source-provider` |
| act attempted against an ended generation | `stale-assignment.ended` |

`retry` and `operation_state` take W1439 §11's meanings. A turn `timeout` or
`transport-lost` that leaves an operation unsettled is `reconcile` with
`operation_state: "unknown"`, never `unsubmitted`.

Provider error strings never select a category. The trusted adapter maps
OBSERVED FACTS to this table and keeps raw detail as untrusted evidence.

## 12. Required semantic validation beyond JSON Schema

A conforming implementation proves all of these, in addition to W1439 §12:

1. Every definition this family reproduces from W1439 is byte-identical to the
   frozen one (§0.3), so no document valid here is invalid there.
2. For an ACP profile, the negotiated wire version equals the pinned version
   exactly; for a provider profile, the observed build and interface digest
   equal the certified binding and `experimental_api` is false. A profile
   carries exactly one of the two routes.
3. Advertised ACP client capabilities are exactly the withheld set of §2.2 —
   no filesystem, no terminal, and no other member, stable or experimental.
4. No refused method (§2.3) was sent, and no unadvertised client method was
   served.
5. At most one session is open per `(runtime_attempt_id, posture)`;
   `session_epoch` is positive and strictly increasing within that pair; and
   no consent session was reused as an execution session.
6. An execution session carries an exact assignment whose `work_ref` equals
   the session's `work_ref`; a consent session carries none; the session ref's
   posture equals the record's; and every Work ID carries the first eight
   characters of its authority UUID. A session record is validated ONLY
   together with the profile it claims — shape and seal first, then the
   bindings, then the profile relationship. A record is a claim about a
   certification, and a claim nobody checks against that certification is not
   evidence, so there is no form of this check that omits the profile.
7. The whole session ran under the pinned policy — the exact
   `session_mode_id` for ACP, or the exact `thread/start` AND `turn/start`
   operands for the App Server, re-sent on every turn — and the session record
   names the profile digest it actually ran under.
7a. The profile itself is certified by ONE entry point that every path uses,
   and that entry point composes three checks IN ORDER — durable shape, then
   seal, then policy — before it reads a single policy field. Reading a policy
   field out of a document whose shape was never checked or whose seal was
   never verified is reading whatever the last writer put there, so proving
   the three separately in tests does not make the runtime path compose them.
   The policy layer requires the exact six session capabilities; the posture
   invariants (consent has no workspace and no declared output, execution has
   both); the posture-bound provider operands, so a consent posture cannot pin
   `workspaceWrite` or a workspace cwd and an execution posture cannot pin
   `readOnly` or a scratch cwd; and exactly one of the version-negotiation or
   provider-binding routes. A partial helper that checks only one layer may
   exist for isolated verification, but it is named as a partial helper and is
   never the certification entry point.
7b. Every request operand comes from the pinned policy. A `cwd` is selected by
   the profile's pinned ROLE from a supplied role-to-path map, never taken as
   a caller-chosen path.
8. No permission or approval response selected an option, granted a scope, or
   returned a non-empty permission subset; every denial matched its family's
   documented reply shape.
9. Every normalized event is a sealed document whose `document_digest`
   recomputes BEFORE any other field is read, has a kind in §6.1's closed set,
   is within `max_activity_bytes`, and was redacted before persistence. A
   consumer answers with the same sealed BYTES and reports lateness,
   observation sequence and replay or drop status beside it.
9a. No durable entry aliases a caller's object, in either direction. "Sealed"
   and "unchanged" are statements about bytes, not about object identity:
   immutable evidence a caller can still reach and edit is not immutable, and
   a replay decision that turns on whether some unrelated caller retained a
   reference is not a decision about content.
10. `source_seq` is positive, unique within its `(attempt, posture, epoch)`,
    and duplicate sequences carry identical arriving content.
11. `agent_session_state` never regresses.
12. The turn outcome is in §5.2's closed set and is derived only from a
    terminal provider fact, a policy failure, the manager deadline, or
    transport death — never from prose, tool status, silence or reachability.
13. `agent-quiescent` is never cited as evidence for a
    `runtime-quiescence:<generation>` gate.
14. No `agent_session_ref` member appears in an `assignment_ref`, and no
    participant, generation or Handler is derived from a provider session id.
15. A `result.declare` was accepted only where §5.5 permits it for the
    observed turn outcome.
16. Every reported error is a category/code PAIR from W1439 §11 — a real code
    under the wrong category is refused.
17. No credential, token or bearer appears in any session record, journal
    entry, normalized event or prompt block.
18. Consent-posture sessions performed no tool call and produced no output.

## 13. Security and privacy invariants

- The relay is the trust boundary. Redaction, bounding and refusal happen
  there, before anything durable exists.
- The agent endpoint holds no Baton capability at any point in its lifetime.
  Not before the claim, not during the assignment, not at cancellation.
- Client-granted filesystem and terminal capability is withheld structurally
  (§2.2), not by policy, because a policy inside the agent cannot revoke a
  capability the client already advertised.
- Cancellation kills publication authority before anything is asked to stop
  (§7.1).
- An agent's own account of what it did is evidence for a human or a verifier
  to read. It is never an input to a Baton state transition.
- A provider surface marked experimental, unstable or under development never
  becomes portable semantics, however convenient the fact it reports.
- Ending a conversation is never proof of ending a runtime (§7.4).

## 14. Conformance-ready traces

`evidence/traces.json` carries 19 machine-readable end-to-end traces, 78
negative vectors and 3 invalid document vectors, each with its expected
normalized outcome or its expected category/code refusal. They are the
vocabulary the W1441 conformance contract consumes; they are not a test
harness for any product.

Every trace builds real sealed schema documents and feeds THOSE documents to
the semantic model, so the two cannot drift apart into separate contracts.

Nine traces cover the ACP boundary:

| Trace | Exercises |
| --- | --- |
| `normal-completion` | handshake, pinned mode, one turn, `end_turn` -> `completed`, `result.declare` accepted |
| `agent-refusal` | `refusal` -> `refused`, only `unable` accepted |
| `ordered-cancellation` | fence-first ordering, `session/cancel`, `cancelled`, `agent-quiescent`, gate NOT satisfied |
| `cancel-drain-timeout` | cancellation ordered, no terminal fact, `agent-quiescence-unknown` |
| `transport-loss-midturn` | epoch death, `transport-lost`, no resume, no re-prompt, ambiguous path |
| `duplicate-and-late-events` | identical duplicate replays, conflicting duplicate refuses, late event does not reopen the turn |
| `policy-refusal` | unexpected approval, `cancelled` outcome selected, nothing granted, `policy-failed` |
| `approval-race` | approval arriving after cancellation was ordered; identical answer, no grant |
| `consent-then-execution` | one W151 attempt, a consent session at epoch 1 with a null assignment, promotion refused, claim settled, a SEPARATE execution session at its own epoch 1 bound to generation 7 |

Ten more cover the Codex App Server profile: normal completion asserting the
complete pinned `thread/start` and `turn/start` operands and a null negotiated
wire version; policy drift refused; an interrupted turn where the
`turn/interrupt` reply is explicitly not the outcome; `ContextWindowExceeded`
reaching `truncated`; `Unauthorized` reaching `policy.denied`; an unrecognized
`codexErrorInfo` taking the last row of §10.6 rather than inventing one; and
one trace per approval family asserting its exact typed denial payload.

The 78 negative vectors cover, among others: a downgraded wire version; a
missing required agent method; ACP negotiation attempted against a provider
profile and provider binding attempted against an ACP profile; an uncertified
build, an uncertified interface digest, and a binding enabling the
experimental API; an advertised `terminal` or `fs` capability; a served
`fs/write_text_file`; `session/resume`; an absent or unavailable pinned mode;
mode drift; identical consent and execution postures; a consent posture with a
workspace; Codex approval-policy drift, turn sandbox drift to
`dangerFullAccess` and thread sandbox drift; a selected `reject_once` option;
each of the four granting Codex answers including
`acceptWithExecpolicyAmendment` and a non-empty permission subset;
`completed` declared after a refusal; any disposition after cancellation;
cancellation ordered before the authority fence; an `agent-quiescent`
observation cited for a runtime-quiescence gate; a session axis regression;
`unknown` promoted to `closed`; a conflicting duplicate sequence; a zero
`source_seq`; an event from another epoch; an unredacted event; a tampered
event seal; an over-limit event; an execution session without an assignment; a
consent session with one; a cross-Work assignment binding; a posture mismatch
between ref and record; a Work ID whose authority prefix does not match; a
consent session promoted to execution; a second concurrent session for one
posture; a provider session id used as a participant; an `agent_session_ref`
carrying a generation or missing its posture; a re-prompt after transport
loss; outcomes inferred from silence, prose and tool status; `process/spawn`;
`command/exec`; `thread/resume`; `dynamicToolCall`; an attempt to answer
`tool/requestUserInput`; and Codex `idle` read as quiescence.

Added after the second review: a bare decision member offered as a command or
file-change response and refused by the provider's own schema; each granting
decision recognized through the `{"decision": …}` envelope; swapped Codex
posture policies; a consent posture pinning `workspaceWrite`; an execution
posture pinning a scratch cwd; a profile declaring a narrow capability set; a
consent posture declaring a workspace; an execution posture declaring no
output; an arbitrary path injected into a request; an unsealed event handed to
the ledger; a sealed event tampered with a VALID kind so that only the digest
catches it; a session record naming a different profile; and a session record
running a policy its profile did not certify.

Added after the third review: a schema-invalid profile reaching certification
and reaching ACP negotiation; a stale-seal profile reaching certification and
reaching provider binding; a session record with a stale seal, an extra member,
a wrong profile digest, or an uncertified pinned policy; a session record
offered for validation without its profile at all; and the posture-swap and
narrow-capability profiles routed through the composing entry point, where the
shape layer refuses them before the policy layer is reached.

The three invalid document vectors are `policyFailure` documents the schema
must refuse: an invented error code, a real code under the wrong category, and
a policy failure claiming it granted something.

## 15. Design evidence and approval boundary

- `schema/agent-session-1.0.schema.json` is the machine-readable shape
  contract for the session profile, session record, turn record and normalized
  event. Its identity, participant, artifact and evidence definitions are
  reproduced verbatim from W1439 and asserted byte-identical (§0.3).
- `evidence/traces.json` holds the traces and negative vectors of §14.
- `evidence/provider-schemas/codex-app-server/` holds the four App Server
  approval response schemas captured from the certified build, with their
  provenance. Every denial payload in §10.5 is validated against them.
- `evidence/acp_boundary_model.py` and `evidence/test_acp_boundary_model.py`
  are an executable design model of the cross-field rules JSON Schema cannot
  express: handshake refusal, capability withholding, mode pinning, permission
  refusal, turn-outcome derivation, update normalization, sequence and
  lateness handling, the monotonic session axis, the quiescence separation,
  and the Codex mapping.

All of it is design evidence. It imports no Baton or `v12/` product code, runs
without a model provider, and certifies no runtime.

Approval is requested for these decisions as one compatible set:

1. **The agent session is a fourth independent version axis** with its own
   family, bound by digest into adapter diagnostics rather than added to the
   frozen runtime-attempt axes (§0.1), and it reproduces W1439's shared
   definitions verbatim rather than re-deriving them (§0.3).
2. **The relay is the ACP client and withholds filesystem and terminal
   capability structurally** (§2.2), and refuses the history-bearing session
   methods (§2.3).
3. **One fresh session per `(attempt, posture, epoch)`**, with no reuse,
   resume or fork in 1.0, no promotion of a consent session into an execution
   session, and no re-prompt after transport loss (§3.2, §8.4).
3a. **The version owns the method and capability sets, and one validator
   certifies every profile** — posture invariants, posture-bound provider
   operands, and exactly one certification route (§2.3, §12.7a).
3b. **A sealed event crosses the boundary unchanged**: the seal is verified
   before any other field is read, the same sealed bytes are returned, and
   lateness, observation sequence and replay status travel beside it because
   they describe the observation rather than the frame (§6.4).
3c. **Certification composes shape, seal and policy in that order at one
   entry point**, a session record is validated only together with the profile
   it claims, and no durable entry aliases a caller's object (§0.2, §12.7a,
   §12.9a).
4. **Exact policy pinning with no fallback — one ACP mode, or the complete
   App Server operands re-sent on every turn — and an approval request is a
   policy failure that grants nothing**, including never selecting a rejecting
   option and never returning a non-empty permission subset (§4, §10.5).
4a. **A provider with no wire version is certified by an exact provider
   binding**, never by pinning a version it does not send (§2.1, §10.1).
5. **The closed turn-outcome vocabulary of §5.2 and the closed normalized
   event set of §6.1**, with turn outcome gating but never deciding
   disposition (§5.5).
6. **Cancellation is ordered intent plus observed quiescence, and agent
   quiescence never satisfies a runtime-quiescence gate** (§7).
7. **The Codex App Server profile of §10**, including its explicit exclusion
   of every experimental, under-development, deprecated and host-application
   surface, and its complete typed denial RESPONSE per approval family
   validated against the provider's captured response schemas (§10.5).
8. **W1439's error taxonomy is reused unchanged and enforced pairwise in the
   schema**; agent-session conditions map into it, no category or code is
   added, and a real code under the wrong category is refused (§11).

Approval freezes this boundary for the dependent conformance Work W1441. It
does not authorize implementation, and it does not certify any adapter,
provider or runtime.
