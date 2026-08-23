# Finding: freeze the v12 worker contract

Work `W1408` (`43c55d4b-W1408`), contained by the v12 isolated-agent-worker
campaign at `work/records/2026/08/finding-v12-isolated-agent-workers/`.

## Assignment boundary

Specify the versioned worker-control API, typed manifests, ACP boundary, and
runtime-neutral conformance contract. Decompose independently accountable
implementation or verification deliverables into separate child Work. This is
design and planning work; it does not authorize v11 or v12 protocol,
application, runtime, or adapter implementation.

## Operational findings at intake

- **Observed 2026-08-21:** W1408 arrived without a repository binding, so no
  exact Work dossier existed to read before execution. The reviewer recorded
  the absence in thread `T1408`, created this canonical child record, and will
  bind W1408 to it before contract research continues.
- **Observed 2026-08-21:** sibling W1410 has the same title, body,
  classification, priority, route, and parent as W1408, was created by the same
  actor 12 seconds later, and is also unbound. W1410 remains untouched for the
  owning operations endpoint to classify; this record and its work products
  belong only to W1408.

### Duplicate resolution — 2026-08-21

**Confirmed and resolved.** `baton.prompt` confirmed in thread `T1408` message
1419 that W1410 was accidental and directed rejected duplicate closure in
favor of W1408. `baton.codex` classified W1410 `duplicate` at authority
sequence 1446 and closed it `rejected`, `duplicate-of=W1408`, at sequence 1447.
W1410 was never claimed or bound; W1408 remains the one canonical M1 Work.

## Research status

### Revalidated baseline — 2026-08-21

- **Confirmed.** The parent record already fixes the ownership split: the
  versioned Baton worker-control API owns assignment identity, fencing,
  runtime lifecycle, inputs, health, output, proposal, verification and
  disposition; ACP owns only agent sessions, prompts, turns, tool/permission
  exchange, cancellation and session events.
- **Confirmed.** The signed-off assignment contract
  `../finding-v12-assignment-state-machine/SPEC.md` is the normative identity
  and transition dependency. M1 must reuse its full `work_ref`,
  `assignment_ref`, operation settlement, typed gates, immutable receipts and
  authority/control-store/artifact ownership split rather than minting a
  second lifecycle model.
- **Observed.** The accepted `v12/` proof is explicitly `0-spike`. Its
  envelopes use authority-local Work selectors, constant generation `1`,
  shallow required-field checks, permissive unknown fields and process-local
  token state. Those choices remain valid PoC evidence but are not a schema to
  freeze.
- **Observed.** The proof currently uses `@agentclientprotocol/sdk` 1.3.0 and
  exercises initialization, fresh sessions, exact session mode, prompt/update,
  permission refusal and supervised cancellation. These are useful test
  evidence, not a Baton wire-version promise.
