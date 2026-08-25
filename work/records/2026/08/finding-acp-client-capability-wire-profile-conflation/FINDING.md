# Finding: separate ACP wire capabilities from the durable profile summary

Discovered during W4/W2929 handshake review on 2026-08-23.
Canonical Baton Work: W641 (`2b077949-W641`).

## Observed

The frozen ACP boundary assigns two incompatible representations to the same
`MINIMAL_CLIENT_CAPABILITIES` concept:

- `work/records/2026/08/finding-v12-isolated-agent-workers/findings/
  finding-v12-worker-contract/findings/finding-acp-agent-boundary/SPEC.md`
  §2.2 says the ACP wire `clientCapabilities` are exactly
  `{ "fs": {}, "terminal": false }`, with both filesystem members absent.
- The pinned ACP SDK 1.3.0 declaration names optional camel-case wire members
  `readTextFile` and `writeTextFile`, so the empty `fs` object is a valid wire
  expression of no filesystem capability.
- The frozen agent-session schema instead requires the normalized durable
  shape `{ "fs": { "read_text_file": false, "write_text_file": false },
  "terminal": false }`.
- `evidence/acp_boundary_model.py` uses that durable snake-case shape for
  `MINIMAL_CLIENT_CAPABILITIES`, validates it as the advertisement, and
  returns it as the negotiated `client_capabilities`. The model therefore
  contradicts §2.2 at the actual ACP wire boundary.

W4 copied the executable model into its handshake implementation. Its
`negotiateAcp()` consequently emits the durable snake-case document as ACP
`clientCapabilities` and refuses the exact wire document pinned by §2.2.
That implementation choice exposed the pre-existing frozen-contract conflict;
it did not create it.

## Confirmed boundary

Wire protocol data and durable agent-session evidence are different domains.
The W4 product must not send durable snake-case field names on the ACP wire,
and must compare the allowed wire capability document structurally rather
than by serialized member order. The owning ACP boundary must separately rule
whether the durable schema remains a normalized summary or is changed to
retain the literal wire representation.

This correction is independent of W4's closed-method enforcement and need not
block that implementation slice. Until the owning contract is corrected, W4
should follow the explicit §2.2 wire text and pinned provider declaration at
the transport boundary while keeping any durable normalization explicitly
named and separate.

## Open decision

Rule and name the two representations. Then explicitly correct or supersede
the model, schema descriptions/examples, trace interpretation and consumer
tests so no single constant is treated as both ACP wire data and normalized
agent-session evidence.

## Confirmed ruling — 2026-08-23

**Confirmed by Slawomir.** Agent-session 1.0 keeps one ACP capability
representation, not a wire document plus a Baton-invented normalized
duplicate. The canonical value is the pinned ACP wire structure:

```json
{"fs": {}, "terminal": false}
```

The ACP profile persists that same structural document and the relay sends an
owned copy of it during initialization. ACP's own member names and omission
semantics are authoritative: absent `readTextFile` and `writeTextFile`
members mean those capabilities were not advertised. Baton must not synthesize
snake-case explicit-false members merely to restate that evidence.

Validation is structural and pinned to the accepted ACP version. JSON object
member order is irrelevant, while an added member, changed value, enabled
capability, snake-case transport member, or unsupported shape refuses. The
durable record need not preserve incidental serialized byte order, but its
data model must remain the ACP document rather than a lossy or expanded
translation.

This supersedes the earlier candidate boundary in this finding that allowed a
separate normalized summary to remain. The frozen schema/model's
`read_text_file: false` and `write_text_file: false` representation is the
contract defect to remove, not a second representation to name. If a future
cross-provider consumer requires a provider-neutral capability model, that
model needs separately justified Work, explicit semantics, and its own
versioned contract.

Implementation must update the owning SPEC, profile schema and examples,
executable model, trace interpretation, product schema copy, handshake code,
and focused positive/negative/retry regressions together. It must retain the
current exact minimal-capability policy and the structural, order-independent
comparison.

## Independent review — 2026-08-23

