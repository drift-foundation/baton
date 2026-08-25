# Finding: reconcile ACP tool-call kind across prose and schema

Discovered during W4/W2929 event-normalization review on 2026-08-23.
Canonical Baton Work: W543 (`2b077949-W543`).

## Observed

The frozen ACP boundary disagrees with itself about the portable tool-call
view:

- `work/records/2026/08/finding-v12-isolated-agent-workers/findings/
  finding-v12-worker-contract/findings/finding-acp-agent-boundary/SPEC.md`
  §6.2 says `tool_call` carries ACP `toolCallId`, `kind`, and `status`.
- The same record's frozen `schema/agent-session-1.0.schema.json`
  `$defs.toolCallView` permits only `tool_call_id`, optional `title`, and
  `status`, with `additionalProperties: false`.
- Its captured `evidence/traces.json` proves root-level `toolCallId` and
  `status`, but the trace carries no `kind`, so it cannot decide the conflict.

The W4 implementation correctly declined to invent a portable `kind` member
while the frozen artefacts conflict. This is not resolved by that omission:
any later consumer relying on the prose will expect evidence the schema
forbids, while a consumer relying on the schema will silently discard a field
the prose requires.

## Confirmed boundary

This is a contract correction, not a W4 implementation choice. Preserve the
current W4 behavior until the owning ACP boundary is ruled and amended. The
old decision text must be explicitly marked corrected or superseded rather
than silently rewritten, and the prose, schema, examples, model, captured
evidence interpretation, and product copy must finish in one state.

## Open decision

Decide whether ACP `kind` is portable in agent-session 1.0 or remains
adapter-private diagnostics. Revalidate the pinned ACP SDK/provider shape
before ruling; do not infer the answer from the current W4 code or its tests.

## Confirmed ruling — 2026-08-23

**Confirmed by Slawomir.** ACP `kind` is portable but optional advisory
evidence in agent-session 1.0. The pinned ACP 1.3 SDK permits it on a tool
call and tool-call update but does not require it. Baton therefore copies a
valid `kind` when the provider supplies one and omits the member when the
provider does not.

Baton never invents a kind. Absence does not become `other`, and no title,
tool name, command text, adapter family, or later status may be used to infer
one. A missing kind is simply missing evidence.

When present, the value must be one of the pinned ACP 1.3 `ToolKind` values:
`read`, `edit`, `delete`, `move`, `search`, `execute`, `think`, `fetch`,
`switch_mode`, or `other`. A value outside that closed versioned vocabulary
refuses rather than silently widening the frozen contract. Supporting a later
ACP vocabulary requires explicit version/certification work.

The field may support presentation, such as a tool-category label or icon. It
must not decide permission, policy, tool authority, turn outcome, success,
failure, or disposition. The correction must update the old §6.2 prose,
schema, examples, executable model, captured-evidence interpretation, product
schema copy, normalizer, and focused present/absent/invalid regressions as one
contract change.

## Independent review — 2026-08-23

**Accepted:** the corrected prose, frozen and byte-identical product schemas,
ten-value vocabulary, present/absent behavior, sealed advisory evidence, and
presentation-only authority agree. A consumer sweep found no runtime reader
beyond the executable model and v12 normalizer.

**Observed; changes requested.** Those two consumers erase the exact pinned
SDK distinction they document: `ToolCall.kind` does not admit null, while
`ToolCallUpdate.kind` does. Initial `tool_call` with `kind: null` is currently
accepted as absence. Omission is absence on either source; explicit null is
absence only on `tool_call_update`; it refuses as `integrity.schema` on the
initial call.

Invalid non-string values must also stay in the closed taxonomy. JavaScript
BigInt currently leaks `TypeError` through diagnostic serialization, while
Python list/dict values leak unhashable `TypeError` through set membership.
Validate string shape before vocabulary membership and format refusals without
serializing rejected caller values.

The review authorizes migrating the existing null-absence fixtures to
`tool_call_update` while retaining their omission assertions. Full findings
and verification: `review-2026-08-23T19-05-30Z.md` and
`evidence/review-round1-2026-08-23.txt`.

## Independent sign-off — 2026-08-23

**Signed off.** Both executable consumers now preserve the pinned source
distinction: omission is absence on either source, explicit null is absence
only on `tool_call_update`, and initial-call null refuses. Invalid values are
shape-checked before vocabulary membership and refusal diagnostics no longer
execute them. Both Python runners execute the same 66 tests.

The corrected SPEC, frozen and product schemas, JavaScript normalizer, and
Python model agree on the ten values and presentation-only authority. The two
schema copies have the same SHA-256 digest, and the current consumer sweep
finds no policy/outcome reader. This completes plan item 7 on the reviewed W4
tree. Agent events are 52/52, the model is 66/66 under both runners, and full
v12 is 650/654 with the four failures independently owned by W641 and W4.
Review and evidence: `review-2026-08-23T20-00-57Z.md` and
`evidence/signoff-round2-2026-08-23.txt`.
