# Progress: v12 ACP agent boundary

Implementer-owned. One writer: `baton.claude`.

## 2026-08-21 — W1440 claimed and specified

Claimed W1440 at authority sequence 1543 after reading `AGENTS.md`,
`docs/EFFECTIVE-BATON.md`, the campaign record, the parent
`finding-v12-worker-contract` record, this child's `FINDING.md`, the signed-off
W151 assignment contract, and the whole of W1439's approved outer contract.

### Revalidation performed before writing anything

| Pinned claim | Source re-read | Outcome |
| --- | --- | --- |
| outer worker-control vocabulary | `../finding-worker-control-api-manifests/SPEC.md`, its schema, its evidence and its review | unchanged; consumed as-is |
| W151 identity, gates, ambiguity rules | `../../finding-v12-assignment-state-machine/SPEC.md` | unchanged; imported, not redefined |
| ACP surface and version | `v12/node_modules/@agentclientprotocol/sdk` 1.3.0 types and method tables | `PROTOCOL_VERSION = 1`; 13 `SessionUpdate` variants; 5 `StopReason` values; `session/cancel` is a notification; client capabilities are `fs`/`terminal` plus five experimental ones |
| ACP prototype behaviour | `v12/src/acp_session.mjs` | four prototype rules confirmed and generalized; its process-local session handling and single posture deliberately not adopted |
| Codex App Server surface | official documentation, re-read 2026-08-21 | thread/turn/item model, four approval request families, `turn/interrupt` as a REQUEST, three terminal turn statuses, 11 `codexErrorInfo` values, and the experimental/under-development/deprecated lists |

No pinned decision was found to have changed, so no supersession was needed.
Two facts the parent record had not recorded were added to `FINDING.md`: the
Codex approval surface is four families rather than one, and `turn/interrupt`
is a request rather than a notification.

### Delivered

- `SPEC.md` — the normative boundary, §0-§15.
- `schema/agent-session-1.0.schema.json` — four sealed documents (`profile`,
  `session`, `turn`, `event`), Draft 2020-12.
- `evidence/traces.json` — 14 traces and 32 negative vectors.
- `evidence/acp_boundary_model.py`, `evidence/test_acp_boundary_model.py` —
  the executable design model and its tests.

### Verification

From `evidence/`:

```text
python3 -B -m unittest -q test_acp_boundary_model
----------------------------------------------------------------------
Ran 31 tests in 0.028s

OK
```

Both JSON files pass `python3 -m json.tool`; Draft 2020-12 schema
self-validation is a test assertion. The model imports no Baton or `v12/`
product code and reaches no model provider.

### Judgement calls a reviewer should check

1. **A fourth version axis rather than new fields on frozen manifests**
   (`SPEC.md` §0.1). Adding agent-session state to W1439 §8.3's
   runtime-attempt axes would have reopened an approved manifest and made
   `execution runtime` mean two things. The alternative chosen binds an
   agent-session record by digest from adapter diagnostics instead. If the
   approver prefers a `baton.worker-manifest` minor bump, that is a
   cross-contract decision for W1408 rather than something this child should
   settle alone.
2. **`document_digest`, not `manifest_digest`** (§0.2), so an agent-session
   document is never mistaken for a `baton.worker-manifest` member.
3. **`unknown` is a TERMINAL session state** (§3.3, §7.3). An epoch whose
   ending nobody observed does not get promoted to `closed`.
4. **The closed error taxonomy is reused, not extended** (§11). Every
   agent-session condition maps into W1439 §11's existing category/code pairs,
   and a test asserts that no pair outside them is ever produced.
5. **Withholding `fs` and `terminal` client capability is structural, not
   policy** (§2.2). This is the strongest single rule here and it is the one
   an implementer is most likely to relax for convenience.

### State

Specification complete; awaiting independent review.

## 2026-08-21 — response to review-2026-08-21T22-53-56Z.md

State: **changes requested, all applied**. Reclaimed W1440 at authority
sequence 1626.

Every counterexample in the review was reproduced against the submitted
artifacts BEFORE anything was changed, and every one was real:

```text
execution-null-assignment  True      consent-live-assignment    True
cross-work-assignment      True      work-id-W0                 True
unsealed-event valid       True      sealed-event valid         False
event-ledger-schema-event  BoundaryError: different session epoch
invented-error-code        (code is a free string in the schema)
```