**Observed; changes requested.** The one-representation correction is
coherent across the schema, model, trace, product copy, fixtures and ordinary
handshake cases. Two JavaScript boundary defects remain. First,
`validateClientCapabilities` treats any object with no enumerable keys as the
empty JSON `fs` document, so it accepts a `Date` even though that value
serializes as a string. Second, its refusal diagnostic serializes a rejected
terminal value and lets a BigInt escape as raw `TypeError` instead of the
closed `policy.denied` pair.

The correction must prove inert JSON records at both object levels while
continuing to accept null-prototype documents and member-order differences,
and every unsupported value must keep the closed refusal taxonomy. Two
additive regressions preserve the boundaries. Full analysis and verification
are in `review-2026-08-23T19-36-46Z.md` and
`evidence/review-round1-2026-08-23.txt`.

## Independent review of the correction — 2026-08-23

**Accepted:** the one-representation correction itself. Schema and product copy
byte-identical, both requiring exactly `{fs: {}, terminal: false}`; model and
handshake using the same ACP-shaped representation; the trace profile correctly
re-sealed; order irrelevant; owned copies; the exact minimal-capability policy
unwidened.

**Observed; changes requested, and corrected the same day.** The structural
validator decided "is this the empty document" by counting enumerable members,
so `{ fs: new Date(0), terminal: false }` passed — and a Date serializes as a
string, not as `{}`. **Looking empty is not being the empty document.** The
validator now proves an INERT JSON RECORD at both levels: an object that is not
an array, carrying `Object.prototype` or no prototype so nothing inherited
decides its wire form, with exactly the expected own keys *counting the ones
`Object.keys` hides* — a non-enumerable `toJSON` is invisible there and decides
the entire serialization — and every member a DATA member, because a getter may
answer one thing to the check and another to the wire. `Object.create(null)`
and either member order remain valid spellings.

**And the refusal must not serialize what it refuses.** The review found
`JSON.stringify` on `terminal`; the envelope and `fs` refusals carried the same
line and the same defect, so a BigInt escaped `policy.denied` as a raw
`TypeError` from any of three sites. Every refusal names the value by its shape
now, through one helper that runs nothing. Member names are still reported —
an inert string, and the whole diagnostic — but never a value.

Full findings and verification: `review-2026-08-23T19-36-46Z.md`,
`evidence/review-round1-2026-08-23.txt` and
`evidence/correction-round1-2026-08-23.txt`.

## Second independent review — 2026-08-23

**Observed; changes requested.** The first correction proves ordinary object
shape and translates reflection that throws, but successful Proxy traps can
still impersonate both accepted records. A Proxy can answer the required
prototype, keys and descriptors at the envelope, or the empty shape at `fs`;
both advertisements are accepted and caller code runs while policy is
decided. A program is not the inert JSON document this boundary promises.

This is the same record primitive W4's sixth reconnect review corrected.
Plan item 7's queued unification is therefore part of the required correction,
not later cleanup: reject a Proxy before reflection through one shared,
non-observing record proof used at both capability levels and reconnect.
Two additive regressions preserve each capability level. Full findings and
verification are in `review-2026-08-23T20-20-01Z.md` and
`evidence/review-round2-2026-08-23.txt`.

## Second review, and one shared record proof — 2026-08-23

**Observed; changes requested, and corrected the same day.** A Proxy whose
traps ANSWER passed a record proof built to catch traps that THROW. Both
capability levels accepted one, and caller code ran while policy was being
decided. Translating a trap that throws does nothing about a trap that answers.

**The same finding had already landed one round earlier, in the other copy of
these rules.** The reconnect envelope and this capability envelope ask the same
question — did the caller hand me data, or a program wearing an object — and
each had grown its own proof. Two implementations of one rule earned the same
finding twice, independently.

**So there is now exactly one.** `v12/src/worker_manager/records.mjs` holds
`classify`, `describe`, `isPlainRecord` and `recordFault`; both boundaries call
it and neither keeps a copy. A Proxy is rejected FIRST by a non-observing
discriminator that reads an internal slot and runs no trap — another try/catch
would not do, because a successful trap walks past one.

**The module returns facts and prose, never a `ContractError`.**
`integrity.schema` at reconnect and `policy.denied` here are the CALLERS'
policies; a shared primitive that threw one of them would be deciding something
that is not its business. And its header carries the six rules that six review
rounds produced, because each was learned by getting it wrong and none of them
is obvious from the code that implements it.