- **Confirmed.** Current official OpenAI App Server documentation describes a
  bidirectional JSON-RPC interface with thread/turn/item streaming,
  server-initiated approval requests and explicit turn interruption. It also
  marks WebSocket transport and `process/*` as experimental; the Codex adapter
  contract must therefore normalize stable session behavior and cannot make
  either experimental surface part of the Baton worker contract. Source:
  [Codex App Server](https://learn.chatgpt.com/docs/app-server), read
  2026-08-21.

## Proposed M1 decomposition

The freeze is three independently accountable contracts, ordered by their
real dependencies:

1. **Outer worker-control API and typed manifests.** Define version
   negotiation, transport-independent operations/events/errors, full identity
   and retry fields, and the input, assignment, output/result, proposal and
   verifier/receipt schemas.
2. **ACP agent boundary.** Against the frozen outer vocabulary, define the
   native ACP relay and non-ACP adapter obligations, including Codex App Server
   mapping, permission failure, cancellation and event normalization. ACP does
   not acquire source, control a runtime or publish a proposal.
3. **Runtime-neutral conformance.** Against both contracts, define black-box
   fixtures, observations and pass/fail rules across local OCI and genuinely
   remote adapters, including negative, race, retry, partition, restart,
   cancellation, leakage and stale-publication cases.

The ACP child depends on the outer contract. Conformance depends on both. This
keeps one runnable design slice at a time and prevents the test vocabulary or
adapter mapping from freezing names the outer API later changes.

### Decomposition approval — confirmed 2026-08-21

The approver accepts this three-child decomposition and its dependency order.
W1439 is the one current design slice; W1440 waits on W1439, and W1441 waits on
both. No child authorizes application, authority, schema, runtime, or adapter
implementation. W1408 remains the M1 coordinator and returns for independent
cross-contract freeze review only after all three child specifications close.

W1408 therefore has a real scheduler dependency on final conformance child
W1441 while the children execute. Campaign W28 has a real scheduler dependency
on W1408 because M2 activation requires the M1 contract freeze. These explicit
edges encode the approved ordering; containment alone continues to carry no
dependency meaning.

## M1 freeze boundary

M1 is ready for approval only when all three child specifications:

- name one compatible version/extension policy and reject unknown major
  versions and unnegotiated capabilities;
- use the W151 identity and effectively-once rules without contradiction;
- keep runtime-specific IDs, paths, engine commands and provider events in
  adapter diagnostics rather than portable protocol semantics;
- carry typed, digest-bound, size-limited, non-secret manifests and immutable
  receipts with explicit unknown-field and canonicalization rules;
- define cancellation as ordered intent plus observed quiescence, never as
  proof that a process stopped; and
- include executable or machine-readable positive and negative examples that
  later implementations can run without a model provider.

This milestone changes design records only. Runtime, authority, schema,
adapter and application implementation belongs to separately authorized later
Work.

## M1 cross-contract freeze — 2026-08-22

**Confirmed.** All three contained specifications closed satisfying after
independent review:

- W1439 freezes `urn:baton:worker-control:1.0`, 17 control message kinds, 31
  typed error code/status pairs, and 10 digest-bound manifest and receipt
  schemas. Its 12 executable model tests pass. *(W4487, 2026-08-22: 17 model
  tests and one more valid plus two more invalid vectors; W4487 review,
  2026-08-22: 23 model tests and one more invalid vector; W4487 re-review,
  2026-08-22: 24 model tests; see the three amendments below.)*
- W1440 freezes `urn:baton:agent-session:1.0`, eight turn outcomes, nine
  session states, 10 normalized event kinds, and four approval families. Its
  provider-free evidence includes 19 normalized traces, 78 negative vectors,
  three invalid-document fixtures, four captured Codex approval-response
  schemas, and 56 passing model tests.
- W1441 freezes `urn:baton:worker-conformance:1.0`, 68 normative obligations
  and 107 executable cases. The local profile selects 106 cases and the remote
  profile selects all 107; its 73 model tests pass. *(W4487, 2026-08-22: 69
  obligations and 110 cases, 109 local and 110 remote; W4487 review,
  2026-08-22: 70 obligations and 112 cases, 111 local and 112 remote; W4487
  re-review, 2026-08-22: 74 model tests, register unchanged; see the three
  amendments below.)*

**Confirmed.** The W1439 definitions imported by W1440 and W1441 are
byte-identical. The family uses one major-version and negotiated-capability
policy, rejects unknown majors and unnegotiated capabilities, reuses W151's
complete identity and effectively-once settlement rules, and gives no
runtime, transport, agent provider or diagnostic identifier portable
authority semantics.

**Confirmed.** The frozen schemas make bounded non-secret input, output,
proposal and receipt evidence digest-verifiable; preserve unknown-field and
canonicalization rules; and distinguish cancellation intent from observed
quiescence. The conformance register mechanically covers both frozen
vocabularies and exercises positive, negative, race, retry, restart,
partition, stale-publication and leakage behavior without a model provider.

The six M1 freeze criteria above are therefore satisfied. This approval
boundary freezes design vocabulary and executable examples only. It neither
authorizes implementation nor certifies an authority, worker runtime, ACP
relay or provider adapter.

## Amendment to the M1 freeze — W4487, 2026-08-22

The freeze above states that the family "reuses W151's complete identity and
effectively-once settlement rules". While preparing W2929 the reviewer found
one place where it could not: W151 `1-ruled` §7 required a declining worker to
present the exact unspent claim bearer, and worker-control 1.0 §6.1 with its
frozen `worker-control-1.0.schema.json` requires `claim_token: null` when
`decision=decline`. Both were frozen and the schema mechanically rejects the
W151 shape, so no Worker Manager could satisfy both by implementation choice.

`baton.slaw` ruled on 2026-08-22, before W2929 implements decline: the
non-secret decline envelope is kept, and W151's token requirement for DECLINE
is explicitly superseded. A decline is authorized by the integrity-protected
`offer.decide` operation bound to `(offer_id, runtime_attempt_id, work_ref,
decision, reason)`; the manager validates that binding and atomically consumes
the offer's durable verifier without minting a claim. **Acceptance is
unchanged** and still requires the exact unspent, unexpired bearer.

**This is the first and so far only post-freeze change to the M1 family, and
it was made across all three contracts together** — a supersession recorded in
one contract while the others kept the old counts would leave the freeze
describing a family that no longer exists:

- W151 `SPEC.md` §1 carries the dated supersession with the old row quoted,
  and §6/§7 carry the replacement. Its evidence gained seven decline scenarios
  (54 -> 61 tests).
- W1439 `SPEC.md` §0 records that the general "W151 wins" precedence rule is
  intact and that this ONE conflict was ruled the other way; §6.1, §12 rule 14
  and §13 carry the decline authorization; the schema carries a `$comment`
  naming the ruling. Its evidence gained one valid and two invalid vectors and
  five model tests (12 -> 17).
- W1441 gained obligation `C-08` and three cases (68 -> 69 obligations,
  107 -> 110 cases), because the one rule the family had to be re-ruled over
  must not be the one nothing certifies.

Full record: `work/records/2026/08/finding-worker-control-decline-token-conflict/`.
The M1 freeze criteria are re-satisfied on the amended contracts; this
amendment still authorizes no implementation.

## Second amendment — the W4487 review, 2026-08-22

The independent review of the amendment above found that the decline it made
tokenless was not yet effectively-once on this side of the boundary. §4.2 of
W1439 defines the operation signature as "the canonical digest of the
operation kind and every effective durable operand" and left the payload to
each implementation; the new decline vector filled it with the BODY digest,
and `validate_envelope` never recomputed it. Changing the decline's durable
reason, recomputing only the body digest and retaining the old signature
passed both the frozen schema and the model — and a manager journalling by
that signature would replay the first decline against conflicting prose.

This one is a CLARIFICATION, not a supersession, and the distinction matters
to a later reader: no document that satisfied §4.2 as written stops being
conformant, because §4.2 never said the signature was the body digest. What
changed is that the payload is now exact instead of inferable.

- W1439 §4.2 fixes the payload as `{"kind", "operands"}` over §3.2 canonical
  bytes, states the receiver's recomputation and the reply exemption, and
  explains why a bearer operand rides as its VERIFIER digest — a signature is
  durable, and §13 keeps the bearer off durable surfaces, while dropping it
  entirely would make an accept under a reused id with a different token an
  exact replay. §12 rule 9 carries the recomputation; the schema's
  `operation` definition carries a `$comment`. Evidence gained one invalid
  vector and six model tests (17 -> 23).
- W1441 gained obligation `E-11` and two cases (69 -> 70 obligations,
  110 -> 112 cases). `E-02` did not cover it: that obligation starts from two
  signatures that already differ, so it says nothing about whether a
  signature describes its own request.
- W151 needed no change. Its decline model already binds the reason into the
  replay signature and its collision regression passes; the two contracts
  agree on the operand set, and neither includes the bearer.

Full record: the same W4487 dossier, `review-2026-08-22T14-39-32Z.md` and the
progress entry answering it. The M1 freeze criteria are re-satisfied on the
clarified contracts; this amendment still authorizes no implementation.

## Third amendment — the W4487 re-review, 2026-08-22

The clarification above said a bearer operand rides the operation signature as
"the verifier the manager already holds". It did not hold: W151 stored SHA-256
over the bearer's raw UTF-8 bytes as bare hexadecimal, and worker-control's new
payload computed SHA-256 over the bearer's JCS JSON encoding with the family's
`sha256:` prefix. For the bearer `"x" * 43` those are different hashed byte
sequences, not formatting variants, so two conforming peers computed different
operation signatures for the same acceptance.

**This is the amendment that most justifies the freeze note existing.** Each
package's tests asserted its own self-consistency and both were green; the
contradiction lived exactly in the space between two contracts that the freeze
claims agree. Nothing inside either package could have caught it.

- W151 §7 now PINS the derivation, because W151 owns the offer record:
  `"sha256:" + lowercase hex of SHA-256 over the bearer's own UTF-8 bytes`.
  The token's own bytes, not a JSON encoding of them, so escaping rules cannot
  enter the value. Evidence gained three cases (61 -> 64).
- W1439 §4.2 NAMES that derivation instead of defining a second one, and §14
  adds it to the approved set. Evidence gained one case (17 -> 24 counting the
  review's six).
- W1441 gained the cross-contract case itself —
  `test_the_claim_token_verifier_is_ONE_value_across_the_contracts` — which
  imports both models, compares the two derivations over bearers neither
  package pins, and asserts the value W151's OFFER RECORD stores equals the
  `claim_token_verifier` in worker-control's payload (73 -> 74 model tests; the
  register is unchanged, because this is contract agreement rather than a new
  runtime obligation).
- A golden bearer and its verifier are pinned as LITERALS in both models, so a
  change to either derivation fails a comparison instead of moving its own
  expectation with it.

Full record: the same W4487 dossier, `review-2026-08-22T14-57-26Z.md`. The M1
freeze criteria are re-satisfied; this amendment still authorizes no
implementation.