I found no finding I disagreed with. Two source facts I had recorded were also
wrong, and both are corrected with their supersession marked in `FINDING.md`
rather than edited away.

### P1 — shared identity and artifact types

Confirmed all four divergences against
`../finding-worker-control-api-manifests/schema/worker-control-1.0.schema.json`:
`W0` admitted where W1439 requires `W[1-9][0-9]*`; participants leading with a
digit admitted and underscores rejected, exactly inverting W1439's pattern;
`byte_length` and a pattern-free media type where W1439 owns `bytes` and a
strict one; and no JSON-safe integer maximum.

Fixed by reproducing `digest`, `opaqueId`, `timestamp`, `participant`,
`workRef`, `assignmentRef`, `artifactRef` and `evidenceRef` VERBATIM, and by
adding `test_shared_definitions_are_byte_identical_to_worker_control`, which
loads both schema files and compares them. I chose mechanical enforcement over
a documented promise because a promise is exactly what failed the first time —
and because when W1439 next revises one of these, the test fails and this
document gets revised with it instead of drifting. `SPEC.md` §0.3 states the
rule and the reason.

The three forbidden bindings are now schema conditionals (`execution` implies
a non-null assignment, `consent` implies null, the ref's posture equals the
record's) plus semantic checks for the two cross-field equalities JSON Schema
cannot express: the assignment's `work_ref` equalling the session's, and
W1439 §12.1's authority-prefix rule. Five negative vectors cover them.

### P1 — normalized events neither sealed nor exercised

Correct, and the underlying problem was worse than the symptom: `EventLedger`
consumed an ad-hoc event with a top-level `session_epoch` while the schema put
the epoch under `agent_session_ref`, so the schema tests and the semantic
tests were proving things about two different objects.

Fixed at the root rather than by adding a field. `normalizedEvent` now carries
`document_digest`; `EventLedger` takes the session ref rather than a bare
epoch, consumes the schema shape, validates `source_seq` and `redacted`
itself, and returns a sealed document. The trace runner builds real schema
documents and feeds those to the model, so there is now one object graph. Four
new negative vectors cover a zero sequence, an event from another epoch, an
unredacted event and a tampered seal.

One subtlety worth flagging for review: the duplicate comparison is over what
ARRIVED, with `late` and `document_digest` stripped, because both are the
ledger's own annotations. Comparing the sealed forms would make every
identical replay look like a conflict.

### P1 — consent/execution cardinality

The contradiction was real: "one fresh session per runtime attempt" cannot
coexist with two mandatory postures under W151's one fixed
`runtime_attempt_id`. I took the reviewer's suggested shape, which is the one
W151 already implies with its separate consent-runtime and execution-runtime
axes.

`posture` is now part of `agent_session_ref`; identity is
`(runtime_attempt_id, posture, session_epoch)`; the epoch counter is scoped
per posture, so both postures start at epoch 1 under one attempt and are still
distinct; `AttemptSessions` refuses a second concurrent session for one
posture; and `promote_consent_to_execution` is a refusal rather than a
convention. The `consent-then-execution` trace runs offer consent at epoch 1
with a null assignment, asserts the promotion refuses, settles the claim, and
opens a separately bound execution session at its own epoch 1 carrying
generation 7 — so W151's fixed attempt identity is exercised rather than
assumed. `SPEC.md` §3.2 marks the old phrasing superseded and says which of
the two statements was the right one.

### P1 — the Codex profile was not executable

All three gaps confirmed by re-reading the official documentation.

1. **No `protocolVersion`.** Confirmed: `initialize` takes `clientInfo` and an
   optional `capabilities` object and returns user-agent and platform
   information. Pinning `1` against that was worse than no check because it
   looked like one. §2.1 now has two routes — a negotiated wire version for
   ACP, an exact `provider_binding` (server build, interface digest,
   certification instant, `experimental_api: false`) for a provider without
   one — and the schema refuses a profile carrying both or neither. Asking
   either route of the other profile refuses.
2. **Policy operands.** Confirmed the real `thread/start` and `turn/start`
   fields. A certified profile now pins the complete operands for both
   postures, `approvalPolicy` is schema-pinned to the constant `never`
   (because `onRequest` and `unlessTrusted` are what PRODUCE the approval
   requests §4.3 treats as failures), `dangerFullAccess` and `externalSandbox`
   cannot be pinned, and the cwd is pinned by ROLE — `scratch` or `workspace`
   — never by host path. The observed shape carries the full provider enums so
   drift is representable and refusable; three drift vectors cover it.
   §10.3 additionally requires the policy re-sent IN FULL on every
   `turn/start`, since a turn may override the thread default and an inherited
   default nobody restated is not a pinned policy.
3. **Typed denials.** Confirmed each family's reply shape.
   `codex_deny_approval` now returns `"decline"` for the two command-shaped
   families, `{"permissions": {}, "scope": "turn"}` for the permissions family
   (empty granted subset at the narrowest scope; no cancel form is documented
   and none is needed), and `{"action": "decline", "content": null}` for
   elicitation. Four traces assert the complete payloads and four negative
   vectors assert that each family's granting answer is recognized as granting.

On the WebSocket note: my re-read still returned the `--ws-auth` flag names,
alongside a `CODEX_REMOTE_TOKEN` environment variable. Rather than argue the
point I removed the dependency — §10.1 now rests the exclusion on the
transport being experimental and unsupported, plus the independent fact that
any remote form puts a bearer credential in the session path. The discrepancy
is recorded in `FINDING.md` as observed and unresolved, because a rationale
that cannot go stale is better than a correct citation that can.

### P2 — open error codes, and the capability inventory

`errorCategoryCode` is now a `oneOf` over the seven categories with their
exact code enums, and `test_error_pairs_in_schema_match_the_closed_taxonomy_exactly`
asserts the schema's pairs equal the model's copy of W1439 §11. Three invalid
document vectors cover an invented code, a real code under the wrong category,
and a policy failure claiming a grant.

The capability inventory correction is the one I got wrong independently of
the review's framing, so I checked it member by member rather than taking it
on trust: `session` is stable and I had recorded it as unstable;
`positionEncodings` is unstable and I had omitted it. §2.2 now withholds
EVERY client capability rather than every unsafe one, which is both simpler
and immune to the next SDK release adding a member.

### Verification

From `evidence/`:

```text
python3 -B -m unittest -q test_acp_boundary_model
----------------------------------------------------------------------
Ran 42 tests in 0.061s

OK
```

42 tests, up from 31; 19 traces, 56 negative vectors, 3 invalid document
vectors. Every reproduced counterexample now refuses:

```text
execution-null-assignment  schema: False    consent-live-assignment schema: False
cross-work-assignment    semantic: integrity.schema
work-id-W0                 schema: False    unsealed-event valid:    False
sealed-event valid:        True             invented-error-code:     False
real-code-wrong-category:  False            codex pinned_wire_version: None
```

Both JSON files parse; Draft 2020-12 self-validation and the W1439 definition
equality are test assertions. The repository whitespace check over the diff is
clean, and only dossier records changed.

### State

Corrections complete; awaiting the second independent review.

## 2026-08-21 — response to review-2026-08-21T23-18-11Z.md

State: **changes requested, all applied**. Reclaimed W1440 at authority
sequence 1705.

All four counterexamples reproduced against the submitted artifacts before
anything changed:

```text
command-denial 'decline' provider-schema-valid  False
unsealed-input-schema-valid False   record-return-schema-valid   False
record-return-digest-valid  False   tampered-sealed-input-accepted True
swapped-codex-postures-schema True  swapped-codex-postures-semantic ACCEPTED
missing-profile-required-methods-negotiate ACCEPTED
```

One nuance on the third: swapping whole posture BINDINGS was already caught by
the workspace booleans. Swapping only the `policy` objects, leaving the
booleans honest, was not — that certifies a consent posture pinning
`workspaceWrite` with a workspace cwd while declaring `workspace: false`. That
narrower case is the real hole and is what the fix targets.

### P1 — approval response envelopes

The `codex` CLI is on this host, so I generated the schemas rather than
reasoning from prose:

```text
codex --version                       -> codex-cli 0.149.0
codex app-server generate-json-schema --out <tmp>
```

`CommandExecutionRequestApprovalResponse` and
`FileChangeRequestApprovalResponse` are both `type: object` with `decision`
required. The bare string validates false; `{"decision": "decline"}` validates
true. The permissions and elicitation payloads were already correct.

Rather than fix the two strings and re-assert equality, I took the reviewer's
underlying point: a self-authored equality assertion cannot prove
provider-shape conformance, which is exactly why the previous round passed
while specifying a reply the provider would reject. The four response schemas
are now captured verbatim under
`evidence/provider-schemas/codex-app-server/` with a PROVENANCE file naming
the CLI version and command, every denial and race form is validated against
them with `Draft7Validator`, and the certified
`provider_binding.interface_digest` is the SHA-256 over that captured bundle —
so a different CLI build is a different certified interface and §2.1 refuses
it. Two new negative vectors assert the bare member is refused by the
provider's own schema.

### P1 — the event ledger boundary

Every part of this was accurate, and my previous correction note overstated
what I had done. The ledger popped `document_digest` without verifying it (so
a tampered sealed event was accepted and re-sealed) and appended `replayed` to
the returned document (forbidden by `additionalProperties: false`, and it
invalidated the digest).

I did not add a verification step to the existing shape. The seal is now
checked FIRST — before identity, sequence, limit or kind — because nothing
below may run against bytes whose digest was never checked, and `record`
returns the document exactly as given.

That forced a real design decision, which is the part worth your attention.
`late` and `observation_seq` cannot stay inside a document the ledger returns
unchanged. I removed them from `normalizedEvent` rather than resealing,
because they are properties of an OBSERVATION and not of the frame: a
retransmitted frame is the same frame, and had lateness been sealed in, the
same frame seen once before a turn ended and once after would carry two
digests and an ordinary duplicate would be indistinguishable from a spliced
stream. They now travel in a `LedgerOutcome` beside the document, along with
replay and drop status. A replay reports the ORIGINAL observation rather than
minting a second, and there is a test for exactly that sequence.

The duplicate comparison is now simply the two `document_digest` values, which
also retires the subtlety I flagged last round — nothing has to be
reconstructed to make the comparison.

### P1 — profile certification

`validate_profile` is now the single certification validator, and every trace,
every negative vector, `negotiate_acp` and `bind_provider` run it, so a
profile cannot reach the rest of the model uncertified.

- The Codex posture operands are schema constants BOUND TO THEIR POSTURE:
  consent pins `readOnly` and a scratch cwd, execution pins `workspaceWrite`
  with `networkAccess: false` and a workspace cwd. The policy swap is now
  refused by the schema and again by the validator.
- `workspace` and `declared_output` are schema constants per posture.
- `required_agent_methods` and `refused_agent_methods` are REMOVED from the
  profile. Making them exact would have preserved two live sources of truth;
  the version owns them, keyed by wire protocol. `session_capabilities` is a
  schema constant of exactly the six.
- The request builders take a role-to-path map and the profile chooses the
  role, so an arbitrary path can no longer be injected.
- `validate_session_binding` now takes the profile and checks the record's
  `profile_digest`, its `pinned_policy` against the certified posture policy,
  and its negotiated capabilities.

One consequence worth naming: two existing negative vectors moved from
`policy.denied` to `policy.profile-uncertified`. That pair already existed in
W1439's closed taxonomy for exactly this case and is the more precise of the
two, so this is a correction rather than a reclassification of convenience.

### P2 — superseded prose

Fixed all four. §0.2, §2.4 and §8.2 now carry the posture in the session
lifetime, the `session.fresh` definition and the relay journal scope; §3.2 now
states the posture-specific cwd — the empty read-only scratch root for
consent, the materialized private workspace for execution — and adds that the
profile pins the role rather than a path. Recorded in `FINDING.md` as its own
point: a chronological correction in the finding history does not help an
implementer reading the normative sections, so live text contradicting a
recorded supersession is itself a defect.

### Verification

From `evidence/`:

```text
python3 -B -m unittest -q test_acp_boundary_model
----------------------------------------------------------------------
Ran 52 tests in 0.076s

OK
```

52 tests, up from 42; 19 traces, 69 negative vectors, 3 invalid document
vectors. Every counterexample now refuses:

```text
command/file denials, both forms      provider-schema-valid True
bare 'decline' against command schema provider-schema-valid False
sealed-input-schema-valid  True   record-return-schema-valid True
record-return-digest-valid True   record-return-is-input     True
unsealed-input-accepted    False (integrity.schema)
tampered-input-accepted    False (integrity.digest)
swapped-codex-postures-schema   False
swapped-codex-postures-semantic policy.profile-uncertified
profile-restating-methods-schema False
arbitrary-cwd-injected          policy.denied
```

Both JSON files parse; Draft 2020-12 self-validation, the W1439 definition
equality, and the captured-bundle digest matching the certified binding are
all test assertions. The repository whitespace check over the diff is clean,
and only dossier records changed.

### State

Corrections complete; awaiting the third independent review.

## 2026-08-21 — response to review-2026-08-21T23-32-48Z.md

State: **changes requested, all applied**. Reclaimed W1440 at authority
sequence 1754.

Both counterexamples reproduced against the submitted artifacts before
anything changed:

```text
extra-method-schema-valid False   extra-method-validate-profile  ACCEPTED
                                  extra-method-negotiate         ACCEPTED
tampered-profile-schema-valid True  tampered-profile-seal        INVALID
                                    tampered-profile-bind-provider ACCEPTED
wrong-profile-digest-without-profile ACCEPTED
caller-return-is-stored-object True  persisted-after-caller-mutation INVALID
```

Both findings are correct, and both are cases where my previous correction
note claimed more than the code did. I have tried to fix the class rather than
the instance in each.

### P1 — certification did not compose

`validate_profile` checked policy fields and nothing else. It never validated
the document against the durable schema and never verified its seal, and both
`negotiate_acp` and `bind_provider` called only that function.

The fix is an ordering rule rather than an extra call: shape, then seal, then
policy, at one entry point, before a single policy field is read. Reading a
policy field out of a document whose seal was never checked is reading
whatever the last writer put there. The model now loads its own schema and
composes all three in `validate_profile`; the semantic-only check survives as
`certify_profile_fields`, named a PARTIAL helper exactly as the review asked,
and is no longer reachable under the certification name.

I also took the general point into `SPEC.md` §12.7a: proving shape, seal and
semantics in three separate tests does not make the runtime path compose them.
That is the sentence I would have needed to read before writing the previous
round.

`validate_session_binding` now takes the profile as a required positional
operand. The optional form was the same bypass in smaller print, and the
second review had already asked for the relationship to be mandatory. The
record's own shape and seal are accepted before any binding field is read, and
the cross-field-only rules live in `validate_session_binding_fields`.

One consequence worth flagging: several existing profile-policy vectors are
also schema-invalid, so through the composing entry point they now refuse at
`integrity.schema` before the policy layer is reached. Rather than weaken
either check I gave each vector an explicit layer — the semantic rule is
proven through the named partial helper, and two new vectors prove the entry
point refuses the same documents earlier. That way neither layer can quietly
stop carrying its weight.

### P1 — the ledger aliased caller-owned dictionaries

Accurate. The seal verification was right and the storage was not: the entry
was the caller's exact dictionary, and `LedgerOutcome` handed that same object
back.

Fixed by copying at both edges, and by stating the rule generally in §0.2
rather than only in the ledger: sealing is a statement about BYTES, and
"unchanged" means byte equality rather than object identity. Immutable
evidence a caller can still reach is not immutable, and a replay decision that
turns on whether an unrelated caller kept a reference is not a decision about
content. `test_the_ledger_owns_its_entry_and_no_caller_can_reach_it` mutates
both the submitted input and the returned outcome, then asserts the persisted
entry is byte-identical, still schema-valid, still seal-valid, and that the
replay decision is unchanged — plus that a genuinely different frame under the
same sequence still refuses.

### Verification

From `evidence/`:

```text
python3 -B -m unittest -q test_acp_boundary_model
----------------------------------------------------------------------
Ran 56 tests in 0.110s

OK
```

56 tests, up from 52; 19 traces, 78 negative vectors, 3 invalid document
vectors. Every counterexample now refuses:

```text
extra-method-validate-profile        integrity.schema
extra-method-negotiate               integrity.schema
tampered-profile-validate-profile    integrity.digest
tampered-profile-bind-provider       integrity.digest
wrong-profile-digest-without-profile TypeError (missing required operand)
wrong-profile-digest-with-profile    integrity.digest
byte-equality-preserved              True
caller-return-is-stored-object       False
persisted-after-caller-mutation      VALID
replay-still-decides                 replayed
```

Both JSON files parse; the provider bundle parses; Draft 2020-12
self-validation, the W1439 definition equality, and the captured-bundle digest
matching the certified binding remain test assertions. The repository
whitespace check over the diff is clean, and only dossier records changed.

### State

Corrections complete; awaiting the fourth independent review.