Verification: records 6/6, handshake 28/28, reconnect 32/32, profile 14/14,
session 18/18; **full v12 670/670**; design models 64/66/24/74; v11 pytest 2980
and serial 52; bridges 336 and 55; frozen and product schemas byte-identical;
whitespace clean. Full findings and evidence:
`review-2026-08-23T20-20-01Z.md`, `evidence/review-round2-2026-08-23.txt` and
`evidence/correction-round2-2026-08-23.txt`.

## Third independent review — 2026-08-23

**Accepted:** the required shared composition and successful-Proxy correction.
Handshake and reconnect now use one primitive; a non-observing Proxy check
precedes reflection; both Proxy regressions pass without traps; reconnect
remains green without changed assertions; and caller taxonomies stay local.

**Observed; changes requested.** `recordFault` accepts an expected own data
member without requiring it to be enumerable. An envelope whose `fs` and
`terminal` properties are both non-enumerable therefore validates even though
its JSON document is `{}`. A hidden required field can be read as a JavaScript
property, but it is not part of the wire document. Require expected members to
be enumerable data descriptors without reading their values or weakening any
Proxy, hidden-extra-member, ordinary/null-prototype, order, or taxonomy rule.

Two additive regressions preserve the primitive and ACP call site. Records is
6/7, handshake 28/29, reconnect 32/32, and full v12 670/672 with exactly the
two new cases failing. Full review and evidence:
`review-2026-08-23T20-37-50Z.md` and
`evidence/review-round3-2026-08-23.txt`.

## Third review: a member that is not in the document — 2026-08-23

**Observed; changes requested, and corrected the same day.** The shared member
proof required every expected member to be a DATA member and did not require
it to be ENUMERABLE. An ACP capability envelope whose `fs` and `terminal` were
both non-enumerable therefore validated: both values readable,
`JSON.stringify` of the envelope `{}`.

**The rule had two directions and one of them was implemented.** "Looking empty
is not being the empty document" was applied by counting hidden own keys, so an
EXTRA non-enumerable member could not smuggle a `toJSON` past the proof — and
the EXPECTED members were then proved by property access alone, which is the
older and weaker question, at the other end of the same function.

A member that is not in the JSON document is not a member of the document. The
proof requires enumerability now, as an inert descriptor check: the value is
never read, no behaviour runs, and Proxy handling is unchanged. Everything the
review required to stay stayed — empty and null-prototype records, insertion
order, hidden extra-member and accessor refusal, and both caller taxonomies.

Verification: records 9/9, handshake 29/29, reconnect 32/32 with no assertion
edited; **full v12 677/677**; design models 64/66/24/74; v11 pytest 2980 and
serial 52; bridges 336 and 55; schemas byte-identical; whitespace clean. Full
findings and evidence: `review-2026-08-23T20-37-50Z.md`,
`evidence/review-round3-2026-08-23.txt` and
`evidence/correction-round3-2026-08-23.txt`.

## Independent sign-off of the third correction — 2026-08-23

**Signed off.** Expected members are now proved as enumerable data
descriptors without reading their values, so acceptance cannot depend on a
hidden required JavaScript property that is absent from the JSON document.
The Proxy-first guard, hidden-extra and symbol counting, accessor refusal,
ordinary/null-prototype acceptance, insertion-order independence, shared
composition and caller-local taxonomies all remain intact.

The current consumer sweep finds one agent-session 1.0 transport consumer,
W4's handshake, using the one canonical ACP-shaped document. The accepted
pre-1.0 spike and earlier v11 bridge remain outside this contract's scope; no
later 1.0 adapter retains the removed summary. Future adapters require review
when they exist and do not keep this correction open indefinitely.

Independent verification: records 8/8, handshake 29/29, reconnect 32/32 and
ACP boundary model 66/66; schemas hash identically. Full v12 is 678/680, with
only two separately owned W4 composition-review cases failing. Review and
evidence: `review-2026-08-23T20-59-26Z.md` and
`evidence/signoff-round3-2026-08-23.txt`.
